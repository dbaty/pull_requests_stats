import datetime


def from_github_formatted_datetime(s: str | None) -> datetime.datetime | None:
    if not s:
        return None
    return datetime.datetime.fromisoformat(s.rstrip("Z"))


def get_week_start(dt: datetime.datetime) -> datetime.date:
    week_day = dt.weekday()
    week_start = dt - datetime.timedelta(days=week_day)
    return week_start.date()
