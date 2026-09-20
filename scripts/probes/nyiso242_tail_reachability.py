"""nyiso-242 phase 0D — can ANY price-formation mechanism reach the missed 2022 tail?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The decisive instrument of this session,
and it is deliberately a BOUND rather than a candidate: it asks what the LP's
own state would have to be for a $300+ energy dual to be possible at all, and
measures how far the keeper's state is from it.

The argument is the LP's, not a modeller's. The energy-balance dual is the
marginal unit's offer, so a zonal price above $300 requires that **every
tranche offering below $300 is already fully dispatched**. Idle sub-$300
capacity is therefore a hard ceiling on price: no reserve demand curve, no
RCPF step, no ORDC adder and no offer-cap change can lift the energy dual past
a tranche the LP can still buy more cheaply. (A reserve product can add a
separate reserve dual on top; what it cannot do is move the ENERGY dual, which
is what C3a, C3b and C3c are scored on.)

So the probe partitions each year's missed tail hours and measures, per hour:

* the model's available thermal capacity by offer band,
* how much of it is idle, and
* how much of THAT is idle below the $300 gate.

A window with several GW idle below $300 is **not reachable by price
formation** — its defect is availability or fuel cost, upstream of pricing. A
window with little idle sub-$300 capacity and a populated $300+ band IS
reachable, and is where a scarcity-pricing mechanism belongs.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_tail_reachability.py [--years 2022 ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def _designated_keeper_bundle(iso: str = "NYISO") -> Path:
    """Resolve the ISO's CURRENT designated keeper bundle from the keeper shard.

    A hardcoded bundle id dies at the next promotion: rule 35 ``[R-PROMOTE]``
    (a) deletes the outgoing keeper's bundle dir in the promoting session, so a
    probe pinned to ``nyiso241_ctcommitted_span`` raised ``FileNotFoundError``
    the moment nyiso-247 promoted. Resolve keeper shard -> registry sidecar ->
    ``bundle`` instead, so the probe follows the designation automatically.
    ``NYISO_KEEPER_BUNDLE`` overrides for an explicit A/B against a non-keeper.
    """
    import os

    override = os.environ.get("NYISO_KEEPER_BUNDLE")
    if override:
        return REPO / override if not Path(override).is_absolute() else Path(override)
    shard = REPO / "frontend" / "data" / "backcast" / "keepers" / f"{iso}.json"
    keeper_id = json.loads(shard.read_text())["keeper"]
    sidecar = REPO / "frontend" / "data" / "backcast" / "registry" / f"{keeper_id}.json"
    return REPO / json.loads(sidecar.read_text())["bundle"]


BUNDLE = _designated_keeper_bundle()
HUB = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
THRESHOLD = 300.0
BANDS = ((0, 50), (50, 100), (100, 200), (200, 300), (300, 500), (500, float("inf")))
#: Thermal = every class whose tranche carries a fuel cost and can be committed.
THERMAL_TOKENS = ("CC", "CT", "ST", "COAL", "OIL", "OTHER_FOSSIL")


def _is_thermal(klass: str) -> bool:
    return any(t in klass.upper() for t in THERMAL_TOKENS)


def fleet_state(year: int):
    """Fleet-only rebuild of the keeper's recipe — no LP is entered."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    return run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)


def missed_mask(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(missed, month) — hours the actual RT hub tail clears $300 and the model does not.

    The actual side is the committed hub series the C3c gate itself counts from
    (``derive_actual_tail``); the model side is the max zonal dual, which is the
    statistic ``score_price_tail`` reads. Both are the gate's own quantities.
    """
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"] != "NYISO_external")]
    mmax = sysf.groupby("hour")["price"].max().sort_index().to_numpy()
    hub = pd.read_parquet(HUB)
    hub = hub[hub["year"] == year].sort_values("hour")["rt"].to_numpy()
    n = min(len(mmax), len(hub))
    missed = (hub[:n] > THRESHOLD) & (mmax[:n] <= THRESHOLD)
    month = pd.date_range(f"{year}-01-01", periods=n, freq="h").month.to_numpy()
    return missed, month


def run_year_probe(year: int) -> dict:
    st = fleet_state(year)
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    klass = np.array([str(k) for k in fa.plant_group])
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], 8760, axis=1)
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, axis=1)
    tm = np.array([_is_thermal(k) for k in klass])

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    windows = {
        "all_missed": idx[missed],
        "winter_missed": idx[missed & np.isin(month, (1, 2, 12))],
        "summer_missed": idx[missed & np.isin(month, (6, 7, 8))],
        "all_8760": idx,
    }

    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    gen = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    tgen = gen[[c for c in gen.columns if _is_thermal(c)]].sum(axis=1)

    out: dict = {"year": year, "windows": {}}
    for label, sel in windows.items():
        sel = sel[sel < mc.shape[1]]
        if not len(sel):
            continue
        sub = mc[np.ix_(tm, sel)]
        cap = pmax[tm][:, None] * av[np.ix_(tm, sel)]
        rec: dict = {"hours": int(len(sel))}
        rec["available_by_band_mw"] = {
            (f"{a:.0f}-{b:.0f}" if np.isfinite(b) else f"{a:.0f}+"): round(
                float(np.median((((sub >= a) & (sub < b)) * cap).sum(axis=0))), 1
            )
            for a, b in BANDS
        }
        avail = float(np.median(cap.sum(axis=0)))
        lt = float(np.median(((sub < THRESHOLD) * cap).sum(axis=0)))
        g = float(tgen.loc[[int(i) for i in sel if int(i) in tgen.index]].median())
        rec["available_thermal_mw"] = round(avail, 1)
        rec["dispatched_thermal_mw"] = round(g, 1)
        rec["utilisation_pct"] = round(100.0 * g / avail, 1) if avail else None
        rec["available_below_gate_mw"] = round(lt, 1)
        # THE NUMBER THIS PROBE EXISTS FOR: capacity the LP could still buy for
        # less than the gate. While it is positive the energy dual CANNOT reach
        # the gate, whatever is done to the pricing layer.
        rec["idle_below_gate_mw"] = round(lt - g, 1)
        # Reported as MW, deliberately NOT reduced to a boolean: any cutoff
        # would be a magic number (rule 5 [R-NO-MAGIC]) and the quantity is
        # monotone anyway — the more sub-gate capacity sits idle, the further
        # out of reach the gate is for anything done to the pricing layer.
        rec["idle_below_gate_pct_of_available"] = (
            round(100.0 * (lt - g) / avail, 1) if avail else None
        )
        out["windows"][label] = rec
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_nyiso242_tail_reachability.json"),
    )
    args = ap.parse_args()

    out = {"bundle": str(BUNDLE.relative_to(REPO)), "threshold": THRESHOLD, "years": {}}
    for y in args.years:
        rec = run_year_probe(y)
        out["years"][str(y)] = rec
        print(f"\n=== {y} ===")
        for label, w in rec["windows"].items():
            print(
                f"  {label:15s} n={w['hours']:5d}  avail={w['available_thermal_mw']:8.0f}  "
                f"gen={w['dispatched_thermal_mw']:8.0f}  util={w['utilisation_pct']:5.1f}%  "
                f"IDLE<${THRESHOLD:.0f}={w['idle_below_gate_mw']:8.0f} MW "
                f"({w['idle_below_gate_pct_of_available']}% of available)"
            )
            print(f"      bands: {w['available_by_band_mw']}")

    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
