# MOFMaster

MOFMaster is a modular multi-agent framework for metal–organic framework (MOF) research, integrating literature understanding, computational modeling, and extensible experiment interfaces. It is designed to orchestrate reading agents, calculation agents, and future experiment agents within a unified, extensible architecture.

## MOF-Scientist Backend

This backend provides a scientific workflow agent designed to democratize computational chemistry for Metal-Organic Frameworks (MOFs). The system accepts natural language queries, validates them against scientific constraints, and executes multi-step simulation workflows.

### Capabilities

The system can perform the following operations:

1. **Structure Search**: Search for MOF structures in the database using natural language queries (e.g., "copper based MOF", "HKUST-1")

2. **Structure Optimization**: Optimize MOF structures using ASE (Atomic Simulation Environment) with various calculators:
   - EMT (Effective Medium Theory) - lightweight, fast
   - Lennard-Jones - for testing
   - Future: MACE and other advanced calculators

3. **Energy Calculation**: Calculate potential energy and forces for MOF structures

### Workflow

The system uses a multi-agent architecture:

1. **Analyzer Agent**: Scopes the query, checks context, and generates a plan
2. **Supervisor Agent**: Validates the plan for scientific soundness
3. **Runner Agent**: Executes tools deterministically
4. **Reporter Agent**: Synthesizes results into a final report

### Installation

```bash
# Install dependencies using Poetry
poetry install

# Copy environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Usage

```bash
# Start the server
poetry run python -m app.server

# Or using uvicorn directly
poetry run uvicorn app.server:app --reload
```

The API will be available at:
- API Documentation: http://localhost:8000/docs
- LangServe Playground: http://localhost:8000/mof-scientist/playground
- Invoke endpoint: POST http://localhost:8000/mof-scientist/invoke
- Stream endpoint: POST http://localhost:8000/mof-scientist/stream

### Example Request

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

### Data Directory

The system uses a `data/` directory for:
- MOF database (`data/mof_database.json`)
- CIF structure files (`data/*.cif`)
- Optimized structures (`data/optimized/*_optimized.cif`)
- Simulation logs

### Scientific Tools

Available tools:
- `search_mof_db(query_string)`: Search MOF database
- `optimize_structure_ase(cif_filepath)`: Optimize structure using ASE
- `calculate_energy_force(cif_filepath)`: Calculate energy and forces

### Notes

- The system uses deterministic execution for reproducibility
- All energy values are in eV, distances in Å
- Structures are saved as CIF files
- The system validates plan order (e.g., optimization before energy calculation)
