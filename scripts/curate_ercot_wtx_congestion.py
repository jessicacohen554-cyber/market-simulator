"""Curate the ``ercot-wtx-congestion`` clean datatype: measured hourly ERCOT
West Texas Export corridor transmission-congestion pressure.

Reads two already-committed raw sources (no network, no new intake):

* ``data/raw/iso-specific-transmission/SCEDBTCNP686_*.parquet`` — ERCOT NP6-86-CD
  "SCED Shadow Prices and Binding Transmission Constraints" (per ~5-minute SCED
  execution, every active constraint with its Limit / flow Value / ShadowPrice
  and monitored From/To station + kV).
* ``data/raw/ercot-settlement-points/SP_List_and_EB_Mapping_*.zip`` — ERCOT's
  authoritative Settlement Points List and Electrical Buses Mapping (NP4-160-SG);
  its ``SUBSTATION`` code matches the NP6-86 ``FromStation``/``ToStation`` codes
  exactly and carries each station's ``SETTLEMENT_LOAD_ZONE`` (LZ_WEST / LZ_NORTH
  / LZ_SOUTH / LZ_HOUSTON).

A SCED binding row (``ShadowPrice > 0``) is attributed to the **West Texas
Export wind corridor** when either monitored station sits in ``LZ_WEST`` (a
138/345 kV element) OR the constraint is a West/Panhandle export GTC (``WESTEX``
or ``PNHNDL``). LZ_WEST maps to the Permian / CREZ / West Texas Export geography
with precision 1.00 against independent HIFLD substation coordinates (every top
West binder — ODEHV, VEALMOOR, KNAPP, SCRCV, RILEY … — resolves to LZ_WEST;
every top South-Texas binder — RIOHONDO, LAREDO, CATARINA, DILLEY … — to
LZ_SOUTH and is correctly excluded). This is a **structural** definition (all
LZ_WEST-attributed binders), NOT a top-N cutoff, so it regenerates identically
every year.

The ~5-minute SCED intervals are stamped in Central *Prevailing* Time (the
NP6-86 ``SCEDTimeStamp``), with the report's own ``RepeatedHourFlag``
disambiguating the fall-back repeat; they are converted CPT -> CST (fixed
UTC-6, the model clock — reusing ``build_ercot_hsl._prevailing_to_standard``)
BEFORE placement, then aggregated onto the fixed non-leap 8760-hour ERCOT-local
**standard**-time clock (Feb 29 dropped — the convention shared with the
``ercot-hsl`` / ORDC / ercot-AS series after the 2026-07-07 clock-unification
round; ``docs/handoffs/ercot-g22-demand-side-design-2026-07.md`` §7). The
pre-fix build placed the prevailing stamps unconverted, shifting the summer
binding-frequency hour cells one hour late. Output is DENSE: one row per local
clock hour, carrying how many SCED executions ran,
how many had at least one West-corridor constraint binding (and the resulting
congestion fraction), the interface-only binding fraction, and the mean positive
West shadow price.

Rule #13/#14 admissibility: this is measured ERCOT SCED transmission-congestion
incidence — a reproducible market/physical INPUT that regenerates every year and
responds to changed grid conditions (more West VRE build -> deeper net-load
troughs -> more corridor congestion). Nothing here reads the model's dispatch,
prices, or the reported HSL curtailment totals (the [3e] VALIDATION target). It
is the identification source for the forward-admissible VRE curtailment-share
driver, NEVER fit to the curtailment volume or a price residual.

Writes one Parquet per calendar year via
:func:`scripts.lib.clean_io.write_clean` (``iso="ERCOT"``, ``year=<year>``).
Idempotent; reads only ``data/raw``.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from scripts.build_ercot_hsl import _prevailing_to_standard  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

DATATYPE = "ercot-wtx-congestion"
TRANSMISSION_SUBDIR = "iso-specific-transmission"
NP686_GLOB = "SCEDBTCNP686_SCEDBTCNP686_*.parquet"
SPL_SUBDIR = "ercot-settlement-points"
SPL_GLOB = "SP_List_and_EB_Mapping_*.zip"

# The West Texas Export settlement load zone (ERCOT NP4-160). LZ_WEST is the
# Permian / CREZ / West Texas Export commercial zone; validated precision 1.00
# vs HIFLD coordinate geography for the wind corridor.
WEST_LOAD_ZONE = "LZ_WEST"
# West/Panhandle export GTCs (empty FromStation aggregate interfaces). Already
# modeled at their measured limits (constants.ERCOT_GTC_LINK_MAP) but included so
# the corridor-congestion signal spans both the interface and the nodal tail.
INTERFACE_GTCS = ("WESTEX", "PNHNDL")
# Monitored-element voltages that carry West wind out of the corridor.
CORRIDOR_KV = (138.0, 345.0)

HOURS_PER_YEAR = 8760

# NP6-86 columns consumed. ``RepeatedHourFlag`` disambiguates the DST fall-back
# repeated hour for the CPT->CST conversion (read defensively — absent in some
# legacy archive vintages, in which case the ambiguous repeat drops to NaT).
_NP686_COLS = [
    "SCEDTimeStamp",
    "RepeatedHourFlag",
    "ConstraintName",
    "ShadowPrice",
    "FromStation",
    "ToStation",
    "FromStationkV",
    "ToStationkV",
]


def _sced_ts_to_cst(df: pd.DataFrame) -> pd.Series:
    """Convert the NP6-86 Central-Prevailing SCED stamps to the fixed CST clock.

    ``SCEDTimeStamp`` is Central Prevailing Time; ``RepeatedHourFlag`` (``Y``
    on the second occurrence of the fall-back repeated hour) disambiguates the
    ambiguous repeat. Rows whose stamp cannot be placed (an unflagged
    ambiguous repeat / malformed spring-forward row) become NaT and are
    dropped by the caller.
    """
    raw = pd.to_datetime(
        df["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    flag = df["RepeatedHourFlag"] if "RepeatedHourFlag" in df.columns else None
    return _prevailing_to_standard(raw, flag)


def load_substation_zone(raw_root: Path) -> dict[str, str]:
    """Return the ``SUBSTATION -> SETTLEMENT_LOAD_ZONE`` map from the SPL bundle.

    Reads the newest ``SP_List_and_EB_Mapping_*.zip`` under
    ``data/raw/ercot-settlement-points`` and pulls the ``Settlement_Points_*.csv``
    member. When a substation carries rows in more than one load zone (a handful
    of tie stations) the modal zone is kept — the dominant commercial assignment.
    """
    spl_dir = raw_root / SPL_SUBDIR
    zips = sorted(spl_dir.glob(SPL_GLOB))
    if not zips:
        raise FileNotFoundError(
            f"no {SPL_GLOB} under {spl_dir} — see its README.md (ERCOT NP4-160-SG)"
        )
    bundle = zips[-1]  # newest weekly Model DB Load
    with zipfile.ZipFile(bundle) as zf:
        member = next(
            (
                n
                for n in zf.namelist()
                if "Settlement_Points" in n and n.endswith(".csv")
            ),
            None,
        )
        if member is None:
            raise ValueError(f"{bundle} has no Settlement_Points_*.csv member")
        sp = pd.read_csv(io.BytesIO(zf.read(member)))
    sp = sp.dropna(subset=["SUBSTATION", "SETTLEMENT_LOAD_ZONE"])
    zone = (
        sp.groupby("SUBSTATION")["SETTLEMENT_LOAD_ZONE"]
        .agg(lambda s: s.mode().iloc[0])
        .to_dict()
    )
    return {str(k): str(v) for k, v in zone.items()}


def _west_corridor_mask(binding: pd.DataFrame, sub2zone: dict[str, str]) -> pd.Series:
    """Boolean mask: binding rows attributed to the West Texas Export corridor.

    A row qualifies when it is a WESTEX/PNHNDL export GTC, or a 138/345 kV
    monitored element with either station in the LZ_WEST settlement zone.
    """
    fz = binding["FromStation"].map(sub2zone)
    tz = binding["ToStation"].map(sub2zone)
    kv = binding["FromStationkV"].isin(CORRIDOR_KV) | binding["ToStationkV"].isin(
        CORRIDOR_KV
    )
    is_iface = binding["ConstraintName"].isin(INTERFACE_GTCS)
    west_nodal = kv & ((fz == WEST_LOAD_ZONE) | (tz == WEST_LOAD_ZONE))
    return is_iface | west_nodal


def _calendar_position() -> pd.Series:
    """Series mapping ``(month, day, hour) -> 0..8759`` on the non-leap clock."""
    cal = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    return pd.Series(
        np.arange(HOURS_PER_YEAR, dtype="int64"),
        index=pd.MultiIndex.from_arrays(
            [cal.month, cal.day, cal.hour], names=["month", "day", "hr"]
        ),
    )


def _to_hourly(df: pd.DataFrame, sub2zone: dict[str, str], year: int) -> pd.DataFrame:
    """Aggregate one year's NP6-86 rows to the hourly West-corridor signal."""
    df = df.assign(ts=_sced_ts_to_cst(df))
    df = df[
        (df["ts"].dt.year == year)
        & ~((df["ts"].dt.month == 2) & (df["ts"].dt.day == 29))
        & df["ts"].notna()
    ]
    if df.empty:
        return pd.DataFrame()

    df = df.assign(month=df["ts"].dt.month, day=df["ts"].dt.day, hr=df["ts"].dt.hour)
    binding = df["ShadowPrice"] > 0
    is_west = _west_corridor_mask(df, sub2zone) & binding
    is_iface = df["ConstraintName"].isin(INTERFACE_GTCS) & binding

    # n_intervals: distinct SCED executions observed per clock hour (any constraint).
    grp_cols = ["month", "day", "hr"]
    n_intervals = df.groupby(grp_cols)["ts"].nunique().rename("n_intervals")
    # n_binding_west: distinct executions with >=1 West-corridor constraint binding.
    n_binding_west = (
        df[is_west].groupby(grp_cols)["ts"].nunique().rename("n_binding_west")
    )
    n_iface = df[is_iface].groupby(grp_cols)["ts"].nunique().rename("n_iface")
    # mean positive West shadow price over the hour's binding West-corridor rows.
    sp_west = (
        df[is_west]
        .groupby(grp_cols)["ShadowPrice"]
        .mean()
        .rename("shadow_price_mean_west")
    )

    out = pd.concat(
        [n_intervals, n_binding_west, n_iface, sp_west], axis=1
    ).reset_index()
    out["n_binding_west"] = out["n_binding_west"].fillna(0).astype("int64")
    out["n_iface"] = out["n_iface"].fillna(0).astype("int64")
    out["n_intervals"] = out["n_intervals"].astype("int64")

    pos = _calendar_position()
    key = pd.MultiIndex.from_frame(out[["month", "day", "hr"]])
    out["hour"] = pos.reindex(key).to_numpy()
    out = out[out["hour"].notna()].copy()
    out["hour"] = out["hour"].astype("int64")

    # Densify to the full 8760 clock: hours with no observed SCED coverage carry
    # zero congestion (n_intervals 0 -> congestion_frac 0), never a fabricated
    # binding-hour envelope.
    dense = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype="int64")})
    out = dense.merge(out, on="hour", how="left")
    out["n_intervals"] = out["n_intervals"].fillna(0).astype("int64")
    out["n_binding_west"] = out["n_binding_west"].fillna(0).astype("int64")
    out["n_iface"] = out["n_iface"].fillna(0).astype("int64")

    denom = out["n_intervals"].to_numpy()
    safe = np.where(denom > 0, denom, 1)
    out["congestion_frac"] = np.where(
        denom > 0, out["n_binding_west"].to_numpy() / safe, 0.0
    )
    out["interface_binding_frac"] = np.where(
        denom > 0, out["n_iface"].to_numpy() / safe, 0.0
    )

    # Non-leap wall clock: build from the 2023 template's month/day/hour applied to
    # this year (Feb 29 already excluded by construction of the 8760 grid).
    tmpl = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    out["interval_start_local"] = pd.to_datetime(
        {
            "year": year,
            "month": tmpl.month,
            "day": tmpl.day,
            "hour": tmpl.hour,
        }
    )
    out["iso"] = "ERCOT"
    return out[
        [
            "iso",
            "hour",
            "interval_start_local",
            "n_intervals",
            "n_binding_west",
            "congestion_frac",
            "interface_binding_frac",
            "shadow_price_mean_west",
        ]
    ].sort_values("hour", ignore_index=True)


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Curate every NP6-86 archive year into the West-corridor congestion signal.

    ``raw_root`` overrides ``data/raw`` for tests; ``isos`` is accepted for
    orchestrator symmetry (the product is ERCOT-only — anything not including
    ERCOT is a no-op). Returns the written clean paths.
    """
    if isos is not None and "ERCOT" not in [i.upper() for i in isos]:
        return []
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    archives = sorted((raw_root / TRANSMISSION_SUBDIR).glob(NP686_GLOB))
    # Skip the tiny DST-supplement (xhr) / retry side-files; the main per-year
    # archives carry the full record and are deduplicated below.
    archives = [
        p for p in archives if "_xhr_" not in p.name and "_retry_" not in p.name
    ]
    if not archives:
        print(f"no {NP686_GLOB} under {raw_root / TRANSMISSION_SUBDIR}")
        return []

    sub2zone = load_substation_zone(raw_root)

    # RepeatedHourFlag is absent in some legacy archive vintages and in the
    # test fixture; read whatever subset of the consumed columns each archive
    # actually carries (a missing flag column just means its fall-back repeat
    # rows drop to NaT in the CPT->CST conversion).
    def _read(p: Path) -> pd.DataFrame:
        have = set(pq.ParquetFile(p).schema.names)
        return pd.read_parquet(p, columns=[c for c in _NP686_COLS if c in have])

    frames = [_read(p) for p in archives]
    rows = pd.concat(frames, ignore_index=True).drop_duplicates(ignore_index=True)
    years = (
        pd.to_datetime(
            rows["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
        )
        .dt.year.dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    source = "; ".join(
        [f"data/raw/{TRANSMISSION_SUBDIR}/{p.name}" for p in archives]
        + [
            f"data/raw/{SPL_SUBDIR} (NP4-160-SG SUBSTATION->SETTLEMENT_LOAD_ZONE)",
            "ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission Constraints",
        ]
    )
    written: list[Path] = []
    for year in sorted(years):
        hourly = _to_hourly(rows, sub2zone, int(year))
        if hourly.empty:
            continue
        path = write_clean(hourly, DATATYPE, iso="ERCOT", year=int(year), source=source)
        validate_clean(path)
        written.append(path)
        cf = hourly["congestion_frac"]
        print(
            f"{year}: {len(hourly)} hours, mean congestion_frac={cf.mean():.3f}, "
            f"hours>0={int((cf > 0).sum())} -> {path}"
        )
    return written


def main() -> None:
    """CLI entry point: curate the archives under ``data/raw`` (or an override)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-root", default=None, help="Override the data/raw root (for testing)."
    )
    args = ap.parse_args()
    written = curate(raw_root=args.raw_root)
    if not written:
        raise SystemExit(1)
    print(f"wrote {len(written)} clean year file(s)")


if __name__ == "__main__":
    main()
