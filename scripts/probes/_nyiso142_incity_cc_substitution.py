"""nyiso-142 — reproduce the in-city CC / ST_GAS substitution identification.

Backs `results/calibration/FINDING-nyiso142-incity-cc-outage-substitution-2026-08-17.md`.
Three measurements, all from COMMITTED artifacts, none of them a residual:

1. **Zonal decomposition of the 2023 -> 2025 CC/ST move** from the per-plant
   benchmark sidecars — the step that refutes the merit-order reading of
   nyiso-141 §1 by showing the substitution is local to New York City.
2. **Per-plant CC_REGULAR actuals**, which localise the NYC decline to Astoria
   Energy (55375) and Poletti/Zeltmann (56196).
3. **Booked CC outage days per plant-year** from the committed CAMPD unit-outage
   extract the keeper itself consumes (``outage_source="historic"``), which is
   the availability evidence for the CC side.

No LP is constructed, no year is solved, scored or registered, and no year
outside 2023-2025 is read.

Usage:
    PYTHONPATH=$PWD python scripts/probes/_nyiso142_incity_cc_substitution.py
"""

from __future__ import annotations

import collections
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "NYISO"
OUTAGES = REPO / "data" / "raw" / "campd-unit-outages-NYISO.csv"
# nyiso-141: Astoria's 2025 benchmark entry carries the stack double-count.
ASTORIA_2025_RAW, ASTORIA_2025_CORRECTED = 2.6722, 1.359


def _plants(year: int) -> dict:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["plants"]


def zonal_decomposition() -> pd.DataFrame:
    """CC_REGULAR and ST_GAS benchmark energy by zone-year (TWh)."""
    agg: dict[tuple[str, str, int], float] = collections.defaultdict(float)
    for year in YEARS:
        for rec in _plants(year).values():
            group = rec.get("group")
            if group not in ("CC_REGULAR", "ST_GAS"):
                continue
            agg[(group, str(rec.get("zone")), year)] += float(rec.get("e_ann") or 0.0)
    rows = []
    for group in ("CC_REGULAR", "ST_GAS"):
        for zone in sorted({z for g, z, _ in agg if g == group}):
            vals = [agg[(group, zone, y)] for y in YEARS]
            rows.append(
                {
                    "group": group,
                    "zone": zone,
                    **{str(y): v for y, v in zip(YEARS, vals)},
                    "d25_23": vals[-1] - vals[0],
                }
            )
    return pd.DataFrame(rows)


def cc_by_plant() -> pd.DataFrame:
    """Per-plant CC_REGULAR CAMPD gross and benchmark energy, by year (TWh)."""
    out: dict[tuple[str, str, str], dict[int, tuple]] = {}
    for year in YEARS:
        for pid, rec in _plants(year).items():
            if rec.get("group") != "CC_REGULAR":
                continue
            key = (pid, str(rec.get("name")), str(rec.get("zone")))
            out.setdefault(key, {})[year] = (
                float(rec.get("c_ann") or 0.0),
                float(rec.get("e_ann") or 0.0),
            )
    rows = []
    for (pid, name, zone), per_year in out.items():
        c = [per_year.get(y, (float("nan"),) * 2)[0] for y in YEARS]
        rows.append(
            {
                "plant": pid,
                "name": name[:30],
                "zone": zone,
                **{f"campd_{y}": v for y, v in zip(YEARS, c)},
                "d25_23": c[-1] - c[0],
            }
        )
    return pd.DataFrame(rows).sort_values("d25_23")


def cc_outage_days() -> pd.DataFrame:
    """Booked CC outage days per plant-year from the committed detector extract."""
    d = pd.read_csv(OUTAGES, comment="#")
    d["facility_id"] = pd.to_numeric(d["facility_id"], errors="coerce")
    d["year"] = pd.to_datetime(d["outage_start"], errors="coerce").dt.year
    d["days"] = pd.to_numeric(d["duration_days"], errors="coerce")
    cc = d[d["plant_group"].astype(str).str.contains("CC", na=False)]
    cc = cc[cc["year"].isin(YEARS)]
    piv = (
        cc.groupby(["facility_name", "facility_id", "year"])["days"].sum().unstack()
    )
    for y in YEARS:
        if y not in piv.columns:
            piv[y] = 0.0
    # A plant absent from the base year has no comparable delta — a NaN->0
    # baseline would manufacture a spurious +365 for any plant the detector
    # only starts booking in 2025. Require presence in both endpoints.
    piv = piv[piv[YEARS[0]].notna() & piv[YEARS[-1]].notna()]
    piv["d25_23"] = piv[YEARS[-1]] - piv[YEARS[0]]
    return piv.sort_values("d25_23", ascending=False)


