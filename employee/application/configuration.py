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

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "iep-development-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    ROLE_DIRECTOR = "director"
    ROLE_EMPLOYEE = "employee"
