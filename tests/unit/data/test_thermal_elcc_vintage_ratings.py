"""capx D84 — the delivery-year VINTAGE axis on PJM THERMAL accreditation.

The thermal transpose of ``test_renewable_elcc_curves.py``'s D75-R block, on
the other axis of the same registry. What is locked here, in the order the
rules weigh it:

* **Rule 13/21/24 — every rating re-derives from the committed source rows.**
  ``THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`` is reconciled BYTE-FOR-BYTE
  against ``data/raw/capacity-market/elcc/pjm/pjm.csv``, so the registry holds
  no typed number and no free parameter. Unlike the VRE half there is not even
  one reconciliation to declare: PJM rates each of the model's thermal classes
  with exactly ONE published class.
* **The admissibility rule** — class-average AND official/final only — is
  asserted against the csv rather than assumed, so a preliminary or marginal
  row can never silently enter the registry.
* **Rule 19 ``[R-ONE-MECH]``** — the rating axis cannot be devintaged while the
  BASIS axis (capx D48) is not, and the two COMPOSE rather than stack: a
  pre-reform delivery year never reaches this registry at all.
* **Rule 25 ``[R-ISO-SCOPE]``** — inert on every ISO but PJM.
* **Byte-identity unarmed**, at ``year=None``, in a plain backcast, and past
  both edges of the table (no hold-last).
"""

import unittest

from market_sim.config.constants import (
    THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO,
)
from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import (
    resolve_thermal_accreditation_basis,
    resolve_thermal_vintage_rating,
    thermal_accreditation_fraction,
    thermal_accreditation_vintage_armed,
)

# The model fuel -> PJM published class map the INCUMBENT single-vintage table
# already uses, restated here so the vintage axis is proven to reuse it rather
# than re-map anything (re-mapping a class would be a second mechanism on the
# same phenomenon — rule 19).
_FUEL_TO_PJM_CLASS = {
    "nuclear": "Nuclear",
    "coal": "Coal",
    "gas_cc": "Gas Combined Cycle",
    "gas_ct": "Gas Combustion Turbine",
    "gas_st": "Steam",
    "oil": "Diesel Utility",
}

# The three vintages the admissibility rule admits, and the delivery year each
# governs. Written out so the test states the RULE, not just its output.
_PJM_DY_PUBLISHED = {
    "2025/2026": "2025/2026 3IA (final for DY 2025/2026; posted 2025-03-12)",
    "2026/2027": "2026/2027 BRA (official/final)",
    "2027/2028": "2027/2028 BRA (official/final)",
}

_EFORD = 0.07


def _rows():
    import csv

    path = RAW_DIR / "capacity-market" / "elcc" / "pjm" / "pjm.csv"
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _config(*, thermal: bool, design: bool = True, iso: str = "PJM", **kw):
    return ScenarioConfig(
        mode="forecast",
        iso=iso,
        hindcast=True,
        pjm_accreditation_design_vintage=design,
        pjm_thermal_accreditation_vintage=thermal,
        **kw,
    )


