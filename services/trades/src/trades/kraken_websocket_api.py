import json

from loguru import logger
from websocket import create_connection

from trades.trade import Trade


class KrakenWebsocketAPI:
    URL = 'wss://ws.kraken.com/v2'

    def __init__(self, symbols: list[str]):
        self.symbols = symbols

        self._ws_client = create_connection(self.URL)
        self._subscribe()

    def is_done(self) -> bool:
        return False

    def get_trades(self) -> list[Trade]:
        data = self._ws_client.recv()

        if 'heartbeat' in data:
            logger.info('Heartbeat received')
            return []

        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding JSON: {e}')
            return []

        try:
            trades_data = data['data']
        except KeyError as e:
            logger.error(f"No 'data' field in the message: {e}")
            return []

        trades = [
            Trade.from_websocket_api(
                symbol=trade['symbol'],
                price=float(trade['price']),
                quantity=float(trade['qty']),
                timestamp=trade['timestamp'],
            )
            for trade in trades_data
        ]

        return trades

    def _subscribe(self):
        self._ws_client.send(
            json.dumps(
                {
                    'method': 'subscribe',
                    'params': {
                        'channel': 'trade',
                        'symbol': self.symbols,
                        'snapshot': False,
                    },
                }
            )
        )

        for _ in self.symbols:
            _ = self._ws_client.recv()
            _ = self._ws_client.recv()

    def _on_message(self, message):
        pass
