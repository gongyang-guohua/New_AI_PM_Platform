# ai_agents/state.py
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Global state object for LangGraph multi-agent orchestration.
    Maintains the conversational and computational continuity throughout the agent flows.
    """
    # Conversational tracking
    messages: List[Dict[str, Any]]
    
    # Project context
    project_id: Optional[str]
    current_intent: str
    
    # Execution Tracking
    requires_multi_step: bool
    execution_plan: List[Dict[str, Any]]
    current_step_index: int
    
    # Results & Payloads aggregated across agents
    context_data: Dict[str, Any]
    final_response: Optional[str]
