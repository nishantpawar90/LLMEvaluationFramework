from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from product_agent.evaluation import runner


def test_cases_are_discovered_from_my_evaluations() -> None:
    cases = runner.discover_cases()

    assert cases
    assert all(case.parent == runner.EVALUATION_DIRECTORY for case in cases)
    assert all(case.name != "__init__.py" for case in cases)


def test_unknown_case_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown evaluation case"):
        runner.run_case("../not_a_case.py")


def test_case_runs_in_project_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    case = runner.discover_cases()[0]
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setenv("PYTHONPATH", "existing-path")

    result = runner.run_case(case.name)

    assert result.returncode == 0
    assert captured["command"][:2] == [runner.sys.executable, "-u"]
    assert captured["cwd"] == runner.PROJECT_DIRECTORY
    assert str(runner.PROJECT_DIRECTORY) in str(captured["env"]["PYTHONPATH"])
    assert "existing-path" in str(captured["env"]["PYTHONPATH"])


@pytest.mark.parametrize(
    "case",
    runner.discover_cases(),
    ids=lambda case: case.stem,
)
@pytest.mark.skipif(
    os.getenv("RUN_EVALUATIONS") != "1",
    reason="Set RUN_EVALUATIONS=1 to run cases that may call external services.",
)
def test_existing_evaluation_case(case: Path) -> None:
    result = runner.run_case(case.name)

    assert result.returncode == 0, f"{case.name} exited with {result.returncode}"