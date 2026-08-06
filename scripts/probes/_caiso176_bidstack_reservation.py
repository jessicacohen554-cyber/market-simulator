"""caiso-176 — does CAISO's OWN published storage bid stack identify the
battery discharge throughput cost (``ScenarioConfig.battery_dispatch_adder``)?

WHY THIS PROBE EXISTS
---------------------
``battery_dispatch_adder = 5.0`` is CAISO's last genuinely free
residual-identified DOF entry (calibration attestation ``free_parameters``,
``identification: "residual"``). Its ledgered forward-valid replacement is
"the measured AS power reservation (``storage_as_commitment``) + an
ATB-derived degradation cost". BOTH halves of that named replacement are
already spent on CAISO:

* the AS half — ``caiso_storage_as_reservation`` — was probe-adjudicated
  INERT at caiso-74 (run ``2026-07-11-caiso-74-storage-as``) and the whole
  AS-award family was then refuted by arithmetic at caiso-127/129 (overnight
  upward award 334-713 MW against 2.1-3.1 GW of remaining headroom);
* the degradation half was BUILT and A/B-solved at caiso-100/101 —
  ``_degradation_cost_per_mwh("li_ion_4hr")`` = $14.25/MWh on the then-current
  constants — and REJECTED PROBE on caiso-100 FINDING §6's pre-registered
  two-sided +/-15 % battery-only throughput guard (2024 chg 6.77 < 7.40 TWh,
  2025 10.28 < 11.07; discharge under floor in all three years) plus a 0.64 TWh
  move of 2025 evening discharge AWAY from measured.

So the question this probe asks is NOT the caiso-101 question again. It is:
does CAISO publish, in its own market data, a DIFFERENT instrument that
identifies the fleet's discharge reservation price WITHOUT a model in the
loop? The one CAISO-own storage instrument that no session has read is the
``bid_stack`` sheet of the Daily Energy Storage Report — committed at
``data/raw/storage-as-awards/CAISO/storage-report-*.xlsx`` and recorded in
that directory's README as "retained but not curated".

WHAT THE INSTRUMENT IS
----------------------
``bid_stack`` columns: TRADE_DATE | HOUR | INTERVAL | MARKET | RES_TYPE |
STATE (CHARGE/DISCHARGE) | RANGE (a price bucket, $/MWh) | VOLUME (MW).
It is the as-submitted bid volume of the whole storage fleet, bucketed by
offer price -- a direct market measurement, no model in the loop.

THE IDENTIFICATION TEST (stated before the numbers are read)
------------------------------------------------------------
The parameter is a scalar $/MWh marginal cost of discharge. For the bid stack
to IDENTIFY it, the published price buckets must be able to separate the
incumbent 5.0 from the rejected ATB-derived alternative. On today's committed
constants that alternative is ``452.6 $/kWh x 1000 / 5000 cyc x 0.25`` =
**$22.63/MWh** -- the constant moved from 285 $/kWh since caiso-101, so the
derived value is now FURTHER in the direction the caiso-101 volume guard
rejected, not nearer.

The economic content the test rests on is one-sided and is stated as such: a
rational participant does not offer energy BELOW its own marginal cost -- the
same premise CAISO's own DEB market-power-mitigation machinery rests on -- so
the lowest price bucket carrying material discharge volume bounds the fleet's
throughput cost FROM ABOVE. The instrument can therefore REFUTE a candidate
value; it cannot confirm one. That asymmetry is the finding, not a limitation
discovered afterwards.

G1 RESOLUTION -- a bucket edge must fall strictly between 5.0 and 22.63, so
     the two candidate values land in different buckets. If the bucket
     spanning 5.0 also spans 22.63, the instrument cannot distinguish them
     and it does not identify the parameter at the grain required.
G2 MASS + STABILITY -- the implied upper bound (the upper edge of the lowest
     priced bucket carrying >= 1 % of the year's PRICED discharge volume) must
     be stable across 2023/2024/2025 to be a parameter rather than a yearly
     outcome. Reported at a 5 % threshold too, so the answer is not an
     artifact of one threshold choice.
G3 CONTAMINATION -- a storage energy bid is an OPPORTUNITY-COST object (the
     value of holding stored energy for a later hour), not a marginal-cost
     object; the LP already generates that opportunity cost endogenously
     through SOC + RTE. Two contamination channels are reported: the share of
     discharge volume carried as ``SELF-SCHED`` (a price-taking submission
     that expresses no cost at all, and is excluded from the priced stack
     before any bound is read) and the share offered at or below $0.

Every gate is a property of the published data, not of any model output, and
none of them reads a price residual (rule 13 ``[R-MEASURED]``).

Usage::

    uv run python scripts/probes/_caiso176_bidstack_reservation.py

Writes ``results/calibration/_caiso176_bidstack_reservation.json``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "storage-as-awards" / "CAISO"
OUT = REPO / "results" / "calibration" / "_caiso176_bidstack_reservation.json"

#: The incumbent free parameter and the ATB-derived alternative caiso-101
#: rejected, recomputed on TODAY's committed constants (see module docstring).
INCUMBENT_ADDER = 5.0
ATB_DERIVED_ADDER = 452.6 * 1000.0 / 5000.0 * 0.25  # = 22.63


def _bucket_bounds(label: str) -> tuple[float, float]:
    """Parse a CAISO ``RANGE`` bucket label into (low, high) $/MWh.

    Labels look like ``(-100,-50]``, ``(0,15]``, ``[-150,-100]`` and — the pair
    that must not be missed — CAISO's scientific-notation edges ``(500,1e+03]``
    and ``(1e+03,2e+03]``. Open/closed ends do not matter for the resolution
    question, only the numeric edges.
    """
    nums = re.findall(r"-?inf|-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", label.lower())
    if len(nums) != 2:
        return (float("nan"), float("nan"))

    def _f(tok: str) -> float:
        if tok.endswith("inf"):
            return float("-inf") if tok.startswith("-") else float("inf")
        return float(tok)

    return (_f(nums[0]), _f(nums[1]))


def _bucket_of(value: float, buckets: list[tuple[str, float, float]]) -> str | None:
    """Return the label of the bucket containing ``value`` (None if unbucketed)."""
    for label, low, high in buckets:
        if low < value <= high:
            return label
    return None


def load_bid_stack() -> pd.DataFrame:
    """Read every committed quarterly ``bid_stack`` sheet into one frame."""
    frames = []
    for path in sorted(RAW.glob("storage-report-*.xlsx")):
        df = pd.read_excel(path, sheet_name="bid_stack")
        df["src"] = path.name
        frames.append(df)
        print(f"  read {path.name}: {len(df):,} rows", flush=True)
    if not frames:
        raise FileNotFoundError(f"no storage-report-*.xlsx under {RAW}")
    out = pd.concat(frames, ignore_index=True)
    out["year"] = pd.to_datetime(out["TRADE_DATE"]).dt.year
    return out


def main() -> None:
    print("reading committed Daily Energy Storage Report bid_stack sheets ...")
    raw = load_bid_stack()

    vocab = sorted(raw["RANGE"].astype(str).unique())
    buckets = [(lab, *_bucket_bounds(lab)) for lab in vocab]
    # NO SILENT DROPS: the only label allowed to fail numeric parsing is the
    # non-price "SELF-SCHED" category. An unparsed PRICE bucket would silently
    # vanish from the census (this bit an earlier revision, which lost the two
    # scientific-notation buckets), so it is a hard error, not a filter.
    unparsed = [lab for lab, low, _hi in buckets if low != low and lab != "SELF-SCHED"]
    if unparsed:
        raise ValueError(
            f"unparsed price bucket label(s), census would be incomplete: {unparsed}"
        )
    buckets = [b for b in buckets if b[1] == b[1]]
    buckets.sort(key=lambda b: b[1])

    result: dict = {
        "probe": "caiso-176 storage bid-stack reservation-price identification",
        "source": "data/raw/storage-as-awards/CAISO/storage-report-*.xlsx (bid_stack sheet)",
        "rows_read": int(len(raw)),
        "years": sorted(int(y) for y in raw["year"].unique()),
        "markets": sorted(raw["MARKET"].astype(str).unique()),
        "res_types": sorted(raw["RES_TYPE"].astype(str).unique()),
        "states": sorted(raw["STATE"].astype(str).unique()),
        "range_vocab": vocab,
        "bucket_edges": [
            {"label": lab, "low": low, "high": high} for lab, low, high in buckets
        ],
        "incumbent_adder": INCUMBENT_ADDER,
        "atb_derived_adder": round(ATB_DERIVED_ADDER, 4),
    }

    # ---- G1: resolution ---------------------------------------------------
    b_inc = _bucket_of(INCUMBENT_ADDER, buckets)
    b_atb = _bucket_of(ATB_DERIVED_ADDER, buckets)
    result["G1_resolution"] = {
        "bucket_containing_incumbent": b_inc,
        "bucket_containing_atb_derived": b_atb,
        "separable": bool(b_inc is not None and b_atb is not None and b_inc != b_atb),
        "note": (
            "PASS requires the two candidate values to fall in DIFFERENT published "
            "buckets; identical buckets mean the instrument cannot distinguish them."
        ),
    }

    # ---- G2 / G3: discharge stack composition -----------------------------
    # CAISO writes the discharge state as "DISCHAR" and carries price-taking
    # submissions in a non-numeric "SELF-SCHED" bucket, which is NOT a price
    # and is excluded from the priced stack before any bound is read.
    per_market: dict = {}
    for market in sorted(raw["MARKET"].astype(str).unique()):
        for res in sorted(raw["RES_TYPE"].astype(str).unique()):
            sel = raw[
                (raw["MARKET"].astype(str) == market)
                & (raw["RES_TYPE"].astype(str) == res)
                & (raw["STATE"].astype(str).str.upper().str.startswith("DISCHAR"))
            ]
            if sel.empty:
                continue
            by_year: dict = {}
            for year, grp in sel.groupby("year"):
                all_tot = float(grp["VOLUME"].sum())
                if all_tot <= 0:
                    continue
                vol = grp.groupby(grp["RANGE"].astype(str))["VOLUME"].sum()
                self_sched = float(vol.get("SELF-SCHED", 0.0))
                priced_tot = all_tot - self_sched
                if priced_tot <= 0:
                    continue
                shares = {
                    lab: float(vol.get(lab, 0.0)) / priced_tot for lab, _, _ in buckets
                }
                ordered = [
                    {"bucket": lab, "share_of_priced": round(shares[lab], 6)}
                    for lab, _lo, _hi in buckets
                    if shares[lab] > 0
                ]
                neg = sum(shares[lab] for lab, _lo, hi in buckets if hi <= 0.0)

                def _bound(threshold: float, _sh: dict = shares) -> dict:
                    """Upper edge of the lowest bucket carrying >= threshold."""
                    for lab, _lo, hi in buckets:
                        if _sh[lab] >= threshold:
                            return {"bucket": lab, "implied_max_marginal_cost": hi}
                    return {"bucket": None, "implied_max_marginal_cost": None}

                by_year[str(int(year))] = {
                    "total_bid_mw": round(all_tot, 3),
                    "priced_bid_mw": round(priced_tot, 3),
                    "share_by_bucket_of_priced": ordered,
                    "G3_share_self_scheduled_of_all": round(self_sched / all_tot, 6),
                    "G3_share_priced_at_or_below_zero": round(neg, 6),
                    "G2_bound_at_1pct": _bound(0.01),
                    "G2_bound_at_5pct": _bound(0.05),
                }
            per_market[f"{market}|{res}"] = by_year
    result["discharge_stack"] = per_market

    dam_lesr = per_market.get("IFM|LESR", {})
    bounds_1 = {
        y: v["G2_bound_at_1pct"]["implied_max_marginal_cost"]
        for y, v in dam_lesr.items()
    }
    bounds_5 = {
        y: v["G2_bound_at_5pct"]["implied_max_marginal_cost"]
        for y, v in dam_lesr.items()
    }
    result["G2_stability"] = {
        "implied_max_marginal_cost_by_year_1pct": bounds_1,
        "implied_max_marginal_cost_by_year_5pct": bounds_5,
        "stable_across_years_1pct": bool(len(set(bounds_1.values())) == 1)
        if bounds_1
        else False,
        "stable_across_years_5pct": bool(len(set(bounds_5.values())) == 1)
        if bounds_5
        else False,
    }
    result["G3_contamination"] = {
        "share_self_scheduled_by_year": {
            y: v["G3_share_self_scheduled_of_all"] for y, v in dam_lesr.items()
        },
        "share_priced_at_or_below_zero_by_year": {
            y: v["G3_share_priced_at_or_below_zero"] for y, v in dam_lesr.items()
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("\nRANGE vocab:", vocab)
    print("G1 separable:", result["G1_resolution"]["separable"])
    print("   incumbent 5.00 ->", b_inc, "| ATB-derived 22.63 ->", b_atb)
    print("G2 implied max marginal cost (IFM|LESR, >=1% of priced):", bounds_1)
    print("G2 implied max marginal cost (IFM|LESR, >=5% of priced):", bounds_5)
    print("G3 contamination:", json.dumps(result["G3_contamination"], indent=2))


if __name__ == "__main__":
    main()
