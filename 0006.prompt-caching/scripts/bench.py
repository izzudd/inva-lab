#!/usr/bin/env python3
"""bench.py — the same loop, turn by turn, with and without caching.

    python3 scripts/bench.py            # first ticket
    python3 scripts/bench.py T-1043     # a specific one
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from agent.loop import load_tickets, run_all  # noqa: E402
from agent.provider import Clock, Provider  # noqa: E402


def main(argv: list[str]) -> int:
    wanted = argv[1] if len(argv) > 1 else None
    tickets = load_tickets()
    if wanted:
        tickets = [ticket for ticket in tickets if ticket["id"] == wanted]
        if not tickets:
            print(f"no ticket {wanted}")
            return 2

    for ticket in tickets:
        provider = Provider(clock=Clock())
        result = run_all(provider, [ticket])
        print(f"\n{ticket['id']} — {ticket['subject']}\n")
        print("  turn   at(s)     sent     read    write    input      $")
        for index, entry in enumerate(provider.log, start=1):
            usage = entry["usage"]
            print(
                f"  {index:>4} {entry['at']:>7,} "
                f"{usage.sent_tokens:>8,} {usage.cache_read_tokens:>8,} "
                f"{usage.cache_write_tokens:>8,} {usage.input_tokens:>8,} "
                f"{usage.cost_usd:>7.5f}"
            )
        print(
            f"\n  {result['turns']} turns, hit rate {result['hit_rate'] * 100:.1f}%, "
            f"${result['cost_usd']:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
