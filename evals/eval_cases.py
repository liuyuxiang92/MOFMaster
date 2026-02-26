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
    "quick": [
        Case(
            case_id="Q01_standard_stability",
            title="Standard stability workflow",
            prompt="I have qmof-8b5bb88. Please optimize its geometry and compute the energy.",
            messages=None,
            expectation="Standard workflow: fetch_structure → optimize_geometry → static_calculation.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="Q02_lookup_only",
            title="Lookup only — no calculations",
            prompt=(
                "Retrieve the structure of qmof-8b5bb88 and tell me its chemical formula. "
                "Do not run any calculations."
            ),
            messages=None,
            expectation="Plan should be [fetch_structure] only.",
            desired_workflow=["fetch_structure"],
        ),
        Case(
            case_id="Q03_bandgap_prediction",
            title="Bandgap prediction",
            prompt="What is the predicted electronic bandgap of qmof-8b5bb88?",
            messages=None,
            expectation="Plan should be fetch_structure → predict_bandgap.",
            desired_workflow=["fetch_structure", "predict_bandgap"],
        ),
        Case(
            case_id="Q04_out_of_scope_md",
            title="Out-of-scope: molecular dynamics",
            prompt="Run a 10 ns molecular dynamics simulation at 300 K for a Zr-based MOF.",
            messages=None,
            expectation="MD is not supported; should return out_of_scope.",
            desired_workflow=[],
        ),
        Case(
            case_id="Q05_need_context_no_id",
            title="Need context — no structure identifier provided",
            prompt="Optimize a copper-based MOF and compute its energy.",
            messages=None,
            expectation=(
                "No QMOF ID or CIF path provided; analyzer must ask for one (need_context)."
            ),
            desired_workflow=[],
        ),
    ],
    "full": [
        # --- fetch_structure workflows ---
        Case(
            case_id="Q01_standard_stability",
            title="Standard stability workflow",
            prompt="I have qmof-8b5bb88. Please optimize its geometry and compute the energy.",
            messages=None,
            expectation="fetch_structure → optimize_geometry → static_calculation.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="Q02_lookup_only",
            title="Lookup only — no calculations",
            prompt=(
                "Retrieve the structure of qmof-8b5bb88 and tell me its chemical formula. "
                "Do not run any calculations."
            ),
            messages=None,
            expectation="Plan should be [fetch_structure] only.",
            desired_workflow=["fetch_structure"],
        ),
        Case(
            case_id="F03_no_optimization",
            title="Non-optimized energy — user explicitly skips relaxation",
            prompt=(
                "For qmof-8b5bb88, give me a quick energy estimate on the as-fetched structure. "
                "Do not relax the geometry first."
            ),
            messages=None,
            expectation=(
                "User explicitly skips optimization; plan should be "
                "fetch_structure → static_calculation (no optimize_geometry)."
            ),
            desired_workflow=["fetch_structure", "static_calculation"],
        ),
        Case(
            case_id="F04_optimize_only",
            title="Optimization only — no energy step",
            prompt=(
                "Fetch qmof-8b5bb88 and relax the geometry. "
                "I only need the optimized structure, not the energy."
            ),
            messages=None,
            expectation="Plan should be fetch_structure → optimize_geometry (no static_calculation).",
            desired_workflow=["fetch_structure", "optimize_geometry"],
        ),
        Case(
            case_id="Q03_bandgap_prediction",
            title="Bandgap prediction",
            prompt="What is the predicted electronic bandgap of qmof-8b5bb88?",
            messages=None,
            expectation="Plan should be fetch_structure → predict_bandgap.",
            desired_workflow=["fetch_structure", "predict_bandgap"],
        ),
        Case(
            case_id="F06_bandgap_after_optimization",
            title="Bandgap prediction after geometry optimization",
            prompt=(
                "For qmof-8b5bb88, first relax the geometry to get a well-prepared structure, "
                "then predict the electronic bandgap."
            ),
            messages=None,
            expectation="Plan should be fetch_structure → optimize_geometry → predict_bandgap.",
            desired_workflow=["fetch_structure", "optimize_geometry", "predict_bandgap"],
        ),
        # --- parse_structure workflows (user-provided CIF) ---
        Case(
            case_id="F07_user_cif_full_workflow",
            title="User provides CIF path — full stability workflow",
            prompt=(
                "I have a CIF file at /data/my_mof.cif. "
                "Please parse it, optimize the geometry, and compute the energy."
            ),
            messages=None,
            expectation=(
                "User provides CIF path; plan should be "
                "parse_structure → optimize_geometry → static_calculation."
            ),
            desired_workflow=["parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="F08_user_cif_optimize_only",
            title="User provides CIF path — optimization only",
            prompt=(
                "Relax the structure in /home/user/mof.cif. "
                "I only want the relaxed structure, not an energy calculation."
            ),
            messages=None,
            expectation="Plan should be parse_structure → optimize_geometry.",
            desired_workflow=["parse_structure", "optimize_geometry"],
        ),
        # --- Need context ---
        Case(
            case_id="Q05_need_context_no_id",
            title="Need context — no structure identifier provided",
            prompt="Optimize a copper-based MOF and compute its energy.",
            messages=None,
            expectation="No QMOF ID or CIF path; analyzer must ask for one (need_context).",
            desired_workflow=[],
        ),
        Case(
            case_id="F10_need_context_cif_no_path",
            title="Need context — CIF mentioned but no path given",
            prompt="Please calculate the energy for the MOF structure in my CIF file.",
            messages=None,
            expectation="CIF file mentioned but path not provided; analyzer must ask for it.",
            desired_workflow=[],
        ),
        # --- Out of scope ---
        Case(
            case_id="Q04_out_of_scope_md",
            title="Out-of-scope: molecular dynamics",
            prompt="Run a 10 ns molecular dynamics simulation at 300 K for a Zr-based MOF.",
            messages=None,
            expectation="MD is not supported; should return out_of_scope.",
            desired_workflow=[],
        ),
        Case(
            case_id="F12_electronic_properties_fallback",
            title="Electronic properties: full band structure out of scope, bandgap in scope",
            prompt=(
                "Compute the band structure and density of states for qmof-8b5bb88. "
                "If that is not possible, do whatever you can to characterize the electronic properties."
            ),
            messages=None,
            expectation=(
                "Full band structure / DOS is out of scope. "
                "predict_bandgap is in-scope and should be the fallback."
            ),
            desired_workflow=None,
            acceptable_workflows=[
                ["fetch_structure", "predict_bandgap"],
                ["fetch_structure", "optimize_geometry", "predict_bandgap"],
            ],
        ),
    ],
    "scenario": [
        Case(
            case_id="S01_multiturn_id_in_second_turn",
            title="Multi-turn: QMOF ID provided in follow-up",
            prompt=None,
            messages=[
                {"role": "user", "content": "I want to assess the stability of a MOF."},
                {"role": "assistant", "content": "Please provide a QMOF ID or a CIF file path."},
                {"role": "user", "content": "Use qmof-8b5bb88. Run the standard stability workflow."},
            ],
            expectation="fetch_structure → optimize_geometry → static_calculation.",
            desired_workflow=["fetch_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="S02_multiturn_cif_path",
            title="Multi-turn: CIF path provided in follow-up",
            prompt=None,
            messages=[
                {"role": "user", "content": "I want to optimize a local MOF structure."},
                {"role": "assistant", "content": "Please share the CIF file path."},
                {"role": "user", "content": "Use /home/user/HKUST-1.cif, optimize and compute the energy."},
            ],
            expectation="parse_structure → optimize_geometry → static_calculation.",
            desired_workflow=["parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="S03_contradictory_constraint",
            title="Contradiction: energy required but computation forbidden",
            prompt=(
                "Compute the energy and max force of qmof-8b5bb88, "
                "but do NOT run any computation on it."
            ),
            messages=None,
            expectation=(
                "Request is contradictory — energy requires computation. "
                "Should ask for clarification (need_context) or explain impossibility."
            ),
            desired_workflow=[],
        ),
        Case(
            case_id="S04_budget_one_step",
            title="Budget: at most one computational step",
            prompt=(
                "For qmof-8b5bb88, you may run at most ONE computational step total. "
                "Choose the most informative option."
            ),
            messages=None,
            expectation="Should choose exactly one step after fetch_structure.",
            desired_workflow=None,
            acceptable_workflows=[
                ["fetch_structure", "optimize_geometry"],
                ["fetch_structure", "static_calculation"],
                ["fetch_structure", "predict_bandgap"],
            ],
        ),
        Case(
            case_id="S05_late_constraint",
            title="Late constraint: user forbids computation after initial request",
            prompt=None,
            messages=[
                {"role": "user", "content": "Assess the stability of qmof-8b5bb88."},
                {"role": "user", "content": "Actually, don't run any calculations. Just fetch the structure."},
            ],
            expectation="Should comply with the latest constraint: [fetch_structure] only.",
            desired_workflow=["fetch_structure"],
        ),
    ],
    "scenario_hard": [
        Case(
            case_id="H01_multiturn_soft_constraints_then_deadline",
            title="Soft constraints + tight deadline (multi-turn)",
            prompt=None,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "I'm preparing a one-page figure for a MOF paper draft. I need a Zr-based framework example that's likely robust. "
                        "Please proceed with a workflow that you can justify scientifically."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "I only have ~5 minutes wall-time; choose a path that is informative but not wasteful."
                    ),
                },
            ],
            expectation=(
                "Should keep tool usage minimal (often search only, or single-candidate workflow if justified) and explain limitations in the final report."
            ),
            desired_workflow=None,
            acceptable_workflows=[["fetch_structure"], ["fetch_structure", "parse_structure", "optimize_geometry"]],
        ),
        Case(
            case_id="H02_multiturn_typo_and_disambiguation",
            title="Name typo + disambiguation (multi-turn)",
            prompt=None,
            messages=[
                {
                    "role": "user",
                    "content": "I need a quantitative proxy for how well-prepared a UiO-66 (Zr) structure is.",
                },
                {
                    "role": "user",
                    "content": (
                        "Please (1) find a UiO-66 structure, (2) relax it, and (3) compute the energy and maximum force your system provides. "
                        "Be explicit about limitations and only use tool outputs."
                    ),
                },
            ],
            expectation=(
                "Should map the name to a good search query (UiO-66) and choose an appropriate minimal workflow to support a stability proxy."
            ),
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H03_constraints_conflict_no_numbers_but_winner",
            title="Conflict: no numbers, still wants a winner",
            prompt=(
                "Between two copper-based MOFs, tell me which is more stable and give me a clear winner, but do not compute or report any numbers. "
                "Also, do not use external knowledge outside your tool outputs."
            ),
            messages=None,
            expectation=(
                "Should ask a clarification question or explain it's not possible to justify a winner under these constraints."
            ),
            desired_workflow=[],
        ),
        Case(
            case_id="H04_multiobjective_rank_then_explain_tradeoffs",
            title="Multiobjective ranking with tradeoffs",
            prompt=(
                "I care about: (1) robustness/stability, (2) large pores, (3) not being an obscure structure. "
                "Use your database/tool outputs only (no external knowledge): first search for well-known Zr-based UiO-type MOFs, "
                "then give a defensible recommendation; if needed, pick ONE candidate for a stability proxy."
            ),
            messages=None,
            expectation=(
                "Should search, then either justify a single pick with minimal compute or clearly explain why only a shortlist is feasible."
            ),
            desired_workflow=None,
            acceptable_workflows=[["fetch_structure"], ["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"]],
        ),
        Case(
            case_id="H05_requires_context_file_unknown",
            title="Ambiguous local file reference",
            prompt=(
                "Use my CIF from last week and tell me whether the structure is sufficiently relaxed and stable."
            ),
            messages=None,
            expectation=(
                "Should request the CIF path (need_context) and not assume it exists in state."
            ),
            desired_workflow=[],
        ),
        Case(
            case_id="H06_branching_logic_without_saying_tools",
            title="Conditional workflow request (without tool hints)",
            prompt=(
                "Pick a representative Cu-based MOF and proceed. If the structure appears poorly prepared, stop early and ask me for what you need; "
                "otherwise provide the best stability proxy you can support."
            ),
            messages=None,
            expectation=(
                "Should encode a sensible default workflow; may need to explain conditionality since branching isn't explicit in tool lists."
            ),
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H07_out_of_scope_plus_fallback_no_keywords",
            title="Out-of-scope request with natural fallback",
            prompt=(
                "I need electronic properties (band gap / DOS) for HKUST-1. If that's not possible here, do whatever you can to still help me assess its stability."
            ),
            messages=None,
            expectation=(
                "Should declare electronic properties out of scope and fall back to supported workflow for stability proxy."
            ),
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H08_no_hallucination_enforced_strictly",
            title="Strict non-hallucination rule",
            prompt=(
                "If your structure search returns zero results, you must not guess any MOF names from memory. "
                "Instead ask me for a better keyword query. Now: find two Zr-based UiO-type MOFs."
            ),
            messages=None,
            expectation=(
                "If tool returns empty results, should ask for a revised search query rather than listing UiO-66/67 from general knowledge."
            ),
            desired_workflow=["fetch_structure"],
        ),
        Case(
            case_id="H09_budget_one_tool_call_only",
            title="Hard quota: one tool call only",
            prompt=(
                "I'm rate-limited: you may perform exactly ONE tool call total. "
                "Help me take the next best step toward selecting a stable copper-based MOF for follow-up computations later."
            ),
            messages=None,
            expectation=(
                "Plan should be [fetch_structure] only and the final response should clearly describe next steps without extra tool calls."
            ),
            desired_workflow=["fetch_structure"],
        ),
        Case(
            case_id="H10_prompt_noise_and_irrelevant_details",
            title="Noisy prompt with irrelevant info",
            prompt=(
                "I spilled coffee on my keyboard and my meeting is in 20 minutes. Anyway, I need a MOF example for teaching. "
                "Prefer zirconium. I want something 'stable' and easy to justify. Please proceed."
            ),
            messages=None,
            expectation=(
                "Should extract core constraints, ignore irrelevant details, and propose a minimal defensible workflow."
            ),
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H11_multi_turn_add_new_constraint_late",
            title="Late constraint: forbid heavy compute after asking for stability",
            prompt=None,
            messages=[
                {"role": "user", "content": "Pick a Cu-based MOF and evaluate its stability."},
                {
                    "role": "user",
                    "content": "New constraint: do not perform any calculations now; only tell me what you would do next and what inputs you need."
                },
            ],
            expectation=(
                "Should comply and likely choose a minimal plan or need_context; should not run a multi-step compute plan after the new constraint."
            ),
            desired_workflow=[],
        ),
        Case(
            case_id="H12_tricky_language_double_negative",
            title="Tricky language without naming operations",
            prompt=(
                "Please don't avoid doing the scientifically standard preparation step before giving me a stability proxy."
            ),
            messages=None,
            expectation=(
                "Should interpret as: do the standard preparation before stability proxy (likely implies the normal workflow ordering)."
            ),
            desired_workflow=[],
        ),
    ],

    # Small targeted suite for diagnosing provider filtering on the UiO-66 stability prompt.
    # Not included in the default "all" suite.
    "h02_variants": [
        Case(
            case_id="H02a_uio66_energy_proxy",
            title="UiO-66: explicit energy/force proxy wording",
            prompt=None,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Please retrieve the MOF structure for UiO-66 (zirconium framework) and follow the standard toolchain: "
                        "geometry optimization then energy/max-force evaluation. Report what you can from tool outputs."
                    ),
                }
            ],
            expectation="Should plan fetch_structure -> parse_structure -> optimize_geometry -> static_calculation.",
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H02b_uio66_relax_then_evaluate",
            title="UiO-66: neutral 'relax then evaluate' phrasing",
            prompt=None,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "I need a quantitative proxy for how well-prepared a UiO-66 (Zr) structure is. "
                        "Please (1) find a UiO-66 structure, (2) relax it, and (3) compute the energy and maximum force your system provides."
                    ),
                }
            ],
            expectation="Should plan fetch_structure -> parse_structure -> optimize_geometry -> static_calculation.",
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
        Case(
            case_id="H02c_uio66_two_turn_no_stability_word",
            title="UiO-66: two-turn, avoids 'stability' word",
            prompt=None,
            messages=[
                {"role": "user", "content": "Use UiO-66 (Zr)."},
                {
                    "role": "user",
                    "content": (
                        "Please use the standard supported workflow to generate a defensible numerical proxy from your tools "
                        "(relaxation first, then energy/forces)."
                    ),
                },
            ],
            expectation="Should plan fetch_structure -> parse_structure -> optimize_geometry -> static_calculation.",
            desired_workflow=["fetch_structure", "parse_structure", "optimize_geometry", "static_calculation"],
        ),
    ],
}


def _build_all_cases() -> list[Case]:
    """Concatenate suites from simple -> hard, deduplicating by case_id."""
    order = ["quick", "full", "scenario", "scenario_hard"]
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
