"""Curate the ``emissions-unit-annual`` clean datatype from CAMPD (CEMS).

Rolls the hourly **unit-level** CAMPD extracts under
``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` up to one row per
``(plant_id, unit_id, year)`` — the small, queryable product the forward
per-plant CO2-rate estimator consumes
(``docs/handoffs/emissions-co2-rate-plan-2026-07.md`` §4).

It reads **only** ``data/raw/campd-unit-level`` (the unit grain is the whole
point — it dissolves the mixed coal/gas facility exclusion by giving each unit
its own history). A state whose extract carries no ``unitId`` column gets
facility-grain rows keyed ``unit_id = "ALL"``. Standardization (masses to kg,
heat in MMBtu) reuses the constants in ``src/market_sim/data/campd.py`` so
there is one source of truth; the CO2 backfill and start-count conventions
mirror ``campd._co2_total`` / ``campd._startup_factors`` (``gross_mw > 1 MW``
off->on transitions on a gap-filled hourly clock).

Quarantined holdout years (2022, H1-2026) are **hard-skipped** even though the
files may sit on disk (CLAUDE.md rule 22): no quarantined-year row ever enters
this derived artifact.

Output is partitioned by year through ``scripts.lib.clean_io.write_clean``:
``data/clean/emissions-unit-annual/emissions-unit-annual_{year}.parquet``, and
each file is round-trip validated. The script reads only ``data/raw`` and is
idempotent.

Usage:
    python scripts/curate_emissions_unit_annual.py               # all years
    python scripts/curate_emissions_unit_annual.py --years 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.data.campd import (
    DEFAULT_CO2_KG_PER_MMBTU,
    LB_TO_KG,
    SHORT_TON_TO_KG,
    _ONLINE_MW,
)

# Repo root on sys.path so ``scripts.lib`` resolves when run by path.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("curate_emissions_unit_annual")

DATATYPE = "emissions-unit-annual"
RAW_UNIT_DIR: Path = paths.RAW_DATA_DIR / "campd-unit-level"

# Holdout years never rolled up (CLAUDE.md rule 22): hard skip regardless of
# what sits on disk.
QUARANTINED_YEARS: frozenset[int] = frozenset({2022, 2026})

_SCHEMA_COLUMNS: tuple[str, ...] = (
    "state",
    "plant_id",
    "unit_id",
    "year",
    "primary_fuel",
    "unit_type",
    "gross_mwh",
    "steam_load_klbh_sum",
    "co2_kg",
    "nox_kg",
    "so2_kg",
    "heat_mmbtu",
    "op_hours",
    "starts",
    "co2_source",
    "mw_source",
)

_YEAR_RE = re.compile(r"_(\d{4})\.parquet$")


def _normalize_unit_hourly(raw: pd.DataFrame, year: int) -> pd.DataFrame:
    """Standardize one raw unit-level extract to unit-grain hourly rows.

    Keeps ``unit_id`` (unlike ``campd._normalize_campd``, which sums units to
    the plant). A frame with no ``unitId`` column is treated as facility grain:
    every row gets ``unit_id = "ALL"``. Masses are converted to kg, heat stays
    MMBtu, and a gap-free hourly timestamp is attached for start detection.
    """
    plant_id = pd.to_numeric(raw["facilityId"], errors="coerce")
    hour = pd.to_numeric(raw["hour"], errors="coerce")
    keep = plant_id.notna() & hour.notna()
    if "unitId" in raw.columns:
        unit_id = raw["unitId"].astype("string")
    else:
        unit_id = pd.Series("ALL", index=raw.index, dtype="string")
    raw = raw[keep]
    plant_id = plant_id[keep].astype("int64")
    hour = hour[keep].astype("int64")
    unit_id = unit_id[keep].fillna("ALL").astype(str)

    ts = pd.to_datetime(raw["date"]) + pd.to_timedelta(hour, unit="h")
    out = pd.DataFrame(
        {
            "plant_id": plant_id.to_numpy(),
            "unit_id": unit_id.to_numpy(),
            "state": raw["stateCode"].astype(str).to_numpy(),
            "primary_fuel": (
                raw["primaryFuelInfo"].astype(str).to_numpy()
                if "primaryFuelInfo" in raw.columns
                else np.array([""] * len(raw))
            ),
            "unit_type": (
                raw["unitType"].astype(str).to_numpy()
                if "unitType" in raw.columns
                else np.array([""] * len(raw))
            ),
            "ts": ts.to_numpy(),
            "gross_mw": pd.to_numeric(raw["grossLoad"], errors="coerce").to_numpy(),
            "steam_load": pd.to_numeric(raw["steamLoad"], errors="coerce").to_numpy(),
            "co2_kg": pd.to_numeric(raw["co2Mass"], errors="coerce").to_numpy()
            * SHORT_TON_TO_KG,
            "nox_kg": pd.to_numeric(raw["noxMass"], errors="coerce").to_numpy()
            * LB_TO_KG,
            "so2_kg": pd.to_numeric(raw["so2Mass"], errors="coerce").to_numpy()
            * LB_TO_KG,
            "heat_mmbtu": pd.to_numeric(raw["heatInput"], errors="coerce").to_numpy(),
        }
    )
    out["year"] = int(year)
    return out


def _co2_annual(co2_kg: pd.Series, heat_mmbtu: pd.Series) -> tuple[float, str]:
    """Return ``(annual_co2_kg, source)`` backfilling unmonitored hours.

    Mirrors ``campd._co2_total`` at the unit grain: a unit reporting CO2 for
    ~all of its heat is taken measured; one reporting CO2 for only part is
    scaled to full heat at its own measured intensity; one reporting none uses
    the EPA natural-gas default factor.
    """
    measured = float(np.nansum(co2_kg.to_numpy()))
    heat_total = float(np.nansum(heat_mmbtu.to_numpy()))
    has_co2 = co2_kg.notna()
    heat_with_co2 = float(np.nansum(heat_mmbtu.to_numpy()[has_co2.to_numpy()]))
    if heat_with_co2 <= 0.0:
        return DEFAULT_CO2_KG_PER_MMBTU * heat_total, "heat_backfilled"
    if heat_with_co2 >= 0.999 * heat_total:
        return measured, "measured"
    return (measured / heat_with_co2) * heat_total, "partial_backfill"


def _starts(ts: pd.Series, gross_mw: pd.Series) -> int:
    """Count off->on transitions on a gap-filled hourly clock (vectorized).

    Off-hours CAMPD omits are reconstructed as zeros over the contiguous span
    the unit reported in; a start is ``gross_mw`` crossing ``_ONLINE_MW``
    (1 MW) from below — the ``campd._startup_factors`` convention. No Python
    loop over hours: the reindex + boolean-shift is fully vectorized.
    """
    s = (
        pd.Series(gross_mw.to_numpy(), index=pd.DatetimeIndex(ts))
        .groupby(level=0)
        .sum()
        .sort_index()
    )
    if s.empty:
        return 0
    full = pd.date_range(s.index.min(), s.index.max(), freq="h")
    gross = s.reindex(full, fill_value=0.0).to_numpy()
    online = gross > _ONLINE_MW
    if online.sum() < 1:
        return 0
    prev = np.concatenate([[False], online[:-1]])
    return int((online & ~prev).sum())


def _aggregate_unit_year(group: pd.DataFrame) -> pd.Series:
    """Roll one ``(plant_id, unit_id, year)`` group up to an annual row."""
    gross = group["gross_mw"]
    heat = group["heat_mmbtu"]
    co2, co2_source = _co2_annual(group["co2_kg"], heat)
    gross_mwh = float(np.nansum(gross.to_numpy()))
    op_hours = int((gross.fillna(0.0) > 0.0).sum())
    heat_total = float(np.nansum(heat.to_numpy()))
    # Gross-MW basis: real gross readings present, else a heat-only unit
    # (CHP/steam host) whose gross is not metered by CEMS.
    mw_source = (
        "measured" if op_hours > 0 else ("heat_proxy" if heat_total > 0 else "measured")
    )
    return pd.Series(
        {
            "state": str(group["state"].iloc[0]),
            "primary_fuel": str(group["primary_fuel"].iloc[0]),
            "unit_type": str(group["unit_type"].iloc[0]),
            "gross_mwh": gross_mwh,
            "steam_load_klbh_sum": float(np.nansum(group["steam_load"].to_numpy())),
            "co2_kg": co2,
            "nox_kg": float(np.nansum(group["nox_kg"].to_numpy())),
            "so2_kg": float(np.nansum(group["so2_kg"].to_numpy())),
            "heat_mmbtu": heat_total,
            "op_hours": op_hours,
            "starts": _starts(group["ts"], gross),
            "co2_source": co2_source,
            "mw_source": mw_source,
        }
    )


def _finalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce the annual frame to the schema's declared dtypes and order."""
    df["plant_id"] = df["plant_id"].astype("int64")
    df["unit_id"] = df["unit_id"].astype("string")
    df["year"] = df["year"].astype("int64")
    df["op_hours"] = df["op_hours"].astype("int64")
    df["starts"] = df["starts"].astype("int64")
    for c in ("state", "primary_fuel", "unit_type", "co2_source", "mw_source"):
        df[c] = df[c].astype("string")
    for c in (
        "gross_mwh",
        "steam_load_klbh_sum",
        "co2_kg",
        "nox_kg",
        "so2_kg",
        "heat_mmbtu",
    ):
        df[c] = df[c].astype("float64")
    return df[list(_SCHEMA_COLUMNS)].reset_index(drop=True)


