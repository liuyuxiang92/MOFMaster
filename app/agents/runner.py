"""
Runner Agent - Deterministic Tool Execution via MCP (HTTP)
"""

import os
import asyncio
import json
import logging
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

    # 1. Search tools
    if tool_name == "search_mofs":
        return {"query": original_query, "query_string": original_query}

    # 2. Parse structure tool
    elif tool_name == "parse_structure":
        # Prefer any CIF path we can find from prior tool outputs.
        cif_path = _find_cif_filepath(tool_outputs, prefer_optimized=True)

        # If the user typed a file path in the query, prefer that.
        user_path = _extract_existing_structure_path(original_query)
        data = user_path or cif_path or original_query
        return {"data": data}

    # 3. Optimization tools
    elif tool_name == "optimize_geometry":
        atoms_dict = _find_latest_atoms_dict(tool_outputs, prefer_optimized=False)
        payload: Dict[str, Any] = {}
        if atoms_dict is not None:
            payload["atoms_dict"] = atoms_dict
        return payload

    # 4. Static energy/force tools
    elif tool_name == "static_calculation":
        # Prefer optimized atoms if available, else parsed atoms.
        atoms_dict = _find_latest_atoms_dict(tool_outputs, prefer_optimized=True)
        payload: Dict[str, Any] = {}
        if atoms_dict is not None:
            payload["atoms_dict"] = atoms_dict
        return payload

    else:
        return {}


def _find_cif_filepath(tool_outputs: Dict[str, Any], prefer_optimized: bool = False) -> str:
    """
    Find a CIF filepath in the tool outputs.
    """

    optimized_path = None
    original_path = None

    # Search through outputs in order
    for key in sorted(tool_outputs.keys()):
        output = tool_outputs[key]

        if isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict):
            # Take first result from search if it matches
            first = output[0]
            if "cif_filepath" in first:
                original_path = first["cif_filepath"]
            if "optimized_cif_filepath" in first:
                optimized_path = first["optimized_cif_filepath"]

        elif isinstance(output, dict):
            if "optimized_cif_filepath" in output:
                optimized_path = output["optimized_cif_filepath"]

            if "cif_filepath" in output and not output.get("error"):
                original_path = output["cif_filepath"]

    if prefer_optimized and optimized_path:
        return optimized_path

    return optimized_path or original_path


def _find_latest_atoms_dict(tool_outputs: Dict[str, Any], prefer_optimized: bool) -> Any:
    """Find the most recent atoms_dict from parse/optimization outputs."""
    # Sort keys to follow step order (step_0_..., step_1_...)
    for key in sorted(tool_outputs.keys(), reverse=True):
        output = tool_outputs[key]
        if not isinstance(output, dict):
            continue

        if prefer_optimized and "optimized_atoms_dict" in output and output.get("optimized_atoms_dict"):
            return output.get("optimized_atoms_dict")
        if "atoms_dict" in output and output.get("atoms_dict"):
            return output.get("atoms_dict")

    return None


def _extract_existing_structure_path(text: str) -> str | None:
    """Extract an existing structure file path from user text (best-effort)."""
    import re
    from pathlib import Path

    # Common structure formats we support downstream
    pattern = r"(/[^\s]+\.(?:cif|xyz|vasp|poscar|POSCAR))"
    match = re.search(pattern, text)
    if not match:
        return None
    candidate = match.group(1)
    try:
        p = Path(candidate)
        return str(p) if p.exists() else None
    except Exception:
        return None
