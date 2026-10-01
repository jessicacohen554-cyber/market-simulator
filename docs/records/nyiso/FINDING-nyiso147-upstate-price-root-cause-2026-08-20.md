# nyiso-147 phase 0 — the 2023 upstate price level is a CHP grid-capacity carve refuted by the plants' own market meters

**Session:** nyiso-147 (the joint-object session chartered by nyiso-146 §3.1).
**Keeper unchanged at phase 0:** `2026-08-19-nyiso-146c-state-scoped`. Phase 0
ran **no LP** — every measurement below is committed artifacts (the nyiso-146
control/keeper/reserve-arm hourly sidecars, the derived actual-LMP reference,
the fleet rebuilt `fleet_only=True` through the nyiso-109/pjm-138 replay
interceptor) plus public measured sources already in `data/raw` (NYISO Gold
Book NYCA generator tables, eGRID 2023, EIA-923). Probes:
`scripts/probes/_nyiso147_upstate_price_phase0.py`,
`_nyiso147_upstate_offer_anatomy.py`, `_nyiso147_chp_grid_capacity.py`;
records `results/calibration/_nyiso147_upstate_price_phase0.json`,
`_nyiso147_upstate_offer_anatomy.json`, `_nyiso147_chp_grid_capacity.json`.

## §1 Where the +9 % lives — the decomposition the charter asked for

C3a per year, verified on the committed sidecars against the bench `rt_lw`
(control / keeper / reserve-duty arm):

| year | actual rt_lw | control | keeper | reserve arm |
|---|---|---|---|---|
| 2023 | 32.25 | **+9.2 %** | +8.7 % | **+11.3 %** |
| 2024 | 38.12 | +2.2 % | +1.6 % | +4.0 % |
| 2025 | 66.43 | −1.9 % | −2.2 % | −1.2 % |

**The whole 2023 error is Upstate_West.** Zone-level contribution to the lw
system error (control, 2023): Upstate_West **+9.46 pp** (zone gap
+$8.77/MWh, **+30.8 %** on its own annual mean), NYC +2.19 pp, Lower_Hudson
+0.51, Capital_Hudson +0.32, Long_Island **−1.63 pp** (−15.0 %). By month the
upstate error is **year-round** (+$6.9 to +$14.7 in 10 of 12 months), not a
winter-basis artifact.

**And it is NOT 2023-specific.** Upstate_West runs **+11.4 % (2024)** and
**+10.8 % (2025)** against downstate under-pricing (NYC −4.4/−7.4 %, LI
−9.5/−11.4 %) that nets the system years to +2.2/−1.9 %. The model carries
essentially **no zonal gradient** (< $1.5 spread across all five zones in
2024/2025; actual gradients $9–15). C3a-2023 is simply the year the
cancellation fails — 2023 downstate is ~right, so nothing offsets the west.
This sharpens nyiso-126 §2.3(4) with the zone attribution it lacked.

## §2 What prices the west — the margin, decomposed

* The model separates the Central-East seam in 28.5 % of 2023 hours (mean
  $3.26) vs the measured $9.44 annual spread — but **even fully separated the
  west clears at $27.8** (all-hours west-marginal offer $30.18). The seam is
  not the primary object; the west's own marginal cost is.
* West marginal-offer decomposition (capacity-weighted over the west-marginal
  unit-hours, control 2023, detection 81.5 % of hours): **offer $30.18 = burn
  $19.59 (HR 10.37 × fuel $1.96) + VOM $2.47 + residual $8.13**; in separated
  hours **$27.84 = 10.04 × $1.79 + $2.37 + $8.16**.
* **The upstate fuel-basis candidate is REFUTED**: the west's marginal
  delivered gas is $1.79–1.96/MMBtu, at the SOM Figure A-6 Tenn Z4 200L
  annual $1.82. `nyiso_zonal_gas_basis` is doing its job.
* **Most of the "markup" is RGGI**, not offer margin: at the marginal HR
  ~10.4 and the NYISO 2023 clearing price $13.49/short ton, carbon is
  ~$7.2–7.4 of the $8.1 residual. The real object is the **marginal unit's
  identity**: the model's west margin is a ~10-HR unit (CC econ-hi tranches,
  CC_CHP, ST_GAS — top pairs `CC_REGULAR:econ` 22,445, `CC_CHP:econ` 18,441
  unit-hours), where the real 2023 west clears on a ~7.2–7.5-HR combined
  cycle at Z4 gas (whose full cost, VOM and RGGI included, reproduces the
  actual west monthly means).

## §3 The root cause — the west's anchor CC enters the LP at 65 % of itself

The model's entire Upstate_West gas ladder below $34 is **~1.05 GW**, and the
census shows the margin lives at its top. The ladder's missing member is
**Sithe Independence Station (54547)** — Zone C, the west's only large
merchant CC (4 × 313.5 MW nameplate; NYISO summer capability 1,012.8 MW),
actual net energy **4.04 / 6.16 / 6.20 TWh** (2023/2024/2025, EIA-923). It is
classed CC_CHP, and the `chp_steam_following` carve removes
**`CHP_BTM_PCT_BY_SECTOR["merchant"] = 35 %`** of it as behind-the-meter host
self-supply — a constant whose own citation comment reads *"residual-identified,
forecast-risk — no independent source yet"*. What survives is 752.6 MW of LP
pmax, of which only ~375 MW (avail-weighted) prices below $24; the top
tranche (102 MW) carries the class peak multiplier at **$37.9**.

**The carve is refuted by the plant's own market meter.** NYISO Gold Book
Table III-2a net energy vs EIA-923 net generation (GWh):

