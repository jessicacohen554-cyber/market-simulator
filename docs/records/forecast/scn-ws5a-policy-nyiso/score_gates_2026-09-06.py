"""SCN-WS5A-POLICY-NYISO gate scorer — reads the solved legs, emits G1-G13.

Zero LP. Reads each leg's committed slim summary plus its cached year results
(for the clean-region duals, the mass-cap allowance price and the dispatch the
escape volume is measured against), and prints/serializes the gate table the
FINDING §3 reports.

Run:  PYTHONPATH=. uv run python docs/handoffs/scn-ws5a-policy-nyiso/score_gates_2026-09-06.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.results import cache  # noqa: E402

ISO = "NYISO"
YEARS = [2026, 2027, 2028, 2029, 2030]
LEGS = REPO / "results/scn-campaign-policy-2026-09-06/NYISO"
PHASE0 = json.loads(
    (Path(__file__).parent / "phase0-nyiso-2026-09-06.json").read_text()
)
ELIG_VOL = ("wind", "solar", "offshore_wind", "geothermal")
CES_CRED = {
    "nuclear": 1.0,
    "hydro": 1.0,
    "wind": 1.0,
    "solar": 1.0,
    "geothermal": 1.0,
    "offshore_wind": 1.0,
    "gas_cc_ccs": 0.95,
}
CES_TARGET = {2026: 0.55, 2027: 0.577778, 2028: 0.605556, 2029: 0.633333, 2030: 0.661111}
ACP = 50.0
# region order per runner._clean_region_arrays_for_year: state (MISO only) ->
# FEDERAL_CES -> VOLUNTARY, appended last.
REGION_ORDER = {
    "CES-T80": ["FEDERAL_CES"],
    "VOL-MID": ["VOLUNTARY"],
    "VOL-HI": ["VOLUNTARY"],
    "CES-P20+VOL-HI": ["VOLUNTARY"],
    "ALL-CLEAN": ["FEDERAL_CES", "VOLUNTARY"],
}
VOL_CEILING = {"VOL-MID": 4.5, "VOL-HI": 7.0, "CES-P20+VOL-HI": 7.0, "ALL-CLEAN": 7.0}
VOL_PATH = {"VOL-MID": "mid", "VOL-HI": "high", "CES-P20+VOL-HI": "high", "ALL-CLEAN": "high"}


def leg_summary(case: str) -> dict | None:
    p = LEGS / case / "full_horizon_summary.json"
    return json.loads(p.read_text()) if p.exists() else None


def year_meta(key: str, year: int) -> dict:
    """clean_region_duals / co2_cap_price / rps dual from the cached year."""
    res = cache.load_result(ISO, key, year)
    return {
        "clean_region_duals": (
            None
            if getattr(res, "clean_region_duals", None) is None
            else [float(x) for x in res.clean_region_duals]
        ),
        "co2_cap_price": (
            None
            if getattr(res, "co2_cap_price", None) is None
            else [float(x) for x in res.co2_cap_price]
        ),
    }


def main() -> int:
    out: dict = {"iso": ISO, "years": YEARS, "cases": {}}
    for case_dir in sorted(p.name for p in LEGS.iterdir() if p.is_dir()):
        s = leg_summary(case_dir)
        if s is None or s.get("error"):
            out["cases"][case_dir] = {"error": (s or {}).get("error", "no summary")}
            continue
        key = s["cache_key"]
        row: dict = {
            "cache_key": key,
            "wall_s": s.get("total_wall_s"),
            "peak_rss_mb": s.get("global_peak_rss_mb"),
            "per_year_perf": s.get("per_year_perf"),
            "invariants": {
                (i.get("ident") or i.get("id") or i.get("name")): i.get("status")
                for i in s.get("invariants", [])
            },
            "per_year": {},
        }
        for r in s["trajectory"]:
            y = r["year"]
            g = r["generation_by_fuel_mwh"]
            elig = sum(g.get(f, 0.0) for f in ELIG_VOL)
            cred = sum(g.get(f, 0.0) * c for f, c in CES_CRED.items())
            demand_twh = PHASE0["cases"].get(
                case_dir, PHASE0["cases"]["REF"]
            )["per_year"][str(y)]["voluntary"]["mid"]["energy_total_twh"]
            vpath = VOL_PATH.get(case_dir)
            V = (
                PHASE0["cases"][case_dir]["per_year"][str(y)]["voluntary"][vpath][
                    "volume_twh"
                ]
                * 1e6
                if vpath and case_dir in PHASE0["cases"]
                else None
            )
            entry = {
                "co2_mt": r["co2_mt"],
                "lw_price": r["lw_price"],
                "total_gen_twh": r["total_gen_mwh"] / 1e6,
                "eligible_twh": elig / 1e6,
                "credited_twh": cred / 1e6,
                "demand_twh": demand_twh,
                "credited_share": cred / (demand_twh * 1e6),
                "ces_target": CES_TARGET[y],
                "ces_shortfall_twh": (CES_TARGET[y] * demand_twh * 1e6 - cred) / 1e6,
                "gas_cc_ccs_twh": g.get("gas_cc_ccs", 0.0) / 1e6,
                "gas_cc_ccs_mw": r["capacity_by_fuel_mw"].get("gas_cc_ccs", 0.0),
                "wind_mw": r["capacity_by_fuel_mw"].get("wind", 0.0),
                "solar_mw": r["capacity_by_fuel_mw"].get("solar", 0.0),
                "builds_renew_mw": r["builds_renew_mw"],
                "builds_thermal_mw": r["builds_thermal_mw"],
                "builds_thermal_backstop_mw": r.get("builds_thermal_backstop_mw", 0.0),
                "builds_storage_mw": r["builds_storage_mw"],
                "retire_mw": r["retire_mw"],
                "neg_price_hour_frac": r["neg_price_hour_frac"],
                "rps_dual": r.get("rps_dual"),
                "reserve_margin": r["reserve_margin"],
                "V_mwh": V,
                "voluntary_escape_twh": (
                    None if V is None else max(0.0, V - elig) / 1e6
                ),
            }
            try:
                entry.update(year_meta(key, y))
            except Exception as exc:  # noqa: BLE001
                entry["dual_read_error"] = repr(exc)
            labels = REGION_ORDER.get(case_dir)
            duals = entry.get("clean_region_duals")
            if labels and duals and len(duals) == len(labels):
                entry["duals_by_label"] = dict(zip(labels, duals))
            entry["vol_ceiling"] = VOL_CEILING.get(case_dir)
            row["per_year"][str(y)] = entry
        out["cases"][case_dir] = row

    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(REPO)}")

    # A compact console table for the FINDING.
    for case, row in out["cases"].items():
        if "error" in row:
            print(f"{case}: ERROR {row['error']}")
            continue
        print(f"\n=== {case}  key={row['cache_key']}  "
              f"wall={row['wall_s']:.0f}s rss={row['peak_rss_mb']:.0f}MB")
        fails = [k for k, v in row["invariants"].items() if v == "FAIL"]
        print(f"    invariants: {len(row['invariants'])} scored, FAIL={fails or 'none'}")
        hdr = (f"    {'yr':<5}{'co2Mt':>9}{'lw$':>8}{'elig':>8}{'ccsTWh':>8}"
               f"{'credSh':>8}{'shortTWh':>9}{'duals':>26}{'capP':>10}{'escTWh':>8}")
        print(hdr)
        for y in YEARS:
            e = row["per_year"].get(str(y))
            if not e:
                continue
            d = e.get("duals_by_label") or e.get("clean_region_duals")
            cp = e.get("co2_cap_price")
            print(f"    {y:<5}{e['co2_mt']:>9.4f}{e['lw_price']:>8.2f}"
                  f"{e['eligible_twh']:>8.3f}{e['gas_cc_ccs_twh']:>8.3f}"
                  f"{e['credited_share']:>8.4f}{e['ces_shortfall_twh']:>9.3f}"
                  f"{str(d):>26}{str(cp):>10}"
                  f"{(e['voluntary_escape_twh'] if e['voluntary_escape_twh'] is not None else float('nan')):>8.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
