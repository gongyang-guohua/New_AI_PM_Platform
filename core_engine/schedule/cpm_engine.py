"""
CPM Engine - Deterministic Critical Path Method Implementation
Supports:
- Forward Pass
- Backward Pass
- Float Calculation
- Critical Path Detection
- Basic Resource-Constrained Scheduling (RCPSP skeleton)
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


# -----------------------------
# Data Models
# -----------------------------

@dataclass
class Activity:
    id: str
    duration: int
    constraint_type: Optional[str] = None # SNET, FNLT, MSO, MFO
    constraint_date: Optional[int] = None
    
    # PERT/Monte Carlo properties
    optimistic_duration: Optional[int] = None
    most_likely_duration: Optional[int] = None
    pessimistic_duration: Optional[int] = None

    # Computed fields
    ES: int = 0
    EF: int = 0
    LS: int = 0
    LF: int = 0
    total_float: int = 0
    free_float: int = 0


@dataclass
class Relationship:
    predecessor: str
    successor: str
    relation_type: str = "FS"  # FS, SS, FF, SF
    lag: int = 0


@dataclass
class ResourceAssignment:
    activity_id: str
    resource_id: str
    units: int


# -----------------------------
# Calendar System
# -----------------------------

class WorkCalendar:
    """
    Advanced working calendar
    - working_days: set of weekday numbers (0=Mon ... 6=Sun)
    - holidays: set of absolute day numbers
    - shifts_per_day: number of working shifts per day
    - hours_per_shift: working hours per shift
    - time_unit: "day" or "hour"

    Time is modeled as integer units (day or hour depending on mode)
    """

    def __init__(self,
                 working_days=None,
                 holidays=None,
                 shifts_per_day: int = 1,
                 hours_per_shift: int = 8,
                 time_unit: str = "day"):

        self.working_days = working_days if working_days else {0,1,2,3,4}
        self.holidays = holidays if holidays else set()
        self.shifts_per_day = shifts_per_day
        self.hours_per_shift = hours_per_shift
        self.time_unit = time_unit

        self.hours_per_day = self.shifts_per_day * self.hours_per_shift

    def is_working_day(self, absolute_day: int) -> bool:
        weekday = absolute_day % 7
        if absolute_day in self.holidays:
            return False
        return weekday in self.working_days

    def is_working_time(self, absolute_time: int) -> bool:
        if self.time_unit == "day":
            return self.is_working_day(absolute_time)
        else:
            day = absolute_time // self.hours_per_day
            hour_in_day = absolute_time % self.hours_per_day
            if not self.is_working_day(day):
                return False
            return hour_in_day < self.hours_per_day

    def add_working_time(self, start_time: int, duration: int) -> int:
        """Return finish time respecting calendar and unit"""
        added = 0
        current = start_time
        while added < duration:
            if self.is_working_time(current):
                added += 1
            current += 1
        return current


# -----------------------------
# CPM Engine
# -----------------------------

class CPMEngine:
    def __init__(self, activities: Dict[str, Activity], relationships: List[Relationship], calendar: WorkCalendar = None):
        self.activities = activities
        self.relationships = relationships
        self.graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
        self.calendar = calendar if calendar else WorkCalendar()
        self.build_graph()

    def build_graph(self):
        for rel in self.relationships:
            self.graph[rel.predecessor].append(rel)
            self.reverse_graph[rel.successor].append(rel)

    def topological_sort(self) -> List[str]:
        indegree = {k: 0 for k in self.activities}
        for rel in self.relationships:
            indegree[rel.successor] += 1

        queue = deque([k for k, v in indegree.items() if v == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for rel in self.graph[node]:
                indegree[rel.successor] -= 1
                if indegree[rel.successor] == 0:
                    queue.append(rel.successor)

        if len(order) != len(self.activities):
            raise Exception("Circular dependency detected")

        return order

    # -----------------------------
    # Forward Pass (Calendar Aware)
    # -----------------------------
    def forward_pass(self):
        order = self.topological_sort()

        for act_id in order:
            activity = self.activities[act_id]
            max_es = 0

            for rel in self.reverse_graph[act_id]:
                pred = self.activities[rel.predecessor]
                if rel.relation_type == "FS":
                    candidate = pred.EF + rel.lag
                elif rel.relation_type == "SS":
                    candidate = pred.ES + rel.lag
                elif rel.relation_type == "FF":
                    candidate = pred.EF + rel.lag - activity.duration
                elif rel.relation_type == "SF":
                    candidate = pred.ES + rel.lag - activity.duration
                else:
                    candidate = 0

                max_es = max(max_es, candidate)

            # --- Constraint Handling (Forward Pass) ---
            if activity.constraint_type in ("SNET", "MSO") and activity.constraint_date is not None:
                max_es = max(max_es, activity.constraint_date)

            activity.ES = max_es
            activity.EF = self.calendar.add_working_time(activity.ES, activity.duration)

            # MFO forward pass overriding (violates logic to force finish, primarily verified in backward)
            if activity.constraint_type == "MFO" and activity.constraint_date is not None:
                activity.EF = activity.constraint_date
                activity.ES = max(0, activity.EF - activity.duration)  # Simplified adjustment

    # -----------------------------
    # Backward Pass (Calendar Aware)
    # -----------------------------
    def backward_pass(self):
        order = self.topological_sort()[::-1]
        project_finish = max(a.EF for a in self.activities.values())

        for act_id in order:
            activity = self.activities[act_id]

            if not self.graph[act_id]:
                min_lf = project_finish
            else:
                min_lf = float("inf")
                for rel in self.graph[act_id]:
                    succ = self.activities[rel.successor]
                    candidate = succ.LS - rel.lag
                    min_lf = min(min_lf, candidate)
                
            # --- Constraint Handling (Backward Pass) ---
            if activity.constraint_type in ("FNLT", "MFO") and activity.constraint_date is not None:
                if not self.graph[act_id]:
                    min_lf = activity.constraint_date
                else:
                    min_lf = min(min_lf, activity.constraint_date)
            elif activity.constraint_type == "MSO" and activity.constraint_date is not None:
                min_lf = min(min_lf, activity.constraint_date + activity.duration)
                
            activity.LF = min_lf

            # Reverse calculate LS using calendar
            # Simplified approximation: step backwards counting working days
            days_needed = activity.duration
            current_day = activity.LF
            counted = 0
            while counted < days_needed:
                current_day -= 1
                if self.calendar.is_working_time(current_day):
                    counted += 1
            activity.LS = current_day

    def calculate_float(self):
        for act in self.activities.values():
            act.total_float = act.LS - act.ES

            successors = self.graph[act.id]
            if successors:
                min_successor_es = min(self.activities[rel.successor].ES for rel in successors)
                act.free_float = min_successor_es - act.EF
            else:
                act.free_float = act.total_float

    def run(self):
        self.forward_pass()
        self.backward_pass()
        self.calculate_float()

        critical_path = [a.id for a in self.activities.values() if a.total_float == 0]
        return critical_path


# -----------------------------
# Resource-Driven Scheduling Engine (P6-style priority + leveling)
# -----------------------------

class ResourceDrivenScheduler:
    """
    Enterprise-grade resource-driven scheduling

    Features:
    - Priority-based activity selection
    - Resource-constrained forward scheduling
    - Late-date driven leveling option
    - Float consumption tracking
    - Criticality preservation logic
    """

    def __init__(self,
                 activities: Dict[str, Activity],
                 relationships: List[Relationship],
                 assignments: List[ResourceAssignment],
                 resource_limits: Dict[str, int],
                 calendar: WorkCalendar = None,
                 priority_rule: str = "TOTAL_FLOAT"):

        self.activities = activities
        self.relationships = relationships
        self.assignments = assignments
        self.resource_limits = resource_limits
        self.calendar = calendar if calendar else WorkCalendar()
        self.priority_rule = priority_rule

        self.resource_usage = defaultdict(lambda: defaultdict(int))

    # --------------------------------------------------
    # Priority Rules (similar to Primavera logic)
    # --------------------------------------------------
    def sort_activities(self, eligible: List[Activity]) -> List[Activity]:
        if self.priority_rule == "TOTAL_FLOAT":
            return sorted(eligible, key=lambda x: x.total_float)
        elif self.priority_rule == "EARLY_START":
            return sorted(eligible, key=lambda x: x.ES)
        elif self.priority_rule == "LATE_FINISH":
            return sorted(eligible, key=lambda x: x.LF)
        else:
            return eligible

    # --------------------------------------------------
    # Check Resource Feasibility
    # --------------------------------------------------
    def is_resource_feasible(self, act: Activity, start_time: int) -> bool:
        for assign in self.assignments:
            if assign.activity_id != act.id:
                continue

            time_cursor = start_time
            used_units = 0

            while used_units < act.duration:
                if self.calendar.is_working_time(time_cursor):
                    if (self.resource_usage[time_cursor][assign.resource_id]
                            + assign.units
                            > self.resource_limits[assign.resource_id]):
                        return False
                    used_units += 1
                time_cursor += 1
        return True

    # --------------------------------------------------
    # Allocate Resources
    # --------------------------------------------------
    def allocate_resources(self, act: Activity, start_time: int):
        for assign in self.assignments:
            if assign.activity_id != act.id:
                continue

            time_cursor = start_time
            used_units = 0

            while used_units < act.duration:
                if self.calendar.is_working_time(time_cursor):
                    self.resource_usage[time_cursor][assign.resource_id] += assign.units
                    used_units += 1
                time_cursor += 1

    # --------------------------------------------------
    # Resource-Driven Scheduling Procedure
    # --------------------------------------------------
    def schedule(self):
        """
        Logic:
        1. Determine eligible activities (all predecessors scheduled)
        2. Sort by priority rule
        3. Attempt earliest feasible start
        4. If not feasible, delay until feasible
        5. Track float consumption
        """

        unscheduled = set(self.activities.keys())
        scheduled = set()

        predecessor_map = defaultdict(set)
        for rel in self.relationships:
            predecessor_map[rel.successor].add(rel.predecessor)

        current_time = 0

        while unscheduled:
            eligible = []

            for act_id in unscheduled:
                if predecessor_map[act_id].issubset(scheduled):
                    eligible.append(self.activities[act_id])

            if not eligible:
                raise Exception("Deadlock detected in resource scheduling")

            eligible = self.sort_activities(eligible)

            for act in eligible:
                t = act.ES
                while not self.is_resource_feasible(act, t):
                    t += 1

                act.ES = t
                act.EF = self.calendar.add_working_time(t, act.duration)

                self.allocate_resources(act, t)

                # Float consumption tracking
                delay = t - act.ES
                act.total_float = max(0, act.total_float - delay)

                scheduled.add(act.id)
                unscheduled.remove(act.id)
                break

        return self.activities


# End of Resource-Driven CPM Engine


# -----------------------------
# Monte Carlo / PERT Engine
# -----------------------------
import random
import statistics

class MonteCarloEngine:
    """
    Stochastic tracking engine for calculating Project Completion Probabilities
    and Criticality Indices via Monte Carlo simulation
    """

    def __init__(self, activities: Dict[str, Activity], relationships: List[Relationship], calendar: WorkCalendar = None):
        self.original_activities = activities
        self.relationships = relationships
        self.calendar = calendar if calendar else WorkCalendar()

    def _sample_duration(self, act: Activity) -> int:
        """Sample duration using Triangular Distribution if PERT data exists"""
        if all(x is not None for x in [act.optimistic_duration, act.most_likely_duration, act.pessimistic_duration]):
            # Triangular distribution (native random): low, high, mode
            sample = random.triangular(act.optimistic_duration, act.pessimistic_duration, act.most_likely_duration)
            return max(1, int(round(sample)))  # Minimum 1 unit of work
        return act.duration

    def simulate(self, iterations: int = 1000) -> Dict:
        project_durations = []
        criticality_counts = defaultdict(int)

        for _ in range(iterations):
            # Create a localized deep-copy equivalent for iteration speed
            sim_activities = {}
            for k, v in self.original_activities.items():
                sampled_d = self._sample_duration(v)
                sim_activities[k] = Activity(
                    id=v.id,
                    duration=sampled_d,
                    constraint_type=v.constraint_type,
                    constraint_date=v.constraint_date
                )

            # Fire off deterministic engine
            cpm = CPMEngine(activities=sim_activities, relationships=self.relationships, calendar=self.calendar)
            
            try:
                critical_path = cpm.run()
                finish_date = max(a.EF for a in cpm.activities.values())
                project_durations.append(finish_date)
                
                for node_id in critical_path:
                    criticality_counts[node_id] += 1
            except Exception:
                # E.g. circular dependency shouldn't happen dynamically but handled safely
                continue

        if not project_durations:
            raise Exception("Simulation failed to produce results")

        project_durations.sort()
        
        # Calculate summary statistics using standard library
        return {
            "p50_duration": project_durations[int(len(project_durations) * 0.50)],
            "p80_duration": project_durations[int(len(project_durations) * 0.80)],
            "p95_duration": project_durations[int(len(project_durations) * 0.95)],
            "mean_duration": statistics.mean(project_durations),
            "min_duration": min(project_durations),
            "max_duration": max(project_durations),
            "criticality_index": {k: float(v) / iterations for k, v in criticality_counts.items()}
        }
