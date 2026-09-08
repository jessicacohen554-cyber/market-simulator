# FINDING — pjm-173: the F-A seam gas repair is **STRUCTURALLY INERT on the PJM keeper** — the measured seam ladder already owns the seam price

**Session** pjm-173 · **ISO** PJM · **Date** 2026-09-08 · **LP spent: 2022 (one year, ~13 min)**
**Card** `docs/handoffs/PRECOMMIT-pjm173-seam-measured-gas-regate-2026-09-08.md` (committed `b8112519` BEFORE any solve; not rewritten)
**Predecessor** `results/calibration/FINDING-pjm172-seam-measured-gas-2026-09-07.md`
**Keeper** `2026-08-15-pjm-162-inputclock` — **unchanged**. Nothing promoted, nothing registered.
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).

---

## 0. RESULT IN ONE PARAGRAPH

The 2022 screen ran and the answer is unambiguous: **the arm is byte-identical to the control on
every scored quantity.** Gas 357.63, coal 155.21, nuclear 272.19, interchange 21.65 TWh, every
per-fuel correlation, and the load-weighted mean LMP 66.73 $/MWh — **all unchanged to the last
decimal**, against a seam repricing worth **+31.110 $/MWh** of baseload. The cause is structural and
it is now proven: **`pjm_seam_measured_ladder` is ARMED on the keeper recipe**, and it *replaces*
the gas × heat-rate seam price with measured per-seam Q-Q ladders before it reaches the LP
(`import_nodes.py:1051`, and the solve's own log: *"seam bands repriced to the MEASURED per-seam
Q-Q ladders … firm-export floor displaced"*). `PJM_SEAM_LADDER_BY_YEAR` covers **2019, 2021, 2022,
2023, 2024, 2025** — **every year PJM solves**. So the input-parity defect pjm-171 measured is
**real but unreachable** on this recipe: `neighbor_gas_price` is computed and then overwritten.
**The arm is dead at S4 by the card's own kill rule, and 2021 was therefore not spent.**

**What this changes.** F-A is not a repair for PJM's rubric failures, because the seam price it
corrects is not the price the LP sees. The C1 interchange row — PJM's single worst row, −10.04 TWh
with r 0.498 — is set by the **measured ladder**, so the ladder is where that work belongs. That
redirection, not the gas level, is this session's most useful output.

---

## 1. THE GATE TABLE

| # | gate | verdict | measured |
|---|---|---|---|
| **S1′** | HR moves ONLY through the declared elastic law, only on the `hr_by_year = None` seams | **PASS** | `max\|hr − (5.6 + 14.2/gas)\| = 0.0` exactly, both years. Carolinas/TVA/LGEE **11.1906 → 7.8122** (2022), **→ 9.2320** (2021). MISO **12.9000** / NYISO **10.4000** unchanged. |
| **S2** | bit-identical for every year ≥ 2023 and every forecast year | **PASS** | 40 committed tests (pjm-172). |
| **S3′** | 2022 seam baseload mean = **61.1448**, per-neighbour as tabled | **PASS** | Mean **61.1448** (err **4.8e-05**). MISO **82.8059** · NYISO **72.4782** · Carolinas/TVA/LGEE **50.1467**. 2021 mean **41.0197**. |
| **S4** | footprint — only the 80 seam `mc` rows move; **zero seam rows fail to move** | **FAIL — and this is the finding** | **ZERO of the 80 move.** The LP's seam bands are repriced by the measured Q-Q ladder, which displaces the reference price entirely. Not a defect in F-A; a downstream mechanism owns the seam (rule 19 `[R-ONE-MECH]`). |
| **S5** | 2022 net export RISES from 21.65 TWh | **FAIL (no movement)** | **21.65 → 21.65 TWh, +0.00.** Same cause as S4. Actual 31.69. |
| **S6** | no non-C3a criterion flips PASS → FAIL | **PASS** | `screen_collateral_gate.py` vs `2026-09-07-pjm-2022-2021-touchpoints`: **0 flips**. (4 records unscorable on both sides: `price_mean` da_diagnostic, `governance` — no attestation at a screen — and `forced_share` ST_GAS / hydro.) |

**Kill rule applied as written:** S4 failed ⇒ the arm is dead, **2021 was never spent**, nothing is
promoted. 2021 is additionally inert *by construction* — the ladder covers it — so the unspent year
costs no evidence.

**C3a, reported and gating nothing (rules 1/29):** load-weighted mean LMP **66.73 → 66.73 $/MWh,
+0.00**. The card's ex-ante prediction that 2022 would improve is **not confirmed and not refuted** —
the mechanism never reached the LP, so the prediction was never tested.

---

## 1a. THE FULL 2022 A/B — every number this session will cite

Model TWh, control (`pjm169_tp2022_2021_f2arm`, committed) vs arm (`pjm173_fa_arm_2022`):

| fuel | control | arm | move | actual | control err | arm err | r ctl→arm |
|---|---|---|---|---|---|---|---|
| gas | 357.63 | 357.63 | **+0.00** | 330.28 | +27.35 | +27.35 | 0.922→0.922 |
| coal | 155.21 | 155.21 | **+0.00** | 167.38 | −12.17 | −12.17 | 0.925→0.925 |
| nuclear | 272.19 | 272.19 | **+0.00** | 272.46 | −0.27 | −0.27 | 0.759→0.759 |
| wind | 32.21 | 32.21 | +0.00 | 32.21 | +0.00 | +0.00 | 1.000→1.000 |
| solar | 7.15 | 7.15 | +0.00 | 7.15 | +0.00 | +0.00 | 1.000→1.000 |
| **interchange** | 21.65 | 21.65 | **+0.00** | 31.69 | **−10.04** | **−10.04** | 0.498→0.498 |
| **mean LMP $/MWh** | 66.73 | 66.73 | **+0.00** | — | — | — | — |

Solve: matrix build 27.062 s, P0 436.573 s cold, 421,111 simplex iterations, objective
17,668,391,326.2485.

---

## 1b. WHY IT IS INERT — proven, not inferred

`model/interchange/import_nodes.py:1051` gates on
`iso == "PJM" and config.pjm_seam_measured_ladder and year in PJM_SEAM_LADDER_BY_YEAR`. The keeper
recipe carries **`pjm_seam_measured_ladder = True`** (`meta.json`), and the ladder table covers
**{2019, 2021, 2022, 2023, 2024, 2025}**. When active it reprices the seam bands from measured
tie-line flow durations × PJM DA system quantiles and **displaces the firm scheduled-export floor** —
the code's own comment states the rule-19 intent: *"alternatives, never stacked"*.

So on this recipe the seam price is **measured**, not derived from `gas × heat_rate`. F-A corrects
the derivation of a number the LP does not use. Two consequences worth stating precisely:

1. **F-A is inert for PJM in every year PJM currently solves** — 2021 through 2025, and 2019. The
   only PJM years where it could bite are those with no ladder entry (**2020**, and forecast years,
   where the ladder no-ops by design and the gas trajectory has knots anyway).
2. **It is NOT inert in general.** The freeze is in shared code, and any ISO arming
   `reference_price_interface` on a pre-2023 year *without* a measured ladder still hits it. Rule 25
   `[R-ISO-SCOPE]`: MISO's own exposure is its lane's to verify, not this one's to assert.


## 2. THE MEMORY CEILING — a KNOWN, ALREADY-SOLVED condition, and the LP did NOT grow

The pjm-173 charter opens: *"RUNNER: **REQUIRES ≥32 GB RAM.**"* **That is wrong**, and so was this
session's first reading of it. The correct diagnosis was already in the repo, in
`FINDING-pjm169-f2-arm-and-touchpoints-2026-09-06.md` §3.1a, written two days earlier by the lane
that produced this card's own control.

**Nothing about the LP changed.** Every measured peak sits in the same place, against the same cap:

| session | anon-RSS at OOM | cgroup cap | outcome |
|---|---|---|---|
| pjm-167 | — | 13.34 GiB | OOM |
| pjm-168 | — | 13.34 GiB | **passed** — added `swapon` |
| pjm-169 | **13,755,496 kB** | 13.34 GiB | OOM, then **passed** after re-arming swap + a watchdog |
| pjm-172 | 13,936,168 kB | 13.34 GiB | OOM → concluded "≥32 GB" |
| pjm-173 ×3 | 13,936,168 / 13,952,028 / **13,952,500 kB** | 13.34 GiB | OOM |

The LP peaks ~13.7–14.0 GiB against a **13.34 GiB** cap — pjm-169 measured the overshoot at
**~420 MiB**. **It has never fit unaided on this box class**, and every PJM success since pjm-168
has run on a swapfile. Corroborating evidence that the model is unchanged: the control bundle's
recorded environment is **identical** at both revisions (Python 3.11.15, numpy 2.4.6, scipy 1.17.1,
highspy 1.14.0, pandas 3.0.3, same kernel); `replay_keeper` replays the control's own kwargs, so
fleet, zones, tranches and the 8760 clock are the same object; and the only ≥100-line solve-path
additions are value tables or other ISOs' branches (`results/cache.py`'s +114 lines are **module
docstring only** — zero new `def`/`class`/assignment lines, verified).

