"""SPP-37 card A: the EIA-860 vintage cache leak — census, quantification, proof.

WHAT THIS ANSWERS
-----------------
SPP-36 measured that a 3-year span invocation does NOT reproduce three
single-year invocations of the same recipe: 2023 matched to 4 dp, 2024 and 2025
did not (``docs/RESULT-spp-36-shortwindow-span-2026-09-12.md`` §4,
``docs/handoffs/SHARDREPORT-spp36-span.md`` §5). This script reproduces the
cause at ZERO LP cost.

THE MECHANISM
-------------
SPP's keeper carries ``eia860_vintage_tracks_solve_year = True``, so
``run_calibration.run_year`` calls ``paths.set_eia860_vintage(year)`` on every
year and the process-global ``_ACTIVE_EIA_860_DIR`` moves
``vintage_2023 -> vintage_2024 -> eia-860`` (no ``vintage_2025/`` is committed,
so 2025 falls through to the canonical snapshot).

Several ``lru_cache``-d loaders read that global but do NOT carry it in their
cache key. The FIRST year of a span therefore pins its own vintage's value for
every later year, while the LP's own fleet — ``load_fleet_from_csv``, which is
not cached — correctly follows each year's vintage. Numerator and denominator
then sit on different EIA-860 vintages, which is exactly the defect class
``outages._iso_plant_capacity``'s own docstring says must never happen ("this
denominator has to be THE SAME capacity the derate multiplier is applied to in
the LP").

Year 1 is always correct (cold cache); years 2+ are not. That is the observed
signature.

WHAT IT PRINTS
--------------
1. The per-year active directory, so the premise is visible rather than asserted.
2. A census of every vintage-blind cached loader, marking those whose value
   actually MOVES across SPP's three vintages (a stable one is not a leak).
3. The span-vs-single-year delta in the outage-derate denominator.
4. The bins the stale denominator misses entirely — whose outage events are
   silently skipped by ``if tgt not in cap: continue``.
5. The resulting delta in the LP's own availability input, in MWh of capability
   removed, for both the >= 5-day and the < 5-day overlays.
6. The repair's blast radius: with ``tracks_solve_year`` off (every non-SPP
   committed run) the directory is constant, so keying a cache on it is a no-op.

Usage::

    python3 scripts/probes/_spp37_vintage_cache_census.py

Read-only: allocates nothing any solve depends on and changes no committed file.
Cited by ``docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md``.
"""

from __future__ import annotations

import hashlib
import pprint
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    active_eia860_dir,
    resolve_backcast_eia860_vintage,
    set_eia860_vintage,
)
from market_sim.data import outages  # noqa: E402
from market_sim.data.fleet import campd_bins, eia860, load_fleet_from_csv  # noqa: E402

#: The three vintages an SPP 2023-2025 span activates, in solve order.
VINTAGES = (2023, 2024, 2025)
ISO = "SPP"
HOURS = 8760
BINS_PATH = str(REPO_ROOT / "data/raw/reference/custom-bin-assignments.csv")

#: SPP keeper 10's own outage-derate arguments, read off its run_config.json.
_DERATE_KW = dict(
    iso=ISO,
    cc_steam_part_reclass=False,
    cc_nameplate_basis=False,
    st_capacity_basis=False,
    per_unit_clip=False,
    extract_basis_share=False,
    fleet_status_scope=False,
)
_LONG_KW = dict(
    _DERATE_KW, mixed_gas_routing=False, per_unit_crosswalk=False,
    merit_order_guard=False, hour_grain=False,
)
_SHORT_KW = dict(_DERATE_KW, gas_scope=False)


def _digest(obj) -> str:
    """Order-insensitive digest that survives tuple-keyed dicts.

    ``json.dumps`` raises on a tuple key and would silently report every such
    loader "stable" — the trap this helper exists to avoid.
    """
    return hashlib.sha256(pprint.pformat(obj, sort_dicts=True).encode()).hexdigest()[:16]


def _cache_clearers(fn, module):
    """Return the ``cache_clear`` callables behind ``fn``.

    Since SPP-38 the vintage-sensitive loaders are UNCACHED public shims over a
    directory-keyed ``_<name>_cached`` core, so clearing "the function" means
    clearing that core. Pre-repair (still-cached) functions clear directly, so
    this probe runs against either tree.
    """
    if hasattr(fn, "cache_clear"):
        return [fn.cache_clear]
    core = getattr(module, f"_{fn.__name__.lstrip('_')}_cached", None)
    return [core.cache_clear] if core is not None else []


