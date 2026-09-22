# RESULT — hydro-1: hydro dispatch physics, PJM + NYISO (in progress, 2026-09-22)

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
