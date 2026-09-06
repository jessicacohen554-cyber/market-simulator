# FINDING nyiso-198 — Cricket Valley's part-load bucket (b−) is an OFFER-POSITION object, and the position is **which capacity sits in the duct band**: 726.5 MW of NYISO's 1,069 MW combined-cycle peak band is filed by EIA-860 as having **no duct burner**. The repair was pre-registered and screened on 2024; **the screen's own S-4 gate STOPPED it** — CC gains what steam and CTs lose, and C1-2024 `CC_REGULAR` flips PASS → FAIL. **The span was not spent.**

**Session:** nyiso-198 (`claude/nyiso-backcast-calibration-jnciv2`), 2026-09-06.
**Keeper: UNCHANGED — `2026-09-06-nyiso-196-extract-basis`** (CALIBRATED, grade 7 of 8, fails 0,
C3c the lone ledgered caveat). **Nothing was promoted and nothing was registered.**
**Solves run: ONE** — the rule-29 2024 screen, a throwaway probe, deleted before merge (rule
29(c)). **No control solve** (control = the keeper's committed bundle, rule 29(b) form 4;
G-DRIFT audited, all INERT).
**Pre-registration:** `results/calibration/PREREG-nyiso198-duct-peaking-row-scope-screen.md`
(§0–§7 pushed at `f56e23cd` before the arm was built; **Addendum A** pushed before the screen
solve). Every gate below is the PREREG's, executed as written.
**Machine records:** `_nyiso198_cricket_partload_phase0.json`,
`_nyiso198_duct_peaking_basis_phase0.json`, `_nyiso198_rebuild_checks_2024.json`,
`_nyiso198_screen_gates.json`; probes `scripts/probes/nyiso198_*.py`.

---

## 1. The result in one paragraph

The queue's live item — Cricket Valley 57185's part-load bucket **(b−), 906.1 GWh in 2024** —
resolves against the LP's own bounds with no solve: **0 GWh** is capacity scope, **≤ 6.6 GWh** is
the commitment bridge's min-gen floor, **100.5 GWh** is the plant pinned at a derated envelope,
and **805.6 GWh (88.9 %) is MERIT** — hours where the LP dispatches 444.7 MW of a 451.9 MW mean
in-the-money capacity (98.4 %) and the meter runs above what the modelled price clears. So of the
brief's three candidates the min-load limb is dead and the object is offer position. Re-attributed
exactly, **56.6 % of (b−) is the plant's envelope headroom sitting in the duct/peak band**. That
band's *price* is untouchable (`peak` 2.25 = `phys_peak` 2.25, markup 0), but its *membership* is
`cc_duct_peaking_pct`, which sets the peaking share as the whole plant's nameplate-minus-net-summer
gap whenever any generator row is flagged `Duct Burners = Y`. **A duct burner fires into the HRSG
and raises the steam turbine's output, and EIA-860 reports the attribute at that grain: across the
entire operable combined-cycle population the column reads Y/N only on CA and CS rows and `X` on
every one of the 1,213 CT rows — `CT ∧ Y` is 0 of 1,213.** At Cricket Valley 203.7 of the 296.4 MW
(69 %) therefore sits on rows the filing says have no duct burner, putting 245.64 MW of the LP's
1,086.9 at 15.78 MMBtu/MWh against a $35.50 mean zonal LMP; fleet-wide it is **726.5 MW, 68 % of
NYISO's combined-cycle peak band**. The zero-DOF repair (`cc_duct_peaking_row_scoped`: take the gap
over the flagged rows, same columns, same formula, nothing chosen) was pre-registered and screened
on 2024. **It does exactly what its arithmetic says** — Cricket Valley +375.4 GWh of a 622.1 GWh
footprint bound, closing 70 % of that plant's gap to its meter, and system prices fall 4.2 % (a
same-weights C3a-2024 indicator of +4.7 % → +0.3 %). **And its own S-4 gate stops it:** the cheaper
CC stack takes 0.71 TWh from `ST_GAS` and 0.06 from `CT_PEAKER` — classes already *under* their
actuals — so C1-2024 `CC_REGULAR` goes **+3.01 → +4.13 TWh, +2.5 → +3.4 pp**, out of the 3.0 pp
band. Under rule 29 the arm is killed at the screen and the remaining years were never spent.
**The honest reading is rule 14's own:** an inaccurate input that was silently compensating for a
different error. The duct-band mis-classification was holding the combined-cycle stack back; remove
it and the model says CC is too cheap against steam and CTs for a *separate* reason. That reason,
not this one, is the next lever.

