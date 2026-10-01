# ADDENDUM B to PRECOMMIT-capx-d75r-arm-2026-09-06 — steps 3–4: THE KEY, DECLARED BEFORE THE SOLVE

**Lane:** capx D75-R-ARM **steps 3–4**, released by the r#54 charter re-emission. **Branch:**
`claude/capx-d75r-arm-steps34-mc5342`, fresh off `origin/main` **`f37121bd`** (0 ahead / 0 behind at
branch creation). **Date:** 2026-09-07. **Model:** Opus. **DATA PROFILE:** `pjm`.

**Pushed before any LP is spent.** Every key, classification and expectation below was measured at
`f37121bd` with **zero LP**, through the shipped harness path, and is recorded here so it cannot be
written to fit a result.

**The parent PRECOMMIT's §0 (steps 3–4 HELD behind D65-B-R) is DISCHARGED**, verified rather than
taken on the charter's word: `c36a3fe7` *"capx D65-B-R board write: the six t1f legs register, NEISO
and NYISO included"* is an **ancestor of my head**, merged as **PR #5283** (`05198bc6`). One nuance
recorded because it is load-bearing for §5 and for nothing else: that commit wrote the **six
`frontend/data/hindcast/*-d65br-arm.json` sidecars** plus `invariant-failures.json` — it did **not**
write `program-status.json`, which still contains **zero** occurrences of "D65-B-R", nor
`ff-verdicts.json` (also zero `d65br`). That is the namespace working as CLAUDE.md rule 15 describes
(the board is GENERATED from the committed sidecars + the two seed files), and it is exactly the
distinction the charter's closing NOTE asks this lane to resolve from the code path — resolved in
§5.

---

## 1. THE KEY QUESTION — ANSWERED, AND THE ANSWER IS **NOT** THE ONE THE CHARTER'S BODY NAMES

The charter's r#54 amendment names three vintages of the bare `pjm-t1h` key and forbids assuming
which applies. **D78-ARM HAS MERGED.** It is in `origin/main` at my head, in two commits:

| commit | what |
|---|---|
| `24311a95` | capx D78-ARM: `retirement_sector_gate` ARMED for PJM (owner ruling **Q56**) |
| `fd2a0d18` | the PR #5319 salvage (merged as **PR #5373**, `f37121bd`) — the arm reproduces at HEAD, census re-measured 25/173, `TestQ52ArmingKeys` re-pinned |

**So the charter's branch B applies, and this lane's row carries `fb16fda2ddb0a94a` — not the
`b518f5fe7d02f961` the charter's body names.** Stated explicitly here, before the solve, exactly as
the charter requires ("say so explicitly rather than silently registering a different key").

### 1.1 The measurement, not the test pin

Measured through `build_config(iso, 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True, **flags)` → `apply_iso_scenario_defaults` → `cache_key()`, the
`TestQ52ArmingKeys` path — instrument
`scripts/probes/capxd75rarm_steps34_key_declaration.py`, output
`docs/handoffs/d75rarm/steps34-keys.json`, both committed with this addendum:

