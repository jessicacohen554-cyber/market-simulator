# FINDING — caiso-258: the hod 22–23 energy balance, written on both sides for the first time. **The CC over-run's counterpart is NET IMPORT (−1.7 / −1.8 GW at hod 22 / 23 in 2025, 117 % of the CC over-run) — and D-3 says why the model does not import it: the armed stack is at ONE THIRD of its capability there, with 8.8 GW priced out $4–20 above a node dual of ~$44 that matches the measured price. The market moved 1.8 GW more at that price. On the plant side the model serves that energy with CC plants the real fleet had OFF — 58 % of the 2025 over-run comes from plant-hours where CEMS reads < 5 % of nameplate, half of it on days the plant never ran at all (Moss Landing 91 whole-plant-off days, Otay Mesa 121; the model has 0 of either).** Two instrument results ride along: caiso-253's P-5 import numbers were on the DST wall clock, not the model's clock (on the loader clock the 22–23 import deficit is −972 / −1,467 / −1,763 MW), and EIA-930 CISO's `NG: NG` column carries geothermal/biomass at night and +2 to +6 GW of non-gas at mid-day, so it is unusable hourly. ZERO LP, nothing armed, keeper UNCHANGED. **4 of 8 predictions falsified, one gate literally missed by 1.4 MW and decomposed rather than widened.**

**Session caiso-258, 2026-09-06.** Branch
`claude/caiso-258-backcast-calibration-b1nal9` off `main` `4b4df964`. Keeper
**`2026-09-06-caiso-257-b1-ctonly`** (`caiso257_ctonly`) **UNCHANGED**,
DETERMINATION **CALIBRATED** (rubric v3.6), C3c-2024 the single ledgered
caveat. Pre-registration `PRECOMMIT-caiso258-hod2223-closure-2026-09-06.md`
(`origin`, pushed before any cell of the object was computed). Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze ACTIVE.
Instrument `scripts/probes/_caiso258_hod2223_closure.py` → artifact
`results/calibration/_caiso258_hod2223_closure.json`. Every EIA-930 actual is
read through `eia930.frames._eia_hourly_frame_filled` (the model's clock,
caiso-255b §6 #1); the gas basis is the scorer's own
`_cems_gas_hourly_fit` construction; the model side is the keeper's committed
`hourly/` sidecars. **No solve was spent, no arm was coded, no
`ScenarioConfig` field was added.** The C4-2025 pre-solve check was not spent
because no arm exists; the object's exposure to that cell is measured in §6.

---

## §1 — G-REPRO: 8 of 9 checks inside the registered ±100 MW; the ninth misses by 1.4 MW, and the miss is the CLOCK, decomposed by measurement

| check | published (caiso-252 keeper) | measured (caiso-257 keeper) | diff |
|---|--:|--:|--:|
| CC_REGULAR error hod 22 / 23, 2025, CEMS basis | +1,547 / +1,558 | **+1,535.5 / +1,546.3** | −11.5 / −11.7 |
| storage (all-tech) − `NG: OTH`, hod 22–23, 2023/24/25 | +532.3 / +549.4 / +707.3 | **+522.3 / +533.0 / +693.7** | −10.0 / −16.4 / −13.6 |
| `import` − 930 net interchange, hod 22–23, 2023 / 2024 | −984 / −1,405 | **−971.8 / −1,466.6** | +12.2 / −61.6 |
| `import` − 930 net interchange, hod 22–23, **2025** | −1,662 | **−1,763.4** | **−101.4 — FAIL as registered** |
| C4 gas fit (r / NRMSE), 2023/24/25 | 0.879/0.287, 0.908/0.263, 0.875/0.300 | identical to 3 dp | — |

**The registered check reads FAIL on that row and is recorded as such; the
tolerance is not widened.** What I did instead of stopping is decompose the
miss into its two possible causes, each by measurement:

1. **Keeper identity.** The caiso-257 arm's own footprint at hod 22–23, read
   from the prior keeper's `class_hourly_<year>.parquet` in git history
   (parent `23bbacd7` of the rule-15 prune commit): CC_REGULAR −28 / −24 /
   **−12 MW**, CT_PEAKER +45 / +59 / +34, `import` −2 / −5 / **−3 MW**. The
   CC diffs above are exactly the arm; the import diff is not.
2. **Clock construction.** caiso-253's P-5 read EIA-930 off the raw parquet
   with `Local time − 1 h` (its `_e930_net_import`). Re-running **that**
   construction on the caiso-257 keeper gives **−986.2 / −1,410.0 /
   −1,664.7 MW** against caiso-253's published −984 / −1,405 / −1,662:
   **diffs −2.2 / −5.0 / −2.7 MW** — the instrument reproduces the source's
   own construction to within 5 MW in every year. The two constructions are
   **identical in the standard-time months (Jan–Feb, Nov–Dec: 0 MW
   difference) and one hour apart through March–October** (2,961 of 8,663
   hours equal; 5,715 equal after a one-hour shift): caiso-253's construction
   is the DST wall clock, the model runs on standard time all year. Same
   defect family caiso-255b found in caiso-253's storage read, one
   construction over.

**Consequence for the record:** on the model's clock the keeper's hod 22–23
import deficit is **−972 / −1,467 / −1,763 MW** (2023 / 2024 / 2025) — larger
than caiso-253 published in 2024 and 2025, and hours 22–23 remain the two
worst import-deficit hours of the day.

**Disclosure (the governing one for this section):** proceeding past a
literal FAIL on one of nine checks is a judgment, and it is mine. The basis is
that the gate's purpose — "am I measuring what the record measured" — is met
more strongly by an exact reproduction on the source's own construction than
by a tolerance I sized from the wrong year's delta (the PRECOMMIT took the
±100 MW from caiso-257's 2023 screen import delta, −0.017 TWh, without asking
what a clock does). No number downstream depends on the choice: the closure
uses the loader clock throughout, and §7 scores P-1 as **8 / 9, one miss**.

