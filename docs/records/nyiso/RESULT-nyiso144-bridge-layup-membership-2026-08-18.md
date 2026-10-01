# RESULT nyiso-144 — the bridge lay-up membership A/B: **ALL SIX GATES PASS, PROMOTED**

Session nyiso-144. Pre-registration:
`PREREG-nyiso144-bridge-layup-membership-2026-08-18.md`, committed **before
either arm solved**. Control `2026-08-18-nyiso-144-control`; arm
`2026-08-18-nyiso-144-layup-exclusion`. Both registered (rule 15), 2023+2024+2025
in one bundle each (rule 16), years sequential (rule 12), holdout freeze ACTIVE
and untouched.

**Keeper: `2026-08-18-nyiso-144-layup-exclusion`**, superseding
`2026-08-18-nyiso-143-n11tsl-arm`. Determination **CALIBRATED** (rubric v3.4).

---

## 1. THE HEADLINE

The commitment bridge gains the laid-up plant **membership** channel that
previously existed only on the reliability floor. nyiso-140 repaired one
*mechanism*, not the plant, so the same mothballed stations stayed floored by
the other mechanism that floors the same class — rule 19 `[R-ONE-MECH]`'s
"enumerate what already floors the same class", one mechanism later.

**One differing `scenario_config` field**: `nyiso_gas_bridge_plant_exclusions`
False → True. **Zero new free parameters** — the DOF ledger goes 39 → 40
entries with `n_residual` **UNCHANGED at 6**, because the entry is a plant-code
*set* produced by a conduct test (`n_scalars` 0).

**It buys no fit improvement, and none was expected.** Across BOTH full
`calibration_verdict` reports the only difference is a SKIPPED, non-gated
day-ahead diagnostic line. **What it buys is legitimacy** (rule 1
`[R-STRUCT]`): the bridge stops manufacturing ~0.57 TWh over three years at
plants whose own meter says they were mothballed.

## 2. THE SIX PRE-REGISTERED KILL GATES

| gate | result |
|---|---|
| **K1** armed and recorded | **PASS** — exactly one solve field differs (`nyiso_gas_bridge_plant_exclusions`); the only other meta delta is `git_sha`, and `git diff --name-only 800d475..684f6be` touches nothing under `src/`, `scripts/run_*`, `scripts/lib/` or `data/raw/` |
| **K2** liveness | **PASS** — see §3 |
| **K3** membership exactness | **PASS** — zero stray losses, zero residuals, all three years |
| **K4** no new D-4 failure | **PASS** — 17 → **3** failures, **zero new**; 14 cleared, every one a declared lay-up plant |
| **K5** no gated-criterion regression | **PASS** — C1/C2/C3a/C3b/C4/C6/C8 identical; C3c bit-unchanged |
| **K6′** forced-share escalation | **PASS without escalating** — every material class's share **falls** |

Scorer `scripts/probes/_nyiso144_layup_ab.py`; record
`results/calibration/_nyiso144_layup_ab.json`.

## 3. K2 — THE PREDICTION WAS MADE BEFORE THE SOLVE AND LANDED WITHIN 1.3 %

The pre-registration computed the expected shed from the **control's own D-4
rows**, before either arm ran, against a ±50 % band:

| year | control floored | arm floored | **measured shed** | **predicted** | error |
|---|---:|---:|---:|---:|---:|
| 2023 | 1.5071 TWh | 1.3870 TWh | **0.1201** | 0.1186 | +1.3 % |
| 2024 | 1.0460 TWh | 0.9054 TWh | **0.1406** | 0.1396 | +0.7 % |
| 2025 | 1.1060 TWh | 0.7961 TWh | **0.3099** | 0.3089 | +0.3 % |

Total bridge floor volume (all rows, from the solve logs) falls 2.14 → 1.95,
2.17 → 1.94, 1.78 → 1.41 TWh.

## 4. K3/K4 — THE MEMBERSHIP IS EXACTLY THE DECLARED SET

Plants that lost their bridge floor, by year:

* 2023 — 2480, 2625, 8006, 10190, 54034, 56188
* 2024 — 2480, 2625, 8006, 10190, 54034, 56188
* 2025 — 2480, 2625, 8006, 10190, 54034, **54592**, 56188

**Zero** non-declared plants lost a floor; **zero** declared plants kept one.

D-4 unit-conduct failures fall **17 → 3**, with **no new failure anywhere**.
The 14 cleared are all `nyiso_gas_commitment_bridge` rows on declared lay-up
plants — including the two largest the nyiso-143 rider convicted, **8006
Roseton** (2025: 0.1881 TWh, 44.9 % of that leg, 60.9 % of floored hours metered
at zero) and **2480 Danskammer**.

## 5. K6′ — NO ESCALATION NEEDED, WHICH IS THE OPPOSITE OF nyiso-140

