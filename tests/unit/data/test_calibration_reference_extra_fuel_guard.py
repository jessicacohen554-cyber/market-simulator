"""The incomplete-vintage swap loop covers an ISO's OWN extra benchmarked fuels.

Lane SPP-47, owner ruling P16 (2026-09-07), on ``FINDING-spp-43-2026-09-07.md``
§6 / ``FINDING-spp-57-2026-09-07.md`` R-15. ``_incomplete_renewable_fuels``
iterated the literal ``("wind", "solar")``, so a fuel this same builder already
declares first-order for an ISO in :data:`_EIA923_EXTRA_FUELS_BY_ISO` was scored
on a preliminary EIA-923 vintage that its own logic would have rejected for
wind: SPP 2025 hydro read 0.0233 TWh against EIA-930's 8.8299 (ratio 0.0026) —
by far the worst of SPP's three benchmarked classes, and the only one left
unswapped.

The candidate set is now ``("wind", "solar") + _EIA923_EXTRA_FUELS_BY_ISO.get
(iso, ())``. What these tests pin is that the repair is a CONSTRUCTION repair
and nothing more (rules 5 ``[R-NO-MAGIC]`` / 21 ``[R-DOF]`` / 23
``[R-FROZEN-DERIVE]``): same 0.80 threshold, same EIA-930 authority, same
per-fuel evaluation, no new parameter — and that it cannot reach an ISO that
declares no extras (rule 25 ``[R-ISO-SCOPE]``).

All EIA-930/EIA-923 values below are the measured ones from the lane's census,
so a regression names a real cell.
"""

from __future__ import annotations

import importlib.util
import unittest

from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "bcr_spp47", str(REPO_ROOT / "scripts" / "data" / "build_calibration_reference.py")
)
bcr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bcr)


class _Patched930:
    """Context manager pinning ``_eia930_annual_by_fuel`` to a fixed mapping."""

    def __init__(self, mapping: dict[str, float]) -> None:
        self._mapping = mapping
        self._orig = None

    def __enter__(self):
        self._orig = bcr._eia930_annual_by_fuel
        bcr._eia930_annual_by_fuel = lambda iso, year: self._mapping
        return self

    def __exit__(self, *exc):
        bcr._eia930_annual_by_fuel = self._orig
        return False


class TestExtraFuelsAreCandidates(unittest.TestCase):
    def test_spp_2025_hydro_is_swapped(self):
        """The cell the repair exists for: 0.0233/8.8299 = 0.0026, far below 0.80."""
        raw = {"wind": 87.7092, "solar": 1.6089, "hydro": 0.0233}
        e930 = {"wind": 110.4574, "solar": 2.3477, "hydro": 8.8299}
        with _Patched930(e930):
            self.assertEqual(
                sorted(bcr._incomplete_renewable_fuels("SPP", 2025, raw)),
                ["hydro", "solar", "wind"],
            )
            patched = bcr._guard_incomplete_eia923("SPP", 2025, raw)
        self.assertEqual(patched["hydro"], 8.8299)
        self.assertEqual(patched["wind"], 110.4574)

    def test_neiso_2025_oil_is_swapped_hydro_too(self):
        """Both of NEISO's extras move in 2025 (0.0177 and 0.7326)."""
        raw = {"wind": 0.0, "solar": 0.0, "hydro": 0.0907, "oil": 0.9092}
        e930 = {"wind": 4.6, "solar": 5.0, "hydro": 5.1207, "oil": 1.2411}
        with _Patched930(e930):
            got = sorted(bcr._incomplete_renewable_fuels("NEISO", 2025, raw))
        self.assertIn("hydro", got)
        self.assertIn("oil", got)


