"""miso-222 phase 0 — HOW MUCH CAPACITY MUST LEAVE THE STACK FOR THE PRICE TO REACH THE TAIL?

Zero-solve. miso-221 measured that MISO's C3c tail is not reachable through the
authorized ``offer_curve_by_group`` channel, and that the block sitting immediately
above the model's clearing price in the object's hours is **oil** — 90.9 / 91.8 /
98.7 % of the non-tranche capacity, ~2.9 GW at a cap-weighted $241-$249/MWh, already
priced in the tail range. So the model is not missing tail-priced supply; it is
missing the **tightness** to reach it.

This probe SIZES that gap, so the owner ask names a cohort and a magnitude rather
than a direction. For each object hour it walks the keeper's own merit stack upward
from the committed clearing price and reports, **decomposed by class|band**, the
capacity that would have to become unavailable for the marginal offer to land at:

* **$200/MWh** — the C3c threshold itself;
* **the oil floor** — the cheapest available oil tranche that hour, i.e. the first
  price at which the unreachable block starts setting price;
* **the measured actual** — the full gap.

The arithmetic is a merit-order displacement at fixed demand: removing ``X`` MW of
capacity priced below level ``L`` moves the clearing point up the residual stack by
exactly ``X``, so the MW that must leave is the capacity lying between the current
clearing price and ``L``. It is first-order — dispatch is not re-optimized and
nothing re-commits — and it is deliberately conservative for the ask, because it
assumes every removed MW is replaced from strictly above rather than from imports,
storage or a neighbouring zone.

**Nothing here proposes or arms a mechanism.** Rule 29 ``[R-SCREEN]`` step 0 only.
Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    python3 scripts/probes/_miso222_removal_sizing_phase0.py       # all three years
    MISO222_YEARS=2025 python3 scripts/probes/_miso222_removal_sizing_phase0.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso221_peak_shape_phase0 as _m221  # noqa: E402

from _miso221_peak_shape_phase0 import (  # noqa: E402
    EPS,
    TAIL_USD,
    _r,
    _stack,
    _stamp,
    actual_lmp,
    keeper_table,
    keeper_zone_price,
    object_hours,
)

KEEPER = _m221.KEEPER
OUT = REPO / "results/calibration/_miso222_removal_sizing.json"
YEARS = tuple(
    int(v) for v in os.environ.get("MISO222_YEARS", "2023,2024,2025").split(",")
)
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"

#: Fuel types carrying NO ``offer_curve_by_group`` entry (miso-221 §3): the block
#: the authorized channel cannot reach. Oil is 91-99 % of the part above the price.
UNREACHABLE_FUELS: tuple[str, ...] = ("oil", "biomass")


def _levels(
    mc_h: np.ndarray,
    cap_h: np.ndarray,
    live: np.ndarray,
    fuel: np.ndarray,
    price: float,
    actual: float,
) -> dict:
    """The three target levels for one hour, with the oil floor measured not assumed."""
    oil = live & (fuel == "oil") & (mc_h > price + EPS)
    oil_floor = float(mc_h[oil].min()) if oil.any() else float("nan")
    return {"200": TAIL_USD, "oil_floor": oil_floor, "actual": actual}


def analyse_year(year: int) -> dict:
    """Per-object-hour removal sizing, decomposed by class|band."""
    mc, klass, band, _zone, pmax, avail = _stack(keeper_table(), year)
    # fuel_type is not carried on the tranche arrays; rebuild the label vector once.
    import dataclasses

    from _miso134_ct_night_order_screen import build_year, keeper_config

    cfg = dataclasses.replace(keeper_config(), offer_curve_by_group=keeper_table())
    _, fleet, _arrays, _, _, _ = build_year(cfg, year)
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])

    zp, hrs, act = keeper_zone_price(year), object_hours(year), actual_lmp(year)
    rows, pooled = [], {}
    for h in hrs:
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0
        mc_h = mc[:, h]
        p, a = float(zp[h]), float(act[h])
        lv = _levels(mc_h, cap_h, live, fuel, p, a)

        row = {
            "hour": int(h),
            "stamp": _stamp(h),
            "hod": int(h % 24),
            "committed_price_usd": _r(p, 2),
            "actual_rt_usd": _r(a, 2),
            "oil_floor_usd": _r(lv["oil_floor"], 2),
        }
        for name, L in lv.items():
            if not np.isfinite(L):
                row[f"mw_to_{name}"] = None
                continue
            sel = live & (mc_h > p + EPS) & (mc_h <= L)
            row[f"mw_to_{name}"] = _r(float(cap_h[sel].sum()), 0)
            if name == "200":
                # the cohort that must leave, by class|band — this is what the ask names
                for k in sorted(set(klass[sel])):
                    for b in sorted(set(band[sel & (klass == k)])):
                        s2 = sel & (klass == k) & (band == b)
                        key = f"{k}|{b}"
                        pooled[key] = pooled.get(key, 0.0) + float(cap_h[s2].sum())
        rows.append(row)

    n = len(hrs)
    cohort = {
        k: _r(v / n, 0)
        for k, v in sorted(pooled.items(), key=lambda kv: -kv[1])
        if v / n >= 1.0
    }
    # what fraction of the must-leave cohort is on the authorized channel at all
    reachable = sum(
        v
        for k, v in pooled.items()
        if k.split("|")[0] in keeper_table() and k.split("|")[1] != "?"
    )
    total = sum(pooled.values())
    out = {
        "year": year,
        "object_hours": hrs,
        "rows": rows,
        "mw_to_200_mean": _r(float(np.mean([r["mw_to_200"] for r in rows])), 0),
        "mw_to_200_min": _r(float(np.min([r["mw_to_200"] for r in rows])), 0),
        "mw_to_200_max": _r(float(np.max([r["mw_to_200"] for r in rows])), 0),
        "mw_to_oil_floor_mean": _r(
            float(
                np.nanmean(
                    [
                        r["mw_to_oil_floor"]
                        for r in rows
                        if r["mw_to_oil_floor"] is not None
                    ]
                )
            ),
            0,
        ),
        "mw_to_actual_mean": _r(
            float(
                np.nanmean(
                    [r["mw_to_actual"] for r in rows if r["mw_to_actual"] is not None]
                )
            ),
            0,
        ),
        "must_leave_cohort_mean_mw_by_class_band": cohort,
        "must_leave_on_authorized_channel_share": _r(reachable / max(total, EPS), 4),
    }
    del mc, klass, band, pmax, avail, fleet
    gc.collect()
    return out


def main() -> int:
    """Run every requested year and write the sizing record."""
    rec = {
        "probe": "miso-222 phase 0 - how much capacity must leave the stack to reach the tail?",
        "keeper": "2026-09-05-miso-220-nonsteam-lift",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solved": False,
        "method": (
            "merit-order displacement at fixed demand: the MW that must become "
            "unavailable for the marginal offer to land at a target level is the "
            "capacity between the committed clearing price and that level. "
            "First-order; no re-dispatch, no re-commitment."
        ),
        "by_year": {},
    }
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        print(f"  {y} done", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