class ThermalElccVintageRegistryTest(unittest.TestCase):
    """The registry itself: reconciliation, admissibility, class mapping."""

    def test_every_rating_rederives_from_the_committed_rows(self):
        """Verbatim transcription — the whole DOF story is that there is none.

        Rules 21/24: nothing here is fitted and nothing is blended, so every
        encoded value must equal its published row exactly.
        """
        rows = _rows()

        def _rating(vintage: str, cls: str) -> float:
            hits = [
                float(r["elcc_pct"])
                for r in rows
                if r["study_vintage"] == vintage and r["resource_class"] == cls
            ]
            self.assertEqual(len(hits), 1, f"{vintage} / {cls}")
            return hits[0]

        table = THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]
        self.assertEqual(set(table), set(_PJM_DY_PUBLISHED))
        for dy, vintage in _PJM_DY_PUBLISHED.items():
            self.assertEqual(set(table[dy]), set(_FUEL_TO_PJM_CLASS), dy)
            for fuel, cls in _FUEL_TO_PJM_CLASS.items():
                self.assertAlmostEqual(
                    table[dy][fuel], _rating(vintage, cls) / 100.0, 12, f"{dy}/{fuel}"
                )

    def test_the_admissibility_rule_holds_against_the_csv(self):
        """Class-average AND official/final only — never a marginal or preliminary row.

        The rule was fixed before any solve and is not selectable by a result;
        this asserts it against the source rather than trusting the comment.
        """
        rows = _rows()
        for vintage in _PJM_DY_PUBLISHED.values():
            hits = [r for r in rows if r["study_vintage"] == vintage]
            self.assertTrue(hits, vintage)
            for r in hits:
                self.assertEqual(r["elcc_type"], "class_average", vintage)
            self.assertNotIn("preliminary", vintage.lower())

        # And the marginal series is genuinely present in the csv, so the
        # exclusion above is doing work rather than being vacuous.
        marginal = {
            r["study_vintage"]
            for r in rows
            if r["elcc_type"] == "marginal"
            and r["resource_class"] in set(_FUEL_TO_PJM_CLASS.values())
        }
        self.assertTrue(marginal)
        self.assertFalse(marginal & set(_PJM_DY_PUBLISHED.values()))

    def test_the_2026_27_row_equals_the_incumbent_single_vintage_table(self):
        """If these two ever diverge, one of them is wrong.

        The incumbent table's own comment declares it to BE the 2026/2027 BRA
        official/final set, so the registry's 2026/2027 row is an exact no-op
        against it by construction.
        """
        self.assertEqual(
            THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]["2026/2027"],
            THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"],
        )

    def test_the_2025_26_row_is_the_defect_and_it_differs(self):
        """DY 2025/26 is the reform's FIRST year and its own ratings differ.

        The premise of the whole card, asserted rather than narrated: gas CC
        78 vs 74, CT 63 vs 60, steam 74 vs 73, diesel 92 vs 91; nuclear and
        coal equal.
        """
        self.assertEqual(
            THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"], "2025/2026"
        )
        incumbent = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]
        vintaged = THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]["2025/2026"]
        deltas = {f: round(vintaged[f] - incumbent[f], 12) for f in incumbent}
        self.assertEqual(
            deltas,
            {
                "nuclear": 0.0,
                "coal": 0.0,
                "gas_cc": 0.04,
                "gas_ct": 0.03,
                "gas_st": 0.01,
                "oil": 0.01,
            },
        )

    def test_biomass_has_no_class_here_either(self):
        """A model fuel the incumbent table omits stays omitted (rule 25 spirit).

        PJM publishes no thermal ELCC class for model ``biomass`` in any
        admitted vintage, so it keeps its UCAP fallback under BOTH arms — the
        vintage axis never invents a class.
        """
        for dy in _PJM_DY_PUBLISHED:
            self.assertNotIn(
                "biomass", THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"][dy]
            )
        armed = _config(thermal=True)
        self.assertAlmostEqual(
            thermal_accreditation_fraction("biomass", _EFORD, "PJM", armed, 2025),
            1.0 - _EFORD,
            12,
        )


