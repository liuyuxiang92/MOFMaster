"""
Runner Agent - Deterministic Tool Execution via MCP (HTTP)
"""

import os
import asyncio
import json
import logging
import re
from typing import Dict, Any, List
# Bohr Agent SDK imports
from dp.agent.client.mcp_client import MCPClient

from app.state import AgentState

# Setup logger
logger = logging.getLogger(__name__)

# Configuration for MCP server connection
# Default to remote Bohrium MCP endpoint; can be overridden via MCP_SERVER_URL env var.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://fmws1368103.bohrium.tech:50001/mcp")


async def runner_node(state: AgentState) -> AgentState:
    """
    Runner Agent - Executes tools via MCP server using bohr-agent-sdk MCPClient.
    Uses Executor and Storage objects for asynchronous job management.
    """

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_outputs = state.get("tool_outputs", {})

    # Check if we're done
    if current_step >= len(plan):
        return state

    # Get the current tool to execute
    tool_name = plan[current_step]

    logger.debug(f"Runner Agent: Connecting to MCP server at {MCP_SERVER_URL}")
    logger.debug(f"Attempting to execute tool '{tool_name}' with current_step={current_step}")

    try:
        # Determine arguments based on tool and previous outputs
        kwargs = _prepare_tool_args(tool_name, tool_outputs, state)
        
        # Executor and Storage configuration as expected by Bohr Agent SDK.
        # These are passed as dicts because they are serialized over MCP (JSON).
        # "type" maps to the drivers defined in the SDK (e.g., "local", "dispatcher").
        executor_config = {"type": "local"}
        storage_config = {"type": "local"}

        # Inject configurations into kwargs - MCPClient.call_tool(async_mode=True) extracts these.
        kwargs["executor"] = executor_config
        kwargs["storage"] = storage_config

        # Execute via Bohr Agent SDK MCPClient
        async with MCPClient(MCP_SERVER_URL) as client:
            # async_mode=True enables the submit -> query -> get_results workflow
            logger.debug(f"Runner Agent: Calling tool '{tool_name}' with arguments: {kwargs}")
            result = await client.call_tool(tool_name, kwargs, async_mode=True)
            tool_outputs[f"step_{current_step}_{tool_name}"] = _process_mcp_result(result, tool_name)

    except Exception as e:
        # Store error
        import traceback
        full_tb = traceback.format_exc()
        error_msg = str(e)
        
        # Enhanced handling for ExceptionGroup (common with anyio/mcp)
        if hasattr(e, "exceptions"):
            # Python 3.11+ ExceptionGroup
            sub_errors = []
            for se in e.exceptions:
                sub_se = f"[{type(se).__name__}] {str(se)}"
                if hasattr(se, "exceptions"): # Nested ExceptionGroups
                    sub_se += f" (Sub: {[str(sse) for sse in se.exceptions]})"
                sub_errors.append(sub_se)
            error_msg = f"{type(e).__name__}: {str(e)} -> {', '.join(sub_errors)}"
        else:
            error_msg = f"{type(e).__name__}: {str(e)}"
            
        logger.error(f"Runner Agent failed executing tool '{tool_name}': {error_msg}")
        logger.debug(f"Full stack trace:\n{full_tb}")
        tool_outputs[f"step_{current_step}_{tool_name}"] = {
            "error": error_msg, 
            "tool_name": tool_name,
            "traceback": full_tb[:500] # Include snippet of TB in state
        }

    # Update state
    state["tool_outputs"] = tool_outputs
    state["current_step"] = current_step + 1

    return state


def _process_mcp_result(result: Any, tool_name: str) -> Dict[str, Any]:
    """Helper to process MCP tool results into standard dictionary format."""
    # Bohr SDK uses .isError, but standard MCP uses .is_error; support both
    is_error = getattr(result, "is_error", False) or getattr(result, "isError", False)
    
    if is_error:
        error_text = result.content[0].text if result.content else "Unknown error"
        return {
            "error": str(error_text),
            "tool_name": tool_name
        }
    
    # Extract content - MCP results usually have a 'content' list
    if not hasattr(result, "content") or not result.content:
        return {}
        
    # Standard MCP content items have a 'text' field
    output_data = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
    
    # Try to parse if it's a string, otherwise use as is
    try:
        if isinstance(output_data, str):
            # Strip any markdown formatting if present
            cleaned_data = output_data.strip()
            if cleaned_data.startswith("```json"):
                import re
                match = re.search(r"```json\s*(\{.*?\})\s*```", cleaned_data, re.DOTALL)
                if match:
                    cleaned_data = match.group(1)
            output_data = json.loads(cleaned_data)
    except:
        pass
        
    return output_data


