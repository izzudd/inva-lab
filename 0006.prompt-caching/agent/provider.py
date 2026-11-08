"""The provider, simulated.

This file is the measuring instrument, not the exercise. Do not edit it: `make
check` reads its ledger. It implements one provider's documented caching rules
(the Claude API, as published in November 2026):

  * a cache entry is written only at a block you marked as a breakpoint;
  * a read walks backward from the breakpoint, at most 20 block positions, and
    takes the first entry a previous request actually wrote;
  * a prefix shorter than 512 tokens cannot be cached at all;
  * a 5-minute TTL by default and a 1-hour TTL if you ask for it, refreshed for
    free every time the entry is read;
  * a write costs 1.25x the input price, a read costs 0.1x.

Other providers differ, and the companion article says how. One token here is
one whitespace-separated word, which is close enough to a real tokenizer for a
6,000-word document and makes the arithmetic readable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

MIN_CACHEABLE = 512
LOOKBACK_BLOCKS = 20
DEFAULT_TTL = 300
LONG_TTL = 3_600
OUTPUT_TOKENS = 300

INPUT_USD_PER_TOKEN = 2.0 / 1_000_000
OUTPUT_USD_PER_TOKEN = 10.0 / 1_000_000
WRITE_MULTIPLIER = 1.25
READ_MULTIPLIER = 0.10


def count_tokens(text: str) -> int:
    return len(text.split())


@dataclass
class Block:
    role: str
    text: str
    cache: bool = False
    ttl: int = DEFAULT_TTL


@dataclass
class Usage:
    input_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = OUTPUT_TOKENS
    cost_usd: float = 0.0

    @property
    def sent_tokens(self) -> int:
        return self.input_tokens + self.cache_write_tokens + self.cache_read_tokens


class Clock:
    """A clock you can move by hand, so a five-minute timeout runs in no time."""

    def __init__(self, start: int = 0) -> None:
        self.now = start

    def advance(self, seconds: int) -> int:
        self.now += seconds
        return self.now


@dataclass
class Entry:
    tokens: int
    ttl: int
    expires_at: int


@dataclass
class Provider:
    cache_enabled: bool = True
    clock: Clock = field(default_factory=Clock)
    entries: dict[str, Entry] = field(default_factory=dict)
    log: list[dict] = field(default_factory=list)

    # -- keys -------------------------------------------------------------
    @staticmethod
    def _key(tools: list[dict], texts: list[str]) -> str:
        payload = json.dumps({"tools": tools, "prefix": texts}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _prefix_tokens(self, tool_tokens: int, token_list: list[int], upto: int) -> int:
        return tool_tokens + sum(token_list[: upto + 1])

    # -- the request ------------------------------------------------------
    def request(self, blocks: list[Block], tools: list[dict]) -> Usage:
        tool_tokens = count_tokens(json.dumps(tools, sort_keys=True))
        texts = [blk.text for blk in blocks]
        token_list = [count_tokens(blk.text) for blk in blocks]
        total = tool_tokens + sum(token_list)

        breakpoints = [i for i, blk in enumerate(blocks) if blk.cache]
        usage = Usage()
        matched_tokens = 0

        if self.cache_enabled and breakpoints:
            matched_tokens = self._lookup(breakpoints, tools, texts, tool_tokens, token_list)

        billed_write = 0
        if self.cache_enabled and breakpoints:
            for bp in breakpoints:
                covered = self._prefix_tokens(tool_tokens, token_list, bp)
                if covered < MIN_CACHEABLE:
                    continue
                self.entries[self._key(tools, texts[: bp + 1])] = Entry(
                    tokens=covered,
                    ttl=blocks[bp].ttl,
                    expires_at=self.clock.now + blocks[bp].ttl,
                )
            last = self._prefix_tokens(tool_tokens, token_list, breakpoints[-1])
            if last >= MIN_CACHEABLE:
                billed_write = max(last - matched_tokens, 0)

        usage.cache_read_tokens = matched_tokens
        usage.cache_write_tokens = billed_write
        usage.input_tokens = max(total - matched_tokens - billed_write, 0)
        usage.cost_usd = (
            usage.input_tokens * INPUT_USD_PER_TOKEN
            + usage.cache_write_tokens * INPUT_USD_PER_TOKEN * WRITE_MULTIPLIER
            + usage.cache_read_tokens * INPUT_USD_PER_TOKEN * READ_MULTIPLIER
            + usage.output_tokens * OUTPUT_USD_PER_TOKEN
        )

        self.log.append(
            {
                "at": self.clock.now,
                "tools_key": self._key(tools, []),
                "tools_tokens": tool_tokens,
                "total_tokens": total,
                "breakpoints": breakpoints,
                "cacheable_tokens": [
                    self._prefix_tokens(tool_tokens, token_list, i) for i in breakpoints
                ],
                "texts": texts,
                "roles": [blk.role for blk in blocks],
                "usage": usage,
            }
        )
        return usage

    def _lookup(self, breakpoints, tools, texts, tool_tokens, token_list) -> int:
        for bp in reversed(breakpoints):
            highest = bp
            lowest = max(bp - (LOOKBACK_BLOCKS - 1), 0)
            for position in range(highest, lowest - 1, -1):
                entry = self.entries.get(self._key(tools, texts[: position + 1]))
                if entry is None:
                    continue
                if entry.expires_at <= self.clock.now:
                    continue
                # a read refreshes the entry for free, exactly as documented
                entry.expires_at = self.clock.now + entry.ttl
                return entry.tokens
        return 0


def price_without_cache(blocks: list[Block], tools: list[dict]) -> float:
    """What the same request would cost with caching switched off."""
    tool_tokens = count_tokens(json.dumps(tools, sort_keys=True))
    total = tool_tokens + sum(count_tokens(blk.text) for blk in blocks)
    return total * INPUT_USD_PER_TOKEN + OUTPUT_TOKENS * OUTPUT_USD_PER_TOKEN