## 2. Phase 0 (zero LP) — the bucket resolved against the LP's own bounds

Every dispatched MW sits between `pmin[g,t] ≤ P[g,t] ≤ pmax[g]·availability[g,t]`, so which bound
binds in each (b−) hour is decidable from the keeper's committed payload plus an on-recipe
`fleet_only` rebuild. **2024, Cricket Valley 57185:**

| binding bound | hours | deficit GWh | share | model / meter / envelope MW | mean LMP |
|---|---:|---:|---:|---|---:|
| CAP_SCOPE — at envelope, no outage (LP capacity too small) | 0 | 0.0 | 0.0 % | — | — |
| CAP_OUTAGE — at a derated envelope | 950 | 100.5 | 11.1 % | 477.8 / 583.6 / 478.2 | $40.54 |
| FLOOR — at the commitment-bridge min-gen | 0 | 0.0 | 0.0 % | — | — |
| **MERIT — interior, headroom the LP declined** | **4,833** | **805.6** | **88.9 %** | 444.7 / 611.4 / 621.7 | $35.50 |

The min-load limb is dead on the keeper's own committed D-4 row (the bridge floors **6.6 GWh over
29 binding hours** at this plant in 2024). The capacity-scope limb is dead (the meter exceeds the
LP's 1,086.9 MW in 53 h for 0.3 GWh; `cc_capacity_reconcile` already set that capacity at the CAMPD
demonstrated peak). Re-attributed as an exact partition of the deficit:

| 2024, Cricket Valley | GWh | share |
|---|---:|---:|
| availability short (meter above the LP envelope) | 268.4 | 29.6 % |
| **peak-band short (envelope headroom in the duct band)** | **512.5** | **56.6 %** |
| econ-band short | 126.6 | 14.0 % |

## 3. The object — the duct band's membership, not its price

`fleet.campd_bins.cc_duct_peaking_pct()`:

```
duct-fired  <=>  ANY of the plant's CC generator rows has "Duct Burners" == Y
pct_peak     =   100 * max(0, SUM_all_rows (nameplate - net_summer)) / SUM_all_rows nameplate
```

**F-0, the population census.** EIA-860 Generator_Y operable, 1,941 combined-cycle rows:
`CA/Y` 466, `CA/N` 194, `CS/Y` 19, `CS/N` 49, **`CT/X` 1,213 — and `CT/Y` is 0.** The attribute is
reported only where the duct burner physically is, on the steam side. A CT row's
nameplate-vs-summer gap is site/ambient derate by construction; the plant-level sum books it as
duct capability and offers it at 2.25× the base heat rate.

**Cricket Valley 57185**, EIA-860 applied vintage:

| rows | nameplate | net summer | winter | gap | Duct Burners |
|---|---:|---:|---:|---:|---|
| 3 × CA (steam) | 522.6 | 429.9 | 450.9 | **92.7** | **Y** |
| 3 × CT | 789.9 | 586.2 | 687.3 | **203.7** | **X** |
| plant | 1,312.5 | 1,016.1 | 1,138.2 | 296.4 | — |

22.6 % → **245.64 MW of 1,086.9 at $53.73/MWh against a $35.50 mean LMP**. The plant's own meter
agrees the gap is ambient: **2024 CAMPD max 1,116.0 MW = 0.85 × nameplate and 0.981 × winter
capability, in April** — and that is a gross-vs-net comparison, so the true ratio is lower still.

**The repo already names the conflation.** `data/fleet/assembly.py:600`, verbatim: *"the raw
nameplate-vs-net-summer gap folds the ambient summer derate into the duct band, oversizing it for
high-gap plants and dropping the price wall below the real duct point."* The remedy in place is
`cc_duct_peaking_cap_pct` — **a chosen number, 8.0 for PJM and `None` for every other ISO**, which
is why NYISO carries the raw gap. Row-scoping chooses nothing and lands Cricket Valley's price wall
at **92.9 %** of capacity: the same ~92 % physical duct point PJM's cap was set to reach,
**arrived at from the filing instead of selected**. That is corroboration, not the ground; the
ground is that 1,213 of 1,213 CT rows read `X`.

