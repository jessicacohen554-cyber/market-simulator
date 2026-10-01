# Merchant-CHP host-load research memo (2026-07) — issue #1335

**Scope.** `CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0`
(`src/market_sim/config/constants.py`) is the only entry in that dict without
an independent source — flagged residual-adjacent by the 2026-07 legitimacy
audit (C-4) and tracked as gap G-26 / issue #1335. This memo surveys
candidate primary sources for an independent merchant/IPP host-load estimate
and recommends a path forward. **It does not change the constant** — that is
explicitly out of scope for this hygiene lane (the value feeds dispatch; any
change belongs to a calibration lane with a registered probe, per CLAUDE.md
rule #1 and rule #22).

## Why "merchant" is the hard case

`CHP_SECTOR_CLASS_BY_PLANT` (`src/market_sim/data/fleet.py`) classifies each
CHP plant by its EIA-923 Page-1 sector: **industrial** and **commercial**
plants serve a host behind the meter and export only surplus; **merchant**
(IPP / EIA "Electric Power Sector," NAICS 22) plants primarily sell to the
grid and may or may not carry a smaller behind-the-meter thermal
obligation. The industrial (70%) and commercial (65%) rows are sourced from
EIA's own "Today in Energy" rollup of Schedule-8 fuel-to-useful-thermal-output
(UTO) allocation ("Combined heat and power technology fills an important
energy niche," eia.gov/todayinenergy/detail.php?id=8250) — but that published
article only rolls up the industrial and commercial sectors; it does not
publish an equivalent merchant/IPP figure. That gap, not a flaw in the
approach, is why `"merchant"` still reads "no independent source yet."

## Candidate primary sources

### 1. EIA-923 Schedule 8 raw microdata, filtered to the merchant/IPP plant set (recommended)

Schedule 8 (Annual Environmental Information / Boiler Fuel) is filed by
**every** CHP plant subject to the form, industrial, commercial, and
NAICS-22 Electric-Power-Sector/IPP alike — it is not an
industrial/commercial-only survey. EIA's own methodology notes describe a
per-plant fuel-consumption-to-UTO allocation using **plant-specific reported
efficiency factors** (2016+ vintage; a multi-year average of self-reported
factors from the 2013-2015 surveys for earlier processing), the exact same
mechanism that produced the published 70%/65% industrial/commercial figures.
Nothing in the schedule or its allocation methodology excludes merchant/IPP
respondents — EIA simply never published a merchant-specific rollup the way
it did for industrial/commercial in the "Today in Energy" piece.

**This means the data to compute an independent merchant figure, by the same
method already used for the other two rows, already exists at EIA and is not
currently ingested by this repo** — `src/market_sim/data/eia923.py` reads
EIA-923 for delivered fuel cost but does not currently pull Schedule 8's
UTO/fuel-allocation fields. The concrete next step: extend the EIA-923 intake
to Schedule 8, filter to the ~15-40 plants `CHP_SECTOR_CLASS_BY_PLANT` already
tags `"merchant"` per ISO, and compute the same
fuel-allocated-to-electric-output share the industrial/commercial rows use.
This is the only candidate that is (a) a plant-level measured input matching
CLAUDE.md rule #13's admissibility test (reproducible from source data, would
regenerate for a forward year), and (b) directly comparable to the existing
industrial/commercial derivation — same form, same methodology, no
cross-source reconciliation needed.

- **Source:** Form EIA-923, Schedule 8 (Annual Environmental Information),
  `eia.gov/electricity/data/eia923/`; methodology notes in the EIA-923
  technical documentation / Electric Power Annual technical notes describing
  the fuel-to-UTO allocation and plant-reported efficiency factors.
- **Effort:** Medium — a new Schedule-8 loader (mirrors the existing
  `data/eia923.py` pattern) plus a filter to the merchant plant-code list
  already in `fleet.py`.
- **Caveat:** Small-N. ERCOT's own `CHP_SECTOR_CLASS_BY_PLANT` lists roughly
  15 merchant plants; other ISOs would need their own EIA-923-derived
  classification (per `chp.py`'s `chp_overrides`/`chp_sector` column, already
  wired for CAISO). A small sample increases the case for reporting a
  distribution (or per-plant overrides via `chp_btm_pct`, which `chp.py`
  already supports) rather than one national scalar — mirroring what CAISO's
  Lever-C re-derivation already does with per-plant `chp_btm_pct` overrides.

### 2. FERC PURPA qualifying-cogeneration-facility rules (18 CFR § 292.205) — structural anchor, not a point estimate

FERC's post-EPAct-2005 cogeneration certification rule sets a **50% aggregate
output safe harbor**: a cogeneration facility's thermal + electrical +
chemical + mechanical output must be at least 50% dedicated to an
industrial/commercial/institutional host to be presumptively "not intended
fundamentally for sale to an electric utility." A facility that is
majority grid-export by design — the defining trait of "merchant" in
`CHP_SECTOR_CLASS_BY_PLANT`'s own taxonomy — therefore structurally sits
*below* that 50% aggregate host-output threshold; it does not, by itself, say
where below 50% the *electric-only* host share lands (the safe harbor is
aggregate output across all forms of energy, not an electric-capacity BTM
percentage). Useful as an upper-bound sanity check (a true merchant plant's
combined host offtake is <50% almost by regulatory definition) and to
confirm the ERCOT plant list's classification (a `CHP_SECTOR_CLASS_BY_PLANT`
entry tagged "merchant" should generally correspond to a plant that either
never sought or does not qualify for QF status on cogeneration grounds) —
not usable on its own to derive 35% or any other specific electric BTM share.

