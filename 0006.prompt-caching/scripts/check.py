#!/usr/bin/env python3
"""check.py — this lab's finish line.

Runs the real loop against the simulated provider and reads the provider's
ledger. Seven checks, one theme: a cache hit is a property of the bytes you
send, not of the feature you switched on.

    python3 scripts/check.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from agent.loop import PAUSE_AFTER_TURN, load_tickets, run_all  # noqa: E402
from agent.provider import MIN_CACHEABLE, Clock, Provider  # noqa: E402

try:  # the solver may move the date around, but the base clock stays put
    from agent.prompt import BASE_TIME
except ImportError:  # pragma: no cover
    BASE_TIME = datetime(2026, 11, 8, 9, 0, 0, tzinfo=timezone.utc)

HIT_RATE_MIN = 0.75
COST_RATIO_MAX = 0.45
SUMMARY = re.compile(r"summary\s+turns=(\d+)\s+hit_rate=([\d.]+)\s+cost_usd=([\d.]+)")


def run(tickets=None, cache: bool = True, start: int = 0):
    provider = Provider(cache_enabled=cache, clock=Clock(start))
    return run_all(provider, tickets), provider


def is_prefix(older: list[str], newer: list[str]) -> bool:
    return len(newer) >= len(older) and newer[: len(older)] == older


def main() -> int:
    tickets = load_tickets()
    main_run, provider = run(tickets)
    baseline_run, _ = run(tickets, cache=False)
    per_ticket = [(ticket, run([ticket])[1]) for ticket in tickets]

    results: list[tuple[str, str, bool, str]] = []

    # A — most of the tokens sent come back as cache reads.
    hit = main_run["hit_rate"]
    results.append((
        "A",
        "cache reads cover at least 75% of the tokens you send",
        hit >= HIT_RATE_MIN,
        f"hit rate {hit * 100:.1f}% of {main_run['sent_tokens']:,} tokens",
    ))

    # B — the bill is at most 45% of the same run without caching.
    ratio = main_run["cost_usd"] / baseline_run["cost_usd"]
    results.append((
        "B",
        "the run costs at most 45% of the same run with caching off",
        ratio <= COST_RATIO_MAX,
        f"${main_run['cost_usd']:.4f} vs ${baseline_run['cost_usd']:.4f} "
        f"({ratio * 100:.0f}%)",
    ))

    # C — the static prefix does not contain the clock, and the date still arrives.
    first, _ = run([tickets[0]], start=0)
    later, later_provider = run([tickets[0]], start=86_400)
    same_prefix = first["provider"].log[0]["texts"][0] == later_provider.log[0]["texts"][0]
    expected = (BASE_TIME + timedelta(seconds=86_400)).strftime("%Y-%m-%d")
    date_reaches = expected in later_provider.log[-1]["texts"][-1]
    results.append((
        "C",
        "the static prefix is identical on two different days, and the date still reaches the model",
        same_prefix and date_reaches,
        f"prefix identical={same_prefix}, {expected} in last block={date_reaches}",
    ))

    # D — every request contains the previous one, unchanged, at the front.
    grows = []
    for ticket, ticket_provider in per_ticket:
        texts = [entry["texts"] for entry in ticket_provider.log]
        grows.append(all(is_prefix(older, newer) for older, newer in zip(texts, texts[1:])))
    results.append((
        "D",
        "each request is the previous one plus new blocks (nothing is rewritten)",
        all(grows),
        "append-only" if all(grows) else f"rewritten in {grows.count(False)} of {len(grows)} tickets",
    ))

    # E — the tool definitions are byte-identical from the first turn to the last.
    tool_keys = {entry["tools_key"] for entry in provider.log}
    results.append((
        "E",
        "the tools array is identical on every request",
        len(tool_keys) == 1,
        f"{len(tool_keys)} distinct tools blocks across {main_run['turns']} requests",
    ))

    # F — the ten-minute pause does not throw the static prefix away.
    survived = [
        ticket_provider.log[PAUSE_AFTER_TURN]["usage"].cache_read_tokens >= MIN_CACHEABLE
        for _, ticket_provider in per_ticket
    ]
    examples = ", ".join(
        f"{ticket['id']}: {ticket_provider.log[PAUSE_AFTER_TURN]['usage'].cache_read_tokens:,}"
        for ticket, ticket_provider in per_ticket
    )
    results.append((
        "F",
        "the turn after the ten-minute pause still reads the static prefix",
        all(survived),
        examples,
    ))

    # G — the loop reports its own numbers, and they are the real ones.
    printed = subprocess.run(
        [sys.executable, str(LAB / "agent" / "loop.py")],
        cwd=str(LAB), capture_output=True, text=True, timeout=180,
    )
    match = SUMMARY.search(printed.stdout)
    honest = False
    detail = "no `summary turns=… hit_rate=… cost_usd=…` line on stdout"
    if match:
        turns, line_hit, line_cost = int(match[1]), float(match[2]), float(match[3])
        fresh, _ = run(tickets)
        honest = (
            turns == fresh["turns"]
            and abs(line_hit - fresh["hit_rate"]) <= 0.01
            and abs(line_cost - fresh["cost_usd"]) <= max(fresh["cost_usd"] * 0.05, 1e-6)
        )
        detail = (
            f"printed turns={turns} hit_rate={line_hit} cost_usd={line_cost}; "
            f"measured {fresh['turns']} / {fresh['hit_rate']:.3f} / {fresh['cost_usd']:.6f}"
        )
    results.append(("G", "the loop prints its measured turns, hit rate and cost", honest, detail))

    print()
    for tag, title, ok, detail in results:
        verdict = "GREEN" if ok else "RED  "
        print(f"  [{verdict}] {tag}. {title}  ({detail})")
    print()

    green = sum(1 for _, _, ok, _ in results if ok)
    total = len(results)
    if green == total:
        print(f"check: {green}/{total} green — done")
        return 0
    print(f"check: {green}/{total} green — not done yet")
    return 1


if __name__ == "__main__":
    sys.exit(main())
