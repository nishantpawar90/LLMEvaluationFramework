from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    mongodb_uri: str | None = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str | None = os.getenv("MONGODB_DATABASE", "product_agent")
    mongodb_collection: str | None = os.getenv("MONGODB_COLLECTION", "ProductUPC")
    model: str = os.getenv("PRODUCT_AGENT_MODEL", "gpt-4.1-mini")
    evaluation_model: str = os.getenv("EVALUATION_MODEL", "gpt-4.1-mini")
    sample_upc: str = os.getenv("PRODUCT_AGENT_SAMPLE_UPC", "0001960004580")

    def require_mongodb(self) -> None:
        missing = [
            name for name, value in (
                ("MONGODB_URI", self.mongodb_uri),
                ("MONGODB_DATABASE", self.mongodb_database),
                ("MONGODB_COLLECTION", self.mongodb_collection),
            ) if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required MongoDB settings: {', '.join(missing)}")

    def require_openai(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to run the product agent.")
