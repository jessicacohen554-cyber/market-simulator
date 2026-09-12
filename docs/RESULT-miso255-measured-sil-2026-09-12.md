# RESULT (miso-255): the measured-SIL arm **fires, moves the import balance toward the meter in
# all five years, and FAILS its own decisive gate on 2021** — it relocates the rail onto the
# envelope instead of removing it.

**Session** `miso-255` · **ISO** MISO · **Date** 2026-09-12 · **Pin** `d0fec486fa2218afc55dbd2eb377bc2570e61699`
**Five shards, one per year, all on one pin.** Parent solved nothing (rule 32(a)). Controls are the
committed bundles (rule 29(b) form 4 — no control solve spent).
PRECOMMIT: `docs/PRECOMMIT-miso255-measured-sil-2026-09-12.md` + addenda 1/2/3.

---

## 1. RESULT

> **G-1 PASSES IN ALL FIVE YEARS — the arm fires**, for the first time in five shard generations
> (see §5 for the three defects that cost the first four). Every year's log carries
> `aggregate simultaneous-transfer limit REPLACED ... declared scalar 8700 MW`.
>
> **G-4 — the gate that decides whether the arm RESOLVES the object — FAILS on 2021.**
>
> | year | hours at ≥99 % of the envelope | pre-registered line | G-4 |
> |---|---:|---:|---|
> | **2021** | **94.75 %** | 80 % | **FAIL** |
> | 2022 | 2.65 % | 80 % | PASS |
> | 2023 | 26.32 % | 80 % | PASS |
> | 2024 | 22.72 % | 80 % | PASS |
> | 2025 | 18.87 % | 80 % | PASS |
>
> In 2021 the LP moves from railing the 8,700 MW planning scalar to railing the measured envelope.
> **That is the mechanism relocating the rail, not removing it** — precisely what G-4 was written to
> catch, and it fired at full strength. The other four years clear it comfortably.
>
> **THE IMPORT BALANCE IMPROVES IN ALL FIVE YEARS, MONOTONICALLY:**
>
> | year | net import: control → arm (meter) | \|error\| control → arm | gas miss control → arm |
> |---|---|---:|---|
> | 2021 | 75.93 → **49.34** (35.51) | 40.42 → **13.83** | −65.64 → **−44.08** |
> | 2022 | −22.58 → **13.83** (30.97) | 53.55 → **17.14** | −32.51 → **−60.68** |
> | 2023 | 43.19 → 41.94 (37.91) | 5.28 → 4.03 | −39.84 → −38.98 |
> | 2024 | 27.50 → 26.39 (23.08) | 4.42 → 3.31 | −33.62 → −32.74 |
> | 2025 | 20.35 → **19.02** (18.95) | 1.40 → **0.07** | −32.45 → −31.43 |
>
> **The pre-registered direction check PASSES**: 2022's absolute import move (36.42 TWh) exceeds
> 2021's (26.59), exactly as the envelope arithmetic predicted before either solve.
>
> **The mechanism does ONE thing, and the class deltas prove it.** The import move is offset almost
> entirely by fossil, with nothing else touched: 2021 `import −26.59` against `CC_REGULAR +16.73,
> COAL_PRB +3.62, CC_CHP +2.07, ST_GAS +1.51, COAL_BIT +1.24`; 2023-25 `import −1.25/−1.11/−1.33`
> against `CC_REGULAR +0.35/+0.32/+0.51` and sub-0.3 TWh elsewhere. No renewable, nuclear, hydro or
> storage class moves materially in any year.
>
> **2022's gas regression is an UNMASKING, not a new defect, and I state it that way with the
> number attached.** The model under-imports 53.55 TWh *and* under-produces gas by 32.51 TWh in
> 2022. Repairing the import axis (+36.42 TWh) necessarily displaces fossil (−33.22 TWh across five
> classes), so the gas miss deepens to −60.68. The export rail was concealing a pre-existing gas
> shortfall by forcing the fleet to generate for export. **That is a real cost of the repair and it
> is reported at full magnitude, not argued away** — but it is not the arm inventing an error.

---

## 2. THE GATES, AS SCORED