---

## §2 — G-CLOSE and G-CAT: neither identity closes cleanly, and both failures are results

### §2.1 — Model side: P-2 FALSIFIED. A +66 / +250 / +261 MW supply excess the committed sidecars do not attribute

Σ_klass `mw` + Σ_tech (`discharge` − `charge`) + `slack` − `dump` − Σ_zone
`demand` over the five CAISO load zones is **not** zero: mean **+66 / +250 /
+261 MW** (2023 / 24 / 25), max **233 / 487 / 504 MW**, positive in 8,213 /
8,760 / 8,760 hours; at hod 22–23 in 2025 it is **+190 / +204 MW**. It is
**0.24 % of generation in 2023 and 1.06 % in 2025**, month-flat in 2024–25,
mildly mid-day-peaked (corr with solar 0.82 in 2025). What it is **not**,
each checked: not the WECC import nodes (zero demand, slack and dump there);
not zone slack or dump (zero in every CAISO zone); **not exports** — the
export sinks (`WECC_*_export_*`, negative-floor pseudo-generators, fuel
`import`) never dispatch (the `import` klass minimum is exactly 0.0 in every
year, and the dispatch frame carries signed MW unclipped); not a link-loss
term (`link_loss` is MISO-only). It enters the closure as its own row
(§3) and goes on the queue as a **sidecar-accounting** item under the
standing per-zone/class sidecar ask (E) — it is 13 % of the 2025 CC over-run
at hod 23 and does not change any attribution below.

### §2.2 — Measured side: the EIA-930 balancing residual, shown

`Demand − Net generation − net import`: mean **+610 / +136 / +201 MW**;
**at hod 22–23: +2,068 / +484 / +632 MW**. The 2023 value is a data-quality
flag on the 2023 CISO `Demand` cell — at 22–23 it exceeds the BA's own
reported supply by 2 GW, and the model's "demand gap" against it (−2,330 /
−1,952 MW, §3) is almost entirely that residual: against 930's **supply side**
the model's 2023 demand at 22–23 matches within ~100 MW.

### §2.3 — G-CAT: P-4 FALSIFIED in the contaminated-column direction

`Net generation − Σ(mapped NG columns)` is **zero** (−0.0 / 0.0 / +0.27 TWh,
the 2025 remainder being the 375 hours in December where `NG: GEO` finally
carries a value, 740 MW). So the ~14 TWh/yr of geothermal + biomass are
**inside a mapped column**, and the only candidate with the energy is
`NG: NG`. Measured against the scorer's CEMS gas actual (which already
carries the flat non-CEMS cogen block):

