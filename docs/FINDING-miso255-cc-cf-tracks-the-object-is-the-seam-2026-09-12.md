# FINDING (miso-255): **NO — MISO's CC_REGULAR is not PJM's defect. Its capacity factor TRACKS
# the meter at r = +0.817, and it is one of MISO's BEST-tracking classes, not its worst.**
# The 2021 miss is downstream of a railed seam: the model's net interchange sits on MISO's
# ±8,700 MW Capacity Import Limit in **8,650 of 8,760 hours**, against **0-3 hours** in every
# training year.

**Session** `miso-255` · **ISO** MISO · **Date** 2026-09-12 · **Branch** `claude/miso-255-cc-cf-tracking-83e0m6`
**ZERO LP.** Committed run payloads, committed bench parts, committed `hourly/` sidecars, CAMPD
unit-level, EIA-930 actuals, the model's own fleet loader. **Nothing solved, nothing armed,
nothing registered, no verdict moved.** Keeper `2026-09-09-miso-250-ep-gas` re-verified
**CALIBRATED** (grade 7, one ledgered C3c caveat) after the work.
Premise: `docs/FINDING-pjm-h1-cc-cf-does-not-track-2026-09-12.md`.

---

## 1. RESULT

> **The commissioned question is answered NO, and the discriminating measurement is the one the
> handoff asked for.** PJM's `pjm-h1` found CC_REGULAR to be the ONE class whose matched-fleet
> annual capacity factor does not track the CAMPD meter across 2020-2025 (cross-year
> r = **−0.183**, model CF range 0.015 against the meter's 0.058) while every other fossil class
> tracked at +0.78 to +0.97. **MISO's CC_REGULAR does the opposite of that in every particular.**
>
> | class | model CF range | meter CF range | **cross-year r** | d(model CF)/d(meter CF) |
> |---|---:|---:|---:|---:|
> | **CC_REGULAR** | **0.2621** | **0.1317** | **+0.817** | **+1.362** |
> | CC_CHP | 0.1633 | 0.0746 | +0.941 | +1.936 |
> | COAL_PRB | 0.2090 | 0.1300 | +0.852 | +1.207 |
> | COAL_BIT | 0.2742 | 0.1634 | +0.789 | +1.304 |
> | CT_PEAKER | 0.0464 | 0.0339 | +0.462 | +0.578 |
> | COAL_LIGNITE | 0.1024 | 0.2114 | +0.444 | +0.209 |
> | ST_GAS | 0.1053 | 0.0815 | +0.202 | +0.288 |
>
> MISO's CC_REGULAR is the **third-best-tracking class of seven**. It is not flat — its model CF
> range (0.2621) is **twice the meter's** (0.1317) and its slope is **+1.36**, i.e. the model
> *over*-responds to the year. PJM's signature was a class that would not move; MISO's CC moves
> too much. **The object `pjm-h1` isolated is PJM-specific and does not generalise**, and this
> lane says so rather than importing it (rule 28(d) `[R-MECH-MATRIX]`, rule 25 `[R-ISO-SCOPE]`).
>
> **ALL THREE OF `pjm-h1`'s FALSIFICATIONS RE-MEASURED ON MISO'S OWN DATA, AND ALL THREE HOLD
> HERE TOO** (§3) — same verdicts, MISO numbers, none assumed:
> (a) **capability** — CC_REGULAR revealed capability (p99.5 meter MW / nameplate, plant grain)
> is **0.889 / 0.897 / 0.925 / 0.911 / 0.921 / 0.933**; 2021 is mid-range and 2020 is the lowest.
> No collapse for a derate to find. (b) **heat rate** — capacity-weighted model **7.2849** vs
> CAMPD-measured-net **7.3361** MMBtu/MWh, the model **0.70 % cheap**, median per-plant delta
> **+0.0336** and **26 of 40 plants DEARER in the model**. A `measured_cc_heat_rates` candidate
> should not be built on this in MISO either. (c) **concentration** — 2021 is fleet-wide
> (**32 of 37 plants under**, top-5 same-sign 44.1 % of the net), so a membership repair has
> nothing to bite on.
>
> **SO THE SESSION TOOK THE HANDOFF'S SECOND BRANCH — work the −32 TWh on MISO's own terms, with
> the C4 time-localisation as the lead — AND THE LEAD PAID.** C4 gas in 2021 (r = 0.864,
> NRMSE = 0.392) is **NOT localised in time and NOT localised in load**: the deficit runs
> −5.7 to −10.4 GW in *every* load decile including the lowest, and every month's own Pearson r
> stays 0.84-0.98 (§4). A residual that is present in every hour, at every load, with the timing
> intact, is a **level substitution**, not a dispatch-response defect. §5 names the counterparty.
>
> **THE COUNTERPARTY IS THE SEAM, AND IT IS RAILED.** Hours the model's net interchange sits on
> MISO's **±8,700 MW Capacity Import Limit** (`EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]`):
>
> | | 2020 | **2021** | **2022** | 2023 | 2024 | 2025 |
> |---|---:|---:|---:|---:|---:|---:|
> | hours on the ±CIL rail | 3,730 | **8,650** | 2,609 | **3** | **0** | **0** |
> | % of the year | 42.6 % | **98.7 %** | 29.8 % | 0.0 % | 0.0 % | 0.0 % |
> | model net import (TWh) | 48.69 | **75.93** | **−22.58** | 43.19 | 27.50 | 20.35 |
> | measured net import (TWh) | 56.37 | 35.51 | 30.97 | 37.91 | 23.08 | 18.95 |
> | **import error (TWh)** | −7.68 | **+40.41** | **−53.55** | +5.28 | +4.43 | +1.40 |
> | C1 failures that year | 0 | **1** | **4** | 0 | 0 | 0 |
>
> In 2021 the model's hourly import takes only **110 distinct values across 8,760 hours** (2023-25:
> 4,210-4,822) — the LP is not clearing imports on merit, it is taking every MW the constraint
> allows, all year. **Every C1 failure MISO has, in any of its six registered years, is in 2021 or
> 2022**, and those are exactly the two years whose annual import error exceeds 40 TWh. The three
> years that never touch the rail carry **zero** C1 failures. §5.
>
> **THE PROVENANCE QUESTION THIS RAISES, WHICH I RAISE AND DO NOT ANSWER.** 8,700 MW is MISO's
> published **Capacity Import Limit** — a PRA/LOLE resource-adequacy planning construct, cited as
> such in `spec.py`'s own comment ("MISO publishes CIL/CEL with the annual Planning Resource
> Auction (PRA) via the LOLE study"). It is being used as the **hourly** simultaneous
> energy-transfer bound, and the measured record does not support it in that role: MISO's own
> metered net import **exceeds 8,700 MW in 583 / 106 / 69 / 118 / 4 / 14 hours** of 2020-2025, and
> its metered net *export* has **never** reached 8,700 MW in any of the six years (deepest
> −5,415 MW, 2024) while the model sits at exactly −8,700 for **2,217 hours** of 2022. That is a
> rule 14 `[R-ACCURATE]` provenance question of the same *class* as the one `nyiso-100` already
> established against NYISO's SIL — **cited as context, not transferred as a verdict**
> (rule 28(d)); MISO's number needs MISO's own adjudication. §6 routes it. **No arm is proposed.**

