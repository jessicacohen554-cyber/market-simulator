# PREREG — caiso-146: `measured_ct_heat_rates` on CAISO's own CAMPD artifact

**Written and committed BEFORE either arm solves** (house rule; caiso-139
precedent). Everything below — coverage, direction, gates, kill conditions — is
fixed at this commit. No gate is added, dropped or re-thresholded after a solve.

* **Session:** caiso-146. **Branch:** `claude/caiso-measured-ct-heat-rates-003f79`.
* **Lever:** `ScenarioConfig.measured_ct_heat_rates` (`scenarios.py:1346`),
  mechanism-matrix row `measured_ct_heat_rates`, CAISO cell `U`
  (`cells: "UUKUKU"` — `K` in PJM at pjm-137 and NYISO at nyiso-89, `K` in MISO
  at miso-106/107).
* **Queue item:** `docs/mechanism-testing-matrix.md` §5.2 item 6.
* **Incumbent keeper:** `2026-07-29-caiso139-dump-guard-offer`
  (`results/calibration/caiso139_dumpguard_B`), determination
  **CALIBRATED-WITH-CAVEATS** since caiso-145: 0 FAILs, 2 ledgered
  non-protective caveats (C3a-2025, C3c-2023/24), 1 of 3 ledger slots free,
  protective 0/1.
* **Rule 22:** CAISO holds **no** calibration-complete marker. `--years 2023
  2024 2025` only; `--holdout-authorized` is **not** passed; no out-of-training
  year is solved, scored or registered.
* **Rule 25:** this is CAISO's own artifact, derived from CAISO's own CAMPD
  data. **No verdict is transferred** from PJM / NYISO / MISO, and none of
  their parameters are reused — only the shared, ISO-agnostic derive script.

---

## 1. Why this lever, on CAISO's own evidence

