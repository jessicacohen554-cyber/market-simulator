# RESULT — UC-2-NEISO: MILP unit-commitment A/B on the NEISO backcast years (calibrated control) — **R: kill #1 (infeasible UC windows in 2021 and 2023); no control flip on the five years that solved**

**Lane:** UC-2-NEISO · **Session:** `session_01D9RZoc9NrNhUBJLcYxyJx4` (Fable) · **Date:** 2026-10-10 · **Branch:** `claude/ucmilp-2-neiso-ab-n7c2` (rebased onto `origin/main` `a49d53ec`).
**PRECOMMIT:** `PRECOMMIT-ucmilp-neiso-ab-2026-10-10.md` (pushed `26c7143d` before any shard; Addendum A = L1 gate + budget before any span shard; Addendum B = launch, kills, composition).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-10); owner: *"launch shards for other ISOs to test"*. **Pin solved:** `2f872a62a7cccadb6800555c11a73745dcdb89a4` (main at PR #7218: engine uc-1.1 + UC-1-FIX + `lean` preset; it predates PR #7224's engine-defect-4 fix, which is NYISO's import-link band and not this collision).
**LP in this session:** zero (one bench shard, seven year-isolated span shards, rule 36). **Registered:** nothing (desk ruling, E13 keeper-only); scored through a local, reverted registration (PRECOMMIT §8(d), Addendum B).

## 0. Headline

**The stage cannot yet run the NEISO span at this pin.** Two of seven year-isolated legs stopped on `UcWindowInfeasible` with an a-priori infeasible LP relaxation
(2021 window 259, Sep 17–18; 2023 window 187, Jul 7–8): the engine's own diagnostic reads *"floor above min-down"* — a kept structural floor needs more units
online than the carried min-down leaves. The only NEISO floor that pins CC_REGULAR by a temperature gate is the enabled `reliability_floor` limb *Central /
CC_REGULAR / hot day (tmax > 29.9 °C) / 49.9 % of available capacity, 24 h*; the UC's CC min-down is 6 h. This is the rule-19 stacking the PRECOMMIT named
(kept `reliability_floor` + UC min-down on the same CC units), here as an infeasibility rather than a double floor. **Kill #1 → verdict R** (PRECOMMIT §6/§7);
routed to UC-DESK and the engine lane; nothing tuned, nothing relaunched (§5.1).

**On the five years that solved (2019, 2020, 2022, 2024, 2025: 1,825 / 1,825 windows Optimal, 0 time-limit hits) the calibrated control does not flip.**
Every gated criterion stays PASS (C1, C2, C3a, C3b, C4, C8); the two C3c CAVEAT → FAIL and C6 UNATTESTED changes are the unattested-probe artefact
(magnitudes identical). But the stage moves the price body by more than the GATESPEC control bar in every year — C3a 2019 +6.8 → +0.3 %, 2020 −1.2 → −7.2 %,
2022 +2.5 → +0.2 %, 2024 +0.5 → −0.9 %, 2025 +3.8 → +2.1 % (|ΔC3a| 1.4–6.5 pp; the 1-pp bar year, 2023, is the year that did not solve) — and 2020 C3b worsens
0.111 → 0.137 (+0.026, past the §7 0.02 line). Structure: CC starts fall from 1.00–1.38× CEMS to 0.64–0.76× (the SPP overshoot again); ST_GAS starts land at
0.5–2.2× CEMS from 1.9–9.7×; the lower-tercile price error falls $0.4–1.5/MWh in every year; the ≤ $15-hour ratio barely moves; reserves stay dormant; make-whole
is 3.6–6.2 % of wholesale energy cost (bar 2 %); wall 10–31× the shard's own P0 + P1 (D-2 ceiling 3×: reported, not judged).

### 0.1 GATESPEC §6.3 gate table — control (keeper `2026-10-02-w0-neiso`, re-scored at HEAD on the same bench parts; identical to its registered record) → arm, every registered year

| year | C1 (class rows) | C2 | C3a (model/actual − 1) | C3b NRMSE | C3c (> $300 h, model / RT) | C4 gas r / NRMSE | C6 | C8 CC_REGULAR forced share (scored; MECH 28 removed) | D-2 MECH 28 share CC / ST_GAS | wall ratio | reading |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | all PASS → all PASS (CC −0.69 → −0.08 TWh) | PASS → PASS | **+6.8 → +0.3 %** PASS → PASS | 0.105 → 0.069 PASS | PASS → PASS (0 / 0) | 0.937 / 0.141 → PASS | PASS → UNATTESTED* | 0.7 → 6.5 % (0.8 %) PASS | 5.6 % / 25.4 % | **17.5** | no flip; |ΔC3a| 6.5 pp |
| 2020 | all PASS → all PASS (CC +0.52 → +1.11) | PASS → PASS | **−1.2 → −7.2 %** PASS → PASS | **0.111 → 0.137** PASS (+0.026) | PASS → PASS (0 / 0) | 0.961 / 0.117 → PASS | — | 1.7 → 4.7 % (1.4 %) PASS | 3.3 % / 35.5 % | **10.4** | no flip; |ΔC3a| 6.0 pp; C3b worse > 0.02 |
| 2021 | — | — | — | — | — | — | — | — | — | — | **kill #1** (window 259, Sep 17–18); Jan–Aug 243 windows Optimal |
| 2022 | all PASS → all PASS (CC −0.37 → −0.04) | PASS → PASS | **+2.5 → +0.2 %** PASS → PASS | 0.091 → 0.091 PASS | CAVEAT → FAIL* (0 / 117, unchanged) | 0.940 / 0.132 → PASS | — | 1.1 → 3.5 % (1.2 %) PASS | 2.3 % / 36.8 % | **31.0** | no flip; |ΔC3a| 2.3 pp |
| 2023 | — | — | (control −3.0 %, the 1-pp bar year) | — | — | — | — | — | — | — | **kill #1** (window 187, Jul 7–8); Jan–Jun 181 windows Optimal |
| 2024 | all PASS → all PASS (CC −0.21 → +0.03) | PASS → PASS | **+0.5 → −0.9 %** PASS → PASS | 0.152 → 0.166 PASS (+0.014) | PASS → PASS (0 / 8) | 0.952 / 0.091 → PASS | — | 0.7 → 2.6 % (0.5 %) PASS | 2.0 % / 38.2 % | **22.4** | no flip; |ΔC3a| 1.4 pp |
| 2025 | SKIPPED → SKIPPED (preliminary EIA-923) | SKIPPED | **+3.8 → +2.1 %** PASS → PASS | 0.070 → 0.064 PASS | CAVEAT → FAIL* (0 / 20, unchanged) | 0.904 / 0.145 → PASS | — | 0.5 → 2.2 % (0.6 %) PASS | 1.6 % / 27.2 % | **17.8** | no flip; |ΔC3a| 1.7 pp |

\* The probe carries no `calibration_attestation.json`: C6 reads UNATTESTED and the rule-22 C3c ledger route is unavailable, so the keeper's ledgered CAVEAT scores
FAIL on the probe at the identical magnitude (SPP Addendum D(3) precedent). Determination: control CALIBRATED; arm NOT-YET on those artefacts only (0 gated
criteria FAIL). The scorer budgets `uc_schedule` energy in C8 at this pin (R4 says report-only): the share is given both ways; CC_REGULAR stays far below the 30 % cap either way.

### 0.2 GATESPEC §6.1 wall rows (standard solve container, 4 cpus, `MARKET_SIM_HIGHS_THREADS=1`, `uc_solver_preset=lean`; baseline = the same shard's P0 + P1, PRECOMMIT §5 proxy)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (windows; mean / p95 MILP s) | P1 s | total s | **ratio** | integers/window (int. clusters / clusters) | nodes p50 / p95 | gap p95 | time-limit hits | peak RSS GB (UC / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NEISO 2019 | 159.2 | 78.0 | 2,585.9 (365; 7.04 / 26.00) | 81.2 | 2,786.2 | **17.5** | 1,368 (38 / 61) | 8 / 122 | 9.97e-4 | 0 | 4.30 / 5.41 |
| NEISO 2020 | 187.3 | 91.3 | 1,698.1 (365; 4.61 / 14.39) | 96.0 | 1,941.1 | **10.4** | 1,440 (40 / 64) | 3 / 54 | 9.97e-4 | 0 | 4.40 / 5.26 |
| NEISO 2021 | — (P0 76.0) | 76.0 | Jan–Aug 243 windows: 2,185 s MILP (8.99 / 38.84), nodes 8 / 261 | — | kill at 2,426 s | — | 1,440 (40 / 68) | — | 1.0e-3 | 0 | — |
| NEISO 2022 | 154.3 | 78.1 | 4,580.4 (365; 12.51 / 41.47) | 76.2 | 4,776.0 | **31.0** | 1,260 (35 / 69) | 27 / 279 | 9.96e-4 | 0 | 4.38 / 5.54 |
| NEISO 2023 | — (P0 82.8) | 82.8 | Jan–Jun 181 windows: 2,030 s MILP (11.21 / 45.37), nodes 11 / 275 | — | kill at 2,184 s | — | 1,332 (37 / 70) | — | 1.0e-3 | 0 | — |
| NEISO 2024 | 159.2 | 81.2 | 3,365.7 (365; 9.18 / 48.36) | 78.0 | 3,565.9 | **22.4** | 1,296 (36 / 71) | 1 / 365 | 9.95e-4 | 0 | 4.31 / 5.24 |
| NEISO 2025 | 161.9 | 79.9 | 2,671.8 (365; 7.28 / 38.85) | 82.0 | 2,876.1 | **17.8** | 1,188 (33 / 68) | 1 / 249 | 9.97e-4 | 0 | 4.24 / 5.36 |

Unlike SPP (every window at the root, 2.6–4.9 s), NEISO's windows branch: the post-root tail is 87–96 % of the stage (2019: tail 2,385 s of 2,586; presolve 120 s;
root LP 54 s), 1.2–2.6× more strong-branching LP iterations than SPP per year. Whole-shard wall 42–80 min; the 162-min LP budget (Addendum A) was never approached.
**D-2 ("Keep 3×; fund speedup") is reported, not judged:** every year is 10–31× its P0 + P1.

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–7; 2021 and 2023 unmeasurable)