| recipe | key at `f37121bd` | what that key IS |
|---|---|---|
| **bare `pjm-t1h`** | **`fb16fda2ddb0a94a`** | **THE ROW.** Q55 **and** Q56 both armed |
| `--no-retirement-sector-gate` | `b518f5fe7d02f961` | the D75-R-ARM / Q55 posture — **and D75-R's own measured full-window arm** |
| `--no-pjm-vre-accreditation-vintage` | `bb6a60239d69508b` | D78-R2's own measured arm (the gate without Q55) |
| both `--no-` flags | `a9c66d8ea25acb9d` | the D67-ARM posture = **the committed `pjm-t1h` bundle**, i.e. this row's control |
| D57 off3, Q55+Q56 on | `f1a9881ed29df6cb` | |
| D57 off3 + `--no-gate` | `1785cb6086cd2b15` | PRECOMMIT §2.1's post-D75-R-ARM literal |
| D57 off3 + `--no-vre` + `--no-gate` | `61dfbc5c48af076b` | PRECOMMIT §2.1's pre-arm literal ✔ |
| D57 off3 + `--no-gate` + `--no-req-pub` | `d2fe4e2b32aef073` | PRECOMMIT §2.1's post-arm literal ✔ |
| D57 off2 (arm B), Q55+Q56 on | `944c89de0a74ca63` | |
| D57 off2 + `--no-gate` | `ab0237198cff24ad` | PRECOMMIT §2.1's post-arm literal ✔ |
| D57 off2 + `--no-vre` + `--no-gate` | `2d5bebd2bceed991` | PRECOMMIT §2.1's pre-arm literal ✔ |
| D57 off2 + `--no-gate` + `--no-req-pub` | `05cdf4af2b9adef8` | PRECOMMIT §2.1's post-arm literal ✔ |
| MISO · NYISO · NEISO · CAISO · ERCOT bare | `1f92943f84f42fd0` · `ee6a3e764324f28f` · `5b292e24dd752ea4` · `8f1c3766703a90c4` · `46d013cbf1f35d27` | **all five byte-identical to PRECOMMIT §2** (rule 25 `[R-ISO-SCOPE]`) |

**Every one of PRECOMMIT §2 / §2.1's D75-R-ARM literals reproduces to the digit at `f37121bd`**, one
axis (Q56) later. Nothing in this addendum re-derives them; they are re-measured and they hold.

**A probe defect worth recording, because it produces a plausible wrong answer.** Setting the
override attributes on an already-built `ScenarioConfig` and calling `apply_iso_scenario_defaults`
afterwards silently re-arms every field, and all twelve PJM legs then collapse onto
`fb16fda2ddb0a94a` — a table that looks like a finding ("the flags are inert!") and is an artifact.
The overrides must go **through `build_config`**, as explicit CLI-caller arguments. Hit and corrected
before any leg was reported; the committed probe carries the correct shape and says why.

### 1.2 THE FOUR D57/D67 CONTROL LEGS MOVE — pre-declared here, as the precedent requires

`FINDING-capx-d67arm-2026-09-06.md` §2.1 recorded exactly one miss against its own PRECOMMIT: a leg
that turns off three named fields and says nothing about a fourth carries the fourth armed. The
parent PRECOMMIT §2.1 pre-declared that for Q55's four legs. **The same thing happens again for Q56,
to the same legs, and it is named here rather than discovered:** `f1a9881ed29df6cb` (off3) and
`944c89de0a74ca63` (off2) are the post-Q56 keys of legs whose pre-Q56 literals were
`1785cb6086cd2b15` / `ab0237198cff24ad`. The cause is structural and unchanged — both fields are
`_CACHE_KEY_OPTIONAL_FIELDS` members registered at `False`, so each is dropped from the hash while
unarmed and enters it once armed, on every PJM forecast leg whatever the other flags say. **Not a
defect. The arm is fully invertible**: the two-flag leg reaches `a9c66d8ea25acb9d` exactly, so every
pre-arm recipe stays both reachable and identified.

---

## 2. WHAT THIS MEANS FOR THE ROW — the honest consequence, stated at the gate

At `f37121bd` there is **exactly ONE bare `pjm-t1h` recipe**, and it carries **both** ruled arms. Two
consequences follow, and neither is optional:

1. **The row this lane registers is a JOINT Q55+Q56 posture.** It is *not* the isolated
   VRE-devintage arm the D75-R A/B measured (`b518f5fe7d02f961`), and **no number in it may be
   attributed to Q55 alone.** The Q55-only attribution already exists and stays where it was
   measured: `FINDING-capx-d75r-2026-09-06.md`'s A/B, control `a9c66d8ea25acb9d` → arm
   `b518f5fe7d02f961`, on one base. This registration does not re-open, re-measure or supersede it.
