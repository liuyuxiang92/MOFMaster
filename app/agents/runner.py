"""Runner Agent: Deterministic Execution of Tools."""

from app.state import AgentState
from app.tools import (
    search_mof_db,
    optimize_structure_ase,
    calculate_energy_force,
)
from pathlib import Path


def runner_node(state: AgentState) -> AgentState:
    """
    Runner Agent: Executes tools deterministically based on the plan.
    
    This agent does NOT use an LLM - it purely maps plan strings to Python functions.
    """
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_outputs = state.get("tool_outputs", {})
    
    if current_step >= len(plan):
        # Plan execution complete
        return state
    
    step_name = plan[current_step]
    
    # Map step names to tool functions
    tool_map = {
        "search_mof_db": search_mof_db,
        "optimize_structure_ase": optimize_structure_ase,
        "calculate_energy_force": calculate_energy_force,
    }
    
    if step_name not in tool_map:
        tool_outputs[step_name] = {
            "error": f"Unknown tool: {step_name}",
        }
        return {
            **state,
            "tool_outputs": tool_outputs,
            "current_step": current_step + 1,
        }
    
    tool_func = tool_map[step_name]
    
    # Execute the tool
    try:
        # For search_mof_db, we need to extract query from original_query
        if step_name == "search_mof_db":
            original_query = state.get("original_query", "")
            # Try to extract MOF name or query from previous outputs
            if "search_mof_db" in tool_outputs:
                # Already searched, use the result
                result = tool_outputs["search_mof_db"]
            else:
                result = tool_func(original_query)
        
        # For optimize_structure_ase, we need a CIF filepath
        elif step_name == "optimize_structure_ase":
            # Check if we have a CIF filepath from previous steps
            cif_filepath = None
            if "search_mof_db" in tool_outputs:
                search_result = tool_outputs["search_mof_db"]
                cif_filename = search_result.get("cif_filename")
                if cif_filename:
                    # Look for the CIF file in data directory
                    data_dir = Path(__file__).parent.parent.parent / "data"
                    cif_filepath = data_dir / cif_filename
                    if not cif_filepath.exists():
                        # Try to find any CIF file
                        cif_files = list(data_dir.glob("*.cif"))
                        if cif_files:
                            cif_filepath = cif_files[0]
            
            if not cif_filepath:
                # Use a default test structure or create one
                result = {
                    "error": "No CIF file found. Please provide a structure file.",
                }
            else:
                result = tool_func(cif_filepath=str(cif_filepath))
        
        # For calculate_energy_force, we need a CIF filepath
        elif step_name == "calculate_energy_force":
            cif_filepath = None
            # Check if we have an optimized structure
            if "optimize_structure_ase" in tool_outputs:
                opt_result = tool_outputs["optimize_structure_ase"]
                cif_filepath = opt_result.get("optimized_cif_path")
            elif "search_mof_db" in tool_outputs:
                search_result = tool_outputs["search_mof_db"]
                cif_filename = search_result.get("cif_filename")
                if cif_filename:
                    data_dir = Path(__file__).parent.parent.parent / "data"
                    cif_filepath = data_dir / cif_filename
            
            if not cif_filepath:
                result = {
                    "error": "No CIF file found. Please provide a structure file.",
                }
            else:
                result = tool_func(cif_filepath=str(cif_filepath))
        
        else:
            result = {"error": f"Tool {step_name} execution not implemented"}
        
        tool_outputs[step_name] = result
    
    except Exception as e:
        tool_outputs[step_name] = {
            "error": str(e),
        }
    
    # Increment step
    return {
        **state,
        "tool_outputs": tool_outputs,
        "current_step": current_step + 1,
    }

