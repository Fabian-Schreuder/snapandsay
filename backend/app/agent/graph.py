from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import analyze_input

def get_agent_graph():
    """
    Initialize and compile the agent graph.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_input", analyze_input)

    # Add edges
    workflow.add_edge(START, "analyze_input")
    workflow.add_edge("analyze_input", END)

    # Compile the graph
    app = workflow.compile()
    return app
