# RESULT — miso-253: the arm is built and half-gated; the screen OOM'd, and the OOM is the finding

```
SESSION : miso-253
ISO     : MISO
KEEPER  : 2026-09-09-miso-250-ep-gas — UNCHANGED. Nothing promoted, nothing registered.
MECHANISM: ScenarioConfig.mustrun_chp_btm_holdout — NEW, default off, byte-identical off
LP SPENT: The parent ran no solve (rule 32(a)). BOTH screen shards DID run and BOTH were
          OOM-KILLED inside HiGHS run() on the P0 pass. No bundle exists.
```

> **CORRECTED 2026-09-11.** §3 of this document originally said both shards "sat at
> `SESSION_STATUS_PENDING` ... never provisioning a container" and that the session "did not
> even measure a cgroup ceiling". **Both statements were wrong.** They were written while the
> shards still read PENDING; both subsequently ran, reported, and merged
> (`docs/SHARD-miso253-screen2023.md`, `docs/SHARD-miso253-screen2023b.md`). The corrected
> account is §3 below, and it carries a finding that is more useful than the arm: **the
> parent's own HARD STOP 0 probe was wrong, and the shards caught it.**

Read with `docs/PRECOMMIT-miso253-mustrun-chp-btm-2026-09-10.md`, which carries the
mechanism, the screen year, the G-DRIFT audit, the pre-registered gates and three addenda —
**all pushed before any solve was attempted**, and none edited since.

---

## 1. What was delivered

**A new mechanism, complete and gate-clean.** `mustrun_chp_btm_holdout` partitions
host-steam / behind-the-meter cogeneration out of the two INJECTED must-run residual
classes (`biomass`, `OTHER`) on the published EIA-923 CHP flag — the partition every
*fossil* cogen class has had for years and these two never received. Rule 14
`[R-ACCURATE]`, **zero free parameters**, rule 13 forward test met, applied at the single
`_eia923_frame` seam that both the injection and the benchmark read.

- 13/13 new tests pass; 844 `tests/unit/config` pass; the adjacent biomass-injection and
  EIA-923-backfill suites pass unchanged (16/16).
- `check_mechanism_matrix.py --base origin/main` **exits 0** — base row plus a cell in all
  seven ISO shards (rule 28 duty (c)).
- Zero new anchor churn (257 pre-existing at HEAD, 257 with the change).
- Default cache key unmoved; armed key distinct.

## 2. What was MEASURED, at zero LP

### G-1 footprint confinement — **PASS**, on real MISO data

`_benchmark_eia923_frame`, MISO 2023, armed vs off. **Exactly two classes move, by exactly
the predicted amounts.** Every other class is `+0.0000`:

| class | bench OFF | bench ARM | Δ |
|---|---:|---:|---:|
| `biomass` | 8.1281 | **2.3233** | **−5.8048** |
| `OTHER` | 10.3253 | **3.6165** | **−6.7088** |
| CC_CHP, CC_REGULAR, COAL_BIT, COAL_LIGNITE, COAL_PRB, CT_CHP, CT_PEAKER, ST_CHP, ST_GAS, hydro, nuclear, oil, solar, wind | — | — | **+0.0000 each** |
| **total** | | | **−12.5136** |

Predicted in the PRECOMMIT before the fact: biomass 2.3233, OTHER 3.6165, total 12.5136,
170 of 2,994 rows. **Reproduced exactly.**

### G-6 bench-total consequence — reported, not a kill

Bench `classFull` total 616.259 → **603.746 TWh**, i.e. −0.04 % → **−2.07 %** against
MISO's EIA-930 reported net generation. Recorded in ADDENDUM A before any result, together
with the finding that the −0.04 % match is the residue of **68.1 TWh of offsetting
per-family error** (gas −33.526, other +23.111, coal +10.827) and is therefore not a
property worth protecting. Armed, the "other" family error falls **+23.111 → +10.598**.

### G-3 lockstep identity — proven structurally, not yet on a solve

Bench and injection read the same seam, so they cannot diverge; asserted mechanically in
`test_injection_equals_reconciled_class_both_ways` and
`test_benchmark_frame_carries_the_same_partition`. **Not yet confirmed on a solved bundle.**

## 3. What the shards found — including that MY OWN STOP CHECK WAS WRONG

Both shards ran on the pinned SHA `6b82b833`, in two different environments, and **both were
OOM-killed inside HiGHS `run()` on the P0 base-cost pass**, ~46 s in. No bundle was written by
either, and neither pushed a partial one (rule 27 `[R-PUSH]` honoured).

### 3.1 The HARD STOP 0 defect — the durable finding of this session

**The ceiling probe I wrote into both shard prompts reads the WRONG cgroup.** It probes
`/sys/fs/cgroup/memory.max` (v2, absent) and `/sys/fs/cgroup/memory/memory.limit_in_bytes` —
the **root** v1 cgroup, which is unlimited — and then falls back to `MemTotal`. But the solve
does not run in the root cgroup:

