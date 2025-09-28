from __future__ import annotations

import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Set, Tuple, Optional, Iterable, Union
import pandas as pd

from src import (
    logger, _TZ, display_dataframe_to_user, Person, Task, Assignment,
    epoch_to_date, daterange, start_of_week
)

def is_task_active_on_day(task: Task, day: date, tz_offset_hours: int = 0) -> bool:
    start_day = epoch_to_date(task.start_epoch, tz_offset_hours)
    end_day = epoch_to_date(task.end_epoch, tz_offset_hours)
    return start_day <= day <= end_day

class PlanStore:
    def __init__(self):
        self._days_by_person: Dict[str, Set[date]] = {}

    def preload(self, assignments: List[Assignment]) -> None:
        for a in assignments:
            self._days_by_person.setdefault(a.person_id, set()).add(a.day)

    def to_json(self) -> str:
        payload = {p: sorted([d.isoformat() for d in days]) for p, days in self._days_by_person.items()}
        return json.dumps(payload, indent=2)

    @staticmethod
    def from_json(payload: str) -> "PlanStore":
        obj = PlanStore()
        data = json.loads(payload)
        for p, day_list in data.items():
            obj._days_by_person[p] = {date.fromisoformat(ds) for ds in day_list}
        return obj

    def assigned_on(self, person_id: str, day: date) -> bool:
        return day in self._days_by_person.get(person_id, set())

    def count_in_window(self, person_id: str, start_day: date, end_day: date) -> int:
        days = self._days_by_person.get(person_id, set())
        return sum(1 for d in days if start_day <= d <= end_day)

    def can_assign(self, person_id: str, day: date, pending_same_day: bool = False) -> bool:
        start_win = day - timedelta(days=6)
        used = self.count_in_window(person_id, start_win, day)
        if pending_same_day and not self.assigned_on(person_id, day):
            used += 1
        return used <= (5 if pending_same_day else 4)

    def commit(self, assignments: List[Assignment]) -> None:
        for a in assignments:
            self._days_by_person.setdefault(a.person_id, set()).add(a.day)

def normalize_pto_map(pto_map: Optional[Dict[date, List[Union[Person, str]]]]) -> Dict[date, Set[str]]:
    norm: Dict[date, Set[str]] = {}
    if not pto_map:
        return {}
    for d, plist in pto_map.items():
        ids: Set[str] = set()
        for p in plist:
            if isinstance(p, Person):
                ids.add(p.person_id)
            else:
                ids.add(str(p))
        norm.setdefault(d, set()).update(ids)
    return norm

class DaySolver:
    def __init__(self,
                 day: date,
                 people: List[Person],
                 tasks: List[Task],
                 plan_store: PlanStore,
                 tz_offset_hours: int = 0,
                 pto_map: Optional[Dict[date, List[Union[Person, str]]]] = None):
        self.day = day
        self.people = sorted(people, key=lambda p: (p.name, p.person_id))
        self.tasks = sorted(tasks, key=lambda t: (t.name, t.task_id))
        self.store = plan_store
        self.tz_offset_hours = tz_offset_hours
        self.pto_ids_by_day: Dict[date, Set[str]] = normalize_pto_map(pto_map)

        self.deficits: Dict[str, Dict[str, int]] = {
            t.task_id: {s: c for s, c in t.daily_requirements.items() if c > 0} for t in self.tasks
        }
        self.task_by_id: Dict[str, Task] = {t.task_id: t for t in self.tasks}
        self.person_by_id: Dict[str, Person] = {p.person_id: p for p in self.people}

        self.assigned_today: Dict[str, str] = {}

    def _is_pto(self, pid: str) -> bool:
        return pid in self.pto_ids_by_day.get(self.day, set())

    def _all_satisfied(self) -> bool:
        return all(all(cnt <= 0 for cnt in sk_cnts.values()) for sk_cnts in self.deficits.values())

    def _select_next_need(self) -> Optional[Tuple[str, str]]:
        best = None
        best_need = -1
        for t in self.tasks:
            needs = self.deficits[t.task_id]
            for skill, cnt in needs.items():
                if cnt > 0:
                    key = (t.name, skill)
                    if cnt > best_need or (cnt == best_need and (best is not None and (key < (self.task_by_id[best[0]].name, best[1])))):
                        best = (t.task_id, skill)
                        best_need = cnt
        return best

    def _candidates_for(self, task_id: str, required_skill: str) -> List[Person]:
        t = self.task_by_id[task_id]
        can_cover = []
        for p in self.people:
            if self._is_pto(p.person_id):
                continue
            if p.person_id in self.assigned_today:
                continue
            if required_skill not in p.skills:
                continue
            if not set(t.daily_requirements.keys()) & p.skills:
                continue
            if not self.store.can_assign(p.person_id, self.day, pending_same_day=False):
                continue
            multi_cover = sum(1 for s in t.daily_requirements.keys()
                              if s in p.skills and self.deficits[task_id].get(s, 0) > 0)
            used_last6 = self.store.count_in_window(p.person_id, self.day - timedelta(days=6), self.day - timedelta(days=1))
            can_cover.append((p, multi_cover, used_last6))
        can_cover.sort(key=lambda x: (-x[1], x[2], x[0].name))
        return [p for (p, _, __) in can_cover]

    def _assign_person_to_task(self, p: Person, t: Task) -> List[Tuple[str, int]]:
        changes = []
        for s in t.daily_requirements.keys():
            if s in p.skills and self.deficits[t.task_id].get(s, 0) > 0:
                self.deficits[t.task_id][s] -= 1
                changes.append((s, +1))
        self.assigned_today[p.person_id] = t.task_id
        return changes

    def _undo_assignment(self, p: Person, t: Task, changes: List[Tuple[str, int]]):
        for (s, delta) in changes:
            self.deficits[t.task_id][s] += delta
        del self.assigned_today[p.person_id]

    def solve(self) -> Tuple[bool, List[Assignment], Dict[str, Dict[str, int]]]:
        if self._all_satisfied():
            return True, [], {}

        def backtrack() -> bool:
            if self._all_satisfied():
                return True
            next_need = self._select_next_need()
            if not next_need:
                return True
            task_id, skill = next_need
            t = self.task_by_id[task_id]
            for p in self._candidates_for(task_id, skill):
                changes = self._assign_person_to_task(p, t)
                if not self.store.can_assign(p.person_id, self.day, pending_same_day=True):
                    self._undo_assignment(p, t, changes)
                    continue
                if backtrack():
                    return True
                self._undo_assignment(p, t, changes)
            return False

        feasible = backtrack()
        if feasible:
            results: List[Assignment] = []
            for pid, tid in sorted(self.assigned_today.items(), key=lambda kv: self.person_by_id[kv[0]].name):
                p = self.person_by_id[pid]
                t = self.task_by_id[tid]
                skills_contrib = tuple(sorted(s for s in t.daily_requirements if s in p.skills))
                results.append(Assignment(day=self.day, person_id=pid, task_id=tid, skills_contributed=skills_contrib))
            return True, results, {}
        else:
            remaining = {
                self.task_by_id[tid].name: {s: c for s, c in sk.items() if c > 0}
                for tid, sk in self.deficits.items()
                if any(v > 0 for v in sk.values())
            }
            return False, [], remaining

