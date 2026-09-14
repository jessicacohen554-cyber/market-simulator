"""capx D62 — the published going-forward BAR gate, pre-solve tests.

The gate replaces the retirement screen's ATB FOM proxy with PJM's OWN
published default gross Avoidable Cost Rate (Manual 18 Rev 62 §5.4.8.4(B)) and
credits the tariff's published reactive component as the single out-of-market
leg of the screen's margin. Charter: ``docs/handoffs/
PRECOMMIT-capx-d62-pjm-acr-bar-2026-09-06.md``; measurement it executes:
``docs/handoffs/FINDING-capx-d61-2026-09-05.md`` §4.

Five properties, one test class each:

1. the OFF path is byte-identical arithmetic and cache-neutral;
2. the resolver returns the ATB path for every non-armed ISO, and for a fuel
   class the armed ISO publishes no row for;
3. the VINTAGE RULE is what ``pjm.csv`` says, asserted from the data (rule 21:
   the rule is fixed in code and cannot be selected by a result);
4. offer == exit identity — the D57 clearing's sell-offer cap and the screen's
   bar are ONE object, so a unit's offer is zero exactly when it passes;
5. the reactive credit enters ONCE, and never on the off path.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config import paths
from market_sim.config.capacity_market import (
    resolve_capacity_going_forward_bar_published,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.avoidable_cost_rate import (
    PUBLISHED_ACR_CLASS_BY_FUEL,
    published_bar_per_kw_yr,
    reactive_offset_per_mw_yr,
)
from market_sim.model.capacity_evolution.retirements import (
    _FOM_MULTIPLIER,
    _THERMAL_FOM,
    resolve_going_forward_bar_per_kw_yr,
)
from scripts.lib import capacity_market_avoidable_cost_rate as acr
from tests.helpers.base import requires_raw

FIELD = "capacity_going_forward_bar_published_by_iso"
SCREENED_FUELS = tuple(_THERMAL_FOM)

# The raw source the two DATA-TIER classes below ultimately read: PJM's own
# published Manual 18 §5.4.8.4(B) table, tracked in the repo. ``requires_raw``
# marks them ``fulldata`` (so the fast lane deselects them) AND skips them when
# that CSV is genuinely absent — the repo's standing idiom for a raw dependency
# (tests/helpers/base.py). The bare ``fulldata`` marker they carried before was
# necessary but not sufficient: it promises ``data/raw``, while the seam reads
# the DERIVED ``data/clean`` partition nothing in the test tier builds, so with
# raw fully present the classes still raised ``PublishedBarUnavailable`` on any
# checkout that had not run the curation script (capx D89). The
# ``published_acr_clean_dir`` fixture builds that partition from THIS file,
# through the real intake, into a scratch CLEAN_DIR.
PUBLISHED_ACR_RAW_CSV = acr.raw_dir_for("PJM", paths.RAW_DIR) / "pjm.csv"


def _fc(**kw) -> ScenarioConfig:
    """A forecast-mode config (the only mode the screen runs in)."""
    return ScenarioConfig(iso=kw.pop("iso", "PJM"), mode="forecast", **kw)


class TestOffPathByteIdentityAndCacheNeutrality:
    def test_default_is_none_for_every_iso(self):
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP"):
            cfg = _fc(iso=iso)
            assert getattr(cfg, FIELD) is None
            assert resolve_capacity_going_forward_bar_published(cfg, iso) is False

    def test_off_path_is_the_atb_expression_exactly(self):
        """Gate off, the resolver IS ``fixed_om x multiplier`` — bit for bit."""
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP"):
            cfg = _fc(iso=iso)
            for fuel, fom_field in _THERMAL_FOM.items():
                mult = getattr(cfg, _FOM_MULTIPLIER.get(fuel, ""), 1.0)
                want = float(getattr(cfg, fom_field)) * float(mult)
                got, basis = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2030)
                assert got == want, (iso, fuel)
                assert basis == "atb_fom"

    def test_field_is_registered_with_its_declared_default(self):
        assert FIELD in _CACHE_KEY_OPTIONAL_FIELDS
        assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[FIELD] == "None"

    def test_cache_key_unmoved_absent_and_explicitly_none(self):
        """The bare keys must not move — PRECOMMIT §6 STOP 2."""
        for mode in ("forecast", "backcast"):
            bare = ScenarioConfig(iso="PJM", mode=mode)
            explicit_none = ScenarioConfig(iso="PJM", mode=mode, **{FIELD: None})
            assert explicit_none.cache_key() == bare.cache_key(), mode

    def test_armed_row_keys_distinctly(self):
        bare = _fc()
        armed = dataclasses.replace(bare, **{FIELD: {"PJM": True}})
        assert armed.cache_key() != bare.cache_key()

    def test_backcast_coerces_the_gate_off(self):
        """A plain backcast runs no capacity evolution — keepers byte-identical."""
        cfg = ScenarioConfig(iso="PJM", mode="backcast", **{FIELD: {"PJM": True}})
        assert getattr(cfg, FIELD) is None
        assert cfg.cache_key() == ScenarioConfig(iso="PJM", mode="backcast").cache_key()

    def test_no_scalar_companion_field_exists(self):
        """The values are DATA (rule 24) — a scalar knob must never appear."""
        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        assert "capacity_going_forward_bar_published" not in names
        assert not any(
            n.startswith("published_acr") or n.startswith("going_forward_bar")
            for n in names
        )


class TestResolutionScope:
    def test_armed_row_for_one_iso_does_not_reach_another(self):
        cfg = _fc(iso="MISO", **{FIELD: {"PJM": True}})
        assert resolve_capacity_going_forward_bar_published(cfg, "MISO") is False
        for fuel in SCREENED_FUELS:
            _, basis = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2030)
            assert basis == "atb_fom", fuel

    def test_armed_iso_without_a_published_table_keeps_the_atb_path(self):
        """Generic in form, PJM-scoped by DATA (rule 25)."""
        cfg = _fc(iso="MISO", **{FIELD: {"MISO": True}})
        assert resolve_capacity_going_forward_bar_published(cfg, "MISO") is True
        for fuel in SCREENED_FUELS:
            mult = getattr(cfg, _FOM_MULTIPLIER.get(fuel, ""), 1.0)
            want = float(getattr(cfg, _THERMAL_FOM[fuel])) * float(mult)
            got, basis = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2030)
            assert got == want and basis == "atb_fom_unpublished", fuel

    def test_unpublished_fuel_class_keeps_the_atb_path_under_an_armed_gate(self):
        """``gas_cc_ccs`` is not one of PJM's eight published resource types."""
        cfg = _fc(**{FIELD: {"PJM": True}})
        assert "gas_cc_ccs" not in PUBLISHED_ACR_CLASS_BY_FUEL["PJM"]
        got, basis = resolve_going_forward_bar_per_kw_yr(cfg, "gas_cc_ccs", 2030)
        assert basis == "atb_fom_unpublished"
        assert got == float(cfg.fixed_om_gas_cc_ccs) * float(
            cfg.retirement_fom_multiplier_gas_cc_ccs
        )

    def test_armed_gate_without_a_year_raises(self):
        cfg = _fc(**{FIELD: {"PJM": True}})
        with pytest.raises(ValueError, match="requires a simulation year"):
            resolve_going_forward_bar_per_kw_yr(cfg, "coal", None)


