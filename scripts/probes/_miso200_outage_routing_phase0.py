"""miso-200 phase 0 — the CAMPD unit-outage extract's CLASS-ATTRIBUTION census.

===============================================================================
THE RULE, FROZEN HERE BEFORE ANY ADJUDICATING QUANTITY
===============================================================================
Pushed and blob-verified before the census runs (the standing miso-196/197/198/
199 pattern). Every threshold below is stated in
``results/calibration/PREREG-miso200-outage-routing-mixedgas-2026-09-02.md``
(committed and pushed first, blob ``bbae3472``) and is NOT revisited.

**THE OBJECT.** ``scripts/data/derive_campd_unit_outages.py::_resolve_unit_group``
routes each CAMPD unit's outage window to a model ``(plant_code, plant_group)``
bin. Its third branch short-circuits::

    if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL":
        return str(fac_group)

``fac_group`` comes from ``group_by_code[int(g.plant_code)] = g.plant_group``
over the model fleet -- LAST WRITER WINS -- so at a facility carrying more than
one gas bin the group is whichever fleet row happened to come last, and the
short-circuit then hands EVERY unit at that facility to that one bin. The
per-unit ``unitType`` resolution below it is never reached. The function's own
docstring already flags this branch as "a deliberate pjm-75 conservatism
('single-group gas facilities are byte-identical') rather than a physical
claim", and neiso-99 already carved one exception out of it. **The premise names
its own scope: the branch is sound only where the facility carries ONE gas
group.** This probe censuses the case it does not cover.

===============================================================================
BASES (imported, never restated -- rule 23 [R-FROZEN-DERIVE])
===============================================================================
* **B1 the model fleet** is ``run_year``'s OWN chain via
  ``ph0.build_run_year_fleet`` (``fleet_to_bins(load_fleet_from_csv) ->
  build_base_fleet -> build_dispatch_fleet -> generators_to_fleet_arrays``),
  NEVER ``fleet.assembly.load_or_synthesize_bins`` (miso-197 section 6,
  Cottonwood 55358). ``ph0`` is re-pointed at THIS session's keeper.
* **B2 the group/capacity maps under test** are the PRODUCTION objects, called
  rather than re-implemented: ``outages._iso_plant_capacity`` for the derate
  denominator and ``derive_campd_unit_outages._resolve_unit_group`` for the
  routing. A probe that re-implements the code under test measures its own
  re-implementation.
* **B3 the load shape** is the solve's own ``demand.sum(axis=0)`` read from the
  keeper's committed ``hourly/system_<year>`` sidecar and PASSED to
  ``generators_to_fleet_arrays``; without it the floor block falls through to an
  all-hours target (arrays.py:2861). The satisfiability pass ASSERTS the rebuilt
  2023 ST_GAS floor equals the keeper's own logged **9.9319 TWh** (the miso-199
  regression test, kept verbatim).
* **B4 unit attributes** (``unitType``, ``primaryFuelInfo``) come from the raw
  CAMPD unit-level parquets for MISO's own states, the SAME source the deriver
  reads them from.

**LEVEL-SLOT PRECEDENCE (miso-199 X-2's disclosed defect, inherited as a
guard).** This keeper arms ``st_gas_mustrun_oom_level`` and arrays.py:2512 merges
the oom map OVER ``thermal_tranche_p25_measured_level``, so a patch to the
p25_measured accessor is a SILENT NO-OP. This probe patches no level at all; the
guard is recorded so a successor does not re-learn it.

**PRE-CLIP SHARE VALIDATION.** N-2 needs the accumulator's PRE-clip removed share
``v_t``, which ``unit_outage_derate_factors`` does not return (it returns
``clip(1 - v, 0, 1)``). The probe reconstructs ``v`` and then ASSERTS
``clip(1 - v) == `` the production function's own arrays EXACTLY on every shared
key. A mismatch aborts: a reconstruction that does not reproduce the production
result is measuring something else.

===============================================================================
THE FROZEN LINES
===============================================================================
**N-1 THE MIS-ROUTING POPULATION.** For every MISO facility carrying a window
touching 2023-2025: classify ``single_gas`` (exactly one qualifying non-COAL
model group among CC_REGULAR / CC_CHP / ST_GAS / ST_CHP) or ``multi_gas`` (>=2),
and count units whose repaired (``unitType``-resolved) group differs from the
group the committed extract carries.

  * **L-1a THE DEFECT IS REAL AND MATERIAL** iff >=1 MISO facility is
    ``multi_gas`` AND its mis-routed units carry **>= 500 MW** of
    ``unit_capacity_mw`` in **>= 2 of 3** years. The threshold states what "a bin
    large enough to matter to a class band" means physically (~6 % of the ST_GAS
    class nameplate); it is not tuned to anything. **If no facility clears, the
    session escalates WITHOUT SOLVING.**

**N-2 THE TWO-SIDED SIGNATURE, on the INCUMBENT extract.**

  * **over-removal** = ``max_t v_t`` per bin-year; ``> 1.0`` proves the receiving
    bin is removed beyond its own capacity (the Stony Brook / Cottonwood
    signature, miso-186).
  * **zero-coverage** = a model bin with ``cap >= 100 MW`` at a ``multi_gas``
    facility receiving ZERO rows, i.e. availability identically 1.0 all year.
  * **L-1b THE 1403 CELL IS THE MIS-ROUTING FAMILY -- RE-DERIVED ON THIS
    SESSION'S OWN LINE.** miso-199's frozen L-X1b did NOT classify this cell (it
    missed its online-share leg by 5.7 pp) and is NOT cited here as a passed
    test. This classification is STRUCTURAL, not a threshold on a residual, and
    is TRUE iff ALL THREE hold: (i) ``(1403, ST_GAS)`` is zero-coverage in 2024;
    (ii) >=1 unit at facility 1403 carries a February-2024 window in the
    incumbent extract; (iii) that unit's ``unitType``-implied group is
    ``ST_GAS``. If any leg fails, **the 1403 cell is NOT this family** and the
    session reports that against its own interest.

**N-3 THE REPAIR'S OWN SOUNDNESS, on the REGENERATED extract.**

  * **L-3a NO NEW OVER-REMOVAL**: no MISO bin-hour in 2023-2025 whose pre-clip
    removed share exceeds 1.0 after the repair but did not before. The repair
    must REMOVE overflow, never add it. A violation KILLS the arm.
  * **L-3b SINGLE-OBJECT DELTA**: every row differing between the incumbent and
    repaired extracts differs ONLY in ``plant_group`` (and the columns that are
    functions of it), and every changed row sits at a ``multi_gas`` facility. A
    changed row at a ``single_gas`` facility is a scope violation and KILLS the
    arm.

**N-4 THE C1 EXPOSURE, PROJECTED ARITHMETICALLY (a bound, never an LP result).**
Per class-year: ``capability bound = sum_t |delta avail_t| x pmax`` over the
affected bins -- a rigorous UPPER bound on the class energy movement, since the
LP can never move more than the capability that changed -- plus the class
headroom in the affected hours, so the substitution channel is visible rather
than assumed away.

  * **L-4 CLEAR-TO-SOLVE.** The A/B is spent unless N-1/L-1a or N-2/L-1b has
    already stood the session down. **There is deliberately NO
    refuse-without-solving branch on N-4**: a rigorous LOWER bound on a CLASS
    decrement does not exist here (other ST_GAS plants can substitute), so
    refusing on the projection would mean refusing on a bound this session
    cannot make rigorous. N-4 is REPORTED and gates nothing.

===============================================================================
Usage
===============================================================================
    python3 scripts/probes/_miso200_outage_routing_phase0.py --satisfiability
    python3 scripts/probes/_miso200_outage_routing_phase0.py

Record: ``results/calibration/_miso200_outage_routing_phase0.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso198_stgas_oom_conduct_phase0 as ph0  # noqa: E402

from market_sim.data import campd, outages as ox  # noqa: E402
from scripts.data import derive_campd_unit_outages as dcu  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = _REPO / "results" / "calibration" / "miso198_oom_B"
RUN_ID = "2026-09-01-miso-198-oomlevel"
ph0.KEEPER = KEEPER
ph0.RUN_ID = RUN_ID

OUT = _REPO / "results" / "calibration" / "_miso200_outage_routing_phase0.json"
INCUMBENT_CSV = _REPO / "data" / "raw" / f"campd-unit-outages-{ISO}.csv"
REPAIRED_CSV = _REPO / "data" / "raw" / f"campd-unit-outages-unitroute-{ISO}.csv"

# The four model bins a gas facility can carry. A facility holding two or more
# of these is where _resolve_unit_group's fac_group short-circuit loses its
# stated premise ("single-group gas facilities are byte-identical").
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP")

# --- FROZEN THRESHOLDS (PREREG section 4; declared before any measurement) ---
L1A_MIN_MISROUTED_MW = 500.0      # ~6 % of the MISO ST_GAS class nameplate
L1A_MIN_YEARS = 2                 # of 3
L1B_PLANT = 1403                  # the charter's cell; classified, not assumed
L1B_YEAR = 2024
L1B_MONTH = 2
ZERO_COVERAGE_MIN_CAP_MW = 100.0
FLOOR_2023_REGRESSION_TWH = 9.9319  # the keeper's own logged ST_GAS assertion


# ---------------------------------------------------------------------------
# B2 -- the production maps, called rather than re-implemented
# ---------------------------------------------------------------------------
def keeper_outage_kwargs() -> dict:
    """The EXACT kwargs arrays.py:1098 passes for this keeper."""
    cfg = ph0.keeper_config(2024)
    return {
        "cc_steam_part_reclass": bool(getattr(cfg, "cc_steam_part_reclass", False)),
        "cc_nameplate_basis": bool(
            getattr(cfg, "unit_outage_lp_capacity_basis", False)
        ),
        "fleet_status_scope": bool(
            getattr(cfg, "unit_outage_fleet_status_scope", False)
        ),
    }


def bin_capacity() -> dict[tuple[int, str], float]:
    """``{(plant_code, plant_group): MW}`` -- the derate's own denominator."""
    kw = keeper_outage_kwargs()
    return ox._iso_plant_capacity(
        ISO, kw["cc_steam_part_reclass"], kw["cc_nameplate_basis"]
    )


