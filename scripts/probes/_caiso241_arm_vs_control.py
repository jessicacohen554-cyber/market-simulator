"""caiso-241 — the B1-minus-A0 comparison, and the HEAD-drift decomposition.

NO LP. Reads three committed bundles' hourly sidecars and metrics:

  * KEEPER — ``caiso240_b1_stgas_peak_measured`` (git_sha 6671c650)
  * A0     — ``caiso241_a0_control``            (the keeper recipe at HEAD)
  * B1     — ``caiso241_b1_ctpeaker_committed`` (A0 + one flag)

Under the owner's 2026-09-03 amendment of the caiso-231 "no control arms"
directive (``PRECOMMIT-caiso241-ADDENDUM2-owner-ruling-2026-09-03.md`` §B2/§B4)
the MECHANISM's effect is ``B1 - A0`` and the keeper-relative difference is
reported alongside as the drift decomposition:

    B1 - KEEPER  =  (B1 - A0)  +  (A0 - KEEPER)
                    mechanism      HEAD drift

G-CTRL (form 3) is scored here: PASS iff every scored criterion's verdict in A0
matches the committed keeper's. No numeric tolerance is declared — the keeper's
git_sha is days and ~40-commits-a-day behind HEAD, and a tolerance chosen now
would be a fitted number (§B4).

Also scored: G-INERT (B1 != A0 somewhere), P-8 (no year is inert), the §H'
envelope's two-sided falsifiers on the annual mean price move, and the C1-side
CT_PEAKER volume response against the §A6 ceiling.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso241_arm_vs_control.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results/calibration"
KEEPER = CAL / "caiso240_b1_stgas_peak_measured"
A0 = CAL / "caiso241_a0_control"
B1 = CAL / "caiso241_b1_ctpeaker_committed"
YEARS = (2023, 2024, 2025)
OUT = CAL / "_caiso241_arm_vs_control.json"

#: The pre-registered two-sided envelope (ADDENDUM §A5), on B1 - A0.
ENVELOPE = {2023: (-0.879762, 0.05), 2024: (-0.380368, 0.05), 2025: (-0.197915, 0.05)}
#: The pre-registered volume ceilings (TWh) and the measured CT_PEAKER miss.
VOL_CEILING = {2023: 0.432, 2024: 0.247, 2025: 0.120}
VOL_MISS = {2023: -2.71, 2024: -3.84, 2025: -2.11}


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return {}
    df = pd.read_parquet(p)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return {k: v / 1e6 for k, v in df.groupby("klass")["mw"].sum().items()}


def _verdicts(bundle: Path) -> dict[str, str]:
    p = bundle / "metrics.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text())
    return {k: v.get("status", "?") for k, v in (m.get("criteria") or {}).items()}


def _determination(bundle: Path) -> dict:
    p = bundle / "metrics.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text())
    return {
        "determination": m.get("determination"),
        "grade_summary": m.get("grade_summary"),
        "caveats": (m.get("caveats") or {}).get("ledgered"),
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-241",
            "purpose": "B1 - A0 mechanism effect + (A0 - KEEPER) HEAD-drift "
            "decomposition, under the owner's 2026-09-03 amendment of the "
            "caiso-231 no-control-arms directive (ADDENDUM2 §B2/§B4)",
            "keeper": str(KEEPER.relative_to(REPO)),
            "control": str(A0.relative_to(REPO)),
            "arm": str(B1.relative_to(REPO)),
            "solves": 0,
        }
    }

    # ---- G-CTRL (form 3): A0's scored verdicts vs the committed keeper's.
    vk, va, vb = _verdicts(KEEPER), _verdicts(A0), _verdicts(B1)
    diff_ctrl = {k: (vk.get(k), va.get(k)) for k in set(vk) | set(va) if vk.get(k) != va.get(k)}
    out["G_CTRL_form3"] = {
        "keeper_verdicts": vk,
        "control_verdicts": va,
        "differing": diff_ctrl,
        "PASS": not diff_ctrl and bool(vk) and bool(va),
        "falsifier": "any scored criterion's verdict differs between A0 and the "
        "committed keeper ⇒ HEAD drift is material and the keeper-relative "
        "comparison is unsafe; reported as a blocking finding, never absorbed",
    }
    out["determinations"] = {
        "keeper": _determination(KEEPER),
        "control": _determination(A0),
        "arm": _determination(B1),
    }
    out["arm_verdicts"] = vb
    out["arm_vs_control_verdict_diff"] = {
        k: (va.get(k), vb.get(k)) for k in set(va) | set(vb) if va.get(k) != vb.get(k)
    }

    per_year: dict = {}
    for year in YEARS:
        sk, sa, sb = (_system(b, year) for b in (KEEPER, A0, B1))
        row: dict = {}
        if sa is not None and sb is not None:
            pa = sa.groupby("hour")["price"].mean()
            pb = sb.groupby("hour")["price"].mean()
            n = min(len(pa), len(pb))
            d_mech = float(pb.iloc[:n].mean() - pa.iloc[:n].mean())
            row["mean_price_control"] = round(float(pa.mean()), 4)
            row["mean_price_arm"] = round(float(pb.mean()), 4)
            row["dP_mechanism_B1_minus_A0"] = round(d_mech, 6)
            lo, hi = ENVELOPE[year]
            row["envelope"] = [lo, hi]
            row["envelope_PASS"] = bool(lo <= d_mech <= hi)
        if sk is not None and sa is not None:
            pk = sk.groupby("hour")["price"].mean()
            pa = sa.groupby("hour")["price"].mean()
            row["mean_price_keeper"] = round(float(pk.mean()), 4)
            row["dP_headdrift_A0_minus_keeper"] = round(
                float(pa.mean() - pk.mean()), 6
            )
        ca, cb = _class_twh(A0, year), _class_twh(B1, year)
        ck = _class_twh(KEEPER, year)
        classes = sorted(set(ca) | set(cb))
        row["class_twh_mechanism"] = {
            k: round(cb.get(k, 0.0) - ca.get(k, 0.0), 6)
            for k in classes
            if abs(cb.get(k, 0.0) - ca.get(k, 0.0)) > 1e-6
        }
        row["class_twh_headdrift"] = {
            k: round(ca.get(k, 0.0) - ck.get(k, 0.0), 6)
            for k in sorted(set(ca) | set(ck))
            if abs(ca.get(k, 0.0) - ck.get(k, 0.0)) > 1e-6
        }
        row["ct_peaker_twh"] = {
            "keeper": round(ck.get("CT_PEAKER", 0.0), 4),
            "control": round(ca.get("CT_PEAKER", 0.0), 4),
            "arm": round(cb.get("CT_PEAKER", 0.0), 4),
            "mechanism_gain": round(
                cb.get("CT_PEAKER", 0.0) - ca.get("CT_PEAKER", 0.0), 4
            ),
            "pre_registered_ceiling": VOL_CEILING[year],
            "measured_miss": VOL_MISS[year],
        }
        g = row["ct_peaker_twh"]["mechanism_gain"]
        row["ct_peaker_twh"]["gap_closed_pct"] = round(
            100.0 * g / abs(VOL_MISS[year]), 2
        )
        row["ct_peaker_twh"]["inside_ceiling"] = bool(g <= VOL_CEILING[year] + 1e-9)
        # P-8 / G-INERT: is this year inert (arm reproduces control to 0.001 TWh)?
        maxd = max(
            (abs(cb.get(k, 0.0) - ca.get(k, 0.0)) for k in classes), default=0.0
        )
        row["max_abs_class_delta_twh"] = round(maxd, 6)
        row["year_is_inert"] = bool(maxd <= 0.001)
        per_year[str(year)] = row
        print(
            f"[{year}] dP mech {row.get('dP_mechanism_B1_minus_A0')}  "
            f"envelope {row.get('envelope')} PASS={row.get('envelope_PASS')}  |  "
            f"drift {row.get('dP_headdrift_A0_minus_keeper')}  |  "
            f"CT_PEAKER {row['ct_peaker_twh']['control']} -> "
            f"{row['ct_peaker_twh']['arm']} TWh "
            f"(+{row['ct_peaker_twh']['mechanism_gain']}, ceiling "
            f"{VOL_CEILING[year]}, closes "
            f"{row['ct_peaker_twh']['gap_closed_pct']} % of the miss)  "
            f"inert={row['year_is_inert']}"
        )
    out["per_year"] = per_year
    out["G_INERT"] = {
        "PASS": any(not v["year_is_inert"] for v in per_year.values()),
        "falsifier": "all three years reproduce the control exactly",
    }
    out["P8_no_inert_year"] = {
        "HOLDS": all(not v["year_is_inert"] for v in per_year.values()),
        "falsifier": "any year reproduces the control to within 0.001 TWh in "
        "every class",
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"\nG-CTRL form 3 PASS: {out['G_CTRL_form3']['PASS']}")
    if out["G_CTRL_form3"]["differing"]:
        print(f"  DIFFERING: {out['G_CTRL_form3']['differing']}")
    print(f"G-INERT PASS: {out['G_INERT']['PASS']}")
    print(f"P-8 (no inert year) HOLDS: {out['P8_no_inert_year']['HOLDS']}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
