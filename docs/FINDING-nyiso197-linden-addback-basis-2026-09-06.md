# FINDING nyiso-197 — the Linden 50006 `CC_CHP` "−1.0 TWh regression" **DOES NOT EXIST** in the committed keeper: it is a CHP add-back basis mismatch inside the nyiso-196 §4.2 table. On the committed payload Linden **ROSE +224 / +243 / +227 GWh**, and against NYISO's own Gold-Book meter the plant is **+0.90 TWh/yr OVER**, not under. **No measured object survives step 2; no solve was run.**

**Session:** nyiso-197 (`claude/linden-50006-regression-zgqpjj`), 2026-09-06.
**Keeper (unchanged):** `2026-09-06-nyiso-196-extract-basis`, bundle
`results/calibration/nyiso196_extract_basis` — CALIBRATED, grade 7, fails 0, C3c ledgered.
**Solves run: ZERO.** Every number below is read from committed artifacts (the two run payloads,
the shared bench part, both bundles' `hourly/` sidecars, the committed `-perunitmerit-` outage
extract, the raw CAMPD unit-level series, EIA-860/923, the NYISO Gold Book editions) plus two
`fleet_only` rebuilds of the keeper's own `meta.json` (no LP).
**Machine records:** `results/calibration/_nyiso197_linden_phase0.json`,
`_nyiso197_linden_rebuild_2023.json`, `_nyiso197_linden_rebuild_2024.json`; probes
`scripts/probes/nyiso197_linden_phase0.py`, `scripts/probes/nyiso197_linden_rebuild.py`.

---

## 1. The result in one paragraph

The object this session was convened on — *"Linden 50006 falls ~1.0 TWh in every year, AWAY from a
7.2–7.4 TWh meter, although its own availability ROSE"*
(`FINDING-nyiso196` §4.2 regression (i), §6 item 1, matrix §5.5 top of queue) — **is not in the
committed artifacts.** Decoding the two registered payloads on the same basis, Linden goes
**6.325 → 6.549 / 6.197 → 6.440 / 6.162 → 6.390 TWh**: it **GAINED** 224 / 243 / 227 GWh under the
extract-basis repair, which is exactly what its own availability census
(`_nyiso196_extract_basis_census.json`: +302 / +326 / +314 GWh available) predicts, and it is the
**second-largest gainer** of the energy Cricket Valley released in all three years. The
nyiso-196 §4.2 row mixes two bases: its *keeper* column is the prior keeper's **payload**
(full-plant, carrying the measured CHP add-back) and its *arm* column is the arm's **LP grid**
series (no add-back). Linden is the **only** plant in that table with a non-zero measured
behind-the-meter hold-out (1.25 TWh/yr, 22.21 %), so it is the only row the mismatch can move —
every other row of §4.2 reproduces from the payloads to the digit. The real, opposite-signed
Linden object is that the model **over-delivers** the station: against NYISO's own Gold Book
Table III-2a net energy for Linden Cogen (PTID 23786, Zone J) the keeper's LP grid dispatch is
**+904.9 GWh (+20.6 %) in 2023 and +901.8 GWh (+21.0 %) in 2024**, and the extract-basis repair
made that *larger* (prior +680.9 / +658.8). Step 2 found **no measured input the model
contradicts**: capacity, availability, the BTM hold-out and the import seam are each already on
the accurate basis, and the one genuine unrepaired mismatch (a New Jersey plant charged the NYC
citygate) has no committed series to swap in and pushes the residual the wrong way. Per the
session brief's step 4 the Linden cell is **filed to the owner court, re-specified**.

## 2. Step 1 — the decomposition, and the diff that refutes the premise

### 2.1 The payload diff (`_nyiso197_linden_phase0.json`, L-3)

Both registered payloads carry `nyiso_chp_btm_measured = true`, so both render the per-plant
series as *LP grid dispatch + the measured flat CHP add-back* — an apples-to-apples pair.

| plant (2024) | prior keeper `…-192-astoria-panel` | keeper `…-196-extract-basis` | Δ |
|---|---|---|---|
| Cricket Valley 57185 | 5.038 | 3.706 | **−1.332** |
| Selkirk 10725 | 0.261 | 0.048 | −0.213 |
| Athens 55405 | 3.572 | 3.837 | +0.265 |
| **Linden 50006** | **6.197** | **6.440** | **+0.243** |
| Sithe 54547 | 7.370 | 7.490 | +0.120 |
| Saranac 54574 | 0.468 | 0.573 | +0.105 |

