"""nyiso-98: NYISO nuclear unit-availability — benchmark audit + provenance gate.

Matrix §5.5 item 7 (`nuclear_unit_availability`, NYISO derivation). No LP: this
is the build-time instrument for the pre-registered gate in
``docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md``, run BEFORE any
solve, in the shape the PJM precedent requires (pjm-nuc-1b,
``docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md`` §8.2.1: that lane's overlay
was fully built and then STOPPED at its build-time provenance gate).

Sections
--------
``census``
    NRC daily Power Reactor Status coverage of the four NYISO reactors and the
    identifier crosswalk onto the model fleet.
``benchmark``
    Data quality of the SCORING TARGET, EIA-930 ``NYIS`` ``NG: NUC``. The lever
    queue's stated defect ("nuclear r_day drops 0.84 -> 0.50/0.51 in 2024-25")
    is measured against this series, so it is audited first. Contiguous blocks
    of hours reported as exactly 0.0 MW are falsified against NRC: a day is a
    GAP DAY when the series posts 0.0 MW in any hour while NRC shows at least
    one NY reactor at power. The fleet cannot produce 0 MW with a reactor
    online, so a gap day carries no information about dispatch timing.
``baseline``
    The model's fleet-month smear (``NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']`` x
    fleet pmax, flat within a month) scored against the target both raw and
    gap-masked. Nuclear is a flat must-run price-taker, so the model's nuclear
    dispatch IS pmax x availability and needs no solve to reconstruct.
``source``
    GATE G1 — the RAW NRC daily series (``avail_raw``, no reconciliation)
    scored the same way. Tests whether the source carries daily timing content
    the smear does not.
``overlay``
    GATE G2/G3 — the RECONCILED series (``avail``, EIA-923 monthly anchor) on
    the same scoring. G2 is the PJM failure mode: does the level reconciliation
    eat the timing signal it is layered on? G3 is level neutrality.

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso98_nuclear_availability_provenance.py
    PYTHONPATH=.:src python scripts/probes/nyiso98_nuclear_availability_provenance.py \
        --sections census benchmark baseline
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ISO = "NYISO"
BA = "NYIS"
YEARS = (2023, 2024, 2025)
NRC_DIR = REPO / "data" / "raw" / "nrc-reactor-status"
# NRC report unit names for the NYISO fleet. Indian Point 2/3 retired
# 2020/2021 and carry no rows in the 2023-2025 reports.
NY_REACTORS = ("FitzPatrick", "Ginna", "Nine Mile Point 1", "Nine Mile Point 2")


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, 0.0 when either side is constant (no shape to correlate)."""
    if a.std() <= 0.0 or b.std() <= 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def fleet_caps() -> dict[tuple[int, int], float]:
    """EIA-860 pmax per (plant_code, unit_no) for the NYISO nuclear fleet."""
    import logging

    logging.disable(logging.WARNING)
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    caps: dict[tuple[int, int], float] = {}
    for g in load_fleet_from_csv(ISO, get_iso_config(ISO), year=YEARS[-1]):
        if g.fuel_type != "nuclear":
            continue
        tail = str(g.unit_id).rsplit("_", 1)[-1]
        if tail.isdigit():
            caps[(int(g.plant_code), int(tail))] = float(g.pmax_mw)
    return caps


def nrc_daily(year: int) -> pd.DataFrame:
    """Per (reactor, date) NRC percent-of-licensed-thermal-power for ``year``."""
    df = pd.read_csv(
        NRC_DIR / f"{year}PowerStatus.txt", sep="|", encoding="utf-8-sig"
    )
    df["date"] = pd.to_datetime(
        df["ReportDt"], format="%m/%d/%Y %I:%M:%S %p"
    ).dt.normalize()
    df = df[(df.date.dt.year == year) & df["Unit"].isin(NY_REACTORS)]
    return df.drop_duplicates(["Unit", "date"], keep="last")


