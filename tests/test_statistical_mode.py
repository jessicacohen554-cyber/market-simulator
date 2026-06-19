"""The --statistical-mode umbrella disables every answer-injection overlay.

`apply_statistical_mode` is the single switch the audit's out-of-sample
backcast (docs/ercot-backcast-audit-2026-06.md §D1) relies on: it must turn
off the historic outage overlay, the CT and spatial deployment floors, the ST
WEFOR-residual relief, and per-plant monthly coal pricing — while leaving the
structural levers alone.
"""

import argparse
import importlib.util
from pathlib import Path
from types import SimpleNamespace

_SPEC = importlib.util.spec_from_file_location(
    "run_calibration_full",
    Path(__file__).resolve().parents[1] / "scripts" / "run_calibration_full.py",
)
_RCF = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RCF)


def _keeper_args() -> argparse.Namespace:
    """The run-115b keeper's overlay-bearing args (all answer-injection ON)."""
    return SimpleNamespace(
        statistical_mode=True,
        outage_source="historic",
        ct_deployment=True,
        reliability_deployment=True,
        wefor_residual=0.06,
        wefor_relief_groups="ST_GAS,ST_CHP",
        no_coal_monthly_pricing=False,
    )


def test_statistical_mode_disables_every_overlay():
    args = _keeper_args()
    _RCF.apply_statistical_mode(args)
    assert args.outage_source == "statistical"
    assert args.ct_deployment is False
    assert args.reliability_deployment is False
    assert args.wefor_residual is None
    assert args.wefor_relief_groups is None
    assert args.no_coal_monthly_pricing is True


def test_no_op_when_flag_unset():
    args = _keeper_args()
    args.statistical_mode = False
    _RCF.apply_statistical_mode(args)
    # Every overlay survives untouched.
    assert args.outage_source == "historic"
    assert args.ct_deployment is True
    assert args.reliability_deployment is True
    assert args.wefor_residual == 0.06
    assert args.no_coal_monthly_pricing is False


def test_ercot_calibration_enables_storage_vintage_ramp():
    """ERCOT (and CAISO) backcast configs ramp storage by COD; PJM stays flat."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "run_calibration",
        Path(__file__).resolve().parents[1] / "scripts" / "run_calibration.py",
    )
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    assert rc._calibration_config(2024, "ERCOT", 8760, 2.19).storage_vintage_ramp
    assert rc._calibration_config(2024, "CAISO", 8760, 2.19).storage_vintage_ramp
    assert not rc._calibration_config(2024, "PJM", 8760, 2.19).storage_vintage_ramp
