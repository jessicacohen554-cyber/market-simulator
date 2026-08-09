"""ERCOT-181 position-tail support construction (PRECOMMIT-ercot181 §2/§3).

The armed measured offer surfaces read their ladders by within-plant position
via ``np.interp`` over ``LADDER_QUANTILES`` (0.1..0.9), which END-CLAMPS at
the p90 rung — the measured population's top decile maps to no readable
position. :func:`tail_support` completes the position axis with THE SAME
STATISTIC on its own measured support: the MW-weighted empirical quantile
function's distinct step points above the frozen grid's top.

Conventions (fixed by the precommit, mirroring the parent derives' own):
multipliers rounded to 3 decimals (the ladders' ``round(m, 3)``), x
(cumulative-MW fraction) rounded to 6 (the contpct node precedent), x
strictly increasing after rounding (equal x keeps the later, higher value —
the step function's right limit). Values arrive HCAP-clipped by the parent
population construction; no clip, clamp, or grid choice is added here.
"""

from __future__ import annotations

import numpy as np

#: Provenance tag of the position-tail artifact vintage (both-direction
#: vintage guards in ``offer_surfaces.py`` key on this exact string).
POSITIONTAIL_TAG = "positiontail-netload-bins"

#: The frozen grid's top point — tails carry only x strictly above this.
GRID_TOP = 0.9


def tail_support(
    mult: np.ndarray, mw: np.ndarray, above: float = GRID_TOP
) -> list[list[float]]:
    """Distinct (cum-MW-fraction, multiplier) step points above ``above``.

    Args:
        mult: Segment prices as effective-HR multipliers (HCAP-clipped by the
            caller's own population construction).
        mw: Segment MW weights, parallel to ``mult``.
        above: Exclusive lower bound on the cumulative-MW fraction
            (the frozen grid's top point).

    Returns:
        ``[[x, v], ...]`` with x strictly increasing in ``(above, 1]`` —
        empty when the population is empty or carries no mass above the
        bound (the zero-support rule: the reader keeps the frozen end-clamp
        byte-identical).
    """
    mult = np.asarray(mult, dtype=float)
    mw = np.asarray(mw, dtype=float)
    ok = np.isfinite(mult) & np.isfinite(mw) & (mw > 0)
    if not ok.any():
        return []
    v = mult[ok]
    w = mw[ok]
    order = np.argsort(v, kind="stable")
    v = np.round(v[order], 3)
    w = w[order]
    cum = np.cumsum(w) / w.sum()
    # one step point per distinct rounded value: the empirical CDF at the
    # END of that value's mass (the quantile function's step edge)
    last = np.flatnonzero(np.r_[v[1:] != v[:-1], True])
    xs = np.round(cum[last], 6)
    ys = v[last]
    out: list[list[float]] = []
    for x, y in zip(xs, ys):
        if x <= above:
            continue
        if out and x <= out[-1][0]:
            out[-1] = [float(x), float(y)]  # equal x after rounding: keep later
        else:
            out.append([float(x), float(y)])
    return out
