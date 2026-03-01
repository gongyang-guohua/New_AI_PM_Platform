F:\New_AI_PM_Platform\
├── docs\                            # 📋 存放所有需求文档、架构设计与规范
│   ├── specs\                       # 核心功能规格说明书
│   │   ├── SKILL.md                 # 存放：项目管理 Skill 功能规格说明书
│   │   └── schedule_engine_spec.md  # 存放：Schedule Engine 引擎规格
│   └── adk_definitions\             # AI 平台的标准化技能配置
│       └── google_adk_skill.yaml    # 存放：ADK Skill 范式文件
│
├── core_engine\                     # ⚙️ 纯确定性算法层 (Python计算引擎)
│   ├── __init__.py
│   ├── schedule\                    # 进度计算模块
│   │   ├── __init__.py
│   │   └── cpm_engine.py            # 存放：你已生成的 CPM 正反算与资源驱动调度核心代码
│   ├── resource\                    # 资源优化模块 (Leveling 等)
│   ├── cost\                        # EVM 挣值计算模块
│   └── risk\                        # Monte Carlo 模拟模块
│
├── ai_agents\                       # 🧠 多智能体编排层 (LangGraph / AutoGen 等)
│   ├── __init__.py
│   ├── master_agent\                # 项目总监：负责意图识别与任务路由
│   │   ├── router.py                # 核心路由逻辑与 JSON 状态输出
│   │   └── prompts.py               # 存放我们刚才讨论的 Master Agent System Prompt
│   ├── sub_agents\                  # 专业智能体：封装对 core_engine 的调用
│   │   ├── schedule_agent.py        # 负责调用 cpm_engine.py 并解释结果
│   │   ├── wbs_agent.py             # 负责结构拆解
│   │   └── resource_agent.py        # 负责资源冲突预警
│   └── shared_state\                # 智能体间传递的上下文与状态图定义
│
├── backend\                         # 🔌 API 服务与数据持久层 (Node.js/Express 或 FastAPI)
│   ├── api\                         # 前端调用的 REST/GraphQL 接口
│   ├── db\                          # PostgreSQL 数据库层
│   │   ├── models.py                # ORM 数据模型 (Project, WBS, Activity, Resource 等)
│   │   └── migrations\              # 数据库迁移文件
│   └── services\                    # 业务逻辑服务
│
├── frontend\                        # 💻 用户界面层 (React 等)
│   ├── components\                  # 可复用组件 (甘特图、网络图、S曲线等)
│   └── pages\                       # 项目仪表盘、对话交互界面
│
├── scripts\                         # 🛠️ 自动化脚本 (测试数据生成、部署脚本)
├── .env                             # 环境变量 (数据库连接、API Keys 等，不要提交到 Git)
├── .gitignore
├── requirements.txt                 # Python 依赖清单
└── README.md                        # 项目工程说明