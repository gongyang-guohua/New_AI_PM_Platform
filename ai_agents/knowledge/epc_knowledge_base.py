# ai_agents/knowledge/epc_knowledge_base.py
"""
化工EPC行业经验知识库。
该模块存储了基于国内EPC行业实际项目数据的工期基准、
规模系数公式以及各阶段并行关系的经验法则。
对接 generate_project_plan 工具进行参数化工期推算。
"""
from typing import Dict, List, Any, Tuple


# ================================================================
# 一、化工装置类型与标准工期基准表（以工作日计）
# 基准项目规模：中型化工装置（10万吨/年为参考基准值）
# ================================================================
PROJECT_TYPE_BENCHMARKS: Dict[str, Dict] = {
    "氯碱": {
        "aliases": ["烧碱", "PVC", "氯化物", "电解盐水", "NaOH"],
        "base_scale_tonnes": 100_000,  # 参考规模（吨/年）
        "phases": {
            "立项与可研": {"id": "APPR", "base_duration": 120, "type": "permit", "parallel_with": []},
            "FEED基础设计": {"id": "FEED", "base_duration": 180, "type": "engineering", "parallel_with": ["APPR"]},
            "详细设计": {
                "id": "DENG",
                "base_duration": 270,
                "type": "engineering",
                "parallel_with": [],
                "disciplines": ["工艺", "配管", "仪表", "电气", "设备", "结构", "总图", "暖通", "给排水"]
            },
            "长周期设备采购": {
                "id": "PROC_LLI",
                "base_duration": 360,
                "type": "procurement",
                "parallel_with": ["FEED"],  # 与基础设计并行（SS+60天），关键氯碱反应槽通常26-30周
                "lag_days": 60,  # 从FEED开始后第60天才能启动采购
                "relation_type": "SS"
            },
            "大宗散材采购": {
                "id": "PROC_BULK",
                "base_duration": 150,
                "type": "procurement",
                "parallel_with": ["DENG"],
                "lag_days": 90,
                "relation_type": "SS"
            },
            "土建与基础施工": {
                "id": "CIVIL",
                "base_duration": 210,
                "type": "construction",
                "parallel_with": ["DENG"],
                "lag_days": 120,  # 土建在详设开始后约120天可启动（总图冻结后）
                "relation_type": "SS"
            },
            "设备安装": {"id": "EQUIP_INST", "base_duration": 180, "type": "construction", "parallel_with": []},
            "管道安装": {"id": "PIPE_INST", "base_duration": 200, "type": "construction", "parallel_with": ["EQUIP_INST"], "lag_days": 30, "relation_type": "SS"},
            "电仪安装调试": {"id": "ELEC_INST", "base_duration": 150, "type": "construction", "parallel_with": ["PIPE_INST"], "lag_days": 60, "relation_type": "SS"},
            "预试车与联调": {"id": "PRECOMM", "base_duration": 90, "type": "construction", "parallel_with": []},
            "投料试车与性能考核": {"id": "COMM", "base_duration": 60, "type": "construction", "parallel_with": []}
        },
        "scale_model": {
            "exponent": 0.6,  # 0.6次方律（化工装置常用）
            "complexity_factors": {
                "standard": 1.0,
                "高腐蚀介质": 1.2,
                "高压高温": 1.3,
                "特殊合金材质": 1.25
            }
        }
    },
    "乙烯": {
        "aliases": ["乙烯裂解", "石脑油", "steam cracker"],
        "base_scale_tonnes": 500_000,
        "phases": {
            "立项与可研": {"id": "APPR", "base_duration": 180, "type": "permit", "parallel_with": []},
            "FEED基础设计": {"id": "FEED", "base_duration": 270, "type": "engineering", "parallel_with": []},
            "详细设计": {"id": "DENG", "base_duration": 360, "type": "engineering", "parallel_with": []},
            "长周期设备采购": {"id": "PROC_LLI", "base_duration": 540, "type": "procurement", "parallel_with": ["FEED"], "lag_days": 60, "relation_type": "SS"},
            "施工安装": {"id": "CONST", "base_duration": 540, "type": "construction", "parallel_with": ["DENG"], "lag_days": 150, "relation_type": "SS"},
            "试车与投产": {"id": "COMM", "base_duration": 120, "type": "construction", "parallel_with": []}
        },
        "scale_model": {"exponent": 0.65, "complexity_factors": {"standard": 1.0}}
    },
    "通用化工": {
        "aliases": [],  # 缺省匹配
        "base_scale_tonnes": 50_000,
        "phases": {
            "立项与可研": {"id": "APPR", "base_duration": 90, "type": "permit", "parallel_with": []},
            "FEED基础设计": {"id": "FEED", "base_duration": 150, "type": "engineering", "parallel_with": []},
            "详细设计": {"id": "DENG", "base_duration": 210, "type": "engineering", "parallel_with": []},
            "采购": {"id": "PROC", "base_duration": 270, "type": "procurement", "parallel_with": ["FEED"], "lag_days": 60, "relation_type": "SS"},
            "施工": {"id": "CONST", "base_duration": 365, "type": "construction", "parallel_with": ["DENG"], "lag_days": 120, "relation_type": "SS"},
            "试车": {"id": "COMM", "base_duration": 60, "type": "construction", "parallel_with": []}
        },
        "scale_model": {"exponent": 0.6, "complexity_factors": {"standard": 1.0}}
    }
}


