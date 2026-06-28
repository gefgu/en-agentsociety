from datetime import datetime
from typing import Union

__all__ = ["ensure_timezone_aware"]


def ensure_timezone_aware(dt: Union[datetime, str]) -> datetime:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo
        return dt.replace(tzinfo=local_tz)
    return dt
