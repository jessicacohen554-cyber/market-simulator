# FINDING — nyiso-185 (`stgas-family-hr-ab` lane): the family heat-rate A/B is SOLVED — the C1-2023 `ST_GAS` cell clears, C3a-2025 improves, and C1-2024 `CC_REGULAR` crosses its share band; registered as a **KEEPER CANDIDATE** under the pre-registered verdict rule, disposition to the owner

**Session:** nyiso-185, `stgas-family-hr-ab` lane
(`claude/nyiso-185-stgas-family-hr-ab`), NYISO backcast-calibration track,
2026-09-04. **Solves run: TWO** — the arm (registered,
`2026-09-04-nyiso-185-family-hr`, bundle `results/calibration/nyiso185_family_hr`)
and the same-HEAD control (`results/calibration/nyiso185_control`, an
INSTRUMENT: bit-identical to the committed keeper, registers nothing).
**Keeper at entry and exit: `2026-09-02-nyiso-177-vintage-matched`** —
determination NOT-YET, target grade 5, fail set {C1-2023 `ST_GAS` +3.86 TWh,
C3a-2025 −11.2 %, C3c}. **Unchanged: this session does not promote.**
**Pre-registration:** `results/calibration/PREREG-nyiso185-stgas-family-hr-ab.md`,
pushed to `origin` at `588aa141` before the first measurement; its §0
discloses that this author holds nyiso-184's post-hoc numbers in context.
**Owner ruling carried (2026-09-04, verbatim):** *"If structural integrity
improves but gates regress that may still be a keeper.."* — read as
authorizing the A/B nyiso-184's S2 withheld, NOT as a promotion in advance.
**Machine records:** `results/calibration/_nyiso185_grounding.json` (G0/G1),
`results/calibration/nyiso185_family_hr/calibration_attestation.json`
(`computed_checks`: G-CONTROL / G-DELTA / G-INPUTS / G-DOF / G-ENGAGE, every
premise computed by `scripts/gen_nyiso185_attestation.py`), the arm's
`metrics.json` + `legitimacy_diagnostics.json`; probe
`scripts/probes/nyiso185_grounding.py`.

---

## 1. The result in one paragraph

The arm is the committed keeper recipe replayed at HEAD plus exactly one
field, `egrid_family_heat_rates=True` (G-DELTA: one field, nothing rode
along; G-CONTROL: the no-override replay reproduces the committed keeper
**bit-identically, 0 of 52,560 hourly zonal prices differ in every year**, so
the 23 LP-relevant commits since the keeper's basis and the
`fossil_announced_exits_enabled` default flip are LP-inert for this backcast
and the committed keeper IS the baseline). The grounding bar fired on all
three legs before the solve (G1: Ravenswood's heat-side factor 1.029 inside
the peers' [1.0006, 1.0707]; eGRID family heat = CEMS heat to 1e-9;
plant-level EIA-923 net ÷ CAMPD gross 0.948 inside the peers' [0.888, 0.959]).
**Scored: NOT-YET, target grade 5, fails 3 — the same grade and fail count as
the keeper, with a different C1 cell.** C1-2023 `ST_GAS` goes **+3.86 → +2.16
TWh (FAIL → PASS)**; C1-2024 `CC_REGULAR` goes **+3.34 → +3.87 TWh, share
2.78 → 3.18 pp (PASS → FAIL on the share band)**; C3a-2025 **−11.2 → −10.5 %**
(still FAIL, owner-court); C3b, C2, C4, C8 PASS; C3c unchanged (1 / 0 / 1 h vs
10 / 13 / 42). Under PREREG §4's verdict rule (rejected iff C2 / C3a / C3b /
C8 flips PASS → FAIL — none did, and G1 fired) the arm is a **KEEPER
CANDIDATE**. Its structural case: a rule-24 per-plant dict and a rule-21 hand
value at Ravenswood are replaced by a measured, vintage-reproducible eGRID
construction with zero free parameters and zero new DOF entries. Its cost: one
load-bearing cell moves from 2023 steam to 2024 combined cycle, and 2024 /
2025 `ST_GAS` deepen as pre-declared. **The disposition is the owner's.**

---

## 2. The gates, as pre-registered and as measured

