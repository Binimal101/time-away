# Revised scheduler with bounded backtracking on daily task ordering + stricter validation
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta
import itertools
from src import logger, _TZ


@dataclass(frozen=True, order=True)
class Person:
    person_id: str
    skills: Set[str]


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
class WeekSchedule:
    week_start_iso: str
    week_end_iso: str
    tz: str
    current_ts: int
    feasible: bool
    violations: List[str]
    days: List[DaySchedule] = field(default_factory=list)


def _week_bounds_from_ts(current_ts: int) -> Tuple[datetime, datetime]:
    now = datetime.fromtimestamp(current_ts, _TZ)
    local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = local_midnight - timedelta(days=local_midnight.weekday())
    end = start + timedelta(days=7)
    return start, end

def _day_interval(d: datetime) -> Tuple[int, int]:
    return int(d.timestamp()), int((d + timedelta(days=1)).timestamp())


class WeeklyScheduler:
    def __init__(self, people: List[Person], tasks: List[Task], current_ts: int):
        self.people = sorted(people, key=lambda p: p.person_id)
        self.tasks = sorted(tasks, key=lambda t: t.task_id)
        self.current_ts = current_ts
        self.week_start, self.week_end = _week_bounds_from_ts(current_ts)
        self.week_days = [self.week_start + timedelta(days=i) for i in range(7)]
        self.person_days_used = {p.person_id: 0 for p in self.people}
        self.violations: List[str] = []
        self.max_days_per_person = 5

    def _active_tasks_for_day(self, day_start_ts: int, day_end_ts: int) -> List[Task]:
        active = [t for t in self.tasks if t.is_active_on_day(day_start_ts, day_end_ts)]
        # default heuristic order: larger total requirements first, then earlier end, then id
        active.sort(key=lambda t: (-sum(t.required_skills.values()), t.end_ts, t.task_id))
        return active

    def _rarity_score(self, tasks: List[Task]) -> Dict[str, float]:
        """Estimate rarity of skills across people to prioritize scarce requirements."""
        # Count supply per skill
        supply = {}
        for p in self.people:
            for s in p.skills:
                supply[s] = supply.get(s, 0) + 1
        # Score task by sum over required skills of (requirement / supply)
        scores = {}
        for t in tasks:
            score = 0.0
            for s, c in t.required_skills.items():
                sup = max(1, supply.get(s, 0))
                score += c / sup
            scores[t.task_id] = score
        return scores

    def _try_order(self, tasks_today: List[Task], day_start_ts: int, date_str: str) -> Tuple[bool, DaySchedule, Dict[str, int]]:
        """Try to assign given ordered tasks; returns success flag, DaySchedule, and a delta of person day-uses."""
        # local copies for tentative assignment (so we can roll back on failure)
        local_person_days_used = dict(self.person_days_used)
        available: Set[str] = {p.person_id for p in self.people if local_person_days_used[p.person_id] < self.max_days_per_person}
        day_sched = DaySchedule(date=date_str, assignments=[])

        for task in tasks_today:
            missing = {s: int(c) for s, c in task.required_skills.items() if c > 0}
            apt = AssignmentPerTaskPerDay(task_id=task.task_id, skill_coverage={s: [] for s in missing}, people_contributions={})

            def uncovered_total():
                return sum(max(0, v) for v in missing.values())

            while uncovered_total() > 0:
                best_p = None
                best_covers: List[str] = []

                for p in self.people:
                    pid = p.person_id
                    if pid not in available:
                        continue
                    covers = [s for s in p.skills if s in missing and missing[s] > 0]
                    if not covers:
                        continue
                    # tie-break: prefer covering more skills, then lexicographic id
                    cand_key = (len(covers), -sum(missing[s] for s in covers), pid)
                    best_key = (len(best_covers), -sum(missing[s] for s in best_covers), best_p.person_id if best_p else "")
                    if cand_key > best_key:
                        best_p = p
                        best_covers = covers

                if best_p is None:
                    return False, day_sched, {}

                # commit
                available.remove(best_p.person_id)
                local_person_days_used[best_p.person_id] += 1
                for s in best_covers:
                    missing[s] -= 1
                    apt.skill_coverage.setdefault(s, []).append(best_p.person_id)
                apt.people_contributions.setdefault(best_p.person_id, []).extend(best_covers)

            day_sched.assignments.append(apt)

        # success
        # compute delta to apply to global counter upon acceptance
        delta = {pid: local_person_days_used[pid] - self.person_days_used[pid] for pid in self.person_days_used}
        return True, day_sched, delta

    def _attempt_day_with_backtracking(self, day_start_ts: int, day_end_ts: int) -> Tuple[bool, DaySchedule]:
        if day_start_ts > self.current_ts:
            date_str = datetime.fromtimestamp(day_start_ts, _TZ).date().isoformat()
            logger.info(f"Skipping future day {date_str} (beyond current_ts).")
            return True, DaySchedule(date=date_str, assignments=[])

        date_str = datetime.fromtimestamp(day_start_ts, _TZ).date().isoformat()
        tasks_today = self._active_tasks_for_day(day_start_ts, day_end_ts)
        logger.info(f"Scheduling day {date_str}; active tasks: {[t.task_id for t in tasks_today]}")

        # Candidate orderings:
        orderings: List[List[Task]] = []

        # 1) default heuristic
        orderings.append(list(tasks_today))

        # 2) rarity-first (scarcer-task-first)
        rarity = self._rarity_score(tasks_today)
        rare_sorted = sorted(tasks_today, key=lambda t: (-rarity.get(t.task_id, 0.0), t.end_ts, t.task_id))
        orderings.append(rare_sorted)

        # 3) earliest end first
        eef = sorted(tasks_today, key=lambda t: (t.end_ts, -sum(t.required_skills.values()), t.task_id))
        orderings.append(eef)

        # 4) Try all permutations if small (factorial blowup guarded)
        if len(tasks_today) <= 6:
            for perm in itertools.permutations(tasks_today):
                orderings.append(list(perm))

        # Deduplicate orderings deterministically
        unique_orders = []
        seen_signatures = set()
        for ord_list in orderings:
            sig = tuple(t.task_id for t in ord_list)
            if sig not in seen_signatures:
                unique_orders.append(ord_list)
                seen_signatures.add(sig)

        # Try each ordering until one fits
        for idx, ord_list in enumerate(unique_orders):
            logger.info(f"Trying ordering {idx+1}/{len(unique_orders)}: {[t.task_id for t in ord_list]}")
            ok, ds, delta = self._try_order(ord_list, day_start_ts, date_str)
            if ok:
                # apply delta to global person day counters
                for pid, d in delta.items():
                    self.person_days_used[pid] += d
                return True, ds

        # If all orderings fail, record violation
        self.violations.append(f"Day {date_str}: could not satisfy all active tasks.")
        return False, DaySchedule(date=date_str, assignments=[])

    def build(self) -> WeekSchedule:
        days: List[DaySchedule] = []
        feasible = True
        for d in self.week_days:
            day_start, day_end = _day_interval(d)
            ok, ds = self._attempt_day_with_backtracking(day_start, day_end)
            days.append(ds)
            if not ok:
                feasible = False

        # weekly cap check
        for pid, used in self.person_days_used.items():
            if used > self.max_days_per_person:
                self.violations.append(f"Weekly cap violated for {pid}: {used}>5")
                feasible = False

        return WeekSchedule(
            week_start_iso=self.week_start.isoformat(),
            week_end_iso=self.week_end.isoformat(),
            tz=str(_TZ),
            current_ts=self.current_ts,
            feasible=feasible and not self.violations,
            violations=self.violations,
            days=days,
        )


