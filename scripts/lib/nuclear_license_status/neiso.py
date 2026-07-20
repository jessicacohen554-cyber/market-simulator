"""NEISO nuclear-license-status spec.

Millstone 2-3 (50-336/423) + Seabrook (50-443); NRC info-finder license pages.
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/neiso.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NEISO",
        source_note="Millstone 2-3 (50-336/423) + Seabrook (50-443); NRC info-finder license pages.",
    )
)
