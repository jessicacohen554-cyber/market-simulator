"""R-ERCOT-24 phase 0 (zero LP): the ORDC curve-parameter vintage.

Two structural deviations from ERCOT's published ORDC (both zero-DOF), read
on ERCOT's own measured RTOLCAP / RTOFFCAP / system lambda / RTORPA
(``data/raw/ercot/ercot_<Y>_ordc_reserves_hourly.parquet``, NP6-905-CD):

(a) **The first-half (spinning) curve.** ORDC OBD §2.3, every vintage
    2019-02-13 .. 2024-10-01: ``SLOLP_s = 1 - CDF(0.5 * mu_s, 0.707 * sigma)``
    with ``mu_s = mu + S * sigma`` — the shift is halved with the mean. The
    model applies ``mu/2 + S * sigma/sqrt(2)``.
(b) **Seasonal mu_s / sigma.** ERCOT re-derives mu and sigma once per season
    (NP6-576-ER, report 13233 — retention-expired on the free MIS path, and the
    credentialed API is owner-declined). The values are read from Figure 3 of
    ERCOT's 2022 and 2024 Biennial ORDC Reports
    (``data/raw/ercot/ordc-biennial/``) by
    ``scripts/data/derive_ercot_ordc_mu_sigma.py`` into
    ``data/raw/ercot/ercot_ordc_mu_sigma_seasonal.csv``. The model uses a flat
    ``mu = 0, sigma = 1,400`` fallback.

Variants (each with the LCAP window, the protocol cap and — from
2023-11-01 — the OBDRR048 floor, exactly as the keeper):
  K  keeper curve (year-grain shift S, mu 0, sigma 1,400, model half form)
  A  K + OBD half form
  B  published seasonal mu_s / sigma, model half form
  AB published seasonal mu_s / sigma + OBD half form (the build)

Never fitted to RTORPA: every curve parameter is a published value.
Writes ``docs/records/ercot/r-ercot/r_ercot24_phase0.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import (  # noqa: E402
    ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR,
)
from market_sim.results.scarcity import (  # noqa: E402
    ORDC_FLOOR_STEPS,
    ercot_effective_swcap_series,
    ercot_published_mu_sigma_hourly,
)

MEAS = ROOT / "data/raw/ercot"
OUT = ROOT / "docs/records/ercot/r-ercot/r_ercot24_phase0.json"
SIGMA_FALLBACK, MU_FALLBACK = 1400.0, 0.0  # ScenarioConfig ordc_lolp_* defaults
FLOOR_FROM = pd.Timestamp("2023-11-01")  # OBDRR048


def seasonal(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Hourly published (mu_s, sigma) for ``year`` — the solve's own loader."""
    return ercot_published_mu_sigma_hourly(year, 8760)


def _lolp(r, mcl, mu, sig):
    return np.where(r <= mcl, 1.0, 1.0 - ndtr((r - mcl - mu) / sig))


def formula(year: int, *, obd_half: bool, published: bool) -> np.ndarray:
    """Published RTORPA on measured inputs under one curve variant."""
    m = pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").iloc[:8760]
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    mcl, s = order["ordc_mcl_mw"], order["ordc_lolp_shift_sigma"]
    voll = ercot_effective_swcap_series(year, 8760, order["ordc_voll"])
    if published:
        mu_s, sig = seasonal(year)
        mu_raw = mu_s - s * sig
    else:
        sig = np.full(8760, SIGMA_FALLBACK)
        mu_raw = np.full(8760, MU_FALLBACK)
        mu_s = mu_raw + s * sig
    half_mu = 0.5 * mu_s if obd_half else mu_raw / 2 + s * sig / np.sqrt(2)
    lam = m.system_lambda.to_numpy()
    hd = np.maximum(voll - lam, 0.0)
    on = m.rtolcap.to_numpy()
    full = on + m.rtoffcap.to_numpy()
    v = 0.5 * hd * (_lolp(full, mcl, mu_s, sig) + _lolp(on, mcl, half_mu, sig / np.sqrt(2)))
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    floor = np.zeros(8760)
    for thr, val in sorted(ORDC_FLOOR_STEPS, reverse=True):
        floor = np.where(on <= thr, val, floor)
    v = np.maximum(v, np.where(idx >= FLOOR_FROM, floor, 0.0))
    return np.minimum(v, hd)


VARIANTS = {
    "K": dict(obd_half=False, published=False),
    "A": dict(obd_half=True, published=False),
    "B": dict(obd_half=False, published=True),
    "AB": dict(obd_half=True, published=True),
}


def identification(year: int) -> dict:
    """Formula / measured RTORPA ($.h) and hourly correlation, per variant."""
    m = pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").iloc[:8760]
    act = m.rtorpa.to_numpy()
    ok = np.isfinite(act) & np.isfinite(m.rtolcap.to_numpy())
    res = {"actual_mean": round(float(act[ok].mean()), 3), "hours": int(ok.sum())}
    for name, kw in VARIANTS.items():
        v = formula(year, **kw)
        res[name] = {
            "ratio": round(float(v[ok].sum() / act[ok].sum()), 3),
            "r": round(float(np.corrcoef(v[ok], act[ok])[0, 1]), 3),
            "mean": round(float(v[ok].mean()), 3),
        }
    return res


