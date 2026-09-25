"""Reconstruct the ERCOT-136 / ERCOT-138 SCED offer instruments on a full
delivery-year corpus (ercot-169, mechanism-testing-matrix §5.1 item 13).

The three armed ERCOT margin identifications — ``COAL_OFFER_MARGIN_LEVEL_BY_ISO``
(ERCOT-137, coal ``_mustrun``), ``CC_COMMITTED_OFFER_LEVEL_BY_ISO`` (ERCOT-139,
gas-CC ``_committed``) and ``COAL_PEAK_OFFER_LEVEL_BY_ISO`` +
``COAL_PEAK_OFFER_GAS_HR_BY_ISO`` (ERCOT-140, coal ``_peak``) — were identified
on the four 2024–2025 60-Day SCED probe-day subsets and each declares in its
``constants.py`` block that *"2023 application is a declared extrapolation (no
2023 SCED disclosure exists) — the margin is fuel-invariant by construction"*.

The ercot-157 delivery-2023 NP3-965 corpus re-upload dissolves that premise (the
rule-14/23 data-vintage trigger ercot-168 executed for the per-plant curves).
Because all three are **margin forms** — 2023 is reached as
``level + HR × (fuel₂₀₂₃ − anchor)`` — the corpus does not merely enable
re-derivation, it **tests the invariance claim itself**. This module supplies the
2023 side of that test.

**Nothing here is a new construction.** Every statistic is the committed
instrument, imported from the probe that built it and fed delivery-year rows:

* :func:`curve_bottom` — ERCOT-136 §B1 ``bot_p50``: the HSL-capacity-weighted
  quantiles of ``p_bot``, the per-interval minimum finite ``Submitted
  TPO-Price{k}`` (min over columns, not column 1 — robust to out-of-order
  submission). Uses ``ercot136._curve`` and ``ercot136._wq`` verbatim.
* :func:`inc_bid_quantiles` — ERCOT-138 ``measured_curves``: the
  incremental-MW-weighted quantiles of the submitted curve's STEPS with the
  cumulative MW clipped into ``[LSL, HSL]`` so the min-load block is not
  double-counted. Calls ``ercot138.measured_curves`` verbatim; ``p90`` is the
  ERCOT-140 identifying statistic.
* :func:`coverage` — the ERCOT-123 headroom decomposition, i.e. the
  RT-instrument licensing test of ERCOT-138 §3.4. Calls ``ercot123._decompose``
  verbatim and reproduces ``ercot123.section_a``'s own expressions for
  ``curve_share`` (the share of resource-intervals carrying a submitted curve —
  the artifact's literal definition, which the constants comments render loosely
  as "% of RT-dispatchable headroom") and ``a_offered`` (the headroom-weighted
  offered share).

Row filters are the ercot-123/144 set, unchanged and unrelaxed: ONLINE
telemetered status, numeric coercion, ``HSL > 0``, ``HSL > LSL``, ``HASL`` and
net output non-null, plus the delivery-year filter that drops the
publication-window bleed (the corpus is publication-month-keyed, delivery =
filename − 2). Timestamps convert CPT (the disclosure clock) → fixed CST (the
model clock) at load, the ercot-166 DST class closed at source, exactly as
``derive_coal_perplant_offer.load_corpus_coal`` does it.

Rule 13 ``[R-MEASURED]`` scope: a measured corpus read on an already-accepted
convention. No ``ScenarioConfig`` field is written, no solve path is touched, no
residual is consulted. Rule 22 ``[R-HOLDOUT]``: :func:`load_corpus_year` refuses
any year outside the 2023–2025 training window.

**ercot-170 extension (matrix §5.1 item 11) — the CAPABILITY census.**
:func:`capability_census` adds the second half this module needed for the CC
headroom/capability object: a per-TRAIN capability roll-up over a delivery year.
It is an EXTENSION, never a rewrite — the functions above are untouched, and the
census imports ``ercot163_cc_commitment_state_census``'s ``_cap_ref`` /
``_train`` / ``_state_of`` / ``_hoy`` **verbatim** for exactly the reason
ercot-169 imported ercot136/138: re-deriving them would make this session's
numbers incomparable to the ercot-163 record they must bridge.

It carries ONE declared row-filter delta from the ercot-123/144 set the
instruments above use, pre-registered in
``docs/PRECOMMIT-ercot170-cc-headroom-crosswalk-2026-08-05.md`` §1a: the
capability census applies **no telemetered-status filter**. A capability
denominator that drops ``OUT``/``OFF`` rows is biased toward committed capacity
and would measure commitment — the object ercot-163 already closed — instead of
capability. The ONLINE-filtered conduct statistics remain available, unchanged,
through :func:`load_corpus_year`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO / "src"), str(REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The NP3-965 full-year corpus root (ercot-157 re-upload), publication-month
#: keyed: a ``YYYY-MM`` shard publishes delivery month ``YYYY-MM`` minus two.
#:
#: THE RTC+B BOUNDARY — this lane stops at delivery 2025-12-04. The
#: ``glob("*.parquet")`` in :func:`load_corpus_year` is NON-RECURSIVE on
#: purpose: the RTC+B-format parts (deliveries 2025-12-05..31) sit in the
#: ``rtcb-format-2026/`` subdirectory because RTC+B REMOVES ``HASL``, which
#: :func:`load_corpus_year` requires and filters on. Never make that glob
#: recursive or point this constant at the subdirectory — RTC+B deliveries are
#: calendar-2025, so the ``ts.dt.year == year`` filter would keep them. They are
#: readable only through ``scripts.lib.sced_rtcb_adapter`` (owner card D /
#: signature D1, ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``).
SCED_CORPUS_DIR = REPO / "data" / "raw" / "ercot" / "SCED"

#: Training window (rule 22 [R-HOLDOUT]). No other year may be loaded.
TRAIN_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})

#: The hour window three of the four identification subsets sample (CST). It
#: carries 77.9 % of the pooled COAL and 75.0 % of the pooled CC res-hours, so
#: it is the matched window for a like-for-like invariance test (precommit §1a).
MATCHED_HOURS: tuple[int, ...] = tuple(range(11, 23))


def _probe_imports():
    """Return the committed constructions, imported (never re-implemented)."""
    from scripts.probes import ercot123_coal_sced_reach as e123
    from scripts.probes import ercot136_coal_headroom_conduct as e136
    from scripts.probes import ercot138_coal_gas_ranking as e138

    return e123, e136, e138


def _census_imports():
    """Return the ERCOT-163 capability-census constructions, imported verbatim.

    ``_cap_ref`` (per-TRAIN p98 telemetered HSL over a delivery year, with the
    configuration aliases collapsed on the trailing ``_<config>`` segment),
    ``_train``, ``_state_of`` (telemetered status -> capability state) and
    ``_hoy`` (SCED timestamp -> hour-of-year on the model's fixed-standard
    clock) are the ercot-163 record this session's numbers must bridge to, so
    they are imported, never re-derived (ercot-170 precommit §1).
    """
    from scripts.probes import ercot163_cc_commitment_state_census as e163

    return e163


def load_corpus_year(
    year: int, classes: tuple[str, ...] = ("COAL", "CC")
) -> pd.DataFrame:
    """Delivery-``year`` rows of ``classes`` from the NP3-965 corpus.

    Applies the ERCOT-123 row filters unchanged (ONLINE telemetered status,
    numeric coercion, ``HSL > 0``, ``HSL > LSL``, ``HASL`` and net output
    non-null) plus the delivery-year filter, and converts CPT → fixed CST.

    Args:
        year: Delivery year to load. Must be inside :data:`TRAIN_YEARS`.
        classes: Comparison classes to keep, via ``ercot123.TYPE_TO_CLASS``
            (``CLLIG → COAL``, ``CCGT90``/``CCLE90 → CC``).

    Returns:
        The filtered frame carrying ``cls``, ``ts`` (CST, tz-naive), the
        coalesced ``netout`` column, and every column the decomposition and the
        two offer instruments read.

    Raises:
        SystemExit: If ``year`` is outside the training window (rule 22), the
            corpus is absent, or no row survives the filters.
    """
    if int(year) not in TRAIN_YEARS:
        raise SystemExit(
            f"--year {year}: rule 22 [R-HOLDOUT] — only {sorted(TRAIN_YEARS)} "
            "may be read here. An out-of-training year needs its tier marker "
            "and its own authorization."
        )
    import pyarrow.dataset as pads
    import pyarrow.parquet as pq

    e123, _e136, _e138 = _probe_imports()
    wanted_types = [t for t, c in e123.TYPE_TO_CLASS.items() if c in classes]

    cols = [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "Output Schedule",
        "HSL",
        "HASL",
        "HDL",
        "LSL",
        "Telemetered Net Output ",
        *e123.AS_UP_COLS,
        *e123.TPO_MW,
        *e123.TPO_PR,
    ]
    files = sorted(SCED_CORPUS_DIR.glob("*.parquet"))
    if not files:
        raise SystemExit(f"no NP3-965 corpus shards under {SCED_CORPUS_DIR}")

    # Per-shard column intersection, exactly as ``ercot123.load_sced`` does it:
    # ``Ancillary Service ECRS`` is absent from every shard publishing a
    # delivery month before 2023-06 because the PRODUCT did not exist yet. Its
    # absence is immaterial to every statistic taken here — the decomposition's
    # AS bucket is ``HSL − HASL`` (telemetered), not the award columns, and
    # ``up_as`` is a reported diagnostic only — but it is filled explicitly
    # rather than allowed to fail or to silently drop the shard.
    frames = []
    for f in files:
        have = set(pq.ParquetFile(f).schema_arrow.names)
        t = pads.dataset(f).to_table(
            columns=[c for c in cols if c in have],
            filter=pads.field("Resource Type").isin(wanted_types),
        )
        if t.num_rows:
            frames.append(t.to_pandas())
    df = pd.concat(frames, ignore_index=True)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan

    df["cls"] = df["Resource Type"].map(e123.TYPE_TO_CLASS)
    df = df[df["cls"].notna()]
    df = df[df["Telemetered Resource Status"].astype(str).str.strip().isin(e123.ONLINE)]
    num = [
        "Output Schedule",
        "HSL",
        "HASL",
        "HDL",
        "LSL",
        "Telemetered Net Output ",
        *e123.AS_UP_COLS,
        *e123.TPO_MW,
        *e123.TPO_PR,
    ]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # ERCOT-123's coalesced net-output name; the pre-December-2025 spelling is
    # the only one this corpus carries.
    df[e123.NETOUT] = df["Telemetered Net Output "]

    ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    loc = ts.dt.tz_localize(
        "America/Chicago", ambiguous=False, nonexistent="shift_forward"
    )
    df["ts_cpt"] = ts
    df["ts"] = loc.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)

    df = df[(df["HSL"] > 0) & (df["HSL"] > df["LSL"])]
    df = df[df["HASL"].notna() & df[e123.NETOUT].notna()]
    df = df[df["ts"].dt.year == int(year)]
    if df.empty:
        raise SystemExit(f"no delivery-{year} rows survived the filters")
    df["month"] = df["ts"].dt.month
    df["hour"] = df["ts"].dt.hour
    return df.reset_index(drop=True)


def restrict_hours(
    df: pd.DataFrame, hours: tuple[int, ...] | None, clock: str = "cst"
) -> pd.DataFrame:
    """Restrict to an hour window on the CST (default) or raw CPT clock.

    ``clock="cpt"`` is the precommit §1a sensitivity read: it bounds how much of
    any measured difference is attributable to the clock convention rather than
    to conduct (the identification subsets were built before the ercot-166
    CPT→CST discipline and carry raw disclosure timestamps).
    """
    if hours is None:
        return df
    col = df["ts"] if clock == "cst" else df["ts_cpt"]
    return df[col.dt.hour.isin(list(hours))]


def curve_bottom(df: pd.DataFrame) -> dict:
    """ERCOT-136 §B1: HSL-cap-weighted quantiles of the submitted curve bottom.

    ``p_bot`` is the per-interval minimum finite ``Submitted TPO-Price{k}``;
    the statistic is its capacity-weighted p10/p25/p50/p75/p90 over the rows
    that carry a curve, using ERCOT-136's own ``_curve`` and ``_wq``. ``bot_p50``
    is the ERCOT-137 (COAL) and ERCOT-139 (CC) identifying statistic.
    """
    _e123, e136, _e138 = _probe_imports()
    P, M, ok = e136._curve(df)
    hsl = df["HSL"].to_numpy(float)
    p_bot = np.where(ok, P, np.inf).min(axis=1)
    sel = ok.any(axis=1) & np.isfinite(p_bot)
    q = (0.10, 0.25, 0.50, 0.75, 0.90)
    vals = e136._wq(p_bot[sel], hsl[sel], q)
    return {
        "res_hours": int(sel.sum()),
        "resources": int(df.loc[sel, "Resource Name"].nunique()),
        **{f"bot_p{int(x * 100)}": v for x, v in zip(q, vals)},
        "bot_mean_capwtd": float(np.average(p_bot[sel], weights=hsl[sel]))
        if sel.any()
        else float("nan"),
    }


def inc_bid_quantiles(df: pd.DataFrame) -> dict:
    """ERCOT-138 ``measured_curves``: incremental-MW-weighted bid quantiles.

    The above-min-load instrument: each submitted curve STEP contributes its own
    MW at its own price with the cumulative MW clipped into ``[LSL, HSL]``.
    ``inc_bid_q["p90"]`` is the ERCOT-140 identifying statistic.
    """
    _e123, _e136, e138 = _probe_imports()
    return e138.measured_curves(df)


def coverage(df: pd.DataFrame) -> dict:
    """The ERCOT-123 headroom decomposition — the §3.4 licensing test.

    Reproduces ``ercot123.section_a``'s own expressions on the decomposed frame:
    ``curve_share`` (share of resource-intervals carrying a submitted curve —
    the licensing quantity, gated in the ercot-169 precommit §1b) alongside the
    headroom-weighted ``a_offered`` / ``b_selfsched`` / ``e_residual`` split and
    ``lsl_over_hsl`` / ``loading``.
    """
    e123, _e136, _e138 = _probe_imports()
    g = e123._decompose(df)
    h_rt, h_tel = g["h_rt"].sum(), g["h_tel"].sum()
    return {
        "res_hours": int(len(g)),
        "resources": int(g["Resource Name"].nunique()),
        "HSL_GW": float(g["HSL"].mean() / 1e3),
        "curve_share": float(g["has_curve"].mean()),
        "a_offered": float(g["off_mw"].sum() / h_rt) if h_rt > 0 else float("nan"),
        "b_selfsched": float(g["ss_mw"].sum() / h_rt) if h_rt > 0 else float("nan"),
        "e_residual": float(g["res_mw"].sum() / h_rt) if h_rt > 0 else float("nan"),
        "c_as_of_Htel": float(g["as_mw"].sum() / h_tel) if h_tel > 0 else float("nan"),
        "lsl_over_hsl": float(g["LSL"].sum() / g["HSL"].sum()),
        "loading": float(g[e123.NETOUT].sum() / g["HSL"].sum()),
    }


def year_instruments(
    year: int,
    cls: str,
    hours: tuple[int, ...] | None = MATCHED_HOURS,
    clock: str = "cst",
    df: pd.DataFrame | None = None,
) -> dict:
    """All three instruments for one class-year, on one hour window.

    Args:
        year: Delivery year (training window only).
        cls: ``"COAL"`` or ``"CC"``.
        hours: Hour window, or ``None`` for the full day.
        clock: ``"cst"`` (the model clock, default) or ``"cpt"`` (raw
            disclosure clock — the precommit §1a convention sensitivity).
        df: An already-loaded corpus frame, to avoid re-reading 315 shards.

    Returns:
        A block carrying the window description, the coverage/licensing row, the
        ERCOT-136 curve-bottom row and the ERCOT-138 incremental-bid row.
    """
    base = load_corpus_year(year) if df is None else df
    d = restrict_hours(base[base["cls"] == cls], hours, clock)
    if d.empty:
        raise SystemExit(f"no delivery-{year} {cls} rows in the requested window")
    return {
        "year": int(year),
        "class": cls,
        "hours": "full-day"
        if hours is None
        else f"h{min(hours)}-{max(hours)} {clock.upper()}",
        "days": int(d["ts"].dt.normalize().nunique()),
        "coverage": coverage(d),
        "curve_bottom": curve_bottom(d),
        "inc_bid": inc_bid_quantiles(d),
    }


def monthly_curve_bottom(df: pd.DataFrame, cls: str, hours=MATCHED_HOURS) -> list[dict]:
    """Per-month ``bot_p50`` — the within-year dispersion read (precommit §1a)."""
    d = restrict_hours(df[df["cls"] == cls], hours)
    out = []
    for m, g in d.groupby("month", observed=True):
        cb = curve_bottom(g)
        out.append(
            {"month": int(m), "res_hours": cb["res_hours"], "bot_p50": cb["bot_p50"]}
        )
    return out


def monthly_inc_p90(df: pd.DataFrame, cls: str, hours=MATCHED_HOURS) -> list[dict]:
    """Per-month incremental-bid ``p90`` — the limb-C within-year dispersion."""
    d = restrict_hours(df[df["cls"] == cls], hours)
    out = []
    for m, g in d.groupby("month", observed=True):
        mc = inc_bid_quantiles(g)
        out.append(
            {
                "month": int(m),
                "res_hours": mc["res_hours"],
                "p90": mc["inc_bid_q"]["p90"],
            }
        )
    return out


# --------------------------------------------------------------------------
# The ercot-169 fuel-invariance test — one registry, one arithmetic
# --------------------------------------------------------------------------
#: The three armed ERCOT margin identifications under test, each described by
#: everything its verdict needs. Values are read back from the committed
#: constants and the committed identification artifacts — nothing here is a new
#: number. ``band_usd`` is the identification's OWN cited cross-subset
#: dispersion expressed in $/MWh on the derives' half-range construction
#: ``100 × (max − min) / (2 × level)``; ``licence`` is the class minimum of
#: ``curve_share`` over the four subsets the constant was licensed on. Both are
#: pre-registered in ``docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md``
#: §§1b/2 and may not be moved after measurement.
LIMBS: dict[str, dict] = {
    "coal_mustrun": {
        "limb": "A",
        "constant": "COAL_OFFER_MARGIN_LEVEL_BY_ISO",
        "mechanism": "coal_offer_net_revenue_margin",
        "lane": "ERCOT-137",
        "cls": "COAL",
        "instrument": ("curve_bottom", "bot_p50"),
        "hr": 10.9832,  # derive_coal_offer_margin_anchor hr_capwtd (static fleet)
        "hr_source": "ERCOT-137 derive hr_capwtd (ercot135 per-plant, identical in all three years)",
        "fuel": "coal",
        "band_usd": 0.9300,  # +/-5.86 % raw half-range (16.86-15.00)/(2*15.8807)
        "band_note": "+/-5.86 % raw half-range; ERCOT-137 precommit P7 states the same "
        "tolerance as +/-$1.00, so $0.9300-$1.0000 is the declared marginal zone",
        "licence": 0.9876,
    },
    "cc_committed": {
        "limb": "B",
        "constant": "CC_COMMITTED_OFFER_LEVEL_BY_ISO",
        "mechanism": "cc_committed_offer_margin",
        "lane": "ERCOT-139",
        "cls": "CC",
        "instrument": ("curve_bottom", "bot_p50"),
        "hr": 7.8521,  # HR_implied, measured from the disclosure itself
        "hr_source": "ERCOT-139 HR_implied (the corpus's own measured fuel response)",
        "fuel": "gas",
        "band_usd": 0.6699,  # +/-6.47 % anchored, the value cited in constants.py
        "band_note": "+/-6.47 % anchored (dispersion_anchored_pct)",
        "licence": 0.95054,
    },
    "coal_peak": {
        "limb": "C",
        "constant": "COAL_PEAK_OFFER_LEVEL_BY_ISO",
        "mechanism": "coal_peak_offer_margin",
        "lane": "ERCOT-140",
        "cls": "COAL",
        "instrument": ("inc_bid", "p90"),
        "hr": 10.4100,  # COAL_PEAK_OFFER_GAS_HR_BY_ISO — the GAS slope
        "hr_source": "COAL_PEAK_OFFER_GAS_HR_BY_ISO (gas-parity slope, ERCOT-140)",
        "fuel": "gas",
        "band_usd": 2.5062,  # +/-7.12 % anchored, the value cited in constants.py
        "band_note": "+/-7.12 % anchored (dispersion_anchored_pct)",
        "licence": 0.9876,
    },
}


def assess_limb(key: str, block: dict, fuel_year: float, armed: float) -> dict:
    """Apply the ercot-169 pre-registered decision rule to one limb.

    Args:
        key: A :data:`LIMBS` key.
        block: A :func:`year_instruments` block for that limb's class/window.
        fuel_year: The solve year's delivered fuel on the identification's OWN
            basis ($/MMBtu) — delivered coal (``ercot135``) for limb A, the
            ERCOT-138 §J CC ``fuel_capwtd`` for limbs B and C.
        armed: The armed constant's value ($/MWh), read from ``constants.py``.

    Returns:
        The verdict block: the measured instrument, the removed fuel response,
        the anchored ``level_year``, its deviation from ``armed``, the licensing
        read, and the verdict — one of ``CONFIRMED`` / ``CONFIRMED-MARGINAL`` /
        ``REFUTED`` / ``NOT-IDENTIFIABLE``. **A limb that fails its coverage
        licence returns NOT-IDENTIFIABLE and its value comparison is reported
        UNLICENSED — the verdict is withheld in BOTH directions, because a
        biased instrument can manufacture a false refutation exactly as easily
        as a false confirmation (precommit §1b: the bar is not lowered, and it
        is not lowered against the constant either).**
    """
    spec = LIMBS[key]
    anchor = 1.7387 if spec["fuel"] == "coal" else 2.2494
    section, stat = spec["instrument"]
    measured = (
        block[section][stat]
        if section == "curve_bottom"
        else block["inc_bid"]["inc_bid_q"][stat]
    )
    term = spec["hr"] * (fuel_year - anchor)
    level = measured - term
    delta = level - armed
    cov = block["coverage"]["curve_share"]
    licensed = cov >= spec["licence"]
    inside = abs(delta) <= spec["band_usd"]
    if not licensed:
        verdict = "NOT-IDENTIFIABLE"
    elif inside:
        verdict = (
            "CONFIRMED-MARGINAL"
            if key == "coal_mustrun" and abs(delta) > 0.9300
            else "CONFIRMED"
        )
    else:
        verdict = "REFUTED"
    return {
        "limb": spec["limb"],
        "constant": spec["constant"],
        "mechanism": spec["mechanism"],
        "lane": spec["lane"],
        "class": spec["cls"],
        "window": block["hours"],
        "instrument": f"{section}.{stat}",
        "measured_usd_mwh": round(float(measured), 4),
        "fuel_year_usd_mmbtu": round(float(fuel_year), 4),
        "anchor_usd_mmbtu": anchor,
        "hr": spec["hr"],
        "hr_source": spec["hr_source"],
        "fuel_response_removed_usd_mwh": round(float(term), 4),
        "level_year_usd_mwh": round(float(level), 4),
        "armed_usd_mwh": armed,
        "delta_usd_mwh": round(float(delta), 4),
        "band_usd_mwh": spec["band_usd"],
        "band_note": spec["band_note"],
        "delta_over_band": round(abs(float(delta)) / spec["band_usd"], 2),
        "curve_share": round(float(cov), 5),
        "licence_threshold": spec["licence"],
        "licensed": bool(licensed),
        "value_read": "INSIDE" if inside else "OUTSIDE",
        "verdict": verdict,
    }


#: Committed ERCOT-138 §J ``fuel_capwtd`` ($/MMBtu) the footing gate reproduces.
ERCOT138_FUEL_CAPWTD: dict[str, dict[int, float]] = {
    "CC": {2024: 2.213, 2025: 3.232},
    "COAL": {2024: 1.748, 2025: 1.630},
}

#: Footing tolerance on that reproduction (precommit §1c), $/MMBtu.
FOOTING_TOL: float = 0.02

#: Delivered coal on the ERCOT-137 anchor's OWN basis (``ercot135`` per-plant
#: cap-weighted; the armed anchor 1.7387 is the plain mean of these three), so
#: limb A needs no reconstruction at all.
COAL_FUEL_BY_YEAR: dict[int, float] = {2023: 1.8169, 2024: 1.7556, 2025: 1.6436}

#: The keeper whose no-LP fleet reconstruction supplies the delivered-fuel
#: array. ERCOT-138's own bundle (``ercot137_margin_arm``) is no longer on disk,
#: so basis-consistency is re-established by REPRODUCING its committed 2024/2025
#: values rather than assumed.
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot168_yearcurves_B"


def fuel_basis_by_year(years: tuple[int, ...] = (2024, 2025, 2023)) -> dict:
    """The ERCOT-138 §J delivered-fuel basis, reconstructed with NO LP.

    Takes the §J statistic verbatim — ``Σ pmax·fuel_price / Σ pmax`` over the
    class's ``committed``/``econ`` model rows, ``fuel_price`` being the row's
    annual-mean delivered fuel captured at the ``apply_coal_tranches`` seam —
    from :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` on
    :data:`KEEPER_BUNDLE`. Years are reconstructed SEQUENTIALLY (rule 12).

    Returns:
        ``{"years": {y: {"CC": …, "COAL": …}}, "footing": [...],
        "footing_pass": bool, "gas_2023": …}``. **The footing list is the gate**:
        the reconstruction must reproduce the committed 2024/2025 values within
        :data:`FOOTING_TOL`, else the basis moved between ERCOT-138 and the
        keeper and no year's value is comparable to the identification's.
    """
    from market_sim.config.plant_taxonomy import COAL_CLASSES
    from scripts.probes.ercot138_coal_gas_ranking import (
        MODEL_CC_GROUPS,
        _tranche_role,
    )

    # The model's coal rows carry their coal SUBCLASS (COAL-SUB, 2026-09-25);
    # the SCED corpus's COAL control class pools every rank, as the former bare
    # ``COAL`` group did.
    MODEL_COAL_GROUPS = COAL_CLASSES

    from scripts import run_calibration as rc
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    out: dict = {"bundle": KEEPER_BUNDLE.name, "years": {}}
    for year in years:
        real_coal = rc.apply_coal_tranches
        box: dict = {}

        def _pre_spy(
            mc, gens, fleet_arrays, fuel_fracs, fuel_prices, config=None, **kw
        ):
            box["fuel_price"] = np.asarray(fuel_prices, dtype=float).mean(axis=1)
            real_coal(mc, gens, fleet_arrays, fuel_fracs, fuel_prices, config, **kw)

        rc.apply_coal_tranches = _pre_spy
        try:
            state, _meta = reconstruct_bundle_fleet(KEEPER_BUNDLE, year, verbose=False)
        finally:
            rc.apply_coal_tranches = real_coal

        fa, fleet = state["fleet_arrays"], state["fleet"]
        grp = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
        role = np.array([_tranche_role(str(u)) for u in fa.unit_ids])
        pmax = np.asarray(fa.pmax, dtype=float)
        fp = box["fuel_price"]
        out["years"][int(year)] = {
            cls: round(
                float((fp[i] * pmax[i]).sum() / pmax[i].sum()),
                4,
            )
            for cls, groups in (("CC", MODEL_CC_GROUPS), ("COAL", MODEL_COAL_GROUPS))
            for i in [
                np.flatnonzero(
                    np.isin(grp, list(groups)) & np.isin(role, ["committed", "econ"])
                )
            ]
        }

    footing = [
        {
            "class": cls,
            "year": y,
            "reconstructed": out["years"][y][cls],
            "committed": committed,
            "delta": round(out["years"][y][cls] - committed, 4),
            "tol": FOOTING_TOL,
            "pass": bool(abs(out["years"][y][cls] - committed) <= FOOTING_TOL),
        }
        for cls, by_year in ERCOT138_FUEL_CAPWTD.items()
        for y, committed in by_year.items()
        if y in out["years"]
    ]
    out["footing"] = footing
    out["footing_pass"] = all(f["pass"] for f in footing)
    if 2023 in out["years"]:
        out["gas_2023"] = out["years"][2023]["CC"]
    return out


# --------------------------------------------------------------------------
# The ercot-170 capability census — per-TRAIN, over a delivery year
# --------------------------------------------------------------------------

#: The ERCOT-163 states counted as reality-side CAPABILITY in the ercot-170
#: attribution identity (precommit §1c): committed or intra-hour startable.
#: ``OUT`` and plain ``OFF`` capability is rolled up too, and reported, but is
#: NOT reality-side capability — a resource on outage cannot serve the tail.
COMMITTED_OR_STARTABLE: tuple[str, ...] = (
    "ONLINE",
    "ONTEST",
    "OFFLINE_STARTABLE",
    "TRANSITION",
)

#: SCED ``Resource Type`` values forming the combined-cycle universe.
CC_RESTYPES: tuple[str, ...] = ("CCGT90", "CCLE90")


def capability_census(
    year: int,
    hours: np.ndarray,
    restypes: tuple[str, ...] = CC_RESTYPES,
) -> dict:
    """Per-TRAIN capability roll-up over ``hours`` of delivery ``year``.

    The reality side of the ercot-170 attribution identity. Every construction
    is the ERCOT-163 one, imported verbatim via :func:`_census_imports`:
    ``_cap_ref`` for the fixed per-train capability denominator (p98 telemetered
    HSL over the whole delivery year), ``_train`` for the configuration-alias
    collapse, ``_state_of`` for the capability-state taxonomy and ``_hoy`` for
    the model's fixed-standard clock.

    **Row filters (precommit §1a).** ``Resource Type`` in ``restypes``, the
    delivery-year filter, and NO telemetered-status filter — the one declared
    delta from the ercot-123/144 set, because a capability denominator that
    drops ``OUT``/``OFF`` rows measures commitment, not capability.

    Args:
        year: Delivery year (training window only, rule 22).
        hours: Hours-of-year (0..8759, model fixed-standard clock) to census.
        restypes: SCED ``Resource Type`` values forming the universe.

    Returns:
        ``{"trains": {train: {...}}, "totals": {...}, "n_intervals": int}``.
        Each train carries ``cap_ref_mw`` (the year-long p98 denominator) and,
        over the requested hours, the interval-mean ``hsl_mw`` / ``hasl_mw`` /
        ``basepoint_mw`` split by capability state plus the committed-or-
        startable aggregates the identity consumes.

    Raises:
        SystemExit: If ``year`` is outside the training window, or no shard
            carries a row of ``restypes``.
    """
    if int(year) not in TRAIN_YEARS:
        raise SystemExit(
            f"capability_census(year={year}): rule 22 [R-HOLDOUT] — only "
            f"{sorted(TRAIN_YEARS)} may be read here."
        )
    e163 = _census_imports()
    if int(year) != int(e163.YEAR):
        # ``_cap_ref`` is imported VERBATIM and reads its own module-level YEAR,
        # so it can only be trusted on the year it was written for. Widening it
        # would mean editing the committed construction — refused (precommit §1).
        raise SystemExit(
            f"capability_census(year={year}): ercot163._cap_ref is pinned to "
            f"delivery {e163.YEAR}. Extending it to another year is an edit to a "
            "committed construction, not a call — do that in its own session."
        )
    from scripts.data.derive_ercot_sced_offer_wall import (
        _delivery_year_rows,
        _sced_source_files,
    )

    files = _sced_source_files(int(year))
    if not files:
        raise SystemExit(f"no SCED corpus shards for delivery {year}")

    # Pass 1 — the fixed per-train capability denominator, ERCOT-163 verbatim.
    ref, cls = e163._cap_ref(files)
    # ``_cap_ref`` censuses BOTH the CC and CT universes (it is the ERCOT-163
    # construction, unmodified); keep the trains whose census class is the one
    # this call's ``restypes`` selects, so a train that telemetered no row in
    # the requested hours still appears with its capability denominator rather
    # than vanishing from the accounting.
    want_cls = {e163.CLASS_OF_RESTYPE[t] for t in restypes}
    keep_trains = {n for n in ref.index if str(cls.get(n, "")) in want_cls}

    want = np.zeros(8760, dtype=bool)
    want[np.asarray(hours, dtype=int)] = True

    cols = [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "HSL",
        "HASL",
        "Base Point",
        "LSL",
    ]
    # accumulators: train -> state -> summed MW over the censused intervals
    acc: dict[str, dict[str, dict[str, float]]] = {}
    seen_iv: set = set()
    for path in files:
        df = pd.read_parquet(path, columns=cols)
        df = _delivery_year_rows(df, int(year))
        df = df[df["Resource Type"].isin(list(restypes))].copy()
        if df.empty:
            continue
        df["hoy"] = e163._hoy(df["SCED Time Stamp"])
        df = df[(df["hoy"] >= 0) & (df["hoy"] < 8760)]
        df = df[want[df["hoy"].to_numpy(int)]]
        if df.empty:
            continue
        for c in ("HSL", "HASL", "Base Point", "LSL"):
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        df["train"] = df["Resource Name"].map(e163._train)
        df["state"] = e163._state_of(df["Telemetered Resource Status"])
        seen_iv.update(df["SCED Time Stamp"].unique().tolist())
        g = df.groupby(["train", "state"], observed=True)[
            ["HSL", "HASL", "Base Point"]
        ].sum()
        for (tr, st), row in g.iterrows():
            b = acc.setdefault(str(tr), {}).setdefault(
                str(st), {"hsl": 0.0, "hasl": 0.0, "bp": 0.0}
            )
            b["hsl"] += float(row["HSL"])
            b["hasl"] += float(row["HASL"])
            b["bp"] += float(row["Base Point"])

    n_iv = max(len(seen_iv), 1)
    trains: dict[str, dict] = {}
    for tr in sorted(set(acc) | keep_trains):
        by_state = acc.get(tr, {})
        rec = {
            "cap_ref_mw": round(float(ref.get(tr, float("nan"))), 2),
            "restype_class": str(cls.get(tr, "")),
            "hsl_mw_by_state": {
                s: round(v["hsl"] / n_iv, 2) for s, v in sorted(by_state.items())
            },
            "hsl_mw": round(
                sum(
                    v["hsl"] for s, v in by_state.items() if s in COMMITTED_OR_STARTABLE
                )
                / n_iv,
                2,
            ),
            "hasl_mw": round(
                sum(
                    v["hasl"]
                    for s, v in by_state.items()
                    if s in COMMITTED_OR_STARTABLE
                )
                / n_iv,
                2,
            ),
            "basepoint_mw": round(
                sum(v["bp"] for s, v in by_state.items() if s in COMMITTED_OR_STARTABLE)
                / n_iv,
                2,
            ),
            "hsl_mw_out": round(
                sum(
                    v["hsl"]
                    for s, v in by_state.items()
                    if s not in COMMITTED_OR_STARTABLE
                )
                / n_iv,
                2,
            ),
            "present": bool(by_state),
        }
        trains[tr] = rec

    tot = {
        k: round(sum(t[k] for t in trains.values()), 2)
        for k in ("hsl_mw", "hasl_mw", "basepoint_mw", "hsl_mw_out")
    }
    tot["cap_ref_mw"] = round(
        float(np.nansum([t["cap_ref_mw"] for t in trains.values()])), 2
    )
    tot["n_trains"] = len(trains)
    tot["n_trains_present"] = int(sum(t["present"] for t in trains.values()))
    return {
        "year": int(year),
        "n_hours": int(want.sum()),
        "n_intervals": n_iv,
        "restypes": list(restypes),
        "row_filter": (
            "Resource Type in restypes + delivery-year; NO telemetered-status "
            "filter (ercot-170 precommit §1a declared delta)"
        ),
        "trains": trains,
        "totals": tot,
    }


def verify_year(
    key: str, year: int, armed: float, df: pd.DataFrame | None = None
) -> dict:
    """One limb's full ercot-169 verification for one delivery year.

    The entry point the three frozen derives' ``--year`` modes call. Resolves
    the limb's own fuel basis (committed for coal, no-LP reconstruction with the
    footing gate for gas), reconstructs the limb's own instrument on the matched
    and full-day windows, and applies the pre-registered decision rule.
    """
    spec = LIMBS[key]
    if spec["fuel"] == "coal":
        fuel_year, fuel_block = (
            COAL_FUEL_BY_YEAR[int(year)],
            {
                "basis": "ercot135 per-plant cap-weighted delivered coal (the ERCOT-137 "
                "anchor's own basis; committed, no reconstruction needed)"
            },
        )
    else:
        fuel_block = fuel_basis_by_year()
        if not fuel_block["footing_pass"]:
            return {
                "limb": spec["limb"],
                "constant": spec["constant"],
                "verdict": "NOT-IDENTIFIABLE",
                "reason": "fuel-basis footing FAILED (precommit §1c) — the delivered-gas "
                "basis moved between ERCOT-138 and the keeper, so no year's value is "
                "comparable to the identification's",
                "fuel_basis": fuel_block,
            }
        fuel_year = fuel_block["years"][int(year)]["CC"]

    base = load_corpus_year(year) if df is None else df
    t1 = year_instruments(year, spec["cls"], MATCHED_HOURS, "cst", base)
    t2 = year_instruments(year, spec["cls"], None, "cst", base)
    return {
        "year": int(year),
        "fuel_basis": fuel_block,
        "T1_gating": assess_limb(key, t1, fuel_year, armed),
        "T2_reported": assess_limb(key, t2, fuel_year, armed),
    }