eGRID publishes **one plant-average ANNUAL heat rate per plant**, and the
non-ERCOT fleet loader hands that number to every combustion turbine. For a
peaker that is wrong twice (the derive script's own docstring):

1. **It is an annual average, not a loaded rate.** A peaker's annual average
   blends startup fuel, part-load hours and shutdown tails into the number that
   sets its offer. The rate that sets an offer is the rate *at load*.
2. **At a mixed facility it is not even the right technology's rate.** CAISO's
   Glenarm (plant 422) is the textbook case and it is in this artifact: the
   model carries 4 `CT_PEAKER` units (138.4 MW) **and** 2 `CC_REGULAR` units
   (84 MW) there, all on a single eGRID figure of 10.3895. CAMPD tags the site's
   units separately — GT3/GT4 are `Combustion turbine` (11.42 / 11.35 all-hours),
   GT5 is `Combined cycle` (9.40). The artifact prices the turbines at their own
   10.6702 and leaves the CC blocks on eGRID.

CAISO's own standing finding is that this class is **priced out of merit**
(caiso-119). The keeper's committed sidecars make the size of that gap explicit:

| year | model CT_PEAKER (TWh) | actual `classFull` (TWh) | model / actual |
|---|---|---|---|
| 2023 | 1.0808 | 4.1284 | **26.2 %** |
| 2024 | 0.4243 | 4.3261 | **9.8 %** |
| 2025 | 0.2731 | 2.3738 | **11.5 %** |

Under rule 14 `[R-ACCURATE]` a measured loaded heat rate is strictly more
accurate than an annual plant average, so the swap is chartered on accuracy
alone — independently of what it does to the residual. Under rule 13
`[R-MEASURED]` it is admissible as an **input**: a unit's loaded heat rate is a
physical characteristic of the machine, it regenerates for a forward year from
the same pipeline, and it responds to changed conditions (a retrofit moves it, a
new unit carries its design rate). It is not a measured outcome, and nothing in
it is fitted to any residual.

## 2. STEP 1 — the derived artifact (already produced; this section is the report)

```
python scripts/data/derive_campd_ct_heat_rates.py --iso CAISO --years 2023 2024 2025 --detail
```

Outputs, both committed with this prereg:
`data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv` (**43 plant rows**) +
`campd_ct_heat_rates_CAISO_units.csv` (**87 unit rows**).

### 2.1 Coverage

* **43 / 43 plant rows carry `flag == "ok"`. ZERO rows are excluded by the
  physical band** — the loader applies every row the derive wrote.
* **Capacity: 5,848 / 7,616 MW = 76.8 %** of the model's `CT_PEAKER` capacity.
* **Metered energy: 8.015 / 8.025 TWh = 99.9 %** of the class's own measured
  CAMPD CT energy (2023–25 pooled, gross).

The energy number is the one that matters for an offer swap, and it is the
reason the capacity number is not a warning sign — see the exclusions.

### 2.2 Exclusions and why (the audit rule-14 requires before arming)

| cause | plants | MW | % class MW | metered CT GWh |
|---|---|---|---|---|
| **A** — no CAMPD account at all | 90 | 1,627.8 | 21.4 % | **0.000** |
| **C** — has CT units, never cleared the loaded window | 1 | 141.0 | 1.9 % | 10.119 |

* **Cause A is the Part-75 reporting boundary, not a selection effect.** These
  90 plants have a median size of **2.2 MW** and, decisively, **zero metered CT
  energy** — there is no measurement to swap in, so they correctly keep eGRID.
  The two largest are Carlsbad Energy Center (59002, 527.5 MW) and Humboldt Bay
  (246, 163.4 MW), neither of which reports to CAMPD at all.
* **Cause C is one plant:** Stanton Energy Reliability Center Hybrid (60698,
  141 MW), whose two CTs ran 221 / 232 hours but never reached 50 hours at
  ≥ 0.8 × their own p95 load. It keeps eGRID.
* **No adverse selection.** Covered capacity-weighted eGRID HR **10.819** vs
  uncovered **11.004** MMBtu/MWh — the uncovered set is not systematically
  dearer or cheaper on paper, so the applied map is not skimming one tail.

**Verdict on STEP 1: coverage is NOT thin and the exclusions are NOT
structural to the model** — they are the source's own reporting boundary, and
they carry no measured energy. This is not the "partial re-price that silently
leaves half the class on eGRID" the session prompt orders a stop for. Proceed.

### 2.3 Direction and magnitude — reported in BOTH directions

CAISO's result is **one-sided**, and that differs from the NYISO precedent
(which found 2× overcharges *and* undercharges in the same class) and from PJM
(35 cheaper / 36 dearer, net **+**0.229). Stating it plainly rather than
assuming the precedent transfers:

* **cheaper (measured < model): 41 plants, 5,649 MW.**
* **dearer (measured > model): 2 plants, 198 MW** — Glenarm (422, 10.6702 vs
  10.3895, the mixed-facility case above) and Greenleaf One (10350, 9.5462 vs
  9.0000).
* `|Δ| > 0.5` MMBtu/MWh: **40 / 43** plants; `> 1.0`: **24**.
* **Capacity-weighted −1.159 MMBtu/MWh (−10.7 %)**; generation-weighted
  **−0.884 MMBtu/MWh (−8.9 %)**.
* ratio model/measured — min 0.943, p25 1.073, median 1.117, p75 1.181, **max
  1.808**.

The largest moves are exactly the signature defect #1 predicts: the lowest-CF
peakers carry the most start fuel in their annual average. Grapeland (56472)
15.5477 → 9.5563, Center (56475) 14.5803 → 9.5251, Delano (58122) 11.8852 →
6.5725, Gilroy (55810) 11.5838 → 8.9884.

### 2.4 One known data-integrity limitation, sized and NOT repaired here

Delano Energy Center (58122, 60.5 MW) is a **broken heat-input channel, not a
machine**: over its 212 loaded hours the hourly rate runs p05 = 0.81, p25 =
3.20 against a median of 7.89, so a minority of under-reported hours drag the
plant aggregate to 6.5725 — below any real simple-cycle machine, yet **above**
the derive's 6.0 plant-level floor, so the guard passes it. (Contrast Gilroy /
Grapeland, whose loaded-hour rates sit tightly inside p25–p95 ≈ 9.3–10.1: that
is what a real machine looks like.)

