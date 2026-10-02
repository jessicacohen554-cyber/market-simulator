# NEISO 2025 — what the W0 posture moves (desk ruling item 3)

Zero LP. `neiso119_span` recipe rebuilt `fleet_only` for 2025 at the recorded posture vs the W0
posture; Σ pmax by (plant, class) of every LP unit (masked or not). Total **−691.6 MW**.

| Plant | Class | recorded → W0 MW | Cause | EIA-860 record |
|---|---|---|---|---|
| 2367 Schiller (units 4, 6) | COAL_BIT | 95.4 → 0 | dark units no longer re-carried | `vintage_2024` operable: units 4/5/6 status **OS** (out of service); `vintage_2025` retired sheet: Retirement **2025-10**. Status OS before the paper date = physical exit (audit §E.5); `retiree_vintage_status_scope` reads the contemporaneous status. Schiller GT1 (oil, OP) stays. |
| 55031 Androscoggin (CT01-03) | CT_PEAKER | 130.2 → 0 | same | `vintage_2024`: **OS**; `vintage_2025` retired: **2025-10**. |
| 1660 Potter Station 2 (CC2, CC3) | CC_REGULAR | 78.1 → 0 | already retired | both vintages' retired sheets: Retirement **2024-01**; the W0 posture no longer carries the cohort into 2025. |
| 60903 Salem Harbor + 13 other CC plants | CC_REGULAR | ≈ −700 MW net | capacity basis | keeper is nameplate-basis CC (`cc_nameplate_summer_derate`); W0 carries the published seasonal envelope under the always-on guard (E.1). Salem Harbor's block is rated on its CT rows (summer 337.8 / 337.2 vs nameplate 158.4) with blank CA rows; the guard holds the plant at its 798.2 MW nameplate. |
| oil / CT additions (557, 10823, 10883, 1678, 59882, 55517 …) | oil / CT_PEAKER | +16 … +44 each | SB admission (E.4) and winter > summer ratings | operable status SB / winter rating. |

**Verdict:** the COAL_BIT 203 → 108 MW move is Schiller 4/6 (95.4 MW). It is an EIA-860 Final-2025
fact (OS in the 2024 vintage, retired 2025-10), not a filter artifact. The −692 MW total is the E.1
basis on nameplate-basis CC, plus three plants EIA-860 records as out of service or retired.
Evidence: `guard-pr7033/`, `fleet_census_2025_{recorded,w0}.json`.
