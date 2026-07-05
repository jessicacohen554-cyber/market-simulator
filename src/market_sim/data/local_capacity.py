"""Local-capacity (LCR-area) dispatch constraint inputs.

Builds the inputs for the LP's local-capacity minimum-generation rows
(``model/dispatch._build_local_capacity_rows``, gated by
``ScenarioConfig.local_capacity_constraints``, default off). For each covered
LCR area ``a`` and hour ``t`` the LP enforces::

    sum_{g in area a} P[g,t]
      + storage_frac_a * sum_{s in zone(a)} (Dis[s,t] - Chg[s,t])
      >= max(0, local_load_a[t] - import_cap_a)          (capped, see below)

which is the exact LP relaxation of a sub-zonal (load-pocket) split: the
pocket's energy balance with its boundary import at the study limit, minus
the LMP separation. It binds only in hours where local load exceeds the
import capability — the rule-17 triple (driver = local load, window emerges
from the driver, forward story = each year's published LCR study / load
growth) holds natively. The row's dual subsidizes in-area units' reduced
costs *without* entering the zonal energy-balance dual — out-of-market
commitment, exactly how real local commitments are paid (bid-cost recovery /
RMR / exceptional dispatch), so the zonal hub LMP benchmark is untouched.

Parameters are published-study values only (no fitted degree of freedom):

- ``requirement`` and ``peak_load`` per (area, year) from the
  capacity-deliverability intake
  (``data/raw/capacity-deliverability/<iso>/<iso>.csv``; CAISO LCT report
  tables, cited per row).
- ``import_cap_a = peak_load_a - requirement_a`` — both sides from the same
  study table, so the subtraction is on a consistent boundary.
- ``local_load_a[t] = share_a * zone_demand[t]`` with
  ``share_a = peak_load_a / zone_peak_load`` (the study's own zonal forecast,
  e.g. CAISO Table 3.2-1 SP26), so the pocket load responds to the year's
  actual weather through the zone shape. Documented rule-14 reconciliation:
  the study's substation boundary is approximated by the zonal load shape.
- ``storage_frac_a`` — the in-area share of the zone's storage power capacity
  (EIA-860 storage counties). The LP's storage is zone-aggregated, so in-area
  batteries enter the pocket balance at their measured capacity share; this
  keeps 2024-25 evening battery discharge from being mis-attributed to
  thermal (a second rule-14 reconciliation).

Feasibility guard: the RHS is capped at 99.9% of the in-area *thermal*
capacity (member ``pmax x availability``) — requiring more than physically
exists is meaningless (the real system sheds load / exceptionally imports
there), and the cap is guaranteed by thermal ALONE so the row stays feasible
even during deep in-area outages. Storage is excluded from the guarantee (its
discharge is SOC-limited) but still enters the row's LHS. Pure physics.

Membership comes from ``data/raw/reference/lcr_area_membership_<ISO>.csv``
(``scripts/derive_lcr_membership.py``): county rule + NQC-list overrides.
The area rules live here so the derive script and the storage-share
computation use one implementation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

logger = logging.getLogger(__name__)

LA_BASIN = "LA Basin"
SD_IV = "San Diego/Imperial Valley"

# ---------------------------------------------------------------------------
# Area assignment rules (shared by scripts/derive_lcr_membership.py and the
# storage-share computation below).
# ---------------------------------------------------------------------------

# Counties wholly inside a covered area for CAISO-metered plants (LADWP is a
# separate BA and never enters the fleet).
COUNTY_AREA_CAISO: dict[str, str] = {
    "Los Angeles": LA_BASIN,
    "Orange": LA_BASIN,
    "San Diego": SD_IV,
    "Imperial": SD_IV,
}
# Counties the LA Basin boundary bisects (Devers/Mira Loma IN; Lugo/Red Bluff
# OUT per the LCT report area definition), resolved geographically: south of
# the San Gabriel/Cajon rim AND west of the Red Bluff/Eagle Mountain desert.
BOUNDARY_COUNTIES_CAISO: frozenset[str] = frozenset({"Riverside", "San Bernardino"})
BOUNDARY_LAT_MAX = 34.35
BOUNDARY_LON_MAX = -115.8


def caiso_area_of(county: str, lat: float, lon: float) -> str | None:
    """Return the covered LCR area of a CAISO site, or ``None`` if outside.

    County rule first, then the Riverside/San Bernardino geographic rule.
    Large boundary plants are pinned by the NQC-list override table in
    ``scripts/derive_lcr_membership.py``; this function is the rule the
    override table corrects, and the storage-share approximation.
    """
    if county in COUNTY_AREA_CAISO:
        return COUNTY_AREA_CAISO[county]
    if county in BOUNDARY_COUNTIES_CAISO:
        if (
            not np.isnan(lat)
            and not np.isnan(lon)
            and lat < BOUNDARY_LAT_MAX
            and lon < BOUNDARY_LON_MAX
        ):
            return LA_BASIN
    return None


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LocalCapacityAreaSpec:
    """One covered LCR area: identity + where its published numbers live."""

    name: str  # membership-CSV / display name
    zone: str  # model zone containing the pocket
    csv_area: str  # `area` value of its requirement/peak_load rows
    zone_csv_area: str  # `area` value of the zonal peak_load rows (share denominator)


# Covered areas per ISO. Phase 1: the two SP15 pockets the CAISO evening-CT
# finding names. NYISO in-zone pockets / PJM sub-LDAs can be added as data
# rows + membership CSVs with no code change (design doc §3).
LOCAL_CAPACITY_AREAS: dict[str, tuple[LocalCapacityAreaSpec, ...]] = {
    "CAISO": (
        LocalCapacityAreaSpec(
            name=LA_BASIN, zone="SP15", csv_area="LA Basin", zone_csv_area="SP26"
        ),
        LocalCapacityAreaSpec(
            name=SD_IV,
            zone="SP15",
            csv_area="San Diego/Imperial Valley",
            zone_csv_area="SP26",
        ),
    ),
}


def _capdel_csv(iso: str) -> Path:
    """Path of the ISO's raw capacity-deliverability intake CSV."""
    return RAW_DATA_DIR / "capacity-deliverability" / iso.lower() / f"{iso.lower()}.csv"


