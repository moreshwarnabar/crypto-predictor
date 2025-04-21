from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='services/trades/src/trades/trades.env')
    
    product_ids: list[str] = ['BTC/EUR', 'BTC/USD', 'ETH/EUR', 'ETH/USD', 'SOL/EUR', 'SOL/USD', 'XRP/EUR', 'XRP/USD']
    kafka_broker_address: str
    kafka_topic: str

settings = Settings()