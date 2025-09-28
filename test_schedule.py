from datetime import datetime, timedelta, date
import os
from server.src.search._search import Person, Task, HorizonSchedulerPTO, HorizonSchedule, DaySchedule, _midnight_local, _mk_ts, _day_interval
from dataclasses import asdict
from collections import deque
import json
from typing import List, Dict, Set
from server.src import _TZ, logger

# ---- Validation & tests ----
import pandas as pd

# Simple replacement for caas_jupyter_tools
def display_dataframe_to_user(title: str, df: pd.DataFrame):
    """Simple replacement for caas_jupyter_tools display function"""
    print(f"\n{title}")
    print("=" * len(title))
    print(df.to_string(index=False))
    print()

def validate_pto_schedule(people: List[Person], tasks: List[Task], hs: HorizonSchedule, start_day: date, span_days: int, pto_map: Dict[date, Set[str]], allow_future: bool, current_ts: int):
    errors = []
    people_by = {p.person_id: p for p in people}
    tasks_by = {t.task_id: t for t in tasks}

    def active_on(t: Task, day_dt: datetime) -> bool:
        s, e = _day_interval(day_dt)
        return t.is_active_on_day(s, e)

    for i, day in enumerate(hs.days):
        day_dt = _midnight_local(start_day) + timedelta(days=i)
        day_start, _ = _day_interval(day_dt)
        pto_today = pto_map.get(day_dt.date(), set())
        require_today = allow_future or (day_start <= current_ts)

        # PTO not assigned
        for apt in day.assignments:
            for pid in apt.people_contributions:
                if pid in pto_today:
                    errors.append(f"{day.date}: person {pid} assigned on PTO")

        if require_today:
            by_task = {a.task_id: a for a in day.assignments}
            for t in tasks:
                if active_on(t, day_dt):
                    if t.task_id not in by_task:
                        if any(c > 0 for c in t.required_skills.values()):
                            errors.append(f"{day.date}: active task {t.task_id} missing")
                        continue
                    apt = by_task[t.task_id]
                    for s, c in t.required_skills.items():
                        if c <= 0: continue
                        assigned = len(apt.skill_coverage.get(s, []))
                        if assigned != c:
                            errors.append(f"{day.date}: {t.task_id} {s} assigned {assigned} != {c}")
            # one task/person/day + skills
            seen = set()
            for apt in day.assignments:
                for pid, skills in apt.people_contributions.items():
                    if pid in seen:
                        errors.append(f"{day.date}: person {pid} on multiple tasks")
                    seen.add(pid)
                    if pid not in people_by:
                        errors.append(f"{day.date}: unknown person {pid}")
                        continue
                    p = people_by[pid]
                    for s in skills:
                        if s not in p.skills:
                            errors.append(f"{day.date}: person {pid} lacks skill {s}")

    # rolling 7-day cap (seeded)
    for p in people:
        prev6 = deque([0,0,0,0,0,0], maxlen=6)
        d = max(0, min(5, int(p.preworked_in_last_7)))
        idx = 5
        while d > 0 and idx >= 0:
            prev6[idx] = 1
            d -= 1
            idx -= 1
        window = deque(prev6, maxlen=7)
        for day in hs.days:
            bit = 0
            for apt in day.assignments:
                if p.person_id in apt.people_contributions:
                    bit = 1; break
            window.append(bit)
            if sum(window) > 5:
                errors.append(f"{day.date}: rolling cap exceeded for {p.person_id} ({sum(window)})")
            prev6.append(bit)
            window = deque(prev6, maxlen=7)

    return errors

