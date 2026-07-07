"""Process EIA-923 Schedules 1 and 5 into per-plant generation and cost tables.

The official EIA-923 release ships one Excel workbook per year covering
both Page 1 ("Generation and Fuel Data" — one row per
plant/prime-mover/fuel with monthly net generation, fuel consumption
and the CHP flag) and Page 5 ("Fuel Receipts and Costs" — one row per
fuel receipt with delivered cost). This script produces two parquets:

  * ``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`` — per-plant
    delivered fuel cost from Page 5 (``$/MMBtu`` after the cents→dollars
    conversion). Consumed by the dispatch fuel-price resolver.
  * ``data/raw/_processed-legacy/eia923_monthly_generation.parquet`` — per-plant
    net generation from Page 1 (MWh), keeping the prime-mover, fuel and
    CHP flag for downstream fossil-class breakdowns. Consumed by the
    calibration diagnostic.

EIA suppresses delivered cost for many records (``FUEL_COST = '.'``);
those receipts are dropped before the quantity-weighted aggregation, so
a plant with no reported cost in a month is simply absent from the
output and the dispatch resolver's fallback (AEO Henry Hub + basis,
COAL_PRICE_*_BY_YEAR) takes over.

Usage:
    python scripts/process_f923_fuel_costs.py [--out-dir DIR] [--ba ERCO]

Defaults to processing every ``f923_*.zip`` in
``data/raw/`` and writing the ERCO-only parquets.
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("process_f923")

# Page 5 (Fuel Receipts and Costs) header sits a few rows down past the
# EIA boilerplate. The exact row varies by release vintage (row 4 for
# final releases, row 3 for the early-cycle 2025 file), so we scan the
# first eight rows for the YEAR header rather than hard-coding it.
_PAGE_5_HEADER_SCAN_ROWS: int = 8
_PAGE_5_SHEET: str = "Page 5 Fuel Receipts and Costs"
# Page 1 ("Generation and Fuel Data") sits a few rows further down — the
# EIA boilerplate is longer. Same scan-for-Plant-Id approach.
_PAGE_1_SHEET: str = "Page 1 Generation and Fuel Data"

_MONTH_NAMES: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

# Columns we keep from the raw receipts sheet, normalised to short names.
# A column may appear under several spellings across release vintages
# (e.g. ``Balancing\nAuthority Code`` in the final releases, ``BA_CODE`` in
# the preliminary 2025 file), so multiple source names can map to one
# canonical name.
_RENAME: dict[str, str] = {
    "YEAR": "year",
    "MONTH": "month",
    "Plant Id": "plant_id",
    "Plant State": "state",
    "ENERGY_SOURCE": "energy_source",
    "FUEL_GROUP": "fuel_group",
    "QUANTITY": "quantity",
    "FUEL_COST": "fuel_cost_cents_per_mmbtu",
    # Schedule-5 contracted-vs-spot flag (codes C / NC / S / T). The header is
    # "Purchase Type" in recent releases, "Contract Type" in older ones; both
    # map to one canonical column. Kept for the coal take-or-pay deriver
    # (scripts/derive_coal_takeorpay.py); cost/rank consumers ignore it.
    "Purchase Type": "purchase_type",
    "Contract Type": "purchase_type",
    "Balancing\nAuthority Code": "ba_code",
    "BA_CODE": "ba_code",
}

# EIA-923 reports FUEL_COST in cents per MMBtu with one-decimal precision,
# i.e. the column value is the dollar price scaled by 100. Dividing by
# this converts the column to delivered $/MMBtu.
_CENTS_PER_DOLLAR: float = 100.0

# Per-fuel plausible delivered-cost band ($/MMBtu) for a single fuel receipt.
# The national EIA-923 file carries a handful of order-of-magnitude data-entry
# errors — gas reported at $99,241/MMBtu (in May), $8,781/MMBtu (in July),
# etc. (wrong units or a near-zero quantity divisor) — that, left in, would
# dominate a plant's quantity-weighted monthly cost and any state/zone
# "nearby plant" average built from it. Receipts outside their fuel's band
# are dropped before aggregation.
#
# A *percentage of the annual average* is the wrong test here: legitimate
# constrained-region winter gas runs +155% to +5,000% of its average (a
# Virginia plant hit $118/MMBtu in Jan 2023; California/Nevada plants cleared
# $35-47/MMBtu on million-MMBtu volumes in the 2022-23 West-coast gas crisis),
# so any percentage band wide enough to keep that real spread catches nothing.
# Instead each fuel gets an absolute physical-plausibility ceiling set well
# above its observed real maximum in this 2023-25 window (gas ~$118, petroleum
# ~$59, coal ~$27), generous enough to admit a worse winter while still
# removing the separate error cluster. The shared small negative floor keeps
# legitimate take-or-pay disposal receipts (a producer paying to offload
# stranded gas). ERCOT receipts sit far inside every band, so the ERCOT table
# is unchanged.
_MIN_DOLLARS_PER_MMBTU: float = -10.0
_MAX_DOLLARS_PER_MMBTU_DEFAULT: float = 200.0
_MAX_DOLLARS_PER_MMBTU_BY_FUEL: dict[str, float] = {
    "Natural Gas": 200.0,  # real max ~$118 (constrained winter)
    "Petroleum": 120.0,  # real max ~$59 (spike-priced distillate)
    "Petroleum Coke": 60.0,  # a cheap residual; real max well under $30
    "Coal": 60.0,  # real max ~$27
}

# Fuel-group strings we keep. Everything else (waste fuels, biomass) is
# outside the gas/coal/oil cost trajectories the dispatch model uses.
_FUEL_GROUP_KEEP: frozenset[str] = frozenset(
    {"Natural Gas", "Coal", "Petroleum", "Petroleum Coke"}
)


def _find_zips(raw_dir: Path) -> list[Path]:
    """Return every ``f923_*.zip`` under ``raw_dir`` in year order."""
    zips = sorted(raw_dir.glob("f923_*.zip"))
    if not zips:
        raise FileNotFoundError(f"No f923_*.zip found in {raw_dir}")
    return zips


def _extract_schedules_xlsx(zip_path: Path) -> bytes:
    """Return the bytes of the Schedules 2-3-4-5 workbook in ``zip_path``."""
    with zipfile.ZipFile(zip_path) as zf:
        members = [
            name
            for name in zf.namelist()
            if re.search(r"Schedules_2_3_4_5", name) and name.lower().endswith(".xlsx")
        ]
        if not members:
            raise FileNotFoundError(f"No Schedules 2-3-4-5 workbook in {zip_path.name}")
        return zf.read(members[0])


# The 2025 annual Early Release workbook (30JUN2026) prepends a caution
# column ("Early release data (July 2026). Not fully edited…") to every
# sheet, shifting the real header key out of column 0. Scan this many
# leading columns for the key; columns to its left are release-vintage
# padding and are dropped before renaming.
_HEADER_SCAN_COLS: int = 3


def _find_header_row(xlsx_bytes: bytes, sheet_name: str, key: str) -> tuple[int, int]:
    """Return ``(header_row, key_column)`` for ``sheet_name`` in the workbook.

    The header key sits in column 0 of the final/monthly-cycle releases and
    in column 1 of the 2025 annual Early Release (which prepends a caution
    padding column), so the scan covers the first ``_HEADER_SCAN_COLS``
    columns of the first few rows.

    Args:
        xlsx_bytes: Workbook contents.
        sheet_name: Sheet to scan.
        key: Header text identifying the data header row
            (e.g. ``"YEAR"`` for Page 5, ``"Plant Id"`` for Page 1).
    """
    probe = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        sheet_name=sheet_name,
        header=None,
        nrows=12,
    )
    target = key.strip().upper()
    for col in range(min(_HEADER_SCAN_COLS, probe.shape[1])):
        for idx, value in enumerate(probe.iloc[:, col]):
            if isinstance(value, str) and value.strip().upper() == target:
                return idx, col
    raise ValueError(f"Could not locate {key!r} header row on {sheet_name!r}")


def _load_receipts(zip_path: Path) -> pd.DataFrame:
    """Read Page 5 from ``zip_path``'s schedules workbook, renaming columns."""
    logger.info("reading Page 5 of %s", zip_path.name)
    xlsx_bytes = _extract_schedules_xlsx(zip_path)
    header, key_col = _find_header_row(xlsx_bytes, _PAGE_5_SHEET, "YEAR")
    raw = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        sheet_name=_PAGE_5_SHEET,
        header=header,
    )
    raw = raw.iloc[:, key_col:]
    keep = [c for c in _RENAME if c in raw.columns]
    return raw[keep].rename(columns=_RENAME)


