# FINDING — SPP-57b: the Oklahoma pocket with the constituent sets re-declared — the rule-29(a) screen (2025) KILLED at the pre-registered STOP gate; topology NOT landed

**Lane** SPP-57b · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-57b-oklahoma-pocket-973wcd` (stem `claude/spp-57b-oklahoma-pocket-sets-h3km`) ·
**PRECOMMIT** `PRECOMMIT-spp-57b-2026-09-07.md` (pushed at `42ed8ff6` before any number of this lane was derived
or solved) · **Data profile** `spp` · **Control** keeper-2 `2026-09-07-spp-2-crosswalk-hydro` /
`results/calibration/spp42_crosswalk_B` (rule 29(b) form 4; G-DRIFT PRECOMMIT §0.1, all hunks INERT for 2025) ·
**LP spent:** ONE year (2025), the rule-29(a) screen. The screen bundle `results/calibration/_spp57b_screen` was
**deleted before the PR** (rule 29(c)); every number this lane will ever cite from it is here and in
`docs/handoffs/spp57b/grade_screen_2025.log` / `flows_at_ratings_2025.log`.

---

## 0. Bottom line — the STOP-gate table first

| leg | quantity, 2025 | **SPP-57b arm** (N↔OK 3,400 / OK↔S 10,700) | SPP-57 arm (6,500 / 6,700) | control keeper-2 (N↔S 3,400) | threshold | verdict |
|---|---|---|---|---|---|---|
| (i) N↔OK | at bound; named-direction share | **2,061 h (23.5 %)** — 1,920 N→OK / 141 OK→N; **93.2 %** N→OK | 215 h (2.5 %); 100 % | N↔S 1,573 / 228 h (20.6 %) | ≥ 5 % live; ≥ 55 % named | **pass** |
| (i) OK↔S | at bound; named-direction (OK→S) share | **0 h (0.0 %)**; flow range −6,211 … +3,133 MW | 0 h | — | same | **STOP (liveness)** |
| (ii) OK − N | model annual mean vs measured sign | **+1.77** (mean \|·\| 1.91, p90 5.81) vs +0.15 | +0.08 | \|S−N\| 1.35 | sign | pass |
| (ii) S − OK | model annual mean vs measured sign | **0.00** exactly (a never-binding link → identical duals) vs **+11.29** | 0.00 | — | sign | **STOP (sign)** |
| (iii) re-curtailment | 1 − delivered / potential | **0.00 %** (122.25 / 122.26 TWh) | 0.00 % | 0.0 % | > 0 | **STOP** |
| (iv) unserved | slack hours ⊆ {h8507} | **444.3 MWh in 2 h — h8507 243.0 + h8508 201.3, `SPP-South`** | 0 | 89.3 MWh, h8507 | ⊆ {h8507} | **STOP (new hour h8508)** |
| (v) fuel families | TWh vs reference, [0.1×, 10×] | coal 1.08 / CC 0.77 / CT 4.46 / ST 0.97 / nuclear 0.97 / wind 1.11 / solar 1.00 — every family with a real actual in band; hydro 8.82 vs the reference's EIA-923-preliminary **0.02** (SPP-57 R-15, a scorer-side vintage defect, stated in the PRECOMMIT as NOT a miss) | same shape | same | in band | pass |

**KILLED on legs (i) OK↔S, (ii) S−OK, (iii) and (iv).** The correction worked exactly where SPP-57 §5.3 said it
would — the corridor-only N↔OK link at 3,400 MW is live 23.5 % of the time and 93 % in the measured-dominant
N→OK direction, against the union-rated 2.5 % — and it did not, and by this construction cannot, rescue the second
link: the `sps_tie` set identifies **only OK→S-loaded** constituents (4 of 7, 6,177 h; zero S→OK), so the
FCITC rule names the link OK→S and rates it 10,700 MW, while the bubbles' own flow on that link runs the
**other way** in every percentile above the median (p50 −1,188, p10 −3,140, p1 −4,682 MW = S→OK; the OK→S flow
never exceeds +3,133 MW). An OK→S-named link therefore cannot be live in its named direction at ANY rating
≥ 3,400 in this solve (§3.3) — the second link is **directionally misaligned with the residual bubble**, not
merely too wide. That is the structural result of this lane, and it routes to SPP-54 (§7 R-17), not to a third
rating.

**Owner question (the standing P14/P15 rule — "if structural integrity improves but gates regress that may
still be a keeper"): NO candidate.** One link improved from inert to live-and-correctly-directed; the other
stayed inert; the pocket traps nothing (re-curtailment 0.00 %, negative-price hours 4 vs the keeper's 6 and
~1,018 measured); and unserved energy rose from 89 to 444 MWh. Against the two-zone keeper, whose single 3,400
link already binds 20.6 % of hours N→S-dominant, the arm's live link is the same object under a new name plus
an inert pipe and a copperplate residual. Nothing to promote; keeper-2 stands.

---

## 1. What ran (rule 29, in order), and what it cost

| step | what | LP | result |
|---|---|---|---|
| 0 | PRECOMMIT pushed `42ed8ff6` (pin `dcb609f4`; G-DRIFT keeper-2 `33034499` → HEAD: 9 hunks, all INERT for a 2025 backcast; the SPP-41 wind screen LIVE for 2023 only) | none | before any derivation |
| 0 | `git checkout f5926636 -- <17 solve-path files + 3 CSVs>` (exact bytes; main had not moved them since `91b5d6fb`); the two `ttc_mw` values, their citation comments, the pinned test and `iso-topologies.json` edited; design commit `7bfe047d` | none | §2, §4 |
| 0 | `aggregate_ttc_57b.py` on SPP-57's committed tables — the two ratings under the re-declared sets, both directions, LOYO, R1–R4 | none | §2 |
| 0 | `validate_topology()` OK; ruff clean; 169 tests green (the five SPP files + `test_persisted_identity.py`); `solve_surface_register --diff origin/main HEAD` **297 → 297, 0 moved** on the committed arm; `run_year(fleet_only=True)` census × 3 years | none | §4 |
| 1 | **screen 2025**: `run_calibration_full.py --iso SPP --year 2025 --out-dir results/calibration/_spp57b_screen --hydro-backfill-year 2024 --hydro-eia930-monthly` (keeper-2's recipe + the topology) | P0 **108.0 s** cold (103,507 it., obj −238,159,367.6), P1 **35.9 s** warm (18,110 it., obj −159,605,223.8); phases data_prep 14.3 / markup 27.3 / results 26.2 s; **211.9 s total, 4.93 GB peak RSS** | **KILLED** (§0, §3) |
| 2 | full span | **not spent** | — |

Rule 12: no other per-plant solve ran in this container (SPP-43 runs in its own). Memory class for the `spp`
profile at three zones: `per_plant=True, co_opt=False, peak_gb=4.9`.

---

## 2. Design (B′) as executed — the two ratings under ONE flowgate group each

Construction, sets, exclusion rule and direction convention exactly as PRECOMMIT §3 declared; instrument
`docs/handoffs/spp57b/aggregate_ttc_57b.py` (+ `.log`, `tstar_n_ok_57b.csv`, `tstar_ok_s_57b.csv`), which reads
SPP-57's committed per-constituent tables and LOYO ψ columns and re-fits nothing (rule 23).

### 2.1 N↔OK — `n_s_corridor` alone = SPP-53's number, unchanged

30 corridor constituents ≥ 263 h; **12 forward-identified (9,254 h), 7 reverse (3,767 h)** → named **N→OK**;
weighted median T* = **3,355 → 3,400 MW** (Franklin 161/69 kV, 4,103 h, 100 MW / ψ 0.0298), weighted p25 / p75
3,355 / 6,437 (**1.92×**); reverse (OK→N) reading **4,206 → 4,200** (p25 / p75 3,025 / 21,937). R1 12 ≥ 3, R2
3,400 < 23,300, R3 < 37,400, R4 1.92 ≤ 10 — all pass. The 37 excluded `oklahoma_internal` rows: **25 of 37
carry |t| ≥ 2 on this spread** (the exclusion rule's coverage, PRECOMMIT §3.1). LOYO as SPP-53 reports it
(2,645 / 3,681 / 11,121, drop 2025 / 2023 / 2024); this instrument's plain re-division reproduces 3,681 and 11,121
and reads 1,510 for drop-2025 (n = 11: one constituent's LOYO ψ is 0 and drops), the difference being SPP-53's
re-identification rule on the LOYO fit — reported, immaterial, the rating is SPP-53's committed value.

### 2.2 OK↔S — `sps_tie` alone: the T* table

| constituent | monitored facility | pooled h | ψ on (p_S − p_OK) | t | L_f (MW, source) | T* | identified |
|---|---|---:|---:|---:|---|---:|---|
| `TEMP50_23126` | Potter County 345/230 kV xfmr | 2,231 | +0.0473 | 2.54 | 505.9 (2026 archive, same Monitored Facility, 9,823 intervals) | **10,705** | fwd (OK→S) |
| `TMP555_29231` | Potter County 345/230 kV xfmr | 1,638 | +0.1321 | 3.50 | 508.7 (2026 archive, same Constraint Name) | 3,850 | fwd |
| `TMP200_25341` | Potter County 345/230 kV xfmr | 1,421 | +0.0049 | 0.21 | 503.1 | — | no |
| `SPSNMTIES` | multi-element (ITP interface) | 1,211 | +0.0892 | 2.35 | 1,018.0 (2026 archive) | 11,409 | fwd |
| `SPPSPSTIES` | multi-element (ITP interface) | 1,097 | +0.2826 | 2.36 | 1,018.0 | 3,602 | fwd |
| `TMP775_29068` | Potter County 345/230 kV xfmr | 762 | −0.0061 | −0.13 | 508.7 | — | no |
| `TMP703_28546` | FPL Switch – Woodward | 411 | −0.0061 | −0.17 | 119.2 | — | no |

**Forward (OK→S): n = 4, 6,177 h, weighted median T* = 10,705 → 10,700 MW**; weighted p25 / p75 3,850 / 10,705
(**2.78×**); unweighted median 7,278; LOYO **8,395 / 10,490 / 14,796** (drop 2023 / 2024 / 2025).
**Reverse (S→OK): no identified constituent** — R1 fails in that direction (0 < 3), so the reverse reading is
"none". Named direction **OK→S** (6,177 h vs 0). R1 4 ≥ 3 pass; **R2 10,700 < 11,085 pass (by 3.5 %)**; R3
< 24,383 pass; R4 2.78 ≤ 10 pass. The 47 excluded rows (`oklahoma_internal` + CSWS-only `other`): 24 carry
|t| ≥ 2 on this spread.

**The charter's expectation ("order 3,000–4,000") was wrong, as PRECOMMIT §3.2 disclosed before the run:** the
weighted median lands on the most-binding constituent, the Potter County constraint with the smallest ψ, not on
the two ~3,600–3,850 readings. The rule decided; the number was not re-cut. Two things about this table are the
identification's own width, stated not absorbed: the same Potter County transformer carries two constraint
names whose ψ differ 2.8× (0.047 vs 0.132 → 10,705 vs 3,850), and the 2025-only fit moves the median to
14,796 (SPP-57 R-14 → SPP-58).

### 2.3 What the three-point spread says about the direction (reused, design C)

The residual South reads DEARER than the Oklahoma hub on every annual mean (S−OK +1.15 / +3.42 / **+11.29**),
and the SPS ties bind on imports INTO the Panhandle (ψ > 0 on p_S − p_OK), so the market names the interface
OK→S-loaded. §3.3 shows the model's residual bubble does the opposite.

---

## 3. The screen, graded as written (PRECOMMIT §4; `grade_screen_2025.log`)

### 3.1 Beside the legs (reported, never gated)

Load-weighted price **$30.54** (control $29.97; measured RT $27.11 / DA $28.72); zone means N 29.11 / **OK 30.88 /
S 30.88** (identical — the OK↔S link never binds, so the two duals coincide in every hour); negative-price hours
**4** (all North; control 6; measured ~1,018); hours > $200 **2** and > $1,000 **2** (the VOLL hours h8507–h8508,
price 2,000.00 in OK and S); range −26.00 … 2,000.00. By class, arm vs control (TWh): CC_REGULAR 29.16 vs 32.57
(**−3.41**), ST_GAS 11.98 vs 9.83 (**+2.15**), COAL_PRB 77.76 vs 77.17 (+0.59), CT_PEAKER 22.82 vs 22.35
(+0.47), COAL_LIGNITE 6.22 vs 6.03 (+0.19); wind / hydro / nuclear / solar identical (122.25 / 8.82 / 15.78 /
2.35). The pattern is the same as SPP-57's arm: a copperplate OK+S region lets Oklahoma's steam and North coal
displace CC.

N↔OK's 1,920 N→OK at-bound hours run through the whole year (by month 249 / 203 / 164 / 191 / 146 / 187 / 105 /
169 / 206 / 99 / 34 / 167) and all hours of the day (58–99 h per hour-of-day); the 141 OK→N hours concentrate in
Nov–Dec (25 / 72). Model OK−N monthly means +0.1 … +6.4 (Dec widest), against a measured 2025 signed mean of
+0.15 with |·| 15.18 — the link binds, but the two bubbles still hold only ~1/8 of the measured separation.

### 3.2 Why each STOP is a kill and not a tie (E-6)

(i) OK↔S: 0 h against 5 % — not within rounding. (ii) S−OK: identically zero by construction. (iii) 0.00 %
exactly, the gate's literal condition — the N→OK pipe binds 1,920 h yet no North wind is re-curtailed, because
the North's 12–29 GW load absorbs its own 17.7 GW of wind and the bound pipe re-orders thermal (coal +0.8 TWh,
CC −3.4) rather than trapping wind. (iv) h8508 is a NEW unserved hour (201.3 MWh) and h8507 rose 89.3 → 243.0
MWh; both in the residual South while OK↔S carries −1,749 / −1,932 MW (S→OK) and N→OK sits at 3,400 — i.e. the
whole OK+S region behind the 3,400 pipe is short, and the LP places the slack in either VOLL zone. Demand in
those hours is identical to the keeper's South (18,596.6 MW = 11,246.8 + 7,349.8), the pipe is the same 3,400,
and system wind is identical (17,472 MW), so the extra 355 MWh is the OK+S region's own generation being lower
in those two hours under the three-zone inputs — attributed to the per-zone wind-shape rebuild (six NASA POWER
sites per zone; the redistribution identity holds at the system level, not per region), not measured per zone
here. Reported at full magnitude; routed (§7 R-18).

### 3.3 What the screen's own flows say — reported, never a re-cut (`flows_at_ratings_2025.log`)

| rating | N↔OK at/over bound (N→OK / OK→N) | OK↔S at/over bound (OK→S / S→OK) |
|---|---|---|
| 3,400 | **2,061 (1,920 / 141)** — SPP-57's killed screen read 2,065 (1,931 / 134) at this rating | 638 (**0** / 638) |
| 4,000 | 0 | 282 (0 / 282) |
| 4,500 | 0 | 122 (0 / 122) |
| 5,000 | 0 | 55 (0 / 55) |
| 6,000 | 0 | 3 (0 / 3) |
| 6,500 – 10,700 | 0 | 0 |

Flow percentiles: N↔OK p1 −3,400 / p10 −1,349 / p50 +1,527 / p90 +3,400 (the link IS the bound); OK↔S p1 −4,682 /
p10 −3,140 / p50 −1,188 / p90 +781 / p99 +2,183, min −6,211, max **+3,133**. Two readings, neither a number to
pick: (a) the corridor-only N↔OK rating is confirmed live and N→OK-dominant in a solve where the second link is
open — the union-rated 6,500 was the whole reason SPP-57's first link died; (b) **no OK→S-named rating ≥ 3,400
can be live in its named direction in this model**, because the residual bubble exports into Oklahoma (mean
−1,182 MW, S→OK) in every hour above the median — the identified loading (imports INTO the Panhandle) and the
bubble's flow point opposite ways. A link rated ~3,400 would be live (7.3 %) but 100 % S→OK, failing the
direction leg against its own identification.

---

## 4. Designs (A), (C), (D) — reused; proofs; census

Reused verbatim from `f5926636` (rule 23): the CSWS split **w_OK 0.5216 / 0.5383 / hold-last 0.5383**
(EIA-861 PSO / (PSO + SWEPCO)); static shares N 0.5125 / OK 0.2830 / S 0.2045; the three-point spread, both ψ
regressions, the L_f table, the registries, sidecars, wind shapes, reference block, tests. Proofs at the
design commit `7bfe047d`: `validate_topology()` OK; **`solve_surface_register --diff origin/main HEAD` 297 → 297,
0 moved** (rule 25 — no other ISO's key reached); `test_persisted_identity.py` green (the SPP plain-backcast key
`989da50bbf0f99d8` unmoved by the D76-ARM-B flip, PRECOMMIT §0.1 #5); 169 SPP-touching tests green; ruff clean.

`run_year(fleet_only=True)` census on keeper-2's recipe (`spp57b/census.py`, `census.csv`), 2025:

| zone | plants | LP units | thermal + hydro MW | wind cap MW / potential TWh | solar MW | demand TWh (min–max MW) |
|---|---:|---:|---:|---|---:|---|
| SPP-North | 223 | 810 | 30,217 | 17,664 / 64.03 | 596 | 153.94 (12,131–29,509) |
| SPP-Oklahoma | 42 | 170 | 16,269 | 13,146 / 40.18 | 423 | 86.60 (6,693–16,702) |
| SPP-South | 35 | 142 | 12,841 | 4,654 / 18.05 | 422 | 61.31 (5,153–11,135) |

2024 and 2025 rows are **byte-identical to SPP-57's `census.csv`**; the 2023 rows differ in the wind-potential
column only (North 56.419 → 56.404, Oklahoma 38.983 → 38.973, South 18.681 → 18.678 TWh; −29.6 GWh in total) —
the SPP-41 unit-slip screen on the 2023 delivered wind profile, i.e. G-DRIFT hunk 6 LIVE in 2023 and inert in
2024/2025, reproduced by the census exactly as the PRECOMMIT declared it.

---

## 5. LOYO, DOF, and what was not done

- **LOYO (rule 22):** not spent — no full span. The identification's own leave-one-year-out width is in §2
  (N↔OK per SPP-53; OK↔S 8,395 / 10,490 / 14,796).
- **DOF ledger (rule 21):** as expected — the CSWS split is a MEASURED value, both TTCs are measured
  constructions (two legs each), **zero tuned scalars**; no band, floor, adder or scarcity term. Nothing moved
  after the result.
- **Not done, by rule:** no re-cut of either rating (the OK↔S link at ~3,400 would be live — and would fail the
  direction leg; rule 29 forbids picking the rating that makes a leg pass, and rule 1 forbids reaching a
  number through a construction the data does not name); no set change after a number was seen; no full span;
  no registration; no keeper change; no second screen (a second arm is a new PRECOMMIT).

---

## 6. What is landed, what is reverted, and the proofs

**Landed (the record):** `docs/handoffs/PRECOMMIT-spp-57b-2026-09-07.md`, this FINDING,
`docs/handoffs/spp57b/` (`aggregate_ttc_57b.py` + log + the two `tstar_*_57b.csv`; `census.py` + `census.csv` +
log; `grade_screen.py` + `grade_screen_2025.log`; `flows_at_ratings.py` + `flows_at_ratings_2025.log`;
`screen_2025_solve.log`), `docs/calibration-log/spp.md` spp-5, the plan §5 / ledger rows, the SPP matrix shard
(`measured_interface_limits` evidence appended; cell stays O).

**Reverted on the branch (solve path byte-identical to `origin/main` `dcb609f4`):** the 17 solve-path files +
the three SPP renewable-capacity CSVs of the design commit `7bfe047d`, restored with `git checkout origin/main
-- <files>` (exact bytes, rule 27), never rewritten. Why revert rather than land, as SPP-57 §7 ruled: the
keeper's topology is the keeper's structure; a killed arm's topology on `main` would silently change every later
SPP lane's zones while the keeper it is scored against has two, and no `ScenarioConfig` gate is permitted (G8).
The complete three-zone implementation under construction (B′) is this branch's design commit **`7bfe047d`**
(SPP-57's is `f5926636`); a re-issue cherry-picks whichever it needs.

**Proofs at the final commit:** `solve_surface_register --diff origin/main HEAD` 0 moved; persisted identity
green; the SPP test files green; `check_registry_payload_parity` clean (the screen bundle is gone);
`check_mechanism_matrix --base origin/main` clean; `audit_keepers --iso SPP` PASS; ruff clean. Rule 22: 2025
only, training tier; no marker touched. Rule 27: no file ≥ 300 lines is changed against `origin/main` at the
final commit (the solve path is restored to its bytes); the pushed docs are fetch-back verified.

---

## 7. Routed (not absorbed) — and the recommendation

| # | item | owner |
|---|---|---|
| R-17 | **The second link is directionally misaligned with the residual bubble, and no rating fixes that.** The `sps_tie` set identifies only OK→S-loaded constituents (the ties bind on imports INTO the Panhandle; the residual South is dearer than the Oklahoma hub on every annual mean), while the model's residual bubble — SPS's 4.65 GW of wind + SWEPCO's AR/LA/east-Texas thermal against a 5–11 GW load — EXPORTS into Oklahoma in every hour above the median (§3.3). The object is the one PRECOMMIT-spp-57 §1 item 2 named: two physically disjoint pockets joined by a copperplate, so SPS wind serves Louisiana load at zero cost and the composite reads as a surplus zone the market never sees. The Oklahoma pocket cannot be completed as a chain until the residual is split — SPP-54's design should start from this lane's §3.3 flow table and SPP-57's R-13 spread table, and its SPS↔Oklahoma link may then use the `sps_tie` set (OK→S-named, 10,700 by this rule; ~3,600–3,850 on the two ITP-interface constituents) against a bubble whose flow direction matches the identification | SPP-54 (re-ranked above any further SPP-57 re-issue by this evidence — desk act) |
| R-18 | The three-zone inputs raise the residual South's unserved energy from 89 MWh (1 h) to 444 MWh (2 h) at identical demand, identical pipe and identical system wind (§3.2): the OK+S region's own generation in h8507–h8508 is lower under the per-zone wind-shape rebuild. A per-zone wind reconciliation of the rebuilt `spp_2025_wind_zone_shape.parquet` against the EIA-930 SWPP profile in the Dec-21 stuck-demand window (the P9-class item keeper-2's note already routes) belongs to whichever lane next carries three zones | SPP-54 / SPP-DESK |
| R-19 | The corridor-only N↔OK rating (SPP-53's 3,400) is now confirmed live and N→OK-dominant in TWO independent solves (2,065 h in SPP-57's, 2,061 h here) as the North↔Oklahoma capability; the standing asymmetric-pair question (S→N / OK→N reading 4,200) is unchanged and stays SPP-58's | SPP-58 |
| R-20 | The hub-pair ψ identification's width on the SPS tie: one transformer, two constraint names, ψ 0.047 vs 0.132 (T* 10,705 vs 3,850); LOYO 8,395–14,796. SPP-58's independent shift-factor identification is the fix; SPP-54 should not rate its SPS link on this table without it | SPP-58 |

**P15 recommendation: no candidate to serve.** Nothing is registered; keeper-2 stands; the topology is not
landed. Lever-queue recommendation to the desk: SPP-54 (split the residual) ahead of any third Oklahoma-pocket
re-issue, because R-17 is a bubble-composition defect that no link rating on the current three bubbles can
reach; then SPP-51 / SPP-58 as ranked.
