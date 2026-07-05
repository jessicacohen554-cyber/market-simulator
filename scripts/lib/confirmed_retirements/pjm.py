"""PJM confirmed-retirement spec (reference ISO implementation).

Binding instrument: a PJM **Generator Deactivation** request that has cleared
reliability review with a confirmed deactivation date and no RMR must-run
requirement (``rto_deactivation``); where an RMR agreement exists, the unit
enters keyed to the RMR **end** date (``rmr_end``) instead — until then it is
compelled to run and is NOT a confirmed exit. Cross-ISO federal consent decrees
and state statutes (IL CEJA private-coal deadline) also apply to PJM units.

Public source to re-query at each intake vintage: the PJM "Generator
Deactivations" posting (XLSX of requests with status and dates) plus the
relevant court / state PUC dockets.

This module is the template the other ISO modules follow: declare an
:class:`IsoSpec` and register it. It uses the default unified-CSV parser.
"""

from __future__ import annotations

from . import IsoSpec, register

# Native labels a reviewer might type -> canonical confirmation-class vocabulary.
_CLASS_ALIASES = {
    "deactivation": "rto_deactivation",
    "deact": "rto_deactivation",
    "rmr": "rmr_end",
    "ceja": "statute",
}

SPEC = register(
    IsoSpec(
        iso="PJM",
        class_aliases=_CLASS_ALIASES,
        source_note=(
            "PJM Generator Deactivations posting (XLSX); federal consent decrees; "
            "IL CEJA coal phase-out statute."
        ),
    )
)
