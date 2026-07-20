"""Measured hydro / interchange / corridor / seam series for :mod:`market_sim.data.eia930`.

The measured capability envelopes and interchange schedules: EIA-930 hydro
(monthly budgets, hourly deliverability ceiling), the CAISO/MISO measured
hub-price and corridor/seam flow envelopes, and the per-ISO net-interchange
schedules ``load_demand`` serves. Split out of ``data/eia_loader.py`` as pure
code motion (W-D2, 2026-07-20).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.interchange_config import CAISO_IMPORT_TRANCHE_HUB
from market_sim.config.paths import ISO_TRANSMISSION_DIR, RAW_DIR

from .frames import _ISO_TO_HOURLY_BA, _MONTH_START_HOUR, _eia_hourly_frame_filled


def _calibration_dir() -> Path:
    """Package-namespace read of ``CALIBRATION_DIR``.

    Tests patch ``market_sim.data.eia_loader.CALIBRATION_DIR`` (the facade
    aliases the ``eia930`` package), so the measured-LMP loaders resolve the
    directory through that shared namespace at call time — exactly the
    pre-split module-global read semantics.
    """
    from market_sim.data import eia930 as _pkg

    return _pkg.CALIBRATION_DIR


# PJM's hourly actual tie-line interchange (import/export) lives here, one file
# per year. Used to add PJM's net export to the demand the internal fleet must
# serve, closing the energy-only model's largest structural gap (PJM is a large
# net exporter, ~40 TWh in 2023).
_PJM_INTERCHANGE_DIR: Path = ISO_TRANSMISSION_DIR


def measured_monthly_hydro(iso: str, year: int) -> np.ndarray | None:
    """Return EIA-930 measured conventional-hydro net generation by month.

    Twelve-entry vector (MWh, index 0 = January) of the ISO's BA ``NG: WAT``
    (water = conventional hydro) summed by local calendar month for ``year``.
    Pumped storage (``NG: PS``) is deliberately excluded — it is a storage
    resource, not inflow hydro. Returns ``None`` when the ISO has no per-BA
    hourly extract, the year is not a clean 8760-hour series, the ``NG: WAT``
    column is absent, or the year's hydro is all-zero/missing.

    Used to repin an incomplete-EIA-923 hydro budget to its measured monthly
    total — see :func:`market_sim.data.hydro.load_hydro_budget`
    ``monthly_target_mwh``.
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    # Use the gap-filling frame, not the strict 8760 one: this helper exists to
    # repin an *incomplete* EIA-923 vintage (notably 2025), and the current-year
    # EIA-930 extract is itself often a few hours short of a clean local year
    # (CISO 2025 is 8751 local-year rows). The strict loader rejects that and
    # the repin silently no-ops on the very year it is meant to fix; the filled
    # loader bridges the <=72h hole. The inserted gap rows carry NaT dates and
    # NaN NG: WAT, so the per-month nansum below ignores them.
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "NG: WAT" not in frame.columns:
        return None
    months = frame["Local date"].dt.month.to_numpy()
    wat = pd.to_numeric(frame["NG: WAT"], errors="coerce").to_numpy()
    out = np.array([np.nansum(wat[months == m]) for m in range(1, 13)], dtype=float)
    return out if out.sum() > 0.0 else None


def climatological_monthly_hydro(
    iso: str, years: "tuple[int, ...] | list[int] | None" = None
) -> np.ndarray | None:
    """Return the normal-water-year monthly hydro climatology (MWh).

    Twelve-entry vector (index 0 = January) of the per-month mean of the
    measured EIA-930 ``NG: WAT`` (conventional hydro) net generation across
    ``years`` — the forecast analogue of :func:`measured_monthly_hydro`. A
    single historical year is a particular wet/dry draw; averaging several
    years gives a *normal water year* the forecast hydro budget level can be
    built from, then scaled by a wet/dry scenario lever
    (:func:`market_sim.data.hydro.forecast_monthly_hydro`). Years the ISO does
    not cover (no per-BA extract, not a usable hydro year) are skipped, so a
    short extract still yields a climatology from whatever years are present.

    Args:
        iso: ISO identifier, e.g. ``"CAISO"``.
        years: Historical years to average. ``None`` (default) uses
            :data:`market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`.

    Returns:
        The ``(12,)`` mean monthly hydro net generation in MWh, or ``None``
        when no year in the window has usable measured hydro for ``iso``.
    """
    if years is None:
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS

        years = HYDRO_CLIMATOLOGY_YEARS
    monthly = [measured_monthly_hydro(iso, int(y)) for y in years]
    monthly = [m for m in monthly if m is not None]
    if not monthly:
        return None
    return np.vstack(monthly).mean(axis=0)


