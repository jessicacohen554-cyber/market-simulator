"""nwpp-50 phase 0: can the NWPP-36 side-inflow gate be repaired from measurement? ZERO LP.

Reproduces every number in ``docs/handoffs/FINDING-nwpp-50-2026-09-24.md`` from
committed artifacts only:

* ``data/raw/nwpp-hydro/crohms/nwpp_crohms_hourly.parquet`` (NWPP-36's CROHMS pull),
  read through ``scripts/data/build_nwpp_hydro_cascade.py``'s own loader and constants,
  so the sentinel screens and the side-inflow balance are the gate's, not a copy;
* ``data/raw/nwpp-hydro/nwpp_hydro_cascade_links.csv`` (τ, NID area, pond band);
* ``data/raw/nwpp-hydro/usgs/nwpp_usgs_daily_discharge.csv`` (this lane's intake:
  independent USGS mainstem and tributary gauges);
* the keeper's committed ``hourly/hydro_cascade_<y>.parquet``
  (``results/calibration/nwpp49_ror_span``).

Four tests:

1. **Identity.** Does ``Flow-Out = Flow-Gen + Flow-Spill``? Any remainder is
   non-power, non-spill outflow (fish passage, locks).
2. **The gate under two bases.** The 2 % floor is applied verbatim (threshold untouched)
   to the side-inflow balance built from ``Flow-Out`` (NWPP-36, reproduced) and from
   ``Flow-Gen + Flow-Spill`` (NWPP-36 §7 item 1(a)).
3. **Tributary closure.** Downstream outflow minus upstream outflow minus the gauged
   tributaries between them, monthly, split into spill and no-spill months. A pure
   spill-metering artefact would vanish in months with no spill.
4. **Keeper row slack.** For each already-coupled plant: hours with a non-zero row dual,
   and hours the pond sits at 0 or at B.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp50_sideinflow_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import build_nwpp_hydro_cascade as bc  # noqa: E402  (the gate's own loader)

HYDRO = Path("data/raw/nwpp-hydro")
USGS = HYDRO / "usgs" / "nwpp_usgs_daily_discharge.csv"
KEEPER = Path("results/calibration/nwpp49_ror_span")
YEARS = (2023, 2024, 2025)
OUT = Path("results/calibration/_nwpp50_sideinflow_phase0.json")
# A month counts as "no spill" when the downstream project's monthly-mean metered
# spill is below 1 kcfs. That is under 1 % of every lower-river project's mean
# outflow (38.7-144.1 kcfs), i.e. spill is below the gate's own 2 % resolution.
NO_SPILL_KCFS = 1.0
# The seven links NWPP-36 STOPPED on the side-inflow floor (FINDING-nwpp-36 §3.5).
SIDE_STOP_D = ("RRH", "PRD", "MCN", "JDA", "TDA", "LGS", "LMN")
# Tributaries entering each pool between the upstream and downstream dams (USGS site_no).
# Umatilla and John Day enter the John Day pool; Yakima and Walla Walla enter the
# McNary pool; the Deschutes enters the Celilo pool above The Dalles Dam.
TRIBS = {
    "TDA": (("JDA",), ("14103000",)),
    "JDA": (("MCN",), ("14048000", "14033500")),
    "MCN": (("PRD", "IHR"), ("12510500", "14018500")),
}
MAINSTEM_GAUGE = {"TDA": "14105700", "PRD": "12472800"}


def _flow(h: dict[str, pd.DataFrame], st: str, basis: str) -> pd.Series:
    """Hourly flow at ``st`` on ``basis`` (``out`` or ``gen+spill``), kcfs."""
    df = h[st]
    if basis == "out":
        return df[bc.S_OUT]
    return df[bc.S_GEN] + df[bc.S_SPILL]


def identity(h: dict[str, pd.DataFrame]) -> dict:
    """Mean of Flow-Out - Flow-Gen - Flow-Spill per station, kcfs and % of outflow."""
    out = {}
    for st, df in h.items():
        r = (df[bc.S_OUT] - df[bc.S_GEN] - df[bc.S_SPILL]).dropna()
        out[st] = dict(
            other_kcfs=round(float(r.mean()), 3),
            other_pct_of_out=round(float(100 * r.mean() / df[bc.S_OUT].mean()), 2),
        )
    return out


def gate_counts(h: dict[str, pd.DataFrame], links: pd.DataFrame, basis: str) -> dict:
    """Plant-months over the 2 % floor per downstream station, on ``basis``."""
    area = links.drop_duplicates("d_station").set_index("d_station")["area_acres"]
    up: dict[str, list[tuple[str, int]]] = {}
    for r in links.itertuples():
        up.setdefault(r.d_station, []).append((r.u_station, int(r.tau_h)))
    res = {}
    for d, us in up.items():
        df = h[d]
        dv = df[bc.S_FB].diff() * area[d] / bc.ACRE_FT_PER_KCFS_H
        arr = sum(_flow(h, u, basis).shift(t) for u, t in us)
        bal = _flow(h, d, basis) + dv - arr
        ok = bal.notna()
        g = pd.DataFrame({"bal": bal[ok], "arr": arr[ok]})
        g = g[g.index < "2026-01-01"]
        m = g.resample("MS").mean()
        floor = (-m["bal"]).clip(lower=0)
        res[d] = dict(
            stop_months=int((floor > bc.SIDE_INFLOW_FLOOR_MAX_FRAC * m["arr"]).sum()),
            max_floor_pct=round(float((floor / m["arr"]).max() * 100), 1),
        )
    return res


def tributary_closure(h: dict[str, pd.DataFrame]) -> dict:
    """Monthly closure, % of upstream outflow, split into spill / no-spill months."""
    q = pd.read_csv(USGS, dtype={"site_no": str}, parse_dates=["date"])
    q = q.pivot(index="date", columns="site_no", values="discharge_cfs") / 1000.0
    qm = q.resample("MS").mean()
    res = {}
    for d, (ups, tribs) in TRIBS.items():
        dm = h[d][bc.S_OUT].resample("MS").mean()
        spill = h[d][bc.S_SPILL].resample("MS").mean()
        um = sum(h[u][bc.S_OUT].resample("MS").mean() for u in ups)
        tm = sum(qm[s] for s in tribs)
        cl = ((dm - um - tm) / um * 100).dropna()
        cl = cl[cl.index < "2026-01-01"]
        sp = spill.reindex(cl.index)
        dry, wet = cl[sp < NO_SPILL_KCFS], cl[sp >= NO_SPILL_KCFS]
        res[f"{'+'.join(ups)}->{d}"] = dict(
            no_spill_months=int(len(dry)),
            no_spill_mean_pct=round(float(dry.mean()), 2) if len(dry) else None,
            no_spill_range_pct=[round(float(dry.min()), 2), round(float(dry.max()), 2)]
            if len(dry)
            else None,
            spill_months=int(len(wet)),
            spill_mean_pct=round(float(wet.mean()), 2),
            spill_range_pct=[round(float(wet.min()), 2), round(float(wet.max()), 2)],
        )
    for d, s in MAINSTEM_GAUGE.items():
        ratio = (h[d][bc.S_OUT].resample("MS").mean() / qm[s]).dropna()
        ratio = ratio[ratio.index < "2026-01-01"]
        res[f"{d}_out_over_usgs_{s}"] = dict(
            min=round(float(ratio.min()), 3),
            max=round(float(ratio.max()), 3),
            months_outside_2pct=int(((ratio - 1).abs() > 0.02).sum()),
            months=int(len(ratio)),
        )
    return res


def keeper_row_slack(links: pd.DataFrame) -> dict:
    """Per coupled plant-year: hours with |row dual| > $1, pond at 0 / at B, mean spill."""
    b = links.drop_duplicates("d_plant_id").set_index("d_plant_id")
    res = {}
    for y in YEARS:
        df = pd.read_parquet(KEEPER / "hourly" / f"hydro_cascade_{y}.parquet")
        for pid, g in df.groupby("plant_code"):
            cap = float(b.loc[pid, "pond_kcfsh"])
            v, w = g["pond_kcfsh"].to_numpy(), g["water_value"].to_numpy()
            res[f"{y}_{b.loc[pid, 'd_station']}"] = dict(
                hours_dual_gt_1=int((np.abs(w) > 1.0).sum()),
                hours_pond_at_0=int((v < 1e-3 * cap).sum()),
                hours_pond_at_B=int((v > cap * (1 - 1e-3)).sum()),
                spill_mean_kcfs=round(float(g["spill_kcfs"].mean()), 1),
            )
    return res


def pond_hours(links: pd.DataFrame) -> dict:
    """Pond band in hours of measured mean outflow, per downstream station."""
    b = links.drop_duplicates("d_station").set_index("d_station")
    return {
        st: dict(
            hours=round(float(b.loc[st, "pond_hours_of_measured_avg_outflow"]), 2),
            coupled=bool(b.loc[st, "coupled"]),
        )
        for st in b.index
    }


def main() -> int:
    """Run the four tests and write the probe record."""
    h = bc.load_hourly()
    links = pd.read_csv(HYDRO / "nwpp_hydro_cascade_links.csv")
    rec = dict(
        identity_out_minus_gen_minus_spill=identity(h),
        gate_out_basis=gate_counts(h, links, "out"),
        gate_gen_plus_spill_basis=gate_counts(h, links, "gen+spill"),
        tributary_closure=tributary_closure(h),
        keeper_row_slack=keeper_row_slack(links),
        pond_hours_of_measured_avg_outflow=pond_hours(links),
    )
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    for k in ("gate_out_basis", "gate_gen_plus_spill_basis"):
        print(k, {d: rec[k][d]["stop_months"] for d in SIDE_STOP_D})
    print(json.dumps(rec["tributary_closure"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
