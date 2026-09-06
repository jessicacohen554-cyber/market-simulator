# FINDING miso-224 — THE BODY IS A FUEL-CONVENTION OBJECT. Pricing MISO gas at marginal commodity moves the 2023 body **−$4.11** (G-1 PASS) and is **KILLED as a standalone arm** on G-3 / G-4: the EIA-923 average print was compensating for missing coal self-commitment and for the seam import ladder (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. **No promotion is proposed.** The screen bundle `miso224_spotgas_S` (2023
only) is NOT registered and is **DELETED before this PR merges** (rule 29 clause 2 and (c),
owner ruling R-AV): every number cited here is in this document or in a committed JSON
record. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; one LP (2023); 2024/2025 never spent.

Records: `PRECOMMIT-miso224-gas-marginal-commodity-2026-09-06.md` (+ Addendum A, both pushed
before the solve at `19949ba5` / `0a68c67c`); instruments
`scripts/probes/_miso224_{floor_anatomy,marginal_frequency,offer_decomposition,static_remerit}_phase0.py`
→ `_miso224_*.json`; blind scorer `_miso224_screen_gates.py` → `_miso224_screen_gates.json`;
arm-side re-reads `_miso224_arm_floor_anatomy_2023.json`,
`_miso224_arm_offer_decomposition_2023.json`. Mechanism: `miso_gas_marginal_commodity_pricing`
(`ScenarioConfig`, default off; `data.fuel.basis.miso.apply_miso_gas_marginal_commodity`);
matrix row `gas_marginal_commodity_pricing`, MISO cell **`O`**.

---

## 0. Verdict in one paragraph

The charter offered two successor objects. **(A) is refused on the bound**: the real MISO
energy price (MEC) went negative in 1 / 7 / 0 hours a year, so the negative-price mechanism
cannot reach a +$6–13 body error; what the real market did in 1,765 / 2,959 / 681 hours was
clear at **$10–20**, below every thermal SRMC the model carries. **(B), aimed by marginal
frequency, is not a multiplier object**: the `econ` bands hold the margin 75–78 % of body
hours, but the multiplier layer of the marginal offer is only $0.1–1.1 of a $3–6 wedge; the
**fuel-convention layer — the EIA-923 *average* delivered print against the *traded* Chicago
hub — is 74 / 74 / 101 % of it.** The arm re-prices every MISO gas unit at its zone's measured
daily hub (the same convention the forecast path already uses) and was screened on 2023, the
footprint year. **It does what its arithmetic says on price — body −$4.11, inside the
pre-registered [−10.08, −3.36]** — and it **dies on the dispatch gates**: coal moves 0.27× the
static prediction in the cheap hours against a 0.30× line, and two C1 cells flip (CC_REGULAR
−4.2 → **+12.6 TWh**, COAL_PRB −1.6 → **−11.9 TWh**). Pre-registered reading 2 applies: the
average-cost print was **compensating** (rule 14) for coal self-commitment in mid-price hours
and for a seam ladder that lets imports out of merit as the model's price falls. Against
interest, C3a-2023 moves +7.15 % → ≈ −5.7 % and stays inside ±10 %; the cancellation that
makes it pass is reduced, not removed.

## 1. THE GATE TABLE, exactly as the blind scorer printed it

| gate | scorer | measured | reading |
|---|---|---|---|
| **S-1** single delta | FAIL | `arm_field_differs = False` because the field is **absent** from the keeper's older config (listed under `fields_absent_from_keeper` with 8 other post-keeper fields); `other_diffs = []`, `year_scoped_diffs = []` | **SCORER ARTIFACT — substantive condition MET** (§2) |
| **S-2** liveness | **PASS** | mechanism line in the SOLVE log, winter-shape line absent; 1,448 gas rows exactly at the daily hubs (Midwest = Chicago, South = Henry Hub) | clean |
| **G-1** body direction & magnitude | **PASS** | Indiana body 33.34 → 29.23, **Δ = −4.11**, band [−10.08, −3.36]; LW body −3.90; tail −6.83; annual LW −4.16 | 61 % of the static −6.72 |
| **G-3** dispatch response | **FAIL** | real sub-$20 hours (n = 1,230): coal **−799 MW** (needed ≤ −876 = 0.30 × −2,919), gas **+2,716 MW** (needed ≥ +897) | **KILL on the coal leg, 0.27× vs 0.30×**; gas leg clears 3× |
| **G-4** no C1 flip | **FAIL** | flips: **CC_REGULAR**, **COAL_PRB**; inconclusive: none; C2 unscored ex ante | **KILL — the pre-registered likeliest kill** |