def _hydro_wat_month_hod(iso: str, year: int) -> "pd.DataFrame | None":
    """Return one year's EIA-930 ``NG: WAT`` on the model clock, long-form.

    Columns ``month`` (1-12), ``hod`` (0-23), ``mw``. The (month, hod) keys
    come from the frame's ROW ORDER (row k = model hour k, the property the
    dispatch itself relies on — verified byte-identical to the demand the LP
    serves), NOT from the extract's ``Local time`` labels, whose stamps carry
    a fixed-offset error against the model clock. Leap years carry 8760 rows
    (Feb 29 dropped by the frame loader), so the fixed non-leap calendar maps
    every row. Returns ``None`` when the extract or column is absent.
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "NG: WAT" not in frame.columns:
        return None
    from market_sim.data.fleet import _hour_to_month_index

    n = len(frame)
    wat = pd.to_numeric(frame["NG: WAT"], errors="coerce").to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "month": _hour_to_month_index(n) + 1,
            "hod": np.arange(n) % 24,
            "mw": wat,
        }
    )


def measured_hydro_hourly_envelope(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
) -> np.ndarray | None:
    """Return the hydro fleet's measured hourly deliverability ceiling (MW).

    For each hour of the run horizon, the ``percentile`` (default
    :data:`market_sim.config.constants.HYDRO_ENVELOPE_PERCENTILE`) of the
    measured EIA-930 ``NG: WAT`` hourly output in that hour's (month ×
    hour-of-day) bucket — the fleet's revealed head/flow/scheduling
    deliverability, which the nameplate ``pmax`` bound ignores. The same
    measured capability-envelope construction as
    :func:`measured_corridor_flow_envelope` (the keeper-blessed corridor ATC
    proxy): the LP still clears its merit order *below* the ceiling, so this
    bounds the budget LP's perfect-foresight hoarding without pinning dispatch
    to the residual (rule #13).

    A backcast year uses its own measured envelope (the same admissibility
    class as same-year CAMPD outage windows — a physical availability input);
    a year the extract does not cover (a forecast year) falls back to the
    pooled per-bucket percentile across
    :data:`~market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`, so the
    mechanism regenerates forward from climatology. (Month, hod) keys come
    from the frames' row order — the model clock — not the extracts'
    fixed-offset ``Local time`` labels; see :func:`_hydro_wat_month_hod`.

    Note: for BAs with no separate pumped-storage series (CISO), ``NG: WAT``
    includes pumped-storage generation while the model's budget-hydro fleet
    excludes it — the envelope is therefore *generous* by the PS discharge in
    the bucket (a documented, conservative misalignment per rule #14; it only
    weakens the cap, never tightens it beyond the measured water fleet).

    Returns ``(hours,)`` MW, or ``None`` when the ISO has no BA extract or no
    year (measured or climatology) yields usable data — the caller leaves the
    fleet uncapped (byte-identical).
    """
    from market_sim.config.constants import (
        HYDRO_CLIMATOLOGY_YEARS,
        HYDRO_ENVELOPE_PERCENTILE,
    )
    from market_sim.data.fleet import _hour_to_month_index

    pct = HYDRO_ENVELOPE_PERCENTILE if percentile is None else float(percentile)
    frames = []
    own = _hydro_wat_month_hod(iso, year)
    if own is not None and np.isfinite(own["mw"]).any() and own["mw"].max() > 0:
        frames = [own]
    else:
        pooled = [_hydro_wat_month_hod(iso, int(y)) for y in HYDRO_CLIMATOLOGY_YEARS]
        frames = [
            f
            for f in pooled
            if f is not None and np.isfinite(f["mw"]).any() and f["mw"].max() > 0
        ]
    if not frames:
        return None
    work = pd.concat(frames, ignore_index=True).dropna(subset=["mw"])
    if work.empty:
        return None

    tab = np.full((12, 24), np.nan)
    for (m, h), g in work.groupby(["month", "hod"], observed=True):
        tab[m - 1, h] = np.percentile(g["mw"].to_numpy(), pct)
    # Fill any empty bucket with its month's max over hours, then the global
    # max, so the cap is always finite and never tighter than a populated
    # neighbour (same fill rule as measured_corridor_flow_envelope).
    for m in range(12):
        row = tab[m]
        if np.all(np.isnan(row)):
            continue
        row[np.isnan(row)] = np.nanmax(row)
    tab[np.isnan(tab)] = np.nanmax(tab)

    rm = _hour_to_month_index(hours)  # 0-based month per model hour
    rh = np.arange(hours) % 24
    return np.clip(tab[rm, rh], 0.0, None)


def measured_interchange_envelope(
    iso: str, year: int, hours: int, percentile: float = 90.0
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return the measured month×hour-of-day net-import/export envelope (MW).

    The priced-interchange node clears a near-constant schedule because its
    tranche capacities are available every hour. Real CAISO interchange instead
    follows a strong diurnal/seasonal duck: it imports overnight (PNW hydro /
    desert-SW gas) and **exports** the midday solar glut. This returns, per hour
    of the run horizon, the ``percentile`` of measured EIA-930 ``Total
    interchange`` for that hour's (month, hour-of-day) bucket, split into the
    net-import and net-export envelopes (EIA sign: positive = net export):

        import_cap[t] = P_pctile( max(0, -interchange) | month(t), hod(t) )
        export_cap[t] = P_pctile( max(0, +interchange) | month(t), hod(t) )

    The caller scales the node's import-tranche availability and export-sink
    floor by these envelopes (relative to the static tranche totals), so the
    node can only import up to roughly its historical capability in that
    period and can export the midday surplus — the price still clears in merit
    order *within* the envelope, so this adds the measured temporal shape
    without pinning the flow or introducing any fitted constant. ``percentile``
    near the top of the distribution (default 90) keeps headroom above the
    median so price, not the cap, sets the typical hour.

    Returns ``(import_cap, export_cap)``, each ``(hours,)`` MW, or ``None`` when
    the ISO has no BA hourly extract or the year is not covered (a forecast
    year), in which case the caller leaves the static node unshaped.
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "Total interchange" not in frame.columns:
        return None
    local = pd.DatetimeIndex(frame["Local time"])
    month = local.month.to_numpy(dtype=float)
    hod = local.hour.to_numpy(dtype=float)
    ti = pd.to_numeric(frame["Total interchange"], errors="coerce").to_numpy()
    imp = np.where(np.isfinite(ti), np.clip(-ti, 0.0, None), np.nan)
    exp = np.where(np.isfinite(ti), np.clip(ti, 0.0, None), np.nan)

    # Per (month, hour-of-day) bucket percentile. Empty buckets stay 0.
    imp_tab = np.zeros((12, 24))
    exp_tab = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            if not sel.any():
                continue
            ii = imp[sel]
            ee = exp[sel]
            ii = ii[np.isfinite(ii)]
            ee = ee[np.isfinite(ee)]
            if ii.size:
                imp_tab[m - 1, h] = np.percentile(ii, percentile)
            if ee.size:
                exp_tab[m - 1, h] = np.percentile(ee, percentile)

    # Map the (month, hod) tables onto the run horizon. Row 0 of the dispatch
    # is the first local hour of the year (see _eia_hourly_frame), so a plain
    # local clock reproduces that index.
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    return imp_tab[rm, rh], exp_tab[rm, rh]


def measured_gas_floor_profile(
    iso: str, year: int, hours: int, percentile: float = 50.0
) -> np.ndarray | None:
    """Return the measured month×hour-of-day EIA-930 ``NG: NG`` profile (MW).

    For each hour of the run horizon, the ``percentile`` of measured EIA-930
    natural-gas net generation (``NG: NG``) for that hour's (month,
    hour-of-day) bucket. Used as the magnitude of the CAISO Resource-Adequacy
    must-offer minimum-commitment floor (see
    :func:`market_sim.model.transmission.inject_caiso_gas_commitment_floor`):
    holding the gas fleet online midday at (a fraction of) this measured
    profile makes the model *long* midday, so its surplus exports/curtails at
    ~$0 — reproducing CAISO's collapsed spring-midday LMP.

    The (month, hour-of-day) bucketing follows
    :func:`measured_interchange_envelope`: a measured diurnal/seasonal shape
    with no fitted constant, robust to leap-year / missing hours (gap rows
    carry NaN ``NG: NG`` and drop out of each bucket). The median (default
    percentile) is the *typical* gas level RA commitment holds the fleet at;
    the caller scales it by ``config.caiso_gas_floor_frac``.

    Note ``NG: NG`` is the EIA-930 gas figure, which for CISO silently absorbs
    geothermal/biomass (EIA-930 reports neither for CISO); that inflation is
    irrelevant here — this profile shapes a *floor*, not a benchmark, and gas
    generation is still validated against EIA-923, not this series.

    Returns ``(hours,)`` MW, or ``None`` when the ISO has no BA hourly extract,
    the ``NG: NG`` column is absent, or the year is uncovered (a forecast
    year), in which case the caller leaves the fleet unfloored (byte-identical).
    """
    ba = _ISO_TO_HOURLY_BA.get(iso)
    if ba is None:
        return None
    frame = _eia_hourly_frame_filled(ba, year)
    if frame is None or "NG: NG" not in frame.columns:
        return None
    local = pd.DatetimeIndex(frame["Local time"])
    month = local.month.to_numpy(dtype=float)
    hod = local.hour.to_numpy(dtype=float)
    ng = pd.to_numeric(frame["NG: NG"], errors="coerce").to_numpy()

    tab = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            v = ng[sel]
            v = v[np.isfinite(v)]
            if v.size:
                tab[m - 1, h] = np.percentile(v, percentile)

    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    out = tab[rm, rh]
    return out if np.any(out > 0.0) else None


# CAISO priced-import tranche -> WECC neighbor hub whose measured intertie LMP is
# the tranche's real delivered energy cost. The PNW blocks (firm hydro + Mid-C
# shoulder) clear against the Malin / COI-PDCI ties; the desert-SW blocks (solar +
# Palo Verde nuclear, then SW gas) clear against the Palo Verde / Path-46 ties.
# WECC_scarcity (west-wide peak economy energy) also tracks Palo Verde at its peak.
# Single source of truth lives in constants (CAISO_IMPORT_TRANCHE_HUB) so this
# loader and the per-hub builder/injector (transmission.py) cannot drift apart.
_CAISO_IMPORT_TRANCHE_HUB: dict[str, str] = CAISO_IMPORT_TRANCHE_HUB


def measured_import_hub_prices(
    iso: str, year: int, hours: int
) -> dict[str, np.ndarray] | None:
    """Return each CAISO import tranche's measured hourly neighbor-hub price.

    Reads the measured WECC intertie scheduling-point LMP
    (``wecc_intertie_lmp_hourly_<ISO>.parquet`` under the calibration source
    dir: columns ``year``, ``hour`` [0..hours-1, local calendar], ``hub``
    [``MALIN`` / ``PALOVRDE``], ``price`` [$/MWh, the delivered nodal LMP =
    energy + congestion + loss (MCE+MCC+MCL) of the CAISO intertie LMP, GHG
    component excluded]) and maps each hub to the import tranches it prices via
    :data:`_CAISO_IMPORT_TRANCHE_HUB`. The congestion/loss components are what
    make MALIN (PNW) and PALOVRDE (desert-SW) differ (the energy component alone
    is system-wide identical at every WECC node).

    These are the *actual delivered energy cost of the imported power* — the
    neighbor hub's own marginal price at the CA border, which crashes in the
    spring PNW runoff (the real reason CAISO Apr/May RT is ~$11-14) and can go
    negative in the desert-SW solar glut (the real reason CAISO has ~870
    negative-price hours). They replace the static, bundle-fitted ladder in
    ``IMPORT_TRANCHES["CAISO"]`` when ``config.caiso_import_hub_prices`` is on;
    see :func:`market_sim.model.transmission.inject_caiso_import_hub_prices`.
    The price is the delivered nodal LMP (energy+congestion+loss, GHG excluded);
    the per-tranche CARB border carbon is re-added by the injector (so a clean
    hydro/solar tranche still pays none), matching the static-ladder carbon
    treatment.

    Returns ``{tranche_name: (hours,) $/MWh}`` for every tranche whose hub has a
    measured series, or ``None`` when the ISO is not CAISO, the parquet is
    absent (forecast years / before the OASIS fetch lands), or the year is
    uncovered — in which case the caller keeps the static ladder (byte-identical).
    """
    if iso.upper() != "CAISO":
        return None
    path = _calibration_dir() / f"wecc_intertie_lmp_hourly_{iso.upper()}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[frame["year"] == year]
    if frame.empty:
        return None

    out: dict[str, np.ndarray] = {}
    for hub, sub in frame.groupby("hub"):
        series = sub.sort_values("hour")
        # Interpolate the isolated DST spring-forward gap (1 interior NaN on the
        # fixed non-leap calendar that every hourly series carries); ``limit=2``
        # leaves a genuine multi-week gap (2023 Jan-Feb, aged out of OASIS
        # retention) NaN for the reference-formula fill below.
        price = (
            pd.to_numeric(series["price"], errors="coerce")
            .interpolate(limit=2)
            .to_numpy(dtype=float)
        )
        if price.shape[0] < hours:
            continue  # incomplete hub series — leave its tranches on the ladder
        price = price[:hours].copy()
        gap = ~np.isfinite(price)
        if gap.any():
            # Hybrid gap-fill for a bulk retention gap (2023 Jan-Feb: ~1.4k
            # hours aged out of OASIS before the fetch): fill the missing hours
            # with the corridor's FORWARD reference price ((HH + basis) × HR ×
            # neighbor load-shape) — the sanctioned forward-native analogue of
            # this measured series (rule #14: a reconciled fill of real data
            # over discarding ten measured months). Bounded to ≤25% of the
            # year so a mostly-missing series still falls back to the ladder;
            # the filled hours are the same hours absent from the actual-LMP
            # benchmark, so C3 price scoring never reads the filled values.
            if gap.mean() > 0.25:
                continue
            from market_sim.config.interchange_config import (
                CAISO_PER_HUB_NEIGHBORS,
            )
            from market_sim.data.neighbor_price import caiso_hub_reference_price

            spec = next(
                (s for s in CAISO_PER_HUB_NEIGHBORS.values() if s.hub == hub),
                None,
            )
            ref = (
                caiso_hub_reference_price(spec, year, hours)
                if spec is not None
                else None
            )
            if ref is None or not np.all(np.isfinite(ref[gap])):
                continue  # no forward fill available — leave on the ladder
            price[gap] = ref[gap]
        for tranche, mapped_hub in _CAISO_IMPORT_TRANCHE_HUB.items():
            if mapped_hub == hub:
                out[tranche] = price
    return out or None


def measured_intertie_hub_price_raw(
    iso: str, year: int, hours: int, hub: str
) -> np.ndarray | None:
    """Return ONE WECC intertie hub's measured hourly LMP, gaps left NaN.

    The raw-evidence companion to :func:`measured_import_hub_prices`: the same
    ``wecc_intertie_lmp_hourly_<ISO>.parquet`` series with the isolated DST
    spring-forward NaN interpolated (``limit=2``) but WITHOUT the bulk
    reference-formula gap fill — a genuine retention gap (2023 Jan–Feb) stays
    NaN. Used where the measured print is EVIDENCE of a market state rather
    than a price to charge (e.g. the caiso-87 surplus-state trigger of
    :func:`market_sim.model.transmission.inject_caiso_dsw_surplus_clean`):
    the formula fill is pricing continuity, not surplus evidence, so filled
    hours must not classify as surplus.

    Returns ``(hours,)`` $/MWh with NaN where unmeasured, or ``None`` when the
    ISO is not CAISO, the parquet is absent, or the year/hub is uncovered.
    """
    if iso.upper() != "CAISO":
        return None
    path = _calibration_dir() / f"wecc_intertie_lmp_hourly_{iso.upper()}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[(frame["year"] == year) & (frame["hub"] == hub)]
    if frame.empty:
        return None
    series = frame.sort_values("hour")
    price = (
        pd.to_numeric(series["price"], errors="coerce")
        .interpolate(limit=2)
        .to_numpy(dtype=float)
    )
    if price.shape[0] < hours:
        return None
    return price[:hours].copy()


def measured_miso_pjm_border_prices(
    iso: str, year: int, hours: int
) -> np.ndarray | None:
    """Return measured hourly PJM border-hub DA LMP for MISO's PJM import seam.

    Reads ``pjm_border_lmp_hourly_MISO.parquet`` (columns ``year``, ``hour``
    [0..8759, MISO Central-time calendar], ``hub`` [``PJM_WEST``], ``price``
    [$/MWh, DA total LMP = energy + congestion + loss]) built by
    ``scripts/data/build_pjm_border_lmp_miso.py`` from PJM Data Miner hub exports.
    ``PJM_WEST`` is the equal-weight mean of the three MISO-facing PJM gen hubs
    (CHICAGO GEN / AEP GEN / ATSI GEN), the same border decomposition the
    ``MISO_PJM_BORDER_HR_BY_YEAR`` derivation uses.

    Returns ``(hours,)`` array of $/MWh, or ``None`` when the ISO is not MISO,
    the parquet is absent, or the year is uncovered — in which case the caller
    keeps the gas × HR ladder (byte-identical).
    """
    if iso.upper() != "MISO":
        return None
    path = _calibration_dir() / "pjm_border_lmp_hourly_MISO.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[(frame["year"] == year) & (frame["hub"] == "PJM_WEST")]
    if frame.empty:
        return None
    series = frame.sort_values("hour")
    price = (
        pd.to_numeric(series["price"], errors="coerce")
        .interpolate(limit=2)
        .to_numpy(dtype=float)
    )
    if price.shape[0] < hours or not np.all(np.isfinite(price[:hours])):
        return None
    return price[:hours]


# Measured clock offset of the CISO per-DIBA interchange stamps relative to
# the model's hourly frame (the ``<BA> hourly`` extract row clock every CAISO
# demand/renewable series runs on): the stamps lag the model clock by 1 hour
# in standard-time months and 2 hours in daylight-time months. Measured by
# per-DST-regime lag scan of the summed per-DIBA series against the extract's
# own Total-interchange column (2023-2025: PST best lag −1 corr 0.972 vs 0.930
# at neighbours; PDT best lag −2 corr 0.961 vs 0.919), anchored absolutely by
# solar astronomy and the 2024-04-08 eclipse dip (both land the extract row
# clock on the true wall hour). Consistent with prevailing-local hour-ENDING
# stamps whose DST offset was applied twice at fetch time (the file predates
# scripts/data/fetch_eia930_interchange.py; see the eia-930-interchange README).
# Frozen against residuals (rule 23): these constants re-derive only from the
# lag scan in scripts/validate_caiso_seam_hod_frame.py, which fails loudly if
# the parquet is ever re-fetched with honest stamps (best lag moves to 0) so
# this correction cannot silently double-shift. Full forensics:
# results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md.
_CAISO_INTERCHANGE_LAG_STD_H: int = 1
_CAISO_INTERCHANGE_LAG_DST_H: int = 2


def _caiso_interchange_model_clock(stamps: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Map CISO per-DIBA ``local_time`` stamps onto the model's hourly clock.

    Subtracts the measured per-regime lag (:data:`_CAISO_INTERCHANGE_LAG_STD_H`
    hours in standard time, :data:`_CAISO_INTERCHANGE_LAG_DST_H` in daylight
    time) so each row lands on the start-of-hour slot of the same physical
    hour in the model's 8760 frame. The DST regime of each stamp is resolved
    with ``US/Pacific`` rules (the repeated fall-back hour is treated as
    standard time, the skipped spring-forward hour shifted forward — both
    choices touch one stamp a year and only move it between adjacent
    (month, hod) envelope buckets).
    """
    localized = stamps.tz_localize(
        "US/Pacific", ambiguous=False, nonexistent="shift_forward"
    )
    # Vectorized DST test: a Pacific stamp maps to UTC at +8h in standard
    # time and +7h in daylight time.
    is_dst = (localized.tz_convert("UTC").tz_localize(None) - stamps) == pd.Timedelta(
        hours=7
    )
    shift = np.where(is_dst, _CAISO_INTERCHANGE_LAG_DST_H, _CAISO_INTERCHANGE_LAG_STD_H)
    return stamps - pd.to_timedelta(shift, unit="h")