@requires_raw(PUBLISHED_ACR_RAW_CSV)
@pytest.mark.usefixtures("published_acr_clean_dir")
class TestVintageRuleFromTheData:
    """The vintage rule, asserted from ``pjm.csv`` itself (rule 21).

    DATA TIER: it reads the curated partition, which is derived from
    ``data/raw`` and gitignored, so ``published_acr_clean_dir`` curates the
    tracked raw CSV into a scratch CLEAN_DIR first.
    """

    # $/MW-day as published, per PRECOMMIT §1.1's table.
    EARLY = {
        "coal": 80.0,
        "gas_cc": 56.0,
        "gas_ct": 50.0,
        "gas_st": 64.0,  # "n/a" in the first column -> the first published value
        "oil": 64.0,
        "nuclear": 445.0,
    }
    LATE = {
        "coal": 94.0,
        "gas_cc": 113.0,
        "gas_ct": 52.0,
        "gas_st": 64.0,
        "oil": 64.0,
        "nuclear": 537.0,
    }

    @pytest.mark.parametrize("year", [2021, 2022, 2023, 2024, 2025])
    def test_delivery_years_through_2025_26_read_the_first_column(self, year):
        for fuel, per_mw_day in self.EARLY.items():
            got = published_bar_per_kw_yr("PJM", fuel, year)
            assert got is not None, fuel
            assert got[0] == pytest.approx(per_mw_day * 365.0 / 1000.0, abs=1e-9)

    @pytest.mark.parametrize("year", [2026, 2027, 2035, 2050])
    def test_delivery_years_from_2026_27_read_the_second_column(self, year):
        for fuel, per_mw_day in self.LATE.items():
            got = published_bar_per_kw_yr("PJM", fuel, year)
            assert got is not None, fuel
            assert got[0] == pytest.approx(per_mw_day * 365.0 / 1000.0, abs=1e-9)

    def test_the_na_limb_is_named_not_silent(self):
        """Steam Oil & Gas is "n/a" through 2025/26 — the basis must say so."""
        for fuel in ("gas_st", "oil"):
            assert published_bar_per_kw_yr("PJM", fuel, 2023)[1] == "first_published"
            assert published_bar_per_kw_yr("PJM", fuel, 2026)[1] == "vintage"
        assert published_bar_per_kw_yr("PJM", "coal", 2023)[1] == "vintage"

    def test_the_published_bars_are_the_d61_operand(self):
        """The armed bars ARE D61 §2d's ``PUBBAR`` — the row the arm is graded on."""
        cfg = _fc(**{FIELD: {"PJM": True}})
        want = {  # $/kW-yr nameplate, D61 reclear-2026-09-05.py PUBBAR
            "coal": 80 * 365 / 1000,
            "gas_cc": 56 * 365 / 1000,
            "gas_ct": 50 * 365 / 1000,
            "gas_st": 64 * 365 / 1000,
            "oil": 64 * 365 / 1000,
            "nuclear": 445 * 365 / 1000,
        }
        for fuel, value in want.items():
            got, _ = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2022)
            assert got == pytest.approx(value, abs=1e-9), fuel

    def test_the_atb_bars_are_the_d61_control_operand(self):
        """And the OFF bars ARE D61's ``BAR`` — so S0 is the committed control."""
        cfg = _fc()
        want = {
            "coal": 58.5,
            "gas_cc": 30.0,
            "gas_ct": 21.0,
            "gas_st": 35.0,
            "oil": 25.0,
            "nuclear": 130.0,
        }
        for fuel, value in want.items():
            got, _ = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2022)
            assert got == pytest.approx(value, abs=1e-9), fuel

    def test_the_multiplier_does_not_apply_to_the_published_bar(self):
        """M18 §5.4.4: the published number is already the avoidable cost."""
        cfg = _fc(**{FIELD: {"PJM": True}})
        hot = dataclasses.replace(cfg, retirement_fom_multiplier_coal=99.0)
        assert (
            resolve_going_forward_bar_per_kw_yr(hot, "coal", 2022)[0]
            == resolve_going_forward_bar_per_kw_yr(cfg, "coal", 2022)[0]
        )
        # ...but it still governs the OFF path, untouched.
        off = _fc()
        off_hot = dataclasses.replace(off, retirement_fom_multiplier_coal=2.0)
        assert resolve_going_forward_bar_per_kw_yr(off_hot, "coal", 2022)[
            0
        ] == pytest.approx(float(off.fixed_om_coal) * 2.0)


