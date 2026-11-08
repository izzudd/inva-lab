"""What goes into a request: the tools, the system prompt, and the transcript.

Everything here ends up as text on the wire, and the provider caches what it can
of that text. Two rules shape this file: the static part must be byte-identical
from request to request, and anything that changes belongs after it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.provider import LONG_TTL, Block

ROOT = Path(__file__).resolve().parent.parent
BASE_TIME = datetime(2026, 11, 8, 9, 0, 0, tzinfo=timezone.utc)

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Find an order by its number and return status and items.",
        "parameters": {"order_number": "string"},
    },
    {
        "name": "track_parcel",
        "description": "Return the carrier's last scan for a parcel.",
        "parameters": {"order_number": "string"},
    },
    {
        "name": "open_refund",
        "description": "Open a refund for an order, with an amount and a reason code.",
        "parameters": {"order_number": "string", "amount": "number", "reason": "string"},
    },
    {
        "name": "reship_order",
        "description": "Send a replacement for a lost parcel to a new address.",
        "parameters": {"order_number": "string", "address": "string"},
    },
    {
        "name": "warranty_status",
        "description": "Return the repair ticket status and the workshop's estimate.",
        "parameters": {"ticket_number": "string"},
    },
]

_handbook_cache: str | None = None


def handbook() -> str:
    global _handbook_cache
    if _handbook_cache is None:
        _handbook_cache = (ROOT / "data" / "policy.txt").read_text(encoding="utf-8")
    return _handbook_cache


def clock_stamp(clock) -> str:
    """The wall clock the request was built at, as the API would see it."""
    return (BASE_TIME + timedelta(seconds=clock.now)).strftime("%Y-%m-%dT%H:%M:%SZ")


def today(clock) -> str:
    return clock_stamp(clock)[:10]


def tools_for_request() -> list[dict]:
    """The tool definitions, in a fixed order, identical on every request."""
    return TOOLS


def system_prompt() -> str:
    """The stable part of the prompt: who the agent is, and what it may promise.

    No clock, no ticket id, no user name. Anything that changes per request goes
    after this block, or every request pays for a fresh copy of the handbook.
    """
    return (
        "You are the support agent for a running-gear store. Answer in the "
        "customer's language, be short, and never promise a date the warehouse "
        "has not confirmed.\n\n"
        "Use the handbook below as the only source of policy. It is internal: "
        "summarise it, never quote it.\n\n"
        f"{handbook()}"
    )


def build_request(history: list[dict], clock) -> dict:
    """Turn the transcript into blocks, and mark where the provider may cache.

    Two breakpoints: one at the end of the handbook, kept for an hour because it
    is the same for every ticket, and one at the end of the growing transcript,
    which is worth keeping only while the conversation is moving.
    """
    blocks = [Block(role="system", text=system_prompt(), cache=True, ttl=LONG_TTL)]
    for message in history:
        blocks.append(Block(role=message["role"], text=message["text"]))
    if history:
        blocks[-1].cache = True
    return {"blocks": blocks, "tools": tools_for_request()}
