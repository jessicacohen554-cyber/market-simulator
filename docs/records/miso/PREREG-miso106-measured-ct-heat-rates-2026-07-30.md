# PREREG — miso-106: `measured_ct_heat_rates` on MISO's own CAMPD artifact

> **Status: PRE-REGISTRATION. Committed BEFORE either arm was solved or readable.**
> Every gate, threshold and predicted direction below is fixed at commit time.
> A gate this document does not contain is not scored; a clause that fails as
> written is recorded as a fail (the pjm-136/137 discipline).

* **Session:** miso-106. **Branch:** `claude/miso-106-ct-heat-rates-nmwcfg`.
* **Outgoing keeper:** `2026-07-28-miso-101b-tempgrain`
  (`results/calibration/miso101_tempgrain_B`). Not touched by this session
  unless the owner promotes at the end.
* **Lever:** `docs/mechanism-testing-matrix.md` §5.4 **item 4** —
  `measured_ct_heat_rates`, MISO cell `U`.
* **Rule frame:** 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
  19 `[R-ONE-MECH]`, 22 `[R-HOLDOUT]`, 25 `[R-ISO-SCOPE]`, 26 `[R-MECH-MATRIX]`.

---

## 0. Why this lever, and why not 5 or 6

MISO's queue items 1–3 are all closed: the coal minimum-take RHS is a standing
data ask (miso-103/104), outage grain is instrument-blocked, and DA virtual
depth was refused ex ante by miso-105 with a DO-NOT-REDO list. Of the three
remaining items, **item 4 is the head** on three grounds the other two lack:

1. **A promoted precedent and a defined derivation path already in-repo.**
   `scripts/data/derive_campd_ct_heat_rates.py --iso MISO` exists and is
   ISO-parameterised; NYISO promoted the mechanism at nyiso-89 and PJM at
   pjm-137. Item 5 (`dual_fuel_switching`) needs a MISO dual-fuel registry that
   does not exist in-repo; item 6 (hydro budget / `NG: PS` pin) is a genuinely
   small-fleet item that can follow.
2. **Audit value independent of any gate** — §2 below measures a MISO CT_PEAKER
   plant the model currently prices at **26.544 MMBtu/MWh**, above the physical
   simple-cycle ceiling, and 1,651 MW of peakers priced at a *combined-cycle*
   heat rate. Those are wrong inputs whatever the residual does (rule 14).
3. **Rule 25 is satisfiable.** The parameter is derivable entirely from MISO's
   own CAMPD over MISO's own states against MISO's own model fleet. **No PJM or
   NYISO value crosses the boundary** — not the rates, not the coverage, not the
   direction. pjm-95's refutation of the committed literature slopes on PJM's
   own CAMPD is the precedent for deriving locally, and pjm-137's PREREG was
   itself **refuted in direction** by PJM's own artifact; MISO's prediction
   below is built from MISO's numbers alone.

## 1. Rule 19 `[R-ONE-MECH]` — what already prices/forces this class

Enumerated from the keeper's own `legitimacy_diagnostics.json` **before**
designing the delta:

| mechanism | class | D-4 window | forced TWh 23/24/25 | off-window |
|---|---|---|---|---|
| `nuclear_mustrun` | (nuclear) | — | 87.15 / 90.20 / 90.59 | — |
| `chp_steam` | CC_CHP, CT_CHP, ST_CHP | h0-23 | 5.999 / 5.764 / 6.923 | 0.000 |
| `reliability_floor` × **CT_PEAKER** | CT_PEAKER | **h14-21** | **1.1881 / 1.2030 / 1.1848** | 0.000 |
| `reliability_floor` × ST_GAS | ST_GAS | h0-23 | 0.2442 / 0.2656 / 0.2883 | 0.000 |
| `st_gas_mustrun_per_plant` | ST_GAS | h0-23 | 8.1182 / 8.4945 / 10.4780 | 0.000 |

**Reconciliation.** The only mechanism touching CT_PEAKER is the h14-21
`reliability_floor`, which is a **quantity floor**. This delta is a **cost
input** on the same class — it changes `mc[g,t]`, not `min_gen`. It is
therefore neither a second floor nor a stacked forcing mechanism: no floor is
added, none is widened, none is re-scoped, and no window is declared (so rule
17 `[R-FLOOR-WINDOW]` has nothing to bind on). What it *does* interact with is
the **D-2 denominator** — see gate G6, which is the tightest gate in this
pre-registration.

## 2. The artifact — derived from MISO's own data, zero transferred parameters

