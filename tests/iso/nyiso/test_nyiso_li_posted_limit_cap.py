"""Tests for the NYISO Long Island posted-limit sub-clip (NYISO-NEXT-6).

``ScenarioConfig.nyiso_li_seam_posted_limit_cap`` caps the
``NYISO_external>Long_Island`` import bound at the summed POSTED import limits
of Neptune / CSC / 1385. The properties its legitimacy rests on:

* it only ever LOWERS the Long Island border link — never raises it, never
  touches another link (the internal ``NYC>Long_Island`` link included);
* posted limits land on the model's fixed non-leap clock (Feb 29 dropped),
  with the more binding posting kept on the DST fall-back hour;
* it never silently no-ops (a missing tie raises);
* it is default-off and keyed only when armed.

Trivial cases first (24 hours), then the committed partitions reproduce the
PRECOMMIT §4 footprint (``fulldata``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data.nyiso_seam_envelope import (
    NYISO_LI_POSTED_LIMIT_TIES,
    nyiso_li_posted_limit_cap,
    posted_import_limit_hourly,
)

NEPTUNE, CSC, L1385 = NYISO_LI_POSTED_LIMIT_TIES


class _Link:
    def __init__(self, from_zone: str, to_zone: str, ttc_mw: float) -> None:
        self.from_zone, self.to_zone, self.ttc_mw = from_zone, to_zone, ttc_mw


class _Config:
    """Minimal ISOConfig stand-in — the module only reads ``links``."""

    def __init__(self, links: list[_Link]) -> None:
        self.links = links


def _links() -> list[_Link]:
    # The internal NYC>Long_Island link comes FIRST and shares the to_zone, so
    # a to_zone lookup alone could select the wrong column.
    return [
        _Link("NYC", "Long_Island", 1650.0),
        _Link("Long_Island", "NYC", 1650.0),
        _Link("NYISO_external", "NYC", 1000.0),
        _Link("NYISO_external", "Long_Island", 1200.0),
    ]


def _posting(start: str, hours: int, limits: dict[str, np.ndarray]) -> pd.DataFrame:
    """A per-tie hourly posting with the given positive limits."""
    stamps = pd.date_range(start, periods=hours, freq="h")
    return pd.concat(
        [
            pd.DataFrame(
                {
                    "interval_start_local": stamps,
                    "interface": tie,
                    "flow_mw": 0.0,
                    "positive_limit_mw": np.asarray(lim, dtype=float),
                }
            )
            for tie, lim in limits.items()
        ],
        ignore_index=True,
    )


def test_clip_lowers_only_the_border_link_and_never_raises():
    """cap = min(envelope, sum of posted limits) on the LI border column only."""
    h = 24
    nep = np.full(h, 660.0)
    nep[5:8] = 0.0  # Neptune on outage for three hours
    frame = _posting(
        "2023-01-01",
        h,
        {NEPTUNE: nep, CSC: np.full(h, 330.0), L1385: np.full(h, 200.0)},
    )
    cfg = _Config(_links())
    envelope = np.tile(np.array([1650.0, 1650.0, 900.0, 1000.0]), (h, 1))
    out = nyiso_li_posted_limit_cap(envelope, cfg, 2023, h, frame=frame)
    li = out[:, 3]
    # posted sum 1,190 > envelope 1,000 when all up: no raise, cap unchanged
    assert np.all(li[np.r_[0:5, 8:24]] == 1000.0)
    # Neptune out: posted sum 530 < 1,000
    assert np.all(li[5:8] == 530.0)
    # every other column byte-identical, the internal LI link included
    np.testing.assert_array_equal(out[:, :3], envelope[:, :3])
    assert np.all(out <= envelope)


def test_posted_limits_use_the_non_leap_model_clock():
    """A leap year's Feb 29 is dropped, so Mar 1 lands on model day 59."""
    hours = 8760
    stamps = pd.date_range("2024-01-01", periods=8784, freq="h")
    lim = np.full(8784, 500.0)
    lim[(stamps.month == 3) & (stamps.day == 1) & (stamps.hour == 0)] = 0.0
    frame = _posting(
        "2024-01-01",
        8784,
        {NEPTUNE: lim, CSC: np.full(8784, 100.0), L1385: np.full(8784, 100.0)},
    )
    got = posted_import_limit_hourly(frame, NYISO_LI_POSTED_LIMIT_TIES, hours)
    assert got.shape == (hours,)
    assert got[59 * 24] == 200.0  # Mar 1 00:00 on the 2023-keyed clock
    assert np.count_nonzero(got == 200.0) == 1


