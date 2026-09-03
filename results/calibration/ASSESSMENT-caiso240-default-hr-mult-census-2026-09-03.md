# ASSESSMENT — caiso-240: the `_DEFAULT_HR_MULT_BY_GROUP` CENSUS, measured on all six keepers

**Session caiso-240, 2026-09-03.** Pre-registered in
`PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md` (`bfa6999a`, pushed
before any footprint measurement) and
`PRECOMMIT-caiso240-ADDENDUM-arm-2026-09-03.md` (`30389e1a`, pushed before the
solve). Instrument: `scripts/probes/_caiso240_default_hr_mult_census.py` →
`results/calibration/_caiso240_default_hr_mult_census.json`. **The census itself
is ZERO SOLVES**; the one arm it authorises is scored separately.

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read and the whole solve stayed inside **2023–2025**.

---

## §1 — HEADLINE

**Of the 28 uncited literals, 26 are DEAD or economically INERT on the six
designated keepers, and the live remainder is not where anyone expected it.**

* **Five of the seven `mr` literals are DEAD BY CONSTRUCTION**, not by
  configuration: `bins_to_fleet` sets `mustrun_cap > 0` only for non-CHP coal, so
  no gas group ever builds a must-run tranche and its `mr` literal can never
  reach the LP. **Prediction P-1 survives its own falsifier but its reasoning was
  wrong** — I expected the `mr` exposure to sit across the gas groups, and it is
  entirely COAL. Scored against interest in §6, alongside the two predictions
  (P-4, P-6) that are outright falsified.
* **The one `mr` literal that IS live — `COAL:mr` on ERCOT, 10 tranches /
  3,649.6 MW — is PRICED-BUT-INERT**: its heat rate moves with the literal and
  its assembled marginal cost does not, because the coal `_mustrun` tranche's
  fuel is sunk under take-or-pay. Structural liveness without economic liveness
  is a distinction this census had to invent to report honestly, and it is
  ERCOT's only live cell of 28.
* **THE REAL OFF-REGISTRY EXPOSURE IS `ST_CHP`, AND IT IS NOT CAISO'S.**
  **No keeper of any of the six ISOs configures an `ST_CHP` offer curve**, so
  `ST_CHP`'s `mc` (1.10), `econ` (1.00) and `peak` (1.10) literals are the sole
  price of every ST_CHP tranche in NYISO, NEISO, MISO and PJM. Under rule 25
  `[R-ISO-SCOPE]` these are **asks for those lanes, never arms here**.
* **CAISO's own remaining exposure is TWO cells**, both on the same three
  once-through-cooling steamers caiso-239 studied, reached through the same
  bypass: `ST_GAS:econ` = 1.00 (2,240.8 MW) and `ST_GAS:peak` = 1.10 (428.8 MW).
* **The peak one is armed and solved** — `caiso_st_gas_peak_measured`, gated
  default off — because its measured counterpart, **1.166**, is *already the
  value the CAISO ST_GAS class band carries*, armed at caiso-231 on the CT
  bucket that `derive_caiso_offer_surface.py` says **contains these very
  steamers**. The bypass withholds the measurement from its own population and
  applies it instead to two EIA-860 retired-window units. **That is caiso-239's
  structural inversion again, one band over.**
* **The econ one is REFUSED at this grain** — larger, and not armed. Its
  counterpart is a two-endpoint ramp against a single flat model band; choosing
  an endpoint would be a free parameter.

---

## §2 — THE INSTRUMENT, AND ITS TWO PRE-REGISTERED FALSIFIERS

The caiso-238 error — grading a scalar from the band dict alone — is made
**structurally impossible**: each of the 28 cells is scaled by its **own unique
probe factor** (1 + k·10⁻⁴) and every LP row's **heat-rate ratio** is read back,
so a row's cell is *identified by measurement*, never inferred from its group or
its name. A second uniform ×1.25 pass catches clip-suppression. Heat-rate
response (structural liveness) and marginal-cost response (economic liveness) are
reported **separately**.

* **M-1 (null pass) — PASS.** A baseline→baseline rebuild of the CAISO keeper is
  byte-identical in `unit_ids`, `heat_rate` and `mc_base` across all 1,801 rows.
  The cache hazard declared in precommit §3.3 does not bite.
