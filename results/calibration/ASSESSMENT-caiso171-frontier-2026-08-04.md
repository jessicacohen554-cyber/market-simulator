# ASSESSMENT — CAISO frontier and `complete`-declaration readiness (caiso-171)

**Date:** 2026-08-04 · **Session:** caiso-171 · **Keeper under assessment:**
`2026-08-04-caiso-166-measured-dlap` (bundle `results/calibration/caiso166_measured_loss_zones`)

**NO LP, NO SOLVE, NO DERIVE, no `ScenarioConfig` field, no run registered, keeper
unchanged.** One network call: the caiso-141 wall probe, which is a network probe by
design. Nothing in `calibration-complete.json` is touched — the marker is an owner act
(rule 22). No out-of-training year was solved, scored or read.

Instrument: `scripts/probes/caiso171_frontier_assessment.py` (committed artifacts only,
re-runs in seconds); record `results/calibration/_caiso171_frontier_assessment.json`.

---

## 0. Recommendation, up front

**YES — CAISO is ready for the `complete` marker.**

> **CORRECTED 2026-08-04, same session, on the owner's restatement of the criterion.**
> This section first read **NO**, on the ground that the active holdout spend freeze made
> the grant hollow. **That ground is wrong and the record refutes it.** `complete` means
> exactly two things — (a) the **2022 touchpoint is allowed**, and (b) **frontier: we have
> tested everything we could have.** It is not a certificate that the DOF ledger is clean
> or that no root-cause issue is open. Measured against the criterion as stated, CAISO
> passes on both limbs. §§1–4 below are unchanged — every measurement stands; only the
> recommendation they were weighed against changes.

**The freeze is not a bar on the marker, and the record settles it.** The freeze was
declared **2026-07-25**. **NYISO and PJM were both declared `complete` on 2026-07-31** —
six days *into* the active freeze. `holdout-freeze.json` says so in its own words: a
freeze is "a **SUSPENSION of the authorization** that a calibration-complete marker
grants, **not a withdrawal of the marker itself**," and it is "deliberately ADDITIVE and
backward-compatible: `calibration-complete.json` is untouched." The two instruments are
orthogonal — the marker records *what the calibration has reached*, the freeze
independently gates *when any ISO may spend* an out-of-training year. Declaring CAISO now
and lifting the freeze later is the same sequence NYISO and PJM already ran.

**Limb (a) — the 2022 touchpoint.** That is the whole of what the `complete` block grants,
and it is what CAISO would be authorized to do once the freeze lifts. Nothing about
CAISO's state argues against granting it.

**Limb (b) — frontier: everything testable has been tested.** This is the substantive
question and CAISO meets it, on measurement rather than assertion:

- **All nine enumerated §5.2 queue items are closed**, each against a real evidence
  document — **16 of 16 verified present** (§1.1). Nothing is struck untried. Items 1, 4
  and 5 were closed with **no solve spent**, which is a stronger outcome than a spent
  rejection.
- **The matrix column census is clean** — `0 / 0 / 0 / 0 / 0` across 63 family fields.
- **The two remaining live `U` cells are closed on CAISO's own data** this session:
  `pumped_storage_cycling_depth` on all three legs (duration data-walled, adder
  wrong-signed and rule-13-refused, RTE a cross-ISO constant), and
  `cc_steam_part_capacity` bounded at **20.0 MW ≈ 0.04 %** of fleet (§1.2). The rest of
  the `U` column is forecast-lane rows, shared-census rows, or rule-barred cells.
- **All three standing walls re-verified and all three hold** (§2), including a live
  5/5-unchanged re-run of the caiso-141 survey. Arm B's wall is *stronger* than "nothing
  on disk": the published limit is **already armed per-year** and does not bind, so any
  tighter one would have to be invented.

That is the definition of having tested everything reachable. **CAISO is at its frontier.**

**What the declaration should carry as caveats — recorded, not blocking.** These are not
`complete` criteria and none of them argues against the marker; they exist so the marker
does not assert more than the evidence:

1. **The C3a caveat widened at the last promotion** — `price_mean` now covers **two**
   years, 2024 having been owner-ledgered 2026-08-04 at +9.5 % → +11.5 %, with 2025 at
   +14.4 % against the ledger text's +10.9 % (§2.1).
