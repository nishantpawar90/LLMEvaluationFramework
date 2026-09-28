"""Run the existing DeepEval cases as isolated Python processes."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


EVALUATION_DIRECTORY = Path(__file__).resolve().parent / "myEvaluations"
PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]


def discover_cases() -> list[Path]:
    """Return the runnable Python files in the myEvaluations directory."""
    return sorted(
        path
        for path in EVALUATION_DIRECTORY.glob("*.py")
        if path.name != "__init__.py"
    )


def run_case(case_name: str) -> subprocess.CompletedProcess[str]:
    """Run one known case without importing it into the test runner."""
    cases = {path.name: path for path in discover_cases()}
    if case_name not in cases:
        raise ValueError(f"Unknown evaluation case: {case_name}")

    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    current_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(PROJECT_DIRECTORY), current_python_path)
        if part
    )

    return subprocess.run(
        [sys.executable, "-u", str(cases[case_name])],
        cwd=PROJECT_DIRECTORY,
        env=environment,
        text=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the myEvaluations cases.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List available cases.")
    selection.add_argument("--run", metavar="CASE", help="Run one case by filename.")
    selection.add_argument("--all", action="store_true", help="Run every case.")
    arguments = parser.parse_args()

    if arguments.list:
        for case in discover_cases():
            print(case.name)
        return 0

    selected_cases = (
        [arguments.run]
        if arguments.run
        else [case.name for case in discover_cases()]
    )
    failed_cases = []

    for case_name in selected_cases:
        print(f"\n=== Running {case_name} ===", flush=True)
        try:
            result = run_case(case_name)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        if result.returncode != 0:
            failed_cases.append(case_name)
            print(f"FAILED: {case_name} (exit code {result.returncode})")
        else:
            print(f"PASSED: {case_name}")

    if failed_cases:
        print("\nFailed cases: " + ", ".join(failed_cases))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())