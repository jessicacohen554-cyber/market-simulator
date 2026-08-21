#!/usr/bin/env python3
"""nyiso-148 A/B gates — ARM D (`chp_layup_duty_split`) vs its same-HEAD base.

Scores the `PREREG-nyiso148-chp-layup-duty-2026-08-21.md` §5 kill gates
D-K1, D-K2, D-K3, D-K4 and D-K6 from the two solved bundles' own artifacts.
D-K5 (criteria, no PASS→FAIL vs the keeper) is scored by
`calibration_verdict.py` after registration and merged in with `--merge-k5`.

BASE = the nyiso147_armA recipe re-solved at this HEAD
(`nyiso_chp_btm_measured` ON, `chp_layup_duty_split` OFF); ARM = BASE plus
the single delta. The keeper `2026-08-19-nyiso-146c-state-scoped` is the
reporting control, read through its byte-identical replay `nyiso147_control`.

The BASE bundle is NOT committed: it reproduces the already-registered
`2026-08-20-nyiso-147a-chp-btm` bit-exactly (max |dprice| = 0.0 over every
zone and hour of all three years), so it is deliberately not double-registered
and takes no dashboard retention slot. To re-run this probe, re-create it
first::

    python scripts/run_calibration_full.py \
        --replay-bundle results/calibration/nyiso147_armA_recipe \
        --out-dir results/calibration/nyiso148_base

`--base-diag` already defaults to the committed twin, so the D-K4 leg needs no
re-solve.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso148_ab_gates.py
    PYTHONPATH=.:src python scripts/probes/_nyiso148_ab_gates.py --merge-k5 '<json>'
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

#: The measured lay-up cohort the census selects (chp_layup_census_NYISO.csv).
COHORT: tuple[int, ...] = (10617, 10725, 50449, 50450, 50451, 54041, 54076)

#: D-K3's metered reference: each census plant's own CAMPD plant-summed GROSS
#: energy per year (GWh), from `_nyiso148_chp_conduct_phase0.json`. Gross, not
#: net, is the conservative choice here — it is the LARGER number, so the
#: model/metered ratios the gate scores are the SMALLER ones, and a passing
#: gate cannot be an artifact of the basis.
PHASE0 = REPO / "results" / "calibration" / "_nyiso148_chp_conduct_phase0.json"

#: D-K3 legs.
K3_COHORT_PHANTOM_FALL: float = 0.60
K3_SELKIRK_MAX_RATIO: float = 2.0
K3_MIN_RETAINED_RATIO: float = 0.25

#: D-K6 legs.
K6_MIN_2025_FALL: float = 0.40
K6_C3A_BAND: float = 10.0


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _dispatch(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    return d[d["pass"] == "P1"]


def _metered_gwh() -> dict[int, dict[int, float]]:
    """Return ``{plant_code: {year: CAMPD plant gross GWh}}`` for the cohort."""
    raw = json.loads(PHASE0.read_text())
    out: dict[int, dict[int, float]] = {}
    for p in raw["plants"]:
        code = int(p["plant_code"])
        if code not in COHORT:
            continue
        out[code] = {
            int(y): float(v["campd_gross_gwh"]) for y, v in p["by_year"].items()
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="results/calibration/nyiso148_base")
    ap.add_argument("--arm", default="results/calibration/nyiso148_armD")
    ap.add_argument("--keeper", default="results/calibration/nyiso147_control")
    # D-K4's BASE side reads the committed diagnostics of nyiso147_armA, which
    # is the SAME RUN as nyiso148_base: the re-solve reproduces it bit-exactly
    # (max |dP| = 0.0 over all zones/hours in all three years), so the base is
    # deliberately not double-registered and its committed twin supplies the
    # diagnostics rather than a redundant regeneration.
    ap.add_argument("--base-diag", default="results/calibration/nyiso147_armA")
    ap.add_argument("--out", default="results/calibration/_nyiso148_ab_gates.json")
    ap.add_argument("--merge-k5", default=None, help="JSON blob for the D-K5 leg")
    args = ap.parse_args()
    base, arm, keep = (REPO / args.base, REPO / args.arm, REPO / args.keeper)

    outp = REPO / args.out
    if args.merge_k5:
        out = json.loads(outp.read_text())
        out["D_K5"] = json.loads(args.merge_k5)
        out["verdict"] = _verdict(out)
        outp.write_text(json.dumps(out, indent=1))
        print(json.dumps(out["D_K5"], indent=1))
        print("verdict:", out["verdict"])
        return

    out: dict = {"base": args.base, "arm": args.arm, "keeper": args.keeper}

    # ── D-K1 exactness ──────────────────────────────────────────────────────
    b_cfg, a_cfg = _cfg(base), _cfg(arm)
    diff = sorted(k for k in set(b_cfg) | set(a_cfg) if b_cfg.get(k) != a_cfg.get(k))
    out["D_K1"] = {
        "diff": diff,
        "passed": diff == ["chp_layup_duty_split"],
    }

    # ── D-K2 liveness: the cohort's tranches collapse onto the peak band ────
    # The dispatch frame carries no offer column, but the tranche NAME encodes
    # the band the offer curve built (``..._committed`` / ``_econc00..`` /
    # ``_peak``), so band composition is a DIRECT liveness test: armed, a
    # census plant's CHP rows must be the peak band alone (pct_mc = 0,
    # pct_peak = room), and every non-census CHP plant's tranche set must be
    # untouched. This is the anti-inert gate nyiso-146b's first solve needed.
    def _band(uid: str) -> str:
        tail = str(uid).rsplit("_", 1)[-1]
        if tail.startswith("econc") or tail == "econ":
            return "econ"
        return tail

    k2: dict = {"per_plant": {}}
    b23, a23 = _dispatch(base, 2023), _dispatch(arm, 2023)
    for code in COHORT:
        row = {}
        for frame, tag in ((b23, "base"), (a23, "arm")):
            sub = frame[frame["plant_code"] == code]
            row[f"{tag}_bands"] = sorted({_band(u) for u in set(sub["unit_id"])})
            row[f"{tag}_gwh"] = round(float(sub["mw"].sum()) / 1000.0, 1)
        row["collapsed_to_peak"] = bool(
            row["arm_bands"] and set(row["arm_bands"]) <= {"peak", "mustrun"}
            and "econ" in row["base_bands"]
        )
        k2["per_plant"][code] = row

    # Every non-census CHP plant's tranche set must be bit-unchanged.
    chp_codes = {
        int(c)
        for c, k in zip(b23["plant_code"], b23["klass"])
        if "CHP" in str(k)
    }
    moved = []
    for code in sorted(chp_codes - set(COHORT)):
        bu = set(b23[b23["plant_code"] == code]["unit_id"])
        au = set(a23[a23["plant_code"] == code]["unit_id"])
        if bu != au:
            moved.append(code)
    k2["non_cohort_chp_moved"] = moved
    k2["non_cohort_chp_unchanged"] = not moved
    k2["cohort_size"] = len(COHORT)
    k2["passed"] = bool(
        all(v["collapsed_to_peak"] for v in k2["per_plant"].values())
        and not moved
    )
    out["D_K2"] = k2

    # ── D-K3 the object: cohort phantom energy ──────────────────────────────
    metered = _metered_gwh()
    k3: dict = {"per_plant": {}, "cohort": {}}
    phantom = {"base": 0.0, "arm": 0.0}
    for year in YEARS:
        b, a = _dispatch(base, year), _dispatch(arm, year)
        for code in COHORT:
            m = metered.get(code, {}).get(year)
            bg = float(b[b["plant_code"] == code]["mw"].sum()) / 1000.0
            ag = float(a[a["plant_code"] == code]["mw"].sum()) / 1000.0
            if m is None:
                continue
            phantom["base"] += max(0.0, bg - m)
            phantom["arm"] += max(0.0, ag - m)
            k3["per_plant"].setdefault(str(code), {})[str(year)] = {
                "metered_gwh": round(m, 1),
                "base_gwh": round(bg, 1),
                "arm_gwh": round(ag, 1),
                "base_ratio": round(bg / m, 2) if m else None,
                "arm_ratio": round(ag / m, 2) if m else None,
            }
    fall = 1 - phantom["arm"] / phantom["base"] if phantom["base"] else 0.0
    k3["cohort"] = {
        "phantom_gwh_base": round(phantom["base"], 1),
        "phantom_gwh_arm": round(phantom["arm"], 1),
        "phantom_fall": round(fall, 3),
    }
    selkirk = k3["per_plant"].get("10725", {})
    k3["selkirk_arm_ratios"] = {y: r.get("arm_ratio") for y, r in selkirk.items()}
    over = [
        (c, y)
        for c, ys in k3["per_plant"].items()
        for y, r in ys.items()
        if r.get("arm_ratio") is not None and r["arm_ratio"] > K3_SELKIRK_MAX_RATIO
        and c == "10725"
    ]
    under = [
        (c, y)
        for c, ys in k3["per_plant"].items()
        for y, r in ys.items()
        if r.get("arm_ratio") is not None and r["arm_ratio"] < K3_MIN_RETAINED_RATIO
    ]
    k3["selkirk_over_bar"] = over
    k3["overkill_below_bar"] = under
    k3["passed"] = bool(
        fall >= K3_COHORT_PHANTOM_FALL and not over and not under
    )
    out["D_K3"] = k3

    # ── D-K4 no new conduct failures ────────────────────────────────────────
    def _diag(bundle: Path) -> dict:
        p = bundle / "legitimacy_diagnostics.json"
        return json.loads(p.read_text()) if p.exists() else {}

    k4: dict = {}
    bd, ad = _diag(REPO / args.base_diag), _diag(arm)
    k4["base_diag_bundle"] = args.base_diag

    def _ident(text: str) -> str:
        """Reduce a D-1/D-2/D-4 failure string to its IDENTITY.

        A row is NEW when its (year, mechanism x class, plant) is new — not
        when the same row's TWh and binding-hour counts moved. Both arms
        dispatch differently by construction, so a full-text diff would call
        every surviving row new (and, worse, would call an IMPROVING row a
        regression). The magnitudes are reported separately, so nothing is
        hidden by the reduction.
        """
        head = str(text).split(" is floored for ")[0]
        return " ".join(head.split())

    if bd and ad:
        for key in ("D1", "D2", "D4"):
            bf = (bd["diagnostics"].get(key, {}).get("failures") or [])
            af = (ad["diagnostics"].get(key, {}).get("failures") or [])
            bi = {_ident(f) for f in bf}
            k4[key] = {
                "base_failures": len(bf),
                "arm_failures": len(af),
                "new": [f for f in af if _ident(f) not in bi],
                "cleared": [f for f in bf if _ident(f) not in {_ident(x) for x in af}],
                "carried_over_texts": [f for f in af if _ident(f) in bi],
            }
        k4["passed"] = bool(
            not k4["D4"]["new"] and not k4["D1"]["new"] and not k4["D2"]["new"]
        )
    else:
        k4["passed"] = None
        k4["note"] = "legitimacy_diagnostics.json not yet generated for one side"
    out["D_K4"] = k4

    # ── zone table + D-K6 the 2025 recovery ─────────────────────────────────
    ref = json.loads(
        (REPO / "data/raw/_validation-source/actual_lmp.json").read_text()
    )["NYISO"]
    zt: dict = {}
    lw: dict = {}
    for year in YEARS:
        zt[year] = {}
        for bundle, tag in ((keep, "keeper"), (base, "base"), (arm, "arm")):
            s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
            s = s[s["pass"] == "P1"]
            for zone in ZONES:
                zs = s[s["zone"] == zone]
                zt[year].setdefault(zone, {})[tag] = round(float(zs["price"].mean()), 2)
                zt[year][zone]["actual"] = ref[str(year)]["zones"][zone]["rt"]
        act = ref[str(year)]["rt_lw"]
        lw[year] = {"actual": act}
        for bundle, tag in ((keep, "keeper"), (base, "base"), (arm, "arm")):
            s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
            s = s[s["pass"] == "P1"]
            # Load-weighted across zones, the C3a basis (the system frame's
            # per-zone demand column is the weight the scorer uses).
            m = float(np.average(s["price"], weights=s["demand"]))
            lw[year][tag] = round(m, 2)
            lw[year][f"{tag}_err_pct"] = round(100.0 * (m - act) / act, 1)
    out["zone_table"] = zt
    out["system_lw"] = lw

    b25, a25 = abs(lw[2025]["base_err_pct"]), abs(lw[2025]["arm_err_pct"])
    fall25 = 1 - a25 / b25 if b25 else 0.0
    out["D_K6"] = {
        "base_2025_err_pct": lw[2025]["base_err_pct"],
        "arm_2025_err_pct": lw[2025]["arm_err_pct"],
        "fall_2025": round(fall25, 3),
        "arm_2023_err_pct": lw[2023]["arm_err_pct"],
        "passed": bool(
            fall25 >= K6_MIN_2025_FALL and abs(lw[2023]["arm_err_pct"]) <= K6_C3A_BAND
        ),
    }

    out["verdict"] = _verdict(out)
    outp.write_text(json.dumps(out, indent=1))
    print(f"wrote {outp.relative_to(REPO)}")
    for k in ("D_K1", "D_K2", "D_K3", "D_K4", "D_K6"):
        print(f"  {k}: {out[k].get('passed')}")
    print("  verdict:", out["verdict"])


def _verdict(out: dict) -> str:
    """Return the pre-registered disposition given the gates scored so far."""
    fails = [
        k
        for k in ("D_K1", "D_K2", "D_K3", "D_K4", "D_K5", "D_K6")
        if k in out and out[k].get("passed") is False
    ]
    if not fails:
        pending = [
            k
            for k in ("D_K1", "D_K2", "D_K3", "D_K4", "D_K5", "D_K6")
            if k not in out or out[k].get("passed") is None
        ]
        return f"PASSES SO FAR (pending {', '.join(pending)})" if pending else "PASSES"
    return "REJECTED-AS-ARMED (" + ", ".join(fails) + ")"


if __name__ == "__main__":
    main()
