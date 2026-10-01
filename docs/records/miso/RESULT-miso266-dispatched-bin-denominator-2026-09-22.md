# RESULT — miso-266: the dispatched-bin derate denominator, solved across all six years

```
SESSION : miso-266        ISO: MISO
KEEPER  : 2026-09-20-miso-264-anchor-vintage — UNCHANGED. Nothing promoted, nothing pruned.
SOLVED  : 12 legs, six years x (control, arm), one flag apart, each pair in ONE container
          at ONE pinned SHA 927f68aff8fabafb57d451f9cf4d4fe726c7e69e.
VERDICT : the mechanism does what its construction says. COAL_BIT +11.535 TWh and
          COAL_PRB +8.652 TWh over the span; C1 2020 COAL_BIT -10.92 -> -6.93.
          The pre-registered adverse move HAPPENED: C1 2022 COAL_PRB +8.13 -> +10.52.
BLOCKED : REGISTRATION, on a benchmark-frame question that is itself a finding (§5).
          NOT registered, NOT scored through calibration_verdict.py, NOT promoted.
ASK     : the promotion question is §7, and it is genuinely open.
```

---

## 1. WHAT WAS SOLVED

Twelve legs. Each year's control and arm ran **in the same container, at the same
SHA, from the same keeper recipe**, differing in exactly one `ScenarioConfig`
field. Config signatures verified on all twelve before any number was read: the
flag `False`/`True`, `miso_measured_reserve_requirements` matching each year's
partition leg, and `unit_outage_per_unit_clip` / `st_capacity_basis` /
`mixed_gas_routing` / `fleet_status_scope` all `True`, `outage_source: historic`.

| year | branch | leg-A wallclock |
|---|---|---|
| 2020 | `claude/miso266b-y2020` @ `b749029109a463043764c98237f83cee8803a998` | — |
| 2021 | `claude/miso266b-y2021r` @ `2109b2f2a93bc42c9173a05b061eaa1aa69d9311` | 14m43s |
| 2022 | `claude/miso266b-y2022` @ `fa92f7b8678419e745ac52ae1a1439a40b2f0203` | — |
| 2023 | `claude/miso266b-y2023` @ `ee7e718e5c36aa195618880ed3f4f270b38c86de` | — |
| 2024 | `claude/miso266b-y2024` @ `8af359794eab8bc53bda445cb0eca84d6d5132c6` | — |
| 2025 | `claude/miso266b-y2025` @ `9266e88b5eec14b1d7573693f2e1a4a660fdbf85` | — |

The first 2021 shard **stalled** — idle 72 minutes mid-solve, no branch — and was
archived and replaced (`y2021r`). Its replacement's prompt added one line the
others lacked: *run each solve in the foreground and do not end a turn while one
is in flight*. That fixed it. Worth carrying into future shard prompts.

## 2. THE MECHANISM, MEASURED — `scripts/probes/_miso266_ab_readout.py`

### 2.1 Price

| yr | keeper | control | drift | arm | arm − ctl | cells moved |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 25.356 | 25.356 | **+0.000** | 24.969 | −0.386 | 61,436 |
| 2021 | 40.307 | 40.307 | **+0.000** | 39.576 | −0.731 | 64,096 |
| 2022 | 60.453 | 60.453 | **+0.000** | 59.933 | −0.520 | 63,842 |
| 2023 | 33.909 | 33.909 | **+0.000** | 33.545 | −0.364 | 62,334 |
| 2024 | 31.254 | 31.254 | **+0.000** | 31.008 | −0.246 | 60,962 |
| 2025 | 42.984 | 42.984 | **+0.000** | 42.602 | −0.382 | 60,557 |

### 2.2 Per-class TWh, arm minus control

