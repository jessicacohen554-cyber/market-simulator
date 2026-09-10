# FINDING — caiso-270: the scarcity/ORDC overlay is measured at ~0 % of the 2022 residual, the chartered STOP fires, and December 2022 is not a mechanism

**Session caiso-270, 2026-09-10. Branch `claude/caiso-scarcity-ordc-overlay-8ehxye`. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
Keeper at HEAD: **`2026-09-10-caiso-269-lateevening-clean`**, DETERMINATION **CALIBRATED**, single ledgered C3c. **UNCHANGED.**
**ZERO LP. NO SHARD WAS LAUNCHED. NOTHING WAS ARMED, SOLVED, REGISTERED OR PROMOTED.**
Predecessor charter: `docs/PRECOMMIT-caiso269-lateevening-clean-2026-09-10.md`, `docs/RESULT-caiso269-lateevening-clean-2026-09-10.md`.

---

## §0 — THE RESULT IN SIX LINES

1. **The chartered STOP fired.** Card 0(c) pre-registered: *"If the overlay is <30 % of it, the lever is
   elsewhere and you say so and stop."* The CAISO scarcity/ORDC overlay's contribution to the
   December-2022 C3a excess is measured at **~0 %**, by four independent instruments (§3). The session
   stopped there and spent no LP.
2. **The charter's mechanism hypothesis is false by CONSTRUCTION, not merely by measurement.** The overlay's
   shortage function is `LOLP(R)` keyed to a **reserve margin in MW**; the price level enters **only** as
   `max(VOLL − λ, 0)`, i.e. as a **dampener**. A fuel spike that lifts λ from $50 to $306 *reduces* the adder
   by 13 %. It cannot double-count a fuel spike (§2).
3. **And by measurement, twice over.** **January 2023 is the same western gas crisis** (delivered gas
   load-weighted **$16.54/MMBtu**, daily max $24.75) and it is the model's **single best month of 48**:
   error **+$0.40/MWh**, implied marginal heat rate 7.87 model vs 7.84 actual. "Gas-crisis months" is not a
   failure class for this model.
4. **December 2022 is not a mechanism at all.** Measured at the *same* delivered-gas series on both sides,
   the model's implied marginal heat rate runs above the market's in **40 of 48 months** (mean **+1.01**,
   median +0.84). **December 2022's +1.73 ranks 12th of 48** — eleven months carry a LARGER bias, every one
   of them at gas of $2.06–$5.43/MMBtu. December's $63.91/MWh error is **1.73 HR × $37.04/MMBtu**: the
   ordinary system-wide bias, levered by a gas price 3.7× the year's mean (§4).
5. **C3a-2022 and C3c-2022 are one object; C3c-2023/24/25 is a DIFFERENT one.** The charter states they are
   one mechanism. Half of that is right: 549 of the model's 580 hours >$200 in 2022 are December, all at
   ordinary implied heat rate. But the 2023–2025 tail **deficit** (23/0/0 model hours >$200 against 47/35
   actual; model maxima $209/$180/$72) is the overlay **under**-firing, which is a separate object (§5).
6. **A governance gap, reported because it cost this session.** The designated keeper's bundle
   `results/calibration/caiso269_lateevening_span/` **is not committed** — `.gitignore:1754-1756` was added
   under rule 31 `[R-RETAIN]` during the screen phase and never lifted at promotion — and its container is
   gone. Rule 15 `[R-DASHBOARD]` requires a KEEPER to commit its `hourly/` sidecars; they exist nowhere (§7).

---

## §1 — CARD 0(a): G-DRIFT (rule 29 `[R-SCREEN]` (b)). ALL HUNKS INERT ⇒ G-CTRL FORM 4 VALID

`git diff 8a4912486cd2a7b6ce9a91cbfaeef03c861f4732 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`, against HEAD
`bd04258e`. Eleven files, **every hunk classified**:

| file | change | verdict |
|---|---|---|
| `data/raw/_validation-source/calibration_reference.json` | 198 changed leaves; **197 under `/isos/MISO`**, 1 the `generated` timestamp, **ZERO CAISO leaves** — verified by a full leaf diff, not by eye | **INERT** — another ISO's benchmark |
| `data/raw/reference/…/MISO_2020_renewable_capacity.csv` | new file, MISO | **INERT** |
| `data/raw/reference/spp_curtailment_share.csv` | new file, SPP | **INERT** |
| `scripts/run_calibration.py`, `scripts/run_calibration_full.py` | the `--spp-curtailment-ceiling` / `--spp-curtail-depth-wind` CLI surface only | **INERT** — SPP-gated, default off |
| `src/market_sim/config/scenarios.py` | three new fields: `nyiso_hub_gap_month_level` (NYISO, default `False`), `spp_curtailment_ceiling`, `spp_curtail_depth_wind` (SPP, default off), plus their cache-key registrations. **Zero CAISO tokens in the diff** (verified mechanically) | **INERT** |
| `src/market_sim/data/curtailment_share.py` | new module, SPP-only | **INERT** |
| `src/market_sim/data/fuel/hubs.py` | `_nyiso_hub_daily_gas_prices` **only**, entirely gated on the default-off NYISO field; the CAISO leg `_caiso_hub_daily_gas_prices` is untouched | **INERT** — *and this is what makes §3–§4's delivered-gas series byte-identical to what the keeper solved on* |
| `src/market_sim/data/outages.py` | 11 ORISPL codes appended to the shared `ST_GAS_PEAKER_PLANTS` frozenset — Archbald 50279, Joliet 874/384, Yorktown 3809, McKee Run 599, Eddystone 3161, Clinch River 3775, Chalk Point 1571, Edge Moor 593, Martins Creek 3148, Montour 3149. **All PJM; no CAISO plant** | **INERT** |
| `src/market_sim/data/renewables.py`, `src/market_sim/runner.py` | both changes entirely under `iso == "SPP" and spp_curtailment_ceiling` | **INERT** |

**All hunks INERT ⇒ G-CTRL form 4 is valid and no control solve was spent.** No LP was spent on anything
else either.

---

## §2 — CARD 0(b): THE LEVER'S DRIVER, AND WHY IT DISSOLVED BEFORE A NUMBER WAS QUOTED

The charter named the candidate: *"is the overlay's shortage function keyed to a reserve margin
(forward-regenerating) or to a price level (which in Dec-2022 double-counts the fuel spike)? Read
`results/scarcity.py` before proposing anything."*

**Read. It is keyed to a reserve margin, and the price level cannot double-count.**
`runner.py:4089` → `results/scarcity.py::caiso_scarcity_overlay` → `ordc_adder`, with CAISO's own tariff
constants (`CAISO_SCARCITY_VOLL` 2000, `CAISO_SCARCITY_MCL_MW` 1400, `CAISO_SCARCITY_SIGMA_MW` 2500,
`CAISO_SCARCITY_SHIFT_SIGMA` 0):

    adder(t) = 0.5 · max(VOLL − λ(t), 0) · [ LOLP(R_total(t)) + LOLP(R_online(t)) ]
    LOLP(R)  = 1 − Φ( (R − MCL − μ) / σ ),  administratively 1.0 at R ≤ MCL

* The **shortage function is `LOLP(R)`** — a function of reserve MW alone (`reserve_headroom`: thermal
  headroom on running plants + storage + curtailed renewables, and quick-start capacity offline). That is
  the forward-regenerating limb, and rule 13 `[R-MEASURED]`'s forward test is met by it.
* **λ enters ONLY through `max(VOLL − λ, 0)`, and it enters as a DAMPENER.** At λ = $50 the multiplier is
  $1,950; at December 2022's λ ≈ $306 it is $1,694. A fuel spike makes the adder **13 % smaller**, not
  larger. The structure the charter suspected of double-counting does the exact opposite.

So the driver evidence for the chartered arm was gone before any residual was measured. That is recorded
here rather than being written up after the fact.

**Rule 28(a) `[R-MECH-MATRIX]`, checked first as the DO-NOT-REDO discipline requires.** The CAISO shard's
`ordc_scarcity_overlay` cell was already **`K`** carrying **caiso-229**'s adjudication (2026-08-31,
`FINDING-caiso229` §8, NO LP): bounded arithmetically with the same four constants against caiso-131 §4's
committed minimum-headroom hour, **max adder $0.017 / $0.006 / $0.003 per MWh (2023/24/25)** — *"Inert on
C3a and on C3c; cite the bound, never the absence."* The chartered lever was already adjudicated inert; what
this session adds is the **2022** limb the bound did not cover, and a direct measurement of the year the
charter targets.

