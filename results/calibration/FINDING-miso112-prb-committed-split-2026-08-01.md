# FINDING miso-112 — COAL_PRB committed-band SPLIT (C7 amplitude lane)

Session miso-112, 2026-07-31/2026-08-01, branch
`claude/miso-112-coal-prb-split-yn0al4`, off `origin/main` (miso-111 merged
at 7b0e406, so this branch carries its artifacts).
Pre-registration committed BEFORE the slice measurement (f9d5d61) and its
post-measurement readout before any solve (c7424c5):
`results/calibration/PREREG-miso112-prb-committed-split-2026-08-01.md`
(filename `...-2026-07-31.md`).

## 0. Verdict

**REJECTED on pre-registered guard G2. Keeper `2026-07-31-miso-109b-hy-level`
stays.** The lane the PREREG opened — "split the committed band, one slice
holds, one cycles" — is **CLOSED IN THIS FORM, both ways**, which is the
outcome §6 said in advance would be valuable enough to register. A named,
measured successor is identified in §5 and it is NOT a variant of this arm.

## 1. The mechanism as built

`coal_prb_committed_split` (ScenarioConfig, default off). For a regulated
(`eia860_selfcommit_scope_plants()`) PRB/subbituminous CAMPD-binned plant
with a flat committed band, the `_committed` tranche splits at the plant's
own MEASURED within-run night level:

```
hold_cap = min(committed_cap, max(0, night_p50 − pct_mr/100) × nameplate)
cyc_cap  = committed_cap − hold_cap
```

- hold-through slice keeps suffix `_committed` — anchor tags and the
  `1 − contract_share` regulated take-or-pay discount;
- cycling slice `_commitcyc` bids full delivered cost under its supply
  passthrough, with the `coal_econ_srmc_bound` ≥ 1.0 clamp;
- `_mustrun` untouched, no floor anywhere, zero fitted parameters.

`night_p50` = p50 of plant load / HSL over ONLINE hours h0–5, pooled
2023–25, WP-3 loading-when-on construction — artifact
`data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv`, frozen
deriver `scripts/data/derive_prb_committed_split.py` (rule 23).

## 2. Phase 2 — the measurement (kill rules did not fire)

30 MISO COAL_PRB plants (26 REG, 4 MER); every REG plant carries a
`thermal_tranches_MISO.csv` COAL row, so the readout basis IS the runtime
basis (`COAL_MUSTRUN_BY_PLANT` holds no MISO plant — verified).

- **K1 NOT fired** — cap-weighted hold share of the band **0.286** (≥0.05).
- **K2 NOT fired** — cap-weighted cycling share **0.714** (≥0.05).
- P-A predicted 0.35/0.65 from miso-111's class aggregates; plant-resolved
  gives 0.29/0.71.
