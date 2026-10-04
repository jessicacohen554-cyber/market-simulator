"""Close-out CAISO w5, phase 0 (ZERO LP): why CC_REGULAR over-runs while CT_PEAKER / ST_GAS under-run, every year.

Control: the w3 probe legs ``results/calibration/closeout_caiso_w3_a1_<y>`` (P1
``unit_marginal`` per-unit mw / cap_mw / offer mc / marginal flag, ``system``
zonal duals, ``floors/<y>_P1.npz``) and the span's pinned shared frames (EIA-923
plant-month by class, CAMPD hourly net MW).

Actual per plant = the EIA-923 monthly record levelled on the plant's CEMS
hourly shape (flat where CEMS is empty), the closeout-caiso-2 construction.

Per year and class:

* model vs actual TWh;
* the MISSED energy: plant-hours the plant ran in reality (actual > 1 MW) above
  its model output, split by the plant's P1 state in that hour —
  ``off_priced``   all its units below cap and its cheapest available offer > lambda;
  ``cap_limited``  every unit at its P1 capability (cap_mw) (availability/derate/outage);
  ``not_in_lp``    the plant has no LP unit that year;
  ``cheap_unused`` an offer <= lambda with headroom (should not happen in an LP —
                   a floor/ramp/coupling artefact or a dual tolerance);
  and the offer gap (offer - lambda) distribution in ``off_priced``;
* the EXCESS energy (model above actual) for CC_REGULAR, split into energy at a
  binding floor (P1 floors, by mechanism code) and economic.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w5_intragas_census.py [--years ...] [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]

ROOT = Path(__file__).resolve().parents[2]
SPAN = ROOT / "results/calibration/closeout_caiso_w3_a1_span"
LEG = ROOT / "results/calibration/closeout_caiso_w3_a1_{y}"
T = 8760
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
MCOLS = [f"m{i:02d}" for i in range(1, 13)]
CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
ON_MW = 1.0


def _shared(prefix: str) -> pd.DataFrame:
    meta = json.loads((SPAN / "meta.json").read_text())
    return pd.read_parquet(SPAN / meta["shared_inputs"][prefix])


def _levelled(campd: np.ndarray, e_mon: np.ndarray) -> np.ndarray:
    out = np.zeros(T)
    for m in range(1, 13):
        k = MONTH == m
        c = np.clip(campd[k], 0, None)
        out[k] = c * (e_mon[m - 1] / c.sum()) if c.sum() > 0 else e_mon[m - 1] / k.sum()
    return out


def census_year(year: int, e923: pd.DataFrame, campd: pd.DataFrame) -> dict:
    """Census of one year."""
    leg = Path(LEG.as_posix().format(y=year))
    um = pd.read_parquet(
        leg / f"hourly/unit_marginal_{year}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    um["plant_group"] = um.plant_group.astype(str)
    um["zone"] = um.zone.astype(str)
    sysh = pd.read_parquet(leg / f"hourly/system_{year}.parquet")
    sysh = sysh[sysh["pass"] == "P1"]
    lam = {
        z: g.set_index("hour").price.reindex(range(T)).to_numpy(float)
        for z, g in sysh.groupby("zone")
    }
    ey = e923[e923.year == year]
    cy = campd[campd.year == year]
    cmap = {
        int(p): g.set_index("hour").net_mw.reindex(range(T)).fillna(0).to_numpy(float)
        for p, g in cy.groupby("plant_id")
    }
    fl = np.load(leg / f"floors/{year}_P1.npz", allow_pickle=True)
    fl_ids = np.asarray(fl["unit_ids"]).astype(str)
    fl_row = {u: i for i, u in enumerate(fl_ids)}

    out = {}
    for klass in CLASSES:
        e = ey[ey.klass == klass].groupby("plant_id")[MCOLS].sum()
        sub = um[um.plant_group == klass]
        plants = sorted(set(e.index.astype(int)) | set(sub.plant_code.astype(int)))
        by_plant = {int(p): g for p, g in sub.groupby("plant_code")}
        tot_m = tot_a = 0.0
        miss = {
            "off_priced": 0.0,
            "cap_limited": 0.0,
            "not_in_lp": 0.0,
            "cheap_unused": 0.0,
        }
        gaps, gap_w = [], []
        excess_floor = {}
        excess_total = 0.0
        plant_rows = []
        for p in plants:
            act = (
                _levelled(cmap.get(p, np.zeros(T)), e.loc[p].to_numpy(float))
                if p in e.index
                else np.zeros(T)
            )
            g = by_plant.get(p)
            if g is None:
                tot_a += act.sum()
                miss["not_in_lp"] += act.sum()
                plant_rows.append((p, 0.0, act.sum()))
                continue
            mw = (
                g.pivot_table(
                    index="hour", columns="unit_id", values="mw", aggfunc="sum"
                )
                .reindex(range(T))
                .fillna(0)
            )
            cap = (
                g.pivot_table(
                    index="hour", columns="unit_id", values="cap_mw", aggfunc="sum"
                )
                .reindex(range(T))
                .fillna(0)
            )
            mc = g.pivot_table(
                index="hour", columns="unit_id", values="mc", aggfunc="mean"
            ).reindex(range(T))
            zone = g.zone.iat[0]
            lz = lam.get(zone, lam.get("SP15_rest"))
            m_tot = mw.sum(axis=1).to_numpy()
            tot_m += m_tot.sum()
            tot_a += act.sum()
            plant_rows.append((p, m_tot.sum(), act.sum()))
            short = np.clip(act - m_tot, 0, None) * (act > ON_MW)
            head = (cap.to_numpy() - mw.to_numpy()) > 1.0
            avail = cap.to_numpy() > 1.0
            mcv = mc.to_numpy()
            cheapest = np.where(head & avail, mcv, np.inf).min(axis=1)
            all_cap = ~(head & avail).any(axis=1)
            priced = ~all_cap & (cheapest > lz + 0.01)
            cheap = ~all_cap & ~priced
            miss["cap_limited"] += short[all_cap].sum()
            miss["off_priced"] += short[priced].sum()
            miss["cheap_unused"] += short[cheap].sum()
            k = priced & (short > 0)
            gaps.append((cheapest - lz)[k])
            gap_w.append(short[k])
            if klass == "CC_REGULAR":
                exc = np.clip(m_tot - act, 0, None)
                excess_total += exc.sum()
                for u in mw.columns:
                    i = fl_row.get(str(u))
                    if i is None:
                        continue
                    mg = fl["min_gen"][i]
                    mech = fl["mechanism"][i]
                    umw = mw[u].to_numpy()
                    at = (mg > 0) & (umw <= mg + 1.0) & (umw > 0)
                    share = np.where(m_tot > 0, umw / np.maximum(m_tot, 1e-9), 0)
                    for code in np.unique(mech[at]):
                        sel = at & (mech == code)
                        excess_floor[str(code)] = excess_floor.get(
                            str(code), 0.0
                        ) + float((exc * share)[sel].sum())
        gaps = np.concatenate(gaps) if gaps else np.array([])
        gap_w = np.concatenate(gap_w) if gap_w else np.array([])
        row = {
            "model_twh": round(tot_m / 1e6, 3),
            "actual_twh": round(tot_a / 1e6, 3),
            "missed_twh": {k: round(v / 1e6, 3) for k, v in miss.items()},
        }
        if gaps.size:
            o = np.argsort(gaps)
            cw = np.cumsum(gap_w[o]) / gap_w.sum()
            row["off_priced_gap_energy_weighted_p25_p50_p75"] = [
                round(float(gaps[o][np.searchsorted(cw, q)]), 2)
                for q in (0.25, 0.5, 0.75)
            ]
            row["off_priced_twh_gap_le_5"] = round(
                float(gap_w[gaps <= 5].sum() / 1e6), 3
            )
            row["off_priced_twh_gap_le_10"] = round(
                float(gap_w[gaps <= 10].sum() / 1e6), 3
            )
        if klass == "CC_REGULAR":
            row["excess_twh"] = round(excess_total / 1e6, 3)
            row["excess_at_floor_twh_by_mechanism"] = {
                k: round(v / 1e6, 3) for k, v in excess_floor.items()
            }
        pr = sorted(plant_rows, key=lambda r: r[1] - r[2])
        row["top_under_plants"] = [
            {
                "plant": int(p),
                "model_gwh": round(m / 1e3, 1),
                "actual_gwh": round(a / 1e3, 1),
            }
            for p, m, a in pr[:8]
        ]
        out[klass] = row
    return out


def main() -> None:
    """Run the census for the requested years."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
    )
    ap.add_argument(
        "--out",
        default=str(
            ROOT / "docs/records/caiso/closeout-caiso-w5/_intragas_census.json"
        ),
    )
    a = ap.parse_args()
    e923, campd = _shared("eia923"), _shared("campd")
    res = {}
    for y in a.years:
        res[str(y)] = census_year(y, e923, campd)
        print(
            y,
            json.dumps(
                {
                    k: {kk: vv for kk, vv in v.items() if kk != "top_under_plants"}
                    for k, v in res[str(y)].items()
                },
                default=float,
            ),
            flush=True,
        )
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
