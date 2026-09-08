# FINDING — pjm-174: the seam ladder's band PRICES are right; its ANCHORING is the defect

**Session** pjm-174 · **ISO** PJM · **Date** 2026-09-08
**Card** `docs/handoffs/PRECOMMIT-pjm174-seam-neighbour-hourly-ladder-2026-09-08.md`, committed
`f2a834de` **BEFORE any solve** and not rewritten.
**Keeper** `2026-08-15-pjm-162-inputclock` — **unchanged.** Nothing promoted, nothing registered.
**PJM headline determination** — **CALIBRATED**, untouched (rule 30(c)).
**Holdout spend: NONE.** The screen year is 2025, a TRAINING year; `--holdout-authorized` was never
passed, and no out-of-training year was solved, scored or registered.

---

## 0. RESULT IN ONE PARAGRAPH

The charter's hypothesis — that `PJM_SEAM_LADDER_BY_YEAR`'s **deep-duration export bands are
mis-derived and clear ~10 TWh short** — is **REFUTED, at zero LP.** The incumbent ladder reproduces
its own basis to **−0.046 TWh (2022)** and **−0.011 TWh (2021)** against total interchange misses of
−10.127 and −14.382 TWh, at per-seam duration RMSE 42–274 MW — inside the derivation's own claimed
40–280 MW band. **The band prices are right.** What is wrong is the **ANCHORING**: the ladder is a
fixed annual PRICE ladder anchored on PJM's own hub — a Q-Q coupling to the *measured* price
duration curve that the LP then clears against the *model's* — so fed the model's own price it loses
**−5.735 TWh (2022)** and **−12.699 TWh (2021)** of net export, **57 % and 88 %** of each year's
miss. Quantile-mapping the model's price onto the measured DA marginal distribution, hourly ranking
untouched, and feeding the **unchanged** committed ladder returns the measured volume **exactly** —
the proof that the band prices are not in it. That is precisely the defect the matrix rows
`seam_neighbour_anchored_ladder` / `seam_neighbour_hourly_ladder` already name, and **PJM's cells
were `U`** — open, never tested. This session built PJM's own form of the repair
(`pjm_seam_neighbour_hourly_ladder`: default off, zero fitted parameters, anchors named on topology
before deriving) and screened it on 2025.

---

## 1. THE DECOMPOSITION — where the interchange miss actually lives

Net export, export-positive TWh, against the PJM settlement-grade tie-line meter. **That meter IS
the scored actual** (31.775 TWh in 2022 — the "31.69" pjm-173 cites), so the EIA-930-vs-tie-line
boundary question raised in the charter is **CLOSED at the total**, not open.

| term | 2022 | 2021 |
|---|---|---|
| measured (tie-line meter) | **31.777** | **37.816** |
| ladder on its OWN basis (measured DA) → **construction gap** | 31.732 (**−0.046**) | 37.805 (**−0.011**) |
| ladder on the MODEL's price → **+ price-shape transmission** | 25.996 (**−5.735**) | 25.106 (**−12.699**) |
| + per-border deliverability envelope | 25.541 (−0.456) | 24.039 (−1.067) |
| the LP's realised result | 21.650 | 23.434 |
| **TOTAL MISS** | **−10.127** | **−14.382** |

**Construction gap: 0.5 % / 0.1 % of the miss.** Per-seam, the incumbent ladder reproduces its
source at duration RMSE 42 / 60 / 87 / 142 / 274 MW (LGEE / TVA / Carolinas / NYISO / MISO) and
per-seam volume within 0.053 TWh.

**The closing proof.** Quantile-map the model's price onto the measured DA marginal distribution,
preserving the model's own hour ranking, and feed the UNCHANGED committed ladder:

| | 2022 | 2021 |
|---|---|---|
| ladder @ model price, as solved | 25.996 | 25.106 |
| ladder @ model price, **duration curve corrected** | **31.732** | **37.805** |
| measured | 31.777 | 37.816 |

Correcting the price duration curve alone recovers everything the ladder can recover. Rank
correlation between the model's price and measured DA is already 0.892 / 0.915 — the *ranking* is
close; it is the *marginal distribution* that is wrong.

### 1a. The transmission term is monotone in the price error

2022, model-minus-measured price by measured-DA decile, and the export it costs:

| decile | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Δprice $/MWh | +11.98 | +9.34 | +8.46 | +7.19 | +5.59 | +2.60 | −0.94 | −5.65 | −14.44 | −48.48 |
| Δexport TWh | −3.308 | −2.130 | −1.737 | −1.031 | −0.990 | −0.090 | +0.266 | +0.572 | +0.853 | +1.860 |

2021 is the same shape and stronger: the model's price is too HIGH in every decile 1–8, and deciles
1–3 alone cost −9.1 TWh. This is the pjm-171 flat stack, transmitted into a volume error by a
mechanism that couples flow to price level.

