from __future__ import annotations

from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import ToolCall

from ..config import Settings
from ..mongo_client import MongoProductRepository
from ..tools import product_facts


def _present(value: object) -> str:
    return str(value) if value not in (None, "") else "not available"


def build_dataset(settings: Settings | None = None) -> EvaluationDataset:
    """Build 15 Goldens from the configured live document; never fabricate facts."""
    settings = settings or Settings()
    repository = MongoProductRepository(settings)
    try:
        facts = product_facts(repository.find_by_upc(settings.sample_upc))
    finally:
        repository.close()
    upc = facts["upc"]

    def golden(name: str, question: str, output: str, tool: str) -> Golden:
        return Golden(name=name, input=question, expected_output=output,
                      expected_tools=[ToolCall(name=tool, input_parameters={"upc": upc})])

    cases = [
        golden("basic_lookup", f"What product is UPC {upc}?", _present(facts["product_name"]), "get_product_by_upc"),
        golden("size", f"What is the size of UPC {upc}?", _present(facts["size"]), "get_product_dimensions"),
        golden("category", f"What category does UPC {upc} belong to?", _present(facts["category"]), "get_product_classification"),
        golden("classification", f"What class is UPC {upc}?", _present(facts["class"]), "get_product_classification"),
        golden("reviews", f"Is UPC {upc} eligible for customer reviews?", _present(facts["review_eligibility"]), "get_product_review_eligibility"),
        golden("sourcing", f"Is UPC {upc} DSD or warehouse supplied?", _present(facts["sourcing"]), "get_product_sourcing"),
        golden("multiple_attributes", f"Give me the product name, size and category for UPC {upc}.", f"{_present(facts['product_name'])}; {_present(facts['size'])}; {_present(facts['category'])}", "get_product_by_upc"),
        golden("summary", f"Summarize product {upc}.", _present(facts["product_name"]), "get_product_by_upc"),
        golden("brand", f"What is the brand of UPC {upc}?", _present(facts["brand"]), "get_product_by_upc"),
        golden("group", f"What product group is UPC {upc} in?", _present(facts["product_group"]), "get_product_classification"),
        golden("subclass_1", f"What is the first subclass for UPC {upc}?", _present(facts["subclass_level_1"]), "get_product_classification"),
        golden("subclass_2", f"What is the second subclass for UPC {upc}?", _present(facts["subclass_level_2"]), "get_product_classification"),
        golden("concise_size", f"Answer concisely: what is the size of UPC {upc}?", _present(facts["size"]), "get_product_dimensions"),
        golden("grounded_brand", f"What is the brand of UPC {upc}? Do not guess.", _present(facts["brand"]), "get_product_by_upc"),
        Golden(name="unknown_upc", input="Does UPC 9999999999999 exist?", expected_output="Product not found.", expected_tools=[ToolCall(name="get_product_by_upc", input_parameters={"upc": "9999999999999"})]),
    ]
    return EvaluationDataset(goldens=cases)
