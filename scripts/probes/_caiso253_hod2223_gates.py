"""caiso-253 phase 0 (ZERO LP): the hod 22-23 window charter's four measured gates.

Registered in ``results/calibration/PRECOMMIT-caiso253-hod2223-window-charter-2026-09-06.md``
(pushed before any of this was computed). Reads committed artifacts and
``data/raw`` only — no solve, no clean tree, no fleet rebuild.

Gates, in the PRECOMMIT's own order:

* **G-REPRO** — reproduce FINDING-caiso252 §2.2's hod-22/23 CC_REGULAR error
  (+1,619 / +1,617 MW, 2025) from the keeper's committed run payload and the
  committed bench part, on the scorer's own ``_cems_gas_hourly_fit`` basis,
  within 25 MW.
* **P-5** — the keeper's hod-22-23 net import against EIA-930 CISO, per year.
  If the model is not SHORT of import there, the object closes.
* **G-WINDOW** — the caiso-87 surplus-trigger ON share at hod 22 and hod 23,
  computed with the injector's own predicate
  (``PaloVerde < HR_DSW_CCGT x SoCal citygate weekly + remote VOM``), decided
  on 2024/2025 with 2023 reported (its 26.4 % overnight share is the
  documented rule-14 citygate misalignment). STARVED <= 10 % / RICH >= 30 % /
  else AMBIGUOUS.
* **G-WEDGE** — the caiso-93 §2 / caiso-94 §2-3 no-wedge admissibility gate
  re-run at hod 22 and hod 23 SEPARATELY (neither finding covers them):
  delivered-basis median <= +$4, wedge-consistent share <= 6 %, raw-hub
  median in [-2, +4]. All three legs, both hours, all three years, or the
  charter arms nothing.

Output: ``results/calibration/_caiso253_hod2223_gates.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso253_hod2223_gates.py
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.argv = [sys.argv[0]]  # calibration_verdict parses argv at import

from scripts.calibration_verdict import load_artifacts  # noqa: E402

KEEPER = "2026-09-05-caiso-252-b1-notrim"
BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
GAP = (22, 23)  # the window gap: the complement of the two frozen windows
OVERNIGHT = (0, 1, 2, 3, 4, 5)  # the caiso-93 window, the STARVED control
BELLY = (10, 11, 12, 13, 14)  # the caiso-94 belly, the RICH control
OUT = REPO / "results/calibration/_caiso253_hod2223_gates.json"

# Registered decision thresholds (PRECOMMIT §1).
G_WINDOW_STARVED_MAX = 0.10
G_WINDOW_RICH_MIN = 0.30
G_WEDGE_DELIVERED_MAX = 4.0
G_WEDGE_CONSISTENT_MAX = 0.06
G_WEDGE_RAWHUB_BAND = (-2.0, 4.0)


def _b64(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8)[:T].astype(float)


def _cc_regular_error(year: int, art: dict) -> np.ndarray:
    """CC_REGULAR model-minus-CEMS MW, the scorer's plant basis (no fleet fill).

    The class term of ``_cems_gas_hourly_fit``: per-plant model and CAMPD
    actual, both at the bench part's nameplate scale. The fleet-level BTM
    removal, cogen block and flat fill are class-agnostic constants in that
    construction, so a CLASS error carries none of them — which is exactly
    how FINDING-caiso252 §2.2's table was built.
    """
    ypay = art["payload"]["years"][str(year)]
    ybench = art["bench"][year]
    err = np.zeros(T)
    for code, bp in ybench["plants"].items():
        if bp.get("group") != "CC_REGULAR" or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        pp = ypay["plants"].get(str(code))
        if cap <= 0.0 or not bp.get("campd") or not pp or not pp.get("m"):
            continue
        scale = cap / 100.0
        err += (_b64(pp["m"]) - _b64(bp["campd"])) * scale
    return err


E930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    """caiso-168's non-leap 8760 mapping (Feb-29 dropped by the caller)."""
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24 + dt.hour.to_numpy()


def _e930_net_import(year: int) -> np.ndarray | None:
    """EIA-930 CISO measured NET interchange as an import (MW, model clock).

    The caiso-252 §3.1 construction verbatim (`_caiso252_c4_gas_nrmse_anatomy.
    _measured_930`): hour-ending local time shifted to hour-beginning, Feb-29
    dropped, net import = -(Total interchange).
    """
    if not E930.exists():
        return None
    d = pd.read_parquet(E930)
    lt = pd.to_datetime(d["Local time"]) - pd.Timedelta(hours=1)
    d = d.assign(lt=lt)
    d = d[
        (d["lt"].dt.year == year) & ~((d["lt"].dt.month == 2) & (d["lt"].dt.day == 29))
    ]
    h = _model_hour(d["lt"], year)
    a = np.full(T, np.nan)
    a[h] = -d["Total interchange"].to_numpy(float)
    return a


