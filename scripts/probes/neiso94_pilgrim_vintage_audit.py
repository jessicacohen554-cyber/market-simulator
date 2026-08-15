#!/usr/bin/env python3
"""neiso-94 — adjudicate the 2019 Pilgrim fleet-vintage gap, on measurement.

Successor to ``scripts/probes/neiso90_final_prereq_audit.py`` (which is re-run
unchanged alongside this and still reproduces byte-identically). That probe
walks *input resolvability*; this one walks the one thing it cannot see — an
input that resolves cleanly and is nonetheless **short a generator**.

Four independent measurements, none of which needs a solve:

1. **The envelope self-test.** Integrate the committed per-reactor nuclear
   availability overlay (``data/raw/nuclear-availability-NEISO.csv``, extended
   to 2019-2022 by neiso-93) against the model fleet's own pmax, and compare to
   EIA-930 ISNE ``NUC`` hourly telemetry — an independent collection. The
   overlay is a *fraction applied to units already in the fleet*, so this
   measures exactly the fleet-membership error and nothing else.

2. **The monthly signature.** Decompose the 2019 gap by month. A fleet-vintage
   defect has a step signature at the retirement date; a CF mis-derivation does
   not.

3. **The scoring consequence.** Size the gap against the C1 fuel-mix volume
   band (``min(2% of ISO total load, 8 TWh)``) it would be spent against, and
   against the C3c tail actuals that determine whether 2019 can discriminate.

4. **The blast radius.** Replicate ``process_eia860.build_within_window_retirees``
   at a lowered ``RETIREMENT_WINDOW_START`` to count what a repair would add,
   per ISO — the number that decides NEISO-local patch vs cross-ISO charter.

**NO YEAR IS SOLVED, SCORED OR REGISTERED.** No LP is constructed and no model
output is produced or read. Every number is either a committed input or a
published actual. Under CLAUDE.md rule 22 as rewritten 2026-08-06 ("WHAT IS
HELD OUT IS THE *SCORE*, NEVER THE *DATA*") this is unrestricted; the spend is
looking at an answer, which nothing here does.

Usage::

    uv run python scripts/probes/neiso94_pilgrim_vintage_audit.py
"""

from __future__ import annotations

import calendar
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import BA_CODE_TO_ISO, load_fleet_from_csv  # noqa: E402

ISO = "NEISO"
YEARS = tuple(range(2019, 2026))
RAW = REPO / "data" / "raw"

# Pilgrim Nuclear Power Station, Plymouth MA. EIA plant code 1590 (NOT 6098 --
# that is Big Stone, a South Dakota coal plant; the mis-citation was corrected
# by neiso-93). Retired 31 May 2019.
PILGRIM = 1590

# C1 fuel-mix volume band (scripts/calibration_verdict.py:322-324).
FUELMIX_VOL_LOAD_FRAC = 0.02
FUELMIX_VOL_CAP_TWH = 8.0

# The constant that gates the mid-year-retiree injection path
# (scripts/data/process_eia860.py:74).
RETIREMENT_WINDOW_START = 2023
PROPOSED_WINDOW_START = 2019


def nuclear_fleet() -> dict[tuple[int, int], float]:
    """Return ``{(plant_code, unit_no): pmax_mw}`` for the model's NEISO nuclear."""
    cfg = get_iso_config(ISO)
    out: dict[tuple[int, int], float] = {}
    for g in load_fleet_from_csv(ISO, cfg):
        if g.fuel_type != "nuclear" or g.pmax_mw <= 0:
            continue
        unit_no = int(str(g.unit_id).rsplit("_", 1)[-1])
        out[(int(g.plant_code), unit_no)] = out.get((int(g.plant_code), unit_no), 0.0) + g.pmax_mw
    return out


def eia930_nuclear() -> pd.Series:
    """Hourly EIA-930 ISNE ``NUC`` net generation, indexed on the ISO's clock."""
    df = pd.read_parquet(RAW / "ISNE_fueltype.parquet")
    df = df[df["fueltype"].astype(str).str.upper() == "NUC"].copy()
    df["period"] = pd.to_datetime(df["period"])
    return df.set_index("period").tz_convert("US/Eastern")["value_mwh"]


def overlay_energy(pmax: dict[tuple[int, int], float]) -> pd.DataFrame:
    """Integrate the per-reactor availability overlay into MWh per reactor-day."""
    df = pd.read_csv(RAW / f"nuclear-availability-{ISO}.csv", parse_dates=["date"])
    df["pmax_mw"] = [
        pmax[(int(p), int(u))] for p, u in zip(df["plant_code"], df["unit_no"], strict=True)
    ]
    df["mwh"] = df["avail"] * df["pmax_mw"] * 24.0
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def measure_envelope(df: pd.DataFrame, actual: pd.Series) -> dict:
    """(1) Annual overlay-implied nuclear vs EIA-930 actual, per year."""
    model = df.groupby("year")["mwh"].sum() / 1e6
    act = actual.groupby(actual.index.year).sum() / 1e6
    rows = []
    for y in YEARS:
        rows.append(
            {
                "year": y,
                "model_overlay_twh": round(float(model.get(y, float("nan"))), 3),
                "eia930_actual_twh": round(float(act.get(y, float("nan"))), 3),
                "gap_twh": round(float(model.get(y, float("nan")) - act.get(y, float("nan"))), 3),
            }
        )
    return {"rows": rows}


