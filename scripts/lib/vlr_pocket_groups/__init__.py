"""Shared contract for the ``vlr-pocket-groups`` clean datatype.

The units an ISO's voltage-and-local-reliability (VLR) operating guides name
for each load pocket, grouped as the source's outage studies group them
(``data/dictionary/schema/vlr-pocket-groups.schema.yaml``). Per-ISO modules
(``miso.py``) register an :class:`IsoSpec`; shared code never branches on the
ISO. Each ISO's raw file is ``data/raw/vlr-pocket-groups/<iso>/<iso>.csv`` with
the canonical columns minus ``uc_family``, which :func:`uc_family_for` derives
from the unit's EIA-860 prime mover and energy source.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "vlr-pocket-groups"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "pocket",
    "group_id",
    "plant_code",
    "plant_name",
    "unit_id",
    "eia860_prime_mover",
    "eia860_energy_source",
    "eia860_retirement_year",
    "uc_family",
    "source_doc",
    "source_page",
)

_STRING_COLS = (
    "iso",
    "pocket",
    "group_id",
    "plant_name",
    "unit_id",
    "eia860_prime_mover",
    "eia860_energy_source",
    "uc_family",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("eia860_retirement_year",)

#: EIA-860 energy-source codes of coal (bituminous, subbituminous, lignite,
#: waste / refined coal) — EIA-860 instructions, Table 28.
COAL_ENERGY_SOURCES: frozenset[str] = frozenset(
    {"BIT", "SUB", "LIG", "ANT", "RC", "WC", "SGC"}
)
#: EIA-860 prime movers of a combined cycle (CT / CA / CS), Table 26.
CC_PRIME_MOVERS: frozenset[str] = frozenset({"CT", "CA", "CS"})
#: The model commitment-cluster families (``model.uc.params.FAMILY_BY_FUEL``).
UC_FAMILIES: frozenset[str] = frozenset({"st_gas", "ct", "cc", "coal"})

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [("iso", str)],
    package=__name__,
    iso_modules=("miso",),
    raw_subpath=(DATATYPE,),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    sort_by=("pocket", "group_id", "plant_code", "unit_id"),
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for


def uc_family_for(prime_mover: str, energy_source: str) -> str:
    """The commitment-cluster family of one unit from its EIA-860 identity.

    A steam turbine (``ST``) is ``coal`` on a coal energy source and
    ``st_gas`` otherwise; a combustion turbine (``GT``) is ``ct``; a
    combined-cycle part (``CT`` / ``CA`` / ``CS``) is ``cc``. Any other prime
    mover raises: the requirement must never silently drop a listed unit.
    """
    pm = str(prime_mover).strip().upper()
    es = str(energy_source).strip().upper()
    if pm == "ST":
        return "coal" if es in COAL_ENERGY_SOURCES else "st_gas"
    if pm == "GT":
        return "ct"
    if pm in CC_PRIME_MOVERS:
        return "cc"
    raise ValueError(f"no commitment-cluster family for prime mover {pm!r}")


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Canonical dtypes, order and sort (``plant_code`` as ``int64``)."""
    out = _R.finalize(df.assign(plant_code=pd.to_numeric(df["plant_code"])))
    out["plant_code"] = out["plant_code"].astype("int64")
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Value-level checks the schema cannot express; raises ``ValueError``."""
    problems: list[str] = []
    bad = sorted(set(df["uc_family"].dropna()) - UC_FAMILIES)
    if bad:
        problems.append(f"uc_family not in {sorted(UC_FAMILIES)}: {bad}")
    key = ["iso", "pocket", "group_id", "plant_code", "unit_id"]
    if df.duplicated(key).any():
        problems.append(f"{int(df.duplicated(key).sum())} duplicate key row(s)")
    # A unit belongs to one group: the requirement sums disjoint groups.
    unit = df.drop_duplicates(["iso", "plant_code", "unit_id", "group_id"])
    multi = unit.duplicated(["iso", "plant_code", "unit_id"])
    if multi.any():
        problems.append(f"{int(multi.sum())} unit(s) listed in more than one group")
    if problems:
        raise ValueError(
            "vlr-pocket-groups tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read ``<raw_dir>/<iso>.csv`` and derive ``uc_family``.

    Returns an empty, correctly-shaped frame when the file is absent so the
    curate script can skip an ISO with nothing transcribed.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str, keep_default_na=False)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["iso"] = spec.iso
    raw["eia860_retirement_year"] = raw["eia860_retirement_year"].replace("", None)
    raw["uc_family"] = [
        uc_family_for(pm, es)
        for pm, es in zip(raw["eia860_prime_mover"], raw["eia860_energy_source"])
    ]
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw file into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)}")
    df = parse_unified_csv(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