Scored by the committed `scripts/probes/_miso255_screen_gates.py`, written and pushed before any
solve. No gate reads C1 `CC_REGULAR`, C3a or the gas volume.

| gate | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** liveness | PASS | PASS | PASS | PASS | PASS |
| **G-2** confinement | **FAIL** (export) | PASS | PASS | PASS | PASS |
| **G-3** rail broken | **FAIL** (literal) | PASS | PASS | PASS | PASS |
| **G-4** not a pin | **FAIL** 0.9475 | PASS 0.0265 | PASS 0.2632 | PASS 0.2272 | PASS 0.1887 |
| **G-5** non-target | unscored | unscored | unscored | unscored | unscored |
| scorer verdict | **STOP** | no STOP | no STOP | no STOP | no STOP |

**TWO OF THE THREE 2021 FAILURES ARE MY SCORER'S DEFECTS, AND I DECLINE TO COUNT THEM AGAINST THE
MECHANISM — while equally declining to use them to excuse G-4.**

* **G-3 is mis-specified.** It tests `arm_rail_hours == 0` at the 8,700 MW scalar. But 2021's
  measured import envelope **peaks at 9,064 MW — above the scalar** — so hours the envelope
  legitimately permits above 8,700 are counted as a "rail" that no longer exists. Measured
  reduction: **8,650 h → 198 h, 97.7 %**. The gate should have tested occupancy of the *new* bound,
  which is what G-4 does. My error, written into the PRECOMMIT before the solves and honoured as
  written rather than silently re-scored.
* **G-2's 2021 export breach is 1,603.8 MW in 3 hours of 8,760, and probably a grain mismatch —
  but I have NOT proven that and do not claim it as settled.** I verified the injected group covers
  every boundary link including the `miso_south_seam_split` re-point
  (`MISO_external_South → MISO-South` is in the group). The likely cause is the scorer comparing the
  `import` **class total** — which includes `miso_firm_imports` modelled as *generators* — against a
  bound that governs **link flows**. The import side matching to **0.0004 MW in all 8,760 hours** is
  consistent with that reading. It is an open item, not a cleared one.
* **G-5 is unscored in every year**: `replay_keeper` writes no `metrics.json` /
  `legitimacy_diagnostics.json` into an arm bundle, so C2/C6/C8 could not be checked from the shard.
  A promotion must score them on the composed bundle before it registers.

**G-4 is in none of those categories.** It is computed identically on arm and control, from the same
series, and it fails cleanly at 94.75 % against an 80 % line fixed before any solve.

---

## 3. WHAT THIS SETTLES, AND WHAT IT DOES NOT

**Settled — the rule 14 `[R-ACCURATE]` provenance repair is sound and its effect is what its
arithmetic said.** The 8,700 MW bidirectional scalar is MISO's published Capacity Import Limit, a
PRA/LOLE accreditation construct; the meter falsifies it in the hourly-energy role in both
directions; replacing it with the measured coincident boundary envelope moves the boundary flow
toward the meter in **every one of five years**, at zero free parameters, touching one interface row
and nothing else.

**NOT settled — that the arm resolves the 2021/2022 object.** It does not. G-4 says the 2021 LP
still wants maximum import in 94.75 % of hours; the arm bounds that want at a defensible ceiling
instead of an indefensible one, which lowers the error from +40.42 to +13.83 TWh but leaves the
*want* untouched. **A price-formation object survives the repair**, and the residual 13.83 TWh
over-import plus the 94.75 % envelope occupancy is its new signature. That is the successor, and it
is a price question, not a seam question.

---

## 4. THE KEEPER RECOMMENDATION

**Recommend: LAND THE CODE. Do NOT claim the arm as the fix for 2021/2022.** On promoting it into
the MISO keeper recipe, the honest position is split and the decision is the owner's:

* **For promotion on the TRAINING SPAN 2023-2025**: all four scorable gates PASS in all three years;
  import error falls (5.28→4.03, 4.42→3.31, 1.40→0.07); the gas miss shrinks in all three
  (+0.86/+0.88/+1.02 TWh toward the meter); `CC_REGULAR` rises slightly toward its benchmark; the
  class deltas are confined to import + fossil; and the structural provenance defect is repaired.
  Under rule 30(c) the held-out years never downgrade the ISO. This is a clean, small, structurally
  motivated improvement on exactly the span the keeper covers.
