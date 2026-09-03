"""Owner-filed EIA-860 Schedule-3 planned retirement dates for FOSSIL units.

The data seam behind ``ScenarioConfig.fossil_announced_exits_enabled`` (capx
D42, 2026-09-02 — the D32 R1 posture A/B; the gate shipped DEFAULT-OFF and was
FLIPPED DEFAULT-ON on 2026-09-03 by capx D44, executing owner ruling Q30 "ARM
AS DEFAULT" on the D42 measurement. An explicit ``False`` restores the pre-Q30
posture and this module is then never read). The pre-Q30 forecast posture
(``forecast_fossil_retirement_economic=True``) deliberately no-ops the
announced-date step for coal/gas/oil, leaving fossil exits to the economic
screen. D32 measured that the owner's filed date is the ONE published per-unit
driver that discriminates the real MISO 2021-2025 exit cohort (filed for 69 %
of the cohort's MW at the 2020 vintage; 87 % of dated MW exiting within ±1 yr
of the filed year) — this loader carries that driver into step 1 of the
capacity evolution as an exogenous input, on step 0's own machinery.

**Rule 13 [R-MEASURED] admissibility — the vintage gate.** A row is read from
the run's ACTIVE EIA-860 snapshot (:func:`market_sim.config.paths.
active_eia860_dir`, a ``vintage_<year>/`` directory for a vintage-seeded
hindcast), so every date it carries was on file at that vintage's cutoff —
the same information gate step 0 applies to a confirmed row's
``instrument_date``. A date is admissible in simulation year Y only because it
was filed before the run's information cutoff, never because the unit is
known to have exited; and the identical construction regenerates for a
forecast year from the then-current 860 (the planned-additions pipeline
already reads the same form's proposed-generator schedule as a forward
input). The filed date is an ex-ante owner PLAN — a forward driver that
responds to changed conditions (it moved for Baldwin, Sherco 1, Schahfer
17/18) — not a measured outcome.

**Verification posture (``verify=True``, the ``hindcast_verified_announced_
exits`` trade).** The vintage set is checked, per unit, against the LATER
in-repo EIA-860 vintages: the latest later snapshot that still lists the
unit operable gives its CURRENT filed date. A later date is a FILED DEFERRAL
(the owner re-filed Schedule 3 — a published per-unit instrument), a dropped
date is a plan withdrawn (a sale with continued operation, a cancelled
closure), and an absent unit means it left the operable file — it exited, so
the vintage date stands. This can DEFER or CANCEL a vintage date but never
INJECT an exit or move one EARLIER (an earlier re-filing is recorded as
``advanced`` and the vintage date stands; a date first filed after the
vintage is not added), the same
"suppress a never-executed exit, never inject one" discipline the flag's
reversal leg carries. It is zero-parameter and applied uniformly — no fitted
filter (rule 21 [R-DOF]) — and every disposition is recorded on the row so a
scorer/finding can separate the ex-ante set from the verified set. Off, the
loader is the pure ex-ante construction: an undated deferral is a false
positive at full magnitude.

**Reversal registry.** Plants in ``reversed_plant_codes``
(:func:`market_sim.data.confirmed_retirements.load_announced_reversal_plants`
— every registry row superseded by a public counter-instrument, e.g. J H
Campbell under DOE §202(c)) are dropped whatever the vintage says.

Consumption: :func:`market_sim.model.capacity.apply_confirmed_exits` (rows
duck-type :class:`~market_sim.data.confirmed_retirements.ConfirmedExit`:
unit-grain rows drop the unit, plant-binned rows derate the plant's
tranches, first-half months carry a completion leg) at step 1 of
:func:`market_sim.model.capacity.evolve_fleet` and in the first-year
:func:`market_sim.data.fleet.build_base_fleet` backlog.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from market_sim.config.paths import EIA_860_DIR, active_eia860_dir
from market_sim.data.fleet.models import (
    BA_CODE_TO_ISO,
    EIA_860_PARQUET_NAME,
    EIA860_OPERABLE_VINTAGE,
    operable_vintage_year,
)

logger = logging.getLogger(__name__)

#: Fuel classes the channel carries — the same set
#: :data:`market_sim.model.capacity_evolution.retirements._FOSSIL_FUELS`
#: exempts from the non-fossil announced step (duplicated here, not imported,
#: to keep ``data`` free of a ``model`` import; the test suite pins equality).
FOSSIL_FUELS: frozenset[str] = frozenset(
    {"coal", "gas_ct", "gas_cc", "gas_st", "gas_cc_ccs", "oil"}
)

#: Raw EIA-860 operable sheet (month + sector columns the canonical
#: ``eia860_generators.parquet`` does not carry).
_OPERABLE_SHEET_NAME = "eia860_generator_operable.parquet"

#: Row dispositions under the verification posture.
DISPOSITION_VINTAGE = "vintage"  # ex-ante row, honored as filed at the vintage
DISPOSITION_KEPT = "kept"  # verified: latest later vintage still carries the date
DISPOSITION_DEFERRED = "deferred"  # verified: re-filed to a later date
DISPOSITION_ADVANCED = (
    "advanced"  # verified: re-filed earlier — recorded, vintage date stands
)
DISPOSITION_CANCELLED = "cancelled"  # verified: later vintage carries no date
DISPOSITION_EXITED = "exited"  # verified: unit absent from every later vintage
DISPOSITION_REVERSED = "reversed"  # registry counter-instrument (dropped)


@dataclass(frozen=True)
class AnnouncedFossilExit:
    """One owner-filed fossil retirement date, ``ConfirmedExit``-shaped.

    ``plant_id`` / ``generator_id`` / ``exit_year`` / ``exit_month`` / ``mw``
    are exactly the attributes :func:`market_sim.model.capacity.
    apply_confirmed_exits` reads. The remaining fields are provenance: the
    vintage the date was read from, the fuel class, the owner sector code,
    the ORIGINAL vintage date (identical to ``exit_year``/``exit_month``
    unless verification moved it), the verifying vintage, and the
    disposition vocabulary above.
    """

    plant_id: int
    generator_id: str
    exit_year: int
    exit_month: int | None
    mw: float | None
    fuel_type: str
    filed_vintage: int
    vintage_exit_year: int
    vintage_exit_month: int | None
    disposition: str = DISPOSITION_VINTAGE
    verified_vintage: int | None = None
    # The FIRST later vintage whose filing differs from the vintage row (the
    # vintage in which the deferral/withdrawal was filed) — the knowability
    # diagnostic: a change first filed in vintage V was knowable for solve
    # year V + 1 onward.
    first_change_vintage: int | None = None
    sector: int | None = None
    plant_name: str = ""
    extra: dict = field(default_factory=dict, compare=False)


def _to_int(value: object) -> int | None:
    try:
        if value is None or pd.isna(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _fuel_of(row: pd.Series) -> str | None:
    # Local import: fleet.eia860 imports config/paths at module load; the
    # fuel mapper is the ONE taxonomy the dispatch fleet is classed on.
    from market_sim.data.fleet.eia860 import _map_fuel_type

    return _map_fuel_type(
        row.get("technology"), row.get("energy_source"), row.get("prime_mover")
    )


def _read_vintage_frame(data_dir: Path) -> pd.DataFrame | None:
    """Canonical generators parquet (+ month/sector from the raw sheet)."""
    path = Path(data_dir) / EIA_860_PARQUET_NAME
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df.copy()
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df[df["plant_id"].notna()]
    df["plant_id"] = df["plant_id"].astype("int64")
    df["generator_id"] = df["generator_id"].astype(str).str.strip()
    sheet = Path(data_dir) / _OPERABLE_SHEET_NAME
    if sheet.exists():
        raw = pd.read_parquet(sheet)
        cols = {
            "Plant Code": "plant_id",
            "Generator ID": "generator_id",
            "Planned Retirement Month": "planned_retirement_month",
            "Sector": "sector",
        }
        have = [c for c in cols if c in raw.columns]
        if "Plant Code" in have and "Generator ID" in have:
            extra = raw[have].rename(columns=cols)
            extra["plant_id"] = pd.to_numeric(extra["plant_id"], errors="coerce")
            extra = extra[extra["plant_id"].notna()]
            extra["plant_id"] = extra["plant_id"].astype("int64")
            extra["generator_id"] = extra["generator_id"].astype(str).str.strip()
            extra = extra.drop_duplicates(["plant_id", "generator_id"])
            df = df.merge(extra, on=["plant_id", "generator_id"], how="left")
    if "planned_retirement_month" not in df.columns:
        df["planned_retirement_month"] = pd.NA
    if "sector" not in df.columns:
        df["sector"] = pd.NA
    return df


def _iso_fossil_operable(df: pd.DataFrame, iso: str) -> pd.DataFrame:
    """Filter a vintage frame to the ISO's OPERABLE (``OP``) fossil units —
    the same membership the dispatch fleet reads (``_rows_to_generators``
    keeps ``status == "OP"``; ``balancing_authority_code`` → ISO)."""
    ba_iso = df["balancing_authority_code"].astype(str).str.strip().map(BA_CODE_TO_ISO)
    out = df[ba_iso == iso.upper()]
    status = out["status"].astype(str).str.strip().str.upper()
    out = out[status == "OP"].copy()
    out["fuel_type"] = out.apply(_fuel_of, axis=1)
    return out[out["fuel_type"].isin(FOSSIL_FUELS)]


def later_vintage_dirs(
    vintage_year: int, base: Path | None = None
) -> list[tuple[int, Path]]:
    """Committed EIA-860 snapshots STRICTLY LATER than ``vintage_year``.

    Every ``vintage_<year>/`` directory under ``base`` with ``year >
    vintage_year``, plus the canonical top-level snapshot
    (:data:`EIA860_OPERABLE_VINTAGE`) when it is later than the last vintage
    directory. Ascending by year. The verification posture reads these; the
    ex-ante posture never calls this.
    """
    base = Path(base) if base is not None else EIA_860_DIR
    found: list[tuple[int, Path]] = []
    if base.exists():
        for p in base.iterdir():
            if p.is_dir() and p.name.startswith("vintage_"):
                try:
                    y = int(p.name.removeprefix("vintage_"))
                except ValueError:
                    continue
                if y > vintage_year and (p / EIA_860_PARQUET_NAME).exists():
                    found.append((y, p))
    found.sort()
    last = found[-1][0] if found else vintage_year
    if EIA860_OPERABLE_VINTAGE > last and (base / EIA_860_PARQUET_NAME).exists():
        found.append((EIA860_OPERABLE_VINTAGE, base))
    return found


def _verify_against_later_vintages(
    rows: list[AnnouncedFossilExit], iso: str, later: list[tuple[int, Path]]
) -> list[AnnouncedFossilExit]:
    """Apply the verification posture (module docstring) to ``rows``."""
    if not later:
        return rows
    # Latest later-vintage record per (plant, gid): (vintage, year, month).
    latest: dict[tuple[int, str], tuple[int, int | None, int | None]] = {}
    # First later vintage whose (year, month) differs from the vintage row.
    first_change: dict[tuple[int, str], int] = {}
    vintage_of = {(r.plant_id, r.generator_id): r for r in rows}
    for vy, vdir in later:
        frame = _read_vintage_frame(vdir)
        if frame is None:
            continue
        frame = _iso_fossil_operable(frame, iso)
        for r in frame.itertuples(index=False):
            key = (int(r.plant_id), str(r.generator_id))
            ry = _to_int(getattr(r, "planned_retirement_year", None))
            rm = _to_int(getattr(r, "planned_retirement_month", None))
            latest[key] = (vy, ry, rm)
            base = vintage_of.get(key)
            if (
                base is not None
                and key not in first_change
                and (ry, rm) != (base.vintage_exit_year, base.vintage_exit_month)
            ):
                first_change[key] = vy
    out: list[AnnouncedFossilExit] = []
    for row in rows:
        key = (row.plant_id, row.generator_id)
        rec = latest.get(key)
        if rec is None:
            out.append(_replace(row, disposition=DISPOSITION_EXITED))
            continue
        vy, ry, rm = rec
        fcv = first_change.get(key)
        if ry is None:
            out.append(
                _replace(
                    row,
                    disposition=DISPOSITION_CANCELLED,
                    verified_vintage=vy,
                    first_change_vintage=fcv,
                )
            )
            continue
        if (ry, rm) == (row.vintage_exit_year, row.vintage_exit_month):
            out.append(_replace(row, disposition=DISPOSITION_KEPT, verified_vintage=vy))
            continue
        if (ry, rm or 12) > (row.vintage_exit_year, row.vintage_exit_month or 12):
            # A filed deferral: honored as the later vintage's information.
            out.append(
                _replace(
                    row,
                    exit_year=ry,
                    exit_month=rm,
                    disposition=DISPOSITION_DEFERRED,
                    verified_vintage=vy,
                    first_change_vintage=fcv,
                )
            )
            continue
        # Re-filed EARLIER: recorded, but the vintage date STANDS — the
        # verification posture may defer or cancel a vintage exit, never move
        # one earlier (the "never inject" discipline: an earlier date is
        # information the vintage did not have, so honoring it would let the
        # verified leg out-time the ex-ante construction with hindsight).
        out.append(
            _replace(
                row,
                disposition=DISPOSITION_ADVANCED,
                verified_vintage=vy,
                first_change_vintage=fcv,
            )
        )
    return out


def _replace(row: AnnouncedFossilExit, **changes: object) -> AnnouncedFossilExit:
    from dataclasses import replace

    return replace(row, **changes)


def load_announced_fossil_exits(
    iso: str,
    data_dir: Path | None = None,
    *,
    verify: bool = False,
    reversed_plant_codes: frozenset[int] = frozenset(),
    vintage_root: Path | None = None,
) -> list[AnnouncedFossilExit]:
    """Return the ISO's owner-filed fossil retirement dates, vintage-gated.

    Args:
        iso: Model ISO name.
        data_dir: EIA-860 snapshot directory to read the VINTAGE set from.
            ``None`` resolves the active directory (a ``vintage_<year>/`` dir
            in a vintage-seeded run) — the information set of the run.
        verify: Apply the verification posture (module docstring) against
            the later in-repo vintages. ``False`` is the pure ex-ante
            construction.
        reversed_plant_codes: Plants whose announced exit a public
            counter-instrument reversed (dropped; disposition ``reversed``
            is logged, the row is not returned — a reversed plant carries no
            exogenous exit).
        vintage_root: Root holding the ``vintage_<year>/`` directories the
            verification scans (tests); ``None`` = the canonical EIA-860
            root.

    Returns:
        Rows sorted by ``(exit_year, plant_id, generator_id)``; every row
        carries a non-null ``exit_year``. Empty when the snapshot is absent
        (logged) or nothing is dated. Rows with disposition ``cancelled``
        are dropped from the returned list (nothing to apply) — the count is
        logged; the :func:`disposition_table` companion returns the full
        audited set for a finding.
    """
    return [
        r
        for r in disposition_table(
            iso,
            data_dir,
            verify=verify,
            reversed_plant_codes=reversed_plant_codes,
            vintage_root=vintage_root,
        )
        if r.disposition not in (DISPOSITION_CANCELLED, DISPOSITION_REVERSED)
    ]


def disposition_table(
    iso: str,
    data_dir: Path | None = None,
    *,
    verify: bool = False,
    reversed_plant_codes: frozenset[int] = frozenset(),
    vintage_root: Path | None = None,
) -> list[AnnouncedFossilExit]:
    """The full audited row set behind :func:`load_announced_fossil_exits`,
    INCLUDING the ``cancelled`` / ``reversed`` rows the loader drops — so a
    finding can report the ex-ante set, the verified set and every
    disposition at full magnitude from one call."""
    iso = iso.upper()
    data_dir = Path(data_dir) if data_dir is not None else active_eia860_dir()
    vintage = operable_vintage_year(data_dir)
    frame = _read_vintage_frame(data_dir)
    if frame is None:
        logger.warning(
            "announced fossil exits unavailable for %s: missing %s",
            iso,
            data_dir / EIA_860_PARQUET_NAME,
        )
        return []
    frame = _iso_fossil_operable(frame, iso)
    rows: list[AnnouncedFossilExit] = []
    for r in frame.itertuples(index=False):
        ry = _to_int(getattr(r, "planned_retirement_year", None))
        if ry is None:
            continue
        rm = _to_int(getattr(r, "planned_retirement_month", None))
        if rm is not None and not 1 <= rm <= 12:
            rm = None
        mw = pd.to_numeric(getattr(r, "nameplate_capacity_mw", None), errors="coerce")
        if pd.isna(mw) or float(mw) <= 0.0:
            mw = pd.to_numeric(
                getattr(r, "net_summer_capacity_mw", None), errors="coerce"
            )
        pid = int(r.plant_id)
        row = AnnouncedFossilExit(
            plant_id=pid,
            generator_id=str(r.generator_id),
            exit_year=ry,
            exit_month=rm,
            mw=(None if pd.isna(mw) else float(mw)),
            fuel_type=str(r.fuel_type),
            filed_vintage=int(vintage),
            vintage_exit_year=ry,
            vintage_exit_month=rm,
            sector=_to_int(getattr(r, "sector", None)),
            plant_name=str(getattr(r, "plant_name", "") or ""),
        )
        if pid in reversed_plant_codes:
            row = _replace(row, disposition=DISPOSITION_REVERSED)
        rows.append(row)
    if verify:
        live = [r for r in rows if r.disposition != DISPOSITION_REVERSED]
        dead = [r for r in rows if r.disposition == DISPOSITION_REVERSED]
        rows = (
            _verify_against_later_vintages(
                live, iso, later_vintage_dirs(vintage, vintage_root)
            )
            + dead
        )
    rows.sort(key=lambda e: (e.exit_year, e.plant_id, e.generator_id))
    n_live = sum(
        1
        for r in rows
        if r.disposition not in (DISPOSITION_CANCELLED, DISPOSITION_REVERSED)
    )
    logger.info(
        "announced fossil exits (%s, vintage %d, verify=%s): %d dated row(s), "
        "%d live, %.0f MW live; dispositions %s",
        iso,
        vintage,
        verify,
        len(rows),
        n_live,
        sum(
            (r.mw or 0.0)
            for r in rows
            if r.disposition not in (DISPOSITION_CANCELLED, DISPOSITION_REVERSED)
        ),
        {
            d: sum(1 for r in rows if r.disposition == d)
            for d in sorted({r.disposition for r in rows})
        },
    )
    return rows


def rows_as_records(rows: list[AnnouncedFossilExit]) -> list[dict]:
    """JSON-ready dicts (the ledger / finding artifact form)."""
    return [
        {
            "plant_id": r.plant_id,
            "generator_id": r.generator_id,
            "plant_name": r.plant_name,
            "fuel": r.fuel_type,
            "mw": r.mw,
            "sector": r.sector,
            "filed_vintage": r.filed_vintage,
            "vintage_exit_year": r.vintage_exit_year,
            "vintage_exit_month": r.vintage_exit_month,
            "exit_year": r.exit_year,
            "exit_month": r.exit_month,
            "disposition": r.disposition,
            "verified_vintage": r.verified_vintage,
            "first_change_vintage": r.first_change_vintage,
        }
        for r in rows
    ]
