# PREREG — miso-117: `measured_ct_heat_rates` on MISO's own CAMPD artifact

**Written and committed BEFORE either arm solved.** Every threshold, kill,
predicted direction and disposition rule below is fixed here. The Phase 0
numbers in §2 were measured before this file was written (they are what
justifies spending the solve at all) and are marked as such; nothing in §4–§7
was chosen after seeing an arm.

* **Session:** miso-117. **Branch:** `claude/miso-117-measured-ct-heat-rates-nc5xme`,
  fresh off `origin/main` at `5885248`.
* **Lever:** `ScenarioConfig.measured_ct_heat_rates` (`scenarios.py:1644`),
  mechanism-matrix row `measured_ct_heat_rates`, **MISO cell `U`** — §5.4 lever
  queue item **4** ("audit-grade"), and the first of the two successors
  miso-116 §7 named.
* **Incumbent keeper:** `2026-07-31-miso-109b-hy-level`
  (`results/calibration/miso109_hy_level_B`), determination **NOT-YET** on one
  failing criterion, **C7 `COAL_PRB`** (`cv_ratio` 0.466 / 0.475 / 0.314 against
  a 0.50 bound). Ledgered caveats 2 of 3: C3a mean LMP, C3c price tail.
* **Charter:** rule 14 `[R-ACCURATE]` — a measured loaded heat rate replaces an
  eGRID plant-average estimate. **Admissible regardless of what it does to the
  residual, and NOT offered as a C7 instrument.**

---

## 1. Why this lever, and what it is NOT

miso-115 §4 measured MISO's `CT_PEAKER` trough heat rate at **11.13 / 11.25 /
11.26 MMBtu/MWh gross** (CAMPD `heatInput / grossLoad`) against the model's
**12.37 net** — the model is **+9.9…+11.1 % too dear**, worth **$3.15 / $2.45 /
$3.91 per MWh** at the keeper's own recorded gas prices ($2.54 / $2.19 / $3.52
per MMBtu). It is not a weighting artifact: the trough-selection control moves
it +0.2…+0.5 %, the class-average control +0.6 %, and gross-vs-net makes the
true gap **larger**. `ST_GAS` is already right (−3.4…−0.0 %), so the defect is
**CT-specific**.

miso-116 audited that result and it **survives intact** — unlike miso-115's two
CHP results, which miso-116 withdrew as a reporting-basis artifact and a
probe-flag artifact respectively. The keeper does not arm
`measured_ct_heat_rates`, so 12.37 is genuinely what its LP charged.

**This is NOT offered as the C7 `COAL_PRB` fix and NOT as the overnight
level-offset fix.** miso-115 measured `CT_PEAKER` online in only **1.9–3.2 %**
of trough plant-hours and explicitly declined to offer it as the level fix. C7
`COAL_PRB` needs the overnight dispatch *distribution* WIDENED (miso-113); a
heat-rate swap on a peaking class is not that mechanism and is not claimed to
be. If C7 moves at all it is a side effect, reported and not banked.

**Nothing else is armed.** Rule 19 `[R-ONE-MECH]`: one flag, one delta.

---

## 2. Phase 0 — measured before this prereg was written, no LP spent

Probe `scripts/probes/_miso117_flag_fidelity.py`; transcript
`results/calibration/PROBE-miso117-flag-fidelity-2026-08-03.txt`. The probe
builds **both** its arms from the keeper's own `run_config.json`
`scenario_config` block — miso-116 §7's methodological finding, which withdrew
two miso-115 results that came from a probe reading the model with a different
configuration than the keeper solved. In particular the keeper arms
`measured_chp_heat_rates=True`, and both arms here carry it.

### 2.1 The arming channel exists and is registry-clean (rule 26 `[R-REGISTRY]`)

`measured_ct_heat_rates` is a `ScenarioConfig` field consumed at
`run_calibration.py:2629` → `load_fleet_from_csv(...)`. It has **no** flag in
`scripts/run_calibration_full.py` and **no** `solve_and_persist` kwarg, so it
routes through `scripts/replay_keeper.py --set`, which writes it to the generic
`prb_overrides` `ScenarioConfig` channel. That is the channel **caiso-146 and
the other three tested ISOs used**, and it lands in the bundle's
`run_config.json` **twice** — `scenario_config.measured_ct_heat_rates: true`
and `calibration_flags.coal_prb_sigmoid_overrides.measured_ct_heat_rates: true`
— so the run records what it solved. **No new CLI flag is added**: a second
arming channel for the same field would itself be a rule-24/26 hazard, and
`--set` already satisfies the registry requirement. (Verified against the
committed `caiso146_ctheatrate_B/run_config.json`, which records both.)

