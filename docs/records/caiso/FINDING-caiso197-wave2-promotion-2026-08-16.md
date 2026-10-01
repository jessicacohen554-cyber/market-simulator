# FINDING — caiso-197 (Wave 2): the composed ladder SURVIVES WHOLE and the final rung is PROMOTED keeper `2026-08-16-caiso-197-w2-r5` under the pre-committed protocol §6 — ledger 11/8 → 10/7, the C1 volume face of the open lane HEALED, C3a's price face honestly declared as the campaign's exhausted residual

**Protocol:** `caiso191-integration-protocol-2026-08-11.md`, pre-committed
2026-08-11 BEFORE any Wave-1 result existed; executed without amendment on the
re-anchored caiso-196 base (the owner's promotion = the re-anchor
authorization; the caiso-197 session brief instructed exactly this ladder).
Registered rungs: **`2026-08-16-caiso-197-w2-r3`** (+L3) and
**`2026-08-16-caiso-197-w2-r5`** (+L5, the final rung — now keeper).
2023–2025 only; both holdout markers and the spend freeze untouched;
rule 22 D-5(b) does not fire (no `complete` marker).

## 0. Direction-hazard regime (campaign clause, verbatim, binding at every rung)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**PROMOTION IS C3a-BLIND (§6)** — and the data exercised the clause in both
directions this campaign: lane 2's sign was favorable, lane 5's measured sign
was ANTI-favorable, and both were accepted on their structural gates alone.

## 1. The ladder as executed (inclusion strictly by Wave-1 structural verdicts)

| rung | content | inclusion basis | verification |
|---|---|---|---|
| 0 CONTROL | caiso-196 keeper recipe replayed (`caiso197_l2_control`) | protocol §3 | **BIT-ZERO** vs the committed keeper (max \|Δ\| = 0.0, every zone-hour and class-hour, all three years; noise floor 0.0 quoted first; seam caps 16055/16452/16148 log-verified; `hydro_ror_split=false` disclosed) |
| 1 (+L1) | — EMPTY | caiso-192: the merit guard is already applied in the committed extract | protocol §2: renumber by omission, no backfill |
| 2 (+L2) | `wefor_multiplier`→1.0, `wefor_residual`→0.0, groups {CC_REGULAR} (= `caiso197_l2_wefor`) | lane 2 ACCEPTED 4/4 | G-ONEMECH exact; ledger 11/8→10/7; engaged 34.6–36.8k zone-hours |
| 3 (+L3) | + `gas_st_wefor_base_override`=0.1591 (`caiso197_w2_r3`) | lane 3 ACCEPTED 5/5 | diff vs base exactly the lane-3 move; vs control exactly the 4-field ladder; composed ledger **10/7**; engaged 6.9–9.6k zone-hours; C1 healing intact (−3.94) |
| 5 (+L5) | + `caiso_ps_plant_params`=true (`caiso197_w2_r5`) | lane 5 ACCEPTED 6/6 | diff vs base exactly the lane-5 move; vs control exactly the **5-field ladder over 714 keys** (G-DELTA recomputed by the attestation generator); composed ledger **10/7**; engaged 25.8–33.4k zone-hours vs base |
| 4 (+L4) | — ABSENT | `hydro_ror_split` R at G-SHARE (caiso-194) | DO-NOT-REDO; re-anchoring is a new charter, not opened |

**Lane-2 premise recheck at composition** (§4's one cross-lane arithmetic
obligation): satisfied by identity — the committed extract IS the
merit-guard-filtered extract (caiso-192), X_c = 0.2443/0.2916/0.3528 ≥ 4.9× W
on the frozen caiso-196 record, and G-EXTRACT proves the extract sha
(5f3e35c5…) identical in control and final rung: the base never moved under
the ladder (the Desert Star NV re-derive is deferred post-ladder by charter).

**A recording artifact, disclosed:** bundles solved after the lane-5 build
record `caiso_ps_plant_params: false` at default where pre-build bundles have
no key; absent ≡ false is the default-identity the cache-key registration
proves (pinned key unmoved, persisted-identity pins green). The rung probes
declare it explicitly; no mechanism rides on it.

## 2. Criteria flips — the §5 protocol NEVER FIRED

No criteria-panel pass→fail flip occurred at any lane or any rung. The two
pre-registered watches closed clean on the final rung:

* **C3b** (the campaign's named watch): 0.097 / 0.174 / 0.181 — PASS every
  year against 0.20 (control 0.077/0.155/0.176; lane 5 contributed the
  movement and never crossed).
* **C1-2023 CC_REGULAR** (the caiso-196 ACCEPT-WITH-FLIP row): the lane-2
  healing SURVIVES composition — control −4.44 TWh (FAIL) → lane-2 −3.94 →
  final rung **−4.13 TWh / −1.7 pp, IN BAND (PASS)**; C1 12/12, free 8/8.
  The two halves of one double-count, repaired in sequence: caiso-196 gave
  the class its measured overlay (removing the phantom dispatch), lane 2
  removed the statistical term that duplicated the same ≥5-day events.

## 3. The promotion (§6) — structural superiority, enumerated

1. **Fewer fitted scalars:** DOF ledger **11/8 → 10/7** — the
   `wefor_multiplier = 0.7` row (identification "residual", ERCOT-derived,
   lineage ≥52 solves) is RETIRED on the gatespec's sanctioned removed path;
   the caiso-188 import-tranche census row (n_scalars 6) carries byte-exact.
2. **Measured inputs replacing fitted:** the ERCOT-fitted ST_GAS base 0.21 is
   replaced by a document-and-table-cited GADS class EFORd derived from
   CAISO's own census; the fleet-average PS aggregate is replaced by six
   cited-physical parameterizations (PG&E/DWR/USBR sources committed as
   provenance corpora), zero MW added.
3. **Mechanisms genuinely engaged:** 40,230/42,844/40,816 price zone-hours
   moved vs control on the final rung (attestation G-ENGAGE, committed
   sidecars); every rung's delta measured non-inert.
4. **The criteria panel is strictly better where it is allowed to speak:**
   load-bearing FAILs 2 → 1 (C1 healed); C2/C3b/C4/C8 PASS; **C6 PASS —
   attestation generated AT the promotion** (`gen_caiso197_attestation.py`,
   every premise computed; the E10 discipline); C3c the single ledgered
   caveat with magnitudes RE-MEASURED on this bundle (caiso-189 §8.3: 2023
   0 h vs 47 h and 2024 0 h vs 35 h UNCHANGED; 2025 PASSES at 8 actual
   hours — no new slot spent).
5. **C3a, reported for transparency and deciding nothing (§0/§6):**
   +4.0/+12.1/+15.6 % vs the incumbent's +4.4/+11.7/+14.5 — 2023 improves,
   2024/25 worsen (lane 5's cited physics is anti-favorable and stays, rule
   14). The determination is **NOT-YET** with C3a the sole load-bearing FAIL.

**LOYO (rule 22 standing clause) — discharged by construction** for the one
verdict flip vs the incumbent (C1 FAIL→PASS): zero fitted parameters exist
anywhere in the composed delta — lane 2's value is the frozen caiso-187
record's arithmetic identity (X_c ≥ 4.9× W in every year singly), lane 3 is a
published 5-year class table × a static census, lane 5 is time-invariant
plant physics. No in-sample gain enters any identification; the mechanism is
identical whichever year is left out.

## 4. The campaign's exhaustion posture (the charter, honored)

The CLOSED lane inventory is fully adjudicated: lane 1 EMPTY (caiso-192),
lanes 2/3/5 ACCEPTED AND COMPOSED (this keeper), lane 4 R (caiso-194), lane 6
desk-refused (caiso-191 §4). **C3a-2025 still fails after the final rung**, so
per the charter the campaign output is exactly this: the ladder's structural
gains promoted on their merits, the C3a residual honestly declared — now
narrowed to its PRICE face alone — and **no improvised lane**. The two named
owner-funded objects remain the only routes on record: the walled hourly PS
water-state intake (caiso-141; owner ruling 4 declined the purchase) and the
8,800 MW declared residual (caiso-191 §4, no citable axis). An EXHAUSTION
MEMO is therefore NOT owed in place of promotion — the protocol's degenerate
case (zero survivors) did not occur; this FINDING's §4 is the exhaustion
record the charter requires for the surviving-residual case.

## 5. Standing duties discharged at promotion

Keeper shard re-authored (note/disposition/prior-keeper/site-retention);
sidecar `market_story` written; matrix shard re-stamped (keeper + gates;
`wefor_residual` O→K, `caiso_ps_plant_params` O→K, `wefor_statistical_stack`
evidence appended; re-stamp history block); §5.2 header + session block
re-stamped; `build_status --iso CAISO` rebuilt; `audit_keepers --iso CAISO`
**PASS 0/0**; `check_mechanism_matrix` clean (keeper stamps + §5.x headers
match). **Site retention (standing 2026-08-15 directive):** the lane is
pruned to the keeper alone — `2026-08-15-caiso-196-e1-elsegundo` (superseded
keeper), the bit-zero control, the three lane arms and the intermediate rung
are off the site (`prune_iso_runs.py --force-uncite`; dangling citations
deliberate; every determination and gate record retained in the FINDINGs and
git history). Calibration-log entry in `docs/calibration-log/caiso.md`.

## 6. Handoff — what the next session opens with

1. **The Desert Star extract re-derive** (the deferred half of this session's
   NV intake): re-derive `data/raw/campd-unit-outages-CAISO.csv` 2018–2026
   with the committed recipe on the now-CA+NV state list, citing the NV data
   landing (rule 23), then A/B on this keeper's recipe — the caiso-196
   pattern exactly (baseline byte-identity proof first; strictly-additive
   55077 rows expected; CC_REGULAR population → 100 % of roster; the lane-2
   premise can only strengthen).
2. The C3a price-face lane stays the owner's: the PS water-state intake
   decision and the 8,800 MW residual are unchanged owner objects.
3. C3c remains the accepted ledgered caveat (owner rulings 5/6 posture).
