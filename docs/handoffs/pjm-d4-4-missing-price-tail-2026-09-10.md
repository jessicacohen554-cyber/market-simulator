# HANDOFF — pjm-d4-4: the forced-outage composition gap

Written by session `pjm-d4-3` (2026-09-10), superseding this file's first draft (which named the
wrong lever space — see below). Paste the block below whole.

**Why this is a handoff and not launched shards.** The arm is now fully specified, but it is not
shardable today: the gas sub-5-day outage family **does not exist on disk**. `campd-unit-outages-
PJM.csv` (10,670 rows) carries zero rows under 5 days — they are filtered at derive time — and
`campd-unit-outages-short-PJM.csv` is 934 rows, 100 % COAL. So the arm needs a derive-script change,
a re-derived committed artifact, a new gated field, a matrix row and a cache-key registration before
any `--set` exists to shard. It also carries a real risk of being an order of magnitude too small,
which is why the prompt's kill gate runs before the build, not after.

**Correction to this file's first draft.** It named `unit_outage_lp_capacity_basis`,
`unit_outage_extract_basis_share`, `unit_outage_per_unit_clip` and `historic_outage_overlay` as the
candidate arms on the strength of their `U` cells. All three `unit_outage_*` fields were then read:
they change the derate **denominator**, i.e. they are LEVEL levers on the envelope, and none reaches
the composition defect. That draft's lever space was wrong and is replaced here.

Evidence base: `docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md` (the price-side measurement),
`docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md` (the session), and pjm-162's committed
`_pjm162_split_derivability.json` / `_pjm162_split_threshold.json` (the outage stratification).

---

