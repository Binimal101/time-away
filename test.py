# We'll implement the solver code and then run unit tests to verify it works.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import logging
import sys
from collections import defaultdict, Counter
import unittest

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger("SkillAssigner")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)  # adjust to DEBUG if you want deeper traces

# -----------------------------------------------------------------------------
# Domain Model
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Skill:
    """Extensible skill representation (e.g., add level, category later)."""
    name: str

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class Person:
    """A team member with a set of skills. Extensible with cost, capacity, etc."""
    pid: str
    skills: Set[Skill]

    def has_skill(self, skill_name: str) -> bool:
        return any(s.name == skill_name for s in self.skills) #generator more efficient than list comprehension


@dataclass
class Task:
    """A task with required skill counts, e.g., {"python": 1, "sql": 2}."""
    tid: str
    required: Dict[str, int]  # skill_name -> count (>= 1)

    def required_copy(self) -> Dict[str, int]:
        return dict(self.required)


@dataclass
class AssignmentResult:
    """Result container: selected minimal people set and per-task assignments."""
    selected_people: List[Person] = field(default_factory=list)
    task_to_people: Dict[str, List[Tuple[str, Set[str]]]] = field(default_factory=dict)
    # task_to_people[tid] = list of (pid, skills_contributed_to_this_task)

    def pretty(self) -> str:
        lines = []
        lines.append("=== Assignment Summary ===")
        lines.append(f"People used ({len(self.selected_people)}): " +
                     ", ".join(p.pid for p in self.selected_people))
        lines.append("")
        for tid, plist in self.task_to_people.items():
            lines.append(f"Task {tid}:")
            for pid, skillset in plist:
                skills_str = ", ".join(sorted(skillset))
                lines.append(f"  - {pid} contributes: {skills_str}")
            lines.append("")
        return "\n".join(lines)