| year | `NG: NG` − CEMS gas, night hod 0–5 | mid-day hod 10–13 | annual |
|---|--:|--:|--:|
| 2023 | 1,496–1,731 MW, flat | **3,259–3,566** | 19.3 TWh |
| 2025 | 1,226–1,543 MW, flat | **6,425–7,369** | 28.2 TWh |

The flat night remainder is geothermal + biomass + non-CEMS gas (the model's
own OTHER + biomass reads 1,568 / 1,425 / 1,045 MW flat, matching the bench's
EIA-923 annual OTHER + biomass of 5.5 + 3.2 TWh in 2025). The **mid-day +2 to
+6 GW is not gas of any kind** — it is the "corrupted EIA-930 NG cell" the
scorer already refuses to score C4 on, and it grows 2023 → 2025 with the
solar and battery build-out. **Every thermal row in the closure is therefore
on the CEMS basis**, and the "other thermal" row is `model OTHER + biomass`
against `NG: NG − CEMS gas` at the hour, labelled as such. (Post-registration
observation, reported only: that mid-day excess has the same hour-of-day shape
and magnitude as the model-vs-930 **demand** gap — −2.1 / −6.0 GW at hod 11
in 2023 / 2025 against +2.0 / +6.4 GW of NG excess — i.e. the 930 `Demand`
cell appears to carry the same mid-day term. That is a lead for the
caiso-247 §4.5 demand-basis ask, not a claim.)

---

## §3 — D-1: THE CLOSURE (Δ = model − measured, mean MW, model clock)

**2025**, the two hours side by side:

| row | hod 22 | hod 23 | basis |
|---|--:|--:|---|
| **demand** | **−785** | **−1,142** | model zone demand vs 930 `Demand` |
| gas, CEMS basis (scorer's) | **+1,297** | **+1,268** | Σ CEMS plants + flat fill/cogen |
| · of which CC_REGULAR | **+1,536** | **+1,546** | 7,258 / 5,723 · 7,145 / 5,598 |
| · of which CT_PEAKER | +21 | −18 | |
| · of which CC_CHP + CT_CHP + ST_GAS | −37 | −38 | |
| other thermal (geo/bio/non-CEMS) | −558 | −541 | model OTHER+biomass 1,045 vs `NG: NG` − CEMS gas 1,603 / 1,586 |
| nuclear | −13 | −12 | |
| hydro, conventional | +177 | +209 | vs `NG: WAT` 3,500 / 3,296 |
| pumped-storage net | +391 | +330 | model only; 930 has no PS column |
| solar / wind | +37 / +13 | +38 / +12 | |
| **li_ion net** | **+256** | **+411** | vs `NG: OTH` 2,750 / 1,273 |
| oil / coal | −40 / +12 | −40 / +12 | |
| **net import** | **−1,719** | **−1,808** | 4,474 / 6,189 · 4,402 / 6,207 |
| Σ supply Δ | −148 | −121 | |
| = Δ demand + 930 residual + model residual | −785 + 447 + 190 = −148 | −1,142 + 816 + 204 = −122 | closes to ≤ 1 MW |

**2024:** demand −770 / −1,121; CC_REGULAR **+1,164 / +1,273**; other thermal
−509 / −551; hydro +94 / +134; PS +415 / +331; li_ion +138 / +181; **import
−1,460 / −1,474**; 930 residual +319 / +648; model residual +177 / +180.
**2023:** demand −2,330 / −1,952 (§2.2); CC_REGULAR **+561 / +487**; CT
+156 / +100; other thermal −18 / +19; hydro +197 / +215; PS +370 / +257;
li_ion +223 / +194; **import −1,091 / −852**; 930 residual +2,230 / +1,905.

**The attribution, mechanical.** Take out the demand basis (the model serves
0.8–1.1 GW less at these hours in 2025, which makes the over-run *harder* to
explain, not easier). What the real market ran that the model did not, at
hod 23 in 2025, ranked by |Δ|:

1. **net import +1.8 GW** (117 % of the CC over-run) — P-5's main leg HOLDS;
2. **other thermal +0.54 GW** — geothermal / biomass / non-CEMS gas the 930
   `NG: NG` cell carries above the model's flat 1,045 MW. Unresolvable at
   hourly grain from this source (§2.3); ~0.35 GW of it survives after the
   cogen block, and it is same-sign in all three years (2023: ≈ 0);
3. the 930 residual itself (+0.8 GW of demand the BA does not attribute to
   any supply).

And what the model ran that the market did not, besides CC: **PS discharge
+0.33 GW, li_ion discharge +0.41 GW, conventional hydro +0.21 GW** — all
same-sign as CC, i.e. the model is long *four* things at 22–23, not one. The
storage half is caiso-255b/256's result re-measured on the closure; the hydro
half is new and small (the model's conventional hydro runs +0.15–0.21 GW over
at night and −0.3 GW under at 07–08 in 2025 — a shape, not a level, question,
and the hydro budget mechanism is a monthly one by design).

**So the object has one name and it is the one caiso-252 §6.1 gave it: the
night/evening price-taking import VOLUME.** Everything else in the closure is
either same-sign (the model long storage and hydro too), a data-basis term
(other thermal, the two residuals), or the demand basis cutting the wrong way.

---

## §4 — D-2: WHAT THE REAL CC FLEET DID — P-6 FALSIFIED in 2025: the over-run is mostly plants that were OFF

Per CEMS-covered CC_REGULAR plant (25 / 25 / 26 plants), plant-hours at
hod 22–23, the REAL unit's state from CEMS (OFF < 5 % of bench nameplate;
PART 5–80 %; HIGH ≥ 80 %):

