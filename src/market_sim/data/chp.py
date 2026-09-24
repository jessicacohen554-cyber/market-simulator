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


def apply_measured_chp_heat_rates(
    generators: list, iso: str, year: int | None = None
) -> frozenset[int]:
    """Swap in the MEASURED power-only CHP heat rate where it covers (in place).

    Gated by ``ScenarioConfig.measured_chp_heat_rates``; ISO-generic, default
    off, byte-identical off. The rate is the plant's own
    ``(PLHTIAN + CHPCHTI) / PLNGENAN`` from the eGRID vintage the model's
    incumbent ``heat_rate`` already comes from — eGRID's steam-credited
    ``PLHTRT`` with eGRID's own published useful-thermal heat-input allocation
    added back, on the same net-generation denominator. See
    :func:`market_sim.data.fleet.campd_bins.measured_chp_heat_rates` and
    ``scripts/data/derive_chp_power_only_heat_rates.py``.

    Runs BEFORE :func:`_correct_chp_steam_credit_hr` and returns the ``id()``
    set of the generators it repriced, which that function then skips: a plant
    on its own measured rate must never also take the 1.8x hand topping factor
    (rule 19 `[R-ONE-MECH]` — one mechanism per phenomenon; caiso-128 §4
    measured that factor over-correcting CAISO CT_CHP by +40 %). Plants the
    measurement does not reach keep the existing eGRID -> hand-factor chain
    untouched.

    Args:
        generators: The ISO's loaded fleet, mutated in place.
        iso: ISO identifier.
        year: The solve year (F1 D4): its own ``ok`` row wins, else the
            pooled row; ``None`` reads the pooled rows only.

    Returns:
        ``id()`` of every generator whose heat rate was replaced. Empty when
        the ISO has no committed artifact.
    """
    from market_sim.data.fleet import measured_chp_heat_rates

    rates = measured_chp_heat_rates(iso, year)
    if not rates:
        return frozenset()
    touched: set[int] = set()
    for gen in generators:
        rate = rates.get((int(gen.plant_code or 0), gen.plant_group or ""))
        if rate is not None and rate > 0.0:
            gen.heat_rate = rate
            touched.add(id(gen))
    logger.info(
        "%s: measured power-only CHP heat rates applied to %d generator(s) "
        "across %d (plant, class) pair(s)",
        iso,
        len(touched),
        len(rates),
    )
    return frozenset(touched)


