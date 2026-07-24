"""caiso-119 A/B scorer: evaluate the min-load delta against the gates
pre-registered in `results/calibration/caiso119_ab_pregistered_gates.md`.

Arms (same HEAD, same box, three years one bundle):
  A  caiso119_base_A     — replay of the 2026-07-23-caiso-netrev-margin-keeper
                           recipe, no delta
  B  caiso119_minload_B  — the same recipe with ONE delta,
                           caiso_ra_min_load_frac 0.26 -> 0.570 (MEASURED)

Reference actuals are the CEMS basis — the series that survived
`_caiso119_gas_basis_adjudication.py` (EIA-930 CISO `NG: NG` is refuted on
level, diurnal shape, and energy balance and must never be used here).

Reports, per year: belly / evening / annual gas for both arms against CEMS,
the belly/evening duck ratio, and an explicit PASS/FAIL on each pre-registered
PRIMARY (P1, P2) and KILL (K1, K2, K4) gate. Price gates (G2/G3) and the
forced-energy gate (G5) come from the bundles' own metrics.json /
legitimacy_diagnostics.json once written.

Run:  .venv/bin/python scripts/probes/_caiso119_ab_score.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
ARMS = {"BASE": "caiso119_base_A", "MINLOAD": "caiso119_minload_B"}
YEARS = (2023, 2024, 2025)
BELLY = (10, 11, 12, 13, 14, 15)
EVENING = (17, 18, 19, 20, 21)
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP")


def cems_ref(year: int) -> dict[str, float]:
    """Belly / evening / annual CAISO gas, CEMS gross (the surviving basis)."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        plants = {int(k): v for k, v in json.load(fh)["bench"]["plants"].items()}
    df = pd.read_parquet(CAMPD / f"CA_{year}.parquet")
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df = df[df["facilityId"].astype(int).isin(plants)].copy()
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    hourly = df.groupby(["date", "hour"])["grossLoad"].sum()
    hod = hourly.index.get_level_values(1)
    return {
        "belly": float(hourly[hod.isin(BELLY)].mean()),
        "evening": float(hourly[hod.isin(EVENING)].mean()),
        "annual": float(hourly.mean()),
    }


def arm_gas(bundle: str, year: int) -> dict[str, float] | None:
    path = CAL / bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[(df["pass"] == "P1") & (df["klass"].isin(GAS_CLASSES))].copy()
    tot = df.groupby("hour")["mw"].sum()
    hod = tot.index.to_numpy() % 24
    return {
        "belly": float(tot[np.isin(hod, BELLY)].mean()),
        "evening": float(tot[np.isin(hod, EVENING)].mean()),
        "annual": float(tot.mean()),
    }


def criteria(bundle: str) -> dict:
    p = CAL / bundle / "metrics.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text())
    return {k: v.get("status") for k, v in m.get("criteria", {}).items()}


def main() -> None:
    print("=" * 100)
    print("caiso-119 A/B — measured min-load 0.26 -> 0.570, scored on the "
          "PRE-REGISTERED gates")
    print("=" * 100)

    verdicts: list[str] = []
    for year in YEARS:
        ref = cems_ref(year)
        a, b = arm_gas(ARMS["BASE"], year), arm_gas(ARMS["MINLOAD"], year)
        print(f"\n--- {year} ---")
        if a is None or b is None:
            print("  (arm not yet solved)")
            continue
        print(f"  {'window':<10}{'CEMS':>10}{'BASE':>10}{'MINLOAD':>10}"
              f"{'BASE gap':>11}{'MIN gap':>10}{'closed':>9}")
        for w in ("belly", "evening", "annual"):
            ga, gb = ref[w] - a[w], ref[w] - b[w]
            closed = (1 - gb / ga) * 100 if abs(ga) > 1 else float("nan")
            print(f"  {w:<10}{ref[w]:>10,.0f}{a[w]:>10,.0f}{b[w]:>10,.0f}"
                  f"{ga:>+11,.0f}{gb:>+10,.0f}{closed:>8.0f}%")
        duck_r, duck_a, duck_b = (ref["belly"] / ref["evening"],
                                  a["belly"] / a["evening"], b["belly"] / b["evening"])
        print(f"  {'duck b/e':<10}{duck_r:>10.2f}{duck_a:>10.2f}{duck_b:>10.2f}")

        # Pre-registered gates.
        ga = ref["belly"] - a["belly"]
        p1 = (1 - (ref["belly"] - b["belly"]) / ga) >= 0.40 if abs(ga) > 1 else False
        p2 = duck_b > duck_a
        k1 = b["belly"] > ref["belly"] * 1.10
        k2 = b["annual"] > ref["annual"] * 1.07
        k4 = b["evening"] > a["evening"]
        for tag, ok, desc in (
            ("P1", p1, "belly gap closed >=40%"),
            ("P2", p2, "duck ratio rises toward measured"),
            ("K1", not k1, "belly does NOT exceed CEMS gross +10% (overshoot)"),
            ("K2", not k2, "annual gas does NOT exceed CEMS +7%"),
            ("K4", not k4, "evening gas does NOT rise further"),
        ):
            print(f"    {tag} {'PASS' if ok else 'FAIL'}  {desc}")
            verdicts.append(f"{year}:{tag}:{'PASS' if ok else 'FAIL'}")

    print("\n" + "=" * 100)
    print("RUBRIC CRITERIA (from each arm's metrics.json, once scored)")
    print("=" * 100)
    ca, cb = criteria(ARMS["BASE"]), criteria(ARMS["MINLOAD"])
    keys = sorted(set(ca) | set(cb))
    if keys:
        print(f"  {'criterion':<16}{'BASE':>12}{'MINLOAD':>12}   delta")
        for k in keys:
            va, vb = ca.get(k, "-"), cb.get(k, "-")
            flag = "" if va == vb else ("  <-- REGRESSION" if vb == "FAIL" else "  <-- improved")
            print(f"  {k:<16}{va:>12}{vb:>12}{flag}")
    else:
        print("  (arms not yet scored — run the calibration verdict first)")

    fails = [v for v in verdicts if v.endswith("FAIL")]
    print("\n" + "=" * 100)
    print(f"GATE TALLY: {len(verdicts) - len(fails)} pass / {len(fails)} fail")
    if fails:
        print("  failures: " + ", ".join(fails))
    print("Disposition per the pre-registered doc: any KILL -> the delta is "
          "rejected AS SIZED; the measured 0.570 stays correct and the bridge's "
          "BINDING SCOPE becomes the next lane. Never tune 0.570 back down.")


if __name__ == "__main__":
    main()