Linden is the **top or second gainer** in every year (+224.0 / +243.0 / +227.4 GWh); Cricket
Valley's released energy lands on Athens, Linden, Sithe, Bethpage, Saranac and Astoria. Zonal
mean prices move +0.06 / +0.53 / +0.26 $/MWh; slack and dump are unchanged at 0.

### 2.2 Cross-check — every OTHER §4.2 row reproduces exactly

| plant (2023, TWh) | nyiso-196 §4.2 `keeper → arm` | committed payloads `prior → keeper` |
|---|---|---|
| Cricket Valley 57185 | 5.41 → 4.81 | 5.405 → 4.812 ✔ |
| Athens 55405 | 1.68 → 1.89 | 1.677 → 1.888 ✔ |
| Bethpage 50292 | 0.19 → 0.26 | 0.194 → 0.256 ✔ |
| CPV Valley 56940 | 3.62 → 3.66 | 3.616 → 3.650 ✔ |
| Selkirk 10725 | 0.15 → 0.04 | 0.152 → 0.040 ✔ |
| Bethlehem 2539 | 4.91 → 4.88 | 4.914 → 4.857 ✔ |
| Saranac 54574 | 0.12 → 0.14 | 0.123 → 0.144 ✔ |
| Sithe 54547 `CC_CHP` | 4.23 → 4.29 | 4.235 → 4.288 ✔ |
| **Linden 50006 `CC_CHP`** | **6.33 → 5.31** | **6.325 → 6.549 ✘** |

Sithe 54547 is the control that closes it: it is `CC_CHP` too, but its **measured** BTM share is
**0.0 %** (`chp_btm_share_measured_NYISO.csv`, grid share 1.003), so it carries no add-back and it
reproduces. Linden carries a 1.25 TWh/yr add-back and it does not.

### 2.3 Provenance of the mis-stated cell — the committed screen record names it

`_nyiso196_screen_gates.json` → `gates.S3_direction.moved_plants[1]`:

```
{"plant": 50006, "group": "CC_CHP",
 "keeper_gwh": 6196.9,      <- the PRIOR keeper's PAYLOAD (LP + 1,249.4 GWh add-back)
 "screen_gwh": 5235.5,      <- the SCREEN bundle's LP grid series (no add-back)
 "meter_gwh": 7344.1,       <- CAMPD GROSS full plant
 "avail_off_mean": 0.855, "avail_on_mean": 0.8956,   <- availability ROSE
 "moved_toward_meter": false}
```

`5235.5 GWh` is the 2024 "arm" figure printed as **5.24** in §4.2. The row is internally
self-refuting: an **availability increase** producing a **15 % energy fall** at a plant that is
online 8,760/8,760 hours has no mechanism, and that is the fingerprint. (2023 and 2025 are the
same construction — payload minus the plant's own add-back gives 5.30 / 5.11 against the doc's
5.31 / 5.21 — but their exact source is the full-span bundle's `dispatch/`, which is
gitignored-absent, so those two are attributed by construction rather than reproduced.)

## 3. Step 1b — what the real Linden gap is: the comparand ladder

Four published quantities for the same station-year (2024; `_nyiso197_linden_phase0.json` L-2):

| quantity | 2023 | 2024 | 2025 | source |
|---|---|---|---|---|
| CAMPD **gross** hourly (the §4.2 "meter") | 7.231 | 7.344 | 7.438 | `campd-unit-level/NJ_<yr>`, 6 CEMS units |
| EIA-923 **net** generation | 5.644 | 5.626 | 5.740 | `eia923_monthly_generation`, BA = NYIS |
| measured CHP BTM hold-out (22.21 %) | 1.254 | 1.249 | 1.275 | `chp_btm_share_measured_NYISO.csv` |
| **NYISO Gold Book net energy** | **4.391** | **4.289** | n/p | Table III-2a, Linden Cogen PTID 23786 |
| model **payload** (full plant) | 6.549 | 6.440 | 6.390 | keeper payload |
| model **LP grid** dispatch | 5.296 | 5.191 | 5.115 | payload − its own flat add-back |

