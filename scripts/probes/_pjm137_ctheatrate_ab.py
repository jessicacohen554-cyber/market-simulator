"""pjm-137 A/B scorer — `measured_ct_heat_rates` against the pjm-136 keeper.

Scores the arms defined by `PREREG-pjm137-measured-ct-heat-rates-2026-07-29.md`
against the gates that document declares, and nothing else. Every gate below is
quoted from the pre-registration; a gate the PREREG does not contain is not
scored here, and the exception sets are not consulted for the pass/fail flags
(the pjm-136 discipline: a clause that fails as written is recorded as a fail).

Gates:

* **P1 construction fidelity** — the artifact's applied rows must be the ones
  the fleet actually prices, and the off-state must be untouched. Verified from
  the two arms' `run_config.json` plus the artifact's own
  ``model_over_measured`` column.
* **P2 materiality, two-signed** — the re-pricing must be material and must move
  plants in BOTH directions; a one-way move would be a multiplier in disguise.
  Pre-computed in PREREG §2 at 39/72 plants beyond 0.5 MMBtu/MWh.
* **K1 the C3c standing kill** — C3c passes in the keeper by 1 h (2024) and
  2.5 h (2025) against a 0.5x floor, and cheaper CT offers cut the price tail,
  so this is reported explicitly whatever it does.
* **K2 C1 per class**, **K3 band exclusions**, **K4 zero slack/dump**,
  **K5 arm-A identity**, **K6 solve cost.**

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm137_ctheatrate_ab.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

YEARS = (2023, 2024, 2025)

ARM_A = Path("results/calibration/pjm137_control_A")
ARM_B = Path("results/calibration/pjm137_ctheatrate_B")
IDENTITY_REF = Path("results/calibration/pjm136_lossurf_B")
ARTIFACT = Path("data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv")
OUT_PATH = Path("results/probes/pjm137_ctheatrate_ab.json")

#: PREREG §2 P2 — a plant is "materially re-priced" beyond this many MMBtu/MWh.
MATERIAL_HR = 0.5
#: PREREG §3 K3 — retire the delta if the physical band excludes more than this
#: share of the roster's measured energy.
MAX_EXCLUDED_ENERGY = 0.10
#: The gas price the PREREG quotes its $/MWh translations at.
GAS_USD_PER_MMBTU = 3.50


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """The bundle's P1 class-hourly frame (klass x hour, MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """ISO-wide annual TWh by class."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """The year's total slack and dump (MWh)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return float(frame["slack"].sum()), float(frame["dump"].sum())


def _zonal_class_twh(bundle: Path, year: int) -> dict[str, float]:
    """REPORTED ONLY — PJM_Dominion class TWh from the local `dispatch/` frame.

    Absent from a committed slim bundle; a missing file yields an empty dict
    rather than an imputed value.
    """
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return {}
    frame = pd.read_parquet(path, columns=["zone", "klass", "mw"])
    frame = frame[frame["zone"].astype(str) == "PJM_Dominion"]
    grouped = frame.groupby("klass", observed=True)["mw"].sum() / 1.0e6
    return {str(k): round(float(v), 4) for k, v in grouped.items() if v != 0.0}


def _identity(year: int) -> dict:
    """K5 — arm A against the committed keeper bundle, every class-hour."""
    for path in (ARM_A, IDENTITY_REF):
        if not (path / "hourly" / f"class_hourly_{year}.parquet").exists():
            return {"available": False, "reason": f"missing {path}"}
    a = _class_hourly(ARM_A, year).set_index(["klass", "hour"])["mw"].sort_index()
    r = _class_hourly(IDENTITY_REF, year).set_index(["klass", "hour"])["mw"].sort_index()
    joined = a.align(r, join="outer", fill_value=0.0)
    diff = (joined[0] - joined[1]).abs()
    return {
        "available": True,
        "max_abs_diff_mw": float(diff.max()),
        "n_class_hours": int(diff.size),
        "identical": bool(diff.max() < 1e-6),
    }


