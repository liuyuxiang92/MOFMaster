"""Example usage of the MOF-Scientist Backend."""

import asyncio
from app.graph import create_graph
from app.state import AgentState
from langchain_core.messages import HumanMessage


async def main():
    """Example: Run a simple query through the workflow."""
    graph = create_graph()
    
    # Create initial state
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Search for a copper-based MOF and optimize its structure")],
        "original_query": "Search for a copper-based MOF and optimize its structure",
        "plan": [],
        "current_step": 0,
        "tool_outputs": {},
        "review_feedback": "",
        "is_plan_approved": False,
    }
    
    # Run the graph
    print("Starting workflow...")
    result = await graph.ainvoke(initial_state)
    
    print("\n=== Final Result ===")
    print(f"Plan: {result.get('plan')}")
    print(f"Plan Approved: {result.get('is_plan_approved')}")
    print(f"Review Feedback: {result.get('review_feedback')}")
    print(f"\nTool Outputs:")
    for step, output in result.get("tool_outputs", {}).items():
        print(f"  {step}: {output}")
    
    print(f"\nFinal Messages:")
    for msg in result.get("messages", []):
        print(f"  {msg.type}: {msg.content[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())

