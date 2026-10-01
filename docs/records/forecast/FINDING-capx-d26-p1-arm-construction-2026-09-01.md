# FINDING — capx D26: the FC-6 P1 arm repaired (additive carbon delta), the pair re-run at the golden's vintage, and neiso-t3's FC-6 re-scored

**Session:** D26 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d26-p1-carbon-arm-t641px`. **Date:** 2026-09-01. **HEAD at launch:**
`3c1f9642` (origin/main). **Solve vintage:** `9e56f0f` + the D26 instrument repair only
(§3). **Charter:** execute D23's attribution — repair the INSTRUMENT so P1 measures the
model instead of the premise of its own pair, then re-score `neiso-t3`'s FC-6 under the
cross-lane re-grade rule (control-first; STOP if anything beyond neiso-t3's FC-6 rows
would flip).

**Headline: the repaired experiment PASSES P1 — under a genuine +$25/t increase over the
resolved RGGI trajectory, cumulative 2026–2050 CO2 FALLS 210.52 → 174.96 Mt (−16.9 %),
prices rise in every year, and CCS retrofits rise. D21's FC-6 P1 FAIL does not survive
the repaired instrument, exactly as D23's attribution predicted: the model's carbon
response has the correct sign in every channel; the FAIL was the arm construction.**
`neiso-t3`'s FC-6 re-scores FAIL → CAVEAT (the surviving CAVEAT is the UNTOUCHED
vacuous-T1.6 battery finding), the determination stays HOLD on FC-1/2/3/4/7, and the
cross-lane re-grade audit confirms nothing beyond neiso-t3's FC-6 rows moved. Published:
prior verdict preserved at `neiso-t3-pre-fc6repair`.

---

## 1. Charter discipline

Repairs are entirely instrument-side, exactly as D23 scoped them: no model parameter,
threshold, band, retirement/retrofit economics, or pre-registered expectation moved. The
one solve-affecting object added is `ScenarioConfig.carbon_price_delta` — an
instrument-grade field the charter explicitly anticipated ("if the honest fix is a new
ScenarioConfig field (e.g. an additive carbon delta)"): default 0.0 (an exact resolver
no-op, proven twice over in §4), forecast-only (rule-13 `__post_init__` guard, the
`gas_price_factor` construction), cache-key registered at its default (default key
unmoved at HEAD `7a57fadff595ca83` and at the vintage pin `603c2498bf71d21d` — both
measured), and never armed in any keeper or golden posture. Rule 28 duties discharged in
the same commit: matrix row + a `carbon_price_delta` cell line in all six ISO shards
(cells `·` by design — instrument plumbing, not a market mechanism to arm; NEISO's `ev`
carries this lane's validation). The vacuous-ladder CAVEAT (`renewable_buildout_pace`,
D21 finding 2) is untouched — still true, still the wiring lane's object. D23's R4
(should `carbon_price` replace, floor, or stack on the program price?) remains the
owner's open design question: the delta field answers the instrument's need without
moving `carbon_price`'s documented replacement semantics for any consumer. No holdout
year (forecast-mode 2026+ solves only, rule 22's own permitted class); nothing in the
backcast namespace; no keeper/shard/marker; no new workflow.

## 2. The repair (what changed, and why this construction)

**The defect being repaired** (D23 §2, in one line): `replace(cfg, carbon_price=25.0)`
REPLACES the resolved carbon signal, and the NEISO base already carries the projected
RGGI trajectory ($26.05/t in 2026 escalating at the published 7 %/yr CCR rate to
$132.16/t by 2050, the EM-6 seam) — so D21's "carbon25" arm CUT the carbon price in
every horizon year and P1 measured the premise of its own pair.

**The repaired construction** — three pieces, one commit (`ef48d446` content):

1. **`ScenarioConfig.carbon_price_delta`** (default 0.0): applied by
   `policy/carbon.py::resolve_carbon_price` as a final additive stage AFTER its
   precedence chain (override / program adder / RFF path), so every carbon consumer —
   dispatch mc (`runner.py:2247`), the capacity-evolution driver (`:1882`), the
   interchange seam (`:2399`), the border adder (`:1224`) — sees base+Δ uniformly.
   The precedence semantics of `carbon_price` are byte-untouched at the default; the
   documented single-consumer replacement behavior D23 verified is exactly as it was.
2. **The paired-arm construction is now first-class**
   (`run_driver_battery.py::PAIRED_ARM_OVERRIDES` + `--paired-arm`), replacing the D21
   scratchpad driver (its finding §8): each arm is the golden's exact reference
   construction (`reference_config(iso, start, end, cmc=False, golden_posture=True)`,
   solved through `solve_and_summarize`) ± exactly one signal. The carbon arm is
   `carbon_plus25 = {"carbon_price_delta": 25.0}` — the base and the arm differ in ONE
   field whose single consumer is the carbon resolver, so the legs differ only in the
   carbon signal, by construction.
3. **The premise is now asserted, not assumed** (D23's R1, both halves):
   `check_forecast_invariants.carbon_pair_premise` resolves both arms' effective signal
   (`resolve_carbon_price` over each arm's own config — the exact resolution every model
   consumer sees) for every common solved year, emits the year-by-year table into
   `paired_invariants.json` (the run record), and refuses to score P1 unless the high
   arm is STRICTLY above base in every year (a violating pair yields P1=SKIP + a FAIL
   premise row). `forecast_verdict.score_fc6` reclassifies a premise-FAIL P1 to a
   MIS-CONSTRUCTED CAVEAT (the rubric §2 FC-6.2 vacuous-evidence lane — never a PASS,
   never a scored FAIL); with no premise row (every pre-D26 committed record) it scores
   exactly as before, measured in §4(a). The battery side gets the same guard for
   carbon-signal ladders (`carbon_ladder_premise`): an inverted ladder's gate rows —
   the D23 §7 T1.1-rung-0 case — are reclassified to vacuous SKIP instead of scoring.

**Why additive-delta and not the other R2 recipes.** R2(i)
(`state_carbon_pricing=False` both arms) sacrifices program realism in the base AND
makes the pair's base leg diverge from the golden — the control-first requirement
(reproduce the committed record, then perturb) wants the base leg to BE the golden's
own base. R2(ii) (program-path mid-vs-high) tests program-escalation response, a
different economic question from P1's pre-registered "+exogenous carbon" object. The
additive delta keeps the base leg identical to the golden, preserves P1's economic
question, and makes the premise hold by construction on every ISO, program or not.

**The year-by-year signal table** (resolved from each arm's own config at the vintage,
`apply_iso_scenario_defaults` applied — the exact resolution the solves consume;
strictly +$25.00/t in all 25 years, the charter's construction requirement):

| Year | Base (projected RGGI) | Repaired arm (+Δ25) | Δ repaired | D21 broken arm | Δ broken |
|---|---|---|---|---|---|
| 2026 | 26.05 | 51.05 | +25.00 | 25.00 | −1.05 |
| 2030 | 34.15 | 59.15 | +25.00 | 25.00 | −9.15 |
| 2035 | 47.90 | 72.90 | +25.00 | 25.00 | −22.90 |
| 2040 | 67.18 | 92.18 | +25.00 | 25.00 | −42.18 |
| 2045 | 94.23 | 119.23 | +25.00 | 25.00 | −69.23 |
| 2050 | 132.16 | 157.16 | +25.00 | 25.00 | −107.16 |

(All 25 years carry Δ = +25.00 exactly; the full table is in the committed
`paired_invariants.json` premise row. The broken-arm column reproduces D23 §2.5's
deltas to the cent.)

## 3. The vintage pin (code and data)

**Code:** solves ran from a sparse worktree at `9e56f0f` (the golden bundle's
`git.basis_sha`, D21's proven vintage) carrying the D26 repair as the ONLY diff —
+46/+20/+184 lines across `scenarios.py` / `policy/carbon.py` /
`run_driver_battery.py`, zero deletions in `src/`, verified by
`git diff 9e56f0f --stat`. The R-A storage-entry default flips and every other
post-golden change stay OUT of the solve code (the vintage ledger keeps
`storage_entry_availability_gate/cost_normalized_rank = "False"`). Scoring ran the
CURRENT instruments from the main checkout at HEAD+repair (checker/scorer), the D21
division of labor made explicit now that the instruments legitimately differ from
their 9e56f0f bytes.

**Pre-solve key parity, the strongest cheap vintage check:** the resolved base config
at the vintage+repair hashes to `0365174ab16cc318` — BYTE-EQUAL to D21's committed base
arm key — and reconstructing D21's broken arm (`carbon_price=25.0`) reproduces its
committed `7924eccc695c0168` too. The repair is therefore key-neutral on the real arm
configs (also isolated directly: pure-vintage code and vintage+repair code produce the
identical key), and the repaired arm keys distinctly at `7784d408fc955785`. Same
split-root environment as D21 (repo=worktree `/home/user/msim-vintage`,
`MARKET_SIM_DATA_ROOT=/home/user/market-simulator`), so keys are comparable to D21's
committed ones and to nothing else (D21 finding 6).

**Data:** `data/clean` was built FRESH from vintage raw bytes (no stale tree to
discard — the D21 leak class closed at the front door): the two NEISO datatypes that
moved since `9e56f0f` — `capacity-market/demand-curve/neiso` (the RC-R +15-line csv)
and `confirmed-retirements/neiso.csv` (+79 lines) — plus the changed
`capacity-market-demand-curve.schema.yaml` were pinned at `9e56f0f` bytes in the data
root, the WORKTREE's own `regenerate_clean.py` rebuilt all datatypes (51 ok; the one
FAIL is `benchmark-corridor`, an FC-5 scoring input never read by a solve, failing on
its own HEAD-side raw/schema drift), both NEISO partitions verified present, and HEAD
raw was restored after curation. The base-arm reproduction (§4b) is the end-to-end
proof of the data vintage, per D21's standing recommendation.

## 4. Control-first (the D8-V/D25 pattern), then the arm

**(a) The committed FC-6 record reproduces from committed artifacts, and the scorer
amendment is inert on it — zero solves.** `forecast_verdict.py` at HEAD+repair, on
exactly the committed inputs (summary, run_config, dof_ledger, hindcast, crossover,
driver-battery, paired_invariants, and D25's corridor + benchmark-corridor), reproduces
the committed `results/ff-t3-neiso-golden/bau/forecast_verdict.json` with **zero
non-provenance diffs** (only `scored_at_sha`/`scored_at_date` differ, as they must).
This is simultaneously the record reproduction AND the measured strictly-additive claim
for the scorer amendment: with no premise row present, nothing moves. (Unit-tested too:
`test_paired_premise_absent_scores_exactly_as_before`.)

**(b) The base arm re-solved at vintage+repair with the field present at 0.0
reproduces the golden exactly.** All 25 trajectory years × every field
(`co2_mt`, `lw_price`, capacity/builds/retirements, scarcity-hour tiers, reserve
margin, `rps_dual`, …) AND the full I1–I14 invariant vector — statuses and details,
the golden's I3 FAIL and I13 WARN included — are identical to the committed
`full_horizon_summary.json`. Cache key `0365174ab16cc318` (= D21's committed base
key; the golden bundle's own `a4b11ef4aaa1be35` is the single-root fold of the same
config, D21 finding 6). 32.1 min wall / 3.44 GB peak RSS, median year 72.4 s. This
is the D21 reproduction gate passed with the NEW FIELD PRESENT AT ITS DEFAULT through
a full 25-year solve — dispatch, capacity evolution, the CCS screen and the
interchange seam all byte-inert under `carbon_price_delta=0.0` — and simultaneously
the end-to-end proof of the vintage data environment (§3). The arm solve was gated
on this check passing (control-first, sequential).

**(c) The repaired arm** (`carbon_plus25`, key `7784d408fc955785`, 31.1 min / 2.93 GB,
25/25 years, no error; committed at `fc6/arms/carbon_plus25/`). Against the
reproduced-golden base, the +$25/t world shows the textbook response in every channel
at once:

- **CO2 falls, in every era.** Cumulative 210.52 → 174.96 Mt (−35.55 Mt, −16.9 %).
  Same-fleet dispatch era: 2026 16.32 → 13.60 Mt (the mirror image of the broken arm's
  +0.21 Mt rise — a −$1/t cut made 2026 dirtier; +$25/t makes it much cleaner).
  Mid-horizon: 2035 10.27 → 5.91 Mt. Late: 2050 3.21 → 3.18 Mt (both fleets nearly
  fully abated by then).
- **Prices rise, in every year** — LW price +$3.4 to +$10.2/MWh (2026: 52.13 → 62.28;
  2040: 70.53 → 75.51) — impossible under the broken arm, whose "carbon" world was
  CHEAPER every year.
- **The CCS screen responds with MORE abatement**: 11,742 vs 11,539 MW by 2032, 13,251
  vs 13,049 by 2040, 15,251 vs 15,049 by 2050 (unabated CC reaches zero in both worlds
  by 2040 — the base's own escalator already drives full conversion; the +$25 arm gets
  there with ~200 MW more CCS capacity throughout). D21's "~3 GW less CCS because of
  the carbon price" is gone with the premise that manufactured it.

## 5. The re-scored P1 and FC-6

**The new `fc6/paired_invariants.json`** (replaced in place, the D21 precedent) is
[P1, P1.premise, P2, P3]: P1 + the premise row scored by the repaired checker on the
new pair — `P1 PASS: cumulative CO2 base 210.52 Mt vs high 174.96 Mt`;
`P1.premise PASS: strictly positive delta in all 25 years (min +25.00, max +25.00 $/t)`
with the full year-by-year base/high/delta table in its `data` block (the charter's
"stated in the run record year-by-year") — and P2/P3 carried VERBATIM from D21's
committed rows. The carry is stated, not smuggled: their arms and construction are
untouched by the carbon repair (multiplicative `gas_price_factor`, D23 §7), and their
per-year solve caches are not re-derivable from the committed summaries; the assembler
refuses to run unless the carried rows match the committed record exactly.

**The re-scored verdict** (same committed inputs as D25's scoring plus the new
paired_invariants; committed at `bau/forecast_verdict.json`):

| | FC-6 battery row | FC-6 paired rows | FC-6 category | Determination |
|---|---|---|---|---|
| committed (D21/D25) | CAVEAT (2 vacuous T1.6 rows) | **P1 FAIL** / P2 PASS / P3 PASS | **FAIL** | HOLD |
| D26 re-score | CAVEAT (2 vacuous T1.6 rows — untouched) | **P1 PASS** (premise annotated) / P2 PASS / P3 PASS | **CAVEAT** | HOLD |

**The cross-lane re-grade audit PASSES** (scripted, both verdicts compared field by
field): the only movements are FC-6's category status FAIL → CAVEAT, its P1 row, the
reasons list dropping `FC-6 driver response FAIL`, and the caveats list gaining
`FC-6 driver response` — all mechanically derived from the FC-6 rows this lane owns.
Every other category, row, reason, caveat and note is byte-identical, and the
determination stays **HOLD** on FC-1/2/3/4/7 (five gates; FC-6 no longer among them).
Nothing beyond neiso-t3's FC-6 flips, so the result publishes rather than STOPs.

**Published:** `ff-verdicts.json` — prior verdict preserved in full at
`neiso-t3-pre-fc6repair` (byte-equal to the prior live entry, asserted), `neiso-t3`
overwritten with the re-score plus the D25-style session narrative (prior stamp
`7b085947b0ee` carried in it); the only changed keys in the file are those two.
`program-status.json` — top-level `d26_fc6_p1_repair` block + the NEISO golden note
append; every other block asserted byte-identical before write;
`t3_determination` stays HOLD. Backcast namespace untouched.

## 6. Pricing (written before launch; measured after)

- **Priced:** two sequential 25-yr solves (base control first — the arm launches only
  after the base gate passes), each ~11–33 min solo / ≤4.3 GB against D21's anchors
  (golden 1753.2 s/3.50 GB; carbon25 solo-ish 655 s; base 1998 s at 2-concurrency on
  the same 4-CPU/15 GB box class) + the ~30-min vintage clean rebuild + scoring (no
  solve). §2.1b basis: the lane charter (director-issued), with the paired-arm driver
  passing `assert_schedulable(2026, 2050, full_solve_authorized=True)` explicitly —
  the D21 §3 licensing posture, now carried by the committed instrument itself.
- **Measured:** vintage clean rebuild 51/52 datatypes ok (~35 min, background); base
  arm 32.1 min / 3.44 GB (median year 72.4 s); carbon_plus25 arm 31.1 min / 2.93 GB;
  both sequential and solo; scoring zero solves. Total solve wall ≈ 1.05 h — inside
  the priced envelope, and the base was gated on its reproduction check before the arm
  launched.

## 7. Blast-radius notes (not this lane's to fix)

- The 11 pinned-cache-key test failures visible at HEAD (`603c2498bf71d21d` pinned vs
  live `7a57fadff595ca83`) PRE-EXIST this lane on clean `origin/main` (measured both
  sides; the R-A arming's declared flip moved the live default). D26 adds no failure
  and moves no key — `check_cache_key_registration.py` passes (219 fields, all
  declared defaults match) and the default key is measured unmoved by the repair on
  both vintages.
- T1.1's pre-registered absolute-rung ladder is still registered ERCOT/PJM-only and
  was not edited (D21's "this lane does not edit pre-registrations" holds here too);
  the battery-side premise guard now detects the D23 §7 rung-0 inversion on any
  program ISO the ladder is ever pointed at, without touching the registry.
- D23's R3 (docs: the stale `state_carbon_pricing` comment; the battery plan's
  program-ISO rung note; D21 §5.2's superseded-by-D23 cross-reference) remains routed
  to a docs/sync-docs pass — not executed here.

## 8. Consequence for the golden re-solve card (ledger §0v.6(a))

**The card's TERMS do not change; its HOLD CONDITION is discharged and one risk leaves
its column.** Stated for the director's sitting:

1. **§0v.6(b) is answered by this lane:** D21's FC-6 P1 FAIL does NOT survive the
   re-score — published FAIL → CAVEAT under the re-grade audit. §0v.6(a)'s "decide
   AFTER the FC-6 P1 instrument repair" precondition is now met.
2. **The sign-defect risk is off the table.** A re-solve is no longer a campaign spent
   into a model with a suspected core carbon-sign defect — the model's response is
   correct-sign in every channel on the correctly-constructed experiment. This
   REMOVES a reason to hold; it does not by itself argue for spending.
3. **The Q16 instrument-ceiling logic is now partially discharged:** FC-5 exists
   (D22/D25) and FC-6's paired leg genuinely grades (premise-guarded). What still caps
   a re-solved golden's FC-6 at CAVEAT is the vacuous T1.6 battery leg — NEISO's
   entire pre-registered battery is that one ladder, and `renewable_buildout_pace`
   remains consumed by no model code (D21 findings 2–3, untouched here). A re-solve
   cannot buy FC-6 PASS until that wiring/registration decision is taken.
4. **One pricing rider the card should carry:** FC-6's paired evidence is
   vintage-pinned, so a re-solved golden needs its OWN paired arms at ITS vintage —
   now turnkey via `run_driver_battery.py --paired-arm` (base reproduces the campaign
   run; carbon_plus25/gasup150/gaspm5 ≈ three more ~30-min solves) plus the ~12-min
   battery. Budget ≈ +2 h of solves on top of the campaign itself.
5. The re-solve's actual object is unchanged and if anything strengthened: the
   zero-storage-entry divergence (D25 §6.3 — the corridor's largest cross-ISO family)
   is what the R-A arms would move; nothing in this lane touched storage entry.

## 8b. Blast radius left standing (unchanged from D23 §7 where not repaired here)

- The T1.1 absolute-rung ladder's pre-registration is unedited; the battery premise
  guard detects (and vacuous-izes) its program-ISO inversion rather than re-arming it.
  Re-registering T1.1 rungs as delta-form for program ISOs is a plan-§2 decision.
- T1.2's "cap dual ≈ $25" expectation still carries the absolute-knob mental model
  (D23 §7's note to R1's owner) — unexamined here; T1.2 is mass-cap machinery, outside
  the exogenous-signal premise by design.
- D23's R4 (replace vs floor vs stack for `carbon_price` itself) remains the owner's
  open question. The delta field neither presupposes nor forecloses any answer.

## 9. Reproduction record

```
# vintage worktree (sparse, no data/raw), repair applied:
git worktree add --no-checkout /home/user/msim-vintage 9e56f0f
(cd /home/user/msim-vintage && git sparse-checkout init --no-cone \
  && git sparse-checkout set '/*' '!/data/raw' && git checkout)
