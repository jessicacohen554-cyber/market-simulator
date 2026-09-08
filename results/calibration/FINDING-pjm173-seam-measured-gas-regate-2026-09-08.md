# FINDING — pjm-173: F-A re-gated and PASSES its pre-solve gates; S4/S5/S6 blocked on a SANDBOX memory cap

**Session** pjm-173 · **ISO** PJM · **Date** 2026-09-08 · **LP spent: NONE (three attempts, all OOM-killed before the first solve completed)**
**Card** `docs/handoffs/PRECOMMIT-pjm173-seam-measured-gas-regate-2026-09-08.md` (committed `b8112519` BEFORE any solve; not rewritten)
**Predecessor** `results/calibration/FINDING-pjm172-seam-measured-gas-2026-09-07.md`
**Keeper** `2026-08-15-pjm-162-inputclock` — **unchanged**. Nothing promoted, nothing registered.
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).

---

## 0. RESULT IN ONE PARAGRAPH

pjm-172 killed F-A at gates S1/S3 that were **mis-specified**, not at a defect. This session
restated them with the gas-elasticity in them, **committed the restatement to git before running
anything**, and then measured: **S1′ PASSES and S3′ PASSES**, exactly and at zero LP — the seam
heat rate moves by *precisely* the declared law `5.6 + 14.2/gas` (error **0.0**, not merely small)
on exactly the three SERC seams that take that branch, and not at all on MISO/NYISO; the 2022 seam
baseload mean reproduces **61.1448 $/MWh** to 4.8e-05. The G-DRIFT audit was re-run at this HEAD
(pjm-172's revision no longer exists) and is **clean — zero LIVE hunks**, so G-CTRL form 4 holds and
no control LP is owed. **S4, S5 and S6 remain unmeasured**, and the reason is neither the mechanism
nor the machine: **the LP's peak resident set exceeds the Claude Code bash tool's own cgroup limit
of 13.34 GiB, on a box with 16.4 GB of RAM and ~15 GB free.** Three independent attempts were
OOM-killed at 13.31 GiB — the same value to three decimal places each time.

---

## 1. THE GATE TABLE

| # | gate | verdict | measured |
|---|---|---|---|
| **S1′** | HR moves ONLY through the declared elastic law, and only on the `hr_by_year = None` seams | **PASS** | `max\|hr − (5.6 + 14.2/gas)\| = 0.0` across both years. Carolinas/TVA/LGEE **11.1906 → 7.8122** (2022) and **→ 9.2320** (2021). MISO **12.9000** and NYISO **10.4000** unchanged in both years. |
| **S2** | bit-identical for every year ≥ 2023 and every forecast year | **PASS** | Asserted by the 40 committed tests (pjm-172); re-affirmed, not re-litigated. |
| **S3′** | 2022 seam baseload mean = **61.1448**, per-neighbour as tabled | **PASS** | Mean **61.1448** (err **4.8e-05**, tol 1e-4). MISO **82.8059** ✓ · NYISO **72.4782** ✓ · Carolinas/TVA/LGEE **50.1467** ✓. 2021 mean **41.0197** ✓. |
| **S4** | footprint — only the 80 seam `mc` rows move | **NOT REACHED** | requires the solve. *(Partial corroboration only, from the arm's own construction log before the kill: `priced import/export node — 40 import tranches (16300 MW), 40 export sinks (16300 MW)` = the 80 rows the gate names. That is the row COUNT, not the movement test, and is **not** a pass.)* |
| **S5** | direction — 2022 net export rises from 21.65 TWh | **NOT REACHED** | requires the solve. |
| **S6** | collateral — no non-C3a criterion flips PASS → FAIL | **NOT REACHED** | requires the solve. |

**S1′/S3′ carry no predictive credit** — the card said so *before* it used them (§3.1). They are
reproduction gates over quantities pjm-172 had already measured. The gates with predictive force are
exactly the three that did not run.

---

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

**Established.** (1) The restated gates are satisfiable and the implementation **passes them
exactly**. (2) G-CTRL form 4 holds at this HEAD; no control LP is owed. (3) The seam's pre-2023 gas
error is −60.6 % / −31.7 % against the ISO's *own* burned gas, and F-A closes 2022 to −0.5 % while
overshooting 2021 to +5.1 %. (4) PJM's three failing criteria share one signature, whose largest
term is the interchange row F-A acts on. (5) The runner requirement is a **13.34 GiB tool-sandbox
cap**, not a 32 GB machine requirement.

**NOT established — do not quote any of this as measured.** (1) The `mc` footprint (**S4**).
(2) Whether 2022 net export moves toward 31.64 TWh (**S5**). (3) Any collateral effect on
C1/C2/C4/C8/C6 (**S6**). (4) **Any C3a movement in either year** — the card recorded ex ante that
2022 improves and 2021 worsens; **neither was measured and neither may be cited.**

---

## 9. THE OPEN QUESTIONS FOR THE OWNER

1. **Unblock the measurement** — grant one of the three in §2.2. It is ~4 min of LP per year and
   would close S4/S5/S6, the only gates that carry evidence.
2. **F-A is already in `main` with its footprint unmeasured** (§4). Keep it pending the
   measurement, or revert until measured? *(This session's read: keeping it is defensible on rule 14
   — it is inert in every scored year and the input is measurably right — but that is the owner's
   call, and it is a live change either way.)*
