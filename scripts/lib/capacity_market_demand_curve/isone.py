"""ISO-NE capacity-market-demand-curve spec.

ISO-NE's Forward Capacity Auction (FCA) prices against a downward-sloping
demand curve anchored on Net CONE, an Installed Capacity Requirement (ICR),
and an Auction Starting Price; since the "Competitive Auctions with Sponsored
Policy Resources" (CASPR) / Pay-for-Performance reforms the curve's shape is
further set by a Marginal Reliability Impact (MRI) parameter. The ``iso``
label used throughout this repo is ``NEISO`` (matching ``config/iso_configs.py``),
not ISO-NE's own "ISO-NE" branding.

Native -> canonical metric map: ``auction_starting_price`` -> ``price_cap``
(ISO-NE's ceiling analog), ``mri`` recorded as its own metric row (added to
the vocabulary as a documentary pass-through under ``price_cap`` when it acts
as a cap, else left out of the curve and noted in source_page per the raw
README) — the retrieval CSV should prefer the canonical names directly.
"""

from __future__ import annotations

from . import IsoSpec, register

_METRIC_ALIASES = {
    "auction_starting_price": "price_cap",
    "icr": "irm",
}

SPEC = register(
    IsoSpec(
        iso="NEISO",
        metric_aliases=_METRIC_ALIASES,
        delivery_year_kind="planning",
    )
)