---

## 2. THE CF MEASUREMENT

Plant-matched, decoded exactly as `legitimacy_diagnostics` decodes the committed payload and bench
(`_decode_cf_bytes`, `load_bench`, `load_payload_plants`). Model from
`2026-09-10-miso-251-tp2020` / `-tp2021` / `-screen2022` (2020-22, all three keeper-recipe replays
carrying the identical seam configuration) and `2026-09-09-miso-250-ep-gas` (2023-25) — MISO's
whole registered set. Instrument: `scripts/probes/_miso255_cc_cf_tracking.py`.

**CC_REGULAR, matched fleet (37-40 plants, 26.6-28.7 GW):**

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| model CF | 0.4510 | **0.2908** | 0.4158 | 0.5160 | 0.5529 | 0.5111 |
| meter CF | 0.4549 | **0.4560** | 0.5099 | 0.5746 | 0.5866 | 0.5380 |
| **Δ** | −0.0039 | **−0.1652** | −0.0941 | −0.0586 | −0.0337 | −0.0269 |
| model TWh | 107.14 | 67.69 | 104.47 | 129.64 | 138.91 | 128.09 |
| meter TWh | 108.06 | 106.14 | 128.12 | 144.36 | 147.38 | 134.82 |
| meter revealed capability (p99.5/npl, plant grain) | 0.8887 | 0.8971 | 0.9253 | 0.9114 | 0.9209 | 0.9327 |

