"""NY-NJ PAR interchange attribution — the published registry and the split.

NYISO's posting *"NY-NJ PAR Interchange Percentages, Operational Base Flow (OBF),
and other MW Offsets"*
(``https://www.nyiso.com/documents/20142/2268509/NY-NJ_PAR_Interchange_and_OBF.pdf``,
percentages effective 5/1/2017; OBF identically 0 MW since 11/1/2019) directs a
published percentage of the PJM-AC interchange over eight named PARs, and closes
the rule: *"If a PAR is out of service, interchange normally distributed over
that PAR will be modeled over the free-flowing western AC tie lines between
NYISO and PJM."*

This module holds the two published objects that rule needs — the PAR registry
(name, PTID, interface, share) and the interface → model-zone landing map — plus
the hourly, availability-conditioned split they generate. **It contains no
chosen MW and no fitted value**: eight published percentages, eight published
PTID identities, and a published outage state (rule 20 ``[R-DOF]``).

Identification (nyiso-127 addendum §2)
--------------------------------------
The PAR ↔ PTID identity comes from MIS **P-33 ``outSched``**, whose
``Equipment Name`` matches the posting's PAR names exactly. It cannot come from
P-34 ``ParFlows``, which carries a bare numeric ``Point ID`` and no facility
name. ``outSched`` supplies the in-service state as well, and P-34 corroborates
it exactly: a PAR ``outSched`` reports out measures 0.00 MW in every interval.

What the measured state turns out to be
---------------------------------------
**ABC-B and ABC-C (Farragut TR11 / TR12) have been out of service since
2018-01-15 and are out for 100 % of every hour of 2023-2025.** Fourteen of the
21 ABC points therefore revert west across the whole training window, so the
attribution is **G 46 % / J 7 % / A 47 %**, not the nameplate 47 / 21 / 32.

Rule 13 ``[R-MEASURED]``: this is an INPUT — published percentages × published
availability — regenerable for a forward year from forward drivers, never an
outcome pinned to a residual.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

logger = logging.getLogger(__name__)

PAR_DIR = RAW_DIR / "NYISO" / "par-data"

# The eight PARs the posting names, each resolved to its published PTID by EXACT
# match against the outSched ``Equipment Name``.
#   PTID: (posting PAR, outSched Equipment Name, interface, published share)
PAR_REGISTRY: dict[int, tuple[str, str, str, float]] = {
    25370: ("3500", "RAMAPO___345_345_PAR3500", "ramapo", 0.16),
    25371: ("4500", "RAMAPO___345_345_PAR4500", "ramapo", 0.16),
    101017299: ("E", "P_HAWTHO-WALDWICK_230_E-2257", "jk", 0.05),
    101016633: ("F", "WALDWICK-HILLSDAL_230_F2258", "jk", 0.05),
    101016389: ("O", "WALDWICK-FAIRLAWN_230_O2267", "jk", 0.05),
    25641: ("A", "GOETHALS_345A_345B_BK 1N", "abc", 0.07),
    25044: ("B", "FARRAGUT_345B_345A_TR11", "abc", 0.07),
    25043: ("C", "FARRAGUT_345C_345A_TR12", "abc", 0.07),
}

# Which model zone each interface's share lands in. Every landing is a cited
# NYISO zone assignment (nyiso-126 finding §1.3), not a modelling choice:
#   ramapo -> Ramapo 345 kV substation, ZONE G (2025 Gold Book Table IV-1b p.127)
#   jk     -> South Mahwah / Waldwick (Con Ed), ZONE G (Operating Study W2023-24 p.9)
#   abc    -> Goethals / Farragut, ZONE J (same study p.9)
#   west   -> Homer City-Stolle Rd / Falconer, ZONE A (Gold Book Tbl IV-1b p.129)
INTERFACE_ZONE: dict[str, str] = {
    "ramapo": "Capital_Hudson",
    "jk": "Capital_Hudson",
    "abc": "NYC",
    "west": "Upstate_West",
}

# The share the posting leaves on the free-flowing western AC ties when every
# PAR is in service: 1 - (2x16 % + 3x5 % + 3x7 %). A derived identity, not a
# parameter — it is whatever the eight published percentages do not cover.
WEST_RESIDUAL_SHARE: float = 1.0 - sum(share for *_, share in PAR_REGISTRY.values())


def load_par_outages() -> pd.DataFrame:
    """Read the committed published PAR outage windows.

    Returns:
        The ``NYISO_par_outages.csv`` frame with parsed window bounds.

    Raises:
        FileNotFoundError: The intake is absent — the mechanism never silently
            no-ops (the pjm-119 silent-overlay-degradation lesson).
    """
    path = PAR_DIR / "NYISO_par_outages.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"nyiso PAR attribution: {path} is absent — run "
            "scripts/data/fetch_nyiso_par_data.py (the mechanism never silently "
            "no-ops)"
        )
    return pd.read_csv(path, parse_dates=["outage_start", "outage_end"])


def par_out_mask(
    outages: pd.DataFrame, ptid: int, index: pd.DatetimeIndex
) -> np.ndarray:
    """Boolean out-of-service mask for one PAR over ``index``.

    The union of every published window. ``outSched`` re-posts an open outage on
    each daily snapshot and rolls its ``Scheduled In`` forward as the outage is
    extended, so the windows for one long-term outage nest rather than tile;
    the union is the state either way.

    Args:
        outages: Frame from :func:`load_par_outages`.
        ptid: Facility PTID.
        index: Hourly local-clock index to evaluate over.

    Returns:
        ``(len(index),)`` boolean array, True where the PAR is out of service.
    """
    sub = outages[outages["ptid"] == ptid]
    mask = np.zeros(len(index), dtype=bool)
    for start, end in zip(sub["outage_start"], sub["outage_end"], strict=True):
        mask |= (index >= start) & (index < end)
    return mask


def zone_shares(outages: pd.DataFrame, year: int) -> dict[str, np.ndarray]:
    """Hourly share of the PJM-AC interchange landing in each model zone.

    Implements the posting's closure rule verbatim: an in-service PAR carries its
    published share into its interface's zone; an out-of-service PAR's share
    reverts to the free-flowing western AC ties. The shares sum to 1.0 in every
    hour by construction.

    Args:
        outages: Frame from :func:`load_par_outages`.
        year: Backcast year (the index is that year's real local calendar, so a
            leap year is keyed correctly before any mapping to the model clock).

    Returns:
        ``{model_zone: (hours,) share array}``.
    """
    index = pd.date_range(
        pd.Timestamp(year, 1, 1),
        pd.Timestamp(year + 1, 1, 1),
        freq="h",
        inclusive="left",
    )
    out: dict[str, np.ndarray] = {
        zone: np.zeros(len(index)) for zone in set(INTERFACE_ZONE.values())
    }
    for ptid, (_par, _name, interface, share) in PAR_REGISTRY.items():
        live = (~par_out_mask(outages, ptid, index)).astype(float)
        out[INTERFACE_ZONE[interface]] += live * share
        # The posting's own closure rule: an out-of-service PAR's share goes west.
        out[INTERFACE_ZONE["west"]] += (1.0 - live) * share
    out[INTERFACE_ZONE["west"]] += WEST_RESIDUAL_SHARE
    return out


# Every P-32 ``SCH -`` row, attributed to the model zone its ties physically land
# in. The NYCA aggregation is A-E -> Upstate_West, F-G -> Capital_Hudson,
# H-I -> Lower_Hudson, J -> NYC, K -> Long_Island (iso_configs NYISO docstring);
# Lower_Hudson has no external ties and correctly has no border link.
# ``SCH - PJ - NY`` is absent here because it is the one row that does NOT land in
# a single zone — it is split hourly by the published PAR shares (zone_shares).
SEAM_ROW_ZONE: dict[str, str] = {
    # Gold Book external interconnections (tie landing points):
    "SCH - OH - NY": "Upstate_West",  # Ontario / Niagara, zones A-B
    "SCH - HQ - NY": "Upstate_West",  # Chateauguay-Massena, zone D
    "SCH - HQ_CEDARS": "Upstate_West",  # Cedars Rapids, zone D
    "SCH - NE - NY": "Capital_Hudson",  # New Scotland / Pleasant Valley AC, F-G
    # The downstate DC/VFT cables — the nyiso-125 map, unchanged.
    "SCH - PJM_HTP": "NYC",
    "SCH - PJM_VFT": "NYC",
    "SCH - PJM_NEPTUNE": "Long_Island",
    "SCH - NPX_CSC": "Long_Island",
    "SCH - NPX_1385": "Long_Island",
}

# The PJM AC row, split by the PAR shares rather than landed in one zone.
PJM_AC_ROW: str = "SCH - PJ - NY"

# An ACCOUNTING duplicate of ``SCH - HQ - NY``, never attributed (it would double
# the HQ seam). Carried by name so a future map edit cannot silently include it.
ACCOUNTING_DUPLICATE: str = "SCH - HQ_IMPORT_EXPORT"


def _model_clock(hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(month_of_hour, hour_of_day)`` on the model's fixed clock.

    The model's calendar is a FIXED NON-LEAP 8760-hour year keyed to 2023, shared
    by every model year.

    Args:
        hours: Dispatch horizon.

    Returns:
        Two ``(hours,)`` integer arrays.
    """
    cal = pd.date_range("2023-01-01", periods=hours, freq="h")
    return cal.month.to_numpy(), cal.hour.to_numpy()