### 1b. The envelope is NOT the constraint

Summed per-border export ceilings are **89.9 TWh** against a 31.8 TWh measured flow; the ladder wants
more than the summed cap in 0.7 % of hours and clipping costs 0.051 TWh. Applied per border it costs
−0.456 TWh (2022) / −1.067 (2021). Recorded so it is not re-opened.

### 1c. What is NOT attributed

A residual remains between the band-clearing arithmetic and the solved flow: **−3.890 TWh (2022)**
after the envelope, **−0.605 (2021)**. Bracketed by the zonal-price sensitivity — feeding each border
zone's own model price gives 24.242–29.757 TWh against 25.996 load-weighted — so it is *application
geometry* (which zone's price each seam link faces, per-border envelope binding in ~6.5 % of hours,
and the LP's simultaneous clearing), not a ladder construction error. **Characterised, not
attributed.** A successor's object.

### 1d. The under-export is NOT a holdout-only problem

On the keeper's own committed 2025 (a CALIBRATED training year) net export is **23.233 TWh against a
measured 32.925 — −9.692 TWh**, the same signature and nearly the same magnitude as 2021/2022. The
interchange row is PJM's weakest row *in the tuned window too*.

---

## 2. THE MECHANISM BUILT — `pjm_seam_neighbour_hourly_ladder`

Band `k`'s offer becomes hourly, `pi_k(t) = neighbour(t) + delta_k`, so it clears on the seam
**SPREAD** rather than on PJM's absolute price level. A **SUB-GATE** of `pjm_seam_measured_ladder`,
refused at the point of use without it; it DISPLACES the parent's scalar band price on the seams it
covers and DEGRADES to that parent everywhere else — never to an unpriced seam (rule 19
`[R-ONE-MECH]`). Default off, byte-identical off.

**Zero fitted parameters** (rules 21/24): the IDENTICAL Q-Q duration coupling — same midpoint-depth
grid on the same `SEAM_FLOW_TRANCHES`, same measured tie-line flows, same no-wash reconciliation —
read off the spread instead of PJM's own DA. The single degree of freedom is *which measured series
the coupling reads*, the same one the MISO neighbour derivations exercise. The committed table is
**pinned to its derive by test** (rule 23 `[R-FROZEN-DERIVE]`), coverage contract included.

**Anchors named on TOPOLOGY, before any ladder was derived** (rule 14 `[R-ACCURATE]` misalignment
clause, the miso-233 `SPP_ANCHOR_HUB` pattern), never by which scores better:

* **MISO** → equal-weight mean of MISO's three PJM-facing zonal hubs (MISO-Illinois / MISO-Indiana /
  MISO-East) — the exact **mirror** of MISO's own `PJM_WEST` for this same physical seam.
* **NYISO** → NYISO's reference DA, the only measured NYISO series held.
* **Carolinas / TVA / LGEE** → never: SERC publishes no hub, the same data boundary the MISO
  derivation states for SOCO/TVA.

