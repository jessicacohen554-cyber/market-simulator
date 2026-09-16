"""EIA-930 measured-actuals benchmark loaders for :mod:`market_sim.data.eia930`.

The per-fuel hourly benchmark series the calibration report scores against
(``load_eia_hourly_benchmark`` and the ERCOT-specific fossil / nuclear /
renewable / battery / other readers), plus the normalized generation-profile
distributions. Split out of ``data/eia_loader.py`` as pure code motion (W-D2,
2026-07-20).

:func:`_screen_fuel_spike_columns` (lane SPP-41, 2026-09-07) repairs EIA-930
unit-slip hours in the per-fuel ``NG: <CODE>`` columns. It is defined here but
APPLIED at the frame-construction seam in :mod:`~market_sim.data.eia930.frames`
(lane NWPP-37, 2026-09-16), so every reader of an EIA-930 hourly frame gets the
repaired columns — not just the readers in this module, which is all the three
former call sites reached. The one application left here is
:func:`load_eia_hourly_benchmark`, which reads the parquet itself rather than
through ``frames``. That function's own docstring lists the full seam.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

from .demand import _DEMAND_SPIKE_THRESHOLD
from .frames import (
    DATA_DIR,
    _GENERATION_PROFILES_FILE,
    _ISO_LOCAL_TZ,
    _ISO_TO_HOURLY_BA,
    _eia_hourly_frame_filled,
    _eia_hourly_path,
    _ercot_hourly_frame,
    _filter_iso_year,
    _read_clean_iso_year,
    _use_clean,
)

logger = logging.getLogger(__name__)


# Clean ``generation`` fuel bucket -> model benchmark series name, restricted to
# the buckets that map 1:1 onto a single EIA-930 ``NG: <CODE>`` column (and so
# equal the raw benchmark within tolerance). The storage family (clean ``storage``
# folds EIA BAT/PS/UES/...; the benchmark keeps ``battery`` / ``pumped_storage``
# split) and the catch-all ``other`` / ``geothermal`` buckets aggregate
# differently and are deliberately not overridden from clean here.
_CLEAN_GEN_FUEL_TO_BENCHMARK: dict[str, str] = {
    "coal": "coal",
    "gas": "gas",
    "nuclear": "nuclear",
    "hydro": "hydro",
    "solar": "solar",
    "wind": "wind",
    "oil": "oil",
}


def _clean_generation_by_fuel(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return clean-backed per-fuel hourly generation (MW), keyed by benchmark name.

    Reshapes the long-form clean ``generation`` (one row per ``(zone, fuel,
    hour)``) into the wide per-fuel arrays the model benchmark expects, summing
    the clean zones per ``(fuel, hour)`` and placing each fuel on the model's
    8760-hour clock. Only the buckets that map 1:1 onto a single EIA-930 fuel
    column (:data:`_CLEAN_GEN_FUEL_TO_BENCHMARK`) are returned. Per-fuel NaN
    holes are gap-filled exactly as :func:`load_eia_hourly_benchmark` does.
    Returns ``None`` when the ISO is unsupported, the partition is absent, or the
    reconstructed grid is not a clean full year.
    """
    if iso not in _ISO_LOCAL_TZ:
        return None
    rows = _read_clean_iso_year("generation", iso, year)
    if rows is None:
        return None
    wide = rows.pivot_table(
        index="interval_start_utc",
        columns="fuel",
        values="generation_mw",
        aggfunc="sum",
    ).sort_index()
    if wide.shape[0] != HOURS_PER_YEAR:
        return None
    out: dict[str, np.ndarray] = {}
    for clean_fuel, bench_name in _CLEAN_GEN_FUEL_TO_BENCHMARK.items():
        if clean_fuel not in wide.columns:
            continue
        series = wide[clean_fuel].interpolate().bfill().ffill().to_numpy(dtype=float)
        if np.isnan(series).any():
            continue
        out[bench_name] = series
    return out or None


