"""Tests for the T1-H Phase-1 Leg A storage entry repairs (D-2 + D-3).

Charter: ``docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md`` Phase-1; defect
register ``docs/FINDING-entry-screen-t1h-2026-08.md``; census/replay
``docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md``. Two GATED mechanisms
— **default-ON since owner ruling R-A of the 2026-08-31 director sitting**
("Arm both", on the A/B record
``docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md`` §4) — each shared by BOTH
storage allocation rules through one helper (rule 19):

* ``storage_entry_availability_gate`` (D-2) — the candidate pool admits a
  technology only at/after its measured first-US-operating year
  (``STORAGE_TECH_AVAILABLE_YEAR``), fail-closed for a class with zero
  national operating base ever;
* ``storage_entry_cost_normalized_rank`` (D-3) — clearing technologies are
  ranked on margin per unit capital cost instead of absolute $/MW-yr;
  sign-preserving, so WHICH technologies clear is unchanged.

Trivial cases first (the helpers on synthetic two-tech registries), then the
live allocators — bang-bang and the D11-R walk — on both synthetic and the
real ``STORAGE_TECHS`` registry. The config refusal surface (cache-key
registration, backcast coercion) is asserted alongside.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.constants import STORAGE_TECH_AVAILABLE_YEAR, STORAGE_TECHS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.storage import (
    _storage_entry_candidates,
    _storage_entry_rank_score,
    apply_storage_new_entry,
    build_default_storage,
)

HOURS = 8760


def _cfg(*, gate: bool = False, rank: bool = False, **kw) -> ScenarioConfig:
    """A config with BOTH storage-entry mechanisms pinned EXPLICITLY.

    Every mechanism case below isolates one leg, so it must not inherit the
    other leg's shipped default — which is ON since the 2026-08-31 R-A arming.
    Pinning both keeps each case meaningful whatever the defaults become; the
    shipped posture itself is asserted once, in :class:`TestConfigFields`.
    """
    return ScenarioConfig(
        storage_entry_availability_gate=gate,
        storage_entry_cost_normalized_rank=rank,
        **kw,
    )


def _high_spread_prices() -> np.ndarray:
    """12 cheap / 12 expensive hours per day — every tech's screen clears."""
    day = np.concatenate([np.full(12, 10.0), np.full(12, 300.0)])
    return np.tile(day, 365)


# Synthetic two-tech registry for deterministic ranking assertions:
# ``big`` earns the larger ABSOLUTE margin (more duration), ``small`` the
# larger margin PER $/kW (a quarter of the capital). cycles=0 disables the
# degradation term so the arithmetic stays transparent.
_SYNTH_TECHS = {
    "big": {
        "duration_hr": 8,
        "rte": 0.80,
        "cycles": 0,
        "capex_per_kw": 4000.0,
        "capex_per_kwh": 500.0,
        "fom_per_kw_yr": 0.0,
    },
    "small": {
        "duration_hr": 4,
        "rte": 0.80,
        "cycles": 0,
        "capex_per_kw": 1000.0,
        "capex_per_kwh": 250.0,
        "fom_per_kw_yr": 0.0,
    },
}


def _patch_synth(available=None):
    """Patch the storage module onto the synthetic registry (and gate map)."""
    patches = [
        mock.patch("market_sim.model.storage.STORAGE_TECHS", _SYNTH_TECHS),
    ]
    if available is not None:
        patches.append(
            mock.patch(
                "market_sim.model.storage.STORAGE_TECH_AVAILABLE_YEAR", available
            )
        )
    return patches


class _InertWalk:
    """Duck-typed D11-R repricer whose signal never moves.

    An inert walk must reproduce the bang-bang totals exactly (the
    test_entry_margin_exhaustion invariant), so it exposes the walk's
    candidate loop and per-tranche pick to the same assertions as the
    bang-bang path without exercising the repricing feedback.
    """

    def add_storage(self, mw, duration_hr, rte):
        pass

    def signal(self, consumed):
        return np.asarray(consumed, dtype=float)