# apply the D26 repair diff for scenarios.py / policy/carbon.py /
# run_driver_battery.py onto the worktree (this branch's first commit vs its parent;
# the one context conflict is the R-A defaults-ledger flip — resolve to the VINTAGE
# "False" values and append only the carbon_price_delta entry)

# vintage clean data (curation reads/writes the MAIN checkout via the seam):
git checkout 9e56f0f -- data/raw/capacity-market/demand-curve/neiso \
    data/raw/confirmed-retirements \
    data/dictionary/schema/capacity-market-demand-curve.schema.yaml
(cd /home/user/msim-vintage && MARKET_SIM_DATA_ROOT=/home/user/market-simulator \
    python scripts/regenerate_clean.py)
git checkout HEAD -- data/raw/capacity-market/demand-curve/neiso \
    data/raw/confirmed-retirements \
    data/dictionary/schema/capacity-market-demand-curve.schema.yaml

# the arms (sequential; env per D21):
cd /home/user/msim-vintage
export MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    MARKET_SIM_DATA_ROOT=/home/user/market-simulator
python scripts/run_driver_battery.py --iso NEISO --start-year 2026 --end-year 2050 \
    --paired-arm base          --out /home/user/fc6-arms/base          --full-solve-authorized
python scripts/run_driver_battery.py --iso NEISO --start-year 2026 --end-year 2050 \
    --paired-arm carbon_plus25 --out /home/user/fc6-arms/carbon_plus25 --full-solve-authorized