def load_ercot_renewable_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly wind and solar net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` extract — the same chronological
    source as the demand and interchange series — so renewable profiles
    share the calibration's time index. Returns ``{"wind": ..., "solar":
    ...}`` of ``(HOURS_PER_YEAR,)`` arrays, or ``None`` when the file, the
    year, or the per-source generation columns are unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("wind", "NG: WND"), ("solar", "NG: SUN")):
        if column not in frame.columns:
            return None
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            return None
        out[fuel] = series.to_numpy(dtype=float)
    return out


# EIA-930 ``<BA> hourly`` per-fuel net-generation columns, mapped to the
# model's benchmark series names. Gas is the whole gas fleet (CC + CT + ST),
# the counterpart to the model's summed gas dispatch. The storage rows are
# *net* series (positive = discharging, negative = charging) and only appear
# in extract vintages whose BA reports the EIA-930 storage split (``BAT`` /
# ``PS`` fuel codes; the current CISO extract predates the split and folds
# batteries into the legacy ``OTH`` category) — absent columns are skipped
# below, so the battery benchmark wires itself in automatically once a
# regenerated extract carries them.
_EIA930_BENCHMARK_COLUMNS: tuple[tuple[str, str], ...] = (
    ("coal", "NG: COL"),
    ("gas", "NG: NG"),
    ("nuclear", "NG: NUC"),
    ("wind", "NG: WND"),
    ("solar", "NG: SUN"),
    ("oil", "NG: OIL"),
    ("hydro", "NG: WAT"),
    # "Other Fuel Sources" (geothermal / biomass / process gas reported outside
    # the NG: NG aggregate). Threaded through so the per-class benchmark can tell
    # how much geothermal+biomass a BA correctly reports here vs silently folds
    # into its "Natural Gas" cell — the partial-fold-in deflation in
    # render_calibration_html.reconcile_vintage_classes (generalizes the CAISO
    # allowlist to MISO and any other partial-fold BA).
    ("other", "NG: OTH"),
    ("battery", "NG: BAT"),
    ("pumped_storage", "NG: PS"),
)

# Storage net-generation series (battery / pumped storage) are the only EIA-930
# fuel rows a BA *begins reporting partway through* a year: the BAT/PS breakout
# is added to a BA's filing on a specific month (e.g. ISNE first reports NG: PS
# in Nov 2024 — Jan–Oct are blank), so a year can carry only a few months of
# data. Unlike the always-reported thermal/VRE rows, a partial storage series is
# NOT a full-year observation: summing it gives a 2-month throughput that would
# read as a spurious annual under/over-count against the model's full 8760 hours.
# A storage series whose raw coverage falls below this fraction is therefore
# treated as not-yet-reporting for the year and dropped (the C5b throughput
# criterion then stays SKIPPED rather than scoring a partial vintage). This is a
# coverage gate on the *measured input*, not a residual-tuned knob; it
# generalises the existing all-NaN guard (a fully-blank series, e.g. ISNE PS
# 2023, is the coverage=0 limit of the same rule).
_STORAGE_BENCHMARK_SERIES: frozenset[str] = frozenset({"battery", "pumped_storage"})
_STORAGE_MIN_COVERAGE_FRAC: float = 0.5

# EIA-930 per-fuel filing gaps that arrive as an exact 0.0 rather than a blank.
# The loader's gap machinery below only guards NaN, so a zero-coded gap reads as
# a measured "the fleet produced nothing this hour" and silently DEFLATES the
# annual benchmark — which then reads as the model over-running that class.
#
# Registry keyed by EIA-930 BA code -> the columns whose exact zeros are filing
# gaps. An entry belongs here ONLY when a fleet-wide zero is physically
# impossible for that BA's fleet AND an independent ISO posting shows material
# generation in the very hours the 930 series reads 0. It is a data-quality
# statement about the source extract (rule 14 — prefer the accurate measurement),
# not a tunable: nothing here responds to a residual, and the repaired series is
# validated against the independent posting, not against any model output.
#
# NYIS ``NG: NUC`` (measured 2026-07-24, this file's only entry):
#   New York's nuclear fleet is four baseload units at three sites (Ginna,
#   Nine Mile Point 1 & 2, FitzPatrick; ~3.4 GW). The NYIS extract reads exactly
#   0 MW for 1,275 h (2023, across 56 distinct days incl. one 1,179-h block),
#   390 h (2024) and 118 h (2025). NYISO's own hourly fuel-mix posting
#   (data/raw/NYISO/fuel-mix/) reports a MINIMUM of 1,989 MW of nuclear over
#   2023 and never once reads 0 — so every one of those hours is a filing gap,
#   worth 3.46 / 1.12 / 0.37 TWh of benchmark deflation. Masking them and
#   letting the existing interpolation bridge them lands the annual total within
#   -0.4 % / -0.4 % / -0.7 % of the NYISO posting (from -13.0 % / -4.5 % / -2.0 %
#   raw).
#
# Deliberately NOT registered — their zeros are physically real, so masking them
# would fabricate generation: ERCO ``NG: WAT`` (a ~0.05-0.24 TWh/yr conventional
# hydro fleet that genuinely sits at 0) and ISNE ``NG: COL`` (ISO-NE coal is all
# but retired and runs only seasonally).
_ZERO_CODED_GAP_SERIES: dict[str, frozenset[str]] = {
    "NYIS": frozenset({"NG: NUC"}),
}

# ---------------------------------------------------------------------------
# EIA-930 ``NG:`` unit-slip screen — ONE mechanism at ONE seam (lane SPP-41).
#
# The factor is the demand screen's own (``eia930.demand._DEMAND_SPIKE_THRESHOLD``
# = 2.5x a robust scale statistic), bound by IMPORT rather than re-spelled so
# there is provably no second threshold (rule 19 [R-ONE-MECH]; SPP-31 §3.2).
_FUEL_SPIKE_RATIO: float = _DEMAND_SPIKE_THRESHOLD
# The scale statistic the second limb uses: the series' own 99.9th percentile,
# about the ninth-largest of 8,760 hours — a robust operating peak that a
# handful of artifact hours cannot drag up. See :func:`_screen_fuel_spike_columns`
# for why the demand screen's median basis cannot be used alone on a fuel series.
_FUEL_SPIKE_SCALE_PCT: float = 99.9
# The zero-baseline guard's rank (lane NWPP-39): the anchor above is ITSELF
# tested by the screen's own premise at the next-coarser rank. The anchor sits
# one decade of rank below the maximum (rank 1 -> rank ~9, 0.1 % of 8,760);
# the guard steps the same decade again (rank ~9 -> rank ~88, 1 %), so the
# rank is DERIVED from the anchor's, not chosen: 100 - 10 * (100 - 99.9) = 99.0
# (spelled as the literal so ``np.percentile`` sees an exact rank rather than
# the expression's float noise; the derivation is pinned by test). See
# :func:`_screen_fuel_spike_columns`, "Why a robust peak can fail to be a
# scale". No new factor: the guard's factor is :data:`_FUEL_SPIKE_RATIO`.
_FUEL_SPIKE_PLATEAU_PCT: float = 99.0
# The screen's scope is the per-fuel ``NG: <CODE>`` columns EXACTLY as card P9
# ruled (SPP addition plan §5, RULED r#2). ``Net generation`` (the ``NG`` total),
# ``Total interchange`` (``TI``) and every ``Demand`` column are outside it, and
# that exclusion is load-bearing, not cosmetic: PJM 2021's ``NG`` total carries
# three int32-overflow hours (2,147,480,064 MW at h6981-6983) whose ``NG:`` fuel
# cells are entirely ordinary, so screening the total would repair real fuel
# data and move a committed PJM block. Demand is ``eia930.demand``'s phenomenon
# (``_screen_demand_spikes`` / ``_screen_demand_dropouts``), never this one's.
_EIA930_FUEL_COLUMN_PREFIX: str = "NG: "


def _screen_fuel_spike_columns(
    frame: pd.DataFrame, *, ba_code: str, year: int
) -> pd.DataFrame:
    """Return ``frame`` with EIA-930 unit-slip hours in its ``NG:`` columns as NaN.

    **What it repairs.** The ``SWPP hourly`` extract posts ``NG: WND`` =
    3,589,445 MW at 2023-06-12 21:00 local (h3907 of the 8760 clock) — a ~100x
    unit slip against a 22,597 MW robust peak — in the same hour
    ``eia930.demand._screen_demand_spikes`` repairs the ``Demand`` column.
    Left in, it inflates SPP 2023 wind by 3.5857 TWh on EVERY consumer of the
    column: the C1/C4 benchmark (``run_calibration_full._eia930_frame_generic``
    → ``e930`` → ``bench/SPP/2023.json.gz``), the ``calibration_reference.json``
    builder, AND the model's own delivered wind profile
    (:func:`load_eia_hourly_renewable_gen` → ``renewables._eia_hourly_cf_profile``
    → the LP's wind bound; SPP-40 §4). SPP-31 screened the builder alone.

    **Where this runs (rule 19 ``[R-ONE-MECH]``).** ONE mechanism — this
    function — applied at the points where an EIA-930 hourly frame is BUILT
    from the parquet, never at a reader:

    * :func:`~market_sim.data.eia930.frames._eia_hourly_frame` (both its
      single-BA and its ``_pool_hourly_frame`` branch), which is also what
      :func:`~market_sim.data.eia930.frames._ercot_hourly_frame` and
      :func:`~market_sim.data.eia930.frames._eia_hourly_frame_filled`'s fast
      path return;
    * :func:`~market_sim.data.eia930.frames._eia_hourly_frame_filled`'s
      gap-bridging reconstruction, which reads the parquet itself;
    * :func:`load_eia_hourly_benchmark` below, which also reads the parquet
      itself — it accepts a year SHORT of 8760 and mean-pads it, a tolerance
      neither ``frames`` loader has, so it cannot be routed through them
      without changing what it returns.

    That is the whole list, and it is what makes the single-seam property
    TRUE rather than asserted. **It did not used to be.** Until lane NWPP-37
    (2026-09-16) the screen was applied at three call sites, ALL inside this
    module, while this docstring claimed "no consumer can reach an unscreened
    copy" — a claim that held only of readers in ``actuals``. Every other
    reader called ``frames._eia_hourly_frame_filled`` directly and got the raw
    columns: measured at that lane's base sha, SIX unscreened ``NG:``-column
    readers across two modules — ``envelopes``' ``measured_monthly_hydro``,
    ``_hydro_wat_month_hod``, ``measured_gas_floor_profile`` and
    ``caiso_solar_fraction``, and ``neighbor_price``'s two net-load shapes —
    so the NWPP pool's hydro budget and envelopes read the unrepaired
    ``NG: WAT`` (NWPP-32 §7 item 1). Moving the application to the
    constructors fixes that for those six and for every reader added since.

    **What this screen does NOT cover, stated rather than implied.** On a POOL
    frame (``_POOL_HOURLY_MEMBERS``) the statistics are the POOLED series', so
    a member's slip that the footprint sum dilutes below 2.5x the pool's own
    p99.9 is not flagged. Measured for NWPP ``NG: WAT`` (NWPP-37 §5): the
    pooled screen catches 2 of 4 artifact hours in 2024 and 3 of 6 in 2025 —
    the misses are NWMT hours of 17,162-32,416 MW, far above that BA's entire
    hydro fleet, which land at 1.04-1.83x the pooled anchor. Screening each
    member BEFORE the sum would catch them, but that re-bases the statistic on
    a per-member population and is a threshold question, not a seam one: on
    the same measurement it also flags PGE ``NG: OTH`` 119 MW (2023 h732) and
    NWMT ``NG: WAT`` 1,782 MW (2024 h5556), neither of which is obviously an
    artifact. Routed to the desk with that evidence; not decided here.

    **Why the demand screen's test needs a second limb here.** That screen
    flags ``x > 2.5 * median(x)``, and its own derivation says why that bar is
    valid: every legitimate demand series has ``max/median <= 2.1``. A fuel
    series has no such property — it legitimately runs from zero to nameplate,
    so its median is not its operating scale. Measured over all seven ISOs and
    2021-2025 (SPP-31 §3.1), the median test ALONE flags 4,116 MISO 2023 solar
    hours, 3,860 NEISO 2024 solar hours and 3,131 NEISO 2025 oil hours — real
    midday solar and real peaker starts — and the largest legitimate
    ``max/median`` anywhere (NEISO 2025 oil, 523x) exceeds the artifact's
    (299x), so no median-ratio threshold separates them. An hour is therefore
    repaired only when it clears the demand screen's bar against BOTH scale
    statistics — the median AND the series' own robust peak
    (:data:`_FUEL_SPIKE_SCALE_PCT`). Since the p99.9 is never below the median
    the peak limb implies the median limb: the test is the demand screen's,
    strengthened and never loosened, and what it can flag is exactly an hour
    above 2.5x the series' own ninth-largest hour. A series whose robust peak is
    not positive (an all-charging storage net series) has no operating scale to
    screen against and passes through — and so does a series whose robust peak
    is not a PLATEAU level, the zero-baseline guard below.

    **Why a robust peak can fail to be a scale (lane NWPP-39, the zero-baseline
    guard).** The peak limb's premise is that the top of a legitimate fuel
    series is a plateau: a fleet dispatched against a nameplate ceiling occupies
    the neighbourhood of that ceiling for many hours, so no hour can sit 2.5x
    above the ninth-largest. That premise needs the ninth-largest hour to lie
    INSIDE the occupied top regime. A series whose operating hours are rare,
    short events — a peaker oil fleet that is off for 97 % of the year — has
    its ninth-largest hour OUTSIDE every event, so the "robust peak" is the idle
    tail, not an operating level, and whether a real start is deleted depends
    on whether it lasted nine hours. Measured (NWPP-37 §6, the case that made
    the defect visible): SOCO ``NG: OIL`` 2024 has median 0.0 MW and p99.9
    71.7 MW (285 positive hours of 8,752; 8 hours >= 100 MW), and h386-392 —
    2024-01-17 03:00-09:00, Winter Storm Heather — is a coherent peaker start
    530 → 649 → 660 → 687 → 762 → 801 → 350 MW tracking SOCO's demand ramp from
    41.0 to 47.4 GW. The unguarded screen deleted it (4.4 GWh, 0.0056 → 0.0012
    TWh), a rule 14 ``[R-ACCURATE]`` violation by construction: a screen that
    deletes a documented weather event is burying real data, not repairing
    telemetry. The same fleet ran >= 9 hours above 851 MW in 2025 and nothing
    was flagged there. This is the fuel-column analogue of the CHPD cold-snap
    failure ``frames._pool_hourly_frame`` documents for the DEMAND spike screen.

    The guard is the screen's own premise applied to its own anchor at the
    next-coarser rank: if the p99.9 is itself more than
    :data:`_FUEL_SPIKE_RATIO` times the series' p99.0
    (:data:`_FUEL_SPIKE_PLATEAU_PCT`, the ninth-largest hour against the
    eighty-eighth), the top 0.1 % of the series is a tail rather than a
    plateau, the premise the limb rests on is falsified by the series itself,
    and there is nothing to screen against — the column passes through
    untouched, exactly as the non-positive case does. A p99.0 of zero under a
    positive p99.9 (the top 1 % is idle) is the same case and needs no branch.
    It is a construction, not a fit: the factor is the screen's by import, the
    rank is one decade below the anchor's exactly as the anchor's is one decade
    below the maximum's, it is a ratio of two order statistics of the same
    series (scale-invariant; no MW level, no other column, no residual), and it
    can only RELEASE a series, never flag an hour the unguarded screen would
    not. Measured over every ``NG:`` series on disk, 2019-2026 (687 with a
    positive p99.9): the ratio's median is 1.066 and its p95 is 1.915; the 26
    series above 2.5 are rarely-run oil fleets, sub-10-MW idle series, and two
    ERCO ``NG: OTH`` years whose anchor a >= 9-hour run had already lifted
    (nothing flagged there with or without the guard). Of the 21 series the
    screen flagged, exactly four are released — SOCO ``NG: OIL`` 2023 (h7975,
    390 MW, a 2023-11-29 morning start 146 → 390 → 100 MW) and 2024 (Heather),
    and one MW-scale hour each in IPCO and NEVP ``NG: OIL`` 2024 (6 and 3 MW,
    both inside a three-hour ramp) — and every other flagged series, the two
    control artifacts included (SWPP 2023 ``NG: WND`` ratio 1.060; NYIS 2024
    ``NG: OTH`` 1.051), is byte-identical. Rejected on principle, not on what
    they flag: a MW floor on the anchor (a magic number, and not scale-invariant
    between a 200 MW PUD member and a 47 GW BA); ``median > 0`` as eligibility
    (releases every solar series, whose nameplate plateau is unambiguous); a
    minimum fraction of positive hours (a new free number, and the median test
    in disguise). What the guard gives up is stated: a series whose top is a
    tail is not screened at all, so a future unit slip in such a series passes —
    but on such a series the unguarded screen could not tell a slip from an
    operating event either, so no reliable repair is lost.

    **Rule 13 ``[R-MEASURED]`` admissibility.** The screen is a property of the
    series itself — two order statistics of the same 8,760 hours — so it
    regenerates for any forward year from that year's own extract and responds
    to nothing but the extract; it reads no residual, no model output and no
    per-window registry. Rule 14 ``[R-ACCURATE]``: the artifact is a defect in
    the telemetry, repaired by the same NaN + linear interpolation the loaders
    apply to a missing meter hour, never a haircut on the measurement. Rule 24
    ``[R-REGISTRY]``: nothing here is a tunable — the factor is the demand
    screen's by import and the anchor is a fixed order statistic; neither is a
    ``ScenarioConfig`` field, an env var or a CLI flag, and neither enters
    ``cache_key()`` (data is not in the key).

    **The screen runs on the RAW column, before any gap-fill** — the order is
    load-bearing. SPP-31's builder-side copy ran on the already-interpolated
    series, and at NYIS 2024 h6759 (a 16,117 MW ``NG: OTH`` hour immediately
    followed by a 9-hour NaN reporting gap) that interpolated THROUGH the spike
    first and then "repaired" five hours of its own interpolation; on the
    H1-2026 partial year the same smear pulled the p99.9 anchor above the
    artifact and flagged nothing. Screening the raw observations flags the one
    real artifact hour, and the loader's own gap-fill then bridges spike and
    gap together from the last real hour to the next. Two order statistics of a
    ~3,900-hour half year sit at the 4th-5th largest hour, so a run of four or
    more consecutive slip hours in a partial year could lift the anchor —
    stated as a limit of the construction, never tuned around.

    **Measured effect** over all seven ISOs, 2019-2026, every reader
    (SPP-41 tables 0a/0b): exactly two benchmark series move in 2021-2025 —
    SPP 2023 ``wind`` 106.6345 → 103.0488 TWh (1 hour, h3907) and NYISO 2024
    ``other`` 3.3846 → 3.3197 TWh (1 hour, h6759, the same NYIS reporting-gap
    window ``_screen_demand_dropouts`` documents for that BA's ``Demand``;
    SPP-31's post-fill copy read 3.3486 for the reason above) — plus NYISO
    H1-2026 ``other`` 5.3153 → 5.1552 (3 hours, h2957-2959, an unscored series
    in a locked-test year, data readiness only) and ONE delivered-profile
    series, SPP 2023 wind, identically. Every other ISO x year x series, and
    every ERCOT-specific reader, is byte-identical.

    **That table is SPP-41's and it is no longer the whole footprint** — NWPP
    and SOCO were registered a week after it was measured (2026-09-14), so the
    screen has always flagged hours in them that no published control set
    named. Re-censused over all NINE regions x 2019-2026 at the frame level
    (NWPP-37 §4): ERCOT, CAISO, PJM, MISO and NEISO carry **no flagged hour in
    any column in any year** — a proof, not a sample, that they cannot move at
    any consumer. NYISO (2024 ``NG: OTH``) and SPP (2023 ``NG: WND``) are the
    two SPP-41 already names. NWPP flags ``NG: WAT`` / ``NG: NG`` / ``NG: COL``
    / ``NG: OTH`` in 2024-2025, and SOCO flags ``NG: NG`` in 2025 (4 hours at
    ~70,000 MW where the BA's WHOLE ``Net generation`` that hour is 25,878-
    34,565 MW — a fuel exceeding the total is impossible, so the repair is
    unambiguous) and ``NG: OIL`` in 2023-2024.

    The SOCO ``NG: OIL`` flags in that census were the FALSE POSITIVE the
    zero-baseline guard above now prevents (NWPP-37 §6 routed it; NWPP-39
    repaired it): with the guard, SOCO ``NG: OIL`` 2023-2024 passes through and
    the 2024 benchmark ``oil`` reads its filed 0.0056 TWh again.

    Only the ``NG: <CODE>`` columns are touched (:data:`_EIA930_FUEL_COLUMN_PREFIX`).
    Returns ``frame`` itself when nothing is flagged and a COPY otherwise. The
    copy stays load-bearing after the move to the construction seam: the frame
    handed in may be another cache's object — ``frames._pool_hourly_frame`` is
    itself ``lru_cache``d — and a repair must never be written back into it.
    What ``frames._eia_hourly_frame`` then caches IS the screened frame, which
    is the point: the screen runs once per (BA, year), not once per reader.
    Flagged hours become NaN so each reader's existing gap-fill
    (``interpolate().bfill().ffill()``) bridges them exactly as it bridges a
    missing meter hour.
    """
    out: pd.DataFrame | None = None
    for column in frame.columns:
        if not str(column).startswith(_EIA930_FUEL_COLUMN_PREFIX):
            continue
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            continue
        median = float(np.median(finite))
        peak = float(np.percentile(finite, _FUEL_SPIKE_SCALE_PCT))
        if peak <= 0.0:
            continue
        # Zero-baseline guard (lane NWPP-39): the anchor must pass the screen's
        # own premise at the next-coarser rank. A ninth-largest hour that is
        # itself a "spike" against the eighty-eighth means the series' top is a
        # tail, not a plateau — no operating scale, nothing to screen against.
        plateau = float(np.percentile(finite, _FUEL_SPIKE_PLATEAU_PCT))
        if peak > _FUEL_SPIKE_RATIO * plateau:
            continue
        spike = (
            np.isfinite(values)
            & (values > _FUEL_SPIKE_RATIO * median)
            & (values > _FUEL_SPIKE_RATIO * peak)
        )
        n_spike = int(spike.sum())
        if n_spike == 0:
            continue
        logger.warning(
            "%s %d: repairing %d EIA-930 %s spike hour(s) %s "
            "(max %.0f MW vs p%.1f %.0f MW) -- unit-slip artifact",
            ba_code,
            year,
            n_spike,
            column,
            np.flatnonzero(spike).tolist(),
            float(np.nanmax(values)),
            _FUEL_SPIKE_SCALE_PCT,
            peak,
        )
        if out is None:
            out = frame.copy()
        repaired = values.copy()
        repaired[spike] = np.nan
        out[column] = repaired
    return frame if out is None else out


def _pad_to_year(series: np.ndarray) -> np.ndarray:
    """Return ``series`` coerced to exactly ``HOURS_PER_YEAR`` samples.

    Longer series are truncated; shorter ones (an EIA-930 BA-year with a few
    missing hours, e.g. PJM 2023) are edge-padded with the series mean so the
    annual total scales to a full year rather than carrying a gap.
    """
    series = np.asarray(series, dtype=float)
    if series.shape[0] >= HOURS_PER_YEAR:
        return series[:HOURS_PER_YEAR]
    pad = np.full(HOURS_PER_YEAR - series.shape[0], float(series.mean()))
    return np.concatenate([series, pad])


def load_eia_hourly_benchmark(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return the EIA-930 hourly benchmark series for any ISO's BA, full year.

    Generalizes the ERCOT-only :func:`load_ercot_fossil_gen` /
    :func:`load_ercot_nuclear_gen` / :func:`load_ercot_renewable_gen` trio to
    every ISO with a per-BA ``<BA> hourly`` extract (see
    :data:`_ISO_TO_HOURLY_BA`). Returns the per-fuel net generation plus the
    actual net generation and net interchange, each as a ``(HOURS_PER_YEAR,)``
    array. Unlike the strict :func:`_eia_hourly_frame`, a BA-year a few hours
    short of 8760 (e.g. PJM 2023) is padded to a full year rather than
    rejected, so the delivered fuel-mix and interchange benchmark is still
    available for the calibration report.

    Per-fuel series listed in :data:`_ZERO_CODED_GAP_SERIES` have their exact
    zeros masked to NaN before that gap-fill, because for those (BA, fuel) pairs
    a zero is a filing gap rather than an observation — see that registry for
    the per-entry evidence.

    The year's frame passes through :func:`_screen_fuel_spike_columns` first,
    so an EIA-930 unit-slip hour in any ``NG:`` column (SPP 2023 wind, h3907)
    is NaN by the time the gap-fill runs and is bridged like a missing meter
    hour. The screen runs before the zero-coded mask: a registered zero gap can
    only lower a series' median (loosening the implied median limb) and cannot
    move its p99.9, so the order does not change what is flagged. ``Net
    generation`` and ``Total interchange`` are outside the screen by ruling.

    EIA's interchange sign convention is positive = net export.

    Returns ``None`` when the ISO is unmapped, the file is missing, or the
    year has no rows.
    """
    ba_code = _ISO_TO_HOURLY_BA.get(iso)
    if ba_code is None:
        return None
    path = _eia_hourly_path(ba_code)
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    local = df["Local date"]
    df = df[
        (local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if df.empty:
        return None
    df = _screen_fuel_spike_columns(df, ba_code=ba_code, year=year)

    out: dict[str, np.ndarray] = {}
    for name, column in _EIA930_BENCHMARK_COLUMNS:
        if column not in df.columns:
            continue
        # Storage breakout series can be reported for only part of the year
        # (the BA added BAT/PS to its filing mid-year); a sub-threshold raw
        # coverage means the series is not a full-year observation, so drop it
        # rather than interpolate a few months across the whole year.
        if name in _STORAGE_BENCHMARK_SERIES:
            coverage = 1.0 - float(df[column].isna().mean())
            if coverage < _STORAGE_MIN_COVERAGE_FRAC:
                continue
        raw = df[column]
        # Zero-coded filing gaps become NaN so the interpolation below bridges
        # them like any other hole, instead of averaging a phantom zero into the
        # benchmark (see _ZERO_CODED_GAP_SERIES for the per-BA evidence).
        if column in _ZERO_CODED_GAP_SERIES.get(ba_code, frozenset()):
            raw = raw.mask(raw == 0.0)
        series = raw.interpolate().bfill().ffill()
        if series.isna().any():
            continue
        out[name] = _pad_to_year(series.to_numpy(dtype=float))

    if "Net generation" in df.columns:
        net_gen = df["Net generation"].interpolate().bfill().ffill()
        if not net_gen.isna().any():
            out["net_gen"] = _pad_to_year(net_gen.to_numpy(dtype=float))
    if "Total interchange" in df.columns:
        interchange = df["Total interchange"].interpolate().bfill().ffill()
        if not interchange.isna().any():
            out["interchange"] = _pad_to_year(interchange.to_numpy(dtype=float))

    # Clean-data seam (gated, default OFF): override the per-fuel generation
    # with the curated clean ``generation`` dataset for the 1:1-mapped fuels
    # (parity-checked in tests). The aggregate ``net_gen`` / ``interchange`` and
    # any non-overridden fuels keep their raw values.
    if _use_clean():
        clean_fuels = _clean_generation_by_fuel(iso, year)
        if clean_fuels:
            out.update(clean_fuels)
    return out or None


def load_eia_hourly_renewable_gen(iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return hourly wind/solar net generation (MW) for an ISO's EIA-930 BA.

    Resolves the ISO to its EIA-930 BA code (see :data:`_ISO_TO_HOURLY_BA`)
    and reads the per-BA wide ``<BA> hourly`` extract — the same chronological
    source as the demand and interchange series — so renewable profiles share
    the calibration's time index. Each present series is gap-filled (linear
    interpolation, then back/forward fill) like the ERCOT renewable path.
    Small calendar holes in the extract itself (PJM's missing first hour and
    fall-back day) are bridged by :func:`_eia_hourly_frame_filled`, so a
    BA-year a day short of 8760 still yields a measured profile instead of
    silently falling back to the normalized EIA-930 distribution shape.

    This is the delivered-profile path the LP consumes
    (``renewables._eia_hourly_cf_profile`` turns it into the wind / solar
    bound), and its frame arrives already screened from
    :func:`~market_sim.data.eia930.frames._eia_hourly_frame_filled`: the SPP
    2023 h3907 wind slip that inflated the C4 benchmark by 3.5857 TWh reached
    the model's wind input through this function (SPP-40 §4) and is repaired
    at the frame-construction seam, with no second application here.

    Returns ``{"wind": ..., "solar": ...}`` of ``(HOURS_PER_YEAR,)`` arrays for
    whichever of the two fuels the BA reports with a usable full-year series,
    or ``None`` when the ISO is unmapped, the file/year is unavailable, or
    neither fuel is usable.
    """
    ba_code = _ISO_TO_HOURLY_BA.get(iso)
    if ba_code is None:
        return None
    frame = _eia_hourly_frame_filled(ba_code, year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("wind", "NG: WND"), ("solar", "NG: SUN")):
        if column not in frame.columns:
            continue
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            continue
        out[fuel] = series.to_numpy(dtype=float)
    return out or None


def load_ercot_fossil_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly coal and natural-gas net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` extract — the same chronological
    source as the demand and renewable series — so the fossil profiles
    share the calibration's time index. ``"gas"`` is the balancing
    authority's whole gas fleet (combined cycle, combustion turbine and
    steam together), the counterpart to the model's summed gas dispatch.
    Returns ``{"coal": ..., "gas": ...}`` of ``(HOURS_PER_YEAR,)`` arrays,
    or ``None`` when the file, the year, or the per-source columns are
    unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel, column in (("coal", "NG: COL"), ("gas", "NG: NG")):
        if column not in frame.columns:
            return None
        series = frame[column].interpolate().bfill().ffill()
        if series.isna().any():
            return None
        out[fuel] = series.to_numpy(dtype=float)
    return out


