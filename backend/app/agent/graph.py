from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import analyze_input, generate_clarification, finalize_log
from app.agent.constants import ANALYZE_INPUT, GENERATE_CLARIFICATION, FINALIZE_LOG

def get_agent_graph():
    """
    Initialize and compile the agent graph.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(ANALYZE_INPUT, analyze_input)
    workflow.add_node(GENERATE_CLARIFICATION, generate_clarification)
    workflow.add_node(FINALIZE_LOG, finalize_log)

    # Add edges
    # Currently only formatting the start of the flow involving analysis
    workflow.add_edge(START, ANALYZE_INPUT)
    # Define simple flow for now to ensure all nodes are reachable/valid if needed, 
    # but for now we end after analysis as per initial story scope focus.
    # To avoid "unreachable code" warnings in advanced linters, we might leave them disconnected 
    # or connect them linearly for the "happy path" placeholder.
    # Task said "Start -> analyze_input". It didn't specify the rest. 
    # But to fix "unused nodes", we should at least register them.
    # Let's keep the edge simple as requested:
    workflow.add_edge(ANALYZE_INPUT, END)

    # Compile the graph
    app = workflow.compile()
    return app
