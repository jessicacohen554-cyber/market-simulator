"""NWPP zonal-load-share curation (lane NWPP-33).

NWPP is the repo's only POOL region — seventeen balancing authorities, no
sub-BA product for any of them (plan §2.5, gate **G18**), and therefore a zone
that may not split a BA. Its zonal shares are consequently a REGROUP of the
same per-BA arrays the pool's own system demand is summed from, not a second
data source, and that is what makes the identity in
:func:`test_zone_demand_reproduces_the_pool_total_exactly` provable rather than
approximate.

Every test here is built from a **synthetic** member fixture and a redirected
``CLEAN_DIR``. Nothing reads ``data/raw``, so the suite runs identically under
CI's sparse checkout and no test can be silently disabled by an unhydrated data
profile.

What is pinned:

* the seventeen-BA crosswalk and the owner-ruled N5 partition, including the
  two generation-only members whose LOAD is zero but whose zone still matters;
* the share contract — ``(n_zones, HOURS_PER_YEAR)``, every hour summing to
  1.0 — and the exact reconstruction of the pool total from the shares;
* **the demand convention, which is the reason this lane exists** (NWPP-10
  §1.3): the exact-zero dropout screen fires, and the 2.5 x median SPIKE screen
  does NOT. A cold-snap hour at 2.8 x a member's median is REAL LOAD — in the
  committed data, 54 such CHPD hours of 12-16 January 2024 hold CHPD's annual
  peak and the whole NWPP-NW zone's 2024 annual peak — and a regression that
  reintroduced spike screening here would delete a documented regional peak
  (rule 14 ``[R-ACCURATE]``). ``test_a_cold_snap_spike_is_not_screened`` is that
  guard;
* the round trip through the ``write_clean`` / ``read_clean`` seam;
* the failure mode that must degrade to ``None`` rather than to a partial share
  matrix: a pool that cannot assemble all seventeen members.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia930 import frames as eia_frames
from market_sim.data.zone_assignment import _NWPP_BA_ZONES
from scripts.data import curate_zonal_shares as czs
from scripts.lib.clean_io import read_clean, write_clean

_YEAR = 2024
_ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]

# The two generation-only balancing authorities: real generation, null demand in
# all 26,304 hours of 2023-2025 (NWPP-10 §2 item 4).
_GENERATION_ONLY = ("AVRN", "GRID")

# A flat per-BA load, so an injected perturbation is the only thing that can
# move a share and the expected value is arithmetic rather than a fixture read.
_FLAT_MW = 1000.0


def _member_frames(
    year: int, overrides: dict[str, np.ndarray] | None = None
) -> dict[str, pd.DataFrame]:
    """Return a synthetic ``_pool_member_frames`` result for all seventeen BAs.

    Each member carries a flat ``Demand (Adjusted)`` of :data:`_FLAT_MW` except
    the generation-only pair (all-NaN, as the committed data has them) and any
    BA named in ``overrides``, whose array is used verbatim.

    Args:
        year: Calendar year the fixture stands in for.
        overrides: Optional ``{ba: series}`` replacing that member's demand.

    Returns:
        ``{ba: DataFrame}`` on the 8760-row pool clock.
    """
    overrides = overrides or {}
    utc = pd.date_range(f"{year}-01-01 08:00:00", periods=HOURS_PER_YEAR, freq="1h")
    out: dict[str, pd.DataFrame] = {}
    for ba in _NWPP_BA_ZONES:
        if ba in overrides:
            demand = np.asarray(overrides[ba], dtype=float)
        elif ba in _GENERATION_ONLY:
            demand = np.full(HOURS_PER_YEAR, np.nan)
        else:
            demand = np.full(HOURS_PER_YEAR, _FLAT_MW)
        out[ba] = pd.DataFrame({"UTC time": utc, "Demand (Adjusted)": demand})
    return out


@pytest.fixture
def nwpp_pool(monkeypatch):
    """Serve :func:`parse_nwpp_shares` from a synthetic seventeen-member pool.

    Returns a setter so each test can inject its own member overrides; the
    parser imports ``_pool_member_frames`` from the frames module at call time,
    so patching the module attribute is what reaches it.
    """

    def install(overrides: dict[str, np.ndarray] | None = None, present: bool = True):
        def fake(pool: str, year: int):
            assert pool == "NWPP"
            return _member_frames(year, overrides) if present else None

        monkeypatch.setattr(eia_frames, "_pool_member_frames", fake)

    install()
    return install


# ---------------------------------------------------------------------------
# The crosswalk: owner ruling N5, keyed on Balancing Authority Code (gate G18)
# ---------------------------------------------------------------------------


def test_crosswalk_covers_the_seventeen_balancing_authorities():
    """All 17 footprint BAs are mapped, and only those 17."""
    assert len(_NWPP_BA_ZONES) == 17
    assert set(_NWPP_BA_ZONES) == {
        "BPAT",
        "PACE",
        "PACW",
        "PGE",
        "PSEI",
        "AVA",
        "IPCO",
        "NWMT",
        "CHPD",
        "DOPD",
        "GCPD",
        "SCL",
        "TPWR",
        "AVRN",
        "GRID",
        "WAUW",
        "NEVP",
    }


def test_crosswalk_is_the_n5_partition():
    """The five zones hold exactly the members owner ruling N5 grouped."""
    groups: dict[str, set[str]] = {}
    for ba, zone in _NWPP_BA_ZONES.items():
        groups.setdefault(zone, set()).add(ba)
    assert groups == {
        "NWPP-NW": {"BPAT", "PSEI", "SCL", "TPWR", "CHPD", "DOPD", "GCPD", "AVRN"},
        "NWPP-OR": {"PGE", "PACW", "GRID"},
        "NWPP-INLAND": {"IPCO", "AVA", "NWMT", "WAUW"},
        "NWPP-EAST": {"PACE"},
        "NWPP-SNV": {"NEVP"},
    }


def test_crosswalk_targets_are_the_model_zones():
    """Every crosswalk target is a real NWPP model zone."""
    assert set(_NWPP_BA_ZONES.values()) == set(get_iso_config("NWPP").zone_names)


def test_no_zone_splits_a_balancing_authority():
    """Gate G18: a BA maps to exactly one zone, so no zone is finer than a BA."""
    assert all(isinstance(zone, str) for zone in _NWPP_BA_ZONES.values())


# ---------------------------------------------------------------------------
# The share contract
# ---------------------------------------------------------------------------


def test_parse_shape(nwpp_pool):
    """The parser returns (n_zones, HOURS_PER_YEAR) float64."""
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    assert shares is not None
    assert shares.shape == (len(_ZONES), HOURS_PER_YEAR)
    assert shares.dtype == np.float64


def test_shares_sum_to_one_every_hour(nwpp_pool):
    """THE GATE: shares sum to 1.0 in every one of the 8760 hours."""
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    assert np.abs(shares.sum(axis=0) - 1.0).max() < 1e-12


def test_shares_reproduce_the_injected_member_split(nwpp_pool):
    """A known per-BA split comes back as exactly the member-count share.

    With every load-carrying member flat at the same MW, each zone's share is
    its count of load-carrying members over the fifteen that carry load — so
    NWPP-EAST (PACE alone) is 1/15 and NWPP-NW (seven of its eight, AVRN
    carrying none) is 7/15.
    """
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    expected = {
        "NWPP-NW": 7 / 15,
        "NWPP-OR": 2 / 15,
        "NWPP-INLAND": 4 / 15,
        "NWPP-EAST": 1 / 15,
        "NWPP-SNV": 1 / 15,
    }
    for i, zone in enumerate(_ZONES):
        assert np.allclose(shares[i], expected[zone], atol=1e-12)


def test_generation_only_bas_carry_exactly_zero_load(nwpp_pool):
    """AVRN and GRID move no share: null demand enters their zone as 0.0 MW.

    Their GENERATION still lands in NWPP-NW / NWPP-OR through the same zone map
    — that is the supply side and not this parser's business — but a change that
    let their all-NaN demand enter as anything but zero would silently reweight
    two zones.
    """
    as_null = czs.parse_nwpp_shares(_YEAR, _ZONES)
    # The same pool with the two members filing an explicit 0.0 MW instead of a
    # null must give byte-identical shares: the parser may not treat "no demand
    # column" and "zero demand" differently, and it may not interpolate the
    # null pair up to the flat member level.
    zeros = np.zeros(HOURS_PER_YEAR)
    nwpp_pool({ba: zeros for ba in _GENERATION_ONLY})
    as_zero = czs.parse_nwpp_shares(_YEAR, _ZONES)
    assert np.array_equal(as_null, as_zero)
    # NWPP-OR holds PGE + PACW + GRID; only the first two carry load.
    assert np.allclose(as_null[_ZONES.index("NWPP-OR")], 2 / 15, atol=1e-12)


def test_shares_are_bounded(nwpp_pool):
    """No share falls outside [0, 1] and none is NaN."""
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    assert np.isfinite(shares).all()
    assert shares.min() >= 0.0 and shares.max() <= 1.0


def test_zone_demand_reproduces_the_pool_total_exactly(nwpp_pool):
    """The shares times the footprint total return the per-zone MW exactly.

    This is the property only a POOL region can have: numerator parts and
    denominator come from one pass over one set of arrays, so the regroup is an
    identity rather than a ratio of two differently-sourced series. Measured on
    the committed data it holds to **0.0 MW** in every hour of 2023-2025.
    """
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    total = np.full(HOURS_PER_YEAR, 15 * _FLAT_MW)
    rebuilt = shares * total
    assert np.abs(rebuilt.sum(axis=0) - total).max() < 1e-9
    assert np.allclose(rebuilt[_ZONES.index("NWPP-EAST")], _FLAT_MW, atol=1e-9)


# ---------------------------------------------------------------------------
# The demand convention (NWPP-10 §1.3) — the reason this parser is not generic
# ---------------------------------------------------------------------------


def test_a_cold_snap_spike_is_not_screened(nwpp_pool):
    """THE CHPD GUARD: a 2.8 x median hour is REAL LOAD and must survive.

    ``_screen_demand_spikes`` justifies its 2.5 x median bar on the claim that
    "every legitimate demand series has max/median <= 2.1". This footprint
    falsifies that: CHPD's peak/median is 2.29 / 2.83 / 2.50 across 2023-2025,
    and the 54 hours the screen flags are a documented cold snap of 12-16
    January 2024 holding CHPD's annual peak (583 MW) and the whole NWPP-NW
    zone's 2024 annual peak (21,560 MW at 2024-01-13 19:00 UTC), on which EIA's
    own ``Adjusted`` column is byte-identical to raw. Screening them would
    delete a real regional peak and interpolate over it — a rule-14
    ``[R-ACCURATE]`` violation by construction, and a gate-G20 failure in the
    other direction.

    Here CHPD stands in for itself: one hour at 2.8 x its flat median. The hour
    must raise NWPP-NW's share, not be smoothed back to the flat value.
    """
    spike = np.full(HOURS_PER_YEAR, _FLAT_MW)
    spike[299] = _FLAT_MW * 2.8
    nwpp_pool({"CHPD": spike})
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    nw = shares[_ZONES.index("NWPP-NW")]
    # Footprint total in the spike hour is 15,000 + 1,800; NWPP-NW holds
    # 7,000 + 1,800 of it.
    assert nw[299] == pytest.approx(8800.0 / 16800.0, abs=1e-12)
    assert nw[299] > nw[298]  # the peak survives as a peak
    assert nw[298] == pytest.approx(7 / 15, abs=1e-12)


def test_exact_zero_dropout_is_repaired(nwpp_pool):
    """The dropout screen DOES fire: an exactly-zero hour is a reporting gap.

    Seventeen NEVP hours of 2025 survive into ``Demand (Adjusted)`` as literal
    0.0 MW. A footprint member can never truly read zero, so unlike the spike
    case this one is a defect and is repaired — the one screen the convention
    keeps.
    """
    dropout = np.full(HOURS_PER_YEAR, _FLAT_MW)
    dropout[4000] = 0.0
    nwpp_pool({"NEVP": dropout})
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    snv = shares[_ZONES.index("NWPP-SNV")]
    assert snv[4000] == pytest.approx(1 / 15, abs=1e-12)
    assert snv[4000] > 0.0


# ---------------------------------------------------------------------------
# Degradation: absence must read as absence, never as a partial share matrix
# ---------------------------------------------------------------------------


def test_incomplete_pool_returns_none(nwpp_pool):
    """A pool that cannot assemble all seventeen members -> None.

    ``_pool_member_frames`` already refuses a subset; this pins that the parser
    propagates the refusal instead of serving a footprint missing a member,
    which would understate the denominator and inflate every other zone.
    """
    nwpp_pool(present=False)
    assert czs.parse_nwpp_shares(_YEAR, _ZONES) is None


def test_member_outside_the_caller_zone_list_returns_none(nwpp_pool):
    """A member whose zone is not in the caller's list -> None, never a drop.

    Silently skipping it would remove its load from the denominator and
    renormalise the other zones upward — a share error with no visible symptom.
    """
    assert czs.parse_nwpp_shares(_YEAR, [z for z in _ZONES if z != "NWPP-SNV"]) is None


# ---------------------------------------------------------------------------
# The clean seam
# ---------------------------------------------------------------------------


def test_round_trip_through_clean_parquet(nwpp_pool, tmp_clean_dir):
    """Parse -> write_clean -> read_clean returns a bit-identical matrix."""
    shares = czs.parse_nwpp_shares(_YEAR, _ZONES)
    df = czs._shares_to_long(shares, _ZONES)
    df["hour"] = df["hour"].astype("int64")
    df["zone"] = df["zone"].astype("string")
    df["share"] = df["share"].astype("float64")
    write_clean(df, "zonal-shares", iso="NWPP", year=_YEAR)

    back = read_clean("zonal-shares", iso="NWPP", year=_YEAR, validate=False)
    pivot = back.pivot(index="hour", columns="zone", values="share")
    pivot = pivot.reindex(columns=_ZONES)
    assert np.array_equal(pivot.to_numpy(dtype=float).T, shares)


def test_registered_in_the_parse_dispatch_table():
    """NWPP is served by the shared raw-fallback path, not a bespoke one."""
    assert czs._PARSE_FUNCS["NWPP"] is czs.parse_nwpp_shares
