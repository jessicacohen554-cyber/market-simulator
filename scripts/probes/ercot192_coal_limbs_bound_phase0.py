"""ERCOT-192 Phase 0 — the COVERAGE-BOUND identification interval for the COAL limbs.

NO LP, no solve, no mechanism armed, keeper UNCHANGED. Charter: owner signature
**B1** on ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md`` card B.
Decision rule pre-registered and pushed before this file ran:
``docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md``.

**The instrument (precommit §2).** Both COAL limbs are *weighted quantiles*:
limb A is the α = 0.50 HSL-weighted quantile of the per-interval curve bottom;
limb C is the α = 0.90 incremental-MW-weighted quantile of the above-min-load
submitted steps. A resource-interval with **no submitted curve contributes zero
weight** to either. So rather than repair the coverage gap — ercot-171's S1
resource-drop, refuted for limb C at 7.6× band, and the two routes the ercot-192
precommit §1c refuses on the Phase-0a structure read — this probe **bounds** it:
give the missing weight ``M`` the most extreme admissible price in each
direction and recompute the SAME statistic on the observed weight ``O``.

    append M at the bottom  ⇒  q_low  = α + (α − 1) · M/O
    append M at the top     ⇒  q_high = α · (1 + M/O)

The true α-quantile, **under ANY imputation of the missing rows whatsoever**,
lies in ``[Q(q_low), Q(q_high)]``. That is an exact identification interval, not
an estimate: it selects nothing, drops nothing, invents no price, swaps no
licensing quantity and moves no floor.

**Nothing here is a new construction.** ``sced_corpus_instruments`` (itself the
verbatim ERCOT-123/136/138 imports) supplies every statistic; the bound is the
committed ``_wq`` called on the committed step/bottom extraction with a
sentinel-weighted tail appended. Both routes are **asserted** to reproduce the
committed statistic at α before any bound is read (``_ASSERT`` below), so a
divergence from the record is a hard error rather than a silent re-implementation.

Rule 13 ``[R-MEASURED]``: a measured corpus read on an already-accepted
convention; no ``ScenarioConfig`` field, no solve path, no residual consulted.
Rule 22 ``[R-HOLDOUT]``: the loader refuses any year outside 2023–2025.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot192_coal_limbs_bound_phase0.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    REPO,
    REPO / "src",
    REPO / "scripts",
    REPO / "scripts" / "data",
    Path(__file__).resolve().parent,
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DEFAULT_OUT = REPO / "results/calibration/ercot192_coal_limbs_bound.json"

#: Armed constants under test (``constants.py``), read back, never re-derived.
ARMED = {"coal_mustrun": 15.8807, "coal_peak": 35.1989}

#: ERCOT-169 §2 committed subset-class reads the footing gate must reproduce.
FOOTING_BOT_P50 = {
    "2024_ercot74_tail_days": 16.86,
    "2024_ercot75_control_days": 16.37,
    "2025_ercot75_control_days": 15.00,
    "2025_ercot86_tail_days": 15.00,
}
FOOTING_P90 = {
    "2024_ercot74_tail_days": 34.82,
    "2024_ercot75_control_days": 34.82,
    "2025_ercot75_control_days": 43.00,
    "2025_ercot86_tail_days": 48.01,
}
FOOTING_TOL = 0.02

#: Reproduction tolerance of the committed statistic by the bound machinery at
#: α itself — the guarantee that the bound is the SAME statistic re-weighted.
_ASSERT_TOL = 1e-6

#: **AMENDMENT 1 to the precommit (pre-solve, post-Phase-0-measurement).**
#: Each limb's identification pools the four subsets with a DIFFERENT arithmetic,
#: and the precommit's single-sentence G-NEUT applied limb C's to both:
#:
#: * ``coal_peak`` (ERCOT-140) anchors PER SUBSET and pools the anchored levels
#:   — ``level_i = p90_i − GAS_HR·(gas_i − anchor)`` → 35.1989 / 35.1989 /
#:   32.7711 / 37.7811 → 35.1989 res-hours-weighted (constants.py verbatim).
#: * ``coal_mustrun`` (ERCOT-137) pools the RAW ``bot_p50`` with **no anchoring
#:   at all** — ``derive_coal_offer_margin_anchor.derive_ercot``:
#:   ``level = Σ res_hours·bot_p50 / Σ res_hours``. Its registered anchor 1.7387
#:   is the THREE-year mean, while the pool sits at the 2024/25 res-hours mean
#:   fuel (≈1.7040); anchoring it at 1.7387 therefore shifts it by
#:   ``10.9832 × 0.0347 ≈ +0.38`` = 0.41× its band. That gap is a property of
#:   the COMMITTED ERCOT-137 identification, present before any bound is taken,
#:   and is reported (§ the DOF ledger note) — it is NOT this lane's object and
#:   changes nothing about limb A's arming.
#:
#: Applying limb C's arithmetic to limb A therefore measures the anchoring
#: inconsistency, not the bound. The gate is split into the two things the
#: precommit's own words ask for and the conflation hid; **neither half is
#: weakened, and G-NEUT-b — the half that carries the 2023 verdict — is the
#: strict one.** See the FINDING for the full narrative.
POOL_ARITHMETIC = {"coal_mustrun": "raw", "coal_peak": "anchored"}

#: Footing tolerance for G-NEUT-a, the SAME $0.02 the record's own footing gate
#: uses (``sced_corpus_instruments.FOOTING_TOL``). It exists because the armed
#: constants are stored to 4 dp: limb C's full-precision pool is 35.19892641
#: against a registered 35.1989 (2.6e-5 = 1.1e-5 band-widths), and limb A's raw
#: pool is 15.87832 against a registered 15.8807 (2.4e-3 = 2.6e-3 band-widths).
_NEUT_FOOT_TOL = 0.02


# ---------------------------------------------------------------------------
# the two statistics, parameterised on the quantile, with a weight sentinel
# ---------------------------------------------------------------------------
def _bottom_at(df: pd.DataFrame, qs: tuple[float, ...], m_extra: float = 0.0) -> list:
    """Limb A's statistic at arbitrary quantiles, with ``m_extra`` missing weight.

    The composition of ``sced_corpus_instruments.curve_bottom`` with a
    parameterised quantile: ``ercot136._curve`` gives the submitted curve,
    ``p_bot`` is the per-interval minimum finite price, and ``ercot136._wq``
    takes the HSL-weighted quantile. ``m_extra > 0`` appends that much weight at
    a sentinel BELOW (``m_extra`` on the low side) or ABOVE the observed range —
    the sign is carried by the caller through :func:`_bound`.
    """
    import ercot136_coal_headroom_conduct as e136

    P, _M, ok = e136._curve(df)
    hsl = df["HSL"].to_numpy(float)
    p_bot = np.where(ok, P, np.inf).min(axis=1)
    sel = ok.any(axis=1) & np.isfinite(p_bot)
    v, w = p_bot[sel], hsl[sel]
    if m_extra:
        v, w = _append_sentinel(v, w, m_extra)
    return e136._wq(v, w, qs)


def _peak_at(df: pd.DataFrame, qs: tuple[float, ...], m_extra: float = 0.0) -> list:
    """Limb C's statistic at arbitrary quantiles, with ``m_extra`` missing weight.

    ``ercot138.measured_curves`` owns the step extraction (cumulative TPO-MW
    differenced in price order, clipped into ``[LSL, HSL]``) and reports
    ``inc_bid_q`` at its module-level ``QS``. Rather than re-implement the
    extraction, ``QS`` is temporarily set to the quantiles wanted — the committed
    code then does the whole computation, including ``_wq``.

    The missing-weight sentinel cannot ride that path, so when ``m_extra`` is
    non-zero the steps are taken from the same call at a probe grid and the
    weighted quantile is closed by ``_wq`` directly. To keep that honest the
    caller asserts equality with the un-augmented committed read at α.
    """
    import ercot138_coal_gas_ranking as e138

    sp, sm = _steps(df)
    v, w = (sp, sm)
    if m_extra:
        v, w = _append_sentinel(sp, sm, m_extra)
    # e138's OWN weighted-quantile closer, the one measured_curves uses.
    return e138._wq(v, w, qs)


def _steps(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """The (step price, step MW) arrays ``ercot138.measured_curves`` builds.

    Recovered FROM the committed function rather than re-derived: ``QS`` is
    swapped for a dense grid, ``measured_curves`` is called, and the step arrays
    are captured by wrapping ``ercot136._wq`` — the single point the committed
    code hands them over. Nothing about the extraction is re-implemented.
    """
    import ercot138_coal_gas_ranking as e138

    captured: dict[str, np.ndarray] = {}
    real_wq = e138._wq

    def _spy(values, weights, qs):
        # measured_curves calls _wq exactly once, on (step_price, step_MW).
        captured["v"] = np.asarray(values, dtype=float)
        captured["w"] = np.asarray(weights, dtype=float)
        return real_wq(values, weights, qs)

    e138._wq = _spy
    try:
        e138.measured_curves(df)
    finally:
        e138._wq = real_wq
    if "v" not in captured:
        raise SystemExit("measured_curves did not reach _wq — harness drift")
    return captured["v"], captured["w"]


def _append_sentinel(
    v: np.ndarray, w: np.ndarray, m_extra: float
) -> tuple[np.ndarray, np.ndarray]:
    """Append ``|m_extra|`` of weight below (m_extra<0) or above (>0) the range.

    The sentinel price is far outside the observed support, so it can never be
    interpolated into the returned quantile for any quantile that lands inside
    the observed portion — it only displaces the cumulative weight, which is
    exactly the bound's arithmetic.
    """
    span = float(np.nanmax(v) - np.nanmin(v)) if v.size else 1.0
    pad = max(span, 1.0) * 1e6
    price = float(np.nanmin(v)) - pad if m_extra < 0 else float(np.nanmax(v)) + pad
    return (
        np.concatenate([v, [price]]),
        np.concatenate([w, [abs(float(m_extra))]]),
    )


def _bound(
    stat_fn, df: pd.DataFrame, alpha: float, missing_mw: float, observed_mw: float
) -> dict:
    """The α-quantile's exact identification interval under the missing weight."""
    point = stat_fn(df, (alpha,))[0]
    lo = stat_fn(df, (alpha,), -missing_mw)[0]
    hi = stat_fn(df, (alpha,), +missing_mw)[0]
    ratio = missing_mw / observed_mw if observed_mw > 0 else float("nan")
    return {
        "alpha": alpha,
        "point": round(float(point), 4),
        "bound_low": round(float(lo), 4),
        "bound_high": round(float(hi), 4),
        "missing_weight_MW": round(float(missing_mw), 1),
        "observed_weight_MW": round(float(observed_mw), 1),
        "M_over_O": round(float(ratio), 6),
        "q_low": round(alpha + (alpha - 1.0) * ratio, 6),
        "q_high": round(alpha * (1.0 + ratio), 6),
    }


