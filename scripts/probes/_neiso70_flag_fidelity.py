"""neiso-70 STEP 2 pre-check: do the two flags actually REACH NEISO's fleet?

No LP. This is the ERCOT-146 lesson run before any solve is spent: there, the
`measured_ct_heat_rates` consumer is ``eia860._rows_to_generators``, but under
``use_campd_bins`` ERCOT's thermal fleet comes from the curated
``load_campd_bins`` sheet, which never receives the kwarg — so the flag was
INERT BY WIRING and an A/B replay would have produced a bit-identical bundle
(matrix cell stamped ``I``, no solve spent).

The NEISO keeper runs the SAME ``use_campd_bins=True`` /
``plant_level_fleet=True`` configuration, so the question has to be asked here
too — but NEISO takes the OTHER branch of
:func:`market_sim.data.fleet.assembly.load_or_synthesize_bins`: only
``iso == "ERCOT"`` reads the curated sheet, and every other ISO SYNTHESIZES its
bins from ``load_fleet_from_csv(..., measured_ct_heat_rates=...,
measured_chp_heat_rates=...)``. This probe verifies that empirically rather
than trusting the read, by rebuilding the runner's own fleet chain
(``load_or_synthesize_bins`` -> ``build_base_fleet``) three times at the
keeper's ScenarioConfig — flags off, CT on, CHP on — and diffing the heat rates
the LP would actually charge.

Reports per arm: generators moved, MW moved, capacity-weighted heat-rate delta
on the target class, and the per-plant rows. A zero diff here means the arm is
inert by wiring and must be stamped ``I`` WITHOUT spending a solve.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_neiso70_flag_fidelity.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import build_base_fleet, load_or_synthesize_bins  # noqa: E402

ISO = "NEISO"
KEEPER = REPO / "results/calibration/neiso61_netrev_margin"
YEAR = 2023
CT_CLASS = "CT_PEAKER"
CHP_CLASSES = ("CC_CHP", "CT_CHP")


def keeper_config(**overrides) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig, with ``overrides`` applied on top.

    Only fields the shipped ScenarioConfig still declares are carried, so a
    stale key in the committed snapshot cannot break the probe.
    """
    snap = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    kw = {k: v for k, v in snap.items() if k in valid}
    kw.update(overrides)
    return ScenarioConfig(**kw)


def build(**overrides) -> pd.DataFrame:
    """Build the base fleet through the runner's own chain; return a plant table."""
    cfg = keeper_config(**overrides)
    iso_config = get_iso_config(ISO)
    zone_names = [z.name for z in iso_config.zones]
    bins = load_or_synthesize_bins(cfg, ISO, iso_config, [])
    fleet = build_base_fleet(
        bins, ISO, iso_config, zone_names, cfg, [], [], YEAR, confirmed_exits=[]
    )
    rows = [
        {
            "plant_code": int(g.plant_code or 0),
            "name": g.name,
            "plant_group": g.plant_group,
            "pmax_mw": float(g.pmax_mw),
            "heat_rate": float(g.heat_rate),
        }
        for g in fleet
    ]
    return pd.DataFrame(rows)


def capwt(df: pd.DataFrame) -> float:
    """Capacity-weighted heat rate of ``df`` (nan when it has no capacity)."""
    if df.empty or df["pmax_mw"].sum() <= 0:
        return float("nan")
    return float(np.average(df["heat_rate"], weights=df["pmax_mw"]))


def compare(base: pd.DataFrame, arm: pd.DataFrame, label: str, classes) -> None:
    """Print the base-vs-arm fleet heat-rate diff for ``classes``."""
    print("=" * 78)
    print(f"ARM: {label}")
    print("=" * 78)
    if len(base) != len(arm):
        print(f"  !! generator count differs: base {len(base)} vs arm {len(arm)}")
    key = ["plant_code", "name", "plant_group"]
    m = base.merge(arm, on=key, how="outer", suffixes=("_base", "_arm"))
    m["delta"] = m["heat_rate_arm"] - m["heat_rate_base"]
    moved = m[m["delta"].abs() > 1e-9]
    print(
        f"  generators moved: {len(moved)} of {len(m)}; "
        f"MW moved {moved['pmax_mw_arm'].sum():,.1f} of {m['pmax_mw_arm'].sum():,.1f}"
    )
    if moved.empty:
        print("  >>> ZERO DIFF — INERT BY WIRING. Stamp I, do NOT spend a solve.")
        return
    print("  >>> FLAG IS LIVE at the fleet seam.")
    for cls in classes:
        b = base[base["plant_group"] == cls]
        a = arm[arm["plant_group"] == cls]
        if b.empty and a.empty:
            continue
        print(
            f"  {cls}: cap-wt HR {capwt(b):.4f} -> {capwt(a):.4f} MMBtu/MWh "
            f"({100 * (capwt(a) - capwt(b)) / capwt(b):+.2f} %); "
            f"class MW {b['pmax_mw'].sum():,.1f} -> {a['pmax_mw'].sum():,.1f}"
        )
    print("\n  moved rows (by |delta| x MW):")
    moved = moved.assign(impact=moved["delta"].abs() * moved["pmax_mw_arm"])
    print(
        moved.sort_values("impact", ascending=False)[
            [
                "plant_code",
                "name",
                "plant_group",
                "pmax_mw_arm",
                "heat_rate_base",
                "heat_rate_arm",
                "delta",
            ]
        ].to_string(index=False)
    )
    print(
        f"\n  classes touched: "
        f"{sorted(moved['plant_group'].dropna().unique().tolist())}"
    )


def main() -> int:
    """Run the three fleet builds and print both arms' fidelity diffs."""
    print(f"Keeper config from {KEEPER}, fleet vintage year {YEAR}\n")
    base = build(measured_ct_heat_rates=False, measured_chp_heat_rates=False)
    ct = build(measured_ct_heat_rates=True, measured_chp_heat_rates=False)
    chp = build(measured_ct_heat_rates=False, measured_chp_heat_rates=True)
    compare(base, ct, "measured_ct_heat_rates=True", (CT_CLASS,))
    compare(base, chp, "measured_chp_heat_rates=True", CHP_CLASSES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