def measured_daily(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Measured daily nuclear GWh and the gap-day mask, on the 365-day clock.

    Returns ``(daily_gwh, is_gap_day)``. A gap day posts 0.0 MW in at least one
    hour; :func:`gap_falsification` verifies NRC contradicts every one of them.
    """
    from market_sim.data.eia930 import frames as fr

    frame = fr._eia_hourly_frame_filled(BA, year)
    if frame is None:
        raise RuntimeError(f"no EIA-930 frame for {BA} {year}")
    mw = np.nan_to_num(frame["NG: NUC"].to_numpy(float))[:8760].reshape(365, 24)
    return mw.sum(1) / 1e3, (mw == 0.0).any(1)


def gap_falsification(year: int) -> pd.DataFrame:
    """Per gap day, the maximum NRC reactor power across the NY fleet.

    A gap day whose NRC maximum is > 0 is falsified as a reporting artifact:
    a four-reactor fleet with one unit at power cannot meter 0 MW.
    """
    _, gap = measured_daily(year)
    piv = nrc_daily(year).pivot_table(
        index="date", columns="Unit", values="Power", aggfunc="last"
    )
    # 365-day model clock: real calendar dates with a leap Feb 29 dropped.
    dates = pd.DatetimeIndex(
        [d for d in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
         if not (d.month == 2 and d.day == 29)]
    )
    sub = piv.reindex(dates[gap])
    return pd.DataFrame({"nrc_max_power": sub.max(axis=1)})


def smear_daily(year: int, caps: dict[tuple[int, int], float]) -> np.ndarray:
    """Model daily nuclear GWh under the fleet-month CF smear.

    Nuclear is a flat must-run at ``pmax x availability`` with availability =
    the month's ``NUCLEAR_MONTHLY_CF_BY_YEAR`` value, so the model's daily
    nuclear energy is exact arithmetic — no solve needed.
    """
    from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR

    cf = np.asarray(NUCLEAR_MONTHLY_CF_BY_YEAR[ISO][year], float)
    fleet_mw = sum(caps.values())
    months = np.array(
        [d.month for d in pd.date_range(f"{2001}-01-01", periods=365, freq="D")]
    )
    return cf[months - 1] * fleet_mw * 24.0 / 1e3


def overlay_daily(
    day: pd.DataFrame, caps: dict[tuple[int, int], float], year: int, col: str
) -> np.ndarray:
    """Daily fleet GWh implied by a per-reactor availability column.

    Units/dates the extract does not cover fall back to the smear, exactly as
    :func:`market_sim.data.outages.nuclear_unit_availability_series` NaN
    semantics make the model do.
    """
    from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR

    cf = np.asarray(NUCLEAR_MONTHLY_CF_BY_YEAR[ISO][year], float)
    dates = pd.DatetimeIndex(
        [d for d in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
         if not (d.month == 2 and d.day == 29)]
    )
    pos = {d: i for i, d in enumerate(dates)}
    out = np.zeros(365)
    sub = day[day.date.dt.year == year]
    for key, cap in caps.items():
        # smear fallback for every day, overwritten where the extract covers
        avail = cf[np.array([d.month for d in dates]) - 1].copy()
        rows = sub[(sub.plant_code == key[0]) & (sub.unit_no == key[1])]
        for d, v in zip(rows.date, rows[col].to_numpy(float)):
            i = pos.get(d.normalize())
            if i is not None and np.isfinite(v):
                avail[i] = v
        out += avail * cap * 24.0 / 1e3
    return out


def _score(model: np.ndarray, actual: np.ndarray, gap: np.ndarray) -> dict:
    """r_day raw and gap-masked, plus the annual level, for one year."""
    ok = ~gap
    return {
        "r_day_raw": _r(model, actual),
        "r_day_clean": _r(model[ok], actual[ok]),
        "n_clean": int(ok.sum()),
        "twh": float(model.sum() / 1e3),
        "twh_act_clean": float(actual[ok].sum() / 1e3),
        "twh_mod_clean": float(model[ok].sum() / 1e3),
    }


def section_census() -> None:
    """NRC coverage of the NYISO fleet and the identifier crosswalk."""
    caps = fleet_caps()
    print("\n=== census — NYISO nuclear fleet vs NRC daily status ===")
    print(f"model fleet: {len(caps)} units, {sum(caps.values()):,.1f} MW")
    for k, v in sorted(caps.items()):
        print(f"    plant {k[0]} unit {k[1]}: {v:,.1f} MW")
    for year in YEARS:
        d = nrc_daily(year)
        n = d.groupby("Unit")["date"].nunique().to_dict()
        cal = 366 if year % 4 == 0 else 365
        print(f"  {year}: {len(n)} reactors; days/reactor {n} (calendar {cal})")


def section_benchmark() -> None:
    """Audit the scoring target: EIA-930 NG:NUC reporting gaps, falsified."""
    print("\n=== benchmark — EIA-930 NYIS 'NG: NUC' data quality ===")
    print("(a gap day posts 0.0 MW in >=1 hour; NRC max power falsifies it)")
    for year in YEARS:
        act, gap = measured_daily(year)
        fals = gap_falsification(year)
        unfalsified = int((fals["nrc_max_power"].fillna(0) == 0).sum())
        print(
            f"  {year}: gap days {int(gap.sum()):>3}/365  "
            f"(measured TWh all {act.sum() / 1e3:5.2f}, "
            f"gap-clean-day mean {act[~gap].mean():5.1f} GWh)  "
            f"NRC min-of-max power on gap days "
            f"{fals['nrc_max_power'].min():.0f} %  "
            f"unfalsified gap days: {unfalsified}"
        )


def section_baseline(caps: dict[tuple[int, int], float]) -> dict:
    """The model's fleet-month smear scored against the audited target."""
    print("\n=== baseline — fleet-month CF smear (the current model) ===")
    print(f"{'year':<6}{'r_day raw':>11}{'r_day CLEAN':>13}{'n_clean':>9}"
          f"{'modTWh':>9}{'actTWh(clean)':>15}")
    out = {}
    for year in YEARS:
        act, gap = measured_daily(year)
        s = _score(smear_daily(year, caps), act, gap)
        out[year] = s
        print(
            f"{year:<6}{s['r_day_raw']:>11.3f}{s['r_day_clean']:>13.3f}"
            f"{s['n_clean']:>9}{s['twh']:>9.2f}{s['twh_act_clean']:>15.2f}"
        )
    print(
        f"  3-yr mean r_day: raw {np.mean([s['r_day_raw'] for s in out.values()]):.3f}"
        f"  CLEAN {np.mean([s['r_day_clean'] for s in out.values()]):.3f}"
    )
    return out


def _arm(caps: dict, col: str, label: str, base: dict) -> dict:
    """Score one availability column (raw NRC or reconciled) vs the baseline."""
    from scripts.data.derive_nuclear_availability import (
        load_daily_raw,
        reconcile_monthly,
    )

    day = load_daily_raw(ISO)
    if col == "avail":
        day = reconcile_monthly(day, ISO)
    print(f"\n=== {label} ===")
    print(f"{'year':<6}{'r_day raw':>11}{'r_day CLEAN':>13}{'d vs smear':>12}"
          f"{'modTWh':>9}{'dTWh %':>9}")
    out = {}
    for year in YEARS:
        act, gap = measured_daily(year)
        s = _score(overlay_daily(day, caps, year, col), act, gap)
        out[year] = s
        d = s["r_day_clean"] - base[year]["r_day_clean"]
        dtwh = 100.0 * (s["twh"] / base[year]["twh"] - 1.0)
        print(
            f"{year:<6}{s['r_day_raw']:>11.3f}{s['r_day_clean']:>13.3f}"
            f"{d:>+12.3f}{s['twh']:>9.2f}{dtwh:>+9.2f}"
        )
    lift = np.mean(
        [out[y]["r_day_clean"] - base[y]["r_day_clean"] for y in YEARS]
    )
    print(f"  3-yr mean CLEAN r_day lift vs smear: {lift:+.3f}")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the requested probe sections."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--sections",
        nargs="+",
        default=["census", "benchmark", "baseline", "source", "overlay"],
    )
    args = ap.parse_args(argv)
    caps = fleet_caps()
    base: dict = {}
    if "census" in args.sections:
        section_census()
    if "benchmark" in args.sections:
        section_benchmark()
    if "baseline" in args.sections or {"source", "overlay"} & set(args.sections):
        base = section_baseline(caps)
    raw = rec = None
    if "source" in args.sections:
        raw = _arm(caps, "avail_raw", "source (GATE G1) — RAW NRC daily", base)
    if "overlay" in args.sections:
        rec = _arm(
            caps, "avail", "overlay (GATE G2/G3) — RECONCILED (923 anchor)", base
        )
    if raw and rec:
        lr = np.mean([raw[y]["r_day_clean"] - base[y]["r_day_clean"] for y in YEARS])
        lc = np.mean([rec[y]["r_day_clean"] - base[y]["r_day_clean"] for y in YEARS])
        print("\n=== GATE SUMMARY ===")
        print(f"  G1 raw-source lift        {lr:+.3f}  (gate: >= +0.10, no year regresses)")
        print(f"  G2 reconciled lift        {lc:+.3f}  "
              f"(retention {100.0 * lc / lr if lr else float('nan'):.0f} % of raw; gate: >= 70 %)")
        worst = min(rec[y]["r_day_clean"] - base[y]["r_day_clean"] for y in YEARS)
        print(f"  G2 worst per-year delta   {worst:+.3f}  (gate: > 0 in every year)")
        dl = max(abs(100.0 * (rec[y]["twh"] / base[y]["twh"] - 1.0)) for y in YEARS)
        print(f"  G3 max |annual dTWh|      {dl:.2f} %   (gate: < 0.5 %)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
