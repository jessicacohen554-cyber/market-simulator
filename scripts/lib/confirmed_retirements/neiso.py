"""ISO-NE confirmed-retirement spec (model label NEISO).

Binding instrument: a **Retirement / Permanent De-List Bid** that has *cleared*
in a Forward Capacity Auction (binding under the tariff), or an approved
Non-Price Retirement Request (``rto_deactivation``). Public source to re-query:
ISO-NE retirements & FCA-results postings. Mystic-class exits are already
historical (carried by the within-window retiree build); the forward list is
short, so the registry CSV lands as DATA NEEDED until it is populated.

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
