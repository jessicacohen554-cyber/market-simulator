"""Curate the ``ancillary-services`` clean datatype.

Reconciles the strongly divergent per-ISO AS layouts under ``data/raw`` onto the
single wide product taxonomy declared in
``data/dictionary/schema/ancillary-services.schema.yaml`` and writes the result
through the frozen :func:`scripts.lib.clean_io.write_clean` seam, partitioned by
``iso`` / ``market`` / ``year``.

Sources and reconciliation (see the schema header for the canonical mapping):

* **NYISO** — ``data/raw/NYISO-AS/NYISO_as_{da,rt}_*.csv`` with columns
  ``Time Stamp, Name, spin_10, nonsync_10, op_30, reg_cap``. The prices are
  per reserve *zone* (``Name``) and ``Time Stamp`` is Eastern wall-clock
  hour-beginning. Mapping: ``spin_10 -> spin_``, ``nonsync_10 -> nonspin_``,
  ``op_30 -> supp_30min_``, ``reg_cap -> reg_up_``. NYISO publishes clearing
  prices only (no cleared MW).

* **PJM** — long/tall parquet, product encoded in ``ancillary_service`` and the
  clearing price in ``value`` (``unit == "Price"``). Day-ahead lives in
  ``da_ancillary_services_*.parquet`` (-> DAM); the near-real-time
  ``ancillary_services_*.parquet`` carries the RT clears (-> RTM). The product
  is pivoted to columns: Regulation Capability -> ``reg_up_``,
  Synchronized Reserve -> ``spin_``, Non-Synchronized Reserve -> ``nonspin_``,
  Thirty-Minute / Secondary Reserve -> ``supp_30min_``. ``RTO``-level products
  are system-wide (``zone="SYSTEM"``); ``Mid-Atlantic/Dominion`` (``MAD``) is a
  sub-zone. ``datetime_beginning_utc`` is already UTC. PJM Primary Reserve (an
  aggregate of sync+non-sync), Regulation *Performance* and the Mileage Ratio
  are not part of the common taxonomy and are intentionally not mapped.

* **ERCOT** — single-zone system (``zone="SYSTEM"``), day-ahead only here.
  Cleared MW per product come from
  ``data/raw/ercot/2_DAY_AS_DISCLOSURE_2d_Cleared_DAM_AS_<PROD>_<year>.parquet``;
  the Market Clearing Price for Capacity (MCPC) comes from the 60-day
  ``data/raw/ercot-AS/*60d_dam_as_only_awards*json.zip`` awards (MCPC is uniform
  across QSEs for a given delivery hour + AS type). Mapping: ``REGUP -> reg_up_``,
  ``REGDN -> reg_down_``, ``RRS* -> spin_``, ``ECRS* -> supp_30min_``,
  ``NSPIN/NSPNM -> nonspin_``. ``Delivery Date`` + ``Hour Ending`` are Central
  prevailing time, hour-ending.

The script reads only ``data/raw`` and is idempotent: re-running overwrites the
same partition files. Run ``python scripts/data/curate_ancillary_services.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

# --- common product taxonomy -> schema column names -------------------------
_PRICE_COL = {
    "reg_up": "reg_up_price_usd_per_mw",
    "reg_down": "reg_down_price_usd_per_mw",
    "spin": "spin_price_usd_per_mw",
    "nonspin": "nonspin_price_usd_per_mw",
    "supp_30min": "supp_30min_price_usd_per_mw",
}
_MW_COL = {
    "reg_up": "reg_up_mw",
    "reg_down": "reg_down_mw",
    "spin": "spin_mw",
    "nonspin": "nonspin_mw",
    "supp_30min": "supp_30min_mw",
}
_KEY_COLS = ["interval_start_utc", "interval_start_local", "iso", "zone", "market"]
ALL_COLUMNS = _KEY_COLS + list(_PRICE_COL.values()) + list(_MW_COL.values())

NYISO_TZ = "America/New_York"
ERCOT_TZ = "America/Chicago"


@dataclass(frozen=True)
class CuratedFrame:
    """One ready-to-write clean partition plus its provenance."""

    df: pd.DataFrame
    iso: str
    market: str
    year: int
    source: str


# ---------------------------------------------------------------------------
# shared finalisation
# ---------------------------------------------------------------------------
def _to_utc(local_naive: pd.Series, tz: str) -> pd.Series:
    """Localize a tz-naive wall-clock series to ``tz`` then convert to UTC.

    DST policy (pragmatic, documented): ambiguous fall-back hours are treated as
    the first (DST) occurrence and spring-forward gaps are shifted forward, so a
    single hour-beginning series localizes without raising.
    """
    return local_naive.dt.tz_localize(
        tz, ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert("UTC")


def _finalize(df: pd.DataFrame, iso: str, market: str) -> pd.DataFrame:
    """Coerce a partial frame to the full canonical schema (dtypes + columns)."""
    out = df.copy()
    out["iso"] = iso
    out["market"] = market
    for col in ALL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    # dtypes
    out["interval_start_utc"] = pd.to_datetime(out["interval_start_utc"], utc=True)
    out["interval_start_local"] = pd.to_datetime(out["interval_start_local"])
    for col in ("iso", "zone", "market"):
        out[col] = out[col].astype("string")
    for col in list(_PRICE_COL.values()) + list(_MW_COL.values()):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out = out[ALL_COLUMNS]
    out = out.sort_values(["zone", "interval_start_utc"]).reset_index(drop=True)
    return out


def _split_by_year(
    df: pd.DataFrame, iso: str, market: str, source: str
) -> Iterator[CuratedFrame]:
    """Yield one :class:`CuratedFrame` per UTC calendar year present in ``df``."""
    if df.empty:
        return
    years = df["interval_start_utc"].dt.year
    for year, part in df.groupby(years):
        yield CuratedFrame(
            df=part.reset_index(drop=True),
            iso=iso,
            market=market,
            year=int(year),
            source=source,
        )


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# NYISO
# ---------------------------------------------------------------------------
_NYISO_PRICE_MAP = {
    "spin_10": "spin",
    "nonsync_10": "nonspin",
    "op_30": "supp_30min",
    "reg_cap": "reg_up",
}


def build_nyiso(raw_root: Path) -> Iterator[CuratedFrame]:
    """Curate NYISO day-ahead and real-time zonal AS clearing prices."""
    as_dir = raw_root / "NYISO-AS"
    for raw_market, market in (("da", "DAM"), ("rt", "RTM")):
        files = sorted(as_dir.glob(f"NYISO_as_{raw_market}_*.csv"))
        if not files:
            continue
        frames = []
        for f in files:
            raw = pd.read_csv(f)
            local = pd.to_datetime(raw["Time Stamp"])
            rec = pd.DataFrame(
                {
                    "interval_start_utc": _to_utc(local, NYISO_TZ),
                    "interval_start_local": local,
                    "zone": raw["Name"].astype("string"),
                }
            )
            for src, product in _NYISO_PRICE_MAP.items():
                if src in raw.columns:
                    rec[_PRICE_COL[product]] = raw[src]
            frames.append(rec)
        df = _finalize(pd.concat(frames, ignore_index=True), "NYISO", market)
        source = "; ".join(_rel(f) for f in files)
        yield from _split_by_year(df, "NYISO", market, source)


# ---------------------------------------------------------------------------
# PJM
# ---------------------------------------------------------------------------
# Zone prefix in the ancillary_service string -> canonical zone.
_PJM_ZONE_PREFIX = (
    ("PJM RTO ", "SYSTEM"),
    ("RTO ", "SYSTEM"),
    ("Mid-Atlantic/Dominion ", "MAD"),
    ("MAD ", "MAD"),
)


def _pjm_classify(service: str) -> tuple[str | None, str | None]:
    """Map a PJM ``ancillary_service`` string to ``(zone, product)``.

    Returns ``(None, None)`` for products outside the common taxonomy
    (Primary Reserve, Regulation Performance, Mileage Ratio, ...).
    """
    zone = None
    rest = service
    for prefix, z in _PJM_ZONE_PREFIX:
        if service.startswith(prefix):
            zone, rest = z, service[len(prefix) :]
            break
    if zone is None:
        return None, None
    rest_l = rest.lower()
    if "regulation capability" in rest_l:
        product = "reg_up"
    elif "non-synchronized reserve" in rest_l:
        product = "nonspin"
    elif "synchronized reserve" in rest_l:
        product = "spin"
    elif "thirty minutes reserve" in rest_l or "secondary reserve" in rest_l:
        product = "supp_30min"
    else:
        product = None
    return zone, product


def _build_pjm_market(
    files: list[Path], market: str, raw_root: Path
) -> Iterator[CuratedFrame]:
    frames = []
    for f in files:
        raw = pd.read_parquet(f)
        raw = raw[raw["row_is_current"] & raw["unit"].str.lower().eq("price")].copy()
        zp = raw["ancillary_service"].map(_pjm_classify)
        raw["zone"] = [z for z, _ in zp]
        raw["product"] = [p for _, p in zp]
        raw = raw[raw["product"].notna() & raw["zone"].notna()]
        if raw.empty:
            continue
        raw["interval_start_utc"] = pd.to_datetime(
            raw["datetime_beginning_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True
        )
        raw["interval_start_local"] = pd.to_datetime(
            raw["datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p"
        )
        wide = raw.pivot_table(
            index=["interval_start_utc", "interval_start_local", "zone"],
            columns="product",
            values="value",
            aggfunc="mean",
        ).reset_index()
        wide = wide.rename(
            columns={p: _PRICE_COL[p] for p in _PRICE_COL if p in wide.columns}
        )
        frames.append(wide)
    if not frames:
        return
    df = _finalize(pd.concat(frames, ignore_index=True), "PJM", market)
    source = "; ".join(_rel(f) for f in files)
    yield from _split_by_year(df, "PJM", market, source)


def build_pjm(raw_root: Path) -> Iterator[CuratedFrame]:
    """Curate PJM day-ahead and real-time reserve/regulation clearing prices."""
    as_dir = raw_root / "PJM-AS"
    da = sorted(as_dir.glob("da_ancillary_services_*.parquet"))
    rt = sorted(
        p
        for p in as_dir.glob("ancillary_services_*.parquet")
        if not p.name.startswith("da_")
    )
    yield from _build_pjm_market(da, "DAM", raw_root)
    yield from _build_pjm_market(rt, "RTM", raw_root)


# ---------------------------------------------------------------------------
# ERCOT
# ---------------------------------------------------------------------------
# AS type / product code (uppercase) -> common taxonomy product.
_ERCOT_PRODUCT = {
    "REGUP": "reg_up",
    "REGDN": "reg_down",
    "RRS": "spin",
    "RRSPFR": "spin",
    "RRSFFR": "spin",
    "RRSUFR": "spin",
    "ECRS": "supp_30min",
    "ECRSS": "supp_30min",
    "ECRSM": "supp_30min",
    "NSPIN": "nonspin",
    "NSRS": "nonspin",
    "NSPNM": "nonspin",
}
_ERCOT_CLEARED_RE = re.compile(
    r"2_DAY_AS_DISCLOSURE_2d_Cleared_DAM_AS_([A-Za-z]+)_(\d{4})\.parquet$"
)


def _ercot_local_to_utc(
    delivery_date: pd.Series, hour_ending: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Build (utc, local) hour-beginning timestamps from ERCOT date + hour-ending."""
    local = pd.to_datetime(delivery_date) + pd.to_timedelta(
        hour_ending.astype(int) - 1, unit="h"
    )
    return _to_utc(local, ERCOT_TZ), local