---

## §3 — CARD 0(c): THE DECOMPOSITION, AND THE STOP

### §3.1 — The instrument, and its validation

C3a is reconstructed as the demand-weighted mean of the per-zone P1 price over all seven CAISO model zones,
from the committed `hourly/system_<year>.parquet` sidecars. It **returns the published control values
exactly**: 2022 **+13.17 %**, 2023 **+4.39 %**, 2024 **+8.90 %**, 2025 **+8.25 %** — the same four numbers
`RESULT-caiso269` §2.1 publishes in its control column.

Delivered gas is the keeper's own series: `_caiso_hub_daily_gas_prices(config, year, spot_level=True,
spot_coverage=True) + CAISO_CITYGATE_TRANSPORT_ADDER` ($0.46), i.e. the measured CA-composite citygate
**daily** spot under the armed `caiso_citygate_spot_level` / `_flow_date` / `_spot_coverage` recipe. Per §1
that code path is byte-identical at HEAD to what the keeper solved on. **The EIA-923/N3045 monthly level
($27.48 for Dec-2022) is NOT the model's December gas price** — the hub overlay supersedes it in covered
months, and 2022 is covered in all 8,760 hours (range $3.80–$53.59 before the adder).

**Basis substitution, stated at the gate.** The keeper's own bundle is not committed and no longer exists
(§7), so §3–§4 run on the committed **predecessor** — `caiso_fuelvintage_tp2022` (2022) and
`caiso_fuelvintage_span` (2023-2025), which are exactly the controls `RESULT-caiso269` §2 differenced
against. The keeper differs from them by **−0.232 / −0.032 / −0.124 / −0.131 $/MWh** on C3a, i.e. **≤ 0.4 %
of the December object**. Every conclusion below is invariant to the substitution.

### §3.2 — C3a-2022 by month

All three columns on the **same** delivered-gas series. `HR` = implied marginal heat rate
(load-weighted price ÷ load-weighted delivered gas); `dHR` = model − actual.

| mo | gas LW $/MMBtu | actual $/MWh | model $/MWh | err | load share % | **contrib $/MWh** | HR act | HR mod | dHR |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | 5.43 | 43.52 | 55.94 | +12.42 | 7.78 | +0.966 | 8.01 | 10.30 | +2.29 |
| 2 | 5.24 | 38.96 | 51.12 | +12.16 | 7.01 | +0.852 | 7.43 | 9.75 | +2.32 |
| 3 | 5.20 | 43.56 | 48.31 | +4.75 | 7.54 | +0.358 | 8.38 | 9.29 | +0.91 |
| 4 | 7.11 | 49.76 | 59.50 | +9.74 | 7.27 | +0.709 | 7.00 | 8.37 | +1.37 |
| 5 | 8.91 | 58.76 | 67.23 | +8.47 | 7.90 | +0.669 | 6.59 | 7.54 | +0.95 |
| 6 | 8.37 | 70.77 | 75.48 | +4.71 | 8.94 | +0.421 | 8.46 | 9.02 | +0.56 |
| 7 | 7.85 | 71.80 | 80.06 | +8.26 | 9.68 | +0.800 | 9.15 | 10.20 | +1.05 |
| 8 | 9.75 | 96.77 | 103.04 | +6.27 | 10.43 | +0.654 | 9.92 | 10.57 | +0.64 |
| 9 | 8.92 | 123.41 | 125.43 | +2.02 | 9.74 | +0.197 | 13.84 | 14.07 | +0.23 |
| 10 | 6.54 | 64.33 | 70.12 | +5.79 | 8.19 | +0.474 | 9.84 | 10.72 | +0.89 |
| 11 | 8.70 | 82.92 | 86.89 | +3.97 | 7.46 | +0.296 | 9.53 | 9.99 | +0.46 |
| **12** | **37.04** | **242.20** | **306.11** | **+63.91** | **8.08** | **+5.163** | **6.54** | **8.27** | **+1.73** |

Total reconstructed contribution **+11.558 $/MWh** (direct annual model − actual **+11.131**; the gap is the
month-share reconstruction). **December is 5.163 / 11.558 = 44.7 % of the 2022 excess** — the single largest
month, and enough on its own to flip C3a-2022 (removing it leaves +6.4 / +7.1 % against a ≤ +10 % band).
**Every one of the twelve months is positive.**

### §3.3 — The overlay's share of that: ~0 %, by four independent instruments

1. **The registered arithmetic bound (caiso-229).** Max adder **$0.017 / $0.006 / $0.003 per MWh** in
   2023/24/25 — cited, not re-derived.
2. **The 2022 limb of the same arithmetic, computed here.** With CAISO's four constants and λ = $306, the
   adder reaches a given size only below a given reserve headroom `R`:

   | adder | requires R ≤ |
   |---|--:|
   | $50.00/MWh | 5,530 MW |
   | $10.00/MWh | 7,110 MW |
   | $1.00/MWh | 9,007 MW |
   | $0.017/MWh | 11,667 MW |

   caiso-229's 2023 bound of $0.017 therefore implies that year's **minimum** headroom was ≈ 11,667 MW
   (consistent with the caiso-59 finding that CAISO's reserve co-opt is inert at ~12.9 GW headroom against a
   2.2 GW requirement). For the adder to supply even **16 %** of December's $63.91 error, CAISO's model
   reserve headroom would have to fall to **≤ 7,110 MW** — about 4.5 GW below the minimum the committed
   record shows for the adjacent years — and to supply the whole of it, to ≈ 5,200 MW.
3. **A direct, assumption-free ceiling.** The adder is added **uniformly to every zone**
   (`runner.py:4099`, `result.prices = result.prices + caiso_adder[None, :]`), so
   `adder(t) ≤ min_z price(z,t)`. In **62 December hours a zone prices at exactly $0.000** — and those hours
   fall at hod 0-4, 11-12 **and 16-23**, i.e. inside the evening net-load peak the overlay exists to price.
   In those hours the adder is provably **exactly $0**, while the December load-weighted price at hod 17-22
   runs $354-372.
4. **The diurnal signature is absent.** December's implied marginal heat rate by hour of day is
   **6.91–9.86 across all 24 hours** — the flattest and lowest profile of the year — with **no evening
   bulge**: its h16-22 values (9.4-9.9) sit *below* February's (11.5-13.2) and November's (11.4-11.8). An
   adder firing on evening reserve tightness produces the opposite shape. And **zero December hours carry an
   implied heat rate above 25**, against 23 such hours in September 2022 (max load-weighted price $1,247,
   implied HR 115 — a peak-band offer, since caiso-229's bound forbids an adder of that size, and since
   `slack` is 0.0 in all 61,320 zone-hours of 2022). **September is the model's best month of 2022**
   (dHR +0.23, contribution +0.197).

**⇒ The overlay's share is ~0 %, far below the pre-registered 30 % threshold. CARD 0(c)'s STOP FIRES.
The lever is elsewhere. No shard was launched.**

### §3.4 — Cards 0(d) and 0(e), discharged by saying what did not happen

* **(d) Screen year.** None is named, because no arm survives card 0(c) to screen.
* **(e) The mandatory zero-LP bind check.** Not run, because there is **no flag to bind** — no
  `ScenarioConfig` field was added, changed or proposed by this session. The check that
  `RESULT-caiso269` §7 made standing is owed by the next lane that adds a solve flag, and it is not
  discharged here by omission.

---

## §4 — WHAT THE OBJECT ACTUALLY IS: A SYSTEM-WIDE +1 HEAT-RATE-POINT MARGINAL-UNIT BIAS

The same instrument over **all 48 months of 2022-2025**, both sides at the same delivered-gas series.

**`dHR` > 0 in 40 of 48 months. Mean +1.01, median +0.84.** The twelve largest:

| rank | month | gas LW $/MMBtu | dHR |
|--:|---|--:|--:|
| 1 | 2024-05 | 2.06 | +5.15 |
| 2 | 2024-04 | 2.07 | +3.62 |
| 3 | 2023-05 | 2.99 | +3.55 |
| 4 | 2024-06 | 2.32 | +2.62 |
| 5 | 2022-02 | 5.24 | +2.32 |
| 6 | 2022-01 | 5.43 | +2.29 |
| 7 | 2025-04 | 2.63 | +2.25 |
| 8 | 2023-06 | 2.93 | +2.05 |
| 9 | 2025-12 | 3.76 | +2.04 |
| 10 | 2024-03 | 2.26 | +2.02 |
| 11 | 2024-08 | 2.50 | +1.94 |
| **12** | **2022-12** | **37.04** | **+1.73** |

Binned by delivered gas level (model / actual implied HR, n months):

| gas $/MMBtu | HR model | HR actual | n |
|---|--:|--:|--:|
| (0, 3] | 12.01 | 10.01 | 13 |
| (3, 5] | 11.20 | 10.71 | 18 |
| (5, 8] | 9.72 | 8.80 | 10 |
| (8, 12] | 10.24 | 9.67 | 5 |
| (12, 20] | 7.87 | 7.84 | 1 |
| (20, 60] | 8.27 | 6.54 | 1 |

**December 2022 is the twelfth-worst month of 48 on the bias, and the worst month by dollars, and those two
facts are the whole story.** Eleven months carry a LARGER marginal-unit bias; every one of them prices at
$2.06-$5.43/MMBtu, where the identical bias is worth $2-12/MWh instead of $64.
**$63.91 = 1.73 HR-points × $37.04/MMBtu.** There is no December mechanism to find: there is one residual,
present in essentially every month of every year, that December's gas price multiplies by ten.

This also disposes of "the 2022 gas-crisis months" as a class. The two crisis months in the record behave
oppositely: **2022-12** (gas $37.04) dHR **+1.73**, and **2023-01** (gas $16.54, daily max $24.75) dHR
**+0.02** — the single best month of the 48, model $130.09 against actual $129.69.

---

## §5 — THE C3c HALVES ARE TWO OBJECTS, NOT ONE

The charter states the C3a and C3c residuals are *"ONE mechanism (the scarcity/ORDC overlay and its
gas-crisis interaction), not two."* Measured, that is half right and half wrong, in a specific way:

| year | model h > $200 (system LW) | of which December | model max LW price | actual RT h > $200 (charter) |
|---|--:|--:|--:|--:|
| 2022 | 580 | **549** | $1,247 | 510 |
| 2023 | 23 | 0 | $209 | 47 |
| 2024 | **0** | 0 | $180 | 35 |
| 2025 | **0** | 0 | $72 | — |

* **2022's tail EXCESS is the same object as C3a-2022** — 549 of 580 hours are December, at ordinary implied
  heat rate (§3.3 item 4). Fuel × the +1 HR bias. The charter is right that these two are one thing.
* **2023-2025's tail DEFICIT is a different object.** The model produces **no hour above $200 at all** in
  2024 or 2025, against 35 measured in 2024, and its annual maxima are $180 and $72. *That* is the overlay
  under-firing, and it is what the ledgered C3c caveat names. It is not the December-2022 mechanism seen
  from another side; it is the opposite sign in different years.

(Counts here are on the system load-weighted series; the charter's 586 is the rubric's own C3c basis. The
549/580 split is what matters and is basis-insensitive.)

---

## §6 — THE SUCCESSOR, NAMED AND DELIBERATELY NOT SOLVED

Phase 0 leaves one well-posed question, and it is **not** the one the session was chartered on:

> **Why does the model's implied marginal heat rate run ~1 point above the market's in 40 of 48 months?**

Two candidate homes. **Neither is proposed as an arm here**, because picking one off this residual is exactly
the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids; each needs its own charter, its own external
driver named before any number, and its own zero-LP footprint:

* **(a) Offer-band / merit-order composition at the top of the CAISO stack.** The bias is largest at LOW gas
  ((0,3] bin: model 12.01 vs actual 10.01) — the spring solar-glut months where the real market clears far
  below gas cost and the model will not. This is the same object caiso-267/268's flat multipliers attacked
  from the wrong end, and the owner refused both on rule 1 grounds; a third flat multiplier is **not**
  proposed and the factor is **not** resized.
* **(b) The quantity side, recorded as a measurement and not as a proposal.** December 2022, monthly means:
  model gas **8,812 MW** (CC_REGULAR 7,341 + CC_CHP 1,118 + CT_PEAKER 198 + CT_CHP 150 + ST_GAS 5) and model
  import **5,613 MW**; measured CISO EIA-930 natural gas **11,829 MW** and net import **4,661 MW**. The
  levels are **not** directly comparable (EIA-930's NG carries BTM/cogen outside the model's CAISO fleet),
  so only the signs are stated: the model imports **more** and burns **less** gas than the measured record in
  the month it over-prices. Nothing is concluded from this here.

**What is NOT re-opened** (rule 28(a) DO-NOT-REDO, all closed by caiso-269 and left closed): the belly
over-import and its p95 corridor percentile; the funded G-26 / audit C-6 import price ladder; depth-shaping
the clean tranches; the hod 22-23 window gap; flat fossil offer multipliers of any size; the CT_PEAKER
volume residual (owner ruling caiso-261).

---

## §7 — DISCLOSURES AGAINST INTEREST, AND ONE GOVERNANCE GAP

1. **The session produced no run and no improvement.** It spent no LP and it moved no criterion. Its entire
   output is a measurement that kills its own charter. That is the deliverable, and it is stated first.
2. **The chartered lever was already adjudicated.** caiso-229 bounded the overlay at $0.017/MWh on
   2026-08-31 and the matrix cell has read `K` with that bound ever since. Checking the matrix **before**
   proposing (rule 28(a)) is what surfaced it; a session that had gone straight to a solve would have spent
   four shard-years to rediscover it.
3. **§3-§4 run on the predecessor bundle, not the keeper's.** Forced by item 5 below. The instrument
   reproduces the published control exactly and the keeper-vs-predecessor gap is ≤ 0.4 % of the object, but
   the substitution is real and is declared rather than glossed.
4. **The 2022 reserve-headroom figure is a BOUND, not a measurement.** §3.3 item 2 says what `R` would have
   to be, not what it was; the keeper's per-generator dispatch is not committed, so `R` for 2022 cannot be
   computed without a solve. Items 3 and 4 of §3.3 are direct and do not depend on it.
5. **GOVERNANCE GAP — the designated keeper's bundle does not exist.**
   `results/calibration/caiso269_lateevening_span/` is named by
   `frontend/data/backcast/keepers/CAISO.json`, by the registry sidecar
   `2026-09-10-caiso-269-lateevening-clean.json`, and by `scripts/gen_caiso269_attestation.py` — and it is
   **not in `main`** (`git ls-tree -r HEAD` returns nothing under it) and not on this container's disk.
   `.gitignore:1754-1756` ignores `results/calibration/caiso269_lateevening_*/`, added under rule 31
   `[R-RETAIN]` while the run was a screen, and **never lifted when the run was promoted to keeper**.
   Rule 15 `[R-DASHBOARD]` requires a KEEPER bundle to commit its `hourly/` sidecars
   (`class_hourly_<year>` + `system_<year>` + `reserve_family_<year>`) precisely so a later diagnostic
   session reads them instead of replaying the solve — and this session is the first one to need them.
   `check_registry_payload_parity.py` does **not** catch it: that gate flags committed dirs with no sidecar,
   not sidecars with no dir. (It is currently RED on seven **ERCOT** bundles — `ercot262_arm_2021..2025`,
   `ercot264_repro_2023/2025` — which is another lane's and untouched here, rule 25.)
   **Recovering the CAISO keeper's sidecars costs a four-year re-solve.** Not spent; put to the owner in §8.

---

## §8 — WHAT I AM ASKING THE OWNER (rule 31 `[R-RETAIN]`)

**Nothing was solved, so no bundle is at risk of being lost with this container.** Rule 31's usual
promotion question does not arise. Two decisions are open instead:

* **(A) Where CAISO's next lane goes.** The chartered object is closed. My recommendation is to charter the
  §6 question — the +1 HR marginal-unit bias measured across 40 of 48 months — as its own session, with the
  low-gas / solar-glut limb (§6a) as the target, since that is where the bias is largest (up to +5.15 HR
  points) and where the *structure* is most obviously missing. **I am explicitly not proposing a mechanism**;
  the next lane should name its driver before it names a number.
* **(B) Whether to re-solve the CAISO keeper to restore its bundle (§7 item 5).** Four shard-years. It buys
  the committed `hourly/` sidecars rule 15 requires of a keeper, without which every future CAISO
  diagnostic pays a replay. If yes, I would also lift `.gitignore:1754-1756` in the same change so the
  promotion actually reaches `main` this time. **I have not spent it.**

Also worth an explicit ruling if the owner wants it: **2020/2021 remain blocked on DATA**
(`data/raw/reference/caiso-supply-consistent-demand/` and `frontend/data/backcast/bench/CAISO/` both start
at 2022). The charter directs that as a separate parallel intake session; it was not started here.

**Next number: caiso-271.**
