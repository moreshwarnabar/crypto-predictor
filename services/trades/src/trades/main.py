from loguru import logger
from quixstreams import Application

from trades.config import settings
from trades.kraken_rest_api import KrakenRestAPI
from trades.kraken_websocket_api import KrakenWebsocketAPI
from trades.trade import Trade


def run(
    broker_address: str,
    kafka_topic_name: str,
    kraken_api: KrakenWebsocketAPI | KrakenRestAPI,
):
    app = Application(broker_address=broker_address)

    topic = app.topic(name=kafka_topic_name, value_serializer='json')

    with app.get_producer() as producer:
        while not kraken_api.is_done():
            events: list[Trade] = kraken_api.get_trades()
            for event in events:
                message = topic.serialize(key=event.symbol, value=event.to_dict())

                producer.produce(topic=topic.name, value=message.value, key=message.key)

                logger.info(f'Produced message to topic: {topic.name}')
                logger.info(f'Trade {event.to_dict()} pushed to kafka')

            import time

            time.sleep(1)


if __name__ == '__main__':
    config = settings

    if config.historical_data:
        logger.info('Using historical data')
        api = KrakenRestAPI(symbol=config.symbols[0], since_days=config.since_days)
    else:
        logger.info('Using real-time data')
        api = KrakenWebsocketAPI(symbols=config.symbols)

    run(
        broker_address=config.kafka_broker_address,
        kafka_topic_name=config.kafka_topic,
        kraken_api=api,
    )
