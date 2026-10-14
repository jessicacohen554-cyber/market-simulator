# PRECOMMIT — UC-3-CAISO: the CAISO UC A/B relaunched at the clean engine (uc-1.4), 2026-10-14

**Written and pushed BEFORE any shard of this lane exists.** Lane `UC-3-CAISO` (Opus), branch `claude/ucmilp-3-caiso-ab` off the pin.
Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on the owner's ruling of 2026-10-14 (*"Go with your recommendations"*:
decision 7 = relaunch every UC-2 ISO at uc-1.4; the CAISO UC-2 `R` is **held, not recorded**). This file is an addendum-by-reference to
`PRECOMMIT-ucmilp-caiso-ab-2026-10-10.md` (UC-2-CAISO, "the prior PRECOMMIT"): **everything in its §§1–7 stands unchanged except the pin,
the engine it carries, and the budget.** Nothing below is moved after a number comes in (GATESPEC §7.1).

**Why.** Every UC-2 verdict was solved before uc-1.3 and carries engine defect 6 (the cluster floor spread pro rata across offer tranches;
FINDING-ucmilp-fix4 §0) and, for CAISO, the uc-1.1 engine (pre defects 4–5, ruling (a), FIX-3, slim window). Rule 1 [R-STRUCT]: an R
reached through an engine defect is not a structural rejection. This lane produces the clean A/B.

## 0. Preconditions (zero LP, checked before this file was written)

