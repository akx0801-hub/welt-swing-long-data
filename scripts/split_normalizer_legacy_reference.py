#!/usr/bin/env python3
"""
Welt-Swing Long DEV v0.1 — provider-neutral split-only OHLC normalizer scaffold.

The provider adapter must map provider-specific split semantics into the canonical factor:
    factor = new_shares / old_shares
Example: 2-for-1 => 2.0; 1-for-5 reverse split => 0.2.

For an event on date D, bars strictly before D are adjusted onto the post-split scale:
    price /= cumulative_future_factor
    volume *= cumulative_future_factor
No dividend adjustment is performed.

DEV/SHADOW only until empirically validated against credentialed provider data and known
corporate-action control cases.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Iterable
import math

@dataclass(frozen=True)
class SplitBar:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass(frozen=True)
class SplitEvent:
    day: date
    factor_new_per_old: float

class SplitNormalizationError(ValueError):
    pass


def normalize_split_only(bars: Iterable[SplitBar], events: Iterable[SplitEvent]) -> list[SplitBar]:
    bs = sorted(list(bars), key=lambda x: x.day)
    evs = sorted(list(events), key=lambda x: x.day)
    if len({b.day for b in bs}) != len(bs):
        raise SplitNormalizationError("Duplicate bar date")
    for e in evs:
        if not math.isfinite(e.factor_new_per_old) or e.factor_new_per_old <= 0:
            raise SplitNormalizationError("Split factor must be positive finite new_shares/old_shares")
    out=[]
    for b in bs:
        cum=1.0
        for e in evs:
            if e.day > b.day:
                cum *= e.factor_new_per_old
        vals=[b.open,b.high,b.low,b.close]
        if any(not math.isfinite(x) or x <= 0 for x in vals):
            raise SplitNormalizationError("Nonpositive/nonfinite OHLC")
        if not math.isfinite(b.volume) or b.volume < 0:
            raise SplitNormalizationError("Invalid volume")
        out.append(SplitBar(
            day=b.day,
            open=b.open/cum,
            high=b.high/cum,
            low=b.low/cum,
            close=b.close/cum,
            volume=b.volume*cum,
        ))
    return out