**ARM KILLED ON G-3 AND G-4.** S-1 does not contribute to the verdict.

## 2. THE NON-KILL, disclosed rather than scored away

S-1's first clause asks whether the arm field *differs* from the keeper's value. The keeper's
`run_config.json` predates the field, so the scorer filed it under "absent from keeper" and
`arm_field_differs` could never be true. Its second clause — nothing else differs over the
non-year-scoped fields — is **met exactly** (`other_diffs = []`), and this time even the
year-scoped set is empty (`replay_keeper` re-stamps the 2023 config identically). I did not
edit the scorer after seeing this (miso-223 §2 discipline). A successor scopes S-1 as "the
arm field is `True` in the arm and absent-or-`False` in the keeper".

## 3. WHAT THE SCREEN MEASURED

### 3.1 Price — the mechanism does what its arithmetic says

Load-weighted system price, 2023, keeper → arm: mean **34.64 → 30.48**; min 20.55 → 17.12;
p10 27.87 → 23.77; p50 33.98 → 30.58; p90 41.17 → 36.86; p99 49.80 → 41.63; hours < $20
**0 → 68** (actual MEC < $20: 1,765). Against the MEC by MEC decile (LW model − MEC):

| MEC decile | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | annual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| keeper | +12.9 | +11.0 | +10.4 | +9.9 | +9.5 | +8.9 | +8.0 | +6.4 | +3.7 | −27.7 | **+5.31** |
| arm | +8.7 | +6.9 | +6.1 | +5.8 | +5.7 | +5.1 | +4.1 | +2.4 | −0.7 | −32.5 | **+1.15** |

The gradient survives at ~two-thirds its size in the cheap deciles. The arm's own marginal
offer, decomposed the same way as phase 0 (`_miso224_arm_offer_decomposition_2023.json`):
body gap 2.26 = markup 0.93 + **fuel convention 0.13** + residual 1.18 — the identity the arm
asserts holds (the layer was 4.68). What remains in the cheap deciles is RESIDUAL: d1 8.28 =
markup 0.34 + fuel −0.32 + **residual 8.23** — the model's marginal unit, at spot fuel, is still
$5–8 dearer than what set the real price, and §3.2 says why.

### 3.2 Dispatch — where the gas came from

Annual class energy, 2023 (TWh, sidecar): gas **+25.1** (CC_REGULAR +16.8, CC_CHP +4.5,
CT_PEAKER +3.1, ST_CHP +0.9, ST_GAS −0.2); **imports −11.85** (45.75 → 33.90; EIA-930 net
import 37.9); **coal −13.3** (PRB −10.3, BIT −2.5, lignite −0.5); wind/solar/nuclear/hydro
unchanged. C1 by delta transfer against the committed `classFull` actuals (band 8.0 TWh):

| class | actual | keeper (err) | arm (err, share pp) | |
|---|---:|---:|---:|---|
| CC_REGULAR | 141.82 | 137.65 (−4.17) | 154.41 (**+12.60**, +2.39) | **FLIP** |
| COAL_PRB | 121.67 | 120.11 (−1.56) | 109.79 (**−11.88**, −1.68) | **FLIP** |
| COAL_BIT | 57.07 | 54.15 (−2.92) | 51.65 (−5.42) | pass |
| CT_PEAKER | 17.04 | 9.05 (**−7.99**, the miso-220 fragile edge) | 12.16 (−4.88) | pass, **toward** |
| CC_CHP | 21.31 | 19.63 (−1.68) | 24.09 (+2.78) | pass, crosses |
| ST_CHP | 5.20 | 2.53 (−2.67) | 3.47 (−1.73) | pass, toward |
| ST_GAS | 13.94 | 14.48 (+0.54) | 14.31 (+0.37) | pass, toward |
| COAL_LIGNITE | 7.05 | 6.38 (−0.67) | 5.92 (−1.13) | pass |

In the real sub-$20 hours (n = 1,781 on the 8-hub set; means, GW): keeper coal 17.73 / gas
18.36 / imports 3.23 against EIA-930 14.49 / 21.33 / 4.89; **arm coal 16.96 / gas 21.08 /
imports 1.45**. The arm's gas lands ON the measurement; coal keeps +2.5 GW of its excess (the
commitment floors hold it there — reading 1 for the cheap hours); imports fall to a third of
the measurement.

