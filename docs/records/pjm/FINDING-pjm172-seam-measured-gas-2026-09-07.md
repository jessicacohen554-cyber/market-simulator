# FINDING — pjm-172: F-A **KILLED at zero LP**, at gates S1 and S3, before any solve

**Session** pjm-172 · **ISO** PJM · **Date** 2026-09-07 · **LP spent: NONE**
**Card** `docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md` (binding; not rewritten)
**Predecessor** `results/calibration/ADDENDUM-pjm171-seam-fuel-basis-freeze-2026-09-07.md`
**Keeper** `2026-08-15-pjm-162-inputclock` — **unchanged**. Nothing promoted, nothing registered.
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).

---

## 0. RESULT IN ONE PARAGRAPH

The F-A repair was implemented exactly as PRECOMMIT §2 declares it and it **works**: below the
trajectory's first knot the seam now resolves Henry Hub from the measured annual series
(2022: $2.54 → **$6.419058**/MMBtu on every PJM seam), the neighbour's `gas_basis` is applied
unchanged, and 2023–2025 plus every forecast year are **bit-identical**. But the card's two
*pre-solve* gates then failed, and they failed for one structural reason the card did not
anticipate: **three of PJM's five seams price their implied heat rate as a function of that very
gas level.** Carolinas / TVA / LGEE carry `hr_by_year = None` in **every** year — SERC publishes no
nodal LMP to anchor a per-year heat rate to — so they always take `neighbor_heat_rate`'s gas-elastic
branch, `hr = 5.6 + 14.2 / gas`. Raising gas therefore *lowers* their heat rate, by design.
Consequently **S1 fails** (it requires `neighbor_heat_rate` to be unchanged, which **no** gas-level
repair can satisfy on this ISO) and **S3 fails** (measured 2022 seam baseload mean **61.145 $/MWh**
against §4's predicted **74.156**, tolerance 1e-6). Per rule 29 `[R-SCREEN]` step 0 and the card's
own kill rule, the arm is dead: **the 2022 screen was never solved and 2021 was never spent.**

---

## 1. THE GATE TABLE — every gate the card pre-registered, graded

Gates S1–S3 are computable at zero LP, which is why the kill lands before the screen (rule 29
step 0: *"An arm that has a computable pre-solve gate does not reach a solve until that gate
passes."*). S4–S6 require the solve and were therefore **never reached**.

| # | gate | verdict | measured |
|---|---|---|---|
| **S1** | resolution — only the seam gas level differs; `neighbor_heat_rate` **unchanged** in both years | **FAIL** | Gas moves on all 5 seams as intended. But `neighbor_heat_rate` **moves on 3 of 5**: Carolinas / TVA / LGEE go **11.1906 → 9.2320** (2021) and **11.1906 → 7.8122** (2022). MISO (12.9) and NYISO (10.4) are unchanged. |
| **S2** | identity — bit-identical for every year ≥ 2023 and every forecast year, all 5 neighbours, `low`/`mid`/`high` | **PASS** | Byte-identical in 2023 / 2024 / 2025 on every seam and every key; the pre-first-knot branch is unreachable at or above a knot. Asserted by test, not argued (PRECOMMIT §3.4). |
| **S3** | magnitude — 2022 seam baseload = §4's **74.156** mean, per-neighbour as tabled, \|err\| ≤ 1e-6 | **FAIL** | Measured mean **61.1448** (err **−13.011**). Per-neighbour: MISO **82.806** ✓, NYISO **72.478** ✓, Carolinas / TVA / LGEE **50.147** against a predicted 71.833 (err **−21.686** each). |
| **S4** | footprint — only the 80 seam `mc` rows move | **NOT REACHED** | requires the solve. |
| **S5** | direction — 2022 net export rises from 21.65 TWh | **NOT REACHED** | requires the solve. |
| **S6** | collateral — no non-C3a load-bearing criterion flips PASS → FAIL | **NOT REACHED** | requires the solve. |

**Kill rule applied as written:** *"any gate fails ⇒ the arm is dead, 2021 is never spent, nothing
is promoted, and the result is the session's finding."* No LP was spent on either year.

---

## 2. THE MEASUREMENT — every number this session will ever cite

Arm = this HEAD. Control = the identical measurement with the change reverted (`git stash`), so the
control column is the true pre-repair path and not a reconstruction.

### 2.1 Per-seam, 2022 (the card's screen year)

| neighbour | gas ctl | gas arm | HR ctl | HR arm | HR moved? | baseload ctl | baseload arm |
|---|---|---|---|---|---|---|---|
| MISO | 2.5400 | 6.4191 | 12.9000 | 12.9000 | no | 32.7660 | **82.8059** |
| NYISO | 3.0900 | 6.9691 | 10.4000 | 10.4000 | no | 32.1360 | **72.4782** |
| Carolinas | 2.5400 | 6.4191 | 11.1906 | **7.8122** | **yes** | 28.4240 | **50.1467** |
| TVA | 2.5400 | 6.4191 | 11.1906 | **7.8122** | **yes** | 28.4240 | **50.1467** |
| LGEE | 2.5400 | 6.4191 | 11.1906 | **7.8122** | **yes** | 28.4240 | **50.1467** |
| **MEAN** | | | | | | **30.0348** | **61.1448** |

### 2.2 Per-seam, 2021

| neighbour | gas ctl | gas arm | HR ctl | HR arm | baseload ctl | baseload arm |
|---|---|---|---|---|---|---|
| MISO | 2.5400 | 3.9097 | 12.9000 | 12.9000 | 32.7660 | 50.4349 |
| NYISO | 3.0900 | 4.4597 | 10.4000 | 10.4000 | 32.1360 | 46.3807 |
| Carolinas / TVA / LGEE | 2.5400 | 3.9097 | 11.1906 | **9.2320** | 28.4240 | 36.0942 |
| **MEAN** | | | | | **30.0348** | **41.0197** |

### 2.3 The measured Henry Hub annual means (the card's only new input)

`data/raw/gas-prices/henry_hub_monthly.csv`, mean of the twelve monthly EIA spot prices — the same
series `HENRY_HUB_TRAJECTORIES` cites for its own historical knots:

| year | measured | card §2 (3 dp) |
|---|---|---|
| 2019 | 2.5650749999999998 | 2.565 |
| 2020 | 2.033716666666667 | 2.034 |
| 2021 | 3.9096833333333336 | 3.910 |
| 2022 | 6.419058333333333 | 6.419 |

All four reproduce §2 to its stated precision. **Zero free parameters, zero new `ScenarioConfig`
fields** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`).

### 2.4 The one §4 conclusion the correction leaves standing

The **screen-year choice is uncontaminated**. On the corrected arithmetic the 2022 footprint is
**+31.110 $/MWh** and 2021's is **+10.985** — a ratio of **2.832**, which is §4's stated **2.83×**
to three significant figures. 2022 was and remains the year the mechanism is largest, so the choice
was correctly made on footprint and not on a residual.

---

## 3. ROOT CAUSE — the card's gates, not the implementation

**The control column vindicates the apparatus.** This session's measured control reproduces §4's
control on **all five** seams exactly — 32.766 / 32.136 / 28.424 ×3, mean 30.0348 vs §4's 30.035 —
including the elastic three at `2.54 × (5.6 + 14.2/2.54) = 2.54 × 11.1906 = 28.424`. So the card and
this session agree wherever the card is self-consistent.

**§4's arm column carried the control's heat rate.** `71.833 = 6.419058 × 11.1906` — that is the
2022 measured gas multiplied by the **$2.54** heat rate. The prediction implicitly held
`neighbor_heat_rate` constant while moving gas. `_HR_GAS_ELASTIC` makes that impossible for these
three seams: `hr = hr_phys + hr_adder / gas`, so the heat rate falls as gas rises. That single
substitution is the whole of the −21.686 per-seam miss and the whole of the −13.011 mean miss.

**And the elasticity is intended behaviour, not a defect.** `neighbor_price.py`'s own module
comment says these coefficients were fitted precisely *"so the coal/nuclear Southeast does not ride
Henry Hub up in a dear-gas year"* — at a flat 11.6 heat rate the seam priced to $40.8 in 2025, only
~$2 below PJM, and the diurnal swing flipped it to a wrong-direction export (+2.0 TWh against a
measured −5.9). The self-cancellation S3 tripped over is the mechanism working as designed.

**Why card F-B would NOT fix this.** The PRECOMMIT excluded F-B (the missing 2021/2022 `hr_by_year`
entries) so that S3 would measure the gas level alone. But the three Southeast seams have
`hr_by_year = None` for **every** year, not merely 2021/2022 — there is no SERC nodal LMP to build
one from. Their elastic branch is their permanent price-formation anchor, so no F-B-shaped card can
make S1's *"`neighbor_heat_rate` is unchanged"* true. **S1 is structurally unsatisfiable for any
change to PJM's pre-2023 seam gas level**, and this is the finding's main transferable content.

---

## 4. WHAT IS AND IS NOT ESTABLISHED

**Established.**

1. The defect the card set out to repair is **real and still unrepaired**: the seam is frozen at
   2023 conditions in every pre-2023 year (−32 % in 2021, −61 % in 2022 on the gas level).
2. The implementation does exactly what §2 declared, and is **inert by test** in every training year
   and every forecast year (gate S2), so **no keeper can move** and no determination is re-verified.
3. Moving the gas level alone moves the seam baseload by **+31.110 $/MWh** in 2022 and **+10.985**
   in 2021 — about **70 %** of the size §4 predicted, because the Southeast self-cancels.
4. `neighbor_gas_price` is materially, not marginally, wrong before 2023 — a rule 14 `[R-ACCURATE]`
   question that this kill does **not** settle.

**NOT established — do not quote any of this as measured.**

1. Whether the repair moves 2022 net export toward the measured 31.64 TWh (**S5 never ran**).
2. Whether its `mc` footprint is confined to the 80 seam rows (**S4 never ran**).
3. Any collateral effect on C1 / C2 / C4 / C8 / C6 (**S6 never ran**).
4. **Any C3a movement, in either year.** The card recorded ex ante that 2022 would improve and 2021
   would worsen; **neither was measured**, and neither may be cited.

---

## 5. GOVERNANCE

- **Rule 29 `[R-SCREEN]`** — killed at step 0, the zero-LP phase. The 2022 screen was never solved;
  2021 was never spent. **No screen bundle exists**, so clause (c) has nothing to delete and the
  parity gate sees nothing (rule 31 `[R-RETAIN]` likewise has no artifact at risk).
- **Rules 1 `[R-STRUCT]` / 29** — no gate was re-read, re-weighted or re-written after a number
  existed. S1 and S3 are graded exactly as the card fixed them, against the card's own numbers.
- **Rule 22 `[R-HOLDOUT]`** — no validation-tier spend occurred. PJM's `complete` marker is unspent
  by this session and `--holdout-authorized` was never passed.
- **Rule 30(c)** — PJM's headline stays **CALIBRATED** regardless.
- **Rule 19 `[R-ONE-MECH]`** — F-B was not bundled, as instructed. §3 records why that separation,
  though correctly motivated, cannot rescue S1.
- **Rule 14 `[R-ACCURATE]`** — the accurate input was **not** discarded to protect a fit; it was
  never scored against one. The promotion question is open and is the owner's (§6).

---

## 6. THE OPEN QUESTION FOR THE OWNER

The arm is dead at its own gates. What is **not** decided — and is not this session's to
decide — is whether the underlying repair should land anyway. The code and its 40 tests are on the
branch, unpromoted and unarmed, and the change is inert in every scored year.

The case for landing it is rule 14 `[R-ACCURATE]`: holding the 2023 knot back into 2021/2022 is a
−32 % / −61 % error in a measured physical fuel price, and *"if swapping a hand estimate for real
data makes the backcast worse, that is a signal that something else in the model is miscalibrated"*.
The case against landing it now is that **nothing about its effect has been measured** — S4/S5/S6
never ran — so landing it would arm a live change to shared seam code on the strength of its
inputs alone.

Three routes, for the owner:

- **(a) Re-gate and screen.** A successor PRECOMMIT restates S1 and S3 with the gas-elasticity in
  them (S1: *"`neighbor_heat_rate` moves only through the declared elastic law"*; S3: the corrected
  **61.145** mean), then screens 2022 as this card intended. One 2022 LP.
- **(b) Land the repair on rule-14 grounds without a screen**, treating it as an input correction
  rather than a mechanism — defensible because it is provably inert in every scored year, but it
  forgoes the footprint and direction evidence.
- **(c) Drop it** and leave the seam frozen before 2023, with the defect documented.

**Recommendation: (a).** The mechanism is sound and the defect is real, but S5 — does net export
actually rise toward the measured 31.64 TWh — is the question worth an LP, and it is the one this
session could not answer.

---

## 7. ARTIFACTS

- `src/market_sim/data/neighbor_price.py` — `_measured_henry_hub_annual`, the pre-first-knot branch,
  and the `hindcast_asknown_*` look-ahead refusal.
- `tests/unit/data/test_neighbor_price_measured_gas.py` — 40 tests, all passing: the measured
  series, the repair, the look-ahead refusal (with a reachability assertion so it cannot go vacuous),
  the S2 inertness identities across every registered ISO, and the §3 root cause asserted rather
  than narrated.
- `docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md` **Appendix A** — the G-DRIFT
  audit: 69 changed solve-path files, **zero LIVE hunks**, PJM solve-surface fingerprint
  `0f749d17202c32d9` identical at `f36cee6e` and HEAD. G-CTRL form 4 was valid and no control LP was
  spent — a conclusion the kill then made moot, but which is recorded because it was established
  before the arm was built, as rule 29(b) requires.

---

## 8. ADDENDUM — the 2021/2022 measurement was ATTEMPTED and is BLOCKED ON CONTAINER RAM

*(Appended after the owner directed the lane to finish the repair rather than stop at the gate
grading of §1. The instruction is followed; the arm was built, the data gaps were closed, and the
solve was launched. It could not complete here, for a reason that has nothing to do with the
mechanism.)*

**What was done.** The G-CTRL form-4 A/B was set up exactly as §6 of the PRECOMMIT specifies:
`scripts/replay_keeper.py results/calibration/pjm169_tp2022_2021_f2arm` at this HEAD, which replays
the committed touchpoint's own kwargs so the **only** difference against the control is the F-A
code delta (G-DRIFT having established zero LIVE hunks). Two environment gaps had to be closed
first, both of them container state rather than repo state:

1. **`data/clean/` was entirely unbuilt** (it is derived, disposable and gitignored). Curated from
   `data/raw` — `transfer-interface-limits` (2019–2025), `ramp-capability`, `load`,
   `demand-profile`, `ancillary-services`, `generation`, `renewables`, `outages`, `fleet`, `egrid`,
   `unit-outage-events`, `partial-outages`, `gtc-limits`, `hydro-plant-modes`,
   `ercot-wtx-congestion`. (`lmp` fails on a **CAISO** raw column — `KeyError: 'MGHG'` in
   `parse_caiso_file` — a pre-existing defect in another ISO's drop, unrelated to PJM and to this
   card.)
2. **`data/raw/pjm-da-virtuals/` was empty** — the converted-corpus payload is gitignored and was
   stripped from history, so recovery is re-fetch only, exactly as the charter's Phase-B note
   warned. **Re-fetched: all 24 monthly `hrl_da_incs_decs_{2021,2022}_*.parquet` files**
   (`scripts/data/fetch_pjm_da_virtuals.py`, DataMiner2 public subscription key, ~3.8 MB). This
   unblocks the EMAAC availability card's Phase B as a side effect.

**Where it stopped.** The solve reached LP construction on 2022 — past every data gate, with the
seam repricing and the per-gen reserve co-opt (39 R columns / 2,392 member units, two balance
families) both logged — and was then **killed by the kernel, SIGKILL / exit 137**, twice:

| attempt | conditions | outcome |
|---|---|---|
| 1 | `--years 2022 2021`, clean-layer build running concurrently | OOM at LP construction |
| 2 | `--years 2022` alone, whole box, **14 GB free at launch** | OOM at LP construction |

Available memory fell monotonically 14 → 6 → 3 → 2 → 0 GB across attempt 2. **This container has
15 GB total, and one PJM plant-level 8760 LP on the keeper recipe exceeds it.** Rule 12
`[R-PARALLEL]` already warns that a single year's LP uses several GB and caps *concurrent*
per-plant multi-zone runs at ~2; here even **one** does not fit.

**Not worked around, deliberately.** Every available lever — dropping `pjm_da_virtual_bids`,
the per-gen reserve co-opt, or the zonal loss surface — would change the recipe, and the A/B's
entire validity rests on the arm being the committed touchpoint's recipe *plus the F-A delta and
nothing else*. A cheaper solve would measure a different model. Nothing was disabled.

**So §4's "NOT established" list stands unchanged**: S4 footprint, S5 net-export direction, S6
collateral and **any C3a movement in either year remain unmeasured and unquotable.** The two
partial bundle directories (`results/calibration/pjm172_fa_arm{,_2022}/`) contain no solved
output — they hold an empty `dispatch/` dir and nothing else — so rule 31 `[R-RETAIN]` has no
artifact to preserve and the promotion question is not gated on them.

**What the successor needs:** a runner with **more RAM** (≥ 32 GB is the safe read on a 15 GB
box OOMing at peak), and nothing else. The repair, the tests, the G-DRIFT audit, the curated
clean layer and the re-fetched virtuals corpus are all in place; the command is one line, in §9
of the handoff.
