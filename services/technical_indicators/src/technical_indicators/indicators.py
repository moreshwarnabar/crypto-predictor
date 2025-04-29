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
    volume = np.array([c['volume'] for c in candles])

    sma_indicators = {}
    # compute a simple moving average
    sma_indicators['close_prices_sma_7'] = stream.SMA(closing_prices, timeperiod=7)
    sma_indicators['close_prices_sma_14'] = stream.SMA(closing_prices, timeperiod=14)
    sma_indicators['close_prices_sma_21'] = stream.SMA(closing_prices, timeperiod=21)
    sma_indicators['close_prices_sma_60'] = stream.SMA(closing_prices, timeperiod=60)

    # compute exponential moving average
    sma_indicators['close_prices_ema_7'] = stream.EMA(closing_prices, timeperiod=7)
    sma_indicators['close_prices_ema_14'] = stream.EMA(closing_prices, timeperiod=14)
    sma_indicators['close_prices_ema_21'] = stream.EMA(closing_prices, timeperiod=21)
    sma_indicators['close_prices_ema_60'] = stream.EMA(closing_prices, timeperiod=60)

    # compute relative strength index
    sma_indicators['close_prices_rsi_7'] = stream.RSI(closing_prices, timeperiod=7)
    sma_indicators['close_prices_rsi_14'] = stream.RSI(closing_prices, timeperiod=14)
    sma_indicators['close_prices_rsi_21'] = stream.RSI(closing_prices, timeperiod=21)
    sma_indicators['close_prices_rsi_60'] = stream.RSI(closing_prices, timeperiod=60)

    # compute average convergence divergence
    (
        sma_indicators['close_prices_macd_7'],
        sma_indicators['close_prices_macd_7_signal'],
        sma_indicators['close_prices_macd_7_hist'],
    ) = stream.MACD(closing_prices, fastperiod=7, slowperiod=21, signalperiod=9)

    # compute on balance volume
    sma_indicators['close_prices_obv'] = stream.OBV(closing_prices, volume)

    return {
        **candle,
        **sma_indicators,
    }