def _correct_chp_steam_credit_hr(
    generators: list, iso: str, skip_ids: frozenset[int] = frozenset()
) -> None:
    """Correct steam-credited heat rates for an ISO's CHP gas turbines (in place).

    Applied to the ISOs in
    :data:`market_sim.data.fleet.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` (CAISO,
    PJM). The correction is TURBINE PHYSICS, not a per-ISO residual fit
    (CLAUDE.md rule 24 governs fitted curves, not physical limits): the
    thresholds/factors/floor below are universal power-only heat-rate limits
    that hold in every market, so the same values apply wherever a CHP unit's
    reported HR is sub-physical.

    CT_CHP: all simple-cycle CHP gas turbines report a steam-credited HR that
    is physically impossible on a power-only basis (< 8.0 MMBtu/MWh).  The
    1.8× topping factor (same as the original EOR-only fix) restores the
    power-only HR, landing these units at 9–11 MMBtu/MWh in the peaker band.

    CC_CHP: combined-cycle CHP plants carry a smaller steam credit from
    process-steam extraction.  Plants with HR below 6.0 (under the most
    efficient CC class) get a 1.15× correction with a 6.3 floor.

    (PJM 2026-07-07: reported CHP HRs of CC_CHP ~4.95 / CT_CHP ~6.14 MMBtu/MWh
    are equally sub-physical — this correction stops steam-credited PJM CHP from
    clearing as the cheapest thermal and over-delivering grid energy vs 923.
    MISO 2026-07-08: audited but NOT added — its HRs are equally sub-physical yet
    its CHP does not over-deliver (BTM-dominated, CT_CHP already under-runs), so
    the correction only worsens CT_CHP; see CHP_STEAM_CREDIT_HR_CORRECTION_ISOS.
    ** MISO 2026-07-27 (miso-97): that decision is VACATED — its load-bearing
    premise is REFUTED. Both clauses rested on a BTM share that was itself the
    unsourced CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0 default, because MISO was
    the only ISO with NO chp_sector data at all (its derive ran without the
    uncommitted raw f923 ZIPs and the preserve-prior guard froze the empty
    column). On the now-measured EIA-860 sector shares (CC_CHP 50.9 %, CT_CHP
    65.5 %) CC_CHP — 72 % of MISO CHP energy — OVER-delivers vs EIA-923 by
    +8.1 % ALREADY AT THE OLD DEFAULT and by up to +44 % on the measured share,
    and CT_CHP's under-run is not robust: raising the hold-out rescales LP
    capacity, the steam floor AND the bench subtrahend by the same (1 - s), so
    the model/actual ratio can only move UP (rho >= f). "Only worsens CT_CHP" is
    also exactly the rule-14 [R-ACCURATE] signal to look elsewhere, and rule 1
    [R-STRUCT] forbids rejecting a correct input on residual grounds.
    NOTE the replacement is NOT this function's hand factors: caiso-128 measured
    the 1.8x topping factor OVER-correcting CAISO CT_CHP by +40 % while five
    ISOs sit 12-62 % under, so a universal factor is wrong in both directions at
    once. The designed successor is the plant's own CEMS power-only rate
    (caiso-128 §6), ISO-generic and default-off. Filed, NOT built — it is a
    separate delta from the sector correction (rule 19 [R-ONE-MECH]).
    Full measurement: results/calibration/FINDING-miso97-chp-sector-btm-2026-07.md
    ** MISO/ISO-generic 2026-07-28 (miso-99): the designed successor IS BUILT and
    armable — :func:`apply_measured_chp_heat_rates` /
    ``ScenarioConfig.measured_chp_heat_rates``, default off. Its measurement is
    NOT the CEMS gross route caiso-128 §6(a) specified (that route needs a
    CHP-specific gross->net ratio ``compute_parasitic_factors`` cannot supply —
    FINDING-miso98 §6.1); it is eGRID's OWN published CHP heat-input allocation
    ``CHPCHTI`` added back to ``PLHTIAN`` over the same ``PLNGENAN``, so no
    gross basis is involved at all. Where that measurement covers a plant it
    wins and this hand factor is skipped. **
    NEISO 2026-07-08: audited but NOT added for the SAME reason — its reported HRs
    are equally sub-physical (CC_CHP 55% of cap < 6.0, CT_CHP 79% < 8.0) but its
    CHP does NOT over-deliver: on 2023-2025 the model runs CC_CHP -37..-42% and
    CT_CHP -71/-71/+5% vs the EIA-923 net-gen class total, and CC_CHP is already
    L1-pinned to the delivered-outcome bound. Raising the HR would only push the
    under-running CT_CHP lower, so the correction is not warranted here.)
    """
    from market_sim.data.fleet import (
        CAISO_CHP_CC_STEAM_CREDIT_FACTOR,
        CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
        CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD,
        CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD,
        CAISO_EOR_TOPPING_FACTOR,
        CHP_STEAM_CREDIT_HR_CORRECTION_ISOS,
    )

    if iso.upper() not in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS:
        return
    for gen in generators:
        if id(gen) in skip_ids:
            # Already on its own MEASURED power-only rate
            # (:func:`apply_measured_chp_heat_rates`). Stacking the hand factor
            # on top would be two mechanisms for one phenomenon (rule 19
            # [R-ONE-MECH]) and would double-correct a plant that is already
            # right.
            continue
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
    :func:`chp_btm_pct` default (:mod:`scripts.data.curate_chp_btm_share`): the
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
def chp_overrides(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[int, tuple[float | None, str | None, float | None]]:
    """Return ``{plant_code: (chp_pmin_cf, sector_class, btm_pct_override)}`` for an ISO.

    The per-ISO CHP steam-following data from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (written by
    ``scripts/data/derive_thermal_tranches.py``): the plant's total must-run floor
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
    from market_sim.data.fleet.campd_bins import thermal_tranche_csv_for_iso

    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
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


@lru_cache(maxsize=2)
def measured_chp_btm_pct_nyiso() -> dict[int, float]:
    """Measured NYISO per-plant CHP BTM electric share (% of nameplate).

    The nyiso-147 rule-23 artifact
    ``data/raw/_processed-legacy/chp_btm_share_measured_NYISO.csv``
    (:mod:`scripts.data.derive_nyiso_chp_btm_share`): per plant,
    ``100 x clip(1 - Gold Book net energy / EIA-923 net generation, 0, 1)``
    pooled CY2022-2024 — the plant's own two published meters, so the share
    regenerates every year and responds to changed host arrangements
    (rule 13 [R-MEASURED]). Consumed only under
    ``ScenarioConfig.nyiso_chp_btm_measured`` (NYISO-only, rule 25
    [R-ISO-SCOPE]); a plant absent from the artifact (no Gold Book station —
    a non-market campus/industrial cogen) keeps the :func:`chp_btm_pct`
    sector default. Empty when the artifact is absent, so the caller falls
    back to the default and an armed run without the artifact fails loud in
    the fleet build rather than silently reverting.
    """
    path = PROCESSED_DIR / "chp_btm_share_measured_NYISO.csv"
    if not path.exists():
        logger.warning(
            "nyiso_chp_btm_measured armed but %s is absent — "
            "run scripts/data/derive_nyiso_chp_btm_share.py",
            path,
        )
        return {}
    df = pd.read_csv(path)
    return {int(r.plant_code): float(r.btm_pct) for r in df.itertuples(index=False)}


def chp_btm_pct(
    plant_code: int,
    group: str,
    iso: str = "ERCOT",
    per_unit: bool = False,
    merit_guard: bool = False,
) -> float:
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

    _, sector, btm_override = chp_overrides(iso, per_unit, merit_guard).get(
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


def chp_pmin_cf(
    plant_code: int,
    iso: str = "ERCOT",
    per_unit: bool = False,
    merit_guard: bool = False,
) -> float | None:
    """Total must-run CF floor (%) for a CHP plant, or ``None`` for no floor.

    Per-ISO derived artifact first (:func:`chp_overrides`), then the hardcoded
    ERCOT CAMPD map (:data:`CHP_PMIN_CF_BY_PLANT`).
    """
    from market_sim.data.fleet import CHP_PMIN_CF_BY_PLANT

    pmin, *_ = chp_overrides(iso, per_unit, merit_guard).get(
        int(plant_code), (None, None, None)
    )
    if pmin is not None:
        return pmin
    return CHP_PMIN_CF_BY_PLANT.get(int(plant_code))