* **M-2 (two-point validation) — PASS.** The `ST_GAS.mc` cell is responsive on
  **exactly 3** tranches — plants 315 / 335 / 350 — in every year on the
  **caiso-231 predecessor recipe**, reproducing caiso-239 F-1 exactly; and on
  **ZERO** tranches in every year on the **caiso-239 keeper**. The instrument is
  validated *and* caiso-239's repair is independently confirmed to have retired
  the literal it claimed to retire.

---

## §3 — THE ROUTE CENSUS (source + committed config, zero compute)

Which code paths can reach a cell at all. It fixes where to look; §4 measures
what is there.

**Two consumption sites, very different reach.**
* **Site A — `campd_bins.py:1063`**, ERCOT's curated-CSV path
  (`plant_level_fleet=False`). A **blank-cell fill** only:
  `_fill_hr_multiplier(csv, default)` uses the literal only where the sheet's
  `HR_Mult_<tranche>` cell is blank. Measured on
  `data/raw/reference/custom-bin-assignments.csv` (304 rows): 259 blank
  `HR_Mult_Must_Run`, 46 blank `HR_Mult_Committed`, 15 blank `HR_Mult_Peaking`,
  **0** blank `HR_Mult_Economic`.
* **Site B — `campd_bins.py:2337`, in `fleet_to_bins`**, the per-plant path used
  by PJM / CAISO / NYISO / NEISO / MISO. **All four** band heat rates are set
  unconditionally from the literals.

**What `bins_to_fleet` then overrides.** `committed_hr`, `peak_hr` and the econ
tranche(s) are replaced **only when `_offer_curve_for_group` resolves**;
`mustrun_hr` is **never** overridden by an offer curve, and
`gas_offer_margin_markup_mult` returns 0 for the `mustrun`/`sync` suffixes, so a
must-run tranche is outside the `gas_offer_net_revenue_margin` decomposition too.
That made the `mr` family look like the census's largest exposure — until §4
measured that gas must-run capacity is identically zero.

**The bypass set** (`offer is None`): a group absent from the ISO's
`offer_curve_by_group`; `ST_GAS` ∩ `ST_GAS_PEAKER_PLANTS`; COAL resolving neither
a supply-specific nor a generic entry. Read off the six committed
`run_config.json`s:

| ISO | keeper | path | groups with NO offer-curve key |
|---|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | A | **ST_CHP, COAL** |
| PJM | `2026-08-15-pjm-162-inputclock` | B | **ST_CHP** |
| CAISO | `2026-09-02-caiso-239-b1-stgas` | B | **ST_CHP** |
| NYISO | `2026-09-02-nyiso-177-vintage-matched` | B | **ST_CHP** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | B | **ST_CHP** |
| MISO | `2026-09-02-miso-201-stbasis` | B | **ST_CHP** |

`econ_split_by_group` is `{}`, `plant_tranche_config_path` is `None` and all
three `gas_st_*_hr_override`s are `None` on **all six**.

**The 29th exposure is DEAD BY CONSTRUCTION.** Both sites fall back to
`_DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"]` for a `Plant_Group` absent from the
dict — but the dict's seven keys are exactly `eia860.BIN_GROUP_TO_FUEL`'s, and a
row that is not in `BIN_GROUP_TO_FUEL` is never binned as thermal. The fallback
is unreachable.

---

## §4 — THE MEASURED CENSUS

Each ISO measured on **its own designated keeper** (rule 25), 2023 / 2024 / 2025;
the table is 2023 and the pattern is stable across years except where noted.
`tranches` = LP rows whose **heat rate** the cell sets (structural liveness);
`mc-live` = of those, the rows whose **assembled marginal cost** also moves
(economic liveness).

| ISO | keeper | fleet rows | live cells | the live cells |
|---|---|--:|--:|---|
| **ERCOT** | `2026-08-25-234-eastex-identity` | 1,780 | **1 / 28** | `COAL:mr` — 10 tranches, 3,649.6 MW, **0 mc-live** |
| **PJM** | `2026-08-15-pjm-162-inputclock` | 3,279 | **4 / 28** | `COAL:mr` 52 tr / 10,393.3 MW / **20** mc-live; `ST_CHP:mc` 23 tr / 101.6 MW; `ST_CHP:econ` 12 tr / 58.8 MW; `ST_CHP:peak` 3 tr / 17.8 MW |
| **CAISO** | `2026-09-02-caiso-239-b1-stgas` | 1,801 | **2 / 28** | `ST_GAS:econ` 3 tr / 2,240.8 MW; `ST_GAS:peak` 3 tr / 428.8 MW |
| **NYISO** | `2026-09-02-nyiso-177-vintage-matched` | 812 | **3 / 28** | `ST_CHP:mc` 3 tr / 106.9 MW; `ST_CHP:econ` 1 tr / 170.1 MW; `ST_CHP:peak` 1 tr / 46.4 MW |
| **NEISO** | `2026-08-17-neiso-99-joint-p1` | 817 | **3 / 28** | `ST_CHP:mc` 7 tr / 18.1 MW; `ST_CHP:econ` 1 tr / 2.8 MW; `ST_CHP:peak` 2 tr / 1.6 MW |
| **MISO** | `2026-09-02-miso-201-stbasis` | 3,077 | **4 / 28** | `COAL:mr` 61 tr / **12,709.0 MW** / **15** mc-live; `ST_CHP:mc` 46 tr / 419.0 MW; `ST_CHP:econ` 27 tr / 186.0 MW; `ST_CHP:peak` 13 tr / 97.1 MW |

