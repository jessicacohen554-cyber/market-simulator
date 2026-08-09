"""FFR-9A R1: the storage-fleet trajectory of a T1-FF arm, by solve year.

The pre-registered R1 read of
``docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md`` §1.4: base +
cumulative endogenous additions, power AND energy, per solve year, against the
measured EIA-860 fleet that actually operated. The base is reconstructed
OFFLINE by the same calls the runner makes (scalar path for the control arm,
vintage-seeded ``load_eia860_storage`` for the treated arm), so the probe
never trusts a narrated number; the additions come from the arm's own
evolution ledgers. The measured comparator is ``load_eia860_storage`` per
year-end against the canonical (2025ER) sheet — reported at full magnitude,
never targeted.

Read-only; never solves. Usage::

    uv run python scripts/probes/ffr9a_storage_trajectory.py \
        --bundle results/hindcast/ercot-2021-2025-t1ff-armr-ffr9a-control \
        --arm control --out docs/handoffs/ffr-9a/storage-trajectory-control.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import set_eia860_vintage  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.storage import (  # noqa: E402
    build_default_storage,
    load_eia860_pumped_storage,
    load_eia860_storage,
)
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

VINTAGE = 2020
START_YEAR = 2021
#: EIA-860 storage-unit rows report energy in MWh; ledger addition rows carry
#: (mw, duration_h) instead, so energy is mw * duration_h.


def _resolve_cache_dir(out_dir: Path) -> Path:
    iso_dir = out_dir / "ERCOT"
    keys = sorted(d for d in iso_dir.iterdir() if d.is_dir())
    if len(keys) != 1:
        raise SystemExit(f"{iso_dir}: expected exactly one cache-key dir, found {keys}")
    return keys[0]


def _fleet_totals(units) -> dict:
    return {
        "n_units": len(units),
        "power_mw": round(sum(u.power_cap_mw for u in units), 1),
        "energy_mwh": round(sum(u.energy_cap_mwh for u in units), 1),
    }


def _base_fleet(arm: str) -> dict:
    """Reconstruct the arm's base storage fleet exactly as the runner builds it."""
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="forecast",
        hindcast=True,
        eia860_vintage_year=VINTAGE,
        start_year=START_YEAR,
        end_year=2025,
    )
    set_eia860_vintage(VINTAGE)
    try:
        if arm == "treated":
            units = load_eia860_storage("ERCOT", START_YEAR, cfg)
            basis = "load_eia860_storage @ vintage_2020, start_year 2021 (FFR-9A seed)"
        else:
            units = build_default_storage(get_iso_config("ERCOT"), cfg)
            units = load_eia860_pumped_storage("ERCOT", START_YEAR, config=cfg) + units
            basis = "build_default_storage (STORAGE_BASE_FLEET_MW scalar) + PS prepend"
    finally:
        set_eia860_vintage(None)
    return {"basis": basis, **_fleet_totals(units)}


def _measured_actual(year: int) -> dict:
    """Measured year-end fleet from the canonical (2025ER) sheet — comparator only."""
    cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
    set_eia860_vintage(None)
    return {"year": year, **_fleet_totals(load_eia860_storage("ERCOT", year, cfg))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--arm", required=True, choices=("control", "treated"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cache_dir = _resolve_cache_dir(Path(args.bundle))
    ledgers = load_ledgers_for_run(cache_dir)
    if not ledgers:
        raise SystemExit(f"{cache_dir}: no evolution ledgers")

    base = _base_fleet(args.arm)
    cum_mw = base["power_mw"]
    cum_mwh = base["energy_mwh"]
    per_year = []
    for year, led in ledgers.items():
        adds = led.get("storage_additions") or []
        add_mw = sum(float(a.get("mw", 0.0)) for a in adds)
        add_mwh = sum(
            float(a.get("mw", 0.0)) * float(a.get("duration_h", 0.0)) for a in adds
        )
        cum_mw += add_mw
        cum_mwh += add_mwh
        per_year.append(
            {
                "ledger_year": year,
                "n_addition_rows": len(adds),
                "added_power_mw": round(add_mw, 1),
                "added_energy_mwh": round(add_mwh, 1),
                "cumulative_power_mw": round(cum_mw, 1),
                "cumulative_energy_mwh": round(cum_mwh, 1),
            }
        )

    result = {
        "probe": "ffr9a_storage_trajectory (R1)",
        "arm": args.arm,
        "cache_dir": str(cache_dir),
        "base_fleet": base,
        "per_year": per_year,
        "measured_actual_year_end": [_measured_actual(y) for y in (2023, 2024, 2025)],
        "note": (
            "measured_actual is the canonical-sheet EIA-860 year-end fleet "
            "(battery + PS), the R1 comparator — reported, never targeted"
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
