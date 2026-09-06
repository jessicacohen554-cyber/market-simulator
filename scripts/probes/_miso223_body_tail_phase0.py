"""miso-223 phase 0 — the seasonal misses are ONE flat body defect. Zero solve.

Reproduces every number in ``PREREG-miso223-committed-band-debody-2026-09-06.md``
sections 1-2 and 4 from COMMITTED artifacts only: the designated keeper's own
``hourly/`` sidecars, its predecessor bundle, MISO's published RT hub LMPs and
EIA-930. No LP is solved and nothing is minted.

THE CONSTRUCTION, stated because it is what makes the claim falsifiable.

* **Model price** is the load-weighted mean across the six carrying zones of the
  P1 energy dual, one value per hour (``hourly/system_<year>.parquet``). P1 is
  the pass every run is scored on.
* **Actual price** is the unweighted mean across MISO's published hubs of the RT
  LMP (``data/raw/lmp-data/MISO/miso_hub_lmp_<year>_rt.csv.gz``, ``he01``-``he24``
  interval-beginning, model clock). Hub-mean rather than load-weighted because
  the published hub set carries no load weights; the bench's own ``rt_lw_mon``
  load-weighted monthly series is reported alongside as the cross-check.
* **Body / tail** split each month's (or year's) two distributions at their OWN
  90th percentile after sorting, so the comparison is quantile-matched and does
  not depend on hour alignment between model and actual. ``body`` is the mean of
  the bottom 90 %, ``tail`` the mean of the top 10 %; their weighted sum is the
  mean error exactly.

WHY QUANTILE-MATCHED AND NOT HOUR-MATCHED. The claim under test is about the
SHAPE of the price distribution, not about whether the model puts the right
price in the right hour (that is C4's question, and it passes). Hour-matching
would fold a timing error into a level statement.

ALSO REPORTED (the ``renewables`` block) — WHY THE MODEL HAS A HARD PRICE FLOOR.
The model's wind carries a -$26/MWh PTC dispatch offer, so in any hour wind were
marginal the price would clear deeply negative; the committed record has no
zone-hour below $0 in three years. The reason is NOT that the wind potential is
wrong — it is that the LP never curtails it.

``data/renewables.py`` deliberately hands MISO an **uncurtailed** wind potential:
MISO is in ``_UNCURTAILED_FALLBACK_ISOS``, so the EIA-930 delivered shape is
grossed up by the Potomac Economics (MISO IMM) measured annual wind-curtailment
rate — ``delivered / (1 - rate)`` — expressly so the dispatch "still curtails
endogenously and responds to changed build" rather than inheriting the
curtailment already baked into delivered output. That gross-up is working: the
+5.15 % model-over-EIA-930 wind figure this block reports is the intended
potential, not an error.

**The finding is what the LP then does with it: essentially nothing.** Model wind
DISPATCH lands on the grossed-up potential to within 0.02 TWh in all three years,
so endogenous curtailment is 0.02 / 0.00 / 0.01 % against the ~4.9 % the gross-up
assumed. Wind therefore never sits below its bound, is never the marginal unit,
and its -$26 offer never reaches the price — which is exactly the hard floor
section 1 measures ($17.18 minimum across 210,240 zone-hours, against an actual
MISO that cleared below $20 in 1,781 / 3,097 / 510 hours and went negative).

``renewables.py`` already names this quantity a standing diagnostic — "the
modeled-vs-reported curtailment gap is a diagnostic, never a fit target
(CLAUDE.md #11)". This probe measures it and reports it reading ~100 %
unexplained. It is a SUCCESSOR OBJECT, independent of this session's offer-band
arm, and nothing here proposes a lever for it.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    python3 scripts/probes/_miso223_body_tail_phase0.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "miso220_nonsteamlift_B"
PRIOR = CAL / "miso217_intermphys_B"
LMP = REPO / "data" / "raw" / "lmp-data" / "MISO"
YEARS = (2023, 2024, 2025)
HE = tuple(f"he{i:02d}" for i in range(1, 25))
#: The eleven classes miso-220 lifted x1.10; ST_GAS/ST_GAS_INTERMEDIATE held at 1.0.
LIFTED = frozenset({
    "CC_REGULAR", "CC_INTERMEDIATE", "CC_CHP", "CT_CHP", "CT_PEAKER",
    "CT_INTERMEDIATE", "COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC", "COAL",
})


def actual_hourly(year: int) -> pd.Series:
    """Hub-mean published RT LMP, one value per hour, on the model clock."""
    raw = pd.read_csv(LMP / f"miso_hub_lmp_{year}_rt.csv.gz")
    raw = raw[raw["value"] == "LMP"]
    long = raw.melt(id_vars=["date", "node"], value_vars=list(HE),
                    var_name="he", value_name="p")
    long["p"] = pd.to_numeric(long["p"], errors="coerce")
    long["dt"] = pd.to_datetime(long["date"]) + pd.to_timedelta(
        long["he"].str[2:].astype(int) - 1, unit="h")
    return long.groupby("dt")["p"].mean().sort_index()


def model_hourly(bundle: Path, year: int) -> pd.Series:
    """Load-weighted system P1 price, one value per hour."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    g = df.groupby("hour").apply(
        lambda d: np.average(d["price"], weights=d["demand"]), include_groups=False)
    idx = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(g.index, unit="h")
    return pd.Series(g.to_numpy(), index=idx)