**Six distinct cells are live anywhere. TWENTY-TWO OF THE TWENTY-EIGHT ARE
MEASURED DEAD IN EVERY ONE OF THE SIX ISOs.** No cell was clip-suppressed (the
×1.25 pass adds no rows anywhere), and no row moved at a ratio other than its own
cell's probe factor (`indirect = 0` everywhere), so the attribution is exact.

### §4.1 — The three structural facts behind that table

1. **Five of the seven `mr` literals are DEAD BY CONSTRUCTION.**
   `assembly.py:487` sets `mustrun_cap = nameplate × pct_mr/100` only when
   `fuel == "coal" and coal_chp_sector is None`; every other bin gets
   `mustrun_cap = 0.0` and its must-run tranche is skipped. On the per-plant path
   `fleet_to_bins` reinforces it — `pct_mr = mustrun if group == "COAL" else
   d_mr`, and `_DEFAULT_TRANCHE_PCT_BY_GROUP` gives `d_mr = 0.0` for all six gas
   groups. So `CC_CHP:mr`, `CC_REGULAR:mr`, `CT_CHP:mr`, `CT_PEAKER:mr`,
   `ST_GAS:mr` and `ST_CHP:mr` cannot reach the LP in any ISO under any
   configuration these keepers use. **This is the census's cleanest result and it
   falsifies my own prediction's reasoning** (§6, P-1).
2. **`COAL:mr` is the largest exposure by MW and mostly PRICED-BUT-INERT.** It
   sets the heat rate of 12,709.0 MW (MISO), 10,393.3 MW (PJM) and 3,649.6 MW
   (ERCOT) of coal min-load — but the `_mustrun` tranche's fuel is **sunk under
   take-or-pay** and it bids VOM + carbon + NOx only, so its assembled marginal
   cost does not move with the literal. Measured: **0 of 10** ERCOT tranches,
   **20 of 52** PJM, **15 of 61** MISO are economically live. PJM's higher share
   is its `coal_sync_srmc_tranche = True` (the only keeper that arms it), which
   splits coal min-load into a fuel-free `_mustrun` and a full-SRMC `_sync` band
   — and `_sync` takes the same `mr` heat rate. The literal's value is **1.00**,
   an identity multiplier, which is why the exposure is a *provenance* problem
   (an uncited modelling assumption on 12.7 GW) rather than a level error.