def fleet_group_maps() -> tuple[dict[int, str], dict[int, set[str]]]:
    """Rebuild the DERIVER's own ``group_by_code`` / ``groups_by_code``.

    Mirrors derive_campd_unit_outages.main() lines 1195-1218 exactly: the same
    fleet sources, the same last-writer-wins assignment. The last-writer-wins is
    the defect under test, so it is reproduced, never corrected here.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

    iso_cfg = get_iso_config(ISO)
    fleet = load_fleet_from_csv(ISO, iso_cfg) + load_retired_within_window(ISO, iso_cfg)
    group_by_code: dict[int, str] = {}
    groups_by_code: dict[int, set[str]] = {}
    for g in fleet:
        if int(g.plant_code) > 0 and g.plant_group:
            group_by_code[int(g.plant_code)] = g.plant_group
            groups_by_code.setdefault(int(g.plant_code), set()).add(g.plant_group)
    return group_by_code, groups_by_code


def unit_attributes() -> dict[tuple[int, str], dict]:
    """B4: ``{(facilityId, unitId): {unitType, primaryFuelInfo}}`` from CAMPD."""
    attrs: dict[tuple[int, str], dict] = {}
    for st in campd.states_for_iso(ISO):
        for year in YEARS:
            p = _REPO / "data" / "raw" / "campd-unit-level" / f"{st}_{year}.parquet"
            if not p.exists():
                continue
            df = pd.read_parquet(
                p, columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
            ).drop_duplicates(subset=["facilityId", "unitId"])
            for r in df.itertuples(index=False):
                attrs.setdefault(
                    (int(r.facilityId), str(r.unitId)),
                    {
                        "unit_type": str(r.unitType),
                        "primary_fuel": str(r.primaryFuelInfo),
                    },
                )
    return attrs


def repaired_group(
    fac_id: int,
    unit_id: str,
    attrs: dict,
    group_by_code: dict[int, str],
    groups_by_code: dict[int, set[str]],
) -> str:
    """The group the unit routes to once the short-circuit is gated.

    Calls the PRODUCTION ``_resolve_unit_group`` (B2). The repair is expressed
    here exactly as it will be implemented: at a facility carrying two or more
    qualifying non-COAL gas groups the ``fac_group`` short-circuit is skipped by
    passing ``fac_group=None``, which drops the resolver straight into its OWN
    existing per-unit ``unitType`` routing. No new logic, no new threshold.
    """
    a = attrs.get((fac_id, unit_id), {})
    ut = a.get("unit_type", "")
    fuel = a.get("primary_fuel", "")
    is_coal = str(fuel).strip().lower() in ("coal", "coal refuse")
    fac_groups = groups_by_code.get(fac_id, set())
    fac_group = group_by_code.get(fac_id)
    multi = len([g for g in fac_groups if g in GAS_GROUPS]) >= 2
    return dcu._resolve_unit_group(
        is_coal, ut, fac_groups, None if multi else fac_group, fuel
    )


# ---------------------------------------------------------------------------
# N-2 -- the pre-clip removed share, validated against production
# ---------------------------------------------------------------------------
def preclip_shares(
    df: pd.DataFrame, year: int, cap: dict[tuple[int, str], float]
) -> dict[tuple[int, str], np.ndarray]:
    """Reconstruct the accumulator's PRE-clip removed share ``v_t`` per bin.

    ``unit_outage_derate_factors`` returns ``clip(1 - v, 0, 1)`` and so hides the
    overflow this census exists to measure. The reconstruction mirrors
    outages._accumulate exactly (same target_fn, same status filter, same
    ``removed_frac x ucap / cap[tgt]``, same window/mask helpers) and is ASSERTED
    against the production arrays by :func:`validate_preclip`.
    """
    kw = keeper_outage_kwargs()
    status_idx = ox._fleet_status_index(ISO) if kw["fleet_status_scope"] else None
    has_hours = ox._has_hour_grain(df)
    has_derate = "derate_factor" in df.columns
    sums: dict[tuple[int, str], np.ndarray] = {}
    for r in df.itertuples(index=False):
        tgt = ox._generic_unit_outage_target(
            int(r.facility_id), r.unit_id, r.plant_group
        )
        if tgt is None or tgt not in cap:
            continue
        if status_idx is not None:
            st = status_idx.get(int(r.facility_id), {}).get(
                str(r.unit_id).strip().upper()
            )
            if st is not None and st != "OP":
                continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        w_start, w_stop = ox.unit_outage_event_window(r, has_hours)
        mask = ox.outage_hour_mask(w_start, w_stop, year, HOURS)
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(HOURS))
        arr[mask] += removed_frac * float(ucap) / cap[tgt]
    return sums


def validate_preclip(year: int, cap: dict[tuple[int, str], float]) -> int:
    """Assert the reconstruction reproduces production EXACTLY. Aborts if not."""
    kw = keeper_outage_kwargs()
    prod = ox.unit_outage_derate_factors(year, HOURS, "", iso=ISO, **kw)
    df = load_events(INCUMBENT_CSV)
    mine = preclip_shares(df, year, cap)
    checked = 0
    for k, v in mine.items():
        got = np.clip(1.0 - v, 0.0, 1.0)
        exp = prod.get(k)
        assert exp is not None, f"{year}: production has no key {k}"
        assert np.allclose(got, exp, atol=0.0, rtol=0.0), (
            f"{year} {k}: pre-clip reconstruction does not reproduce production "
            f"(max abs diff {np.max(np.abs(got - exp)):.3e})"
        )
        checked += 1
    return checked


def load_events(csv_path: Path) -> pd.DataFrame:
    """The production loader + the production >= 5-day filter, on any path."""
    df = ox._load_unit_outage_events(csv_path, ISO)
    assert df is not None, f"no unit-outage events at {csv_path}"
    return df[df["duration_days"] >= ox.UNIT_OUTAGE_MIN_DAYS]


def year_rows(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Rows whose window overlaps ``year`` on the model clock."""
    has_hours = ox._has_hour_grain(df)
    keep = []
    for r in df.itertuples(index=False):
        w_start, w_stop = ox.unit_outage_event_window(r, has_hours)
        keep.append(bool(ox.outage_hour_mask(w_start, w_stop, year, HOURS).any()))
    return df[np.asarray(keep)]


