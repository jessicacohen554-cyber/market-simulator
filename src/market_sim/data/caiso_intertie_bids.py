"""CAISO measured price-insensitive INTERTIE ceiling, from OASIS DAM public bids.

Loader for the frozen artifact
``data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv`` produced by
``scripts/data/derive_caiso_intertie_selfsched.py`` (caiso-151; specified at
caiso-150 §F). The derive script's module docstring carries the full
construction, the identification wall, and the frozen honesty gates — this
module only maps the (month × hod) table onto the model's hour grid.

The series measures, from CAISO's own as-submitted day-ahead bids
(OASIS ``PUB_DAM_GRP``, tariff §6.5.2.2, 90-day lag), how much intertie MW is
offered **price-insensitively**::

    ceiling[month, hod] = ( ALL intertie self-schedule MW, both directions,
                            unsigned )
                        + ( import-classified economic MW offered at or below
                            $0/MWh )

Both limbs together are the floor's OWN definition of price-taking conduct
("self-scheduled **or** bid at/below $0/MWh", CPUC D.20-06-028), and both are
taken generously, so the table is a one-sided CEILING:
``ceiling[t] >= (true price-insensitive IMPORT position)[t]`` in every hour.
Direction is not identifiable in the masked feed (caiso-150 §B), and that is
precisely why the consuming mechanism uses only the upper-bound property — it
can remove forcing the measured record cannot support, never add any.

Rule 13 ``[R-MEASURED]``: OASIS publishes continuously at a 90-day lag, so the
same quantity regenerates for any forward year and responds to changed
conditions. The table is a pooled climatology and is applied identically in a
backcast and a forecast year — it carries no same-year outcome.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.paths import PROCESSED_DIR

#: The frozen (month × hod) artifact (rule 23 ``[R-FROZEN-DERIVE]``).
CAISO_INTERTIE_SELFSCHED_CSV = PROCESSED_DIR / "caiso_intertie_selfsched_ceiling.csv"


def measured_intertie_selfsched_ceiling(
    iso: str, year: int, hours: int
) -> np.ndarray | None:
    """Return CAISO's measured price-insensitive intertie ceiling, per model hour.

    Expands the pooled (month × hod) table onto the model's fixed non-leap
    calendar — :func:`~market_sim.data.fleet._hour_to_month_index` for the month
    and ``hour % 24`` for the hour-of-day, the same calendar the LP, the hydro
    budgets and :func:`~market_sim.data.eia930.envelopes.measured_firm_import_shape`
    use — so the ceiling aligns hour-for-hour with the dispatch it bounds.

    ``year`` is accepted for signature symmetry with the other measured
    interchange series and is deliberately unused: the artifact is a pooled
    climatology (equal-weight across the train years), which is what makes it
    apply unchanged in a forecast year.

    Returns ``(hours,)`` MW, or ``None`` when the ISO is not CAISO or the
    artifact is absent — in which case the caller leaves the floor unclipped
    (byte-identical).
    """
    if iso.upper() != "CAISO":
        return None
    if not CAISO_INTERTIE_SELFSCHED_CSV.exists():
        return None
    from market_sim.data.fleet import _hour_to_month_index

    frame = pd.read_csv(CAISO_INTERTIE_SELFSCHED_CSV)
    tab = np.full((12, 24), np.nan)
    tab[frame["month"].to_numpy() - 1, frame["hod"].to_numpy()] = frame[
        "ceiling_mw"
    ].to_numpy(dtype=float)
    if not np.all(np.isfinite(tab)):
        return None  # an incomplete table is never partially applied
    rm = _hour_to_month_index(hours)  # 0-based month per model hour
    rh = np.arange(hours) % 24
    return np.clip(tab[rm, rh], 0.0, None)
