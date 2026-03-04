import sys
import os
sys.path.append(r"f:\New_AI_PM_Platform")
from dotenv import load_dotenv
load_dotenv(r"f:\New_AI_PM_Platform\.env")

from ai_agents.master_agent.router import MasterRouter

def test_caustic_project():
    """端到端测试：化工宏观项目描述 → 行业知识推断 → CPM测算"""
    router = MasterRouter()
    history = []
    prompt = "新建一套30万吨/年的烧碱装置，原料为盐湖中制备的raw salt，耗氯产品为36万吨/年PVC，请编制项目初步计划。"
    print(f"User Prompt:\n{prompt}\n")
    print("[Agent 思考中，正在调用行业知识库和 CPM 引擎...]")
    try:
        history = router.process_message(prompt, history)
        print("\n--- 交互链路日志 ---")
        for msg in history:
            print(f"\n[{type(msg).__name__}]")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  ▶ 工具调用: {tc['name']}")
            elif hasattr(msg, 'name') and msg.name:
                print(f"  ◀ 工具'{msg.name}'返回结果（见下）")
                # 只打印前300字符的工具返回
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                print(f"  {content}")
            else:
                print(f"  Agent 最终回复:\n{msg.content}")
            print("-" * 50)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_caustic_project()
