"""SOCO zonal-load-share curation (lane SOCO-32).

Every test here is built from a **synthetic** raw fixture written into a
temporary directory and a redirected ``CLEAN_DIR``. Nothing reads
``data/raw``, so the suite runs identically under CI's sparse checkout
(plan §7 gate G17) and no test can be silently disabled by an unhydrated
data profile.

What is pinned:

* **the five-respondent set, and the exclusion of Southern Power (186)** — the
  owner's re-ruling at desk r#5, which chose a *larger* residual with a cited
  basis over a smaller one resting on an uncited component. That is the one
  thing in this lane a well-meaning later edit is most likely to "improve", so
  it gets its own test with the reasoning in the docstring;
* the respondent → zone map, including the two Georgia wholesale respondents
  that join Georgia Power in ``SOCO_GA`` (the map is deliberately NOT 1:1);
* the share contract — ``(n_zones, HOURS_PER_YEAR)``, every hour summing to
  1.0, which is this lane's headline gate;
* the redistribution identity: shares × a system series sums back to that
  series to 1e-9;
* the round trip through the ``write_clean`` / ``read_clean`` seam;
* the bounded tail fill — exactly the clock-offset shortfall is repaired and
  announced, anything larger degrades to ``None`` rather than to a partly-NaN
  share matrix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from scripts.data import curate_zonal_shares as czs
from scripts.lib.clean_io import read_clean, write_clean

_YEAR = 2023
_ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]

# The five respondents the owner ruled in, by FERC-714 respondent id.
_ALABAMA_POWER = 2
_OGLETHORPE = 107
_GEORGIA_POWER = 183
_MISSISSIPPI_POWER = 184
_MEAG = 210
# The one the owner ruled OUT.
_SOUTHERN_POWER = 186


def _fake_frame(year: int) -> pd.DataFrame:
    """Return a stand-in EIA-930 hourly frame: 8760 rows on a fixed UTC clock.

    Row ``k`` is model local hour-of-year ``k``, which is the only property
    :func:`curate_zonal_shares._soco_utc_to_local_hoy` uses. A fixed -6 h
    offset stands in for SOCO's Central clock; the helper derives the mapping
    from this column rather than assuming an offset, so the exact value is
    arbitrary.
    """
    start = pd.Timestamp(f"{year}-01-01 06:00:00")
    return pd.DataFrame(
        {"UTC time": pd.date_range(start, periods=HOURS_PER_YEAR, freq="1h")}
    )


def _write_ferc714_fixture(
    directory,
    year: int,
    per_respondent: dict[int, float],
    hours: int = HOURS_PER_YEAR,
):
    """Write a synthetic FERC-714 planning-area parquet.

    Args:
        directory: Stand-in ``ZONE_DEMAND_DIR``.
        year: Calendar year the fixture's clock covers.
        per_respondent: ``{respondent_id: constant MW}``.
        hours: How many of the year's hours to write (short values exercise
            the tail-fill guard).

    Returns:
        The ``SOCO`` subdirectory the fixture was written into.
    """
    utc = _fake_frame(year)["UTC time"].iloc[:hours]
    rows = [
        pd.DataFrame(
            {
                "datetime_utc": utc,
                "respondent_id_ferc714": rid,
                "demand_reported_mwh": mw,
            }
        )
        for rid, mw in per_respondent.items()
    ]
    soco_dir = directory / "SOCO"
    soco_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(rows, ignore_index=True).to_parquet(
        soco_dir / czs._SOCO_FERC714_FILE, index=False
    )
    return soco_dir


@pytest.fixture
def soco_raw(tmp_path, monkeypatch):
    """Redirect the curation module's raw dir and clock onto a synthetic fixture."""
    monkeypatch.setattr(czs, "ZONE_DEMAND_DIR", tmp_path)
    monkeypatch.setattr(
        czs, "_eia_hourly_frame_filled", lambda ba, year: _fake_frame(year)
    )
    return tmp_path


