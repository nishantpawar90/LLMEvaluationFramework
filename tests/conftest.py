"""Shared pytest fixtures for live product-agent evaluation tests."""

import pytest

from product_agent.agent import ProductAgent
from product_agent.config import Settings
from product_agent.evaluation.dataset import build_dataset


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide one immutable configuration snapshot to the evaluation suite."""
    return Settings()


@pytest.fixture(scope="module")
def evaluation_dataset(settings: Settings):
    """Build Goldens from the configured MongoDB product once per test module."""
    return build_dataset(settings)


@pytest.fixture(scope="module")
def agent(settings: Settings):
    """Create one live agent and always close its MongoDB client afterwards."""
    product_agent = ProductAgent(settings)
    yield product_agent
    product_agent.close()