# scoring (main checkout, HEAD+repair instruments):
scripts/check_forecast_invariants.py --paired \
    /home/user/fc6-arms/base/NEISO/0365174ab16cc318 \
    /home/user/fc6-arms/carbon_plus25/NEISO/7784d408fc955785 \
    --pair-kind carbon --json
scripts/forecast_verdict.py --tier t3 \
    --summary results/ff-t3-neiso-golden/bau/full_horizon_summary.json \
    --run-config results/ff-t3-neiso-golden/bau/run_config.json \
    --dof-ledger results/ff-t3-neiso-golden/bau/dof_ledger.json \
    --hindcast-score results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json \
    --crossover-score results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json \
    --driver-battery results/ff-t3-neiso-golden/bau/fc6/driver-battery-neiso-2026-08-31.json \
    --paired-invariants results/ff-t3-neiso-golden/bau/fc6/paired_invariants.json \
    --corridor results/ff-corridor/dispositions/neiso-t3.json \
    --benchmark-corridor results/ff-corridor/benchmark-corridor-anchors.json \
    --json-out results/ff-t3-neiso-golden/bau/forecast_verdict.json
# (paired_invariants.json = the new [P1, P1.premise] output + D21's committed P2/P3
#  rows carried verbatim; the control run of the same command with the COMMITTED
#  paired_invariants reproduces the committed verdict with zero non-provenance diffs)
```
