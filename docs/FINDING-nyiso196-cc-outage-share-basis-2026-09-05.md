# FINDING nyiso-196 — the C1-2024 `CC_REGULAR` over-run decomposed to ONE measured object (the combined-cycle unit-outage removed SHARE taken across two capacity bases; at Cricket Valley 57185 an EIA-860 id collision halves it), repaired with the zero-DOF `unit_outage_extract_basis_share`, screened on 2024, solved 2023–2025 and PROMOTED — the NYISO keeper reads **CALIBRATED** (2026-09-05 / 06)

**Session:** nyiso-196 (`claude/nyiso-cc-regular-overrun-2024-apt3d6`), 2026-09-05 → 06.
**Owner instructions in force:** nyiso-194/195 (*"Only run 2024 to see if it fixes the c1 gas
cc miss … No control arm just use the last keeper"*), and this session's, verbatim: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves but gates
regress that may still be a keeper.."*
**Keeper at entry:** `2026-09-05-nyiso-192-astoria-panel` (NOT-YET, grade 6, fails 2 — C1-2024
`CC_REGULAR` +3.68 TWh / +3.03 pp against ±3.98 TWh / ±3.0 pp; C3c then not lone).
**Keeper at exit:** `2026-09-06-nyiso-196-extract-basis` (bundle
`results/calibration/nyiso196_extract_basis`) — **CALIBRATED, grade 7 of 8, fails 0, C3c the lone
ledgered caveat; C1 all 14/14, free 10/10.**
**Solves run: TWO** — one rule-29 2024 screen (throwaway, deleted after its gates were recorded)
and ONE full 2023–2025 bundle. **No control solve** (control = the keeper's committed bundle,
rule 29(b) form 4; G-DRIFT audited).
**Pre-registration:** `results/calibration/PREREG-nyiso196-cc-outage-share-basis-screen.md`,
pushed at `64cc970b` BEFORE the screen (Addendum A before the solve); every gate below is the
PREREG's, executed verbatim. **Machine records:** `_nyiso196_cc_overrun_decomp.json`,
`_nyiso196_extract_basis_census.json`, `_nyiso196_rebuild_checks_2024.json`,
`_nyiso196_screen_gates.json`; probes `scripts/probes/nyiso196_*.py`; attestation
`scripts/gen_nyiso196_attestation.py` (every check computed, refuses on failure).

---

## 1. The result in one paragraph

The keeper's +3.68 TWh `CC_REGULAR` over-run in 2024 was not an offer-level object (nyiso-194/195
adjudicated every offer-side lever R). Decomposed at plant-hour grain against the meter, the
growth of the class net from 2023 to 2024 is the **online-hours bucket** — hours the model runs a
plant the meter shows dark — and **466 GWh of the class's 1,471 GWh sit at Cricket Valley 57185,
99.9 % of it in hours the LP was handed more available capacity than the committed unit-outage
extract states** (671 h inside windows where the extract has all three blocks out). The cause is
visible in two data files: CAMPD's stack ids `U001`–`U003` collide with EIA-860 generator ids
`U001`–`U003`, which are the plant's **steam turbines** (prime mover CA, 174.2 MW), so the outage
deriver writes each 1×1 block at 174.2 MW and the LP loader divides that by the plant's 1,016.8 MW
net-summer bin — **17.1 % removed per block against the physical 33.3 %, 48.6 % of a dark plant
left available**. The extract's own columns say 33.3 % (`unit_pct_of_plant`). Taking the removed
fraction on the extract's own basis for combined-cycle bins (one bool, zero DOF, the same
committed extract) removes the contradiction at every CC plant, moves Cricket Valley from
+0.80 TWh above its 2024 meter to 0.53 below it, brings the class cell from +3.68 TWh / +3.03 pp to
**+3.01 TWh / +2.53 pp**, and the keeper reads CALIBRATED. The promotion is on rules 14 / 13 / 1
and on the merits; the regressions are stated at full magnitude in §4.