def _load_ercot_mcpc(raw_root: Path) -> tuple[pd.DataFrame, list[Path]]:
    """Read MCPC clearing prices from the 60-day DAM AS awards JSON zips."""
    files = sorted((raw_root / "ercot-AS").glob("*60d_dam_as_only_awards*json.zip"))
    rows = []
    for f in files:
        with zipfile.ZipFile(f) as zf:
            payload = json.loads(zf.read(zf.namelist()[0]))
        names = [fld["name"] for fld in payload["fields"]]
        sub = pd.DataFrame(payload["data"], columns=names)
        rows.append(sub[["deliveryDate", "hourEnding", "ASType", "MCPC"]])
    if not rows:
        return pd.DataFrame(), files
    awards = pd.concat(rows, ignore_index=True)
    awards["product"] = awards["ASType"].str.upper().map(_ERCOT_PRODUCT)
    awards = awards[awards["product"].notna()]
    # MCPC is uniform across QSEs for a delivery hour + product; collapse.
    price = awards.groupby(["deliveryDate", "hourEnding", "product"], as_index=False)[
        "MCPC"
    ].mean()
    utc, local = _ercot_local_to_utc(price["deliveryDate"], price["hourEnding"])
    price["interval_start_utc"] = utc
    price["interval_start_local"] = local
    wide = price.pivot_table(
        index=["interval_start_utc", "interval_start_local"],
        columns="product",
        values="MCPC",
        aggfunc="mean",
    ).reset_index()
    wide = wide.rename(
        columns={p: _PRICE_COL[p] for p in _PRICE_COL if p in wide.columns}
    )
    return wide, files


