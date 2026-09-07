"""SPP zonal-load-share curation (lane SPP-32).

Every test here is built from a **synthetic** raw fixture written into a
temporary directory and a redirected ``CLEAN_DIR``. Nothing reads
``data/raw``, so the suite runs identically under CI's sparse checkout
(plan §7 gate G17) and no test can be silently disabled by an unhydrated
data profile.

What is pinned:

* the 17 EIA-930 SPP sub-BA tokens and their North/South partition — the
  SPP-20 P1 zone grouping, including the one member (``EDE``) whose side is
  not decidable from SPP's reserve-zone registry;
* the share contract — ``(n_zones, HOURS_PER_YEAR)``, every hour summing to
  1.0, which is this lane's headline gate;
* the round trip through the ``write_clean`` / ``read_clean`` seam;
* the two failure modes that must degrade to ``None`` rather than to a
  partly-NaN share matrix: a missing raw file and a year the export does not
  cover.
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
_ZONES = ["SPP-North", "SPP-South", "SPP-SPS"]

# One representative token per zone is enough to exercise the partition; the
# full 17 are pinned separately by the crosswalk tests below. SPS is its own
# token and its own zone since lane SPP-54 (2026-09-07).
_NORTH_TOKENS = ("WR", "NPPD", "EDE")
_SOUTH_TOKENS = ("OKGE", "CSWS")
_SPS_TOKENS = ("SPS",)


def _fake_frame(year: int) -> pd.DataFrame:
    """Return a stand-in EIA-930 hourly frame: 8760 rows on a fixed UTC clock.

    Row ``k`` is model local hour-of-year ``k``, which is the only property
    :func:`curate_zonal_shares._spp_utc_to_local_hoy` uses. A fixed -6 h offset
    stands in for SPP local time; the helper derives the mapping from this
    column rather than assuming an offset, so the exact value is arbitrary.
    """
    start = pd.Timestamp(f"{year}-01-01 06:00:00")
    return pd.DataFrame(
        {"UTC time": pd.date_range(start, periods=HOURS_PER_YEAR, freq="1h")}
    )


def _write_subba_fixture(
    directory, year: int, north_mw: float, south_mw: float, sps_mw: float = 0.0
):
    """Write a synthetic SPP sub-BA demand CSV covering the whole year.

    Splits ``north_mw`` / ``south_mw`` / ``sps_mw`` evenly across the tokens of
    each zone so the expected share is exactly each total over the grand total.
    """
    utc = _fake_frame(year)["UTC time"]
    rows = []
    for tokens, total in (
        (_NORTH_TOKENS, north_mw),
        (_SOUTH_TOKENS, south_mw),
        (_SPS_TOKENS, sps_mw),
    ):
        per = total / len(tokens)
        for tok in tokens:
            rows.append(
                pd.DataFrame(
                    {
                        "period": utc.dt.strftime("%Y-%m-%dT%H"),
                        "subba": tok,
                        "value": per,
                    }
                )
            )
    spp_dir = directory / "SPP"
    spp_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(rows, ignore_index=True).to_csv(
        spp_dir / "spp_subba_demand_2023-2025.csv", index=False
    )
    return spp_dir


@pytest.fixture
def spp_raw(tmp_path, monkeypatch):
    """Redirect the curation module's raw dir and clock onto a synthetic fixture."""
    monkeypatch.setattr(czs, "ZONE_DEMAND_DIR", tmp_path)
    monkeypatch.setattr(
        czs, "_eia_hourly_frame_filled", lambda ba, year: _fake_frame(year)
    )
    return tmp_path


# ---------------------------------------------------------------------------
# The crosswalk: the SPP-20 P1 grouping, written on the sub-BA tokens
# ---------------------------------------------------------------------------