def curate_year(
    year: int,
    *,
    unit_dir: Path = RAW_UNIT_DIR,
    allow_quarantined: bool = False,
    states: frozenset[str] | None = None,
) -> Path:
    """Curate one year of unit-level CAMPD into ``emissions-unit-annual``.

    Raises ``ValueError`` for a quarantined year (never rolled up) and
    ``FileNotFoundError`` when no extract is present. Returns the written path.

    ``states``, when given, restricts the input glob to those state-code
    extracts (e.g. a single ISO's states) instead of every state on disk.
    The written file is still the whole-year ``emissions-unit-annual``
    artifact — downstream readers (``derive_plant_emissions_v2.py``) already
    filter by state after reading, so a state-scoped curate is equivalent for
    any consumer that only wants those states' rows, just cheaper to compute.
    """
    if year in QUARANTINED_YEARS and not allow_quarantined:
        raise ValueError(
            f"year {year} is under CLAUDE.md rule 22 quarantine; "
            f"{DATATYPE} never rolls up 2022/H1-2026 (pass --holdout-intake "
            "<ISO> with its calibration-complete marker for the one-shot)"
        )
    if unit_dir.is_dir():
        paths_in = sorted(unit_dir.glob(f"*_{year}.parquet"))
        if states is not None:
            paths_in = [p for p in paths_in if p.name.split("_")[0] in states]
    else:
        paths_in = []
    if not paths_in:
        raise FileNotFoundError(
            f"no unit-level CAMPD extracts for {year} in {unit_dir}"
            + (f" (states filter: {sorted(states)})" if states else "")
        )

    frames = [_normalize_unit_hourly(pd.read_parquet(p), year) for p in paths_in]
    hourly = pd.concat(frames, ignore_index=True)

    annual = (
        hourly.groupby(["plant_id", "unit_id", "year"], observed=True)
        .apply(_aggregate_unit_year, include_groups=False)
        .reset_index()
    )
    annual = _finalize_dtypes(annual).sort_values(["plant_id", "unit_id"])

    source = f"data/raw/campd-unit-level/*_{year}.parquet"
    path = clean_io.write_clean(annual, DATATYPE, year=year, source=source)
    clean_io.validate_clean(path)
    logger.info(
        "%s %d: %d unit-year rows (%d plants) -> %s",
        DATATYPE,
        year,
        len(annual),
        annual["plant_id"].nunique(),
        path,
    )
    return path