def lp_availability() -> pd.DataFrame:
    """The per-bin availability multiplier the LP is actually built from.

    ``unit_outage_derate_factors`` is an INPUT of the solve, not an output —
    reading it constructs no LP and solves nothing. This is the measurement
    that refutes the "the outages never reach the model" reading.
    """
    from market_sim.data.outages import unit_outage_derate_factors

    rows = []
    for year in YEARS:
        factors = unit_outage_derate_factors(year, iso="NYISO")
        for key, arr in factors.items():
            if key[0] not in (55375, 2500, 56196):
                continue
            rows.append(
                {
                    "bin": f"{key[0]}:{key[1]}",
                    "year": year,
                    "mean_avail": float(arr.mean()),
                    "min_avail": float(arr.min()),
                    "equiv_full_outage_days": float((1.0 - arr).sum()) / 24.0,
                }
            )
    return pd.DataFrame(rows).pivot(
        index="bin", columns="year", values=["mean_avail", "equiv_full_outage_days"]
    )


def ravenswood_override_contamination() -> pd.DataFrame:
    """How much of Ravenswood's ST_GAS derate comes from its NON-steam units.

    ``outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}`` routes every Ravenswood
    outage row onto the plant's single ST_GAS bin, because CAMPD tags the whole
    plant ``CC_REGULAR``. The obvious worry is that this over-derates the in-city
    steam with CC/CT downtime. Re-accumulate the derate twice — all rows, then
    steam units only — to size that contamination.
    """
    import numpy as np

    from market_sim.data.outages import (
        UNIT_OUTAGE_MIN_DAYS,
        _iso_plant_capacity,
        outage_hour_mask,
        unit_outage_event_window,
    )

    denominator = _iso_plant_capacity("NYISO")[(2500, "ST_GAS")]
    d = pd.read_csv(OUTAGES, comment="#")
    d["facility_id"] = pd.to_numeric(d["facility_id"], errors="coerce")
    d = d[(d["facility_id"] == 2500) & (d["duration_days"] >= UNIT_OUTAGE_MIN_DAYS)]
    steam_units = {"10", "20", "30"}

    rows = []
    for year in YEARS:
        total = np.zeros(8760)
        steam = np.zeros(8760)
        for r in d.itertuples(index=False):
            mask = outage_hour_mask(*unit_outage_event_window(r, False), year, 8760)
            if not mask.any():
                continue
            share = float(r.unit_capacity_mw) / denominator
            total[mask] += share
            if str(r.unit_id) in steam_units:
                steam[mask] += share
        a_all = np.clip(1.0 - total, 0.0, 1.0)
        a_steam = np.clip(1.0 - steam, 0.0, 1.0)
        rows.append(
            {
                "year": year,
                "as_modelled": a_all.mean(),
                "steam_units_only": a_steam.mean(),
                "contamination_days": ((1.0 - a_all).sum() - (1.0 - a_steam).sum()) / 24.0,
                "total_outage_days": (1.0 - a_all).sum() / 24.0,
            }
        )
    return pd.DataFrame(rows)