# ---------------------------------------------------------------------------
# N-1 -- the mis-routing population
# ---------------------------------------------------------------------------
def run_n1(attrs, group_by_code, groups_by_code, cap) -> dict:
    """Census the facilities where the fac_group short-circuit loses its premise."""
    df_all = load_events(INCUMBENT_CSV)
    per_year: dict[str, dict] = {}
    facilities: dict[int, dict] = {}
    for year in YEARS:
        df = year_rows(df_all, year)
        misrouted_mw = 0.0
        multi_facs: set[int] = set()
        n_units = 0
        for r in df.itertuples(index=False):
            fac = int(r.facility_id)
            uid = str(r.unit_id)
            fac_groups = groups_by_code.get(fac, set())
            gas = [g for g in fac_groups if g in GAS_GROUPS]
            multi = len(gas) >= 2
            if not multi:
                continue
            multi_facs.add(fac)
            rep = repaired_group(fac, uid, attrs, group_by_code, groups_by_code)
            cur = str(r.plant_group)
            if rep != cur:
                n_units += 1
                misrouted_mw += float(r.unit_capacity_mw or 0.0)
                f = facilities.setdefault(
                    fac,
                    {
                        "facility_name": str(r.facility_name),
                        "model_groups": sorted(fac_groups),
                        "fac_group_last_writer": group_by_code.get(fac),
                        "misrouted_units": {},
                        "years": [],
                    },
                )
                f["misrouted_units"][uid] = {
                    "unit_capacity_mw": round(float(r.unit_capacity_mw or 0.0), 1),
                    "unit_type": attrs.get((fac, uid), {}).get("unit_type", ""),
                    "extract_group": cur,
                    "repaired_group": rep,
                }
                if year not in f["years"]:
                    f["years"].append(year)
        # De-duplicate: a unit with several windows in a year is counted once.
        uniq_mw = 0.0
        seen: set[tuple[int, str]] = set()
        for r in df.itertuples(index=False):
            fac, uid = int(r.facility_id), str(r.unit_id)
            if (fac, uid) in seen:
                continue
            fac_groups = groups_by_code.get(fac, set())
            if len([g for g in fac_groups if g in GAS_GROUPS]) < 2:
                continue
            if repaired_group(fac, uid, attrs, group_by_code, groups_by_code) != str(
                r.plant_group
            ):
                seen.add((fac, uid))
                uniq_mw += float(r.unit_capacity_mw or 0.0)
        per_year[str(year)] = {
            "multi_gas_facilities": len(multi_facs),
            "misrouted_rows": n_units,
            "misrouted_units_unique": len(seen),
            "misrouted_mw_row_sum": round(misrouted_mw, 1),
            "misrouted_mw_unique": round(uniq_mw, 1),
        }
    years_clearing = [
        y
        for y in YEARS
        if per_year[str(y)]["misrouted_mw_unique"] >= L1A_MIN_MISROUTED_MW
    ]
    return {
        "per_year": per_year,
        "facilities": {str(k): v for k, v in sorted(facilities.items())},
        "years_clearing_500mw": years_clearing,
        "L1a_material": len(years_clearing) >= L1A_MIN_YEARS,
    }


