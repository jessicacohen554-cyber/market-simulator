# FFR-§W1-X — Wave-1 close: attestations, the single cache-epoch bump, the held CI job

**Session:** §W1-X of `docs/forecast-readiness-prompt-pack-2026-07.md` (the Wave-1 close
checklist, four items). Branch `claude/wave1-close-attestations-epoch-7811lz`, authored off
`origin/main` @ `a92ae97` and **rebased onto `ee44a37`** before push (§9), 2026-08-02.
**No LP solve anywhere** — every number below is computed from committed artifacts, config
re-hashes, and per-merge git diffs.

**Verdict: GREEN-LIGHT for FFR Wave 2 and Wave FH's FH-4/FH-5.** All seven Wave-1 lanes are
merged; the three required attestations are present and re-confirmed against the *merged*
tree and the *current* keeper set; the single cache epoch is taken; the three-part
regression audit passes on all three limbs; FFR-1E's held parity job is in CI. Five findings
are recorded (§5) — one repaired here as a root cause, the rest handed on with their owning
lanes named. None blocks Wave 2.

---

## 0. Headline

| §W1-X item | Verdict | Where |
|---|---|---|
| 1. Attestations present & sound (1A-arm-1 / 1B / 1D) | **PASS ×3**, one doc arithmetic slip | §1 |
| 2. Single cache-epoch bump | **TAKEN 2026-08-02** (`results/cache.py` ledger) + root-cause repair | §2 |
| 3. No band widened / default moved / out-of-training year touched | **PASS / PASS / PASS** | §3 |
| 4. FFR-1E's held `forecast-parity-guard` job | **LANDED** | §4 |
| 5. Green-light Wave 2 + FH-4/FH-5 | **GREEN** | §6 |

Merges re-verified at this HEAD (all present on `origin/main`):
FFR-1A `1eeef40` (#3248) · 1B `255c015` (#3239) · 1C `50c5193` (#3243) · 1D `24665ee`
(#3245) · 1E `f5c462b` (#3246) · PA `5118288` (#3247) · PB `64905b4` (#3244).

Keepers read from `frontend/data/backcast/keepers/<ISO>.json` at this HEAD — unchanged from
the dispatch brief, and **none moved during this session**:
ERCOT `2026-08-01-ercot149-gas-event-cap` · PJM `2026-07-31-pjm-143b-hy-level` ·
CAISO `2026-07-31-caiso-151-firm-selfsched` · NYISO `2026-08-01-nyiso109-zonal-margin-anchor` ·
NEISO `2026-07-31-neiso-72-hy-window` · MISO `2026-07-31-miso-109b-hy-level`.

---

## 1. Attestation audit — three lanes, explicit verdicts

Method, stated up front because it is what makes the verdicts falsifiable. Only
`ScenarioConfig` determines a cache key, so exactly three Wave-1 merges could move one:
1B, PB and 1D touched `config/scenarios.py`; 1A, 1C, 1E and PA did not (`git diff --stat`
per merge, verified). For each of those three merges I reconstructed all **six current
keepers'** committed `run_config.json` `scenario_config` into a `ScenarioConfig` and hashed
it at the merge's first parent and at the merge itself, in an identical path context (the
`cache_key` path-folding is checkout-sensitive when `data/` is absent, so a cross-context
absolute comparison is not evidence — every comparison below is within one context).

| merge | lane | ERCOT | PJM | CAISO | NYISO | NEISO | MISO |
|---|---|---|---|---|---|---|---|
| `255c015^1` → `255c015` | 1B | = | = | = | = | = | = |
| `64905b4^1` → `64905b4` | PB | = | = | = | = | = | = |
| `24665ee^1` → `24665ee` | 1D | = | = | = | = | = | = |

`=` means the 16-char key is byte-identical across the merge. The 1D row was additionally
re-run in the **main checkout** (swapping `scenarios.py` to `eb69a2b`'s blob and back, with
a sha256 restore check): all six keys identical either side —
`{CAISO d78ed6e7b664d3d2, ERCOT d22a8089080aa1cc, MISO 0b6dda717f9cea44,
NEISO 899401f3b6c3f8a6, NYISO 939e5c82de1c8c77, PJM d18a4f90f5694aec}`.

**No keeper moved. Rule 11's stop-the-line contingency was not triggered.**

### 1.1 FFR-1A arm 1 — §4.1 byte-identity — **PASS (survived the merge intact)**

§4.1 attests the ledger-only arm as dispatch-inert on two probe ISOs: NEISO and PJM T1-F
2026–2030, identical config → identical cache key `ff63ca9a0a1d65c6`, every value column of
every `year_<y>.parquet` element-wise equal, objective equal to the last decimal, floor-
retention JSONs byte-identical, and `meta_diffs=['build_time','solve_time']` only.

Re-confirmed at HEAD: 1A touched no `ScenarioConfig` field (its merge's `scenarios.py`
diff is empty), so its keeper impact is nil *by construction* — capacity evolution runs
only in forecast mode. Its four source files (`capacity_evolution/{evolve,retirements}.py`,
`results/evolution_ledger.py`, `scripts/check_forecast_invariants.py`) have been touched
once since its merge, by FFR-1D's own FR-24 commit `93c56c8` to the invariants checker —
1D's file by the wave's ownership map, not a conflict with the attestation.

### 1.2 FFR-1B — §3 byte-identity on all six keepers — **PASS (re-confirmed on the current keeper set)**

§3 attests 102/102 identical hash/key comparisons across the six keeper configs × three
keeper years, over `cache_key()`, the `generators_to_fleet_arrays` availability/`min_gen`
surface and the full `ReserveDesign` surface, threaded both `sim_year=Y` and the legacy
`None` fallback.

Two things needed re-confirming, because the attestation was written against the keeper set
as it stood on 2026-08-01 and **four keepers have moved since** (ERCOT→149, CAISO→151,
NYISO→109, NEISO→72):

* **Cache-key half, re-run on today's six keepers:** identical across the 1B merge (table
  above). The scratch probe `ffr1b_byte_identity.py` was not committed, so the
  input-surface half is not re-runnable here; its structural argument is, and it holds —
  every changed line is a `weather_year → solve_year` substitution whose operands are
  pinned equal in backcast, a `mode=="backcast"` gate, or a comment/new-error path
  unreachable in backcast.