| # | reading | control (2019 · 2020 · 2022 · 2024 · 2025) | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | M3 lower-tercile mean error $/MWh | +10.56 · +6.75 · +25.92 · +10.21 · +15.90 | **+9.11 · +6.03 · +24.85 · +9.81 · +15.15** | toward 0 | **yes, every year** (−$0.4 … −$1.5; the excess stays) |
| T2 | ratio of model/actual hours ≤ $15 | 0.350 · 0.020 · 0.000 · 0.000 · 0.000 | 0.357 · 0.031 · 0.000 · 0.000 · 0.000 | rises | sign right in 2 of 5, flat in 3 (the model still makes almost no ≤ $15 hours) |
| T3 | ratio of model/actual hours < $0 | 0 · 0 · 0 · 0 · 0 | 0.50 · 0 · 0 · 0 · 0 | rises | 2019 only |
| T4 | M4 reserve dormancy | n/a (no NEISO AS reference on disk); model share of hours with reserve MCP < $1 = 1.00 | 1.00 in every year; mean MCP $0 | falls | **no move** (as SPP) |
| control | no PASS → FAIL flip, any gated criterion, any year | — | **none** on 2019 / 2020 / 2022 / 2024 / 2025 (artefacts aside) | none | met on the years that solved |
| control | |ΔC3a 2023| ≤ 1 pp | −3.0 % | **not measurable** (kill); every solved year moved 1.4–6.5 pp, all toward lower prices | ≤ 1 pp | not met where measured |
| control | every leg P1 Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | — | 5 / 5 Optimal; unserved 0.0 MWh every year; D-4: 2020 adds `chp_steam` plants 54605 / 54907 rows (0.0001 TWh, the control's own 2021 54605 row class), 2022 54605 again | — | met except the D-4 rows (same mechanism/plant class as the control's own failure, not UC-driven; reported) |
| S1 | MECH 28 share of class energy | 0 | CC_REGULAR 5.6 / 3.3 / 2.3 / 2.0 / 1.6 % (2.48 / 1.55 / 1.16 / 1.16 / 0.94 TWh); ST_GAS 25–38 %; COAL_BIT 2–9 % | reported (R4) | — |
| S2 | starts per plant-year vs CEMS (M1) | CC 2,877 / 2,600 / 2,852 / 2,826 / 2,501 vs CEMS 2,743 / 2,190 / 2,682 / 2,051 / 2,195 (1.05–1.38×); ST_GAS 709 / 301 / 156 / 284 / 149 vs 73 / 80 / 38 / 66 / 20 (1.9–9.7×) | **CC 1,755 / 1,644 / 1,930 / 1,474 / 1,679 (0.64–0.76×)**; **ST_GAS 112 / 37 / 40 / 62 / 44 (0.46–2.2×)** | CC closer to 1 in ≥ 4 of 7 | **no**: CC crosses from over- to under-cycling and is farther from CEMS in 4 of 5 years (2024 closer); ST_GAS lands on CEMS |
| S3 | online capacity vs a measured series | none on disk | arm mean UC online 6.45 / 6.54 / 7.19 / 7.28 / 7.72 GW of 13.1–15.1 GW integer capacity (model-internal) | — | skipped as declared |
| S4 | integer set / no-load source | UC-0 M6: 37 clusters | 33–40 integer clusters of 61–71 plant clusters; 1,188–1,440 integers per window | reported | — |
| S5 | M2(a) CEMS online ≤ (mlf+0.10)·cap while model off, CC_REGULAR TWh | 1.30 / 1.25 / 0.89 / 2.10 / 1.59 | **4.10 / 4.29 / 3.37 / 4.80 / 3.98** | reported | the UC decommits CC in 2–3 TWh/yr more hours where the meter says online |
| W1 | wall rows | — | §0.2 | reported | — |
| W2 | time-limit hits | — | 0 / 365 every solved year | ≤ 3 | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ·load | — | 6.2 / 5.6 / 5.3 / 3.6 / 4.0 % ($192 / 119 / 488 / 156 / 310 M; integer-cluster energy cost $1.0–4.3 B) | ≤ 2 % | **breached every year** |
| W4 | infeasible windows | — | 0 in the solved years; **1 each in 2021 and 2023** | 0 | **kill #1** |
| kill #2 | non-determinism | — | not exercised (one run per year) | — | — |
| kill #3 | control flip / |ΔC3a 2023| > 1 pp | — | no flip; 2023 unmeasured | — | not fired |