# -----------------------------------------------------------------------------
# Solver
# -----------------------------------------------------------------------------
class AssignmentSolver:
    """
    Two-phase solver:
      Phase 1: Global greedy set cover to minimize people quickly (compute-first).
      Phase 2: Per-task greedy assignment using selected people; fallback to small backtracking if needed.
      Phase 3: Prune unused people.
    """

    def __init__(self, tasks: List[Task], people: List[Person]) -> None:
        self.tasks = tasks
        self.people = people
        self.skill_pool = self._build_skill_pool(people)

    # ---------- Utilities ----------
    @staticmethod
    def _build_skill_pool(people: List[Person]) -> Set[str]:
        pool = set()
        for p in people:
            for s in p.skills:
                pool.add(s.name)
        return pool

    def _feasibility_quick_check(self) -> None:
        """Quickly log if any task requires a skill absent from the pool."""
        missing: List[Tuple[str, str]] = []
        for t in self.tasks:
            for sk, cnt in t.required.items():
                if cnt > 0 and sk not in self.skill_pool:
                    missing.append((t.tid, sk))
        if missing:
            msg = "Infeasible: missing skills in team pool: " + ", ".join(
                f"{tid}:{sk}" for tid, sk in missing
            )
            logger.error(msg)
            raise ValueError(msg)
        logger.info("Feasibility check passed: all required skills exist in pool.")

    # ---------- Phase 1: Global Greedy Set Cover ----------
    def _global_greedy_people_selection(self) -> List[Person]:
        """
        Build global uncovered counts per (task, skill).
        Pick people maximizing marginal coverage:
          - A person can cover at most 1 unit of a given skill per task.
          - They can cover multiple different skills and multiple tasks.
        """
        # Build uncovered counts per (task, skill)
        uncovered: Dict[Tuple[str, str], int] = {}
        for t in self.tasks:
            for sk, cnt in t.required.items():
                if cnt > 0:
                    uncovered[(t.tid, sk)] = uncovered.get((t.tid, sk), 0) + cnt

        selected: List[Person] = []
        remaining_people: List[Person] = list(self.people)

        total_units = sum(uncovered.values())
        logger.info(f"[Phase 1] Global set cover starting. Total units = {total_units}")

        def marginal_gain(person: Person) -> Tuple[int, Dict[Tuple[str, str], int]]:
            """
            Returns how many units this person can reduce from `uncovered`, but capped at 1
            per (task, skill). Also returns the deltas by key for applying if picked.
            """
            gain = 0
            deltas: Dict[Tuple[str, str], int] = {}
            # For each (task, skill) pair still uncovered, see if person can cover one.
            for (tid, sk), need in uncovered.items():
                if need <= 0:
                    continue
                if person.has_skill(sk):
                    # Person can cover at most one unit of this skill for this task
                    deltas[(tid, sk)] = 1
                    gain += 1
            return gain, deltas

        while True:
            # Check if done
            remaining_units = sum(uncovered.values())
            if remaining_units == 0:
                logger.info("[Phase 1] All units covered globally.")
                break

            # Pick person with best marginal gain
            best_person: Optional[Person] = None
            best_gain: int = 0
            best_deltas: Dict[Tuple[str, str], int] = {}

            for p in remaining_people:
                gain, deltas = marginal_gain(p)
                if gain > best_gain:
                    best_person = p
                    best_gain = gain
                    best_deltas = deltas

            if best_person is None or best_gain == 0:
                # No one can improve coverage: infeasible under current interpretation.
                logger.error("[Phase 1] No further coverage possible; stopping early.")
                break

            # Apply deltas
            for key, d in best_deltas.items():
                uncovered[key] -= d
                if uncovered[key] < 0:
                    uncovered[key] = 0

            selected.append(best_person)
            remaining_people = [p for p in remaining_people if p.pid != best_person.pid]

            logger.info(
                f"[Phase 1] Selected {best_person.pid} covering {best_gain} unit(s). "
                f"Remaining units: {sum(uncovered.values())}"
            )

        logger.info(f"[Phase 1] Selected {len(selected)} people.")
        return selected

    # ---------- Phase 2: Per-task Assignment ----------
    @staticmethod
    def _greedy_assign_task(task: Task, candidates: List[Person]) -> List[Tuple[str, Set[str]]]:
        """
        Greedily cover a single task's requirements using a subset of candidates.
        A person can contribute multiple distinct skills to the same task,
        but at most one "unit" per skill.
        Returns list of (pid, contributed_skills_for_this_task).
        """
        remaining = Counter(task.required_copy())  # skill -> count
        assignment: Dict[str, Set[str]] = defaultdict(set)

        # Pre-check: every required skill has at least one candidate
        for sk, cnt in remaining.items():
            if cnt <= 0:
                continue
            if not any(p.has_skill(sk) for p in candidates):
                raise ValueError(f"Task {task.tid} requires {sk} but no candidate has it.")

        def marginal_gain_for_task(person: Person) -> int:
            gain = 0
            # Count how many distinct remaining skills they could reduce by 1
            for sk, need in remaining.items():
                if need > 0 and person.has_skill(sk):
                    gain += 1
            return gain

        picked: List[Person] = []
        while any(c > 0 for c in remaining.values()):
            # Choose the person that covers the most *distinct* remaining skills
            best_p: Optional[Person] = None
            best_gain: int = 0
            for p in candidates:
                if p in picked:
                    continue
                g = marginal_gain_for_task(p)
                if g > best_gain:
                    best_gain = g
                    best_p = p

            if best_p is None or best_gain == 0:
                # Greedy failed to improve; signal for fallback
                break

            # Apply best_p contributions: for each skill they have, reduce by 1 if needed.
            contributed = set()
            for sk, need in list(remaining.items()):
                if need > 0 and best_p.has_skill(sk):
                    remaining[sk] -= 1
                    contributed.add(sk)
            picked.append(best_p)
            assignment[best_p.pid].update(contributed)

        # If not fully covered, try a tiny backtracking fallback limited to candidates
        if any(c > 0 for c in remaining.values()):
            logger.info(f"[Phase 2] Greedy incomplete for task {task.tid}, invoking small DFS fallback.")

            # Simple depth-first search: try adding/removing one candidate at a time
            best_solution: Optional[List[Tuple[str, Set[str]]]] = None

            need_snapshot = Counter(task.required_copy())
            cand_list = [p for p in candidates]

            def dfs(i: int, rem: Counter, partial: Dict[str, Set[str]]) -> bool:
                nonlocal best_solution
                if all(v <= 0 for v in rem.values()):
                    best_solution = [(pid, skills) for pid, skills in partial.items()]
                    return True
                if i >= len(cand_list):
                    return False

                # Branch 1: include cand i
                p = cand_list[i]
                # Compute contribution
                contributed_now = set()
                for sk, cnt in list(rem.items()):
                    if cnt > 0 and p.has_skill(sk):
                        rem[sk] -= 1
                        contributed_now.add(sk)

                if contributed_now:
                    partial.setdefault(p.pid, set()).update(contributed_now)
                    if dfs(i + 1, rem, partial):
                        return True
                    # backtrack contribution
                    for sk in contributed_now:
                        rem[sk] += 1
                    partial[p.pid].difference_update(contributed_now)
                    if not partial[p.pid]:
                        del partial[p.pid]

                # Branch 2: skip cand i
                if dfs(i + 1, rem, partial):
                    return True
                return False

            rem_copy = need_snapshot.copy()
            partial_init: Dict[str, Set[str]] = {}
            dfs(0, rem_copy, partial_init)

            if best_solution is None:
                raise RuntimeError(f"Task {task.tid}: fallback search failed, inconsistent input?")
            # Merge fallback solution into assignment (overwrite greedy)
            assignment = defaultdict(set)
            for pid, skills in best_solution:
                assignment[pid].update(skills)

        # Return as stable list
        return [(pid, skills) for pid, skills in assignment.items()]

    def _assign_tasks_with_selected(self, selected: List[Person]) -> Dict[str, List[Tuple[str, Set[str]]]]:
        out: Dict[str, List[Tuple[str, Set[str]]]] = {}
        for t in self.tasks:
            logger.info(f"[Phase 2] Assigning Task {t.tid}")
            per_task = self._greedy_assign_task(t, selected)
            # Sanity check coverage
            covered = Counter()
            for _, skills in per_task:
                for sk in skills:
                    covered[sk] += 1
            need = Counter(t.required)
            ok = all(covered[sk] >= need[sk] for sk in need)
            if not ok:
                raise RuntimeError(f"Task {t.tid} not fully covered after Phase 2.")
            out[t.tid] = per_task
            logger.info(f"[Phase 2] Task {t.tid} covered with {len(per_task)} person(s).")
        return out

    # ---------- Phase 3: Prune ----------
    @staticmethod
    def _prune_unused(selected: List[Person], task_to_people: Dict[str, List[Tuple[str, Set[str]]]]) -> List[Person]:
        used_ids: Set[str] = set()
        for _, plist in task_to_people.items():
            for pid, _skills in plist:
                used_ids.add(pid)
        pruned = [p for p in selected if p.pid in used_ids]
        dropped = [p for p in selected if p.pid not in used_ids]
        if dropped:
            logger.info("[Phase 3] Dropping unused people: " + ", ".join(p.pid for p in dropped))
        return pruned

    # ---------- Top-level API ----------
    def solve(self) -> AssignmentResult:
        # Step 0: sanity
        self._feasibility_quick_check()

        # Phase 1: global selection
        selected = self._global_greedy_people_selection()

        if not selected:
            raise RuntimeError("No people selected; cannot proceed.")

        # Phase 2: per-task assignment
        task_to_people = self._assign_tasks_with_selected(selected)

        # Phase 3: prune
        selected_pruned = self._prune_unused(selected, task_to_people)

        # Done
        return AssignmentResult(
            selected_people=selected_pruned,
            task_to_people=task_to_people,
        )