| gate | statistic | measured | bar | verdict |
|---|---|---|---|---|
| G0 | armed no-LP reconstruction: plants moved | exactly the nyiso-184 footprint (7 plants, 64 tranche rows, 6,335 MW) | ⊆ footprint | PASS |
| G0 | (2500, `ST_GAS`) tranche ratio on ÷ off | 1.29387 (= 12.2918 ÷ 9.5) | ± 1e-3 | PASS |
| G0 | (2500, `CC_REGULAR`) tranche ratio on ÷ off | 0.83517 (= 7.3499 ÷ 8.8005) | ± 1e-3 | PASS |
| G1a | `F_H` = CAMPD all-hours HR ÷ running-hour HR, Ravenswood steam | **1.029** | peers [1.0006, 1.0707] | HOLDS |
| G1b | `F_B` = eGRID ST-family `HTIAN` ÷ CAMPD steam heat | **1.0000** | [0.99, 1.01] | HOLDS |
| G1c | plant `PLNGENAN` ÷ CAMPD gross over EVERY unit of 2500 | **0.948** | peers [0.888, 0.959] | HOLDS |
| G2 | control vs committed keeper, hourly zonal price | 0 / 0 / 0 of 52,560 differ; max \|Δ\| 0.0 | measured | bit-identical → keeper is the baseline |
| G-DELTA | arm vs control `scenario_config` | `egrid_family_heat_rates` False → True, nothing else | one field | PASS |

**G1d, reported not gated:** `F_D` (gross ÷ EIA-923 net) 1.115 for the steam
family (peers 1.043–1.112), 1.029 for the CC family; per generator net ÷ gross
0.913 (unit 10, CF 8.4 %), 0.933 (unit 20, CF 6.8 %), **0.862 (unit 30, CF
4.2 %)** — nyiso-184 §3.1's number, on the denominator the construction does
not control.

---

## 3. The A/B, at full magnitude (keeper = baseline, bit-identical control)

### 3.1 Criteria

| criterion | keeper | arm |
|---|---|---|
| **C1 2023 `ST_GAS`** (actual 8.141) | 11.999, **+3.86 TWh, +3.21 pp — FAIL** | 10.299, **+2.16 TWh, +1.85 pp — PASS** |
| C1 2023 `CC_REGULAR` (actual 33.012) | 32.796, −0.22 — PASS | 33.587, +0.58 — PASS |
| **C1 2024 `CC_REGULAR`** (actual 34.060) | 37.401, +3.34 TWh, +2.78 pp — PASS | 37.934, **+3.87 TWh, +3.18 pp — FAIL (share)** |
| C1 2024 `ST_GAS` (actual 9.913) | 9.799, −0.11 — PASS | 8.821, −1.09 — PASS |
| C1 2025 `ST_GAS` (actual 13.712; SKIPPED, preliminary 923) | 10.014, −3.70 | 9.370, **−4.34** |
| C1 2025 `CC_REGULAR` (actual 33.544; SKIPPED) | 35.807, +2.26 | 36.117, +2.57 |
| C1 free / all | 9/10 · 13/14 | 9/10 · 13/14 |
| C2 | PASS | PASS |
| C3a 2023 (RT 32.25) | 32.96 (+2.2 %) | 33.75 (+4.7 %) |
| C3a 2024 (RT 38.12) | 37.79 (−0.9 %) | 38.25 (+0.3 %) |
| **C3a 2025** (RT 66.43) | 58.99 (**−11.2 %**) FAIL | 59.48 (**−10.5 %**) FAIL |
| C3b NRMSE 2023 / 2024 / 2025 | 0.115 / 0.173 / 0.196 | 0.122 / 0.173 / 0.191 |
| C3c (h > $300, model vs RT) | 1/10, 0/13, 1/42 FAIL | identical |
| C4 | PASS | PASS |
| C6 | PASS (attested) | PASS (attested, computed premises) |
| C8 `ST_GAS` D-2 share | 0.177 / 0.237 / 0.198 PASS | 0.192 / 0.253 / 0.203 PASS |
| C8 `CC_REGULAR` D-2 share | 0.044 / 0.039 / 0.034 PASS | 0.049 / 0.034 / 0.033 PASS |
| C5a CO2 (reported) | +3.0 / +1.2 / +4.7 % | +1.8 / +0.6 / +4.3 % |
| **determination** | **NOT-YET, grade 5, fails 3** | **NOT-YET, grade 5, fails 3** |

### 3.2 Where the energy went (unit-hourly sidecars, control vs arm, TWh)