The meter is *flat* between 2020 and 2021 (0.4549 → 0.4560). The model falls **16.0 CF points**.
Whatever happened in the model's 2021 did not happen in MISO's 2021.

**The hours/loading split is DEGENERATE in MISO and must not be read as PJM's was.** MISO runs
legacy equal-width heat-rate bins rather than ERCOT's CAMPD per-plant bins, so a bench "plant" is a
multi-unit aggregate: the CC_REGULAR on-hours fraction is **1.0000 for the model AND the meter in
every year**, so the `a` (model-on/meter-off) and `c` (meter-on/model-off) legs are ~0.00 TWh and
the whole net lands on the loading leg by construction (2021: net −38.45 = hours −0.46 + loading
−37.99). This is an artifact of grain, not a finding, and the PJM comparison on that split does not
carry across. **The CF and capability numbers are unaffected** — both are grain-free.

**One decoding caveat, reported because it bounds a neighbouring row and not this one.** The bench
carries slice keys whose nameplate is a **1.0 MW sentinel** (a class slice whose capacity sits on
its sibling slice). CC_REGULAR's exposure is **0.01 TWh in 2020 and exactly 0.00 in every other
year**, so its CF table is clean; COAL_BIT carries 6.1-8.5 TWh of sentinel-nameplate energy in
2020-2022 and its meter CF is correspondingly biased high in those years. Capability in §1/§3(a) is
therefore computed at **plant grain** (slices summed, plants under 10 MW dropped), where the
sentinel cannot appear.

---

## 3. THE THREE FALSIFICATIONS, RE-RUN ON MISO DATA

A PJM verdict fills no MISO cell (rule 28(d)). Each was re-measured here; each holds.

**(a) Capability / partial derates — FALSIFIED.** Per-plant p99.5 hourly meter MW ÷ nameplate,
CC_REGULAR fleet mean at plant grain: **0.8887 / 0.8971 / 0.9253 / 0.9114 / 0.9209 / 0.9327**
(medians 0.8798-0.9344, n = 37-40). **2021 is the second-lowest by 0.008 and 2020 is lower still**,
while 2020 is MISO's only held-out year with zero C1 failures. There is no 2021 capability event
for a derate mechanism to find. MISO's `temp_dependent_derate` is already **K** and
`gas_coldsnap_derate` **I**; nothing here argues for re-opening either.

**(b) CC heat rate — FALSIFIED, more strongly than in PJM.** The motivating asymmetry is identical
in MISO: `measured_ct_heat_rates` (**K**) and `measured_chp_heat_rates` (**K**) are armed, while
CC_REGULAR carries the eGRID plant-average ANNUAL rate and has no measured artifact. Measured:
CAMPD unit-level, `unitType` naming a combined cycle, operating hours only (`opTime>0`,
`grossLoad>0`, `heatInput>0`), pooled 2023-2025 — **1,776,751 rows, 434.5 TWh gross on all 40 bench
plants** — converted gross → net at a **stated (not fitted) 2.2 % own-use**, the figure `pjm-h1`
used, reused verbatim so the two ISOs are comparable. Model side from
`load_fleet_from_csv("MISO", …)` at the keeper's own flags (`measured_ct_heat_rates=True`,
`measured_chp_heat_rates=True`, `cc_steam_part_capacity=True`, every eGRID variant off).

