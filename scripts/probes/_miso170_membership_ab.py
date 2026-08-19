"""miso-170 — adjudicate PREREG-miso170 K-0..K-6 from committed artifacts only.

Two jobs, both read-only:

* ``--identity CONTROL KEEPER`` — the K-0 prerequisite. Compares every scored
  sidecar of every year between the control bundle and the committed keeper and
  asserts numeric ``max|diff| = 0`` with non-numeric columns equal. The control
  is solved on the patched tree with both membership flags OFF, so a non-zero
  delta means the code change or the new ``exclude_plant_codes`` column is not
  inert at its default — a stop-the-line, not a finding.

* ``--gates CONTROL ARM`` — K-1 (membership exactness), K-2 (liveness vs the
  pre-registered shed), K-3 (D-4 conduct failures), K-4 (C8 per year), K-6
  (D-1 shape). K-5 (no gated PASS -> FAIL flip) is scored from
  ``calibration_verdict.py --json`` on both bundles.

Writes the verdict record to ``results/calibration/_miso170_membership_ab.json``
so the adjudication is reproducible from committed bytes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

# The 15-plant CAMPD lay-up census (PREREG-miso170 §2), read from the committed
# artifact rather than hardcoded so the gate cannot drift from the deriver.
CENSUS_CSV = (
    REPO
    / "data"
    / "raw"
    / "_processed-legacy"
    / "campd_bridge_layup_exclusions_MISO.csv"
)
# The two mechanisms the census is armed against (PREREG-miso170 §3).
MECHS = ("reliability_floor", "st_gas_mustrun_per_plant")
# Pre-registered shed, TWh, from the control's own committed D-4 rows
# (PREREG-miso170 §4). K-2 band is +/- 50 %.
PREREG_SHED = {2023: 0.5044, 2024: 0.7531, 2025: 0.7853}
K2_BAND = 0.50
# The single D-4 conduct failure the prereg expects to SURVIVE (§2a / K-3).
EXPECTED_SURVIVOR = (2023, "st_gas_mustrun_per_plant", "1402")
# D-1 gates C8's grounded-above-budget escalation reads (K-6).
D1_MIN_R, D1_MIN_CV = 0.80, 0.50


def _census() -> frozenset[int]:
    """Return the committed MISO lay-up plant codes."""
    df = pd.read_csv(CENSUS_CSV)
    return frozenset(int(c) for c in df["plant_code"])


def _legit(bundle: Path) -> dict:
    """Return a bundle's committed legitimacy diagnostics."""
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _d4_rows(legit: dict) -> list[dict]:
    return legit.get("diagnostics", {}).get("D4", {}).get("rows", [])


def _d2_summary(legit: dict, klass: str = "ST_GAS") -> dict[int, dict]:
    return {
        int(r["year"]): r
        for r in legit.get("diagnostics", {}).get("D2", {}).get("summary", [])
        if r.get("class") == klass
    }


def _d1_rows(legit: dict, klass: str = "ST_GAS") -> dict[int, dict]:
    return {
        int(r["year"]): r
        for r in legit.get("diagnostics", {}).get("D1", {}).get("rows", [])
        if r.get("class") == klass
    }


def _mech_of(row: dict) -> str:
    """Return the bare mechanism name from a D-4 ``floor`` label."""
    return str(row.get("floor", "")).split(" × ")[0]


def identity(control: Path, keeper: Path) -> dict:
    """K-0 — every scored sidecar of every year must be bit-identical."""
    out: dict = {"gate": "K-0", "files": [], "passed": True}
    for path in sorted((keeper / "hourly").glob("*.parquet")):
        other = control / "hourly" / path.name
        rec = {"file": path.name}
        if not other.exists():
            rec.update(present=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        a, b = pd.read_parquet(path), pd.read_parquet(other)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            rec.update(shape_match=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        worst = 0.0
        nonnum_ok = True
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]):
                d = np.abs(a[col].to_numpy(dtype=float) - b[col].to_numpy(dtype=float))
                worst = max(worst, float(np.nanmax(d)) if len(d) else 0.0)
            else:
                nonnum_ok &= bool(a[col].equals(b[col]))
        ok = worst == 0.0 and nonnum_ok
        rec.update(max_abs_diff=worst, nonnumeric_equal=nonnum_ok, passed=ok)
        out["files"].append(rec)
        out["passed"] &= ok
    return out


def _verdict_json(bundle: Path) -> dict:
    """Return ``calibration_verdict.py --json`` for a bundle."""
    # check=False deliberately: the scorer exits non-zero on a NOT-YET
    # determination, which is the expected state on both sides of this A/B.
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"calibration_verdict.py produced no JSON for {bundle}")
    return json.loads(res.stdout)


def _records(verdict: dict) -> dict[tuple, str]:
    """Flatten a verdict payload to {(criterion, key, year): status}.

    ``criteria`` is {criterion: {..., "records": [...]}}; the per-record grain
    is what K-5 compares, so a class- or year-local flip cannot hide inside a
    criterion that still reads PASS overall.
    """
    out: dict[tuple, str] = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[(rec.get("criterion", name), rec.get("key"), rec.get("year"))] = (
                rec.get("status")
            )
    return out


