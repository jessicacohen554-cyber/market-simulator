"""NYISO external-seam deliverability envelope from measured MIS P-32 schedules.

The NYISO analogue of :func:`~market_sim.data.gtc.ercot_gtc_ttc_hourly` and
:func:`~market_sim.data.transfer_interface_limits.pjm_interface_ttc_hourly`:
expand the static per-link TTC array into an hourly, DIRECTIONAL cap on the
external border links, read off NYISO's own measured external schedules.

Why (nyiso-124 §6.1 / nyiso-125 Phase 0)
----------------------------------------
The model hosts every NYISO seam on one external star node
(``NYISO_external``), so the only thing allocating imports across the state is
the border links' TTCs — and those are flat, symmetric and time-invariant. The
consequence, measured on the committed network layer: the three downstate
border links sit at their bound in 98-100 % of ALL hours of all three training
years (a flat 3,800 MW against a measured downstate median of 1,870 / 1,772 /
2,040 MW) while ``NYISO_external>Upstate_West`` runs net EXPORT against a
measured import. The seam's NET reconciles to 2-11 % while ~1.8-2.0 GW of
surplus import lands EAST of the Central-East cutset, so the model's CE link
carries util 0.253 where the real interface carries 0.591.

What this module caps, and what it deliberately does NOT
--------------------------------------------------------
**Only the two border links whose external ties land unambiguously in a single
NYISO load zone** — ``NYC`` (Zone J) and ``Long_Island`` (Zone K). Their
envelopes are attribution-invariant and carry ZERO identification freedom.

``Upstate_West`` and ``Capital_Hudson`` are **REFUSED ON IDENTIFICATION**
(rule 20 ``[R-DOF]``) and keep their static ratings. ``SCH - PJ - NY`` is the
one posting row that spans the Central-East cutset — the PJM AC interface
carries the Ramapo 345 kV PARs and Waldwick 230 kV ties into Zone G (east) AND
the Homer City-Stolle Road / Falconer ties into Zone A (west) — and no public
source separates them: NYISO's P-32 posts the interface total, and PJM's own
tie-line file buckets all four NYISO-facing ties as ``NYIS``/``NEPT``/``HUDS``/
``LIND`` with the AC ties as ONE row
(:data:`~market_sim.data.eia930.envelopes._PJM_TIE_ZONE`). The split brackets
``Capital_Hudson``'s import envelope across 45-955 / 0-916 / 0-1,134 MW in
2023 / 2024 / 2025 — the whole range that matters, on the link carrying the
defect. Choosing inside that bracket would be choosing a number so the CE link
starts binding, which is exactly what rules 1 / 11 forbid.

The split-invariant JOINT (Upstate_West + Capital_Hudson) cap needs no split
and was measured to be inert: the model's joint AC-seam net import
(+597 / +80 / -89 MW p50) already sits far below the measured envelope
(1,818 / 1,706 / 1,243 MW p50). It is therefore not built.

Evidence: ``scripts/probes/_nyiso125_seam_envelope.py`` /
``results/calibration/_nyiso125_seam_envelope.json`` /
``results/calibration/PREREG-nyiso125-seam-envelope-2026-08-04.md``.

Admissibility (rule 13 ``[R-MEASURED]``)
----------------------------------------
The envelope is a per-neighbour deliverability CAPABILITY, not an outcome
pinned back into the model: it bounds what the seam may deliver and leaves the
LP to choose what it does deliver. It regenerates for a forward year from the
forward tie set by the same frozen formula and responds to changed conditions
(it moves 974 -> 828 -> 975 MW on ``NYC`` and 1,012 -> 986 -> 990 MW on
``Long_Island`` across 2023-25 purely from measured behaviour, and a new tie
such as CHPE is picked up automatically). It is the same object class the repo
already carries for MISO (``miso_seam_envelope_merit_cap``) and PJM
(``inject_pjm_seam_flow_limit``) — but built, per rule 25 ``[R-ISO-SCOPE]``,
entirely from NYISO's own market with NYISO's own parameters.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATATYPE = "nyiso-interface-flows"

# The tie -> model landing-zone map for the links this module caps. Each P-32
# external schedule is placed by the NYCA load zone its ties physically land
# in (NYISO Gold Book external interconnections — the same tie geography
# already cited in interchange.spec.IMPORT_NODE_LINKS["NYISO"]):
#   SCH - PJM_HTP      Hudson Transmission Project  -> Zone J
#   SCH - PJM_VFT      Linden VFT                   -> Zone J
#   SCH - PJM_NEPTUNE  Neptune                      -> Zone K
#   SCH - NPX_CSC      Cross Sound Cable            -> Zone K
#   SCH - NPX_1385     Northport-Norwalk 1385       -> Zone K
# Every one lands in exactly ONE NYISO load zone, so the attribution carries no
# freedom. The zones NOT here are refused on identification (module docstring).
NYISO_SEAM_TIE_LANDING: dict[str, tuple[str, ...]] = {
    "NYC": ("SCH - PJM_HTP", "SCH - PJM_VFT"),
    "Long_Island": ("SCH - PJM_NEPTUNE", "SCH - NPX_CSC", "SCH - NPX_1385"),
}

# ``SCH - HQ_IMPORT_EXPORT`` is an ACCOUNTING duplicate of ``SCH - HQ - NY``
# (equal within 0.5 MW in 40.7 / 77.9 / 90.9 % of hours; corr 0.977 / 0.989 /
# 0.993; the only SCH row carrying the +/-9,999 unbounded sentinel on its
# negative limit). It names no tie this module reads, and is listed here so a
# future landing-zone entry cannot silently double the HQ seam.
NYISO_SEAM_ACCOUNTING_DUPLICATE: str = "SCH - HQ_IMPORT_EXPORT"


def _model_clock(hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(month_of_hour, hour_of_day)`` on the model's fixed clock.

    The model's calendar is a FIXED NON-LEAP 8760-hour year keyed to 2023
    (``build_ercot_as_withholding._CALENDAR``), shared by every model year.

    Args:
        hours: Dispatch horizon.

    Returns:
        Two ``(hours,)`` integer arrays.
    """
    cal = pd.date_range("2023-01-01", periods=hours, freq="h")
    return cal.month.to_numpy(), cal.hour.to_numpy()


