"""Closeout ERCOT-ECRS (R-39) phase 0: static re-clear of 2023 under the ECRS design.

Zero LP. Reads the keeper bundle's committed 2023 hourlies and the measured
2023 inputs, perturbs the system price by the design's one NEW element, and
scores C3a/C3b with the repo's own scorers (``calibration_verdict``,
``score_bundle_price_shape``). Nothing is solved, written to the bundle, or
registered.

The design (brief R-39 §1c): ECRS awards withheld from energy at the measured
hourly procurement (ALREADY ARMED in the keeper: ``ercot_ecrs_conservative_
deployment`` + ``ercot_multiproduct_as_coopt`` + ASPLANNP433 plan) AND the
online-reserve quantity the ORDC curve sees reduced by the sequestered MW (the
only NEW element), replacing the x33 peak bands.

PRE-FIXED READING (written before computing; committed with this file):
  bar: C3a 2023 moves from -24.7 % ($48.98 vs $65.02) toward the actual by
  >= half the gap (model >= $57.00, C3a >= -12.35 %) AND C3b 2023 <= 0.30.
  Estimates are reported on two reserve bases and two price baselines; the
  x33-band keeper baseline is an UPPER bound (the design removes the bands,
  which only lowers prices). A miss on the upper bound is a miss.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _p in (_ROOT, _ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.results import scarcity as sc  # noqa: E402
from scripts import calibration_verdict as cv  # noqa: E402
from scripts import score_bundle_price_shape as sbp  # noqa: E402

BUNDLE = _ROOT / "results/calibration/closeout_ercot_l1_span"
OUT = _ROOT / "results/phase0/ercot/closeout_ecrs_static_reclear.json"
YEAR = 2023
T = 8760


def published_adder(r_full, r_online, lam, cfg) -> np.ndarray:
    """The keeper's published ORDC adder (R-ERCOT-24b form) on given reserves."""
    mu_s, sigma = sc.ercot_published_mu_sigma_hourly(YEAR, T)
    s = float(cfg["ordc_lolp_shift_sigma"])
    return sc.ordc_adder(
        r_full, lam, voll=float(cfg["ordc_voll"]), mcl_mw=float(cfg["ordc_mcl_mw"]),
        mu_mw=mu_s - s * sigma, sigma_mw=sigma, shift_sigma=s,
        multistep_floor=bool(cfg["ordc_multistep_floor"]),
        floor_active=sc.floor_active_mask(YEAR, T), reserves_online_mw=r_online,
        obd_half_shift=True,
    )