def _membership_csv(iso: str) -> Path:
    """Path of the ISO's LCR-area membership crosswalk."""
    return RAW_DATA_DIR / "reference" / f"lcr_area_membership_{iso.upper()}.csv"


def load_lcr_parameters(iso: str, year: int) -> dict[str, dict[str, float]]:
    """Return per-area published LCR parameters for one delivery year.

    Reads the capacity-deliverability intake CSV and returns, per covered
    area name: ``requirement``, ``peak_load``, ``zone_peak_load``,
    ``import_cap`` (= peak_load - requirement) and ``share``
    (= peak_load / zone_peak_load). Areas whose rows are missing for the year
    are omitted (with a log line) rather than guessed.
    """
    specs = LOCAL_CAPACITY_AREAS.get(iso.upper())
    path = _capdel_csv(iso)
    if not specs or not path.exists():
        return {}
    df = pd.read_csv(path)
    df = df[df.delivery_year.astype(str) == str(year)]

    def _value(area: str, metric: str) -> float | None:
        rows = df[(df.area == area) & (df.metric == metric)]
        return float(rows.value_mw.iloc[0]) if len(rows) else None

    out: dict[str, dict[str, float]] = {}
    for spec in specs:
        req = _value(spec.csv_area, "requirement")
        peak = _value(spec.csv_area, "peak_load")
        zone_peak = _value(spec.zone_csv_area, "peak_load")
        if req is None or peak is None or zone_peak is None:
            logger.info(
                "local-capacity: %s %s %s missing requirement/peak_load rows; "
                "area skipped",
                iso,
                year,
                spec.name,
            )
            continue
        out[spec.name] = {
            "zone": spec.zone,
            "requirement_mw": req,
            "peak_load_mw": peak,
            "zone_peak_load_mw": zone_peak,
            "import_cap_mw": peak - req,
            "share": peak / zone_peak,
        }
    return out


def load_lcr_membership(iso: str) -> dict[str, np.ndarray]:
    """Return per-area member EIA plant codes from the committed crosswalk."""
    path = _membership_csv(iso)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {
        str(area): g.plant_id.to_numpy(dtype=int) for area, g in df.groupby("lcr_area")
    }


