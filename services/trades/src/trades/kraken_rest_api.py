import json
import time

import requests
from loguru import logger

from trades.trade import Trade


class KrakenRestAPI:
    URL = 'https://api.kraken.com/0/public/Trades'

    def __init__(self, symbol: str, since_days: int = 0):
        self.symbol = symbol
        self.since = int(time.time_ns() - since_days * 24 * 60 * 60 * 1000000000)
        self._is_done = False

    def get_trades(self) -> list[Trade]:
        """
        Get trades from Kraken REST API
        returns list of Trade objects
        """
        headers = {'Accept': 'application/json'}
        params = {'pair': self.symbol, 'since': self.since}

        try:
            response = requests.get(self.URL, headers=headers, params=params)
        except requests.exceptions.SSLError as e:
            logger.error(f'Error getting trades from Kraken REST API: {e}')
            time.sleep(10)
            return []

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding JSON: {e}')
            return []

        try:
            trades = data['result'][self.symbol]
        except KeyError:
            logger.error(f'Error getting trades from Kraken REST API: {data}')
            return []

        # transform trades to Trade objects
        trades = [
            Trade.from_rest_api(self.symbol, trade[0], trade[1], trade[2])
            for trade in trades
        ]

        self.since = int(float(data['result']['last']))
        if self.since > int(time.time_ns() - 1000000000):
            self._is_done = True

        return trades

    def is_done(self) -> bool:
        return self._is_done
