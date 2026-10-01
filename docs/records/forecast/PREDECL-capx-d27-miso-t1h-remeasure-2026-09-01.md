# PRE-DECLARATION — capx D27: HEAD re-measure of the MISO T1-H leg

**Lane:** capx D27 — the EXECUTION of D17-R's routed PRIMARY (R1).
**Read first:** `FINDING-capx-d17-miso-exit-channel-2026-09-01.md` (the attribution, the
≈14.7 GW arithmetic, and the standing refusal) · `PRECOMMIT-capx-d17-miso-exit-channel-2026-09-01.md`.
**Session date:** 2026-09-01. **Branch:** `claude/capx-d27-miso-t1h-remeasure-9z817j`.
**Discipline:** D4-M — this document is written and pushed BEFORE the solve starts. Every
prediction below is graded at full magnitude afterwards, misses included.

**What this session is NOT.** No mechanism is tested. No `ScenarioConfig` field is added or
moved. No FOM constant, retirement threshold, execution lag, margin adder or screen parameter
moves — D17's standing refusal (its K7, inherited from the NEISO-RC R6 refusal) binds this
lane identically. Rule 28 is not triggered; no matrix cell is written. The G3 cap-grain fix
stays; the pre-fix knife-edge PASS is not a target to restore.

---

## 1. The run

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d27
```

A **bare invocation at HEAD** — every solve-affecting flag omitted so each inherits its
shipped default. This is the FFR-3A-3 recipe (that battery's §1.3: "all six solve-affecting
flags were omitted from every invocation") and the D4-M ERCOT recipe with `--iso` swapped.
Years run sequentially inside one invocation (rule 12). Solve years `{2021, 2023, 2024, 2025}`,
2022 bridged, scored 2023–2025 (rule 22 — no out-of-training year is solved, scored or
registered; the holdout freeze is untouched).

**Priced before launch (D17 R1):** ≈25 min solo / ≈10 GB peak RSS by the s123-verify
analogue. Host has 15 GB RAM / 4 cores / 20 GB free disk. One leg only; no control arm.

### 1.1 Resolved posture at HEAD — read BEFORE the solve, not after

Resolved by evaluating `run_capacity_hindcast.build_config(...)` +
`apply_iso_scenario_defaults(..., "MISO")` at HEAD with no solve:

| field | resolved |
|---|---|
| `retirement_rule` | `pipeline` |
| `entry_lookahead_reprice` | True |
| `correlated_forced_outage` | True |
| `entry_rate_limits` | True |
| `entry_commissioning_lag` | True |
| `exit_rate_limits` | **False** (FFR-3F's D-8 present but unarmed — Addendum G.1 honoured) |
| `capacity_screen_unified_lookahead` | False |
| `capacity_screen_scarcity_restoration` | False |
| `entry_pipeline_aware_signal` | False |
| `entry_margin_exhaustion` | False |
| `entry_forward_reserve_leg` | False |
| `entry_forward_expectation_signal` | False |
| `storage_entry_availability_gate` | **True** |
| `storage_entry_cost_normalized_rank` | **True** |
| `hindcast_verified_announced_exits` | **True** |
| `entry_vre_capacity_revenue` | **True** (MISO ISO default) |
| `miso_rps_compliance_regions` / `miso_clean_tier_rows` | **True / True** (MISO ISO defaults) |
| `capacity_market_clearing_by_iso["MISO"]` | True |
| `screen_reserve_value_enabled` | True |
| `reserve_margin_build_enabled` | None (⇒ ON for a capacity-market ISO) |

The first six reproduce FFR-3A-3 §1.3 exactly.

**S-123 operands verified in force at HEAD** (read from the registries, no solve):
`PLANNING_RESERVE_MARGIN_BY_ISO["MISO"] = 0.157` (S-1, was 0.179),
`ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"] = 3505.9` (S-2),
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"] = 9004.4 / 135213 = 0.0665940` (S-3a).

### 1.2 D17 R1 guard (a) — cache-key freshness, discharged BEFORE launch

The three S-123 operands sit OUTSIDE the cache-key digest (S-123 §7.8), so a stale key could
serve a pre-package bundle. Two independent discharges:

1. The resolved HEAD cache key for this invocation is **`501b5f64b8adf8d4`**, which is not
   FFR-2B's `0a4455fd0d642364` nor the legacy arm's `df5c3de1bad16670`.
2. `run_capacity_hindcast.py` redirects `cachemod.CACHE_ROOT = args.out_dir` (line 1841), so
   a **fresh, empty `--out-dir` cannot serve any pre-existing bundle at any key.** The
   out-dir is verified absent/empty immediately before launch.

The run's realized key is recorded in the finding; a key ≠ `501b5f64b8adf8d4` is itself a
reportable finding (the pre-solve resolution and the solve-time resolution disagreeing).

### 1.3 D17 R1 guard (b) — the scoring target, and the vintage seam

