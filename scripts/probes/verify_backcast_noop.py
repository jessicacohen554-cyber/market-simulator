"""One-shot check: the confirmed-exit channel is a hard no-op in backcast mode.

Verification harness for the 2026-07-05 ``confirmed_exits_enabled`` default
flip (docs/handoffs/confirmed-retirement-plan-2026-07.md §7). Runs a short
ERCOT backcast twice -- once with the flag off, once on (the new default) --
with ``market_sim.runner.load_confirmed_exits`` patched to record whether it
is ever invoked, and compares the two runs' per-year evolution ledgers.
Diagnostic only; not registered anywhere.

Usage:
    python -m scripts.probes.verify_backcast_noop --year 2023 \\
        --scratch /tmp/confirmed_exits_backcast_check
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import market_sim.runner as runner
from market_sim.config.scenarios import ScenarioConfig
from market_sim.results import cache as cache_mod
from market_sim.results.evolution_ledger import load_ledgers_for_run

logging.basicConfig(level=logging.WARNING)


def _run(iso: str, year: int, enabled: bool, out_dir: Path) -> dict:
    cache_mod.CACHE_ROOT = out_dir
    calls: list = []
    orig = runner.load_confirmed_exits

    def _spy(*a, **kw):
        calls.append((a, kw))
        return orig(*a, **kw)

    runner.load_confirmed_exits = _spy
    try:
        config = ScenarioConfig(
            iso=iso,
            mode="backcast",
            start_year=year,
            end_year=year,
            confirmed_exits_enabled=enabled,
        )
        runner.run_scenario_iso(config, iso)
    finally:
        runner.load_confirmed_exits = orig
    run_dir = out_dir / iso / config.cache_key()
    return {
        "load_confirmed_exits_calls": len(calls),
        "ledgers": load_ledgers_for_run(run_dir),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--scratch", default="/tmp/confirmed_exits_backcast_check")
    ap.add_argument("--out", default="/tmp/confirmed_exits_backcast_check/result.json")
    args = ap.parse_args()

    scratch = Path(args.scratch)
    off = _run(args.iso, args.year, False, scratch / "off")
    on = _run(args.iso, args.year, True, scratch / "on")

    result = {
        "iso": args.iso,
        "year": args.year,
        "off_calls": off["load_confirmed_exits_calls"],
        "on_calls": on["load_confirmed_exits_calls"],
        "ledgers_byte_identical": off["ledgers"] == on["ledgers"],
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
