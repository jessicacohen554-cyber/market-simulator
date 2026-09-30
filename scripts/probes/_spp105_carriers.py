"""SPP-105 candidate gas-family carriers for the zero-LP re-clear (``_spp105_gas_outage_hourly_phase0``).

Record: ``docs/handoffs/DESIGN-spp-105-gas-family-outage-2026-09-30.md`` s4. Each carrier is a
deterministic function of the keeper's own rebuilt arrays and SPP's published hourly Natural Gas
outage; none has a tunable. They are INSTRUMENTS for the design card, never configs.

* ``stat_off_covered`` -- the rule-19 repair alone: the statistical WEFOR is removed from the gas
  classes that already carry CAMPD event windows (CC_REGULAR / CC_CHP / ST_GAS / ST_CHP; POF is
  already dropped there by ``coal_drop_pof``). CTs untouched.
* ``crow_residual`` -- the gas-family replacement: EVERY gas row's statistical outage-type terms
  (WEFOR + POF) are removed and replaced by SPP's measured residual
  ``R(t) = max(0, SPP_gas(t) - E(t))``, ``E`` the keeper's own CAMPD event-window gas MW, allocated
  across gas rows pro rata to each row's ANNUAL statistical outage-type MW (the incumbent's own
  class-rate key, time-invariant, so the seasonal and hourly shape is SPP's, not the model's).
  Allocation is capped at each row's available MW; the unplaceable remainder is reported.
"""

from __future__ import annotations

import numpy as np

COVERED = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP")


def _stat(ctx: dict) -> np.ndarray:
    """Per row x hour statistical outage-type MW (WEFOR + POF) on live hours."""
    return np.where(ctx["live"], ctx["un"]["full"] - ctx["un"]["event"], 0.0)


def stat_off_covered(ctx: dict) -> np.ndarray:
    """Keeper stack with the statistical WEFOR restored on CAMPD-covered gas classes."""
    sel = ctx["gas"] & np.isin(ctx["cls"], COVERED)
    a = ctx["av0"].copy()
    a[sel] = np.minimum(a[sel] + _stat(ctx)[sel], ctx["pm"][sel, None])
    return a


def crow_residual(ctx: dict) -> np.ndarray:
    """Keeper stack with gas statistical terms replaced by SPP's measured residual."""
    gas = ctx["gas"]
    st = _stat(ctx)
    a = ctx["av0"].copy()
    a[gas] = np.minimum(a[gas] + st[gas], ctx["pm"][gas, None])
    ev = np.where(ctx["live"], ctx["un"]["event"], 0.0)[gas].sum(0)
    spp = ctx["spp"]
    r = np.where(np.isfinite(spp), np.maximum(0.0, spp - ev), 0.0)
    w = st[gas].mean(1)
    w = w / w.sum()
    take = np.minimum(w[:, None] * r[None, :], np.where(ctx["live"][gas], a[gas], 0.0))
    a[gas] = a[gas] - take
    ctx.setdefault("diag", {})["crow_residual"] = {
        "binding_hour_share": float((r > 0).mean()),
        "residual_gw_mean": float(r.mean() / 1e3),
        "replaced_stat_gw_mean": float(st[gas].sum(0).mean() / 1e3),
        "unplaced_gw_mean": float((r - take.sum(0)).mean() / 1e3),
    }
    return a


def _built(arm: str):
    """The BUILT arm's own rebuilt availability (the code path, not the instrument)."""

    def f(ctx: dict) -> np.ndarray:
        from scripts.probes._spp105_gas_outage_hourly_phase0 import rebuild_armed

        a = rebuild_armed(ctx["y"], ctx["cache"], arm)
        return a["pmax"].astype(float)[:, None] * a["availability"].astype(float)

    return f


CARRIERS = {
    "stat_off_covered": stat_off_covered,
    "crow_residual": crow_residual,
    "A_built": _built("A"),
    "B_built": _built("B"),
}