def _clear() -> None:
    """Drop every cache this script measures, so each read is cold."""
    for fn, mod in (
        (outages._iso_plant_capacity, outages),
        (outages._iso_plant_unit_capacity, outages),
        (outages.unit_outage_derate_factors, outages),
        (outages.unit_outage_short_derate_factors, outages),
    ):
        for clear in _cache_clearers(fn, mod):
            clear()


def report_active_dirs() -> None:
    """Print the directory each solve year actually resolves to."""
    print("=== 1. the premise: the active EIA-860 directory moves per year ===")
    for v in VINTAGES:
        set_eia860_vintage(v)
        print(f"    solve year {v} -> {active_eia860_dir().name}")


# The vintage-sensitive loaders under measurement. Shared by the section-2
# census (does the DATA move?) and the section-2b re-key check (does a WARM
# cache honour a vintage switch? -- the SPP-38 invariant).
_CASES = [
    ("outages._iso_plant_capacity(SPP,F,F)", outages._iso_plant_capacity,
     ("SPP", False, False)),  # module resolved from fn.__module__ below
    ("outages._iso_plant_unit_capacity(SPP,F)", outages._iso_plant_unit_capacity,
     ("SPP", False)),
    ("outages._fleet_status_index(SPP)", outages._fleet_status_index, ("SPP",)),
    ("campd_bins.cc_duct_peaking_pct(False)", campd_bins.cc_duct_peaking_pct,
     (False,)),
    ("campd_bins.cc_summer_capacity()", campd_bins.cc_summer_capacity, ()),
    ("campd_bins.cc_winter_capacity()", campd_bins.cc_winter_capacity, ()),
    ("campd_bins.coal_summer_capacity()", campd_bins.coal_summer_capacity, ()),
    ("eia860._eia860_plant_sector()", eia860._eia860_plant_sector, ()),
    ("eia860.eia860_plant_states()", eia860.eia860_plant_states, ()),
    ("eia860.eia860_regulated_plants()", eia860.eia860_regulated_plants, ()),
    ("eia860.eia860_costofservice_majority_plants()",
     eia860.eia860_costofservice_majority_plants, ()),
    ("eia860.eia860_selfcommit_scope_plants()",
     eia860.eia860_selfcommit_scope_plants, ()),
]


def census() -> list[str]:
    """Mark every vintage-blind cached loader whose value moves across vintages."""
    cases = _CASES
    print("\n=== 2. census: which vintage-blind caches actually MOVE ===")
    leaks: list[str] = []
    for label, fn, args in cases:
        seen = {}
        for v in VINTAGES:
            _clear()
            for clear in _cache_clearers(fn, sys.modules[fn.__module__]):
                clear()
            set_eia860_vintage(v)
            try:
                seen[v] = _digest(fn(*args))
            except Exception as exc:  # noqa: BLE001 - a missing artifact is not a leak
                seen[v] = f"ERR:{type(exc).__name__}"
        moves = len(set(seen.values())) > 1
        if moves:
            leaks.append(label)
        print(f"    {'LEAKS ' if moves else 'stable'}  {label}")
    return leaks


def denominator_delta() -> None:
    """Span-vs-single-year delta in the outage-derate denominator."""

    def cap(vintage: int) -> dict:
        _clear()
        set_eia860_vintage(vintage)
        return dict(outages._iso_plant_capacity(ISO, False, False))

    maps = {v: cap(v) for v in VINTAGES}
    print("\n=== 3. the outage-derate denominator, per year ===")
    for v in VINTAGES:
        print(f"    {v}: {len(maps[v])} bins, {sum(maps[v].values()):,.2f} MW")

    stale = maps[2023]  # what years 2 and 3 of a span actually see
    print("\n=== 4. bins the span's stale denominator MISSES (events skipped) ===")
    for y in (2024, 2025):
        true = maps[y]
        missed = sorted(k for k in true if k not in stale)
        print(f"    {y}: {len(missed)} bin(s) absent from the stale map; "
              f"{sum(true[k] for k in missed):,.1f} MW of fleet whose outage "
              f"events never reach the LP")
        for k in sorted(missed, key=lambda k: -true[k])[:5]:
            print(f"         {k}: {true[k]:,.1f} MW")


