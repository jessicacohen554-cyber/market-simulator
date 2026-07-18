"""Curate the ``chp-btm-share`` clean datatype: measured CHP host self-supply.

Replaces the sector-keyed default (:func:`market_sim.data.chp.chp_btm_pct`)
with a directly measured, per-plant behind-the-meter host share, per
(plant, CHP class)::

    btm_share = (eia923_net_mwh - campd_net_mwh) / eia923_net_mwh

``eia923_net_mwh`` is the plant-class's EIA-923 Page-1 filed net generation
(gross minus station service — includes the host's on-site self-consumption).
``campd_net_mwh`` is the same plant-class's CAMPD CEMS grid-net generation
(already net of parasitic/station-service load, via the committed
``plant_emission_rates_v2`` artifact), summed **only over CEMS units that
report steam load** (``steam_load_klbh_sum > 0`` — the CHP signature
:func:`market_sim.results.emissions.measured_class_cf` also keys off, so the
two measured CHP factors agree on which units are "the cogen").

Both sides are measured, reproducible quantities that regenerate for a
forward year and respond to changed unit composition (CLAUDE.md rule 13);
neither depends on the model's own dispatch. Rows are pooled across every
available non-quarantined year (2022 and 2026 excluded, CLAUDE.md rule 22) for
stability, then clipped to [0, 1].

Sources (both already-committed, derived-legacy artifacts under
``data/raw/_processed-legacy``, read directly — no new raw intake):
``plant_emission_rates_v2.parquet`` (CAMPD, from
``scripts/data/derive_plant_emissions_v2.py``) and
``eia923_monthly_generation.parquet`` (EIA-923, from
``scripts/data/process_f923_fuel_costs.py``). Writes one Parquet partition per ISO
via the frozen :func:`scripts.lib.clean_io.write_clean` seam. Idempotent;
reads only ``data/raw``.

Usage:
    python scripts/data/curate_chp_btm_share.py                  # all ISOs
    python scripts/data/curate_chp_btm_share.py --isos ERCOT CAISO
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import classify_plant
from market_sim.results.emissions import _chp_group_from_unit_type
from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "chp-btm-share"

# CHP classes this datatype covers (the gas cogen bins the must-run
# reconstruction sizes; coal cogens use a separate sector-share treatment).
_CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")

# Years under full holdout quarantine — never intaken (CLAUDE.md rule 22).
_QUARANTINED_YEARS = frozenset({2022, 2026})

_V2_RELPATH = Path("_processed-legacy") / "plant_emission_rates_v2.parquet"
_GEN_RELPATH = Path("_processed-legacy") / "eia923_monthly_generation.parquet"

_COLUMNS = [
    "iso",
    "plant_id",
    "plant_group",
    "eia923_net_mwh",
    "campd_net_mwh",
    "btm_share",
    "steam_load_klbh_sum",
    "n_years",
    "first_year",
    "last_year",
]


def _campd_grid_net(v2: pd.DataFrame) -> pd.DataFrame:
    """Return per-(iso, plant_id, plant_group, year) CAMPD grid-net generation.

    Restricted to CEMS units reporting steam load (the CHP signature); a unit
    without one is not part of any cogen's measured host self-supply.
    """
    df = v2[v2["steam_load_klbh_sum"].astype(float) > 0.0].copy()
    df["plant_group"] = df["unit_type"].map(_chp_group_from_unit_type)
    df = df[df["plant_group"].isin(_CHP_GROUPS)]
    if df.empty:
        return pd.DataFrame(
            columns=[
                "iso",
                "plant_id",
                "plant_group",
                "year",
                "campd_net_mwh",
                "steam_load_klbh_sum",
            ]
        )
    out = (
        df.groupby(["iso", "plant_id", "plant_group", "year"], observed=True)
        .agg(
            campd_net_mwh=("net_mwh", "sum"),
            steam_load_klbh_sum=("steam_load_klbh_sum", "sum"),
        )
        .reset_index()
    )
    return out


def _eia923_class_net(gen: pd.DataFrame) -> pd.DataFrame:
    """Return per-(plant_id, plant_group, year) EIA-923 net class generation.

    Uses the same canonical taxonomy (:func:`classify_plant`) the fleet and
    calibration benchmark use, so a plant's class here matches its class on
    the CAMPD side.
    """
    df = gen.copy()
    df["plant_group"] = [
        classify_plant(f, pm, str(c).upper().startswith("Y"), int(pid))
        for f, pm, c, pid in zip(
            df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
        )
    ]
    df = df[df["plant_group"].isin(_CHP_GROUPS)]
    if df.empty:
        return pd.DataFrame(
            columns=["plant_id", "plant_group", "year", "eia923_net_mwh"]
        )
    out = (
        df.groupby(["plant_id", "plant_group", "year"], observed=True)[
            "netgen_annual_mwh"
        ]
        .sum()
        .reset_index()
        .rename(columns={"netgen_annual_mwh": "eia923_net_mwh"})
    )
    return out


def build(v2: pd.DataFrame, gen: pd.DataFrame) -> pd.DataFrame:
    """Return the full (all-ISO) ``chp-btm-share`` frame from the two sources.

    Joins the CAMPD steam-reporting grid-net total and the EIA-923 net class
    total on ``(plant_id, plant_group, year)``, drops quarantined years and
    years without both sides, then pools across the remaining years per
    ``(iso, plant_id, plant_group)`` before computing the share.
    """
    v2 = v2[~v2["year"].isin(_QUARANTINED_YEARS)]
    gen = gen[~gen["year"].isin(_QUARANTINED_YEARS)]

    campd = _campd_grid_net(v2)
    eia923 = _eia923_class_net(gen)
    if campd.empty or eia923.empty:
        return pd.DataFrame(columns=_COLUMNS)

    merged = campd.merge(eia923, on=["plant_id", "plant_group", "year"], how="inner")
    merged = merged[merged["eia923_net_mwh"] > 0.0]
    if merged.empty:
        return pd.DataFrame(columns=_COLUMNS)

    pooled = (
        merged.groupby(["iso", "plant_id", "plant_group"], observed=True)
        .agg(
            eia923_net_mwh=("eia923_net_mwh", "sum"),
            campd_net_mwh=("campd_net_mwh", "sum"),
            steam_load_klbh_sum=("steam_load_klbh_sum", "sum"),
            n_years=("year", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
    )
    pooled["btm_share"] = np.clip(
        (pooled["eia923_net_mwh"] - pooled["campd_net_mwh"]) / pooled["eia923_net_mwh"],
        0.0,
        1.0,
    )
    pooled["plant_id"] = pooled["plant_id"].astype("int64")
    pooled["n_years"] = pooled["n_years"].astype("int64")
    pooled["first_year"] = pooled["first_year"].astype("int64")
    pooled["last_year"] = pooled["last_year"].astype("int64")
    return (
        pooled[_COLUMNS]
        .sort_values(["iso", "plant_id", "plant_group"])
        .reset_index(drop=True)
    )


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Curate and write every requested ISO's ``chp-btm-share`` partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory holding the two source parquets under
        ``_processed-legacy``.
    isos:
        Subset of ISOs to write (default: every ISO present in the merged
        frame). An ISO with no covered plants is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    v2_path = raw_root / _V2_RELPATH
    gen_path = raw_root / _GEN_RELPATH
    if not v2_path.is_file() or not gen_path.is_file():
        print(f"[skip] chp-btm-share: missing source(s) — {v2_path} / {gen_path}")
        return []

    v2 = pd.read_parquet(v2_path)
    gen = pd.read_parquet(gen_path)
    full = build(v2, gen)
    if full.empty:
        print("[skip] chp-btm-share: no covered (plant, class, year) rows")
        return []

    wanted = [i.upper() for i in isos] if isos else sorted(full["iso"].unique())
    written: list[Path] = []
    for iso in wanted:
        sub = full[full["iso"] == iso].reset_index(drop=True)
        if sub.empty:
            print(f"[skip] {iso}: no covered plants")
            continue
        path = clean_io.write_clean(
            sub,
            DATATYPE,
            iso=iso,
            year=None,
            source=f"{_V2_RELPATH} + {_GEN_RELPATH}",
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(sub)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: every ISO covered by the source data)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