2. **This solve IS the solve D78-ARM still owes.** `docs/handoffs/d78arm/run_arm.sh` and this lane's
   step 3 are the same invocation at the same key against the same control — `FINDING-pr5319-d78arm-
   salvage-2026-09-07.md` §4 item 1, verbatim: *"the armed `pjm-t1h`, key `fb16fda2ddb0a94a`, PJM
   solo, years sequential (rule 12), HEAD-guarded."* There is no second row to solve. Registering it
   once therefore discharges **both** lanes' registration duty, and the collision clause applies as
   written: this lane lands first and states its key; D78-ARM COMPLETION rebases and re-declares
   rather than assuming, and **must not solve or register a second `pjm-t1h`**.

   Rule 19 `[R-ONE-MECH]` in its registration form: one recipe, one row, one bundle.

**This lane touches no `retirement_sector_gate` code, config, test, help string or matrix cell** —
the charter's DO-NOT is honoured to the letter. What it cannot do is un-arm the field: Q56 is in
`_pjm_config` at HEAD, so it is in the recipe. Carrying an armed field that another lane owns is not
touching it.

### 2.1 The preserved prior — and why the charter's name is the CORRECT one on the merits

The charter names `pjm-t1h-pre-d75rarm`. D78-ARM's held `VERDICT_MAP` hunk names the same bundle
`pjm-t1h-pre-d78arm` (salvage §3). **They are not interchangeable, and the charter's is right:**

- the bundle being preserved is `pjm-2021-2025-realized-t1h-d67arm`, key `a9c66d8ea25acb9d`;
- that key is the posture **immediately before D75-R-ARM**, which is what `-pre-d75rarm` says;
- the posture immediately before **D78-ARM** is `b518f5fe7d02f961`, and **no bundle at that key
  exists to preserve** — D76-P3B solved it as its own control and deleted it before merge under rule
  29(c), which the charter's own note says does not discharge anything.

So `-pre-d78arm` would label an `a9c66d8ea25acb9d` bundle with a `b518f5fe7d02f961` posture's name.
**This registration uses `pjm-t1h-pre-d75rarm`**, and D78-ARM COMPLETION should adopt it rather than
create a second alias for one object.

---

## 3. G-DRIFT — rule 29(b), re-run for THIS window

Form-4 differencing needs the audit over **the control bundle's own sha → my head**, not the parent
PRECOMMIT's window. The control is the committed `pjm-t1h` (`pjm-2021-2025-realized-t1h-d67arm`),
whose sidecar provenance records `scored_at_sha` **`9911ff21f42e`**. Window
**`9911ff21f42e` → `f37121bd`**: **22 non-merge commits** on the solve path
(`src/market_sim scripts/run_capacity_hindcast.py scripts/lib data/raw/_validation-source
data/raw/reference`).

**THREE commits are LIVE, and all three are THE OBJECT:**

| commit | what | classification |
|---|---|---|
| `f3d0396e` + `6164231e` | capx D75-R's build + **the Q55 arm** | **LIVE — THE OBJECT.** What this lane registers |
| `24311a95` + `fd2a0d18` | **the Q56 arm** + its salvage | **LIVE — THE OBJECT**, owner-ruled, in the recipe at HEAD, and the reason §2 exists |

**Every other hunk is INERT, with its reason:**