def _prepare_tool_args(
    tool_name: str, tool_outputs: Dict[str, Any], state: AgentState
) -> Dict[str, Any]:
    """
    Prepare arguments for tool execution.
    Handles multiple variations of tool names and argument keys.
    """
    original_query = state.get("original_query", "")

    # 1. Fetch structure tool
    if tool_name == "fetch_structure":
        mof_id = _extract_mof_id(original_query) or original_query
        return {"mof_id": mof_id}

    # 2. Parse structure tool
    elif tool_name == "parse_structure":
        # Prefer an explicit file path, then inline CIF, then inline XYZ, then raw query.
        data = (
            _extract_existing_structure_path(original_query)
            or _extract_cif_content(original_query)
            or _extract_xyz_content(original_query)
            or original_query
        )
        return {"data": data}

    # 3. Optimization tools
    elif tool_name == "optimize_geometry":
        atoms_dict = _find_latest_atoms_dict(tool_outputs, prefer_optimized=False)
        if atoms_dict is None:
            logger.warning("⚠️  optimize_geometry: no atoms_dict found in prior tool outputs")
        payload: Dict[str, Any] = {}
        if atoms_dict is not None:
            payload["atoms_dict"] = atoms_dict
        return payload

    # 4. Static energy/force tools
    elif tool_name == "static_calculation":
        # Prefer optimized atoms if available, else parsed atoms.
        atoms_dict = _find_latest_atoms_dict(tool_outputs, prefer_optimized=True)
        if atoms_dict is None:
            logger.warning("⚠️  static_calculation: no atoms_dict found in prior tool outputs")
        payload: Dict[str, Any] = {}
        if atoms_dict is not None:
            payload["atoms_dict"] = atoms_dict
        return payload

    # 5. Bandgap prediction tool
    elif tool_name == "predict_bandgap":
        atoms_dict = _find_latest_atoms_dict(tool_outputs, prefer_optimized=True)
        if atoms_dict is None:
            logger.warning("⚠️  predict_bandgap: no atoms_dict found in prior tool outputs")
        payload: Dict[str, Any] = {}
        if atoms_dict is not None:
            payload["atoms_dict"] = atoms_dict
        return payload

    else:
        return {}


def _find_latest_atoms_dict(tool_outputs: Dict[str, Any], prefer_optimized: bool) -> Any:
    """Find the most recent atoms_dict from parse/optimization outputs."""

    def _step_index(k: str) -> int:
        m = re.match(r"step_(\d+)_", k)
        return int(m.group(1)) if m else -1

    # Sort by numeric step index (descending) so step_10 sorts after step_9
    for key in sorted(tool_outputs.keys(), key=_step_index, reverse=True):
        output = tool_outputs[key]
        if not isinstance(output, dict):
            continue

        if prefer_optimized and "optimized_atoms_dict" in output and output.get("optimized_atoms_dict"):
            return output.get("optimized_atoms_dict")
        if "atoms_dict" in output and output.get("atoms_dict"):
            return output.get("atoms_dict")

    return None


def _extract_mof_id(text: str) -> str | None:
    """Extract a QMOF ID (e.g. qmof-8b5bb88) from user text."""
    match = re.search(r"\bqmof-[a-f0-9]+\b", text, re.IGNORECASE)
    return match.group(0) if match else None


def _extract_cif_content(text: str) -> str | None:
    """Extract an inline CIF block from mixed user text.

    A CIF data block always begins with 'data_<name>' at the start of a line.
    Lines are kept while they match CIF patterns; trailing English sentences are dropped.
    """
    # Find the start of a CIF data block
    start = re.search(r"(?m)^[ \t]*(data_\w)", text)
    if not start:
        return None

    cif_raw = text[start.start():].strip()
    lines = cif_raw.splitlines()

    # A line belongs to the CIF block if it matches any of these patterns:
    _cif_line = re.compile(
        r"""^\s*(?:
            data_\w       |   # block header
            loop_         |   # loop declaration
            _[a-z_]       |   # CIF tag  (_atom_site_label, etc.)
            ['"]          |   # quoted value
            \s*$              # blank line
        )""",
        re.VERBOSE,
    )
    # Also match atom-site data rows: label + element + 3 numbers
    _atom_row = re.compile(r"^\s*\w+\s+[A-Za-z]{1,2}\s+[-\d.]+\s+[-\d.]+\s+[-\d.]")

    last_cif = -1
    for i, line in enumerate(lines):
        if _cif_line.match(line) or _atom_row.match(line):
            last_cif = i

    if last_cif < 0:
        return None
    return "\n".join(lines[: last_cif + 1]).strip()


def _extract_xyz_content(text: str) -> str | None:
    """Extract an inline XYZ block from mixed user text.

    XYZ format: line 1 is the atom count (bare integer), line 2 is a free
    comment, lines 3..N+2 are 'Element  x  y  z' rows.
    """
    lines = text.splitlines()
    _atom_row = re.compile(r"^\s*[A-Za-z]{1,2}\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*$")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.isdigit():
            continue
        n_atoms = int(stripped)
        if n_atoms <= 0:
            continue
        # Need comment line (i+1) + n_atoms data lines (i+2 … i+1+n_atoms)
        end = i + 2 + n_atoms
        if end > len(lines):
            continue
        atom_lines = lines[i + 2 : end]
        if all(_atom_row.match(l) for l in atom_lines):
            return "\n".join(lines[i:end]).strip()

    return None


def _extract_existing_structure_path(text: str) -> str | None:
    """Extract a structure file path from user text (best-effort).

    Does not check whether the path exists locally — the file may live on a
    remote server (e.g. Bohrium) and only needs to be valid on that side.
    """
    # Common structure formats we support downstream
    pattern = r"(/[^\s]+\.(?:cif|xyz|vasp|poscar|POSCAR))"
    match = re.search(pattern, text)
    return match.group(1) if match else None