* **Post-merge drift on 1B's files:** `data/fleet/arrays.py` was touched once since, by
  ERCOT-149 (`73e237a`). Read: the change is confined to the measured DAM-award event-cap
  `min()` block (widening its class scope from COAL to the DAM-covered gas classes) — a
  backcast-only overlay path, disjoint from 1B's availability-aging and Martin Lake seams.
  `eia860.py`, `reserves/spec.py` and `results/scarcity.py` are untouched since the merge.

### 1.3 FFR-1D — the rebase re-confirmation — **PASS, with one doc arithmetic slip**

1D's PR was rebased after its findings doc was written (base `255c015` → `6e98263`; diff
30 files/+2,136 → 34 files/+2,234), so its attestation described a pre-rebase tree. Its
merged `scenarios.py` content was therefore re-derived from the merge itself
(`git diff 24665ee^1 24665ee -- src/market_sim/config/scenarios.py`, 138 insertions /
3 deletions) and compared line-by-line against what §3/§4/§5 declare:

| declared | in the merged tree | verdict |
|---|---|---|
| §5 dedupe: two duplicate `_CACHE_KEY_OPTIONAL_FIELDS` literals removed | the only 3 deleted lines are `nyiso_li_locational_reserve`, `nyiso_incity_commitment_obligation` and their comment | matches |
| §4 `_BACKCAST_ONLY_OVERLAY_FIELDS` + the `outage_source="historic"` value + the forecast raise | present, verbatim | matches |
| §3 `correlated_forced_outage` backcast coercion | present, one line, `mode=="backcast"` only | matches |
| "**No `ScenarioConfig` field was added or deleted**" | 668 fields both sides; zero added, zero removed, zero default changed | matches |

