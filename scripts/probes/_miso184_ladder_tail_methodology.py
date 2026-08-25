"""miso-184 — the South export-ladder scarce-tail METHODOLOGY adjudication.

READ-ONLY. No LP is solved and nothing here re-enters a solve (rule 13
``[R-MEASURED]``): every number is a measurement of committed artifacts and
already-intaken public actuals, written to a JSON record for the finding.

Everything below is frozen by
``results/calibration/PREREG-miso184-south-export-ladder-tail-2026-08-24.md``
(committed and pushed BEFORE any adjudicating quantity was computed). The
question (miso-183 §5 / §8 item (5), owner-engaged): does the Q-Q derivation
(``scripts/data/derive_miso_seam_ladders.py``) — which couples the measured
South-seam flow-duration curve to DA hub LMP quantiles — reproduce its own
target flow in the RT-scarce tail the model is scored on, and if not, is a
corrected price basis (RT hub / South-zone DA / South-zone RT) the licensed
zero-free-parameter repair?

Stages (PREREG §2):
  F   footing — scarce sets 11/14/47; the frozen machinery re-derives the
      registered ladder byte-equal (STOP gates, not verdicts); the P9
      unconditional context.
  A   tail reproduction — measured scarce-mean South net export vs the
      registered ladder's export-side simulated clearing driven by DA (the
      derive's own offline-P9 convention, scarce-restricted). Defect line
      (2025): GAP >= 0.5 GW AND X_DA <= 0.5 x E_meas.
  B   coincidence orientation — unconditional vs scarce-conditional export
      depth durations per band; Spearman rank correlations (diagnosis; one
      declared reported line: c_1 >= d_1).
  C   basis attribution — per candidate B1 (RT hub) / B2 (South-zone DA) /
      B3 (South-zone RT): the as-armable re-derived export tuple (frozen Q-Q,
      cents rounding, no-wash clamp vs the UNCHANGED registered DA import
      ladder) and its scarce-tail clearing X_B driven by B. Repair line
      (2025): X_B >= 0.5 x E_meas as-armable; non-inversion (2023):
      X_B >= X_DA - 0.1 GW. Selection: largest as-armable X_B(2025);
      tie -> B1.

Sign conventions: seam ``flow`` is import-positive (the derive's own);
net export E = -flow; X = export-side simulated clearing, export-positive GW.

Run:
  uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,pyyaml \
    --python 3.12 python scripts/probes/_miso184_ladder_tail_methodology.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

CAL = ROOT / "results" / "calibration"
OUT = CAL / "_miso184_ladder_tail_methodology.json"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
ZONAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_zonal_MISO.parquet"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive (miso-174/178/183)
SCARCE_RT = 200.0
EXPECTED_SCARCE = {2023: 11, 2024: 14, 2025: 47}

# PREREG §2 frozen lines.
DEFECT_GAP_GW = 0.5
DEFECT_FRAC = 0.5
REPAIR_FRAC = 0.5
NONINVERT_GW = 0.1
FOOTING_TOL = 0.01  # $/MWh, any band beyond this -> STOP


def _load_derive_module():
    """Import the frozen derive machinery byte-for-byte from its own file."""
    spec = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", ROOT / "scripts" / "data" / "derive_miso_seam_ladders.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scarce_mask(year: int) -> np.ndarray:
    """The frozen miso-174/178/183 scarce mask: summer AND hub RT > $200."""
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year]
    rt = a.set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)
    idx = np.arange(HOURS)
    summer = (idx >= SUMMER[0]) & (idx < SUMMER[1])
    return summer & (rt > SCARCE_RT)


def south_zone_price(kind: str) -> pd.Series:
    """Hub-mean MISO-South measured price ('da'/'rt') indexed by (year, hour)."""
    z = pd.read_parquet(ZONAL)
    z = z[z["zone"] == "MISO-South"].copy()
    z["year"] = z["year"].astype("int64")
    z["hour"] = z["hour"].astype("int64")
    return z.groupby(["year", "hour"])[kind].mean().rename(f"south_{kind}")


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation (scipy-free: Pearson on ranks)."""
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def x_export(price: np.ndarray, sigmas: list[float], step: float, mask: np.ndarray) -> float:
    """Scarce-mean export-side clearing (GW): sum_k step * 1[price < sigma_k]."""
    x = sum(step * (price < s) for s in sigmas)
    v = x[mask]
    return float(v.mean()) / 1000.0 if v.size else float("nan")