- **Source:** 18 CFR § 292.205(d) (cogeneration facility certification
  criteria); FERC Form No. 556 self-certifications (public, per-plant, filed
  by QF-seeking facilities) as a plant-by-plant cross-check of which
  "merchant" list entries hold or ever held QF status.
- **Effort:** Low (regulatory text) to Medium (per-plant Form 556 lookups for
  the ~15-40 named merchant plants).
- **Caveat:** Structural bound, not a measured percentage; would corroborate
  or flag anomalies in the classification, not size the constant itself.

### 3. DOE/ORNL-ICF Onsite Energy (formerly CHP) Installation Database — plant-level cross-check

The DOE-sponsored, ICF/ORNL-maintained installation database
(`doe.icfwebservices.com`, successor to the CHP Installation Database) lists
individual CHP installations with capacity, technology, fuel, sector/
application, and (for many records) the host facility. It would not by
itself yield a UTO percentage, but it is the most direct way to identify,
for each ERCOT/CAISO "merchant" plant code, the actual host arrangement
(e.g. the well-documented Calpine Pasadena/Phillips Petroleum project, where
a 240 MW merchant cogeneration facility dedicates roughly 90 MW plus 200,000
lb/hr steam to its refinery host — a ~37.5% electric-capacity host share,
notably close to the current 35.0% assumption, though this is one anecdote,
not a statistical sample).

- **Source:** DOE/ICF/ORNL Onsite Energy Installation Database
  (`doe.icfwebservices.com`; historical CHP Installation Database exports
  via `chp.ecatalog.ornl.gov`).
- **Effort:** Low-Medium — a cross-reference exercise against the existing
  merchant plant-code list, not a new ingest pipeline.
- **Caveat:** Sparse/inconsistent host-load reporting across records; best
  used to corroborate or flag individual plants ahead of the Schedule-8
  derivation in (1), not as a standalone national estimate.

### 4. FERC Form 1 / EQR — considered, weak fit

Most merchant/IPP CHP owners are not FERC Form 1 filers (Form 1 targets
major public utilities), and FERC EQR (Electric Quarterly Report) transaction
data reports wholesale electric sales, not steam/thermal host offtake. Ruled
out as a primary source for this specific question; noted for completeness
since it is the natural first guess for "merchant generator financial data."

## Recommendation

**Pursue candidate (1): extend the EIA-923 intake to Schedule 8 and derive
the merchant share directly, by the same method already used for the
industrial (70%) and commercial (65%) rows**, filtered to the plant codes
`CHP_SECTOR_CLASS_BY_PLANT` (and each ISO's `chp_sector` column) already
tags `"merchant"`. This is the only candidate that is independently measured,
reproducible for a forward year (rule #13), and directly comparable in
methodology to the two rows the constant already sits beside — no new
cross-source reconciliation logic is needed, only a new schedule from a form
this repo already partially ingests. Use candidate (3) (installation-database
cross-reference) as a cheap sanity check on the derived figure and candidate
(2) (the FERC 50%-safe-harbor rule) as a structural upper-bound check on the
plant classification itself, both before committing the Schedule-8 derive
script.

Given the small plant count, the derive script should report a distribution
(and consider per-plant `chp_btm_pct` overrides via the existing
`chp_overrides`/`chp.py` mechanism, as CAISO's Lever-C re-derivation already
does) rather than collapsing straight to a second national scalar — a single
national "merchant" percentage may itself be the wrong shape for this sector,
unlike industrial/commercial where the published EIA rollup is already a
verified national aggregate.

**Not done here:** no change to `CHP_BTM_PCT_BY_SECTOR["merchant"]`. That
value feeds dispatch (`data/chp.py:chp_btm_pct`), so replacing it requires a
registered calibration probe under CLAUDE.md rules #1/#9/#11 (structure
first, never fit to the residual) and #13 (rule-13 admissibility), which is
out of scope for this zero-collision hygiene lane.
