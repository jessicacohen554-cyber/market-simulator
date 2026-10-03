"""Read the ``transfer-interface-limits`` clean datatype and build hourly link caps.

The model's consumption seam for PJM's measured internal interface transfer
limits (PJM Data Miner 2 ``transfer_limits_and_flows`` →
``scripts/data/curate_transfer_interface_limits.py`` →
``data/clean/transfer-interface-limits``) — the PJM analogue of
:mod:`market_sim.data.gtc`. The one public builder,
:func:`pjm_interface_ttc_hourly`, expands the static per-link TTC array to a
``(hours, n_links)`` forward-direction cap matrix on the links whose static
``ttc_mw`` was seeded from these postings
(``constants.PJM_INTERFACE_LINK_MAP``), leaving every other link static.

Hourly cap construction (per link, all quantities measured):

* the link's forward (west→east congestion direction) cap each hour is the
  **elementwise min of its mapped published series** — where an interface
  publishes both pre- and post-contingency limits, both are
  simultaneously-enforced security limits and the operative capability is
  the tighter one;
* non-positive published limits clamp to **0** (no secure transfer that
  hour) — never a negative bound, which would FORCE counterflow;
* the reverse direction keeps the static capability (the published limits
  are directional security limits on the west→east cut, not reverse
  ratings) — the same asymmetric-seam convention as the ERCOT measured GTC
  overlay;
* an hour a series does not cover (never the case for the committed dense
  2023-25 partitions; a guard for partial future drops) rides the static
  rating.

This reconstruction is formulaic over the published series — nothing is
scaled to a price or volume residual (rules #13/#14). Callers gate on
``ScenarioConfig.pjm_measured_interface_limits`` / ``pjm_east_interface_cut``
(backcast overlays, default off). A wholly missing partition RAISES rather than
degrading to the static ratings (pjm-119): the clean tree is gitignored and
disposable, so a fresh container starts without it, and the previous silent
fallback let the pjm-118 PJM keeper solve with these overlays off while its
recorded config and attestation still claimed them — see
``docs/records/pjm/FINDING-pjm119-silent-overlay-degradation-2026-07.md``. An individual
series absent from a PRESENT partition still rides that link's static rating.
Forecast years never call this: the static seeds (2024 means of the same feed)
are the forward story.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_INTERFACE_LINK_MAP

logger = logging.getLogger(__name__)

DATATYPE = "transfer-interface-limits"

#: Fraction of covered hours in which the MEASURED flow may exceed a published
#: limit before that year's series is judged inadmissible as an enforceable
#: security limit (``ScenarioConfig.pjm_interface_feed_admissibility_gate``).
#:
#: DECLARED EX ANTE and never swept (rule 29 ``[R-SCREEN]`` clause (c); pjm-167
#: PRECOMMIT ``PRECOMMIT-pjm167-interface-feed-admissibility-2026-09-06.md``).
#: 5 % is the conventional materiality bar, not a tuned value: the partition it
#: produces on PJM's "Average Eastern" series is IDENTICAL for any threshold in
#: (2.1 %, 17.5 %) — an eightfold range — so no result selects it.
#:
#: Why a limit is judged by its own flows. A transfer limit is a statement that
#: flow above it is insecure; a posting the realized flow exceeds in a QUARTER
#: of all hours is not that statement. Measured on PJM "Average Eastern"
#: (pjm-167 §2.2): 2019 1.6 %, 2020 18.7 %, 2021 27.9 %, 2022 17.5 %,
#: 2023 2.1 %, 2024 0.0 %, 2025 0.0 % — and the distinct-value count over ~8760
#: hours moves 7,063 / 1 / 85 / 58 / 5,677 / 8,767 / 8,750 across the same
#: years. Pre-2023 the feed posts a near-static seasonal LIMIT-SET value; from
#: 2024 it posts the hourly-averaged TLC the mechanism's docstring describes.
#: They are different quantities under one series name, which is exactly rule 14
#: ``[R-ACCURATE]``'s named exception ("a different time/area aggregation"), and
#: enforcing the early vintage verbatim is what rule 14 calls making results
#: LESS reflective of reality.
PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC: float = 0.05


def interface_series_admissibility(
    frame: pd.DataFrame, name: str
) -> tuple[bool, dict[str, float]]:
    """Judge one published limit series against its own measured flows.

    The clean datatype carries ``transfer_mw`` beside ``limit_mw`` and its
    schema reserves that column for exactly this use — *"carried ONLY for
    crosswalk sanity checks (binding frequency / flow direction), never as a
    dispatch target"*. Nothing here reads a model output, a price or a scoring
    target: it compares two columns of one published feed to each other.

    A series is INADMISSIBLE when the measured flow exceeds the posted limit in
    more than :data:`PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC` of the hours where
    both are present. Hours missing either column are excluded rather than
    counted as passes, so a sparse series cannot pass by absence.

    Args:
        frame: The year's dense hourly interface frame from
            :func:`load_interface_hourly`.
        name: The published series name, e.g. ``"Average Eastern"``.

    Returns:
        ``(admissible, diagnostics)``. ``diagnostics`` carries
        ``exceedance_frac``, ``n_hours``, ``n_exceed``, ``max_excess_mw`` and
        ``n_distinct_limits`` — the last reported for provenance only, never
        applied as a second test (rule 19 ``[R-ONE-MECH]``: one criterion).
        An absent or empty series is reported ``admissible=True`` with
        ``n_hours=0``, leaving the caller's existing missing-series contract
        untouched.
    """
    sub = frame[frame["interface"] == name]
    diag: dict[str, float] = {
        "exceedance_frac": 0.0,
        "n_hours": 0.0,
        "n_exceed": 0.0,
        "max_excess_mw": 0.0,
        "n_distinct_limits": 0.0,
    }
    if sub.empty:
        return True, diag
    limit = pd.to_numeric(sub["limit_mw"], errors="coerce").to_numpy(dtype=float)
    flow = (
        pd.to_numeric(sub["transfer_mw"], errors="coerce").to_numpy(dtype=float)
        if "transfer_mw" in sub.columns
        else np.full(limit.shape, np.nan)
    )
    both = np.isfinite(limit) & np.isfinite(flow)
    diag["n_distinct_limits"] = float(np.unique(limit[np.isfinite(limit)]).size)
    if not both.any():
        # No measured flow to judge against — the test cannot fire, so the
        # series keeps the pre-gate behaviour rather than being refused blind.
        return True, diag
    excess = flow[both] - limit[both]
    diag["n_hours"] = float(both.sum())
    diag["n_exceed"] = float((excess > 0.0).sum())
    diag["exceedance_frac"] = diag["n_exceed"] / diag["n_hours"]
    diag["max_excess_mw"] = float(excess.max())
    return diag["exceedance_frac"] <= PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC, diag


def load_interface_hourly(iso: str, year: int) -> pd.DataFrame | None:
    """Return the year's dense hourly interface-limit frame, or ``None``.

    A missing partition (raw drop not curated) is logged and returns ``None``
    so callers degrade to the static link ratings.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning("transfer-interface-limits: scripts.lib.clean_io unavailable")
        return None
    try:
        return read_clean(DATATYPE, iso=iso.upper(), year=year)
    except FileNotFoundError:
        logger.info(
            "transfer-interface-limits: no clean partition for %s %d (run "
            "scripts/data/curate_transfer_interface_limits.py)",
            iso,
            year,
        )
        return None