* **The §4.2 meter is not usable for this plant.** The CAMPD gross series peaks at **1,272 /
  1,179 / 1,188 MW** — 131 % of EIA-860 nameplate (974.1 MW), **34 % / 27 % / 28 % above NYISO's
  own registered *winter* station capability (924.9 MW)** and 49 % above its summer capability
  (790.8 MW). The repo's own parasitic derive already rejects the reconciliation: 
  `parasitic_load_factors.parquet` flags plant 50006 **`out_of_band` in every year** (measured
  net/gross 0.743) and substitutes the 0.97 class default. A model reproducing NYISO's metered
  energy will therefore *always* read ≈ −2 TWh against that series; the "gap" is a comparand
  artifact, not a dispatch error. The CEMS series is internally consistent on its own terms
  (implied gross heat rate 6,966 Btu/kWh, CO2 0.376 t/MWh gross) — the contradiction is between
  CEMS's level and the NYISO/EIA registries, and this session does not adjudicate which is right.
* **On the market meter the sign flips.** Model LP grid vs Gold Book net energy:
  **+904.9 GWh (+20.6 %) in 2023**, **+901.8 GWh (+21.0 %) in 2024** — and the extract-basis
  repair *increased* it (prior keeper +680.9 / +658.8). Linden is also the largest single
  contributor to the `CC_CHP` class's 923 over-run (model 6.440 vs 923 5.626 = **+0.814 TWh**,
  **35 %** of the class cell's +2.327 TWh in 2024).
* **The bucket split says the same thing.** Against the CAMPD gross series the entire gap is
  bucket (b−) loading deficit — 863 / 966 / 1,124 GWh, with buckets (a) and (c) at 0.0 and the
  plant online 8,760/8,760 hours — flat across all 24 hours of the day (28–52 GWh per hour bucket)
  and rising monotonically with the NYC price quartile (2024: 90 / 210 / 289 / 377 GWh). That is a
  **level** difference between two meters, not a dispatch shape.

## 4. Step 2 — the four candidate measured objects, adjudicated

Rebuilds: `scripts/lib/bundle_fleet.reconstruct_bundle_fleet` on the keeper's committed
`meta.json`, 2023 and 2024 (`_nyiso197_linden_rebuild_<yr>.json`).

**(a) Availability — NOT contradicted; and the plant is not capacity-bound.** The extract's
Linden rows are `observed_peak`-based (`plant_capacity_mw` 1,240–1,275 MW; `unit_pct_of_plant`
≈ 15 % × 5 + ≈ 25 %). The keeper's `unit_outage_extract_basis_share` takes the removed fraction
on that same basis, which is the internally consistent construction — a *share*, so the CEMS
level cancels; the prior keeper divided an observed-peak MW by the 974 MW fleet bin and
over-removed. LP availability mean 0.852. More decisively, the LP sits at its envelope in only
**896 / 586 hours** (10 % / 7 %) and leaves **415.8 / 466.7 GWh** of headroom unused below it:
Linden is **price-following, not capacity-bound**, so no availability change can be the object.

**(b) Capacity / BTM hold-out / CHP duty — already on the accurate basis.** LP `pmax` totals
**757.76 MW** across 8 tranches (committed 118.87 + 6 × econ 96.74 + peak 58.45) = nameplate
974.1 × (1 − 22.21 %). NYISO's own registered **net** capability is 737.1 (2024 ed.) / 748.2
(2025 ed.) MW summer — the model is within **2.8 % / 1.3 %** of it. The 22.21 % share is itself
the Gold-Book ÷ 923 measurement. `chp_layup_duty_curve` is armed but its census **deliberately
abstains** at Linden (median gross load is non-zero in every 4-hour block), so the mechanism does
not reach the plant and inventing a duty curve for it would be fitting. **No object.**

**(c) The Linden VFT / import seam — refuted.** NYISO's Gold Book carries Linden Cogen as an
**internal NYCA Zone-J station** (PTID 23786, billing organization East Coast Power LLC), not as
an import; `SCH - PJM_VFT` is a separate merchant tie in the seam envelope. There is no double
count and no cap to contradict — and nyiso-196's own I-1 check already measured **0 of 8,760
hours** in which the LP's import capability binds below the measured scheduled flow. **No
object.**

