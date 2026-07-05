"""MISO confirmed-retirement spec.

Binding instrument: an **Attachment Y** retirement request that has been
*approved* (``rto_deactivation``). Suspensions are reversible and are excluded.
Federal consent decrees and state statutes also apply. Public source to
re-query: the MISO generator-retirements / Attachment Y public status posting.
The registry CSV lands as DATA NEEDED until the Attachment Y block is itemized.
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
