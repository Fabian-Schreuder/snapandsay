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

    # Currently only formatting the start of the flow involving analysis
    workflow.add_edge(START, ANALYZE_INPUT)
    
    # Placeholder flow: Connect all nodes to ensure reachability
    workflow.add_edge(ANALYZE_INPUT, GENERATE_CLARIFICATION)
    workflow.add_edge(GENERATE_CLARIFICATION, FINALIZE_LOG)
    workflow.add_edge(FINALIZE_LOG, END)

    # Compile the graph
    app = workflow.compile()
    return app
