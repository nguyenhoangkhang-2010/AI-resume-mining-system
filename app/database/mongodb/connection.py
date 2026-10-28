import re

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError
from loguru import logger

from app.core.config.settings import settings
from app.core.exceptions import DatabaseUnavailableError


def _mask_credentials(uri: str) -> str:
    return re.sub(r"//[^/@]+@", "//***@", uri)


class MongoDBConnection:
    _instance = None
    client: MongoClient | None = None
    db: Database | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance

    def connect(self) -> None:
        if self.client is not None:
            logger.warning("MongoDB client is already connected.")
            return

        client = None

        try:
            logger.info(f"Connecting to MongoDB at {_mask_credentials(settings.MONGO_URI)}...")
            client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)

            client.admin.command('ping')
            self.client = client
            self.db = client[settings.DB_NAME]

            logger.info(f"Successfully connected to MongoDB database: '{settings.DB_NAME}'")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._discard(client)
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while connecting to MongoDB: {e}")
            self._discard(client)
            raise e

    @staticmethod
    def _discard(client: MongoClient | None) -> None:
        if client is not None:
            client.close()

    def get_db(self) -> Database:
        if self.db is None:
            logger.warning("Database connection is not established. Trying to connect.")

            try:
                self.connect()
            except Exception as exc:
                raise DatabaseUnavailableError("MongoDB is not connected.") from exc

        return self.db

    def ping(self) -> bool:
        if self.client is None:
            return False

        try:
            self.client.admin.command('ping')
            return True
        except PyMongoError:
            return False

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection gracefully closed.")

mongo_db = MongoDBConnection()
