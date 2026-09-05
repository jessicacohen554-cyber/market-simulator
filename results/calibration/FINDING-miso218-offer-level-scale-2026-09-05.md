# FINDING miso-218 — THE RATIO-PRESERVING OFFER-LEVEL SCALE (×1.10): **the owner's premise held and my decisive pre-registered prediction was WRONG** — all three C3a years land inside ±10 % and the lane's standing C3a-2025 failure CLOSES (−12.297 → **−6.313 PASS**). It buys that by breaking a **load-bearing C1 cell** (`ST_GAS`-2024 −7.155 → **−8.030**, PASS → FAIL), pushing **every** C8 class-year further over budget, and leaving the scarcity tail **exactly as absent as before** — so the determination trades one load-bearing failure for another and does not improve. **NOT a keeper candidate**, pre-committed before the solve (2026-09-05)

**KEEPER UNCHANGED at `2026-09-05-miso-217-intermphys`.** This run is a **rule-13
DIAGNOSTIC PROBE**, registered as `2026-09-05-miso-218-levelscale-probe` (bundle
`results/calibration/miso218_levelscale_B`). PREREG
`PREREG-miso218-offer-level-scale-2026-09-05.md` pushed **BLIND** at `1deae2b2`, before the
solve. **No `ScenarioConfig` field minted, no matrix row, ledger 41/2 unchanged.** Rule 22:
2023–2025 only.

---

## 0. Verdict in one paragraph

The owner asked for a run that *"keeps relative offer curve ratio the same but shifts
multipliers up… +10 % room to keep all 3 years calibrated while maintaining fossil merit
order"*, on the reading that C3a-2025 *"kinda seems like a peaking price miss"*. Executed
literally — every band multiplier of all 13 fossil classes ×1.10, within-class ratios and
fossil merit order preserved exactly, `phys_*` and structural shares untouched. **The
premise held and I was wrong about the thing I said was decisive.** I pre-registered that
C3a-2023, sitting at +1.096 % against a ±10 % band, would **exit**; it does not — it lands
at **+8.402 % PASS**. The measured price pass-through is **+7.23 / +7.49 / +6.82 %**, and
**all three C3a years finish inside the band**: 2023 +8.402, 2024 +4.396, **2025 −12.297 →
−6.313 PASS**. The lane's standing C3a-2025 failure is closed by this lever. **What it costs
is why it is still not a keeper, and the reasons are independent.** First, and declared in
the PREREG **before the solve**: a uniform multiplicative lift chosen to move a price
residual is a **fitted level scalar identified against that residual**, which rule 1
`[R-STRUCT]` forecloses as a keeper mechanism and rule 13 admits only as a default-off
diagnostic probe. Second, and now measured: **it is not even a gates win.** It flips
**`fuelmix` `ST_GAS`-2024 out of the ±8.00 TWh band** (−7.155 → **−8.030**, PASS → FAIL) —
the only PASS→FAIL flip on the board and a **load-bearing** criterion — so the determination
goes **NOT-YET on C3a-2025 → NOT-YET on fuelmix**. Third, it does nothing to the object the
owner correctly identified: **C3c hours above $200/MWh move 3 / 7 / 0 → 3 / 7 / 1 against an
actual 30 / 37 / 88.** The peaking miss is exactly as absent as before; the mean closed
because a Jun–Jul median that miso-202/203 measured as **already above actual** (37.47 vs
32.73) was pushed higher still.

## 1. What was run

Every offer-curve band multiplier (`committed`, `econ_low`, `econ_high`, `peak`) of all
**13 fossil classes** scaled **×1.10**. Verified before the solve: **within-class ratios
preserved exactly**, `phys_*` keys **untouched**, structural shares (`econ_low_share`,
`pct_peaking`) **untouched**. Because every class scales by the same factor, **fossil merit
order is preserved exactly** for the fuel-scaled component of every unit's marginal cost —
the owner's constraint, met by construction.

| class | before | after |
|---|---|---|
| `CT_PEAKER` | 1.025 / 1.00 / 1.00 / 4.00 | 1.1275 / 1.10 / 1.10 / 4.40 |
| `CT_INTERMEDIATE` | 1.00 / 1.00 / 1.20 / 3.00 | 1.10 / 1.10 / 1.32 / 3.30 |
| `CC_REGULAR` | 1.005 / 0.95 / 1.08 / 2.25 | 1.1055 / 1.045 / 1.188 / 2.475 |
| `ST_GAS` | 1.00 / 1.00 / 1.00 / 1.00 | 1.10 / 1.10 / 1.10 / 1.10 |
| `COAL_PRB` | 1.00 / 1.00 / 1.19 / 1.48 | 1.10 / 1.10 / 1.309 / 1.628 |

**Nothing was minted.** The scale rides the existing `offer_curve_by_group` operator channel
via `replay_keeper --set`, recorded verbatim in the probe's `run_config.json`. No
`ScenarioConfig` field, no registry surface (rule 24), no matrix row (rule 28c not engaged).
Control is the keeper bundle itself, S-0 inherited, never re-solved.

