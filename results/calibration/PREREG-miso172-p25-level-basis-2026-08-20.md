# PREREG miso-172 (arm 2) — the p25 must-run LEVEL is reconstructed on the wrong basis

**Written and committed BEFORE any arm result is read.** Session miso-172,
2026-08-20. Keeper `2026-08-19-miso-170-sitegrain` (bundle `miso170_layup_B2`).

Executes the Ames (1122) successor named in
`FINDING-miso170-congestion-elmp-assessment-2026-08-19.md` §3 and
`RESULT-miso171-d4-attribution-repair-2026-08-20.md` §5(c). **Separately gated
and separately solved from the per-year window arm** (rule 19 `[R-ONE-MECH]` —
the two are different phenomena of the same floor and are never bundled into one
flag or one solve): `PREREG-miso172-mustrun-window-vintage-2026-08-20.md`.

---

## 1. The defect — a dropped basis, proved by the plants where it cannot bite

The frozen deriver measures

```
acf      = net_MW / (nameplate × avail_mult)     # avail_mult is HOURLY
p25_cf   = percentile(acf[online], 25)           # a fraction of AVAILABLE capacity
```

and `campd_bins.thermal_tranche_p25_level` reconstructs the runtime floor LEVEL
as **`p25_cf × nameplate`** — dropping the very `avail_mult` the statistic was
divided by. On a plant carrying a deep availability derate the reconstructed
floor lands **`1 / avail_mult` too high**.

**MISO 1122 Ames**, the chartering case: `p25_cf` 0.674 × 108.7 MW nameplate =
**73.3 MW**, against a measured p25-of-online of **33.0 MW**; and 0.674 × its
implied ~49 MW available base = 33.0 MW **exactly**. The keeper consequently ran
Ames at **+65 / +77 / +93 %** of its own metered energy (586/593/591 GWh model vs
356/336/306 GWh meter), ~90 % floor-forced, near its measured p95 while the real
plant load-follows at half load.

**The census answers the charter's "does it reach other plants" question in both
directions, and it is the diagnostic proof of the mechanism:** measuring the same
percentile of the same online sample **directly in MW** and comparing to the
runtime's reconstruction over all 134 MISO rows —

* **88 of 134 rows agree to within 0.1 %.** Those are exactly the plants with no
  availability derate, where `avail_mult = 1` makes the two bases identical. A
  random discrepancy could not do that.
* **25 of 134 rows are ≥ 1.10×**, all of them derated. Worst: **1402 Little
  Gypsy 2.594×** (137.5 vs 53.0 MW), **1122 Ames 2.220×**, 2070 2.03×,
  **3459 Sabine 1.726×** (494.0 vs 286.2 MW), 55714 1.72×.
* By group: ST_GAS median 1.15× (max 2.59), CC_REGULAR median 1.01× (max 2.03),
  CT_PEAKER median 1.00× (max 1.50). The CC/CT rows are **latent** — MISO's
  keeper runs `cc_mustrun_per_plant=False` — but they are the same defect and
  would fire for any ISO that arms the CC leg.

Of the **7 ST_GAS plants actually floored on the MISO keeper**, four are
over-floored — 1402 (2.594×), 1122 (2.220×), 3459 (1.726×), 3457 (1.249×) — and
three are exact (990 1.002×, 1403 1.000×, 6035 0.988×).

## 2. The mechanism (GATED, default off)

`ScenarioConfig.st_gas_mustrun_p25_measured_level: bool = False`. When armed, the
floor LEVEL becomes the **same percentile of the same online sample, taken
directly in MW** — no reconstruction, so no basis can be dropped.

* **Data:** `data/raw/_processed-legacy/thermal_tranches_p25_level_mw_MISO.csv`,
  written by `scripts/data/derive_thermal_tranche_p25_level_mw.py`, which
  **imports** the frozen deriver's online mask (`_ONLINE_FRAC` = 5 % of
  *available*), parasitic-factor net, derate source, fleet nameplate/primary-group
  attribution and pooled window — same statistic, same sample, MW instead of a CF.
* **Rule 14 `[R-ACCURATE]`** is the governing rule: prefer the measured quantity
  over an estimate of it. It is also why the instrument is a **LEVEL repair and
  never an exclusion** — Ames's floor is right in kind (a real municipal
  self-commitment), wrong in LEVEL. Fix the measurement, never delete the plant.
* **Rule 23 `[R-FROZEN-DERIVE]`:** frozen deriver untouched (zero bytes), pooled
  artifact not regenerated, additive side artifact on the **same pooled window**
  — so the ONLY thing a consumer sees change is the basis. Trigger is a measured
  level/meter mismatch, never a residual.
