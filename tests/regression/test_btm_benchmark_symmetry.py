"""The grid-delivered benchmark's subtrahend may never escape its minuend.

The dashboard benchmark's ``classFull`` cell is

    classFull[k] = e923_bench[k] - btm[k]

built from ``_benchmark_eia923_frame`` (minuend) and ``_btm_frame``
(subtrahend). Both are keyed on the same per-(plant, class) EIA-923 totals and
the BTM host share is a fraction <= 1, so ``btm[k] <= e923_bench[k]`` must hold
for every class -- a metered grid volume cannot be negative.

It did not hold. ``--btm-backfill-year`` carries a plant's donor-vintage class
total when the target year's EIA-923 release is a thin monthly survey, and it
was applied to the BTM side ONLY: the CAMPD backfill inside
``_backfill_eia923_with_campd`` fires on **non-CHP** plants by construction, so
a backfilled CHP plant's host share was subtracted from a class total that
never received the plant's energy. PJM 2025 committed
``classFull.CT_CHP = -0.3726 TWh`` on exactly that path (pjm-129 §6, localized
and reproduced by pjm-130: arming ``--btm-backfill-year 2024`` recovers the
committed ``btmClass`` cells 4.4251 / 2.0959 / 0.6801 to 4 dp).

``_backfill_chp_eia923_from_donor`` mirrors the repair onto the benchmark. These
tests pin the invariant and the no-op property, on synthetic frames so they run
without the EIA-923/CAMPD corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import run_calibration_full as rcf  # noqa: E402

MCOLS = [f"m{i:02d}" for i in range(1, 13)]


def _bench_frame(rows: list[tuple[int, str, float]], year: int) -> pd.DataFrame:
    """Minimal ``_benchmark_eia923_frame``-shaped frame."""
    return pd.DataFrame(
        [
            {
                "year": np.int16(year),
                "plant_id": pid,
                "klass": klass,
                "annual_mwh": annual,
                **{c: annual / 12.0 for c in MCOLS},
            }
            for pid, klass, annual in rows
        ]
    )


def _generation(rows: list[tuple[int, int, str, str, str, float]]) -> pd.DataFrame:
    """Minimal EIA-923 ``generation``-shaped frame.

    rows: (year, plant_id, fuel_type, prime_mover, chp_flag, netgen_annual_mwh)
    """
    cols = rcf.monthly_netgen_columns()
    return pd.DataFrame(
        [
            {
                "year": y,
                "plant_id": pid,
                "fuel_type": fuel,
                "prime_mover": pm,
                "chp": chp,
                "netgen_annual_mwh": net,
                **{c: net / 12.0 for c in cols},
            }
            for y, pid, fuel, pm, chp, net in rows
        ]
    )


def test_donor_backfill_lifts_the_benchmark_for_a_missing_chp_plant():
    """A CHP plant absent from the thin vintage is carried onto BOTH sides."""
    year, donor_year = 2025, 2024
    # Plant 100 reports nothing in 2025 and 3.0 TWh of CT_CHP in 2024.
    gen = _generation([(donor_year, 100, "NG", "GT", "Y", 3_000_000.0)])
    bench = _bench_frame([(200, "CT_CHP", 1_000_000.0)], year)

    out = rcf._backfill_chp_eia923_from_donor(
        bench,
        gen,
        {100: "CT_CHP", 200: "CT_CHP"},
        year,
        donor_year,
        campd_active={100},
    )
    total = out.groupby("klass")["annual_mwh"].sum()["CT_CHP"]
    assert total == pytest.approx(4_000_000.0)
    assert 100 in set(out["plant_id"])


def test_measured_plant_is_never_overwritten():
    """A (plant, class) the target vintage already reports is left alone."""
    year, donor_year = 2025, 2024
    gen = _generation([(donor_year, 100, "NG", "GT", "Y", 9_000_000.0)])
    bench = _bench_frame([(100, "CT_CHP", 1_000_000.0)], year)

    out = rcf._backfill_chp_eia923_from_donor(
        bench, gen, {100: "CT_CHP"}, year, donor_year, campd_active={100}
    )
    assert out.groupby("klass")["annual_mwh"].sum()["CT_CHP"] == pytest.approx(
        1_000_000.0
    )


def test_cems_silent_plant_stays_dropped_on_both_sides():
    """``campd_active`` gates the benchmark repair exactly as it gates the BTM."""
    year, donor_year = 2025, 2024
    gen = _generation([(donor_year, 100, "NG", "GT", "Y", 3_000_000.0)])
    bench = _bench_frame([(200, "CT_CHP", 1_000_000.0)], year)

    out = rcf._backfill_chp_eia923_from_donor(
        bench, gen, {100: "CT_CHP", 200: "CT_CHP"}, year, donor_year, campd_active=set()
    )
    assert out.groupby("klass")["annual_mwh"].sum()["CT_CHP"] == pytest.approx(
        1_000_000.0
    )


def test_non_chp_classes_are_untouched():
    """The repair covers only CC_CHP / CT_CHP / ST_CHP -- never a grid class."""
    year, donor_year = 2025, 2024
    gen = _generation([(donor_year, 100, "NG", "CA", "N", 5_000_000.0)])
    bench = _bench_frame([(200, "CC_REGULAR", 1_000_000.0)], year)

    out = rcf._backfill_chp_eia923_from_donor(
        bench, gen, {100: "CC_REGULAR", 200: "CC_REGULAR"}, year, donor_year, None
    )
    pd.testing.assert_frame_equal(out, bench)


def test_complete_vintage_is_a_no_op():
    """Nothing missing -> the frame is returned unchanged (byte-identical)."""
    year, donor_year = 2025, 2024
    gen = _generation([(donor_year, 100, "NG", "GT", "Y", 3_000_000.0)])
    bench = _bench_frame([(100, "CT_CHP", 2_000_000.0)], year)

    out = rcf._backfill_chp_eia923_from_donor(
        bench, gen, {100: "CT_CHP"}, year, donor_year, campd_active={100}
    )
    pd.testing.assert_frame_equal(out, bench)


def test_repaired_benchmark_dominates_the_repaired_btm():
    """The invariant itself: btm[k] <= e923_bench[k], so classFull >= 0.

    The BTM side books ``carried * host_share`` for the same (plant, class) the
    benchmark side books ``carried`` for. With both repaired from the same donor
    and the host share <= 1, the class subtraction cannot go negative -- which
    is what the one-sided repair violated.
    """
    year, donor_year = 2025, 2024
    carried = 3_000_000.0
    gen = _generation([(donor_year, 100, "NG", "GT", "Y", carried)])
    bench = _bench_frame([], year)
    bench = pd.DataFrame(columns=["year", "plant_id", "klass", "annual_mwh", *MCOLS])

    repaired = rcf._backfill_chp_eia923_from_donor(
        bench, gen, {100: "CT_CHP"}, year, donor_year, campd_active={100}
    )
    e923_k = float(repaired.groupby("klass")["annual_mwh"].sum()["CT_CHP"])

    # Any admissible host share is a fraction of the same carried total.
    for share in (0.0, 0.25, 0.5, 0.9, 1.0):
        btm_k = carried * share
        assert btm_k <= e923_k + 1e-9
        assert e923_k - btm_k >= -1e-9