def _mw_by_tech(existing, fleet):
    """Total NEW power MW by tech_name (fleet minus the existing units)."""
    existing_ids = {u.unit_id for u in existing}
    out: dict[str, float] = {}
    for u in fleet:
        if u.unit_id in existing_ids:
            continue
        out[u.tech_name] = out.get(u.tech_name, 0.0) + u.power_cap_mw
    return out


class TestConfigFields(unittest.TestCase):
    """Field registration, defaults, cache-key stability, backcast coercion."""

    def test_defaults_armed(self):
        """Both mechanisms ship ON since the 2026-08-31 R-A arming."""
        cfg = ScenarioConfig()
        self.assertTrue(cfg.storage_entry_availability_gate)
        self.assertTrue(cfg.storage_entry_cost_normalized_rank)

    def test_disarmed_moves_cache_key(self):
        """An EXPLICIT disarm is non-default, so control arms stay separable.

        The post-arming direction of the pre-flip ``test_armed_moves_cache_key``:
        ``cache_key()`` drops a ``_CACHE_KEY_OPTIONAL_FIELDS`` member at the LIVE
        default, so it is now the OFF value that hashes distinctly. The armed
        default deliberately does NOT move the key — that same-key collision is
        the declared cache epoch (``results/cache.py``, epoch 2026-08-31), not a
        property this suite can assert away.
        """
        base = ScenarioConfig().cache_key()
        k_gate = ScenarioConfig(storage_entry_availability_gate=False).cache_key()
        k_rank = ScenarioConfig(storage_entry_cost_normalized_rank=False).cache_key()
        self.assertNotEqual(k_gate, base)
        self.assertNotEqual(k_rank, base)
        self.assertNotEqual(k_gate, k_rank)

    def test_default_key_pin_unmoved_by_the_arming(self):
        """The global default-config pin is untouched by the flip (measured)."""
        self.assertEqual(ScenarioConfig().cache_key(), "e5ecd4105ada3e58")

    def test_backcast_coerces_off(self):
        cfg = ScenarioConfig(
            mode="backcast",
            storage_entry_availability_gate=True,
            storage_entry_cost_normalized_rank=True,
        )
        self.assertFalse(cfg.storage_entry_availability_gate)
        self.assertFalse(cfg.storage_entry_cost_normalized_rank)

    def test_backcast_key_invariant_to_arming(self):
        """A backcast hashes the same however the fields are passed.

        The coercion is load-bearing after the R-A arming — the runner reaches
        the storage-entry screen on year 2+ of ANY multi-year run, so a backcast
        inheriting the armed default must be pinned off. This asserts the
        invariant that survives the flip: whatever a caller passes, a backcast
        lands on ONE key and one behaviour. (The absolute backcast key did move
        at the arming, since coerced-off is now non-default; that is recorded in
        the cache-epoch ledger, and is a one-time cache miss, never a different
        answer.)
        """
        bare = ScenarioConfig(mode="backcast")
        armed = ScenarioConfig(
            mode="backcast",
            storage_entry_availability_gate=True,
            storage_entry_cost_normalized_rank=True,
        )
        self.assertEqual(bare.cache_key(), armed.cache_key())


class TestAvailabilityYearRegistry(unittest.TestCase):
    """The measured STORAGE_TECH_AVAILABLE_YEAR constant."""

    def test_every_storage_tech_has_an_entry(self):
        # Fail-closed depends on the mapping being complete: a tech missing
        # from it would silently never build under the gate, so completeness
        # is asserted rather than assumed.
        self.assertEqual(set(STORAGE_TECH_AVAILABLE_YEAR), set(STORAGE_TECHS))

    def test_values_are_years_or_fail_closed(self):
        for tech, year in STORAGE_TECH_AVAILABLE_YEAR.items():
            if year is None:
                continue  # fail-closed (zero national base of the class ever)
            self.assertIsInstance(year, int, tech)
            # EIA-860 derivation bounds: no US grid storage class predates the
            # earliest measured record and none postdates the 2025 ER vintage.
            self.assertGreaterEqual(year, 1990, tech)
            self.assertLessEqual(year, 2025, tech)

    def test_li_ion_durations_share_the_lib_class_year(self):
        # EIA-860 classes by chemistry (LIB), not duration — the derivation
        # note's contract.
        self.assertEqual(
            len(
                {
                    STORAGE_TECH_AVAILABLE_YEAR[t]
                    for t in ("li_ion_4hr", "li_ion_8hr", "li_ion_12hr")
                }
            ),
            1,
        )

    def test_compressed_air_is_fail_closed(self):
        # The modeled class is non-cavern adiabatic CAES with zero national
        # operating base ever (the only US CAES generator is diabatic
        # salt-cavern) — see the constant's derivation note.
        self.assertIsNone(STORAGE_TECH_AVAILABLE_YEAR["compressed_air"])


