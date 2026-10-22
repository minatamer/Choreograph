"""Exact business rules. No HTTP, database, settings or vendor imports."""
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .errors import DomainError

RATES = {
    "regular": {1: (6000, 90), 2: (8000, 120), 3: (10000, 150)},
    "deep": {1: (9000, 150), 2: (12000, 180), 3: (15000, 210)},
    "move-out": {1: (12000, 180), 2: (16000, 240), 3: (20000, 300)},
}
NAMES = {"regular": "Regular cleaning", "deep": "Deep cleaning", "move-out": "Move-out cleaning"}
STAFF_IDS = ("ada", "noah")


def quote(service: str, bedrooms: int, oven: bool, revision: int = 1):
    if type(bedrooms) is not int or bedrooms not in (1, 2, 3) or service not in RATES or type(oven) is not bool:
        raise DomainError("SERVICE_UNSUPPORTED", "Choose a listed service and one to three bedrooms.", 422)
    cents, minutes = RATES[service][bedrooms]
    items = [{"name": f"{NAMES[service]} · {bedrooms} bedroom{'s' if bedrooms != 1 else ''}", "cents": cents, "minutes": minutes}]
    if oven:
        cents += 2500
        minutes += 30
        items.append({"name": "Inside oven", "cents": 2500, "minutes": 30})
    return {"currency": "USD", "cents": cents, "minutes": minutes, "revision": revision, "items": items}


def local_to_utc(local: datetime, zone: str) -> datetime:
    if local.tzinfo is not None:
        raise DomainError("LOCAL_TIME_REQUIRED", "Use a local date and time.", 422)
    tz = ZoneInfo(zone)
    candidates = {local.replace(tzinfo=tz, fold=fold).astimezone(UTC) for fold in (0, 1)
                  if local.replace(tzinfo=tz, fold=fold).astimezone(UTC).astimezone(tz).replace(tzinfo=None) == local}
    if len(candidates) != 1:
        raise DomainError("TIME_UNCLEAR", "That local time changes with daylight saving. Choose another time.", 422)
    return candidates.pop()


def validate_start(start: datetime, minutes: int, zone: str, now: datetime) -> datetime:
    if start.tzinfo is None:
        raise DomainError("TIMEZONE_REQUIRED", "Choose a time from the local calendar.", 422)
    local = start.astimezone(ZoneInfo(zone))
    canonical = local_to_utc(local.replace(tzinfo=None), zone)
    end = canonical + timedelta(minutes=minutes)
    local_end = end.astimezone(ZoneInfo(zone))
    today = now.astimezone(ZoneInfo(zone)).date()
    if (canonical < now or not today <= local.date() < today + timedelta(days=30) or local.weekday() == 6 or
            local.second or local.microsecond or local.minute % 30 or local.time().replace(tzinfo=None) < time(9) or
            local_end.date() != local.date() or local_end.time().replace(tzinfo=None) > time(18)):
        raise DomainError("TIME_UNAVAILABLE", "Choose a listed time within the next 30 days.", 422)
    return canonical


@dataclass(frozen=True)
class Busy:
    staff_id: str
    start: datetime
    end: datetime


def eligible(start: datetime, minutes: int, busy: list[Busy]) -> list[str]:
    end = start + timedelta(minutes=minutes)
    return [staff for staff in STAFF_IDS if not any(b.staff_id == staff and start < b.end and b.start < end for b in busy)]


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def working_day_after(day: date) -> date:
    day += timedelta(days=1)
    return day + timedelta(days=1) if day.weekday() == 6 else day


def availability(week: date, minutes: int, zone: str, now: datetime, busy: list[Busy]):
    today = now.astimezone(ZoneInfo(zone)).date()
    if week.weekday() != 0 or week < week_start(today) or week > today + timedelta(days=29):
        raise DomainError("WEEK_UNAVAILABLE", "Choose a week within the next 30 days.", 422)
    days = []
    for offset in range(7):
        day = week + timedelta(days=offset)
        slots = []
        candidates = 0
        if day.weekday() != 6 and today <= day < today + timedelta(days=30):
            for half in range(18):
                naive = datetime.combine(day, time(9)) + timedelta(minutes=half * 30)
                try:
                    start = validate_start(local_to_utc(naive, zone), minutes, zone, now)
                except DomainError:
                    continue
                candidates += 1
                staff = eligible(start, minutes, busy)
                if staff:
                    slots.append({"start": start, "end": start + timedelta(minutes=minutes), "staff_ids": staff})
        status = "past" if day < today or (day == today and day.weekday() != 6 and not candidates) else "outside" if day >= today + timedelta(days=30) else "closed" if day.weekday() == 6 else "available" if slots else "busy"
        occupied = [{"start": b.start, "end": b.end, "staff_id": b.staff_id} for b in busy if b.start.astimezone(ZoneInfo(zone)).date() == day]
        days.append({"date": day, "weekday": day.strftime('%a'), "status": status, "slots": slots, "occupied": occupied})
    return {"week_start": week, "timezone": zone, "minutes": minutes, "days": days,
            "can_previous":week > week_start(today), "can_next":week + timedelta(days=7) <= today + timedelta(days=29)}
