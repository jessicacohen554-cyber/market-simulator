"""ERCOT confirmed-retirement spec.

Binding instrument: a **Notification of Suspension of Operations (NSO)** accepted
with the RMR review concluded WITHOUT a must-run agreement, for a *permanent*
(not seasonal) suspension (``rto_deactivation``). A unit under an accepted
RMR-type agreement enters keyed to that agreement's end date (``rmr_end``) — it
is compelled to run until then and is not a confirmed exit. Federal consent
decrees and dated state mandates also apply.

Public source to re-query: ERCOT market notices / suspension-retirement notices.
CPS Energy-style press announcements (J K Spruce / O W Sommers) are
*announced-grade* and deliberately stay OUT of the registry unless a binding
settlement emerges — they remain with the economic-retirement screen.
"""

from __future__ import annotations

from . import IsoSpec, register

_CLASS_ALIASES = {
    "nso": "rto_deactivation",
    "suspension": "rto_deactivation",
    "rmr": "rmr_end",
}

SPEC = register(
    IsoSpec(
        iso="ERCOT",
        class_aliases=_CLASS_ALIASES,
        source_note=(
            "ERCOT market notices / NSO suspension-retirement postings; federal "
            "consent decrees; state mandates."
        ),
    )
)
