"""miso-109 evidence probe: the EIA-930 ``NG: WAT`` hydro LEVEL pin at MISO.

Reproduces every number the miso-109 level fix rests on, from committed raw
inputs only (no solve, no bundle). Six sections:

  §1 fuel columns      — which ``NG: <CODE>`` columns each BA's extract carries,
                         i.e. whether pumped storage has its own column at all.
  §2 nameplate breach  — hours the BA's ``NG: WAT`` exceeds its OWN conventional
                         (prime mover ``HY``) nameplate, plus the count of
                         negative hours. Conventional hydro cannot exceed its
                         nameplate, and a series that nets pumping would go
                         negative; neither holds for MISO.
  §3 level gap         — 930 ``NG: WAT`` (what the keeper pins the level to)
                         against 923 ``HY`` (what the LP units actually are),
                         GATED ON PLANT COVERAGE so an early-release filing is
                         never differenced against a full one (the 2025 trap:
                         MISO files 14 HY plants for 2025 against 165 for
                         2023/24, which reads as a -90% collapse in generation).
  §4 reconciliation    — is a 930->923 scale factor identifiable? (It is not:
                         MISO's conventional share drifts 0.99 -> 0.84 across
                         2019-2024, and the monthly gap changes sign by month.)
  §5 diurnal           — the shape signature of the contamination.
  §6 inertness         — whether ``hydro_budget_nameplate_aware`` does anything
                         once the level is corrected.

Usage:
    python scripts/probes/_miso109_hydro_level_audit.py [--iso MISO ...]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia930.envelopes import measured_monthly_hydro  # noqa: E402
from market_sim.data.eia930.frames import (  # noqa: E402
    _ISO_TO_HOURLY_BA,
    _eia_hourly_frame_filled,
)
from market_sim.data.fleet import ISO_TO_BA_CODE  # noqa: E402
from market_sim.data.hydro import (  # noqa: E402
    _load_hydro_nameplate,
    load_hydro_budget,
)

YEARS = range(2019, 2026)


def _hy_by_plant(gen: pd.DataFrame, mcols: list[str], ba: str, year: int):
    """Return the ``(plant_id -> 12 monthly MWh)`` EIA-923 ``HY`` frame."""
    sub = gen[
        (gen["year"] == year) & (gen["ba_code"] == ba) & (gen["prime_mover"] == "HY")
    ]
    return sub.groupby("plant_id")[mcols].sum()


def section_1_fuel_columns(isos: list[str]) -> None:
    print("\n== §1 EIA-930 per-fuel columns (is there an NG: PS column?) ==")
    for iso in isos:
        frame = _eia_hourly_frame_filled(_ISO_TO_HOURLY_BA.get(iso, iso), 2024)
        if frame is None:
            print(f"  {iso:6s} no extract")
            continue
        cols = [c for c in frame.columns if c.startswith("NG:")]
        print(f"  {iso:6s} {' '.join(cols)}   NG: PS present = {'NG: PS' in cols}")


def section_2_nameplate_breach(isos: list[str]) -> None:
    print("\n== §2 does NG: WAT breach the BA's own conventional-hydro nameplate? ==")
    for iso in isos:
        np_mw = sum(_load_hydro_nameplate(iso).values())
        print(f"  -- {iso}: conventional (HY) EIA-860 nameplate {np_mw:,.1f} MW")
        for year in YEARS:
            frame = _eia_hourly_frame_filled(_ISO_TO_HOURLY_BA.get(iso, iso), year)
            if frame is None or "NG: WAT" not in frame.columns:
                continue
            wat = pd.to_numeric(frame["NG: WAT"], errors="coerce").to_numpy()
            wat = wat[~np.isnan(wat)]
            if not wat.size:
                continue
            over = wat > np_mw
            print(
                f"     {year}: max {wat.max():7,.0f} MW "
                f"(+{wat.max() - np_mw:7,.0f} over nameplate) | "
                f"{int(over.sum()):4d} h above ({over.mean() * 100:4.1f}%) | "
                f"{np.clip(wat - np_mw, 0, None).sum() / 1e6:.3f} TWh above | "
                f"negative hours {int((wat < 0).sum())}"
            )


def _modal_census(gen: pd.DataFrame, mcols: list[str], ba: str) -> int:
    """Return the modal EIA-923 ``HY`` plant census, the early-release gate.

    A filing carrying materially fewer plants than the ISO's usual census is a
    monthly early release covering only the large reporters; differencing it
    against a complete year measures SOURCE COVERAGE, not hydrology.
    """
    counts = [_hy_by_plant(gen, mcols, ba, y).shape[0] for y in YEARS]
    return int(np.median([c for c in counts if c]))


def section_3_level_gap(isos: list[str]) -> None:
    print("\n== §3 930 NG: WAT (pinned level) vs 923 HY (the LP units) ==")
    print("   coverage-gated: a year whose HY plant count is a small fraction of")
    print("   the modal census is an EARLY RELEASE and is NOT differenced.")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    for iso in isos:
        ba = ISO_TO_BA_CODE[iso]
        modal = _modal_census(gen, mcols, ba)
        print(f"  -- {iso}: modal HY plant census {modal}")
        for year in YEARS:
            hy = _hy_by_plant(gen, mcols, ba, year)
            n = hy.shape[0]
            hy_twh = np.nan_to_num(hy.to_numpy(dtype=float)).sum() / 1e6
            wat = measured_monthly_hydro(iso, year)
            wat_twh = float("nan") if wat is None else wat.sum() / 1e6
            complete = n >= 0.8 * modal
            gap = (
                f"{wat_twh - hy_twh:+7.3f} TWh ({(wat_twh / hy_twh - 1) * 100:+6.1f}%)"
                if complete and hy_twh > 0 and wat_twh == wat_twh
                else "  EARLY RELEASE — not differenced"
            )
            print(
                f"     {year}: 923 HY {hy_twh:7.3f} TWh over {n:4d} plants "
                f"({'complete' if complete else 'PARTIAL '}) | "
                f"930 WAT {wat_twh:7.3f} TWh | gap {gap}"
            )


def section_4_reconciliation(isos: list[str]) -> None:
    print("\n== §4 is a 930->923 reconciliation constant identifiable? ==")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    for iso in isos:
        ba = ISO_TO_BA_CODE[iso]
        shares, rows = [], []
        for year in YEARS:
            hy = _hy_by_plant(gen, mcols, ba, year)
            if hy.shape[0] < 0.8 * _modal_census(gen, mcols, ba):
                continue  # early release — never differenced
            monthly = np.nan_to_num(hy.to_numpy(dtype=float)).sum(axis=0)
            wat = measured_monthly_hydro(iso, year)
            if wat is None or monthly.sum() <= 0:
                continue
            shares.append(monthly.sum() / wat.sum())
            rows.append((year, (wat - monthly) / 1e3))
        if shares:
            print(
                f"  {iso}: conventional share of NG: WAT by year "
                f"{[f'{s:.4f}' for s in shares]} | spread "
                f"{max(shares) - min(shares):.4f}"
            )
        for year, gap in rows:
            print(
                f"     {year} monthly gap GWh: "
                + " ".join(f"{g:6.0f}" for g in gap)
                + f"  (sign changes: {int((np.sign(gap[:-1]) != np.sign(gap[1:])).sum())})"
            )


def section_5_diurnal(isos: list[str]) -> None:
    print("\n== §5 diurnal signature of NG: WAT (model-clock hour of day) ==")
    for iso in isos:
        for year in (2023, 2024):
            frame = _eia_hourly_frame_filled(_ISO_TO_HOURLY_BA.get(iso, iso), year)
            if frame is None or "NG: WAT" not in frame.columns:
                continue
            wat = pd.to_numeric(frame["NG: WAT"], errors="coerce").to_numpy()
            hod = np.arange(len(wat)) % 24
            prof = np.array([np.nanmean(wat[hod == h]) for h in range(24)])
            month = frame["Local date"].dt.month.to_numpy()
            month = np.nan_to_num(month, nan=0.0).astype(int)
            top = np.argsort(np.nan_to_num(wat, nan=-1.0))[-200:]
            print(
                f"  {iso} {year}: overnight floor {prof[:4].mean():,.0f} MW -> "
                f"peak {prof.max():,.0f} MW at HE{int(prof.argmax()) + 1} "
                f"(swing {prof.max() / prof[:4].mean():.2f}x); top-200 hours "
                f"months {np.bincount(month[top], minlength=13)[1:].tolist()}"
            )


def section_6_inertness() -> None:
    """Does ``hydro_budget_nameplate_aware`` do anything once the level is right?

    Both arms go through :func:`load_hydro_budget` rather than
    :func:`build_hydro_fleet`, because the fix lives in the latter: at HEAD the
    fleet builder REFUSES the pin for MISO, so it can no longer reproduce the
    pre-fix (contaminated) arm. Passing ``monthly_target_mwh`` here reconstructs
    exactly what the keeper ran, which is what makes the contrast measurable
    after the fix has landed.
    """
    print("\n== §6 hydro_budget_nameplate_aware on the corrected vs pinned level ==")
    for year in (2023, 2024, 2025):
        for label, target in (
            ("CORRECTED (923 HY, no pin)", None),
            ("PRE-FIX   (930 NG: WAT pin)", measured_monthly_hydro("MISO", year)),
        ):
            a = load_hydro_budget(
                "MISO",
                year,
                backfill_year=2024,
                monthly_target_mwh=target,
                nameplate_aware_target=False,
            ).monthly_energy
            b = load_hydro_budget(
                "MISO",
                year,
                backfill_year=2024,
                monthly_target_mwh=target,
                nameplate_aware_target=True,
            ).monthly_energy
            print(
                f"  {year} {label}: level {a.sum() / 1e6:7.4f} TWh | "
                f"nameplate-aware identical = {np.array_equal(a, b)} "
                f"(L1 {np.abs(a - b).sum() / 1e3:8.3f} GWh)"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=["MISO", "PJM", "NYISO", "NEISO"])
    args = ap.parse_args()
    logging.disable(logging.WARNING)
    section_1_fuel_columns(args.iso)
    section_2_nameplate_breach(args.iso)
    section_3_level_gap(args.iso)
    section_4_reconciliation(args.iso)
    section_5_diurnal(args.iso)
    if "MISO" in args.iso:
        section_6_inertness()


if __name__ == "__main__":
    main()
