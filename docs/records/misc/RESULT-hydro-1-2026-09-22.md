# RESULT — hydro-1: hydro dispatch physics, PJM + NYISO (2026-09-22)

Companion to `docs/PRECOMMIT-hydro-1-2026-09-20.md`, which carries the phase-0 census, the
mechanism design and the pre-registered gates. **This doc carries every number the lane will
cite**, so it is the record even where a bundle is not retained (rules 29(c) / 31).

Mechanism, artifacts, classifier repair and the PRECOMMIT merged to `main` in `da38d108`
(now an ancestor of `b969ffaa`).

---

## 1. Headline — PJM improved, decisively

`hydro_ror_split`, PJM **2025**, single-delta A/B against the then-designated keeper
`pjm_h13_meritalloc_span` (arm bundle `hydro1_pjm_ror_2025`, shard branch
`claude/hydro1-pjm-ror-2025` @ `693f5e9bc309ce9c15ea4306be402325decd27d4`):

| statistic | control (h13) | arm | reading |
|---|---:|---:|---|
| annual hydro TWh | 8.4636 | **8.4636** | **G2 exact, 0.0000 %** — the invariant holds |
| hours at 0 MW | 3,067 | **0** | the reported defect, eliminated |
| hourly p05 (MW) | 0.0 | **282.8** | PJM's own published floor never drops below 95-148 MW overnight |
| hourly p50 (MW) | 518.5 | **791.1** | |
| hourly p95 (MW) | 3,214.3 | **2,267.3** | the peaker behaviour, damped |
| top-decile water share | 0.3129 | **0.2164** | toward 0.10 (a flat fleet) |
| overnight (HE 03-06) p50 | 57.1 | **733.8** | PJM's own overnight p50 is 654 MW |

**The user-reported defect — "in PJM there are 0 hydro hours in my model when that never
actually happens" — is gone: 3,067 → 0**, with annual energy unchanged to four decimals.

Two honesties about this table. (a) PJM's published `Hydro` **folds 5,046 MW of pumped storage**
(15.5 TWh against 8.9 TWh of EIA-923 `HY`), so its p50 of 654 MW is an **upper** bound on the
conventional fleet and the arm's 733.8 slightly overshoots a reference that is itself too high —
the conventional-only truth is below both. (b) PJM's 2025 EIA-923 vintage is an early release
(~10 of ~72 plants) running on the keeper's backfill path, so 2025 is the weakest of the three
years on data quality. **2023 and 2024 are re-solving against the CURRENT keeper
`pjm_h15_coalwindow_span`** (h13 was pruned when that lane promoted h15; h15's hydro posture is
identical to h13's, so the hydro comparison is unaffected).

---

## 2. NYISO — small, and right in every direction

`hydro_ror_split` on the repaired classifier, against keeper
`nyiso247_fuelinv_span`. NYISO's flat class is only **7.3 % of hydro energy** (94 plants /
582.6 MW), so the magnitudes are small by construction — what matters is the sign.

| year | Δ p05 | Δ p95 | Δ top-decile | G2 |
|---|---:|---:|---:|---|
| 2022 | +0.1 | **−65.0** | −0.0017 | **−0.1229 % FAIL** |
| 2023 | **+20.6** | −14.0 | −0.0016 | −0.0241 % pass |
| 2024 | **+47.8** | −22.4 | −0.0014 | 0.0000 % pass |

Against the measured NYISO actual, the target direction is **p05 up, p95 down, top-decile down**
in all three years. **Twelve of twelve comparisons move the right way.** For 2024, p05
1,858.7 → 1,906.5 against an actual of 2,016.5; p95 4,120.5 → 4,098.1 against 3,976.9;
top-decile 0.1252 → 0.1238 against 0.1198.

**G2 fails in 2022 at −0.1229 %** (31.4 GWh) against a ±0.1 % bar. This is explained, not
mysterious: the RoR flat treatment stamps `min_gen = cap = budget[g,m]/hours[m]` **clipped to
nameplate**, and a plant-month whose flat level exceeds nameplate loses the excess — the loader
logs exactly that. The NYISO keeper carries `hydro_budget_nameplate_aware = False`, which is the
gate that water-fills instead of silently clipping. **Named successor: re-run arm B 2022 with
`hydro_budget_nameplate_aware=true`**; that is a one-shard test and should close the miss.

