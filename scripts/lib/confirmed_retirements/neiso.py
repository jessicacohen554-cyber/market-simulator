"""ISO-NE confirmed-retirement spec (model label NEISO).

Binding instrument: a **Retirement / Permanent De-List Bid** that has *cleared*
in a Forward Capacity Auction (binding under the tariff), or an approved
Non-Price Retirement Request (``rto_deactivation``). Public source to re-query:
ISO-NE retirements & FCA-results postings. Mystic-class exits are already
historical (carried by the within-window retiree build). Seeded 2026-07-05:
Merrimack Station 1-2 — via a 2024 Clean Water Act consent decree
(``consent_decree``), not the FCA de-list-bid tracker (the tracker's other
forward candidates could not be matched to a current EIA-860 identity and
were excluded — see ``data/raw/confirmed-retirements/neiso.csv``).

The model calls this ISO "NEISO"; its filings say "ISO-NE". The canonical label
in the ``iso`` column and clean partition is NEISO (the model name).
"""

from __future__ import annotations

from . import IsoSpec, register

_CLASS_ALIASES = {
    "delist": "rto_deactivation",
    "de-list": "rto_deactivation",
    "npr": "rto_deactivation",
}

SPEC = register(
    IsoSpec(
        iso="NEISO",
        class_aliases=_CLASS_ALIASES,
        source_note="ISO-NE cleared permanent de-list bids / FCA results.",
    )
)