class TestCandidatesHelper(unittest.TestCase):
    """_storage_entry_candidates: trivial cases on the synthetic registry."""

    def test_gate_off_returns_full_pool_in_registry_order(self):
        cfg = _cfg()
        for p in _patch_synth({"big": 2020, "small": None}):
            p.start()
            self.addCleanup(p.stop)
        self.assertEqual(
            _storage_entry_candidates(2023, cfg),
            list(_SYNTH_TECHS.items()),
        )

    def test_gate_admits_only_available_years(self):
        cfg = _cfg(gate=True)
        for p in _patch_synth({"big": 2020, "small": 2025}):
            p.start()
            self.addCleanup(p.stop)
        self.assertEqual([t for t, _ in _storage_entry_candidates(2023, cfg)], ["big"])
        # A tech becomes admissible exactly AT its first observed year.
        self.assertEqual(
            [t for t, _ in _storage_entry_candidates(2025, cfg)], ["big", "small"]
        )
        self.assertEqual(_storage_entry_candidates(2019, cfg), [])

    def test_gate_fails_closed_on_none_and_on_missing_entries(self):
        cfg = _cfg(gate=True)
        # ``small`` has a None entry; ``big`` is missing from the map entirely.
        for p in _patch_synth({"small": None}):
            p.start()
            self.addCleanup(p.stop)
        self.assertEqual(_storage_entry_candidates(2050, cfg), [])

    def test_gate_on_real_registry_2023(self):
        # The Phase-0 anachronism year: iron_air (2024) and the fail-closed
        # compressed_air are out; the three li-ion classes (2012) and
        # flow_battery (2017) are in.
        cfg = _cfg(gate=True)
        admitted = {t for t, _ in _storage_entry_candidates(2023, cfg)}
        self.assertEqual(
            admitted, {"li_ion_4hr", "li_ion_8hr", "li_ion_12hr", "flow_battery"}
        )
        # iron_air enters the pool exactly at its measured first year.
        self.assertIn("iron_air", {t for t, _ in _storage_entry_candidates(2024, cfg)})


class TestRankScoreHelper(unittest.TestCase):
    """_storage_entry_rank_score: trivial cases."""

    def test_off_is_the_margin_identity(self):
        cfg = _cfg()
        self.assertEqual(_storage_entry_rank_score("li_ion_4hr", 123.4, cfg), 123.4)

    def test_on_normalizes_by_capex(self):
        cfg = _cfg(rank=True)
        capex = float(STORAGE_TECHS["li_ion_4hr"]["capex_per_kw"])
        self.assertAlmostEqual(
            _storage_entry_rank_score("li_ion_4hr", 1000.0, cfg), 1000.0 / capex
        )

    def test_sign_preserving(self):
        # The flag re-orders clearing techs; it must never flip who clears.
        cfg = _cfg(rank=True)
        for margin in (-5.0, 0.0, 5.0):
            self.assertEqual(
                np.sign(_storage_entry_rank_score("iron_air", margin, cfg)),
                np.sign(margin),
            )