The artifact is **not re-derived** (rule 23 `[R-FROZEN-DERIVE]`):
`data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv` is on `main` and
loads **86 plant entries** via `fleet.campd_bins.measured_ct_heat_rates("MISO")`
(min / median / max 8.899 / 11.771 / 17.545 MMBtu/MWh). It landed under PR
**#3217** (neiso-71), not the closed #3140.

*(Incidental, committed with this prereg:*
`scripts/run_calibration_full.py --help` *crashed on a pre-existing argparse
bug — three help strings carried a bare `%` that argparse read as a format
spec. Escaped to `%%`; `--help` now renders 2,883 lines. Pushed as the exact
on-disk bytes via* `git push` *and blob-verified per rule 27 `[R-PUSH]`. No
solve-affecting change —* `replay_keeper.py` *calls* `solve_and_persist`
*directly and never builds the CLI parser.)*

*(Transport note for successors, measured here:* `git push` *is refused with
**HTTP 413 on every pack, including an empty commit**, when the push would
**CREATE** the remote ref. It is **not** a pack-size limit — a 58 KB thin pack
and a ~200-byte empty-commit pack both fail identically. Creating the branch
first with* `mcp__github__create_branch` *and then pushing to the now-existing
ref succeeds. This matters because CLAUDE.md's Git & Pushing section attributes
413 to pack size, and* `mcp__github__push_files` *cannot carry a 548 KB core
file (~457 KB cap) — so a session that reads the 413 as a size limit will
wrongly conclude the file is unpushable.)*

### 2.2 The flag REACHES the MISO LP seam — it is NOT the ERCOT-146 wiring case

Under `use_campd_bins` ERCOT reads the curated `load_campd_bins` sheet and the
flag is byte-identically **inert**; every other ISO synthesizes bins from
`load_fleet_from_csv`. Verified **empirically**, as neiso-70 did, not read off
the branch:

| measured at the keeper's config | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| tranches moved (of 2,740) | 509 | 509 | 509 |
| `CT_PEAKER` MW moved (of 22,281.8) | 19,120.7 | 19,120.7 | 19,120.7 |
| `CT_PEAKER` cap-wt HR, tranche grain | 14.8022 → 14.3999 | idem | idem |
| **`CT_PEAKER` cap-wt HR, PLANT grain** | **12.3720 → 12.0351 (−2.72 %)** | idem | idem |
| covered subset only | 12.2899 → 11.8972 (−3.20 %) | idem | idem |
| uncovered stays | 12.8673 | idem | idem |

**`classes touched: ['CT_PEAKER']`** — no scope leak. Artifact coverage is
**254 of 516 class plants = 19,120.7 of 22,289.2 MW (85.8 %)**, and all 86
artifact plants apply. The plant-grain base value reproduces miso-115 §4's
published model figure **12.3720 ≡ 12.37 exactly**, which is the check that the
probe is keeper-matched. The three vintages are identical because the artifact
is one pooled 2023–2025 measurement.

**The direction is TWO-SIDED** — 360 tranches / 13,801.1 MW **cheaper**, 149 /
5,319.6 MW **dearer**. That is the NYISO/PJM shape, not CAISO's one-sided
result. **Recorded here before any solve**: the fleet does not simply get
cheaper.

**Sizing the expected close, fixed in advance.** A −2.72 % class heat rate
against a measured +9.9…+11.1 % gap closes roughly **a quarter** of it. The
reasons are structural and known now, not discovered later: coverage is 85.8 %
of class MW, and the uncovered tail is *dearer* (12.87) than the covered
(12.29). **I do not predict the measured gap closes**, and a partial close is
not a defect of the lever.

---

## 3. Arms — one flag, nothing else (rule 19), all three years (rule 16)

| arm | bundle | delta |
|---|---|---|
| **A — control** | `results/calibration/miso117_control_A` | none (zero-delta keeper replay at this HEAD) |
| **B — treatment** | `results/calibration/miso117_ctheatrate_B` | `--set measured_ct_heat_rates=true`, **one flag, nothing else** |