| CY | Gold Book (NYISO-metered) | EIA-923 net | ratio |
|---|---|---|---|
| 2022 | 3,693.1 | 3,683.4 | 1.003 |
| 2023 | 4,049.2 | 4,042.5 | 1.002 |
| 2024 | 6,183.0 | 6,158.0 | 1.004 |

The host's behind-the-meter electric pull is **zero** — everything EIA-923
meters reaches the NYISO grid. eGRID 2023 corroborates: ELCALLOC 0.923, host
steam 8.3 % of heat input (a steam sale, not an electricity one). In 2024/25
the carve is **capacity-infeasible**: 6.16 TWh through 752.6 MW is CF 0.93 —
the model cannot reproduce the plant's own metered year at 100 % availability.

**The defect is fleet-wide, in both directions.** The same Gold-Book-vs-923
identity across every NYISO CHP plant (record
`_nyiso147_chp_grid_capacity.json` + the phase-0 tables):

| plant | zone | npl MW | model grid MW | CY23 grid GWh | implied CF on model cap | measured BTM (pooled 22–24) | model BTM |
|---|---|---|---|---|---|---|---|
| 54547 Independence | Upstate_West | 1,158 | 752.6 | 4,049 | 0.61 (0.93 in 2024) | **~0 %** | 35 % |
| 50006 Linden Cogen | NYC | 974 | 633.2 | 4,391 | 0.79 | **~22 %** | 35 % |
| 56259 Empire | Capital_Hudson | 654 | 424.9 | 2,994 | 0.80 | **~0 %** | 35 % |
| 54914 Brooklyn Navy Yard | NYC | 322 | 209.3 | 1,954 | **1.07 — impossible** | **~3 %** | 35 % |
| 2493 East River | NYC | 716 | 400.1 | 3,078 | 0.88 | **~0 %** | 35/90 % |
| 10025 RED-Rochester | Upstate_West | 163 | ~46 | 2.0 | — | **~98 %** | 35/90 % |

The C1 gate never caught this because the benchmark's `classFull` is
`EIA-923 − BTM` **using the same wrong share** — both sides of the comparison
shrink together, so the error is invisible at class level and materializes
as *price* (the LP's supply curve is short ~1.3 GW of cheap CHP capability
state-wide, the west's margin lands on ~10-HR units) and as *conduct* (other
plants dispatch phantom replacement energy the add-back then re-labels).

## §4 What the phantom cohort buys (the rule-14 quantification the charter asked for)

Reserve-duty arm minus control, 2023: removing the ~1.4 TWh of phantom cheap
upstate CC energy raises Upstate_West +$0.86/MWh (every month) and the lw
system mean +$0.66 (+2.1 pp of C3a). **19 % of the true structural
overpricing (+11.3 %) is masked by energy from plants whose meters say they
were not running.** The two defects are additive at the west margin: the
capacity-only cohort's phantom energy sits *below* the (already too high)
margin because Independence's real capacity, which should occupy that band,
is carved out. One defect hides the other.

## §5 Allegany 7784 (the charter's taxonomy question)

eGRID 2023 carries the plant as ORISPL 10619 "Allegany Station No. 133"
(67 MW, CF 0.020, CHPFLAG blank — its cogen host is gone); the model's 7784
row is the legacy cogen identity. Its CC_REGULAR classing is therefore *not*
the defect — by 2023 conduct it is a capacity-only merchant CC exactly like
the rest of the cohort. What kept it in merit under the reserve-duty arm is
the *level* question (`hr 7.5 × 2.25 ≈ $39.8` peak-routed vs a control margin
of ~$30): with the §3 repair moving the west margin to the low $20s, the same
routing sits ~$18 above the margin instead of ~$8. Whether that clears its
standing ≥80 % C-K2 bar is measured, not re-litigated (PREREG-nyiso146b §ARM
C gates stand).

## §6 The lever this identifies (pre-registered separately)

Replace the sector-default CHP BTM electric share with the **measured
per-plant share** `1 − (Gold Book net energy / EIA-923 net generation)`,
pooled CY2022–2024, clipped to [0, 1], for every NYISO CHP plant the
PTID-verified station join covers — consumed consistently by the three legs
that today share the sector default (LP grid-capacity carve, `_btm_frame`
add-back, benchmark `classFull` subtrahend), gated by a new default-off
`ScenarioConfig.nyiso_chp_btm_measured`. Rule 13 admissibility: both meters
are published, regenerate every year, and respond to changed host
arrangements; the share is a plant-physical property, not an outcome. Rule
14: the measured value replaces an estimate whose own comment declares it
residual-identified. Rule 25: NYISO's own meters only; no other ISO's cell
moves. Blast radius is disclosed ex ante: the benchmark parts for NYISO
2023–2025 regenerate (the pjm-147/pjm-130 precedent), so registered NYISO
runs re-score against the truer benchmark.

## §7 Governance

* No solve ran in phase 0; no parameter moved; the keeper and its dashboard
  entry are untouched. Holdout freeze ACTIVE — all measurements 2023–2025 or
  year-independent; the CY2022 Gold Book column is *input collection*
  (rule 22's 2026-08-06 clause: data intake is unrestricted; nothing was
  solved or scored out-of-training).
* Rule 28a: the NYISO shard, gates stamp and lever queue were read first;
  no cell adjudicated R/I/G covers this object. The pjm-148 host-steam
  refusal is PJM-scoped (rule 25) and its ground — *no measured host share
  exists* — is exactly what NYISO's Gold Book supplies.
* DO-NOT-REDO respected: no min-run work, no unscoped online-hours leg, no
  LI CC/ST basis extension, no 7314 lever, no Zone-K bound, no RHO_CLIP, no
  Iroquois winter spread, no Astoria attribution (East River is measured
  here as a *BTM share*, not re-attributed across the campus boundary).