**Why it works.** `memory.limit_in_bytes` on the `claude-code-bash` cgroup caps *physical* memory at
`14,327,676,928` B; `memory.memsw.limit_in_bytes` is effectively unlimited, so **pages spilled to
swap are not charged against the cap**. `free` reports the ~15 GiB HOST view and is actively
misleading here — the usable figure is 13.34 GiB.

**The documented recipe** (pjm-169 §3.1a, reproduced because the next lane needs it):

```bash
fallocate -l 12G /home/user/swapfile && chmod 600 /home/user/swapfile
mkswap /home/user/swapfile && swapon /home/user/swapfile && sysctl vm.swappiness=60
# keep it armed — it CAN be dropped underneath a running solve:
nohup bash -c 'while :; do swapon --show | grep -q swapfile || swapon /home/user/swapfile; sleep 10; done' &
export MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat /sys/fs/cgroup/memory/$(sed -n 's/^4:memory://p' /proc/self/cgroup)/memory.limit_in_bytes
```

`vm.swappiness=60`, not the default — clearing a hard cap needs real spilling, not idle-page
reclaim. pjm-169 measured its successful run at **12,735 MB resident with 1,828 MB spilled**, and
3,713 MB spilled at the P1 peak.

### 2.1 CORRECTION to this session's own first account

