"""Supervisor Agent: Quality Control and Safety."""

from app.state import AgentState
from app.schema import SupervisorReview
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor Agent: Reviews the plan for scientific soundness.
    
    Checks:
    - Order of operations (e.g., Optimization must happen before Energy calculation)
    - Feasibility (e.g., Reject plans that request unavailable tools)
    """
    plan = state.get("plan", [])
    
    if not plan:
        return {
            **state,
            "is_plan_approved": False,
            "review_feedback": "No plan provided for review.",
        }
    
    # Create system prompt with structured output format
    system_prompt = """You are a scientific supervisor reviewing computational chemistry workflows.

Available tools:
- search_mof_db: Search for MOF structures
- optimize_structure_ase: Optimize a structure (requires CIF file)
- calculate_energy_force: Calculate energy and forces (requires CIF file)

Rules:
1. Optimization must happen BEFORE energy calculation if both are in the plan
2. Structure search or file input must happen BEFORE optimization/energy calculation
3. Reject plans that request unavailable tools (e.g., "dynamics", "md_simulation")
4. Reject plans that are out of scope (e.g., synthesis, experimental work)

Review the plan: {plan}

Respond with a JSON object in this exact format:
{{
  "approved": true or false,
  "feedback": "explanation of your decision"
}}"""

    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    llm = get_llm()
    
    # Use structured output if available, otherwise parse JSON from response
    try:
        # Try to use structured output (works with OpenAI and Anthropic)
        structured_llm = llm.with_structured_output(SupervisorReview)
        chain = prompt | structured_llm
        review = chain.invoke({"plan": plan})
    except Exception:
        # Fallback: parse JSON from text response
        chain = prompt | llm
        response = chain.invoke({"plan": plan})
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                review = SupervisorReview(**data)
            except (json.JSONDecodeError, Exception):
                # Default to approved if parsing fails
                review = SupervisorReview(
                    approved=True,
                    feedback="Could not parse review, defaulting to approved."
                )
        else:
            # Default to approved if no JSON found
            review = SupervisorReview(
                approved=True,
                feedback="No structured review found, defaulting to approved."
            )
    
    return {
        **state,
        "is_plan_approved": review.approved,
        "review_feedback": review.feedback,
    }