def load_ercot_nuclear_gen(year: int) -> np.ndarray | None:
    """Return ERCOT hourly nuclear net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` ``NG: NUC`` series on the same
    chronological clock as the demand, renewable and fossil series.
    Returns a ``(HOURS_PER_YEAR,)`` array, or ``None`` when the file,
    the year, or the column is unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None or "NG: NUC" not in frame.columns:
        return None
    series = frame["NG: NUC"].interpolate().bfill().ffill()
    if series.isna().any():
        return None
    return series.to_numpy(dtype=float)


def load_ercot_other_gen(year: int) -> np.ndarray | None:
    """Return ERCOT hourly "Other Fuel Sources" net generation (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` ``NG: OTH`` series on the same
    chronological clock as the other benchmark series. Threaded into the
    calibration bundle so the benchmark can tell how much other/biomass
    generation ERCO reports OUTSIDE its "Natural Gas" cell: since the
    Nov-2024 EIA-930 storage breakout moved battery discharge out of OTH
    (into BAT/UES), ERCO's Other series carries roughly biomass alone
    (~0.26 TWh in 2025) while EIA-923 books ~1.1 TWh of OTHER + biomass grid
    generation — the balance sits inside ``NG: NG``. Carrying the measured
    Other series lets the gas fold-in deflation subtract only the
    genuinely-folded portion (``render_calibration_html._gas_foldin_deflation``
    and the C2 family fallback in ``calibration_verdict.score_sysvol``)
    instead of scoring the model's gas fleet against gas + other. Returns
    ``None`` when the file, the year, or the column is unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None or "NG: OTH" not in frame.columns:
        return None
    series = frame["NG: OTH"].interpolate().bfill().ffill()
    if series.isna().any():
        return None
    return series.to_numpy(dtype=float)


def load_ercot_battery_gen(year: int) -> dict[str, np.ndarray] | None:
    """Return ERCOT hourly battery discharge and charge (MW) for a year.

    Reads the EIA-930 ``ERCO hourly`` battery series on the same
    chronological clock as the other benchmark series: ``NG: BAT`` carries
    the fleet's net discharge and ``NG: UES`` (unspecified energy storage)
    its net charge as negative MW. The two are folded into non-negative
    ``{"battery_discharge": ..., "battery_charge": ...}`` arrays of
    ``(HOURS_PER_YEAR,)``.

    Unlike the fossil/nuclear loaders, hours the BA had not yet begun
    reporting (ERCOT's battery series starts mid-2024) are kept as NaN
    rather than gap-filled or rejected, so a partial-coverage year still
    yields a benchmark over its reported window. Returns ``None`` when the
    file, the year, or both battery columns are unavailable.
    """
    frame = _ercot_hourly_frame(year)
    if frame is None:
        return None
    cols = [c for c in ("NG: BAT", "NG: UES") if c in frame.columns]
    if not cols:
        return None
    # BAT (discharge) and UES (charge) can be nonzero in the same hour, so
    # positive/negative MW are folded per column — never netted across them.
    values = frame[cols].to_numpy(dtype=float)
    if np.isnan(values).all():
        return None
    discharge = np.nansum(np.clip(values, 0.0, None), axis=1)
    charge = np.nansum(np.clip(-values, 0.0, None), axis=1)
    unreported = np.isnan(values).all(axis=1)
    discharge[unreported] = np.nan
    charge[unreported] = np.nan
    return {"battery_discharge": discharge, "battery_charge": charge}


def load_generation_profiles(
    iso: str,
    year: int,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Load per-fuel hourly generation profiles for an ISO and year.

    The ``value`` column is a normalized distribution that sums to roughly
    1.0 over the hours of each ``(iso, year, fuel)`` group.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A DataFrame with columns ``iso``, ``year``, ``fuel``, ``hour`` and
        ``value`` for the requested ISO and year.

    Raises:
        ValueError: if no data matches ``(iso, year)``.
    """
    profiles = pd.read_parquet(data_dir / _GENERATION_PROFILES_FILE)
    return _filter_iso_year(profiles, iso, year)
