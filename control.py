import os
import re
import json

import docker
import redis

from config import Configuration, RedisConfiguration
from util import Singleton

"""
Blocking right-pop is an atomic operation, 
so Redis also guarantees that no matter how many consumers you've got listening for messages, 
each message is delivered to only one consumer.
"""


class Queue(metaclass=Singleton):
    def __init__(cls, *args, **kwargs):
        cls._config = kwargs.get("config")
        cls._connection = redis.StrictRedis(host=cls.host, port=6379)

    @property
    def queue_key(cls):
        return cls._config.redis.queue_key

    @property
    def host(cls):
        return cls._config.redis.host

    def enqueue(self, data):
        self._connection.lpush(self.queue_key, data)

    def dequeue(self):
        try:
            return self._connection.brpop(self.queue_key)
        except (ConnectionError, TypeError, IndexError):
            return None


config = Configuration(
    redis=RedisConfiguration(
        host=os.getenv("REDIS_HOST", "localhost"),
        queue_key=os.getenv("QUEUE_KEY", "game_queue"),
    )
)

queue = Queue(config=config)

while True:
    try:
        new_game_data = queue.dequeue()
        client = docker.from_env()

        new_game = json.loads(new_game_data[1].decode("utf-8"))

        game_port = new_game.get("port")
        game_id = new_game.get("gameId")

        container_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", new_game.get("gameTitle"))
        client.containers.run(
            "pwr9/godr4ft",
            f"/main -port={game_port} -gameId={game_id}",
            ports={f"{game_port}/tcp": game_port},
            environment=dict(NODE_ENV="dev"),
            name=container_name,
            network="pwr9_pwr9",
            detach=True,
        )
        print(f"started: {game_id} on port {game_port}")
    except Exception as e:
        print(e)
        pass