def seam_envelope_by_zone(
    frame: pd.DataFrame, hours: int, percentile: float
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Build each identified landing zone's directional hourly envelope.

    Within each (month x hour-of-day) bin, the ``percentile`` of the
    directionally-clipped measured net schedule — the same construction
    :func:`~market_sim.data.eia930.envelopes.measured_interchange_envelope` and
    the MISO/PJM seam limits use, on NYISO's own postings. Source hours are
    binned by their OWN local (month, hour); Feb 29 is dropped so a leap year
    contributes the same calendar as the model's clock.

    Args:
        frame: The ``nyiso-interface-flows`` clean partition for one year.
        hours: Dispatch horizon (length of the returned arrays).
        percentile: Envelope percentile (``constants.NYISO_SEAM_FLOW_PERCENTILE``).

    Returns:
        ``{zone: (import_cap, export_cap)}`` for every zone in
        :data:`NYISO_SEAM_TIE_LANDING` whose ties are all present in ``frame``,
        each array ``(hours,)`` and non-negative. Zones whose ties are missing
        are omitted (the caller decides whether that is fatal).
    """
    ts = pd.to_datetime(frame["interval_start_local"])
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    src = frame.loc[keep].copy()
    src["_mo"] = ts.loc[keep].dt.month.to_numpy()
    src["_hr"] = ts.loc[keep].dt.hour.to_numpy()

    month_of_hour, hour_of_day = _model_clock(hours)
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for zone, ties in NYISO_SEAM_TIE_LANDING.items():
        present = set(src["interface"].unique())
        missing = [t for t in ties if t not in present]
        if missing:
            logger.warning(
                "nyiso seam envelope: landing zone %s is missing interface(s) "
                "%s from the clean partition — zone skipped",
                zone,
                missing,
            )
            continue
        sel = src[src["interface"].isin(ties)]
        # One row per (month, day, hour) x interface; sum the zone's ties within
        # the hour BEFORE the directional clip, exactly as the seam nets.
        net = (
            sel.groupby(["_mo", sel["interval_start_local"].dt.day, "_hr"])["flow_mw"]
            .sum()
            .reset_index()
        )
        net.columns = ["_mo", "_dy", "_hr", "net_mw"]
        imp = np.clip(net["net_mw"].to_numpy(), 0.0, None)
        exp = np.clip(-net["net_mw"].to_numpy(), 0.0, None)
        src_mo, src_hr = net["_mo"].to_numpy(), net["_hr"].to_numpy()

        import_cap = np.zeros(hours, dtype=float)
        export_cap = np.zeros(hours, dtype=float)
        for m in range(1, 13):
            for h in range(24):
                bin_src = (src_mo == m) & (src_hr == h)
                if not bin_src.any():
                    continue
                bin_dst = (month_of_hour == m) & (hour_of_day == h)
                if not bin_dst.any():
                    continue
                import_cap[bin_dst] = np.percentile(imp[bin_src], percentile)
                export_cap[bin_dst] = np.percentile(exp[bin_src], percentile)
        out[zone] = (import_cap, export_cap)
    return out


def nyiso_seam_ttc_hourly(
    ttc: np.ndarray,
    iso_config,
    year: int,
    hours: int,
    percentile: float | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Expand the static border-link TTC to the measured seam envelope.

    Replaces — never stacks on (rule 19 ``[R-ONE-MECH]``) — the flat symmetric
    static rating on ``NYISO_external>NYC`` and ``NYISO_external>Long_Island``
    with NYISO's own measured directional hourly deliverability envelope. Every
    other link, including the two refused on identification, keeps the array it
    came in with.

    The envelope is clipped to the incumbent static: a *deliverability*
    envelope cannot exceed the *rating*. Measured across 2023-2025 this guard
    never binds (the ``NYC`` envelope maxes at 975 MW against a 1,000 MW static;
    ``Long_Island`` at 1,190 / 1,190 / 1,125 against 1,200), and it is here as a
    monotonicity property, not a fitted clip.

    Args:
        ttc: Static per-link capability, ``(n_links,)`` or ``(hours, n_links)``,
            after any earlier overrides so this composes with them.
        iso_config: The NYISO :class:`ISOConfig`, **after**
            ``apply_interchange_topology`` has appended the external node (the
            border links must already be in ``iso_config.links``).
        year: Backcast year whose clean partition is read.
        hours: Dispatch horizon (rows of the output matrices).
        percentile: Envelope percentile; defaults to
            ``constants.NYISO_SEAM_FLOW_PERCENTILE``.

    Returns:
        ``(ttc_hourly, ttc_import)`` — the ``(hours, n_links)`` forward
        (import) cap and the ``(hours, n_links)`` reverse (export) cap, the
        latter applied by the LP as ``-ttc_import``.

    Raises:
        FileNotFoundError: No ``nyiso-interface-flows`` clean partition for
            ``year``, or it carries none of the mapped landing zones. Callers
            are gated on ``ScenarioConfig.nyiso_seam_deliverability_envelope``,
            so silently keeping the static TTC would leave the run claiming a
            measured input it never read (the pjm-119 silent-overlay-degradation
            lesson: the mechanism never silently no-ops).
    """
    from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE

    pct = NYISO_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)

    try:
        from scripts.lib.clean_io import read_clean

        frame = read_clean(DATATYPE, iso="NYISO", year=year, validate=False)
    except Exception as exc:  # noqa: BLE001 — re-raised as the gated error below
        raise FileNotFoundError(
            f"nyiso_seam_deliverability_envelope {year}: could not read the "
            f"{DATATYPE!r} clean partition ({exc}) — run "
            "scripts/regenerate_clean.py nyiso-interface-flows (the mechanism "
            "never silently no-ops)"
        ) from exc
    if frame is None or frame.empty:
        raise FileNotFoundError(
            f"nyiso_seam_deliverability_envelope {year}: empty {DATATYPE!r} "
            "clean partition — run scripts/regenerate_clean.py "
            "nyiso-interface-flows (the mechanism never silently no-ops)"
        )

    static = np.asarray(ttc, dtype=float)
    ttc_hourly = (
        np.broadcast_to(static, (hours, static.shape[-1])).copy()
        if static.ndim == 1
        else static.copy()
    )
    ttc_import = ttc_hourly.copy()

    link_idx = {link.to_zone: i for i, link in enumerate(iso_config.links)}
    envelopes = seam_envelope_by_zone(frame, hours, pct)
    if not envelopes:
        raise FileNotFoundError(
            f"nyiso_seam_deliverability_envelope {year}: the {DATATYPE!r} clean "
            f"partition carries none of {sorted(NYISO_SEAM_TIE_LANDING)} — run "
            "scripts/regenerate_clean.py nyiso-interface-flows (the mechanism "
            "never silently no-ops)"
        )

    n_capped = 0
    for zone, (import_cap, export_cap) in envelopes.items():
        i = link_idx.get(zone)
        if i is None:
            logger.warning(
                "nyiso seam envelope %d: no border link lands in %s — skipped "
                "(has apply_interchange_topology run?)",
                year,
                zone,
            )
            continue
        incumbent = ttc_hourly[:, i]
        capped_imp = np.minimum(import_cap, incumbent)
        capped_exp = np.minimum(export_cap, incumbent)
        logger.info(
            "nyiso_seam_deliverability_envelope %d: %s import cap p50 %.0f MW "
            "(static %.0f, binds below it in %.1f %% of hours, mean %.1f MW "
            "removed); export cap p50 %.0f MW",
            year,
            zone,
            float(np.median(capped_imp)),
            float(np.median(incumbent)),
            float((capped_imp < incumbent).mean()) * 100.0,
            float(np.clip(incumbent - capped_imp, 0.0, None).mean()),
            float(np.median(capped_exp)),
        )
        ttc_hourly[:, i] = capped_imp
        ttc_import[:, i] = capped_exp
        n_capped += 1

    if not n_capped:
        raise FileNotFoundError(
            f"nyiso_seam_deliverability_envelope {year}: no border link matched "
            f"{sorted(NYISO_SEAM_TIE_LANDING)} — the external node is absent "
            "from iso_config (the mechanism never silently no-ops)"
        )
    return ttc_hourly, ttc_import
