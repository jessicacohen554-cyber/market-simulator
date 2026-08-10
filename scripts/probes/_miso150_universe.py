"""miso-150 probe — the MODEL-SIDE UNIVERSE FIX (§5.4 MISO queue, item 8). **NO LP.**

Adjudicates PREREG ``results/calibration/PREREG-miso150-model-side-universe-2026-08-10.md``
(pushed at ``79f2e90c``, blob verified against the fetched remote ref, BEFORE this
script was written).

THE OBJECT
----------
miso-145 measured MISO's real submitted offer book against the model's own offer
stack on **asymmetric universes**: the book carries its VRE at <= $0, while the
model's wind and solar are LP decision variables absent from the model-side
curve entirely.  miso-146 §8(a) REFUTED subtracting VRE from the corpus and
named the fix — **add the model's own VRE to the model's curve at its own offer
price**.  This builds it.

Four model-side universes, one real side, everything else miso-145's verbatim:

``U0``   fleet generator rows only (miso-145's construction, re-based).
``U1``   U0 + the model's VRE at ``wind_mc``/``solar_mc`` — the charter's fix.
``U1S``  U1 + storage discharge capability at the storage tiebreaker epsilon —
         the model's COMPLETE offerable universe, hence the UPPER BOUND on any
         foot-addition correction.
``U4``   U1 minus the model's import tranches — the residual asymmetry miso-146
         requires be stated (no analogue in a book of MISO-internal resources).

``U2`` is a LOCATOR, never load-bearing (PREREG §3): U1 with the model's VRE
truncated per hour to the intermittent MW miso-146's screen identifies in the
book, evaluated across that screen's own swept thresholds.

WHAT IS REUSED VERBATIM, NEVER RE-DERIVED
-----------------------------------------
``_miso145_offer_conduct`` (``load_real_segments``, ``curve_readings``,
``price_at_pctl``, ``price_at_cum``, ``model_block``), ``_miso143_stack``
(``fleet_state``, ``hygiene``, ``klass_of``, ``markup_ceiling``, ``windows``,
``sidecar_price``), ``_miso146_intermittent_screen`` (``load_declarations``,
``unit_features``, ``classify``) for the U2 locator only.

The renewable offer prices come from ``run_year``'s own ``fleet_only`` exit
(``wind_mc``/``solar_mc``, added there by this session) — the assembled arrays
the LP is handed, never a re-derivation of the credit sequence outside the
orchestrator (the failure mode ``_miso143_stack``'s docstring names).

THE KEEPER-POINTER SEAM (PREREG TRAP-6)
---------------------------------------
``_miso143_stack.KEEPER`` is hard-coded to the SUPERSEDED ``miso132_ccmin_B``.
The footing runs at that pointer and must reproduce miso-145's committed
artifact; only then is the pointer moved to the CURRENT keeper
``miso148_basis_B`` for the new measurement, saved and restored around every
call.  **Every Delta this probe reports is U-arm-vs-U0 on ONE keeper.**

Usage::

    python scripts/probes/_miso150_universe.py --footing   # G-F0/G-F0b/G-F1 only
    python scripts/probes/_miso150_universe.py             # footing, then measure
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

# TRAP-7: _miso147_strata._cache_dir() writes into the CWD (Path("") is truthy).
# This probe never inherits the miso-147/149 caches -- a different keeper.
os.environ.setdefault("MISO150_CACHE", str(Path("/tmp") / "_miso150_cache"))

import _miso143_stack as stack  # noqa: E402
import _miso145_offer_conduct as oc  # noqa: E402

#: PREREG §2 -- the CURRENT keeper. The footing target is stack.KEEPER itself.
KEEPER150 = REPO / "results" / "calibration" / "miso148_basis_B"
OUT = REPO / "results" / "calibration" / "_miso150_universe.json"

#: PREREG §2 -- footing bars, by unit family.
BAR_USD, BAR_GW, BAR_PCTL = 0.01, 0.05, 0.0005

#: Rule 9 [R-EPSILON] -- the storage tiebreaker. U1S prices storage discharge
#: here because the LOWEST admissible placement maximises the foot mass, which
#: is the conservative direction for a quantity used as an UPPER BOUND.
STORAGE_EPSILON = 0.001

#: PREREG §5 -- miso-145's reinstatement bar, the target of the G-4 ceiling.
REINSTATEMENT_BAR_USD = 18.0
#: PREREG §5 / miso-146 EIA-860 control -- MISO VRE nameplate, the G-4 yardstick.
VRE_NAMEPLATE_GW = {2023: 36.380, 2024: 40.794, 2025: 49.747}
#: miso-146's committed model VRE dispatch, 2025 JJA h12-17 (TRAP-4 reference).
MISO146_VRE_DISPATCH_GW = 16.286
#: miso-146's committed import-tranche reconciliation (TRAP-5).
IMPORT_TRANCHES_N, IMPORT_TRANCHES_MW = 32, 17_200.0

UNIVERSES = ("U0", "U1", "U1S", "U4")


# --------------------------------------------------------------- primitives


def seg_mw_between(
    hours: np.ndarray,
    seg_h: np.ndarray,
    seg_p: np.ndarray,
    seg_mw: np.ndarray,
    lo: np.ndarray,
    hi: np.ndarray,
) -> np.ndarray:
    """Per-hour MW priced strictly above ``lo`` and at or below ``hi``.

    The segment-grain twin of ``_miso145_offer_conduct.model_mw_between``.
    G-F0b asserts the two agree exactly on U0, so this path is verified against
    miso-145's own dense construction rather than trusted (PREREG TRAP-1).
    """
    idx = np.searchsorted(hours, seg_h)
    m = (seg_p > lo[idx]) & (seg_p <= hi[idx])
    return np.bincount(idx[m], weights=seg_mw[m], minlength=hours.size)


class CurvePack:
    """One price-sorted curve per hour, sorted ONCE.

    ``price_at_pctl`` re-``lexsort``s its whole segment set on every call, which
    the G-4 bisection would pay ~30 times per cell.  This packs the same
    construction — and gate **G-F0c** measures :meth:`price_at_pctl` against
    ``_miso145_offer_conduct.price_at_pctl`` on the real curve of every
    year x window x market cell, so the speed-up is verified rather than
    asserted (PREREG TRAP-1: machinery that tests an identity must itself be
    checked against the construction it replaces).
    """

    def __init__(self, hours, seg_h, seg_p, seg_mw) -> None:
        order = np.lexsort((seg_p, seg_h))
        h_s, p_s, m_s = seg_h[order], seg_p[order], seg_mw[order]
        i0 = np.searchsorted(h_s, hours, side="left")
        i1 = np.searchsorted(h_s, hours, side="right")
        self.hours = hours
        self.price = [p_s[a:b] for a, b in zip(i0, i1)]
        self.cum = [np.cumsum(m_s[a:b]) for a, b in zip(i0, i1)]
        self.total = np.array([c[-1] if c.size else 0.0 for c in self.cum])

    def price_at_pctl(self, pctl: np.ndarray) -> np.ndarray:
        """Offer price at a per-hour fraction of the curve's OWN total MW."""
        out = np.full(self.hours.size, np.nan)
        for k, (p, c) in enumerate(zip(self.price, self.cum)):
            if p.size:
                out[k] = oc.price_at_cum(p, c, float(pctl[k]) * float(c[-1]))
        return out

    def mw_at_or_below(self, level: np.ndarray) -> np.ndarray:
        """Per-hour MW priced at or below ``level``."""
        out = np.zeros(self.hours.size)
        for k, (p, c) in enumerate(zip(self.price, self.cum)):
            if p.size:
                j = int(np.searchsorted(p, level[k], side="right"))
                out[k] = float(c[j - 1]) if j else 0.0
        return out

    def price_at_cum(self, x: np.ndarray) -> np.ndarray:
        """Offer price at an absolute per-hour cumulative MW."""
        out = np.full(self.hours.size, np.nan)
        for k, (p, c) in enumerate(zip(self.price, self.cum)):
            if p.size:
                out[k] = oc.price_at_cum(p, c, float(x[k]))
        return out


