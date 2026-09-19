"""SPP-49 (ZERO LP): the benchmark-membership census across EVERY registered region.

SPP-48 §4 established that the BENCHMARK drops a mid-window retiree by a defect
the fleet repair does not fix. This probe answers the question that decides what
to do about it: **how far does that defect reach, and in which direction would
each candidate repair move each region's ACTUAL?**

THE MECHANICAL CAUSE, pinned here rather than inferred. The benchmark's ISO
membership is ``run_calibration_full._iso_plant_ids`` ->
``zone_assignment.build_zone_lookup``, whose EIA-860 supplement reads
``zone_assignment._EIA860_PLANT_PATH`` -- a MODULE-LEVEL constant bound AT
IMPORT to the canonical ``EIA_860_DIR``, never to ``paths.active_eia860_dir()``.
The supplement therefore CANNOT follow ``eia860_vintage_tracks_solve_year``, and
no config can redirect it. Measured: SPP's plant set is 830 under every vintage
with Oklaunion (127) absent from all of them, although vintage_2018/2019/2020's
own plant file carries it BA-coded SWPP with valid coordinates.

WHAT THE THREE LEGS REPORT
--------------------------
``census``  -- per ISO, the plants in that ISO's EIA-860 BA footprint in SOME
               committed vintage but ABSENT from ``build_zone_lookup``, and the
               EIA-923 generation they carry per year. The plain size of the
               hole in each region's ACTUAL.

``shapes``  -- the two candidate repairs, differenced:
                 ADDITIVE = lookup UNION year-matched vintage  (never removes)
                 STRICT   = year-matched vintage alone         (can DELETE)
               STRICT is the variant that looks tidier and is REFUSED: it
               deletes real metered generation in 7 of 9 registered regions
               (SOCO 2024 -7,275.9 GWh, PJM 2020 -9,077.7, SPP -828.8..-893.1 in
               every year 2019-2023), which is "rescaling an input so the
               model's output lands on the actuals" (rule 13 [R-MEASURED]) and
               "burying the error back inside an inaccurate input" (rule 14
               [R-ACCURATE]) -- the same refusal SPP-48 made of a HEAD rebuild.
               This leg also checks the double-count hazard a YEAR-AGNOSTIC
               union would carry (a BA-switcher counted in two ISOs at once).

``inert``    -- the stop-the-line enumeration, at ROW grain rather than MWh,
               because a zero-MWh row still changes the frame's bytes. This is
               what establishes that SPP's 2023-2025 KEEPER YEARS are INERT (0
               added rows, frame byte-identical) and that PJM is LIVE IN EVERY
               YEAR -- 8.8 TWh absent from its 2025 ACTUAL, a live keeper year,
               for the SEPARATE reason that PJM is not in
               ``zone_assignment._EIA860_SUPPLEMENT_ISOS`` at all and so has no
               EIA-860 supplement of any kind.

Because more than SPP moves, ``benchmark_membership_vintage_union`` is gated
DEFAULT-OFF and armed per ISO by explicit recipe (rule 25 [R-ISO-SCOPE]).

``build_zone_lookup`` is vintage-INVARIANT (that is the defect), so unlike
``_spp48_benchmark_membership.py`` this probe needs no per-vintage fork: it
reads the vintage plant files directly and calls the lookup once per ISO.

Run: PYTHONPATH=src python3 scripts/probes/_spp49_membership_census.py [leg]
     leg in {census, shapes, inert, all}; default all.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

# Every registered region and the years its registered run(s) carry.
ISO_YEARS: dict[str, list[int]] = {
    "CAISO": [2022, 2023, 2024, 2025],
    "ERCOT": [2021, 2022, 2023, 2024, 2025],
    "MISO": [2020, 2021, 2022, 2023, 2024, 2025],
    "NEISO": [2020, 2021, 2022, 2023, 2024, 2025],
    "NWPP": [2023, 2024, 2025],
    "NYISO": [2022, 2023, 2024, 2025],
    "PJM": [2020, 2021, 2022, 2023, 2024, 2025],
    "SOCO": [2023, 2024, 2025],
    "SPP": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
}
VINTAGES: list = ["canonical", 2018, 2019, 2020, 2021, 2022, 2023, 2024]


def _ba_mask(df: pd.DataFrame, iso: str):
    """The SAME admission predicate ``zone_assignment`` applies, reused."""
    from market_sim.data.zone_assignment import _iso_ba_codes, _nwpp_admitted

    ba = df["Balancing Authority Code"].astype(str).str.strip()
    if iso == "NWPP":
        nerc = df["NERC Region"] if "NERC Region" in df.columns else None
        return _nwpp_admitted(ba, nerc)
    return ba.isin(_iso_ba_codes(iso))


def _plant_file(vintage) -> Path:
    from market_sim.config.paths import EIA_860_DIR

    if vintage == "canonical":
        return EIA_860_DIR / "eia860_plant.parquet"
    return EIA_860_DIR / f"vintage_{int(vintage)}" / "eia860_plant.parquet"


def _ba_set(iso: str, vintage) -> set[int]:
    path = _plant_file(vintage)
    if not path.exists():
        return set()
    df = pd.read_parquet(path)
    codes = pd.to_numeric(df["Plant Code"], errors="coerce")[_ba_mask(df, iso)]
    return {int(c) for c in codes.dropna()}


def _annual_by_plant() -> pd.DataFrame:
    from market_sim.data.eia923 import load_monthly_generation

    gen = load_monthly_generation()[["year", "plant_id", "netgen_annual_mwh"]].copy()
    gen["plant_id"] = pd.to_numeric(gen["plant_id"], errors="coerce")
    return gen.groupby(["year", "plant_id"], as_index=False)["netgen_annual_mwh"].sum()


def leg_census() -> dict:
    """Plants in the ISO's BA footprint (any vintage) but not in the lookup."""
    from market_sim.data.zone_assignment import build_zone_lookup

    per = _annual_by_plant()
    vsets = {
        iso: {v: _ba_set(iso, v) for v in VINTAGES} for iso in ISO_YEARS
    }
    report: dict = {}
    print("=== MISSING: in the ISO's EIA-860 BA footprint, NOT in build_zone_lookup ===")
    print(f"{'ISO':>6} {'lookup':>7} {'union':>6} {'missing':>8}   GWh of EIA-923 generation by year")
    for iso, years in ISO_YEARS.items():
        cur = set(build_zone_lookup(iso))
        union: set[int] = set().union(*vsets[iso].values())
        missing = sorted(union - cur)
        rows = []
        for y in years:
            g = per[(per["year"] == y) & (per["plant_id"].isin(missing))]
            g = g[g["netgen_annual_mwh"] > 0]
            rows.append(
                {
                    "year": y,
                    "n_plants_with_gen": int(len(g)),
                    "gwh": round(float(g["netgen_annual_mwh"].sum()) / 1000.0, 4),
                }
            )
        report[iso] = {
            "n_current_lookup": len(cur),
            "n_vintage_union": len(union),
            "n_missing": len(missing),
            "years": rows,
        }
        ys = "  ".join(f"{r['year']}:{r['gwh']:.1f}" for r in rows)
        print(
            f"{iso:>6} {len(cur):>7} {len(union):>6} {len(missing):>8}   {ys}"
        )
    return report


