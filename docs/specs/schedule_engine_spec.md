# Schedule Engine Specification

## Module Name
Schedule Engine Skill

## Purpose
Provide deterministic Critical Path Method (CPM) scheduling calculations with constraint handling, float analysis, and extensible optimization hooks for AI enhancement.

---

# 1. Core Responsibilities

- Construct directed acyclic activity network
- Execute forward pass (early dates)
- Execute backward pass (late dates)
- Calculate Total Float and Free Float
- Identify Critical Path
- Validate logical consistency
- Support scheduling constraints

---

# 2. Input Data Requirements

## Activity Structure
- id
- duration
- calendar_id
- constraint_type (optional)
- constraint_date (optional)

## Relationship Structure
- predecessor_id
- successor_id
- relation_type (FS | SS | FF | SF)
- lag

## Calendar
- working_days
- exceptions

---

# 3. Network Construction

## 3.1 Graph Model
- Directed graph G(V, E)
- V = Activities
- E = Relationships

Validation:
- Detect circular dependencies
- Detect orphan activities
- Validate constraint conflicts

---

# 4. Forward Pass Calculation

For each activity i:

ES(i) = max(EF(predecessors) + lag)
EF(i) = ES(i) + duration

Special handling per relationship type:

FS:
ES(successor) >= EF(predecessor) + lag

SS:
ES(successor) >= ES(predecessor) + lag

FF:
EF(successor) >= EF(predecessor) + lag

SF:
EF(successor) >= ES(predecessor) + lag

Output:
- Early Start (ES)
- Early Finish (EF)

---

# 5. Backward Pass Calculation

Initialize project finish:
LF(project_finish) = max(EF)

For each activity i (reverse order):

LF(i) = min(LS(successors) - lag)
LS(i) = LF(i) - duration

Output:
- Late Start (LS)
- Late Finish (LF)

---

# 6. Float Calculation

Total Float (TF):
TF = LS - ES

Free Float (FF):
FF = min(ES(successors)) - EF

Critical Path Rule:
Activities with TF = 0 are critical.

---

# 7. Constraint Handling

Supported Constraints:
- Must Start On
- Must Finish On
- Start No Earlier Than
- Finish No Later Than

Constraint Application Order:
1. Apply constraint during forward pass
2. Recalculate dependent activities
3. Validate feasibility

Constraint violations must generate warnings.

---

# 8. Output Structure

schedule_result:
  activities:
    - id
      ES
      EF
      LS
      LF
      total_float
      free_float
      is_critical
  project_finish_date
  critical_path_list

---

# 9. Error Detection

- Circular logic detection
- Negative float detection
- Invalid constraint detection
- Disconnected network detection

---

# 10. Extension Hooks (AI Mode)

## Delay Simulation Hook
Input: delay_days, activity_id
Output: impact_on_finish

## Risk Analysis Hook
Inject probabilistic duration distributions
Run Monte Carlo simulation

## Auto Optimization Hook
Suggest logic adjustments or activity resequencing

---

# 11. Performance Requirements

- Support 10,000+ activities
- O(N + E) graph traversal complexity
- Parallelizable Monte Carlo extension

---

# 12. V1 Scope

Included:
- Deterministic CPM engine
- Constraint handling
- Critical path detection
- Float calculation

Deferred:
- Resource-constrained scheduling (separate module)
- Portfolio cross-project dependencies
- Machine learning duration prediction

---

# End of Specification

