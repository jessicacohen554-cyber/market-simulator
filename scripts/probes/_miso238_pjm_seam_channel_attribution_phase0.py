"""miso-238 phase 0 — WHICH CHANNEL of the PJM seam reconstruction carries the model's
spurious own-net-load response, and which carries the REMAINDER of its excess residual
price alignment? Handoff queue items 3 and 2, on ONE exact decomposition. Zero LP.

Pre-registration:
``results/calibration/PREREG-miso238-pjm-seam-channel-attribution-2026-09-07.md``
(pushed at ``0deffdb9``, before any adjudicating quantity). Every decision rule applied
here is fixed there; nothing below selects anything.

miso-237 minted the object and attributed none of it: the model's PJM seam residual carries
a large, stable, NEGATIVE own-net-load response (-866.2/-1043.4/-843.5 MW per z-score) the
real seam does not have, and roughly half of the model's excess residual price alignment is
still unaccounted for after miso-237's own-state purge. The handoff NAMED one hypothesis for
the first — the deliverability envelope binding in exactly those hours — and left it
untested.

The reconstruction's algebra makes the question exactly answerable with zero free
parameters (PREREG §0c/§2). Every band term is ``price indicator x envelope weight``:

    imp(t) = sum_k m_k(t) * b_k(t)      exp(t) = sum_k q_k(t) * c_k(t)
    model_net(t) = imp(t) - exp(t)

with ``m_k``/``q_k`` pure functions of PRICE and ``b_k``/``c_k`` pure functions of the
(month x hod) deliverability ENVELOPE template. Writing each factor as mean-plus-deviation
splits ``model_net`` into three channels, up to an additive constant every statistic here
annihilates:

    MERIT    = sum_k m~_k(t) * b-_k  -  sum_k q~_k(t) * c-_k     (pure price)
    ENVELOPE = sum_k m-_k * b~_k(t)  -  sum_k q-_k * c~_k(t)     (pure (month x hod) template)
    INTERACT = sum_k m~_k(t) * b~_k(t) - sum_k q~_k(t) * c~_k(t) (the envelope binding
                                                                  differently by price hour)

* **Provenance gate (PREREG §1), four legs.** (G-P1) miso-235's ``sigma_measured_mw`` and
  ``sigma_resid_measured_mw``, 4 seams x 3 years, to <= 0.5 MW. (G-P2) miso-237's
  ``own_net_load_coef_resid_model`` and ``..._measured``, 4 x 3, to <= 0.5 MW/z — the object
  this session decomposes, reproduced in miso-237's own metric first. (G-P3) miso-237
  ADDENDUM §A's four-value alignment column, 4 x 3, to <= 0.001. (G-ID) the decomposition
  identity to <= 1e-6 MW. Any leg failing declares the instrument BROKEN and nothing else
  is read.
* **Q-A (PREREG §3, item 3).** ``gamma`` — miso-237's PARTIAL OLS coefficient on own net
  load in ``ols_resid(., p1) ~ [1 | z_own_net_load | z_own_VRE]`` (see
  ``ADDENDUM-miso238-gate-repair-and-the-partial-coefficient-2026-09-07.md``) — decomposed
  across the three channels. GATED on PJM: ENVELOPE-DRIVEN iff
  ``(gamma_ENV + gamma_INT)/gamma_model >= 0.50`` all three years, MERIT-DRIVEN iff
  ``gamma_MERIT/gamma_model >= 0.50`` all three years, else MIXED; read only where
  ``|gamma_model| >= 200`` MW/z.
* **Q-A' (PREREG §3a).** The saturation census — REPORTED, NOT GATED, evidence for the
  verdict's story and never for the verdict.
* **Q-B (PREREG §4, item 2).** The alignment numerator ``a = cov(resid, P_RT)/sigma(P_RT)``
  (MW, additive where ``|corr|`` is not) decomposed across the same channels, on the raw AND
  the own-state-purged residual, model side AND measured side. GATED on PJM with the mirror
  bars; read only where ``|a_model_purged| >= 100`` MW.

Basis discipline (miso-234 §0a, miso-235 §0b, miso-236 §0b, miso-237 §0b): the Indiana-hub
**RT** series builds the finite-hour ``ok`` mask (byte-identically to miso-236/237, so the
hour set is the predecessors') and is the alignment price ``P``; every regressor and every
merit signal is the Indiana-hub **DA** series. They correlate only +0.402/+0.424/+0.553 and
are never interchanged.

Usage: python3 scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso233_sppseam_K"
BALANCE_DIR = REPO / "data/raw/eia-930"
MISO235 = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
MISO237 = (
    REPO / "results/calibration/_miso237_price_representation_vs_state_phase0.json"
)
OUT = REPO / "results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
FOUR_SEAM = ("PJM", "SPP", "South", "Manitoba")
BUS_OF_SEAM = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}

# PREREG §1 provenance bars, fixed ex ante.
TOL_SIGMA_MW = 0.5
TOL_COEF_MW = 0.5
TOL_ALIGN = 0.001
TOL_IDENTITY_MW = 1e-6
# PREREG §3/§4 decision bars, fixed ex ante.
CHANNEL_BAR = 0.50
GAMMA_FLOOR_MW = 200.0
ALIGN_FLOOR_MW = 100.0
GATED_SEAM = "PJM"

CHANNELS = ("MERIT", "ENVELOPE", "INTERACT")

_MONTH_LEN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0, *[24 * d for d in _MONTH_LEN]])[:12]


def ols_resid(x: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Residual of ``x = a + beta*z + r`` (the miso-235 §3 single-regressor OLS)."""
    zc = z - z.mean()
    var_z = float((zc * zc).mean())
    beta = float(((x - x.mean()) * zc).mean() / var_z) if var_z > 0 else 0.0
    return x - (x.mean() + beta * zc)


