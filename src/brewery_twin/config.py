import os

from dotenv import load_dotenv

# Reads the .env file and loads the values into environment variables
load_dotenv()


def _required(key: str) -> str:
    """Reads an environment variable and raises an error if it's missing or empty."""
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


DB_USER = _required("POSTGRES_USER") #eswtriko
DB_PASSWORD = _required("POSTGRES_PASSWORD") #eswtriko_password
DB_NAME = _required("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# The connection string to be used with psycopg
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"