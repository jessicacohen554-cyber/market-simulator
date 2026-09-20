"""nyiso-247 phase 0 — the ZERO-LP gates of the fuel-invariance-limb disarm.

Evaluates, against ``docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md``
§3 and nothing else:

* **G-A** — the identity: the arm's ``mc`` differs from the keeper's by exactly
  ``- offer_markup_hr x (anchor - fuel)``, verified by the per-row slope of
  ``mc`` against delivered fuel moving by exactly ``offer_markup_hr`` (armed =
  ``phys x base_HR``, disarmed = ``mult x base_HR``), and by zero movement on
  every row whose markup clips to 0.
* **G-B** — the sign guard: ``Q_mod`` under both legs on the family's frozen
  199-point grid against the committed book vector, with legs S1 (direction),
  S2 (no overshoot above p50) and S3 (net closure over the full grid).
* **G-E** — level neutrality, per zone per year, REPORTED at full magnitude.
* **G-F** — the rule 19 census of the rows the disarm touches.

Reuses ``nyiso246_dispersion_phase0``'s own ``affected`` selector, its
``weighted_quantiles`` estimator and ``derive_nyiso_offer_level_dispersion``'s
``state_windows`` unchanged — one construction, one identification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.probes.nyiso246_dispersion_phase0 import (  # noqa: E402
    GRID,
    affected,
    weighted_quantiles,
)

CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
ART = REPO / "data" / "raw" / "_validation-source" / "nyiso_offer_level_dispersion.json"
YEARS = (2022, 2023, 2024, 2025)
ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "Long_Island", "NYC")


def zone_of(unit_id: str) -> str:
    """The LP row's zone token (`<CLASS>_<ZONE>_p<plant>_<band>`)."""
    for z in ZONES:
        if f"_{z}_" in unit_id:
            return z
    return "?"


def slopes(mc: np.ndarray, fuel: np.ndarray) -> np.ndarray:
    """Per-row d(mc)/d(fuel) over the year — cov/var, vectorized (rule 2)."""
    fm = fuel - fuel.mean(axis=1, keepdims=True)
    var = (fm * fm).sum(axis=1)
    cov = ((mc - mc.mean(axis=1, keepdims=True)) * fm).sum(axis=1)
    return np.where(var > 0, cov / np.where(var > 0, var, 1.0), np.nan)


