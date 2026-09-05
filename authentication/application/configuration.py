import os
from datetime import timedelta


class Configuration:
    """Sva konfiguracija dolazi iz varijabli okruzenja (ConfigMap / Secret)."""

    DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.environ.get("DATABASE_PORT", "3306")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "iep_users")
    DATABASE_USER = os.environ.get("DATABASE_USER", "root")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "root")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "iep-development-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Podaci pocetnog direktora (koristi ih samo migrate.py)
    DIRECTOR_FORENAME = os.environ.get("DIRECTOR_FORENAME", "Scrooge")
    DIRECTOR_SURNAME = os.environ.get("DIRECTOR_SURNAME", "McDuck")
    DIRECTOR_EMAIL = os.environ.get("DIRECTOR_EMAIL", "onlymoney@gmail.com")
    DIRECTOR_PASSWORD = os.environ.get("DIRECTOR_PASSWORD", "evenmoremoney")

    ROLE_DIRECTOR = "director"
    ROLE_EMPLOYEE = "employee"
