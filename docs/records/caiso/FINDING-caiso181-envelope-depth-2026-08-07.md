# FINDING — caiso-181: the regenerated CAISO outage envelope **IS DEPTH-CORRECT**. The detector never asserts unavailability its own CEMS record contradicts — **interior contradiction is EXACTLY ZERO** — and the +1.1 / +1.6 pp is therefore located in the **offer curves**, not the envelope

**Outcome: PRE-REGISTERED BRANCH I — CLEAN. Both bars clear. READING (i) is adopted.**
The 2026-07-24 regeneration did **not** over-derate. Under `DECISION-MEMO-ercot-148149`
§3 that makes the stale envelope's better fit a confirmed **COMPENSATING ERROR PAIR**:
the phantom-long windows were **masking a pre-existing over-pricing defect**, and removing
them **exposed** it. **No repair is indicated, no LP was spent, and nothing is registered** —
exactly as the charter directs for this branch.

Keeper **UNCHANGED** at `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1,
8 criteria, C3a the sole FAIL). DOF ledger **UNCHANGED at 11 / 8**. No `ScenarioConfig`
field added, removed or re-valued. **No solve was run, so no bundle exists and none is
registered** (stated explicitly so the absence is not read as a skipped registration).
`calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED**. 2023 + 2024 + 2025 only.

Pre-registration: `PRECHECK-caiso181-envelope-depth-2026-08-07.md`, pushed and
blob-verified (sha256 `1c8e91f8…`, 482 lines, byte-identical both sides) **before any
metric was read**. Instrument: `scripts/probes/_caiso181_cems_confrontation.py`.
Record: `results/calibration/_caiso181_cems_confrontation.json`.

---

## 1. THE RESULT — L1, the gating measurement

Route 1 confronts every committed window with the **same CEMS record the detector was
built from**. 100 % of CAISO's envelope is produced by `detect_outages_eventbased`, whose
contract is exact: **zero in-window hours at CF ≥ 0.02 (`ST_GAS_CF_PEAK`)**.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| windows tested | 545 | 456 | 603 |
| in-window hours | 218,880 | 204,096 | 253,752 |
| — of which **interior** | 192,720 | 182,208 | 224,808 |
| contradicted hours (CF ≥ 0.02) | 7,350 | 6,630 | 9,008 |
| — **edge** (first/last calendar day) | **7,350** | **6,630** | **9,008** |
| — **INTERIOR** | **0** | **0** | **0** |
| **interior share (B-1)** | **0.00000000** | **0.00000000** | **0.00000000** |
| B-1 bar | 0.005 | 0.005 | 0.005 |
| max distance from a window boundary | **22 h** | **22 h** | **22 h** |
| share of contradictions within 24 h of a boundary | **1.0000** | **1.0000** | **1.0000** |

**B-1 CLEARS, and it clears at exactly zero — not "near zero".** Across
**599,736 interior in-window hours** in three years, there is **not one hour** in which a
windowed unit's own CEMS shows it generating above the detector's break threshold. The
event-based contract holds **perfectly** wherever the detector actually placed a window.

**Every one of the 22,988 contradicted hours lies within 22 hours of a window boundary**,
in all three years, with **no exceptions**. The maximum is 22 h — strictly below the 24 h
the day-granular round-trip can produce, and unreachable if the detector itself were at
fault. This is not a distributional tendency; it is a hard bound.

**The direct answer to the chartered question: the model is NOT asserting unavailability
its own source contradicts. The depth is correct.**

## 2. H-EDGE — CONFIRMED, ATTRIBUTED, SIZED, and BELOW THE BAR

The pre-registered hypothesis (PRECHECK §2c(2), derived from source **before**
measurement) is confirmed at 100 % concentration. The mechanism is the CSV round-trip:
the deriver works in **hours** (`start = clock[s]`, `last = clock[e-1]`) but writes
`strftime("%Y-%m-%d")`, and the loader re-expands **`outage_start` 00:00 → `outage_end`
23:00**. Up to 23 h at each edge are asserted unavailable that the detector never detected
— and by the event-based contract the hour just outside a window is a **running** hour, so
those are precisely the hours CEMS lights up.

