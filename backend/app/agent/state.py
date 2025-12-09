from typing import TypedDict, Annotated, Optional, List, Dict, Any
from uuid import UUID
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of the agent.
    
    Core input fields:
        messages: Annotated list of messages with add_messages reducer
        image_url: URL to the uploaded food image
        audio_url: URL to the uploaded voice description audio
        
    Analysis output fields:
        nutritional_data: Extracted food items and nutritional estimates
        log_id: UUID of the DietaryLog record being processed
        
    Confidence routing fields:
        overall_confidence: Average confidence score across detected items (0-1)
        clarification_count: Number of clarification questions asked so far
        needs_clarification: Whether the agent needs to ask a follow-up question
        needs_review: Whether the log should be flagged for human review
    """
    messages: Annotated[List[BaseMessage], add_messages]
    image_url: Optional[str]
    audio_url: Optional[str]
    nutritional_data: Optional[Dict[str, Any]]
    log_id: Optional[UUID]
    overall_confidence: float
    clarification_count: int
    needs_clarification: bool
    needs_review: bool
    user_token: Optional[str]