class ThermalElccVintageGateTest(unittest.TestCase):
    """The predicate, the resolver, and byte-identity everywhere it is off."""

    def test_default_config_is_unarmed_and_the_ladder_is_unchanged(self):
        default = ScenarioConfig(mode="forecast", iso="PJM", hindcast=True)
        self.assertFalse(default.pjm_thermal_accreditation_vintage)
        self.assertFalse(thermal_accreditation_vintage_armed(default, "PJM"))

    def test_armed_fractions_are_the_delivery_years_own_published_ratings(self):
        ctl, arm = _config(thermal=False), _config(thermal=True)
        vintaged = THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]["2025/2026"]
        for fuel, want in vintaged.items():
            self.assertAlmostEqual(
                thermal_accreditation_fraction(fuel, _EFORD, "PJM", arm, 2025), want, 12
            )
            self.assertAlmostEqual(
                thermal_accreditation_fraction(fuel, _EFORD, "PJM", ctl, 2025),
                THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"][fuel],
                12,
            )

    def test_pre_reform_years_never_reach_the_registry(self):
        """The two axes COMPOSE, never stack (rule 19).

        Under the D48 arm every delivery year before the reform entry resolves
        the UCAP basis, so the ``elcc_class_rating`` branch — the registry's
        only reader — is not taken and the arm is byte-identical there.
        """
        ctl, arm = _config(thermal=False), _config(thermal=True)
        for year in (2021, 2022, 2023, 2024):
            self.assertEqual(
                resolve_thermal_accreditation_basis("PJM", arm, year), "ucap"
            )
            for fuel in _FUEL_TO_PJM_CLASS:
                self.assertEqual(
                    thermal_accreditation_fraction(fuel, _EFORD, "PJM", arm, year),
                    thermal_accreditation_fraction(fuel, _EFORD, "PJM", ctl, year),
                    f"{year}/{fuel}",
                )
                self.assertAlmostEqual(
                    thermal_accreditation_fraction(fuel, _EFORD, "PJM", arm, year),
                    1.0 - _EFORD,
                    12,
                )

    def test_no_hold_last_past_the_last_tabulated_delivery_year(self):
        """Past 2027/2028 the incumbent table is the right basis and is used."""
        ctl, arm = _config(thermal=False), _config(thermal=True)
        for year in (2028, 2035):
            self.assertIsNone(
                resolve_thermal_vintage_rating(arm, "PJM", "gas_ct", year), year
            )
            for fuel in _FUEL_TO_PJM_CLASS:
                self.assertEqual(
                    thermal_accreditation_fraction(fuel, _EFORD, "PJM", arm, year),
                    thermal_accreditation_fraction(fuel, _EFORD, "PJM", ctl, year),
                    f"{year}/{fuel}",
                )

    def test_the_thermal_half_cannot_be_armed_without_the_d48_basis_half(self):
        alone = _config(thermal=True, design=False)
        self.assertFalse(thermal_accreditation_vintage_armed(alone, "PJM"))
        for fuel in _FUEL_TO_PJM_CLASS:
            self.assertAlmostEqual(
                thermal_accreditation_fraction(fuel, _EFORD, "PJM", alone, 2025),
                THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"][fuel],
                12,
            )

    def test_inert_on_every_other_iso(self):
        """Rule 25: no ISO inherits PJM's verdict, armed flag or not."""
        for iso in ("ERCOT", "CAISO", "MISO", "NYISO", "NEISO", "SPP", "NWPP"):
            armed = _config(thermal=True, iso=iso)
            self.assertFalse(thermal_accreditation_vintage_armed(armed, iso), iso)
            self.assertIsNone(
                resolve_thermal_vintage_rating(armed, iso, "gas_cc", 2025), iso
            )

    def test_year_none_is_byte_identical_to_the_pre_d84_resolver(self):
        arm = _config(thermal=True)
        for fuel in _FUEL_TO_PJM_CLASS:
            self.assertAlmostEqual(
                thermal_accreditation_fraction(fuel, _EFORD, "PJM", arm, None),
                THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"][fuel],
                12,
            )
        self.assertIsNone(resolve_thermal_vintage_rating(arm, "PJM", "gas_cc", None))
        self.assertIsNone(resolve_thermal_vintage_rating(None, "PJM", "gas_cc", 2025))
        self.assertIsNone(resolve_thermal_vintage_rating(arm, None, "gas_cc", 2025))

    def test_a_plain_backcast_coerces_the_gate_off(self):
        back = ScenarioConfig(
            mode="backcast",
            iso="PJM",
            pjm_accreditation_design_vintage=True,
            pjm_thermal_accreditation_vintage=True,
        )
        self.assertFalse(back.pjm_thermal_accreditation_vintage)
        self.assertFalse(thermal_accreditation_vintage_armed(back, "PJM"))

    def test_the_gate_keys_distinctly_and_leaves_the_unarmed_key_stable(self):
        """Registered in the cache key's optional-field drop list at False."""
        ctl, arm = _config(thermal=False), _config(thermal=True)
        bare = ScenarioConfig(
            mode="forecast",
            iso="PJM",
            hindcast=True,
            pjm_accreditation_design_vintage=True,
        )
        self.assertEqual(ctl.cache_key(), bare.cache_key())
        self.assertNotEqual(arm.cache_key(), ctl.cache_key())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
