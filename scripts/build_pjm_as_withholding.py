"""Build PJM hourly ancillary-service (reserve-withholding) MW series.

For each requested year this writes
``data/raw/PJM-AS/pjm_<year>_as_up_mw.parquet`` — a single system-wide
hourly MW series of the reserve capacity PJM holds *out* of the energy market,
mirroring the ERCOT withholding layout (``ercot_<year>_as_up_mw.parquet``,
column ``as_up_mw``). The backcast's reserve-withholding probe
(``ScenarioConfig.as_reserve_withholding``) removes it from the gas/flexible-
thermal headroom before the energy supply curve clears (see
``fleet.generators_to_fleet_arrays``).

Withheld quantity — the **Primary Reserve requirement** (``as_req_mw`` for
``service == "PR"``, ``locale == "PJM_RTO"``). PJM clears three nested reserve
products — Synchronized (SR) ⊆ Primary (PR) ⊆ 30-Minute (30MIN) (Manual 11
sec 4.4.1) — and Primary is the binding upward 10-minute requirement that nests
Synchronized, so the Primary requirement is the capacity the market reserves
(holds out of energy) for the contingency. It is a reliability quantity
(≈ 1.5 × Largest Single Contingency, Manual 11 sec 4.3), ~3 GW RTO-wide. We
take the *requirement* (``as_req_mw``), not cleared ``total_mw``: cleared total
includes Tier-1 synchronized headroom on already-dispatched units that is *not*
withdrawn from energy (it is headroom that exists anyway), so the requirement is
the conservative, defensible "held out of energy" quantity.

Basis — Real-Time (``reserve_market_results_<year>.parquet``), aggregated
5-min → hourly (mean over the twelve intervals). The Day-Ahead market
(``da_reserve_market_results_<year>``) was considered as the basis for our
single-clearing (day-ahead-style) perfect-foresight model, mirroring the ERCOT
DAM-cleared precedent. Two findings drove the choice of RT:

  1. The Primary requirement is a *reliability* quantity (≈ 1.5 × LSC), not a
     market-condition price, so it is basis-independent to first order — the DA
     and RT PR requirements agree within ~3% every year (RT/DA means: 2023
     3094/3213, 2024 3422/3504, 2025 3348/3337 MW). The "DA-cleared model"
     concern is therefore moot for the *requirement*.
  2. The RT parquet has complete year coverage, whereas the DA parquet is
     truncated at year-end (the Dec-31 tail is missing, ~24 h gaps). RT is the
     cleaner, more complete series.

So RT is used for completeness; the conclusion is unchanged had we used DA.

Clock — the model's fixed non-leap 8760-hour clock keyed to PJM-local
(Eastern Prevailing) time, exactly as the ERCOT builder: Feb 29 of a leap year
is dropped, the repeated DST fall-back hour is averaged, and the spring-forward
gap is interpolated. The Primary requirement is a smooth, strictly-positive
reliability quantity that is never legitimately zero, so scattered gaps and the
one ~24 h data hole each year are interpolated (linear, both directions) rather
than zero-filled.

Source: PJM Data Miner 2 "Ancillary Services Market Results — Reserve Market
Results" (RT), data/raw/PJM-AS/reserve_market_results_<year>.parquet;
provenance for the curve/products in docs/multi-iso/pjm-reserve-curve-source.md.

Run:
    python scripts/build_pjm_as_withholding.py                 # 2023 2024 2025
    python scripts/build_pjm_as_withholding.py --year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HOURS_PER_YEAR = 8760
REPO_ROOT = Path(__file__).resolve().parents[1]
# W1 collapsed inputs/raw-data into data/raw (CLAUDE.md directory map); the
# source and output parquets both live under data/raw/PJM-AS.
AS_DIR = REPO_ROOT / "data" / "raw" / "PJM-AS"

DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Reserve zones (Manual 11 sec 4.2: the RTO Reserve Zone and its one Reserve
# Subzone, Mid-Atlantic/Dominion) and the binding upward product (Primary,
# which nests Synchronized — Manual 11 sec 4.4.1).
_LOCALE = "PJM_RTO"
_LOCALE_MAD = "MAD"  # Mid-Atlantic/Dominion reserve subzone
_PRIMARY = "PR"
_SYNCHRONIZED = "SR"  # carried as a reference column only

# A contiguous data hole longer than this (hours) is treated as missing
# coverage (a partial-year upload) and aborts the build rather than
# interpolating across a multi-day gap. The known holes are a 1-hour DST gap
# and one ~24-hour block per year — both well under this bound.
_MAX_GAP_HOURS = 72

# (month, day, hour) calendar of the fixed non-leap 8760-hour clock, shared by
# every model year (matches the ERCOT builder and the demand clock).
_CALENDAR = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
_FULL_INDEX = pd.MultiIndex.from_arrays(
    [_CALENDAR.month, _CALENDAR.day, _CALENDAR.hour],
    names=["month", "day", "hour"],
)


def _hourly_requirement(
    year: int, service: str, locale: str = _LOCALE
) -> tuple[np.ndarray, int]:
    """Hourly ``as_req_mw`` for ``service`` in ``locale`` on the non-leap clock.

    Reads the RT 5-minute reserve-market parquet, filters to the reserve
    zone (``locale``: RTO-wide ``PJM_RTO`` or the Mid-Atlantic/Dominion
    subzone ``MAD``) and ``service``, and averages each clock hour's twelve
    5-minute intervals. Feb-29 is dropped; the result is reindexed onto the
    fixed non-leap calendar and interpolated across the DST spring-forward gap
    and the one ~24-hour data hole (the requirement is never legitimately zero).

    Returns ``(series, n_missing)`` where ``n_missing`` is the count of clock
    hours that had no source data and were interpolated.
    """
    path = AS_DIR / f"reserve_market_results_{year}.parquet"
    df = pd.read_parquet(
        path, columns=["datetime_beginning_ept", "locale", "service", "as_req_mw"]
    )
    df = df[(df["locale"] == locale) & (df["service"] == service)].copy()
    dt = pd.to_datetime(
        df["datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    )
    keep = dt.notna() & ~((dt.dt.month == 2) & (dt.dt.day == 29))
    df, dt = df[keep], dt[keep]
    grouped = df.groupby([dt.dt.month, dt.dt.day, dt.dt.hour])["as_req_mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    aligned = grouped.reindex(_FULL_INDEX)

    isna = aligned.isna().to_numpy()
    n_missing = int(isna.sum())
    # Reject a single contiguous hole longer than _MAX_GAP_HOURS (partial-year
    # coverage); interpolate everything else (a strictly-positive reliability
    # quantity, never a true zero).
    if n_missing:
        runs, start = [], None
        for i, m in enumerate(isna):
            if m and start is None:
                start = i
            elif not m and start is not None:
                runs.append(i - start)
                start = None
        if start is not None:
            runs.append(len(isna) - start)
        if max(runs) > _MAX_GAP_HOURS:
            raise ValueError(
                f"PJM {service} {year}: a {max(runs)}-hour contiguous data "
                f"hole exceeds the {_MAX_GAP_HOURS}-hour bound — incomplete "
                "source upload, refusing to interpolate across it."
            )
        aligned = aligned.interpolate(limit_direction="both")
    return aligned.to_numpy(dtype=float), n_missing


def build_year(year: int) -> bool:
    """Build and write one year's PJM reserve-withholding parquet."""
    print(f"\n=== PJM {year} cleared RT reserve (withholding MW) ===")
    path = AS_DIR / f"reserve_market_results_{year}.parquet"
    if not path.exists():
        print(f"  no source parquet {path.name} — skipping.")
        return False

    pr_req, pr_missing = _hourly_requirement(year, _PRIMARY)
    sr_req, _ = _hourly_requirement(year, _SYNCHRONIZED)
    # Mid-Atlantic/Dominion subzone requirements (Manual 11 sec 4.2) — the
    # locational RHS of the per-gen reserve co-opt's MAD balance family
    # (docs/multi-iso/pjm-reserve-ordc.md Phase 2). Same measured source,
    # same clock; reference-only until the pergen build consumes them.
    mad_pr_req, mad_missing = _hourly_requirement(year, _PRIMARY, _LOCALE_MAD)
    mad_sr_req, _ = _hourly_requirement(year, _SYNCHRONIZED, _LOCALE_MAD)
    as_up = pr_req  # Primary requirement = the withheld upward quantity.

    print(
        f"  Primary req (withheld): mean {as_up.mean() / 1000:5.2f} GW   "
        f"peak {as_up.max() / 1000:5.2f} GW   "
        f"min {as_up.min() / 1000:5.2f} GW   "
        f"({pr_missing} h interpolated)"
    )
    print(f"  Synchronized req (ref): mean {sr_req.mean() / 1000:5.2f} GW")
    print(
        f"  MAD Primary req (subzone): mean {mad_pr_req.mean() / 1000:5.2f} GW   "
        f"({mad_missing} h interpolated)"
    )

    frame = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "sr_req_mw": sr_req,
            "pr_req_mw": pr_req,
            "as_up_mw": as_up,
            "mad_sr_req_mw": mad_sr_req,
            "mad_pr_req_mw": mad_pr_req,
        }
    )

    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "PJM Data Miner 2 Reserve Market Results (RT), "
            "data/raw/PJM-AS/reserve_market_results_"
            f"{year}.parquet; locale PJM_RTO, service PR (Primary "
            "Reserve), column as_req_mw.",
            "description": f"PJM {year} system-wide hourly reserve-withholding MW "
            "= the RTO Primary Reserve requirement (as_req_mw, "
            "service PR), the binding upward 10-minute requirement "
            "that nests Synchronized (Manual 11 sec 4.4.1). RT "
            "5-min aggregated to the non-leap 8760-hour PJM-local "
            "clock. sr_req_mw (Synchronized requirement) carried "
            "for reference only; as_up_mw == pr_req_mw is the "
            "withheld series. mad_pr_req_mw / mad_sr_req_mw are the "
            "Mid-Atlantic/Dominion reserve-subzone requirements "
            "(locale MAD, Manual 11 sec 4.2) for the per-gen "
            "reserve co-opt's locational balance family.",
            "units": "MW (cleared reserve requirement per hour)",
            "year": str(year),
        }
    )
    out = AS_DIR / f"pjm_{year}_as_up_mw.parquet"
    pq.write_table(table, out)
    print(f"  Wrote {out.relative_to(REPO_ROOT)} ({out.stat().st_size / 1024:.1f} KiB)")
    return True


def main(argv: list[str] | None = None) -> int:
    """Build the requested PJM reserve-withholding parquets."""
    parser = argparse.ArgumentParser(
        prog="build_pjm_as_withholding",
        description="Build PJM hourly reserve-withholding (Primary Reserve "
        "requirement) parquets from the RT reserve-market reports.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help="Years to build (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    built = [year for year in args.year if build_year(year)]
    skipped = sorted(set(args.year) - set(built))
    if skipped:
        print(f"\nSkipped (no source data): {skipped}")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
