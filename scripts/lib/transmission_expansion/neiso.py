"""ISO-NE transmission-expansion spec (model label NEISO).

Binding instruments: state-contracted HVDC with construction underway (NECEC /
New England Clean Energy Connect under the MA 83D contracts) and ISO-NE PAC
reliability projects with approved Transmission Cost Allocation. Public sources
to re-query: ISO-NE RSP project list / PAC materials, MA DPU dockets. Base
statics are the RSP ~2023-vintage interface limits (pre-NECEC), so NECEC is
additive on ``HQ_import -> North`` and the ``HQ_import_simultaneous`` group
even though its COD may precede 2026.

The model calls this ISO "NEISO"; its filings say "ISO-NE". The canonical label
in the ``iso`` column and clean partition is NEISO (the model name).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NEISO",
        source_note=(
            "MA 83D NECEC contracts + ISO-NE PAC/RSP reliability projects "
            "with approved cost allocation."
        ),
    )
)
