# Setup Guide

This guide will help you set up and run the MOF-Scientist Backend.

## Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

## Installation Steps

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file from example
   cp .env.example .env
   
   # Edit .env and add your API keys:
   # OPENAI_API_KEY=your_key_here
   # or
   # ANTHROPIC_API_KEY=your_key_here
   ```

4. **Create sample data** (optional):
   ```bash
   poetry run python scripts/create_sample_cif.py
   ```
   This will create sample CIF files in the `data/` directory.

## Running the Server

```bash
# Using Poetry
poetry run python -m app.server

# Or using uvicorn directly
poetry run uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## Testing the API

### Using curl:

```bash
curl -X POST http://localhost:8000/mof-scientist/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "Search for a copper-based MOF and optimize its structure"
        }
      ]
    }
  }'
```

### Using the Playground:

Visit `http://localhost:8000/mof-scientist/playground` in your browser for an interactive interface.

### Using Python:

```bash
poetry run python example_usage.py
```

## Project Structure

```
mof-backend/
├── app/
│   ├── __init__.py
│   ├── server.py          # FastAPI + LangServe entry point
│   ├── graph.py           # Main LangGraph definition
│   ├── schema.py          # Pydantic models
│   ├── state.py           # AgentState TypedDict
│   ├── agents/            # Agent nodes
│   │   ├── analyzer.py
│   │   ├── supervisor.py
│   │   ├── runner.py
│   │   └── reporter.py
│   ├── tools/             # Scientific tools
│   │   ├── atomistics.py
│   │   ├── retrieval.py
│   │   └── io.py
│   └── utils/
│       └── llm.py         # LLM factory
├── data/                  # Data directory
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

## Troubleshooting

### API Key Issues

If you get errors about missing API keys:
- Make sure `.env` file exists and contains your API keys
- Check that the keys are correct and have proper permissions

### Missing CIF Files

If tools fail with "No CIF file found":
- Run `scripts/create_sample_cif.py` to create sample structures
- Or place your own CIF files in the `data/` directory

### Import Errors

If you get import errors:
- Make sure you're running commands with `poetry run`
- Or activate the Poetry virtual environment: `poetry shell`

## Next Steps

- Add more MOF structures to `data/mof_database.json`
- Customize calculators in `app/tools/atomistics.py`
- Extend the workflow in `app/graph.py`