def gates(control: Path, arm: Path) -> dict:
    """K-1..K-6 from both bundles' committed artifacts."""
    census = _census()
    lc, la = _legit(control), _legit(arm)
    rc, ra = _d4_rows(lc), _d4_rows(la)
    years = sorted({int(r["year"]) for r in rc if r.get("year") is not None})
    res: dict = {"census_size": len(census), "years": years}

    # --- K-1 membership exactness -----------------------------------------
    def keyset(rows):
        return {
            (int(r["year"]), _mech_of(r), str(r.get("plant", "")))
            for r in rows
            if r.get("plant") and _mech_of(r) in MECHS
        }

    kc, ka = keyset(rc), keyset(ra)
    residuals = sorted(k for k in ka if int(k[2] or 0) in census)
    strays = sorted(k for k in (kc - ka) if int(k[2] or 0) not in census)
    res["K1"] = {
        "gate": "membership exactness",
        "census_rows_remaining": residuals,
        "non_census_rows_lost": strays,
        "passed": not residuals and not strays,
    }

    # --- K-2 liveness ------------------------------------------------------
    d2c, d2a = _d2_summary(lc), _d2_summary(la)
    k2 = {"gate": "liveness vs pre-registered shed", "years": {}, "passed": True}
    for y in years:
        pred = PREREG_SHED.get(y)
        got = float(d2c[y]["forced_twh"]) - float(d2a[y]["forced_twh"])
        lo, hi = pred * (1 - K2_BAND), pred * (1 + K2_BAND)
        ok = lo <= got <= hi
        k2["years"][y] = {
            "predicted_twh": pred,
            "measured_twh": round(got, 4),
            "band": [round(lo, 4), round(hi, 4)],
            "passed": ok,
        }
        k2["passed"] &= ok
    res["K2"] = k2

    # --- K-3 conduct failures ---------------------------------------------
    def fails(rows):
        return {
            (int(r["year"]), _mech_of(r), str(r.get("plant", "")))
            for r in rows
            if str(r.get("verdict")) == "FAIL"
            and str(r.get("check", "window")) == "unit-conduct"
        }

    fc, fa = fails(rc), fails(ra)
    new = sorted(fa - fc)
    res["K3"] = {
        "gate": "D-4 per-unit conduct failures",
        "control_count": len(fc),
        "arm_count": len(fa),
        "arm_failures": sorted(fa),
        "new_failures": new,
        "expected_survivor_present": EXPECTED_SURVIVOR in fa,
        "passed": not new,
    }

    # Any off-window (non-conduct) D-4 failure is also a K-3 kill if new.
    def offwindow(rows):
        return {
            (int(r["year"]), _mech_of(r), str(r.get("plant", "")))
            for r in rows
            if str(r.get("verdict")) == "FAIL"
            and str(r.get("check", "window")) != "unit-conduct"
        }

    new_ow = sorted(offwindow(ra) - offwindow(rc))
    res["K3"]["new_offwindow_failures"] = new_ow
    res["K3"]["passed"] &= not new_ow

    # --- K-4 C8 (objective, not a kill) ------------------------------------
    vc, va = _verdict_json(control), _verdict_json(arm)
    rec_c, rec_a = _records(vc), _records(va)
    k4 = {"gate": "C8 ST_GAS per year", "years": {}}
    for y in years:
        k4["years"][y] = {
            "control": rec_c.get(("forced_share", "ST_GAS", y)),
            "arm": rec_a.get(("forced_share", "ST_GAS", y)),
            "control_share": float(d2c[y]["forced_share"]),
            "arm_share": float(d2a[y]["forced_share"]),
        }
    res["K4"] = k4

    # --- K-5 no gated PASS -> FAIL flip ------------------------------------
    flips = sorted(
        str(k) for k, v in rec_c.items() if v == "PASS" and rec_a.get(k) == "FAIL"
    )
    res["K5"] = {
        "gate": "no record-grain PASS -> FAIL flip",
        "flips": flips,
        "records_compared": len(rec_c),
        "passed": not flips,
    }

    # --- K-6 D-1 shape -----------------------------------------------------
    d1a = _d1_rows(la)
    k6 = {"gate": "ST_GAS D-1 shape", "years": {}, "passed": True}
    for y in years:
        row = d1a.get(y, {})
        r, cv = float(row.get("profile_r", 0.0)), float(row.get("cv_ratio", 0.0))
        ok = r >= D1_MIN_R and cv >= D1_MIN_CV
        k6["years"][y] = {"profile_r": r, "cv_ratio": cv, "passed": ok}
        k6["passed"] &= ok
    res["K6"] = k6

    res["kills_silent"] = all(res[k]["passed"] for k in ("K1", "K2", "K3", "K5", "K6"))
    return res


def main() -> None:
    """CLI entry point: run the identity check, the gates, or both."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--identity", nargs=2, metavar=("CONTROL", "KEEPER"))
    ap.add_argument("--gates", nargs=2, metavar=("CONTROL", "ARM"))
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_miso170_membership_ab.json"),
    )
    args = ap.parse_args()
    record: dict = {}
    if args.identity:
        record["identity"] = identity(Path(args.identity[0]), Path(args.identity[1]))
        print(json.dumps(record["identity"], indent=1))
    if args.gates:
        record["gates"] = gates(Path(args.gates[0]), Path(args.gates[1]))
        print(json.dumps(record["gates"], indent=1, default=str))
    if record:
        out = Path(args.out)
        prior = json.loads(out.read_text()) if out.exists() else {}
        prior.update(record)
        out.write_text(json.dumps(prior, indent=1, default=str) + "\n")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