```
.venv/bin/python scripts/replay_keeper.py results/calibration/miso109_hy_level_B \
    --out-dir results/calibration/miso117_control_A \
    --note "miso-117 arm A: zero-delta replay of the 2026-07-31-miso-109b-hy-level keeper at HEAD (control)"

.venv/bin/python scripts/replay_keeper.py results/calibration/miso109_hy_level_B \
    --out-dir results/calibration/miso117_ctheatrate_B \
    --set measured_ct_heat_rates=true \
    --note "miso-117 arm B: the miso-109b keeper recipe with ONE delta, measured_ct_heat_rates=true, on MISO's own CAMPD artifact"
```

Each invocation carries the keeper's full span `[2023, 2024, 2025]` in **one**
bundle, **years sequential inside the invocation** (rules 12 / 16). **The two
chains run SEQUENTIALLY, not concurrently** — a single MISO per-plant multi-zone
year peaks near 15.5 GB (miso-113 §7) on a 15.4 GB box; rule 12's
separate-invocation concurrency does not license two MISO chains. An 8 GB
swapfile is enabled as headroom. **No third arm, no stacked mechanism, no
offer-curve override.**

---

## 4. Construction gates — must all pass, else the arms are not comparable

* **K1 — flag fidelity.** Arm B's `run_config.scenario_config.measured_ct_heat_rates`
  is `true` and arm A's is `false`; **both** carry
  `measured_chp_heat_rates: true` (the keeper's own setting — the miso-116
  trap). Applied plants = 86.
* **K2 — control integrity.** Arm A reproduces the committed keeper's
  scorecard: same determination (**NOT-YET**), same nine criterion statuses,
  same C7 `COAL_PRB` failure in all three years. Reported on **two** bases and
  both are stated whatever they show: (a) the **scorecard** basis above, which
  is the comparability gate; (b) the **strict-byte** basis — arm A minus the
  committed keeper's `class_hourly_<year>.parquet`, per class-hour. Same-HEAD
  drift on the strict-byte basis is **reported, not a kill** (caiso-146,
  neiso-69 and ercot-150 all measured real drift while the A/B stayed
  unconfounded, because both arms share it); a scorecard that does **not**
  reproduce **is** a kill.
* **K3 — mechanism is LIVE** (the nyiso-89 §4a check). The class hourlies must
  show a real dispatch delta: `max |Δ CT_PEAKER MW|` **> 50 MW** in at least one
  year. Byte-identical arms ⇒ verdict **`I` (inert)**, not `R`.
* **K4 — single delta.** The `run_config` diff between arms is exactly the one
  boolean in both of its recorded places, plus provenance (timestamp, note, git
  sha, basis sha).
* **K5 — year span.** Both bundles carry `years == [2023, 2024, 2025]`. **No
  out-of-training year appears in any solve, probe or score** — MISO holds no
  `calibration-complete` marker, so neither the validation ladder (2022) nor the
  locked test (2019, H1-2026) is available (rule 22 `[R-HOLDOUT]`, D-6
  quarantine).

---

## 5. Predicted directions — including the ones I expect to worsen

