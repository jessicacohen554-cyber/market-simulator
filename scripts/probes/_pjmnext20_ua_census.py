"""PJM-NEXT-20 (zero LP): what non-benchmark supply moves ``U_a`` 2023 -> 2024?

NEXT-16 card 1b defines ``U_a = EIA-930 PJM demand + tie-meter export - classFull``; it
falls 7.6 TWh 2023 -> 2024. Since EIA-930 demand = net generation - total interchange,
``U_a`` splits EXACTLY into

  sum_f (930 NG_f - classFull_f)  +  930 unknown-fuel NG
  + (tie-meter export - 930 total interchange)  +  930 balance residual (D + TI - NG),

so each fuel's 930-minus-benchmark gap is an additive term. For every year 2019-2025:

1. **Fuel census** - EIA-930 PJM BA net generation by fuel (the NEXT-16 ``_e930``
   time axis: fixed EST, first 8760 hours) vs the bench ``classFull`` mapped to the same
   fuel, and vs the raw EIA-923 Page-1 net generation of the benchmark members
   (``run_calibration_full._iso_plant_ids(..., vintage_union=True)``) by fuel code.
2. **Gas plants** - members' EIA-923 gas net generation, the top 20 2023 -> 2024 risers
   with EIA-860 BA code (vintage of the year, and current), bench zone and first CC/CT
   operating year; member gas by EIA-860 BA code; non-member PJM-BA gas plants.
3. **Boundary evidence** - EIA-930 PJM interchange by directly interconnected BA, the
   PJM tie-meter legs present per year, EIA-930 demand vs PJM's own RTO metered load
   (``hrl_load_metered``), and EIA-930 by fuel vs PJM's own ``gen_by_fuel`` feed.
4. **Localising the gas gap** - monthly EIA-930 gas minus the bench members' monthly
   EIA-923 gas (``e_mon``), and an hourly within-month (month fixed effects) regression
   of (930 gas - bench CAMPD gas, rescaled to 923) on each top-10 riser's CAMPD hourly:
   a coefficient near -1 means that plant's output is absent from 930 gas, near 0 that
   it is present.

Writes ``results/phase0/pjm/_pjmnext20_ua_census.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext20_ua_census.py``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "scripts"), str(REPO / "scripts" / "probes")):
    if p not in sys.path:
        sys.path.insert(0, p)

import _pjmnext16_cc_loading as P  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext20_ua_census.json"
BOUNDARY = REPO / "results/phase0/pjm/_pjmnext16_fleet_boundary.json"
F923 = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
TIES = REPO / "data/raw/iso-specific-transmission"
E860 = REPO / "data/raw/eia-860"
XCHG = REPO / "data/raw/eia-930-interchange/PJM interchange hourly.parquet"
METERED = REPO / "data/raw/zone-specific-demand"
GBF = REPO / "data/raw/ISO-specific-gen-data"
GAS_GROUPS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
YEARS = P.YEARS
T = 8760
FUELS = ("gas", "coal", "nuclear", "wind", "solar", "hydro", "oil", "other")
# EIA-930 fuel columns; from 2024-07 EIA splits hydro / pumped storage, solar and wind
# with/without batteries, battery and other storage, geothermal (a FORM change, part 3).
E930_COL = {
    "gas": ("Natural Gas",),
    "coal": ("Coal",),
    "nuclear": ("Nuclear",),
    "wind": (
        "Wind",
        "Wind without Integrated Battery Storage",
        "Wind with Integrated Battery Storage",
    ),
    "solar": (
        "Solar",
        "Solar without Integrated Battery Storage",
        "Solar witho Integrated Battery Storage",
    ),
    "hydro": ("Hydropower and Pumped Storage", "Hydropower Excluding Pumped Storage"),
    "pumped_storage": ("Pumped Storage ",),
    "oil": ("All Petroleum Products",),
    "other": ("Other Fuel Sources", "Geothermal"),
    "storage": (
        "Battery Storage",
        "Other Energy Storage",
        "Unknown Energy Storage",
    ),
    "unknown": ("Unknown Fuel Sources",),
}
# Zero-filled (a blank is "none reported"), and folded for the fuel census:
# pumped storage -> hydro (the pre-2024-07 basis), storage -> other.
ZERO_FILL = ("unknown", "pumped_storage", "storage")
FOLD = {"pumped_storage": "hydro", "storage": "other"}
CLASS_FUEL = {
    "CC_CHP": "gas",
    "CC_REGULAR": "gas",
    "CT_CHP": "gas",
    "CT_PEAKER": "gas",
    "ST_CHP": "gas",
    "ST_GAS": "gas",
    "COAL_BIT": "coal",
    "COAL_PRB": "coal",
    "COAL_WC": "coal",
    "COAL_LIGNITE": "coal",
    "nuclear": "nuclear",
    "wind": "wind",
    "solar": "solar",
    "hydro": "hydro",
    "oil": "oil",
    "OTHER_FOSSIL": "other",
    "OTHER": "other",
    "biomass": "other",
}
F923_FUEL = {
    **dict.fromkeys(("NG", "OG", "BFG", "PG"), "gas"),
    **dict.fromkeys(("BIT", "SUB", "LIG", "RC", "WC", "ANT", "SGC"), "coal"),
    "NUC": "nuclear",
    "WND": "wind",
    "SUN": "solar",
    "WAT": "hydro",
    **dict.fromkeys(("DFO", "RFO", "KER", "JF", "PC", "WO"), "oil"),
}
GAS_CODES = ("NG", "OG", "BFG")


def _e930_fuel(year: int) -> pd.DataFrame:
    """PJM BA hourly EIA-930 (adjusted) on NEXT-16's ``_e930`` time axis, every fuel.

    Columns: demand, interchange, net_gen, each ``E930_COL`` key, and the raw count of
    the split-era columns present (``split_form``) so the 2024-07 form change is visible.
    """
    fr = []
    for f in sorted(P.E930.glob(f"EIA930_BALANCE_{year}_*.parquet")):
        d = pd.read_parquet(f)
        d = d[d["Balancing Authority"] == "PJM"]
        x = pd.DataFrame({"ts": d["UTC Time at End of Hour"].values})
        x["demand"] = pd.to_numeric(d["Demand (MW) (Adjusted)"], errors="coerce").values
        x["interchange"] = pd.to_numeric(
            d["Total Interchange (MW) (Adjusted)"], errors="coerce"
        ).values
        x["net_gen"] = pd.to_numeric(
            d["Net Generation (MW) (Adjusted)"], errors="coerce"
        ).values
        for k, names in E930_COL.items():
            cols = [
                c
                for n in names
                if (c := f"Net Generation (MW) from {n} (Adjusted)") in d.columns
                or (c := f"Net Generation (MW) from {n}(Adjusted)") in d.columns
            ]
            v = d[cols].apply(pd.to_numeric, errors="coerce") if cols else None
            x[k] = v.sum(axis=1, min_count=1).values if v is not None else 0.0
        x["split_form"] = float("Battery Storage" in " ".join(d.columns))
        fr.append(x)
    d = pd.concat(fr)
    d["ts"] = pd.to_datetime(d["ts"], format="%m/%d/%Y %I:%M:%S %p") - pd.Timedelta(
        hours=5
    )
    d = d.sort_values("ts").drop_duplicates("ts")
    d = d[d["ts"] > pd.Timestamp(f"{year}-01-01")].drop(columns="ts")
    d = d.reset_index(drop=True)
    for k in ZERO_FILL:
        d[k] = d[k].fillna(0.0)
    d = d.interpolate(limit_direction="both").iloc[:T].reset_index(drop=True)
    return d.reindex(range(T)).ffill()


def _bench(y: int) -> dict:
    """The C1 bench payload for ``y``."""
    return json.load(gzip.open(P.BENCH / f"{y}.json.gz"))["bench"]


def _ba_map(y: int | None) -> pd.Series:
    """EIA-860 plant -> BA code from the ``y`` vintage (``None`` = current file)."""
    d = E860 if y is None or y > 2024 else E860 / f"vintage_{y}"
    p = pd.read_parquet(d / "eia860_plant.parquet")
    return p.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]


def _first_gas_year() -> pd.Series:
    """First operating year of each plant's gas CC/CT generators (current EIA-860)."""
    g = pd.read_parquet(E860 / "eia860_generators.parquet")
    g = g[
        g.energy_source.isin(GAS_CODES) & g.prime_mover.isin(("CT", "CA", "CS", "GT"))
    ]
    return g.groupby("plant_id").operating_year.min()


