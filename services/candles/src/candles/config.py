from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='services/candles/src/candles/candles.env'
    )

    kafka_broker_address: str
    kafka_input_topic: str
    kafka_output_topic: str
    candle_duration: int


settings = Settings()