| | capacity-weighted | median per-plant Δ | plants model CHEAP | plants model DEAR |
|---|---:|---:|---:|---:|
| model | **7.2849** | **+0.0336** | **14 / 40** | **26 / 40** |
| measured (net) | **7.3361** | — | — | — |
| **Δ** | **−0.0512 (−0.70 %)** | | | |

**Reported against my own prior**, as `pjm-h1` reported against its: I expected MISO's CC to be too
efficient and therefore stuck too deep in merit, which would have explained a fleet-wide over-run —
except MISO's 2021 error is an *under*-run, so the prior was incoherent with the sign before it was
even measured. It is 0.70 % cheap at the fleet and dearer at 65 % of plants. The three large
model-cheap outliers are **7985 (−3.76), 1007 (−3.14) and 1004 Edwardsport (−2.17)** — the
gasification / steam-part family `miso-125` / `miso-126` already adjudicated
(`cc_steam_part_capacity` **K**, `cc_steam_part_reclass` **U**, MISO deliberately out of
`CC_STEAM_PART_RECLASS_ISOS`) — a separate and much smaller question, not re-opened here.

**(c) Concentration — FALSIFIED as a membership repair.** CC_REGULAR net miss at plant level:

| yr | net TWh | plants | over | under | top-5 same-sign | % of net |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | −0.92 | 40 | 20 | 20 | −7.94 | 860 % |
| **2021** | **−38.45** | 37 | **5** | **32** | −16.96 | **44.1 %** |
| 2022 | −23.65 | 40 | 10 | 30 | −14.89 | 63.0 % |
| 2023 | −14.72 | 40 | 17 | 23 | −16.16 | 110 % |
| 2024 | −8.47 | 40 | 21 | 19 | −11.69 | 138 % |
| 2025 | −6.73 | 39 | 19 | 20 | −11.92 | 177 % |

2021 is the only year in which the fleet moves as one — 32 of 37 plants under, no five plants
carrying it. In the training years the top five carry 110-177 % of the net (the rest offsetting),
which is the signature of a plant-set question; 2021's is not one.

---

## 4. C4 IN TIME — THE HANDLE `pjm-h1` DID NOT HAVE, AND WHAT IT SAYS

Instrument `scripts/probes/_miso255_c4_gas_localisation.py`, rebuilding C4's own series exactly as
`render_calibration_html` does at registration (model = P1 hourly sum of `classes_for_fuel930`
classes from the committed `hourly/class_hourly_<year>.parquet`; actual =
`load_eia_hourly_benchmark`). It reproduces every registered `fuelRows` r/NRMSE to ±0.006.

**By month — the residual is everywhere, and the timing is intact everywhere.** 2021's per-month
gas residual runs −1.5 to −8.4 TWh in all twelve months (H2 roughly twice H1), and its **per-month
Pearson r is 0.84-0.98** — statistically indistinguishable from 2023-2025's 0.90-0.98. The
whole-year r falls to 0.858 only because the months' *levels* are mis-ordered relative to each
other, not because any month's shape is wrong.

**By load decile — flat, including the bottom.** 2021, model minus bench mean GW, D1 (lowest load)
to D10: **−5.66, −6.61, −6.55, −6.77, −7.69, −7.99, −7.73, −7.44, −8.11, −10.38**. A dispatch-
response defect concentrates where the price crosses the class's marginal cost; this does not
concentrate anywhere. The training years show the same flatness at a third of the amplitude
(2023: −3.48 to −5.10; 2025: −1.76 to −4.86).

**A residual that is uniform in month and in load, with per-month timing intact, is a level
substitution.** §5 identifies the substitute.

---

## 5. THE OBJECT: THE SEAM RAILS, AND IT RAILS ONLY IN THE HELD-OUT YEARS

Instrument `scripts/probes/_miso255_import_envelope.py`.

