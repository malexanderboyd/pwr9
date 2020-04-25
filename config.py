from dataclasses import dataclass


@dataclass
class RedisConfiguration:
    host: str
    queue_key: str


@dataclass
class Configuration:
    redis: RedisConfiguration
