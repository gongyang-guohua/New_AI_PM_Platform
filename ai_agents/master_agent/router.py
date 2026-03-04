# ai_agents/master_agent/router.py
import os
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from ai_agents.state import AgentState
from ai_agents.tools.schedule_tools import calculate_cpm_schedule, run_monte_carlo_simulation
from ai_agents.tools.project_planning_tool import generate_project_plan
from ai_agents.master_agent.prompts import MASTER_AGENT_SYSTEM_PROMPT

class MasterRouter:
    """
    ProjectMaster LangGraph Orchestrator. 
    Uses Tool Calling and StateGraph to act as an autonomous project management assistant.
    """
    def __init__(self):
        # Configure LLM supporting Tool Calling (bind_tools)
        # We use standard ChatOpenAI wrapper and point it to the Kimi (Moonshot) API 
        # which acts nicely as a very smart Chinese orchestrator with tool support.
        # Fallback to local could be handled similarly via changing base_url.
        api_key = os.getenv("MOONSHOT_API_KEY", "dummy-key")
        self.llm = ChatOpenAI(
            model="moonshot-v1-8k",
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            temperature=0.1
        )
        
        # Tools available to the agent
        self.tools = [generate_project_plan, calculate_cpm_schedule, run_monte_carlo_simulation]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self._build_graph()

    def _should_continue(self, state: AgentState) -> Literal["tools", "__end__"]:
        """Decide whether to call tools or end."""
        last_message = state["messages"][-1]
        
        # If the LLM generates tool_calls, route to the tool node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return "__end__"

    def _call_model(self, state: AgentState):
        """Invoke the LLM brain to decide the next action or to reply."""
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # Nodes
        builder.add_node("agent", self._call_model)
        tool_node = ToolNode(self.tools)
        builder.add_node("tools", tool_node)
        
        # Edges
        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", self._should_continue)
        builder.add_edge("tools", "agent")
        
        # Compile graph
        self.graph = builder.compile()

    def process_message(self, user_text: str, current_messages: list = None) -> list:
        """
        Processes a single user message against the agent graph. 
        Maintains conversational context via current_messages.
        """
        if current_messages is None or len(current_messages) == 0:
            current_messages = [SystemMessage(content=MASTER_AGENT_SYSTEM_PROMPT)]
            
        current_messages.append(HumanMessage(content=user_text))
        
        initial_state = {"messages": current_messages}
        final_state = self.graph.invoke(initial_state)
        
        # Return the resulting message list updated by the graph iteration
        return final_state["messages"]