def _detect_years(unit_dir: Path) -> list[int]:
    """Return sorted non-quarantined years present under the unit-level dir."""
    years: set[int] = set()
    if unit_dir.is_dir():
        for p in unit_dir.glob("*.parquet"):
            m = _YEAR_RE.search(p.name)
            if m:
                years.add(int(m.group(1)))
    return sorted(y for y in years if y not in QUARANTINED_YEARS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Curate CAMPD unit-level CEMS into emissions-unit-annual."
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=None,
        help="Years to curate (default: every non-quarantined year on disk).",
    )
    parser.add_argument(
        "--holdout-intake",
        default=None,
        metavar="ISO",
        help="authorize rolling up quarantined-year (2022/2026) extracts for the "
        "named ISO's one-shot holdout validation (requires its "
        "calibration-complete marker; CLAUDE.md rule 22).",
    )
    parser.add_argument(
        "--states",
        nargs="*",
        default=None,
        metavar="STATE",
        help="restrict the input glob to these 2-letter state codes instead of "
        "every state extract on disk (cheaper when only one ISO's rows are "
        "needed downstream — derive_plant_emissions_v2.py already filters by "
        "state after reading, so this is equivalent for that consumer).",
    )
    args = parser.parse_args(argv)

    allow_quarantined = False
    if args.holdout_intake:
        import json

        marker_path = (
            paths.REPO_ROOT
            / "frontend"
            / "data"
            / "backcast"
            / "calibration-complete.json"
        )
        try:
            complete = {
                str(k).upper()
                for k in (json.loads(marker_path.read_text()).get("complete") or {})
            }
        except (OSError, ValueError):
            complete = set()
        iso = args.holdout_intake.upper()
        if iso not in complete:
            parser.error(
                f"no calibration-complete marker for {iso} in {marker_path} "
                f"(complete: {sorted(complete) or 'none'}); rule 22 one-shot "
                "holdout intake requires the marker"
            )
        allow_quarantined = True

    years = args.years or _detect_years(RAW_UNIT_DIR)
    if not allow_quarantined:
        skipped = [y for y in (args.years or []) if y in QUARANTINED_YEARS]
        for y in skipped:
            logger.warning("skipping quarantined year %d (CLAUDE.md rule 22)", y)
        years = [y for y in years if y not in QUARANTINED_YEARS]
    if not years:
        logger.error("no curatable years found under %s", RAW_UNIT_DIR)
        return 1
    states = frozenset(s.upper() for s in args.states) if args.states else None
    for year in years:
        curate_year(year, allow_quarantined=allow_quarantined, states=states)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
