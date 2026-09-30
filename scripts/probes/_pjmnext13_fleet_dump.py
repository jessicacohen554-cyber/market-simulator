"""PJM-NEXT-13 zero-LP: dump the keeper's rebuilt fleet arrays for one year (no LP).

``fleet_only`` rebuild of the keeper recipe (``pjmnext8_xf_span``) through the
sanctioned, fidelity-guarded :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`.
Writes ``<scratch>/pjmnext13_fleet_<year>.npz`` with, per LP unit: ``unit_ids``,
``plant_code``, ``plant_group``, ``zone`` (name), ``pmax``, hourly ``availability``
(float32, 8760), hourly ``fuel_price`` and ``mc_base`` where the rebuild carries them
hourly, and ``heat_rate``. The three NEXT-13 cards read these arrays; nothing here
changes a solve.

Run: ``python3 scripts/probes/_pjmnext13_fleet_dump.py <out_dir> 2019 [...]``
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.lib import bundle_fleet as BF  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"


def _hourly(a: np.ndarray, n: int, t: int = 8760) -> np.ndarray:
    """Coerce a per-unit array to (n, t) float32 (broadcasting a per-unit scalar)."""
    a = np.asarray(a, dtype=float)
    if a.ndim == 2 and a.shape == (n, t):
        return a.astype(np.float32)
    if a.ndim == 2 and a.shape == (t, n):
        return a.T.astype(np.float32)
    if a.ndim == 1 and a.shape[0] == n:
        return np.repeat(a[:, None], t, axis=1).astype(np.float32)
    raise ValueError(f"unexpected shape {a.shape} for n={n}")


#: The ARM recipe (PJM-NEXT-13 PRECOMMIT): replacement-cost fuel on, and the three
#: gas-keyed coal passthrough gates it supersedes (rule 19) off.
ARM_SET: dict[str, bool] = {
    "pjm_replacement_cost_fuel": True,
    "coal_bit_passthrough_sigmoid": False,
    "coal_prb_passthrough_sigmoid": False,
    "coal_prb_passthrough_tiered": False,
}


def _rebuild(year: int, arm: bool = False) -> dict:
    """``reconstruct_bundle_fleet`` with ONE override: ``pjm_da_virtual_bids`` off.

    The DA virtual INC/DEC units are demand-side LP rows (``VIRTUAL_*`` groups) that
    carry no availability, fuel price or offer for any physical unit, and their
    gitignored corpus is not needed to read the physical fleet (the
    ``_pjmnext8_exitfix_avail_delta.py`` precedent). Every other recorded flag is
    carried and the fidelity guard still runs.
    """
    import json

    BF.ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False
    if arm:
        # Both channels, exactly as replay_keeper --set routes a key.
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **ARM_SET}
        for k, v in ARM_SET.items():
            if k in kw:
                kw[k] = v
        # The bit gate's run_year kwarg is named ``coal_bit_sigmoid`` (meta and
        # ScenarioConfig say ``coal_bit_passthrough_sigmoid``); it re-arms the
        # field after prb_overrides, so the kwarg must be disarmed too.
        kw["coal_bit_sigmoid"] = False
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    BF.assert_reconstruction_fidelity(
        meta, state["config"], BF.DEFAULT_REQUIRED_FLAGS, BF.DEFAULT_REQUIRED_SEQUENCES
    )
    return state


def dump(year: int, out_dir: Path, arm: bool = False) -> Path:
    """Rebuild ``year`` (keeper, or the ARM recipe) and write the npz."""
    state = _rebuild(year, arm)
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)
    zones = list(state["config"].zones) if hasattr(state["config"], "zones") else None
    zidx = np.asarray(fa.zone_idx, int)
    zname = (
        np.asarray([zones[i] for i in zidx], dtype=object)
        if zones
        else zidx.astype(str).astype(object)
    )
    arrs = {
        "unit_ids": np.asarray(fa.unit_ids, dtype=object),
        "plant_code": np.asarray(fa.plant_code).astype(str).astype(object),
        "plant_group": np.asarray(fa.plant_group, dtype=object),
        "zone": zname,
        "pmax": np.asarray(fa.pmax, float),
        "heat_rate": np.asarray(fa.heat_rate, float),
        "availability": _hourly(fa.availability, n),
    }
    for key in ("fuel_prices", "mc_base"):
        v = state.get(key)
        if v is not None:
            try:
                arrs[key] = _hourly(v, n)
            except ValueError as e:
                print(f"  {key}: {e}", flush=True)
    # The P1 mid-curve offer FLOOR (pjm_offer_midcurve_conditional), exactly as
    # run_year builds it at the mc_bid_adjust seam, so the arm delta is read on
    # the bid the LP sees rather than on mc_base (the floor only raises bids).
    cfg = state["config"]
    if getattr(cfg, "pjm_offer_midcurve_conditional", False):
        from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup

        net = (
            state["demand"].sum(axis=0)
            - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
            - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
        )
        mk = build_pjm_offer_midcurve_conditional_markup(
            fa, state["fleet"], state["mc_base"], net, cfg, year
        )
        if mk is not None:
            arrs["midcurve_markup"] = _hourly(mk, n)
    dest = out_dir / f"pjmnext13_fleet_{year}{'_arm' if arm else ''}.npz"
    np.savez_compressed(dest, **arrs, allow_pickle=True)
    print(f"{year}: {n} units -> {dest}", flush=True)
    return dest


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    arm = "--arm" in sys.argv
    for y in [int(a) for a in sys.argv[2:] if a != "--arm"]:
        dump(y, out, arm)
