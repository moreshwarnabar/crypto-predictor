import great_expectations as ge
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions


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
        inclusive_min=False,
        inclusive_max=False,
    )
    if not validation_result.success:
        raise ValueError(validation_result.get_failure_cases())

    # Check that the target is positive.
    validation_result = ge_data.expect_column_values_to_be_between(
        column='target',
        min_value=0,
        max_value=float('inf'),
        inclusive_min=False,
        inclusive_max=False,
    )
    if not validation_result.success:
        raise ValueError(validation_result.get_failure_cases())

    # Check that closing price is not NaN.
    validation_result = ge_data.expect_column_values_to_be_of_type(
        column='closing_price',
        type='float64',
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
):
    """
    Train the model for the given symbol.
    Pushes to the model registry.
    """
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
    data['target'] = data['closing_price'].shift(-pred_horizon_sec // candle_duration)

    # Validate the data.
    validate_data(data)

    # Perform EDA on the data (Data Profiling).


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
    )
