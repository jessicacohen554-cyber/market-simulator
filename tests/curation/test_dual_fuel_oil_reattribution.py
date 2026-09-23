"""The EIA-923 dual-fuel oil re-attribution: two-sided, supply-classed, and first.

``run_calibration_full._reattribute_dual_fuel_oil`` (nyiso-240) books a modelled
plant's EIA-923 ``oil`` rows into the classes its units dispatch in. miso-267
(``docs/FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md``)
found three defects, each pinned here on trivial synthetic fixtures (no on-disk
data):

* **one-sided** — only ``annual > 0`` rows moved, so a modelled plant's
  net-NEGATIVE oil row (station service in a year the unit barely ran) stayed in
  ``oil`` and drove the class below zero: MISO 2022 raw ``+0.3836`` TWh became
  ``-0.0731``;
* **generic COAL** — a coal plant with no measured class shares was booked to
  the bare ``COAL`` model group, a class no other benchmark row carries;
* **order** — it ran AFTER the CAMPD annual backfill, which rebuilds a class
  from a CEMS meter that already contains the unit's oil-fired output, so those
  MWh were booked twice.

The same finding narrows the sibling missing-month backfill
(``_backfill_eia923_missing_months``) to the plant's OPERATING WINDOW: a new
plant's pre-COD months are blank in EIA-923 because they are outside its
reporting boundary, not withheld, and the CEMS energy there is commissioning
test energy the COD-gated fleet cannot dispatch (tests ``d``).
"""

import importlib.util

