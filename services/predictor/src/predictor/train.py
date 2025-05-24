import os

import mlflow
import pandas as pd
from lazypredict.Supervised import LazyRegressor
from loguru import logger
from sklearn.metrics import mean_absolute_error

from predictor.models import BaselineModel, get_model


def train_model(
    data: pd.DataFrame,
    symbol: str,
    candle_duration: int,
    pred_horizon_sec: int,
    train_test_split_ratio: float,
    generate_report: bool,
    mlflow_tracking_uri: str,
):
    """
    Train the model for the given data.
    Pushes to the model registry.

    Args:
        data: The prepared dataframe.
        symbol: The symbol being predicted.
        candle_duration: The duration of each candle in seconds.
        pred_horizon_sec: The prediction horizon in seconds.
        train_test_split_ratio: The ratio of training data to test data.
        generate_report: Whether to generate a data profiling report.
        mlflow_tracking_uri: The URI of the MLflow tracking server.
    """
    logger.info(f'Training model for {symbol} with {data.shape[0]} rows')
    # Log training parameters.
    mlflow.log_param('prediction_horizon_seconds', pred_horizon_sec)
    mlflow.log_param('train_test_split_ratio', train_test_split_ratio)

    # Log the data to mlflow.
    dataset = mlflow.data.from_pandas(data)
    mlflow.log_input(dataset, context='training')

    mlflow.log_param('data-shape', data.shape)

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
    models.sort_values(by='MAE', inplace=True)
    for model_name in models['Model']:
        try:
            best_model = get_model(model_name)
            break
        except ValueError:
            logger.error(f'Model {model_name} not found, skipping')
            continue

    best_model.fit(X_train, y_train)

    # Validate the best model.
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mlflow.log_metric('mae_best_model', mae)
    logger.info(f'Best model MAE: {mae}')
