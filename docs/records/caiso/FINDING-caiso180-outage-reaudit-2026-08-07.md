# FINDING — caiso-180: the CAISO outage re-audit is **DONE**. The regeneration is **MATERIAL and UNFAVOURABLE**, the guard leg is inert, and the accurate envelope **STAYS**

**Outcome: PRE-REGISTERED BRANCH I — MATERIAL, and the current envelope scores WORSE.**
Under rule 14 `[R-ACCURATE]` that is a **discovered bug**, not grounds to revert: the keeper's
offer curves were identified against a superseded phantom-outage envelope and have been
silently compensating for it. **The current envelope stays; the residual becomes an open
root-cause issue.**

Keeper **UNCHANGED** at `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1, 8 criteria,
C3a the sole FAIL). DOF ledger **UNCHANGED at 11 / 8** — verified per arm. No `ScenarioConfig`
field added, removed or re-valued. `calibration-complete.json` and `holdout-freeze.json`
**UNTOUCHED**. 2023 + 2024 + 2025 only, one bundle per arm, arms sequential, years sequential.

Pre-registration: `PRECHECK-caiso180-outage-reaudit-2026-08-07.md`, pushed and blob-verified
(sha256 `565f4590…`, blob `37217dd7…`) **before any scored metric was read**.
Runs: `2026-08-07-caiso-180-a0-control` · `-a1-pre` · `-a2-regen`, all three registered.
Records: `_caiso180_outage_reaudit.json`, `_caiso180_sha_ledger.json`, `_caiso180_gate_check.json`.
Instruments: `scripts/probes/_caiso180_arm_identity.py`, `scripts/probes/_caiso180_gate_check.py`.

---

## 1. Phase 0 — the envelope IS recoverable, and it reconciles exactly

**Branch (a) fired.** The clone was shallow (271 commits); `git fetch --deepen=200` exposed the
history. Three states, all recovered as exact blobs:

| state | commit | blob | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|
| **PRE** | `d7c9a53a` (`49e85fb4^`) | `e40847c8` | **439** | **405** | **509** |
| **REGEN** | `49e85fb4` *"re-derive CAISO in full (owner instruction)"* | `3dc01fae` | **640** | **622** | **733** |
| **GUARD** | `6a8f285c` *"neiso-65: adopt guard-corrected CAMPD extracts"* | `e0de2fc3` | **547** | **458** | **635** |

PRE and REGEN reproduce the `intake_log`'s quoted figures **in both directions**, which
identifies them as the right blobs rather than lookalikes. GUARD is **byte-identical** to the
current on-disk file (`c4ded33d…`), so the ladder terminates exactly at what the keeper reads.

### 1a. The charter described ONE change. There are TWO.

The keeper does **not** consume the 640/622/733 state. The merit-order guard subsequently moved
the economic-layup windows into `campd-unit-outages-layup-CAISO.csv`, and the arithmetic closes
with **zero residual**: 547+93 = 640, 458+164 = 622, 635+98 = 733. Because the legs are
opposite-signed and could partially cancel, the third arm was made **mandatory rather than
conditional**, and the pre-registration fixed in advance that a null on the net difference would
not license a null on either leg. That precaution turned out not to be load-bearing — the legs
did not cancel, the guard leg is simply small (§3) — but it was the right call to take before
the numbers were known.

---

## 2. The control reproduces the keeper EXACTLY — **$0.000 drift, all three years**

The charter's central warning was that caiso-175 measured incidental same-head code drift at
+0.168 / +0.049 / +0.115 $/MWh — **larger than its own treatment** — so differencing against
committed keeper metrics would misattribute.

**At this head there is no drift at all:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| A0 − KEEPER, load-weighted mean LMP | **+0.000** | **+0.000** | **+0.000** |
| A0 − KEEPER, C3a | **+0.00 pp** | **+0.00 pp** | **+0.00 pp** |

**BRANCH IV does NOT fire.** Every difference quoted below is A-versus-A at one head, and the
control additionally proves — in *effect*, not merely by inspection — that the eight
`ScenarioConfig` fields added since the keeper solved are inert for CAISO (§5).

---

## 3. THE RESULT — decomposed into its two legs

C3a is the load-weighted mean LMP % error on the **RT** basis (the gating row; the DA rows in
the same criterion are SKIPPED diagnostics and are not the gate).

| arm | envelope | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| KEEPER | — | +4.2 % PASS | +11.5 % FAIL | +14.7 % FAIL |
| **A0** | GUARD (current) | +4.2 % PASS | +11.5 % FAIL | +14.7 % FAIL |
| **A1** | PRE (pre-regeneration) | +3.7 % PASS | +10.4 % FAIL | +13.1 % FAIL |
| **A2** | REGEN (guard-off) | +4.3 % PASS | +11.6 % FAIL | +14.8 % FAIL |

Materiality bar, pre-registered at **|Δ| ≥ 1.0 pp on C3a in any year**:

| difference | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **A1→A2 — the REGENERATION leg** (the chartered object) | +0.60 pp | **+1.20 pp** | **+1.70 pp** | **MATERIAL** |
| **A2→A0 — the GUARD leg** | −0.10 pp | −0.10 pp | −0.10 pp | **IMMATERIAL** |
| **A1→A0 — the TOTAL unaudited input change** | +0.50 pp | **+1.10 pp** | **+1.60 pp** | **MATERIAL** |

In $/MWh: the regeneration adds **+0.31 / +0.44 / +0.60**, the guard removes **−0.05 / −0.05 /
−0.07**, net **+0.26 / +0.39 / +0.53**.

**The regeneration is essentially the entire effect — roughly 12× the guard leg.** The guard
leg is inert at this bar and, where it moves at all, moves *favourably*.

**Independent corroboration across five keepers.** caiso-123 attributed the guard's own effect
at **−0.18 % (favourable)** and the extract-content change at **+1.24 % λ**, measured on
`2026-07-26-caiso120-meritguard-a1`. This session, on a keeper five promotions later and a
corrected TAC load series, measures the guard at **−0.10 pp (favourable)** and the regeneration
at **+1.20 pp in 2024**. Two independent measurements, different keepers, same split. That is
the strongest thing in this finding, and it was not sought.

---

## 4. The mechanism, and why the direction is what it is

The regenerated envelope is **deeper** in the two failing years — outage MW-hours, measured
directly from each blob:

| year | A1 PRE | A2 REGEN | A0 GUARD | median window: PRE → REGEN |
|---|---:|---:|---:|---|
| 2023 | 38.03 M | 44.46 M | 36.68 M | 14.7 d → 10.9 d |
| 2024 | 38.80 M | 47.75 M | 42.88 M | 16.4 d → 11.6 d |
| 2025 | 49.99 M | 60.06 M | 55.43 M | 16.6 d → 11.5 d |

**The regeneration did not simply "add windows" — it changed window SHAPE.** The superseded
pre-2026-07-19 detector produced *fewer but far longer* windows; the current one produces *more
and shorter* ones. That is exactly the signature of replacing a phantom-outage detector, and it
is independent evidence that the 07-24 change was a genuine accuracy improvement.

The dispatch consequence is coherent and monotone: the deeper envelope removes cheap CC
capability and dearer units backfill, which lifts the clearing price.

| class | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC_REGULAR (TWh, A1→A0) | −0.11 | **−0.44** | **−0.67** |
| ST_GAS | +0.03 | +0.13 | +0.07 |
| CT_PEAKER | +0.02 | +0.04 | +0.06 |

Same signature as the MISO and NEISO guard re-audits, opposite sign because this change *removes*
supply rather than restoring it.

**Why it lands unfavourably:** the model was already **over**-priced in 2024/2025 (+11.5 / +14.7 %),
and the accurate envelope pushes it *further over*. The stale envelope's phantom-long windows
were, in net, holding the model's price down in the two years where it runs hot.

---

## 5. Every pre-registered gate, and the two that were corrected

| gate | result |
|---|---|
| L1 — identity on the keeper's own 692 keys | **PASS**, 0 differences, all three arms |
| L2 — arm-to-arm identity over all 700 keys | **PASS**, 0 differences |
| L3 — additive schema drift, gated | **PASS** — 8 new fields (4 ERCOT, 2 MISO, 2 NYISO), every one at its `ScenarioConfig` default, none CAISO-scoped |
| sha ladder, before == after == intended | **PASS** on all three arms; envelope restored to `c4ded33d…`, matching committed |
| envelope distinctness | **PASS** — no two arms share a derate census |
| DOF ledger 11 / 8 | **PASS** per arm |
| partial audit | **NO** — all three arms completed |

**Two corrections, both reported rather than quietly applied.**

**(a) §3a leg 2 is WITHDRAWN AS MALFORMED, falsified by this session's own measurement.** It
asserted `A1 ≥ A0, A2` in available capability on the inference *"fewer outage windows ⇒ more
capability"*. Window count is not envelope depth: in 2023 the 439-window PRE envelope is
*deeper* (38.03 M outage MW-h) than the 547-window GUARD one (36.68 M), so A1 legitimately
derates **more** plant-tranches than A0 that year (284 vs 275) and the gate would have voided a
sound arm. A second, independent reason surfaced in 2024: A1 carries **less** depth than A0
(38.80 M vs 42.88 M) yet still derates more tranches (276 vs 261), because its windows touch
**more plants** (38 vs 36). Neither window count nor depth orders the derate census. Replaced by
a pairwise **distinctness** check — the hazard actually worth catching is two arms silently
solving the same input — with the sha ladder remaining the load-bearing proof.

**(b) The §4 predicate was SPLIT, not relaxed.** The first implementation compared over the
union of key sets, which is stricter than the pre-registered text (*"key-by-key over all 692
keys"*), and it fired on 8 purely additive fields. Nothing among the keeper's 692 keys was
exempted — **zero of them differ in value and none is missing at HEAD**, so the recipe
`--replay-bundle` reproduced is byte-identical. The additive keys were **not** waved through on
narrative: L3 fails closed unless each is at its code default *and* outside CAISO's namespace.
The control's $0.000 drift (§2) then confirms their inertness empirically.

### 5a. What did NOT move

**No criterion status differs across any arm.** C1, C2, C3b, C4, C8 PASS everywhere; C3a FAIL in
2024/2025 everywhere; determination **NOT-YET** for all three arms and the keeper. The
regeneration does not create a new failure — it **widens an existing one**. C6 `UNATTESTED` and
C3c `FAIL`-instead-of-`CAVEAT` on the arms are artifacts of probe arms carrying no
`calibration_attestation.json` (the keeper's ledger exceptions live there), **not** envelope
effects; stated so the reader does not mistake them for findings.

---

## 6. The rule-14 gate check — asked as a question, answered per gate

Record: `_caiso180_gate_check.json`. **No gate was armed; none may be armed without its own
pre-registration.**

| gate | reading | basis |
|---|---|---|
| `unit_outage_short_windows` | **E — empty BY CONSTRUCTION** | detector filters `plant_group == "COAL"`; CAMPD's CAISO population is **Natural Gas / Other Gas / Pipeline Natural Gas / Wood**, zero coal |
| `unit_partial_outage_windows` | **E — empty BY CONSTRUCTION** | same identification guards |
| `unit_outage_maxgen_events` | **DATA GAP, not a structural n/a** | no CAISO input exists at all |
| layup companion | **NOT a finding** | the deriver's own `--help`: a companion *"which no loader reads"* |

CAISO's only model-fleet coal is **Argus Cogen Plant** (plant 10684, 2 × 25 MW, ZP26) —
**0.16 %** of fleet capacity — and it is **not a CAMPD reporter** (0 rows in both the outage and
layup extracts). Arming either window gate is therefore **provably inert**, and OFF is correct
*and examined*.

**Cross-ISO control — corroborated, not asserted.** Short-window row counts track coal fleet
size across all six ISOs: **PJM 934, MISO 987, NEISO 1, CAISO 0, NYISO 0**. The emptiness is a
property of the detector's scope, not of CAISO's wiring. This independently reproduces
**caiso-136's** existing `I` verdict, which is **cited rather than re-minted** (rule 28
DO-NOT-REDO) — on a stronger basis than the original: not "no rows produced" but "no coal in the
source population at all".

**The maxgen gate is deliberately NOT collapsed into reading E.** Its input does not exist
rather than being provably empty: the registry is a hand-curated per-ISO set of declared
capacity-emergency instruments built for MISO's price-formation lane, and CAISO *does* declare
real analogues (EEA levels). That is a data-intake gap. **Reported, not armed** — landing a
CAISO registry is a separate charter.

---

## 7. Disposition

1. **The accurate envelope STAYS.** Rule 14 is explicit that a degraded criterion does not
   revert a correct measured input, and rule 1 that a structurally-correct input is never judged
   by whether it improves the fit. The current envelope is the current detector plus the adopted
   guard correction, and §4 shows the regeneration is a genuine detector improvement.
2. **A new OPEN ROOT-CAUSE ISSUE is filed:** the keeper's offer curves carry **+1.1 / +1.6 pp**
   of C3a in 2024/2025 that was previously absorbed by a superseded outage envelope. Any
   re-tune is a **later, separately chartered** session, scored leave-one-year-out within
   2023–2025 before promotion (rule 22).
3. **No promotion, and no promotion was ever available here.** C3a is a live FAIL, so a C3a move
   is REPORTED and never a promotion basis (rule 1). The keeper's designation is unchanged, as
   the pre-registration expected.
4. **The re-audit precondition is DISCHARGED on this item.** caiso-171 named the re-audit a
   precondition for spending 2022; it is now done, with the data change measured, decomposed and
   attributed. This is **not** a statement about the freeze or the marker — the holdout spend
   freeze is ACTIVE, CAISO does **not** hold `complete`, and both remain **owner acts**.

## 8. Known-open, carried forward unchanged

1. **The N–S congestion majority** — model 5.2 / 2.4 / 2.9 % of the measured NP15−ZP26 basis;
   the N–S topology lever stays **FORBIDDEN** (caiso-164 §0/§6).
2. **C3a is an OPEN root-cause issue**, now with a second named contributor (§7.2) beside the
   unrestrained pumped-storage pumping of FINDING-caiso140 §B, whose closure route is the
   **walled** hourly PS water state — an owner-level data question.
   `caiso_ps_charge_shape_anchor` stays `G`.
3. **`battery_dispatch_adder` is a PERMANENT DECLARED-RESIDUAL DOF** — all three exits closed
   (caiso-176/178/179). Not re-opened here. Its ledger `root_cause` should be re-worded to
   *permanent declared residual* by a future keeper-lane session.
4. `curate_dam_public_bids.py` cannot process a full CAISO year (~14.3 GB vs ~15 GB RAM,
   caiso-178). Unfixed; needs a data-contract session. Nothing here depended on it.
5. **NEW:** the `unit_outage_maxgen_events` CAISO data gap (§6) — a data-intake charter, not a
   calibration lever.