`scripts/probes/_caiso146_hourly_hr_integrity.py` measures how far this reaches.
**It is a property of the shared derive in every ISO, not a CAISO defect:**

| ISO | sub-floor loaded hours | energy-wt unit HR as-is → hour-screened | Δ |
|---|---|---|---|
| CAISO | 2,537 / 73,346 (3.46 %) | 8.9312 → 9.0456 | **+0.114** |
| NYISO | 3,704 / 151,014 (2.45 %) | 10.2142 → 10.3360 | +0.122 |
| PJM | 8,435 / 544,586 (1.55 %) | 10.7227 → 10.8034 | +0.081 |
| MISO | 1,290 / 433,271 (0.30 %) | 11.2300 → 11.2439 | +0.014 |

**This session does not change the shared derive.** An hour-grain screen would
move the input of three committed keepers (nyiso-89, pjm-137, miso-106) — that
is not a CAISO session's call (rules 24 `[R-FROZEN-DERIVE]` / 25
`[R-ISO-SCOPE]`), and it is filed as a cross-cutting audit item with the numbers
above attached. The CAISO arm is armed on the artifact **exactly as the shared
script produces it**, and gate **K6** below proves the verdict does not hinge on
the affected rows: the swap is −8.9 % generation-weighted, of which the
meter-hour bias can account for at most **+1.3 points**.

---

## 3. Arms — one flag, nothing else (rule 19 `[R-ONE-MECH]`)

Both arms replay the incumbent keeper's recipe from its own `meta.json` at this
session's HEAD, `--years 2023 2024 2025` in **one invocation each**, years
sequential inside the invocation (rules 12 / 16).

| arm | bundle | delta |
|---|---|---|
| **A — control** | `results/calibration/caiso146_control_A` | none (zero-delta keeper replay at HEAD) |
| **B — treatment** | `results/calibration/caiso146_ctheatrate_B` | `--set measured_ct_heat_rates=true`, **one flag, nothing else** |

```
.venv/bin/python scripts/replay_keeper.py results/calibration/caiso139_dumpguard_B \
    --out-dir results/calibration/caiso146_control_A \
    --note "caiso-146 arm A: zero-delta replay of the caiso-139 keeper at HEAD (control)"

.venv/bin/python scripts/replay_keeper.py results/calibration/caiso139_dumpguard_B \
    --out-dir results/calibration/caiso146_ctheatrate_B \
    --set measured_ct_heat_rates=true \
    --note "caiso-146 arm B: the caiso-139 keeper recipe with ONE delta, measured_ct_heat_rates=true, on the newly derived CAISO artifact"
```

Per rule 12 the two invocations are independent and may run concurrently, capped
at 2 for CAISO per-plant multi-zone LPs. Arm A starts first and its first-year
peak RSS is measured; arm B starts concurrently only if that peak leaves margin
on the 15 GB box, otherwise the arms run sequentially. **No third arm, no
stacked mechanism, no offer-curve override.**

---

## 4. Construction gates — must all pass, else the arms are not comparable

* **K1 — flag fidelity.** Arm B's `run_config.scenario_config.measured_ct_heat_rates`
  is `true`, arm A's is `false`. Applied rows = 43 (all `flag == "ok"`).
* **K2 — control integrity.** Arm A reproduces the committed keeper's scorecard
  (same determination, same criterion statuses). A control that does not
  reproduce the keeper invalidates the comparison.
* **K3 — mechanism is LIVE** (the nyiso-89 §4a check, which caught an inert
  arm elsewhere). The class hourlies must show a real dispatch delta:
  `max |Δ CT_PEAKER MW|` **> 50 MW** in at least one year. If the arms are
  byte-identical the verdict is **`I` (inert)**, not `R`.
