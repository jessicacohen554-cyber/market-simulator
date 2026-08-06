#!/usr/bin/env python
"""Build the capacity-hindcast scoring target from the latest EIA-860 release.

Emits ``data/raw/_validation-source/capacity_actuals_<iso>.csv`` — every
generator **retirement** and **addition** an ISO saw in 2021-2025, in the
model's own fuel taxonomy — from the committed EIA-860 release series
(operable + retired-and-canceled sheets, current release and every
``vintage_<year>/`` snapshot). These are *outcome registry facts* (COD and
cessation dates), the admissible scoring target for
``scripts/score_capacity_hindcast.py`` (plan §1.2.3).

**Retirements are dated at PHYSICAL cessation, not at the paper date**
(FFR-7A, owner decision D-21(b); evidence FFR-6A
``docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md`` §3.3, verdict
rows 5a/5b). Two defects made the old "current retired sheet, ``Retirement
Year`` verbatim" target un-gradeable:

* It **counted only status RE**, so a unit EIA still carries on the *operable*
  sheet at status ``OS`` — out of service, not expected back next calendar
  year — never appeared at all. V H Braunig 1+2 (plant 3612, 477 MW, ERCOT)
  and Sandy Creek (plant 56611, 1008 MW coal) are real in-window exits the old
  target missed entirely.
* It **took the reported retirement year verbatim**, so a unit that physically
  stopped years earlier and was only *papered* later scored as an in-window
  exit. J T Deely 1+2 (plant 6181, 932 MW coal, ERCOT) ceased operating in
  2018 — status ``OS`` in every release from 2018 on — but carries EIA
  ``Retirement Year`` 2023. The model's vintage-2020 fleet basis does not
  carry it (``data/fleet/eia860.py`` keeps ``status == "OP"`` only), so no
  screen could ever retire it, yet the scorer graded against it. Potter
  Station 2 (1660, NEISO) and Ravenswood GT32/GT34 (2500, NYISO) are the same
  pathology.

:func:`physical_exit_year` fixes both from the same EIA-860 field —
``Status`` read across the release series (see its docstring for the rule).
:data:`FLEET_VINTAGE_YEAR` then applies the rule-5a hygiene gate: a unit
already inactive at the fleet-basis vintage is dropped outright, because the
hindcast arm's base fleet cannot carry it.

Information gate (rule 13/14): every field used is either **vintage-visible**
(the status a release published for its own reporting year) or **outcome
registry data used ONLY as a validation target** — rule 13's benchmark branch.
No measured outcome is fed back into any solve path; this file writes a
scoring target and nothing else.

Rule 22: the window is 2021-2025. 2022 rows are registry dates on real units
(EIA-860 already carries them in the current release), not the quarantined
2022 *bench* domain — they are retained so cumulative scoring is complete, and
the scorer flags any timing metric that lands on the 2022 bridge. No 2026 rows
are ever emitted.

Usage::

    python scripts/data/build_capacity_actuals.py --iso ERCOT
    python scripts/data/build_capacity_actuals.py --iso PJM
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.config.paths import CALIBRATION_DIR, EIA_860_DIR  # noqa: E402
from market_sim.data.fleet import BA_CODE_TO_ISO, _map_fuel_type  # noqa: E402

WINDOW = range(2021, 2026)  # 2021-2025 inclusive; never 2026 (rule 22).
LARGE_UNIT_MW = 300.0  # flagged per plan §1.2.3

# The emitted row schema, fixed so an ISO with no changed rows keeps a
# byte-identical CSV body across builder revisions (``large_unit`` is appended
# by :func:`main`). Additions and retirements share it.
_RETIREMENT_COLUMNS = ("kind", "unit_id", "plant_id", "fuel", "mw", "year", "state")

# EIA-860 Schedule 3 generator ``Status`` codes (EIA-860 instructions, the
# "Generator Status Codes" table shipped with every release):
#   OP  operating
#   SB  standby / backup — available for service, not normally used
#   OA  out of service, but EXPECTED to return within the next calendar year
#   OS  out of service, and NOT expected to return within the next calendar year
#   RE  retired (moved to the retired-and-canceled sheet)
# A *physical exit* is OS or RE. OA and SB are deliberately excluded: EIA
# defines both as still-available capacity, and the fleet loader treats them
# the same way (``data/fleet/eia860.py`` re-carries OA units and scopes that
# channel to OA explicitly, "OS/SB/retired statuses are deliberately" not
# re-carried).
INACTIVE_STATUSES = frozenset({"OS", "RE"})

# The EIA-860 vintage the hindcast's base fleet is seeded from — one year
# before the first scored year, matching ``run_capacity_hindcast.py``'s plain
# hindcast (``--vintage 2020``, plan §1.1, first scored year 2021). Derived
# from WINDOW rather than written as a literal so the two cannot drift.
FLEET_VINTAGE_YEAR = min(WINDOW) - 1

# Resolved through the registry (config/paths.py) — the old Path("data/raw/…")
# literals here were CWD-relative and only worked from the repo root.
OUT_DIR = CALIBRATION_DIR
# Lives in OUT_DIR, not EIA_860_DIR: data/raw/eia-860/*.csv is gitignored
# (override-CSV convention, source of truth there is parquet/json only), and
# this file is a committed, citation-backed permanent fix, not a local
# override -- see OUT_DIR/README.md's "RD-5 actuals-coverage fix" note.
RETIRED_SHEET_GAP_FIX = OUT_DIR / "retired_sheet_coverage_gaps.csv"


def _iso_to_ba(iso: str) -> set[str]:
    """Return the EIA balancing-authority codes that map to ``iso``."""
    return {ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}


def _renewable_or_storage_fuel(technology: object, prime_mover: object) -> str | None:
    """Classify the non-thermal resources ``_map_fuel_type`` returns None for."""
    tech = str(technology or "").strip().lower()
    mover = str(prime_mover or "").strip().upper()
    if "onshore wind" in tech or "offshore wind" in tech or mover == "WT":
        return "wind"
    if "solar" in tech or "photovoltaic" in tech or mover == "PV":
        return "solar"
    if "batter" in tech or mover in {"BA", "ES"} or "energy storage" in tech:
        return "storage"
    if "pumped" in tech or mover == "PS":
        return "storage"
    if "hydro" in tech or mover in {"HY", "HC"}:
        return "hydro"
    if "geothermal" in tech:
        return "geothermal"
    return None


def _fuel(technology: object, energy_source: object, prime_mover: object) -> str:
    """Model fuel/tech class, thermal first then renewable/storage."""
    thermal = _map_fuel_type(technology, energy_source, prime_mover)
    if thermal is not None:
        return thermal
    return _renewable_or_storage_fuel(technology, prime_mover) or "other"


def _uid(plant_code: int, generator_id: object) -> str:
    """``<plant>_<generator>`` id with the CSV comment char stripped.

    Some EIA generator IDs contain ``#`` (e.g. NYISO plant 63625 unit ``HJD#1``).
    Both this file's provenance header and the scorer's ``load_actuals`` read the
    CSV with ``pandas comment="#"``, which truncates *any* line at the first
    ``#`` — mangling such a row into an all-NaN entry. Replacing ``#`` with ``-``
    keeps the id readable and the CSV parseable; no existing committed actuals
    row carries ``#``, so ERCOT/PJM/MISO are byte-unchanged.
    """
    return f"{plant_code}_{str(generator_id).replace('#', '-')}"


def _plant_ba(release_dir: Path | None = None) -> pd.Series:
    """Return a Plant Code → Balancing Authority Code map from the plant sheet."""
    root = EIA_860_DIR if release_dir is None else release_dir
    plant = pd.read_parquet(root / "eia860_plant.parquet")
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    return plant.drop_duplicates("Plant Code").set_index(
        plant["Plant Code"].astype(float).astype(int)
    )["Balancing Authority Code"]


# --------------------------------------------------------------------------- #
# EIA-860 release series → per-unit status history (FFR-7A)
# --------------------------------------------------------------------------- #
def current_release_year() -> int:
    """Reporting year of the top-level (current) EIA-860 release.

    EIA-860 is an annual survey: a release for reporting year *Y* reports the
    fleet as of 31-Dec-*Y*, so the newest ``Operating Year`` on its operable
    sheet **is** *Y*. Verified against every committed snapshot — each
    ``vintage_<Y>/eia860_generators.parquet`` has ``max(operating_year) == Y``
    (2018…2024), and the current release's max is 2025 — so the release year is
    read from the data rather than pinned to a literal that would rot at the
    next intake. Falls back to the last window year when the sheet carries no
    usable ``operating_year`` (fixture trees in the tests).
    """
    gens = pd.read_parquet(EIA_860_DIR / "eia860_generators.parquet")
    if "operating_year" not in gens.columns or gens.empty:
        return max(WINDOW)
    years = pd.to_numeric(gens["operating_year"], errors="coerce").dropna()
    return int(years.max()) if len(years) else max(WINDOW)


def release_series() -> list[tuple[int, Path]]:
    """``(reporting_year, directory)`` for every committed release, oldest first.

    The ``vintage_<year>/`` snapshots plus the top-level current release. A
    vintage directory's name *is* its reporting year; the current release's is
    derived by :func:`current_release_year`.
    """
    releases = [
        (int(d.name.split("_")[1]), d)
        for d in sorted(EIA_860_DIR.glob("vintage_*"))
        if d.is_dir() and d.name.split("_")[-1].isdigit()
    ]
    releases.append((current_release_year(), EIA_860_DIR))
    return sorted(releases, key=lambda pair: pair[0])


def _release_frame(year: int, release_dir: Path) -> pd.DataFrame:
    """One release's generator rows, operable + retired, in a common schema.

    Columns: ``plant_id, generator_id, release_year, status, ba, technology,
    energy_source, prime_mover, mw, state, retirement_year``. Sheets absent
    from a partial snapshot (``vintage_2023``/``vintage_2024`` ship the
    operable sheet only) are skipped, never faked.
    """
    frames: list[pd.DataFrame] = []

    operable = release_dir / "eia860_generators.parquet"
    if operable.is_file():
        gens = pd.read_parquet(operable)
        if "status" in gens.columns and not gens.empty:
            frames.append(
                pd.DataFrame(
                    {
                        "plant_id": pd.to_numeric(gens["plant_id"], errors="coerce"),
                        "generator_id": gens["generator_id"].astype(str).str.strip(),
                        "status": gens["status"].astype(str).str.strip().str.upper(),
                        "ba": gens.get("balancing_authority_code"),
                        "technology": gens.get("technology"),
                        "energy_source": gens.get("energy_source"),
                        "prime_mover": gens.get("prime_mover"),
                        "mw": pd.to_numeric(
                            gens["nameplate_capacity_mw"], errors="coerce"
                        ),
                        "state": gens.get("state"),
                        "retirement_year": pd.NA,
                    }
                )
            )

    retired = release_dir / "eia860_generator_retired_and_canceled.parquet"
    if retired.is_file():
        ret = pd.read_parquet(retired)
        codes = pd.to_numeric(ret["Plant Code"], errors="coerce")
        ret = ret[codes.notna()].copy()
        ret["plant_id"] = codes[codes.notna()].astype(int)
        ba_map = _plant_ba(release_dir)
        retirement_year = pd.to_numeric(ret["Retirement Year"], errors="coerce")
        # The sheet carries retirements (RE) alongside cancellations (CN) and
        # indefinitely-postponed proposals (IP), which are NOT exits — only RE
        # is in INACTIVE_STATUSES. Where a snapshot omits the Status column,
        # a dated row is a retirement and an undated one a cancellation.
        status = (
            ret["Status"].astype(str).str.strip().str.upper()
            if "Status" in ret.columns
            else retirement_year.notna().map({True: "RE", False: "CN"})
        )
        frames.append(
            pd.DataFrame(
                {
                    "plant_id": ret["plant_id"],
                    "generator_id": ret["Generator ID"].astype(str).str.strip(),
                    "status": status,
                    "ba": ret["plant_id"].map(ba_map),
                    "technology": ret.get("Technology"),
                    "energy_source": ret.get("Energy Source 1"),
                    "prime_mover": ret.get("Prime Mover"),
                    "mw": pd.to_numeric(
                        ret["Nameplate Capacity (MW)"], errors="coerce"
                    ),
                    "state": ret.get("State"),
                    "retirement_year": retirement_year,
                }
            )
        )

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out = out[out["plant_id"].notna()].copy()
    out["plant_id"] = out["plant_id"].astype(int)
    out["release_year"] = year
    return out


def load_release_history(bas: set[str]) -> pd.DataFrame:
    """Every release's rows for units that map to ``bas`` in *any* release.

    A unit's balancing authority is resolved from whichever releases carry it
    (the current plant sheet drops some plants outright — the RD-5 coverage
    gap), so a plant that has vanished from the newest release is still scoped
    to its ISO from the vintage that last reported it.
    """
    frames = [_release_frame(year, d) for year, d in release_series()]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(
            columns=["plant_id", "generator_id", "release_year", "status"]
        )
    hist = pd.concat(frames, ignore_index=True)
    in_iso = hist.loc[hist["ba"].isin(bas), ["plant_id", "generator_id"]]
    keys = set(map(tuple, in_iso.drop_duplicates().to_numpy()))
    if not keys:
        return hist.iloc[0:0]
    unit_key = list(zip(hist["plant_id"], hist["generator_id"]))
    return hist[[k in keys for k in unit_key]].copy()


def physical_exit_year(
    statuses: dict[int, str], reported_year: int | None
) -> int | None:
    """Year a unit physically left the fleet, or ``None`` if it is still in it.

    ``statuses`` maps an EIA-860 reporting year to the ``Status`` that
    release published; ``reported_year`` is the ``Retirement Year`` from the
    most recent release that carries the unit on its retired sheet (``None``
    when no release ever did). The rule:

    1. If the **most recent observed** status is active (not in
       :data:`INACTIVE_STATUSES`), the unit is in the fleet — no exit. This is
       what keeps a *reversed* retirement (Palisades: retired 2022, restarted
       2025 and back on the operable sheet) from scoring as an exit off its
       stale RE row.
    2. Otherwise the exit is the **first year of the final unbroken run of
       inactive statuses** — the release year from which the registry never
       again reported the unit as available.
    3. The answer is ``min`` of that run start and ``reported_year``: EIA's own
       retirement date wins whenever it is earlier (the normal case, since a
       release published for year *Y* reports retirements that happened in
       *Y* or before), and the status evidence corrects it down when the
       registry itself shows the unit was already out of service years before
       the paper date (J T Deely: OS from 2018, ``Retirement Year`` 2023).

    Only *observed* years take part — a release that omits the unit (or ships
    no retired sheet at all) is a gap, not a return to service. The series is
    left-censored at the oldest committed release, so a unit already inactive
    then is dated at that release and lands outside any later window, which is
    the correct answer for the window even though the true date is earlier.
    """
    years = sorted(statuses)
    if not years:
        return reported_year
    if statuses[years[-1]] not in INACTIVE_STATUSES:
        return None
    run_start = years[-1]
    for year in reversed(years[:-1]):
        if statuses[year] not in INACTIVE_STATUSES:
            break
        run_start = year
    return min(run_start, reported_year) if reported_year is not None else run_start


def build_additions(bas: set[str]) -> pd.DataFrame:
    """Additions: operable units whose COD (Operating Year) is in the window."""
    gens = pd.read_parquet(EIA_860_DIR / "eia860_generators.parquet")
    gens = gens[gens["balancing_authority_code"].isin(bas)].copy()
    gens["operating_year"] = pd.to_numeric(gens["operating_year"], errors="coerce")
    gens = gens[gens["operating_year"].isin(list(WINDOW))]
    rows = []
    for _, g in gens.iterrows():
        rows.append(
            {
                "kind": "addition",
                "unit_id": _uid(int(g["plant_id"]), g["generator_id"]),
                "plant_id": int(g["plant_id"]),
                "fuel": _fuel(g["technology"], g["energy_source"], g["prime_mover"]),
                "mw": float(g["nameplate_capacity_mw"] or 0.0),
                "year": int(g["operating_year"]),
                "state": g.get("state", ""),
            }
        )
    return pd.DataFrame(rows)


def load_retired_sheet_gap_fix(bas: set[str]) -> pd.DataFrame:
    """Retirement rows for plants the CURRENT top-level retired sheet omits.

    RD-5 (forecast-retirement-calibration-plan-2026-07.md §5): the committed
    ``eia860_generator_retired_and_canceled.parquet`` "2025 Early Release"
    snapshot has fully dropped some plants that genuinely retired inside the
    scoring window (Indian Point 3) or un-retired since (Palisades' 2025
    restart moved it back to the operable sheet, erasing its 2022 retirement
    row from the current snapshot). :data:`RETIRED_SHEET_GAP_FIX` carries
    those rows verbatim from this repo's own earlier EIA-860 vintage
    snapshots (still the authoritative EIA-860 survey, just read at the
    vintage where the plant was still in that release's retired sheet) with
    an explicit ``ba_code`` column, since the missing plant(s) may also be
    absent from the current plant sheet and so cannot resolve a BA via
    :func:`_plant_ba`. Returns an empty frame if the fix file is absent.
    """
    if not RETIRED_SHEET_GAP_FIX.is_file():
        return pd.DataFrame()
    gap = pd.read_csv(RETIRED_SHEET_GAP_FIX, comment="#")
    gap = gap[gap["ba_code"].isin(bas)]
    gap = gap[pd.to_numeric(gap["retirement_year"], errors="coerce").isin(list(WINDOW))]
    rows = []
    for _, g in gap.iterrows():
        rows.append(
            {
                "kind": "retirement",
                "unit_id": _uid(int(g["plant_code"]), g["generator_id"]),
                "plant_id": int(g["plant_code"]),
                "fuel": _fuel(g["technology"], g["energy_source_1"], g["prime_mover"]),
                "mw": float(g["nameplate_capacity_mw"] or 0.0),
                "year": int(g["retirement_year"]),
                "state": g.get("state", ""),
            }
        )
    return pd.DataFrame(rows)


def build_retirements(
    bas: set[str],
    *,
    fleet_vintage: int | None = FLEET_VINTAGE_YEAR,
    audit: dict | None = None,
) -> pd.DataFrame:
    """Retirements: units whose **physical exit** year falls inside the window.

    One row per unit, dated by :func:`physical_exit_year` off the EIA-860
    ``Status`` series rather than off the current retired sheet's
    ``Retirement Year`` alone — so an ``OS`` mothball counts (V H Braunig,
    Sandy Creek) and a late paper date does not (J T Deely). Unit metadata
    (fuel, nameplate, state) is taken from the most recent release that
    carries the unit.

    ``fleet_vintage`` applies the rule-5a hygiene gate: a unit whose status at
    that release is already in :data:`INACTIVE_STATUSES` is dropped, because
    the hindcast arm seeded from that vintage has no such unit to retire —
    ``data/fleet/eia860.py`` keeps ``status == "OP"`` rows only. Pass ``None``
    to build an ungated target. A unit merely *absent* from the vintage is not
    gated (it was built inside the window, and the model can build it too).

    Unions in :func:`load_retired_sheet_gap_fix` so plants the current
    top-level snapshot has dropped (RD-5) still score (see that function's
    docstring); the gap-fix rows are curated overrides and bypass the status
    logic, which is what keeps a *reversed* retirement (Palisades) in the
    target for RC-0B to adjudicate rather than silently dropping it here.

    ``audit``, when given, is populated with ``excluded`` (rows the status
    rule or the vintage gate kept out, each with its reason and status
    history) so callers can report the delta instead of guessing at it.
    """
    hist = load_release_history(bas)
    vintage_status: dict[tuple[int, str], str] = {}
    if fleet_vintage is not None and not hist.empty:
        at_vintage = hist[hist["release_year"] == fleet_vintage]
        vintage_status = {
            (int(r.plant_id), r.generator_id): r.status for r in at_vintage.itertuples()
        }

    rows: list[dict] = []
    excluded: list[dict] = []
    for (plant_id, generator_id), grp in (
        hist.groupby(["plant_id", "generator_id"], sort=True) if not hist.empty else []
    ):
        grp = grp.sort_values("release_year")
        statuses = dict(zip(grp["release_year"], grp["status"]))
        reported = grp["retirement_year"].dropna()
        reported_year = int(reported.iloc[-1]) if len(reported) else None
        year = physical_exit_year(statuses, reported_year)
        if year is None or year not in WINDOW:
            continue
        latest = grp.iloc[-1]
        record = {
            "kind": "retirement",
            "unit_id": _uid(int(plant_id), generator_id),
            "plant_id": int(plant_id),
            "fuel": _fuel(
                latest["technology"], latest["energy_source"], latest["prime_mover"]
            ),
            "mw": float(latest["mw"] or 0.0),
            "year": int(year),
            "state": latest["state"] if pd.notna(latest["state"]) else "",
        }
        gate = vintage_status.get((int(plant_id), generator_id))
        if gate in INACTIVE_STATUSES:
            excluded.append(
                {
                    **record,
                    "reason": f"inactive ({gate}) at the {fleet_vintage} fleet vintage",
                    "history": ",".join(
                        f"{y}:{s}" for y, s in sorted(statuses.items())
                    ),
                }
            )
            continue
        rows.append(record)

    df = pd.DataFrame(rows, columns=list(_RETIREMENT_COLUMNS))
    gap_fix = load_retired_sheet_gap_fix(bas)
    if not gap_fix.empty:
        existing = set(zip(df["plant_id"], df["unit_id"])) if not df.empty else set()
        gap_fix = gap_fix[
            ~gap_fix.apply(lambda r: (r["plant_id"], r["unit_id"]) in existing, axis=1)
        ]
        df = pd.concat([df, gap_fix], ignore_index=True)
    if audit is not None:
        audit["excluded"] = excluded
        audit["fleet_vintage"] = fleet_vintage
        audit["releases"] = [year for year, _ in release_series()]
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO, e.g. ERCOT or PJM.")
    parser.add_argument(
        "--fleet-vintage",
        type=int,
        default=FLEET_VINTAGE_YEAR,
        help=(
            "EIA-860 vintage the graded arm's base fleet is seeded from; units "
            f"already out of service then are dropped (default {FLEET_VINTAGE_YEAR}). "
            "Pass -1 to build an ungated target."
        ),
    )
    args = parser.parse_args(argv)
    iso = args.iso.upper()
    bas = _iso_to_ba(iso)
    if not bas:
        raise SystemExit(f"no EIA balancing authority maps to ISO {iso!r}")
    fleet_vintage = None if args.fleet_vintage < 0 else args.fleet_vintage

    adds = build_additions(bas)
    audit: dict = {}
    rets = build_retirements(bas, fleet_vintage=fleet_vintage, audit=audit)
    both = pd.concat([rets, adds], ignore_index=True)
    both["large_unit"] = both["mw"] >= LARGE_UNIT_MW
    both = both.sort_values(
        ["kind", "year", "fuel", "mw"], ascending=[True, True, True, False]
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"capacity_actuals_{iso.lower()}.csv"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    gap_fix_note = ""
    gap_fix_rows = load_retired_sheet_gap_fix(bas)
    if not gap_fix_rows.empty:
        plants = sorted(gap_fix_rows["plant_id"].unique().tolist())
        gap_fix_note = (
            f"# RD-5 actuals-coverage fix applied: plant(s) {plants} unioned in from "
            f"{RETIRED_SHEET_GAP_FIX} (missing from the current top-level retired "
            f"sheet) -- see that file's header and data/raw/eia-860/README.md.\n"
        )
    gate_note = ""
    if fleet_vintage is not None:
        gate_note = (
            f"# Retirements dated at PHYSICAL cessation (EIA-860 Status series "
            f"across releases {audit.get('releases', [])}, FFR-7A / D-21(b)), not at "
            f"the reported paper date; units already OS/RE at the {fleet_vintage} "
            f"fleet vintage are excluded ({len(audit.get('excluded', []))} here).\n"
        )
    header = (
        f"# capacity_actuals_{iso.lower()}.csv — capacity-hindcast scoring target "
        f"(W2-P5, plan §1.2.3)\n"
        f"# Source: latest committed EIA-860 (data/raw/eia-860/ operable + "
        f"retired_and_canceled sheets); registry outcome facts, not bench.\n"
        f"# Window 2021-2025 (rule 22: no 2026). Fuel in the model taxonomy "
        f"(data.fleet._map_fuel_type + renewable/storage). Built {stamp}.\n"
        f"# Units >= {LARGE_UNIT_MW:.0f} MW flagged (large_unit). "
        f"BA(s): {sorted(bas)}.\n"
        f"{gate_note}"
        f"{gap_fix_note}"
    )
    with open(out, "w") as fh:
        fh.write(header)
        both.to_csv(fh, index=False)

    r = rets["mw"].sum() / 1000.0 if not rets.empty else 0.0
    a = adds["mw"].sum() / 1000.0 if not adds.empty else 0.0
    print(
        f"{iso}: {len(rets)} retirements ({r:.1f} GW), {len(adds)} additions ({a:.1f} GW)"
    )
    print(f"  wrote {out}")
    for kind, df in (("retired", rets), ("added", adds)):
        if not df.empty:
            by_fuel = df.groupby("fuel")["mw"].sum().div(1000).round(2).to_dict()
            print(f"  {kind} GW by fuel: {by_fuel}")
    for row in audit.get("excluded", []):
        print(
            f"  vintage-gate excluded {row['unit_id']} {row['fuel']} "
            f"{row['mw']:.1f} MW ({row['year']}): {row['reason']} [{row['history']}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
