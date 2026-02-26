#!/usr/bin/env python3
"""Automated MOFMaster eval — full pipeline, no HTTP server required.

Usage:
  uv run python evals/run_eval.py --cases quick
  uv run python evals/run_eval.py --cases full --out data/evals
  uv run python evals/run_eval.py --cases quick --only Q01_standard_stability
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.graph import get_compiled_graph
from evals.eval_cases import CASES, Case


@dataclass
class Result:
    case: Case
    actual_plan: list[str]
    approved: bool
    passed: bool
    reason: str
    last_ai_preview: str | None = None


def _check(case: Case, actual_plan: list[str], approved: bool) -> tuple[bool, str]:
    if case.desired_workflow == []:
        if actual_plan == [] and not approved:
            return True, "out_of_scope / need_context"
        return False, f"expected empty plan, got {actual_plan}"
    acceptable = list(case.acceptable_workflows or [])
    if case.desired_workflow is not None:
        acceptable.append(case.desired_workflow)
    if acceptable:
        if actual_plan in acceptable and approved:
            return True, f"plan={actual_plan}"
        if actual_plan not in acceptable:
            return False, f"plan_mismatch — got {actual_plan}, expected one of {acceptable}"
        return False, "plan correct but not approved by supervisor"
    return True, f"manual review (plan={actual_plan})"


def _build_init(case: Case) -> dict:
    if case.messages is not None:
        msgs = [
            HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"])
            for m in case.messages
        ]
    else:
        msgs = [HumanMessage(case.prompt)]
    return {
        "messages": msgs,
        "original_query": "",
        "plan": [],
        "current_step": 0,
        "tool_outputs": {},
        "review_feedback": "",
        "is_plan_approved": False,
        "_rejection_count": 0,
        "_previous_plan": [],
    }


def _last_ai_preview(messages: list) -> str | None:
    """Return a short preview of the last AI message, for use in inspect.py."""
    for msg in reversed(messages):
        if hasattr(msg, "content") and type(msg).__name__ == "AIMessage":
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            return (text[:220] + "…") if len(text) > 220 else text
    return None


async def _run(cases: list[Case]) -> list[Result]:
    graph = get_compiled_graph()
    results = []
    total = len(cases)
    for i, case in enumerate(cases, 1):
        final = await graph.ainvoke(_build_init(case))
        actual_plan = final.get("plan", [])
        approved = final.get("is_plan_approved", False)
        passed, reason = _check(case, actual_plan, approved)
        label = "PASS" if passed else "FAIL"
        print(f"[{i}/{total}] {case.case_id:<38} {label}  {reason}")
        results.append(Result(case, actual_plan, approved, passed, reason,
                              _last_ai_preview(final.get("messages", []))))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MOFMaster eval suite against the full pipeline.")
    parser.add_argument("--cases", choices=sorted(CASES.keys()), default="quick")
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="Run only the specified case_id(s). Can be provided multiple times.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Directory to save summary.json (optional)",
    )
    args = parser.parse_args()

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("ERROR: missing environment variable: LLM API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        return 1
    if not os.getenv("MCP_SERVER_URL"):
        print("WARNING: MCP_SERVER_URL not set — runner will use its built-in default endpoint.")
        print("         Tool execution may fail, but plan/approval checks will still work.\n")

    selected = CASES[args.cases]
    if args.only:
        selected = [c for c in selected if c.case_id in set(args.only)]
        if not selected:
            print(f"ERROR: no matching cases found for --only={args.only}")
            return 1

    print(f"\nMOFMaster Eval — suite: {args.cases}  ({len(selected)} cases)")
    print("━" * 60)
    results = asyncio.run(_run(selected))
    print("━" * 60)

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    print(f"Result: {len(passed)} / {len(results)} passed", end="")

    if args.out:
        out_dir = Path(args.out) / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = [
            {
                "case_id": r.case.case_id,
                "title": r.case.title,
                "plan": r.actual_plan,
                "approved": r.approved,
                "passed": r.passed,
                "reason": r.reason,
                "expectation": r.case.expectation,
                "desired_workflow": r.case.desired_workflow,
                "last_ai_preview": r.last_ai_preview,
            }
            for r in results
        ]
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        print(f"\nSaved: {out_dir / 'summary.json'}")

    if not failed:
        print(" ✓")
        return 0

    print(f"  ✗\n  Failed cases:")
    for r in failed:
        print(f"    • {r.case.case_id} — {r.reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