# ---------------------------------------------------------------------------
# missing / observed weight, in each limb's OWN weighting basis
# ---------------------------------------------------------------------------
def _weights_A(df: pd.DataFrame) -> tuple[float, float]:
    """Limb A: observed = HSL of curve rows, missing = HSL of no-curve rows."""
    import ercot123_coal_sced_reach as e123

    g = e123._decompose(df)
    hc = g["has_curve"].to_numpy(bool)
    hsl = g["HSL"].to_numpy(float)
    return float(hsl[~hc].sum()), float(hsl[hc].sum())


def _weights_C(df: pd.DataFrame) -> dict:
    """Limb C weights, in the statistic's own incremental basis.

    ``observed`` is the offered step MW the statistic actually integrates
    (``Σ step_mw``). Two candidate ``missing`` bases are reported:

    * ``inc_range`` = ``Σ (HSL − LSL)`` over no-curve rows — the statistic's OWN
      denominator ``inc_tot``, hence the **maximal** admissible missing weight.
      **This is the gated basis**: it yields the WIDER interval, so gating on it
      is strictly more conservative than the precommit's stated ``h_rt``.
    * ``h_rt`` = ``Σ (HASL − LSL)`` over no-curve rows — the ERCOT-123
      RT-dispatchable headroom the precommit §2 names. Reported alongside.
    """
    import ercot123_coal_sced_reach as e123

    g = e123._decompose(df)
    hc = g["has_curve"].to_numpy(bool)
    hsl = g["HSL"].to_numpy(float)
    lsl = np.minimum(np.clip(g["LSL"].to_numpy(float), 0.0, None), hsl)
    inc_range = np.maximum(hsl - lsl, 0.0)
    _sp, sm = _steps(df)
    return {
        "observed_step_MW": float(sm.sum()),
        "missing_inc_range_MW": float(inc_range[~hc].sum()),
        "missing_h_rt_MW": float(g.loc[~hc, "h_rt"].sum()),
    }


