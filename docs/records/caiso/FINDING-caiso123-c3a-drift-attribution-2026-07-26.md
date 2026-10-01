# FINDING — caiso-123: the C3a-2025 basis drift IS the CAISO outage extract — in the states caiso-122 never tested. The extract was **derived-not-committed until 2026-07-24**; the keeper solved on a **session-local PARTIAL derivation** whose bytes were never committed and which **no full derivation regenerates**; the 07-24 backfill committed a materially heavier full derivation (**CC_REGULAR +618/+688 MW avg removed, 2024/25**) and every later solve reads it. Confirmed by a same-HEAD extract A/B: **+1.24 % λ / CC_REGULAR −0.49 TWh / import +0.42 TWh** from the extract content alone. The caiso-120 "guard-corrected extract" re-tune trigger conflated this with the guard (guard's own isolated effect: **−0.18 %, favourable**) and is WITHDRAWN-AS-STATED (2026-07-26)

**Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. Nothing registered
(both arms are single-year throwaway probes under rule 16's diagnostic clause,
gitignored in `results/probes/`). The lane's C3a-2025 blocker is now
attributed; whether it re-tunes or waits on the extract over-count freeze lane
is an owner/charter call (§6).**

---

## §1 — the pre-drift basis, established by measurement

The keeper's recorded provenance cannot anchor anything (caiso-122 §1:
`git_sha abb0fcd` unreachable, `timestamp` date-hybridized by replay). The
basis was recovered from committed bundle evidence and main history:

1. **`caiso119_base_A/hourly/`** (committed `dd6f602`) — the keeper's exact
   recipe, no delta, at caiso-119's session HEAD `f28340b` (2026-07-24
   evening): λ-2025 **+1.55 %** above the keeper, CC_REGULAR −0.44 TWh /
   import +0.41 TWh. **The full drift existed one day after the keeper
   solved.** (`caiso119_minload_B` cross-checks: its +0.89/+0.76/+1.38 %
   minus caiso-121's measured min-load effect reproduces the caiso-122 drift
   +0.50/+0.99/+1.41 % within 0.08 pp per year.)
2. **`run_config.json` deep-diff** keeper vs caiso-122 arm: every difference
   is the intended min-load delta, later-added default-off fields, or
   provenance. No registered tunable moved (rule 24 `[R-REGISTRY]` holds).
3. **`meta.shared_inputs` content hashes** (eia930/eia923/campd parquets)
   are identical across the keeper and every 07-24…07-26 bundle — the
   shared-input layer never moved. (The derived outage extract is NOT in
   that hash set; see §7.)
4. The keeper session (branch `claude/gas-offer-net-revenue-isos-1px5vg`,
   solve finished 07-23 22:29 UTC, clean tree) merged as PR #2824
   (`2895bbe75`, 23:21). The CAMPD outage backfill landed the next day in
   two merges: PR #2842 (`421596f77`, 07-24 05:17, carrying `59f8bc30d`
   which **created** `data/raw/campd-unit-outages-CAISO.csv`) and PR #2844
   (`c95f98c`, 17:34, carrying `49e85fb4a` "re-derive CAISO in full (owner
   instruction)" — **+642 rows, 0 deletions**, every inserted row a
   2023–2025 window, 504 of them CC_REGULAR, ~7,900 window-days, only 1 %
   overlapping an existing same-unit window).

## §2 — the load-bearing discovery: the extract was derived-not-committed

At the keeper's merged tree (`2895bbe75`) **no `campd-unit-outages*.csv`
main extract exists anywhere in the repo — for any ISO** (only the
maxgen-MISO / short-MISO / short-PJM companions). `git log` confirms
`data/raw/campd-unit-outages.csv` and the per-ISO files were **first
committed by `59f8bc30d` on 07-24**. Before that, every session derived its
own extract locally (`scripts/data/derive_campd_unit_outages.py`, last
changed 07-18) and the file was untracked. The keeper DID carry an overlay
(caiso-122 §3: CC_CHP r=0.99343 vs overlay-ON, ~6,950 derated hours) — from
its own container's derivation, whose bytes died with the container.

**The keeper's derivation was PARTIAL.** Re-running the keeper-era script
(worktree at `2895bbe75`, byte-identical `campd-unit-level` raw) reproduces
the **full** detection — in-window mass identical to the post-"re-derive in
full" committed state (blob `3dc01fae`) to 0.1 MW. Yet the keeper's λ and
class hourlies are inconsistent with that state (+1.60 % away) and closest
to the **light partial** `e40847c` state (#2842's 04:45 derivation — itself
superseded the same day by the owner-ordered full re-derive):

