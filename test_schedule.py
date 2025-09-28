from sss import Skill, Person, Task, DayAssignment, MultiDaySchedulerWeekCap, SECONDS_PER_DAY, compute_horizon_days
import unittest
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Optional


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
