# FINDING — ercot-221 (THE ADAPTIVE-EXPECTATION STORAGE OFFER, Phase-1 A/B, owner-instructed): the mechanism is BUILT, LIVE, and BEHAVES EXACTLY AS DESIGNED — the 2023/24/25 split SELF-GENERATES from the model's own price path (7/3/0 spike days; 2025 byte-identical to control, the self-extinction property working) and 2023 moves toward actual on every measure — but the single-pass bootstrap recovers only a SLIVER of the depth object (C3a-2023 −30.4 → −29.8 %, tail 67 → 71 of 181), and the mechanical verdict is **REJECTED-AS-ARMED on G-SHED alone**: one NEW 17.9 MW load-shed hour (2024 h3066, a REAL storm hour — actual RT $2,451; the control already priced it $4,925). Every other gate PASSES. The promotion question goes to the owner's standing structural standard, with the session's recommendation recorded in §6.

**Session ercot-220/221, 2026-08-18/19, branch
`claude/ercot-220-lever-phase0-je3znm`.** Keeper resolved fresh at session
start: `2026-08-17-ercot215-arm-decontam` (NOT-YET, {C3a-2023 −40.1 %,
C3b-2023 0.736}, C3c ledgered CAVEAT ×3). Owner card: the direct dispatch
recorded verbatim in `docs/PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md`
§0 ("Ok yes let's do this"; "I want you to do the adaptive battery fix for
sure"), with the precommit + Amendments 1–4 pushed and blob-verified before
every corresponding step. RETENTION HOLD honoured. A parallel owner-side
session (PR #4116) contributed the pair's attestation generator and the
G-DOF ledger entry; both are used here.

## 0. THE RECORD, IN ORDER (every step pushed before the next)

1. **Phase-0 identification, v1 and v2 — both FAILED as pre-registered,
   recorded unrewritten** (`ercot221_adaptive_phase0.json`). v2 (the
   two-constant family: trailing-EWMA half-life + gain) passes the monthly
   level reconstruction (Jul/Aug/Sep/Oct in ±35 %), G-BOOT and the
   ablation leg, and identifies **half-life 30 d, β 3.0077** on the
   measured 2023 daily evening storage offer surface — the response is a
   textbook experience-follower ($175 → $761 → $4,700 → $5,000 → $1,852 →
   $300 Jun–Dec against spike-day counts 1/2/16/4/0/0/0) — but misses the
   daily-correlation bar (0.447 vs 0.6; the daily surface is a cap-or-cheap
   switching series), the fall-decay speed (the Oct→Nov cliff needs a
   seasonal end-of-season term one memory constant cannot carry), and
   G-SAFE-2024 by 0.0011. Also recorded: Jan–Feb 2023 evening asks parked
   at $5,000 — post-Uri winter memory, cross-year adaptive conduct outside
   this family's per-year window.
2. **Phase-1 ENTERED ON OWNER INSTRUCTION over the recorded screen-fail**
   (the ercot-188/213/215 pattern; Amendment 2), with the §4 direction-blind
   A/B kill table unchanged as the mechanical protection.
3. **The purity correction, caught live (Amendments 3–4).** On the owner's
   direct question ("You're not letting it see actual 2023 price right?"),
   the event basis was first tightened to bare model λ (Amendment 3) — and
   the first armed launch then read **0 spike days** (P_hat ≡ 0): the
   model's deep-scarcity expression lives in its OWN co-optimization
   scarcity adder, not its energy dual (λ tops out ~$700; its one $5,000
   hour is λ $299 + model adder $4,701). That arm was STOPPED and
   DISCARDED as a diagnostic. Amendment 4 restated the basis precisely:
   **λ + the model's own decontaminated anchored scarcity-adder mirror** —
   both duals of the model's own pass-1 LP, zero measured content —
   verified to reproduce the expected 7/3/0 spike days on the keeper's own
   committed path before relaunch.
4. **Control replay: G-REPRO strongest form** — `ercot221_control_A`
   reproduces the ercot-215 keeper **12/12 hourly sidecars byte-identical**.
5. **The armed member** (`ercot221_adaptive_B`): built on the existing
   ercot-219 stage-3 seam, two-pass P1 (one adaptation pass), floor
   `max(vom, P_hat × VOLL)` in h17–20 CST only.

## 1. THE MECHANISM'S OWN SIGNATURE — the split self-generates (nothing is keyed)

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| pass-1 model spike days (own path, λ + own adder ≥ $1,000) | **7** | 3 | **0** |
| P_hat max | 0.370 | 0.176 | 0.000 |
| evening window hours with floor > vom | 776 / 1,460 | 568 / 1,460 | **0** |
| hours with floor ≥ $1,000 | 160 | 0 | 0 |
| floor max | $1,850 | $878 | $0 |

2025's pass 2 is **identical to its control** — the self-extinction property
demonstrated in the solve itself, not asserted. No year key, no measured
price, no regime parameter (ercot-217 stays closed): the 2023-heavy pattern
is the model's own storm calendar amplified by the identified memory rule.

## 2. THE GATE TABLE (PRECOMMIT-ercot221 §4, direction-blind)

| gate | result | verdict |
|---|---|---|
| G-CAP | 0 violations in 26,280 h | **PASS** |
| G-SPUR | 9→11 (+2, bar +5) / 11→10 (improves) / 1→1 | **PASS** |
| **G-SHED** | 2023 0→0; **2024 {3067} → {3066, 3067}** — ONE new hour, **17.9 MW**, at a REAL extreme hour (actual RT $2,451, the Jan-2024 storm; control already priced it $4,925 with 600 MW shed at the adjacent h3067 in BOTH members); 2025 0→0 | **FAIL** |
| G-BAT | 2024 ratio 0.886, 2025 1.076 (±25 % band) | **PASS** |
| G-DOF | ledger delta = exactly {`ercot_adaptive_half_life_days`, `ercot_adaptive_beta`}, measured-conduct identification cited; **n_residual 6 → 6** | **PASS** |
| G-D2 | no new D-4 rows; the `ercot_storage_adaptive_expectation` attribution row present with its declared window | **PASS** |
| G-REPRO | control = keeper, 12/12 sidecars byte-identical | **PASS** |
| LOYO | 2023-conduct-measured constants (ercot-168/192 precedent); G-SAFE declared in its place ex ante — realized in-solve as the 2025 no-op | declared |

**Mechanical verdict: REJECTED-AS-ARMED on G-SHED** — recorded unrewritten;
promotion over it is the owner's separate act (§6).

## 3. SIDE-EFFECT REPORTING AT FULL MAGNITUDE (Q-B FINAL / R-A — never a basis, never a gate)

Probe basis (demand-weighted P1 settled vs actual hub RT):

| year | C3a control → arm | NRMSE control → arm | model tail > $200 (actual) |
|---|---|---|---|
| 2023 | −30.4 % → **−29.8 %** | 3.452 → 3.422 | 67 → **71** (181) |
| 2024 | +7.9 % → +8.6 % | 2.344 → 2.357 | 22 → 22 (53) |
| 2025 | +0.5 % → +0.5 % | 0.939 → 0.939 | 1 → 1 (31) |

2023 moves toward actual on all three measures, un-targeted; the magnitude
is the honest price of purity, quantified ex ante (precommit §4 bound): the
model's own path carries 7 spike days against reality's 23, so the
bootstrapped expectation reaches $1,850 floors against reality's
$3,400–5,000 asks, and one adaptation pass recovers ~0.6 pp of the ~24-pp
depth ceiling (RESEARCH-ercot220b §1). 2024's +0.7 pp stays well inside its
official band.

## 4. WHAT THE RESULT ESTABLISHES (and what it does not)

**Established:** the adaptive-expectation architecture is admissible,
buildable, live, correctly signed, self-extinguishing, and moves the 2023
object in the right direction with zero measured content — the first
representation of the adjudicated conduct channel ever to survive its own
cross-year falsifiers. The binding limitation is now measured precisely:
**the bootstrap is starved, not wrong** — the model's own tail (7 spike
days) is ~30 % of reality's event experience, so a single pass cannot reach
reality's offer levels.

**Not established / left standing:** the missed-hour count half (117 hours)
stays with FINDING-ercot220's closure (B-2 unsigned, Door D the floor). The
named successor knobs — a second adaptation pass (fixed-point iteration),
the cross-year memory (the measured Jan–Feb-2023 post-Uri cap-parking), a
seasonal end-of-season term — each carry real DOF and need their own
identification; none is built here.

## 5. GOVERNANCE

Rules 5/23/24: three registered `ScenarioConfig` fields, cache-key
registrations landed with the fields (pinned default key `603c2498bf71d21d`
unmoved; `test_persisted_identity` 13/13); conventions as cited constants in
`results/scarcity.py`; no env-var knob, nothing residual-derived. Rule 19:
mutual exclusion with `ercot_storage_reservation_offer` enforced (loud
ValueError). Rule 22: {2023, 2024, 2025} only, no marker sought. Rule 25:
ERCOT-gated (`iso == "ERCOT"`); every other ISO's shard cell `·`. Rule 27:
edits local, exact bytes pushed, ≥300-line files blob-verified on every
push. Rule 28: family row + cell lines in all six shards landed in the build
commit (28c, `check_mechanism_matrix.py` exit 0); the ERCOT cell verdict
stamped this session (28b). Rule 15/16: both members registered with
payloads, all three years in one bundle per member, same session. DO-NOT-REDO
honoured: Door A static conduct functions not re-tested (this is the dynamic
family their post-mortems named); `ercot_storage_rt_offer_surface` (R) not
re-opened (no measured surface fed — the armed path reads only model duals);
the ercot-219 aggregate reconciliation (R), item 11 (Q-B), the mid-band and
regime lanes all untouched. C6: attestations for both members name the
Phase-0 record and the owner instruction (the #4116 generator). No new
workflows, no cron, no PR (push-and-stop on the designated branch).

## 6. THE PROMOTION QUESTION (the owner's standing standard, applied)

The owner's standard, given in advance this session: *"Is this a recommended
keeper candidate? If so plz promote. If structural integrity improves but
gates regress that may still be a keeper."*

**The session's recommendation: PROMOTE.** Grounds: (a) structural integrity
improves unambiguously — a real, admissibly-identified market behaviour
(rule 1) representing the channel every prior route to the 2023 object
closed on, with the split self-generating and the self-extinction property
demonstrated in-solve; (b) the sole gate regression is a 17.9 MW × 1 h
intensification of an already-extreme REAL event hour (actual $2,451), not a
phantom event — qualitatively unlike the fabricated-shed failures that
killed ercot-159/219; (c) every protective gate that has historically caught
illegitimate mechanisms (G-SPUR, G-CAP, G-BAT, G-DOF, G-D2) passes; (d) the
scored object (2023) improves on every measure. The counterweight — the
small magnitude of the gain — is a reason to keep working the successor
knobs (§4), not to leave the first admissible conduct representation
disarmed. Promotion executed in-session on this recommendation under the
standing authorization; the mechanical REJECTED-AS-ARMED verdict stands
recorded unrewritten beside it (the ercot-188/213/215 pattern, fourth
application).

**Session consumed the ercot-221 shorthand. Next shorthand: ercot-222**
(ercot-199 remains unclaimed).
