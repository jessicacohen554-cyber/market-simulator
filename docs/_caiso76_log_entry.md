### 2026-07-11 — CAISO — caiso-76 (measured 2025 hydro budget correction): C2 clears to CAVEAT, **PROMOTED to keeper**; evening-CC build gated off; battery adder resolved no-change

STEP-0-first session on the C2 2025 gas gate (+6.5 %, the promotion blocker vs
the keeper's CAVEAT). Solve + registration on CI (`caiso76-solve-register`);
`FINDING-caiso76-hydro-budget-2026-07-11.md`.

- **STEP-0 root cause** (rule 14, no mechanism until measured): the 2025
  EIA-923 vintage is a monthly-survey-only early release — CAISO hydro
  carries 26 of ~185 plants, 12.32 of the measured 21.32 TWh (930 `NG: WAT`).
  The missing 9.0 TWh of inflow is served by gas (+4.4 TWh = the C2 FAIL),
  imports (40.7 vs 35.9 measured) and un-curtailed solar (+3.6 vs 930); it
  also flattens off-peak CC (overnight +1.2-1.7 GW, belly +2.0 GW vs CAMPD,
  evening ramp late) and inflates C5a-2025 (+46 %). D-2 rules out floors
  (the RA bridge forces 2.5 % of CC energy). 2023/24 budgets are
  near-measured (final vintages) — the C1 CC-over cluster there stays open.
- **caiso-76** (`2026-07-11-caiso-76-hydro-budget`): `hydro_backfill_year=2024`
  + `hydro_eia930_monthly=True` — restore per-plant coverage/MW envelope from
  the 2024 vintage, repin every year's monthly budget to measured 930
  `NG: WAT` (23.90→24.40 / 21.48→22.68 / 12.32→21.32 TWh). Existing
  NEISO-2025 machinery, first keeper use; zero fitted parameters (nothing
  fit to any year — LOYO n/a); measured-input rule-13/14 class. A/B vs
  caiso-75: **C2-2025 +6.5 % FAIL → −4.1 % CAVEAT** (gas 72.96 → 65.71 TWh —
  the 9 TWh hydro displaced 7.25 TWh gas, overshooting slightly to under);
  C5a +7.0/+19.0/+46.0 → +6.6 (PASS)/+17.9/+32.7 %; C1 CC_REGULAR 2024
  +7.64 → +7.04 TWh (share breach clears), 2023 +5.35 → +5.05; C3a-2025
  +47.4 → +40.7 % (the hydro-starvation share of the LMP ramp; the ~+22 %
  all-years base is the deferred offer-level issue); C4 gas r up all years
  (2025 0.566 → 0.576). v2.4: NOT-YET with C6/C7/C8 PASS, C2 CAVEAT.
  **PROMOTED per the pre-authorized conditions** (C6+C7+C8 PASS; no gate
  regressed vs the keeper's rescore — C2 CAVEAT matches its bar, C6/C8
  improve on UNATTESTED/FAIL; C1/C2 volume cluster improved). Zero-forcing
  ablation twin registered alongside.
- **Evening-CC commitment build: GATED OFF** by its own design-doc §0
  re-measure on the caiso-75 line: evening CC gap +1.7/+1.1/+0.3 GW
  (2023/24/25) — 2025 under the 0.5 GW build threshold and the 2025 belly
  flipped to model-OVER (−0.8 GW). A floor that adds evening CC energy
  cannot fix an annual-volume EXCESS gate; re-measure on the caiso-76 line
  before any build (2024 +1.1 GW is still open).
- **Battery cycling adder (queued caiso-74 follow-up): resolved NO-CHANGE,
  documented.** CAISO BPM Market Instruments V91 RDT `STORAGE_VARIABLE_COST`
  (the Storage-DEB ρ of DMM-2024 Eq 2.11.1, "including cycling and cell
  degradation costs") **defaults to $0/MWh** (resource-specific values are
  validated, not published); and the measured LESR RTD energy schedules
  (raw `storage-as-awards` quarterlies, HYBD excluded as solar-contaminated)
  give actual battery discharge 5.67/10.04/12.06 TWh 2023/24/25 vs model
  5.33/7.60/10.48 — the zero-adder LP already UNDER-cycles CAISO, so the
  ERCOT over-cycling failure mode (which that keeper's $10 adder corrects)
  is absent and a positive adder would regress throughput fidelity.
  `battery_dispatch_adder` stays 0.0 for CAISO; no new knob, no probe.
- **Registry**: caiso-69 pair pruned (top-15 retention; d690187 precedent).
- **Bench follow-up filed** (FINDING §4): the 2025 bench CO2 actual
  (21.68 Mt) is computed off the same preliminary-923 class generation and
  is vintage-understated (CO2-implied CC_REGULAR 37.5 TWh vs the 930 family
  ~68.5) — rebuild on a complete-coverage basis (or eGRID 2025) when data
  lands; C5a-2025 carries this caveat until then. Also open: the C1
  2023/24 CC-over/CT-under cluster (evening ledger re-measure on the
  caiso-76 line), Bay-Area local topology for the 2024/25 C3c tail (QUEUED),
  offer-curve level (C3a base, LAST per rule 1).
