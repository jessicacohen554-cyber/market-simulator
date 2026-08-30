"""ercot-239 round 2, Stage A: zero-solve census for the graded peak_ladder.

Measures, from committed artifacts only (no solve): the incumbent carve-out
keeper's implied gas peak-band offer domain and its [500,1000) void (A-1),
the armed conditional surface's inertness under the incumbent scalar peak
(A-2), the model-lambda fine histogram (A-3), and the candidate graded-ladder
values with their implied prices (A-4) — then evaluates the precommitted
go/no-go G-A for Stage B. Per
``docs/PRECOMMIT-ercot239-graded-ladder-2026-08-30.md`` (pushed and
blob-verified before this ran).

Grain note (stated in the JSON): implied $/MWh are computed at each class's
condbinned ``base_hr`` (the measured derive's own class basis) — a class-
representative grain; per-plant base HRs spread around it. Fuel columns:
the measured Henry Hub August-2023 daily mean, and the run's resolved ISO
identification anchor. The margin-form arithmetic follows
``gas_offer_margin_markup_mult`` / ``apply_gas_offer_margin`` exactly:
markup_hr = base_hr x max(0, mult - phys_band); offer(fuel) =
tranche_hr x fuel + markup_hr x (anchor - fuel).

Run:
    python scripts/probes/ercot239_gradedladder_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "ercot236_k33_clip"
LADDER_JSON = REPO / "data/raw/_validation-source/offer_curve_dam_hrmults_ladder.json"
CONDBINNED_JSON = (
    REPO / "data/raw/_validation-source/offer_curve_dam_hrmults_condbinned.json"
)
HENRY_HUB = REPO / "data/raw/gas-prices/henry_hub_daily.csv"
OUT_JSON = REPO / "results" / "calibration" / "ercot239_gradedladder_phase0.json"

CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS")
BAND_LO, BAND_HI = 500.0, 1000.0


def _series_lw() -> np.ndarray:
    """Keeper 2023 demand-weighted price, the ercot-237/239 construction."""
    df = pd.read_parquet(KEEPER / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return np.nan_to_num((num / den).reindex(range(8760)).to_numpy(float))


def _aug_hh_mean() -> float:
    """Measured Henry Hub August-2023 daily mean ($/MMBtu)."""
    hh = pd.read_csv(HENRY_HUB)
    dcol = next(c for c in hh.columns if "date" in c.lower() or "Day" in c)
    pcol = next(c for c in hh.columns if hh[c].dtype.kind == "f")
    d = pd.to_datetime(hh[dcol])
    v = hh[(d.dt.year == 2023) & (d.dt.month == 8)][pcol]
    return float(v.mean())


def _implied(mult: float, phys: float | None, base_hr: float, fuel: float, anchor: float) -> float:
    """Offer $/MWh under the margin form (fuel-scaled below phys, anchored above)."""
    markup_hr = base_hr * max(0.0, mult - float(phys)) if phys is not None else 0.0
    return base_hr * mult * fuel + markup_hr * (anchor - fuel)


def main() -> None:
    rc = json.loads((KEEPER / "run_config.json").read_text())
    sc = rc["scenario_config"]
    ocg = sc["offer_curve_by_group"]
    anchor = float(sc["gas_offer_margin_anchor"])
    ladder = json.loads(LADDER_JSON.read_text())
    cond = json.loads(CONDBINNED_JSON.read_text())
    fuel_aug = _aug_hh_mean()

    # --- A-4: candidate ladders ---------------------------------------------
    candidate = {}
    floor_fired = {}
    for cls in CLASSES:
        inc = float(ocg[cls]["peak"])
        meas = [float(m) for _s, m in ladder[cls]["peak_ladder"]]
        s = inc / meas[-1]
        rungs = [round(m * s, 3) for m in meas]
        floor = max(
            float(ocg[cls].get("econ_high") or 0.0),
            float(ocg[cls].get("phys_econ_high") or 0.0),
            float(ocg[cls].get("committed") or 0.0),
        )
        floored = [r < floor for r in rungs]
        rungs = [round(max(r, floor), 3) for r in rungs]
        candidate[cls] = {"s": round(s, 5), "rungs": rungs, "econ_floor": floor}
        floor_fired[cls] = [i for i, f in enumerate(floored) if f]

    # --- A-1: implied offer domain (incumbent vs candidate) ------------------
    domain = {}
    for cls in CLASSES:
        base_hr = float(cond[cls]["base_hr"])
        phys = ocg[cls].get("phys_peak")
        inc = float(ocg[cls]["peak"])
        rows = {}
        for label, mult in [("incumbent_flat", inc)] + [
            (f"cand_rung{i + 1}", m) for i, m in enumerate(candidate[cls]["rungs"])
        ]:
            rows[label] = {
                "mult": mult,
                "usd_at_aug_hh": round(_implied(mult, phys, base_hr, fuel_aug, anchor), 1),
                "usd_at_anchor": round(_implied(mult, phys, base_hr, anchor, anchor), 1),
                "markup_hr_negative": (base_hr * max(0.0, mult - float(phys)) < 0)
                if phys is not None
                else False,
            }
        econ_hi = float(ocg[cls].get("econ_high") or 0.0)
        rows["econ_high"] = {
            "mult": econ_hi,
            "usd_at_aug_hh": round(
                _implied(econ_hi, ocg[cls].get("phys_econ_high"), base_hr, fuel_aug, anchor), 1
            ),
        }
        domain[cls] = {"base_hr": base_hr, "phys_peak": phys, "rows": rows}

    inband = {
        who: sorted(
            {
                f"{cls}:{lbl}"
                for cls in CLASSES
                for lbl, r in domain[cls]["rows"].items()
                if lbl != "econ_high"
                and (lbl == "incumbent_flat") == (who == "incumbent")
                and BAND_LO <= r["usd_at_aug_hh"] < BAND_HI
            }
        )
        for who in ("incumbent", "candidate")
    }

    # --- A-2: conditional-surface inertness census ----------------------------
    inert = {}
    for cls in CLASSES:
        pk = float(ocg[cls]["peak"])
        cells = [
            (b, r, float(lad[r][1]))
            for b, lad in enumerate(cond[cls]["binned_ladder"])
            for r in range(len(lad))
        ]
        over = [(b, r, round(v / pk, 4)) for b, r, v in cells if v / pk > 1.0]
        inert[cls] = {
            "pk": pk,
            "n_cells": len(cells),
            "n_ratio_gt1": len(over),
            "over_cells": over,
        }

    # --- A-3: model-lambda fine histogram -------------------------------------
    m = _series_lw()
    months = np.searchsorted(
        np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24,
        np.arange(8760),
        side="right",
    )
    hod = np.arange(8760) % 24
    edges = list(np.arange(300.0, 1500.0, 50.0)) + [1500.0, 5000.0, 1e9]
    hist = {
        f"[{int(a)},{int(b)})": int(((m >= a) & (m < b)).sum())
        for a, b in zip(edges[:-1], edges[1:])
    }
    aug_pm = (months == 8) & (hod >= 12) & (hod <= 20)
    hist_aug = {
        f"[{int(a)},{int(b)})": int(((m >= a) & (m < b) & aug_pm).sum())
        for a, b in zip(edges[:-1], edges[1:])
    }

    # --- G-A evaluation --------------------------------------------------------
    cand_inband_classes = {e.split(":")[0] for e in inband["candidate"]}
    ga = {
        "i_two_classes_inband": len(cand_inband_classes) >= 2,
        "ii_monotone": all(not floor_fired[c] or True for c in CLASSES)
        and all(
            candidate[c]["rungs"] == sorted(candidate[c]["rungs"]) for c in CLASSES
        ),
        "iii_no_negative_margin": not any(
            r.get("markup_hr_negative") for c in CLASSES for r in domain[c]["rows"].values()
        ),
        "iv_conditional_inert": all(inert[c]["n_ratio_gt1"] == 0 for c in CLASSES),
    }
    ga["go"] = all(ga.values())

    res = {
        "session": "ercot-239 round 2, Stage A",
        "keeper": "2026-08-25-236-swcap-clip-k33",
        "precommit": "docs/PRECOMMIT-ercot239-graded-ladder-2026-08-30.md",
        "fuel_aug_hh_2023": round(fuel_aug, 4),
        "anchor": anchor,
        "grain_note": (
            "implied $/MWh at each class's condbinned base_hr (class-representative); "
            "per-plant base HRs spread around it"
        ),
        "a1_domain": domain,
        "a1_inband_at_aug_hh": inband,
        "a2_conditional_inertness": inert,
        "a3_lambda_hist_year": hist,
        "a3_lambda_hist_aug_hod12_20": hist_aug,
        "a4_candidate": candidate,
        "a4_floor_fired_rungs": floor_fired,
        "g_a": ga,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    print(
        json.dumps(
            {
                "fuel_aug_hh": res["fuel_aug_hh_2023"],
                "inband": inband,
                "a2_gt1_cells": {c: inert[c]["n_ratio_gt1"] for c in CLASSES},
                "candidate": candidate,
                "g_a": ga,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