```
/proc/self/cgroup -> 4:memory:/process_api/<id>/claude-code-bash
```

| quantity | value |
|---|---:|
| `MemTotal` (what my probe reported) | 15.70 GiB |
| root `memory.limit_in_bytes` (what my probe read) | *unlimited* |
| **nested `claude-code-bash` limit — the one that binds** | **13.344–13.345 GiB** |
| nested `memory.max_usage_in_bytes` after the kill | 13.344–13.345 GiB (**hit the wall exactly**) |

**My stated hypothesis was false.** The PRECOMMIT §7 claimed "~16.46 GB MemTotal = 15.70 GiB,
no cgroup limit, giving ~2.4 GiB headroom over the 13.29 GiB peak". The real headroom is
**≈0.055 GiB**. Read correctly, HARD STOP 0's own 14 GiB rule would have fired and **neither
shard should have attempted its solve** — both said so independently.

**The correct probe, for every future MISO/PJM shard:**

```sh
P=$(grep -E '^[0-9]+:memory:' /proc/self/cgroup | cut -d: -f3)
cat /sys/fs/cgroup/memory$P/memory.limit_in_bytes    # v1, nested
cat /sys/fs/cgroup$P/memory.max                      # v2, nested
```

**This also supersedes `FINDING-miso252` §1b's diagnosis.** That section concluded "the
container misreports its own size". It does not: `free` and `MemTotal` are telling the truth
about the *machine*, and the limit is on a **nested cgroup** the probe never looked at. That is
why miso-252 lost three containers to the same wall, and why its "Full access OOM at 15 GB"
reading was never reconcilable with its "Default 13.344 GiB" reading — both were 13.3 GiB all
along.

### 3.2 The peak, located exactly

LP size **1,026,876 rows × 29,643,840 cols, 86,198,400 nnz**. Build-phase `VmHWM` tops out at
**6.98 GiB** after `addRows`; the kill comes later, inside `h.run()`. Kernel record: terminal
anon-RSS **13.30 GiB**, `oom_memcg=/process_api/<id>/claude-code-bash`, total-vm 30.30 GiB.

That reproduces miso-252's 13.29 GiB peak to within 0.01 GiB. **The build is not the problem
and never was**, and the arm's one boolean does not change the memory profile — same LP shape,
same wall, same line.

### 3.3 G-1 confirmed a second time, on the solve path

Shard A reached the injection before dying, and the log line matched the pre-registered
prediction **to the digit**:

```
must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y host-steam
generation from the injected residual classes (170 of 2994 rows)
```

| | expected | observed |
|---|---:|---:|
| dropped energy | 12.514 TWh | **12.514 TWh** |
| rows touched | 170 of 2,994 | **170 of 2,994** |

Only the armed path emits that line, so the arming is evidenced even though `run_config.json`
was never written.

### 3.4 Still unmeasured — the half that decides the arm

**G-2 (dispatch response), G-4 (off-path criterion flips) and G-5 (recording) require a
completed solve, and neither shard produced one.** Also unmeasured: the second limb of G-1
(injected class totals from a bundle), G-3 on a solved bundle, the 2023 criteria verdicts, and
prices.

**Therefore the arm remains UNADJUDICATED** — not a keeper, not a rejection, no cell verdict
minted. MISO's matrix cell stays **`O`**; the other six stay **`U`**.

## 4. The larger finding, which is not about biomass

MISO's benchmark reconciles to the grid in aggregate and is **wrong in every family**:

| family | bench | EIA-930 | bench − 930 |
|---|---:|---:|---:|
| gas | 207.651 | 241.177 | **−33.526** |
| other | 27.602 | 4.491 | **+23.111** |
| coal | 185.787 | 174.961 | **+10.827** |
| nuclear / wind / solar / hydro | | | −0.664 / −0.006 / +0.000 / −0.001 |
| **TOTAL** | 616.259 | 616.519 | **−0.259** |

