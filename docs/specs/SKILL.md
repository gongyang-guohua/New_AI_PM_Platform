# ProjectMaster Agent Skill

## Overview
ProjectMaster Agent is an engineering-grade project management skill designed for complex construction, EPC, R&D, and manufacturing projects. It provides deterministic scheduling algorithms combined with AI-enhanced forecasting and optimization.

---

# 1. Core Architecture

ProjectMasterAgent
- Core Data Layer
- WBS Skill
- Schedule Engine Skill
- Resource Optimization Skill
- Cost Intelligence Skill
- Risk Prediction Skill
- Reporting Skill

---

# 2. Core Data Model

## Project
- id
- name
- type (construction | r&d | manufacturing)
- baseline_version
- start_date
- finish_date
- status

## WBS
- id
- project_id
- parent_id
- level
- code
- weight
- budget_cost
- actual_cost

## Activity
- id
- wbs_id
- duration
- start
- finish
- remaining_duration
- constraint_type
- activity_type
- percent_complete
- calendar_id

## Relationship
- predecessor_id
- successor_id
- relation_type (FS | SS | FF | SF)
- lag

## Resource
- id
- type (labor | equipment | material)
- max_units
- cost_rate

## Assignment
- activity_id
- resource_id
- units
- cost

## CostAccount
- planned_cost
- actual_cost
- earned_value

---

# 3. Skill Modules

## 3.1 WBS Skill
Capabilities:
- Auto-generate WBS templates by industry
- Cross-discipline decomposition
- Hierarchical cost aggregation
- Weight calculation
- Multi-baseline support

AI Enhancements:
- Intelligent structure recommendation
- Granularity validation
- Historical template learning

---

## 3.2 Schedule Engine Skill
Core: CPM calculation engine

Functions:
- Forward pass (ES/EF)
- Backward pass (LS/LF)
- Total Float
- Free Float
- Critical path detection
- Constraint handling

AI Enhancements:
- Logic error detection
- Delay impact simulation
- Auto-optimization of network structure

---

## 3.3 Resource Optimization Skill
Functions:
- Resource histogram generation
- Conflict detection
- Automatic leveling
- Peak load analysis
- Multi-shift simulation

AI Enhancements:
- Optimal reallocation proposals
- Bottleneck prediction
- Capacity forecasting

---

## 3.4 Cost Intelligence Skill
EVM Support:
- PV
- EV
- AC
- CPI
- SPI
- EAC

Functions:
- S-curve generation
- Variance analysis
- Cash flow forecasting

AI Enhancements:
- Overrun early warning
- Dynamic margin analysis

---

## 3.5 Risk Prediction Skill
Risk Types:
- Schedule risk
- Resource risk
- Financial risk
- Supply chain risk

Functions:
- Monte Carlo simulation
- Delay probability calculation
- Critical risk path identification

---

## 3.6 Reporting Skill
Outputs:
- Gantt charts
- Network diagrams
- Resource histograms
- S-curves
- Executive summary reports

---

# 4. Execution Modes

## Deterministic Mode
Rule-based CPM and cost calculations.

## AI-Enhanced Mode
Predictive analytics using historical datasets and probabilistic modeling.

---

# 5. V1 Scope

Phase 1 includes:
- WBS Skill
- CPM Engine
- Critical Path Analysis
- Basic Resource Conflict Detection

Future phases will expand into full portfolio optimization and enterprise forecasting.