| yr | COAL_BIT | COAL_PRB | COAL_LIG | CC_REG | ST_GAS | CT_PEAK | import | CC_CHP | ST_CHP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | +3.987 | +1.010 | −0.076 | −1.583 | −0.879 | −0.635 | −0.920 | −0.759 | −0.082 |
| 2021 | +3.232 | +1.522 | −0.087 | −2.015 | −0.537 | −0.561 | −0.718 | −0.701 | −0.089 |
| 2022 | +0.897 | +2.393 | −0.062 | −1.424 | −0.551 | −0.172 | −0.728 | −0.291 | −0.028 |
| 2023 | +0.729 | +1.701 | −0.051 | +0.030 | −0.535 | −0.800 | −0.739 | −0.268 | −0.033 |
| 2024 | +1.203 | +1.265 | −0.011 | −0.254 | −0.321 | −0.959 | −0.570 | −0.293 | −0.027 |
| 2025 | +1.486 | +0.761 | −0.023 | −0.876 | −0.135 | −0.571 | −0.399 | −0.204 | −0.023 |
| **SPAN** | **+11.535** | **+8.652** | −0.310 | −6.123 | −2.959 | −3.699 | −4.074 | −2.517 | −0.282 |

**Coal is up in every single year and every gas/import class is down.** Total
generation is conserved to ±0.0043 TWh in five years; 2021's −0.0228 TWh is
storage round-trip loss (more coal changes the battery cycling), confirmed by
that shard against a 642.28 TWh demand that closes on both legs.

**The CC_CHP and ST_CHP moves are merit-order displacement, not a changed
availability envelope** — the flag excludes those bins by construction, and
`_miso266_chp_exclusion_check.py` proves it on the real fleet: all 121 CHP bins
byte-identical (max |Δ availability| exactly 0.000000) while COAL moves 28 bins,
CC_REGULAR 24 and ST_GAS 5.

## 3. C1, AGAINST THE COMMITTED BENCH

Computed directly from the committed `bench/MISO/*.json.gz` actuals and the
bundles' own dispatch — **no registration, no re-based benchmark** (see §5).
The control column reproduces the keeper's published misses exactly, which is
what validates this readout: 2020 COAL_BIT −10.92 and 2022 COAL_PRB +8.13 are
the charter's own numbers.

| year | class | actual | control err | arm err | |
|---|---|---:|---:|---:|---|
| 2020 | **COAL_BIT** | 66.27 | **−10.92** | **−6.93** | better by 3.99 |
| 2020 | COAL_PRB | 126.68 | −4.76 | −3.75 | better |
| 2020 | CC_REGULAR | 106.91 | +3.98 | +2.39 | better |
| 2021 | COAL_BIT | 77.20 | −6.54 | −3.30 | better by 3.23 |
| 2021 | CC_REGULAR | 103.82 | −2.02 | −4.03 | **worse** |
| 2022 | **COAL_PRB** | 149.69 | **+8.13** | **+10.52** | **WORSE by 2.39** |
| 2022 | CC_REGULAR | 125.57 | −5.59 | −7.02 | **worse** |
| 2023 | COAL_PRB | 121.67 | −1.55 | +0.15 | better |
| 2024 | COAL_BIT | 53.33 | −4.27 | −3.07 | better |
| 2024 | CT_PEAKER | 19.22 | +3.15 | +2.19 | better |
| 2025 | COAL_PRB | 146.10 | −10.61 | −9.84 | better |
| 2025 | CC_REGULAR | 138.19 | −0.65 | −1.52 | **worse** |

**The pre-registered adverse move happened exactly as predicted.**
PRECOMMIT §6 item 2 said C1 2022 COAL_PRB "is +8.13 TWh long and the repair
hands PRB capability back. If it deepens, that is reported at full magnitude and
is not a reason to narrow the mechanism's scope." It deepened to **+10.52**. It
is reported, and the scope is unchanged.

**CT_PEAKER gets worse in four of six years** (2020, 2021, 2023, 2025) — it was
already short and the arm takes more off it. Not predicted, reported.

## 4. THE G-DRIFT CALL WAS WRONG, AND THE CONTROL LEGS ARE WHAT PROVED IT

PRECOMMIT §4 concluded form 4 was void and spent six control solves on that
basis. **Measured worst per-class drift across all six years: 0.000008 TWh** —
eight kWh on totals of 5–160 TWh, against a stated 1e-4 TWh tolerance.

The keeper's own `meta.json` records `composed_from` as **six single-year
bundles**, already year-isolated. Rule 36's 7–24 TWh divergence was measured
against a keeper solved as multi-year legs; this is not one. I reasoned from the
rule's general statement instead of reading the artifact's provenance.