def test_crosswalk_covers_the_seventeen_eia930_subbas():
    """All 17 SWPP sub-BA tokens are mapped, and only those 17."""
    assert len(czs._SPP_SUBBA_ZONE_GROUPS) == 17
    assert set(czs._SPP_SUBBA_ZONE_GROUPS) == {
        "CSWS",
        "EDE",
        "GRDA",
        "INDN",
        "KACY",
        "KCPL",
        "LES",
        "MPS",
        "NPPD",
        "OKGE",
        "OPPD",
        "SECI",
        "SPRM",
        "SPS",
        "WAUE",
        "WFEC",
        "WR",
    }


def test_crosswalk_is_the_spp20_p1_partition_with_the_sps_pocket():
    """North gets 12 sub-BAs (owner ruling r#5), the residual South 4, SPS its own.

    SPS is its own EIA-930 token (FINDING-spp-32 §2), so the SPP-54 pocket
    needs no sub-allocation — every token still maps whole and the grouping
    is a partition. CSWS stays whole in the residual South.
    """
    north = {k for k, v in czs._SPP_SUBBA_ZONE_GROUPS.items() if v == "SPP-North"}
    south = {k for k, v in czs._SPP_SUBBA_ZONE_GROUPS.items() if v == "SPP-South"}
    sps = {k for k, v in czs._SPP_SUBBA_ZONE_GROUPS.items() if v == "SPP-SPS"}
    assert north == {
        "EDE",
        "INDN",
        "KACY",
        "KCPL",
        "LES",
        "MPS",
        "NPPD",
        "OPPD",
        "SECI",
        "SPRM",
        "WAUE",
        "WR",
    }
    assert south == {"CSWS", "GRDA", "OKGE", "WFEC"}
    assert sps == {"SPS"}


def test_ede_lands_north():
    """EDE is North.

    Pinned on its own because it is the one member SPP's reserve-zone registry
    cannot decide: EDE's settlement locations sit wholly in RESZONE 4, and
    RESZONE 4 straddles the seam (it also holds OKGE, CSWS, GRDA, SPS and WFEC,
    all South). A future edit that "fixes" EDE by following the reserve zone
    would silently move ~600 MW of Missouri load across the seam.
    """
    assert czs._SPP_SUBBA_ZONE_GROUPS["EDE"] == "SPP-North"


def test_crosswalk_targets_are_the_model_zones():
    """Every crosswalk target is a real SPP model zone."""
    assert set(czs._SPP_SUBBA_ZONE_GROUPS.values()) == set(
        get_iso_config("SPP").zone_names
    )


# ---------------------------------------------------------------------------
# The share contract
# ---------------------------------------------------------------------------


def test_parse_shape(spp_raw):
    """The parser returns (n_zones, HOURS_PER_YEAR) float64."""
    _write_subba_fixture(spp_raw, _YEAR, north_mw=5000.0, south_mw=5000.0)
    shares = czs.parse_spp_shares(_YEAR, _ZONES)
    assert shares is not None
    assert shares.shape == (3, HOURS_PER_YEAR)
    assert shares.dtype == np.float64


def test_shares_sum_to_one_every_hour(spp_raw):
    """THE GATE: shares sum to 1.0 in every one of the 8760 hours."""
    _write_subba_fixture(
        spp_raw, _YEAR, north_mw=5125.0, south_mw=3616.0, sps_mw=1259.0
    )
    shares = czs.parse_spp_shares(_YEAR, _ZONES)
    assert np.abs(shares.sum(axis=0) - 1.0).max() < 1e-9


def test_shares_reproduce_the_injected_split(spp_raw):
    """A known North/South/SPS MW split comes back as exactly that share."""
    _write_subba_fixture(
        spp_raw, _YEAR, north_mw=5000.0, south_mw=3500.0, sps_mw=1500.0
    )
    shares = czs.parse_spp_shares(_YEAR, _ZONES)
    assert np.allclose(shares[0], 0.50, atol=1e-12)
    assert np.allclose(shares[1], 0.35, atol=1e-12)
    assert np.allclose(shares[2], 0.15, atol=1e-12)


