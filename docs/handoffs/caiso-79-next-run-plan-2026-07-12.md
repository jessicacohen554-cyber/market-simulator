# CAISO next-run plan (post caiso-78) — path toward calibrated (2026-07-12)

Planning handoff for the session that runs **caiso-79**. Grounded in the repo
state at HEAD: keeper `2026-07-12-caiso-78-cc-hr` (+ ablation twin), the
caiso-78 calibration-log entry, `FINDING-caiso78-cc-hr-basis-2026-07-12.md`,
`FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md`, and the caiso-70/71/72
lane ledger.

## 1. Where CAISO stands (keeper caiso-78, rubric v2.4, determination NOT-YET)

From `results/calibration/caiso78_cc_hr_basis/metrics.json`:

| Tier | Gate | Status | Reading |
|---|---|---|---|
| load-bearing | C1 fuelmix | **PASS** | all classes in band; CC scramble fixed (HR-basis bug) |
| load-bearing | C2 sysvol | **FAIL** | 2025 −10.2% — adjudicated: the 930 NG cell is corrupted (bench FINDING §3/§4) |
| load-bearing | C3a mean LMP | **FAIL** | +26.9/+37.0/+45.1% — the real open model miss (body overprice, unmasked by the HR fix) |
| load-bearing | C3b shape | **FAIL** | NRMSE ~0.31/0.41/0.41 — same root-cause family as C3a |
| load-bearing | C5a CO2 | **FAIL** | +3.2/+9.1/+25.0% — 2025 actual on the same corrupted preliminary-923/930 basis |
| supporting | C3c tail | FAIL | 2023 spurious system tail vs 21 h actual; 2024/25 0 h vs 35/8 (local tail the topology can't form) |
| supporting | C4 dispatch r | FAIL | gas 0.888/0.830/0.565 — 2024/25 degradation scores the noon-corrupted 930 NG hourly series |
| protective | C6/C7/C8 | **PASS** | governance, diurnal shape, forced-energy budget all hold |

So the distance to "calibrated" decomposes into exactly two problems:

1. **A benchmark problem** (C2-2025, C4-2024/25, C5a-2025, and the C1/C2
   actuals' ×1.10/×1.21/×1.44 inflation): the CISO EIA-930 NG cell carries a
   growing solar-shaped block no gas fleet produced; the G-21 reconcile scales
   the whole fossil classFull to it. Design to fix it is filed
   (930-NG FINDING §5) — scorer/bench layer, CAISO only, **no re-solve** —
   and is *pending owner sign-off*.
2. **A price-formation problem** (C3a/C3b, plus the C3c local tail): the body
   overprice (+27..+45%) and the missing 2024/25 local scarcity tail. The CC
   volume side is now clean; the CT_PEAKER evening gap (~3–4 TWh/yr) remains,
   owned by the local-commitment granularity lane (every system-level lever is
   measured inert: caiso-59/62/70/71; offer re-ordering refuted by caiso-78
   STEP-0 (c)).

Priority order stays as logged (rule 1: structure first, offer level last):
**(i) CT_PEAKER local topology/commitment, (ii) bench-basis rework,
(iii) C3a body base.** (i) and (ii) do not interact — (ii) is scorer-layer —
so they proceed in parallel: (ii) is a sign-off + rescore, (i) is the solve.

## 2. Gating decision to request FIRST: bench-basis rework sign-off

Ask the owner to sign off the 930-NG FINDING §5 design (CEMS-anchored CAISO
fossil actual: CEMS bench-gas hourly × gross→net + the flat 923 non-CEMS cogen
block; C4 gas actual on the same series from the 2024-05 onset; C5a-2025 CO2
rebuilt on complete coverage; other ISOs unchanged). Rationale for doing this
before burning more solves:

- It is the cheapest move on the board (no LP) and flips or honestly re-bases
  **four** of the six FAILs (C2-2025, C4-2024, C4-2025, C5a-2025).
- It re-bases the C1/C2 actuals for *everything after it* — solving first and
  re-scoring later risks tuning against numbers that then move.
- **Disclosed consequence (pre-register it):** the corrected basis moves the
  C1 actual *against* the model in 2023/24 (the inflated classFull was
  flattering the CC level — the caiso-78 print +2.32/+0.97/−0.67 TWh sits on
  actuals inflated by +5.4/+9.7/+16.6 TWh class-wide). C1 may print worse or
  FAIL on the honest basis. That is rule-14 behaviour working as intended: it
  reopens the CC lane honestly instead of leaving it silently closed by a
  corrupted benchmark.

Execution once signed off (same session, before or alongside the caiso-79
solve): implement the scorer/bench change, regenerate the CAISO bench parts
(`frontend/data/backcast/bench/CAISO/*.json.gz`), re-score caiso-78 + twin in
place (`calibration_verdict.py --write-metrics`, the sanctioned no-LP path),
update the dashboard, log the entry. If the owner declines, C2-2025/C4/C5a-2025
keep the standing adjudication notes and the lane stays open — do NOT touch the
model to chase a benchmark known to be corrupt.

## 3. The caiso-79 solve: CT_PEAKER local-commitment lane, STEP-0 gated

The lane's evidence chain (all committed): system reserve co-opt inert
(caiso-59/62), commitment posture inert ex-ante (caiso-70), locational AS floor
15× under free supply (caiso-71), bridge de-crowding negative (caiso-70),
temporal displacement fixed via hydro envelope + firm-import shape/selfschedule
(caiso-72/73/77), offer-band re-ordering refuted — cheapest CT is never under
the marginal CC offer, gap $43–82/MWh (caiso-78 STEP-0). What remains is the
caiso-71 §3 conclusion: CAISO CT energy is **locally committed** (pocket
congestion + local RA/RMR/exceptional dispatch), and the model's topology
cannot see it. Concretely (caiso-72): NorCal CT actual ≈ 388 MW evening vs
model 14 — the Greater Bay pockets don't exist in the topology; LA_BASIN's LCT
import link (12,008 MW ≈ the basin's whole evening load) never binds; SDGE
(1,436 MW cap, binds 27% of evening hours) already works.

Note the honest framing: C1 already PASSes with the CT gap inside the
`min(2% load, 8 TWh)` band. This lane is rule-1 structural work whose scored
payoff is the 2024/25 **C3c local tail**, the C7 CT diurnal shape, and evening
C3a/C3b shape — not a C1 flip.

### STEP-0 (no LP — the caiso-70/71/78 decide-before-solving method)

1. **Data completion (train-year, on-disk source pattern, no quarantine
   issue):** `data/raw/capacity-deliverability/caiso/caiso.csv` already has
   Greater Bay `requirement` (7,312/7,329/7,441 MW, 2023/24/25) but **no
   Greater Bay `peak_load` row** — intake it from the same Final LCT reports
   (Table 3.x), same schema. Build NorCal membership rows for
   `lcr_area_membership_CAISO.csv` (county rule — Bay-Area counties; the
   existing file covers only LA Basin + San Diego/Imperial).
2. **Ex-ante bind test (cheap arithmetic before any build):** compute
   `import_cap = peak_load − LCR` for Greater Bay; from CAMPD, the pocket's
   actual evening CT/gas; from the caiso-78 payload, what the model serves
   that pocket-share of NP15 load with. The gate: in the measured evening
   hours, does `pocket_load − import_cap − in-pocket non-CT supply` go
   positive often enough to call ~0.4–1 GW of CT? (The LA_BASIN lesson: an
   LCT cap ≈ pocket load never binds — verify Greater Bay is tighter before
   building.)
3. **Fork on the answer:**
   - **Cap can bind → build the split** (caiso-79a): `NP15 → GREATER_BAY +
     NP15_rest` with a one-way import-limited internal link, replaying the
     SP15-split playbook verbatim (`docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md`
     FOUNDATION DECISIONS: config zones/shares summing exactly, corridor
     re-homes — COI/Path-66 terminates on NP15 today and must be re-pointed
     deliberately — TAC weights, zone_assignment county branches, crosswalk,
     gas-hub rows, `apply_caiso_local_import_limits` per-year caps, the ~16
     topology test files).
   - **Cap cannot bind → do NOT build the split.** The lane redirects to an
     explicit **local commitment driver** on the pocket's named units
     (exceptional-dispatch / minimum-online-commitment analogue): a min-gen
     window keyed to a measured, forward-native driver (pocket net-load ramp),
     rule-12/17/18/19 compliant — window + driver + forward story declared, a
     `D4_WINDOWS` entry in `scripts/legitimacy_diagnostics.py`, one mechanism
     per phenomenon (enumerate what already floors CT: `ra_mustoffer_bridge`
     only, ~0.1–0.3%). Design doc first, owner-visible, before any solve.

### The solve (whichever fork)

- Recipe: single delta on the caiso-78 keeper recipe (`run_config.json` in
  `results/calibration/caiso78_cc_hr_basis/` is the base).
- `--year 2023 2024 2025` in ONE invocation (years sequential within it),
  main + zero-forcing ablation twin (rule 21), ≤2 concurrent invocations.
- Pre-register directions BEFORE solving (the FINDING pattern): CT_PEAKER up
  toward 4.56/5.24/3.09 TWh with the D-1 profile advancing into h15–18; NorCal
  CT evening 14 → ~388 MW; the 2024/25 C3c tail forms locally (target 35/8 h,
  not a re-armed system tail); C1 CC holds; C6/C7/C8 hold; C3a body move
  disclosed either way (a local premium raises pocket λ but the body base is a
  different lane).
- Register main + twin as PROBES via the `calibration-report` skill
  (`scripts/dashboard_add_run.py` + `build_manifest.py`) in the same session;
  push via `mcp__github__push_files` (never `git push`). Promotion only on the
  rubric bar + LOYO within 2023–2025 (a topology change is not
  LOYO-exempt — it must not be justified by one year's tail).
- Keeper swap, if earned: edit `keepers.json`, rebuild status, then run the
  `calibration-keeper-auditor` agent.

## 4. After both: the C3a body base (LAST, and only on the honest bench)

Do not start this lane until §2 lands (the rework re-bases what the model's
gas fleet should be doing, hence what λ it should print). It is a
decomposition, not a tune:

1. Refresh the belly/evening commitment probe
   (`scripts/archive/caiso_belly_commitment_probe.py`) on the **caiso-78** payload —
   its numbers are caiso-65-vintage and pre-date the firm-selfschedule and HR
   fixes.
2. Adjudicate the demand-basis conflict (caiso-72 STEP-0 candidate 4): 930
   `Demand` vs supply-implied load vs CAISO TAC actuals disagree by ~1.5 GW in
   the afternoon ramp — a rule-14 measured-data decision, needs its own memo.
3. Fuel-basis level check: model marginal-offer implied heat rate × delivered
   gas vs the measured DA λ/gas ratio by month/hub — isolates fuel price vs HR
   vs commitment as the overpricer.
4. Only if 1–3 exhaust without closing it does an offer-curve level re-tune
   get considered (rule 1's "tune second"), on CAMPD-grounded bands, never on
   the residual.

## 5. Parallel housekeeping (not CAISO-blocking, don't let it rot)

- **PJM / NYISO / NEISO re-gate on the fixed `fleet_to_bins`** (caiso-78 blast
  radius — their keepers solved on per-plant-deflated CC offer stacks, and
  their offer multipliers were partly calibrated against it). Separate
  sessions/invocations, parallelizable per rule 12.
- CAISO has **no calibration-complete marker**: no 2022/2019/≤2021/H1-2026
  solve, score, or registration of any kind (rule 22). Forecast-mode 2026+
  runs remain unrestricted.

## 6. Definition of done for this arc

v2.4 load-bearing gates (C1, C2, C3a, C3b, C5a) PASS/CAVEAT **on the honest
benchmark** with C6/C7/C8 holding and the DOF ledger + ablation twin clean →
owner declares the CAISO calibration-complete marker → 2022 validation ladder,
then the one-shot locked test (2019 + H1-2026). The expected shape of the
remaining work: §2 retires the benchmark-side FAILs, §3 closes the structural
CT/tail story, and §4 is the last mile on C3a/C3b — which is where the
determination flips.