**The model's import series is degenerate in 2021.** Distinct hourly values across 8,760 hours:
**110** in 2021, against 3,611 / 4,168 / 4,553 / 4,822 / 4,210 in 2020 / 2022 / 2023 / 2024 / 2025.
Its p5, p50 and p95 are all exactly **8,700.0 MW**. Mean 8,667 MW × 8,760 h = 75.9 TWh, which is
the whole annual import.

**8,700 MW is `EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]`** — the bidirectional
`MISO_simultaneous_import` constraint over every border link of the `MISO_external` bus. Rail
occupancy and its consequence:

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| hours at +8,700 | 3,695 | **8,647** | 392 | 3 | 0 | 0 |
| hours at −8,700 | 35 | 3 | **2,217** | 0 | 0 | 0 |
| **% of year on a rail** | 42.6 % | **98.7 %** | 29.8 % | **0.0 %** | **0.0 %** | **0.0 %** |
| model net import TWh | 48.69 | 75.93 | −22.58 | 43.19 | 27.50 | 20.35 |
| measured net import TWh | 56.37 | 35.51 | 30.97 | 37.91 | 23.08 | 18.95 |
| **import error TWh** | −7.68 | **+40.41** | **−53.55** | +5.28 | +4.43 | +1.40 |
| model gas TWh | 174.19 | 115.40 | 175.88 | 201.40 | 218.46 | 200.78 |
| meter gas TWh | 197.38 | 181.04 | 208.39 | 241.24 | 252.08 | 233.23 |
| **gas miss TWh** | −23.19 | **−65.64** | −32.51 | −39.84 | −33.62 | −32.45 |

**Read the gas row carefully, because it is the honest part.** MISO carries a **chronic −23 to −40
TWh gas miss in every year, training years included** — that is the in-sample residual C1 passes on
and it is NOT what this finding is about. What 2021 adds is a **further ~−32 TWh on top of the
~−33 TWh baseline**, and that increment is the same size as the +40.4 TWh over-import (the balance
going to coal +1.7 and a 10.5 TWh lower modelled demand). It is also the same size as the C1 record
the card was commissioned on: **2021 CC_REGULAR −32.06 TWh**.

**The complete C1 failure ledger across all six registered MISO years:**

| year | C1 failures |
|---|---|
| 2020 | *(none)* |
| **2021** | CC_REGULAR −32.06 TWh, share −3.9pp |
| **2022** | CC_REGULAR −15.74; CT_PEAKER +8.52; COAL_PRB **+37.05**; COAL_BIT **+13.48** |
| 2023 / 2024 / 2025 | *(none)* |

2022 is the mirror image and it corroborates rather than complicates: the model **net-exports**
22.58 TWh where MISO imported 30.97, and **coal fills the −53.6 TWh hole** (+37.05 PRB + 13.48 BIT
= +50.5 TWh of the four failing rows). Same constraint, other rail, opposite substitution.

**Rail hours alone do not predict the failure — the ANNUAL error does, and it separates perfectly.**
2020 sits on a rail 42.6 % of the year yet has zero C1 failures, because its annual import error is
only −7.68 TWh: the +CIL hours and the interior hours net out. Ordered by |import error|:
1.40, 4.43, 5.28, 7.68 | **40.41, 53.55** — every year below 8 TWh passes C1 and both years above
40 TWh fail it, with a factor-of-five gap between the groups.

**The armed deliverability envelope does not bound this.** The keeper runs `miso_seam_flow_limit`
+ `miso_seam_export_limit` + `miso_seam_envelope_merit_cap` + `miso_seam_envelope_hour_ending_key`
+ `miso_seam_measured_ladder` + `miso_pjm_border_anchor`, all `True`, in **all four bundles**
(verified in each `run_config.json` — the three held-out replays carry the keeper's seam
configuration exactly, so this is not a configuration difference between years). Rebuilding that
p90 envelope at the keeper's own settings gives 64.87 TWh for 2021, and the model imports
**75.93 TWh = 117 % of it**, flat at 8,700 while the envelope varies (utilisation 1.641 in the
lowest-envelope decile falling to 0.838 in the highest — the signature of a *constant* against a
*varying* ceiling). **The per-seam envelope caps the priced seam bands; the aggregate is being set
by the CIL above them.** Which of those two objects should own the hourly bound is the successor
question, and it is a structural one, not a residual one.

