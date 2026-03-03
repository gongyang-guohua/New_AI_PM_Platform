# ai_agents/sub_agents/schedule_agent.py
from typing import Dict, Any, List
from ai_agents.tools.schedule_tools import calculate_cpm_schedule
from ai_agents.llm_gateway import LLMGateway

class ScheduleAgent:
    """
    Sub-agent responsible for translating user language into parameters for the CPM engine,
    running the engine, and generating a natural language project progress assessment.
    """
    def __init__(self):
        self.llm = LLMGateway()
        # In a real LangGraph setup with Tool calling, we bind tools to the LLM.
        # This is a simplified direct implementation.
        self.tools = [calculate_cpm_schedule]

    def execute(self, required_action: str, parameters: Dict[str, Any]) -> str:
        """
        Executes a scheduling command using the provided structured parameters.
        """
        if required_action == "calculate_cpm_schedule":
            # Direct invocation of our core engineering tool
            result_json = calculate_cpm_schedule(
                activities_data=parameters.get("activities", []),
                dependencies_data=parameters.get("dependencies", [])
            )
            
            # Use LLM to summarize the JSON output
            summary_prompt = f"""
            You are an expert Project Scheduler. Based on the following CPM Engine output:
            {result_json}
            
            Provide a short engineering summary (Critical Path, Project Length, Risks).
            """
            
            messages = [{"role": "user", "content": summary_prompt}]
            return self.llm.chat_completion(messages=messages, temperature=0.1)
            
        return f"Error: Action '{required_action}' is not supported by ScheduleAgent."
