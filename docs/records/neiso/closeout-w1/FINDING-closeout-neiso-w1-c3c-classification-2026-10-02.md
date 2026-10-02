# FINDING — closeout-NEISO wave 1, step 1: one C3c classification for 2022 / 2023 / 2025 (DRAFT for owner signature, R-10)

Lane `closeout-neiso-wave1`, 2026-10-02. Zero LP. Keeper `2026-09-26-neiso-119-anchor-fuelsec`
(`results/calibration/neiso119_span`), determination CALIBRATED, unchanged by anything here.
The 2025 re-score on EIA-923 Final is lane closeout-A's and is not duplicated.

## 1. The defect: three labels for one phenomenon

| year | RT h > $300 (model 0) | status-part label | where the label comes from |
|---|---|---|---|
| 2022 | 117 | ACCEPTED MODEL-CLASS LIMITATION | **no** attestation entry; reached only by the C3c standing-rule scoped path (`calibration_verdict.py` ~L1700–1730, `classification = MODEL_LIMIT`) |
| 2023 | 15 | ACCEPTED MEASURED-INPUT LIMITATION | attestation `exceptions[price_tail, 2023]` with **no `kind`** → `_apply_ledger` default `MEASURED_LIMIT` (`calibration_verdict.py:1733`); the entry's own text says `MODEL MISS` |
| 2024 | 8 | PASS (small-count, \|Δ\| ≤ 10 h) | entry present but inert |
| 2025 | 20 | ACCEPTED MEASURED-INPUT LIMITATION | as 2023 |

The 2023/2025 label is an artifact of a missing field, not a judgement: nobody ever argued the tail is a
measured-input limitation, and the entries' own `classification` reads MODEL MISS. The 2022 label is right
in kind but rests on no owner-signed entry.

## 2. The decomposition (zero LP, `c3c_decomposition.py` → `c3c_decomposition.json`)

Committed ISO-NE SMD hub sheets (`data/raw/lmp-data/NEISO/<Y>_smd_hourly.xlsx`, sheet `ISO NE CA`):

| year | RT h > $300 | of which DA ≥ $300 | **RT-only** | median DA on those hours | RT energy-component share | months (RT h) | top event days |
|---|---:|---:|---:|---:|---:|---|---|
| 2022 | 117 | 9 | **108 (92.3 %)** | $209.60 | 0.995 | Dec 52 · Jul 15 · Feb 14 · Jan 11 · Mar 10 · Nov 7 · Aug 5 · May 2 · Jun 1 | Dec-24 23, Dec-23 9, Mar-29 9, Dec-25 8, Dec-26 6 |
| 2023 | 15 | 1 | **14 (93.3 %)** | $169.57 | 0.996 | Feb 10 · Sep 4 · Jul 1 | Feb-04 9, Sep-05 2, Sep-06 2 |
| 2024 | 8 | 0 | 8 (100 %) | $159.38 | 1.000 | Aug 3 · Jun 2 · Jul 2 · Dec 1 | Aug-01 3 |
| 2025 | 20 | 6 | **14 (70.0 %)** | $242.72 | 1.000 | Jun 8 · Jan 5 · Jul 2 · Nov 2 · Feb/Aug/Dec 1 | Jun-24 5 |

Reserve-shortage hours from the primary source (ISO-NE IMM Annual Markets Reports; 2025 AMR Table 4-6):
negative **Total30** margin 2022 **1.4 h**, 2023 0.5 h, 2024 2.2 h, 2025 3.6 h; negative Total10 0.1 / 0.3 / 1.1 / 0.3 h
(the research shard `SHARD-NEISO-closeout-research-2026-10-02.md` §4 carries the page citations).

**Reading.**

1. The tail is **system-wide energy-price formation** (energy component ≈ 100 % of RT LMP in every tail hour — not
   congestion, not loss), and **70–93 % of it never appears in the day-ahead market**. A day-ahead-equivalent,
   hourly, cost-based LP has no channel for RT-only, five-minute transient price formation.
2. **Real reserve shortage explains ≤ 4 h a year** (1.4 h in 2022 against 117 RT hours). The RCPF-stacked
   scarcity that the co-opt can produce therefore cannot close the gate even with perfect reserve physics:
   2022 would need ≥ 59 h, 2023 ≥ 8 h (the real DA cleared ≥ $300 in only 5), 2025 ≥ 10 h.
3. What remains is oil-steam / fast-start offer conduct, fast-start pricing (+$5.68 on the 2022 system LMP, IMM
   2022 AMR Table 3-1) and Pay-for-Performance-era offer incentives — none an LMP mechanism admissible under rule 13
   without an offer adder tuned to the tail, which rule 1 forbids.