* **Rule 21 `[R-DOF]`: ZERO new free parameters.** `n_scalars` 0.
* **Rule 19:** the level SOURCE is replaced. Membership, window, mechanism id
  (`MECH_ST_GAS_MUSTRUN_PER_PLANT`) and the cheapest-first
  `pmax × availability` clip are untouched; no second floor is stacked.
* **Rule 13:** a pooled multi-year percentile of measured operation — the same
  admissible family as `p25_cf` itself, with the identical forward story (it
  re-derives from each new CAMPD vintage). Registered backcast-only alongside
  `st_gas_mustrun_p25_level`.
* Vintage stays **pooled** here on purpose: bundling the per-year window into
  this arm would make the two effects unattributable (rule 19).

## 3. Pre-registered gates

Control `miso172_control` (shared with arm 1) = same-recipe `replay_keeper` at
this HEAD, both new flags OFF. Arm `miso172_p25mw` = the control `--set
st_gas_mustrun_p25_measured_level=true`. `--year 2023 2024 2025`, sequential in
ONE invocation.

| gate | pass condition |
|---|---|
| **K-0** control inertness | shared with arm 1: every scored sidecar, every year, `max\|diff\| = 0.0` vs the committed keeper. Verified BEFORE any arm output is read. |
| **L-1** level exactness | in the arm, every live plant's floor level equals its measured MW row (within the `pmax × availability` clip), and no live plant is still floored at `p25_cf × nameplate`. Unit grain, from the arm's own `floors/<year>_P1.npz`. |
| **L-2** liveness | the mechanism's D-2 forced energy lands inside the §4 bands in all three years, with 1122/3459/1402/3457 down and 990/1403/6035 unmoved (±5 %). |
| **L-3** Ames dispatch | 1122's modelled annual energy moves **toward** its meter in all three years, and overshoots it in none. Control: +65/+77/+93 %. |
| **K-3** conduct failures | ZERO NEW D-4 conduct failures and zero new off-window binding. (A LOWER floor cannot create one; this gate is the falsifier.) |
| **K-5** no gated flip | zero record-grain PASS→FAIL flips over the full scorer output. A flip is reported and blocks promotion on this arm alone; the structure-vs-gates question goes to the owner. |
| **K-6** ST_GAS shape | D-1 `profile_r ≥ 0.80`, `cv_ratio ≥ 0.5` all three years, `profile_r` no more than 0.05 below the control. |

**Declared in advance, so it cannot be spun either way:** this arm removes
~20 % of the mechanism's forced energy, which (a) may take ST_GAS's C8 forced
share **under** the 30 % cap in 2023–24, and (b) pushes the ST_GAS class
**further below** its actual energy and frees ~1.5–1.9 TWh/yr to cheaper units,
which can make **C3a-2025 worse**. Under rule 1 `[R-STRUCT]` neither outcome
decides the arm: a correct basis stays in if the fit worsens, and a C8 pass
bought here is a *consequence*, not the objective. Both are reported at full
magnitude whichever way they land.

## 4. L-2 bands, computed from committed artifacts BEFORE the solve

Same instrument as arm 1's K-2 (`predicted = control × est_arm / est_pool`), band
**± 50 %** on the change. Because a lower floor also lets economic dispatch clear
it more often, these predictions are **upper bounds** on the surviving forced
energy — a larger reduction than predicted is expected-direction, not a miss.
Mechanism totals (`st_gas_mustrun_per_plant` forced TWh):

| year | control | predicted | Δ | band on Δ |
|---|---|---|---|---|
| 2023 | 7.2596 | **5.7714** | −1.488 | [−2.232, −0.744] |
| 2024 | 7.3357 | **5.8545** | −1.481 | [−2.222, −0.741] |
| 2025 | 9.3428 | **7.4317** | −1.911 | [−2.867, −0.956] |

Per plant (2023 / 2024 / 2025, TWh, control → predicted):

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| 3459 Sabine | 2.3277 → **1.4559** | 2.1371 → **1.3275** | 2.9533 → **1.7189** |
| 1122 Ames | 0.5457 → **0.2458** | 0.5758 → **0.2594** | 0.5329 → **0.2401** |
| 1402 Little Gypsy | 0.3529 → **0.1360** | 0.4618 → **0.1781** | 0.4819 → **0.1858** |
| 3457 Lewis Creek | 0.4948 → **0.3960** | 0.3551 → **0.2842** | 0.4388 → **0.3512** |
| 990 / 1403 / 6035 | unmoved (±5 %) | unmoved | unmoved |

## 5. Governance

Rule 22 fail-closed: MISO holds neither `complete` nor `final`, spend freeze
ACTIVE, **2023–2025 only**. Rule 28: base row + a cell line in every ISO shard in
the same PR; only MISO's shard is stamped with a verdict (rule 25). Rule 15: the
arm is registered on the dashboard in this session whatever the outcome.
