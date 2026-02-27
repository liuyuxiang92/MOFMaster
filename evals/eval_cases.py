"""MOFMaster eval case definitions — shared by all eval scripts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    case_id: str
    title: str
    prompt: str | None
    messages: list[dict[str, str]] | None
    expectation: str
    desired_workflow: list[str] | None = None
    acceptable_workflows: list[list[str]] | None = None


CASES: dict[str, list[Case]] = {
    # -------------------------------------------------------------------------
    # 1. CORE WORKFLOWS: Testing the happy paths for valid patterns
    # -------------------------------------------------------------------------
    "quick": [
        Case(
            case_id="C01_standard_stability",
            title="Standard stability workflow",
            prompt="Could you run a standard stability check on qmof-8b5bb88?",
            messages=None,
            expectation="Standard workflow: fetch_structure → optimize_geometry → static_calculation.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="C02_lookup_only",
            title="Lookup only — no calculations",
            prompt=(
                "Could you pull the database record for qmof-8b5bb88? "
                "I just need to verify its chemical formula and exact unit cell parameters for my notes."
            ),
            messages=None,
            expectation="Plan should be [fetch_structure] only.",
            desired_workflow=["fetch_structure"],
        ),
        Case(
            case_id="C03_unrelaxed_energy",
            title="Single-point energy on raw structure",
            prompt=(
                "I need to check the baseline DFT energy of the experimental qmof-8b5bb88 structure. "
                "Can you pull it and run a single-point energy calculation on the raw coordinates?"
            ),
            messages=None,
            expectation="Plan should be fetch_structure → static_calculation.",
            desired_workflow=["fetch_structure", "static_calculation"],
        ),
        Case(
            case_id="C04_relax_only",
            title="Optimization only — export clean geometry",
            prompt=(
                "I'm preparing a 3D visualization of qmof-8b5bb88 for a presentation. "
                "Can you fetch it and relax the coordinates so I have a clean, physically sound geometry to export?"
            ),
            messages=None,
            expectation="Plan should be fetch_structure → optimize_geometry.",
            desired_workflow=["fetch_structure", "optimize_geometry"],
        ),
        Case(
            case_id="C05_bandgap_quick",
            title="Quick bandgap prediction",
            prompt="Can you give me a quick estimate of the bandgap for qmof-8b5bb88?",
            messages=None,
            expectation="Plan should be fetch_structure → predict_bandgap.",
            desired_workflow=["fetch_structure", "predict_bandgap"],
        ),
        Case(
            case_id="C06_bandgap_accurate",
            title="Accurate bandgap prediction (relax first)",
            prompt=(
                "Can I get an accurate bandgap prediction for qmof-8b5bb88? "
                "Make sure the structure is fully relaxed first."
            ),
            messages=None,
            expectation="Plan should be fetch_structure → optimize_geometry → predict_bandgap.",
            desired_workflow=["fetch_structure", "optimize_geometry", "predict_bandgap"],
        ),
        Case(
            case_id="C07_cif_full",
            title="User provides CIF path — full workflow",
            prompt=(
                    "I just generated a new structure in CIF format:\n\n"
                    """data_test_mof
                    _symmetry_space_group_name_H-M   'P 1'
                    _symmetry_Int_Tables_number      1
                    _cell_length_a    10.000
                    _cell_length_b    10.000
                    _cell_length_c    10.000
                    _cell_angle_alpha 90
                    _cell_angle_beta  90
                    _cell_angle_gamma 90

                    loop_
                    _symmetry_equiv_pos_as_xyz
                      'x, y, z'

                    loop_
                    _atom_site_label
                    _atom_site_type_symbol
                    _atom_site_fract_x
                    _atom_site_fract_y
                    _atom_site_fract_z
                    _atom_site_occupancy
                    Zn1   Zn   0.0000   0.0000   0.0000   1.0
                    O1    O    0.2000   0.2000   0.2000   1.0
                    O2    O    0.8000   0.8000   0.8000   1.0
                    C1    C    0.3000   0.3000   0.3000   1.0
                    C2    C    0.7000   0.7000   0.7000   1.0
                    H1    H    0.3500   0.3500   0.3500   1.0
                    H2    H    0.6500   0.6500   0.6500   1.0
                    """
                    "\nCan you relax it and get the final ground state energy?"
            ),
            messages=None,
            expectation="Plan should be parse_structure → optimize_geometry → static_calculation.",
            desired_workflow=["parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="C08_xyz_full",
            title="User provides inline XYZ — full workflow",
            prompt=(
                "I just generated a new structure in XYZ format:\n\n"
                "7\n"
                "small_test_mof converted from CIF (10x10x10 Å cubic cell)\n"
                "Zn   0.0000   0.0000   0.0000\n"
                "O    2.0000   2.0000   2.0000\n"
                "O    8.0000   8.0000   8.0000\n"
                "C    3.0000   3.0000   3.0000\n"
                "C    7.0000   7.0000   7.0000\n"
                "H    3.5000   3.5000   3.5000\n"
                "H    6.5000   6.5000   6.5000\n"
                "\nCan you relax it and get the final ground state energy?"
            ),
            messages=None,
            expectation="Plan should be parse_structure → optimize_geometry → static_calculation.",
            desired_workflow=["parse_structure", "optimize_geometry", "static_calculation"],
        ),
    ],

    # -------------------------------------------------------------------------
    # 2. MISSING CONTEXT & SCOPE: Testing boundaries, fallbacks, and clarification
    # -------------------------------------------------------------------------
    "scope_and_context": [
        Case(
            case_id="M01_missing_id",
            title="Need context — missing MOF identifier",
            prompt="Can we calculate the stability of a typical Cu-based MOF?",
            messages=None,
            expectation="Analyzer must ask for a QMOF ID or CIF path (need_context).",
            desired_workflow=[],
        ),
        Case(
            case_id="M02_missing_cif_path",
            title="Need context — CIF mentioned but no path",
            prompt="I've got a CIF file of a new synthesis candidate. Can you calculate its ground state energy?",
            messages=None,
            expectation="Analyzer must ask for the file path.",
            desired_workflow=[],
        ),
        Case(
            case_id="M03_out_of_scope_md",
            title="Out-of-scope outright rejection (MD)",
            prompt="I want to see how a typical Zr-MOF holds up at 300K. Can we run a quick 10 ns MD trajectory?",
            messages=None,
            expectation="MD is not supported; should return out_of_scope.",
            desired_workflow=[],
        ),
        Case(
            case_id="M04_fallback_dos",
            title="Out-of-scope with natural fallback (DOS -> Bandgap)",
            prompt=(
                "I need to map out the electronic properties of qmof-8b5bb88, specifically looking at the band structure and DOS. "
                "If we can't do that, what's the next best thing we can run to characterize it?"
            ),
            messages=None,
            expectation="Should declare DOS out of scope and fall back to predict_bandgap.",
            desired_workflow=["fetch_structure", "optimize_geometry", "predict_bandgap"],
            acceptable_workflows=[["fetch_structure", "predict_bandgap"]],
        ),
    ],

    # -------------------------------------------------------------------------
    # 3. COMPLEX SCENARIOS: Multi-turn, constraints, logic, and noise
    # -------------------------------------------------------------------------
    "complex_scenario": [
        Case(
            case_id="S05_noisy_prompt",
            title="Reasoning: Ignoring irrelevant noise",
            prompt=(
                "Ugh, the lab equipment is acting up and I've got a group meeting in 20 minutes. Anyway, I need a solid MOF example for my slides. "
                "Something like qmof-8b5bb88. Can you run the numbers to prove its stability?"
            ),
            messages=None,
            expectation="Should ignore the story about lab equipment and extract the core ID and stability goal.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="S06_double_negative",
            title="Reasoning: Double negative logic parsing",
            prompt=(
                "For qmof-8b5bb88, when you calculate the stability proxy, make sure you don't skip the standard structural preparation step first."
            ),
            messages=None,
            expectation="Should interpret 'don't skip preparation' as requiring optimize_geometry before static_calculation.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
    ],
}


def _build_all_cases() -> list[Case]:
    """Concatenate suites in order, deduplicating by case_id."""
    order = ["quick", "scope_and_context", "complex_scenario"]
    seen: set[str] = set()
    out: list[Case] = []
    for suite in order:
        for c in CASES[suite]:
            if c.case_id in seen:
                continue
            seen.add(c.case_id)
            out.append(c)
    return out


CASES["all"] = _build_all_cases()