2. **Two open root-cause issues stay named** — the N–S congestion majority (model
   reproduces 4.0/1.5/1.9 % of the measured basis) and the caiso-170 within-day storage
   placement pointer (§4).
3. **The DOF ledger is the honest weak spot** — 4 ISO-specific residual entries, the most
   of any ISO measured (NEISO 0, PJM 1, NYISO 2). Two are superseded on the keeper's
   binding path; one rests on a closure route that does not check out (§3.4). NYISO holds
   the marker with an unledgered criterion **FAIL**, so this is not disqualifying — but it
   is where CAISO's next non-lever work lives.

§5 lists what remains as follow-on work, none of it a precondition.

---

## 1. Every queue item closed, with the evidence that closed it

Walked `docs/mechanism-testing-matrix.md` §5.2 items 1–9 and the CAISO column of
`docs/codebase-site/data/mechanism-matrix.js` row by row.

### 1.1 The enumerated §5.2 queue

| # | Item | Verdict | Evidence file (all verified present) | What measurement closed it |
|---|---|---|---|---|
| 1 | `energy_reserve_coopt` + completing `caiso_reserve_coopt` | **I** — discharged ex ante, no LP | `FINDING-caiso144-…-2026-07-30.md` (201 ln) | Family-level reserve slack strictly positive in all 26,280 h; in reality's own RT>$200 hours the pool is slack by **+1,568 / +1,632 MW min, +10,246 / +10,486 mean**. A design provably inert at every optimum. |
| 2 | Corridor / export-path congestion family | **CLOSED**, both halves, no solve | `FINDING-caiso167-…-2026-08-04.md` (312 ln); export at caiso-142/143 | Surplus-regime basis measured for the first time: real `SP15−PALOVRDE` **−1.167/−3.824/−1.825** vs model **+7.077/+9.569/+7.100**; model wedge `<0` in **0.000 %** of 26,280 corridor-hours. Seam loss surface refused on measured reach (**1.6/0.1/1.4 %** of the defect, stress-`eps` 0.13 → 19.3–39.5 %). |
| 3 | S2 DA/RT two-settlement charter | **R** (caiso-170) + substitute **G** (caiso-169) | `FINDING-caiso170-…` (410 ln), `FINDING-caiso169-…` (362 ln) | Model beats the **measured** fleet on within-day capture by **−0.014/+0.019/+0.007** against a pre-registered ≥0.10 — **0 of 3**. Measured fleet already at **0.922/0.917/0.907** of its own perfect-foresight ceiling. Separation is real (Spearman **0.813**) — a refutation, not a null. |
| 4 | `tranche_startup_amortization` | **G** — refused ex ante, no solve | `FINDING-caiso149-…-2026-07-31.md` (266 ln) | CAISO has no fast-start pricing (BCR uplift outside the LMP, DMM sourced twice, 2017 + 2025); **92.9 %** of the 7,808 MW targeted already carries an identified margin at **2.19–7.86×** the candidate's own $3.85/MWh. |
| 5 | `unit_outage_short_windows` for CAISO | **I** — nothing to derive | `FINDING-caiso136-…-2026-07-28.md` (140 ln) | Detector is coal-only; CAISO coal is **2 units / 50.0 MW** at one facility **absent from CAMPD entirely**. Both derives return 0 windows — no input series exists. |
| 6 | `measured_ct_heat_rates` | **K** — promoted | `FINDING-caiso146-…-2026-07-31.md` (266 ln) | 43 plant rows, **99.9 %** of the class's metered CAMPD CT energy; cap-wt **−1.159 MMBtu/MWh (−10.7 %)**. Zero fitted parameters. |
| 7 | `measured_chp_heat_rates` | **K** — promoted | `FINDING-caiso147-…-2026-07-31.md` (392 ln) | 30 rows / 2,371.8 MW, CC_CHP at **100.0 %** of class metered energy, CEMS validation **13/13** at median 1.00000. Derive defect found and fixed pre-solve (59 of 65 rows were excluded by the hand factor alone). |
| 8 | `nuclear_unit_availability` | **K** — promoted | `FINDING-caiso148-…-2026-07-31.md` (391 ln) | 1,886 NRC daily rows = Diablo Canyon 1+2 = **100 %** of CAISO nuclear; overlay binds 4,368/3,672/2,232 h, energy-neutral ≤0.045 %; nuclear `r_day` 0.787/0.847/0.855 → **0.971/0.992/0.988**. |
| 9 | Re-identify the offer-surface gas-coupling classifier | **CLEARED** at caiso-153 | `FINDING-caiso153-…-2026-08-02.md` (246 ln) | Defect was the **estimator**, not the body probe: OLS→Theil-Sen drops the physically-impossible population 32 res/10,880 MW → 13/2,692 MW; G1 CT_PEAKER **0.235 FAIL → 1.306 PASS**, `hr_cut` unmoved (rule 23). |