`data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv` (86 plant rows) +
`campd_ct_heat_rates_MISO_units.csv` (250 unit rows), written by
`scripts/data/derive_campd_ct_heat_rates.py --iso MISO --detail` at this
session's HEAD. Method, frozen in that script since nyiso-89 and unchanged
here: per CAMPD unit with `unitType == "Combustion turbine"`, over hours at
≥ 0.80 × p95 of that unit's own gross load and ≥ 50 such hours,
`Σ heatInput / Σ grossLoad`, converted to a **net** basis by the committed
`parasitic_load_factors.parquet` (the same map the benchmark's net actual
uses), pooled 2023–2025, aggregated to the plant generation-weighted.

**Coverage and shape (all MISO-measured):**

| quantity | value |
|---|---|
| plants covered / in class | **86 / 168** |
| capacity covered | **19,121 / 22,289 MW = 85.8 %** |
| covered roster's own CAMPD energy | 17.73 TWh/yr vs a class actual of 18.4–19.3 TWh/yr ⇒ **≈92–96 % of the class's real energy** |
| plants excluded by the physical band [6.0, 25.0] | **0** |
| plants moved > 0.5 / > 1.0 / > 2.0 MMBtu/MWh | **51 / 32 / 16** |
| direction split | **56 cheaper / 30 dearer** |
| ISO capacity-weighted | 12.290 → **11.868** (−0.422, **−3.4 %**) |
| ISO generation-weighted | 11.436 → **11.427** (−0.009, **−0.1 %**) |

**The two defects it repairs (rule 14 `[R-ACCURATE]`), both MISO instances:**

1. **Annual average ≠ loaded rate.** *South Fond Du Lac* (7203, 326.5 MW, 4 CTs)
   carries an eGRID plant rate of **26.544 MMBtu/MWh** — above the physical
   simple-cycle ceiling of 25.0 and ~2× any operating turbine. CAMPD shows why:
   the four units produced 2.2–3.7 GWh each in 2024 (CF ≈ 0.5 %), so the annual
   average is overwhelmingly start and part-load fuel. Their **loaded** rate is
   13.79–13.93 gross ⇒ **14.014 net**. It is one of **5** MISO CT_PEAKER plants
   (445 MW) the model prices outside [6, 25] today.
2. **Wrong technology at a mixed facility** — MISO's Doswell. **42 of 168**
   CT_PEAKER plants (2,768 MW) share a `plant_code` with another class, and
   **19 plants / 1,651 MW (7.4 % of class MW)** carry an eGRID plant rate
   **below 9.0** — i.e. a *combined-cycle* rate on a peaker. CAMPD's own
   `unitType` tag is what makes them separable and is decisive: at *Perryville*
   (55620) units 1-1/1-2 are tagged `Combined cycle` and unit 2-1
   `Combustion turbine`; the model prices the 152.7 MW peaker at **6.890**
   against a measured **10.774**. At *Zeeland* (55087) CC1/CC2 are tagged
   `Combustion turbine` and CC3/CC4 `Combined cycle`, and the model's 318.2 MW
   of CT_PEAKER — which matches CC1+CC2 — is priced at **8.587** against a
   measured **10.922**. The artifact covers 7 of the 19 (1,068 MW): Zeeland
   8.587→10.922, Black Dog 8.517→10.491, Alsey 8.617→10.373, Perryville
   6.890→10.774, Moselle 8.892→12.144, Delta Energy Park 7.840→9.582, Hinds
   7.083→10.492.

**Rule 13 admissibility.** A unit's loaded heat rate is a physical
characteristic of the machine. It regenerates for a forward year from the same
pipeline and responds to changed conditions (a retrofit moves it; a new unit
carries its design rate). It is an INPUT, not a measured outcome fed back: no
step of the derivation reads a price, a residual, or a model output. Rule 23
`[R-FROZEN-DERIVE]`: it re-derives only when CAMPD publishes new vintages.

## 3. The mechanical prediction: the CT curve **compresses**, it does not shift

This is the structural claim the gates below are predicted from, and it is
where MISO differs from PJM. Sorting the covered roster into a supply curve at
realized Henry Hub (2023 $2.54, 2024 $2.19, 2025 $3.52 /MMBtu):

| roster quantile | 2023 model → measured | 2025 model → measured |
|---|---|---|
| p10 | $25.86 → $25.80 (−0.06) | $35.84 → $35.76 (−0.08) |
| p50 | $30.02 → $29.92 (−0.10) | $41.60 → $41.46 (−0.14) |
| p90 | $36.72 → $35.07 (−1.64) | $50.88 → $48.61 (−2.28) |
| **p100** | **$67.42 → $53.53 (−13.89)** | **$93.43 → $74.18 (−19.25)** |

Plant-matched, the two ends move in **opposite directions**:

* **bottom-12 of the model's curve** (1,982 MW, the peakers the LP dispatches
  first) — capacity-weighted **+1.280 MMBtu/MWh**, i.e. **dearer**. Seven of
  the twelve are the CC-rate-on-a-peaker set.
