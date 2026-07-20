"""ERCOT nuclear-license-status spec.

Comanche Peak (dockets 50-445/446) + South Texas Project (50-498/499); NRC info-finder license pages; NRC SLR + uprate status lists.
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/ercot.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="ERCOT",
        source_note="Comanche Peak (dockets 50-445/446) + South Texas Project (50-498/499); NRC info-finder license pages; NRC SLR + uprate status lists.",
    )
)
