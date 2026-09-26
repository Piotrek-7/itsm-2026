# ai-generated: 100% - Codex implemented the API from the receipted specification.
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr
from starlette.exceptions import HTTPException
from .clock import UTC, deadlines, evaluate, parse_instant, stamp

DB = os.environ.get("SVCDESK_DB", "/data/svcdesk.db")
Path(DB).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def database():
    conn = sqlite3.connect(DB, timeout=20)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


with database() as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, body TEXT NOT NULL)")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class Reporter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: StrictStr = Field(min_length=1, max_length=100)
    email: StrictStr | None = None
    vip: StrictBool = False


class CreateTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: StrictStr = Field(min_length=1, max_length=200)
    description: StrictStr = Field(default="", max_length=4000)
    reporter: Reporter
    impact: StrictInt = Field(ge=1, le=3)
    urgency: StrictInt = Field(ge=1, le=3)
    related_to: StrictStr | None = None


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(status_code=422, content={"error": {"code": "validation", "message": "Invalid request", "details": [
        {"location": list(e["loc"]), "message": e["msg"]} for e in exc.errors()]}})


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


def fail(status, code, message):
    raise HTTPException(status, {"code": code, "message": message})


def request_clock(request: Request):
    header = request.headers.get("X-Test-Clock")
    if os.environ.get("SVCDESK_TEST_CLOCK", "").lower() in ("1", "true") and header is not None:
        try:
            return parse_instant(header)
        except (ValueError, OverflowError):
            fail(422, "invalid_clock", "X-Test-Clock must be an RFC 3339 instant with timezone")
    return datetime.now(UTC)


def find_ticket(conn, ticket_id):
    row = conn.execute("SELECT body FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        fail(404, "not_found", "Ticket not found")
    return json.loads(row[0])


@app.get("/health")
def health():
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
def create_ticket(body: CreateTicket, now=Depends(request_clock)):
    priority = (("P1", "P2", "P3"), ("P2", "P3", "P4"), ("P3", "P4", "P4"))[body.impact-1][body.urgency-1]
    ticket = {**body.model_dump(), "id": str(uuid4()), "state": "new", "priority": priority,
              "created_at": stamp(now), "acknowledged_at": None, "resolved_at": None, "closed_at": None,
              "sla": deadlines(now, priority)}
    with database() as conn:
        conn.execute("INSERT INTO tickets (id, body) VALUES (?, ?)", (ticket["id"], json.dumps(ticket)))
    return ticket


@app.get("/tickets")
def list_tickets(state: str | None = None, priority: str | None = None):
    with database() as conn:
        tickets = [json.loads(row[0]) for row in conn.execute("SELECT body FROM tickets")]
    return [t for t in tickets if (state is None or t["state"] == state) and (priority is None or t["priority"] == priority)]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    with database() as conn:
        return find_ticket(conn, ticket_id)


@app.get("/tickets/{ticket_id}/sla")
def get_sla(ticket_id: str, now=Depends(request_clock)):
    with database() as conn:
        return evaluate(find_ticket(conn, ticket_id), now)


TRANSITIONS = {"ack": ("new", "acknowledged", "acknowledged_at"),
               "start": ("acknowledged", "in_progress", None),
               "resolve": ("in_progress", "resolved", "resolved_at"),
               "close": ("resolved", "closed", "closed_at")}


@app.post("/tickets/{ticket_id}/{action}")
def transition(ticket_id: str, action: str, now=Depends(request_clock)):
    if action not in TRANSITIONS and action != "reopen":
        fail(404, "not_found", "Unknown action")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        ticket = find_ticket(conn, ticket_id)
        if action == "reopen":
            if ticket["state"] != "resolved":
                fail(409, "invalid_transition", "Only resolved tickets can reopen; closed tickets are immutable")
            if now > parse_instant(ticket["resolved_at"]) + timedelta(days=7):
                fail(409, "reopen_window_expired", "The seven-day reopen window has elapsed")
            ticket.update(state="in_progress", resolved_at=None, closed_at=None)
        else:
            source, target, event = TRANSITIONS[action]
            if ticket["state"] != source:
                fail(409, "invalid_transition", "Action is not allowed from the current state")
            ticket["state"] = target
            if event:
                ticket[event] = stamp(now)
        conn.execute("UPDATE tickets SET body = ? WHERE id = ?", (json.dumps(ticket), ticket_id))
    return ticket