## 4. THE FINDING — two compensated mechanisms, named by the pre-registration

Reading 2 of PRECOMMIT §5 was written before the solve for exactly this outcome:

1. **Coal self-commitment.** Real PRB coal ran 121.7 TWh in 2023 through the spring and
   autumn hours in which Chicago gas traded at $2.0–2.4 and a CC's SRMC sat below a PRB
   unit's incremental cost. The model's coal econ tranches offer at delivered cost × a 10.5–13
   heat rate, so once gas is at the hub they are undercut in the MID-price hours and coal loses
   13 TWh — not in the cheap hours, where the per-plant floors (`coal_mustrun_per_plant`,
   `coal_warm_committed`, the take-or-pay committed band) hold it. Real MISO coal is
   self-scheduled: the IMM's standing finding is that a large share of coal capacity commits
   itself and runs through hours priced below its offer. The dear average-cost gas was doing
   that job by PRICE. Rule 14 `[R-ACCURATE]`: keep the accurate input, fix this root cause — a
   coal self-commitment floor needs a window, a driver and a forward story (rule 17), measured
   from CAMPD conduct (hours online at LMP below the unit's own delivered incremental cost)
   the way miso-111 / miso-152 measured PRB conduct.
2. **The seam import ladder.** Imports are priced at measured MISO-DA-hub quantiles by flow
   duration (`miso_seam_measured_ladder`). When the model's own price falls, those bands go
   out of merit and imports contract — the arm cut them 11.85 TWh, and in the cheap hours to
   1.45 GW against a measured 4.89. The real market imported MOST when it was cheapest (SPP wind,
   PJM off-peak). This is queue item 2 (the D-2 5(i) seam object), whose admissibility ruling is
   outstanding; the screen gives it a magnitude.

Neither is a residual argument. Both are dispatch identities the arm exposed by removing the
input that hid them, which is what rule 14's "the estimate was silently compensating" clause
describes.

## 5. WHAT THIS DOES NOT LICENSE, and the cell

- **No keeper, no full span, no registration.** The arm is dead as a standalone arm on the
  screen's own pre-registered gates. Rule 29: the remaining years are never spent.
- **The convention question stays in owner court** (miso-212 §8). This screen is the
  evidence for it, stated plainly: gas at marginal commodity moves the body the predicted way,
  keeps C3a-2023 inside its band, and exposes two structural gaps the current keeper hides.
- **Matrix cell `O`, not `R`.** The mechanism did what it claimed on price (G-1), is a real
  market convention, and has an exact forward analogue. It MUST NOT be re-run alone; a JOINT
  screen with a coal self-commitment floor and/or a seam repair is new evidence.
- **Reported against interest.** The tail moved −$6.83 (the gas stack shifts in every hour),
  so the top-decile deficit the reserve/ORDC family owns (miso-219/221/222) is larger under the
  arm, and C3a-2025 — where the tail deficit is −$44 — would not survive a uniform version of
  this move without its own mechanism.

## 6. GOVERNANCE — what happened, in the order it happened

- **First launch killed with no LP solved** (PRECOMMIT Addendum A): the calibration chain
  `run_calibration.py::run_year` bypasses the resolver hook; the winter-shape line was in the
  log and the mechanism line was not. Hook mirrored there, the zonal applier made to honour
  hub-priced rows, and S-2 made to read the SOLVE log — all before any result existed.
- **Second launch OOM-killed** at anon-RSS 13.95 GB in the 13 GB cgroup: the swapfile created
  at session start had gone inactive (`/proc/swaps` empty, file intact). Re-`swapon`, checked
  from a separate call, then the miso-169 §3 recipe held: exit 0, 2.8 MB of swap touched.
- **No control solve.** G-DRIFT `b3fb0edc..HEAD`: six files, 448 insertions, 0 deletions,
  ALL INERT (a default-off NYISO field that hard-errors elsewhere, one forecast-only import,
  session tooling). Form 4: the committed keeper is the control.
- Rule 27: `scenarios.py`, `run_calibration.py`, `basis/miso.py`, `test_fuel.py`, the matrix
  files and this lane's docs were edited locally and pushed as on-disk bytes; every ≥300-line
  blob was verified equal on the remote after each push.
- Rule 28: row + six cell lines minted with the field; MISO cell stamped in this session.
- DOF ledger unchanged at 41/2: zero fitted scalars minted.
