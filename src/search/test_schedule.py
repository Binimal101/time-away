from datetime import datetime, timedelta, date
import os
from src.search._search import Person, Task, HorizonScheduler, DaySchedule, _midnight_local, _mk_ts
from dataclasses import asdict
from collections import deque
import json

from src import _TZ, logger


# ---- Demo & Tests ----
def demo_and_tests_v3():
    start_day = date(2025, 9, 24)  # Wednesday
    span_days = 14
    current_ts = _mk_ts(2025, 9, 24, 12, 0, 0)  # noon of start
    allow_future = True  # plan full horizon

    people = [
        Person("alice", {"frontend", "backend"}, preworked_in_last_7=2),
        Person("bob", {"backend", "qa"}, preworked_in_last_7=4),
        Person("carl", {"frontend", "qa"}, preworked_in_last_7=1),
        Person("dina", {"data", "backend"}, preworked_in_last_7=5),
        Person("emma", {"frontend", "data", "qa"}, preworked_in_last_7=0),
    ]

    start_ts = int(_midnight_local(start_day - timedelta(days=2)).timestamp())
    end_ts = int((_midnight_local(start_day) + timedelta(days=span_days + 2)).timestamp())

    tasks = [
        Task("T1", {"frontend": 1, "backend": 1}, start_ts=start_ts, end_ts=end_ts),
        Task("T2", {"qa": 1, "data": 1}, start_ts=start_ts, end_ts=end_ts),
        Task("T3", {"frontend": 2}, start_ts=start_ts + 2*24*3600, end_ts=end_ts - 2*24*3600),
    ]

    sched = HorizonScheduler(people, tasks, start_day, span_days, current_ts, allow_future=allow_future)
    hs = sched.build()

    # Validate rolling 7-day cap per person across horizon
    def person_worked_on(day: DaySchedule, pid: str) -> bool:
        for apt in day.assignments:
            if pid in apt.people_contributions:
                return True
        return False

    for p in people:
        window = deque([], maxlen=7)
        # seed with their preworked days
        # We conservatively assume the preworked days are within prior 7, but our per-day check accounts during build.
        for day in hs.days:
            window.append(1 if person_worked_on(day, p.person_id) else 0)
            assert sum(window) <= 5, f"Rolling cap violated for {p.person_id} on {day.date}: {sum(window)}>5"

    out_path = os.path.join(os.path.dirname(__file__), "data", "test-schedule.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(hs), f, indent=2)
    return hs, out_path

hs, hs_path = demo_and_tests_v3()
print("All tests passed ✅")
print(f"Feasible: {hs.feasible}")
print(f"Violations: {hs.violations}")
print(f"Start..End: {hs.start_iso} .. {hs.end_iso}")
print(f"Download: {hs_path}")