def _load_generation(zip_path: Path, year: int) -> pd.DataFrame:
    """Read Page 1 from ``zip_path``, returning per-plant-row generation.

    Page 1 has one row per ``(plant, prime mover, fuel)`` triple with 12
    ``Netgen <Month>`` columns and an annual ``Net Generation`` total.
    Rows are kept in their original granularity so a downstream consumer
    can classify a CC plant's CA-vs-CT components separately.
    """
    logger.info("reading Page 1 of %s", zip_path.name)
    xlsx_bytes = _extract_schedules_xlsx(zip_path)
    header, key_col = _find_header_row(xlsx_bytes, _PAGE_1_SHEET, "Plant Id")
    raw = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        sheet_name=_PAGE_1_SHEET,
        header=header,
    )
    raw = raw.iloc[:, key_col:]
    rename = {
        "Plant Id": "plant_id",
        "Plant Name": "plant_name",
        "Reported\nPrime Mover": "prime_mover",
        "Reported\nFuel Type Code": "fuel_type",
        "Combined Heat And\nPower Plant": "chp",
        "Net Generation\n(Megawatthours)": "netgen_annual_mwh",
        "Balancing\nAuthority Code": "ba_code",
        "BA_CODE": "ba_code",
    }
    columns = [c for c in rename if c in raw.columns]
    df = raw[columns + [f"Netgen\n{m}" for m in _MONTH_NAMES]].rename(
        columns=rename,
    )
    for m in _MONTH_NAMES:
        df[f"netgen_{m.lower()}_mwh"] = pd.to_numeric(
            df[f"Netgen\n{m}"], errors="coerce"
        )
        df = df.drop(columns=[f"Netgen\n{m}"])
    df["netgen_annual_mwh"] = pd.to_numeric(df["netgen_annual_mwh"], errors="coerce")
    df["year"] = year
    return df