**(d) Delivered gas — a real mismatch, but not a screenable object and the wrong direction.**
The keeper's assembled delivered gas for the Linden tranches equals the committed measured NYC
hub monthly (`transco_z6_iroquois_monthly.csv`, Transco Z6 NY) in **11 of 12 months exactly** in
both years (the twelfth is the dual-fuel/daily cap). Physically the plant is in **Linden, New
Jersey (Union County), on Transcontinental Gas Pipeline Zone 6 NON-NY** (EIA-860 pipeline field),
not the NYC citygate. This is a genuine unrepaired basis mismatch, but: **no Z6 non-NY series is
committed in this repository**, so there is no zero-DOF input to swap — it is a data-intake ask,
not a screen — and the direction is wrong: Z6 non-NY is *cheaper* than Z6 NY (materially so only
in winter), which would make Linden's offer cheaper and the +21 % over-run **larger**. It joins
the owner court's standing NYC delivered-gas intake item.

**What the over-run actually is, stated without a lever.** In the hours below its envelope the
NYC LMP clears Linden's **cheapest** tranche 99.8 % / 98.7 % of the time and its **peak** band
only 9.7 % / 9.2 %: the committed band's assembled `mc_base` averages **$23.36 / $27.19** against
a modelled NYC LMP mean of **$36.62 / $39.99**. The plant is a near-price-taker in the model's
Zone-J merit order and runs at **79.8 % / 78.2 %** capacity factor where the market ran the
station at **68.0 % / 65.4 %**. This is an **offer-position / merit-order** object in `CC_CHP` —
a class whose offer curve has never been the subject of a NYISO lane. *(Observation, coverage
stated, not a finding: on the partial committed zonal RT series — 1,464 / 4,344 / 744 hours —
the model's NYC zonal price runs +16.5 % / +11.7 % / +16.6 % above the measured N.Y.C. LBMP over
the overlapping hours. Too thin to conclude from; system-wide C3a is +4.6 / +4.7 / −6.9 %.)*

## 5. Step 3 / 4 — no PREREG, no screen, no solve

Step 3 of the brief is conditional on step 2 naming a measured object. **None survives**, so
under the brief's step 4 nothing was pre-registered and **no LP was run** — the session's result
is this document. Naming a `CC_CHP` offer-band multiplier as the "one object" would be exactly
the residual-driven selection rule 1 `[R-STRUCT]` condition (c) forbids (the band multipliers are
an authorized channel only when set ex ante on a non-residual ground and never swept against the
gates), and the brief's DO-NOT-REDO list already closes the `cc_capacity_reconcile` `CC_CHP`
scope (nyiso-191, rule 19) that the capacity ladder would otherwise point at.

## 5b. Reconstruction fidelity (the rebuilds' own G-DRIFT note)

The two `fleet_only` rebuilds ran at HEAD `af6269cf` against a keeper solved at `f7bb76a5`, and
that span carries live solve-path hunks (`data/fleet/eia860.py`, `cod_ramp.py`,
`zone_assignment.py`, new `scenarios.py` fields), so the reconstruction is **not** asserted to be
byte-faithful to the keeper's solve. It does not have to be, for two reasons:

* **§2 and §3 — the refutation and the comparand ladder — use no rebuild output at all.** They are
  read from the two committed payloads, the shared bench part, the committed outage extract, the
  raw CAMPD/EIA-860/EIA-923 series and the Gold Book editions.
* **The three quantities §4 does read back are either definitional or reproduce a committed
  record:** LP `pmax` 757.76 MW is exactly `974.1 × (1 − 0.2221)`, the nameplate-times-hold-out
  identity; the assembled delivered gas equals the committed measured NYC hub monthly in 11 of 12
  months in both years; and the rebuilt availability is consistent with the keeper's own committed
  `_nyiso196_extract_basis_census.json`. A drifted rebuild would break all three.

## 6. Governance

* **Rule 29 `[R-SCREEN]`:** phase 0 only. Zero LP; control = the keeper's committed bundle
  (form 4). No screen bundle was created, so nothing is retained or pruned (clause (c) moot).
* **Rule 13 / 14:** every quantity is a committed measured artifact; nothing is fitted, no
  residual enters any construction, and no input was changed. The one *proposed* repair (d) is
  refused for want of a committed series, not accepted on the residual.
