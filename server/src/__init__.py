from datetime import timezone, datetime, timedelta
from typing import Tuple
import logging

logger = logging.getLogger("WeeklySchedulerV2")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/New_York")
except Exception:
    _TZ = timezone.utc

def _day_interval(dt: datetime) -> Tuple[int, int]:
    start = int(dt.timestamp())
    end = int((dt + timedelta(days=1)).timestamp())
    return start, end