import numpy as np
import pandas as pd
import pytest
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "rcf_dual_fuel_oil", str(REPO_ROOT / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_MCOLS = [f"m{i:02d}" for i in range(1, 13)]


def _row(pid: int, klass: str, annual: float, year: int = 2022) -> dict:
    """One EIA-923 benchmark row, its annual spread evenly over twelve months."""
    return {
        "year": np.int16(year),
        "plant_id": int(pid),
        "klass": klass,
        "annual_mwh": float(annual),
        **{c: float(annual) / 12.0 for c in _MCOLS},
    }


def _annual(e923: pd.DataFrame, pid: int, klass: str) -> float:
    m = (e923["plant_id"] == pid) & (e923["klass"] == klass)
    return float(e923.loc[m, "annual_mwh"].sum())


def _class(e923: pd.DataFrame, klass: str) -> float:
    return float(e923.loc[e923["klass"] == klass, "annual_mwh"].sum())


# --------------------------------------------------------------------------- #
# two-sided
# --------------------------------------------------------------------------- #
def test_a_modelled_plants_negative_oil_row_moves_too():
    """The MISO 2022 shape: a fleet plant's negative oil row may not stay behind."""
    e923 = pd.DataFrame(
        [
            _row(1, "CT_PEAKER", 50_000.0),
            _row(1, "oil", 3_000.0),  # modelled, positive
            _row(2, "COAL_BIT", 900_000.0),
            _row(2, "oil", -4_000.0),  # modelled, NEGATIVE (station service)
            _row(9, "oil", 500.0),  # NOT modelled -> genuinely oil
        ]
    )
    out = rcf._reattribute_dual_fuel_oil(e923, {1: "CT_PEAKER", 2: "COAL_BIT"})
    assert _class(out, "oil") == pytest.approx(500.0)  # exactly the non-fleet row
    assert _annual(out, 1, "CT_PEAKER") == pytest.approx(53_000.0)
    assert _annual(out, 2, "COAL_BIT") == pytest.approx(896_000.0)
    # Under the one-sided rule this read 500 - 4,000 = -3,500 MWh: a negative
    # "measured" class manufactured from a positive raw total (-500 + ...).


def test_a_the_move_conserves_every_months_mass():
    """A relabelling may not create or destroy a MWh, in any month."""
    e923 = pd.DataFrame(
        [
            _row(1, "CC_REGULAR", 1_000_000.0),
            _row(1, "oil", -2_400.0),
            _row(2, "ST_GAS", 80_000.0),
            _row(2, "oil", 12_000.0),
            _row(3, "oil", -600.0),  # not modelled
        ]
    )
    out = rcf._reattribute_dual_fuel_oil(e923, {1: "CC_REGULAR", 2: "ST_GAS"})
    for col in ("annual_mwh", *_MCOLS):
        assert float(out[col].sum()) == pytest.approx(float(e923[col].sum()))
    assert _class(out, "oil") == pytest.approx(-600.0)  # measured, non-fleet


def test_a_a_non_fleet_negative_row_is_left_as_measured():
    """The residual may be negative — but only through NON-fleet measurement."""
    e923 = pd.DataFrame([_row(7, "oil", -1_200.0)])
    out = rcf._reattribute_dual_fuel_oil(e923, {})
    assert _class(out, "oil") == pytest.approx(-1_200.0)


def test_a_all_zero_row_is_left_alone():
    """Nothing to move is not a move (and adds no target row)."""
    e923 = pd.DataFrame([_row(1, "CT_PEAKER", 10_000.0), _row(1, "oil", 0.0)])
    out = rcf._reattribute_dual_fuel_oil(e923, {1: "CT_PEAKER"})
    assert len(out) == 2
    assert _annual(out, 1, "CT_PEAKER") == pytest.approx(10_000.0)


def test_a_multi_class_plant_splits_a_negative_row_by_its_shares():
    """Both signs follow the same measured prime-mover split."""
    e923 = pd.DataFrame(
        [
            _row(4, "COAL_BIT", 750_000.0),
            _row(4, "ST_GAS", 250_000.0),
            _row(4, "oil", -1_000.0),
        ]
    )
    shares = {4: {"COAL_BIT": 0.75, "ST_GAS": 0.25}}
    out = rcf._reattribute_dual_fuel_oil(e923, {4: "COAL"}, class_shares=shares)
    assert _annual(out, 4, "COAL_BIT") == pytest.approx(749_250.0)
    assert _annual(out, 4, "ST_GAS") == pytest.approx(249_750.0)
    assert _class(out, "oil") == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# generic COAL
# --------------------------------------------------------------------------- #
def test_b_generic_coal_group_books_to_the_supply_class(monkeypatch):
    """No share entry + the bare ``COAL`` model group -> the supply class."""
    monkeypatch.setattr(rcf, "_coal_supply_class", lambda pid, fuel_code="": "COAL_PRB")
    e923 = pd.DataFrame([_row(5, "COAL_PRB", 400_000.0), _row(5, "oil", 800.0)])
    out = rcf._reattribute_dual_fuel_oil(e923, {5: "COAL"})
    assert _annual(out, 5, "COAL_PRB") == pytest.approx(400_800.0)
    assert "COAL" not in set(out["klass"])


# --------------------------------------------------------------------------- #
# order: re-attribute BEFORE the CEMS repairs read the frame
# --------------------------------------------------------------------------- #
def _campd_flat(pid: int, total_mwh: float, hours: int = 8760) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "plant_id": np.int32(pid),
            "hour": np.arange(hours, dtype=np.int32),
            "net_mw": np.full(hours, total_mwh / hours),
        }
    )


def test_c_cems_backfill_does_not_book_oil_fired_mwh_twice(monkeypatch):
    """A dual-fuel peaker whose year ran mostly on oil.

    923 books 30 GWh under gas and 40 GWh under oil; CEMS meters the unit's
    70 GWh whatever it burned. Re-attributed first, the plant's class reads
    70 GWh — reported adequately, so the annual backfill does not fire and the
    class is 70 GWh. The old order fired on the 30 GWh gas row, rebuilt it from
    CEMS (70 GWh, oil hours included) and then added the 40 GWh of oil again:
    110 GWh for a unit that made 70.
    """
    year = 2022
    raw = pd.DataFrame([_row(6, "CT_PEAKER", 30_000.0), _row(6, "oil", 40_000.0)])
    monkeypatch.setattr(rcf, "_eia923_frame", lambda *a, **k: raw.copy())
    monkeypatch.setattr(rcf, "_plant_class_shares", lambda *a, **k: {})
    monkeypatch.setattr(rcf, "_backfill_renewables_eia930", lambda e923, *a, **k: e923)
    no_rows = pd.DataFrame({"year": pd.Series(dtype="int64")})
    out = rcf._benchmark_eia923_frame(
        year,
        no_rows,  # generation: only the missing-month mask reads it -> no gaps
        "MISO",
        _campd_flat(6, 70_000.0),
        {6: "CT_PEAKER"},
        None,
    )
    assert _annual(out, 6, "CT_PEAKER") == pytest.approx(70_000.0)
    assert _class(out, "oil") == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# missing-month backfill: only the plant's operating window is filled