def fuel_census(g923: pd.DataFrame, members: dict[int, frozenset]) -> dict:
    """Per year: 930 by fuel, classFull by fuel, member 923 by fuel, and the U_a split."""
    ua = json.loads(BOUNDARY.read_text())["years"]
    out = {}
    for y in YEARS:
        a = _e930_fuel(y)
        raw = {k: float(a[k].sum()) / 1e6 for k in E930_COL}
        e930 = {k: v for k, v in raw.items() if k not in FOLD}
        for k, tgt in FOLD.items():
            e930[tgt] += raw[k]
        cf: dict[str, float] = dict.fromkeys(FUELS, 0.0)
        unmapped = {}
        for k, v in _bench(y)["classFull"].items():
            if k in CLASS_FUEL:
                cf[CLASS_FUEL[k]] += float(v)
            else:
                unmapped[k] = float(v)
        gy = g923[(g923.year == y) & g923.plant_id.isin(members[y])]
        r923 = (
            gy.groupby(
                gy.fuel_type.map(F923_FUEL).fillna("other")
            ).net_generation_mwh.sum()
            / 1e6
        )
        tie = pd.read_csv(TIES / f"PJM_{y}_import_export_act_sch_interchange.csv")
        x_tie = float(-tie.actual_flow.sum()) / 1e6
        d930, ti930 = float(a.demand.sum()) / 1e6, float(a.interchange.sum()) / 1e6
        ng930 = float(a.net_gen.sum()) / 1e6
        cf_tot = sum(cf.values()) + sum(unmapped.values())
        gap = {f: e930[f] - cf[f] for f in FUELS}
        split = {
            **{f"930_minus_classFull_{f}": gap[f] for f in FUELS},
            "930_unknown": e930["unknown"],
            "classFull_unmapped": -sum(unmapped.values()),
            "fuel_sum_vs_930_netgen": sum(e930[f] for f in (*FUELS, "unknown")) - ng930,
            "tie_export_minus_930_TI": x_tie - ti930,
            "930_D_plus_TI_minus_NG": d930 + ti930 - ng930,
        }
        out[str(y)] = {
            "e930": {k: round(v, 2) for k, v in e930.items()},
            "e930_unfolded": {k: round(v, 2) for k, v in raw.items()},
            "e930_split_form_hours": int(a.split_form.sum()),
            "e930_demand": round(d930, 2),
            "e930_total_interchange": round(ti930, 2),
            "e930_net_gen": round(ng930, 2),
            "tie_export": round(x_tie, 2),
            "classFull_by_fuel": {k: round(v, 2) for k, v in cf.items()},
            "classFull_unmapped": {k: round(v, 2) for k, v in unmapped.items()},
            "member923_by_fuel": {k: round(float(v), 2) for k, v in r923.items()},
            "e930_minus_member923": {
                f: round(e930[f] - float(r923.get(f, 0.0)), 2) for f in FUELS
            },
            "U_a_recomputed": round(d930 + x_tie - cf_tot, 2),
            "U_a_next16": ua[str(y)]["U_a"],
            "U_a_split": {k: round(v, 2) for k, v in split.items()},
            "U_a_split_sum": round(sum(split.values()), 2),
        }
    return out


