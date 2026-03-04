import sys
import os
sys.path.append(r"f:\New_AI_PM_Platform")
from dotenv import load_dotenv
load_dotenv(r"f:\New_AI_PM_Platform\.env")

from ai_agents.master_agent.router import MasterRouter

def test():
    router = MasterRouter()
    history = []
    prompt = "我有一个盖房项目。A是挖地基10天，B是做框架20天，B必须在A完成之后。C是粉刷30天，也必须在B之后。麻烦用你的计算工具帮我测算一下这个项目的工期和所有活动的时差。"
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
    test()
