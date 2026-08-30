"""ercot-226 A/B gate scorer — the PRECOMMIT-ercot226 §5.3 table.

A thin wrapper over the shared ``ercot221_gates`` constructions (imported):

* adds ``--years`` (default: 2023 only — the W-2 single-year probe shape);
* G-SPUR is gated on the LIDLESS count inherited from ``ercot221_gates``
  (``S_nolid = #{model >= 150 & actual < 150}``, +5/yr bar vs the re-minted
  9/12/1 baseline) since the ercot-225 card's Option A was owner-signed
  2026-08-26; the ``S_band``/``S_top`` split stays as the kept report
  decomposition (its ``SPUR_BASELINE`` hour-list hygiene defect was repaired
  in the same signature commit);
* adds the precommit §5.3 withheld-family diagnostics from
  ``hourly/reserve_family_<y>.parquet``: VOLL-shortfall engagement hours on
  any ``*_withheld`` or ``*_held`` family (the manufactured-shortage
  signature — must be 0), family-dual >= VOLL−ε hours, and requirement
  totals (control vs arm) so the F2 conserving credit is visible;
* reports G-ADA (adaptive expression) for CONTROL and ARM — the
  spike-day/floor response is the precommit §5.2 adaptive-interaction
  measurement;
* reports the D5 row presence of the ercot-226 mechanism
  (``ercot_as_held_location``) alongside the adaptive rows.

C3a/C3b probe-basis numbers remain side-effect reporting (Q-B FINAL / R-A);
the ADOPTION criteria run on the OFFICIAL basis via
``ercot226_official_score.py``.

Usage:
    python scripts/probes/ercot226_gates.py --control <bundle> --arm <bundle> \\
        [--years 2023] [--out results/calibration/ercot226_gates_<factor>.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ercot221_gates import (  # noqa: E402  (frozen constructions, imported)
    MID_BAND,
    SHED_BASELINE,
    SPUR_BAR,
    SPUR_BASELINE,
    VOLL,
    _actual,
    _d4_rows,
    _d5_adaptive_rows,
    _gada,
    _gbat,
    _member,
    _spur_hours,
)

VOLL_EPS = 1.0  # $/MWh — "dual at VOLL" tolerance for the engagement count


def _spur_lidless(m: np.ndarray, a: np.ndarray) -> dict:
    """The ercot-225 card's Option-A vocabulary (Option A owner-signed
    2026-08-26: ``s_nolid`` is now the gated count; ``s_band``/``s_top``
    the kept report decomposition)."""
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    lo = aa < MID_BAND[0]
    return {
        "s_nolid": int(((mm >= MID_BAND[0]) & lo).sum()),
        "s_band": int(((mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & lo).sum()),
        "s_top": int(((mm > MID_BAND[1]) & lo).sum()),
    }


def _reserve_family_diag(bundle: Path, year: int) -> dict:
    """Withheld/held family engagement diagnostics (precommit §5.3)."""
    p = bundle / "hourly" / f"reserve_family_{year}.parquet"
    if not p.exists():
        return {"present": False}
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    fam_col = next(
        (c for c in ("family", "name", "family_name") if c in df.columns), None
    )
    if fam_col is None:
        return {"present": True, "note": f"no family column in {sorted(df.columns)}"}
    out: dict = {"present": True, "families": {}}
    rigid = df[df[fam_col].astype(str).str.contains("_withheld|_held", regex=True)]
    for fam, g in rigid.groupby(fam_col, observed=True):
        rec: dict = {}
        if "shortfall_mw" in g.columns and "hour" in g.columns:
            eng = g.loc[g["shortfall_mw"].to_numpy(float) > 1e-6, "hour"]
            rec["shortfall_hour_set"] = sorted(int(h) for h in eng.unique())
            rec["shortfall_hours"] = len(rec["shortfall_hour_set"])
            rec["shortfall_max_mw"] = round(float(g["shortfall_mw"].max()), 3)
        if "dual" in g.columns:
            rec["dual_ge_voll_hours"] = int(
                (g["dual"].to_numpy(float) >= VOLL - VOLL_EPS).sum()
            )
            rec["dual_max"] = round(float(g["dual"].max()), 2)
        if "requirement_mw" in g.columns:
            rec["requirement_mean_mw"] = round(float(g["requirement_mw"].mean()), 1)
            rec["requirement_max_mw"] = round(float(g["requirement_mw"].max()), 1)
        if "held_mw" in g.columns:
            rec["held_mean_mw"] = round(float(g["held_mw"].mean()), 1)
        out["families"][str(fam)] = rec
    out["total_rigid_shortfall_hours"] = int(
        sum(r.get("shortfall_hours", 0) for r in out["families"].values())
    )
    return out


#: Non-leap hour windows (0-based hour-of-year): the 2023 scarcity-episode
#: window Jun-10 00:00 (ECRS go-live, day 160) .. Sep-30 24:00 (day 273), and
#: the ercot-217 calm fortnight Jun-24 (day 174) .. Jul-7 24:00 (day 188).
_EPISODE = (160 * 24, 273 * 24)
_CALM = (174 * 24, 188 * 24)


def _summer_block(ctl: dict, arm: dict, a: np.ndarray) -> dict:
    """Precommit §5.2: miss-set response, window concentration, calm
    fortnight, channel attribution (λ vs adder) — all ctl-vs-arm."""
    aa = np.nan_to_num(a, nan=-np.inf)
    tail = aa > 200.0
    pc = np.nan_to_num(ctl["price"])
    pa = np.nan_to_num(arm["price"])
    miss_ctl = tail & (pc <= 200.0)
    d_price = pa - pc
    d_lam = np.nan_to_num(arm["lam"]) - np.nan_to_num(ctl["lam"])
    dem = np.nan_to_num(ctl["demand"])
    win = np.zeros(pc.size, dtype=bool)
    win[_EPISODE[0] : _EPISODE[1]] = True
    tot = float((d_price * dem).sum())
    win_share = float((d_price[win] * dem[win]).sum()) / tot if abs(tot) > 1e-6 else None

    def _bias(p: np.ndarray, lo: int, hi: int) -> float:
        w = dem[lo:hi]
        act = a[lo:hi]
        ok = np.isfinite(act) & (w > 0)
        m = float((p[lo:hi][ok] * w[ok]).sum() / w[ok].sum())
        x = float((act[ok] * w[ok]).sum() / w[ok].sum())
        return (m - x) / x * 100.0

    improved = miss_ctl & (d_price > 1.0)
    if improved.any():
        di = float((d_price[improved] * dem[improved]).sum())
        lam_share = float((d_lam[improved] * dem[improved]).sum()) / di if di else None
    else:
        lam_share = None
    return {
        "miss_split_ctl": {
            "caught": int((tail & (pc > 200.0)).sum()),
            "missed": int(miss_ctl.sum()),
            "phantom": int(((~tail) & (pc > 200.0) & np.isfinite(a)).sum()),
        },
        "miss_split_arm": {
            "caught": int((tail & (pa > 200.0)).sum()),
            "missed": int((tail & (pa <= 200.0)).sum()),
            "phantom": int(((~tail) & (pa > 200.0) & np.isfinite(a)).sum()),
        },
        "d_price_at_miss_p50": round(float(np.median(d_price[miss_ctl])), 3)
        if miss_ctl.any()
        else None,
        "d_price_at_miss_max": round(float(d_price[miss_ctl].max()), 2)
        if miss_ctl.any()
        else None,
        "window_concentration": round(win_share, 4) if win_share is not None else None,
        "calm_fortnight_bias_pct": {
            "control": round(_bias(pc, *_CALM), 2),
            "arm": round(_bias(pa, *_CALM), 2),
        },
        "channel_lambda_share_at_improved_miss": (
            round(lam_share, 4) if lam_share is not None else None
        ),
        "improved_miss_hours": int(improved.sum()),
    }


def _d5_held_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D5", {}).get("rows", [])
    return sorted(
        r["mechanism"] for r in rows if r["mechanism"].startswith("ercot_as_held")
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/ercot226_gates.json")
    )
    args = ap.parse_args()
    ctl_b, arm_b = Path(args.control), Path(args.arm)

    out: dict = {
        "probe": "ercot226_gates",
        "charter": "PRECOMMIT-ercot226-held-sequestration-2026-08-22 §5.3",
        "control": str(ctl_b),
        "arm": str(arm_b),
        "years": list(args.years),
        "per_year": {},
    }
    gcap_viol = 0
    spur_fail = shed_fail = gbat_fail = shortfall_fail = False
    for y in args.years:
        a = _actual(y)
        tail = np.where(np.nan_to_num(a) > 200.0)[0]
        yr: dict = {}
        for name, b in (("control", ctl_b), ("arm", arm_b)):
            m = _member(b, y)
            viol = int(
                (
                    np.nan_to_num(m["adder"]) > np.maximum(VOLL - m["lam"], 0.0) + 1e-6
                ).sum()
            )
            spur = _spur_hours(m["price"], a)
            shed = [int(h) for h in np.where(m["slack"] > 1e-6)[0]]
            ok = np.isfinite(m["price"]) & np.isfinite(a)
            mm, aa = m["price"][ok], a[ok]
            yr[name] = {
                "gcap_violations": viol,
                "spur_hours": spur,
                "spur_count": len(spur),
                "spur_lidless": _spur_lidless(m["price"], a),
                "shed_hours": shed,
                "c3a_probe_pct": round(
                    float((mm.mean() - aa.mean()) / aa.mean() * 100.0), 2
                ),
                "c3b_probe_nrmse": round(
                    float(np.sqrt(np.mean((mm - aa) ** 2)) / aa.mean()), 4
                ),
                "tail_model_gt200": int((mm > 200.0).sum()),
                "model_mean": round(float(mm.mean()), 3),
                "reserve_family": _reserve_family_diag(b, y),
                "gada": _gada(b, y),
            }
            if name == "arm":
                gcap_viol += viol
                if len(spur) > len(SPUR_BASELINE[y]) + SPUR_BAR:
                    spur_fail = True
                if sorted(shed) != sorted(SHED_BASELINE[y]) and not set(shed) <= set(
                    SHED_BASELINE[y]
                ):
                    shed_fail = True
                yr["gbat_arm"] = _gbat(arm_b, y, tail)
                if yr["gbat_arm"].get("pass") is False:
                    gbat_fail = True
                # AMENDMENT 1 (precommit; keeper self-test 2026-08-22): the
                # keeper's OWN rigid families engage their VOLL steps in 21
                # 2023 hours (ECRS 11 / RRS 9 / RegUp 11 shortfall hours) —
                # the model's designed scarcity expression at caught hours.
                # The no-manufactured-shortage rule is therefore the G-SHED
                # subset discipline: per family, the arm's shortfall HOUR SET
                # must be a subset of the control's — never absolute zero.
                ctl_fams = yr["control"]["reserve_family"].get("families", {})
                for fam, rec in yr[name]["reserve_family"].get("families", {}).items():
                    arm_set = set(rec.get("shortfall_hour_set", []))
                    ctl_set = set(
                        ctl_fams.get(fam, {}).get("shortfall_hour_set", [])
                    )
                    if not arm_set <= ctl_set:
                        shortfall_fail = True
                        rec["new_shortfall_hours"] = sorted(arm_set - ctl_set)
        yr["summer"] = _summer_block(_member(ctl_b, y), _member(arm_b, y), a)
        yr["spur_baseline"] = SPUR_BASELINE[y]
        yr["shed_baseline"] = SHED_BASELINE[y]
        out["per_year"][str(y)] = yr

    out["d4_rows_control"] = _d4_rows(ctl_b)
    out["d4_rows_arm"] = _d4_rows(arm_b)
    out["d4_no_new_rows"] = set(out["d4_rows_arm"]) <= set(out["d4_rows_control"]) or (
        out["d4_rows_arm"] == out["d4_rows_control"]
    )
    out["d5_adaptive_rows_arm"] = _d5_adaptive_rows(arm_b)
    out["d5_held_rows_arm"] = _d5_held_rows(arm_b)
    out["gates"] = {
        "G-CAP": {"violations": gcap_viol, "pass": gcap_viol == 0},
        "G-SPUR": {
            "pass": not spur_fail,
            "bar": f"+{SPUR_BAR}/yr vs 9/12/1 (LIDLESS, ercot-225 Option A "
            "owner-signed 2026-08-26; band/top decomposition reported)",
        },
        "G-SHED": {"pass": not shed_fail},
        "G-BAT": {"pass": not gbat_fail},
        "G-D2": {"no_new_d4_rows": bool(out["d4_no_new_rows"])},
        "G-SHORTFALL": {
            "pass": not shortfall_fail,
            "rule": "per rigid family, arm shortfall hour-set ⊆ control's "
            "(precommit AMENDMENT 1 — no MANUFACTURED shortage; the keeper "
            "baseline itself carries 21 designed VOLL-engagement hours)",
        },
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    print(json.dumps(out["gates"], indent=1))


if __name__ == "__main__":
    main()
