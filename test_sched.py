# Step C — Enforce weekly cap (≤ 5 days/week). Add a week-aware scheduler and tests.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import logging, sys, math
import unittest

logger = logging.getLogger("TimeScheduler")
logger.setLevel(logging.DEBUG)

SECONDS_PER_DAY = 86400

@dataclass(frozen=True)
class Skill:
    name: str
    def __hash__(self) -> int:
        return hash(self.name)

@dataclass
class Person:
    pid: str
    skills: Set[Skill]
    def has_skill(self, sk: str) -> bool:
        return any(s.name == sk for s in self.skills)

@dataclass
class Task:
    tid: str
    required: Dict[str, int]     # skill -> count per day
    timebox_seconds: int
    @property
    def days_required(self) -> int:
        return max(1, math.ceil(self.timebox_seconds / SECONDS_PER_DAY))

@dataclass
class DayAssignment:
    task_to_people: Dict[str, List[Tuple[str, Set[str]]]] = field(default_factory=dict)

@dataclass
class MultiDaySchedule:
    by_day: Dict[int, DayAssignment] = field(default_factory=dict)
    days_worked: Dict[str, Dict[int, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))

# ---- Utilities ----
def compute_horizon_days(tasks: List[Task]) -> int:
    return max((t.days_required for t in tasks), default=0)

def active_tasks_on_day(tasks: List[Task], day: int) -> List[Task]:
    return [t for t in tasks if day < t.days_required]

def skill_supply_map(people: List[Person]) -> Counter:
    c = Counter()
    for p in people:
        for s in p.skills:
            c[s.name] += 1
    return c

def week_id_for_day(day: int) -> int:
    return day // 7

# ---- Daily Pair-Greedy (reused) ----
class DailyAssigner:
    @staticmethod
    def assign(tasks: List[Task], people: List[Person], day: int, logger: logging.Logger) -> DayAssignment:
        active = active_tasks_on_day(tasks, day)
        if not active:
            return DayAssignment({})

        # (task, skill) -> count
        uncovered: Dict[Tuple[str, str], int] = {}
        for t in active:
            for sk, cnt in t.required.items():
                if cnt > 0:
                    uncovered[(t.tid, sk)] = cnt

        available: Dict[str, Person] = {p.pid: p for p in people}
        task_assign: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

        supply = skill_supply_map(people)

        def total_uncovered() -> int:
            return sum(uncovered.values())

        def task_constrained_score(tid: str) -> float:
            score = 0.0
            for (t_id, sk), need in uncovered.items():
                if t_id != tid or need <= 0:
                    continue
                score += need / max(1, supply[sk])
            return score

        def gain_for_pair(p: Person, tid: str) -> Tuple[int, Set[str]]:
            needed = {sk for (t_id, sk), need in uncovered.items() if t_id == tid and need > 0}
            contrib = {s.name for s in p.skills if s.name in needed}
            return len(contrib), contrib

        logger.info(f"[Day {day}] Start assigning. Active: {[t.tid for t in active]}; Units: {total_uncovered()}")
        while total_uncovered() > 0:
            best: Optional[Tuple[str, str, int, Set[str]]] = None

            for pid, p in list(available.items()):
                best_for_p = None
                for t in active:
                    g, contrib = gain_for_pair(p, t.tid)
                    if g <= 0:
                        continue
                    cscore = task_constrained_score(t.tid)
                    task_size = sum(need for (tt, _), need in uncovered.items() if tt == t.tid and need > 0)
                    key = (g, cscore, task_size)
                    if best_for_p is None or key > best_for_p[3]:
                        best_for_p = (pid, t.tid, contrib, key)
                if best_for_p is None:
                    continue
                pid0, tid0, contrib0, key0 = best_for_p
                if best is None:
                    best = (pid0, tid0, len(contrib0), contrib0)
                else:
                    _, tid_b, g_b, contrib_b = best
                    key_b = (g_b,
                             task_constrained_score(tid_b),
                             sum(need for (tt, _), need in uncovered.items() if tt == tid_b and need > 0))
                    if key0 > key_b:
                        best = (pid0, tid0, len(contrib0), contrib0)

            if best is None:
                missing = [(t, s, n) for (t, s), n in uncovered.items() if n > 0]
                raise RuntimeError(f"[Day {day}] Infeasible daily assignment. Uncovered: {missing}")

            pid, tid, gain, skills = best
            for sk in skills:
                key = (tid, sk)
                if uncovered.get(key, 0) > 0:
                    uncovered[key] -= 1
            task_assign[tid][pid].update(skills)
            available.pop(pid, None)
            logger.info(f"[Day {day}] Assign {pid} -> {tid} covering {gain} skill(s). Remaining: {total_uncovered()}")

        day_map = {tid: [(pid, skills) for pid, skills in m.items()] for tid, m in task_assign.items()}
        return DayAssignment(task_to_people=day_map)