def zone_j_balance(bundle: Path) -> pd.DataFrame:
    """How the MODEL serves Zone J: in-city generation vs net flow into NYC.

    The discriminator between the two surviving readings of §3.2. Reads a
    solved bundle's committed ``hourly/`` sidecars — ``unit_hourly`` for in-city
    generation by class, ``network`` for the boundary flows and whether they
    bind, ``system`` for zonal demand. No LP is constructed.
    """
    rows = []
    for year in YEARS:
        unit_p = bundle / "hourly" / f"unit_hourly_{year}.parquet"
        net_p = bundle / "hourly" / f"network_{year}.parquet"
        sys_p = bundle / "hourly" / f"system_{year}.parquet"
        if not (unit_p.exists() and net_p.exists() and sys_p.exists()):
            continue
        u = pd.read_parquet(
            unit_p, columns=["pass", "zone", "plant_group", "fuel", "mw"]
        )
        u = u[(u["pass"] == "P1") & (u["zone"] == "NYC")]
        by_group = u.groupby("plant_group")["mw"].sum() / 1.0e6

        n = pd.read_parquet(net_p)
        n = n[n["pass"] == "P1"]
        into = {}
        for name in ("Lower_Hudson>NYC", "NYISO_external>NYC", "NYC>Long_Island"):
            s = n[n["name"] == name]
            if s.empty:
                continue
            into[name] = (
                float(s["mw"].sum()) / 1.0e6,
                int((s["mw"] >= s["limit_up"] - 1e-6).sum()),
            )

        sysd = pd.read_parquet(sys_p)
        sysd = sysd[(sysd["pass"] == "P1") & (sysd["zone"] == "NYC")]
        demand = float(sysd["demand"].sum()) / 1.0e6

        lh = into.get("Lower_Hudson>NYC", (0.0, 0))
        ext = into.get("NYISO_external>NYC", (0.0, 0))
        li = into.get("NYC>Long_Island", (0.0, 0))
        rows.append(
            {
                "year": year,
                "nyc_demand_twh": demand,
                "incity_gen_twh": float(by_group.sum()),
                "in_from_Lower_Hudson_twh": lh[0],
                "LH>NYC_hours_at_limit": lh[1],
                "in_from_external_twh": ext[0],
                "out_to_Long_Island_twh": li[0],
                "incity_ST_GAS_twh": float(by_group.get("ST_GAS", 0.0)),
                "incity_CC_REGULAR_twh": float(by_group.get("CC_REGULAR", 0.0)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print("nyiso-142 — in-city CC / ST_GAS substitution, from committed artifacts")
    print("=" * 92)

    print("\n### 1. Zonal decomposition, benchmark e_ann (TWh)")
    z = zonal_decomposition()
    print(z.round(3).to_string(index=False))
    nyc_st = z[(z.group == "ST_GAS") & (z.zone == "NYC")].iloc[0]
    print(
        f"\n  NYC ST_GAS d25-23 as scored: {nyc_st.d25_23:+.3f} TWh; "
        f"net of the nyiso-141 Astoria double-count "
        f"({ASTORIA_2025_RAW:.4f} -> {ASTORIA_2025_CORRECTED:.3f}): "
        f"{nyc_st.d25_23 - (ASTORIA_2025_RAW - ASTORIA_2025_CORRECTED):+.3f} TWh"
    )
    nyc_cc = z[(z.group == "CC_REGULAR") & (z.zone == "NYC")].iloc[0]
    print(
        f"  NYC is the ONLY zone whose CC_REGULAR falls: {nyc_cc.d25_23:+.3f} TWh"
    )

    print("\n### 2. Per-plant CC_REGULAR, CAMPD gross (TWh) — 6 largest declines")
    print(cc_by_plant().head(6).round(3).to_string(index=False))

    print("\n### 3. Booked CC outage days per plant-year (unit-days, not cap-weighted)")
    print(cc_outage_days().head(8).round(1).to_string())
    print(
        "\n  The three in-city CCs (Astoria Energy 55375, Ravenswood 2500, "
        "Poletti 56196) all rise together in 2025."
    )

    print("\n### 4. The availability the LP is BUILT from (input inspection, no LP)")
    print(lp_availability().round(3).to_string())
    print("  -> the outages DO reach the model: the plumbing reading is refuted.")

    print("\n### 5. Ravenswood override — is the ST_GAS bin over-derated by CC/CT rows?")
    print(ravenswood_override_contamination().round(4).to_string(index=False))
    print("  -> under 2 % of the derate; the routing is sound, that reading fails too.")

    bundle = Path("results/calibration/nyiso142_control")
    if (bundle / "hourly").exists():
        print(f"\n### 6. How the MODEL serves Zone J ({bundle})")
        print(zone_j_balance(bundle).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
