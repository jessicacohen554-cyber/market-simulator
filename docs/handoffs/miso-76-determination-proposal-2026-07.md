# miso-76 — Determination-path proposal: ledger the irreducible scarcity tail (OWNER DECISION REQUIRED)

**Date:** 2026-07-19. **Lane:** post-miso-75 (next number miso-76). **Session
branch:** `claude/miso-backcast-calibration-76-k4i77f`. **Status: PROPOSAL —
nothing in this document is applied.** The keeper bundle, its attestation, the
registry, `keepers.json`, `status.js` and the dashboard are all UNCHANGED by
this session. Per the lane charter the exceptions-ledger conversion is
**owner-only**; this doc is the ask.

---

## 1. What is being proposed

Convert the MISO keeper's two remaining FAILs into **ledgered
`ACCEPTED MEASURED-INPUT LIMITATION` caveats** in
`results/calibration/miso75_manitoba_meritcap/calibration_attestation.json`,
moving the MISO determination **NOT-YET → CALIBRATED-WITH-CAVEATS** with **no
solve, no payload change, no bench change, no new mechanism, and no fabricated
scarcity** (rubric §3; scorer-only re-read per rubric §6).

Current keeper: `2026-07-18-miso-75-manitoba-meritcap` (owner-promoted
2026-07-19). Verdict at HEAD (rubric v2.7, re-confirmed this session):

- **PASS:** C1 16/16 (free 12/12), C2, C3b (0.082/0.137/0.198 — 2025 is 0.002
  under the 0.20 veto), C4, C5a, C6, C7, C8 (ST_GAS grounded-above-budget all
  three years). DOF 28/2, zero fitted scalars.
- **FAIL (both ledger-undocumented):**
  - **C3a-2025** mean LMP −15.4% (load-bearing, beyond the ±10% band).
  - **C3c** RT tail all three years: model 0/6/0 h vs RT actual 30/37/88 h
    (supporting; 0.00×/0.16×/0.00×).

Both fails are the **Phase-A irreducible scarcity tail** (miso-71/74 findings,
`docs/multi-iso/miso-scarcity-tail-diagnosis.md`, calibration-log 2026-07-17/18/19
entries). The lane's standing instruction: do NOT chase them with coal offers or
fabricated scarcity (rules 1/11/13).

### Dry-run verification (scorer-only, this session)

The four draft entries in §4 were applied to a temporary copy of the
attestation and scored with `scripts/calibration_verdict.py`; the attestation
was then restored **byte-identical** (sha256-verified, tree clean). Result:

```
CALIBRATION DETERMINATION: CALIBRATED-WITH-CAVEATS
[~] CAVEAT  LOAD  C3a mean LMP [ledgered]
[~] CAVEAT  SUPP  C3c price tail / scarcity (RT hourly) [ledgered]
determination basis:
  - 2 ledgered measured-input caveat(s): C3a mean LMP, C3c price tail / scarcity
```

Budget check: 2 ledgered non-protective criteria ≤ 3 (rubric §2); the two
dormant storage entries (ex-C5b/C5c, removed in v2.7) match no criterion and
stay inert history. All other criteria unchanged.

---

## 2. Why these two fails qualify as measured-input limitations (the evidence)

**C3c (RT tail 30/37/88 vs model 0/6/0).** The committed anatomy
(`docs/multi-iso/miso-scarcity-tail-diagnosis.md` §1, D6 Indiana-Hub hourly
actuals):

- **2023 — 30 h, ALL isolated single-hour transients** (30×1 h, ramp hours,
  26 days across all seasons). In those same hours the DA market — which has
  unit commitment, ramp modeling and a full network — priced a **median $40 and
  never crossed $200** (DA tail: 1 h). These are 5-minute-market events (ramp
  scarcity inside the hour, net-load forecast misses, RT re-dispatch) averaged
  up to an hourly bar.
- **2024 — 37 h (35×1 h + 1×2 h)**; the 24 h DA tail is Winter Storm Heather
  (Jan 14–17) and is **almost disjoint** from the RT set (1 shared hour).
  Heather is measured NOT-a-reserve-event (reserve MCPs ~$3 — miso-71 R3);
  the model's 6 h include the declared Aug-26-2024 Warning window, R2-clean.
