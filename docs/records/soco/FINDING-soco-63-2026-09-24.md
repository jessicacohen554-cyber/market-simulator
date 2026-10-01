# FINDING — SOCO-63 (2026-09-24): measured incremental-HR bands move the CT/ST split the WRONG way — phase 0 only, no solve

**Lane** SOCO-63 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Owner ruling on G5 scope:** BLANK in the lane prompt. So this lane ran **phase 0 only**: no field
added, `_SOCO_OFFER_CURVE` untouched, no shard, no registration.
**Keeper / control of record:** `2026-09-24-soco61-dark-unit`, unchanged. Verified at `origin/main`
`bc41b21f`: `keepers/SOCO.json` names it, and `git ls-remote origin 'refs/heads/claude/soco63*'` printed
nothing except this lane's own working branch.
**Per-plant legs:** recovered at zero LP from the SOCO-61 shard SHAs (all three fetched) into
`results/calibration/soco61_arm_<Y>`. Gitignored; 0 files tracked.
**Probe:** `scripts/probes/_soco63_phase0.py` (subcommands `derive fleet reach c4`). **LP cost: zero.**

---

## 1. HEADLINE

**The arm fails phase 0 on its own terms. It should not be taken even if the owner rules YES on G5 as
posed.**

| check | result |
|---|---|
| framing | **`phys_*` keys are inert in SOCO.** Their only consumer is `gas_offer_net_revenue_margin` (`gas_offer_margin_markup_mult`), and that mechanism is OFF in the keeper. The offer HR is set by the multiplier bands. So a real arm would have to **replace the multiplier bands** with measured values, as `committed_band_measured_basis` does for `committed`. |
| (a) measured bands | CT_PEAKER's incremental HR is **0.76 × its average**; ST_GAS's is **0.94–0.99 ×**. |
| (b) non-selective form | Because CTs get far cheaper than boilers, the split moves the **wrong way**: 2023 CT_PEAKER goes +5.23 → **+18.5 TWh (FAIL)**, 2023 ST_GAS FAIL, 2024 CT_PEAKER FAIL. |
| refused ST-only diagnostic | It still moves only +0.44 TWh of the 5.50 TWh ST deficit, because ST's committed band rises ×1.08. |
| (d) rule 14 | **The case fails.** In a start-cost-free LP tranche, average HR is the only place CT no-load fuel lives. Swapping in incremental HR deletes a real cost. Rule 14's misalignment exception applies. |

## 2. PHASE 0 (a) — THE MEASURED BANDS

The construction is `derive_campd_marginal_hr.py`'s own (`load_campd`, `derive_unit_bands`: opTime ≥ 0.95,
per-unit normalized-quadratic IO fit, cap-weighted p50, pooled 2023–2025), with two ex-ante changes:

- **Unit-grain class map.** It comes from the committed `campd_{ct,st,cc,coal}_heat_rates_SOCO_units.csv`,
  the same unit→class attribution the model's measured heat rates use. The ST file carries the ST deriver's
  capacity-rank boiler pairing.
  - There is no `bin_assignments_SOCO.csv`.
  - Plant grain is unsound at Greene County, Watson, Gaston and Barry.
  - No unit is attributed to two classes (the probe asserts this).
- **Normalization to each unit's OWN measured average HR** (`hr_gross` in the same file). That average is
  the per-plant base the model multiplies against under `measured_*_heat_rates`, so band × base equals the
  measured marginal HR exactly. The deriver's class-base normalization is also reported (`cls_*` columns);
  it agrees within ~0.03.

Scratch only: `…/scratchpad/soco63_marginal_hr_scratch.csv`. **Nothing was written to
`data/raw/reference/`.**