# --------------------------------------------------------------- model side


def model_block150(year: int, keeper: Path | None) -> dict:
    """miso-145's ``model_block`` plus the VRE / storage / import payload.

    ``keeper`` None keeps ``_miso143_stack``'s own pointer (the footing target);
    a path re-points it for the duration of the call and restores it after, so
    the shared modules are left exactly as found (PREREG TRAP-6).
    """
    prev = stack.KEEPER
    if keeper is not None:
        stack.KEEPER = keeper
    try:
        st = stack.fleet_state(year)
        price, dem = stack.sidecar_price(year)
    finally:
        stack.KEEPER = prev

    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    mk = stack.markup_ceiling(gens, fa, st["config"])
    kl = stack.klass_of(gens)
    for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
        assert (kl == k).sum() > 0, f"class {k!r} has ZERO fleet rows (TRAP-5)"

    # TRAP-5: imports carry no plant_group; klass_of falls back to
    # _model_class_for_unit, which returns "import" for fuel_type == "import".
    is_import = np.array([str(g.fuel_type) == "import" for g in gens], dtype=bool)

    cap = fa.pmax[:, None] * fa.availability
    n_h = cap.shape[1]

    def _bcast(v, n_rows):
        return np.broadcast_to(np.asarray(v, dtype=float), (n_rows, n_h))

    w_cap = np.atleast_1d(np.asarray(st["wind_cap"], dtype=float))
    s_cap = np.atleast_1d(np.asarray(st["solar_cap"], dtype=float))
    w_cf = np.atleast_2d(np.asarray(st["wind_cf"], dtype=float))
    s_cf = np.atleast_2d(np.asarray(st["solar_cf"], dtype=float))
    spc = np.asarray(st["storage_power_cap"], dtype=float)
    if spc.ndim == 1:
        spc = np.broadcast_to(spc[:, None], (spc.size, n_h))

    return {
        "offer": {"lo": mc0, "hi": mc0 + mk[:, None]},
        "cap": cap,
        "klass": kl,
        "is_import": is_import,
        "p1_price": price,
        "demand": dem,
        "wind_mw": w_cap[:, None] * w_cf[:, :n_h],
        "wind_mc": _bcast(st["wind_mc"], w_cf.shape[0]),
        "solar_mw": s_cap[:, None] * s_cf[:, :n_h],
        "solar_mc": _bcast(st["solar_mc"], s_cf.shape[0]),
        "storage_mw": spc[:, :n_h],
        "n_gen": len(gens),
        "n_import": int(is_import.sum()),
        "import_mw": float(fa.pmax[is_import].sum()),
    }


