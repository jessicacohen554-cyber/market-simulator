# PRECOMMIT — UC-4-CAISO: arm U4 (UC on uc-1.7 + DA-forecast commitment + reserve co-opt with the u-gate), every CAISO year, 2026-10-15

**Written and pushed BEFORE any shard of this lane exists.** Lane `UC-4-CAISO` (Opus), branch `claude/ucmilp-4-caiso` off the pin.
Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) at r14 (`docs/uc-milp-program-plan-2026-10.md` §11 r14, §12 row UC-4-CAISO; PR #7265).
Protocol: GATESPEC §5 (kills), §6.1 (wall row), §7 (honesty). Structure, readings and verdict rule are inherited from
`PRECOMMIT-ucmilp-caiso-ab-2026-10-10.md` §§2–7 ("UC-2 §n") and `PRECOMMIT-ucmilp3-caiso-ab-2026-10-14.md` (+ Addenda A–B). **One arm, U4.
No control solve (rule 29(b)). No tuning; nothing below is moved after a number comes in.**

## 0. Preconditions (zero LP, this session)

| check | result |
|---|---|
| `HEAD` == pin `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (main at #7260, engine **uc-1.7**) | yes (main has since moved to `ca90d2e8` = #7265, docs only; not chased) |
| U4 recipe validates at the pin, every year 2019–2025 (keeper `run_config_<y>.json` `scenario_config` + the §1 `--set` list) | **validates** (7/7) |
| U4 **without** `caiso_scarcity_pricing=false` | **refused**, 7/7: *"caiso_scarcity_pricing and caiso_reserve_coopt are mutually exclusive (rule 19 — one mechanism per phenomenon)"* — see §1.2 |
| `solve_surface_register.py --diff 2dd69d5a 7dbfe20f` | *"342 → 345 names; 0 value(s) moved, 3 added, 0 removed … NO VALUE MOVED"* (added: `COMMITMENT_DF_DATA_ERROR_FRACTION`, `COMMITMENT_DF_SEASON_OF_MONTH`, `VLR_GROUP_MIN_COMMITTED_UNITS`) |
| CAISO EIA-930 day-ahead forecast present for every year (`commitment_demand.ba_forecast_error_mw('CAISO', y)`) | yes, 7/7 (table §1.1) |
| `_ucmilp_compose_span.py` at the pin | still lacks `gas_price_override` in `PER_YEAR_FIELDS` → the UC-2 §8 scratch-copy workaround applies verbatim (declared now) |

## 1. Control, pin, arm

- **Control (rule 29(b)):** keeper `2026-10-02-closeout-caiso-w1-arm2`, bundle `results/calibration/closeout_caiso_w1_a2_span` (legs solved at
  `566bc8fa`), re-scored at the pin by the pin's `calibration_verdict.py`. Same control as UC-2/UC-3.
- **Pin:** every shard's `source_revision` = the full SHA of this branch's head after this file is pushed (= `7dbfe20f` + records only).
- **Arm U4 — exact recipe** (`replay_keeper.py results/calibration/closeout_caiso_w1_a2_span --years <y>` plus):

  ```
  --set unit_commitment_milp=true
  --set caiso_ra_mustoffer=false --set caiso_ra_startup_bridge=false
  --set caiso_ra_bridge_decommit=false --set caiso_ra_startup_trajectory=false
  --set uc_commitment_demand_source='"da_forecast"'
  --set energy_reserve_coopt=true --set caiso_reserve_coopt=true
  --set caiso_scarcity_pricing=false
  ```

  Every other `uc_*` field at its registry default (`uc_window_hours` 24 · `uc_lookahead_hours` 12 · `uc_mip_rel_gap` 1e-3 ·
  `uc_window_time_limit_s` 600 · `uc_integer_scope` physics · `uc_noload_source` campd_regression · `uc_boundary_mode` p0_targets ·
  `uc_prefixing` false · `uc_solver_preset` lean · `uc_slim_window` true), never swept. Every other keeper field unchanged (incl.
  `caiso_reserve_online_scoped=false`, `caiso_commitment_posture=false`, `caiso_locational_as_families=false`, `scarcity_pricing_enabled=true`).

### 1.1 What U4 adds over the UC-3 arm (each landed on `main`, each admitted by CAISO)

| mechanism | field / epoch | CAISO admits? | note |
|---|---|---|---|
| UC on engine uc-1.7 | `unit_commitment_milp` | yes (UC-2/3 arm) | uc-1.6 u-gate, uc-1.7 commitment demand |
| per-unit `ut_h` / `dt_h` | uc-params epoch 2026-10-15a (#7262) | yes, automatic (data, not a field) | rule-23 derivation-defect fix; plant-basis → per-unit CAMPD runs |
| per-unit `mlf` on CEMS full-hours | uc-params epoch 2026-10-15b (#7264) | yes, automatic | UC-3 2019 CC mlf was 0.259 (plant basis, ≈1/n of a unit's minimum) |
| DA-forecast commitment demand | `uc_commitment_demand_source="da_forecast"` (r13 ruling 1) | yes | P1 still clears on actual load (rule 4) |
| reserve co-opt + u-gate | `energy_reserve_coopt` + `caiso_reserve_coopt` (desk charter: "the u-gate needs co-opt; record it as part of the arm") | yes | uc-1.6 `reserve_headroom_u_terms` covers the per-generator joint P+R pool rows CAISO builds |
| SPP spin share | `spp_spinning_reserve_share` | **no** (SPP-only; RSG p.5) | not armed |
| MISO VLR pocket | `vlr_pocket_commitment` | **no** (MISO-only) | not armed |

Measured commitment-demand increment, EIA-930 CISO DF − actual (MW, model hours; QA-dropped hours contribute 0) — written now, before any solve:

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| mean | +586 | +124 | −179 | −416 | −525 | −1,089 | −1,555 |
| p95 | +3,189 | +1,558 | +955 | +1,663 | +2,157 | +1,897 | +1,427 |
| QA-dropped h | 45 | 4 | 5 | 3 | 2 | 62 | 178 |

Rule-14 misalignment, documented (module docstring of `data/commitment_demand.py`): the CAISO keeper arms `caiso_demand_clock_realign`,
`caiso_supply_consistent_demand` and `caiso_tac_shares_standard_time`; the increment rides the EIA-930 frame clock (≤ 1 h offset) and the
default TAC split. The system total of the increment is unaffected.

### 1.2 The scarcity-overlay substitution (rule 19; validator-forced, not a choice)

The keeper prices CAISO reserve scarcity with the **post-solve overlay** (`caiso_scarcity_pricing=true`, cell `ordc_scarcity_overlay` K).
The charter arms the **in-LP co-opt** (`caiso_reserve_coopt`). Both price the same phenomenon, and the validator refuses the pair.
`runner.py` already skips the overlay whenever `energy_reserve_coopt` is on (`... and not energy_reserve_coopt`). So setting
`caiso_scarcity_pricing=false` only states what the code does anyway. It is the same rule-19 substitution as the RA bridge off. Consequences,
named now:
- the scored price loses the overlay adder in every hour, and gains the co-opt's shortfall duals (BAL-002-WECC-3 requirement, tariff
  §27.1.2.3.5 curves) wherever the u-gated pools run short;
- C3c (scarcity hours) is the criterion most exposed; C3a moves by the overlay's mean adder, in either direction;
- **rule 28 note:** CAISO `energy_reserve_coopt` reads `I` (caiso-144, dormancy). The new evidence that justifies arming it again is the
  uc-1.6 u-gate: an offline integer cluster no longer backs reserve. That is a different object from the ungated pergen pool caiso-144 judged.
  The verdict here is the UC arm's. It does not re-adjudicate the `energy_reserve_coopt` or `ordc_scarcity_overlay` cells.

### 1.3 DOF (rule 21)

Zero free parameters added. Commitment demand = measured EIA-930 DF. Reserve requirement and curves = NERC/tariff. `ut_h`/`dt_h`/`mlf` =
per-unit CAMPD, frozen derives (rule 23, epochs 15a/15b). Offer bands = the keeper's, zeroed on integer clusters (R3). No
`authorized_price_tuning` block.

## 2. G-DRIFT vs the keeper (zero LP; rule 29(b))

Chain of record, keeper basis `566bc8fa` → pin: `566bc8fa → 2f872a62` (UC-2 §0: CAISO 0 values moved; golden PASS at `ec758d64`) →
`dc3860be` → `580c4fbf` (UC-3 §2) → `2dd69d5a` (UC-3 Addendum A): in every hop, nothing is LIVE for CAISO outside the UC stage. This hop:

| commit | content | CAISO classification |
|---|---|---|
| `1aec8c4e` uc-1.6 | `model/uc/window.py` `reserve_headroom_u_terms`; `pipeline/uc.py` | LIVE, gate-on only (the u-gate; no-op without co-opt) |
| `3b96390d` UC-DATA-UT | uc-params `ut_h`/`dt_h` per unit; `solve_surface.py` epoch 15a; `cache.py` docstring; `model/uc/params.py` | LIVE, gate-on only (the epoch `requires` the UC gate; uc-params is read only by the UC stage) |
| `01b90bd0` UC-DATA-UT (2) | uc-params `mlf` per unit; epoch 15b | LIVE, gate-on only |
| `3a55fa75` VLR | `model/uc/pocket.py`, window rows, `vlr_pocket_commitment` (default off, MISO data) | INERT for CAISO (field off; no CAISO pocket groups) |
| `72c017d6` SPP-SPIN | `reserves/spec.py` (SPP design only), `lp/model.py` (`reserve_synchronized=None` default; guard only), `pipeline/solve.py` (runs only when the UC stage returns overrides), `pipeline/uc.py` | INERT for CAISO (SPP-only field; `synchronized_reserve_overrides` returns `{}` without a synchronized class) |
| `7dbfe20f` uc-1.7 | `data/commitment_demand.py` (new); `eia930/demand.py` (`load_zone_weights` extracted, same code path, same call); `pipeline/uc.py`; registry +2 constants | `eia930/demand.py`: INERT (pure extraction, identical arguments and arithmetic); the rest LIVE, gate-on and source-on only |

**Nothing LIVE for CAISO on the gate-off keeper path.** The control stands without a solve.

## 3. Readings, kills, verdict (fixed now)

**Targets (UC-2 §2, unchanged):** T1a/b/c C1 CC_REGULAR 2019/2020/2021 ≤ +5.24 / +9.03 / +5.71 TWh; T2 C3a 2021 ≤ +11.35 %; T3 CC_REGULAR
starts ≤ 5,075 / 5,619 / 5,995 / 6,748 / 6,375 / 6,295 / 6,071 (2019–2025); T4 sub-min-up CC energy share falls (sign); T5 reserve dormancy
falls / mean MCP rises (sign). The keeper's T5 dormancy is 1.00 because it carries no co-opt; U4's MCP is the co-opt's own reserve dual.

**Control readings (UC-2 §3, unchanged):** no PASS → FAIL flip on any year, criterion or class row (keeper re-scored at the pin vs the composed
U4 span, same scorer, same committed bench parts). Attestation artefacts are compared by magnitude, not counted as flips: C6 UNATTESTED,
C3c 2021/2024, C3a/C3b 2021 CAVEAT → FAIL. Every leg's P1 must be Optimal. No new D-4 FAIL row.
**Unserved energy ≤ keeper + 500 MWh in every year** (keeper: 0 MWh every year).

**Kills (GATESPEC §5; any one ⇒ record and stop, no re-tune, no second arm):**
1. An infeasible window or "no incumbent". This is an engine defect: stop that leg and report a repro to UC-DESK. Never patch `src/`.
2. A non-deterministic schedule. Exercised only if a year is solved twice to completion.
3. A control flip (as above), including unserved > keeper + 500 MWh.

**Verdict (UC-2 §7, unchanged):**
- **K candidate** iff T1a–c, T2 and T3 are all met, T4/T5 signs are right, no kill fires, and every leg is Optimal.
- **R** on any wrong-way target or any kill.
- **I** if there is no kill and no wrong-way move, but the moves are sub-bar.
- Mixed rows take the worst row, stated row by row.

The lane never promotes (rule 31; D-6 is the owner's).

**Reported per year, control → UC-3 arm (uc-1.5, committed slim span `data/ucmilp15_caiso_span/`) → U4.** Not gating unless named above.
- C1 (every class row), C3a, C3b, C3c, C4, C8. C8 is reported both as scored and with MECH 28 removed (R4).
- Unserved MWh.
- Uplift % of Σλ·load (W3 ≤ 2 % sanity).
- **CC_REGULAR and ST_GAS starts ÷ CEMS**, from `screen_year` M1 on both bundles, same thresholds.
- Forced `_peak*` TWh (expect 0).
- Reserve: mean MCP, dormancy share, and shortfall hours per family.
- The commitment-demand increment actually applied (from the leg log).
- S5: where CC energy goes.
- The §6.1 wall row: ratio total ÷ (P0+P1), TL hits (W2 ≤ 3/yr reported), integer clusters.
- The price diagnosis by hour class and tercile, zero LP.

## 4. Expectation, written before any number

- **DA forecast:** in CAISO the bias is small and changes sign. It is +0.6 GW mean in 2019 and −0.4 to −1.6 GW mean in 2022–25, so the UC
  commits against *less* load than materialises in the years where C3a already fails (+10.5 to +12.5 % at uc-1.5). Expected direction:
  slightly less CC committed in 2022–25, so more imports/CT and price up; slightly more in 2019. UC-DIAG measured CAISO peak DF bias ≈ 0, so the
  move should be small.
- **Per-unit `mlf`/`ut_h`:** per-unit `mlf` is above the plant-basis 0.259 for multi-unit CCs. Each committed unit therefore carries more
  min-load energy, which makes commitment lumpier. The UC may commit fewer units, or commit them and lower the trough. Shorter per-unit
  `ut_h` should lift CC starts toward CEMS (uc-1.5: 0.34–0.82×). Sign on price: open.
- **Co-opt + u-gate, overlay off:** the requirement is ~2.2 GW. Offline CTs (non-integer, fast-start) can still back non-spin, while storage
  and hydro are not in the pergen builder (documented gaps that overstate scarcity). Expected: the u-gate binds in some evening hours, as
  SPP-SPIN found once a synchronized share existed; CAISO has no synchronized sub-row other than the co-drawn spin half. Removing the
  overlay lowers C3c counts and shaves the scored price where the adder fired.
- **Net:** this file makes no prediction on the C3a 2022–25 flips. If they persist, the uc-1.5 reading stands: the missing object is a
  measured import/WEIM price, a calibration-lane item rather than a UC value.

## 5. Solve plan (rules 16, 32–36)

- **Seven shards, 2019–2025**, one year each, launched **serially ≈ 5 min apart** (r11 infra note). Prompts come from
  `scripts/shard_prompt.py --iso CAISO --all-years --sha <branch head> --lane ucmilp4-caiso --bundle results/calibration/closeout_caiso_w1_a2_span`
  plus the nine `--set` values above and `--budget 720` (the charter's per-shard ceiling). The parent appends:
  - the UC additions (the four UC files in the pushed tree, the §6.1 wall row, the > 95 MB split rule);
  - **memory gate hard stop 2b:** ceiling + swap ≥ 22.4 GiB from `prepare_solve_container`'s `swap:` line, else STOP before any data step.
  Out-dir `results/calibration/ucmilp4_caiso_<y>`, branch `claude/ucmilp4-caiso-<y>`. Committed as `shard-prompts-ucmilp4-caiso.txt`.
- **Blocked year** (memory gate or OOM): at most **4 relaunches ≈ 30 min apart**, each in a fresh container. After that, the year is a
  coverage gap with its attempt log. A budget stop is reported, not relaunched with any changed setting.
- **On each report:** fetch; check `git ls-tree -r <sha> -- results/calibration/ucmilp4_caiso_<y>` is non-empty; check out; verify the bytes
  of `dispatch/<y>_P1.parquet` and the four UC files; then archive the shard (rule 33).
- **Compose and score, zero LP, at the pin.** Use a scratch copy of `_ucmilp_compose_span.py` with `gas_price_override` added to the per-year
  fields (UC-2 §8). Local registration only to feed the scorer; it is removed before commit. Nothing is registered or promoted (E13).
- **Deliver:**
  - RESULT and slim span under `docs/records/caiso/ucmilp/` (`data/ucmilp4_caiso_span/`, `data/ucmilp4_readings/`);
  - the CAISO cells `unit_commitment_milp` and `uc_commitment_demand_source` stamped from the RESULT;
  - one records-only PR to main. UC-DESK merges it.

## Addendum A (2026-10-15 ~10:20Z, before any U4 number exists) — defect stop FIX-8; attempt log

**UC-DESK hold, 10:09Z.** At `7dbfe20f`, `uc_commitment_demand_source="da_forecast"` raises in `data/commitment_demand.py:254`
("commitment increment has N zones, demand N+k") for every ISO with an `IMPORT_ZONE` pseudo-zone. CAISO has one (`WECC_import`), and the
desk confirmed it without an LP. The defect is deterministic, so every CAISO year fails at UC prep. This lane confirmed from the code that the shape
check sits between `backcast_commitment_increment` (real zones) and the solve demand (real zones + import pseudo-zone). Nothing was patched (`src/` untouched).

| year | shard session | launched | reached | memory gate (`swap:` line) | outcome |
|---|---|---|---|---|---|
| 2019 | `session_018fBc5hQH45cYV5CJ815ojV` | 09:52Z | data prep / P0 build (co-opt rows logged: 2 families, req 1,120 MW each, 21 pergen R columns, Σ ramp cap 18.7 GW); killed ≈10:10Z before the UC stage | ceiling 13.36 + swap 9.0 = "22.4 GiB" (22.36 unrounded) | stopped on hold; nothing pushed; archived |
| 2020 | `session_01PrfXjh22z5RbzxfGPF2F3d` | 09:57Z | data prep / P0 build (Σ ramp cap 19.1 GW); killed before the UC stage | same, 22.36 unrounded | stopped on hold; nothing pushed; archived |
| 2021 | `session_01Spg7FCVmBRKwVuTasPrGzJ` | 10:03Z | HEAD check only | not run | stopped on hold; archived |
| 2022 | `session_01J8TdBgnGoWF6oQZvj68RzS` | 10:08Z | no report (interrupted) | — | archived; `git ls-remote` shows no `claude/ucmilp4-caiso-*` branch |
| 2023–2025 | — | not launched | — | — | — |

This is a defect stop. Per the desk, it spends none of the four memory relaunches. **Gate note for the desk:** the shard containers print
"22.4 GiB" from a raw 22.36 GiB (13.36 ceiling + 9.0 swap). Two shards read that as passing. The relaunch keeps the gate as the printed
`swap:` total ≥ 22.4. CAISO's UC-3 peak RSS was 7.4–7.6 GB, so CAISO is not memory-bound at this ceiling.

**What changes on relaunch:** the pin only, which will be the desk's FIX-8 full SHA, recorded in Addendum B with its G-DRIFT before any shard. The arm,
readings, kills, verdict rule and budget are unchanged.

## Addendum B (2026-10-15 ~10:45Z, before any U4 number exists) — re-pin to FIX-8

**Pin: `7c93273ec9056b1cd9f6e4fcf387e812f78f6e8a`** (main at #7267, UC-1-FIX-8: the DA-forecast increment is mapped onto the runtime zone
rows by name, and interchange pseudo-zones get 0). The engine label stays **uc-1.7**. The desk repro for CAISO 2022 gives runtime zones = 5 load + `WECC_PNW` +
`WECC_DSW`, pseudo rows 0, mean increment −415.6 MW. That agrees with this file's §1.1 table (2022 mean −416 MW). This branch merges the pin, so
shards run at this branch head = pin + records only (`git diff --stat 7c93273e HEAD` touches only `docs/records/caiso/ucmilp/`).

**G-DRIFT `7dbfe20f` → `7c93273e` (zero LP).** Two commits: `ca90d2e8` (desk docs) and `7c93273e` (FIX-8):

| file | hunk | CAISO classification |
|---|---|---|
| `data/commitment_demand.py` | increment mapped by zone name; new `zone_names` argument | LIVE, `da_forecast` path only (the fix) |
| `pipeline/uc.py`, `pipeline/solve.py`, `pipeline/year.py`, `runner.py`, `scripts/run_calibration.py` | `zone_names` plumbed to the UC stage (keyword argument, default `None`) | INERT gate-off: read only by the UC stage's `da_forecast` commitment demand |
| `scripts/lib/uc_bench.py` | bench capture carries `zone_names` | INERT: not the solve path |

`solve_surface_register.py --diff 7dbfe20f 7c93273e`: *"345 → 345 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*. The
control stands without a solve (rule 29(b)).

**Unchanged:** the arm (the nine `--set` values, `'"da_forecast"'` quoted), readings, kills, verdict rule, the 720-min budget and serial launch.
Memory gate per the desk's ruling (10:19Z): pass iff the printed ceiling+swap rounds to ≥ 22.4 GiB (raw ≥ 22.35). A blocked year gets ≤ 4
relaunches about 30 min apart, then becomes a coverage gap. The Addendum A defect stop spends none of them.

## Addendum C (2026-10-16 ~02:30Z, before any 2021–25 U4 number exists): resume on the owner's gate ruling, re-pin 2021–25 to uc-1.8

**Owner ruling (2026-10-16, decision card; desk log r16, PR #7273 `5bdc2c58`).** The memory gate is now 1.25 × each ISO's measured peak; the
uniform 22.4 GiB is retired. For CAISO the measured peak is 9.4 GiB (U4 2019 cgroup 9.30 GiB, 2020 9.38 GiB), so the **gate is 11.8 GiB of
ceiling + swap at boot**. Each held year (2021–2025) carries its attempt count forward at 3/4, which leaves **one attempt per year** under the
new gate. A miss on it is a coverage gap.

**Pin for 2021–2025: `41cd55dc9b254a412f52cce051257ea15965c70e`** (main at #7270, UC-1-FIX-9, engine **uc-1.8**). This branch merges the pin;
shards run at this branch head (pin + records only).

**G-DRIFT `7c93273e` → `41cd55dc` (zero LP).** Three commits. `e2380108` and `5ff4443b` are records only (UC-4-SPP, UC-4-MISO). `41cd55dc` is FIX-9:

| file | hunk | CAISO classification |
|---|---|---|
| `model/uc/solve.py` | `lean` preset `lp_heuristics` False → True (RINS / RENS / root reduced cost) | **LIVE, UC solver path only**: the window model, integer feasible set, `uc_mip_rel_gap` 1e-3 and the 600 s time limit are unchanged, so a window's optimum can move only within the declared gap |
| `pipeline/uc.py` | `UC_ENGINE_VERSION` uc-1.7 → uc-1.8 (enters the input digest, so no uc-1.7 schedule is reused) | LIVE, gate-on only (label + digest) |
| `config/scenarios.py` | comments only | INERT |

`solve_surface_register.py --diff 7c93273e 41cd55dc`: *"345 → 345 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*. Gate-off
path untouched, so the control stands.

**The 2019–20 legs (uc-1.7) stay valid.** FIX-9 changes how HiGHS searches, not what it solves. Both engines solve the same window model to the same
1e-3 gap, so a uc-1.7 leg and a uc-1.8 leg differ by at most one gap-width per window. That is the same tolerance every UC lane already
accepts between two incumbents. The RESULT records the engine per year (2019–20 uc-1.7, 2021–25 uc-1.8) and reports any 2021–25 reading whose
move is within the 2019–20 vs UC-3 engine noise as such.

**Unchanged:** the arm (nine `--set` values), readings, kills, verdict rule and the 720-min budget. **Shard prompt changes:**
- hard stop 2b reads ceiling + swap ≥ 11.8 GiB;
- watcher / `send_later` keep-alive every ≤ 90 min (25 min recommended; desk standing rule after the NEISO reclaim).
