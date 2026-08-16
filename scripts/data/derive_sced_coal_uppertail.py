#!/usr/bin/env python
"""ERCOT-124 — the measured coal offer-curve UPPER TAIL, from the 60-Day SCED disclosure.

Phase 1 of the lane chartered by
``docs/DIAGNOSIS-ercot123-coal-sced-reach-2026-07-27.md`` §5/§7.2. That session
CLOSED the coal offer-*reach* question (coal offers 99.4-100.0 % of its
RT-dispatchable headroom into SCED, a *higher* reach than the CC control) and
named exactly one surviving defect: above \\$25 the measured RT coal supply curve
needs \\$500 to reach 1.00 while the model's coal stack is fully offered by
\\$32-34 (ERCOT-122 §3). This derivation measures that tail.

What is measured
----------------
Per **delivery year** and per **rank band**, the share of telemetered ``HASL``
that carries a submitted RT energy offer at or below each price edge — the
ERCOT-117 §1.1 convention (``supply(x) = clip(max{MW_k : price_k <= x}, LSL,
HASL)``, curve-carrying units floored at ``LSL``), so the numbers are directly
comparable to that session's model-side coal supply shares. Each band carries
its **capacity ``coverage``** — the share of fleet ``HSL`` held by resources that
contribute any MW to that band — recorded exactly as
``offer_curve_dam_hrmults_coal_yearly.json`` records it, plus a top-1
concentration. Coverage is the receipt that stops a tail band measured on a
minority of resources being applied to 100 % of the class: that substitution is
precisely what ERCOT-122 §1 refuted in the pooled ``COAL_LIGNITE econ_high``
2.856, and this artifact is built so the same mistake cannot be made silently.

Basis (ERCOT-122 §2)
--------------------
Multipliers are on the **delivered coal price the model dispatches on**
(``COAL_PRICE_LIGNITE_BY_YEAR`` / ``COAL_PRICE_PRB_BY_YEAR`` via
``derive_dam_offer_hrmults.coal_fuel_price``), never Henry Hub — the EP gas-basis
correction is gas-specific and has no coal analogue. Both output groups read the
SAME measured distribution and differ only by that divisor, exactly as the
ERCOT-122 coal artifact's two groups do.

How the price edges were chosen (rule 23 ``[R-FROZEN-DERIVE]``)
--------------------------------------------------------------
The edges are fixed from the **measured distribution's own structure**, before
any model quantity was read, and no edge was chosen because it moved a residual:

* ``$20`` / ``$25`` / ``$500`` are carried verbatim from the ERCOT-123 §5 grid,
  themselves fixed from this same measured RT distribution one session earlier.
* ``$35`` / ``$60`` / ``$100`` bound the three plateaus the measured cumulative
  curve exhibits above its \\$25 knee (it is flat 0.948->0.948 across \\$35-\\$40,
  0.954->0.954 across \\$50-\\$60, and 0.964->0.964 across \\$80-\\$100 in 2024).
* ``$150`` brackets the measured jump between \\$100 and \\$200, where the curve
  goes 0.964 -> 0.990 -> 0.998.
* ``$5000`` is the published ERCOT high system-wide offer cap (HCAP).

The model's own \\$32-34 top-of-stack is **reported against** this grid in the
diagnosis; it was never used to place an edge.

Variants
--------
Two are written for every year. ``all`` is the whole CLLIG fleet. ``ex_owner_split``
drops ``FPPYD1_FPP_G1_J02`` / ``FPPYD1_FPP_G2_J02`` — the **second owner's
registered share** of Fayette units 1 and 2. The same two physical units are also
registered as ``..._J01``, and the two shares of one machine offer \\$18.41/\\$18.74
against \\$150.10. That is an owner-share conduct on one jointly-owned plant, not
a class behaviour, and the model's fleet has no owner-share dimension to carry it
(``custom-bin-assignments.csv`` holds Fayette Power Project as ONE plant, code
6179). The pair is reported both ways so the class-representative residual is
visible rather than assumed.

Sampling — carry this caveat on every number
--------------------------------------------
The on-disk SCED subsets are **82 probe days across 2024-2025 only**; no 2023
SCED exists on disk and no full-span SCED exists at all. Three of the four
subsets sample **hours 11-22 only**, so the hour-of-day bias is bounded directly
in the ``_hour_of_day_bound`` block from the one all-24-hour subset rather than
assumed away. Nothing here is an annual statistic, and a probe-day supply share
is never multiplied by an annual hour count inside this script.

Usage
-----
    python scripts/data/derive_sced_coal_uppertail.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO, _REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config import paths  # noqa: E402

# The SCED loader is reused verbatim from the ERCOT-123 probe rather than
# re-written: it already coalesces the two ``Telemetered Net Output`` spellings
# and EXPLICITLY DROPS the December-2025 schema-revision intervals (in which
# HASL/LASL and the AS *award* block are gone and unrecoverable), instead of
# letting them silently NaN out of the aggregates.
from scripts.probes import ercot123_coal_sced_reach as sced  # noqa: E402
from scripts.data import derive_dam_offer_hrmults as dam  # noqa: E402

OUT_JSON = paths.CALIBRATION_DIR / "offer_curve_sced_coal_uppertail.json"

# See the module docstring for how each edge was fixed from the measured
# distribution. Monotone; the last edge is the published HCAP.
PRICE_EDGES: tuple[float, ...] = (20.0, 25.0, 35.0, 60.0, 100.0, 150.0, 500.0, 5000.0)

# Output groups differ ONLY by the delivered-coal divisor (ERCOT-122 §2); the
# disclosure carries no lignite/PRB split.
OUTPUT_GROUPS: tuple[str, ...] = ("COAL_LIGNITE", "COAL_PRB")

# Second-owner registered shares of the jointly-owned Fayette units 1 and 2 —
# see the module docstring's "Variants" section.
OWNER_SPLIT_RESOURCES: frozenset[str] = frozenset(
    {"FPPYD1_FPP_G1_J02", "FPPYD1_FPP_G2_J02"}
)


def band_mw(g: pd.DataFrame) -> tuple[dict[float, np.ndarray], np.ndarray, np.ndarray]:
    """Per-interval offered MW in each price band, plus HASL and HSL.

    The monotone TPO staircase is evaluated at every edge as
    ``supply(x) = clip(max{MW_k : price_k <= x}, LSL, HASL)``, forced
    non-decreasing across edges; the MW in band ``(x_{i-1}, x_i]`` is the
    difference. Intervals with no submitted curve contribute nothing above
    ``LSL``, which is the ERCOT-117 §1.1 floor convention.
    """
    prices = g[sced.TPO_PR].to_numpy(float)
    mws = g[sced.TPO_MW].to_numpy(float)
    ok = np.isfinite(prices) & np.isfinite(mws)
    hsl = g["HSL"].to_numpy(float)
    hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
    lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hasl)
    prev = np.zeros(len(g))
    out: dict[float, np.ndarray] = {}
    for edge in PRICE_EDGES:
        sel = ok & (prices <= edge)
        sup = np.max(np.where(sel, mws, -np.inf), axis=1)
        sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
        sup = np.maximum(sup, prev)
        out[edge] = sup - prev
        prev = sup
    return out, hasl, hsl


def measure(g: pd.DataFrame) -> dict:
    """Band shares, cumulative supply curve, coverage and concentration.

    ``share`` is MW-weighted over the fleet (sum band MW / sum HASL), never a
    per-unit mean. ``coverage`` is the share of fleet HSL held by resources
    contributing any MW to the band — the ERCOT-122 selection-bias receipt.
    ``top1_concentration`` is the largest single resource's share of the band's
    MW, which coverage alone does not reveal.
    """
    bands, hasl, hsl = band_mw(g)
    den = float(hasl.sum())
    res = g["Resource Name"].to_numpy()
    fleet_hsl = pd.DataFrame({"res": res, "hsl": hsl}).groupby("res")["hsl"].max()
    cum = 0.0
    rows: dict[str, dict] = {}
    cumulative: dict[str, float] = {}
    prev_edge = 0.0
    for edge in PRICE_EDGES:
        mw = bands[edge]
        share = float(mw.sum()) / den if den > 0 else float("nan")
        cum += share
        per_res = pd.DataFrame({"res": res, "mw": mw}).groupby("res")["mw"].sum()
        contrib = per_res > 1e-6
        cov = (
            float(fleet_hsl[contrib].sum() / fleet_hsl.sum()) if contrib.any() else 0.0
        )
        total = float(per_res.sum())
        rows[f"({prev_edge:g},{edge:g}]"] = {
            "share_of_hasl": round(share, 5),
            "coverage": round(cov, 4),
            "n_resources": int(contrib.sum()),
            "top1_concentration": (
                round(float(per_res.max() / total), 3) if total > 0 else None
            ),
        }
        cumulative[f"<={edge:g}"] = round(cum, 5)
        prev_edge = edge
    return {
        "n_intervals": int(len(g)),
        "n_resources": int(len(fleet_hsl)),
        "hasl_mw_interval_mean": round(den / len(g), 1) if len(g) else None,
        "cumulative_supply_share_of_hasl": cumulative,
        "bands": rows,
        "tail_share_above_35": round(
            float(
                sum(
                    v["share_of_hasl"]
                    for k, v in rows.items()
                    if k != "(0,20]" and float(k.split(",")[1][:-1]) > 35.0
                )
            ),
            5,
        ),
    }


def hrmults(year: int, output_group: str, base_hr: float) -> dict:
    """The band edges restated as heat-rate multipliers on delivered coal.

    ``mult = edge_price / (delivered_coal_$/MMBtu x base_HR)`` — the units the
    model's coal offer surface consumes, so a band edge can be read straight
    against a ``COAL_PRB`` / ``COAL_LIGNITE`` curve band (rule: divide by the
    same fuel series the model later multiplies, ERCOT-118 FINDING §1).
    """
    fuel = dam.coal_fuel_price(output_group)[year]
    return {
        "delivered_fuel_usd_mmbtu": fuel,
        "base_hr": round(base_hr, 3),
        "edge_multipliers": {
            f"{edge:g}": round(edge / (fuel * base_hr), 3) for edge in PRICE_EDGES
        },
    }


def load_coal_frames() -> tuple[dict[int, pd.DataFrame], dict[str, dict]]:
    """Coal (CLLIG) SCED intervals pooled per delivery year, plus load coverage."""
    per_year: dict[int, list[pd.DataFrame]] = {}
    cov: dict[str, dict] = {}
    for tag, year, _fam in sced.SUBSETS:
        got = sced.load_sced(tag)
        if got is None:
            continue
        df, load_cov = got
        cov[tag] = load_cov
        per_year.setdefault(year, []).append(df[df["cls"] == "COAL"])
    return (
        {y: pd.concat(p, ignore_index=True) for y, p in sorted(per_year.items())},
        cov,
    )


def hour_of_day_bound() -> dict:
    """Bound the daytime-sampling bias on the ONE all-24-hour subset.

    Three of the four subsets sample hours 11-22 only. ERCOT-123 §8 bounded that
    bias for offer *reach*; the tail is a different moment and gets its own
    bound here rather than inheriting one.
    """
    got = sced.load_sced("2025_ercot86_tail_days")
    if got is None:
        return {}
    df, _ = got
    d = df[df["cls"] == "COAL"].copy()
    d["h"] = d["ts"].dt.hour
    day = d[(d["h"] >= 11) & (d["h"] <= 22)]
    night = d[(d["h"] < 11) | (d["h"] > 22)]
    return {
        "subset": "2025_ercot86_tail_days",
        "note": (
            "the only all-24-hour subset; if the tail were a daytime artifact the "
            "h11-22 share would exceed the h23-h10 share"
        ),
        "h11_22": measure(day)["tail_share_above_35"] if len(day) else None,
        "h23_h10": measure(night)["tail_share_above_35"] if len(night) else None,
    }


def dam_cross_instrument() -> dict:
    """The same tail measured on the DAM disclosure — the ONLY instrument covering 2023.

    No 2023 SCED exists on disk, so any 2023 application of an RT-identified tail
    is an extrapolation. This is the one available test of whether that
    extrapolation is supportable: the identical band construction on the 60-Day
    **DAM** Gen Resource curves, per delivery year 2023-2025, denominated in
    ``HSL`` (the DAM disclosure carries no ``HASL``).

    Read it against the RT tail, not as a substitute for it. DAM reach is only
    0.16-0.18 (ERCOT-122 §4), so this is a thin slice of a thin slice and is the
    low-coverage instrument ERCOT-122 §1 declined to adopt a level from — but it
    is the only 2023 evidence in existence, and a contradiction between the two
    instruments' year-trends is itself the answer to whether 2023 is identified.
    """
    df = dam._load_raw_cc_curve_points(dam.COAL_RESOURCE_TYPES, with_hour_status=True)
    out: dict[str, dict] = {}
    for year, g in df.groupby("year"):
        g = g[(g["hsl"] > g["lsl"]) & np.isfinite(g["curve_mw"])]
        key = ["delivery_date", "Hour Ending", "resource_name"]
        base = g.groupby(key).agg(hsl=("hsl", "max"), lsl=("lsl", "max"))
        hsl = base["hsl"].to_numpy(float)
        lsl = np.clip(base["lsl"].to_numpy(float), 0.0, hsl)
        prev = lsl.copy()
        cum = float(lsl.sum())
        den = float(hsl.sum())
        cumulative: dict[str, float] = {}
        for edge in PRICE_EDGES:
            sup = (
                g[g["curve_price"] <= edge]
                .groupby(key)["curve_mw"]
                .max()
                .reindex(base.index)
                .to_numpy(float)
            )
            sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hsl)
            sup = np.maximum(sup, prev)
            cum += float((sup - prev).sum())
            prev = sup
            cumulative[f"<={edge:g}"] = round(cum / den, 5) if den > 0 else None
        out[str(int(year))] = {
            "n_resource_hours": int(len(base)),
            "n_resources": int(base.index.get_level_values(2).nunique()),
            "cumulative_supply_share_of_hsl": cumulative,
            "tail_share_above_35": round(
                cumulative[f"<={PRICE_EDGES[-1]:g}"] - cumulative["<=35"], 5
            ),
        }
    return {
        "note": (
            "DAM instrument, denominated in HSL (no HASL in the DAM disclosure). "
            "The ONLY instrument covering 2023. Low-coverage (DAM reach 0.16-0.18) "
            "— do NOT read a level from it; read the year-trend against the RT tail."
        ),
        "years": out,
    }


def build() -> dict:
    frames, load_cov = load_coal_frames()
    base_hr = dam.output_base_hr(dam.class_base_hr(), ("COAL",))
    payload: dict = {
        "_provenance": {
            "iso": "ERCOT",
            "source": (
                "ERCOT 60-Day SCED Disclosure 60d_SCED_Gen_Resource_Data raw "
                "parquets, CLLIG (Coal and Lignite) submitted TPO energy curves, "
                "online telemetered statuses only"
            ),
            "method": (
                "share of telemetered HASL carrying a submitted RT offer at or "
                "below each price edge (ERCOT-117 §1.1 convention: supply(x) = "
                "clip(max{MW_k : price_k <= x}, LSL, HASL), curve-carrying units "
                "floored at LSL); MW-weighted fleet aggregate, per band capacity "
                "coverage and top-1 concentration recorded alongside"
            ),
            "basis": (
                "delivered coal $/MMBtu the model dispatches on "
                "(COAL_PRICE_LIGNITE_BY_YEAR / COAL_PRICE_PRB_BY_YEAR), NOT Henry "
                "Hub — the EP gas-basis correction is gas-specific and has no coal "
                "analogue (ERCOT-122 §2)"
            ),
            "rule23_citation": (
                "derived from the raw SCED disclosure against the ERCOT-124 "
                "charter's measurement question (the coal offer-curve upper tail "
                "named by DIAGNOSIS-ercot123 §5); price edges fixed from the "
                "measured distribution's own plateaus and jump BEFORE any model "
                "quantity was read; no residual entered the derivation and no "
                "edge was chosen because it moved one"
            ),
            "sampling": (
                "82 probe days, 2024-2025 ONLY — no 2023 SCED exists on disk and "
                "no full-span SCED exists at all. Three of four subsets sample "
                "hours 11-22 only; see _hour_of_day_bound. Nothing here is an "
                "annual statistic."
            ),
            "dec_2025_schema_drop": (
                "ERCOT revised the disclosure schema in December 2025 — HASL/LASL "
                "and the AS award block are dropped and unrecoverable. Those "
                "intervals are excluded explicitly by the reused ERCOT-123 "
                "load_sced(), never silently NaN-skipped; see load_coverage."
            ),
            "coverage_warning": (
                "A band's coverage is the share of fleet HSL held by resources "
                "that contribute ANY MW to it. A low-coverage band describes that "
                "subsample, NOT the class — applying one class-wide is exactly the "
                "error ERCOT-122 §1 refuted in the pooled COAL_LIGNITE econ_high "
                "2.856. Read coverage and top1_concentration before adopting."
            ),
            "price_edges": list(PRICE_EDGES),
            "owner_split_resources": sorted(OWNER_SPLIT_RESOURCES),
            "load_coverage": load_cov,
        },
        "_hour_of_day_bound": hour_of_day_bound(),
        "_dam_cross_instrument": dam_cross_instrument(),
    }
    for year, g in frames.items():
        block: dict = {
            "all": measure(g),
            "ex_owner_split": measure(
                g[~g["Resource Name"].isin(OWNER_SPLIT_RESOURCES)]
            ),
        }
        for grp in OUTPUT_GROUPS:
            block[grp] = hrmults(year, grp, base_hr)
        payload[str(year)] = block
    return payload


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--json-out",
        default=None,
        help=f"output path (default {OUT_JSON})",
    )
    args = ap.parse_args()
    payload = build()
    out = Path(args.json_out) if args.json_out else OUT_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}")
    for year in sorted(k for k in payload if k.isdigit()):
        for variant in ("all", "ex_owner_split"):
            m = payload[year][variant]
            print(
                f"  {year} {variant:15s} tail>$35 = {m['tail_share_above_35']:.4f} "
                f"({m['n_resources']} resources, {m['n_intervals']:,} intervals)"
            )


if __name__ == "__main__":
    main()
