from loguru import logger
from quixstreams import Application

from trades.config import settings
from trades.kraken_api import KrakenAPI, Trade


def run(broker_address: str, kafka_topic_name: str, kraken_api: KrakenAPI):
    app = Application(broker_address=broker_address)

    topic = app.topic(name=kafka_topic_name, value_serializer='json')

    with app.get_producer() as producer:
        while True:
            events: list[Trade] = kraken_api.get_trades()
            for event in events:
                message = topic.serialize(
                    # key=event["id"],
                    value=event.to_dict()
                )

                producer.produce(topic=topic.name, value=message.value, key=message.key)

                logger.info(f'Produced message to topic: {topic.name}')
                logger.info(f'Trade {event.to_dict()} pushed to kafka')

            import time

            time.sleep(1)


if __name__ == '__main__':
    config = settings

    api = KrakenAPI(product_ids=config.product_ids)
    run(
        broker_address=config.kafka_broker_address,
        kafka_topic_name=config.kafka_topic,
        kraken_api=api,
    )