Fixed here, before any arm result is visible. The mechanism cuts the covered
CT fleet's SRMC by roughly `Δ HR × gas` ≈ **−$1.0 / −$0.9 / −$1.4 per MWh** on
the class average (−0.337 MMBtu/MWh × the keeper's $2.54 / $2.19 / $3.52), with
individual plants moving **both ways** (§2.2).

1. **`CT_PEAKER` energy RISES in all three years**, net cheaper fleet on a
   top-of-stack class. Predicted magnitude **+0.2 to +1.5 TWh**/yr.
2. **C1 `CT_PEAKER` improves in 2023 and WORSENS in 2024.** The keeper is
   **−1.57 TWh** in 2023 (under) and **+0.61 TWh** in 2024 (over), so one
   direction cannot help both. **Recorded now**: a 2024 C1 degradation is the
   *expected* cost, not a surprise, and is not grounds to revert an accurate
   input (rule 14). 2025 C1 `CT_PEAKER` is SKIPPED by the scorer (preliminary
   EIA-923, 26 % plant reporting) and is reported as a diagnostic only.
3. **C1 may worsen for the displaced class**, most plausibly `CC_REGULAR`
   (keeper −2.56 / +3.03 TWh) or imports. **I do not know the sign and record
   that now**; it is reported either way.
4. **C3a mean LMP moves DOWN.** The keeper is already **−1.2 % / −6.4 % /
   −14.2 %** — negative in every year, with 2025 the ledgered CAVEAT. A cheaper
   peaking class pushes λ further down, so **this lever's most likely scored
   cost is C3a, and 2024 (−6.4 % against a ±10 % band) is the most exposed
   number in this arm.** This is a **hazard stated in advance, never a target**
   — see §7.
5. **C8 / D-2 `CT_PEAKER` forced share RISES.** miso-107 already measured this
   interaction on miso-106's arm: the h14-21 `reliability_floor × CT_PEAKER`
   limb's forced energy rose **1.188 → 1.743 TWh (+47 %)** and the D-2 share
   **11.77 → 14.21 %** against a **15 % peaker cap**. This keeper's baseline is
   **0.1157 / 0.0821 / 0.0867**. Predicted: rises in all three years, **2023 the
   one at risk of crossing 0.15**.
6. **C7 `COAL_PRB`** (the failing criterion): **predicted essentially
   unchanged.** Nothing here widens the overnight coal distribution.
7. **C3b / C3c**: small; C3c is the ledgered administrative-ORDC tail a cheaper
   CT fleet cannot manufacture. Predicted **unchanged**.

**Precedent shapes carry NOTHING** (rule 25 `[R-ISO-SCOPE]`): NYISO `K`, PJM `K`
(+0.229 net), CAISO `K` (one-sided −1.159), NEISO `K` (two-sided −0.579, CT
floor share **collapsed**), ERCOT `I` (wiring-inert). miso-107's measurement
predicts MISO moves the **opposite** way to NEISO on the floor share.
**Whichever happens is reported.**

---

## 6. Gates — pre-registered thresholds

Baselines are the incumbent keeper's own committed scorecard
(`scripts/calibration_verdict.py --run-id 2026-07-31-miso-109b-hy-level`) and
its committed `legitimacy_diagnostics.json`.

### 6.1 Protective (rule 20 `[R-FORCED-BUDGET]`) — `CT_PEAKER`

`CT_PEAKER` is in MISO's `d1_gated_classes`, so C7 applies in all three years
regardless of the 2 % materiality floor.

* **C7 / D-1 diurnal shape.** Gates `profile_r ≥ 0.80`, `cv_ratio ≥ 0.50`.
  Keeper `CT_PEAKER` baseline: `profile_r` **0.972 / 0.971 / 0.985**,
  `cv_ratio` **0.982 / 0.836 / 0.799**. A drop below either bound in any year is
  a **protective FAIL**.
* **C8 / D-2 forced share.** Peaker cap **0.15**. Keeper baseline **0.1157 /
  0.0821 / 0.0867** (`reliability_floor`). **If the share crosses 0.15, the
  route is the rule-20 conditional pass on D-4 window + D-1 shape — NEVER
  relaxing the limb.** The h14-21 `reliability_floor × CT_PEAKER` limb's level
  is `commit_frac × min_stable_pct`, with no price, dispatch or residual in any
  term (miso-107, refuted by construction), so a rising share is the floor
  becoming **load-bearing**, not becoming wrong. Its D-4 row exists and reads
  `offwindow_share 0.000` in all three years, so the conditional pass is
  scorable from the committed artifact.
* **D-4 off-window binding** stays **0.000** on every floor. The arm arms no
  floor and must not create one. A non-zero off-window share on any limb is a
  **protective FAIL**.

### 6.2 Scored criteria

Reported for both arms, all three years: C1 (all + free-class), C2, C3a, C3b,
C3c, C4, C6, plus the determination and the D-10 free-class headline. **No
threshold here is a kill condition** — see §7.

---

## 7. What makes this a REJECT — and what explicitly does NOT

**Rule 1 `[R-STRUCT]` + rule 14 `[R-ACCURATE]` govern this arm.** A measured
loaded heat rate is a more accurate input than an eGRID annual plant average.
**A worse backcast is therefore NOT a reject and NOT a reason to revert** — it
is a *discovered bug*: the input stays and the degradation becomes a root-cause
item.

**REJECT (`R`) only if the INPUT ITSELF is shown invalid:**

* **R1** — the artifact is shown not to be a measured input in the rule-13
  `[R-MEASURED]` sense (an outcome, or fitted to a residual).
* **R2** — coverage or exclusions turn out to be selective in a way §2.2 missed,
  i.e. the applied map systematically re-prices one tail of the class. §2.2
  already records the one known asymmetry (uncovered tail dearer at 12.87 vs
  covered 12.29); a *further* selection defect found in the arm is R2.

**INERT (`I`) if K3 fails** — armed but changes no dispatch. §2.2 makes this
unlikely, but the verdict is pre-registered.

**BLOCKS PROMOTION but is NOT a reject:**

* a **protective FAIL** (C7 `CT_PEAKER` `profile_r` < 0.80 or `cv_ratio` < 0.50;
  C8 > 0.15 *without* clearing the rule-20 conditional pass; any D-4 off-window
  break). The keeper holds **0 of 1** protective slots and this session does not
  spend one.
* any load-bearing criterion flipping **PASS → FAIL**.
* the keeper's own failing criterion, C7 `COAL_PRB`, getting **worse**.

**Promotion requires:** K1–K5 pass, no protective FAIL, no PASS → FAIL flip, C7
`COAL_PRB` not degraded, and the class-level evidence showing the re-price is
structurally faithful. **Promotion is not the objective of this session** — the
lever is chartered on accuracy, and `U → K` / `U → R` / `U → I` / `U → O` are
all admissible outcomes.

---

## 8. Hazards stated in advance

* **C3a is the exposed criterion, and it is a LEDGERED caveat.** The ledger does
  not forbid this work and does not forbid it moving C3a; it forbids reaching
  for a mechanism *because* it targets that residual. This lever was selected
  off §5.4 queue item 4 on miso-115 §4's measured input error, and §5 predicts a
  **downward** λ move — i.e. the direction that makes C3a **worse** — as a
  consequence, not a purpose. **Movement in C3a is reported, never tuned
  toward.** No parameter, threshold or scope here is chosen with reference to
  it, and none will be adjusted after seeing it.
* **If the arm materially moves any load-bearing criterion** (|Δ| ≥ 1.0 pp on
  C3a, or a C1 class crossing its band), it is scored **leave-one-year-out
  within 2023–2025** before any promotion (rule 22): an in-sample gain with
  held-out degradation is overfitting, not skill.
* **HARD BARS carried from the handoff, none of which this arm touches.** Do
  **not** relax the h14-21 `CT_PEAKER` reliability-floor limb to buy back C1
  volume (rules 1 / 14; barred by the miso-106 keeper note); do **not**
  re-derive `min_stable_pct` against a residual (rule 23; rule 25 — MISO derives
  its own or not at all); do **not** re-open the `CC_CHP` volume or heat-rate
  questions (miso-116, both WITHDRAWN) or the trough-quantity question
  (miso-115, refused); do **not** quote the `CT_CHP` / `ST_CHP` ratios (VOID on
  coverage); do **not** arm `miso_cc_coal_rebalance`, re-license
  `miso_firm_import_floor` or `miso_pjm_lmp_import_pricing`, or re-test the
  SPENT regulated-PRB self-commitment family (miso-111 `R` / miso-112 `R` /
  miso-113 `I`).
* **Contamination declared.** This session read miso-115, miso-116, the MISO
  calibration log and the matrix notes before writing this prereg, so it is
  **not blind** to the expected direction — the handoff named the hypothesis and
  the charter. What is fixed in advance is the decision rule, the gates and the
  §5 predictions, including the two (C1-2024, C3a) that predict the arm makes a
  scored number **worse**.

---

## 9. Deliverables (rules 15 / 28b), regardless of verdict

* **Both arms** registered on the backcast dashboard in this session — bundle
  slim files + registry sidecars + `runs/<id>.js` payloads + changed `bench/` —
  committed and pushed, honouring the top-15-per-ISO MISO retention.
* The `measured_ct_heat_rates` **MISO cell + evidence citation stamped in
  `docs/codebase-site/data/mechanism-matrix.js` in this session**, including if
  the verdict is `R` or `I`.
* miso-117 logged in `docs/calibration-log/miso.md` with its own DO-NOT-REDO
  section, and a `FINDING-miso117-*.md`.
* If promoted: `frontend/data/backcast/keepers/MISO.json` +
  `build_status.py --iso MISO` + the `calibration-keeper-auditor` subagent.
  (MISO holds no `complete` marker, so no `calibration-complete.json` re-key is
  due — rule 22 D-5(b) does not apply here.)
