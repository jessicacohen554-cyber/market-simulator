"""ERCOT-171 Phase 0 — a LICENSED sub-population instrument for the 2023 COAL rows.

NO LP, no solve, no mechanism armed, keeper UNCHANGED
(``2026-08-05-run168b-year-curves``). Charter: the OWNER ADJUDICATION taken
in-session 2026-08-05 on the ERCOT-169 §6 open decision — **option 2, "charter a
licensed sub-population instrument for the 2023 COAL rows."** Decision rule
pre-registered and pushed before this file ran:
``docs/PRECOMMIT-ercot171-coal-licensed-subpopulation-2026-08-05.md``.

**The question.** ERCOT-169 could not license either COAL limb on delivery-2023:
``curve_share`` 0.9702 against the 0.9876 floor, the shortfall located in Martin
Lake units 1–3 (own ``curve_share`` 0.757/0.761/0.797, concentrated Mar–Jun). The
verdict was withheld in BOTH directions. This probe asks whether a *coverage*
restriction — stated as a rule, applied identically to every year — produces an
instrument that (a) clears the SAME floor on 2023 and (b) still reproduces the
committed constants on the 2024/25 subsets where they ARE licensed.

**(b) is the load-bearing gate.** A coverage restriction is admissible only if it
fixes coverage and not level. The four identification subsets are the frames
these constants were identified on, so "does the restriction move the
identification where the instrument already works?" is the direct test.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot171_coal_licensed_subpop_phase0.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

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

DEFAULT_OUT = REPO / "results/calibration/ercot171_coal_licensed_subpop.json"
YEAR = 2023

#: The ERCOT-138 §3.4 licensing floor. THE SAME floor ercot-169 failed on —
#: pre-registered, not lowered, and not lowered against the constants either.
LICENCE_FLOOR = 0.9876

#: Armed constants under test (``constants.py``), with their own cited bands.
ARMED = {"coal_mustrun": 15.8807, "coal_peak": 35.1989}

#: ERCOT-169 §2 committed subset-class reads the footing gate must reproduce.
FOOTING_BOT_P50 = {
    ("2024_ercot74_tail_days"): 16.86,
    ("2024_ercot75_control_days"): 16.37,
    ("2025_ercot75_control_days"): 15.00,
    ("2025_ercot86_tail_days"): 15.00,
}
FOOTING_P90 = {
    ("2024_ercot74_tail_days"): 34.82,
    ("2024_ercot75_control_days"): 34.82,
    ("2025_ercot75_control_days"): 43.00,
    ("2025_ercot86_tail_days"): 48.01,
}
FOOTING_TOL = 0.02


def _resource_curve_share(df: pd.DataFrame) -> pd.Series:
    """Per-resource ``curve_share`` on a loaded frame, ERCOT-123's own quantity.

    Uses ``ercot123._decompose`` verbatim (through the shared harness's import
    path) and reproduces ``section_a``'s ``has_curve`` mean, grouped by resource
    instead of pooled — the rule S1 is stated on.
    """
    import ercot123_coal_sced_reach as e123

    g = e123._decompose(df)
    return g.groupby("Resource Name")["has_curve"].mean()


def _apply_s1(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], float]:
    """S1 — drop resources whose OWN ``curve_share`` is below the floor.

    The rule, not a named exclusion list: whichever resources fail, fail. Applied
    identically to every year (precommit §1a).

    Returns the restricted frame, the dropped resource names, and the HSL-cap
    share the drop removes (reported, non-gating).
    """
    share = _resource_curve_share(df)
    drop = sorted(share[share < LICENCE_FLOOR].index.astype(str))
    keep = df[~df["Resource Name"].astype(str).isin(drop)]
    cap_all = float(df["HSL"].sum())
    cap_drop = float(df[df["Resource Name"].astype(str).isin(drop)]["HSL"].sum())
    return keep, drop, (cap_drop / cap_all if cap_all > 0 else 0.0)


def _subset_frames() -> dict[str, pd.DataFrame]:
    """The four committed identification subsets, COAL rows, via ercot123."""
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


def _subset_reads(frames: dict[str, pd.DataFrame], restrict: bool) -> list[dict]:
    """Per-subset instrument reads, optionally under S1."""
    from scripts.lib import sced_corpus_instruments as sci

    rows = []
    for tag, d in frames.items():
        dropped: list[str] = []
        cap_share = 0.0
        if restrict:
            d, dropped, cap_share = _apply_s1(d)
        year = int(tag.split("_", 1)[0])
        cb = sci.curve_bottom(d)
        ib = sci.inc_bid_quantiles(d)
        cov = sci.coverage(d)
        rows.append(
            {
                "subset": tag,
                "year": year,
                "family": "tail" if "tail" in tag else "control",
                "res_hours_curve": cb["res_hours"],
                "bot_p50": round(float(cb["bot_p50"]), 4),
                "res_hours_inc": ib["res_hours"],
                "p90": round(float(ib["inc_bid_q"]["p90"]), 4),
                "curve_share": round(float(cov["curve_share"]), 5),
                "n_dropped": len(dropped),
                "dropped": dropped,
                "cap_share_dropped": round(cap_share, 5),
            }
        )
    return rows


def _pool_limb_a(rows: list[dict]) -> float:
    """Limb A level — res-hours-weighted pooled ``bot_p50`` (derive's own form)."""
    w = sum(r["res_hours_curve"] for r in rows)
    return sum(r["res_hours_curve"] * r["bot_p50"] for r in rows) / w


def _pool_limb_c(rows: list[dict], gas_by_year: dict[int, float], anchor: float) -> dict:
    """Limb C level — the derive's own two-year slope then res-hours pooling."""
    years = sorted({r["year"] for r in rows})
    if len(years) != 2:
        raise SystemExit(f"limb C needs exactly two fuel-distinct years; got {years}")
    y_lo, y_hi = years

    def _p90_year(y: int) -> float:
        sel = [r for r in rows if r["year"] == y]
        w = sum(r["res_hours_inc"] for r in sel)
        return sum(r["res_hours_inc"] * r["p90"] for r in sel) / w

    p_lo, p_hi = _p90_year(y_lo), _p90_year(y_hi)
    gas_hr = (p_hi - p_lo) / (gas_by_year[y_hi] - gas_by_year[y_lo])
    lv = [
        {**r, "level": r["p90"] - gas_hr * (gas_by_year[r["year"]] - anchor)}
        for r in rows
    ]
    w = sum(r["res_hours_inc"] for r in lv)
    return {
        "gas_hr": round(float(gas_hr), 4),
        "p90_by_year": {str(y_lo): round(p_lo, 4), str(y_hi): round(p_hi, 4)},
        "level": sum(r["res_hours_inc"] * r["level"] for r in lv) / w,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

    from scripts.lib import sced_corpus_instruments as sci

    t0 = time.time()
    anchor_gas = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"])

    # ---- footing: the UNRESTRICTED pipeline must reproduce the committed reads
    frames = _subset_frames()
    base_rows = _subset_reads(frames, restrict=False)
    footing = []
    for r in base_rows:
        for stat, table in (("bot_p50", FOOTING_BOT_P50), ("p90", FOOTING_P90)):
            footing.append(
                {
                    "subset": r["subset"],
                    "stat": stat,
                    "reconstructed": r[stat],
                    "committed": table[r["subset"]],
                    "delta": round(r[stat] - table[r["subset"]], 4),
                    "tol": FOOTING_TOL,
                    "pass": bool(abs(r[stat] - table[r["subset"]]) <= FOOTING_TOL),
                }
            )
    footing_pass = all(f["pass"] for f in footing)

    # ---- the fuel basis (ercot-169's, footing-gated) ------------------------
    fuel = sci.fuel_basis_by_year()
    gas_by_year = {int(y): float(v["CC"]) for y, v in fuel["years"].items()}
    base_a = _pool_limb_a(base_rows)
    base_c = _pool_limb_c(base_rows, gas_by_year, anchor_gas)

    # ---- G-NEUT: the SAME rule on the 2024/25 identification subsets --------
    neut_rows = _subset_reads(frames, restrict=True)
    neut_a = _pool_limb_a(neut_rows)
    neut_c = _pool_limb_c(neut_rows, gas_by_year, anchor_gas)
    gneut = {
        "coal_mustrun": {
            "pooled_restricted": round(neut_a, 4),
            "pooled_unrestricted": round(base_a, 4),
            "armed": ARMED["coal_mustrun"],
            "delta_vs_armed": round(neut_a - ARMED["coal_mustrun"], 4),
            "band": sci.LIMBS["coal_mustrun"]["band_usd"],
            "pass": bool(
                abs(neut_a - ARMED["coal_mustrun"])
                <= sci.LIMBS["coal_mustrun"]["band_usd"]
            ),
        },
        "coal_peak": {
            "pooled_restricted": round(neut_c["level"], 4),
            "pooled_unrestricted": round(base_c["level"], 4),
            "armed": ARMED["coal_peak"],
            "delta_vs_armed": round(neut_c["level"] - ARMED["coal_peak"], 4),
            "band": sci.LIMBS["coal_peak"]["band_usd"],
            "pass": bool(
                abs(neut_c["level"] - ARMED["coal_peak"])
                <= sci.LIMBS["coal_peak"]["band_usd"]
            ),
        },
        "gas_hr_restricted": neut_c["gas_hr"],
        "gas_hr_unrestricted": base_c["gas_hr"],
        "gas_hr_armed": sci.LIMBS["coal_peak"]["hr"],
        "subset_rows_restricted": neut_rows,
        "subset_rows_unrestricted": [
            {k: v for k, v in r.items() if k != "dropped"} for r in base_rows
        ],
    }

    # ---- G-LIC: the restricted delivery-2023 population --------------------
    corpus = sci.load_corpus_year(YEAR, ("COAL",))
    t1 = sci.restrict_hours(corpus[corpus["cls"] == "COAL"], sci.MATCHED_HOURS)
    share_2023 = _resource_curve_share(t1)
    t1_s1, dropped_2023, cap_drop_2023 = _apply_s1(t1)
    cov_s1 = sci.coverage(t1_s1)
    glic = {
        "curve_share_unrestricted": round(float(sci.coverage(t1)["curve_share"]), 5),
        "curve_share_restricted": round(float(cov_s1["curve_share"]), 5),
        "floor": LICENCE_FLOOR,
        "pass": bool(cov_s1["curve_share"] >= LICENCE_FLOOR),
        "n_dropped": len(dropped_2023),
        "dropped": dropped_2023,
        "cap_share_dropped": round(cap_drop_2023, 5),
        "per_resource_curve_share": {
            str(k): round(float(v), 4) for k, v in share_2023.sort_values().items()
        },
    }

    # ---- the 2023 verdicts (only meaningful if both gates pass) ------------
    def _block(d: pd.DataFrame, window: str) -> dict:
        return {
            "year": YEAR,
            "class": "COAL",
            "hours": window,
            "coverage": sci.coverage(d),
            "curve_bottom": sci.curve_bottom(d),
            "inc_bid": sci.inc_bid_quantiles(d),
        }

    blk_t1 = _block(t1_s1, "h11-22 CST (S1-restricted)")
    full = sci.restrict_hours(corpus[corpus["cls"] == "COAL"], None)
    full_s1, _d2, _c2 = _apply_s1(full)
    blk_t2 = _block(full_s1, "full-day (S1-restricted)")

    limbs = {}
    for key in ("coal_mustrun", "coal_peak"):
        fuel_year = (
            sci.COAL_FUEL_BY_YEAR[YEAR]
            if sci.LIMBS[key]["fuel"] == "coal"
            else gas_by_year[YEAR]
        )
        t1_assess = sci.assess_limb(key, blk_t1, fuel_year, ARMED[key])
        t2_assess = sci.assess_limb(key, blk_t2, fuel_year, ARMED[key])
        gates_ok = footing_pass and fuel["footing_pass"] and glic["pass"] and gneut[key]["pass"]
        if not gates_ok:
            verdict = "NOT-IDENTIFIABLE-2023 CONFIRMED"
        elif t1_assess["value_read"] == "INSIDE":
            verdict = "CONFIRMED"
        else:
            verdict = "REFUTED"
        limbs[key] = {
            "limb": sci.LIMBS[key]["limb"],
            "constant": sci.LIMBS[key]["constant"],
            "G_LIC_pass": glic["pass"],
            "G_NEUT_pass": gneut[key]["pass"],
            "T1_gating": t1_assess,
            "T2_reported": t2_assess,
            "verdict": verdict,
        }

    # ---- S2 month-scoped sensitivity (REPORTED, pre-declared NON-GATING) ----
    monthly = []
    for m, g in t1.groupby("month", observed=True):
        monthly.append(
            {"month": int(m), "curve_share": round(float(sci.coverage(g)["curve_share"]), 4)}
        )
    keep_months = [r["month"] for r in monthly if r["curve_share"] >= LICENCE_FLOOR]
    t1_s2 = t1[t1["month"].isin(keep_months)]
    blk_s2 = _block(t1_s2, f"h11-22 CST (S2 months {keep_months})")
    s2 = {
        "note": "REPORTED SENSITIVITY, pre-declared NON-GATING (precommit §1a)",
        "monthly_curve_share": monthly,
        "months_kept": keep_months,
        "curve_share": round(float(blk_s2["coverage"]["curve_share"]), 5),
        "limbs": {
            key: sci.assess_limb(
                key,
                blk_s2,
                sci.COAL_FUEL_BY_YEAR[YEAR]
                if sci.LIMBS[key]["fuel"] == "coal"
                else gas_by_year[YEAR],
                ARMED[key],
            )
            for key in ("coal_mustrun", "coal_peak")
        },
    }

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot171_coal_licensed_subpop_phase0.py",
            "session": "ercot-171 Phase 0 (no LP, no solve, keeper unchanged)",
            "keeper": "2026-08-05-run168b-year-curves",
            "precommit": "docs/PRECOMMIT-ercot171-coal-licensed-subpopulation-2026-08-05.md",
            "charter": (
                "OWNER ADJUDICATION in-session 2026-08-05 on the ercot-169 §6 open "
                "decision: option 2, a licensed sub-population instrument"
            ),
            "year": YEAR,
            "licence_floor": LICENCE_FLOOR,
            "elapsed_s": None,
        },
        "footing": {"subset_reads": footing, "pass": footing_pass},
        "fuel_basis": {
            "footing": fuel["footing"],
            "footing_pass": fuel["footing_pass"],
            "gas_by_year": gas_by_year,
            "coal_by_year": sci.COAL_FUEL_BY_YEAR,
        },
        "G_LIC": glic,
        "G_NEUT": gneut,
        "limbs": limbs,
        "S2_sensitivity": s2,
    }
    out["_provenance"]["elapsed_s"] = round(time.time() - t0, 1)
    args.out.write_text(json.dumps(out, indent=1, default=float))

    print("footing pass:", footing_pass, "| fuel footing:", fuel["footing_pass"])
    print(
        f"G-LIC  curve_share {glic['curve_share_unrestricted']} -> "
        f"{glic['curve_share_restricted']} (floor {LICENCE_FLOOR}) "
        f"PASS={glic['pass']}  dropped={glic['n_dropped']} "
        f"({glic['cap_share_dropped']:.1%} of HSL-cap): {glic['dropped']}"
    )
    for k in ("coal_mustrun", "coal_peak"):
        n = gneut[k]
        print(
            f"G-NEUT {k}: unrestricted {n['pooled_unrestricted']} / restricted "
            f"{n['pooled_restricted']} vs armed {n['armed']} "
            f"(delta {n['delta_vs_armed']}, band {n['band']}) PASS={n['pass']}"
        )
        L = limbs[k]
        print(
            f"  2023 T1: measured {L['T1_gating']['measured_usd_mwh']} -> level "
            f"{L['T1_gating']['level_year_usd_mwh']} vs armed {L['T1_gating']['armed_usd_mwh']} "
            f"(delta {L['T1_gating']['delta_usd_mwh']}, {L['T1_gating']['delta_over_band']}x band)"
            f"  => {L['verdict']}"
        )
    print(f"wrote {args.out} ({out['_provenance']['elapsed_s']} s)")


if __name__ == "__main__":
    main()
