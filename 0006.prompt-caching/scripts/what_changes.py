#!/usr/bin/env python3
"""inspect.py — compare two consecutive requests, byte by byte.

    python3 scripts/inspect.py            # first ticket, turns 1 and 2
    python3 scripts/inspect.py T-1043 3   # a ticket and a turn number

Prints what the provider would hash: the tools, and each block. A request that
does not start with the previous request is a request that cannot hit.
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from agent.loop import load_tickets, run_all  # noqa: E402
from agent.provider import Clock, Provider  # noqa: E402


def show(entry: dict, previous: dict | None, index: int) -> None:
    print(f"\nrequest {index}: {entry['total_tokens']:,} tokens, "
          f"breakpoints at {entry['breakpoints']}, "
          f"tools key {entry['tools_key'][:8]}")
    if previous is not None:
        same_tools = "same" if entry["tools_key"] == previous["tools_key"] else "DIFFERENT"
        print(f"  tools: {same_tools} as the request before "
              f"({previous['tools_key'][:8]})")
    for position, (role, text) in enumerate(zip(entry["roles"], entry["texts"])):
        same = ""
        if previous is not None and position < len(previous["texts"]):
            same = " same" if previous["texts"][position] == text else " CHANGED"
        mark = "^" if position in entry["breakpoints"] else " "
        print(f"  {mark}[{position:>2}] {role:<9} {len(text.split()):>6,} words{same}")


def main(argv: list[str]) -> int:
    argv = [argument for argument in argv if argument]
    tickets = load_tickets()
    wanted = argv[1] if len(argv) > 1 else tickets[0]["id"]
    turns = [t for t in tickets if t["id"] == wanted]
    if not turns:
        print(f"no ticket {wanted}")
        return 2
    upto = int(argv[2]) if len(argv) > 2 else 2

    provider = Provider(clock=Clock())
    run_all(provider, turns)
    for index, entry in enumerate(provider.log[:upto]):
        show(entry, provider.log[index - 1] if index else None, index + 1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
