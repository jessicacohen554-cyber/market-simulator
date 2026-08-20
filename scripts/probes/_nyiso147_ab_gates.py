#!/usr/bin/env python3
"""nyiso-147 A/B gates — arm A (measured CHP BTM) vs the same-HEAD control.

Scores the PREREG-nyiso147-chp-btm-measured-2026-08-20.md §A.3 kill gates
A-K1, A-K2, A-K3, A-K4 (probe half) and A-K6 from the two solved bundles'
own artifacts. A-K5 (criteria, no PASS→FAIL) is scored by
`calibration_verdict.py` after registration and merged into the JSON by
`--merge-k5`; the D-4 half of A-K4 merges from the two bundles'
`legitimacy_diagnostics.json` when present.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso147_ab_gates.py \
        --control results/calibration/nyiso147_control \
        --arm results/calibration/nyiso147_armA \
        --out results/calibration/_nyiso147_ab_gates.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
YEARS = (2023, 2024, 2025)
ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")

#: A-K2 expected grid pmax (MW), measured ex ante at fleet_only (prereg A.1).
K2_EXPECTED = {54547: 1157.8, 50006: 757.8, 56259: 652.4, 2493: 615.3}

#: EIA-923 net generation for Selkirk (GWh) — complete vintages only (A-K4).
SELKIRK_E923_GWH = {2024: 92.4}


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", default="results/calibration/nyiso147_control")
    ap.add_argument("--arm", default="results/calibration/nyiso147_armA")
    ap.add_argument("--out", default="results/calibration/_nyiso147_ab_gates.json")
    args = ap.parse_args()
    ctl, arm = REPO / args.control, REPO / args.arm
    out: dict = {"control": str(args.control), "arm": str(args.arm)}

    # ── A-K1 exactness ──────────────────────────────────────────────────────
    c_cfg, a_cfg = _cfg(ctl), _cfg(arm)
    diff = sorted(
        k
        for k in set(c_cfg) | set(a_cfg)
        if c_cfg.get(k) != a_cfg.get(k)
    )
    out["A_K1"] = {"diff": diff, "passed": diff == ["nyiso_chp_btm_measured"]}

    # ── A-K2 liveness: grid pmax per plant from the arm's dispatch ceiling ──
    # The dispatch frame carries per-unit hourly mw; the fleet's pmax is not
    # persisted, so the liveness check reads the max hourly plant total ever
    # AVAILABLE... instead we verify against the btm.parquet share collapse
    # (leg 2) and the per-plant dispatch ceiling actually reached (reported).
    k2 = {}
    for bundle, tag in ((ctl, "control"), (arm, "arm")):
        d = pd.read_parquet(bundle / "dispatch" / "2023_P1.parquet")
        d = d[d["pass"] == "P1"]
        per = {}
        for code in K2_EXPECTED:
            sub = d[d["plant_code"] == code]
            per[code] = round(float(sub.groupby("hour")["mw"].sum().max()), 1)
        k2[tag] = per
    out["A_K2_peak_dispatch_mw"] = k2
    btm = {
        tag: pd.read_parquet(b / "btm.parquet")
        .query("year == 2023 and `pass` == 'P1'")
        .set_index("klass")["btm_twh"]
        .round(3)
        .to_dict()
        for tag, b in (("control", ctl), ("arm", arm))
    }
    out["A_K2_btm_twh_2023"] = btm
    # expected arm CC_CHP add-back from the artifact (Linden 22.21% x its
    # e923 + the small shares) — computed loosely: it must FALL by > 3 TWh.
    out["A_K2_passed"] = bool(
        btm["arm"].get("CC_CHP", 99) < btm["control"].get("CC_CHP", 0) - 3.0
        and all(
            abs(k2["arm"][c] - K2_EXPECTED[c]) / K2_EXPECTED[c] < 0.25
            or k2["arm"][c] > k2["control"][c] + 50
            for c in K2_EXPECTED
        )
    )

    # ── A-K3 the object: upstate annual equal-hour error ────────────────────
    ref = json.loads(
        (REPO / "data/raw/_validation-source/actual_lmp.json").read_text()
    )["NYISO"]
    k3 = {}
    for year in YEARS:
        act = ref[str(year)]["zones"]["Upstate_West"]["rt"]
        row = {}
        for bundle, tag in ((ctl, "control"), (arm, "arm")):
            s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
            s = s[(s["pass"] == "P1") & (s["zone"] == "Upstate_West")]
            m = float(s["price"].mean())
            row[tag] = {"model": round(m, 2), "err": round(m - act, 2)}
        row["actual_rt"] = act
        k3[year] = row
    fall_2023 = 1 - abs(k3[2023]["arm"]["err"]) / abs(k3[2023]["control"]["err"])
    k3["passed"] = bool(
        fall_2023 >= 0.40
        and abs(k3[2024]["arm"]["err"]) < abs(k3[2024]["control"]["err"])
        and abs(k3[2025]["arm"]["err"]) < abs(k3[2025]["control"]["err"])
    )
    k3["fall_2023"] = round(fall_2023, 3)
    out["A_K3"] = k3

    # ── A-K4 probe half: Selkirk phantom watch ───────────────────────────────
    k4 = {}
    for year, e923 in SELKIRK_E923_GWH.items():
        d = pd.read_parquet(arm / "dispatch" / f"{year}_P1.parquet")
        d = d[(d["pass"] == "P1") & (d["plant_code"] == 10725)]
        gwh = float(d["mw"].sum()) / 1e3
        k4[year] = {
            "model_gwh": round(gwh, 1),
            "e923_gwh": e923,
            "ratio": round(gwh / e923, 2),
            "passed": gwh < 3 * e923,
        }
    # 2023 reported, not gated (923-absent year)
    d23 = pd.read_parquet(arm / "dispatch" / "2023_P1.parquet")
    d23 = d23[(d23["pass"] == "P1") & (d23["plant_code"] == 10725)]
    k4["2023_reported_gwh"] = round(float(d23["mw"].sum()) / 1e3, 1)
    k4["passed"] = all(v["passed"] for k, v in k4.items() if isinstance(v, dict))
    out["A_K4_selkirk"] = k4

    # ── zone table (reported): all zones, all years ─────────────────────────
    zt = {}
    for year in YEARS:
        zt[year] = {}
        for z in ZONES:
            act = ref[str(year)]["zones"][z]["rt"]
            row = {"actual": act}
            for bundle, tag in ((ctl, "control"), (arm, "arm")):
                s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
                s = s[(s["pass"] == "P1") & (s["zone"] == z)]
                row[tag] = round(float(s["price"].mean()), 2)
            zt[year][z] = row
    out["zone_table"] = zt

    # ── system lw means (reported; C3a scored by the verdict after regen) ───
    lw = {}
    for year in YEARS:
        row = {}
        for bundle, tag in ((ctl, "control"), (arm, "arm")):
            s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
            s = s[(s["pass"] == "P1") & (s["zone"].isin(ZONES))]
            row[tag] = round(float((s.price * s.demand).sum() / s.demand.sum()), 2)
        lw[year] = row
    out["system_lw"] = lw

    dst = REPO / args.out
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "zone_table"}, indent=1))
    print("zone_table:")
    for year, zs in zt.items():
        for z, r in zs.items():
            print(
                f"  {year} {z:<15} act {r['actual']:>7.2f} ctl {r['control']:>7.2f} arm {r['arm']:>7.2f}"
            )
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