| year | positive over-run from actual-OFF / PART / HIGH plant-hours | plant-hours OFF: actual vs model | 21→23 shutdowns: actual vs model |
|---|---|---|---|
| 2023 | 35 % / 57 % / 7 % | 6,584 vs 7,705 | 197 vs **432** |
| 2024 | 48 % / 47 % / 5 % | 7,639 vs 6,981 | 182 vs 288 |
| **2025** | **58 % / 37 % / 5 %** | **9,462 vs 8,424** | 155 vs 160 |

Two things follow, and they point away from where a "commitment" reading
would first look:

* **It is NOT an evening-shutdown deficit.** The model shuts CC plants down
  between hod 21 and 23 as often as the real fleet in 2025 and *more* often
  in 2023–24. The ~1,000 extra OFF plant-hours the real fleet shows at 22–23
  in 2025 are not units that ramped off after the peak.
* **Half of the OFF-state over-run is on days the plant never ran at all.**
  D-2b (post-registration refinement of D-2 item 2, labelled so in the probe):
  of the 2025 OFF plant-hours, **7,862 are whole-plant-off days** (daily max
  < 5 %) and 1,451 are days the plant ran and had cycled off; they carry
  **649 MW and 588 MW** of the over-run respectively (of +1,541 net; 2024:
  398 / 456; 2023: 305 / 295). By plant, 2025 whole-plant-off days actual vs
  model: **Moss Landing 91 vs 0**, **Otay Mesa 121 vs 0**, Alamitos 108 vs
  58, Huntington Beach 82 vs 42, Russell City 127 vs 94, Palomar 146 vs 120.
  The model runs Moss Landing at hod 22–23 on **every day of 2025** (cf 0.39
  vs actual 0.18; actual OFF in 42 % of those hours) and Otay Mesa likewise
  (0.64 vs 0.36; OFF 46 %).

**What this is, and is not.** The CAMPD outage overlay the keeper runs on
(`campd-unit-outages-CAISO.csv`, sha `cf156483`) DOES carry Moss Landing
2025 windows — units 1A / 2A / 3A out together 16 Jan–12 Feb, 3–21 Apr, and
more — but they derate the plant to its remaining unit(s) rather than to
zero, so a plant-level "OFF" (< 5 % of the 1,848 MW bench nameplate) is never
reached in the model while CEMS shows the whole plant dark for 91 days. That
gap between a unit-level mechanical overlay and whole-plant days off is the
standing **caiso-187 §3 / caiso-192 mechanical-vs-layup object** (matrix cell
`campd_outage_windows`, K, with its long adjudication record: the
merit-order guard is already applied, post-guard CC_REGULAR X_c 0.24–0.35, and
the spring signature sits on the *mechanical* spans). This session re-measures
it from the dispatch side at two specific plants and two specific hours and
**proposes nothing on it** — it is under DO-NOT-REDO from caiso-192 onward
and it is a per-plant question rule 13 forbids answering with a pin.

**Why the plant reading and the import reading are the same object.** The
model has to serve the hour. At hod 23 in 2025 it serves ~1.8 GW less import
than the market did (§5 says why), so it commits CC plants the market left
off. Turning those plants off in the model would not reproduce the market;
it would leave the LP 1.8 GW short at $44. The plant conduct is the *symptom
on the supply side*; the cause is on the import side.

