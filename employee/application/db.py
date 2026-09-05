import redis
from pymongo import MongoClient

from application.configuration import Configuration

_mongo_client = MongoClient(Configuration.MONGO_URI, tz_aware=False)
_redis_client = redis.Redis(
    host=Configuration.REDIS_HOST,
    port=Configuration.REDIS_PORT,
    db=Configuration.REDIS_DB,
    password=Configuration.REDIS_PASSWORD,
    decode_responses=True,
)


def assets():
    """MongoDB kolekcija u kojoj se cuva imovina fonda."""
    return _mongo_client[Configuration.MONGO_DATABASE][Configuration.MONGO_COLLECTION]


def cache():
    """Redis klijent u kojem se cuvaju zahtevi koji cekaju odluku direktora."""
    return _redis_client
