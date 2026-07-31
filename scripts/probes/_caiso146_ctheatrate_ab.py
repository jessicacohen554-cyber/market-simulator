"""caiso-146 A/B scorer — `measured_ct_heat_rates` against the caiso-139 keeper.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-caiso146-ct-heat-rates-2026-07-31.md`` from the two
solved bundles plus the committed CAISO artifact. **No solve, and no gate that
is not in the prereg.**

Construction gates (prereg §4):

* **K1 flag fidelity** — arm B records ``measured_ct_heat_rates=true``, arm A
  ``false``; all 43 artifact rows carry ``flag == "ok"``.
* **K2 control integrity** — arm A reproduces the committed keeper class-hour
  for class-hour (a true zero-delta replay lands at 0.0 MW).
* **K3 mechanism is LIVE** — ``max |Δ CT_PEAKER MW| > 50`` in at least one
  year (the nyiso-89 §4a check). Failing this is verdict ``I``, not ``R``.
* **K4 single delta** — the arms' ``run_config`` scenario blocks differ in
  exactly the one boolean.
* **K5 year span** — both bundles carry ``[2023, 2024, 2025]`` and nothing else
  (rule 22 / D-6 quarantine).
* **K6 Delano sensitivity** — CT_PEAKER energy recomputed with plant 58122
  (the broken heat-input channel of prereg §2.4) excluded, both arms. The
  verdict must not hinge on that row.

Everything else — C1-class TWh, mean λ, slack/dump — is REPORTED, per prereg §7:
a worse backcast is a discovered bug under rules 1/14, not a kill condition.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso146_ctheatrate_ab.py
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = Path("results/calibration/caiso146_control_A")
ARM_B = Path("results/calibration/caiso146_ctheatrate_B")
KEEPER = Path("results/calibration/caiso139_dumpguard_B")
ARTIFACT = Path("data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv")
BENCH = Path("frontend/data/backcast/bench/CAISO")
OUT_PATH = Path("results/probes/caiso146_ctheatrate_ab.json")

#: PREREG §4 K3 — the liveness floor, in MW of class dispatch divergence.
K3_LIVENESS_MW = 50.0
#: PREREG §4 K2 — a zero-delta replay must land inside this many MW.
K2_TOL_MW = 1e-6
#: PREREG §2.4 — the broken heat-input channel excluded by the K6 sensitivity.
DELANO_PLANT_CODE = 58122
#: The three plants caiso-119 R4 named when it attributed the CT_PEAKER
#: priced-out defect (model/actual TWh 2024: 0.019/1.42, 0.077/0.48,
#: 0.082/0.32). Reported per-plant so this arm answers R4 directly — R4's
#: standing guardrail is that "marking peaker offers down until 4 TWh appears"
#: is rule-1/13 forbidden, so what matters is whether a MEASURED re-price moves
#: them at all, not whether it closes the gap.
CAISO119_R4_PLANTS = {56803: "Panoche", 57482: "Sentinel", 57515: "Walnut Creek"}
#: Realized Henry Hub by year, the basis the prereg quotes its $/MWh at.
GAS_USD_PER_MMBTU = {2023: 2.54, 2024: 2.19, 2025: 3.52}


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max/by-class class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
        },
    }


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _ca_lambda(bundle: Path, year: int) -> float:
    """CA demand-weighted mean λ (WECC seam pseudo-nodes excluded).

    The caiso-125 ``ca_lambda`` definition, inlined so this scorer depends only
    on the committed sidecars.
    """
    frame = _system(bundle, year)
    ca = frame[~frame["zone"].str.startswith("WECC")]
    return round(float((ca["price"] * ca["demand"]).sum() / ca["demand"].sum()), 4)


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


def _flag(bundle: Path) -> bool | None:
    """The bundle's recorded ``measured_ct_heat_rates`` setting."""
    path = bundle / "run_config.json"
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    scen = cfg.get("scenario_config", {})
    if "measured_ct_heat_rates" in scen:
        return bool(scen["measured_ct_heat_rates"])
    # replay_keeper routes --set through the generic prb_overrides channel too.
    ovr = (cfg.get("calibration_flags", {}) or {}).get(
        "coal_prb_sigmoid_overrides"
    ) or {}
    if "measured_ct_heat_rates" in ovr:
        return bool(ovr["measured_ct_heat_rates"])
    return None


def _scenario_block(bundle: Path) -> dict:
    cfg = json.loads((bundle / "run_config.json").read_text())
    return cfg.get("scenario_config", {}) or {}