| commit(s) | what | why INERT |
|---|---|---|
| `8ad280ed` | capx D76 phase 1 — measured-hindcast screen-peak gate (`runner.py` +101) | GATED `capacity_screen_peak_measured_hindcast`, dataclass default **False**, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at False. Hunk inspected line by line: the new branch is guarded by `config.capacity_screen_peak_measured_hindcast and config.hindcast and not is_crossover_forward_year`; the `else` limb is the pre-existing `_scale_demand` + `add_load_layers` verbatim, and the `_hindcast_measured_demand` extraction passes the identical `load_demand` arguments and the identical truncation. Value-preserving while off |
| `20611146` | pjm-169 F4 — gas-offer margin anchor | GATED `gas_offer_margin_anchor_vintage` default **False**, registered at False; the commit touches `scenarios.py` only (field + registration) |
| `15fc14ac` | pjm-169 F2 — **"ARM the PJM interface-feed admissibility gate"** | **Armed in `pipeline/backcast_config.py` ONLY**, never in `_pjm_config`; the dataclass default stays `False` (`scenarios.py:14558`) and a `mode="forecast"` hindcast never enters `backcast_config`. Measured: the resolved PJM hindcast posture reads `pjm_interface_feed_admissibility_gate=False` at HEAD. The word "ARM" in the subject is a **backcast** arm |
| `cd96fa26`, `beb74f0f` | pjm-167 F2/F1 builds | GATED, default False, registered at False; backcast-runner-only (parent PRECOMMIT §3, re-verified) |
| `14ae4d76`, `caa2936e`, `0e769df0` | MISO seam ladders + CT drag | GATED `miso_seam_neighbour_hourly_ladder` / `_spp` default **False**, registered at False; MISO-scoped besides (rule 25). MISO's bare key is unmoved from PRECOMMIT §2 |
| `9ee67e3c`, `24aeed4e`, `18507f13`, `de0166b9`, `62681e22` | SPP registered as the seventh ISO | Another ISO's branch. Measured, not asserted: their `iso_configs.py` hunks add SPP's own config; **every `pjm`-matching changed line in all five is a comment**, and the five non-PJM bare keys plus PJM's are byte-identical to the literals declared before these merged |
| `16210868` | capx D79 — solve-surface fingerprint | INERT in FROZEN-HASH form (parent PRECOMMIT §3, re-verified: the bare key at HEAD equals the literal the D78-ARM PRECOMMIT measured before/after these merges) |
| `bf97317f` | capx D78-R2 STEP 0 — delete producer-less `exempt_unit_ids` | Removing a branch whose guard was always `False` (parent PRECOMMIT §3) |
| `b8e0c537`, `caaa3e05`, `7ff10b64`, `486c115f` | ERCOT RRS series · CAISO-260 promotion · ruff format (AST-identical) · constants re-export | Other ISOs / no behaviour. ERCOT and CAISO bare keys unmoved |

**Verdict: the ONLY live drift is the two ruled arms.** Form 4 is therefore valid *for what it is
asked to do here* — and note this row is a **ruled registration, not an A/B**, so no control solve
is earned and none is spent (rule 29(b)). The control is the committed `pjm-t1h` bundle, differenced,
never re-solved.

## 3.1 Rule 29(a) — why there is no screen solve

Unchanged from the parent PRECOMMIT §4: 29(a) exists to *select* an arm before spending a span.
There is nothing to select. Both arms in this recipe are owner-ruled (Q55, Q56) on already-spent
full-window A/Bs. This lane executes ruled arming and spends exactly **one** invocation.

---

## 4. DECLARED BEFORE THE SOLVE — graded at full magnitude, whatever they read

**D-1 (the declaration the charter demands).** The realized `cache_key` written into
`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/meta.json` will be
**`fb16fda2ddb0a94a`**. **If the realized key is not that literal, this lane STOPS and reports** — a
mismatch means the arm does not reproduce the recipe the A/Bs were measured on and the Q55/Q56 bases
need re-reading. Realized-vs-declared is reported either way.

**D-2 (the HEAD guard).** `H0=$(git rev-parse HEAD)` = `f37121bd951fb3b40c74cd866968303ec3d9f9c2`;
the solve runs PJM solo, years 2021–2025 **sequential** in ONE invocation (rule 12
`[R-PARALLEL]`); `[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`. **No commit is made while the
solve runs** (the error `FINDING-capx-d75r` §7 item 1 records).

**D-3 (the invariant bar).** D67-ARM's: **all 14 invariants PASS**, verified live in the committed
control sidecar (I1–I14, 14 PASS / 0 FAIL / 0 WARN). D75-R measured all 26 scored bands
byte-identical between its control and arm, so Q55 contributes no invariant risk; **Q56 is the axis
that can move one**, and any FAIL is DECLARED against the leg's own committed prior in the same
commit (the Y-24 ratchet). A declaration is not a fix: nothing is relaxed, re-scored or exempted.

