"""PJM nuclear-phantom decomposition (no-LP, measured) — does the fleet-month
nuclear CF smear hide a material CAMPD-blind availability phantom in the C3c
summer scarcity hours?

Context (pjm-nuc-1 charter): the pjm-113 keeper's C3c-2025 summer tail residual
was disclosed as congestion-surface-bound plus ~1.7 GW of frozen-constant-
invisible coal partial derates (docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md
§8.1) — both measured in the CAMPD-covered fossil fleet. This probe measures a
THIRD candidate the CAMPD-only decomposition is blind to by construction: PJM
nuclear (33.5 GW / 32 units) runs on a fleet-wide MONTHLY CF smear
(constants.NUCLEAR_MONTHLY_CF_BY_YEAR, EIA-923-derived) that cannot see a
unit-specific refuel/trip inside a scarcity hour. ERCOT fixed exactly this
with a per-reactor daily overlay (``ercot_nuclear_unit_availability``); this
probe decides whether PJM needs the analogue.

Everything is computed from committed artifacts + raw measured data only (no
solve, no config flip — rule 1 diagnostic-first):

  * model side: EXACT reconstruction, not payload decode — nuclear is flat
    must-run (fleet.py: floor == availability cap == pmax x monthly CF), so
    model nuclear(t) = fleet_pmax x NUCLEAR_MONTHLY_CF_BY_YEAR[PJM][yr][month],
    with the dormant Crane/TMI-1 unit (NUCLEAR_DORMANT_UNTIL) zeroed. Nuclear
    plants are NOT in the dashboard payload's per-plant dict (that dict is
    CAMPD fossil only), so the reconstruction is validated instead against the
    payload's own fuelRows annual nuclear TWh (asserted to < 0.05 TWh).
  * actual side: EIA-930 PJM nuclear hourly net generation via the canonical
    ``load_eia_hourly_benchmark`` (the exact series the payload's nuclear
    fuelRow r/nrmse is scored against — local-clock hour-of-year, the model's
    time index). Nuclear is a price-taker, so realized ~= available; CEMS
    cannot see nuclear, hence EIA-930 is the measurement basis.
  * cross-checks: the long-format ``data/raw/PJM_fueltype.parquet`` (UTC)
    converted to EPT (clock-convention robustness), and the EIA-923
    plant-month envelope (per-reactor attribution of monthly dips).

PRIMARY MEASUREMENT: mean(model_nuclear − EIA-930_nuclear) over the 22 actual
summer 2025 DA-tail hours (DA > $200, Jun/Jul — the Jun 23-25 and Jul 28-29
heat events, reproduced from the same arithmetic as
``_pjm_c3c_summer_tail_decomp.py`` and asserted to count exactly 22).

PRE-DECLARED STOP CONDITION (set before measurement, rule 1): if the mean
phantom is < ~400 MW (~one small reactor), the nuclear phantom is not the
lever — no overlay, no flag, no solve; the null result is written into the
diagnosis §8 and the coal/congestion story stands unchanged.

Sections (run all by default, or --section <name>):

  tail       reproduce the 22 summer-2025 DA-tail hours (assert count == 22).
  phantom    PRIMARY: model-minus-EIA-930 nuclear MW in the tail hours, per
             year, with per-event breakout and whole-month context.
  clock      robustness: same measurement with actuals read from the
             long-format PJM_fueltype.parquet on the UTC clock and shifted
             to EPT.
  plants923  attribution: EIA-923 plant-month nuclear CF for the event months
             (which reactors were down at monthly grain, i.e. what a
             per-reactor overlay could ever re-time).

Usage: .venv/bin/python scripts/probes/_pjm_nuclear_phantom_decomp.py
           [--run-id 2026-07-16-pjm-113-short-only] [--section NAME]

Findings doc: docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §8.2 (null result).
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.WARNING)

from market_sim.config.constants import (  # noqa: E402
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia_loader import load_eia_hourly_benchmark  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

RUNS_DIR = REPO / "frontend/data/backcast/runs"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
E930_LONG = REPO / "data/raw/PJM_fueltype.parquet"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"

HOURS = 8760
_MDAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)
TAIL_THR = 200.0
YEARS = (2023, 2024, 2025)
# Pre-declared materiality threshold (~one small reactor); set in the pjm-nuc-1
# charter BEFORE the measurement was run — never moved after seeing the result.
STOP_MW = 400.0


def load_payload(run_id: str) -> dict:
    raw = (RUNS_DIR / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def actual_da(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL_LMP)
    a = a[a.year == year].sort_values("hour")
    return a["da"].to_numpy()[:HOURS]


def summer_tail(year: int) -> np.ndarray:
    """Boolean mask of the actual summer DA-tail hours (same arithmetic as
    ``_pjm_c3c_summer_tail_decomp.py``: DA > $200 in months 6-9)."""
    return (actual_da(year) > TAIL_THR) & np.isin(MONTH, (6, 7, 8, 9))


def model_nuclear(year: int, pay: dict) -> tuple[np.ndarray, float]:
    """Exact model nuclear hourly MW + the active fleet pmax it derives from.

    Nuclear is flat must-run: fleet.py builds min_gen == availability cap ==
    pmax x NUCLEAR_MONTHLY_CF_BY_YEAR[PJM][year][month] (from_actual=True, so
    no EFORD layering), with dormant units (NUCLEAR_DORMANT_UNTIL) zeroed in
    backcast years. The LP therefore dispatches every nuclear unit at exactly
    that bound in every hour. Validated against the committed payload's own
    fuelRows annual nuclear TWh (assert < 0.05 TWh).
    """
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    pmax = sum(
        g.pmax_mw
        for g in gens
        if g.fuel_type == "nuclear"
        and year >= NUCLEAR_DORMANT_UNTIL.get(int(g.plant_code), 0)
    )
    cf = np.asarray(NUCLEAR_MONTHLY_CF_BY_YEAR["PJM"][year], dtype=float)
    series = pmax * cf[MONTH - 1]
    fr = {f["fuel"]: f for f in pay["years"][str(year)]["fuelRows"]}
    recon_twh = series.sum() / 1e6
    assert abs(recon_twh - fr["nuclear"]["m"]) < 0.05, (
        f"{year}: reconstructed {recon_twh:.2f} TWh != payload "
        f"{fr['nuclear']['m']} TWh — reconstruction basis broke"
    )
    return series, pmax


def actual_nuclear_930(year: int) -> np.ndarray:
    """EIA-930 PJM nuclear hourly MW on the model's local-clock hour-of-year
    (the exact series the payload's nuclear fuelRow is scored against)."""
    bench = load_eia_hourly_benchmark("PJM", year)
    return np.asarray(bench["nuclear"], dtype=float)[:HOURS]


# ------------------------------------------------------------------ tail
def sec_tail(pay: dict) -> None:
    for year in YEARS:
        tail = summer_tail(year)
        by_mon = {
            int(m): int(c) for m, c in zip(*np.unique(MONTH[tail], return_counts=True))
        }
        print(
            f"=== {year}: {tail.sum()} actual summer DA>${TAIL_THR:.0f} hours {by_mon}"
        )
    n25 = int(summer_tail(2025).sum())
    assert n25 == 22, f"2025 summer tail reproduced {n25} hours, expected 22"
    idx = pd.date_range("2025-01-01", periods=HOURS, freq="h")
    da = actual_da(2025)
    print(
        "  2025 roster:",
        ", ".join(
            f"{idx[h].strftime('%m-%d %H')}h(${da[h]:.0f})"
            for h in np.where(summer_tail(2025))[0]
        ),
    )


# ---------------------------------------------------------------- phantom
def sec_phantom(pay: dict) -> None:
    d25: np.ndarray | None = None
    for year in YEARS:
        tail = summer_tail(year)
        model, pmax = model_nuclear(year, pay)
        act = actual_nuclear_930(year)
        d = model - act
        if year == 2025:
            d25 = d[tail]
        print(
            f"=== {year}: active fleet {pmax:.0f} MW | recon annual "
            f"{model.sum() / 1e6:.2f} TWh == payload | EIA-930 annual {act.sum() / 1e6:.2f} TWh"
        )
        if tail.any():
            print(
                f"  PHANTOM over {tail.sum()} summer tail hours: mean {d[tail].mean():+.0f} MW | "
                f"min {d[tail].min():+.0f} / max {d[tail].max():+.0f} | "
                f"model {model[tail].mean():.0f} vs actual {act[tail].mean():.0f}"
            )
        for m in (6, 7):
            mm = MONTH == m
            print(
                f"  month {m}: model flat {model[mm].mean():.0f} | actual mean {act[mm].mean():.0f} "
                f"p10 {np.percentile(act[mm], 10):.0f} min {act[mm].min():.0f} "
                f"(month-mean phantom {d[mm].mean():+.0f} MW)"
            )
        if year == 2025:
            idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
            for lbl, lo, hi in (
                ("Jun 23-25 event", "2025-06-23", "2025-06-26"),
                ("Jul 28-29 event", "2025-07-28", "2025-07-30"),
            ):
                ev = tail & (idx >= lo) & (idx < hi)
                if ev.any():
                    print(
                        f"    {lbl}: {ev.sum()} tail hours, phantom mean {d[ev].mean():+.0f} MW "
                        f"(actual nuclear mean {act[ev].mean():.0f})"
                    )
    assert d25 is not None
    verdict = (
        "MATERIAL — proceed to overlay design"
        if d25.mean() >= STOP_MW
        else (
            "NULL — below the pre-declared ~400 MW stop threshold; no overlay, no solve"
        )
    )
    print(
        f"\n  VERDICT (pre-declared stop at {STOP_MW:.0f} MW): mean {d25.mean():+.0f} MW -> {verdict}"
    )


# ------------------------------------------------------------------ clock
def sec_clock(pay: dict) -> None:
    """Robustness: repeat the 2025 measurement from the long-format UTC feed."""
    df = pd.read_parquet(E930_LONG)
    nuc = df[df.fueltype == "NUC"].copy()
    ept = nuc.period.dt.tz_convert("America/New_York").dt.tz_localize(None)
    nuc = nuc[(ept.dt.year == 2025) & ~((ept.dt.month == 2) & (ept.dt.day == 29))]
    base = pd.Timestamp("2025-01-01")
    hoy = ((pd.DatetimeIndex(ept[nuc.index]) - base).total_seconds() // 3600).astype(
        int
    )
    act = np.full(HOURS, np.nan)
    ok = (hoy >= 0) & (hoy < HOURS)
    act[hoy[ok]] = nuc.value_mwh.to_numpy()[ok]
    tail = summer_tail(2025)
    model, _ = model_nuclear(2025, pay)
    d = (model - act)[tail]
    print(
        f"=== 2025 clock cross-check (PJM_fueltype.parquet, UTC->EPT): phantom mean "
        f"{np.nanmean(d):+.0f} MW over {tail.sum()} tail hours "
        f"({np.isnan(d).sum()} uncovered) — vs the canonical-loader number in `phantom`"
    )


# -------------------------------------------------------------- plants923
def sec_plants923(pay: dict) -> None:
    """Per-reactor monthly attribution: what a unit overlay could ever re-time."""
    df = pd.read_parquet(E923)
    mcols = {6: "netgen_june_mwh", 7: "netgen_july_mwh"}
    for year in YEARS:
        tail = summer_tail(year)
        if not tail.any():
            continue
        nuc = df[
            (df.year == year)
            & (df.fuel_type.str.contains("NUC", na=False))
            & (df.ba_code == "PJM")
        ]
        byp = nuc.groupby(["plant_id", "plant_name"])[list(mcols.values())].sum()
        cfg = get_iso_config("PJM")
        pmax_by_plant: dict[int, float] = {}
        for g in load_fleet_from_csv("PJM", cfg, year=year):
            if g.fuel_type == "nuclear":
                pmax_by_plant[int(g.plant_code)] = (
                    pmax_by_plant.get(int(g.plant_code), 0.0) + g.pmax_mw
                )
        print(
            f"=== {year} EIA-923 plant-month nuclear CF, event months (plants with a dip < 0.90):"
        )
        for (pid, name), r in byp.iterrows():
            cap = pmax_by_plant.get(int(pid))
            if not cap:
                continue
            cfs = {m: r[c] / (cap * (MONTH == m).sum()) for m, c in mcols.items()}
            if min(cfs.values()) < 0.90:
                print(
                    f"    {int(pid):>5d} {name[:24]:24s} {cap:5.0f} MW  "
                    + "  ".join(f"m{m} CF {v:.2f}" for m, v in cfs.items())
                )
        print(
            "    (monthly grain: a refuel/trip inside an event shows here only if it "
            "moves the plant's whole-month energy; intra-month timing needs NRC/ecomax — "
            "moot under a null primary measurement)"
        )


SECTIONS = {
    "tail": sec_tail,
    "phantom": sec_phantom,
    "clock": sec_clock,
    "plants923": sec_plants923,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-id", default="2026-07-16-pjm-113-short-only")
    ap.add_argument("--section", choices=sorted(SECTIONS), default=None)
    args = ap.parse_args()
    pay = load_payload(args.run_id)
    for name, fn in SECTIONS.items():
        if args.section and name != args.section:
            continue
        print(f"\n########## {name} ##########")
        fn(pay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