def _k4_single_delta() -> dict:
    """PREREG K4 — the arms' ScenarioConfig blocks differ in one boolean."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "passed": list(diff) == ["measured_ct_heat_rates"],
    }


def _k5_year_span() -> dict:
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    ok = all(v == [2023, 2024, 2025] for v in spans.values())
    return {"years": spans, "passed": ok}


def _k6_delano(year: int) -> dict:
    """PREREG K6 — CT_PEAKER energy with the broken-meter plant excluded."""
    out: dict = {"plant_code": DELANO_PLANT_CODE}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
        if not path.exists():
            out[name] = None
            continue
        frame = pd.read_parquet(
            path, columns=["pass", "plant_code", "plant_group", "mw"]
        )
        frame = frame[(frame["pass"] == "P1") & (frame["plant_group"] == "CT_PEAKER")]
        total = float(frame["mw"].sum()) / 1e6
        delano = (
            float(frame.loc[frame["plant_code"] == DELANO_PLANT_CODE, "mw"].sum()) / 1e6
        )
        out[name] = {
            "ct_peaker_twh": round(total, 4),
            "delano_twh": round(delano, 4),
            "ct_peaker_twh_ex_delano": round(total - delano, 4),
        }
    if out.get("A") and out.get("B"):
        d_full = out["B"]["ct_peaker_twh"] - out["A"]["ct_peaker_twh"]
        d_ex = out["B"]["ct_peaker_twh_ex_delano"] - out["A"]["ct_peaker_twh_ex_delano"]
        out["delta_twh_full"] = round(d_full, 4)
        out["delta_twh_ex_delano"] = round(d_ex, 4)
        out["delano_share_of_delta"] = (
            round(1.0 - d_ex / d_full, 4) if abs(d_full) > 1e-9 else None
        )
        # The verdict hinges on Delano only if removing it reverses the sign or
        # wipes out the class move entirely.
        out["passed"] = bool(
            abs(d_full) < 1e-9 or (d_ex * d_full > 0 and abs(d_ex) > 0.2 * abs(d_full))
        )
    else:
        out["passed"] = False
    return out


def _r4_plants(year: int) -> dict:
    """Per-plant CT_PEAKER TWh for the three plants caiso-119 R4 named."""
    out: dict = {}
    frames: dict[str, pd.DataFrame] = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
        if not path.exists():
            return {}
        frame = pd.read_parquet(
            path, columns=["pass", "plant_code", "plant_group", "mw"]
        )
        frames[name] = frame[
            (frame["pass"] == "P1") & (frame["plant_group"] == "CT_PEAKER")
        ]
    for code, label in CAISO119_R4_PLANTS.items():
        a = float(frames["A"].loc[frames["A"]["plant_code"] == code, "mw"].sum()) / 1e6
        b = float(frames["B"].loc[frames["B"]["plant_code"] == code, "mw"].sum()) / 1e6
        out[label] = {
            "plant_code": code,
            "A": round(a, 4),
            "B": round(b, 4),
            "delta": round(b - a, 4),
        }
    return out


def _actual_class_twh(year: int) -> dict:
    path = BENCH / f"{year}.json.gz"
    if not path.exists():
        return {}
    bench = json.loads(gzip.open(path).read())["bench"]
    return bench.get("classFull", {})


def _artifact_report() -> dict:
    art = pd.read_csv(ARTIFACT)
    ok = art[art["flag"] == "ok"].dropna(subset=["model_heat_rate_egrid"])
    delta = ok["heat_rate"] - ok["model_heat_rate_egrid"]
    cap, gen = ok["class_capacity_mw"], ok["gross_mwh"]
    return {
        "plants_total": int(len(art)),
        "plants_applied": int(len(ok)),
        "plants_excluded_by_band": int((art["flag"] != "ok").sum()),
        "capacity_applied_mw": round(float(cap.sum()), 1),
        "cheaper": int((delta < 0).sum()),
        "dearer": int((delta > 0).sum()),
        "moved_gt_0p5": int((delta.abs() > 0.5).sum()),
        "moved_gt_1p0": int((delta.abs() > 1.0).sum()),
        "cap_weighted_model": round(
            float((ok["model_heat_rate_egrid"] * cap).sum() / cap.sum()), 4
        ),
        "cap_weighted_measured": round(
            float((ok["heat_rate"] * cap).sum() / cap.sum()), 4
        ),
        "gen_weighted_model": round(
            float((ok["model_heat_rate_egrid"] * gen).sum() / gen.sum()), 4
        ),
        "gen_weighted_measured": round(
            float((ok["heat_rate"] * gen).sum() / gen.sum()), 4
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """Score the prereg's construction gates and report the scored criteria."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args(argv)

    result: dict = {
        "probe": "caiso146_ctheatrate_ab",
        "prereg": "results/calibration/PREREG-caiso146-ct-heat-rates-2026-07-31.md",
        "arm_a": str(ARM_A),
        "arm_b": str(ARM_B),
        "keeper": str(KEEPER),
        "gas_usd_per_mmbtu": GAS_USD_PER_MMBTU,
        "artifact": _artifact_report(),
        "K1_flag_fidelity": {},
        "K4_single_delta": _k4_single_delta(),
        "K5_year_span": _k5_year_span(),
        "years": {},
    }
    art = result["artifact"]
    result["K1_flag_fidelity"] = {
        "arm_a_flag": _flag(ARM_A),
        "arm_b_flag": _flag(ARM_B),
        "all_rows_ok": art["plants_excluded_by_band"] == 0,
        "passed": bool(
            _flag(ARM_A) is False
            and _flag(ARM_B) is True
            and art["plants_excluded_by_band"] == 0
        ),
    }

    k2_ok, k3_any, k6_ok = True, False, True
    for year in YEARS:
        row: dict = {}
        live = _pairwise(ARM_A, ARM_B, year)
        ct = live["max_by_class_mw"].get("CT_PEAKER", 0.0)
        row["K3_liveness"] = {
            **live,
            "ct_peaker_max_abs_diff_mw": ct,
            "passed": bool(ct > K3_LIVENESS_MW),
        }
        k3_any = k3_any or row["K3_liveness"]["passed"]

        ident = _pairwise(ARM_A, KEEPER, year)
        ident["passed"] = bool(ident["max_abs_diff_mw"] < K2_TOL_MW)
        row["K2_control_integrity"] = ident
        k2_ok = k2_ok and ident["passed"]

        a_twh, b_twh = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        actual = _actual_class_twh(year)
        row["class_twh"] = {
            k: {
                "A": a_twh.get(k, 0.0),
                "B": b_twh.get(k, 0.0),
                "delta": round(b_twh.get(k, 0.0) - a_twh.get(k, 0.0), 4),
                "actual": actual.get(k),
            }
            for k in sorted(set(a_twh) | set(b_twh))
        }
        row["ca_lambda_usd_mwh"] = {
            "A": _ca_lambda(ARM_A, year),
            "B": _ca_lambda(ARM_B, year),
        }
        row["ca_lambda_usd_mwh"]["delta"] = round(
            row["ca_lambda_usd_mwh"]["B"] - row["ca_lambda_usd_mwh"]["A"], 4
        )
        sa, da = _slack_dump(ARM_A, year)
        sb, db = _slack_dump(ARM_B, year)
        row["slack_dump_mwh"] = {
            "A_slack": sa,
            "B_slack": sb,
            "A_dump": da,
            "B_dump": db,
        }

        row["caiso119_r4_plants"] = _r4_plants(year)
        row["K6_delano"] = _k6_delano(year)
        k6_ok = k6_ok and bool(row["K6_delano"]["passed"])
        result["years"][str(year)] = row

    result["summary"] = {
        "K1_flag_fidelity": result["K1_flag_fidelity"]["passed"],
        "K2_control_integrity": k2_ok,
        "K3_liveness": k3_any,
        "K4_single_delta": result["K4_single_delta"]["passed"],
        "K5_year_span": result["K5_year_span"]["passed"],
        "K6_delano_sensitivity": k6_ok,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")

    print(json.dumps(result["summary"], indent=1))
    print(
        f"\nartifact: {art['plants_applied']}/{art['plants_total']} rows applied, "
        f"{art['cheaper']} cheaper / {art['dearer']} dearer, cap-wt "
        f"{art['cap_weighted_model']} -> {art['cap_weighted_measured']} MMBtu/MWh"
    )
    for year in YEARS:
        row = result["years"][str(year)]
        ct = row["class_twh"].get("CT_PEAKER", {})
        lam = row["ca_lambda_usd_mwh"]
        print(f"\n{year}:")
        print(
            f"  CT_PEAKER TWh   A {ct.get('A')} -> B {ct.get('B')} "
            f"({ct.get('delta'):+}) vs actual {ct.get('actual')}"
        )
        print(f"  CA lambda $/MWh A {lam['A']} -> B {lam['B']} ({lam['delta']:+})")
        print(
            f"  liveness  max |Δ CT_PEAKER| {row['K3_liveness']['ct_peaker_max_abs_diff_mw']} MW"
            f" ; arm-A vs keeper max |Δ| {row['K2_control_integrity']['max_abs_diff_mw']} MW"
        )
        big = sorted(
            (
                (k, v["delta"])
                for k, v in row["class_twh"].items()
                if abs(v["delta"]) > 0.01
            ),
            key=lambda kv: -abs(kv[1]),
        )
        if big:
            print(
                "  class moves >0.01 TWh: " + ", ".join(f"{k} {d:+.4f}" for k, d in big)
            )
        r4 = row.get("caiso119_r4_plants") or {}
        if r4:
            print(
                "  caiso-119 R4 plants: "
                + ", ".join(
                    f"{k} {v['A']}->{v['B']} ({v['delta']:+.4f})" for k, v in r4.items()
                )
            )
        k6 = row["K6_delano"]
        if k6.get("A"):
            print(
                f"  K6 Delano: class Δ {k6['delta_twh_full']:+} TWh, "
                f"ex-Delano {k6['delta_twh_ex_delano']:+} TWh "
                f"(Delano is {k6['delano_share_of_delta']} of it)"
            )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