def _load_ercot_mw(raw_root: Path) -> tuple[pd.DataFrame, list[Path]]:
    """Read cleared MW per product from the 2-day DAM AS disclosure parquets."""
    files = sorted(
        (raw_root / "ercot").glob("2_DAY_AS_DISCLOSURE_2d_Cleared_DAM_AS_*.parquet")
    )
    rows = []
    used = []
    for f in files:
        m = _ERCOT_CLEARED_RE.search(f.name)
        if not m:
            continue
        product = _ERCOT_PRODUCT.get(m.group(1).upper())
        if product is None:
            continue
        raw = pd.read_parquet(f)
        value_cols = [c for c in raw.columns if c.startswith("Total Cleared AS")]
        if not value_cols or "Delivery Date" not in raw.columns:
            continue
        utc, local = _ercot_local_to_utc(raw["Delivery Date"], raw["Hour Ending"])
        rows.append(
            pd.DataFrame(
                {
                    "interval_start_utc": utc,
                    "interval_start_local": local,
                    "product": product,
                    "mw": raw[value_cols[0]],
                }
            )
        )
        used.append(f)
    if not rows:
        return pd.DataFrame(), used
    long = pd.concat(rows, ignore_index=True)
    # Multiple AS subtypes can map to one product (e.g. RRSPFR/FFR/UFR -> spin);
    # the cleared total for that product is their sum within the delivery hour.
    agg = long.groupby(
        ["interval_start_utc", "interval_start_local", "product"], as_index=False
    )["mw"].sum()
    wide = agg.pivot_table(
        index=["interval_start_utc", "interval_start_local"],
        columns="product",
        values="mw",
        aggfunc="sum",
    ).reset_index()
    wide = wide.rename(columns={p: _MW_COL[p] for p in _MW_COL if p in wide.columns})
    return wide, used


