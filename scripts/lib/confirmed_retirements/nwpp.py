"""NWPP confirmed-retirement spec.

Registered 2026-09-14 by lane NWPP-20 (docs/multi-iso/nwpp-addition-plan-2026-09.md
§5 row NWPP-20). **DATA NEEDED — no rows yet**: ``data/raw/confirmed-retirements/
nwpp.csv`` does not exist, so :func:`parse_unified_csv` returns the empty,
correctly-shaped frame and step 0 applies nothing for NWPP.

What the curation will and will not find, from NWPP-12's sweep of the seven
participant IRPs (``FINDING-nwpp-12-2026-09-13.md`` §2.4;
``data/raw/coal-prices/SOURCES_nwpp_coal.md`` §4): **the only enforceable public
instrument with a date is the Jim Bridger Consent Decree** — Wyoming and
PacifiCorp, Wyoming State District Court, filed 2022-02-14, heat-input limits
consistent with converting Bridger units 1 and 2 to natural gas by 2024-01-01
(Idaho Power 2025 IRP printed p. 17) — a ``consent_decree`` row that meets
CLAUDE.md's step-0 bar. Everything else is an IRP INTENTION and is recorded as
one, including two that contradict each other: PacifiCorp plans a Colstrip exit
"by 2030" while NorthWestern's Base Case retires Colstrip "according to its
project book life on December 31, 2042". Idaho Power files its North Valmy gas
conversion "by summer 2026" under "Actions Committed to before the 2025 IRP —
Not for Regulatory Acknowledgment", i.e. the utility itself declines to call it
an instrument. Two instruments NOT yet obtained, named so a follow-up goes
straight to them: Washington's coal-transition statute governing Centralia
(RCW 80.80) and Washington's CETA (RCW 19.405) behind the Avista and PacifiCorp
Washington-allocated Colstrip exits at end-2025.

The shared vocabulary, unchanged: a row needs a binding public instrument with a
date. For this largely vertically-integrated footprint the classes are
``regulatory_order`` (state commission orders — WUTC, OPUC, IPUC, PSC of Utah,
Montana PSC, PUCN — acknowledging or approving a retirement), federal
``consent_decree`` rows, and ``statute``; there is no RTO deactivation process
in the pool, so ``rto_deactivation`` is not expected to appear. An EIA-860
planned retirement date, an IRP filing, or an owner's exit-by-year intention is
NOT an instrument and stays with the announced-exit / economic screens.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NWPP",
        source_note=(
            "State commission retirement orders (WUTC/OPUC/IPUC/UT PSC/MT PSC/"
            "PUCN), consent decrees (Jim Bridger 1&2, WY District Court "
            "2022-02-14), statutes (RCW 80.80, RCW 19.405); no nwpp.csv "
            "curated yet."
        ),
    )
)
