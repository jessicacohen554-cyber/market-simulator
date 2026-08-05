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

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

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
