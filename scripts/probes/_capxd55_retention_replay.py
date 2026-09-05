"""capx D55 retention-key replay probe (committed artifacts only, no solve).

D32 §3.2 (``docs/handoffs/FINDING-capx-d32-floor-retention-2026-09-02.md``)
found that ``_floor_retention_merit`` key 1 was computed per unit as
``(FOM × pmax × 1000) / (pmax × (1 − EFORd))`` instead of the class constant
``FOM × 1000 / (1 − EFORd)``, so IEEE-754 rounding put same-fuel units on
different floats at the 1e-11 level and the CO2 / heat-rate tie-breaks fired
only inside rounding buckets. This probe replays the reliability floor's
retention loop (``_apply_reliability_floor``: sort the eligible set by the
merit key, retain until the accredited shortfall is covered) on a committed
T1-H bundle's ``pipeline_events`` with BOTH key forms and reports:

1. **Validation** — the DEFECTIVE key reproduces the committed decision
   (every ``entry_capped`` unit sorts before every ``decided`` unit), so the
   replay is exact against the run's own record;
2. **Prediction** — the FIXED key's retained prefix / released suffix, i.e.
   the released set the same run would have produced with key 1 as the class
   constant (the D55 pre-declaration's item (b));
3. the cross-fuel totals of both (must be identical — the fix cannot move a
   unit across fuels), and the plant-grain composition of each release.

The shortfall the floor covered is not persisted in the ledger; it is bounded
from the committed decision (``R − firm(last retained) < S ≤ R``, ``R`` the
retained firm sum) and the prediction is reported EXACT only when every
shortfall in that interval yields the same fixed-key prefix.

Usage::

    uv run python scripts/probes/_capxd55_retention_replay.py \\
        results/hindcast/miso-2021-2025-realized-t1h-d31 [--year 2022] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import build_base_fleet, load_or_synthesize_bins  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    _FOM_MULTIPLIER,
    _THERMAL_FOM,
    resolve_internal_supply_accounting_ratio,
    thermal_accreditation_fraction,
)
from market_sim.model.interchange import (  # noqa: E402
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)


def plant_of(unit_id: str) -> str | None:
    """EIA plant code from a tranche (``_p<code>_``) or raw (``<code>_``) id."""
    m = re.search(r"_p(\d+)(?:_|$)", unit_id)
    if m:
        return m.group(1)
    m = re.match(r"(\d+)(?:_|$)", unit_id)
    return m.group(1) if m else None


def load_bundle(bundle: Path) -> tuple[dict, dict[int, dict], dict]:
    """(meta, ledgers by year, solved scenario_config mapping)."""
    meta = json.loads((bundle / "meta.json").read_text())
    cache = Path(meta["bundle"])
    if not cache.exists():
        cache = bundle / meta["iso"] / meta["cache_key"]
    ledgers = {
        int(p.stem.split("_")[1]): json.loads(p.read_text())
        for p in sorted(cache.glob("evolution_*.json"))
    }
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    return meta, ledgers, sc


def solved_config(sc: dict) -> ScenarioConfig:
    """Rebuild the solved ``ScenarioConfig``, dropping dead (removed) fields.

    A field the run recorded but HEAD no longer declares (e.g. D31's
    ``caiso_bidir_intertie``) is dropped; a field HEAD declares but the run
    predates is pinned to the posture the run actually had where it matters
    for the fleet (the fossil-dates channel is forced OFF for a bundle that
    predates the field — its ledgers carry no ``announced_derates``).
    """
    live = {f.name for f in fields(ScenarioConfig)}
    kw = {k: v for k, v in sc.items() if k in live}
    if "fossil_announced_exits_enabled" not in sc:
        kw["fossil_announced_exits_enabled"] = False
    return ScenarioConfig(**kw)


def base_fleet_attrs(config: ScenarioConfig, iso: str, year: int) -> dict[str, dict]:
    """Per-unit physical attributes from the run's base fleet (runner mirror).

    Only the attributes the merit key reads (fuel, EFORd, CO2 rate, heat
    rate); ``pmax`` is taken from the event row itself (the screen-time
    value, post-derate), never from here. Exit channels are deliberately not
    applied — a unit's attributes do not depend on which other units left.
    """
    # The runner's vintage seam (runner.py, before any load): a hindcast
    # initialises from the EIA-860 vintage snapshot, not the canonical one —
    # without this the rebuilt fleet is the 2025ER census (Erickson 1832
    # already gone, plant 2790's coal units missing) and ~13 % of the run's
    # event ids match nothing.
    from market_sim.config.paths import set_eia860_vintage

    set_eia860_vintage(
        config.eia860_vintage_year
        if (config.mode == "backcast" or config.hindcast)
        else None
    )
    iso_config = get_iso_config(iso)
    spec = get_interchange_spec(config, iso)
    import_generators = build_interchange_fleet(spec, 0.0)
    iso_config = apply_interchange_topology(
        iso_config, spec, config, year=year, extend_node=bool(import_generators)
    )
    bins = load_or_synthesize_bins(config, iso, iso_config, [])
    fleet = build_base_fleet(
        bins, iso, iso_config, iso_config.zone_names, config, [], [], year
    )
    return {
        g.unit_id: {
            "fuel": g.fuel_type,
            "eford": float(g.eford),
            "co2": float(g.emission_rate_co2),
            "heat_rate": float(g.heat_rate),
        }
        for g in fleet
    }


def key_defective(config: ScenarioConfig, a: dict, pmax: float, year: int) -> tuple:
    """Key 1 in the pre-D55 quotient form (D32 §3.2)."""
    fom = getattr(config, _THERMAL_FOM[a["fuel"]])
    mult = getattr(config, _FOM_MULTIPLIER.get(a["fuel"], ""), 1.0)
    gfc = fom * mult * pmax * 1000.0
    firm = pmax * thermal_accreditation_fraction(
        a["fuel"], a["eford"], config.iso, config, year
    )
    return (gfc / firm if firm > 0.0 else float("inf"), a["co2"], a["heat_rate"])


def key_fixed(config: ScenarioConfig, a: dict, year: int) -> tuple:
    """Key 1 as the class constant (the D55 repair): $/firm-MW-yr without pmax."""
    fom = getattr(config, _THERMAL_FOM[a["fuel"]])
    mult = getattr(config, _FOM_MULTIPLIER.get(a["fuel"], ""), 1.0)
    frac = thermal_accreditation_fraction(
        a["fuel"], a["eford"], config.iso, config, year
    )
    return (
        fom * mult * 1000.0 / frac if frac > 0.0 else float("inf"),
        a["co2"],
        a["heat_rate"],
    )


def replay(
    config: ScenarioConfig, attrs: dict[str, dict], led: dict, year: int
) -> dict:
    """Replay one screen year's admission floor with both key forms."""
    rows = [
        e for e in led["pipeline_events"] if e["event"] in ("decided", "entry_capped")
    ]
    # The floor's eligible order (worst-first depth, then unit_id) — Python's
    # sort is stable, so full-key ties resolve in this order.
    for e in rows:
        if "depth_usd_per_kw_yr" in e:
            e["_depth"] = float(e["depth_usd_per_kw_yr"])
        else:
            e["_depth"] = (
                (float(e["going_forward_cost_usd"]) - float(e["net_revenue_usd"]))
                / (float(e["mw"]) * 1000.0)
                if float(e["mw"]) > 0.0
                else 0.0
            )
    rows.sort(key=lambda e: (-e["_depth"], e["unit_id"]))
    missing = [e["unit_id"] for e in rows if e["unit_id"] not in attrs]
    rows = [e for e in rows if e["unit_id"] in attrs]
    ratio = resolve_internal_supply_accounting_ratio(config.iso, config)

    def firm(e: dict) -> float:
        a = attrs[e["unit_id"]]
        return (
            float(e["mw"])
            * thermal_accreditation_fraction(
                a["fuel"], a["eford"], config.iso, config, year
            )
            * ratio
        )

    capped = {e["unit_id"] for e in rows if e["event"] == "entry_capped"}
    decided = {e["unit_id"] for e in rows if e["event"] == "decided"}
    by_old = sorted(
        rows,
        key=lambda e: key_defective(config, attrs[e["unit_id"]], float(e["mw"]), year),
    )
    by_new = sorted(rows, key=lambda e: key_fixed(config, attrs[e["unit_id"]], year))

    # Validation: under the defective key every retained unit precedes every
    # released one (the greedy prefix IS the committed capped set).
    old_prefix = [e["unit_id"] for e in by_old[: len(capped)]]
    # Units whose committed status contradicts the replay order: a retained
    # unit sorting into the released tail (or vice versa). The base-fleet
    # attribute the key reads (a tranche's CO2 rate) can differ from the
    # screen-year value the run held, which the ledger does not persist; such
    # a unit is reported and PINNED to its committed status in the prediction.
    contradictions = sorted(set(old_prefix) ^ capped)
    valid = not contradictions
    n_buckets = len(
        {
            key_defective(config, attrs[e["unit_id"]], float(e["mw"]), year)[0]
            for e in rows
            if attrs[e["unit_id"]]["fuel"] == "coal"
        }
    )

    out = {
        "year": year,
        "n_eligible": len(rows),
        "n_missing_attrs": len(missing),
        "missing_attrs": missing,
        "n_capped": len(capped),
        "n_decided": len(decided),
        "released_mw_committed": round(
            sum(float(e["mw"]) for e in rows if e["unit_id"] in decided), 3
        ),
        "defective_key_reproduces_committed_decision": valid,
        "committed_status_contradictions": contradictions,
        "coal_key1_rounding_buckets_defective": n_buckets,
    }
    if not decided:
        out["note"] = (
            "the floor exhausted the eligible set (every failing unit retained); "
            "the retention ORDER is irrelevant and the fixed key releases the "
            "same empty set"
        )
        out["predicted_released_fixed"] = []
        out["prediction_exact"] = True
        return out
    if len(contradictions) > max(2, len(decided) // 4):
        out["note"] = (
            "defective-key replay does not reproduce the committed decision "
            "(too many contradictions); prediction withheld"
        )
        return out
    # Pinned to committed status: a contradicting retained unit stays retained
    # (its firm MW counted up front), a contradicting released unit stays
    # released — both drop out of the fixed-key ordering.
    pinned = {u for u in contradictions if u in capped}
    pinned_released = {u for u in contradictions if u in decided}
    # Shortfall bounds from the committed decision: R = the committed retained
    # firm sum; the last retained unit (in defective-key order) bounds it below.
    committed_retained = [e for e in by_old if e["unit_id"] in capped]
    r_sum = sum(firm(e) for e in committed_retained)
    last = firm(committed_retained[-1])
    lo, hi = r_sum - last, r_sum
    by_new = [e for e in by_new if e["unit_id"] not in pinned | pinned_released]
    pinned_firm = sum(firm(e) for e in rows if e["unit_id"] in pinned)

    def prefix_for(shortfall: float) -> int:
        acc = pinned_firm
        for i, e in enumerate(by_new):
            if acc >= shortfall:
                return i
            acc += firm(e)
        return len(by_new)

    n_lo = prefix_for(lo + 1e-9)
    n_hi = prefix_for(hi)
    exact = n_lo == n_hi

    def rowdict(e: dict) -> dict:
        a = attrs[e["unit_id"]]
        return {
            "unit_id": e["unit_id"],
            "plant": plant_of(e["unit_id"]),
            "fuel": a["fuel"],
            "mw": round(float(e["mw"]), 3),
            "co2": round(a["co2"], 4),
            "heat_rate": round(a["heat_rate"], 3),
        }

    released_new = [rowdict(e) for e in by_new[n_hi:]] + [
        rowdict(e) for e in rows if e["unit_id"] in pinned_released
    ]
    ambiguous = [rowdict(e) for e in by_new[n_lo:n_hi]]
    released_old = [rowdict(e) for e in by_old if e["unit_id"] in decided]
    out["pinned_to_committed_status"] = {
        "retained": sorted(pinned),
        "released": sorted(pinned_released),
    }

    def fuel_tot(rs: list[dict]) -> dict:
        t: dict[str, float] = {}
        for r in rs:
            t[r["fuel"]] = round(t.get(r["fuel"], 0.0) + r["mw"], 3)
        return t

    def plant_tot(rs: list[dict]) -> dict:
        t: dict[str, float] = {}
        for r in rs:
            t[str(r["plant"])] = round(t.get(str(r["plant"]), 0.0) + r["mw"], 3)
        return dict(sorted(t.items(), key=lambda kv: -kv[1]))

    out.update(
        {
            "shortfall_bounds_firm_mw": [round(lo, 3), round(hi, 3)],
            "prediction_exact": exact,
            "committed_released_defective": released_old,
            "committed_released_by_fuel": fuel_tot(released_old),
            "committed_released_by_plant": plant_tot(released_old),
            "predicted_released_fixed": released_new,
            "predicted_released_by_fuel": fuel_tot(released_new),
            "predicted_released_by_plant": plant_tot(released_new),
            "predicted_released_mw_fixed": round(sum(r["mw"] for r in released_new), 3),
            "boundary_ambiguous_units": ambiguous,
            "cross_fuel_identical": fuel_tot(released_old).keys()
            == fuel_tot(released_new).keys(),
            "retained_head_fixed_top10": [rowdict(e) for e in by_new[:10]],
            "released_co2_range_defective": [
                min(r["co2"] for r in released_old),
                max(r["co2"] for r in released_old),
            ],
            "released_co2_range_fixed": [
                min(r["co2"] for r in released_new),
                max(r["co2"] for r in released_new),
            ]
            if released_new
            else None,
        }
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument(
        "--year",
        type=int,
        default=None,
        help="screen year (default: every year with decisions)",
    )
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    meta, ledgers, sc = load_bundle(args.bundle)
    config = solved_config(sc)
    iso = meta["iso"]
    start = min(ledgers)
    attrs = base_fleet_attrs(config, iso, start)
    years = (
        [args.year]
        if args.year
        else [y for y, led in ledgers.items() if led.get("pipeline_events")]
    )
    result = {
        "bundle": str(args.bundle),
        "cache_key": meta["cache_key"],
        "iso": iso,
        "n_fleet_units": len(attrs),
        "accounting_ratio": resolve_internal_supply_accounting_ratio(iso, config),
        "years": {str(y): replay(config, attrs, ledgers[y], y) for y in years},
    }
    for y, r in result["years"].items():
        print(
            f"[{args.bundle.name}] {y}: eligible {r['n_eligible']} (missing attrs {r['n_missing_attrs']}), "
            f"capped {r['n_capped']}, decided {r['n_decided']} / {r['released_mw_committed']} MW; "
            f"defective key reproduces decision: {r['defective_key_reproduces_committed_decision']} "
            f"(contradictions {r['committed_status_contradictions']}); "
            f"coal key-1 buckets (defective): {r['coal_key1_rounding_buckets_defective']}"
        )
        if r.get("predicted_released_fixed") is not None and r["n_decided"]:
            print(
                f"    fixed key releases {len(r['predicted_released_fixed'])} rows / "
                f"{r['predicted_released_mw_fixed']} MW (exact: {r['prediction_exact']}; "
                f"boundary-ambiguous {len(r['boundary_ambiguous_units'])}); by fuel "
                f"{r['predicted_released_by_fuel']} vs committed {r['committed_released_by_fuel']}"
            )
            print(f"    committed release by plant: {r['committed_released_by_plant']}")
            print(
                f"    predicted  release by plant: {r['predicted_released_by_plant']}"
            )
            print(
                f"    released CO2 range: defective {r['released_co2_range_defective']} -> "
                f"fixed {r['released_co2_range_fixed']}"
            )
        elif r.get("note"):
            print(f"    {r['note']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2))
        print(f"[json] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