def _even(mw: float) -> dict[int, float]:
    """Return a constant-MW book over the five ruled respondents."""
    return {
        _ALABAMA_POWER: mw,
        _OGLETHORPE: mw,
        _GEORGIA_POWER: mw,
        _MISSISSIPPI_POWER: mw,
        _MEAG: mw,
    }


# ---------------------------------------------------------------------------
# The respondent set — card S3 as re-ruled at desk r#5
# ---------------------------------------------------------------------------


def test_the_five_cited_respondents_and_only_those():
    """Exactly the five fully-cited FERC-714 respondents are mapped."""
    assert set(czs._SOCO_RESPONDENT_ZONE_GROUPS) == {
        _ALABAMA_POWER,
        _OGLETHORPE,
        _GEORGIA_POWER,
        _MISSISSIPPI_POWER,
        _MEAG,
    }


def test_southern_power_186_is_excluded():
    """Respondent 186 is OUT, and re-adding it is not an improvement.

    Pinned on its own with the reasoning, because the arithmetic invites the
    opposite edit: the SIX-respondent sum has the SMALLER residual
    (1.63 / 1.50 / -0.03 % against the five-set's 3.03 / 2.92 / 1.18 %) and the
    owner chose the five-set anyway at desk r#5. SOCO-14 could cite 107 and 210
    into the BA from primary sources and returned a **documented NO** on 186 —
    nothing establishes where its planning-area LOAD sits, and its near-flat
    0.795-load-factor series is inconsistent with a territorial load. A cited
    basis beats a smaller residual (rules 1 ``[R-STRUCT]`` / 13
    ``[R-MEASURED]``), and the six-set's NEGATIVE 2025 residual is precisely
    the overshoot SOCO-11's PowerSouth + Tallahassee falsifier was built to
    detect. Putting 186 back needs the load-side citation SOCO-14 could not
    find, and the card returns to the owner (plan §7 gate G22).
    """
    assert _SOUTHERN_POWER not in czs._SOCO_RESPONDENT_ZONE_GROUPS


def test_southern_power_rows_do_not_enter_the_shares(soco_raw):
    """A 186 row in the raw file is dropped, not silently absorbed."""
    book = _even(1000.0)
    book[_SOUTHERN_POWER] = 9_999.0
    _write_ferc714_fixture(soco_raw, _YEAR, book)
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    # Three GA respondents of five equal ones => GA is exactly 3/5.
    assert np.allclose(shares[_ZONES.index("SOCO_GA")], 0.6, atol=1e-12)


def test_the_map_is_geographic_not_one_to_one():
    """Two Georgia wholesale respondents join Georgia Power in SOCO_GA.

    Card S3 (ii): zones are named for their GEOGRAPHY, never for an operating
    company, so the five respondents do not map 1:1 onto three zones. This is
    SOCO-32's declared construction.
    """
    groups = czs._SOCO_RESPONDENT_ZONE_GROUPS
    assert groups[_ALABAMA_POWER] == "SOCO_AL"
    assert groups[_MISSISSIPPI_POWER] == "SOCO_MS"
    assert groups[_GEORGIA_POWER] == groups[_OGLETHORPE] == groups[_MEAG] == "SOCO_GA"


def test_crosswalk_targets_are_the_model_zones():
    """Every crosswalk target is a real SOCO model zone."""
    assert set(czs._SOCO_RESPONDENT_ZONE_GROUPS.values()) <= set(
        get_iso_config("SOCO").zone_names
    )


def test_filed_value_is_the_series_consumed():
    """The parser reads FERC's filed column, not PUDL's imputed one."""
    assert czs._SOCO_DEMAND_COLUMN == "demand_reported_mwh"


# ---------------------------------------------------------------------------
# The share contract
# ---------------------------------------------------------------------------


