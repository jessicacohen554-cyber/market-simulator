"""CHP (combined heat and power) behind-the-meter percentages, Pmin CFs, and overrides.

Extracted from :mod:`market_sim.data.fleet` — CHP-specific data functions
that size the behind-the-meter host-steam pull-out and must-run floors for
gas and coal cogens across ISOs.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import pandas as pd

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CHP flag from EIA-860
# ---------------------------------------------------------------------------

# Per-year CHP designation parquet (under _processed-legacy). When
# present it lets a multi-year backcast bucket each year with its own vintage's
# CHP designation instead of the single committed snapshot.
EIA_860_CHP_BY_YEAR_NAME: str = "eia860_chp_by_year.parquet"


@lru_cache(maxsize=8)
def _chp_by_plant(eia860_dir, year: int | None = None) -> "pd.Series":
    """Return ``{plant_id: "Y"/"N"}`` plant-level CHP flag from EIA-860.

    With ``year`` set and the per-year lookup
    (:data:`EIA_860_CHP_BY_YEAR_NAME`, under ``data/raw/_processed-legacy``) present, the
    flag is read from THAT year's EIA-860 release, so a 3-year backcast does not
    classify 2023/2024 with the latest snapshot's cogen status. Falls back to
    the single committed operable-generator sheet (the most recent vintage) when
    no year is given, the per-year lookup is missing, or the year is absent from
    it. A plant is CHP when *any* of its operable units is flagged. Empty series
    when no source exists, so callers default every plant to non-CHP.
    """
    from pathlib import Path

    eia860_dir = Path(eia860_dir)
    if year is not None:
        by_year = PROCESSED_DIR / EIA_860_CHP_BY_YEAR_NAME
        if by_year.exists():
            df = pd.read_parquet(by_year)
            sub = df[df["year"] == int(year)]
            if not sub.empty:
                return pd.Series(
                    sub["chp"].to_numpy(), index=sub["plant_id"].to_numpy()
                )
    path = eia860_dir / "eia860_generator_operable.parquet"
    col = "Associated with Combined Heat and Power System"
    if not path.exists():
        return pd.Series(dtype="object")
    raw = pd.read_parquet(path, columns=["Plant Code", col])
    is_y = raw[col].astype(str).str.strip().str.upper().str.startswith("Y")
    return is_y.groupby(raw["Plant Code"]).any().map({True: "Y", False: "N"})


# ---------------------------------------------------------------------------
# CAISO CHP steam-credit heat-rate correction
# ---------------------------------------------------------------------------


def _correct_caiso_chp_steam_credit_hr(generators: list, iso: str) -> None:
    """Correct steam-credited heat rates for all CAISO CHP plants (in place).

    CT_CHP: all simple-cycle CHP gas turbines report a steam-credited HR that
    is physically impossible on a power-only basis (< 8.0 MMBtu/MWh).  The
    1.8× topping factor (same as the original EOR-only fix) restores the
    power-only HR, landing these units at 9–11 MMBtu/MWh in the peaker band.

    CC_CHP: combined-cycle CHP plants carry a smaller steam credit from
    process-steam extraction.  Plants with HR below 6.0 (under the most
    efficient CC class) get a 1.15× correction with a 6.3 floor.
    """
    from market_sim.data.fleet import (
        CAISO_CHP_CC_STEAM_CREDIT_FACTOR,
        CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
        CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD,
        CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD,
        CAISO_EOR_TOPPING_FACTOR,
    )

    if iso.upper() != "CAISO":
        return
    for gen in generators:
        if gen.plant_group == "CT_CHP":
            if gen.heat_rate < CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD:
                gen.heat_rate *= CAISO_EOR_TOPPING_FACTOR
        elif gen.plant_group == "CC_CHP":
            if gen.heat_rate < CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD:
                gen.heat_rate = max(
                    gen.heat_rate * CAISO_CHP_CC_STEAM_CREDIT_FACTOR,
                    CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
                )


# ---------------------------------------------------------------------------
# CHP overrides from derived thermal-tranche artifacts
# ---------------------------------------------------------------------------


@lru_cache(maxsize=8)
def measured_btm_share_by_plant(iso: str) -> dict[int, float]:
    """Return ``{plant_code: measured BTM host-share}`` from the ``chp-btm-share`` artifact.

    The per-plant measured replacement for the sector-keyed
    :func:`chp_btm_pct` default (:mod:`scripts.curate_chp_btm_share`): the
    fraction of the plant's EIA-923 net class generation that never reaches
    CAMPD's CEMS-metered grid-net total, pooled across every available
    non-quarantined year. Both sides are measured and independent of the
    model's own dispatch, so this regenerates identically for a forward year
    (CLAUDE.md rule 13) -- forecast-only source; the backcast BTM add-back
    (``scripts/run_calibration_full.py::_btm_frame``) is unchanged and keeps
    using the sector-keyed share.

    Returns an empty map when the clean partition is absent (curation not yet
    run for this ISO / ``scripts.lib.clean_io`` unavailable) or empty, so the
    caller falls back to :func:`chp_btm_pct`.
    """
    try:
        from scripts.lib.clean_io import clean_exists, read_clean
    except ModuleNotFoundError:
        logger.warning("chp-btm-share: scripts.lib.clean_io unavailable")
        return {}
    if not clean_exists("chp-btm-share", iso=iso.upper()):
        return {}
    df = read_clean("chp-btm-share", iso=iso.upper(), validate=False)
    if df.empty:
        return {}
    return {
        int(pid): float(share) for pid, share in zip(df["plant_id"], df["btm_share"])
    }


@lru_cache(maxsize=8)
def chp_overrides(iso: str) -> dict[int, tuple[float | None, str | None, float | None]]:
    """Return ``{plant_code: (chp_pmin_cf, sector_class, btm_pct_override)}`` for an ISO.

    The per-ISO CHP steam-following data from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (written by
    ``scripts/derive_thermal_tranches.py``): the plant's total must-run floor
    (CAMPD p2 available-CF where CEMS covers the plant, EIA-923 class CF
    otherwise — see the row's ``status``), its EIA-923 sector class
    (merchant / industrial / commercial) sizing the behind-the-meter share,
    and an optional per-plant ``chp_btm_pct`` override (% of nameplate) that
    supersedes the sector-keyed :data:`CHP_BTM_PCT_BY_SECTOR` default when
    measured grid-delivery data shows the sector default is mis-sized for that
    plant (e.g. a large industrial cogen whose host consumes a higher-than-sector-
    average share of output). The override is populated by the Step-5 CAISO CHP
    re-derivation (Lever C) and is absent for ISOs without such a column.
    This is the ISO-generic analogue of the hardcoded ERCOT maps
    :data:`CHP_PMIN_CF_BY_PLANT` / :data:`CHP_SECTOR_CLASS_BY_PLANT`; empty
    when the ISO has no artifact or it predates the CHP columns.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "chp_pmin_cf" not in df.columns:
        return {}
    out: dict[int, tuple[float | None, str | None, float | None]] = {}
    for r in df.itertuples(index=False):
        pmin = getattr(r, "chp_pmin_cf", None)
        sector = getattr(r, "chp_sector", None)
        sector = str(sector) if isinstance(sector, str) and sector else None
        btm_raw = getattr(r, "chp_btm_pct", None)
        btm = float(btm_raw) if btm_raw is not None and not pd.isna(btm_raw) else None
        if pd.isna(pmin) and sector is None:
            continue
        out[int(r.plant_code)] = (
            None if pd.isna(pmin) else float(pmin),
            sector,
            btm,
        )
    return out


# ---------------------------------------------------------------------------
# Behind-the-meter percentage and Pmin CF
# ---------------------------------------------------------------------------


def chp_btm_pct(plant_code: int, group: str, iso: str = "ERCOT") -> float:
    """Behind-the-meter pull-out share (% of nameplate) for a CHP plant.

    Per-plant override from the ISO's derived artifact takes precedence when the
    ``chp_btm_pct`` column is populated (e.g. CAISO industrial plants whose
    measured grid delivery is below 30% of nameplate). Falls back to the
    sector-keyed :data:`CHP_BTM_PCT_BY_SECTOR` default.
    """
    from market_sim.data.fleet import (
        CHP_BTM_PCT_BY_SECTOR,
        CHP_SECTOR_CLASS_BY_PLANT,
        CHP_ST_BTM_PCT,
    )

    _, sector, btm_override = chp_overrides(iso).get(
        int(plant_code), (None, None, None)
    )
    if btm_override is not None:
        return btm_override
    if sector is None:
        sector = CHP_SECTOR_CLASS_BY_PLANT.get(int(plant_code))
    if sector is None:
        return (
            CHP_ST_BTM_PCT if group == "ST_CHP" else (CHP_BTM_PCT_BY_SECTOR["merchant"])
        )
    if group == "ST_CHP" and iso.upper() == "ERCOT":
        return CHP_ST_BTM_PCT
    return CHP_BTM_PCT_BY_SECTOR.get(sector, CHP_BTM_PCT_BY_SECTOR["merchant"])


@lru_cache(maxsize=8)
def chp_class_netgen_mwh(year: int) -> dict[tuple[int, str], float]:
    """Return ``{(plant_id, klass): annual net MWh}`` from EIA-923 for ``year``.

    Per-(plant, class) EIA-923 Page-1 net generation, bucketed by the canonical
    :func:`market_sim.config.plant_taxonomy.classify_plant` (the same taxonomy
    the fleet and the calibration benchmark use). Feeds the measured
    steam-following export floor
    (``ScenarioConfig.chp_export_floor_measured``): a cogen's total measured
    class CF for the year — its host-steam-driven operating level — times its
    grid-delivery share (1 − :func:`chp_btm_pct`) is the grid export the steam
    contract sustains. Keyed per class so a plant that splits across classes
    (a merchant CC block plus a CHP train) cannot lend one class's output to
    another. Empty for a year absent from the EIA-923 artifact.
    """
    from market_sim.config.plant_taxonomy import classify_plant
    from market_sim.data.eia923 import load_monthly_generation

    gen = load_monthly_generation()
    gen = gen[gen["year"] == int(year)]
    if gen.empty:
        return {}
    klass = [
        classify_plant(f, pm, str(c).upper().startswith("Y"), int(pid))
        for f, pm, c, pid in zip(
            gen["fuel_type"], gen["prime_mover"], gen["chp"], gen["plant_id"]
        )
    ]
    totals = gen.groupby(
        [gen["plant_id"].astype(int), pd.Series(klass, index=gen.index)]
    )["netgen_annual_mwh"].sum()
    return {(int(pid), str(k)): float(v) for (pid, k), v in totals.items() if v > 0.0}


def chp_pmin_cf(plant_code: int, iso: str = "ERCOT") -> float | None:
    """Total must-run CF floor (%) for a CHP plant, or ``None`` for no floor.

    Per-ISO derived artifact first (:func:`chp_overrides`), then the hardcoded
    ERCOT CAMPD map (:data:`CHP_PMIN_CF_BY_PLANT`).
    """
    from market_sim.data.fleet import CHP_PMIN_CF_BY_PLANT

    pmin, *_ = chp_overrides(iso).get(int(plant_code), (None, None, None))
    if pmin is not None:
        return pmin
    return CHP_PMIN_CF_BY_PLANT.get(int(plant_code))