def _dense_parts(hours, price_2d, mw_2d):
    """(seg_h, seg_p, seg_mw) from a (n_rows, T) offer/capability pair.

    Row-major over hours exactly as ``_miso145_offer_conduct.model_curve_readings``
    builds it, so U0 is byte-for-byte that construction.
    """
    p = price_2d[:, hours]
    m = mw_2d[:, hours]
    n = p.shape[0]
    return np.repeat(hours, n), p.T.reshape(-1), m.T.reshape(-1)


def universe_segments(
    mb: dict, hours: np.ndarray, bracket: str, universe: str, vre_scale=None
):
    """Model-side segments for one universe. ``vre_scale`` is the U2 locator."""
    keep = ~mb["is_import"] if universe == "U4" else np.ones(mb["n_gen"], bool)
    parts = [_dense_parts(hours, mb["offer"][bracket][keep], mb["cap"][keep])]

    if universe != "U0":
        for tech in ("wind", "solar"):
            mw = mb[f"{tech}_mw"]
            if vre_scale is not None:
                mw = mw * vre_scale[None, :]
            parts.append(_dense_parts(hours, mb[f"{tech}_mc"], mw))
    if universe == "U1S":
        st_mw = mb["storage_mw"]
        parts.append(
            _dense_parts(
                hours, np.full_like(st_mw, STORAGE_EPSILON), st_mw
            )
        )

    seg_h = np.concatenate([p[0] for p in parts])
    seg_p = np.concatenate([p[1] for p in parts])
    seg_mw = np.concatenate([p[2] for p in parts])
    ok = seg_mw > 0.0
    return seg_h[ok], seg_p[ok], seg_mw[ok]