**The scenarios.py reconciliation against FFR-1B specifically — the point of the
re-check.** 1D §9 says 1B's `__post_init__` AS-guard hunk "did not land here … It lands in
FFR-1B after this merges". In the event 1B merged **first** (`255c015`, 2026-07-31) and 1D
rebased onto it. The merged tree carries **three** `ercot_as_forward_requirement` guards:
the two pre-existing endogenous-storage / endogenous-thermal ones, and 1B's bare-co-opt
FR-12 guard last (so the specific messages keep firing) — exactly as 1B's own doc describes
its single hunk (`git diff 255c015^1 255c015` shows it as 1B's *only* `scenarios.py`
change, 22 insertions). 1D's merge adds nothing in that region. **The reconciliation is
clean: every guard and coercion in the merged `__post_init__` is attested by exactly one
findings doc, and nothing is attested by none.**

**The one slip.** 1D §4 prose says the family is "36 fields"; the family as merged holds
**37**, and 1D's own §4 table enumerates all 37 (checked programmatically: the table's
field set and the dict's key set are equal, zero symmetric difference). A prose miscount,
not a content divergence — the guarded surface is exactly what the doc lists. Recorded, not
escalated. *(The family is 38 as of this session — see §5.1.)*

---

## 2. The single cache-epoch bump — what it concretely did

### 2.1 Establishing the mechanism before acting

There is no `CACHE_EPOCH` constant in the repo, and the "documented cache epoch" named at
`results/cache.py:24` is an operator policy (refactor-consolidation plan §7 H, compat
clause 2 — where it is still listed as an *unimplemented* operational item). The concrete
mechanism the policy intends already exists, on two distinct surfaces, and one of them has
been exercised once before:

* **Key advances** are recorded at `PINNED_DEFAULT_CACHE_KEY` in
  `tests/regression/test_persisted_identity.py`, as a dated cause block above the literal.
  The precedent is the **2026-07-27 bump `edbc1b103207170a` → `603c2498bf71d21d`**
  (owner-authorized, path-portability re-key). That ledger also records the *negative*
  case explicitly — the 2026-07-23 gas-offer fields were registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` so "the default cache_key stays pinned … **no advance**".
  **A key movement caused by an unregistered new field is therefore not an epoch bump; it
  is a registration defect.**
* **Same-key invalidations** — a behavior change that leaves every key unmoved — had no
  surface at all. That is precisely the FR-1/2/7/8 case, and it is the gap §W1-X is for.

I did **not** add an in-repo epoch token. A `CACHE_EPOCH` inside `ScenarioConfig` would move
every config's key including the backcast keepers (solve-affecting under rule 24, and a
rule-28 matrix row for something that is not a mechanism); one outside the key would be
inert. Both are worse than a dated ledger a human reads. *(If a future session wants
detectability rather than discipline, the non-config-field option is stamping the epoch into
the per-bundle `config.yaml` `cache.save_result` already writes and refusing reuse on a
stale stamp — a behavior change, and a proposal, not something taken here.)*

### 2.2 The bump

**Epoch 2026-08-02 — FFR Wave-1 forecast fixes (FR-1, FR-2, FR-7, FR-8)**, recorded as a
"Cache-epoch ledger (same-key invalidations)" section in `src/market_sim/results/cache.py`'s
docstring, immediately under the policy paragraph that calls for it. The docstring now also
states the division of labour between the two surfaces above, so the next session does not
have to re-derive it.

| finding | lane | effect on a cached forecast bundle |
|---|---|---|
| FR-1 | 1A arm 1 | dispatch-inert, but every pre-fix `evolution_<year>.json` lacks its `confirmed_derates` rows and the `confirmed`/`announced` reason split |
| FR-2 | 1A arm 2 | **behavioral** — partial-year exits complete in year+1; fleet MW, dispatch and prices move from the exit year+1 onward |
| FR-7 | 1B | **behavioral in every forecast year** — availability aging keys on the solve year; entrants no longer carry a negative age |
| FR-8 | 1B | **behavioral for every T1-X leg** — the measured 2025 Martin Lake derate can no longer leak into a `weather_year=2025` pin |

**Invalidated:** every cached bundle produced in **forecast mode** (`mode="forecast"`,
including `hindcast=True` capacity-hindcast and T1-X crossover legs) at a commit before the
Wave-1 merges — **any solve year, not only 2026+**, because FR-8 reaches a crossover's
realized 2023–2025 legs too. This subsumes the pack §0a-6 debt (the `scenarios.py` field
additions since the audit): those are now re-keyed by §2.3 rather than carried.

**NOT invalidated:** backcast caches and every keeper bundle. FR-7/FR-8 are mode-gated,
FR-1/FR-2 run only under forecast-mode capacity evolution, and §1's table attests every
keeper key unmoved across all three `scenarios.py`-touching merges.

**Purge:** the ledger carries the copy-pasteable command (the per-ISO cache roots plus the
contents of every forecast `--out-dir` cache, preserving the tracked `.gitignore`
keep-files). Executed in-session; **verified zero `year_*.parquet` anywhere under
`results/` afterwards** — this container was cloned fresh after the Wave-1 merges, so there
was nothing stale here. The command is in the ledger for checkouts that predate 2026-08-02.

### 2.3 The root-cause repair the bump surfaced (rule 11)

FFR-1B §6 and FFR-1D §8.2 both handed the stale `PINNED_DEFAULT_CACHE_KEY` to this session,
and 1D was explicit that re-pinning is the wrong remedy. Root-caused by walking the default
key across every `scenarios.py` commit since the pin was last set:

```
626217e 603c2498bf71d21d   <- the pin
a9e5b18 603c2498bf71d21d
c633dac 8161b094a391de90   <- PR #3207, miso-111: +coal_prb_committed_dispatchable
5abbc1d 8161b094a391de90
ef607f9 8161b094a391de90
12659bb 0e9fce2fb55b889f   <- PR #3232, miso-112: +coal_prb_committed_split
…       0e9fce2fb55b889f   (through origin/main a92ae97)
```

Both fields ship **default off** and both promise "Default off — every existing keeper
byte-identical" in their own docstrings. **Neither was registered in
`_CACHE_KEY_OPTIONAL_FIELDS`**, so each entered the hash at its default and moved the
default key — orphaning every on-disk cache twice and reddening four pinned-literal tests
across two BLOCKING CI jobs (`refactor-guards`, `fast-tests`). This is occurrences **six and
seven** of the exact failure `scripts/check_cache_key_registration.py` was built to prevent;
neither PR was caught because the guard's new-field check only fires with `--base`, on the
PR that adds the field.

Repaired by registration — the remedy that script's docstring names, and the one the
`test_persisted_identity` ledger's own 2026-07-23 precedent applied:

* default key **restored to the pin `603c2498bf71d21d`**;
* an armed run still hashes distinct (`coal_prb_committed_split=True` →
  `f7bbda26e4ca33ad`), which is correct — it is a different scenario;
* the four failing tests pass (27/27 across the three pinned-literal modules);
* MISO / NEISO / PJM keeper reconstructions return to their **exact** pre-miso-111 keys
  (`4cdc9a60…`, `f102a330…`, `33ee0065…`) — the orphaning is undone, not accepted.
  ERCOT / CAISO / NYISO do not, and should not: those three keepers are newer than
  `a9e5b18` and arm fields that did not exist then.
* No default moved, no field added or deleted, no solve path touched. `check_mechanism_matrix`
  and `check_cache_key_registration` both green.

---

## 3. Wave-1 regression audit — three limbs, with the evidence

Scope: the seven merged Wave-1 lanes, audited **per merge** (`M^1` vs `M`) rather than over
a commit range, because ~15 non-Wave-1 calibration merges are interleaved and a range diff
would attribute their changes here.

### (a) Did any session widen a band? — **PASS**

Evidence checked, not asserted:

1. Every removed (`-`) line across all seven merges under `src/`, `scripts/`, `tests/` and
   `.github/` containing a numeric literal was read. There are 41; none is a loosened
   tolerance. They fall into three groups: re-indented-but-unchanged assertions (1C's
   `accredited_firm_capacity_mw` values `1_281.7 / 3_371.0 / 567.0` are byte-identical
   either side), PB's source-doc/URL prose, and 1D's relocation of
   `MAX_UNAUTHORIZED_SOLVE_YEARS = 5` from `scripts/lib/schedulable.py` to
   `src/market_sim/config/schedulable.py` (**value re-verified 5 at HEAD**; `scripts/lib`
   now re-exports it).
2. `scripts/golden_forecast_bands.py` — the one band file any lane touched (1D, +31) —
   changes **no band**: the diff is two `assert_config_schedulable` calls and their
   `--full-solve-authorized` flags, i.e. the §2.1b cap applied to a 15-solve-year reseed.
3. The one assertion 1D *removed* (`assertNotAlmostEqual(fc_frac, …)` in
   `test_summer_availability_constants.py`) was replaced by a **stricter** one: the config
   now `raises` where the overlay previously silently no-opped.
4. The one new exemption in the wave is 1D's `tests/golden/staleness_waiver.json` — and it
   is a net *tightening*: it introduces a guard that did not exist (FR-26: the golden band
   check was `slow`/env-gated and produced no red anywhere), and hard-fails on
   **2026-10-31**. A dated, owner-routed deadline is not a widened band. Flagged so the
   expiry is not a surprise.

### (b) Did any session move a default outside its declared guard/coercion/deletion set? — **PASS**

The decisive check is mechanical: for each of the seven merges, dump every `ScenarioConfig`
field's default (resolving `default_factory`) at `M^1` and at `M`, and diff.

```
1C: added=[] removed=[] changed={}      1B: added=[] removed=[] changed={}
PB: added=[] removed=[] changed={}      1E: added=[] removed=[] changed={}
PA: added=[] removed=[] changed={}      1A: added=[] removed=[] changed={}
1D: added=[] removed=[] changed={}
```

**Zero fields added, zero removed, zero defaults changed, across the entire wave** (668
fields throughout). PB's `scenarios.py` diff is the only one that looks like a default
change and is not: 26 insertions / 6 deletions, **all comment**, replacing the IRA
step-year provenance caveat with primary-statute verification while the values
`2033/2034/2035/2036` stay byte-identical — which is exactly what its findings doc claims.

Beyond `ScenarioConfig`: 1C's `config/{capacity_market,constants}.py` additions are new
constants (`HYDRO_ACCREDITATION_CREDIT_BY_ISO` and its facade re-export), each a cited
ISO-published accreditation factor; no existing constant's value moved in any merge.

### (c) Did any session solve, score, or register an out-of-training year? — **PASS**

Every artifact any Wave-1 merge wrote under `frontend/data/` or `results/`:

* **15 registered sidecars**, all under `frontend/data/hindcast/` (the forecast-family
  namespace), never the backcast registry. Every one reads `meta.mode = "forecast"` with
  `start_year ≥ 2026`: 1A's six T1-F legs (2026–2030) + two ERCOT T0 legs (2026–2028), 1B's
  NEISO T0 (2026–2028), 1C's six adequacy probes (2026–2026), 1D's re-seeded
  `invariant-failures.json`. Each window is ≤ 5 solve-years (§2.1b).
* **12 `results/ffr1c/*` files**, `full_horizon_summary.json` + `evolution_2026.json`, all
  `start_year = end_year = 2026`.
* **Exactly one touch under `frontend/data/backcast/`** in the whole wave: 1D's
  regeneration of `status/MISO.js`. Semantically diffed key-by-key (JSON payload parsed,
  recursive compare): **three changes total** — the `generated` timestamp, `share_pp
  −0.96 → −0.95`, `vintage_gap_twh −0.205 → −0.204`. No criterion, no status, no
  determination, no keeper. Exactly what 1D §7c declares.
* **No `frontend/data/backcast/keepers/**` file was touched by any Wave-1 merge**, and none
  by this session.
* No backcast solve at all: zero forecast-mode `run_config.json` exists in the repo, and
  no Wave-1 merge added a `results/calibration/` bundle.

The **holdout freeze** (`holdout-freeze.json`, held 2026-07-26) was never engaged: it blocks
out-of-training *backcast* years, and every Wave-1 solve is forecast-mode 2026+. This
session solves nothing.

---

## 4. FFR-1E's held CI job — landed

`.github/workflows/ci.yml` gains the `forecast-parity-guard` job **verbatim from
`ffr-1e-forecast-parity-check-2026-07-31.md` §6** (job id, name, `timeout-minutes: 5`,
stdlib-only `python3 scripts/check_forecast_parity.py`, no `uv sync`). Placed next to the
other artifact-level guards, after 1D's `forecast-invariant-artifacts`.

Re-verified before wiring, **against today's keeper set** (four of six moved after 1E was
written): 1.0 s wall, **exit 0**, `6 keeper postures; 0 unaccounted, 8 filed gaps, 0
registry failures, 0 errors`. The eight FILED gaps report but do not fail; `--strict-gaps`
flips that in the session that closes them. **Nothing was wired or fixed** — the gaps keep
their own session, per 1E's charter and this session's brief.

**Path filters — deviation, stated rather than buried.** 1E §6 asks to extend the
`on.pull_request.paths` list with `src/market_sim/**`, `scripts/run_calibration*.py`,
`scripts/lib/forecast_parity_registry.py` and `frontend/data/backcast/keepers/**`. Checked
glob by glob against the list as it now stands: all four are already subsumed —
the first three by the existing `src/**` and `scripts/**`, the fourth by
`frontend/data/backcast/**`. Adding narrower duplicates would change no trigger and only
add noise, so **no filter edit was made** and the reasoning is recorded inline in `ci.yml`
next to the job. 1E's §6 was written before it could see 1D's merged filter block.

---

## 5. Findings

### 5.1 REPAIRED here — `ercot_dam_availability_gas_event_cap` was missing from the FR-11 backcast-only family

`ercot_dam_availability_coal_event_cap` is in 1D's `_BACKCAST_ONLY_OVERLAY_FIELDS`. Its
literal sibling `ercot_dam_availability_gas_event_cap` — same measured 60-Day DAM-award
record, same `min()` block in `data/fleet/arrays.py`, class scope merely widened to the
DAM-covered gas classes — was **not**, because it landed with ERCOT-149 (`73e237a`,
2026-08-01) after 1D's family was written. That left a one-flag rule-13 hole in a guard
whose entire value is that the family be complete.

Added (family 37 → 38), with the timing cited in-comment so it is not mistaken for 1D's.
Blast radius nil, verified: **no committed forecast-mode `run_config.json` exists at all**,
and the only config arming the field is the backcast ERCOT keeper. Confirmed the guard
raises in forecast and accepts in backcast; default key unmoved at `603c2498bf71d21d`; the
101 config-guard + persisted-identity tests pass.

This is the mechanism-timing gap 1D's own §4 anticipates ("if a session establishes that
[a field] reads a year-keyed artifact, it belongs in the family") — and it is a standing
hazard, not a one-off: **the FR-11 family has no CI guard of its own.** A future measured
overlay added by a parallel lane will silently miss it the same way. Worth a checker in the
L-INP lane (the natural home is alongside `check_cache_key_registration.py`, which already
proves the pattern works).

### 5.2 FILED — three post-1D fields whose family membership is a judgement call

Not decided here; each belongs to its own lane. All three are default-off, and none is
armed in any forecast-mode config (there are none):

| field | lane | the question |
|---|---|---|
| `caiso_firm_import_selfsched_clip` | CAISO (caiso-151) | a measured price-insensitive intertie *ceiling* — capability envelope (admissible, rule 14) or year-keyed record? |
| `coal_prb_committed_split` | MISO (miso-112) | measured per-plant night loading p50 — its declared status is "year-static plant conduct, same as `coal_takeorpay_share`", which reads admissible; but its family siblings `coal_prb_mustrun_override` etc. *are* guarded |
| `gas_offer_margin_zonal_anchor` / `_anchor_by_zone` | NYISO (nyiso-109) | 1D §4 states offer-curve tuning knobs are contained by rule 25 + the run_config registry, **not** by mode — so these are probably correctly out; recorded so the reasoning is not re-derived |

### 5.3 FILED — FFR-1D §4 prose says "36 fields"; the family it shipped has 37

Documentation only; §1.3 has the check. Not corrected in 1D's doc (it is that session's
record); corrected here.

### 5.4 FILED — pre-existing reds on `origin/main`, none caused here (rule 11)

Found while sweeping `tests/unit/config`, `tests/scoring`, `tests/regression`,
`tests/unit/data/test_{outages,fleet}.py` (1,691 passed, 6 skipped, 40 subtests). **Every
one reproduces with `scenarios.py` swapped to the pristine `origin/main` blob** (verified
by file swap + sha256 restore, at both `a92ae97` and `ee44a37`), and this session touched no
test file. Two classes, and the distinction matters for whoever picks them up:

**(i) Two genuine reds.**

| test | failure | reading |
|---|---|---|
| `tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` | `assert _marker_state("PJM")["marker"] == "none"` → got `"complete"` | the test still encodes `complete = {NEISO, NYISO}`; **PJM was declared 2026-07-31** (pack §0a-2). Stale test, live marker file — the fixture needs re-deriving from `calibration-complete.json`, not re-hardcoding. Owner: the governance lane (FFR-2D / 3A). |
| `tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` | an unknown-ISO nuclear availability map returns per-unit 8760 arrays instead of empty | unrelated to any Wave-1 lane; predates them. |

**(ii) Four environment-dependent failures in the same battery file** —
`test_walk_inputs_trivial_single_year`, `test_resolve_report_no_hard_fail_full_horizon`,
`test_ercot_confirmed_horizon_is_reported_not_failed`,
`test_build_registration_scorecard_no_iso_gate_open`. All four fail on
`ERCOT:confirmed_retirements [MISSING] clean partition unbuilt` — `data/clean` is derived
and **gitignored**, and this container was cloned fresh without running the curation. They
are *order-sensitive too*: the same four passed in the broader `-n 2` sweep (where another
module redirects `CLEAN_DIR`) and fail when the file runs alone. That order-sensitivity is
itself worth a look by the lane that owns the battery — a test whose verdict depends on
which siblings ran with it is not a guard — but it is not a §W1-X item and not a Wave-1
regression.

Class (i) is in the **fast tier**, so `fast-tests` is red on `origin/main` independently of
the four pinned-literal failures §2.3 repairs. Nothing here is fixed in this session: (i) is
a governance-lane fixture plus a data-lane defect, (ii) is provisioning. Recorded so the
next session does not attribute any of it to Wave 1 or to this close.

### 5.5 CARRIED — the golden staleness waiver expires 2026-10-31

`tests/golden/staleness_waiver.json` hard-fails
`test_golden_fixture_config_identity_is_current` on that date. Resolving it means executing
owner decision **D-7** (a 15-solve-year reseed). Naming it here so it lands on a wave plan
rather than surfacing as an unexplained red in an unrelated session.

---

## 6. GREEN-LIGHT

**FFR Wave 2 (2A, 2B, 2C, 2D, 2E): GREEN.** Its gate is "all Wave-1 lanes merged + the
§W1-X close checklist". All seven are merged (§0), all four checklist items are discharged
(§0 table), and the attestations hold against the merged tree and the current keeper set.
Two things Wave 2 must carry:

* **2A owns the first re-solve on the new epoch.** Its T1-X 2023–2027 legs for ERCOT/PJM/
  MISO are exactly the runs the epoch invalidates (FR-8 reaches their realized years), so
  they must be solved **cold** — run the §2.2 purge on any checkout predating 2026-08-02
  before the first leg. The quarantine still applies: scoring stops at 2025.
* **2B reuses committed BEFORE legs.** Those legs predate the epoch. A leg may be reused
  only if FR-1/2/7/8 provably do not touch it; a forecast leg with capacity evolution or
  any aging-sensitive availability is not such a leg. When in doubt, re-solve.

**Wave FH — FH-4 and FH-5: GREEN.** Their gate was explicitly "W1 merge + §W1-X epoch bump
(FR-7/FR-8 corrupt weather-pinned historic runs)". Both fixes are merged and the bump is
taken and dated, so FH-4's 3 solve-yr × 6 ISOs × 2 arms and FH-5's 4 solve-yr may proceed —
**on cold caches**, which is the whole point of the gate. Rule 12 concurrency stands: ≤ 2
concurrent invocations, PJM and MISO never co-run.

**Nothing filed in §5 blocks either.** §5.1 is repaired; §5.2/§5.3 are records; §5.4 is a
dated deadline two waves out.

---

## 7. Files

| file | change |
|---|---|
| `src/market_sim/config/scenarios.py` | `_CACHE_KEY_OPTIONAL_FIELDS` += the two miso-111/112 PRB fields (root-cause pin repair, §2.3); `_BACKCAST_ONLY_OVERLAY_FIELDS` += `ercot_dam_availability_gas_event_cap` (§5.1). No field added/removed, no default moved. |
| `src/market_sim/results/cache.py` | the cache-epoch ledger + the two-surface policy statement (§2) |
| `.github/workflows/ci.yml` | `forecast-parity-guard` job (§4) |
| `docs/forecast-readiness-prompt-pack-2026-07.md` | new §0c close report (beside the parallel manager session's §0b, which it discharges rather than replaces), the header pointer, the W1/WFH wave-map gate cells, and §W1-X marked discharged item by item |
| `docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md` | this doc |

## 8. What this session did NOT do

* **No solve, no LP, no scoring.** Every number is from committed artifacts, config
  re-hashes and git diffs.
* **No dashboard registration** (rule 15): no run was produced, on either namespace.
* **No `frontend/data/backcast/keepers/**` touch.** No keeper moved.
* **No out-of-training year** touched, in any mode.
* **No new GitHub Actions workflow** — the existing `ci.yml` was extended (private repo,
  billed minutes).
* **No `ScenarioConfig` default changed**, and no field added or deleted — so no rule-28
  matrix row is triggered (`check_mechanism_matrix` green; duties (a)–(d) not engaged: no
  mechanism was proposed, tested or armed).
* **Wired none of FFR-1E's eight filed parity gaps** — they keep their own session.

---

## 9. Rebase onto `ee44a37` (2026-08-02)

Authored against `a92ae97`; rebased onto `origin/main` `ee44a37` before push (10 commits:
FFR-2D #3262, the forecast-readiness *manager* session #3263, caiso-153 #3261, pjm-144
#3264).

**One conflict, in `docs/forecast-readiness-prompt-pack-2026-07.md`.** The manager session
landed its own **§0b** (`1740a42`) at the same insertion point as mine — recording Wave 1 as
merged 7/7 and naming §W1-X *the live gate, not yet run*. Both sides are right about
different moments, so **both are kept**: its §0b stays as the pre-close state record (the
lane/PR/findings-doc table, the acceptance highlights, the keeper-drift table, the release
order), and this session's block moves to **§0c**, the discharge of the §0b-2 gate. Where
they disagree, §0c wins, and the three §0b items the close supersedes (2 "not yet run",
5 "FH-4/5 remain gated", 6 dispatch state) are struck through in place with a pointer,
rather than rewritten — the brief §W1-X was dispatched against stays legible. The pack
header now names both. **No content from either side was dropped.**

Its §0b-2 also flagged the two items beyond the checklist's four that it wanted §W1-X to
carry; both are closed here — FFR-1E's parity job is in `ci.yml` (§4), and 1D's pre-rebase
attestation is re-confirmed against the merged tree (§1.3).

**Re-verified at the new base**, since all of it is load-bearing:

* All six keepers **unchanged** at `ee44a37` (pjm-144 is a pre-registration, not a
  promotion), so §1's attestation table stands as written.
* **No new-main commit touched `scenarios.py`**, so §2.3's repair holds: default key
  `603c2498bf71d21d`, registry 112/112 resolving, overlay family 38.
* `check_cache_key_registration`, `check_mechanism_matrix`, `check_forecast_parity`,
  `check_forecast_invariants --sidecar-dir`, `audit_keepers --check`, `ruff check` and
  `ruff format --check` all green; the five pinned-literal / config-guard modules pass
  132 tests + 17 subtests.
* §5.4's pre-existing reds **still fail at `ee44a37`** — not fixed by 2D or any other
  merge, and re-attributed there by swapping `scenarios.py` to the pristine `ee44a37` blob:
  identical failure set either side, so still not this session's.
