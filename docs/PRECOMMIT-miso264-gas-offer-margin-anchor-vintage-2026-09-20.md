# PRECOMMIT — miso-264: MISO's gas-offer margin is identified at a FROZEN 2023-2025 anchor and priced against it in EVERY year. Arm `gas_offer_margin_anchor_vintage`.

```
SESSION : miso-264        ISO: MISO        PARENT LP: ZERO (rule 32 [R-SHARD] (a)).
KEEPER  : 2026-09-19-miso-263-coal-ceiling (results/calibration/miso263_coalcap_span),
          span 2020-2025. TRAIN TIER 2023-2025 CALIBRATED, C3c the lone ledgered
          caveat. Verified present on main before any work.
OBJECT  : the BULK price residual FINDING-miso262 §5 reported and did not fix.
ARM     : gas_offer_margin_anchor_vintage = True (BUILT, default-off,
          byte-identical off; pjm-169 F4). ZERO new fields, ZERO free parameters.
BASIS   : rule 14 [R-ACCURATE]. NOT the residual (rule 1 [R-STRUCT]).
PROBES  : scripts/probes/_miso264_bulk_price_setter_phase0.py (§A-§D)
          scripts/probes/_miso264_marginal_hr_2020.py (§E)
```

---

## 0. WHAT PHASE 0 WAS ASKED, AND WHAT IT ANSWERS

The charter's phase 0: *"what sets the bulk price in 2020's internal zone-hours,
class by class, from the keeper's committed `class_band_hourly` + `system`
sidecars. ZERO LP."* §1 answers it. §2 is what answering it turned up.

