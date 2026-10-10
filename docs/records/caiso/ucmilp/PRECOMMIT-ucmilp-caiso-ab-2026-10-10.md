# PRECOMMIT — UC-2-CAISO: pre-registered A/B of the MILP unit-commitment stage on every CAISO backcast year, 2026-10-10

**Written and pushed BEFORE any span shard exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing is moved after a number comes in (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-2-CAISO`
(session `session_01T6HUKtuBPRdR9nXaHvALxT`, Fable), branch `claude/ucmilp-2-caiso-ab-c3q9` off the pin. Chartered by
UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-10) under the owner's direction *"launch shards for other ISOs to
test"*. Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7; plan `docs/uc-milp-program-plan-2026-10.md`
§3 (UC-2), §8.1 (R3, R4, R6); structure copied from the SPP precedent `docs/records/spp/ucmilp/PRECOMMIT-ucmilp-spp-ab-2026-10-04.md`
(+ Addenda A–D) and its RESULT.

## 0. Preconditions (checked before this file was written; all zero-LP)

| check | result |
|---|---|
| `HEAD` == the pin `2f872a62a7cccadb6800555c11a73745dcdb89a4` (main at the merge of PR #7218: engine + UC-1-FIX + UC-SPEED lean preset) | yes; `origin/main` has since moved (`525b3f4e`) and is NOT chased |
| `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` ≥ 1 | yes (gate + `uc_*` fields + `UC_REFUSED_ALWAYS`) |
| the CAISO keeper's `run_config.json` arms fields in `UC_REFUSED_ALWAYS` | **4 armed**: `caiso_ra_mustoffer`, `caiso_ra_startup_bridge`, `caiso_ra_bridge_decommit`, `caiso_ra_startup_trajectory` = `true` (the other three CAISO RA legs — `_quantity_gate`, `_startup_aware`, `_curtailment_release` — already `false`) |
| arm config validates at the pin (`ScenarioConfig(**keeper 2021 scenario_config, unit_commitment_milp=True, <4 offs>)`) | **validates**; with the gate alone the validator refuses exactly those four fields (verbatim refusal recorded in the session) |
| `uc_*` at the pin | `uc_window_hours` 24 · `uc_lookahead_hours` 12 · `uc_mip_rel_gap` 1e-3 · `uc_window_time_limit_s` 600 · `uc_integer_scope` physics · `uc_noload_source` campd_regression · `uc_boundary_mode` p0_targets · `uc_prefixing` false · `uc_solver_preset` **lean** (UC-SPEED default) |
| CAISO golden (gate off) | **PASS at `ec758d64`** (UC-DESK r03, plan §11: "goldens @ec758d64: PASS NEISO/SPP/ERCOT/SOCO/CAISO"); the golden's main base is `e85705325` (closeout-CAISO-w2 merge, 2026-10-03; SPP PRECOMMIT Addendum B names main's advance `e8570532..d62ae1a7` as what the rebase carried in) |
| `scripts/solve_surface_register.py --diff 566bc8fa… 2f872a62…` | *"336 → 342 names; 1 value moved, 6 added, 0 removed … per-ISO totals: ERCOT 0, **CAISO 0**, MISO 1, PJM 1, NYISO 0, NEISO 0, SPP 1, NWPP 1, SOCO 1"* — the moved value (`NUCLEAR_MONTHLY_CF_BY_YEAR`) re-keys no CAISO year |
| `_ucmilp_compose_span.py` at the pin | present; still lacks `gas_price_override` in `PER_YEAR_FIELDS` (SPP Addendum D.1 gap unchanged) — the scratch-copy workaround is declared in §8 now, not after; the Addendum D.2 respan step is not needed for an unregistered span (§8) |
| `check_bench_freshness.py --iso CAISO` at the pin | **7/7 CAISO bench parts STALE** (builder payload fingerprint unresolvable vs HEAD `1b89b7110328`). Consequence declared in §3: control and arm are scored against the SAME committed parts by the SAME scorer at the pin; the registered 3.17 numbers are printed beside the re-score |
| L1 gate (charter step 0; HANDOFF block D, one bench shard, L1 + January rolled month, Opus) | shard `session_01YCHGbBrjNnfeuoiRcGrDgL` launched 00:46Z at the pin; **result in §5 and Addendum A** — no span shard launches before it reads window 0 Optimal and 31/31 Optimal |

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** CAISO's designated keeper `2026-10-02-closeout-caiso-w1-arm2`, bundle
  `results/calibration/closeout_caiso_w1_a2_span`, seven year-isolated legs 2019–2025 solved at
  `566bc8fa3dd2ad6bdd5e56a2315c744c9be83e07` (`meta.json basis_sha`); its committed `metrics.json` (rubric 3.17),
  `legitimacy_diagnostics.json`, `hourly/*` and `frontend/data/backcast/keepers/CAISO.json` are the control record, and
  the keeper bundle re-scored at the pin by `calibration_verdict.py` (rubric 3.20, zero LP) is the control ladder the arm
  is diffed against (§3).
- **Pin (every shard):** `2f872a62a7cccadb6800555c11a73745dcdb89a4`. `source_revision` is this full SHA, never a branch.
- **Arm — ONE logical delta** (the gate plus the rule-19 substitutions the validator itself names, exact field names from
  the keeper's `run_config.json`):

  ```
  replay_keeper.py results/calibration/closeout_caiso_w1_a2_span --years <y> \
      --set unit_commitment_milp=true \
      --set caiso_ra_mustoffer=false --set caiso_ra_startup_bridge=false \
      --set caiso_ra_bridge_decommit=false --set caiso_ra_startup_trajectory=false
  ```

  Every `uc_*` field stays at its declared default (table in §0) and is **never swept**. `uc_window_time_limit_s` = 600
  (the DESIGN §3 placeholder, as SPP; the L1-month row in §5 is the only wall evidence and sets nothing).
- **D-5 for CAISO (desk-set under the owner's direction; the owner may override):** the arm switches OFF every
  `UC_REFUSED_ALWAYS` field the keeper arms — the RA must-offer bridge and its three legs — because the UC *replaces* the
  bridge (UC-0 FINDING §4: *"the bridge detects P0 runs and floors them; the UC chooses them"*; ASSESSMENT §6 "form
  change"). **Every other floor is KEPT**, mirroring SPP arm 1 so results compare across ISOs. The kept floors, from the
  keeper's D-2 rows (summed over the span): `nuclear_mustrun` 119.4 TWh, `firm_import` 170.2 TWh, `chp_steam` CC_CHP 30.3 /
  CT_CHP 8.3 TWh, `hydro_min_flow` 32.2 TWh. **Stacking risk, named:** SPP showed the UC stacking on a kept *conduct* floor
  (CC energy → coal through `st_gas_mustrun_per_plant`/`coal_mustrun`). CAISO's kept set contains no merchant conduct floor
  on a UC class (no coal, no `cc_mustrun_per_plant`, no `st_gas_mustrun_per_plant`, `caiso_gas_commitment_floor=false`);
  the CHP steam floors are D-2-exempt physical obligations and the CHP classes are not UC classes. The nearest stacking
  channel is therefore the *import ladder* (`firm_import` + the priced DSW/hub ladder): CC energy the UC decommits can be
  served by imports instead; S1/S5 report where it goes. `caiso_ra_min_load_frac` (0.57, measured) stays recorded but is
  dead with the bridge off (read only by the bridge paths in `pipeline/commitment.py`); the UC's CC min-load comes from
  the `uc-params` clean partition (CAMPD plant-basis p5, frozen derive, rule 23) — a disclosed basis change between two
  measured quantities, zero free parameters.
- **Pricing (owner ruling R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC objective;
  make-whole reported in `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (owner ruling R4, D-4):** UC min-load energy is REPORTED under MECH 28 and not budgeted. The scorer at this pin
  still budgets `uc_schedule` energy inside the D-2 share (SPP RESULT §1); a C8 move through MECH 28 is therefore reported
  twice — as scored and with MECH 28 removed — exactly as SPP did.
- **Not a matrix re-test (rule 28).** CAISO's DO-NOT-REDO list (`docs/mechanism-testing-matrix.md` §5.2) carries *"CC
  must-run floors (wrong sign)"*; the UC is not a floor — it may decommit a CC the bridge would have held, and it chooses
  the commitment the bridge only detects — so integer state is new evidence, not a re-test of the floor family. The
  `caiso_ra_mustoffer` family cells are the keeper's (K) and are not re-adjudicated: the arm removes them because the
  validator refuses the stack (rule 19), not because of any evidence about them. The cell this lane feeds is
  `unit_commitment_milp` (minted `U` by UC-1); this lane stamps it from the RESULT as its last commit (charter step 4).
  DO-NOT-REDO honoured: no sub-zonal topology, no export-sink family, no DA/RT two-settlement, no CC winter capability, no
  offer-band retune, no second `--set`.
- **DOF (rule 21):** zero free parameters added. Every UC parameter is measured or published (UC-0 FINDING §5): no-load =
  CAMPD per-unit intercept × delivered fuel (CAISO: 68/66 units fitted, R² 0.98 in 2021; per-year in UC-0 §4), UT = CAMPD
  plant-basis p25 run length, DT = the published class table, start cost = the NREL class table. The keeper's
  `offer_curve_by_group` bands (CC_REGULAR committed 1.0 / econ_low 1.066 / econ_high 1.072 / peak 1.386; no
  `authorized_price_tuning` block) ride unchanged on the non-integer clusters and are zeroed (R3) on the integer ones.

## 2. Target readings (fixed ex ante; bar = half the distance to the gate band, the closeout convention)

Control values are the keeper bundle re-scored at the pin (rubric 3.20) — the registered 3.17 values are in brackets where
they differ. "met" is decided on the composed span's `calibration_verdict.py` output and the zero-LP re-measurement of
UC-0's M1/M3/M4 on BOTH bundles (`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported, same thresholds), so
the starts comparison is apples-to-apples whatever UC-0's own table read.

| # | reading | control (pin re-score) | sign expected | bar (met iff) |
|---|---|---|---|---|
| T1a | C1 CC_REGULAR 2019 (model − actual, grid-delivered) | **+5.63 TWh** FAIL (band ±4.84) [registered +10.19] | negative (CC energy down) | arm ≤ **+5.24 TWh** (moves ≥ 0.40) |
| T1b | C1 CC_REGULAR 2020 | **+13.46 TWh**, share +5.4 pp FAIL (band ±4.60, ±3 pp) [+16.45] | negative | arm ≤ **+9.03 TWh** (moves ≥ 4.43) |
| T1c | C1 CC_REGULAR 2021 | **+6.59 TWh** FAIL (band ±4.83) [+8.11] | negative | arm ≤ **+5.71 TWh** (moves ≥ 0.88) |
| T2 | C3a 2021 mean LMP, RT-covered window (model/actual − 1) | **+12.7 %** (CAVEAT: reference-coverage, in-window band FAIL) [+12.6 % UC-0] | negative (body down) | arm ≤ **+11.35 %** (moves ≥ 1.35 pts) |
| T3 | CC_REGULAR starts per plant-year vs CEMS (UC-0 M1, on-threshold 1 % of available cap; `screen_year` re-run on the keeper bundle in this session, zero LP, 2026-10-10) | model / CEMS: 2019 **7,470 / 2,679** · 2020 **8,078 / 3,160** · 2021 **8,700 / 3,289** · 2022 **10,028 / 3,467** · 2023 **9,528 / 3,222** · 2024 **9,692 / 2,898** · 2025 **9,322 / 2,820** (2.6–3.3×) | down, toward CEMS | arm CC_REGULAR starts ≤ (control + CEMS)/2 in every year: **2019 ≤ 5,075 · 2020 ≤ 5,619 · 2021 ≤ 5,995 · 2022 ≤ 6,748 · 2023 ≤ 6,375 · 2024 ≤ 6,295 · 2025 ≤ 6,071**; met iff every year clears; an overshoot below CEMS (SPP: 0.52–0.77×) is reported as such |
| T4 | share of CC_REGULAR energy inside on-runs shorter than UT (M1 short-on, same re-run) | 2019 13.7 % (6.33 TWh) · 2020 12.8 % (7.62) · 2021 14.6 % (8.37) · 2022 19.4 % (10.19) · 2023 14.7 % (7.46) · 2024 16.2 % (7.17) · 2025 16.6 % (6.34) | falls | sign only; magnitude reported |
| T5 | M4 reserve dormancy (share of hours with model reserve MCP < $1) vs actual, years with an AS reference (same re-run; 2021 coverage 0.50) | model 1.00 vs actual: 2020 0.28 · 2021 0.68 (mean MCP $0 vs $3.0) · 2023 0.51 · 2024 0.69 · 2025 0.61 | falls; mean MCP rises | sign only; magnitude reported |

**Not targets, reported with sign:** M3 low-price-hour ratios model/actual (≤ $15 and < $0; 2021 re-run: 0.528 and 0.61 on 254 / 41 actual hours; UC-0 table 0.53–0.70 and 0.61–0.91 over 2021–2025) — the
UC's no-load cost can move CAISO either way; C3a 2022–2025 (model-high +8.6 / +7.6 / +6.6 / +6.0 %, all PASS) — a body-down
move helps these, a body-up move is the §3 control risk. C3a/C3b 2019–2020 are unscoreable (R-40 reference-coverage caveat,
no measured hourly LMP): no price reading is fixed on them.

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered CAISO year, any criterion, any class row** (`calibration_verdict.py --json`
per-(criterion, key, year) status diff, keeper bundle vs composed span, both scored at the pin). A CAVEAT → FAIL that is
not the attestation artefact (next paragraph) counts as a flip. Years with the least headroom, named now so the reading
cannot be re-interpreted later:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| 2025 | C4 gas NRMSE | 0.283 PASS (≤ 0.30) | **0.017** | the keeper's own standing tripwire (R-14); any re-shaping of CC hours moves it |
| 2022 | C4 gas NRMSE | 0.249 PASS | 0.051 | same |
| 2022 | C3a | +8.6 % PASS (±10 %) | 1.4 pts | model-high: if the UC's no-load cost LIFTS the trough body (fewer low hours), it flips |
| 2023 / 2024 / 2025 | C3a | +7.6 / +6.6 / +6.0 % PASS | 2.4 / 3.4 / 4.0 pts | same direction risk |
| 2021 | C1 CT_PEAKER | +2.52 TWh PASS (band ±4.83) | 2.31 | CC energy the UC decommits can land on CTs |
| 2022 / 2024 / 2025 | C1 CC_REGULAR | +0.95 / −1.67 / −0.36 TWh PASS (bands ±5.01 / ±5.29 / ±5.08) | 4.1 / 3.6 / 4.7 | a large CC shift (SPP moved 5–8 TWh) would flip the model-low years |
| 2023 | C3c | 51 h vs 47 h PASS ([24, 94]) | 24 h | scarcity hours move with commitment |
| 2022 | C3c | 515 h vs 510 h PASS ([255, 1020]) | 260 h | same |
| 2025 | C3c | 0 h vs 8 h PASS (small-count \|Δ\| ≤ 10) | 18 h | same |
| every year | C8 CC_REGULAR forced share | 8.6 / 6.2 / 6.8 / 7.1 / 7.6 / 10.8 / 12.3 % PASS (< 30 %) | ≥ 17.7 pts | the RA-bridge row disappears and MECH 28 appears; reported as scored and with MECH 28 removed (R4) |
| 2021, 2024 | C3c | CAVEAT (0 h vs 27 h; 0 h vs 35 h), ledgered through the keeper's attestation | — | the probe carries no `calibration_attestation.json`, so C6 reads UNATTESTED and these read FAIL: **an artefact, not a flip** (SPP Addendum D.3); the magnitudes are compared directly |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper; no new D-4 FAIL row.

**Benchmark basis, declared.** `check_bench_freshness.py` reads every CAISO part STALE at the pin, and the keeper re-scored at
the pin reads C1 CC_REGULAR +5.63 / +13.46 / +6.59 TWh where its registered record (rubric 3.17) reads +10.19 / +16.45 /
+8.11. Both bundles are scored by the same scorer against the same committed parts, so the flip test is consistent; the
registered-vs-re-scored gap is a CAISO calibration-lane / desk matter (routed in the RESULT), not this lane's to repair, and
no number here is a certified CAISO calibration number (rule 22).

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, CT_PEAKER, ST_GAS) and ISO-wide | 0 (no UC); `ra_mustoffer_bridge` CC 3.7–4.8 TWh/yr (6.2–10.8 %) | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 |
| S2 | starts per plant-year vs CEMS (= T3), plus the engine's own count Σ`v` per cluster from `uc_schedule_<y>.parquet` | T3 row | `screen_year` M1 on both bundles |
| S3 | online capacity vs a measured online series | **no CAISO comparator on disk** (no measured hourly online-capacity-by-fuel series is curated for CAISO; OASIS history is owner-closed, 2026-10-02) — SKIPPED and named; the arm's `online_mw` from `uc_schedule_<y>.parquet` is reported against the keeper's available MW (model-internal) |
| S4 | integer set and fallback shares | UC-0 M6: 32 CAISO plant clusters, 17.2 GW; no-load fitted 68/66 (2021) | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| S5 | where decommitted CC energy goes (class TWh deltas: imports, CT_PEAKER, hydro, storage, CC_CHP) | keeper class sidecars | composed `class_hourly_<y>.parquet` deltas — the CAISO analogue of SPP's CC → coal reading |

## 5. Cost readings (reported; D-2 ceiling 3× is REPORTED as a ratio, never judged here)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all seven years |
| W1-denominator | the keeper bundle records no P0/P1 seconds (`environment` block only). **Declared proxy (SPP §5):** baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line, so ratio = total / (P0 + P1) in one container; the L1 shard's `capture_wall_s` (the keeper 2021 recipe replayed gate-off, P0 + P1) is the one measured CAISO baseline and is printed beside it | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` ÷ Σ_t λ_P1 × load (`hourly/system_<y>.parquet`) | ≤ **2 %** (sanity) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise §6 kill) |

**L1 gate row and shard budget** — Addendum A records the L1 shard's numbers verbatim (window 0 status, 31/31 January
windows, `capture_wall_s`, January wall). Budget per span shard = **ceil(1.3 × (capture_wall_s + 12 × January base wall +
60 s build))** in minutes, written in Addendum A before any span shard launches; if the L1 shard stops without a January
row, the budget is the charter fallback **90 min** and the span does not launch until the desk rules on the missing gate.
One shard commit ≤ 20 min of runtime is read as rule 32's commit grain, not the solve wall (the SPP shards ran 33–45 min
end to end under the same rule); a shard approaching the budget with no artifact stops and reports.

## 6. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's "no incumbent" hard stop): an engine
   defect, routed to UC-DESK, never a tuning invitation.
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed runs of the
   same recipe-year. Exercised only if a relaunched shard (PENDING > 45 min rule) and its predecessor both complete;
   otherwise recorded "not exercised".
3. **A control flip** (§3) in any registered year.

## 7. Verdict rule (fixed) and the D-6 card

- **K candidate** — T1a–T1c and T2 met, T3 met in every year, T4/T5 signs right, no kill, every leg Optimal: recommend
  the owner's D-6 card read "promote on structure"; the lane never promotes (rule 31; UC-4 is the desk's slot).
- **R** — any target reading moves the wrong way past its control (C1 CC_REGULAR 2019–2021 up, C3a 2021 up, CC starts up),
  or any kill fires.
- **I** — no kill, no wrong-sign move, but |Δ| below the bar on T1–T3 (GATESPEC §7.2: "the relaxation was already tight
  here" is a finding).
- Mixed: the verdict is the worst of the target rows, stated row by row. The determination (`iso_determination`) is
  reported, not gating: CAISO is NOT-YET on C1 2019–2021 and C4 2019–2021 and stays so unless every failing row clears,
  which no reading here predicts (C4 is not a target: the UC changes hourly CC shape, so its direction is reported).
- The RESULT carries the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve plan (rules 16, 32–36) and the composition workaround (declared now)

- **Seven shards, 2019–2025**, one year each, `claude/ucmilp-caiso-<y>`, out-dir `results/calibration/ucmilp_caiso_<y>`,
  prompts from `scripts/shard_prompt.py --iso CAISO --all-years --sha 2f872a62a7cccadb6800555c11a73745dcdb89a4 --lane
  ucmilp-caiso --bundle results/calibration/closeout_caiso_w1_a2_span --set unit_commitment_milp=true --set
  caiso_ra_mustoffer=false --set caiso_ra_startup_bridge=false --set caiso_ra_bridge_decommit=false --set
  caiso_ra_startup_trajectory=false --budget <Addendum A> --note "ucmilp-caiso: UC A/B"`, each appended with: confirm
  `hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json` and `hourly/unit_marginal_<y>.parquet`
  are in the pushed tree; report the GATESPEC §6.1 wall row (the `log_year_phase_timing` line + `uc_solve_log_<y>.json
  summary`). Committed as `shard-prompts-ucmilp-caiso.txt`. `create_session` per year: `source_revision` = the pin, model
  `claude-opus-5-5`, tag `ucmilp:UC-2-CAISO-shard`. PENDING > 45 min: archive and relaunch.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_caiso_<y>` non-empty; check out; verify
  `dispatch/<y>_P1.parquet` + the three UC files; THEN `archive_session` (rule 33).
- **Compose and score, zero LP, at the pin.** `scripts/probes/_ucmilp_compose_span.py` at the pin aborts on CAISO's per-year
  `gas_price_override` (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52 $/MMBtu, the only per-year field beside `weather_year`)
  and has no `_respan_shared_inputs`. **Workaround, declared ex ante (SPP Addendum D):** a scratch copy of the composer in
  the session scratchpad (never under `scripts/`, never committed) with `gas_price_override` added to `PER_YEAR_FIELDS` —
  the CAISO keeper's own composer `_closeout_caiso_w1_compose_span.py` declares `YEAR_INDEXED = {"weather_year",
  "gas_price_override"}`; everything else is the committed script's logic. The keeper composer's `_respan_shared_inputs`
  is NOT applied: it rebuilds the benchmark frames from `data/raw` for `--restore-shared-inputs`, which only a registration
  invokes, and this span is never registered; `calibration_verdict.py` and `legitimacy_diagnostics.py` read the committed
  bench parts, not the frames. The composite's `meta.json` therefore keeps the first leg's recorded one-year frame hashes,
  and the RESULT says so (a truthful record beats a re-pointed one). Then `calibration_verdict.py` (+ `--json`),
  `legitimacy_diagnostics.py` (regenerated, never copied), and `screen_year` M1/M3/M4 on both bundles. The parent runs no LP.
- **No dashboard registration** (desk ruling 2026-10-10 on the SPP probe: audit E13 admits only keepers or folded runs); the
  slim span (hourly sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`, `uc_solve_log_<y>.json`,
  regenerated `legitimacy_diagnostics.json`, `metrics.json`; no `dispatch/`) lands under
  `docs/records/caiso/ucmilp/data/ucmilp_caiso_span/`; the full leg bundles stay on the shard branches by SHA (rule 31:
  nothing deleted; rule 33: transport, not storage). Never promote. One PR; UC-DESK merges.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-caiso-ab-<date>.md`: gate table first, wall rows, every reading answered,
  kills checked, verdict, D-6 card, where each bundle is and what a promotion costs, `## Log entry`); the CAISO
  `unit_commitment_milp` cell stamped as the last commit after rebasing; message UC-DESK with the gate table, then the wall rows.

## 9. G-DRIFT — main at the pin vs the keeper's basis `566bc8fa` (zero LP; rule 29(b): no control solve)

The keeper's basis `566bc8fa` is an ancestor of the pin (merge-base = `566bc8fa` itself; 687 main-side commits). Two tiers:

1. **`566bc8fa` → `e85705325` (the golden's main base): INERT for CAISO by solve.** The gate-off CAISO golden replay at
   `ec758d64` (= `e85705325` + the UC-1 engine commits `ca33a51f0`…`d3aa55ed6`) reproduced the keeper (UC-DESK r03). That
   covers every main-side solve-path change up to that base (the 2026-10-02/03 closeout commits: dispatched-bin outage
   denominator, SPP-107/108, SOCO/NWPP/nuclear rows, the inert vectorization pass, `634506afc` flipped-default replay
   posture, `7b1aa134e` CAISO AS drops by dated window, closeout-CAISO-w2's default-off arm) and the engine's one gated hunk in
   `pipeline/solve.py`.
2. **`e85705325` → `2f872a62` (after the golden): every non-merge solve-path commit, classified on the objects.**

| commit | content | CAISO classification |
|---|---|---|
| `4e7b54d58`, `1c0a8b8f1`, `84e928efd`, `5dc76955d` | UC-1 checkpoint fix; UC-1-FIX (Rajan–Takriti history in rows, look-ahead min-down guard); UC-SPEED profile + `uc_solver_preset` field; lean path | files: `model/uc/*`, `pipeline/uc.py`, `scripts/lib/uc_bench.py`, the `uc_solver_preset` field (read only under the gate) — **LIVE on the gate-on path only: this IS the arm** |
| `c0f786715` closeout-CAISO-w6 | `caiso_chp_btm_measured: bool = False`; `data/chp.py` + `fleet/assembly.py` under `getattr(config, "caiso_chp_btm_measured", False)`; `paths.py` + raw `chp_btm_share_measured_CAISO.csv`, `eia-923-disposition/` read only under the flag | **INERT**: default off, ABSENT from the keeper recipe, unarmed in `iso_configs` (its CAISO `_caiso_config` diff vs `566bc8fa` is empty) |
| `6cf95135b` closeout-ERCOT-w6 | `ercot_chp_btm_measured` (ERCOT-scoped) | INERT |
| `9d06ad034` closeout-ERCOT-w3 | `coal_perplant_cliff_split`, ERCOT-gated | INERT |
| `6cfad57bb` closeout-SOCO-w3 | `diagnostic_coal_metered_online_floor` (never promotable); `pipeline/commitment.py` wrap is the identity when off; MECH 29 id | INERT |
| `e64b41c22` closeout-SOCO-w3 | `run_calibration_full.py` `--rebuild-benchmark` reader (`mustrun_chp_btm_holdout` detection) | not the solve path; INERT |
| `41a9e2d9c`, `bc163dbc8` closeout-PJM-w3 | `nuclear_winter_capability_basis` PJM-gated; `NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR` added, `NUCLEAR_MONTHLY_CF_BY_YEAR` re-keys MISO/NWPP/PJM/SOCO/SPP only | INERT (solve surface: CAISO 0) |
| `72ed3d857` closeout-MISO-w3 | `miso_seam_neighbour_hourly_full_span`, `interchange/miso.py` + `spec.py` MISO tables | INERT |
| `90cea7206` closeout-PJM-elliott | `pjm_elliott_measured_outage_overlay`, `fleet/arrays.py` under `_iso == "PJM"` | INERT |
| `440ad1441` NWPP-NEXT-27 | `nwpp_path76_served_schedule`; `eia930/demand.py`, `envelopes.py`, `ttc.py`, `runner.py` hunks under `iso == "NWPP"` | INERT (CAISO reads `eia930/*` but every hunk is NWPP-guarded, verified on the diff) |
| `data/dictionary`, `uc-params.schema.yaml` | the UC datatype contract | gate-on only |

Tooling byte-identity: `shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `replay_keeper.py` are
used AT the pin for both arms; the control is scored by the pin's scorer (§3). `replay_keeper` handles the one field the
keeper records that the pin deleted (`unit_outage_dispatched_bin_live_denominator`, rule 26; recorded `False`, the
inert polarity — the replay guard's declared case). **Nothing is LIVE for CAISO outside the UC stage.**

## 10. DO NOT REDO

`docs/mechanism-testing-matrix.md` §5.2 DO-NOT-REDO (sub-zonal topology, export-sink family, DA/RT two-settlement, CC
must-run floors, CC winter capability); `ASSESSMENT-caiso261-panoche-instrument-search` (no CT floor, pin or window for
Panoche); no `uc_*` value other than the declared defaults; no second `--set`; no control solve; no NEISO/NYISO span.