def _series_hourly(frame: pd.DataFrame, name: str, hours: int) -> np.ndarray | None:
    """One published series' ``(hours,)`` limit, NaN where uncovered.

    Returns ``None`` when the series is absent from the partition entirely
    (an older drop) so the caller can fall back to the static rating and log
    it. Vectorized — no loop over hours.
    """
    sub = frame[frame["interface"] == name]
    if sub.empty:
        return None
    out = np.full(hours, np.nan, dtype=float)
    idx = sub["hour"].to_numpy(dtype=int)
    keep = idx < hours
    out[idx[keep]] = sub["limit_mw"].to_numpy(dtype=float)[keep]
    return out


#: The Manual-03 EASTERN reactive transfer interface series (PJM Manual 03
#: §3.8 Rev 71: Breinigsville–Alburtis ×2, Juniata–Alburtis,
#: Lauschtown–Hosensack, Peach Bottom–Limerick, Rock Springs–Keeney,
#: Lackawanna–Hopatcong — the EHV cut into the eastern Mid-Atlantic). The
#: DataMiner2 feed posts its hourly-averaged TLC limit as "Average Eastern".
PJM_EASTERN_INTERFACE_SERIES = "Average Eastern"


def pjm_eastern_interface_hourly(
    year: int, hours: int, admissibility_gate: bool = False
) -> np.ndarray:
    """The measured EMAAC-import-cut hourly limit (``pjm_east_interface_cut``).

    Returns the ``(hours,)`` "Average Eastern" published limit — the joint
    cap for the Central_PA→EMAAC + SWMAAC→EMAAC link pair (the reduced
    network's EMAAC import cut; see the ScenarioConfig field docstring and
    diagnosis §10.5). Uncovered hours (never the case for the committed dense
    2023–25 partitions) ride ``+inf`` so the group row is simply non-binding
    there rather than inventing a static joint rating.

    RAISES rather than returning ``None`` when the input is missing (pjm-119).
    This function is only ever reached from a site already gated on
    ``ScenarioConfig.pjm_east_interface_cut``, so an absent partition is a
    misconfiguration, not a modelling choice — and its input lives in the
    CURATED ``data/clean`` tree, which is gitignored and disposable, so a fresh
    container starts without it. The previous ``None``-and-warn contract let the
    caller skip the cut while the run's recorded config, and the keeper
    attestation's DOF ledger, still claimed it as a live measured input: the
    pjm-118 keeper was solved and scored with this cut silently off, worth 17→40
    C3c tail hours (diagnosis §10.7), and its residual written up as a
    summer-scarcity structural miss. Guarding here rather than at the call site
    protects every present and future caller — the guard must not depend on the
    analyst remembering. Same posture as ``pjm_da_virtual_bids``. See
    ``docs/records/pjm/FINDING-pjm119-silent-overlay-degradation-2026-07.md``.

    ``admissibility_gate`` (GATED default-off,
    ``ScenarioConfig.pjm_interface_feed_admissibility_gate``; pjm-167): judge
    the year's posted series against its OWN measured flows through
    :func:`interface_series_admissibility` before enforcing it, and where it
    fails, return an all-``+inf`` array so the joint cut is non-binding and the
    two links keep their static per-link TTCs — the same posture a forecast year
    already takes. This is rule 14 ``[R-ACCURATE]``'s named exception, not a
    licence to drop measured data: the pre-2023 vintage of this feed is a
    near-static seasonal limit-set posting, a DIFFERENT QUANTITY from the
    post-2023 hourly TLC under one series name, and the model enforced it as a
    hard LP bound below flows PJM actually carried (pjm-167 §2). The
    fall-through is LOGGED AT WARNING with its full arithmetic and is selected
    by the feed alone — never by a price, a residual or any model output.

    Raises:
        FileNotFoundError: No clean partition for ``year``, or the partition
            carries no "Average Eastern" series.
    """
    frame = load_interface_hourly("PJM", year)
    if frame is None or frame.empty:
        raise FileNotFoundError(
            f"pjm_east_interface_cut {year}: no transfer-interface-limits clean "
            "partition — run scripts/regenerate_clean.py "
            "transfer-interface-limits (the mechanism never silently no-ops)"
        )
    measured = _series_hourly(frame, PJM_EASTERN_INTERFACE_SERIES, hours)
    if measured is None:
        raise FileNotFoundError(
            f"pjm_east_interface_cut {year}: the transfer-interface-limits "
            f"clean partition carries no {PJM_EASTERN_INTERFACE_SERIES!r} "
            "series — run scripts/regenerate_clean.py "
            "transfer-interface-limits (the mechanism never silently no-ops)"
        )
    if admissibility_gate:
        ok, diag = interface_series_admissibility(frame, PJM_EASTERN_INTERFACE_SERIES)
        if not ok:
            logger.warning(
                "pjm_east_interface_cut %d: %r is INADMISSIBLE as an enforceable "
                "security limit and the joint EMAAC import cut is NOT APPLIED "
                "this year (the links keep their static per-link TTCs, the "
                "forecast-lane posture). The measured flow exceeds the posted "
                "limit in %.1f%% of %d covered hours (bar %.1f%%), by up to "
                "%.0f MW; the series takes %d distinct values over the year. "
                "This is a LOUD, RECORDED fall-through under "
                "ScenarioConfig.pjm_interface_feed_admissibility_gate — not the "
                "silent degradation pjm-119 forbids.",
                year,
                PJM_EASTERN_INTERFACE_SERIES,
                100.0 * diag["exceedance_frac"],
                int(diag["n_hours"]),
                100.0 * PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC,
                diag["max_excess_mw"],
                int(diag["n_distinct_limits"]),
            )
            return np.full(hours, np.inf, dtype=float)
    out = np.where(np.isnan(measured), np.inf, measured)
    # Non-positive published limits clamp to 0 (no secure transfer that
    # hour), matching the per-link overlay's convention.
    return np.maximum(out, 0.0)


