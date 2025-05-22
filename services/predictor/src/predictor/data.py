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
) -> pd.DataFrame:
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
        candle_duration: The duration of each candle in seconds.

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


def prepare_data(
    data: pd.DataFrame, pred_horizon_sec: int, candle_duration: int
) -> pd.DataFrame:
    """
    Prepare the data for training by adding the target column and cleaning the data.

    Args:
        data: The input dataframe.
        pred_horizon_sec: The prediction horizon in seconds.
        candle_duration: The duration of each candle in seconds.

    Returns:
        The prepared dataframe.
    """
    # Add the target column to the dataframe.
    data['target'] = data['closing_price'].shift(-pred_horizon_sec // candle_duration)

    # Drop rows with NaN values in the target column.
    data = data.dropna(subset=['target'])
    # Drop symbol and candle_duration columns.
    data = data.drop(columns=['symbol', 'candle_duration'])

    return data