* **K4 — single delta.** `run_config` diff between arms is exactly the one
  boolean (plus provenance fields: timestamp, note, git sha).
* **K5 — year span.** Both bundles carry `years == [2023, 2024, 2025]`; no
  out-of-training year appears anywhere (rule 22 / D-6 quarantine).
* **K6 — Delano sensitivity (§2.4).** Reported for both arms: CT_PEAKER class
  energy and the C1 CT_PEAKER delta recomputed with plant 58122 excluded. **The
  verdict must not hinge on that row** — 60.5 MW is 1.03 % of covered capacity
  and 0.22 % of covered energy, so if excluding it flips any gate, the arm is
  reported as hinging on a broken meter and is **not** promoted this session.

---

## 5. Predicted directions — including the ones I expect to worsen

The mechanism cuts CT SRMC by roughly `Δ HR × gas` ≈ **−$2.9 / −$2.5 / −$4.1
per MWh** (2023 / 2024 / 2025, at the keeper's recorded $2.54 / $2.19 / $3.52
per MMBtu). Predictions, fixed here:

1. **CT_PEAKER energy RISES in all three years.** The class is 4–10× under-
   produced and a top-of-stack class is the most price-elastic thing in the
   fleet. **I do NOT predict the gap closes** — a $3/MWh SRMC cut cannot
   manufacture 3 TWh. Predicted magnitude: **+0.1 to +0.8 TWh** per year.
2. **C1 fuel-mix improves or is neutral for CT_PEAKER**, because the class is
   under-produced and the move is upward.
3. **C1 may WORSEN for the displaced class.** The energy has to come from
   somewhere, most plausibly `CC_REGULAR` (the other merchant gas class) or
   imports. If `CC_REGULAR` is currently over-produced this helps; if it is
   under-produced this hurts. **I record now that I do not know the sign**, and
   it will be reported either way.
4. **C3a mean LMP moves DOWN**, because CTs set price in peak hours and they
   just got cheaper. **This points at the ledgered C3a-2025 caveat (+10.9 %
   high), and that is a hazard, not a goal** — see §7.
5. **C3b / C3c**: small. C3c is a winter-morning fuel/cold-snap tail that
   caiso-144 showed the model already prices to its measured daily-spot SRMC
   ceiling; a cheaper CT fleet cannot manufacture a tail. Predicted
   **essentially unchanged**.
6. **C4 dispatch correlation**: neutral to slightly better.

## 6. Gates — pre-registered thresholds

Baselines are the incumbent keeper's own committed scorecard and its
`legitimacy_diagnostics.json`.

### 6.1 Protective (rule 20) — CT_PEAKER

`CT_PEAKER` annual energy is **1.99 % / 2.04 % / 1.15 %** of CA load
(actual, 4.1284 / 4.3261 / 2.3738 TWh against 207.4 / 212.19 / 205.59 TWh), so
the class straddles the 2 % materiality floor. **It is gated here regardless**:
`d1_gated_classes` lists `CT_PEAKER` explicitly, so C7 applies in all three
years, and C8 is checked as a protective criterion.

* **C7 / D-1 diurnal shape.** Gates: `profile_r ≥ 0.80`, `cv_ratio ≥ 0.50`.
  Keeper baseline: `profile_r` **0.901 / 0.950 / 0.836**, `cv_ratio` **2.635 /
  2.049 / 2.086**. **2025 carries only 0.036 of headroom on `profile_r` and is
  the single most exposed number in this arm.** A drop below 0.80 in any year
  is a **protective FAIL**.
* **C8 / D-2 forced share.** Peaker cap 0.15. Keeper baseline **0.0032 / 0.0104
  / 0.0012** (`ra_mustoffer_bridge`). Making CTs cheaper raises the
  denominator, so the share should fall further; a rise above 0.15 is a
  protective FAIL.
