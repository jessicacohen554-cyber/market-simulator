"""ercot-261 Card A: the corroboration sub-gate on the ERCOT gas LEVEL anchor.

``ercot_ep_gas_basis_monthly`` relocates the measured TX electric-power
delivered-gas level to the months it was measured in. That is right wherever the
monthly print is a price, and wrong where it is a monthly cost/volume RATIO --
February 2021 reads $59.73/MMBtu because Texas gas traded near $3 for ~24 days
and $100-1,200 for ~4.

These tests pin the admissibility rule, its fail-closed behaviour, and that it is
byte-inert in every year where the two measured series corroborate each other.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.constants import ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU
from market_sim.data.fuel.basis.ercot import (
    ercot_electric_power_gas_basis,
    ercot_electric_power_gas_basis_monthly,
)

#: Years whose two independent measurements agree in every month, so the filter
#: must be a no-op there (PRECOMMIT-ercot261 SS2c).
CORROBORATED_YEARS = (2019, 2020, 2022, 2023, 2024, 2025)


def test_tolerance_is_the_declared_value():
    """The DOF-ledgered tolerance is 1.00 $/MMBtu and is never swept."""
    assert ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU == 1.00


@pytest.mark.parametrize("year", CORROBORATED_YEARS)
def test_inert_where_both_series_agree(year):
    """In six of seven years the filter holds out nothing — byte-identical."""
    plain = ercot_electric_power_gas_basis_monthly(year)
    filtered = ercot_electric_power_gas_basis_monthly(year, corroborated=True)
    assert plain is not None and filtered is not None
    np.testing.assert_array_equal(plain, filtered)


def test_2021_holds_out_february_and_december():
    """2021 is the only year the filter fires, and it fires on the right months."""
    plain = ercot_electric_power_gas_basis_monthly(2021)
    filtered = ercot_electric_power_gas_basis_monthly(2021, corroborated=True)
    moved = ~np.isclose(plain, filtered)
    assert set(np.flatnonzero(moved) + 1) == {2, 12}


def test_uri_is_not_priced_at_the_monthly_ratio():
    """February 2021's +54.4 $/MMBtu basis must not survive the filter.

    Left in, it puts every one of February's 672 hours above $200/MWh on fuel
    cost alone — the measured cause of the ercot-254 C3c regression.
    """
    filtered = ercot_electric_power_gas_basis_monthly(2021, corroborated=True)
    assert filtered[1] < 1.0, "February 2021 must not keep the Uri cost ratio"


def test_fallback_is_the_corroborated_mean_not_the_annual_form():
    """A held-out month takes the year's corroborated mean.

    Never the annual mean: 2021's +5.278 IS February, so falling back to it
    would re-break the very month the filter is protecting.
    """
    plain = ercot_electric_power_gas_basis_monthly(2021)
    filtered = ercot_electric_power_gas_basis_monthly(2021, corroborated=True)
    admissible = np.isclose(plain, filtered)
    expected = float(plain[admissible].mean())
    assert filtered[1] == pytest.approx(expected)
    assert filtered[11] == pytest.approx(expected)
    annual = ercot_electric_power_gas_basis(2021)
    assert abs(filtered[1] - annual) > 4.0, "must not fall back to the annual form"


def test_fails_closed_on_a_missing_corroborator(tmp_path):
    """No corroborator file ⇒ the un-filtered monthly form, never a partial one."""
    missing = tmp_path / "absent.csv"
    plain = ercot_electric_power_gas_basis_monthly(2021)
    got = ercot_electric_power_gas_basis_monthly(
        2021, corroborated=True, corroborator_path=missing
    )
    np.testing.assert_array_equal(plain, got)


def test_fails_closed_on_an_incomplete_corroborator_year(tmp_path):
    """A corroborator missing any month of the year ⇒ un-filtered monthly form."""
    partial = tmp_path / "partial.csv"
    partial.write_text(
        "year,month,price_usd_mmbtu\n"
        + "".join(f"2021,{m},3.0\n" for m in range(1, 12))  # 11 months only
    )
    plain = ercot_electric_power_gas_basis_monthly(2021)
    got = ercot_electric_power_gas_basis_monthly(
        2021, corroborated=True, corroborator_path=partial
    )
    np.testing.assert_array_equal(plain, got)


def test_all_months_inadmissible_falls_back_rather_than_emptying(tmp_path):
    """If nothing corroborates there is no mean to fall back to — keep the data."""
    absurd = tmp_path / "absurd.csv"
    absurd.write_text(
        "year,month,price_usd_mmbtu\n"
        + "".join(f"2021,{m},999.0\n" for m in range(1, 13))
    )
    plain = ercot_electric_power_gas_basis_monthly(2021)
    got = ercot_electric_power_gas_basis_monthly(
        2021, corroborated=True, corroborator_path=absurd
    )
    np.testing.assert_array_equal(plain, got)


def test_off_by_default_is_the_unfiltered_form():
    """The gate is opt-in; the default argument changes nothing."""
    for year in (2021, *CORROBORATED_YEARS):
        np.testing.assert_array_equal(
            ercot_electric_power_gas_basis_monthly(year),
            ercot_electric_power_gas_basis_monthly(year, corroborated=False),
        )


# --------------------------------------------------------------------------
# ercot-265: the RECEIPTS FALLBACK sub-gate.
#
# The filter above asks whether two independent measurements of the same
# delivered-gas quantity agree. When they do not, the incumbent fallback
# substitutes the year's corroborated mean -- discarding BOTH measurements and
# pricing an extraordinary month at an ordinary level. ``receipts_fallback``
# fills the held-out month from the corroborator itself (EIA-923 Schedule-5
# receipts, what the plants actually paid) instead. Rule 14 [R-ACCURATE].
# --------------------------------------------------------------------------


def test_receipts_fallback_is_off_by_default():
    """Opt-in: the default argument reproduces the incumbent filter exactly."""
    for year in (2021, *CORROBORATED_YEARS):
        np.testing.assert_array_equal(
            ercot_electric_power_gas_basis_monthly(year, corroborated=True),
            ercot_electric_power_gas_basis_monthly(
                year, corroborated=True, receipts_fallback=False
            ),
        )


def test_receipts_fallback_is_inert_where_every_month_corroborates():
    """It can only change a HELD-OUT month, so a clean year is byte-identical."""
    for year in CORROBORATED_YEARS:
        np.testing.assert_array_equal(
            ercot_electric_power_gas_basis_monthly(year, corroborated=True),
            ercot_electric_power_gas_basis_monthly(
                year, corroborated=True, receipts_fallback=True
            ),
        )


def test_receipts_fallback_requires_the_corroboration_gate():
    """A sub-gate, never a mechanism beside it (rule 19 [R-ONE-MECH])."""
    for year in (2021, *CORROBORATED_YEARS):
        np.testing.assert_array_equal(
            ercot_electric_power_gas_basis_monthly(year, corroborated=False),
            ercot_electric_power_gas_basis_monthly(
                year, corroborated=False, receipts_fallback=True
            ),
        )


def test_receipts_fallback_moves_only_the_held_out_months_of_2021():
    """2021 m02/m12 are the only cells that may move, and they move UP."""
    incumbent = ercot_electric_power_gas_basis_monthly(2021, corroborated=True)
    armed = ercot_electric_power_gas_basis_monthly(
        2021, corroborated=True, receipts_fallback=True
    )
    moved = set(np.flatnonzero(np.abs(armed - incumbent) > 1e-9) + 1)
    assert moved == {2, 12}, moved
    # The held-out months carry a measured extraordinary cost, so the receipts
    # value must exceed the year's ordinary central value it replaced.
    assert armed[1] > incumbent[1]
    assert armed[11] > incumbent[11]
    # Every corroborated month is untouched.
    keep = [m for m in range(12) if m not in (1, 11)]
    np.testing.assert_array_equal(armed[keep], incumbent[keep])


def test_receipts_fallback_fills_from_the_corroborator_not_the_year_mean():
    """The substituted value IS the corroborator's own basis, exactly.

    Both forms difference against the SAME monthly hub, so the hub cancels::

        armed - raw == receipts - survey

    That identity is exact and pins the fallback to the receipts series rather
    than to any central value derived from the other months.
    """
    import csv

    from market_sim.config.paths import RAW_DATA_DIR
    from market_sim.data.fuel.basis.ercot import (
        _MCF_TO_MMBTU,
        ERCOT_GAS_CORROBORATOR_PATH,
        _load_ercot_electric_power_gas,
    )

    raw = ercot_electric_power_gas_basis_monthly(2021, corroborated=False)
    armed = ercot_electric_power_gas_basis_monthly(
        2021, corroborated=True, receipts_fallback=True
    )
    receipts = {}
    with open(ERCOT_GAS_CORROBORATOR_PATH, newline="") as fh:
        for row in csv.DictReader(fh):
            if int(row["year"]) == 2021:
                receipts[int(row["month"])] = float(row["price_usd_mmbtu"])
    frame = _load_ercot_electric_power_gas(None)
    survey_mcf = frame[frame["year"] == 2021].set_index("month")["price_usd_mcf"]
    for month in (2, 12):
        survey = float(survey_mcf.loc[month]) / _MCF_TO_MMBTU
        assert armed[month - 1] - raw[month - 1] == pytest.approx(
            receipts[month] - survey, abs=1e-9
        )
    assert RAW_DATA_DIR is not None