---

## §5 — D-3: THE ARMED IMPORT STACK AT hod 22–23 — P-7 FALSIFIED: a PRICE gap, not a capability gap

On-recipe `fleet_only` rebuild (seam cap `mic_partition` 16,055 / 16,452 /
16,148 MW verified; no fallback warning; committed `import` ≤ Σ capability
in every hour of every year), every `WECC_*` row at hod 22–23 against the
keeper's committed node duals (PNW $43.8, DSW $44.4 in 2025):

| row (2025) | capability | floor | offer | dual | priced-out share | idle capability |
|---|--:|--:|--:|--:|--:|--:|
| PNW_hydro_base | 2,170 | 1,636 | $28.0 | 43.8 | 0.01 | 9 |
| PNW_midC | 1,764 | 0 | $49.8 | 43.8 | 0.89 | **1,573** |
| DSW_solar_PV (firm) | 2,627 | 1,988 | $48.0 | 44.4 | 0.70 | 401 |
| DSW_CCGT | 1,764 | 0 | $58.7 | 44.4 | 1.00 | **1,757** |
| DSW_CT | 2,156 | 0 | $63.8 | 44.4 | 1.00 | **2,156** |
| WECC_scarcity | 2,940 | 0 | $62.4 | 44.4 | 1.00 | **2,940** |
| DSW_surplus_clean | 38 | 0 | $48.4 | 44.4 | 0.80 | 0 |
| DSW_overnight_clean | **0** (window 0–5) | 0 | $44.4 | 44.4 | — | 0 |
| DSW_daytime_clean | **0** (window 6–21) | 0 | $44.4 | 44.4 | — | 0 |

**Committed import 4,438 MW of 13,459 MW capability (33 %); 8,836 MW priced
out.** 2024: 4,130 of 13,182 (31 %), 8,717 idle. 2023: 4,419 of 12,278 (36 %),
7,039 idle. What the model does import at 22–23 is the two firm floors
(3.6 GW) plus the $28 hydro-base headroom; the next rung is $4–6 above λ
(midC, the solar-PV headroom) and the fossil rungs $14–20 above. **The
model's own stack says: at $44 there is no more import worth buying. The
market moved 1.8 GW more at that price** — caiso-252 §3.2's "price-taking
volume at a matched price" now measured on the stack itself, with the node
dual matching the measured night DA (≈ $42–44) that caiso-252 tabulated.

**What this does and does not license.** It does not re-open pricing:
caiso-252 §7 #2 forbids a ladder-price lever and this table is the reason —
any rung moved down to $44 would be a fitted price. It does not re-open the
clean-transfer windows at 22–23: caiso-253 refused that on the measured
raw-hub discriminator (CAISO clears *below* Palo Verde there in 2023 DA
because the DSW peaks later), and the 1.8 GW that moved did so at or below
the hub, which is exactly why no at-hub row can represent it. What it says is
that the missing volume is **contracted, self-scheduled or WEIM-transferred
energy whose dispatch does not respond to the CAISO hub spread** — the state
variable caiso-253 §3.4 said neither construction carries — and that the
representation the model already has for such volume is the **firm block**
(a floor at capability, price-taking). Its level is a capability (the DMM RA
import figure, 2,323 → 3,371 → 3,371 carried), and the firm rows at 22–23
sit at 3.6 GW against a measured net import of 6.2 GW. **The next step is a
data intake, not a mechanism**: a measured, forward-regenerating source for
contracted import volume beyond the RA showing — the DMM §17 native-load-need
showings caiso-252 §6.1 named, or the CPUC RA import showings — with rule-13
admissibility adjudicated *before* it is wired (a showing is a contracted
capability, not a realised flow; the realised EIA-930 flow is an outcome and
stays forbidden as an input).

---

## §6 — D-4: the object's C4-2025 exposure — P-8 HOLDS

Hours 22–23 carry **8.0 / 7.9 / 9.4 %** of the gas-fleet MSE (2023 / 24 /
25). Zeroing their error would read NRMSE **0.275 / 0.253 / 0.285** against
the scored 0.287 / 0.263 / **0.300**. So the object sits *inside* the cell
that has no margin, and a carrier that closed it would move C4-2025 away from
the bound, not toward it. A direction statement, recorded so it is never
mistaken for evidence; C4 stays excluded from any promotion basis on this
object.

