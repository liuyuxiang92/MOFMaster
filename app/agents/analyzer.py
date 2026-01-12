"""Analyzer Agent: Scopes, Context Gathering, and Planning."""

from pathlib import Path
from app.state import AgentState
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage


def analyzer_node(state: AgentState) -> AgentState:
    """
    Analyzer Agent: Checks scope, gathers context, and generates a plan.
    
    This agent:
    1. Checks if the user query is in scope
    2. Checks if all necessary context is available
    3. Generates a step-by-step plan using available tools
    """
    # Load README knowledge base
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    knowledge_base = ""
    if readme_path.exists():
        knowledge_base = readme_path.read_text()
    
    # Get the latest user message
    messages = state.get("messages", [])
    user_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    if not user_message:
        user_message = state.get("original_query", "")
    
    # Create system prompt
    system_prompt = """You are a computational chemistry assistant. Read the knowledge base below to understand your capabilities.

Available tools:
- search_mof_db(query_string): Search for MOF structures in the database
- optimize_structure_ase(cif_filepath): Optimize a structure using ASE
- calculate_energy_force(cif_filepath): Calculate energy and forces for a structure

Your tasks:
1. Check if the user query is **in scope**. If not, politely refuse.
2. Check if you have all necessary context (e.g., if user asks 'calculate energy', do you have a structure?). If not, ask the user for it.
3. If ready, generate a step-by-step plan using available tools.

Format your plan as a JSON list of tool names, e.g., ["search_mof_db", "optimize_structure_ase", "calculate_energy_force"]

Knowledge Base:
{knowledge_base}
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("messages"),
    ])
    
    llm = get_llm()
    chain = prompt | llm
    
    # Prepare messages for the chain
    chain_messages = messages if messages else [HumanMessage(content=user_message)]
    
    response = chain.invoke({
        "messages": chain_messages,
        "knowledge_base": knowledge_base,
    })
    
    # Extract plan from response
    # Try to parse JSON from the response
    import json
    import re
    
    plan = []
    response_text = response.content
    
    # Try to find JSON array in the response
    json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
    if json_match:
        try:
            plan = json.loads(json_match.group())
        except json.JSONDecodeError:
            # Fallback: extract tool names from text
            if "search_mof" in response_text.lower():
                plan.append("search_mof_db")
            if "optimize" in response_text.lower():
                plan.append("optimize_structure_ase")
            if "energy" in response_text.lower() or "calculate" in response_text.lower():
                plan.append("calculate_energy_force")
    else:
        # Fallback: extract tool names from text
        if "search_mof" in response_text.lower():
            plan.append("search_mof_db")
        if "optimize" in response_text.lower():
            plan.append("optimize_structure_ase")
        if "energy" in response_text.lower() or "calculate" in response_text.lower():
            plan.append("calculate_energy_force")
    
    # Update state
    new_messages = messages + [response]
    
    return {
        **state,
        "messages": new_messages,
        "original_query": user_message,
        "plan": plan,
        "current_step": 0,
        "tool_outputs": state.get("tool_outputs", {}),
        "is_plan_approved": False,
    }