## 2. Steps 1–3 (zero LP) — what the decomposition measured

Full tables: PREREG §0 and `_nyiso196_cc_overrun_decomp.json`. The keeper's per-plant hourly MW is
the committed dashboard payload (the `legitimacy_diagnostics` decode); the meter is the bench
part's CAMPD series on the same plant/group split.

| year | model | meter (CAMPD gross) | net | (a) model on / meter off | (b+) | (b−) | (c) | online plant-h model / meter |
|---|---|---|---|---|---|---|---|---|
| 2023 | 34.07 | 33.46 | +0.62 | **+1.18** | +4.05 | −3.77 | −0.84 | 91,873 / 89,406 |
| 2024 | 37.61 | 36.44 | +1.17 | **+1.47** | +3.62 | −3.33 | −0.58 | 101,929 / 90,664 |
| 2025 | 35.43 | 33.88 | +1.55 | **+2.27** | +3.99 | −3.56 | −1.15 | 119,192 / 95,550 |

* **Step 2 — mechanism.** The commitment bridge binds 40 h at Cricket Valley in 2024 (D-4
  unit-conduct rows; 92 / 152 in 2023 / 2025); `CC_REGULAR` carries no reliability-floor limb.
  In 97.1 % of the plant's 1,052 bucket-(a) hours the keeper's Capital_Hudson LMP (mean $56.45)
  clears the committed tranche's assembled offer (mean $27.25): **plain economics on the
  availability the LP was given** — the contradicted input is availability, not a floor and not
  an offer. Bucket (a) is flat across the hours of the day (18.6–21.0 GWh per hour) and sits in
  January / March / October / December — the plant's outage calendar.
* **Step 3 — the neighbours, refuted as objects.** Same-zone `ST_GAS` runs 567 GWh below its
  meter in the class's excess hours (the cell-G / owner-court steam object, not a contradicted
  input); imports run 885 GWh below measured in those hours but the LP's import capability never
  binds below the measured scheduled flow (0 of 8,760 h); the keeper's delivered gas equals the
  committed measured hub monthly at Capital_Hudson / Long_Island / NYC in 11 of 12 months exactly
  (Upstate_West rides the SOM annual offset at 1.715 vs 1.83 — a −$0.11/MMBtu level effect in
  every year, not a 2024 signature). **No basis error makes upstate CC cheaper than downstate
  steam in 2024 only.**

## 3. The object, the repair, the census (PREREG §1)

`outages._unit_outage_factors_from_events` derates a bin by `unit_capacity_mw / cap[bin]` —
numerator from the committed extract, denominator from `outages._iso_plant_capacity` (the fleet's
net-summer pmax sum). At Cricket Valley the deriver's exact-id route lands on a CA row, the CT
steam-coupling augmentation never fires, and the two bases diverge by the whole steam share.

**The repair — `ScenarioConfig.unit_outage_extract_basis_share` (default off, registered in the
cache-key drop list in the same commit):** a COMBINED-CYCLE bin's removed fraction is
`unit_capacity_mw / plant_capacity_mw` on the extract's own basis (the published
`unit_pct_of_plant`; the group's distinct-unit sum at a multi-group facility). CC bins only
(`_CC_NAMEPLATE_BASIS_GROUPS`): a CEMS unit at a combined cycle is a block whose plant share the
deriver's `fac_cap` states; steam bins keep `unit_outage_st_capacity_basis` (disjoint, rule 19).
The unscoped construction was measured first and REJECTED for this arm — it also moved Astoria
8906 `ST_GAS` (+1.8 TWh available) and Ravenswood 2500 (+0.55), steam bins the nyiso-192 panel
just adjudicated. Non-ERCOT; mutually exclusive with `unit_outage_lp_capacity_basis` (the loader
raises). Threaded through the std / short / partial / lay-up loaders (the additivity contract),
not maxgen. `tests/unit/data/test_unit_outage_extract_basis_share.py` pins the arithmetic, the
full-stop-is-zero invariant, scope, exclusion and registration.