## 4. The mechanism and the pre-solve gates

**`cc_duct_peaking_row_scoped`** (`ScenarioConfig`, default **off**, rule 24): numerator over the
flagged rows; denominator, clip, plant-selection rule, `cc_duct_peaking_cap_pct` and every consumer
unchanged. **Zero free parameters, no DOF entry**, rule-13 forward-regenerable, byte-inert off.

**F-1 and F-2 as first written FAILED, and what failed was the PREREG's census, not the mechanism.**
726.53 MW moved across 17 plants against a predicted 647.95 across 11, with four unexpected movers,
and one plant's total `pmax` changed. Both causes are recorded in Addendum A: the mover classifier
ignored that the builder sets `peak_cap = grid_cap × pct_peak / (100 − pct_mr)`, so any plant with a
must-run share was misfiled; and the identity claim was too strong by one mechanism class (at
Riverbay 52168 there is no econ band at all, so the released 1.2122 MW would have to open six
sub-bins of 0.202 MW each — below the floor that admitted World Generation X's 0.821 MW sub-bins —
and it leaves the LP instead).

**The replacement is a forward prediction, not a widened tolerance**, and it is a strictly harder
gate — 31 plants pinned individually against the builder's own formula instead of 11 against a
table:

> **Set B** = `_chp_layup_cohort` ∪ `_chp_duty_curve` ∪ `_reserve_duty_cohort` (14 plants,
> enumerable before the rebuild) — peak band **unchanged, exactly**.
> **Set A** = every other CC plant — peak band scales by `peak_off × pct_row / pct_cur`.

**Measured: residual 0.000 MW at every plant.** 57185 245.639 → 77.170 (predicted 77.170);
56940 105.111 → 4.873 (4.873); 54547 160.934 → 72.941 (72.941); 2539 80.379 → 4.466 (4.466);
50006 58.446 → 4.871 (4.871); 10190 4.913 → **24.706** (24.706 — a plant that *gains* band because
its CT rows are filed with summer capacity above nameplate, which the plant-level sum was netting
against real steam-row gap). **F-1′ PASS. F-2′ PASS** with the Riverbay exception named at full
magnitude: 1.2122 MW, **0.011 %** of the 11.0 GW NYISO CC fleet, at a plant whose whole 2024
pre-solve reachable energy is 0.2 GWh — a pre-existing property of the tranche builder's small-band
filter that this arm surfaces, carried forward rather than swept.

**Screen year 2024**, named in the PREREG before the screen and re-derived on the corrected MW in
Addendum A before the solve — footprint = re-banded MW × availability × hours the zonal LMP sits
between the plant's econ and peak offers, **no meter and no residual in the metric**: 2,879,183 /
**3,047,026** / 2,790,739 MWh for 2023 / 2024 / 2025.

## 5. The screen — S-3 clears, **S-4 stops**

