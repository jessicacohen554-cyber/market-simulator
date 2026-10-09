# PRECOMMIT — UC-2-SPP-B: pre-registered A/B of the MILP unit-commitment stage on every SPP backcast year with SPP's two conduct floors OFF, 2026-10-09

> **STATUS: DRAFT, HELD (UC-DESK 18:01Z: "HOLD the shard launch … a second logical delta … I'm taking it to the owner as a card").** The seven shards
> launched 18:08–18:10Z before the HOLD reached this session (18:14Z) were interrupted at 18:15Z and archived at 18:17Z with nothing pushed (Addendum B).
> §1 now carries BOTH arm variants; which one is solved is the owner's ruling. No shard launches until it lands. Every other section is unchanged.

**Written and pushed BEFORE any shard exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing moves after a number comes in (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-2-SPP-B`
(session `session_01N2LCxAQwPFjvYwCdSH4uCx`, Fable), branch `claude/ucmilp-2-spp-b-v3k` off `origin/main`
`6cf95135b8db1b827d55831d81df7870a76bf12c`. Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on
**owner ruling D-6 SPP (2026-10-09, decision card), verbatim: *"Record R + test floors-off arm (Recommended)"***.
Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7; plan `docs/uc-milp-program-plan-2026-10.md` §8.
Predecessor (the first arm, "arm A"): `PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (+ Addenda A–D) and
`RESULT-ucmilp-spp-ab-2026-10-04.md` on `claude/ucmilp-2-spp-ab-r7qd` (PR #7207), verdict **R**. This file copies
their structure, readings and bars (never re-derived) and adds the floors-off hypothesis readings H1–H4.

**Why this is new evidence, not a re-test (rule 28).** Arm A kept both conduct floors (owner ruling R5, D-5 SPP) and read
R: the UC priced CC start and no-load while the kept floors held coal and ST_GAS online, so CC energy shifted to coal
(rule 19 stacking: RESULT-A §0, §2 "Coal for CC", C8 §1). This arm **replaces** both floors with the UC's own commitment.
The config is different; the SPP `unit_commitment_milp` cell is re-entered on this evidence, not re-tested.

## 0. Preconditions (checked before this file was written; zero LP)

| check | result |
|---|---|
| `main` carries the UC engine plus UC-1-FIX: `git log origin/main --oneline \| grep -c "UC-1-FIX\|ucmilp-1-fix"` ≥ 1 | **4** (merge `ae224faf` of PR #7201 + three UC-1-FIX commits) |
| `src/market_sim/pipeline/uc.py` at the pin has no `artifact_dir` | **0 references** |
| a UC-SPEED PR merged before launch? | **no**: `git log origin/main` has no speed/UC-3 commit; open PRs are #7217, #7210, #7207 only. The pin is `origin/main` HEAD at session start and is not chased |
| the SPP keeper arms nothing in `UC_REFUSED_ALWAYS` (15 fields) | every refused field reads `False` — **0 armed** (`UC_REFUSED_BY_RULING` is empty at the pin) |
| the arm config validates | `ScenarioConfig(**keeper_2019_scenario_config, **delta)` constructs with no refusal; `uc_*` resolve to the declared defaults; `cache_key()` `72eb143b…` → `675327b4…` |
| tooling and control byte-identical `ae224faf` → `6cf95135` | `shard_prompt.py`, `replay_keeper.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `_ucmilp_compose_span.py`, `_ucmilp_benefit_screen.py`, `_closeoutsppnuc_compose_span.py`, `lib/unit_marginal.py`, `pipeline/uc.py`, `model/uc/`, `config/iso_configs.py`, `keepers/SPP.json`, `results/calibration/closeout_spp_nuc_span/**` — **all IDENTICAL** |
| solve surface `ae224faf` → `6cf95135` | *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"* |

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** SPP's designated keeper **now** `2026-10-03-closeout-spp-nuc-keeper`
  (`frontend/data/backcast/keepers/SPP.json`), bundle `results/calibration/closeout_spp_nuc_span`, seven year-isolated legs
  2019–2025 at `8c3ea461…`; its committed `metrics.json`, `legitimacy_diagnostics.json`, `hourly/*` and the status part are the
  control readings. The same control as arm A.
- **Second comparator:** arm A's composed span `results/calibration/ucmilp_spp_span` on `claude/ucmilp-2-spp-ab-r7qd`
  (`82d6ee60`; PROBE `2026-10-05-ucmilp-spp-uc-b`), read into a scratch directory — never re-solved, never edited.
- **Pin (every shard):** `6cf95135b8db1b827d55831d81df7870a76bf12c` = `origin/main` HEAD at session start
  (*closeout-ERCOT-w6*, PR #7216). `source_revision` is this full SHA, never a branch.
- **Arm — ONE logical delta (UC on, conduct floors off). Two variants, written out; the owner picks one (card D-5b):**

  **V1 — registered fields only:** `replay_keeper.py results/calibration/closeout_spp_nuc_span --years <y> --set unit_commitment_milp=true
  --set st_gas_mustrun_per_plant=false --set coal_sync_srmc_tranche=false --set coal_mustrun_per_plant=false`. Removes the MECH 16 floor and the
  MECH 3 floor, **and** re-prices the PRB `_sync` band (the side-effect quantified in Addendum B — a second logical delta under GATESPEC §5's
  one-delta rule, which is why this is held). Needs no code change; solvable at the pin today.

  **V2 — one delta, new field:** `--set unit_commitment_milp=true --set st_gas_mustrun_per_plant=false --set <new field>=true`, where the new
  field (proposed name `coal_sync_floor_release: bool = False`, default off, byte-identical off, in `_CACHE_KEY_OPTIONAL_FIELDS`) makes
  `assembly.py:1645` read `sync_floor = 0.0` while `coal_sync` stays True — the forcing goes, the `_mustrun`/`_sync` split and its pricing stay.
  Rule 19: it removes a mechanism, adds none. Rule 28: a solve-affecting `ScenarioConfig` field ⇒ its row in `mechanism-matrix.js` and a cell in
  every ISO shard, in the PR that adds it (CI `check_mechanism_matrix.py`), plus a unit test that the fleet is byte-identical with it off and
  that `coal_sync_pmin_mw == 0` on every coal row with it on. That PR is `src/` work outside this lane's charter and must merge (or be pinned as
  the engine SHA was for arm A, owner ruling R6) before the shards launch; the pin then moves and §8's G-DRIFT is redone in an addendum.

  Under either variant everything else — the recipe, `uc_*` at their declared defaults (table below), the keeper's authorized price tuning
  (`offer_curve_by_group` all bands 0.93), pricing (R3: markup zeroed on integer clusters, uplift sidecar), rule 20 (R4: MECH 28 reported, not
  budgeted) — is identical to arm A.

- **Disclosed side-effect of the V1 coal off-switch (not a tuning; the only registered route; quantified zero-LP in Addendum B).** With `coal_sync_srmc_tranche` off the
  keeper's split of each coal plant's min-load band into a fuel-free contracted `_mustrun` tranche and a spot `_sync` tranche priced
  at full SRMC collapses back to one fuel-free `_mustrun` band (`assembly.py:633–641`). In SPP that re-prices the PRB `_sync` share —
  783 MW of the 4,895 MW PRB min-load band (16 %), 4.8 TWh/yr dispatched in the keeper; lignite carries no `_sync` — from full SRMC to
  VOM + carbon + NOx. The UC's own coal min-load (`mlf`, `model/uc/params.py`) comes from the uc-params artifact and is untouched.
  Bound on the confound: the `_sync` band already ran 4.5–4.8 TWh/yr forced in the keeper, so the re-pricing can add at most
  ≈ 2 TWh/yr of PRB energy (783 MW × 8760 h = 6.9 TWh ceiling); it opposes H2 and is reported beside it. Routed to UC-DESK
  before launch (message 2026-10-09) with the alternative — a new field that zeroes the forcing but keeps the split — which is a
  `src/` change outside this lane's charter.
- **Per-plant tables they gate:** the ST_GAS floor reads `thermal_tranches_SPP.csv` `online_frac` rows under
  `_TRANCHE_GATE_COLUMNS` (`campd_bins.py:2123`); with the gate off those rows are not read. The coal floor's `coal_sync_online_frac`
  and take-or-pay shares are read only inside the `coal_sync` block. No data file is edited (rule 23); nothing in `data/` moves.
- **Not a matrix re-test (rule 28):** `spp_commitment_posture` (R), `spp_gas_commitment_bridge` (R, DO-NOT-REDO), `online_capacity_envelope`
  (SPP-83) are not re-run in any form. The cell this lane feeds is `unit_commitment_milp` × SPP, currently stamped from arm A (R by the desk);
  the verdict follows this RESULT.
- **DOF (rule 21):** zero free parameters added; two measured-behaviour floors removed by owner ruling (the removal is the ruling's
  object, not a sweep). Arm A's DOF statement otherwise stands.

## 2. Target readings (fixed ex ante; bars copied from arm A — half the distance to the gate band)

Control values are the keeper's registered records. "met" is decided on the composed span's `calibration_verdict.py` output and the
zero-LP re-measurement of M1/M3/M4 (`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported, pointed at the span).

| # | reading | control | arm A (for reference) | sign expected | bar (met iff) |
|---|---|---|---|---|---|
| T1 | SPP 2020 C3a mean LMP (model/actual − 1) | **+27.7 %** FAIL (band ±10 %) | +19.0 % (0.16 pt short) | negative | arm ≤ **+18.85 %** |
| T2 | SPP 2019 C3a | **+12.3 %** FAIL | +10.3 % (met) | negative | arm ≤ **+11.15 %** |
| T3 | SPP 2020 C3b NRMSE | **0.345** FAIL (≤ 0.20) | 0.273 (0.0005 short) | down | arm ≤ **0.2725** |
| T4 | low-price-hour count ratio model/actual, hours ≤ $15 and < $0 (M3), 2019 and 2020 | 2019: 0.025 / 0.04 · 2020: 0.15 / 0.11 | 2019 0.094 / 0.271 · 2020 0.310 / 0.456 | both rise toward 1 | sign only; magnitude reported |
| T5 | M4 reserve dormancy (share of hours with model reserve MCP < $1) vs actual, 2019 and 2020 | model 1.00 vs actual 0.09 / 0.08 | 1.00 (no move) | dormancy falls; mean MCP rises | sign only |

**Expected cost, declared, not a kill (UC-0 F2; arm A measured it):** SPP 2024 C3a is model-LOW (−11.2 % FAIL; arm A −22.6 %) and its
C3b 0.216 (arm A 0.344). The UC lowers the body; removing the coal floor lowers it less (coal no longer held in at VOM in the trough) or more
(cheaper `_sync` band) — the sign is **not** predicted here; both C3a and C3b for 2024 are reported as a cost row beside the verdict.

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered SPP year, any criterion, any class row** vs the **keeper** (`calibration_verdict.py` per-(criterion,
key, year) status diff). The tight rows, named now (unchanged from arm A §3):

| year | criterion | control | headroom | why it is tight; what arm A did |
|---|---|---|---|---|
| 2021 | C3a | +7.1 % PASS | 2.9 pts | body down helps (A: +3.8 %) |
| 2022 | C3a | −4.8 % PASS | 5.2 pts | model-low (A: −9.4 %) |
| 2023 | C3a | −6.4 % PASS | 3.6 pts | model-low, train tier (**A flipped: −15.9 %**) |
| 2025 | C3a | −4.3 % PASS | 5.7 pts | model-low (A: −10.0 %, boundary) |
| 2019 | C3b | 0.160 PASS | 0.040 | shape (A: 0.143) |
| 2021–2025 | C3b | 0.176 / 0.175 / 0.176 / —(2024 FAIL) / 0.153 PASS | 0.024–0.047 | shape (**A flipped 2023: 0.233**) |
| 2019–2020, 2023–2025 | C1 CC_REGULAR | +2.25 / +1.60 / −4.49 / −5.80 / −7.86 TWh PASS (±8 TWh, ±3 pp) | 2025: 0.14 TWh | **A flipped 2023/2024/2025** (−10.18 / −11.83 / −13.76) |
| 2019–2020, 2023–2025 | C1 COAL_PRB | +0.24 / −3.03 / +0.57 / +0.82 / +7.39 TWh PASS | 2025: 0.61 TWh | **A flipped 2025** (+10.21); 2021/2022 already FAIL (+10.98 / +10.75) |
| 2019–2022 | C3c | CAVEAT (ledgered through the keeper's attestation) | — | a probe carries no attestation: CAVEAT → FAIL here is the Addendum-D artefact, compared on magnitude (0 h / 372 h) |
| every year | C8 forced share | PASS (ST_GAS 15.7–33.8 %; 2022 grounded conditional) | — | **A flipped 2021/2022/2023/2025** through the kept ST_GAS floor; with the floor off the only ST_GAS forcing left is MECH 28 (reported, R4) |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper; no new D-4 FAIL row.
**The seven D-4 FAIL rows of the control are all `st_gas_mustrun_per_plant` plant rows (1230/3008/6193); with the floor off they must be
absent — their disappearance is expected, not a reading.**

## 4. Hypothesis readings (ADDED; fixed ex ante; the D-6 card reads them). Instrument: the composed sidecars, same for all three bundles

All three bundles are read with ONE instrument per row so the three columns are comparable: P1 class energy from `hourly/class_hourly_<y>.parquet`
(`pass == P1`, Σ`mw` by `klass`, TWh); forced shares from the regenerated `legitimacy_diagnostics.json` D-2 summary; starts from
`screen_year` M1 (on = CF ≥ the script's `ON_CEMS` threshold; CEMS from the bench `campd` frame — a measured comparator, never an input).
"Gap" = arm A − control. Years: all seven.

| # | reading | control | arm A | sign expected in arm B | bar (met iff) |
|---|---|---|---|---|---|
| H1 | CC_REGULAR P1 energy, TWh | 46.12 / 46.78 / 25.78 / 26.75 / 41.26 / 40.09 / 34.76 | 37.74 / 40.12 / 21.10 / 22.73 / 35.57 / 34.05 / 28.86 (gap −4.7 … −8.4) | **up vs arm A** (back toward the control) in every year | B − A ≥ ½·(control − A) in ≥ 4 of 7 years AND B > A in every year |
| H2 | COAL_PRB + COAL_LIGNITE P1 energy, TWh | 87.84 / 71.71 / 100.54 / 101.55 / 73.70 / 67.23 / 88.15 | 95.56 / 79.58 / 103.46 / 103.64 / 80.17 / 74.38 / 91.46 (gap +2.9 … +7.9) | **down vs arm A** in every year | A − B ≥ ½·(A − control) in ≥ 4 of 7 years AND B < A in every year; COAL_PRB and COAL_LIGNITE each reported |
| H3 | C8 ST_GAS forced share (D-2 summary `forced_share`, scorer at the pin — budgets MECH 28; the R4-adjusted value with MECH 28 removed is reported beside it) | 0.181 / 0.157 / 0.288 / 0.338 F / 0.231 / 0.183 / 0.177 | 0.277 / 0.257 / 0.368 F / 0.392 F / 0.336 F / 0.283 / 0.314 F | **falls vs arm A** in every year (the floor is gone) | B < A in every year AND ≤ 0.30 in every year (arm A's four C8 FAILs clear) |
| H4 | coal starts per plant-year vs CEMS (M1: model / CEMS, COAL_PRB and COAL_LIGNITE) | PRB 77:259 / 134:341 / 146:278 / 161:274 / 285:301 / 211:372 / 198:305 (model:CEMS, 2019→2025); LIG 8:15 / 11:35 / 11:33 / 7:20 / 1:19 / 2:12 / 2:23 (model:CEMS, 2019→2025) | PRB 60:259 / 83:341 / 94:278 / 108:274 / 124:301 / 111:372 / 88:305 (model:CEMS, 2019→2025); LIG 8:15 / 11:35 / 11:33 / 7:20 / 1:19 / 2:12 / 2:23 (model:CEMS, 2019→2025) | PRB starts **rise vs arm A toward CEMS** (no floor holds the plant in; the UC's start cost and min-down now decide) | PRB model/CEMS ratio B > A in ≥ 5 of 7 years; magnitude reported, never judged against CEMS (comparator, not target) |

**Expected cost, stated (the ruling's own risk).** Removing the conduct floors can under-commit coal in the hours SPP's regulated owners
self-commit (ASSESSMENT §6: "36 % of 2020 energy self-committed"; MISO SOM Table 7 analogue). What that does to the **C1 coal rows 2021–2025**:
COAL_PRB 2021 (+10.98 TWh FAIL) and 2022 (+10.75 FAIL) are model-HIGH, so a fall moves them toward the band — a PASS there is a gain, not a
cost; COAL_PRB 2023 (+0.57), 2024 (+0.82) and 2025 (+7.39) are PASS with 8.57 / 8.82 / 0.61 TWh of low-side headroom — a fall beyond that
flips them PASS → FAIL on the low side, and that is counted as a control flip (kill #3) exactly like any other. COAL_LIGNITE rows are reported
the same way. The cost is declared, not excused: if the UC alone under-commits SPP coal, that is the finding the owner asked for.

## 5. Structure and cost readings (reported; copied from arm A §4–§5)

| # | reading | control | arm A | arm B instrument |
|---|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, COAL_PRB, COAL_LIGNITE, ST_GAS) and ISO-wide | 0 | CC 2.3–5.2 %, PRB 0.9–2.7 %, ST_GAS 1.7–2.5 % (12.0 % 2025) | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 |
| S2 | starts per plant-year vs CEMS (M1) for CC, PRB, LIG, ST_GAS | CC 1.6–2.3× CEMS; PRB 0.23–0.95×; ST_GAS 0.45–0.95× | CC 0.52–0.77×; PRB 0.23–0.41×; ST_GAS 0.14–0.27× | `screen_year` M1 on the span; `uc_schedule_<y>.parquet` Σ`v` per cluster as the engine's own count |
| S3 | online capacity vs the SPP portal series | comparator not on disk (arm A §4) | skipped | skipped and named; `online_mw` from `uc_schedule_<y>.parquet` vs available MW reported |
| S4 | integer set and fallback shares | — | 82–94 integer clusters of 208–226; no-load `uc-params` 122–123 | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| W1 | the GATESPEC §6.1 wall row per year (baseline = the same shard's `solve_p0 + solve_p1`, arm A's declared proxy) | — | ratios 5.1–10.2× | reported for all seven years **against the ruled D-2 ceiling of 3×** (charter: "D-2 = 3× (ruled; report the ratio)"); above the ceiling is a cost finding (GATESPEC §7.3), never a defeat |
| W2 | time-limit hits | — | 0 / 365 | ≤ 3 of 365 per year |
| W3 | uplift share = Σ make-whole ÷ Σ λ_P1·load | — | 1.0–4.4 % (breached 2020–25) | ≤ 2 % (sanity) |
| W4 | infeasible windows | — | 0 | 0 (else kill #1) |

**Shard budget:** arm A's whole-shard wall was 33–45 min end to end (clone, hydrate, regenerate, P0, UC, P1, push). Budget per shard
= **ceil(1.3 × 45) = 59 min** (the charter's formula). One shard commit ≤ 20 min of runtime (rule 32); a shard approaching the budget with no
artifact stops and reports. PENDING > 45 min: archive and relaunch.

## 6. Kills (GATESPEC §5; unchanged from arm A) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"): an engine defect, routed to
   UC-DESK, never a tuning invitation.
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed runs of the same recipe-year
   (exercised only if a relaunched shard and its predecessor both complete; otherwise "not exercised").
3. **A control flip** (§3) in any registered year, vs the keeper.

## 7. Verdict rule (fixed) and the D-6 card

- **K candidate** — T1, T2, T3 met, T4/T5 signs right, no kill, every leg Optimal, H1–H3 met: recommend the owner's D-6 card read
  "promote on structure"; the lane never promotes (rule 31).
- **R** — any target reading moves the wrong way past its control (C3a 2019 or 2020 up, C3b 2020 up), or any kill fires.
- **I** — no kill, no wrong-sign move, |Δ| below the bar on T1–T3.
- Mixed: the verdict is the worst of the three target rows, stated row by row; H1–H4 are reported beside it whatever the verdict — they
  answer the stacking hypothesis independently of the gates (an R with H1–H3 met is "the stacking was real, the UC alone still misses").
- The RESULT carries the §6.3 gate table with **three columns per gate (control · arm A · arm B)**, H1–H4 answered, the kills, the verdict,
  and the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. G-DRIFT: `main` since `ae224faf` (arm A's pin) → `6cf95135`, classified for SPP (zero LP, on the objects)

23 commits. `solve_surface_register.py --diff ae224faf 6cf95135`: *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*.

| content | files | SPP classification |
|---|---|---|
| closeout-CAISO-w6 / ERCOT-w6: measured CHP BTM share (#7209, #7211, #7216) | `scenarios.py` +53: `caiso_chp_btm_measured`, `ercot_chp_btm_measured` (both `bool = False`, in `_CACHE_KEY_OPTIONAL_FIELDS` with default `"False"`); `data/chp.py` +95: `measured_chp_btm_pct_{caiso,ercot}`, `measured_chp_btm_pct_for_iso` (returns `{}` for every ISO but NYISO/CAISO/ERCOT), `chp_btm_measured_armed` (False unless the ISO is one of those three); `data/fleet/assembly.py` ±16: the NYISO-only `if` becomes `if chp_btm_measured_armed(config)` — same branch, now a function; `run_calibration_full.py` +54: the `--ercot-chp-btm-measured` flag and the two kwargs threaded through `_btm_frame` / `solve_and_persist` / `run_p2_layer`; `scripts/data/build_bench_part_zero_lp.py` +6: the two kwargs; `config/paths.py` +10: `EIA_923_DISPOSITION_*` paths | **INERT**: both fields default off, ISO-gated in code (`chp_btm_measured_armed` is False for SPP; `measured_chp_btm_pct_for_iso("SPP")` is `{}`), ABSENT from the SPP keeper's `run_config.json`, unarmed in `iso_configs.py` (byte-identical); the optional cache-key fields at default drop out of `cache_key()`. The assembly hunk is a refactor of a branch SPP never enters |
| derive / fetch scripts and probes | `scripts/data/{derive_caiso_chp_btm_share,derive_ercot_chp_btm_share,fetch_eia923_disposition,rebase_measured_hr_parasitic}.py` (new), `derive_parasitic_load.py` +448, `derive_pjm_seam_ladders.py` ±16; `scripts/probes/_closeout_*` (new) | not on the solve path (derive scripts produce artifacts; none of the SPP artifacts the recipe reads changed — see next row) |
| data | `data/raw/_processed-legacy/chp_btm_share_measured_CAISO.csv` (new), `data/raw/eia-923-disposition/*` (new), three READMEs | no SPP-read file moved: the SPP recipe reads none of these |
| records, matrix shards, desk docs | `docs/records/**`, `docs/codebase-site/data/mechanism-matrix/{CAISO,ERCOT,MISO,SOCO}.js`, status/registry parts of other ISOs | docs; SPP's shard, keeper and status part byte-identical |

Nothing is LIVE for SPP. No control solve is owed (rule 29(b)); the keeper bundle is the control.

## 9. Solve plan (rules 16, 32–36) — HELD until the D-5b ruling; the `--set` list and the pin follow the chosen variant

- **Seven shards, 2019–2025**, one year each, branch `claude/ucmilp-spp-b-<y>`, out-dir `results/calibration/ucmilp_spp_b_<y>`, prompts (V1 as committed; V2 regenerated at the new pin) from
  `scripts/shard_prompt.py --iso SPP --all-years --sha 6cf95135b8db1b827d55831d81df7870a76bf12c --lane ucmilp-spp-b --bundle
  results/calibration/closeout_spp_nuc_span --set unit_commitment_milp=true --set st_gas_mustrun_per_plant=false --set coal_sync_srmc_tranche=false
  --set coal_mustrun_per_plant=false --budget 59 --note "ucmilp-spp-b: …"`, each appended with: confirm the three UC files and
  `hourly/unit_marginal_<y>.parquet` in the pushed tree; paste the four field values from the leg's `run_config.json` and the count of
  `coal_mustrun` / `st_gas_mustrun_per_plant` rows in the leg's `floors/` output (expected 0); report the GATESPEC §6.1 wall row. Committed as
  `shard-prompts-ucmilp-spp-b.txt`. `create_session` per year: `source_revision` = the pin, model `claude-opus-5-5`, tag `ucmilp:UC-2-SPP-B-shard`.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_spp_b_<y>` non-empty; check out; verify `dispatch/<y>_P1.parquet`
  + the three UC files + `unit_marginal`; the leg's `run_config.json` carries the four values; THEN `archive_session` (rule 33).
- **Compose and score, zero LP:** `_ucmilp_compose_span.py` at the pin aborts on `gas_price_override` (per-year by the keeper's design) and lacks
  `_respan_shared_inputs` (arm A Addendum D). The lane applies **the same scratch-copy workaround as arm A** and discloses it in the RESULT:
  a scratch copy of the composer with `gas_price_override` added to `PER_YEAR_FIELDS`, then the keeper composer's `_respan_shared_inputs` applied
  to the span's `meta.json` so the frames resolve to the keeper's own hashes (`campd-8b15fb193a60`, `eia923-ada99c7451fd`, `eia930-c3bec7e7b952`),
  then `--restore-shared-inputs` verification. No repo script is edited. Then `calibration_verdict.py`, `legitimacy_diagnostics.py`
  (regenerated, never copied), the M1/M3/M4 re-measurement, and the H1–H4 instrument over the three bundles.
- **No registration** (desk ruling: E13 is keeper-only). The slim span goes to `docs/records/spp/ucmilp/data/ucmilp_spp_b_span/`
  (`metrics.json`, `legitimacy_diagnostics.json`, `run_config*.json`, `meta.json`, `uc_solve_log_<y>.json`, `hourly/` sidecars incl.
  `uc_schedule`, `uc_uplift`, `unit_marginal`, `class_hourly`, `class_band_hourly`, `system`, `storage`; never `dispatch/`). Push by pack size.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-spp-b-<date>.md`: the three-column gate table first, wall rows vs 3×, H1–H4, kills, verdict,
  D-6 card, bundles and cost, `## Log entry`); after rebasing onto `main`, append the evidence to the `unit_commitment_milp` × SPP cell in
  `docs/codebase-site/data/mechanism-matrix/SPP.js` as the last commit (the verdict follows the RESULT); ONE PR; message UC-DESK with the gate
  table, then the wall rows, then H1–H4. Never delete a bundle; never promote (rule 31).

## 10. DO NOT REDO

Everything in `docs/mechanism-testing-matrix.md` §5.7's DO-NOT-REDO (curtailment ceiling, gas bridge, offer-band retunes); `spp_commitment_posture`
(R) is not re-run in any form; no `uc_*` value other than the declared defaults; no further `--set` beyond the four above; no control solve; no
re-solve of arm A; no sweep of which floor to remove (the ruling removes both).

## Addendum A (2026-10-09 18:10Z, before any number exists) — launch record

PRECOMMIT pushed as `fb38c1bf` (blobs verified: PRECOMMIT `1660ebdd…` 214 lines, prompts `7d90b10d…` 228 lines) **before** any shard.
Seven shards launched 18:08–18:10Z at `6cf95135b8db1b827d55831d81df7870a76bf12c`, model `claude-opus-5-5`, tag `ucmilp:UC-2-SPP-B-shard`:
`session_01RzxGcy7V73PvDkyYYVFPpX` 2019 · `session_01Jo1Vb2KagT3KCaR8Qujdfw` 2020 · `session_018cHDvhzMZAo46DjRRG5GXE` 2021 ·
`session_014X7kCzmZ1acusvESw62sRw` 2022 · `session_01Nu2YzSrXyvMu97NFYaidmU` 2023 · `session_01YKxBH98RAXEcKXTmt3c2HK` 2024 ·
`session_01Ucr9zKmeBjgoqaeVuygUku` 2025. The floor-mapping finding (§1) was sent to UC-DESK at 17:58Z before launch; no reply had
arrived at launch, so the arm stands as written (the desk may still re-rule before the legs are scored; a re-ruling after launch is
recorded here and the legs are not re-used for a different config).

## Addendum B (2026-10-09 18:15–18:40Z, before any number exists) — HOLD, the interrupted launch, and the re-pricing quantified (zero LP)

**HOLD.** UC-DESK's reply to this lane's floor-mapping message (queued 18:01Z, delivered 18:14Z): *"HOLD the shard launch. coal_sync_srmc_tranche=false
is a second logical delta: it re-prices ~16 % of the PRB min-load band toward zero fuel, which biases the arm toward coal, the opposite of H1/H2. That
breaks GATESPEC §5's one-delta rule. I'm taking it to the owner as a card now."* The seven shards had launched at 18:08–18:10Z (Addendum A); all seven
were interrupted at 18:15Z and archived at 18:17Z. **None pushed a branch** (`git ls-remote --heads origin 'claude/ucmilp-spp-b-*'` is empty); nothing
was fetched, composed or scored; no number exists. The desk asked for (a) this PRECOMMIT as a DRAFT carrying both arm variants — done above (§1
V1/V2) — and (b) the offer-stack delta of `coal_sync_srmc_tranche=false` with the gate off, which follows. Launch waits for the owner's card.

**(b) The re-pricing alone, from the keeper's own `hourly/unit_marginal_<y>.parquet` (P1 offer `mc`, `cap_mw`, `mw` per unit-hour; zero LP, no rebuild).**
With `coal_sync_srmc_tranche=false` every `_sync` tranche (spot share of the coal min-load band, priced at full SRMC) merges into the plant's fuel-free
`_mustrun` tranche (VOM + carbon + NOx; SPP 2019: $4.50/MWh flat on 8 of 9 plants). The `mc` is a per-unit offer constant across the year, so the $/MWh
moved is the same in every hour band (trough = off-peak = peak); what varies by band is the CC offer it is measured against. "Crosses" = the `_sync`
offer sits above the cheapest offered CC_REGULAR tranche before and below it after. Nine PRB plants carry a `_sync` band (Jeffrey EC 272 MW, La Cygne
169, Iatan 144, Nearman/6068 137, 1250 36, 6139 10, 56564 8, 6138 6, Lawrence/60 1); lignite none.

| year | `_sync` MW (9 PRB plants) | `_sync` TWh in keeper / cap-factor | `_sync` offer → re-priced, cap-weighted $/MWh | cheapest CC offer, trough h0–5: min / q25 $/MWh | share of hours `_sync` above CC-min BEFORE | **share crossing below CC-min AFTER** | share crossing below CC-q25 | hours `_sync` was marginal |
|---|---|---|---|---|---|---|---|---|
| 2019 | 783 | 4.83 / 0.986 | 20.23 → 4.24 (Δ −14.80) | 14.77 / 18.31 | 0.925 | **0.823** | 0.672 | 71 |
| 2020 | 773 | 4.59 / 0.974 | 20.27 → 4.27 (Δ −14.99) | 13.34 / 16.34 | 0.972 | **0.861** | 0.762 | 52 |
| 2021 | 782 | 5.07 / 0.983 | 19.10 → 4.29 (Δ −13.78) | 21.88 / 38.60 | 0.756 | **0.672** | 0.104 | 39 |
| 2022 | 782 | 5.07 / 0.980 | 23.47 → 4.24 (Δ −17.49) | 22.03 / 45.97 | 0.638 | **0.527** | 0.000 | 25 |
| 2023 | 735 | 4.51 / 0.979 | 21.77 → 4.22 (Δ −15.85) | 16.04 / 20.86 | 0.981 | **0.870** | 0.604 | 32 |
| 2024 | 798 | 4.31 / 0.975 | 21.04 → 4.27 (Δ −15.52) | 15.89 / 19.41 | 0.932 | **0.823** | 0.679 | 21 |
| 2025 | 798 | 4.92 / 0.987 | 20.94 → 4.34 (Δ −15.64) | 19.38 / 25.16 | 0.716 | **0.614** | 0.179 | 47 |

**Reading.** The re-pricing moves **735–798 MW** of PRB from a **$19–23/MWh** spot offer to a **$4.2–4.5/MWh** fuel-free offer (Δ ≈ **−$14 to −$17.5/MWh**),
in every hour. Against SPP's CC fleet that is merit-order-relevant exactly where the hypothesis is tested: in the low-gas years (2019, 2020, 2023, 2024)
the `_sync` band sits above the cheapest CC tranche in 92–98 % of hours today and would fall below it in **82–87 %** of hours (below CC's q25 offer in
60–76 %). In the high-gas years (2021, 2022) CC offers are higher, so the crossing is 53–67 % at CC-min and 0–10 % at CC-q25; 2025 is in between
(61 % / 18 %). In the keeper the band is forced anyway (cap-factor 0.97–0.99 under the MECH 3 floor), so the re-pricing changes little while the
floor stands; with the floor removed and the UC deciding commitment, a fuel-free 780 MW is a band the UC will keep online through the trough instead
of backing down at $20 — a coal-ward bias of up to ≈ 2 TWh/yr (the Addendum-free bound in §1) concentrated in trough hours. **Conclusion: the desk's
objection holds; V1 is two deltas. V2 (a field that zeroes `sync_floor` and keeps the split) is the one-delta arm.** Which is solved is the owner's card.
