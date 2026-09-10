# PRECOMMIT — capx D92: charter D77's named residue, scoped before any LP

**Lane:** capx **D92** · **Date:** 2026-09-10 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/d77-co2-residue-resolve-fux1gc` (harness-designated; the charter names the lane
`claude/capx-d92-d77-co2-residue` — naming only), fresh off `origin/main` `c6640b97`
**Authority:** OWNER RULING **Q65** (2026-09-10, capx ledger §0bi.3(a)) — *"Charter D77's named residue only."*
**Predecessors read:** `FINDING-capx-d90-rescore-2026-09-09.md` (§5.1 attribution) ·
`FINDING-capx-d90r-2026-09-09.md` · `FINDING-capx-d77-2026-09-06.md` §8 ·
`PRECOMMIT-capx-d90-rescore-2026-09-09.md` + Addenda A/B (validated scorer, FC-7 rule)

**PUSHED BEFORE ANY LP IS SPENT.** Every gate, prediction and scope call below is fixed at this
commit. Nothing here is graded charitably later.

---

## 1. PART 1(a) — THE SCOPE, ENUMERATED FROM THE COMMITTED RECORD AT THIS HEAD

### 1.1 What D77 actually named — quoted, not paraphrased

> **"the three NEISO T3 verdicts' co2@2030/2035/2040 FC-5 rows and their FC-6 paired-P1
> cumulative-CO2 row are the only SCORED cells mis-stated"**
> — `FINDING-capx-d77-2026-09-06.md` §8.2

The three verdicts D77 listed, from its own §8.2 table: **`neiso-t3`**, **`neiso-t3-pre-d60`**,
**`neiso-t3-pre-d47`**. D77 also recorded, as context and not as named residue, that the same
verdicts' non-CO2 corridor rows "move too", that FC-6 `paired P2` is "likewise mis-stated in its
operands", that `paired P3` is "unlikely to move", and that the FC-6 battery rows' "**status will
not change**".

### 1.2 A ZERO-LP FORENSIC TEST replaces the merge timestamp

Rather than date each bundle against a D77 merge sha (this clone's history is grafted — every
`campd_bins.py` change resolves to one boundary commit), each committed NEISO golden bundle is
classified by **what its own numbers say**. D77's published A/B separates the two worlds by more
than a factor of two at 2029 (14.021 pre-fix vs 6.795 post-fix), so `co2_mt@2029` is a clean
discriminator. Measured over every committed `results/ff-t3-neiso-golden/**` bundle:

| bundle | solved | co2 2028 / 2029 / 2030 | carries D77? |
|---|---|---|---|
| `bau` | 2026-09-01T19:41Z | 16.769 / 15.217 / 14.885 | **NO** |
| `bau/fc6/arms/*` (4) | 2026-09-01/02 | 15.36–16.77 / 14.62–15.22 / 14.60–14.89 | **NO** |
| `bau-d46` | 2026-09-03T10:00Z | 16.855 / 15.305 / 14.710 | **NO** |
| `bau-d46/fc6/arms/*` (4) | 2026-09-03 | 15.45–16.63 / 14.71–15.31 / 14.36–14.71 | **NO** |
| `bau-prera-2026-08-31` + its 5 arms | 2026-08-31/09-01 | 15.43–17.46 / 14.70–15.76 / 14.34–14.87 | **NO** |
| `bau-d60` | 2026-09-06T03:46Z | **15.856 / 14.021 / 13.368** | **NO** — reproduces D77's control leg to 3 d.p. |
| `bau-d65br` | 2026-09-07T02:45Z | 9.872 / 4.757 / 6.106 | **YES** |
| `d90-rescore` | 2026-09-09T02:29Z | **12.928 / 6.795 / 6.955** | **YES** — reproduces D77's arm leg to 3 d.p. |

The two clusters are separated by ~7 Mt at 2029 with nothing in between. This is a measurement,
not an inference.

### 1.3 THE SCOPE TABLE

| verdict at HEAD | run_id it names | primary bundle | bundle vs D77 | FC-5 co2 rows read from | FC-6 P1 read from | IN / OUT |
|---|---|---|---|---|---|---|
| **`neiso-t3`** (LIVE) | `neiso-2026-2050-t3-golden3-d90` | `d90-rescore` (`ae317e63263c8eef`) | **POSTDATES** | `ff-corridor/dispositions/neiso-t3.json`, `model_source.cache_key` **`706e7ba8e6582d42` = `bau`, PRE-D77** | `bau-d46/fc6/paired_invariants.json`, arms `67678e58b2d0526c` / `56019f3b0850e9f9`, **PRE-D77** | **IN — the two named cells ONLY** |
| `neiso-t3-pre-d90r` | `neiso-2026-2050-t3-golden3-d60` | `bau-d60` | predates | same | same | **OUT — frozen prior** |
| `neiso-t3-pre-d60` | `neiso-2026-2050-t3-golden3-bau` | epoch `67678e58b2d0526c` (`bau-d46`) | predates | same | same | **OUT — frozen prior** |
| `neiso-t3-pre-d47` | `neiso-2026-2050-t3-golden3-bau` | epoch `67678e58b2d0526c` (`bau-d46`) | predates | same | same | **OUT — frozen prior** |

**What D90-R already closed:** `neiso-t3`'s **primary bundle**. D90-R re-pointed the record from
`bau-d60` to `neiso-2026-2050-t3-golden3-d90`, which the forensic test above places on the
post-D77 side. FC-1, FC-2, FC-3, FC-4, FC-7 and FC-8 on that verdict are therefore scored on a
repaired bundle and are **not** stale for D77's reason.

**What D90-R did NOT close, and this lane owns:** the two carried inputs. `bau-d60` and
`d90-rescore` carry **no `fc6/` directory at all** (verified: `ls` shows `NEISO/`, `dof_ledger.json`,
`forecast_attestation.json`, `forecast_verdict.json`, `full_horizon_summary.json`,
`run_config.json` — nothing else), and the corridor table's own `model_source` block names `bau`.
So the live board's FC-5 co2 rows and FC-6 paired-P1 row are computed from bundles the forensic
test classifies **PRE-D77**. That is D77's named residue, still live, at this HEAD.

### 1.4 PART 1(b) — THE STOP GATE, APPLIED

* **`d90-rescore` POSTDATES D77 ⇒ the bundle is NOT in scope.** Its FC-1/FC-2/FC-3/FC-4/FC-7/FC-8
  legs are dropped from this lane. They are not re-solved, not re-scored on new numbers, and not
  discussed further except as carried inputs.
* **`neiso-t3-pre-d90r` / `-pre-d60` / `-pre-d47` are frozen priors and are dropped.** A `pre-X`
  record exists to say what was scored *before* X; re-solving one destroys the thing it records.
  Two of them are D77's own named verdicts, and this is the reason they are nonetheless OUT: their
  numbers are *supposed* to be the superseded ones. `-pre-d90r` was created after D77's list and
  inherits the same status.
* **Consequence, stated plainly:** the scope is **two cells on one verdict**, not four verdicts.
  Everything else that could be called "stale on this record" is named in §9 and left.

### 1.5 What this lane does NOT touch (declared before it can become convenient)

The FC-6 **driver-battery** input (`bau-d46/fc6/driver-battery-neiso-2026-09-03.json`, the T1.6
ladder) is a **separate scorer input** (`--driver-battery`, not `--paired-invariants`) and D77
named its status as unable to change. It is carried byte-identical and is **OUT**. The FC-5
table's 51 non-CO2 rows are handled in §6.2 — read that clause, it is a fork this lane declares
rather than resolves silently.

---

## 2. PART 2 — THE `G1_UNKNOWN`, DIAGNOSED BEFORE ANY SOLVE

`scripts/check_key_provenance.py` is **EXIT 1** at `c6640b97`. The charter quotes one failure; at
this head there are **seven**:

```
[G1_UNKNOWN] docs/handoffs/scn-ws5b-neiso/{ALL-CLEAN,CAP-STATE-TIGHT,CARB-HI,CES-P60,CES-T80}/run_config.json
[G1_UNKNOWN] results/ff-t3-neiso-golden/d90-rescore/run_config.json
[G6_UNREGISTERED_SCHEMA_DRIFT] caiso_dsw_lateevening_clean   (the CAISO lane's; named-and-left, §9)
```

### 2.1 The measurement: ALL SIX reproduce under the ONE listed recipe

Each record's stored `scenario_config` payload was re-hashed with
`scripts.lib.key_provenance.apply_recipe` under the recipe already committed for the single listed
`lag` entry — `{"undrop": ["pjm_seam_neighbour_hourly_ladder"]}`:

| record | recorded key | HEAD rules | **UNDROP recipe** | |
|---|---|---|---|---|
| `scn-ws5b-neiso/REF` *(the ONE listed entry)* | `1b452c457ca786a6` | `09b7e61d88f83579` | `1b452c457ca786a6` | **MATCH** |
| `d90-rescore` | `ae317e63263c8eef` | `f04fd06348e1623d` | `ae317e63263c8eef` | **MATCH** |
| `scn-ws5b-neiso/CAP-STATE-TIGHT` | `9bceb08bc291fced` | `31e7090a388d7da7` | `9bceb08bc291fced` | **MATCH** |
| `scn-ws5b-neiso/ALL-CLEAN` | `1c5c40a4fd011b6b` | `aaecf1bb07355400` | `1c5c40a4fd011b6b` | **MATCH** |
| `scn-ws5b-neiso/CES-P60` | `bd7de61415f5d950` | `859b3ca99d187974` | `bd7de61415f5d950` | **MATCH** |
| `scn-ws5b-neiso/CARB-HI` | `0e65d419ef104c54` | `3b6a4671622d909a` | `0e65d419ef104c54` | **MATCH** |
| `scn-ws5b-neiso/CES-T80` | `e4286b070d08cdcb` | `5d22c3d99d9e8d2e` | `e4286b070d08cdcb` | **MATCH** |

Every payload carries the field at `False`; today's rule drops it at `False`; un-dropping that one
field reproduces every recorded literal **exactly**. The `d90-rescore` line also reproduces D90's
own §4.1 measurement to the character (`ae317e63263c8eef` ↔ `f04fd06348e1623d`).

### 2.2 THE DISPOSITION: direction (ii), with one correction to how it is usually stated

**It is a listing gap on records whose non-reproduction IS understood — and the gap is
STRUCTURAL, not a miscount.** capx D91 registered `pjm_seam_neighbour_hourly_ladder` at
`ee2275d2`, merged to `main` at **2026-09-09T03:09:30Z**, and counted **one** orphan. That count
was correct *for what was committed on `main` at that instant*. The six records here were solved
on SHAs that do **not** contain the registration:

| record | solved | solve sha | contains D91's registration? |
|---|---|---|---|
| `REF` | 01:57Z | `4e28ee41` | no (verified `merge-base --is-ancestor`) |
| `d90-rescore` | 02:29Z | `09ef52a3` | no (sha not in this clone; D90 §4.1 states it) |
| `CAP-STATE-TIGHT` | 05:39Z | `2c1b0379` | **no** — solved 2.5 h AFTER the merge |
| `ALL-CLEAN` | 07:06Z | `e81c6e61` | **no** — verified, branch never rebased |
| `CES-P60` / `CARB-HI` / `CES-T80` | 07:36–11:21Z | `1bb1c2b8` / `fd140315` / `5c67e02d` | no |

Rule 32 `[R-SHARD]`(c)(1) *requires* a shard to pin an immutable SHA and forbids it to rebase. So
a registration repair keeps minting orphans for as long as any lane is still running on a pre-repair
SHA — here, at least **9 hours 24 minutes** past the merge. **D91's orphan set was never a fixed
number that could be counted once and listed.** That is the finding, and it is not a defect in D90-R's
registration, in this desk's work, or in D91's arithmetic.

### 2.3 WHAT THIS LANE DOES WITH IT: nothing. It stays RED.

`key-provenance-exceptions.json`'s own `what_this_is_not` — *"NOT a place to park a NEW mismatch. A
sixteenth is a FINDING: the lane that meets one stops and reports it, and only an owner card adds a
class here"* — and the charter both forbid appending. **No entry is added. The gate is left EXIT 1
and reported.** What is owed is an owner card deciding whether a `lag`-class record can be listed by
a lane that did not create it, and whether the recipe should be a *class rule* (any payload carrying
`pjm_seam_neighbour_hourly_ladder` at `False` with a pre-`ee2275d2` solve sha) rather than seven
hand-listed rows. **Owner: the capx director / the key-provenance owner (capx D85/D91's desk). Named,
not "routed to a batch".**

### 2.4 What it tells me about my own arm — the reason the charter ordered this first

My legs solve at a HEAD that **contains** `ee2275d2`, so their `run_config.json` will hash under the
same rules the gate applies. **My bundles will reproduce their own keys and will not add a G1.**
Verified in advance, not assumed: the construction `head_key(payload)` and
`ScenarioConfig.cache_key()` agree at this HEAD for a config built here.

---

## 3. G-DRIFT — AND WHY THIS LANE BUYS THE CONTROL RATHER THAN ARGUING ABOUT IT

Form 4 on a recorded-key basis audits **config drift only**. D88 §3 showed it is blind to
derived-input drift; D90 §5.1 showed it is blind to **non-config code drift**, and that D77 *is*
exactly that. The window here is worse than D90's, not better: `capx-director r#64` records **573
commits** merged in the window that closed at this HEAD.

**Therefore: no form-4 differencing against a committed bundle, and no argument about whether HEAD
moved.** Leg **L0 (`base`)** is a **same-container control solved at the same pinned HEAD as every
arm**, and *every* gate below is graded against L0 — never against `d90-rescore`. L0's differences
from the committed `d90-rescore` bundle are reported as a measurement of HEAD drift
(`09ef52a3` → this HEAD) and are attributed to nothing without evidence.

**One config fact established at zero LP, because it decides the arms' recipe.** HEAD's
`run_full_horizon.reference_config("NEISO", 2026, 2050, cmc=False, golden_posture=True)` differs from
`d90-rescore`'s recorded payload in **17 fields**, of which:

* **6 are request-vs-resolution, not differences** — `scarcity_price_overlay`, `ordc_voll`,
  `ordc_mcl_mw`, `ordc_lolp_sigma_mw`, `ordc_lolp_shift_sigma`, `ordc_multistep_floor` are
  *verbatim* NEISO's own `ISOConfig.default_scenario_overrides` (read and printed), which the runner
  resolves into the payload;
* **8 are schema growth** — fields absent from the older payload, all at their HEAD dataclass default;
* **2 are REAL and are `d90-rescore`'s own pins** — `ccs_retrofit_vom_adder` **8.0** (HEAD default
  2.95) and `ccs_retrofit_fixed_cost_co2_scaling` **False** (HEAD default True). These are exactly the
  two `UNIDENTIFIED` DOF entries D90-R §3.4 named.

So `run_driver_battery.py --paired-arm`, which builds from `reference_config` unpinned, would solve a
**third** recipe — neither the verdict's nor a control's. Every leg here therefore carries both pins
explicitly, so the FC-6 block describes the same model the rest of the verdict describes.

---

## 4. THE LEGS — four, indivisible, in shards (rule 32 `[R-SHARD]`)

Each leg: NEISO, **2026–2050, ONE invocation** (the evolution chain links the years; rule 12
`[R-PARALLEL]` makes them sequential inside a run, so the horizon **cannot** be sharded). Measured
cost from the committed record: **1,803–2,104 s wall, 2.9–3.9 GB peak RSS** per leg.

| leg | arm | overrides beyond the two pins | serves |
|---|---|---|---|
| **L0** | `base` | — | the **control**; FC-6 base operand; FC-5 model basis |
| **L1** | `carbon_plus25` | `carbon_price_delta=25.0` | **P1** — D77's named cell |
| **L2** | `gasup150` | `gas_price_factor=1.5` | P2 |
| **L3** | `gaspm5` | `gas_price_factor=1.05` | P3 |

Command shape (identical but for the arm override and `--out-dir`):

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src .venv/bin/python scripts/run_full_horizon.py \
  --iso NEISO --start-year 2026 --end-year 2050 --golden-posture --full-solve-authorized \
  --no-ccs-retrofit-fixed-cost-co2-scaling --set ccs_retrofit_vom_adder=8.0 \
  [--set <arm override>] --out-dir results/ff-t3-neiso-golden/d92/<arm>
```

**Rule 32 compliance and the one place it cannot be met.** (a) The parent runs **no LP**: every leg
goes to its own shard container, and the parent does phase 0, composition, scoring and registration
only. (c) Each shard gets a full 40-character immutable SHA (this PRECOMMIT's), its own `--out-dir`,
its own branch, an explicit `git add -f <its path only>`, and the named prohibitions. **(b) cannot be
met and is declared, not evaded:** one leg is an indivisible ~32-minute invocation, and 32(b)'s
remedy — subdivide and launch children — is unavailable because the year loop is the chain. The
shards are therefore instructed to run to completion rather than to stop at 20 minutes; the charter's
own §PART 3 states this leg shape and its 31.1-minute measured cost.

**P1/P2/P3 are computed in the PARENT from SLIM artifacts, so no shard ships a multi-GB cache.**
`check_forecast_invariants` needs the cache dirs for P1 (parquets) and P3 (evolution ledgers), and
supports summaries for P2 and run_configs for the premise. Resolution, each half validated:

* **P1** — from each arm's `full_horizon_summary.json` `trajectory.co2_mt`. **Validated on the
  committed d46 pair before this lane solves anything:** `sum(co2_mt)` = **284.42** (base) and
  **273.92** (carbon_plus25), which is the committed P1 detail string *exactly*, on both operands.
* **P1.premise** — `--paired-run-configs` (capx-D73's first-class artifact mode, zero LP).
* **P2** — `--paired-summaries --pair-kind gas_up` (capx-D35's first-class artifact mode).
* **P3** — `--paired --pair-kind gas_pm5` over ledger-only directories; `check_p3_perturbation`
  reads `run.ledgers` alone, so the parquets are not required.

Each shard commits only `full_horizon_summary.json`, `run_config.json`, `config.yaml` and the 25
`evolution_<year>.json`, and reports its cumulative CO2, per-year CO2 at 2028/2029/2030/2035/2040/2050,
terminal reserve margin and wall time **in numbers in its final message** (rule 32(c)(5)).

---

## 5. PART 1(c) — PRE-DECLARED PREDICTIONS. FIXED HERE.

Anchored on `d90-rescore` as the best available post-D77 proxy for L0, **explicitly acknowledging
that L0 will differ from it by HEAD drift** — which is why several brackets are wide, and why a wide
bracket is declared as weak evidence rather than claimed as a hit later.

| # | prediction | grading rule |
|---|---|---|
| **D1** | **L0 cumulative CO2 (2026–2050) lands in [140, 175] Mt**, down from the committed P1 base operand **284.42 Mt** | HIT iff in bracket |
| **D2** | **P1 stays PASS** — L1's cumulative CO2 is strictly below L0's | HIT iff P1 PASS |
| **D3** | **The P1 margin NARROWS in absolute Mt**: `base − high` < **10.50 Mt** (its committed value) | falsifiable both ways; the mechanism is D77's own — a correctly-rated captured unit pays 1/10 of the carbon adder, so the arm the adder acts on is smaller |
| **D4** | **P1.premise stays PASS** (+25.00 $/t in all 25 years) | structural, near-certain; **declared as a near-certainty, so a hit here is worth nothing** |
| **D5** | **FC-6 CATEGORY stays CAVEAT**, still on the two vacuous T1.6 battery rows (carried, unchanged) | HIT iff CAVEAT and the detail still names T1.6a/T1.6b |
| **D6** | **FC-5 `co2@2030` SIGN-FLIPS**: divergence from **+60.6 %** to somewhere in **[−45 %, −5 %]** — the committed explanation ("Model CO2 at 2030 is HIGHER (+60 %)") is FALSIFIED and must be re-authored | HIT iff sign flips AND lands in bracket |
| **D7** | **FC-5 `co2@2035` divergence goes from −2.0 % to below −40 %** — the committed "level crossing … −2.0 % level agreement" explanation is FALSIFIED | HIT iff < −40 % |
| **D8** | **FC-5 `co2@2040` moves LEAST of the three**, staying inside **[−70 %, −50 %]** (committed −57.4 %) | HIT iff in bracket and \|Δ\| smaller than D6's and D7's |
| **D9** | **Exactly two committed IN-CORRIDOR rows become divergent (\|div\| > 15 %) and need a new explanation, and they are `capacity:gas_cc@2040` and `generation:total@2040`** | HIT iff both appear; **PARTIAL** if 1–4 rows flip and both are among them; MISS otherwise |
| **D10** | **HEAD drift is small for a NEISO forecast**: L0's cumulative CO2 differs from `d90-rescore`'s **154.42 Mt** by **< 5 %** | falsifiable both ways; a large drift is the interesting outcome and would be reported as such |
| **D11** | **DETERMINATION stays HOLD** | near-certain (FC-1/2/3/4/7 already FAIL); **declared as a near-certainty** |
| **D12** | Each leg's wall time in **[25, 45] min**; FC-8 stays PASS | HIT iff all four legs in bracket |
| **D13** | **FC-5 CATEGORY stays CAVEAT** after re-authoring — no row is left UNEXPLAINED | HIT iff CAVEAT; a FAIL here is an honest result and will be reported as one, not re-authored away |

**The one-sentence summary I will be graded on:** *the repaired basis moves D77's named cells a
great deal and moves no category status — FC-5 stays CAVEAT and FC-6 stays CAVEAT — while the
model's CO2 moves decisively AWAY from the AEO2025 anchor at 2030 and 2035, so the honest reading is
that closing this residue makes the record truer and the corridor gap larger.*

---

## 6. WHAT GETS RE-STATED, AND THE ONE FORK THIS LANE DECLARES

### 6.1 FC-6 — the whole paired block, because a half-rebased pair is incoherent

`paired_invariants.json` is regenerated from L0/L1/L2/L3. P1 alone is D77's named cell, but P1's
base operand is shared with P2 and P3: re-basing P1 and leaving P2/P3 on `bau-d46`'s pre-D77 base
would produce a file whose three rows compare three different worlds. All four legs are solved for
that reason and no other. The prior file is **not edited** — `bau-d46/fc6/` is left byte-identical.

### 6.2 FC-5 — THE FORK, DECLARED RATHER THAN RESOLVED SILENTLY

D77 named **3 rows**. The disposition table has **54** (18 quantities × 2030/2035/2040) and one
`model_source`. Editing 3 rows leaves a table whose cells are keyed to two different bundles; editing
54 re-bases 51 rows for a reason that is **run drift, not D77**.

**Zero-LP phase 0 built and VALIDATED the missing instrument.**
`docs/handoffs/d92/corridor_model_values.py` implements each row's own `model_basis` string literally
and **reproduces 54/54 committed `model_value` cells** from the bundle the table declares
(`bau`, `706e7ba8e6582d42`). A row it cannot reproduce would never be re-based; none exists.

**The declared resolution.** A NEW disposition is authored at
`results/ff-corridor/dispositions/neiso-t3.json` on the L0 basis, with the current table preserved
byte-equal at `dispositions/neiso-t3-pre-d92.json` — the pattern this very directory already uses
(`neiso-t3-prera-2026-08-31.json`, preserved by the T3-GOLDEN-2 session under owner ruling Q25).
All 54 `model_value`s are recomputed **mechanically** by the validated instrument; explanations are
re-authored **only** where a row's verdict changes or its existing text is falsified by the new
number. **The 51 non-CO2 rows move as a consequence of closing the 3 named ones, and that is stated
in the FINDING as a cost, not hidden as a tidy-up.** If the owner wants the narrower edit, the
preserved file is one `git mv` away.

### 6.3 The re-score — a CONTROLLED SWAP, and TWO readings

The scorer control is **already established in this container, before any leg exists**:
`forecast_verdict.py --tier t3` over the committed `d90-rescore` artifacts reproduces
`d90-rescore/forecast_verdict.json` with **NON-PROVENANCE IDENTICAL = True** — every category, row,
status and detail string — and reproduces the registered `ff-verdicts.json[neiso-t3]` record on every
field but `notes` (registration prose). Carried-input set, frozen (D90 Addendum D.2, re-verified):

| flag | artifact | in this re-score |
|---|---|---|
| `--summary` / `--run-config` / `--dof-ledger` / `--attestation` | `d90-rescore/*` | **carried** (reading i) / swapped for L0 (reading ii) |
| `--hindcast-score` | `hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json` | carried |
| `--crossover-score` | `hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json` | carried (**`rcrepair`**, not `capxd14` — D90 D.2 established this by experiment) |
| `--driver-battery` | `bau-d46/fc6/driver-battery-neiso-2026-09-03.json` | **carried** (§1.5) |
| `--paired-invariants` | `bau-d46/fc6/paired_invariants.json` | **SWAPPED — D77's named cell** |
| `--corridor` | `ff-corridor/dispositions/neiso-t3.json` | **SWAPPED — D77's named cell** |

* **Reading (i), the HEADLINE and what is registered:** `neiso-t3` on its own committed `d90-rescore`
  bundle with only the two named inputs swapped. This is D77's residue closed and **nothing else**.
* **Reading (ii), reported not registered:** everything scored on L0 — a fully coherent successor at
  one HEAD. Reported so the owner can see what a successor would read, exactly as D90 §7 asked and
  did not act on.

**FC-7 handling follows D90 ADDENDUM B literally**, all four clauses, if FC-7 moves. Pre-recorded
now: FC-7 currently reads **FAIL** ("UNATTESTED SKELETON: 2 of 9 entries … `ccs_retrofit_fixed_cost_co2_scaling`,
`ccs_retrofit_vom_adder`"), reading (i) carries that ledger unchanged so FC-7 **cannot move**, and L0
carries the identical two pins so reading (ii) should read FAIL for the identical reason. **If it
does, that is not a finding about this lane's arm** — it is the program-wide `CURATED_IDENTIFICATIONS`
desynchronization D90-R §3.4 routed, and it is not repaired here (clause 4).

---

## 7. RULE 31 `[R-RETAIN]` — DECLARED BEFORE THE FIRST BYTE IS WRITTEN

`results/ff-t3-neiso-golden/d92/**` is added to `.gitignore` in this same commit. **That, and not
`rm`, is what discharges rule 29 `[R-SCREEN]`(c)** — the ercot-255 incident is the reason. **No
solved bundle is deleted by this lane for any reason**, including a conclusion that it is not
promotable. The promotion question is asked explicitly in the FINDING's close, together with the
statement that the bundles live only on this container's disk.

## 8. BOUNDARIES

* **No file under `src/market_sim/` is edited.** Verified at close by `git diff --stat`.
* No `scripts/` file is edited. `docs/handoffs/d92/corridor_model_values.py` is a **measurement
  record**, not standing tooling, and its docstring says so.
* Rule 28 `[R-MECH-MATRIX]`: **does not fire.** No mechanism is proposed, tested or added; no
  `ScenarioConfig` field changes. This is a solve-score-register lane.
* No backcast artifact, keeper, marker, shard or freeze is touched. `program-status.json` moves only
  if reading (i) moves a NEISO `fc` letter.

## 9. NAMED AND LEFT — other reds on `main`, none of them this lane's

1. Four dead ERCOT bundle dirs failing the parity gate — `ercot262_arm_2024/2025`,
   `ercot264_repro_2023/2025` (rule 29(c)). **Owner: the ERCOT lane.**
2. The SPP mechanism-matrix shard is missing two cells. **Owner: the SPP lane.**
3. `status/SPP.js` is stale. **Owner: the SPP lane.**
4. The CAISO marker asserts CALIBRATED on a NOT-YET keeper. **Owner: the CAISO lane.**
5. `caiso_dsw_lateevening_clean` unregistered — the `G6` red, exposed by 273 records. **Owner: the
   CAISO lane** (D91's new gate caught it).
6. **The seven-record `lag` listing gap (§2).** **Owner: the capx director / key-provenance owner.**
7. **FC-6 is CARRIED on every T3 golden and has never been measured on its own solve** (D90-R routed
   item 5). This lane re-bases the *paired* half onto L0 for the one verdict in scope; the general
   problem — every other T3 golden, and the driver battery — **HAS NO LIVE OWNER. There is none.**
   Saying so is this lane's charter.
