from loguru import logger
from quixstreams import Application


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    candle_duration: int,
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
    """
    app = Application(
        broker_address=kafka_broker_address,
    )

    trades_topic = app.topic(kafka_input_topic, value_deserializer='json')
    candles_topic = app.topic(kafka_output_topic, value_serializer='json')

    # Create a dataframe to ingest trades from the trades topic
    sdf = app.dataframe(topic=trades_topic)

    # Update the dataframe to log the received trades for now.
    # TODO: replace with the actual logic to aggregate trades into candles.
    sdf = sdf.update(lambda message: logger.info(f'Received trade: {message}'))

    # Write the transformed dataframe to the candles topic.
    sdf = sdf.to_topic(candles_topic)

    # Run the application.
    app.run()


if __name__ == '__main__':
    run(
        kafka_broker_address='localhost:31234',
        kafka_input_topic='trades',
        kafka_output_topic='candles',
        candle_duration=60,
    )
