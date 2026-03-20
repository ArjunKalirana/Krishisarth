from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base configuration
    PROJECT_NAME: str = "KrishiSarth"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    
    # Database Configuration
    DATABASE_URL: str
    
    # InfluxDB Configuration
    INFLUXDB_URL: str
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str = "krishisarth_sensors"
    
    # Redis Configuration
    REDIS_URL: str
    
    # Security Configuration
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_ACCESS_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int = 1883
    
    # AWS Configuration
    AWS_S3_BUCKET: str
    AWS_REGION: str
    
    # Third-party APIs
    OPENWEATHER_API_KEY: str
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
