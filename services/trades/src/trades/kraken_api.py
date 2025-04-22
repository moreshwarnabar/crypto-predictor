import json

from loguru import logger
from pydantic import BaseModel
from websocket import create_connection


class Trade(BaseModel):
    product_id: str
    price: float
    quantity: float
    timestamp: str

    def to_dict(self) -> dict:
        return self.model_dump()


class KrakenAPI:
    URL = 'wss://ws.kraken.com/v2'

    def __init__(self, product_ids: list[str]):
        self.product_ids = product_ids

        self._ws_client = create_connection(self.URL)
        self._subscribe()

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
            Trade(
                product_id=trade['symbol'],
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
                        'symbol': self.product_ids,
                        'snapshot': False,
                    },
                }
            )
        )

        for _ in self.product_ids:
            _ = self._ws_client.recv()
            _ = self._ws_client.recv()

    def _on_message(self, message):
        pass
