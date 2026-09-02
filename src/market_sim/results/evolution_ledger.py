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
      "announced_derates":  [{"unit_id","fuel","mw_before","mw_after","derate_mw"}],
                            # capx D42: the fossil announced-date step-1 channel's
                            # plant-binned derates (fossil_announced_exits_enabled)
      "announced_fossil_schedule": [{...}],  # first ledger year only, under the
                            # D42 gate: the audited dated-row set (every
                            # disposition, incl. cancelled/reversed)
      "floor_retained":     [{"unit_id","fuel","mw"}],            # econ wanted out
      "pipeline_events":    [{"event","unit_id","fuel","mw","year",...}],  # R-NEW
                            # decided|re_confirmed|reversed|entry_capped|executed
                            # (retirement_rule="pipeline" only; empty under legacy)
                            # FFR-5A bar decomposition (diagnostic, rows written
                            # since 2026-08-05): each row also carries both bar
                            # sides (net_revenue_usd, going_forward_cost_usd),
                            # the per-leg split (energy_margin_usd,
                            # reserve_uplift_usd, attribute_revenue_usd,
                            # capacity_revenue_usd, as_annual_credit_usd,
                            # as_pricing) and the screen-basis descriptors
                            # (screen_price_mean/max_usd_mwh,
                            # reserve_signal_mean_usd_mwh, availability_mean,
                            # mc_mean_usd_mwh) of the screen that emitted it.
      "thermal_additions":  [{"unit_id","fuel","mw","zone","source","eia860_id"}],
      "ccs_retrofits":      [{"unit_id","mw","from_fuel","to_fuel"}],
      "renewable_additions":[{"zone","tech","mw"}],
      "storage_additions":  [{"unit_id","tech","mw","zone","duration_h"}],
      "fleet_by_fuel_before": {fuel: mw}, "fleet_by_fuel_after": {fuel: mw},
      "peak_demand_mw": float, "firm_clean_mw": float,
      "firm_clean_accredited_mw": float,
      "wind_cap_mw": float, "solar_cap_mw": float,
      "renewable_credit_applied": {fuel: credit},
      "storage_power_mw": float,   # storage FLEET power after the entry screen
      "storage_firm_mw": float,    # the same fleet, pre-dilution accredited
      "reserve_margin": float, "rps_dual": float,
      "solve_counts": {"P0": 1, "P1": 1, "P2": 0}
    }

``thermal_additions`` sources are ``planned`` | ``economic`` |
``reserve_backstop``; ``retirements`` reasons are ``confirmed`` | ``announced``
| ``economic`` — the channel-attributed split of the pre-split single
``known`` reason, taken before step 0 and step 1 separately instead of once
before both. ``confirmed_derates`` records a confirmed-registry row that
derates a plant-binned tranche without retiring its ``unit_id`` entirely,
previously invisible to the recorder's unit-id set-diff (the I4/A1 accounting
leak, FR-1). RC-1B documented this schema but the writers landed only with
FFR-1A (2026-07-31): :func:`new_events` creates the key and
``evolve_fleet``'s step-0/step-1 recorder seam populates it. Additive:
bundles committed before FFR-1A still carry ``known`` rows and no
``confirmed_derates`` key — both readers must treat an absent/legacy value as
backward-compatible, not malformed.

``firm_clean_mw`` is the model's dispatched conventional-hydro NAMEPLATE and
``firm_clean_accredited_mw`` the same resources at the ISO's published
accreditation factor — the MW that actually enter
``accredited_firm_capacity_mw``. Both landed with FFR-3B (2026-08-02, closing
FFR-1C finding F-5): before it, ``firm_clean_mw`` summed the PERSISTENT fleet,
which structurally never contains hydro, so **every ledger written before that
date reports 0.0 regardless of the ISO's real hydro fleet** — read those values
as "not measured", not as zero hydro. The change is a display seam only (nothing
decides on either field; the adequacy screens read
``accredited_firm_capacity_mw``), and ``firm_clean_accredited_mw`` is absent
from every pre-FFR-3B bundle — treat it as backward-compatible, like
``confirmed_derates``.

``storage_power_mw`` is the storage fleet's NAMEPLATE POWER after that year's
new-entry screen (``sum(u.power_cap_mw for u in storage_units)``, written by
``runner.run_scenario_iso``). It is the ONLY durable record of the storage
fleet state: :class:`~market_sim.results.outputs.FleetContext` carries the
fleet's storage ENERGY capacity (``storage_energy_cap_mwh``) but no power
column, and the LP's storage resources are not generators, so nothing on the
generator axis ever sums to it. ``run_full_horizon.extract_trajectory`` reads
this key for the summary's ``storage_power_mw`` (capx D29) precisely because
the alternative — the generator-axis ``cap.get("storage")`` its legacy
``storage_mw`` key uses — is 0.0 by construction. Like the two fields above it
is additive: 83 ledgers written before it exists carry no such key, and a
reader must render that as "not measured", never as zero storage.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# Ledger schema version, stamped into every payload by :func:`write_ledger`.
# Bump only on a breaking schema change; both readers treat an absent
# ``ledger_version`` key (pre-versioning bundles) as version 1 (legacy).
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
        "confirmed_derates": [],
        "announced_derates": [],
        "floor_retained": [],
        "pipeline_events": [],
        "thermal_additions": [],
        "ccs_retrofits": [],
        "renewable_additions": [],
        "fleet_by_fuel_before": {},
        "fleet_by_fuel_after": {},
    }


def write_ledger(path: Path, ledger: dict) -> Path:
    """Write ``ledger`` as pretty JSON to ``path`` and return the path.

    Stamps ``ledger_version`` (:data:`LEDGER_VERSION`) into the written payload
    when the caller has not already set it — additive, so existing callers and
    readers are unaffected (a reader that ignores the key sees the same data).
    The input dict is not mutated.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(ledger)
    payload.setdefault("ledger_version", LEDGER_VERSION)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
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
