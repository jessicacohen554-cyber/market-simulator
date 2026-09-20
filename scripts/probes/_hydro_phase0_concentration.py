"""Phase-0 hydro water-CONCENTRATION census for PJM and NYISO (zero LP).

The companion to ``_hydro_phase0_pjm_nyiso.py``. That probe asks *where the
hydro sits*; this one asks the question the defect report is actually about:
**how much of each month's water does the model spend in the month's scarcest
hours, against how much the real fleet spends there**. A monthly energy budget
with no intra-month conservation lets the LP bank ~730 hours of water at zero
cost and land all of it on the peak, which is the "dispatches like a peaker
with perfect foresight" signature.

Statistics, per (ISO, year), all computed within each calendar month so the
water year and the monthly budget level cancel out:

* ``top_decile_share`` — the share of the month's hydro energy delivered in the
  month's top-10 % gross-load hours, model vs actual.
* ``top_50h_share`` — the same for the month's top 50 load hours.
* ``peak_day_share`` — the share of the month's energy delivered on the
  month's single highest-load day (a within-month day-to-day banking test).
* ``envelope_bind_share`` — for NYISO, the share of hours the model sits within
  1 % of the armed ``hydro_dispatch_envelope`` p95 ceiling (the caiso-125 §1
  "riding the ceiling" statistic), plus the model's mean percentile rank in the
  measured (month x hour-of-day) bucket distribution. A fleet that rides a p95
  ceiling every hour delivers p95 output ~20x more often than the real fleet.

PJM's published hourly ``Hydro`` FOLDS pumped storage (Data Miner ``Storage``
is batteries only, 20 MW max; PJM is also in ``EIA930_PS_FOLDED_INTO_WAT``), so
PJM's actual column here is NOT a like-for-like population and is printed only
as a SHAPE reference with that caveat attached. PJM's admissible statements are
the model-side ones and the EIA-923 ``HY`` level.

Run: ``uv run --no-sync python3 scripts/probes/_hydro_phase0_concentration.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from _hydro_phase0_pjm_nyiso import (  # noqa: E402
    KEEPERS,
    actual_nyiso,
    actual_pjm,
    model_demand,
    model_hydro,
)

from market_sim.data.fleet import _hour_to_month_index  # noqa: E402


def concentration(series: np.ndarray, load: np.ndarray, mi: np.ndarray) -> dict:
    """Return within-month water-concentration shares for one hourly series."""
    dec, top50, peakday = [], [], []
    day = np.arange(len(series)) // 24
    for mo in range(12):
        sel = mi == mo
        if sel.sum() < 24 * 20:
            continue
        s, l = series[sel], load[sel]
        tot = s.sum()
        if tot <= 0:
            continue
        n10 = max(1, int(0.10 * len(s)))
        order = np.argsort(l)
        dec.append(float(s[order[-n10:]].sum() / tot))
        top50.append(float(s[order[-50:]].sum() / tot))
        d = day[sel]
        dl = pd.Series(l).groupby(d).mean()
        ds = pd.Series(s).groupby(d).sum()
        peakday.append(float(ds[dl.idxmax()] / tot))
    return {
        "top_decile_share": round(float(np.mean(dec)), 4),
        "top_50h_share": round(float(np.mean(top50)), 4),
        "peak_day_share": round(float(np.mean(peakday)), 4),
    }


def envelope_diagnostics(iso: str, year: int, model: np.ndarray) -> dict:
    """Return how hard the model rides the armed p95 deliverability ceiling."""
    from market_sim.data.eia930.envelopes import (
        _hydro_wat_month_hod,
        measured_hydro_hourly_envelope,
    )

    env = measured_hydro_hourly_envelope(iso, year, 8760)
    if env is None:
        return {"error": "no measured envelope"}
    bind = float((model >= 0.99 * env).mean())
    # Model's percentile rank inside each (month, hod) measured bucket.
    obs = _hydro_wat_month_hod(iso, year)
    if obs is None:
        return {"envelope_bind_share": round(bind, 4)}
    mi = _hour_to_month_index(8760) + 1
    hod = np.arange(8760) % 24
    buckets = {
        k: g["mw"].dropna().to_numpy()
        for k, g in obs.groupby(["month", "hod"], observed=True)
    }
    ranks = np.array(
        [
            float((buckets[(m, h)] <= v).mean()) if (m, h) in buckets else np.nan
            for m, h, v in zip(mi, hod, model)
        ]
    )
    return {
        "envelope_bind_share": round(bind, 4),
        "model_mean_bucket_pctile_rank": round(float(np.nanmean(ranks)), 4),
        "model_hours_above_measured_p95_bucket": int(np.nansum(ranks >= 0.95)),
    }


def main() -> None:
    out: dict = {}
    for iso, (bundle, years) in KEEPERS.items():
        out[iso] = {}
        for y in years:
            m = model_hydro(bundle, y)
            load = model_demand(bundle, y)
            mi = _hour_to_month_index(8760)
            a = actual_pjm(y) if iso == "PJM" else actual_nyiso(y)
            rec: dict = {"model": concentration(m, load, mi)}
            if a is not None:
                af = np.nan_to_num(a, nan=0.0)
                rec["actual"] = concentration(af, load, mi)
                if iso == "PJM":
                    rec["actual_CAVEAT"] = (
                        "PJM Data Miner 'Hydro' folds pumped storage "
                        "(15.5 TWh vs 8.9 TWh EIA-923 HY; 6.4 GW max vs "
                        "3.3 GW conventional nameplate) — shape reference only"
                    )
            rec["envelope"] = envelope_diagnostics(iso, y, m)
            out[iso][y] = rec
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
