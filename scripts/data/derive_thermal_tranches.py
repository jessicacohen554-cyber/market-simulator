"""Derive each thermal plant's committed and must-run tranche % from CAMPD.

Generalizes :mod:`scripts.data.derive_cc_committed_pct` (CC-only, ERCOT-only) to
**every thermal group and every ISO**, so a plant's minimum-stable-load
(committed) and baseload-floor (must-run) tranche sizes are grounded in its own
observed EPA CAMPD/CEMS hourly output rather than coarse assumed CSV buckets.
This is the per-ISO analogue of the hardcoded ERCOT maps
``fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT`` / ``fleet.COAL_MUSTRUN_BY_PLANT``:
the output CSV is loaded at runtime and applied per plant, so adding a new ISO
is just running this script against that ISO's CAMPD extracts.

Method, per ``(plant, group)`` in the ISO's fleet (groups: CC_REGULAR, CC_CHP,
CT_PEAKER, CT_CHP, ST_GAS, COAL):

  1. CAMPD gross load is summed across the plant's units per hour and scaled to
     **net** by the plant's parasitic factor (same grid-MW basis the dispatch
     produces), via :func:`market_sim.data.campd.plant_hourly_net`.
  2. Available capacity per hour = nameplate x the unit-outage availability
     multiplier (:func:`market_sim.data.outages.unit_outage_derate_factors`),
     i.e. nameplate net of the plant's units the unit-outage extract reports in
     maintenance — so a plant running its remaining units while one is out is
     not mistaken for running below its true minimum.
  3. **Committed %** = the P5 of the available-capacity factor over the plant's
     *online* hours (net > ``_ONLINE_FRAC`` of available capacity): the minimum
     stable load the plant holds at when backed down, excluding ramp transients.
  4. **Must-run %** = the P5 of the available-CF over *all* hours the plant has
     any available capacity. For a baseload unit that almost never shuts off
     (coal) this is the sunk floor it holds even when prices are low; for a
     load-following unit that cycles off (CC/CT/ST gas) it is ~0, exactly the
     physical must-run of an economically-dispatched plant. The dispatch uses
     this floor only where it is structurally meaningful (coal), so gas values
     are recorded for transparency but generally land near zero.

     **Must-run online % (coal only)** = the P5 of online *net MW* as a
     fraction of nameplate — the genuine synchronization Pmin (the level the
     unit holds 95% of the time it is synchronized). The all-hours
     available-CF must-run above reads ~2x high for an always-online coal unit
     (its all-hours P5 sits in its normal operating band, and the
     outage-derate denominator inflates the available-CF), so this online-net
     floor (~20-30% of nameplate) is the smaller, physically-truer
     synchronization floor. Written as ``mustrun_online_pct``; selected at
     runtime over ``mustrun_pct`` by ``ScenarioConfig.coal_mustrun_online_pmin``
     (rebuild step 2). See
     docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md.
  5. **Peaking %** (combined cycles only) = the duct-firing / scarcity reach:
     the share of the plant's demonstrated sustained maximum (P99.5 of online
     net MW) that it clears in fewer than 5% of its online hours,
     ``100 x (1 - P95/P99.5)``. Computed on raw net-MW ratios (not the
     available-CF, whose top tail is distorted by outage-derate windows and
     the gross-vs-nameplate basis), capped at :data:`_PEAKING_CAP`. A plant
     that holds one flat full-load plateau derives ~0 (no duct band); a CC
     whose top capacity only shows up in scarcity hours derives the size of
     that rarely-used band. Applied per plant in ``bins_to_fleet`` via
     ``fleet.thermal_tranche_peaking`` (supersedes the offer curve's class
     ``pct_peaking``).

Per ISO it writes ``data/raw/_processed-legacy/thermal_tranches_{ISO}.csv`` with one row
per ``(plant_code, plant_group)``. Plants with too little run-time to set a
reliable floor are written with ``status != ok`` and keep the model's CSV/class
default.

``--chp-floors-from PATH`` consumes the CHP steam-following floors
(``chp_pmin_cf`` / ``chp_sector`` and the ``eia923_cf`` fallback rows) from a
previously committed artifact instead of re-deriving them, so a re-derivation
of the committed/peaking shares over a different year window (e.g. CAISO P2:
shares from 2024-25, floors from P3's pooled 2023-25 run) does not silently
move the must-run layer.

Usage:
    python scripts/data/derive_thermal_tranches.py --iso PJM --years 2024
    python scripts/data/derive_thermal_tranches.py --iso ERCOT --years 2023 2024
    python scripts/data/derive_thermal_tranches.py --iso CAISO --years 2024 2025 \
        --chp-floors-from data/raw/_processed-legacy/thermal_tranches_CAISO.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins, load_fleet_from_csv  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

# Thermal groups that carry an offer-curve committed/must-run tranche.
_THERMAL_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP", "COAL"}
)

# CHP cogen groups: these additionally get a steam-following floor
# (``chp_pmin_cf``) and an EIA-923 sector class (``chp_sector``), the
# ISO-generic analogue of the hardcoded ERCOT maps
# ``fleet.CHP_PMIN_CF_BY_PLANT`` / ``fleet.CHP_SECTOR_CLASS_BY_PLANT``.
_CHP_GROUPS: frozenset[str] = frozenset({"CC_CHP", "CT_CHP", "ST_CHP"})

# Percentile of the all-hours available-CF distribution taken as a CHP cogen's
# total must-run floor — the steady host-steam output it holds essentially
# always. P2 matches how ERCOT's CHP_PMIN_CF_BY_PLANT values were derived
# (p2 CAMPD gross CF, non-outage hours).
_CHP_PMIN_PCTILE: int = 2

# Percentile of the ONLINE-hours available-CF distribution used in a CHP
# cogen's steam-host OPERATING level (``steam_level_cf``). WP-3 (owner-ruled
# 2026-07-19, `docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md`,
# rule-23 re-derivation citing FINDING-caiso95 §5): the former p25-of-all-hours
# statistic mixed economic/host-driven offline zeros into the LEVEL, so a host
# that runs a high baseload when on but takes offline stretches (the measured
# CAISO CT_CHP conduct: >=70 % loading in 79/85/88 % of on-capacity-hours,
# 2023/24/25) under-measured to a ~12-14 % trickle. The replacement conditions
# on being online:
#
#   steam_level_cf = (on-hour frequency over available hours)
#                    x (p50 available-CF conditional on online)
#
# which reproduces the measured loading-when-on baseload directly. The
# statistic still self-targets with no threshold parameter: outage hours drop
# out of the sample (avail_cap = 0), a rarely-online cycler's on-frequency
# collapses its level toward 0, and a genuinely flat steam host keeps its
# online level. The p2 floor above only captures the never-below minimum.
# Consumed by ScenarioConfig.chp_steam_floor_p25 (field name kept for run-config
# lineage; the level source is this statistic since WP-3).
_CHP_STEAM_LEVEL_ON_PCTILE: int = 50

# EIA-923 Page 1 "EIA Sector Number" -> the BTM sector class the model's
# chp_btm_pct uses. Cogen sectors map directly (3 = NAICS-22 / merchant cogen,
# 5 = commercial cogen, 7 = industrial cogen); non-cogen sectors land on the
# nearest class so a plant whose 923 rows are mixed still classifies.
_EIA_SECTOR_CLASS: dict[int, str] = {
    1: "merchant",
    2: "merchant",
    3: "merchant",
    4: "commercial",
    5: "commercial",
    6: "industrial",
    7: "industrial",
}


def _chp_sector_map(years: list[int]) -> dict[int, str]:
    """Return ``{plant_id: sector_class}`` from the EIA-923 Page 1 workbooks.

    Reads "EIA Sector Number" for every plant from the raw
    ``data/raw/f923_{year} (1).zip`` archives (the same source the
    monthly-generation artifact is built from) and maps it through
    :data:`_EIA_SECTOR_CLASS`. When a plant's sector differs across rows or
    years (rare), the most frequent class wins.
    """
    import zipfile
    from collections import Counter

    votes: dict[int, Counter] = {}
    for year in years:
        zpath = REPO / "inputs" / "raw-data" / f"f923_{year} (1).zip"
        if not zpath.exists():
            print(f"  (no EIA-923 archive for {year}: {zpath.name})")
            continue
        z = zipfile.ZipFile(zpath)
        sheet_file = next((n for n in z.namelist() if "Schedules_2_3_4_5" in n), None)
        if sheet_file is None:
            continue
        with z.open(sheet_file) as f:
            df = pd.read_excel(
                f,
                sheet_name="Page 1 Generation and Fuel Data",
                skiprows=5,
                usecols=["Plant Id", "EIA Sector Number"],
            )
        df = df.dropna()
        for pid, sector in df.itertuples(index=False):
            klass = _EIA_SECTOR_CLASS.get(int(sector))
            if klass is not None:
                votes.setdefault(int(pid), Counter())[klass] += 1
    return {pid: c.most_common(1)[0][0] for pid, c in votes.items()}


# EIA-923-CF fallback floor for CHP plants without CAMPD coverage (small
# cogens below the CEMS reporting threshold — e.g. every PJM ST_CHP, and the
# CAISO refinery / Kern EOR cogens, which are largely exempt from Part 75
# CEMS). The floor is the plant's MINIMUM monthly EIA-923 class CF over the
# pooled window — the monthly analogue of the CAMPD all-hours P2: a cogen that
# idles (or stands down for an outage) for a whole month carries no hard steam
# obligation at that level, while a steady steam host's worst month measures
# the output it always holds. The month-to-hour haircut converts that monthly
# average into an hourly holdable floor (within its floor month a plant's
# hourly P2 runs a bit under the monthly mean), and the cap keeps a
# CEMS-invisible plant from being forced on harder than any CAMPD-observed
# peer.
_CHP_F923_FLOOR_FACTOR: float = 0.40
_CHP_F923_FLOOR_CAP: float = 75.0

# Days per month (non-leap); February is overridden per year so a leap-year
# CF is not understated by ~3.4%.
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _chp_f923_floor_cf(
    years: list[int],
    cap: dict[tuple[int, str], float],
) -> dict[tuple[int, str], tuple[float, float]]:
    """Return ``{(code, group): (pmin_cf %, steam_level_cf %)}`` from EIA-923.

    For each CHP ``(plant, group)`` in the fleet, every reported month's net
    generation of that class (canonical :func:`classify_plant` bucketing)
    divided by ``nameplate x hours-in-month`` gives a monthly CF sample; the
    minimum over the pooled window, scaled by :data:`_CHP_F923_FLOOR_FACTOR`
    and capped, becomes the total must-run floor for plants the CAMPD
    extracts cannot see. Plants with no class generation at all are absent
    from the result (no row, no floor); a plant with a zero month keeps a row
    with a zero floor — its EIA-923 sector still sizes the BTM share.

    The second element is the WP-3 scope-(b) steam-host operating LEVEL for
    CEMS-invisible cogens (owner-ruled 2026-07-19): the pooled mean class CF —
    the plant's measured EIA-923 grid delivery spread over its reported
    months, i.e. the implied sustained baseload the host's steam contract
    delivers. It is the EIA-923 analogue of the CAMPD loading-when-on
    construction (on-frequency x median-on loading integrates to the same
    delivered-energy level), so the two lenses emit ONE statistic family into
    ``steam_level_cf``. Uncapped except at 100 % of nameplate; a cycling or
    mostly-idle cogen's low delivered energy keeps its level low (the
    statistic self-targets on delivery, no threshold parameter).
    """
    from market_sim.config.plant_taxonomy import classify_plant
    from market_sim.data.eia923 import load_monthly_generation, monthly_netgen_columns

    gen = load_monthly_generation()
    gen = gen[gen["year"].isin(years)].copy()
    gen["klass"] = [
        classify_plant(f, pm, str(c).upper().startswith("Y"), int(pid))
        for f, pm, c, pid in zip(
            gen["fuel_type"], gen["prime_mover"], gen["chp"], gen["plant_id"]
        )
    ]
    mcols = monthly_netgen_columns()
    by_key = gen.groupby(["plant_id", "klass", "year"])[mcols].sum()
    out: dict[tuple[int, str], tuple[float, float]] = {}
    for (code, group), nameplate in cap.items():
        if group not in _CHP_GROUPS or nameplate <= 0:
            continue
        min_cf, total_mwh, total_hours = np.inf, 0.0, 0.0
        for year in years:
            try:
                months = by_key.loc[(code, group, year)].to_numpy(dtype=float)
            except KeyError:
                continue
            hours = np.array(_DAYS_IN_MONTH, dtype=float) * 24.0
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                hours[1] = 29.0 * 24.0
            cf = months / (nameplate * hours)
            min_cf = min(min_cf, float(np.nanmin(cf)))
            total_mwh += float(np.nansum(months))
            total_hours += float(np.sum(hours[np.isfinite(cf)]))
        if total_mwh <= 0.0 or not np.isfinite(min_cf):
            continue
        pmin = min(
            100.0 * max(min_cf, 0.0) * _CHP_F923_FLOOR_FACTOR,
            _CHP_F923_FLOOR_CAP,
        )
        level = (
            min(100.0, 100.0 * max(total_mwh, 0.0) / (nameplate * total_hours))
            if total_hours > 0.0
            else 0.0
        )
        out[(code, group)] = (pmin, level)
    return out


# An hour counts as "online / committed" when net output clears this fraction
# of the hour's available capacity — low enough to admit one unit of a
# multi-unit plant idling at part load, high enough to reject CEMS sensor noise
# and the single-hour ramp through zero on start/stop.
_ONLINE_FRAC: float = 0.05

# Plant-level synchronization-fraction threshold (step-3a online%-scaled
# forcing). An hour counts toward ``online_frac`` when the plant's net MW
# clears this fraction of *nameplate* — i.e. ANY unit of the plant is
# synchronized (producing) rather than fully shut down. Deliberately near zero
# (not the 5%-of-*available* ``_ONLINE_FRAC`` mask used for the floor
# percentiles, which under-counts a deeply-backed-down but still-synchronized
# supercritical): a unit two-shifting to zero reads its true online share while
# an always-online unit reads ~1.0. Just above CEMS zero-noise so a reported-but-
# idle hour does not inflate the fraction. See
# docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md (Thread D).
_SYNC_MW_NAMEPLATE_FRAC: float = 0.01

# Percentile of the CF distribution taken as the floor. P5 (not the absolute
# minimum) discards isolated ramp-transient hours while still capturing the
# minimum stable / baseload load.
_FLOOR_PCTILE: int = 5

# A plant needs at least this many online hours over the window to set a floor.
_MIN_ONLINE_HOURS: int = 24

# Physical ceilings on the derived tranche shares (a unit's CEMS gross can
# exceed its EIA nameplate, which would otherwise push the floor above 100%).
_COMMITTED_CAP: float = 0.70
_MUSTRUN_CAP: float = 0.60

# Combined-cycle groups that derive a duct-firing peaking share.
_PEAKING_GROUPS: frozenset[str] = frozenset({"CC_REGULAR", "CC_CHP"})

# Groups whose measured synchronization fraction (``online_frac``) is emitted:
# COAL for the step-3a online%-scaled min-load forcing, and the merchant gas
# committed groups for the per-plant local-reliability commitment floor
# (``ScenarioConfig.cc_mustrun_per_plant`` / ``st_gas_mustrun_per_plant``).
# ST_GAS joined 2026-07-12 (MISO 2025 Southern-gas lane): the Entergy South
# steam fleet is measured mostly-/always-online (Nine Mile 98.2% of all hours,
# Sabine 85.6%, Lewis Creek 87.8% over 2023-2025 CEMS) under VLR/self-
# commitment, so its synchronization fraction is a real measured quantity the
# runtime floor needs — the old "ST gas cycles off, floors come from the drag
# mechanisms" assumption is contradicted by the measurement itself for these
# plants (true cyclers still publish their small fractions and force little).
# The fraction itself is computed for every group (``sync_hours``); this set
# only gates which rows publish it.
_ONLINE_FRAC_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"}
)

# Ceiling on the derived peaking share (% of capacity). Duct burners add at
# most ~20-25% over a CC's unfired base rating; anything larger from the
# estimator is distribution noise (a cycler with a thin top tail), not duct.
_PEAKING_CAP: float = 25.0

# The peaking band is the capacity reached in fewer than (100 - P) % of
# online hours, against the P99.5 demonstrated sustained maximum.
_PEAKING_BASE_PCTILE: float = 95.0
_PEAKING_MAX_PCTILE: float = 99.5


def _parasitic_factor_map() -> dict[int, float]:
    """Return ``{plant_id: net/gross factor}`` from the derived artifact."""
    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def _fleet_nameplate_and_group(
    iso: str,
) -> tuple[dict[tuple[int, str], float], dict[int, str]]:
    """Return ``({(code, group): nameplate}, {code: primary_group})`` for an ISO.

    ERCOT reads the CAMPD bin sheet (one bin per plant); other ISOs read the
    per-plant EIA-860 fleet. The primary group is the group holding the most
    nameplate at each plant, used to attribute the facility-summed CAMPD net.
    """
    cap: dict[tuple[int, str], float] = {}
    if iso == "ERCOT":
        bins = load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
        for c, g, m in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
        ):
            if m and float(m) > 0:
                cap[(int(c), str(g))] = cap.get((int(c), str(g)), 0.0) + float(m)
    else:
        for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
            code = int(gen.plant_code)
            if code <= 0 or not gen.plant_group:
                continue
            key = (code, gen.plant_group)
            cap[key] = cap.get(key, 0.0) + float(gen.pmax_mw)
    primary: dict[int, str] = {}
    best: dict[int, float] = {}
    for (code, group), mw in cap.items():
        if mw > best.get(code, -1.0):
            best[code], primary[code] = mw, group
    return cap, primary


def _consume_chp_floors(rows: list[dict], prior: pd.DataFrame) -> list[dict]:
    """Override the freshly derived CHP floors with a prior artifact's values.

    Every CHP ``(plant_code, plant_group)`` present in ``prior`` keeps its
    committed ``chp_pmin_cf`` / ``chp_sector`` verbatim (the must-run layer is
    consumed, not re-derived); prior CHP rows the new derivation no longer
    emits are appended — verbatim for ``eia923_cf`` fallback rows, or as a
    floor-only row (``status="chp_floor_only"``, no committed/must-run tranche
    columns) when the plant was CAMPD-visible in the prior window but not in
    the new one. CHP rows absent from ``prior`` keep their fresh values.
    """
    prior_chp = prior[prior["plant_group"].isin(_CHP_GROUPS)]
    by_key: dict[tuple[int, str], dict] = {
        (int(r["plant_code"]), str(r["plant_group"])): r.to_dict()
        for _, r in prior_chp.iterrows()
    }
    seen: set[tuple[int, str]] = set()
    for row in rows:
        key = (row["plant_code"], row["plant_group"])
        if row["plant_group"] not in _CHP_GROUPS:
            continue
        if row["status"] not in ("ok", "eia923_cf"):
            continue  # filtered from the output (rarely_online), not a floor
        seen.add(key)
        p = by_key.get(key)
        if p is not None:
            row["chp_pmin_cf"] = p.get("chp_pmin_cf")
            row["chp_sector"] = p.get("chp_sector")
            if "chp_btm_pct" in p and p.get("chp_btm_pct") not in (None, float("nan")):
                row["chp_btm_pct"] = p["chp_btm_pct"]
    for key, p in sorted(by_key.items()):
        if key in seen:
            continue
        if str(p.get("status")) != "eia923_cf":
            p = dict(
                p,
                status="chp_floor_only",
                committed_pct=None,
                mustrun_pct=None,
                p25_cf=None,
                median_cf=None,
                # Null the steam LEVEL columns: the new statistic
                # (steam_level_cf, WP-3) and the superseded p25_allhr_cf a
                # pre-WP-3 prior artifact may still carry.
                p25_allhr_cf=None,
                steam_level_cf=None,
                online_hours=0,
            )
            print(
                f"  (carrying forward CHP floor for {key[0]} {key[1]}: "
                f"CAMPD-visible in the prior window only)"
            )
        rows.append(p)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--years", nargs="+", type=int, default=[2024])
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--chp-floors-from",
        default=None,
        help="Existing artifact whose CHP steam-following floors "
        "(chp_pmin_cf / chp_sector, incl. eia923_cf rows) are consumed "
        "verbatim instead of re-derived.",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    from market_sim.config.paths import PROCESSED_DIR

    out_path = (
        Path(args.out) if args.out else (PROCESSED_DIR / f"thermal_tranches_{iso}.csv")
    )

    states = campd.states_for_iso(iso)
    if not states:
        ap.error(f"no CAMPD state mapping for ISO {iso}")

    cap, primary = _fleet_nameplate_and_group(iso)
    factors = _parasitic_factor_map()
    chp_sectors = _chp_sector_map(args.years)

    # Pool the available-CF samples across the requested years, per (code, group).
    online_cf: dict[tuple[int, str], list[np.ndarray]] = {}
    allhr_cf: dict[tuple[int, str], list[np.ndarray]] = {}
    online_mw: dict[tuple[int, str], list[np.ndarray]] = {}
    # Synchronization fraction (step-3a): [synced-hour count, total-hour count]
    # pooled across years, per (code, group). frac = synced / total, capped 1.0.
    sync_hours: dict[tuple[int, str], list[int]] = {}
    for year in args.years:
        df = campd.load_campd_hourly(states, [year])
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue
        net = campd.plant_hourly_net(df, factors, year)  # {code: (8760,) net MW}
        derate = unit_outage_derate_factors(year, iso=iso)
        for (code, group), nameplate in cap.items():
            if group not in _THERMAL_GROUPS or nameplate <= 0:
                continue
            # Attribute the facility-summed CAMPD net to the plant's primary
            # group only; secondary-group rows at a multi-group plant are left
            # to the CSV default (their net cannot be separated from CEMS).
            if primary.get(code) != group:
                continue
            series = net.get(code)
            if series is None:
                continue
            avail_mult = derate.get((code, group), np.ones(len(series)))
            avail_cap = nameplate * avail_mult
            with np.errstate(divide="ignore", invalid="ignore"):
                acf = np.where(avail_cap > 0.0, series / avail_cap, 0.0)
            acf = np.clip(acf, 0.0, 1.5)  # guard multi-unit CEMS noise
            # Exclude hours with no usable net (NaN from a missing parasitic
            # factor or a CEMS reporting gap) from both samples.
            finite = np.isfinite(acf) & (avail_cap > 0.0)
            online = finite & (series > _ONLINE_FRAC * avail_cap)
            # Synchronization fraction (coal step-3a online%-scaled forcing):
            # count hours the plant has ANY unit synchronized on the net-MW
            # basis (net > 1% of nameplate), against the full year (8760). The
            # net series is always finite (offline unit-hours are zeros), so the
            # denominator is the whole year — a plant offline for a stretch
            # genuinely scores below 1.0. Pooled across years below.
            sync = series > _SYNC_MW_NAMEPLATE_FRAC * nameplate
            acc = sync_hours.setdefault((code, group), [0, 0])
            acc[0] += int(sync.sum())
            acc[1] += int(len(series))
            allhr_cf.setdefault((code, group), []).append(acf[finite])
            if online.any():
                online_cf.setdefault((code, group), []).append(acf[online])
                # Raw net MW over online hours, for the peaking (duct-firing)
                # estimator: percentile ratios of net MW are basis-free, so
                # the gross-vs-nameplate mismatch and derate-window spikes
                # that pollute the available-CF top tail cancel out.
                online_mw.setdefault((code, group), []).append(series[online])

    names = {}
    if iso != "ERCOT":
        for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
            names[int(gen.plant_code)] = gen.name

    rows: list[dict] = []
    for (code, group), nameplate in sorted(cap.items()):
        if group not in _THERMAL_GROUPS or primary.get(code) != group:
            continue
        on = online_cf.get((code, group))
        allh = allhr_cf.get((code, group))
        n_online = int(sum(len(a) for a in on)) if on else 0
        if not on or n_online < _MIN_ONLINE_HOURS:
            rows.append(
                {
                    "plant_code": code,
                    "plant_group": group,
                    "name": names.get(code, ""),
                    "status": "rarely_online",
                    "online_hours": n_online,
                }
            )
            continue
        on_cat = np.concatenate(on)
        all_cat = np.concatenate(allh) if allh else on_cat
        # Committed = min stable load when online; cap at a physical ceiling
        # (a plant whose CEMS gross runs above its EIA nameplate, e.g. Doswell,
        # would otherwise report a committed floor > 100%).
        committed = min(float(np.percentile(on_cat, _FLOOR_PCTILE)), _COMMITTED_CAP)
        # Must-run = the always-on baseload floor. Physically meaningful only
        # for COAL (take-or-pay baseload) — the dispatch applies a must-run
        # floor to coal only; fast gas (CC / CT / ST) is load-following and is
        # never forced on, so its must-run is recorded as zero even when its
        # high capacity factor would make the all-hours floor look high.
        if group == "COAL":
            mustrun = min(float(np.percentile(all_cat, _FLOOR_PCTILE)), _MUSTRUN_CAP)
            # Step 2 (synchronization min-load): the net MW the unit holds 95%
            # of its *online* time, as a fraction of nameplate — the genuine
            # online Pmin. For an ~always-online coal unit the all-hours
            # available-CF floor above reads high (its all-hours P5 sits in its
            # normal operating band, not its true minimum) and on the
            # outage-adjusted available-CF basis it is ~2x the level CEMS shows
            # the unit actually holds. This online-net-MW floor (~20-30% of
            # nameplate) is the synchronization Pmin the dispatch should force
            # on instead. See
            # docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md
            # (Thread C/D); selected at runtime by coal_mustrun_online_pmin.
            mw_on = np.concatenate(online_mw[(code, group)])
            mustrun_online = (
                min(
                    float(np.percentile(mw_on, _FLOOR_PCTILE)) / nameplate, _MUSTRUN_CAP
                )
                if nameplate > 0.0
                else mustrun
            )
        else:
            mustrun = 0.0
            mustrun_online = 0.0
        row = {
            "plant_code": code,
            "plant_group": group,
            "name": names.get(code, ""),
            "status": "ok",
            "nameplate_mw": round(nameplate, 1),
            "online_hours": n_online,
            "committed_pct": round(100.0 * committed, 1),
            "mustrun_pct": round(100.0 * mustrun, 1),
            "mustrun_online_pct": round(100.0 * mustrun_online, 1),
            # Synchronization fraction: the share of the year the plant has any
            # unit synchronized. COAL drives the step-3a online%-scaled min-load
            # forcing (coal_sync_online_frac): an ~always-online supercritical
            # (~1.0) is held all 8760 h, a two-shifting cycler is forced only in
            # its top-load online hours. The merchant gas committed groups
            # (:data:`_GAS_MUSTRUN_GROUPS`) carry the SAME measured fraction for
            # the local-reliability commitment floor (cc_mustrun_per_plant,
            # G-20 eastern under-run follow-up): it sizes the committed window —
            # the top-online_frac system-load hours the plant's committed
            # tranche is held on. ST_GAS carries it for the same floor under
            # its own gate (st_gas_mustrun_per_plant — the VLR/self-commitment
            # trace of the Entergy South steam fleet). Same CEMS quantity,
            # same estimator; only the consumer differs. CHP groups stay
            # blank — their floor is the steam host (rule 19).
            "online_frac": (
                round(
                    min(
                        1.0, sync_hours[(code, group)][0] / sync_hours[(code, group)][1]
                    ),
                    3,
                )
                if group in _ONLINE_FRAC_GROUPS
                and sync_hours.get((code, group), [0, 0])[1] > 0
                else ""
            ),
            "p25_cf": round(100.0 * float(np.percentile(on_cat, 25)), 1),
            "median_cf": round(100.0 * float(np.percentile(on_cat, 50)), 1),
        }
        # Duct-firing / scarcity peaking share (combined cycles): the share
        # of the demonstrated sustained maximum that only shows up in the
        # rarest online hours. Net-MW percentile ratio, so the CF basis
        # cancels (see module docstring, step 5).
        if group in _PEAKING_GROUPS:
            mw = np.concatenate(online_mw[(code, group)])
            mw_max = float(np.percentile(mw, _PEAKING_MAX_PCTILE))
            mw_base = float(np.percentile(mw, _PEAKING_BASE_PCTILE))
            if mw_max > 0.0:
                row["peaking_pct"] = round(
                    min(100.0 * max(0.0, 1.0 - mw_base / mw_max), _PEAKING_CAP),
                    1,
                )
        # CHP cogens additionally carry their steam-following total must-run
        # floor (P2 of the all-hours available-CF, the ERCOT
        # CHP_PMIN_CF_BY_PLANT convention) and the EIA-923 sector class that
        # sizes the behind-the-meter host self-supply share.
        if group in _CHP_GROUPS:
            row["chp_pmin_cf"] = round(
                100.0 * float(np.percentile(all_cat, _CHP_PMIN_PCTILE)), 1
            )
            row["chp_sector"] = chp_sectors.get(code, "")
            # Steam-host operating level (see _CHP_STEAM_LEVEL_ON_PCTILE):
            # on-hour frequency x median loading-conditional-on-online, over
            # the same multi-year sample and masks the p2 floor uses (WP-3
            # loading-when-on construction; supersedes the p25-of-all-hours
            # statistic that mixed offline zeros into the level).
            on_freq = len(on_cat) / len(all_cat) if len(all_cat) else 0.0
            row["steam_level_cf"] = round(
                100.0
                * on_freq
                * float(np.percentile(on_cat, _CHP_STEAM_LEVEL_ON_PCTILE)),
                1,
            )
        rows.append(row)

    # CHP plants the CAMPD extracts cannot see (no facility series, or too few
    # online hours) get an EIA-923-derived steam-following floor instead, so
    # the sub-CEMS cogen fleet (e.g. every PJM ST_CHP plant) still carries its
    # measured host-steam obligation. status="eia923_cf" marks the source; the
    # committed/must-run tranche columns stay blank (class defaults apply).
    have_floor = {
        (r["plant_code"], r["plant_group"])
        for r in rows
        if r["status"] == "ok" and r["plant_group"] in _CHP_GROUPS
    }
    f923_floors = _chp_f923_floor_cf(args.years, cap)
    for (code, group), (pmin, level) in sorted(f923_floors.items()):
        if (code, group) in have_floor or primary.get(code) != group:
            continue
        rows.append(
            {
                "plant_code": code,
                "plant_group": group,
                "name": names.get(code, ""),
                "status": "eia923_cf",
                "nameplate_mw": round(cap[(code, group)], 1),
                "online_hours": 0,
                "chp_pmin_cf": round(pmin, 1),
                # WP-3 scope (b): the EIA-923 delivery-implied steam level for
                # cogens the CAMPD extracts cannot see (below the Part 75 CEMS
                # threshold — the bulk of the CAISO CT_CHP delivery gap).
                "steam_level_cf": round(level, 1),
                "chp_sector": chp_sectors.get(code, ""),
            }
        )

    if args.chp_floors_from:
        rows = _consume_chp_floors(rows, pd.read_csv(args.chp_floors_from))

    out = pd.DataFrame(rows)
    ok = out[out["status"].isin(["ok", "eia923_cf", "chp_floor_only"])].sort_values(
        ["plant_group", "plant_code"]
    )

    # Carry forward per-plant annotations from any existing output file.
    # chp_btm_pct: manual BTM override (physical annotation, not re-derived).
    # chp_sector: EIA-923 sector class — re-derived from ZIP archives; when
    #   those archives are unavailable the column comes back all-NaN, so fall
    #   back to the prior file to avoid silently losing sector classifications.
    if out_path.exists():
        _preserve_cols: list[str] = []
        if "chp_btm_pct" not in ok.columns:
            _preserve_cols.append("chp_btm_pct")
        if ok.get("chp_sector", pd.Series(dtype=object)).isna().all():
            _preserve_cols.append("chp_sector")
        if _preserve_cols:
            try:
                prior_out = pd.read_csv(
                    out_path,
                    usecols=["plant_code", "plant_group"] + _preserve_cols,
                )
                # Only preserve rows that actually have a value in at least one col
                mask = prior_out[_preserve_cols].notna().any(axis=1)
                prior_out = prior_out[mask]
                if not prior_out.empty:
                    ok = ok.drop(
                        columns=[c for c in _preserve_cols if c in ok.columns],
                        errors="ignore",
                    )
                    ok = ok.merge(
                        prior_out, on=["plant_code", "plant_group"], how="left"
                    )
            except (ValueError, KeyError):
                pass  # prior file missing expected columns — nothing to preserve

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok.to_csv(out_path, index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 400)
    print(
        f"\n{iso} thermal committed / must-run %  —  CAMPD years "
        f"{args.years} (net vs available capacity)\n"
    )
    cols = [
        "plant_code",
        "plant_group",
        "name",
        "nameplate_mw",
        "online_hours",
        "committed_pct",
        "mustrun_pct",
        "mustrun_online_pct",
        "median_cf",
    ]
    campd_ok = ok[ok["status"] == "ok"]
    print(campd_ok[cols].to_string(index=False))
    chp_rows = ok[ok["plant_group"].isin(_CHP_GROUPS)]
    if not chp_rows.empty:
        print(
            "\nCHP steam-following floors (chp_pmin_cf % of nameplate; "
            "source: CAMPD p2 where status=ok, EIA-923 CF otherwise):"
        )
        print(
            chp_rows[
                [
                    "plant_code",
                    "plant_group",
                    "name",
                    "nameplate_mw",
                    "status",
                    "chp_pmin_cf",
                    "chp_sector",
                ]
            ].to_string(index=False)
        )
    print("\nby group (capacity-weighted committed%):")
    for g, sub in campd_ok.groupby("plant_group"):
        w = sub["nameplate_mw"]
        cw = float((sub["committed_pct"] * w).sum() / w.sum()) if w.sum() else 0.0
        mw = float((sub["mustrun_pct"] * w).sum() / w.sum()) if w.sum() else 0.0
        mwo = (
            float((sub["mustrun_online_pct"] * w).sum() / w.sum())
            if w.sum() and "mustrun_online_pct" in sub
            else 0.0
        )
        print(
            f"  {g:<12} n={len(sub):>3}  committed~{cw:5.1f}%  "
            f"mustrun~{mw:5.1f}%  mustrun_online~{mwo:5.1f}%"
        )
    skipped = out[out["status"] != "ok"]
    print(
        f"\nwrote {len(ok)} plant-groups to {out_path} "
        f"({len(skipped)} skipped: too little run-time)"
    )


if __name__ == "__main__":
    main()
