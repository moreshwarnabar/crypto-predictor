def get_experiment_name(
    symbol: str, candle_duration: int, pred_horizon_sec: int
) -> str:
    """
    Get the experiment name for the given symbol, candle duration, and prediction horizon.
    """
    return f'{symbol}-{candle_duration}-{pred_horizon_sec}'
