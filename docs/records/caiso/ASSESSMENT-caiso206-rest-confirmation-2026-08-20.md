# ASSESSMENT — caiso-206: post-caiso-205 REST CONFIRMED. The CAISO record re-verified clean on committed bytes (no solve, no probe, no LP), keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET), and the ONE live decision restated as an owner packet — FUND a tail-formation object, or rest continues (2026-08-20)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due** (rule 15 applies to completed runs — the caiso-134/140/150/202
disposition). The lane is rested by owner ruling (caiso-201 Q1) and no owner
order to fund arrived in this session, so the charter's **default branch —
REST CONTINUES — is what executed**. Everything below is re-measured from
already-committed artifacts.

## §A — Verification pass, item by item

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `frontend/data/backcast/keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged since 2026-08-17** |
| 2 | determination | `scripts/calibration_verdict.py --run-id <keeper>` (committed artifacts only, never a solve) | **NOT-YET** — reproduced exactly |
| 3 | keeper text truthfulness | `scripts/audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** (keeper, holdout, marker, status all clean) |
| 4 | dashboard status sync | `scripts/build_status.py --iso CAISO --check` | **"status parts in sync (1 keepers: CAISO)"** |
| 5 | caiso-205 registration | registry sidecars + run payloads | both present and committed: `2026-08-19-caiso205-ctl-headbase` / `-arm-adaptive`, years `[2023, 2024, 2025]` each |
| 6 | DOF ledger | `calibration_attestation.json` on all three bundles | keeper **10/7**, control **10/7**, arm **11/7** — the 11th entry lives ONLY on the registered arm, exactly as the guardrail requires |
| 7 | holdout posture | `calibration-complete.json`, `holdout-freeze.json` | CAISO absent from **both** `complete` and `final`; **freeze ACTIVE**; no out-of-training year touched anywhere in the lane |
| 8 | mechanism matrix | CAISO shard + `docs/mechanism-testing-matrix.md` §5.2 | `ercot_storage_adaptive_expectation` **I** carrying the caiso-205 full-magnitude stamp; §5.2 caiso-205 block present. **No cell verdict moves this session — nothing was tested** |

**The re-verified scorecard (item 2), in full:** C1 fuel-mix PASS (12/12, free
8/8) · C2 system volume PASS · **C3a mean LMP FAIL — the SOLE load-bearing
failure** (2023 passes; 2024 **+12.8 %**, 2025 **+15.7 %** vs actual RT LMP) ·
C3b price duration/shape PASS · **C3c the SINGLE ledgered caveat** (2023 model
0 h vs RT actual 47 h; 2024 1 h vs 35 h; 2025 PASS) · C4 PASS · C6 governance
PASS · C8 forced-energy PASS. Determination basis: *undocumented
out-of-tolerance (FAIL) criteria: price_mean*. This is the charter's standing
description confirmed to the digit.

## §B — Standing state a future CAISO session inherits (do not re-litigate)

- **Binding rulings.** C3a is judged against **actual RT LMP only** — the basis
  question is CLOSED (caiso-203 ruling 1, re-affirming ruling 5); model-vs-DA is
  context, never skill. **No funded data intakes** (caiso-203 ruling 2, FINAL):
  the PS water-state intake stays declined, the import spot capacities stay a
  declared residual. Rest is the default (caiso-201 Q1). The proposed caiso-204
  owner sitting is superseded — do not convene it.
- **The in-model lever queue is EXHAUSTED**, and caiso-205 re-confirmed it at
  full magnitude rather than by argument: the last chartered lever was built,
  A/B'd against a zero-delta control, passed every pre-registered gate, and
  measured **byte-identical in 2023/2025 / near-inert in 2024** (floor max
  $14.5). An inert arm is not a lever.