**What the measured record says about the 8,700 MW bound itself**, stated because rule 14
`[R-ACCURATE]` makes it the first question and not the last:

* MISO's **metered** net import **exceeds 8,700 MW** in **583 / 106 / 69 / 118 / 4 / 14** hours of
  2020-2025 (max 12,601 MW, 2021). As an hourly ceiling it is falsified by the meter.
* MISO's metered net **export** never reaches 8,700 MW in any of the six years — the deepest is
  **−5,415 MW** (2024) — while the model sits at exactly −8,700 for **2,217 hours** of 2022.
* `spec.py`'s own comment sources it to "MISO PRA clearing results; MISO LOLE Study Report; MTEP",
  i.e. the **Capacity Import Limit** published with the annual Planning Resource Auction. A CIL is
  a resource-adequacy accreditation limit for a delivery year, not an hourly ATC.

**Cross-ISO context, explicitly NOT a transferred verdict** (rule 28(d), rule 25 `[R-ISO-SCOPE]`):
the same table's NYISO entry already carries a documented **PROVENANCE DEFECT** — `nyiso-100`
established that NYISO's 4,350 MW "SIL" is in fact an internal G-J locality limit, and minted
`nyiso_import_sil_retire` to drop it. That tells this lane **what to ask**, not what the answer is.
MISO's CIL has its own provenance and needs MISO's own adjudication against MISO's own published
documents; a NYISO verdict fills no MISO cell.

---

## 6. WHAT I ROUTE, AND WHAT I DO NOT PROPOSE

**No arm is proposed and no cell verdict moves.** The handoff's gate was explicit: propose nothing
until phase 0 says which branch MISO is. It is the **CF-tracks** branch, so `pjm-h1`'s object is
not here to work, and the lead it directed me to — the C4 time-localisation — landed on the seam
rather than on any CC mechanism. Reaching for a lever now would be selecting a mechanism against
the 2021 residual, which rule 1 `[R-STRUCT]` forbids and rule 29 `[R-SCREEN]` clause 0 exists to
prevent. What is owed first is a **provenance adjudication of the 8,700 MW bound** — a documents
question with no LP in it — and only then, if the bound is found mis-attributed or mis-graded, a
pre-registered structural screen with its own footprint-largest year (**which on this evidence is
2021**, where the rail occupies 98.7 % of hours — chosen by footprint, not by residual, exactly as
rule 29 requires).

**Recorded so no successor spends an LP on them, in MISO:**
* `measured_cc_heat_rates` as a MISO candidate — **falsified at the fleet** (§3b): 0.70 % cheap,
  26 of 40 plants dearer.
* A capability/derate lever aimed at 2021 CC — **falsified** (§3a): 2021 is mid-range and 2020 is
  lower.
* A membership/registry repair of the 2021 CC shortfall — **falsified** (§3c): 32 of 37 plants.
* Importing `pjm-h1`'s CC dispatch-response object into MISO — **the premise is absent here**
  (§1, §2): r = +0.817 with slope +1.36.

**What this hands the seam lane that it did not have.** Every prior MISO seam adjudication —
`miso-174` (`measured_interface_limits` **R**), `miso-176` (`m2m_seam_entitlement_cap` **G**),
`miso-181` (`miso_seam_coincident_envelope` **R**), `miso-211` (`miso_rdt_measured_limit` **R**),
`miso-241` (`seam_flow_envelopes` **K**, evidence-only) — was measured **inside 2023-2025**, where
the CIL rail is touched in **3, 0 and 0 hours**. Those verdicts are therefore untouched by this
finding and none is re-opened: they were all correctly measured in a regime where this constraint
never binds. **The rail is a 2020-2022 object that no MISO seam session has ever been in a position
to see**, and it is refutable in the same way `pjm-h1`'s is: a repair to the aggregate seam bound
that does not move the 2021 rail occupancy off 98.7 % has not addressed it.

