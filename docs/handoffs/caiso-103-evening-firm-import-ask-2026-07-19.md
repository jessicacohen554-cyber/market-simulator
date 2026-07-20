# CAISO-103 owner ask — price-taking firm import blocks (the evening CT-rung composition fix)

**Status: GRANTED (caiso-104 session, 2026-07-20) then ADJUDICATED INERT —
no leg solved; evening lane RE-CHARTERED (owner ruling on the evidence).**
The caiso-104 pin-check (`scripts/probes/_caiso104_firm_pin_check.py`)
established that the caiso-77 must-flow floor
(`caiso_firm_import_selfschedule=True`) is LIVE in the caiso-102-hourfix
keeper recipe: both firm blocks are pinned at `dispatch == min_gen == pmax ×
availability` in 1.0000 of capable hours in all three years, so the bid swap
this ask proposes is provably byte-inert, and §1's "interior / 1.7–2.5 GW
withheld" attribution was an artifact of the p99 interior-dispatch proxy on
pinned month-varying dispatch. The §3.2 pre-measurement WAS executed
(negative-hub conduct → bid constant $0, `_caiso104_firm_negative_hub.py`)
and stands for any successor mechanism. See
`results/calibration/FINDING-caiso104-m1-meve1-execution-2026-07-20.md` §1–§2.
The original ask text is preserved below unchanged for the record.

---

**Status: PENDING owner ruling.** No mechanism built or solved; measured
decomposition in FINDING-caiso103 §3 (`_caiso103_evening_margin.py` on the
same-machine `caiso102_repro_A`, which reproduces the caiso-102-hourfix
keeper digit-for-digit).

## 1. The measured defect (one paragraph)

In the deepest evening resid-quartile (Q1, mean resid −36.6/−25.5/−15.4
$/MWh), the marginal supply is the import node in 97-100 % of hours, the
corridors carry 5-6 GW unused headroom (never saturated), CC headroom is
0.2 GW, and Q1 λ stops a median +1.3/+3.6/+13.1 $/MWh BELOW the model's own
CT rung entry. Actual CAISO RT clears at/above the measured intertie hub LMP
in those hours (median −0.7/+2.6/+4.8) while model λ sits 8-40 $ BELOW the
same hubs. Tranche attribution: the price-setters are the two FIRM/CONTRACTED
blocks (`PNW_hydro_base` $28, `DSW_solar_PV` $48 — static Tier-3
contract-cost proxies kept by `caiso_perhub_firm_base`), interior in
96-100 % of Q1 hours, with 1.7-2.5 GW of their contracted capability
economically WITHHELD in exactly those hours. The code's own rationale for
these blocks (transmission.py, `CAISO_FIRM_IMPORT_TRANCHES`) says they are
inframarginal price-takers that "flow largely independent of the hourly spot
spread" (BPA firm hydro / DSW solar PPAs; RA-import must-offer =
self-schedule or ≤$0 bid, CPUC D.20-06-028) — the elastic contract-cost
offer contradicts the mechanism's own documented driver.

## 2. Proposed mechanism (M-EVE-1): self-scheduled firm blocks

