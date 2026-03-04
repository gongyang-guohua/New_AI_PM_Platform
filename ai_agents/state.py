# ai_agents/state.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Global state object for LangGraph multi-agent orchestration.
    Maintains the conversational and computational continuity throughout the agent flows.
    """
    # The `messages` key is required strictly when dealing with a standard React/Tool agent format
    # `add_messages` automatically appends new messages properly without wiping the list
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Optional active project ID tracker
    project_id: str
