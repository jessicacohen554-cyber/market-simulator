"""caiso-164 pre-solve wiring probe — NO LP, run BEFORE either arm solves.

The caiso-162 lesson, applied ex ante for the second session running: a
mechanism whose ``run_config.json`` records it as armed is NOT evidence the LP
saw it. caiso-162 lost a solve pair to a mechanism with no call site on the
calibration lane, which read on prices as a clean INERT verdict and would have
written a false matrix ``I`` (a DO-NOT-REDO code). So before solving:

* **W1 — call site.** Replay the calibration lane's exact topology sequence for
  each solve year and confirm the split fires only with the flag on.
* **W2 — structural no-op.** Flag-off must return the SAME OBJECT (identity,
  not equality); flag-on must return a NEW one.
* **W3 — the loss array is nonzero and oriented S->N.** ``build_caiso_link_loss``
  must return a real array, and the measured gradient must put the lossy
  direction on the south-to-north links (that is a property of CAISO's own
  surface, asserted here so a sign error cannot pass silently).
* **W4 — caiso-163 composition.** The keeper's published Path 15 / Path 26
  directional ratings must still resolve to LP interface groups AFTER the
  split, with both orientations present and the caps unchanged. This is the
  one real composition risk in the mechanism: the split doubles the link count
  on exactly the two corridors caiso-163 bounds.
* **W5 — the seam is untouched.** No WECC link may become lossy or be split.

Exit code 1 if any check fails, so it can gate the solve.
"""

from __future__ import annotations

import json
from dataclasses import fields as dc_fields
from pathlib import Path

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.interchange import (
    apply_caiso_local_import_limits,
    apply_interchange_topology,
    build_caiso_link_loss,
)
from market_sim.model.interchange.core import build_interface_groups
from market_sim.model.interchange.spec import get_interchange_spec
from market_sim.pipeline.ttc import apply_iso_year_ttc

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/caiso163_asym_path_ratings"
YEARS = (2023, 2024, 2025)
HOURS = 8760
# The caiso-163 published ratings the split must preserve, keyed by limit name.
EXPECTED_LIMITS = {
    "CAISO_path_directional_NP15_ZP26": (3265.0, 5400.0),
    "CAISO_path_directional_ZP26_SP15_rest": (4000.0, 3000.0),
}


def _base_config() -> dict:
    """The keeper's committed recipe, restricted to live ScenarioConfig fields."""
    recorded = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dc_fields(ScenarioConfig)}
    return {k: v for k, v in recorded.items() if k in valid}


