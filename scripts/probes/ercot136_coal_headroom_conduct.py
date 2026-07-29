#!/usr/bin/env python
"""ERCOT-136 — the SCED TPO instrument on the coal headroom BOTTOM: what price
does the real fleet attach to the block the model bids at $4.50?

Phase 1 of the lane the ERCOT-135 charter routed here
(``docs/DIAGNOSIS-ercot135-coal-merit-order-2026-07-28.md`` §6): ERCOT-135
measured that only 27.8/38.7/39.1 % of committed coal resource-hours submit ANY
**DAM** incremental energy curve, and refused to build a mechanism because the
unoffered remainder might be **self-scheduled** (in which case the model's
$4.50/MWh take-or-pay tranche is structurally faithful), **withheld** (in which
case the model should not be offering it), or **telemetered down** (an
availability question already closed by ERCOT-126).

**Prior art that this probe does NOT redo.** ``DIAGNOSIS-ercot123`` (2026-07-27)
already ran the three-way decomposition on this very instrument and settled it:
coal offers **0.9945-0.9998** of its RT-dispatchable headroom (``HASL - LSL``)
into SCED, the genuinely-unoffered residual is **0.0001-0.0002**, and the
price-taking bucket is **0.000-0.005** (CC control 0.008-0.035). None of the
charter's three branches fires: the DAM non-submission is QSE self-supply
bypassing the DAM transaction, and the same capacity carries a full three-part
offer in real time. That result is **reproduced here as section A**, on
ERCOT-123's own loader and conventions (imported, not re-implemented), so the
two lanes stand on one footing.

**What ERCOT-123 could NOT see, and this probe measures.** Its decomposition
runs over ``HASL - LSL`` and its supply curve is floored at ``LSL``
(``supply(-inf) = LSL``), so **the min-load block is excluded by construction**
— ERCOT-123 §4 flags this in terms ("the charter's denominator structurally
cannot see the quantity bucket (b) was meant to detect"). Its price grid is
also ``(0, 20, 25, 40, 100, 500)``, so the whole $0-20 region — where the
model's bimodal cheap band lives — is one lump. The model's tranche-1 is
**30 % of coal capacity at $4.50/MWh**, which is *inside* that lump and *below*
that floor. So the ERCOT-135 question is untouched by ERCOT-123 and is exactly
what this probe resolves:

* **A** — the ERCOT-123 decomposition, reproduced (footing check, no new claim).
* **B** — **the RT curve BOTTOM.** Capacity-weighted distribution of
  ``Submitted TPO-Price1``, the price of the fleet's *first and cheapest*
  offered MW, plus a sub-$20-resolving supply grid on two denominators: the
  ERCOT-123 convention (floored at ``LSL``, denominator ``HASL``) and an
  **unfloored** convention (from 0 MW, denominator ``HSL``) that makes the
  min-load block's pricing visible.
* **C** — **the min-load block's own declared price.** ``Min Gen Cost``, which
  ERCOT-123 §7.4(b) recorded as present-but-unused. Its units are proved here
  rather than assumed.
* **D** — the model side, read from the **committed** ERCOT-135 artifact
  ``results/calibration/ercot135_coal_merit_order.json`` (no re-solve, no LP).
* **E** — **the price-responsiveness conduct test.** Does SCED's ``Base Point``
  track the ``Output Schedule`` (price-taking) or the submitted curve evaluated
  at the clearing price (economic)? This is the operational meaning of
  "self-scheduled" and is what licenses or refuses a near-zero bid.
* **F** — the rule 19 ``[R-ONE-MECH]`` enumeration: what already floors or
  prices ERCOT coal min-load in the current keeper.

**Rule 13 [R-MEASURED] / rule 1 [R-STRUCT] scope.** Nothing here is tuned and
nothing here is a mechanism. Every number is either a measured corpus read on an
already-accepted convention or the model's own committed construction read back.
No ``ScenarioConfig`` field is written, no solve path is touched, no keeper file
is touched, and no year outside {2023, 2024, 2025} is read (rule 22
``[R-HOLDOUT]``).

**SAMPLING — carried on every number, per ERCOT-123 §8.** The on-disk SCED
subsets are **probe days, not a full span**: 82 delivery days across
**2024-2025 only** (no 2023 SCED exists on disk), and three of the four subsets
sample **hours 11-22 only**. December-2025 intervals are dropped explicitly by
the shared loader (ERCOT revised the disclosure schema: ``HASL``/``LASL`` and
the AS *award* block are gone). Nothing here is an annual statistic. §B reports
every statistic **split by day-family (tail vs control)** so the deliberate
price-based day selection is its own robustness control rather than an
unquantified caveat.

Usage
-----
    python scripts/probes/ercot136_coal_headroom_conduct.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO / "src"), str(_REPO), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ERCOT-123's loader and conventions are IMPORTED, never re-implemented, so the
# two lanes' bases match by construction (the ERCOT-135 charter's requirement).
from ercot123_coal_sced_reach import (  # noqa: E402
    SUBSETS,
    TPO_MW,
    TPO_PR,
    _decompose,
    _subset_path,
    load_sced,
    section_a as ercot123_section_a,
)


def attach_min_gen_cost(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    """Join ``Min Gen Cost`` onto an already-loaded, already-filtered frame.

    ERCOT-123's ``load_sced`` does not request this column, and that module is
    **prior art that must not be edited** — so the column is re-read from the
    same parquet and merged on the natural key ``(Resource Name, SCED Time
    Stamp)``. Merging rather than re-applying ERCOT-123's row filters is
    deliberate: replicating the filter logic is exactly how two lanes silently
    drift onto different corpora.
    """
    import pyarrow.parquet as pq

    path = _subset_path(tag)
    have = set(pq.ParquetFile(path).schema_arrow.names)
    if "Min Gen Cost" not in have:
        df["Min Gen Cost"] = np.nan
        return df
    key = ["Resource Name", "SCED Time Stamp"]
    side = pd.read_parquet(path, columns=key + ["Min Gen Cost"])
    side["Min Gen Cost"] = pd.to_numeric(side["Min Gen Cost"], errors="coerce")
    side = side.drop_duplicates(subset=key)
    for k in key:
        side[k] = side[k].astype(str)
    out = df.copy()
    join = pd.DataFrame({k: out[k].astype(str) for k in key})
    out["Min Gen Cost"] = join.merge(side, on=key, how="left")[
        "Min Gen Cost"
    ].to_numpy()
    return out


#: The committed ERCOT-135 model-side capture. Read, never regenerated — the
#: model's coal bid array at the LP seam, after ``apply_coal_tranches``.
ERCOT135_ARTIFACT = _REPO / "results" / "calibration" / "ercot135_coal_merit_order.json"

OUT_JSON = _REPO / "results" / "calibration" / "ercot136_coal_headroom_conduct.json"

#: The model's tranche-1 take-or-pay bid, ``coal_tranche_1_fuel_passthrough =
#: 0.00`` => VOM only. ERCOT-135 §1 measured it at p10 AND p25 in all 3 years.
MODEL_TRANCHE1_BID = 4.50

#: Sub-$20-resolving price grid. $4.50 is an explicit edge: it is the model's
#: own tranche-1 bid, so the band ``[0, 4.5)`` is precisely "MW the real fleet
#: offers at or below what the model charges for 30 % of its coal".
FINE_GRID: tuple[float, ...] = (
    0.0,
    2.0,
    4.5,
    7.5,
    10.0,
    12.5,
    15.0,
    17.5,
    20.0,
    25.0,
    30.0,
    40.0,
    100.0,
    500.0,
)


def _wq(values: np.ndarray, weights: np.ndarray, qs: tuple[float, ...]) -> list[float]:
    """Capacity-weighted quantiles.

    A 750 MW Oak Grove interval and a 90 MW unit are not the same evidence, so
    every distributional statistic in this probe is weighted by ``HSL`` — the
    same convention ERCOT-135 §1 used for the measured DAM curve.
    """
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not ok.any():
        return [float("nan")] * len(qs)
    v, w = values[ok], weights[ok]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) / w.sum()
    return [float(np.interp(q, cw, v)) for q in qs]


def _curve(g: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the (price, MW, valid-mask) arrays of the submitted TPO curve."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    return P, M, np.isfinite(P) & np.isfinite(M)


def section_a(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """A — ERCOT-123's headroom decomposition, reproduced on its own code.

    No new claim is made here. This runs ``ercot123_coal_sced_reach.section_a``
    unchanged so that every downstream number in this probe is demonstrably on
    the same corpus, the same ``ONLINE`` status set, the same December-2025 drop
    and the same capacity weighting as the session that closed the reach
    question. A divergence here would mean the two lanes are not comparable.
    """
    return ercot123_section_a(frames)


def section_a2(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """A2 — the charter's literal classification, on the FULL telemetered range.

    ERCOT-123 decomposed ``HASL - LSL``. The ERCOT-135 question is about a model
    band that *includes* min-load, so the same capability is re-decomposed over
    the whole telemetered capability ``HSL``, exhaustively:

    * ``minload``  ``[0, LSL]`` — bought by the **commitment** decision, not by
      the energy curve. This is the block the model prices at $4.50.
    * ``offered``  the part of ``[LSL, HASL]`` the submitted TPO curve reaches.
    * ``selfsched`` output-schedule / telemetered MW **above** the curve's reach
      (ERCOT-123's bucket (b) reference, unchanged).
    * ``as_held``  ``HSL - HASL`` — the awarded up-AS power reservation.
    * ``residual`` everything else: the genuinely unoffered, unused block.

    The point of the re-cut is that ``minload`` is a *named share of HSL* here
    instead of being divided out, which is what makes it comparable to the
    model's ``coal_tranche_1_frac = 0.30``.
    """
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            hsl = g["HSL"].sum()
            if hsl <= 0:
                continue
            lsl = g["LSL"].clip(lower=0.0).sum()
            rows.append(
                {
                    "year": year,
                    "family": fam,
                    "class": cls,
                    "res_hours": len(g),
                    "minload_of_HSL": float(lsl / hsl),
                    "offered_of_HSL": float(g["off_mw"].sum() / hsl),
                    "selfsched_of_HSL": float(g["ss_mw"].sum() / hsl),
                    "as_held_of_HSL": float(g["as_mw"].sum() / hsl),
                    "residual_of_HSL": float(g["res_mw"].sum() / hsl),
                    "curve_share": float(g["has_curve"].mean()),
                    "osched_gt0_share": float(
                        (g["Output Schedule"].fillna(0.0) > 0).mean()
                    ),
                }
            )
    return pd.DataFrame(rows)


def section_b(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """B — THE DECISIVE MEASUREMENT: the bottom of the real fleet's RT curve.

    Two objects, both capacity-weighted, both split by day family:

    **B1 — the bottom price.** ``Submitted TPO-Price1`` is the price of the
    fleet's *first and cheapest* offered MW. Its capacity-weighted p10/p25/p50
    is the direct counterpart of ERCOT-135 §1's "model bid p10 / p25 = 4.50 /
    4.50". Also reported: ``TPO-MW1 / LSL``, which says whether the curve starts
    at min load (so the first offered MW *is* the min-load block) or above it.

    **B2 — the supply grid, sub-$20 resolved**, on two denominators:

    * ``floored``   ``supply(x) = clip(max{MW_k : price_k <= x}, LSL, HASL)``
      with ``supply(-inf) = LSL``, denominator ``HASL``. This is ERCOT-123 §5's
      convention **verbatim**, so its published ≤$20 / ≤$25 figures reproduce and
      the new sub-$20 bands are demonstrably the same curve, just resolved finer.
    * ``unfloored`` ``supply(x) = clip(max{MW_k : price_k <= x}, 0, HSL)`` with
      ``supply(-inf) = 0``, denominator ``HSL``. Nothing is assumed bought
      before the curve speaks, so the min-load block appears **at the price the
      QSE actually attached to it**. This is the convention the ERCOT-135
      comparison needs and the one ERCOT-123 did not run.

    The ``[0, 4.5)`` band is the headline number: the share of real coal
    capability offered at or below the model's own tranche-1 bid.
    """
    lvl_rows, grid_rows = [], []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            P, M, ok = _curve(g)
            hsl = g["HSL"].to_numpy(float)
            hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
            lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
            has_curve = ok.any(axis=1)

            # --- B1: the bottom of the curve ------------------------------
            # The cheapest submitted point, and the MW at which it sits. Taking
            # the min over the price columns (not column 1 blindly) is robust to
            # a QSE that submits its points out of order.
            p_bot = np.where(ok, P, np.inf).min(axis=1)
            k_bot = np.where(ok, P, np.inf).argmin(axis=1)
            mw_bot = M[np.arange(len(M)), k_bot]
            sel = has_curve & np.isfinite(p_bot)
            q = (0.10, 0.25, 0.50, 0.75, 0.90)
            lvl_rows.append(
                {
                    "year": year,
                    "family": fam,
                    "class": cls,
                    "res_hours": int(sel.sum()),
                    **dict(
                        zip(
                            [f"bot_p{int(x * 100)}" for x in q],
                            _wq(p_bot[sel], hsl[sel], q),
                        )
                    ),
                    "bot_mean_capwtd": float(np.average(p_bot[sel], weights=hsl[sel]))
                    if sel.any()
                    else float("nan"),
                    "share_MW_bot_below_4p50": float(
                        hsl[sel & (p_bot <= MODEL_TRANCHE1_BID)].sum() / hsl[sel].sum()
                    )
                    if sel.any()
                    else float("nan"),
                    "mw1_over_lsl_p50": float(
                        np.median(
                            (mw_bot[sel] / np.where(lsl[sel] > 0, lsl[sel], np.nan))
                        )
                    )
                    if sel.any()
                    else float("nan"),
                }
            )

            # --- B2: the supply grid on both denominators ------------------
            for conv, floor, cap, denom in (
                ("floored", lsl, hasl, hasl),
                ("unfloored", np.zeros_like(lsl), hsl, hsl),
            ):
                prev = floor.copy()
                rec: dict[str, float] = {}
                for x in FINE_GRID:
                    s = ok & (P <= x)
                    sup = np.max(np.where(s, M, -np.inf), axis=1)
                    sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), floor, cap)
                    sup = np.maximum(sup, prev)  # monotone across edges
                    rec[f"<={x:g}"] = float(sup.sum())
                    prev = sup
                tot = float(denom.sum())
                if tot <= 0:
                    continue
                grid_rows.append(
                    {
                        "year": year,
                        "family": fam,
                        "class": cls,
                        "conv": conv,
                        **{k: v / tot for k, v in rec.items()},
                    }
                )
    return pd.DataFrame(lvl_rows), pd.DataFrame(grid_rows)


def section_c(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """C — the min-load block's OWN declared price (``Min Gen Cost``).

    ERCOT-123 §7.4(b) recorded this column as present and populated on 29-31 %
    of online coal resource-intervals, and deliberately did not use it. It is
    used here for exactly one purpose: the model prices the min-load block at
    $4.50, and this is the only measured statement in the corpus about what that
    block costs.

    **Units are proved, not assumed.** If ``Min Gen Cost`` were a $/hr
    make-whole total it would scale with ``LSL`` (hundreds of MW => thousands of
    dollars); the reported ``per_LSL`` ratio and the ``corr`` and level match
    against ``TPO-Price1`` settle it. Reported so the reader can check rather
    than trust.
    """
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None or "Min Gen Cost" not in d.columns:
            continue
        for cls, g in d.groupby("cls", observed=True):
            mg = pd.to_numeric(g["Min Gen Cost"], errors="coerce")
            have = mg.notna()
            if not have.any():
                continue
            hsl = g["HSL"].to_numpy(float)
            P, _, ok = _curve(g)
            p_bot = np.where(ok, P, np.inf).min(axis=1)
            both = have.to_numpy() & np.isfinite(p_bot)
            q = (0.10, 0.25, 0.50, 0.75, 0.90)
            rows.append(
                {
                    "year": year,
                    "family": fam,
                    "class": cls,
                    "populated_share": float(have.mean()),
                    "n": int(have.sum()),
                    **dict(
                        zip(
                            [f"mingen_p{int(x * 100)}" for x in q],
                            _wq(
                                mg.to_numpy(float)[have.to_numpy()],
                                hsl[have.to_numpy()],
                                q,
                            ),
                        )
                    ),
                    "per_LSL": float(
                        (mg[have] / g["LSL"][have].replace(0, np.nan)).mean()
                    ),
                    "corr_with_tpo_bottom": float(
                        np.corrcoef(mg.to_numpy(float)[both], p_bot[both])[0, 1]
                    )
                    if both.sum() > 2
                    else float("nan"),
                    "tpo_bottom_p50_same_rows": _wq(p_bot[both], hsl[both], (0.50,))[0],
                }
            )
    return pd.DataFrame(rows)


def section_d() -> dict:
    """D — the model side, read from the COMMITTED ERCOT-135 artifact.

    No LP is built and no solve is replayed: ERCOT-135 already captured the
    model's coal bid array at the exact seam the LP consumes it (after
    ``apply_coal_tranches``), and that capture is committed. Re-deriving it here
    would risk a second, subtly different convention for no gain.
    """
    if not ERCOT135_ARTIFACT.exists():
        return {"error": f"missing {ERCOT135_ARTIFACT}"}
    blob = json.loads(ERCOT135_ARTIFACT.read_text())
    out: dict = {"source": str(ERCOT135_ARTIFACT.relative_to(_REPO))}
    for key in ("A", "section_a", "model_curve", "a_model_offer_surface"):
        if key in blob:
            out["model_curve_key"] = key
            out["model_curve"] = blob[key]
            break
    out["keys_present"] = sorted(blob.keys())
    return out


def section_e(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """E — the price-responsiveness conduct test (what "self-scheduled" MEANS).

    A block is *price-taking* if its dispatch does not respond to price. The
    charter's three branches are ultimately claims about conduct, so conduct is
    measured directly, three ways per subset:

    * ``bp_eq_os_1MW`` / ``bp_eq_os_5MW`` — how often SCED's ``Base Point`` just
      **is** the ``Output Schedule``. A genuinely self-scheduled fleet sits at
      its schedule; a dispatched one does not.
    * ``corr_bp_curve_at_price`` vs ``corr_bp_osched`` — whether ``Base Point``
      tracks the unit's **own TPO curve evaluated at the hourly RT price** or
      its output schedule. The curve is evaluated exactly as ERCOT-123 §H does
      (same hourly ``actual_lmp_hourly_ERCOT`` series, same clip), so the
      comparison inherits that section's stated hourly-price approximation.
    * ``bp_minus_os_corr_price`` — the correlation of the **deviation**
      ``Base Point - Output Schedule`` with price.
    * ``mae_bp_vs_curve`` / ``mae_bp_vs_osched`` — which reference explains the
      base point better in MW.

    **This section is CORROBORATING, NOT DECISIVE, and is reported as such.**
    Both correlations are high for a reason that has nothing to do with price
    response: ``Base Point``, ``Output Schedule`` and curve-at-price all scale
    with the unit's size and commitment state, so the common component dominates
    either correlation. The decisive evidence for the charter's question is §A2
    (self-scheduled MW above the curve ~ 0) and §B (the curve bottom), not this.
    It also inherits ERCOT-123 §H's stated hourly-price approximation: the
    5-minute SCED LMP is not on disk, so a 5-minute base point is compared
    against an hourly mean price and the deviation-vs-price correlation is
    attenuated by construction. Do not read a weak ``bp_minus_os_corr_price`` as
    evidence of price-taking.
    """
    lmp = (
        _REPO
        / "data"
        / "raw"
        / "_validation-source"
        / "actual_lmp_hourly_ERCOT.parquet"
    )
    if not lmp.exists():
        return pd.DataFrame()
    px = pd.read_parquet(lmp)
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        pr = px[px["year"] == year].sort_values("hour")["rt"].to_numpy(float)
        if pr.size == 0:
            continue
        for cls, g in d.groupby("cls", observed=True):
            ts = g["ts"]
            hoy = (
                (ts - pd.Timestamp(year=int(year), month=1, day=1))
                // pd.Timedelta(hours=1)
            ).to_numpy()
            m = (hoy >= 0) & (hoy < pr.size)
            g = g[m]
            if g.empty:
                continue
            p = pr[hoy[m]]
            P, M, ok = _curve(g)
            hsl = g["HSL"].to_numpy(float)
            hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
            lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
            s = ok & (P <= p[:, None])
            sup = np.max(np.where(s, M, -np.inf), axis=1)
            sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
            bp = pd.to_numeric(g["Base Point"], errors="coerce").to_numpy(float)
            os_ = np.nan_to_num(g["Output Schedule"].to_numpy(float))
            fin = np.isfinite(bp) & np.isfinite(sup) & np.isfinite(p)
            if fin.sum() < 3:
                continue

            def _c(a: np.ndarray, b: np.ndarray) -> float:
                if np.std(a) == 0 or np.std(b) == 0:
                    return float("nan")
                return float(np.corrcoef(a, b)[0, 1])

            rows.append(
                {
                    "year": year,
                    "family": fam,
                    "class": cls,
                    "n": int(fin.sum()),
                    "bp_eq_os_1MW": float((np.abs(bp - os_)[fin] <= 1.0).mean()),
                    "bp_eq_os_5MW": float((np.abs(bp - os_)[fin] <= 5.0).mean()),
                    "corr_bp_curve_at_price": _c(bp[fin], sup[fin]),
                    "corr_bp_osched": _c(bp[fin], os_[fin]),
                    "bp_minus_os_corr_price": _c((bp - os_)[fin], p[fin]),
                    "mean_bp_minus_os_MW": float((bp - os_)[fin].mean()),
                    "mae_bp_vs_curve": float(np.abs(bp - sup)[fin].mean()),
                    "mae_bp_vs_osched": float(np.abs(bp - os_)[fin].mean()),
                }
            )
    return pd.DataFrame(rows)


def section_g(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """G — the hour-of-day bias bound, on ERCOT-123 §8's convention.

    Three of the four subsets sample **hours 11-22 only**. Rather than assume
    the daytime bias away, it is bounded directly on the one subset that covers
    all 24 hours (``2025_ercot86_tail_days``), splitting the §B headline
    statistics into ``h11-22`` and ``h23-h10``. If the curve bottom and the
    ≤$4.50 share are stable across the split, the three daytime-only subsets are
    not driving the conclusion.
    """
    tag = "2025_ercot86_tail_days"
    d = frames.get(tag)
    if d is None:
        return pd.DataFrame()
    rows = []
    hr = d["ts"].dt.hour
    for cls, g_all in d.groupby("cls", observed=True):
        h = hr.loc[g_all.index]
        for label, m in (
            ("h11-22", (h >= 11) & (h <= 22)),
            ("h23-h10", (h < 11) | (h > 22)),
        ):
            g = g_all[m.to_numpy()]
            if g.empty:
                continue
            P, M, ok = _curve(g)
            hsl = g["HSL"].to_numpy(float)
            lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
            p_bot = np.where(ok, P, np.inf).min(axis=1)
            sel = ok.any(axis=1) & np.isfinite(p_bot)
            if not sel.any():
                continue
            # Unfloored supply at the model's own tranche-1 bid.
            s = ok & (P <= MODEL_TRANCHE1_BID)
            sup = np.max(np.where(s, M, -np.inf), axis=1)
            sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), 0.0, hsl)
            rows.append(
                {
                    "subset": tag,
                    "class": cls,
                    "hours": label,
                    "res_hours": int(len(g)),
                    "bot_p10": _wq(p_bot[sel], hsl[sel], (0.10,))[0],
                    "bot_p50": _wq(p_bot[sel], hsl[sel], (0.50,))[0],
                    "share_MW_bot_below_4p50": float(
                        hsl[sel & (p_bot <= MODEL_TRANCHE1_BID)].sum() / hsl[sel].sum()
                    ),
                    "unfloored_supply_at_4p50": float(sup.sum() / hsl.sum()),
                    "minload_of_HSL": float(lsl.sum() / hsl.sum()),
                }
            )
    return pd.DataFrame(rows)


def section_h(b1: pd.DataFrame, b2: pd.DataFrame, a2: pd.DataFrame) -> pd.DataFrame:
    """H — the headline: the model's cheap block against the measured one.

    ERCOT-135 §1 measured the model's coal bid at **p10 = p25 = $4.50** with
    ``coal_tranche_1_frac = 0.30``, i.e. **30 % of coal capacity at $4.50/MWh**.
    This table puts the measured RT counterpart beside it on the *unfloored*
    convention (§B2), which is the only one that can see the min-load block.

    ``ratio_model_over_measured`` is the direct sizing of the ERCOT-135 defect on
    this instrument: how many times more cheap coal the model offers than the
    real fleet does.
    """
    rows = []
    coal2 = b2[(b2["class"] == "COAL") & (b2["conv"] == "unfloored")]
    for _, r in coal2.iterrows():
        bot = b1[
            (b1["class"] == "COAL")
            & (b1["year"] == r["year"])
            & (b1["family"] == r["family"])
        ]
        ml = a2[
            (a2["class"] == "COAL")
            & (a2["year"] == r["year"])
            & (a2["family"] == r["family"])
        ]
        measured = float(r["<=4.5"])
        rows.append(
            {
                "year": r["year"],
                "family": r["family"],
                "model_share_at_4p50": 0.30,
                "measured_share_at_or_below_4p50": measured,
                "ratio_model_over_measured": 0.30 / measured
                if measured > 0
                else np.nan,
                "measured_curve_bottom_p50": float(bot["bot_p50"].iloc[0])
                if not bot.empty
                else np.nan,
                "measured_minload_of_HSL": float(ml["minload_of_HSL"].iloc[0])
                if not ml.empty
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def section_f() -> list[dict]:
    """F — rule 19 ``[R-ONE-MECH]``: what already floors or prices coal min-load.

    Enumerated **before** any mechanism is proposed, as rule 19 requires. This is
    a static reading of the current keeper's configuration and the committed
    mechanism registry, not a measurement.
    """
    return [
        {
            "mechanism": "ercot_coal_min_config_floor",
            "role": "FLOORS the min-load block",
            "detail": "ERCOT-129 (in the keeper): a coal plant may not be pushed "
            "below the registered minimum load of its smallest online "
            "configuration (EIA-860, 10 plants / 13,611 MW, cap-wtd "
            "0.1590), applied availability-conditionally.",
            "status": "ARMED in 2026-07-28-ercot116-regate-base",
        },
        {
            "mechanism": "coal_tranche_1_frac / coal_tranche_1_fuel_passthrough",
            "role": "PRICES the min-load block",
            "detail": "30 % of coal capacity bid at VOM only (passthrough 0.00) "
            "=> $4.50/MWh, the take-or-pay band. ERCOT-135 §1 measured "
            "it at both p10 and p25 in all three years.",
            "status": "ARMED (model default)",
        },
        {
            "mechanism": "coal_mustrun_per_plant",
            "role": "FLOORS the min-load block (per-plant)",
            "detail": "Each coal plant's must-run % comes from the CAMPD-derived "
            "COAL_MUSTRUN_BY_PLANT table (data/offer_curves.py:831) "
            "rather than a uniform lignite/PRB override — a second, "
            "independently-derived floor on the same block.",
            "status": "ARMED in the keeper",
        },
        {
            "mechanism": "coal_econ_marginal_hr_bound",
            "role": "FLOORS the ECONOMIC band from below",
            "detail": "ERCOT-115 keeper: clamps each coal class's economic band up "
            "to the ISO's measured CAMPD marginal heat rate; lifts "
            "COAL_PRB.econ_low 0.400 -> 0.886. Does NOT touch tranche-1.",
            "status": "ARMED in the keeper",
        },
        {
            "mechanism": "ercot_thermal_as_endogenous",
            "role": "PRICES the AS reservation",
            "detail": "Thermal AS priced in the co-optimisation; ERCOT-123 §1(c) "
            "measured the awarded up-AS block at 3.3-5.2 % of coal's "
            "telemetered range and ruled re-reserving it a rule-19 stack.",
            "status": "ARMED",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json-out", type=Path, default=OUT_JSON)
    args = ap.parse_args(argv)

    frames, coverage = {}, {}
    for tag, _year, _fam in SUBSETS:
        got = load_sced(tag)
        if got is None:
            print(f"  [skip] {tag}: not on disk")
            continue
        df, cov = got
        frames[tag] = attach_min_gen_cost(_decompose(df), tag)
        coverage[tag] = cov

    if not frames:
        print("FATAL: no SCED subset on disk")
        return 1

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)

    a = section_a(frames)
    a2 = section_a2(frames)
    b1, b2 = section_b(frames)
    c = section_c(frames)
    d = section_d()
    e = section_e(frames)
    f = section_f()
    g = section_g(frames)
    h = section_h(b1, b2, a2)

    def show(title: str, df: pd.DataFrame) -> None:
        print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
        print(
            df.to_string(index=False, float_format=lambda v: f"{v:.4f}")
            if not df.empty
            else "  (empty)"
        )

    show("A — ERCOT-123 decomposition, reproduced (footing check)", a)
    show("A2 — full-range classification, min-load VISIBLE (share of HSL)", a2)
    show("B1 — the RT curve BOTTOM price (cap-weighted)", b1)
    show("B2 — supply grid, sub-$20 resolved (two denominators)", b2)
    show("C — Min Gen Cost: the min-load block's declared price", c)
    show("E — price-responsiveness conduct test (CORROBORATING, not decisive)", e)
    show("G — hour-of-day bias bound (all-24h subset)", g)
    show("H — HEADLINE: model $4.50 block vs the measured RT counterpart", h)

    print(
        f"\n{'=' * 78}\nF — rule 19 enumeration: what already floors/prices coal min-load\n{'=' * 78}"
    )
    for row in f:
        print(f"  {row['mechanism']:<45} {row['role']}")
        print(f"    {row['detail']}")
        print(f"    status: {row['status']}")

    print(f"\n{'=' * 78}\nD — model side (committed ERCOT-135 artifact)\n{'=' * 78}")
    print(f"  source: {d.get('source')}  keys: {d.get('keys_present')}")

    blob = {
        "lane": "ercot136-coal-headroom-conduct",
        "phase": 1,
        "no_lp": True,
        "coverage": coverage,
        "model_tranche1_bid": MODEL_TRANCHE1_BID,
        "A_ercot123_reproduced": a.to_dict("records"),
        "A2_full_range": a2.to_dict("records"),
        "B1_curve_bottom": b1.to_dict("records"),
        "B2_supply_grid": b2.to_dict("records"),
        "C_min_gen_cost": c.to_dict("records"),
        "D_model_side": d,
        "E_conduct": e.to_dict("records"),
        "F_rule19_enumeration": f,
        "G_hour_bias_bound": g.to_dict("records"),
        "H_headline": h.to_dict("records"),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(blob, indent=2, default=float))
    print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