@requires_raw(PUBLISHED_ACR_RAW_CSV)
@pytest.mark.usefixtures("published_acr_clean_dir")
class TestReactiveLeg:
    def test_reactive_is_the_published_row(self):
        assert reactive_offset_per_mw_yr("PJM") == pytest.approx(2199.0)

    def test_no_reactive_row_for_an_iso_without_a_table(self):
        assert reactive_offset_per_mw_yr("MISO") is None

    def test_offer_equals_exit_identity_on_a_toy_stack(self):
        """The bar the screen tests IS the bar the D57 offer is capped at.

        ``offer_g = max(0, GFC_g - EAS_g) / (A_g x 365)`` and the screen fails a
        unit iff ``EAS_g < GFC_g`` — so ``offer > 0`` iff the unit fails, for
        the SAME bar. Asserted here on a toy stack under BOTH postures, which
        is what makes the two one object (rule 19 [R-ONE-MECH]).
        """
        for gate in (None, {"PJM": True}):
            cfg = _fc(**{FIELD: gate})
            for fuel in ("coal", "gas_ct", "gas_st", "oil", "gas_cc"):
                bar, _ = resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2022)
                pmax, a_frac = 500.0, 0.92
                a_mw = pmax * a_frac
                gfc = bar * pmax * 1000.0
                for eas in (0.0, 0.5 * gfc, gfc - 1.0, gfc, 2.0 * gfc):
                    offer = max(0.0, gfc - eas) / (a_mw * 365.0)
                    fails = eas < gfc
                    assert (offer > 0.0) is fails, (gate, fuel, eas)

    def test_reactive_credit_is_once_and_only_when_armed(self):
        """``pmax x rate``, added once — and exactly zero on the off path."""
        rate = reactive_offset_per_mw_yr("PJM")
        pmax = 500.0
        armed = _fc(**{FIELD: {"PJM": True}})
        off = _fc()
        assert resolve_capacity_going_forward_bar_published(off, "PJM") is False
        assert resolve_capacity_going_forward_bar_published(armed, "PJM") is True
        # The screen's expression, reproduced: one multiplication, no stacking.
        assert pmax * rate == pytest.approx(2199.0 * 500.0)
        # And the credit's magnitude is ~$2.2/kW-yr, i.e. small beside every
        # bar it offsets — the D61 §2d S1 row, so a reader can see it cannot
        # be the price-landing device (rules 1/13).
        for fuel in ("coal", "gas_ct", "gas_st", "oil"):
            bar, _ = resolve_going_forward_bar_per_kw_yr(armed, fuel, 2022)
            assert (rate / 1000.0) < 0.15 * bar, fuel
