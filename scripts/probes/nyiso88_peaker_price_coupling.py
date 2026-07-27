"""Test whether NYISO's CT_PEAKER volume gap is a C3c price-formation symptom.

nyiso-87 removed the owner-adjudicated-inaccurate h14-21 peak-window floors and
CT_PEAKER's diurnal SHAPE became good (D-1 profile_r 0.88/0.93/0.95, cv_ratio
1.38/1.07/1.15) while its LEVEL collapsed to 0.46 TWh against a 2.26 TWh CEMS
actual (2023). The nyiso-88 charter offers three admissible directions, and
names direction (c) as the one to test FIRST because it may make the other two
unnecessary:

    "if peak prices formed correctly, peakers would clear economically and the
    level would partly self-heal. Test the coupling BEFORE building anything...
    If most of the 1.8 TWh comes back, this is a C3c symptom."

This probe answers that WITHOUT an LP, from committed artifacts only (rule 14):

* the keeper's own hourly sidecars (``hourly/class_hourly_<year>.parquet`` +
  ``hourly/system_<year>.parquet``) for model CT_PEAKER dispatch and the model's
  internal zonal prices,
* the committed CAMPD bench (``frontend/data/backcast/bench/NYISO/<year>.json.gz``)
  for the plant-level actual the D-1 gate itself scores against.

The construction is an **offer-stack revealed-preference** one. The model's own
CT_PEAKER dispatch, read against the model's own price in the same hour, reveals
the class's effective offer curve: the price at which each increment of the class
comes in-merit. That curve is then re-evaluated against a **counterfactual price
series** — the model's price with the diurnal swing widened to the measured
NYISO DA swing (nyiso-86 §3: model $8.36 vs real $22.5 load-weighted
hour-of-day max-minus-min) — to ask the charter's question directly: how much of
the 1.8 TWh gap does correct peak-price formation buy back?

The counterfactual is a **scoring-side thought experiment**, never a model input:
it estimates an upper bound on direction (c)'s reach. If the bound is well short
of the gap, (c) is refuted as the sole explanation and the lane must build a real
peaker mechanism ((a) non-spin borne by offline quick-start GTs, or (b)
start-cost recovery in the offer).

CLOCK: the committed hourly parquet is on the model's non-leap 8760
local-standard clock, which DROPS local-standard Feb 29 in a leap year; the
bench series is on the same clock, so no remap is needed here (both are indexed
0..8759 on the identical model clock — see ``nyiso85_tail_anatomy._utc_of_hour``
for the UTC mapping that IS needed when joining to wall-clock sources).

Usage::

    python scripts/probes/nyiso88_peaker_price_coupling.py \
        --bundle results/calibration/nyiso87_cmeas_minrun \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.legitimacy_diagnostics import load_bench  # noqa: E402

#: The class whose level collapsed — the nyiso-87 dominant open item.
PEAKER_CLASS = "CT_PEAKER"

#: Internal NYISO zones (the seam node carries no internal price).
INTERNAL_ZONES = (
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
)

#: Measured NYISO DA load-weighted hour-of-day price swing (max-minus-min),
#: 2023/2024/2025 — nyiso-86 §3, reproduced by nyiso87_arm_compare.py against
#: ``actual_lmp_hourly_NYISO.parquet``. The counterfactual widens the model's
#: own swing to these values.
ACTUAL_DIURNAL_SWING = {2023: 22.5, 2024: 25.1, 2025: 43.3}


def load_model_peaker(bundle: Path, year: int) -> np.ndarray:
    """Return the keeper's P1 hourly CT_PEAKER dispatch (MW, length 8760)."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == PEAKER_CLASS)]
    out = np.zeros(8760)
    out[df["hour"].to_numpy(dtype=int)] = df["mw"].to_numpy(dtype=float)
    return out