* **top-8** (1,454 MW, the never-dispatched tail; real CF 0.064) —
  capacity-weighted **−4.510 MMBtu/MWh**, i.e. much **cheaper**.

So the class's cheap end rises, its expensive tail collapses, and the
generation-weighted mean barely moves (−0.1 %). Every prediction below follows
from that compression.

## 4. Arms

Both arms are `scripts/replay_keeper.py` runs off the outgoing keeper's
`meta.json` at this session's HEAD, `--years 2023 2024 2025` in **one
invocation each**, years sequential inside the invocation (rules 12/16). The
two invocations run **sequentially, not concurrently**: miso-92 measured MISO's
single-year peak at **14.4 GB** against a 15 GB box, so two at once would OOM.

| arm | bundle | delta |
|---|---|---|
| **A — control** | `results/calibration/miso106_control_A` | none (byte-faithful keeper replay at HEAD) |
| **B — treatment** | `results/calibration/miso106_ctheatrate_B` | `--set measured_ct_heat_rates=true`, **one flag, nothing else** |

Rule 22: `--year` is restricted to {2023, 2024, 2025}. **MISO carries no
calibration-complete marker**, so no out-of-training year is solved, scored or
registered, and `--holdout-authorized` is not passed.

## 5. Gates — pre-registered thresholds and predicted directions

Baselines are the outgoing keeper's own committed scorecard
(`scripts/calibration_verdict.py --run-id 2026-07-28-miso-101b-tempgrain`) and
its `legitimacy_diagnostics.json`. **Predicted directions include the ones I
expect to worsen.**

### Construction gates (must all pass, else the arms are not comparable)

* **G1 — flag fidelity.** Arm B's `run_config.scenario_config.measured_ct_heat_rates`
  is `true` and arm A's is `false`; the artifact's `flag != "ok"` row count is
  0, so applied rows = all 86.
* **G2 — the swap is LIVE.** Max |Δ| between arms in the CT_PEAKER class-hourly
  frame is **> 0 in every year** (the nyiso-89 §4a liveness check). A
  bit-identical arm B means the flag did not fire and the run is void, not a
  null result.
* **G3 — arm-A equality.** Arm A reproduces `miso101_tempgrain_B` at
  **max |Δ| < 1e-6 MW on every class-hour in every year** (reported as
  0.00000 % per class-year). This is what makes every arm-B movement
  attributable to the single flag.
* **G4 — zero slack / dump.** Both arms carry the keeper's slack and dump
  profile; a new load-shed hour would mean the re-pricing broke feasibility,
  not that it re-priced.

### Scored gates