This is CAISO's structural analogue of ERCOT fault 3 — *a coarser-grained representation
used as a finer-grained ceiling* — but it is a **schema quantization seam, not a detection
error**, and it is **smaller than its ERCOT cousin by construction** (≤ 23 h per window
edge, versus a multi-week plateau).

### 2a. B-2 — the envelope-grain magnitude, decomposed

L2 ports ercot-172's `f_ceiling` vs `f_CEMS` to bin grain, using the **shipped loader**.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| raw impossible MW-h | 1,349,277 | 1,714,458 | 1,839,441 |
| **as share of committed depth (B-2)** | **3.68 %** | **4.00 %** | **3.32 %** |
| B-2 bar | 5 % | 5 % | 5 % |

**B-2 CLEARS in all three years.** And the raw figure is the *conservative* one: it
decomposes exactly (identity `(f_cems − f_model)⁺ ≡ (f_cems − 1)⁺ + (min(f_cems,1) −
f_model)⁺`) into two parts, only one of which any envelope could own:

| component | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **BASIS mismatch** — CEMS gross above the bin's **entire** EIA-860 nameplate | 461,441 MW-h (**1.26 %**) | 694,252 MW-h (**1.62 %**) | 414,254 MW-h (**0.75 %**) |
| **ENVELOPE excess** — inside [0,1], the part an availability model owns | 887,837 MW-h (**2.42 %**) | 1,020,206 MW-h (**2.38 %**) | 1,425,187 MW-h (**2.57 %**) |
| — of which **edge-day** | 74.2 % | 79.6 % | 80.8 % |
| — of which interior-day | 25.8 % | 20.4 % | 19.2 % |

The basis term is real and is **not an outage defect**: at the worst bins `f_CEMS` reaches
**1.146 / 1.098 / 1.130** — CEMS gross exceeding the bin's whole nameplate, which no
availability envelope can represent. It is a gross-vs-nameplate capacity-basis question
(§5 item 2), reported here and owned elsewhere.

**The envelope-attributable excess is 2.42 / 2.38 / 2.57 % of depth — under half the B-2
bar in every year.**

**The interior-day residual is NOT the detector.** L1 proves at unit grain that interior
contradiction is *exactly zero*, so that residual cannot be a windowed unit generating
while held down. It is arithmetically forced to be bin-grain capacity allocation — a
**non-windowed** unit at the plant producing more than its nameplate share of the bin
denominator — i.e. the same basis family, below the `f_CEMS = 1` line. Stated as a
consequence of the measurement, not as an assumption.

### 2b. B-3's duration prediction is **FALSIFIED — monotonically, in all three years**