* **D-4 off-window binding** stays at 0.000 for every floor; the arm arms no
  floor and must not create one.

### 6.2 Scored criteria

Reported for both arms, all three years: C1, C2, C3a, C3b, C3c, C4, plus the
determination. **No threshold here is a kill condition** — see §7.

---

## 7. What makes this a REJECT — and what explicitly does NOT

**Rule 1 `[R-STRUCT]` + rule 14 `[R-ACCURATE]` govern this arm.** A measured
loaded heat rate is more accurate than an annual plant average. **A worse
backcast is therefore NOT a reject and NOT a reason to revert** — it is a
*discovered bug*: the input stays, and the degradation becomes a root-cause
investigation. `CT_PEAKER` is also below/at the materiality floor, so this arm
is judged on **structural faithfulness and class-level dispatch/offer
evidence, NOT on system MAE**.

**REJECT (`R`) only if the INPUT ITSELF is shown invalid:**

* **R1** — the artifact is shown not to be a measured input in the rule-13
  sense (an outcome, or fitted to a residual). Nothing in the derive fits
  anything; this is a completeness check, not an expected outcome.
* **R2** — coverage or exclusions turn out to be selective in a way §2.2 missed,
  i.e. the applied map systematically re-prices one tail of the class.
* **R3** — **K6 fails**: the result hinges on the Delano broken-meter row.

**INERT (`I`) if K3 fails** — the flag is armed but changes no dispatch.

**BLOCKS PROMOTION but is NOT a reject:**

* a **protective FAIL** (C7 `profile_r` < 0.80, or C8 > 0.15). The keeper holds
  0 of 1 protective slots and this session does not spend one. The measured
  input is still the correct input; the arm is not promoted, and the protective
  break is the finding.
* any load-bearing criterion flipping **PASS → FAIL**. Same disposition: keep
  the input, do not promote, open the root cause.

**Promotion requires:** K1–K6 pass, no protective FAIL, no PASS → FAIL flip,
and the class-level evidence showing the re-price is structurally faithful.

## 8. The ledger hazard — stated in advance

The caiso-145 ledgers do **not** forbid this work and do **not** forbid it
moving C3a-2025 or C3c. They forbid reaching for a mechanism *because* it
targets those residuals. This lever was selected off §5.2 queue item 6 on
caiso-119's CT priced-out finding, and §5 predicts a downward λ move as a
**consequence** of the re-price, not as its purpose.

Binding commitments, fixed here before any result is visible:

* **Movement in C3a-2025 is reported, never tuned toward.** No parameter,
  threshold or scope in this arm is chosen with reference to that residual, and
  none will be adjusted after seeing it.
* **A favourable C3a move is NOT the justification** for promotion, and will not
  be quoted as one. The justification is and remains rule 14 accuracy.
* **If the arm materially moves C3a-2025** (|Δ| ≥ 1.0 pp on the C3a metric), it
  is scored **leave-one-year-out within 2023–2025** before any promotion
  (rule 22): re-derived and re-scored holding out each year in turn, so an
  in-sample gain with held-out degradation is caught as overfitting.
* **No re-litigation of either ledgered caveat as an open mechanism lane.** This
  arm is not a C3a or C3c lever and is not offered as one.

## 9. Deliverables (rule 15 / 28b), regardless of verdict

* **Both arms** registered on the backcast dashboard, bundles + registry
  sidecars + `runs/<id>.js` payloads + changed `bench/` committed and pushed.
* The `measured_ct_heat_rates` **CAISO cell + evidence citation updated in
  `docs/codebase-site/data/mechanism-matrix.js` in this session** — including
  if the verdict is `R` or `I`.
* caiso-146 logged in `docs/calibration-log/caiso.md` with its own DO-NOT-REDO
  section.
* If promoted: `frontend/data/backcast/keepers/CAISO.json` +
  `build_status.py --iso CAISO` + the keeper-auditor subagent.