def gas_plants(g923: pd.DataFrame, members: dict[int, frozenset]) -> dict:
    """Member gas 2023 -> 2024 risers, member gas by BA, and PJM-BA non-member gas."""
    gas = g923[g923.fuel_type.isin(GAS_CODES)]
    by = (
        gas.pivot_table(
            index="plant_id", columns="year", values="net_generation_mwh", aggfunc="sum"
        ).fillna(0.0)
        / 1e6
    )
    zone: dict[int, str] = {}
    for y in YEARS:
        for k, p in _bench(y)["plants"].items():
            zone.setdefault(int(str(k).split(":")[0]), p.get("zone"))
    names = (
        pd.read_parquet(E860 / "eia860_plant.parquet")
        .drop_duplicates("Plant Code")
        .set_index("Plant Code")["Plant Name"]
    )
    ba_now, ba23, ba24 = _ba_map(None), _ba_map(2023), _ba_map(2024)
    cod = _first_gas_year()
    m23_24 = members[2023] | members[2024]
    d = (by[2024] - by[2023]).reindex(sorted(m23_24)).dropna().sort_values()
    top = []
    for pid, dv in d[::-1].head(20).items():
        top.append(
            {
                "plant_id": int(pid),
                "name": str(names.get(pid, "?")),
                "twh_2023": round(float(by.loc[pid, 2023]), 2),
                "twh_2024": round(float(by.loc[pid, 2024]), 2),
                "delta": round(float(dv), 2),
                "ba_v2023": str(ba23.get(pid)),
                "ba_v2024": str(ba24.get(pid)),
                "ba_current": str(ba_now.get(pid)),
                "zone": zone.get(int(pid)),
                "member_2023": bool(pid in members[2023]),
                "member_2024": bool(pid in members[2024]),
                "first_cc_ct_year": None if pd.isna(cod.get(pid)) else int(cod[pid]),
            }
        )
    by_ba = {}
    for y in YEARS:
        bay = _ba_map(y)
        s = by[y].reindex(sorted(members[y])).fillna(0.0)
        g = s.groupby(s.index.map(lambda p, b=bay: str(b.get(p, "NA")))).sum()
        by_ba[str(y)] = {k: round(float(v), 2) for k, v in g.items() if abs(v) >= 0.05}
    nonmem = {}
    for y in YEARS:
        bay = _ba_map(y)
        pjm = set(bay[bay == "PJM"].index.astype(int))
        s = by[y].reindex(sorted(pjm - members[y])).fillna(0.0)
        nonmem[str(y)] = {
            "twh": round(float(s.sum()), 2),
            "top": [
                [int(p), str(names.get(p, "?")), round(float(v), 2)]
                for p, v in s.sort_values()[::-1].head(5).items()
                if v > 0.05
            ],
        }
    entr = {}
    for y in (2022, 2023, 2024, 2025):
        pids = [p for p in cod.index if cod[p] == y]
        rows = [
            [
                int(p),
                str(names.get(p, "?")),
                str(ba_now.get(p)),
                {str(k): round(float(by.loc[p, k]), 2) for k in YEARS if p in by.index},
                bool(any(p in members[k] for k in YEARS)),
            ]
            for p in pids
            if str(ba_now.get(p)) == "PJM" or any(p in members[k] for k in YEARS)
        ]
        entr[str(y)] = rows
    return {
        "member_gas_total": {
            str(y): round(float(by[y].reindex(sorted(members[y])).fillna(0).sum()), 2)
            for y in YEARS
        },
        "top20_risers_2023_2024": top,
        "member_gas_by_ba": by_ba,
        "pjm_ba_nonmember_gas": nonmem,
        "new_gas_cc_ct_by_cod": entr,
    }