class WeeklyScheduler:
    def __init__(self, people: List[Person], tasks: List[Task], plan_store: PlanStore, tz_offset_hours: int = 0):
        self.people = people
        self.tasks = tasks
        self.store = plan_store
        self.tz_offset = tz_offset_hours

    def schedule_week(self,
                      week_start_day: date,
                      now_epoch: int,
                      pto_map: Optional[Dict[date, List[Union[Person, str]]]] = None
                      ) -> Tuple[List[Assignment], List[Tuple[date, Dict[str, Dict[str, int]]]]]:
        all_assignments: List[Assignment] = []
        unsatisfied: List[Tuple[date, Dict[str, Dict[str, int]]]] = []

        for d in daterange(week_start_day, week_start_day + timedelta(days=6)):
            active = [t for t in self.tasks
                      if is_task_active_on_day(t, d, self.tz_offset) and t.end_epoch >= now_epoch]
            if not active:
                logger.info(f"[{d.isoformat()}] No active tasks; skipping.")
                continue
            solver = DaySolver(d, self.people, active, self.store, tz_offset_hours=self.tz_offset, pto_map=pto_map)
            ok, assignments, deficits = solver.solve()
            if ok:
                logger.info(f"[{d.isoformat()}] Day solved with {len(assignments)} assignments.")
                self.store.commit(assignments)
                all_assignments.extend(assignments)
            else:
                logger.warning(f"[{d.isoformat()}] UNSAT day. Deficits: {deficits}")
                unsatisfied.append((d, deficits))

        return all_assignments, unsatisfied

def cache_schedule(store: PlanStore,
                   assignments: List[Assignment],
                   pto_map: Optional[Dict[date, List[Union[Person, str]]]] = None,
                   pending_pto: Optional[Dict[date, List[Union[Person, str]]]] = None,
                   accept_pto: bool = False) -> Dict[date, List[str]]:
    store.commit(assignments)
    base = normalize_pto_map(pto_map or {})
    if accept_pto and pending_pto:
        pend = normalize_pto_map(pending_pto)
        for d, ids in pend.items():
            base.setdefault(d, set()).update(ids)
    return {d: sorted(list(ids)) for d, ids in base.items()}

def pretty_assignments(assignments: List[Assignment], people: List[Person], tasks: List[Task]) -> pd.DataFrame:
    pmap = {p.person_id: p for p in people}
    tmap = {t.task_id: t for t in tasks}
    rows = []
    for a in sorted(assignments, key=lambda x: (x.day, tmap[x.task_id].name, pmap[x.person_id].name)):
        rows.append({
            "date": a.day.isoformat(),
            "task": tmap[a.task_id].name,
            "person": pmap[a.person_id].name,
            "skills_used": ", ".join(sorted(set(tmap[a.task_id].daily_requirements)
                                            .intersection(pmap[a.person_id].skills)))
        })
    df = pd.DataFrame(rows, columns=["date", "task", "person", "skills_used"])
    return df
