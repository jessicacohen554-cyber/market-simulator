"""CAISO nuclear-license-status spec.

Diablo Canyon 1-2 (50-275/323); NRC 2026 federal renewal (ROD ML26022A077) vs CA SB 846 state ceiling (see confirmed-retirements).
The default unified-CSV parser applies; the per-ISO rows live in
``data/raw/nuclear-license-status/caiso.csv``. Public sources to re-query:
NRC per-reactor info-finder pages, the NRC Subsequent License Renewal status
list, and the NRC approved-power-uprate list (see the datatype README).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="CAISO",
        source_note="Diablo Canyon 1-2 (50-275/323); NRC 2026 federal renewal (ROD ML26022A077) vs CA SB 846 state ceiling (see confirmed-retirements).",
    )
)
