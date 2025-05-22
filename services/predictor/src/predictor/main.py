import os

import mlflow
from loguru import logger

from predictor.data import load_data_from_risingwave, prepare_data, validate_data
from predictor.profiling import profile_data
from predictor.train import train_model
from predictor.utils import get_experiment_name


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

        # Prepare the data for training.
        data = prepare_data(data, pred_horizon_sec, candle_duration)

        # Validate the data.
        validate_data(data)

        # Perform EDA on the data (Data Profiling).
        if generate_report:
            profile_data(data, 'data_profiling.html')
            if os.path.exists('data_profiling.html'):
                mlflow.log_artifact(
                    local_path='data_profiling.html', artifact_path='eda_report'
                )

        # Train the model.
        train_model(
            data=data,
            symbol=symbol,
            candle_duration=candle_duration,
            pred_horizon_sec=pred_horizon_sec,
            train_test_split_ratio=train_test_split_ratio,
            generate_report=generate_report,
            mlflow_tracking_uri=mlflow_tracking_uri,
        )


if __name__ == '__main__':
    train(
        rw_host='localhost',
        rw_port=4567,
        rw_user='root',
        rw_password='',
        rw_database='dev',
        symbol='ETH/EUR',
        since_days=10,
        candle_duration=60,
        pred_horizon_sec=300,
        generate_report=False,
        mlflow_tracking_uri='http://localhost:8283',
        train_test_split_ratio=0.8,
    )