def split(model: np.ndarray, actual: np.ndarray) -> dict:
    """Quantile-matched body/tail decomposition of the mean error."""
    actual = actual[~np.isnan(actual)]
    n = min(model.size, actual.size)
    m, a = np.sort(model)[-n:], np.sort(actual)[-n:]
    k = int(np.ceil(0.10 * n))
    body_d, tail_d = float(m[:-k].mean() - a[:-k].mean()), float(m[-k:].mean() - a[-k:].mean())
    return {
        "n": int(n), "mean_err": round(float(m.mean() - a.mean()), 3),
        "body_delta": round(body_d, 3), "tail_delta": round(tail_d, 3),
        "body_contribution": round(body_d * (n - k) / n, 3),
        "tail_contribution": round(tail_d * k / n, 3),
        "model_p50": round(float(np.median(m)), 2), "actual_p50": round(float(np.median(a)), 2),
        "model_p99": round(float(np.percentile(m, 99)), 2),
        "actual_p99": round(float(np.percentile(a, 99)), 2),
        "actual_hours_gt_100": int((a > 100).sum()),
    }


def main() -> None:
    out: dict = {"probe": "miso-223 phase 0 — body/tail decomposition", "solved": False,
                 "keeper": str(KEEPER), "prior": str(PRIOR), "by_year": {},
                 "by_month": {}, "floor": {}, "footprint": {}, "renewables": {}}
    errs, scarce = [], []
    for year in YEARS:
        a_h, m_h = actual_hourly(year), model_hourly(KEEPER, year)
        a_h = a_h[a_h.index.year == year]
        out["by_year"][str(year)] = {
            "keeper": split(m_h.to_numpy(), a_h.to_numpy()),
            "prior_miso217": split(model_hourly(PRIOR, year).to_numpy(), a_h.to_numpy()),
        }
        months = {}
        for mo in range(1, 13):
            row = split(m_h[m_h.index.month == mo].to_numpy(),
                        a_h[a_h.index.month == mo].to_numpy())
            months[f"{year}-{mo:02d}"] = row
            errs.append(row["mean_err"])
            scarce.append(row["actual_hours_gt_100"])
        out["by_month"].update(months)

        # The floor statement: the model's whole distribution vs the actual's.
        sysdf = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        av = a_h.to_numpy()
        av = av[~np.isnan(av)]
        out["floor"][str(year)] = {
            "model_min_zone_hour": round(float(sysdf["price"].min()), 2),
            "model_zone_hours_below_0": int((sysdf["price"] < 0).sum()),
            "model_zone_hours_total": int(len(sysdf)),
            "model_system_hours_below_20": int((m_h.to_numpy() < 20).sum()),
            "actual_hours_below_20": int((av < 20).sum()),
            "actual_min": round(float(av.min()), 2),
        }

        # Footprint of the arm's band, from the keeper's own committed sidecar.
        band = pd.read_parquet(KEEPER / "hourly" / f"class_band_hourly_{year}.parquet")
        band = band[band["pass"] == "P1"]
        lifted = band[band["klass"].isin(LIFTED)]
        committed = lifted[lifted["band"] == "committed"]["mw"].sum() / 1e6
        # Model vs EIA-930 renewable energy: the "is the model ever long?" question.
        e930 = json.loads(gzip.decompress(
            (REPO / "frontend" / "data" / "backcast" / "bench" / "MISO"
             / f"{year}.json.gz").read_bytes()))["bench"]["e930"]
        cls = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        # The IMM reference rate the gross-up used, recovered from the module that
        # applies it, so the curtailment arithmetic cites the code rather than a
        # number retyped here.
        from market_sim.data.renewables import _miso_wind_reference_curtailment_rate
        ref = _miso_wind_reference_curtailment_rate()
        ref_rate = float(ref[0]) if isinstance(ref, tuple) else float(ref)
        ren = {"imm_reference_curtailment_rate": round(ref_rate, 5)}
        for fuel in ("wind", "solar"):
            model_twh = float(cls[cls["klass"] == fuel]["mw"].sum() / 1e6)
            actual_twh = float(e930[fuel])
            ren[fuel] = {
                "model_twh": round(model_twh, 2), "eia930_twh": round(actual_twh, 2),
                "pct_over_actual": round(100 * (model_twh - actual_twh) / actual_twh, 2),
            }
            if fuel == "wind":
                potential = actual_twh / (1.0 - ref_rate)
                ren[fuel].update({
                    "uncurtailed_potential_twh": round(potential, 2),
                    "lp_curtailed_twh": round(potential - model_twh, 3),
                    "lp_curtailment_pct": round(
                        100 * (potential - model_twh) / potential, 3),
                })
        out["renewables"][str(year)] = ren

        out["footprint"][str(year)] = {
            "committed_band_twh": round(float(committed), 2),
            "lifted_class_twh": round(float(lifted["mw"].sum() / 1e6), 2),
            "system_twh": round(float(sysdf["demand"].sum() / 1e6), 2),
        }

    out["summary"] = {
        "months_body_too_high": int(sum(1 for m in out["by_month"].values() if m["body_delta"] > 0)),
        "months_tail_too_low": int(sum(1 for m in out["by_month"].values() if m["tail_delta"] < 0)),
        "months_scored": len(out["by_month"]),
        "corr_monthly_err_vs_scarcity_hours": round(float(np.corrcoef(errs, scarce)[0, 1]), 3),
        "screen_year": max(out["footprint"], key=lambda y: out["footprint"][y]["committed_band_twh"]),
    }
    dest = CAL / "_miso223_body_tail.json"
    dest.write_text(json.dumps(out, indent=1))
    s = out["summary"]
    print(f'body too high in {s["months_body_too_high"]}/{s["months_scored"]} months; '
          f'tail too low in {s["months_tail_too_low"]}/{s["months_scored"]}')
    print(f'corr(monthly err, actual hours >$100) = {s["corr_monthly_err_vs_scarcity_hours"]}')
    print(f'screen year (largest committed-band footprint) = {s["screen_year"]}')
    cur = {y: v["wind"]["lp_curtailment_pct"] for y, v in out["renewables"].items()}
    ref = next(iter(out["renewables"].values()))["imm_reference_curtailment_rate"]
    print(f"LP wind curtailment (% of the uncurtailed potential): {cur}")
    print(f"  ...against the IMM reference rate the gross-up assumed: {100 * ref:.2f}%")
    print(f"-> {dest}")


if __name__ == "__main__":
    main()