## 2. What the UC did to the dispatch (zero LP, from the composed sidecars)

- **Body down, modestly, everywhere it solved:** demand-weighted mean price $34.82 → 32.70 (2019), 24.83 → 23.33, 93.40 → 91.29, 41.87 → 41.31, 72.90 → 71.67.
  The two low-gas years move most (−6 pp of C3a), the high-gas years least. The scarcity tail is untouched (0 h > $300 in every year, as the control).
- **Energy barely moves — this is a price-formation effect, not an energy one:** CC_REGULAR +0.6 / +0.6 / +0.3 / +0.2 / −0.2 TWh, CT_PEAKER −0.2 … −0.3 TWh,
  CC_CHP −0.2 … −0.4 TWh (2019–2022), ST_GAS −0.1 (2020), oil +0.5 TWh (2025). C1 is untouched (the largest CC move is 1.1 TWh against a ±2.8 TWh band).
- **Cycling collapses past the meter:** CC starts −35 … −48 % to 0.64–0.76× CEMS; the UC holds CC online through troughs (MECH 28 1–2.5 TWh/yr of min-load
  energy on CC) and that is what depresses the body. ST_GAS cycling, which the control over-counted 2–10×, lands within ±2× of CEMS.
- **Stacking with the kept floors:** `reliability_floor` forced CC energy 0.36–0.67 TWh/yr in the arm vs 0.19–0.77 in the control (same order; the floor and the UC
  both hold CC online, mostly the same hours), and in two years the floor's hot-day limb collides with the UC's min-down hard enough to make a window infeasible (§5.1).