# ---- Week-aware multi-day scheduler ----
class MultiDaySchedulerWeekCap:
    def __init__(self, tasks: List[Task], people: List[Person], weekly_cap: int = 5) -> None:
        self.tasks = tasks
        self.people = people
        self.weekly_cap = weekly_cap

    def schedule(self) -> MultiDaySchedule:
        H = compute_horizon_days(self.tasks)
        sched = MultiDaySchedule()
        days_worked = sched.days_worked
        logger.info(f"[Sched] Horizon days: {H}. Weekly cap: {self.weekly_cap}")

        for d in range(H):
            wk = week_id_for_day(d)
            # Filter eligible people by weekly cap
            eligible = []
            for p in self.people:
                w = days_worked[p.pid][wk]
                if w < self.weekly_cap:
                    eligible.append(p)
            logger.info(f"[Day {d}] Eligible people: {[p.pid for p in eligible]}")

            day_assign = DailyAssigner.assign(self.tasks, eligible, d, logger=logger)
            # Update cap counters
            used_today = set(pid for plist in day_assign.task_to_people.values() for pid, _ in plist)
            for pid in used_today:
                days_worked[pid][wk] += 1
            sched.by_day[d] = day_assign
            # Sanity: ensure nobody exceeds cap
            for pid, wk_map in days_worked.items():
                if wk_map[wk] > self.weekly_cap:
                    raise AssertionError(f"Person {pid} exceeded weekly cap in week {wk}: {wk_map[wk]}")
        return sched

# ---- Tests for Step C ----
def _skills(*names: str) -> Set[Skill]:
    return {Skill(n) for n in names}

def _day_task_covered(task: Task, day_assignment: DayAssignment) -> bool:
    need = Counter(task.required)
    covered = Counter()
    plist = day_assignment.task_to_people.get(task.tid, [])
    for _, skills in plist:
        for sk in skills:
            covered[sk] += 1
    return all(covered[sk] >= need[sk] for sk in need)

class TestStepC_WeeklyCap(unittest.TestCase):
    def test_eight_day_single_skill_two_people_respects_cap(self):
        # Task needs x each day over 8 days (crosses a week boundary).
        people = [Person("P1", _skills("x")), Person("P2", _skills("x"))]
        tasks = [Task("T", {"x":1}, timebox_seconds=SECONDS_PER_DAY*8)]
        sched = MultiDaySchedulerWeekCap(tasks, people, weekly_cap=5).schedule()

        # Coverage each day
        for d in range(8):
            self.assertTrue(_day_task_covered(tasks[0], sched.by_day[d]))

        # Check weekly cap: week 0 has 7 days -> each person ≤ 5 in that week
        wk0_counts = {pid: sched.days_worked.get(pid, {}).get(0, 0) for pid in ["P1","P2"]}
        self.assertLessEqual(wk0_counts["P1"], 5)
        self.assertLessEqual(wk0_counts["P2"], 5)
        # Total 7 assignments in week 0; with cap 5, distribution must be (5,2) in some order
        self.assertEqual(wk0_counts["P1"] + wk0_counts["P2"], 7)

        # Week 1 day (d=7) adds +1 to one person in week 1
        wk1_counts = {pid: sched.days_worked.get(pid, {}).get(1, 0) for pid in ["P1","P2"]}
        self.assertEqual(wk1_counts["P1"] + wk1_counts["P2"], 1)
        self.assertTrue(all(c <= 5 for c in wk1_counts.values()))

    def test_multi_task_ten_days_with_bench_depth(self):
        # Two tasks over 10 days, enough people so nobody exceeds 5 per week
        people = [
            Person("G", _skills("a","b","c")),  # generalist
            Person("A1", _skills("a")),
            Person("A2", _skills("a")),
            Person("B1", _skills("b")),
            Person("B2", _skills("b")),
            Person("C1", _skills("c")),
            Person("C2", _skills("c")),
        ]
        tasks = [
            Task("T1", {"a":1, "b":1}, timebox_seconds=SECONDS_PER_DAY*10),
            Task("T2", {"c":1}, timebox_seconds=SECONDS_PER_DAY*10),
        ]
        sched = MultiDaySchedulerWeekCap(tasks, people, weekly_cap=5).schedule()

        # Daily coverage
        H = compute_horizon_days(tasks)
        for d in range(H):
            for t in tasks:
                self.assertTrue(_day_task_covered(t, sched.by_day[d]))

        # Weekly caps respected for week 0 (days 0..6) and week 1 (days 7..9)
        for pid, wk_map in sched.days_worked.items():
            for wk, cnt in wk_map.items():
                self.assertLessEqual(cnt, 5, f"{pid} exceeded cap in week {wk}")

# Run Step C tests only
suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStepC_WeeklyCap))
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)

# Add an extra invariant check: no person appears on more than one task per day under week-cap scheduler.

import unittest
from collections import defaultdict

def _no_person_multi_task_same_day(day_assignment: DayAssignment) -> bool:
    seen = set()
    for _, plist in day_assignment.task_to_people.items():
        for pid, _ in plist:
            if pid in seen:
                return False
            seen.add(pid)
    return True

class TestStepC_Invariants(unittest.TestCase):
    def test_no_person_multi_task_per_day(self):
        people = [
            Person("G", {Skill("a"), Skill("b")}),
            Person("A1", {Skill("a")}),
            Person("B1", {Skill("b")}),
        ]
        tasks = [
            Task("T1", {"a":1}, timebox_seconds=SECONDS_PER_DAY*4),
            Task("T2", {"b":1}, timebox_seconds=SECONDS_PER_DAY*4),
        ]
        sched = MultiDaySchedulerWeekCap(tasks, people, weekly_cap=5).schedule()
        for d, day_assign in sched.by_day.items():
            self.assertTrue(_no_person_multi_task_same_day(day_assign))

suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStepC_Invariants))
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