def boundary_evidence() -> dict:
    """EIA-930 PJM interchange by neighbour BA, and tie-meter legs present, per year."""
    x = pd.read_parquet(XCHG)
    x["year"] = pd.to_datetime(x.local_time).dt.year
    xi = x[x.year.isin(YEARS)].pivot_table(
        index="diba", columns="year", values="mw", aggfunc="sum"
    )
    n = x[x.year.isin(YEARS)].pivot_table(
        index="diba", columns="year", values="mw", aggfunc="count"
    )
    legs = {}
    for y in YEARS:
        t = pd.read_csv(TIES / f"PJM_{y}_import_export_act_sch_interchange.csv")
        legs[str(y)] = {
            str(k): round(float(-v) / 1e6, 2)
            for k, v in t.groupby("tie_line").actual_flow.sum().items()
        }
    return {
        "e930_interchange_twh_by_diba": {
            str(d): {
                str(y): round(float(xi.loc[d, y]) / 1e6, 2)
                for y in YEARS
                if y in xi.columns and pd.notna(xi.loc[d, y])
            }
            for d in xi.index
        },
        "e930_interchange_hours_by_diba": {
            str(d): {
                str(y): int(n.loc[d, y])
                for y in YEARS
                if y in n.columns and pd.notna(n.loc[d, y])
            }
            for d in n.index
        },
        "tie_meter_export_twh_by_leg": legs,
    }