def attributed_zone_net(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    """Attribute every posted seam row to a model zone, hour by hour.

    Each single-landing row goes wholly to its zone; ``SCH - PJ - NY`` is split by
    the published, availability-conditioned PAR shares. The accounting duplicate
    is excluded. Rows are keyed by LOCAL wall-clock throughout — never
    positionally — and the PAR share series is joined on that same key.

    Args:
        frame: The ``nyiso-interface-flows`` clean partition for one year.
        year: The year ``frame`` covers (keys the PAR availability calendar).

    Returns:
        One row per (local hour, model zone) with the attributed net MW.

    Raises:
        ValueError: A posted ``SCH -`` row is attributed zero times or more than
            once (kill gate K9), or the PJM AC row is missing.
    """
    src = frame.copy()
    src["local_hour"] = pd.to_datetime(src["interval_start_local"]).dt.floor("h")

    posted = {r for r in src["interface"].unique() if str(r).startswith("SCH -")}
    mapped = set(SEAM_ROW_ZONE) | {PJM_AC_ROW, ACCOUNTING_DUPLICATE}
    unattributed = posted - mapped
    if unattributed:
        raise ValueError(
            f"nyiso_seam_par_attribution {year}: posted seam row(s) "
            f"{sorted(unattributed)} are attributed to no zone (kill gate K9) — "
            "a silently dropped row would delete real seam capability"
        )
    if PJM_AC_ROW not in posted:
        raise ValueError(
            f"nyiso_seam_par_attribution {year}: {PJM_AC_ROW!r} is absent from "
            "the clean partition (the mechanism never silently no-ops)"
        )

    parts: list[pd.DataFrame] = []
    single = src[src["interface"].isin(SEAM_ROW_ZONE)].copy()
    single["zone"] = single["interface"].map(SEAM_ROW_ZONE)
    parts.append(single[["local_hour", "zone", "flow_mw"]])

    pjm = (
        src[src["interface"] == PJM_AC_ROW]
        .groupby("local_hour")["flow_mw"]
        .mean()  # the DST fall-back hour repeats one label; average it
        .rename("pjm_mw")
    )
    shares = zone_shares(load_par_outages(), year)
    index = pd.date_range(
        pd.Timestamp(year, 1, 1),
        pd.Timestamp(year + 1, 1, 1),
        freq="h",
        inclusive="left",
    )
    for zone, arr in shares.items():
        share = pd.Series(arr, index=index, name="share")
        joined = pd.concat([pjm, share], axis=1, join="inner")
        parts.append(
            pd.DataFrame(
                {
                    "local_hour": joined.index,
                    "zone": zone,
                    "flow_mw": joined["pjm_mw"].to_numpy() * joined["share"].to_numpy(),
                }
            )
        )

    allrows = pd.concat(parts, ignore_index=True)
    return allrows.groupby(["local_hour", "zone"], as_index=False)["flow_mw"].sum()


def attributed_envelope_by_zone(
    frame: pd.DataFrame, year: int, hours: int, percentile: float
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Directional hourly envelope per zone from the attributed seam net.

    Same construction as the armed ``nyiso_seam_deliverability_envelope`` — the
    ``percentile`` of the directionally-clipped net within each (month x
    hour-of-day) bin — applied to the attributed net rather than to a single
    zone's own ties. Feb 29 is dropped so a leap year contributes the model's
    calendar.

    Args:
        frame: The ``nyiso-interface-flows`` clean partition for one year.
        year: The year ``frame`` covers.
        hours: Dispatch horizon (length of the returned arrays).
        percentile: Envelope percentile (``constants.NYISO_SEAM_FLOW_PERCENTILE``).

    Returns:
        ``{zone: (import_cap, export_cap)}``, each ``(hours,)`` and non-negative.
    """
    net = attributed_zone_net(frame, year)
    net = net[~((net["local_hour"].dt.month == 2) & (net["local_hour"].dt.day == 29))]
    net["_mo"] = net["local_hour"].dt.month.to_numpy()
    net["_hr"] = net["local_hour"].dt.hour.to_numpy()

    month_of_hour, hour_of_day = _model_clock(hours)
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for zone, sub in net.groupby("zone"):
        imp = np.clip(sub["flow_mw"].to_numpy(), 0.0, None)
        exp = np.clip(-sub["flow_mw"].to_numpy(), 0.0, None)
        src_mo, src_hr = sub["_mo"].to_numpy(), sub["_hr"].to_numpy()
        import_cap = np.zeros(hours, dtype=float)
        export_cap = np.zeros(hours, dtype=float)
        for m in range(1, 13):
            for h in range(24):
                bin_src = (src_mo == m) & (src_hr == h)
                bin_dst = (month_of_hour == m) & (hour_of_day == h)
                if not bin_src.any() or not bin_dst.any():
                    continue
                import_cap[bin_dst] = np.percentile(imp[bin_src], percentile)
                export_cap[bin_dst] = np.percentile(exp[bin_src], percentile)
        out[str(zone)] = (import_cap, export_cap)
    return out


def nyiso_par_attributed_ttc_hourly(
    ttc: np.ndarray,
    iso_config,
    year: int,
    hours: int,
    percentile: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Replace every NYISO border-link static with the attributed seam envelope.

    SUPERSEDES ``data.nyiso_seam_envelope.nyiso_seam_ttc_hourly`` (rule 19
    ``[R-ONE-MECH]``) — it computes that mechanism's two links from the same
    measured rows, so the caller applies exactly one of the two.

    **The envelope is NOT clipped to the incumbent static.** The armed nyiso-125
    mechanism clips, because there the static is the *rating* of the very ties
    being measured and a deliverability envelope cannot exceed a rating. Here the
    statics are lumped multi-neighbour stand-ins for exactly this quantity, and
    on ``NYC`` the attributed tie set is strictly larger than the static's (the
    ABC AC path is real and absent from the 1,000 MW HTP+VFT rating), so clipping
    would delete a physically-real path. The cap is the measured p90 of NYISO's
    own schedules over the full attributed tie set, and that is the object.

    Args:
        ttc: Static per-link capability, ``(n_links,)`` or ``(hours, n_links)``,
            after any earlier overrides so this composes with them.
        iso_config: The NYISO ``ISOConfig``, **after** ``apply_interchange_topology``
            has appended the external node.
        year: Backcast year whose clean partition is read.
        hours: Dispatch horizon (rows of the output matrices).
        percentile: Envelope percentile; defaults to
            ``constants.NYISO_SEAM_FLOW_PERCENTILE``.

    Returns:
        ``(ttc_hourly, ttc_import)`` — the ``(hours, n_links)`` forward (import)
        cap and the ``(hours, n_links)`` reverse (export) cap.

    Raises:
        FileNotFoundError: No ``nyiso-interface-flows`` clean partition for
            ``year``, or no border link matched. Callers are gated on
            ``ScenarioConfig.nyiso_seam_par_attribution``, so silently keeping the
            static would leave the run claiming a measured input it never read
            (the pjm-119 silent-overlay-degradation lesson).
    """
    from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE

    pct = NYISO_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)

    try:
        from scripts.lib.clean_io import read_clean

        frame = read_clean(
            "nyiso-interface-flows", iso="NYISO", year=year, validate=False
        )
    except Exception as exc:  # noqa: BLE001 — re-raised as the gated error below
        raise FileNotFoundError(
            f"nyiso_seam_par_attribution {year}: could not read the "
            f"'nyiso-interface-flows' clean partition ({exc}) — run "
            "scripts/regenerate_clean.py nyiso-interface-flows (the mechanism "
            "never silently no-ops)"
        ) from exc
    if frame is None or frame.empty:
        raise FileNotFoundError(
            f"nyiso_seam_par_attribution {year}: empty 'nyiso-interface-flows' "
            "clean partition (the mechanism never silently no-ops)"
        )

    static = np.asarray(ttc, dtype=float)
    ttc_hourly = (
        np.broadcast_to(static, (hours, static.shape[-1])).copy()
        if static.ndim == 1
        else static.copy()
    )
    ttc_import = ttc_hourly.copy()

    link_idx = {link.to_zone: i for i, link in enumerate(iso_config.links)}
    envelopes = attributed_envelope_by_zone(frame, year, hours, pct)

    n_capped = 0
    for zone, (import_cap, export_cap) in envelopes.items():
        i = link_idx.get(zone)
        if i is None:
            continue
        logger.info(
            "nyiso_seam_par_attribution %d: %s import cap p50 %.0f MW "
            "(incumbent static p50 %.0f), export cap p50 %.0f MW",
            year,
            zone,
            float(np.median(import_cap)),
            float(np.median(ttc_hourly[:, i])),
            float(np.median(export_cap)),
        )
        ttc_hourly[:, i] = import_cap
        ttc_import[:, i] = export_cap
        n_capped += 1

    if not n_capped:
        raise FileNotFoundError(
            f"nyiso_seam_par_attribution {year}: no border link matched the "
            "attributed zones — the external node is absent from iso_config "
            "(the mechanism never silently no-ops)"
        )
    return ttc_hourly, ttc_import
