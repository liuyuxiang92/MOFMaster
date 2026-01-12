"""ASE/Pymatgen wrappers for structure optimization and energy calculations."""

from pathlib import Path
from typing import Dict, Any, Union
from ase import Atoms
from ase.optimize import BFGS
from ase.calculators.emt import EMT

# Try to import LennardJones, but it may not be available in all ASE versions
try:
    from ase.calculators.lennardjones import LennardJones
except ImportError:
    LennardJones = None

from .io import read_cif, write_cif


def optimize_structure_ase(
    cif_content: str = None,
    cif_filepath: Union[str, Path] = None,
    calculator_type: str = "EMT",
    fmax: float = 0.05,
) -> Dict[str, Any]:
    """
    Optimize a structure using ASE.
    
    Args:
        cif_content: CIF file content as string (alternative to filepath)
        cif_filepath: Path to CIF file
        calculator_type: Calculator to use ("EMT" or "LennardJones")
        fmax: Maximum force convergence criterion (eV/Å)
    
    Returns:
        Dictionary with optimized_cif_path and final_energy
    """
    # Load structure
    if cif_filepath:
        atoms = read_cif(cif_filepath)
    elif cif_content:
        # Write temporary file
        temp_path = Path("/tmp/temp_structure.cif")
        temp_path.write_text(cif_content)
        atoms = read_cif(temp_path)
    else:
        raise ValueError("Either cif_content or cif_filepath must be provided")
    
    # Initialize calculator
    if calculator_type == "EMT":
        calculator = EMT()
    elif calculator_type == "LennardJones":
        if LennardJones is None:
            raise ValueError("LennardJones calculator is not available in this ASE version. Use 'EMT' instead.")
        calculator = LennardJones()
    else:
        raise ValueError(f"Unknown calculator type: {calculator_type}")
    
    atoms.calc = calculator
    
    # Run optimization
    opt = BFGS(atoms)
    opt.run(fmax=fmax)
    
    # Save optimized structure
    original_name = Path(cif_filepath).stem if cif_filepath else "structure"
    output_dir = Path(__file__).parent.parent.parent / "data" / "optimized"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{original_name}_optimized.cif"
    
    write_cif(atoms, output_path)
    
    return {
        "optimized_cif_path": str(output_path),
        "final_energy": float(atoms.get_potential_energy()),
        "max_force": float(max([abs(f) for f in atoms.get_forces().flatten()])),
    }


def calculate_energy_force(cif_filepath: Union[str, Path], calculator_type: str = "EMT") -> Dict[str, Any]:
    """
    Calculate energy and forces for a structure (static point calculation).
    
    Args:
        cif_filepath: Path to CIF file
        calculator_type: Calculator to use ("EMT" or "LennardJones")
    
    Returns:
        Dictionary with energy_ev and max_force
    """
    # Load structure
    atoms = read_cif(cif_filepath)
    
    # Initialize calculator
    if calculator_type == "EMT":
        calculator = EMT()
    elif calculator_type == "LennardJones":
        if LennardJones is None:
            raise ValueError("LennardJones calculator is not available in this ASE version. Use 'EMT' instead.")
        calculator = LennardJones()
    else:
        raise ValueError(f"Unknown calculator type: {calculator_type}")
    
    atoms.calc = calculator
    
    # Calculate energy and forces
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    max_force = float(max([abs(f) for f in forces.flatten()]))
    
    return {
        "energy_ev": float(energy),
        "max_force": max_force,
    }