| year | Ravenswood `ST_GAS` | other ten `ST_GAS` | class `ST_GAS` | Ravenswood `CC_REGULAR` | `CC_REGULAR` ex-Ravenswood | class `CC_REGULAR` |
|---|---|---|---|---|---|---|
| 2023 | 6.328 → 4.181 (**−2.147**) | 5.691 → 6.136 (+0.445; Arthur Kill +0.390) | 12.020 → 10.317 | 1.931 → 1.935 (+0.004) | 30.942 → 31.731 (+0.789) | 32.873 → 33.666 |
| 2024 | 3.468 → 2.317 (**−1.151**) | 6.365 → 6.535 (+0.170) | 9.833 → 8.852 | 1.916 → 1.950 (+0.034) | 35.722 → 36.225 (+0.503) | 37.638 → 38.175 |
| 2025 | 2.688 → 1.851 (**−0.837**) | 7.481 → 7.657 (+0.176) | 10.169 → 9.508 | 1.958 → 1.968 (+0.010) | 34.510 → 34.817 (+0.307) | 36.468 → 36.784 |

*(The control's 2023 Ravenswood 6.328 TWh reproduces nyiso-181's unreproducible
figure exactly, so that record is now re-grounded on a committed bit-identical
replay.)*

### 3.3 The pre-declared expectations, checked

| PREREG §4 expectation | outcome |
|---|---|
| (i) Ravenswood `ST_GAS` FALLS every year | **yes**: −2.15 / −1.15 / −0.84 TWh |
| (ii) C1-2023 `ST_GAS` moves toward zero | **yes**: +3.86 → +2.16 TWh, the cell PASSES |
| (iii) 2024 / 2025 `ST_GAS` DEEPEN | **yes**: −0.11 → −1.09 (in band) and −3.70 → −4.34 (unscored) — the nyiso-140 precedent, expected of a correct repair, not compensated |
| (iv) Ravenswood `CC_REGULAR` RISES | **barely**: +0.004 / +0.034 / +0.010 TWh — the block already runs ~82 % CF, so a cheaper family rate cannot move it; the `CC_REGULAR` gain is at OTHER plants (+0.79 / +0.50 / +0.31), which is what crosses the 2024 share band |
| (v) no price claim | C3a-2025 improves 0.7 pp and 2023 worsens 2.5 pp; **nothing banked** |

### 3.4 Legitimacy diagnostics

D-1, D-2, D-5, D-9, D-10 PASS on both. D-4 reads `passed: false` on **both**,
on the SAME five unit-conduct rider rows (the rule-17 signature nyiso-181 §7
recorded: `reliability_floor × ST_GAS` at 2480 and 2500 in 2023 / 2024, the gas
bridge at 54574 in 2024). Ravenswood's rider share **rises 0.0042 → 0.0183
(2023) and 0.0077 → 0.0207 (2024)**: with its steam dearer, the floor now
holds it in a few more metered-off hours that economics no longer fill. Small
in TWh, real in direction, reported. `ST_GAS`'s C8 share rises 0.177 → 0.192 /
0.237 → 0.253 / 0.198 → 0.203 (bar 0.30; the nyiso-181 grain under-count
escalation stands, and 2024 is the closest cell).

### 3.5 LOYO

The mechanism carries no fitted scalar (G-DOF: 0 added), so leave-one-year-out
reduces to the per-year record above: 2023 improves on C1, 2024 regresses on C1
(`CC_REGULAR` share), 2025 improves on C3a and deepens on the unscored `ST_GAS`
row. There is no in-sample year the construction was fitted to, so the
"in-sample gain with held-out degradation" signature LOYO exists to catch
cannot arise; what the split shows is a real trade across years, stated as
such.

---

## 4. The case, both ways, for the owner