def _design(X: np.ndarray, n: int) -> np.ndarray:
    """``[1 | X]`` with an intercept, tolerating an empty regressor block."""
    return np.column_stack([np.ones(n), X]) if X.size else np.ones((n, 1))


def purge(r: np.ndarray, S: np.ndarray) -> np.ndarray:
    """miso-237 ADDENDUM §A: ``r`` with the state block ``S`` projected out.

    A DIAGNOSTIC PROJECTION, not a proposed mechanism — nothing here proposes removing a
    term from the model. Linear in ``r``, so it preserves the PREREG §2 decomposition.
    """
    A = _design(S, len(r))
    return r - A @ np.linalg.lstsq(A, r, rcond=None)[0]


def _z(a: np.ndarray) -> np.ndarray:
    """Z-score a regressor column; a constant column becomes zeros."""
    s = float(a.std())
    return (a - a.mean()) / s if s > 0 else np.zeros_like(a)


def gamma(r: np.ndarray, s_own: np.ndarray) -> float:
    """miso-237's ``own_net_load_coef_resid_*`` — the PARTIAL OLS coefficient on own net load.

    The slope on ``z_own_net_load`` in ``r ~ [1 | z_own_net_load | z_own_VRE]``, i.e. holding
    own VRE fixed. Byte-for-byte miso-237's estimator
    (``_miso237_price_representation_vs_state_phase0.py`` lines 543-558); the ADDENDUM
    ``ADDENDUM-miso238-gate-repair-and-the-partial-coefficient-2026-09-07.md`` records that
    the PREREG named a simple covariance here, that provenance leg G-P2 caught it at
    457.126 MW/z against a 0.5 bar before any adjudicating quantity was read, and that the
    repair moves no bar.

    ``e1' (X'X)^-1 X' r`` with ``X = [1 | S_own]`` fixed across channels is **linear in r**,
    exactly as a covariance is, so the PREREG §2 decomposition stays exact.
    """
    A = _design(s_own, len(r))
    return float(np.linalg.lstsq(A, r, rcond=None)[0][1])


def gamma_marginal(r: np.ndarray, z_nl: np.ndarray) -> float:
    """``cov(r, z_own_net_load)`` — the MARGINAL coefficient, REPORTED NOT GATED.

    The statistic the PREREG originally named. Reported beside :func:`gamma` per the
    ADDENDUM §2 disclosure so the size of the correction is visible rather than asserted; no
    bar attaches to it and no verdict is read on it.
    """
    return float(((r - r.mean()) * (z_nl - z_nl.mean())).mean())


