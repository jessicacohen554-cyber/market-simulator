# FINDING — nyiso-227: the sub-5-day gas outage family is MEASURED NEAR-INERT for NYISO, and the census that shows it closes the whole availability-side lever family for ST_GAS

**Session:** nyiso-227 · **ISO:** NYISO · **Date:** 2026-09-11 · **ZERO LP.**
**Keeper:** `2026-09-09-nyiso-221-fuelvintage-span`, **UNCHANGED. Nothing armed, no cell promoted.**
**Mechanism:** `unit_outage_short_windows_gas` (row minted by pjm-d4-4, 2026-09-10). NYISO cell
**U → I**.

---

## 0. Headline

The candidate is a genuine rule-14 `[R-ACCURATE]` input-coverage gap — **NYISO's sub-5-day
outage layer is completely empty**, and 438 measured CAMPD full stops of 1–5 days on 77 gas
units at 38 plants reach the LP nowhere. It was worth measuring and it is **cheap, zero-parameter
and forward-regenerable**. It is also, on NYISO's own committed artifacts, **unable to change the
dispatch**:

| class | hours the extra removal could bind, of 8,760 | min headroom in the hours it is live |
|---|---|---|
| **ST_GAS** | **0 / 0 / 0** (2023/24/25) | **2,207 / 1,334 / 1,280 MW** |
| CC_REGULAR | 50 / 32 / 70 (0.6 / 0.4 / 0.8 %) | 23 / 249 / 113 MW |
| CC_CHP | 0 / 7 / 0 | 638 / 663 / 495 MW |

**Zero reach on ST_GAS — the class this lane has been trying to move.** The family would have to
be roughly **20× larger** to touch it. Rule 29 `[R-SCREEN]` (0): the arm does not reach a solve.

## 1. The candidate, and why it looked good

The matrix cell's own protocol (pjm-d4-4) set the test: *"derive this ISO's own gas sub-5-day
family … measure its annual-mean and event-hour MW … before proposing anything."* Done:

    python3 scripts/data/derive_campd_unit_outages.py --iso NYISO --years 2023 2024 2025 \
      --short-windows --short-window-groups gas --merit-order-guard

**438 windows, 38 plants, 77 units, median duration 2.6 d (max 4.9 d — the ≥5-day floor's exact
complement).**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| windows | 136 | 133 | 169 |
| annual-mean MW removed | 208.2 | 191.5 | 280.7 |
| hours with ≥1 event | 4,464 (50.96 %) | 4,728 (53.83 %) | 4,968 (56.71 %) |
| mean MW in event hours | 408.6 | 355.8 | 495.0 |
| peak MW | 2,351.0 | 1,653.1 | 1,800.0 |

Per class, annual-mean MW: ST_GAS 71.1 / 60.3 / 64.7; CC_REGULAR 87.8 / 74.6 / 135.0;
CC_CHP 48.4 / 51.1 / 76.8; ST_CHP 0.8 / 5.6 / 4.2.

**And the coverage gap is total, not partial.** `unit_outage_short_windows` is `False` in the
keeper, and NYISO's coal-scoped short extract `data/raw/campd-unit-outages-short-NYISO.csv` is
**header-only — 1 line, ZERO rows** — because NYISO has no coal. So the sub-5-day layer is not
narrow here; it is **empty**. On a naive energy bound it looked material: the model's own output
in the affected hours is 0.614 / 0.482 / 0.519 TWh of ST_GAS, i.e. **29–37 % of the standing C1
ST_GAS |miss|** (1.669 / 1.369 TWh). That bound is what the next section retires.

## 2. THE SCREEN THAT KILLS IT: a removal can only bite if it eats headroom the model is not using

The naive bound is wrong because it assumes the removed MW were being used. They were not. For
each hour, from **committed artifacts only**:

    avail[h] = fleet_MW − (existing ≥5-day removal)[h]        # the ceiling the LP already faces
    head[h]  = avail[h] − model[h]                            # unused headroom
    binds    = short_family_removal[h] > head[h]

`model[h]` is the keeper's own `hourly/class_hourly_<year>.parquet` (P1); the existing removal is
`data/raw/campd-unit-outages-perunitmerit-NYISO.csv`, the extract `run_config.resolved_inputs`
names as the one the keeper reads (`campd_unit_outages`, sha256 `58799099…`); the fleet
denominator is the union of both extracts' distinct unit capacities — **ST_GAS 9,591 MW,
CC_REGULAR 7,181 MW, CC_CHP 4,714 MW, ST_CHP 514 MW.**

**The proxy is AUDITED, not assumed: `model[h] > avail[h]` occurs in 0 of 26,280 hours in all
nine class-years, max overshoot 0 MW.** The denominator is therefore not too small anywhere the
test is applied, which is the one way this screen could have been wrong.

**The result, per class-year, is the table in §0.** ST_GAS carries **1,280–2,207 MW of unused
headroom in the very hours the short family is live**, against a family whose ST_GAS peak is
1,008 / 1,242 / 1,395 MW and whose ST_GAS annual mean is 60–71 MW.

