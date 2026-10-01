"""R-ERCOT-23 phase 0 (zero LP): the 2020/2021 ORDC adder over-statement.

Four reads, all on committed artifacts plus ERCOT's own measured ORDC series
(``data/raw/ercot/ercot_<Y>_ordc_reserves_hourly.parquet``, NP6-905-CD):

1. **Per-term decomposition.** RTORPA = RTOFFPA (full-hour LOLP on RTOLCAP +
   RTOFFCAP) + the half-hour term (LOLP on RTOLCAP). The measured ``rtoffpa``
   isolates the first term, so each term's formula/measured ratio is read
   separately, by year and (2020/2021) by month.
2. **RTORPA identification.** The published formula on measured inputs under
   (i) the keeper's curve, (ii) + the LCAP window
   (``constants.ERCOT_LCAP_WINDOWS_BY_YEAR``), (iii) the ORDC OBD's half-hour
   form (mean 0.5 x (mu + S sigma)) and (iv) ERCOT's published seasonal
   mu / sigma digitized from Figure 3 of its 2022 Biennial ORDC Report —
   (iii)/(iv) are DIAGNOSTIC (carded, not built: they move every year).
3. **The protocol cap census.** Hours where the r-22 keeper's written price
   exceeds the hour's effective SWCAP (lambda + adders > SWCAP).
4. **Zero-LP prediction** of ``ercot_swcap_effective_hourly`` on the r-22
   keeper: in the LCAP window the in-LP reserve penalties scale by
   LCAP / HCAP, so at the keeper's own (measured-cap-bound) reserve level
   the written ORDC adder scales by the same ratio; then every hour's adders
   are trimmed to SWCAP - lambda. Energy lambda is held at the keeper's.

Never fitted to RTORPA: every curve parameter is a published value.
Read 4 reads the r-22 keeper bundle ``r_ercot22_span``, pruned at the R-ERCOT-23
promotion (rule 35); restore it from git history (its last commit on main) to
re-run that read.
Writes ``docs/records/ercot/r-ercot/r_ercot23_phase0.json``.
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
from market_sim.results.scarcity import ercot_effective_swcap_series  # noqa: E402

KEEPER = ROOT / "results/calibration/r_ercot22_span/hourly"
MEAS = ROOT / "data/raw/ercot"
OUT = ROOT / "docs/records/ercot/r-ercot/r_ercot23_phase0.json"
SIGMA_FALLBACK, MU_FALLBACK = 1400.0, 0.0  # ScenarioConfig ordc_lolp_* defaults

# ERCOT 2022 Biennial ORDC Report, Figure 3 (seasonal "ORDC Mu" — shift
# included — and "ORDC Sigma"), digitized from the 160-dpi render: right axis
# 3,000 MW at y=438 px, 0 MW at y=787 px (8.6 MW/px, read to ~±2 px). Each
# row: (effective date, mu_shifted px, sigma px). DIAGNOSTIC ONLY.
_FIG3 = [
    ("2018-12-01", 750, 645),
    ("2019-03-01", 712, 646),
    ("2019-06-01", 714, 646),
    ("2019-09-01", 715, 646),
    ("2019-12-01", 716, 646),
    ("2020-03-01", 681, 646),
    ("2020-06-01", 683, 646),
    ("2020-09-01", 685, 646.5),
    ("2020-12-01", 686, 646.5),
    ("2021-03-01", 687, 646.5),
    ("2021-06-01", 688, 646.5),
    ("2021-09-01", 688, 646.5),
    ("2021-12-01", 683, 638),
    ("2022-03-01", 683, 638),
    ("2022-06-01", 685, 638),
    ("2022-09-01", 686, 638),
]


def _px(y: float) -> float:
    return (787.0 - y) * 3000.0 / 349.0


def _shift(year: int, idx: pd.DatetimeIndex) -> np.ndarray:
    """PUCT 48551 shift (sigma units) in force at each hour."""
    if year == 2019:
        return np.where(idx >= pd.Timestamp("2019-03-01"), 0.25, 0.0)
    if year == 2020:
        return np.where(idx >= pd.Timestamp("2020-03-01"), 0.5, 0.25)
    return np.full(len(idx), 0.5)


def _lolp(r, mcl, mu_s, sig):
    return np.where(r <= mcl, 1.0, 1.0 - ndtr((r - mcl - mu_s) / sig))


def _measured(year: int) -> pd.DataFrame:
    return pd.read_parquet(MEAS / f"ercot_{year}_ordc_reserves_hourly.parquet").iloc[
        :8760
    ]


def _formula(
    year: int, *, lcap: bool, obd_half: bool, fig3: bool
) -> tuple[np.ndarray, np.ndarray]:
    """(full-hour term, half-hour term) of the published RTORPA on measured inputs."""
    m = _measured(year)
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    hcap, mcl = order["ordc_voll"], order["ordc_mcl_mw"]
    voll = (
        ercot_effective_swcap_series(year, 8760, hcap) if lcap else np.full(8760, hcap)
    )
    if fig3:
        mu_s = np.zeros(8760)
        sig = np.zeros(8760)
        for d, a, b in _FIG3:
            k = idx >= pd.Timestamp(d)
            mu_s[k], sig[k] = _px(a), _px(b)
    else:
        sig = np.full(8760, SIGMA_FALLBACK)
        mu_s = MU_FALLBACK + _shift(year, idx) * sig
    hd = np.maximum(voll - m.system_lambda.to_numpy(), 0.0)
    on = m.rtolcap.to_numpy()
    full = on + m.rtoffcap.to_numpy()
    half_mu = (
        0.5 * mu_s if obd_half else MU_FALLBACK / 2 + (mu_s - MU_FALLBACK) / np.sqrt(2)
    )
    tf = 0.5 * hd * _lolp(full, mcl, mu_s, sig)
    th = 0.5 * hd * _lolp(on, mcl, half_mu, sig / np.sqrt(2))
    return tf, th


def per_term(year: int) -> dict:
    """Read 1: formula / measured, by term (keeper curve)."""
    m = _measured(year)
    tf, th = _formula(year, lcap=False, obd_half=False, fig3=False)
    aoff = m.rtoffpa.to_numpy()
    aon = m.rtorpa.to_numpy() - aoff
    out = {
        "full_hour_term_ratio": round(float(tf.sum() / aoff.sum()), 3),
        "half_hour_term_ratio": round(float(th.sum() / aon.sum()), 3),
    }
    if year in (2020, 2021):
        mon = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month
        df = pd.DataFrame({"m": mon, "model": tf + th, "actual": m.rtorpa.to_numpy()})
        g = df.groupby("m").sum()
        out["by_month_model_actual"] = {
            int(k): [round(float(r.model)), round(float(r.actual))]
            for k, r in g.iterrows()
            if r.model + r.actual > 200
        }
    return out


def identification(year: int) -> dict:
    """Read 2: total formula / measured RTORPA under each variant."""
    m = _measured(year)
    act = m.rtorpa.to_numpy()
    if not np.isfinite(act).all():
        return {"skipped": "non-finite RTORPA in the measured series"}
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    variants = {
        "keeper": dict(lcap=False, obd_half=False, fig3=False),
        "keeper+LCAP": dict(lcap=True, obd_half=False, fig3=False),
        "diag_OBD_half+LCAP": dict(lcap=True, obd_half=True, fig3=False),
    }
    if year <= 2022:
        variants["diag_fig3_mu_sigma+OBD_half+LCAP"] = dict(
            lcap=True, obd_half=True, fig3=True
        )
    voll = ercot_effective_swcap_series(year, 8760, order["ordc_voll"])
    hd = np.maximum(voll - m.system_lambda.to_numpy(), 0.0)
    res = {"actual_sum": round(float(act.sum()))}
    for name, kw in variants.items():
        tf, th = _formula(year, **kw)
        v = np.minimum(tf + th, hd) if kw["lcap"] else tf + th
        res[name] = {
            "ratio": round(float(v.sum() / act.sum()), 3),
            "r": round(float(np.corrcoef(v, act)[0, 1]), 3),
        }
    return res


def _keeper_system(year: int) -> pd.DataFrame:
    d = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"].copy()
    for c in ("ordc_adder", "rtordpa_overlay", "dam_as_overlay"):
        d[c] = d[c].fillna(0.0) if c in d else 0.0
    return d


def prediction(year: int) -> dict:
    """Reads 3+4: protocol-cap census and the zero-LP prediction."""
    d = _keeper_system(year)
    T = int(d.hour.max()) + 1
    hcap = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]["ordc_voll"]
    sw = ercot_effective_swcap_series(year, T, hcap)
    d["adders"] = d.ordc_adder + d.rtordpa_overlay + d.dam_as_overlay
    d["energy"] = d.price - d.adders
    pz = d.pivot(index="hour", columns="zone", values="price").to_numpy()
    ez = d.pivot(index="hour", columns="zone", values="energy").to_numpy()
    dz = d.pivot(index="hour", columns="zone", values="demand").to_numpy()
    g = d.groupby("hour").first()
    lam = (ez * dz).sum(1) / dz.sum(1)
    ordc = g.ordc_adder.to_numpy()
    rtd = g.rtordpa_overlay.to_numpy()
    das = g.dam_as_overlay.to_numpy()
    room = np.maximum(sw - lam, 0.0)
    o_new = np.minimum(ordc * sw / hcap, room)
    r_new = np.minimum(rtd, room - o_new)
    a_new = np.minimum(das, room - o_new - r_new)
    delta = (o_new + r_new + a_new) - (ordc + rtd + das)
    pn = pz + delta[:, None]
    lw = lambda p: float((p * dz).sum() / dz.sum())  # noqa: E731
    sysp = lambda p: (p * dz).sum(1) / dz.sum(1)  # noqa: E731
    w = dz.sum(1) / dz.sum()
    lc = sw < hcap
    m = _measured(year).iloc[:T]
    act = (m.system_lambda + m.rtorpa + m.rtordpa).to_numpy()
    return {
        "hours_lambda_plus_adders_gt_swcap": int(
            ((lam + ordc + rtd + das) > sw + 1e-6).sum()
        ),
        "max_system_price": [
            round(float(sysp(pz).max())),
            round(float(sysp(pn).max())),
        ],
        "LW": [round(lw(pz), 2), round(lw(pn), 2)],
        "actual_LW": round(float((act * w).sum()), 2),
        "C3a_proxy": [
            round(lw(pz) / float((act * w).sum()) - 1, 4),
            round(lw(pn) / float((act * w).sum()) - 1, 4),
        ],
        "lcap_window_adder_LW": {
            "model_before": round(float((ordc * w)[lc].sum()), 2),
            "model_after": round(float((o_new * w)[lc].sum()), 2),
            "measured_rtorpa": round(float((m.rtorpa.to_numpy() * w)[lc].sum()), 2),
        },
        "h_gt_1k": [int((sysp(pz) > 1000).sum()), int((sysp(pn) > 1000).sum())],
        "h_gt_200": [int((sysp(pz) > 200).sum()), int((sysp(pn) > 200).sum())],
    }


def main() -> None:
    """Run the reads and write the JSON record."""
    years = range(2019, 2026)
    rec = {
        "per_term": {y: per_term(y) for y in range(2019, 2025)},
        "rtorpa_identification": {y: identification(y) for y in years},
        "prediction_on_r22_keeper": {y: prediction(y) for y in years},
    }
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps(rec, indent=1, default=str))


if __name__ == "__main__":
    main()