**What is in representation and wrong today** (being repaired for accuracy, not for the gate — §4 of the PRECOMMIT):
the event-day Algonquin gas price (Wednesday-only prints; model $12.5–15 vs IMM $35.37 Dec 24–27 2022) and
fuel-name reserve eligibility (2,855 MW of oil steam counted as ten-minute reserve; spin served by offline quick-start).
Neither can produce the missing RT-only hours; both make the event-day price more faithful.

## 3. Draft classification for owner signature

One kind for all three years: **model-class**. Proposed attestation entries (replace the two kind-less
2023/2025 `price_tail` entries; add 2022). Not written to the keeper attestation by this lane — signing and the
attestation edit + status rebuild are the owner's / desk's.

```json
[
  {"criterion": "price_tail", "year": "2022", "kind": "model-class",
   "metric": "hours RT hub LMP > $300/MWh (C3c, NEISO $300 threshold)",
   "magnitude": "model 0 h vs RT actual 117 h (DA 27 h); 108 of 117 RT-only",
   "reason": "OWNER DECISION: <date, session — pending signature> (R-10, closeout plan §5.0). EXHAUSTION RECORD: (i) zero-LP decomposition docs/records/neiso/closeout-w1/c3c_decomposition.json — 92.3 % of tail hours RT-only, energy component 0.995, median DA $209.60 on the tail hours; (ii) real reserve shortage 1.4 h Total30 (ISO-NE IMM 2022 AMR), so RCPF scarcity cannot supply >= 59 h; (iii) refuted/inert within-class families: measured_offer_surface I (neiso-58), da_virtual_bids R (neiso-76), neiso_rcpf_postsolve_overlay G (rule 19 under co-opt), dynamic_reserve_requirements alone R (neiso-57/111: does not bind), winter fuel-security family dormant (neiso-110: oil burn is availability, not price), dual_fuel_oil_daily_parity refuted as the oil driver (neiso-110). OPEN RESIDUAL LANE: closeout-NEISO step 3 scarcity-physics arm (AGT event-day completion + ULSD daily + response-scoped eligibility + measured nested requirements; PRECOMMIT-closeout-neiso-scarcity-physics-2026-10-02.md) — fidelity, not expected to close the gate; Elliott Dec 23-26 is 46 of the 117 h."},
  {"criterion": "price_tail", "year": "2023", "kind": "model-class",
   "metric": "hours RT hub LMP > $300/MWh (C3c, NEISO $300 threshold)",
   "magnitude": "model 0 h vs RT actual 15 h (DA 5 h); 14 of 15 RT-only",
   "reason": "OWNER DECISION: <pending>. EXHAUSTION RECORD: as 2022; 93.3 % RT-only, real DA >= $300 in 5 h against a gate floor of 8 h (CHARTER-neiso75 §2.4); Total30 shortage 0.5 h. 9 of 15 h are the Feb-04 arctic-blast day. OPEN RESIDUAL LANE: as 2022."},
  {"criterion": "price_tail", "year": "2025", "kind": "model-class",
   "metric": "hours RT hub LMP > $300/MWh (C3c, NEISO $300 threshold)",
   "magnitude": "model 0 h vs RT actual 20 h (DA 12 h); 14 of 20 RT-only",
   "reason": "OWNER DECISION: <pending>. EXHAUSTION RECORD: as 2022; 70.0 % RT-only; Total30 shortage 3.6 h across the two PFP events (Jun-24, Nov-23; 2025 AMR §7.3). OPEN RESIDUAL LANE: as 2022 (Jun-24 is the summer test of the arm)."}
]
```

Consequences, computed from the scorer's code path, not asserted: the determination is unchanged (C3c is
supporting-tier; `kind: model-class` is admissible there under v3.0 and C3c is the only ledgerable criterion
under v3.1). All three caveats read **ACCEPTED MODEL-CLASS LIMITATION**. Rule 22 `[R-C3C]`'s lone-failure route
stays valid (lone C3c, C6 passes). Whether 2025 drops "with-caveats" after closeout-A's EIA-923 Final re-score is
closeout-A's to report; this classification does not depend on it.

## 4. Question for the owner

Sign the three entries now (the decomposition R-10 asks for is §2), or hold them until the step-3 arm has run?
Recommendation: **sign now**. The arm is a fidelity repair whose own PRECOMMIT predicts it does not close the
gate, and the entries already name it as the open residual lane, so a later PASS simply makes them inert in place.
