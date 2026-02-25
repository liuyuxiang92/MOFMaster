# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MOFMaster is a multi-agent AI framework for Metal-Organic Framework (MOF) computational chemistry research. It accepts natural language queries, orchestrates multi-step computational workflows, and executes simulations via an external MCP server (Bohrium platform).

## Development Commands

```bash
# Install dependencies
uv sync

# Run server
uv run python -m app.server
# With hot reload
DEBUG=true uv run python -m app.server

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unit/test_tools.py

# Lint and format
uv run ruff check app/
uv run black app/
```

Code style: Black and Ruff with `line-length=100`, `target-version=py310`.

## Architecture

The system is a **LangGraph state machine** with four sequential agents sharing `AgentState` (defined in `app/state.py`):

1. **Analyzer** (`app/agents/analyzer.py`) — Parses user query using `README_KNOWLEDGE.md` as system prompt. Outputs JSON with a `plan` (list of tool steps) or a rejection reason. On supervisor rejection, retries with feedback.

2. **Supervisor** (`app/agents/supervisor.py`) — Reviews the plan for scientific soundness. Uses Pydantic structured output (`SupervisorReview`). Auto-approves after 3 rejections to prevent infinite loops.

3. **Runner** (`app/agents/runner.py`) — Executes one plan step per graph invocation. Connects to the Bohrium MCP server via `bohr-agent-sdk`'s `MCPClient`. Stores results in `state["tool_outputs"]` keyed as `step_{index}_{tool_name}`.

4. **Reporter** (`app/agents/reporter.py`) — Synthesizes `tool_outputs` into a final Markdown report.

Graph compilation and routing logic is in `app/graph.py` (recursion limit: 10). Conditional edges route between agents based on plan approval status and step completion.

## MCP Tools

Tools are executed remotely on the Bohrium MCP server — they are not run locally. The five tools are:
- `fetch_structure` — fetches a MOF structure from the QMOF database by ID
- `parse_structure` — parses a CIF file into an atoms dict
- `optimize_geometry` — runs ML force field geometry optimization
- `static_calculation` — runs a single-point energy/force calculation
- `predict_bandgap` — predicts the electronic bandgap of a MOF structure (eV)

Tool outputs follow a consistent schema (see `IMPLEMENTATION.md` for full details).

## API

FastAPI + LangServe server (`app/server.py`):
- `POST /mof-scientist/invoke` — blocking execution
- `POST /mof-scientist/stream` — streaming events
- `GET /mof-scientist/playground` — interactive UI

Input format: `{"input": {"messages": [{"role": "user", "content": "..."}]}}`

## LLM Configuration

`app/utils/llm.py` provides a model factory supporting OpenAI, Anthropic, and custom endpoints. Default model is `gpt-4o`. Set via `LLM_MODEL_NAME` env var.

## Required Environment Variables

Copy `.env.example` to `.env`:
```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...        # if using Anthropic models
MCP_SERVER_URL=...           # Bohrium MCP server endpoint
```

Optional:
```
LANGCHAIN_TRACING_V2=true    # enable LangSmith tracing
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=...
```

## Evaluation Scripts

`scripts/` contains tools for batch evaluation of the analyzer agent:
- `analyzer_eval.py` — runs eval harness against test cases in `data/evals/`
- `inspect_eval_run.py` — inspects individual eval run results
- `render_eval_report.py` — renders summary reports