- **Reserves untouched; uplift large.** Reserve MCP < $1 in every hour, as in the control. Make-whole 3.6–6.2 % of wholesale energy cost — above SPP's 1–4 % and the 2 % sanity bar.

## 3. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7, unchanged): kill #1 fired in two of seven years; independently 2020 C3b worsened by 0.026 (> 0.02). No control flip occurred on
  the five scorable years, so this `R` is *first* an engine/stacking defect at the pin and *second* a body-shift that is larger than the GATESPEC control bar in every
  year — not a measured regression of the keeper's gates. The S2 structure bar is not met (CC under-cycles past CEMS, as in SPP). The relaxation was **not** already tight
  here (GATESPEC §7.2): the L1 integrality gap was 0.33 % of the window objective and the stage moved prices 1–6 pp.
- **Matrix:** NEISO `unit_commitment_milp` → **R** with this RESULT as the citation; the cell re-opens as `U` only with new evidence — a fixed engine (the floor-vs-min-down
  collision) and a relaunch under the SPP Addendum A rule at a fixed pin.
- **D-6 card (copy-paste):** *"UC-2 NEISO A/B — record R, engine first. At 2f872a62 the MILP UC stage cannot complete the NEISO span: 2021 (window 259, Sep 17–18) and
  2023 (window 187, Jul 7–8) stop on an a-priori infeasible window where the kept reliability_floor hot-day CC limb needs units the UC's 6-h min-down has just stopped
  ('floor above min-down'); the other five years solve 365/365 Optimal at 10–31× the P0+P1 wall. Where it solved, the calibrated control does not flip on any gated
  criterion, but the price body moves 1.4–6.5 pp in every year (2019 C3a +6.8→+0.3 %, 2020 −1.2→−7.2 %), 2020 C3b worsens 0.111→0.137, CC starts fall to 0.64–0.76×
  CEMS, make-whole is 3.6–6.2 % of energy cost, reserves stay dormant. Options: (1) record R, stage default-off for NEISO; route the floor-vs-min-down collision to the engine
  lane (a floor the UC must honour must either release the min-down of the units it needs or be visible to the look-ahead guard) and relaunch 2021/2023 only after a fix at
  a new pin [recommended]; (2) hold pending the fix and re-read the five scored years then; (3) promote on structure (not recommended: unfinished span, |ΔC3a| above the
  control bar everywhere, uplift above the sanity bar)."*
