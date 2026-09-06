"""SPP confirmed-retirement spec.

Registered 2026-09-06 by lane SPP-20 (docs/multi-iso/spp-addition-plan-2026-09.md
§5 row SPP-20) so the ``confirmed-retirements`` datatype has an SPP partition
the moment rows are curated. **DATA NEEDED — no rows yet**: no
``data/raw/confirmed-retirements/spp.csv`` exists, so :func:`parse_unified_csv`
returns the empty, correctly-shaped frame and the confirmed-exit injector has
nothing to apply for SPP (the same additive posture every ISO took before its
intake landed).

What a row will need (the shared vocabulary, unchanged): a binding public
instrument with a date. For SPP's largely vertically-integrated footprint the
expected classes are ``regulatory_order`` (state commission orders approving a
utility's retirement — OCC, KCC, NPSC/OPPD board, MPSC, NMPRC, PUCT), federal
``consent_decree`` rows, and ``statute``; SPP itself does not run a PJM-style
deactivation-acceptance process, so ``rto_deactivation`` is not expected to
appear. An EIA-860 planned retirement date is NOT an instrument and stays with
the announced-exit / economic screens (the package docstring's rule).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SPP",
        source_note=(
            "DATA NEEDED: state commission retirement orders (OCC/KCC/NPSC/MPSC/"
            "NMPRC/PUCT), consent decrees, statutes; no spp.csv curated yet."
        ),
    )
)