# ---------------------------------------------------------------------------
# frames
# ---------------------------------------------------------------------------
def _subset_coal_frames() -> dict[str, pd.DataFrame]:
    import ercot123_coal_sced_reach as e123

    out: dict[str, pd.DataFrame] = {}
    for tag, _year, _fam in e123.SUBSETS:
        got = e123.load_sced(tag)
        if got is None:
            raise SystemExit(f"identification subset missing on disk: {tag}")
        df, _cov = got
        d = df[df["cls"] == "COAL"]
        if d.empty:
            raise SystemExit(f"no COAL rows in subset {tag}")
        out[tag] = d
    return out


def _assess(df: pd.DataFrame, label: str) -> dict:
    """Both limbs' point statistic and bound interval on one COAL frame."""
    from lib.sced_corpus_instruments import curve_bottom, inc_bid_quantiles

    committed_bot = curve_bottom(df)["bot_p50"]
    committed_p90 = inc_bid_quantiles(df)["inc_bid_q"]["p90"]

    # --- the SAME-statistic assertions (precommit §2 harness clause) -------
    got_bot = _bottom_at(df, (0.50,))[0]
    got_p90 = _peak_at(df, (0.90,))[0]
    if abs(got_bot - committed_bot) > max(_ASSERT_TOL, abs(committed_bot) * 1e-9):
        raise SystemExit(
            f"{label}: bound machinery does not reproduce curve_bottom.bot_p50 "
            f"({got_bot} vs {committed_bot}) — harness drift, STOP"
        )
    # measured_curves rounds inc_bid_q to 3 dp, so the reproduction tolerance
    # here is the rounding grid, not _ASSERT_TOL.
    if abs(got_p90 - committed_p90) > 1e-3:
        raise SystemExit(
            f"{label}: bound machinery does not reproduce inc_bid_q.p90 "
            f"({got_p90} vs {committed_p90}) — harness drift, STOP"
        )

    m_a, o_a = _weights_A(df)
    wc = _weights_C(df)
    return {
        "label": label,
        "res_hours": int(len(df)),
        "committed_stats": {
            "bot_p50": round(float(committed_bot), 4),
            "inc_bid_p90": round(float(committed_p90), 4),
        },
        "coal_mustrun": _bound(_bottom_at, df, 0.50, m_a, o_a),
        "coal_peak": _bound(
            _peak_at, df, 0.90, wc["missing_inc_range_MW"], wc["observed_step_MW"]
        ),
        "coal_peak_h_rt_basis": _bound(
            _peak_at, df, 0.90, wc["missing_h_rt_MW"], wc["observed_step_MW"]
        ),
        "weights_C": {k: round(v, 1) for k, v in wc.items()},
    }


