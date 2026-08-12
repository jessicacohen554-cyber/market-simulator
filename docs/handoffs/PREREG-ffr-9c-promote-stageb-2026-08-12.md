# PREREG — FFR-9C-PROMOTE: promote stage B as one coherent forward posture

**Session.** FFR-9C-PROMOTE `[OPUS]`. Branch `claude/ffr-9c-promote-stageb-hlfnpg`,
off a freshly fetched `origin/main` **`15261093`** (the brief's `f6381c5` had been
superseded by the time this lane started — re-verified at own head per the brief's
own instruction). Owner card **D-30, SIGNED 2026-08-11, sitting Addendum AK.8**:
promote STAGE B (R-a + R-b + R-d).

**Head move during pre-registration, adjudicated against the D-30 clause.** The
lane started at `2738d5de` (PR #3877 merge) and `origin/main` advanced to
`15261093` while the pre-registration was being written. **No solve had been
launched**, so no run was at risk and nothing was discarded. The D-30 clause is
about a *forecast-default change*, so the question is whether any solve-affecting
byte moved. It did not, verified structurally rather than by reading the diff —
the git tree hashes are identical on both sides (FH-5 §1.1's own technique):

```
2738d5de:src     = 15261093:src     = b3f11751475ad11e1b2d9f947bcfa0eb6a948f3b
2738d5de:scripts = 15261093:scripts = 682ad9e87d8b13a787b395c6b9db48ae9f22b852
```

The lane therefore rebased onto `15261093` and proceeded rather than stopping.
**Solves run at `15261093`, with `src/` and `scripts/` provably equal to the
`2738d5de` head this lane's pre-flight verification was performed against.**

**Everything in §1 was written and committed BEFORE any default was edited and
before any solve was launched.** §2+ are filled in order, as produced.

---

## 0. PRE-FLIGHT #1 — FH-5 discharged, verified at this head

The lane was blocked on FH-5. Verified on disk at `2738d5de`:

- `docs/handoffs/fh-5-phase-b-2026-08-11.md` is present on `main` (39,300 bytes).
- Its **§4 THE HORIZON-DEGRADATION READ is populated**: "all six ISOs, 11 of 12
  arms", the registered-id table with runtime keys, the §4.1 horizon-vs-year
  effect table (13 ISO×metric cells), the §4.2 per-ISO Arm R rows, §4.5 invariant
  record.
- **The I6 rider PASSED on every one of the 11 arms** (§4 opening, §4.5 table).
- **CAISO Arm K is BLOCKED-not-failed** on the absent as-of-2021 CAISO
  demand-growth cell (§1.4), exactly as the brief states.

Gate CLEAR; this lane proceeds. Note the ERCOT keeper moved after FH-5 pinned:
FH-5 §1.1 records `2026-08-09-ercot185-shaped-partial`, while this lane's keeper
is `2026-08-11-run188-arm-topfine-cliff` (MOVED 2026-08-11, ercot-188 SCHEME R1,
owner decision E2). That is a keeper advance after FH-5's pin, not a conflict.

---

## 1. PRE-FLIGHT #2 — WHAT "PROMOTE" MEANS HERE

### 1.1 The question the brief poses

FFR-9C's stages were measured ON TOP OF a control recipe that itself arms
`capacity_screen_unified_lookahead` + `capacity_screen_scarcity_restoration` BY
INVOCATION. Addendum AG.1 ruled those are NOT a shipped-default flip and parked
their promotion on "FH-4's own skill evidence" — which FH-5 has now supplied
(AO.2). So flipping stage B's three flags ALONE would ship **stage B minus its
own base recipe**: a combination nobody has ever solved.

**DECISION: promote as ONE coherent unit.** All five flags move together. A
partial promotion is not merely unsound here — for two of the five it is
*mechanically impossible*, and the measured basis for the other three does not
exist without them. Reasoning below, recorded before any default is edited.

### 1.2 Ground 1 — the two screen flags cannot be separated from each other

`ScenarioConfig.__post_init__` (`src/market_sim/config/scenarios.py:11740`)
**raises** when the restoration flag is armed without the lookahead:

```
capacity_screen_scarcity_restoration requires
capacity_screen_unified_lookahead: the repair extends the unified lookahead
object's armed stack (FFR-8A).
```

One object, one gate per layer. They are a pair by construction.

### 1.3 Ground 2 — a GLOBAL default flip is impossible, not just unwise

The same validator (`scenarios.py:11747`) **raises for any non-ERCOT ISO**:

```
capacity_screen_scarcity_restoration is ERCOT-only: the forward
committed-capability (RTOLCAP/RTOFFCAP) share tables are ERCOT-identified
(rule 25 [R-ISO-SCOPE]); got iso=...
```

So setting `capacity_screen_scarcity_restoration: bool = True` on the
`ScenarioConfig` dataclass would make **every CAISO, MISO, NYISO, NEISO and PJM
config raise at construction**. The shipped-default scalar cannot express this
posture at all. This is dispositive: the promotion MUST be ISO-scoped.

### 1.4 Ground 3 — stage B's own three flags have no measured basis without the pair

R-a (`entry_pipeline_aware_signal`), R-b (`smr_available_year`) and R-d
(`vre_procurement_additions_enabled`) were measured as a delta **on top of** the
armed control recipe. The reported magnitudes (§2 below) are stage-B-over-control
numbers. Shipping the three without the pair would ship a posture whose only
evidence is a measurement of a different posture. Rule 13 `[R-MEASURED]` forbids
asserting a number that was never solved.

### 1.5 The vehicle — ERCOT's `default_scenario_overrides`

The mechanism is `ISOConfig.default_scenario_overrides`, resolved by
`apply_iso_scenario_defaults(config, iso)`
(`src/market_sim/config/iso_configs.py:1482`) and called from `runner.py:1023`
**before the run record is built**, so a sidecar reports the posture it actually
solved rather than the caller's unresolved one (the FFR-2E defect; ARM3-MEASURE
hit exactly that). An ISO-level default fills only a field the caller left at the
`ScenarioConfig` default — **an explicit caller value always wins**, so every
existing invocation that passes these flags explicitly stays byte-identical.

**Precedent, from the SAME owner sitting.** Owner decision **D-29 (sitting
Addendum AK.8, signed 2026-08-11)** — the same sitting that signed our D-30 —
armed `miso_clean_tier_rows` for MISO through exactly this seam
(`iso_configs.py` MISO block; lane ARM-3-ARM). D-30 is the ERCOT analogue of a
promotion the owner has already expressed this way, once, at this sitting. This
lane follows that precedent rather than inventing a second mechanism (rule 19
`[R-ONE-MECH]`).

ERCOT already carries one such override (`scarcity_price_overlay: True`), so the
table exists and this lane adds rows to it.

### 1.6 The promotion, exactly

Five rows added to `_ercot_config().default_scenario_overrides`:

| Flag | To | Role |
|---|---|---|
| `capacity_screen_unified_lookahead` | `True` | control recipe (AG.1 → AO.2) |
| `capacity_screen_scarcity_restoration` | `True` | control recipe (AG.1 → AO.2) |
| `entry_pipeline_aware_signal` | `True` | **R-a** — repairs a real double-count (rule 19) |
| `smr_available_year` | `2030` | **R-b** — removes 4 GW of 2022-vintage ERCOT SMR |
| `vre_procurement_additions_enabled` | `True` | **R-d** — nets exactly, bounded 1.84 GW |

**Zero fitted parameters in any stage.** ERCOT only; no other ISO's shard,
defaults or verdicts are touched (rule 25 `[R-ISO-SCOPE]`).

### 1.7 What is NOT promoted

Stage A, stage C and any other FFR-9C stage. D-30 signs stage B only.

---

## 2. THE ACCEPTED COST — reported at full magnitude

D-30 was signed WITH these numbers. They are **not** softened, and they are not
defects to be tuned away in this lane (rules 1/13/14).

**Costs:**

| Metric | Control | Stage B |
|---|---|---|
| wind | −57 % | **−73 %** |
| CC GW error | +5.8 | **+8.8** |
| CO2 2023 | −11.28 | **−12.84** |

**Against that:**

| Metric | Control | Stage B | Actual |
|---|---|---|---|
| additions basis | 45.05 GW | **50.0 GW** | 55.4 GW |
| solar | −60 % | **−40 %** | — |

and the mid-window price/reserve objects land onto measured levels for the first
time in this posture.

---

## 3. THE EPOCH

This promotion **re-bases every ERCOT hindcast**. It IS an epoch and is declared
as one.

**Every pre-epoch ERCOT hindcast sidecar is now historical record and NEVER a
baseline for post-epoch comparison — FH-5's own ERCOT legs included.** That is
expected and was the entire point of the ordering: FH-5 landed complete and
committed FIRST, so its horizon table is a finished artifact, not a casualty.

- **FH-5 is NOT re-solved and NOT "refreshed."** Its §4 table stands as delivered.
- **For reproducers:** FH-5's artifacts were produced at `src/` == **`3ae7465`**
  (its §3 pin), which is NOT this branch's head.
- The pinned default cache key **MOVES**. The epoch is declared and the
  cache-key-pin CI verdict is awaited before any merge.

---

## 4. GOVERNANCE (pre-registered)

- **Rule 28, ONE COMMIT.** The ERCOT shard's cells in
  `docs/codebase-site/data/mechanism-matrix/ERCOT.js` +
  `_CACHE_KEY_OPTIONAL_FIELDS` + the defaults ledger land in a single commit.
  `scripts/check_mechanism_matrix.py` runs before the push. The base
  `docs/codebase-site/data/mechanism-matrix.js` is edited ONLY if a NEW MECHANISM
  ROW is owed; its visible keeper stamps are the FROZEN pre-2026-08-11 log and
  are not "updated".
- **Rule 15.** Forecast/hindcast namespace only, via
  `scripts/register_forecast_run.py`.
- **Rule 22.** Forecast/hindcast years only; holdout freeze ACTIVE; ERCOT holds
  no marker (`complete` = {NEISO, NYISO, PJM}; `final` EMPTY).
- **Rule 12.** ≤5 solve-years per invocation, sequential; ≤2 concurrent.
- **Rule 25.** A MISO lane (ARM-3-ARM) may run beside this one; this lane is
  ERCOT and never touches MISO's shard, defaults or verdicts.
- **Rule 27.** Opus; blob-verify any push touching a ≥300-line file.
- **E10 attestation.** This lane PROMOTES, so it writes a C6 governance
  attestation including `"schema": "calibration-attestation/v1"`
  (`audit_keepers.py` checks completeness — caiso-188 was found promoted with no
  attestation at all).
- **Scenarios.py insertion convention.** ERCOT-prefixed / ERCOT-scoped rows go at
  the END of ERCOT's own cluster; `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` gets the
  same discipline in the SAME commit. No legacy entry is reordered. On conflict,
  resolve BY UNION (an edit was lost taking one side wholesale at `c5593684`).
- **Clean-partition guard.** This recipe arms neither
  `capacity_deliverability_limits` nor `hydro_ror_split`, so
  `check_clean_partitions` is a no-op for it; `scripts/regenerate_clean.py` is
  still run as the cold-container prerequisite because `data/clean/` is
  gitignored and the solves read it.

---

## 5. CONTAINER PROVENANCE — a dead clone, and what it cost

Recorded because it bears on reproducibility, not as an excuse.

This container's initial clone **never completed**. `/home/user/market-simulator`
held only a `.git` with: a 6.7 GB `objects/pack/tmp_pack_vuG112` with **no
`.idx`** (an `index-pack` that never finished), a stale `shallow.lock` with no
`shallow`, a 0-byte `FETCH_HEAD`, an empty `refs/`, and zero commits. `git status`
reported "No commits yet."

This is the documented failure mode in `docs/fast-clone.md` — an ~11.5 GiB pack,
~97 % immutable `data/raw/` binaries, stalling through the egress proxy. Recovery
followed that doc: the dead `.git` was removed (reclaiming 6.7 GB) and replaced
with `git clone --filter=blob:none`. **The whole history graph transferred in
12.22 MiB**; the original clone died moving historical blobs it never needed.

A plain `git push` from the resulting partial clone also stalls (verified: timed
out at 2 min, ref absent from `git ls-remote` afterwards), so this lane pushes
via the GitHub API exactly as `docs/fast-clone.md` and CLAUDE.md require.

Two things this lane did NOT do and that remain open for the owner:

1. The environment-side clone filter (fast-clone.md's "highest-leverage fix,
   needs no code change") is still unset — every new container repeats this.
2. `.claude/hooks/session-start.sh` cannot repair the zero-commit case: it runs
   `uv sync` first under `set -euo pipefail`, and with no working tree there is no
   `pyproject.toml`, so the hook aborts **before** reaching its blobless
   fast-forward. In precisely the case the repair exists for, it is unreachable.

Neither is this lane's object and neither is fixed here (no silent infra change).

---

*(Sections below are filled AFTER the pre-registered work runs, in order, as
produced.)*