| gate | baseline (keeper) 2023 / 2024 / 2025 | threshold | **predicted direction** |
|---|---|---|---|
| **C1 CT_PEAKER volume** | model 15.321 / 19.543 / 18.929 TWh vs actual 19.199 / 19.296 / 18.425 ⇒ **−20.20 % / +1.28 % / +2.74 %** | ±min(2 % load, 8 TWh) = **±8 TWh** and share ≤ 3.0 pp | **volume FALLS in all three years.** ⇒ **2023 WORSENS** (already 3.878 TWh under; 4.12 TWh of band headroom, so no verdict flip expected), **2024 and 2025 IMPROVE** (both currently over). Driver: the 1,068 MW priced at a CC rate leave the CC-competitive band. |
| **C1 CC_REGULAR** | −1.96 % / +0.90 % / −1.78 % | same | **rises** (absorbs the displaced energy) ⇒ 2023 improves, 2024 worsens, 2025 improves. |
| **C1 verdict** | PASS | — | **stays PASS in all three years.** |
| **C3a mean LMP** | 32.41/32.87 = −1.4 % PASS · 30.10/32.27 = −6.7 % PASS · 38.91/45.39 = **−14.3 % CAVEAT (ledgered)** | ±10 % | **\|Δ\| ≤ 1.0 pp in every year; no verdict flip.** **Sign NOT predicted** and deliberately so: the two limbs oppose — a dearer curve bottom raises price when a cheap CT is marginal, but those same MW are replaced by cheaper CC/coal, while the collapsing tail lowers price in the tightest hours. Whichever sign appears is recorded as *unpredicted*, not rationalised after the fact. |
| **C3b price shape — THE KILL GUARD** | NRMSE **0.075 / 0.116 / 0.190**, all PASS | **≤ 0.20 veto** | **WORSENS (rises) in all three years.** The mechanism removes the top of the CT curve, and MISO's standing diagnosed defect (miso-89) is exactly diurnal/seasonal **spread compression** — the model already reproduces only 29–47 % of observed peak-minus-night spread. **2025 has only 0.010 of headroom.** A 2025 crossing to > 0.20 is a **load-bearing PASS→FAIL flip** and will be reported as one. Per rule 1 it does **not** by itself reject the input — but it does block promotion pending the owner, because MISO's ledgered-caveat budget is **saturated 3/3** and the miss could not be ledgered. |
| **C3c price tail** | model 1 / 6 / 0 h > $200 vs actual 30 / 37 / 88 h — CAVEAT (ledgered) | [0.5×, 2×] | **unchanged or marginally worse** (a cheaper CT tail cannot manufacture scarcity hours). Already ≈ 0, so the floor bounds the damage. Predicted change: **≤ 2 hours in any year.** |
| **C4 (C5a) dispatch corr** | gas r 0.944 / 0.934 / 0.952, NRMSE 0.178 / 0.170 / 0.222; coal r 0.896 / 0.875 / 0.890 | r ≥ 0.70, NRMSE ≤ 0.30 | **essentially unchanged, \|Δr\| ≤ 0.010**, verdict PASS. A within-class re-pricing of a class that is 2.4–3.0 % of load cannot move a fleet-level correlation materially. |
| **D-1 / C7 CT_PEAKER** | profile_r 0.971 / 0.971 / 0.985; cv_ratio 0.979 / 0.847 / 0.805 — PASS | r ≥ 0.8, cv_ratio ≥ 0.5 | **cv_ratio RISES in all three years** (the class becomes more peaker-like once the CC-priced units stop running CC-like hours — the physically right direction). **profile_r stays ≥ 0.95.** Verdict **stays PASS.** |
| **D-1 / C7 COAL_PRB** | FAIL all three years (cv_ratio 0.467 / 0.476 / 0.318) | same | **UNCHANGED.** This is MISO's determination blocker and a CT heat-rate change does not touch it. If it moves at all, say so; do **not** claim it as a gain. |
| **D-2 / C8 CT_PEAKER — the tightest gate** | **11.77 % / 8.39 % / 8.78 %** (1.1881/1.2030/1.1848 TWh forced on class totals 10.0964/14.3473/13.4885) | **< 15 %** for a peaker class | **RISES in all three years**, because the h14-21 `reliability_floor` is a fixed MW schedule and this delta shrinks its denominator. **Breach thresholds: the D-2 class total must not fall below 7.921 / 8.020 / 7.899 TWh — a 21.6 % / 44.1 % / 41.4 % fall. 2023 is the binding cell.** A 2023 breach is a protective-tier FAIL and is pre-registered here as the single most likely gate failure. |
| **D-2 / C8 ST_GAS** | 33.4 % / 34.9 % / 45.8 % — above cap but **GROUNDED** (D-4 clear + D-1 clear) | < 30 %, or grounded | **moves < 2 pp and stays GROUNDED.** Not touched except through LP rebalancing. |
| **D-4 off-window** | every limb 0.000 off-window — PASS | ≤ 5 % | **stays exactly 0.000 on every limb.** The delta declares no window and adds no floor; any off-window energy appearing here is a bug, not a result. |

### Pre-registered failure modes, stated in advance

1. **C3b-2025 crosses 0.20** (0.010 of headroom, and the mechanism pushes the
   wrong way). Most consequential.
2. **D-2 CT_PEAKER-2023 crosses 15 %** (needs a 21.6 % class-volume fall).
   Most likely protective failure.
3. **C1 CT_PEAKER-2023 worsens** from −20.20 %. Expected, not a flip.
4. **Zeeland runs a lot in reality** — 4.45 TWh of CAMPD gross over 2023–2025,
   CF 0.532 on its 318.2 MW. Making it $6–8/MWh dearer will cut its model run
   hours against an actual that says it runs hard. This is rule 14's named
   scenario: if the accurate input worsens that plant's fit, the estimate was
   compensating for something else, and the answer is to keep the accurate
   input and open the root cause — **not** to revert.

## 6. Decision rule, fixed now

* The input is **kept regardless of the scorecard** (rules 1/14): it replaces a
  physically impossible 26.544 MMBtu/MWh and 1,068 MW of combined-cycle rates
  on peakers with the machines' own measured loaded rates.
* **Keeper promotion is a separate question** and is *not* claimed by this
  session if either pre-registered failure mode 1 or 2 fires: MISO's
  ledgered-caveat budget is saturated at 3/3, so a new load-bearing miss must
  be **built**, not ledgered, and a protective-tier FAIL is hard.
* No scope widening to chase any gate. No offer adder, no multiplier, no
  re-scoping of the artifact to the plants that help. If a gate moves the wrong
  way it is reported and left.
* Both arms are registered on the dashboard in this session (rule 15) whatever
  the outcome, and the MISO `measured_ct_heat_rates` matrix cell is updated in
  this session (rule 26 duty b) — including if the verdict is a rejection.