**Census (zero LP, loader on vs off on the committed extract; GWh available, arm − keeper; only
CC bins move, 17 in 2024, 0 steam):** Cricket Valley **−801 / −1,832 / −1,599** (2023 / 2024 /
2025); Selkirk 10725 `CC_CHP` −1,360 / −1,576 / −1,129 (three blocks dark ~340 days a year; the LP
had it 35 % available against a 0.11 TWh meter); Linden 50006 +303 / +326 / +314; Athens 55405
+236 / +272 / +410; Bethpage 50292 +202 / +154 / +102; Saranac 54574 +94 / +128 / +152; Sithe
54547 +182 / +89 / +98; the rest ±0–75. `CC_REGULAR` net −248 / −1,183 / −667. Every CC bin
moves toward the availability its own extract rows state.

**Screen year 2024**, named in the PREREG from the object's own footprint (0.86 / 1.96 / 1.71 TWh
of over-availed energy at Cricket Valley on 190 / 450 / 398 unit-outage days; the class-wide
absolute footprint is 2 % larger in 2025, stated there for honesty).

## 4. The screen (2024) and the full span (2023–2025)

### 4.1 Screen — CLEARED on every pre-registered structural gate (`_nyiso196_screen_gates.json`)

* **F-1 footprint / F-2 identity — PASS.** 128 LP units' availability move, all CC bins of the 17
  census plants, 0 steam; `pmax`, heat rate, `offer_markup_hr`, `mc_base`, `fuel_prices` max |Δ|
  0.0; arm ÷ keeper availability equals the loader's on ÷ off ratio hour for hour (max error
  3.6e-6); the screen's fleet parquet carries the keeper rebuild's `pmax` on all 704 units;
  G-DELTA exactly the flag (two HEAD-default fields reported: `ccs_retrofit_capex_co2_scaling`
  — the capx D60 default flip, backcast-inert — and `miso_intermediate_gas_offer_margin`, added
  after the keeper solved, at its default).
* **S-3 direction — PASS.** Cricket Valley's energy in the extract's all-blocks-out windows
  **257 → 0.0 GWh** (672 h); energy above the arm's envelope 0.0; annual **5,038 → 3,706 GWh**
  (meter 4,241; required fall ≥ 256 GWh); online 8,748 → 8,082 h (meter 7,704); bucket (a)
  466 → 125 GWh. Selkirk 261 → 48 GWh (meter 108).
* **S-4 companions — PASS.** No load-bearing flip; same-weights C3a-like −0.72 → +0.67 %,
  monthly NRMSE 0.183 → 0.182; gas family 67.79 → 67.75 TWh; imports 20.71 → 20.72.
* **Reported, never gated:** C1-2024 `CC_REGULAR` +3.68 → +3.01 TWh / +3.03 → +2.53 pp at the
  scorer's construction; `CC_CHP` +2.10 → +2.31; `ST_GAS` −1.43 → −1.17. The screen bundle was
  deleted after the record was written (rule 29).

### 4.2 Full span — ONE bundle, `replay_keeper --years 2023 2024 2025 --set unit_outage_extract_basis_share=true`

