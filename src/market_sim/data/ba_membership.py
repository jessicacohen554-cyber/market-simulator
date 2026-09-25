"""Balancing-authority membership rules shared by the LP fleet and the benchmark.

Two registries in :mod:`market_sim.config.constants` decide which plants belong
to a modelled region beyond its plain EIA-860 ``Balancing Authority Code``
filter. Both are read HERE, and nowhere else, so the LP fleet, the EIA-923
benchmark and the must-run injection stay on the one boundary EIA-930 measures
the region's load on (rule 19 [R-ONE-MECH]; lane R-SOCO-B, 2026-09-25):

* :data:`~market_sim.config.constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` —
  plants the CURRENT EIA-860 plant file codes to another BA leave the region
  (:func:`current_ba_recoded_plants`, :func:`drop_current_ba_recoded_rows`).
  SOCO: the former Gulf Power plants, which EIA-930's SOCO series has excluded
  in every year although vintages 2019-2023 code them SOCO.
* :data:`~market_sim.config.constants.ISO_BA_JOINS` — a BA that joined the
  region part-way through a backcast year (:func:`joining_ba_codes`,
  :func:`ba_join_first_month`). SOCO: PowerSouth (``AEC``), 2021-09-01.

Every function is a pure read of committed EIA-860 parquet keyed on its
arguments (no ``ScenarioConfig``, no process global), and every one returns an
empty result for a region neither registry names, so every other region is
byte-identical.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from market_sim.config.constants import (
    ISO_BA_JOINS,
    ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE,
)

#: Returned by :func:`ba_join_first_month` for a plant whose BA has not yet
#: joined in the year asked about: no month of that year is inside the region.
NOT_A_MEMBER_THIS_YEAR: int = 13


def drops_current_ba_recode(iso: str) -> bool:
    """Return whether ``iso`` drops plants the current EIA-860 recodes elsewhere."""
    return bool(ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE.get(iso.upper(), False))


@lru_cache(maxsize=8)
def current_ba_recoded_plants(iso: str) -> frozenset[int]:
    """Plants the CURRENT EIA-860 plant file codes to a BA other than ``iso``'s.

    Read only for an ISO in ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` (see that
    constant for the measurement). A plant absent from the current file, or
    carrying no BA code there, is NOT returned: only an explicit recode to
    another balancing authority removes a plant from ``iso``'s membership. A
    plant with rows coded to BOTH this ISO and another stays in.

    Moved here from ``scripts/run_calibration_full.py`` (lane R-SOCO-B) so the
    fleet loaders and the benchmark read the same function; the body is
    unchanged.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.zone_assignment import _iso_ba_codes

    path = EIA_860_DIR / "eia860_plant.parquet"
    codes = set(_iso_ba_codes(iso))
    if not codes or not path.exists():
        return frozenset()
    df = pd.read_parquet(path, columns=["Plant Code", "Balancing Authority Code"])
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    other = df[(ba != "") & ~ba.isin(["nan", "None"]) & ~ba.isin(codes)]
    ours = set(
        pd.to_numeric(df[ba.isin(codes)]["Plant Code"], errors="coerce")
        .dropna()
        .astype(int)
    )
    plants = pd.to_numeric(other["Plant Code"], errors="coerce").dropna().astype(int)
    return frozenset(int(p) for p in plants if int(p) not in ours)


def drop_current_ba_recoded_rows(
    df: pd.DataFrame, iso: str, plant_col: str = "plant_id"
) -> pd.DataFrame:
    """Drop fleet rows whose plant the current EIA-860 recodes out of ``iso``.

    The LP-fleet half of ``ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE``: applied
    right after each fleet loader's BA filter (operable, within-window retiree,
    mothball re-carry). Returns ``df`` itself — the same object — when ``iso``
    is not registered, when the frame is empty or lacks ``plant_col``, or when
    no row is dropped, so every other region and every clean year is
    byte-identical.
    """
    if df.empty or plant_col not in df.columns or not drops_current_ba_recode(iso):
        return df
    recoded = current_ba_recoded_plants(iso.upper())
    if not recoded:
        return df
    plant = pd.to_numeric(df[plant_col], errors="coerce")
    drop = plant.isin(recoded).to_numpy(dtype=bool)
    if not drop.any():
        return df
    return df[~drop]


def joining_ba_codes(iso: str, year: int | None) -> tuple[str, ...]:
    """Return the BAs that have joined ``iso`` by ``year`` (join year included).

    A fleet loader admits rows coded to these BAs in addition to ``iso``'s own
    codes. ``year=None`` (no solve year known) admits none. In a year after the
    join the vintages already code the plants to ``iso``, so the extra codes
    select nothing there; only the join year's vintage carries them.
    """
    if year is None:
        return ()
    joins = ISO_BA_JOINS.get(iso.upper(), {})
    return tuple(ba for ba, (jy, _jm) in joins.items() if int(year) >= jy)


@lru_cache(maxsize=64)
def ba_join_first_month(iso: str, year: int) -> dict[int, int]:
    """Return ``{plant_code: first calendar month inside iso}`` for ``year``.

    Covers only plants coded to a registered JOINING BA
    (``ISO_BA_JOINS[iso]``) in the EIA-860 vintage that covers ``year``
    (``vintage_<year>/eia860_plant.parquet``, holding last to the canonical
    file): the month is the join month in the join year, and
    :data:`NOT_A_MEMBER_THIS_YEAR` in an earlier year. A year after the join
    returns ``{}`` (the vintages code the plants to ``iso`` and they are
    members all year). Empty for any unregistered region.
    """
    joins = ISO_BA_JOINS.get(iso.upper(), {})
    live = {ba: jm for ba, (jy, jm) in joins.items() if int(year) == jy}
    live.update(
        {ba: NOT_A_MEMBER_THIS_YEAR for ba, (jy, _jm) in joins.items() if year < jy}
    )
    if not live:
        return {}
    from market_sim.config.paths import EIA_860_DIR

    path = EIA_860_DIR / f"vintage_{int(year)}" / "eia860_plant.parquet"
    if not path.exists():
        path = EIA_860_DIR / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Balancing Authority Code"])
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    plant = pd.to_numeric(df["Plant Code"], errors="coerce")
    out: dict[int, int] = {}
    for code, b in zip(plant, ba):
        if pd.notna(code) and b in live:
            out[int(code)] = int(live[b])
    return out