def test_parse_shape(soco_raw):
    """The parser returns (n_zones, HOURS_PER_YEAR) float64."""
    _write_ferc714_fixture(soco_raw, _YEAR, _even(1000.0))
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert shares is not None
    assert shares.shape == (3, HOURS_PER_YEAR)
    assert shares.dtype == np.float64


def test_shares_sum_to_one_every_hour(soco_raw):
    """THE GATE: shares sum to 1.0 in every one of the 8760 hours."""
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        {
            _ALABAMA_POWER: 6600.0,
            _OGLETHORPE: 4500.0,
            _GEORGIA_POWER: 9000.0,
            _MISSISSIPPI_POWER: 1300.0,
            _MEAG: 1350.0,
        },
    )
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert np.abs(shares.sum(axis=0) - 1.0).max() < 1e-9


def test_shares_reproduce_the_injected_split(soco_raw):
    """A known per-respondent MW book comes back as exactly its zone split."""
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        {
            _ALABAMA_POWER: 3000.0,
            _OGLETHORPE: 2000.0,
            _GEORGIA_POWER: 4000.0,
            _MISSISSIPPI_POWER: 1000.0,
            _MEAG: 0.0,
        },
    )
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert np.allclose(shares[0], 0.3, atol=1e-12)  # AL  3000 / 10000
    assert np.allclose(shares[1], 0.6, atol=1e-12)  # GA  (2000+4000) / 10000
    assert np.allclose(shares[2], 0.1, atol=1e-12)  # MS  1000 / 10000


def test_shares_are_bounded(soco_raw):
    """No share falls outside [0, 1] and none is NaN."""
    _write_ferc714_fixture(soco_raw, _YEAR, _even(1000.0))
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert np.isfinite(shares).all()
    assert shares.min() >= 0.0 and shares.max() <= 1.0


def test_redistribution_identity(soco_raw):
    """Shares x a system series sum back to that series to 1e-9.

    The load path multiplies these fractions into the measured EIA-930 system
    demand (``eia930.demand.load_demand``: ``demand = weights * raw_mw``), so
    what this asserts is that the zonal allocation neither creates nor destroys
    energy in any hour.
    """
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        {
            _ALABAMA_POWER: 6600.0,
            _OGLETHORPE: 4500.0,
            _GEORGIA_POWER: 9000.0,
            _MISSISSIPPI_POWER: 1300.0,
            _MEAG: 1350.0,
        },
    )
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    rng = np.random.default_rng(0)
    system = 20_000.0 + 15_000.0 * rng.random(HOURS_PER_YEAR)
    zonal = shares * system[None, :]
    assert np.abs(zonal.sum(axis=0) - system).max() < 1e-9


# ---------------------------------------------------------------------------
# Degradation: absence must read as absence, never as a partial share matrix
# ---------------------------------------------------------------------------


def test_missing_raw_file_returns_none(soco_raw):
    """No raw file -> None, so the caller falls back to the static load_share."""
    assert czs.parse_soco_shares(_YEAR, _ZONES) is None


def test_missing_clock_returns_none(soco_raw, monkeypatch):
    """No EIA-930 SOCO frame for the year -> None."""
    _write_ferc714_fixture(soco_raw, _YEAR, _even(1000.0))
    monkeypatch.setattr(czs, "_eia_hourly_frame_filled", lambda ba, year: None)
    assert czs.parse_soco_shares(_YEAR, _ZONES) is None


def test_uncovered_year_returns_none(soco_raw):
    """A year the file does not cover -> None, not a mostly-NaN matrix."""
    _write_ferc714_fixture(soco_raw, _YEAR, _even(1000.0))
    assert czs.parse_soco_shares(2024, _ZONES) is None


