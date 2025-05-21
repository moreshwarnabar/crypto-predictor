import os

import great_expectations as ge
import mlflow
import pandas as pd
from lazypredict.Supervised import LazyRegressor
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions
from sklearn.metrics import mean_absolute_error
from ydata_profiling import ProfileReport

from predictor.models import BaselineModel, get_model
from predictor.utils import get_experiment_name


def profile_data(data: pd.DataFrame, output_file: str):
    """
    Profile the data and save the report to the given file.
    Generates a HTML file containing the EDA report.

    Args:
        data: The data to profile.
        output_file: The file to save the report to.
    """
    profile = ProfileReport(
        data,
        tsmode=True,
        sortby='window_start_ms',
        title='Data Profiling Report',
    )
    profile.to_file(output_file)


def validate_data(data: pd.DataFrame):
    """
    Runs a battery of checks on the data.
    If any of the checks fail, the function will raise an exception.
    """
    # Check that the closing price is positive.
    ge_data = ge.from_pandas(data)
    validation_result = ge_data.expect_column_values_to_be_between(
        column='closing_price',
        min_value=0,
        max_value=float('inf'),
        strict_min=True,
        strict_max=True,
    )
    if not validation_result.success:
        raise ValueError(validation_result.get_failure_cases())

    # Check that the target is positive.
    validation_result = ge_data.expect_column_values_to_be_between(
        column='target',
        min_value=0,
        max_value=float('inf'),
        strict_min=True,
        strict_max=True,
    )
    if not validation_result.success:
        raise ValueError(validation_result.get_failure_cases())

    # Check that closing price is not NaN.
    validation_result = ge_data.expect_column_values_to_be_of_type(
        column='closing_price',
        type_='float64',
    )
    if not validation_result.success:
        raise ValueError(validation_result.get_failure_cases())


