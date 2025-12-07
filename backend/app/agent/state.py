from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The state of the agent.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    image_url: Optional[str]
    nutritional_data: Optional[Dict[str, Any]]