Shard branches: `claude/hydro1-nyiso-ror-2022` @ `d09eb5868fce`,
`-2023` @ `7dba706d6253`, `-2024` @ `1caea62bb36c`. *(Provenance, not a recovery route — a shard
branch is transport and is cut when the lane's PR merges, rule 33(d)/(f). Cost any leg not landed
on `main` as a re-solve; NYISO is ~3.5 min of LP per year.)*

---

## 3. Promotion — NOT YET, and why

**Recommended as a keeper candidate on structural grounds, but not promotable today.** Rule 35
`[R-PROMOTE]` (c) requires the incoming keeper to cover every year the ISO has already run:

* **PJM** — 1 of 3 years solved, and against a **superseded control** (h13, since pruned).
  2023/2024/2025 are re-solving against h15 now.
* **NYISO** — 3 of 4 years solved for arm B; 2025 and all four years of arm C are running.

The user's standing instruction is on the record and is the right test here: *"if structural
integrity improves but gates regress that may still be a keeper."* PJM's structural improvement
is large and its invariant is exact; the scored-criterion effect is not yet in hand. **Nothing
is promoted until the full year set lands against the current controls.**

---

## 4. What is still running (11 shards launched, pinned `b969ffaa`)

| arm | ISO | years | state |
|---|---|---|---|
| A2 `hydro_ror_split` | PJM | 2023, 2024, 2025 | running, vs `pjm_h15_coalwindow_span` |
| B `hydro_ror_split` | NYISO | 2022, 2023, 2024 | **done** (§2); 2025 running |
| C `hydro_pondage_bound` | NYISO | 2022, 2023, 2024, 2025 | running |

