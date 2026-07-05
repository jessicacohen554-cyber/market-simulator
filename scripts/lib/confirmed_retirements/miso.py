"""MISO confirmed-retirement spec.

Binding instrument: an **Attachment Y** retirement request that has been
*approved* (``rto_deactivation``). Suspensions are reversible and are excluded.
Federal consent decrees and state statutes also apply. Public source to
re-query: the MISO generator-retirements / Attachment Y public status posting.
Seeded 2026-07-05: DTE Monroe 1-4 (Michigan PSC Case No. U-21193 settlement,
a ``regulatory_order`` rather than a directly-fetched Attachment Y approval —
MISO's own posting could not be fetched in that intake pass; TLS/access
errors on oasis.oati.com and misoenergy.org). See
``data/raw/confirmed-retirements/miso.csv`` for the full evaluated candidate
list (most of the ~13.5 GW 2026-2028 coal cluster is announced/IRP-stage, not
yet approved).
"""

from __future__ import annotations

from . import IsoSpec, register

_CLASS_ALIASES = {"attachment_y": "rto_deactivation", "att_y": "rto_deactivation"}

SPEC = register(
    IsoSpec(
        iso="MISO",
        class_aliases=_CLASS_ALIASES,
        source_note="MISO Attachment Y approved-retirement posting; consent decrees.",
    )
)