def main() -> None:
    """Run the identification and write the JSON record."""
    rec = {"rtorpa_identification": {y: identification(y) for y in range(2019, 2026)}}
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps(rec, indent=1, default=str))




# --------------------------------------------------------------------------
# Read 2: zero-LP prediction on the r-23 keeper (dispatch held fixed).
# --------------------------------------------------------------------------
KEEPER = ROOT / "results/calibration/r_ercot23_span/hourly"
SPAN_SIGMA = 5.0  # ercot_ordc_demand_steps sigma_span default


def _curve(r, voll, mcl, mu_s, sig, half_mu, floor_on):
    v = 0.5 * voll * (
        _lolp(r, mcl, mu_s, sig) + _lolp(r, mcl, half_mu, sig / np.sqrt(2))
    )
    if floor_on is not None:
        fl = np.zeros_like(v)
        for thr, val in sorted(ORDC_FLOOR_STEPS, reverse=True):
            fl = np.where(r <= thr, val, fl)
        v = np.maximum(v, np.where(floor_on, fl, 0.0))
    return v


def prediction(year: int) -> dict:
    """Re-price the keeper's cleared ORDC reserve level on the AB curve.

    The family's cleared reserve level on the keeper grid is
    ``req_total_K - shortfall`` (credits net the requirement, so held + credit
    sits at that grid point). The adder written into the price scales by the
    curve-value ratio AB / K at that level; energy lambda and every other
    family are held at the keeper's. First order: re-dispatch is ignored.
    """
    s = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    f = pd.read_parquet(KEEPER / f"reserve_family_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f.family == "ercot_ordc_total")].sort_values("hour")
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    mcl, sh = order["ordc_mcl_mw"], order["ordc_lolp_shift_sigma"]
    T = len(f)
    voll = ercot_effective_swcap_series(year, T, order["ordc_voll"])
    req_k = mcl + sh * SIGMA_FALLBACK + SPAN_SIGMA * SIGMA_FALLBACK
    r = req_k - f.shortfall_mw.to_numpy()
    idx = pd.date_range(f"{year}-01-01", periods=T, freq="h")
    floor_on = (idx >= FLOOR_FROM) if year >= 2023 else None
    pk = _curve(
        r, voll, mcl, sh * SIGMA_FALLBACK, np.full(T, SIGMA_FALLBACK),
        sh * SIGMA_FALLBACK / np.sqrt(2), floor_on,
    )
    mu_s, sig = seasonal(year)
    mu_s, sig = mu_s[:T], sig[:T]
    pab = _curve(r, voll, mcl, mu_s, sig, 0.5 * mu_s, floor_on)
    ratio = np.where(pk > 1e-9, pab / np.maximum(pk, 1e-9), 1.0)
    dz = s.pivot(index="hour", columns="zone", values="demand").to_numpy()
    pz = s.pivot(index="hour", columns="zone", values="price").to_numpy()
    w = dz.sum(1) / dz.sum()
    oa = s.groupby("hour").ordc_adder.first().to_numpy()
    lw = float((pz * dz).sum() / dz.sum())
    d_oa = oa * (ratio - 1.0)
    sysp = (pz * dz).sum(1) / dz.sum(1)
    m = pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").iloc[:T]
    act = (m.system_lambda + m.rtorpa + m.rtordpa).to_numpy()
    act_lw = float(np.nansum(act * w))
    new = sysp + d_oa
    bands = {}
    for lo, hi in ((-1e9, 100), (100, 1000), (1000, 1e9)):
        k = (sysp >= lo) & (sysp < hi)
        bands[f"{lo:g}..{hi:g}"] = {
            "hours": int(k.sum()),
            "d_LW_contrib": round(float((d_oa * w)[k].sum()), 3),
        }
    return {
        "recalc_check_r_dual": round(
            float(np.corrcoef(pk * np.where(f.dual > 0, 1, 0), f.dual)[0, 1]), 3
        )
        if (f.dual > 0).any()
        else None,
        "LW": [round(lw, 2), round(lw + float((d_oa * w).sum()), 2)],
        "ordc_adder_LW": [
            round(float((oa * w).sum()), 2),
            round(float(((oa + d_oa) * w).sum()), 2),
        ],
        "measured_rtorpa_LW": round(float(np.nansum(m.rtorpa.to_numpy() * w)), 2),
        "C3a_proxy": [
            round(lw / act_lw - 1, 4),
            round((lw + float((d_oa * w).sum())) / act_lw - 1, 4),
        ],
        "by_price_band": bands,
        "h_gt_1k": [int((sysp > 1000).sum()), int((new > 1000).sum())],
        "h_gt_200": [int((sysp > 200).sum()), int((new > 200).sum())],
    }


def main_all() -> None:
    """Both reads; writes the JSON record."""
    rec = {
        "rtorpa_identification": {y: identification(y) for y in range(2019, 2026)},
        "prediction_on_r23_keeper": {y: prediction(y) for y in range(2019, 2026)},
    }
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps(rec["prediction_on_r23_keeper"], indent=1, default=str))


if __name__ == "__main__":
    main_all()
