"""caiso-242 — the CT_PEAKER anatomy: which of price, availability or absence binds.

NO LP, NO SOLVE, NOTHING ARMED. Reads the committed keeper bundle
(``caiso241_b1_ctpeaker_committed``) and rebuilds its fleet ONCE per year with
``run_year(fleet_only=True)`` at the recorded config — no flag delta — so the
question the caiso-241 FINDING §7 left open is answered by measurement rather
than by intuition:

  (a) are the ECON/PEAK bands the binding price, and is the reformed offer
      curve NON-MONOTONE (peak cheaper than econ) as the caiso-242 charter
      suspects;
  (b) is AVAILABILITY the binding envelope; or
  (c) is the class priced correctly and something else serves the ramp.

Everything written to ``results/calibration/_caiso244_ctpeaker_anatomy_onrecipe.json``
(re-measured ON-RECIPE at caiso-244 through ``replay_keeper.run_year_kwargs``; the
``_caiso242_ctpeaker_anatomy.json`` artifact is frozen as the historical record —
its keeper-relative numbers were measured on a lookalike recipe).

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso242_ctpeaker_anatomy.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# caiso-244: re-measured ON-RECIPE against the CURRENT keeper. The caiso-242
# artifact (``_caiso242_*.json``, measured on caiso241 through the by-name
# pattern) is frozen as the historical record and never regenerated.
BUNDLE = REPO / "results/calibration/caiso243_b1_f923_fallback_guard"
YEARS = (2023, 2024, 2025)
HOURS = 8760
GROUP = "CT_PEAKER"
OUT = REPO / "results/calibration/_caiso244_ctpeaker_anatomy_onrecipe.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def _band(unit_id: str) -> str:
    """Return the LP tranche suffix (the last underscore token)."""
    return str(unit_id).rsplit("_", 1)[-1]


def rebuild(year: int) -> dict:
    """Rebuild the keeper fleet as recorded (no LP, no flag delta)."""
    from run_calibration import run_year
    from replay_keeper import run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    # ON-RECIPE (caiso-244 repair of the caiso-243 §7.3 instrument defect): the
    # strict, remapping meta -> run_year reconstruction. The by-parameter-NAME
    # filter this replaced dropped ``coal_prb_sigmoid_overrides`` ->
    # ``prb_overrides`` (36 CAISO structural flags, incl. the daily citygate
    # spot level) and rebuilt a lookalike recipe; every keeper-relative number
    # this probe published at caiso-242 is VOID until re-measured here.
    kwargs = run_year_kwargs(meta)
    CENSUS._clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    gens = st.get("fleet") or []
    markup = np.array(
        [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in gens], dtype=float
    )
    group = np.array([str(getattr(g, "plant_group", "")) for g in gens])
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "hr": np.asarray(fa.heat_rate, dtype=float),
        "mc": mc,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": np.asarray(fa.availability, dtype=float),
        "markup": markup,
        "group": group,
        "zone_idx": np.asarray(fa.zone_idx, dtype=int),
        "zones": list(st.get("zones") or []),
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-244 (on-recipe re-run of the caiso-242 probe)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-04-caiso-243-b1-f923",
            "note": "no LP, no flag delta; fleet rebuilt at the recorded config",
        },
        "years": {},
    }
    for year in YEARS:
        f = rebuild(year)
        sel = f["group"] == GROUP
        bands = np.array([_band(u) for u in f["uid"]])
        avail_mw = f["pmax"][:, None] * f["avail"]  # (n_gen, T)

        # --- per-band anatomy -------------------------------------------------
        per_band: dict = {}
        for b in sorted(set(bands[sel])):
            m = sel & (bands == b)
            cap = float(f["pmax"][m].sum())
            am = avail_mw[m].sum(axis=0)
            mc_row = f["mc"][m]
            w = f["pmax"][m]
            per_band[b] = {
                "n_tranches": int(m.sum()),
                "pmax_mw": round(cap, 2),
                "avail_mw_mean": round(float(am.mean()), 2),
                "avail_mw_p99": round(float(np.quantile(am, 0.99)), 2),
                "avail_mw_max": round(float(am.max()), 2),
                "mc_capwt_mean": round(
                    float((mc_row.mean(axis=1) * w).sum() / max(w.sum(), 1e-9)), 4
                ),
                "mc_min": round(float(mc_row.mean(axis=1).min()), 4),
                "mc_max": round(float(mc_row.mean(axis=1).max()), 4),
                "markup_hr_capwt": round(
                    float((f["markup"][m] * w).sum() / max(w.sum(), 1e-9)), 4
                ),
                "hr_capwt": round(
                    float((f["hr"][m] * w).sum() / max(w.sum(), 1e-9)), 4
                ),
            }

        # --- class envelope ---------------------------------------------------
        cls_avail = avail_mw[sel].sum(axis=0)
        cls_cap = float(f["pmax"][sel].sum())

        # --- dispatch from the committed sidecar ------------------------------
        d = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
        d = d[(d["pass"] == "P1") & (d["klass"] == GROUP)]
        disp = d.pivot_table(
            index="hour", columns="band", values="mw", aggfunc="sum"
        ).reindex(range(HOURS)).fillna(0.0)
        cls_disp = disp.sum(axis=1).to_numpy()

        # --- prices -----------------------------------------------------------
        s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        s = s[s["pass"] == "P1"]
        price = s.pivot_table(index="hour", columns="zone", values="price")
        # load-weighted system price, the class's effective clearing reference
        dem = s.pivot_table(index="hour", columns="zone", values="demand")
        sysprice = (price * dem).sum(axis=1) / dem.sum(axis=1)
        sysprice = sysprice.reindex(range(HOURS)).to_numpy()

        # cheapest available CT_PEAKER offer per hour (capacity-weighted floor:
        # the minimum mc over tranches with any availability)
        mcs = f["mc"][sel]
        av = f["avail"][sel]
        mc_masked = np.where(av > 1e-9, mcs, np.inf)
        cheapest = mc_masked.min(axis=0)

        # --- the three routes, measured --------------------------------------
        headroom = cls_avail - cls_disp
        out["years"][year] = {
            "class_pmax_mw": round(cls_cap, 2),
            "class_avail_mw_mean": round(float(cls_avail.mean()), 2),
            "class_avail_mw_p05": round(float(np.quantile(cls_avail, 0.05)), 2),
            "class_avail_mw_max": round(float(cls_avail.max()), 2),
            "class_dispatch_twh": round(float(cls_disp.sum() / 1e6), 4),
            "class_dispatch_max_mw": round(float(cls_disp.max()), 2),
            "hours_dispatch_gt0": int((cls_disp > 1e-6).sum()),
            "hours_headroom_lt_1pct_cap": int((headroom < 0.01 * cls_cap).sum()),
            "hours_cheapest_offer_gt_price": int((cheapest > sysprice).sum()),
            "hours_cheapest_offer_le_price": int((cheapest <= sysprice).sum()),
            "cheapest_offer_capwt_mean": round(
                float(cheapest[np.isfinite(cheapest)].mean()), 4
            ),
            "sysprice_mean": round(float(np.nanmean(sysprice)), 4),
            "median_gap_cheapest_minus_price": round(
                float(np.nanmedian(cheapest - sysprice)), 4
            ),
            "per_band": per_band,
        }
        print(f"--- {year} ---")
        print(json.dumps(out["years"][year], indent=2))
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
