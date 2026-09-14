"""SOCO transmission-expansion spec.

Binding instrument: a **Georgia PSC certificate** for a Georgia Power transmission
project under the IRP Act, or an **Alabama PSC / Mississippi PSC** order for the
other two operating companies — the Southern Company balancing authority plans
transmission company-by-company under state jurisdiction and runs no
RTO-style board-approved portfolio. The public source a curation would read is
the 2025 IRP's transmission chapter (Georgia PSC Docket 56002, document 221233;
``data/raw/soco-planning/transcriptions/GPC_2025_IRP_Main_Document.txt``,
landed by SOCO-12) and the Southern Company FERC Form 715 / Attachment K
postings — none of which states an inter-OpCo transfer capability, because
**no such published number exists, structurally**: the OpCos are one pooled
dispatch under the Intercompany Interchange Contract (SOCO-12 README §4b).

That is why ``iso_configs._soco_config``'s two links (AL<->GA 24,400 MW, AL<->MS
4,300 MW) are Tier-3 placeholders that cannot bind — each the smaller side's
EIA-860 2025 ER winter capability — and why SOCO's entry in
``TRANSMISSION_BASE_STATIC_VINTAGE`` is **2025**, following the only source the
placeholder has. Lever SOCO-54 owns the real limit and has no price signal to
validate it against (owner card S2: no zonal price, spread or congestion archive
exists for this footprint). If SOCO-54 lands a limit from a different vintage,
the vintage row follows it, as SPP's did (2025 -> 2026 at SPP-53).

**DATA NEEDED — no rows yet**: ``data/raw/transmission-expansion/soco.csv`` does
not exist, so :func:`parse_unified_csv` returns the empty, correctly-shaped
frame and the forward TTC channel applies nothing for SOCO. At this three-zone
grain most certificated projects will be ``intra_zonal`` (recorded,
dispatch-inert); only a project that raises the AL<->GA or AL<->MS corridor
would map to a ``link`` row, and there is no measured base for it to be
reconciled against until SOCO-54 lands one. Registered 2026-09-14 by lane SOCO-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SOCO",
        source_note=(
            "Georgia PSC IRP-Act transmission certificates (2025 IRP, Docket "
            "56002) / Alabama and Mississippi PSC orders; no soco.csv curated "
            "yet; no inter-OpCo limit is published (IIC pooled dispatch)."
        ),
    )
)