def leg_shapes() -> dict:
    """ADDITIVE vs STRICT, and the year-agnostic double-count hazard."""
    from market_sim.data.zone_assignment import build_zone_lookup

    per = _annual_by_plant()

    def gwh(year: int, plants) -> float:
        g = per[(per["year"] == year) & (per["plant_id"].isin(list(plants)))]
        return round(float(g[g["netgen_annual_mwh"] > 0]["netgen_annual_mwh"].sum()) / 1000.0, 3)

    def year_vintage(year: int):
        return year if _plant_file(year).exists() else "canonical"

    cur = {iso: set(build_zone_lookup(iso)) for iso in ISO_YEARS}
    out: dict = {}
    print(f"{'ISO':>6} {'year':>5} | {'ADDITIVE +GWh':>14} | {'STRICT -GWh (DELETES)':>22}")
    print("-" * 56)
    additive: dict = {}
    for iso, years in ISO_YEARS.items():
        out[iso] = []
        for y in years:
            v = _ba_set(iso, year_vintage(y))
            a_gwh, d_gwh = gwh(y, v - cur[iso]), gwh(y, cur[iso] - v)
            additive[(iso, y)] = cur[iso] | v
            out[iso].append(
                {"year": y, "add_gwh": a_gwh, "strict_delete_gwh": d_gwh}
            )
            flag = "  <-- DELETES REAL GENERATION" if d_gwh > 0.5 else ""
            print(f"{iso:>6} {y:>5} | {a_gwh:>14.1f} | {d_gwh:>22.1f}{flag}")

    print(
        "\n=== double-count hazard a YEAR-AGNOSTIC union would carry "
        "(a plant added to A that is also in B for the same year) ==="
    )
    clash = []
    for y in sorted({y for ys in ISO_YEARS.values() for y in ys}):
        isos = [i for i in ISO_YEARS if y in ISO_YEARS[i]]
        for i, a in enumerate(isos):
            adds_a = additive[(a, y)] - cur[a]
            for b in isos[i + 1:]:
                for p in adds_a & additive[(b, y)]:
                    g = gwh(y, {p})
                    if g > 0:
                        clash.append({"year": y, "a": a, "b": b, "plant": int(p), "gwh": g})
    for c in sorted(clash, key=lambda c: -c["gwh"])[:15]:
        print(f"  {c['year']} plant {c['plant']:>6} in BOTH {c['a']} and {c['b']}  {c['gwh']:>9.2f} GWh")
    print(f"  TOTAL {len(clash)} clashes, {round(sum(c['gwh'] for c in clash), 1)} GWh")
    return {"per_iso": out, "double_count": clash}