#: The Manual-03 AP SOUTH reactive transfer interface series. PJM posts it as
#: pre- AND post-contingency limits; both are simultaneously-enforced security
#: limits, so the operative hourly capability is their elementwise MIN — the
#: same convention :func:`pjm_interface_ttc_hourly` applies to the per-link
#: overlay (``constants.PJM_INTERFACE_LINK_MAP`` maps West_APS→SWMAAC to this
#: same pair).
PJM_APSOUTH_INTERFACE_SERIES: tuple[str, ...] = (
    "AP-South Pre-Contingency",
    "AP-South Post-Contingency",
)


def pjm_apsouth_interface_hourly(year: int, hours: int) -> np.ndarray:
    """The measured western→MAD joint cut hourly limit (``pjm_apsouth_interface_cut``).

    Returns the ``(hours,)`` AP-South published limit — the elementwise min of
    the pre- and post-contingency postings — as the joint cap for the
    West_APS→SWMAAC + West_APS→Dominion link pair. ``constants.py``'s own
    ``PJM_INTERFACE_LINK_MAP`` note records why the pair, not one link, is the
    faithful reading: *"AP-South is the aggregate western→MAD 500 kV flowgate,
    one of several parallel paths this 8-zone mesh splits across
    West_APS→SWMAAC and West_APS→Dominion"*. Applying it per-link to the seeded
    link alone leaves the parallel path on a 3,000 MW static, so the LP's
    west→MAD capability is ``AP-South(t) + 3,000`` — roughly 1.8× the published
    flowgate, all of the excess Dominion-facing
    (``FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md`` §4).

    Uncovered hours ride ``+inf`` so the group row is simply non-binding there
    rather than inventing a static joint rating; non-positive published limits
    clamp to 0 (no secure transfer), never a negative bound that would FORCE
    counterflow. Same contract as :func:`pjm_eastern_interface_hourly`.

    RAISES rather than returning ``None`` when the input is missing (pjm-119):
    this function is only reached from a site already gated on
    ``ScenarioConfig.pjm_apsouth_interface_cut``, so an absent partition is a
    misconfiguration, not a modelling choice — and a mechanism the recorded
    config and the DOF ledger both claim must never silently no-op.

    Raises:
        FileNotFoundError: No clean partition for ``year``, or the partition
            carries neither AP-South series.
    """
    frame = load_interface_hourly("PJM", year)
    if frame is None or frame.empty:
        raise FileNotFoundError(
            f"pjm_apsouth_interface_cut {year}: no transfer-interface-limits "
            "clean partition — run scripts/regenerate_clean.py "
            "transfer-interface-limits (the mechanism never silently no-ops)"
        )
    stack = [
        series
        for name in PJM_APSOUTH_INTERFACE_SERIES
        if (series := _series_hourly(frame, name, hours)) is not None
    ]
    if not stack:
        raise FileNotFoundError(
            f"pjm_apsouth_interface_cut {year}: the transfer-interface-limits "
            f"clean partition carries none of {PJM_APSOUTH_INTERFACE_SERIES} "
            "— run scripts/regenerate_clean.py transfer-interface-limits "
            "(the mechanism never silently no-ops)"
        )
    measured = np.nanmin(np.vstack(stack), axis=0)
    out = np.where(np.isnan(measured), np.inf, measured)
    return np.maximum(out, 0.0)


