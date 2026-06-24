"""Tests for the PJM firm scheduled-export floor on the reference-price seam.

PJM exports to MISO / NYISO in ~87-100% of hours at a mean spread too thin for a
pure hourly energy-spread seam to clear every hour, because a large share is
firm, long-term SCHEDULED capacity/energy that flows regardless of the hourly
price (the export-direction mirror of the Manitoba/HQ firm imports). The economic
seam alone backs this firm base off in cheap-spread hours — the PJM 2023 NYISO
+4.3 vs +18.5 TWh miss.

:func:`inject_reference_price_firm_export` forces the cheapest export tranches on
at the measured firm base (``firm_export_floor_by_year``) by lowering their upper
bound (``pmax``) to a negative value — the seam's export rows are negative-output
sinks, so an upper bound of ``-x`` forces at least ``x`` MW of export.
"""

import unittest

import numpy as np

from market_sim.config.constants import INTERFACE_NEIGHBORS
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.transmission import (
    build_reference_price_node,
    inject_reference_price_firm_export,
)

T = 24


class _FA:
    """Minimal fleet-arrays stand-in for the seam pseudo-generators."""

    def __init__(self, gens):
        self.unit_ids = [g.unit_id for g in gens]
        self.pmax = np.array([g.pmax_mw for g in gens], dtype=float)
        self.pmin = np.array([g.pmin_mw for g in gens], dtype=float)
        self.availability = np.ones((len(gens), T))


def _spec(name):
    return next(n for n in INTERFACE_NEIGHBORS["PJM"] if n.name == name)


class TestFirmExportFloor(unittest.TestCase):
    def setUp(self):
        self.gens = build_reference_price_node("PJM")
        self.fa = _FA(self.gens)

    def _forced(self, name):
        """Return {tranche_k: pmax} for the forced export rows of a neighbor."""
        out = {}
        suffix = f"_refexp_{name}#"
        for r, uid in enumerate(self.fa.unit_ids):
            if suffix in uid and self.fa.pmax[r] != 0.0:
                out[int(uid.rsplit("#", 1)[1])] = self.fa.pmax[r]
        return out

    def test_floor_sums_to_measured_base_cheapest_first(self):
        applied = inject_reference_price_firm_export(self.fa, "PJM", 2023)
        self.assertTrue(applied)
        spec = _spec("MISO")
        floor = spec.firm_export_floor_by_year[2023]
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        forced = self._forced("MISO")
        # The cheapest bands (lowest k) are filled first; total forced == floor.
        self.assertAlmostEqual(-sum(forced.values()), floor)
        self.assertEqual(min(forced), 1)  # band 1 is the cheapest, filled first
        # Every fully-forced band is at the full step; only the last is partial.
        self.assertAlmostEqual(forced[1], -step)

    def test_floor_forces_export_lower_bound_feasible(self):
        inject_reference_price_firm_export(self.fa, "PJM", 2023)
        # A forced band's upper bound (pmax, negative) must stay >= its lower
        # bound (pmin = -step), so the LP stays feasible: output in [pmin, pmax].
        for r, uid in enumerate(self.fa.unit_ids):
            if "_refexp_" in uid and self.fa.pmax[r] != 0.0:
                self.assertGreaterEqual(self.fa.pmax[r], self.fa.pmin[r])
                self.assertLess(self.fa.pmax[r], 0.0)  # forces export

    def test_import_seams_get_no_floor(self):
        inject_reference_price_firm_export(self.fa, "PJM", 2023)
        # Carolinas / TVA / LGEE are net-import seams: no firm-export floor.
        for name in ("Carolinas", "TVA", "LGEE"):
            self.assertEqual(self._forced(name), {})

    def test_zero_floor_year_is_noop_for_seam(self):
        # MISO 2025 floor is 0 -> no MISO export row forced (NYISO still floored).
        inject_reference_price_firm_export(self.fa, "PJM", 2025)
        self.assertEqual(self._forced("MISO"), {})
        self.assertTrue(self._forced("NYISO"))

    def test_forecast_year_is_byte_identical(self):
        # No firm_export_floor_by_year entry for a forecast year -> no-op.
        before = self.fa.pmax.copy()
        applied = inject_reference_price_firm_export(self.fa, "PJM", 2030)
        self.assertFalse(applied)
        np.testing.assert_array_equal(self.fa.pmax, before)

    def test_non_pjm_iso_is_noop(self):
        applied = inject_reference_price_firm_export(self.fa, "ERCOT", 2023)
        self.assertFalse(applied)


if __name__ == "__main__":
    unittest.main()
