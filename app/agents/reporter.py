"""Reporter Agent: Data Synthesis and Report Generation."""

from app.state import AgentState
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate


def reporter_node(state: AgentState) -> AgentState:
    """
    Reporter Agent: Synthesizes tool outputs into a final report.
    
    Generates a Markdown-formatted summary answering the original query.
    Must include units (eV, Å) and cite the files created.
    """
    original_query = state.get("original_query", "")
    tool_outputs = state.get("tool_outputs", {})
    
    # Create system prompt
    system_prompt = """You are a scientific reporter synthesizing computational chemistry results.

Your task is to generate a clear, Markdown-formatted report that:
1. Answers the original user query
2. Includes all relevant results with proper units (eV for energy, Å for distances)
3. Cites the files created (e.g., optimized CIF files)
4. Provides scientific context and interpretation

Tool outputs:
{tool_outputs}

Original query: {original_query}

Generate a comprehensive report in Markdown format."""
    
    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    llm = get_llm()
    chain = prompt | llm
    
    report = chain.invoke({
        "tool_outputs": str(tool_outputs),
        "original_query": original_query,
    })
    
    # Add the report to messages
    from langchain_core.messages import AIMessage
    messages = state.get("messages", [])
    report_message = AIMessage(content=report.content)
    
    return {
        **state,
        "messages": messages + [report_message],
    }