# ------------------------------------------------------------ the readings


def model_readings(mb, hours, bracket, universe, anchor, target, wgt, vre_scale=None):
    """Every model-side statistic miso-145 reports, on one universe."""
    seg_h, seg_p, seg_mw = universe_segments(mb, hours, bracket, universe, vre_scale)
    cr = oc.curve_readings(hours, seg_h, seg_p, seg_mw, anchor)
    pctl = np.clip(cr["mw_below_anchor"] / np.maximum(1e-9, cr["mw_total"]), 0.0, 1.0)
    wall = seg_mw_between(hours, seg_h, seg_p, seg_mw, anchor, target)
    pack = CurvePack(hours, seg_h, seg_p, seg_mw)
    return {
        "model_capability_gw": round(float((cr["mw_total"] * wgt).sum()) / 1000.0, 3),
        "model_clearing_percentile": round(float((pctl * wgt).sum()), 4),
        "model_gw_anchor_to_hour_actual": round(float((wall * wgt).sum()) / 1000.0, 4),
        "model_ladder_slope_usd_per_gw": {
            f"+{g:g}GW": round(
                float(((cr[f"p_plus_{g:g}gw"] - anchor) / g * wgt).sum()), 4
            )
            for g in oc.LADDER_GW
        },
        "model_price_at_pctl": {
            f"p{int(q * 100)}": round(
                float((pack.price_at_pctl(np.full(hours.size, q)) * wgt).sum()), 3
            )
            for q in oc.PCTL_GRID
        },
        "_pctl": pctl,
        "_below": cr["mw_below_anchor"],
        "_total": cr["mw_total"],
    }


def level_terms(real: CurvePack, pctl, anchor, target, wgt, ordinary):
    """miso-145's LEVEL/POSITION identity at the MODEL's own clearing percentile.

    PREREG TRAP-8: the real curve is NEVER read at its own percentile, which
    would make the level term identically zero by construction.
    """
    rp = real.price_at_pctl(pctl)
    fin = np.isfinite(rp)
    wl = wgt * fin
    wl = wl / max(1e-9, wl.sum())
    wo = wgt * ordinary * fin
    wo = wo / max(1e-9, wo.sum())
    return {
        "real_at_model_percentile_usd": round(float((rp * wl)[fin].sum()), 3),
        "LEVEL_term_usd_per_mwh": round(float(((rp - anchor) * wl)[fin].sum()), 3),
        "POSITION_term_usd_per_mwh": round(float(((target - rp) * wl)[fin].sum()), 3),
        "ordinary_LEVEL_term_usd_per_mwh": round(
            float(((rp - anchor) * wo)[fin].sum()), 3
        ),
        "n_finite_hours": int(fin.sum()),
    }


def ceiling_v_star(real: CurvePack, below, total, anchor, wgt, bar=REINSTATEMENT_BAR_USD):
    """G-4 — the zero-priced model-side mass V* that would reach ``bar``.

    ``V`` is additional foot mass measured from U0, so the model's clearing
    percentile becomes ``(below + V) / (total + V)`` per hour.  Bisected on the
    MEASURED real curve, never on the linearised prior.  Returns None (with the
    saturated level) when the real curve tops out below the bar — a flat curve
    is never credited with a tail it does not reach.
    """

    def level_at(v_mw: float) -> float:
        pctl = np.clip((below + v_mw) / np.maximum(1e-9, total + v_mw), 0.0, 1.0)
        rp = real.price_at_pctl(pctl)
        fin = np.isfinite(rp)
        wl = wgt * fin
        wl = wl / max(1e-9, wl.sum())
        return float(((rp - anchor) * wl)[fin].sum())

    hi_mw = 10_000_000.0  # 10 TW -- the saturation probe, not a search bound
    if level_at(hi_mw) < bar:
        return {"v_star_gw": None, "saturated_level_usd": round(level_at(hi_mw), 3)}
    lo_mw = 0.0
    for _ in range(60):
        mid = 0.5 * (lo_mw + hi_mw)
        if level_at(mid) < bar:
            lo_mw = mid
        else:
            hi_mw = mid
    return {"v_star_gw": round(0.5 * (lo_mw + hi_mw) / 1000.0, 1)}