**68.1 TWh of absolute per-family error cancelling to −0.259.** MISO's EIA-930 fuel split
is exhaustive (it reconciles to the BA's own reported net generation to 0.0002 %), so this
is not an artifact of a residual bucket. C1 passes because it is scored against this
benchmark — the model matches the bench, and the bench does not match the grid.

**That is a bigger object than the arm that found it, and it is nobody's lever yet.**

## 5. The competing hypothesis, still open

ADDENDUM A.3: MISO's telemetry may label blast-furnace / coke-oven **steam** cogen as `NG`
rather than `OTH`, in which case `OTH` is not a pure comparator, the cogen **is** on the
grid, and the repair belongs on the gas side — i.e. **the arm's premise would be wrong**.

ADDENDUM B tested it with CAMPD, whose applicability keys on *selling* electricity:
**76.9 % (9.614 TWh) of the 12.514 TWh chp=Y block is at sites with no metered CEMS
generation at all** (65.2 % absent entirely, 11.7 % present at zero load). Only 23.2 %
(2.900 TWh) is at a CEMS-reporting facility, and at six of those seven plants the CEMS load
is plainly other units at the same site — so **2.900 TWh is an upper bound on wrongful
removal, not an estimate.**

This moves the balance toward the arm's premise **without settling it**: CAMPD absence is
strong but circumstantial and says nothing about how the telemetry *labels* the units that
are grid-connected, which was the hypothesis's actual mechanism. Discriminating it needs a
per-generator EIA-930 fuel attribution or MISO's registered-resource roster — **neither is
on disk, and both are intake work, not a solve.**

## 6. Recorded before the result, because it may go against the arm

ADDENDUM C: keeper `CC_REGULAR` is 138.151 TWh against a bench 141.817 (−3.666), and at a
$34.467/MWh load-weighted mean it is marginal in most hours. If it absorbs most of the
withdrawn 12.5136 TWh it lands ~148–150 — **about +7 TWh OVER bench, flipping the sign of
its C1 error rather than closing it.** That changes no gate (C1 `CC_REGULAR` is the target
residual; gating on it either way is the fitted-mechanism selection rule 1 `[R-STRUCT]`
forbids), and if it happens the honest reading is not that the partition is too large — it
has no parameter to tune — but that the −33.5 TWh gas-family error of §4 and this defect
interact.

The keeper also shows **slack 0.0 MWh and dump 0.0 MWh** in 2023, so the withdrawal should
be absorbed by the merit order rather than priced as scarcity.

## 7. Rule compliance

- **Rule 29 `[R-SCREEN]`**: screen year 2023 named in the PRECOMMIT *before* the screen, on
  measured footprint (largest chp=Y block AND the only complete vintage of the three).
  Gates STOP-only and explicitly not keyed to the target residual.
- **Rule 29(b)**: G-DRIFT run against base `25675896`; all 23 changed solve-path files
  classified INERT for MISO 2023–2025, including a measured zero-overlap check of the 11
  new PJM `ST_GAS` plant codes against MISO's 381-plant bin sheet. **Form 4 valid; no
  control solve spent.**
- **Rule 32 `[R-SHARD]`**: the parent ran no LP. Shards pinned to a full 40-char SHA.
- **Rule 31 `[R-RETAIN]`**: nothing deleted. No bundle exists to retain — both shards were
  OOM-killed before writing one, and neither pushed a partial bundle.
- **Rule 15 `[R-DASHBOARD]`**: nothing to register. No run completed.
- **Rule 27 `[R-PUSH]`**: both ≥300-line files blob-verified after push (line count + hash
  identical to local).

## 8. Open for the owner

1. **A container whose NESTED cgroup ceiling clears ~14.5 GiB.** This is now a hard,
   precisely-quantified resource fact rather than a vague one: a MISO plant-level single-year
   LP needs **13.30 GiB** at the solve, and every container class reachable from here caps its
   Bash-tool cgroup at **13.344 GiB** — 0.055 GiB of headroom. miso-252 lost six shards to this
   wall and miso-253 lost two more. **The arm is one 2023 shard from an answer, and no amount of
   retrying in this container class will produce it.** The alternative is a solve-phase memory
   reduction not already spent (the build is only 6.98 GiB; the peak is inside HiGHS `run()`).
2. **The §4 benchmark family error (68.1 TWh, offsetting).** Bigger than this arm and
   currently owned by nobody. Naming it as a lane is an owner call.
3. **The §5 discriminator.** A per-generator EIA-930 fuel attribution, or MISO's
   registered-resource roster — an intake, not a solve. It would settle whether this arm's
   premise is right.
4. Carried forward from miso-252, unchanged: `MISO_PRICING_API_KEY` (unblocks C3a/C3b/C3c
   on 2020/2021 with no re-solve), and the `min_gen` sparse-override cleanup (worth doing
   on its own merits; buys 18 MiB, not a solve).

## 9. Honest summary

The mechanism is real, cheap, structurally motivated and **half-verified**: its footprint gate
reproduces the pre-registered prediction exactly — twice, once on real data in the parent and
once on the solve path in a shard. Whether it *helps* is unknown and this session cannot say:
the dispatch half was OOM-killed. Anyone quoting this work should quote it as **an arm that is
built and specified, not an arm that was tested.**

**It is NOT a keeper candidate, and it cannot be promoted.** A keeper is a registered run with
scored years; this arm has no bundle, no criteria and no determination. The "structural
integrity improves but gates regress may still be a keeper" test does not rescue it — that test
compares gate results, and there are none.

**The session's most useful output is the correction in §3.1**, not the arm: the nested-cgroup
ceiling is now measured, the correct probe is written down, and `FINDING-miso252` §1b's
"the container misreports its own size" diagnosis is superseded. That unblocks whoever gets a
bigger container, and it stops the next lane losing shards to the same wall.