What the spend bought, stated without inflation: form 4's validity is now
measured rather than argued, and **the 749-line solve-path drift between the
keeper's `23b5d44e` and the shard `927f68af` — PERF-C S1/S2, `model/lp/rows.py`,
`pipeline/solve.py` — is measurably INERT on MISO.** Full correction in the
PRECOMMIT's own §4 correction block.

## 5. REGISTRATION IS BLOCKED, AND THE BLOCKER IS A FINDING

Registration fails at `render_calibration_html.build_payload`, which needs the
benchmark frames from the gitignored shared store `results/calibration/_shared/`
— a SIBLING of the bundle dir that a shard's `git add <out-dir>` cannot carry.
That is the exact gap commit `7fd12b91` was written to close, and its named
remedy `--restore-shared-inputs` regenerates the frames at zero LP and verifies
each against the hash `meta.json` records.

**It refuses, and it is right to:**

```
'campd' REGENERATED TO DIFFERENT BYTES than the solve read.
  meta.json records : ../_shared/MISO/campd-d5fd8457f1fe.parquet
  rebuild produced  : ../_shared/MISO/campd-d57af607eaf4.parquet
```

**The benchmark builders have changed between the shard SHA and HEAD.** Adopting
the new frame would re-base a scored run's benchmark against a dispatch solved on
the old one. The guard re-points nothing and writes the new file as an unreferenced
store entry.

**I did not force past it**, because `--rebuild-benchmark` would regenerate the
committed `bench/MISO/*.json.gz` parts — MISO's actuals for **every registered
run including the keeper**. That is precisely the NYISO incident
`calibration_verdict.py` documents, where a regenerated part moved a metered
actual by ~4 TWh and flipped every registered NYISO run to NOT-YET. The charter's
own instruction is *"BEFORE REGISTERING: diff bench parts against HEAD, confirm
ZERO movement."* It does not confirm; it moves.

### 5.1 AMENDED — there are TWO defects here, and one test separates them