| check | result |
|---|---|
| `HEAD` == pin `580c4fbf80b8bf970bc19acf14f614728de9d401` (main at #7239; engine uc-1.4 = #7237 merit fill + #7238 P1 floor `mlf·p̄·a·u`) | yes |
| `grep -c unit_commitment_milp scenarios.py` | 7 |
| arm validates at the pin (`ScenarioConfig(**keeper scenario_config, unit_commitment_milp=True, 4 RA offs)`) | **validates**; gate alone is refused naming exactly the same four `caiso_ra_*` fields as at `2f872a62` |
| `uc_*` at the pin | `uc_window_hours` 24 · `uc_lookahead_hours` 12 · `uc_mip_rel_gap` 1e-3 · `uc_window_time_limit_s` 600 · `uc_integer_scope` physics · `uc_noload_source` campd_regression · `uc_boundary_mode` p0_targets · `uc_prefixing` false · `uc_solver_preset` lean · **`uc_slim_window` true** (new since `dc3860be`, UC-SLIM #7222: an exact reduction, born at its default and dropped from the cache key) |
| `solve_surface_register.py --diff dc3860be 580c4fbf` | *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"* |
| byte-identical `dc3860be` → pin | `shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `replay_keeper.py`, `run_calibration_full.py`, `run_calibration.py`, `iso_configs.py`, `pipeline/solve.py`, `pipeline/commitment.py`, `_ucmilp_benefit_screen.py`, `frontend/data/backcast/keepers/CAISO.json`; `results/calibration/closeout_caiso_w1_a2_span/**` 0 files differ |
| defect-6 footprint in the UC-2 CAISO arm (uc-1.1 legs, zero LP, `data/fix4/fix4_readings.py` on the committed slim span) | forced CC/ST_GAS `_peak*` energy **0.54 / 0.76 / 0.66 / 0.63 / 0.68 / 0.57 / 0.52 TWh** (2019–2025), median offer $47–111/MWh; uplift 0.05–0.20 % |

## 1. Control, pin, arm (prior PRECOMMIT §1, unchanged but for the pin)

- **Control (rule 29(b), no control solve):** keeper `2026-10-02-closeout-caiso-w1-arm2`, bundle `results/calibration/closeout_caiso_w1_a2_span`,
  re-scored at the pin by the pin's scorer (byte-identical to the scorer UC-2 used, so the control readings in prior §2–§3 are the control here).
- **Pin:** every shard's `source_revision` = the full 40-char SHA of this branch's head after this PRECOMMIT is pushed (= `580c4fbf` + records only).
- **Arm (verbatim the prior arm):** `replay_keeper.py results/calibration/closeout_caiso_w1_a2_span --years <y> --set unit_commitment_milp=true
  --set caiso_ra_mustoffer=false --set caiso_ra_startup_bridge=false --set caiso_ra_bridge_decommit=false --set caiso_ra_startup_trajectory=false`.
  Every `uc_*` at its registry default (table above), never swept. Every other floor kept (desk D-5 for CAISO). Pricing R3, rule-20 reporting R4,
  zero free parameters (rule 21) — all as prior §1.

## 2. G-DRIFT `dc3860be` → `580c4fbf` (zero LP; rule 29(b))

Non-merge commits touching `src/`, `scripts/`, `configs/`, `data/dictionary` between the pins (16 files, +1,652/−232):

| commit(s) | content | CAISO classification |
|---|---|---|
| `6e8afcc6`, `3572bf95` UC-SLIM | `model/uc/slim.py` (new), `uc_slim_window` field (default True, cache-key optional) | **LIVE, gate-on only** (the arm); exact by construction (equivalence gate in its FINDING) |
| `adb07411` defect 4 | `model/uc/window.py`: monthly-banded import links pinned to P0 flows inside a window | LIVE, gate-on only |
| `e8507b79`, `f2c7166a`, `e4a57362`, `7688a68a` uc-1.2 | infeasible-window diagnostics; min-down guard reads the pinned fleet (defect 5); ruling (a) all-budget-pinned clusters carry no integer; slim expand fill order; per-window log | LIVE, gate-on only |
| `121cee93` FIX-3 | `scripts/lib/uc_params/*`, `data/campd_crosswalk.py` (`crosswalk_of_record` refactored onto `load_crosswalk`, same rows; new `camd_to_eia_plant` used only by the uc-params derive), `clean_profiles.py` uc-params raw inputs | LIVE, gate-on only (uc-params partition re-keyed by EIA plant code; the gate-off path reads `crosswalk_of_record`, whose output is unchanged) |
| `4d13594e` uc-1.3, `936a4b43` uc-1.4 | `pipeline/uc.py` merit floor fill, input-digest reuse, P1 floor `mlf·p̄·a·u`; `model/uc/uplift.py` `uplift_from_bundle` deleted | LIVE, gate-on only — the fix this lane exists to test |
| `7c8b0325` | data-dictionary rows reverted | not the solve path |
| `scripts/probes/_ucmilp_compose_span.py`, `uc_bench.py`, `bench_uc_ladder.py` | composer/bench tooling | not the solve path; composer used zero-LP by the parent |

**Nothing LIVE for CAISO outside the UC stage**; the gate-off keeper path is untouched (`pipeline/solve.py`, `commitment.py`, `iso_configs.py`
byte-identical; solve surface unmoved). The control stands without a solve.

## 3. Readings, kills, verdict — prior PRECOMMIT §§2–7, unchanged, restated for launch

- **Targets (prior §2):** T1a/b/c C1 CC_REGULAR 2019/2020/2021 arm ≤ +5.24 / +9.03 / +5.71 TWh; T2 C3a 2021 ≤ +11.35 %; T3 CC_REGULAR starts ≤
  5,075 / 5,619 / 5,995 / 6,748 / 6,375 / 6,295 / 6,071 (2019–2025); T4, T5 sign only.
- **Control (prior §3):** no PASS → FAIL flip on any year, criterion or class row (keeper re-scored at the pin vs composed arm span, same scorer);
  the C6/attestation artefacts (C3c 2021/2024, C3a/C3b 2021 CAVEAT → FAIL) are artefacts, compared by magnitude; every leg P1 Optimal; unserved
  ≤ +500 MWh any year; no new D-4 FAIL row.
- **Kills (GATESPEC §5, prior §6):** #1 an infeasible window / no incumbent (engine defect → stop that leg, report to UC-DESK with a repro, never
  patch `src/` here); #2 non-deterministic schedule (exercised only if a leg is solved twice); #3 a control flip.
- **Verdict (prior §7):** K candidate iff T1a–c, T2, T3 all met, T4/T5 signs right, no kill; R on any wrong-way target or any kill; I on
  no-kill/no-wrong-way but sub-bar moves; mixed = worst row, stated row by row.
- **Reported per year, control → arm (charter list):** C1, C3a, C3b, C3c, C4, C8 as scored and with MECH 28 removed (R4), unserved MWh, uplift %
  of Σλ·load, CC_REGULAR / ST_GAS / coal starts vs CEMS (`screen_year` M1, both bundles), **forced `_peak*` TWh** (`data/fix4/fix4_readings.py`,
  zero LP; expect ≈ 0), wall ÷ (P0+P1) (prior §5 proxy), integer clusters of the gate set, time-limit hits; plus S5 (where CC energy goes).
- **Diagnostic, not gating:** the uc-1.4 arm vs the UC-2 uc-1.1 arm (committed slim span) per year — the engine delta in isolation. Any
  price move is diagnosed by sign and hour class (which hours, which classes marginal) from the bundles, zero LP. No tuning of anything.

## 4. Expectation, written before any number (so it cannot be fitted afterwards)

CAISO's defect-6 footprint was small (§0: ≈ 0.5–0.8 TWh/yr of forced peak-tranche CC energy at $47–111/MWh, uplift ≤ 0.2 %), against the
8–10 TWh/yr CC decommitment and the $3–7/MWh body rise UC-2 measured. The UC-2 reading — the RA bridge held CC online in the trough and set
trough prices with it; the UC removes both — is therefore **not expected to be a defect-6 artefact in CAISO**. Expected: forced `_peak*` → ≈ 0;
CC energy slightly lower than UC-2 (the forced peak energy goes); the C3a/C3b direction unchanged; the 12 UC-2 control flips largely
reproduced. If the gates move materially toward the control, the engine delta (uc-1.2 ruling (a), FIX-3 uc-params re-keying, defects 4–5) is
the first place to look, and the diagnostic row above isolates it.

## 5. Solve plan (rules 16, 32–36)

- Seven shards 2019–2025, one year each, prompts from `scripts/shard_prompt.py --iso CAISO --all-years --sha <branch head> --lane ucmilp3-caiso
  --bundle results/calibration/closeout_caiso_w1_a2_span` + the five `--set` above, `--budget 180`, plus the UC additions (four UC files in the
  pushed tree; §6.1 wall row; any file > 100 MB split into parts with sha256 recorded before commit). Out-dir `results/calibration/ucmilp3_caiso_<y>`,
  branch `claude/ucmilp3-caiso-<y>`. Committed as `shard-prompts-ucmilp3-caiso.txt`.
- **Budget 180 min LP wall per shard** (charter ceiling 720): UC-2 CAISO LP walls were 39–82 min; uc-1.3+ on ERCOT ran faster than uc-1.2. A
  budget is a cost line, not a solve setting; a budget stop is reported, and at most one relaunch at a larger budget changes nothing else.
- On each report: fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp3_caiso_<y>` non-empty; check out; verify `dispatch/<y>_P1.parquet` +
  the four UC files; then archive (rule 33).
- Compose + score zero LP at the pin (`_ucmilp_compose_span.py`; if it still lacks `gas_price_override` per year, the prior §8 scratch-copy
  workaround applies verbatim). Local registration only to feed the scorer, removed before commit; nothing registered or promoted (E13).
- Deliver: RESULT + slim span under `docs/records/caiso/ucmilp/` (`data/ucmilp3_caiso_span/`), the CAISO `unit_commitment_milp` cell stamped
  from the RESULT, one PR to main (UC-DESK merges).

## Addendum A (2026-10-14 ~12:55Z, before any uc-1.5 number of this lane exists) — relaunch at engine uc-1.5

**Why.** UC-DESK (12:46Z): engine defect 7 — the UC objective paid integer clusters' no-load twice (once explicitly, once inside the
average-rate heat rate) — is fixed in #7246 (`FINDING-ucmilp-fix5-cost-basis-2026-10-14.md`; CAISO 2023: $307 M, 12.4 % of CC energy cost).
The uc-1.4 `R` above (RESULT, PR #7243) is confounded by it (rule 1 [R-STRUCT]). Branch `claude/ucmilp-3-caiso-ab-uc15`, fresh from the pin.

**Pin: `2dd69d5aa936547b402a1ba54d2eba57e759b7e7`** (main at #7246). Arm, readings (UC-2 PRECOMMIT §§2–7), kills, verdict rule, `uc_*`
defaults and the five `--set` values are UNCHANGED. The pin is the only change. Budget 180 min LP per shard (charter ceiling 720).

**G-DRIFT `580c4fbf` → `2dd69d5a` (zero LP).** Two non-merge commits touch code:

| commit | content | CAISO classification |
|---|---|---|
| `2dd69d5a` uc-1.5 (#7246) | `model/uc/params.py` `incremental_energy_cost` (integer members' UC energy = `mc_base` less no-load heat per MWh at full output); `pipeline/uc.py` uses it in the window objective, the boundary targets and the uplift cost side; `UC_ENGINE_VERSION` uc-1.5 | **LIVE, gate-on only** — the fix under test |
| `a81b9683` UC-BANDS-ERCOT 1a (#7242) | new `scripts/data/derive_ercot_sced_uc_bands.py`; `scripts/lib/uc_bench.py` 3 lines | INERT: an ERCOT derive script and the bench harness; no solve-path import, no registry field |

`solve_surface_register.py --diff 580c4fbf 2dd69d5a`: *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*.
Byte-identical between the pins: `shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `replay_keeper.py`,
`run_calibration_full.py`, `run_calibration.py`, `iso_configs.py`, `scenarios.py`, `pipeline/solve.py`, `pipeline/commitment.py`,
`_ucmilp_compose_span.py`, `keepers/CAISO.json`; the keeper bundle 0 files differ. The control stands without a solve (rule 29(b)).

**Reused leg (declared now): 2023 = FIX-5 repro `claude/ucmilp-fix5-caiso-2023` @ `a2635bd6`**, solved at `f92d01ea` (the #7246 head before
merge). G-DRIFT `f92d01ea` → `2dd69d5a`: `git diff --stat` over `src/ scripts/ configs/` is **empty** → INERT. Its `run_config.json`
`scenario_config` is identical, field by field, to this lane's uc-1.4 2023 leg recipe (diff = {}); engine `uc-1.5`; clean tree; 0 time-limit
hits. So **six new shards** (2019, 2020, 2021, 2022, 2024, 2025) at the pin, and 2023 is taken from `a2635bd6`.

**Reported in the RESULT addendum:** the §3 per-year list control → uc-1.4 → **uc-1.5**, the same verdict rule against the control, and the
price diagnosis (imports, CT, hydro water value by hour class; zero LP). Expectation, written before the numbers: the double-counted no-load
made committed CC look dearer than it is, so uc-1.5 should keep more CC online. The FIX-5 2023 repro recovered 5.3 of 8.2 TWh. If that
holds in every year, the C1 CC_REGULAR 2022–25 flips may clear, and C1 CC_REGULAR 2019–21 may re-open on the over-run side. The price
direction is the open question.
