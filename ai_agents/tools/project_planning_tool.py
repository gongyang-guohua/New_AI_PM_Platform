# ai_agents/tools/project_planning_tool.py
"""
项目宏观规划推理工具。
接收用户的自然语言项目描述，通过化工EPC行业知识库推导出
完整的 WBS 阶段、参数化工期、并行关系，并调用本地 CPM API
进行精准的时间测算，最终返回结构化的项目初步计划。
"""
import json
import httpx
from langchain_core.tools import tool
from typing import Optional

# 引入行业知识库
from ai_agents.knowledge.epc_knowledge_base import (
    identify_project_type,
    parse_production_scale,
    calculate_scale_factor,
    get_phase_sequence
)

CPM_CALCULATE_URL = "http://localhost:8000/api/v1/engine/cpm/calculate"


def _build_cpm_payload(phases: list) -> dict:
    """
    将行业知识库返回的阶段序列转换为 CPM 端点所需的 activities + relationships 格式。
    自动识别并行关系，生成 FS/SS 逻辑。
    """
    activities = []
    relationships = []
    
    # 建立 id → phase 的映射
    id_map = {phase["id"]: phase for phase in phases}
    
    # 生成活动列表
    for phase in phases:
        activities.append({
            "id": phase["id"],
            "name": phase["name"],
            "duration": phase["duration"]
        })
    
    # 生成关系列表（基于 parallel_with 和串联逻辑）
    # 首先处理纯串联（FS）关系：对没有显式并行声明的阶段，按顺序连接
    processed_ids = set()
    phase_list = list(id_map.keys())
    
    for i, phase in enumerate(phases):
        phase_id = phase["id"]
        parallel_with = phase.get("parallel_with", [])
        lag = phase.get("lag_days", 0)
        relation_type = phase.get("relation_type", "FS")
        
        if parallel_with:
            # 此阶段与 parallel_with 列表中的某个阶段并行启动
            for ancestor_id in parallel_with:
                if ancestor_id in id_map:
                    relationships.append({
                        "predecessor": ancestor_id,
                        "successor": phase_id,
                        "relation_type": relation_type,
                        "lag": lag
                    })
                    processed_ids.add(phase_id)
        else:
            # 默认 FS 关系：找到紧邻的没有被并行处理的前任阶段
            if i > 0:
                # 寻找最近的一个没有显式并行声明标记了当前节点的前任
                for prev_i in range(i - 1, -1, -1):
                    prev_phase = phases[prev_i]
                    prev_id = prev_phase["id"]
                    # 检查 prev_phase 是否已经在某种形式上连接了 phase_id
                    already_linked = any(
                        r["predecessor"] == prev_id and r["successor"] == phase_id
                        for r in relationships
                    )
                    if not already_linked:
                        # 找到上一个主线阶段（没有并行的）
                        if not prev_phase.get("parallel_with"):
                            relationships.append({
                                "predecessor": prev_id,
                                "successor": phase_id,
                                "relation_type": "FS",
                                "lag": 0
                            })
                            break
                        else:
                            # 有并行关系，跳过，继续往前找
                            continue
    
    return {"activities": activities, "relationships": relationships}


@tool
def generate_project_plan(project_description: str, additional_complexity: Optional[str] = None) -> str:
    """
    根据用户输入的项目宏观描述，利用化工EPC行业知识库生成完整的项目初步计划。
    适用于当用户描述了项目类型（如烧碱、乙烯、PVC）和产能规模时。
    该工具会自动：①识别行业类型，②计算规模系数，③生成各阶段工期和并行关系，④调用CPM引擎测算时差和关键路径。
    
    Args:
        project_description: 完整的自然语言项目描述字符串，包含装置类型和产能信息。
        additional_complexity: 可选，额外复杂度描述，如'高腐蚀介质','特殊合金材质'等。
        
    Returns:
        包含完整项目计划（总工期、各阶段关键路径、并行分析）的 JSON 字符串报告。
    """
    # ① 识别项目类型
    project_type = identify_project_type(project_description)
    
    # ② 解析生产规模
    scale_tonnes, scale_unit = parse_production_scale(project_description)
    
    # ③ 计算规模系数（0.6次方律）
    scale_factor = calculate_scale_factor(project_type, scale_tonnes)
    
    # ④ 获取参数化后的阶段序列（含工期和并行关系）
    phases = get_phase_sequence(project_type, scale_factor)
    
    # ⑤ 构建 CPM 请求体
    cpm_payload = _build_cpm_payload(phases)
    
    # ⑥ 调用本地 CPM API
    try:
        response = httpx.post(CPM_CALCULATE_URL, json=cpm_payload, timeout=30.0)
        response.raise_for_status()
        cpm_result = response.json()
    except Exception as e:
        return json.dumps({
            "error": f"CPM API 调用失败: {str(e)}",
            "project_type": project_type,
            "scale_tonnes": scale_tonnes,
            "scale_factor": scale_factor,
            "phases_generated": [p["name"] for p in phases]
        }, ensure_ascii=False)
    
    # ⑦ 将行业语义标签附加到 CPM 结果中，便于 AI 解读
    enhanced_result = {
        "inference_meta": {
            "identified_project_type": project_type,
            "production_scale": f"{scale_tonnes:,.0f} {scale_unit}",
            "scale_factor_applied": scale_factor,
            "total_phases_generated": len(phases),
            "parallel_phases": [p["name"] for p in phases if p.get("parallel_with")]
        },
        "cpm_calculation": cpm_result,
        "phase_details": [
            {
                "id": p["id"],
                "name": p["name"],
                "adjusted_duration_days": p["duration"],
                "type": p["type"],
                "parallel_logic": f"{p['relation_type']}+{p['lag_days']}天" if p.get("parallel_with") else "串联 FS"
            }
            for p in phases
        ]
    }
    
    return json.dumps(enhanced_result, indent=2, ensure_ascii=False)