**S-3 direction and magnitude bound (meter-free): PASS.** The mechanism does what its arithmetic
says. Cricket Valley **3,706.1 → 4,081.5 GWh, +375.4** against a 622.1 GWh footprint bound (and
against a 4,240.9 GWh meter — 70 % of the plant's gap closes). Fleet combined cycle **+1,238.1 GWh**
against a 3,047.0 bound. **C8 / D-4: PASS** — no new D-4 failure, no forced-share change.

**S-4 load-bearing companions: STOP.** C1-2024 `CC_REGULAR` flips **PASS → FAIL**.

| C1 2024 cell | keeper | screen | actual |
|---|---|---|---|
| **`CC_REGULAR`** | **+3.01 TWh, +2.5 pp — PASS** | **+4.13 TWh, +3.4 pp — FAIL** | 34.060 |
| `CC_CHP` | +2.31, +1.9 — PASS | +2.43, +2.0 — PASS | 17.017 |
| `ST_GAS` | −1.17, −0.8 — PASS | **−1.88, −1.4** — PASS | 9.913 |
| `CT_PEAKER` | −1.52, −1.1 — PASS | −1.58, −1.2 — PASS | 1.911 |
| `ST_CHP` | +0.21, +0.2 — PASS | +0.05, +0.0 — PASS | 0.872 |

Class deltas (TWh): `CC_REGULAR` **+1.121**, `CC_CHP` +0.117, `ST_GAS` **−0.706**, `CT_CHP` −0.252,
`ST_CHP` −0.159, `CT_PEAKER` −0.061, import −0.053. **Prices fall 4.2 %** (mean 38.386 → 36.775,
p95 60.61 → 58.47, 0 hours > $300 either way), a same-weights C3a-2024 indicator of
**+4.7 % → +0.3 %** — an approximation, not the scored C3a.

**Plant grain, both sides on the LP-grid basis** (the payload's flat CHP add-back removed — the
nyiso-197 §8 item 4 assertion, now implemented in the screen-gate probe, which otherwise fabricates
a −898 GWh fall at Linden where the truth is **+351**):

| plant | re-banded MW | keeper GWh | screen GWh | Δ | meter GWh | toward |
|---|---:|---:|---:|---:|---:|---|
| CPV Valley 56940 | 100.2 | 4,354.2 | 4,833.3 | **+479.1** | 4,981.9 | **yes** |
| Cricket Valley 57185 | 168.5 | 3,706.1 | 4,081.5 | **+375.4** | 4,240.9 | **yes** |
| Linden 50006 | 53.6 | 5,190.5 | 5,541.6 | +351.1 | 7,344.1 | see note |
| Sithe 54547 | 88.0 | 7,490.4 | 7,786.2 | +295.8 | 6,286.1 | no |
| Astoria Energy II 57664 | 87.8 | 4,314.9 | 4,593.0 | +278.1 | 4,136.7 | no |
| Bethlehem 2539 | 75.9 | 5,990.4 | 6,222.3 | +231.9 | 5,539.0 | no |
| Empire 56259 | 48.4 | 3,011.3 | 2,867.9 | −143.4 | 2,980.8 | no |

*Linden note:* against the CAMPD **gross** meter it moves toward, but nyiso-197 established that
this plant's correct comparand is NYISO's Gold Book Table III-2a **net** energy (4,288.7 GWh for
CY2024), against which the keeper is already +0.90 TWh over — so on the right basis Linden moves
**further over**. That is the plant nyiso-197 filed to the owner court as an offer-position object,
and this arm makes it larger.

**Verdict: STOP.** Per rule 29 the arm is killed at the screen and the 2023 / 2025 years were never
spent. The screen bundle is deleted before merge (rule 29(c)); every number this session will ever
cite from it is in this document.

## 6. What the stop actually means — rule 14's own diagnosis

The failure is not "the residual didn't move". It moved a great deal, and in two directions at once:

* **Within** the combined-cycle class the plant-grain distribution improves markedly — the two
  largest movers are the two plants furthest *under* their meters, and Cricket Valley's own
  906 GWh part-load bucket, the object this session was convened on, closes by 70 %.
* **Between** classes it gets worse. The cheaper CC stack takes 0.71 TWh from `ST_GAS` and
  0.06 from `CT_PEAKER` — both already *under* their actuals — and hands it to `CC_REGULAR`, which
  was already the over-run class.

Rule 14 `[R-ACCURATE]` names this situation exactly: *"If swapping a hand estimate for real data
makes the backcast worse, that is a signal that something else in the model is miscalibrated and the
estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate
input, find and fix the real root cause… Do not bury the error back inside an inaccurate input."*
**726.5 MW of mis-classified expensive band was holding the combined-cycle stack back, and it was
the only thing doing so.** Remove it and the model says CC is too cheap relative to steam and
peakers for a *different* reason — the CC-vs-`ST_GAS`/`CT_PEAKER` merit order. That, not the duct
band, is where the next lever belongs, and it is a sharper question than the queue had before this
session: `ST_GAS` at −1.17 TWh and `CT_PEAKER` at −1.52 are not small, and both got worse the moment
a real CC constraint was removed.

**A note on the standing owner-ruled lever.** The NYISO shard carries, from nyiso-193 (2026-09-05):
*"tune the cc regular offer curve up for the duct burner peaking tranche because it's merit order is
wrong."* This session's object is the same tranche, approached from its capacity rather than its
price, and the diagnosis "its merit order is wrong" is confirmed — with a cause. Two measurements
bear on the ruled lever, both from committed artifacts: on the current keeper the `CC_REGULAR` peak
band runs at **12.8 % CF** (2024; `CC_CHP` peak 11.4 %) and carries **3.5 % of class energy**, so
raising its offer moves little energy; and 69 % of the band it would raise is not duct capability at
all. Raising the price of a mis-classified band and correcting the classification are different
repairs, and the second is zero-DOF. **This is stated for the owner court, not decided here.**

## 7. Governance

* **Rule 29 `[R-SCREEN]`:** phase 0 (zero LP) → pre-solve F-gates (zero LP) → ONE screen year, named
  by footprint before the solve → **STOP**, span not spent. PREREG and Addendum A both pushed before
  the solve they govern. Screen bundle deleted before merge (29(c)).
* **Rule 29(b):** no control solve. G-DRIFT `5b5af5ab..982ba9aa`, 26 commits, every hunk INERT for a
  NYISO backcast, with two empirical checks stronger than the diff reading — the keeper's own
  `unit_outage_extract_basis_share` reproduces to the digit at HEAD (Cricket Valley 2024 mean
  **0.5763** vs the committed 0.576) and the committed nyiso-197 Linden rebuild re-runs at HEAD with
  an **empty `git diff`**. Re-checked after rebasing onto `821c11c5`: the 31 new commits touch **zero
  solve-path files**.
* **Rule 1 `[R-STRUCT]`, boundary named not assumed:** the carve-out lists `pct_peaking` as not an
  authorized price-tuning channel. This arm **selects no value** — the share is computed from
  EIA-860's own columns at the grain the flag is reported — and is admitted under rules 14 / 13 on
  the nyiso-196 precedent (a structural quantity corrected against its own source, zero DOF,
  pre-registered and screened by this lane without a ruling). **Whether a *derivation* repair falls
  inside that clause is filed to the owner court and is not claimed here.** No band multiplier and
  no `phys_*` value moves.
* **Rules 21 / 23:** zero free parameters, no DOF entry, no derive re-run, no artifact touched.
* **Rule 15 `[R-DASHBOARD]`:** nothing registered — a rule-29 screen bundle is never registered, and
  no full-span bundle was produced. The keeper's dashboard row is untouched.
* **Rules 24 / 26:** the field is registered in `ScenarioConfig` with its `_CACHE_KEY_OPTIONAL_FIELDS`
  entry and pinned default in the same commit; the matrix carries its base row plus a cell in every
  ISO shard (NYISO **O**, the other five **U** with their own zero-LP census named as the transfer
  question — rule 25, no NYISO verdict crosses the boundary).
* **Rule 22:** 2023–2025 only; no marker requested; `complete` remains withdrawn.

## 8. Handed forward

1. **THE NEXT LEVER, and it is sharper than the queue's previous one: the `CC_REGULAR` vs
   `ST_GAS` / `CT_PEAKER` merit order.** This session measured that the duct-band
   mis-classification was the only thing holding the CC stack back; with it removed CC takes
   0.71 TWh from `ST_GAS` and 0.06 from `CT_PEAKER`, both of which were already under. Phase 0 for
   that lever should start where this one did — at the bound that binds, not at the residual.
2. **`cc_duct_peaking_row_scoped` is filed to the owner court, not rejected.** The object is real
   and measured (726.5 MW, 68 % of the NYISO CC peak band, 0 of 1,213 CT rows flagged Y); the
   mechanism does exactly what its arithmetic says; its cost is one load-bearing cell. Under the
   owner's standing formula — *"if structural integrity improves but gates regress that may still
   be a keeper"* — the owner may want the full 2023–2025 span scored. **That needs an explicit
   ruling**, because the pre-registered gate stopped the arm and because of the rule-1 boundary
   in §7. The matrix cell is **O**, not R, so the DO-NOT-REDO discipline does not close it.
3. **Two repo-wide items surfaced, both outside this lane (rule 25).** (a) `cc_duct_peaking_cap_pct`
   is applied in `data/fleet/assembly.py` but **not** in its `data/offer_curves.py` mirror, so for
   PJM the dashboard band and the dispatch band disagree. (b) The `CT ∧ Y = 0 of 1,213` census is
   national: every ISO's duct band carries the same construction, and each needs its own zero-LP
   census (the recipe is in every shard's `U` cell).
4. **Riverbay 52168's 1.2122 MW**, reported at full magnitude in §4 — the tranche builder's
   small-band filter drops a released band that cannot open six viable econ sub-bins. Immaterial
   here (0.011 % of the CC fleet); worth a line in the builder's docstring.
5. **nyiso-197 §8 item 4 is DISCHARGED**: the screen-gate probe now removes the payload's CHP
   add-back so both sides of a plant-grain comparison are LP grid. It caught a fabricated −898 GWh
   fall at Linden on this session's own first pass; the truth is +351.
6. Owner court, unchanged: the `complete` re-entry declaration; the Linden `CC_CHP` offer-position
   cell (which this arm would enlarge); the NYC steam delivered-gas intake spec; the D-2 unit-grain
   scorer card; the AORR fetch; the Q45 footing.

*(nyiso-198, 2026-09-06. ONE screen solve, deleted before merge. Nothing registered, nothing
promoted. Keeper unchanged: `2026-09-06-nyiso-196-extract-basis`.)*

---

# §9 — THE FULL SPAN, UNDER THE OWNER RULING: **NOT-YET, grade 5, fails 3.** The recommendation is **DO NOT PROMOTE**, and the pre-named risk is exactly what landed.

**Owner ruling, 2026-09-06, verbatim:** *"Is this a recommended keeper candidate? If so plz promote.
If structural integrity improves but gates regress that may still be a keeper.."* — recorded in the
PREREG's **Addendum B** and pushed at `a8f42835` **before the span was solved**, together with the
G-DRIFT re-check on the rebased base and, in §B.2, the arm's most likely second failure **named in
advance**.

**Run:** `2026-09-06-nyiso-198-duct-row`, bundle `results/calibration/nyiso198_duct_rowscope`,
`--year 2023 2024 2025` in ONE invocation and ONE bundle (rule 16), registered the same session
(rule 15). Attestation computed and PASSING on every check
(`scripts/gen_nyiso198_attestation.py`; G-CONTROL max |Δprice| disk-vs-git **0.0** across all three
years, G-DELTA **exactly `{cc_duct_peaking_row_scoped: False → True}`** with
`ccs_retrofit_fixed_cost_co2_scaling` reported as `head_defaults_not_recipe`, G-INPUTS the EIA-860
sheet pinned with `CT ∧ Y = 0 of 1,213` recomputed, G-DOF 13 / `n_residual` 6 verbatim with **0
added**, G-ENGAGE the solved fleet carrying the predicted peak band).

## 9.1 The determination

| | keeper `…-196-extract-basis` | arm `…-198-duct-row` |
|---|---|---|
| **determination** | **CALIBRATED** | **NOT-YET** |
| target grade | 7 | **5** |
| failing criteria | **0** (C3c the lone ledgered caveat) | **3 — C1, C3a, C3c** |
| C1 fuel mix | 14/14, free 10/10 | **13/14, free 9/10** |
| C1-2024 `CC_REGULAR` | +3.01 TWh, +2.5 pp — PASS | **+4.13 TWh, +3.4 pp — FAIL** |
| C3a mean LMP | +4.6 / +4.7 / −6.9 % — PASS | **2025 −10.3 % — FAIL** |
| C3c price tail | ledgered CAVEAT (lone) | **FAIL** (no longer lone) |
| C2 / C3b / C4 / C6 / C8 | PASS | PASS |

**The C3c flip is collateral, not a new defect.** The standing rule reclassifies C3c to a ledgered
caveat only when it is the **lone** failure; with C1 and C3a failing, that guard correctly stays
silent and C3c reads FAIL at the same unchanged magnitude (3 / 1 / 4 h vs 10 / 13 / 42 h > $300).

## 9.2 The pre-named risk landed exactly

Addendum B §B.2, written before the solve: *"the keeper's C3a-2025 is **−6.9 %** … and the screen
moved 2024 prices **−4.2 %**. If 2025 takes a similar move it lands near **−11 %** and C3a-2025
fails. This is the arm's most likely second failure and it was never screened."*

**Measured on the span:** prices −3.10 / −4.20 / −3.68 % and **C3a-2025 −10.3 % — FAIL.** The
mechanism is not surprising anyone; it is doing precisely what its arithmetic said, in the year the
screen never looked at because the screen year was chosen by footprint rather than by risk.

## 9.3 The realised span, at full magnitude

Class energy, TWh (keeper → arm), all three years the same signature:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`CC_REGULAR`** | 33.840 → 34.987 (**+1.147**) | 37.067 → 38.188 (**+1.121**) | 35.102 → 36.484 (**+1.383**) |
| `CC_CHP` | +0.192 | +0.117 | +0.108 |
| **`ST_GAS`** | 9.952 → 9.034 (**−0.918**) | 8.739 → 8.034 (**−0.706**) | 9.606 → 8.806 (**−0.801**) |
| `CT_CHP` | −0.221 | −0.252 | −0.194 |
| `ST_CHP` | −0.102 | −0.159 | −0.113 |
| `CT_PEAKER` | −0.080 | −0.061 | −0.309 |
| import | −0.021 | −0.053 | −0.079 |
| mean LMP | **−3.10 %** | **−4.20 %** | **−3.68 %** |

`ST_GAS` sat at −1.17 TWh under its actual on the keeper and goes to −1.88 in 2024; `CT_PEAKER` at
−1.52 goes to −1.58. **The arm takes energy from two classes that were already under and gives it
to the one that was already over**, in every year, and takes 3–4 % off prices that were only over in
two of three years.

## 9.4 The recommendation: **DO NOT PROMOTE**

The owner's formula is *"may still be a keeper"* — permissive, not automatic — and the honest answer
on this span is **no**. The reasoning, stated against the formula's own two halves:

* **Structural integrity does improve, and that half is not in doubt.** 726.5 MW — 68 % of NYISO's
  combined-cycle peak band — is capacity EIA-860 states has no duct burner, priced at 2.25× base
  heat rate; removing it costs **zero free parameters** and no DOF entry, and the mechanism lands
  on the builder's own predicted value at all 31 plants with residual 0.000 MW. Nothing here is
  fitted.
* **But the gates do not "regress" — the determination collapses.** CALIBRATED (0 fails) →
  NOT-YET (3 fails), losing **both** load-bearing families the keeper held: C1 and C3a. That is a
  different thing from the precedents the formula was built on. nyiso-193 promoted a NOT-YET over
  a CALIBRATED, but its arm carried **zero `ScenarioConfig` deltas** and fixed a keeper that could
  not be *reproduced at all* — an independent, non-negotiable ground. nyiso-196 promoted an arm that
  **improved** the determination. This arm has neither: it is a one-flag delta whose only claim is
  the structural one, and it trades a clean keeper for three failures.
* **Decisively, rule 14 `[R-ACCURATE]` tells us what to do with this result, and it is not
  "ship it".** Its instruction where an accurate input makes the fit worse is: *"Treat the worse fit
  as a discovered bug: keep the accurate input, **find and fix the real root cause**… Do not bury
  the error back inside an inaccurate input."* Both clauses bind. We do **not** bury it — the
  mis-classification is now measured, registered and documented, and `cc_duct_peaking_row_scoped`
  stays in the codebase (default off) ready to be armed. And we do **not** ship the half-repair
  either: the root cause it exposed — the `CC_REGULAR` vs `ST_GAS` / `CT_PEAKER` merit order — is
  unfixed, and arming the repair alone is what produces the three failures.

**The repair is right and incomplete.** It should be re-armed **paired** with the merit-order fix,
not alone, and that pairing is the next lever. **Keeper unchanged:
`2026-09-06-nyiso-196-extract-basis`.**

## 9.5 What is now known that was not before

1. **The `CC_REGULAR` over-run has a measured, non-offer cause and a measured cost.** Removing
   726.5 MW of phantom duct band moves +1.1 to +1.4 TWh into `CC_REGULAR` in every year — i.e. the
   keeper's C1-2024 `CC_REGULAR` PASS is standing on 726.5 MW of mis-classified capacity. **The
   keeper passes that cell for a reason that is not physical.** That is worth knowing whether or
   not this arm is ever promoted, and it sharpens the class cell from "an over-run" to "an over-run
   currently held in band by a construction defect".
2. **The merit-order object is now sized.** `ST_GAS` −0.7 to −0.9 TWh and `CT_PEAKER` −0.06 to
   −0.31 TWh are what the CC stack absorbs when the artificial constraint is removed; any fix to the
   CC-vs-steam/CT order has to find roughly that much.
3. **Prices carry ~3–4 % of headroom against this one mechanism**, which is the scale of the C3a
   budget in both directions (2024 +4.7 %, 2025 −6.9 %) — so the two are the same problem seen
   twice, and C3a-2025's −6.9 % is not independent slack.

*(nyiso-198 §9, 2026-09-06. Two solves total: the 2024 screen (deleted before merge) and the
2023–2025 span (registered, attested, NOT promoted). No control solve. Keeper unchanged.)*