def align_num(r: np.ndarray, p: np.ndarray) -> float:
    """``cov(r, P)/sigma(P)`` in MW — the additive numerator of ``|corr(r, P)|``.

    ``|corr|`` is not additive across channels; this is, and ``|corr| = |a|/sigma(r)``
    recovers the published statistic (PREREG §4).
    """
    sp = float(p.std())
    return float(((r - r.mean()) * (p - p.mean())).mean() / sp) if sp > 0 else 0.0


def corr_abs(a: np.ndarray, b: np.ndarray) -> float:
    """``|corr(a, b)|``, the miso-235 §4b / miso-237 ADDENDUM §A alignment statistic."""
    sa, sb = float(a.std()), float(b.std())
    if sa <= 0 or sb <= 0:
        return 0.0
    return abs(float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb)))


def hour_index(local_end: pd.Series) -> np.ndarray:
    """Hour-ending local wall clock -> the lane's fixed non-leap hour-of-year index.

    Identical construction to ``derive_miso_seam_ladders.load_joined`` and to
    ``_miso236``/``_miso237``'s ``hour_index``.
    """
    t = pd.to_datetime(local_end) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    hr = np.where((t.dt.month == 2) & (t.dt.day == 29), -1, hr)
    return hr


_FUEL = {
    "wind": lambda c: c.startswith("Net Generation (MW) from Wind"),
    "solar": lambda c: c.startswith("Net Generation (MW) from Solar"),
}