**All 16 cited evidence documents verified present on disk** (140–410 lines each). **No
item is struck untried.** Every closure is a measured refusal or a promotion; items 1, 4
and 5 were closed with **no solve spent**, which is a stronger outcome than a spent
rejection, not a weaker one.

### 1.2 Cells whose closure rests on assertion rather than a number — FLAGGED

The matrix column census is clean (`mechanism_matrix_gap_sweep.py --iso CAISO` →
**0 / 0 / 0 / 0 / 0**, 63 family fields), and the CAISO column reads 59 `K` · 19 `U` ·
13 `I` · 6 `R` · 5 `G` · 4 `O`. Three flags:

**FLAG 1 — a stale premise number carried forward as current.** `FINDING-caiso165`
records `LA_BASIN − SP15_rest` separating in **0.00 % of belly hours in all three years
(0 of 8,760)** — "a hard copper-plate on exactly the corridor caiso-164 named." That was
measured on the **caiso-164** keeper and is **stale for caiso-166**, which arms the
measured loss zones. Re-measured on the current keeper (probe F4):

| year | `LA_BASIN−SP15_rest` sep % | mean | ratio sd | what it is |
|---|---:|---:|---:|---|
| 2023 | 0.00 % | +0.000 | 0.00000 | unseparated |
| 2024 | **100.00 %** | +0.582 | **0.00382** | proportional **loss** wedge |
| 2025 | **100.00 %** | +0.665 | **0.00261** | proportional **loss** wedge |

The conclusion **survives** — a separation whose `(p_a−p_b)/p_b` ratio has sd < 0.004 is
a constant ~2.6 % loss wedge, not congestion, so the corridor still never binds — but the
headline number no longer means what it says. **Do not re-quote "0.00 % separation" for
the caiso-166 keeper.** The SDGE limb is not a loss wedge (ratio sd 161.4 / 16.7) and
remains **inverted**: model **−2.090 / −4.761** against measured **+4.038 / +6.451**.

**FLAG 2 — `pumped_storage_cycling_depth` CAISO `U`, with the note carrying CAISO's
closure implicitly.** The row is adjudicated at PJM (`G`, the $10 adder retired as
rule-13 fitted) and NEISO (`G`, premise inverts), with "CAISO/MISO/NYISO untested — do
not transfer either verdict (rule 25)." Measured here, all three legs are closed for
CAISO on its own data without a transfer: the **duration** leg is data-walled — EIA-860's
generator table carries **no energy (MWh) column** and PS is **absent from the
energy-storage table** (technologies are Batteries / Flywheels / CAES / Solar Thermal;
prime movers BA, CE, CP, FW), so the shipped `PUMPED_STORAGE_DURATION_HOURS = 10.0` is a
DOE **national fleet-average** with no published CAISO-specific replacement on disk; the
**adder** leg is wrong-signed for the defect and rule-13-refused at PJM; the **RTE** leg
is a cross-ISO constant rule 25 forbids fitting on one ISO's residual. This is now a
measured closure rather than an untested cell — recorded, cell left `U` because no
mechanism was tested.

**FLAG 3 — `cc_steam_part_capacity` CAISO `U`, bounded and immaterial.** The national
census names CAISO **54912** as a qualifying row. Measured in EIA-860: *Martinez
Refining* STG1, prime mover **CA**, Energy Source 1 **OG**, Unit Code **CC1**, siblings
GTG1/GTG2 (CT, NG, 40 MW each) — it matches the miso-125 predicate exactly, and its
capacity is **20.0 MW**. That bounds the whole lever at 20 MW on a ~50 GW fleet
(≈ **0.04 %**), immaterial under any gate. Untested, but it cannot matter. Cell left `U`.

