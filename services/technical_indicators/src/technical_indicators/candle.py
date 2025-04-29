from quixstreams import State

from technical_indicators.config import settings


def is_same_window(candle: dict, last_candle: dict) -> bool:
    """
    Checks if the new candle corresponds to the same window and symbol as the last candle.

    Args:
        candle (dict): The new candle to check.
        last_candle (dict): The last candle in the state.
    """
    return (
        candle['symbol'] == last_candle['symbol']
        and candle['window_start_ms'] == last_candle['window_start_ms']
        and candle['window_end_ms'] == last_candle['window_end_ms']
    )


def update_candle_state(candle: dict, state: State):
    """
    Updates the state with the new candle.

    Args:
        candle (dict): The new candle to update the state with.
        state (State): The state to update.

    Returns:
        updated_state (dict): The updated state.
    """
    candles = state.get('candles', default=[])

    # check if new candle corresponds to the same window as the state
    if is_same_window(candle, candles[-1]):
        candles[-1] = candle
    else:
        candles.append(candle)

    if len(candles) > settings.max_candles:
        candles.pop(0)

    state.set('candles', candles)
    return {'candles': candles}
