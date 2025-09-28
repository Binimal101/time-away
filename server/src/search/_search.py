# Re-run PTO-aware Horizon Scheduler V4 after state reset (include all definitions + tests again).

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime, timedelta, date
from collections import deque
import itertools

from src import _TZ, logger, _day_interval

@dataclass(frozen=True, order=True)
class Person:
    person_id: str
    skills: Set[str]
    preworked_in_last_7: int = 0

@dataclass(frozen=True, order=True)
class Task:
    task_id: str
    required_skills: Dict[str, int]
    start_ts: int
    end_ts: int
    def is_active_on_day(self, day_start_ts: int, day_end_ts: int) -> bool:
        return (self.start_ts < day_end_ts) and (self.end_ts > day_start_ts)

@dataclass
class AssignmentPerTaskPerDay:
    task_id: str
    skill_coverage: Dict[str, List[str]]
    people_contributions: Dict[str, List[str]]

@dataclass
class DaySchedule:
    date: str
    assignments: List[AssignmentPerTaskPerDay] = field(default_factory=list)

@dataclass
class HorizonSchedule:
    start_iso: str
    end_iso: str
    tz: str
    current_ts: int
    allow_future: bool
    feasible: bool
    violations: List[str]
    days: List[DaySchedule] = field(default_factory=list)

def _midnight_local(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_TZ)

def _mk_ts(y, m, d, hh=0, mm=0, ss=0):
    return int(datetime(y, m, d, hh, mm, ss, tzinfo=_TZ).timestamp())

