# PRECOMMIT — pjm-174: PJM's seam ladder is anchored on its OWN hub; re-anchor it on the neighbour, hourly

**Session** pjm-174 · **ISO** PJM · **Date** 2026-09-08
**Keeper** `2026-08-15-pjm-162-inputclock` (bundle `pjm_debugb_inputclock_A`) — **unchanged by this card.**
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).
**COMMITTED BEFORE ANY SOLVE.** Every gate, bar and numeric prediction below is fixed here and is
not rewritten after a number is on the table (rule 29 `[R-SCREEN]` (c)).

---

## 1. WHAT PHASE 0 FOUND — and how it departs from the charter

The pjm-174 charter asked whether `PJM_SEAM_LADDER_BY_YEAR`'s **deep-duration export bands are
mis-derived** — whether they "clear ~10 TWh short". **They are not, and the hypothesis is
REFUTED.** But the same object carries a *different* construction defect, which phase 0 sizes, and
that is what this card screens.

All of §1–§2 is ZERO-LP, computed from committed artifacts (the pjm-169 touchpoint bundle
`pjm169_tp2022_2021_f2arm`, the keeper bundle `pjm_debugb_inputclock_A`, the PJM tie-line meter and
the measured DA series).

### 1a. The miss decomposes, and the ladder's band prices are not in it

Net export, export-positive TWh, against the PJM settlement-grade tie-line meter — which **is** the
scored actual (31.775 TWh in 2022, i.e. the "31.69" the pjm-173 finding cites; the EIA-930/tie-line
boundary question is therefore CLOSED at the total, not open):

| term | 2022 | 2021 |
|---|---|---|
| measured (tie-line meter) | **31.777** | **37.816** |
| ladder on its OWN basis (measured DA) → **construction gap** | 31.732 (**−0.046**) | 37.805 (**−0.011**) |
| ladder on the MODEL's price → **+ price-shape transmission** | 25.996 (**−5.735**) | 25.106 (**−12.699**) |
| per-border deliverability envelope | 25.541 (−0.456) | 24.039 (−1.067) |
| the LP's realised result | 21.650 | 23.434 |
| **TOTAL MISS** | **−10.127** | **−14.382** |

**The construction gap is 0.5 % / 0.1 % of the miss.** Per-seam the incumbent ladder reproduces its
own source at duration RMSE 42–274 MW, inside the derivation's own claimed 40–280 MW band, and
per-seam volume within 0.053 TWh. The band prices are RIGHT.

The closing proof: quantile-map the model's price onto the measured DA marginal distribution,
**keeping the model's own hourly ranking**, and feed the UNCHANGED committed ladder — it returns
**31.732 TWh (2022) and 37.805 (2021)**, i.e. the measured volume exactly. Correcting the price
duration curve alone recovers everything the ladder can recover.

### 1b. The defect that IS there: the anchoring

`PJM_SEAM_LADDER_BY_YEAR` is a **fixed annual PRICE ladder anchored on PJM's own DA hub** — a Q-Q
coupling to the *measured* price duration curve, which the LP then clears against the *model's*
price duration curve. It is therefore only as good as the model's reproduction of that curve, and
PJM's is compressed (the pjm-171 flat stack). The transmission term decomposes monotonically by
measured-DA decile — 2022, model-minus-measured price and the export it costs:

| decile | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Δprice $/MWh | +11.98 | +9.34 | +8.46 | +7.19 | +5.59 | +2.60 | −0.94 | −5.65 | −14.44 | −48.48 |
| Δexport TWh | −3.308 | −2.130 | −1.737 | −1.031 | −0.990 | −0.090 | +0.266 | +0.572 | +0.853 | +1.860 |

