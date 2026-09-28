"""Load the supplied Mongo shell-style ProductUPC document into local MongoDB."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

SOURCE = Path(r"D:\DT\ProductUPC.txt")
URI = "mongodb://localhost:27017"
DATABASE = "product_agent"
COLLECTION = "ProductUPC"


def convert_dates(value: object, key: str = "") -> object:
    if isinstance(value, dict):
        return {name: convert_dates(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [convert_dates(item, key) for item in value]
    if key in {"createdDate", "modifiedDate"} and isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def load_document(path: Path = SOURCE) -> dict:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"^\s*/\*.*?\*/\s*", "", raw, count=1, flags=re.DOTALL)
    raw = re.split(r"(?m)^\s*/\*\s*\d+\s*\*/\s*$", raw, maxsplit=1)[0]
    json_text = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', raw)
    return convert_dates(json.loads(json_text))


if __name__ == "__main__":
    document = load_document()
    with MongoClient(URI, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        collection = client[DATABASE][COLLECTION]
        write = collection.replace_one({"_id": document["_id"]}, document, upsert=True)
        collection.create_index("upcId", unique=True, name="uniq_upcId")
        saved = collection.find_one(
            {"upcId": document["upcId"]},
            {"_id": 0, "upcId": 1, "itemDesc.internetItemDsc": 1, "itemDimensions.size": 1},
        )
        print({"matched": write.matched_count, "upserted": write.upserted_id is not None, "stored": saved})