D-2 forced share, control → arm:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| ST_GAS | 20.2 → **19.7 %** | 24.9 → **23.9 %** | 16.7 → **14.7 %** |
| CC_REGULAR | 4.8 → **4.4 %** | 2.6 → **2.4 %** | 1.9 → **1.8 %** |
| CT_CHP | 17.8 → 17.5 % | 27.2 → 26.7 % | 6.2 → 6.0 % |
| hydro | 21.3 → 21.3 % | 23.1 → 23.1 % | 38.2 → 38.3 % |

Every material class falls. At nyiso-140 the surviving bridge share *rose*
while doing strictly less work, which is what forced the K6′ escalation; here
the mechanism does less work **and** carries less share.

## 6. K5 — WHAT MOVED, IN FULL

Diffing both complete `calibration_verdict` reports yields **eight lines**, all
one non-gated diagnostic:

```
C3a da_diagnostic   2023  +6.7 % → +7.0 %
                    2024  +0.3 % → +0.6 %
                    2025  -0.6 % → -0.2 %
```

Everything else is identical: C1 PASS, C2 PASS, C3a PASS, C3b PASS, C4 PASS,
C8 PASS, and **C3c 2 / 0 / 5 h against RT actual 10 / 13 / 42 h — bit-unchanged**.
This arm changes commitment membership, not price formation.

## 7. THE C3c LEDGER — LINEAGE CARRIED, RATIONALE RESTATED

The magnitude is re-measured and unchanged, so the ledger entry is carried. Its
**reason is rewritten rather than inherited**: the incumbent's reads *"C3c
regresses in exchange for a published input replacing a netted estimate"* —
nyiso-143's trade-off, not this arm's, which regresses nothing. Carrying that
sentence would assert a trade-off that did not happen. **The nyiso-143
structure-over-gates clause is neither invoked nor needed here.**

## 8. TWO PLANTS DELIBERATELY LEFT IN — declared before the solve

Both were named in the pre-registration so neither could be added after seeing
a residual:

* **7314** is the eighth D-4 FAIL (2025: 0.0774 TWh, 2,235 h, **77.1 %** of
  them metered at zero) and does **not** pass the lay-up test. It is a cycler
  the model's own P0 over-runs, so its forcing is an **offer/economics** defect;
  excluding it here would bury that error inside a membership list (rules 1 /
  14). **It is the named successor.**
* **2517 Port Jefferson** is correctly excluded from the reliability FLOOR
  (whose always-on baseline it does not have) but stays in the BRIDGE
  population, which is keyed to detected runs it genuinely performs. Its
  committed D-4 verdict on this mechanism is `pass` in all three years.

## 9. A CORRECTION TO THE RECORD, made before the solve

The nyiso-144 handoff (from `RESULT-nyiso143` §6 / `ASSESSMENT-nyiso143` §2.3)
states the bridge floors 2517 for **0.1495 TWh in 2024**, 34.6 % of that leg,
**4,623 h**, median **0.000 MW**, **71.2 %** at zero. The keeper's own committed
`legitimacy_diagnostics.json` says **0.0616 TWh**, 19.5 %, **1,716 h**, median
**45.222 MW**, **44.7 %** at zero, verdict **pass**.

The Roseton row matches the handoff exactly; 2517's and 7314's do not. The
committed artifact is the source of truth, and the arm was scoped to what it
says. (Likely provenance: the assessment's own note that a first, payload-based
rider run covering 100 plants and substituting 127 was superseded by the
full-dispatch numbers.)

## 10. GOVERNANCE

* Pre-registered before either solve; both arms registered (rule 15); all three
  years in one bundle each (rule 16); years sequential (rule 12).
* Holdout freeze **ACTIVE**; every year solved, scored or read is 2023–2025
  (rule 22).
* Rule 22 D-5(b): the superseded keeper **re-scores CALIBRATED at this HEAD**,
  so the worse-determination stop does not fire; `calibration-complete.json`'s
  NYISO entry is re-keyed with the determination re-verified from committed
  artifacts, no solve. `scripts/audit_keepers.py --iso NYISO` passes clean.
* Rule 28(b)/(c): the NYISO matrix shard's bridge cell and keeper stamp are
  re-stamped, and the new `ScenarioConfig` field is registered under the bridge
  row's documented sub-scalar escape hatch.
* Rules 25 / 28(d): **transfers to no other ISO** — any other ISO must identify
  its own laid-up units from its OWN CAMPD conduct. No other ISO's shard,
  keeper shard or lane file touched.

## 11. REPRODUCTION

```
python scripts/data/derive_campd_bridge_layup_exclusions.py --iso NYISO --detail
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso143_n11tsl_arm \
    --out-dir results/calibration/nyiso144_control
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso144_arm_recipe \
    --out-dir results/calibration/nyiso144_layup_arm
python scripts/legitimacy_diagnostics.py --bundle <dir> --iso NYISO --json-out <dir>/legitimacy_diagnostics.json
python scripts/gen_nyiso144_attestation.py --bundle results/calibration/nyiso144_layup_arm
python scripts/probes/_nyiso144_layup_ab.py
```
