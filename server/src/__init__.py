from __future__ import annotations
from datetime import timezone, datetime, timedelta, date
from typing import Tuple, Dict, List, Set, Optional, Iterable, Union
from dataclasses import dataclass, field
import logging
import json
import pandas as pd

# Centralized logger setup
logger = logging.getLogger("WeeklySchedulerV2")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# Timezone setup
try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/New_York")
except Exception:
    _TZ = timezone.utc

# Common utility functions
def _day_interval(dt: datetime) -> Tuple[int, int]:
    start = int(dt.timestamp())
    end = int((dt + timedelta(days=1)).timestamp())
    return start, end

def _midnight_local(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_TZ)

def _mk_ts(y, m, d, hh=0, mm=0, ss=0):
    return int(datetime(y, m, d, hh, mm, ss, tzinfo=_TZ).timestamp())

def epoch_to_date(ts: int, tz_offset_hours: int = 0) -> date:
    return (datetime.utcfromtimestamp(ts) + timedelta(hours=tz_offset_hours)).date()

def daterange(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def start_of_week(d: date, week_start: int = 0) -> date:
    return d - timedelta(days=(d.weekday() - week_start) % 7)

# Simple replacement for caas_jupyter_tools
def display_dataframe_to_user(title: str, df: pd.DataFrame):
    """Simple replacement for caas_jupyter_tools display function"""
    print(f"\n{title}")
    print("=" * len(title))
    print(df.to_string(index=False))
    print()

# Common dataclasses
@dataclass(frozen=True)
class Person:
    person_id: str
    name: str
    skills: Set[str]

@dataclass(frozen=True)
class Task:
    task_id: str
    name: str
    start_epoch: int
    end_epoch: int
    daily_requirements: Dict[str, int]

@dataclass(frozen=True)
class Assignment:
    day: date
    person_id: str
    task_id: str
    skills_contributed: Tuple[str, ...] = field(default_factory=tuple)