import json
from ai_agents.deliverable_agent import DeliverableAgent

def verify_all():
    agent = DeliverableAgent()
    
    print("Testing decomposition for Electrical discipline...")
    result = agent.decompose_discipline("electrical", "中试装置扩产项目，重点关注变电站扩容。")
    
    with open("tmp/verification_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Verification result saved to tmp/verification_result.json")

if __name__ == "__main__":
    verify_all()