def identify_project_type(description: str) -> str:
    """
    根据项目描述文本识别对应的行业类型。
    返回 PROJECT_TYPE_BENCHMARKS 中的关键字。
    """
    description_lower = description.lower()
    for project_type, data in PROJECT_TYPE_BENCHMARKS.items():
        for alias in data.get("aliases", []):
            if alias.lower() in description_lower:
                return project_type
    return "通用化工"


def calculate_scale_factor(project_type: str, actual_scale_tonnes: float) -> float:
    """
    根据装置规模计算相对参考项目的工期放大系数。
    使用化工工程标准的0.6次方律（六分之一法则）。
    """
    benchmark = PROJECT_TYPE_BENCHMARKS.get(project_type, PROJECT_TYPE_BENCHMARKS["通用化工"])
    base_scale = benchmark["base_scale_tonnes"]
    exponent = benchmark["scale_model"]["exponent"]
    
    if actual_scale_tonnes <= 0:
        return 1.0
    
    scale_factor = (actual_scale_tonnes / base_scale) ** exponent
    return round(scale_factor, 3)


def parse_production_scale(description: str) -> Tuple[float, str]:
    """
    从项目描述中提取生产规模数字（以吨/年计）。
    返回 (数量, 单位) 元组。
    """
    import re
    # 匹配 "30万吨" "5万吨/年" "300kt/a" 等格式
    patterns = [
        (r'(\d+(?:\.\d+)?)万吨', 10_000),
        (r'(\d+(?:\.\d+)?)kt/a', 1_000),
        (r'(\d+(?:\.\d+)?)万吨/年', 10_000),
        (r'(\d+(?:\.\d+)?)吨/年', 1),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, description)
        if match:
            return float(match.group(1)) * multiplier, "吨/年"
    return 50_000, "吨/年"  # 缺省返回中型规模


def get_phase_sequence(project_type: str, scale_factor: float) -> List[Dict[str, Any]]:
    """
    返回考虑了规模系数调整后的完整阶段序列（含并行关系）。
    此函数为 generate_project_plan 工具的核心数据来源。
    """
    benchmark = PROJECT_TYPE_BENCHMARKS.get(project_type, PROJECT_TYPE_BENCHMARKS["通用化工"])
    phases = benchmark["phases"]
    
    result = []
    for phase_name, phase_data in phases.items():
        phase_type = phase_data.get("type", "engineering")
        base_dur = phase_data.get("base_duration", 90)
        
        # 审批类不受规模因子影响（审批周期是固定政策时间）
        if phase_type == "permit":
            adjusted_duration = base_dur
        else:
            adjusted_duration = int(base_dur * scale_factor)
        
        result.append({
            "id": phase_data["id"],
            "name": phase_name,
            "duration": adjusted_duration,
            "type": phase_type,
            "parallel_with": phase_data.get("parallel_with", []),
            "lag_days": phase_data.get("lag_days", 0),
            "relation_type": phase_data.get("relation_type", "FS"),
        })
    
    return result