# ----------------------------------------------------------- the U2 locator


def book_screen_pack(year: int, market: str, hours: np.ndarray) -> dict:
    """The miso-146 screen's per-unit features plus this window's meta segments.

    The screen is miso-146's verbatim (``load_declarations`` / ``unit_features``
    / ``classify``); only the symmetric threshold is swept, and the expensive
    halves (the corpus read and the feature build) are done ONCE per
    year x market rather than once per threshold.
    """
    import _miso146_intermittent_screen as scr

    feat = scr.unit_features(scr.load_declarations(year, market))
    segs = oc.load_real_segments(year, market, hours, with_meta=True)
    return {
        "feat": feat,
        "unit": segs["unit_code"],
        "idx": np.searchsorted(hours, segs["hour"].to_numpy()),
        "mw": segs["seg_mw"].to_numpy(float),
    }


def book_intermittent_mw(pack: dict, hours: np.ndarray, thr: float) -> np.ndarray:
    """Per-hour MW the miso-146 screen labels intermittent, at threshold ``thr``.

    miso-146's P-1 found the threshold load-bearing, which is exactly why U2 is
    reported as a BAND and is never load-bearing on any verdict here (PREREG §3).
    """
    import _miso146_intermittent_screen as scr

    lab = scr.classify(pack["feat"], thr, thr)
    is_int = pack["unit"].map(lab).fillna(False).to_numpy(bool)
    return np.bincount(
        pack["idx"][is_int], weights=pack["mw"][is_int], minlength=hours.size
    )


# ----------------------------------------------------------------- footing


def _classify_bar(path: str) -> float:
    p = path.lower()
    if "percentile" in p or "share" in p:
        return BAR_PCTL
    if "_gw" in p or "capability" in p:
        return BAR_GW
    return BAR_USD


