"""NWPP-NEXT-4 phase 0: unit-level coal swing census against CAMPD. ZERO LP.

For every NWPP coal plant and year, compares keeper #10's per-band P1 dispatch
(``hourly/unit_hourly_<y>.parquet`` of the seven ``nwppnext3_<y>`` shard legs)
with the plant's CAMPD hourly gross load, and classifies WHY the model plant is
flat: how much of its dispatch sits in fuel-cheap blocks (``_mustrun`` +
``_committed``) that run in every hour, how often each band is pinned at its
available cap / at zero / partially loaded, and the plant's intra-day and
daily-mean swing, model against measured.

The shard legs are not on ``main`` (rule 32(d)); they are read from the leg
commits named in RESULT-nwppnext3 §4 (provenance only, rule 33(d)) into
``--legs`` with ``git archive <sha> results/calibration/nwppnext3_<y>``.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwppnext4_coal_census.py --legs DIR [--json OUT]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
CAMPD = Path("data/raw/campd-unit-level")
STATES = ("WY", "UT", "MT", "NV", "WA")
N = 8760
CHEAP = ("mustrun", "committed")


def _split_sd(x: np.ndarray) -> tuple[float, float]:
    """Return (sd of daily means, mean within-day sd) of an hourly vector."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    return float(x.mean(1).std()), float(x.std(1).mean())


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, NaN when either vector is constant."""
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def campd_plant_hourly(year: int) -> dict[int, np.ndarray]:
    """CAMPD coal-unit gross load summed per facility onto an 8760 vector."""
    out: dict[int, np.ndarray] = {}
    for st in STATES:
        f = CAMPD / f"{st}_{year}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f, columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo"]
        )
        d = d[d.primaryFuelInfo.fillna("").str.contains("Coal")]
        how = (d.date - pd.Timestamp(year, 1, 1)).dt.days * 24 + d.hour
        d = d.assign(h=how.to_numpy(), g=d.grossLoad.fillna(0.0))
        for fid, g in d.groupby("facilityId"):
            v = g.groupby("h").g.sum().reindex(range(N), fill_value=0.0).to_numpy(float)
            out[int(fid)] = v
    return out


def census(legs: Path) -> dict:
    """Per plant-year census of band pinning and swing, model vs CAMPD."""
    rec: dict = {}
    for y in YEARS:
        u = pd.read_parquet(
            legs / f"results/calibration/nwppnext3_{y}/hourly/unit_hourly_{y}.parquet",
            columns=[
                "unit_id",
                "plant_code",
                "plant_group",
                "hour",
                "mw",
                "cap_mw",
                "mc",
            ],
        )
        u = u[u.plant_group.astype(str).str.startswith("COAL")]
        u = u.assign(band=u.unit_id.astype(str).str.rsplit("_", n=1).str[-1])
        cp = campd_plant_hourly(y)
        yr: dict = {}
        for pc, g in u.groupby("plant_code"):
            tot = (
                g.groupby("hour")
                .mw.sum()
                .reindex(range(N), fill_value=0)
                .to_numpy(float)
            )
            if tot.sum() < 0.2e6:
                continue
            bands = {}
            for b, gb in g.groupby("band"):
                hb = (
                    gb.groupby("hour")[["mw", "cap_mw"]]
                    .sum()
                    .reindex(range(N), fill_value=0)
                )
                mw = hb.mw.to_numpy(float)
                cap = hb.cap_mw.to_numpy(float)
                on = cap > 0.5
                at_cap = on & (mw >= cap - 0.5)
                at_zero = on & (mw <= 0.5)
                bands[b] = {
                    "twh": round(mw.sum() / 1e6, 3),
                    "cap_mean_mw": round(float(cap.mean()), 1),
                    "mc_mean": round(float(gb.mc.mean()), 2),
                    "h_avail": int(on.sum()),
                    "h_at_cap": int(at_cap.sum()),
                    "h_at_zero": int(at_zero.sum()),
                    "h_partial": int((on & ~at_cap & ~at_zero).sum()),
                }
            cheap_twh = sum(v["twh"] for b, v in bands.items() if b in CHEAP)
            m_d, m_i = _split_sd(tot)
            row = {
                "model_twh": round(tot.sum() / 1e6, 3),
                "cheap_share": round(cheap_twh / max(tot.sum() / 1e6, 1e-9), 3),
                "cheap_cap_mw": round(
                    sum(v["cap_mean_mw"] for b, v in bands.items() if b in CHEAP), 1
                ),
                "model_sd_daily": round(m_d, 1),
                "model_sd_intra": round(m_i, 1),
                "model_p05": round(float(np.percentile(tot, 5)), 1),
                "bands": bands,
            }
            a = cp.get(int(pc))
            if a is not None and a.sum() > 0:
                a_d, a_i = _split_sd(a)
                run = a[a > 0]
                row.update(
                    campd_twh=round(a.sum() / 1e6, 3),
                    campd_sd_daily=round(a_d, 1),
                    campd_sd_intra=round(a_i, 1),
                    campd_p05=round(float(np.percentile(a, 5)), 1),
                    campd_p10_running=round(float(np.percentile(run, 10)), 1),
                    campd_max=round(float(a.max()), 1),
                    r_hourly=round(_r(tot, a), 3),
                )
            yr[int(pc)] = row
        rec[y] = yr
    return rec


TRANCHES = Path("data/raw/_processed-legacy/thermal_tranches_NWPP.csv")
EIA930 = Path("results/calibration/_shared/NWPP/eia930-6da961d2d14a.parquet")


def nested_prediction(legs: Path) -> dict:
    """Zero-LP, price-taker prediction of the nested committed band.

    For each coal plant with a measured ``thermal_tranches_NWPP.csv`` COAL row
    the committed band shrinks from ``committed_pct`` to
    ``max(0, committed_pct - mustrun_pct)`` of nameplate; the removed MW
    (``min(committed, mustrun) / committed`` of the band's hourly cap) moves to
    the econ bands at the plant's econ offer. In an hour where the plant's econ
    band clears (reduced cost <= 0) the plant's output is unchanged; otherwise
    the committed MW above the new cap is lost. Fleet coal r against EIA-930 is
    reported for the keeper (``base``) and this full-loss bound (``arm``); the
    truth under price feedback lies between the two.
    """
    t = pd.read_csv(TRANCHES)
    t = t[(t.plant_group == "COAL") & (t.status == "ok")]
    frac = {
        int(r.plant_code): (min(r.committed_pct, r.mustrun_pct) / r.committed_pct)
        for r in t.itertuples()
        if r.committed_pct > 0
    }
    e = pd.read_parquet(EIA930)
    out: dict = {}
    for y in YEARS:
        u = pd.read_parquet(
            legs / f"results/calibration/nwppnext3_{y}/hourly/unit_hourly_{y}.parquet",
            columns=[
                "unit_id",
                "plant_code",
                "plant_group",
                "hour",
                "mw",
                "cap_mw",
                "red_cost",
            ],
        )
        u = u[u.plant_group.astype(str).str.startswith("COAL")]
        u = u.assign(band=u.unit_id.astype(str).str.rsplit("_", n=1).str[-1])
        base = (
            u.groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy(float)
        )
        loss = np.zeros(N)
        for pc, f in frac.items():
            g = u[u.plant_code == pc]
            c = g[g.band == "committed"].groupby("hour")[["mw", "cap_mw"]].sum()
            c = c.reindex(range(N), fill_value=0)
            ec = g[g.band.str.startswith("econ")].groupby("hour").red_cost.min()
            ec = ec.reindex(range(N), fill_value=np.inf).to_numpy(float)
            new_cap = c.cap_mw.to_numpy(float) * (1.0 - f)
            lost = np.maximum(c.mw.to_numpy(float) - new_cap, 0.0)
            loss += np.where(ec <= 1e-6, 0.0, lost)
        arm = base - loss
        a = (
            e[(e.year == y) & (e.series == "coal")]
            .sort_values("hour")
            .mw.to_numpy(float)[:N]
        )
        bd, bi = _split_sd(base)
        ad, ai = _split_sd(arm)
        xd, xi = _split_sd(a)
        out[y] = {
            "r_base": round(_r(base, a), 3),
            "r_arm_full_loss": round(_r(arm, a), 3),
            "r_arm_half_loss": round(_r(base - 0.5 * loss, a), 3),
            "coal_twh_base": round(base.sum() / 1e6, 3),
            "coal_twh_lost_full": round(loss.sum() / 1e6, 3),
            "eia930_coal_twh": round(a.sum() / 1e6, 3),
            "sd_intra_base_arm_actual": [round(bi), round(ai), round(xi)],
            "sd_daily_base_arm_actual": [round(bd), round(ad), round(xd)],
            "hours_with_loss": int((loss > 0.5).sum()),
        }
        print(y, out[y])
    return out


def main() -> None:
    """Print the census table and optionally dump it to JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    rec = census(a.legs)
    for y, yr in rec.items():
        print(f"\n== {y}")
        print(
            f"{'plant':>6} {'mTWh':>6} {'cTWh':>6} {'cheapMW':>7} {'cheap%':>6} "
            f"{'m_sdI':>6} {'c_sdI':>6} {'m_sdD':>6} {'c_sdD':>6} {'m_p05':>6} {'c_p10r':>6} {'r':>6}"
        )
        for pc, r in sorted(yr.items(), key=lambda kv: -kv[1]["model_twh"]):
            print(
                f"{pc:>6} {r['model_twh']:6.2f} {r.get('campd_twh', float('nan')):6.2f} "
                f"{r['cheap_cap_mw']:7.0f} {r['cheap_share']:6.2f} {r['model_sd_intra']:6.0f} "
                f"{r.get('campd_sd_intra', float('nan')):6.0f} {r['model_sd_daily']:6.0f} "
                f"{r.get('campd_sd_daily', float('nan')):6.0f} {r['model_p05']:6.0f} "
                f"{r.get('campd_p10_running', float('nan')):6.0f} {r.get('r_hourly', float('nan')):6.2f}"
            )
    pred = nested_prediction(a.legs)
    if a.json:
        a.json.write_text(
            json.dumps({"census": rec, "nested_prediction": pred}, indent=1)
        )


if __name__ == "__main__":
    main()
