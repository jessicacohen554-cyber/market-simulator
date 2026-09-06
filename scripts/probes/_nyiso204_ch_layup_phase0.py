"""nyiso-204 phase 0 — the Capital_Hudson lay-up exclusion, sized with ZERO LP.

Rule 29 step 0: this GATES the solve. Nothing here runs an LP.

THE ARM (not taken here): add Danskammer 2480 + Roseton 8006 to the
``exclude_plant_codes`` column of the Capital_Hudson ``ST_GAS`` ``tmax 31.1``
row of ``data/raw/reference/reliability_floor_coeffs_NYISO.csv`` — the
already-armed, already-adjudicated ``reliability_floor_plant_exclusions``
channel (nyiso-140 + owner ruling 2026-08-16), which on this keeper carries
exactly one entry (Port Jefferson 2517).

WHY THE PRECEDENT DOES NOT TRANSFER MECHANICALLY, which is what this probe is
for. nyiso-140 excluded from a Long_Island PERSISTENT 24 h BASE limb with
``distribution=pro_rata``, where dropping a unit simply stops flooring it. The
live Capital_Hudson limb is neither:

  * it is the ``tmax 31.1 / floor_pct 0.0973`` HOT-DAY STEP (the ``CH_ST_ev``
    ramp family is disabled on the keeper via ``reliability_floor_overrides``;
    the ``tmin`` limb ships ``enabled=False``), so its driver is a design-cooling-day
    commitment, not a persistent baseline; and
  * its ``distribution`` column is EMPTY, which defaults to ``cheapest_first``
    (``iso_configs.ReliabilityFloorSpec.distribution``), so the limb sizes a
    ZONAL target ``0.0973 × Σ available capacity`` and fills it cheapest-first
    by heat rate, each unit capped at its own availability.

Excluding a plant therefore does TWO things, not one (``core.py``
``_distribute_group_floor``: ``target = frac × avail_cap[rows].sum(0)`` over the
POST-exclusion rows, then ``order = rows`` sorted by heat rate): it SHRINKS the
target's capacity base AND removes the unit from the fill order. The floor can
therefore REDISTRIBUTE onto the other Capital_Hudson steam units. That
redistribution is the arm's real footprint and is measured here.

METHOD. Rather than re-implement the limb's day gate, min-event bridging and
cheapest-first fill, this probe calls the SHIPPED engine
(``model.interchange.core.inject_reliability_floor``) twice on the same
reconstructed fleet — once with the keeper's specs, once with 2480 + 8006 added
to the target row's ``exclude_plant_codes`` — and diffs ``min_gen``. The
redistribution is then exact by construction, not by my arithmetic.

OUTPUTS, per year 2023/2024/2025:
  (a) who is in the cheapest-first fill at 0.0973, the zonal target MW, and how
      much of it 2480 + 8006 currently absorb;
  (b) the REDISTRIBUTION: which units take the freed target and how much;
  (c) the arm's own REACHABILITY BOUND in MWh — the floor energy it can move —
      stated BEFORE the screen.
  (d) the rule-17 [R-FLOOR-WINDOW] DRIVER test, which is the argument the hot
      step needs and the persistent-base precedent does NOT supply: what do 2480
      and 8006 actually do ON THE LIMB'S OWN FLAGGED HOURS? nyiso-140's Port
      Jefferson RAN on hot days (P(on) 0.932 at tmax >= 30 C, mean 166 MW) — it
      was in the wrong limb, not a dead plant. If 2480/8006 also run on design
      cooling days, this arm must NOT go, whatever their annual conduct says.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace as _dc_replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = ROOT / "results" / "calibration" / "nyiso202_startup_aware"
KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
YEARS = (2023, 2024, 2025)
ZONE = "Capital_Hudson"
KLASS = "ST_GAS"
DRIVER = "tmax"
THRESHOLD = 31.1
CANDIDATES = (2480, 8006)  # Danskammer, Roseton
OUT = ROOT / "results" / "calibration" / "_nyiso204_ch_layup_phase0.json"


def _ch_step_spec(specs):
    """The one live Capital_Hudson ST_GAS limb: the tmax 31.1 standalone step."""
    hits = [
        s
        for s in specs
        if s.zone == ZONE
        and s.plant_class == KLASS
        and s.driver == DRIVER
        and abs(float(s.threshold) - THRESHOLD) < 1e-9
        and getattr(s, "enabled", True)
        and not (getattr(s, "ramp_group", "") or "")
    ]
    if len(hits) != 1:
        raise SystemExit(
            f"expected exactly 1 live {ZONE}/{KLASS}/{DRIVER}@{THRESHOLD} step, got {len(hits)}"
        )
    return hits[0]


def _run_floor(state, specs, year):
    """Apply ONLY these floor specs to a fleet reset to ``pmin``; return min_gen.

    THE RESET IS LOAD-BEARING AND WAS A REAL BUG IN THE FIRST CUT OF THIS PROBE.
    ``reconstruct_bundle_fleet`` runs the solve path's own preamble, which
    ALREADY injects the reliability floor (the log says so: "reliability floor —
    3 enabled limb spec(s) applied"). ``_distribute_group_floor`` composes with
    any existing floor through ``np.maximum``, so calling the engine again on the
    already-floored arrays can only ever RAISE min_gen — the armed (lower) leg
    was silently masked by the base floor already sitting there, and both legs
    came back byte-identical. Resetting to ``pmin`` before each leg is what makes
    the two legs comparable.

    What this therefore measures is THIS LIMB IN ISOLATION — the reliability
    floor's own footprint, which is the object the exclusion acts on. The
    LP-visible floor is the maximum of this and the other mechanisms (notably the
    NYISO gas commitment bridge), so a unit-hour where the bridge already floors
    higher would not move in a solve. That composition is measured on the screen,
    not asserted here.
    """
    from market_sim.model.interchange.core import inject_reliability_floor

    fa = state["fleet_arrays"]
    saved_min_gen = None if fa.min_gen is None else fa.min_gen.copy()
    saved_mech = getattr(fa, "floor_mechanisms", None)
    saved_mech = None if saved_mech is None else saved_mech.copy()

    hours = int(fa.availability.shape[1])
    fa.min_gen = np.broadcast_to(fa.pmin[:, np.newaxis], (fa.pmin.size, hours)).copy()
    if saved_mech is not None:
        fa.floor_mechanisms = np.zeros_like(saved_mech)

    inject_reliability_floor(
        fa,
        state["config"].iso,
        year,
        specs,
        state["zone_names"],
        demand=state.get("demand"),
        wind_cf=state.get("wind_cf"),
        wind_cap=state.get("wind_cap"),
        solar_cf=state.get("solar_cf"),
        solar_cap=state.get("solar_cap"),
    )
    out = fa.min_gen.copy()
    fa.min_gen = saved_min_gen
    if saved_mech is not None:
        fa.floor_mechanisms = saved_mech
    return out


def main() -> int:
    from market_sim.config.iso_configs import (
        RELIABILITY_FLOOR_REGISTRY,
        apply_reliability_floor_overrides,
        apply_reliability_floor_plant_exclusions,
        drop_drag_owned_reliability_specs,
        drop_obligation_owned_reliability_specs,
    )

    report: dict = {
        "probe": "nyiso-204 phase 0 — Capital_Hudson lay-up exclusion",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "zero_lp": True,
        "limb": {
            "zone": ZONE,
            "plant_class": KLASS,
            "driver": DRIVER,
            "threshold_c": THRESHOLD,
        },
        "candidates": list(CANDIDATES),
        "years": {},
    }

    for year in YEARS:
        state, meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
        cfg = state["config"]
        fa = state["fleet_arrays"]
        # Canonical source, as scripts/run_calibration.py:2548 uses it.
        from market_sim.config.iso_configs import get_iso_config

        zone_names = list(get_iso_config(cfg.iso).zone_names)
        state["zone_names"] = zone_names

        # The canonical solve-path sequence, verbatim from
        # scripts/run_calibration.py (overrides -> drag -> obligation ->
        # exclusions), so the specs this probe measures are the specs the
        # keeper's own solve applied.
        specs = apply_reliability_floor_overrides(
            RELIABILITY_FLOOR_REGISTRY.get(cfg.iso, []),
            getattr(cfg, "reliability_floor_overrides", None),
        )
        specs = drop_drag_owned_reliability_specs(specs, cfg)
        specs = drop_obligation_owned_reliability_specs(specs, cfg)
        specs = apply_reliability_floor_plant_exclusions(specs, cfg)
        step = _ch_step_spec(specs)

        z_idx = zone_names.index(ZONE)
        # Same selection the engine makes (core.py: groups =
        # np.asarray(fleet_arrays.plant_group)).
        groups = np.asarray(fa.plant_group)
        sel = (groups == KLASS) & (fa.zone_idx == z_idx) & (fa.pmax > 0.0)
        rows = np.flatnonzero(sel)

        base = _run_floor(state, specs, year)
        armed_specs = [
            _dc_replace(
                s,
                exclude_plant_codes=frozenset(
                    set(s.exclude_plant_codes) | set(CANDIDATES)
                ),
            )
            if s is step
            else s
            for s in specs
        ]
        armed = _run_floor(state, armed_specs, year)

        pmax = fa.pmax
        avail = fa.availability
        pin = fa.pmin

        yr: dict = {"n_rows": int(rows.size), "units": [], "flagged_hours": None}

        # The limb's own flagged hours: where the base leg raised ANY CH ST_GAS
        # row above its pmin. (The step is the only live limb for this group.)
        raised_any = (base[rows, :] > (pin[rows, np.newaxis] + 1e-9)).any(axis=0)
        yr["flagged_hours"] = int(raised_any.sum())

        target_mw = float(step.floor_pct) * (
            pmax[rows, np.newaxis] * avail[rows, :]
        ).sum(axis=0)
        yr["zonal_target_mw_on_flagged"] = {
            "mean": float(target_mw[raised_any].mean()) if raised_any.any() else 0.0,
            "max": float(target_mw[raised_any].max()) if raised_any.any() else 0.0,
        }
        yr["floor_pct"] = float(step.floor_pct)

        tot_base = 0.0
        tot_armed = 0.0
        for r in rows:
            pc = int(fa.plant_code[r])
            b = base[r, :] - pin[r]
            a = armed[r, :] - pin[r]
            b = np.maximum(b, 0.0)
            a = np.maximum(a, 0.0)
            tot_base += float(b.sum())
            tot_armed += float(a.sum())
            yr["units"].append(
                {
                    "plant_code": pc,
                    "unit_id": str(fa.unit_ids[r]) if hasattr(fa, "unit_ids") else "",
                    "pmax_mw": float(pmax[r]),
                    "heat_rate": float(fa.heat_rate[r]),
                    "fill_rank_by_heat_rate": None,  # filled below
                    "is_candidate": pc in CANDIDATES,
                    "floor_energy_base_mwh": float(b.sum()),
                    "floor_energy_armed_mwh": float(a.sum()),
                    "delta_mwh": float(a.sum() - b.sum()),
                    "binding_h_base": int((b > 1e-9).sum()),
                    "binding_h_armed": int((a > 1e-9).sum()),
                }
            )
        order = rows[np.argsort(fa.heat_rate[rows], kind="stable")]
        rank = {int(r): i for i, r in enumerate(order)}
        for u, r in zip(yr["units"], rows):
            u["fill_rank_by_heat_rate"] = rank.get(int(r))
        yr["units"].sort(key=lambda u: u["fill_rank_by_heat_rate"] or 0)

        cand_base = sum(
            u["floor_energy_base_mwh"] for u in yr["units"] if u["is_candidate"]
        )
        cand_armed = sum(
            u["floor_energy_armed_mwh"] for u in yr["units"] if u["is_candidate"]
        )
        # MEASURED on both legs, never inferred: the first cut derived
        # `other_armed` by assuming the candidates contribute 0 once excluded,
        # which turned a no-op into a phantom redistribution when the exclusion
        # silently failed to take. Both sides are now read off the arrays.
        other_base = sum(
            u["floor_energy_base_mwh"] for u in yr["units"] if not u["is_candidate"]
        )
        other_armed = sum(
            u["floor_energy_armed_mwh"] for u in yr["units"] if not u["is_candidate"]
        )
        yr["totals"] = {
            "floor_energy_base_mwh": tot_base,
            "floor_energy_armed_mwh": tot_armed,
            "candidates_absorb_base_mwh": cand_base,
            "candidates_absorb_armed_mwh": cand_armed,
            "others_base_mwh": other_base,
            "others_armed_mwh": other_armed,
            "REDISTRIBUTION_onto_others_mwh": other_armed - other_base,
            "NET_floor_energy_removed_mwh": tot_base - tot_armed,
        }
        # Export the per-plant BINDING-hour mask (union over the plant's rows) so
        # phase 0 (d) can score conduct on the exact hours D-4 scores, not merely
        # on the limb's flagged hours. The two differ: the step flags a whole hot
        # day for the zone, but cheapest-first only BINDS a given unit once the
        # cheaper rows are exhausted.
        bind = {}
        for pc in set(int(fa.plant_code[r]) for r in rows):
            m = np.zeros(base.shape[1], dtype=bool)
            for r in rows:
                if int(fa.plant_code[r]) == pc:
                    m |= (base[r, :] - pin[r]) > 1e-9
            bind[str(pc)] = np.flatnonzero(m).tolist()
        yr["binding_hours_by_plant"] = bind

        report["years"][str(year)] = yr

        print(
            f"  {year}: flagged {yr['flagged_hours']} h | floor E "
            f"{tot_base:,.1f} -> {tot_armed:,.1f} MWh | candidates absorbed "
            f"{cand_base:,.1f} | REDISTRIBUTION onto others "
            f"{other_armed - other_base:+,.1f} MWh"
        )

    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