This is exactly the defect `seam_neighbour_anchored_ladder` / `seam_neighbour_hourly_ladder`
already name in the matrix (minted miso-225 / miso-231): *"a FIXED price ladder is cleared by the LP
against its OWN internal price, so re-anchoring moves where the bands sit and not WHEN they clear."*
**PJM's cells for both are `U`** and the rows' own notes name `PJM_SEAM_LADDER_BY_YEAR` as carrying
the same defect. No verdict is transferred (rule 25 `[R-ISO-SCOPE]`): every parameter below is
derived from PJM's own market data.

### 1c. The envelope is NOT the constraint

Sum of the per-border export ceilings is **89.9 TWh** against a 31.8 TWh measured flow; the ladder
wants more than the summed cap in 0.7 % of hours and clipping costs 0.051 TWh. Applied per border it
costs −0.456 TWh (2022) / −1.067 (2021). Reported so it is not re-opened.

---

## 2. THE ARM — `pjm_seam_neighbour_hourly_ladder`

Band `k`'s offer becomes hourly, `pi_k(t) = neighbour(t) + delta_k`, so it clears on the seam
**SPREAD** rather than on PJM's absolute price level. A **SUB-GATE** of
`pjm_seam_measured_ladder`, refused at the point of use without it, DISPLACING the parent's scalar
band price on the seams it covers and DEGRADING to that parent everywhere else (rule 19
`[R-ONE-MECH]`: alternatives never stacked, and never a degrade to an unpriced seam).

**Zero fitted parameters** (rules 21/24). The offsets are the IDENTICAL Q-Q duration coupling —
same midpoint-depth grid on the same `SEAM_FLOW_TRANCHES`, same measured tie-line flows, same
same-seam no-wash reconciliation — read off the spread instead of PJM's own DA. The single degree
of freedom is *which measured series the coupling reads*, the same one the MISO neighbour
derivations exercise. Derived by `scripts/data/derive_pjm_seam_ladders.py --neighbour-hourly`
(rule 23 `[R-FROZEN-DERIVE]`: re-derives only when its source data updates).

**The anchor is named on TOPOLOGY, before any ladder was derived** (rule 14 `[R-ACCURATE]`
misalignment clause, the miso-233 `SPP_ANCHOR_HUB` pattern), never by which scores better:

* **MISO** → equal-weight mean of MISO's three **PJM-facing** zonal hubs (MISO-Illinois /
  MISO-Indiana / MISO-East). The exact **mirror** of MISO's own construction for this same physical
  seam, where `PJM_WEST` is the equal-weight mean of the three MISO-facing PJM gen hubs. PJM's MISO
  ties land on ComEd (Illinois), AEP-Ohio (Indiana), ATSI (Michigan/East) — `_PJM_TIE_ZONE`.
* **NYISO** → NYISO's reference DA, the only measured NYISO series held under `data/raw`.
* **Carolinas / TVA / LGEE** → no row, ever: SERC publishes no hub or nodal price, the same data
  boundary the MISO derivation states for SOCO/TVA.