My first reading of §5 named a single cause ("the benchmark builders have
changed"). Checking the artifact's provenance — which is the step I had already
skipped once this session, in §4 — shows **two independent defects**, and the
evidence I first cited could not tell them apart.

**Defect A — the frames are PER-YEAR and the composer copies only the first
year's reference.** Measured over the six control bundles:

| input | distinct hashes across the six years |
|---|---|
| `eia930`, `eia923`, `campd` | **6 — one per year** |
| the six `unit_outages*` frames | 1 — shared |

The composer (inherited from `_miso260_compose_span.py`) writes the first leg's
whole `shared_inputs` block into the composite's `meta.json`, so
`miso266_ctl_span` claims **2020's** `campd-d5fd8457f1fe` as if it covered
2020–2025. `--restore-shared-inputs` then rebuilt a six-year frame and compared
it against a one-year hash. That comparison could never have matched, whatever
the builders were doing. **This is a composer defect, it is inherited rather than
introduced here, and another lane reports fixing the same object independently.**

**Defect B — the builders really have drifted, and this is what proves it
separately.** Running the same restore against the **single-year** 2020 control
bundle, where the composer cannot be implicated at all:

```
'eia923' REGENERATED TO DIFFERENT BYTES than the solve read.
  meta.json records : ../_shared/MISO/eia923-4b912c050da4.parquet
  rebuild produced  : ../_shared/MISO/eia923-55e98d5c8712.parquet
```

One year, one frame, one recorded hash — and it still does not reproduce. So the
benchmark builders **did** move between the shard SHA and HEAD, independently of
Defect A.

**Both defects block registration, and each would block it alone.** Defect A is a
plumbing bug with a known fix; Defect B is the substantive one, and it is what
makes `--rebuild-benchmark` a re-basing of MISO's committed actuals rather than a
formality.

**A CORRECTION TO MY OWN EARLIER CLAIM.** I wrote that `7fd12b91`'s change is
byte-inert so "the actuals cannot have moved." That is proven for what it covers
— `require_bundle_input` is `bundle_input_path` plus a raise on the `None`
branch, so the payload renderer cannot move a number — and I **over-generalized
it**. The benchmark FRAMES are a different object with a different builder, and §5.1
Defect B shows they do move. The bench-STALE banner is still a false positive
about the *payload* fingerprint; the frame drift is real and separate.

**And a correction to the correction, stated because the sequence matters more
than the conclusion.** I first read §5's `campd` mismatch as proving Defect B on
its own. It did not — Defect A explains the same observation without any builder
drift, and I only separated them by testing a single-year bundle. The conclusion
survives; the reasoning that first reached it was not sound. **That is the same
failure mode as §4: concluding from an artifact without checking its
provenance.** Twice in one session is a pattern, and the cheap guard in both
cases was the same — read the bundle's own `meta.json` first.

The recorded `campd-d5fd8457f1fe.parquet` is **unrecoverable**: gitignored, and it
existed only on the shard containers, now archived.

### 5.2 THE SCORING SUITE NAMES THE SAME OBJECT, ACROSS ALL NINE ISOs

`pytest tests/scoring` moved 22 → 23 failures over this lane's rebase. Compared
by NAME SET rather than count, the 19 baseline failures are unchanged and there
is exactly **one** addition:
`test_bench_stamp_payload.py::test_d_every_committed_part_resolves_to_a_known_builder_state`.

It is not this branch's. It enumerates **44 committed bench parts across all
nine ISOs** — CAISO, ERCOT, MISO, NEISO, NWPP, NYISO, PJM, SOCO, SPP — all
carrying aggregate `64b6829fb757`, which `PAYLOAD_FINGERPRINT_BY_BUILDER` cannot
resolve. This branch touches no bench part, no `bench_stamp.py` and no payload
source; the failure arrived with `main`.

**And it corrects the remedy I proposed earlier.** I wrote that the fix is the
zero-LP "Y-8 re-stamp". The test states the rule itself, and it is the opposite:

> If the aggregate moved because `bench_stamp.py` was edited and NO payload
> source changed, add to `PAYLOAD_FINGERPRINT_BY_BUILDER`. **If a PAYLOAD source
> changed, the parts are genuinely stale and must be regenerated by their ISO's
> calibration desk — do NOT add an entry.**

A payload source *did* change (`render_calibration_html.py`, `7fd12b91`), so the
table entry is the wrong instrument and regeneration is the right one.

**The tension with my own proof, stated rather than resolved away.** I proved
`7fd12b91`'s change byte-inert on the payload, so regeneration would be a no-op
*for that commit's contribution*. The test cannot know that — it keys on whether
a source file's AST moved, which is the conservative and correct default. But
§5.1 Defect B shows the **frames** drifted too, and that is a real source of
movement the proof does not cover. **So regeneration is genuinely needed — just
not for the reason the fingerprint fired.** Whoever owns it should regenerate on
Defect B's evidence, not on the fingerprint's.

## 6. WHAT THIS DOES NOT CLAIM

* **No gate table.** Nothing went through `calibration_verdict.py`, so there is
  no determination, no caveat budget, no C2/C3/C4/C6/C8 verdict. §3 is C1
  evidence computed against the committed bench, not a scored run.
* **The mechanism is still argued from construction, never the residual** (rule
  1 `[R-STRUCT]`). §3 improving is not why it should arm, and §3's 2022
  regression is not why it should not.
* **84.5 % of the ceiling contradiction survives** — the level-short and
  wrong-hours shapes, plus a ~7 % nameplate numerator that **cannot** be fixed at
  a per-plant-binned ISO, which has tranches and no units.
* Nothing about any other ISO. All eight non-MISO shards carry the cell as `U`.

## 7. THE PROMOTION QUESTION — OPEN, AND IT IS YOURS (rule 31 `[R-RETAIN]`)

**What exists.** Twelve solved bundles and two composed six-year spans
(`miso266_ctl_span`, `miso266_arm_span`, 1.1 GB each), on this container's local
disk, gitignored. The twelve per-year bundles are also on their shard branches —
**transport, not storage** (rule 33 `[R-SHARD-ARCHIVE]` (f)): those refs are cut
when this lane's PR merges, so cost any recovery from them as a re-solve.

**What promotion would cost.** The bundles are at SHA `927f68af`, which is no
longer `main`. A registerable keeper needs (a) the benchmark-frame question in §5
resolved, and (b) a re-solve at merged `main` — twelve legs, ~15 min each, about
one hour of wall clock across parallel shards.

**What you would be risking.** The 2023–2025 train tier reads CALIBRATED today.
The arm moves all three years. On the C1 evidence the coal classes mostly
improve there, but CC_REGULAR 2025 and CT_PEAKER 2023/2025 get worse, and
**no scored determination exists** to say whether the tier holds.

**The questions:**

1. **Arm the mechanism for MISO?** The case is rule 14 `[R-ACCURATE]`: the
   denominator is a year-independent constant standing in for a year-varying
   capacity, wrong by 0.414×–0.814× at exactly the contradicted plants. That case
   does not depend on §3 and is not retracted by the 2022 regression.
2. **If yes, re-solve at merged `main` to get a registerable keeper?** ~1 hour.
3. **Who owns the §5 benchmark-frame drift?** It is cross-ISO and it blocks any
   sharded registration, not just this one.

**I am not promoting anything, deleting anything, or re-basing the benchmark on
my own judgement.** The bundles are on ephemeral disk and will not survive this
container.

---

## 8. RESOLVED 2026-09-23 — REGISTERED AND SCORED, PROMOTED, THEN THE PROMOTION WITHDRAWN. §5 AND §7 ARE SUPERSEDED.

The owner ruled on the §7 question, verbatim: *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper."* That is rule 31 `[R-RETAIN]` trigger (i). The arm
was registered, scored and promoted — **and the promotion was then withdrawn**,
for a reason that had nothing to do with its merits. Both halves are recorded.

### 8.1 §5's BLOCKER WAS REAL, ITS MECHANISM WAS WRONG, AND THAT IS WHY IT WAS SEPARABLE

§5 said `--rebuild-benchmark` "would regenerate the committed
`bench/MISO/*.json.gz` parts". **It does not.** `rebuild_benchmark()` writes only
to the gitignored shared store `results/calibration/_shared/<ISO>/` and re-points
that one bundle's `meta.json`; its trailing `report_run()` is a printer. The
re-base happens one step later, in `dashboard_add_run.py` — *"newest run covering
a year supplies it"*.

That distinction is the whole difference between blocked and not blocked. Because
the two steps are separable, the bench move could be **measured first and then
refused**:

1. `--rebuild-benchmark` on `miso266_arm_span` — resolves the frames, touches no
   committed part.
2. `_miso257_bench_gate.py` **dry run** — `classFull` moves −0.24 to +2.65 TWh per
   class-year, and `classFull.oil` regenerates **NEGATIVE** in 2022 (−0.0731) and
   2025 (−0.0124). A measured actual cannot be negative.
3. `dashboard_add_run.py` → `RUN_ID=2026-09-22-miso-266-dispatched-bin`.
4. All six bench parts **restored byte-for-byte**, verified by `sha256sum -c`.

`hydro-5` independently reached the same conclusion the same day: *"MISO's
regenerated parts moved content (miso266 builder drift) and were NOT committed."*
Record and routing: `docs/FINDING-miso266-bench-regeneration-hazard-2026-09-23.md`
— now **`miso-267` STEP 1**.

**§5's second defect, for the record.** It also named `campd` as the blocker; that
was §5.1's Defect A (the composer copying leg 2020's per-year ref onto a six-year
composite), which `--rebuild-benchmark` cures outright. The frame that actually
refused on the single-year test was `eia923`.