# -------- Validation (stricter) --------
def validate_schedule(people: List[Person], tasks: List[Task], ws: WeekSchedule) -> Tuple[bool, List[str]]:
    people_by = {p.person_id: p for p in people}
    tasks_by = {t.task_id: t for t in tasks}
    errors: List[str] = []
    weekly_use = {p.person_id: 0 for p in people}

    start_dt = datetime.fromisoformat(ws.week_start_iso)
    days_dt = [start_dt + timedelta(days=i) for i in range(7)]
    intervals = [(_day_interval(d)) for d in days_dt]

    # index day assignments by task_id for lookup
    for day_idx, day in enumerate(ws.days):
        day_start, day_end = intervals[day_idx]
        date_str = day.date

        # Build map for quick task checks
        map_task = {a.task_id: a for a in day.assignments}

        # For every task active that day AND day_start <= current_ts, require a record
        for t in tasks:
            active = t.is_active_on_day(day_start, day_end)
            if active and not (day_start > ws.current_ts):
                if t.task_id not in map_task:
                    errors.append(f"{date_str}: active task {t.task_id} missing from schedule.")
                    continue
                apt = map_task[t.task_id]
                # per-skill exact match
                for s, c in t.required_skills.items():
                    if c <= 0:
                        continue
                    assigned = len(apt.skill_coverage.get(s, []))
                    if assigned != c:
                        errors.append(f"{date_str} {t.task_id} skill {s}: assigned {assigned} != {c}")
                # people contributions validity + one-task-per-day
        seen: Set[str] = set()
        for apt in day.assignments:
            # task must be active if scheduled
            t = tasks_by.get(apt.task_id)
            if not t:
                errors.append(f"{date_str}: unknown task {apt.task_id}")
                continue
            if not t.is_active_on_day(day_start, day_end):
                errors.append(f"{date_str}: task {apt.task_id} scheduled though inactive")

            for pid, skills in apt.people_contributions.items():
                p = people_by.get(pid)
                if not p:
                    errors.append(f"{date_str}: unknown person {pid}")
                    continue
                if pid in seen:
                    errors.append(f"{date_str}: person {pid} assigned to multiple tasks in a day")
                seen.add(pid)
                for s in skills:
                    if s not in p.skills:
                        errors.append(f"{date_str}: person {pid} lacks skill {s} used")

        for pid in seen:
            weekly_use[pid] += 1

        # No scheduling after current_ts
        if day_start > ws.current_ts and day.assignments:
            errors.append(f"{date_str}: assignments occur after current_ts")

    # Weekly cap
    for pid, used in weekly_use.items():
        if used > 5:
            errors.append(f"Weekly cap violated for {pid}: used={used}>5")

    return (len(errors) == 0), errors