**D-4 (FC-3, reported and gated on nothing).** The control column is read row-by-row out of the
committed `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d67arm.json`. The arm column is the
**joint** posture, so the predictions below are composed from the two ruled findings and are
explicitly **not** an attribution of either arm:

| FC-3 row | control (committed `pjm-t1h`) | Q55 alone (D75-R §5.2) | Q56 alone (CLAUDE.md / D78-R3 §5) | joint expectation |
|---|---:|---:|---:|---|
| `retirements.total_gw` (actual 15.062) | **18.058** | 17.294 | 15.937 | **falls; may cross FAIL→PASS** |
| `false_retire.false_gw` | **8.065** | 7.596 | — | falls, **stays FAIL** |
| `unit_recall_gt300.recall` | **0.650** | 0.650 (unchanged) | **0.550** | **FALLS — a partition removing matched sector-1 exits must** |
| `plant_release_precision.window.all` | **0.421** | 0.439 | — | rises, reported-only |
| 2025/26 clearing price ($/MW-day) | — | — | 358.267 → 236.945 | moves on the steep VRR limb |

**Stated at the gate, ex ante:** `false_retire` is expected to stay FAIL and `unit_recall_gt300` is
expected to **fall**, because a sector partition removes matched exits along with false ones. That is
the honest reading of both mechanisms and it is written here **before** the solve so it cannot be
framed as a success afterwards. Neither is a criterion in either direction (Q56 was ruled on
structure, Q55 on rule 14 `[R-ACCURATE]`), and the CT / ST / oil zero-E&AS operand (D57 §4) remains
the named successor for the retirement bands. Nothing is re-tuned in response (rule 1 `[R-STRUCT]`).

---

## 5. WHICH ARTIFACT THE REGISTRATION TOUCHES — resolved from the code path, not assumed

The charter asks this to be determined from the code and stated. Read at `f37121bd`:

* `scripts/register_forecast_run.py` declares `HINDCAST_DIR = frontend/data/hindcast` **"the CANONICAL
  per-run record"** and writes `frontend/data/hindcast/<id>.json`. Everything else it emits —
  `registry/<id>.json`, `runs/<id>.js`, `manifest.js`, `program-status.js` — is the **gitignored
  generated namespace**, whose single writer is the Pages deploy (`--reindex` regenerates it locally
  for the `file://` preview only).
* `ff-verdicts.json` is **READ, never written**, by that script: `_load_verdicts` resolves
  `FORECAST_DIR / "ff-verdicts.json"` as a verdict *source*, and the module docstring names it a
  **"COMMITTED input (the source, NOT output)"** beside the `program-status.json` board seed.

**So this registration touches `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d75rarm.json`** (plus
`invariant-failures.json` if the run posts one), **and not `ff-verdicts.json`.** The corroborating
evidence is already committed and is worth naming because it looks like staleness and is not: the live
`ff-verdicts.json` `pjm-t1h` entry still carries `run_id = pjm-2021-2025-realized-t1h-d57-clearing`,
`cache_epoch = f0e050e820c1159a` — i.e. **D67-ARM's own registration did not move it either**, for the
same reason. A verdict snapshot moves when a verdict moves; the D65-B-R batch, which did register six
runs, moved neither seed file.

The one non-sidecar edit this registration DOES carry is the `VERDICT_MAP` re-key inside
`register_forecast_run.py` itself (`pjm-2021-2025-realized-t1h-d67arm` → `pjm-t1h-pre-d75rarm`, and the
new bundle → `pjm-t1h`), which is correct **at** registration and wrong before it — the reason the
D78-ARM salvage explicitly held its own version of that hunk (salvage §3).

---

## 6. What this addendum does NOT claim or do

