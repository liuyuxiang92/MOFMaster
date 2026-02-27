#!/usr/bin/env python3
"""Batch-evaluate the MOF-Scientist analyzer via the running LangServe endpoint.

Usage:
  uv run python evals/analyzer_eval.py --out data/evals
  uv run python evals/analyzer_eval.py --base-url http://localhost:8000 --out data/evals --cases quick

This script is intentionally lightweight: it sends prompts, saves raw JSON responses,
then prints a short summary focusing on analyzer/supervisor behavior.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from evals.eval_cases import Case, CASES  # noqa: F401 — re-exported for backwards compat


def _safe_filename(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)[:120]


def _extract_plan(resp: dict[str, Any]) -> list[str] | None:
    output = resp.get("output")
    if isinstance(output, dict):
        plan = output.get("plan")
        if isinstance(plan, list) and all(isinstance(x, str) for x in plan):
            return plan
    return None


def _extract_last_ai_message(resp: dict[str, Any]) -> str | None:
    output = resp.get("output")
    if not isinstance(output, dict):
        return None
    messages = output.get("messages")
    if not isinstance(messages, list):
        return None
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("type") == "ai":
            content = msg.get("content")
            if isinstance(content, str):
                return content
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--path", default="/mof-scientist/invoke")
    parser.add_argument("--out", default="data/evals")
    parser.add_argument("--cases", choices=sorted(CASES.keys()), default="quick")
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="Run only the specified case_id(s). Can be provided multiple times.",
    )
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) / f"run_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = CASES[args.cases]
    if args.only:
        only_set = set(args.only)
        selected = [c for c in selected if c.case_id in only_set]
        if not selected:
            raise SystemExit(f"No matching cases found for --only={args.only}")

    client = httpx.Client(timeout=args.timeout)

    print(f"Base URL: {args.base_url}{args.path}")
    label = args.cases if not args.only else f"{args.cases} filtered"
    print(f"Cases: {label} ({len(selected)})")
    print(f"Output dir: {out_dir}")

    summary: list[dict[str, Any]] = []

    for idx, case in enumerate(selected, start=1):
        if case.messages is not None:
            messages = case.messages
        else:
            if not case.prompt:
                raise ValueError(f"Case {case.case_id} missing both prompt and messages")
            messages = [{"role": "user", "content": case.prompt}]

        payload = {"input": {"messages": messages}}

        try:
            r = client.post(f"{args.base_url}{args.path}", json=payload)
            r.raise_for_status()
            resp = r.json()
        except Exception as e:
            resp = {"error": str(e)}

        raw_path = out_dir / f"{idx:02d}_{case.case_id}_{_safe_filename(case.title)}.json"
        raw_path.write_text(json.dumps(resp, indent=2, ensure_ascii=False), encoding="utf-8")

        plan = _extract_plan(resp)
        approved = None
        rejection_count = None
        if isinstance(resp.get("output"), dict):
            approved = resp["output"].get("is_plan_approved")
            rejection_count = resp["output"].get("_rejection_count")

        last_ai = _extract_last_ai_message(resp)

        summary_item = {
            "case_id": case.case_id,
            "title": case.title,
            "plan": plan,
            "approved": approved,
            "rejection_count": rejection_count,
            "expectation": case.expectation,
            "desired_workflow": case.desired_workflow,
            "acceptable_workflows": case.acceptable_workflows,
            "raw": str(raw_path),
            "last_ai_preview": (last_ai[:220] + "…")
            if isinstance(last_ai, str) and len(last_ai) > 220
            else last_ai,
        }
        summary.append(summary_item)

        print(
            f"[{idx:02d}/{len(selected)}] {case.case_id}: plan={plan} approved={approved} raw={raw_path.name}"
        )

    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\nWrote:")
    print(f"- {out_dir / 'summary.json'}")
    print("- per-case raw JSON responses")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