* **Against**: by this session's own pre-registration, **a STOP gate fired on a screen year**, and
  the PRECOMMIT says a screen "may kill an arm; it may never promote one". Promoting now banks a
  level improvement while the object G-4 identifies survives untouched. The owner's standing rule
  ("structural integrity improves but gates regress may still be a keeper") is what makes promotion
  available at all here — it is not something this lane may invoke on its own authority.

**A promotion needs no new solves**: the 2023 / 2024 / 2025 legs exist and were solved on one pin.
The parent composes them into one span bundle, runs `stamp_config_partition.py --check`, scores
C2/C6/C8 (unscored above), registers, and flips the keeper. **Rule 31 `[R-RETAIN]`: the five
`miso255_sil_*` bundles are gitignored on five ephemeral shard containers and will NOT survive
them.** If promotion is wanted, it is cheapest now and costs ~35 min of re-solve later.

---

## 5. THE FOUR GENERATIONS THIS COST, AND WHY EACH FAILED

Recorded because three of the four were my defects and a successor should not repeat them.

| gen | outcome | cause |
|---|---|---|
| A | died ~29 s in | **My defect.** `solve_and_persist` passed a kwarg `run_year` never accepted — the nyiso-229 class, reproduced independently. Caught by an AST check of the pin; fixed by threading the parameter (ADDENDUM 1). |
| relaunch | stalled BLOCKED | Asked the parent whether to rebase; no channel existed to answer. Fixed by pre-answering every git question in the prompt. |
| B | solved, arm INERT | **My defect.** The consumer sat only in `runner.run_scenario_iso` — the forecast path. The backcast builds its own `interface_groups`. **Found by a shard that investigated and reported instead of patching**, and independently by its sibling stopping at HARD STOP 4 (ADDENDUM 2). |
| C | stopped before solving | **My defect.** A 20 GiB free-disk hard stop I set reactively off one ENOSPC report without doing the arithmetic. `solve_container.py` sizes its own swapfile as `min(deficit, free − 6)` and needs ~13 GiB, not 20; miso-254 shard A had solved on ~17 GiB free. Corrected to 13 GiB. |
| **D** | **all five solved, arm live** | — |

**The pre-registered liveness gate (G-1 / HARD STOP 4) earned its place**: it caught the inert-arm
generation from one side while a shard's own investigation caught it from the other. **No wrong
number reached any artifact in any generation.** Measured cost: five MISO years at 639-911 s
(peak 16.4-18.9 GiB rss+swap), plus ~9 stopped shards.

---

## 6. RULES

* **Rule 29 `[R-SCREEN]`** — gates, values, screen years and the direction check were all fixed
  before any solve and are reported as written, including the two I got wrong. The owner's
  "launch them all" inverted the screen-first ordering; ADDENDUM 3 recorded that before any number
  existed.
* **Rule 29(b) form 4** — the committed bundles are the controls; **no control solve was spent** in
  any generation. G-DRIFT re-audited at each rebase; all hunks INERT for MISO.
* **Rule 14 `[R-ACCURATE]` / rule 13 `[R-MEASURED]`** — the repair is motivated by the meter
  falsifying the scalar, not by the residual; the envelope is a ceiling the measured flow exceeds in
  11.8-15.4 % of hours, guarded by test.
* **Rule 19 `[R-ONE-MECH]`** — the scalar is REPLACED, never stacked; exactly one interface row
  moves, confirmed by the class-delta census.
* **Rule 30(c)** — 2021/2022 are held-out; they are reported and never downgrade MISO.
* **Rule 31 `[R-RETAIN]`** — nothing deleted; bundles gitignored, on ephemeral disk, and the
  promotion question is put to the owner explicitly in §4.
* **Rule 32 `[R-SHARD]`** — the parent never solved; one year per shard, one pin for all five so the
  legs compose.
