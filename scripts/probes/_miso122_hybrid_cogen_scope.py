"""miso-122 Phase-0 probe — the hybrid-cogen scope gate, measured before it is built.

NO LP IS SOLVED. Every number is read from committed artifacts:

* ``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` — CAMPD hourly unit
  ``heatInput`` / ``grossLoad`` / ``unitType``, the ONLY source that resolves a
  cogen's fuel to the unit that burned it (eGRID's allocation is plant-level and
  cannot see a hybrid),
* ``data/raw/_processed-legacy/chp_power_only_heat_rates_<ISO>.csv`` — the five
  committed artifacts the derive writes,
* the keeper bundle ``results/calibration/miso117_ctheatrate_B`` — its
  ``run_config.json`` supplies the exact ``ScenarioConfig`` the model side is
  built from (the miso-115/116 measurement trap: a probe that lets
  ``load_fleet_from_csv`` default the heat-rate flags reads a different model
  than the keeper solved).

The pre-registered question, the correction, the six kills and the decision rule
are in ``results/calibration/PREREG-miso122-hybrid-cogen-scope-gate-2026-08-03.md``,
written and committed BEFORE this file was written.

What it measures, in the pre-registration's order:

* **A** — the dark-fuel census across all five artifact ISOs: for every
  ``flag == "ok"`` (plant, class) row, the share of the plant's CEMS fuel burned
  in units that report heat input and ZERO gross load all year. That fuel makes
  no electricity, so it cannot be a topping cycle's free co-product, and the
  derive currently charges it to the plant's power tranches.
* **K1** — are those units boilers, or turbines with a reporting gap?
* **K2** — does the share persist across 2023/2024/2025?
* **K3** — does CEMS reconcile with eGRID at the corrected plants?
* **K4** — does the corrected rate stay physical (>= credited, inside the band)?
* **K6** — which ``ok`` rows CEMS does not cover at all, stated not hidden.
* **W1** — the pre-arm wiring check: what the corrected rate does to the loaded
  fleet, per (plant, class), through the model's OWN loader.

Rule 24 ``[R-REGISTRY]``: every crosswalk is the repo's own (``states_for_iso``,
``_hour_index_8760``, ``unit_family``, ``load_fleet_from_csv``,
``_CACHE_KEY_RETIRED_FIELDS``). No hand map is introduced.

Usage::

    .venv/bin/python scripts/probes/_miso122_hybrid_cogen_scope.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import fields as dc_fields
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lib.bench_multiclass import unit_family  # noqa: E402
from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.campd import _hour_index_8760, states_for_iso  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

#: The five ISOs the derive writes an artifact for (ERCOT prices CHP through the
#: CAMPD per-plant binning path and has no row here).
ISOS: tuple[str, ...] = ("MISO", "PJM", "CAISO", "NYISO", "NEISO")

#: The ISO whose lever queue this session is working, and whose keeper the A/B
#: replays. Only its rows drive a verdict; the other four are the generality
#: sweep the pre-registration requires before an ISO-agnostic derive changes.
ISO = "MISO"
BUNDLE = ROOT / "results" / "calibration" / "miso117_ctheatrate_B"

#: The eGRID vintage the artifact is frozen at, hence the CEMS year the share is
#: measured from (PREREG section 3, property 3: no vintage is mixed).
VINTAGE = 2023
#: Rule 16 ``[R-ALLYEARS]`` span; K2 persistence is checked across all of it.
YEARS = (2023, 2024, 2025)

#: Pre-registered kill bands (PREREG section 4).
K1_BOILER_SHARE = 0.90  # >= this share of dark fuel must be non-turbine
K2_MAX_MIN_RATIO = 2.0  # dark-share stability across YEARS
K3_CEMS_BAND = (0.90, 1.10)  # miso-118's two-meter agreement band, reused
#: Reporting floor for the census table. ZERO by pre-registration (section 3,
#: property 4: the correction has no threshold, so neither does the census —
#: an 0.09 % plant is reported, not rounded away).
REPORT_FLOOR = 0.0

UNIT_COLS = [
    "facilityId",
    "unitId",
    "date",
    "hour",
    "grossLoad",
    "heatInput",
    "unitType",
    "primaryFuelInfo",
]


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def artifact(iso: str) -> pd.DataFrame:
    """The committed power-only CHP heat-rate artifact for ``iso``, all flags."""
    return pd.read_csv(PROCESSED_DIR / f"chp_power_only_heat_rates_{iso}.csv")


def campd_units(iso: str, year: int, plant_codes: set[int]) -> pd.DataFrame:
    """CAMPD hourly unit rows for ``plant_codes``, on the model's calendar.

    Same construction as miso-116/118 so the census is comparable to the
    measurements those sessions published. ``grossLoad`` is NaN, not 0, for a
    unit that has no gross-load channel at all — which is exactly the boiler
    case — so both channels are filled to 0.0 before any aggregation.
    """
    frames = []
    for state in states_for_iso(iso):
        path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=UNIT_COLS)
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(plant_codes)]
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["plant_code"] = out["facilityId"].astype(int)
    dt = pd.to_datetime(out["date"])
    out["hoy"] = _hour_index_8760(dt.dt.month, dt.dt.day, out["hour"])
    out = out[out["hoy"] >= 0]  # rule 8 [R-8760]: Feb 29 dropped
    out["family"] = [
        unit_family(t, f)
        for t, f in zip(out["unitType"], out["primaryFuelInfo"], strict=True)
    ]
    out["grossLoad"] = out["grossLoad"].fillna(0.0)
    out["heatInput"] = out["heatInput"].fillna(0.0)
    return out


def dark_share_table(iso: str, year: int, plant_codes: set[int]) -> pd.DataFrame:
    """``{plant_code -> dark fuel share, dark MMBtu, total MMBtu, n dark units}``.

    A DARK unit is one that reports ``heatInput > 0`` and ``grossLoad == 0``
    summed over the WHOLE year — a purely behavioural definition, never a
    ``unitType`` allowlist (which would be a hand map, rule 24). K1 then checks
    that the units the behaviour selects really are boilers.
    """
    u = campd_units(iso, year, plant_codes)
    if u.empty:
        return pd.DataFrame(
            columns=["plant_code", "dark_share", "dark_mmbtu", "total_mmbtu", "n_dark"]
        )
    by_unit = u.groupby(["plant_code", "unitId"])[["heatInput", "grossLoad"]].sum()
    by_unit["dark"] = (by_unit["grossLoad"] <= 0.0) & (by_unit["heatInput"] > 0.0)
    rows = []
    for code, grp in by_unit.groupby(level="plant_code"):
        total = float(grp["heatInput"].sum())
        if total <= 0.0:
            continue
        dark = float(grp.loc[grp["dark"], "heatInput"].sum())
        rows.append(
            {
                "plant_code": int(code),
                "dark_share": dark / total,
                "dark_mmbtu": dark,
                "total_mmbtu": total,
                "n_dark": int(grp["dark"].sum()),
            }
        )
    return pd.DataFrame(rows)


def keeper_config() -> ScenarioConfig:
    """The MISO keeper's exact ``ScenarioConfig`` (the miso-118 construction).

    Unknown keys are a hard failure unless they appear in the repo's own retired
    -field registry — a silently dropped live flag is the miso-115 section 4
    defect.
    """
    from market_sim.config.scenarios import _CACHE_KEY_RETIRED_FIELDS

    d = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    unknown = set(d) - {f.name for f in dc_fields(ScenarioConfig)}
    stale = unknown & set(_CACHE_KEY_RETIRED_FIELDS)
    if unknown - stale:
        raise SystemExit(f"unknown ScenarioConfig keys {sorted(unknown - stale)}")
    return ScenarioConfig(**{k: v for k, v in d.items() if k not in stale})


def loaded_chp_rates(iso: str, year: int) -> pd.DataFrame:
    """Capacity-weighted loaded heat rate per (plant, CHP class), keeper flags."""
    cfg = keeper_config()
    gens = load_fleet_from_csv(
        iso,
        year=year,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        measured_ct_heat_rates=getattr(cfg, "measured_ct_heat_rates", False),
    )
    rows = [
        {
            "plant_code": int(g.plant_code),
            "plant_group": str(g.plant_group),
            "pmax_mw": float(g.pmax_mw),
            "heat_rate": float(g.heat_rate),
        }
        for g in gens
        if g.plant_code is not None and str(g.plant_group) in ("CC_CHP", "CT_CHP")
    ]
    d = pd.DataFrame(rows)
    if d.empty:
        return d
    d["wh"] = d["pmax_mw"] * d["heat_rate"]
    g = d.groupby(["plant_code", "plant_group"]).agg(
        cap_mw=("pmax_mw", "sum"), wh=("wh", "sum")
    )
    g["loaded_hr"] = g["wh"] / g["cap_mw"]
    return g.reset_index().drop(columns="wh")


# --------------------------------------------------------------------------- #
# A. The census
# --------------------------------------------------------------------------- #
def part_a() -> dict[str, pd.DataFrame]:
    """Dark-fuel share for every ``ok``-flagged plant in all five ISOs."""
    print("=" * 78)
    print("A. DARK-FUEL CENSUS — all five artifact ISOs, ok-flagged rows, "
          f"CEMS {VINTAGE}")
    print("=" * 78)
    out: dict[str, pd.DataFrame] = {}
    for iso in ISOS:
        art = artifact(iso)
        ok = art[art["flag"] == "ok"]
        codes = {int(p) for p in ok["plant_code"]}
        ds = dark_share_table(iso, VINTAGE, codes)
        merged = (
            ok.merge(ds, on="plant_code", how="left")
            .assign(dark_share=lambda d: d["dark_share"].fillna(0.0))
            .sort_values("dark_share", ascending=False)
        )
        # The applied share is the MEASURED share gated on the two meters
        # agreeing (K3) and on the plant not being entirely dark — the same
        # two conditions the derive applies, so census and artifact cannot
        # drift apart.
        lo_r, hi_r = K3_CEMS_BAND
        ratio = merged["cems_vs_egrid_total"].astype(float)
        reconciled = ratio.between(lo_r, hi_r) & (merged["dark_share"] < 1.0)
        merged["applied_share"] = merged["dark_share"].where(reconciled, 0.0)
        merged["corrected_hr"] = merged["heat_rate"] * (1.0 - merged["applied_share"])
        merged["delta_pct"] = merged["corrected_hr"] / merged["heat_rate"] - 1.0
        out[iso] = merged

        hit = merged[merged["dark_share"] > REPORT_FLOOR]
        covered = merged[merged["plant_code"].isin(set(ds["plant_code"]))]
        print(
            f"\n  {iso}: {len(merged)} ok rows / "
            f"{merged['class_capacity_mw'].sum():,.0f} MW; "
            f"CEMS covers {len(covered)} rows / "
            f"{covered['class_capacity_mw'].sum():,.0f} MW; "
            f"{len(hit)} rows carry dark fuel > {REPORT_FLOOR:.1%} "
            f"({hit['class_capacity_mw'].sum():,.0f} MW)"
        )
        if hit.empty:
            print("      (no row moves)")
            continue
        print(
            f"      {'plant':<8}{'class':<9}{'name':<28}{'cap MW':>9}"
            f"{'dark':>8}{'applied':>9}{'loaded':>9}{'corrected':>11}{'delta':>9}"
        )
        for r in hit.itertuples(index=False):
            print(
                f"      {r.plant_code:<8}{r.plant_group:<9}"
                f"{str(r.plant_name)[:26]:<28}{r.class_capacity_mw:9,.1f}"
                f"{r.dark_share:8.1%}{r.applied_share:9.1%}"
                f"{r.heat_rate:9.4f}{r.corrected_hr:11.4f}{r.delta_pct:9.1%}"
            )
    return out


# --------------------------------------------------------------------------- #
# Kills
# --------------------------------------------------------------------------- #
def part_k1(census: dict[str, pd.DataFrame]) -> bool:
    """K1 — the dark units must be boilers, not turbines with a reporting gap."""
    print("\n" + "=" * 78)
    print("K1. ARE THE DARK UNITS BOILERS? (bar: >= "
          f"{K1_BOILER_SHARE:.0%} of dark fuel in a non-turbine unitType)")
    print("=" * 78)
    ok = True
    for iso, merged in census.items():
        hit = merged[merged["dark_share"] > REPORT_FLOOR]
        if hit.empty:
            continue
        codes = {int(p) for p in hit["plant_code"]}
        u = campd_units(iso, VINTAGE, codes)
        by_unit = u.groupby(["plant_code", "unitId", "unitType", "family"])[
            ["heatInput", "grossLoad"]
        ].sum()
        for code in sorted(codes):
            sub = by_unit.loc[code]
            dark = sub[(sub["grossLoad"] <= 0.0) & (sub["heatInput"] > 0.0)]
            if dark.empty:
                continue
            tot = float(dark["heatInput"].sum())
            print(f"\n  {iso} plant {code}: {len(dark)} dark unit(s), "
                  f"{tot:,.0f} MMBtu")
            nonturbine = 0.0
            for (unit, utype, fam), r in dark.iterrows():
                is_turbine = str(fam).startswith(("CC", "CT"))
                if not is_turbine:
                    nonturbine += float(r["heatInput"])
                print(
                    f"      unit {str(unit):<8} unitType {str(utype)[:34]:<36} "
                    f"family {str(fam):<8} heat {r['heatInput']:12,.0f}"
                    f"{'   <-- TURBINE' if is_turbine else ''}"
                )
            share = nonturbine / tot if tot > 0 else 0.0
            verdict = "PASS" if share >= K1_BOILER_SHARE else "FIRES -> VOID"
            print(f"      non-turbine share of dark fuel {share:.1%}  {verdict}")
            ok = ok and share >= K1_BOILER_SHARE
    print(f"\n  K1 overall: {'PASS' if ok else 'FIRES'}")
    return ok


def part_k2(census: dict[str, pd.DataFrame]) -> bool:
    """K2 — the share must persist across 2023/2024/2025 within a factor of 2."""
    print("\n" + "=" * 78)
    print(f"K2. PERSISTENCE across {YEARS} (bar: non-zero every year, "
          f"max/min <= {K2_MAX_MIN_RATIO})")
    print("=" * 78)
    ok = True
    for iso, merged in census.items():
        hit = merged[merged["dark_share"] > REPORT_FLOOR]
        if hit.empty:
            continue
        codes = {int(p) for p in hit["plant_code"]}
        per_year = {y: dark_share_table(iso, y, codes) for y in YEARS}
        for code in sorted(codes):
            vals = []
            for y in YEARS:
                d = per_year[y]
                v = d.loc[d["plant_code"] == code, "dark_share"]
                vals.append(float(v.iloc[0]) if len(v) else 0.0)
            lo, hi = min(vals), max(vals)
            good = lo > 0.0 and (hi / lo) <= K2_MAX_MIN_RATIO
            ok = ok and good
            print(
                f"  {iso} plant {code}: "
                + "  ".join(f"{y} {v:6.2%}" for y, v in zip(YEARS, vals, strict=True))
                + f"   max/min {hi / lo if lo > 0 else float('inf'):.2f}"
                + f"   {'PASS' if good else 'FIRES -> VOID'}"
            )
    print(f"\n  K2 overall: {'PASS' if ok else 'FIRES'}")
    return ok


def part_k3(census: dict[str, pd.DataFrame]) -> bool:
    """K3 — CEMS must reconcile with eGRID's total at every corrected plant."""
    print("\n" + "=" * 78)
    print(f"K3. TWO-METER RECONCILIATION (band {K3_CEMS_BAND}, "
          "miso-118's pre-registered band reused)")
    print("=" * 78)
    lo, hi = K3_CEMS_BAND
    ok = True
    for iso, merged in census.items():
        hit = merged[merged["dark_share"] > REPORT_FLOOR]
        for r in hit.itertuples(index=False):
            v = r.cems_vs_egrid_total
            good = pd.notna(v) and lo <= float(v) <= hi
            ok = ok and good
            print(
                f"  {iso} plant {r.plant_code} {r.plant_group}: "
                f"cems_vs_egrid_total {v}   "
                f"{'PASS' if good else 'FIRES -> flag out, do not correct'}"
            )
    print(f"\n  K3 overall: {'PASS' if ok else 'FIRES'}")
    return ok


