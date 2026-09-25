"""The EIA-860 vintage-cache keying invariant (SPP-38, rule 14 ``[R-ACCURATE]``).

Under ``ScenarioConfig.eia860_vintage_tracks_solve_year`` a span run re-points the
process-global :data:`~market_sim.config.paths._ACTIVE_EIA_860_DIR` on every year.
Twelve ``lru_cache``d loaders read that global while omitting it from their cache
key, so year 1 of a span pinned its vintage's value for every later year — the
outage-derate DENOMINATOR and the CC duct-peaking PEAK OFFER BAND among them, both
direct LP inputs. Measured, with the mechanism and magnitudes, in
``docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md``; repaired by
SPP-38 by keying each cache on the active directory.

Two legs, both required:

* **RE-KEYS** — with the vintage flipped between calls on a WARM cache, each
  loader returns each vintage's own value. This is the defect itself.
* **STRICT NO-OP** — with the vintage CONSTANT (which is every ISO but SPP, and
  every SPP single-year run) the second call is a cache HIT: the same object back,
  and exactly one entry in the core's cache. The repair must cost nothing where
  there was nothing wrong.

Hermetic: synthetic one-row EIA-860 parquets in ``tmp_path``, no ``data/raw``.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.data import outages
from market_sim.data.fleet import campd_bins, eia860

# (module, public name, cached-core name). The full census is FINDING-spp-37 §3.
REPAIRED: tuple[tuple[object, str, str], ...] = (
    (outages, "_iso_plant_capacity", "_iso_plant_capacity_cached"),
    (outages, "_iso_plant_unit_capacity", "_iso_plant_unit_capacity_cached"),
    (outages, "_fleet_status_index", "_fleet_status_index_cached"),
    (campd_bins, "cc_duct_peaking_pct", "_cc_duct_peaking_pct_cached"),
    (campd_bins, "cc_summer_capacity", "_cc_summer_capacity_cached"),
    (campd_bins, "cc_winter_capacity", "_cc_winter_capacity_cached"),
    (campd_bins, "coal_summer_capacity", "_coal_summer_capacity_cached"),
    (eia860, "_eia860_plant_sector", "_eia860_plant_sector_cached"),
    (eia860, "eia860_plant_states", "_eia860_plant_states_cached"),
    (eia860, "eia860_regulated_plants", "_eia860_regulated_plants_cached"),
    (
        eia860,
        "eia860_costofservice_majority_plants",
        "_eia860_costofservice_majority_plants_cached",
    ),
    (
        eia860,
        "eia860_selfcommit_scope_plants",
        "_eia860_selfcommit_scope_plants_cached",
    ),
)

# The nine loaders that read an EIA-860 sheet directly, and so can be driven from
# synthetic parquets. The remaining three build from the fleet and are covered by
# `TestTheFleetBackedLoadersRekey` (monkeypatched fleet) and the structural test.
_FLEET_BACKED = {"_iso_plant_capacity", "_iso_plant_unit_capacity"}
# `eia860_selfcommit_scope_plants` composes two repaired loaders and gets its own
# test; the fleet-backed pair need a fleet, not a sheet.
_ARGS: dict[str, tuple] = {"_fleet_status_index": ("SPP",)}
_SHEET_BACKED = tuple(
    (m, pub, core, _ARGS.get(pub, ()))
    for m, pub, core in REPAIRED
    if pub not in _FLEET_BACKED | {"eia860_selfcommit_scope_plants"}
)


def _write_vintage(root: Path, *, marker: int) -> Path:
    """Write a minimal EIA-860 vintage whose every value keys off ``marker``."""
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Plant Code": [marker],
            "Utility ID": [900 + marker],
            "Sector": [marker % 7 + 1],
            "State": ["KS" if marker % 2 else "OK"],
            "Regulatory Status": ["RE" if marker % 2 else "NR"],
        }
    ).to_parquet(root / "eia860_plant.parquet")
    pd.DataFrame(
        {
            "Plant Code": [marker, marker],
            "Generator ID": ["1", "2"],
            "Status": ["OP", "OP"],
            "Technology": [
                "Natural Gas Fired Combined Cycle",
                "Conventional Steam Coal",
            ],
            "Duct Burners": ["Y", "X"],
            "Nameplate Capacity (MW)": [100.0 + marker, 200.0 + marker],
            "Summer Capacity (MW)": [90.0 + marker, 180.0 + marker],
            "Winter Capacity (MW)": [110.0 + marker, 210.0 + marker],
        }
    ).to_parquet(root / "eia860_generator_operable.parquet")
    # Schedule 4 / utility, for eia860_costofservice_majority_plants.
    pd.DataFrame(
        {
            "Plant Code": [marker],
            "Generator ID": ["1"],
            "Ownership ID": [900 + marker],
            "Percent Owned": [100.0],
        }
    ).to_parquet(root / "eia860_owner.parquet")
    pd.DataFrame(
        {"Utility ID": [900 + marker], "Entity Type": ["M" if marker % 2 else "Q"]}
    ).to_parquet(root / "eia860_utility.parquet")
    return root


@pytest.fixture
def vintages(tmp_path):
    """Two synthetic EIA-860 vintages that disagree about everything."""
    return _write_vintage(tmp_path / "v_a", marker=1), _write_vintage(
        tmp_path / "v_b", marker=2
    )


@pytest.fixture(autouse=True)
def _cold_caches():
    """Every test starts and ends with every repaired cache empty."""

    def clear():
        for mod, _pub, core in REPAIRED:
            getattr(mod, core).cache_clear()

    clear()
    yield
    clear()


def _point_at(monkeypatch, directory: Path) -> None:
    """Move the process-global active vintage, as ``run_year`` does per year."""
    monkeypatch.setattr(paths, "_ACTIVE_EIA_860_DIR", Path(directory))


class TestTheLoadersRekeyOnAVintageSwitch:
    """Leg 1 — the defect: a WARM cache must not serve the prior vintage."""

    @pytest.mark.parametrize(
        ("pub", "core", "args"),
        [(p, c, a) for _m, p, c, a in _SHEET_BACKED],
        ids=[p for _m, p, _c, _a in _SHEET_BACKED],
    )
    def test_warm_cache_returns_each_vintage_own_value(
        self, monkeypatch, vintages, pub, core, args
    ):
        mod = next(m for m, p, _c, _a in _SHEET_BACKED if p == pub)
        fn = getattr(mod, pub)
        a, b = vintages

        # Cold reference: each vintage read on its own, caches empty.
        _point_at(monkeypatch, a)
        getattr(mod, core).cache_clear()
        cold_a = fn(*args)
        _point_at(monkeypatch, b)
        getattr(mod, core).cache_clear()
        cold_b = fn(*args)
        assert cold_a != cold_b, f"{pub}: the fixture must make the vintages differ"

        # Warm: one process, cache NEVER cleared -- exactly the span path.
        getattr(mod, core).cache_clear()
        _point_at(monkeypatch, a)
        warm_a = fn(*args)
        _point_at(monkeypatch, b)
        warm_b = fn(*args)

        assert warm_a == cold_a, f"{pub} lost vintage A's value"
        assert warm_b == cold_b, (
            f"{pub} served a STALE vintage on a warm cache -- this is the "
            "SPP-37 defect (FINDING-spp-37-order-sensitivity-2026-09-12.md)"
        )

    def test_the_union_loader_rekeys_through_both_its_legs(self, monkeypatch, vintages):
        # eia860_selfcommit_scope_plants composes two repaired loaders, so it
        # needs the directory in its OWN key too -- otherwise it pins year 1's
        # union even with repaired inputs.
        a, b = vintages
        _point_at(monkeypatch, a)
        warm_a = eia860.eia860_selfcommit_scope_plants()
        _point_at(monkeypatch, b)
        warm_b = eia860.eia860_selfcommit_scope_plants()
        assert warm_a != warm_b
        assert warm_a == frozenset({1}) and warm_b == frozenset()


class TestTheFleetBackedLoadersRekey:
    """The two fleet-summed loaders: the outage-derate denominator and its roster."""

    @staticmethod
    def _install_vintage_dependent_fleet(monkeypatch):
        """A fleet whose capacity is a function of the ACTIVE vintage directory."""
        import market_sim.data.fleet as fleet_pkg

        def _fleet(iso, iso_config, **kwargs):
            marker = float(len(paths.active_eia860_dir().name))
            return [
                SimpleNamespace(
                    plant_code=1234,
                    plant_group="COAL_BIT",
                    unit_id="1234_1",
                    pmax_mw=100.0 * marker,
                )
            ]

        monkeypatch.setattr(fleet_pkg, "load_fleet_from_csv", _fleet)
        monkeypatch.setattr(fleet_pkg, "load_retired_within_window", lambda *a, **k: [])

    def test_iso_plant_capacity_rekeys(self, monkeypatch, tmp_path):
        self._install_vintage_dependent_fleet(monkeypatch)
        a = tmp_path / "vA"  # 2 chars
        b = tmp_path / "vintage_2024"  # 12 chars
        a.mkdir()
        b.mkdir()

        _point_at(monkeypatch, a)
        warm_a = outages._iso_plant_capacity("SPP")
        _point_at(monkeypatch, b)
        warm_b = outages._iso_plant_capacity("SPP")

        assert warm_a == {(1234, "COAL"): 200.0}
        assert warm_b == {(1234, "COAL"): 1200.0}, (
            "the outage-derate DENOMINATOR served a stale vintage against the "
            "LP fleet built from a newer one -- the numerator/denominator basis "
            "split _iso_plant_capacity's own docstring forbids"
        )

    def test_iso_plant_unit_capacity_rekeys(self, monkeypatch, tmp_path):
        self._install_vintage_dependent_fleet(monkeypatch)
        a = tmp_path / "vA"
        b = tmp_path / "vintage_2024"
        a.mkdir()
        b.mkdir()

        _point_at(monkeypatch, a)
        warm_a = outages._iso_plant_unit_capacity("SPP")
        _point_at(monkeypatch, b)
        warm_b = outages._iso_plant_unit_capacity("SPP")

        assert warm_a == {(1234, "COAL"): {"1": 200.0}}
        assert warm_b == {(1234, "COAL"): {"1": 1200.0}}


class TestTheRepairIsAStrictNoOpAtAConstantVintage:
    """Leg 2 — every ISO but SPP, and every SPP single-year run.

    With ``eia860_vintage_tracks_solve_year`` off the active directory never
    moves (probe ``_spp37_vintage_cache_census.py`` §6), so the added key is one
    constant string and the cache must behave exactly as before: a hit, the same
    object back, one entry.
    """

    @pytest.mark.parametrize(
        ("pub", "core", "args"),
        [(p, c, a) for _m, p, c, a in _SHEET_BACKED],
        ids=[p for _m, p, _c, _a in _SHEET_BACKED],
    )
    def test_second_call_is_a_cache_hit_and_the_same_object(
        self, monkeypatch, vintages, pub, core, args
    ):
        mod = next(m for m, p, _c, _a in _SHEET_BACKED if p == pub)
        fn = getattr(mod, pub)
        a, _b = vintages
        _point_at(monkeypatch, a)

        first = fn(*args)
        second = fn(*args)
        info = getattr(mod, core).cache_info()

        assert second is first, f"{pub} rebuilt at a constant vintage"
        assert info.currsize == 1, f"{pub} holds {info.currsize} entries, expected 1"
        assert info.hits >= 1, f"{pub} never hit its cache"


class TestTheKeyingCannotBeRegressedAway:
    """Structural guard over all twelve: the shape itself, not a value."""

    @pytest.mark.parametrize(
        ("pub", "core"),
        [(p, c) for _m, p, c in REPAIRED],
        ids=[p for _m, p, _c in REPAIRED],
    )
    def test_public_name_is_uncached_and_the_core_is_directory_keyed(self, pub, core):
        mod = next(m for m, p, _c in REPAIRED if p == pub)
        public = getattr(mod, pub)
        cached = getattr(mod, core)

        assert not hasattr(public, "cache_info"), (
            f"{pub} is cached again. A cache on the public name is vintage-blind "
            "by construction -- that is the SPP-37 defect. Cache the core."
        )
        assert hasattr(cached, "cache_info"), f"{core} is not an lru_cache"
        first = next(iter(inspect.signature(cached).parameters))
        assert first == "eia860_dir", (
            f"{core}'s first parameter is {first!r}, not 'eia860_dir' -- the "
            "active EIA-860 directory must lead the cache key"
        )
