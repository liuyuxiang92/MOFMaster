"""MOF database search functionality."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


# MVP: Simple JSON-based MOF database
# In production, this would be replaced with a vector database
_MOF_DB_PATH = Path(__file__).parent.parent.parent / "data" / "mof_database.json"


def _load_mof_db() -> List[Dict[str, Any]]:
    """Load the MOF database from JSON file."""
    if not _MOF_DB_PATH.exists():
        # Create a sample database if it doesn't exist
        _MOF_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        sample_db = [
            {
                "mof_name": "HKUST-1",
                "cif_filename": "HKUST-1.cif",
                "properties": {
                    "metal": "copper",
                    "linker": "BTC",
                    "space_group": "Fm-3m",
                    "description": "Copper-based MOF with benzene-1,3,5-tricarboxylate linker"
                }
            },
            {
                "mof_name": "MOF-5",
                "cif_filename": "MOF-5.cif",
                "properties": {
                    "metal": "zinc",
                    "linker": "BDC",
                    "space_group": "Fm-3m",
                    "description": "Zinc-based MOF with benzene-1,4-dicarboxylate linker"
                }
            }
        ]
        with open(_MOF_DB_PATH, "w") as f:
            json.dump(sample_db, f, indent=2)
        return sample_db
    
    with open(_MOF_DB_PATH, "r") as f:
        return json.load(f)


def search_mof_db(query_string: str) -> Dict[str, Any]:
    """
    Search the MOF database for structures matching the query.
    
    Args:
        query_string: Search query (e.g., "copper based", "HKUST-1")
    
    Returns:
        Dictionary containing mof_name, cif_filename, and properties
        If multiple matches, returns the first one
    """
    db = _load_mof_db()
    query_lower = query_string.lower()
    
    # Simple keyword matching (MVP)
    # Future: Use vector search or more sophisticated matching
    for mof in db:
        mof_name = mof.get("mof_name", "").lower()
        properties = mof.get("properties", {})
        description = properties.get("description", "").lower()
        metal = properties.get("metal", "").lower()
        
        if (query_lower in mof_name or 
            query_lower in description or 
            query_lower in metal):
            return mof
    
    # If no match found, return a default structure
    return {
        "mof_name": "Not Found",
        "cif_filename": None,
        "properties": {
            "error": f"No MOF found matching '{query_string}'"
        }
    }