Registered `2026-09-06-nyiso-196-extract-basis`; attested by
`scripts/gen_nyiso196_attestation.py` (G_CONTROL: the committed keeper on disk equals its git
blobs, 0 of 52,560 hours differing per year; G_DELTA: exactly the flag; G_INPUTS: both bundles pin
the SAME committed extract, sha256 `58799099…`; G_DOF: 13 / `n_residual` 6 verbatim, 0 added;
G_ENGAGE: Cricket Valley's loader availability 0.905 / 0.782 / 0.810 → 0.815 / 0.576 / 0.630);
scored by `calibration_verdict.py --run-id` from committed artifacts only.

| | keeper `2026-09-05-nyiso-192-astoria-panel` | **arm `2026-09-06-nyiso-196-extract-basis`** |
|---|---|---|
| determination | NOT-YET (grade 6 of 8, fails 2) | **CALIBRATED (grade 7 of 8, fails 0, 1 ledgered)** |
| C1 fuel-mix | FAIL — 13/14, free 9/10 (2024 `CC_REGULAR` +3.68 TWh / +3.0 pp, share out of band) | **PASS — 14/14, free 10/10** (2024 `CC_REGULAR` **+3.01 TWh / +2.5 pp**; 2023 +1.08 → **+0.83** / +1.4 → +1.2 pp) |
| C1 companions | 2023 `CC_CHP` +0.75, `ST_GAS` +1.77; 2024 `CC_CHP` +2.10, `ST_GAS` −1.43, `CT_PEAKER` −1.56 | 2023 `CC_CHP` +0.95, `ST_GAS` +1.81; 2024 `CC_CHP` **+2.31**, `ST_GAS` −1.17, `CT_PEAKER` −1.52 (all PASS; 2025 class cells SKIPPED on the preliminary 923 vintage, governed by C2) |
| C2 | PASS | PASS (gas family 62.81 / 67.79 / 69.57 → 62.80 / 67.75 / 69.52 TWh) |
| C3a mean LMP | PASS: +4.8 / +3.2 / −7.3 % | PASS: +4.6 / **+4.7** / −6.9 % |
| C3b shape | PASS: 0.118 / 0.172 / 0.167 | PASS: 0.119 / 0.175 / **0.154** |
| C3c | FAIL (not lone): 3 / 0 / 4 h vs 10 / 13 / 42 | CAVEAT, ledgered (lone): 3 / 1 / 4 h vs 10 / 13 / 42 |
| C4 / C6 | PASS / PASS | PASS / PASS |
| C8 (D-2) | PASS: `CC_REGULAR` 2.7 / 0.8 / 1.1 %; `ST_GAS` 17.1 / 23.8 / 18.6 % | PASS: `CC_REGULAR` 2.8 / 0.8 / 1.2 %; `ST_GAS` **16.6 / 22.4 / 18.2 %** |
| D-4 failures (rider rows) | 8 | 5 |

**Plant grain, at full magnitude (TWh, keeper → arm vs meter):**

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| Cricket Valley 57185 | 5.41 → 4.81 vs 5.32 | 5.04 → **3.71 vs 4.24** | 5.04 → 3.90 vs 4.86 |
| Athens 55405 | 1.68 → 1.89 vs 1.88 | 3.57 → 3.84 vs 4.05 | 2.85 → 3.22 vs 3.32 |
| Bethpage 50292 | 0.19 → 0.26 vs 0.46 | 0.31 → 0.40 vs 0.49 | 0.43 → 0.49 vs 0.65 |
| CPV Valley 56940 | 3.62 → 3.66 vs 4.38 | 4.30 → 4.40 vs 4.98 | 3.85 → 3.96 vs 4.70 |
| Selkirk 10725 `CC_CHP` | 0.15 → 0.04 vs 0.16 | 0.26 → 0.05 vs 0.11 | 0.34 → 0.19 vs 0.38 |
| **Linden 50006 `CC_CHP`** | 6.33 → ~~5.31~~ **6.55** vs 7.23 | 6.20 → ~~5.24~~ **6.44** vs 7.34 | 6.16 → ~~5.21~~ **6.39** vs 7.44 | *(CORRECTED 2026-09-06, nyiso-197 — see the note below §4.2)* |
| Bethlehem 2539 | 4.91 → 4.88 vs 4.18 | 5.97 → 6.05 vs 5.54 | 5.70 → 5.87 vs 5.27 |
| Saranac 54574 | 0.12 → 0.14 vs 0.25 | 0.47 → 0.57 vs 0.37 | 0.53 → 0.67 vs 0.40 |
| Sithe 54547 `CC_CHP` | 4.23 → 4.29 vs 4.06 | 7.37 → 7.49 vs 6.29 | 7.65 → 7.76 vs 6.33 |

> **CORRECTION 2026-09-06 (nyiso-197) — the Linden row above was WRONG and regression (i) below
> is VOID.** Its *keeper* column is the prior keeper's **payload** (full plant, carrying the
> measured 1.25 TWh/yr CHP add-back) while its *arm* column is the arm's **LP grid** series (no
> add-back); Linden is the only plant in this table with a non-zero measured BTM hold-out, so it
> is the only row the mismatch can move — every other row reproduces from the committed payloads
> to the digit, Sithe 54547 `CC_CHP` (measured share 0.0 %) included. On the committed payloads
> Linden **GAINED** +224 / +243 / +227 GWh, which is what its own availability census
> (+302 / +326 / +314 GWh available) predicts. The provenance is in this session's own record:
> `_nyiso196_screen_gates.json` `S3_direction.moved_plants[1]` carries `keeper_gwh` 6196.9
> (payload) against `screen_gwh` 5235.5 (LP) — the 5.24 printed above. **Nothing else in this
> document changes**: the repair, the screen, the determination and every other §4.2 row are
> unaffected, and the promotion never rested on this row. Evidence:
> `docs/FINDING-nyiso197-linden-addback-basis-2026-09-06.md`,
> `results/calibration/_nyiso197_linden_phase0.json`. Original text preserved below, unedited.

