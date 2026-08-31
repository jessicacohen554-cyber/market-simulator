"""Tests for the gas-ofo-events intake on a tiny synthetic ENVOY fixture.

Writes a minimal year-column OFO ledger into a tmp raw tree, runs ``curate``,
and asserts the written Parquet is schema-valid and the tidy reconciliation is
correct: the column position supplies the year, the stage segment is optional
(the pre-2018 high-OFO vintage), the published tolerance sign is preserved, and
``(WAIVED)`` lands as a real bool. ``CLEAN_DIR`` is redirected to a tmp dir by
:class:`tests.helpers.base.RawFixtureTestCase` so nothing touches the real tree.

Trivial case first (one cell, one year), then the full-vocabulary fixture.
"""

from __future__ import annotations

import pandas as pd
import pytest

from scripts.data import curate_gas_ofo_events as curate_ofo
from scripts.lib import gas_ofo_events as ofo
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import RawFixtureTestCase


def _ledger(years: list[str], rows: list[list[str]]) -> str:
    """Render an ENVOY-shaped year-column ledger page from cell text.

    ``rows`` is a list of table rows, each a list of cell strings positionally
    aligned to ``years`` (empty string = the blank padding cell ENVOY emits for
    a year with fewer events).
    """
    head = "".join(f'<th class="header_row" nowrap>{y}</th>' for y in years)
    body = ""
    for row in rows:
        cells = "".join(
            f'<td class="{"red_data" if "WAIVED" in c else "ledger_data"}" '
            f"nowrap>&nbsp;{c}&nbsp;</td>"
            if c
            else '<td class="ledger_data" nowrap>&nbsp;</td>'
            for c in row
        )
        body += f'<tr class="even_row">{cells}</tr>'
    return (
        '<html><body><table class="ledger_table">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody>"
        "</table></body></html>"
    )


# Low ledger: two years, exercising a plain stage, a decimal sub-stage, a
# WAIVED cell, and the blank padding cell for the shorter year.
_LOW = _ledger(
    ["2025", "2024"],
    [
        ["January 6, Stage 2, -13%", "January 4, Stage 1, -11%"],
        ["February 9, Stage 3.1, -5% (WAIVED)", ""],
    ],
)
# High ledger: the staged modern vintage beside the pre-2018 unstaged vintage.
_HIGH = _ledger(
    ["2025", "2017"],
    [["March 2, Stage 3.1, 10%", "February 5, 5%"]],
)


class TestCurateGasOfoEvents(RawFixtureTestCase):
    def _write_fixture(self, low: str = _LOW, high: str | None = _HIGH) -> None:
        d = ofo.raw_dir_for("CAISO", self.raw_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "socalgas_low_ofo_events.html").write_text(low)
        if high is not None:
            (d / "socalgas_high_ofo_events.html").write_text(high)

    def _curate(self) -> pd.DataFrame:
        written = curate_ofo.curate(raw_root=self.raw_dir, isos=["CAISO"])
        self.assertEqual(len(written), 1, "expected one CAISO partition")
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "gas-ofo-events")
        return pd.read_parquet(written[0])

    def test_trivial_single_event(self) -> None:
        """One cell, one year — the smallest thing the seam can carry."""
        self._write_fixture(
            low=_ledger(["2024"], [["January 4, Stage 1, -11%"]]), high=None
        )
        df = self._curate()
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["iso"], "CAISO")
        self.assertEqual(row["utility"], "SOCALGAS")
        self.assertEqual(row["side"], "low")
        self.assertEqual(row["stage"], "1")
        self.assertEqual(row["tolerance_pct"], -11.0)
        self.assertIs(bool(row["waived"]), False)
        self.assertEqual(pd.Timestamp(row["gas_day"]), pd.Timestamp("2024-01-04"))

    def test_schema_valid_and_columns(self) -> None:
        self._write_fixture()
        df = self._curate()
        self.assertEqual(list(df.columns), list(ofo.CANONICAL_COLUMNS))
        self.assertEqual(len(df), 5)
        self.assertEqual(set(df["side"]), {"low", "high"})

    def test_year_comes_from_column_position(self) -> None:
        """A cell names only a month/day; its column supplies the year."""
        self._write_fixture()
        low = self._curate().query("side == 'low'")
        self.assertEqual(
            sorted(str(d.date()) for d in low["gas_day"]),
            ["2024-01-04", "2025-01-06", "2025-02-09"],
        )

    def test_waived_parsed_as_bool(self) -> None:
        self._write_fixture()
        df = self._curate()
        self.assertEqual(df["waived"].dtype, bool)
        waived = df[df["waived"]]
        self.assertEqual(len(waived), 1)
        self.assertEqual(
            pd.Timestamp(waived.iloc[0]["gas_day"]), pd.Timestamp("2025-02-09")
        )
        # The tolerance keeps its published value; WAIVED is a separate fact.
        self.assertEqual(waived.iloc[0]["tolerance_pct"], -5.0)

    def test_tolerance_sign_follows_side(self) -> None:
        """Low orders publish a negative band, high orders a positive one."""
        self._write_fixture()
        df = self._curate()
        self.assertTrue((df.loc[df["side"] == "low", "tolerance_pct"] < 0).all())
        self.assertTrue((df.loc[df["side"] == "high", "tolerance_pct"] > 0).all())

    def test_unstaged_high_vintage_is_null_stage(self) -> None:
        """SoCalGas printed high OFOs with no stage before mid-2018."""
        self._write_fixture()
        df = self._curate()
        pre = df[df["gas_day"].dt.year == 2017]
        self.assertEqual(len(pre), 1)
        self.assertTrue(pd.isna(pre.iloc[0]["stage"]))
        self.assertEqual(pre.iloc[0]["side"], "high")
        # ... while the modern vintage keeps its sub-stage.
        self.assertEqual(
            set(df.loc[df["gas_day"].dt.year == 2025, "stage"]) & {"3.1"}, {"3.1"}
        )

    def test_same_gas_day_both_sides_is_not_a_duplicate(self) -> None:
        """A utility may declare a high and a low order on one gas day."""
        self._write_fixture(
            low=_ledger(["2025"], [["November 18, Stage 1, -5%"]]),
            high=_ledger(["2025"], [["November 18, Stage 3.1, 10%"]]),
        )
        df = self._curate()
        self.assertEqual(len(df), 2)
        self.assertEqual(set(df["side"]), {"low", "high"})

    def test_idempotent(self) -> None:
        self._write_fixture()
        first = self._curate()
        second = self._curate()
        pd.testing.assert_frame_equal(first, second)

    def test_unparsable_cell_raises(self) -> None:
        """A ledger format change must fail loudly, never drop events."""
        self._write_fixture(
            low=_ledger(["2025"], [["sometime in January, huge"]]), high=None
        )
        with pytest.raises(ValueError, match="did not match the published grammar"):
            curate_ofo.curate(raw_root=self.raw_dir, isos=["CAISO"])

    def test_missing_snapshot_is_skipped_not_fatal(self) -> None:
        """An ISO whose snapshots have not landed yields no partition."""
        written = curate_ofo.curate(raw_root=self.raw_dir, isos=["CAISO"])
        self.assertEqual(written, [])
