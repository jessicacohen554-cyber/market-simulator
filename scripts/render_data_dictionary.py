#!/usr/bin/env python
"""Render ``data/dictionary/data-dictionary.md`` deterministically.

The data dictionary is a generated artifact, not a hand-maintained document.
Two sources feed it, and only these:

* **Per-column tables** come from the canonical schema YAMLs under
  ``data/dictionary/schema/`` (the source of truth — name, dtype, unit,
  nullability, description). Change a column there and re-render; never edit the
  table here.
* **The ISO x year coverage matrix** comes from the ``market_sim.*`` provenance
  metadata embedded in each ``data/clean`` Parquet file (``iso`` / ``year`` /
  ``datatype``), read through :func:`scripts.lib.clean_io.read_clean_metadata`.
  Regenerate the clean tree first with ``python scripts/regenerate_clean.py``;
  the matrix then reflects exactly what landed on disk.

The narrative scaffold around those two — each datatype's one-line purpose and
its "Reconciles" note — lives in :data:`NARRATIVE` below, so the whole document
is reproducible from this script plus the schemas plus the clean tree.

Usage
-----
    python scripts/render_data_dictionary.py            # write the doc
    python scripts/render_data_dictionary.py --check    # exit 1 if out of date
    python scripts/render_data_dictionary.py --stdout    # print, don't write

A companion test (``tests/test_data_dictionary_sync.py``) asserts the committed
doc equals a fresh render.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

# Allow running as a plain script (``python scripts/render_data_dictionary.py``)
# as well as a module — clean_io lives in the ``scripts`` package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib import clean_io  # noqa: E402
from market_sim.config import paths  # noqa: E402

DOC_PATH: Path = paths.DICTIONARY_DIR / "data-dictionary.md"

# ISO columns of the coverage matrix, in the project's canonical order.
ISO_ORDER: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# Datatype sections, in render order. Mostly mirrors scripts/regenerate_clean.DATATYPES,
# plus `energy-offers`, which ships a schema but is curated by a dedicated pipeline
# (scripts/fetch_pjm_energy_offers.py → scripts/curate_energy_offers.py) rather than
# the generic regenerate path. This tuple must cover every data/dictionary/schema/*.yaml
# (enforced by tests/test_data_dictionary_sync.py).
DATATYPE_ORDER: tuple[str, ...] = (
    "lmp",
    "load",
    "ancillary-services",
    "energy-offers",
    "generation",
    "renewables",
    "emissions",
    "outages",
    "validation",
    "fleet",
    "fuel-prices",
    "reference",
    "border-lmp",
    "zonal-shares",
    "weather",
)

# Per-datatype narrative scaffold. ``summary`` is the one-line purpose under the
# heading; ``reconciles`` is the "what raw layouts fold into this" note. ``keys``
# overrides the schema key list only where the prose says more than the schema
# (reference). Everything else — the per-column table, the key list — is derived.
NARRATIVE: dict[str, dict[str, str]] = {
    "lmp": {
        "summary": "Locational marginal prices and components.",
        "reconciles": (
            "CAISO `LMP/MCC/MCE/MCL/MGHG`, PJM `DA_LMP/RT_LMP`, NYISO LBMP "
            "components, ERCOT settlement-point price, NEISO SMD hub LMP — into "
            "one total `lmp_usd_per_mwh` plus energy/congestion/loss/ghg "
            "components, with DA vs RT carried in the `market` key."
        ),
    },
    "load": {
        "summary": "Hourly demand and forecast by zone.",
        "reconciles": (
            "CAISO TAC-area `mw`, NYISO `Load`, EIA-930 `Demand` / "
            "`Demand forecast` — into `load_mw`, `load_forecast_mw`, optional "
            "`net_load_mw`."
        ),
    },
    "ancillary-services": {
        "summary": "AS clearing prices and cleared quantities.",
        "reconciles": (
            "NYISO `spin_10/nonsync_10/op_30/reg_cap`, PJM long "
            "`ancillary_service/value`, ERCOT `REGUP/REGDN/RRS/ECRS/NSPIN`, "
            "CAISO `RU/RD/SR/NR` — onto a common product taxonomy (reg up/down, "
            "spin, nonspin, 30-min supplemental), prices in `$/MW`."
        ),
    },
    "energy-offers": {
        "summary": "PJM Real-Time effective energy offer curves (long step form).",
        "reconciles": (
            "PJM DataMiner2 `energy_market_offers` wide `mw1..mw20`/`bid1..bid20` "
            "breakpoints (plus daily `avg_ecomin`/`avg_ecomax`, no-load and "
            "hot/cold/inter start costs) — pivoted to one row per "
            "(`unit_code` × operating-hour × `step_idx`) with `step_mw` / "
            "`step_price_usd_per_mwh`. PJM-only; unit identity is anonymised and "
            "rotated annually (not joinable across calendar years)."
        ),
    },
    "generation": {
        "summary": "Generation by fuel (long form).",
        "reconciles": (
            "EIA-930 wide `NG: *` fuel columns (unpivoted), PJM "
            "`fuel_type/mw/is_renewable`, CAISO technology buckets."
        ),
    },
    "renewables": {
        "summary": "Renewable output, availability (HSL) and curtailment.",
        "reconciles": (
            "CAISO/ERCOT HSL `wind_gen_mw/wind_hsl_mw/solar_*` (unpivoted), "
            "CAISO curtailment — into `generation_mw`, `hsl_mw`, "
            "`curtailment_mw`."
        ),
    },
    "emissions": {
        "summary": "Hourly CEMS/CAMPD emissions by plant/unit.",
        "reconciles": (
            "CAMPD facility- and unit-level "
            "`co2Mass/noxMass/so2Mass/heatInput/grossLoad` — masses "
            "standardized to `*_kg`, heat input to MMBtu."
        ),
    },
    "outages": {
        "summary": "Generator outages / available capacity.",
        "reconciles": (
            "CAMPD-derived downtime, ERCOT curated unit-outage lists — into "
            "`outage_mw` / `available_mw`."
        ),
    },
    "validation": {
        "summary": "Calibration/validation reference targets (tidy long form).",
        "reconciles": (
            "heterogeneous `_validation-source` benchmark files (renewable "
            "capacity, generation, emissions, price) into `(dimensions → "
            "metric, value, unit)`."
        ),
    },
    "fleet": {
        "summary": "Generator fleet registry.",
        "reconciles": (
            "EIA-860 (`Plant Code`, `Generator ID`, `Nameplate Capacity "
            "(MW)`, …), master plant registry, eGRID — into snake_case + "
            "unit-suffixed columns."
        ),
    },
    "fuel-prices": {
        "summary": "Delivered fuel price benchmarks.",
        "reconciles": (
            "Henry Hub daily `price_usd_mmbtu`, citygate/basis benchmarks — "
            "into `price_usd_per_mmbtu` by `fuel`/`hub`."
        ),
    },
    "reference": {
        "summary": "Crosswalk / lookup tables (heterogeneous).",
        "reconciles": (
            "master plant registry, bin assignments, zone/node crosswalks — "
            "conventions enforced, table-specific columns permitted."
        ),
        "keys": "`key` (+ `plant_id`/`iso`/`zone`/`node` when applicable)",
    },
    "border-lmp": {
        "summary": "Measured neighbor-border hourly Day-Ahead LMP.",
        "reconciles": (
            "CAISO OASIS WECC intertie LMP (MALIN, PALOVRDE), PJM hub LMP "
            "(CHICAGO GEN / AEP GEN / ATSI GEN equal-weight mean for MISO "
            "PJM_WEST) — on the model's fixed non-leap 8760-hour local-year "
            "calendar, dense `price` (NaN for gaps)."
        ),
    },
    "zonal-shares": {
        "summary": "Hourly zonal load share fractions (per ISO, per year).",
        "reconciles": (
            "PJM metered-load CSV (20 real zones → 8 model zones), ERCOT "
            "native-load XLSX (8 weather zones → 6 model zones), CAISO "
            "TAC-area CSV (4 areas → 3 trading-hub zones), MISO EIA-930 "
            "sub-BA CSV (6 sub-BAs → 3 model zones), NYISO pal CSV "
            "(11 settlement zones → 5 model zones), NEISO SMD wide CSV "
            "(8 load zones → 4 model zones) — into `share` fractions "
            "summing to ≈1.0 per hour, long format `(hour, zone, share)`. "
            "Files are ISO-partitioned by directory path "
            "(`data/clean/zonal-shares/<ISO>/`)."
        ),
    },
    "weather": {
        "summary": "Daily maximum and minimum temperature by model zone.",
        "reconciles": (
            "Per-ISO NOAA GHCN-Daily TMAX/TMIN CSVs (zone-level files plus "
            "load-weighted ISO aggregates for CAISO and NEISO, NYC-metro "
            "aggregate for NYISO) — into one `(date, zone, tmax_c, tmin_c)` "
            "row per zone per calendar day. Sentinel zones: `_load_weighted` "
            "(CAISO, NEISO ISO-level aggregate), `_downstate` (NYISO "
            "NYC-metro). Files are ISO-partitioned by directory path "
            "(`data/clean/weather/<ISO>/`)."
        ),
    },
}

# Short scope note for the national (non-ISO-partitioned) datatypes' table.
NATIONAL_SCOPE: dict[str, str] = {
    "emissions": "CAMPD/CEMS, by plant and unit",
    "outages": "derived (CAMPD downtime + curated ERCOT lists)",
    "fleet": "EIA-860 / eGRID / master registry",
    "fuel-prices": "national hubs (Henry Hub)",
    "reference": "crosswalks / lookups (ISO-agnostic)",
    "border-lmp": "neighbor-border hubs (WECC intertie, PJM_WEST)",
    "zonal-shares": "per-ISO via directory partitioning",
    "weather": "per-ISO via directory partitioning",
}

NA = "n/a"
NONE_CELL = "—"

PREAMBLE = """\
# Data dictionary

