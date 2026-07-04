"""Shared contract for the ``winter-fuel-inventory`` clean datatype.

Backs component A of the NEISO winter fuel-inventory build
(``docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md``): the
forward-derivable capacity/logistics quantities that size a winter-season
(Nov-Mar) oil-burn energy budget for the fuel-constrained fleet. Every quantity
is a rule-#13-admissible physical/market INPUT — tank capacity, start-of-season
fill, re-supply delivery rate, boiler firing rate, dual-fuel oil-limb MW,
season length, program membership — that regenerates for a forward year from
forward drivers and responds to changed conditions. Measured burn/delivery
*outcomes* (the rejected F923 petroleum receipts) are deliberately absent and
inadmissible as budget drivers.

Two kinds of source feed the one tidy schema in
``data/dictionary/schema/winter-fuel-inventory.schema.yaml``:

* **EIA-860** (committed under ``data/raw/eia-860``) — per-plant, machine
  derivable now: the dual-fuel oil-limb net winter capacity (multifuel table)
  and the maximum petroleum firing rate (boiler design-parameters table).
* **ISO-NE studies + program filings** — fleet/system/program level, curated by
  hand into a unified CSV under
  ``data/raw/winter-fuel-inventory/<iso>/<iso>.csv`` with exact citations
  (start-of-season fill, delivery-rate caps, tank capacities, winter-program
  unit lists).

Per-ISO logic lives in sibling modules (``isone.py``, ...), each registering an
:class:`IsoSpec` via :func:`register`. Shared code never branches on the ISO
name — it looks the spec up in :data:`REGISTRY`. This keeps new ISOs additive
(drop a module, register a spec) per ``docs/adding-new-data-types.md``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "winter-fuel-inventory"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "entity",
    "entity_type",
    "plant_code",
    "season",
    "delivery_year",
    "metric",
    "value",
    "unit",
    "fuel_kind",
    "source_doc",
    "source_page",
)

# Controlled vocabularies (mirror the schema descriptions; validated below).
ENTITY_TYPES: frozenset[str] = frozenset(
    {"plant", "fleet", "fuel_class", "program", "system"}
)
SEASONS: frozenset[str] = frozenset({"winter", "annual"})
FUEL_KINDS: frozenset[str] = frozenset(
    {"distillate", "residual", "oil", "lng", "dual_fuel"}
)

# Allowed (metric -> {unit, ...}) pairing. The metric names carry semantics; the
# unit column carries the physical unit, and only these pairings are legal. The
# unit vocabulary is deliberately broad enough to record each ISO-NE study
# figure in the form it is *published* (tank autonomy in days, oil re-supply as
# fills-per-winter, LNG as Bcf/day) rather than forcing a lossy conversion at
# intake; the downstream budget derivation reconciles units.
METRIC_UNITS: dict[str, frozenset[str]] = {
    # On-site oil storage: barrels/MMBtu where published, else tank autonomy
    # (days of full-output burn) as OFSA states it ("~10 days' worth of oil").
    "tank_capacity": frozenset({"bbl", "mmbtu", "days"}),
    # Assumed start-of-season oil inventory (fleet/system/program).
    "start_fill": frozenset({"bbl", "mmbtu"}),
    # Re-supply / replenishment cap: oil (bbl or MMBtu per day, or tank fills
    # per winter) or LNG injection (Bcf/day).
    "delivery_rate": frozenset(
        {"bbl_per_day", "mmbtu_per_day", "fills_per_season", "bcf_per_day"}
    ),
    # Environmental / permit annual oil-run cap (days per year on oil).
    "annual_run_limit": frozenset({"days"}),
    # Max physical petroleum burn rate (EIA-860 boiler design).
    "firing_rate": frozenset({"bbl_per_hr"}),
    # Dual-fuel unit's net capacity when burning oil (EIA-860 multifuel).
    "oil_limb_capacity": frozenset({"mw"}),
    # Fleet/class oil-capable capacity from an ISO-NE study.
    "oil_fleet_capacity": frozenset({"mw"}),
    # Capacity retained under a winter-reliability / retention program.
    "winter_program_capacity": frozenset({"mw"}),
    # Length of the budget horizon (Nov-Mar season / OFSA 90-day winter).
    "season_days": frozenset({"days"}),
    # Membership flag in a winter-reliability / retention program (value=1).
    "winter_program_member": frozenset({"flag"}),
}
METRIC_VOCAB: frozenset[str] = frozenset(METRIC_UNITS)

_STRING_COLS = (
    "iso",
    "entity",
    "entity_type",
    "season",
    "delivery_year",
    "metric",
    "unit",
    "fuel_kind",
    "source_doc",
    "source_page",
)

# EIA-860 raw filenames the per-plant derivation reads (committed vintage).
EIA860_DIRNAME = "eia-860"
_MULTIFUEL_FILE = "eia860_multifuel_operable.parquet"
_BOILER_FILE = "eia860_enviro_equip_boiler_info_design_parameters.parquet"

# EIA-860 field that reports the boiler's max petroleum firing rate. The header
# unit is *tenths* of a barrel per hour, so the raw value is divided by 10 to
# reach bbl/hr (documented in the raw README).
_FIRING_RATE_FIELD = "Firing Rate Using Petroleum (0.1 Barrels per Hour)"
_FIRING_RATE_SCALE = 0.1  # 0.1 bbl/hr units -> bbl/hr


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's winter-fuel-inventory sources.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (e.g. ``"ISONE"``).
    eia_states:
        USPS state codes whose EIA-860 oil-capable plants belong to this ISO.
        Used to filter the per-plant EIA-860 derivation. ISO-NE is exactly the
        six New England states; an ISO that spans partial states supplies a
        custom ``parse`` hook instead.
    eia_vintage:
        Label stamped as ``delivery_year`` on the EIA-860-derived rows and
        embedded in their ``source_doc`` (the committed EIA-860 vintage).
    parse:
        Optional custom reader ``(raw_root: Path, spec: IsoSpec) -> DataFrame``.
        Defaults to :func:`parse_default`, which unions the EIA-860 per-plant
        derivation (over ``eia_states``) with the hand-curated study CSV.
    """

    iso: str
    eia_states: tuple[str, ...] = ()
    eia_vintage: str = ""
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules are
# skipped, so intake waves land independently.
_ISO_MODULES: tuple[str, ...] = ("isone",)
_loaded = False


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label. Returns the spec."""
    REGISTRY[spec.iso.upper()] = spec
    return spec


def load_registry() -> dict[str, IsoSpec]:
    """Import every available ISO module (idempotent) and return the registry."""
    global _loaded
    if not _loaded:
        for name in _ISO_MODULES:
            try:
                importlib.import_module(f"{__name__}.{name}")
            except ModuleNotFoundError:
                continue  # ISO not implemented yet — additive by design.
        _loaded = True
    return REGISTRY


def eia860_dir(raw_root: Path) -> Path:
    """Directory holding the committed EIA-860 raw parquet (per-plant source)."""
    return raw_root / EIA860_DIRNAME


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's hand-curated study/program CSV."""
    return raw_root / DATATYPE / iso.lower()


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order.

    Missing optional columns (``plant_code`` / ``fuel_kind`` / source locators)
    are filled with nulls so a source that carries only some fields still
    yields a schema-shaped frame.
    """
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string")
    out["value"] = pd.to_numeric(out["value"], errors="coerce").astype("float64")
    # Nullable integer plant code (schema accepts int64 or float-with-NaN).
    out["plant_code"] = pd.to_numeric(out["plant_code"], errors="coerce").astype(
        "Int64"
    )
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(
        ["entity_type", "entity", "season", "delivery_year", "metric"]
    ).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary + metric/unit rules before ``write_clean``.

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes, nulls, naming)
    with the value-level rules the schema can't express: entity_type / season /
    fuel_kind vocabularies, the metric vocabulary, the legal metric<->unit
    pairing, and a non-negative ``value``. Raises :class:`ValueError` on any
    violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_et = sorted(set(df["entity_type"].dropna()) - ENTITY_TYPES)
    if bad_et:
        problems.append(f"entity_type(s) not in vocab: {bad_et}")
    bad_season = sorted(set(df["season"].dropna()) - SEASONS)
    if bad_season:
        problems.append(f"season(s) not in vocab: {bad_season}")
    bad_metric = sorted(set(df["metric"].dropna()) - METRIC_VOCAB)
    if bad_metric:
        problems.append(f"metric(s) not in vocab: {bad_metric}")
    bad_fk = sorted(set(df["fuel_kind"].dropna()) - FUEL_KINDS)
    if bad_fk:
        problems.append(f"fuel_kind(s) not in vocab: {bad_fk}")
    # metric <-> unit pairing (only for rows whose metric is known).
    for metric, allowed in METRIC_UNITS.items():
        rows = df[df["metric"] == metric]
        bad_unit = sorted(set(rows["unit"].dropna()) - allowed)
        if bad_unit:
            problems.append(
                f"metric {metric!r} carries illegal unit(s) {bad_unit} "
                f"(allowed: {sorted(allowed)})"
            )
    if bool((df["value"] < 0).any()):
        problems.append(f"{int((df['value'] < 0).sum())} row(s) have value < 0")
    if problems:
        raise ValueError(
            "winter-fuel-inventory tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


# ---------------------------------------------------------------------------
# EIA-860 per-plant derivation (forward-derivable oil-limb MW + firing rate)
# ---------------------------------------------------------------------------
def derive_eia860_rows(
    raw_root: Path, iso: str, states: tuple[str, ...], vintage: str
) -> pd.DataFrame:
    """Derive per-plant oil-limb capacity + petroleum firing rate from EIA-860.

    Reads the committed EIA-860 multifuel and boiler design-parameter tables,
    filters to plants in ``states``, and produces two per-plant metrics:

    * ``oil_limb_capacity`` (unit ``mw``, season ``winter``, fuel_kind
      ``dual_fuel``) — the net winter capacity when burning oil, summed over a
      plant's oil/gas-switch-capable generators (EIA-860 multifuel
      ``Net Winter Capacity with Oil (MW)``). This is the physical MW the
      dual-fuel gas fleet can serve on its oil limb — the coverage hole that
      killed the neiso-40 monthly-F923 probe.
    * ``firing_rate`` (unit ``bbl_per_hr``, season ``annual``, fuel_kind
      ``oil``) — the maximum physical petroleum burn rate, summed over a
      plant's boilers (EIA-860 ``Firing Rate Using Petroleum``; the header unit
      is tenths of a barrel per hour, rescaled to bbl/hr). This bounds how fast
      a plant can draw down its tank and how much re-supply it needs.

    Returns an empty (correctly-shaped) frame if the EIA-860 tables are absent
    so the datatype degrades to CSV-only. Reads only ``data/raw``.
    """
    edir = eia860_dir(raw_root)
    rows: list[pd.DataFrame] = []
    state_set = {s.upper() for s in states}

    mf_path = edir / _MULTIFUEL_FILE
    if mf_path.is_file():
        mf = pd.read_parquet(mf_path)
        switch = mf["Switch Between Oil and Natural Gas?"].astype(str).str.upper()
        cap = pd.to_numeric(mf["Net Winter Capacity with Oil (MW)"], errors="coerce")
        sel = mf[
            mf["State"].astype(str).str.upper().isin(state_set)
            & switch.str.startswith("Y")
            & (cap > 0)
        ].copy()
        sel["_cap"] = pd.to_numeric(
            sel["Net Winter Capacity with Oil (MW)"], errors="coerce"
        )
        by_plant = sel.groupby("Plant Code", dropna=True)["_cap"].sum()
        if not by_plant.empty:
            rows.append(
                _plant_frame(
                    iso,
                    by_plant,
                    metric="oil_limb_capacity",
                    unit="mw",
                    season="winter",
                    fuel_kind="dual_fuel",
                    vintage=vintage,
                    source_doc=f"EIA-860 {vintage} 3_5_Multifuel (operable)",
                    source_page="Net Winter Capacity with Oil (MW)",
                )
            )

    bo_path = edir / _BOILER_FILE
    if bo_path.is_file():
        bo = pd.read_parquet(bo_path)
        fr = pd.to_numeric(bo[_FIRING_RATE_FIELD], errors="coerce") * _FIRING_RATE_SCALE
        bo = bo.assign(_fr=fr)
        sel = bo[bo["State"].astype(str).str.upper().isin(state_set) & (bo["_fr"] > 0)]
        by_plant = sel.groupby("Plant Code", dropna=True)["_fr"].sum()
        if not by_plant.empty:
            rows.append(
                _plant_frame(
                    iso,
                    by_plant,
                    metric="firing_rate",
                    unit="bbl_per_hr",
                    season="annual",
                    fuel_kind="oil",
                    vintage=vintage,
                    source_doc=f"EIA-860 {vintage} 6_2_EnviroEquipY boiler design",
                    source_page=_FIRING_RATE_FIELD,
                )
            )

    if not rows:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    return finalize(pd.concat(rows, ignore_index=True))


def _plant_frame(
    iso: str,
    by_plant: pd.Series,
    *,
    metric: str,
    unit: str,
    season: str,
    fuel_kind: str,
    vintage: str,
    source_doc: str,
    source_page: str,
) -> pd.DataFrame:
    """Build a canonical per-plant frame from a plant_code -> value Series."""
    codes = [int(c) for c in by_plant.index]
    return pd.DataFrame(
        {
            "iso": iso,
            "entity": [str(c) for c in codes],
            "entity_type": "plant",
            "plant_code": codes,
            "season": season,
            "delivery_year": vintage,
            "metric": metric,
            "value": by_plant.to_numpy(dtype=float),
            "unit": unit,
            "fuel_kind": fuel_kind,
            "source_doc": source_doc,
            "source_page": source_page,
        }
    )


# ---------------------------------------------------------------------------
# Study/program CSV parser (hand-curated ISO-NE figures with citations)
# ---------------------------------------------------------------------------
def parse_study_csv(raw_root: Path, iso: str) -> pd.DataFrame:
    """Read an ISO's hand-curated study/program CSV into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. Rows carry the
    fleet/system/program figures pulled from ISO-NE fuel-security studies and
    winter-program filings, each with a ``source_doc`` / ``source_page``
    citation. Returns an empty (correctly-shaped) frame when the CSV is absent
    (or has no data rows) so the datatype degrades to EIA-860-only.
    """
    csv = raw_dir_for(iso, raw_root) / f"{iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str, comment="#", skip_blank_lines=True)
    raw.columns = [c.strip().lower() for c in raw.columns]
    if raw.empty:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw["iso"] = iso
    df = finalize(raw)
    return df[df["value"].notna()].reset_index(drop=True)


def parse_default(raw_root: Path, spec: IsoSpec) -> pd.DataFrame:
    """Default parser: union of the EIA-860 derivation and the study CSV."""
    eia = derive_eia860_rows(raw_root, spec.iso, spec.eia_states, spec.eia_vintage)
    study = parse_study_csv(raw_root, spec.iso)
    frames = [f for f in (eia, study) if not f.empty]
    if not frames:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    return finalize(pd.concat(frames, ignore_index=True))


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/winter_fuel_inventory/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_default
    df = reader(raw_root, spec)
    if not df.empty:
        validate_tidy(df)
    return df