It arms nothing further. It moves no `ScenarioConfig` default, no registry value, no marker, no
freeze file, no calibration determination, and no other ISO's shard or cell (rule 25 — PJM only). It
does not touch `retirement_sector_gate` in any artifact. It does not re-open D75-R's A/B, D78-R3's
window, or any adjudicated matrix cell. It writes **no** board file: `program-status.json` and
`ff-verdicts.json` are not this lane's, and the registration path that is used
(`scripts/register_forecast_run.py`, the SINGLE path, rule 15) writes the per-run hindcast sidecar —
`ff-verdicts.json` moves only when a verdict moves, which is determined from the code path and
reported in the close, not assumed here.

It does not claim either arm closes what its own finding says it does not: the model still
over-retires against 15.062 GW actual, `unit_recall_gt300` does not improve, and the 2024/25 and
2025/26 census stay below the published cleared position — D66 card B's remaining half, routed and
untouched.

---

## 7. RE-MEASURED AT `abdd30c9` — the declaration HOLDS, and one non-PJM literal in §1.1 does not

`origin/main` advanced **45 commits** (`f37121bd` → **`abdd30c9`**) between this addendum's push and
the solve. The addendum's own commit (`df1cda74`) is among them, so the branch fast-forwards rather
than diverging. Because §4's D-1 declaration and §3's G-DRIFT window were both pinned to `f37121bd`,
**the key was re-measured at the new head before the solve was started** — a solve launched at a
stale head either trips its own guard or registers a key that was never declared.

**Instrument:** the same probe, unmodified. **Output:** `docs/handoffs/d75rarm/steps34-keys-abdd30c9.json`,
committed beside the `f37121bd` measurement so both are inspectable.

**Result: every one of the twelve PJM legs is byte-identical to §1.1.** The bare row is
**`fb16fda2ddb0a94a`**, the three inverse legs are `b518f5fe7d02f961` / `bb6a60239d69508b` /
`a9c66d8ea25acb9d`, and the four D57/D67 control legs and their inverses all reproduce. **The D-1
declaration stands unchanged and the solve proceeds against it.** The resolved PJM forecast posture
is also unchanged field for field, `pjm_interface_feed_admissibility_gate=False` included.

**One literal in §1.1's last row is now WRONG, and it is corrected rather than quietly restated.**
ERCOT's bare key moved **`46d013cbf1f35d27` → `f18431f2447bad01`**. §1.1 declared all five non-PJM
bare keys "byte-identical to PRECOMMIT §2"; that is true of MISO, NYISO, NEISO and CAISO at
`abdd30c9` and **false of ERCOT**. The cause is ERCOT's own lane, not this one: `09c812aa`
(*ercot-253 PRECOMMIT: the 2021 validation rung, its four measured-input extensions, and the
published pre-Uri ORDC order parameters*) is the only commit in the window touching
`src/market_sim/config/`, and neither `iso_configs.py` nor `scenarios.py` changed in it at all.

Reported at full magnitude and **not** a defect in this lane's act: rule 25 `[R-ISO-SCOPE]` says a
lane owns its own ISO, and the property §1.1 was actually asserting — that **the Q55 arm moves no
non-PJM key** — is untouched, because the mover is another ISO's measured-input act rather than
anything in `_pjm_config`. The four non-PJM keys that a PJM override could plausibly have disturbed
are all still exactly where the PRECOMMIT put them.

**G-DRIFT extension over the 45 commits:** the window adds no `_pjm_config` edit, no
`scenarios.py` edit and no PJM forecast-path change — measured, and independently corroborated by the
twelve unmoved PJM keys, which is the strongest available statement that the PJM solve surface did
not move. `b4f1da55` (*capx D76-ARM: the (b′-1) route cannot land at zero key moves — STOP fires,
nothing armed*) is the one capx arming attempt in the window and it **armed nothing**. The lanes that
did land — ercot-253, the SPP-2x/3x/5x series, miso-233/234/235, nyiso-211, SCN-DESK — are all other
ISOs' or non-solve. **The §3 verdict is unchanged: the only live drift on this row is the two ruled
arms.**

**The HEAD guard is re-pinned:** `H0` = `abdd30c92058133677f22c6a84ec2852fd9175b6`.
