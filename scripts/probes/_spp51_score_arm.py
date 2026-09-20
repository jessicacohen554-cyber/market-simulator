"""SPP-51 (ZERO LP): score the arm against its own same-HEAD control, per year.

Rule 29 [R-SCREEN] (b) form 4 is VOID for SPP -- both registered runs predate the
rule 36 [R-YEAR-ISOLATION] warm-start flip (cb1e60b7) and were solved as single
multi-year invocations, so the committed keeper is not a like-for-like control
for a year-isolated solve at HEAD. Each shard therefore solved BOTH legs, and
this scores arm - control at one HEAD, plus control - keeper, which is the first
measurement of the rule-36 contamination in SPP.

Run: PYTHONPATH=src python3 scripts/probes/_spp51_score_arm.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from scripts.lib.spp63_g5 import score_c3, class_twh, load_bench  # noqa: E402

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
KEEPER = {y: "results/calibration/spp49_benchmembership_span" for y in (2019, 2020, 2021, 2022)}
KEEPER.update({y: "results/calibration/spp42_span_a" for y in (2023, 2024, 2025)})
CLASSES = ("COAL_PRB", "COAL_LIGNITE", "CC_REGULAR", "CT_PEAKER", "ST_GAS", "wind", "solar")


def price_stats(bundle: str | Path, year: int) -> dict:
    """Load-weighted system price, negative-hour count and minimum."""
    s = pd.read_parquet(Path(bundle) / "hourly" / f"system_{year}.parquet")
    if "pass" in s.columns:
        s = s[s["pass"] == "P1"]
    mp = ((s["price"] * s["demand"]).groupby(s["hour"]).sum()
          / s.groupby("hour")["demand"].sum()).to_numpy()
    d = s.groupby("hour")["demand"].sum().to_numpy()
    return {
        "lw_price": float((mp * d).sum() / d.sum()),
        "h_neg": int((mp < 0).sum()),
        "min_price": float(mp.min()),
        "slack_MWh": float(s["slack"].sum()),
        "dump_MWh": float(s["dump"].sum()),
    }


def main() -> None:
    have = [y for y in YEARS
            if (REPO / f"results/calibration/spp51_arm_{y}").exists()
            and (REPO / f"results/calibration/spp51_control_{y}").exists()]
    if not have:
        print("no SPP-51 bundle pairs on disk yet")
        return
    pd.set_option("display.width", 250)

    vol, prc, sc = [], [], []
    for y in have:
        arm, ctl, kp = (f"results/calibration/spp51_arm_{y}",
                        f"results/calibration/spp51_control_{y}", KEEPER[y])
        a, c = class_twh(arm, y), class_twh(ctl, y)
        k = class_twh(kp, y)
        b = load_bench(y)["classFull"]
        row = {"year": y}
        for cl in CLASSES:
            row[f"{cl}|ctl"] = c.get(cl, 0.0)
            row[f"{cl}|arm"] = a.get(cl, 0.0)
            row[f"{cl}|d"] = a.get(cl, 0.0) - c.get(cl, 0.0)
            row[f"{cl}|drift"] = c.get(cl, 0.0) - k.get(cl, 0.0)
            row[f"{cl}|act"] = float(b.get(cl, float("nan")))
        vol.append(row)

        pa, pc = price_stats(arm, y), price_stats(ctl, y)
        prc.append({"year": y,
                    "lw_ctl": pc["lw_price"], "lw_arm": pa["lw_price"],
                    "lw_d": pa["lw_price"] - pc["lw_price"],
                    "hneg_ctl": pc["h_neg"], "hneg_arm": pa["h_neg"],
                    "hneg_d": pa["h_neg"] - pc["h_neg"],
                    "min_ctl": pc["min_price"], "min_arm": pa["min_price"],
                    "slack_arm": pa["slack_MWh"], "dump_arm": pa["dump_MWh"],
                    "slack_ctl": pc["slack_MWh"]})

        bench = load_bench(y)
        ra, rc = score_c3(arm, y, bench), score_c3(ctl, y, bench)
        sc.append({"year": y,
                   "C3a_ctl": rc["C3a"].get("model"), "C3a_arm": ra["C3a"].get("model"),
                   "C3a_st_ctl": rc["C3a"].get("status"), "C3a_st_arm": ra["C3a"].get("status"),
                   "C3b_ctl": rc["C3b"].get("model"), "C3b_arm": ra["C3b"].get("model"),
                   "C3b_st_ctl": rc["C3b"].get("status"), "C3b_st_arm": ra["C3b"].get("status")})

    V = pd.DataFrame(vol)
    print("=== C1 VOLUMES (TWh): arm - control, at one HEAD ===")
    print(V[["year"] + [f"{c}|{k}" for c in CLASSES for k in ("ctl", "arm", "d")]]
          .to_string(index=False, float_format=lambda v: f"{v:8.3f}"))
    print()
    print("=== C1 vs ACTUAL (model - actual, TWh) ===")
    err = {"year": V["year"]}
    for c in CLASSES:
        err[f"{c}|ctl"] = V[f"{c}|ctl"] - V[f"{c}|act"]
        err[f"{c}|arm"] = V[f"{c}|arm"] - V[f"{c}|act"]
    print(pd.DataFrame(err).to_string(index=False, float_format=lambda v: f"{v:8.3f}"))
    print()
    print("=== RULE 36 CONTAMINATION: control(HEAD, year-isolated) - keeper(committed) TWh ===")
    print(V[["year"] + [f"{c}|drift" for c in CLASSES]]
          .to_string(index=False, float_format=lambda v: f"{v:8.4f}"))
    print()
    print("=== PRICE ===")
    print(pd.DataFrame(prc).to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
    print()
    print("=== C3a / C3b (scorer's own functions, committed bench) ===")
    print(pd.DataFrame(sc).to_string(index=False))


if __name__ == "__main__":
    main()
