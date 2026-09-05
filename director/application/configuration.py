import os
from datetime import timedelta


class Configuration:
    """Sva konfiguracija dolazi iz varijabli okruzenja (ConfigMap / Secret)."""

    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "fund")
    MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "assets")

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or None
    REDIS_ORDERS_KEY = os.environ.get("REDIS_ORDERS_KEY", "pending_orders")
    REDIS_CONTRACTS_KEY = os.environ.get("REDIS_CONTRACTS_KEY", "voting_contracts")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "iep-development-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    ROLE_DIRECTOR = "director"
    ROLE_EMPLOYEE = "employee"

    # Ethereum / Ganache
    GANACHE_URL = os.environ.get("GANACHE_URL", "http://localhost:8545")
    CONTRACT_GAS_LIMIT = int(os.environ.get("CONTRACT_GAS_LIMIT", "3000000"))
    VOTE_GAS_LIMIT = int(os.environ.get("VOTE_GAS_LIMIT", "200000"))
    # indeks racuna sa kojeg se placa naknada za kreiranje ugovora
    DEPLOYER_ACCOUNT_INDEX = int(os.environ.get("DEPLOYER_ACCOUNT_INDEX", "0"))

    # Nadgledanje glasanja
    WATCHER_ENABLED = os.environ.get("WATCHER_ENABLED", "true").lower() == "true"
    WATCHER_INTERVAL = float(os.environ.get("WATCHER_INTERVAL", "2"))