The canonical contract for the curated `data/clean` tree. Every clean datatype
has exactly one schema under [`schema/`](schema/) (`<datatype>.schema.yaml`)
declaring its canonical columns — name, dtype, unit, nullability — and its key
columns. All curation sessions write through the shared
[`scripts/lib/clean_io.py`](../../scripts/lib/clean_io.py) `write_clean(...)`
seam, which validates against these schemas before writing Parquet and embeds
the schema version + source provenance in each file.

**Conventions (enforced by `clean_io`):**

- Columns are `lower_snake_case`.
- Time is tz-aware **UTC** in `interval_start_utc`; an optional tz-naive
  wall-clock `interval_start_local` may accompany it (UTC is authoritative).
- Standard keys: `iso`, `zone`, `node`, `plant_id`, `unit_id`, `year`,
  `month`, `hour`.
- Units are explicit in column names: `*_mw`, `*_mwh`, `price_*_usd_per_mwh`,
  `*_usd_per_mw` (AS capacity), `*_usd_per_mmbtu` (fuel), `*_kg` (emissions).

> **This file is generated — do not hand-edit.** Per-column tables are rendered
> from the schema YAMLs and the coverage matrix from the provenance metadata
> embedded in `data/clean`. To change a column, edit its schema YAML (or
> recurate the data) and run `python scripts/render_data_dictionary.py`. The
> test `tests/test_data_dictionary_sync.py` guards that the committed file
> matches a fresh render.

