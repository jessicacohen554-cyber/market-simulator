# SPP MMU — unavailable conventional generation capacity, annual (2020–2024)

- **Source:** SPP Market Monitoring Unit, *Unavailable Generation Capacity in SPP Markets: Causes and
  Impacts*, published 2025-12-19 (SPP document 75563).
  `https://spp.org/documents/75563/unavailable%20generation%20capacity%20in%20spp%20markets%20causes%20and%20impacts.pdf`
  (666,507 bytes; fetched 2026-10-01).
- **File:** `spp_mmu_unavailable_capacity.csv`, one row per year, MW, annual averages on the MMU's
  *rated conventional capacity* basis (capability-test output; VERs, demand response and grid-switching
  resources are excluded).

| column | source in the report | exact or digitized |
|---|---|---|
| `rated_conventional_mw` | Fig 16, dashed line | digitized (±~100 MW) |
| `eco_to_emer_max_mw` | Fig 17, "between economic and emergency maximum" (prose: 1,600–1,800 MW) | digitized |
| `above_emer_max_mw` | Fig 17, "above emergency maximum" <10 MW + >10 MW (Fig 4 line agrees; prose: 2,500 in 2020, ~1,500 in 2021) | digitized |
| `reliability_status_all_mw` | Fig 17, "reliability status" (prose: 1,600 in 2020 → 3,000 in 2024) | digitized |
| `reliability_status_gas_mw` | Fig 3, natural-gas grey squares (prose: avg just over 1,300, almost 2,000 in 2024) | digitized |
| `ambient_derate_mw_on_days`, `ambient_derate_days` | Fig 12 table | **exact** |

- **Digitization:** read by eye from the 80-dpi page renders (`pdftoppm -r 80`) by session SPP-106,
  2026-10-01. Each value is ±~100 MW. The prose numbers above are the check.
- **Coverage:** 2020–2024 only. No hour, unit, or technology (CC / CT / ST) grain is published. Only
  reliability status is split by fuel.
- **Known rule-14 tension:** the MMU's 2024 *State of the Market* (doc 73953) gives "reliability status
  or above economic maximum" as ~4,000 MW for 2024. This file's two corresponding columns sum to 4,650.
  The two products use different bases (installed vs rated capacity, and scope). DESIGN-spp-106 §1.
- **Read by:** `market_sim.data.spp_mmu_unavailability`, under
  `ScenarioConfig.spp_mmu_offer_unavailability` (SPP-106, default off); also
  `scripts/probes/_spp106_offer_unavailability_phase0.py`.
- **Identity:** `SHA256SUMS.txt`.
