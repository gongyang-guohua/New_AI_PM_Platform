import sys
import os
from ai_agents.moonshot_client import MoonshotClient

def refine_spec(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    client = MoonshotClient()
    
    prompt = f"""
你是一个资深的工程项目管理专家和大模型架构师。我有一个关于“电气交付物分解智能体 (Electrical Deliverable Agent)”的规格说明书（Specification）。
请你根据以下要求对其进行完善和调整：
1. **保留核心内容**：不要删除原有的专业知识和核心工序（如 ETAP 计算、防爆分区等）。
2. **结构化增强**：确保规格说明书具有清晰的结构，包括：
   -角色定义 (Role)
   -专业知识 (Domain Knowledge)
   -业务逻辑/规则 (Operational Rules)
   -输出约束 (Output Constraints)
   -核心交付物清单 (Core Deliverables) 以 JSON 格式嵌入，且 JSON 字段应包含 activity_id, name, type, duration, predecessors, resource 等。
3. **专业性提升**：用更专业的工程术语补充细节，特别是关于“交付物”（Deliverable）的定义和审核流程。
4. **增加协作逻辑**：描述如何与其他智能体（如 WBS_Agent, Schedule_Agent）协作。

以下是原始内容：
---
{content}
---

请直接输出完善后的 Markdown 内容。
"""

    response = client.chat_completion([
        {"role": "system", "content": "你是一个专业的 AI 架构师和工程项目管理专家。"},
        {"role": "user", "content": prompt}
    ], model="moonshot-v1-32k")
    
    return response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python refine_spec.py <file_path> [output_path]")
        sys.exit(1)
    
    improved_content = refine_spec(sys.argv[1])
    
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(improved_content)
        print(f"Improved content saved to {sys.argv[2]}")
    else:
        print(improved_content)