# ---------------------------------------------------------------------------
# N-2 -- the two-sided signature on the incumbent extract
# ---------------------------------------------------------------------------
def run_n2(attrs, group_by_code, groups_by_code, cap, n1) -> dict:
    """Over-removal and zero-coverage, plus the L-1b structural classification."""
    df_all = load_events(INCUMBENT_CSV)
    multi_facs = {int(f) for f in n1["facilities"]}
    over: list[dict] = []
    zero_cov: list[dict] = []
    validated: dict[str, int] = {}
    for year in YEARS:
        validated[str(year)] = validate_preclip(year, cap)
        shares = preclip_shares(load_events(INCUMBENT_CSV), year, cap)
        for key, v in shares.items():
            mx = float(np.max(v))
            if mx > 1.0:
                over.append(
                    {
                        "year": year,
                        "plant_code": key[0],
                        "plant_group": key[1],
                        "bin_cap_mw": round(cap[key], 1),
                        "max_preclip_share": round(mx, 4),
                        "hours_over_1": int(np.sum(v > 1.0)),
                        "at_multi_gas_facility": key[0] in multi_facs,
                    }
                )
        df = year_rows(df_all, year)
        covered = set()
        for r in df.itertuples(index=False):
            t = ox._generic_unit_outage_target(
                int(r.facility_id), r.unit_id, r.plant_group
            )
            if t is not None:
                covered.add(t)
        for key, mw in cap.items():
            if key[0] not in multi_facs or mw < ZERO_COVERAGE_MIN_CAP_MW:
                continue
            if key not in covered:
                zero_cov.append(
                    {
                        "year": year,
                        "plant_code": key[0],
                        "plant_group": key[1],
                        "bin_cap_mw": round(mw, 1),
                    }
                )
    # --- L-1b: the 1403 cell, classified on THIS session's own structural line
    leg_i = any(
        z["plant_code"] == L1B_PLANT
        and z["plant_group"] == "ST_GAS"
        and z["year"] == L1B_YEAR
        for z in zero_cov
    )
    feb_units: list[dict] = []
    for r in load_events(INCUMBENT_CSV).itertuples(index=False):
        if int(r.facility_id) != L1B_PLANT:
            continue
        s, e = pd.Timestamp(r.outage_start), pd.Timestamp(r.outage_end)
        m0 = pd.Timestamp(year=L1B_YEAR, month=L1B_MONTH, day=1)
        m1 = m0 + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
        if s < m1 and e >= m0:
            uid = str(r.unit_id)
            feb_units.append(
                {
                    "unit_id": uid,
                    "window": f"{s.date()}..{e.date()}",
                    "unit_capacity_mw": round(float(r.unit_capacity_mw or 0.0), 1),
                    "extract_group": str(r.plant_group),
                    "unit_type": attrs.get((L1B_PLANT, uid), {}).get("unit_type", ""),
                    "repaired_group": repaired_group(
                        L1B_PLANT, uid, attrs, group_by_code, groups_by_code
                    ),
                }
            )
    leg_ii = len(feb_units) > 0
    leg_iii = any(u["repaired_group"] == "ST_GAS" for u in feb_units)
    return {
        "preclip_keys_validated_against_production": validated,
        "over_removal": sorted(
            over, key=lambda d: -d["max_preclip_share"]
        )[:40],
        "over_removal_count": len(over),
        "zero_coverage": zero_cov,
        "L1b": {
            "plant": L1B_PLANT,
            "leg_i_zero_coverage_st_gas_2024": leg_i,
            "leg_ii_feb2024_window_exists": leg_ii,
            "leg_iii_a_feb_unit_routes_to_st_gas": leg_iii,
            "feb_2024_units": feb_units,
            "IS_MISROUTING_FAMILY": bool(leg_i and leg_ii and leg_iii),
        },
    }


