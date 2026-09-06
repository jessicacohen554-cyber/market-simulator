"""SCN-WS1b — score one ISO's paired 2026 T0 against the PRECOMMIT's STOP gate.

Reads the two arms' ``full_horizon_summary.json`` + their redirected caches,
rebuilds the per-year annual summary through the SHIPPED
``results.export._summarize_year`` (so every number here is the harness's own,
not a reconstruction), and emits:

  * the headline pair table (CO2, load-weighted price, unserved, clean share);
  * the by-fuel and by-zone CO2 partitions and their deltas;
  * ``import_co2_mt_reported`` beside ``emissions_mt`` — the SCN-WS0 leakage
    duty (FINDING-scn-ws0-2026-09-05.md §5 item 2), per ISO, as a NUMBER,
    including the zeros;
  * the eight STOP-gate rows of PRECOMMIT §3.3, each PASS / FAIL / REPORTED.

The gate is STOP-only: it may kill an arm, it may never promote one, and no row
reads a residual, a benchmark or an actual (rule 29 ``[R-SCREEN]``).

Run:
  PYTHONPATH=src python docs/handoffs/scn-ws1b/score_t0_pair.py \
      --iso NEISO --ref-dir results/scn-ws1-probe/neiso/REF \
      --arm-dir results/scn-ws1-probe/neiso/CARB [--year 2026]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.results import cache  # noqa: E402
from market_sim.results.export import _summarize_year  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from scripts.run_full_horizon import reference_config  # noqa: E402

# PRECOMMIT §3.2: the repo's own fossil CO2 rate span. G4's structural bound is
# that Δprice / Δcarbon cannot exceed the dirtiest marginal unit's rate.
MAX_FOSSIL_RATE = 1.08  # constants.CO2_RATES["coal"]["older"]
DELTA_CARBON = 25.0

# PRECOMMIT §3.2, the per-ISO predicted Δ load-weighted price band ($/MWh).
PREDICTED_PRICE_BAND: dict[str, tuple[float, float]] = {
    "ERCOT": (6.0, 10.0),
    "CAISO": (9.0, 11.0),
    "PJM": (10.0, 18.0),
    "MISO": (12.0, 22.0),
    "NYISO": (9.0, 14.0),
    "NEISO": (9.0, 11.0),
}

# PRECOMMIT §3.4, the per-ISO predicted Δ import_co2_mt_reported (Mt).
PREDICTED_LEAKAGE: dict[str, str] = {
    "ERCOT": "exactly 0.0000 (no import node)",
    "MISO": "exactly 0.0000 (no import tranche built; MODEL-BOUNDARY artifact)",
    "CAISO": "~0, smallest of the seam ISOs (imports also pay CARB border carbon)",
    "PJM": "UP, +0.2 to +1.5 Mt",
    "NYISO": "UP, +0.5 to +2.5 Mt",
    "NEISO": "UP, ~+1.7 to +2.0 Mt (reproduction of WS-0's +1.8548)",
}

ZERO_CARBON_FUELS = {
    "wind", "solar", "hydro", "nuclear", "storage", "biomass", "geothermal",
    "import", "other_renew", "ps_hydro", "battery",
}


def summary_for(arm_dir: Path, iso: str, year: int) -> tuple[dict, dict]:
    """Return (full_horizon_summary, the year's _summarize_year row) for an arm.

    ``run_full_horizon`` redirects ``cache.CACHE_ROOT`` to the arm's out-dir, so
    this points the cache module at that arm before loading and restores it
    after — the two arms live in separate roots by construction.
    """
    fhs = json.loads((arm_dir / "full_horizon_summary.json").read_text())
    key = fhs["cache_key"]
    prev = cache.CACHE_ROOT
    try:
        cache.CACHE_ROOT = arm_dir
        result = cache.load_result(iso, key, year)
        context = cache.load_fleet_context(iso, key, year)
        cfg_path = cache.get_config_path(iso, key, year)
        config = None
        if cfg_path.exists():
            from market_sim.config.scenarios import ScenarioConfig

            config = ScenarioConfig.from_yaml(cfg_path)
        row = _summarize_year(result, context, config)
    finally:
        cache.CACHE_ROOT = prev
    return fhs, row


def delta_table(ref: dict, arm: dict, key: str) -> list[tuple[str, float, float, float]]:
    """Union-keyed (name, ref, arm, delta) rows for a dict-valued metric."""
    a, b = ref.get(key) or {}, arm.get(key) or {}
    names = sorted(set(a) | set(b))
    return [(n, float(a.get(n, 0.0)), float(b.get(n, 0.0)),
             float(b.get(n, 0.0)) - float(a.get(n, 0.0))) for n in names]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--ref-dir", type=Path, required=True)
    ap.add_argument("--arm-dir", type=Path, required=True)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    iso, year = args.iso.upper(), args.year
    ref_fhs, ref = summary_for(args.ref_dir, iso, year)
    arm_fhs, arm = summary_for(args.arm_dir, iso, year)

    rc = reference_config(iso, year, year, False)
    ac = replace(rc, carbon_price_delta=DELTA_CARBON)
    carbon_ref = resolve_carbon_price(rc, year)
    carbon_arm = resolve_carbon_price(ac, year)

    co2_ref, co2_arm = float(ref["emissions_mt"]), float(arm["emissions_mt"])

    # The GATE's price is the LOAD-WEIGHTED price (the trajectory row's
    # lw_price), not _summarize_year's simple-mean avg_price: a carbon adder's
    # pass-through is a load-weighted claim, and the PRECOMMIT's bands were
    # written against the load-weighted numbers WS-0 and WS-1a reported.
    def _lw(fhs: dict) -> float:
        for r in fhs.get("trajectory") or []:
            if int(r.get("year", -1)) == year:
                return float(r["lw_price"])
        raise SystemExit(f"no trajectory row for {year}")

    p_ref, p_arm = _lw(ref_fhs), _lw(arm_fhs)
    imp_ref = float(ref.get("import_co2_mt_reported", 0.0))
    imp_arm = float(arm.get("import_co2_mt_reported", 0.0))
    uns_ref = float(ref.get("unserved_mwh", 0.0))
    uns_arm = float(arm.get("unserved_mwh", 0.0))
    d_price = p_arm - p_ref
    implied_rate = d_price / DELTA_CARBON

    print("=" * 78)
    print(f"{iso} 2026 T0 — REF vs CARB (+${DELTA_CARBON:.0f}/t on the resolved signal)")
    print("=" * 78)
    print(f"{'metric':38s} {'REF':>14s} {'CARB':>14s} {'delta':>12s}")
    rows = [
        ("resolved carbon $/t", carbon_ref, carbon_arm),
        ("emissions_mt (in-ISO, scored)", co2_ref, co2_arm),
        ("import_co2_mt_reported (disclosure)", imp_ref, imp_arm),
        ("load-weighted price $/MWh", p_ref, p_arm),
        ("simple-mean price $/MWh", float(ref.get("avg_price", 0.0)), float(arm.get("avg_price", 0.0))),
        ("peak hourly price $/MWh", float(ref.get("peak_price", 0.0)), float(arm.get("peak_price", 0.0))),
        ("unserved_mwh", uns_ref, uns_arm),
        ("clean_share", float(ref.get("clean_share", 0.0)), float(arm.get("clean_share", 0.0))),
    ]
    for name, a, b in rows:
        print(f"{name:38s} {a:14.4f} {b:14.4f} {b - a:12.4f}")
    print(f"{'CO2 % change':38s} {'':14s} {'':14s} "
          f"{(co2_arm - co2_ref) / co2_ref * 100 if co2_ref else 0.0:11.2f}%")

    print()
    print("-- CO2 by fuel (Mt) " + "-" * 55)
    fuel_rows = delta_table(ref, arm, "emissions_by_fuel_mt")
    for n, a, b, d in fuel_rows:
        if abs(a) > 1e-9 or abs(b) > 1e-9:
            print(f"{n:38s} {a:14.4f} {b:14.4f} {d:12.4f}")
    print(f"{'TOTAL':38s} {sum(r[1] for r in fuel_rows):14.4f} "
          f"{sum(r[2] for r in fuel_rows):14.4f} {sum(r[3] for r in fuel_rows):12.4f}")

    print()
    print("-- CO2 by zone (Mt) " + "-" * 55)
    for n, a, b, d in delta_table(ref, arm, "emissions_by_zone_mt"):
        print(f"{n:38s} {a:14.4f} {b:14.4f} {d:12.4f}")

    print()
    print("-- generation by fuel (TWh) " + "-" * 47)
    gen_rows = delta_table(ref, arm, "generation_twh")
    for n, a, b, d in gen_rows:
        if abs(a) > 1e-6 or abs(b) > 1e-6:
            print(f"{n:38s} {a:14.4f} {b:14.4f} {d:12.4f}")

    # ---------------------------------------------------------------- gate --
    gate: list[tuple[str, str, str]] = []

    def add(tag: str, ok: bool | None, detail: str) -> None:
        gate.append((tag, "PASS" if ok else ("REPORTED" if ok is None else "FAIL"), detail))

    add("G1 premise",
        abs((carbon_arm - carbon_ref) - DELTA_CARBON) < 1e-9,
        f"delta resolved carbon = {carbon_arm - carbon_ref:+.4f} $/t (need +25.0000)")
    add("G2 CO2 does not rise", co2_arm <= co2_ref + 1e-9,
        f"{co2_ref:.4f} -> {co2_arm:.4f} Mt ({(co2_arm - co2_ref) / co2_ref * 100:+.2f} %)")
    add("G3 price does not fall", p_arm >= p_ref - 1e-9,
        f"{p_ref:.3f} -> {p_arm:.3f} $/MWh ({d_price:+.3f})")
    lo, hi = PREDICTED_PRICE_BAND[iso]
    in_bound = 0.0 <= implied_rate <= MAX_FOSSIL_RATE
    in_band = lo <= d_price <= hi
    add("G4 magnitude",
        True if (in_bound and in_band) else (None if in_bound else False),
        f"delta p / delta carbon = {implied_rate:.4f} t/MWh "
        f"(structural bound [0, {MAX_FOSSIL_RATE}]: {'ok' if in_bound else 'BREACHED'}; "
        f"precommit band [{lo}, {hi}] $/MWh: {'in' if in_band else 'MISS'})")
    partition_ok = abs(sum(r[2] for r in fuel_rows) - co2_arm) < 5e-4 and \
        abs(sum(r[1] for r in fuel_rows) - co2_ref) < 5e-4
    nonfossil_decrease = [n for n, a, b, d in fuel_rows
                          if d < -1e-6 and n.lower() in ZERO_CARBON_FUELS]
    add("G5 fossil confinement", partition_ok and not nonfossil_decrease,
        f"by-fuel partition reproduces emissions_mt: {partition_ok}; "
        f"zero-carbon classes booking a CO2 decrease: {nonfossil_decrease or 'none'}")
    imp_fuel_ref = float((ref.get("emissions_by_fuel_mt") or {}).get("import", 0.0))
    imp_fuel_arm = float((arm.get("emissions_by_fuel_mt") or {}).get("import", 0.0))
    add("G6 import books no in-ISO CO2",
        abs(imp_fuel_ref) < 1e-9 and abs(imp_fuel_arm) < 1e-9,
        f"emissions_by_fuel_mt['import'] = {imp_fuel_ref} / {imp_fuel_arm}")

    def n_fail(fhs: dict) -> int:
        """Count FAIL rows in the run's forecast-invariant list (I1..I14)."""
        inv = fhs.get("invariants") or []
        if isinstance(inv, dict):
            inv = inv.get("checks") or inv.get("rows") or []
        return sum(1 for r in inv if isinstance(r, dict)
                   and str(r.get("status", "")).upper() == "FAIL")

    def n_warn(fhs: dict) -> int:
        """Count WARN rows in the run's forecast-invariant list."""
        inv = fhs.get("invariants") or []
        return sum(1 for r in inv if isinstance(r, dict)
                   and str(r.get("status", "")).upper() == "WARN")

    add("G7 no non-target flip", n_fail(arm_fhs) <= n_fail(ref_fhs),
        f"invariant FAIL/WARN REF={n_fail(ref_fhs)}/{n_warn(ref_fhs)} "
        f"ARM={n_fail(arm_fhs)}/{n_warn(arm_fhs)} (of "
        f"{len(ref_fhs.get('invariants') or [])} scored)")
    add("G8 unserved energy", not (uns_ref == 0.0 and uns_arm > 0.0),
        f"unserved_mwh {uns_ref} -> {uns_arm}")

    print()
    print("=" * 78)
    print("STOP GATE (PRECOMMIT §3.3) — structural, STOP-only, fixed before the solve")
    print("=" * 78)
    for tag, verdict, detail in gate:
        print(f"{verdict:9s} {tag:32s} {detail}")
    killed = [t for t, v, _ in gate if v == "FAIL"]
    print()
    print(f"VERDICT: {'ARM KILLED — ' + ', '.join(killed) if killed else 'ARM NOT KILLED'}"
          "  (the gate promotes nothing)")

    print()
    print("-- LEAKAGE (SCN-WS0 duty) " + "-" * 49)
    d_imp = imp_arm - imp_ref
    d_co2 = co2_arm - co2_ref
    frac = (d_imp / abs(d_co2) * 100.0) if abs(d_co2) > 1e-9 else 0.0
    print(f"predicted (PRECOMMIT §3.4): {PREDICTED_LEAKAGE[iso]}")
    print(f"measured  : import_co2_mt_reported {imp_ref:.4f} -> {imp_arm:.4f} "
          f"(delta {d_imp:+.4f} Mt)")
    print(f"headline  : in-ISO CO2 delta {d_co2:+.4f} Mt")
    print(f"displaced : {frac:.1f} % of the headline reduction is offset by the "
          f"reported import line")
    print(f"net       : {d_co2 + d_imp:+.4f} Mt read with the disclosure line beside it")

    payload = {
        "iso": iso, "year": year,
        "cache_key_ref": ref_fhs["cache_key"], "cache_key_arm": arm_fhs["cache_key"],
        "wall_s_ref": ref_fhs.get("total_wall_s"), "wall_s_arm": arm_fhs.get("total_wall_s"),
        "rss_mb_ref": ref_fhs.get("global_peak_rss_mb"),
        "rss_mb_arm": arm_fhs.get("global_peak_rss_mb"),
        "per_year_perf_ref": ref_fhs.get("per_year_perf"),
        "per_year_perf_arm": arm_fhs.get("per_year_perf"),
        "carbon_ref": carbon_ref, "carbon_arm": carbon_arm,
        "emissions_mt": {"ref": co2_ref, "arm": co2_arm, "delta": d_co2},
        "import_co2_mt_reported": {"ref": imp_ref, "arm": imp_arm, "delta": d_imp,
                                   "displaced_pct_of_headline": frac},
        "invariants": {"ref_fail": n_fail(ref_fhs), "ref_warn": n_warn(ref_fhs),
                       "arm_fail": n_fail(arm_fhs), "arm_warn": n_warn(arm_fhs),
                       "n_scored": len(ref_fhs.get("invariants") or [])},
        "lw_price": {"ref": p_ref, "arm": p_arm, "delta": d_price,
                     "implied_marginal_rate_t_per_mwh": implied_rate},
        "unserved_mwh": {"ref": uns_ref, "arm": uns_arm},
        "emissions_by_fuel_mt": {"ref": ref.get("emissions_by_fuel_mt"),
                                 "arm": arm.get("emissions_by_fuel_mt")},
        "emissions_by_zone_mt": {"ref": ref.get("emissions_by_zone_mt"),
                                 "arm": arm.get("emissions_by_zone_mt")},
        "generation_twh": {"ref": ref.get("generation_twh"),
                           "arm": arm.get("generation_twh")},
        "import_co2_basis": arm.get("import_co2_basis"),
        "gate": [{"check": t, "verdict": v, "detail": d} for t, v, d in gate],
        "killed": killed,
    }
    dest = args.out or (Path(__file__).parent / "t0" / f"{iso.lower()}_t0_score.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float))
    print(f"\nwrote {dest}")
    return 1 if killed else 0


if __name__ == "__main__":
    raise SystemExit(main())