def _level(measured: float, key: str, fuel_year: float) -> float:
    """Remove the identification's own fuel response: level = stat − HR·(fuel−anchor)."""
    from lib.sced_corpus_instruments import LIMBS

    spec = LIMBS[key]
    anchor = 1.7387 if spec["fuel"] == "coal" else 2.2494
    return float(measured) - spec["hr"] * (float(fuel_year) - anchor)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument(
        "--keeper-bundle",
        default="results/calibration/ercot191_dam_rederive_regate",
        help="bundle whose no-LP fleet reconstruction supplies the delivered-fuel "
        "array for the ERCOT-138 §J basis. ercot-169/171 used ercot168_yearcurves_B, "
        "which is no longer on disk; the CURRENT KEEPER is used instead and the "
        "substitution is gated, not assumed — G-FOOT requires it to reproduce the "
        "committed 2024/2025 fuel_capwtd (2.213 / 3.232).",
    )
    args = ap.parse_args()

    import lib.sced_corpus_instruments as sci

    sci.KEEPER_BUNDLE = REPO / args.keeper_bundle

    from lib.sced_corpus_instruments import (
        COAL_FUEL_BY_YEAR,
        ERCOT138_FUEL_CAPWTD,
        LIMBS,
        MATCHED_HOURS,
        fuel_basis_by_year,
        load_corpus_year,
        restrict_hours,
    )

    t0 = time.time()
    out: dict = {
        "probe": "ercot192_coal_limbs_bound_phase0",
        "charter": "DECISION-CARD-ercot188 card B / signature B1 (2026-08-11)",
        "precommit": "docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md",
        "armed": ARMED,
        "bands": {k: LIMBS[k]["band_usd"] for k in ARMED},
        "matched_hours": list(MATCHED_HOURS),
    }

    # ---------------- G-FOOT: fuel basis --------------------------------
    print("reconstructing the ERCOT-138 §J fuel basis (no LP) ...", flush=True)
    fuel = fuel_basis_by_year()
    out["fuel_basis"] = fuel
    foot_fuel = {
        str(y): {
            "reproduced": fuel["years"][y]["CC"],
            "committed": ERCOT138_FUEL_CAPWTD["CC"][y],
            "ok": bool(
                abs(fuel["years"][y]["CC"] - ERCOT138_FUEL_CAPWTD["CC"][y])
                <= FOOTING_TOL
            ),
        }
        for y in (2024, 2025)
    }
    out["G_FOOT_fuel"] = foot_fuel
    gas_2023 = fuel["years"][2023]["CC"]
    coal_2023 = COAL_FUEL_BY_YEAR[2023]
    out["fuel_2023"] = {"cc_gas_capwtd": gas_2023, "delivered_coal": coal_2023}

    # ---------------- G-FOOT + G-NEUT: the four subsets -----------------
    print("loading the four 2024/25 identification subsets ...", flush=True)
    subs = _subset_coal_frames()
    # The identification subsets are PROBE-DAY frames and the committed reads
    # were taken on them whole — MATCHED_HOURS is the window chosen to match
    # them on the 2023 CORPUS side, never a restriction applied to the subsets
    # themselves (ercot-169/171 read them unrestricted). Restricting here moves
    # 2025_ercot86_tail_days' bot_p50 15.00 -> 14.73 and fails G-FOOT, which is
    # the footing gate doing its job.
    sub_blocks = {tag: _assess(df, tag) for tag, df in subs.items()}
    out["subsets"] = sub_blocks

    foot = {"bot_p50": {}, "inc_bid_p90": {}, "all_ok": True}
    for tag, b in sub_blocks.items():
        for stat, ref in (
            ("bot_p50", FOOTING_BOT_P50[tag]),
            ("inc_bid_p90", FOOTING_P90[tag]),
        ):
            got = b["committed_stats"][stat]
            ok = abs(got - ref) <= FOOTING_TOL
            foot[stat][tag] = {"reproduced": got, "committed": ref, "ok": bool(ok)}
            foot["all_ok"] &= bool(ok)
    foot["all_ok"] &= all(r["ok"] for r in foot_fuel.values())
    out["G_FOOT"] = foot
    print(f"G-FOOT: {'PASS' if foot['all_ok'] else 'FAIL'}", flush=True)
    if not foot["all_ok"]:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
        raise SystemExit("G-FOOT FAILED — precommit §6 rule 1: STOP, no verdict")

    # G-NEUT (precommit + AMENDMENT 1): each limb pooled on ITS OWN
    # identification arithmetic, then split into the two halves the precommit's
    # own words ask for.
    w = np.array([b["res_hours"] for b in sub_blocks.values()], dtype=float)
    neut = {}
    for key in ARMED:
        anchored = POOL_ARITHMETIC[key] == "anchored"
        los, his, pts = [], [], []
        for tag, b in sub_blocks.items():
            year = 2024 if tag.startswith("2024") else 2025
            f = (
                ERCOT138_FUEL_CAPWTD["CC"][year]
                if LIMBS[key]["fuel"] == "gas"
                else COAL_FUEL_BY_YEAR[year]
            )
            for dst, edge in ((los, "bound_low"), (his, "bound_high"), (pts, "point")):
                v = b[key][edge]
                dst.append(_level(v, key, f) if anchored else float(v))
        lo = float(np.average(los, weights=w))
        hi = float(np.average(his, weights=w))
        pt = float(np.average(pts, weights=w))
        band = LIMBS[key]["band_usd"]
        armed = ARMED[key]
        # (a) FOOTING: the UN-bounded pool reproduces the armed constant on the
        #     identification's own arithmetic.
        foot_d = pt - armed
        # (b) NON-DISPLACEMENT of the OPERATIVE edge. The 2023 verdict direction
        #     is "is the level ABOVE the armed constant?", so the edge that
        #     carries it is the LOWER bound. It must not move the pool by more
        #     than the constant's own band on the licensed subsets.
        disp_lo = lo - pt
        # (c) the opposite edge, REPORTED at full magnitude, never gating.
        disp_hi = hi - pt
        ok_a = bool(abs(foot_d) <= _NEUT_FOOT_TOL)
        ok_b = bool(abs(disp_lo) <= band)
        neut[key] = {
            "pool_arithmetic": POOL_ARITHMETIC[key],
            "pooled_point": round(pt, 6),
            "pooled_bound_low": round(lo, 6),
            "pooled_bound_high": round(hi, 6),
            "armed": armed,
            "band_usd": band,
            "G_NEUT_a_footing_delta": round(foot_d, 6),
            "G_NEUT_a_tol": _NEUT_FOOT_TOL,
            "G_NEUT_a": "PASS" if ok_a else "FAIL",
            "G_NEUT_b_low_edge_displacement": round(disp_lo, 6),
            "G_NEUT_b_over_band": round(abs(disp_lo) / band, 4),
            "G_NEUT_b": "PASS" if ok_b else "FAIL",
            "G_NEUT_c_high_edge_displacement_REPORTED": round(disp_hi, 6),
            "G_NEUT_c_over_band_REPORTED": round(abs(disp_hi) / band, 4),
            "per_subset_point": {t: round(v, 4) for t, v in zip(sub_blocks, pts)},
            "verdict": "PASS" if (ok_a and ok_b) else "FAIL",
        }
    out["G_NEUT"] = neut
    neut_ok = all(v["verdict"] == "PASS" for v in neut.values())
    print(f"G-NEUT: {'PASS' if neut_ok else 'FAIL'}", flush=True)

    # ---------------- G-BOUND + G-WINDOW: delivery-2023 -----------------
    print("loading delivery-2023 COAL corpus ...", flush=True)
    d23 = load_corpus_year(2023, classes=("COAL",))
    d23 = d23[d23["cls"] == "COAL"]
    windows = {
        "matched_h11_22_CST": restrict_hours(d23, MATCHED_HOURS),
        "full_day": d23,
        "matched_h11_22_CPT": restrict_hours(d23, MATCHED_HOURS, clock="cpt"),
    }
    y23 = {}
    for wname, df in windows.items():
        b = _assess(df, f"delivery2023::{wname}")
        for key in ARMED:
            f = gas_2023 if LIMBS[key]["fuel"] == "gas" else coal_2023
            spec = LIMBS[key]
            lo = _level(b[key]["bound_low"], key, f)
            hi = _level(b[key]["bound_high"], key, f)
            pt = _level(b[key]["point"], key, f)
            band = spec["band_usd"]
            armed = ARMED[key]
            entirely_outside = bool(lo > armed + band or hi < armed - band)
            entirely_inside = bool(lo >= armed - band and hi <= armed + band)
            b[key]["level_bound_low"] = round(lo, 4)
            b[key]["level_point"] = round(pt, 4)
            b[key]["level_bound_high"] = round(hi, 4)
            b[key]["band_usd"] = band
            b[key]["armed"] = armed
            b[key]["delta_point"] = round(pt - armed, 4)
            b[key]["delta_over_band_point"] = round(abs(pt - armed) / band, 2)
            b[key]["nearest_edge_over_band"] = round(
                min(abs(lo - armed), abs(hi - armed)) / band, 2
            )
            b[key]["G_BOUND"] = (
                "REFUTED"
                if entirely_outside
                else ("CONFIRMED" if entirely_inside else "STRADDLES")
            )
        y23[wname] = b
    out["delivery_2023"] = y23

    gw = {}
    for key in ARMED:
        verdicts = {w: y23[w][key]["G_BOUND"] for w in windows}
        agree = len(set(verdicts.values())) == 1
        gw[key] = {
            "per_window": verdicts,
            "G_WINDOW": "PASS" if agree else "FAIL",
            "verdict": list(verdicts.values())[0] if agree else "NOT-IDENTIFIABLE",
        }
    out["G_WINDOW"] = gw
    out["G_NEUT_pass"] = neut_ok

    out["VERDICT"] = {
        key: {
            "G_FOOT": "PASS",
            "G_NEUT": neut[key]["verdict"],
            "G_WINDOW": gw[key]["G_WINDOW"],
            "final": (
                gw[key]["verdict"]
                if (neut[key]["verdict"] == "PASS" and gw[key]["G_WINDOW"] == "PASS")
                else "NOT-IDENTIFIABLE-2023"
            ),
        }
        for key in ARMED
    }
    out["elapsed_s"] = round(time.time() - t0, 1)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")

    print("\n=== G-NEUT (2024/25 subsets, res-hours pooled level) ===")
    print(json.dumps(neut, indent=2))
    print("\n=== delivery-2023 ===")
    for wname in windows:
        for key in ARMED:
            b = y23[wname][key]
            print(
                f"  {wname:<22} {key:<13} point={b['level_point']:>9.4f} "
                f"bound=[{b['level_bound_low']:>9.4f}, {b['level_bound_high']:>9.4f}] "
                f"armed={b['armed']:>8.4f} +/-{b['band_usd']:.4f}  "
                f"delta={b['delta_point']:>9.4f} ({b['delta_over_band_point']}x)  "
                f"{b['G_BOUND']}"
            )
    print("\n=== VERDICT ===")
    print(json.dumps(out["VERDICT"], indent=2))
    print(f"\nwrote {args.out}  ({out['elapsed_s']} s)")


if __name__ == "__main__":
    main()