def run_pto_tests():
    rows = []

    # Test 1
    start = date(2025, 9, 22)
    span = 3
    current_ts = _mk_ts(2025,9,22,0,0,0)
    allow_future = True

    people = [Person("alice", {"frontend"}), Person("bob", {"backend"})]
    tasks = [Task("T", {"frontend":1, "backend":1}, int(_midnight_local(start).timestamp()), int((_midnight_local(start)+timedelta(days=span)).timestamp()))]
    pto = { start: {"alice"} }

    hs = HorizonSchedulerPTO(people, tasks, start, span, current_ts, allow_future, pto).build()
    errs = validate_pto_schedule(people, tasks, hs, start, span, pto, allow_future, current_ts)
    rows.append({"case": "PTO blocks critical skill (infeasible Day1)", "feasible": hs.feasible, "violations": len(hs.violations), "validator_errors": len(errs)})

    # Test 2
    people2 = [Person("a1", {"frontend"}), Person("a2", {"frontend"}), Person("b", {"backend"})]
    pto2 = { start: {"a1"} }
    hs2 = HorizonSchedulerPTO(people2, tasks, start, span, current_ts, allow_future, pto2).build()
    errs2 = validate_pto_schedule(people2, tasks, hs2, start, span, pto2, allow_future, current_ts)
    # Ensure a1 never appears on PTO day
    pto_assigned = any(
        ("a1" in apt.people_contributions) and (day.date == start.isoformat())
        for day in hs2.days for apt in day.assignments
    )
    rows.append({"case": "PTO with alternates (feasible)", "feasible": hs2.feasible and (not pto_assigned), "violations": len(hs2.violations), "validator_errors": len(errs2)})

    # Test 3
    start4 = date(2025, 9, 22); span4 = 5
    people4 = [Person("x", {"qa"}, preworked_in_last_7=4), Person("y", {"data"}), Person("z", {"qa"})]
    tasks4 = [Task("U", {"qa":1, "data":1}, int(_midnight_local(start4).timestamp()), int((_midnight_local(start4)+timedelta(days=span4)).timestamp()))]
    pto4 = { start4: {"z"} }  # leaves 'x' with preworked=4 => day1 infeasible
    hs4 = HorizonSchedulerPTO(people4, tasks4, start4, span4, current_ts, True, pto4).build()
    errs4 = validate_pto_schedule(people4, tasks4, hs4, start4, span4, pto4, True, current_ts)
    rows.append({"case": "Rolling cap + PTO interplay", "feasible": hs4.feasible, "violations": len(hs4.violations), "validator_errors": len(errs4)})

    # Test 4: Month helper
    def build_month_schedule_with_pto(people, tasks, month_date: date, pto_map: Dict[date, Set[str]], allow_future=True):
        first = month_date.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        span = (last - first).days + 1
        return HorizonSchedulerPTO(people, tasks, first, span, int(datetime.now(tz=_TZ).timestamp()), allow_future, pto_map).build()

    month_people = [Person("fe", {"frontend"}), Person("be", {"backend"}), Person("qa1", {"qa"}), Person("qa2", {"qa"})]
    month_tasks = [
        Task("Dev", {"frontend":1, "backend":1}, int(_midnight_local(date(2025,9,1)).timestamp()), int(_midnight_local(date(2025,10,1)).timestamp())),
        Task("Test", {"qa":1}, int(_midnight_local(date(2025,9,1)).timestamp()), int(_midnight_local(date(2025,10,1)).timestamp())),
    ]
    pto_month = {date(2025,9,5): {"qa2"}, date(2025,9,12): {"qa2"}, date(2025,9,19): {"qa2"}, date(2025,9,26): {"qa2"}}
    hs_month = build_month_schedule_with_pto(month_people, month_tasks, date(2025,9,15), pto_month, allow_future=True)
    errs_month = validate_pto_schedule(month_people, month_tasks, hs_month, date(2025,9,1), (date(2025,9,30)-date(2025,9,1)).days+1, pto_month, True, _mk_ts(2025,9,1))
    rows.append({"case": "Month helper with recurring PTOs", "feasible": hs_month.feasible, "violations": len(hs_month.violations), "validator_errors": len(errs_month)})

    df = pd.DataFrame(rows)
    display_dataframe_to_user("PTO-aware Scheduler - Test Results", df)

    out = "/mnt/data/pto_scheduler_test_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    out_sched = "/mnt/data/pto_month_schedule.json"
    with open(out_sched, "w", encoding="utf-8") as f:
        json.dump(asdict(hs_month), f, indent=2)

    print("Saved:", out, "and", out_sched)
    return out, out_sched

out_summary, out_sched = run_pto_tests()
print("Artifacts:", out_summary, out_sched)
print("Download tests:", out_summary)
print("Download schedule:", out_sched)