def part_k4(census: dict[str, pd.DataFrame]) -> bool:
    """K4 — the corrected rate must stay >= credited and inside the class band."""
    # The band is the derive's own constant, imported rather than restated
    # (rule 5 [R-NO-MAGIC] / rule 24 [R-REGISTRY]: one definition, one place).
    sys.path.insert(0, str(ROOT / "scripts" / "data"))
    from derive_chp_power_only_heat_rates import _HR_BAND  # noqa: E402

    print("\n" + "=" * 78)
    print("K4. CORRECTED RATE STAYS PHYSICAL (>= credited, inside _HR_BAND)")
    print("=" * 78)
    ok = True
    for iso, merged in census.items():
        hit = merged[merged["dark_share"] > REPORT_FLOOR]
        for r in hit.itertuples(index=False):
            lo, hi = _HR_BAND[r.plant_group]
            good = (
                r.corrected_hr >= r.heat_rate_credited
                and lo <= r.corrected_hr <= hi
            )
            if iso == ISO:
                ok = ok and good
            print(
                f"  {iso} plant {r.plant_code} {r.plant_group}: corrected "
                f"{r.corrected_hr:.4f} vs credited {r.heat_rate_credited:.4f}, "
                f"band [{lo}, {hi}]   {'PASS' if good else 'FIRES -> flag out'}"
            )
    # K4's pre-registered disposition (PREREG section 4) is PER PLANT — "that
    # plant is flagged out, not corrected", via the derive's existing band
    # machinery. It is NOT a global stop, and it is not an AND across ISOs:
    # only this session's ISO can decide this session's verdict (rule 25
    # [R-ISO-SCOPE]). Other ISOs' firings are reported for their own lanes.
    print(f"\n  K4 for {ISO}: {'PASS' if ok else 'FIRES'} "
          "(other ISOs' firings are per-plant flag-outs, reported not gating)")
    return ok