## Regenerate from raw

The clean tree is derived and disposable; it is rebuilt from `data/raw` by the
per-datatype curation scripts (`scripts/curate_*.py`, added per session), each
calling `clean_io.write_clean(df, datatype, ...)`. To regenerate everything run
`python scripts/regenerate_clean.py`; to verify an existing file round-trips
against its embedded schema, call `clean_io.validate_clean(path)`. Raw inputs
are described in [`../README.md`](../README.md) and are never modified in place."""


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def _para(text: str) -> str:
    """Wrap a paragraph at 79 cols without splitting links or hyphenated tokens."""
    return textwrap.fill(text, width=79, break_long_words=False, break_on_hyphens=False)


def _bullet(label: str, text: str) -> str:
    """Render a ``- **Label:** text`` bullet, wrapped with a hanging indent."""
    return textwrap.fill(
        f"- **{label}:** {text}",
        width=79,
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _fmt_years(years: set[int]) -> str:
    """Compact a set of years into contiguous ranges (e.g. ``2021, 2023–2025``)."""
    ys = sorted(years)
    if not ys:
        return NONE_CELL
    runs: list[tuple[int, int]] = []
    start = prev = ys[0]
    for y in ys[1:]:
        if y == prev + 1:
            prev = y
            continue
        runs.append((start, prev))
        start = prev = y
    runs.append((start, prev))
    return ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in runs)


# ---------------------------------------------------------------------------
# Schema-driven per-column tables
# ---------------------------------------------------------------------------
def column_table(datatype: str) -> str:
    """Render a datatype's per-column table straight from its schema YAML."""
    schema = clean_io.load_schema(datatype)
    lines = [
        "| column | dtype | unit | nullable | description |",
        "|---|---|---|---|---|",
    ]
    for col in schema.columns:
        desc = " ".join(col.description.split()).replace("|", r"\|")
        nullable = "yes" if col.nullable else "no"
        lines.append(
            f"| `{col.name}` | `{col.dtype}` | `{col.unit}` | {nullable} | {desc} |"
        )
    return "\n".join(lines)


def _keys(datatype: str) -> str:
    """Key columns for a datatype — narrative override, else the schema list."""
    override = NARRATIVE[datatype].get("keys")
    if override:
        return override
    schema = clean_io.load_schema(datatype)
    return ", ".join(f"`{k}`" for k in schema.key_columns)


