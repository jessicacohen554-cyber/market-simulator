"""SPP confirmed-retirement spec.

Registered 2026-09-06 by lane SPP-20 (docs/multi-iso/spp-addition-plan-2026-09.md
§5 row SPP-20); **first rows curated 2026-09-07 by lane SPP-60**
(``data/raw/confirmed-retirements/spp.csv``, read by the default
:func:`parse_unified_csv`): Tolk 1 / 2 (SWEPCO/SPS, EIA 6194, 2 × 567.9 MW) under
NMPRC Case 22-00286-UT (final order 2023-10-19, retire by end-2028), deferred to
2029-03-31 by the NMPRC's 2026-05-07 approval of SPS's 2025 NM IRP. The CSV
header records the candidates evaluated and held out (North Omaha 4/5 — an
OPPD board resolution that defers with no binding date; Lawrence 4/5 — IRP
filings only; Northeastern 3 — 860-dated, no order located; Pirkey 1 and
Horseshoe Lake ST6/ST7 — in-window exits already carried by their EIA-860
owner-filed dates, so a confirmed row would decide the same exit twice,
rule 19). Every instrument on file post-dates 2020-12-31, so a 2020-vintage
hindcast applies none of them by the information gate; they are live in
forecast and 2023-vintage runs (``PRECOMMIT-spp-60-2026-09-07.md`` §1.2).

The shared vocabulary, unchanged: a row needs a binding public instrument with
a date. For SPP's largely vertically-integrated footprint the classes are
``regulatory_order`` (state commission orders approving a utility's retirement —
OCC, KCC, NPSC, MPSC, NMPRC, PUCT), federal ``consent_decree`` rows, and
``statute``; SPP itself does not run a PJM-style deactivation-acceptance
process, so ``rto_deactivation`` is not expected to appear. An EIA-860 planned
retirement date, an IRP filing, or a board resolution that *defers* a date is
NOT an instrument and stays with the announced-exit / economic screens (the
package docstring's rule).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SPP",
        source_note=(
            "State commission retirement orders (NMPRC/OCC/KCC/NPSC/MPSC/PUCT), "
            "consent decrees, statutes. spp.csv first curated 2026-09-07 "
            "(SPP-60): Tolk 1/2, NMPRC 22-00286-UT."
        ),
    )
)
