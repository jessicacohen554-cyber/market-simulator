"""miso-231 screen scorer — the FOUR gates of PRECOMMIT §4d as corrected by
Addendum A, applied to the 2024 screen arm against the keeper's committed 2024
artifacts.

Committed and pushed BEFORE the arm's bundle was read (rule 29: a gate the
result cannot have been written to fit). Every bar and every comparator is a
module-level constant below, taken from the PRECOMMIT and its Addendum A.

The gates are STRUCTURAL and STOP-ONLY. They may kill the arm; they may never
promote it. None is gated on the target residual and none contributes to a
determination.

Usage: python3 scripts/probes/_miso231_screen_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso230_ctdrag_seam_K"
ARM = REPO / "results/calibration/miso231_hourlyseam_S"
OUT = REPO / "results/calibration/_miso231_screen_gates.json"
YEAR = 2024
ZONE = "MISO-Indiana"
HOURS = 8760

# --- comparators, all from the keeper's own committed 2024 artifacts --------
KEEPER_CORR_OWN_PRICE = 0.4461  # Addendum A.1
G1_MIN_FALL = 0.30  # PRECOMMIT §4d magnitude, re-anchored by A.1
G1_OVERSHOOT_FLOOR = -0.60  # below this ⇒ wiring error
KEEPER_SLACK_TWH_2024 = 0.0196  # miso-230 assessment §8(f), pre-existing
G5_CHEAP_HOURS_N = 2111  # frozen miso-225/226 G-2 hour set, 2024
KEEPER_CHEAP_IMPORT_MW = 2129.3  # Addendum A.3


def _price(bundle: Path, zone: str) -> np.ndarray:
    s = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] == zone)]
    return s.sort_values("hour")["price"].to_numpy(float)


def _imports(bundle: Path) -> np.ndarray:
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == "import")]
    return (
        c.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def _slack_dump_twh(bundle: Path) -> tuple[float, float]:
    s = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
    s = s[s["pass"] == "P1"]
    out = []
    for col in ("slack_mw", "slack", "dump_mw", "dump"):
        if col in s.columns:
            out.append((col, float(s[col].sum()) / 1e6))
    d = dict(out)
    return (
        d.get("slack_mw", d.get("slack", float("nan"))),
        d.get("dump_mw", d.get("dump", float("nan"))),
    )


def _decile_slope(price: np.ndarray, series: np.ndarray) -> float:
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    return float(series[parts[0]].mean() - series[parts[-1]].mean())


def main() -> int:
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    if not (ARM / f"hourly/class_hourly_{YEAR}.parquet").exists():
        print(f"arm bundle not present at {ARM}")
        return 2

    k_imp, a_imp = _imports(KEEPER), _imports(ARM)
    k_p, a_p = _price(KEEPER, ZONE), _price(ARM, ZONE)
    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    cheap = np.isfinite(act) & (act < 20.0)

    res: dict[str, object] = {
        "scorer": "miso-231 screen gates (PRECOMMIT §4d as corrected by Addendum A)",
        "year": YEAR,
        "keeper": "2026-09-06-miso-230-ctdrag-seam",
        "arm_bundle": ARM.name,
        "gates": {},
        "reported_only": {},
    }

    # --- G-1 responsiveness -------------------------------------------------
    a_corr = float(np.corrcoef(a_imp, a_p)[0, 1])
    fall = KEEPER_CORR_OWN_PRICE - a_corr
    g1_pass = bool(fall >= G1_MIN_FALL and a_corr >= G1_OVERSHOOT_FLOOR)
    res["gates"]["G1_responsiveness"] = {
        "bar": f"corr falls >= {G1_MIN_FALL} from the keeper's own 2024 "
        f"{KEEPER_CORR_OWN_PRICE:+.4f} (land <= "
        f"{KEEPER_CORR_OWN_PRICE - G1_MIN_FALL:+.4f}); no overshoot below "
        f"{G1_OVERSHOOT_FLOOR:+.2f}",
        "keeper_corr_own_price": KEEPER_CORR_OWN_PRICE,
        "arm_corr_own_price": round(a_corr, 4),
        "fall": round(fall, 4),
        "measured_target": -0.101,
        "verdict": "PASS" if g1_pass else "FAIL",
    }

    # --- G-3 confinement (feasibility half; the band half is structural) ----
    k_sl, k_du = _slack_dump_twh(KEEPER)
    a_sl, a_du = _slack_dump_twh(ARM)
    g3_pass = bool(
        (np.isnan(a_sl) or a_sl <= KEEPER_SLACK_TWH_2024 + 1e-6)
        and (np.isnan(a_du) or a_du <= 1e-6)
    )
    res["gates"]["G3_confinement"] = {
        "bar": "no slack increase beyond the keeper's pre-existing "
        f"{KEEPER_SLACK_TWH_2024} TWh; dump 0.0000 TWh. The band half (SPP / "
        "South / Manitoba mc byte-identical) is verified structurally ex ante "
        "by tests/iso/miso/test_miso_seam_ladder.py::TestHourlyNeighbourOverlay"
        "::test_spp_and_south_keep_their_scalar_ladders",
        "keeper_slack_twh": round(k_sl, 4) if not np.isnan(k_sl) else None,
        "arm_slack_twh": round(a_sl, 4) if not np.isnan(a_sl) else None,
        "keeper_dump_twh": round(k_du, 4) if not np.isnan(k_du) else None,
        "arm_dump_twh": round(a_du, 4) if not np.isnan(a_du) else None,
        "verdict": "PASS" if g3_pass else "FAIL",
    }

    # --- G-5 cheap-hour direction ------------------------------------------
    a_cheap = float(a_imp[cheap].mean())
    g5_pass = bool(a_cheap > KEEPER_CHEAP_IMPORT_MW)
    res["gates"]["G5_cheap_hour_direction"] = {
        "bar": "solved imports RISE in the frozen miso-225/226 G-2 hour set "
        f"(real Indiana hub < $20, n = {G5_CHEAP_HOURS_N})",
        "n_hours": int(cheap.sum()),
        "keeper_import_mw": KEEPER_CHEAP_IMPORT_MW,
        "arm_import_mw": round(a_cheap, 1),
        "delta_mw": round(a_cheap - KEEPER_CHEAP_IMPORT_MW, 1),
        "verdict": "PASS" if g5_pass else "FAIL",
    }

    # --- G-4 is scored from calibration_verdict.py, recorded separately -----
    res["gates"]["G4_no_collateral_flip"] = {
        "bar": "no non-target load-bearing criterion flips PASS->FAIL vs the "
        "keeper's committed 2024 scores (C1 cells, C2, C3a, C3b, C6); C3c "
        "excluded (ledgered caveat, rubric v3.3)",
        "verdict": "SCORED SEPARATELY — scripts/calibration_verdict.py on the "
        "arm bundle vs the keeper's committed metrics.json",
    }

    # --- REPORTED-ONLY (Addendum A.2: G-2 withdrawn) ------------------------
    res["reported_only"]["annual_import_volume"] = {
        "note": "Addendum A.2 — G-2 WITHDRAWN as a gate: the slim keeper "
        "bundle carries no unit-level dispatch, so the control's imports "
        "cannot be decomposed by seam, and the model's GROSS import class is "
        "not comparable to the measured NET seam total. Recorded, not gated.",
        "keeper_twh": round(float(k_imp.sum()) / 1e6, 4),
        "arm_twh": round(float(a_imp.sum()) / 1e6, 4),
        "delta_twh": round(float(a_imp.sum() - k_imp.sum()) / 1e6, 4),
    }
    res["reported_only"]["decile_slope"] = {
        "keeper_on_own_price_mw": -4362.3,
        "arm_on_own_price_mw": round(_decile_slope(a_p, a_imp), 1),
        "keeper_on_measured_price_mw": -3321.6,
        "arm_on_measured_price_mw": round(
            _decile_slope(act[np.isfinite(act)], a_imp[np.isfinite(act)]), 1
        ),
        "measured_seam_2024_mw": 1384.0,
        "note": "POSITIVE = imports MORE when MISO is cheap (the measured "
        "behaviour). Reported, not gated — the PRECOMMIT's pre-committed "
        "non-claim is that the slope stays negative.",
    }
    res["reported_only"]["arm_corr_on_measured_price"] = round(
        float(np.corrcoef(a_imp[np.isfinite(act)], act[np.isfinite(act)])[0, 1]), 4
    )
    res["reported_only"]["keeper_corr_on_measured_price"] = 0.3211

    scored = [
        v for v in res["gates"].values() if v["verdict"] in ("PASS", "FAIL")
    ]
    res["verdict"] = (
        "ALL SCORED GATES PASS"
        if all(v["verdict"] == "PASS" for v in scored)
        else "KILLED"
    )
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"wrote {OUT}\n")
    for name, g in res["gates"].items():
        print(f"[{g['verdict']:>4}] {name}")
        for k, v in g.items():
            if k in ("verdict", "bar"):
                continue
            print(f"         {k}: {v}")
    print("\n--- REPORTED-ONLY ---")
    print(json.dumps(res["reported_only"], indent=1))
    print(f"\nSCREEN VERDICT (scored gates): {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