# --------------------------------------------------------------------------- #
def _gen_with_blank_months(
    pid: int, year: int, blank: list[int], mwh: float
) -> pd.DataFrame:
    """One EIA-923 generation row: ``blank`` months NaN, every other month ``mwh``."""
    cols = rcf.monthly_netgen_columns()
    row = {"year": year, "plant_id": pid}
    for i, c in enumerate(cols, start=1):
        row[c] = np.nan if i in blank else mwh
    return pd.DataFrame([row])


def _fill_case(monkeypatch, first_cod: dict) -> pd.DataFrame:
    """A 1 GW-class CC whose EIA-923 is blank Jan-May while CEMS meters every month."""
    year, pid = 2022, 8
    monkeypatch.setattr(rcf, "_plant_first_cod", lambda: first_cod)
    e923 = pd.DataFrame(
        [
            {
                "year": np.int16(year),
                "plant_id": pid,
                "klass": "CC_REGULAR",
                "annual_mwh": 700_000.0,
                **{c: (0.0 if i <= 5 else 100_000.0) for i, c in enumerate(_MCOLS, 1)},
            }
        ]
    )
    return rcf._backfill_eia923_missing_months(
        e923,
        _campd_flat(pid, 120.0 * 8760),
        {pid: "CC_REGULAR"},
        year,
        _gen_with_blank_months(pid, year, [1, 2, 3, 4, 5], 100_000.0),
    )


def test_d_pre_cod_blank_months_are_not_filled(monkeypatch):
    """COD 2022-06: Jan-May are commissioning energy, outside the fleet boundary."""
    out = _fill_case(monkeypatch, {8: (2022, 6)})
    assert _annual(out, 8, "CC_REGULAR") == pytest.approx(700_000.0)


def test_d_withheld_months_inside_the_window_are_still_filled(monkeypatch):
    """An operating plant's blank months are withheld and ARE repaired."""
    out = _fill_case(monkeypatch, {8: (2001, 3)})
    # CEMS 120 MW flat; the plant's own reported-month ratio scales it:
    # e_rep 700,000 / c_rep (120 MW x the Jun-Dec hours).
    months = rcf._hour_to_month(8760)
    c_rep = 120.0 * float((months >= 6).sum())
    gap = 120.0 * float((months <= 5).sum())
    assert _annual(out, 8, "CC_REGULAR") == pytest.approx(
        700_000.0 + gap * 700_000.0 / c_rep
    )


def test_d_unknown_cod_keeps_the_whole_year_window(monkeypatch):
    """No EIA-860 unit record -> no narrowing (the pre-miso-267 behaviour)."""
    out = _fill_case(monkeypatch, {})
    assert _annual(out, 8, "CC_REGULAR") > 700_000.0


def test_d_operating_window_is_inclusive_of_the_cod_month():
    """Mirrors cod_ramp.monthly_online_mask: online FROM the COD month."""
    w = rcf._operating_window((2022, 6), 2022)
    assert w.tolist() == [False] * 5 + [True] * 7
    assert rcf._operating_window((2023, 1), 2022).sum() == 0
    assert rcf._operating_window((2019, 9), 2022).all()
    assert rcf._operating_window(None, 2022).all()