def test_clock_offset_tail_is_filled_not_rejected(soco_raw):
    """Exactly the clock-offset shortfall is repaired, and the year survives.

    The committed 714 pull and the EIA-930 extract were both bounded on UTC, so
    the last 7 Central hour-ending labels of the final year have no filing on
    EITHER side (soco-data-audit §3.2). Rejecting the year for that would
    dispatch all 8760 hours on the flat static fallback — the miso-251 defect —
    to avoid inheriting a share for 0.08 % of them.
    """
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        _even(1000.0),
        hours=HOURS_PER_YEAR - czs._SOCO_MAX_UNCOVERED_HOURS,
    )
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert shares is not None
    assert np.abs(shares.sum(axis=0) - 1.0).max() < 1e-9
    # The filled tail carries the last measured hour's split, not a zero column.
    last_measured = HOURS_PER_YEAR - czs._SOCO_MAX_UNCOVERED_HOURS - 1
    assert np.allclose(shares[:, -1], shares[:, last_measured], atol=1e-12)


def test_gap_larger_than_the_clock_offset_returns_none(soco_raw):
    """One hour past the structural shortfall and the year is refused."""
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        _even(1000.0),
        hours=HOURS_PER_YEAR - czs._SOCO_MAX_UNCOVERED_HOURS - 1,
    )
    assert czs.parse_soco_shares(_YEAR, _ZONES) is None


def test_single_respondent_gap_does_not_dent_its_zone(soco_raw):
    """One respondent missing for one hour is filled, not treated as zero load.

    2024 carries exactly this case — Oglethorpe is absent at one hour — and
    without the per-respondent fill that hour would drop ~5 GW out of Georgia's
    total and put a one-hour notch in the zone's share.
    """
    soco_dir = _write_ferc714_fixture(soco_raw, _YEAR, _even(1000.0))
    path = soco_dir / czs._SOCO_FERC714_FILE
    frame = pd.read_parquet(path)
    hole = (frame["respondent_id_ferc714"] == _OGLETHORPE) & (
        frame["datetime_utc"] == frame["datetime_utc"].iloc[100]
    )
    frame[~hole].to_parquet(path, index=False)
    shares = czs.parse_soco_shares(_YEAR, _ZONES)
    assert np.allclose(shares[:, 100], shares[:, 99], atol=1e-12)


# ---------------------------------------------------------------------------
# The clean seam
# ---------------------------------------------------------------------------


def test_round_trip_through_clean_parquet(soco_raw, tmp_clean_dir):
    """Parse -> write_clean -> read_clean returns a bit-identical matrix."""
    _write_ferc714_fixture(
        soco_raw,
        _YEAR,
        {
            _ALABAMA_POWER: 6600.0,
            _OGLETHORPE: 4500.0,
            _GEORGIA_POWER: 9000.0,
            _MISSISSIPPI_POWER: 1300.0,
            _MEAG: 1350.0,
        },
    )
    shares = czs.parse_soco_shares(_YEAR, _ZONES)

    df = czs._shares_to_long(shares, _ZONES)
    df["hour"] = df["hour"].astype("int64")
    df["zone"] = df["zone"].astype("string")
    df["share"] = df["share"].astype("float64")
    write_clean(df, "zonal-shares", iso="SOCO", year=_YEAR)

    back = read_clean("zonal-shares", iso="SOCO", year=_YEAR)
    assert len(back) == HOURS_PER_YEAR * len(_ZONES)
    matrix = (
        back.pivot(index="hour", columns="zone", values="share")[_ZONES]
        .to_numpy(dtype=float)
        .T
    )
    assert np.array_equal(matrix, shares)
    assert np.abs(matrix.sum(axis=0) - 1.0).max() < 1e-9


def test_soco_is_registered_in_the_dispatch_table():
    """SOCO resolves through the same registry every other ISO uses.

    This is also what serves the raw fallback:
    ``eia930.zonal_shares._zonal_shares_from_raw`` imports ``_PARSE_FUNCS``
    from here, so registering the parser once serves both the clean-parquet
    path and the fresh-clone path with no second crosswalk.
    """
    assert czs._PARSE_FUNCS["SOCO"] is czs.parse_soco_shares
