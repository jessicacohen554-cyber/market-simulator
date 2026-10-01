# FFR-3B — Staleness machinery, bookkeeping reconciliation, and the four signed decisions

**Session.** FFR-3B of `docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-3B,
2026-08-02. Branch `claude/ffr-3b-staleness-reconciliation-78hthm`, based on
`origin/main` **`e81f22d`** (the dispatch brief named `b9a96a9`; main had moved).
**No LP was solved, constructed, or scored. No `ScenarioConfig` default was
changed** (rule 24 — D-1's flip and D-2's damper arming are SIGNED but belong to
FFR-3A step 0). No out-of-training year was touched; the holdout spend freeze is
untouched and nothing here makes any tier spendable.

Ran fully parallel with FFR-2A, which owns the solve slots and the crossover-seam
files; none of those files is touched here.

---

## 1. The four signed decisions — all executed

Signature for all four: **owner sitting HELD 2026-08-02, all eleven decisions
signed**, `docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum C.1. Each
landed as its own commit citing the signature.

### D-5(a) — ADOPT the §2.1b(2)(a) paragraph — `aaf6297`

`docs/forecast-development-plan-2026-07.md` §2.1b(2)(a) replaced with the signed
text **verbatim** (not paraphrased, not improved). The superseded
NYISO-withdrawal example is dropped. The consequence is stated once, as
instructed: gate (a) now reads as **met by three ISOs — NEISO, NYISO, PJM** — the
current membership of the `complete` block; conditions (b)–(d) still gate every
full solve and the freeze still gates every holdout spend.

### D-5(b) — RE-KEY on promotion, with per-promotion re-verification — `37d2ee7`

The owner chose **Option B** over the packet's recommendation, and chose the
honest implementation: re-key **and re-verify the determination**, so the marker
never asserts a determination that was never scored against the run it names.

**The owner-facing finding first: the re-verification IS reliable without a
solve.** `scripts/calibration_verdict.py` reads a run's committed artifacts only
and never re-solves the LP — its own module docstring states that re-running it
on any keeper reproduces the verdict byte-for-byte. Re-verifying a promotion is a
seconds-long, deterministic read of already-committed data. **The mechanical
field-update degradation the owner explicitly declined is not needed**, and the
accepted cost (a verification pass at ~20 promotions per 10 days) is far below
what was signed for.

**Policy wired, in three places:**

1. **`scripts/audit_keepers.py` check M1** (`marker_currency_failures`), run over
   the `complete` block and scoped by `--iso` like the other lane checks:
   - **M1a** — the entry's `keeper` == the ISO's designated keeper shard.
   - **M1b** — the determination the entry asserts == the **live** verdict of the
     run it names.
   M1a short-circuits M1b: re-verifying a superseded run answers a stale
   question, and the re-key carries its own re-verification.
2. **`.claude/agents/calibration-keeper-auditor.md`** — the agent that already
   fires on every keeper-shard edit, which the sitting named as the natural home.
   It gains the two-step repair in a binding order: **RE-VERIFY FIRST, then
   re-key**, editing only the promoted ISO's entry. And it must **STOP AND
   ESCALATE rather than write the marker** if the re-verified determination is
   worse or the caveat count rose — a marker downgrade is an owner-facing
   calibration event, not marker bookkeeping.
3. **`CLAUDE.md` rule 22** and the keeper-promotion lane note record the policy;
   the marker file's own `note` re-states the `keeper` field's semantics (it is
   no longer a declaration-time snapshot).

**Markers re-keyed, each determination re-verified this session, no solve:**

| ISO | was (declaration basis) | now (designated keeper) | re-verified determination |
|---|---|---|---|
| PJM | `2026-07-30-pjm-140-rampenv` | `2026-07-31-pjm-143b-hy-level` | **CALIBRATED**, zero caveats (C1 all 16/16, free 12/12) — unchanged |
| NYISO | `2026-07-30-nyiso-100-silretire` | `2026-08-02-nyiso112-ramp-plus-peaker` | **CALIBRATED-WITH-CAVEATS**, 1 ledgered caveat (C3c) — unchanged |
| NEISO | `2026-07-08-neiso-54-steamgas-ct` | `2026-07-31-neiso-72-hy-window` | **CALIBRATED-WITH-CAVEATS**, 1 ledgered caveat (C3c) — this entry had **no** `determination` field before the re-key |