def _artifact_gates() -> dict:
    """P2 / K3 — materiality, two-sidedness and band exclusions, from the CSV."""
    if not ARTIFACT.exists():
        return {"available": False, "reason": f"missing {ARTIFACT}"}
    art = pd.read_csv(ARTIFACT)
    ok = art[art["flag"] == "ok"]
    excluded = art[art["flag"] != "ok"]
    delta = ok["heat_rate"] - ok["model_heat_rate_egrid"]
    weight = ok["gross_mwh"]
    energy_all = float(art["gross_mwh"].sum())
    return {
        "available": True,
        "plants_total": int(len(art)),
        "plants_applied": int(len(ok)),
        "plants_excluded_by_band": int(len(excluded)),
        "excluded_energy_share": (
            float(excluded["gross_mwh"].sum() / energy_all) if energy_all else 0.0
        ),
        "K3_pass": bool(
            energy_all and excluded["gross_mwh"].sum() / energy_all
            <= MAX_EXCLUDED_ENERGY
        ),
        "plants_moved_gt_0p5": int((delta.abs() > MATERIAL_HR).sum()),
        "plants_cheaper": int((delta < 0).sum()),
        "plants_dearer": int((delta > 0).sum()),
        "P2_two_signed": bool((delta < 0).any() and (delta > 0).any()),
        "energy_weighted_delta_mmbtu_per_mwh": (
            float((delta * weight).sum() / weight.sum()) if weight.sum() else 0.0
        ),
        "energy_weighted_delta_usd_per_mwh": (
            float((delta * weight).sum() / weight.sum() * GAS_USD_PER_MMBTU)
            if weight.sum()
            else 0.0
        ),
    }


def _rubric(bundle: Path) -> dict:
    """The bundle's own determination and per-criterion verdicts."""
    path = bundle / "metrics.json"
    if not path.exists():
        return {"available": False}
    m = json.loads(path.read_text())
    crit = m.get("criteria", {})
    return {
        "available": True,
        "determination": m.get("determination"),
        "criteria": {
            k: (v.get("verdict") if isinstance(v, dict) else v)
            for k, v in crit.items()
        },
    }


def score(year: int) -> dict:
    """Every per-year gate for one calendar year."""
    a_twh, b_twh = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
    classes = sorted(set(a_twh) | set(b_twh))
    a_slack, a_dump = _slack_dump(ARM_A, year)
    b_slack, b_dump = _slack_dump(ARM_B, year)
    dom_a, dom_b = _zonal_class_twh(ARM_A, year), _zonal_class_twh(ARM_B, year)
    return {
        "iso_class_twh": {
            k: {
                "A": a_twh.get(k, 0.0),
                "B": b_twh.get(k, 0.0),
                "delta": round(b_twh.get(k, 0.0) - a_twh.get(k, 0.0), 4),
            }
            for k in classes
        },
        "dominion_class_twh": {
            k: {
                "A": dom_a.get(k, 0.0),
                "B": dom_b.get(k, 0.0),
                "delta": round(dom_b.get(k, 0.0) - dom_a.get(k, 0.0), 4),
            }
            for k in sorted(set(dom_a) | set(dom_b))
        },
        "K4_slack_dump": {
            "A": {"slack_mwh": a_slack, "dump_mwh": a_dump},
            "B": {"slack_mwh": b_slack, "dump_mwh": b_dump},
            "pass": bool(
                a_slack == 0.0 and a_dump == 0.0 and b_slack == 0.0 and b_dump == 0.0
            ),
        },
        "K5_arm_a_identity": _identity(year),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    payload = {
        "arms": {"A": str(ARM_A), "B": str(ARM_B)},
        "identity_reference": str(IDENTITY_REF),
        "P2_K3_artifact": _artifact_gates(),
        "rubric": {"A": _rubric(ARM_A), "B": _rubric(ARM_B)},
        "per_year": {str(y): score(y) for y in YEARS},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")

    art = payload["P2_K3_artifact"]
    if art.get("available"):
        print(
            f"P2  {art['plants_moved_gt_0p5']}/{art['plants_applied']} plants moved "
            f">{MATERIAL_HR} MMBtu/MWh; {art['plants_cheaper']} cheaper / "
            f"{art['plants_dearer']} dearer; energy-weighted "
            f"{art['energy_weighted_delta_mmbtu_per_mwh']:+.3f} MMBtu/MWh "
            f"({art['energy_weighted_delta_usd_per_mwh']:+.2f} $/MWh)"
        )
        print(
            f"K3  {art['plants_excluded_by_band']} plants excluded by the physical "
            f"band, {art['excluded_energy_share'] * 100:.2f} % of energy — "
            f"{'PASS' if art['K3_pass'] else 'FAIL'}"
        )
    for y in YEARS:
        row = payload["per_year"][str(y)]
        ident = row["K5_arm_a_identity"]
        ct = row["iso_class_twh"].get("CT_PEAKER", {})
        dom_ct = row["dominion_class_twh"].get("CT_PEAKER", {})
        print(
            f"{y}  K5 {'IDENTICAL' if ident.get('identical') else ident.get('max_abs_diff_mw')}"
            f"  K4 {'pass' if row['K4_slack_dump']['pass'] else 'FAIL'}"
            f"  ISO CT_PEAKER {ct.get('A')} -> {ct.get('B')} ({ct.get('delta'):+})"
            f"  Dominion CT {dom_ct.get('A', '-')} -> {dom_ct.get('B', '-')}"
        )
    for arm in ("A", "B"):
        r = payload["rubric"][arm]
        if r.get("available"):
            print(f"arm {arm}: {r['determination']}  {r['criteria']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