| keeper's committed hourly vs | CC_REGULAR r / MAD | CC_CHP r / MAD |
|---|---|---|
| arm K (light `e40847c` @HEAD) | 0.99594 / 96 MW | **0.99858 / 2.4 MW** |
| base_A (heavy full @f28340b) | 0.99328 / 186 MW | 0.99489 / 16.4 MW |

The keeper's availability envelope is e40847c-class. Its exact bytes are
**unrecoverable** — and, decisively for the lane: **no full derivation (the
keeper-era script or today's, guard on or off) regenerates an envelope that
light.** The keeper's C3a-2025 PASS rests on an input state the pipeline
cannot reproduce — a rule-13 `[R-MEASURED]` reproducibility failure baked
into the committed keeper.

## §3 — the extract-state λ ladder (2025, CA demand-weighted, one formula)

In-window derate mass (avg removed MW, CC_REGULAR / total):

| extract state | rows | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| light partial `e40847c` (#2842) | 4,497 | 3,007 / 3,944 | 3,387 / 3,947 | 4,208 / 4,864 |
| full re-derive `3dc01fae` (#2844) | 5,139 | 3,516 / 4,559 | 4,261 / 4,856 | 5,184 / 5,881 |
| keeper-era script, full run (blob `8bf3ccd`) | 1,995* | 3,516 / 4,559 | 4,261 / 4,856 | 5,184 / 5,881 |
| HEAD (guard-on, `6a8f285`) | 4,329 | 3,294 / 3,703 | 4,005 / 4,513 | 4,896 / 5,548 |

*2023–25 span only (the old script's default); in-window mass identical to
the full re-derive — the detector core never changed, #2842's file was
simply incomplete.

λ-2025 by solve (this session's arms at HEAD `3253345`, capacity-deliverability
partition regenerated and its load affirmatively verified in the logs):

| arm | extract | λ-2025 | vs keeper | ≈C3a-2025 |
|---|---|---|---|---|
| committed keeper | session-local partial (unrecoverable) | 37.8212 | — | +9.97 % PASS |
| **arm K** (`caiso123_keeper_extract`) | light `e40847c` | 37.7313 | **−0.24 %** | ≈ +9.7 % pass-class |
| **arm C** (`caiso123_head_control`) | HEAD guard file | 38.1975 | **+1.00 %** | ≈ +11.1 % FAIL |
| base_A (07-24, f28340b) | full `3dc01fae` | 38.4060 | +1.55 % | ≈ +11.5–11.7 % FAIL |
| caiso-122 arms (their formula, de62eb1) | absent / full / guard | 36.4778 / 38.6290 / 38.5585 | −4.06 / +1.60 / +1.41 % | — |

λ is **strictly monotone in in-window derate mass** across all seven solved
states. The keeper sits just above the light-partial state and 1.0–1.6 %
below every committed post-07-24 state.

**The same-HEAD isolation (arm C − arm K, one container, one basis, both
logs clean): +0.466 $/MWh = +1.24 % λ, CC_REGULAR −0.49 TWh, import
+0.42 TWh** — reproducing the drift's class signature. The extract content
change (partial → committed full derivation) is the drift. ≈C3a values are
model-side λ ratios mapped through the keeper's scored +9.97 % (±0.2 pp
formula skew vs the real scorer; caiso-121 scored the f28340b-class control
at +11.49 %).

## §4 — TASK 1: the caiso-120 vs caiso-122 contradiction, settled

- caiso-120's A0/A1 (`2026-07-26-caiso120-meritguard-a1`) compared **A0 =
  the keeper's committed bytes** (session-local light-partial extract)
  against A1 = the recipe at `42747a9` (committed full extract, guard-on):
  C3a-2025 +10.0 → +11.1 %. Its method note ("the guard is byte-inert off,
  so A0 = the keeper by construction") was valid for the guard *flag* but
  not the extract *file*, which #2842/#2844 had already replaced with a
  heavier full derivation, independent of the guard, two days earlier.
- caiso-122's same-HEAD isolation of the guard step (full `3dc01fae` →
  guard `6a8f285`): **−0.07 $/MWh (−0.18 %)** — small and *favourable* to
  C3a. Confirmed directionally here (the guard file solves 0.2 % below the
  full file at HEAD).
- **Settlement: both sessions were right about what they measured and wrong
  about what it meant.** The A0→A1 move is real but is ~entirely the
  partial→full extract-content change, not the guard. The charter-§5
  "RE-TUNE REQUIRED (2025 C3a flips on the corrected envelope)" trigger for
  CAISO is **withdrawn as stated**: the guard adoption per se moved CAISO
  *toward* passing. The **re-derived trigger** is: *the keeper's C3a-2025
  PASS was calibrated against a non-reproducible partial outage envelope;
  on any honest full derivation of the measured extract (guard on or off),
  C3a-2025 fails by ~+1.1 pp.* That is a rule-11-class finding (the light
  envelope was silently compensating), and the re-tune decision transfers
  to that predicate.
- caiso-122's first revision ("keeper solved with the extract absent") and
  its correction ("the extract is not the drift") were **both** wrong in
  opposite directions; the truth is between: the keeper solved WITH an
  overlay, from a lighter partial derivation. Its §3 CC_CHP r-refutation
  stands (the overlay was present); its §5 "family exhausted" is corrected
  — the family never contained the keeper's actual (light) state.
- The NYISO re-audit cell is unaffected by this specific confound: #2842/
  #2844 changed only the CAISO extract among `campd-unit-outages*`.

## §5 — residual: a second, smaller basis motion since de62eb1 (OPEN, flagged)

Cross-basis comparisons shift by ~−0.2…−0.5 pp λ between de62eb1/f28340b-era
solves and today's HEAD: caiso-122's control read +1.41 % (de62eb1, their
formula) where today's faithful arm C reads +1.00 %; arm K sits −0.24 %
below the keeper with a near-keeper envelope; class volumes move further
(CC_REGULAR ≈ −0.8 TWh / import ≈ +0.8 TWh common to both arms). Config
surface is clean (arm C vs caiso-122 `run_config` deep-diff: only new
default-off fields `dual_fuel_oil_daily_parity` / 
`nyiso_ordc_measured_step_span`). Candidates, none attributed this session:
the de62eb1..HEAD src window (16 files; the miso-91 SUMMER_* re-home is
verified value-identical, `renewables.py` itertuples refactor is
MISO/forecast-scoped on inspection; `scenarios.py`/`bounds.py`/`runner.py`
diffs are nominally NYISO/PJM/refactor-scoped — one may not be
CAISO-inert), container/partition state of the EARLIER sessions'
uncommitted arms (the silent-degrade trap was only documented 07-26,
RESULTS-neiso65 §2), and alternate-optimal vertex wander (recorded in
meta's own solver-provenance note). Small against the +1.24 % extract
effect; direction *helps* C3a-2025 and *worsens* C5a-direction volumes.
Next session: same derive-first protocol, now with `basis_sha` anchors.

## §6 — what the lane can and cannot do now (rules 1/11/13/14)

- **Restoring a light extract to make C3a pass is FORBIDDEN.** The light
  envelope is not a derivable state of the measured input — it was a
  partial derivation. Rules 13/14 protect *reproducible measured inputs*;
  they do not protect an accident of an incomplete file.
- **The honest envelope is the full derivation** (currently the guard-on
  HEAD file) — while the detector's absolute level remains the open
  over-count question (neiso-66: CAISO active-plant 1.40–1.90× published on
  the revision-aware build; freeze ACTIVE). Re-tuning CAISO offers against
  an input under known dispute, vs first settling the over-count in the
  freeze lane, is the owner/charter sequencing decision. This session armed
  nothing.
- The measured min-load 0.570 disposition is untouched (KEPT; promotion
  remains an owner call, caiso-122 §6).

## §7 — governance closures and recommendation

- **`basis_sha` landed** (this session): `solve_and_persist` stamps
  `merge-base(HEAD, origin/main)` — the newest origin-durable ancestor —
  into `meta.json` + `run_config.json.git`; `replay_keeper` ignores it on
  replay input and its `_restore_display_date` provably rewrites only the
  timestamp's date prefix. `tests/test_basis_sha_provenance.py` pins the
  contract. This finding's §1 reconstruction becomes
  `git log <basis_sha>..HEAD -- data/ scripts/` next time.
- **Recommendation (not implemented):** extend the `shared_inputs`
  content-hash block to the *derived* outage extracts (and any other
  derived-not-shared solve input), so a bundle pins the exact extract bytes
  it solved on. The keeper's unrecoverable envelope is exactly the gap this
  closes.

## §8 — reproduction

```
scripts/probes/_caiso123_extract_repro.py --extract <csv> --out-dir results/probes/<name> --years 2025
git show c95f98c^:data/raw/campd-unit-outages-CAISO.csv   # light partial e40847c
git show c95f98c:data/raw/campd-unit-outages-CAISO.csv    # full re-derive 3dc01fae
# keeper-era full derivation (reproduces 3dc01fae's in-window mass):
#   git worktree add <dir> 2895bbe75 && cd <dir> && PYTHONPATH=.:src python scripts/data/derive_campd_unit_outages.py --iso CAISO
```
