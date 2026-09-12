# PLAN — SPP-31: the road to `complete` / `frontier`. A decision memo for the owner, and the ordered work plan behind it.

**Lane** SPP-31 · **Base** `9e499b0e8d6f851a4e726bbd42b207ca5368654c` · **LP SPENT: ZERO** (rule 32
`[R-SHARD]` (a) — this session is an orchestrator with nothing to orchestrate; no shard launched, no
solve, no replay) · **Keeper UNCHANGED and UNTOUCHED** `2026-09-10-spp-27-commitment-grain`, bundle
`results/calibration/spp27_span` (read, never written) · **Nothing registered, no verdict minted, no
matrix cell moved, no marker file touched, no `rm` issued.**

**Declaring `complete` or `frontier` is an OWNER ACT. This document asks; it does not do.**

Every number below is re-derived in this session from the committed artifacts and
`scripts/calibration_verdict.py`, including every number the handoff prompt supplied. Where the
prompt's numbers and HEAD disagree, §5 says so.

---

## 1. RECOMMENDATION

| | recommendation |
|---|---|
| **`complete`** | **DECLARE.** SPP clears the measured peer bar today, on the same rubric, in the same shape as the two most recent declarations. |
| **`frontier`** | **DO NOT DECLARE.** Not close, and the disqualifying fact is measurable: **16 of 173** applicable mechanism-matrix cells are adjudicated in SPP against **66–131 of 152–182** in every declared ISO. `frontier` means the lever queue is exhausted. SPP's has **155 untested cells**. |

They are separate claims and this memo answers them separately (§4).

**What would change the `complete` recommendation:** if the owner reads `complete` as saying anything
about out-of-training readiness. It does not at HEAD (§5), but SPP is the only ISO in the program with
**zero** out-of-training price coverage, and if the marker is meant to signal "ready for the validation
ladder", SPP-30 must land first.

---

## 2. THE PEER TABLE — measured, not asserted

Every row re-scored in this session with `scripts/calibration_verdict.py --run-id <id> --json` at HEAD,
rubric **v3.7**, committed artifacts only, no solve.

### 2a. Today, one rubric, all seven ISOs

| ISO | keeper (current) | det. | grade | fails | ledgered | protective | free-class C1 | DOF n/res | auth. price tuning | D1 | D2 | D4 | marker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **SPP** | `2026-09-10-spp-27-commitment-grain` | **CALIBRATED** | 7/8 | **0** | 1 (C3c) | 0 | **16/16 · 12/12** | **3 / 2** | **YES** | ✓ | ✓ | ✗ | **none** |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | CALIBRATED | 7/8 | 0 | 1 (C3c) | 0 | 30/30 · 22/22 | 12 / 7 | no | ✓ | ✓ | ✗ | complete |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | CALIBRATED | 7/8 | 0 | 1 (C3c) | 0 | 12/12 · 8/8 | 8 / 6 | no | ✗ | ✗ | ✗ | complete |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | CALIBRATED | **8/8** | 0 | **0** | 0 | 16/16 · 12/12 | 19 / 6 | no | ✗ | ✓ | ✗ | complete |
| CAISO | `2026-09-10-caiso-271-egrid-family` | CALIBRATED | 7/8 | 0 | 1 (C3c) | 0 | 12/12 · 8/8 | 9 / 6 | no | ✗ | ✓ | ✗ | complete |
| NYISO | `2026-09-09-nyiso-221-fuelvintage-span` | CALIBRATED | 7/8 | 0 | 1 (C3c) | 0 | 14/14 · 10/10 | 13 / 6 | no | ✓ | ✓ | ✗ | complete |
| MISO | `2026-09-09-miso-250-ep-gas` | CALIBRATED | 7/8 | 0 | 1 (C3c) | 0 | 16/16 · 12/12 | 42 / 2 | no | ✗ | ✓ | ✗ | **none** |

Criterion statuses are identical across all seven but PJM: `fuelmix / sysvol / price_mean / price_shape /
dispatch_corr / governance / forced_share` = PASS, `price_tail` = CAVEAT (ledgered). PJM's `price_tail`
PASSes, which is why it grades 8/8. **D4 is `False` in all seven** — it is nobody's discriminator.

### 2b. At declaration

| ISO | declared | `keeper_at_declaration` | re-scorable at HEAD? | re-scored verdict |
|---|---|---|---|---|
| NYISO | 2026-09-06 | `2026-09-06-nyiso-202-startup-aware` | **yes** | **CALIBRATED · 7/8 · 0 fails · 1 ledgered C3c · 0 protective · C1 14/14 · 10/10** |
| CAISO | 2026-09-06 | `2026-09-06-caiso-260-b1-demand` | **yes** | **CALIBRATED · 7/8 · 0 fails · 1 ledgered C3c · 0 protective · C1 12/12 · 8/8** |
| ERCOT | 2026-08-31 | `2026-08-25-234-eastex-identity` + `2026-08-25-236-swcap-clip-k33` (two-config partition) | no | — |
| PJM | 2026-07-31 | `2026-07-30-pjm-140-rampenv` | no | — |
| NEISO | 2026-07-07 | `2026-07-08-neiso-54-steamgas-ct` | no | — |

