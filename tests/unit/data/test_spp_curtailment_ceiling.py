"""SPP wind curtailment ceiling (SPP-58) — mechanism and CLI-delivery guards.

Two things are guarded here, and the second exists because it actually failed.

1. **The mechanism.** ``spp_curtail_multipliers`` ceilings wind on both SPP
   zones and never touches solar, the multiplier is a strict function of the
   depth and the share table, and ``depth = 0`` is exactly inert.

2. **CLI DELIVERY — the silent-drop guard.** The SPP-58 screen shard was
   launched against a build in which ``scripts/run_calibration_full.py`` PARSED
   ``--spp-curtailment-ceiling`` and then never read ``args.spp_curtailment_
   ceiling`` into either ``solve_and_persist`` call site. The flag was accepted
   silently and dropped, so the invocation reduced to the CONTROL recipe. That
   failure mode is invisible from the outside: no error, no warning, a bundle
   that looks like a solved arm, and a "null-effect" result that a less careful
   lane would have reported as a real verdict about the mechanism. The shard
   caught it only because it was told to grep the log for a message the
   mechanism must emit.

   ``test_cli_flags_reach_the_solve_seam`` closes that hole for these two
   fields by intercepting the seam the CLI really calls and asserting the
   values arrive. It is deliberately narrow: a general
   every-ScenarioConfig-flag-is-delivered check is a bigger job (a crude static
   sweep flags 31 of 244 candidates, most of which are delivered by other
   routes) and is routed rather than absorbed here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from market_sim.config import paths as _paths
from market_sim.data.curtailment_share import (
    SPP_CEILING_ZONES,
    load_spp_share_table,
    spp_curtail_multipliers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ZONES = ["SPP-North", "SPP-South"]
DEPTH = 0.288137


@pytest.fixture(scope="module")
def reference_dir() -> Path:
    """The derived-table directory, skipping when the table is not built."""
    ref = _paths.RAW_DIR / "reference"
    if load_spp_share_table(ref) is None:
        pytest.skip("spp_curtailment_share.csv not derived in this checkout")
    return ref


def _net_load(n_hours: int = 8760) -> np.ndarray:
    """A synthetic but strictly-varying net load, so every decile is populated."""
    rng = np.random.default_rng(0)
    return (
        20_000.0
        + 8_000.0 * np.sin(np.arange(n_hours) / 137.0)
        + rng.normal(0.0, 500.0, n_hours)
    )


def test_ceiling_applies_to_wind_on_both_zones_and_never_to_solar(reference_dir):
    """Wind is ceilinged on both SPP zones; the solar multiplier is exactly 1.0.

    SPP's solar bound is ``delivered_pinned`` — it carries no gross-up headroom
    — so ceilinging it would curtail energy the market actually delivered.
    """
    wind, solar = spp_curtail_multipliers(
        _net_load(), ZONES, depth_wind=DEPTH, reference_dir=reference_dir
    )
    assert wind.shape == (2, 8760)
    assert np.array_equal(solar, np.ones((2, 8760)))
    assert set(ZONES) == set(SPP_CEILING_ZONES)
    # Both zones carry the SAME ceiling: the derived incidence is footprint-wide
    # and the 2-zone reduction offers no corridor to attribute it to.
    assert np.array_equal(wind[0], wind[1])
    assert wind.min() > 0.0 and wind.max() <= 1.0
    # It must actually bite somewhere, or the guard is vacuous.
    assert wind.min() < 1.0


def test_depth_zero_is_exactly_inert(reference_dir):
    """``depth = 0`` is the ablation: the bound is returned untouched."""
    wind, solar = spp_curtail_multipliers(
        _net_load(), ZONES, depth_wind=0.0, reference_dir=reference_dir
    )
    assert np.array_equal(wind, np.ones((2, 8760)))
    assert np.array_equal(solar, np.ones((2, 8760)))


def test_non_spp_zones_are_untouched(reference_dir):
    """A zone list carrying no SPP zone gets neutral multipliers, not a crash."""
    wind, solar = spp_curtail_multipliers(
        _net_load(),
        ["West", "Panhandle"],
        depth_wind=DEPTH,
        reference_dir=reference_dir,
    )
    assert np.array_equal(wind, np.ones((2, 8760)))
    assert np.array_equal(solar, np.ones((2, 8760)))


def test_missing_share_table_degrades_to_none(tmp_path):
    """No derived table => ``None``, so the caller keeps the static bound."""
    assert (
        spp_curtail_multipliers(
            _net_load(), ZONES, depth_wind=DEPTH, reference_dir=tmp_path
        )
        is None
    )


def test_ceiling_is_deeper_where_congestion_is_measured_higher(reference_dir):
    """The ceiling tracks the measured share: lower net load, deeper ceiling.

    Not a claim about any residual — it asserts only that the multiplier is the
    declared monotone function of the derived incidence, which is what makes the
    reduction concentrated rather than flat (PRECOMMIT gate G-3's premise).
    """
    net_load = _net_load()
    wind, _ = spp_curtail_multipliers(
        net_load, ZONES, depth_wind=DEPTH, reference_dir=reference_dir
    )
    lowest = np.argsort(net_load)[: 8760 // 10]
    highest = np.argsort(net_load)[-(8760 // 10) :]
    assert wind[0][lowest].mean() < wind[0][highest].mean()


@pytest.mark.slow
def test_cli_flags_reach_the_solve_seam(tmp_path):
    """``--spp-curtailment-ceiling`` must ARRIVE at ``solve_and_persist``.

    The regression this exists for: the flag parsed and was then dropped, so a
    solve launched with it silently produced the control. Intercepting the seam
    the CLI actually calls is the only check that catches that — reading the
    argparse block does not, because the argparse block was correct.
    """
    spec = importlib.util.spec_from_file_location(
        "_rcf_delivery_probe", REPO_ROOT / "scripts" / "run_calibration_full.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["_rcf_delivery_probe"] = module
    saved_argv = sys.argv
    try:
        sys.argv = ["run_calibration_full.py"]
        spec.loader.exec_module(module)

        captured: dict = {}

        class _Reached(Exception):
            pass

        def _intercept(*_args, **kwargs):
            captured.update(kwargs)
            raise _Reached

        module.solve_and_persist = _intercept
        sys.argv = [
            "run_calibration_full.py",
            "--iso",
            "SPP",
            "--year",
            "2024",
            "--out-dir",
            str(tmp_path / "probe"),
            "--spp-curtailment-ceiling",
            "--spp-curtail-depth-wind",
            "0.25",
        ]
        with pytest.raises(_Reached):
            module.main()
    finally:
        sys.argv = saved_argv
        sys.modules.pop("_rcf_delivery_probe", None)

    assert captured.get("spp_curtailment_ceiling") is True, (
        "--spp-curtailment-ceiling was parsed but never delivered to "
        "solve_and_persist — the SPP-58 silent-drop regression is back"
    )
    assert captured.get("spp_curtail_depth_wind") == pytest.approx(0.25), (
        "--spp-curtail-depth-wind was parsed but never delivered to solve_and_persist"
    )