def x_import(price: np.ndarray, pis: list[float], step: float, mask: np.ndarray) -> float:
    """Scarce-mean import-side clearing (GW): sum_k step * 1[price > pi_k]."""
    x = sum(step * (price > p) for p in pis)
    v = x[mask]
    return float(v.mean()) / 1000.0 if v.size else float("nan")


def main() -> None:
    mod = _load_derive_module()
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS  # noqa: E402
    from market_sim.model.interchange.spec import MISO_SEAM_LADDER_BY_YEAR  # noqa: E402
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES  # noqa: E402

    south_spec = next(n for n in INTERFACE_NEIGHBORS["MISO"] if n.name == "South")
    step = south_spec.interface_limit_mw / SEAM_FLOW_TRANCHES  # 375.0
    mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step  # 187.5 .. 2812.5
    seam_names = [n.name for n in INTERFACE_NEIGHBORS["MISO"]]

    df = mod.load_joined()
    df = df.join(south_zone_price("da")).join(south_zone_price("rt"))

    rec: dict = {
        "session": "miso-184",
        "prereg": "PREREG-miso184-south-export-ladder-tail-2026-08-24.md",
        "keeper_bundle": "miso177_rho_B (unchanged by this probe; no LP spent here)",
        "sign_convention": "seam flow import-positive; E/X net-export-positive GW",
        "band_grid_mw": {"step": step, "midpoints": mids.tolist()},
        "footing": {},
        "legA_tail_reproduction": {},
        "legB_orientation": {},
        "legC_candidates": {},
        "verdict": {},
    }

    stop = []
    E_meas: dict[int, float] = {}
    X_DA: dict[int, float] = {}
    XB: dict[str, dict[int, dict]] = {b: {} for b in ("B1_rt_hub", "B2_south_da", "B3_south_rt")}

    for y in YEARS:
        ys = str(y)
        g = df.loc[y]
        mask_hr = scarce_mask(y)

        # ---- F-1/F-2 footing
        n_sc = int(mask_hr.sum())
        ladders, notes = mod.derive(g)
        reg = MISO_SEAM_LADDER_BY_YEAR[y]
        max_dev, dev_where = 0.0, ""
        for seam, sides in reg.items():
            for side, vals in sides.items():
                got = ladders.get(seam, {}).get(side)
                if got is None or len(got) != len(vals):
                    stop.append(f"{y} {seam} {side}: derive shape mismatch")
                    continue
                d = float(np.max(np.abs(np.asarray(got) - np.asarray(vals))))
                if d > max_dev:
                    max_dev, dev_where = d, f"{seam}/{side}"
        if max_dev > FOOTING_TOL:
            stop.append(f"{y}: F-2 re-derivation deviates {max_dev:.2f} at {dev_where}")
        if n_sc != EXPECTED_SCARCE[y]:
            stop.append(f"{y}: F-1 scarce set {n_sc} != {EXPECTED_SCARCE[y]}")
        p9 = mod.offline_score(g, ladders)["South"]
        rec["footing"][ys] = {
            "n_scarce": n_sc,
            "rederive_max_abs_dev_usd": max_dev,
            "rederive_dev_where": dev_where,
            "derive_notes": notes,
            "p9_south_annual": p9,
        }

        # ---- base row set: g3 (derive's own) + finite rt
        g3 = g.dropna(subset=["da"] + seam_names)
        base = g3.dropna(subset=["rt"])
        hours_base = base.index.to_numpy()
        sc_base = mask_hr[hours_base]
        flow = base["South"].to_numpy(dtype=float)
        da = base["da"].to_numpy(dtype=float)
        rt = base["rt"].to_numpy(dtype=float)

        sig_reg = list(reg["South"]["export"])
        pi_reg = list(reg["South"]["import"])
        em = float((-flow)[sc_base].mean()) / 1000.0
        xda = x_export(da, sig_reg, step, sc_base)
        E_meas[y], X_DA[y] = em, xda

        rec["legA_tail_reproduction"][ys] = {
            "rows_base": int(len(base)),
            "rows_dropped_for_rt": int(len(g3) - len(base)),
            "scarce_rows_covered": int(sc_base.sum()),
            "E_meas_scarce_gw": em,
            "X_DA_scarce_gw": xda,
            "GAP_DA_gw": em - xda,
            "X_DA_frac_of_meas": (xda / em) if em else float("nan"),
            "net_sim_scarce_gw_reported": x_import(da, pi_reg, step, sc_base)
            - x_export(da, sig_reg, step, sc_base),
            "import_side_DA_scarce_gw_reported": x_import(da, pi_reg, step, sc_base),
            "E_meas_annual_gw": float((-flow).mean()) / 1000.0,
            "X_DA_annual_gw": x_export(da, sig_reg, step, np.ones(len(base), dtype=bool)),
        }

        # ---- Leg B: durations + orientation
        d_k = [float((flow < -m).mean()) for m in mids]
        c_k = [float((flow[sc_base] < -m).mean()) for m in mids]
        rec["legB_orientation"][ys] = {
            "d_k_unconditional": d_k,
            "c_k_scarce_conditional": c_k,
            "orientation_line_c1_ge_d1": bool(c_k[0] >= d_k[0]),
            "spearman_flow_vs": {
                "da": spearman(flow, da),
                "rt": spearman(flow, rt),
                "south_da": spearman(
                    base.dropna(subset=["south_da"])["South"].to_numpy(dtype=float),
                    base.dropna(subset=["south_da"])["south_da"].to_numpy(dtype=float),
                ),
                "south_rt": spearman(
                    base.dropna(subset=["south_rt"])["South"].to_numpy(dtype=float),
                    base.dropna(subset=["south_rt"])["south_rt"].to_numpy(dtype=float),
                ),
            },
        }

        # ---- Leg C: candidates
        lim = min(pi_reg) - mod.NO_WASH_EPS
        for key, col in (("B1_rt_hub", "rt"), ("B2_south_da", "south_da"), ("B3_south_rt", "south_rt")):
            sub = base.dropna(subset=[col])
            hb = sub.index.to_numpy()
            sc_sub = mask_hr[hb]
            fl = sub["South"].to_numpy(dtype=float)
            pr = sub[col].to_numpy(dtype=float)
            dk = [float((fl < -m).mean()) for m in mids]
            sig_pre = [round(float(np.quantile(pr, d)), 2) for d in dk]
            sig_arm = [min(s, round(lim, 2)) for s in sig_pre]
            clamped = [k + 1 for k, (a, b) in enumerate(zip(sig_pre, sig_arm)) if a > b]
            xb_arm = x_export(pr, sig_arm, step, sc_sub)
            xb_pre = x_export(pr, sig_pre, step, sc_sub)
            XB[key][y] = {
                "rows": int(len(sub)),
                "scarce_rows_covered": int(sc_sub.sum()),
                "d_k": dk,
                "sigma_preclamp": sig_pre,
                "sigma_armable": sig_arm,
                "no_wash_lim": round(lim, 2),
                "bands_clamped": clamped,
                "clamp_duration_distortion": [
                    {"band": k, "d_k": dk[k - 1], "cleared_dur_armable": float((pr < sig_arm[k - 1]).mean())}
                    for k in clamped
                ],
                "X_B_armable_scarce_gw": xb_arm,
                "X_B_preclamp_scarce_gw": xb_pre,
                "X_B_frac_of_meas": (xb_arm / em) if em else float("nan"),
                "net_sim_scarce_gw_reported": x_import(pr, pi_reg, step, sc_sub) - xb_arm,
                "import_side_scarce_gw_reported": x_import(pr, pi_reg, step, sc_sub),
                "X_B_annual_gw": x_export(pr, sig_arm, step, np.ones(len(sub), dtype=bool)),
                "E_meas_annual_gw_this_rowset": float((-fl).mean()) / 1000.0,
            }
            rec["legC_candidates"].setdefault(ys, {})[key] = XB[key][y]

    # ---- verdict (PREREG §4; 2025 load-bearing)
    if stop:
        rec["verdict"] = {"STOP": stop}
    else:
        em5, xda5 = E_meas[2025], X_DA[2025]
        defect = (em5 - xda5 >= DEFECT_GAP_GW) and (xda5 <= DEFECT_FRAC * em5)
        cands = {}
        for key in XB:
            xb5 = XB[key][2025]["X_B_armable_scarce_gw"]
            repair = xb5 >= REPAIR_FRAC * em5
            noninv = XB[key][2023]["X_B_armable_scarce_gw"] >= X_DA[2023] - NONINVERT_GW
            cands[key] = {
                "X_B_2025_armable": xb5,
                "repair_line": bool(repair),
                "noninversion_2023": bool(noninv),
                "clears": bool(repair and noninv),
            }
        clearing = [k for k, v in cands.items() if v["clears"]]
        if not defect:
            v25 = "V-SOUND"
            winner = None
        elif clearing:
            v25 = "V-DEFECT-BASIS"
            best = max(c["X_B_2025_armable"] for k, c in cands.items() if k in clearing)
            tied = [k for k in clearing if cands[k]["X_B_2025_armable"] == best]
            winner = "B1_rt_hub" if "B1_rt_hub" in tied else sorted(tied)[0]
        else:
            v25 = "V-DEFECT-COUPLING"
            winner = None
        rec["verdict"] = {
            "defect_line_components": {
                "E_meas_2025": em5,
                "X_DA_2025": xda5,
                "GAP_DA_2025": em5 - xda5,
                "defect_established": bool(defect),
            },
            "candidates": cands,
            "verdict_2025": v25,
            "winner": winner,
            "concurrence_2023": {
                "E_meas": E_meas[2023],
                "X_DA": X_DA[2023],
                "GAP": E_meas[2023] - X_DA[2023],
            },
            "reported_only_2024": {
                "E_meas": E_meas[2024],
                "X_DA": X_DA[2024],
                "GAP": E_meas[2024] - X_DA[2024],
                "note": "EIA-930 internal-inconsistency year (r=0.8286)",
            },
        }

    OUT.write_text(json.dumps(rec, indent=2, default=str))
    print(f"wrote {OUT}\n")
    for y in YEARS:
        ys = str(y)
        f = rec["footing"][ys]
        a = rec["legA_tail_reproduction"][ys]
        print(
            f"=== {y}: n_scarce={f['n_scarce']} rederive max|dev| ${f['rederive_max_abs_dev_usd']:.2f}"
            f" ({f['rederive_dev_where']})"
        )
        print(
            f"    A: E_meas {a['E_meas_scarce_gw']:+.3f} GW  X_DA {a['X_DA_scarce_gw']:+.3f}"
            f"  GAP {a['GAP_DA_gw']:+.3f}  (annual E {a['E_meas_annual_gw']:+.3f} X {a['X_DA_annual_gw']:+.3f})"
        )
        b = rec["legB_orientation"][ys]
        print(
            f"    B: d_1 {b['d_k_unconditional'][0]:.3f} c_1 {b['c_k_scarce_conditional'][0]:.3f}"
            f"  spearman da {b['spearman_flow_vs']['da']:+.2f} rt {b['spearman_flow_vs']['rt']:+.2f}"
            f" s_da {b['spearman_flow_vs']['south_da']:+.2f} s_rt {b['spearman_flow_vs']['south_rt']:+.2f}"
        )
        for key in ("B1_rt_hub", "B2_south_da", "B3_south_rt"):
            c = rec["legC_candidates"][ys][key]
            print(
                f"    C {key}: X arm {c['X_B_armable_scarce_gw']:+.3f} (pre {c['X_B_preclamp_scarce_gw']:+.3f})"
                f" GW  top sigma {c['sigma_armable'][0]:.2f} (pre {c['sigma_preclamp'][0]:.2f},"
                f" lim {c['no_wash_lim']:.2f})  clamped {c['bands_clamped']}"
            )
    print("\nVERDICT:", json.dumps(rec["verdict"].get("verdict_2025", rec["verdict"]), indent=1)[:400])
    if "winner" in rec["verdict"]:
        print("winner:", rec["verdict"]["winner"])


if __name__ == "__main__":
    main()