**Escalated rather than absorbed:** the provenance of `EXTERNAL_SIMULTANEOUS_LIMITS["MISO"] =
8,700 MW` as an **hourly** bound, given that (i) it is sourced to the PRA/LOLE capacity construct,
(ii) the meter exceeds it in 894 hours across six years, and (iii) the meter never approaches it in
the export direction where the model spends 2,217 hours. This lane did not create a field, did not
change the constant, and did not touch the shared table.

---

## 7. WHAT WAS AND WAS NOT CHANGED

* **`frontend/data/backcast/status/MISO.js` regenerated** (`build_status.py --iso MISO`). It was
  **stale at `origin/main` before this session** — `audit_keepers --iso MISO` failed S1 on arrival.
  The entire diff is one **REPORTED-ONLY, band-free** 2025 `diurnal_amplitude` record moving
  `SKIPPED` → `REPORTED` (amplitude 34.1 % of measured, hod_r 0.94, phase_ok). **Determination,
  grade and caveat budget are byte-identical before and after: CALIBRATED, grade 7, ledgered
  `["C3c price tail / scarcity (RT hourly)"]`, protective `[]`.** MISO's own file, MISO's own lane
  (rule 25); no other ISO's keeper, status, matrix or log was touched.
* **2023-2025 re-verified `CALIBRATED`** after the regeneration, with its single ledgered C3c
  caveat, `audit_keepers --iso MISO` PASS (0 failures, 0 warnings). Rule 30(c) holds: nothing here
  is quoted as certifying or decertifying MISO, and the held-out years remain reported evidence.
* **Four new probe scripts**, read-only over committed artifacts. No `ScenarioConfig` field, no
  solve-path edit, no registration, no bundle, no deletion (rule 31 `[R-RETAIN]` is not engaged —
  **nothing was solved, so there is nothing to promote and nothing at risk from the container
  ending**).

---

## 8. RULES

* **Rule 29 `[R-SCREEN]` clause 0** — the whole session is phase 0. Four candidate arms killed
  before any solve, and the object relocated to a different mechanism family entirely.
* **Rule 28 `[R-MECH-MATRIX]` (a)** — MISO's own cells read before anything was proposed:
  `measured_ct_heat_rates` / `measured_chp_heat_rates` (**K**), `cc_steam_part_capacity` (**K**),
  `cc_steam_part_reclass` (**U**), `cc_mustrun_per_plant` (**·**), `temp_dependent_derate` (**K**),
  `gas_coldsnap_derate` (**I**), `campd_outage_windows` (**K**), `seam_flow_envelopes` (**K**),
  `measured_interface_limits` (**R**), `miso_rdt_measured_limit` (**R**),
  `miso_seam_coincident_envelope` (**R**), `m2m_seam_entitlement_cap` (**G**),
  `diurnal_price_amplitude` (**G**). Nothing marked R/I/G is re-tested or re-opened. Duty (b):
  **no mechanism was tested and no cell verdict moves**; the falsifications are recorded here and
  annotated on MISO's shard.
* **Rule 28(d) / rule 25 `[R-ISO-SCOPE]`** — `pjm-h1`'s three falsifications told this lane what to
  measure; all three were re-measured on MISO data and none was assumed. The `nyiso-100` SIL
  precedent is cited as a question to ask, never as MISO's answer.
* **Rule 1 `[R-STRUCT]`** — nothing armed toward a residual; the surviving object is escalated with
  its provenance question, not pulled.
* **Rule 14 `[R-ACCURATE]`** — the 8,700 MW bound is questioned *because the measured record
  contradicts it*, not because the residual moved.
* **Rule 32 `[R-SHARD]`** — the parent ran no LP, and none was earned.
* **Rule 30(c)** — the training span is untouched and re-verified CALIBRATED.