def part_k6(census: dict[str, pd.DataFrame]) -> None:
    """K6 — state, do not hide, the ok rows CEMS does not cover."""
    print("\n" + "=" * 78)
    print("K6. COVERAGE HONESTY — ok rows CEMS does not cover keep dark_share=0")
    print("=" * 78)
    for iso, merged in census.items():
        uncov = merged[merged["cems_vs_egrid_total"].isna()]
        print(
            f"  {iso}: {len(uncov)} of {len(merged)} ok rows uncovered "
            f"({uncov['class_capacity_mw'].sum():,.0f} of "
            f"{merged['class_capacity_mw'].sum():,.0f} MW). Their rates are "
            "UNCHANGED — the status quo, not a claim of no dark fuel."
        )


# --------------------------------------------------------------------------- #
# W1. Pre-arm wiring check
# --------------------------------------------------------------------------- #
def part_w1(census: dict[str, pd.DataFrame]) -> None:
    """W1 — what the correction does to the LOADED fleet, per (plant, class).

    Read through the model's own loader with the KEEPER's flags, so the number
    is the rate the LP would actually price with, not the artifact column.
    """
    print("\n" + "=" * 78)
    print(f"W1. LOADED-FLEET EFFECT ({ISO}, keeper flags, all three years)")
    print("=" * 78)
    merged = census[ISO]
    hit = merged[merged["dark_share"] > REPORT_FLOOR]
    if hit.empty:
        print("  nothing moves")
        return
    for year in YEARS:
        loaded = loaded_chp_rates(ISO, year)
        print(f"\n  {year}")
        for r in hit.itertuples(index=False):
            m = loaded[
                (loaded["plant_code"] == r.plant_code)
                & (loaded["plant_group"] == r.plant_group)
            ]
            if m.empty:
                print(
                    f"    plant {r.plant_code} {r.plant_group}: NOT IN FLEET "
                    "-> W1 FAILS for this row"
                )
                continue
            cur = float(m["loaded_hr"].iloc[0])
            cap = float(m["cap_mw"].iloc[0])
            print(
                f"    plant {r.plant_code} {r.plant_group}: cap {cap:7,.1f} MW  "
                f"loaded {cur:.4f} -> corrected {r.corrected_hr:.4f}  "
                f"({r.corrected_hr / cur - 1:+.1%})"
            )


def main() -> int:
    """Run every pre-registered Phase-0 measurement and print the verdict."""
    census = part_a()
    k1 = part_k1(census)
    k2 = part_k2(census)
    k3 = part_k3(census)
    k4 = part_k4(census)
    part_k6(census)
    part_w1(census)

    print("\n" + "=" * 78)
    print("PHASE-0 VERDICT")
    print("=" * 78)
    allok = k1 and k2 and k3 and k4
    print(f"  {ISO}: K1 boilers {k1}   K2 persistence {k2}   "
          f"K3 reconciliation {k3}   K4 physical {k4}")
    print(
        "  -> "
        + (
            f"PROCEED for {ISO}: build the scope gate, re-derive {ISO} only, "
            "run the A/B."
            if allok
            else f"STOP for {ISO}: a kill fired; see above."
        )
    )
    print(
        "\n  OTHER ISOs are a GENERALITY SWEEP, not a verdict (rule 25\n"
        "  [R-ISO-SCOPE]). Their artifacts are NOT re-derived here: each lane\n"
        "  owns its own A/B and its own keeper. Handed off with measured\n"
        "  numbers in the finding."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