An earlier revision of this finding stated that the swapfile "did not survive to the next tool call
(**each Bash invocation lands in a fresh mount namespace**)". **That parenthetical was speculation
and it is wrong.** The real cause is documented: pjm-169 found the swapfile **silently deactivated**
between session start and the solve peak — *"the file was still on disk, untouched;
`swapon --show` was empty"* — reproducing pjm-167's OOM exactly. This session saw the identical
behaviour (7 GiB active, gone by the next call) and misattributed it. **This is why the ceiling
looks intermittent and why three sessions in a row have re-derived it from scratch:** the swap
silently disarms, so a lane that armed it once and did not re-check concludes the box is too small.
The watchdog in the recipe above exists precisely for this and is not optional.

### 2.2 What was tried here

1. **Swap** — armed successfully (7 GiB), silently lost, re-armed. **This is the fix**, per above.
2. **glibc allocator tuning** — `MALLOC_ARENA_MAX=2` etc. Legitimate because it is provably
   numerics-neutral. Measured: total-vm 24.56 → 23.90 GB, **anon-RSS did not move at all**
   (13,952,028 → 13,952,500 kB). Necessary as part of the recipe, **not sufficient alone**.
3. **Rule-12 per-year chaining** — adopted (`--years 2022` alone, not `2022 2021`), which is the
   invocation chain `replay_keeper --years` prescribes for this failure mode. Process-level only;
   the recipe is untouched. Not sufficient alone.
