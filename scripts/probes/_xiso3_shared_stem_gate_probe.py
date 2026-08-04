"""xiso-3 O-1: are the keeper-armed-looking shared scalars READABLE at all?

Pre-registered in ``PREREG-xiso3-shared-stem-backlog-2026-08-04.md`` §7 as
observation **O-1**, with PASS / FAIL / UNINFORMATIVE and a **mandatory
positive control** specified before the probe ran.

**Written on CONSTRUCTION, not on a solved dual** — the binding lesson of
nyiso-115 G2 and nyiso-118 (a scope question gated on a solved dual can only
pass when the mechanism does nothing, and a provably-unchanged construction can
still move its dual through general equilibrium). **No LP, no solve, no dual.**

The shape is caiso-161 §5 / pjm-151 / nyiso-121 G-1: a ``run_config.json`` that
records a scalar at a non-default value OVERSTATES what the solve read when the
scalar's own gate is off. Scanning the six keepers for each of the 45 shared
fields' code-level gates surfaces seven candidate pairs in two ISOs:

* **ERCOT** — ``coal_prb_passthrough_floor`` 0.76, ``coal_prb_follower_floor``
  0.76, ``coal_lignite_passthrough_floor`` 0.675 and
  ``coal_lignite_passthrough_ceil`` 1.0, behind rank sigmoid gates the ercot158
  keeper sets ``False``.
* **CAISO** — ``ct_drag_slope_per_gw`` 0.00901, ``ct_drag_intercept`` -0.1124
  and ``ct_drag_cap`` 0.36, behind ``ct_netload_drag=False``.

Each quantity is built **twice at one HEAD** — the scalar at its keeper value
vs a large perturbation — and diffed with ``np.array_equal`` on float32:
**exact equality, not a tolerance** (a 1e-6 tolerance is unsatisfiable in
principle on these columns; nyiso-116 G3/P4). Every arm carries a positive
control that flips ONLY the gate: the instrument must be shown to SEPARATE
before its silence is trusted, or that arm is VOID.

This probe adjudicates nothing (rule 28(d)). It reports.

Usage:
    PYTHONPATH=.:src python scripts/probes/_xiso3_shared_stem_gate_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.floors import apply_ct_netload_drag_floor
from market_sim.data.fleet.models import FleetArrays, Generator
from market_sim.data.fuel.trajectories import (
    coal_passthrough_by_supply,
    prb_follower_passthrough_series,
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/calibration/xiso3_shared_stem_gate_probe.json"
HOURS = 8760
YEAR = 2024


def _keeper_config(iso: str) -> tuple[str, dict]:
    """The ISO's designated keeper id and its recorded ``scenario_config``."""
    kid = json.loads((REPO / f"frontend/data/backcast/keepers/{iso}.json").read_text())[
        "keeper"
    ]
    bundle = json.loads(
        (REPO / f"frontend/data/backcast/registry/{kid}.json").read_text()
    )["bundle"]
    name = Path(bundle).name
    for pattern in ("*/run_config.json", "*/*/run_config.json"):
        for path in (REPO / "results/calibration").glob(pattern):
            if path.parent.name == name:
                return kid, json.loads(path.read_text())["scenario_config"]
    raise SystemExit(f"UNINFORMATIVE: no run_config.json for the {iso} keeper {kid}")


def _cfg(base: dict, **overrides) -> ScenarioConfig:
    """A ``ScenarioConfig`` on the keeper's own recorded fields plus overrides."""
    fields = set(ScenarioConfig.__dataclass_fields__)
    kwargs = {k: v for k, v in base.items() if k in fields and k != "iso"}
    kwargs.update(overrides)
    return ScenarioConfig(iso=base["iso"], **kwargs)


def _supply_map(cfg: ScenarioConfig) -> dict[str, np.ndarray]:
    """The per-supply passthrough map the coal offer curves consume, float32."""
    out = {}
    for supply, series in coal_passthrough_by_supply(cfg, YEAR, HOURS).items():
        out[supply] = np.asarray(
            np.broadcast_to(np.asarray(series, dtype=np.float32), (HOURS,))
        ).astype(np.float32)
    return out


