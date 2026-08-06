"""The bench nameplate lookup must cover plants that RETIRE inside the backcast
window, not just the operable EIA-860 vintage (pjm-159, the cross-ISO defect
pjm-158 §1.1 found).

The defect: ``render_calibration_html._eia860_plant_info`` read only the operable
snapshot — a single recent vintage — so a plant that ran through part of
2022-2025 and retired before that vintage was absent from it entirely. Such a
plant fell through the ``or 1.0`` guard at the payload sites and got
``npl = 1 MW``. Because the per-plant hourly series is stored as
``uint8 round(100 * mw / nameplate)`` **clipped at 250**
(:func:`render_calibration_html._b64`), a 1 MW denominator saturates every real
generation hour: the blob collapses to ``{0, 250}`` and the loading profile
inside committed hours is gone. ``c_ann`` and every annual gate stayed correct,
so nothing failed — the corruption was invisible to the rubric and wrong only for
consumers that reconstruct hourly/monthly actuals from the blob (D-1 diurnal
shape, D-2 forced share, and any probe reading ``bench.plants[*].campd``).

Measured at the fix, across every committed bench part: 24.17 TWh of plant-years
stranded in four ISOs (PJM 9.87 + 3.26 + 0.32, MISO 2.77 + 1.79 + 1.60,
NEISO 1.66 + 1.34 + 1.27, CAISO 0.29), all of it recovered by the union.

Two guards, both hermetic (no data tree, no LP):

1. **Structural** — the lookup reads BOTH vintages, and the retiree pass cannot
   overwrite an operable nameplate.
2. **Behavioural** — a plant present only in the retiree vintage resolves to its
   real nameplate rather than falling through to the 1 MW default, and the
   ``_b64`` saturation that makes the defect silent is itself pinned so a future
   codec change cannot quietly reintroduce it.
"""

from __future__ import annotations

import ast
import base64

import numpy as np
import pytest

from tests.helpers import REPO_ROOT

RENDERER = REPO_ROOT / "scripts/render_calibration_html.py"


def _lookup_fn() -> ast.FunctionDef:
    """The ``_eia860_plant_info`` AST node."""
    tree = ast.parse(RENDERER.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_eia860_plant_info":
            return node
    raise AssertionError("_eia860_plant_info not found in render_calibration_html")


def test_lookup_reads_both_eia860_vintages() -> None:
    """Both the operable and the within-window retiree parquet names are read."""
    src = ast.unparse(_lookup_fn())
    assert "EIA_860_PARQUET_NAME" in src, "operable vintage no longer read"
    assert "EIA_860_RETIRED_WINDOW_PARQUET_NAME" in src, (
        "the within-window retiree vintage is not read — a plant that retires "
        "mid-backcast will silently get npl = 1 MW and its hourly campd blob "
        "will be destroyed while every annual gate stays green (pjm-159)"
    )


def test_operable_wins_over_retiree_on_conflict() -> None:
    """The retiree vintage is read FIRST, so the operable pass overwrites it.

    Ordering is the whole correctness argument for the union being purely
    additive: every plant that already resolved keeps its operable nameplate, so
    no already-correct bench entry moves.
    """
    src = ast.unparse(_lookup_fn())
    i_ret = src.index("EIA_860_RETIRED_WINDOW_PARQUET_NAME")
    i_op = src.rindex("EIA_860_PARQUET_NAME")
    assert i_ret < i_op, (
        "the operable vintage must be read AFTER the retiree vintage so it wins "
        "on conflict; reversing the order would let a retiree row override a "
        "live plant's nameplate"
    )


def test_retiree_only_plant_resolves_to_real_nameplate(monkeypatch) -> None:
    """A plant only in the retiree vintage gets its real MW, not the 1 MW default.

    Both parquet reads are stubbed, so this exercises the union logic itself with
    no dependency on the committed data tree.
    """
    import pandas as pd

    import scripts.render_calibration_html as rch

    operable = pd.DataFrame(
        {
            "plant_id": [10, 10, 20],
            "plant_name": ["Live A", "Live A", "Live B"],
            "nameplate_capacity_mw": [100.0, 50.0, 700.0],
        }
    )
    retiree = pd.DataFrame(
        {
            # 99 exists ONLY here — the defect's population.
            "plant_id": [99, 99, 20],
            "plant_name": ["Retired C", "Retired C", "STALE NAME"],
            # 20 also appears here with a WRONG value: operable must win.
            "nameplate_capacity_mw": [1706.5, 306.0, 1.0],
        }
    )

    def fake_read_parquet(path, columns=None):
        return retiree if "retired_within_window" in str(path) else operable

    monkeypatch.setattr(rch.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(rch.Path, "exists", lambda self: True)
    rch._eia860_plant_info.cache_clear()
    try:
        npl, nm = rch._eia860_plant_info()
    finally:
        rch._eia860_plant_info.cache_clear()

    # The retiree-only plant is recovered, summed over its units.
    assert npl[99] == pytest.approx(2012.5)
    assert nm[99] == "Retired C"
    # Operable plants are untouched, and operable wins the 20 conflict.
    assert npl[10] == pytest.approx(150.0)
    assert npl[20] == pytest.approx(700.0)
    assert nm[20] == "Live B"


def test_b64_saturation_is_what_makes_the_defect_silent() -> None:
    """Pin the codec behaviour the defect exploited.

    ``_b64`` clips at 250, so a 1 MW denominator maps every hour above 2.5 MW to
    the same byte: the series becomes a run/no-run indicator, energy-exact after
    the consumer's ``c_ann`` rescale but shape-flat inside committed hours. This
    is why no annual gate ever caught it. If a future codec change removes the
    clip (or the scale), this test fails and the reasoning above must be redone.
    """
    import scripts.render_calibration_html as rch

    mw = np.array([0.0, 1.0, 2.4, 2.6, 900.0, 1700.0])
    decoded = np.frombuffer(
        base64.b64decode(rch._b64(100.0 * mw / 1.0)), dtype=np.uint8
    )[: mw.size]
    assert decoded.tolist() == [0, 100, 240, 250, 250, 250], (
        "the 250 clip is the mechanism that collapses a mis-denominated series "
        "to a binary run indicator"
    )
    # With the CORRECT denominator the same hours stay distinguishable.
    ok = np.frombuffer(base64.b64decode(rch._b64(100.0 * mw / 1706.5)), dtype=np.uint8)[
        : mw.size
    ]
    assert len(set(ok.tolist())) > 2 and ok.max() < 250
