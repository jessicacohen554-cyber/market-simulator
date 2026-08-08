"""miso-143 gate G-A0 — the FOOTING STOP GATE (PREREG P1, P2, P9).

No solve, no keeper replay.  Rebuilds the model's own MISO offer stack through
``run_year(fleet_only=True)`` (see ``_miso143_stack``) and asks the only
question that licenses everything downstream: **does the stack, cleared
merit-order against the model's own hourly thermal requirement, reproduce the
keeper's own committed P1 clearing price?**

A stack that cannot reproduce the keeper's prices is not an instrument for
**levels**.  The PREREG fixed the bar in advance and pre-committed a landing
place for failure (BRANCH-INSTRUMENT-FAIL: report GAPS only, the gain as a
bound and never a point), so this gate cannot be talked past after the fact.

**P1 (STOP GATE)** — 2025 JJA h12-17: median |Δ| ≤ **$4.00**/MWh AND Pearson
*r* ≥ **0.85**.  Point prediction: median |Δ| $2.50, *r* 0.93.

**P2** — the merit-order clearing tranche is **coal** in **30-55 %** of those
hours (an INDEPENDENT cross-check on miso-142's OLS 43.6 % marginal-coal share,
not an inheritance of it — TRAP 2).  Falsified below 20 % or above 70 %.

**P9** — the rebuilt window coal MW reproduces the keeper's own sidecar coal MW
to within **1 %** (TRAP 4/5 self-check; > 1 % stops the session).

Both bracket endpoints are reported (``lo`` = pure P0 basis, ``hi`` = P0 + the
v3 measured-horizon startup-markup floor on gas), because the markup's class
incidence -- zero on coal, positive on gas -- is not neutral to this lane's
question.  See ``_miso143_stack`` for the bracket's construction and its
direction of honesty.

Usage::

    .venv/bin/python scripts/probes/_miso143_footing.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import (  # noqa: E402
    COAL_COLS,
    HOURS,
    THERMAL_COLS,
    YEARS,
    clear_many,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    sidecar_classes,
    sidecar_price,
    windows,
)

OUT = REPO / "results/calibration/_miso143_footing.json"

# PREREG bars, fixed BEFORE the numbers were seen.
P1_MED_ABS_BAR = 4.00  # $/MWh
P1_R_BAR = 0.85
P2_BAND = (0.30, 0.55)
P2_FALSIFY = (0.20, 0.70)
P9_BAR = 0.01  # 1 %


def year_block(year: int) -> dict:
    """Footing + marginal-class census for one year, both bracket endpoints."""
    st = fleet_state(year)
    gens = st["fleet"]
    fa = st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    cap = fa.pmax[:, None] * fa.availability  # (n_gen, T) capability

    kl = klass_of(gens)
    assert kl.size == len(gens)
    # TRAP 5: every class this probe reads must be non-empty in the FLEET.
    for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
        assert (kl == k).sum() > 0, (
            f"class {k!r} has ZERO fleet rows -- plant_group is populated for "
            "the fossil classes only and a silent empty filter reads as absence "
            "(TRAP 5, miso-142)"
        )

    mk = markup_ceiling(gens, fa, st["config"])
    offers = {"lo": mc0, "hi": mc0 + mk[:, None]}

    piv = sidecar_classes(year)
    thermal = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    coal_side = piv[list(COAL_COLS)].sum(axis=1).to_numpy(float)
    price, _w = sidecar_price(year)

    out: dict = {
        "n_gen": len(gens),
        "markup_rows_nonzero": int((mk > 0).sum()),
        "markup_mean_usd_per_mwh_nonzero": (
            round(float(mk[mk > 0].mean()), 4) if (mk > 0).any() else 0.0
        ),
        "windows": {},
    }

    for wname, sel in windows().items():
        ok = sel & np.isfinite(price) & np.isfinite(thermal) & (thermal > 0)
        hrs = np.nonzero(ok)[0]
        need = thermal[hrs]
        blk: dict = {"n_hours": int(hrs.size)}

        # ---- P9: the rebuilt stack must be able to carry the sidecar's coal.
        coal_rows = kl == "COAL"
        coal_capability = cap[coal_rows][:, hrs].sum(axis=0)
        blk["p9_coal_sidecar_mw"] = round(float(coal_side[hrs].mean()), 2)
        blk["p9_coal_capability_mw"] = round(float(coal_capability.mean()), 2)
        blk["p9_coal_dispatch_over_capability"] = round(
            float(coal_side[hrs].mean() / max(1e-9, coal_capability.mean())), 4
        )

        for tag, offer in offers.items():
            p_hat, row = clear_many(offer, cap, need, hrs)
            unreached = row < 0
            d = p_hat - price[hrs]
            fin = np.isfinite(d)
            r = (
                float(np.corrcoef(p_hat[fin], price[hrs][fin])[0, 1])
                if fin.sum() > 2
                else float("nan")
            )
            marg = np.where(unreached, "<unreached>", kl[np.clip(row, 0, None)])
            n = max(1, marg.size)
            share = {
                k: round(float((marg == k).sum()) / n, 4)
                for k in sorted(set(marg.tolist()))
            }
            blk[tag] = {
                "model_clear_mean": round(float(np.mean(p_hat)), 3),
                "keeper_p1_mean": round(float(np.mean(price[hrs])), 3),
                "bias_mean": round(float(np.mean(d)), 3),
                "median_abs_err": round(float(np.median(np.abs(d))), 3),
                "pearson_r": round(r, 4),
                "unreached_frac": round(float(unreached.mean()), 4),
                "marginal_class_share": share,
                "marginal_coal_share": round(
                    float(sum(v for k, v in share.items() if k == "COAL")), 4
                ),
            }
        out["windows"][wname] = blk
    return out


def main() -> None:
    hygiene()
    res = {
        "prereg": "results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md",
        "gate": "G-A0 (footing STOP gate) + P2 marginal-class + P9 self-check",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": "NO SOLVE -- run_year(fleet_only=True) reconstruction only",
        "basis": "model-only (keeper P0 offer stack + keeper P1 sidecars); no "
        "EIA-930/EIA-923 instrument enters this gate (TRAP 3)",
        "bars": {
            "P1_median_abs_err_max": P1_MED_ABS_BAR,
            "P1_pearson_r_min": P1_R_BAR,
            "P2_band": list(P2_BAND),
            "P2_falsify_outside": list(P2_FALSIFY),
            "P9_rel_tol": P9_BAR,
        },
        "years": {},
    }
    for y in YEARS:
        res["years"][str(y)] = year_block(y)

    # --- verdict on the PREREG bars, scored on 2025 JJA h12-17 -------------
    g = res["years"]["2025"]["windows"]["JJA_h12_17"]
    verdict = {}
    for tag in ("lo", "hi"):
        b = g[tag]
        verdict[tag] = {
            "P1_median_abs_err": b["median_abs_err"],
            "P1_pearson_r": b["pearson_r"],
            "P1_PASS": bool(
                b["median_abs_err"] <= P1_MED_ABS_BAR and b["pearson_r"] >= P1_R_BAR
            ),
            "P2_marginal_coal_share": b["marginal_coal_share"],
            "P2_in_band": bool(
                P2_BAND[0] <= b["marginal_coal_share"] <= P2_BAND[1]
            ),
            "P2_falsified": bool(
                b["marginal_coal_share"] < P2_FALSIFY[0]
                or b["marginal_coal_share"] > P2_FALSIFY[1]
            ),
        }
    res["verdict_2025_JJA_h12_17"] = verdict
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