Scored against the **CURRENT committed** `data/raw/_validation-source/capacity_actuals_miso.csv`
(header "Built 2026-08-07", landed on main 2026-08-30, PR #4387), whose 2021–2025 retirement
aggregate is:

| basis | total | coal | gas_st | gas_cc | oil | gas_ct | nuclear | biomass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **current target** (GW) | 17.600 (all fuels) / 17.371 thermal | 12.434 | 2.128 | 0.858 | 0.543 | 0.399 | 0.812 | 0.196 |
| 2026-08-02-era target, as scored in the baseline | 15.227 | 10.934 | *(folded)* | 0.521 | 0.502 | 2.435 | 0.812 | 0.023 |

**Both coal signs are quoted in the finding, per D17 R4.** The baseline's 11.932 GW of model
coal reads **+9.1 %** against the era target and **−4.0 %** against the current one. The
missing non-coal fossil target is **3.458 GW** on the era basis and **3.926 GW** on the
current basis; the ZERO is vintage-independent.

### 1.4 CONFOUNDS — declared before the run, not after

**This is a HEAD re-measure, not an S-123-isolating A/B, and no causal attribution to S-123
alone will be claimed from it.** Since the FFR-3A-3 baseline (solved 2026-08-04) these
MISO-relevant defaults moved, every one of them post-baseline:

* `miso_rps_compliance_regions` → True (owner D-26, signed 2026-08-06)
* `miso_clean_tier_rows` → True (owner D-29, signed 2026-08-11)
  — both change the LP's RPS constraint set, hence prices, hence **every screen margin**
* `entry_vre_capacity_revenue` → True (MISO ISO default)
* `storage_entry_availability_gate`, `storage_entry_cost_normalized_rank` → True
  (owner R-A, 2026-08-31) — storage entry only
* `hindcast_verified_announced_exits` → True (harness default, 2026-08-22)
* the S-123 adequacy package itself — the object

One leg is priced, so no control arm runs. Movement measured here is the movement **HEAD
produces**; separating S-123's share from the five confounds above would need a paired
control and is NOT in this session's budget or scope.

---

## 2. The baseline being re-measured

Committed FFR-2B pipeline arm (`results/hindcast/miso-2021-2025-cmc-pipeline-ffr2b/MISO/0a4455fd0d642364`),
byte-identical to the FFR-3A-3 leg on every retirement quantity (FFR-3A-3 §2.5):

| year | decided | entry_capped | re_confirmed | executed | reversed | reserve_margin |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | — | — | — | — | — | 0.272935 |
| 2023 | 1,105.3 | **93,016.7** | 11,931.6 | — | — | 0.217566 |
| 2024 | 901.0 | **105,542.9** | 13,037.0 | 11,931.6 (all coal) | — | 0.119461 |
| 2025 | — | — | — | — | 2,006.3 | 0.218797 |

Cumulative economic exits: **coal 11,931.6 MW, everything else 0.0**. Backstop 0.0 MW in
every year. `retire.total_gw` model **12.716 GW**, band **FAIL**.

The registered verdict at the bare `miso-t1h` key (session FFR-3A-2, `scored_at_sha`
`8ba592814d92`): determination **HOLD**; FC-3 **FAIL** (add bands); FC-7 **FAIL**
(`run_config.json absent` + DOF-ledger CAVEAT); FC-1/FC-8 SKIPPED; FC-2/4/5/6 n/a.

---

## 3. PREDICTIONS (graded at full magnitude afterwards)

**Standing honest note, stated before any number below.** D17's ≈14.7 GW is a **screen-side
arithmetic on the requirement identity — NOT a dispatch guarantee.** It bounds how much
admission budget the corrected basis frees. It says nothing about which units sit deepest
below the bar, whether the execution-time reliability floor releases them, or whether the
LP's own HEAD prices leave the same set failing. Every prediction below inherits that limit.

### P1 — `entry_capped` (2023 / 2024)

* **Direction: DOWN in both years.**
* **Magnitude: 2023 −8 to −18 GW (→ ~75–85 GW); 2024 −10 to −20 GW (→ ~86–96 GW).**
* Basis: at the 2024 screen the baseline's post-exit position was `reserve_margin` 0.1195,
  i.e. 1.1195/1.09952 = **1.0182** on the pre-S-123 factor — the cap binding at ~1.8 % slack.
  On the corrected factor 1.00715 the same fleet sits at 1.1116, ~11.2 % of a 121,560 MW peak
  ≈ **13.6 GW**, plus **3.5 GW** external accredited firm ≈ **17 GW** of accredited headroom.
  Nameplate admitted exceeds accredited admitted (accreditation derates), so the nameplate
  fall in `entry_capped` should be ≥ the accredited release.
* **FALSIFIER:** |Δ| < 3 GW in *both* years ⇒ the admission cap was **not** the binding
  rationer at HEAD, and D17's thread-(iii) CONFIRMED-PRIMARY must be re-opened rather than
  confirmed. That outcome is reported as a MISS, not re-narrated.

### P2 — executed non-coal exits vs the actual

* **The channel OPENS: executed non-coal (gas_st + gas_cc + gas_ct + oil) is STRICTLY
  POSITIVE**, against a baseline of exactly 0.000 GW.
* **Magnitude: 2–8 GW**, with **gas_st the largest single contributor**.
* **And it MISSES the composition.** I predict gas_st **over**-shoots its 2.128 GW actual,
  while the small-unit tail (oil 103 units / 542.8 MW; gas_ct 18 units / 398.7 MW; actual
  non-coal cohort median 2 MW) stays **under**-produced — because D17 §4.2's measured
  discrimination defect (the bar fails ~119.5 of 142.6 GW, capacity leg $0 at every long
  position) is untouched by a requirement-side repair and cannot resolve a 2 MW grain.
* **FALSIFIER for "the channel opens":** non-coal executed stays exactly 0.000 GW.

### P3 — `retire.total_gw` and the G3 row

* **Model RISES from 12.716 GW to 22–34 GW, central ~28 GW.**
* Against the current 17.600 GW target that is **+25 % to +93 %, central ~+59 %**.
* **Band: FAIL, WITH THE SIGN FLIPPED** — from under-retention (−16.5 % era / −27.7 %
  current) to **OVER**-retirement.
* Basis: this is the direct consequence of taking D17's own two findings together. If the cap
  is the binding rationer (thread iii) *and* the bar fails ~83 % of the thermal fleet
  (§4.2), then releasing ~17 GW of accredited headroom releases ~17 GW of accredited exits —
  **not** the 3.93 GW the target wants. **The headroom being 3.7–4.3× the target is exactly
  why I do NOT predict the target is hit.** A repair that un-starves a channel does not aim it.
* **Explicitly pre-registered alternative, which I judge ~25 % likely:** the release lands
  inside the ±10 % band (15.84–19.36 GW) and `retire.total_gw` **PASSES**. If that happens it
  is recorded as a prediction MISS on magnitude and a hit on direction — and it does **not**
  license calling the object closed, because P2's composition test still governs.

### P4 — verdict rows and cross-lane safety

* **FC-3 STAYS FAIL.** The five addition bands (`add.by_tech.wind/solar/gas_cc/gas_ct/storage`
  + three `add.shares`) are untouched by a requirement-side repair; `retire.total_gw` is
  predicted out of band with its sign flipped.
* **FC-7 row 1 `run_config` FLIPS FAIL → PASS by construction** — the FFR-3K blocker-7 fix
  makes `run_capacity_hindcast.py` write `run_config.json` from the bundle's own resolved
  config (line 1985), which the FFR-3A-2/FFR-3A-3 legs predate. The DOF-ledger row stays
  CAVEAT, so **FC-7 goes FAIL → CAVEAT.** This is an instrument change, not a model
  improvement, and will be labelled as such.
* **FC-1 and FC-8 stay SKIPPED** (this harness emits no `summary.invariants` and no
  `total_wall_s` perf ledger).
* **Determination STAYS HOLD** (FC-3 FAIL is sufficient on its own).
* **No verdict outside `miso-t1h`'s own rows moves.** If one does, the session **STOPS and
  ROUTES** (cross-lane re-grade) rather than writing it.

### P5 — adequacy trace

* The run's own evolution ledgers reproduce the corrected requirement — factor ≈ **1.00715 ×
  peak** plus **+3,505.9 MW** external accredited firm — matching D17 §4.1's arithmetic up to
  the cap-horizon peak projection. **This is the direct grade of the ≈14.7 GW figure.**
* End-of-window `reserve_margin` falls **materially below** the baseline's 0.218797 (2025) —
  predicted **0.02–0.12**.
* **Non-trivial chance (~40 %)** that the adequacy backstop fires (baseline: 0.0 MW in every
  year) and/or unserved energy appears in 2025 — the same endogenous signature S-123-V
  measured in the 2029/2030 forecast years.

---

## 4. Registration plan (frozen here)

**Preserve-then-overwrite, the NEISO-RC-R pattern.** The current `miso-t1h` verdict record is
preserved verbatim under **`miso-t1h-pre-d27`** — a PRESERVED BASELINE, never quoted as
current state — and the HEAD re-measure is registered to the **bare `miso-t1h`** key via
`scripts/register_forecast_run.py`, with the MISO board block refreshed. Every other ISO's
rows are untouched. Run id: **`miso-2021-2025-realized-t1h-d27`**.

## 5. Kills

* **K-a — solve budget.** One T1-H leg. If it OOMs or exceeds ~2× its price, the session
  reports the failure and registers nothing rather than trimming years (rule 16's spirit: the
  window is the window).
* **K-b — no parameter moves.** If any prediction misses in a direction that "wants" a tuned
  constant, that is an open root-cause issue routed onward, never a parameter (rule 21).
* **K-c — no cross-lane writes.** miso-t1h key + MISO board block only. D26 (neiso-t3 FC-6),
  D29 (`run_full_horizon.py`) and D24-R (cache plumbing) are in flight; a conflict is rebased,
  never resolved in another lane's favour.
* **K-d — rule 22.** No out-of-training year is solved, scored or registered; nothing is
  scored against measured H1-2026.
