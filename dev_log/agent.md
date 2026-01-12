# Product Requirements Document (PRD): MOF-Scientist Backend

**Version:** 1.0
**Type:** Backend API (Python)
**Frameworks:** LangGraph, LangServe, ASE (Atomic Simulation Environment)

## 1. Executive Summary

We are building a scientific workflow agent designed to democratize computational chemistry for Metal-Organic Frameworks (MOFs). The system accepts natural language queries, validates them against scientific constraints, and executes multi-step simulation workflows (Structure Search, Optimization, Energy Calculation, etc) using a deterministic agentic loop.

**Goal:** Create a robust, observable, and scientifically grounded API that acts as a "Computational Chemist" for non-expert users.

## 2. System Architecture

The system is designed as a **State Graph** (using LangGraph) exposed via a REST API (using LangServe).

**High-Level Flow:**

1. **User Request**  **Analyzer Agent** (Scopes & Plans)
2. **Plan**  **Supervisor Agent** (Validates Scientific Soundness)
* *If Rejected:* Return to Analyzer for re-planning.
* *If Approved:* Proceed to Runner.


3. **Approved Plan**  **Runner Agent** (Executes Tools Deterministically)
4. **Raw Results**  **Reporter Agent** (Synthesizes Answer)
5. **Final Report**  **User Response**

### 2.1 File Structure

```text
mof-backend/
├── .env.example                # API Keys (OpenAI, Anthropic, etc.)
├── pyproject.toml              # Poetry dependencies (langgraph, ase, pymatgen, faststream)
├── README.md                   # The "Knowledge Base" the Analyzer Agent reads
├── data/                       # Local storage for CIF structures and simulation logs
├── app/
│   ├── __init__.py
│   ├── server.py               # FastAPI + LangServe entry point
│   ├── graph.py                # Main LangGraph definition (The "Brain")
│   ├── schema.py               # Pydantic models for Input/Output
│   ├── state.py                # TypedDict definition for AgentState
│   ├── agents/                 # The Nodes
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Scope & Context validator
│   │   ├── supervisor.py       # Plan review & critique
│   │   ├── runner.py           # Tool executor (Async)
│   │   └── reporter.py         # Summary generator
│   ├── tools/                  # The Scientific Toolbelt
│   │   ├── __init__.py
│   │   ├── atomistics.py       # ASE/Pymatgen wrappers (Optimization, Energy)
│   │   ├── retrieval.py        # Vector DB search logic
│   │   └── io.py               # Reading/Writing CIF files
│   └── utils/
│       └── llm.py              # Model factory (GPT-4o, Claude 3.5)
└── tests/
    ├── unit/
    └── integration/

```

---

## 3. Data Structures (The "Memory")

### 3.1 `AgentState` Schema

This `TypedDict` is the shared memory passed between all agents.

```python
class AgentState(TypedDict):
    # Standard LangChain chat history
    messages: Annotated[list[AnyMessage], add_messages]
    
    # The original goal parsed from user input
    original_query: str
    
    # The structured plan of execution
    plan: List[str]  # e.g., ["search_mof", "optimize_structure", "calc_energy"]
    
    # Current execution status
    current_step: int
    
    # Shared dictionary for tool outputs (keys = step names)
    tool_outputs: Dict[str, Any]
    
    # Supervisor feedback
    review_feedback: str
    is_plan_approved: bool

```

---

## 4. Agent Specifications

### 4.1 Analyzer Agent (The Architect)

* **Role:** Scoping, Context Gathering, and Planning.
* **Inputs:** `messages`, `README_KNOWLEDGE.md`.
* **System Prompt:**
> "You are a computational chemistry assistant. Read the `README_KNOWLEDGE.md` to understand your capabilities.


> 1. Check if the user query is **in scope**. If not, politely refuse.
> 2. Check if you have all necessary context (e.g., if user asks 'calculate energy', do you have a structure?). If not, ask the user for it.
> 3. If ready, generate a step-by-step plan using available tools."
> 
> 


* **Outputs:** Updates `plan` in `AgentState`.

