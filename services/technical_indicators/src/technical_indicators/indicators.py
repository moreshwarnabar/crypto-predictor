import numpy as np
from talib import stream


def compute_technical_indicators(candle: dict, state: dict) -> dict:
    """
    Computes technical indicators for a list of candles.

    Args:
        candle (dict): A dictionary of data.
        state (dict): The state of the application.

    Returns:
        dict: A dictionary of technical indicators.
    """
    # extract the close prices from the candles into a numpy array
    candles = state.get('candles', [])
    closing_prices = np.array([c['closing_price'] for c in candles])
    _opening_prices = np.array([c['opening_price'] for c in candles])
    _high_prices = np.array([c['high_price'] for c in candles])
    _low_prices = np.array([c['low_price'] for c in candles])
    _volume = np.array([c['volume'] for c in candles])

    sma_indicators = {}
    # compute a simple moving average
    sma_indicators['close_prices_sma_7'] = stream.SMA(closing_prices, timeperiod=7)
    sma_indicators['close_prices_sma_14'] = stream.SMA(closing_prices, timeperiod=14)
    sma_indicators['close_prices_sma_21'] = stream.SMA(closing_prices, timeperiod=21)
    sma_indicators['close_prices_sma_60'] = stream.SMA(closing_prices, timeperiod=60)

    # breakpoint()

    return {
        **candle,
        **sma_indicators,
    }
