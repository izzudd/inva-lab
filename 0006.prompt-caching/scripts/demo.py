#!/usr/bin/env python3
"""demo.py — what the bill looks like right now.

    python3 scripts/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from agent.loop import load_tickets, run_all  # noqa: E402
from agent.provider import Clock, Provider  # noqa: E402


def line(label: str, result: dict) -> str:
    return (
        f"  {label:<22} turns={result['turns']:<3} "
        f"sent={result['sent_tokens']:>7,}  "
        f"read={result['read_tokens']:>7,}  "
        f"hit={result['hit_rate'] * 100:5.1f}%  "
        f"${result['cost_usd']:.4f}"
    )


def main() -> int:
    tickets = load_tickets()

    print("\nOne ticket at a time, caching on as it ships today:\n")
    for ticket in tickets:
        result = run_all(Provider(clock=Clock()), [ticket])
        print(line(ticket["id"], result))

    full = run_all(Provider(clock=Clock()), tickets)
    baseline = run_all(Provider(cache_enabled=False, clock=Clock()), tickets)
    print()
    print(line("all three tickets", full))
    print(line("same run, cache off", baseline))
    print(
        f"\n  cache reads cover {full['hit_rate'] * 100:.1f}% of the tokens sent, "
        f"and the bill is {full['cost_usd'] / baseline['cost_usd']:.2f}x the no-cache bill."
    )

    provider = full["provider"]
    last = provider.log[-1]
    print("\nThe last request, block by block (^ = cache breakpoint):\n")
    for index, (role, text) in enumerate(zip(last["roles"], last["texts"])):
        mark = "^" if index in last["breakpoints"] else " "
        print(f"  {mark} [{index:>2}] {role:<9} {len(text.split()):>6,} words")
    print(
        f"\n  cacheable tokens at the last breakpoint: "
        f"{last['cacheable_tokens'][-1] if last['cacheable_tokens'] else 0:,}"
        f" of {last['total_tokens']:,} sent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
