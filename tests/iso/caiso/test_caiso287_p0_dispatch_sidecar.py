"""caiso-287: the OPT-IN P0 dispatch / dual sidecar — round-trip and byte-neutrality.

The MW-valued sibling of ``test_miso155_p0_commitment_sidecar``, and it exists
for a property that one cannot carry: the bit-packed on/off pattern recovers
the RA-bridge detector's ``runs``, but neither screen that acts on them can be
replayed from it. The ``startup_aware`` run screen scores each run on
``sum((price - mc) * dispatch) / pmax`` and the surplus decommit screen derives
its hourly absorption from the interchange rows' dispatch
(:mod:`market_sim.model.commitment`) — both read MW, and both read the P0
DUALS, which no committed sidecar carries either (``hourly/system_<year>``
is ``pass == "P1"`` only). That is why ``RESULT-caiso286`` section 7 could only
bound the two screens instead of splitting them.

The traps this covers:

* **Exactness.** The payload round-trips bit-for-bit through the parquet. A
  narrowed float would make the reproduction gate a tolerance rather than an
  equality, which is the only property the sidecar has.
* **The zone map.** The prices carry their zone NAMES, taken from the solve's
  own ``iso_config.zone_names``. A consumer that re-derives the ordering with
  ``sorted(unique)`` reads every price from the wrong zone — the defect
  caiso-286 section 4 caught in its own probe, and the reason the names are
  written rather than left to be recomputed.
* **Write-only.** With the flag off ``p2_state`` carries no record and the
  writer adds no file, so every existing bundle stays byte-identical.
* **The load-bearing property**, last and on the real detector: a
  ``caiso_ra_mustoffer_min_gen`` call driven by the ROUND-TRIPPED arrays
  returns a floor identical to the one the originals produce. That equality is
  what makes an offline screen replay evidence rather than an approximation.

Trivial cases first (CLAUDE.md testing pattern): the round-trip tests run on
hand-built arrays, and the detector equivalence on a 2-gen / 48-hour fleet.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from tests.helpers import REPO_ROOT as REPO  # noqa: E402

for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.run_calibration_full import _write_p0_dispatch_sidecar  # noqa: E402


class _G:
    """The two attributes the writer touches."""

    def __init__(self, uid: str) -> None:
        self.unit_id = uid


def _read_dispatch(path: Path) -> np.ndarray:
    """Rebuild the ``(n_gen, T)`` MW array the way a consumer must."""
    pd = pytest.importorskip("pandas")
    df = pd.read_parquet(path).sort_values("gen_index")
    hours = int(df["n_hours"].iloc[0])
    out = np.stack([np.frombuffer(b, dtype=np.float64) for b in df["mw"]])
    assert out.shape[1] == hours
    return out


def test_writer_is_a_noop_without_the_record(tmp_path: Path) -> None:
    """Flag off => no key in ``p2_state`` => no file, not an empty one."""
    assert _write_p0_dispatch_sidecar(tmp_path, 2023, {"fleet": []}) == []
    assert not (tmp_path / "hourly").exists()


def test_dispatch_round_trips_bit_for_bit(tmp_path: Path) -> None:
    """Exactness: every MW value survives the parquet trip unchanged."""
    rng = np.random.default_rng(0)
    # Values with full float64 mantissas, plus the exact zeros a real dispatch
    # is mostly made of — a narrowing cast would survive the zeros and fail here.
    disp = rng.random((5, 48)) * 137.37731331
    disp[disp < 0.3 * 137.0] = 0.0
    state = {
        "fleet": [_G(f"U{i}") for i in range(5)],
        "p0_dispatch_mw": disp,
        "p0_zonal_prices": None,
    }

    written = _write_p0_dispatch_sidecar(tmp_path, 2024, state)
    assert [p.name for p in written] == ["p0_dispatch_2024.parquet"]

    back = _read_dispatch(written[0])
    # array_equal, not allclose: the point is bit-for-bit.
    assert np.array_equal(back, disp)


def test_prices_carry_their_zone_names_in_row_order(tmp_path: Path) -> None:
    """The caiso-286 trap: the map is WRITTEN, and it is the solve's own order.

    ``zone_names`` here is deliberately NOT in sorted order, so a consumer that
    re-derived it with ``sorted(unique)`` would silently transpose the rows.
    """
    pd = pytest.importorskip("pandas")

    zone_names = ["NP15", "ZP26", "LA_BASIN", "SDGE"]
    assert zone_names != sorted(zone_names), "fixture must defeat sorted()"
    prices = np.arange(4 * 6, dtype=float).reshape(4, 6) * 1.5 - 7.25

    written = _write_p0_dispatch_sidecar(
        tmp_path,
        2024,
        {
            "fleet": [_G("U0")],
            "p0_dispatch_mw": np.zeros((1, 6)),
            "p0_zonal_prices": prices,
            "zone_names": zone_names,
        },
    )
    assert [p.name for p in written] == [
        "p0_dispatch_2024.parquet",
        "p0_prices_2024.parquet",
    ]

    df = pd.read_parquet(written[1])
    for z, name in enumerate(zone_names):
        sub = df[df["zone"] == name].sort_values("hour")
        assert list(sub["zone_index"].unique()) == [z]
        assert np.array_equal(sub["price"].to_numpy(), prices[z])


def test_row_count_mismatches_raise_rather_than_pad(tmp_path: Path) -> None:
    """Row alignment is the whole value of the file, so a mismatch is fatal."""
    with pytest.raises(ValueError, match="row alignment"):
        _write_p0_dispatch_sidecar(
            tmp_path,
            2024,
            {"fleet": [_G("U0")], "p0_dispatch_mw": np.zeros((3, 6))},
        )
    with pytest.raises(ValueError, match="zone names"):
        _write_p0_dispatch_sidecar(
            tmp_path,
            2024,
            {
                "fleet": [_G("U0")],
                "p0_dispatch_mw": np.zeros((1, 6)),
                "p0_zonal_prices": np.zeros((4, 6)),
                "zone_names": ["A", "B"],
            },
        )


def test_round_tripped_arrays_reproduce_the_production_detector(
    tmp_path: Path,
) -> None:
    """The property the whole sidecar exists for.

    The REAL ``caiso_ra_mustoffer_min_gen``, with both screens armed, must
    return an identical floor whether it is handed the original arrays or the
    ones read back off disk. Trivial fleet first: two gas CCs, 48 hours.
    """
    from market_sim.data.fleet import generators_to_fleet_arrays
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen

    from tests.helpers.builders import make_gen

    hours = 48
    gens = [
        make_gen(
            unit_id="CC_A",
            zone="Z0",
            fuel_type="gas_cc",
            plant_group="CC_REGULAR",
            heat_rate=7.2,
            startup_cost_per_mw=50.0,
            pmax_mw=400.0,
        ),
        make_gen(
            unit_id="IMP",
            zone="Z0",
            fuel_type="import",
            plant_group="IMPORT",
            heat_rate=0.0,
            pmax_mw=500.0,
            pmin_mw=-200.0,
        ),
    ]
    arrays = generators_to_fleet_arrays(gens, ["Z0"])

    # Two runs with an idle gap between them — the shape the gap bridges read.
    disp = np.zeros((2, hours), dtype=float)
    disp[0, 0:10] = 331.7318273641
    disp[0, 22:48] = 288.1093827465
    disp[1, :] = 74.3319284716  # the import row the decommit screen absorbs on
    mc = np.full((2, hours), 31.3617238491)
    # The run hours must clear MC or ``startup_aware`` drops both runs and the
    # detector goes inert; the gap must be cheap enough that the restart
    # inequality passes, or nothing bridges. Both are asserted below rather
    # than assumed.
    prices = np.full((1, hours), 60.4471339287, dtype=float)
    prices[0, 10:22] = 25.1183726449  # the gap the bridge has to hold across

    def _floor(d: np.ndarray, p: np.ndarray) -> np.ndarray:
        return caiso_ra_mustoffer_min_gen(
            d,
            arrays,
            gens,
            0.26,
            p1_prices=p,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
            startup_aware=True,
        )

    want = _floor(disp, prices)
    # T-7, disbelieve clean zeros: an all-zero floor would make the equality
    # below pass vacuously. Assert the detector is LIVE on this fixture first.
    assert want.any(), "detector is inert — the equality test would be vacuous"

    written = _write_p0_dispatch_sidecar(
        tmp_path,
        2024,
        {
            "fleet": [_G(g.unit_id) for g in gens],
            "p0_dispatch_mw": disp,
            "p0_zonal_prices": prices,
            "zone_names": ["Z0"],
        },
    )
    pd = pytest.importorskip("pandas")
    back_disp = _read_dispatch(written[0])
    pdf = pd.read_parquet(written[1]).sort_values(["zone_index", "hour"])
    back_prices = pdf["price"].to_numpy().reshape(1, hours)

    assert np.array_equal(_floor(back_disp, back_prices), want)