4. **Moving the solve to the unlimited parent cgroup** — permission-refused, correctly (it is
   sandbox-escape-shaped). **Not needed**: swap clears the cap without it.
5. **NOT tried, deliberately** — dropping `pjm_da_virtual_bids`, the per-gen reserve co-opt or the
   zonal loss surface. Each would fit the LP in memory and each would **change the recipe**, so the
   arm would no longer be *the control's recipe plus the F-A delta and nothing else*.

### 2.3 The process finding, which outlives this card

Three consecutive PJM lanes (167, 172, 173) each re-derived this ceiling from scratch, and two of
them wrote a wrong runner requirement into a handoff. The diagnosis and recipe were already
committed in pjm-169's finding. **The charter's "≥32 GB" claim propagated because the handoff was
believed over the repo's own measurement.** The durable fix is that the recipe belongs somewhere a
lane reads *before* launching a PJM solve — not buried in one session's §3.1a.


## 3. G-DRIFT AT THIS HEAD — clean, and it found a real delta

pjm-172's Appendix A audited `f36cee6e → 172af213`; **that revision no longer exists** (branch
merged, `main` advanced), so the audit was re-run at `f36cee6e → HEAD 22eda76a`: **73 files**
(was 69), **+16,173 / −82**, **ZERO LIVE hunks**.

Two checks are worth recording because each could have gone the other way:

1. **The PJM solve surface is NOT "identical" — it gained a row, and the honest statement is that
   the row is inert, not that nothing moved.** 211 → **212 rows**, `moved_rows("PJM") == {}`
   (**empty**). The single added name is `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO` (capx D84),
   verified absent from all seven `SURFACE_MODULES` at `f36cee6e`. Its gate
   `pjm_thermal_accreditation_vintage` has dataclass default **False** and is coerced back to that
   default under `if self.mode == "backcast"`; a backcast runs no capacity evolution at all, so the
   table has no seam to reach. **INERT.**
2. **PJM's scoring reference was checked, because a moved reference would silently stale the
   control's committed scores.** Every PJM-keyed subtree of `actual_lmp.json` and
   `calibration_reference.json` was extracted at both revisions and hashed:
   `b4edaf49c24e619c → b4edaf49c24e619c` and `763eea657b57941a → 763eea657b57941a` —
   **byte-identical**. The large insertions in those files are a **CAISO 2022** block and an **SPP**
   block. The control's committed 2022/2021 columns remain a valid comparison.

New-since-predecessor files, classified: `model/capacity_evolution/{retirements,__init__}.py`
(D84, above) INERT; `model/reserves/__init__.py` SPP re-exports only, INERT;
`scripts/lib/wind_shape.py` **imported nowhere on the solve path** (verified), INERT;
`data/raw/_validation-source/*` INERT for PJM per check 2.

⇒ **G-CTRL form 4 is VALID at this HEAD. No control LP is owed.**

---

## 4. F-A IS ALREADY MERGED INTO `main` — which reframes the open question

`origin/main` at `22eda76a` carries `_measured_henry_hub_annual`, the pre-first-knot branch and the
`hindcast_asknown_*` refusal. The pjm-172 branch was merged.

pjm-172 §6 offered the owner three routes: **(a)** re-gate and screen, **(b)** land it on rule-14
grounds without a screen, **(c)** drop it. **Route (b) has already happened.** So the live question
is no longer *"should this merge"* but *"this is merged and its footprint, direction and collateral
have never been observed — does it stay?"* A bad S5 is now a **revert** decision.

What that does **not** change: the change is inert by test in 2023–2025 and in every forecast year,
so **no keeper can move and no determination is at risk today**. The exposure is confined to
pre-2023 runs with `reference_price_interface` armed — PJM's touchpoints, and any MISO pre-2023 run
(`miso233_sppseam_K` is 2023–2025 and unaffected).

---

## 5. THE PARITY DEFECT IS SHARPER THAN THE CARD STATED