## 2. THE RESULT — C3a, and my own decisive prediction refuted

| year | keeper C3a | probe C3a | price lift | band ±10 % |
|---|---:|---:|---:|---|
| 2023 | +1.096 % PASS | **+8.402 % PASS** | +7.23 % | inside |
| 2024 | −2.879 % PASS | **+4.396 % PASS** | +7.49 % | inside |
| **2025** | **−12.297 % FAIL** | **−6.313 % PASS** | +6.82 % | **inside** |

**PREREG P-2 — the prediction I called decisive — is WRONG.** I predicted C3a-2023 would
exit the band, landing in [+8.5 %, +11.5 %]. It lands at **+8.402 %**, inside the band and
below my own range. The owner's "+10 % room to keep all 3 years calibrated" premise is
**correct as measured**, and my pre-solve arithmetic (§3 of the PREREG, which computed only
+8.90 % of headroom on 2023) was too pessimistic because it assumed a full 10 % price
pass-through; the measured pass-through is **6.82–7.49 %**, since `vom` and emission adders
do not scale. **P-1 is also wrong on its 2025 leg** (6.82 % against a predicted 7.0–9.5 %
floor). **P-3's substantive claim is right** (2025 clears) though its band [−6.0, −3.0]
missed the value by 0.31 pp.

## 3. WHAT IT COSTS — and why the determination does not improve

**A load-bearing C1 band exit.** `fuelmix` `ST_GAS`-2024 goes **−7.155 → −8.030 TWh**
against a ±8.00 band: **PASS → FAIL**, the **only** PASS→FAIL flip on the board.

| C1 cell | keeper | probe | Δ | arm headroom |
|---|---:|---:|---:|---:|
| **`ST_GAS`\|2024** | **−7.155** | **−8.030** | −0.875 | **EXIT** |
| `CT_PEAKER`\|2024 | −3.634 | −5.212 | −1.578 | 2.788 |
| `COAL_PRB`\|2023 | +1.071 | −0.376 | −1.447 | 7.624 |
| `CC_REGULAR`\|2024 | +7.947 | +6.564 | −1.383 | 1.436 |
| `COAL_PRB`\|2025 | −4.231 | −5.581 | −1.350 | 2.419 |
| `CT_PEAKER`\|2023 | −5.934 | −7.086 | −1.152 | **0.914** |

So the determination is **NOT-YET on `price_mean` (C3a-2025) → NOT-YET on `fuelmix`
(`ST_GAS`-2024)**. **The run closes one load-bearing failure and opens another.** It is not
a determination improvement; it is a substitution.

**The pre-registered named risk did NOT fire, and a different cell did.** I named
`CC_REGULAR`-2024 — left with 0.053 TWh of band by miso-217 — as the most likely way P-6
would be wrong. It moved the **safe** way (+7.947 → +6.564), because a uniform lift suppresses
CC as well. **P-6 is wrong about which cell and right that a C1 cell was the live risk.**

**C8 rises on every class-year**, because pricing fossil out leaves the forced floors a larger
share of a smaller class:

| class | keeper 23/24/25 | probe 23/24/25 |
|---|---|---|
| `CT_PEAKER` (0.15 budget) | 0.2280 / 0.1573 / 0.1319 | **0.2571 / 0.1756 / 0.1437** |
| `ST_GAS` (0.30 budget) | 0.1479 / 0.1555 / 0.2070 | 0.1665 / 0.1784 / 0.2162 |

All three `CT_PEAKER` years are now above the 0.15 peaker budget, where 2025 was below it.

## 4. THE TAIL IS UNTOUCHED — the owner's own diagnosis, confirmed against the lever

The owner read C3a-2025 as *"a peaking price miss"*. **That reading is right, and it is
exactly what this lever does not fix.**

| year | model hours RT LMP > $200 | | actual |
|---|---:|---:|---:|
| 2023 | 3 → **3** | | 30 |
| 2024 | 7 → **7** | | 37 |
| 2025 | 0 → **1** | | 88 |

**PREREG P-5 RIGHT.** A 10 % lift on a $183.22 model maximum reaches ~$202 against an actual
$1,669.52. C3c stays the single ledgered caveat in both legs. The mean closed **not** by
adding the missing peaks but by raising the whole distribution — including a Jun–Jul median
miso-202/203 measured as **already above actual** (37.47 vs 32.73), in a year where the top
1 % of hours carry 99.9 % of the mean gap and 13 of the 15 scarce hours fall in h18–h21.

**C3b (price shape, NRMSE, lower better):** 0.080 → 0.115 and 0.105 → 0.111 (**worse**, as
P-4 predicted) but **0.180 → 0.149 in 2025 (better)**, which P-4's reasoning did not
anticipate and which is reported against the prediction. **P-4 RIGHT on its 2-of-3 bar,
wrong on its mechanism for the year that matters.**