def pjm_own_feeds() -> dict:
    """EIA-930 demand vs PJM RTO metered load, and 930 fuels vs PJM ``gen_by_fuel`` (TWh)."""
    fmt = "%m/%d/%Y %I:%M:%S %p"
    ld = pd.concat(
        [
            pd.read_csv(
                f,
                usecols=[
                    "datetime_beginning_utc",
                    "datetime_beginning_ept",
                    "load_area",
                    "mw",
                ],
            )
            for f in sorted(METERED.glob("PJM20*_hrl_load_metered.csv"))
        ],
        ignore_index=True,
    )
    ld = ld[ld.load_area == "RTO"].drop_duplicates("datetime_beginning_utc")
    ld_y = pd.to_datetime(ld.datetime_beginning_ept, format=fmt).dt.year
    gb = pd.concat(
        [pd.read_csv(f) for f in sorted(GBF.glob("PJM_20*_gen_by_fuel.csv"))],
        ignore_index=True,
    ).drop_duplicates(["datetime_beginning_utc", "fuel_type"])
    gb["y"] = pd.to_datetime(gb.datetime_beginning_ept, format=fmt).dt.year
    gbf = gb.pivot_table(index="y", columns="fuel_type", values="mw", aggfunc="sum")
    out = {}
    for y in YEARS:
        a = _e930_fuel(y)
        met = float(ld.mw[ld_y == y].sum()) / 1e6
        rec = {
            "e930_demand": round(float(a.demand.sum()) / 1e6, 2),
            "pjm_rto_metered_load": round(met, 2),
            "e930_minus_metered": round(float(a.demand.sum()) / 1e6 - met, 2),
        }
        if y in gbf.index:
            rec["pjm_gen_by_fuel"] = {
                str(k): round(float(v) / 1e6, 2)
                for k, v in gbf.loc[y].items()
                if pd.notna(v)
            }
        out[str(y)] = rec
    return out


def gas_gap_localise(cands: list[int]) -> dict:
    """Monthly 930-minus-923 gas gap, and within-month hourly loadings of ``cands``."""
    out = {}
    for y in (2022, 2023, 2024, 2025):
        a = _e930_fuel(y)
        mon = pd.date_range(f"{y}-01-01 01:00", periods=T, freq="h").month.values
        e_mon = np.zeros(12)
        tot = np.zeros(T)
        c = {k: np.zeros(T) for k in cands}
        for k, p in _bench(y)["plants"].items():
            if p.get("group") not in GAS_GROUPS:
                continue
            e_mon += np.asarray(p.get("e_mon") or np.zeros(12), float) / 1e3
            if not p.get("campd") or str(p.get("nodata")) == "True":
                continue
            v = P._dec(p["campd"], p.get("e_ann") or p.get("c_ann"))[:T]
            tot += v
            if int(str(k).split(":")[0]) in c:
                c[int(str(k).split(":")[0])] += v
        g930 = a.gas.values
        lag = max(range(-8, 9), key=lambda s: np.corrcoef(np.roll(g930, s), tot)[0, 1])
        gap = np.roll(g930, lag) - tot

        def demean(x: np.ndarray) -> np.ndarray:
            """Remove each month's mean (month fixed effects)."""
            return x - pd.Series(x).groupby(mon).transform("mean").values

        cols = [c[k] for k in cands] + [tot - sum(c.values())]
        coef = np.linalg.lstsq(
            np.column_stack([demean(x) for x in cols]), demean(gap), rcond=None
        )[0]
        m930 = pd.Series(g930).groupby(mon).sum().values / 1e6
        out[str(y)] = {
            "monthly_930_minus_923_gas": [round(float(v), 2) for v in m930 - e_mon],
            "hourly_lag_h": int(lag),
            "within_month_coef": {
                **{str(k): round(float(b), 2) for k, b in zip(cands, coef)},
                "rest_of_gas_fleet": round(float(coef[-1]), 2),
            },
        }
    return out


def main() -> None:
    """Run the three censuses; print the headline and write the JSON artifact."""
    import run_calibration_full as R

    g923 = pd.read_csv(F923, low_memory=False)
    members = {y: frozenset(R._iso_plant_ids("PJM", y, True)) for y in YEARS}
    res = {
        "what": "PJM-NEXT-20 U_a census: 930 vs benchmark by fuel. ZERO LP.",
        "fuel_census": fuel_census(g923, members),
        "gas_plants": gas_plants(g923, members),
        "boundary": boundary_evidence(),
        "pjm_own_feeds": pjm_own_feeds(),
    }
    cands = [r["plant_id"] for r in res["gas_plants"]["top20_risers_2023_2024"][:10]]
    res["gas_gap_localise"] = gas_gap_localise(cands)
    fc = res["fuel_census"]
    res["delta_2023_2024"] = {
        k: round(fc["2024"]["U_a_split"][k] - fc["2023"]["U_a_split"][k], 2)
        for k in fc["2023"]["U_a_split"]
    }
    OUT.write_text(json.dumps(res, indent=1))
    for y, r in fc.items():
        print(y, r["U_a_recomputed"], r["U_a_next16"], r["U_a_split"])
    print("delta", res["delta_2023_2024"])
    for y, r in res["gas_gap_localise"].items():
        print(y, r["within_month_coef"])


if __name__ == "__main__":
    main()