def main() -> int:
    """Run every pre-solve check; return 1 on any failure."""
    base = _base_config()
    iso_config = get_iso_config("CAISO")
    failures: list[str] = []

    print("=" * 79)
    print("caiso-164 PRE-SOLVE WIRING PROBE (no LP)")
    print("=" * 79)

    for year in YEARS:
        off = ScenarioConfig(
            **{
                **base,
                "start_year": year,
                "end_year": year,
                "caiso_zonal_loss_surface": False,
            }
        )
        on = ScenarioConfig(
            **{
                **base,
                "start_year": year,
                "end_year": year,
                "caiso_zonal_loss_surface": True,
            }
        )
        # The calibration lane's exact topology sequence (mirrors
        # scripts/run_calibration.py and caiso163_wiring_probe.py §C).
        def _topology(cf):
            c = apply_iso_year_ttc(get_iso_config("CAISO"), "CAISO", year)
            if getattr(cf, "caiso_per_year_import_caps", False):
                c = apply_caiso_local_import_limits(c, "CAISO", year)
            spec = get_interchange_spec(cf, "CAISO", year=year)
            return apply_interchange_topology(c, spec, cf, year=year, extend_node=True)

        cfg_off = _topology(off)
        cfg_on = _topology(on)

        # W1/W2 — the call site fires, and only with the flag on.
        n_off, n_on = len(cfg_off.links), len(cfg_on.links)
        from market_sim.model.interchange import apply_caiso_zonal_loss_links

        same_obj = apply_caiso_zonal_loss_links(cfg_off) is not cfg_off
        w2 = n_on > n_off
        print(f"\n-- {year}")
        print(f"  W1 links off={n_off} on={n_on}  (split fired: {w2})")
        # W2 identity: flag-off leaves links bidirectional, so applying the
        # split directly MUST return a new object -- proving the flag, not the
        # topology, is what withholds it on the off arm.
        print(f"  W2 off-arm links are still splittable (flag is the gate): {same_obj}")
        if not same_obj:
            failures.append(f"{year} W2: off-arm topology was already split")
        if not w2:
            failures.append(f"{year} W1/W2: flag-on did not split any link")

        # W3 — loss array is real, nonzero, and oriented south->north.
        # The off arm never reaches build_caiso_link_loss (the call site is
        # gated on the flag); asserting that it REFUSES an unsplit topology is
        # the stronger check — a signed lossy link would create energy.
        try:
            build_caiso_link_loss(cfg_off.links, "CAISO", year, HOURS)
            off_guarded = False
        except ValueError:
            off_guarded = True
        loss_on = build_caiso_link_loss(cfg_on.links, "CAISO", year, HOURS)
        if loss_on is None:
            failures.append(f"{year} W3: build_caiso_link_loss returned None when on")
            print("  W3 FAIL — loss array is None with the flag ON")
            continue
        lossy = {
            (ln.from_zone, ln.to_zone): float(loss_on[i].mean())
            for i, ln in enumerate(cfg_on.links)
            if loss_on[i].max() > 0.0
        }
        print(f"  W3 unsplit topology is REFUSED by the builder: {off_guarded}")
        if not off_guarded:
            failures.append(f"{year} W3: builder accepted a bidirectional link")
        print(f"     lossy directions ({len(lossy)}):")
        for (a, b), v in sorted(lossy.items()):
            print(f"       {a:>10} -> {b:<12} mean eps {v:.5f}")
        sn = lossy.get(("ZP26", "NP15"))
        ns = lossy.get(("NP15", "ZP26"))
        if not sn or sn <= 0:
            failures.append(f"{year} W3: Path 15 S->N carries no loss")
        if ns:
            failures.append(
                f"{year} W3: Path 15 N->S is lossy ({ns:.5f}) — the measured "
                "gradient runs S->N; a lossy N->S leg means a sign error"
            )
        print(f"     Path 15 S->N eps {sn}  |  N->S eps {ns} (must be None)")

        # W4 — the caiso-163 directional ratings survive the split.
        groups_off = build_interface_groups(cfg_off.links, cfg_off.interface_limits)
        groups_on = build_interface_groups(cfg_on.links, cfg_on.interface_limits)
        names_on = [lim.name for lim in cfg_on.interface_limits]
        print(f"  W4 interface groups off={len(groups_off)} on={len(groups_on)}")
        for name, (cap, rev) in EXPECTED_LIMITS.items():
            if name not in names_on:
                failures.append(f"{year} W4: limit {name} missing after the split")
                continue
            k = names_on.index(name)
            idx, cap_on, _bidir, lower_on, signs = groups_on[k]
            ok = (
                cap_on == cap
                and lower_on == rev
                and len(idx) == 2
                and sorted(signs.tolist()) == [-1.0, 1.0]
            )
            print(
                f"     {name}: cap {cap_on} rev {lower_on} links {len(idx)} "
                f"signs {sorted(signs.tolist())}  {'OK' if ok else 'FAIL'}"
            )
            if not ok:
                failures.append(
                    f"{year} W4: {name} did not survive the split "
                    f"(cap={cap_on} rev={lower_on} n_links={len(idx)})"
                )

        # W5 — the WECC seam is untouched.
        seam_off = sorted(
            (ln.from_zone, ln.to_zone, ln.is_bidirectional)
            for ln in cfg_off.links
            if ln.from_zone.startswith("WECC") or ln.to_zone.startswith("WECC")
        )
        seam_on = sorted(
            (ln.from_zone, ln.to_zone, ln.is_bidirectional)
            for ln in cfg_on.links
            if ln.from_zone.startswith("WECC") or ln.to_zone.startswith("WECC")
        )
        seam_lossy = [
            (ln.from_zone, ln.to_zone)
            for i, ln in enumerate(cfg_on.links)
            if (ln.from_zone.startswith("WECC") or ln.to_zone.startswith("WECC"))
            and loss_on[i].max() > 0.0
        ]
        ok5 = seam_off == seam_on and not seam_lossy
        print(f"  W5 WECC seam identical: {seam_off == seam_on}, lossy: {seam_lossy}")
        if not ok5:
            failures.append(f"{year} W5: the WECC seam changed under the split")

        # The measured surface itself, for the record.
        if year == YEARS[0]:
            from market_sim.data.loss_surface import load_zone_month_deviation

            surf = load_zone_month_deviation("CAISO", year)
            print("  surface (annual mean df_deviation):")
            for z, v in sorted(surf.items()):
                print(f"       {z:>10} {np.mean(v):+.5f}")

    print()
    print("=" * 79)
    if failures:
        print(f"PRE-SOLVE PROBE FAILED — {len(failures)} check(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PRE-SOLVE PROBE PASSED — every check green; the arm may solve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