def aggregate_monthly_fuel_costs(
    zip_paths: list[Path], ba_code: str | None = None
) -> pd.DataFrame:
    """Return a quantity-weighted monthly fuel-cost table from EIA-923 zips.

    Receipts whose ``FUEL_COST`` is the EIA-suppressed sentinel ``.`` are
    dropped before aggregation; a plant-month with no reported cost is
    therefore absent from the result (the dispatch resolver's per-fuel
    fallback covers it).

    Args:
        zip_paths: One ``f923_*.zip`` per calendar year.
        ba_code: When given, keep only receipts at plants in this
            balancing authority (e.g. ``"ERCO"``); ``None`` keeps every BA.

    Returns:
        ``(year, month, plant_id, state, fuel_group, price_per_mmbtu,
        quantity)`` with one row per plant-month-fuel. ``state`` is the
        plant's USPS state code, carried so the dispatch resolver can build
        a state-level "nearby plant" fallback price for plants that do not
        report their own delivered cost (see
        :func:`market_sim.data.fuel.apply_plant_monthly_fuel_prices`).
    """
    frames = [_load_receipts(path) for path in zip_paths]
    df = pd.concat(frames, ignore_index=True)

    df["fuel_cost_cents_per_mmbtu"] = pd.to_numeric(
        df["fuel_cost_cents_per_mmbtu"], errors="coerce"
    )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df = df.dropna(subset=["fuel_cost_cents_per_mmbtu", "quantity"])
    df = df[df["quantity"] > 0]
    df = df[df["fuel_group"].isin(_FUEL_GROUP_KEEP)]

    # Drop anomalous receipts (EIA data-entry errors) outside the plausible
    # per-fuel delivered-cost band so a single bad record cannot skew a
    # plant's quantity-weighted monthly cost or a nearby-plant average.
    dollars = df["fuel_cost_cents_per_mmbtu"] / _CENTS_PER_DOLLAR
    ceiling = (
        df["fuel_group"]
        .map(_MAX_DOLLARS_PER_MMBTU_BY_FUEL)
        .fillna(_MAX_DOLLARS_PER_MMBTU_DEFAULT)
    )
    n_before = len(df)
    df = df[(dollars >= _MIN_DOLLARS_PER_MMBTU) & (dollars <= ceiling)]
    n_dropped = n_before - len(df)
    if n_dropped:
        logger.info(
            "dropped %d anomalous fuel receipts outside the per-fuel "
            "plausibility band (floor $%.0f/MMBtu)",
            n_dropped,
            _MIN_DOLLARS_PER_MMBTU,
        )

    if ba_code is not None:
        df = df[df["ba_code"] == ba_code]

    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df.dropna(subset=["plant_id"])
    df["plant_id"] = df["plant_id"].astype(int)

    # A plant sits in one state; take its modal reported state code so the
    # state column survives the (year, month, fuel) aggregation below.
    if "state" in df.columns:
        plant_state = (
            df.dropna(subset=["state"])
            .groupby("plant_id")["state"]
            .agg(lambda s: s.astype(str).str.strip().mode().iat[0])
        )
    else:
        plant_state = pd.Series(dtype=str)

    df["weighted"] = df["fuel_cost_cents_per_mmbtu"] * df["quantity"]

    key = ["year", "month", "plant_id", "fuel_group"]
    grouped = (
        df.groupby(key, sort=True)
        .agg(weighted=("weighted", "sum"), quantity=("quantity", "sum"))
        .reset_index()
    )
    grouped["price_per_mmbtu"] = (
        grouped["weighted"] / grouped["quantity"] / _CENTS_PER_DOLLAR
    )
    grouped["plant_id"] = grouped["plant_id"].astype(int)
    grouped["year"] = grouped["year"].astype(int)
    grouped["month"] = grouped["month"].astype(int)
    grouped["state"] = grouped["plant_id"].map(plant_state).fillna("")
    return grouped[
        [
            "year",
            "month",
            "plant_id",
            "state",
            "fuel_group",
            "price_per_mmbtu",
            "quantity",
        ]
    ]