## 5. Disposition — NOT a keeper candidate, for two independent reasons

1. **Pre-committed before the solve (PREREG §2).** A uniform multiplicative lift chosen to
   move a price residual is a fitted level scalar identified against that residual. Rule 1
   `[R-STRUCT]`: *never reach the right number through a mechanism that isn't real — a
   fitted adder, a load proxy, a haircut tuned to the residual.* Rule 13 `[R-MEASURED]` gives
   it its only admissible form, which is what this is: an explicitly-labelled, default-off
   diagnostic probe that must never be enabled in a keeper.
2. **Measured after the solve, and independent of (1): it is not a gates win.** It trades
   C3a-2025 for C1 `ST_GAS`-2024 — NOT-YET in, NOT-YET out — while pushing every C8
   class-year further over budget and leaving C3c where it was. The owner's standing formula
   (*structural integrity improves but gates regress may still be a keeper*) does not reach
   it: **structural integrity does not improve here, and the gates do not net improve
   either.**

**Nothing about (1) is a reason to have skipped the run.** The bound it produces is real and
new: **a pure level lever CAN put all three C3a years inside ±10 %, at a measured cost of one
load-bearing C1 cell and a uniformly worse C8** — and it demonstrates, with the tail numbers
beside it, that closing C3a-2025 by level is not the same as fixing the 2025 miss.

## 6. My prior, scored against interest

* **P-1 — WRONG on the 2025 leg.** Predicted pass-through 7.0–9.5 % in every year; measured
  7.23 / 7.49 / **6.82**.
* **P-2 — WRONG, and it was the decisive one.** Predicted C3a-2023 EXITS the band in
  [+8.5, +11.5]; measured **+8.402, inside**. The owner's premise survived my objection.
* **P-3 — substantively RIGHT, band missed by 0.31 pp** (predicted [−6.0, −3.0], measured
  −6.313).
* **P-4 — RIGHT on its bar** (C3b worse in 2 of 3) **and wrong on its reasoning for 2025**,
  where shape improved 0.180 → 0.149.
* **P-5 — RIGHT.** C3c hours rise by ≤ 5 in every year (3→3, 7→7, 0→1) and the criterion does
  not flip to PASS.
* **P-6 — WRONG on the cell, RIGHT on the class of risk.** I predicted no C1 band exit and
  named `CC_REGULAR`-2024 as the danger; `CC_REGULAR`-2024 moved the safe way and
  **`ST_GAS`-2024 exited instead**. The largest class-year |Δ| is 1.578 TWh, inside my
  predicted < 3.0.
* **P-7 — held.** P(proposed as keeper) = 0, and it is not proposed.

## 7. Reported against interest

1. **The owner was right and I was wrong on the number that decides the premise.** All three
   C3a years fit inside ±10 %. My PREREG §3 arithmetic assumed a full pass-through and
   therefore concluded there was no room; the measured pass-through is ~7 %, and there is.
2. **The C3a-2025 gain is real, not an artefact.** −12.297 → −6.313 on a load-bearing
   criterion. Anyone weighing rule 1 against the board's only standing failure should weigh
   that number, not a caricature of it.
3. **The exit that stops it is 0.030 TWh past the line.** `ST_GAS`-2024 lands at −8.030
   against a ±8.00 band. A smaller scale factor would very likely keep it inside — this
   finding does **not** sweep for that factor, because sweeping a scalar against the gates is
   precisely the fitting rule 1 forbids, and doing it would convert a bounded diagnostic into
   the thing the PREREG said it must not become.
4. **C3b-2025 improved.** The shape criterion got *better* in the year the level lift was
   aimed at, which cuts against the "it just raises an already-high median" reading for that
   specific year, even though the Jun–Jul median statistic behind that reading
   (miso-202/203) is unchallenged.
5. **This probe consumed a top-15 MISO dashboard slot** and one ~65-minute solve. It bought a
   bound, not a keeper.

## 8. Governance

Rule 15 `[R-DASHBOARD]`: registered as `2026-09-05-miso-218-levelscale-probe` in this
session, with its attestation (written so the run could be **scored** — without it C6 reads
UNATTESTED and guard (b) of the C3c standing rule blocks reclassification, the trap miso-217
documented). Rule 13 `[R-MEASURED]`: explicitly labelled, default-off by construction (no
field exists to arm), never enabled in a keeper, never quoted as evidence of skill. Rule 1
`[R-STRUCT]`: disposition declared before the solve and unchanged by the result. Rule 21
`[R-DOF]`: ledger 41/2 unchanged — the probe mints nothing. Rule 24 `[R-REGISTRY]`: no new
tunable; the scale is recorded verbatim in `run_config.json` via the existing operator
channel. Rule 28c: not engaged (no field added). Rule 22: 2023–2025 only. Rule 12/16: three
years sequential in one in-session invocation, never on CI. **The keeper does not change on
this session's authority.**

Next shorthand: **miso-219**.
