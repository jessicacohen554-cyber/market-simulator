# FF-2B — exact source changes (apply spec) + status — 2026-07-19

**Why this file:** the full source files are too large to transport through this
session's only write path (`push_files` requires full inline content;
constants.py 345 KB / capacity.py 204 KB exceed reliable inline reproduction —
a patch attempt corrupted; direct git-data API writes are proxy-blocked 403;
git push is banned/413). Every change below is small, precise, and verified in
the local working tree. Apply these exact edits, then `pytest tests/test_capacity.py`.

## src/market_sim/config/constants.py
1. `PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]`: `0.157` → `30_305.0 / 27_298.0 - 1.0`
   (= 0.1102). ISO-NE Net ICR 30,305 MW / summer 50/50 peak 27,298 MW, FCA 17
   (CCP 2026/2027), FERC Docket ER23-405-000 (2022-11-08): ICR 31,306, HQICC
   1,001, Net ICR 30,305 (p.2-3); 50/50 peak 27,298 (p.9-10, 2022 CELT).
2. `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`: add `"NEISO": 2_940.0 / 30_305.0`.
   FCA 17 cleared 2,940 MW demand resources (ISO-NE press release 2023-03-10) ÷
   Net ICR 30,305 (rule-14 reconciliation, PJM pattern).
3. `ADEQUACY_EXTERNAL_TIE_FIRM_MW`: add `"CAISO": 3_371.0` (DMM 2024 Annual
   Report Table 15.6 RA "Imports" = model's own firm import tranches) and
   `"NEISO": 567.0` (FCA 17 cleared imports NY/QC/NB). Generalize the header
   comment to cover import-node ISOs (no double-count: accredited ledger reads
   the persistent `fleet`, which excludes the dispatch import pseudo-generators).

## src/market_sim/model/capacity.py
4. Add helper `_firm_import_mw(iso) -> float` (before `accredited_firm_capacity_mw`):
   `return ADEQUACY_EXTERNAL_TIE_FIRM_MW.get(iso or "", 0.0)` — the single
   resolver (rule 19) for adequacy-counted firm imports; docstring documents the
   two provenance cases + no-double-count.
5. In `accredited_firm_capacity_mw`, replace
   `if iso is not None: firm += ADEQUACY_EXTERNAL_TIE_FIRM_MW.get(iso, 0.0)`
   with `firm += _firm_import_mw(iso)` (+ comment); update the docstring line
   naming CAISO/NEISO import-node ISOs.

## src/market_sim/runner.py
6. Add `UNSET,` to the `from market_sim.pipeline import (...)` block (line ~133).
   Blocker fix: miso-76 merge 2ad50aa used `UNSET` (the `miso_zonal_loss_surface`
   else-branch, hit by EVERY forecast run since the flag defaults off) without
   importing it → NameError. Without this, no forecast run executes.

## tests/test_capacity.py
7. Add `class TestFF2BAdequacyBasis` (4 tests, after `TestPJMAdequacySideRegistries`):
   NEISO PRM = Net ICR/50-50 peak; NEISO DR × 30,305 = 2,940; requirement netting
   at CELT peak = Net_ICR − DR = 27,365; firm-import credits CAISO 3,371 / NEISO 567.

## docs
- `docs/forecast-development-plan-2026-07.md` §1.2 row 5: rewrite (NEISO I7 PASS;
  CAISO/NYISO hydro-dominated → FF-1C).
- `docs/gap-register-2026-07.md`: append to R5b (requirement side CLOSED); add
  R5c (hydro excluded from accredited ledger → FF-1C).

## Result (verified locally, base-year 2026 forecast, HEAD defaults)
- **NEISO I7 FAIL→PASS**: firm 27,171→27,738 vs requirement 28,797→24,951; run 0 FAIL/0 WARN.
- **CAISO I7 FAIL→FAIL** (improved): firm 42,734→46,105 vs req 57,306 (+import 3,371);
  residual = hydro excluded from ledger (3,601 MW, FF-1C) + peak-currency + VRE ELCC (CR-3.1).
- **NYISO I7 FAIL (unchanged)**: basis already correct (FF-3D ratio 0.8679); gap 1,799
  ≈ hydro excluded from ledger (3,343 MW, FF-1C). No constant changed.
- **Central finding**: only NEISO was a basis mis-pairing; CAISO/NYISO are dominated by the
  ledger-structure hydro exclusion (dispatched-but-not-accredited), routed to FF-1C. Not
  tuned to force closure (rule 1/11). Full write-up: `ff-2b-adequacy-basis-2026-07.md` (local).
- NEISO first capacity-hindcast pair (fixed/curve) + per-vintage Pass-1B done + registered.

`tests/test_capacity.py` passes (27 relevant); band pre-registration pushed (837c6d0).
