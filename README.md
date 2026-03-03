# ProjectMaster AI: Engineering-Grade AI PM Platform 🚀

ProjectMaster AI 是一个专为复杂工程项目（如化工 EPC、中试装置研发、大型设备制造）设计的 AI 项目管理助手平台。它将 **大语言模型的意图识别能力** 与 **纯确定性工程计算引擎** 深度结合，确保在利用 AI 提升效率的同时，保持工程级的计算精度。

## 🌟 核心价值

- **确定性计算**：核心调度（CPM）、资源优化（Leveling）和挣值分析（EVM）由纯数学引擎驱动，不依赖 AI 猜测，保证 100% 准确。
- **多智能体编排**：基于 **LangGraph** 实现复杂指令的逻辑拆解与路由，支持多步自动化工作流。
- **模型中立**：通过统一的 LLM 网关，支持在本地开源模型（如 Llama3）、Kimi (Moonshot API)、Google Gemini、OpenAI 和 Claude 之间无缝切换。
- **工程级深度**：支持 Oracle Primavera P6 等级的权重分配、逻辑关系（FS/SS/FF/SF）及日历换算。

## 🏗️ 目录架构

```text
├── docs/                      # 📋 需求文档、规格说明书 (SKILL.md, ADK Skill)
├── core_engine/               # ⚙️ 纯确定性算法层 (Python 计算引擎)
│   ├── schedule/              # CPM 进度计划引擎
│   ├── resource/              # 资源冲突与平衡引擎
│   └── cost/ risk/            # EVM 挣值与 Monte Carlo 风险模拟
├── ai_agents/                 # 🧠 多智能体编排层 (LangGraph)
│   ├── master_agent/          # 项目总监：意图识别与路由
│   ├── sub_agents/            # 领域专家：调用 core_engine
│   └── tools/                 # Agent 调用的工程具函数
├── backend/                   # 🔌 FastAPI 服务与 SQLAlchemy 数据层
└── frontend/                  # 💻 React + Vite + Tailwind 仪表盘/交互界面
```

## 🚀 快速开始

### 1. 后端环境配置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (.env)
LLM_MODEL=moonshot/moonshot-v1-8k
MOONSHOT_API_KEY=your_key_here
DATABASE_URL=postgresql://projectmaster:projectmaster@localhost:5432/projectmaster
```

### 2. 前端环境配置
```bash
cd frontend
npm install
npm run dev
```

### 3. 运行服务
- **后端**：`uvicorn backend.app.main:app --reload`
- **前端**：访问 `http://localhost:5173`

## 💡 使用示例

- **进度压缩**：“如果反应器到货延误两周，对关键路径有什么影响？帮我寻找最经济的压缩方案。”
- **资源冲突**：“检查下个月电气专业的工程师负荷情况，并给出削峰填谷建议。”
- **风险评估**：“针对目前的 WBS 进度，运行一次 1000 次的蒙特卡洛模拟，并输出延误概率分布图。”

---
*Powered by DeepMind Advanced Agentic Code Team*