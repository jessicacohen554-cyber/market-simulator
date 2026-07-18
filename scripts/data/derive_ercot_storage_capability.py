"""Derive ERCOT's measured hourly battery-fleet capability from the 60-Day DAM disclosure.

The storage analogue of ``derive_ercot_thermal_dam_availability.py`` (ERCOT-57)
at FLEET-hour grain: for each delivery hour, the ISO-wide battery capability

    capability(hour) = sum over storage resources of non-OUT HSL

where a storage resource is a ``PWRSTR`` row of the ``Gen_Resource_Data``
disclosure file or — from the RTC+B go-live delivery day 2025-12-06, when
ERCOT re-modeled storage out of the Gen-resource ledger — an ``ESR`` row of
the ``ESR_Data`` file (same 48-column layout; HSL is the discharge-side max
of the combined negative-LSL envelope). An ``OUT`` resource contributes zero;
every other telemetered status (``ON``/``OFF``/``ONTEST``/``EMR``/…)
contributes its reported HSL — commitment state is not an availability event,
and a battery is startable within the hour.

BASIS DECISION (what this replaces and why). The registered non-OUT HSL is
ERCOT's own ledger of what it could actually call on: it embeds the real COD
energization timing (which the EIA-860 Operating-Month ramp lags by up to a
month), the hybrid battery halves the EIA-860 energy-storage schedule
under-covers, and the fleet's real outages/derates (which the model otherwise
carries NO storage-outage assumption for). It therefore replaces BOTH the
EIA-860 monthly COD power ramp AND the (absent) storage outage model in
backcast mode. The summer-availability audit measured the EIA-860 basis ~2 GW
below this registry in both summers (5.8 vs 7.7 GW Aug-2024; 10.6 vs 12.5 GW
Jul-2025) — the phantom-evening margin defect
(docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md §1c).

What this does NOT replace: EIA-860 stays the ZONE-assignment and DURATION
(MWh) basis — the disclosure is resource-name-keyed with no plant crosswalk,
so the model-side consumer allocates this ISO-wide hourly MW across zones by
the EIA-860 zone power shares and caps energy at disclosure-MW x the zone's
EIA-860 fleet duration (see model.storage.ercot_storage_capability_caps).

Provenance / admissibility (CLAUDE.md rules 13/14): the disclosure HSL +
Resource Status is an ERCOT-published, resource-resolved MW capability
quantity — a physical/market availability measurement, never a price and
never the dispatch outcome being validated (the outcome is the EIA-930
discharge series; this is the capability ceiling ERCOT registered before the
fact). Same source family and admissibility as the ERCOT-57 thermal
DAM-availability intake. In backcast mode the measured series REPLACES the
EIA-860 estimate of the same quantity; forecast years keep EIA-860 + the
planned pipeline (the forward-regenerating analogue — the G4 mode-aware seam).

Coverage: uncovered delivery hours are written as EMPTY (NaN) — never
zero-filled (zero would fabricate a fleet-wide outage) and never interpolated
across the known multi-week hole (deliveries 2023-10-02..2023-11-01, the
Dec-2023 publication that predates the MIS rolling retention window). The
consumer falls back to the EIA-860 basis for NaN hours. Scattered intra-day
telemetry holes up to 24 h are interpolated (the build_ercot_as_withholding
convention).

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the disclosure source
files update; never because a residual moved. Re-derivation commits must cite
the data change.

Usage::

    python scripts/data/derive_ercot_storage_capability.py \
        [--years 2023 2024 2025] [--out data/raw/ercot-storage-capability.csv]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DAM_DIR = REPO / "data" / "raw" / "ercot"
DEFAULT_OUT = REPO / "data" / "raw" / "ercot-storage-capability.csv"

HOURS_PER_YEAR = 8760
# Interpolate telemetry holes up to one day; leave longer gaps NaN for the
# consumer's EIA-860 fallback (the build_ercot_as_withholding convention).
_MAX_INTERP_GAP_HOURS = 24

_COLS = ["Delivery Date", "Hour Ending", "Resource Type", "HSL", "Resource Status"]

# Non-leap (month, day, hour) index — the model's fixed 8760 calendar.
_CALENDAR = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
_FULL_INDEX = pd.MultiIndex.from_arrays(
    [_CALENDAR.month, _CALENDAR.day, _CALENDAR.hour], names=["month", "day", "hour"]
)


def _load_storage_rows(year: int) -> pd.DataFrame:
    """Read every storage disclosure row whose DELIVERY date falls in ``year``.

    PWRSTR rows come from the ``Gen_Resource_Data`` files; ESR rows (the
    post-RTC+B storage model) from the ``ESR_Data`` files. The 60-day
    publication lag spills a year's Nov-Dec deliveries into the following
    year's files, so ``<year>`` and ``<year+1>`` files are scanned and
    filtered on the Delivery Date column.
    """
    frames: list[pd.DataFrame] = []
    for family, rtype in (("Gen_Resource_Data", "PWRSTR"), ("ESR_Data", "ESR")):
        for y in (year, year + 1):
            for path in sorted(DAM_DIR.glob(f"*60d_DAM_{family}_{y}_*.parquet")):
                df = pd.read_parquet(path, columns=_COLS)
                df = df[df["Resource Type"] == rtype]
                if df.empty:
                    continue
                dt = pd.to_datetime(df["Delivery Date"])
                df = df[dt.dt.year == year]
                if not df.empty:
                    frames.append(df)
    if not frames:
        return pd.DataFrame(columns=_COLS)
    return pd.concat(frames, ignore_index=True)


def derive_year(year: int) -> np.ndarray:
    """Return the (8760,) measured fleet capability MW for one delivery year.

    Uncovered hours are NaN (see module docstring's coverage convention).
    """
    import sys

    sys.path.insert(0, str(REPO / "scripts"))

    sys.path.insert(0, str(REPO / "scripts" / "data"))
    from build_ercot_as_withholding import prevailing_he_to_cst

    df = _load_storage_rows(year)
    if df.empty:
        return np.full(HOURS_PER_YEAR, np.nan)

    live = df["HSL"].to_numpy(dtype=float)
    live = np.where(df["Resource Status"].to_numpy() == "OUT", 0.0, live)
    # ESR HSL is the discharge-side max of the combined envelope; clip any
    # negative reads (charge-side artifacts) to zero.
    live = np.clip(live, 0.0, None)

    rows = pd.DataFrame(
        {
            "ts": prevailing_he_to_cst(
                pd.to_datetime(df["Delivery Date"]).dt.normalize(),
                df["Hour Ending"].astype(int),
            ),
            "mw": live,
        }
    )
    keep = (rows["ts"].dt.year == year) & ~(
        (rows["ts"].dt.month == 2) & (rows["ts"].dt.day == 29)
    )
    rows = rows[keep]
    fleet = rows.groupby([rows["ts"].dt.month, rows["ts"].dt.day, rows["ts"].dt.hour])[
        "mw"
    ].sum()
    fleet.index.names = ["month", "day", "hour"]
    aligned = fleet.reindex(_FULL_INDEX)

    # Interpolate only short intra-coverage holes; a longer run of missing
    # hours (the Oct-2023 publication hole) stays NaN for the consumer's
    # EIA-860 fallback.
    isna = aligned.isna().to_numpy()
    if isna.any() and not isna.all():
        vals = aligned.to_numpy(dtype=float).copy()
        # Run-length scan of NaN gaps; vectorized over gap boundaries.
        idx = np.flatnonzero(np.diff(np.concatenate(([0], isna.view(np.int8), [0]))))
        starts, ends = idx[::2], idx[1::2]
        interp = pd.Series(vals).interpolate(limit_direction="both").to_numpy()
        for s, e in zip(starts, ends):
            if e - s <= _MAX_INTERP_GAP_HOURS:
                vals[s:e] = interp[s:e]
        aligned = pd.Series(vals, index=aligned.index)
    return aligned.to_numpy(dtype=float)


def main() -> None:
    """Derive and write the hourly fleet-capability CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    frames = []
    for y in args.years:
        cap = derive_year(y)
        frames.append(
            pd.DataFrame(
                {
                    "year": np.full(HOURS_PER_YEAR, y, dtype=int),
                    "hour": np.arange(HOURS_PER_YEAR, dtype=int),
                    "capability_mw": np.round(cap, 1),
                }
            )
        )
        cov = np.isfinite(cap)
        print(
            f"{y}: covered {int(cov.sum())}/{HOURS_PER_YEAR} h; "
            f"capability mean {np.nanmean(cap):,.0f} MW, "
            f"p95 {np.nanpercentile(cap, 95):,.0f}, max {np.nanmax(cap):,.0f}"
        )
    out = pd.concat(frames, ignore_index=True)
    args.out.write_text(out.to_csv(index=False))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
