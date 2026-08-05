"""FFR-5D paired-arm read-out: the four PRE-REGISTERED reads, per arm.

Reads the evolution ledgers of the two FFR-5D arms (shipped / unified) and
emits exactly the reads pre-registered in
``docs/handoffs/ffr-5d-price-object-2026-08-05.md`` §2, per arm:

  (a) the coal cohort's pipeline event sequence
      (decided / re_confirmed / reversed / executed, counts + MW,
      ``decided_year`` read off event rows — never the ledger year);
  (b) the enriched bar decomposition, cap-weighted over each (year, event)
      row group (the FFR-5A ledger fields — USD/yr, reported here in
      $/kW-yr by dividing by MW x 1000);
  (c) the fleet-wide ``entry_capped`` census (count + MW by fuel, per year);
  (d) executed/economic thermal exits by fuel and year (vs the real 1.534 GW
      of 2023-25 ERCOT exits).

Read-only; never solves. Usage:

    uv run python scripts/probes/ffr5d_paired_arm.py \\
        results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-shipped \\
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

PIPELINE_EVENTS = ("decided", "re_confirmed", "reversed", "executed")
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


def _capw(rows: list[dict], field: str) -> float:
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
    """Produce the four pre-registered reads for one arm."""
    cache_dir = _resolve_cache_dir(out_dir)
    ledgers = load_ledgers_for_run(cache_dir)
    if not ledgers:
        raise SystemExit(f"{cache_dir}: load_ledgers_for_run returned {{}} (wrong path?)")
    out: dict = {"cache_dir": str(cache_dir), "years": sorted(ledgers)}

    # (a) + (b): pipeline event sequence with bar decomposition, coal cohort
    # and all-fuel, grouped by (ledger year, event).
    seq: dict = {}
    for year in sorted(ledgers):
        rows = ledgers[year].get("pipeline_events") or []
        for event in PIPELINE_EVENTS:
            ev_rows = [r for r in rows if r.get("event") == event]
            if not ev_rows:
                continue
            for label, grp in (
                ("all", ev_rows),
                ("coal", [r for r in ev_rows if r.get("fuel") == "coal"]),
            ):
                if not grp:
                    continue
                entry = {
                    "n": len(grp),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in grp), 1),
                    "decided_years": sorted(
                        {r.get("decided_year") for r in grp if "decided_year" in r}
                    ),
                    "execute_years": sorted(
                        {r.get("execute_year") for r in grp if "execute_year" in r}
                    ),
                }
                if any(f in r for r in grp for f in DECOMP_FIELDS):
                    entry["bar_usd_per_kw_yr"] = {
                        f.replace("_usd", ""): round(_capw(grp, f), 2)
                        for f in DECOMP_FIELDS
                    }
                    entry["basis"] = {
                        f: round(_capw_basis(grp, f), 3)
                        for f in BASIS_FIELDS
                        if any(f in r for r in grp)
                    }
                    pricing = sorted({r.get("as_pricing") for r in grp if "as_pricing" in r})
                    if pricing:
                        entry["as_pricing"] = pricing
                seq.setdefault(str(year), {}).setdefault(event, {})[label] = entry
    out["pipeline_sequence"] = seq

    # (c) entry_capped census by fuel per year.
    census: dict = {}
    for year in sorted(ledgers):
        rows = [
            r
            for r in (ledgers[year].get("pipeline_events") or [])
            if r.get("event") == "entry_capped"
        ]
        if not rows:
            continue
        by_fuel: dict[str, dict] = defaultdict(lambda: {"n": 0, "mw": 0.0})
        for r in rows:
            f = by_fuel[r.get("fuel", "?")]
            f["n"] += 1
            f["mw"] += float(r.get("mw", 0.0))
        census[str(year)] = {
            "total": {"n": len(rows), "mw": round(sum(float(r.get("mw", 0.0)) for r in rows), 1)},
            "by_fuel": {k: {"n": v["n"], "mw": round(v["mw"], 1)} for k, v in sorted(by_fuel.items())},
        }
    out["entry_capped"] = census

    # (d) executed pipeline exits + economic retirements by fuel/year.
    exits: dict = {}
    for year in sorted(ledgers):
        led = ledgers[year]
        executed = [
            r
            for r in (led.get("pipeline_events") or [])
            if r.get("event") == "executed"
        ]
        econ = [r for r in (led.get("retirements") or []) if r.get("reason") == "economic"]
        if executed or econ:
            exits[str(year)] = {
                "pipeline_executed": {
                    "n": len(executed),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in executed), 1),
                    "by_fuel": _mw_by_fuel(executed),
                },
                "economic_retirements": {
                    "n": len(econ),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in econ), 1),
                    "by_fuel": _mw_by_fuel(econ),
                },
            }
    out["thermal_exits"] = exits
    out["reserve_margins"] = {
        str(y): ledgers[y].get("reserve_margin") for y in sorted(ledgers)
    }
    out["bridged_years"] = [y for y in sorted(ledgers) if ledgers[y].get("bridge")]
    return out


def _mw_by_fuel(rows: list[dict]) -> dict[str, float]:
    acc: dict[str, float] = defaultdict(float)
    for r in rows:
        acc[r.get("fuel", "?")] += float(r.get("mw", 0.0))
    return {k: round(v, 1) for k, v in sorted(acc.items())}


def main(argv: list[str]) -> int:
    """Read both arms and print the paired JSON summary."""
    if len(argv) != 2:
        print(__doc__)
        return 2
    report = {
        "shipped": read_arm(Path(argv[0])),
        "unified": read_arm(Path(argv[1])),
        "actual_exits_note": (
            "real 2023-25 ERCOT thermal exits: 1.534 GW (three units > 300 MW)"
        ),
    }
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
