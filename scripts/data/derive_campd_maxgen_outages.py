"""Derive declared-event-window revealed unit derates from CAMPD (M-2).

The third window shape of the measured unit-availability family (M-2 of the
MISO price-formation lane, ``docs/handoffs/miso-price-formation-design-
2026-07.md`` §3, guards frozen there; registry adjudications in
``docs/handoffs/miso-maxgen-registry-findings-2026-07.md``): per-unit MW
reductions revealed by each unit's own CAMPD trace inside the ISO's
*declared* capacity-emergency windows (the ``maxgen-events`` registry,
``data/raw/maxgen-events/<iso>/``). Emits
``data/raw/campd-unit-outages-maxgen-<ISO>.csv``, consumed by
:func:`market_sim.data.outages.unit_outage_maxgen_derate_factors` under
``ScenarioConfig.unit_outage_maxgen_events`` (tier 3, default off).

**Why only inside declared windows.** The raw "missing capability" gap has NO
identification: hot non-event control days measure MORE invisible capability
than event days (design §2a — Jul 14-15 2025: 7.91 GW vs 5.43 at the Jul 28-29
peak), because on a slack day most absence is economics. Only inside a
declared emergency window — where the instrument plus deep in-merit prices
guarantee an available unit runs — is absence evidence of unavailability.
That is why this is a registry-scoped overlay, never a general detector, and
why it is CLASS-AGNOSTIC (the only channel that can carry the CT/CC leg: the
std extract's 5-day floor and the short channel's coal-only CF >= 0.55 guard
exclude it by design).

Frozen identification guards (design §3/M-2 — all measured; no model,
price-residual, or tuning input):

1. **Window scope:** derates exist only within registry windows, clipped to
   the declared start/end (hour-granular; overlapping/contiguous qualifying
   windows of the same declared region merge into one event block so overlap
   hours never double-count).
2. **In-merit certificate:** a window qualifies only where the measured DA
   hub LMP for the declared region's hubs exceeds
   :data:`IN_MERIT_THRESHOLD_USD` ($150/MWh) for >=
   :data:`MIN_CERTIFICATE_HOURS` (2) distinct window hours. $150 is a
   conservative in-merit certificate, not a tuned scalar; the design's claim
   that any value in [$120, $200] selects the same windows holds for every
   window it knew about, but the Aug-26-2024 Max Gen Warning found at M-1
   peaks at $169 — thresholds above $169 would drop it (a measured fact about
   a declared, Tier-0/1-priced emergency whose in-merit depth is genuinely
   shallower than the 2023/2025 events; recorded per the registry-findings
   memo §2, not retuned). Measured at derivation 2026-07-16: the low end of
   the band is also not fully flat — at $120 the 2023 pre-event Alert (max
   $134, slack at $150) would enter. Both facts are recorded, and the frozen
   $150 stands. The script recomputes and prints this sensitivity at every
   derivation.
3. **Capability basis:** unit capability = max CAMPD gross load in a
   ±:data:`CAPABILITY_WINDOW_DAYS`-day (45) window centered on the event
   block (seasonal-honest; month-basis 9.07 vs year-basis 14.45 GW invisible
   for Jan-2024 in the design's recompute — the ±45d basis pins capability to
   season-adjacent evidence). Derate = capability − the unit's best
   event-window hour, floored at 0: crediting the best hour makes reserve
   holdback invisible to the measure — a unit that touched capability inside
   the window is not derated. Gross-load basis throughout (capability and
   best-hour on the same CAMPD gross series); the std extract's CC steam
   augmentation is deliberately NOT applied — the frozen guard is stated on
   gross, and folding steam into the difference would inflate the channel
   beyond the design's pre-registered event sizes (conservative for CC CTs).
   **F3 fallback (pre-declared):** if the ±45d vs event-month capability
   basis changes an event block's total derate GW by more than
   :data:`F3_BASIS_RATIO` (2x), the block freezes to the SMALLER basis and
   the choice is recorded in the ``capability_basis`` column.
4. **Disjointness:** a unit whose std (>= 5-day) or short (< 5-day) extract
   already covers any hour of the event block is excluded from that block
   (its absence is already represented); zero same-unit overlaps are
   ASSERTED on the emitted rows.
5. **No control-day screen.** The design §2a control screen is Phase-A
   identification evidence, not a derivation input — inside a declared,
   in-merit-certified window the absence IS the measurement, and a control
   screen would wrongly discard true peaker freeze-offs (a peaker idle on a
   mild control day is economics, not health).

Rule-12 triple: *driver* = the ISO's own declared emergency-procedure
instruments (per-event primary provenance in the registry) + each unit's own
CAMPD trace inside them; *window* = exactly the declared windows (D-4 binds
outside a registry window is a bug by definition); *forward story* =
availability-event overlay, backcast/calibration only — the registry +
derates regenerate from each new CAMPD/declaration vintage, and a forecast
year carries the class outage-rate machinery instead.

Clock convention (CORRECTED 2026-09-04, miso-210): MISO declares its windows
in EST (Tariff Module A; the registry stores UTC converted from declared
EST), but the MODEL clock the emitted ``window_start``/``window_end`` are
consumed on is CST hour-beginning — measured by miso-208 with two r = 1.000
witnesses. The registry is therefore placed through the SAME loader and
constant the tier-pricing consumer uses (:data:`MODEL_TZ`, mirroring
``maxgen_events.MODEL_TZ_BY_ISO``), and the DA hub certificate record
(``he01``-``he24`` hour-ending EST) is shifted by the same hour
(:data:`DA_HUB_EST_TO_MODEL_HOURS`) so guard 2 compares the same physical
hours. Until this repair the deriver converted to EST and every emitted
window landed one hour LATE on the model clock (and the 2021/2022 registry
rows landed 2026-07-31 had made the deriver unrunnable, see ``main``). The
CAMPD grids stamp plant local standard time: on the corrected placement the
<= 1 h skew sits on the ISO's EST-minority plants (IN/MI/KY) rather than the
CST majority, inherited from the std/short extract family and made robust by
the best-event-hour credit — named, not repaired here.

Usage::

    python scripts/data/derive_campd_maxgen_outages.py --iso MISO

Reads only ``data/raw`` (+ the curated registry partition, regenerating it
from raw when absent); idempotent.
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

from market_sim.config.paths import EIA_860_DIR, RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.maxgen_events import (  # noqa: E402
    MODEL_TZ_BY_ISO,
    load_maxgen_registry_model_clock,
)
from market_sim.data.outages import (  # noqa: E402
    _iso_plant_capacity,
    unit_outage_csv_for_iso,
    unit_outage_maxgen_csv_for_iso,
    unit_outage_short_csv_for_iso,
)
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    _load_unit_year,
    _resolve_unit_group,
    _unit_year_grid,
    build_capacity_index,
    unit_capacity_mw,
)

# --- Frozen identification constants (design §3/M-2; cited in module doc) ---

# Guard 2: the DA in-merit certificate — far above any in-fleet thermal SRMC.
IN_MERIT_THRESHOLD_USD: float = 150.0
# Guard 2: distinct window hours that must clear the threshold.
MIN_CERTIFICATE_HOURS: int = 2
# The design's stated insensitivity band for the certificate (checked and
# printed at every derivation; see module docstring for the Aug-2024 caveat).
CERT_SENSITIVITY_BAND: tuple[float, float] = (120.0, 200.0)
# Guard 3: half-width (days) of the capability window centered on the event.
CAPABILITY_WINDOW_DAYS: int = 45
# F3 fallback: basis-instability trigger on an event block's total derate.
F3_BASIS_RATIO: float = 2.0

# The MODEL clock the emitted windows are consumed on — the SAME constant the
# tier-pricing consumer reads (``maxgen_events.MODEL_TZ_BY_ISO``), so the two
# armed consumers can never drift apart again. MISO: ``Etc/GMT+6`` = CST
# hour-beginning, MEASURED (miso-208, two r = 1.000 witnesses). The registry's
# endpoints are declared in EST and converted from UTC by the shared loader;
# until miso-210 this constant was ``Etc/GMT+5`` (EST) and every window
# landed one hour LATE on the model clock.
MODEL_TZ: str = MODEL_TZ_BY_ISO["MISO"]

# The DA hub record (``he01``-``he24``) is hour-ENDING EST: ``he13`` is the EST
# hour-beginning 12:00 interval, which on the CST model clock is 11:00. Shift
# the certificate record by the same hour the registry conversion applies, so
# guard 2 compares exactly the physical hours it always did (the miso-210
# S-3 certificate-invariance line: n_cert per registry row is unchanged).
DA_HUB_EST_TO_MODEL_HOURS: int = -1

# DA hub record per declared region (design guard 2 "region-scoped hubs";
# the North/South hub split of the design §1 July-2025 decomposition).
REGION_HUBS: dict[str, tuple[str, ...]] = {
    "midwest": ("ILLINOIS.HUB", "INDIANA.HUB", "MICHIGAN.HUB", "MINN.HUB"),
    "south": ("ARKANSAS.HUB", "LOUISIANA.HUB", "MS.HUB", "TEXAS.HUB"),
    "footprint": (
        "ARKANSAS.HUB",
        "ILLINOIS.HUB",
        "INDIANA.HUB",
        "LOUISIANA.HUB",
        "MICHIGAN.HUB",
        "MINN.HUB",
        "MS.HUB",
        "TEXAS.HUB",
    ),
}

# Model zones inside each declared region (units are derated only where the
# declaring instrument + in-merit certificate apply). MISO-South is LRZ 8-10;
# every other model zone is the Midwest subregion.
_SOUTH_ZONES: frozenset[str] = frozenset({"MISO-South"})


def _zone_in_region(zone: str, region: str) -> bool:
    """Return whether a model zone is inside a declared region scope."""
    if region == "footprint":
        return True
    if region == "south":
        return zone in _SOUTH_ZONES
    if region == "midwest":
        return zone not in _SOUTH_ZONES
    raise ValueError(f"unknown declared region {region!r}")


def load_registry_model_clock(iso: str) -> pd.DataFrame:
    """Return the ISO's maxgen-events registry on the naive MODEL clock.

    Delegates to :func:`market_sim.data.maxgen_events.load_maxgen_registry_model_clock`
    — the tier-pricing consumer's own loader (curated partition through the
    frozen ``clean_io`` seam, regenerated from ``data/raw`` when absent;
    ``start_model`` hour-floored, ``end_model_excl`` hour-ceiled half-open) —
    so the derate windows and the tier windows are placed by ONE function.
    """
    return load_maxgen_registry_model_clock(iso)


def da_hub_path(iso: str, year: int) -> Path:
    """Return the year's gzip DA hub LMP record path (may not exist).

    2023-2025 ship as one gzip yearly file. Other years ship as ``_p<NN>.csv``
    ~7-day chunks (``data/raw/lmp-data/MISO/README.md``) carrying the SAME
    verbatim columns (``date,node,type,value,he01..he24``); see
    :func:`da_hub_paths`, which reads either layout.
    """
    return RAW_DATA_DIR / "lmp-data" / iso / f"{iso.lower()}_hub_lmp_{year}_da.csv.gz"


def da_hub_paths(iso: str, year: int) -> list[Path]:
    """Return the staged DA hub LMP file(s) for ``year``: the gzip, else the chunks.

    R-MISO (2026-09-24, AUDIT-backcast-inputs-860-heatrate-outage §5.3.3;
    FINDING-f2-campd-outage-coverage §2 "Maxgen ... spans 2023-2025 only ->
    R-MISO"): the chunk layout is the same verbatim hub rows the gzip carries
    (``derive_miso_hub_lmp._staged_paths`` reads both), so it is as much a
    certificate source as the gzip. The former gzip-only reader dropped the
    registry's 2021 (Uri) and 2022 declarations as "uncertifiable" on the
    stated ground that they sat outside the 2023-2025 training span — a ground
    that lapsed with ``[R-HOLDOUT]``'s removal (2026-09-09) while the MISO
    keeper solves both years. Prefers the gzip when both exist.
    """
    gz = da_hub_path(iso, year)
    if gz.exists():
        return [gz]
    return sorted(gz.parent.glob(f"{iso.lower()}_hub_lmp_{year}_da_p??.csv"))


def da_hub_long_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape a DA hub LMP record to a wide ``ts x hub`` frame on the MODEL clock.

    ``he01``-``he24`` are hour-ending EST labels -> 0-based EST hour-beginning
    timestamps, then shifted by :data:`DA_HUB_EST_TO_MODEL_HOURS` onto the CST
    model clock (the same hour the registry conversion applies). Pure, so the
    placement is unit-testable on a synthetic row.
    """
    df = df[df["value"] == "LMP"]
    he_cols = [f"he{h:02d}" for h in range(1, 25)]
    long = df.melt(
        id_vars=["date", "node"], value_vars=he_cols, var_name="he", value_name="lmp"
    )
    long["hour"] = long["he"].str.slice(2).astype(int) - 1 + DA_HUB_EST_TO_MODEL_HOURS
    long["ts"] = pd.to_datetime(long["date"]) + pd.to_timedelta(long["hour"], unit="h")
    return long.pivot_table(index="ts", columns="node", values="lmp")


def load_da_hub_wide(iso: str, year: int) -> pd.DataFrame:
    """Return the year's DA hub LMP as a wide ``ts x hub`` frame (MODEL clock).

    Reads the committed record (gzip yearly file or ``_p<NN>`` chunks,
    :func:`da_hub_paths`) and places it through :func:`da_hub_long_to_wide`.
    """
    return da_hub_long_to_wide(
        pd.concat([pd.read_csv(p) for p in da_hub_paths(iso, year)], ignore_index=True)
    )


def certificate_hours(
    hub_wide: pd.DataFrame,
    region: str,
    start_model: pd.Timestamp,
    end_model_excl: pd.Timestamp,
    threshold: float = IN_MERIT_THRESHOLD_USD,
) -> int:
    """Count distinct window hours whose region-hub max DA LMP exceeds ``threshold``."""
    hubs = [h for h in REGION_HUBS[region] if h in hub_wide.columns]
    win = hub_wide.loc[
        (hub_wide.index >= start_model) & (hub_wide.index < end_model_excl), hubs
    ]
    if win.empty:
        return 0
    return int((win.max(axis=1) > threshold).sum())


def merge_event_blocks(qualified: pd.DataFrame) -> list[dict]:
    """Merge overlapping/contiguous qualifying windows into event blocks.

    Same declared region only (the unit scope differs by region). Guard 1's
    clipping is preserved — a block is the union of declared windows, never
    wider — and merging keeps overlap hours (Jul-28-2025 carries a Capacity
    Advisory, a Max Gen Alert and the Jul-29 Warning simultaneously) from
    double-counting a unit's derate. Returns blocks sorted by start:
    ``{region, start, end, levels, n_windows}``.
    """
    blocks: list[dict] = []
    for region, sub in qualified.groupby("region"):
        sub = sub.sort_values("start_model")
        cur: dict | None = None
        for r in sub.itertuples(index=False):
            if cur is not None and r.start_model <= cur["end"]:
                cur["end"] = max(cur["end"], r.end_model_excl)
                cur["levels"].append(str(r.level))
                cur["n_windows"] += 1
            else:
                if cur is not None:
                    blocks.append(cur)
                cur = {
                    "region": str(region),
                    "start": r.start_model,
                    "end": r.end_model_excl,
                    "levels": [str(r.level)],
                    "n_windows": 1,
                }
        if cur is not None:
            blocks.append(cur)
    return sorted(blocks, key=lambda b: b["start"])


def capability_and_derate(
    gross: np.ndarray,
    clock: pd.DatetimeIndex,
    block_start: pd.Timestamp,
    block_end_excl: pd.Timestamp,
    basis: str = "pm45d",
    window_days: int = CAPABILITY_WINDOW_DAYS,
) -> tuple[float, float, float]:
    """Return ``(capability_mw, best_window_mw, derate_mw)`` for one unit.

    ``basis``: ``"pm45d"`` = max gross in the ±``window_days`` window centered
    on the block midpoint (guard 3, the frozen default); ``"event_month"`` =
    max gross in the block's starting calendar month (the F3 comparison
    basis). Both clip to the CAMPD clock (publication horizon / year edges).
    Derate = capability − best in-block hour, floored at 0 (best-hour credit:
    a unit that touched capability inside the block is not derated).
    """
    win_mask = (clock >= block_start) & (clock < block_end_excl)
    if basis == "pm45d":
        mid = block_start + (block_end_excl - block_start) / 2
        lo = mid - pd.Timedelta(days=window_days)
        hi = mid + pd.Timedelta(days=window_days)
        cap_mask = (clock >= lo) & (clock < hi)
    elif basis == "event_month":
        cap_mask = (clock.year == block_start.year) & (clock.month == block_start.month)
    else:
        raise ValueError(f"unknown capability basis {basis!r}")
    capability = float(gross[cap_mask].max()) if cap_mask.any() else 0.0
    best = float(gross[win_mask].max()) if win_mask.any() else 0.0
    return capability, best, max(0.0, capability - best)


def _load_covered_windows(
    iso: str, mixed_gas_routing: bool = False
) -> dict[tuple[int, str], list[tuple]]:
    """Return std + short extract windows keyed ``(facility_id, unit_id)``.

    Day-grain rows become half-open hour intervals
    ``[outage_start 00:00, outage_end + 1 day)`` — the same reconstruction the
    overlay loaders use — for guard 4 (disjointness): a unit already covered
    on any block hour is excluded from that block.

    ``mixed_gas_routing`` (miso-200) reads the std extract the ARMED run will
    itself read, so the guard is checked against the same file the overlay
    loads. The keys here are ``(facility_id, unit_id)`` and the routing repair
    changes neither the rows nor their windows, so the covered set is identical
    either way -- the flag is threaded for wiring consistency, not to change a
    verdict.
    """
    covered: dict[tuple[int, str], list[tuple]] = {}
    for path in (
        unit_outage_csv_for_iso(iso, mixed_gas_routing),
        unit_outage_short_csv_for_iso(iso),
    ):
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
        for r in df.itertuples(index=False):
            covered.setdefault((int(r.facility_id), str(r.unit_id)), []).append(
                (r.outage_start, r.outage_end + pd.Timedelta(days=1))
            )
    return covered


def _overlaps(
    covered: dict[tuple[int, str], list[tuple]],
    facility_id: int,
    unit_id: object,
    start: pd.Timestamp,
    end_excl: pd.Timestamp,
) -> bool:
    """Return whether the unit has any std/short coverage inside the block."""
    for lo, hi in covered.get((int(facility_id), str(unit_id)), ()):
        if lo < end_excl and hi > start:
            return True
    return False


def assert_disjoint(rows: list[dict], covered: dict[tuple[int, str], list[tuple]]):
    """Guard 4: assert zero same-unit overlaps between emitted rows and std/short."""
    for row in rows:
        key = (int(row["facility_id"]), str(row["unit_id"]))
        s = pd.Timestamp(row["window_start"])
        e = pd.Timestamp(row["window_end"])
        for lo, hi in covered.get(key, ()):
            assert not (lo < e and hi > s), (
                f"maxgen derate for {key} [{s}..{e}) overlaps a std/short "
                f"window [{lo}..{hi}) — guard 4 (disjointness) violated"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument(
        "--eia860",
        default=str(EIA_860_DIR / "eia860_generators.parquet"),
        help="EIA-860 generator parquet, for per-unit nameplate capacity.",
    )
    ap.add_argument(
        "--mixed-gas-routing",
        action="store_true",
        help=(
            "miso-200: skip _resolve_unit_group's fac_group short-circuit at a "
            "facility carrying two or more model gas bins (see that function's "
            "docstring). Writes the '-unitroute-' companion so the incumbent "
            "extract is never overwritten."
        ),
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output CSV; defaults to data/raw/campd-unit-outages-maxgen-{ISO}.csv.",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    if args.out:
        out_path = Path(args.out)
    elif args.mixed_gas_routing:
        # Constructed EXPLICITLY, never via the reader helper: that helper falls
        # back to the incumbent path when the companion does not yet exist, so
        # using it here would OVERWRITE the incumbent extract on the very first
        # derivation (miso-200).
        out_path = unit_outage_maxgen_csv_for_iso(iso).with_name(
            f"campd-unit-outages-maxgen-unitroute-{iso}.csv"
        )
    else:
        out_path = unit_outage_maxgen_csv_for_iso(iso)

    ev = load_registry_model_clock(iso)
    # Guard 2 needs the year's DA hub record. Registry years without one (the
    # 2021/2022 rows landed 2026-07-31 under the rule-22 intake channel; their
    # hub record is absent or staged as unreadable chunks) cannot be
    # certified and are dropped HERE, with notice -- they are outside the
    # 2023-2025 training span in any case, and a window that cannot be
    # certified never emits a derate (miso-210: the deriver could not run at
    # all once those rows existed, so the committed extract had gone
    # unreproducible).
    years_all = sorted(int(y) for y in ev["start_model"].dt.year.unique())
    years = [y for y in years_all if da_hub_paths(iso, y)]
    skipped = sorted(set(years_all) - set(years))
    if skipped:
        print(
            f"registry years with no DA hub record, dropped (uncertifiable): "
            f"{skipped} -> {int(ev['start_model'].dt.year.isin(skipped).sum())} rows"
        )
        ev = ev[~ev["start_model"].dt.year.isin(skipped)].reset_index(drop=True)
    hub_by_year = {y: load_da_hub_wide(iso, int(y)) for y in years}

    # Guard 2: in-merit certificate per registry row, plus the stated
    # sensitivity check across CERT_SENSITIVITY_BAND (printed, never tuned).
    print("in-merit certificate (guard 2, region-scoped DA hub record):")
    n_cert, lo_flip, hi_flip = [], [], []
    lo_t, hi_t = CERT_SENSITIVITY_BAND
    for r in ev.itertuples(index=False):
        hub = hub_by_year[r.start_model.year]
        n = certificate_hours(hub, r.region, r.start_model, r.end_model_excl)
        n_lo = certificate_hours(hub, r.region, r.start_model, r.end_model_excl, lo_t)
        n_hi = certificate_hours(hub, r.region, r.start_model, r.end_model_excl, hi_t)
        n_cert.append(n)
        q = n >= MIN_CERTIFICATE_HOURS
        if (n_lo >= MIN_CERTIFICATE_HOURS) != q:
            lo_flip.append(str(r.level))
        if (n_hi >= MIN_CERTIFICATE_HOURS) != q:
            hi_flip.append(str(r.level))
        print(
            f"  {str(r.level):22s} {str(r.region):9s} "
            f"{r.start_model} .. {r.end_model_excl}  hours>${IN_MERIT_THRESHOLD_USD:.0f}"
            f"={n:3d}  {'QUALIFIES' if q else 'excluded (slack)'}"
        )
    ev = ev.assign(n_cert=n_cert)
    print(
        f"certificate sensitivity over ${lo_t:.0f}-${hi_t:.0f}: "
        f"{'no window flips' if not (lo_flip or hi_flip) else ''}"
        f"{'flip at low end: ' + ', '.join(lo_flip) if lo_flip else ''}"
        f"{(' | ' if lo_flip and hi_flip else '')}"
        f"{'flip at high end: ' + ', '.join(hi_flip) if hi_flip else ''}"
    )

    qualified = ev[ev["n_cert"] >= MIN_CERTIFICATE_HOURS]
    blocks = merge_event_blocks(qualified)
    print(f"\n{len(qualified)}/{len(ev)} windows qualify -> {len(blocks)} event blocks")

    # Fleet maps: model zone + (plant_code, plant_group) capacity denominator.
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

    iso_config = get_iso_config(iso)
    fleet = load_fleet_from_csv(iso, iso_config) + load_retired_within_window(
        iso, iso_config
    )
    zone_by_code: dict[int, str] = {}
    groups_by_code: dict[int, set[str]] = {}
    group_by_code: dict[int, str] = {}
    name_by_code: dict[int, str] = {}
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        zone_by_code.setdefault(code, g.zone)
        group_by_code[code] = g.plant_group
        name_by_code[code] = g.name
        groups_by_code.setdefault(code, set()).add(g.plant_group)
    plant_cap = _iso_plant_capacity(iso)

    exact, by_digits = build_capacity_index(Path(args.eia860))
    covered = _load_covered_windows(iso, bool(args.mixed_gas_routing))

    # Blocks by calendar year (all current blocks are within-year; a block
    # straddling Dec 31 would clip at the CAMPD year files' edges).
    blocks_by_year: dict[int, list[dict]] = {}
    for b in blocks:
        blocks_by_year.setdefault(int(b["start"].year), []).append(b)

    rows: list[dict] = []
    excluded_covered = 0
    for year, yblocks in sorted(blocks_by_year.items()):
        # Per-unit gross grids for every fleet facility in the ISO's states.
        for state in campd.states_for_iso(iso):
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            horizon_end = df["date"].max() + pd.Timedelta(hours=23)
            clock = pd.date_range(f"{year}-01-01", horizon_end, freq="h")
            df["facilityId"] = [
                campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
                for f, u in zip(df["facilityId"].astype(int), df["unitId"].astype(str))
            ]
            for fac_id, fac in df.groupby("facilityId", observed=True):
                code = int(fac_id)
                zone = zone_by_code.get(code)
                if zone is None:
                    continue  # not a model fleet plant
                fac_groups = groups_by_code.get(code, set())
                fac_group = group_by_code.get(code)
                units = {
                    uid: _unit_year_grid(u, year, end=horizon_end)
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                unit_is_coal = {
                    uid: str(u["primaryFuelInfo"].iloc[0]).strip().lower()
                    in ("coal", "coal refuse")
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                unit_type = {
                    uid: str(u["unitType"].iloc[0])
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # The unit's OWN CEMS-reported primary fuel, for the liquid-fuel
                # combustion-turbine guard in :func:`_resolve_unit_group`.
                unit_fuel = {
                    uid: str(u["primaryFuelInfo"].iloc[0])
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                for uid, gross in units.items():
                    peak = float(gross.max())
                    if peak <= 0.0:
                        continue  # no gross basis this year
                    ugroup = _resolve_unit_group(
                        unit_is_coal[uid],
                        unit_type.get(uid, ""),
                        fac_groups,
                        fac_group,
                        unit_fuel.get(uid, ""),
                        mixed_gas_routing=bool(args.mixed_gas_routing),
                    )
                    if (code, ugroup) not in plant_cap:
                        continue  # routed to a bin absent from the model fleet
                    detect_cap, _derate_cap, cap_src = unit_capacity_mw(
                        code, uid, exact, by_digits, peak
                    )
                    for b in yblocks:
                        if not _zone_in_region(zone, b["region"]):
                            continue
                        if _overlaps(covered, code, uid, b["start"], b["end"]):
                            excluded_covered += 1
                            continue  # guard 4: std/short already covers it
                        capability, best, derate = capability_and_derate(
                            gross, clock, b["start"], b["end"], basis="pm45d"
                        )
                        cap_m, best_m, derate_m = capability_and_derate(
                            gross, clock, b["start"], b["end"], basis="event_month"
                        )
                        if derate <= 0.0 and derate_m <= 0.0:
                            continue
                        rows.append(
                            {
                                "facility_name": name_by_code.get(code, ""),
                                "facility_id": code,
                                "unit_id": uid,
                                "plant_group": ugroup,
                                "zone": zone,
                                "region": b["region"],
                                "levels": "+".join(b["levels"]),
                                "window_start": b["start"].strftime("%Y-%m-%d %H:%M"),
                                "window_end": b["end"].strftime("%Y-%m-%d %H:%M"),
                                "capability_mw": round(capability, 1),
                                "capability_month_mw": round(cap_m, 1),
                                "capability_basis": "pm45d",
                                "best_window_mw": round(best, 1),
                                "derate_mw": round(derate, 1),
                                "derate_month_mw": round(derate_m, 1),
                                "nameplate_mw": round(detect_cap, 1),
                                "capacity_source": cap_src,
                                "plant_capacity_mw": round(
                                    plant_cap[(code, ugroup)], 1
                                ),
                            }
                        )

    # F3 (pre-declared): per event block, compare the two capability bases on
    # the block's TOTAL derate; > F3_BASIS_RATIO instability freezes the block
    # to the SMALLER basis and records it.
    frame = pd.DataFrame(rows)
    if not frame.empty:
        for (ws, region), idx in frame.groupby(
            ["window_start", "region"]
        ).groups.items():
            sub = frame.loc[idx]
            tot45 = float(sub["derate_mw"].sum())
            totm = float(sub["derate_month_mw"].sum())
            hi, lo = max(tot45, totm), min(tot45, totm)
            label = f"{ws} ({region})"
            if lo > 0 and hi / lo > F3_BASIS_RATIO and totm < tot45:
                # Freeze to the smaller (event-month) basis for this block.
                frame.loc[idx, "derate_mw"] = frame.loc[idx, "derate_month_mw"]
                frame.loc[idx, "capability_mw"] = frame.loc[idx, "capability_month_mw"]
                frame.loc[idx, "capability_basis"] = "event_month_f3"
                print(
                    f"F3 ENGAGED {label}: pm45d {tot45 / 1e3:.2f} GW vs "
                    f"event-month {totm / 1e3:.2f} GW (> {F3_BASIS_RATIO}x) — "
                    "frozen to the smaller (event-month) basis"
                )
            else:
                print(
                    f"F3 check {label}: pm45d {tot45 / 1e3:.2f} GW / "
                    f"event-month {totm / 1e3:.2f} GW — stable, pm45d kept"
                )
        frame = frame[frame["derate_mw"] > 0.0]

    out_rows = frame.to_dict("records") if not frame.empty else []
    assert_disjoint(out_rows, covered)

    cols = [
        "facility_name",
        "facility_id",
        "unit_id",
        "plant_group",
        "zone",
        "region",
        "levels",
        "window_start",
        "window_end",
        "capability_mw",
        "capability_month_mw",
        "capability_basis",
        "best_window_mw",
        "derate_mw",
        "derate_month_mw",
        "nameplate_mw",
        "capacity_source",
        "plant_capacity_mw",
    ]
    out = pd.DataFrame(out_rows, columns=cols).sort_values(
        ["window_start", "facility_id", "unit_id"]
    )
    out.to_csv(out_path, index=False)
    print(
        f"\nwrote {len(out)} maxgen derate rows to {out_path} "
        f"({excluded_covered} unit-block pairs excluded as std/short-covered)"
    )
    if not out.empty:
        summary = (
            out.assign(gw=out["derate_mw"] / 1e3)
            .groupby(["window_start", "region", "plant_group"])["gw"]
            .sum()
            .round(2)
        )
        print("\nderate GW by block x class:")
        print(summary.to_string())
        blk = out.groupby(["window_start", "region"])["derate_mw"].sum() / 1e3
        print("\nblock totals (GW):")
        print(blk.round(2).to_string())


if __name__ == "__main__":
    main()
