"""Plant-grain EXIT membership for the LP fleet (R-ERCOT-14).

``constants.ISO_PLANT_EXITS`` registers Oklaunion (127) as leaving ERCOT at
hour-ending UTC 2020-10-01 06:00 (last ERCOT DAM operating day 2020-09-30).
``market_sim.data.ba_membership.plant_exit_first_outside_row`` gives the fleet
hour mask its first outside row; every other region reads an empty registry.
"""

import pytest

from market_sim.config.constants import ISO_PLANT_EXITS
from market_sim.data import ba_membership as bm
from tests.helpers import REPO_ROOT

_HAVE_930 = any((REPO_ROOT / "data" / "raw").glob("eia-930*"))


def test_registry_is_oklaunion_only():
    assert ISO_PLANT_EXITS == {"ERCOT": {127: "2020-10-01 06:00"}}


def test_before_and_after_the_exit_year():
    assert bm.plant_exit_first_outside_row("ERCOT", 2019) == {}
    for y in (2021, 2022, 2025):
        assert bm.plant_exit_first_outside_row("ERCOT", y) == {127: 0}
    for iso in ("SOCO", "PJM", "SPP"):
        assert bm.plant_exit_first_outside_row(iso, 2020) == {}


@pytest.mark.skipif(not _HAVE_930, reason="EIA-930 extract not hydrated")
def test_exit_year_row_is_the_first_hour_of_october():
    row = bm.plant_exit_first_outside_row("ERCOT", 2020)[127]
    # The 8,760-row LP clock drops Feb 29, so Jan-Sep is 273 days; the stamp is
    # HE01 CDT = HE24 CST Sep 30 on the standard-time clock, one row earlier
    # (the Frontera entry row 2447 = 102 x 24 - 1 follows the same convention).
    assert row == 273 * 24 - 1
