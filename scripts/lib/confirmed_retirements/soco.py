"""SOCO confirmed-retirement spec.

Registered 2026-09-14 by lane SOCO-20 (docs/multi-iso/soco-addition-plan-2026-09.md
§5 row SOCO-20). **DATA NEEDED — no rows yet**: ``data/raw/confirmed-retirements/
soco.csv`` does not exist, so :func:`parse_unified_csv` returns the empty,
correctly-shaped frame and step 0 applies nothing for SOCO.

The shared vocabulary, unchanged: a row needs a binding public instrument with a
date. For the Southern Company balancing authority — vertically integrated, three
state commissions — the admissible classes are ``regulatory_order`` (a **Georgia
PSC** certification / decertification order under the IRP Act, O.C.G.A. §46-3A;
a **Mississippi PSC** order on a Mississippi Power IRP; **Alabama has no IRP
statute and no equivalent order**), federal ``consent_decree`` rows, and
``statute``; SOCO runs no RTO deactivation process, so ``rto_deactivation``
never appears.

What lane SOCO-12 found when it swept the record (FINDING-soco-12 §6), stated so
the first curation does not re-learn it: **the record is one of REVERSALS.** The
only executed-and-dated exits are Plant Wansley 1-2 / 5A and Plant Boulevard 1
(2022-08-31, pre-window). The 2022 IRP Order's Scherer 3 and Gaston 1-4/A
decertifications by 2028-12-31 were **superseded by the 2025 IRP Order**
("extended operation ... shall be approved"); Barry 5's and SEGCO Gaston 1-4's
retirements were reversed by company decision (coal-to-gas conversion; operation
through 2034); Daniel 2's date is being extended by Mississippi PSC filing. And
**an ELG-rule Notice of Planned Participation is NOT a step-0 instrument** — it is
a revocable environmental-compliance election, and the record above holds two
NOPPs reversed and a third overtaken. Bowen 1-2 and Greene County 1-2 are
announced, not instrument-bound, and stay with the announced-exit / economic
screens (the package docstring's rule). This is exactly the case CLAUDE.md's
step-1b reversal registry exists for.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SOCO",
        source_note=(
            "Georgia PSC IRP-Act certification/decertification orders, "
            "Mississippi PSC IRP orders, consent decrees, statutes (Alabama has "
            "no IRP statute). No soco.csv curated yet; the record is one of "
            "reversals (FINDING-soco-12 §6)."
        ),
    )
)
