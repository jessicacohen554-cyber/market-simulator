#!/usr/bin/env python
"""FFR-3T: cache-key census across the forecast and backcast paths (D-10).

The measurement behind `docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md` §3.
Owner decision D-10 turns cross-year LP warm start OFF for forecast bundles, and
the coordination note attached to it expected that to shift every forecast cache
key. Whether it does depends entirely on HOW the value is made effective, because
``ScenarioConfig.cache_key`` drops a ``_CACHE_KEY_OPTIONAL_FIELDS`` member when it
equals the **live** default — so a DEFAULT FLIP leaves the key exactly where it
was while an EXPLICIT non-default value moves it. This script measures both
sides rather than reasoning about them:

* **forecast keys** — six ISOs x the four shipped forecast configs (T1-F
  ``run_full_horizon.reference_config``; T1-H and T1-X
  ``run_capacity_hindcast.build_config``; the §2.1a golden posture
  ``ff_readiness_battery.golden_posture_config``);
* **backcast keys** — each designated keeper's config, rebuilt from the
  ``scenario_config`` block of its committed ``run_config.json``, which is the
  check that proves the change did not reach the backcast.

Run it at the pre-change commit and again after, and diff the two JSON files. The
DEFAULT-FLIP counterfactual cannot be produced in-process: the dataclass bakes
the default into the generated ``__init__`` signature, so monkeypatching the
field spec (or the class attribute) does not reach a constructed config and the
census silently reports the unflipped numbers. Edit the field, run, revert.

Usage::

    python scripts/probes/_ffr3t_cache_key_census.py > before.json
    # ... apply the change ...
    python scripts/probes/_ffr3t_cache_key_census.py > after.json
    python scripts/probes/_ffr3t_cache_key_census.py --diff before.json after.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (_SRC, _ROOT):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

ISOS = ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO")

#: Each ISO's designated keeper bundle at 2026-08-04. Read from
#: ``frontend/data/backcast/registry/<keeper id>.json``; kept here as a literal so
#: the census reproduces the exact six bundles it measured even after a promotion.
KEEPER_BUNDLES = {
    "ERCOT": "results/calibration/ercot158_poolarm_B",
    "PJM": "results/calibration/pjm151_seam_B",
    "CAISO": "results/calibration/caiso164_zonal_loss_surface",
    "NYISO": "results/calibration/nyiso120_c119_scopegate",
    "NEISO": "results/calibration/neiso_c156_meter_screen_B",
    "MISO": "results/calibration/miso124_dualfuel_B",
}

_SPECS = {f.name: f for f in fields(ScenarioConfig)}


def _coerce(name: str, value):
    """Restore a JSON-decoded value to the field's stored python type.

    Only the list/tuple case matters: ``json`` cannot represent a tuple, and a
    list would hash differently from the tuple the solve actually stored. Applied
    identically on both sides of the before/after diff either way.
    """
    default = _SPECS[name].default
    if isinstance(value, list) and isinstance(default, tuple):
        return tuple(value)
    return value


def keeper_config(iso: str) -> ScenarioConfig:
    """Rebuild an ISO keeper's backcast ScenarioConfig from its committed bundle."""
    path = _ROOT / KEEPER_BUNDLES[iso] / "run_config.json"
    with open(path) as fh:
        payload = json.load(fh)["scenario_config"]
    return ScenarioConfig(
        **{k: _coerce(k, v) for k, v in payload.items() if k in _SPECS}
    )


def forecast_configs() -> dict[str, ScenarioConfig]:
    """Build one config per shipped forecast runner per ISO."""
    from scripts.ff_readiness_battery import golden_posture_config
    from scripts.run_capacity_hindcast import build_config
    from scripts.run_full_horizon import reference_config

    out: dict[str, ScenarioConfig] = {}
    for iso in ISOS:
        out[f"T1-F/run_full_horizon/{iso}"] = reference_config(
            iso, 2026, 2050, cmc=False, golden_posture=True
        )
        out[f"T1-H/run_capacity_hindcast/{iso}"] = build_config(
            iso, 2021, 2025, variant="realized"
        )
        out[f"T1-X/run_capacity_hindcast/{iso}"] = build_config(
            iso, 2021, 2030, variant="realized", crossover=True
        )
        out[f"battery/golden_posture/{iso}"] = golden_posture_config(iso)
    return out


def census() -> dict:
    """Return the full key census for this working tree."""
    out: dict = {
        "pinned_default_cache_key": ScenarioConfig().cache_key(),
        "shipped_field_default": ScenarioConfig().forecast_xyear_warmstart,
        "backcast_keeper_keys": {},
        "forecast_keys": {},
    }
    for iso in ISOS:
        cfg = keeper_config(iso)
        out["backcast_keeper_keys"][iso] = {
            "cache_key": cfg.cache_key(),
            "mode": cfg.mode,
            "forecast_xyear_warmstart": cfg.forecast_xyear_warmstart,
        }
    for label, cfg in forecast_configs().items():
        out["forecast_keys"][label] = {
            "cache_key": cfg.cache_key(),
            "forecast_xyear_warmstart": cfg.forecast_xyear_warmstart,
        }
    return out


def diff(before_path: str, after_path: str) -> int:
    """Print a before/after table and return a non-zero code if nothing moved."""
    with open(before_path) as fh:
        before = json.load(fh)
    with open(after_path) as fh:
        after = json.load(fh)
    moved = 0
    print(
        f"pinned default {before['pinned_default_cache_key']} -> "
        f"{after['pinned_default_cache_key']}"
    )
    for block in ("forecast_keys", "backcast_keeper_keys"):
        tag = "FC" if block == "forecast_keys" else "BC"
        n_moved = 0
        for key in sorted(before[block]):
            a = before[block][key]["cache_key"]
            b = after[block][key]["cache_key"]
            state = "SAME" if a == b else "MOVED"
            n_moved += state == "MOVED"
            print(f"  {tag} {key:44s} {a} -> {b}  {state}")
        print(f"  {tag}: {n_moved} moved of {len(before[block])}")
        moved += n_moved if block == "forecast_keys" else 0
    return 0 if moved else 1


def main(argv: list[str] | None = None) -> int:
    """Emit the census as JSON, or diff two previously-emitted censuses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("BEFORE", "AFTER"),
        help="diff two census JSON files instead of emitting one",
    )
    args = parser.parse_args(argv)
    if args.diff:
        return diff(*args.diff)
    print(json.dumps(census(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