**Regressions, stated:** (i) **Linden 50006 falls ~1.0 TWh in every year, AWAY from a 7.2–7.4 TWh
meter, although its own availability ROSE (+0.3 TWh/yr)** — the LP re-placed the released
combined-cycle energy; Linden sits on the NYC node behind the Linden VFT and its CHP duty
mechanisms, and its energy placement is a plant-grain displacement the `CC_CHP` class cell absorbs
(+2.10 → +2.31 TWh in 2024, PASS). It is the one plant-grain regression of size and is handed
forward (§6). (ii) Cricket Valley now sits 0.53 TWh UNDER its 2024 meter and 0.96 under in 2025 —
the extract's own availability is now binding there, and the residual is the plant's loading in
the hours it is available (bucket b−: 371 → 906 GWh in 2024), a different object. (iii) C3a-2024
+3.2 → +4.7 % and C3b-2024 0.172 → 0.175 (both PASS; C3b-2025 improves 0.167 → 0.154). (iv)
Bethlehem +0.08 / +0.17 TWh further above its meter in 2024 / 2025; Sithe +0.05 / +0.12 / +0.11.

## 5. Governance and the promotion

* **Rule 1 / 13 / 14:** the bars were fixed and pushed before the screen; the object is a measured
  input the model contradicted hour by hour, repaired by taking the extract's own columns on one
  basis; nothing is fitted, no residual enters the construction; a forecast year's extract
  regenerates identically. **Rule 19:** CC-scoped so no bin carries two share constructions; the
  loader raises on the one stacking case. **Rule 21:** zero DOF (the ledger is the keeper's, 13 /
  6, verbatim). **Rule 22:** 2023–2025 only; no marker requested; `complete` is NOT re-declared —
  NYISO sits in `calibration-complete.json`'s `withdrawn` block and re-entry is a **new owner
  declaration** under that block's re-entry clause (gate (a) re-keyed in that PR). **Rule 23:** no
  derive re-run, no artifact touched. **Rule 24 / 28:** a registered field, its matrix row and a
  cell in every ISO shard in the same PR; NYISO cell K. **Rule 25:** NYISO's own extract; every
  other ISO enters U with its own zero-LP census as the transfer question. **Rule 29:** phase 0 →
  one-year screen → full span, keeper as control, G-DRIFT `d5bba63b..5b5af5ab` all INERT (PREREG
  §5). **Rule 15:** registered, attested, verdict re-verified, keeper shard promoted,
  `status/NYISO.js` rebuilt, `audit_keepers --iso NYISO` PASS (the E11 recipe-field declaration
  for the capx D60 default flip is in the promotion prose). The former keeper's bundle and
  dashboard row are **protected by governance citations** (`calibration-complete.json` withdrawn
  block, the shard's `superseded` entry) and are left in place; `prune_iso_runs.py --iso NYISO`
  prunes nothing without `--force-uncite`.
* **Promotion.** Owner instruction, this session: *"Is this a recommended keeper candidate? If so
  plz promote. If structural integrity improves but gates regress that may still be a keeper.."*
  The arm is recommended on the merits and promoted: structural integrity improves (a
  contradicted measured input removed at every combined-cycle bin, zero DOF) AND the determination
  improves NOT-YET → CALIBRATED; the regressions of §4.2 are stated at full magnitude and none
  crosses a band.

## 6. Handed forward

1. ~~**Linden 50006 `CC_CHP`** (NYC node): −1.0 TWh/yr away from a 7.3 TWh meter under this keeper,
   with its availability up — the largest plant-grain miss the class cell now hides. Object:
   its placement against the Linden VFT / NYC steam and its CHP duty (`chp_layup_duty_curve`,
   `nyiso_chp_btm_measured` hold-out 22.2 %) — measure before any lever.~~
   **VOID 2026-09-06 (nyiso-197): the fall does not exist** — see the correction note above §4.2.
   Linden ROSE +224 / +243 / +227 GWh on the committed payloads. The cell is re-specified and
   filed to the owner court: the model delivers **+0.90 TWh/yr (+21 %) MORE** from Linden Cogen
   into Zone J than NYISO's Gold Book Table III-2a says the station delivered (4,390.7 / 4,288.7
   GWh for CY2023 / CY2024, PTID 23786), at a merit position where its committed band clears the
   modelled NYC LMP in 99 % of hours. The VFT limb is refuted (the Gold Book carries Linden as an
   internal Zone-J station, and I-1 already measured 0 of 8,760 h of binding import capability);
   the duty limb is inert (the lay-up census abstains at Linden). Any lever is an OFFER-position
   lever on `CC_CHP` and needs an owner ruling under rule 1's carve-out conditions.
   Evidence: `docs/FINDING-nyiso197-linden-addback-basis-2026-09-06.md`.