### 8.2 §6's "NO GATE TABLE" IS NOW A GATE TABLE — AND IT IS AN EXACT WASH

Scored through `calibration_verdict.py` against the same committed bench as
`2026-09-20-miso-264-anchor-vintage`, the base both this arm and hydro-5's were
built on:

| criterion | miso-264 (base) | **miso-266 (arm)** |
|---|---|---|
| C1 fuel-mix | FAIL | **FAIL** |
| C2 system volume | PASS | **PASS** |
| C3a mean LMP | FAIL | **FAIL** |
| C3b price shape | FAIL | **FAIL** |
| C3c price tail | CAVEAT (ledgered) | **CAVEAT (ledgered)** |
| C4 dispatch corr | PASS | **PASS** |
| C6 governance | PASS | **PASS** |
| C8 forced share | PASS | **PASS** |
| **full span** | NOT-YET | **NOT-YET** |
| **train tier 2023–2025** | CALIBRATED, zero fails | **CALIBRATED, zero fails** |
| D-10 free-class C1 | 38/40 all · 28/30 free | **38/40 all · 28/30 free** |

**Which cells fail did move**, reported in both directions:

| | miso-264 | miso-266 |
|---|---|---|
| C1 2020 COAL_BIT | −10.92 **FAIL** | −6.93 (out of the set) |
| C1 2021 COAL_BIT | −6.54 | −3.30 |
| C1 2022 COAL_PRB | +8.13 **FAIL** | **+10.52 FAIL** (pre-registered) |
| C1 2022 CC_REGULAR | (passing) | **−8.74 FAIL** (new) |
| C3a 2020 | +14.6 % **FAIL** | +12.7 % **FAIL** |
| C3a 2022 | (passing) | **−10.5 % FAIL** (new) |
| C3b 2021 | NRMSE 0.304 **FAIL** | NRMSE 0.304 **FAIL** |

