"""miso-155: the OPT-IN P0 commitment sidecar — round-trip and byte-neutrality.

Covers the two traps the sidecar itself introduces
(``results/calibration/PREREG-miso155-p0-exact-commitment-instrument-2026-08-13.md``
section 9):

* **T-12** — the bit-packing must round-trip EXACTLY, including the final
  partial byte (``T = 8760`` is not a multiple of 8, so ``np.packbits`` pads
  with 4 zero bits that ``unpackbits`` will hand back unless the caller
  re-slices to ``T``). A silent truncation here would corrupt the last four
  hours of every year and nothing downstream would notice.
* **T-14** — the flag must be write-only: with it off, ``p2_state`` carries no
  record and the writer adds no file; the surrogate dispatch rebuilt from the
  pattern must reproduce the PRODUCTION markup bit-identically, which is the
  property that lets the markup be READ instead of reconstructed.

Trivial cases first (CLAUDE.md testing pattern): the packing tests run on
hand-built patterns, and the markup-equivalence test on a 1-gen/24-h fleet
before the real bundle is ever touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.run_calibration import p0_commitment_pattern  # noqa: E402
from scripts.run_calibration_full import (  # noqa: E402
    _write_p0_commitment_sidecar,
)


def _unpack(bits: np.ndarray, hours: int) -> np.ndarray:
    """Rebuild the ``(n_gen, hours)`` boolean the way a consumer must."""
    return np.unpackbits(bits, axis=1)[:, :hours].astype(bool)


@pytest.mark.parametrize("hours", [8, 24, 8759, 8760, 8761])
def test_t12_packing_round_trips_exactly(hours: int) -> None:
    """T-12: pack→unpack is elementwise exact, partial final byte included."""
    rng = np.random.default_rng(0)
    on = rng.random((7, hours)) < 0.4
    pmax = np.full(7, 100.0)
    # A dispatch that is unambiguously above/below the 5%-of-Pmax threshold.
    dispatch = np.where(on, 90.0, 0.0)

    bits = p0_commitment_pattern(dispatch, pmax)
    assert bits.shape == (7, (hours + 7) // 8)
    assert np.array_equal(_unpack(bits, hours), on)


def test_t12_threshold_is_five_percent_of_pmax() -> None:
    """The recorded boolean is exactly the markup's own ``> 0.05 * pmax``."""
    pmax = np.array([100.0, 200.0])
    # Column 0 straddles: 4% of Pmax is OFF, 6% is ON. Column 1 is exactly 5%,
    # which is NOT ``>`` the threshold and must record as OFF.
    dispatch = np.array([[4.0, 5.0, 6.0], [8.0, 10.0, 12.0]])
    got = _unpack(p0_commitment_pattern(dispatch, pmax), 3)
    assert np.array_equal(got, np.array([[False, False, True]] * 2))


def test_t12_zero_pmax_rows_record_as_off() -> None:
    """A ``pmax == 0`` row packs all-off — what the markup itself sees."""
    got = _unpack(p0_commitment_pattern(np.zeros((1, 16)), np.zeros(1)), 16)
    assert not got.any()


def test_t14_writer_is_a_noop_without_the_record(tmp_path: Path) -> None:
    """T-14: flag off ⇒ no key in ``p2_state`` ⇒ no file, not an empty one."""
    assert _write_p0_commitment_sidecar(tmp_path, 2023, {"fleet": []}) == []
    assert not (tmp_path / "hourly").exists()


def test_t14_writer_is_additive_and_readable(tmp_path: Path) -> None:
    """Both sidecars are written, and the pattern survives the parquet trip."""
    pd = pytest.importorskip("pandas")

    class _G:
        def __init__(self, uid: str) -> None:
            self.unit_id = uid

    hours = 24
    on = np.zeros((2, hours), dtype=bool)
    on[0, 3:9] = True
    on[1, ::2] = True
    state = {
        "fleet": [_G("PLANT_A_1"), _G("PLANT_B_2")],
        "p0_commitment_bits": np.packbits(on, axis=1),
        "startup_run_ratio_t": np.linspace(0.6, 1.1, hours),
    }

    written = _write_p0_commitment_sidecar(tmp_path, 2024, state)
    assert [p.name for p in written] == [
        "p0_commitment_2024.parquet",
        "startup_run_ratio_2024.parquet",
    ]

    df = pd.read_parquet(written[0])
    assert list(df["unit_id"]) == ["PLANT_A_1", "PLANT_B_2"]
    back = np.stack([np.frombuffer(b, dtype=np.uint8) for b in df["on_bits"]])
    assert np.array_equal(_unpack(back, hours), on)

    ratios = pd.read_parquet(written[1])
    assert len(ratios) == hours
    assert np.allclose(ratios["run_ratio"].to_numpy(), state["startup_run_ratio_t"])


def test_t14_v3_basis_writes_no_ratio_file(tmp_path: Path) -> None:
    """``run_ratio_t is None`` (the v3 basis) ⇒ the ratio sidecar is omitted."""

    class _G:
        unit_id = "U1"

    written = _write_p0_commitment_sidecar(
        tmp_path,
        2025,
        {
            "fleet": [_G()],
            "p0_commitment_bits": np.packbits(np.ones((1, 8), dtype=bool), axis=1),
            "startup_run_ratio_t": None,
        },
    )
    assert [p.name for p in written] == ["p0_commitment_2025.parquet"]


def test_surrogate_dispatch_reproduces_the_production_markup() -> None:
    """The property the whole sidecar exists for.

    A surrogate dispatch rebuilt as ``pmax * unpacked`` must drive the
    PRODUCTION ``compute_monthly_markup`` to a bit-identical array — that is
    what makes the markup READ rather than reconstructed. Trivial fleet first:
    one CT, 24 hours.
    """
    from market_sim.data.fleet import generators_to_fleet_arrays
    from market_sim.model.commitment import compute_monthly_markup

    from tests.helpers.builders import make_gen

    gens = [
        make_gen(
            fuel_type="gas_ct",
            plant_group="CT_PEAKER",
            heat_rate=10.5,
            startup_cost_per_mw=20.0,
        )
    ]
    arrays = generators_to_fleet_arrays(gens, ["Z0"])
    hours = 24
    rng = np.random.default_rng(7)
    dispatch = np.where(rng.random((1, hours)) < 0.5, float(arrays.pmax[0]) * 0.8, 0.0)

    want = compute_monthly_markup(gens, arrays, dispatch, hours)
    # T-7 / T-3, disbelieve clean zeros: an all-zero markup would make the
    # equality below pass vacuously. Assert the instrument is LIVE first.
    assert want.min() > 0.0, "markup is inert — the equality test would be vacuous"

    bits = p0_commitment_pattern(dispatch, arrays.pmax)
    surrogate = arrays.pmax[:, None] * _unpack(bits, hours)
    got = compute_monthly_markup(gens, arrays, surrogate, hours)

    assert np.array_equal(want, got)
