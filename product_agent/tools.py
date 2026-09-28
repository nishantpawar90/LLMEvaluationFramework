from __future__ import annotations

from typing import Any

from deepeval.tracing import observe
from langchain_core.tools import tool

from .mongo_client import MongoProductRepository, ProductNotFoundError, validate_upc


def _value(product: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value: Any = product
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value not in (None, "", [], {}):
            return value
    return None


def product_facts(product: dict[str, Any]) -> dict[str, Any]:
    """Maps likely source variations to stable business labels without inventing data."""
    mappings = {
        "product_name": ("itemDesc.internetItemDsc", "itemDesc.retailItemDsc", "productName", "itemDescription"),
        "brand": ("brandNm", "brandName"),
        "size": ("itemDimensions.size", "size", "netWeight"),
        "product_group": ("productGroup.productGroupNm",),
        "category": ("productCategory.productCategoryNm", "category"),
        "class": ("productClass.productClassNm",),
        "subclass_level_1": ("productSubClassLevel1.productSubClassLevel1Nm",),
        "subclass_level_2": ("productSubClassLevel2.productSubClassLevel2Nm",),
        "review_eligibility": ("reviewsEligibility.isReviewWriteEligible", "reviewEligibility"),
    }
    facts = {label: _value(product, *paths) for label, paths in mappings.items()}
    dsd = _value(product, "itemSourcingType.dsdInd")
    warehouse = _value(product, "itemSourcingType.warehouseInd")
    facts["sourcing"] = "DSD supplied" if dsd == "Y" else "Warehouse supplied" if warehouse == "Y" else None
    facts["upc"] = str(_value(product, "upcId") or "")
    return facts


def make_product_tools(repository: MongoProductRepository):
    def fetch(upc: str) -> dict[str, Any]:
        try:
            return {"found": True, "product": product_facts(repository.find_by_upc(upc))}
        except ValueError as exc:
            return {"found": False, "error": str(exc)}
        except ProductNotFoundError:
            return {"found": False, "error": "Product not found."}
        except ConnectionError as exc:
            return {"found": False, "error": str(exc)}

    @tool
    @observe(type="tool")
    def get_product_by_upc(upc: str) -> dict[str, Any]:
        """Get a product's general facts, or multiple requested facts, by UPC."""
        return fetch(upc)

    @tool
    @observe(type="tool")
    def get_product_review_eligibility(upc: str) -> dict[str, Any]:
        """Get customer review eligibility for a product by UPC."""
        result = fetch(upc)
        if result["found"]:
            result["product"] = {"review_eligibility": result["product"]["review_eligibility"]}
        return result

    @tool
    @observe(type="tool")
    def get_product_classification(upc: str) -> dict[str, Any]:
        """Get category, group, class, and subclasses for a product by UPC."""
        result = fetch(upc)
        if result["found"]:
            p = result["product"]
            result["product"] = {key: p[key] for key in ("product_group", "category", "class", "subclass_level_1", "subclass_level_2")}
        return result

    @tool
    @observe(type="tool")
    def get_product_dimensions(upc: str) -> dict[str, Any]:
        """Get the product size or dimensions by UPC."""
        result = fetch(upc)
        if result["found"]:
            result["product"] = {"size": result["product"]["size"]}
        return result

    @tool
    @observe(type="tool")
    def get_product_sourcing(upc: str) -> dict[str, Any]:
        """Get whether a product is warehouse or DSD supplied by UPC."""
        result = fetch(upc)
        if result["found"]:
            result["product"] = {"sourcing": result["product"]["sourcing"]}
        return result

    return [get_product_by_upc, get_product_review_eligibility, get_product_classification, get_product_dimensions, get_product_sourcing]