def pjm_interface_ttc_hourly(
    ttc: np.ndarray,
    iso_config,
    year: int,
    hours: int,
    admissibility_gate: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Expand static TTC to measured hourly forward caps on the mapped links.

    Args:
        ttc: Static per-link capability, shape ``(n_links,)`` — after any
            static overrides (``pjm_congestion``) so the reverse direction
            and uncovered-hour fill stay consistent with the run's statics.
        iso_config: The PJM :class:`ISOConfig` (supplies link zone pairs).
        year: Backcast year to read the clean partition for.
        hours: Dispatch horizon (rows of the output matrix).

    Returns:
        ``(ttc_hourly, ttc_import)`` — the ``(hours, n_links)`` forward-
        direction cap matrix and the static ``(n_links,)`` array kept as the
        reverse-direction bound.

    ``admissibility_gate`` (GATED default-off,
    ``ScenarioConfig.pjm_interface_feed_admissibility_gate``; pjm-167): each
    mapped series is judged against its OWN measured flows by
    :func:`interface_series_admissibility`, and one that fails is DROPPED from
    that link's stack — so a link whose every mapped series fails keeps its
    static rating, while a link with one good and one bad series (the pre/post
    pairs) still rides the good one. Measured on the six consumed series
    (pjm-167 §2.2 addendum): AEP/DOM, both AP-South and both Bedington postings
    clear at 0.0-1.0 % in EVERY year 2019-2025, and "Average Central" at
    <=2.5 %; only "Average Eastern" (18.7 / 27.9 / 17.5 % in 2020/21/22) and
    "Average Western" (6.2 / 6.7 / 9.7 %) fail, and only there. The gate is
    therefore INERT for 2019 and 2023-2025 on every link, so every committed
    backcast keeper is byte-identical under it.

    Raises:
        FileNotFoundError: No clean partition for ``year``, or the partition
            carries none of the mapped series. Callers are gated on
            ``ScenarioConfig.pjm_measured_interface_limits``, so silently
            keeping the static TTC would leave the run claiming a measured
            input it never read (pjm-119 — see
            :func:`pjm_eastern_interface_hourly` and
            ``docs/records/pjm/FINDING-pjm119-silent-overlay-degradation-2026-07.md``).
    """
    frame = load_interface_hourly("PJM", year)
    if frame is None or frame.empty:
        raise FileNotFoundError(
            f"pjm_measured_interface_limits {year}: no transfer-interface-limits "
            "clean partition — run scripts/regenerate_clean.py "
            "transfer-interface-limits (the mechanism never silently no-ops)"
        )

    ttc = np.asarray(ttc, dtype=float)
    ttc_hourly = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    link_idx = {
        (link.from_zone, link.to_zone): i for i, link in enumerate(iso_config.links)
    }
    n_mapped = 0
    for zones, series_names in PJM_INTERFACE_LINK_MAP.items():
        i = link_idx.get(zones)
        if i is None:
            logger.warning(
                "transfer-interface-limits %d: link %s->%s not in topology — skipped",
                year,
                zones[0],
                zones[1],
            )
            continue
        stack = []
        for name in series_names:
            if admissibility_gate:
                ok, diag = interface_series_admissibility(frame, name)
                if not ok:
                    logger.warning(
                        "pjm_measured_interface_limits %d: series %r is "
                        "INADMISSIBLE as an enforceable security limit and is "
                        "DROPPED from %s->%s (the link keeps its static rating "
                        "unless another mapped series carries it). The measured "
                        "flow exceeds the posted limit in %.1f%% of %d covered "
                        "hours (bar %.1f%%), by up to %.0f MW; the series takes "
                        "%d distinct values over the year. Loud, recorded "
                        "fall-through under "
                        "ScenarioConfig.pjm_interface_feed_admissibility_gate.",
                        year,
                        name,
                        zones[0],
                        zones[1],
                        100.0 * diag["exceedance_frac"],
                        int(diag["n_hours"]),
                        100.0 * PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC,
                        diag["max_excess_mw"],
                        int(diag["n_distinct_limits"]),
                    )
                    continue
            measured = _series_hourly(frame, name, hours)
            if measured is None:
                logger.warning(
                    "transfer-interface-limits %d: series %r absent from the "
                    "partition — %s->%s falls back to the static rating for "
                    "that series",
                    year,
                    name,
                    zones[0],
                    zones[1],
                )
                continue
            stack.append(measured)
        if not stack:
            continue
        # Operative hourly cap = min over the link's simultaneously-enforced
        # published limits; uncovered hours (all-NaN — impossible for the
        # dense committed partitions) ride the static rating; non-positive
        # published limits clamp to 0 (no secure forward transfer), never a
        # negative bound (which would force counterflow).
        with np.errstate(invalid="ignore"):
            combined = np.nanmin(np.vstack(stack), axis=0)
        combined = np.where(np.isnan(combined), ttc[i], combined)
        ttc_hourly[:, i] = np.maximum(combined, 0.0)
        n_mapped += 1
        logger.info(
            "transfer-interface-limits %d: %s->%s forward cap follows %s "
            "(hourly %0.0f-%0.0f MW, mean %0.0f; static %0.0f kept on the "
            "reverse direction)",
            year,
            zones[0],
            zones[1],
            " min ".join(series_names),
            float(ttc_hourly[:, i].min()),
            float(ttc_hourly[:, i].max()),
            float(ttc_hourly[:, i].mean()),
            ttc[i],
        )
    if n_mapped == 0:
        raise FileNotFoundError(
            f"pjm_measured_interface_limits {year}: partition present but none "
            "of the mapped interface series were found — re-pull the raw drop "
            "and run scripts/regenerate_clean.py transfer-interface-limits "
            "(the mechanism never silently no-ops)"
        )
    return ttc_hourly, ttc


def _fixed_pst_hour(local: pd.Series, year: int) -> np.ndarray:
    """Prevailing-Pacific naive hour starts -> index on NWPP's fixed-PST 8760 clock.

    The CAISO partition sits on CAISO's prevailing-time clock; NWPP's LP runs
    on fixed PST with Feb 29 dropped (``market_sim.data.eia930.demand``). A
    DST hour moves back one hour; the merged fall-back row is read as its
    daylight occurrence and the filled spring-forward row shifts forward. Rows
    landing outside ``year`` (or on Feb 29) return ``-1``.
    """
    aware = pd.DatetimeIndex(local).tz_localize(
        "America/Los_Angeles", ambiguous=True, nonexistent="shift_forward"
    )
    pst = aware.tz_convert("Etc/GMT+8").tz_localize(None)
    hrs = ((pst - pd.Timestamp(year, 1, 1)) // pd.Timedelta(hours=1)).to_numpy()
    leap = pd.Timestamp(year, 12, 31).dayofyear == 366
    if leap:
        feb29 = (pst.month == 2) & (pst.day == 29)
        hrs = np.where(feb29, -1, np.where(pst.month > 2, hrs - 24, hrs))
    hrs = np.where(pst.year == year, hrs, -1)
    return np.asarray(hrs, dtype=int)


def _nwpp_cap_series(
    frame: pd.DataFrame,
    names: tuple[str, ...],
    sign: float,
    year: int,
    hours: int,
    fixed_clock: bool,
) -> np.ndarray:
    """Sum of ``names`` x ``sign`` per model hour, clamped at 0; NaN where any is absent.

    ``fixed_clock`` True reads ``hour`` directly (the NWPP partition is
    curated on fixed PST); False remaps the prevailing-time ``interval_start_local``
    (the CAISO partition). Vectorized: no loop over hours.
    """
    total = np.zeros(hours, dtype=float)
    for name in names:
        sub = frame[frame["interface"] == name]
        out = np.full(hours, np.nan, dtype=float)
        if not sub.empty:
            if fixed_clock:
                idx = sub["hour"].to_numpy(dtype=int)
                vals = sub["limit_mw"].to_numpy(dtype=float)
            else:
                idx = _fixed_pst_hour(sub["interval_start_local"], year)
                vals = sub["limit_mw"].to_numpy(dtype=float)
                keep = (idx >= 0) & (idx < hours)
                s = pd.Series(vals[keep]).groupby(idx[keep]).mean()
                idx, vals = s.index.to_numpy(dtype=int), s.to_numpy(dtype=float)
            keep = (idx >= 0) & (idx < hours)
            out[idx[keep]] = vals[keep]
            if not fixed_clock:
                # The prevailing->fixed remap leaves the fall-back standard
                # hour empty (its row merged into the daylight one): fill an
                # ISOLATED one-hour interior gap from its neighbours (the CAISO
                # spec's own max_fill_hours = 1); longer gaps stay NaN.
                gap = np.isnan(out)
                lone = gap.copy()
                lone[1:] &= ~gap[:-1]
                lone[:-1] &= ~gap[1:]
                lone[[0, -1]] = False
                out[lone] = 0.5 * (
                    out[np.flatnonzero(lone) - 1] + out[np.flatnonzero(lone) + 1]
                )
        total = total + out
    return np.maximum(sign * total, 0.0)


def nwpp_seam_limits_hourly(
    year: int, hours: int
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Measured hourly caps on NWPP's priced seams (``nwpp_seam_measured_limits``).

    Returns ``{seam: (import_cap, export_cap)}``, each ``(hours,)`` MW >= 0 on
    NWPP's fixed-PST clock, for every seam in
    ``constants.NWPP_SEAM_LIMIT_SERIES`` (``CAISO_NEVP`` is absent and keeps
    its registered rating). ``import`` = counterparty -> NWPP.

    * ``WECC_CAN``: BPA's BC Intertie operating limit (NWPP partition).
    * ``CAISO_COI``: CAISO's hourly OTC on MALIN500_ISL + CASCADE_ITC where
      OASIS has the hour (CAISO partition, 2023-06-19 on); every other hour
      ``NWPP_COI_CAISO_SHARE`` x BPA's whole-path COI operating limit.

    A measured operating limit is a physical operating condition (rule 13,
    the outage-window kind of input); nothing here reads a flow, a schedule
    or a model output. An hour neither source covers raises: the NWPP
    partition is dense over 2019-2025, so a gap means a broken curation, not
    a modelling choice.

    Raises:
        FileNotFoundError: The NWPP partition for ``year`` is absent, or a
            year from 2023 lacks the CAISO partition, or a cap has an
            uncovered hour (the mechanism never silently no-ops, pjm-119).
    """
    from market_sim.config.constants import (
        NWPP_COI_CAISO_SHARE,
        NWPP_COI_PATH_SERIES,
        NWPP_SEAM_LIMIT_SERIES,
    )

    frames = {"NWPP": load_interface_hourly("NWPP", year)}
    if frames["NWPP"] is None or frames["NWPP"].empty:
        raise FileNotFoundError(
            f"nwpp_seam_measured_limits {year}: no NWPP transfer-interface-limits "
            "clean partition — run scripts/regenerate_clean.py --solve-profile NWPP"
        )
    frames["CAISO"] = load_interface_hourly("CAISO", year)
    if frames["CAISO"] is None and year >= 2023:
        raise FileNotFoundError(
            f"nwpp_seam_measured_limits {year}: no CAISO transfer-interface-limits "
            "clean partition (MALIN500_ISL OTC) — run scripts/regenerate_clean.py "
            "--solve-profile NWPP"
        )
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for seam, dirs in NWPP_SEAM_LIMIT_SERIES.items():
        caps: dict[str, np.ndarray] = {}
        for direction, (part, names, sign) in dirs.items():
            frame = frames[part]
            cap = (
                _nwpp_cap_series(frame, names, sign, year, hours, part == "NWPP")
                if frame is not None
                else np.full(hours, np.nan)
            )
            if seam == "CAISO_COI":
                path_name, path_sign = NWPP_COI_PATH_SERIES[direction]
                path = _nwpp_cap_series(
                    frames["NWPP"], (path_name,), path_sign, year, hours, True
                )
                cap = np.where(np.isnan(cap), NWPP_COI_CAISO_SHARE * path, cap)
            if np.isnan(cap).any():
                raise FileNotFoundError(
                    f"nwpp_seam_measured_limits {year}: {seam} {direction} cap has "
                    f"{int(np.isnan(cap).sum())} uncovered hour(s) — re-curate "
                    "transfer-interface-limits"
                )
            caps[direction] = cap
        out[seam] = (caps["import"], caps["export"])
        logger.info(
            "nwpp_seam_measured_limits %d: %s import cap mean %0.0f MW, "
            "export cap mean %0.0f MW",
            year,
            seam,
            float(caps["import"].mean()),
            float(caps["export"].mean()),
        )
    return out