def score(sys_df: pd.DataFrame) -> dict:
    """C3a + C3b with the scorer's own arithmetic on a perturbed system frame."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "hourly").mkdir()
    sys_df.to_parquet(tmp / "hourly" / f"system_{YEAR}.parquet")
    lmp = sbp.zone_lmp_block(tmp, YEAR)
    p1 = sys_df[sys_df["pass"] == "P1"]
    for zone, zg in p1.groupby("zone", observed=True):
        dd = float(zg["demand"].sum())
        if dd <= 0:  # load-less zone (Panhandle): zero weight in the lw mean
            continue
        lmp[str(zone)]["p"] = round(float((zg["price"] * zg["demand"]).sum()) / dd, 2)
        lmp[str(zone)]["d"] = round(dd / 1e6, 4)
    ypay = {"lmp": lmp}
    bench = sbp.bench_year("ERCOT", YEAR)
    a = cv.score_price_mean(YEAR, ypay, bench, "ERCOT")
    b = cv.score_price_shape(YEAR, ypay, bench, "ERCOT")
    shutil.rmtree(tmp)
    return {"C3a": a, "C3b": b}


def main() -> int:
    """Compute the static re-clear and write the phase-0 JSON."""
    cfg = json.loads((BUNDLE / f"run_config_{YEAR}.json").read_text())["scenario_config"]
    sys_all = pd.read_parquet(BUNDLE / "hourly" / f"system_{YEAR}.parquet")
    sys_p1 = sys_all[sys_all["pass"] == "P1"].copy()
    hours = sys_p1["hour"].to_numpy()
    ecrs = sc.ercot_ecrs_requirement_mw(YEAR, T)  # measured ASPLANNP433 ECRS plan
    meas = pd.read_parquet(_ROOT / f"data/raw/ercot/ercot_{YEAR}_ordc_reserves_hourly.parquet")
    meas = meas.set_index("hour").reindex(range(T))
    rf = pd.read_parquet(BUNDLE / "hourly" / f"reserve_family_{YEAR}.parquet")
    tot = rf[(rf["pass"] == "P1") & (rf["family"] == "ercot_ordc_total")].set_index("hour")
    tot = tot.reindex(range(T))
    # Model energy price net of its own adder (system-hour, max over zones of
    # price - adder is the zone-independent lambda proxy; use the North zone).
    north = sys_p1[sys_p1["zone"] == "North"].set_index("hour").reindex(range(T))
    lam_model = (north["price"] - north["ordc_adder"]).to_numpy(float)

    bases = {
        # Reality's own telemetry: RTOLCAP (online) + RTOFFCAP, measured lambda.
        "measured_rtolcap": (
            (meas["rtolcap"] + meas["rtoffcap"]).to_numpy(float),
            meas["rtolcap"].to_numpy(float), meas["system_lambda"].to_numpy(float),
        ),
        # The keeper's own cleared ORDC-total reserve, model lambda.
        "model_ordc_total": (
            tot["held_mw"].to_numpy(float), tot["held_mw"].to_numpy(float), lam_model,
        ),
    }
    res: dict = {"bar": {"C3a_model_min_usd": 57.00, "C3a_min_pct": -12.35, "C3b_max": 0.30},
                 "ecrs_plan_mean_mw_jun_dec": float(ecrs[3839:].mean()),
                 "keeper": score(sys_all)}
    for name, (r_full, r_on, lam) in bases.items():
        a0 = published_adder(r_full, r_on, lam, cfg)
        a1 = published_adder(r_full - ecrs, r_on - ecrs, lam, cfg)
        d = np.nan_to_num(a1 - a0)
        pert = sys_all.copy()
        m = pert["pass"] == "P1"
        pert.loc[m, "price"] = pert.loc[m, "price"].to_numpy() + d[pert.loc[m, "hour"].to_numpy()]
        res[name] = {
            "delta_adder_mean_usd": float(d.mean()),
            "delta_adder_mean_jun_dec_usd": float(d[3839:].mean()),
            "delta_adder_p99_usd": float(np.percentile(d, 99)),
            "hours_delta_gt_100": int((d > 100).sum()),
            "baseline_adder_mean_usd": float(np.nan_to_num(a0).mean()),
            "scored_on_x33_keeper_upper_bound": score(pert),
        }
    # A basis is admissible only if its BASELINE adder reproduces the keeper's
    # realized in-LP adder (system ordc_adder column) to within $1/MWh.
    realized = float(sys_p1["ordc_adder"].mean())
    res["keeper_realized_ordc_adder_mean_usd"] = realized
    for name in bases:
        res[name]["baseline_reproduces_keeper"] = bool(
            abs(res[name]["baseline_adder_mean_usd"] - realized) <= 1.0
        )
    del hours
    # IDENTIFICATION TEST (rule 14): which reserve basis did ERCOT's own 2023
    # RTORPA form on? The published curve on GROSS RTOLCAP (ECRS counted) vs on
    # RTOLCAP net of the ECRS plan, each against the published RTORPA.
    r_full, r_on, lam = bases["measured_rtolcap"]
    pub = meas["rtorpa"].to_numpy(float)
    gross = published_adder(r_full, r_on, lam, cfg)
    net = published_adder(r_full - ecrs, r_on - ecrs, lam, cfg)
    ident = {}
    for lab, sl in (("year", slice(0, T)), ("ecrs_live_h3839_on", slice(3839, T)),
                    ("pre_ecrs", slice(0, 3839))):
        ident[lab] = {
            "published_rtorpa_mean": float(np.nanmean(pub[sl])),
            "gross_mean": float(np.nanmean(gross[sl])),
            "gross_rmse": float(np.sqrt(np.nanmean((gross[sl] - pub[sl]) ** 2))),
            "net_mean": float(np.nanmean(net[sl])),
            "net_rmse": float(np.sqrt(np.nanmean((net[sl] - pub[sl]) ** 2))),
            "hours_gt_100_published": int((pub[sl] > 100).sum()),
            "hours_gt_100_gross": int((gross[sl] > 100).sum()),
            "hours_gt_100_net": int((net[sl] > 100).sum()),
        }
    res["identification_rtorpa_basis"] = ident
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