def load_balance_miso() -> pd.DataFrame:
    """EIA-930 BALANCE 2023-2025, MISO only -> (utc, local, demand, wind, solar).

    Same construction as ``_miso236``/``_miso237``'s ``load_balance`` restricted to the
    MISO row set, which is all this session's own-state block needs; only the
    ``(Adjusted)`` columns are read, never ``(Imputed)``.
    """
    import pyarrow.parquet as pq

    frames = []
    for year in YEARS:
        for half in ("Jan_Jun", "Jul_Dec"):
            path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
            names = set(pq.ParquetFile(path).schema.names)
            fuel = {
                k: [
                    c
                    for c in names
                    if "(Adjusted)" in c and "Imputed" not in c and pred(c)
                ]
                for k, pred in _FUEL.items()
            }
            read = [
                "Balancing Authority",
                "Local Time at End of Hour",
                "UTC Time at End of Hour",
                "Demand (MW) (Adjusted)",
            ] + sorted({c for cols in fuel.values() for c in cols})
            df = pd.read_parquet(path, columns=read)
            df = df[df["Balancing Authority"].astype(str) == "MISO"]
            out = pd.DataFrame(
                {
                    "utc": pd.to_datetime(df["UTC Time at End of Hour"], utc=True),
                    "local": df["Local Time at End of Hour"],
                    "demand": pd.to_numeric(
                        df["Demand (MW) (Adjusted)"], errors="coerce"
                    ),
                }
            )
            for k, cols in fuel.items():
                out[k] = (
                    df[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                    if cols
                    else 0.0
                )
            frames.append(out)
    return pd.concat(frames, ignore_index=True)


def channel_split(
    merit: np.ndarray, band: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """PREREG §2 split of one leg ``sum_k merit[k,t]*band[k,t]`` into its three channels.

    ``merit`` is the (K, T) price indicator and ``band`` the (K, T) envelope weight; both
    means are taken over the same T columns (the ``ok`` hours). Returns
    ``(pure-price, pure-template, interaction)``, whose sum equals the leg up to the
    additive constant ``sum_k mean(merit_k)*mean(band_k)``.
    """
    m_bar = merit.mean(axis=1, keepdims=True)
    b_bar = band.mean(axis=1, keepdims=True)
    m_dev = merit - m_bar
    b_dev = band - b_bar
    return (
        (m_dev * b_bar).sum(0),
        (m_bar * b_dev).sum(0),
        (m_dev * b_dev).sum(0),
    )


def _verdict(shares_env: list[float], shares_merit: list[float], ok_floor: bool) -> str:
    """PREREG §3/§4 decision rule, applied identically to Q-A and Q-B."""
    if not ok_floor:
        return "NOT MEANINGFUL (below the pre-registered absolute floor)"
    if all(s >= CHANNEL_BAR for s in shares_env):
        return "ENVELOPE-DRIVEN"
    if all(s >= CHANNEL_BAR for s in shares_merit):
        return "MERIT-DRIVEN"
    return "MIXED"


def main() -> int:  # noqa: PLR0915 - one linear probe, mirrors the PREREG section order
    from market_sim.data.eia_loader import (
        measured_miso_spp_hub_prices,
        measured_seam_import_envelope,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_MANITOBA_SEAM_SPEC,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    prior235 = json.loads(MISO235.read_text())["years"]
    prior237 = json.loads(MISO237.read_text())["years"]

    bal = load_balance_miso()
    bal["hour"] = hour_index(bal["local"])
    bal["year"] = (pd.to_datetime(bal["local"]) - pd.Timedelta(hours=1)).dt.year
    bal = bal[(bal["hour"] >= 0) & (bal["hour"] < HOURS)]

    report: dict = {
        "probe": (
            "miso-238 phase 0 — MERIT / ENVELOPE / INTERACT attribution of the MISO seam "
            "reconstruction's own-net-load response and residual price alignment"
        ),
        "prereg": (
            "results/calibration/"
            "PREREG-miso238-pjm-seam-channel-attribution-2026-09-07.md"
            " (pushed 0deffdb9)"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "price_basis": (
            "Indiana hub RT builds the ok mask and is the alignment price P; every "
            "regressor and every merit signal is Indiana hub DA"
        ),
        "bars": {
            "tol_sigma_mw": TOL_SIGMA_MW,
            "tol_coef_mw_per_z": TOL_COEF_MW,
            "tol_alignment": TOL_ALIGN,
            "tol_identity_mw": TOL_IDENTITY_MW,
            "channel_bar": CHANNEL_BAR,
            "gamma_floor_mw_per_z": GAMMA_FLOOR_MW,
            "alignment_floor_mw": ALIGN_FLOOR_MW,
        },
        "gated_seam": GATED_SEAM,
        "tranches": SEAM_FLOW_TRANCHES,
        "years": {},
    }

    provenance: dict[str, dict] = {}
    years_out: dict[str, dict] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        p_rt = act[ok]

        def dense(col: str) -> np.ndarray:
            return (
                gy[col]
                .reindex(range(HOURS))
                .interpolate(limit=3)
                .ffill()
                .bfill()
                .to_numpy(float)
            )

        border = dense("pjm_border")
        da = dense("da")
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)

        my = bal[bal["year"] == year].drop_duplicates("hour")

        def miso_series(col: str) -> np.ndarray:
            s = pd.Series(my[col].to_numpy(), index=my["hour"].to_numpy())
            return s.reindex(range(HOURS)).to_numpy(float)

        miso_nl = (miso_series("demand") - miso_series("wind") - miso_series("solar"))[
            ok
        ]
        miso_vre = (miso_series("wind") + miso_series("solar"))[ok]
        z_nl = _z(miso_nl)
        s_own = np.column_stack([z_nl, _z(miso_vre)])

        # Model-side reconstruction — miso-235's four-seam form, unchanged from miso-237.
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        p1_of = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }

        prov: dict[str, dict] = {}
        seams_out: dict[str, dict] = {}

        for seam in FOUR_SEAM:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                in_merit = (pb - border)[None, :] > d[:, None]
            elif seam == "SPP":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ],
                    float,
                )
                in_merit = (pb - spp_hub)[None, :] > d[:, None]
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = pb[None, :] > lad[:, None]
            band_i = np.clip(
                np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width
            )
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            in_merit_e = pb[None, :] < lade[:, None]
            band_e = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )

            # Restrict every (K, HOURS) array to the ok hours BEFORE any mean is taken,
            # so channel means are over exactly the rows every statistic uses.
            mi = in_merit[:, ok].astype(float)
            bi = band_i[:, ok]
            me = in_merit_e[:, ok].astype(float)
            be = band_e[:, ok]

            imp = (mi * bi).sum(0)
            exp_ = (me * be).sum(0)
            model_net = imp - exp_
            meas_net = dense(seam)[ok]

            imp_merit, imp_env, imp_int = channel_split(mi, bi)
            exp_merit, exp_env, exp_int = channel_split(me, be)
            chan = {
                "MERIT": imp_merit - exp_merit,
                "ENVELOPE": imp_env - exp_env,
                "INTERACT": imp_int - exp_int,
            }
            legs = {
                "MERIT_import": imp_merit,
                "MERIT_export": -exp_merit,
                "ENVELOPE_import": imp_env,
                "ENVELOPE_export": -exp_env,
                "INTERACT_import": imp_int,
                "INTERACT_export": -exp_int,
            }

            # ---- G-ID: the decomposition identity, to machine precision ----
            total = chan["MERIT"] + chan["ENVELOPE"] + chan["INTERACT"]
            resid_id = total - model_net
            identity_max_abs = float(np.abs(resid_id - resid_id.mean()).max())

            p1s = p1_of[seam][ok]
            r_meas = ols_resid(meas_net, p1s)
            r_model = ols_resid(model_net, p1s)

            # ---- G-P1 / G-P2 / G-P3 ----
            ref235 = prior235[str(year)]["decomposition"][seam]
            ref237 = prior237[str(year)]["seams"][seam]
            r237 = ref237["own_state_reported"]
            a237 = ref237["own_state_purge_addendum_A"]
            g_model = gamma(r_model, s_own)
            g_meas = gamma(r_meas, s_own)
            rm_p = purge(r_model, s_own)
            rx_p = purge(r_meas, s_own)
            align = {
                "alignment_model": corr_abs(r_model, p_rt),
                "alignment_model_purged": corr_abs(rm_p, p_rt),
                "alignment_measured": corr_abs(r_meas, p_rt),
                "alignment_measured_purged": corr_abs(rx_p, p_rt),
            }
            prov[seam] = {
                "sigma_measured_mw": round(float(meas_net.std()), 1),
                "sigma_measured_mw_miso235": ref235["sigma_measured_mw"],
                "sigma_resid_measured_mw": round(float(r_meas.std()), 1),
                "sigma_resid_measured_mw_miso235": ref235["sigma_resid_measured_mw"],
                "max_abs_delta_sigma_mw": round(
                    max(
                        abs(float(meas_net.std()) - ref235["sigma_measured_mw"]),
                        abs(float(r_meas.std()) - ref235["sigma_resid_measured_mw"]),
                    ),
                    3,
                ),
                "own_net_load_coef_resid_model": round(g_model, 2),
                "own_net_load_coef_resid_model_miso237": r237[
                    "own_net_load_coef_resid_model"
                ],
                "own_net_load_coef_resid_measured": round(g_meas, 2),
                "own_net_load_coef_resid_measured_miso237": r237[
                    "own_net_load_coef_resid_measured"
                ],
                "max_abs_delta_coef_mw_per_z": round(
                    max(
                        abs(g_model - float(r237["own_net_load_coef_resid_model"])),
                        abs(g_meas - float(r237["own_net_load_coef_resid_measured"])),
                    ),
                    3,
                ),
                "alignment": {k: round(v, 4) for k, v in align.items()},
                "alignment_miso237": {k: a237[k] for k in align},
                "max_abs_delta_alignment": round(
                    max(abs(align[k] - float(a237[k])) for k in align), 5
                ),
                "identity_max_abs_mw": float(f"{identity_max_abs:.3e}"),
            }

            # ---- Q-A: the own-net-load response, decomposed ----
            r_chan = {c: ols_resid(chan[c], p1s) for c in CHANNELS}
            r_legs = {k: ols_resid(v, p1s) for k, v in legs.items()}
            g_chan = {c: gamma(r_chan[c], s_own) for c in CHANNELS}
            g_legs = {k: gamma(v, s_own) for k, v in r_legs.items()}
            share_g = (
                {c: g_chan[c] / g_model for c in CHANNELS}
                if abs(g_model) > 0
                else dict.fromkeys(CHANNELS, float("nan"))
            )

            # ---- Q-B: the alignment numerator, decomposed, raw and purged ----
            a_model = align_num(r_model, p_rt)
            a_meas = align_num(r_meas, p_rt)
            a_model_p = align_num(rm_p, p_rt)
            a_meas_p = align_num(rx_p, p_rt)
            a_chan = {c: align_num(r_chan[c], p_rt) for c in CHANNELS}
            a_chan_p = {c: align_num(purge(r_chan[c], s_own), p_rt) for c in CHANNELS}
            a_legs_p = {k: align_num(purge(v, s_own), p_rt) for k, v in r_legs.items()}
            share_a_p = (
                {c: a_chan_p[c] / a_model_p for c in CHANNELS}
                if abs(a_model_p) > 0
                else dict.fromkeys(CHANNELS, float("nan"))
            )

            # ---- Q-A' (PREREG §3a): the saturation census, reported not gated ----
            n_merit = mi.sum(0)
            sat = n_merit >= SEAM_FLOW_TRANCHES
            top = z_nl >= np.quantile(z_nl, 0.9)
            envs = np.asarray(env_i[seam], float)[ok]
            census = {
                "sat_share": round(float(sat.mean()), 4),
                "sat_share_top_decile_own_net_load": round(float(sat[top].mean()), 4),
                "mean_z_own_net_load_saturated": (
                    round(float(z_nl[sat].mean()), 3) if sat.any() else None
                ),
                "mean_z_own_net_load_unsaturated": (
                    round(float(z_nl[~sat].mean()), 3) if (~sat).any() else None
                ),
                "mean_bands_in_merit": round(float(n_merit.mean()), 3),
                "corr_env_import_own_net_load": round(
                    float(np.corrcoef(envs, z_nl)[0, 1]), 4
                ),
                "corr_env_import_price_rt": round(
                    float(np.corrcoef(envs, p_rt)[0, 1]), 4
                ),
                "env_import_mean_mw": round(float(envs.mean()), 1),
                "env_import_mean_mw_top_decile_own_net_load": round(
                    float(envs[top].mean()), 1
                ),
            }

            seams_out[seam] = {
                "sigma_model_recon_mw": round(float(model_net.std()), 1),
                "sigma_measured_mw": round(float(meas_net.std()), 1),
                "identity_max_abs_mw": float(f"{identity_max_abs:.3e}"),
                "own_net_load_response": {
                    "gamma_model_mw_per_z": round(g_model, 2),
                    "gamma_measured_mw_per_z": round(g_meas, 2),
                    "gamma_marginal_model_mw_per_z": round(
                        gamma_marginal(r_model, z_nl), 2
                    ),
                    "gamma_marginal_measured_mw_per_z": round(
                        gamma_marginal(r_meas, z_nl), 2
                    ),
                    "by_channel": {c: round(g_chan[c], 2) for c in CHANNELS},
                    "share_of_model": {c: round(share_g[c], 3) for c in CHANNELS},
                    "share_envelope_plus_interact": round(
                        share_g["ENVELOPE"] + share_g["INTERACT"], 3
                    ),
                    "by_leg": {k: round(v, 2) for k, v in g_legs.items()},
                },
                "price_alignment": {
                    "a_model_mw": round(a_model, 1),
                    "a_measured_mw": round(a_meas, 1),
                    "a_model_purged_mw": round(a_model_p, 1),
                    "a_measured_purged_mw": round(a_meas_p, 1),
                    "corr_abs_model": round(align["alignment_model"], 4),
                    "corr_abs_model_purged": round(align["alignment_model_purged"], 4),
                    "corr_abs_measured": round(align["alignment_measured"], 4),
                    "corr_abs_measured_purged": round(
                        align["alignment_measured_purged"], 4
                    ),
                    "a_by_channel_raw_mw": {c: round(a_chan[c], 1) for c in CHANNELS},
                    "a_by_channel_purged_mw": {
                        c: round(a_chan_p[c], 1) for c in CHANNELS
                    },
                    "share_of_model_purged": {
                        c: round(share_a_p[c], 3) for c in CHANNELS
                    },
                    "share_envelope_plus_interact_purged": round(
                        share_a_p["ENVELOPE"] + share_a_p["INTERACT"], 3
                    ),
                    "a_by_leg_purged_mw": {k: round(v, 1) for k, v in a_legs_p.items()},
                },
                "saturation_census_reported_not_gated": census,
            }

        provenance[str(year)] = prov
        years_out[str(year)] = {"seams": seams_out}

    # ---------------- provenance verdicts ----------------
    worst = {
        "G_P1_max_abs_delta_sigma_mw": max(
            provenance[str(y)][s]["max_abs_delta_sigma_mw"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_P2_max_abs_delta_coef_mw_per_z": max(
            provenance[str(y)][s]["max_abs_delta_coef_mw_per_z"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_P3_max_abs_delta_alignment": max(
            provenance[str(y)][s]["max_abs_delta_alignment"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
        "G_ID_max_abs_mw": max(
            provenance[str(y)][s]["identity_max_abs_mw"]
            for y in YEARS
            for s in FOUR_SEAM
        ),
    }
    gate = {
        "G_P1_sigmas_miso235": worst["G_P1_max_abs_delta_sigma_mw"] <= TOL_SIGMA_MW,
        "G_P2_own_net_load_coefs_miso237": (
            worst["G_P2_max_abs_delta_coef_mw_per_z"] <= TOL_COEF_MW
        ),
        "G_P3_alignment_column_miso237": (
            worst["G_P3_max_abs_delta_alignment"] <= TOL_ALIGN
        ),
        "G_ID_decomposition_identity": worst["G_ID_max_abs_mw"] <= TOL_IDENTITY_MW,
    }
    gate["ALL_PASS"] = all(gate.values())
    report["provenance_gate"] = {
        "worst_case": worst,
        "legs": gate,
        "by_year": provenance,
    }

    # ---------------- PREREG §3/§4 verdicts ----------------
    verdicts: dict[str, dict] = {}
    for seam in FOUR_SEAM:
        g_env = [
            years_out[str(y)]["seams"][seam]["own_net_load_response"][
                "share_envelope_plus_interact"
            ]
            for y in YEARS
        ]
        g_mer = [
            years_out[str(y)]["seams"][seam]["own_net_load_response"]["share_of_model"][
                "MERIT"
            ]
            for y in YEARS
        ]
        g_abs = [
            abs(
                years_out[str(y)]["seams"][seam]["own_net_load_response"][
                    "gamma_model_mw_per_z"
                ]
            )
            for y in YEARS
        ]
        a_env = [
            years_out[str(y)]["seams"][seam]["price_alignment"][
                "share_envelope_plus_interact_purged"
            ]
            for y in YEARS
        ]
        a_mer = [
            years_out[str(y)]["seams"][seam]["price_alignment"][
                "share_of_model_purged"
            ]["MERIT"]
            for y in YEARS
        ]
        a_abs = [
            abs(
                years_out[str(y)]["seams"][seam]["price_alignment"]["a_model_purged_mw"]
            )
            for y in YEARS
        ]
        verdicts[seam] = {
            "gated": seam == GATED_SEAM,
            "Q_A_own_net_load_response": _verdict(
                g_env, g_mer, all(v >= GAMMA_FLOOR_MW for v in g_abs)
            ),
            "Q_A_shares_envelope_plus_interact": g_env,
            "Q_A_shares_merit": g_mer,
            "Q_B_alignment_remainder": _verdict(
                a_env, a_mer, all(v >= ALIGN_FLOOR_MW for v in a_abs)
            ),
            "Q_B_shares_envelope_plus_interact_purged": a_env,
            "Q_B_shares_merit_purged": a_mer,
        }
    report["verdicts"] = verdicts
    report["years"] = years_out

    OUT.write_text(json.dumps(report, indent=1) + "\n")

    print(f"provenance gate: {gate}")
    print(f"worst case: {worst}")
    if not gate["ALL_PASS"]:
        print("INSTRUMENT BROKEN — PREREG §1 forbids reading anything below.")
        return 1
    for seam in FOUR_SEAM:
        v = verdicts[seam]
        tag = "GATED" if v["gated"] else "reported"
        print(
            f"{seam:9s} [{tag:8s}] Q-A {v['Q_A_own_net_load_response']:<12s} "
            f"env+int {['%.3f' % x for x in v['Q_A_shares_envelope_plus_interact']]} | "
            f"Q-B {v['Q_B_alignment_remainder']:<12s} "
            f"env+int {['%.3f' % x for x in v['Q_B_shares_envelope_plus_interact_purged']]}"
        )
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