def main() -> None:
    art = load_artifacts(KEEPER)
    res: dict = {"keeper": KEEPER, "gap_hours": list(GAP), "years": {}}

    # ---- measured series, once per year -------------------------------------
    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF  # noqa: F401
    from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw
    from market_sim.data.fuel.hubs import socal_citygate_weekly_hourly
    from market_sim.model.interchange.caiso import _CAISO_IMPORT_COUPLE_HR
    from market_sim.model.interchange.spec import (
        CAISO_DSW_SURPLUS_REMOTE_VOM,
        CAISO_IMPORT_DELIVERY_BASIS,
    )

    # DISCLOSED CORRECTION (this probe's first run used the OVERNIGHT-CLEAN
    # row's own (0.0, 0.0) basis here, which is raw-hub BY DESIGN, so legs 1-2
    # were computed on the raw-hub spread rather than on delivered parity).
    # The caiso-93 §2 / caiso-94 §2 gate is defined against the SCHEDULED-import
    # delivered basis, i.e. the fossil spot rung's own basis at the same hub —
    # PALOVRDE (0.03, 4.0), the same constants _caiso252_c4_gas_nrmse_anatomy.py
    # carries as WHEEL. Leg 3 (the raw-hub discriminator) is unaffected: it was
    # always `actual - PALOVRDE`.
    loss, wheel = CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]  # (0.03, 4.0)
    # The wedge the gate tests against is the CARB unspecified-import border
    # adder the model charges every non-clean spot rung (caiso-93 §2 basis).
    from market_sim.model.interchange.import_nodes import wecc_border_carbon_adder
    from market_sim.policy.carbon import resolve_carbon_price
    from market_sim.config.scenarios import ScenarioConfig

    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    )

    for y in YEARS:
        cfg = ScenarioConfig(iso="CAISO", mode="backcast", start_year=y, end_year=y)
        carbon = float(resolve_carbon_price(cfg, y))
        wedge = float(wecc_border_carbon_adder(carbon))

        pv = measured_intertie_hub_price_raw("CAISO", y, T, "PALOVRDE")
        gas = socal_citygate_weekly_hourly(y, T)
        hr = _CAISO_IMPORT_COUPLE_HR["DSW_CCGT"]
        floor = hr * np.asarray(gas, float) + CAISO_DSW_SURPLUS_REMOTE_VOM
        on = np.isfinite(pv) & np.isfinite(floor) & (pv < floor)
        measured = np.isfinite(pv)

        # ---- G-WINDOW ------------------------------------------------------
        def on_share(hods) -> float:
            m = np.isin(HOD, hods) & measured
            return float(on[m].sum() / max(m.sum(), 1))

        gwin = {
            "hod22": on_share([22]),
            "hod23": on_share([23]),
            "gap_22_23": on_share(GAP),
            "control_overnight_0_5": on_share(OVERNIGHT),
            "control_belly_10_14": on_share(BELLY),
            "measured_hub_hours_at_gap": int((np.isin(HOD, GAP) & measured).sum()),
        }

        # ---- G-WEDGE -------------------------------------------------------
        ly = lmp[lmp["year"] == y].sort_values("hour")
        da = pd.to_numeric(ly["da"], errors="coerce").to_numpy(float)[:T]
        rt = pd.to_numeric(ly["rt"], errors="coerce").to_numpy(float)[:T]
        delivered = pv * (1.0 + loss) + wheel
        gwedge = {}
        for basis, actual in (("DA", da), ("RT", rt)):
            if actual is None or len(actual) < T:
                continue
            gwedge[basis] = {}
            for label, hods in (
                ("hod22", [22]),
                ("hod23", [23]),
                ("gap_22_23", GAP),
                ("control_overnight_0_5", OVERNIGHT),
            ):
                m = np.isin(HOD, hods) & measured & np.isfinite(actual)
                sp_del = (actual - delivered)[m]
                sp_raw = (actual - pv)[m]
                gwedge[basis][label] = {
                    "n": int(m.sum()),
                    "delivered_median": round(float(np.median(sp_del)), 2),
                    "delivered_p25": round(float(np.percentile(sp_del, 25)), 2),
                    "delivered_p75": round(float(np.percentile(sp_del, 75)), 2),
                    "wedge_consistent_share": round(
                        float((sp_del >= wedge - 2.0).mean()), 4
                    ),
                    "rawhub_median": round(float(np.median(sp_raw)), 2),
                    "above_delivered_share": round(float((sp_del > 0.0).mean()), 4),
                }
        # ---- P-5: the keeper's import at the gap vs EIA-930 -----------------
        ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        imp = (
            ch[ch["klass"] == "import"]
            .set_index("hour")["mw"]
            .reindex(range(T))
            .to_numpy(float)
        )
        e930 = _e930_net_import(y)
        p5 = {
            "model_import_by_hod_mw": [
                round(float(imp[HOD == h].mean()), 1) for h in range(24)
            ]
        }
        if e930 is not None:
            d = imp - e930
            p5.update(
                {
                    "e930_net_import_by_hod_mw": [
                        round(float(np.nanmean(e930[HOD == h])), 1) for h in range(24)
                    ],
                    "model_minus_930_by_hod_mw": [
                        round(float(np.nanmean(d[HOD == h])), 1) for h in range(24)
                    ],
                    "gap_22_23_model_minus_930_mw": round(
                        float(np.nanmean(d[np.isin(HOD, GAP)])), 1
                    ),
                    "gap_22_23_model_minus_930_twh": round(
                        float(np.nansum(d[np.isin(HOD, GAP)]) / 1e6), 3
                    ),
                    "eve_18_21_model_minus_930_twh": round(
                        float(np.nansum(d[np.isin(HOD, (18, 19, 20, 21))]) / 1e6), 3
                    ),
                    "e930_gap_22_23_twh": round(
                        float(np.nansum(e930[np.isin(HOD, GAP)]) / 1e6), 3
                    ),
                }
            )
        # ---- G-REPRO: the CC_REGULAR error at the gap ------------------------
        cc = _cc_regular_error(y, art)
        repro = {
            "cc_regular_error_by_hod_mw": [
                round(float(cc[HOD == h].mean()), 0) for h in range(24)
            ],
            "cc_regular_error_gap_mw": round(float(cc[np.isin(HOD, GAP)].mean()), 0),
        }
        res["years"][y] = {
            "carbon_price": round(carbon, 2),
            "border_wedge": round(wedge, 2),
            "G_REPRO": repro,
            "P5_import": p5,
            "G_WINDOW": gwin,
            "G_WEDGE": gwedge,
        }

    # ---- verdicts ----------------------------------------------------------
    dec_years = (2024, 2025)
    on_vals = [
        res["years"][y]["G_WINDOW"][k] for y in dec_years for k in ("hod22", "hod23")
    ]
    if max(on_vals) <= G_WINDOW_STARVED_MAX:
        gwin_verdict = "STARVED"
    elif max(on_vals) >= G_WINDOW_RICH_MIN:
        gwin_verdict = "RICH"
    else:
        gwin_verdict = "AMBIGUOUS"

    wedge_fail = []
    for y in YEARS:
        for basis, blk in res["years"][y]["G_WEDGE"].items():
            for label in ("hod22", "hod23"):
                c = blk.get(label)
                if c is None:
                    continue
                if c["delivered_median"] > G_WEDGE_DELIVERED_MAX:
                    wedge_fail.append(
                        f"{y}/{basis}/{label}: delivered median {c['delivered_median']}"
                    )
                if c["wedge_consistent_share"] > G_WEDGE_CONSISTENT_MAX:
                    wedge_fail.append(
                        f"{y}/{basis}/{label}: wedge share {c['wedge_consistent_share']}"
                    )
                if not (
                    G_WEDGE_RAWHUB_BAND[0]
                    <= c["rawhub_median"]
                    <= G_WEDGE_RAWHUB_BAND[1]
                ):
                    wedge_fail.append(
                        f"{y}/{basis}/{label}: raw-hub median {c['rawhub_median']}"
                    )

    res["verdicts"] = {
        "G_WINDOW": gwin_verdict,
        "G_WINDOW_decided_on": list(dec_years),
        "G_WINDOW_max_on_share": round(max(on_vals), 4),
        "G_WEDGE": "PASS" if not wedge_fail else "FAIL",
        "G_WEDGE_failures": wedge_fail,
        "P5": {
            y: res["years"][y]["P5_import"].get("gap_22_23_model_minus_930_mw")
            for y in YEARS
        },
    }
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")

    # ---- report ------------------------------------------------------------
    for y in YEARS:
        r = res["years"][y]
        print(
            f"\n===== {y} (carbon {r['carbon_price']}, border wedge {r['border_wedge']}) ====="
        )
        print("  CC_REGULAR err by hod:", r["G_REPRO"]["cc_regular_error_by_hod_mw"])
        print(
            f"  CC_REGULAR err at 22-23: {r['G_REPRO']['cc_regular_error_gap_mw']} MW"
        )
        w = r["G_WINDOW"]
        print(
            f"  G-WINDOW caiso-87 ON share: hod22 {w['hod22']:.3f} hod23 {w['hod23']:.3f} "
            f"| controls: overnight 0-5 {w['control_overnight_0_5']:.3f}, belly 10-14 {w['control_belly_10_14']:.3f}"
        )
        for basis, blk in r["G_WEDGE"].items():
            for label in ("hod22", "hod23", "control_overnight_0_5"):
                c = blk.get(label)
                if c:
                    print(
                        f"  G-WEDGE {basis} {label:22s} n={c['n']:5d} delivered med {c['delivered_median']:+7.2f} "
                        f"| wedge-consistent {c['wedge_consistent_share']:.3f} | raw-hub med {c['rawhub_median']:+7.2f}"
                    )
        p = r["P5_import"]
        print("  model import by hod:", p["model_import_by_hod_mw"])
        if "model_minus_930_by_hod_mw" in p:
            print("  model-930 by hod:   ", p["model_minus_930_by_hod_mw"])
            print(
                f"  P-5 at 22-23: {p['gap_22_23_model_minus_930_mw']} MW ({p['gap_22_23_model_minus_930_twh']} TWh); "
                f"18-21 check {p['eve_18_21_model_minus_930_twh']} TWh"
            )
    print("\n===== VERDICTS =====")
    print(json.dumps(res["verdicts"], indent=1))


if __name__ == "__main__":
    main()