* **Rule 15 `[R-DASHBOARD]`:** no run was produced, so nothing registers. The keeper's
  determination, bundle, sidecar and payload are untouched.
* **Rule 16 / 22:** no solve, 2023–2025 only, no holdout year touched, no marker requested;
  `calibration-complete.json` untouched (NYISO stays in the `withdrawn` block).
* **Rule 21 / 23 / 24:** no parameter, no derive re-run, no registry field added.
* **Rule 28 `[R-MECH-MATRIX]`:** no mechanism was tested, so no cell verdict changes; §5.5's
  queue text and the NYISO shard's keeper note are corrected for the void object (§7).
* **Rule 27 `[R-PUSH]`:** the two probes are new files; the record corrections are local `Edit`s
  pushed as on-disk bytes.

## 7. Record corrections made in this session

The void object is quoted in three committed places and would send the next session after a
phantom. Each is **annotated, not rewritten** — the original text stands and carries a pointer:

1. `docs/FINDING-nyiso196-cc-outage-share-basis-2026-09-05.md` — §4.2 regression (i) and §6
   item 1 carry a correction note. **Nothing else in that document changes**: the repair, its
   screen, the determination and every other row of §4.2 are unaffected, and the promotion
   stands on its own merits (the Linden row was a reported plant-grain regression, never a gate).
2. `docs/mechanism-testing-matrix.md` §5.5 — the 2026-09-06 queue-status block's "NEW TOP OF
   QUEUE (U) — Linden 50006 `CC_CHP` placement" item is superseded by a nyiso-197 block.
3. `docs/calibration-log/nyiso.md` — a nyiso-197 entry.

## 8. Handed forward (owner court)

1. **The Linden cell, RE-SPECIFIED.** Not "−1.0 TWh under a 7.3 TWh meter" but: *the model
   delivers +0.90 TWh/yr (+21 %) MORE from Linden Cogen into Zone J than NYISO's Gold Book says
   the station delivered, at a merit position where its committed band clears the modelled NYC
   LMP in 99 % of hours.* It is `CC_CHP`'s largest single contribution to that class's 923
   over-run (+0.814 of +2.327 TWh in 2024). Any lever here is an **offer-position** lever on
   `CC_CHP`, which under rule 1's carve-out conditions (a)–(e) needs an **owner ruling and an
   ex-ante, non-residual ground** before it can be pre-registered — this session does not
   propose a value.
2. **The plant-grain comparand for CHP plants with a measured BTM hold-out.** The run-page
   plant table compares a *923-net-basis* model reconstruction to a *CEMS-gross* meter; at
   Linden those two differ by 1.7 TWh/yr and the CEMS level exceeds NYISO's registered station
   capability by 27–34 %. A scorer-side card: either render the Gold-Book/923 comparand for
   plants the parasitic derive flags `out_of_band`, or label the row. **No LP consequence** —
   the shares CAMPD feeds the LP are scale-invariant — so this is a diagnostic-honesty item,
   not a calibration one.
3. **Delivered gas for the New Jersey Zone-J plants** — Transco Z6 **non-NY** for Linden 50006
   (and any other NJ-sited NYISO resource), against the Z6 NY citygate the model charges today.
   Needs a committed series; folds into the standing NYC steam delivered-gas intake spec.
4. **A guard for the add-back basis.** The mismatch that produced the void object is mechanical
   and repeatable: any probe that compares an *arm's LP series* to a *keeper's payload* will
   fabricate a regression at exactly the plants carrying a CHP add-back. `nyiso-192` already
   filed the mirror defect (`_nyiso192_payload_addback_audit.json`, the 35 % sector default added
   on top of a measured-share LP). Worth one assertion in the screen-gate probe pattern: both
   sides of a plant-grain comparison must declare their basis.
5. Owner court, unchanged: the `complete` re-entry declaration on this keeper; the D-2 unit-grain
   scorer card; the AORR fetch; the Q45 footing. Cricket Valley 57185's part-load bucket (b−)
   remains the queue's other open item and is **untouched by this session**.

*(nyiso-197, 2026-09-06. ZERO solves. Keeper unchanged: `2026-09-06-nyiso-196-extract-basis`.)*
