import sys
import os
sys.path.append(r"f:\New_AI_PM_Platform")
from dotenv import load_dotenv
load_dotenv(r"f:\New_AI_PM_Platform\.env")

from ai_agents.master_agent.router import MasterRouter

def test_complex():
    router = MasterRouter()
    history = []
    prompt = "新建一套30万吨/年的烧碱装置，原料为盐湖中制备的raw salt，耗氯产品为36万吨/年PVC，请编制项目初步计划。"
    print(f"User Prompt: {prompt}")
    try:
        history = router.process_message(prompt, history)
        print("\n--- Interaction Log ---")
        for msg in history:
            print(f"[{type(msg).__name__}]")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print(f"Tool calls: {msg.tool_calls}")
            print(f"Content: {msg.content}")
            print("-" * 20)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complex()