class TestUnchangedByConstruction(unittest.TestCase):
    def test_iso_without_extras_evaluates_only_wind_and_solar(self):
        """Rule 25 [R-ISO-SCOPE]: ERCOT/PJM/CAISO declare no extras, so the
        candidate set is exactly the former literal pair — a wildly under-counted
        hydro row cannot be swapped there even if one were present."""
        raw = {"wind": 100.0, "solar": 50.0, "hydro": 0.01}
        e930 = {"wind": 100.0, "solar": 50.0, "hydro": 9.0}
        for iso in ("ERCOT", "PJM", "CAISO"):
            self.assertEqual(bcr._EIA923_EXTRA_FUELS_BY_ISO.get(iso, ()), ())
            with _Patched930(e930):
                self.assertEqual(bcr._incomplete_renewable_fuels(iso, 2025, raw), [])

    def test_miso_oil_never_swaps_because_eia930_does_not_report_it(self):
        """MISO carries ``oil`` in its extras, but EIA-930 publishes no MISO oil
        series, so the ``ref <= 0.0`` guard skips it — the fuel stays on EIA-923
        rather than being zeroed out of the benchmark."""
        raw = {"wind": 100.0, "solar": 20.0, "hydro": 8.7887, "oil": 2.7871}
        e930 = {"wind": 100.0, "solar": 20.0, "hydro": 9.9790}
        with _Patched930(e930):
            got = bcr._incomplete_renewable_fuels("MISO", 2023, raw)
            patched = bcr._guard_incomplete_eia923("MISO", 2023, raw)
        self.assertNotIn("oil", got)
        self.assertEqual(patched["oil"], 2.7871)

    def test_threshold_and_strictness_unchanged(self):
        """Same 0.80 constant, still a STRICT ``<``: a fuel exactly at the
        fraction does not swap, and one just under does."""
        self.assertEqual(bcr._EIA923_RENEWABLE_COMPLETENESS_FRACTION, 0.80)
        e930 = {"wind": 1.0, "solar": 1.0, "hydro": 10.0}
        with _Patched930(e930):
            at = bcr._incomplete_renewable_fuels(
                "SPP", 2024, {"wind": 1.0, "solar": 1.0, "hydro": 8.0}
            )
            under = bcr._incomplete_renewable_fuels(
                "SPP", 2024, {"wind": 1.0, "solar": 1.0, "hydro": 7.999}
            )
        self.assertEqual(at, [])
        self.assertEqual(under, ["hydro"])

    def test_complete_vintage_is_a_no_op(self):
        """SPP 2023/2024 hydro agree with EIA-930 (1.0067 / 0.9697), so the
        guard leaves them on EIA-923 exactly as before the repair."""
        for year, v923, v930 in ((2023, 8.4002, 8.3441), (2024, 8.7018, 8.9734)):
            raw = {"wind": 100.0, "solar": 5.0, "hydro": v923}
            e930 = {"wind": 100.0, "solar": 5.0, "hydro": v930}
            with _Patched930(e930):
                self.assertEqual(
                    bcr._incomplete_renewable_fuels("SPP", year, raw), [], str(year)
                )

    def test_no_vintage_is_still_left_missing(self):
        """An empty ``raw`` (no EIA-923 release) is not fabricated from EIA-930."""
        with _Patched930({"hydro": 9.0}):
            self.assertEqual(bcr._incomplete_renewable_fuels("SPP", 2021, {}), [])

    def test_no_new_parameter_was_introduced(self):
        """Rules 5 [R-NO-MAGIC] / 21 [R-DOF]: the repair adds no constant of its
        own — the candidate set is composed from the table that already existed.

        This pins the FOUR entries that existed at the SPP-47 repair, and that
        every entry (those four included) still draws from the two-fuel
        vocabulary the loop can evaluate. It deliberately does NOT pin the
        dict WHOLE any more (relaxed 2026-09-14, lane NWPP-31): a whole-dict
        snapshot fails the moment a newly registered region declares a
        first-order class of its own — NWPP's conventional hydro, 106.9 /
        107.9 TWh, ~36 % of its footprint's energy and the largest benchmarked
        hydro in the repo — which is an ENTRY IN THE EXISTING REGISTRY, not a
        new parameter, and is exactly what rule 24 [R-REGISTRY] wants such a
        declaration to be. The property these rules actually care about is
        that the repair introduced no constant of its own and that no entry
        smuggles in a fuel the loop has no mask for, and that is what is
        asserted here.
        """
        for iso, fuels in (
            ("NYISO", ("hydro", "oil")),
            ("NEISO", ("hydro", "oil")),
            ("MISO", ("hydro", "oil")),
            ("SPP", ("hydro",)),
        ):
            self.assertEqual(bcr._EIA923_EXTRA_FUELS_BY_ISO[iso], fuels, iso)
        for iso, fuels in bcr._EIA923_EXTRA_FUELS_BY_ISO.items():
            self.assertTrue(
                set(fuels) <= {"hydro", "oil"},
                f"{iso} declares an extra fuel _eia923_generation_raw has no "
                f"mask for: {sorted(set(fuels) - {'hydro', 'oil'})}",
            )


if __name__ == "__main__":
    unittest.main()
