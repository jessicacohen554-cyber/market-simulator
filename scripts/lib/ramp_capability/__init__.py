"""Shared contract for the ``ramp-capability`` clean datatype.

Measured per-plant ramp / fast-start capability, reconciled from two public
sources onto ONE tidy frame declared in
``data/dictionary/schema/ramp-capability.schema.yaml``:

* **EIA-860** Schedule 3.1 ``Time from Cold Shutdown to Full Load`` — the
  respondent-reported start-capability category per generator. ``"10M"``
  (full load within 10 minutes) is the measured per-unit fast-start flag.
* **EPA CAMPD (CEMS)** hourly unit gross load — the measured operating
  envelope: the maximum observed 1-hour increase in plant-level gross load
  (units summed per hour, gap-hours excluded), pooled over
  :data:`POOLED_VINTAGES`.

The per-ISO scoping lives in sibling modules (``pjm.py``, ``miso.py``, ...),
each of which registers an :class:`IsoSpec` via :func:`register` — the spec is
pure scoping (EIA-860 balancing-authority code + CAMPD state list); the
derivation itself is one generic path (:func:`derive_iso`), so shared code
never branches on the ISO name (``docs/adding-new-data-types.md``). Adding an
ISO is a new module + a ``register(...)`` call.

Vintage policy: :data:`POOLED_VINTAGES` is 2023-2025 only. 2022 and 2026 are
the designated holdout periods (CLAUDE.md rule 22) and are never read here.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATATYPE = "ramp-capability"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "plant_code",
    "fast_start_mw",
    "thermal_nameplate_mw",
    "ramp_up_1h_mw",
    "observed_pmax_mw",
    "hours_observed",
    "vintage_span",
    "source_doc",
)

# CAMPD vintages pooled for the CEMS envelope. 2023-2025 = the calibration
# span; 2022 and H1-2026 are the designated holdouts (CLAUDE.md rule 22 — no
# holdout data intake without session-logged owner authorization), so they are
# excluded by construction, matching docs/ramp-locational-design-2026-07.md.
POOLED_VINTAGES: tuple[int, ...] = (2023, 2024, 2025)

# EIA-860 "Time from Cold Shutdown to Full Load" category meaning full load
# within 10 minutes (EIA-860 Layout, Schedule 3.1: 10M | 1H | 12H | OVER).
EIA860_FAST_START_CODE: str = "10M"

# EIA-860 prime movers making up the thermal (combustion/steam) plant
# aggregate FleetArrays.ramp10 covers: steam turbine, simple-cycle and
# combined-cycle gas turbines and their steam parts, single-shaft CC, and
# internal-combustion engines. Nuclear is excluded via its energy source
# (below) — it runs baseload and carries no upward operating reserve in the
# model (fleet.RAMP10_FRAC maps give it 0).
THERMAL_PRIME_MOVERS: frozenset[str] = frozenset(
    {"ST", "GT", "IC", "CA", "CT", "CS", "CC"}
)

# EIA-860 Energy Source 1 code for nuclear, excluded from the thermal
# aggregate (see THERMAL_PRIME_MOVERS note).
_NUCLEAR_ENERGY_SOURCE: str = "NUC"

# Raw file locations relative to the raw root (the immutable source tree).
_EIA860_OPERABLE = "eia-860/eia860_generator_operable.parquet"
_EIA860_GENERATORS = "eia-860/eia860_generators.parquet"
_CAMPD_DIR = "campd-unit-level"

_SOURCE_DOC = (
    "EIA-860 Schedule 3.1 generator table (Time from Cold Shutdown to Full "
    "Load, Nameplate Capacity); EPA CAMPD unit-level hourly emissions/gross-"
    "load extracts (data/raw/campd-unit-level)"
)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative scoping of one ISO's ramp-capability derivation.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean
        partition (e.g. ``"PJM"``, ``"MISO"``).
    ba_code:
        EIA-860 balancing-authority code selecting the ISO's fleet plants
        (``PJM``, ``MISO``, ``NYIS``, ``ISNE``, ``CISO``, ``ERCO``).
    campd_states:
        CAMPD ``{STATE}_{YEAR}.parquet`` extracts to scan for the CEMS
        envelope (the ISO's physical footprint,
        :data:`market_sim.data.campd.ISO_STATES` convention). A listed state
        whose extract is absent is skipped with a note, so coverage widens
        automatically as extracts land.
    """

    iso: str
    ba_code: str
    campd_states: tuple[str, ...]


