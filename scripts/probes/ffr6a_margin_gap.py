"""FFR-6A margin-gap read-out: per-fuel bar decomposition at every screen.

Reads the evolution ledgers of one hindcast arm (the FFR-5D unified arm,
re-solved by FFR-6A because the per-unit ``entry_capped`` decompositions were
never committed) and emits the read pre-registered in
``docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md`` §2 R1:

  Per (ledger year, fuel), cap-weighted over ALL ``pipeline_events`` rows of
  that fuel (``entry_capped`` + ``decided`` + ``re_confirmed`` + ``reversed``
  + ``executed`` — one screen row per screened unit), the FFR-5A bar
  decomposition ($/kW-yr) and screen-basis descriptors, plus the event
  census.  This is the repaired-level per-fuel margin table the FFR-6A gap
  decomposition compares against the Potomac-SOM benchmark.

Read-only; never solves. Usage:

    uv run python scripts/probes/ffr6a_margin_gap.py \\
        results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-unified
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

DECOMP_FIELDS = (
    "net_revenue_usd",
    "going_forward_cost_usd",
    "energy_margin_usd",
    "reserve_uplift_usd",
    "attribute_revenue_usd",
    "capacity_revenue_usd",
    "as_annual_credit_usd",
)
BASIS_FIELDS = (
    "screen_price_mean_usd_mwh",
    "screen_price_max_usd_mwh",
    "reserve_signal_mean_usd_mwh",
    "availability_mean",
    "mc_mean_usd_mwh",
)


def _resolve_cache_dir(out_dir: Path) -> Path:
    """Return ``<out-dir>/ERCOT/<key>`` (exactly one key dir expected)."""
    iso_dir = out_dir / "ERCOT"
    keys = sorted(d for d in iso_dir.iterdir() if d.is_dir())
    if len(keys) != 1:
        raise SystemExit(f"{iso_dir}: expected exactly one cache-key dir, found {keys}")
    return keys[0]


def _capw_usd(rows: list[dict], field: str) -> float:
    """Capacity-weighted $/kW-yr of a USD/yr row field (0 when absent)."""
    mw = sum(float(r.get("mw", 0.0)) for r in rows)
    if mw <= 0.0:
        return 0.0
    return sum(float(r.get(field, 0.0)) for r in rows) / (mw * 1000.0)


def _capw_basis(rows: list[dict], field: str) -> float:
    """Capacity-weighted mean of a basis descriptor field."""
    mw = sum(float(r.get("mw", 0.0)) for r in rows)
    if mw <= 0.0:
        return 0.0
    return sum(float(r.get(field, 0.0)) * float(r.get("mw", 0.0)) for r in rows) / mw


def read_arm(out_dir: Path) -> dict:
    """Per-(ledger-year, fuel) cap-weighted decomposition over screen rows."""
    cache_dir = _resolve_cache_dir(out_dir)
    ledgers = load_ledgers_for_run(cache_dir)
    if not ledgers:
        raise SystemExit(f"{cache_dir}: no evolution ledgers found (wrong path?)")
    result: dict = {"cache_dir": str(cache_dir), "years": {}}
    for year in sorted(ledgers):
        events = ledgers[year].get("pipeline_events", []) or []
        if not events:
            continue
        by_fuel: dict[str, list[dict]] = defaultdict(list)
        for row in events:
            by_fuel[str(row.get("fuel", "?"))].append(row)
        ytab: dict = {}
        for fuel in sorted(by_fuel):
            rows = by_fuel[fuel]
            entry = {
                "n": len(rows),
                "mw": round(sum(float(r.get("mw", 0.0)) for r in rows), 1),
                "events": dict(
                    sorted(
                        defaultdict(
                            int,
                            {
                                e: sum(1 for r in rows if r.get("event") == e)
                                for e in {r.get("event") for r in rows}
                            },
                        ).items()
                    )
                ),
                "bar_usd_per_kw_yr": {
                    f.removesuffix("_usd"): round(_capw_usd(rows, f), 2)
                    for f in DECOMP_FIELDS
                },
                "basis": {
                    f: round(_capw_basis(rows, f), 3) for f in BASIS_FIELDS
                },
            }
            ytab[fuel] = entry
        result["years"][year] = ytab
    return result


def main() -> int:
    """CLI: read one arm's ledgers, print the per-fuel table as JSON."""
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    print(json.dumps(read_arm(Path(sys.argv[1])), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
