# PROMPT PACK — SPP, the road to `complete` / `frontier` (issued 2026-09-12, lane SPP-31/32)

One pasteable prompt per remaining card of `docs/handoffs/PLAN-spp-31-complete-frontier-2026-09-12.md`,
updated for what lane SPP-32 settled. **One lever = one lane = one PR** (rule 28(b)).

## Standing facts every prompt below assumes (re-derived 2026-09-12, cite rather than re-quote prose)

- **Keeper 9** `2026-09-10-spp-27-commitment-grain`, bundle `results/calibration/spp27_span`
  (COMMITTED with `hourly/` sidecars), recorded `basis_sha` **`09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8`**.
  **Difference against it; NEVER re-solve it.**
- **Determination** `CALIBRATED`, rubric v3.7, grade 7 of 8, **0 FAILS**, 1 ledgered C3c caveat,
  0 protective, free-class C1 16/16 · 12/12. **DOF ledger n_entries 3 / n_residual 2.**
- **Keeper 2025 baseline (P1)**: COAL_PRB 80.4149 · CC_REGULAR 34.9097 · CT_PEAKER 14.2422 ·
  ST_GAS 12.0198 · COAL_LIGNITE 6.7981 · CC_CHP 1.9343 · CT_CHP 1.1487 · ST_CHP 0.1760 ·
  wind 122.0210 · nuclear 15.7804 · hydro 8.8204 · solar 2.3244 · biomass 0.9490 · OTHER 0.4891 ·
  oil 0.0000 TWh; demand 301.8402 TWh; dump 0.0000 MWh; LW mean price 28.7893; max zonal 73.7731.
- **Slack across the keeper's own span: 0.0000 / 370.1017 / 0.0000 MWh** (2023/2024/2025); the 2024
  event is 2 hours in SPP-South at VOLL $2,000. **A gate demanding slack = 0 is stricter than the
  keeper itself** — SPP-32's G4 made that mistake; do not repeat it.
- **C3a/C3b instrument**: `sum(price*demand)/sum(demand)` on the committed `hourly/system_<y>.parquet`
  (`pass == "P1"`) and monthly-LW NRMSE against `bench/SPP/<y>.json.gz` → `bench.avgLMP.rt_lw_mon`
  reproduce the scorer to 4 dp (control 2025: **28.7893** vs 28.79; NRMSE **0.1638** vs 0.164).
  2025 actual `rt_lw` = 28.60; monthly = [29.96, 29.60, 16.92, 16.20, 28.34, 31.37, 36.39, 33.58,
  35.39, 26.44, 24.58, 28.17]. **Every 2025 C1 row and all of C2 are SKIPPED by the scorer on the
  preliminary EIA-923 vintage**, so on a 2025 screen the load-bearing set is C3a + C3b only.
- **Cost**: SPP solves **499 s for 2023–2025** (~166 s/year). Measured on this session's shards, a
  cold container's whole cycle (clone + `pip install` + fleet build + one-year solve + report) is
  **~20–25 min wall**, of which the solve step was 138–202 s. **One year = one shard = one commit**
  (rule 32(b)).
- **Matrix cells at issue** (`docs/codebase-site/data/mechanism-matrix/SPP.js`):
  `spp_curtailment_ceiling` **O** · `internal_congestion_split` **U** · `ordc_scarcity_overlay` **U** ·
  `unit_outage_short_windows` **O** · `unit_outage_short_windows_gas` **R** ·
  `mustrun_window_commitment_grain` **K** · `energy_reserve_coopt` **I** ·
  `negative_renewable_offers` **I** · `spp_gas_commitment_bridge` **R**.

## NO-BUILD — do not re-open without new evidence meeting rule 28(a)

