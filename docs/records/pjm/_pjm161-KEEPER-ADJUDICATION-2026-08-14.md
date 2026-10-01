# pjm-161 — keeper adjudication: `pjm_measured_outage_event_cap` is NOT a keeper

**Session:** pjm-161 · **Date:** 2026-08-14
**Arm:** `2026-08-14-pjm-161-event-cap` (`pjm161_evcap_B`), single delta on
`2026-08-14-pjm-161-control` (`pjm161_ctl_A`)
**Full evidence:** `FINDING-pjm161-outage-inversion-and-da-virtual-energy-2026-08-14.md`
**Pre-registration:** `PREREG-pjm161-measured-outage-event-cap-2026-08-14.md`

## The question

The owner's standing standard is *"if structural integrity improves but gates
regress that may still be a keeper."* Applied to this arm it does **not** carry a
promotion — and the reason is worth stating exactly, because the arm's *numbers*
look promotable.

## The gate half of the test is not what fails

**No gate regresses.** Both arms score **C1 16/16 · free 12/12**, and C2, C3a,
C3b, C3c, C4, C8 all PASS. Both read NOT-YET only on the C6 governance gate
being UNATTESTED, which is the ordinary state of a replay bundle (the same state
pjm-158's two arms were registered in). Several class errors move favourably:

| TWh error vs EIA-923 `classFull` | control | arm |
|---|---:|---:|
| 2025 `COAL_BIT` | +5.357 | **+3.477** |
| 2024 `CC_REGULAR` | +0.322 | **+0.039** |
| 2025 `CC_REGULAR` | +3.957 | **+3.268** |
| 2023 `CC_REGULAR` | −3.451 | −3.959 |
| 2025 `CT_PEAKER` | +3.555 | +4.821 |

On residuals alone this reads as a promotion.

## The premise fails: structural integrity does not improve

The decisive number is the **level**, and it was in the ex-ante record before
either arm solved (`_pjm161_removeonly_exante.json`):

| GW, annual mean | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model's asserted **fossil-thermal** outage | **41.7** | **43.2** | **41.2** |
| PJM's published **whole-fleet** outage total | 33.3 | 33.0 | 35.9 |

**Even if every megawatt PJM reports out were fossil-thermal, the model already
asserts more outage on the fossil fleet alone than the operator reports for the
entire system.** That is the neiso-63 economic-layup over-count, visible
directly. A REMOVE-ONLY cap can only make it deeper, so on **level** the
mechanism moves *away* from the operator's record rather than toward it.

On **shape** it moves toward the record only in the middle of the load
distribution. The pre-registered P6 measurement is unambiguous: corr(unavailable
MW, net load) narrows (−0.674→−0.651 / −0.704→−0.690 / −0.752→−0.720), but the
**top-1 % net-load unavailable MW is unchanged** — 23,160→23,160 /
25,403→25,403 / 24,222→24,249, i.e. within 27 MW. And P4 **failed outright**:
C3c hours > $200 are 3→3, 10→10, 32→32 with the max price identical at
258 / 301 / 722.

## Why that settles it

The mechanism's justification is *"the envelope is too shallow in scarcity"*.
The effect it actually delivers is *"the envelope is deepened in mid-load hours,
on top of a level that is already too deep"*. The favourable class errors are
therefore produced by an effect the justification does not cover — reaching the
right number through a mechanism that is not doing the thing it is defended by,
which rule 1 [R-STRUCT] forbids independently of whether the residual improved.

**Verdict: NOT a keeper candidate. Not promoted. Matrix cell `R`.**
**Keeper remains `2026-08-04-pjm-152-collapse` (CALIBRATED, 9/9).**

## What is NOT refuted

The Phase-0 finding that motivated the lever stands untouched: the CAMPD outage
envelope **is** anti-correlated with scarcity in every year (corr −0.68 to
−0.77; top-1 % net-load hours carry 0.22–0.38× the annual-mean derate), and
during Winter Storm Elliott it asserts its **lowest derate of 2022** — 15.6 GW
against PJM's own published 31.1 / 35.8 / 27.1 GW forced. That defect is real,
measured in every year, and **still unrepaired**. What is refuted is the *cap*
as a repair for it. FINDING §7.4 names the two successors the same measurement
selects:

1. **pjm-145 route (1)** — the restore ceiling composed with the
   structural-derate registry (port the ercot137 fix). The defect is **shape**,
   not level, and fixing a shape needs a mechanism that moves capacity in
   **both** directions; route (1) is what makes restoring safe.
2. **A planned/forced split of the CAMPD-detected windows** — the model's
   envelope carries none, which is why neither the total nor the forced basis
   works.