---

## §7 — PREDICTIONS, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-REPRO within ±100 MW on all nine | 8 / 9; import-2025 at −101.4; miss decomposed to the clock (§1) | **8 / 9, one miss** |
| **P-2** | model identity closes < 1 MW every hour | +66 / +250 / +261 MW mean, max 504 | **FALSIFIED** (§2.1) |
| P-3 | demand gap at 22–23 in 2025 between 0.3 and 2.0 GW | −785 / −1,142 MW | **HOLDS** |
| **P-4** | unmapped remainder +1–2 GW flat; `NG: OTH` clean | remainder ≈ 0; geo/bio inside `NG: NG`, which also carries +2–6 GW non-gas at mid-day | **FALSIFIED** (contaminated-column reading) |
| P-5 | import the largest counterpart ≥ 60 %; storage same-sign; hydro and unmapped each < 400 MW | import 117 %; storage same-sign; **hydro+PS +539 / +567, other thermal −541 / −558** | **main leg HOLDS; magnitude leg FALSIFIED** |
| **P-6** | ≥ 50 % of the 2025 over-run from plants ON at lower load | actual-OFF plant-hours carry 58 % | **FALSIFIED** (2025); holds 2023 (35 %), borderline 2024 (48 %) |
| **P-7** | capability gap: import ≥ 90 % of Σ capability, < 500 MW priced out | 33 %; 8,836 MW priced out | **FALSIFIED** — price gap |
| P-8 | 22–23 carry 8–16 % of the 2025 gas MSE; NRMSE ≈ 0.28 if zeroed | 9.4 %; 0.285 | **HOLDS** |

Four falsified, three hold, one 8/9. Every falsification moved the object
somewhere less convenient than registered: the sidecar identity does not
close, the 930 gas cell is unusable, the real fleet had the plants *off* (a
harder story than turn-down), and the model's stack is idle above its own
price rather than exhausted.

---

## §8 — DISCLOSURES AGAINST INTEREST