def _diff(a, b, path="", out=None):
    """Recursive numeric comparison of two committed-artifact trees."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in a and k in b:
                _diff(a[k], b[k], f"{path}/{k}", out)
            else:
                out.append((path + "/" + k, None, None, float("inf"), 0.0))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, bool) or isinstance(b, bool):
            return out
        bar = 0.0 if path.rsplit("/", 1)[-1].startswith("n_") else _classify_bar(path)
        d = abs(float(a) - float(b))
        if d > bar:
            out.append((path, a, b, d, bar))
    return out


def footing(markets=("RT", "DA")) -> dict:
    """G-F0 / G-F0b / G-F1 — reproduce before extend. A failure is a HARD STOP."""
    stack.hygiene()
    committed = json.loads(
        (REPO / "results/calibration/_miso145_offer_conduct.json").read_text()
    )
    fresh = oc.run(markets=markets, out_path=None)
    bad = _diff(fresh, committed, "")
    gf0 = {
        "n_out_of_tolerance": len(bad),
        "worst": sorted(bad, key=lambda r: -r[3])[:12],
        "verdict": "PASS" if not bad else "FAIL",
    }

    # G-F1 is _miso145_offer_conduct's own TRAP-7 gate, restated here.
    gf1 = {}
    for key, want in oc.COMMITTED_DEFICITS.items():
        y, w = key.split("|")
        got = fresh["years"][y]["windows"][w]["deficit_usd_per_mwh"]
        gf1[key] = {"got": got, "committed": want, "abs_delta": round(abs(got - want), 4)}
    gf1_ok = all(v["abs_delta"] <= BAR_USD for v in gf1.values())

    # G-F0b -- this probe's SEGMENT path must reproduce miso-145's DENSE path on
    # miso-145's OWN keeper, for U0.  TRAP-1: the invariance identities are only
    # meaningful if the machinery that tests them is verified independently.
    gf0b, wins = {}, stack.windows()
    for year in stack.YEARS:
        mb = model_block150(year, keeper=None)  # miso-145's own pointer
        rt_actual, _ = _actuals(year)
        for wname, sel in wins.items():
            ok = sel & np.isfinite(mb["p1_price"]) & np.isfinite(rt_actual)
            hours = np.nonzero(ok)[0]
            anchor, target = mb["p1_price"][hours], rt_actual[hours]
            w = mb["demand"][hours]
            wgt = w / max(1e-9, w.sum())
            for bracket in ("lo", "hi"):
                got = model_readings(mb, hours, bracket, "U0", anchor, target, wgt)
                want = committed["years"][str(year)]["windows"][wname][bracket]["model"]
                gf0b[f"{year}|{wname}|{bracket}"] = {
                    k: round(abs(got[k] - want[k]), 5)
                    for k in (
                        "model_capability_gw",
                        "model_clearing_percentile",
                        "model_gw_anchor_to_hour_actual",
                    )
                }
    gf0b_ok = all(
        v["model_capability_gw"] <= BAR_GW
        and v["model_gw_anchor_to_hour_actual"] <= BAR_GW
        and v["model_clearing_percentile"] <= BAR_PCTL
        for v in gf0b.values()
    )

    # TRAP-check: sidecar_price's demand denominator IS _miso137's weight W.
    from _miso137_c3a_gap_decomposition import model_hourly

    _h, _p, w137, _z = model_hourly(2025)
    _pr, den = stack.sidecar_price(2025)
    weight_ok = float(np.nanmax(np.abs(np.nan_to_num(w137) - np.nan_to_num(den)))) <= 1e-6

    return {
        "G_F0_miso145_reproduction": gf0,
        "G_F0b_segment_path_vs_dense": {
            "verdict": "PASS" if gf0b_ok else "FAIL",
            "cells": gf0b,
        },
        "G_F1_committed_window_deficits": {
            "verdict": "PASS" if gf1_ok else "FAIL",
            "cells": gf1,
        },
        "weight_identity_sidecar_den_eq_miso137_W": weight_ok,
        "verdict": (
            "PASS"
            if (gf0["verdict"] == "PASS" and gf0b_ok and gf1_ok and weight_ok)
            else "FAIL"
        ),
    }


def _actuals(year: int):
    from _miso137_c3a_gap_decomposition import actual_hourly

    return actual_hourly(year)


# -------------------------------------------------------------------- main


def measure(markets=("RT", "DA"), u2_thresholds=(0.30, 0.50, 0.70)) -> dict:
    """The four universes on the CURRENT keeper. Every Delta is arm-vs-U0."""
    stack.hygiene()
    wins = stack.windows()
    res: dict = {
        "prereg": "results/calibration/PREREG-miso150-model-side-universe-2026-08-10.md",
        "keeper": "2026-08-09-miso-148-basis-aware",
        "bundle": str(KEEPER150.relative_to(REPO)),
        "posture": "NO SOLVE -- run_year(fleet_only=True) stack vs the measured MISO offer corpus",
        "universes": {
            "U0": "fleet generator rows only (miso-145)",
            "U1": "U0 + model VRE at wind_mc/solar_mc (the charter's fix)",
            "U1S": "U1 + storage discharge at epsilon (complete offerable universe; UPPER BOUND)",
            "U4": "U1 minus import tranches (the residual asymmetry, sized)",
        },
        "years": {},
    }

    for year in stack.YEARS:
        mb = model_block150(year, keeper=KEEPER150)
        rt_actual, _da = _actuals(year)
        yr: dict = {
            "n_gen": mb["n_gen"],
            "import_reconcile": {
                "n_import_rows": mb["n_import"],
                "import_pmax_mw": round(mb["import_mw"], 1),
                "committed_miso146": {
                    "n": IMPORT_TRANCHES_N,
                    "mw": IMPORT_TRANCHES_MW,
                },
            },
            "windows": {},
        }
        union = np.nonzero(np.logical_or.reduce(list(wins.values())))[0]
        seg_cache = {m: oc.load_real_segments(year, m, union) for m in markets}

        for wname, sel in wins.items():
            ok = sel & np.isfinite(mb["p1_price"]) & np.isfinite(rt_actual)
            hours = np.nonzero(ok)[0]
            anchor, target = mb["p1_price"][hours], rt_actual[hours]
            w = mb["demand"][hours]
            wgt = w / max(1e-9, w.sum())
            ordinary = target <= oc.TAIL_USD

            vre_h = (
                mb["wind_mw"][:, hours].sum(axis=0) + mb["solar_mw"][:, hours].sum(axis=0)
            )
            vre_off = np.maximum(
                mb["wind_mc"][:, hours].max(axis=0), mb["solar_mc"][:, hours].max(axis=0)
            )
            # PREREG TRAP-2: the ONE channel by which the invariance identities
            # may legitimately break -- hours whose anchor is at or below the
            # model's own VRE offer, where VRE is not foot mass.
            foot = anchor > vre_off
            blk: dict = {
                "n_hours": int(hours.size),
                "anchor_lw_price": round(float((anchor * wgt).sum()), 3),
                "actual_lw_price": round(float((target * wgt).sum()), 3),
                "vre": {
                    "model_vre_capability_gw": round(float((vre_h * wgt).sum()) / 1000.0, 3),
                    "model_wind_capability_gw": round(
                        float((mb["wind_mw"][:, hours].sum(axis=0) * wgt).sum()) / 1000.0, 3
                    ),
                    "model_solar_capability_gw": round(
                        float((mb["solar_mw"][:, hours].sum(axis=0) * wgt).sum()) / 1000.0, 3
                    ),
                    "vre_offer_usd_lw": round(float((vre_off * wgt).sum()), 4),
                    "committed_miso146_vre_dispatch_gw": MISO146_VRE_DISPATCH_GW,
                    "storage_capability_gw": round(
                        float((mb["storage_mw"][:, hours].sum(axis=0) * wgt).sum()) / 1000.0,
                        3,
                    ),
                },
                "trap2_anchor_le_vre_offer": {
                    "n_hours": int((~foot).sum()),
                    "share": round(float((~foot).mean()), 4),
                },
                "model": {},
                "real": {},
            }

            packs = {}
            for market in markets:
                s = seg_cache[market]
                s = s[s["hour"].isin(hours)]
                sh = s["hour"].to_numpy()
                sp = s["seg_price"].to_numpy(float)
                sm = s["seg_mw"].to_numpy(float)
                packs[market] = CurvePack(hours, sh, sp, sm)
                # G-F0c -- the packed reader against miso-145's own primitive.
                q = np.full(hours.size, 0.85)
                d = np.nanmax(
                    np.abs(
                        packs[market].price_at_pctl(q)
                        - oc.price_at_pctl(hours, sh, sp, sm, q)
                    )
                )
                blk["real"][market] = {
                    "real_capability_gw": round(
                        float((packs[market].total * wgt).sum()) / 1000.0, 3
                    ),
                    "n_segments": int(s.shape[0]),
                    "G_F0c_pack_vs_miso145_price_at_pctl_max_abs": round(float(d), 8),
                }

            for bracket in ("lo", "hi"):
                base = None
                for uni in UNIVERSES:
                    r = model_readings(mb, hours, bracket, uni, anchor, target, wgt)
                    pctl, below, total = r.pop("_pctl"), r.pop("_below"), r.pop("_total")
                    for market in markets:
                        r.setdefault("level_decomposition", {})[market] = level_terms(
                            packs[market], pctl, anchor, target, wgt, ordinary
                        )
                    if uni == "U0":
                        base = r
                        for market in markets:
                            r["G4_ceiling"] = r.get("G4_ceiling", {})
                            r["G4_ceiling"][market] = ceiling_v_star(
                                packs[market], below, total, anchor, wgt
                            )
                            r["G4_ceiling"][market]["vre_nameplate_gw"] = (
                                VRE_NAMEPLATE_GW[year]
                            )
                    else:
                        r["delta_vs_U0"] = {
                            "d_clearing_percentile": round(
                                r["model_clearing_percentile"]
                                - base["model_clearing_percentile"],
                                4,
                            ),
                            "G1_d_ladder_slope_usd_per_gw": {
                                k: round(
                                    r["model_ladder_slope_usd_per_gw"][k]
                                    - base["model_ladder_slope_usd_per_gw"][k],
                                    4,
                                )
                                for k in r["model_ladder_slope_usd_per_gw"]
                            },
                            "G2_d_wall_gw": round(
                                r["model_gw_anchor_to_hour_actual"]
                                - base["model_gw_anchor_to_hour_actual"],
                                4,
                            ),
                            "G3_d_LEVEL_usd_per_mwh": {
                                m: round(
                                    r["level_decomposition"][m]["LEVEL_term_usd_per_mwh"]
                                    - base["level_decomposition"][m][
                                        "LEVEL_term_usd_per_mwh"
                                    ],
                                    3,
                                )
                                for m in markets
                            },
                        }
                    blk["model"].setdefault(bracket, {})[uni] = r

                # TRAP-2 counter-measurement: G-1/G-2 re-evaluated on the
                # complement, where the identity must hold EXACTLY.
                if foot.sum() and int((~foot).sum()):
                    wf = wgt * foot
                    wf = wf / max(1e-9, wf.sum())
                    hf = hours[foot]
                    a_f, t_f = anchor[foot], target[foot]
                    r0 = model_readings(mb, hf, bracket, "U0", a_f, t_f, wf)
                    r1 = model_readings(mb, hf, bracket, "U1", a_f, t_f, wf)
                    blk.setdefault("trap2_foot_only", {})[bracket] = {
                        "G2_d_wall_gw": round(
                            r1["model_gw_anchor_to_hour_actual"]
                            - r0["model_gw_anchor_to_hour_actual"],
                            5,
                        ),
                        "G1_d_slope_+1GW": round(
                            r1["model_ladder_slope_usd_per_gw"]["+1GW"]
                            - r0["model_ladder_slope_usd_per_gw"]["+1GW"],
                            5,
                        ),
                    }

            # U2 locator -- banded, never load-bearing (PREREG §3).
            if wname == "JJA_h12_17":
                u2: dict = {}
                for market in markets:
                    spack = book_screen_pack(year, market, hours)
                    for thr in u2_thresholds:
                        cap_h = book_intermittent_mw(spack, hours, thr)
                        scale = np.clip(
                            cap_h / np.maximum(1e-9, vre_h), 0.0, 1.0
                        )
                        r = model_readings(
                            mb, hours, "lo", "U1", anchor, target, wgt, vre_scale=scale
                        )
                        lv = level_terms(
                            packs[market], r["_pctl"], anchor, target, wgt, ordinary
                        )
                        u2[f"{market}|thr{thr}"] = {
                            "book_intermittent_gw": round(
                                float((cap_h * wgt).sum()) / 1000.0, 3
                            ),
                            "model_clearing_percentile": r["model_clearing_percentile"],
                            "LEVEL_term_usd_per_mwh": lv["LEVEL_term_usd_per_mwh"],
                        }
                blk["U2_locator_lo_bracket"] = u2

            yr["windows"][wname] = blk
        res["years"][str(year)] = yr

    return res


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT), type=Path)
    ap.add_argument("--footing", action="store_true", help="footing gates only")
    ap.add_argument("--markets", nargs="+", default=["RT", "DA"])
    args = ap.parse_args()

    res = {"footing": footing(markets=tuple(args.markets))}
    print(f"FOOTING: {res['footing']['verdict']}")
    for k in ("G_F0_miso145_reproduction", "G_F0b_segment_path_vs_dense", "G_F1_committed_window_deficits"):
        print(f"  {k}: {res['footing'][k]['verdict']}")
    if res["footing"]["verdict"] != "PASS":
        print("HARD STOP -- PREREG §2. No new statistic computed.")
        for row in res["footing"]["G_F0_miso145_reproduction"]["worst"]:
            print("   ", row)
    elif not args.footing:
        res["measurement"] = measure(markets=tuple(args.markets))

    args.out.write_text(json.dumps(res, indent=1, default=float))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
