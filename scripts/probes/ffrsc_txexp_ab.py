#!/usr/bin/env python3
"""FFR-SC: measure the CAISO transmission-expansion A/B at the registered interfaces.

Reads the two arms' cached year parquets. ``run_full_horizon.py`` runs with
``redirect_cache=True``, so an arm's parquets live at
``<out_dir>/<ISO>/<cache_key>/year_<y>.parquet`` — pass the two OUT-DIRS, and
the cache key is resolved from each arm's ``full_horizon_summary.json``.
Reports, per solve year:

* the ``WECC_import_simultaneous`` interface flow (the sum of the two WECC_import
  legs, the ONLY element the registry moves in CAISO 2026-2030), its binding-hour
  share against that year's applied cap, and its duration statistics;
* the per-leg WECC link flows;
* zonal and load-weighted prices;
* the 0-delta registered elements (NP15-ZP26, SP15_rest-SDGE) as controls.

Findings-only: reconstructs from committed artifacts, tunes nothing (rule 1).
Run: ``PYTHONPATH=.:src python scripts/probes/ffrsc_txexp_ab.py <off_dir> <on_dir>``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.transmission_expansion import (
    apply_transmission_expansion,
    load_transmission_expansions,
)
from market_sim.results.outputs import DispatchResult

ISO = "CAISO"
YEARS = (2026, 2027, 2028, 2029, 2030)
# The registered CAISO elements (data/raw/transmission-expansion/caiso.csv), by
# target_kind the channel can apply. The two 0.0-delta links are controls.
WECC_LEGS = [("WECC_import", "NP15"), ("WECC_import", "SP15_rest")]
CONTROL_LINKS = [("NP15", "ZP26"), ("SP15_rest", "SDGE")]


def _link_index(cfg) -> dict[tuple[str, str], int]:
    return {(ln.from_zone, ln.to_zone): i for i, ln in enumerate(cfg.links)}


def _zone_index(cfg) -> dict[str, int]:
    return {z.name: i for i, z in enumerate(cfg.zones)}


def arm_cache_key(out_dir: Path) -> str:
    """Return the arm's solved ``cache_key`` from its full_horizon_summary.json."""
    summary = json.loads((Path(out_dir) / "full_horizon_summary.json").read_text())
    key = summary.get("cache_key")
    if not key:
        raise ValueError(
            f"{out_dir}/full_horizon_summary.json carries no cache_key "
            f"(n_solved_years={summary.get('n_solved_years')!r}, "
            f"error={summary.get('error')!r}) — the leg did not solve"
        )
    return key


def load_arm(out_dir: Path, cache_key: str, year: int) -> DispatchResult:
    path = Path(out_dir) / ISO / cache_key / f"year_{year}.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return DispatchResult.from_parquet(path)


def summarize(off_dir: str, on_dir: str) -> dict:
    base = get_iso_config(ISO)
    rows = load_transmission_expansions(ISO, required=True)
    li = _link_index(base)
    zi = _zone_index(base)
    off_key, on_key = arm_cache_key(Path(off_dir)), arm_cache_key(Path(on_dir))
    out: dict[str, dict] = {
        "_arms": {
            "off": {"out_dir": str(off_dir), "cache_key": off_key},
            "on": {"out_dir": str(on_dir), "cache_key": on_key},
            "keys_distinct": off_key != on_key,
        }
    }

    for year in YEARS:
        try:
            off = load_arm(Path(off_dir), off_key, year)
            on = load_arm(Path(on_dir), on_key, year)
        except FileNotFoundError as exc:
            out[str(year)] = {"error": f"missing {exc}"}
            continue

        cfg_on = apply_transmission_expansion(base, ISO, year, rows)
        cap_off = next(
            i.cap_mw for i in base.interface_limits if i.name == "WECC_import_simultaneous"
        )
        cap_on = next(
            i.cap_mw
            for i in cfg_on.interface_limits
            if i.name == "WECC_import_simultaneous"
        )

        # Pre-COD control: 2026-2027 carry NO applied delta (SWIP-North is the
        # only live CAISO element and enters 2028), so the two arms must be
        # ARRAY-IDENTICAL there. A difference in a pre-COD year is a defect in
        # the channel, not a result.
        identical = {}
        for field in ("dispatch", "prices", "flows", "slack", "wind", "solar"):
            a, b = getattr(off, field, None), getattr(on, field, None)
            if a is None or b is None:
                identical[field] = None
            else:
                identical[field] = bool(
                    np.array_equal(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
                )

        rec: dict = {
            "cap_off_mw": cap_off,
            "cap_on_mw": cap_on,
            "delta_applies": cap_on != cap_off,
            "arms_array_identical": identical,
        }
        for tag, res, cap in (("off", off, cap_off), ("on", on, cap_on)):
            flows = np.asarray(res.flows, dtype=float)  # (n_links, T)
            iface = sum(flows[li[k]] for k in WECC_LEGS)
            prices = np.asarray(res.prices, dtype=float)  # (n_zones, T)
            rec[tag] = {
                "iface_mean_mw": float(iface.mean()),
                "iface_max_mw": float(iface.max()),
                "iface_p95_mw": float(np.percentile(iface, 95)),
                "iface_energy_twh": float(iface.sum() / 1e6),
                # "binding" = within 1 MW of the applied simultaneous cap
                "iface_binding_hours": int((iface >= cap - 1.0).sum()),
                "iface_ge_99pct_hours": int((iface >= 0.99 * cap).sum()),
                "legs_mean_mw": {
                    f"{a}->{b}": float(flows[li[(a, b)]].mean()) for a, b in WECC_LEGS
                },
                "control_links_mean_mw": {
                    f"{a}->{b}": float(flows[li[(a, b)]].mean())
                    for a, b in CONTROL_LINKS
                    if (a, b) in li
                },
                "zone_mean_price": {
                    z: float(prices[i].mean()) for z, i in sorted(zi.items())
                },
                "system_mean_price": float(prices.mean()),
                "max_price": float(prices.max()),
                "hours_ge_500": int((prices.max(axis=0) >= 500.0).sum()),
                "unserved_mwh": (
                    float(np.asarray(res.slack, dtype=float).sum())
                    if getattr(res, "slack", None) is not None
                    else None
                ),
            }
        rec["delta"] = {
            "iface_mean_mw": rec["on"]["iface_mean_mw"] - rec["off"]["iface_mean_mw"],
            "iface_energy_twh": rec["on"]["iface_energy_twh"]
            - rec["off"]["iface_energy_twh"],
            "iface_binding_hours": rec["on"]["iface_binding_hours"]
            - rec["off"]["iface_binding_hours"],
            "system_mean_price": rec["on"]["system_mean_price"]
            - rec["off"]["system_mean_price"],
            "zone_mean_price": {
                z: rec["on"]["zone_mean_price"][z] - rec["off"]["zone_mean_price"][z]
                for z in rec["off"]["zone_mean_price"]
            },
            "unserved_mwh": (
                None
                if rec["off"]["unserved_mwh"] is None
                else rec["on"]["unserved_mwh"] - rec["off"]["unserved_mwh"]
            ),
        }
        out[str(year)] = rec
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    res = summarize(argv[0], argv[1])
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
