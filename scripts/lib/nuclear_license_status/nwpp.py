"""NWPP nuclear-license-status spec.

The ONE reactor in the NWPP footprint — **Columbia Generating Station** (EIA
plant 371, WA, balancing authority BPAT, 1,200.0 MW nameplate / 1,151 MW summer,
NRC docket 50-397, NRC info-finder slug ``wash2`` — the WNP-2 heritage; ``colu``
is a 404). Landed by lane NWPP-12 in ``data/raw/nuclear-license-status/nwpp.csv``
(FINDING-nwpp-12 §1 row 4) from the NRC pages cited in
``data/raw/nwpp-planning/SOURCES.md`` §4; the default unified-CSV parser
applies. Its biennial refuelling is the whole of the monthly-CF variance the
constants table carries (audit §7 row 10: annual CF 0.802 / 0.948 / 0.737 for
2023 / 2024 / 2025, deep outages May–Jun 2023 and Apr–Jun 2025, none in 2024).

Nothing in the solve path consumes this registry yet, for any ISO (the
forward-channel design is ``docs/handoffs/ff-g5-nuclear-registry-2026-07.md``).

Registered 2026-09-14 by lane NWPP-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NWPP",
        source_note=(
            "Columbia Generating Station (EIA 371, BPAT, docket 50-397; NRC "
            "info-finder slug wash2); nwpp.csv landed by NWPP-12."
        ),
    )
)