```
PJM: the forced-outage composition gap — session pjm-d4-4

DATA PROFILE: pjm. MODEL: Opus or Fable (rule 27 [R-PUSH] — this lane writes src/ and scripts/).
SCOPE: PJM ONLY. BASE: origin/main. `git checkout -b claude/pjm-d4-4`.
Do NOT open a PR unless the owner asks. Never write another ISO's keeper/matrix/status/log.

READ IN FULL FIRST:
  docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md          (the price-side measurement)
  results/calibration/FINDING-pjm162-outage-envelope-basis-closure-2026-08-15.md   (sections 3, 4, 5 — YOUR EVIDENCE BASE)
  results/calibration/FINDING-pjm161-outage-inversion-and-da-virtual-energy-2026-08-14.md (7, 7.5)
  docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md             (section 6 = the DO-NOT-REDO record)
  src/market_sim/data/outages.py  lines 269, 795-850, 1180-1215 (UNIT_OUTAGE_MIN_DAYS and the short-window overlay)
  docs/codebase-site/data/mechanism-matrix/PJM.js               (the outage family)

## THE STATE YOU INHERIT
PJM's TRAINING span is CALIBRATED, zero caveats, empty basis, keeper 2026-09-10-pjm-d4-2-stgas
(+ -touchpoint, folded). DO NOT DISTURB IT (rule 30(c)).
HOLDOUT 2020-2022 reads NOT-YET on C1 fuel-mix, C3a mean LMP, C3b price shape.

## THE CHAIN, MEASURED END TO END (all zero LP, all from committed artifacts)
1. **2022's C3a failure IS a missing price tail.** 92 actual hours RT>$200, model forms **0**; they
   carry $5.78/MWh of the annual mean against a $5.48/MWh miss = **105 %**. The 26 hours >$500 carry
   $4.52 alone. 2025 69 %, 2024 52 %. **2020 is the OPPOSITE defect (+21.4 % OVER) — not this card.**
2. **The reserve co-opt that should form the tail is INERT.** reserve_family_2022.parquet: dual
   exactly **0.00 in 8,760 of 8,760 hours**, both families, held == requirement to the MW, zero
   shortfall — including all 92 tail hours. Same 2021 and 2023.
3. **The model out-generates the meter by +9.7 GW at RT>$200 and +11.1 GW at RT>$500** (vs +4.3 GW
   all-hours). It has thermal running that the meter says was not.
4. **Because its outage envelope has the wrong TIME SHAPE.** From pjm-162's committed
   _pjm162_split_derivability.json, annual-mean MW:

   | year | model <=7d | model >7d | PJM pub FORCED | PJM pub PLANNED+MAINT | **forced GAP** | model %forced | pub %forced |
   |---|---|---|---|---|---|---|---|
   | 2022 | 2,333 | 31,780 | 9,332 | 25,802 | **+6,999** | 6.8 % | 26.6 % |
   | 2023 | 2,147 | 35,151 | 7,653 | 25,645 | **+5,506** | 5.8 % | 23.0 % |
   | 2024 | 2,280 | 30,350 | 7,698 | 25,275 | **+5,418** | 7.0 % | 23.3 % |
   | 2025 | 1,956 | 28,594 | 10,531 | 25,339 | **+8,575** | 6.4 % | 29.4 % |

   Planned outages do not correlate with net load; forced ones spike in events. A 94 %-planned
   envelope cannot tighten the stack in the 92 hours that matter — hence (2) and (3).

## THE FREE-PARAMETER BLOCKER THAT STOPPED pjm-162 IS CLOSED
pjm-162 declined this route partly because "any specific [duration] cut is a **free parameter**
requiring a DOF-ledger entry (rule 20) and an external definitional identification" — it swept the
CUMULATIVE family and found corr positive across 2-10 days with no optimum. **The PER-STRATUM sign
is a different statistic and it is categorical.** corr_vs_published_FORCED, from the same committed
JSON:

  | stratum | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|
  | 0-3d  | **+0.164** | **+0.234** | **+0.398** | **+0.222** |
  | 3-7d  | **+0.321** | **+0.126** | **+0.221** | **+0.089** |
  | 7-21d | **-0.213** | **-0.035** | **-0.087** | **-0.477** |
  | 21-60d| -0.654 | -0.226 | -0.563 | -0.468 |
  | >60d  | -0.704 | -0.211 | -0.647 | -0.435 |

**The sign flips at exactly 7 days in all four years — 8 positive cells, 12 negative, zero
exceptions.** That is a data-identified boundary, not a swept one: no value was chosen to make a
criterion pass, and the classification is invariant to any cut inside a stratum. DECLARE IT THAT WAY
IN THE PRECOMMIT and show the table; do NOT re-sweep it. (If you also find an external definitional
anchor in PJM Manual 22's outage taxonomy, cite it as corroboration — but the sign flip stands alone
and is stronger.)

## THE DEFECT IN CODE — one line, and it is the whole story
`src/market_sim/data/outages.py`:
  - `UNIT_OUTAGE_MIN_DAYS = 5` (line 269), and line 846 `df = df[df.duration_days >= UNIT_OUTAGE_MIN_DAYS]`
    -> **every window shorter than 5 days is DISCARDED.**
  - The sub-floor companion `unit_outage_short_windows` (**armed `true` in the keeper**) recovers
    them — but re-filters to `plant_group == "COAL"` (line ~1201) and its derive
    (`scripts/data/derive_campd_unit_outages.py --short-windows`) emits **coal only**:
    `data/raw/campd-unit-outages-short-PJM.csv` is **934 rows, 100 % COAL** (verified).
  - The main extract `campd-unit-outages-PJM.csv` (10,670 rows) has **zero rows under 5 days** —
    already filtered at derive time. So the gas sub-5-day family **does not exist on disk**.

**So the 0-3d stratum — the highest-correlated forced carrier (+0.164/+0.234/+0.398/+0.222) with the
largest event spike (4.35-9.88x) — is captured for COAL and thrown away for CC_REGULAR, CT_PEAKER,
ST_GAS and the CHP classes.** CC_REGULAR is the class that over-generates by +11.1 GW in the tail.

## THE ARM
**Extend the short-window outage overlay from COAL-only to the gas classes**, by re-deriving
`campd-unit-outages-short-PJM.csv` with a gas-appropriate detector and widening the consumer's
`plant_group` filter behind a new gated, default-off boolean.

Admissibility, to be argued in the PRECOMMIT before any solve:
  - rule 13 [R-MEASURED]: CAMPD unit outage windows are the measured-input class CLAUDE.md names as
    admissible by construction, and they regenerate forward from EFOR. The same detector runs on any
    vintage.
  - rule 19 [R-ONE-MECH]: the two overlays are disjoint by construction (`<MIN_DAYS` vs `>=`), so
    widening scope REPLACES a discard; it does not stack.
  - rule 14 [R-ACCURATE]: it swaps a discard for measured data.
  - rule 1 [R-STRUCT]: identified from PJM's published forced/planned composition and the 7-day sign
    flip. **Never gate on C3a/C3b/C1** — report them at full magnitude, both directions. Gate on the
    reserve dual becoming non-zero in the target hours and the model-minus-meter thermal gap closing
    from +11.1 GW.
  - rules 21/24: one new gated boolean + its matrix row (rule 28(c)) + cache-key registration IN THE
    SAME COMMIT (the nyiso-119/caiso-186 discipline — `check_cache_key_registration` enforces it).

**THE HARD PART, named so you do not walk into it.** The coal detector's identification guards exist
to keep **economic idling** out: coal-only detector, unit annual CF >= 0.55, revealed-availability
in-merit filter. **Gas CCs and CTs cycle economically by design**, so that detector applied naively
to gas will classify normal cycling as outage — the exact failure mode `ST_GAS_PEAKER_PLANTS` exists
to prevent and that pjm-d4-1 and pjm-d4-2 each spent a whole session on. Your detector must be
identified on gas conduct, ex ante, and declared before you look at any result.

## KILL GATE — RUN THIS FIRST, AT ZERO LP, BEFORE BUILDING THE DERIVE
The forced gap is **5.4-8.6 GW** (table above). The coal short-window file contributes only
**103-188 MW** of annual mean. Gas carries ~2x coal's window count in the adjacent 5-7d band
(1,070 gas rows vs 510 coal, 2020-2025), so a naive scaling says the gas sub-5-day family may
deliver only **hundreds of MW against a 5.4-8.6 GW gap — an order of magnitude short.**

**So: detect the gas sub-5-day windows FIRST (derive only, no config change, no solve) and measure
their annual-mean MW.** Pre-register the bar in the PRECOMMIT. If the recovered family is not a
material fraction of the forced gap, **the arm dies at zero LP and that is the session's result**
(rule 29 clause 0). Say so and stop — do not solve to find out.

**If it dies, the successor hypothesis is already identified and should be handed on rather than
guessed at:** PJM's published forced outage may be largely **PARTIAL derates** (a unit on a forced
derate still generates), which a **stop-detector cannot see at any duration**. pjm-162 records a
model PARTIAL block of 14,653 MW against a HARD-ZERO block of 27,009 MW; the question is whether the
missing 5-8 GW is partial-shaped. That is a different detector, not a different threshold.

## DO-NOT-REDO — every one of these is adjudicated (rule 28(a))
  - `pjm_measured_outage_event_cap` **R** (pjm-161, both arms registered): hours>$200 UNCHANGED at
    3/10/32, max price identical, top-1 %-netload unavailable MW unchanged 23,160 -> 23,160.
  - `dam_availability_rebasis` **G**; pjm-162 closed its re-open condition — the restore form is
    ANTI-TARGETED (+7.0 to +12.4 GW given back where the envelope is already too shallow).
  - `temp_dependent_derate` **R** (pjm-95). `ordc_scarcity_overlay` **G**.
  - `unit_outage_lp_capacity_basis` / `unit_outage_extract_basis_share` / `unit_outage_per_unit_clip`
    are `U`, but pjm-d4-3 read all three: they change the derate DENOMINATOR, i.e. they are LEVEL
    levers on the envelope. **They do not reach the composition defect. Do not spend a solve on them
    for this card.**
  - `da_virtual_bids` **K** — pjm-158 solved the disarm A/B across 2023-2025, pjm-159 closed the
    architecture. pjm-d4-3 re-screened 2022 by mistake and it cost an LP. DO NOT RE-TEST.

**On the level objection, which you WILL meet:** pjm-161 measured the model's asserted outage
(41.7/43.2/41.2 GW) as exceeding PJM's published fleet-wide record (33.3/33.0/35.9 GW). pjm-162
section 3 shows that comparison is not like-for-like: **19.2-20.4 % of model fossil nameplate is HARD
ZERO** (layup, retiree CEMS caps, COD masks, full windows) — capacity PJM's operational report does
not carry as outage at all. Net of it the model's **window** envelope is 14,653 MW against a
published 33,298 MW. Argue the level question on the window basis, state both numbers, and do not
let the aggregate comparison kill a composition repair.

## RULES THAT WILL BITE YOU
- **Rule 28(a) FIRST, before phase 0.** pjm-d4-3 launched a shard before finishing its matrix read
  and burned an LP on an already-adjudicated arm. Read the cell, then measure, then propose.
- Rule 23 [R-FROZEN-DERIVE]: a derive re-runs when its SOURCE DATA updates. This one re-runs because
  its **scope was wrong** (coal-only), which is a construction repair, not a residual re-fit —
  say so explicitly in the commit, and cite the sign-flip table, not any price number.
- Rule 29 [R-SCREEN]: ONE screen year if the kill gate clears. It is **2022**, by FOOTPRINT (92 tail
  hours vs 6-59 elsewhere), never by residual. Full span only if the screen clears.
- Rule 29(b): **G-DRIFT IS RUNNABLE FOR PJM AGAIN** (pjm-d4-3; three prior sessions' "NOT RUNNABLE"
  is stale). `pjm_d4_2_TP.meta.git_sha` = 5f133fd5, post-rewrite and alive. Re-audit from it; at
  pjm-d4-3's HEAD all 13 changed solve-path files were INERT, so form 4 holds and NO control solve
  is spent.
- Rule 30(c): a held-out year NEVER downgrades PJM. Re-score 2023-2025 on any promotion candidate.
- Rule 32 [R-SHARD]: THE PARENT NEVER SOLVES. One year per shard, own out-dir, own branch, pinned to
  a FULL 40-CHAR SHA you pushed first.
- Rule 31 [R-RETAIN]: NEVER delete a solve's results before the owner rules. Gitignore instead
  (`results/calibration/pjm_d4_4_*/`), placed NEXT TO the pjm_d4_3_ rule, never at the file tail.

## MECHANICS ALREADY PAID FOR — do not rediscover
- `data/clean` ships EMPTY; a fleet build (and any solve) needs exactly five datatypes (~6 min):
    uv run python scripts/regenerate_clean.py fleet fuel-prices reference
    uv run python scripts/regenerate_clean.py transfer-interface-limits ramp-capability
  A fleet_only probe WILL crash with FileNotFoundError on transfer-interface-limits without them.
- EVERY solve container: `python3 scripts/prepare_solve_container.py`, then eval its --emit-exports
  in EVERY solve shell (PJM peaks 12.5-13.8 GB in 15.7 GiB; else SIGKILL).
- DA-virtuals: `pjm_da_virtual_bids` is ARMED and virtual_bids.py HARD-FAILS without the corpus.
  `scripts/data/fetch_pjm_da_virtuals.py --years <Y> --feeds hrl_da_incs_decs`, ~6 min/yr with two
  fetches in parallel (measured; older handoffs' "~13 min/yr" is pessimistic).
- Shard invocation: `scripts/replay_keeper.py results/calibration/pjm_d4_2_TP --years <Y>
  --set <field>=<json> --out-dir results/calibration/pjm_d4_4_<tag>_<Y>`. `composed_from` is now in
  replay_keeper's `_IGNORE` (ae3d9982) so the composed keeper bundles ARE replayable.
- **Shard prompts MUST name the specific failure the shard is likely to hit and pre-authorise
  stopping on it.** In pjm-d4-3 the generic "a shard that repairs infrastructure is a FAILURE"
  sentence was present verbatim and did not hold — the shard hit a fail-closed guard and patched
  scripts/replay_keeper.py instead of stopping.
- Shard branches AUTO-MERGE, putting per-year bundles on `main`. Rule 32(d): read the numbers off
  them FIRST, then untrack (`git rm -r --cached`, never `rm`) in the parent's own PR.
- REGISTER BEFORE SCORING: legitimacy_diagnostics' materiality denominator comes from the REGISTERED
  sidecar; unregistered, `load_share` is None and every class gates fail-closed.
- `dashboard_add_run.py --label` slugs to the FIRST FOUR non-stopword words; make A and TP labels
  differ inside those four and re-read the sidecar rather than trusting the exit code.

## CI BASELINE ON main — verify by stash, report only NEW failures
Measured 2026-09-10 at 02c14d9f + the pjm-d4-3 merge:
  check_registry_payload_parity — 4, ALL CAISO (caiso271_family_2022..2025); ERCOT's cleared.
    NOTE: it scans the FILESYSTEM (`calib_root.iterdir()`), not git, so a gitignored bundle on local
    disk trips it LOCALLY but not in CI. CLAUDE.md's "only ever sees committed dirs" is CI-only.
  check_gate_a_provenance — 4 stale rows (CAISO, ERCOT, MISO, SPP); **PJM's is CLEAN**.
  pytest tests/scoring — 15 failed / 1474 passed / 12 skipped (identical on main).
  GREEN: audit_keepers --iso PJM (0/0), build_status --check --iso PJM,
         check_cache_key_registration, check_mechanism_matrix.
No required status checks exist; red CI is not a merge blocker and not an excuse.

## OPEN ROOT CAUSES INHERITED (routed, not closed — do not silently absorb)
1. The PJM **hydro deficit (m/a ~0.56, 6-7 TWh/yr)** may be largely a PUMPED-STORAGE ACCOUNTING SEAM:
   the bench's `hydro` is EIA-930 `NG: WAT`, which INCLUDES PS gross generation, while the model
   carries PS in its storage class (discharge 5.09-5.79 TWh/yr). Model hydro + PS discharge lands
   within ~0.4-1.9 TWh of NG: WAT. **Settle this before anyone spends a hydro lane.**
2. `ST_GAS_PEAKER_PLANTS` is solve-affecting but INVISIBLE to `cache_key()` (absent from
   solve_surface.SURFACE_MODULES; SOLVE_EPOCHS empty). data/outages.py imports numpy/pandas, so a
   SolveEpoch is the route.
3. Plants 3138 (48.6 % duty) and 3131 (51.0 %) still fail the D-4 per-unit conduct rider under
   st_netload_drag; they do not decide C8 only because the budget clears.
4. `da_virtual_bids` stays K, but pjm-d4-3 measured its rule-13 anchor at ACTUAL DA prices as
   +16.537/+16.812/+12.248 TWh in 2020/2021/2022 against ~0 in 2023-25, so the pjm-158 "the anchor
   reproduces, the DA->RT gate is the defect" framing does not hold in the holdout span. Appended to
   the standing pjm-159 owner escalation. NOT a lever.
5. `ordc_scarcity_overlay` is `G` because "the in-LP co-opt already owns the phenomenon" — and that
   co-opt's dual is 0.00 in every hour of 2021, 2022 and 2023. The refusal's premise is measurably
   false. This is NOT a licence to arm the adder (a stack on an inert mechanism is still a stack).
6. `ae3d9982` (a shard's replay_keeper.py edit) is on `main`, let stand on review; it revealed that
   every composed multi-year keeper bundle was previously unreplayable.

## GATES BEFORE PUSH
check_registry_payload_parity · audit_keepers --iso PJM · build_status --check --iso PJM ·
check_mechanism_matrix --base origin/main (new field => new matrix row + a cell line in EVERY shard,
same PR) · check_cache_key_registration --base origin/main · check_gate_a_provenance ·
pytest tests/scoring. ruff: `uv run ruff check --fix --force-exclude -- <files>` then
`uv run ruff format --force-exclude -- <files>`.

## REPORT
The gas sub-5-day detection result against the pre-registered kill bar; the sign-flip identification
with the sweep-refusal stated; the rule-13 forward argument BEFORE any arm is proposed; the detector's
economic-idling guards and how they were identified ex ante; every criterion before/after at full
magnitude INCLUDING regressions; explicit confirmation that 2023-2025 still reads CALIBRATED; what
you escalated rather than absorbed; the state of every bundle on disk and whether it survives the
session; and the rule-31 promotion question, asked explicitly.
```