def test_dst_duplicate_hour_keeps_the_more_binding_posting():
    """Two postings on one local label: the lower limit governs the hour."""
    frame = _posting(
        "2023-01-01", 2, {NEPTUNE: [600, 600], CSC: [300, 300], L1385: [100, 100]}
    )
    dup = frame.iloc[[0]].copy()
    dup["positive_limit_mw"] = 0.0  # same local hour, NEPTUNE posts 0
    frame = pd.concat([frame, dup], ignore_index=True)
    got = posted_import_limit_hourly(frame, NYISO_LI_POSTED_LIMIT_TIES, 2)
    np.testing.assert_array_equal(got, [400.0, 1000.0])


def test_missing_tie_raises_rather_than_no_opping():
    """A tie absent from the partition is an error, never a silent no-clip."""
    frame = _posting("2023-01-01", 24, {NEPTUNE: np.full(24, 660.0)})
    with pytest.raises(ValueError, match="never silently no-ops"):
        posted_import_limit_hourly(frame, NYISO_LI_POSTED_LIMIT_TIES, 24)


def test_missing_border_link_raises():
    """No NYISO_external>Long_Island link: the clip refuses to run."""
    frame = _posting(
        "2023-01-01",
        24,
        {t: np.full(24, 100.0) for t in NYISO_LI_POSTED_LIMIT_TIES},
    )
    cfg = _Config([_Link("NYC", "Long_Island", 1650.0)])
    with pytest.raises(FileNotFoundError, match="Long_Island"):
        nyiso_li_posted_limit_cap(np.ones((24, 1)), cfg, 2023, 24, frame=frame)


def test_field_is_default_off_and_keyed_only_when_armed():
    """Default off; the default config's cache key is unmoved by the field."""
    from market_sim.config.scenarios import ScenarioConfig

    base = ScenarioConfig()
    assert base.nyiso_li_seam_posted_limit_cap is False
    armed = base.with_overrides(nyiso_li_seam_posted_limit_cap=True)
    assert armed.cache_key() != base.cache_key()
    assert (
        base.with_overrides(nyiso_li_seam_posted_limit_cap=False).cache_key()
        == base.cache_key()
    )


@pytest.mark.fulldata
@pytest.mark.integration
@pytest.mark.parametrize(
    ("year", "hours_cut", "cut_twh"),
    # PRECOMMIT-nyiso-next5 §4. 2024 is 969 / 0.269 on the model clock: the
    # NEXT-5 probe indexed hours from Jan 1 without dropping Feb 29, which
    # gives 968 / 0.270 (docs/RESULT-nyiso-next6-li-posted-limit-2026-09-27.md).
    [
        (2021, 860, 0.160),
        (2022, 1468, 0.343),
        (2023, 1688, 0.268),
        (2024, 969, 0.269),
        (2025, 1734, 0.308),
    ],
)
def test_committed_partitions_reproduce_the_precommit_footprint(
    year, hours_cut, cut_twh
):
    """The real postings give the pre-registered LI hours cut and TWh removed."""
    pytest.importorskip("pyarrow")
    from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE
    from market_sim.data.nyiso_seam_envelope import seam_envelope_by_zone

    try:
        from scripts.lib.clean_io import read_clean

        frame = read_clean(
            "nyiso-interface-flows", iso="NYISO", year=year, validate=False
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"nyiso-interface-flows clean partition absent: {exc}")
    if frame is None or frame.empty:
        pytest.skip("nyiso-interface-flows clean partition absent")
    cap = seam_envelope_by_zone(frame, 8760, NYISO_SEAM_FLOW_PERCENTILE)["Long_Island"][
        0
    ]
    cfg = _Config(_links())
    env = np.zeros((8760, 4))
    env[:, 3] = cap
    out = nyiso_li_posted_limit_cap(env, cfg, year, 8760, frame=frame)
    cut = cap - out[:, 3]
    assert int((cut > 0).sum()) == hours_cut
    assert round(float(cut.sum()) / 1e6, 3) == pytest.approx(cut_twh, abs=1e-9)