def availability_delta() -> None:
    """The delta in the LP's own availability input, in MWh of removed capability."""

    def factors(prime_vintage: int | None):
        _clear()
        if prime_vintage is not None:
            # Year 1 of the span builds the denominator under ITS OWN vintage.
            set_eia860_vintage(prime_vintage)
            outages._iso_plant_capacity(ISO, False, False)
        set_eia860_vintage(2025)  # the year-3 (or single-year) solve
        return (
            outages.unit_outage_derate_factors(2025, HOURS, BINS_PATH, **_LONG_KW),
            outages.unit_outage_short_derate_factors(2025, HOURS, BINS_PATH, **_SHORT_KW),
        )

    set_eia860_vintage(2025)
    cap25: dict = {}
    for g in load_fleet_from_csv(ISO, get_iso_config(ISO)):
        if int(g.plant_code) > 0 and g.plant_group:
            key = (int(g.plant_code), g.plant_group)
            cap25[key] = cap25.get(key, 0.0) + float(g.pmax_mw)

    span_long, span_short = factors(2023)
    sing_long, sing_short = factors(None)

    def removed(fac) -> tuple[float, dict]:
        per = {
            k: float(np.sum(1.0 - np.asarray(a, dtype=float)) * cap25[k])
            for k, a in fac.items()
            if k in cap25
        }
        return sum(per.values()), per

    print("\n=== 5. the LP's availability input for 2025 ===")
    for name, sp, sg in (
        (">= 5-day overlay", span_long, sing_long),
        ("<  5-day overlay", span_short, sing_short),
    ):
        st, sper = removed(sp)
        nt, nper = removed(sg)
        n_moved = len([
            k for k in set(sper) | set(nper)
            if abs(sper.get(k, 0.0) - nper.get(k, 0.0)) > 1e-6
        ])
        print(f"    {name}: capability removed  span={st:,.0f} MWh  "
              f"single-year={nt:,.0f} MWh  delta={st - nt:+,.0f} MWh "
              f"({n_moved} bins differ)")


def blast_radius() -> None:
    """With vintage tracking off the directory is constant, so a dir key no-ops."""
    print("\n=== 6. repair blast radius ===")
    for tracks in (True, False):
        names = []
        for y in VINTAGES:
            set_eia860_vintage(resolve_backcast_eia860_vintage(None, y, tracks))
            names.append(active_eia860_dir().name)
        verdict = (
            "CHANGES per year -> the leak is live (SPP only, today)"
            if len(set(names)) > 1
            else "constant -> keying a cache on it is a strict NO-OP"
        )
        print(f"    tracks_solve_year={tracks!s:<5} {names}  {verdict}")


def rekey_check() -> list[str]:
    """SPP-38's invariant: a WARM cache must still honour a vintage switch.

    Section 2 clears before every read, so it measures whether the DATA moves.
    This measures the defect itself: read vintage A, then read vintage B
    **without clearing**, and compare against B's own cold value. Pre-repair the
    vintage-blind loaders returned A's value here; post-repair every one must
    return B's.
    """
    print("\n=== 2b. SPP-38 invariant: warm cache honours a vintage switch ===")
    bad: list[str] = []
    for label, fn, args in _CASES:
        mod = sys.modules[fn.__module__]
        for clear in _cache_clearers(fn, mod):
            clear()
        cold = {}
        for v in VINTAGES:  # cold reference value per vintage
            for clear in _cache_clearers(fn, mod):
                clear()
            set_eia860_vintage(v)
            try:
                cold[v] = _digest(fn(*args))
            except Exception as exc:  # noqa: BLE001
                cold[v] = f"ERR:{type(exc).__name__}"
        for clear in _cache_clearers(fn, mod):
            clear()
        warm = {}
        for v in VINTAGES:  # one process, cache NEVER cleared -- the span path
            set_eia860_vintage(v)
            try:
                warm[v] = _digest(fn(*args))
            except Exception as exc:  # noqa: BLE001
                warm[v] = f"ERR:{type(exc).__name__}"
        stale = [v for v in VINTAGES if warm[v] != cold[v]]
        if stale:
            bad.append(f"{label} (stale in {stale})")
        print(f"    {'STALE ' if stale else 'rekeys'}  {label}")
    return bad


def main() -> None:
    report_active_dirs()
    leaks = census()
    stale = rekey_check()
    denominator_delta()
    availability_delta()
    blast_radius()
    print("\n=== vintage-blind caches whose value moves across SPP's span ===")
    for label in leaks:
        print(f"    - {label}")
    print("\n=== loaders still serving a STALE vintage on a warm cache ===")
    if stale:
        for label in stale:
            print(f"    - {label}")
    else:
        print("    (none -- every loader re-keys on the active directory)")


if __name__ == "__main__":
    main()
