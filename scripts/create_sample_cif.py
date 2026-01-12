"""Script to create a sample CIF file for testing."""

from pathlib import Path
import ase
from ase import Atoms
from ase.io import write


def create_sample_mof():
    """Create a simple sample MOF structure for testing."""
    # Create a simple cubic structure (e.g., MOF-5-like)
    # This is a minimal example - in production, you'd load real MOF structures
    
    # Simple cubic unit cell with a few atoms
    atoms = Atoms(
        symbols=['Zn', 'O', 'C', 'C', 'H', 'H'],
        positions=[
            [0.0, 0.0, 0.0],      # Zn
            [2.0, 0.0, 0.0],      # O
            [4.0, 0.0, 0.0],      # C
            [6.0, 0.0, 0.0],      # C
            [4.0, 1.0, 0.0],      # H
            [4.0, -1.0, 0.0],     # H
        ],
        cell=[10.0, 10.0, 10.0],
        pbc=True
    )
    
    return atoms


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample CIF files
    sample_mof = create_sample_mof()
    
    # Save as HKUST-1.cif (sample)
    hkust_path = data_dir / "HKUST-1.cif"
    write(str(hkust_path), sample_mof, format="cif")
    print(f"Created sample CIF file: {hkust_path}")
    
    # Save as MOF-5.cif (sample)
    mof5_path = data_dir / "MOF-5.cif"
    write(str(mof5_path), sample_mof, format="cif")
    print(f"Created sample CIF file: {mof5_path}")

