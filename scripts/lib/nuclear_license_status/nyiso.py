"""NYISO nuclear-license-status spec.

FitzPatrick / Nine Mile Point 1-2 / Ginna; NRC info-finder; NMP1 + Ginna SLR under review (2026).
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/nyiso.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NYISO",
        source_note="FitzPatrick / Nine Mile Point 1-2 / Ginna; NRC info-finder; NMP1 + Ginna SLR under review (2026).",
    )
)