`keeper_at_declaration` preserves each entry's original evidence basis. NEISO's
`locked_test_scored_on` was deliberately **NOT** re-keyed by this lane. *[Corrected
2026-08-06, owner decision D-23: this sentence described that field as "the SPENT
one-shot's frozen `neiso-53` config" whose "score stands as taken (rule 22)". There was
no such score — NEISO's locked test has **never been granted or run**, and the id the
field named is a **TRAIN-tier 2023–2025 config**, not a 2019 run. The field is now
`locked_test_scored_on_WITHDRAWN`. This lane's own action is unaffected: not re-keying
it was correct, but the exemption was **moot** rather than exercised. Citation chain:
`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
`docs/third-party-peer-review-2026-07.md` §6.3 item 1 → D-23 / sitting Addendum X.6.]*

**M1 caught real drift on its first live run.** NYISO's designated keeper had
already moved past the id this lane was dispatched against (`nyiso109` →
`nyiso112`) — exactly the churn the owner accepted the verification cost for. The
re-key targets the keeper at this HEAD; a promotion landing after this merge will
trip M1 again, which is the mechanism working.

### D-5(c) — CORRECT the stale tier-agnostic sentence — `e19986c`

PJM's marker `locked_test` asserted *"The CI marker gate is tier-agnostic … even
though CI will not catch it."* False since 2026-07-31: all three rule-22 gates
read the tier map from `scripts/lib/holdout_policy.py` and require the `final`
block for a locked-test year. **That one sentence was corrected; nothing else in
the file was changed by this commit** — it is a governance file.

The replacement keeps the discipline the original was carrying, by naming what CI
genuinely cannot see: **CI checks the GRANT, not the spend history**, so
re-solving an already-spent locked test remains a governance breach CI will not
catch — which is what each ISO's `locked_test` note records.

### D-7(i) — RE-ISSUE the golden-fixture waiver — `a26443b`

`tests/golden/staleness_waiver.json` re-issued under its own `on_expiry` clause.
**The test is NOT deleted. There is NO reseed** — explicitly withheld (sitting
C.5), and the file now says so in a dedicated `not_authorized_by_this_reissue`
field.

**New expiry: `2027-01-31`** — **FFR-3B's proposal, flagged adjustable in the
file.** The owner signed the re-issue, not the date. It is ~6 months of runway
for the off-ERCOT move plus its own seed-authorization sitting; nothing
downstream keys on the value, and the only consumer is the date comparison in
`test_golden_fixture_config_identity_is_current`.

**Why re-issued rather than resolved**, recorded in the file so nobody re-derives
it: resolving means reseeding, and the fixture is to be **MOVED OFF ERCOT first**.
ERCOT is absent from the `complete` block, its keeper carries **DETERMINATION
NOT-YET** (fail set {C3a, C3b, C3c, C7}), and it churns keepers near-daily —
which is much of *why* the fixture keeps going stale. Reseeding on ERCOT today
buys a fixture that re-stales on the next keeper. The move is separate scoped work
needing its own signed 15-solve-year seed authorization, and it is a **code
change, not a flag** (`iso="ERCOT"` and both golden filenames are hardcoded).

**Verified facts recorded in the waiver** so no later session re-derives them:
`test_golden_bands_hold` is `@pytest.mark.slow` **and** skipped unless
`RUN_GOLDEN_FORECAST=1`, so it runs nowhere automatically; `ci.yml`'s only
reference to `tests/golden/**` is a path filter; the test this waiver actually
holds off is a pure config-hash comparison that builds no LP. Recorded against
the packet for honesty: the fixture already sets `use_campd_bins=False`, so the
**speed** case for switching ISOs is weak — the **calibration** case is strong.

`tests/regression/test_golden_forecast_bands.py`: 2 passed, 1 skipped.

---

## 2. FR-21 staleness machinery — live (`bfaafbb`)

The failure being closed: FF-2D scored 2026-07-20; over the next ten days ~20
keeper promotions landed, the pinned default config cache key moved twice
(`2a1cb710` → `edbc1b10` → `603c2498`) and was broken-and-restored once, and the
NYISO forecast orchestrator was rewired — with no FC verdict re-scored. The board
kept rendering 07-20 verdicts as if they described the code. **Nothing detected
it because no artifact recorded when, and against what, it was scored.**

### 2.1 Schema (pack item 1)

`scripts/lib/forecast_provenance.py` defines one stamp —
`scored_at_sha` + `scored_at_date` + `cache_epoch` — carried by:

- **`scripts/forecast_verdict.py`** — stamps every verdict, and carries the stamp
  through `condensed_sidecar` into `ff-verdicts.json`.
- **`scripts/register_forecast_run.py`** — stamps the canonical hindcast sidecar
  at **fresh** registration, each generated registry sidecar and run payload, and
  adds a board-level block to the manifest meta (newest scored sha/date, distinct
  epochs, stamped/unstamped counts).

**FFR-3A populates them** when it re-scores the battery. The stamp is total: a
missing git binary or a malformed artifact yields `None` fields, never an
exception — a provenance stamp must not be able to fail a scoring run.

Two design decisions worth carrying forward:

- **`cache_epoch` is READ from the run's own artifacts, never recomputed.** The
  epoch that matters is the one the run actually solved under, not what the code
  would produce today.
- **The stamp is PRESERVED, never minted, on `--reindex`.** Reindex re-derives
  sidecars from committed inputs without re-scoring anything, so stamping it
  "scored now" would reset the board's apparent freshness on every Pages deploy —
  which *is* the FR-21 failure. A run predating the machinery records
  `sha`/`date` as `None` plus a note: **absence of a scoring record is not
  evidence of freshness.** The board today honestly reports **93 stamped, 0
  scored**.

### 2.2 CI check (pack item 2)

`scripts/check_forecast_staleness.py` reads the stamps back, takes the newest
scored sha, and counts solve-affecting commits (`src/market_sim/**` + the
schedulable forecast scripts) landed since. Wired into **`ci.yml` as a new
`forecast-staleness-warn` job — an EXISTING workflow, no new one** (private repo,
billed minutes), with `fetch-depth: 0` so the distance is measurable at all.

**WARN, never FAIL.** The script exits 0 unless `--fail-on-stale`, which CI
deliberately does not pass: backcast calibration velocity must not be blocked by
forecast-board freshness, and the backcast lane is the one producing the keepers
that make the board stale. A test pins that `ci.yml` never adds the flag.

Second signal, reported but never on its own a warning: **epoch spread** (85
distinct `cache_epoch` values today). A mixed-vintage board legitimately holds
several; the note flags that a cross-run delta may not be a model effect.

Live output at this HEAD:

```
  newest scored sha   : (none recorded)
  stamped / scored    : 93 stamped, 0 scored
  distinct epochs     : 85
  WARN: 93 board artifact(s) are stamped but NONE records a scored-at sha …
```

18 tests (`tests/scoring/test_forecast_staleness.py`).

---

## 3. FR-27 forecast DOF-ledger stub — chartered honestly (`716241f`)

`scripts/build_forecast_dof_ledger.py` enumerates, from a run's own `run_config`,
every solve-affecting parameter the forecast carries — grouped by attestation
question (retirement / entry / capacity_market / fuel_and_policy /
demand_and_weather / dispatch_mechanism), with `source` and `evidence` blank and
`identification` written as the literal token **`unattested`**.

**It attests nothing, and the verdict effect is NONE by construction.**
`forecast_verdict.py`'s FC-7 scorer now recognizes `unattested` as *not
identified*, so an all-skeleton ledger scores the **same status as an absent
one** at every tier — CAVEAT at t1/t2, FAIL at t3. Verified side by side:

| tier | absent ledger | all-skeleton ledger |
|---|---|---|
| t1 | CAVEAT | CAVEAT |
| t2 | CAVEAT | CAVEAT |
| t3 | FAIL | FAIL |

What changes is **specificity**: the CAVEAT goes from "DOF ledger absent
(identification unproven)" to naming the awaiting entries. Without the scorer
change, a config walk that attests nothing would have silently flipped FC-7
CAVEAT → PASS — the artifact rule 21 exists to prevent. A test pins the parity.

Scope is the run's **non-default** fields (default `ScenarioConfig` imported
lazily and guarded): a field at its default is an un-armed mechanism or an
untouched threshold, not a free parameter *of this run*. On a real bundle
(`results/hindcast/pjm-2021-2025-realized-s3`) that is **15 fillable entries**
rather than 300 mostly-inert ones. Where the model stack cannot be imported, the
scope widens and the ledger **declares that in its `scope` field** rather than
hiding it.

Rule 21 is not weakened: a filled `residual` entry with no open `root_cause`
still FAILs, and a partly-filled ledger still CAVEATs. Both tested (13 tests).

Full attestation remains WG / Phase-B work (audit §4 Phase 5) — the stub does not
pretend otherwise.

---

## 4. Bookkeeping reconciliation (FR-21/FR-23) — `fb31f29`

Every corrected claim cites where the truth now lives.

### 4.1 Code — FFR-1C finding F-5 CLOSED

`runner.py`'s `firm_clean_mw` summed `_FIRM_CLEAN_FUELS=("hydro",)` over the
**persistent** fleet, which structurally never contains hydro — so **every
evolution ledger ever written reports 0.0 for every ISO and year.** It now reports
the nameplate the model actually dispatches (`modelled_hydro_nameplate_mw`,
resolved for the solve year) plus any hydro that did reach the persistent fleet,
keeping the field's own nameplate units. A companion **`firm_clean_accredited_mw`**
reports the same resources at the ISO's published accreditation factor — the MW
that actually enter `accredited_firm_capacity_mw`. Reported *alongside* rather
than replacing, because silently changing a field's units is how the next reader
gets misled a second time.

**Dispatch-inert by construction:** nothing decides on either field (the adequacy
screens read `accredited_firm_capacity_mw`, which FFR-1C already corrected).
Verified NEISO 1,899.5 MW nameplate / 949.75 MW accredited, matching FFR-1C's
census. The `evolution_ledger.py` and `retirements.py` docstrings are corrected to
match, and both record that **pre-2026-08-02 ledgers read 0.0 as "not measured",
not as zero hydro**.

### 4.2 Docs — the corrections

| Claim | Correction | Truth now lives in |
|---|---|---|
| FF plan §1.2 rows 1/3 | D-1/D-2 **SIGNED but defaults NOT moved** — FFR-3A executes | sitting Addendum C.1; `ffr-2b-…-2026-08-02.md` |
| FF plan §1.2 row 5 | FFR-1C landed; the row's CAISO 3.6 / NYISO 3.3 GW magnitudes are **superseded** (complete-census: CAISO 6,568 / NYISO 4,587 / NEISO 1,899 / MISO 2,371 / PJM 3,301 / ERCOT 546 MW); **I7 still FAILs** | `ffr-1c-hydro-accreditation-2026-07-31.md` |
| FF plan §1.2 row 11 | all four WAVE FI sessions landed | §6 WAVE FI table |
| FF plan §6 WAVE FI ×4 | read "prompt issued" for **thirteen days** after landing; now name the committed deliverable, with **G4/G5 marked memo/registry-only** | `ff-g{2,3,4,5}-…-2026-07.md` |
| FF plan §7.2 Git clause | read "push via `push_files` ONLY (never `git push`)"; CLAUDE.md superseded this 2026-07-25 (PR #2878 pushed a 434,784-byte blob over `git push`, no 413). Following it strands run payloads sidecar-only | CLAUDE.md "Git & Pushing"; `dashboard-payload-push-gap-2026-07.md` |
| gap register §3.11 | FF-G2 **CLOSED**; FF-G3 **PARTLY OPEN on (a)**; FF-G4/FF-G5 **MEMO/REGISTRY LANDED but GAP STILL OPEN** — the landed artifact is not the mechanism | each session's handoff |
| wave-manager ledger | gains the **WAVE FI block (5 rows)** and the **FFR block (15 rows)** — neither program was ever entered | this file + the per-lane handoffs |
| `forecasting-entry-exit-assessment.md` | headline **RE-GRADED post-FF-2C** (see below) | `ffr-2e-…`, `ffr-2c-…`, sitting C.3 |
| `ff-t1-gate` §4.1 NYISO row | cited the **wrong arm** (see §5) | committed sidecars |
| CLAUDE.md "coal=1yr" | **coal=3yr** — `scenarios.py` ships `retirement_years_coal: int = 3`, rule-23-identified to the EIA-860 median; also scoped to the **legacy** rule, which is what the field governs | `config/scenarios.py:1257` |
| mechanism matrix (.js + .md) | **header hygiene only, no cell verdict touched** — the 2026-07-27 keeper lists annotated as HISTORICAL BUILD SNAPSHOTS pointing at the live `keepers:` object | `mechanism-matrix.js` `keepers:` |
| `test_ff_readiness_battery` | asserted `PJM == "none"` for two days after PJM was declared `complete` — an FR-21 desync **inside a test** | `calibration-complete.json` |

**The entry-exit headline re-grade, stated precisely.** The one-line verdict
stands; its **mechanism** does not. "In the five capacity-market ISOs the fixed
capacity payment makes fossil retirement arithmetically impossible" is no longer
the shipped mechanism in **PJM/MISO/CAISO/NEISO** (FF-2C flipped them ON), is
still true of **NYISO** (never flipped), and never applied to energy-only
**ERCOT**. But the flip **inverted the failure rather than closing it**: FFR-2E
measured **zero** capacity revenue on the curve arm for PJM/NEISO/MISO where the
fixed arm pays full net-CONE, so "impossible to retire" became **over-fire** —
which is exactly why every curve-ON T1-H leg FAILs FC-3 on the retirement band.
CAISO's curve-ON is **provably inert**. PJM is the directional exception (FFR-2C's
floor reverses the posture-gap sign from 2028). **No body number was
re-measured** — the body remains the 2026-07-13 measurement record.

### 4.3 Already correct — recorded so nobody re-derives them

FR-23's list is stale in four respects, all verified at this HEAD:

- **`ercot.md:336`** — the ERCOT-93 "Machinery MERGED" claim was already corrected
  **and resolved** on 2026-07-26: the machinery is **DROPPED** (never on main, the
  patch rotted, the orphan test C-DELETED). **No edit was needed.**
- **gap register R5c** — already carries its FFR-1C closure *and* the magnitude
  correction.
- **`evolution_ledger.py:38-45`** — the `confirmed_derates` schema now has its
  writer (FFR-1A) and the docstring says so.
- **`retirements.py:109-114`** — the "hydro included" claim was already corrected;
  this session updated it again, in the *other* direction, because FFR-1C has
  since made hydro genuinely reach the ledger.

---

## 5. The FFR-2E citation correction (scoped as instructed)

**Done — the NYISO arm.** `ff-t1-gate-2026-07.md` §4.1 cited
`nyiso-2021-2025-curve` as NYISO's FC-3 evidence, but production ships NYISO
**curve-OFF** ("excluded pending re-calibration"), making that leg a
`--capacity-market-clearing` **force-ON probe** — the FR-14 shape one level up, in
the evidence chain. Re-pointed to the committed shipped-posture twin
`nyiso-2021-2025-fixed`.

**Both arms FAIL, so no determination flips — only the number and the claim it
supports.** Verified here **directly from the committed sidecars**, not relayed
from 2E:

| arm | `capacity_market_clearing` | model retire | actual | err | band |
|---|---|---|---|---|---|
| `nyiso-2021-2025-curve` (probe) | `True` | 3.318 GW | 1.488 GW | **+123 %** | FAIL |
| `nyiso-2021-2025-fixed` (shipped) | `False` | 1.036 GW | 1.488 GW | **−30.4 %** | FAIL |

The probe arm over-fires by 2.2× what the shipped arm does, so the "curve-ON
over-fire" reading in §4.1 is a property of **the probe**, not of NYISO's shipped
posture. `false_retire` PASSes on the shipped arm (0.024 GW, 2.3 % of model)
where it FAILed on the probe.

**NOT done — 2E's second correction, and why.** Re-pointing every FC-3 citation to
a post-epoch leg **cannot be completed**: post-epoch replacements exist for NEISO
and CAISO (`*-ffr2e`) and for PJM and MISO (`*-cmc-{legacy,pipeline}-ffr2b`), but
**none exists for NYISO** — its only two legs (`-curve`, `-fixed`, cache keys
`9eacbc5bc4732ff6` / `1aeb808af7e0f4be`) are both pre-epoch. Per the brief, this
is **FLAGGED and routed to FFR-3A** rather than citing a leg that is not there.
It converges with signed **D-6**, which schedules the NYISO pair regeneration —
and per 2E it must be regenerated as a **shipped-vs-fixed** pair, not the
force-ON probe pair this correction just relabelled. The §4.1 note records all of
this in place.

---

## 6. FLAGGED, not fixed — the explicit list

1. **The pre-epoch FC-3 citations, NYISO half — routed to FFR-3A.** No post-epoch
   NYISO leg exists (§5). Converges with signed D-6.
2. **FFR-1C finding F-6 — routed to FFR-3A.** Threading the solve year to the four
   `accredited_firm_capacity_mw` call sites (`runner.py`, `evolve.py`,
   `retirements.py`) changes backcast numbers by ≤2 % nameplate (CAISO 6,432.7 vs
   6,568.4; NYISO 4,647.5 vs 4,587.1). It is a real accuracy improvement (rule 14)
   but it **moves numbers**, and this lane runs no solves, so it cannot be probed
   here. F-5 was closed because it is provably display-only; F-6 is not.
3. **FF plan §1.2 row 11 item (5) ends mid-sentence at "BLK-9".** Text is missing
   from the source. This session could not source what it said and did **not**
   invent it (rule 1, findings-first).
4. **`test_ff_readiness_battery` — 4 remaining failures are environmental, not
   defects.** They are FFR-1C's F-7 note: `data/clean` is gitignored and absent
   from a fresh clone. Confirmed **pre-existing on `origin/main`** (13 failures
   across the three affected files, byte-identical count on both refs) and
   confirmed environmental: **all 21 pass** after
   `PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py` builds the
   partition. Nothing to commit — the artifact is gitignored.
5. **The other 9 pre-existing failures** (`test_measured_chp_heat_rates`,
   `test_outages`) are identical on `origin/main`; **none is caused by this
   lane**. Not investigated — out of charter.
6. **D-5(b) creates a standing race with keeper promotions.** M1 will FAIL any
   time a `complete` ISO promotes without re-keying. That is the mechanism
   working as signed, but it means a promotion session that skips the marker step
   now fails CI's `audit_keepers --check`. The agent doc carries the procedure;
   if the cadence proves painful, the owner's lever is the policy, not the check.
7. **`run_full_horizon.py:242` derives its own `firm_clean` independently** of the
   ledger field this session fixed (from a `cap` dict, a different population).
   Not touched — it is a separate seam, and FFR-2A/3A territory. Flagged so the
   two are reconciled deliberately rather than by accident.

---

## 7. Verification

- `scripts/audit_keepers.py` — **PASS, 0 failures, 0 warnings** (all six ISOs,
  H1 holdout quarantine, M1 marker currency, S1 status sync).
- `scripts/check_mechanism_matrix.py` — integrity OK; **keeper stamps match every
  `keepers/<ISO>.json`**.
- `scripts/check_forecast_staleness.py` — runs, WARNs correctly, **exits 0**.
- `scripts/register_forecast_run.py --reindex` — 93 runs regenerate; stamps
  preserved, not minted.
- New tests: 18 staleness + 13 DOF-ledger + 6 M1 = **37**, all passing.
- `tests/regression/test_golden_forecast_bands.py` — 2 passed, 1 skipped.
- `ruff check` + `ruff format --check` — clean on every touched file.
- Rule 27: every pushed file ≥300 lines blob-verified against local
  (`git hash-object` vs `git rev-parse origin/<branch>:<path>`) before the next
  commit.

## 8. Commits

| sha | what |
|---|---|
| `aaf6297` | D-5(a) — §2.1b(2)(a) verbatim |
| `e19986c` | D-5(c) — the one stale marker sentence |
| `37d2ee7` | D-5(b) — re-key + M1 + agent + CLAUDE.md |
| `a26443b` | D-7(i) — waiver re-issue, expiry 2027-01-31 |
| `bfaafbb` | FR-21 staleness machinery + WARN-level CI job |
| `716241f` | FR-27 forecast DOF-ledger stub |
| `fb31f29` | FR-21/FR-23 bookkeeping reconciliation + F-5 |
