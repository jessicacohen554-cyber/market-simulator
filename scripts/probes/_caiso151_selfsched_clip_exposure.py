"""caiso-151 — pre-arm exposure of ``caiso_firm_import_selfsched_clip``.

The "report before arming" step the session charter requires: how the derived
measured price-insensitive ceiling
(``scripts/data/derive_caiso_intertie_selfsched.py``) compares, hour by hour, to
the firm must-flow floor it will clip — computed on the KEEPER's own fleet, with
**no LP and no solver** beyond the fleet reconstruction
(``run_calibration.run_year(fleet_only=True)``, the caiso-131/134/140/142/143/150
machinery).

It reproduces the mechanism exactly as ``inject_caiso_firm_import_selfschedule``
applies it — the same pro-rata allocation of the system ceiling across firm
tranches — so the removed energy printed here is the removed energy the armed
solve will see, and the ex-ante magnitude in
``PREREG-caiso151-firm-selfsched-clip-2026-07-31.md`` is falsifiable against it.

THE ``coal_prb_sigmoid_overrides`` TRAP (caiso-150 §E2, cost that session real
time). CAISO's firm-import flags have **no CLI flag and no top-level meta.json
key**; they reach a solve ONLY through the generic ``ScenarioConfig`` override
channel, whose meta.json name is ``coal_prb_sigmoid_overrides``
(-> ``run_year(prb_overrides=)``). A probe that omits the rename below rebuilds
the fleet with the entire ~27 TWh must-flow block ABSENT while every other CAISO
mechanism still arms and logs normally, which looks like a correct fleet.

Usage::

    .venv/bin/python scripts/probes/_caiso151_selfsched_clip_exposure.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
# `scripts.lib.clean_io` (hydro modes, capacity deliverability) imports by
# PACKAGE path, so the repo root must be importable too — without it the fleet
# build degrades silently on some seams and hard-fails on the hydro one.
sys.path.insert(0, str(REPO_ROOT))

HOURS = 8760
YEARS = (2023, 2024, 2025)
KEEPER = REPO_ROOT / "results" / "calibration" / "caiso148_nucavail_B"

#: meta.json -> run_year kwarg renames. See the trap note in the module
#: docstring: ``coal_prb_sigmoid_overrides`` is NOT a coal key.
_META_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
}


def fleet_state(year: int, arm: bool = False) -> dict:
    """Reconstruct the keeper's fleet for ``year`` (no LP, no solve).

    With ``arm`` the clip flag is added to the SAME generic override channel a
    real ``replay_keeper --set`` writes to, so the returned fleet is the one the
    armed solve builds — which is what makes the plumbing check below a check of
    the plumbing and not of this probe's own arithmetic.
    """
    import inspect

    from run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    if arm:
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = dict(kwargs["prb_overrides"])
        kwargs["prb_overrides"]["caiso_firm_import_selfsched_clip"] = True
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def firm_floor(fa, zones, tranches) -> np.ndarray:
    """System-total firm must-flow floor (MW per hour) on a built fleet."""
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, HOURS))
    total = np.zeros(HOURS)
    for r, uid in enumerate(fa.unit_ids):
        z = next((zz for zz in zones if str(uid).startswith(f"{zz}_")), None)
        if z is None or str(uid)[len(z) + 1 :] not in tranches:
            continue
        total += np.clip(np.asarray(mg[r, :], dtype=float), 0.0, None)
    return total


def main() -> int:
    """Print the per-year and diurnal exposure of the clip."""
    from market_sim.config.interchange_config import CAISO_PER_HUB_IMPORT_ZONES
    from market_sim.data.caiso_intertie_bids import (
        measured_intertie_selfsched_ceiling,
    )
    from market_sim.model.interchange.caiso import CAISO_FIRM_IMPORT_TRANCHES

    print("=== caiso-151 pre-arm exposure: measured ceiling vs the firm floor ===")
    ceiling = measured_intertie_selfsched_ceiling("CAISO", 2024, HOURS)
    if ceiling is None:
        print("  NO ARTIFACT — run scripts/data/derive_caiso_intertie_selfsched.py")
        return 2

    zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    predicted: dict[int, np.ndarray] = {}
    for year in YEARS:
        st = fleet_state(year)
        fa = st["fleet_arrays"] if isinstance(st, dict) else st.fleet_arrays
        total = firm_floor(fa, zones, CAISO_FIRM_IMPORT_TRANCHES)

        # Same guarded form as the injector: np.where evaluates both branches,
        # so the zero-floor hours need the errstate suppression too.
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = np.where(total > 0.0, np.minimum(1.0, ceiling / total), 1.0)
        clipped = total * scale
        binds = clipped < total - 1e-6
        removed = float((total - clipped).sum() / 1e6)
        print(
            f"\n  {year}: forced {total.sum() / 1e6:7.3f} TWh -> "
            f"{clipped.sum() / 1e6:7.3f} TWh   "
            f"REMOVED {removed:6.3f} TWh ({100 * removed / max(1e-9, total.sum() / 1e6):4.1f} %)"
        )
        print(
            f"    clip binds in {int(binds.sum()):5d} h of {HOURS} "
            f"({100 * binds.sum() / HOURS:4.1f} %)"
        )
        prof_f = total.reshape(-1, 24).mean(axis=0)
        prof_c = clipped.reshape(-1, 24).mean(axis=0)
        prof_e = ceiling.reshape(-1, 24).mean(axis=0)
        print(
            f"    {'hod':>4s} {'floor':>8s} {'ceiling':>9s} {'clipped':>9s} {'ratio':>7s}"
        )
        for h in range(0, 24, 2):
            print(
                f"    {h:4d} {prof_f[h]:8.0f} {prof_e[h]:9.0f} {prof_c[h]:9.0f} "
                f"{prof_f[h] / max(1e-9, prof_e[h]):7.2f}"
            )
        night = np.isin(np.arange(HOURS) % 24, [22, 23, 0, 1, 2, 3, 4, 5])
        print(
            f"    overnight h22-h05 share of removed energy: "
            f"{100 * (total - clipped)[night].sum() / max(1e-9, (total - clipped).sum()):.1f} %"
        )
        predicted[year] = clipped

    # --- plumbing check ---------------------------------------------------- #
    # Everything above is this probe's own arithmetic on an UNARMED fleet. This
    # rebuilds 2024 with the flag armed through the SAME generic override
    # channel `replay_keeper --set` writes to, and checks the built fleet's own
    # floor equals the prediction. It is what proves the flag actually reaches
    # the injector before ~80 minutes of solve time is spent on two arms.
    print("\n  PLUMBING CHECK — 2024 fleet rebuilt with the flag armed via the")
    print("  generic override channel (the path replay_keeper --set uses):")
    st = fleet_state(2024, arm=True)
    fa = st["fleet_arrays"] if isinstance(st, dict) else st.fleet_arrays
    armed = firm_floor(fa, zones, CAISO_FIRM_IMPORT_TRANCHES)
    exp = predicted[2024]
    dev = float(np.abs(armed - exp).max())
    print(
        f"    armed fleet floor {armed.sum() / 1e6:7.3f} TWh vs predicted "
        f"{exp.sum() / 1e6:7.3f} TWh   max|d| = {dev:.6f} MW"
    )
    ok = dev <= 1e-6
    print(
        f"    {'PASS — the flag reaches the injector' if ok else 'FAIL — flag NOT wired; do NOT solve'}"
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
