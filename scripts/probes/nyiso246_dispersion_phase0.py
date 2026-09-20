"""nyiso-246 phase 0 — the model side of the conditional-dispersion object (ZERO LP).

Reads the committed keeper's cached fleet arrays (``_nyiso245_cache``) and the
frozen PRECOMMIT state geometry. Computes, in order:

* **G0 anatomy** — why the TIGHT conjunction is narrow: the marginal counts of
  each coordinate and their overlap, per year.
* **Q_mod** — the model's own conditional response over the affected tranches,
  built by the IDENTICAL construction the book side uses (per-hour
  normalization by ``G(t)``, capacity-weighted step-function quantiles on the
  frozen 199-point grid).
* **G1 reach anatomy** — the affected-tranche capacity and its rank spread.
* **G2** — whether any affected row is also another armed writer's base row.

Every number here is DIAGNOSTIC: ``G0`` already stopped the mechanism
(PRECOMMIT section 3), so nothing computed here can revive it and no geometry
variant is tried.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso246_dispersion_phase0.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
YEARS = (2022, 2023, 2024, 2025)
HOURS = 8760
GRID = np.round(np.arange(0.005, 0.9951, 0.005), 4)

#: The family's selector, adopted unchanged minus COAL (NYISO has none).
_BAND = re.compile(r"^(econ\w*|peak\w*)$")
_CLASS = re.compile(r"^(CC_|CT_|ST_GAS)")


def weighted_quantiles(v: np.ndarray, w: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Step-function weighted quantiles — the family's estimator."""
    order = np.argsort(v, kind="stable")
    vs, cum = v[order], np.cumsum(w[order])
    cum = cum / cum[-1]
    return vs[np.clip(np.searchsorted(cum, grid), 0, vs.size - 1)]


def affected(unit_ids: np.ndarray, plant_group: np.ndarray) -> np.ndarray:
    """Row indices of the affected econ/peak tranches of the gas classes."""
    band = np.array([str(u).rpartition("_")[2] for u in unit_ids])
    return np.nonzero(
        np.array([bool(_BAND.match(b)) for b in band])
        & np.array([bool(_CLASS.match(str(c))) for c in plant_group])
    )[0]


def main() -> None:
    from scripts.data.derive_nyiso_offer_level_dispersion import state_windows

    tight, ordinary, meta = state_windows()
    out: dict = {"session": "nyiso-246", "state_meta": meta, "years": {}}

    pooled_delta: list[np.ndarray] = []
    pooled_w: list[np.ndarray] = []

    for year in YEARS:
        z = np.load(CACHE / f"{year}.npz", allow_pickle=False)
        gas = np.load(CACHE / f"gas_{year}.npy").astype(float)
        uid, grp = z["unit_ids"], z["plant_group"]
        pmax, mc = z["pmax"].astype(float), z["mc_base"].astype(float)
        av = z["availability"].astype(float)
        aff = affected(uid, grp)
        t, o = tight[year], ordinary[year]

        # G0 anatomy: the two coordinates' marginals and their overlap.
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        import pandas as pd

        df = _eia_hourly_frame_filled("NYIS", year)
        nl = (
            pd.to_numeric(df["Demand"], errors="coerce")
            - pd.to_numeric(df.get("NG: WND", 0.0), errors="coerce").fillna(0.0)
            - pd.to_numeric(df.get("NG: SUN", 0.0), errors="coerce").fillna(0.0)
        ).interpolate().bfill().ffill().to_numpy(float)
        gas_hi = gas >= np.quantile(gas, 0.90)
        load_hi = nl >= np.quantile(nl, 0.90)
        month = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h").month.to_numpy()

        rec: dict = {
            "gas_ge_p90_hours": int(gas_hi.sum()),
            "load_ge_p90_hours": int(load_hi.sum()),
            "overlap_hours": int((gas_hi & load_hi).sum()),
            "overlap_if_independent": round(float(gas_hi.mean() * load_hi.mean() * HOURS), 1),
            "gas_hi_winter_share": round(float(np.isin(month[gas_hi], (1, 2, 12)).mean()), 3),
            "load_hi_summer_share": round(float(np.isin(month[load_hi], (6, 7, 8)).mean()), 3),
            "tight_hours": int(t.sum()),
            "ordinary_hours": int(o.sum()),
            "affected_tranches": int(aff.size),
            "affected_pmax_mw": round(float(pmax[aff].sum()), 1),
        }

        if t.sum() and o.sum() and aff.size:
            # Q_mod, the IDENTICAL construction the book side uses.
            m_t = (mc[np.ix_(aff, np.nonzero(t)[0])] / gas[t][None, :]).mean(axis=1)
            m_o = (mc[np.ix_(aff, np.nonzero(o)[0])] / gas[o][None, :]).mean(axis=1)
            d = m_t - m_o
            w = pmax[aff]
            pooled_delta.append(d)
            pooled_w.append(w)
            q = weighted_quantiles(d, w, np.array([0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]))
            rec["Q_mod_mmbtu_per_mwh"] = {
                f"p{int(p * 100)}": round(float(v), 4)
                for p, v in zip((0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99), q)
            }
            # The same object in $/MWh at the mean TIGHT-hour gas, so it is
            # directly comparable to nyiso-245 section 5.2's committed table.
            gbar = float(gas[t].mean())
            rec["mean_tight_gas_usd_per_mmbtu"] = round(gbar, 4)
            rec["Q_mod_usd_per_mwh"] = {
                f"p{int(p * 100)}": round(float(v * gbar), 3)
                for p, v in zip((0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99), q)
            }
            # D1: rank spread of the affected stack on its TIGHT-hour mean mc.
            mc_t = mc[np.ix_(aff, np.nonzero(t)[0])].mean(axis=1)
            order = np.argsort(mc_t, kind="stable")
            cum = np.cumsum(w[order])
            mid = (cum - 0.5 * w[order]) / float(cum[-1])
            r_g = np.empty_like(mid)
            r_g[order] = mid
            rec["D1_rank_spread"] = round(float(r_g.max() - r_g.min()), 4)
            # Idle-below-$300 affected capacity in the median TIGHT hour.
            th = np.nonzero(t)[0]
            capt = pmax[aff][:, None] * av[np.ix_(aff, th)]
            cheap = mc[np.ix_(aff, th)] < 300.0
            rec["affected_available_below_300_median_tight_mw"] = round(
                float(np.median((capt * cheap).sum(axis=0))), 1
            )
        out["years"][str(year)] = rec

    if pooled_delta:
        d = np.concatenate(pooled_delta)
        w = np.concatenate(pooled_w)
        q = weighted_quantiles(d, w, GRID)
        out["Q_mod_pooled_mmbtu_per_mwh"] = [round(float(x), 6) for x in q]
        out["Q_mod_pooled_summary"] = {
            f"p{int(p * 100)}": round(float(np.interp(p, GRID, q)), 4)
            for p in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
        }

    dest = REPO / "results" / "calibration" / "_nyiso246_dispersion_phase0.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out["years"], indent=1))
    print("Q_mod pooled:", json.dumps(out.get("Q_mod_pooled_summary", {})))
    print("wrote", dest)


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