- **DO-NOT-REDO, consolidated and carried forward.** Do not re-run the caiso-205
  A/B (the registered pair IS the full-magnitude record); do not re-run the
  caiso-204 identification; do not re-measure the caiso-202 level-vs-basis
  table, bucket decomposition, marginal-rung attribution or CC-interior witness;
  do not re-attribute the overrun to biomass, coal or the import price ladder;
  do not re-test the caiso-202 §F killed levers (per-year band multipliers,
  per-year margin anchor, static-priced conduct sweep, the wedge instruments).
  **New evidence means one thing only: a keeper whose own scored path spikes.**

## §C — The ONE live decision (owner act; nothing here is executable by a session)

Only a **funded tail-formation object** can move the C3a/C3c compression — they
are two faces of one behaviour (caiso-202 §B: the model overprices every
sub-$60 bucket by +$6–15/h in all three years and underprices the >$60 tail in
all three; C3a's year pattern is just how many tail hours exist to cancel
with). The two candidates, with their **measured** bounds stated against
interest:

| object | status | measured reach |
|---|---|---|
| **(a) PS water-state hourly intake** | declined **3×** (caiso-141 / ruling 4 / caiso-201 Q2(a)) | covers **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move **at its most favourable bound** (caiso-186 sitting) |
| **(b) import spot-capacity derivation** | not funded (caiso-191 §4 / caiso-201 Q2(b)) | direct λ share **< 5 %** of the positive gap (caiso-202 §C) |

**Neither closes C3a on its own arithmetic**, and that is the honest packet: the
move C3a needs is a broad **~$2–3/h** level-down across the sub-$60 buckets
(caiso-202 §B), and no admissible in-model instrument of that size exists
(§F) — the mid-band clearing level is already set by CAISO's own measured DAM
bid stack. Funding (a) is the larger of the two by a wide margin and is the only
object with a plausible path to the 2024 half of the miss; (b) is bounded small
by its own measurement. **Reaching the number through any §F-killed lever would
be a rule-13 act**, which is why NOT-YET is the honest fallback (ruling 5).

**If no funding order issues, the correct state is the current one: rest.**

## §D — Filed items carried forward (each fixed at the NEXT promotion, whichever branch produces one; none is fixable without one)

1. **Stale DOF-ledger text** — the `offer_curve_by_group` row's
   "identification: residual" overstates the residual content for CAISO's
   CC_REGULAR / CT_PEAKER bands, measured from OASIS `PUB_DAM_GRP` since
   2026-08-02 (caiso-202 §H). Correct at the next promotion's attestation.
   *(Verified still stale on the keeper bundle this session.)*
2. **Diagnostics vintage drift** — the keeper-vintage
   `legitimacy_diagnostics.json` differs from fresh bundles on one D-4 row
   (chp_steam plant 10034), a diagnostics-code evolution since 2026-08-17,
   identical in the caiso-205 control and arm (caiso-205 §C.3). Regenerate the
   keeper's diagnostics at HEAD at the next promotion rather than discovering it
   there.
3. **Site retention** — the caiso-205 pair postdates the keeper, and every prior
   sweep under the standing 2026-08-15 owner directive executed **at a
   promotion**. The pair therefore **stays on the site** until the next CAISO
   promotion, at which point the directive prunes it as prior-to-keeper in the
   ordinary way. No action now; flagged so the next promoting session does not
   treat it as an anomaly.
4. **Session mechanics** (caiso-205 §D, unchanged and still binding on this
   container class): regenerate `data/clean` partitions before any solve — a
   fresh container starts empty and the strict input-completeness guard is
   wired; and run **ONE** CAISO 3-year invocation at a time (~13.3 GiB cgroup
   cap — concurrent invocations OOM, rule 12's parallel default is subordinate
   to the box).

## §E — Record changes

- This file; `docs/calibration-log/caiso.md` caiso-206 entry; matrix §5.2
  caiso-206 block.
- **Keeper, markers, holdout freeze, every matrix cell verdict: UNCHANGED.** No
  run registered (none produced). No CAISO shard cell edited — rule 28b attaches
  to sessions that test a mechanism, and this one tested none.

Next number: caiso-207.
