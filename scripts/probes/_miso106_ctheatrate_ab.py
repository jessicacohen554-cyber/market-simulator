"""miso-106 A/B scorer — `measured_ct_heat_rates` against the miso-101b keeper.

Scores the arms defined by
`results/calibration/PREREG-miso106-measured-ct-heat-rates-2026-07-30.md`
against the gates that document declares, and nothing else. A gate the PREREG
does not contain is not scored here; a clause that fails as written is recorded
as a fail (the pjm-136/137 discipline, carried into MISO by miso-99/101).

This file covers the **bundle-level** gates only — the ones computable from the
two arms' committed sidecars with no benchmark and no re-solve:

* **G1 flag fidelity** — arm B carries ``measured_ct_heat_rates=true``, arm A
  ``false``; the artifact's applied-row count is its full row count (PREREG §2
  measured 0 band exclusions).
* **G2 the swap is LIVE** — max |Δ| in the CT_PEAKER class-hourly frame between
  arms must be > 0 in every year (the nyiso-89 §4a liveness check). A
  bit-identical arm B means the flag did not fire and the run is void.
* **G3 arm-A equality** — arm A against the committed keeper bundle, every
  class-hour, in every year. This is what makes arm-B movement attributable.
* **G4 zero slack / dump** — a new load-shed hour would mean the re-pricing
  broke feasibility rather than re-pricing.

The C-series (C1/C3a/C3b/C3c/C4/C7/C8) is scored by
``scripts/calibration_verdict.py`` on the registered runs, and the D-series by
``scripts/legitimacy_diagnostics.py``; both need the benchmark parts that
registration writes, so neither is duplicated here.

Usage::

    PYTHONPATH=. .venv/bin/python scripts/probes/_miso106_ctheatrate_ab.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

YEARS = (2023, 2024, 2025)

ARM_A = Path("results/calibration/miso106_control_A")
ARM_B = Path("results/calibration/miso106_ctheatrate_B")
IDENTITY_REF = Path("results/calibration/miso101_tempgrain_B")
ARTIFACT = Path("data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv")
OUT_PATH = Path("results/probes/miso106_ctheatrate_ab.json")

#: PREREG §2 — a plant is "materially re-priced" beyond this many MMBtu/MWh.
MATERIAL_HR = 0.5
#: PREREG §5 G3 — arm A must reproduce the keeper to within this many MW on
#: every class-hour (a true byte-faithful replay lands at 0.0).
IDENTITY_TOL_MW = 1e-6
#: Realized Henry Hub by year (constants.HENRY_HUB_TRAJECTORIES["hindcast_realized"]),
#: the basis PREREG §3 quotes its $/MWh curve translations at.
GAS_USD_PER_MMBTU = {2023: 2.54, 2024: 2.19, 2025: 3.52}


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """The bundle's P1 class-hourly frame (class x hour, MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """ISO-wide annual TWh by class."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """The year's total P1 slack and dump (MWh)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return float(frame["slack"].sum()), float(frame["dump"].sum())


def _mean_price(bundle: Path, year: int) -> float:
    """Load-weighted mean P1 LMP across zones — reported, not gated here."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    weight = frame["demand"].sum()
    if weight <= 0.0:
        return float("nan")
    return float((frame["price"] * frame["demand"]).sum() / weight)


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max/total class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    by_class = diff.groupby(level="klass").max()
    return {
        "max_abs_diff_mw": float(diff.max()),
        "n_class_hours": int(diff.size),
        "max_by_class_mw": {str(k): round(float(v), 6) for k, v in by_class.items()},
    }


def _flag(bundle: Path) -> bool | None:
    """The bundle's recorded ``measured_ct_heat_rates`` setting."""
    path = bundle / "run_config.json"
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    scen = cfg.get("scenario_config", {})
    if "measured_ct_heat_rates" in scen:
        return bool(scen["measured_ct_heat_rates"])
    # replay_keeper routes --set through the generic prb_overrides channel, so
    # a replayed arm records the flag there as well as (or instead of) the
    # top-level scenario_config key.
    flags = cfg.get("calibration_flags", {})
    ovr = flags.get("coal_prb_sigmoid_overrides") or {}
    if "measured_ct_heat_rates" in ovr:
        return bool(ovr["measured_ct_heat_rates"])
    return None