def measure_monthly(df: pd.DataFrame, actual: pd.Series, year: int) -> dict:
    """(2) Monthly gap decomposition — the step signature test."""
    m = df[df["year"] == year].groupby("month")["mwh"].sum()
    a = actual[actual.index.year == year]
    am = a.groupby(a.index.month).sum()
    rows = []
    for mo in range(1, 13):
        hours = calendar.monthrange(year, mo)[1] * 24
        gap = float(m.get(mo, 0.0) - am.get(mo, 0.0))
        rows.append(
            {
                "month": mo,
                "model_gwh": round(float(m.get(mo, 0.0)) / 1e3, 1),
                "actual_gwh": round(float(am.get(mo, 0.0)) / 1e3, 1),
                "gap_gwh": round(gap / 1e3, 1),
                "gap_avg_mw": round(gap / hours, 0),
            }
        )
    pre = sum(r["gap_gwh"] for r in rows[:5]) / 1e3
    post = sum(r["gap_gwh"] for r in rows[5:]) / 1e3
    return {"rows": rows, "jan_may_twh": round(pre, 3), "jun_dec_twh": round(post, 3)}


def measure_scoring_consequence() -> dict:
    """(3) The C1 band the gap would be spent against, and the C3c tail actuals."""
    reg = pd.read_parquet(RAW / "ISNE_region.parquet")
    reg["period"] = pd.to_datetime(reg["period"])
    reg = reg.set_index("period").tz_convert("US/Eastern")
    lmp = pd.read_parquet(RAW / "_validation-source" / f"actual_lmp_hourly_{ISO}.parquet")
    price_col = next((c for c in ("rt", "rt_lmp", "rt_price") if c in lmp.columns), None)
    rows = []
    for y in YEARS:
        s = reg[reg.index.year == y]
        gen = float(s[s["type_name"] == "Net Generation"]["value_mwh"].sum()) / 1e6
        ti = float(s[s["type_name"] == "Total Interchange"]["value_mwh"].sum()) / 1e6
        load = gen - ti
        rec = {
            "year": y,
            "net_generation_twh": round(gen, 2),
            "total_load_twh": round(load, 2),
            "c1_volume_band_twh": round(min(FUELMIX_VOL_LOAD_FRAC * load, FUELMIX_VOL_CAP_TWH), 3),
        }
        if price_col is not None and "year" in lmp.columns:
            yr = lmp[lmp["year"] == y][price_col].dropna()
            if len(yr):
                rec["rt_max"] = round(float(yr.max()), 2)
                rec["rt_hours_gt_300"] = int((yr > 300.0).sum())
        rows.append(rec)
    return {"rows": rows, "price_col": price_col}


def measure_blast_radius() -> dict:
    """(4) What lowering RETIREMENT_WINDOW_START would add, per ISO.

    Replicates ``process_eia860.build_within_window_retirees``' own filters:
    BA-mapped to a modelled ISO, whole-plant exits only (absent from the
    operable snapshot), latest vintage record per plant.
    """
    eia860 = RAW / "eia-860"
    plants = []
    for d in sorted(eia860.glob("vintage_*")) + [eia860]:
        for f in d.glob("eia860_plant*.parquet"):
            p = pd.read_parquet(f)
            if {"Plant Code", "Balancing Authority Code"} <= set(p.columns):
                plants.append(p[["Plant Code", "Balancing Authority Code"]])
    ba = (
        pd.concat(plants)
        .drop_duplicates("Plant Code")
        .set_index("Plant Code")["Balancing Authority Code"]
    )
    operable = pd.read_parquet(eia860 / "eia860_generator_operable.parquet")
    op_ids = set(pd.to_numeric(operable["Plant Code"], errors="coerce").dropna().astype(int))

    frames = []
    for d in sorted(eia860.glob("vintage_*")):
        f = d / "eia860_generator_retired_and_canceled.parquet"
        if not f.exists():
            continue
        r = pd.read_parquet(f)
        frames.append(
            pd.DataFrame(
                {
                    "plant_id": pd.to_numeric(r["Plant Code"], errors="coerce"),
                    "ret_year": pd.to_numeric(r["Retirement Year"], errors="coerce"),
                    "ret_month": pd.to_numeric(r["Retirement Month"], errors="coerce"),
                    "mw": pd.to_numeric(r["Nameplate Capacity (MW)"], errors="coerce"),
                }
            )
        )
    a = pd.concat(frames, ignore_index=True)
    a["iso"] = a["plant_id"].map(ba).astype("string").str.strip().map(BA_CODE_TO_ISO)
    a = a[a["iso"].notna()]
    a = a[~a["plant_id"].isin(op_ids)]
    a = a.drop_duplicates(subset=["plant_id"], keep="last")
    added = a[(a["ret_year"] >= PROPOSED_WINDOW_START) & (a["ret_year"] < RETIREMENT_WINDOW_START)]

    by_iso = (
        added.groupby("iso")
        .agg(plants=("plant_id", "nunique"), mw=("mw", "sum"))
        .round(1)
        .reset_index()
        .to_dict("records")
    )
    neiso = added[added["iso"] == ISO].sort_values("mw", ascending=False)
    pilgrim = a[a["plant_id"] == PILGRIM]
    return {
        "window_start_now": RETIREMENT_WINDOW_START,
        "window_start_proposed": PROPOSED_WINDOW_START,
        "by_iso": by_iso,
        "total_plants": int(added["plant_id"].nunique()),
        "total_mw": round(float(added["mw"].sum()), 1),
        "neiso_top": neiso.head(10)[["plant_id", "ret_year", "ret_month", "mw"]].to_dict("records"),
        "pilgrim_record": pilgrim[["plant_id", "ret_year", "ret_month", "mw", "iso"]].to_dict(
            "records"
        ),
    }