def leg_inert() -> dict:
    """ROW-grain inertness of the ARM, per ISO x year. The stop-the-line check.

    Row grain, not MWh: a zero-MWh row still changes the frame's bytes, so only
    ZERO ADDED ROWS proves a year's benchmark is byte-identical under the arm.
    """
    import importlib.util

    from market_sim.data.eia923 import load_monthly_generation

    argv, sys.argv = sys.argv, ["_spp49"]
    try:
        spec = importlib.util.spec_from_file_location(
            "rcf_spp49", REPO / "scripts" / "run_calibration_full.py"
        )
        rcf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rcf)
    finally:
        sys.argv = argv

    gen = load_monthly_generation()
    pid = pd.to_numeric(gen["plant_id"], errors="coerce")
    out: dict = {}
    print(f"{'ISO':>6} {'year':>5} {'+plants':>8} {'+923 rows':>10} {'+MWh':>16}  verdict")
    print("-" * 68)
    for iso, years in ISO_YEARS.items():
        out[iso] = []
        for y in years:
            added = rcf._iso_plant_ids(iso, y, True) - rcf._iso_plant_ids(iso, y, False)
            g = gen[(gen["year"] == y) & (pid.isin(list(added)))]
            rows, mwh = len(g), float(g["netgen_annual_mwh"].sum())
            verdict = "INERT (frame byte-identical)" if rows == 0 else "LIVE"
            out[iso].append(
                {"year": y, "n_added": len(added), "rows": rows, "mwh": mwh, "verdict": verdict}
            )
            print(f"{iso:>6} {y:>5} {len(added):>8} {rows:>10} {mwh:>16,.0f}  {verdict}")
    return out


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    legs = {"census": leg_census, "shapes": leg_shapes, "inert": leg_inert}
    if which not in legs and which != "all":
        raise SystemExit(f"unknown leg {which!r}; expected one of {sorted(legs)} or 'all'")
    result = {}
    for name, fn in legs.items():
        if which in (name, "all"):
            print(f"\n{'=' * 72}\n{name.upper()}\n{'=' * 72}")
            result[name] = fn()
    out = REPO / "results/calibration/_spp49_membership_census.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
