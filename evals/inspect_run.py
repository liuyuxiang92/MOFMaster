#!/usr/bin/env python3
"""Inspect failures (or a specific case) from an eval run directory.

Usage:
  # Show all failures in a run
  uv run python evals/inspect.py data/evals/run_YYYYMMDD_HHMMSS

  # Show details for a specific case
  uv run python evals/inspect.py data/evals/run_YYYYMMDD_HHMMSS Q01_standard_stability
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _print_case(item: dict[str, Any]) -> None:
    case_id = item.get("case_id", "")
    title = item.get("title", "")
    passed = item.get("passed")
    result_str = "PASS" if passed is True else ("FAIL" if passed is False else "?")
    desired = item.get("desired_workflow")
    actual = item.get("plan")
    approved = item.get("approved")
    reason = item.get("reason", "")

    print(f"\n── {case_id} {'─' * max(0, 60 - len(case_id))}")
    print(f"Title:     {title}")
    print(f"Result:    {result_str}")
    print(f"Expected:  {desired}")
    print(f"Actual:    {actual}")
    print(f"Approved:  {approved}")
    print(f"Reason:    {reason}")

    # Try to show LLM output preview from last_ai_preview field
    last_ai = item.get("last_ai_preview")
    if last_ai:
        print(f"\nLLM Output Preview:")
        for line in last_ai.splitlines():
            print(f"  {line}")


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: inspect.py <run_dir> [case_id]")

    run_dir = Path(sys.argv[1])
    case_filter = sys.argv[2] if len(sys.argv) >= 3 else None

    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"Missing {summary_path}")

    summary = _read_json(summary_path)
    if not isinstance(summary, list):
        raise SystemExit("summary.json must be a list")

    if case_filter:
        items = [item for item in summary if item.get("case_id") == case_filter]
        if not items:
            raise SystemExit(f"No case found with case_id={case_filter!r}")
    else:
        items = [item for item in summary if not item.get("passed")]

    if not items:
        print(f"No failures in {run_dir}")
        return 0

    label = f"case {case_filter}" if case_filter else "failures"
    print(f"Run: {run_dir}  ({label})")

    for item in items:
        _print_case(item)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