The remaining `U` cells are forecast-lane rows (`economic_retirement_screen`,
`entry_dampers`), rows added by the nyiso-115 **shared-field census** rather than by a
CAISO lever proposal (`coal_drop_pof`, `gas_st_startup_spread`, `cc_duct_peaking`,
`cc_nameplate_summer_derate`, `cc_capacity_reconcile_path`), or rows explicitly barred
elsewhere (`td_loss_factor` — rule 19, must not stack on the armed loss surface).

---

## 2. Every residual attributed to a walled measured input — walls re-verified

### Wall 1 — C3a-2025 (and now 2024): non-public hourly pumped storage. **HOLDS.**

Re-ran `scripts/probes/_caiso141_water_source_survey.py` against the **live** public
endpoints this session. **All five checks return `unchanged`:**

| check | result 2026-08-04 | verdict |
|---|---|---|
| S1 EIA-930 `PS` fuel category | API carries `PS`; **CISO PS rows = 0** | WALL |
| S2 CAISO Today's Outlook fuel mix | hydro minima **910 / −414 / 1033 MW**; vs 930 WAT n=72 **corr 0.950**, mean abs diff **287 MW** | same PS-NET feed — WALL |
| S3 Outlook `storage.csv` | columns: Total / Stand-alone / Hybrid **batteries** only | WALL |
| S4 CDEC hourly telemetry | **CTG 0, WSN 0, SHV 0** hourly sensors (Helms 1,053 MW + Eastwood 199.8 MW = **60.3 %** of the fleet) | WALL |
| S5 EIA-930 sub-BA route | data columns `['value']`, facets `['parent','subba']` — demand-only | WALL |

No source has appeared. The wall stands exactly as caiso-141 filed it.

### Wall 2 — Arm B: no published intra-SP15 transfer limit. **HOLDS, and it is stronger than "nothing on disk."**

Censused `data/raw` this session. The only published corridor numbers that exist for the
two intra-SP15 pockets are the **LCT-derived pocket import capabilities**
(`import_cap = peak_load − LCR`, from `data/raw/capacity-deliverability/caiso/caiso.csv`):
LA Basin **12,008 / 15,224 / 15,174 MW** and SDG&E **1,436 / 2,074 / 2,071 MW** for
2023/24/25.

**Those numbers are already armed, per-year** — `caiso_per_year_import_caps = True` in the
keeper's `run_config.json` (caiso-162's recommendation was carried in). So the wall is not
"no published number exists." It is: **the published number is armed at its published
value and the corridor does not bind there** (§1.2 FLAG 1). Any limit tight enough to
reproduce the measured congestion would have to be *invented*, and caiso-165 measured
those targets precisely (belly separation **89.31 / 98.05 / 94.23 / 99.69 %**, mean
`|dMCC|` **1.038 / 1.999 / 4.038 / 6.451**). Knowing them precisely makes the
outcome-pin prohibition bind **harder** (rule 13 `[R-MEASURED]`, rules 5/21/24). The
`capacity-deliverability` README is explicit that MIC is "a *seam* import limit, **not an
internal-LDA transfer**", and no path rating or ATC construction for an intra-SP15
corridor is on disk. **FILED, not approximated.**

### Wall 3 — C3c 2023/24: the SoCalGas OFO declaration record. **HOLDS.**

Searched `data/raw` for any OFO / operational-flow-order / SoCalGas envoy artifact. The
**only** hit is `data/raw/gas-prices/pge_socal_citygate_weekly.csv` — a **price** series,
not a declaration record. Nothing on disk carries OFO event windows. Unchanged since
caiso-144 re-verified it.

**All three walls hold. No intake has landed that would make any of them the lane
instead.**

### 2.1 One qualifier the declaration must carry: the C3a caveat widened at the last promotion

The ledger still spends **2 of 3** non-protective slots (slots are per criterion), but the
C3a criterion now carries **two years**, not one. `price_mean` **2024** was ledgered
**2026-08-04** by the owner (`AMENDMENT-caiso166-S3-recharter-2026-08-04.md` §4) when the
caiso-166 loss arm moved it **+9.5 % (PASS) → +11.5 %**; 2025 stands at **+14.4 %**
against the **+10.9 %** the caiso-145 ledger text describes.