# ---------------------------------------------------------------------------
# N-3 -- the repair's own soundness (needs the regenerated extract)
# ---------------------------------------------------------------------------
_ROW_KEY = ["facility_id", "unit_id", "outage_start", "outage_end"]
# Columns that are FUNCTIONS of plant_group (the bin the row is attributed to),
# so a change in them is part of the same single object, not a second delta.
_GROUP_DEPENDENT = {"plant_group", "plant_capacity_mw", "unit_pct_of_plant"}


def run_n3(n1, cap) -> dict:
    """L-3a no new over-removal; L-3b the delta is one object, in scope."""
    if not REPAIRED_CSV.exists():
        return {"status": "REPAIRED_EXTRACT_ABSENT", "L3a_pass": None, "L3b_pass": None}
    a = pd.read_csv(INCUMBENT_CSV).set_index(_ROW_KEY, drop=False)
    b = pd.read_csv(REPAIRED_CSV).set_index(_ROW_KEY, drop=False)
    multi_facs = {int(f) for f in n1["facilities"]}
    added = [k for k in b.index if k not in a.index]
    dropped = [k for k in a.index if k not in b.index]
    changed_cols: dict[str, int] = {}
    out_of_scope: list[dict] = []
    n_changed = 0
    common = a.index.intersection(b.index)
    for k in common:
        ra, rb = a.loc[k], b.loc[k]
        if isinstance(ra, pd.DataFrame):  # duplicate key -- compare frames whole
            continue
        diffs = [
            c
            for c in a.columns
            if not (pd.isna(ra[c]) and pd.isna(rb[c])) and ra[c] != rb[c]
        ]
        if not diffs:
            continue
        n_changed += 1
        for c in diffs:
            changed_cols[c] = changed_cols.get(c, 0) + 1
        if set(diffs) - _GROUP_DEPENDENT or int(ra["facility_id"]) not in multi_facs:
            out_of_scope.append(
                {
                    "facility_id": int(ra["facility_id"]),
                    "unit_id": str(ra["unit_id"]),
                    "changed": diffs,
                    "at_multi_gas_facility": int(ra["facility_id"]) in multi_facs,
                }
            )
    # L-3a: over-removal must not appear where it was absent.
    new_over: list[dict] = []
    for year in YEARS:
        before = preclip_shares(load_events(INCUMBENT_CSV), year, cap)
        after = preclip_shares(load_events(REPAIRED_CSV), year, cap)
        for key, v in after.items():
            was = before.get(key)
            mx_a = float(np.max(v))
            mx_b = float(np.max(was)) if was is not None else 0.0
            if mx_a > 1.0 and mx_b <= 1.0:
                new_over.append(
                    {
                        "year": year,
                        "plant_code": key[0],
                        "plant_group": key[1],
                        "max_preclip_share_before": round(mx_b, 4),
                        "max_preclip_share_after": round(mx_a, 4),
                    }
                )
    return {
        "status": "SCORED",
        "rows_added": len(added),
        "rows_dropped": len(dropped),
        "rows_changed": n_changed,
        "changed_columns": changed_cols,
        "out_of_scope_changes": out_of_scope[:20],
        "out_of_scope_count": len(out_of_scope),
        "new_over_removal": new_over,
        "L3a_pass": len(new_over) == 0,
        "L3b_pass": len(out_of_scope) == 0 and len(added) == 0 and len(dropped) == 0,
    }