The MISO **system** hub is reported by the derive as a sensitivity and **selects nothing** (2022
corr +0.270, 2023 +0.323, against the topology anchor's +0.306 / +0.425).

**Coverage — a row exists iff the solve can arm it.** MISO is absent in 2019/2021 (no series) and
2022 (ONE contiguous **525 h** outage in the zonal DA, far past the repo-standard `limit=3`
interpolation): full coverage or nothing, because `_inject_seam_ladder` applies one ladder per
seam-year.

### 2a. READOUT A — measured record, scored on measured flow (hourly corr, incumbent → arm)

| seam | 2019 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **NYISO** | −0.387 → **+0.568** | −0.231 → **+0.620** | +0.235 → **+0.723** | +0.071 → **+0.553** | +0.201 → **+0.544** | +0.001 → **+0.514** |
| **MISO** | — | — | — | +0.419 → +0.425 | +0.487 → **+0.393** | +0.316 → +0.391 |

A **sign flip** on the NYISO seam in three of six years; volume preserved within 0.02 TWh in every
seam-year. **REPORTED AGAINST THE ARM:** the MISO leg is roughly neutral and is **WORSE in 2024**
(−0.093). The repair is the NYISO leg and this card claims no more.

---

## 3. SCREEN YEAR — **2025**, fixed on MEASURED FOOTPRINT before any solve

Rule 29 `[R-SCREEN]` step 1: the screen year is the year the mechanism's **own measured footprint is
largest**, never the year with the biggest residual.

| year | tier | hours changed | mean \|ΔMW\| | corr gain NYISO | corr gain MISO |
|---|---|---|---|---|---|
| 2022 | validation | 95.3 % | 1,855 | +0.488 | +0.015 |
| 2023 | TRAIN | 95.0 % | 1,877 | +0.482 | +0.007 |
| 2024 | TRAIN | 93.2 % | 1,659 | +0.343 | −0.093 |
| **2025** | **TRAIN** | **96.3 %** | **1,907** | **+0.513** | **+0.075** |

**2025 wins on every measure**, and it is a **training year** — so this screen spends **no holdout
authorization at all** (`--holdout-authorized` is not passed and no out-of-training year is solved,
scored or registered). This DEPARTS from the charter's named 2022 and the departure is stated here:
the footprint ranking is a property of *this* mechanism, which is not the one the charter posited,
and the permitted year with the largest footprint is 2025. 2025 additionally makes every gate below
purely **protective** — C1/C3a/C3b PASS there on the keeper — so rule 29's "never gated on the
target residual" holds trivially.

---

## 4. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — and why a CONTROL SOLVE IS SPENT

`f36cee6e` (the pjm-169 control's `git_sha`) no longer exists after the squash-merge; per the
charter the audit runs from the pjm-173 anchor **`22eda76a` → HEAD `cbf9be9f`**: 11 files on the
solve path, +802/−8.

INERT: `model/interchange/spec.py` (cent-level re-derivations of **MISO's** ladder only —
`PJM_SEAM_LADDER_BY_YEAR` untouched); `constants.py` (SPP gas-bridge constants); `fleet/floors.py`
(gated on `netload_drag_layup_window_mask`, default False, absent from PJM's recipe);
`runner.py` (capacity-market clearing / `curve_reserve_position` — a forecast path a
`mode="backcast"` run never enters); the CAISO WECC intertie parquet.

**LIVE:** `data/fuel/plant_prices.py` + `f923_gas_price_plausibility_screen`, **default `True`** and
reachable on PJM's own gates (the control's `run_config.json` carries `mode = backcast` **and**
`gas_plant_monthly_fuel_pricing = True`), so it resolves ON at HEAD and was behaviourally OFF when
the pjm-169 control was solved. A second candidate (`EGRID_CT_HR_PHYSICAL_FLOOR`, `fleet/eia860.py`)
is not adjudicated because it cannot change the decision.

**⇒ G-CTRL form 4 is VOID for this session.** The committed pjm-169 bundle is NOT the control. This
screen spends a **same-HEAD control solve** (G-CTRL form 1), so the only difference between the two
bundles is this card's single declared delta and the drift is neutralised by construction.

---

## 5. THE A/B

Single declared delta on the keeper's own frozen recipe, both legs at HEAD `cbf9be9f`:

```
python scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A \
  --years 2025 --out-dir results/calibration/pjm174_ctl_2025 --note "pjm-174 control"
python scripts/replay_keeper.py results/calibration/pjm_debugb_inputclock_A \
  --years 2025 --out-dir results/calibration/pjm174_arm_2025 \
  --set pjm_seam_neighbour_hourly_ladder=true --note "pjm-174 arm"
```

Sequential, one year per process (rule 12 `[R-PARALLEL]`; a single PJM plant-level 8760 LP peaks
~13.9 GiB against the 13.34 GiB cgroup cap and is cleared by the pjm-169 swapfile recipe — two
concurrent PJM years would OOM). Bundles are **gitignored** (`results/calibration/pjm174_*/`), never
registered (rule 29 (c)), and **never deleted before the owner rules on promotion** (rule 31
`[R-RETAIN]`).

---

## 6. THE PRE-REGISTERED GATES — STOP-only; they may kill the arm, never promote it

**S1 — IDENTITY.** On the covered seams the applied cost is exactly `anchor(t) + offset_k`; on every
uncovered seam it is exactly the parent's scalar band price.
**BAR: `max|mc − law| = 0` exactly**, on all 32 covered rows (MISO 16 + NYISO 16) and all 48
uncovered rows. *Instrument: the committed unit tests in
`tests/iso/pjm/test_pjm_seam_neighbour_hourly_ladder.py`.*

**S2 — BYTE-IDENTICAL OFF.** The arm's off posture, every non-PJM ISO and every forecast year are
bit-identical to the parent ladder. **BAR: exact equality**, asserted by the committed tests; the
control leg of §5 is the off posture at the same HEAD.

**S3 — FOOTPRINT CONFINED.** Only the covered-seam band rows move. **BAR: exactly 32 `mc` rows
differ between arm and control; ZERO non-seam rows differ; the 48 SERC seam rows are unchanged.**

**S4 — THE DISPATCH RESPONSE MATCHES ITS OWN ARITHMETIC.** The pre-solve band-clearing prediction on
the KEEPER's committed 2025 price, computed and fixed **here, before the solve**:

| | incumbent | arm | Δ |
|---|---|---|---|
| MISO seam | 22.545 | 25.159 | **+2.613** |
| NYISO seam | 21.280 | 22.258 | **+0.977** |
| **band-clearing net export** | **28.531** | **32.122** | **+3.591 TWh** |

The band arithmetic over-states the keeper's own LP export (28.531 against the LP's 23.233 TWh, the
same ≈5 TWh application residual §1a records for 2022), so **S4 is a DIRECTION + ORDER-OF-MAGNITUDE
bar on the LP, not a point value**:
**BAR: the LP's net export must RISE, and the rise must lie in [+1.0, +7.0] TWh.** A wrong sign, no
movement, or a magnitude outside that interval means the mechanism is not doing what its own
arithmetic says, and **the arm is dead**.

**S5 — COLLATERAL (protective).** No load-bearing criterion (C1 `fuelmix`, C2 `sysvol`,
C3a `price_mean`, C3b `price_shape`) may flip **PASS → FAIL** in 2025 against the control.
**BAR: zero flips.** 2025 is a CALIBRATED keeper year; a flip kills the arm outright.

**KILL RULE.** Any of S1/S3/S4/S5 failing kills the arm; nothing is promoted, the remaining years
are never spent, and the FINDING reports the failure as the session's result.

**REPORTED, GATING NOTHING (rules 1 `[R-STRUCT]` / 29).** C1, C3a, C3b and the interchange row are
reported at full magnitude on both legs. They are **not** gates in either direction: an arm killed
on structure is not revived by a target improving, and an arm that clears S1–S5 is not promoted by
one either — promotion is the owner's decision on the full span.

---

## 7. WHAT THIS CARD DOES NOT CLAIM

* It does not repair the **price duration curve**. §1a shows that channel is worth the whole
  −5.735 / −12.699 TWh and this arm addresses only part of it; `diurnal_price_amplitude` stays `G`
  (owner-closed frontier) and is not re-opened.
* It does not close the **≈4 TWh LP application residual** between the band-clearing arithmetic and
  the solved flow (2022 −3.890 after the envelope; 2025 −5.298 on the keeper). Characterised, not
  attributed — a successor's object.
* The **MISO leg is not claimed as a repair** (neutral, and worse in 2024). The NYISO leg is.
* No ISO's verdict is transferred (rule 25) and PJM's keeper, headline and marker are untouched.