**The screen is CONSERVATIVE in the direction that matters.** The keeper runs
`unit_outage_extract_basis_share = True`, so the LP applies the removal as the unit's
**capacity share of its bin**, never as raw unit MW. The real removal is therefore ≤ the raw MW
used here, so the true binding-hour count is ≤ the counts reported. Nothing in this finding
depends on the share transform, and arming it cannot make the family bite more.

## 3. WHY IT IS INERT — and this is the part that generalises

ST_GAS in this keeper is **not availability-constrained at any point in the year**:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| ST_GAS energy (model) | 9.827 TWh | 8.581 TWh | 9.477 TWh |
| hours with ST_GAS on | 8,760 (100 %) | 8,736 (99.7 %) | 8,760 (100 %) |
| mean MW when on | 1,121.9 | 979.6 | 1,081.9 |
| **mean unused headroom** | **3,641 MW** | **3,205 MW** | **3,121 MW** |
| p99 / max MW | 4,894 / 6,356 | 6,101 / 6,846 | 6,121 / 7,464 |

The class runs in essentially every hour of the year at ~11 % of its fleet, with 3.1–3.6 GW of
derated capacity sitting unused in the mean hour. **Whatever sets NYISO ST_GAS output in this
model, it is not the availability layer** — it is the offer curve and the floors.

**Therefore (the DO-NOT-REDO half): every availability-side lever aimed at NYISO ST_GAS is inert
by this same census, not just this one.** A future lane proposing to add, widen, re-derive or
re-base any ST_GAS *availability* input should run the three-line headroom test above first and
expect 0 binding hours. The live ST_GAS objects are the **offer curve** and the **reliability
floor** (C8 forced share 0.161 / 0.209 / 0.181), and nothing here touches either.

## 4. What is reported against this finding, rather than buried

- **CC_REGULAR is not zero.** 50 / 32 / 70 hours a year could bind, with min headroom of
  23 / 249 / 113 MW at CC peaks. That is real but tiny, it is not the class under pressure, and
  it does not by itself justify an LP. If a future lane arms this family for a CC-side reason,
  **these are the hours to pre-register**, and the arm should be expected to be near-inert.
- **The composition question is NOT settled and is not claimed to be.** NYISO's existing ≥5-day
  gas outage layer removes, as an annual-mean share of fleet MW, **CC_REGULAR 26.6 %,
  CC_CHP 29.4 %, ST_GAS 50.4 %, ST_CHP 24.5 %** (2023; lay-up is a *separate* extract and is
  excluded). Published NERC GADS 2023 is COMBINED CYCLE **FOR 5.46 / EFORd 5.02** and FOSSIL Gas
  Primary **FOR 19.72 / EFORd 15.63**. Those are **not like-for-like** — the model's extract mixes
  forced with planned (median window 12–15 d is maintenance-length), while GADS FOR is forced-only
  and **NERC-wide, not NYISO** — so this is a **flag, not a finding**, and no conclusion is drawn
  from it here. It is recorded because a successor asking "is the availability budget already
  spent?" should start from these numbers, and because the like-for-like statistic that would
  settle it (a NYISO-specific planned/forced composition, or GADS EAF/POF) **is not in this repo**.
- **The cell's third protocol leg was UNAVAILABLE, and that is stated rather than substituted.**
  It asks for *"the per-stratum correlation sign against this ISO's own published FORCED series"*.
  **NYISO publishes no unit-typed forced-outage series we hold** — there is no `nyiso-outages`
  corpus (PJM and MISO have one; NYISO does not), and the Gold Book carries planning-class EFORd,
  not an event series. The identification leg is therefore **not performable for NYISO**, exactly
  as the cell's own text anticipated. The verdict here rests on the headroom census instead, which
  is a *stronger* test for this purpose: it does not ask whether the input is right, it shows the
  input cannot reach the LP's answer.

## 5. Rules

- **Rule 1 `[R-STRUCT]`** — nothing was decided on a residual. The kill is a reach test on the
  model's own committed dispatch; it would read the same whatever the residual did.
- **Rule 14 `[R-ACCURATE]`** — the input is accurate and the gap is real. It is not rejected as
  *wrong*; it is reported as **inert**, which is a different cell (`I`, not `R`) and a different
  claim. If a future structural change opens ST_GAS headroom, this family becomes live again and
  should be re-tested — that is why the census, not a verdict, is the artifact.
- **Rule 29 `[R-SCREEN]` (0)** — the zero-LP phase-0 killed the arm before a solve. No screen
  year was named and no LP was spent, which is the rule working as intended.
- **Rule 30 `[R-MECH-MATRIX]` (b)/(d)** — the NYISO cell is updated in this session. The verdict
  is NYISO's alone and fills no other ISO's cell; PJM's own verdict on this row is untouched.
- **Rule 31 `[R-RETAIN]`** — nothing deleted. The derived extract lives in this session's
  scratchpad and is **deliberately not committed**: it is an un-armed diagnostic, and committing a
  per-ISO artifact for a mechanism no keeper reads would be an unregistered input channel in
  spirit (rule 24 `[R-REGISTRY]`). Reproducing it is the one derive command in §1, ~4 minutes.