| class | units fitted / listed | coverage of model class MW | avg_committed p50 | marg_econ_low p50 | marg_econ_high p50 |
|---|---|---|---|---|---|
| CT_PEAKER | 74 / 79 | 91.7 % | 1.078 [1.04, 1.13] | **0.759** [0.73, 0.82] | **0.754** [0.71, 0.84] |
| ST_GAS | 12 / 12 | 108.7 %¹ | 1.080 [1.04, 1.14] | 0.942 [0.89, 0.95] | 0.990 [0.85, 1.03] |
| CC_REGULAR | 58 / 58 | 109.5 %¹ | 1.032 [1.02, 1.07] | 1.007 [0.92, 1.04] | 1.185 [1.00, 1.23] |
| COAL | 15 / 15 | 99.8 % | 1.043 [1.02, 1.07] | 0.930 [0.91, 0.97] | 0.969 [0.92, 1.06] |

¹ CEMS `cap_mw` (p97 gross load) exceeds the model's net availability-capped class MW. That is basis, not
extra units.

**Physics check.** A simple-cycle gas turbine's heat input is roughly `no-load + b × P`. At full load the
no-load share is ~20–30 % of heat input, so incremental ≈ 0.70–0.80 × average. The CT number is physical, not
a fit artifact.

## 3. PHASE 0 (b) — THE NON-SELECTIVE FORM AND RULE 19

**Declared ex ante.** Every covered class gets its own measured bands, mapped as follows:

- `committed` → `avg_committed`;
- `econlo` → `marg_econ_low`;
- `econhi` → `marg_econ_high`;
- `peak` and `mustrun` → 1.0 (not measured by the artifact; the rule-24 neutral);
- CHP classes → 1.0 (no artifact row).

This mirrors `committed_band_measured_basis`'s non-selective precedent. ST alone would be a selection and is
refused.

**Rule 19 relation.**

| mechanism | relation to the arm |
|---|---|
| `measured_*_heat_rates` | Stays the base, and the band is a ratio on it. With own-average normalization the two cannot double-count. |
| PRB passthrough sigmoid | Already inside the coal fuel term, so a coal econ band would multiply it. The `committed_band_measured_basis` charter shows that stacking lands on the measurement in no year. |
| `coal_warm_committed` | Prices the same coal `_committed` tranche. |
| `coal_econ_marginal_hr_bound` (ERCOT-only, off) | Same operand. |
| `tranche_startup_amortization` (G) | The only other carrier of CT fixed cost (§4). |

The arm field does not exist, so the unit_id-grain `fleet`/`fleetcmp` comparison was **not run**. The
control fleet was built (`fleet`, one process per year). It reproduces the solved `mc` to within 2e-6 $/MWh,
and the arm side is the exact analytical re-price `mc + (b − 1) × HR × fuel` on the named tranches only.

## 4. PHASE 0 (c) — CHECKS A–F (keeper legs, zero LP)

**Method.** Greedy hourly re-stack over the economic thermal tranches:

- Nuclear, hydro, storage, wind, solar, interchange and `_mustrun` tranches are held at the solved dispatch.
  Energy-limited classes are excluded from headroom.
- Reported as **greedy arm − greedy control**, so greedy bias cancels.
- Greedy control vs solved: CT 9.79 vs 9.56, ST 3.21 vs 3.80 TWh (2023).

**A — distance** (generation-weighted offer, $/MWh, control → arm):

| year | CT_PEAKER | ST_GAS | CC_REGULAR | COAL |
|---|---|---|---|---|
| 2023 | 34.00 → **27.65** | 34.35 → 34.77 | 23.52 → 24.83 | 28.16 → 28.67 |
| 2024 | 31.93 → 25.89 | 32.44 → 32.88 | 22.03 → 23.22 | 27.40 → 27.77 |
| 2025 | 45.52 → 36.55 | 46.35 → 47.25 | 31.53 → 33.27 | 32.20 → 32.46 |

The near-tie does not resolve in the boilers' favour: CTs drop ~$6/MWh **below** them.

**B/E — predicted C1 rows** (committed scorer re-run on the shifted `gmModel`; 2025 rows SKIPPED as
preliminary). Scale ×1 is the non-selective arm; ×0.5 and ×2 are check D on the band deviation.