def storage_area_share(iso: str, area: str, zone: str, year: int) -> float:
    """Return the in-area share of the zone's storage power capacity.

    Measured from the EIA-860 operable storage table (county + operating
    year <= ``year``), assigned by :func:`caiso_area_of`, and normalized by
    the same table's total for plants in the area's *zone*. The share is a
    reconciliation of the LP's zone-aggregated storage onto the pocket, not a
    precise metering split.
    """
    if iso.upper() != "CAISO":
        return 0.0
    path = RAW_DATA_DIR / "eia-860" / "eia860_energy_storage_operable.parquet"
    if not path.exists():
        return 0.0
    s = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "State",
            "County",
            "Nameplate Capacity (MW)",
            "Operating Year",
        ],
    )
    s.columns = ["plant_id", "state", "county", "mw", "op_year"]
    s = s[(s.state == "CA") & (pd.to_numeric(s.op_year, errors="coerce") <= year)]
    s["mw"] = pd.to_numeric(s.mw, errors="coerce").fillna(0.0)
    plants = pd.read_parquet(
        RAW_DATA_DIR / "eia-860" / "eia860_plant.parquet",
        columns=["Plant Code", "Latitude", "Longitude"],
    )
    plants.columns = ["plant_id", "lat", "lon"]
    plants["lat"] = pd.to_numeric(plants.lat, errors="coerce")
    plants["lon"] = pd.to_numeric(plants.lon, errors="coerce")
    s = s.merge(plants.drop_duplicates("plant_id"), on="plant_id", how="left")

    # Zone split on the fleet's Path 15 / Path 26 latitude convention
    # (data/zone_assignment._caiso_zone): SP15 is south of lat 35.0.
    in_zone = s[s.lat < 35.0] if zone == "SP15" else s[s.lat >= 35.0]
    if not len(in_zone) or in_zone.mw.sum() <= 0:
        return 0.0
    areas = in_zone.apply(
        lambda r: caiso_area_of(str(r.county), float(r.lat), float(r.lon)), axis=1
    )
    share = float(in_zone.mw[areas == area].sum() / in_zone.mw.sum())
    return share


def build_local_capacity_specs(
    iso: str,
    year: int,
    fleet_plant_code: np.ndarray,
    pmax: np.ndarray,
    availability: np.ndarray,
    zone_names: list[str],
    demand: np.ndarray,
    storage_zone_idx: np.ndarray | None,
    storage_power_cap: np.ndarray | None,
) -> tuple[list[tuple[np.ndarray, np.ndarray, float, np.ndarray]], dict]:
    """Assemble the per-area LP row specs for one ISO-year.

    Returns ``(specs, meta)`` where ``specs`` is a list of
    ``(thermal_gen_idx, storage_idx, storage_frac, rhs_T)`` tuples for
    :func:`market_sim.model.dispatch.build_constraints` (``local_capacity_specs=``)
    and ``meta`` records each area's resolved parameters. Empty when the ISO
    has no covered areas or the intake rows are absent (identical LP).
    """
    params = load_lcr_parameters(iso, year)
    membership = load_lcr_membership(iso)
    specs: list[tuple[np.ndarray, np.ndarray, float, np.ndarray]] = []
    meta: dict[str, dict] = {}
    if not params or not membership:
        return specs, meta

    plant_code = np.asarray(fleet_plant_code, dtype=int)
    for area, p in params.items():
        members = membership.get(area)
        if members is None or not len(members):
            logger.info("local-capacity: %s has no membership rows; skipped", area)
            continue
        z = zone_names.index(p["zone"])
        gen_idx = np.flatnonzero(np.isin(plant_code, members))
        if not gen_idx.size:
            continue
        rhs = np.clip(
            p["share"] * np.asarray(demand, dtype=float)[z] - p["import_cap_mw"],
            0.0,
            None,
        )

        s_frac = storage_area_share(iso, area, p["zone"], year)
        if (
            storage_zone_idx is not None
            and storage_power_cap is not None
            and s_frac > 0
        ):
            s_idx = np.flatnonzero(np.asarray(storage_zone_idx, dtype=int) == z)
        else:
            s_idx = np.zeros(0, dtype=int)
            s_frac = 0.0

        # Feasibility guard: cap RHS at 99.9% of in-area THERMAL capacity
        # (guaranteed satisfiable by thermal alone; storage excluded from the
        # guarantee since its discharge is SOC-limited — counting it went
        # infeasible in 2023). Storage still enters the row LHS below.
        avail_cap_t = (
            np.asarray(pmax, dtype=float)[gen_idx, None]
            * np.asarray(availability, dtype=float)[gen_idx, :]
        ).sum(axis=0)
        rhs = np.minimum(rhs, 0.999 * avail_cap_t)

        specs.append((gen_idx, s_idx, s_frac, rhs))
        meta[area] = {
            **{k: v for k, v in p.items()},
            "storage_frac": round(s_frac, 4),
            "n_member_gens": int(gen_idx.size),
            "member_capacity_mw": float(np.asarray(pmax, dtype=float)[gen_idx].sum()),
            "binding_hours_potential": int((rhs > 0).sum()),
        }
        logger.info(
            "local-capacity %s %s: %d member gens (%.0f MW), import_cap %.0f MW, "
            "share %.3f, storage_frac %.3f, RHS>0 in %d hours (max %.0f MW)",
            iso,
            area,
            gen_idx.size,
            meta[area]["member_capacity_mw"],
            p["import_cap_mw"],
            p["share"],
            s_frac,
            meta[area]["binding_hours_potential"],
            float(rhs.max()) if rhs.size else 0.0,
        )
    return specs, meta
