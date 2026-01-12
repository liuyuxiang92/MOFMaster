"""Main LangGraph definition - The 'Brain' of the system."""

from typing import Literal
from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents import (
    analyzer_node,
    supervisor_node,
    runner_node,
    reporter_node,
)


def route_after_analyzer(state: AgentState) -> Literal["supervisor"]:
    """After analyzer, always go to supervisor."""
    return "supervisor"


def route_after_supervisor(state: AgentState) -> Literal["runner", "analyzer"]:
    """After supervisor, go to runner if approved, else back to analyzer."""
    if state.get("is_plan_approved", False):
        return "runner"
    else:
        return "analyzer"


def route_after_runner(state: AgentState) -> Literal["runner", "reporter"]:
    """After runner, continue if more steps, else go to reporter."""
    current_step = state.get("current_step", 0)
    plan = state.get("plan", [])
    
    if current_step < len(plan):
        # More steps to execute
        return "runner"
    else:
        # All steps done, go to reporter
        return "reporter"


def create_graph():
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("runner", runner_node)
    workflow.add_node("reporter", reporter_node)
    
    # Set entry point
    workflow.set_entry_point("analyzer")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "analyzer",
        route_after_analyzer,
        {
            "supervisor": "supervisor",
        },
    )
    
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "runner": "runner",
            "analyzer": "analyzer",
        },
    )
    
    workflow.add_conditional_edges(
        "runner",
        route_after_runner,
        {
            "runner": "runner",  # Loop back to runner if more steps
            "reporter": "reporter",
        },
    )
    
    # Reporter always ends
    workflow.add_edge("reporter", END)
    
    return workflow.compile()