| row | keeper | ×1 | ×0.5 | ×2 |
|---|---|---|---|---|
| 2023 CT_PEAKER | +5.23 / +2.19 pp | **+18.48 / +7.7 pp FAIL** | +7.08 / +3.0 pp (0.04 pp margin) | FAIL +22.3 pp |
| 2023 ST_GAS | −5.50 / −2.26 pp | **−7.60 / −3.1 pp FAIL** | −7.04 / −2.9 pp | FAIL |
| 2023 CC_REGULAR | +2.30 / +1.3 pp | −5.77 / −2.1 pp | — | FAIL −16.0 pp |
| 2024 CT_PEAKER | +2.36 / +0.98 pp | **+14.76 / +5.9 pp FAIL** | +5.09 / +2.1 pp | FAIL |
| 2024 ST_GAS | −4.69 / −1.81 pp | −6.77 / −2.6 pp | −6.14 / −2.4 pp | −2.6 pp |
| 2024 CC_REGULAR | +3.14 / +2.19 pp | −4.25 / −0.8 pp | +2.63 / +2.0 pp | FAIL −15.6 pp |
| 2024 COAL_PRB | −4.19 / −1.45 pp | −6.76 / −2.5 pp (0.52 pp margin) | — | FAIL −3.2 pp |

- **Check D.** The direction holds at every scale. Even at half-strength both 2023 rows land within
  0.1 pp of failing.
- **Ex-ante requirement not met.** The prompt required showing that neither 2023 CT/ST row crosses its band.
  **Both cross at ×1.**

**C4 coal** (keeper reproduced exactly, r / NRMSE):

| year | keeper | arm |
|---|---|---|
| 2023 | 0.904 / 0.210 | 0.887 / 0.275 |
| 2024 | 0.843 / 0.235 | 0.837 / **0.290** (0.01 from the 0.30 gate) |
| 2025 | 0.882 / 0.200 | 0.846 / 0.186 |

**F — per-plant Σ|model − 923|, TWh, keeper → arm:**

| year | CT_PEAKER | ST_GAS | CC_REGULAR |
|---|---|---|---|
| 2023 | 8.68 → **19.62** | 5.35 → 7.46 | 11.97 → 12.00 |
| 2024 | 7.06 → 16.38 | 4.51 → 6.58 | 9.29 → 9.99 |
| 2025 | 6.19 → 15.89 | 4.99 → 6.52 | 10.49 → 12.94 |

**Refused ST-only selection (diagnostic, never armable):**

- 2023 ST −5.50 → −5.05 TWh; CT +5.23 → +4.79 TWh.
- ST's generation-weighted offer *rises* (34.35 → 34.77), because `committed` ×1.080 outweighs the econ
  drop.
- So even the forbidden selection reaches ~8 % of the object.

## 5. PHASE 0 (d) — RULE 14 DOES NOT CARRY THE CASE

"If the only argument for this arm were that 2023 ST_GAS passes, it would not be taken." Here it does not
even have that argument.

The rule-14 claim was: the identity band misstates a measured physical input-output curve. At the
representation SOCO actually has, that claim is false:

- a pure-LP tranche carries **no no-load cost**;
- CT econ/peak tranches carry **no start cost** (`tranche_startup_amortization` G);
- so the average HR is the **only** place a CT's no-load fuel is charged.

Replacing it with the incremental HR does not correct a misstatement. It **deletes a real cost** from
91.7 % of CT capacity. The measured incremental curve is correct physics that is **misaligned to the
representation**, which is exactly rule 14's exception. It becomes admissible only **jointly with** a
no-load/start-cost carrier on the CT tranches, and that carrier is the G'd cell.

## 6. GOVERNANCE / GATES

- No `ScenarioConfig` field. No bundle, sidecar, payload or bench part. No offer band touched, and no
  `authorized_price_tuning` key.
- The keeper's reads are unchanged: C1 14/14 · free 10/10 · C2/C4/C6/C8 PASS · C3a/b/c UNSCORABLE · grade
  5/5/0 · DOF 13/1. The scorer's literal "PHYSICALLY-CALIBRATED (PRICE UNSCORED)" is not SOCO's
  determination.