# ---------------------------------------------------------------------------
# Clean-tree-driven coverage
# ---------------------------------------------------------------------------
def enumerate_coverage() -> tuple[
    dict[str, dict[str, set[int]]], dict[str, set[int]], set[str]
]:
    """Read ``data/clean`` provenance into coverage maps.

    Returns ``(iso_years, national_years, iso_datatypes)``:

    * ``iso_years[datatype][iso]`` -> set of years (datatypes with an ``iso``
      partition),
    * ``national_years[datatype]`` -> set of years (datatypes with no ``iso``),
    * ``iso_datatypes`` -> the set of datatypes that carry any ``iso``.
    """
    iso_years: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    national_years: dict[str, set[int]] = defaultdict(set)
    iso_datatypes: set[str] = set()

    for path in sorted(paths.CLEAN_DIR.rglob("*.parquet")):
        meta = clean_io.read_clean_metadata(path)
        datatype = meta.get("datatype")
        if not datatype:
            continue
        iso = meta.get("iso")
        raw_year = meta.get("year")
        year = int(raw_year) if raw_year not in (None, "") else None
        if iso:
            iso_datatypes.add(datatype)
            if year is not None:
                iso_years[datatype][iso].add(year)
        elif year is not None:
            national_years[datatype].add(year)
    return iso_years, national_years, iso_datatypes


def _iso_partitioned(datatype: str) -> bool:
    """Whether a datatype is ISO-partitioned, per its schema.

    Classification is schema-driven (``iso`` is a key column) rather than
    derived from whichever files happen to exist in ``data/clean``. This keeps
    :func:`coverage_section` deterministic and crash-free when the (gitignored)
    clean tree is absent, while reproducing the data-driven partition for the
    actually-curated datatypes.
    """
    return "iso" in clean_io.load_schema(datatype).key_columns


def coverage_section() -> str:
    """Render the ISO x year matrix and the national-datatype table."""
    iso_years, national_years, _ = enumerate_coverage()
    iso_datatypes = {d for d in DATATYPE_ORDER if _iso_partitioned(d)}

    out: list[str] = ["## ISO coverage matrix", ""]
    out.append(
        _para(
            "Built from the `market_sim.*` provenance metadata embedded in "
            "`data/clean` (regenerate the tree with `python "
            "scripts/regenerate_clean.py`). Each cell is the span of calendar "
            "years curated for that datatype and ISO; `—` means none is "
            "curated. Markets (DAM/RTM) are aggregated here — see each "
            "datatype's section for the market split."
        )
    )
    out.append("")
    out.append("| datatype | " + " | ".join(ISO_ORDER) + " |")
    out.append("|---|" + "---|" * len(ISO_ORDER))
    for datatype in DATATYPE_ORDER:
        if datatype not in iso_datatypes:
            continue
        cells = [_fmt_years(iso_years[datatype].get(iso, set())) for iso in ISO_ORDER]
        out.append(f"| {datatype} | " + " | ".join(cells) + " |")

    out.append("")
    out.append("### National / ISO-agnostic datatypes")
    out.append("")
    out.append(
        _para(
            "Not partitioned by ISO (no `iso` in their `data/clean` "
            "provenance); coverage is national. `n/a` marks datatypes with no "
            "year partition (a single current snapshot)."
        )
    )
    out.append("")
    out.append("| datatype | scope | years |")
    out.append("|---|---|---|")
    for datatype in DATATYPE_ORDER:
        if datatype in iso_datatypes:
            continue
        years = national_years.get(datatype, set())
        years_cell = _fmt_years(years) if years else NA
        out.append(
            f"| {datatype} | {NATIONAL_SCOPE.get(datatype, NONE_CELL)} | {years_cell} |"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def _datatype_section(datatype: str) -> str:
    narrative = NARRATIVE[datatype]
    summary = (
        f"{narrative['summary']} Schema: "
        f"[`schema/{datatype}.schema.yaml`](schema/{datatype}.schema.yaml)."
    )
    return "\n".join(
        [
            f"## {datatype}",
            "",
            _para(summary),
            "",
            _bullet("Keys", _keys(datatype)),
            _bullet("Reconciles", narrative["reconciles"]),
            "",
            column_table(datatype),
        ]
    )


def render_document() -> str:
    """Render the full data-dictionary markdown (ends with a trailing newline)."""
    parts = [PREAMBLE, coverage_section(), "---"]
    parts.extend(_datatype_section(dt) for dt in DATATYPE_ORDER)
    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed doc differs from a fresh render",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="write the rendered doc to stdout instead of the file",
    )
    args = parser.parse_args(argv)

    doc = render_document()

    if args.stdout:
        sys.stdout.write(doc)
        return 0

    if args.check:
        current = DOC_PATH.read_text() if DOC_PATH.is_file() else ""
        if current != doc:
            print(
                f"{DOC_PATH} is out of date — run "
                f"`python scripts/render_data_dictionary.py`",
                file=sys.stderr,
            )
            return 1
        print(f"{DOC_PATH} is up to date")
        return 0

    DOC_PATH.write_text(doc)
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
