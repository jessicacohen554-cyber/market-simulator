# FINDING ws6-parity — the eight unmapped NYISO bundle dirs are solve INPUT, not dead output

**Session:** ws6-parity-repair (2026-08-20). **Charter:**
`docs/model-audit-release-plan-2026-08.md` §0/§3 WS6 (BLOAT). Repair lane —
no solves, no keeper moves, no mechanism work.

**Result: `scripts/check_registry_payload_parity.py` runs CLEAN at this HEAD.**

```
registry/payload parity OK (52 runs checked, 62 bundle dirs swept, 0 known-unsynced tolerated)
```

`tests/scoring/test_registry_payload_parity.py` — 10 passed.

## 1. What the gate actually found

The dispatch reported nine failures. At `origin/main` `66ae225` the gate
reports **eight**, all NYISO: `miso172_control` had already cleared itself
when the miso-172 arms registered (`1e780aa`, `f647a3e`), which is the same
self-clearing the board predicted for `ercot221_control_A` and which
`ercot221_control_A` has since done. That pattern is the finding in miniature:
**a control bundle unmapped at HEAD is usually an in-flight lane, not litter.**

The eight:

| dir | contents | class |
|---|---|---|
| `nyiso144_arm_recipe` | 1 file, `meta.json` (20 KB) | spent recipe |
| `nyiso146_arm_recipe` | 1 file, `meta.json` | spent recipe |
| `nyiso146b_armB_recipe` | 1 file, `meta.json` | spent recipe |
| `nyiso146b_armC_recipe` | 1 file, `meta.json` | spent recipe |
| `nyiso146c_armB2_recipe` | 1 file, `meta.json` | spent recipe (**keeper's**) |
| `nyiso147_armA_recipe` | 1 file, `meta.json` | **LIVE** recipe |
| `nyiso147_armB_recipe` | 1 file, `meta.json` | **LIVE** recipe |
| `nyiso147_control` | 3.7 MB, `hourly/` ×3 yr + diagnostics | **LIVE** control |

**Seven of the eight contain no solve output whatsoever** — no `metrics.json`,
no `calibration_attestation.json`, no per-year parquet, nothing a solve
writes. The gate's message classes them as "dead solve output". That
classification is factually wrong for them, and it is what made a
naming-pattern batch-prune look reasonable.

## 2. Why a one-file dir is a complete artifact, not a truncated one

`run_calibration_full.run_replay_bundle` reads **only** `bundle/meta.json`:

```python
meta = json.loads((bundle / "meta.json").read_text())
kwargs = rk.build_kwargs(meta)
```

Its own docstring: *"the bundle's `meta.json` is the authoritative snapshot of
every `solve_and_persist` kwarg, so a keeper/probe recipe reproduces exactly
at the dispatched ref — including single-delta A/B arms whose delta is a code
change — without expressing the recipe through the workflow input surface."*

So a dir holding exactly one `meta.json` is a **complete and valid**
`--replay-bundle` input by construction. It is also the *only* way to express
an A/B arm whose delta is a code change — such an arm cannot be reconstructed
from CLI flags, which is precisely why the NYISO lane started writing these
dirs at nyiso-144 (earlier sessions, e.g. nyiso-140, composed their arms from
the control bundle plus an override flag and needed no recipe dir).

Each was committed **before** its arm solved — the commit subjects say so
outright: *"pre-register duty-scoped state floor (arm B2) before its solve"*
(`74ff852`), *"pre-register the online-hours LSL state leg"* (`e2deaf5`),
*"pre-register the measured CHP BTM repair"* (`3affcaa`). This is the lane's
pre-registration discipline, not stray output.

## 3. Disposition, per dir, on the merits

Rule applied throughout: `frontend/data/backcast/keepers/README.md` **Class-E
point 4** (bundle linkage / parity sweep), with the keep-required carve-out
the point itself provides. The precedent followed is the allowlist's only
pre-existing entries, `miso170_layup_A` / `miso170_layup_B`, which are kept on
exactly this ground — *cited by a committed record as evidence, therefore
legitimately outliving their sidecars*.

**All eight → KEEP-REQUIRED** (`KEEP_REQUIRED_UNMAPPED_BUNDLES`). None was
registered (none is registrable — see §4) and none was pruned.

### 3a. The five spent recipes — kept because pruning kills a live citation

Each is named as the sole input of a reproduction command in a **committed**
PREREG/RESULT doc:

| recipe | citation | produced (registered) |
|---|---|---|
| `nyiso144_arm_recipe` | `PREREG-nyiso144…:162`, `RESULT-nyiso144…:169` | `nyiso144_layup_arm` |
| `nyiso146_arm_recipe` | `RESULT-nyiso146-perplant-min-run-ab…:86` | `nyiso146_perplant_arm` |
| `nyiso146b_armB_recipe` | `RESULT-nyiso146bc…:99` | `nyiso146b_online_arm` |
| `nyiso146b_armC_recipe` | `RESULT-nyiso146bc…:101` | `nyiso146b_reserve_arm` |
| `nyiso146c_armB2_recipe` | `RESULT-nyiso146bc…:100` | `nyiso146c_state_arm` — **the current NYISO keeper** |

**The citations are FAITHFUL, not stale** — measured, not assumed. Each recipe
was diffed against the `meta.json` of the arm it produced (volatile fields
`timestamp` / `git_sha` / `basis_sha` / `environment` / `shared_inputs` /
`highspy_version` excluded):

* `nyiso144_arm_recipe` vs `nyiso144_layup_arm`: **0 differing fields, no key
  asymmetry** — exact.
* the other four differ only by `miso_reserve_online_gated` `null`→`false` (a
  MISO field, NYISO-inert, default drift), plus fields the arm carries that
  the recipe lacks because they **did not exist in `ScenarioConfig` when the
  recipe was declared** (`cc_reserve_duty_split`,
  `nyiso_gas_bridge_plant_min_run`, `nyiso_gas_bridge_online_hours`,
  `nyiso_gas_bridge_state_floor_min_run`). **Every one of those is recorded
  `null` in the arm** — i.e. it took its default — so replaying the recipe
  reproduces the arm.

Deleting these five would therefore convert four committed reproduction
sections into dead references — including the command that reproduces **the
designated NYISO keeper** — for a saving of 100 KB. Against the program's
standing warning that pre-2026-08-16 sha citations are already dead
(`docs/FINDING-history-rewrite-2026-08-16.md`), spending live citations to
reclaim 100 KB is a bad trade. Removal condition recorded in the allowlist:
removable when the citing doc is retired, or its reproduction section is
re-pointed at the registered arm bundle.

### 3b. The three nyiso-147 dirs — a LIVE lane; pruning would destroy an experiment

`PREREG-nyiso147-chp-btm-measured-2026-08-20.md` (committed **today**)
pre-registers a two-arm A/B whose **arms have not yet solved**.
`nyiso147_control` is its control — *"replay of the keeper
`2026-08-19-nyiso-146c-state-scoped` at this session's HEAD … verified
byte-identical P1 zonal prices to the committed keeper hourlies in all three
years before this document was written (max |Δprice| = 0.0)"*. Kill gates
**A-K1** (exactness), **A-K3** (the object), **A-K4** (no new phantom
conduct) and **A-K5** (criteria) are each defined *vs the control*. Deleting
it destroys the reference arm of a pre-registered experiment — the cross-lane
deletion the dispatch warned about.

`git ls-remote --heads origin` shows only `claude/caiso-206-…` and
`claude/ercot-221-…`, so nyiso-147 has **no live branch** — but its branch
merged and its artifacts are dated today with arms outstanding. *Branch
absence is not lane death*, and treating it as such is exactly how a
cross-lane deletion happens.

**Removal condition (explicit, naming the lane):** session **nyiso-147**
clears all three when it registers arms A/B under rule 15 — the control
registers alongside them, exactly as `ercot221_control_A` and
`miso172_control` cleared themselves. If nyiso-147 is abandoned, the lane that
retires it prunes all three in that commit.

## 4. Nothing was registered — and nothing here is registrable

`nyiso147_control` is full-span (2023/2024/2025 hourlies present), so rule 16
`[R-ALLYEARS]` does not block it. It is nonetheless **not** this lane's to
register:

1. It lacks `metrics.json` and `calibration_attestation.json`, which every
   registered NYISO bundle carries.
2. Registration is declared in `PREREG-nyiso147` as **that lane's** act, in
   the same commit as its arms, so the A/B pair renders together.
3. Registering it would trigger the NYISO bench regeneration the PREREG
   discloses as arm A's blast radius (*"the NYISO bench parts for 2023–2025
   regenerate at registration … every registered NYISO run re-scores against
   the truer benchmark"*). A parity-repair lane must not fire that.

The seven recipe dirs are not registrable at all: no run, no metrics, no
payload — there is nothing to register.

## 5. PREVENTION (recommendation only — not built in this lane)

**Nine dead dirs in one cycle is a process defect.** The diagnosis is that the
Class-E sweep has a **classification gap, not an enforcement gap**: it sweeps
every non-`_` dir and calls each one "dead solve output", but two legitimate
non-output classes now live under `results/calibration/` — pre-registered
**recipe dirs** and in-flight **control bundles**. Both are *supposed* to
exist before any sidecar does. The gate therefore fires on healthy artifacts
by design, and the only relief it offers is a hand-maintained allowlist that
grows by one to three entries per A/B session, forever. Its own docstring
warns that a stale entry is "a re-armable hole in the gate" — an allowlist on
that trajectory becomes a junk drawer, and the gate's signal decays.

Ranked recommendation:

1. **Primary — a class-level carve-out in the gate (structural, cheap).**
   Stop enumerating recipe dirs. Exempt, by *property* rather than by name:
   (a) a dir whose only file is `meta.json` — solve input by construction,
   since `run_replay_bundle` reads nothing else — **and** which is referenced
   by some committed `results/calibration/*.md`; failing that reference, it
   fails as today. This is the same "cited by a committed record" test already
   used to justify `miso170_layup_A/B`, promoted from prose to code. It
   removes seven of this cycle's eight failures permanently and every future
   recipe dir with them.
2. **Secondary — a lane-side duty, stated where lanes read it.** The residue
   is then only in-flight controls. Make the pre-registration commit that
   creates a control state its clearing condition, and add one line to the
   `calibration-report` skill's close-out: *"a control bundle registers with
   its arms; if the lane ends without solving them, prune the control in the
   closing commit."* This is a duty, not a check — the honest cadence is that
   an in-flight control is unmapped for hours or days by design.
3. **Not recommended — a pre-merge CI check.** A stricter or earlier gate
   makes this worse, not better: the artifact is legitimately unmapped while
   the lane is mid-flight, so a pre-merge check would block correct
   pre-registration commits and train lanes to skip pre-registration — the
   opposite of what the program wants. The defect is in the classifier, not
   the timing.

Recommendation 1 is one PR against `check_bundle_retention`, no data change,
and would have caught this cycle before it reached the board twice.

## 6. Files changed by this lane

* `scripts/check_registry_payload_parity.py` — eight entries added to
  `KEEP_REQUIRED_UNMAPPED_BUNDLES`, each with citation and removal condition.
  No logic change.
* `results/calibration/FINDING-ws6-parity-nyiso-recipe-dirs-2026-08-20.md` —
  this record.
* `docs/handoffs/audit-program-director-board-2026-08.md`,
  `docs/model-audit-release-plan-2026-08.md` — WS6 rows updated from
  "gate RED / RE-OPENED" to green, pointing here.

No solve ran. No keeper moved. No run was registered or pruned. No mechanism
changed, so no mechanism-matrix cell moved (rule 28).