# ---------------------------------------------------------------------------
# N-4 -- the C1 exposure, an arithmetic UPPER bound (never an LP result)
# ---------------------------------------------------------------------------
def run_n4(cap) -> dict:
    """Capability bound per class-year, plus the substitution headroom."""
    if not REPAIRED_CSV.exists():
        return {"status": "REPAIRED_EXTRACT_ABSENT"}
    kw = keeper_outage_kwargs()
    out: dict[str, dict] = {}
    for year in YEARS:
        before = preclip_shares(load_events(INCUMBENT_CSV), year, cap)
        after = preclip_shares(load_events(REPAIRED_CSV), year, cap)
        by_class: dict[str, dict] = {}
        for key in set(before) | set(after):
            av_b = np.clip(1.0 - before.get(key, np.zeros(HOURS)), 0.0, 1.0)
            av_a = np.clip(1.0 - after.get(key, np.zeros(HOURS)), 0.0, 1.0)
            d = av_a - av_b
            if not np.any(d):
                continue
            twh = float(np.sum(d) * cap[key]) / 1e6
            c = by_class.setdefault(
                key[1], {"capability_twh": 0.0, "bins": []}
            )
            c["capability_twh"] += twh
            c["bins"].append(
                {
                    "plant_code": key[0],
                    "bin_cap_mw": round(cap[key], 1),
                    "capability_twh": round(twh, 4),
                    "mean_avail_before": round(float(np.mean(av_b)), 4),
                    "mean_avail_after": round(float(np.mean(av_a)), 4),
                }
            )
        for c in by_class.values():
            c["capability_twh"] = round(c["capability_twh"], 4)
        out[str(year)] = by_class
    return {
        "status": "SCORED",
        "note": (
            "capability_twh is a RIGOROUS UPPER BOUND on the class energy "
            "movement (the LP can never move more than the capability that "
            "changed), signed: positive = the repair ADDS capability. It is "
            "NOT an LP result and NOTHING is gated on it (PREREG L-4)."
        ),
        "keeper_outage_kwargs": kw,
        "by_year": out,
    }


