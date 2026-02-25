"""
Unit tests for tools
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Stub out the dp SDK so runner.py can be imported without the package installed
for _mod in ("dp", "dp.agent", "dp.agent.client", "dp.agent.client.mcp_client"):
    sys.modules.setdefault(_mod, MagicMock())

from app.tools.io import get_data_dir, write_cif_file, read_cif_file


def test_get_data_dir():
    """Test that data directory is created"""
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert data_dir.is_dir()


def test_write_and_read_cif():
    """Test writing and reading CIF files"""
    data_dir = get_data_dir()
    test_file = data_dir / "test.cif"

    # Write file
    content = "data_test\n_cell_length_a 10.0\n"
    write_cif_file(str(test_file), content)

    # Read file
    read_content = read_cif_file(str(test_file))

    assert read_content == content

    # Cleanup
    test_file.unlink()


def test_prepare_args_search_mofs():
    """Test that _prepare_tool_args returns correct args for search_mofs"""
    from app.agents.runner import _prepare_tool_args

    state = {"original_query": "copper MOF"}
    args = _prepare_tool_args("search_mofs", {}, state)
    assert args["query"] == "copper MOF"
    assert args["query_string"] == "copper MOF"


def test_prepare_args_predict_bandgap_with_atoms():
    """Test that _prepare_tool_args picks up atoms_dict from parse_structure output"""
    from app.agents.runner import _prepare_tool_args

    atoms = {"numbers": [29], "positions": [[0, 0, 0]]}
    tool_outputs = {"step_0_parse_structure": {"atoms_dict": atoms}}
    args = _prepare_tool_args("predict_bandgap", tool_outputs, {"original_query": ""})
    assert args["atoms_dict"] == atoms


def test_prepare_args_predict_bandgap_prefers_optimized():
    """Test that predict_bandgap prefers optimized_atoms_dict over atoms_dict"""
    from app.agents.runner import _prepare_tool_args

    raw_atoms = {"numbers": [29], "positions": [[0, 0, 0]]}
    opt_atoms = {"numbers": [29], "positions": [[0.1, 0, 0]]}
    tool_outputs = {
        "step_0_parse_structure": {"atoms_dict": raw_atoms},
        "step_1_optimize_geometry": {"optimized_atoms_dict": opt_atoms},
    }
    args = _prepare_tool_args("predict_bandgap", tool_outputs, {"original_query": ""})
    assert args["atoms_dict"] == opt_atoms


def test_prepare_args_unknown_tool():
    """Test that an unknown tool name returns an empty dict without crashing"""
    from app.agents.runner import _prepare_tool_args

    args = _prepare_tool_args("nonexistent_tool", {}, {"original_query": ""})
    assert args == {}