1. **I proceeded past a literal G-REPRO FAIL** (one row, 1.4 MW over a
   tolerance I set from the wrong year's delta). §1 gives the decomposition
   and the reasoning; the row stays recorded as FAIL.
2. **D-2b is post-registration.** The whole-plant-off / cycled split refines
   D-2 item 2 and was computed after the registered legs; it is labelled
   `POST_REGISTRATION` in the artifact and scores no prediction.
3. **"OFF" is a plant-level state at 5 % of the BENCH nameplate**, which for
   multi-unit plants (Moss Landing's bench 1,848 MW against the overlay's
   1,141 MW plant capacity) is coarse: one unit at minimum load reads PART.
   The direction of §4 does not depend on the threshold; the 58 / 42 split
   between whole-day-off and cycled does, mildly.
4. **The prior keeper's hourlies were read from git history**, not from a
   committed file; the numbers in §1 item 1 are cited here and in the
   artifact and the files were not re-committed (rule 15: git history is the
   record).
5. **The model-side residual is unexplained.** Bounded, characterised and
   excluded from four candidate explanations, but not attributed. It is a
   sidecar-accounting item and it would take the full (gitignored) dispatch
   frames or a replay to close; neither was spent.
6. **The "other thermal" row is a difference of two contaminated things** —
   the model's flat OTHER + biomass against a 930 column that carries
   non-gas at mid-day. At 22–23 the mid-day contamination is absent (the
   night remainder is flat), so the row is meaningful there and nowhere else.
7. **Pumped storage has no measured counterpart.** The closure shows the
   model's PS net at 22–23 (+0.33–0.39 GW) beside conventional hydro and
   does not claim it is wrong; caiso-141/145's wall stands.
8. **No arm, no solve, no promotion, and therefore no ninth C3a direction.**
   The PRECOMMIT §0.1 statement stands: any future arm on this object has a
   favourable first-order C3a direction by construction and must declare it
   unusable before its solve.
9. **The instrument's D-3 leg rebuilds at HEAD, not at the keeper's sha.**
   The cross-check (committed import ≤ Σ capability every hour; seam cap
   `mic_partition`) passed in every year, and nothing solve-affecting on the
   CAISO backcast path has been reported LIVE since caiso-257's bit-identity
   measurement — but this session did not re-run the identity probe, since no
   solve was at stake.

---

## §9 — THE QUEUE AFTER THIS SESSION

1. **The hod 22–23 object is RE-NAMED, with a size: the night/evening
   price-taking import volume, ~1.8 GW at 22–23 in 2025 that no armed rung
   offers at λ ≈ $44** (caiso-252 §6.1's object A, now measured on the stack).
   **Data-intake question first**: a measured, forward-regenerating source
   for contracted import volume beyond the DMM RA showing (DMM §17
   native-load-need showings; CPUC RA import showings), rule-13
   admissibility adjudicated before any wiring. Not a price lever
   (caiso-252 §7 #2), not a window (caiso-253 §7 #1).
2. **The whole-plant-off days the model runs** — Moss Landing 91, Otay Mesa
   121 in 2025 — are the caiso-187/192 mechanical-vs-layup object seen from
   dispatch. Under DO-NOT-REDO from that lane; re-measured here, not
   re-opened.
3. **The sidecar identity residual** (+1 % of generation in 2024–25) — the
   per-zone/class sidecar ask (E), now with a concrete symptom.
4. **The 930 demand-basis lead** (§2.3, post-registration): the 930 `Demand`
   cell appears to carry the same mid-day term as the contaminated `NG: NG`
   cell. Belongs to the caiso-247 §4.5 owner ask, not to this lane.
5. **C4-2025's zero margin**: the 22–23 object is 9.4 % of the cell and
   closing it would relax the constraint (§6).
6. Carried unchanged, raised not granted: **the `complete` marker** (owner
   act, rule 22 — CAISO is CALIBRATED and holds none; raised again); the
   stale `program-status.json` top-level CAISO keeper stamp (not touched);
   the C3a weight basis; the per-zone storage/class sidecar; the DMM 2025
   RA-import basis; Panoche; the borrowed ST_GAS multiplier (untouched this
   session); S2 (unfunded).

---

## §10 — DO-NOT-REDO ADDS

1. **Never cite caiso-253 P-5's −984 / −1,405 / −1,662 MW as model-clock
   numbers.** They are the DST wall clock. On the model's clock the hod 22–23
   import deficit is **−972 / −1,467 / −1,763 MW**. (Extends caiso-255b §6
   #1 from the storage read to the import read.)
2. **Never read hourly `NG: NG` for CISO as gas.** It carries geothermal +
   biomass at night and +2–6 GW of non-gas at mid-day; use the scorer's CEMS
   basis, as C4 already does.
3. **Never read the hod 22–23 CC over-run as an evening-shutdown deficit.**
   The model shuts down at 21→23 as often as, or more often than, the real
   fleet; the excess OFF plant-hours are whole-plant days and cycled days
   the model commits because it is short of import.
4. **Never propose re-pricing a priced-out import rung to reach the 22–23
   volume.** D-3 is a description of why the model does not import; the
   lever it forbids is the one caiso-252 §7 #2 already forbids.
5. **Never attribute the model-side sidecar residual to exports.** The
   export sinks never dispatch (import klass minimum 0.0, all years).
6. caiso-257 §10, caiso-256 (partition) §7 and (storage) §6, caiso-255b §6,
   caiso-254 §6, caiso-253 §7, caiso-252 §7 and §12, caiso-251 §8, caiso-250
   §7, caiso-249 §7, caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7,
   caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7,
   caiso-239 §8, caiso-230 §9, caiso-229 §10, caiso-169 §9, caiso-168 §8
   stand in full.

---

## §11 — DELIVERABLES

`PRECOMMIT-caiso258-hod2223-closure-2026-09-06.md` (pushed first);
`scripts/probes/_caiso258_hod2223_closure.py` +
`results/calibration/_caiso258_hod2223_closure.json`; this finding; the
`docs/calibration-log/caiso.md` entry; rule-28 CAISO matrix-shard
**evidence appends** on `import_hub_pricing` and `caiso_firm_selfsched_floor`
(no verdict move — no mechanism was tested); the §5.2 queue clause in
`docs/mechanism-testing-matrix.md`.

**No run registered (none produced — no solve was spent), no keeper change,
no `ScenarioConfig` field, no new matrix row, no matrix verdict move, no
`complete` declaration.** Rule 15 `[R-DASHBOARD]` is not engaged: it registers
completed calibration *runs*, and this session produced none.

**Next number: caiso-259.**