An exact wash on the gates. The mechanism's case therefore rests entirely on
rule 1 `[R-STRUCT]` — *"a run is a keeper because it is the most structurally
faithful, not because it has the lowest MAE"* — and rule 14 `[R-ACCURATE]`.

### 8.3 THE PROMOTION WAS WITHDRAWN, AND WHY

While this was being written up, **a sibling arm on the same `miso-264` base
landed on `main` first**: `hydro-5`'s `2026-09-22-hydro-5-miso-ror`
(`hydro_ror_split`), promoted on the same owner instruction. The two arms are
**siblings, not a chain** — each is `miso-264` plus one different flag — so
promoting this one would have silently **reverted** `hydro_ror_split`.

The promotion was withdrawn rather than overwrite another lane's work. MISO's
keeper is `2026-09-22-hydro-5-miso-ror`. The registry sidecar, run payload and
keeper-shard edits for `2026-09-22-miso-266-dispatched-bin` were dropped; the
mechanism-matrix cell stays **`O`** (built, solved, scored, **not armed**), with
the gate table above as its evidence.

### 8.4 §7's COST ESTIMATE WAS WRONG THEN AND IS RIGHT AGAIN NOW

§7 costed a registerable keeper at "twelve legs … about one hour". At the time
that was wrong — **zero LP** was needed; the `927f68af` bundles registered and
scored as they stood, and §7's premise was §5's wrong mechanism.

**It is true again, for a different reason.** The arm bundle does not carry
`hydro_ror_split`, so it is stale against the current keeper: arming this flag now
needs a **re-solve on the hydro-5 base** — six shards, ~15 min each. The
`miso266_arm_span` and `miso266_ctl_span` bundles were on ephemeral session disk
and did not survive. Rule 33 `[R-SHARD-ARCHIVE]` (f): the shard branches are
transport and are cut when this lane's PR merges; **cost any recovery as a
re-solve.**

### 8.5 WHAT IS STILL OPEN

* **The successor object has MOVED**, from 2020 coal to a **2022 gas/coal
  substitution**: the arm hands PRB capability back into a year where PRB was
  already long and CC already short, so 2022 demands the opposite move from 2020.
* **CT_PEAKER worsens in four of six years**, unpredicted. Reported, not absorbed.
* **84.5 % of the ceiling contradiction survives**, unchanged from §6.
* **MISO's bench parts are stamp-stale and the HEAD builder is defective** — two
  lanes refused to adopt it on the same day. 44 parts across all nine ISOs are in
  the same state. `miso-267` STEP 1.
* **One composer defect, unrepaired on `main`.** `_miso266_compose_span.py` writes
  leg 1's whole `shared_inputs` block and its `calibration_flags.years` onto the
  composite; `eia930`/`eia923`/`campd` are **per-year** (6 distinct hashes) while
  the six `unit_outages*` frames are shared (1). Symptoms: `--restore-shared-inputs`
  refuses, and `audit_keepers` E3 warns on the years mismatch — which
  `miso264_anchor_span` and `hydro5_miso_ror_span` both carry.