**For promotion (rules 14 + 1, the owner's formula):**
1. The keeper prices 1,725 MW of steam through `MIXED_FACILITY_STEAM_HR[2500] =
   9.5` — a hardcoded per-plant dict (rule 24) whose value its own comment
   derives from assumed capacity factors that are wrong by a factor of two
   against the meter (rule 21). The arm prices it from eGRID at the grain
   eGRID publishes, on the identical net-annual basis every peer already
   carries, from the same vintage and window the join reads. Zero parameters;
   regenerates per vintage; responds to changed conditions.
2. Both halves of one blend move apart as the source says they should (steam
   12.29, CC 7.35); the construction's footprint beyond Ravenswood is seven
   plants at ≤ 0.5 MMBtu/MWh, all from the same rule.
3. The pre-declared consequence arrived: Ravenswood's economic excess falls by
   a third in 2023, and the C1-2023 cell that has failed since nyiso-177
   passes. C3a-2025 moves the right way.
4. Same grade, same fail count, C6 attested with computed premises, C8 PASS.

**Against promotion, at full magnitude:**
1. **C1-2024 `CC_REGULAR` crosses its share band** (+3.34 → +3.87 TWh, 2.78 →
   3.18 pp). The keeper sat marginally inside that band; the volume Ravenswood's
   steam gives up is picked up by other combined cycles, in a class already
   over. That is the nyiso-177 §5.3 pattern in mirror image — a cell the
   keeper passed on ~0.2 pp of margin that a wrong heat rate was supplying.
2. **2024 / 2025 `ST_GAS` deepen** (−0.11 → −1.09; −3.70 → −4.34) exactly as
   pre-declared: the other ten plants are short by −6.8 / −8.0 TWh
   economically and this repair removes volume from the eleventh. That deficit
   is the next object, not this mechanism's.
3. C3a-2023 worsens +2.2 → +4.7 % (in band); C3b-2023 0.115 → 0.122 (in band).
4. Ravenswood's rule-17 rider share rises (§3.4).

**This session's recommendation, stated so it can be overruled:** promote.
The arm is more structurally faithful on every dimension rule 1 names, its
one regression is a marginal band crossing in a class the keeper already
over-ran, and the gain it books is the cell the lane has been chasing for
five sessions. **It is registered as a candidate, not promoted, per PREREG §4
and the brief's step 5.**

---

## 5. What this session does NOT claim

* The construction is not proved to be the "right" loaded heat rate for
  Ravenswood; it is proved to be the class's basis (G1). nyiso-184's G2c miss
  on the denominator stands as recorded and was not re-litigated.
* The 2024 `CC_REGULAR` crossing is not attributed to a named CC mechanism
  here; it is the class absorbing steam volume. Which combined cycles take it,
  and whether their own bases are right, is an open question.
* Ravenswood's own CC did not move (+0.2–1.8 %); expectation (iv) held only
  in sign.
* The second object (the merit-panel stack-duplicate defect at Astoria) was
  not opened — no time remained for its own pre-registered A/B.

## 6. Governance

Rule 1: nothing adopted or rejected on a residual; the verdict rule was fixed
before the solve. Rules 5 / 21 / 23: zero parameters, zero new DOF entries (13
/ 6 carried verbatim), no re-derivation. Rule 13: the construction reads
published eGRID fields; CAMPD diagnosed only. Rule 15: the arm is registered
(`2026-09-04-nyiso-185-family-hr`); the bit-identical control registers
nothing; retention pruned `2026-08-22-nyiso-152-duty-complete` (top-15).
Rule 16 / 12: one invocation each, years sequential, two concurrent solves
under 15 GB. Rule 19: superseded, never stacked (G0 proves the dict skip).
Rule 22: 2023–2025 only, no marker requested. Rule 24: one registered field
already on main. Rules 25 / 28: NYISO shard only, cell stays `O` annotated
KEEPER CANDIDATE / owner-court until the owner rules. Rule 27: on-disk bytes
pushed, ≥300-line blobs verified.

## 7. Handed forward

1. **Owner decision:** promote `2026-09-04-nyiso-185-family-hr` or not. If
   promoted: keeper shard + `build_status.py --iso NYISO`, the
   `calibration-keeper-auditor`, NYISO matrix re-stamp (cell → K), §5.5
   header; no `complete` marker exists, so no D-5(b) re-key.
2. **If promoted, the fail set becomes {C1-2024 `CC_REGULAR` share, C3a-2025,
   C3c}** and the shortest path to CALIBRATED is the 2024 `CC_REGULAR` over-run
   (+3.87 TWh) — a class object, not a plant one; start from which plants
   absorbed Ravenswood's volume (unit-hourly sidecars now exist on the arm).
3. The other-ten-plant `ST_GAS` deficit (−6.8 / −8.0 TWh) is unchanged and is
   the 2024 / 2025 object.
4. The Astoria merit-panel defect (nyiso-184 §4.1) remains sized and unbuilt.
