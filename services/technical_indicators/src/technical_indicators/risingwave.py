def create_table(table_name: str, kafka_topic: str, kafka_broker_address: str):
    """
    Create the table in RisingWave.
    Connects the table to a Kafka topic.

    RisingWave will then automatically ingest the data from the Kafka topic
    in real-time and update the table.
    """
    pass