- **2025 — 88 h**: 52×1 h transients plus the first genuine multi-hour blocks;
  the DA-visible (representation-reachable) bound is 38 h. The engagement
  adjudication (miso-71) is decisive: the measured Midwest reserve family HOLDS
  the measured requirement (1,862/1,941/2,253 MW) through the Jun/Jul deep
  windows with a **$0 dual**, because the measured cleared series itself
  **dips to 957/851 MW** in the tightest hours — the requirement series is a
  lower bound (leg-(b)); plus the sub-hourly Jul-28 40-min $3,100 transient.
- The scarcity machinery already in the keeper — `maxgen_emergency_tier_pricing`,
  the measured market-wide/South/Midwest cleared-reserve families, engagement
  scarcity — is **at its legitimate measured extent** (miso-56/70/71
  adjudications). The 2025 MISO SOM reports a system price-cost markup of
  **−1.07%** and publishes **no offer-distribution table**, so there is no
  measured basis to raise offers (rule 23). Every remaining candidate closes
  the count only by modeling forecast error / sub-hourly re-dispatch (outside
  this model's representation) or by a tuned mechanism that fails the rule-13
  admissibility test.

**C3a-2025 (−15.4%).** The Phase-A decomposition (miso-74 lane, derive-first):
**~78% of the miss is the out-of-representation scarcity-tail content** — the
broad load-weighted price level is correct (−$0.19) — and the SOM's −1.07%
markup refutes an offer-level cause. The move from −13.3% (miso-74) to −15.4%
is the **pre-registered rule-14 disclosed side effect** of the merit cap's
restored seam supply (charter B3), not a defect: the suppressed seam had been
masking part of the same tail residual. C3a-2023 (−2.5%) and C3a-2024 (−8.9%)
PASS — the level mechanism is right; only the tail-carrying year fails.

---

## 3. What the owner must explicitly rule on (the honest tensions)

This is not a rubber stamp. Three points require an explicit owner ruling,
which is why the lane forbids self-authorization:

1. **Rubric §3 lists "a collapsed price tail" among examples that are NEVER
   ledgerable.** MISO 2023/2025 are 0 h — literally collapsed. The
   counter-reading: that example targets a tail collapsed by a *model defect*
   (offer curves too aggressive, missing scarcity mechanism), whereas MISO's is
   a *documented representation bound* — the mechanisms exist, are measured, and
   are adjudicated at their legitimate extent; the missing hours are
   sub-hourly/forecast-error formations with no admissible hourly-LP analogue.
   Precedent cuts both ways (see §3a). If the owner authorizes, the ruling
   should be recorded (in the ledger entries themselves and the calibration
   log) as a deliberate owner interpretation of §3, so it cannot be cited later
   as a loophole.
2. **Rubric v2.7 consciously superseded the sub-hourly-transient argument for
   *gating*** ("transients that push an hourly RT average over the threshold
   are part of realized scarcity and now gate"). The proposal does NOT re-open
   the gate — C3c still gates and still reads FAIL-magnitude — it asks whether
   the same argument is acceptable as a *ledger reason*. Those are different
   questions (the gate defines the judged quantity; the ledger classifies whose
   limitation the miss is), but the owner should accept the argument's return
   through the ledger door knowingly.
3. **C3a is load-bearing.** Ledgering a load-bearing price year means the
   certification "intended-use delivery at or above commercial grade" carries a
   −15.4% 2025 mean-price caveat on its face. The mitigations: 2023/2024 pass
   clean, ~78% of the 2025 miss is decomposed to the same tail limitation, and
   the caveat is listed, never hidden. Downstream: CALIBRATED-WITH-CAVEATS
   makes MISO eligible to seed the forecast-error prior
   (`docs/forecast-validation-plan.md` Phase 3) — the owner should be
   comfortable with that eligibility carrying this caveat.

### 3a. Precedent

- **NYISO-62 (current keeper, CALIBRATED-WITH-CAVEATS)** — the direct template:
  ledgered `price_mean` (2024/2025, −12.8/−13.7%), `price_shape` (2024) and
  `price_tail` (2023/2024/2025, incl. the v2.7 RT-basis 2024 0.25× fail),
  each grounded in a documented data-blocked/lower-bound measured input (B1
  reserve increment, Iroquois Z2). Exactly 3 ledgered criteria — at budget.
- **NEISO-59 (current keeper)** — ledgered `price_tail` all three years with
  RT hour-set anatomy reasons (14/15, 8/8, 14/20 hours RT-only formations).
- **ERCOT-82 (current keeper, NOT-YET)** — the deliberate counter-example: its
  collapsed tail is ledgered for 2023 only, and the entry itself says "Until
  then ERCOT is NOT-YET", because ERCOT's tail miss is a *re-calibration gap*
  (offer/scarcity curves fitted against a phantom-tightened fleet), i.e. a
  model defect with a named successor lane. MISO differs on exactly that
  point: its scarcity mechanisms are measured, adjudicated at full legitimate
  extent, and the residual has **no named admissible successor lane** — that
  is what "frontier/irreducible" means here.

If authorized, MISO would be the third ISO on the ledgered-tail path (after
NYISO/NEISO), not the first, and the first to pair it with a ledgered
load-bearing C3a year (NYISO already ledgers two C3a years).

---

## 4. The draft ledger entries (exact, ready to apply on authorization)

Append these four entries to `exceptions` in
`results/calibration/miso75_manitoba_meritcap/calibration_attestation.json`,
replacing `<OWNER-AUTH>` with the authorizing session/date reference:

```json
[
  {
    "criterion": "price_mean",
    "year": 2025,
    "metric": "C3a system load-weighted mean LMP (RT lw basis)",
    "magnitude": "-15.4% (2023 -2.5% PASS, 2024 -8.9% PASS)",
    "classification": "ACCEPTED MEASURED-INPUT LIMITATION (out-of-representation scarcity-tail content)",
    "reason": "Phase-A decomposition (miso-74 lane, derive-first, no LP): ~78% of the 2025 miss is the out-of-representation RT scarcity tail (C3c below) -- the broad load-weighted price level is correct (-$0.19) and the 2025 MISO SOM reports a system price-cost markup of -1.07% with NO offer-distribution table, so there is no measured basis to raise offers (rule 23). The -13.3 -> -15.4% move at miso-75 is the pre-registered rule-14 disclosed side effect of the merit cap's restored seam supply (charter B3), not a defect. maxgen_emergency_tier_pricing + the measured market-wide/South/Midwest cleared-reserve families are at their legitimate measured extent (miso-56/70/71 adjudications). Never chased with a tuned adder/haircut (C6). Owner-authorized FAIL->CAVEAT conversion: <OWNER-AUTH>. Evidence: docs/multi-iso/miso-scarcity-tail-diagnosis.md; calibration-log 2026-07-17 (miso-71), 2026-07-18 (miso-74 Phase-A), 2026-07-19 (miso-75)."
  },
  {
    "criterion": "price_tail",
    "year": 2023,
    "metric": "C3c RT hourly tail hours >$200 (Indiana Hub)",
    "magnitude": "model 0h vs RT actual 30h (0.00x); DA diagnostic 0h vs 1h",
    "classification": "ACCEPTED MEASURED-INPUT LIMITATION (sub-hourly RT-only formation, out of hourly-LP representation)",
    "reason": "The entire 2023 RT tail is 30x1h isolated single-hour transients at morning/evening ramp hours across 26 days; in those same hours the DA market (with commitment, ramp and a full network) priced a median of $40 and never crossed $200 (DA tail: 1h). These are 5-minute-market formations (intra-hour ramp scarcity, net-load forecast misses, RT re-dispatch) averaged up to an hourly bar -- a deterministic realized-weather hourly LP has no admissible mechanism for them, and one tuned to hit the count would fail rule-13. The keeper's scarcity machinery is at its legitimate measured extent (miso-56/70/71). Rubric-3 note: the owner rules this a documented representation bound, NOT the never-ledgerable model-defect collapsed-tail case (mechanisms measured and adjudicated; no admissible successor lane). Owner-authorized: <OWNER-AUTH>. Evidence: docs/multi-iso/miso-scarcity-tail-diagnosis.md section 1."
  },
  {
    "criterion": "price_tail",
    "year": 2024,
    "metric": "C3c RT hourly tail hours >$200 (Indiana Hub)",
    "magnitude": "model 6h vs RT actual 37h (0.16x); DA diagnostic 6h vs 24h",
    "classification": "ACCEPTED MEASURED-INPUT LIMITATION (sub-hourly RT-only formation, out of hourly-LP representation)",
    "reason": "35 of 37 actual RT hours are isolated 1h transients (plus one 2h run); the 24h DA tail is Winter Storm Heather (Jan 14-17) and is almost disjoint from the RT set (1 shared hour) -- Heather is measured NOT-a-reserve-event (reserve MCPs ~$3; miso-71 R3), so the winter DA tail is a commitment-conservatism premium, not deliverable-reserve scarcity. The model's 6h include the declared Aug-26-2024 Maxgen/Warning window (R2-clean engagement, all inside the declared window). Same representation bound and rubric-3 ruling as 2023. Owner-authorized: <OWNER-AUTH>. Evidence: docs/multi-iso/miso-scarcity-tail-diagnosis.md section 1; calibration-log 2026-07-17 (miso-71 R2/R3)."
  },
  {
    "criterion": "price_tail",
    "year": 2025,
    "metric": "C3c RT hourly tail hours >$200 (Indiana Hub)",
    "magnitude": "model 0h vs RT actual 88h (0.00x); DA diagnostic 0h vs 38h",
    "classification": "ACCEPTED MEASURED-INPUT LIMITATION (leg-(b) measured-requirement lower bound + sub-hourly formation)",
    "reason": "52 of 88 actual RT hours are isolated 1h transients; the DA-visible (representation-reachable) bound is 38h. The miso-71 engagement adjudication is decisive: the measured Midwest reserve family HOLDS the measured cleared requirement (1,862/1,941/2,253 MW) through the Jun/Jul deep windows with a $0 dual because the measured cleared series itself DIPS to 957/851 MW in the tightest hours -- the requirement series is a lower bound (leg-(b)), and undoing the dip would be residual-fitting (rules 1/13; the NYISO B1 ledgered-lower-bound precedent). Plus the sub-hourly Jul-28 40-min $3,100 transient. The 2025 SOM markup of -1.07% with no offer-distribution table leaves no measured offer basis. Same rubric-3 ruling as 2023. Owner-authorized: <OWNER-AUTH>. Evidence: calibration-log 2026-07-17 (miso-71 decisive read); docs/multi-iso/miso-scarcity-tail-diagnosis.md sections 1-2."
  }
]
```

---

## 5. Execution checklist on authorization (miso-76 — scorer-only, NO solve)

1. Append the §4 entries (with the real `<OWNER-AUTH>` stamp) to the keeper
   attestation; add a one-line `governance.note` addendum naming the conversion.
2. `python scripts/calibration_verdict.py results/calibration/miso75_manitoba_meritcap`
   — confirm CALIBRATED-WITH-CAVEATS, 2 ledgered caveats, budget 2/3.
3. `calibration_verdict --write-metrics` to refresh the bundle `metrics.json`
   (`determination` field), then `python scripts/build_status.py` to refresh
   the committed `frontend/data/backcast/status.js` (the Calibration Status
   page).
4. `python scripts/build_manifest.py` + `scripts/check_registry_payload_parity.py`
   (no sidecar/payload change expected — parity must still PASS).
5. Consider the **MISO frontier declaration** in `keepers.json` (the
   NEISO/NYISO template): every named admissible scarcity mechanism tried on
   record, remaining residual out of representation, further C3c work needs a
   NEW measured identification. Optional but symmetrical.
6. Calibration-log entry (miso-76) recording the owner ruling verbatim,
   including the §3 rubric-interpretation point; note in
   `docs/calibration-determination-rubric.md` §9 only if the owner wants the
   ruling codified as an amendment.
7. Push per rule 27 (small commit; fetch-back SHA-compare; no source file
   ≥300 lines involved). Registry stays at 14 — no new run is registered
   (attestation edit only, rubric §6 re-scores in place).

## 6. If the owner declines (the alternatives, unchanged from the lane state)

- **(B) North/Central zonal price-separation topology split** — structural,
  Phase-A derive-first charter required before any build; does not touch the
  irreducible tail.
- **PJM twin of the uniform-derate defect** (port `miso_seam_envelope_merit_cap`
  semantics to `inject_pjm_seam_flow_limit`) — high-value, separate lane, moves
  the PJM keeper.
- **all-ISO `gas_daily_shape_factors` interp-mislocation fix** (miso-72 design
  §3.7; July-2025 ~−$3.3) — correctness bug, separate lane.

Declining C and picking a lane still leaves MISO NOT-YET on the same two fails,
by construction — neither alternative touches them.
