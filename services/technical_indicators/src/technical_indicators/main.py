from loguru import logger
from quixstreams import Application

from technical_indicators.candle import update_candle_state


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group: str,
    candle_duration: int,
):
    """
    Transforms a stream of input candles into a stream of technical indicators.

    - Ingests candles from the 'kafka_input_topic' topic.
    - Aggregates candles into technical indicators.
    - Produces technical indicators to the 'kafka_output_topic' topic.

    Args:
        kafka_broker_address (str): The address of the Kafka broker.
        kafka_input_topic (str): The topic to ingest candles from.
        kafka_output_topic (str): The topic to produce technical indicators to.
        candle_duration (int): The duration of the candles in seconds.
        kafka_consumer_group (str): The consumer group to use for the application.
    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
    )

    candles_topic = app.topic(kafka_input_topic, value_deserializer='json')
    technical_indicators_topic = app.topic(kafka_output_topic, value_serializer='json')

    # Create a dataframe to ingest candles from the candles topic
    sdf = app.dataframe(topic=candles_topic)

    # filter the candles by the candle duration
    sdf = sdf[sdf['candle_duration'] == candle_duration]

    # Add candles to a state dictionary
    sdf = sdf.apply(update_candle_state, stateful=True)

    # TODO: Compute the technical indicators

    sdf = sdf.update(lambda value: logger.debug(f'Value: {value}'))

    # Write the transformed dataframe to the technical indicators topic.
    sdf = sdf.to_topic(technical_indicators_topic)

    # Run the application.
    app.run()


if __name__ == '__main__':
    from technical_indicators.config import settings

    run(
        kafka_broker_address=settings.kafka_broker_address,
        kafka_input_topic=settings.kafka_input_topic,
        kafka_output_topic=settings.kafka_output_topic,
        kafka_consumer_group=settings.kafka_consumer_group,
        candle_duration=settings.candle_duration,
    )
