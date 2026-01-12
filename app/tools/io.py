"""I/O utilities for CIF files."""

from pathlib import Path
from typing import Union
import ase.io


def read_cif(filepath: Union[str, Path]) -> "ase.Atoms":
    """
    Read a CIF file and return an ASE Atoms object.
    
    Args:
        filepath: Path to the CIF file
    
    Returns:
        ASE Atoms object
    """
    return ase.io.read(str(filepath))


def write_cif(atoms: "ase.Atoms", filepath: Union[str, Path]) -> Path:
    """
    Write an ASE Atoms object to a CIF file.
    
    Args:
        atoms: ASE Atoms object
        filepath: Path where to write the CIF file
    
    Returns:
        Path to the written file
    """
    filepath = Path(filepath)
    ase.io.write(str(filepath), atoms, format="cif")
    return filepath

