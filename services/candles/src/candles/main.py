from datetime import timedelta
from typing import Any, List, Optional, Tuple

from loguru import logger
from quixstreams import Application
from quixstreams.models import TimestampType


def timestamp_extractor(
    value: any,
    headers: Optional[List[Tuple[str, Any]]],
    timestamp: float,
    timestamp_type: TimestampType,
) -> int:
    """
    Extract the timestamp from the value.
    """
    return value['timestamp_ms']


def init_candle(trade: dict) -> dict:
    """
    Initialize a candle with the first trade
    """
    return {
        'open': trade['price'],
        'high': trade['price'],
        'low': trade['price'],
        'close': trade['price'],
        'volume': trade['quantity'],
        'symbol': trade['symbol'],
    }


def update_candle(candle: dict, trade: dict) -> dict:
    """
    Update the candle with a new trade
    """
    candle['close'] = trade['price']
    candle['high'] = max(candle['high'], trade['price'])
    candle['low'] = min(candle['low'], trade['price'])
    candle['volume'] += trade['quantity']

    return candle


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    candle_duration: int,
    kafka_consumer_group: str,
):
    """
    Transforms a stream of input trades into a stream of output candles.

    - Ingests trades from the 'kafka_input_topic' topic.
    - Aggregates trades into candles of a fixed duration (in seconds).
    - Produces candles to the 'kafka_output_topic' topic.

    Args:
        kafka_broker_address (str): The address of the Kafka broker.
        kafka_input_topic (str): The topic to ingest trades from.
        kafka_output_topic (str): The topic to produce candles to.
        candle_duration (int): The duration of the candles in seconds.
        kafka_consumer_group (str): The consumer group to use for the application.
    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
    )

    trades_topic = app.topic(
        kafka_input_topic,
        value_deserializer='json',
        timestamp_extractor=timestamp_extractor,
    )
    candles_topic = app.topic(kafka_output_topic, value_serializer='json')

    # Create a dataframe to ingest trades from the trades topic
    sdf = app.dataframe(topic=trades_topic)

    # Update the dataframe to log the received trades for now.
    sdf = (
        # define the tumbling window
        sdf.tumbling_window(timedelta(seconds=candle_duration))
        # reducers to aggregate trades into candles
        .reduce(
            reducer=update_candle,  # updates the candle with a new trade
            initializer=init_candle,  # returns initial value for the candle
        )
    )

    sdf = sdf.current()

    # extract the candle details and re-format the dataframe
    sdf['opening_price'] = sdf['value']['open']
    sdf['high_price'] = sdf['value']['high']
    sdf['low_price'] = sdf['value']['low']
    sdf['closing_price'] = sdf['value']['close']
    sdf['volume'] = sdf['value']['volume']
    sdf['symbol'] = sdf['value']['symbol']

    sdf['window_start_ms'] = sdf['start']
    sdf['window_end_ms'] = sdf['end']

    # keeping relevant columns
    sdf = sdf[
        [
            'symbol',
            'window_start_ms',
            'window_end_ms',
            'opening_price',
            'high_price',
            'low_price',
            'closing_price',
            'volume',
        ]
    ]

    sdf['candle_duration'] = candle_duration

    sdf = sdf.update(lambda value: logger.debug(f'Candle: {value}'))

    # Write the transformed dataframe to the candles topic.
    sdf = sdf.to_topic(candles_topic)

    # Run the application.
    app.run()


if __name__ == '__main__':
    from candles.config import settings

    run(
        kafka_broker_address=settings.kafka_broker_address,
        kafka_input_topic=settings.kafka_input_topic,
        kafka_output_topic=settings.kafka_output_topic,
        candle_duration=settings.candle_duration,
        kafka_consumer_group=settings.kafka_consumer_group,
    )