The grounds are sound and measured — losses consume MWh so the direction is physically
obligatory; the control already sat 0.5 pp inside the band; against CAISO's **own DA
basis** (the basis the surface is derived on) the arm sits **+1.8 % / +11.3 %** with a
DA−RT premium of **+$3.30 / +$0.98**; no compensating adder was added. It is a correct
rule-14 outcome. But the honest frontier statement is that **the C3a residual's coverage
widened at the most recent promotion rather than narrowing**, and a declaration should say
so rather than inherit the single-year framing.

---

## 3. The DOF ledger

`n_entries = 11`, **`n_residual = 9`** — re-read off the keeper's own
`calibration_attestation.json`, confirming the 11/9 the matrix carries. Nine of eleven
free parameters are identification `residual`, not identified from data.

Taken bare that reads alarming, so it is measured against the ISOs that already hold the
marker. Five residual entries are **shared machinery every ISO carries**
(`offer_curve_by_group`, `offer_curve_committed_below_floor`, `offer_curve_smoothing`,
`COAL_SIGMOID_DEFAULTS`, `wefor_multiplier`) and are not a CAISO property. The comparable
statistic is the **ISO-specific remainder** (probe F2):

| ISO | entries | residual | core | **ISO-specific** | `complete` marker |
|---|---:|---:|---:|---:|---|
| **CAISO** | 11 | 9 | 5 | **4** | **no** |
| PJM | 19 | 6 | 5 | 1 | yes |
| NYISO | 33 | 6 | 4 | 2 | yes |
| NEISO | 12 | 5 | 5 | **0** | yes (locked test SPENT) |
| MISO | 27 | 2 | 2 | 0 | no |

**CAISO carries the most ISO-specific residual DOF of any ISO measured.** The four, each
inspected:

