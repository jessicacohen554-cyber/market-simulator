#!/usr/bin/env python
"""miso-110 §A-§D: measure the FORWARD hydro-level defect at a PS-folding BA.

miso-109 fixed the BACKCAST level for BAs in
``constants.EIA930_PS_FOLDED_INTO_WAT`` (EIA-930 ``NG: WAT`` is
conventional-hydro PLUS pumped-storage discharge at those BAs, so it is not an
admissible LEVEL for a conventional-hydro-only unit population). It deliberately
left the FORWARD analogue -- ``hydro.forecast_monthly_hydro`` ->
``eia930.climatological_monthly_hydro``, the multi-year mean of that same
contaminated series -- unfixed and merely WARNED about. This probe measures what
the corrected forward level is, before any code changes.

Sections::

  §A  EIA-923 ``HY`` plant census per year, per ISO -- the COVERAGE GATE. A
      filing carrying materially fewer plants than the ISO's modal census is a
      monthly early release; averaging it into a climatology would measure
      source coverage, not hydrology.
  §B  EIA-930 ``NG: WAT`` year availability per ISO -- which years actually
      enter the incumbent climatology (the 930 side's REALISED window).
  §C  THE TRAP, stated explicitly: the naive climatology-vs-climatology delta
      mixes the PS fold with a WINDOW MISMATCH (the two sides realise different
      year sets). Printed with both realised windows beside it, plus a
      window-matched comparison that isolates the fold, plus the CAISO control
      -- CAISO shows a large naive delta yet screens CLEAN on the
      three-signature PS test, which is the proof that a climatology gap is NOT
      evidence of a fold.
  §D  The candidate forward level: the coverage-gated EIA-923 ``HY``
      climatology, 12-vector, per registry ISO.

Run::

    PYTHONPATH=. uv run python scripts/probes/_miso110_forward_level_audit.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    EIA930_PS_FOLDED_INTO_WAT,
    HYDRO_CLIMATOLOGY_YEARS,
)
from market_sim.data.zone_assignment import _ISO_TO_BA_CODE as ISO_TO_BA_CODE
from market_sim.data.eia923 import (
    EIA923_LATEST_FINAL_VINTAGE,
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia930.envelopes import (
    climatological_monthly_hydro,
    measured_monthly_hydro,
)

ISOS: list[str] = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
# Widened past HYDRO_CLIMATOLOGY_YEARS so §A/§B can answer design decision 3
# (should the window extend?) from the source data rather than from a residual.
SCAN_YEARS: tuple[int, ...] = (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
HY = "HY"


def _hy_monthly(
    gen: pd.DataFrame, mcols: list[str], ba: str, year: int
) -> pd.DataFrame:
    """Return one row per EIA-923 ``HY`` plant with its twelve monthly columns.

    Mirrors ``data.hydro._load_hydro_generation``'s filter and clip so the
    census and totals here are the ones the LP budget itself would see.
    """
    sub = gen[
        (gen["prime_mover"] == HY) & (gen["year"] == year) & (gen["ba_code"] == ba)
    ]
    if sub.empty:
        return sub
    agg = sub.groupby("plant_id", as_index=False).agg({c: "sum" for c in mcols})
    agg[mcols] = agg[mcols].clip(lower=0.0)
    return agg[agg[mcols].sum(axis=1) > 0.0].reset_index(drop=True)


def section_a_census(gen: pd.DataFrame, mcols: list[str]) -> dict[str, dict[int, int]]:
    """Print, and return, the per-ISO per-year EIA-923 ``HY`` plant census."""
    print("\n== §A EIA-923 `HY` plant census per year (the COVERAGE GATE) ==")
    print("   a year whose census is far below the ISO's modal census is an")
    print("   EARLY RELEASE and must not enter a climatology mean.")
    out: dict[str, dict[int, int]] = {}
    for iso in ISOS:
        ba = ISO_TO_BA_CODE[iso]
        counts = {y: _hy_monthly(gen, mcols, ba, y).shape[0] for y in SCAN_YEARS}
        out[iso] = counts
        nz = [c for c in counts.values() if c]
        modal = int(np.median(nz)) if nz else 0
        cells = " ".join(
            f"{y}:{c:>4d}{'*' if c and c < 0.8 * modal else ' '}"
            for y, c in counts.items()
        )
        print(f"  -- {iso:6s} modal {modal:4d} | {cells}")
    print("   (* = below 0.8 x modal -> gated OUT as an early release)")
    print(f"   EIA923_LATEST_FINAL_VINTAGE = {EIA923_LATEST_FINAL_VINTAGE}")
    return out


def section_b_930_years(gen: pd.DataFrame, mcols: list[str]) -> None:
    """Print which years each ISO actually contributes to the 930 climatology."""
    print("\n== §B EIA-930 `NG: WAT` year availability (the 930 REALISED window) ==")
    print(f"   HYDRO_CLIMATOLOGY_YEARS = {HYDRO_CLIMATOLOGY_YEARS}")
    for iso in ISOS:
        have = [y for y in SCAN_YEARS if measured_monthly_hydro(iso, y) is not None]
        realised = [y for y in HYDRO_CLIMATOLOGY_YEARS if y in have]
        missing = [y for y in HYDRO_CLIMATOLOGY_YEARS if y not in have]
        print(
            f"  -- {iso:6s} extract years {have} | "
            f"realised climatology window {realised}"
            + (f" | MISSING {missing}" if missing else "")
        )


def _hy_climatology(
    gen: pd.DataFrame,
    mcols: list[str],
    iso: str,
    years: tuple[int, ...],
    census: dict[int, int],
) -> tuple[np.ndarray | None, list[int]]:
    """Return the coverage-gated EIA-923 ``HY`` climatology and its realised window."""
    ba = ISO_TO_BA_CODE[iso]
    nz = [c for c in census.values() if c]
    modal = int(np.median(nz)) if nz else 0
    rows: list[np.ndarray] = []
    used: list[int] = []
    for y in years:
        if y > EIA923_LATEST_FINAL_VINTAGE:
            continue
        n = census.get(y, 0)
        if not n or n < 0.8 * modal:
            continue
        hy = _hy_monthly(gen, mcols, ba, y)
        rows.append(hy[mcols].to_numpy(dtype=float).sum(axis=0))
        used.append(y)
    if not rows:
        return None, []
    return np.vstack(rows).mean(axis=0), used


def section_c_trap(
    gen: pd.DataFrame, mcols: list[str], census: dict[str, dict[int, int]]
) -> None:
    """The window-mismatch trap: never let a climatology delta stand for the fold."""
    print("\n== §C THE TRAP -- naive climatology delta != the PS fold ==")
    for iso in ISOS:
        c930 = climatological_monthly_hydro(iso, HYDRO_CLIMATOLOGY_YEARS)
        w930 = [
            y
            for y in HYDRO_CLIMATOLOGY_YEARS
            if measured_monthly_hydro(iso, y) is not None
        ]
        c923, w923 = _hy_climatology(
            gen, mcols, iso, HYDRO_CLIMATOLOGY_YEARS, census[iso]
        )
        if c930 is None or c923 is None:
            print(f"  -- {iso:6s} no climatology on one side (930={c930 is not None})")
            continue
        naive = (c930.sum() / c923.sum() - 1) * 100
        print(
            f"  -- {iso:6s} NAIVE  930 {c930.sum() / 1e6:6.3f} TWh over {w930} vs "
            f"923 {c923.sum() / 1e6:6.3f} TWh over {w923} -> {naive:+6.1f}% "
            "<< MIXES fold + WINDOW MISMATCH, not quotable as the fold"
        )
        # Window-matched: restrict BOTH sides to the years both realise. This
        # removes hydrology from the comparison; what is left is the fold.
        both = tuple(y for y in w930 if y in w923)
        if both:
            m930 = np.vstack([measured_monthly_hydro(iso, y) for y in both]).mean(
                axis=0
            )
            m923, _ = _hy_climatology(gen, mcols, iso, both, census[iso])
            matched = (m930.sum() / m923.sum() - 1) * 100
            print(
                f"     {'':6s} MATCHED window {list(both)}: 930 "
                f"{m930.sum() / 1e6:6.3f} vs 923 {m923.sum() / 1e6:6.3f} TWh "
                f"-> {matched:+6.1f}%   (per-year: "
                + ", ".join(
                    f"{y} {(measured_monthly_hydro(iso, y).sum() / _hy_monthly(gen, mcols, ISO_TO_BA_CODE[iso], y)[mcols].to_numpy(dtype=float).sum() - 1) * 100:+.1f}%"
                    for y in both
                )
                + ")"
            )


def section_d_candidate(
    gen: pd.DataFrame, mcols: list[str], census: dict[str, dict[int, int]]
) -> None:
    """Print the candidate forward level for every registry ISO."""
    print("\n== §D candidate FORWARD level: coverage-gated EIA-923 `HY` climatology ==")
    print(
        f"   registry EIA930_PS_FOLDED_INTO_WAT = {sorted(EIA930_PS_FOLDED_INTO_WAT)}"
    )
    for iso in sorted(EIA930_PS_FOLDED_INTO_WAT):
        c923, used = _hy_climatology(
            gen, mcols, iso, HYDRO_CLIMATOLOGY_YEARS, census[iso]
        )
        c930 = climatological_monthly_hydro(iso, HYDRO_CLIMATOLOGY_YEARS)
        if c923 is None:
            print(f"  -- {iso}: NO complete 923 filing in the window -> fallback path")
            continue
        print(
            f"  -- {iso}: realised 923 window {used}, total {c923.sum() / 1e6:.4f} TWh"
        )
        print("     month:   " + " ".join(f"{m:>7d}" for m in range(1, 13)))
        print("     923 GWh: " + " ".join(f"{v / 1e3:7.1f}" for v in c923))
        if c930 is not None:
            print("     930 GWh: " + " ".join(f"{v / 1e3:7.1f}" for v in c930))
            print(
                "     delta %: "
                + " ".join(f"{(a / b - 1) * 100:+7.1f}" for a, b in zip(c930, c923))
            )


def main() -> None:
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    census = section_a_census(gen, mcols)
    section_b_930_years(gen, mcols)
    section_c_trap(gen, mcols, census)
    section_d_candidate(gen, mcols, census)


if __name__ == "__main__":
    main()
