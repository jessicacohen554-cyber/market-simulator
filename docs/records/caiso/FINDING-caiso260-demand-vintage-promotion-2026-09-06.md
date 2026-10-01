# FINDING — caiso-260: the demand-artifact vintage re-derive is **PROMOTED TO KEEPER**, `2026-09-06-caiso-260-b1-demand`, **DETERMINATION CALIBRATED**, zero parameters, DOF unchanged. **The one gate movement, first: C3c-2023 goes PASS → CAVEAT at 23 h vs 47 (0.49×), where the keeper passed at 24 h (0.51×) — one hour across the 0.5× line on a supporting-tier criterion, auto-ledgered under the standing rule, determination unchanged.** Every load-bearing criterion holds; C3b improves in every year; C4-2025 moves off its zero-margin bound (0.300 → 0.298) in the direction the pre-solve statistic predicted; the demand identity holds to the MW in every hour of every year.

**Session caiso-260, 2026-09-06.** Branch
`claude/caiso-258-backcast-calibration-b1nal9`. Keeper
**`2026-09-06-caiso-257-b1-ctonly` → `2026-09-06-caiso-260-b1-demand`**
(bundle `caiso260_demand_vintage`). Pre-registration
`PRECOMMIT-caiso260-demand-vintage-rederive-2026-09-06.md` +
`ADDENDUM-caiso260-phase0-2026-09-06.md`, both pushed before any LP. Rule
22 `[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze
ACTIVE. **Two LP-years-equivalent spent**: one 2023 screen (bundle deleted,
rule 29(c)) and the three-year keeper bundle in ONE invocation (rule 16).

---

## §1 — THE OBJECT AND THE ARM

`ASSESSMENT-caiso259 §8`: the keeper's demand input — the caiso-80 Option A
supply-consistent series — had been derived on a bench whose CEMS anchors
read **60.344 / 53.428 TWh** (2023/24) with a flat cogen block of 8.399 TWh,
while the bench parts C1/C4 score against carry **62.209 / 54.588 / 44.429**
and cogen 6.604 / 6.416 / 6.416 — the plant map the caiso-196 (El Segundo),
caiso-199 (Desert Star) and caiso-200 (member panel) landings widened after
the artifact's 2026-07-13 vintage. The keeper's demand basis and its scoring
basis no longer shared a coverage vintage, which is precisely the defect
caiso-80 Option A exists to remove.

**The arm is the committed producer run unchanged on the current bench.** No
threshold, window or field moves; the derive's own guards pass untouched;
the DOF ledger is byte-for-byte 9 entries / 6 residual; no
`authorized_price_tuning` block. Admissibility: rule 14 (the more faithful
input by construction), rule 23 (re-derived because the *source data*
updated — the three bench refreshes — never because a residual moved), rule
13 (every term a measured input).

## §2 — G-REPRO AND PHASE 0 (ADDENDUM §1–§2, unchanged)

R-1/R-2/R-3 all PASS: max |Δdemand| **1,451.7 / 862.8 / 583.3 MW**, annual
**+69.4 / −33.0 / −752.7 GWh**, only `cems_gas_grid_mw` moved, flat term
−204.9 / −136.2 / −136.2 MW. The hourly delta **is El Segundo + Desert Star
to the MW** in 2024/25 (least squares 1.000 / 1.000, R² 0.99998), with a
6.8 % variance remainder in 2023. Shape: 2023/24 demand moves from the belly
(−83 / −65 MW) to the evening and night (+127 / +56; hod 22–23 +86 / +60);
2025 down in every hour (hod 22–23 −64). C4-2025 pre-solve statistic
`S < 0` in every year (bound ≤ 1.75 % of MSE). **Screen year 2023 by the
gross footprint** (1,976 / 1,310 / 1,093 GWh) — P-2's expectation of 2025
falsified; the rule governed.

**G-DRIFT `c78f6d94 → HEAD` by measurement: every LP input bit-identical in
all three years** with the artifact committed; three constants changed and
one added, each settled empirically. **G-CTRL form 4; no control solve.**
The identity probe was re-pointed from the pruned caiso-252 bundle to
`caiso257_ctonly` (a path edit only).

## §3 — THE SCREEN (2023): every STOP gate passes

Preconditions PASS (`mic_partition` 16,055 MW; hydro partition present, flag
off; outage/tranche sha256 identical; **"P1 route: COLD REBUILD"**). G-IDENT
**0.000 MW** (arm − keeper demand +69.4 GWh, exactly the artifact delta);
G-FOOT nuclear / wind / solar 0.000 / 0.000 / 0.08 %; no C1 flip; C3b 0.083
(keeper 0.088). Reported only: C4 0.882 / 0.286 (keeper 0.879 / 0.287), C3a
+4.38 % (keeper +4.49 %). Screen bundle deleted before merge; its numbers are
in `_caiso260_screen2023.json`.

## §4 — THE FULL SPAN, SCORED (the arm re-scored at HEAD, rubric v3.6)

| criterion | tier | keeper (caiso-257) | arm (caiso-260) | verdict |
|---|---|---|---|---|
| C1 fuel-mix | LOAD | 12/12, free 8/8 | **12/12, free 8/8** | PASS→PASS |
| C2 system volume | LOAD | PASS | **PASS** | — |
| C3a mean LMP ($/MWh, model vs actual) | LOAD | 56.60 / 37.73 / 37.42 (+4.49 / +8.89 / +8.72 %) | **56.54 / 37.73 / 37.26 (+4.37 / +8.89 / +8.25 %)** | PASS→PASS, **EXCLUDED** |
| C3b shape NRMSE | LOAD | 0.088 / 0.147 / 0.115 | **0.083 / 0.142 / 0.111** | PASS→PASS |
| **C3c price tail (h > $200, model vs RT actual)** | SUPP | 24 / 0 / 0 vs 47 / 35 / 8 → PASS / CAVEAT / PASS | **23 / 0 / 0** → **CAVEAT / CAVEAT / PASS** | **2023 PASS→CAVEAT (§5)** |
| C4 gas r / NRMSE | SUPP | 0.879/0.287, 0.908/0.263, **0.875/0.300** | **0.881/0.287, 0.912/0.260, 0.877/0.298** | PASS→PASS, excluded |
| C6 governance | PROT | PASS | **PASS** (attested at promotion) | — |
| C8 forced share | PROT | PASS | **PASS** | — |

**Determination CALIBRATED**: 8 scored, target grade 7, 0 fails, 1 ledgered
caveat (the scorer counts the criterion, not the year). **G-IDENT holds in
every hour of every year** (max |arm − artifact| 0.000 MW; arm − keeper
demand +69.4 / −33.0 / −752.7 GWh, exactly the artifact delta).

**Dispatch response, arm − keeper (TWh).** 2023: CT_PEAKER +0.173, import
−0.119, ST_GAS +0.037, solar −0.031, CC_REGULAR +0.031 — the evening/night
demand the re-derive adds is served by CT and CC, the belly it removes by
less import and a little curtailment. 2024: CT_PEAKER +0.087, solar −0.051,
import −0.041. 2025: CC_REGULAR **−0.452**, import −0.240 — the −0.75 TWh of
demand comes off CC first, which is the direction the C4 cell wanted.
Nuclear / wind untouched in every year.

## §5 — THE ONE GATE MOVEMENT: C3c-2023 PASS → CAVEAT

The keeper cleared the 2023 tail at **24 h vs 47 (0.51×)**; the arm reads
**23 h (0.49×)**. One hour, across the 0.5× line. The standing rule
auto-ledgers it (`ACCEPTED MODEL-CLASS LIMITATION`; C3c is the only failing
criterion and governance passes), the determination stays CALIBRATED, and
the caveat still spends the single ledgerable slot — which C3c-2024 already
spent, so nothing new is spent. It is nonetheless a **regression on a
scored criterion and is reported here first**, not as a footnote. Under the
owner's promotion basis (structural integrity improving while gates regress
may still be a keeper; a load-bearing new FAIL goes to the owner before the
shard is edited) it does not block: C3c is supporting-tier and the
determination did not move. **It is on the record as the arm's cost.** The
mechanism is the one caiso-144 closed on every in-model route: a
deterministic hourly LP does not contain the probabilistic real-time
scarcity premium; the arm did not touch pricing.

## §6 — PROMOTION BASIS, CHECKED

(a) G-IDENT holds on the full span — **yes**. (b) C6 attested, C8 PASS —
**yes**. (c) no load-bearing criterion regresses to a new FAIL — **none**
(C1/C2/C3a/C3b all PASS→PASS). C3a and C4 entered none of the three.
**PROMOTED.**

## §7 — PREDICTIONS, SCORED

| # | registered | verdict |
|---|---|---|
| P-1 | G-REPRO R-1/R-2/R-3 | **HOLDS** |
| P-2 | screen year 2025 | **FALSIFIED** — gross footprint names 2023 |
| P-3 | Δcems = El Segundo + Desert Star, no other plant > 10 % | **HOLDS** (2024/25 exact; 2023 remainder 6.8 % of variance) |
| P-4 | Δd at hod 22–23 in 2025 negative | **HOLDS** (−64 MW) |
| P-5 | `S < 0` in 2025 | **HOLDS**; and the solve agreed (0.300 → 0.298) |
| P-6 | screen response confined to gas + import + storage; renewables < 0.5 % | **HOLDS** |
| P-7 | no load-bearing PASS → FAIL on the full span | **HOLDS** |
| P-8 | DOF byte-identical 9 / 6 | **HOLDS** |

Seven hold, one falsified — the falsified one was the handoff's expectation
about the screen year, and the pre-fixed rule decided it.

## §8 — DISCLOSURES AGAINST INTEREST

1. **C3c-2023 regressed** (§5). One hour, but a PASS → CAVEAT is a gate
   movement whatever its size.
2. **C3a moved favourably in 2023 and 2025 and was flat in 2024** (37.73 →
   37.73). Declared unusable in the PRECOMMIT and excluded both ways; whether
   this counts as the ninth consecutive favourable direction in the lane is
   a matter of definition (two of three years) and it is stated rather than
   argued. The promotion basis contains no price.
3. **The C4-2025 improvement was predicted before the solve** (`S < 0`) and
   is still excluded from the basis; it is a direction that came true, not
   evidence for the arm.
4. **The object was found by accident** (a `--help` probe that ran the
   derive, caiso-259 §8). The PRECOMMIT records the six numbers seen before
   registration as the G-REPRO target, not as results.
5. **The 2023 attribution is not exact** (R² 0.932): a further 6.8 % of
   variance in the 2023 CEMS delta is not El Segundo or Desert Star. Named
   candidates by correlation (Redondo Beach, Malburg, La Paloma) are plant-map
   differences in the 2023 bench between vintages; not attributed further.
6. **The screen year the handoff expected was wrong** (P-2). The gross-footprint
   rule was fixed before F was computed and it governed; 2023 is also the
   year with the smallest expected C4 movement, which cuts against convenience.
7. **A standing duty this creates, stated at the gate:** the derive's anchor
   guard is windowed on the annual total, so a bench-part regeneration that
   changes the CEMS plant map does NOT trip it. When a CAISO bench part is
   regenerated, the demand artifact must be re-derived in the same PR, or
   the demand basis and the scoring basis diverge silently again. Recorded in
   the matrix `demand_repairs` cell.
8. **Three probes now hard-code the pruned `caiso257_ctonly` path**
   (`_caiso258_hod2223_closure.py`, `_caiso260_screen.py`,
   `_caiso255_gdrift_identity.py` as re-pointed) and must be re-pointed
   before re-use — the same consequence caiso-257 recorded for caiso-252.

## §9 — DO-NOT-REDO ADDS

1. **Never regenerate a CAISO bench part without re-deriving the
   supply-consistent demand artifact in the same PR** (§8 #7).
2. **Never run `derive_caiso_supply_consistent_demand.py` casually** — it
   takes no arguments and rewrites the committed artifacts on any invocation.
3. **Never quote the C4-2025 move or the C3a moves as evidence for this
   arm.** Both were excluded before the solve.
4. caiso-258 §10, caiso-257 §10 and every section they carry stand in full.

## §10 — QUEUE

1. **C3c-2023 at 23 h vs 47** — the accepted model-class limitation, now a
   ledgered caveat in two years; in-model queue empty on every route
   (caiso-144). Not an object.
2. **The hod 22–23 price-taking import volume** (caiso-258 §9) — a data
   intake first.
3. **Panoche / the CT volume miss**; **the whole-plant-off days**
   (caiso-187/192, DO-NOT-REDO); **the sidecar identity residual** (caiso-258
   §2.1).
4. **2022 readiness** (caiso-259 §1–§2): H-1 is now buildable on the same
   bench vintage as 2023–2025; H-2/H-3 remain the owner's price-source
   decision.
5. Carried, raised not granted: the **`complete` marker** (owner act — CAISO
   is CALIBRATED on a keeper whose demand basis now matches its scoring
   basis; raised again); the stale `program-status.json` CAISO stamp (not
   touched); the C3a weight basis; the DMM 2025 RA-import basis; S2.

## §11 — DELIVERABLES

PRECOMMIT + ADDENDUM (pushed first); `_caiso260_demand_vintage_phase0.py` +
json; `_caiso260_gdrift_at_solve.json`; `_caiso260_screen.py` +
`_caiso260_screen2023.json` (screen) + `_caiso260_screen{2023,2024,2025}_fullspan.json`;
`gen_caiso260_attestation.py`; the re-derived artifact
(`data/raw/reference/caiso-supply-consistent-demand/*`, committed as the arm);
the bundle `caiso260_demand_vintage` (slim files + `hourly/` sidecars,
attestation with DOF ledger, `metrics.json`, `_verdict.json`); run
**`2026-09-06-caiso-260-b1-demand`** (KEEPER, CALIBRATED) with sidecar and
payload; `keepers/CAISO.json` + `status/CAISO.js`; the caiso-257 run pruned;
the CAISO matrix shard re-stamped (keeper, gates, `demand_repairs` evidence)
and the §5.2 header rewritten; this finding; the calibration-log entry.
Screen bundle deleted.

**Keeper PROMOTED. No `ScenarioConfig` field, no DOF row, no `complete`
declaration, no out-of-training year touched, freeze ACTIVE. Next number:
caiso-261.**
