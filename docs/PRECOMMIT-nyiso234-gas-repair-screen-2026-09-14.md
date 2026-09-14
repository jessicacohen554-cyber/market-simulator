# PRECOMMIT — nyiso-234: rule 29 screen of the repaired NYISO delivered-gas series

**Session** nyiso-234 · **Date** 2026-09-14 · **Keeper under test**
`2026-09-13-nyiso-232-st-gas` (bundle `results/calibration/nyiso232_deleak_span`), **UNCHANGED**.
Written and pushed **BEFORE the screen solves**, per rule 29 `[R-SCREEN]` (1).

Evidence this rests on: `docs/FINDING-nyiso234-tail-gas-is-unobserved-2026-09-14.md` (the object),
`docs/FINDING-nyiso234b-the-gas-series-was-published-2026-09-14.md` (the cause and the repair),
`docs/DECISION-CARD-nyiso234-tail-gas-coverage-2026-09-14.md` (the owner ruling of 2026-09-14,
*"Yes to 1 and 2"*, funding the intake).

---

## 1. WHAT IS BEING SCREENED — an INPUT repair, not a mechanism

**Zero `ScenarioConfig` fields change. No flag is added, armed or flipped. The DOF ledger is
untouched and there is no `authorized_price_tuning` block.** What changes is the content of two
committed raw artifacts and one derived from them, all through the repo's own documented fetchers:

| artifact | change | producer |
|---|---|---|
| `data/raw/gas-prices/transco_z6_ny_daily.csv` | +129 rows, 9 corrected, 3 holiday rows removed | `fetch_transco_daily_spot.py` (repaired) |
| `data/raw/gas-prices/transco_z6_iroquois_monthly.csv` | monthly means recomputed from the completed dailies | `fetch_nyiso_gas_narrative.py` |
| `data/raw/gas_basis_by_iso_month.csv` (NYISO rows only) | Iroquois monthly − Henry Hub monthly | `fetch_nyiso_gas_narrative.py` |

This is a rule 14 `[R-ACCURATE]` input correction and a rule 23 `[R-FROZEN-DERIVE]` re-derivation
**cited to a source-coverage and source-alignment defect, never to a residual**. Under rule 14 a
worse fit is explicitly **not** grounds to revert it: *"keep the accurate input, find and fix the
real root cause."*

## 2. THE SCREEN YEAR, AND HOW IT WAS CHOSEN

**Screen year: 2022.** Chosen on the **mechanism's own measured footprint** — the summed absolute
change in the delivered gas series the LP actually sees — and **never on the residual**, per rule 29
(1). Measured zero-LP by `scripts/probes/_nyiso234_gas_repair_footprint.py`:

| year | footprint (Σ&#124;Δ&#124; $/MMBtu·h) | hours moved | max Δ |
|---|---:|---:|---:|
| **2022** | **3,983** | 1,464 (16.7 %) | **+31.57** |
| 2025 | 1,354 | 2,928 (33.4 %) | +0.97 |
| 2024 | 1,069 | 3,672 (41.9 %) | +7.91 |
| 2023 | 597 | 3,600 (41.1 %) | +0.71 |

**2022 leads by 2.9×.** These are the FINAL figures over the complete repair — both the daily
series and the monthly anchor recomputed from it — measured before the screen and unchanged in
ordering from the daily-only reading that first selected 2022 (3,961 / 2,100 / 988 / 669, a 1.9×
lead). **No amendment to the screen year was needed.**

*Measurement note, recorded because it changed a number this document relies on:* the monthly level
enters `_nyiso_hub_daily_gas_prices` through its **`basis_path` argument**
(`gas_basis_by_iso_month.csv`), **not** through `basis.nyiso.TRANSCO_IROQUOIS_MONTHLY_PATH`.
Repointing that constant was measured to be a **no-op** (0 of 8,760 hours), which would have
compared a HYBRID baseline — old dailies against the new monthly level. The probe was corrected to
swap the argument, verified effective (1,464 hours move on a basis-only swap), and the table above
is from the corrected run. The hybrid reading had given 2022 = 4,798; the ordering was the same,
but the number was measuring the wrong thing and is not quoted.

The 2022 days that move most, and what the model burned on them:

| date | before | after |
|---|---:|---:|
| **2022-12-23** | 8.05 | **39.62** |
| 2022-12-22 | 8.05 | 35.73 |
| 2022-12-24 | 8.05 | 31.46 |
| 2022-12-25 | 8.05 | 23.31 |
| 2022-12-29/30/31 | 8.05 | 3.66 / 3.08 / 3.08 |

The late-December days moving **down** is the monthly recomputation working as intended: their own
published prints are 3.29 / 2.77, and the daily-only repair had pushed them to **2.53** by funding
the spike out of the rest of the month. That over-correction is what §1's second step removes.

**2022 is ALSO the worst C3a year (−11.6 %), and that is a coincidence this document names rather
than relies on.** The choice is made on footprint alone; had the largest footprint fallen in a
passing year, the screen would have gone there. Nothing below reads C3a.

## 3. THE GATES — STRUCTURAL, AND A STOP GATE ONLY

Rule 29: the screen asks whether the mechanism does what its own arithmetic says. **It may kill the
arm; it may never promote one.** None of these reads the target residual.

| id | gate | STOP condition |
|---|---|---|
| **G-1 FOOTPRINT CONFINEMENT** | the delivered gas array changes **only** on dates the repaired CSV touches | any hour outside the touched dates moves by > 1e-6 $/MMBtu |
| **G-2 DIRECTION** | on the recovered Elliott days the delivered gas **rises**, and system price rises with it | gas falls on Dec 22–23, or load-weighted price on those days does not rise |
| **G-3 ORDER OF MAGNITUDE** | the Dec 22–23 price response is consistent with the pre-solve Δmc, bounded above by the dual-fuel oil-parity cap ($24.85/MMBtu, measured) | price response exceeds what Δmc × heat rate admits, i.e. the LP is amplifying rather than repricing |
| **G-4 NO STRUCTURAL BREAK** | slack and dump stay at zero; the solve is feasible in every hour | any VOLL load-shed hour or dump appears that the control did not have |
| **G-5 IDENTITY** | annual gas burn and fuel mix move only through the re-priced hours — no class appears or vanishes | a plant class's annual energy moves by > 10 % with no Δmc to explain it |

**G-4 is the one most likely to fire and it is the reason the screen exists.** Raising downstate
gas to $32–36/MMBtu could push the LP into shedding load if the fleet cannot cover; that would be a
structural failure of the arm, not a better fit, and it stops the arm.

## 4. WHAT IS EXPLICITLY *NOT* A GATE

* **C3a, C1, C3b, and every other criterion.** They are **reported at full magnitude in the RESULT
  and gate nothing here.** Gating a screen on the target residual is the fitted-mechanism selection
  rule 1 `[R-STRUCT]` forbids, done one year at a time.
* **"Did the tail improve."** Same reason.
* **A worse C3a is NOT a STOP.** It is the *predicted* direction: nyiso-232 established NYISO's C3a
  is a difference of two large errors of opposite sign, and nyiso-234 §3 established that this
  repair raises the tail with no compensating re-level onto ordinary hours. So the headline may
  move against us while the model gets more truthful. That is rule 14's case, stated in advance so
  it cannot be constructed afterwards.

## 5. THE CONTROL — rule 29(b) form 4, no control solve

**The incumbent keeper's committed bundle IS the control** (`nyiso232_deleak_span`, all four years
on `main`). No control solve is spent.

**G-DRIFT** (the code-level drift audit form 4 requires) is trivially satisfied here and is stated
rather than assumed: the arm's diff against the keeper's `git_sha` on the solve path is **this
session's commits only**, and they are (a) `scripts/data/fetch_transco_daily_spot.py` — a
**fetcher**, never imported by the solve path; (b) `scripts/audit_keepers.py` — a **scorer-side
audit**, never imported by the solve path; (c) probes and docs; (d) the three raw data artifacts of
§1, which are **the arm itself**. **Zero LIVE hunks in `src/market_sim/`.** The only thing that
moves between control and arm is the data under test, which is exactly what form 4 requires.

## 6. EXECUTION

Rule 32 `[R-SHARD]`: **the parent runs zero LP.** The screen is one shard, one year (2022), pinned
to this document's commit SHA, pushing its bundle per rule 34 `[R-SHARD-PROMOTABLE]` (a) so the
result can back a promotion without a re-solve.

**If the screen clears**, the full span is ONE shard, ONE `--years 2022 2023 2024 2025`
invocation, ONE bundle (rules 16 / 32(b)) — the screen year re-solved inside it.

**If the screen STOPS**, that is the session's result; the remaining years are never spent, and the
repaired input still stands on rule 14 with the structural failure reported as the open root cause.

## 7. WHAT THIS DOCUMENT COMMITS TO IN ADVANCE

1. The screen year is **2022**, chosen on footprint, fixed before the solve.
2. The gates are **§3 as written**; none will be re-cut after seeing a number, and a STOP will not
   be rescinded by this session.
3. Every criterion movement is **reported at full magnitude** in the RESULT, including ones that
   look bad, and **none of them is a gate**.
4. **No offer-curve band multiplier, adder, haircut or scalar is touched.** If the repaired input
   makes a criterion worse, the answer is an open root-cause issue — never a compensating tune.
