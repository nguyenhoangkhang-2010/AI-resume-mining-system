from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from loguru import logger

from app.core.config.settings import settings


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

        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
            self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            
            self.client.admin.command('ping')
            self.db = self.client[settings.DB_NAME]
            
            logger.info(f"Successfully connected to MongoDB database: '{settings.DB_NAME}'")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while connecting to MongoDB: {e}")
            raise e

    def get_db(self) -> Database:
        if self.db is None:
            logger.error("Database connection is not established. Call connect() first.")
            raise ConnectionError("MongoDB is not connected.")
        return self.db

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection gracefully closed.")

mongo_db = MongoDBConnection()