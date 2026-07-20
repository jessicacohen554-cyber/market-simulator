"""PJM nuclear-license-status spec.

~30 units across IL/PA/OH/MD/VA/NJ/MI; NRC info-finder license pages; SLR grants (Peach Bottom/Surry/North Anna/Dresden); Crane/TMI-1 restart (docket 50-289).
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/pjm.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="PJM",
        source_note="~30 units across IL/PA/OH/MD/VA/NJ/MI; NRC info-finder license pages; SLR grants (Peach Bottom/Surry/North Anna/Dresden); Crane/TMI-1 restart (docket 50-289).",
    )
)
