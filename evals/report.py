#!/usr/bin/env python3
"""Render a clean eval report from a run directory's summary.json.

Usage:
  uv run python evals/report.py data/evals/run_YYYYMMDD_HHMMSS
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _plan_str(plan: Any) -> str:
    if not isinstance(plan, list) or len(plan) == 0:
        return "[]"
    return " → ".join(plan)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: report.py <run_dir>")

    run_dir = Path(sys.argv[1])
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"Missing {summary_path}")

    summary = _read_json(summary_path)
    if not isinstance(summary, list):
        raise SystemExit("summary.json must be a list")

    run_name = run_dir.name
    total = len(summary)

    lines: list[str] = []
    lines.append(f"MOFMaster Eval Report — {run_name}  ({total} cases)")
    lines.append("━" * 80)
    lines.append(f" {'Case':<30} {'Result':<8} Plan")
    lines.append("─" * 80)

    passed_count = 0
    for item in summary:
        case_id = item.get("case_id", "")
        passed = item.get("passed")
        plan = item.get("plan", [])
        reason = item.get("reason", "")

        if passed is True:
            result_str = "PASS"
            passed_count += 1
        elif passed is False:
            result_str = "FAIL"
        else:
            result_str = "?"

        if isinstance(plan, list) and len(plan) == 0:
            plan_display = f"[] ({reason})" if reason else "[]"
        else:
            plan_display = _plan_str(plan)

        lines.append(f" {case_id:<30} {result_str:<8} {plan_display}")

    lines.append("━" * 80)
    check = "✓" if passed_count == total else "✗"
    lines.append(f"{passed_count} / {total} passed {check}")

    report_text = "\n".join(lines) + "\n"
    print(report_text, end="")

    report_path = run_dir / "report.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\nSaved: {report_path}")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