Rule 28 `[R-MECH-MATRIX]` (a): the target ISO's cell verdicts were read BEFORE
the object was framed. The arm is **on-queue by the matrix's own words** — the
`gas_offer_margin_anchor_vintage` cell in `docs/codebase-site/data/mechanism-
matrix/MISO.js` reads `U` with the evidence *"row minted pjm-169 (2026-09-06)
… This ISO carries the SAME construction in kind — one frozen 2023-2025 window
anchor in `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, applied to whatever year
is solved — and **it is this lane's to adjudicate on its own market's data**
(rule 25 `[R-ISO-SCOPE]`): no PJM verdict fills this cell, and PJM has minted
none."* Nothing adjudicated `R` / `I` / `G` is re-tested. In particular the
seam stays closed (`import_shape_lever` `G`, re-open condition unmet) and no
COAL_BIT offer-band multiplier is proposed — `FINDING-miso262` §6 refused that
on rule 1(b) and this session does not reopen it.

## 1. WHAT SETS MISO's 2020 BULK PRICE, CLASS BY CLASS

Method: the keeper's own 2020 fleet/offer arrays rebuilt with no LP
(`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`, the sanctioned
reconstruction), then every internal zone-hour's committed P1 dual matched
against the available offer rows at a tolerance **fixed at $0.05/MWh before the
first number**. MISO 2020 has zero slack, zero dump, and a non-zero reserve
dual in 0.01 % of hours, so the energy dual is a clean marginal-offer read.

**The identification is essentially complete: 99.4 % of internal MWh match a
row**, and of the 0.6 % that do not, **0.00 % sit above or below the whole live
stack** — every unmatched hour's dual is interior, i.e. a congestion blend, not
a missing price-setter. Tolerance sensitivity (pooled matched share): 84.7 % at
$0.01, 99.4 % at $0.05, 99.97 % at $0.10, 100.0 % at $0.25. The census does not
move on the tolerance.

MWh-weighted share of the price-setting role, 2020, pooled over internal zones:

| model price band | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| p00–p10 | **CC econ 53.7 %** | coal econ 9.2 % | CC committed 8.5 % | ST_CHP 7.8 % |
| p10–p50 | **CC econ 33.7 %** | coal econ 22.3 % | ST_CHP 8.6 % | ST_GAS econ 6.7 % |
| p50–p90 | **coal econ 53.8 %** | CC econ 9.5 % | CT econ 8.5 % | ST_GAS econ 7.7 % |
| p90–p100 | coal econ 34.8 % | CT econ 21.7 % | ST_GAS econ 9.3 % | CC econ 8.9 % |
| all | coal econ 36.3 % | CC econ 21.8 % | CT econ 8.1 % | ST_GAS econ 7.0 % |

**The answer, in one line: MISO's 2020 bulk is a two-class stack — gas CC econ
owns the bottom half of the price distribution and coal econ owns the top half
— and the seam owns 7.7 % of the cheapest decile and ~3 % overall**, which is
consistent with, and independent of, `FINDING-miso262` §4's 12.6 % hour-count
measurement of the same thing.

That matters because the 2020 miss is **worst at the bottom**: model p10
$20.34 vs RT $14.58, model p50 $26.60 vs RT $19.86. The decile the model
over-prices hardest is the one **a gas class sets 54 % of**.

### 1.1 AND WHAT THE 2020 OFFER IS MADE OF — the uniform implied-HR gap

The same census, carrying each matched row's physical heat rate, delivered
fuel and markup, with the same hours' measured RT price expressed on the same
basis (`_miso264_marginal_hr_2020.py`). `above` is the non-fuel wedge
`mc − HR×fuel`; `imHR` is `price / delivered gas`, the scale-free instrument
`FINDING-caiso270` §4 and miso-214 both used.

| family | share | mc | fuel leg | above | phys HR | markup HR | $/MMBtu | imHR model | imHR market | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| coal econ | 36.3 % | 28.17 | 23.71 | 4.45 | 12.482 | 0.000 | 1.900 | 14.827 | 12.925 | **+1.90** |
| CC econ | 21.8 % | 23.87 | 21.20 | 2.67 | 8.881 | 1.236 | 2.387 | 10.001 | 8.343 | **+1.66** |
| CT econ | 8.1 % | 29.43 | 22.60 | 6.83 | 10.556 | 3.770 | 2.141 | 13.748 | 12.263 | +1.49 |
| ST_GAS econ | 7.0 % | 28.24 | 22.45 | 5.78 | 10.521 | 2.014 | 2.134 | 13.229 | 11.569 | +1.66 |
| CT committed | 5.4 % | 27.46 | 23.50 | 3.96 | 11.256 | 0.826 | 2.088 | 13.152 | 11.378 | +1.77 |
| ST_CHP | 5.1 % | 24.49 | 20.89 | 3.60 | 7.962 | 0.000 | 2.624 | 9.332 | 7.841 | +1.49 |
| CC committed | 4.0 % | 24.25 | 22.42 | 1.83 | 9.364 | 0.107 | 2.394 | 10.130 | 8.124 | +2.01 |
| coal committed | 3.1 % | 27.84 | 23.36 | 4.48 | 11.502 | 0.000 | 2.031 | 13.705 | 11.764 | +1.94 |
| coal peak | 1.7 % | 29.52 | 25.07 | 4.45 | 15.315 | 0.000 | 1.637 | 18.036 | 16.627 | +1.41 |

**The gap is +1.41 to +2.01 in EVERY family, gas and coal alike.** No class is
the carrier. So the 2020 bulk residual is **not** a merit-order or offer-level
defect in any one class's curve, and a lever that reprices one class cannot be
the repair — which independently re-derives `FINDING-miso262` §6's refusal of
the COAL_BIT band lever, by a different instrument.

**DISCLOSED, BECAUSE IT WEAKENS THE READING:** the uniformity is partly
arithmetic. `Δ imHR = (mc − RT) / fuel`, `mc ≈ λ` by construction of the census,
and delivered gas varies only over $1.64–$2.62 across the families, so a roughly
uniform $/MWh price gap divided by a roughly uniform fuel level must come back
roughly uniform. What the table adds beyond that is the **decomposition** — the
non-fuel wedge `above` runs $1.83 (CC committed) to $6.83 (CT econ), i.e. the
offer *forms* differ a great deal between families while the *miss* does not.
A defect that is invariant to a five-fold difference in the non-fuel wedge is
not living in the wedge.

**WHAT THAT LEAVES FOR 2020, NAMED AND NOT TAKEN.** If no offer curve carries
it, the remaining candidate is a QUANTITY story: the model is standing too high
in everyone's stack because cheaper supply that ran in the real 2020 is not
running in the model. `FINDING-miso262` §3 measured exactly that shape — 2020
coal is **short 12.71 TWh** on the gating basis while the seam is **long +6.50
TWh** — and §1 of the same finding showed the seam's volume error is the price
residual transduced, not its cause. This session does not resolve which way that
runs; it records that the 2020 object is a quantity/commitment object, not an
offer-level one, and hands the successor an instrument that says so.

## 2. THE DEFECT THAT FINDING TURNED UP: THE GAS-OFFER MARGIN IS IDENTIFIED AT A FROZEN ANCHOR

`gas_offer_net_revenue_margin` is armed on this keeper (`K` since miso-83) and
reprices 1,295 tranches. Its mc-side half is exactly

```
mc[g, t] += offer_markup_hr[g] x (anchor - fuel[g, t])
```

and its own documentation states the identity that makes the anchor meaningful:
**at `fuel == anchor` the reformed offer reduces EXACTLY to the registered band
multiplier — "the identification point, not a tunable".** The term is a LINEAR
extrapolation with no saturation, so the further a year's delivered gas sits
from the anchor the further the offer departs from the multiplier the ISO was
calibrated with.

The keeper prices **all six years** at `gas_offer_margin_anchor = 3.0492`, the
frozen mean of the model's own delivered-gas series over the **2023-2025**
window. Measured here, by letting `run_year`'s own production block resolve the
solve-year anchor (never a re-implementation of the formula):

| year | frozen anchor | the year's OWN anchor | Δ $/MMBtu | that year's Henry Hub |
|---|---:|---:|---:|---:|
| 2020 | 3.0492 | **2.3294** | **−0.7198** | 2.03 |
| 2021 | 3.0492 | **4.0189** | **+0.9697** | 3.72 |
| 2022 | 3.0492 | **6.5881** | **+3.5389** | 6.45 |
| 2023 | 3.0492 | 3.0187 | −0.0305 | 2.54 |
| 2024 | 3.0492 | 2.5580 | −0.4912 | 2.19 |
| 2025 | 3.0492 | 3.8190 | +0.7698 | 3.52 |

**In 2022 the model prices its entire gas offer surface off an identification
point $3.54/MMBtu — 54 % — below the fuel its units actually burn.** That is
the year the mechanism's own identity says nothing at all about, and it is
MISO's worst-signed price year.

**A THIRD FACT, REPORTED AGAINST INTEREST AND NOT ACTED ON HERE.** The mean of
the three in-window runtime anchors is **3.1319**, not 3.0492 — a **+0.0827
$/MMBtu (2.7 %) construction gap** between the frozen derive
(`scripts/data/derive_gas_offer_margin_anchor.py`, whose `GAS_SERIES_FLAGS
["MISO"]` mirrors the **2026-07-23 miso-81 keeper's** gas recipe) and the
delivered series today's keeper actually prices against. So the identity is
already slightly off even inside the window. This is a rule-23
`[R-FROZEN-DERIVE]` question about a stale derive recipe, it is **not** what
this arm fixes, and it is **routed, not absorbed** — a successor either
re-derives the constant on the current keeper's recipe (citing the recipe
change) or documents why the 2026-07 recipe remains the identification basis.

## 3. THE OFFER-SURFACE RESPONSE, EXACT AND AT ZERO LP

The keeper's `mc_base` rebuilt twice per year, control and armed, differenced.
The per-row shift is constant in `t` to **5.7e-14** — the closed form, measured
rather than assumed. Cap-weighted Δmc, $/MWh:

| year | CC econ | CT econ | ST_GAS econ | CT peak | CC committed | CT committed |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | −0.852 | −3.860 | −1.569 | −19.671 | −0.044 | −0.461 |
| 2021 | +1.151 | +5.204 | +2.137 | +26.041 | +0.057 | +0.594 |
| 2022 | **+4.214** | **+18.976** | **+7.720** | **+94.722** | +0.178 | +2.166 |
| 2023 | −0.036 | −0.164 | −0.067 | −0.817 | −0.002 | −0.018 |
| 2024 | −0.584 | −2.630 | −1.100 | −13.145 | −0.027 | −0.298 |
| 2025 | +0.914 | +4.122 | +1.726 | +20.749 | +0.042 | +0.470 |

Coal, hydro, nuclear, storage, wind, solar and the seam bands carry
`offer_markup_hr = 0` and are **untouched in every year**. The arm is a pure
gas-offer re-identification.

## 4. THE PREDICTION, REGISTERED BEFORE ANY SHARD IS LAUNCHED

First-order, from §1's census and §3's Δmc: each internal zone-hour's price
moves by the demand-weighted mean Δmc over its own matched marginal rows. This
is an ESTIMATE, not a solve — the LP re-dispatches, so the realised move will
differ, and the direction of the error is not known in advance.

| year | predicted Δ price $/MWh | C3a now | C3a predicted | band |
|---|---:|---:|---:|---|
| 2020 | **−0.553** | +16.3 % **FAIL** | ≈ **+13.8 %** | still FAIL |
| 2021 | **+1.251** | +3.0 % PASS | ≈ +6.2 % | PASS, moved AWAY |
| 2022 | **+7.513** | −14.6 % **FAIL** | ≈ **−3.8 %** | FAIL → PASS |
| 2023 | −0.044 | +5.9 % PASS | ≈ +5.8 % | PASS |
| 2024 | −0.839 | +2.2 % PASS | ≈ −0.5 % | PASS |
| 2025 | +1.593 | −4.0 % PASS | ≈ −0.3 % | PASS |

**Four years toward, two away, and the largest move is the one the defect is
largest in.** That is the signature of a real index rather than a fitted level:
a single boolean, one formula, identical in every year, whose effect changes
sign because the MEASURED FUEL changes — which is exactly the property rule 1
`[R-STRUCT]` condition (b) denies a multiplier and `FINDING-miso262` §6 refused
the coal lever for lacking.

**STATED AGAINST THE ARM, IN ADVANCE:**

1. **It does NOT close the charter's 2020 object.** C1 2020 COAL_BIT −10.29 TWh
   and C3a 2020 +16.3 % are the named object; the arm moves 2020 by −0.55 $/MWh,
   about **14 %** of the +$4.05 load-weighted bulk gap. 2020 is predicted to
   stay FAIL. The 2020 object remains open after this session whatever the
   shards return.
2. **C1 2022 CC_REGULAR is predicted to get WORSE.** Through the seam
   transducer `FINDING-miso262` §1 measured (slope 0.462 TWh per +1 pp of price
   bias), a +10.8 pp price move in 2022 pulls in roughly **+5 TWh of extra
   imports**, and 2022's coal is already at its `coal_fuel_inventory` ceiling in
   7 of 12 months, so the displaced energy comes off the marginal gas classes.
   C1 2022 CC_REGULAR is −9.47 TWh today and could deepen toward ~−13 TWh.
   **If that happens it is reported at full magnitude and not tuned away.**
3. **2021 and 2025 move away from zero** (+3.2 pp and +3.7 pp), both staying
   inside the ±10 % band on the prediction. 2021 also carries the span's only
   C3b failure (NRMSE 0.299) and its CT peak tranches move +26 $/MWh, so C3b
   2021 could move either way.
4. **The train tier (2023-2025) is exposed.** 2023 is negligible (−0.04) but
   2024 (−0.84) and 2025 (+1.59) are not. MISO reads CALIBRATED on that tier
   today; a regression there is a real cost and is reported as one.
5. **C3c may improve, which is not a reason to arm.** Raising 2022/2025 peak
   tranche offers by $95/$21 could produce >$200 hours the model currently has
   none of (2022: model 0h vs RT 116h). That is a side effect, reported, not a
   criterion.

## 5. THE DECISION RULE, FIXED NOW

**The arm is adjudicated on rule 14 `[R-ACCURATE]`, and on nothing else.** The
anchor is DEFINED as the mean of the model's own delivered-gas series for the
year being priced; evaluating it on a frozen 2023-2025 window while solving
2020 or 2022 is the wrong index, and the mechanism's own identity is the
evidence — not any residual. Rule 14's own words govern the outcome: *"If
swapping a hand estimate for real data … makes the backcast worse, that is a
signal that something else in the model is miscalibrated. Keep the accurate
input, find and fix the real root cause."*

So:

* **The arm is reported as the candidate whatever §4 turns out to be**, and the
  recommendation to the owner states every regression at full magnitude. A
  worse gate does not retract it; a better gate does not validate it.
* **Nothing is swept.** No alternative anchor, window, scope or cohort is
  tried. One boolean, already built, already default-off, already cache-key
  registered at its `False` drop value.
* **Rule 21 `[R-DOF]`: zero free parameters added.** The keeper's 43 DOF
  entries carry over unchanged. The anchor is not a new parameter — it is the
  same measurement on a different index, and the run records the resolved value
  (rule 24 `[R-REGISTRY]`).
* **Rule 19 `[R-ONE-MECH]`:** the arm REPLACES the frozen identification point,
  it does not stack. `gas_offer_margin_zonal_anchor` is `I` for MISO
  (miso-119/120) and stays off; `run_year` hard-exits on the combination.

## 6. G-DRIFT — form 4 is VALID, so the keeper's committed bundle is the control

Rule 29 `[R-SCREEN]` (b). `git diff bb6e266e..HEAD` over `src/market_sim`,
`scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference` — five commits, every hunk
classified:

| commit | what | verdict |
|---|---|---|
| `aa4bb5b5` caiso-288 | citygate blackout bridge, gated `caiso_citygate_blackout_bridge` | **INERT** — CAISO-only field, default-off, absent from MISO's recipe |
| `3fc20b97` MAC page | `new_entry.py` `cf_override`/`life_override` | **INERT** twice over — capacity evolution is forecast-only (a `mode="backcast"` run never enters it) AND both default `None` = byte-identical |
| `e63f730a` spp-49 | benchmark-membership repair | **INERT** — every hunk threads `benchmark_membership_vintage_union`, a new field defaulting `False`; with it False the code is byte-identical, on the solve path and the bench path alike |
| `5356fb71` nyiso-241 | `nyiso_ct_peaker_committed_measured` | **INERT** — NYISO-gated, default-off, absent from MISO's recipe |
| `cc1bcb24` soco-53e | `measured_st_heat_rates` | **INERT** — default-off, and the only committed artifact is `campd_st_heat_rates_SOCO.csv` |

**All hunks INERT ⇒ form 4 is valid and no control solve is earned.**

**And it is corroborated EMPIRICALLY, which is stronger than the code read.**
The §1 census is a HEAD reconstruction matched against the keeper's COMMITTED
duals: if HEAD's offer path had drifted, those duals would not sit within 5
cents of a HEAD offer row. They do, in **99.4 / 95.7 / 92.1 / 99.0 / 98.3 /
96.5 %** of MWh (2020→2025), with **0.00 % of unmatched MWh outside the live
stack in every year**. The below-99 % years are the congested ones (an interior
blend is not drift), not the drifted ones.

**ONE CORRECTION TO THE INHERITED RECORD, ROUTED NOT ABSORBED.**
`RESULT-miso263` §5.1 attributes a 2.651 TWh actual-side bench move at HEAD to
`e63f730a`. Read hunk by hunk that commit is **threading only** — every new
parameter defaults `False` and is byte-identical at `False` — and at this HEAD
`check_bench_freshness --iso MISO` reports **0 STALE, payload fingerprint
matching**, i.e. the committed MISO parts reproduce at HEAD. I cannot reproduce
the attribution and I do not re-litigate it: **this run is scored on the
COMMITTED bench, the same bench the incumbent was scored on**
(`_miso260_bench_parity` = 0.000000 TWh), so the question cannot reach the
comparison either way. The discrepancy is flagged for whoever owns spp-49.

## 7. HOW IT IS SOLVED

Rule 36 `[R-YEAR-ISOLATION]` + rule 34 `[R-SHARD-PROMOTABLE]`: **six shards,
one per year, one `--years <single year>` invocation each, each pushing its
FULL bundle** (`dispatch/<y>_P1.parquet` included) to its own branch, all pinned
to this PRECOMMIT's immutable SHA. The parent composes at zero LP with
`scripts/probes/_miso260_compose_span.py`, then scores, attests and registers
once (rule 32(d)).

Every shard runs `curate_coal_stocks.py` + `curate_coal_receipts.py` first —
`coal_fuel_inventory` resolves through the derived, gitignored
`data/clean/{coal-stocks,coal-receipts}` and is now a fatal
`PartitionRequirement` (miso-263 §4), so a shard that skips them STOPS, which is
the intended behaviour.

The replay carries the per-year reserve partition explicitly
(`--set miso_measured_reserve_requirements` / `--set miso_reserve_online_gated`
True for 2023/2024/2025, False for 2020/2021/2022), because `replay_keeper.py`
builds its recipe from the span-wide `meta.json` and has no per-year dimension
(`RESULT-miso263` §3). Warm start and the P1 basis seed stay at their
default-OFF (rule 36(d)); neither env var is set.

## 8. WHAT THIS SESSION DOES NOT CLAIM

* It does not close C1 2020 COAL_BIT or C3a 2020. §4 item 1.
* It does not touch the seam. `import_shape_lever` stays `G`.
* It does not touch any coal offer. Coal carries no markup row (§3).
* It does not re-derive `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"]`. §2's 2.7 %
  construction gap is routed, not fixed.
* It spends no LP in the parent (rule 32(a)).