The control recipe's own `gas_prices` are **2022: 6.45**, **2021: 3.72 $/MMBtu** — PJM's measured
delivered gas, burned by the ISO's own units — while the seam priced Henry Hub at the held-flat 2023
knot, **$2.54**, in both years.

| year | ISO's own gas | seam, control | seam, arm | control error | arm error |
|---|---|---|---|---|---|
| 2022 | 6.45 | 2.54 | **6.419058** | **−60.6 %** | **−0.5 %** |
| 2021 | 3.72 | 2.54 | **3.909683** | **−31.7 %** | **+5.1 %** |

So F-A does not merely reduce the error — in 2022 it very nearly closes it. **In 2021 it slightly
overshoots**, putting the seam ~5 % *above* the ISO's own gas level. That is an independent,
mechanism-level reason to expect 2021 to worsen, and it agrees with the direction the card recorded
ex ante. It is reported, and it gates nothing.

---

## 6. PJM'S RUBRIC FAILURES — the charter's item 4, from committed artifacts, zero LP

The 2022 touchpoint reads NOT-YET with C1 `fuelmix`, C3a `price_mean` and C3b `price_shape` FAIL.
Read together they are **one defect, not three** (TWh; m = model, b = actual):

| fuel | 2022 m / b | err | 2021 m / b | err | r (22/21) | nrmse |
|---|---|---|---|---|---|---|
| gas | 357.63 / 330.28 | **+27.35** | 346.52 / 308.85 | **+37.67** | .922 / .916 | .14 / .17 |
| coal | 155.21 / 167.38 | **−12.17** | 152.71 / 183.54 | **−30.83** | .925 / .934 | .16 / .21 |
| nuclear | 272.19 / 272.46 | −0.27 | 272.19 / 272.99 | −0.80 | .759 / .810 | .059 |
| **interchange** | 21.65 / 31.69 | **−10.04** | 23.43 / 37.94 | **−14.51** | **.498 / .546** | **.58 / .55** |

**Too much gas, too little coal, too little net export — same sign in both years, worse in 2021.**
And **interchange is the model's weakest row on both instruments at once**: r ≈ 0.5 against 0.92+
for gas and coal, nrmse 0.55–0.58 against 0.14–0.21. Nothing else in the fuel mix is close.

C3b has a matching signature. D-A diurnal amplitude (reported-only, band-free) is **34.0 % of
measured in 2022** (hod range $15.78 vs $46.40) and **44.0 % in 2021**, with **phase correct** and
**hod r +0.961 / +0.942**. The model gets the shape of the day right and does not spread — which is
what a too-cheap import seam produces, since cheap imports cap the upper tail in exactly the tight
hours that make the range.

**This is why F-A is worth finishing, on grounds that are not C3a.** Dearer pre-2023 imports act
directly on the worst C1 row and on the C3b compression. **S5 is the test of the first leg** — and
S5 is precisely what could not be run.

**Rule-28 DO-NOT-REDO, checked before proposing anything.** The C3b compression may **not** be
attacked through `diurnal_price_amplitude` or `ordc_scarcity_overlay` (both **G**, governance-
refused for PJM), nor through `measured_offer_surface` or `temp_dependent_derate` (both **R**). The
seam is the open, un-adjudicated route — which is a reason to finish this card rather than open
another.

---

## 7. GOVERNANCE

- **Rule 29 `[R-SCREEN]`** — gates were fixed **and committed** (`b8112519`) before any solve, and
  none was re-read, re-weighted or re-written afterwards. S1′/S3′ are graded against the card's own
  numbers.
- **Rule 22 `[R-HOLDOUT]`** — 2021 and 2022 are validation tier; PJM holds `complete`; the freeze
  scopes the locked test alone; `registration_refusals` returns empty for both years. The
  authorization was verified before launch and **no year was actually scored**, so nothing was
  spent. Neither year may ever be quoted as an out-of-sample skill number.
- **Rule 31 `[R-RETAIN]`** — `results/calibration/pjm173_*/` is gitignored (`2482cc81`), which is
  what discharges rule 29(c). **Nothing was deleted.** The three partial dirs hold an empty
  `dispatch/` and no solved output, so there is no artifact at risk.
