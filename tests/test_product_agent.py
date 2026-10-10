"""Product-agent checks.

Pytest collects this file because the name starts with test_.
Pytest runs each function below because the name starts with test_.
"""

import pytest
from deepeval import assert_test

from product_agent.evaluation.cases import build_test_case
from product_agent.evaluation.metrics import build_metrics

pytestmark = pytest.mark.evaluation


def _check_product_answer(agent, evaluation_dataset, settings, name: str) -> None:
    """Run one saved product question. Pytest ignores this helper: the name does not start with test_."""
    golden = next(item for item in evaluation_dataset.goldens if item.name == name)
    result = agent.run(golden.input)
    assert_test(
        build_test_case(golden, result),
        metrics=build_metrics(settings),
        run_async=False,
    )


def test_basic_lookup(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "basic_lookup")


def test_size(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "size")


def test_category(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "category")


def test_classification(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "classification")


def test_reviews(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "reviews")


def test_sourcing(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "sourcing")


def test_multiple_attributes(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "multiple_attributes")


def test_summary(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "summary")


def test_group(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "group")


def test_subclass_1(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "subclass_1")


def test_subclass_2(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "subclass_2")


def test_concise_size(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "concise_size")


def test_unknown_upc(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "unknown_upc")