**Why three are not re-scorable, stated rather than glossed.** Their declaration-time bundles, registry
sidecars and run payloads were pruned under rule 15 `[R-DASHBOARD]`'s keeper-only retention, and this
clone cannot reach the declaration-date trees: `git rev-list --count HEAD` = **666** and the earliest
commit in it is dated **2026-09-07**, while `frontend/data/backcast/status/<ISO>.js` (the per-ISO status
shard that carries a keeper's scored verdict) was itself only created on 2026-09-09. Their
declaration-era verdicts were also produced under earlier rubric versions, so even a recovered score
would not be like-for-like with v3.7. **This is a limit of the record, not a finding against them** — and
it is the reason §2a, not §2b, is the decision-relevant table.

### 2c. Does SPP clear the bar?

**Yes, exactly.** The two declarations we *can* re-score at HEAD — the two most recent, six days ago —
are **byte-identical in shape** to SPP today: CALIBRATED, grade 7 of 8, 0 fails, one ledgered C3c caveat,
0 protective caveats, every free class in band. SPP additionally has the **leanest DOF ledger in the
program** (3 entries / 2 residual) and is one of only **three** ISOs whose D-1 *and* D-2 legitimacy
diagnostics both pass.

---

## 3. THE CASE — AGAINST FIRST (house convention, `RESULT-spp27-span.md` §8)

### 3a. AGAINST

1. **SPP is the ONLY ISO whose keeper reaches its determination through the rule-1 `[R-STRUCT]`
   authorized price-tuning channel** (`calibration_attestation.json` → `free_parameters.entries[].
   authorized_price_tuning`: present in SPP, absent in all six others). The value is a uniform **0.93**
   on all four bands of the ten fossil classes SPP dispatches, and the record is explicit that
   **C3a and C3b PASS only after it** — before SPP-52a, C3a was FAIL (2025 +10.3 %) and C3b was FAIL
   (2025 NRMSE 0.204); after, +1.36 / −0.61 / +3.61 % and 0.1647 / 0.1762 / 0.1755
   (`docs/calibration-log/spp.md` spp-20). It is fully rule-legal — conditions (a)–(e) of the 2026-09-05
   amendment were verified at promotion, one config across all three years, the owner's own number,
   declared in `PRECOMMIT-spp-52a-2026-09-09.md` **before** the solve, never swept, C6 PASSes on the
   declaration — but **it is a difference in kind from how all five declared ISOs got there**, and a
   `complete` entry that does not say so on its determination basis would be hiding it.
2. **Zero out-of-training coverage — SPP is alone in this.** `frontend/data/backcast/tail/actual_tail.json`
   carries SPP `{2023, 2024, 2025}` against ERCOT/NEISO/NYISO `{2018…2026}`, PJM `{2018…2025}`,
   CAISO/MISO `{2022…2026}`; `frontend/data/backcast/bench/SPP/` holds exactly `2023/2024/2025` against
   2020- or 2021- for every peer. Every declared ISO had a validation ladder *available* when it was
   declared, spent or not. SPP has no rung to climb.
3. **The keeper is one day old and is the NINTH in five days.** SPP's first-ever solve was 2026-09-07
   (`docs/calibration-log/spp.md` spp-1); keeper 9 landed 2026-09-11. A `complete` entry's `keeper` field
   is under `audit_keepers` M1 currency + determination re-verification, so a lane this fast will churn
   the marker on roughly every promotion.
4. **Q5's uniform rule makes the marker fragile on a lane whose stated promotion convention is
   structure-over-gates.** Standing owner rule (r#12, 2026-08-30): *"a `complete` marker cannot stand on
   a NOT-YET keeper"*. NYISO's marker has fallen to it **three times**, each on an accurate-input repair
   the standing formula promotes and the marker cannot carry
   (`calibration-complete.json` → `complete.NYISO.prior_withdrawal_2026_09_05.reason`). Keeper 9 was
   promoted by the owner on exactly that principle: *"If structural integrity improves but gates regress
   that may still be a keeper."* A declared SPP should be expected to lose the marker at some future
   structural repair, and that is a cost, not a surprise.
5. **A named, unrepaired structural absence that no declared peer's basis carries an equivalent of.**
   `FINDING-spp-64-2026-09-10.md` §5: SPP's LP carries **one** internal constraint; its two zonal prices
   are identical in **87.4 / 86.1 / 76.8 %** of hours (mean |N−S| 0.595 / 1.227 / 1.573 against a measured
   hub spread of 12.129 / 17.227 / 15.180), while SPP's own published RTBM archive shows **735 / 723**
   distinct internal constraints binding in **96.4 % / 97.9 %** of all hours. The model reproduces
   **5–13 %** of measured congestion rent.

### 3b. FOR

1. **The bar is measured and SPP clears it exactly** (§2c). Declining on the same evidence that
   supported CAISO's and NYISO's declarations six days ago would apply a bar to SPP that was applied to
   nobody else.
2. **SPP is the leanest model in the program on the measure rule 21 `[R-DOF]` exists to police.**
   3 ledgered free parameters / 2 residual-identified, against 8–42 / 2–7 elsewhere. And of those two,
   `offer_curve_by_group` is expressly **not** an open root-cause issue under rule 20's R-AY
   cross-reference, leaving `wefor_multiplier` = 0.7 (audit C-15) as SPP's single genuinely open
   residual DOF — which **four of the five declared ISOs also carry** (all but CAISO).
3. **Its legitimacy diagnostics are among the cleanest**: D1 ✓ / D2 ✓, matched only by ERCOT and NYISO.
   NEISO, PJM, CAISO and MISO all carry a failing D-1.
4. **The marker authorizes nothing at HEAD, so declaring is low-stakes and reversible.** `[R-HOLDOUT]`
   and every enforcing gate are gone (§5). Withdrawal is a routine, precedented act with a written
   procedure (NYISO, three times).
5. **It unblocks the one thing that is actually blocked, and the blocker is the marker itself.** The
   forecast board's §2.1b gate (a) reads `fail` for exactly the two ISOs with no `complete` entry —
   **MISO and SPP — both of which score CALIBRATED**
   (`frontend/data/forecast/program-status.json` → `isos.<ISO>.gate.a_keeper_marker.status`). SPP's own
   detail string says it in terms: *"SPP still has NO `complete` entry … marker complete=False
   final=False and THIS ROW'S STATUS IS UNCHANGED BY THE RE-KEY."*
6. **C3c is closed as a work item and the closure is earned** (§6), so the single ledgered caveat is not
   a deferred to-do. Rule 22 `[R-C3C]`'s model-class limitation is, for SPP, a measurement.

### 3c. What the `complete` entry must carry if declared

Beyond the standard keys (`declared / keeper / by / determination / keeper_at_declaration /
tier_authorized / locked_test / freeze_interaction / keeper_rekey_policy`), three items belong on the
determination basis, reported at full magnitude — the same way CAISO's entry carries *"standing
constraints carried, not hidden"*:

- the **authorized price-tuning channel** (uniform 0.93, ledgered, `authorized_price_tuning` declared,
  C6 passes on the declaration) and the fact that C3a/C3b PASS after it;
- the **one-zone root cause** (`FINDING-spp-64` §5) and that card **R-be** is open on the keeper;
- **zero out-of-training coverage**, and that `CALIBRATED` is a rubric determination, **not** a certified
  out-of-sample skill claim — true of every ISO since `[R-HOLDOUT]` was removed, and especially worth
  saying for an ISO with no out-of-training year at all.

---

## 4. `frontier` IS A SEPARATE CLAIM — and SPP does not have it

`complete` designates the keeper and feeds the forecast program's gate (a). **`frontier` is a
methodology-frontier claim**: the ISO's in-model lever queue is exhausted. The existing bases say so in
their own words — PJM: *"Structural lever queue measured EMPTY at pjm-142"*; CAISO: *"The in-model lever
queue was measured empty at caiso-200"*; ERCOT: *"every chartered lane adjudicated on record"*.

**The measurement, from the mechanism-matrix shards** (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`,
counting `cell:` verdicts; `.` = n/a excluded from "applicable"):

| ISO | applicable cells | adjudicated (K/R/I/G) | open (O) | **untested (U)** | adjudicated share | `frontier`? |
|---|---|---|---|---|---|---|
| NYISO | 182 | 131 | 3 | 48 | 72 % | yes |
| MISO | 182 | 120 | 9 | 53 | 66 % | no marker |
| CAISO | 176 | 107 | 6 | 63 | 61 % | yes |
| ERCOT | 178 | 103 | 16 | 59 | 58 % | yes |
| PJM | 165 | 85 | 7 | 73 | 52 % | yes |
| NEISO | 152 | 66 | 4 | 82 | 43 % | yes |
| **SPP** | **173** | **16** | **2** | **155** | **9 %** | **—** |

SPP is not within a factor of four of the lowest declared ISO. Its keeper shard
(`frontend/data/backcast/keepers/SPP.json`) carries no `frontier` block, and the four cards in §7 are
live, chartered work. **`frontier` is not a close call and this memo does not ask for it.**

*(Caveat on the peer column, stated honestly: NEISO's 43 % is the frontier bar as actually applied, and
its declaration is the oldest. The measurement above is a census of adjudication breadth, not a
like-for-like reconstruction of what each declaring session measured.)*

---

## 5. THE GATE-CODE QUESTION — the handoff's premise is FALSE at HEAD, and that CHANGES the sequencing

The handoff asserts that CLAUDE.md rule 22's `[R-HOLDOUT]` coda (*"every enforcing gate was removed
2026-09-09"*) is contradicted by live code, and concludes that **a `complete` declaration is a
prerequisite for SPP to spend a validation year**. **It is not.** Checked limb by limb at
`9e499b0e`:

| claim | HEAD | evidence |
|---|---|---|
| `run_calibration_full.enforce_holdout_year_gate` is called at two entry points | **the function does not exist** | `grep -rn "def enforce_holdout_year_gate" --include=*.py .` → no match. The name survives only in stale docstrings: `scripts/run_calibration.py:15`, `scripts/knob_jacobian.py:10,230`, `scripts/data/derive_actual_tail.py:72`, `scripts/data/fetch_campd_unit_level.py:71`, `scripts/lib/invariant_ledger.py:20` |
| `--holdout-authorized` is still a CLI flag in both runners | **not a flag in either** | no `add_argument("--holdout-authorized")` anywhere; `python3 scripts/run_calibration_full.py --help \| grep -i holdout` and the same for `run_calibration.py` both return nothing |
| `dashboard_add_run.py` still reads the marker | **no** | `enforce_registration_marker_gate` is named in the module docstring at `scripts/dashboard_add_run.py:31` and **does not exist**; the file's only functions are `_protected_run_ids`, `_bundle_dir`, `resolve_bundle`, `_load_json_doc`, `prune_iso`, `main` (lines 70/112/128/148/163/235) |
| `derive_actual_tail.py` / `derive_actual_amplitude.py` silently skip an unauthorized ISO-year | **no** | `_year_emittable` is `return True` unconditionally — `derive_actual_tail.py:103-111`, `derive_actual_amplitude.py:74-82` |
| the locked tier is unspendable under an **ACTIVE** `holdout-freeze.json` | **the file does not exist** | `frontend/data/backcast/holdout-freeze.json`: *No such file or directory*. The only readers left are comments |
| `run_calibration_full.py` carries a year gate | **two dead constants** | `HOLDOUT_CALIBRATION_YEARS` and `HOLDOUT_MARKER_FILE` are defined at `scripts/run_calibration_full.py:8690-8691` and **referenced nowhere else in the file** |
| `audit_keepers` H1 holdout quarantine | **vestigial** | `"H1"` appears only at `scripts/audit_keepers.py:992,996`, both inside the *pass* branch. No code path emits an H1 failure |
| `holdout_policy.tier_for_year` | **pure classifier, as CLAUDE.md says** | `scripts/lib/holdout_policy.py:129-148`; module docstring lines 5-15 |

**THE CODE AGREES WITH CLAUDE.md. What is stale is a set of DOCSTRINGS AND COMMENTS**, and they are what
the handoff's premise was built on. **This memo does not edit any of them** (routed as card **R-bg**,
§7) — the correction that matters is the sequencing one:

> **SPP may solve, score and register 2020 / 2021 / 2022 — or 2018, 2019, 2026 — today, with no marker,
> no flag and no authorization.** Lane SPP-30 is not blocked on this declaration and must not wait for
> it. A `complete` declaration is **not** a prerequisite for anything SPP wants to spend.

**What the marker DOES still do at HEAD — three live consequences, all verified:**

1. **`audit_keepers` M1** (`scripts/audit_keepers.py:159-199`) — for ISOs *in* `complete` only, the
   entry's `keeper` must name the current designated keeper (M1a) and the determination it asserts must
   match that run's live verdict (M1b). Declaring puts SPP under this audit. A benefit, and a duty.
2. **Quarantined-year plant-emission-rate intake.** `scripts/data/derive_plant_emissions_v2.py
   --holdout-intake SPP` requires `complete` **or** a logged `intake_log` authorization — and the
   intake-log reader's ISO vocabulary at line 244 is `{"ERCOT","CAISO","PJM","MISO","NYISO","NEISO"}`,
   which **excludes SPP**. So for 2022 / 2026 emission rows, the marker is **SPP's only route**. This is
   the one place where declaring materially unblocks SPP-30's successor work.
3. **Forecast §2.1b gate (a)** (`scripts/ff_readiness_battery.py:1163-1183`) — `fail` today on the
   marker alone. **Note also** that `GOLDEN_ISOS` at `ff_readiness_battery.py:102` does **not** include
   SPP, so the battery does not compute SPP's scorecard; SPP's board row is hand-maintained by the SPP
   lane. Admitting SPP to `GOLDEN_ISOS` is a separate act — the board itself says so:
   *"GOLDEN_ISOS is the capx director's call."*

**I have not resolved the discrepancy, edited CLAUDE.md, or deleted or repaired any gate or docstring.**

---

## 6. C3c IS CLOSED AS A WORK ITEM, AND NOTHING BELOW PLANS AGAINST IT

Reproduced this session from the committed artifacts:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model hours > $200 (max zonal dual) | **0** | **5** | **0** |
| RT actual (`actual_tail.json` `rt_gt`) | 42 | 59 | 68 |
| DA actual (`da_gt`, reported-only) | 6 | 35 | 0 |

`FINDING-spp-29-c3c-price-tail-2026-09-11.md` establishes, at zero LP, that the residual is neither
congestion (ρ(hourly congestion rent, RT hub price) = **+0.019**) nor any hourly quantity error: SPP's
**own** fully-nodal day-ahead market cleared >$200 in **0 / 14 / 0** of those tail hours with a 2025 DA
annual maximum of **$176.62**, and re-pricing the keeper's own fleet against SPP's **metered** net load
with perfect foresight still gives **7 / 29 / 0** against 42 / 59 / 68 — **FAIL on the scorer's own band
in all three years**, 2025 capping at **$166.50**. What remains is an offer markup of **9.5× / 7.3× /
9.4×** marginal cost in real time.

**No card below is chartered against C3c.** Rule 22 `[R-C3C]`'s model-class limitation is earned and
measured for SPP. Re-opening it needs new evidence meeting rule 28(a), not a fresh opinion.

---

## 7. THE ORDERED WORK PLAN

Ordering principle: **zero-LP first, then the one card with a real structural object behind it.** SPP's
measured span cost is **499 s of LP for 2023–2025** (`docs/SHARDREPORT-spp27-span.md:24`), ≈166 s/year,
so under rule 32 `[R-SHARD]` (b) **one year = one shard = one commit**, comfortably inside the 20-minute
ceiling once a cold container's clone + `--profile spp` hydrate is counted (~20–35 min wall per shard,
of which the LP is under 3 min). A screen is 1 shard; a span is 3 parallel shards. **The parent runs no
LP.**

Every card below states: the ONE seam · the rule-19 `[R-ONE-MECH]` enumeration · the rule-13 forward
story · the rule-21 `[R-DOF]` effect · a **structural** screen gate that never reads the target residual
· shard cost.

### Card 1 — **R-bf**: the 2024 hourly availability remnant. ZERO LP. *Do this first.*

- **Object.** 2024 is the only year whose tail is an hourly net-load event (34 of 59 tail hours in the
  top actual-net-load decile; SPP's own DA market reached $563.55 and 35 hours >$200) and the only year
  that misses the perfect-quantity band at all — by 0.0085. The model produces 5 hours there and all 5
  are `ISOConfig.voll` infeasibility cliffs, not a scarcity curve (keeper 2024 LP max is exactly
  $2,000.00). **The question is a rule-14 `[R-ACCURATE]` availability question, not a price question:**
  *in 2024's 35 DA-tail hours, does the model's supply availability match what SPP actually had?* In
  those hours the model holds a median **8,233 MW** above its $74.80 marginal unit.
- **ONE seam.** The SPP hourly availability array — i.e. whichever of
  `data/raw/campd-unit-outages-SPP.csv` / `-short-SPP` / `-layup-SPP` / `campd-partial-outages-SPP.csv`
  the phase-0 census shows is missing the winter event (Winter Storm Heather is in this window).
- **Rule 19 enumeration.** Availability reaches `pmax × availability[g,t]` and nothing else; the
  commitment floors (`mustrun_*`), the offer channel (`offer_curve_by_group`) and the curtailment
  channel are separate seams and are not touched. Any repair **replaces** a row in the outage extract;
  it never stacks a second derate on the same unit-hour.
- **Forward story.** Forced-outage / derate windows are the canonical rule-13 admissible input: a
  physical availability event, reproducible for a forward year from forward drivers (the same extract
  the forecast path builds), responsive to changed conditions.
- **DOF effect.** **Zero** — a measured extract correction adds no free parameter.
- **Screen gate (STRUCTURAL, never reads C3c).** *Does the model's 2024 availability differ from CAMPD's
  own record in the named hours, in the direction and magnitude the census implies?* The gate is a
  **census identity**: model available MW vs CAMPD-reported available MW, per unit, in the 35 DA-tail
  hours. It may kill the card; it may not promote it. **C3c is not in the gate and must not be.**
- **Shard cost: 0.** Answerable entirely in the parent against committed CAMPD and the keeper's
  committed `hourly/` sidecars. Only a *confirmed, sized* discrepancy earns a solve — and then one
  2024 screen shard, then the full span (3 shards) under rule 16 `[R-ALLYEARS]`.
- **Why first.** It is the only reachable tail-adjacent work left (`FINDING-spp-29` §5), it costs
  nothing, and it is the kind of card that either dies at phase 0 or produces a real measured input.

### Card 2 — **R-bc**: price-forming curtailment. *The one card with a real structural object.*

- **Object.** Rule 14 `[R-ACCURATE]` owes the model ~**11.8 TWh** of SPP wind curtailment. The
  refuted channel (`spp_curtailment_ceiling`, a CF upper bound) removes the price-setter, so a
  price-forming curtailment must **replace** it: a reduced-form curtailment entering as an **LP
  constraint whose dual reaches the zonal price** — the same standing the transmission limit already has
  — so that when it binds, wind is marginal, the price goes to its offer, and the curtailment and the
  negative-price hour are **one event**, as in the real market.
- **CHARTER BOUNDARY, BINDING.** **Against the NEGATIVE tail and the wind volume ONLY.**
  `FINDING-spp-29` §2 shows the over-delivered wind is absent from the upper-tail hours
  (+0.18 / −1.20 / +0.31 GW) and §3 shows the upper tail survives perfect quantities. **A lane that
  charters R-bc against C3c will fail, and it will fail for reasons that have nothing to do with R-bc's
  merits.** The words *"and the upper tail"* must never be added to its success test.
- **ONE seam.** A new constraint row in the LP (`model/dispatch.py` matrix build), not an offer edit and
  not a bound. `spp_curtailment_ceiling` must be **off** in the same arm — never stacked.
- **Rule 19 enumeration.** Nothing else prices SPP wind: `pmin_mw`, `min_run_hours`, `min_down_hours`,
  `startup_cost_per_mw` are 0 on every SPP fossil unit (SPP-44 / SPP-63, reproduced at SPP-64); the only
  live channels are `offer_curve_by_group` at a uniform 0.93 and the flat −$26 PTC offer. This mechanism
  **replaces** the ceiling.
- **Forward story.** A reduced-form transmission-limited curtailment regenerates for a forward year from
  forward drivers (installed wind by zone, the zonal shape, the corridor rating) and responds to changed
  conditions — more wind, more binding. It must **not** be parameterized from the solve year's own
  metered curtailment volume, which would be a backcast-only overlay.
- **DOF effect.** Depends entirely on construction, and this is the card's real risk: a reduced form with
  a fitted depth is a new residual-identified free parameter (SPP's ledger would go 3 / 2 → 4 / 3). The
  PRECOMMIT must state the identification source **before** the solve. A construction identified from
  SPP's own published flowgate limits is admissible; one identified from the negative-hour count is not.
- **Screen gate (STRUCTURAL).** Pre-registered, four legs moving **together**: wind volume **down**
  toward the measured level; negative hours **up** toward **1,018** (model 167); congestion rent **up**
  toward the measured $12–17 mean |N−S|; C3b down. **A variant that moves only the volume is the arm
  already killed** (SPP-63). None of these four is C3c.
- **Screen year: NAMED IN THE PRECOMMIT BEFORE THE SCREEN RUNS, and it is the year whose MEASURED SPP
  wind-curtailment volume is largest** — read at phase 0 from
  `data/raw/spp-hsl/spp_wind_curtailment_annual.csv`, **never** the year with the biggest residual
  (rule 29 `[R-SCREEN]` (1)).
- **Shard cost.** phase 0 in the parent (0 LP) → **1 screen shard** (~20–35 min wall, ~3 min LP) → full
  span **3 shards in parallel** (~20–35 min wall each) only if the screen clears its pre-registered gate.
- **Control.** Keeper 9's **committed** bundle, differenced — rule 29(b) form 4, with a `G-DRIFT` code
  audit recorded in the PRECOMMIT. **No control solve.**

### Card 3 — **R-be remnant**: day selection for the ST_GAS must-run window. *Expect it to die at phase 0.*

- **Object.** Keeper 9 fixed the window's **grain** (peak-to-mean 1.2349/1.2159/1.2159 → **1.0000**;
  implied starts 2,843/3,002/2,792 → 288/342/315 against a meter of 647/746/778). What remains is **day
  SELECTION**: for plants 1230 / 1235 / 1271 the day-selection lift over chance is only ~**2×**, and
  `D4.passed` stays `False` at 4/4/4 conduct-FAIL rows.
- **ONE seam.** The ranking key inside `caiso_ra_mustoffer_min_gen`'s SPP limb — the signal by which
  operating days are ordered. Size (`online_frac`), level (`committed_pct`) and membership stay untouched.
- **Rule 19 enumeration.** One mechanism id (`st_gas_mustrun_per_plant` / mechanism-16) already floors
  this class; this card **re-keys** its day ordering and adds nothing beside it.
- **Forward story — AND THIS IS WHERE IT DIES.** Both SPP-27 and SPP-28 report the same conclusion:
  **no forecast-admissible signal available to this model reaches it.** The plants answer to their own
  utility's conditions, not to SPP-wide load. Per-year `mustrun_online_frac_per_year` is registered
  backcast-only and is refused. A per-plant grain predicate needs a threshold — a free parameter chosen
  against the very statistic it is scored on, which rule 1 `[R-STRUCT]` (c) forbids. **Mooreland 3008 is
  deliberately not special-cased.**
- **Screen gate.** *Phase 0 only, zero LP:* enumerate every candidate day-ranking signal and show it is
  rule-13 admissible (computable for a forward year from forward drivers). **If the enumeration is empty
  — which both predecessors say it is — the card CLOSES with no LP spent.** That is the expected and
  correct outcome, and it should be recorded as one rather than forced into a solve.
- **Shard cost: 0** expected. If a genuinely admissible signal is found: 1 screen shard + 3 span shards.

### Card 4 — **R-ba**: the ST_GAS / CT_PEAKER merit-order inversion. *Last, and bounded.*

- **Object.** Real and reproduced (`FINDING-spp-64` §6): ST_GAS runs at **12.9 %** CF below CT_PEAKER at
  **19.0 %**. But **every thermal class clears within a ~$5 band** (COAL_PRB p50 $33.67, CC_REGULAR
  $33.90, CT_PEAKER $35.22, ST_GAS $32.51, COAL_LIGNITE $34.55). Correcting the order re-ranks classes
  inside a band that should be tens of dollars wide.
- **ONE seam.** Class heat-rate / offer construction for ST_GAS and CT_PEAKER — **not**
  `offer_curve_by_group`, which is the authorized *level* channel and must not be re-cut or swept here.
- **Rule 19 enumeration.** The must-run floor (card 3) and the offer level (0.93) already act on ST_GAS;
  a merit repair must reconcile with the floor, not stack on it.
- **Forward story.** A measured per-plant loaded heat rate from SPP's own CAMPD record is rule-13
  admissible and regenerates forward — the same construction PJM already carries in its ledger.
- **DOF effect.** Zero if measured per-plant; a new residual entry if fitted. Measured only.
- **Screen gate (STRUCTURAL).** *Does the measured heat-rate ordering of the two classes differ from the
  model's, in the direction the CF inversion implies?* Zero-LP, computable against CAMPD before any arm.
- **Shard cost.** phase 0 in the parent → 1 screen shard → 3 span shards.
- **Sequencing.** **Behind R-bc**, exactly as `FINDING-spp-63` §8 and `FINDING-spp-64` §9 both declare:
  the band's *width* is the deeper fact, and the width is the wind/congestion object.

### Card 5 — **R-bg** (NEW, routed not fixed): the stale holdout docstrings.

Zero LP, docs-only, **owner-optional**. §5's table lists nine places where a comment or docstring names
a gate that no longer exists. They mislead: this lane's own handoff was built on them and reached the
wrong sequencing conclusion. **Not actioned here** — a lane that edits a governance surface while
planning about it has pre-empted the owner. Named so it is not re-discovered a third time.

---

## 8. NO-BUILD LIST — do not re-open these without new evidence meeting rule 28(a)

| object | status | why |
|---|---|---|
| **Sub-zonal topology change** (`internal_congestion_split`, cards SPP-54 / SPP-57) | **NO-BUILD for C3c; `U` and not opened** | `FINDING-spp-64` §8: 2024 congestion rent is spread over **444** monitored facilities — top-20 = 47.4 %, **23** for half, **115** for 90 %. That is not a 3-zone object; it is the same shape as MISO's RO-3 NO-BUILD verdict. `FINDING-spp-29` §1c: SPP's **own fully-nodal hourly DA market** does not produce the tail either (0/42, 14/59, 0/68), so a *reduced* zonal split cannot. Cost would be a data intake, a crosswalk, a topology build and a full re-calibration of every SPP gate. |
| **`energy_reserve_coopt`** | **`I` (inert) — DO NOT RE-TEST** | SPP-55: 1 / 0 / 0 hours of C3c overlap. Independently corroborated from a new direction at SPP-29 §1c (the tail is an RT−DA wedge spread across all twelve months, not a concentrated shortage event). SPP's reserve shortage is a 5-minute object. |
| **`negative_renewable_offers`** | **`I` (inert)** | Adjudicated provably inert for SPP; not re-tested at SPP-64 or SPP-29. |
| **`spp_gas_commitment_bridge`** | **`R` (rejected)** | Killed at the rule-29(a) 2023 screen STOP gate (`docs/calibration-log/spp.md` spp-7). |
| **`spp_curtailment_ceiling` as a CF upper bound** | **channel refused; the OBJECT stays `O`** | `FINDING-spp-64` §3: a CF bound removes the price-setter, so it cannot deliver the price half. Card R-bc **replaces** it; the two must never be stacked. |
| **Card R-bd (the tail as congestion rent)** | **CLOSED as chartered** | `FINDING-spp-29` §1, three independent readings. |
| **A price adder / offset / haircut / load proxy for C3c** | **forbidden** | Rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]`. The rule-1 carve-out does not reach it: selecting a multiplier because C3c passes is condition (c)'s named prohibition. |
| **Re-cutting or sweeping `offer_curve_by_group`** | **forbidden in every card above** | Uniform 0.93, one config across all three years, set ex ante and never swept. Re-cutting it against a gate voids the carve-out. |
| **Moving C3c to the DA basis** | **NOT PROPOSED; owner's call alone** | `FINDING-spp-29` §4 reports that SPP would read PASS/FAIL/PASS on the reported-only DA row. That is a measurement of the limitation's size. **Moving a criterion to the basis on which it passes is gate-shopping.** |

---

## 9. GOVERNANCE

- **Rule 32 `[R-SHARD]` (a)** — ZERO LP. No shard launched; no `run_calibration_full.py`,
  `run_calibration.py` or `replay_keeper.py` invoked. All work (scoring, census, differencing, code
  audit) is the parent's under the rule's own clause.
- **Rule 31 `[R-RETAIN]`** — nothing created, nothing deleted, **no `rm` issued**. This lane produced no
  bundle, so **there is no promotion question to put** and nothing is lost when this container is
  reclaimed.
- **Rule 15 `[R-DASHBOARD]`** — no run produced, nothing to register. This document is the record.
- **Rule 28 `[R-MECH-MATRIX]`** — **NO VERDICT MINTED and NO CELL MOVED.** This lane tested no mechanism;
  it measured the keeper, the peer markers, the scorer and the code. The §4 census is a *read* of the
  shards, not an edit.
- **Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — no adder, offset, haircut, proxy or rescaled input is
  proposed anywhere. `offer_curve_by_group` was read (uniform 0.93) and **not** re-cut, swept or
  examined against any gate.
- **Rule 21 `[R-DOF]`** — SPP's ledger is unchanged at **n_entries 3 / n_residual 2**. No mechanism, no
  free parameter.
- **Untouched, deliberately**: `calibration-complete.json`, `keepers/*.json`, `CLAUDE.md`,
  `scripts/lib/holdout_policy.py`, and every gate and docstring named in §5.
- **`[R-HOLDOUT]` was removed 2026-09-09.** No year is protected from being iterated against, so
  **no SPP number in this memo is a certified out-of-sample skill claim.** `CALIBRATED` is a rubric
  determination. Nothing here should be quoted as skill, and a `complete` entry must not imply it.

---

## 10. WHAT THIS DOES NOT ESTABLISH

- It does **not** re-derive the declaration-time verdicts of ERCOT, PJM or NEISO — their artifacts are
  pruned and this clone's history begins 2026-09-07 (§2b). The peer bar is measured on §2a and on the
  two declarations that *are* recoverable.
- The §4 matrix census measures **adjudication breadth**, not each declaring session's own frontier
  test. It is decisive about SPP (9 % vs 43–72 %); it is not a re-audit of anyone else's `frontier`.
- It does **not** measure whether R-bc would close any gate. `FINDING-spp-64` §11's limit stands: the
  structure is absent and its absence is consistent with every open gate; no repair has been built or
  solved.
- It does **not** adjudicate `spp_curtailment_ceiling` (stays `O`), rank SPP-54 against SPP-57, or
  re-read any spent gate.
- **The keeper is untouched and SPP's determination is unchanged: `CALIBRATED`, grade 7 of 8, 0 fails,
  1 ledgered C3c caveat.**

---

## 11. THE QUESTION TO THE OWNER

> **Declare SPP `complete` on keeper `2026-09-10-spp-27-commitment-grain` — yes or no?**
> This lane recommends **YES** (it clears the measured peer bar exactly, and gate (a) is `fail` on the
> marker alone), and recommends **NOT** declaring `frontier` (16 of 173 matrix cells adjudicated against
> 66–131 in every declared ISO). If `complete` is granted, the entry will carry on its determination
> basis: the authorized price-tuning channel, the open one-zone root cause (card R-be), and zero
> out-of-training coverage.
>
> A one-line ruling answers it. If the answer is *yes*, the follow-on question — **admit SPP to
> `GOLDEN_ISOS`?** — is the capx director's, not this lane's, and is not being asked here.

**Next shorthand: spp-32.**
