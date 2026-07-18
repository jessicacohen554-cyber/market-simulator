"""Persisted per-year capacity-evolution ledger.

Every simulation year writes an ``evolution_<year>.json`` file beside its
cached dispatch parquet (see :func:`market_sim.results.cache.get_cache_path`).
The ledger is the shared substrate for both forecast validators built in W2-P5:

* ``scripts/check_forecast_invariants.py`` reads it for the capacity-accounting,
  no-retire-and-reenter, economic-retirement-sanity, reliability-floor,
  planned-additions, storage and one-pass invariants (plan §2.2).
* ``scripts/score_capacity_hindcast.py`` reads it to score modelled builds and
  retirements against actuals (plan §1.4).

Before W2-P5 only the in-memory ``retrofit_log`` was threaded through
``prior_results``; retirements and builds were log lines, not data. This module
turns them into a durable, machine-readable record.

The schema (one object per scenario-year)::

    {
      "iso": "ERCOT", "year": 2027, "mode": "forecast", "hindcast": false,
      "retirements":        [{"unit_id","fuel","mw","reason"}],   # confirmed|announced|economic
      "confirmed_derates":  [{"unit_id","fuel","mw_before","mw_after","derate_mw"}],
      "floor_retained":     [{"unit_id","fuel","mw"}],            # econ wanted out
      "pipeline_events":    [{"event","unit_id","fuel","mw","year",...}],  # R-NEW
                            # decided|re_confirmed|reversed|entry_capped|executed
                            # (retirement_rule="pipeline" only; empty under legacy)
      "thermal_additions":  [{"unit_id","fuel","mw","zone","source","eia860_id"}],
      "ccs_retrofits":      [{"unit_id","mw","from_fuel","to_fuel"}],
      "renewable_additions":[{"zone","tech","mw"}],
      "storage_additions":  [{"unit_id","tech","mw","zone","duration_h"}],
      "fleet_by_fuel_before": {fuel: mw}, "fleet_by_fuel_after": {fuel: mw},
      "peak_demand_mw": float, "firm_clean_mw": float,
      "reserve_margin": float, "rps_dual": float,
      "solve_counts": {"P0": 1, "P1": 1, "P2": 0}
    }

``thermal_additions`` sources are ``planned`` | ``economic`` |
``reserve_backstop``; ``retirements`` reasons are ``confirmed`` | ``announced``
| ``economic`` (RC-1B — the channel-attributed split of the pre-RC-1B single
``known`` reason, taken before step 0 and step 1 separately instead of once
before both; ``confirmed_derates`` is new and records a confirmed-registry row
that derates a plant-binned tranche without retiring its ``unit_id`` entirely,
previously invisible). Additive: bundles committed before RC-1B still carry
``known`` rows and no ``confirmed_derates`` key — both readers must treat an
absent/legacy value as backward-compatible, not malformed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# Fuel classes carried in the persistent thermal fleet. Renewables (wind/solar)
# and storage grow separate pools, so they are ledgered in their own lists, not
# in ``fleet_by_fuel_*``.
LEDGER_VERSION = 1

_LEDGER_PREFIX = "evolution_"


def ledger_path(parquet_path: Path) -> Path:
    """Return the ledger path sitting beside a cached year parquet.

    ``results/{iso}/{key}/year_{year}.parquet`` →
    ``results/{iso}/{key}/evolution_{year}.json``.
    """
    parquet_path = Path(parquet_path)
    year = parquet_path.stem.replace("year_", "").split("_")[0]
    return parquet_path.parent / f"{_LEDGER_PREFIX}{year}.json"


def fleet_totals_by_fuel(fleet) -> dict[str, float]:
    """Sum ``pmax_mw`` by ``fuel_type`` over a generator list.

    Args:
        fleet: Iterable of ``Generator`` objects.

    Returns:
        ``{fuel_type: total_pmax_mw}`` with float MW values.
    """
    totals: dict[str, float] = defaultdict(float)
    for g in fleet:
        totals[g.fuel_type] += float(g.pmax_mw)
    return {k: round(v, 6) for k, v in sorted(totals.items())}


def new_events() -> dict:
    """Return an empty event dict for :func:`evolve_fleet` to populate."""
    return {
        "retirements": [],
        "floor_retained": [],
        "pipeline_events": [],
        "thermal_additions": [],
        "ccs_retrofits": [],
        "renewable_additions": [],
        "fleet_by_fuel_before": {},
        "fleet_by_fuel_after": {},
    }


def write_ledger(path: Path, ledger: dict) -> Path:
    """Write ``ledger`` as pretty JSON to ``path`` and return the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True))
    return path


def load_ledger(path: Path) -> dict:
    """Load a ledger JSON file."""
    return json.loads(Path(path).read_text())


def load_ledgers_for_run(cache_dir: Path) -> dict[int, dict]:
    """Load every ``evolution_<year>.json`` in a run's cache directory.

    Args:
        cache_dir: ``results/{iso}/{cache_key}/`` directory.

    Returns:
        ``{year: ledger_dict}`` sorted by year.
    """
    cache_dir = Path(cache_dir)
    out: dict[int, dict] = {}
    for p in sorted(cache_dir.glob(f"{_LEDGER_PREFIX}*.json")):
        try:
            year = int(p.stem.replace(_LEDGER_PREFIX, ""))
        except ValueError:
            continue
        out[year] = load_ledger(p)
    return dict(sorted(out.items()))
