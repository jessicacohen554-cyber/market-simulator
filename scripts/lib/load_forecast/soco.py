"""SOCO load-forecast spec — Georgia Power "Budget 2025 (B2025)", 2025 IRP.

The Southern Company balancing authority publishes no footprint-wide load
forecast. The only public forward load series in the footprint is **Georgia
Power Company's "Budget 2025 Load and Energy Forecast"**, filed as Technical
Appendix Volume 1 §1 of the 2025 Integrated Resource Plan (Georgia PSC Docket
56002, document 221233, filed 2025-01-31; approved 2025-07-15, order filed
2025-07-31), whose public summary workbook carries **summer peak, winter peak
and energy for 2025-2044** on a declared ``net`` basis for the peaks. Lane
SOCO-12 transcribed the 60 rows into ``data/raw/load-forecast/soco/soco.csv``
(edition ``Budget 2025 (B2025) / 2025 IRP``, vintage 2025; FINDING-soco-12
§0.1, gate G12), read by the package's default
:func:`~scripts.lib.load_forecast.parse_unified_csv`.

Two properties of the source are stated here because a consumer would
otherwise have to infer them (``SOURCES.md`` beside the CSV says the same):

* **The series is GEORGIA POWER, not the balancing authority.** The same
  workbook carries a "System" column — the Intercompany Interchange Contract
  companies, i.e. SOCO — and every System cell is REDACTED in the public
  disclosure, in all four summary sheets and in ``Energies``. Alabama Power
  files no public IRP because Alabama has no IRP statute (SOCO-12 §5), and
  Mississippi Power's 2024 IRP was not retrieved. So the datatype covers
  roughly half the footprint by peak (Georgia Power's 2025 winter peak
  16,264 MW against the BA's measured 47,368 MW), and **nothing is grossed
  up**: a SOCO-wide forward peak is a CONSTRUCTION lane SOCO-32 must declare,
  and ``constants.DEMAND_GROWTH_RATES["SOCO"]`` says on its row that its CAGRs
  are Georgia Power's (rule 14 ``[R-ACCURATE]``'s different-boundary
  exception, disclosed rather than reconciled).
* **One unit correction, declared by SOCO-12 (§4):** the workbook's
  ``Energies`` sheet is headed "GWh" and its cells are MWh (95.3 million "GWh"
  for 2025 would be ~2.5x total US generation); the CSV carries the published
  cell / 1000 labelled ``gwh``, each affected row saying so in ``source_page``.

Rule 13 ``[R-MEASURED]`` posture is the package's: a forward-looking published
input that regenerates from the next IRP cycle (Georgia files triennially;
the 2022 IRP and 2023 IRP Update carry earlier vintages of the same series)
and responds to changed conditions; never a measured outcome, never a target.

Registered 2026-09-14 by lane SOCO-20 (docs/multi-iso/soco-addition-plan-2026-09.md
§5, gate G12 — a spec needs a real edition and a vintage >= 2020, which the
SOCO-12 intake supplied).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="SOCO",
        edition="Budget 2025 (B2025) / 2025 IRP",
        vintage=2025,
        default_basis="net",
    )
)