REGISTRY: dict[str, IsoSpec] = {}

# Sibling modules auto-imported by load_registry; each registers its spec.
_ISO_MODULES: tuple[str, ...] = ("pjm", "miso")


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label and return it."""
    REGISTRY[spec.iso.upper()] = spec
    return spec


def load_registry() -> dict[str, IsoSpec]:
    """Import every per-ISO module and return the populated registry."""
    for mod in _ISO_MODULES:
        importlib.import_module(f"{__name__}.{mod}")
    return REGISTRY


def _eia860_plant_capability(spec: IsoSpec, raw_root: Path) -> pd.DataFrame:
    """Per-plant EIA-860 fast-start / thermal nameplate for one ISO.

    Joins the operable generator table (which carries the ``Time from Cold
    Shutdown to Full Load`` category) to the trimmed generators table (which
    carries the balancing-authority code) on (plant, generator), restricts to
    the ISO's BA and thermal prime movers (nuclear excluded), and aggregates
    to the plant: ``fast_start_mw`` (nameplate sum over ``"10M"`` rows) and
    ``thermal_nameplate_mw`` (nameplate sum over all thermal rows).
    """
    operable_path = raw_root / _EIA860_OPERABLE
    ba_path = raw_root / _EIA860_GENERATORS
    if not operable_path.is_file() or not ba_path.is_file():
        return pd.DataFrame(
            columns=["plant_code", "fast_start_mw", "thermal_nameplate_mw"]
        )
    gens = pd.read_parquet(
        operable_path,
        columns=[
            "Plant Code",
            "Generator ID",
            "Prime Mover",
            "Energy Source 1",
            "Nameplate Capacity (MW)",
            "Time from Cold Shutdown to Full Load",
        ],
    ).rename(
        columns={
            "Plant Code": "plant_code",
            "Generator ID": "generator_id",
            "Prime Mover": "prime_mover",
            "Energy Source 1": "energy_source",
            "Nameplate Capacity (MW)": "nameplate_mw",
            "Time from Cold Shutdown to Full Load": "cold_start_category",
        }
    )
    ba = pd.read_parquet(
        ba_path, columns=["plant_id", "generator_id", "balancing_authority_code"]
    ).rename(columns={"plant_id": "plant_code"})
    ba["plant_code"] = ba["plant_code"].astype("int64")
    gens["plant_code"] = pd.to_numeric(gens["plant_code"], errors="coerce").astype(
        "Int64"
    )
    gens = gens.dropna(subset=["plant_code"])
    gens["plant_code"] = gens["plant_code"].astype("int64")
    merged = gens.merge(ba, on=["plant_code", "generator_id"], how="inner")
    merged = merged[
        (merged["balancing_authority_code"].astype(str) == spec.ba_code)
        & merged["prime_mover"].astype(str).isin(THERMAL_PRIME_MOVERS)
        & (merged["energy_source"].astype(str) != _NUCLEAR_ENERGY_SOURCE)
    ]
    if merged.empty:
        return pd.DataFrame(
            columns=["plant_code", "fast_start_mw", "thermal_nameplate_mw"]
        )
    merged["nameplate_mw"] = pd.to_numeric(merged["nameplate_mw"], errors="coerce")
    is_fast = merged["cold_start_category"].astype(str) == EIA860_FAST_START_CODE
    merged["fast_mw"] = merged["nameplate_mw"].where(is_fast, 0.0)
    out = (
        merged.groupby("plant_code")
        .agg(
            fast_start_mw=("fast_mw", "sum"),
            thermal_nameplate_mw=("nameplate_mw", "sum"),
        )
        .reset_index()
    )
    return out


def _campd_plant_envelope(spec: IsoSpec, raw_root: Path) -> pd.DataFrame:
    """Per-plant CEMS 1-hour up-ramp envelope for one ISO's state extracts.

    For each ``{STATE}_{YEAR}.parquet`` in the spec's state list over
    :data:`POOLED_VINTAGES`: sum unit gross load to plant-hours (offline
    unit-hours are real 0 MW — CAMPD carries the row with null grossLoad),
    diff consecutive timestamps per plant (diffs across a timestamp gap are
    excluded), and keep the pooled maximum positive delta, the observed
    plant pmax, and the observed plant-hour count. Missing extracts are
    skipped (coverage widens as they land).
    """
    campd_dir = raw_root / _CAMPD_DIR
    best: dict[int, dict[str, float]] = {}
    for state in spec.campd_states:
        for year in POOLED_VINTAGES:
            path = campd_dir / f"{state}_{year}.parquet"
            if not path.is_file():
                continue
            df = pd.read_parquet(
                path, columns=["facilityId", "date", "hour", "grossLoad"]
            )
            if df.empty:
                continue
            # Offline unit-hours are present with null grossLoad — a real 0.
            df["grossLoad"] = df["grossLoad"].astype(float).fillna(0.0)
            ts = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
            plant = (
                pd.DataFrame(
                    {
                        "facilityId": df["facilityId"].astype(int),
                        "ts": ts,
                        "grossLoad": df["grossLoad"],
                    }
                )
                .groupby(["facilityId", "ts"], sort=True)["grossLoad"]
                .sum()
                .reset_index()
            )
            for fac, grp in plant.groupby("facilityId"):
                grp = grp.sort_values("ts")
                load = grp["grossLoad"].to_numpy(dtype=float)
                tdelta = grp["ts"].diff().dt.total_seconds().to_numpy()
                dload = np.diff(load)
                consecutive = tdelta[1:] == 3600.0
                up = float(dload[consecutive].max()) if consecutive.any() else 0.0
                rec = best.setdefault(
                    int(fac),
                    {"ramp_up_1h_mw": 0.0, "observed_pmax_mw": 0.0, "hours": 0},
                )
                rec["ramp_up_1h_mw"] = max(rec["ramp_up_1h_mw"], up)
                rec["observed_pmax_mw"] = max(
                    rec["observed_pmax_mw"], float(load.max())
                )
                rec["hours"] += int(len(grp))
    if not best:
        return pd.DataFrame(
            columns=[
                "plant_code",
                "ramp_up_1h_mw",
                "observed_pmax_mw",
                "hours_observed",
            ]
        )
    rows = [
        {
            "plant_code": fac,
            "ramp_up_1h_mw": rec["ramp_up_1h_mw"],
            "observed_pmax_mw": rec["observed_pmax_mw"],
            "hours_observed": rec["hours"],
        }
        for fac, rec in sorted(best.items())
    ]
    return pd.DataFrame(rows)


def derive_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Build the full schema-shaped frame for one registered ISO.

    Outer-joins the EIA-860 plant capability onto the CAMPD envelope so a
    plant with either source gets a row; plants with neither are absent (the
    model falls back to the class-fraction estimate,
    ``fleet.RAMP10_FRAC_BY_GROUP``).
    """
    spec = REGISTRY[iso.upper()]
    eia = _eia860_plant_capability(spec, raw_root)
    cems = _campd_plant_envelope(spec, raw_root)
    if eia.empty and cems.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    merged = eia.merge(cems, on="plant_code", how="outer")
    merged["hours_observed"] = (
        merged.get("hours_observed", pd.Series(dtype=float)).fillna(0).astype("int64")
    )
    vintage_span = f"{POOLED_VINTAGES[0]}-{POOLED_VINTAGES[-1]}"
    out = pd.DataFrame(
        {
            "iso": spec.iso,
            "plant_code": merged["plant_code"].astype("int64"),
            "fast_start_mw": merged.get("fast_start_mw", np.nan).astype(float),
            "thermal_nameplate_mw": merged.get("thermal_nameplate_mw", np.nan).astype(
                float
            ),
            "ramp_up_1h_mw": merged.get("ramp_up_1h_mw", np.nan).astype(float),
            "observed_pmax_mw": merged.get("observed_pmax_mw", np.nan).astype(float),
            "hours_observed": merged["hours_observed"],
            "vintage_span": vintage_span,
            "source_doc": _SOURCE_DOC,
        }
    )
    return out.sort_values("plant_code").reset_index(drop=True)[list(CANONICAL_COLUMNS)]


def raw_dirs_for(raw_root: Path) -> tuple[Path, Path]:
    """The raw inputs this datatype reads (for provenance strings)."""
    return raw_root / "eia-860", raw_root / _CAMPD_DIR