The PRECHECK §4c prediction (mine, derived from caiso-180's shape result) was that
contradictions concentrate in the **LONGEST** windows. The measurement says the opposite,
and says it cleanly:

| duration quartile | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **Q1** (5.0–6.8 d) | **8.32 %** | **9.70 %** | **10.12 %** |
| Q2 (6.8–11.5 d) | 6.25 % | 6.56 % | 6.86 % |
| Q3 (10.8–20.7 d) | 3.67 % | 3.35 % | 3.82 % |
| **Q4** (18.0–153.9 d) | **1.48 %** | **1.41 %** | **1.53 %** |

Monotone decreasing, a 5.6× / 6.9× / 6.6× gradient. **Reported as a falsification, not
smoothed over** — and it is the sharpest corroboration of H-EDGE in the record: an edge
cost is a **fixed ~23 h per WINDOW**, so as a *share* it scales as 1/duration. The
measured gradient tracks the duration ratio almost exactly. The contradiction is a
**per-window constant, not a per-MW-h property.**

*This falsifies the prediction I derived from caiso-180, not caiso-180's own measurement.*
Its window-shape result (fewer/longer → more/shorter) is a measured fact and stands.

### 2c. The seam is **NOT** the caiso-180 driver — the arithmetic, run against interest

Because the cost is per-window and the regeneration **added** windows, H-EDGE is a genuine
contributor to the caiso-180 result. It is a **small** one. At the measured per-window edge
cost (1,208 / 1,780 / 1,910 MW-h):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| windows added (PRE → GUARD) | +108 | +53 | +126 |
| implied added edge over-derate | 0.130 M MW-h | 0.094 M MW-h | 0.241 M MW-h |
| vs \|A1→A0 depth change\| | 1.35 M | 4.08 M | 5.44 M |
| **share of the measured depth change** | **9.7 %** | **2.3 %** | **4.4 %** |

**The seam cannot account for the +0.5 / +1.1 / +1.6 pp.** It is ~2–10 % of the depth
movement that carried it. Reported at full magnitude and labelled **immaterial against its
own bar** — never rounded to "no effect", and never inflated into an explanation it cannot
support.

---

## 3. WHAT THIS SETTLES — the memo §3 framing, resolved

The pre-registration fixed two readings and what separates them. The separator was the
presence, magnitude and **location** of a same-source CEMS contradiction. The measurement
is unambiguous:

> **READING (i) — DEPTH-CORRECT / EXPOSER — is ADOPTED.**

The envelope's windows sit on genuinely dead hours. The stale envelope did **not** fit
better because it was more accurate; it fit better because **the keeper's offer curves had
been identified against its phantom depth and were silently compensating for it**. That is
the memo §3 compensating-error pair, now confirmed on CAISO's own data rather than
transferred: *"multiplying layers hides the error by over-derating everywhere; removing the
product exposes it."* CAISO has no product to remove — it runs the **window layer alone**
(§4) — but the same asymmetry holds one layer down.

**The +1.1 / +1.6 pp is therefore LOCATED. It belongs to the offer curves.** caiso-180
filed it as an open root-cause issue with a suspected owner; this session **discharges the
suspicion by eliminating the alternative**. The residual is not a data error hiding in the
envelope, so re-identifying the offer curves can no longer bury one.

**Rule 14 `[R-ACCURATE]` is vindicated rather than merely obeyed.** caiso-180 kept the
accurate input against a worse fit on principle. Route 1 now shows the input was in fact
correct, and that the worse fit was the *symptom of a defect elsewhere becoming visible* —
which is precisely what rule 14 predicts a discovered bug looks like.

---

## 4. What this session did NOT do, and why

- **No revert.** Not available in any branch (PRECHECK §5), and the measurement removes
  even the appearance of a case for one.
- **No repair built.** Both bars cleared; the pre-registration authorises a repair only in
  branch II. H-EDGE is **confirmed but sub-bar**, so it is **filed, not fixed** (§5 item 1).
- **No offer-curve re-tune.** The memo §5 sequencing ruling binds this session
  (PRECHECK §9): construction question first, offer curves last. That ordering has now
  *paid off* — the construction question is answered clean, so the re-identification can
  proceed on a verified input instead of over a possible data error.
- **No LP, no bundle, no registration.** Charter-directed for branch I. Rule 15
  `[R-DASHBOARD]` is not engaged because nothing solved; rule 16 `[R-ALLYEARS]` likewise.
- **ROUTE 2 NOT REACHED.** It is entered only on branch III (ambiguous). Route 1 was
  unambiguous — a bar cleared at exactly zero with a hard 22 h bound. **The comparator does
  exist**, however, and that is a durable Phase-0 deliverable: CAISO's daily **Curtailed and
  Non-Operational Generator** reports are already fetched (1,094 daily snapshots), curated
  (`caiso-dam-outage-windows.parquet`, 794,103 episodes, 2021-05-07 → 2025-12-31),
  crosswalked, wired behind `ScenarioConfig.caiso_dam_outages` (default off) and **committed**.
  Its matrix cell is `U`. **Not armed, not compared, not adjudicated here** — and any future
  session that reaches for it must clear the charter §9 **definitional seam** first
  (published = *unavailability*; the CEMS detector = *non-operation*).
- **The NEISO precedent was honoured as a constraint, not a lead.** Route 1 is immune to
  that seam by construction — it compares the detector to the **same** record it is built
  from — which is why a zero here is a statement about *construction*, and why no
  definitional argument can explain the result away.
- **Nothing from PR #3685 transferred but method.** CAISO has no two-layer product
  (re-verified: partial/short files header-only, `campd-partial-outages.csv` ERCOT-only,
  all three gates off, zero coal). No `min()`/product rule was proposed; G-COAL148 was not
  treated as relevant. Rule 25 `[R-ISO-SCOPE]`, rule 28 duty d.

### 4a. Scope and instrument honesty

- **34 / 32 windows excluded from L1 are all `eia923_netzero`** (2 in 2023, 2 in 2024, 32
  in 2025): synthetic full-year rows for **non-CEMS** plants — hospitals, universities,
  small cogens — derived from EIA-923, not CAMPD. Confronting them with CEMS is a category
  error (their defining condition is *having no CAMPD record*), so they are excluded and
  the exclusion is stated. The 2025 jump is the EIA-923 filing lag widening that
  population; it is not a coverage gap in the test.
- **Conservative conventions, all pre-registered.** A missing/NaN CAMPD hour is **not**
  counted as a contradiction; CF uses the detector's **own** `detect_mw` basis via the
  deriver's own `unit_capacity_mw`; L1 runs entirely on the CAMPD clock, so it carries **no
  timezone exposure**. Every convention can only *under*-count contradictions — and the
  count still came back exactly zero.
- **Feb 29 2024** (77,321 MW-h of CEMS gross) has no counterpart on the model's fixed
  8760-hour clock and is excluded from **both** sides of L2. Disclosed, not silent.
- Instruments **reused, never re-implemented**: `build_capacity_index` / `unit_capacity_mw`
  (the deriver's own), `campd.CAMPD_UNIT_PLANT_REMAP`, and for L2 the shipped
  `unit_outage_derate_factors` / `_generic_unit_outage_target` / `_iso_plant_capacity`.

---

## 5. NEW OPEN ITEMS — filed, sized, and NOT fixed here

1. **The H-EDGE day-granular schema seam.** `campd-unit-outages-*.csv` stores window
   **dates**; the detector produces window **hours**. The round-trip re-expands every
   window by up to 23 h at each edge, asserting unavailability the detector never detected.
   **CONFIRMED at 100 % of unit-grain contradictions** and sized at **2.4 / 2.4 / 2.6 % of
   envelope depth** (74–81 % of the envelope-attributable excess). Below this session's
   bar, so **not repaired**. The admissible repair is named in PRECHECK §8: carry the
   window's start/end **hour** through the schema and the loader — **zero DOF**, no
   parameter, no threshold re-valued, a strict **grain** change of the ercot-174
   BE-1/BE-2/BE-3 class. It needs its **own** charter, precommit and gates.
   **NOTE: this is a CROSS-ISO schema property, not a CAISO one** — the same writer and the
   same loader serve all six ISOs. Its magnitude elsewhere is **unmeasured**, and no
   verdict transfers (rule 25). It is likely **larger** where windows are shorter and more
   numerous.
2. **The capacity-basis mismatch.** CEMS gross exceeds the bin's entire EIA-860 nameplate
   at 1.26 / 1.62 / 0.75 % of depth (`f_CEMS` up to 1.146), concentrated at the CC bins —
   including the two `CAMPD_UNIT_PLANT_REMAP` plants 62115 / 62116 (AES Alamitos /
   Huntington Beach). Gross-vs-net and nameplate-vs-demonstrated-capability. Not an outage
   mechanism; belongs to the fleet-capacity lane. Reported, not acted on.

## 6. Governance

Rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`: the accurate envelope stays and is now
*verified* accurate; no mechanism was judged by its effect on the fit. Rule 13
`[R-MEASURED]`: no measured outcome entered any input; nothing was tuned to C3a, which is
a live FAIL and is REPORTED only. Rule 15 / 16: **no solve, therefore no bundle and no
registration** — stated so the absence is not mistaken for an omission. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no out-of-training year was solved, scored, registered or
read; the holdout spend freeze was respected and both markers left untouched (owner acts).
Rule 23 `[R-FROZEN-DERIVE]`: **no derive re-run, no identification constant re-valued, no
output byte changed.** Rule 24 `[R-REGISTRY]`: no field added or re-valued; no off-registry
channel. Rule 25 `[R-ISO-SCOPE]`: CAISO-scoped; no other ISO's keeper shard, registry
sidecar, status part or bench file read or written; the item-1 cross-ISO note transfers
**no verdict**. Rule 27 `[R-PUSH]`: the pre-registration was pushed and blob-verified
before any metric was read; every push blob-verified; no existing ≥300-line source file
rewritten. Rule 28 `[R-MECH-MATRIX]`: the `campd_outage_windows` CAISO cell and §5.2 are
stamped **in this session**; `check_mechanism_matrix.py` exit 0.

**DO-NOT-REDO honoured in full** — `battery_dispatch_adder` not re-opened or re-derived,
`_degradation_cost_per_mwh` routing closed, the AS-power-reservation family closed, the
N–S topology lever FORBIDDEN and untouched, `caiso_ps_charge_shape_anchor` stays `G`, and
`unit_outage_short_windows` / `unit_partial_outage_windows` not re-tested (caiso-180's `I`
cited, not re-minted).

## 7. Disposition and the named successor

1. **The envelope STAYS and is now VERIFIED depth-correct.** The caiso-180 open
   root-cause issue is **narrowed to one owner**: the offer curves.
2. **THE NEXT SESSION'S CHARTERED LEVER IS THE OFFER-CURVE RE-IDENTIFICATION**, on the
   rule-23 `[R-FROZEN-DERIVE]` **source-data-changed** basis, cited to the 2026-07-24 CAMPD
   data change — **not** to the C3a residual. Its precondition is discharged: the
   construction question is answered, so a re-tune can no longer bury a data error inside a
   fitted curve. It is scored **leave-one-year-out within 2023–2025** before any promotion
   (rule 22), and C3a remains a **reported** quantity, never the promotion basis (rule 1).
3. **No promotion, and none was ever available here.** No solve; keeper designation
   unchanged, exactly as the pre-registration expected.
4. **No existing adjudication is repealed.** Nothing was tested that could repeal one.

## 8. Known-open, carried forward unchanged

1. **The N–S congestion majority** — model 5.2 / 2.4 / 2.9 % of the measured NP15–ZP26
   basis; the N–S topology lever stays **FORBIDDEN** (caiso-164 §0/§6).
2. **C3a's first named contributor is the WALLED hourly PS water state**
   (`FINDING-caiso140` §B) — owner-level data, not a session lever. Its second named
   contributor is now **located in the offer curves** (§7.2).
3. **`battery_dispatch_adder` is a PERMANENT DECLARED-RESIDUAL DOF** — all three exits
   closed (caiso-176 / 178 / 179). Its ledger `root_cause` still needs re-wording to
   *permanent declared residual* by a **keeper-lane** session. Not this one.
4. **`unit_outage_maxgen_events` is a CAISO DATA GAP** (no registry exists) — a data-intake
   charter; reported, not armed.
5. `curate_dam_public_bids.py` cannot process a full CAISO year (~14.3 GB vs ~15 GB RAM,
   caiso-178). Unfixed; needs a data-contract session. **Nothing here depended on it.**

**Next shorthand: caiso-182 — the offer-curve re-identification.**
