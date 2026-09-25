"""soco-67 census (ZERO LP): CAMPD outage windows that overlap a bin's pre-COD months.

The COD ramp (``data.fleet.arrays``, applied LAST) multiplies a plant-bin's
availability by the online-capacity fraction of its EIA-860 constituents
(``cod_ramp.bin_online_fraction``). A CAMPD unit-outage window derived from a
unit's own zero output BEFORE its commercial operation date removes the same
not-yet-built capacity a second time. This lists every SOCO (plant, class,
year) where a keeper-armed outage extract carries a window over a month the COD
ramp already holds below 1.0, with the overlapping capacity.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_soco67_cod_census.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data/raw"
EXTRACTS = (
    "campd-unit-outages-perunitdark-SOCO.csv",
    "campd-unit-outages-short-SOCO.csv",
    "campd-unit-outages-shortgas-SOCO.csv",
    "campd-partial-outages-SOCO.csv",
)
GROUP_FUEL = {"CC_REGULAR": "gas_cc", "CT_PEAKER": "gas_ct", "ST_GAS": "gas_st",
              "CC_CHP": "gas_cc", "CT_CHP": "gas_ct", "ST_CHP": "gas_st"}
YEARS = range(2019, 2026)


def main() -> None:
    """Print and write the census."""
    from market_sim.data.cod_ramp import _load_unit_cod_map, bin_online_fraction

    cods = _load_unit_cod_map(RAW / "eia-860")
    rows = []
    for name in EXTRACTS:
        o = pd.read_csv(RAW / name)
        o["s"] = pd.to_datetime(o.outage_start)
        o["e"] = pd.to_datetime(o.outage_end)
        for r in o.itertuples():
            fuel = GROUP_FUEL.get(r.plant_group, "coal" if str(r.plant_group).startswith("COAL") else None)
            units = cods.get((int(r.facility_id), fuel))
            if not units:
                continue
            for y in YEARS:
                fr = bin_online_fraction(units, y)
                for m in range(1, 13):
                    ms = pd.Timestamp(y, m, 1)
                    me = ms + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
                    ov = (min(r.e, me) - max(r.s, ms)).total_seconds() / 86400
                    if ov <= 0:
                        continue
                    frac = float(fr[m - 1])
                    if frac < 1.0:
                        rows.append({"extract": name, "plant": int(r.facility_id),
                                     "group": r.plant_group, "unit": str(r.unit_id),
                                     "unit_mw": float(r.unit_capacity_mw), "year": y, "month": m,
                                     "overlap_days": round(ov, 2), "cod_online_frac": round(frac, 4)})
    df = pd.DataFrame(rows)
    out = REPO / "results/calibration/_soco67/cod_overlap_census.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        print("NO OVERLAP")
        out.write_text("[]\n")
        return
    df["mwh_double"] = df.unit_mw * df.overlap_days * 24
    g = df.groupby(["extract", "plant", "group", "unit", "year"]).agg(
        months=("month", lambda s: f"{s.min()}-{s.max()}"), days=("overlap_days", "sum"),
        unit_mw=("unit_mw", "first"), frac_min=("cod_online_frac", "min"),
        twh_double=("mwh_double", lambda s: s.sum() / 1e6)).reset_index()
    print(g.round(3).to_string(index=False))
    out.write_text(json.dumps(g.round(4).to_dict(orient="records"), indent=1) + "\n")


if __name__ == "__main__":
    main()