class TestBangBangAllocator(unittest.TestCase):
    """The winner-take-share split under the two flags (synthetic registry)."""

    def _run(self, cfg, year=2027, entry_reprice=None):
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, cfg)
        fleet = apply_storage_new_entry(
            existing,
            _high_spread_prices(),
            year,
            cfg,
            "ERCOT",
            entry_reprice=entry_reprice,
        )
        return _mw_by_tech(existing, fleet)

    def test_flags_off_ranks_absolute(self):
        # ``big`` leads on absolute margin -> slot 1 (3,000 = 5,000 x 0.6).
        for p in _patch_synth():
            p.start()
            self.addCleanup(p.stop)
        built = self._run(_cfg())
        self.assertAlmostEqual(built["big"], 3000.0, places=6)
        self.assertAlmostEqual(built["small"], 2000.0, places=6)

    def test_rank_flag_flips_to_per_capex(self):
        # ``small`` leads on margin per $/kW -> slot 1 under the D-3 metric.
        for p in _patch_synth():
            p.start()
            self.addCleanup(p.stop)
        built = self._run(_cfg(rank=True))
        self.assertAlmostEqual(built["small"], 3000.0, places=6)
        self.assertAlmostEqual(built["big"], 2000.0, places=6)

    def test_gate_excludes_unavailable_tech(self):
        for p in _patch_synth({"big": 2020, "small": 2030}):
            p.start()
            self.addCleanup(p.stop)
        built = self._run(_cfg(gate=True), year=2027)
        self.assertNotIn("small", built)
        self.assertAlmostEqual(built["big"], 3000.0, places=6)

    def test_real_registry_gate_2023_builds_no_anachronism(self):
        # The Phase-0 defect case on the live registry: a 2023 decision year
        # must not build iron_air (first US MW 2024) or compressed_air
        # (fail-closed) under the gate; ungated it builds iron_air (D-2).
        cfg_on = _cfg(gate=True)
        built_on = self._run(cfg_on, year=2023)
        self.assertNotIn("iron_air", built_on)
        self.assertNotIn("compressed_air", built_on)
        self.assertGreater(sum(built_on.values()), 0.0)
        built_off = self._run(_cfg(), year=2023)
        self.assertIn("iron_air", built_off)


class TestWalkAllocator(unittest.TestCase):
    """The D11-R walk consumes the SAME gate and ranking (rule 19)."""

    def _run(self, cfg, year=2027):
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, cfg)
        fleet = apply_storage_new_entry(
            existing,
            _high_spread_prices(),
            year,
            cfg,
            "ERCOT",
            entry_reprice=_InertWalk(),
        )
        return _mw_by_tech(existing, fleet)

    def test_walk_gate_excludes_unavailable_tech(self):
        for p in _patch_synth({"big": 2020, "small": 2030}):
            p.start()
            self.addCleanup(p.stop)
        built = self._run(_cfg(gate=True), year=2027)
        self.assertNotIn("small", built)
        self.assertAlmostEqual(built.get("big", 0.0), 3000.0, places=6)

    def test_walk_rank_flag_flips_to_per_capex(self):
        for p in _patch_synth():
            p.start()
            self.addCleanup(p.stop)
        built = self._run(_cfg(rank=True))
        # An inert walk reproduces the bang-bang split, so the D-3 flip must
        # match TestBangBangAllocator.test_rank_flag_flips_to_per_capex.
        self.assertAlmostEqual(built["small"], 3000.0, places=6)
        self.assertAlmostEqual(built["big"], 2000.0, places=6)

    def test_walk_flags_off_matches_bang_bang(self):
        # Both flags off: the inert walk and the bang-bang split agree — the
        # helpers are byte-identical pass-throughs on the off path.
        for p in _patch_synth():
            p.start()
            self.addCleanup(p.stop)
        cfg = _cfg()
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, cfg)
        bang = _mw_by_tech(
            existing,
            apply_storage_new_entry(
                existing, _high_spread_prices(), 2027, cfg, "ERCOT"
            ),
        )
        walk = _mw_by_tech(
            existing,
            apply_storage_new_entry(
                existing,
                _high_spread_prices(),
                2027,
                cfg,
                "ERCOT",
                entry_reprice=_InertWalk(),
            ),
        )
        self.assertEqual(set(bang), set(walk))
        for tech, mw in bang.items():
            self.assertAlmostEqual(mw, walk[tech], places=6, msg=tech)


if __name__ == "__main__":
    unittest.main()