def build_ercot(raw_root: Path) -> Iterator[CuratedFrame]:
    """Curate ERCOT day-ahead AS: MCPC prices joined to cleared MW (zone SYSTEM)."""
    price, price_files = _load_ercot_mcpc(raw_root)
    mw, mw_files = _load_ercot_mw(raw_root)
    if price.empty and mw.empty:
        return
    if price.empty:
        merged = mw
    elif mw.empty:
        merged = price
    else:
        merged = price.merge(
            mw, on=["interval_start_utc", "interval_start_local"], how="outer"
        )
    merged["zone"] = "SYSTEM"
    df = _finalize(merged, "ERCOT", "DAM")
    source = "; ".join(_rel(f) for f in (price_files + mw_files))
    yield from _split_by_year(df, "ERCOT", "DAM", source)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------
_BUILDERS = {
    "NYISO": build_nyiso,
    "PJM": build_pjm,
    "ERCOT": build_ercot,
}


def iter_clean_frames(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> Iterator[CuratedFrame]:
    """Yield every curated AS partition for the requested ISOs."""
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    wanted = [s.upper() for s in isos] if isos else list(_BUILDERS)
    for iso in wanted:
        builder = _BUILDERS.get(iso)
        if builder is None:
            raise ValueError(f"unknown ISO {iso!r}; known: {sorted(_BUILDERS)}")
        yield from builder(raw_root)


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Curate and write every AS partition, validating each written file.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    written: list[Path] = []
    for cf in iter_clean_frames(raw_root, isos):
        path = clean_io.write_clean(
            cf.df,
            "ancillary-services",
            iso=cf.iso,
            year=cf.year,
            market=cf.market,
            source=cf.source,
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(cf.df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: all of NYISO PJM ERCOT)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
