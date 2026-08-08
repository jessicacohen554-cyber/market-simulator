"""miso-143 gate G-B — WHY the model re-ranks coal ahead of gas harder than the
market did (PREREG P6, P7; B-1 / B-2 / B-4).  **B-3 is already ELIMINATED** by
G-A1's P8 reading and is not re-tested here.

No solve.  Every number is the model's own offer stack
(``run_year(fleet_only=True)``, see ``_miso143_stack``) or a committed
constant, read at the SAME grain the mechanism itself is defined on.

**B-1 — the gas offer margin's FIXED-ANCHOR FORM (P6).**  The keeper arms
``gas_offer_net_revenue_margin=True`` at ``gas_offer_margin_anchor=3.0492``
$/MMBtu, the 2023-2025 training-window mean delivered gas.
``apply_gas_offer_margin`` (``data/offer_curves.py:613``) applies::

    mc[g,t] += offer_markup_hr[g] x (anchor - fuel_price[g,t])

so the gas markup is a **fuel-invariant** $/MWh margin fixed at the anchor.
Mechanically, therefore, the mechanism **compresses the year-to-year swing of
gas offers around the middle of its own training window**: in 2023 (fuel below
the anchor) it LIFTS gas offers; in 2025 (fuel well above it) it CUTS them, by
``markup_hr x (fuel - anchor)``.  That is a 2025-specific, monotone-in-gas-price
haircut on exactly the class the model under-runs.

This is a **FORM** question, not a fitted level, and it is measured two ways:

* the **fleet-wide** haircut (cap-weighted over every gas tranche carrying a
  markup) -- the mechanism's size; and
* the **price-relevant** haircut, restricted to the tranche sitting AT the
  hour's own clearing price, because a haircut on an inframarginal tranche
  moves no price at all.  A mechanism's reach is where it is marginal, not
  where it is large (the miso-129 bar, applied to a mechanism rather than to a
  class).

**B-2 — delivered coal price (P7).**  The keeper runs
``coal_plant_monthly_pricing=True``, so a coal plant reporting an EIA-923
monthly delivered cost is priced at its OWN measured cost and only the
non-reporting remainder falls back to the trajectory.  The measurement that
matters is therefore not just the level but the **fallback share**: that is the
only place a coal-price defect can hide, and it is reported explicitly.

**B-4 — CC/CT heat-rate distribution.**  Reported DESCRIPTIVELY and named last,
because it is the candidate least able to produce a 2025-SPECIFIC step: heat
rates do not move with the gas price.

Usage::

    .venv/bin/python scripts/probes/_miso143_gb_mechanisms.py
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
    GAS_COLS,
    THERMAL_COLS,
    YEARS,
    fleet_state,
    hygiene,
    klass_of,
    sidecar_classes,
    sidecar_price,
    windows,
)

OUT = REPO / "results/calibration/_miso143_gb_mechanisms.json"

# PREREG P6 bars, fixed before the numbers were seen.
P6_HAIRCUT_2025 = (0.60, 3.00)
P6_UPLIFT_2023 = (0.80, 2.50)
P6_SWING = (1.50, 5.00)
P6_INERT_BELOW = 0.50
P6_DOMINANT_ABOVE = 8.00
P7_TOL = 0.15  # +/-15 % on the delivered coal price


def _wavg(x: np.ndarray, w: np.ndarray) -> float:
    s = float(w.sum())
    return float((x * w).sum() / s) if s > 1e-9 else float("nan")


def year_block(year: int) -> dict:
    st = fleet_state(year)
    gens, fa, cfg = st["fleet"], st["fleet_arrays"], st["config"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    fp = np.asarray(st["fuel_prices"], dtype=float)
    cap = fa.pmax[:, None] * fa.availability
    kl = klass_of(gens)

    anchor = float(getattr(cfg, "gas_offer_margin_anchor", 0.0) or 0.0)
    armed = bool(getattr(cfg, "gas_offer_net_revenue_margin", False))
    markup_hr = np.array(
        [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in gens], dtype=float
    )
    is_gas = np.isin(kl, list(GAS_COLS))
    is_coal = kl == "COAL"
    has_markup = markup_hr > 0.0

    # B-1: the haircut, per generator-hour.  POSITIVE = the fixed-anchor form
    # prices the tranche BELOW the registered multiplier form (fuel > anchor).
    haircut = markup_hr[:, None] * (fp - anchor)

    piv = sidecar_classes(year)
    thermal = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    price, _ = sidecar_price(year)

    out: dict = {
        "gas_offer_net_revenue_margin_armed": armed,
        "gas_offer_margin_anchor_usd_mmbtu": anchor,
        "n_tranches_with_markup": int(has_markup.sum()),
        "markup_hr_mmbtu_per_mwh": {
            "median": round(float(np.median(markup_hr[has_markup])), 4),
            "cap_weighted_mean": round(
                _wavg(markup_hr[has_markup], fa.pmax[has_markup]), 4
            ),
            "max": round(float(markup_hr[has_markup].max()), 4),
        },
        "windows": {},
    }

    for wname, sel in windows().items():
        ok = sel & np.isfinite(price) & np.isfinite(thermal) & (thermal > 0)
        hrs = np.nonzero(ok)[0]

        gm = is_gas & has_markup
        w = cap[gm][:, hrs]
        # ---- B-1 leg 1: the FLEET-WIDE haircut (the mechanism's size) -----
        fleet_haircut = _wavg(haircut[gm][:, hrs], w)
        fleet_fuel = _wavg(fp[gm][:, hrs], w)

        # ---- B-1 leg 2: the PRICE-RELEVANT haircut (its reach) -----------
        # The tranche sitting AT the hour's own clearing price is the one whose
        # haircut actually moves the price; everything inframarginal moves
        # nothing.  Identified per hour as the available tranche with the
        # largest offer not exceeding the hour's P1 price.
        marg_class, marg_haircut, marg_offer = [], [], []
        for t in hrs:
            o_t, c_t, a = mc0[:, t], cap[:, t], float(price[t])
            m = (o_t <= a) & (c_t > 0)
            if not m.any():
                continue
            idx = np.nonzero(m)[0]
            j = idx[int(np.argmax(o_t[idx]))]
            marg_class.append(str(kl[j]))
            marg_offer.append(float(o_t[j]))
            marg_haircut.append(float(haircut[j, t]) if is_gas[j] else 0.0)

        n = max(1, len(marg_class))
        cls_share = {
            k: round(marg_class.count(k) / n, 4) for k in sorted(set(marg_class))
        }
        gas_marg_share = float(
            sum(v for k, v in cls_share.items() if k in GAS_COLS)
        )

        # ---- B-2: delivered coal price and the FALLBACK share ------------
        cw = cap[is_coal][:, hrs]
        coal_price = _wavg(fp[is_coal][:, hrs], cw)
        # A plant priced from the trajectory has an identical price in EVERY
        # month; a plant priced from its own measured EIA-923 monthly cost
        # varies.  Measured structurally rather than asserted.
        cf = fp[is_coal][:, hrs]
        flat = np.isclose(cf.max(axis=1), cf.min(axis=1), rtol=1e-9, atol=1e-9)
        fallback_cap_share = float(
            cw[flat].sum() / max(1e-9, cw.sum())
        )

        # ---- B-4: CC/CT effective heat rates (descriptive) ---------------
        hr_rows = {}
        for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL"):
            rows = kl == k
            if not rows.any():
                continue
            hr_rows[k] = {
                "cap_weighted_hr": round(_wavg(fa.heat_rate[rows], fa.pmax[rows]), 4),
                "p10": round(float(np.quantile(fa.heat_rate[rows], 0.10)), 4),
                "p50": round(float(np.quantile(fa.heat_rate[rows], 0.50)), 4),
                "p90": round(float(np.quantile(fa.heat_rate[rows], 0.90)), 4),
                "n_rows": int(rows.sum()),
            }

        out["windows"][wname] = {
            "n_hours": int(hrs.size),
            "b1_fleet_gas_delivered_fuel_usd_mmbtu": round(fleet_fuel, 4),
            "b1_fuel_minus_anchor_usd_mmbtu": round(fleet_fuel - anchor, 4),
            "b1_fleet_haircut_usd_mwh": round(fleet_haircut, 4),
            "b1_marginal_tranche_class_share": cls_share,
            "b1_marginal_tranche_gas_share": round(gas_marg_share, 4),
            "b1_price_relevant_haircut_usd_mwh": round(
                float(np.mean(marg_haircut)), 4
            )
            if marg_haircut
            else None,
            "b1_marginal_offer_mean": round(float(np.mean(marg_offer)), 4)
            if marg_offer
            else None,
            "b2_coal_delivered_usd_mmbtu": round(coal_price, 4),
            "b2_trajectory_fallback_cap_share": round(fallback_cap_share, 4),
            "b4_heat_rates": hr_rows,
        }
    return out


def main() -> None:
    hygiene()
    res = {
        "prereg": "results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md",
        "gate": "G-B (why the model re-ranks harder) -- B-1 / B-2 / B-4",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": "NO SOLVE -- run_year(fleet_only=True) offer stack only",
        "b3_status": "ELIMINATED at G-A1 by P8: the effective fuel passthrough "
        "of the MARGINAL coal tranches is 1.000 in 2025 (0.995-0.998 in "
        "2023/24), so the sunk-fuel 0.0 / 0.35 bands are INFRAMARGINAL and the "
        "coal tranche structure is not the merit-order channel. Not re-tested.",
        "bars": {
            "P6_haircut_2025": list(P6_HAIRCUT_2025),
            "P6_uplift_2023": list(P6_UPLIFT_2023),
            "P6_swing": list(P6_SWING),
            "P6_inert_below": P6_INERT_BELOW,
            "P6_dominant_above": P6_DOMINANT_ABOVE,
            "P7_tolerance": P7_TOL,
        },
        "years": {},
    }
    for y in YEARS:
        res["years"][str(y)] = year_block(y)

    # ---- P6 scored on JJA h12-17, the lane's window ----------------------
    w = "JJA_h12_17"
    h25 = res["years"]["2025"]["windows"][w]["b1_fleet_haircut_usd_mwh"]
    h23 = res["years"]["2023"]["windows"][w]["b1_fleet_haircut_usd_mwh"]
    pr25 = res["years"]["2025"]["windows"][w]["b1_price_relevant_haircut_usd_mwh"]
    pr23 = res["years"]["2023"]["windows"][w]["b1_price_relevant_haircut_usd_mwh"]
    res["p6_verdict"] = {
        "window": w,
        "fleet_haircut_2025": h25,
        "fleet_uplift_2023": round(-h23, 4),
        "fleet_swing_2023_to_2025": round(h25 - h23, 4),
        "price_relevant_haircut_2025": pr25,
        "price_relevant_uplift_2023": round(-pr23, 4) if pr23 is not None else None,
        "price_relevant_swing": (
            round(pr25 - pr23, 4) if (pr25 is not None and pr23 is not None) else None
        ),
        "in_band_haircut_2025": bool(
            P6_HAIRCUT_2025[0] <= h25 <= P6_HAIRCUT_2025[1]
        ),
        "in_band_uplift_2023": bool(
            P6_UPLIFT_2023[0] <= -h23 <= P6_UPLIFT_2023[1]
        ),
        "in_band_swing": bool(P6_SWING[0] <= (h25 - h23) <= P6_SWING[1]),
        "inert": bool((h25 - h23) < P6_INERT_BELOW),
        "dominant": bool((h25 - h23) > P6_DOMINANT_ABOVE),
    }
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