def aggregate_monthly_generation(
    zip_paths: list[Path], ba_code: str | None = None
) -> pd.DataFrame:
    """Return per-plant monthly net generation from EIA-923 Page 1.

    One row per ``(year, plant_id, prime_mover, fuel_type, chp)`` tuple,
    with twelve ``netgen_<month>_mwh`` columns and an
    ``netgen_annual_mwh`` total. The CHP flag and prime mover are kept
    so a downstream consumer can bucket gas plants into the model's
    CC_CHP / CC_REGULAR / CT_CHP / CT_PEAKER / ST_GAS / ST_CHP classes.

    Args:
        zip_paths: One ``f923_*.zip`` per calendar year.
        ba_code: When given, keep only plants in this balancing authority
            (e.g. ``"ERCO"``).
    """
    years = []
    for path in zip_paths:
        # F923 zip names look like ``f923_2024 (1).zip`` — the year is
        # the four-digit token after the ``f923_`` prefix.
        match = re.search(r"f923[_-]?(\d{4})", path.stem)
        year = int(match.group(1)) if match else 0
        years.append((path, year))

    frames = [_load_generation(path, year) for path, year in years]
    df = pd.concat(frames, ignore_index=True)
    if ba_code is not None:
        df = df[df["ba_code"] == ba_code]
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df.dropna(subset=["plant_id"])
    df["plant_id"] = df["plant_id"].astype(int)
    return df.reset_index(drop=True)


def main() -> None:
    """Process every ``f923_*.zip`` under data/raw and write parquet."""
    parser = argparse.ArgumentParser(
        description="Process EIA-923 fuel receipts into a monthly cost table."
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directory holding the f923_*.zip releases.",
    )
    parser.add_argument(
        "--out-dir",
        default="data/raw/_processed-legacy",
        help="Directory for the output parquet.",
    )
    parser.add_argument(
        "--ba",
        default="",
        help="Balancing-authority filter (e.g. ERCO); blank (the default) "
        "keeps every BA so multi-ISO runs (PJM, etc.) find their "
        "plants. Pass --ba ERCO to reproduce the legacy ERCOT-only "
        "table.",
    )
    parser.add_argument(
        "--merge-years",
        nargs="+",
        type=int,
        default=None,
        metavar="YEAR",
        help="Surgical vintage refresh: process only the zips for these "
        "years, then replace those years' rows in the EXISTING costs "
        "parquet, leaving every other year byte-stable (used to intake "
        "the 2025 annual Early Release without re-downloading the "
        "2022/2026 vintages). In this mode the Page-1 generation "
        "parquet is NOT rewritten: it is a calibration benchmark, and "
        "refreshing it re-benches every registered run — a separate, "
        "owner-visible operation.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zips = _find_zips(raw_dir)
    ba = args.ba or None
    cost_path = out_dir / "eia923_monthly_fuel_costs.parquet"

    if args.merge_years is not None:
        wanted = set(args.merge_years)
        zips = [
            z
            for z in zips
            if (m := re.search(r"f923[_-]?(\d{4})", z.stem))
            and int(m.group(1)) in wanted
        ]
        if not zips:
            raise FileNotFoundError(
                f"No f923_*.zip for years {sorted(wanted)} in {raw_dir}"
            )
        existing = pd.read_parquet(cost_path)
        fresh = aggregate_monthly_fuel_costs(zips, ba_code=ba)
        merged = pd.concat(
            [existing[~existing["year"].isin(wanted)], fresh], ignore_index=True
        ).sort_values(["year", "month", "plant_id", "fuel_group"], ignore_index=True)
        merged.to_parquet(cost_path, index=False)
        logger.info(
            "merged %s: years %s refreshed (%d rows) onto %d carried rows",
            cost_path,
            sorted(wanted),
            len(fresh),
            (~existing["year"].isin(wanted)).sum(),
        )
        return

    costs = aggregate_monthly_fuel_costs(zips, ba_code=ba)
    costs.to_parquet(cost_path, index=False)
    logger.info(
        "wrote %s (%d plant-months across %d years, BA filter=%s)",
        cost_path,
        len(costs),
        costs["year"].nunique(),
        ba or "ALL",
    )

    generation = aggregate_monthly_generation(zips, ba_code=ba)
    gen_path = out_dir / "eia923_monthly_generation.parquet"
    generation.to_parquet(gen_path, index=False)
    logger.info(
        "wrote %s (%d plant-rows across %d years, BA filter=%s)",
        gen_path,
        len(generation),
        generation["year"].nunique(),
        ba or "ALL",
    )


if __name__ == "__main__":
    main()
