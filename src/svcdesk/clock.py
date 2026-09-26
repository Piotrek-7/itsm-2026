# ai-generated: 100% - Codex implemented the receipted SLA specification.
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
WARSAW = ZoneInfo("Europe/Warsaw")
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")
TARGETS = {"P1": (15, 240), "P2": (60, 480), "P3": (240, 1440), "P4": (480, 4320)}


def parse_instant(value):
    if not RFC3339.fullmatch(value):
        raise ValueError("Expected RFC 3339 with explicit timezone")
    return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).astimezone(UTC)


def stamp(value):
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def business_open(value):
    local = value.astimezone(WARSAW)
    return local.weekday() < 5 and 8 <= local.hour < 16


def business_due(created, minutes):
    local = created.astimezone(WARSAW)
    remaining = timedelta(minutes=minutes)
    while True:
        opening = local.replace(hour=8, minute=0, second=0, microsecond=0)
        closing = local.replace(hour=16, minute=0, second=0, microsecond=0)
        if local.weekday() >= 5 or local >= closing:
            local = opening + timedelta(days=1)
            continue
        local = max(local, opening)
        available = closing - local
        if remaining <= available:
            return (local + remaining).astimezone(UTC)
        remaining -= available
        local = opening + timedelta(days=1)


def deadlines(created, priority):
    ack, resolve = TARGETS[priority]
    def due(minutes):
        return created + timedelta(minutes=minutes) if priority == "P1" else business_due(created, minutes)
    return {"ack_due_at": stamp(due(ack)), "resolve_due_at": stamp(due(resolve))}


def evaluate(ticket, now):
    result = {"priority": ticket["priority"], **ticket["sla"]}
    for prefix, event in [("ack", "acknowledged_at"), ("resolve", "resolved_at")]:
        observed = parse_instant(ticket[event]) if ticket[event] else now
        result[prefix + "_breached"] = observed > parse_instant(ticket["sla"][prefix + "_due_at"])
    result["paused"] = (ticket["state"] not in ("resolved", "closed")
                        and ticket["priority"] != "P1" and not business_open(now))
    return result