The MISO **system** hub sensitivity **selects nothing** (2022 +0.270, 2023 +0.323, against the
topology anchor's +0.306 / +0.425).

**Coverage is full-or-omit**, so a table row exists iff the solve can arm it. MISO is absent in
2019/2021 (no series) and 2022 (ONE contiguous **525 h** outage in the zonal DA, far past the
repo-standard `limit=3` interpolation).

### 2a. READOUT A — measured record, scored on measured flow (hourly corr, incumbent → arm)

| seam | 2019 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **NYISO** | −0.387 → **+0.568** | −0.231 → **+0.620** | +0.235 → **+0.723** | +0.071 → **+0.553** | +0.201 → **+0.544** | +0.001 → **+0.514** |
| **MISO** | — | — | — | +0.419 → +0.425 | +0.487 → **+0.393** | +0.316 → +0.391 |

A **sign flip** on the NYISO seam in three of six years; volume preserved within 0.02 TWh in every
seam-year. **REPORTED AGAINST THE ARM:** the MISO leg is roughly neutral and **WORSE in 2024**
(−0.093). The repair is the NYISO leg and this session claims no more.

The structural reading: the incumbent NYISO ladder is **negatively correlated with the measured seam
in 2019 and 2021 and ~zero in 2023/2025** — the model's NYISO seam is uncorrelated-to-backwards
against reality, and the spread anchor fixes the sign.

---

## 3. G-DRIFT — and why a CONTROL SOLVE WAS SPENT

`f36cee6e` (the pjm-169 control's `git_sha`) no longer exists after a squash-merge, so per the
charter the audit ran from the pjm-173 anchor **`22eda76a` → HEAD `cbf9be9f`**: 11 solve-path files,
+802/−8.

**INERT:** `model/interchange/spec.py` (cent-level re-derivations of **MISO's** ladder only —
`PJM_SEAM_LADDER_BY_YEAR` untouched); `constants.py` (SPP gas-bridge constants); `fleet/floors.py`
(gated on `netload_drag_layup_window_mask`, default False, absent from PJM's recipe); `runner.py`
(capacity-market clearing — a forecast path a `mode="backcast"` run never enters); the CAISO WECC
intertie parquet.

**LIVE — two, both confirmed active on PJM:**
1. `f923_gas_price_plausibility_screen` (`data/fuel/plant_prices.py`), **default `True`** and
   reachable on PJM's own gates — the control's `run_config.json` carries `mode = backcast` **and**
   `gas_plant_monthly_fuel_pricing = True`, so it resolves ON at HEAD and was behaviourally OFF when
   the pjm-169 control was solved.
2. `EGRID_CT_HR_PHYSICAL_FLOOR` (`fleet/eia860.py`) — **observed firing on PJM in this session's own
   solve log**, clamping ~20 PJM GT/IC plants to the 9.000 MMBtu/MWh simple-cycle floor.

**⇒ G-CTRL form 4 is VOID for this session.** The committed pjm-169 bundle is NOT the control. The
screen spent a **same-HEAD control solve** (G-CTRL form 1), so the only difference between the two
bundles is this card's single declared delta and both live hunks cancel by construction.

---

## 4. THE SCREEN — 2025, gates fixed before the solve

Screen year chosen on **measured footprint** (rule 29 step 1), fixed in the PRECOMMIT: 2025 leads on
every measure (96.3 % of hours changed, mean |ΔMW| 1,907, corr gain NYISO +0.513 / MISO +0.075) and
is a **training** year, so the screen spends no holdout authorization and every gate is purely
protective.

### 4a. Gates S1 / S3 — measured, ZERO LP, at the real 8760 clock

| gate | bar | measured | verdict |
|---|---|---|---|
| **S1 identity** | `max\|mc − law\| = 0` exactly | covered rows (n=32): **0** · uncovered rows (n=48): **0** | **PASS** |
| **S3 footprint** | exactly 32 rows move; 0 non-seam; 0 SERC | 32 moved of 32 expected · 0 non-seam · **0 of 48** SERC | **PASS** |

The applied cost on the covered seams is exactly `anchor(t) + offset_k`, and every uncovered seam
row is exactly the parent's scalar band price — the rule-19 degrade, verified rather than asserted.

### 4b. Gates S4 / S5 — MEASURED

The A/B: `replay_keeper` on the keeper's own frozen recipe, **both legs at HEAD `5e3b6c6a`**, one
declared delta. Control `run_config` carries `pjm_seam_neighbour_hourly_ladder = False`, the arm
`True`, both `mode = backcast` with `pjm_seam_measured_ladder = True`; the arm's solve log carries
*"NEIGHBOUR-ANCHORED HOURLY overlay armed on the covered seams (bands clear on the measured seam
SPREAD)"* and the control's does not. The mechanism is not a no-op: P0 objective 10.948e9 → 11.965e9
(+9.3 %) and P1 11.302e9 → 12.330e9 (+9.1 %), at near-identical simplex counts (99,866 → 100,942).

| gate | bar (fixed in the PRECOMMIT) | measured | verdict |
|---|---|---|---|
| **S4** dispatch response | net export RISES, rise in **[+1.0, +7.0] TWh** | **23.270 → 25.070, +1.800 TWh** | **PASS** |
| **S5** collateral | no load-bearing criterion flips PASS → FAIL | **0 flips** (`screen_collateral_gate`) | **PASS** |

**S4 at full magnitude, including against the arm.** The realised +1.800 TWh is **half** the
pre-registered +3.591 band-clearing prediction (ratio 0.501). It clears the bar, and the bar was
written wide *because* §1a had already measured the band arithmetic over-stating the LP — but 2×
is a larger over-statement than the ~20–25 % §1a records, and that is a fact about the LP's
application geometry (§1c), not a vindication of the estimator.

**The S5 move that is NOT the mechanism's.** The gate reports one non-load-bearing move,
`forced_share 2025 ST_GAS PASS → FAIL`. It appears **identically in the CONTROL's own run of the
same gate against the same keeper**, so it is a replay/HEAD artifact common to both legs and cancels
in the A/B. This is precisely what the §3 same-HEAD control was spent to establish, and it is the
reason a form-4 differencing against the committed pjm-169 bundle would have mis-attributed it to
this card.

### 4c. REPORTED AT FULL MAGNITUDE, GATING NOTHING (rules 1 `[R-STRUCT]` / 29)

| quantity | control | arm | move |
|---|---|---|---|
| net export TWh (measured **32.925**) | 23.270 | 25.070 | **+1.800**, miss −9.655 → **−7.855** |
| **interchange hourly r vs measured** | **+0.587** | **+0.556** | **−0.031 (WORSE)** |
| load-weighted price $/MWh | 42.352 | 43.001 | +0.648 |
| C3a `price_mean` vs band | −3.51 | **−2.89** | toward (control replay moves *away*, −3.54) |
| CT_PEAKER TWh | 27.454 | 28.646 | **+1.192** |
| ST_GAS TWh | 17.060 | 17.311 | +0.251 |
| CC_REGULAR TWh | 334.424 | 334.228 | −0.196 |
| COAL_BIT TWh | 130.726 | 130.771 | +0.045 |
| VIRTUAL_DEC TWh | −18.596 | −17.767 | +0.829 |
| nuclear / wind / solar / hydro | — | — | **+0.000 each** |

**The correlation result is stated against the card.** Readout A predicted the arm would improve
hourly agreement, and on the aggregate net-export series measured against the tie-line meter it does
the opposite: **+0.587 → +0.556**. The two instruments are not the same object — readout A scores
each seam's own flow against its own measured series, while this scores the SUMMED net position —
but the honest reading is that **the seam-level shape repair readout A measures did not survive
aggregation into the LP's net position in this year**, and this card does not claim it did.

**Where the extra export comes from is a real cost, not a free win.** The +1.800 TWh of export is
served almost entirely by **CT_PEAKER (+1.192)** and ST_GAS (+0.251), with CC_REGULAR slightly
*down*. That is the model buying export with peaking gas, and it is the mechanism's honest
signature: raising the export bands' merit position pulls the marginal unit up the stack, which in
PJM 2025 is a peaker. Zero-carbon classes are untouched to the third decimal, as a seam-only
mechanism must leave them.

---

## 5. VERDICT

**The arm CLEARS every pre-registered gate: S1 PASS · S2 PASS · S3 PASS · S4 PASS · S5 PASS.**

Under rule 29 `[R-SCREEN]` that is exactly and only this: **the arm is not killed.** A screen "may
kill an arm; it may never promote one." Nothing here is a promotion, and this bundle is a
throwaway diagnostic probe — 2025 only, never registered, and rule 16 `[R-ALLYEARS]` forbids a
single-year keeper in any case.

**What the session established, in order of confidence:**

1. **The charter's hypothesis is refuted** (zero-LP, unambiguous): the ladder's band prices are
   right to −0.046 / −0.011 TWh.
2. **The anchoring defect is real and large**: −5.735 / −12.699 TWh, 57 % / 88 % of each year's
   miss, with the quantile-map test proving the band prices are not in it.
3. **The repair is real but PARTIAL**: it recovers +1.800 TWh of a −9.655 TWh miss in 2025 — about
   19 % — and it does not repair the hourly shape at the aggregate net position.
4. **The residual is not the ladder's**: −3.890 TWh (2022) of application geometry (§1c) and the
   price-duration-curve error itself (§1) remain untouched.

---

## 6. THE PROMOTION QUESTION — OWNER-FACING, AND IT IS OPEN (rule 31 `[R-RETAIN]`)

**This session does NOT recommend promoting on this evidence, and the reason is a rule, not a
judgement about the mechanism:** a keeper needs a full `--year 2023 2024 2025` bundle (rule 16), and
this is a 2025 screen. The owner's standing ruling — *structural integrity may improve while gates
regress and it can still be a keeper* (rule 1 `[R-STRUCT]`) — is exactly the right frame for this
mechanism, but it needs a full-span bundle to be applied to.

**What promotion would cost:** one `--year 2023 2024 2025` invocation on the arm recipe, ~35–70 min
of LP, plus its control if the owner wants the span differenced rather than scored against the
registered keeper.

**RETENTION, stated plainly per rule 31.** `results/calibration/pjm174_ctl_2025/` and
`pjm174_arm_2025/` are on local disk, **gitignored** (`results/calibration/pjm174_*/`, which is what
discharges rule 29 (c) — they can never reach `main` or turn the parity gate red). **They were NOT
deleted.** This container is ephemeral, so they will not survive session reclamation; if the owner
wants the full span, the 2025 legs would be re-solved as part of it anyway.

**Recommended next step (not taken here):** the higher-value lever is upstream. §1 shows the whole
−5.7 / −12.7 TWh is recoverable by fixing the price duration curve, and the EMAAC CC-availability
card (`ADDENDUM-pjm171-emaac-availability-census-2026-09-07.md`) is a candidate *source* for that
error — phantom CC availability would put CC at the overnight margin, which is pjm-171's measured
trough signature (model overnight implied heat rate 7.9–9.3 vs actual 5.9–7.0). That is a
hypothesis this session did not test, stated as such.

