"""SPP nuclear-license-status spec.

The two reactors in the SPP footprint — **Wolf Creek Generating Station 1**
(EIA 210, KS, 1,296.3 MW, docket 50-482, licence expires **2045-03-11**,
``renewed_60``, SLR ``announced_intent`` — application expected Jan-Mar 2030,
letter ML25345A467, NOT filed) and **Cooper Nuclear Station 1** (EIA 8036, NE,
801.0 MW, docket 50-298, licence expires **2034-01-18**, ``renewed_60``, SLR
``under_review`` — received 2026-05-07, accepted 2026-06-05, NOT granted). Both
were landed by lane SPP-12 in ``data/raw/nuclear-license-status/spp.csv``
(FINDING-spp-12 §7) under the SPP desk's r#2 addendum, ahead of this
registration; the default unified-CSV parser applies. Public sources to
re-query: NRC per-reactor info-finder pages (``/reactors/wc``, ``/reactors/cns``),
the NRC Subsequent License Renewal status list, the NRC expected-applications
letter.

Worth every SPP forecast lane's attention (FINDING-spp-12 §7): Cooper's
2034-01-18 expiry falls INSIDE the 2026-2050 horizon with its SLR under review
rather than granted, and Wolf Creek's 2045 expiry likewise with only an
announced intent behind it — so a forecast that assumes 2,097 MW of firm nuclear
through 2050 assumes outcomes the instrument record does not yet support.
Nothing in the solve path consumes this registry yet, for any ISO (the
forward-channel design is ``docs/handoffs/ff-g5-nuclear-registry-2026-07.md``).

Registered 2026-09-06 by lane SPP-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SPP",
        source_note=(
            "KS/NE units (Wolf Creek 1, Cooper); NRC info-finder; SLR: Cooper "
            "under review (received 2026-05-07), Wolf Creek announced intent "
            "(expected 2030)."
        ),
    )
)