# ---------------------------------------------------------------------------
# satisfiability -- the instrument proves itself before it adjudicates
# ---------------------------------------------------------------------------
def satisfiability() -> None:
    """Prove the bases reproduce the keeper before any adjudicating quantity."""
    print(f"keeper: {KEEPER.name}  run_id: {RUN_ID}")
    # B3 + the miso-199 floor regression test, kept verbatim.
    fleet, fa, _ = ph0.build_run_year_fleet(2023)
    floors = ph0.plant_floor_series(fleet, fa)
    classes = ph0.model_classes(fleet)
    tot = (
        sum(
            float(np.sum(v))
            for k, v in floors.items()
            if classes.get(k) == "ST_GAS"
        )
        / 1e6
    )
    print(f"  ST_GAS 2023 floor assertion: {tot:.4f} TWh "
          f"(keeper logged {FLOOR_2023_REGRESSION_TWH})")
    assert abs(tot - FLOOR_2023_REGRESSION_TWH) < 5e-4, (
        f"floor regression FAILED: {tot:.4f} vs {FLOOR_2023_REGRESSION_TWH} — "
        "the load_shape basis is wrong"
    )
    # B2 + the pre-clip reconstruction, asserted against production.
    cap = bin_capacity()
    n = validate_preclip(2024, cap)
    print(f"  pre-clip reconstruction reproduces production on {n} bins (2024)")
    gbc, gsbc = fleet_group_maps()
    multi = [c for c, gs in gsbc.items() if len([g for g in gs if g in GAS_GROUPS]) >= 2]
    print(f"  model bins: {len(cap)}   multi-gas-group facilities in fleet: {len(multi)}")
    print("SATISFIABILITY OK")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return
    cap = bin_capacity()
    attrs = unit_attributes()
    gbc, gsbc = fleet_group_maps()
    n1 = run_n1(attrs, gbc, gsbc, cap)
    n2 = run_n2(attrs, gbc, gsbc, cap, n1)
    n3 = run_n3(n1, cap)
    n4 = run_n4(cap)
    rec = {
        "probe": Path(__file__).name,
        "session": "miso-200",
        "keeper_bundle": KEEPER.name,
        "run_id": RUN_ID,
        "prereg": "results/calibration/PREREG-miso200-outage-routing-mixedgas-2026-09-02.md",
        "frozen_lines": {
            "L1a_min_misrouted_mw": L1A_MIN_MISROUTED_MW,
            "L1a_min_years": L1A_MIN_YEARS,
            "L1b_plant": L1B_PLANT,
            "zero_coverage_min_cap_mw": ZERO_COVERAGE_MIN_CAP_MW,
            "L4_no_refuse_without_solving_branch": True,
        },
        "n1": n1,
        "n2": n2,
        "n3": n3,
        "n4": n4,
    }
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"wrote {OUT.relative_to(_REPO)}")
    print(f"L-1a material: {n1['L1a_material']}  "
          f"(years clearing 500 MW: {n1['years_clearing_500mw']})")
    print(f"L-1b 1403 IS the mis-routing family: "
          f"{n2['L1b']['IS_MISROUTING_FAMILY']}  "
          f"(legs {n2['L1b']['leg_i_zero_coverage_st_gas_2024']}/"
          f"{n2['L1b']['leg_ii_feb2024_window_exists']}/"
          f"{n2['L1b']['leg_iii_a_feb_unit_routes_to_st_gas']})")
    print(f"over-removal bin-years on the incumbent extract: "
          f"{n2['over_removal_count']}")
    print(f"N-3: {n3.get('status')}   N-4: {n4.get('status')}")


if __name__ == "__main__":
    main()