def load_model_price(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (load-weighted internal price, internal demand) hourly arrays."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["zone"].isin(INTERNAL_ZONES))]
    wide_p = df.pivot_table(index="hour", columns="zone", values="price")
    wide_d = df.pivot_table(index="hour", columns="zone", values="demand")
    load = wide_d.sum(axis=1)
    # 2024/2025 each carry a handful of hours with zero demand in EVERY internal
    # zone (3 h and 2 h respectively — a demand-source gap in the committed
    # sidecar, not a solve artifact). Load-weighting is undefined there; fall
    # back to the unweighted zonal mean so the hour still carries a price.
    price = (wide_p * wide_d).sum(axis=1) / load.where(load > 0.0)
    price = price.fillna(wide_p.mean(axis=1))
    return price.to_numpy(dtype=float)[:8760], load.to_numpy(dtype=float)[:8760]


def load_actual_peaker(year: int) -> np.ndarray:
    """Return the CEMS actual hourly CT_PEAKER total (MW), the D-1 benchmark."""
    bench = load_bench(REPO, "NYISO", year)
    out = np.zeros(8760)
    for rec in bench.values():
        if rec["group"] == PEAKER_CLASS:
            out += np.asarray(rec["mw"], dtype=float)[:8760]
    return out


def offer_curve(model_mw: np.ndarray, price: np.ndarray, n_bins: int = 60):
    """Return the class's revealed offer curve as (price_edge, mw) step points.

    Sorting the model's own hours by price and taking the running maximum of
    class dispatch recovers a monotone non-decreasing supply function: the MW
    the class is willing to produce at or below each price. This is the LP's
    own merit order for the class, read off its solution rather than rebuilt
    from the offer tables — so it already embeds availability, min-gen and any
    binding commitment structure.
    """
    order = np.argsort(price)
    p_sorted = price[order]
    mw_sorted = model_mw[order]
    edges = np.quantile(p_sorted, np.linspace(0.0, 1.0, n_bins + 1))
    edges = np.unique(edges)
    # Per price bin, the class's 90th-percentile dispatch: the capacity that is
    # genuinely reachable at that price, robust to individual outage hours.
    idx = np.clip(np.searchsorted(edges, p_sorted, side="right") - 1, 0, len(edges) - 2)
    reach = np.zeros(len(edges) - 1)
    for b in range(len(edges) - 1):
        sel = mw_sorted[idx == b]
        reach[b] = float(np.quantile(sel, 0.90)) if sel.size else 0.0
    return edges, np.maximum.accumulate(reach)


def apply_counterfactual_swing(
    price: np.ndarray, demand: np.ndarray, target_swing: float
) -> np.ndarray:
    """Widen the price series' load-weighted diurnal swing to *target_swing*.

    The model's hour-of-day price profile is stretched about its load-weighted
    mean by the ratio the measured swing bears to the model's own, leaving the
    annual mean price and every within-hour-of-day deviation untouched. This is
    deliberately the MOST generous rendering of direction (c): it grants the
    model perfect peak/off-peak price formation for free, with no offsetting
    cost anywhere, so the recovered volume it implies is an UPPER BOUND on what
    fixing C3c-style price formation could buy CT_PEAKER.
    """
    hod = np.arange(8760) % 24
    w = demand
    prof = np.array(
        [np.average(price[hod == h], weights=w[hod == h]) for h in range(24)]
    )
    swing = float(prof.max() - prof.min())
    if swing <= 1e-9:
        return price.copy()
    scale = target_swing / swing
    mean = float(np.average(price, weights=w))
    lift = (prof - mean) * (scale - 1.0)
    return price + lift[hod]


def volume_at(edges: np.ndarray, curve: np.ndarray, price: np.ndarray) -> float:
    """Return TWh the revealed offer curve yields against a price series."""
    idx = np.clip(np.searchsorted(edges, price, side="right") - 1, 0, len(curve) - 1)
    return float(curve[idx].sum() / 1e6)


def analyse(bundle: Path, year: int) -> dict:
    """Return the coupling statistics for one year."""
    model = load_model_peaker(bundle, year)
    actual = load_actual_peaker(year)
    price, demand = load_model_price(bundle, year)

    edges, curve = offer_curve(model, price)
    cf_price = apply_counterfactual_swing(price, demand, ACTUAL_DIURNAL_SWING[year])

    model_twh = float(model.sum() / 1e6)
    actual_twh = float(actual.sum() / 1e6)
    cf_twh = volume_at(edges, curve, cf_price)
    base_twh = volume_at(edges, curve, price)

    # Where the actual energy sits in the model's own price distribution: if the
    # missing energy is in hours the model prices near the top, direction (c) is
    # live; if it is spread through mid-merit hours, no peak uplift reaches it.
    pct = pd.Series(price).rank(pct=True).to_numpy()
    gap = np.maximum(actual - model, 0.0)
    bands = {}
    for lo, hi, name in ((0.0, 0.5, "p0_50"), (0.5, 0.9, "p50_90"), (0.9, 1.0, "p90_100")):
        sel = (pct > lo) & (pct <= hi) if lo else (pct <= hi)
        bands[name] = round(float(gap[sel].sum() / 1e6), 3)

    # The C3c tail itself, for scale: hours the model's max internal zonal price
    # clears $300 cannot hold more than a few GWh however they are priced.
    return {
        "year": year,
        "model_twh": round(model_twh, 3),
        "actual_twh": round(actual_twh, 3),
        "gap_twh": round(actual_twh - model_twh, 3),
        "model_swing": round(
            float(
                np.max(
                    [
                        np.average(price[np.arange(8760) % 24 == h], weights=demand[np.arange(8760) % 24 == h])
                        for h in range(24)
                    ]
                )
                - np.min(
                    [
                        np.average(price[np.arange(8760) % 24 == h], weights=demand[np.arange(8760) % 24 == h])
                        for h in range(24)
                    ]
                )
            ),
            2,
        ),
        "target_swing": ACTUAL_DIURNAL_SWING[year],
        "curve_base_twh": round(base_twh, 3),
        "curve_counterfactual_twh": round(cf_twh, 3),
        "counterfactual_recovery_twh": round(cf_twh - base_twh, 3),
        "recovery_share_of_gap": (
            round((cf_twh - base_twh) / (actual_twh - model_twh), 3)
            if actual_twh > model_twh
            else None
        ),
        "gap_by_model_price_band_twh": bands,
        "actual_hours_running": int((actual > 1.0).sum()),
        "model_hours_running": int((model > 1.0).sum()),
        "actual_peak_mw": round(float(actual.max()), 1),
        "model_peak_mw": round(float(model.max()), 1),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the coupling probe and print/emit the per-year statistics."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    rows = [analyse(args.bundle, y) for y in args.years]
    for r in rows:
        print(json.dumps(r, indent=2))
    print("\n--- summary -------------------------------------------------")
    print(f"{'year':>6} {'model':>8} {'actual':>8} {'gap':>8} {'cf recov':>9} {'share':>7}")
    for r in rows:
        print(
            f"{r['year']:>6} {r['model_twh']:>8.2f} {r['actual_twh']:>8.2f} "
            f"{r['gap_twh']:>8.2f} {r['counterfactual_recovery_twh']:>9.2f} "
            f"{(r['recovery_share_of_gap'] or 0):>7.1%}"
        )
    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