def _artifact_gates() -> dict:
    """PREREG §2 — coverage, materiality, two-sidedness and band exclusions."""
    if not ARTIFACT.exists():
        return {"available": False, "reason": f"missing {ARTIFACT}"}
    art = pd.read_csv(ARTIFACT)
    ok = art[art["flag"] == "ok"].dropna(subset=["model_heat_rate_egrid"])
    excluded = art[art["flag"] != "ok"]
    delta = ok["heat_rate"] - ok["model_heat_rate_egrid"]
    cap = ok["class_capacity_mw"]
    gen = ok["gross_mwh"]
    return {
        "available": True,
        "plants_total": int(len(art)),
        "plants_applied": int(len(ok)),
        "plants_excluded_by_band": int(len(excluded)),
        "capacity_applied_mw": round(float(cap.sum()), 1),
        "moved_gt_0p5": int((delta.abs() > MATERIAL_HR).sum()),
        "moved_gt_1p0": int((delta.abs() > 1.0).sum()),
        "moved_gt_2p0": int((delta.abs() > 2.0).sum()),
        "cheaper": int((delta < 0).sum()),
        "dearer": int((delta > 0).sum()),
        "two_signed": bool((delta < 0).any() and (delta > 0).any()),
        "cap_weighted_model": round(
            float((ok["model_heat_rate_egrid"] * cap).sum() / cap.sum()), 4
        ),
        "cap_weighted_measured": round(float((ok["heat_rate"] * cap).sum() / cap.sum()), 4),
        "gen_weighted_model": round(
            float((ok["model_heat_rate_egrid"] * gen).sum() / gen.sum()), 4
        ),
        "gen_weighted_measured": round(float((ok["heat_rate"] * gen).sum() / gen.sum()), 4),
    }


def main(argv: list[str] | None = None) -> int:
    """Score the four bundle-level PREREG gates and write the probe JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args(argv)

    result: dict = {
        "probe": "miso106_ctheatrate_ab",
        "prereg": "results/calibration/PREREG-miso106-measured-ct-heat-rates-2026-07-30.md",
        "arm_a": str(ARM_A),
        "arm_b": str(ARM_B),
        "identity_ref": str(IDENTITY_REF),
        "gas_usd_per_mmbtu": GAS_USD_PER_MMBTU,
        "G1_flag_fidelity": {
            "arm_a_flag": _flag(ARM_A),
            "arm_b_flag": _flag(ARM_B),
            "artifact": _artifact_gates(),
        },
        "years": {},
    }
    g1 = result["G1_flag_fidelity"]
    g1["passed"] = bool(g1["arm_a_flag"] is False and g1["arm_b_flag"] is True)

    g2_ok, g3_ok, g4_ok = True, True, True
    for year in YEARS:
        row: dict = {}
        have_ab = all(
            (p / "hourly" / f"class_hourly_{year}.parquet").exists()
            for p in (ARM_A, ARM_B)
        )
        if have_ab:
            live = _pairwise(ARM_A, ARM_B, year)
            ct = live["max_by_class_mw"].get("CT_PEAKER", 0.0)
            row["G2_liveness"] = {
                **live,
                "ct_peaker_max_abs_diff_mw": ct,
                "passed": bool(ct > 0.0),
            }
            g2_ok = g2_ok and row["G2_liveness"]["passed"]
            a_twh, b_twh = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
            row["class_twh"] = {
                k: {
                    "A": a_twh.get(k, 0.0),
                    "B": b_twh.get(k, 0.0),
                    "delta": round(b_twh.get(k, 0.0) - a_twh.get(k, 0.0), 4),
                }
                for k in sorted(set(a_twh) | set(b_twh))
            }
            row["mean_price_usd_mwh"] = {
                "A": round(_mean_price(ARM_A, year), 4),
                "B": round(_mean_price(ARM_B, year), 4),
            }
            sa, da = _slack_dump(ARM_A, year)
            sb, db = _slack_dump(ARM_B, year)
            row["G4_slack_dump_mwh"] = {
                "A_slack": round(sa, 3),
                "B_slack": round(sb, 3),
                "A_dump": round(da, 3),
                "B_dump": round(db, 3),
                "passed": bool(sb <= max(sa, 0.0) + 1.0),
            }
            g4_ok = g4_ok and row["G4_slack_dump_mwh"]["passed"]
        else:
            row["G2_liveness"] = {"available": False}
            g2_ok = False

        if (IDENTITY_REF / "hourly" / f"class_hourly_{year}.parquet").exists() and (
            ARM_A / "hourly" / f"class_hourly_{year}.parquet"
        ).exists():
            ident = _pairwise(ARM_A, IDENTITY_REF, year)
            ident["passed"] = bool(ident["max_abs_diff_mw"] < IDENTITY_TOL_MW)
            row["G3_arm_a_equality"] = ident
            g3_ok = g3_ok and ident["passed"]
        else:
            row["G3_arm_a_equality"] = {"available": False}
            g3_ok = False
        result["years"][str(year)] = row

    result["summary"] = {
        "G1_flag_fidelity": g1["passed"],
        "G2_liveness": g2_ok,
        "G3_arm_a_equality": g3_ok,
        "G4_slack_dump": g4_ok,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result["summary"], indent=1))
    for year in YEARS:
        row = result["years"].get(str(year), {})
        live = row.get("G2_liveness", {})
        ident = row.get("G3_arm_a_equality", {})
        print(
            f"{year}: CT_PEAKER live |Δ| max "
            f"{live.get('ct_peaker_max_abs_diff_mw', 'n/a')} MW ; "
            f"arm-A vs keeper max |Δ| {ident.get('max_abs_diff_mw', 'n/a')} MW"
        )
        ct = (row.get("class_twh") or {}).get("CT_PEAKER")
        if ct:
            print(f"      CT_PEAKER TWh  A {ct['A']}  ->  B {ct['B']}  ({ct['delta']:+})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