2. **The deriver's id resolution** (`derive_campd_unit_outages.unit_capacity_mw`): a CAMPD stack
   id must never resolve to a CA (steam) generator; the shared EIA-860 `Unit Code` links the CA
   row to its CTs. A record-only follow-up (rule 23: re-derive only citing this defect); the
   loader-side share already makes the extract's value immaterial for CC bins.
3. **Cricket Valley's loading when available** (2024 now 0.53 TWh UNDER): bucket (b−) 906 GWh —
   the plant runs at part load in the model where the meter runs it full; the wall / econ-ramp
   objects of nyiso-194/195 (all R) do not reach it; a new phase 0 is needed before any lever.
4. **Transfer census (rule 25):** every other ISO's `unit_outage_extract_basis_share` cell is U;
   the zero-LP on/off census (`unit_outage_derate_factors` per CC bin-year) is the transfer
   question, per ISO from its own extract.
5. Owner court, unchanged: the `complete` re-entry declaration on this keeper; the NYC steam
   delivered-gas intake spec; the D-2 unit-grain scorer card; the AORR fetch; the Q45 footing.

*(nyiso-196, 2026-09-05 → 06. Two solves: one 2024 screen (deleted), one 2023–2025 bundle
(registered, attested, promoted). No control solve. Keeper: `2026-09-06-nyiso-196-extract-basis`.)*
