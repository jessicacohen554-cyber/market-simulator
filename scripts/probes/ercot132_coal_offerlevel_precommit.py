"""ERCOT-132 leg B: ex-ante capture of the coal offer-LEVEL arm (no LP).

The ERCOT-122 offer-level controlled refutation (``DIAGNOSIS-ercot122`` §5.1,
run under owner overrule of that section's recommend-and-STOP) replaces the
keeper's coal ``econ_low``/``peak`` heat-rate multipliers with the measured
fleet-representative levels from
``data/raw/_validation-source/offer_curve_dam_hrmults_coal_yearly.json``
(§5.3: the ``econ_low``/``peak_typical`` pair, 100 % capacity coverage and
LOYO-stable; §5.2: the pooled ``econ_high`` 2.856 is NOT re-armed).

This probe reproduces ``DIAGNOSIS-ercot122`` §3's model-side coal band table
(``scripts/probes/ercot117_coal_gas_ranking.py`` §D) under BASE and ARM so the
pre-commit can state the arm's direction and magnitude in $/MWh **before** the
solve runs. It builds the fleet and aborts before HiGHS — no LP is solved and
nothing is written to the repo.

Usage::

    python scripts/probes/ercot132_coal_offerlevel_precommit.py --year 2023
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import ercot117_coal_gas_ranking as e117  # noqa: E402

DEFAULT_BUNDLE = "results/calibration/ercot129_conditional"
COAL_ARTIFACT = (
    "data/raw/_validation-source/offer_curve_dam_hrmults_coal_yearly.json"
)
YEARS = (2023, 2024, 2025)


def measured_levels() -> dict[str, dict[str, float]]:
    """The §5.3 fleet-representative coal offer level (TARGET resolved bands).

    ``econ_low`` -> the artifact's ``econ_low`` (rel <= 0.33 competitive body);
    ``peak`` -> the artifact's ``peak_typical`` (per-resource MEDIAN DAILY
    top-of-curve, the stable variant of the mode-B ``peak`` ERCOT-119 proved
    inert). Both carry 100 % capacity coverage in every year. The config
    surface holds ONE number per band, so each is the mean of the three
    measured delivery years — a summary of an already-stable measured series
    (spreads 0.025-0.107 hr-mult), not a refit against any residual.

    ``econ_high`` is deliberately ABSENT: §5.2 forbids re-arming the pooled
    2.856, and §1 refutes the measured ``econ_high`` as fleet-representative in
    every year (21-47 % capacity coverage). ``committed`` is absent because the
    band was destroyed by the 2026-07-22 raw slimming (§2). Both therefore keep
    the keeper's resolved value.
    """
    d = json.loads((REPO / COAL_ARTIFACT).read_text())
    out: dict[str, dict[str, float]] = {}
    for cls in ("COAL_LIGNITE", "COAL_PRB"):
        lo = [float(d[str(y)][cls]["econ_low"]) for y in YEARS]
        pk = [float(d[str(y)][cls]["peak_typical"]) for y in YEARS]
        out[cls] = {
            "econ_low": round(sum(lo) / len(lo), 4),
            "peak": round(sum(pk) / len(pk), 4),
        }
    return out


def arm_offer_curve(bundle: Path) -> dict[str, dict[str, float]]:
    """The arm's ``--offer-curve-json`` payload, built off the keeper's meta.

    Two corrections the naive "pass the measured numbers" spec gets wrong, both
    verified by capture rather than assumed:

    1. ``--offer-curve-json`` REPLACES ``offer_curve_overrides`` wholesale, so
       the keeper's CC_REGULAR / CC_CHP entries must be carried through
       verbatim or the arm silently re-prices the gas fleet too and stops being
       a single-delta coal probe.
    2. The keeper's separate ``offer_curve_deltas`` are added ON TOP of the
       overrides (COAL_PRB ``econ_low`` -0.30 / ``peak`` +0.082, COAL_LIGNITE
       ``econ_low`` +0.076). The arm's premise is that the MEASURED level
       replaces the FITTED one, so each written value is ``measured - delta``
       and the RESOLVED band lands on the measured level exactly —
       arithmetically identical to zeroing the coal run delta and setting the
       base to the measured value.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    payload = {
        cls: dict(bands)
        for cls, bands in (meta.get("offer_curve_overrides") or {}).items()
    }
    deltas = meta.get("offer_curve_deltas") or {}
    for cls, bands in measured_levels().items():
        d = deltas.get(cls) or {}
        payload[cls] = {
            band: round(target - float(d.get(band, 0.0)), 6)
            for band, target in bands.items()
        }
    return payload


