"""miso-247 phase 0 — the P19 posture at MISO. ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0: an arm with a computable pre-solve gate does not
reach a solve until that gate passes. This probe runs every measured leg of
``PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md`` §2 (the ``G-DRIFT``
re-audit) and §3 (phase 0), and applies §4's screen-year selection rule, without
spending an LP minute.

The two objects, both landed by owner ruling **P19** (2026-09-08, repo-wide)
AFTER the keeper's own solve commit ``d059fcf7`` and neither ever carried by a
MISO solve:

  **A** ``ScenarioConfig.f923_gas_price_plausibility_screen`` — default ON at
  HEAD, frozen cache-key drop ``"False"``, ABSENT from the keeper's recorded
  config. Pinnable.

  **B** ``market_sim.data.fleet.eia860._apply_simple_cycle_hr_floor`` — applied
  unconditionally at the single eGRID read seam. **Ungated and unkeyed**: no
  ``ScenarioConfig`` field, no cache-key entry, ``SOLVE_EPOCHS`` empty, and
  ``data.fleet.eia860`` is not in ``solve_surface.SURFACE_MODULES``. It is
  reproduced in its pre-P19 posture by restoring the identity function at that
  seam -- the only way to express "the tree the keeper solved on" for a change
  that carries no gate.

Both fleets are built through ``run_calibration.run_year(fleet_only=True)`` on
the keeper's own recipe (``replay_keeper.build_kwargs`` over its ``meta.json``),
so each comparison is the keeper's exact configuration with a single declared
delta. ``mc_base`` from that state dict is the assembled P0 objective -- the same
offer prices the LP solves on -- so §3's footprint statistic is measured on the
LP's own operand and never on a residual, a band or a criterion.

No LP is solved, nothing is fitted, nothing is promoted, and rule 22
``[R-HOLDOUT]`` is honoured: 2023-2025 only.

Writes ``results/calibration/_miso247_p19_posture_phase0.json``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402
from market_sim.data.fleet import eia860  # noqa: E402

KEEPER = REPO / "results/calibration/miso245_ladderfix_K"
OUT = REPO / "results/calibration/_miso247_p19_posture_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER_SHA = "d059fcf7"

#: PREREG §3 P-1: a row counts toward the footprint when its hour-mean assembled
#: marginal cost moves by more than this. A resolution floor on float64 noise,
#: declared before the statistic was computed; never swept.
MC_EPS = 0.01

_ORIG_HR_FLOOR = eia860._apply_simple_cycle_hr_floor


def _clear_caches() -> None:
    """Drop every ``lru_cache`` in the fleet/fuel read path.

    Posture **B** is applied inside a cached eGRID read seam
    (``_rows_to_generators``), so a stale entry would silently serve one
    posture's heat rates to the other's build. Cleared exhaustively rather than
    by name, so a newly-added cache cannot reintroduce the bug.
    """
    import gc
    from functools import _lru_cache_wrapper  # type: ignore[attr-defined]

    for obj in gc.get_objects():
        if isinstance(obj, _lru_cache_wrapper):
            try:
                obj.cache_clear()
            except Exception:  # pragma: no cover - defensive
                pass


def build(year: int, *, screen: bool, hr_floor: bool) -> dict:
    """Build the keeper's fleet for ``year`` under one declared posture.

    Reconstruction goes through ``replay_keeper.run_year_kwargs`` +
    ``derived_run_year_inputs`` -- THE ONLY SANCTIONED fleet-only path
    (caiso-243 §7.3 / caiso-248). An earlier draft of this probe splatted
    ``build_kwargs`` directly, which is the lookalike-recipe defect that
    docstring exists to forbid; it failed loudly on an unmapped kwarg rather
    than silently measuring a different recipe, and the repair is recorded in
    ADDENDUM 1.

    Posture **A** rides ``prb_overrides``, the generic override bag
    ``run_year`` applies through ``config.with_overrides`` -- the screen has no
    named ``run_year`` kwarg. Its consumer (``data.fuel.plant_prices``) runs
    during fleet/fuel assembly, AFTER that channel applies, so the nyiso-199
    ordering defect does not reach it; the assertion below proves the flag
    landed on the RESOLVED config rather than trusting that argument.

    Args:
        year: Solve year (2023-2025 only, rule 22).
        screen: Posture **A** -- ``f923_gas_price_plausibility_screen``.
        hr_floor: Posture **B** -- whether the P19 simple-cycle heat-rate floor
            is applied at the eGRID seam.

    Returns:
        The ``run_year(fleet_only=True)`` state dict.

    Raises:
        AssertionError: The requested posture did not reach the resolved config.
    """
    meta = json.loads((KEEPER / "meta.json").read_text())
    call = rk.run_year_kwargs(meta)
    call.update(rk.derived_run_year_inputs(KEEPER, year))
    call["year"] = year
    call["iso"] = meta["iso"]
    call["hours"] = HOURS
    call["fleet_only"] = True
    call["gas_price"] = float(meta["gas_prices"][str(year)])
    call["ttc_overrides"] = {}
    prb = dict(call.get("prb_overrides") or {})
    prb["f923_gas_price_plausibility_screen"] = bool(screen)
    call["prb_overrides"] = prb

    eia860._apply_simple_cycle_hr_floor = (
        _ORIG_HR_FLOOR if hr_floor else (lambda df: df)
    )
    _clear_caches()
    try:
        state = rc.run_year(**call)
    finally:
        eia860._apply_simple_cycle_hr_floor = _ORIG_HR_FLOOR
        _clear_caches()
    got = bool(getattr(state["config"], "f923_gas_price_plausibility_screen", False))
    assert got == bool(screen), (
        f"posture A did not reach the resolved config: asked {screen}, got {got}"
    )
    return state


def _mc_hourmean(state: dict) -> np.ndarray:
    """Hour-mean assembled marginal cost per generator row ($/MWh)."""
    mc = np.asarray(state["mc_base"], dtype=float)
    return mc.mean(axis=1) if mc.ndim == 2 else mc


def _footprint(base: dict, arm: dict) -> dict:
    """PREREG §3 ``P-1``: pmax MW of rows whose hour-mean ``mc_base`` moves."""
    n = min(len(base["fleet_arrays"].pmax), len(arm["fleet_arrays"].pmax))
    signed = _mc_hourmean(arm)[:n] - _mc_hourmean(base)[:n]
    moved = np.abs(signed) > MC_EPS
    pmax = np.asarray(arm["fleet_arrays"].pmax, dtype=float)[:n]
    return {
        "n_rows": int(n),
        "rows_moved": int(moved.sum()),
        "MW_moved": round(float(pmax[moved].sum()), 3),
        "max_abs_dmc": round(float(np.abs(signed).max()) if n else 0.0, 6),
        # Capacity-weighted mean signed move over the moved rows: the SIGN is
        # what G-1 tests the realized dispatch response against.
        "signed_MWwtd_dmc": (
            round(float(np.average(signed[moved], weights=pmax[moved])), 6)
            if moved.any()
            else 0.0
        ),
    }


def _hr_delta(base: dict, arm: dict) -> dict:
    """PREREG §2 ``D-1``: generator rows whose ``heat_rate`` moves."""
    hb = np.asarray(base["fleet_arrays"].heat_rate, dtype=float)
    ha = np.asarray(arm["fleet_arrays"].heat_rate, dtype=float)
    n = min(hb.size, ha.size)
    d = ha[:n] - hb[:n]
    moved = np.abs(d) > 1e-12
    pmax = np.asarray(arm["fleet_arrays"].pmax, dtype=float)[:n]
    out = {
        "n_rows": int(n),
        "rows_moved": int(moved.sum()),
        "MW_moved": round(float(pmax[moved].sum()), 3),
        "max_abs_dhr": round(float(np.abs(d).max()) if n else 0.0, 6),
        "min_signed_dhr": round(float(d.min()) if n else 0.0, 6),
        "identity_max_is_floor": True,
        "rows": [],
    }
    idx = np.flatnonzero(moved)
    for i in idx[:60]:
        # P-2 identity: the clamp is max(hr_before, floor), so it may only RAISE.
        if d[i] <= 0:
            out["identity_max_is_floor"] = False
        out["rows"].append(
            {
                "unit_id": str(arm["fleet_arrays"].unit_ids[i]),
                "pmax": round(float(pmax[i]), 3),
                "hr_before": round(float(hb[i]), 6),
                "hr_after": round(float(ha[i]), 6),
            }
        )
    return out


def _min_gen_sig(state: dict) -> str:
    """PREREG §2 ``D-2``: bit signature of the assembled per-unit min_gen."""
    mg = getattr(state["fleet_arrays"], "min_gen", None)
    if mg is None:
        return "absent"
    return hashlib.sha256(np.ascontiguousarray(mg, dtype=float).tobytes()).hexdigest()[
        :24
    ]


def _class_of(unit_id: str, fleet_arrays, i: int) -> str:
    for attr in ("plant_group", "group", "class_name"):
        v = getattr(fleet_arrays, attr, None)
        if v is not None:
            try:
                return str(v[i])
            except Exception:
                pass
    return "unknown"


def _reclear(state_b: dict, state_a: dict) -> dict:
    """PREREG §3 ``P-3``: pooled re-clearing energy prediction, per class.

    Merit-orders the assembled offer stack against the keeper's own committed
    hourly load in each posture and reports the per-class energy delta (TWh).
    This is ``G-1``'s predictor and it is fixed before any LP runs. It is a
    single-zone economic re-clear, so it carries no transmission, no commitment
    and no storage -- it predicts DIRECTION and ORDER OF MAGNITUDE, which is
    exactly what ``G-1`` tests it on.
    """
    out = {}
    fa = state_a["fleet_arrays"]
    demand = np.asarray(state_a["demand"], dtype=float)
    load = demand.sum(axis=0) if demand.ndim == 2 else demand
    pmax = np.asarray(fa.pmax, dtype=float)
    for tag, st in (("base", state_b), ("arm", state_a)):
        mc = np.asarray(st["mc_base"], dtype=float)
        if mc.ndim == 1:
            mc = np.repeat(mc[:, None], load.size, axis=1)
        energy = np.zeros(pmax.size)
        # Vectorized over rows within each hour; the hour loop is a probe-side
        # merit sort, NOT LP construction (rule 2 [R-VECTOR] scopes the matrix
        # builder), and it runs on <= 8760 hours once per posture.
        for t in range(load.size):
            order = np.argsort(mc[:, t], kind="stable")
            cum = np.cumsum(pmax[order])
            k = int(np.searchsorted(cum, load[t]))
            take = np.zeros(pmax.size)
            take[order[:k]] = pmax[order[:k]]
            if k < order.size:
                take[order[k]] = max(0.0, load[t] - (cum[k - 1] if k else 0.0))
            energy += take
        out[tag] = energy
    by_class: dict[str, float] = {}
    for i in range(pmax.size):
        c = _class_of(str(fa.unit_ids[i]), fa, i)
        by_class[c] = by_class.get(c, 0.0) + float(out["arm"][i] - out["base"][i]) / 1e6
    return {
        k: round(v, 4) for k, v in sorted(by_class.items(), key=lambda kv: -abs(kv[1]))
    }


def main() -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip()
    )
    rec: dict = {
        "probe": "_miso247_p19_posture_phase0",
        "prereg": "PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md",
        "zero_lp": True,
        "keeper": "2026-09-08-miso-245-ladderfix",
        "keeper_git_sha": KEEPER_SHA,
        "provenance": {"head": head, "dirty": dirty},
        "mc_eps": MC_EPS,
        "years": {},
    }
    for y in YEARS:
        # Four postures: keeper (A off / B off), B only, A only, arm (A on / B on).
        s_keeper = build(y, screen=False, hr_floor=False)
        s_bonly = build(y, screen=False, hr_floor=True)
        s_aonly = build(y, screen=True, hr_floor=False)
        s_arm = build(y, screen=True, hr_floor=True)
        rec["years"][str(y)] = {
            "D1_hr_floor": _hr_delta(s_keeper, s_bonly),
            "D2_min_gen": {
                "keeper": _min_gen_sig(s_keeper),
                "arm": _min_gen_sig(s_arm),
            },
            "P1_F_A": _footprint(s_keeper, s_aonly),
            "P1_F_B": _footprint(s_keeper, s_bonly),
            "P1_F_AB": _footprint(s_keeper, s_arm),
        }
        del s_bonly, s_aonly
        rec["years"][str(y)]["_states"] = "released"
        rec["years"][str(y)]["P3_reclear_TWh"] = _reclear(s_keeper, s_arm)
        del s_keeper, s_arm
        print(f"[miso-247] {y} done", flush=True)
    # PREREG §4 selection rule, applied exactly as written.
    f_b_all_zero = all(rec["years"][str(y)]["P1_F_B"]["rows_moved"] == 0 for y in YEARS)
    key = "P1_F_A" if f_b_all_zero else "P1_F_AB"
    best = max(YEARS, key=lambda y: (rec["years"][str(y)][key]["MW_moved"], -y))
    rec["D1_verdict"] = "B INERT at MISO" if f_b_all_zero else "B LIVE at MISO"
    rec["form4_valid"] = f_b_all_zero
    rec["screen_year_statistic"] = key
    rec["screen_year"] = int(best)
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps({k: v for k, v in rec.items() if k != "years"}, indent=1))


if __name__ == "__main__":
    main()