def measured_corridor_flow_envelope(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
    direction: str = "import",
) -> dict[str, np.ndarray] | None:
    """Return each CAISO import corridor's measured net-import deliverability cap.

    For each WECC import corridor (``WECC_PNW`` = COI/Path-66 into NP15,
    ``WECC_DSW`` = Path-46/WOR into SP15), returns the per-hour ceiling on net
    import (MW), built as the per-(month × hour-of-day) ``percentile`` of the
    MEASURED net import on that corridor from EIA-930 BA-to-BA interchange
    (``data/raw/eia-930-interchange/CISO interchange hourly.parquet``; columns
    ``diba``, ``mw`` [EIA sign: + = CISO exports to the DIBA], ``local_time``).
    Each CISO↔DIBA pair is summed into its corridor via
    :data:`~market_sim.config.interchange_config.CAISO_CORRIDOR_DIBA`, then
    ``net_import = -sum(interchange over the corridor's DIBAs)``.

    This is an ATC proxy: the corridor's *deliverable* transfer ceiling (the
    physical line rating net of parallel commitments and the neighbor's own
    diurnal length), which collapses midday when the desert-SW / Pacific-NW are
    themselves long on solar. The caller applies it as a one-sided hourly upper
    bound on the corridor link's import-direction flow, so the LP still clears
    its merit order *below* the ceiling — a capability limit, not a flow pinned
    to the residual (rule #12). ``percentile`` defaults to
    :data:`~market_sim.config.interchange_config.CAISO_CORRIDOR_FLOW_PERCENTILE` (95).

    Hours are mapped onto the model's fixed non-leap calendar
    (:func:`~market_sim.data.fleet._hour_to_month_index` for the month, ``hour %
    24`` for the hour-of-day), the same calendar the LP and the hydro budgets
    use, so the cap aligns hour-for-hour with the dispatch. The parquet's
    ``local_time`` stamps are first mapped onto the model clock via
    :func:`_caiso_interchange_model_clock` (the stamps lag the model frame by
    a measured 1 h standard-time / 2 h daylight-time — see the constant block
    above it), so each (month × hod) bucket keys the same physical hour the
    LP dispatches.

    Returns ``{corridor_zone: (hours,) MW}`` for both corridors, or ``None`` when
    the ISO is not CAISO, the parquet is absent, or the year is uncovered (a
    forecast year) — in which case the caller leaves the corridors uncapped
    (byte-identical).

    With ``direction="export"`` the same machinery instead returns each
    corridor's measured net-*export* deliverability ceiling (the per-(month ×
    hour-of-day) ``percentile`` of measured net export = −net import, clipped at
    0). It is the symmetric counterpart of the import ceiling: just as the import
    ATC collapses midday when the WECC neighbors are long on solar, the export
    ATC collapses in the evening ramp when the neighbors are themselves short
    (their own peak), so a corridor that reliably net-imports in an evening
    (month, hod) bucket caps export there at ~0 — forbidding the LP's unphysical
    evening wheel-out of cheap CA gas. Like the import ceiling it is a smoothed
    capability envelope the LP clears *below*, not the hourly residual flow
    (rule #12). Applied as the reverse-direction floor of the corridor's
    asymmetric interface group (see
    :func:`~market_sim.model.transmission.build_caiso_corridor_flow_groups`).
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    if iso.upper() != "CAISO":
        return None
    from market_sim.config.interchange_config import (
        CAISO_CORRIDOR_DIBA,
        CAISO_CORRIDOR_FLOW_PERCENTILE,
    )
    from market_sim.data.fleet import _hour_to_month_index

    pct = CAISO_CORRIDOR_FLOW_PERCENTILE if percentile is None else float(percentile)
    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    frame = frame[local.year == year]
    local = local[local.year == year]
    if frame.empty:
        return None
    corridor = frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    work = pd.DataFrame(
        {
            "corridor": corridor.to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["corridor", "mw"])
    # Net import per corridor per timestamp = -sum(interchange over its DIBAs).
    per_ts = work.groupby(["corridor", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")

    rm = _hour_to_month_index(hours) + 1  # 1-based month per model hour
    rh = np.arange(hours) % 24
    out: dict[str, np.ndarray] = {}
    for zone in ("WECC_PNW", "WECC_DSW"):
        sub = per_ts[per_ts["corridor"] == zone]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            vals = g["net_import"].to_numpy()
            if direction == "export":
                vals = -vals  # net export = -net import; p95 export deliverability
            tab[m - 1, h] = np.percentile(vals, pct)
        # Fill any empty (month, hod) bucket with that month's max over hours
        # (a conservative ceiling), then the global max, so the cap is always
        # finite and never tighter than a populated neighbour.
        for m in range(12):
            row = tab[m]
            if np.all(np.isnan(row)):
                continue
            tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        # Clip at 0: the cap bounds net flow in ``direction``; a (month, hod)
        # bucket whose p95 is negative (the corridor reliably runs the OTHER way
        # then — e.g. import p95 < 0 where the PNW corridor net-exports midday, or
        # export p95 < 0 where a corridor net-imports the evening ramp) caps that
        # direction at zero, never forcing the reverse flow.
        out[zone] = np.clip(tab[rm - 1, rh], 0.0, None)
    return out or None


def measured_firm_import_shape(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
) -> np.ndarray | None:
    """Return the unit-mean measured shape of CAISO's firm import base.

    For each hour of the run horizon, the per-(month × hour-of-day)
    ``percentile`` (default
    :data:`~market_sim.config.interchange_config.CAISO_FIRM_IMPORT_SHAPE_PERCENTILE`,
    the median) of the MEASURED total CISO corridor net import from EIA-930
    BA-to-BA interchange (``data/raw/eia-930-interchange/CISO interchange
    hourly.parquet``, summed over the corridor DIBAs of
    :data:`~market_sim.config.interchange_config.CAISO_CORRIDOR_DIBA`),
    clipped at 0 and normalized to UNIT MEAN over the mapped 8760 — a pure
    weight profile w(t), mean(w) = 1.

    The caller (:func:`market_sim.model.transmission
    .inject_caiso_firm_import_shape`) multiplies each firm/contracted import
    tranche's year-grounded DMM level by this weight, so the firm block's
    ANNUAL energy capability equals the published DMM RA-import × MIC-split
    sizing (the ``IMPORT_TRANCHES_BY_YEAR`` derivation) while its diurnal /
    seasonal availability follows the measured revealed import base: CAISO's
    net imports run 5.3–6.3 GW overnight, 0.2–1.3 GW midday (its own solar
    displaces them) and ramp back to 5.4–6.2 GW in the evening — a shape the
    flat 8760 block cannot represent. The median is the revealed
    typical-day schedule of the contracted/self-scheduled base, robust to
    both scarcity spikes and outage dips; because the profile is normalized
    to unit mean, the level never comes from this series (rule #13: EIA-930
    net flows cannot size a gross firm block — the DMM ladder carries the
    level, this carries only the shape).

    A backcast year uses its own measured shape (the same admissibility
    class as same-year CAMPD outage windows — the market's realized
    contracted-schedule structure); a year the extract does not cover (a
    forecast year) pools ALL covered years into one climatological shape, so
    the mechanism regenerates forward (DMM RA import contracting is a
    persistent market structure; the pool extends automatically as the
    extract does, rule #23). The extract's ``local_time`` stamps are mapped
    onto the model clock via :func:`_caiso_interchange_model_clock` before
    (month, hod) bucketing — never bucketed by their offset labels.

    Returns ``(hours,)`` unit-mean weights, or ``None`` when the ISO is not
    CAISO, the parquet is absent, or no usable data survives — the caller
    leaves the firm blocks flat (byte-identical).
    """
    if iso.upper() != "CAISO":
        return None
    from market_sim.config.interchange_config import (
        CAISO_CORRIDOR_DIBA,
        CAISO_FIRM_IMPORT_SHAPE_PERCENTILE,
    )
    from market_sim.data.fleet import _hour_to_month_index

    pct = (
        CAISO_FIRM_IMPORT_SHAPE_PERCENTILE if percentile is None else float(percentile)
    )
    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    covered = frame[local.year == year]
    if covered.empty:
        # Forecast year: pooled multi-year climatological shape.
        work_frame, work_local = frame, local
    else:
        work_frame, work_local = covered, local[local.year == year]
    corridor = work_frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    work = pd.DataFrame(
        {
            "month": work_local.month.to_numpy(),
            "hod": work_local.hour.to_numpy(),
            "ts": work_local.to_numpy(),
            "mw": pd.to_numeric(work_frame["mw"], errors="coerce").to_numpy(),
        }
    )[corridor.notna().to_numpy()].dropna(subset=["mw"])
    if work.empty:
        return None
    # Total net import per timestamp = -sum(interchange over corridor DIBAs).
    per_ts = (
        -work.groupby(["ts", "month", "hod"], observed=True)["mw"].sum()
    ).reset_index(name="net_import")
    tab = np.full((12, 24), np.nan)
    for (m, h), g in per_ts.groupby(["month", "hod"], observed=True):
        tab[m - 1, h] = np.percentile(g["net_import"].to_numpy(), pct)
    tab = np.clip(tab, 0.0, None)  # a net-export bucket carries zero firm weight
    # Fill any empty bucket with its month's mean over populated hours, then
    # the global mean — a weight, so the neutral fill is the mean (the
    # envelope functions fill with max because theirs is a ceiling).
    for m in range(12):
        row = tab[m]
        if np.all(np.isnan(row)):
            continue
        row[np.isnan(row)] = np.nanmean(row)
    if np.any(np.isnan(tab)):
        tab = np.where(np.isnan(tab), np.nanmean(tab), tab)
    rm = _hour_to_month_index(hours)  # 0-based month per model hour
    rh = np.arange(hours) % 24
    raw = tab[rm, rh]
    mean = float(raw.mean())
    if not np.isfinite(mean) or mean <= 0.0:
        return None
    return raw / mean


def caiso_solar_fraction(year: int, hours: int) -> np.ndarray | None:
    """Return CISO's hourly solar penetration (solar / demand) on the LP clock.

    A forward driver for the CAISO corridor ATC derate
    (:func:`market_sim.model.transmission.forward_corridor_atc_envelope`): the
    region's midday solar share, which collapses the deliverable WECC import
    transfer (the desert-SW / Pacific-NW are themselves long on solar midday).
    Built from the EIA-930 CISO extract (``NG: SUN`` / ``Demand``) on the model's
    local 8760 clock, so it aligns hour-for-hour with the dispatch. The desert-SW
    shares CAISO's solar resource and time zone, so the CISO share proxies the
    corridor's midday saturation; it responds to a changed forecast solar build,
    unlike the measured corridor flow.

    Returns a ``(hours,)`` fraction clipped to ``[0, 1]``, or ``None`` when the
    CISO extract is absent / too short (a forecast year with no extract — the
    caller then leaves the corridor uncapped).
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None or "Demand" not in frame.columns:
        return None
    demand = pd.to_numeric(frame["Demand"], errors="coerce")
    solar = pd.to_numeric(frame.get("NG: SUN"), errors="coerce").fillna(0.0)
    demand = demand.interpolate().bfill().ffill().to_numpy(dtype=float)
    solar = solar.to_numpy(dtype=float)
    if demand.shape[0] < hours or np.isnan(demand).any():
        return None
    demand = demand[:hours]
    solar = solar[:hours]
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(demand > 0.0, solar / demand, 0.0)
    return np.clip(np.nan_to_num(frac, nan=0.0), 0.0, 1.0)


def measured_seam_import_envelope(
    iso: str,
    year: int,
    hours: int,
    percentile: float | None = None,
    direction: str = "import",
) -> dict[str, np.ndarray] | None:
    """Return each priced seam's measured net-import deliverability cap (MW).

    The MISO analogue of :func:`measured_corridor_flow_envelope`. For each
    reference-price seam in :data:`~market_sim.config.interchange_config.MISO_SEAM_DIBA`
    (``PJM`` / ``SPP`` / ``South``), returns the per-hour ceiling on net import
    (MW), built as the per-(month × hour-of-day) ``percentile`` of the MEASURED
    net import summed over that seam's EIA-930 Directly-Interconnected BAs
    (``data/raw/eia-930-interchange/<BA> interchange hourly.parquet``; columns
    ``diba``, ``mw`` [EIA sign: + = ISO exports to the DIBA], ``local_time``).
    Each seam's net import is ``−sum(mw over its DIBAs)`` per timestamp.

    This is a transfer-capability / ATC proxy: the seam's *deliverable* net
    import in that period — congestion- and firm-rights-limited below the
    nameplate interface rating, and naturally near zero (or capped to zero) on a
    seam the ISO actually net-exports over (SPP, South). The caller applies it as
    a one-sided hourly upper bound on that seam's import bands, so the LP still
    clears its merit order *below* the ceiling and the export direction stays
    economic — a capability limit, not a flow pinned to the residual (claude.md
    rules #1/#12). ``percentile`` defaults to
    :data:`~market_sim.config.constants.MISO_SEAM_FLOW_PERCENTILE` (90).

    Hours map onto the model's fixed non-leap calendar
    (:func:`~market_sim.data.fleet._hour_to_month_index` for the month, ``hour %
    24`` for the hour-of-day), the same calendar the LP uses, so the cap aligns
    hour-for-hour with the dispatch. Leap-day samples fold into their (month,
    hour-of-day) buckets and never reach the dispatch clock.

    Returns ``{seam_name: (hours,) MW}`` for every seam with measured data, or
    ``None`` when the ISO has no seam-DIBA map, the parquet is absent, or the
    year is uncovered (a forecast year) — in which case the caller leaves the
    seams uncapped (byte-identical).

    With ``direction="export"`` the same machinery instead returns each seam's
    measured net-*export* deliverability ceiling (the per-(month × hour-of-day)
    ``percentile`` of measured net export = −net import, clipped at 0). It is the
    symmetric counterpart of the import ceiling: just as the import cap clips a
    net-importing seam, the export ceiling caps a seam's deliverable net export —
    so the eastern PJM seam (which MISO reliably net-*imports* over) caps export
    at ~0, forbidding the LP's unphysical export of cheap MISO coal back over the
    PJM border, while the southern (TVA) and SPP seams keep their measured ~GW of
    export headroom. Like the import ceiling it is a smoothed capability envelope
    the LP clears *below*, not the hourly residual flow (rules #1/#12). Applied
    by :func:`~market_sim.model.transmission.inject_miso_seam_flow_limit` as the
    reverse-direction floor (raised ``min_gen`` lower bound) on each seam's
    negative-output export bands.
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import MISO_SEAM_DIBA
    from market_sim.data.fleet import _hour_to_month_index

    seam_diba = {"MISO": MISO_SEAM_DIBA}.get(iso.upper())
    if not seam_diba:
        return None
    pct = MISO_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)
    ba = _ISO_TO_HOURLY_BA.get(iso.upper())
    if ba is None:
        return None
    path = RAW_DIR / "eia-930-interchange" / f"{ba} interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = pd.DatetimeIndex(frame["local_time"])
    frame = frame[local.year == year]
    if frame.empty:
        return None
    local = pd.DatetimeIndex(frame["local_time"])
    # Map each DIBA to its seam; rows whose DIBA is in no seam (e.g. MHEB, the
    # firm-hydro block) drop out.
    diba_to_seam = {d: s for s, dibas in seam_diba.items() for d in dibas}
    seam = frame["diba"].astype(str).map(diba_to_seam)
    work = pd.DataFrame(
        {
            "seam": seam.to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["seam", "mw"])
    # Net import per seam per timestamp = −sum(interchange over its DIBAs).
    per_ts = work.groupby(["seam", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")

    rm = _hour_to_month_index(hours) + 1  # 1-based month per model hour
    rh = np.arange(hours) % 24
    out: dict[str, np.ndarray] = {}
    for name in seam_diba:
        sub = per_ts[per_ts["seam"] == name]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            vals = g["net_import"].to_numpy()
            if direction == "export":
                vals = -vals  # net export = -net import; pXX export deliverability
            tab[m - 1, h] = np.percentile(vals, pct)
        # Fill any empty (month, hod) bucket with that month's max over hours,
        # then the global max, so the cap is always finite.
        for m in range(12):
            row = tab[m]
            if np.all(np.isnan(row)):
                continue
            tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        # Clip at 0: the cap bounds net flow in ``direction``; a bucket whose pXX
        # is negative (the seam reliably runs the OTHER way then — net import on a
        # net-exporting seam, or net export on the net-importing PJM seam) caps
        # that direction at zero, never forcing the reverse flow. The opposite
        # direction is left to the priced seam's own economics.
        out[name] = np.clip(tab[rm - 1, rh], 0.0, None)
    return out or None


def pjm_net_interchange(year: int) -> np.ndarray | None:
    """Return PJM's hourly net export (MW, export-positive), or ``None``.

    Reads PJM's actual tie-line interchange file for ``year``, sums
    ``actual_flow`` across all 22 ties each hour, and flips the sign so a net
    **export** is positive — the convention :func:`load_demand` expects for an
    interchange schedule (a net export raises the generation the internal fleet
    must serve; a net import lowers it). This is PJM's import/export "node",
    modeled as the *measured* schedule rather than a price-responsive offer,
    so a backcast reproduces the ~40 TWh (2023) the fleet actually exported
    instead of serving internal load alone.

    Returns ``None`` when the file is absent (e.g. forward years), so PJM falls
    back to zero interchange. The series is placed on the model's fixed non-leap
    8760-hour clock (Feb 29 dropped); the lone DST gap is back-filled.
    """
    path = _PJM_INTERCHANGE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["datetime_beginning_ept", "actual_flow"])
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    # Sum actual flow across ties per hour-of-year; negate to export-positive.
    net = np.zeros(HOURS_PER_YEAR, dtype=float)
    counted = np.zeros(HOURS_PER_YEAR, dtype=bool)
    flow = df["actual_flow"].to_numpy(dtype=float)
    valid = (hoy >= 0) & (hoy < HOURS_PER_YEAR) & ~np.isnan(flow)
    np.add.at(net, hoy[valid], flow[valid])
    counted[hoy[valid]] = True
    export = -net
    # Back-fill any hour with no rows (the DST gap) from the previous hour.
    for h in np.nonzero(~counted)[0]:
        export[h] = export[h - 1] if h > 0 else 0.0
    return export


# PJM tie line -> the model border zone it interconnects, so the net export is
# drawn out of the zone that physically carries it (vs. spread system-wide).
# NYISO/NYC cables sit on the EMAAC border; the MISO-west/upper-Midwest ties on
# ComEd; the Indiana/Ohio/Kentucky ties on AEP-Ohio; Michigan on ATSI; the
# Carolinas/Duke/TVA ties on Dominion. Tier 3 (calibration) — approximate
# pending PJM's authoritative tie-to-zone assignment.
_PJM_TIE_ZONE: dict[str, str] = {
    "NYIS": "PJM_EMAAC",
    "NEPT": "PJM_EMAAC",
    "HUDS": "PJM_EMAAC",
    "LIND": "PJM_EMAAC",
    "AMIL": "PJM_ComEd",
    "ALTE": "PJM_ComEd",
    "ALTW": "PJM_ComEd",
    "CWLP": "PJM_ComEd",
    "MEC": "PJM_ComEd",
    "WEC": "PJM_ComEd",
    "MDU": "PJM_ComEd",
    "LAGN": "PJM_ComEd",
    "CIN": "PJM_AEP_Ohio",
    "IPL": "PJM_AEP_Ohio",
    "NIPS": "PJM_AEP_Ohio",
    "SIGE": "PJM_AEP_Ohio",
    "LGEE": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "MECS": "PJM_ATSI",
    "CPLE": "PJM_Dominion",
    "CPLW": "PJM_Dominion",
    "DUK": "PJM_Dominion",
    "TVA": "PJM_Dominion",
}
# Border zone that absorbs any tie not in the map above (keeps total export
# conserved). ComEd is the largest western export interface.
_PJM_TIE_ZONE_DEFAULT: str = "PJM_ComEd"


def pjm_zonal_interchange(year: int, zone_names: list[str]) -> np.ndarray | None:
    """Return PJM's hourly net export by model zone (``(n_zones, T)``, MW).

    Like :func:`pjm_net_interchange`, but attributes each tie's net export to
    the border zone it interconnects (:data:`_PJM_TIE_ZONE`) instead of
    spreading the system total across all zones by load share. So the export
    is drawn out of the zones that physically carry it (ComEd/AEP to the
    Midwest, EMAAC to NYISO, Dominion to the Carolinas), sharpening the
    inter-zone congestion. Row order matches ``zone_names``; the column sum
    equals :func:`pjm_net_interchange`. ``None`` when the file is absent.
    """
    path = _PJM_INTERCHANGE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    if not path.exists():
        return None
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
    )
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    out = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    flow = df["actual_flow"].to_numpy(dtype=float)
    tie_zone = (
        df["tie_line"]
        .map(lambda t: _PJM_TIE_ZONE.get(str(t), _PJM_TIE_ZONE_DEFAULT))
        .to_numpy()
    )
    valid = (hoy >= 0) & (hoy < HOURS_PER_YEAR) & ~np.isnan(flow)
    for z, i in zone_idx.items():
        sel = valid & (tie_zone == z)
        if sel.any():
            np.add.at(out[i], hoy[sel], -flow[sel])  # export-positive
    return out


def pjm_zonal_interchange_envelope(
    year: int, zone_names: list[str], hours: int, percentile: float = 95.0
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return PJM's per-border (month×hod) import/export interchange envelope (MW).

    The per-border-zone analogue of :func:`measured_interchange_envelope` (CAISO),
    built from :func:`pjm_zonal_interchange` (the measured per-tie net export
    attributed to the model border zone it physically interconnects). For each
    border zone and each hour of the run horizon, the ``percentile`` of measured
    net interchange in that hour's (month, hour-of-day) bucket, split into the
    import and export directions (``pjm_zonal_interchange`` is export-positive):

        import_cap[z, t] = P_pctile( max(0, -interchange) | z, month(t), hod(t) )
        export_cap[z, t] = P_pctile( max(0, +interchange) | z, month(t), hod(t) )

    The caller (:func:`market_sim.model.transmission.build_pjm_external_flow_groups`)
    caps each ``PJM_external→border`` link's signed flow asymmetrically — import
    (positive flow, hub→border) at ``import_cap`` and export (negative flow,
    border→hub) at ``export_cap`` — so the priced external node delivers only
    roughly its historical per-border capability in each period rather than ~30 GW
    uncongested in every hour. The dominant direction keeps a generous high-
    percentile ceiling the LP clears below; the minor direction (EMAAC import,
    Dominion export, the interior zones with no tie) collapses toward ~0. A
    measured capability envelope with no fitted constant (rule #12), the price
    still clearing in merit order within it.

    Returns ``(import_cap, export_cap)``, each ``(n_zones, hours)`` MW with row
    order matching ``zone_names``, or ``None`` when the measured tie file is
    absent (a forecast year), in which case the caller leaves the node uncapped.
    """
    zonal = pjm_zonal_interchange(year, zone_names)
    if zonal is None:
        return None
    src_hours = zonal.shape[1]
    src_clock = pd.date_range(f"{year}-01-01", periods=src_hours, freq="h")
    s_month = src_clock.month.to_numpy()
    s_hod = src_clock.hour.to_numpy()
    n = len(zone_names)
    imp_tab = np.zeros((n, 12, 24))
    exp_tab = np.zeros((n, 12, 24))
    for zi in range(n):
        e = zonal[zi]
        imp = np.clip(-e, 0.0, None)  # import into PJM at this border
        exp = np.clip(e, 0.0, None)  # export out of PJM at this border
        for m in range(1, 13):
            for h in range(24):
                sel = (s_month == m) & (s_hod == h)
                if not sel.any():
                    continue
                imp_tab[zi, m - 1, h] = np.percentile(imp[sel], percentile)
                exp_tab[zi, m - 1, h] = np.percentile(exp[sel], percentile)
    # Map the (month, hod) tables onto the run horizon (row 0 = first local hour).
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    rm = clock.month.to_numpy() - 1
    rh = clock.hour.to_numpy()
    import_cap = imp_tab[:, rm, rh]
    export_cap = exp_tab[:, rm, rh]
    return import_cap, export_cap


def _eia930_net_interchange(ba_code: str, year: int) -> np.ndarray | None:
    """Return a BA's hourly net export (MW, export-positive), or ``None``.

    Reads the EIA-930 ``<BA> hourly`` extract's ``Total interchange`` column
    for ``year`` on the model's fixed non-leap 8760-hour clock (the same frame
    the demand series is drawn from, so interchange stays aligned to demand).
    EIA's sign convention is **already** the one :func:`load_demand` expects —
    positive = net export (raises what the internal fleet must serve), negative
    = net import (lowers it) — so the column is returned as-is, with **no** sign
    flip (unlike :func:`pjm_net_interchange`, which negates PJM's
    import-positive tie-line file). Small calendar holes are interpolated.

    Returns ``None`` when the file, the year, or the ``Total interchange``
    column is unavailable, so the caller falls back to zero interchange.
    """
    frame = _eia_hourly_frame_filled(ba_code, year)
    if frame is None or "Total interchange" not in frame.columns:
        return None
    interchange = (
        frame["Total interchange"].interpolate().bfill().ffill().to_numpy(dtype=float)
    )
    if np.isnan(interchange).any() or interchange.shape[0] != HOURS_PER_YEAR:
        return None
    return interchange


def nyiso_net_interchange(year: int) -> np.ndarray | None:
    """Return NYISO's hourly net export (MW, export-positive), or ``None``.

    Sources the measured net interchange from the EIA-930 ``NYIS hourly``
    extract's ``Total interchange`` column (see :func:`_eia930_net_interchange`
    for the sign convention). NYISO is a steady ~16%-of-load net importer (2023:
    −23.45 TWh), so the series is predominantly negative and serving it reduces
    the residual the in-state fleet must generate — the import wedge that would
    otherwise be mis-attributed to internal gas (P9 / playbook §8.2). Mirrors
    :func:`pjm_net_interchange`'s shape; ``None`` when the year is unavailable.
    """
    return _eia930_net_interchange("NYIS", year)


def nyiso_forward_net_import_monthly(
    year: int,
    forward_net_import_twh: dict[int, float] | float | None,
    system_demand: np.ndarray | None = None,
) -> np.ndarray | None:
    """Return NYISO's FORECAST monthly net import (MWh, import-positive), or ``None``.

    The forward analogue of the measured backcast band target
    (:func:`nyiso_net_interchange`). In a forecast there is no measured EIA-930
    schedule to reconcile against, so the band target is the **neighbor's
    forecast net position** supplied by the caller as an annual NYISO net
    *import* in TWh (positive = net import) — derived externally from the
    PJM / Hydro-Québec / Ontario / ISO-NE forward export outlooks
    (NYISO Gold Book imports, neighbor capacity-expansion / interface
    schedules), NOT from any NYISO output. The annual total is shaped to the
    twelve monthly targets by the forecast **load distribution** when
    ``system_demand`` is supplied (imports track load, so the band responds to
    changed conditions — the forward-reproducibility test, CLAUDE.md rule #12),
    else split evenly by each month's hour count.

    Returns ``None`` (band relaxes to the bare priced-seam economics) when no
    forecast is supplied for ``year`` — either ``forward_net_import_twh`` is
    ``None`` or, when it is a per-year mapping, ``year`` is absent from it.

    Args:
        year: Forecast calendar year keying the supplied trajectory.
        forward_net_import_twh: Forecast NYISO annual net import (TWh,
            import-positive). A ``dict[year -> TWh]`` is looked up by ``year``;
            a bare ``float`` is used for every year; ``None`` relaxes the band.
        system_demand: Optional hourly system demand, shape ``(T,)`` or
            ``(n_zones, T)`` (summed over zones), used to weight the monthly
            split. ``None`` falls back to an hour-count (near-flat) split.

    Returns:
        Monthly net-import targets in MWh, shape ``(n_months,)``, or ``None``.
    """
    if forward_net_import_twh is None:
        return None
    if isinstance(forward_net_import_twh, dict):
        annual_twh = forward_net_import_twh.get(year)
        if annual_twh is None:
            annual_twh = forward_net_import_twh.get(str(year))
    else:
        annual_twh = float(forward_net_import_twh)
    if annual_twh is None:
        return None

    from market_sim.data.fleet import _hour_to_month_index

    annual_mwh = float(annual_twh) * 1.0e6  # TWh -> MWh
    month_index = _hour_to_month_index(HOURS_PER_YEAR)
    n_months = int(month_index.max()) + 1

    if system_demand is not None:
        demand = np.asarray(system_demand, dtype=float)
        if demand.ndim == 2:
            demand = demand.sum(axis=0)
        demand = demand.reshape(-1)[:HOURS_PER_YEAR]
        weight = np.zeros(n_months, dtype=float)
        np.add.at(weight, month_index[: demand.size], demand)
    else:
        weight = np.zeros(n_months, dtype=float)
        np.add.at(weight, month_index, np.ones(HOURS_PER_YEAR))

    total = weight.sum()
    if total <= 0.0:
        return None
    return annual_mwh * (weight / total)


def neiso_net_interchange(year: int) -> np.ndarray | None:
    """Return NEISO's hourly net export (MW, export-positive), or ``None``.

    Sources the measured net interchange from the EIA-930 ``ISNE hourly``
    extract's ``Total interchange`` column (see :func:`_eia930_net_interchange`
    for the sign convention). ISO-NE is a steady ~9%-of-load net importer (2024:
    −10.30 TWh — the HQ Phase II + New Brunswick + NYISO wedge), so serving the
    series reduces the residual the internal fleet must generate (P9 / playbook
    §8.2). Mirrors :func:`pjm_net_interchange`'s shape; ``None`` when the year
    is unavailable.
    """
    return _eia930_net_interchange("ISNE", year)


# ISOs whose measured net interchange is served as a system-wide scalar
# schedule (spread across zones by load share), as opposed to PJM's per-border-
# zone tie attribution or ERCOT's demand-aligned DC-tie series. CAISO is
# deliberately excluded — its imports are supply modeled by the WECC_import
# node, not netted into demand (playbook §8.1); ERCOT is islanded and carries
# its DC ties through its own EIA-930 extract.
_SCALAR_INTERCHANGE_ISOS: dict[str, Callable[[int], np.ndarray | None]] = {
    "NYISO": nyiso_net_interchange,
    "NEISO": neiso_net_interchange,
}
