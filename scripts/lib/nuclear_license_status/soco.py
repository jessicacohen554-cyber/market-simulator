"""SOCO nuclear-license-status spec.

The eight reactors in the Southern Company balancing authority — all Southern
Nuclear Operating Co. — landed by lane SOCO-12 in
``data/raw/nuclear-license-status/soco.csv`` (FINDING-soco-12 §3), read by the
default unified-CSV parser:

* **Joseph M. Farley 1 / 2** (EIA 6001, AL, 888.2 MW each; dockets 50-348 /
  50-364) — licences expire **2037-06-25** / **2041-03-31**, ``renewed_60``, SLR
  ``announced_intent`` (letter of intent ML26048A183, NOI 2026-02-16, application
  expected Apr-May 2027; NOT filed).
* **Edwin I. Hatch 1 / 2** (EIA 6051, GA, 924.0 MW each; 50-321 / 50-366) —
  **SLR GRANTED 2026-06-11**, the footprint's only granted subsequent renewal;
  post-SLR expiries **2054-08-06** / **2058-06-13** (the NRC info-finder still
  printed the pre-SLR 2034 / 2038 dates four months after the decision — a
  publication lag the CSV's notes record, not a conflicting instrument).
* **Vogtle 1 / 2** (EIA 649, GA, 1,215.0 MW each; 50-424 / 50-425) — expire
  **2047-01-16** / **2049-02-09**, ``renewed_60``, **no SLR of any kind on file**.
* **Vogtle 3 / 4** (EIA 649, 1,114.0 MW each; Part 52 COLs 52-025 / 52-026,
  operating 2023-07 / 2024-04) — expire **2062-08-03** / **2063-07-28**, forty
  years after the 10 CFR 52.103(g) finding; not on the info-finder.

Worth every SOCO forecast lane's attention (SOCO-12 §3): **six of eight expiries
fall inside the 2026-2050 horizon** — Farley 1-2 (1,776.4 MW, intent only) and
Vogtle 1-2 (2,430 MW, nothing on file) — so a forecast that assumes 8,282 MW of
firm nuclear through 2050 assumes outcomes the instrument record does not
support for 4,206.4 MW of it. Georgia PSC approved uprates in the 2025 IRP
order (+58 MW Hatch 1-2, +54 MW Vogtle 1-2, published at two-unit grain and
carried once on each plant's unit-1 row). Nothing in the solve path consumes
this registry yet, for any ISO (the forward-channel design is
``docs/handoffs/ff-g5-nuclear-registry-2026-07.md``).

Registered 2026-09-14 by lane SOCO-20.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SOCO",
        source_note=(
            "AL/GA units (Farley 1-2, Hatch 1-2, Vogtle 1-4); NRC info-finder + "
            "COL-holder pages; SLR: Hatch granted 2026-06-11, Farley announced "
            "intent (expected 2027), Vogtle none."
        ),
    )
)