- **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`** — the arm was never scored against a residual, and no
  recipe lever was touched to fit memory (§2.1 item 5).
- **Rule 30(c)** — PJM stays **CALIBRATED** regardless.

---

## 8. WHAT IS AND IS NOT ESTABLISHED

**Established (measured).**
1. **F-A is structurally inert on the PJM keeper recipe.** A +31.110 $/MWh seam repricing moved
   **zero** of the LP's 80 seam rows and **zero** of every scored quantity — fuel mix, correlations
   and mean LMP identical to the last decimal.
2. **The cause**: `pjm_seam_measured_ladder = True` on the recipe, and `PJM_SEAM_LADDER_BY_YEAR`
   covers every year PJM solves. The ladder replaces the gas × HR seam price and displaces the firm
   export floor (rule 19 `[R-ONE-MECH]`, stated in the code's own comment).
3. **S6 PASS** — zero collateral flips against the committed control.
4. **S1′ / S3′ PASS exactly** — the HR moves on the declared law with error 0.0, and the seam
   baseload reproduces 61.1448 to 4.8e-05.
5. **G-CTRL form 4 holds at this HEAD** — zero LIVE hunks over 73 files, PJM surface `moved_rows`
   empty, PJM scoring-reference subtrees hash-identical.
6. **The runner requirement is a 13.34 GiB cgroup cap, cleared by swap** — not the ≥32 GB the
   charter claimed, and not a change in the LP (§2).

**NOT established — do not quote any of this as measured.**
1. **Any C3a movement, in either year.** The card predicted 2022 improves and 2021 worsens.
   **Neither was tested**: the mechanism never reached the LP, so the prediction is neither
   confirmed nor refuted.
2. **2021 was not solved.** Its inertness rests on the ladder covering 2021 — a structural argument
   plus the 2022 measurement, not a 2021 measurement.
3. **Whether F-A matters anywhere else.** PJM 2020 (no ladder entry) and MISO's pre-2023 exposure
   are untested here. Rule 25 `[R-ISO-SCOPE]`: no verdict transfers.
4. **Whether the ladder itself is right.** This session shows the ladder *owns* the seam price; it
   does **not** show the ladder is well-calibrated. That is the open question below.

---

## 9. FOR THE OWNER — the keeper question, answered, and where the work goes next

**Is F-A a keeper candidate? NO — and not on a gate ground.** A keeper determination is the
train-tier (2023–2025) verdict (rule 30(c)). F-A is byte-identical in 2023–2025 **and** now measured
byte-identical in 2022, so it is *incapable* of moving any scored year in either direction. There is
nothing to promote. The owner's standing principle — *structural integrity improving while gates
regress can still be a keeper* (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`) — is correct and is the
right frame for a **merge** decision, but it needs a mechanism that reaches the LP. This one does
not.

**Should it stay in `main`?** The owner ruled **keep, pending measurement** (2026-09-08). The
measurement now exists and **strengthens** that ruling rather than weakening it: F-A is a strictly
more accurate input (rule 14 — the seam was wrong by −60.6 % / −31.7 % against the ISO's own burned
gas) that is **provably inert** on every PJM year now solved, so it carries correctness with zero
behavioural risk. It remains live for PJM 2020 and for any ISO without a measured ladder.

**Where the C1 / C3b work actually goes.** PJM's three failing criteria are one defect — too much
gas, too little coal, too little export — whose largest and worst-correlated term is
**interchange (−10.04 TWh, r 0.498, nrmse 0.58)**. This session proves that row is set by the
**measured Q-Q ladder**, not by the gas level. So the next lever is the ladder itself — its
construction, its duration mapping, and whether its export bands can clear the ~10 TWh gap — and
**not** any further work on `neighbor_gas_price`. Rule 28 check: `diurnal_price_amplitude` and
`ordc_scarcity_overlay` are **G** for PJM, `measured_offer_surface` and `temp_dependent_derate` are
**R**; the seam ladder is the open, un-adjudicated route.