def main() -> None:
    pmax = nuclear_fleet()
    actual = eia930_nuclear()
    df = overlay_energy(pmax)

    out = {
        "iso": ISO,
        "nuclear_fleet_pmax_mw": {f"{p}_{u}": round(v, 2) for (p, u), v in sorted(pmax.items())},
        "nuclear_fleet_total_mw": round(sum(pmax.values()), 1),
        "pilgrim_in_overlay": bool((df["plant_code"] == PILGRIM).any()),
        "envelope_self_test": measure_envelope(df, actual),
        "monthly_2019": measure_monthly(df, actual, 2019),
        "scoring_consequence": measure_scoring_consequence(),
        "blast_radius": measure_blast_radius(),
    }

    print(f"### NEISO nuclear fleet (model): {out['nuclear_fleet_total_mw']:,.1f} MW")
    for k, v in out["nuclear_fleet_pmax_mw"].items():
        print(f"    plant_unit {k}: {v:,.2f} MW")
    print(f"    Pilgrim ({PILGRIM}) present in overlay: {out['pilgrim_in_overlay']}")

    print("\n### (1) Envelope self-test — overlay-implied nuclear vs EIA-930 actual")
    print("  year   model_TWh  actual_TWh     gap_TWh")
    for r in out["envelope_self_test"]["rows"]:
        print(f"  {r['year']}   {r['model_overlay_twh']:9.3f}  {r['eia930_actual_twh']:10.3f}  {r['gap_twh']:+10.3f}")

    print("\n### (2) 2019 monthly gap — the step signature")
    print("  mo   model_GWh  actual_GWh    gap_GWh   gap_avgMW")
    for r in out["monthly_2019"]["rows"]:
        print(f"  {r['month']:02d}  {r['model_gwh']:10.1f}  {r['actual_gwh']:10.1f}  {r['gap_gwh']:+9.1f}  {r['gap_avg_mw']:+10.0f}")
    print(f"  Jan-May {out['monthly_2019']['jan_may_twh']:+.3f} TWh | Jun-Dec {out['monthly_2019']['jun_dec_twh']:+.3f} TWh")

    print("\n### (3) Scoring consequence — the C1 band the gap is spent against")
    print("  year   netgen_TWh   load_TWh   C1_vol_band_TWh   RT_max$   RT_h>300")
    for r in out["scoring_consequence"]["rows"]:
        print(
            f"  {r['year']}   {r['net_generation_twh']:10.2f} {r['total_load_twh']:10.2f}"
            f"   {r['c1_volume_band_twh']:14.3f}   {r.get('rt_max', float('nan')):8.2f}"
            f"   {r.get('rt_hours_gt_300', -1):8d}"
        )

    br = out["blast_radius"]
    print(f"\n### (4) Blast radius — lowering RETIREMENT_WINDOW_START {br['window_start_now']} -> {br['window_start_proposed']}")
    print("  iso      plants        MW")
    for r in br["by_iso"]:
        print(f"  {r['iso']:<8} {r['plants']:6d}  {r['mw']:9.1f}")
    print(f"  TOTAL    {br['total_plants']:6d}  {br['total_mw']:9.1f}")
    print(f"  Pilgrim record: {br['pilgrim_record']}")

    dest = REPO / "results" / "calibration" / "_neiso94_pilgrim_vintage_audit.json"
    dest.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