1. **`WECC_import_simultaneous.cap_mw = 7500.0`** — *not a backcast defect.* Superseded in
   the caiso-51 keeper by the published branch-group MIC sum (**16,055 / 16,452 / 16,148
   MW**, which is on disk and curated) and re-verified by measurement at caiso-157:
   binding in **0 / 0 / 0 hours**. The residual survives only as a **forecast-mode parity**
   item (the fitted 7,500 still caps forecast imports; issue #1373).
2. **`IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`** — *largely superseded on the binding path.*
   The keeper prices the binding seam off **measured hub prices**; the fitted year-keyed
   ladder survives as the fallback. Named replacement exists (the NEISO derive precedent,
   `derive_neiso_import_tranches.py`); issue #1350.
3. **`battery_dispatch_adder = 5.0`** — live and genuinely calibrated. Inside the
   literature range (NREL ATB 2024 ~$15–25/MWh; Xu et al. 2018 $25–50/MWh) but the
   specific value is not identified. Named forward-valid replacement: measured AS power
   reservation (`storage_as_commitment`) + ATB-derived degradation cost.
4. **`CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'] = {NP15: 0.86, ZP26: 0.14}`** — **the one that
   matters, and its stated closure route does not check out.** This splits PG&E TAC load
   across **Path 15** — i.e. it sets how much load sits on each side of the exact
   boundary carrying §4's largest open defect — on a "prior ratio of unverified
   provenance." Its `root_cause` says to "refine when NP15/ZP26 zonal load lands via the
   OASIS fetch workflow (OASIS confirmed reachable 2026-07-07)." **Verified this session:
   the wired `load` dataset in `fetch_caiso_oasis.py` is `SLD_FCST` at TAC-area grain, and
   the committed series `CAISO_tac_load_hourly_<year>.csv` carries exactly
   `['CA ISO-TAC','PGE-TAC','SCE-TAC','SDGE-TAC','VEA-TAC']`.** NP15/ZP26 is a **sub-TAC**
   boundary. No NP15/ZP26 load series exists on disk, and whether OASIS publishes a
   sub-TAC load report at all is **UNVERIFIED**. This is a **fourth open data question**
   filed here, not an available lever — and it is a `[R-DOF]` closure lane, not a
   residual-fitted one.

**Verdict on §3:** the ledger is **not clean**, and CAISO's ISO-specific residual count is
the highest measured. It is not disqualifying — NYISO holds the marker at 2 with an
unledgered criterion FAIL, and two of CAISO's four are superseded on the binding path —
but it is the substantive gap between CAISO and the ISOs it would be joining.

---

## 4. Open root-cause issues being carried — NAMED, not buried

A frontier declaration must state these. Neither is closed and neither is ledgered.

### KNOWN-OPEN 1 — the N–S congestion majority (caiso-163 / caiso-164)

Re-measured on the **current** keeper (probe F3; annual means, clock-invariant, so the
`FINDING-caiso168` Feb-29/UTC alignment defect cannot touch it):

| year | measured `NP15−ZP26` | `dMCC` | `dMCL` | congestion share | **model** | model / measured |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | +5.947 | +4.771 | +1.176 | **80.2 %** | +0.236 | **4.0 %** |
| 2024 | +8.576 | +7.475 | +1.102 | **87.2 %** | +0.127 | **1.5 %** |
| 2025 | +5.727 | +4.677 | +1.049 | **81.7 %** | +0.109 | **1.9 %** |

The model reproduces **1.5–4.0 %** of CAISO's measured north–south basis. caiso-164's
loss surface fixed the **sign** (it was −0.077/−0.109/−0.084 before) and correctly
represented the **loss minority** (12.8–19.8 %); the **congestion majority — 80–87 % of a
$5.7–8.6/MWh basis — is unrepresented.** caiso-163 named its successor hypothesis (the
reduced two-link N–S topology and zonal aggregation) and explicitly did **not** adjudicate
it. It remains open, un-chartered, and correctly so: caiso-164 §6 files it as a data
blocker and forbids chartering an N–S topology lever against it.

### KNOWN-OPEN 2 — the within-day storage placement pointer (caiso-170)

caiso-170 refused S2 and **re-pointed, explicitly as a pointer and not a verdict**, to a
within-day **placement** object: on the same annual energy the model over-charges the
belly (**+359 / +179 / +262 MW/h**), under-charges overnight (**−167 / −159 / −149**) and
over-discharges the evening (**+130 / +678 / +902**). It is **not a bound** — in the
2,920/2,555/2,190 overnight hours where `caiso_storage_shape_anchor` is live the model
charges **23.3 / 40.8 / 21.8 MW** against a bound of **632 / 803 / 833 MW**. The untested
pointer is the **aggregated battery representation**, which caiso-170 explicitly declined
to claim. **Untested.**

Carry the caiso-170 framing correction with it: on a like-for-like battery basis the
"overnight over-position" **reverses sign in 2024 and 2025** (model **under** by
−227 / −306 MW/h). No successor may scope itself to "remove overnight discharge."

### Also carried, not open lanes

The **SDGE limb inversion** (§1.2 FLAG 1: model −2.090/−4.761 vs measured +4.038/+6.451,
a combined error of roughly $6.1/$11.2 per MWh) and the **C3a two-year widening** (§2.1).

---

## 5. Follow-on work — none of it a precondition for the marker

*(This section previously listed preconditions for flipping the answer to YES. With the
criterion restated — §0 — the answer is already YES and none of these blocks it. They are
the CAISO lane's next work, ordered by value.)*

1. **The freeze still gates the *exercise*.** The marker authorizes the 2022 touchpoint;
   the freeze independently suspends every ISO's ability to spend it. CAISO cannot solve
   2022 until the owner lifts the freeze on the
   `campd-economic-layup-fix-charter-2026-07.md` verdict — exactly as is true today for
   NYISO, PJM and NEISO, all of which hold markers under the same freeze. **Declaring is
   not blocked by it; spending is.**
2. **When the freeze lifts, re-audit the keeper on the corrected availability envelope**
   before spending 2022, per the freeze's own `held` rationale (a residual over-count
   survives the merit-order guard). If the corrected envelope moves the determination,
   rule 22 D-5(b) requires the marker be re-keyed and re-verified against the new run
   anyway — so this is a standing obligation, not a one-off.
3. **The one genuinely high-value no-LP question: does CAISO publish load at sub-TAC
   (NP15/ZP26) grain at all?** This is the gate on discharging
   `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` (§3.4). If **yes**, it is a rule-14
   `[R-ACCURATE]` re-identification sitting on the boundary of KNOWN-OPEN 1 — the highest-
   value CAISO lane available, and a DOF *closure* rather than another fitted parameter.
   If **no**, it becomes CAISO's **fourth wall** and should be filed as one alongside the
   other three.
4. **`battery_dispatch_adder`** has a named forward-valid replacement (measured AS power
   reservation + ATB-derived degradation cost) and is the other live DOF entry.
5. **KNOWN-OPEN 1 and 2 stay named** (§4). Neither is chartered; an N–S topology lever
   against KNOWN-OPEN 1 remains forbidden (caiso-164 §0/§6).

---

## 6. If the answer is YES — what the owner would be authorizing

Stated plainly, because the two marker blocks are independent and one declaration must
never spend both:

- **The `complete` block authorizes the VALIDATION ladder and NOTHING else** — 2022, and
  its backward extension (2020–2022, earlier as data lands and is authorized). It is
  **iterable by design**: a 2022 miss MAY send the lane back to re-tune 2023–2025 and
  re-solve. Because it is iterated against, **a 2022 number is model-SELECTION evidence
  and must never be quoted as a certified out-of-sample skill number.**
- **The locked test (2019, H1-2026) is NOT authorized by it.** That needs the separate
  **`final`** block, which is deliberately empty as of 2026-07-31 ("Neither is final"). An
  ISO in `complete` but not `final` may spend 2022 and nothing else.
- **The holdout freeze still outranks the marker** and is checked first. Until it is
  lifted, a `complete` CAISO may still solve nothing outside 2023–2025.
- **It creates a new standing obligation on every future CAISO session.** Under rule 22
  D-5(b) (owner decision, signed 2026-08-02), once CAISO holds a `complete` entry **every
  subsequent keeper promotion must (a) re-key that entry's `keeper` field to the newly
  designated run and (b) RE-VERIFY its `determination` against that run** with
  `python scripts/calibration_verdict.py --run-id <id>` (committed artifacts only, never a
  re-solve), **in the promotion commit itself**. A re-verified determination that is
  *worse* **stops the promotion and escalates to the owner** — it is never silently
  written. `keeper_at_declaration` preserves the declaration-time basis. This is enforced
  by `scripts/audit_keepers.py` check M1, which the `calibration-keeper-auditor` agent runs
  on every keeper-shard edit. CAISO promotions are currently a two-file act; they would
  become a three-file act with a verification gate.

---

## 7. Verification performed this session

| check | result |
|---|---|
| `calibration_verdict.py --run-id 2026-08-04-caiso-166-measured-dlap` | **CALIBRATED-WITH-CAVEATS**, 0 FAIL, 2 ledgered caveats (C3a, C3c), D-10 free-class C1 12/12 · free 8/8 |
| `audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings (keeper, holdout, marker, status) |
| `calibration-complete.json` blocks | `complete` = NEISO, NYISO, PJM — **CAISO ABSENT**; `final` deliberately empty |
| `holdout-freeze.json` | **`active: true`** — ALL ISOs, BOTH tiers, outranks both blocks |
| `_caiso141_water_source_survey.py` (network) | **5/5 unchanged** — wall holds |
| Arm B / C3c `data/raw` census | no intra-SP15 limit; no OFO record — both walls hold |
| `mechanism_matrix_gap_sweep.py --iso CAISO` | **0 / 0 / 0 / 0 / 0** (63 family fields) |
| `check_registry_payload_parity.py` | OK, 90 runs, 0 unsynced |
| `derive_caiso_loss_surface.py --acceptance` | see §8 / commit checks |
| §5.2 evidence documents | **16 of 16 present** |

**Nothing was registered on the dashboard** — no run was produced.

---

## 8. Files

- This assessment.
- `scripts/probes/caiso171_frontier_assessment.py` — the instrument (no LP, no network).
- `results/calibration/_caiso171_frontier_assessment.json` — its record.
- `docs/mechanism-testing-matrix.md` §5.2 header — assessment + verdict recorded (rule 28 duty b).
- `docs/calibration-log/caiso.md` — appended.
