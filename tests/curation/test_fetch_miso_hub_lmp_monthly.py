"""Tests for the pre-2023 MONTHLY pricing-report route in ``fetch_miso_hub_lmp``.

MISO changed report FAMILIES in 2023 rather than deleting its history: the daily
all-node files serve 2023 onward, the monthly ``{YYYYMM}_{da,rt}_pr_xls.zip``
archives serve 2015-2022, and between them the record is unbroken. Three route
audits missed the second family and concluded the pre-2023 years were
unrecoverable, so the route is covered here against the two conventions that
would silently corrupt it:

* the **real-time member is named for its PUBLISH date** and carries the PRIOR
  day's market, so keying on the filename mis-dates every RT row by one day;
* an hour published as **0.0 at all eight hubs at once** is the report's
  missing-data marker, and staging it as a price would put a false $0.00 into
  the validation reference.

Nothing here touches the network: the zip bytes are built in-process and
``_fetch`` is patched.
"""

from __future__ import annotations

import io
import sys
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import fetch_miso_hub_lmp as f  # noqa: E402

_HUB_LABELS = [
    "MISO System",
    "Arkansas Hub",
    "Illinois Hub",
    "Indiana Hub",
    "Louisiana Hub",
    "Michigan Hub",
    "Minnesota Hub",
    "MS.HUB",
    "Texas Hub",
]


def _sheet_bytes(market_date: date, blank_hour: int | None = None) -> bytes:
    """Build one day's ``.xls`` exactly as MISO lays the real report out.

    ``blank_hour`` (hour-ending) writes 0.0 across EVERY hub for that hour --
    the report's missing-data marker.
    """
    import xlwt

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sheet1")
    ws.write(0, 0, "Day-Ahead Pricing Report")
    ws.write(1, 0, f"Market Date:  {market_date:%m/%d/%Y}")
    ws.write(4, 0, "Pricing Results")
    header = 6
    for c, label in enumerate(_HUB_LABELS):
        ws.write(header, c + 1, label)
    for he in range(1, 25):
        ws.write(header + he, 0, f"Hour  {he:02d}")
        for c in range(len(_HUB_LABELS)):
            ws.write(header + he, c + 1, 0.0 if he == blank_hour else 20.0 + he + c)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _zip_bytes(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, body in members.items():
            zf.writestr(name, body)
    return buf.getvalue()


class MonthlyRoute(unittest.TestCase):
    """The monthly route must date rows by MARKET date and blank absent hours."""

    def setUp(self) -> None:
        f._monthly_cache.clear()
        self.addCleanup(f._monthly_cache.clear)

    def test_rows_are_keyed_by_market_date_not_filename(self) -> None:
        """A publish-date filename must not shift the staged date (the RT case)."""
        # Named for 06/15 (publish), carrying 06/14 (market) -- the RT convention.
        body = _zip_bytes({"20220615_rt_pr.xls": _sheet_bytes(date(2022, 6, 14))})
        with mock.patch.object(f, "_fetch", return_value=body):
            rows = f._hub_rows_monthly(date(2022, 6, 14), "rt")
        self.assertIsNotNone(rows, "the market date must resolve")
        self.assertTrue(all(r[0] == "2022-06-14" for r in rows))
        # ...and the publish date itself holds nothing.
        self.assertIsNone(f._hub_rows_monthly(date(2022, 6, 15), "rt"))

    def test_month_end_is_found_in_the_following_months_zip(self) -> None:
        """The last market day of a month ships in the NEXT month's archive."""
        nxt = _zip_bytes({"20210201_rt_pr.xls": _sheet_bytes(date(2021, 1, 31))})
        empty = _zip_bytes({})

        def fake_fetch(url: str) -> bytes:
            return nxt if "202102" in url else empty

        with mock.patch.object(f, "_fetch", side_effect=fake_fetch):
            rows = f._hub_rows_monthly(date(2021, 1, 31), "rt")
        self.assertIsNotNone(rows, "month-end must fall through to the next month")
        self.assertTrue(all(r[0] == "2021-01-31" for r in rows))

    def test_all_hub_zero_hour_is_blank_not_a_zero_price(self) -> None:
        """0.0 at every hub is missing data; it must never stage as $0.00."""
        body = _zip_bytes(
            {"20200615_da_pr.xls": _sheet_bytes(date(2020, 6, 15), blank_hour=17)}
        )
        with mock.patch.object(f, "_fetch", return_value=body):
            rows = f._hub_rows_monthly(date(2020, 6, 15), "da")
        for row in rows:
            self.assertEqual(row[4 + 16], "", "HE17 must be blank")
            self.assertNotEqual(row[4 + 15], "", "neighbouring hours must survive")

    def test_stages_the_eight_named_hubs_and_not_miso_system(self) -> None:
        """MISO System is an average, not one of the eight named hubs (D6)."""
        body = _zip_bytes({"20200615_da_pr.xls": _sheet_bytes(date(2020, 6, 15))})
        with mock.patch.object(f, "_fetch", return_value=body):
            rows = f._hub_rows_monthly(date(2020, 6, 15), "da")
        self.assertEqual({r[1] for r in rows}, set(f.HUBS))
        self.assertTrue(all(r[3] == "LMP" for r in rows), "this family is LMP-only")

    def test_absent_month_returns_none_so_the_api_fallback_still_runs(self) -> None:
        """A 404 month must not be mistaken for a staged one."""
        with mock.patch.object(f, "_fetch", side_effect=f._NotFound()):
            self.assertIsNone(f._hub_rows_monthly(date(2023, 6, 15), "da"))


if __name__ == "__main__":
    unittest.main()
