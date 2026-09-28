from __future__ import annotations

from typing import Any

from deepeval.tracing import observe
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .config import Settings


class ProductNotFoundError(LookupError):
    pass


def validate_upc(upc: str) -> str:
    normalized = str(upc).strip()
    if not normalized.isdigit() or not 8 <= len(normalized) <= 14:
        raise ValueError("UPC must contain 8 to 14 digits.")
    return normalized


class MongoProductRepository:
    """The sole data-access boundary; deliberately exposes no arbitrary query API."""

    def __init__(self, settings: Settings):
        settings.require_mongodb()
        self._client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        self._collection = self._client[settings.mongodb_database][settings.mongodb_collection]

    @observe(type="tool")
    def find_by_upc(self, upc: str) -> dict[str, Any]:
        normalized = validate_upc(upc)
        try:
            product = self._collection.find_one({"upcId": normalized}, {"_id": 0})
        except PyMongoError as exc:
            raise ConnectionError("Unable to retrieve product information from MongoDB.") from exc
        if product is None:
            raise ProductNotFoundError(normalized)
        return product

    def close(self) -> None:
        self._client.close()