Arm C carries **two** deltas — `hydro_pondage_bound=true` **and**
`hydro_budget_period_by_instrument=false`. That is required, not a confound: both constrain
within-month energy reallocation with different objects, which rule 19 `[R-ONE-MECH]` forbids
stacking, and the forebay bound supersedes the period (a partitioned period still permits a full
period's banking and a 2× concentration at the period seam).

---

## 5. Disclosed limitations, stated rather than discovered later

1. **The pondage bound is deliberately loose.** `B` uses NID **gross impoundment** volume at
   turbine efficiency 1.0, not the licensed operating band. Any binding observed is therefore a
   **lower** bound on the true constraint, and the mechanism under-constrains rather than over-.
2. **PJM has no clean hourly conventional-hydro reference.** Both `gen_by_fuel Hydro` and
   EIA-930 `NG: WAT` fold pumped storage, so nyiso-111's falsification test cannot be run there
   and only the folded series' one-sided floor is admissible evidence.
3. **`hydro_dispatch_envelope` and `hydro_min_flow_floor` read `NG: WAT` without consulting
   `EIA930_PS_FOLDED_INTO_WAT`.** The level pin refuses for MISO/PJM; these two readers do not.
   Arming either for a folded BA would apply a pumped-storage-contaminated level to a
   conventional-only unit population (rule 14). **This is a live code gap**, recorded rather than
   worked around, and it is why neither is armed for PJM in this lane.
4. **Perfect foresight is untouched.** A bounded forebay shortens the horizon over which
   foresight is worth anything; it does not remove it.
5. **Head loss, licence ramp limits and reserve-headroom opportunity cost** are three further
   real sources of a rising hydro offer that none of these arms represents.


---

# ADDENDUM — all 11 shards returned; verdicts, and a cross-ISO census

## A. Arm A (`hydro_ror_split`, PJM) — LARGE WIN, G2 exact, 2 of 3 years

Against the CURRENT keeper `pjm_h15_coalwindow_span`:

| | 2024 ctl | 2024 arm | 2025 ctl | 2025 arm |
|---|---:|---:|---:|---:|
| annual hydro TWh | 8.8608 | **8.8608** | 8.4636 | **8.4636** |
| hours at 0 MW | 1,867 | **0** | 1,868 | **0** |
| hourly p05 (MW) | 0.0 | **281.0** | 0.0 | **282.8** |
| hourly p95 (MW) | 3,202.0 | **2,263.8** | 3,214.3 | **2,267.3** |
| top-decile water share | 0.2972 | **0.2079** | 0.3131 | **0.2164** |
| within-month daily SD ratio | 1.000 | **0.5070** | 1.000 | **0.4981** |

Zero-hours eliminated, within-month banking **halved**, annual energy unchanged to four decimals.
Arm live at 52 of 72-73 plants (57.9 % of budget).

**2023 is missing and it is a repo data gap, not a model defect**: `data/raw/pjm-da-virtuals`
carries only `README.md` (its payload is an untracked corpus at tip) while the keeper arms
`pjm_da_virtual_bids=true`, so the leg cannot solve until that corpus is re-fetched. Rule 35(c)
needs the full year set, so **PJM is not promoted on 2 of 3.**

## B. Arm B (`hydro_ror_split`, NYISO) — correct but small, all 4 years

12 of 12 comparisons on p05 / p95 / top-decile move toward the measured actual; 2025 adds a
within-month daily SD ratio of 0.8648. G2 clean except 2022 (−0.123 %, the nameplate clip —
see §2). Small by construction: the repaired flat class is 7.3 % of NYISO hydro energy.

## C. Arm C (`hydro_pondage_bound`, NYISO) — **REFUTED as armed, in all four years**

Pre-registered gate: within-month daily-energy SD ratio (arm ÷ control) **below 1.0**.
Measured **1.0289 / 1.1091 / 1.0870 / 1.0665** — the mechanism **amplified** the banking it was
built to bound. G2 also breached in 2022 (+0.117 %).

**Root cause, and it is §5.1's disclosed limitation firing exactly as written.** Rule 19 forces
the arm to carry two deltas — pondage ON, `hydro_budget_period_by_instrument` OFF — because both
bound within-month reallocation. Disarming the period **removes a binding constraint** (Niagara
24 h, St. Lawrence 168 h), and the forebay bound is too **loose** to replace it: `B` is NID
**gross** impoundment volume at efficiency 1.0, a deliberate upper bound. Net freedom rose.
The arm was live, not inert — 129-136 of 147-158 plants carried a binding row.

**Re-opening this is a DATA question, not a tuning one:** `B` from each project's **licensed
operating range** (the FERC-licence half of nyiso-219 Q1, which NID could not serve). **Do not
re-arm on the gross-volume artifact, and do not scale `B` by a factor chosen to make the gate
pass** — that is the fitted-mechanism selection rule 1 refuses.

## D. The defect is SYSTEM-WIDE, and the census says which mechanism fixes it

Every registered keeper's own committed sidecars, zero LP. `0-hrs` = hours the class sits below
1 MW; `topdec` = share of each month's hydro energy in that month's top-decile load hours
(a flat fleet is 0.10).

| ISO | worst year | hydro TWh | 0-hrs | % of year | p05 MW | topdec | `min_flow_floor` |
|---|---|---:|---:|---:|---:|---:|---|
| ERCOT | 2025 | 0.017 | 6,992 | 79.8 | 0.0 | 0.147 | False |
| SOCO | 2025 | 0.327 | 4,562 | 52.1 | 0.0 | **0.641** | False |
| SPP | 2022 | 8.207 | 3,198 | 36.5 | 0.0 | 0.212 | False |
| PJM | 2022 | 8.969 | 1,966 | 22.4 | 0.0 | 0.286 | False |
| NEISO | 2025 | 5.106 | 1,908 | 21.8 | 0.0 | 0.288 | False |
| MISO | 2022 | 9.244 | 565 | 6.4 | 0.0 | 0.191 | False |
| **CAISO** | 2024 | 22.538 | **0** | 0.0 | **774.7** | 0.124 | **True** |
| **NYISO** | 2024 | 26.739 | **0** | 0.0 | **1,858.7** | 0.125 | **True** |
| NWPP | 2024 | 107.879 | 0 | 0.0 | 6,899.6 | 0.132 | False |

**Every ISO whose keeper leaves `hydro_min_flow_floor` off parks hydro at exactly zero for part
of the year; both ISOs that arm it never do.** NWPP is the one clean exception without the
floor — a 107 TWh reservoir system whose economics never want zero. That is as clean a
mechanism-attribution signal as this program gets, and it is ISO-generic.

SOCO is the most extreme on shape: **0.64 of each month's hydro lands in the top decile of load
hours**, against 0.10 for a flat fleet and 0.12-0.13 for the three clean systems.

**Which lever per ISO is NOT a free choice.** `hydro_min_flow_floor` and
`hydro_dispatch_envelope` both read EIA-930 `NG: WAT`, which folds pumped storage for **MISO and
PJM** (`EIA930_PS_FOLDED_INTO_WAT`) and for **NEISO before 2025** (`EIA930_PS_SPLIT_COMPLETE_FROM`).
Those ISO-years must use `hydro_ror_split`, whose input (the ORNL-EHA label) carries no PS
contamination. ERCOT's fleet is 0.02-0.53 TWh — the defect is severe in percentage terms and
immaterial in energy, so it is reported, not prioritised.