class HorizonSchedulerPTO:
    def __init__(
        self,
        people: List[Person],
        tasks: List[Task],
        start_day: date,
        span_days: int,
        current_ts: int,
        allow_future: bool = False,
        pto_map: Optional[Dict[date, Set[str]]] = None,
    ):
        self.people = sorted(people, key=lambda p: p.person_id)
        self.tasks = sorted(tasks, key=lambda t: t.task_id)
        self.start_day = start_day
        self.span_days = span_days
        self.current_ts = current_ts
        self.allow_future = allow_future
        self.pto_map: Dict[date, Set[str]] = pto_map or {}

        self.history_prev6: Dict[str, deque] = {}
        for p in self.people:
            d = max(0, min(5, int(p.preworked_in_last_7)))
            q = deque([0,0,0,0,0,0], maxlen=6)
            idx = 5
            while d > 0 and idx >= 0:
                q[idx] = 1
                d -= 1
                idx -= 1
            self.history_prev6[p.person_id] = q

        self.violations: List[str] = []
        self.max_per_7 = 5
        self.horizon_midnights: List[datetime] = [_midnight_local(self.start_day) + timedelta(days=i) for i in range(span_days)]

    def _active_tasks_for_day(self, day_start_ts: int, day_end_ts: int) -> List[Task]:
        active = [t for t in self.tasks if t.is_active_on_day(day_start_ts, day_end_ts)]
        active.sort(key=lambda t: (-sum(t.required_skills.values()), t.end_ts, t.task_id))
        return active

    def _rarity_score(self, tasks_today: List[Task]) -> Dict[str, float]:
        supply = {}
        for p in self.people:
            for s in p.skills:
                supply[s] = supply.get(s, 0) + 1
        scores = {}
        for t in tasks_today:
            sc = 0.0
            for s, c in t.required_skills.items():
                sup = max(1, supply.get(s, 0))
                sc += c / sup
            scores[t.task_id] = sc
        return scores

    def _commit_day_usage(self, assigned_today: Set[str]):
        for p in self.people:
            pid = p.person_id
            bit = 1 if pid in assigned_today else 0
            self.history_prev6[pid].append(bit)

    def _try_order(self, tasks_today: List[Task], day_date: date, day_start_ts: int, date_str: str) -> Tuple[bool, DaySchedule, Dict[str, List[str]]]:
        snapshot = {pid: deque(q, maxlen=6) for pid, q in self.history_prev6.items()}
        assigned_today: Set[str] = set()
        day_sched = DaySchedule(date=date_str, assignments=[])
        pto_people = self.pto_map.get(day_date, set())

        for task in tasks_today:
            missing = {s: int(c) for s, c in task.required_skills.items() if c > 0}
            apt = AssignmentPerTaskPerDay(task_id=task.task_id, skill_coverage={s: [] for s in missing}, people_contributions={})

            def uncovered():
                return sum(max(0, v) for v in missing.values())

            while uncovered() > 0:
                best_p = None
                best_covers: List[str] = []

                for p in self.people:
                    pid = p.person_id
                    if pid in assigned_today:
                        continue
                    if pid in pto_people:
                        continue
                    used_prev6 = sum(snapshot[pid])
                    if used_prev6 + 1 > self.max_per_7:
                        continue
                    covers = [s for s in p.skills if s in missing and missing[s] > 0]
                    if not covers:
                        continue
                    cand_key = (len(covers), -sum(missing[s] for s in covers), pid)
                    best_key = (len(best_covers), -sum(missing[s] for s in best_covers), best_p.person_id if best_p else "")
                    if cand_key > best_key:
                        best_p = p
                        best_covers = covers

                if best_p is None:
                    return False, day_sched, {}

                assigned_today.add(best_p.person_id)
                snapshot[best_p.person_id].append(1)
                for s in best_covers:
                    missing[s] -= 1
                    apt.skill_coverage.setdefault(s, []).append(best_p.person_id)
                apt.people_contributions.setdefault(best_p.person_id, []).extend(best_covers)

            day_sched.assignments.append(apt)

        assigned_map = {pid: [] for pid in assigned_today}
        for a in day_sched.assignments:
            for pid, skills in a.people_contributions.items():
                assigned_map.setdefault(pid, []).extend(skills)
        return True, day_sched, assigned_map

    def _attempt_day(self, day_dt: datetime) -> Tuple[bool, DaySchedule]:
        day_start_ts, day_end_ts = _day_interval(day_dt)
        date_str = day_dt.date().isoformat()
        day_date = day_dt.date()

        if (not self.allow_future) and (day_start_ts > self.current_ts):
            logger.info(f"Skipping future day {date_str} (beyond current_ts).")
            return True, DaySchedule(date=date_str, assignments=[])

        tasks_today = self._active_tasks_for_day(day_start_ts, day_end_ts)
        if not tasks_today:
            self._commit_day_usage(set())
            return True, DaySchedule(date=date_str, assignments=[])

        logger.info(f"{date_str}: active tasks { [t.task_id for t in tasks_today] }; PTO={list(self.pto_map.get(day_date, set()))}")

        orderings: List[List[Task]] = []
        orderings.append(list(tasks_today))
        rarity = self._rarity_score(tasks_today)
        orderings.append(sorted(tasks_today, key=lambda t: (-rarity.get(t.task_id, 0.0), t.end_ts, t.task_id)))
        orderings.append(sorted(tasks_today, key=lambda t: (t.end_ts, -sum(t.required_skills.values()), t.task_id)))
        if len(tasks_today) <= 6:
            for perm in itertools.permutations(tasks_today):
                orderings.append(list(perm))

        uniq, seen = [], set()
        for ord_list in orderings:
            sig = tuple(t.task_id for t in ord_list)
            if sig not in seen:
                uniq.append(ord_list)
                seen.add(sig)

        for idx, ord_list in enumerate(uniq, start=1):
            logger.info(f"{date_str}: try ordering {idx}/{len(uniq)} -> {[t.task_id for t in ord_list]}")
            ok, ds, assigned_map = self._try_order(ord_list, day_date, day_start_ts, date_str)
            if ok:
                self._commit_day_usage(set(assigned_map.keys()))
                return True, ds

        self.violations.append(f"{date_str}: could not satisfy all active tasks within constraints (PTO-respecting)")
        self._commit_day_usage(set())
        return False, DaySchedule(date=date_str, assignments=[])

    def build(self) -> HorizonSchedule:
        days: List[DaySchedule] = []
        feasible = True
        for day_dt in self.horizon_midnights:
            ok, ds = self._attempt_day(day_dt)
            days.append(ds)
            if not ok:
                feasible = False

        final_feasible = feasible and not self.violations
        if not final_feasible:
            for day_schedule in days:
                day_schedule.assignments = []

        return HorizonSchedule(
            start_iso=self.horizon_midnights[0].isoformat(),
            end_iso=(self.horizon_midnights[-1] + timedelta(days=1)).isoformat(),
            tz=str(_TZ),
            current_ts=self.current_ts,
            allow_future=self.allow_future,
            feasible=final_feasible,
            violations=self.violations,
            days=days,
        )
