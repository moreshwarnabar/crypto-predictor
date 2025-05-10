from datetime import datetime, timezone

from pydantic import BaseModel


class Trade(BaseModel):
    symbol: str
    price: float
    quantity: float
    timestamp: str
    timestamp_ms: float

    @classmethod
    def from_rest_api(
        cls, symbol: str, price: float, quantity: float, timestamp_sec: float
    ) -> 'Trade':
        """
        Convert a trade from the Kraken REST API to a Trade object.
        """
        return cls(
            symbol=symbol,
            price=price,
            quantity=quantity,
            timestamp=datetime.fromtimestamp(timestamp_sec, tz=timezone.utc).strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            timestamp_ms=timestamp_sec * 1000,
        )

    def to_dict(self) -> dict:
        return self.model_dump()