def load_data_from_risingwave(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    symbol: str,
    since_days: int,
    candle_duration: int,
):
    """
    Load the data from the risingwave table.

    Args:
        host: The host of the risingwave cluster.
        port: The port of the risingwave cluster.
        user: The user of the risingwave cluster.
        password: The password of the risingwave cluster.
        database: The database to use.
        symbol: The symbol to load the data for.
        since_days: The number of days to load the data for.

    Returns:
        A pandas dataframe containing the data.
    """
    logger.info(f'Connecting to risingwave: {host}:{port} {user} {password} {database}')
    rw = RisingWave(
        RisingWaveConnOptions.from_connection_info(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
    )

    query = f"""
    SELECT *
    FROM public.technical_indicators
    WHERE symbol = '{symbol}'
        AND candle_duration = {candle_duration}
        AND to_timestamp(window_start_ms / 1000) > now() - interval '{since_days} days'
    ORDER BY window_start_ms ASC;
    """
    data = rw.fetch(query, format=OutputFormat.DATAFRAME)
    logger.info(
        f'Loaded {len(data)} rows from risingwave for {symbol} in the last {since_days} days'
    )

    return data


def train(
    rw_host: str,
    rw_port: int,
    rw_user: str,
    rw_password: str,
    rw_database: str,
    symbol: str,
    since_days: int,
    candle_duration: int,
    pred_horizon_sec: int,
    generate_report: bool,
    mlflow_tracking_uri: str,
    train_test_split_ratio: float,
):
    """
    Train the model for the given symbol.
    Pushes to the model registry.
    """
    logger.info(f'Setting MLFlow tracking URI to {mlflow_tracking_uri}')
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    logger.info(f'Setting MLFlow experiment to {symbol}')
    mlflow.set_experiment(
        get_experiment_name(symbol, candle_duration, pred_horizon_sec)
    )

    with mlflow.start_run() as run:
        logger.info(f'Starting MLFlow run {run.info.run_id}')

        # Log training parameters.
        mlflow.log_param('since_days', since_days)
        mlflow.log_param('candle_duration', candle_duration)
        mlflow.log_param('prediction_horizon_seconds', pred_horizon_sec)
        mlflow.log_param('train_test_split_ratio', train_test_split_ratio)

        # Load the data from the risingwave table.
        data = load_data_from_risingwave(
            host=rw_host,
            port=rw_port,
            user=rw_user,
            password=rw_password,
            database=rw_database,
            symbol=symbol,
            since_days=since_days,
            candle_duration=candle_duration,
        )

        # Add the target column to the dataframe.
        data['target'] = data['closing_price'].shift(
            -pred_horizon_sec // candle_duration
        )

        # Drop rows with NaN values in the target column.
        data = data.dropna(subset=['target'])
        # Drop symbol and candle_duration columns.
        data = data.drop(columns=['symbol', 'candle_duration'])

        # Log the data to mlflow.
        dataset = mlflow.data.from_pandas(data)
        mlflow.log_input(dataset, context='training')

        # Validate the data.
        validate_data(data)

        mlflow.log_param('data-shape', data.shape)

        # Perform EDA on the data (Data Profiling).
        if generate_report:
            profile_data(data, 'data_profiling.html')
        if os.path.exists('data_profiling.html'):
            mlflow.log_artifact(
                local_path='data_profiling.html', artifact_path='eda_report'
            )

        # Split the data into train and test.
        train_size = int(len(data) * train_test_split_ratio)
        train_data = data.iloc[:train_size]
        test_data = data.iloc[train_size:]

        # Log the train and test data to mlflow.
        mlflow.log_param('train-data-shape', train_data.shape)
        mlflow.log_param('test-data-shape', test_data.shape)

        # Split the data into features and target.
        X_train = train_data.drop(columns=['target'])
        y_train = train_data['target']
        X_test = test_data.drop(columns=['target'])
        y_test = test_data['target']

        # Log the features and target to mlflow.
        mlflow.log_param('X_train-shape', X_train.shape)
        mlflow.log_param('y_train-shape', y_train.shape)
        mlflow.log_param('X_test-shape', X_test.shape)
        mlflow.log_param('y_test-shape', y_test.shape)

        # Train a baseline model.
        model = BaselineModel()
        y_pred = model.predict(X_test)

        # Log the metrics to mlflow.
        baseline_mae = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric('mae_baseline', baseline_mae)
        logger.info(f'Baseline MAE: {baseline_mae}')

        mlflow_tracking_uri = os.environ.get('MLFLOW_TRACKING_URI')
        del os.environ['MLFLOW_TRACKING_URI']
        # Train a set of N models using lazy predict.
        reg = LazyRegressor(
            verbose=0, ignore_warnings=False, custom_metric=mean_absolute_error
        )
        models, _ = reg.fit(X_train, X_test, y_train, y_test)
        models.reset_index(inplace=True)
        if 'mean_absolute_error' in models.columns:
            models.rename(columns={'mean_absolute_error': 'MAE'}, inplace=True)

        os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
        mlflow.log_table(models, 'models_summary.json')
        logger.info(f'Models summary:\n\n {models}')

        # Pick the best model and perform hyper-parameter tuning.
        best_model = None
        for model_name in models['model']:
            try:
                model = get_model(model_name)
            except ValueError:
                logger.error(f'Model {model_name} not found, skipping')
                continue

        best_model.fit(X_train, y_train)

        # Validate the best model.
        y_pred = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric('mae_best_model', mae)
        logger.info(f'Best model MAE: {mae}')


if __name__ == '__main__':
    train(
        rw_host='localhost',
        rw_port=4567,
        rw_user='root',
        rw_password='',
        rw_database='dev',
        symbol='ETH/EUR',
        since_days=30,
        candle_duration=60,
        pred_horizon_sec=300,
        generate_report=True,
        mlflow_tracking_uri='http://localhost:8283',
        train_test_split_ratio=0.8,
    )