Sub-zonal topology change for C3c (`FINDING-spp-64` §8: 444 facilities, 115 for 90 % of 2024 rent —
not a 3-zone object; `FINDING-spp-29` §1c: SPP's own fully-nodal DA market produces no tail either) ·
`energy_reserve_coopt` (`I`) · `negative_renewable_offers` (`I`) · `spp_gas_commitment_bridge` (`R`) ·
`unit_outage_short_windows_gas` (`R`, SPP-32) · `spp_curtailment_ceiling` **as a CF upper bound**
(channel refused; the object stays `O`) · card **R-bd** (closed) · any C3c price adder · re-cutting or
sweeping `offer_curve_by_group` · moving C3c to the DA basis (gate-shopping; owner's call, not proposed).

## C3c IS CLOSED AS A WORK ITEM

`FINDING-spp-29` measured it and SPP-32 confirmed the last reachable route is dead. **No prompt below
is chartered against C3c, and none may add it to a gate.**

## HOW TO LAUNCH A SHARD SO IT ACTUALLY WORKS (rule 32(c); learned the hard way at SPP-32)

1. `mcp__Claude_Code_Remote__create_session` with `source_revision` = **the full 40-character SHA of
   your own pushed PRECOMMIT**, never a branch. Give the shard `git rev-parse HEAD` equality as hard
   stop 1, and forbid `git pull` / `git rebase` / any "sync" by name.
2. **The parent CANNOT read a cloud shard's transcript** (no `list_events`; cloud siblings do not
   appear in `ListAgents`). A shard told to "push nothing" strands its numbers. **Require each shard
   to write and push exactly ONE markdown file** `docs/handoffs/SHARDREPORT-<lane>-<arm>-<year>.md`
   and nothing under `results/` — that satisfies rule 29(c) and still reaches the parent.
3. These containers have **no `.venv`**: tell the shard to run
   `python3 -m pip install --ignore-installed PyYAML -r requirements.txt` (the bare
   `-r requirements.txt` fails on Debian's PyYAML) and to use `python3`. The clone is FULL, so
   `hydrate_data.py` is a no-op.
4. The arm mechanism is
   `python3 scripts/replay_keeper.py results/calibration/spp27_span --years <Y> --out-dir results/calibration/<lane>_<arm>_<Y> --set <field>=<json> --note "..."`.
   `--set` is repeatable and the value is JSON.
5. **Add your lane's `.gitignore` pattern (`results/calibration/<lane>_*/`) in the PRECOMMIT commit**,
   before any shard runs. That is what discharges rule 29(c) — never `rm` (rule 31 `[R-RETAIN]`).
6. Forbid by name: `git add -A`/`git add .`, `dashboard_add_run.py`, `build_manifest.py`,
   `build_status.py`, `prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under
   `src/` or `scripts/`, opening a PR, deleting any result.
7. Put this sentence in every shard prompt: *"A shard that stops with a clear report is a SUCCESS; a
   shard that repairs infrastructure is a FAILURE."*

---

# PROMPT 1 — SPP-33: card R-be remnant (day selection). ZERO LP. Run this first; it is free.

```
You are lane SPP-33 (SPP: card R-be's remaining half — DAY SELECTION for the ST_GAS must-run
window). DATA PROFILE: spp.
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-33-day-selection-<suffix>.

## YOUR OBJECT — A PHASE-0 ADJUDICATION. ZERO LP IS A HARD CEILING, NOT A BUDGET.
Keeper 9 (`2026-09-10-spp-27-commitment-grain`, bundle `results/calibration/spp27_span`, COMMITTED)
fixed the must-run window's GRAIN: peak-to-mean 1.2349/1.2159/1.2159 -> 1.0000 and implied starts
2,843/3,002/2,792 -> 288/342/315 against a meter of 647/746/778. What it did NOT fix is which DAYS
the window lands on. `D4.passed` is still False at 4/4/4 per-unit conduct-FAIL rows, and for plants
1230 Cimarron River / 1235 Great Bend / 1271 Coffeyville the day-selection lift over chance is only
~2x. Both SPP-27 and SPP-28 concluded that NO FORECAST-ADMISSIBLE SIGNAL AVAILABLE TO THIS MODEL
REACHES IT.

## THE GATE, AND IT IS THE WHOLE LANE
Enumerate every candidate day-ranking signal for the SPP limb of
`model/commitment.py::caiso_ra_mustoffer_min_gen` and, for each, answer rule 13 [R-MEASURED]'s
forward test: COULD THIS SAME QUANTITY BE PRODUCED FOR A FORWARD YEAR FROM FORWARD DRIVERS, AND
WOULD IT RESPOND TO CHANGED CONDITIONS? Candidates you must consider and adjudicate individually,
not as a block: day-mean gross load (the incumbent), day-PEAK load, NET load (load - wind - solar),
day-mean net load, a temperature/weather driver, an SPP-published commitment or outage instrument,
and anything the SPP data audit (`docs/multi-iso/spp-data-audit.md`) lists that you judge relevant.
**IF THE ADMISSIBLE-AND-REACHING SET IS EMPTY, THE CARD CLOSES WITH NO LP SPENT.** That is the
expected and correct outcome and you should report it as a result, not as a failure to find one.

## WHAT IS ALREADY REFUSED — do not re-propose (rule 28(a) DO-NOT-REDO)
- `mustrun_online_frac_per_year` — registered BACKCAST-ONLY because it reads the solve year's own
  meter. Refused by SPP-27 for exactly that reason.
- A per-plant grain predicate keyed on a threshold — a free parameter (rule 21 [R-DOF]) chosen
  against the statistic it is scored on, which rule 1 [R-STRUCT](c) forbids.
- Special-casing Mooreland 3008 (the one measured two-shifter) — miso-170's own warning: a
  plant-level exclusion "would bury that error inside a membership list".
- A day-PEAK key or a NET-load key BUNDLED with anything else. SPP-27 measured both at phase 0
  (net+peak 0.8368 vs day-mean-gross 0.8238 on the conduct-overlap statistic over 65 plant-years;
  net-vs-gross a WASH at the hour grain, 0.8168 vs 0.8168) and refused them because each bundles a
  second, independently-unmotivated change. If you propose one, it must be ALONE and its motivation
  must be a driver, not that statistic.

## IF (AND ONLY IF) A SIGNAL SURVIVES THE FORWARD TEST
Write a PRECOMMIT that states: the ONE seam (the ranking key, size/level/membership untouched), the
rule-19 [R-ONE-MECH] enumeration (mechanism-16 already floors this class — you RE-KEY its ordering,
you never add a floor beside it), the forward story, the DOF effect (must be ZERO — a new threshold
kills it), and a STRUCTURAL screen gate that reads the D-4 per-unit `measured_zero_share` rows and
NOT any price criterion. Screen year = the year that signal's own measured footprint is largest,
named in the PRECOMMIT before the screen runs. Then shard it (see the pack's launch section).

## HARD CONSTRAINTS
- ZERO LP unless a signal survives the forward test. You are an orchestrator (rule 32 [R-SHARD](a)).
- Touch NONE of: `calibration-complete.json`, `keepers/*.json`, CLAUDE.md, any gate.
- Rule 28(b): you are adjudicating a cell. If the set is empty, ANNOTATE `st_gas_mustrun_per_plant`'s
  cell family in SPP's shard ONLY with the enumeration and the closure; mint a verdict only if you
  actually tested a mechanism.
- Rule 31 [R-RETAIN]: delete nothing, no `rm`.
- C3c is CLOSED; no gate here may read it.
Deliverable: `docs/handoffs/FINDING-spp-33-day-selection-<date>.md` + a `docs/calibration-log/spp.md`
entry. Lead with the verdict. Next shorthand: spp-34.
```

---

# PROMPT 2 — SPP-34: card R-ba (merit-order inversion). ZERO-LP phase 0 first; a screen only if it survives.

```
You are lane SPP-34 (SPP: card R-ba, the ST_GAS / CT_PEAKER merit-order inversion). DATA PROFILE: spp.
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-34-merit-inversion-<suffix>.

## YOUR OBJECT
Keeper 9's own committed dispatch shows ST_GAS running at ~12.9 % CF BELOW CT_PEAKER at ~19.0 % —
the wrong way round. Re-derive that from `results/calibration/spp27_span/hourly/` yourself; do not
take it from prose. The bound `FINDING-spp-64` §6 puts on the card is REAL and you must carry it:
every SPP thermal class clears within a ~$5 band (2025 p50: COAL_PRB 33.67 · CC_REGULAR 33.90 ·
CT_PEAKER 35.22 · ST_GAS 32.51 · COAL_LIGNITE 34.55), so correcting the ORDER re-ranks classes
inside a band that should be tens of dollars wide. **This card cannot by itself produce a price
distribution spanning $1,130 and must not be sold as if it could.**

## PHASE 0 — ZERO LP, and it may kill the card
Measure, from SPP's OWN CAMPD record (`data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` over SPP's
states) and eGRID: the per-unit LOADED heat rate of SPP's ST_GAS and CT_PEAKER fleets, and the
implied marginal-cost ordering of the two classes at the keeper's own delivered gas price. Compare
against the heat rates the model actually assigns (rebuild the fleet with
`scripts/lib/bundle_fleet.reconstruct_bundle_fleet` against `results/calibration/spp27_span`; NOTE
the known defect — that function is ORDER-DEPENDENT ACROSS YEARS WITHIN A PROCESS for SPP, so build
one year per process and say which history you used).
**THE GATE:** does the MEASURED ordering differ from the MODEL's, in the direction the CF inversion
implies? If the measured heat rates already order the two classes the way the model does, the
inversion is not a heat-rate object and this card CLOSES at zero LP — report that and stop.

## IF IT SURVIVES
- **ONE seam**: the per-plant measured loaded heat rate for SPP's ST_GAS and CT_PEAKER units — the
  same construction PJM already carries in its DOF ledger ("Measured loaded CT heat rates (CAMPD,
  per plant)"). **NOT `offer_curve_by_group`**, which is the authorized LEVEL channel and must stay
  byte-identical at a uniform 0.93, un-re-cut and un-swept (rule 1 [R-STRUCT] carve-out condition c).
- **Rule 19 [R-ONE-MECH]**: enumerate what already prices these two classes — the 0.93 band
  multipliers, the flat -$26 PTC wind offer, and (for ST_GAS) mechanism-16's must-run floor. A
  measured heat rate REPLACES the estimated one; it never stacks a second adder beside it.
- **Rule 13 forward story**: a measured per-plant loaded heat rate regenerates for a forward year
  from the then-current CAMPD vintage.
- **Rule 21 [R-DOF]**: ZERO if measured per-plant; a new residual entry if fitted. MEASURED ONLY —
  a fitted heat rate is refused outright.
- **Rule 28(d)**: PJM's verdict fills no SPP cell. Derive SPP's numbers from SPP's own data.
- **Screen gate (STRUCTURAL, STOP-only, never reads a residual)**: the two classes' CF ordering moves
  toward the measured ordering; the footprint is confined to ST_GAS and CT_PEAKER; energy conserved;
  no non-target load-bearing criterion flips PASS -> FAIL. **Do NOT gate on C3a/C3b improving, and
  do NOT gate on C3c at all.** Do NOT write "slack must be 0.0000" — the keeper's own 2024 carries
  370.1017 MWh and SPP-32's G4 made exactly that mistake; if you gate slack, gate it against the
  keeper's own per-year value.
- Screen year: the year the measured heat-rate discrepancy is largest, NAMED IN THE PRECOMMIT before
  the screen runs. Then the full `--year 2023 2024 2025` span only if the screen clears.

## CONTROL AND DRIFT
Control = keeper 9's COMMITTED bundle, differenced, NEVER re-solved (rule 29(b) form 4). Run and
record the G-DRIFT audit in the PRECOMMIT before any arm:
`git diff 09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
and classify EVERY hunk INERT-with-reason or LIVE. Only a LIVE hunk earns a control solve.

## HARD CONSTRAINTS
Rule 32 [R-SHARD](a): the parent runs no LP. Rule 31: delete nothing. Add
`results/calibration/spp34_*/` to `.gitignore` in the PRECOMMIT commit. Touch no marker, no keeper
shard, no gate, not CLAUDE.md. Rule 28(b): move the cell you test, in SPP's shard only.
Deliverable: PRECOMMIT + `docs/RESULT-spp-34-*.md` + a `docs/calibration-log/spp.md` entry.
Next shorthand: spp-35.
```

---

# PROMPT 3 — SPP-35: card R-bc, PRICE-FORMING curtailment. The one card with a real structural object.

```
You are lane SPP-35 (SPP: card R-bc — price-forming wind curtailment as an LP constraint whose dual
reaches the zonal price). DATA PROFILE: spp.
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-35-priceforming-curtailment-<suffix>.

## YOUR OBJECT — AND ITS CHARTER BOUNDARY, WHICH IS BINDING
Rule 14 [R-ACCURATE] owes SPP's model ~11.8-13.0 TWh/yr of wind curtailment it does not represent.
The refuted channel (`spp_curtailment_ceiling`, cell `O`) is a CF UPPER BOUND, and a bound removes
the price-setter: when it binds, wind simply is not there, so nothing is marginal at wind's offer.
The object is a REDUCED-FORM CURTAILMENT THAT ENTERS AS AN LP CONSTRAINT WHOSE DUAL REACHES THE
ZONAL PRICE — the same standing the transmission limit already has — so that when it binds, wind IS
marginal, the price goes to its offer, and the curtailment and the negative-price hour are ONE EVENT
as they are in the real market. It REPLACES `spp_curtailment_ceiling`; the two must never be stacked.

> **CHARTER AGAINST THE NEGATIVE TAIL AND THE WIND VOLUME ONLY. THIS IS NOT NEGOTIABLE.**
> `FINDING-spp-29` §2 shows the over-delivered wind is ABSENT from the upper-tail hours
> (+0.18 / -1.20 / +0.31 GW) and §3 shows the upper tail survives perfect quantities. A lane that
> charters R-bc against C3c WILL FAIL, and it will fail for reasons that have nothing to do with
> R-bc's merits. The words "and the upper tail" must never be added to your success test.

## RE-DERIVE THESE BEFORE YOU DESIGN ANYTHING (zero LP, from committed artifacts)
Keeper 9's committed `hourly/system_<y>.parquet` (`pass == "P1"`), 2023/2024/2025:
- hours with min-zonal price < 0: **238 / 225 / 213**, against actual RT < 0 of **992 / 1172 / 1018**
  (`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`).
- model mean |N-S| zonal spread: **0.5759 / 1.1834 / 1.5072** $/MWh, against a measured hub spread of
  ~12.13 / 17.23 / 15.18.
- measured curtailment (`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`, MMU ASOM, metered basis):
  avg hourly **1,097 / 1,483 / 1,382 MW**; curtailed **9,609.7 / 12,991.1 / 12,106.3 GWh**; share
  **8.49 / 10.56 / 9.90 %**.
Reproduce every one of these yourself. If any disagrees, STOP and report the disagreement first.

## THE DESIGN, AND ITS THREE KILL CONDITIONS
- **ONE seam**: a NEW constraint row in the LP matrix builder (`model/dispatch.py`), vectorized
  (rule 2 [R-VECTOR]: no Python loop over hours), with the wind decision variables on the LHS.
  NOT an offer edit, NOT a bound, NOT a netting. `spp_curtailment_ceiling` must be OFF in the arm.
- **Rule 19 [R-ONE-MECH] enumeration**: nothing else prices SPP wind. `pmin_mw`, `min_run_hours`,
  `min_down_hours` and `startup_cost_per_mw` are 0 on EVERY SPP fossil unit (SPP-44 / SPP-63,
  reproduced at SPP-64 — reproduce it again); the only live channels are `offer_curve_by_group` at a
  uniform 0.93 and the flat -$26 PTC offer. Your mechanism REPLACES the ceiling. Say so in the
  PRECOMMIT and prove the two cannot both be armed.
- **Rule 13 [R-MEASURED] forward story — KILL CONDITION 1.** The constraint's right-hand side must
  regenerate for a FORWARD year from FORWARD drivers (installed wind by zone, the zonal shape, the
  corridor rating) and must respond to changed conditions — more wind, more binding. **It must NOT
  be parameterized from the solve year's own metered curtailment volume**, which would be a
  backcast-only overlay and would make the mechanism unusable in the forecast. If your construction
  cannot pass this test, the design dies here.
- **Rule 21 [R-DOF] — KILL CONDITION 2, and this is the card's real risk.** A reduced form with a
  FITTED depth is a new residual-identified free parameter and takes SPP's ledger from 3/2 to 4/3.
  **State the identification source in the PRECOMMIT BEFORE the solve.** A construction identified
  from SPP's own published flowgate limits (`data/raw/spp-binding-constraints/Flowgates.csv`,
  `rtbm_bc_corridor_limits_2026.parquet`) is admissible. One identified from the negative-hour count,
  the curtailment residual, or any gate is NOT, and is refused under rule 1 [R-STRUCT](c).
- **KILL CONDITION 3**: if the constraint's dual does not actually reach the zonal energy-balance
  price — verify this on a trivial case first (1 zone, 1 wind unit, 24 hours; CLAUDE.md Testing
  Pattern) — the mechanism is the ceiling again under another name and dies.

## THE SCREEN GATE — pre-registered, STRUCTURAL, STOP-only, FOUR LEGS THAT MUST MOVE TOGETHER
1. wind volume DOWN toward the measured level;
2. hours with min-zonal price < 0 UP from 213 toward ~1,018 (2025 basis; use the screen year's own pair);
3. congestion rent / mean |N-S| UP from ~1.51 toward the measured ~15.18;
4. C3b NRMSE DOWN from the control's own value for that year.
**A variant that moves ONLY the volume is the arm SPP-63 already killed.** None of these four is
C3c, and C3c must not appear in the gate in either direction. Add a confinement leg (the response is
confined to wind and to the zones the constraint names) and an identity leg (energy conserved, dump
behaviour explained) — but **do NOT write "slack must be 0.0000"**: the keeper's own span carries
0 / 370.1017 / 0 MWh and SPP-32's G4 was mis-set exactly that way. Gate slack against the keeper's
own per-year value or not at all.

## SCREEN YEAR — named in the PRECOMMIT, before the screen runs
The year the mechanism's OWN measured footprint is largest, which on the metered basis is **2024**
(1,483 MW avg hourly / 12,991.1 GWh / 10.56 %, against 2023's 1,097 / 9,609.7 / 8.49 % and 2025's
1,382 / 12,106.3 / 9.90 %). Confirm it from the CSV yourself and declare it; if your construction's
own footprint statistic disagrees with the metered one, use YOUR mechanism's statistic and say why.
**Never the year with the biggest residual** (rule 29 [R-SCREEN](1)).

## CONTROL, DRIFT AND SHARDS
Control = keeper 9's COMMITTED bundle differenced, NEVER re-solved (rule 29(b) form 4). Record the
G-DRIFT audit in the PRECOMMIT before any arm:
`git diff 09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`,
classifying EVERY hunk INERT-with-reason or LIVE. **Your own new constraint is a LIVE change to
`src/`, so the shards CANNOT use `replay_keeper.py --set` against a keeper that predates your field
unless the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its default in the SAME commit
(the nyiso-119 / caiso-186 discipline).** Do that, and verify the keeper's cache key is byte-stable
before you launch anything. Then: phase 0 in the parent (0 LP) -> ONE screen shard -> the full span
as three one-year shards ONLY if the screen clears. Add `results/calibration/spp35_*/` to
`.gitignore` in the PRECOMMIT commit. Follow the pack's shard-launch section exactly.

## HARD CONSTRAINTS
Rule 32 [R-SHARD](a): the parent never solves. Rule 28(c): a NEW ScenarioConfig field needs its
matrix ROW in `mechanism-matrix.js` plus a cell line in EVERY ISO shard, in the same PR. Rule 25
[R-ISO-SCOPE]: SPP only; every other ISO byte-identical. Rule 31: delete nothing, no `rm`. Rule 1 /
13: `offer_curve_by_group` stays byte-identical at a uniform 0.93 — not re-cut, not swept, not
examined against any gate; no adder, offset, haircut, proxy or rescaled input. Touch no marker file.
Deliverable: a DESIGN doc, a PRECOMMIT, then `docs/RESULT-spp-35-*.md` + a
`docs/calibration-log/spp.md` entry. Next shorthand: spp-36.
```

---

# PROMPT 4 — SPP-36: arm A to the full span. **OWNER-GATED — issue only if the owner rules YES on SPP-32's promotion question.**

```
You are lane SPP-36 (SPP: take SPP-32 arm A — `unit_outage_short_windows` — to the full 2023-2025
span). DATA PROFILE: spp. **DO NOT START unless the owner has ruled YES on the promotion question in
`docs/RESULT-spp-32-shortwindow-screen-2026-09-12.md` §7. Quote the ruling verbatim in your PRECOMMIT.**
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-36-shortwindow-span-<suffix>.

## WHAT YOU ARE DOING AND WHY IT IS NOT A RE-SCREEN
SPP-32 screened `unit_outage_short_windows=true` (COAL scope) on 2025 and it cleared G1 direction,
G2 confinement, G3 magnitude and G5 no-non-target-flip. It was STOPPED by G4, which demanded
`slack == 0.0000` — a gate SPP-32 itself showed to be mis-set, because keeper 9's OWN committed span
carries 0.0000 / **370.1017** / 0.0000 MWh of slack and the 2024 event (2 hours, SPP-South, VOLL) is
LARGER than arm A's 240.5966 MWh. The owner's ruling, not this lane's judgement, is what re-opens it.
**Do not re-litigate the screen and do not re-run 2025 as a screen** — go straight to the span.

## THE ARM — ONE FIELD, ZERO CODE, ZERO FREE PARAMETERS
`--set unit_outage_short_windows=true` on keeper 9's recipe. `unit_outage_short_windows_gas` STAYS
**FALSE**: it is cell `R` for SPP (SPP-32 killed it at slack 10,911.0219 MWh and two load-bearing
flips), and re-arming it is refused under rule 28(a) without new evidence.
- Extract: `data/raw/campd-unit-outages-short-SPP.csv`, COMMITTED, 620 windows, 24 plants, 39 units,
  620/620 rows `plant_group == COAL`. **Do NOT re-derive it** (rule 23 [R-FROZEN-DERIVE]: a
  measured-behaviour artifact re-derives only when its SOURCE DATA updates).
- DOF: ledger stays **n_entries 3 / n_residual 2**. `offer_curve_by_group` byte-identical at 0.93.
- Rule 19: disjoint from the >=5-day overlay (`outage_source="historic"`, already on) by DURATION.

## HOW TO RUN IT
Three shards, ONE YEAR EACH (rule 32 [R-SHARD](b); ~166 s of LP per year, ~20-25 min wall per cold
container), each `python3 scripts/replay_keeper.py results/calibration/spp27_span --years <Y>
--out-dir results/calibration/spp36_<Y> --set unit_outage_short_windows=true --note "..."`, then the
PARENT composes the three into ONE bundle and registers ONE run across `--year 2023 2024 2025`
(rule 16 [R-ALLYEARS]; a single-year SPP keeper is refused). Per-year shard dirs stay OUT of `main`
(rule 32(d)) — add `results/calibration/spp36_*/` to `.gitignore` in the PRECOMMIT commit; the
COMPOSITE is what gets registered. Control = keeper 9's committed bundle, differenced, never
re-solved; record the G-DRIFT audit first.

## WHAT THE PARENT OWES AFTER THE SHARDS LAND (rule 32(d), all in the parent, once)
1. Compose, then `scripts/stamp_config_partition.py --check` if applicable.
2. `python3 scripts/calibration_verdict.py --run-id <new id>` — the FULL scored verdict, all three
   years. **Report it whatever it says.** Arm A degraded C3a +0.66 % -> +5.15 % and C3b 0.1638 ->
   0.1878 on 2025 alone; 2023 and 2024 are unmeasured and may go either way.
3. `scripts/legitimacy_diagnostics.py` and the D-1/D-2/D-4 rows.
4. Register on the dashboard (rule 15 [R-DASHBOARD]) with `hourly/` sidecars — a run is not done
   until its bundle and dashboard files are committed and pushed IN THIS SESSION.
5. Rule 28(b): move `unit_outage_short_windows` in SPP's shard from `O` to `K` **only if the owner
   promotes it**, else to `R` or leave `O` with the span evidence annotated. **Promotion is the
   owner's act — recommend, do not act** (rule 31 [R-RETAIN]).
6. Put the promotion question explicitly in your final report, and say plainly that the bundles are
   on local disk and will not survive the container.

## HARD CONSTRAINTS
Rule 32(a): the parent never solves. Rule 31: delete nothing, no `rm`. Do NOT touch
`calibration-complete.json`. Do NOT arm the gas scope. Do NOT gate anything on C3c. Deliverable:
PRECOMMIT + `docs/RESULT-spp-36-*.md` + registration + a `docs/calibration-log/spp.md` entry.
Next shorthand: spp-37.
```

---

# PROMPT 5 — SPP-37: execute the `complete` declaration. **OWNER-GATED — issue only on an explicit YES.**

```
You are lane SPP-37 (SPP: execute the owner's `complete` declaration). DATA PROFILE: code.
**DO NOT START without an explicit owner ruling. Quote it verbatim in the entry you write.
Declaring `complete` is an OWNER ACT; this lane only executes one that has already been made.**
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-37-complete-<suffix>.
ZERO LP.

## READ FIRST
`docs/handoffs/PLAN-spp-31-complete-frontier-2026-09-12.md` — the decision memo, especially §2 (the
peer table), §3c (what the entry must carry) and §5 (what the marker actually does at HEAD).

## WHAT TO WRITE — one entry in `frontend/data/backcast/calibration-complete.json` -> `complete.SPP`
Mirror the key set the five existing entries carry; read NYISO's and CAISO's as worked examples
before writing a line. Required keys: `declared` · `keeper` · `by` (the owner's ruling VERBATIM,
with the session) · `determination` · `keeper_at_declaration` · `tier_authorized` · `locked_test` ·
`freeze_interaction` · `keeper_rekey_policy`. **`frontier_basis`: OMIT IT.** SPP does not hold
`frontier` and PLAN §4 refuses it on a measurement (16 of 173 applicable matrix cells adjudicated,
9 %, against 43-72 % in every declared ISO).

**RE-VERIFY, DO NOT COPY, before you write `determination`:**
`python3 scripts/calibration_verdict.py --run-id 2026-09-10-spp-27-commitment-grain` — it must read
`CALIBRATED`, grade 7 of 8, 0 fails, 1 ledgered C3c caveat, 0 protective, free-class C1 16/16 · 12/12.
If it does not, STOP and report; the marker may not assert an unscored determination (D-5(b)).

**THREE THINGS THE DETERMINATION BASIS MUST STATE AT FULL MAGNITUDE** (PLAN §3c) — a `complete`
entry that omits them is hiding what the peer table shows:
1. SPP is the ONLY ISO whose keeper declares `authorized_price_tuning` (the rules 1/13 carve-out
   channel, uniform 0.93 on the ten fossil classes, one config across all three years, set ex ante
   in `PRECOMMIT-spp-52a-2026-09-09.md` and never swept) — and **C3a and C3b PASS only after it**
   (spp-20: C3a FAIL 2025 +10.3 % -> PASS; C3b FAIL 0.204 -> PASS).
2. The ONE-ZONE root cause is open and card R-be is carried on the keeper (`FINDING-spp-64` §5: the
   LP holds ONE internal constraint against SPP's own 735/723; zonal prices identical in
   87.4/86.1/76.8 % of hours; 5-13 % of measured congestion rent reproduced).
3. SPP has **ZERO out-of-training coverage** — the only ISO in the program with none — and
   `CALIBRATED` is a RUBRIC DETERMINATION, **not** a certified out-of-sample skill claim
   (`[R-HOLDOUT]` was removed 2026-09-09; no year is protected from having been iterated against).

**`tier_authorized` / `locked_test` / `freeze_interaction` must be written to HEAD's reality, not to
the older entries' text.** At HEAD every holdout gate is GONE and `holdout-freeze.json` DOES NOT
EXIST — PLAN §5 carries the file:line evidence. Do not copy NYISO's freeze prose forward as if the
freeze were live. What the marker still does at HEAD, and all it does: `audit_keepers` M1 currency +
determination re-verification; `derive_plant_emissions_v2.py --holdout-intake SPP` (the intake-log
ISO vocabulary at line 244 EXCLUDES SPP, so the marker is SPP's only route to 2022/2026 emission
rows); and the forecast §2.1b gate (a).

## THE REST OF THE PROCEDURE
- `frontend/data/forecast/program-status.json` -> `isos.SPP.gate.a_keeper_marker`: flip `fail` ->
  `pass` and rewrite the detail to say the marker now exists. **The file is stored
  `ensure_ascii=True`** — a re-serialization with `ensure_ascii=False` rewrites hundreds of lines
  across every ISO (the SPP-64 trap, hit and avoided at spp-28). Verify the committed diff is
  SPP-only. Then `python3 scripts/check_gate_a_provenance.py`.
- **Do NOT add SPP to `GOLDEN_ISOS`** (`scripts/ff_readiness_battery.py:102`). That is the capx
  director's call, not this lane's, and it is not implied by the marker.
- `python3 scripts/audit_keepers.py --iso SPP --check` must pass (M1 now covers SPP).
- `python3 scripts/build_status.py --iso SPP` and commit `status/SPP.js`.
- Rule 28: re-stamp SPP's matrix shard `gates:` line if the declaration changes what it asserts.
- **Do NOT touch `keepers/SPP.json`'s keeper id** (no promotion is happening here) and do NOT add a
  `frontier` block to it.
Deliverable: the marker entry + the board flip + a `docs/calibration-log/spp.md` entry that quotes
the ruling verbatim. Next shorthand: spp-38.
```

---

# PROMPT 6 — SPP-38 / R-bg: the stale holdout docstrings. ZERO LP, docs-only, OWNER-OPTIONAL.

```
You are lane SPP-38 (repo-wide: card R-bg — the stale `[R-HOLDOUT]` docstrings). DATA PROFILE: code.
Base: latest origin/main. Record `git rev-parse HEAD`. Branch: claude/spp-38-holdout-docstrings-<suffix>.
ZERO LP. **DOCS AND COMMENTS ONLY — you may not change one line of executable code.**

## THE PROBLEM, ALREADY MEASURED
`[R-HOLDOUT]` and every enforcing gate were removed 2026-09-09 and the CODE AGREES WITH CLAUDE.md.
What is stale is a set of docstrings and comments that still name gates which no longer exist — and
they mislead: lane SPP-31's own handoff was built on them and reached the wrong conclusion about
what SPP may spend. `docs/handoffs/PLAN-spp-31-complete-frontier-2026-09-12.md` §5 carries the
file:line table. Re-verify every row yourself before touching anything:
- no `def enforce_holdout_year_gate` anywhere; the name survives only in docstrings at
  `scripts/run_calibration.py:15`, `scripts/knob_jacobian.py:10,230`,
  `scripts/data/derive_actual_tail.py:72`, `scripts/data/fetch_campd_unit_level.py:71`,
  `scripts/lib/invariant_ledger.py:20`;
- `--holdout-authorized` is registered nowhere and is in neither runner's `--help`;
- `scripts/dashboard_add_run.py:31` names `enforce_registration_marker_gate`, which does not exist;
- `_year_emittable` returns True unconditionally (`derive_actual_tail.py:103-111`,
  `derive_actual_amplitude.py:74-82`);
- `frontend/data/backcast/holdout-freeze.json` does not exist;
- `HOLDOUT_CALIBRATION_YEARS` / `HOLDOUT_MARKER_FILE` (`run_calibration_full.py:8690-8691`) are
  defined and referenced nowhere;
- `audit_keepers.py` H1 has no failure emitter (`"H1"` appears only at lines 992/996, both in the
  pass branch).

## WHAT TO DO
Rewrite each stale comment/docstring to describe HEAD's actual behaviour, citing the removal
(2026-09-09 owner instruction; `docs/governance/rule-history.md` §18). Where a constant or a named
seam is dead but deliberately kept (`_year_emittable`, `tier_for_year`), say so explicitly and say
WHY it survives, so the next reader does not "restore" a gate. Where a constant is simply dead
(`HOLDOUT_CALIBRATION_YEARS`, `HOLDOUT_MARKER_FILE`, the H1 branch), **propose** deletion under rule
26 [R-DELETE] ("a deprecated parameter that still parses is a re-armable answer key") in your
findings doc — **do not delete it yourself**; a dead constant's removal touches executable code and
is the owner's call.

## HARD CONSTRAINTS
- **Do NOT edit CLAUDE.md** — it is already correct.
- **Do NOT add, remove, weaken or restore any gate.** No behavioural change of any kind: prove it
  with `git diff` showing only comment/docstring lines, and run the test suite to confirm.
- Rule 27 [R-PUSH]: several of these files are >=300 lines. Edit locally, push the exact on-disk
  bytes, and verify the pushed blob (line count + hash) immediately after each push.
- Rule 28: no mechanism is tested; mint no verdict, move no cell.
- Rule 31: delete nothing on disk, no `rm`.
Deliverable: `docs/handoffs/FINDING-spp-38-holdout-docstrings-<date>.md` (the verified table, the
edits made, and the dead-code deletions PROPOSED but not made) + the doc edits. This is repo-wide
housekeeping, not an SPP lane — log it in `docs/calibration-log/governance.md`, not `spp.md`.
```

---

## Sequencing

| order | lane | LP | why here |
|---|---|---|---|
| 1 | **SPP-33** (R-be day selection) | **0** | free, and both predecessors expect it to CLOSE at phase 0 |
| 2 | **SPP-34** (R-ba merit inversion) | 0 phase 0, then 1 screen + 3 span if it survives | zero-LP census can kill it; bounded upside (~$5 band) |
| 3 | **SPP-35** (R-bc price-forming curtailment) | 1 screen + 3 span, after a build | the only card with a real structural object; needs new LP code, so it is the long pole |
| — | **SPP-36** (arm A full span) | 3 shards | **owner-gated** on SPP-32 §7 |
| — | **SPP-37** (`complete`) | 0 | **owner-gated**; independent of all of the above |
| — | **SPP-38** (R-bg docstrings) | 0 | owner-optional housekeeping; run any time |

SPP-33 and SPP-34's phase 0 are both zero-LP and independent, so they can run **concurrently** with
SPP-35's design (rule 12 [R-PARALLEL]). **SPP-30** (SPP's out-of-training price coverage) is chartered
separately and runs independently of every lane here — do not duplicate it, and do not wait for it.
