import os
import json
import re
from typing import Dict, List, Any
from ai_agents.moonshot_client import MoonshotClient

class DeliverableAgent:
    """
    Deliverable Agent responsible for decomposing project disciplines into 
    specific deliverables based on predefined specifications.
    """
    def __init__(self, specs_dir: str = "docs/specs/deliverable_agents"):
        self.specs_dir = specs_dir
        self.client = MoonshotClient()
        self.specs = self._load_specs()

    def _load_specs(self) -> Dict[str, str]:
        """Load all available discipline specifications."""
        specs = {}
        if not os.path.exists(self.specs_dir):
            return specs
            
        for filename in os.listdir(self.specs_dir):
            if filename.endswith(".md"):
                discipline = filename.replace("_deliverable_agent.md", "").lower()
                with open(os.path.join(self.specs_dir, filename), 'r', encoding='utf-8') as f:
                    specs[discipline] = f.read()
        return specs

    def decompose_discipline(self, discipline: str, project_context: str = "") -> Dict[str, Any]:
        """
        Decompose a discipline into deliverables using Moonshot based on the spec.
        """
        discipline_key = discipline.lower().replace(" ", "_")
        spec = self.specs.get(discipline_key)
        
        if not spec:
            return {"status": "error", "message": f"Specification for discipline '{discipline}' not found."}

        prompt = f"""
你是一个专业的 {discipline} 交付物分解专家。
根据以下规格说明书（Specification）和项目上下文，将该专业的任务进一步细化为可执行的交付物清单。

# Specification
{spec}

# Project Context
{project_context}

请严格按照规格说明书中的 JSON 格式进行输出。只输出 JSON 内容。
"""

        response = self.client.chat_completion([
            {"role": "system", "content": f"你是一个专业的 {discipline} 工程师。"},
            {"role": "user", "content": prompt}
        ], model="moonshot-v1-32k")

        # Extract JSON from response
        try:
            # More robust regex to catch JSON between backticks or just the first curly brace
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # If it's missing the final brace because of cutoff, try to fix it
                if json_str.count('{') > json_str.count('}'):
                    # This is naive but might help for a simple activities list
                    if '"activities": [' in json_str:
                         # Attempt to close the last activity, the activities list, and the main object
                         if not json_str.strip().endswith('}'):
                             json_str += '\n    }\n  ]\n}'
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to parse AI response as JSON: {str(e)}",
                "raw_response": response
            }

if __name__ == "__main__":
    # Test decomposition
    agent = DeliverableAgent()
    result = agent.decompose_discipline("electrical", "中试装置扩产项目，包含两座新的变电站。")
    print(json.dumps(result, indent=2, ensure_ascii=False))