def _diff(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> tuple[bool, float]:
    """Exact-equality verdict over every supply, plus the max abs delta."""
    keys = sorted(set(a) | set(b))
    equal = all(k in a and k in b and np.array_equal(a[k], b[k]) for k in keys)
    worst = max(
        (float(np.max(np.abs(a[k] - b[k]))) for k in keys if k in a and k in b),
        default=0.0,
    )
    return equal, worst


def _ercot_offer_supply_map(cfg: ScenarioConfig) -> dict[str, np.ndarray]:
    """The per-supply map the COAL OFFER CURVES actually consume.

    Mirrors ``data/fleet/assembly.py`` exactly, including the tiered branch —
    ``coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered`` — which is
    the ONLY path by which ``coal_prb_follower_floor`` reaches a fleet. Testing
    the follower against the plain ``coal_passthrough_by_supply`` map would be
    an instrument that cannot separate on it in principle, so its silence there
    would prove nothing.

    Both cohorts are kept as separate keys, because assembly holds BOTH maps at
    once: the tiered branch builds ``foll`` as an ALTERNATIVE and ``_pt_for``
    routes only the low-must-run plants to it, leaving every other prb plant on
    the baseload curve. An emulation that OVERWRITES the baseload entry would be
    blind to ``coal_prb_passthrough_floor`` even with its gate on — which is
    exactly what the per-field positive control caught on this probe's first
    per-field revision, and why the control is mandatory rather than advisory.
    """
    out = _supply_map(cfg)
    out["prb_baseload"] = out.pop("prb")
    if cfg.coal_prb_passthrough_sigmoid and cfg.coal_prb_passthrough_tiered:
        series = prb_follower_passthrough_series(cfg, YEAR, HOURS)
        out["prb_follower"] = np.broadcast_to(
            np.asarray(series, dtype=np.float32), (HOURS,)
        ).astype(np.float32)
    return out


def ercot_coal_arms(base: dict) -> list[dict]:
    """ERCOT: is each rank scalar readable with its OWN gate at the keeper?

    One arm PER FIELD, each with its OWN positive control, because a single
    pooled control can pass on one field's movement while never exercising
    another's read path at all.
    """
    cases = [
        ("coal_prb_passthrough_floor", 0.05, {"coal_prb_passthrough_sigmoid": True}),
        (
            "coal_lignite_passthrough_floor",
            0.05,
            {"coal_lignite_passthrough_sigmoid": True},
        ),
        (
            "coal_lignite_passthrough_ceil",
            0.05,
            {"coal_lignite_passthrough_sigmoid": True},
        ),
        # The follower floor's ONLY read path is the tiered branch, which needs
        # BOTH flags; the keeper carries tiered=True but sigmoid=False.
        ("coal_prb_follower_floor", 0.05, {"coal_prb_passthrough_sigmoid": True}),
    ]
    rows = []
    for field, value, gate_on in cases:
        keeper = _ercot_offer_supply_map(_cfg(base))
        moved = _ercot_offer_supply_map(_cfg(base, **{field: value}))
        equal, worst = _diff(keeper, moved)
        rows.append(
            {
                "arm": f"ERCOT {field}, GATE AT KEEPER SETTING",
                "fields": [field],
                "gates": {
                    g: base.get(g, "<absent>")
                    for g in (
                        "coal_prb_passthrough_sigmoid",
                        "coal_lignite_passthrough_sigmoid",
                        "coal_prb_passthrough_tiered",
                    )
                },
                "exactly_equal": equal,
                "max_abs_delta": worst,
                "verdict": "INERT (provably unreadable)" if equal else "LIVE",
            }
        )
        ctl_equal, ctl_worst = _diff(
            _ercot_offer_supply_map(_cfg(base, **gate_on)),
            _ercot_offer_supply_map(_cfg(base, **gate_on, **{field: value})),
        )
        rows.append(
            {
                "arm": f"POSITIVE CONTROL — {field}, its own gate ON ({gate_on})",
                "fields": [field],
                "exactly_equal": ctl_equal,
                "max_abs_delta": ctl_worst,
                "verdict": "SEPARATES (instrument live)" if not ctl_equal else "VOID",
            }
        )
    return rows


def _toy_ct_fleet() -> tuple[FleetArrays, list[Generator], np.ndarray]:
    """A 1-generator / 1-zone CT_PEAKER fleet — trivial case first (docs/testing).

    The drag floor writes ``fleet_arrays.min_gen``; nothing else about the fleet
    matters to it, so the smallest fleet that can carry the floor is the honest
    instrument.
    """
    n, t = 1, HOURS
    fa = FleetArrays(
        pmax=np.array([100.0]),
        pmin=np.zeros(n),
        heat_rate=np.array([10.0]),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.zeros(n, dtype=int),
        availability=np.ones((n, t)),
        unit_ids=np.array(["CT_TEST"]),
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.array([1]),
        min_gen=np.zeros((n, t)),
        min_gen_mechanism=np.zeros((n, t), dtype=np.int16),
        state=np.array(["TX"]),
        plant_group=np.array(["CT_PEAKER"]),
        ramp10=np.zeros(n),
    )
    gens = [
        Generator(
            unit_id="CT_TEST",
            name="CT_TEST",
            zone="Z1",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            heat_rate=10.0,
            plant_group="CT_PEAKER",
            plant_code=1,
        )
    ]
    # A net-load ramp that spans the curve's whole range, so a live coefficient
    # cannot fail to bite for want of headroom.
    net_load = np.linspace(10_000.0, 60_000.0, t)
    return fa, gens, net_load


def caiso_ct_drag_arms(base: dict) -> list[dict]:
    """CAISO: are the CT drag coefficients readable with ct_netload_drag off?"""
    perturb = {
        "ct_drag_slope_per_gw": 0.05,
        "ct_drag_intercept": -0.5,
        "ct_drag_cap": 0.95,
    }

    def build(**over) -> np.ndarray:
        fa, gens, net_load = _toy_ct_fleet()
        apply_ct_netload_drag_floor(fa, gens, net_load, _cfg(base, **over))
        return fa.min_gen.astype(np.float32)

    rows = []
    a, b = build(), build(**perturb)
    equal = np.array_equal(a, b)
    rows.append(
        {
            "arm": "CAISO ct_drag coefficients, GATE AT KEEPER SETTING",
            "fields": sorted(perturb),
            "gates": {"ct_netload_drag": base.get("ct_netload_drag", "<absent>")},
            "exactly_equal": bool(equal),
            "max_abs_delta": float(np.max(np.abs(a - b))),
            "verdict": "INERT (provably unreadable)" if equal else "LIVE",
        }
    )
    c = build(ct_netload_drag=True)
    d = build(ct_netload_drag=True, **perturb)
    ctl_equal = np.array_equal(c, d)
    rows.append(
        {
            "arm": "POSITIVE CONTROL — same perturbation, ct_netload_drag ON",
            "fields": sorted(perturb),
            "exactly_equal": bool(ctl_equal),
            "max_abs_delta": float(np.max(np.abs(c - d))),
            "verdict": "SEPARATES (instrument live)" if not ctl_equal else "VOID",
        }
    )
    return rows


def main() -> None:
    """Run both O-1 families and write the probe record."""
    ercot_id, ercot_cfg = _keeper_config("ERCOT")
    caiso_id, caiso_cfg = _keeper_config("CAISO")
    doc = {
        "probe": "xiso-3 O-1 shared-stem gate readability (CONSTRUCTION, no LP)",
        "prereg": "results/calibration/PREREG-xiso3-shared-stem-backlog-2026-08-04.md",
        "keepers": {"ERCOT": ercot_id, "CAISO": caiso_id},
        "comparison": "np.array_equal on float32 — EXACT equality, not a tolerance",
        "arms": ercot_coal_arms(ercot_cfg) + caiso_ct_drag_arms(caiso_cfg),
    }
    OUT.write_text(json.dumps(doc, indent=2))
    for row in doc["arms"]:
        print(
            f"{row['arm']}\n"
            f"    exactly_equal={row['exactly_equal']}  "
            f"max|delta|={row['max_abs_delta']:.6g}  -> {row['verdict']}"
        )
        if "gates" in row:
            print(f"    gates: {row['gates']}")
    controls = [r for r in doc["arms"] if "POSITIVE CONTROL" in r["arm"]]
    tests = [r for r in doc["arms"] if "POSITIVE CONTROL" not in r["arm"]]
    if any(r["exactly_equal"] for r in controls):
        print("\nO-1 VOID: a positive control did not separate.")
    elif all(r["exactly_equal"] for r in tests):
        print("\nO-1 PASS: every arm is provably unreadable on its own keeper.")
    else:
        print("\nO-1 FAIL: a scalar is LIVE — the pre-registered hypothesis is WRONG.")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