def capture_with(bundle: Path, year: int, overrides: dict | None) -> dict:
    """``e117.capture`` with an ``offer_curve_overrides`` injection."""
    import replay_keeper  # noqa: F401  (adds scripts to path, pins warmstart)
    import run_calibration_full as rcf

    rc_mod = sys.modules[rcf.run_year.__module__]
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = REPO / "scratch" / "ercot132_capture_junk"
    kwargs["note"] = "ERCOT-132 leg B ex-ante capture (aborts before solve)"
    if overrides is not None:
        kwargs["offer_curve_overrides"] = overrides

    grabbed: dict = {}
    real = rc_mod.run_energy_solve

    def _patched(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
        import numpy as np

        grabbed["fleet"] = fleet
        grabbed["fa"] = fleet_arrays
        grabbed["config"] = config
        grabbed["mc_base"] = np.asarray(mc_base)
        adj = kw.get("mc_bid_adjust")
        grabbed["mc_bid_adjust"] = None if adj is None else np.asarray(adj)
        raise e117._StopAfterCapture()

    rc_mod.run_energy_solve = _patched
    try:
        rcf.solve_and_persist(**kwargs)
    except e117._StopAfterCapture:
        pass
    finally:
        rc_mod.run_energy_solve = real
    if "fleet" not in grabbed:
        raise SystemExit(f"{year}: capture failed (run_energy_solve never reached)")
    return grabbed


def main(argv: list[str] | None = None) -> int:
    """Print the BASE vs ARM coal band table and the arm's offer spec."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=DEFAULT_BUNDLE)
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args(argv)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)

    bundle = REPO / args.bundle
    target = measured_levels()
    ov = arm_offer_curve(bundle)
    print("=" * 78)
    print("ERCOT-132 leg B — the §5.1 arm's offer-level spec (from §5.3's pair)")
    print("=" * 78)
    print("TARGET resolved coal bands (measured):")
    print(json.dumps(target, indent=1))
    print("\n--offer-curve-json payload (measured - keeper delta; CC carried verbatim):")
    print(json.dumps(ov, indent=1))

    print(f"\n[capture] {args.year} BASE (keeper curve) ...", flush=True)
    g_base = capture_with(bundle, args.year, None)
    base = e117.coal_band_table(g_base)
    print(f"[capture] {args.year} ARM (measured level) ...", flush=True)
    g_arm = capture_with(bundle, args.year, ov)
    arm = e117.coal_band_table(g_arm)

    print("\n--- resolved offer_curve_by_group (BASE -> ARM) ---")
    for cls in ("COAL_LIGNITE", "COAL_PRB", "CC_REGULAR", "CC_CHP"):
        b = g_base["config"].offer_curve_by_group.get(cls)
        a = g_arm["config"].offer_curve_by_group.get(cls)
        print(f"  {cls}:")
        print(f"    base {b}")
        print(f"    arm  {a}")

    print(f"\n--- {args.year} coal bands, cap-weighted P1 bid $/MWh ---")
    cmp = base[["pmax_mw", "summer_bid", "shoulder_bid"]].join(
        arm[["summer_bid", "shoulder_bid"]], lsuffix="_base", rsuffix="_arm"
    )
    cmp["d_summer"] = cmp["summer_bid_arm"] - cmp["summer_bid_base"]
    cmp["d_shoulder"] = cmp["shoulder_bid_arm"] - cmp["shoulder_bid_base"]
    print(cmp.round(2).to_string())

    cheaper = cmp[cmp["d_summer"] < 0]["pmax_mw"].sum()
    dearer = cmp[cmp["d_summer"] > 0]["pmax_mw"].sum()
    print(f"\nMW made CHEAPER (summer): {cheaper:,.0f}")
    print(f"MW made DEARER  (summer): {dearer:,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
