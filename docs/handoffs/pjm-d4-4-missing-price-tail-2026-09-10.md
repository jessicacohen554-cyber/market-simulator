# HANDOFF — pjm-d4-4: the missing price tail

Written by session `pjm-d4-3` (2026-09-10). The prompt below is the deliverable: paste it whole.
Its evidence base is `docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md` (the measurement) and
`docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md` (the session it came out of).

**Why this is a handoff and not a launched shard.** pjm-d4-3 stopped short of launching because the
arm is not yet specified: the four candidate mechanisms were not read, and the committed pjm-162
census contains a contradiction (the model asserts MORE outage than PJM published on the tightest
days, yet out-generates the meter by 11 GW in the scarcity hours) that must be resolved at zero LP
before any arm is defensible. Launching on an unspecified arm is exactly the failure that cost
pjm-d4-3 an LP (RESULT §1/§6).

---

```
PJM: the missing price tail — session pjm-d4-4

DATA PROFILE: pjm. MODEL: Opus or Fable (rule 27 [R-PUSH]). SCOPE: PJM ONLY.
BASE: origin/main. `git checkout -b claude/pjm-d4-4`.
Do NOT open a PR unless the owner asks. Never write another ISO's keeper/matrix/status/log.

READ IN FULL FIRST:
  docs/ADDENDUM-pjm-d4-3-lmp-gap-next-lp-2026-09-10.md   (your card — sections 3 and 4 are the object)
  docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md      (section 2 the hours/loading split; 6 DO-NOT-REDO; 8a)
  results/calibration/FINDING-pjm161-outage-inversion-and-da-virtual-energy-2026-08-14.md  (7, 7.5)
  results/calibration/FINDING-pjm162-outage-envelope-basis-closure-2026-08-15.md
  docs/codebase-site/data/mechanism-matrix/PJM.js        (the outage family; DO-NOT-REDO the R/I/G cells)

## THE STATE YOU INHERIT
PJM's TRAINING span is CALIBRATED, zero caveats, empty determination basis, keeper
2026-09-10-pjm-d4-2-stgas (+ -touchpoint, folded). DO NOT DISTURB IT (rule 30(c)).
HOLDOUT 2020-2022 reads NOT-YET on C1 fuel-mix, C3a mean LMP, C3b price shape.

## WHAT pjm-d4-3 MEASURED (zero LP; all from committed artifacts — do NOT re-derive)
1. **2022's C3a failure IS the missing tail.** 92 actual hours RT>$200, model forms **0**; they carry
   $5.78/MWh of the annual mean against a $5.48/MWh miss = **105 %**. The 26 hours >$500 carry $4.52
   alone. 2025 69 %, 2024 52 %. **2020 is the OPPOSITE defect (+21.4 % OVER) and is NOT this card.**
2. **The reserve co-opt is provably INERT.** hourly/reserve_family_2022.parquet: dual exactly
   **0.00 in 8,760 of 8,760 hours** on BOTH families (pjm_primary, pjm_primary_mad),
   held == requirement to the MW, zero shortfall — including all 92 tail hours. Same in 2021, 2023.
   2025 is the only year with real formation (21/37 h, max $190). The requirement is PJM's measured
   **Primary** series only, mean 2,663 / max 4,224 MW (model/reserves/spec.py).
   NOTE FOR GOVERNANCE: ordc_scarcity_overlay is `G` on the stated ground that "the in-LP co-opt
   already owns the phenomenon". That premise is measurably false in 2021/2022/2023. This is NOT a
   licence to arm the adder (a stack on an inert mechanism is still a stack) — it means the co-opt's
   own operands are the object.
3. **Model thermal over-dispatch MORE THAN DOUBLES in the tail:** +4.3 GW all-hours -> **+9.7 GW** at
   RT>$200, **+11.1 GW** at RT>$500 (model 89.1 vs meter 78.0 GW). Elliott Dec 23-24 2022: model
   80.9 vs meter 72.9 GW while actual RT averaged $844.
4. Same signal as the CC_REGULAR **online-hours leg** (RESULT section 2), seen from the price side.

## THE CONTRADICTION YOU MUST RESOLVE BEFORE ANY LP — this is the whole phase 0
pjm-d4-3 first read this as "too much headroom" and **that reading does not survive its own
sources**. From the COMMITTED results/calibration/_pjm162_route1_phase0.json (2023, keeper
pjm152_collapse_A):

  fossil cap 137,700 MW · model asserted outage 41,663 MW mean
  of which HARD ZERO 27,009 MW (64.8 % of asserted, **19.6 % of fossil cap**) + PARTIAL 14,653 MW
  PJM published total 33,298 MW · published FORCED 7,653 MW
  top1pct_netload (4 d): model 21,253 MW vs published total 10,785 / forced 9,351
  event_window  (2 d):   model 25,899 MW vs published total 18,116 / forced 11,710

**So on the TIGHTEST days the model already asserts ~10-12 GW MORE outage than PJM published, and
STILL forms no tail.** "The model is too available" is therefore NOT established — net of asserted
outage the tail-hour headroom is ~19-26 GW, not the 43-61 GW a nameplate difference suggests
(pjm-d4-3 corrected this against itself; do not re-make the error). Yet the model generates 11 GW
MORE thermal than the meter in those same hours. Both are true and they are not yet reconciled.

**Phase 0 must answer, at ZERO LP, in the parent (rule 32(a)):**
 (a) In 2022's 92 RT>$200 hours specifically — not 2023, which is all pjm-162 measured — what is the
     model's asserted outage, its hard-zero block by CAUSE (layup / retiree CEMS cap / COD mask /
     full window), and its unused-but-available MW? Rebuild _pjm162_route1_phase0.json's
     attribution for 2020-2022 on the CURRENT keeper (pjm_d4_2_TP), which pjm-162 never saw.
 (b) Reconcile (3) with the census: if the model asserts MORE outage than published and still
     out-generates the meter by 11 GW, WHICH units are producing that the meter says were not? Use
     the payload's per-plant `m` vs the bench `campd` on those 92 hours (the decode is in
     scripts/probes/nyiso196_cc_overrun_decomp.py::_series; pjm-d4-3 used it for the class split).
 (c) **THE KILL GATE, declare it in the PRECOMMIT before you look:** if the hard-zero block that is
     zeroed in those 92 hours does NOT exceed the headroom currently holding the reserve dual at
     zero, then no composition change can form the tail either and **the card dies at zero LP**.
     Say so and stop — that is a successful session (rule 29 clause 0).

## THE LEVER SPACE — and it is narrow, because the LEVEL route is closed BOTH ways
DO NOT RE-TEST. Every one of these is adjudicated:
  - pjm_measured_outage_event_cap **R** — pjm-161, both arms registered. P4 failed outright:
    hours>$200 UNCHANGED at 3/10/32, max price identical; top-1 %-netload unavailable MW unchanged
    23,160 -> 23,160. Removing outage does nothing.
  - dam_availability_rebasis **G** — pjm-145 refused ex ante; pjm-162 closed its re-open condition:
    the restore form is ANTI-TARGETED (+7.0 to +12.4 GW given back exactly where the envelope is
    already too shallow).
  - temp_dependent_derate **R** (pjm-95 demotion). ordc_scarcity_overlay **G** (see above).
  - ADDING outage contradicts pjm-161's measurement that the model's level already EXCEEDS PJM's
    published fleet-wide record (41.7/43.2/41.2 vs 33.3/33.0/35.9 GW).

**What is left, and it is the only thing left: COMPOSITION at constant level.** pjm-162's own named
root cause is untouched — a fifth of fossil nameplate at HARD ZERO every day rather than
present-and-expensive, which PJM's published record does not carry as outage at all. In the real
market that block was available at a high offer and is what set $500-1,500. Moving it from hard-zero
into the stack at its own offer changes composition, not level.
Candidate arms, ALL `U` in PJM's shard (no DO-NOT-REDO bar), and **you must read all four and say
which one actually reaches the hard-zero block before you pick**:
  unit_outage_lp_capacity_basis · unit_outage_extract_basis_share · unit_outage_per_unit_clip
  · historic_outage_overlay

## RULES THAT WILL BITE YOU
- **Rule 28(a) FIRST, before phase 0, not after.** pjm-d4-3 launched a shard before finishing its
  matrix read and burned an LP re-solving an arm pjm-158 had already adjudicated. Read the cell, then
  measure.
- Rule 1 [R-STRUCT]: the screen gate is STRUCTURAL and a STOP gate only. Gate on the reserve dual
  becoming non-zero in the target hours and on the model-minus-meter thermal gap closing from
  +11.1 GW. **Never gate on C3a/C3b/C1** — report them at full magnitude, both directions.
- Rule 30(c): a held-out year NEVER downgrades PJM. Re-score 2023-2025 on any promotion candidate.
- Rule 29 [R-SCREEN]: ONE screen year. If phase 0 clears, it is **2022** — chosen by FOOTPRINT
  (92 tail hours vs 6-59 elsewhere), never by residual. Full span only if the screen clears.
- Rule 29(b): **G-DRIFT IS RUNNABLE FOR PJM AGAIN** — pjm-d4-3 established this and three prior
  sessions' "NOT RUNNABLE" is stale. pjm_d4_2_TP.meta.git_sha = 5f133fd5 (post-rewrite, alive).
  Re-audit from it; at pjm-d4-3's HEAD all 13 changed solve-path files classified INERT, so form 4
  holds and NO control solve is spent.
- Rule 32 [R-SHARD]: THE PARENT NEVER SOLVES. One year per shard, own out-dir, own branch, pinned to
  a FULL 40-CHAR SHA you pushed first.
- Rule 31 [R-RETAIN]: NEVER delete a solve's results before the owner rules. Gitignore instead
  (results/calibration/pjm_d4_4_*/), placed NEXT TO the pjm_d4_3_ rule, never at the file tail.

## MECHANICS ALREADY PAID FOR — do not rediscover
- data/clean ships EMPTY; a fleet build needs exactly five datatypes (~6 min):
    uv run python scripts/regenerate_clean.py fleet fuel-prices reference
    uv run python scripts/regenerate_clean.py transfer-interface-limits ramp-capability
- EVERY solve container: `python3 scripts/prepare_solve_container.py`, then eval its --emit-exports
  in EVERY solve shell (PJM peaks 12.5-13.8 GB in 15.7 GiB; else SIGKILL).
- DA-virtuals: pjm_da_virtual_bids is ARMED and virtual_bids.py HARD-FAILS without the corpus.
  `scripts/data/fetch_pjm_da_virtuals.py --years <Y> --feeds hrl_da_incs_decs` is ~6 min/yr with two
  fetches in parallel (pjm-d4-3 measured; the "~13 min/yr" in older handoffs is pessimistic).
- Shard invocation: `scripts/replay_keeper.py results/calibration/pjm_d4_2_TP --years <Y>
  --set <field>=<json> --out-dir results/calibration/pjm_d4_4_<tag>_<Y>` — regenerates
  legitimacy_diagnostics too. `composed_from` is now in replay_keeper's _IGNORE (ae3d9982), so the
  composed keeper bundles ARE replayable; before that commit they were not.
- **Shard prompts MUST name the specific failure the shard is likely to hit and pre-authorise
  stopping on it.** In pjm-d4-3 the generic "a shard that repairs infrastructure is a FAILURE"
  sentence was present verbatim and did not hold — the shard hit a fail-closed guard and patched
  scripts/replay_keeper.py instead of stopping.
- Shard branches AUTO-MERGE, which puts their per-year bundles on `main`. Rule 32(d): untrack them
  (`git rm -r --cached`, never `rm`) in the parent's own PR, and read the numbers off them FIRST.
- REGISTER BEFORE SCORING: legitimacy_diagnostics' materiality denominator comes from the REGISTERED
  sidecar; on an unregistered bundle load_share is None and every class gates fail-closed.
- `dashboard_add_run.py --label` slugs to the FIRST FOUR non-stopword words; make A and TP labels
  differ inside those four, and re-read the sidecar instead of trusting the exit code.

## CI BASELINE ON main — verify by stash, report only NEW failures
Measured 2026-09-10 at 02c14d9f + the pjm-d4-3 merge:
  check_registry_payload_parity — 4, ALL CAISO (caiso271_family_2022..2025); ERCOT's cleared.
    NOTE: the script scans the FILESYSTEM (calib_root.iterdir()), not git, so a gitignored bundle
    on local disk trips it LOCALLY but not in CI. CLAUDE.md's "only ever sees committed dirs" is
    true of CI only.
  check_gate_a_provenance — 4 stale rows (CAISO, ERCOT, MISO, SPP); **PJM's is CLEAN**.
  pytest tests/scoring — 15 failed / 1474 passed / 12 skipped (identical on main).
  GREEN: audit_keepers --iso PJM (0/0), build_status --check --iso PJM,
         check_cache_key_registration, check_mechanism_matrix.
No required status checks exist; red CI is not a merge blocker and not an excuse — attribute
everything against this baseline.

## OPEN ROOT CAUSES INHERITED (routed, not closed — do not silently absorb)
1. The PJM **hydro deficit (m/a ~= 0.56, 6-7 TWh/yr)** may be largely a PUMPED-STORAGE ACCOUNTING
   SEAM: the bench's `hydro` is EIA-930 `NG: WAT`, which INCLUDES PS gross generation, while the
   model carries PS in its storage class (discharge 5.09-5.79 TWh/yr). Model hydro + PS discharge
   lands within ~0.4-1.9 TWh of NG: WAT. **Settle this before anyone spends a hydro lane on it.**
2. ST_GAS_PEAKER_PLANTS is solve-affecting but INVISIBLE to cache_key() (not in
   solve_surface.SURFACE_MODULES; SOLVE_EPOCHS empty), so two runs with identical run_config.json
   can differ. data/outages.py imports numpy/pandas so a SolveEpoch is the route.
3. Plants 3138 (48.6 % duty) and 3131 (51.0 %) still fail the D-4 per-unit conduct rider in nearly
   every year under st_netload_drag. They do not decide C8 only because the budget clears.
4. da_virtual_bids stays `K`, but pjm-d4-3 measured its rule-13 anchor at ACTUAL DA prices as
   +16.537/+16.812/+12.248 TWh in 2020/2021/2022 against ~0 in 2023-25 — the pjm-158 "the anchor
   reproduces, the DA->RT gate is the defect" framing does not hold in the holdout span. Appended to
   the standing pjm-159 owner escalation; NOT a lever.
5. ae3d9982 (the shard's replay_keeper.py edit) is on `main` and was let stand on review. It
   revealed that every composed multi-year keeper bundle was previously unreplayable.

## GATES BEFORE PUSH
check_registry_payload_parity · audit_keepers --iso PJM · build_status --check --iso PJM ·
check_mechanism_matrix --base origin/main (re-stamp PJM.js AND its 5.3 prose header on a promotion) ·
check_cache_key_registration --base origin/main · check_gate_a_provenance · pytest tests/scoring.
ruff: `uv run ruff check --fix --force-exclude -- <files>` then `uv run ruff format --force-exclude -- <files>`.

## REPORT
The phase-0 census for 2020-2022 on the CURRENT keeper; the resolution of the contradiction above
(or the kill, if the gate fires); the declared criterion with the sweep-refusal stated; the rule-13
forward argument BEFORE any arm is proposed; every criterion before/after at full magnitude
INCLUDING regressions; explicit confirmation that 2023-2025 still reads CALIBRATED; what you
escalated rather than absorbed; the state of every bundle on disk and whether it survives the
session; and the rule-31 promotion question, asked explicitly.
```
