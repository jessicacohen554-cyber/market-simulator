"""miso-117 PHASE 0: does ``measured_ct_heat_rates`` REACH MISO's fleet seam?

No LP. This is the ERCOT-146 wiring check run before any solve is spent: there,
the ``measured_ct_heat_rates`` consumer is ``eia860._rows_to_generators``, but
under ``use_campd_bins`` ERCOT's thermal fleet comes from the curated
``load_campd_bins`` sheet, which never receives the kwarg — so the flag was
INERT BY WIRING and an A/B replay would have produced a bit-identical bundle
(matrix cell stamped ``I``, no solve spent).

MISO runs the same ``use_campd_bins=True`` / ``plant_level_fleet=True``
configuration, so the question has to be asked here too — but MISO takes the
OTHER branch of :func:`market_sim.data.fleet.assembly.load_or_synthesize_bins`:
only ``iso == "ERCOT"`` reads the curated sheet, and every other ISO SYNTHESIZES
its bins from ``load_fleet_from_csv(..., measured_ct_heat_rates=...)``. This
probe verifies that empirically rather than trusting the read, exactly as
``_neiso70_flag_fidelity.py`` did for NEISO.

**The base arm is the KEEPER's own configuration**, rebuilt from
``results/calibration/miso109_hy_level_B/run_config.json`` — not a default
``ScenarioConfig``. miso-116 §3 withdrew two miso-115 results that came from a
probe reading the model with a different configuration than the keeper solved
(``measured_chp_heat_rates`` defaults False; the MISO keeper ARMS it), and
neither error was visible in the reported ratio. The single delta measured here
is therefore keeper + ``measured_ct_heat_rates=True`` vs keeper as-solved.

Reports per fleet vintage year: generators moved, MW moved, capacity-weighted
heat-rate delta on ``CT_PEAKER``, and the per-plant rows. A zero diff means the
arm is inert by wiring and must be stamped ``I`` WITHOUT spending a solve.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso117_flag_fidelity.py
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
from market_sim.data.fleet import (  # noqa: E402
    build_base_fleet,
    load_fleet_from_csv,
    load_or_synthesize_bins,
)
from market_sim.data.fleet.campd_bins import measured_ct_heat_rates  # noqa: E402

ISO = "MISO"
KEEPER = REPO / "results/calibration/miso109_hy_level_B"
YEARS = (2023, 2024, 2025)
CT_CLASS = "CT_PEAKER"


def keeper_config(**overrides) -> ScenarioConfig:
    """Rebuild the KEEPER's ScenarioConfig, with ``overrides`` applied on top.

    Only fields the shipped ScenarioConfig still declares are carried, so a
    stale key in the committed snapshot cannot break the probe.
    """
    snap = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    kw = {k: v for k, v in snap.items() if k in valid}
    kw.update(overrides)
    return ScenarioConfig(**kw)


def build(year: int, **overrides) -> pd.DataFrame:
    """Build the base fleet through the runner's own chain; return a plant table."""
    cfg = keeper_config(**overrides)
    iso_config = get_iso_config(ISO)
    zone_names = [z.name for z in iso_config.zones]
    bins = load_or_synthesize_bins(cfg, ISO, iso_config, [])
    fleet = build_base_fleet(
        bins, ISO, iso_config, zone_names, cfg, [], [], year, confirmed_exits=[]
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
    df = pd.DataFrame(rows)
    # (plant_code, name, plant_group) is NOT unique — MISO's nuclear plants
    # carry several identically-named units, and a plain merge on those three
    # columns fans them out cartesian-style, pairing base row i against arm row
    # j and reporting a spurious +/-13.5 MMBtu/MWh "move" on a class the flag
    # cannot touch. Number the occurrences within each key so the merge pairs
    # like with like (the fleet build is deterministic, so occurrence order is
    # stable across arms — asserted in compare()).
    df["dup"] = df.groupby(["plant_code", "name", "plant_group"]).cumcount()
    return df


def capwt(df: pd.DataFrame) -> float:
    """Capacity-weighted heat rate of ``df`` (nan when it has no capacity)."""
    if df.empty or df["pmax_mw"].sum() <= 0:
        return float("nan")
    return float(np.average(df["heat_rate"], weights=df["pmax_mw"]))


def compare(base: pd.DataFrame, arm: pd.DataFrame, label: str) -> pd.DataFrame:
    """Print the base-vs-arm fleet heat-rate diff; return the moved rows."""
    print("=" * 78)
    print(f"ARM: {label}")
    print("=" * 78)
    if len(base) != len(arm):
        print(f"  !! generator count differs: base {len(base)} vs arm {len(arm)}")
    key = ["plant_code", "name", "plant_group", "dup"]
    # Alignment kill: if the two builds emit the fleet in a different order the
    # occurrence numbering pairs the wrong rows and every delta below is noise.
    aligned = base[key].equals(arm[key])
    print(f"  row-key alignment (base vs arm, positional): {aligned}")
    if not aligned:
        print("  !! ARMS NOT ALIGNED — deltas below are not trustworthy")
    m = base.merge(arm, on=key, how="outer", suffixes=("_base", "_arm"))
    m["delta"] = m["heat_rate_arm"] - m["heat_rate_base"]
    moved = m[m["delta"].abs() > 1e-9]
    print(
        f"  generators moved: {len(moved)} of {len(m)}; "
        f"MW moved {moved['pmax_mw_arm'].sum():,.1f} of {m['pmax_mw_arm'].sum():,.1f}"
    )
    if moved.empty:
        print("  >>> ZERO DIFF — INERT BY WIRING. Stamp I, do NOT spend a solve.")
        return moved
    print("  >>> FLAG IS LIVE at the fleet seam.")
    b = base[base["plant_group"] == CT_CLASS]
    a = arm[arm["plant_group"] == CT_CLASS]
    print(
        f"  {CT_CLASS}: cap-wt HR {capwt(b):.4f} -> {capwt(a):.4f} MMBtu/MWh "
        f"({100 * (capwt(a) - capwt(b)) / capwt(b):+.2f} %); "
        f"class MW {b['pmax_mw'].sum():,.1f} -> {a['pmax_mw'].sum():,.1f}"
    )
    dearer = moved[moved["delta"] > 0]
    cheaper = moved[moved["delta"] < 0]
    print(
        f"  direction: {len(cheaper)} rows / {cheaper['pmax_mw_arm'].sum():,.1f} MW "
        f"CHEAPER, {len(dearer)} rows / {dearer['pmax_mw_arm'].sum():,.1f} MW DEARER"
    )
    # Plant-grain roll-up: one LP unit per plant-group, so per-plant is the
    # grain the artifact is keyed on.
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
    return moved


def plant_grain(year: int) -> None:
    """Print the PLANT-grain CT_PEAKER heat rate, on and off, for ``year``.

    The tranche-grain figure above is not comparable with miso-115 §4's
    published model value (12.37 MMBtu/MWh): tranching splits every plant into
    a rising offer curve whose top ``peak`` block carries a startup-amortised
    rate of 30-37 MMBtu/MWh, so a cap-weighted average over tranches sits well
    above the machine rate. This leg reads the same seam the flag enters —
    ``load_fleet_from_csv`` — which is the grain miso-115/116 measured at, and
    the keeper's own ``measured_chp_heat_rates`` is carried in both arms.
    """
    cfg = keeper_config()
    out = {}
    for label, ct_flag in (("keeper (off)", False), ("armed (on)", True)):
        gens = load_fleet_from_csv(
            ISO,
            year=year,
            measured_chp_heat_rates=cfg.measured_chp_heat_rates,
            measured_ct_heat_rates=ct_flag,
        )
        df = pd.DataFrame(
            [
                {
                    "plant_code": int(g.plant_code),
                    "plant_group": str(g.plant_group),
                    "pmax_mw": float(g.pmax_mw),
                    "heat_rate": float(g.heat_rate),
                }
                for g in gens
                if g.plant_code is not None
            ]
        )
        out[label] = df
    b = out["keeper (off)"]
    a = out["armed (on)"]
    bc = b[b["plant_group"] == CT_CLASS]
    ac = a[a["plant_group"] == CT_CLASS]
    art = measured_ct_heat_rates(ISO)
    cov = bc[bc["plant_code"].isin(art)]
    print(
        f"  PLANT grain (load_fleet_from_csv, the miso-115 §4 basis): "
        f"{CT_CLASS} cap-wt HR {capwt(bc):.4f} -> {capwt(ac):.4f} MMBtu/MWh "
        f"({100 * (capwt(ac) - capwt(bc)) / capwt(bc):+.2f} %)"
    )
    print(
        f"    artifact coverage: {len(cov)} of {len(bc)} class plants, "
        f"{cov['pmax_mw'].sum():,.1f} of {bc['pmax_mw'].sum():,.1f} MW "
        f"({100 * cov['pmax_mw'].sum() / bc['pmax_mw'].sum():.1f} %)"
    )
    covd = ac[ac["plant_code"].isin(art)]
    print(
        f"    covered subset only: {capwt(cov):.4f} -> {capwt(covd):.4f} "
        f"MMBtu/MWh ({100 * (capwt(covd) - capwt(cov)) / capwt(cov):+.2f} %); "
        f"uncovered stays {capwt(bc[~bc['plant_code'].isin(art)]):.4f}"
    )


def main() -> int:
    """Run the per-year fleet builds and print the arm's fidelity diff."""
    art = measured_ct_heat_rates(ISO)
    print(f"Artifact: measured_ct_heat_rates('{ISO}') -> {len(art)} plant entries")
    print(f"Keeper config from {KEEPER} (run_config.scenario_config)\n")
    keeper_snap = json.loads((KEEPER / "run_config.json").read_text())[
        "scenario_config"
    ]
    for k in ("measured_ct_heat_rates", "measured_chp_heat_rates", "use_campd_bins"):
        print(f"  keeper {k} = {keeper_snap.get(k, 'ABSENT')}")
    print()
    for year in YEARS:
        print(f"\n################ fleet vintage year {year} ################")
        plant_grain(year)
        base = build(year)
        arm = build(year, measured_ct_heat_rates=True)
        moved = compare(base, arm, f"keeper + measured_ct_heat_rates=True ({year})")
        if not moved.empty:
            covered = set(moved["plant_code"]) & set(art)
            print(
                f"  artifact coverage: {len(covered)} of {len(art)} artifact plants "
                f"moved this vintage"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