- **Not a tuning invitation.** No `uc_*` value, limb or floor was moved; the misses are reported as misses (GATESPEC §7.1).
- **For the engine lane (routed, not fixed here):** the collision is between `units_needed_for_floor` (the lower bound `u ≥ ceil(Σ member min_gen / p̄)` built from
  the kept `reliability_floor`) and `hist_w` (stops carried into the window within DT). Candidate mechanisms, undecidable from the shard reports: (a) the day-gated hot-day
  limb switches on at a floor the previous window's look-ahead did not need, after an economic stop the guard did not cover; (b) an availability-forced stop (a unit-outage
  window ending inside DT) counted as a `w` that the floor then needs back. Either way the SPP span never met it because SPP arms no temperature-gated CC floor.

## 4. Bundles, cost, what survives (rule 31: nothing deleted by the parent)

| artefact | where | promotable? |
|---|---|---|
| five leg bundles (full, incl. `dispatch/<y>_P1.parquet`, 35–45 MB each; the shards' negation also carried `hourly/unit_hourly_<y>.parquet`) | shard branches `claude/ucmilp-neiso-2019` `c01b941a` · `-2020` `59afec7b` · `-2022` `2b04f4c5` · `-2024` `0c0a47ad` · `-2025` `f76b6f08` (all parented on the pin); checked out locally under `results/calibration/ucmilp_neiso_<y>/` | in form yes (rule 34), but a five-year span is not registrable (rule 16); no promotion proposed |
| 2021 / 2023 | nothing pushed (kill #1); the UC month checkpoints stayed in the containers | — |
| composed partial span `results/calibration/ucmilp_neiso_span` (slim copy: `hourly/` sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`, `uc_solve_log_<y>.json`, regenerated `legitimacy_diagnostics.json`, `metrics.json`, configs; no dispatch, no `unit_hourly`, no `network`/`reserve_family`) | `docs/records/neiso/ucmilp/data/ucmilp_neiso_span/` (20 MB, this PR) | the record |
| bench L1 + L2 artefacts | `claude/ucmilp-bench-neiso-2023-L1L2` `bcd35c32`; `results/bench/uc/neiso_2023_L{1,2}` checked out locally | bench, never registrable |
| dashboard | **nothing registered**; the local sidecar/payload (`2026-10-10-ucmilp-neiso-uc-b`) used for scoring was removed before the commit; `frontend/data/` untouched | — |

Cost: 8 shard containers (1 bench, 7 legs; 36–80 min each), zero LP in the parent. Reproducing the five solved legs: five shards at the pin, 42–80 min wall each. Shard
branches are transport (rule 33): the owner may delete the six `claude/ucmilp-*neiso*` branches once this PR merges (a session cannot, 403). **Promotion question: none
proposed; the lane recommends R.** The leg bundles will not survive this container; they survive on the shard branches.

## 5. Process record (rule 33: every shard archived; rule 31: nothing deleted by the parent)

| shard | session | outcome | branch / SHA | archived |
|---|---|---|---|---|
| bench L1 + January L2, NEISO 2023 | `session_012ycymxYWiMTrKiuCs6PZnW` | L1 window 0 Optimal; L2 31/31 windows, 0 time-limit hits, 0 infeasible (PRECOMMIT Addendum A) | `claude/ucmilp-bench-neiso-2023-L1L2` `bcd35c32` | 01:08Z |
| 2019 | `session_01HoP2UhK6AnpAS6yGWVkfuv` | solved; 365/365 Optimal; pushed (two false starts before the clean run: no `/usr/bin/time` in the container; a `pkill -f` that matched its own shell; the shard then removed its own aborted run's partial out-dir — an unauthorised `rm` of a few-seconds-old empty directory, disclosed) | `claude/ucmilp-neiso-2019` `c01b941a` | 02:10Z |
| 2020 | `session_01GtX64qX7V4jD9uUXRWeqcF` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-2020` `59afec7b` | 01:56Z |
| 2021 | `session_014rjmPknpDkWTTFbgthZaRZ` | **kill #1**: `UcWindowInfeasible` window 259 [6216, 6252) (Sep 17–18); Jan–Aug 243 windows Optimal; nothing pushed | — | 02:16Z |
| 2022 | `session_0139MxkTunndpZfw9rGV3Hz6` | solved; 365/365 Optimal; pushed (one aborted launch seconds in; the shard removed that run's empty `dispatch/` dir before the clean run) | `claude/ucmilp-neiso-2022` `2b04f4c5` | 02:48Z |
| 2023 | `session_01XbPPrKssS9ygkNxteZkJXL` | **kill #1**: `UcWindowInfeasible` window 187 [4488, 4524) (Jul 7–8); Jan–Jun 181 windows Optimal; nothing pushed | — | 02:16Z |
| 2024 | `session_01UkzJ1WkuLwxMGJoEeMzeQ7` | solved; 365/365 Optimal; pushed | `claude/ucmilp-neiso-2024` `0c0a47ad` | 02:22Z |
| 2025 | `session_013467WdXSissQzWUrUTkd9S` | solved; 365/365 Optimal; pushed (two early launches never solved: a 2-h background cap; no `/usr/bin/time`) | `claude/ucmilp-neiso-2025` `f76b6f08` | 02:15Z |

Every shard ran `uv sync` once because the container had no `.venv` (the system interpreter lacks pyarrow); the repo's only install route, not a repair. No shard edited `src/`, `scripts/` or `frontend/data/`; none opened a PR. The shards' `.gitignore` negation also carried `hourly/unit_hourly_<y>.parquet` (16 MB, normally kept off `main`) onto the shard branches; the slim span drops it.

### 5.1 The two infeasible windows (kill #1), verbatim

```
2021: market_sim.model.uc.window.UcWindowInfeasible: UC window 259 [6216, 6252) solve ended Infeasible with no feasible incumbent (37188 columns, 8100 rows, 40 integer clusters); LP relaxation: Infeasible; a-priori contradictory rows: min_down=1; carried starts above n: 0; floor above min-down: 1
2023: market_sim.model.uc.window.UcWindowInfeasible: UC window 187 [4488, 4524) solve ended Infeasible with no feasible incumbent (35388 columns, 7560 rows, 37 integer clusters); LP relaxation: Infeasible; a-priori contradictory rows: min_down=3; carried starts above n: 0; floor above min-down: 3
```
Call chain in both: `replay_keeper.py` → `run_calibration_full.py solve_and_persist` → `run_calibration.py run_year` → `pipeline/solve.py:754 run_energy_solve` → `pipeline/uc.py:290 p1_fleet_prep` → `uc.py:396 run` → `model/uc/solve.py:460 solve_window`.

What the engine's own diagnostic (`model/uc/diagnose.py::diagnose_window`) says, read against the source at the pin: `floor_above_min_down` counts cluster-hours where `u_lower > n − hist_w`, i.e. a structural member floor (`units_needed_for_floor`: `min_gen` clipped to `pmax × availability`, summed per cluster → `ceil(floor / p̄)`) needs more units online than the carried min-down leaves available (`hist_w` = units stopped within `DT` hours before the window). The LP relaxation is infeasible a priori, so neither branching nor the 600-s time limit is involved. The windows are a July heat week (2023) and a September heat day (2021): the only NEISO floor that pins **CC_REGULAR** by a temperature gate is the enabled `reliability_floor` limb *Central / CC_REGULAR / tmax > 29.92 °C / 49.9 % of available capacity, all 24 h, cheapest-first* (`RELIABILITY_FLOOR_REGISTRY["NEISO"]`; the other five enabled limbs are CT_PEAKER HB15–21 limbs in Boston / Connecticut / North). The UC's CC_REGULAR cluster physics is DT = 6 h. The collision class is therefore **a day-gated reliability floor landing on a CC cluster inside the min-down of a stop the UC (or a zero-availability hour — an outage window ending — counted as a stop) took in the preceding hours**: the kept `reliability_floor` and the UC's min-down both constrain the same CC units (the rule-19 stacking risk the PRECOMMIT named), and the UC-1-FIX look-ahead min-down guard did not cover this instance. Which of the two stop sources (an economic decommit the look-ahead did not see as floor-bound, or an availability-forced stop) is not decidable from the shard reports; the capture is gone with the containers. **Routed to UC-DESK / the engine lane (not this lane's region, rule 32: a shard that repairs infrastructure is a failure).** The SPP span never met it because SPP's keeper arms no temperature-gated CC floor.

Not a tuning invitation: no `uc_*` field, no floor and no limb was moved; nothing was relaunched (PRECOMMIT §6 kill #1: record and STOP; a relaunch is a desk decision at a fixed pin, SPP Addendum A rule).

## L1 gate (PRECOMMIT §7, Addendum A) — PASS before the span

Window 0 of NEISO 2023 Optimal (10.34 s, 12 nodes, gap 7.3e-4, 1,332 integers); January 31/31 windows with 0 time-limit hits and no infeasible window, gap max 9.9966e-4; integrality gap $17,376 on a $5.28 M window (0.33 %); MILP starts 5 vs 77 in the P1 slice. The gate passed and did not predict the summer collision: January has no hot-day limb.

## Log entry

- 2026-10-10 · UC-2-NEISO `session_01D9RZoc9NrNhUBJLcYxyJx4` (Fable) · `claude/ucmilp-2-neiso-ab-n7c2` · zero LP in the parent · PRECOMMIT `26c7143d` before any shard;
  L1 gate PASS (window 0 Optimal; January 31/31, 0 TL hits) → budget 162 min by the declared rule · seven shards at `2f872a62`: **2021 and 2023 kill #1
  (`UcWindowInfeasible`, "floor above min-down" — the kept `reliability_floor` hot-day CC limb vs the UC's 6-h min-down)**; 2019 / 2020 / 2022 / 2024 / 2025 solved
  365/365 Optimal, wall 10.4–31.0× P0+P1 · partial five-year span composed (scratch composer: `gas_price_override` per-year + respan; local reverted registration) ·
  **no control flip on any gated criterion**; C3a 2019 +6.8→+0.3 %, 2020 −1.2→−7.2 %, 2022 +2.5→+0.2 %, 2024 +0.5→−0.9 %, 2025 +3.8→+2.1 % (|Δ| 1.4–6.5 pp, all
  above the 1-pp control bar); 2020 C3b 0.111→0.137; CC starts 1.05–1.38× → 0.64–0.76× CEMS; ST_GAS starts to 0.5–2.2× CEMS; lower-tercile error −$0.4…−1.5; ≤ $15
  hours flat; reserves dormant; uplift 3.6–6.2 % · **verdict R** (kill #1; 2020 C3b > 0.02) · cell `unit_commitment_milp` NEISO → R · D-6: record R, route the
  floor-vs-min-down collision to the engine lane, relaunch 2021/2023 only at a fixed pin · nothing registered, nothing promoted, nothing deleted; 8 shards archived.