### 4.2 Supervisor Agent (The PI)

* **Role:** Quality Control and Safety.
* **Inputs:** `plan`.
* **Behavior:**
* Uses an LLM (e.g., GPT-4o) to review the plan.
* **Checks:**
* Order of operations (e.g., Optimization must happen *before* Energy calculation).
* Feasibility (e.g., Reject plans that request 'Dynamics' if only 'Static' tools are available).


* **Output Format (Structured):**
```json
{
  "approved": boolean,
  "feedback": "string explaining why"
}

```





### 4.3 Runner Agent (The Lab Tech)

* **Role:** Deterministic Execution.
* **Inputs:** `plan`, `current_step`.
* **Behavior:**
* Does **not** use an LLM to "think". It purely maps the string in `plan[current_step]` to a Python function in `app/tools/`.
* Executes the tool asynchronously.
* Saves the result to `tool_outputs`.
* Increments `current_step`.


* **Loop Logic:** Checks if `current_step < len(plan)`. If yes, repeats. If no, goes to Reporter.

### 4.4 Reporter Agent (The Author)

* **Role:** Data Synthesis.
* **Inputs:** `tool_outputs`, `original_query`.
* **Behavior:**
* Reads the raw JSON/Float outputs from the Runner.
* Generates a Markdown-formatted summary answering the original query.
* **Constraint:** Must include units (eV, Å) and cite the files created.



---

## 5. Tool Definitions (Scientific Capabilities)

These functions must be implemented in `app/tools/` and wrapped as LangChain tools.

### 5.1 `search_mof_db`

* **Input:** `query_string` (e.g., "copper based", "HKUST-1").
* **Logic:**
* (MVP) Search a local JSON/CSV file of MOF metadata.
* (Future) Vector search.


* **Output:** A JSON object containing `mof_name`, `cif_filename`, and `properties`.

### 5.2 `optimize_structure_ase`

* **Input:** `cif_content` (string) or `cif_filepath`.
* **Logic:**
* Load structure using `ase.io.read`.
* Initialize a calculator (Use `EMT` or `LennardJones` for lightweight testing; prepare hooks for `MACE`).
* Run `BFGS` optimization until `fmax < 0.05 eV/Å`.


* **Output:** Path to the `_optimized.cif` file and the final potential energy.

### 5.3 `calculate_energy_force`

* **Input:** `cif_filepath`.
* **Logic:**
* Load structure.
* Run static point calculation.


* **Output:** Dictionary `{ "energy_ev": float, "max_force": float }`.

---

## 6. API Specifications (LangServe)

The backend must expose the graph via **FastAPI** / **LangServe**.

**Base URL:** `http://localhost:8000`

### Endpoints

1. **`POST /mof-scientist/invoke`**
* **Description:** Run the full workflow (blocking).
* **Payload:** `{ "input": { "messages": [ { "role": "user", "content": "..." } ] } }`


2. **`POST /mof-scientist/stream`**
* **Description:** Stream events (essential for frontend visibility).
* **Events:** `on_chat_model_start`, `on_tool_start`, `on_tool_end`.



---

## 7. Development Roadmap (For the Coder)

**Phase 1: Skeleton & State**

* Initialize project with Poetry.
* Define `AgentState` in `state.py`.
* Create `graph.py` with dummy nodes (print statements only) to verify the flow `Analyzer -> Supervisor -> Runner`.

**Phase 2: The Brains (Analyzer + Supervisor)**

* Implement `analyzer.py` with the `README` context loading.
* Implement `supervisor.py` using structured outputs (Pydantic).
* Test the loop: Verify that a bad plan gets rejected and re-planned.

**Phase 3: The Muscle (Tools + Runner)**

* Install `ase` and `pymatgen`.
* Implement `optimize_structure_ase` using the `EMT` calculator (built-in to ASE, no extra deps needed).
* Implement the `Runner` node to parse the plan strings and call these tools.

**Phase 4: API & Polish**

* Wrap `graph.compile()` in `server.py` using `add_routes`.
* Test with `curl` or the LangServe Playground (`/docs`).