- **Matrix (rule 28(b)):** no verdict changed. SOCO-63 notes were prepended to
  `committed_band_measured_basis` (U), `tranche_startup_amortization` (G) and
  `gas_offer_net_revenue_margin` (U) in the SOCO shard, plus a §5.8 note. `check_mechanism_matrix.py`
  passes.
- **E13 standing:** `2026-09-20-soco53g-prb-own-iso` is still unruled, and rule 31 forbids deleting it.
  **Owner question, re-raised:** decline it? (Standing recommendation: decline.)

## 7. ROUTED — THE OWNER QUESTION, RE-POSED

The G5 question as posed ("measured `phys_*` bands") has a mechanical answer (inert) and a substantive
answer (wrong-way). **Recommendation: do not open G5 for incremental-HR bands on their own.**

The only structure that would separate committed boilers from CT blocks is a CT **start/no-load cost** on
the econ/peak tranches. Incremental-HR bands could then ride on top of it without deleting CT fixed cost.

**The question for the owner:** is there new evidence that would justify reopening
`tranche_startup_amortization` (G) for SOCO, jointly with measured incremental-HR bands? Absent that, the
2023 split stays a ledgered near-tie at a 0.74 / 0.81 pp margin.

Leftover shard refs for the owner (a session cannot delete refs): `claude/soco61-arm-{2023,2024,2025}`,
`claude/soco60-arm-*`, `claude/soco60-armB-*`. SOCO-63 created **no** shard branches.

## 8. WHERE EVERY BYTE LIVES

- Nothing was solved, so there is **no promotion question** from this lane.
- The keeper bundle on `main` is untouched.
- The scratch derivation CSV and the fleet `.npz` arrays live only in this container's scratchpad. They are
  regenerable in ~2 min with `_soco63_phase0.py derive` and `fleet`.

## Log entry

```
## soco-63 — 2026-09-24

MEASURED INCREMENTAL-HR BANDS MOVE THE CT/ST SPLIT THE WRONG WAY -- PHASE 0
ONLY, ZERO LP. Owner G5 ruling blank, so no field, no solve, _SOCO_OFFER_CURVE
untouched. Keeper 2026-09-24-soco61-dark-unit unchanged.

Framing: phys_* keys are consumed only by gas_offer_net_revenue_margin (OFF in
SOCO), so "measured phys_* bands" are inert; a real arm must replace the
multiplier bands. CEMS IO-slope derivation at UNIT grain (committed per-unit
HR artifacts as class map; own-average normalization), cap-weighted p50:
CT_PEAKER marg 0.759/0.754 of average, ST_GAS 0.942/0.990, CC 1.007/1.185,
COAL 0.930/0.969; committed 1.078/1.080/1.032/1.043; CT coverage 91.7 %.
Non-selective form, greedy re-stack on the keeper legs (arm minus greedy
control): CT offer 34.00 -> 27.65 $/MWh below boilers 34.77; 2023 CT_PEAKER
+5.23 -> +18.48 TWh FAIL, 2023 ST_GAS -7.60 FAIL, 2024 CT_PEAKER +14.76 FAIL;
C4 2024 coal NRMSE 0.235 -> 0.290; per-plant CT error 8.68 -> 19.62 TWh. x0.5
and x2 same direction. Refused ST-only diagnostic reaches +0.44 of 5.50 TWh.
Rule 14 fails: in a start-cost-free LP the average HR is the only carrier of CT
no-load fuel; incremental HR is admissible only jointly with a CT start/no-load
carrier (tranche_startup_amortization, G).

OWNER QUESTIONS: (1) any new evidence to reopen tranche_startup_amortization
(G) for SOCO jointly with measured incremental-HR bands? (recommendation: do
not open G5 for incremental-HR bands alone) (2) decline
2026-09-20-soco53g-prb-own-iso (E13)? Leftover refs for the owner:
claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-63-2026-09-24.md,
scripts/probes/_soco63_phase0.py.
```
