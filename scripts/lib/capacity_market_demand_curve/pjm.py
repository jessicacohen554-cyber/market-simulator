"""PJM capacity-market-demand-curve spec (reference ISO implementation).

PJM's RPM Base Residual Auction (BRA) prices against a sloped "Variable
Resource Requirement" (VRR) demand curve, anchored on Net CONE (Net Cost of
New Entry) and an IRM (Installed Reserve Margin) target, published per
delivery year in the "Planning Period Parameters" filings.

Native -> canonical metric map: the retrieval CSV may already use canonical
names (``net_cone``, ``irm``, ``price_cap``, ``curve_point``); ``vrr_point`` is
accepted as an alias for ``curve_point``. One curve per delivery year (no
locality split — PJM's VRR curve is RTO-wide).

This module is the template the other ISO modules (nyiso/isone/miso/caiso)
follow: declare an :class:`IsoSpec` and register it. It uses the default
unified-CSV parser.
"""

from __future__ import annotations

from . import IsoSpec, register

_METRIC_ALIASES = {
    "vrr_point": "curve_point",
}

SPEC = register(
    IsoSpec(
        iso="PJM",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