def test_shares_are_bounded(spp_raw):
    """No share falls outside [0, 1] and none is NaN."""
    _write_subba_fixture(spp_raw, _YEAR, north_mw=9000.0, south_mw=1000.0)
    shares = czs.parse_spp_shares(_YEAR, _ZONES)
    assert np.isfinite(shares).all()
    assert shares.min() >= 0.0 and shares.max() <= 1.0


# ---------------------------------------------------------------------------
# Degradation: absence must read as absence, never as a partial share matrix
# ---------------------------------------------------------------------------


def test_missing_raw_file_returns_none(spp_raw):
    """No raw file -> None, so the caller falls back to the static load_share."""
    assert czs.parse_spp_shares(_YEAR, _ZONES) is None


def test_uncovered_year_returns_none(spp_raw):
    """A year the export does not cover -> None, not a mostly-NaN matrix.

    The UTC->local mapping still lands a handful of rows for an adjacent year
    (Jan 1st's first UTC hours belong to the previous local year), so the
    ``df.empty`` guard alone does not catch this — the NaN sweep does.
    """
    _write_subba_fixture(spp_raw, _YEAR, north_mw=5000.0, south_mw=5000.0)
    assert czs.parse_spp_shares(2024, _ZONES) is None


def test_missing_clock_returns_none(spp_raw, monkeypatch):
    """No EIA-930 SWPP frame for the year -> None."""
    _write_subba_fixture(spp_raw, _YEAR, north_mw=5000.0, south_mw=5000.0)
    monkeypatch.setattr(czs, "_eia_hourly_frame_filled", lambda ba, year: None)
    assert czs.parse_spp_shares(_YEAR, _ZONES) is None


def test_unknown_subba_tokens_are_ignored(spp_raw):
    """A token outside the crosswalk (e.g. SPP's WEIS-side WACM) is dropped.

    EIA-930 does not report SPP's western RESZONE-21 members as SWPP sub-BAs,
    but a future export that added one must not silently enter the shares.
    """
    spp_dir = _write_subba_fixture(spp_raw, _YEAR, north_mw=5000.0, south_mw=5000.0)
    path = spp_dir / "spp_subba_demand_2023-2025.csv"
    df = pd.read_csv(path)
    intruder = df[df["subba"] == "WR"].copy()
    intruder["subba"] = "WACM"
    intruder["value"] = 99999.0
    pd.concat([df, intruder], ignore_index=True).to_csv(path, index=False)
    shares = czs.parse_spp_shares(_YEAR, _ZONES)
    assert np.allclose(shares[0], 0.5, atol=1e-12)


# ---------------------------------------------------------------------------
# The clean seam
# ---------------------------------------------------------------------------


def test_round_trip_through_clean_parquet(spp_raw, tmp_clean_dir):
    """Parse -> write_clean -> read_clean returns a bit-identical matrix."""
    _write_subba_fixture(
        spp_raw, _YEAR, north_mw=5125.0, south_mw=3616.0, sps_mw=1259.0
    )
    shares = czs.parse_spp_shares(_YEAR, _ZONES)

    df = czs._shares_to_long(shares, _ZONES)
    df["hour"] = df["hour"].astype("int64")
    df["zone"] = df["zone"].astype("string")
    df["share"] = df["share"].astype("float64")
    write_clean(df, "zonal-shares", iso="SPP", year=_YEAR)

    back = read_clean("zonal-shares", iso="SPP", year=_YEAR)
    assert len(back) == HOURS_PER_YEAR * len(_ZONES)
    matrix = (
        back.pivot(index="hour", columns="zone", values="share")[_ZONES]
        .to_numpy(dtype=float)
        .T
    )
    assert np.array_equal(matrix, shares)
    assert np.abs(matrix.sum(axis=0) - 1.0).max() < 1e-9


def test_spp_is_registered_in_the_dispatch_table():
    """SPP resolves through the same registry every other ISO uses."""
    assert czs._PARSE_FUNCS["SPP"] is czs.parse_spp_shares
