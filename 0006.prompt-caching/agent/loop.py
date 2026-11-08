"""The ticket loop: eight turns per ticket, three tickets, one provider.

Run it and nothing happens on screen. The provider keeps a ledger; the bill is
what tells you what happened.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompt import build_request
from agent.provider import Clock, Provider

ROOT = Path(__file__).resolve().parent.parent

GAP_S = 90            # the agent answers within a minute and a half
PAUSE_AFTER_TURN = 4  # the customer goes quiet after this many turns
PAUSE_S = 600         # ... and comes back ten minutes later
SUMMARY_KEEP = 3      # summarise older turns every few turns to keep the context small

FAKE_REPLY = (
    "Thanks for the details, that is everything I need to look at this properly. "
    "I pulled the order and the carrier's last scan, and here is where things "
    "stand: the parcel was handed to the carrier on the promised day and the last "
    "scan is at the regional hub, which is one step before the delivery depot. "
    "That scan is older than the delivery promise allows, so this is no longer a "
    "normal delay and I am treating it as a trace rather than asking you to wait "
    "longer. I have opened the trace with the carrier and they have two working "
    "days to answer; if the parcel does not turn up in that window we move to a "
    "replacement without you having to ask again. While the trace is open I cannot "
    "send a second parcel, because two parcels on one order block each other in the "
    "warehouse and the second one gets cancelled automatically. What you can do in "
    "the meantime is keep the tracking link, and if the carrier marks the parcel as "
    "delivered at an address that is not yours, tell me the same day and I will "
    "reopen the claim with that note attached. If you would rather not wait at all, "
    "the other option is a refund, which I can start today and which goes back to "
    "the card you paid with, usually within three to five working days depending on "
    "your bank. I would suggest waiting out the trace first, because a replacement "
    "keeps the price you paid and a refund does not: the same shoes are more "
    "expensive this week. Either way, tell me which one you want and I will set it "
    "in motion, and if anything changes on the carrier's side before you answer, I "
    "will write here first so you are not the one chasing it."
)


def load_tickets() -> list[dict]:
    return json.loads((ROOT / "data" / "tickets.json").read_text(encoding="utf-8"))


def compress(history: list[dict]) -> list[dict]:
    """Replace the oldest exchanges with one summary line.

    The context stays small, which is what the code is trying to do: eight turns
    of a helpful reply each is a lot of text to carry around.
    """
    if len(history) <= SUMMARY_KEEP + 1:
        return history
    older = history[:-SUMMARY_KEEP]
    kept = history[-SUMMARY_KEEP:]
    asked = " ".join(message["text"][:60] for message in older if message["role"] == "user")
    return [{"role": "user", "text": f"Earlier in this ticket: {asked}"}] + kept


def run_ticket(ticket: dict, provider: Provider) -> None:
    history: list[dict] = []
    for index, text in enumerate(ticket["turns"]):
        history.append({"role": "user", "text": text})
        provider.request(**build_request(history, provider.clock))
        history.append(
            {"role": "assistant", "text": f"{FAKE_REPLY} Reference {ticket['id']}-{index + 1}."}
        )

        if (index + 1) % SUMMARY_KEEP == 0 and index < len(ticket["turns"]) - 1:
            history = compress(history)

        provider.clock.advance(PAUSE_S if index + 1 == PAUSE_AFTER_TURN else GAP_S)


def run_all(provider: Provider | None = None, tickets: list[dict] | None = None) -> dict:
    provider = provider or Provider()
    tickets = tickets if tickets is not None else load_tickets()

    for ticket in tickets:
        run_ticket(ticket, provider)

    sent = sum(entry["usage"].sent_tokens for entry in provider.log)
    read = sum(entry["usage"].cache_read_tokens for entry in provider.log)
    cost = sum(entry["usage"].cost_usd for entry in provider.log)
    return {
        "turns": len(provider.log),
        "sent_tokens": sent,
        "read_tokens": read,
        "hit_rate": (read / sent) if sent else 0.0,
        "cost_usd": cost,
        "provider": provider,
    }


if __name__ == "__main__":
    result = run_all(Provider(clock=Clock()))
