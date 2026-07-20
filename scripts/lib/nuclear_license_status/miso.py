"""MISO nuclear-license-status spec.

AR/MO/IL/MI/MS/MN/WI/LA units; NRC info-finder; SLR grants (Monticello/Point Beach); Palisades restart (docket 50-255).
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/miso.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="MISO",
        source_note="AR/MO/IL/MI/MS/MN/WI/LA units; NRC info-finder; SLR grants (Monticello/Point Beach); Palisades restart (docket 50-255).",
    )
)