- **The heterogeneity is the point**: 8 plants measure `night_p50 ≤`
  their mustrun band (whole band cycles — miso-111's form is correct at
  *those* plants, per their own meter), 12 measure `night_p50 ≥` the band
  top (the keeper's form persists there), and **only 6 genuinely split**.
  miso-111 applied one answer to all 26; both uniform answers are refuted
  per-plant.

## 3. Phase 3 — the A/B

Arms, each 2023+2024+2025 in ONE bundle (rule 16), years chained
sequentially (rule 12) via `scripts/probes/_miso112_chain.sh`:

- **A (control)** `results/calibration/miso112_control_A` →
  `2026-08-01-miso-112a-control`
- **B (arm)** `results/calibration/miso112_prbsplit_B` →
  `2026-08-01-miso-112b-prb-split` (A + `coal_prb_committed_split=true`)

**Control integrity.** Arm A reproduces the committed 109b keeper at
**L1 0.00000 %** in 2023 and 2024 (max class-hour |diff| 0.000 MW); 2025
carries **0.03007 %** HEAD drift, the same magnitude miso-111 measured
from ~1 day of main, with every COAL_PRB gate statistic identical to the
keeper (cv_ratio 0.314, profile_r 0.971). Every arm-B movement is
attributable to the single flag.

**Operational note for the next session (rule-12 hygiene).** The first A/B
attempt ran with `_miso112_chain.sh` **untracked**; `--reuse-solved` refuses
on a dirty `src/scripts/data` tree, so every link re-solved its whole span
in one process and arm B's 3-year link **OOM-killed at 15.9 GB**. Committing
the chain script first (974918d) restored per-year reuse and both chains
then completed. *Commit the chain script before launching it.*

### 3.1 Results

**D-1 COAL_PRB (the C7 gate), A → B:**

| year | profile_r | model off-peak CV | actual | cv_ratio | verdict |
|---|---|---|---|---|---|
| 2023 | 0.988 → 0.989 | 0.072 → 0.114 | 0.155 | **0.466 → 0.738** | FAIL → **PASS** |
| 2024 | 0.978 → 0.985 | 0.058 → 0.106 | 0.121 | **0.475 → 0.872** | FAIL → **PASS** |
| 2025 | 0.971 → 0.968 | 0.023 → 0.029 | 0.074 | **0.314 → 0.393** | FAIL → FAIL |

**C-series, arm B:** C1 **15/16 (free 11/12)** — one flip, **2024 COAL_PRB
−10.23 TWh** against a ±8 band. 2023 COAL_PRB comes back INSIDE the band
(model 123.69 → 115.57 TWh, a 8.12 TWh shed against miso-111's 10.79).
C2 PASS; C3a improves (2025 −14.2 % → −13.7 %) and 2023/24 hold; C3b PASS;
C3c unchanged (ledgered tail); C4 PASS; C8 PASS with COAL_PRB carrying
**zero forced rows in both arms**; D-4 passes in both. COAL_BIT untouched
(cv_ratio 0.716/0.631/1.103 vs control 0.719/0.600/1.120, profile_r within
0.002).

### 3.2 Guard readout

| guard | result |
|---|---|
| G1 C7 2023+2024 ≥ 0.5 | **PASS** (0.738 / 0.872, profile_r 0.989 / 0.985) |
| G2 C1 16/16 every year | **FAIL** — 2024 COAL_PRB −10.23 TWh |
| G3 COAL_BIT ≤ 2.0, r within 0.05 | PASS |
| G4 C3a/C3b/C3c no regression | PASS (C3a improved) |
| G5 no new forcing | PASS (zero D-2 rows, D-4 clean) |
| G6 both arms registered + matrix | PASS (this session) |

The 2025 expectation stated before solving held exactly: it improves
(0.314 → 0.393) and stays under 0.5, and the residual belongs to the
overnight price-formation defect (data-blocked miso-78/79), not reopened.
Prediction **P-B was accurate and self-refuting**: it sized the 2024 risk
at ≈ −9 TWh "marginally outside"; the arm landed −10.23.

## 4. Why it fails — the structural test that decides the promotion question

The owner's standing grant (structural integrity may outrank gate
regression) was weighed against a measurement, not a preference. The
committed-band split exists to put the fleet's **within-run night level**
where the meter puts it, so that is the statistic that adjudicates it.
Per-plant, online-hours-only, capacity-weighted over the 26 regulated PRB
plants, model vs the plants' own measured `night_p50`:

| year | MEASURED | model A (control) | model B (split) | cap-wtd abs error A → B |
|---|---|---|---|---|
| 2023 | 0.434 | 0.483 | **0.407** | 0.117 → 0.137 (**16 % worse**) |
| 2024 | 0.434 | 0.437 | **0.374** | 0.107 → 0.107 (flat, sign flipped) |

**The keeper's night LEVEL was already right** — 0.437 against a measured
0.434 in 2024 — and the split arm pushes it *below* the meter. What the
keeper gets wrong is the within-day **variability** (C7's CV), not the
level. Arm B buys the variability by overshooting the backdown: it does
not relocate the fleet onto its measured night level, it drives it under.

The cause is intrinsic to the design, and this is the finding worth
keeping: **the hold-through slice is offer-side only — a price discount
with no floor.** In genuinely cheap hours it backs out along with the
cycling slice, so nothing holds the fleet AT the measured level. That is
why 12.09 TWh (2024) leaves rather than the ~8 the hold share would
predict.

So arm B is not "structurally better with worse gates." It improves one
structural statistic (CV) while degrading another (night level) *and*
volume — the same trade miso-111 was rejected for, in reduced form: a
fleet that decommits energy reality kept burning. Rule 1 forbids promoting
it for the same reason it forbids rejecting a correct mechanism on gates.
**Not promoted.**

## 5. The named successor (miso-113) — a floor, and why it is NOT inert

miso-111 PREREG §8 retired the commitment-bridge form as "provably inert"
because it sized the floor at the measured **LSL** (plant-basis
loading-when-on p5 = 0.182), which sits *below* the per-plant `_mustrun`
bands (0.30–0.52). **That argument does not extend to the night level.**
The measured within-run night level is p50-of-online-night = **0.434
cap-weighted on the plant basis** (0.62 × HSL on miso-111's class basis) —
*above* the mustrun band at most plants, and exactly the level §4 shows
neither arm holds.

The successor is therefore the repo's existing, ISO-proven construction
(CAISO RA must-offer / ERCOT / NYISO gas bridges): a P0-detected
committed-run pattern → `min_gen` floor at a MEASURED fraction, sized at
`night_p50` rather than at LSL, with the committed band above it free to
price. It satisfies rule 17 [R-FLOOR-WINDOW] — driver = regulated
self-commitment (SOM Table 7, 53–56 % of coal starts); window = the
detected committed run; forward story = regenerates from any year's P0
pattern plus the frozen measured level. It is the *floor* half miso-111
dismissed on the wrong statistic, and §4 is the evidence that the floor —
not a second price — is the missing object.

Standing caveats it inherits: C7-2025 will still need the overnight
price-formation lane (model off-peak p10 $29.71 vs actual hub p10 $17.95 —
data-blocked miso-78/79 congestion + sub-hourly RT), which no offer or
floor lever may be stacked on (rule 19).

## 6. Rule duties discharged

- **Rule 15**: both arms registered on the backcast dashboard this session
  (`2026-08-01-miso-112a-control`, `2026-08-01-miso-112b-prb-split`),
  rejection included; top-15 MISO retention honoured (pruned
  `2026-07-26-miso-93-meritguard-a1`, `2026-07-26-miso-94-outage-family`).
- **Rule 26b/c**: `coal_prb_committed_split` carries its OWN matrix row,
  added in the same PR as the field and stamped **R** with this finding.
  The `coal_prb_committed_dispatchable` cell is NOT altered — no new
  evidence changes its R adjudication, and its whole-band form was not
  re-tested.
- **Rule 22**: `--year` strictly {2023, 2024, 2025}; MISO holds no holdout
  marker and none was touched.
- **Rule 21**: no free parameter added — the split consumes one measured
  conduct input formulaically; the arm is not a keeper, so no DOF ledger
  entry is created.