def main() -> None:
    from scripts.data.derive_nyiso_offer_level_dispersion import state_windows

    tight, ordinary, _meta = state_windows()
    book = np.asarray(
        json.loads(ART.read_text())["pooled"]["quantiles_mmbtu_per_mwh"], dtype=float
    )
    out: dict = {"session": "nyiso-247", "precommit": "40316764", "years": {}}
    pool: dict[str, list[np.ndarray]] = {"k": [], "a": [], "w": []}

    for year in YEARS:
        z = np.load(CACHE / f"{year}.npz", allow_pickle=False)
        gas = np.load(CACHE / f"gas_{year}.npy").astype(float)
        uid, grp = z["unit_ids"], z["plant_group"]
        pmax = z["pmax"].astype(float)
        mc_k = z["mc_base"].astype(float)
        fuel = z["fuel_prices"].astype(float)
        mk = z["gen_markup_hr"].astype(float)
        anc = z["gen_margin_anchor"].astype(float)

        term = mk[:, None] * (anc[:, None] - fuel)  # what the keeper added
        mc_a = mc_k - term  # the disarm
        armed = mk > 0.0

        # ---- G-A: the identity ------------------------------------------
        s_k, s_a = slopes(mc_k, fuel), slopes(mc_a, fuel)
        d_slope = (s_a - s_k)[armed]
        rec = {
            "GA_rows_armed": int(armed.sum()),
            "GA_armed_pmax_mw": round(float(pmax[armed].sum()), 1),
            "GA_max_abs_slope_err_mmbtu_per_mwh": round(
                float(np.nanmax(np.abs(d_slope - mk[armed]))), 8
            ),
            "GA_max_abs_mc_move_on_unarmed_usd": round(
                float(np.abs(term[~armed]).max()) if (~armed).any() else 0.0, 12
            ),
            "GA_keeper_slope_over_base_is_phys": round(float(np.nanmedian(s_k[armed])), 4),
            "GA_arm_slope_over_base_is_mult": round(float(np.nanmedian(s_a[armed])), 4),
        }

        # ---- G-E: level neutrality, per zone, ALL 8760 hours -------------
        zon = np.array([zone_of(str(u)) for u in uid])
        ge: dict[str, float] = {}
        for zz in ZONES:
            sel = armed & (zon == zz)
            if not sel.any():
                continue
            w = pmax[sel]
            ge[zz] = round(
                float((term[sel].mean(axis=1) * w).sum() / w.sum()), 4
            )
        rec["GE_annual_mean_removed_term_usd_per_mwh_by_zone"] = ge
        w_all = pmax[armed]
        rec["GE_annual_mean_removed_term_usd_per_mwh_iso"] = round(
            float((term[armed].mean(axis=1) * w_all).sum() / w_all.sum()), 4
        )

        # ---- Q_mod, nyiso-246's IDENTICAL construction -------------------
        aff = affected(uid, grp)
        t, o = tight[year], ordinary[year]
        ti, oi = np.nonzero(t)[0], np.nonzero(o)[0]
        for tag, mcx in (("k", mc_k), ("a", mc_a)):
            d = (mcx[np.ix_(aff, ti)] / gas[t][None, :]).mean(axis=1) - (
                mcx[np.ix_(aff, oi)] / gas[o][None, :]
            ).mean(axis=1)
            pool[tag].append(d)
        pool["w"].append(pmax[aff])

        # ---- G-F: the census of rows the disarm touches ------------------
        band = np.array([str(u).rpartition("_")[2] for u in uid])
        rec["GF_armed_rows_by_class_band"] = {
            f"{c}:{b}": int(n)
            for (c, b), n in sorted(
                {
                    (str(grp[i]), str(band[i])): int(
                        ((grp == grp[i]) & (band == band[i]) & armed).sum()
                    )
                    for i in np.nonzero(armed)[0]
                }.items()
            )
        }
        rec["GF_armed_pmax_by_class"] = {
            str(c): round(float(pmax[armed & (grp == c)].sum()), 1)
            for c in sorted(set(grp[armed].tolist()))
        }
        out["years"][str(year)] = rec

    # ---- G-B: the sign guard, pooled on the frozen 199-point grid --------
    w = np.concatenate(pool["w"])
    qk = weighted_quantiles(np.concatenate(pool["k"]), w, GRID)
    qa = weighted_quantiles(np.concatenate(pool["a"]), w, GRID)
    idx = {p: int(np.argmin(np.abs(GRID - p))) for p in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)}
    up = GRID >= 0.50
    s1 = {f"p{int(p*100)}": (round(float(qk[i]), 4), round(float(qa[i]), 4), round(float(book[i]), 4))
          for p, i in idx.items()}
    over = qa[up] - book[up]
    mad_k = float(np.abs(qk - book).mean())
    mad_a = float(np.abs(qa - book).mean())
    out["GB"] = {
        "keeper_arm_book_by_rank": s1,
        "S1_direction_pass": bool(all(qa[idx[p]] > qk[idx[p]] for p in (0.50, 0.75, 0.90))),
        "S2_no_overshoot_above_p50_pass": bool((over <= 0).all()),
        "S2_max_positive_excursion_above_p50": round(float(over.max()), 4),
        "S2_first_overshoot_rank": (
            None if (over <= 0).all() else float(GRID[up][int(np.argmax(over > 0))])
        ),
        "S3_rank_mean_abs_dev_keeper": round(mad_k, 4),
        "S3_rank_mean_abs_dev_arm": round(mad_a, 4),
        "S3_net_closure_pass": bool(mad_a < mad_k),
        "reported_below_p50_mean_abs_dev": {
            "keeper": round(float(np.abs(qk - book)[~up].mean()), 4),
            "arm": round(float(np.abs(qa - book)[~up].mean()), 4),
        },
    }
    dst = REPO / "results" / "calibration" / "_nyiso247_fuelinv_phase0.json"
    dst.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["GB"], indent=1))
    for y, r in out["years"].items():
        print(y, "G-A slope err", r["GA_max_abs_slope_err_mmbtu_per_mwh"],
              "| unarmed move", r["GA_max_abs_mc_move_on_unarmed_usd"],
              "| G-E iso", r["GE_annual_mean_removed_term_usd_per_mwh_iso"],
              "| G-E zones", r["GE_annual_mean_removed_term_usd_per_mwh_by_zone"])
    print("wrote", dst)


if __name__ == "__main__":
    main()