3. **`ST_CHP` IS THE OFF-REGISTRY CLASS. No keeper of any ISO configures an
   `ST_CHP` offer curve**, so all three of its reachable literals price every
   ST_CHP tranche in four ISOs: MISO (46 / 27 / 13 tranches on mc / econ / peak),
   PJM (23 / 12 / 3), NEISO (7 / 1 / 2) and NYISO (3 / 1 / 1). CAISO has no
   ST_CHP plant; ERCOT's two are measured dead. Per-ISO capacity is modest
   (419.0 MW is the largest, MISO's `ST_CHP:mc`), but this is the only class in
   the model whose **entire offer surface** is uncited literals.

---

## §5 — THE PER-CELL GRADES AND THE ASKS

Graded under the precommit §5 taxonomy, **footprint first**.

| cell | ISOs live | grade | the ask |
|---|---|---|---|
| the six gas `mr` cells | none | **F0 — DEAD BY CONSTRUCTION** | none. Recorded with the condition that would make them live: a `pct_mr > 0` for a gas group, which no code path can currently produce. |
| `COAL:mr` = 1.00 | ERCOT, PJM, MISO | **F3 at the model's grain** | **no arm.** A measured counterpart for a *min-load* burn ratio exists (`avg_committed_p50`), but the model splits the min-load region into `mr` + `mc` while the measurement reports ONE number for the whole at-or-below-LSL band — a grain mismatch, and the identity value 1.00 is a modelling assumption (min-load priced at plant-average HR) rather than a fitted level. **The honest ask is a CITATION, not a value**: name the assumption and its source in `campd_bins.py`, and record it in the affected ISOs' DOF ledgers. That is a PJM/MISO/ERCOT-lane item (rule 25). |
| `COAL:mc` / `COAL:econ` / `COAL:peak` | none | **F0 — DEAD** | none. ERCOT has no COAL offer-curve key at all, yet its curated bin sheet populates `HR_Mult_Committed` / `_Economic` / `_Peaking` for all 10 coal rows, so the blank-cell fill never fires. **P-5 confirmed.** |
| `ST_CHP:mc` = 1.10 | PJM, NYISO, NEISO, MISO | **F2 in MISO, F3 elsewhere** | **a data-intake ask for those lanes.** Only MISO's `campd_marginal_hr_summary.csv` carries an `ST_CHP` row at all, and it is `n_units = 1` (`avg_committed_p50` 1.803) — a single unit standing for 46 tranches, which is a thin basis and is reported as such. PJM / NYISO / NEISO have **no ST_CHP row**, so no counterpart exists to arm. |
| `ST_CHP:econ` = 1.00 | PJM, NYISO, NEISO, MISO | **F3** | none. Same flat-band-vs-ramp grain mismatch as `ST_GAS:econ` below. |
| `ST_CHP:peak` = 1.10 | PJM, NYISO, NEISO, MISO | **F3** | none. No measured peak-band object exists for ST_CHP in any ISO's committed artifacts. |
| `ST_GAS:econ` = 1.00 | **CAISO** | **F3 at the model's grain** | **no arm, and this is the census's one close call.** Footprint is CAISO's *largest* (2,240.8 MW, 15,958.8 GWh available) and the population is exactly plants 315/335/350. But every measured counterpart is a **two-endpoint ramp** — the class's measured bid `econ_low` 1.145 / `econ_high` 1.166, or the physical `marg_econ_low` 0.725 / `marg_econ_high` 0.755 — while the bypassed plant's band is a **single flat multiplier**. Choosing an endpoint is a free parameter, which precommit §6(3) forbids. Its F1 route is named in §5.1. |
| `ST_GAS:peak` = 1.10 | **CAISO** | **F1 — GROUNDABLE NOW** | **ARMED AND SOLVED** (§8). |
| `ST_GAS:mr`, all four `CC_*`/`CT_*` non-`mr` cells | none | **F0 — DEAD** | none. Every CC/CT group resolves an offer curve in every keeper, so `mc` / `econ` / `peak` are overridden before the literal can price anything. **P-2 confirmed: no responsive `mc`/`econ`/`peak` row anywhere for a group that resolves a curve.** |

### §5.1 — The `ST_GAS:econ` F1 route, and why it is NOT this session's to take

Rendering the measured ramp for the bypassed plants — `_econ_curve_steps(base_hr,
1.145, 1.166, econ_cap, n = 6, exp = 1.0)` — would use **zero free parameters**
(both endpoints measured; `n` and `exp` are the keeper's own registered values,
and `econ_low_share` is not consulted when `n > 0`). But it changes the band's
**grain**, one flat tranche to six slices, which is a mechanism change and not
the zero-free-parameter *substitution* F1 is defined as. Its measured adverse
bound is already computed and on record for whoever takes it:
**+0.0108 / +0.0084 / +0.0044 $/MWh** (`_caiso240_cell_bound.json`), i.e. ~8×
the armed cell's and still ~1 % of 2024's required move.

**A second, deeper reason to put it to the owner rather than take it.** The
bypassed plants carry `offer_markup_hr = 0` — `bins_to_fleet` computes the
markup only when `offer is not None` — so they are outside
`gas_offer_net_revenue_margin` entirely and price fully fuel-scaled. Setting
their econ band to the **physical** basis (0.725 / 0.755) would have them offer
at cost with **no** net-revenue margin while every other CAISO gas tranche
offers at bid with its markup compressed to a fixed $/MWh; setting it to the
**bid** basis (1.145 / 1.166) without the margin decomposition gives them a
fully fuel-scaled markup nobody else has. **Neither is right on its own** — the
complete repair is the §7 split, and the §7 split is dependency-blocked on
caiso-239's refusal of the class `committed` band. **The CAISO census converges
on §7**, which is why §7 is the substantive ask this session leaves.

---

## §6 — THE PREDICTIONS, SCORED AGAINST INTEREST

| # | prediction | verdict |
|---|---|---|
| **P-1** | an `mr` cell live on ≥ 10 tranches on the plant-level ISOs, and the `mr` family's live capacity exceeding the `mc` family's | **HOLDS ON ITS FALSIFIER, WRONG ON ITS MECHANISM.** 61 MISO tranches and 12,709 MW vs the `mc` family's ~545 MW, so the falsifier does not fire. But I predicted the exposure would be *across the gas groups*, on the strength of the (correct) route fact that no offer curve ever overrides `mustrun_hr`. It is **entirely COAL**: five of the seven `mr` literals are dead by construction, and the one live cell is mostly priced-but-inert. The prediction was right for the wrong reason and is recorded that way. |
| **P-2** | `mc`/`econ`/`peak` live ONLY inside the bypass set | **HOLDS.** Every live `mc`/`econ`/`peak` row is `ST_CHP` (no curve in any keeper) or CAISO `ST_GAS` (the `ST_GAS_PEAKER_PLANTS` bypass). Zero exceptions in 18 ISO-years. |
| **P-3** | `ST_CHP`'s three bypass cells live in ≥ 1 ISO | **HOLDS**, in four. |
| **P-4** | ERCOT's responsive tranche count below the median of the five plant-level ISOs | **FALSIFIED, narrowly and by a tie.** Responsive rows: NYISO 5, CAISO 6, **NEISO 10**, PJM 90, MISO 147 → median **10**; ERCOT is **10**, i.e. *at* the median, not below. The underlying claim — that site A's blank-cell rule makes ERCOT's exposure smaller than a per-plant ISO's — is true of PJM and MISO and false of the three small ISOs, whose fleets simply contain few bypassed plants. The falsifier is called as written. |
| **P-5** | `COAL:mc` / `COAL:peak` dead or near-dead on ERCOT despite the missing COAL key | **HOLDS** — exactly zero responsive ERCOT coal `mc`/`peak` tranches. |
| **P-6** | CAISO's largest live cell by capacity is in the `mr` family | **FALSIFIED.** CAISO has **no** live `mr` cell at all, and its largest live cell is `ST_GAS:econ`. |
| **P-7** | the DOF ledger does not move | scored in the FINDING after the arm's ledger rebuild. |

**Two predictions falsified, one right for the wrong reason, three confirmed.**
The two misses (P-4, P-6) both come from the same error — reasoning about the
`mr` family from the *route* (no offer curve overrides `mustrun_hr`) without
first measuring whether any gas must-run tranche exists. That is the caiso-238
error in miniature, made by the same session that built the instrument to prevent
it, and it is only visible because the instrument was built.

---

## §7 — SECOND OBJECT: the `ST_GAS_PEAKER_PLANTS` double duty — PROPOSE ONLY

### §7.1 — It is not a double duty. It is SIX scopes on one frozenset.

`data/outages.py::ST_GAS_PEAKER_PLANTS` = 9 plants — ERCOT {3504 Stryker Creek,
3453 Mountain Creek, 3490 Graham, 3507 Trinidad, 3576 Ray Olinger, 4266 Spencer}
and CAISO {315 AES Alamitos, 335 AES Huntington Beach, 350 Ormond Beach}. Its
docstring names two duties. The code has six consumers, and on the CAISO keeper
only two are live:

| # | scope | consumer | live on the CAISO keeper? |
|---|---|---|---|
| S1 | outage-overlay exclusion | `scripts/data/derive_campd_unit_outages.py` (864, 1585, 1971) | **LIVE**, and DERIVE-TIME — baked into the committed artifacts |
| S2 | reliability min-gen floor exclusion | `data/fleet/floors.py:264`, under `gas_st_netload_drag` | **INERT** — that flag is `False` on CAISO (True only on ERCOT and PJM) |
| S3 | offer-curve bypass | `data/offer_curves.py:193` | **LIVE** — the caiso-239 / caiso-240 channel |
| S4 | econ-split bypass | `data/offer_curves.py:243` | **INERT** — `econ_split_by_group = {}` on all six keepers |
| S5 | `gas_st_*_hr_override` scope guard | `assembly.py:782`, `offer_curves.py:1044` | **INERT** — all three overrides `None` on all six |
| S6 | ERCOT drag-seasonal derive scope | `scripts/data/derive_ercot_stgas_drag_seasonal.py` | ERCOT-only, derive-time |

**The rule-19 finding, sharpened.** `_offer_curve_for_group`'s docstring
justifies S3 by *"matching the `gas_st_*_hr_override` scope"* — that is **S5**,
and S5 is inert in **every one of the six keepers**. The offer bypass's only
*stated* warrant is a scope no keeper exercises. Its real, unstated warrant is
S1's: these are run-when-called reliability units whose CEMS record the
event-based outage rule cannot read. Whether that also justifies denying them an
offer curve has never been argued anywhere in the codebase.

S1 corroborated from committed artifacts, zero compute: plants 315 / 335 / 350
have **zero rows** in `campd-unit-outages-CAISO.csv`, `-layup-`, `-short-` and
`campd-partial-outages-CAISO.csv`. The exclusion is already materialised in the
data, not merely a runtime branch.

### §7.2 — What a split would cost: it REVERSES caiso-239

Splitting S3 out means giving 315 / 335 / 350 the CAISO `ST_GAS` offer curve,
which on the keeper is `{committed 0.81, econ_low 1.145, econ_high 1.166,
peak 1.166, econ_low_share 0.5, pct_peaking 15.0, phys_* …}`. That would:

1. **Move their committed band from the caiso-239 measured 1.683 to the refused
   0.81** — undoing the current keeper's structural repair and re-imposing, on
   those exact plants, the scalar caiso-239 refused on three independent measured
   grounds. Not a side effect: a **hard dependency**. The split is inadmissible
   until the class `committed` band is itself re-grounded, and that is a
   DO-NOT-REDO item.
2. **Replace their single flat econ tranche (× 1.00) with a rising ramp
   1.145 → 1.166 sliced `offer_curve_smoothing_n = 6`** — +14.5 % to +16.6 % on
   the econ band of 2,240.8 MW, and the split's largest limb. **ADVERSE.**
3. **Move their peak band 1.10 → 1.166** (+6.0 %) — which is exactly what
   caiso-240's armed mechanism does *without* limbs 1 and 2.
4. **Newly subject them to `gas_offer_net_revenue_margin`**: that mechanism keys
   on `offer_markup_hr`, which `bins_to_fleet` computes only when
   `offer is not None`, so today these plants carry markup 0 and price fully
   fuel-scaled. A second structural change riding on the first — which rule 19
   says should not be bundled.
5. **`pct_peaking`: identity.** The curve's 15.0 equals
   `_DEFAULT_TRANCHE_PCT_BY_GROUP["ST_GAS"][2] = 15.0`. Reported so the blast
   radius is not overstated.

### §7.3 — The recommendation: NOT the split. The zero-blast-radius half of it.

**Do not arm a split of S3 in its current form**: dependency-blocked on an
adjudicated refusal (1), bundles two mechanisms (4), and its largest limb (2) is
an adverse move on a band with no counterpart at the model's grain.

**What IS a clean rule-19 repair and costs nothing:** give the offer-side scope
its **own named frozenset**, seeded byte-identically —

```python
# data/outages.py
ST_GAS_PEAKER_PLANTS: frozenset[int] = frozenset({...})           # S1/S2/S6: availability
ST_GAS_OFFER_BYPASS_PLANTS: frozenset[int] = ST_GAS_PEAKER_PLANTS  # S3/S4/S5: offer side
```

with `_offer_curve_for_group`, `_econ_split_for_group` and the two
`gas_st_*_hr_override` guards re-pointed at the second name. **Gate: byte
identity** — the two sets are equal at introduction, so every solve in every ISO
is provably unchanged, verifiable by a source diff plus a fleet rebuild with zero
differing rows and **no LP run at all**. It separates the phenomena, makes each
scope independently editable and citable, and leaves the substantive question
open for a session that can also answer §7.2(1).

**Cost:** one PR, four call-site edits, two unit tests (the sets are equal at
introduction; the offer path reads only the offer-side name). **No solve, no
bundle, no registration.** A refactor with a proof, not a mechanism change.

---

## §9 — CARRIED, PROPOSE-ONLY, NOT STARTED

caiso-238 object 4 (`battery_dispatch_adder` → measured AS reservation + ATB
degradation; F2, and the strongest standing ask — materiality COMPOUNDING,
li-ion 1.87 → 5.29 % of generation), object 3 (own-curve shape derive), the
SoCalGas OFO arm (`PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`), and the
`IMPORT_TRANCHES[CAISO]` LEVEL object.