Gate `ScenarioConfig.caiso_firm_import_selfschedule` (default off; CAISO
backcast recipe arms it): the two `CAISO_FIRM_IMPORT_TRANCHES` keep their
existing caiso-73 measured shaped hourly AVAILABILITY (unchanged artifact,
frozen derive) but bid **−ε instead of the $28/$48 contract-cost ladder
prices** — price-taking supply that flows whenever λ > −ε, exactly the
self-schedule/≤$0 RA must-offer conduct. The contract-cost estimates leave
the price-formation path entirely (they were never a marginal price in the
real market; the buyer's contract cost is sunk).

- **Effect direction (both toward measured):** the withheld 1.7-2.5 GW flows
  → evening import volume rises toward the aligned-clock measured level
  (model currently −0.5/−0.3/−1.4 TWh evening); the margin moves UP to the
  measured-hub-priced spot tranches (Mid-C economy / DSW thermal / scarcity)
  and the domestic CT rung → tight-evening λ climbs from the contract rung
  toward the hub/CT level reality pays (hub separation −39.8/−18.9/−8.5 →
  toward −2.3/+4.0/+6.7).
- **Rule 12**: driver = RA-import must-offer conduct (CPUC D.20-06-028) +
  specified-source contract self-scheduling (the block's existing
  documented rationale). Window = the blocks' existing measured caiso-73
  shaped availability (all hours; no new window). Forward story = RA import
  contract volume regenerates from the RA program requirement; shape ×
  contract MW (the existing firm-shape derive, untouched).
- **Rule 1 / guardrails**: NOT a CT floor (caiso-91b untouched — CT enters
  on its own offer when the margin reaches its rung); NOT an import
  throttle (flow INCREASES); does not touch the caiso-87/93/94/97 clean
  windows or any tranche capacity; the caiso-95 §4 comparison artifact is
  not the basis (the aligned FINDING-caiso102 §4 measurement is).
- **Rules 24/25**: no new tunable — the change DELETES two fitted Tier-3
  scalars from the marginal-cost path (DOF ledger shrinks by two rows; the
  ladder entries remain only as the non-perhub fallback path's prices).
- **D-2/C8**: import is not a gated merchant class; C8 untouched. D-2: the
  firm blocks' flow becomes conduct-scheduled supply — new mechanism id
  (`firm_import_selfschedule`) with a D4_WINDOWS entry = the caiso-73 shape
  support, so the C8-escalation machinery can see it.
- **Interactions**: composes with `caiso_perhub_firm_base` (which already
  special-cases these blocks — the flag's else-branch simply changes WHAT
  the special case does: static price → price-taker); the caiso-97 evening
  trim and caiso-87 windows are untouched; belly-side effect bounded (the
  caiso-73 shape has 0.2-1.3 GW midday capability, and a −ε bid in glut
  hours flows only when λ > −ε — behavior in negative-λ hours must be
  gate-checked: the block must NOT flow through negative prices reality
  curtails through... measured conduct check to pre-register: the firm flow
  vs negative-hub hours).

## 3. Known risks (to pre-register as gates)

1. **Overnight over-supply**: the caiso-73 shape carries 5-6 GW overnight;
   price-taking flow could deepen overnight λ (current resid +0.8/−0.0/+1.4
   — a small positive buffer exists). Gate: overnight resid must not go
   below −1.5 in any year (symmetric to its current band).
2. **Negative-price hours**: −ε bids flow through λ≈0 glut hours the
   contract-holder would economically curtail; if the measured firm profile
   shows curtailment conduct in negative-hub hours, the bid floor may need
   to be $0 + tie-break rather than −ε. Measure first, then fix the bid
   constant a priori (no sweep).
3. **Evening overshoot**: λ must not cross above actual (the caiso-100 gate
   convention); import volume must not exceed the measured aligned evening
   TWh by more than the current under-shoot magnitude.
4. Standard protections: C1 12/12 holds; C7/C8 PASS; C3c unchanged or
   toward actual; C5a no regression; 2023/2024/2025 all-years one bundle
   (rule 16); single delta vs `caiso102_repro_A`.

## 4. THE ASK

1. Authorize M-EVE-1: the gate + the −ε (or $0, per the §3.2 measurement)
   bid on the two firm blocks, one single-delta B-leg vs `caiso102_repro_A`
   with the §3 gates pre-registered in the FINDING before the solve,
   registered whatever the result (rule 15), promotion on
   no-status-regression (owner call).
2. If refused: the evening lane's remaining named lever is the CT-rung
   offer-surface composition itself (the caiso-92 pooled artifact — its
   2025-slice re-derive is this session's priority 3), but the §3
   decomposition says the rung's PRICE is roughly right (entry 47-59 $) and
   the model simply never gets there — a supply-side fix below the rung is
   the structural answer, not a rung re-price.
