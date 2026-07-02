"""Derive *unit-level* outage windows from EPA CAMPD hourly gross generation.

The facility-level detector (``scripts/derive_campd_outages.py``) sums every
unit at a plant into one CEMS series, so a single-unit outage at a multi-unit
plant — and, critically, a *coal*-unit outage at a mixed coal/gas facility
(W A Parish, Barney M Davis) — is masked by the units that keep running and is
never detected. This script reads the per-unit CAMPD extracts in
``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` (one row per
``unit``-hour, carrying ``unitId``) and detects an outage for each *unit*
independently, on the unit's own gross output.

For every sustained unit outage (>= ``--min-outage-days``) it writes one row to
``data/raw/campd-unit-outages.csv`` in the schema the unit-level derate
overlay (:func:`market_sim.data.outages.unit_outage_derate_factors`) consumes:
each row removes the unit's capacity share of its model bin from availability
over the outage window. The unit's capacity is the EIA-860 generator nameplate
(matched on plant code + normalised unit id), falling back to the unit's
observed CAMPD peak gross when no EIA-860 generator matches.

The detector is chosen by the *unit's own fuel*, because what a per-unit output
gap means depends on how the unit is run:

* **Coal** units are baseload — they run continuously when available, so a
  sustained CF below :data:`~scripts.derive_campd_outages.REAL_RUN_CF` genuinely
  marks an outage. They use the averaged real-run rule (same as the facility
  detector for coal). This is the layer's core job: catch coal-unit outages the
  facility detector hides behind a mixed facility's running gas units (W A
  Parish 5-8) or behind other coal units at a multi-unit plant.
* **Everything else** (combined cycle, gas-steam) is load-following: an idle
  hour is usually economics, not a forced outage, so the averaged rule would
  badly over-flag a merchant CC turbine that simply isn't dispatched. These use
  the **event-based** rule — a window is broken by *any* single hour above
  :data:`~scripts.derive_campd_outages.ST_GAS_CF_PEAK` — so a unit is flagged
  only when it produced essentially nothing for the whole span (a genuine dead
  period), while an economically-idle-but-occasionally-firing unit is left to
  the economic dispatch and the facility-level overlay.

Detection is per calendar year, matching the facility detector; a window
straddling Dec 31 is clipped at the year boundary and each side must
independently clear the duration floor.

Combustion-turbine peakers carry no outage overlay (they dispatch
economically), so plants whose model bin is ``CT_PEAKER`` — and the
``ST_GAS`` peaker plants in
:data:`market_sim.data.outages.ST_GAS_PEAKER_PLANTS` — are skipped, matching the
overlay's convention.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    CAMPD_BINS_CSV,
    EIA_860_DIR,
    PROCESSED_DIR,
    RAW_DATA_DIR,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
)
from scripts.derive_campd_outages import (  # noqa: E402
    FULL_STOP_OVERRIDE_CF,
    FULL_STOP_OVERRIDE_DAYS,
    HIGH_LOAD_PCTL,
    MIN_INMERIT_HOURS,
    ST_GAS_CF_PEAK,
    WINDOW_DAYS,
    detect_outages,
    detect_outages_eventbased,
    filter_revealed_outages,
    high_load_mask,
)

# CAMPD unit-level extracts live in their own subdirectory; the flat raw-data
# files are facility-summed and carry no unitId.
UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"

# The revealed-availability (high-load) filter and its constants
# (HIGH_LOAD_PCTL, MIN_INMERIT_HOURS, high_load_mask) are shared with the
# facility-level detector — imported above from scripts.derive_campd_outages.


def _norm_unit_id(uid: object) -> str:
    """Return an upper-cased alphanumeric-only unit id (drop spaces/dashes)."""
    return re.sub(r"[^0-9A-Za-z]", "", str(uid)).upper()


# EIA-860 prime movers for the combined-cycle steam coupling. A combined
# cycle's combustion turbines (``CT``) exhaust into a heat-recovery boiler that
# drives a separate steam turbine, reported as its own ``CA`` generator. The
# steam turbine burns no fuel, so it has no CAMPD CEMS series and can never be
# detected as an outage on its own — yet when a feeding CT goes down it loses
# that CT's share of steam. Single-shaft combined cycles (``CS``) put the CT and
# its steam turbine on one shaft under a single generator id whose nameplate
# already includes the steam, so they carry no orphaned ``CA`` and must NOT be
# augmented (that would double-count their steam).
_CC_COMBUSTION_PM: str = "CT"
_CC_STEAM_PM: str = "CA"


# A capacity-index entry: ``(detect_mw, derate_mw, cc_augmented)``. ``detect_mw``
# is the unit's own physical nameplate — the CF denominator the outage detector
# thresholds on, so detection is unchanged by the steam coupling. ``derate_mw``
# is the unit's block share written to the CSV (steam-augmented for CC CTs), the
# numerator the availability derate divides into the model bin. They differ only
# for a combined-cycle combustion turbine, where ``derate_mw`` folds in steam.
CapEntry = tuple[float, float, bool]


def build_capacity_index(
    eia860_path: Path,
) -> tuple[
    dict[tuple[int, str], CapEntry],
    dict[tuple[int, str], list[CapEntry]],
]:
    """Return ``(exact, by_digits)`` EIA-860 capacity lookups.

    CAMPD unit ids and EIA-860 generator ids label the same units differently
    (CAMPD ``WAP5`` vs EIA ``5``; CAMPD ``1`` vs EIA ``OG1``), so two lookups
    are built keyed by EIA plant code, each mapping to a :data:`CapEntry`
    ``(detect_mw, derate_mw, cc_augmented)``:

    * ``exact``: ``(plant, NORMALISED_ID) -> CapEntry`` — a direct hit when the
      ids already agree once punctuation/case are normalised.
    * ``by_digits``: ``(plant, DIGITS) -> [CapEntry, ...]`` — matched only when
      a single generator at the plant carries those trailing digits, so
      ``WAP5``/``5`` and ``1``/``OG1`` join without colliding.

    **Combined-cycle steam coupling.** ``detect_mw`` is always the EIA-860
    nameplate (the CF basis for the detector — detection is *not* changed by
    this fix). ``derate_mw`` equals the nameplate too, except a combined-cycle
    combustion turbine (``prime_mover == CT``) at a plant that also carries
    combined-cycle steam (``prime_mover == CA``) is *augmented* by its pro-rata
    share of that steam:

        derate_mw = CT_nameplate * (1 + Σ CA_nameplate / Σ CT_nameplate)

    so the plant's CT shares sum back to the full block (CT + steam) — the same
    basis as the model bin denominator the derate divides into — and one CT out
    derates its turbine *plus* the steam it fed, not the CT alone. The steam
    sums are taken per plant over ``CT``/``CA`` prime movers, so the allocation
    never crosses a split facility (W A Parish's coal/gas ``ST`` units and
    Barney M Davis's gas-steam ``ST`` unit are not ``CT``/``CA`` and neither
    receive nor donate steam) and single-shaft (``CS``) blocks — which carry no
    separate ``CA`` — are left at their steam-inclusive nameplate. The boolean
    flags the augmented entries so :func:`unit_capacity_mw` can label them.
    """
    gens = pd.read_parquet(
        eia860_path,
        columns=["plant_id", "generator_id", "nameplate_capacity_mw", "prime_mover"],
    ).dropna(subset=["generator_id"])
    gens = gens.copy()
    gens["nameplate_capacity_mw"] = pd.to_numeric(
        gens["nameplate_capacity_mw"], errors="coerce"
    )
    gens = gens[gens["nameplate_capacity_mw"] > 0.0]
    # Per-plant combined-cycle steam-allocation factor (1 + ΣCA/ΣCT), built only
    # where the plant carries both a combustion turbine and a distinct steam
    # turbine; absent (factor 1.0) for pure-CT, single-shaft (CS) and non-CC
    # plants.
    ct_sum = (
        gens[gens["prime_mover"] == _CC_COMBUSTION_PM]
        .groupby("plant_id")["nameplate_capacity_mw"]
        .sum()
    )
    ca_sum = (
        gens[gens["prime_mover"] == _CC_STEAM_PM]
        .groupby("plant_id")["nameplate_capacity_mw"]
        .sum()
    )
    steam_factor: dict[int, float] = {}
    for plant_id, cts in ct_sum.items():
        cas = float(ca_sum.get(plant_id, 0.0))
        if float(cts) > 0.0 and cas > 0.0:
            steam_factor[int(plant_id)] = 1.0 + cas / float(cts)

    exact: dict[tuple[int, str], CapEntry] = {}
    by_digits: dict[tuple[int, str], list[CapEntry]] = {}
    for plant_id, gen_id, cap, pm in gens[
        ["plant_id", "generator_id", "nameplate_capacity_mw", "prime_mover"]
    ].itertuples(index=False):
        pid = int(plant_id)
        nameplate = float(cap)
        factor = steam_factor.get(pid, 1.0) if str(pm) == _CC_COMBUSTION_PM else 1.0
        augmented = factor > 1.0
        value: CapEntry = (nameplate, nameplate * factor, augmented)
        full = _norm_unit_id(gen_id)
        exact[(pid, full)] = value
        digits = re.sub(r"\D", "", full)
        if digits:
            by_digits.setdefault((pid, digits), []).append(value)
    return exact, by_digits


def plant_nameplate_index(eia860_path: Path) -> dict[int, float]:
    """Return ``plant_id -> total generator nameplate MW`` from EIA-860."""
    gens = pd.read_parquet(
        eia860_path, columns=["plant_id", "nameplate_capacity_mw"]
    ).dropna()
    out: dict[int, float] = {}
    for plant_id, cap in gens.itertuples(index=False):
        if float(cap) > 0.0:
            out[int(plant_id)] = out.get(int(plant_id), 0.0) + float(cap)
    return out


def unit_capacity_mw(
    plant_id: int,
    unit_id: object,
    exact: dict[tuple[int, str], CapEntry],
    by_digits: dict[tuple[int, str], list[CapEntry]],
    observed_peak: float,
) -> tuple[float, float, str]:
    """Return ``(detect_mw, derate_mw, source)`` for a CAMPD unit.

    Prefers the EIA-860 capacity (exact id match, then a unique trailing-digit
    match); falls back to the unit's observed CAMPD peak gross when no generator
    matches. ``detect_mw`` is the unit's own nameplate — the CF denominator the
    outage detector thresholds on (unchanged by the steam fix) — and
    ``derate_mw`` is the block share written to the CSV. They differ only for a
    combined-cycle combustion turbine, whose ``derate_mw`` folds in its allocated
    steam (see :func:`build_capacity_index`); those rows are labelled
    ``eia_exact_cc`` / ``eia_digits_cc`` so the steam-coupled derates are
    auditable. The observed-peak fallback already folds the CT's steam into its
    CAMPD gross, so its detect and derate capacities are the same.
    """
    full = _norm_unit_id(unit_id)
    if (plant_id, full) in exact:
        detect, derate, augmented = exact[(plant_id, full)]
        return detect, derate, "eia_exact_cc" if augmented else "eia_exact"
    digits = re.sub(r"\D", "", full)
    if digits:
        hits = by_digits.get((plant_id, digits))
        if hits and len(hits) == 1:
            detect, derate, augmented = hits[0]
            return detect, derate, "eia_digits_cc" if augmented else "eia_digits"
    return observed_peak, observed_peak, "observed_peak"


def _unit_year_grid(sub: pd.DataFrame, year: int, col: str = "grossLoad") -> np.ndarray:
    """Return one unit-year's hourly gross on the full calendar-year clock.

    CAMPD omits non-operating hours, so the unit's reported hours are placed on
    a gap-free hourly index spanning the whole year and missing hours are
    zero-filled (missing = no activity = offline), matching the facility
    detector. Returns the gross-MW array (length = hours in the year).
    """
    ts = sub["date"] + pd.to_timedelta(sub["hour"], unit="h")
    series = pd.Series(sub[col].to_numpy(dtype=float), index=ts)
    series = series.groupby(level=0).sum().sort_index()
    full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    return series.reindex(full).fillna(0.0).to_numpy(dtype=float)


def _load_unit_year(state: str, year: int) -> pd.DataFrame:
    """Load one unit-level state-year extract, or empty when absent."""
    path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
    if not path.exists():
        print(f"  (no unit-level extract for {state} {year}: {path.name})")
        return pd.DataFrame()
    df = pd.read_parquet(
        path,
        columns=[
            "facilityId",
            "facilityName",
            "unitId",
            "date",
            "hour",
            "grossLoad",
            "opTime",
            "primaryFuelInfo",
        ],
    )
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df["facilityId"] = df["facilityId"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce")
    df["opTime"] = pd.to_numeric(df["opTime"], errors="coerce")
    return df.dropna(subset=["hour"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--min-outage-days", type=float, default=5.0)
    ap.add_argument(
        "--no-inmerit-filter",
        action="store_true",
        help="Disable the revealed-availability filter (keep every detected "
        "down span as an outage, the pre-fix behaviour).",
    )
    ap.add_argument(
        "--high-load-pctl",
        type=float,
        default=HIGH_LOAD_PCTL,
        help=f"System-load percentile above which an hour is 'high load' (a "
        f"down unit was needed) (default {HIGH_LOAD_PCTL}).",
    )
    ap.add_argument(
        "--min-inmerit-hours",
        type=int,
        default=MIN_INMERIT_HOURS,
        help=f"High-load hours a span must overlap to count as a real outage "
        f"(default {MIN_INMERIT_HOURS}).",
    )
    ap.add_argument(
        "--high-load-window-days",
        type=int,
        default=WINDOW_DAYS,
        help=f"Centered window (days) the high-load percentile is measured over "
        f"— the LOCAL/seasonal band that keeps real shoulder outages. 0 = legacy "
        f"single-annual percentile (default {WINDOW_DAYS}).",
    )
    ap.add_argument(
        "--fullstop-override-days",
        type=int,
        default=FULL_STOP_OVERRIDE_DAYS,
        help=f"A sustained full-stop (CF<override-cf) lasting >= this many days is "
        f"kept as a mechanical outage regardless of net-load overlap "
        f"(default {FULL_STOP_OVERRIDE_DAYS}).",
    )
    ap.add_argument(
        "--fullstop-override-cf",
        type=float,
        default=FULL_STOP_OVERRIDE_CF,
        help=f"Span mean-CF below which the full-stop override treats a long down "
        f"span as a mechanical outage (default {FULL_STOP_OVERRIDE_CF}).",
    )
    ap.add_argument(
        "--no-fullstop-override",
        action="store_true",
        help="Disable the full-stop duration override (keep only the net-load "
        "revealed-availability test).",
    )
    ap.add_argument(
        "--bins",
        default=str(CAMPD_BINS_CSV),
        help="Per-plant bin CSV; supplies each facility's model plant group.",
    )
    ap.add_argument(
        "--eia860",
        default=str(EIA_860_DIR / "eia860_generators.parquet"),
        help="EIA-860 generator parquet, for per-unit nameplate capacity.",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output CSV; defaults to data/raw/campd-unit-outages.csv "
        "(ERCOT) or campd-unit-outages-{ISO}.csv.",
    )
    args = ap.parse_args()
    if args.no_fullstop_override:
        args.fullstop_override_days = 10**9
    min_outage_hours = int(round(args.min_outage_days * 24))
    iso = args.iso.upper()
    if args.out is None:
        fname = (
            "campd-unit-outages.csv"
            if iso == "ERCOT"
            else f"campd-unit-outages-{iso}.csv"
        )
        args.out = str(RAW_DATA_DIR / fname)

    # Each facility's model plant group (the LP bin the derate routes into).
    # Split facilities (W A Parish 3470, Barney M Davis 4939) carry their
    # primary group here; the overlay's _unit_outage_target re-routes their
    # gas-steam units to the split code by unit id, so the group passed for
    # them is immaterial.
    #
    # ERCOT sources the plant->group map from the CAMPD bin sheet
    # (custom-bin-assignments.csv); other ISOs have no bin sheet and run a
    # per-plant EIA-860 fleet, so their group map comes from the fleet's
    # plant_group (the same source _fleet_group_by_code / the benchmark backfill
    # use). Without this every non-ERCOT facility missed the bin sheet, fell
    # through QUALIFYING_PLANT_GROUPS, and produced zero unit-outage windows.
    name_by_code: dict[int, str] = {}
    # ALL model plant groups at a plant code (a mixed coal/CC facility like
    # Chesterfield 3797 carries several) — the per-unit group resolver below
    # routes each CAMPD unit's outage to the bin matching the UNIT's own
    # class, not whichever group the last fleet row happened to carry.
    groups_by_code: dict[int, set[str]] = {}

    def _resolve_unit_group(
        is_coal: bool,
        unit_type: str,
        fac_groups: set[str],
        fac_group: str | None,
    ) -> str:
        """Route a CAMPD unit's outage row to the model bin matching the UNIT.

        ``group_by_code`` keeps ONE group per plant code, so at a mixed
        facility every unit's window landed on that single bin — Chesterfield
        (3797): 1,036 MW of coal units 5/6, out Apr-Dec 2023 for their
        retirement, were tagged CC_REGULAR and blocked the surviving 386 MW
        gas-CC plant for most of 2023 (the pjm-75 2023 CC under-run
        root-cause finding, ~2.35 TWh). Resolution: a solid-fuel unit is
        always COAL; a non-coal unit at a facility whose primary group is
        COAL (or non-qualifying) is routed by its CAMPD ``unitType`` to the
        facility's matching gas bin; otherwise the facility group stands
        (single-group gas facilities are byte-identical). A row routed to a
        ``(plant_code, group)`` bin absent from the model fleet is skipped by
        the overlay (outages.unit_outage_derate_factors) — correct: a retired
        coal unit's window must not derate the surviving gas plant.
        """
        if is_coal:
            return "COAL"
        if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL":
            return str(fac_group)
        ut = str(unit_type).strip().lower()
        if "combined cycle" in ut:
            for g in ("CC_REGULAR", "CC_CHP"):
                if g in fac_groups:
                    return g
            return "CC_REGULAR"
        if "combustion turbine" in ut:
            if "CT_CHP" in fac_groups:
                return "CT_CHP"
            return "CT_PEAKER"  # excluded downstream: peakers carry no overlay
        for g in ("ST_GAS", "ST_CHP"):
            if g in fac_groups:
                return g
        return str(fac_group or "")

    if iso == "ERCOT":
        bins = pd.read_csv(args.bins)
        group_by_code = {
            int(c): str(g) for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])
        }
    else:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import (
            load_fleet_from_csv,
            load_retired_within_window,
        )

        iso_config = get_iso_config(iso)
        group_by_code = {}
        # Within-window plant exits dispatch in the backcast fleet too, so they
        # need their observed CEMS outage windows derived — else an injected
        # retiree (e.g. Mystic) runs uncapped at its full economic merit.
        fleet = load_fleet_from_csv(iso, iso_config) + load_retired_within_window(
            iso, iso_config
        )
        for g in fleet:
            if int(g.plant_code) > 0 and g.plant_group:
                group_by_code[int(g.plant_code)] = g.plant_group
                name_by_code[int(g.plant_code)] = g.name
                groups_by_code.setdefault(int(g.plant_code), set()).add(g.plant_group)
    # Facility names for units re-keyed by the CEMS->EIA split-plant remap
    # (their CAMPD facilityName is the legacy plant's).
    remap_names = {
        c: name_by_code[c]
        for c in set(campd.CAMPD_UNIT_PLANT_REMAP.values())
        if c in name_by_code
    }

    exact, by_digits = build_capacity_index(Path(args.eia860))
    npl_by_plant = plant_nameplate_index(Path(args.eia860))

    states = campd.states_for_iso(iso)
    rows: list[dict] = []
    summary: list[tuple] = []
    # year -> in-merit (system-tight) hour mask, built once per year.
    inmerit_cache: dict[int, np.ndarray | None] = {}
    # (facility, year) -> any non-null CAMPD grossLoad seen; feeds the
    # net-zero-to-grid rule below (mirrors the benchmark's CAMPD backfill).
    campd_gross_seen: set[tuple[int, int]] = set()
    for state in states:
        for year in args.years:
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            for fac_id, has in (
                df.groupby("facilityId", observed=True)["grossLoad"]
                .apply(lambda s: s.notna().any())
                .items()
            ):
                if has:
                    campd_gross_seen.add((int(fac_id), year))
            # CEMS->EIA split-plant remap (campd.CAMPD_UNIT_PLANT_REMAP):
            # re-key units that report under a legacy ORIS to the EIA plant
            # the model fleet carries (AES Alamitos / Huntington Beach CCGTs),
            # BEFORE the group lookup and the peaker-exclusion check, so the
            # new CC plants get their own windows and the legacy steamers'
            # exclusion does not swallow them.
            df["facilityId"] = [
                campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                for f, u in zip(df["facilityId"].astype(int), df["unitId"].astype(str))
            ]
            for fac_id, fac in df.groupby("facilityId", observed=True):
                group = group_by_code.get(int(fac_id))
                fac_groups = groups_by_code.get(
                    int(fac_id), {group} if group else set()
                )
                # Only the coal/CC/gas-steam fleet carries an outage overlay;
                # peakers (CT and the listed ST_GAS peakers) dispatch
                # economically and are skipped, matching the overlay. A
                # facility qualifies when ANY of its model bins does — a
                # mixed plant whose primary lookup lands on CT_PEAKER can
                # still carry derivable coal/CC units (per-unit resolution
                # below routes and skips unit-by-unit).
                if not (fac_groups & QUALIFYING_PLANT_GROUPS):
                    continue
                if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                    continue
                fac_name = remap_names.get(
                    int(fac_id), str(fac["facilityName"].iloc[0])
                )
                units = {
                    uid: _unit_year_grid(u, year)
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # A unit is coal (baseload) when its primary fuel is solid;
                # CAMPD labels every solid fuel — including ERCOT's lignite —
                # as "Coal".
                unit_is_coal = {
                    uid: str(u["primaryFuelInfo"].iloc[0]).strip().lower()
                    in ("coal", "coal refuse")
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                unit_type = {
                    uid: str(u["unitType"].iloc[0])
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # Per-unit (detect_mw, derate_mw, source) — the detector's CF
                # basis and the CSV's block share — plus the facility derate
                # total for the informational pct column.
                peaks = {uid: float(g.max()) for uid, g in units.items()}
                caps: dict[object, tuple[float, float, str]] = {
                    uid: unit_capacity_mw(
                        int(fac_id), uid, exact, by_digits, peaks[uid]
                    )
                    for uid in units
                }
                # Gross-silent facility fallback (non-ERCOT): some units
                # report opTime but never grossLoad (Seward's CFB boilers),
                # so the gross-based detector is blind to them in every year.
                # When NO unit at the facility reports any gross, rebuild the
                # unit series as a BINARY operated/idle proxy x an equal
                # share of the EIA-860 plant nameplate: a boiler that
                # operated at all in an hour was available (fractional
                # opTime is cycling, not an outage — scaling by the fraction
                # over-flags sustained part-load spans as outages under the
                # coal rule). Boiler<->generator id matching is unreliable
                # at such plants, so the equal split (not the per-unit EIA
                # match) is the capacity basis: one boiler down at a
                # two-boiler CFB derates half the plant.
                if iso != "ERCOT" and all(p <= 0.0 for p in peaks.values()):
                    npl = npl_by_plant.get(int(fac_id), 0.0)
                    ot_units = {
                        uid: u
                        for uid, u in fac.groupby("unitId", observed=True)
                        if float(
                            pd.to_numeric(u["opTime"], errors="coerce")
                            .fillna(0.0)
                            .max()
                        )
                        > 0.0
                    }
                    if npl > 0.0 and ot_units:
                        share = npl / len(ot_units)
                        units = {
                            uid: np.where(
                                _unit_year_grid(u, year, col="opTime") > 0.0, share, 0.0
                            )
                            for uid, u in ot_units.items()
                        }
                        peaks = {uid: float(g.max()) for uid, g in units.items()}
                        caps = {uid: (share, share, "optime_proxy") for uid in units}
                fac_cap = sum(derate for _, derate, _ in caps.values()) or 0.0
                ran = {uid for uid, pk in peaks.items() if pk > 0.0}
                for uid, gross in units.items():
                    detect_cap, derate_cap, cap_src = caps[uid]
                    # A unit that never reported gross output this year is
                    # left to the statistical/facility layers — we cannot
                    # distinguish a real full-year outage from a unit monitored
                    # under another id, and have no capacity basis for it.
                    if peaks[uid] <= 0.0 or derate_cap <= 0.0:
                        continue
                    # Route this unit's window to ITS model bin (non-ERCOT;
                    # ERCOT keeps the bin-sheet group verbatim and reroutes
                    # its split plants downstream in _unit_outage_target).
                    ugroup = (
                        group
                        if iso == "ERCOT"
                        else _resolve_unit_group(
                            unit_is_coal[uid],
                            unit_type.get(uid, ""),
                            fac_groups,
                            group,
                        )
                    )
                    if ugroup not in QUALIFYING_PLANT_GROUPS:
                        continue
                    # Coal (baseload): a sustained low-output gap is an outage.
                    # Everything else (load-following CC / gas-steam): only a
                    # genuine dead span — no output at all — counts, via the
                    # event-based rule, so economic idleness is not over-flagged.
                    # The detector thresholds on the unit's own nameplate
                    # (detect_cap), so the CC steam allocation — which lifts only
                    # the derate share — leaves every detected window unchanged.
                    if unit_is_coal[uid]:
                        windows = detect_outages(gross, detect_cap, min_outage_hours)
                    else:
                        windows = detect_outages_eventbased(
                            gross, detect_cap, min_outage_hours, ST_GAS_CF_PEAK
                        )
                    if not windows:
                        continue
                    clock = pd.date_range(
                        f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h"
                    )
                    # Revealed-availability filter: drop down spans that never
                    # overlap an in-merit (system-tight) hour — those are
                    # economic idling, not mechanical outages, so the unit is
                    # left available (not removed from energy or the co-opt
                    # reserve pool). Real outages coincide with tight hours and
                    # survive. No-op when --no-inmerit-filter or no price file.
                    if not args.no_inmerit_filter:
                        if year not in inmerit_cache:
                            inmerit_cache[year] = high_load_mask(
                                iso,
                                year,
                                len(clock),
                                args.high_load_pctl,
                                args.high_load_window_days,
                            )
                        mask = inmerit_cache[year]
                        cf = (
                            gross / detect_cap
                            if detect_cap > 0
                            else np.zeros_like(gross)
                        )
                        windows = filter_revealed_outages(
                            windows,
                            mask,
                            cf,
                            args.min_inmerit_hours,
                            args.fullstop_override_days,
                            args.fullstop_override_cf,
                        )
                        if not windows:
                            continue
                    out_days = 0.0
                    for s, e in windows:
                        start = clock[s]
                        last = clock[e - 1]
                        duration_days = round((e - s) / 24.0, 1)
                        out_days += duration_days
                        peers = sum(1 for o in ran if o != uid)
                        rows.append(
                            {
                                "facility_name": fac_name,
                                "facility_id": int(fac_id),
                                "unit_id": uid,
                                "unit_capacity_mw": round(derate_cap, 1),
                                "plant_capacity_mw": round(fac_cap, 1),
                                "unit_pct_of_plant": (
                                    round(100.0 * derate_cap / fac_cap, 1)
                                    if fac_cap
                                    else None
                                ),
                                "plant_group": ugroup,
                                "capacity_source": cap_src,
                                "outage_start": start.strftime("%Y-%m-%d"),
                                "outage_end": last.strftime("%Y-%m-%d"),
                                "duration_days": duration_days,
                                "peer_units_online": peers,
                                "total_units_at_plant": len(units),
                            }
                        )
                    if out_days > 0:
                        summary.append(
                            (
                                int(fac_id),
                                fac_name,
                                uid,
                                ugroup,
                                year,
                                len(windows),
                                out_days,
                            )
                        )

    # Net-zero-to-grid years (non-ERCOT). A fleet plant that reported real
    # grid generation in an earlier EIA-923 year but, in a target year, has
    # no F923 filing AND no CAMPD gross output (so the benchmark's CAMPD
    # backfill can't see it either) delivered nothing the benchmark counts —
    # even when CAMPD opTime shows its boilers running (the PA waste-coal
    # behind-the-meter crypto conversions: Gilberton, Panther Creek,
    # Scrubgrass, Grant Town). An explicit ~zero F923 filing counts too.
    # Plants that stopped filing F923 but still report CAMPD gross (Colver,
    # Cordova) are NOT flagged: the benchmark backfills them and they
    # genuinely serve the grid. One full-year window per plant-year.
    if iso != "ERCOT":
        e923 = pd.read_parquet(
            PROCESSED_DIR / "eia923_monthly_generation.parquet",
            columns=["plant_id", "netgen_annual_mwh", "year"],
        )
        tot = e923.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum(min_count=1)
        years_in_923 = sorted(e923["year"].unique())
        for fac_id, group in sorted(group_by_code.items()):
            if group not in QUALIFYING_PLANT_GROUPS:
                continue
            if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                continue
            npl = npl_by_plant.get(int(fac_id), 0.0)
            if npl <= 0.0:
                continue
            for year in args.years:
                if year not in years_in_923:
                    continue
                t = tot.get((fac_id, year))
                prior = [tot.get((fac_id, y)) for y in years_in_923 if y < year]
                ran_before = any(
                    p is not None and not pd.isna(p) and p > 10_000.0 for p in prior
                )
                filed = t is not None and not pd.isna(t)
                zero_now = (filed and t < 1_000.0) or (
                    not filed and (int(fac_id), year) not in campd_gross_seen
                )
                if not (ran_before and zero_now):
                    continue
                rows.append(
                    {
                        "facility_name": name_by_code.get(int(fac_id), ""),
                        "facility_id": int(fac_id),
                        "unit_id": "NET0-923",
                        "unit_capacity_mw": round(npl, 1),
                        "plant_capacity_mw": round(npl, 1),
                        "unit_pct_of_plant": 100.0,
                        "plant_group": group,
                        "capacity_source": "eia923_netzero",
                        "outage_start": f"{year}-01-01",
                        "outage_end": f"{year}-12-31",
                        "duration_days": 365.0,
                        "peer_units_online": 0,
                        "total_units_at_plant": 1,
                    }
                )
                summary.append(
                    (
                        int(fac_id),
                        name_by_code.get(int(fac_id), ""),
                        "NET0-923",
                        group,
                        year,
                        1,
                        365.0,
                    )
                )

    cols = [
        "facility_name",
        "facility_id",
        "unit_id",
        "unit_capacity_mw",
        "plant_capacity_mw",
        "unit_pct_of_plant",
        "plant_group",
        "capacity_source",
        "outage_start",
        "outage_end",
        "duration_days",
        "peer_units_online",
        "total_units_at_plant",
    ]
    out = pd.DataFrame(rows, columns=cols).sort_values(
        ["facility_id", "unit_id", "outage_start"]
    )
    out.to_csv(args.out, index=False)

    print(f"\nwrote {len(out)} unit-outage windows to {args.out}\n")
    print(
        f"{'code':>6} {'plant':<24}{'unit':<8}{'group':<11}{'yr':>5}"
        f"{'#win':>5}{'out d':>8}"
    )
    for code, nm, uid, g, yr, n, td in sorted(
        summary, key=lambda r: (r[0], str(r[2]), r[4])
    ):
        print(f"{code:>6} {nm[:23]:<24}{str(uid):<8}{g:<11}{yr:>5}{n:>5}{td:>8.0f}")


if __name__ == "__main__":
    main()
