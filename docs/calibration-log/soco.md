# Calibration Log — SOCO

Per-region continuation of `docs/calibration-log.md` (frozen archive, entries through 2026-07-19) for
the **SOCO balancing authority** — Southern Company Services, Inc. – Trans (EIA-930 / EIA-860 BA code
`SOCO`, NERC SERC), which dispatches **Alabama Power, Georgia Power and Mississippi Power** as one
pooled, cost-based system under the Intercompany Interchange Contract. **SOCO is a single balancing
authority, not an RTO/ISO** — no day-ahead market, no LMP, no capacity auction, no ancillary-service
market, no offer cap; every name downstream still says "ISO". Entry format matches the other per-region
logs — `## <lane> — YYYY-MM-DD — title`, **newest at the BOTTOM**. Only this region's lanes appear
here, so parallel per-ISO sessions never conflict (the per-ISO lane convention, 2026-07-19; see
`frontend/data/backcast/keepers/README.md`).

Entries are appended **verbatim** by the SOCO ADDITION DESK from each lane's FINDING `## Log entry`
section (plan §8.0 rule 1 — **a lane never writes this file**). Newest last.

Program: `docs/multi-iso/soco-addition-plan-2026-09.md` (definition of done, owner cards S1–S12, wave
graph W1–W6, lane table, fetch manifest, hard gates, prompt pack). Desk handoff
`docs/handoffs/soco-desk-handoff-2026-09-12.md`; desk ledger
`docs/handoffs/soco-desk-ledger-2026-09.md` — **the ledger wins where the two diverge**. Phase-0
census: `docs/multi-iso/soco-data-audit.md`. Lever queue: `docs/mechanism-testing-matrix.md` §5.8
(NWPP is §5.9 — SOCO's shard landed first, on 2026-09-13 by lane SOCO-21, so SOCO is the **eighth
matrix shard** even though it is the **ninth builder**; the two orderings cross and both are correct);
cell verdicts `docs/codebase-site/data/mechanism-matrix/SOCO.js`.

**Next shorthand: soco-35.** Headings in this file carry the lane's own number, so a lane chartered in
the plan's §5 table keeps that number (W3's SOCO-30/31/32/33, W4's SOCO-40, W5's SOCO-54–57); soco-35
is the next free number for a lane the table does not name.

## Lane state (header refreshed 2026-09-16, lane SOCO-34)

**No keeper exists.** SOCO was registered as the **ninth** region on 2026-09-14 by lane SOCO-20
(`docs/handoffs/FINDING-soco-20-2026-09-14.md`), so `frontend/data/backcast/keepers/SOCO.json` does
not exist, no bundle has been solved, and there is no run to score, no determination and no gates. The
first-ever solve and the first keeper are lane **SOCO-40**'s. Training window **2023–2025**, and rule
16 `[R-ALLYEARS]` binds from day one: a single-year SOCO keeper is refused, and lane SOCO-40 runs
**one shard, one `--year 2023 2024 2025` invocation, one bundle** (rule 32 `[R-SHARD]`(b)).

**Region count measured at this refresh:** `config/iso_configs._ISO_BUILDERS` carries **NINE** regions
— ERCOT CAISO MISO PJM NYISO NEISO SPP **NWPP SOCO**. NWPP and SOCO both registered 2026-09-14; NWPP
merged first, so SOCO is the ninth builder. Derived topology totals over the nine: **47 zones, 44
carrying load, 58 links**. Seven keeper shards exist (neither NWPP nor SOCO has one). Prose saying
"seven ISOs" is stale, and prose saying "eight" was true only between the two merges.

**No year is protected, and no SOCO number will be a certified out-of-sample number.** Rule
`[R-HOLDOUT]` was **removed** 2026-09-09 (owner instruction; CLAUDE.md rule 22's coda — that ordinal
now carries `[R-C3C]`). Any year may be solved, scored and registered with no authorization, no marker
and no one-shot. The cost is stated rather than hidden: nothing is held back from being iterated
against, so every SOCO run is model-**selection** evidence and a skill claim built on a year that has
been tuned against is not a skill claim. Say what a number is when quoting it. Sibling logs that still
cite "rule 22 `[R-HOLDOUT]`" as live (`spp.md`) predate the removal.

Facts every SOCO session inherits, so nobody rediscovers one in a residual:

- **THERE IS NO SOCO PRICE, and the rubric already knows it.** Owner card **S2** is the program's
  load-bearing card precisely because a cost-based BA publishes no LMP, no zonal price, no spread and
  no congestion archive. Lane **SOCO-13** was chartered to build a candidate series under a STOP gate
  pre-registered before any data was read, and it **read NO**
  (`docs/handoffs/FINDING-soco-13-2026-09-13.md`): D2.2 failed every year (3.66 / 2.69 / 2.64 % vs a
  ≥ 5 % bar), D3.1 failed 2024 and 2025 (+54.2 / +72.1 % vs ±15 %), D4.2 failed 2025. **No bar was
  moved after the series was seen and nothing landed to `_validation-source`.** So a SOCO run reads a
  determination **naming its own basis, never a bare `CALIBRATED`**: rubric **v3.8**'s
  `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` / `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`,
  keyed on the absence of an `actual_lmp.json` block — landed by lane **SOCO-22**, which re-scored all
  seven keepers byte-identically, and since adopted by NWPP. The zones are validated on **load and
  dispatch only**.
- **Both transmission links are Tier-3 placeholders that cannot bind.** No public inter-OpCo transfer
  limit exists *structurally*: the Operating Companies "function as a single, integrated public-utility
  system" and are "committed and dispatched as a common System without regard to the ownership of each
  generating facility" (FY2025 10-K), so they publish no internal interface rating. AL↔GA 24,400 MW
  and AL↔MS 4,300 MW are each the smaller side's EIA-860 2025 winter capability — an upper bound on
  any physically possible flow, on the SPP-20 precedent. The real values are pre-declared lever
  **SOCO-54**, which has **no public source and no price signal to validate against**. Never tune a
  placeholder to a residual (rules 1 / 13 / 14), and never sell the three-zone split as improving
  accuracy (card S3 condition (iii)) — until a link binds, a three-zone and a one-zone SOCO produce
  the same dispatch.
- **The static `load_share`s are a fleet-MW fallback, NOT load shares.** 0.3510 / 0.5842 / 0.0648 is
  the EIA-860 2025 ER operable nameplate split (audit §5 row 4), registered only because the load
  derive is lane **SOCO-32**'s by ruling and because the non-binding links above make it unable to
  move the dispatch. SOCO-32 replaces it with FERC-714 hourly shapes.
- **The load basis is FIVE FERC Form 714 respondents, and Southern Power is NOT one of them.** Alabama
  Power (2), Georgia Power (183), Mississippi Power (184), **Oglethorpe (107)** and **MEAG (210)** —
  hourly sum closes the metered EIA-930 BA demand to a 3.03 / 2.92 / 1.26 % residual in
  2023 / 2024 / 2025. **Southern Power (186) is EXCLUDED**: lane SOCO-14 returned a *documented NO* on
  whether its planning-area load sits in the BA, gate G22 is discharged for the five-set and no other,
  and 186's 1.3–1.4 % is named on the first keeper's determination basis. Zones are named for
  **geography, never for an operating company** (card S3) — Georgia Power owns 241.6 MW in Alabama and
  Oglethorpe + MEAG own 7.1 GW in Georgia that is not Georgia Power's, so OpCos do not map 1:1 onto
  zones.
- **VOLL is $61,900/MWh — the only region not on $2,000.** SOCO takes no offers and has no offer cap,
  so there is no tariff ceiling to inherit; the field is the LP's slack (load-shed) penalty, an
  *economic* value of lost load, derived rather than borrowed: LBNL/DOE "ICE Calculator 2" (OSTI
  3021993) cost per unserved kWh at the 2-hour column, weighted by the EIA-861 2024 retail-sales
  customer mix over the 85 utility rows with BA code `SOCO` — 0.4009 × $5,030 + 0.5991 × $100,000 =
  $61,927 → $61,900. Construction fixed in `PRECOMMIT-soco-20-2026-09-14.md` §3 **before** the number
  was written. Honest width, reported and never selected on: 8 h → $32,384, 24 h → $19,447. Stated
  misalignment: ICE 2's cost functions are national pooled models, so the "Southeast" leg is the
  customer-class **mix**, not a regional cost function. Because this is the slack penalty at ~31× the
  $2,000 regions', any unserved energy dominates a SOCO objective far more sharply — read a SOCO dual
  with that in mind.
- **Two timezones, one clock** (gate G19, closed by SOCO-10 §3.4). The footprint spans
  America/Chicago (AL, MS) and America/New_York (GA), but the BA is dispatched from one control centre
  and EIA stamps it on ONE clock — **`America/Chicago`, DST-aware, hour-ending** — measured over all
  26,304 rows of the committed `SOCO hourly.parquet` (0 mismatches vs a Central wall clock, 26,301 vs
  Eastern). Every SOCO series is Central and joins on `UTC time`; all three zones are Central, because
  the timezone is a property of the BA, not of a zone.
- **No import node, and no capacity market.** The seams are the served measured EIA-930 `Total
  interchange` schedule (`_SCALAR_INTERCHANGE_ISOS`, card S4) — SOCO is a net **exporter** of
  +10.2 / +10.8 / +13.0 TWh, so the served series *raises* what the internal fleet must generate in
  most hours — plus eight **default-off** `NeighborInterface` blocks for lever **SOCO-56**
  (`SOCO_TVA` is the one genuinely two-way seam, −3,150 .. +3,007 MW). SOCO is deliberately absent
  from `capacity_market.MARKET_DESIGN` (→ `DEFAULT_MARKET_DESIGN`, card S6), from every offer-curve
  tuning channel (gate G5: SOCO takes no offers, so every band multiplier is the identity) and from
  any reserve co-optimisation or scarcity seed (card S5) — hence no `default_scenario_overrides`.
  `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"] = 0.26`, the **winter** margin, the binding season here.
- **The CEMS gap was the critical path and it is closed.** No AL/GA CEMS existed for any year at
  charter — 91.6 % of CEMS-eligible fossil MW (45,797.3 of 50,005.0). Lane SOCO-11 landed all 8 AL/GA
  files schema-equal to `MS_2024`. The **FERC-714 reconciliation gate FAILED at 73.2 %** and
  **nothing was rescaled** — that failure is inherited, not fixed.
- **There is no reliability floor, bridge or derate for SOCO**, and no
  `reliability_floor_coeffs_SOCO.csv`, so `RELIABILITY_FLOOR_REGISTRY["SOCO"]` is empty and lane
  SOCO-40's keeper is built without one. A cost-based pooled system is commitment-heavy by
  construction, so the temptation to floor it is real: any later floor arrives through rule 17
  `[R-FLOOR-WINDOW]` with a declared driver, window and forward story — never as a residual patch.

---

## soco-10 — 2026-09-13 — Phase-0 data audit (zero-LP)

Lane SOCO-10, Opus claude-opus-5, branch claude/soco-10-audit-k3m9, base 2c2fc065.
Deliverable: docs/multi-iso/soco-data-audit.md (NEW) + 00-iso-addition-protocol.md
§0/§3 + 01-data-needs-and-upload-manifest.md SOCO rows. No solve, no src/ edit,
no matrix cell, no shared record.

CENSUS. EIA-860 BA "SOCO": 336 plants / 788 gens / 70,667.2 MW nameplate
(66,161.2 summer / 69,096.8 winter). Charter's 335/786/70,665.7 is that MINUS the
1.5 MW MA row, while its own per-state list INCLUDES it and sums to 70,667.2 —
both right about different sets, one labelled. Per-state and per-technology all
confirm to 0.1 MW. MA row (plant 67241 "401 South", Berkshire MA, NERC NPCC)
REJECTED as an EIA-860 BA-field mis-entry under a stated two-key rule (SERC +
AL/GA/MS/FL-panhandle). Six FL plants (309.6 MW, all NERC SERC, panhandle) KEPT;
the load-side question (former Gulf Power, own FERC-714 respondent 185) routed to
SOCO-11. Reconciled to Southern's FY2024 10-K Item 2 (pp. I-30..I-33) on a stated
whole-unit-vs-ownership-share bridge; the wedge is exact on nuclear (10-K 4,786.7
MW vs EIA-860 8,282.4 MW = the Oglethorpe 30 / MEAG 22.7 / Dalton 2.2 % share of
Vogtle+Hatch).

CEMS GAP — THE CRITICAL PATH. No AL_*, GA_* or FL_* parquet for ANY year; MS
present 2019-2026. Missing for the window: {AL,GA} x {2023,2024,2025} = 6 files,
exactly as chartered. Worth 91.6 % of CEMS-eligible fossil MW (45,797.3 of
50,005.0), incl. 91.0 % of coal and 90.5 % of gas-CC. SPP's gap was 44.9 %.
ISO_STATES["SOCO"] should read ("AL","GA","MS","FL").

GATE G19 CLOSED. Committed SOCO hourly.parquet Local time == America/Chicago
DST-aware wall clock in 26,304 of 26,304 hours (New_York 26,301 mismatches, fixed
CST 9,171, fixed EST 17,133); two offsets only (-6/-5) switching on the correct
DST dates; 3 duplicate Local time values (fall-back hours), 0 duplicate UTC hours.
Hour is EIA hour-ENDING 1..24 (25 on fall-back day). CONVENTION FOR EVERY
DOWNSTREAM SERIES: America/Chicago, hour-ending, JOIN ON UTC time. All zones are
Central if S3 lands 3. convert_eia930.BA_TIMEZONES ALREADY carries
"SOCO": "US/Central" — but fetch_eia930_hourly.BA_TIMEZONE and
build_eia930_hourly_from_raw.BA_TIMEZONE do NOT and both default to Eastern, and
fetch_eia930_interchange imports the first — so SOCO-11's interchange pull writes
EASTERN unless fixed first (routed R-1/R-2).

CARD S8 — WORSE THAN THE CARD ASSUMED. cod_ramp.effective_cod always prefers the
plant-collapsed COD over the unit's own Operating Month for the ONLINE date (the
per-unit preference is retirement-only, the Homer City seam), and _load_cod_map
collapses a plant to a capacity-weighted MEAN. Measured live: load_cod_map()[649]
= (2005,5) so Vogtle 3 AND 4 are online all 12 months of 2023/24/25; [3] = (1991,3)
so Barry A3 is online all of 2023; [56] = (2023,9) so a GREENFIELD plant does ramp
— the bug is brownfield-only. Phantom energy at measured EIA-923 unit CFs (V3 88.6 %,
V4 89.1 %): +12.979 TWh in 2023 (+24.8 % on 52.435) and +2.167 TWh in 2024 (+3.4 %).
Modelled 2023 nuclear would read ~65.41 TWh, ABOVE measured 2025's 64.17 — inverting
the 52.4 -> 63.0 -> 64.2 step. Barry A3: 774 MW ten months early, 2.3-4.6 TWh.
Blast radius: SOCO 3,040.3 MW vs SPP 1,127.4 / ERCOT 1,091.4 / CAISO 1,037.2 /
MISO 927.4 / PJM 177.2 / NYISO 72.9 / NEISO 50.0 — SOCO worst by 2.7x and Vogtle
3/4 are the two largest trapped units nationally. ROUTED AS AN OWNER CARD (R-4);
recommendation is to prefer the unit's own date (rule 14), cross-ISO A/B as its own
lane, with "state the bias on the determination basis" as the floor.

EIA-930. All charter energy figures confirmed. TI is positive = NET EXPORT;
Demand + TI = NetGen closes to 0.0000 TWh in 2023 and 2024. 2025's "7 missing
hours" is a UTC-bounded fetch, not missing data (7+8760+8784+8753 = 26,304) —
extend by 7 h, never pad. NG: PS/BAT/SNB/OES nulls are an EIA taxonomy cut-over at
2024-07-15, and NG: WAT never goes negative before it (min +32 MW), so pumped
storage is UNOBSERVABLE for 2023 and most of 2024 (C1 constraint, routed R-6).
Defect screen: Demand is clean (max/median 1.79-1.84, both screens no-ops); four
NG: NG hours post ~70 GW against a 36,336 MW gas fleet; the netgen identity breaks
in 2025 only (595 h, max 13,120 MW, +0.696 TWh, netgen the corrupted side); one 1-h
partial demand dropout at 2025-10-23 16:00 (12,638 MW). NO EXISTING SCREEN CATCHES
ANY OF THEM (routed R-5); no new constant proposed (rule 23). Independent check:
EIA-930 NG: NUC vs EIA-923 agrees to +0.58 / -0.11 / -0.10 %.

CARD S6 EVIDENCE. SOCO is WINTER-peaking in 2 of 3 years (47,368 MW 2024-01-17
07:00; 46,490 MW 2025-01-22 08:00) and summer-peaking in 2023 (45,558 MW
2023-08-25 16:00); 2025's summer peak is 0.25 % below its winter peak. A scalar PRM
misrepresents this system. Georgia Power 2025 IRP (Docket 56002): 26 % winter /
20 % summer TRM, raised from 16.25 % summer.

CARD S3 RECOMMENDATION (recommend only). 3 zones on state FIPS (AL/GA/MS, FL->AL,
no MA key), Tier-3 non-binding TTCs, IF SOCO-11's load reconciliation closes; else
1 zone. Fleet side is the cleanest of any registered ISO. Load side needs a scope
correction: FERC-714 has EIGHT footprint respondents, not three (Gulf Power 185,
Oglethorpe 107, MEAG 210, PowerSouth 1, "Southern company" 142 alongside the three
OpCos), and the three OpCos structurally cannot sum to the BA — GP's own winter
peak is 16,284 MW against a BA peak of 47,368 MW. Check respondent 142 first
(routed R-3). THE PART THAT MATTERS: with no price, a SOCO zone split can be
validated on load, monthly per-zone generation and (once AL/GA CEMS land) hourly
fossil generation — and can NEVER be validated on price spread, congestion or the
TTCs themselves. 3-zone and 1-zone SOCO produce the SAME dispatch until a TTC
binds, so the split must be chosen for structure and never sold as accuracy.

CARD S5 NOTE. $2,000/MWh is FERC Order 831's OFFER cap. SOCO takes no offers —
cost-based dispatch, no DA market, no LMP, no capacity market. Recommend an
economic VOLL from the DOE/LBNL ICE calculator on the SERC/Southeast class mix
(pending SOCO-12); the Brattle ERCOT study is cited as METHOD only, never value
(rule 25). If nothing citable survives Phase 0, $2,000 is acceptable ONLY with the
misalignment written on the field and the value ledgered under rule 21.

OTHER: no wind anywhere in the SOCO fleet (R-12); CAES maps on 25 MW not 110 MW
(R-8); PSH summer capacity exceeds nameplate, 9 rows (R-9); `soco` profile token is
collision-free but does not hydrate eia-930-hourly/SOCO hourly.parquet (R-10);
cod_ramp.py docstring is stale vs its own code (R-11). Registry-values table: 18
rows, every cell a citation or an explicit pending. Manual manifest: 12 items with
exact URLs.

---

## soco-11 — 2026-09-13 — CEMS AL/GA + FERC-714 spine + interchange

Landed all eight {AL,GA} x {2023,2024,2025,2026-Q1} CAMPD extracts
(schema-equal to MS_2024; AL 23 fac / 88 units, GA 32 / 131), the FERC-714
hourly planning-area demand spine (8 respondents, 210,431 rows, via PUDL --
FERC's own host 403s from this egress as it did at charter), and the SOCO
BA-to-BA interchange book (236,736 rows, 9 DIBAs, keyless bulk route).

THE 714 RECONCILIATION GATE FAILS: the three chartered respondents are 73.2%
of the BA's metered demand (short 61.4 / 66.2 / 64.2 TWh; r = 0.996 / 0.996 /
0.990). Nothing rescaled -- raw landed, failure documented, lane stopped, per
rule 13. Diagnostic offered not applied: Oglethorpe + MEAG close it to
3.0 / 2.9 / 1.3%, and the falsifier (PowerSouth + Tallahassee, own BAs)
overshoots to -2.3 / -2.4 / -4.2%. BLOCKER ROUTED: PUDL carries no county
attribution for Oglethorpe or MEAG, so their BA membership needs a primary
citation before SOCO-32 builds any share.

Interchange CONFIRMS the charter: SOCO nets +10.155 / +10.832 / +13.038 TWh
exported, agreeing with the BA book to 0.001 / 0.001 / 0.017 TWh. Zero NaN
hours and no impossible print -- the cleanest interchange book in the corpus.
TVA is the only genuinely two-way seam.

Timezone: America/Chicago, measured on two independent sources (930 offsets
are CST/CDT; every Southern 714 respondent reports Central). BA_TIMEZONE
gains "SOCO" as an additive key.

---

record this lane must not edit, plan §8.0 rule 1.)*

## soco-12 — 2026-09-13 — planning corpus, NRC, LTLF, gas (W1, zero-LP)

**Gate G12 is MET.** The SOCO long-term load forecast is Georgia Power's
**Budget 2025 (B2025)**, vintage **2025**, horizon 2025–2044, filed with the 2025
IRP (GA PSC Docket 56002, doc 221233, 2025-01-31) and approved 2025-07-15 — 60
rows at `data/raw/load-forecast/soco/soco.csv`, parser- and validator-clean.
Caveat on the record: it is **Georgia Power only**; the workbook's Southern
Company **System** column is REDACTED throughout, and **Alabama Power files no
public IRP** (Alabama has no IRP statute), so roughly half the footprint has no
public forward load forecast.

**Card S2 / SEEM — the charter's finding is corrected in three ways but its
operative conclusion stands.** SEEM launched **November 2022**, not 2023. SEEM's
own site publishes **no price** (its three informational-report pages all read
"No reports available at this time"; "Public Data" is registration-gated), but its
**Independent Market Auditor publishes monthly clearing prices publicly, back to
2022-11** — ~$30 (2023), ~$23 (2024), ~$32 (2025) per MWh, SEEM-wide. And a
FERC-accepted settlement (2026-01-05) obliges SEEM to post **hourly** average
prices prospectively; the page is still empty. None of it is a SOCO hourly
benchmark — it is SEEM-wide, monthly, and prices ~0.5 % of SOCO demand — so
**card S2 stands unchanged**, with the auditor figures newly available to SOCO-13
as its independent reconciliation anchor. SEEM's own FAQ routes price to FERC
reporting, corroborating the EQR route.

**Card S6 — seasonal PRM, measured.** Southern Company System Target Reserve
Margin: **winter 26.0 %, summer 20.0 %** long-term (25.5 / 19.5 inside three
years), from the *2024 Reserve Margin Study of the Target Reserve Margin for the
Southern Company System* (Jan 2025), whose scope is exactly the IIC companies.
Winter is the binding season by the study's own words. **The footprint's 2024 and
2025 annual maxima are January events** (38,194 MW on 2024-01-17 is the all-time
system maximum; 2022 and 2023 peaked in summer), while Georgia Power alone stays
summer-peaking — adequacy binds in winter, energy peaks in summer.

**Card S3 — there is NO published inter-OpCo transfer limit, structurally.** The
Operating Companies *"function as a single, integrated public-utility system"*
under the IIC and are *"committed and dispatched as a common System without regard
to the ownership of each generating facility"*. They are not separately-dispatched
areas, so any three-zone topology registers **Tier-3, non-binding** TTCs on the
SPP-20 precedent. External seam transfer capabilities **are** published (MISO-South
1,791/2,374 MW, TVA 480/478 MW, eleven more rows) — card S4's input.

**Confirmed retirements — the record is one of reversals.** Only Wansley 1-2/5A
and Boulevard 1 (2022-08-31) are executed-and-dated. The 2022 IRP Order's Scherer 3
and Gaston 1-4/A retirements were **superseded by the 2025 IRP Order**; Barry 5 and
SEGCO Gaston 1-4 were reversed by company decision; Daniel 2's date is being
extended. **An ELG Notice of Planned Participation is NOT a step-0 instrument** —
the enforceable instrument here is a state-PSC order, and Alabama has none.

**NRC** — eight reactors landed at `data/raw/nuclear-license-status/soco.csv`.
**Six of eight expiries fall inside the 2026–2050 horizon.** Hatch 1-2 hold the
footprint's only granted SLR (2026-06-11, → 2054/2058); Farley 1-2 have an
announced intent only (expected Apr–May 2027); **Vogtle 1-2 (2,430 MW) expire
2047/2049 with no SLR of any kind on file**. Georgia PSC approved uprates of
+58 MW (Hatch 1-2) and +54 MW (Vogtle 1-2).

**Gas** — AL/GA/MS delivered-to-electric-power monthly series landed from the
key-free EIA dnav route; 108/108 cells reconcile with the committed all-state
table. **GA and MS publish nothing for 2025** — a real in-window gap. The
footprint's basis is **Southern Natural Gas** (50 % Southern Company Gas) plus
**Transco** into northwest Georgia via the Dalton Pipeline; **no free public daily
index exists at either**, measured against both EIA daily/weekly tables.

FINDING: `docs/handoffs/FINDING-soco-12-2026-09-13.md`. Zero solves.

---

## soco-13 — 2026-09-13

**FERC-EQR price index (card S2 option a): NO.** PRECOMMIT pushed before any value was read; STOP
gate D1 / D5 pass, **D2.2 fails every year** (indexed short-term energy 3.66 / 2.69 / 2.64 % of SOCO
demand vs ≥ 5 %), **D3.1 fails 2024 / 2025** (index $33.5 / $35.5 / $55.1 vs the SEEM auditor's
$30 / $23 / $32, +11.7 / +54.2 / +72.1 % vs ±15 %; shape passes, `r` 0.86–0.88 Peak / Off-Peak
against the digitised annual-report figures), **D4.2 fails 2025** (2.008× the F-class CC fuel cost vs
a 2.0 ceiling; gas tracking `r` 0.78 passes). The level gap is scarcity in the bilateral slice
(Jan 20–25 2025 daily $153–378; 2025 mean/median 1.41), present in every seller and increment; the
SOCO-delivered SEEM matches price at 2–3× the SEEM-wide average, so the anchor is confirmed
SEEM-wide, not SOCO. Raw store `data/raw/ferc-eqr/` committed (981,070 SOCO-POD rows from 1.83 bn
EQR rows / 41 GB streamed; 26,286-hour UTC index, 99 % priced; digitised SEEM anchor; fuel-cost
anchor; ledger; gate). **Nothing landed to `_validation-source`**; S2 limb (b) / rubric v3.8 applies;
G6 and S9 skipped by design. Routed: (i) price unscored vs (ii) a labelled bilateral benchmark = a new
owner ruling, never a re-cut gate. `FINDING-soco-13-2026-09-13.md`.

---

## soco-14 — 2026-09-13 — BA membership of FERC-714 respondents 107 / 210 / 186

GATE G22 = FAIL, 2 of 3 cited.

Oglethorpe (107) YES: NERC/SERC public compliance audit NCR01248 p.3 -- "The
Reliability Coordinator (RC), Balancing Authority (BA), and Transmission
Operator for GSOC is Southern Company Services, Inc. - Transmission." GSOC
schedules and dispatches Oglethorpe's resources and is the registered LSE for
the 38 member EMCs (OPC FY2024/FY2025 10-K, Control Area Compact with Georgia
Power). SCS-Trans is EIA BA code SOCO / BA ID 18195 (EIA-861 2024). 37 of 38
members coded BA=SOCO in EIA-861 2024; 154/154 member counties inside the SOCO
BA's 252-county footprint. Cross-check: EIA-861 Operational_Data winter peak
10,489 MW == the 714 series' 2024 maximum.

MEAG (210) YES, in MEAG's own words: Annual Information Statement FY2024
(dated 2025-05-22, printed pp.25-26) places MEAG's Territorial Load inside "the
Southern Company Balancing Authority Area", and the PSSA's exit clause speaks of
MEAG later joining "another balancing authority area". 48 of 49 Participants
coded BA=SOCO; 51/51 counties inside. Cross-check: EIA-861 summer peak 2,399 MW
== the 714 series' 2024 maximum.

Southern Power (186) NO -- documented. FERC Form 714 has no field in which a
planning-area respondent names its BA (sample form p.1 + instructions IV.A);
PUDL/EIA give 186 no BA code, no counties, no EIA-861 presence at all; EIA-860
shows 42 of its 53 plants OUTSIDE SOCO, in 15 BAs across 13 states, so "its
generation is in the footprint" is false as stated and is the wrong claim
regardless; and its 714 series is a flat ~390 MW block (LF 0.795, diurnal
0.95-1.04x) that is not a territorial load. The document that would settle it,
Part III Schedule 1 "Electric Utilities That Compose the Planning Area", is in
FERC's bulk CSVs -- 403 from this egress, as at the SOCO-11 charter -- and
Zenodo (PUDL's raw archive) is 403 too. Routed as one fetch.

Also routed: the falsifier's STATED reason does not hold for 2023-2025 --
EIA-861's BA registry dropped AEC (PowerSouth) after 2019 and now codes
PowerSouth's own rows to SOCO, while PUDL still classifies it AEC through 2025.
The measured overshoot is unaffected; the explanation is. And county containment
is corroboration only: AEC's 50-county footprint sits entirely inside SOCO's 252,
so a nested BA passes that test.

No share derived, no parquet written, no solve, no matrix cell moved.

---

## soco-22 — 2026-09-13 — rubric v3.8, the no-price determination class (zero-LP)

`scripts/calibration_verdict.py` gains one determination branch keyed on the absence of an
`actual_lmp.json` block: `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` / `-WITH-CAVEATS`, never
`CALIBRATED`, scored on C1/C2/C4/C6/C8, price gap on the basis at full magnitude on every route.
All 14 registered runs (7 keepers) re-score byte-identically on the full span and per year (only
`rubric_version` 3.7 → 3.8 moves). 34 new tests. Serves NWPP card N2 limb (b) with the same amendment.
Routed: rubric doc entry, `audit_keepers._DET_TOKENS`, `calibration-status.js` label map.

---

## soco-15 — 2026-09-13 — the COD-seam cross-ISO repair (card S12)

**DESK-AUTHORED STUB.** Lane SOCO-15's FINDING carries no `## Log entry` section, so there is
nothing to append verbatim (plan §8.0 rule 1). Rather than fabricate the lane's own words, the desk
records only what another ISO's lane must know, and points at the source:
`docs/handoffs/FINDING-soco-15-2026-09-13.md`.

WHAT LANDED: the `cod_ramp` online-date repair, commit `9398000d` (PR #6127). A raw EIA-860 unit
with a known own year keeps its OWN `(online_year, online_month)`; a plant-level object keeps the
plant map's; retirement resolution unchanged. One shared seam
(`cod_ramp.generator_online_mask`), no per-ISO branch, no `ScenarioConfig` field, so no matrix row.

WHY EVERY OTHER ISO'S LANE SHOULD READ THIS: the repair deliberately MOVES RESULTS for registered
keepers while leaving CACHE KEYS untouched. If your ISO's numbers move and its key does not, this is
why — do not read it as your own regression. Measured, arm − control: MISO CC_CHP −0.15 to −0.20
TWh/yr 2020–24, CT_PEAKER 2022 −0.326; SPP 2025 CT_PEAKER −0.645 (−4.0 %), CC_REGULAR +0.334,
ST_GAS +0.156, COAL_PRB +0.131, price +0.23 $/MWh (2023/24 identical); ERCOT 2021 CC_CHP −0.314 and
CC_REGULAR +0.310 (both TOWARD measured), 2023 price +2.34 $/MWh — the largest single effect in the
A/B; PJM ≤ 0.073 TWh and prices identical. NYISO ≤ 0.028, CAISO ≤ 0.037, NEISO ≤ 0.003 TWh/yr —
bounded by input census, not solved. Both directions are reported: COAL_PRB and CT_CHP moved AWAY
from measured and the lane says so.

EXIT CONDITIONS, all three MET: (a) all seven keeper `cache_key()` values byte-identical across the
repair — `caiso bab5e9b08681e54c · ercot 0f89d4c5f45043f7 · miso b35a8f20b73a5fbf ·
neiso 28266b333667e16f · nyiso 7e0dc0344f297fc2 · pjm b05e09c319c2c5f5 · spp 6d6205e381e982c2`;
(b) greenfield still ramps and three brownfield tests fail on the old seam and pass on the new, both
directions demonstrated; (c) rule 25 intact.

SOCO-20 IS CLEARED TO PROCEED on this lane's account.


## soco-21 — 2026-09-13 — the eighth mechanism-matrix shard

**DESK-AUTHORED STUB**, for the same reason as soco-15 above; source
`docs/handoffs/FINDING-soco-21-2026-09-13.md`.

`docs/codebase-site/data/mechanism-matrix/SOCO.js` is live as the eighth shard, one commit
(gate G2). Census: **327** mechanism ids, **168 `U`** (untested), **159 `·`** (structurally n/a),
327 = 168 + 159 with exactly one cell line per base id. `keeper` and `gates` are deliberately EMPTY
— the same fail-open state SPP's column held between SPP-21 and SPP-40, and correct here because
**SOCO has no keeper, no registered run and no solve of any kind at HEAD; NO VERDICT WAS MINTED.**
The `·` classification rule is stated in the shard's own header so a later lane can audit any single
cell without re-deriving the column; the largest class is 100 cells that name another ISO's own
market object, and a foreign-stemmed row that some other ISO HAS entered reads `U`, not `·`.
Card rulings S5 and S6 supply six more (`·` for no capacity market, four for no cleared AS market,
one for no scarcity pricing, one for carbon-`None`).

---

## soco-20 — 2026-09-14 — SOCO registered as the ninth region (zero-LP)

Lane SOCO-20, Fable claude-fable-5-1, branch claude/soco-20-register-fvj01g, base d083b0b1.
Deliverable: ONE PR — _ISO_BUILDERS["SOCO"] appended last, DEMAND_LOADERS["SOCO"] and
SURFACE_ISOS += SOCO in the SAME commit (eb9d015a), _ISO_TO_BA_CODE["SOCO"]="SOCO"; 22 src
modules, 9 scripts, four new scripts/lib/<pkg>/soco.py specs, the soco data profile, the
calibration-solve dropdown. No solve, no matrix cell, no keeper, no ScenarioConfig field.

REGISTERED AS A BALANCING AUTHORITY. Three geographic zones SOCO_AL/GA/MS on shares
0.3510/0.5842/0.0648 (five FERC-714 respondents, Southern Power 186 EXCLUDED, residual
3.03/2.92/1.26 %); Tier-3 links 24,400 / 4,300 MW that CANNOT bind; no capacity market,
no import node, no AS design (reserves.spec refuses SOCO by name); every offer band 1.0;
VOLL 61,900 $/MWh from ICE 2 on the EIA-861 BA=SOCO class mix; PRM 0.26 winter; McIntosh
CAES a 25 MW gas CT and skipped by the storage loader. Zone lookup 413 plants (GA 299 /
AL 97 / MS 17); plant 67241 (MA) REJECTED. Fleet 393 thermal units / 55.09 GW, 8 nuclear
incl. Vogtle 3 (2023-07) and 4 (2024-04) on their own CODs. Demand 239.6 / 249.5 / 252.6
TWh; net export +10.16 / +10.81 / +13.03 TWh.

G8 HOLDS. solve_surface_register --diff origin/main HEAD: ERCOT 0, CAISO 0, MISO 0, PJM 0,
NYISO 0, NEISO 0, SPP 0 moved (SOCO 20 = its own new rows, undeclared, R-1 state). All
seven keepers' cache_key() re-derived from run_config.json BYTE-IDENTICAL to the PRECOMMIT
§6 baseline (nyiso on 2026-09-13-nyiso-232-st-gas, 93be4aeb93d78283).

TWO SEAM REPAIRS, both no-ops for the seven: derive_nuclear_monthly_cf divides by the
MONTH-ONLINE nuclear pmax (--check: seven committed tables match); load_eia860_storage
drops the one national CAES row. Curated EIA-860 parquets rescoped (+SOCO rows only).

THE RESCOPE WAS NOT ADDITIVE AND THE SUITE CAUGHT IT: --rescope-from-parquet dropped the
eGRID heat_rate join on the canonical + 2020/2023/2024 tables and admitted one PJM row.
Repaired before push as main's frame byte-for-byte + SOCO rows (heat_rate joined from
the PLNT23 cache); script defect ROUTED with the recipe. REBASED onto c6c70190 after
NWPP-20 registered the eighth region the same day (55 conflicts, union NWPP-then-SOCO;
SOCO is the NINTH region; parquets = main's NWPP-inclusive frames + SOCO rows). Suites
on the rebased tree: unit 5,539 passed / 8 failed; curation+regression+scoring 2,916 /
31. Every failure fails identically with origin/main's code in the same tree or arrived
with main's own commits (CAISO artifact drift PR #6037, Mystic oil rows, ERCOT fleet
golden, NYISO surface 210 vs 209, NYISO gas-anchor pins after c0a9d5ba, coal-stocks
dictionary after 3857d801, 10 NEISO forecast key-provenance records, 19 scoring pins,
and data/clean FileNotFound x11). G8 re-proved: NWPP 0 moved too.

TAIL_THRESHOLD SKIPPED x3 (SOCO-13 read NO price). Routed: D79 undeclared rows, the 7-h
2025 tail fetch, the four ~70 GW NG:NG hours, curate_demand_profile.MODEL_ISOS (SOCO-31),
dashboard ISO_ORDER / keepers index (SOCO-34/40), VOLL in forecast screens (SOCO-55),
the process_eia860 rescope defect. Pre-existing on main, not this lane's:
ci_refactor_guards script-refs (run_calibration_full -> missing mirror script) and the
seven test failures above.

## soco-30 — 2026-09-16 — unit outage windows + thermal tranches (W3 frozen derives, zero-LP)

Lane SOCO-30, Opus claude-opus-5, branch claude/soco-30-outages-tranches-r4t8, base edd40943.
Source `docs/handoffs/FINDING-soco-30-2026-09-16.md`. Zero solves, zero src/ edits, zero
derive-script edits, zero matrix cells moved (rule 28 — this lane arms nothing). Rule 23
trivially satisfied: SOCO has never been solved, so there is no residual to derive against.

COVERAGE BY STATE, the headline, re-measured on SOCO-10's own 50,004.8 MW denominator:
MS 99.83 % · AL 98.86 % · GA 93.52 % · FL 0.00 % (no extract); footprint 95.95 %, uncovered
2,027.2 MW / 4.05 %. THE CHARTER'S PREMISE IS INVERTED AND IS CORRECTED HERE: SOCO-10's 91.6 %
was the MISSING share BEFORE SOCO-11 landed AL and GA, not a coverage ceiling. Coal 100.00 %,
CC 99.68 %, CAES 100.00 % covered; the 4 % gap is peaking CTs and small industrial sites, and
its two largest members (Dahlberg 919.0 MW, Hartwell 360.0 MW — 63 % of the gap) are CT_PEAKER,
which the overlay skips in every ISO anyway. Uncovered plants listed by plant and class in the
FINDING §0.1; nothing padded, no window inferred (rule 13).

SIX ARTIFACTS, six invocations, no flag or constant changed: campd-unit-outages-SOCO.csv 1119
windows (321f9af3), -short 34, -layup 34, -e923 4, campd-partial-outages-SOCO.csv 12,
thermal_tranches_SOCO.csv 60 rows (7b7f5f27). Standard extract derived twice byte-identical;
re-derived guard-off after --merit-order-guard rewrote it (1119 -> 1085) and verified identical
to the pre-guard blob. CEMS vintage: AL/GA/MS x 2023-2025, nine blobs pinned in FINDING §2.

GATE G4 LEG 1 PASS: AL 196/206/240, GA 115/118/155, MS 21/31/37 = 1119. No state-year zero.
GATE G4 LEG 2: 8 full-year rows, ALL the eia923_netzero structural fallback, ALL 2025, all small
non-CEMS CHP, each named by unit in §4; ZERO measured full-year CEMS outages and no unit fell
back for want of data. The deriver's own diagnostic says 8 candidate plants had NO 2025 EIA-923
filing against 0 in 2023/2024, so SOCO-40 reads the 2025 rows as a preliminary-vintage FILING gap
— stated, not adjusted (rule 1). GATE G19 PASS BY INHERITANCE: every window America/Chicago,
DST-aware, hour-ending per SOCO-10 §1.3; no lane-level timezone decision was taken.

CARD S7 APPLIED, NOT RE-OPENED: McIntosh 7063 is CT_PEAKER at pmax 25.0 MW beside the site's four
conventional CTs. VOGTLE EMITS ZERO ROWS (plant 649 absent from the extract; no nuclear plant
appears) — SOCO-15's COD mask owns it and the phantom was not re-introduced.

CLASS BANDS vs MISO, reported never tuned (§8): committed p10/p50/p90 CC_REGULAR 22.5/44.8/70.0
vs 28.4/42.1/70.0 · CT_PEAKER 7.3/12.2/21.0 vs 7.2/13.4/34.3 · ST_GAS 17.2/18.6/27.6 vs
9.3/18.4/32.5 · COAL 36.6/43.2/59.8 vs 27.1/36.7/61.2. Three divergences named: coal mustrun_pct
47.0 vs 28.9 is the estimator's known ~2x-high behaviour on an always-online fleet (Miller 8,760
online hours) while mustrun_online reads 24.3 vs 27.6, in band; CC peaking 7.7 vs 4.9 is a
duct-fired summer-peaking fleet; CT_CHP 48.2 vs 69.5 is one plant against five.

STEPS 3 AND 4 COMMIT NOTHING: tag_mixed_plants.py is ERCOT-only and its Plant_Code intersection
with SOCO's 110 fleet codes is EMPTY (run against scratch copies; both committed sheets verified
byte-identical, 19d726cd / 49e8d9ee). build_offer_curve_overrides --iso SOCO --list: all 13
classes 1.0 on committed/econ_low/econ_high/peak, no phys_* rows, delta JSON {} — no ERCOT-fitted
multiplier leaks (rule 25). SOCO-40 declares authorized_price_tuning: NONE.

THREE FINDINGS ROUTED TO SOCO-DESK, each needing a file this lane must not touch. (1) The layup
merit guard is COAL-ONLY because gas_basis_by_iso_month.csv has ZERO SOCO rows, so all 238 gas
units of the 279-unit panel drop out and 15 priced units approx = the 17 coal — NWPP-30 §7.1
reproduced; re-derive when SOCO-32 lands a gas hub, and until then do not read the companion as
"SOCO has no economic layup". (2) THE PRIMARY-GROUP FILTER DROPS 15 (plant,group) PAIRS /
4,872.9 MW FROM THE TRANCHE FILE, INCLUDING 2,954.5 MW — 25.7 % — OF SOCO'S COAL: SOCO has 7
mixed plants and Barry/Daniel/Gaston each lose their COAL row to a CC or ST primary, which also
inflates Barry's median_cf to the 150.0 cap. Bounded today because SOCO is deliberately absent
from CAMPD_BINNING_ISOS and NOTHING IN W4 READS THIS FILE. SOCO-20's comment says SOCO-30 adds
SOCO to CAMPD_BINNING_ISOS "with the artifact" — THIS LANE CANNOT: it is src/, a declared
solve_surface value (65b4e3e163ffd580), a gate-G8 cache-key move and a [FABLE] call; the artifact
now exists and §6.2 is the evidence the desk should weigh. --per-unit-attribution is NOT a safe
fix as-is: its classifier keys on CAMPD unitType, a prime-mover descriptor with no coal concept,
and on the 2024 panel it re-seats Barry/Daniel/Gaston onto CC/ST and finds ZERO coal. (3) Four
SOCO CC plants (6073, 7897, 55382, 57037) carry corrupt EIA-860 summer-capacity rows and
1,412.3 MW is reconciled away at every fleet load — existing committed behaviour, unchanged here,
but every unit_pct_of_plant in the extract sits on that basis.

Plan §5 row SOCO-30 -> LANDED. Gate G4 discharged for the SOCO-30 leg of SOCO-40's precondition.

## 2026-09-16 — SOCO-31: the scoring benchmarks (W3, zero-LP)

GATE G9 PASSES, MEASURED AS A DIFF. build_reference --isos SOCO moved nothing else:
all EIGHT pre-existing regions byte-identical on both isos.<R> and egrid_benchmark.<R>
(CAISO/ERCOT/MISO/NEISO/NWPP/NYISO/PJM/SPP), 39 of 39 pre-existing renewable-capacity
CSVs byte-identical by cmp, whole-file diff +295/-1 with the ONE deletion being the
"generated" date stamp. description / calibration_years / henry_hub_actual unchanged.

SOCO BENCHMARK, 2023/2024/2025. Demand 229.4688 / 238.6990 / 239.5576 TWh; peak
45,558 / 47,368 / 46,490 MW. NET EXPORTER EVERY YEAR: interchange +10.1562 / +10.8067
/ +13.0321 TWh, net generation 239.6251 / 249.5057 / 251.8847 TWh, and demand + export
= 239.63 / 249.51 / 252.59 reproduces the charter's target to the 0.01 TWh. EIA-923 by
fuel: coal 37.2434 / 40.2395 / 43.2752, gas_cc 117.3899 / 113.7601 / 109.7396, gas_ct
6.6852 / 6.2537 / 1.9659, gas_st 12.6350 / 9.4821 / 6.6071, nuclear 52.1354 / 63.0598 /
64.2324, solar 9.0323 / 10.3849 / 10.3165, hydro 6.8150 / 6.3014 / 6.0123 (2025 swapped
to EIA-930, 923 ratio 0.054), wind 0.0. Three capacity CSVs, 37 lines each -- solar
only, because SOCO has no wind. egrid_benchmark: eGRID 2023 PLNT23 BACODE=SOCO, 332
rows, the one non-SERC row (67241 MA) contributing 0.0 MWh and no CO2 -- stated, not
filtered, and no NERC admission key added for a row that moves no number.

THE PRICE SIDE IS NOT LANDED AND NOT SUBSTITUTED. actual_lmp.json UNTOUCHED -- no SOCO
block, not even an empty one, because its ABSENCE is the key rubric v3.8 reads:
_price_reference_absent("SOCO") measured True at HEAD, so a SOCO run reads
PHYSICALLY-CALIBRATED (PRICE UNSCORED). TAIL_THRESHOLD skipped in all three copies
(gate G6) and VERIFIED BY EXECUTION: both derives re-run, both emitted ZERO SOCO rows,
both outputs reverted to committed bytes. Gate G17 upheld -- no neighbouring hub, no
adjusted MISO-South series, no state average; not reached for.

THE ROUTED MODEL_ISOS ITEM WAS NOT ENOUGH. The legacy eia_demand_profiles extract is
frozen, has no live builder and carries NO SOCO rows, so curate_all wrote nothing and
load_demand_meta("SOCO", 2023) still raised -- the F3 failure one axis over.
curate_unextracted() closes it as the in-window twin of curate_pre_window(): same
per-BA adapter, same screen, same writer (_write_per_ba_partition), and
unextracted_iso_years() is data-driven on the raw file -- EMPTY for the seven ISOs the
extract was built around, so their partitions cannot move. SOCO 2021/2022 SKIPPED and
reported, never padded. _EIA923_EXTRA_FUELS_BY_ISO["SOCO"] = ("hydro",) on measurement
(3.52/2.84/2.39 % of footprint energy); oil omitted at 0.11/0.10/0.04 %.

WHAT CANNOT BE SCORED. R-i: SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in
EIA-930 for 2023 (NG: PS 0 of 8,760 hours) and 99.7 % of 2024 (24 hours, all from the
2024-07-15 taxonomy cut-over), and NG: WAT never goes negative before it (min +32 and
+35 MW) -- so PS charging was NOT folded into hydro, it was NOT REPORTED. A hard
constraint on the C1 fuelmix benchmark, for the first keeper's determination basis,
never a hole to fill. R-h loader-seam spikes reported with NO new constant proposed
(rule 23): NG: OIL 1 h 2023 and 7 h 2024, and four 2025 NG: NG hours at 70,683 MW
against a 36,336 MW gas fleet. NEW THIS LANE: 2025 demand.min_mw = 12,638 MW is a
one-hour partial post (2025-10-23 21:00 UTC, D and NG both halve and both recover) that
NO existing screen catches -- 0.486x median against a documented 0.2 floor -- reported
and ROUTED, no downward bound invented. Also new: the EIA-930 balance identity
NG - D - TI is exactly zero in every hour of 2023 and 2024 and nonzero in 633 hours of
2025 (-0.6963 TWh, 0.28 % of net generation), routed to SOCO-33.

eia923_2025.json regenerated. It carries two non-SOCO deltas -- a NEW NWPP block (the
audit loops over _ISO_BUILDERS and NWPP-31 never ran it) and a one-plant SPP
COAL_BIT/COAL_PRB prior-year move with NO status and NO gate change -- and BOTH are
origin/main's own, proved by a control run of main's code with data/clean removed that
is BYTE-IDENTICAL to the committed file. Routed to the NWPP and SPP lanes. 2025 carries
no eia923_incomplete flag (ratio 0.9533, the most complete of all nine regions) but its
PEAKER census is not: 6 of 23 CT_PEAKER plants and 1 of 6 CC_CHP have filed, so no SOCO
pair is gate-eligible and a 2025 gas-split comparison must defer to EIA-930.

## soco-33 — 2026-09-16 — seam derive (card S4, zero-LP)

Lane SOCO-33, Opus claude-opus-5, branch claude/soco-33-seam-derive-mz1tng,
base edd40943. Deliverable: data/raw/reference/soco_seam_{served_schedule,
hr_by_year,hr_elasticity,diba_duration,limit_binding}.csv + soco_seam_SOURCES.md.
DERIVE ONLY — FOR A LATER LANE TO ARM. No spec.py, no ScenarioConfig, no
neighbour's object, no producer script, no matrix cell, no solve; git status is
those six paths and nothing else (gate G9 holds).

SANITY CHECK PASSES. SOCO is a net EXPORTER in every year on both clocks: the
served array soco_net_interchange() reads +10.156 / +10.807 / +13.032 TWh, the
sum of the nine DIBA legs +10.155 / +10.832 / +13.039, reproducing the charter
and SOCO-11 §4.1 independently. Residuals explained, not padded: 2024's 0.0248
TWh is 0.0242 leap day (2024-02-29, 24 h, 24.18 GWh, dropped by the 8,760 clock)
+ 0.0007 UTC→local re-binning; 2023 0.0012, 2025 0.0064.

GATE G19 CLOSED ON THIS LANE'S SIDE. Sign convention stated on every row and
VERIFIED, not asserted: mw>0 = SOCO EXPORTS. Shift test over 26,294 joined
hours — sum-of-legs equals the BA book exactly in 24,100 h (91.7 %, r +0.9985)
at zero shift, collapsing to 54 / 52 h (0.2 %, r +0.955) at ∓1 h; both series
mean +1,293 MW, positive. Both products are America/Chicago; the served array
is UTC-built onto the model's non-leap 8,760 clock, and each CSV row names its
clock.

HEADLINE — THE INTERFACE LIMITS, NOT THE HEAT RATES. Arming the eight
registered blocks at their registered interface_limit_mw would REFUSE 10.66 /
12.81 / 14.21 TWh, 35.6 / 39.0 / 41.7 % of the eight seams' gross throughput.
SOCO_SCEG (limit 126 MW, SOCO's largest export seam) is over limit in 99.2 /
99.8 / 99.8 % of hours and loses 6.02 / 7.74 / 8.68 of 7.12 / 8.85 / 9.78 TWh;
SOCO_TAL (20 MW) 77/76/73 % refused; TVA (478) 42/40/39 %; DUK (407) 30/32/41 %;
FPC (50) 31/36/47 %; SC (533) 8/15/18 %; FPL (1,317) 3.6/2.5/1.0 %. SOCO_MISO
(2,374 MW) is the ONLY seam never exceeded in any hour of any year — and the
only one with a price anchor. The values are correctly transcribed adequacy-
study AVERAGE import transfer capability (SOCO-12 §4c), i.e. the wrong QUANTITY
for a transfer limit: rule 14's misalignment exception, whose instruction is a
reconciled real quantity, not the estimate and not a guess. Routed to SOCO-56
on the SPP-51 ERCOT-tie precedent.

hr_by_year — ONE of eight seams is anchorable. SOCO_MISO, off MISO-South's own
zonal LMP (actual_lmp_hourly_zonal_MISO, 35,040/35,040/35,036 rows): RT 9.52 /
10.09 / 9.28, DA 9.89 / 10.23 / 9.37; K = 1.0 exactly (every SOCO block is
load_shape_exponent 1.0). The registered flat 9.63 constructs within 1.1–5.9 %
of the measured mean in every year. ERROR AGAINST INTEREST: spec.py carries
9.54 / 10.08 / 9.26 and the producer's arithmetic gives 9.52 / 10.09 / 9.28
(Δ ≤ 0.02, ≤ 0.24 %) — SOCO-20 hand-computed on unrounded Henry Hub (2.536 /
2.192 / 3.529) where neighbor_gas_price reads HENRY_HUB_TRAJECTORIES (2.54 /
2.19 / 3.52). Inert (default-off); routed to SOCO-56, not fixed. The other
seven neighbours publish no LMP (TVA, DUK, SCEG, SC, FPL, FPC, TAL — all
vertically integrated) and are REPORTED unanchored with blank hr_by_year, never
proxied: PJM's 11.6 flat and its (5.6, 14.2) Southeast fit stay PJM's (rule 25),
and the CSV reports only what the 11.6 placeholder would CONSTRUCT ($29.46 /
$25.40 / $40.83) with no error column.

ELASTICITY. SOCO_MISO (7.95, 4.96), r² 0.9935, sign OK — but on THREE points
and two parameters, so r² is near-mechanical and this is a sign and an order of
magnitude, not a forward-skill claim. Mean |err| 0.12 elastic vs 0.31 flat, yet
WORSE than flat in 2023 (0.17 vs 0.11). Materiality stated so nobody
over-invests: the flat is already within 1.1–5.9 %, the elastic buys ~$0.7/MWh
at 2025 gas, on one seam carrying 4.4–4.7 of a 21–25 TWh gross book. Not SPP's
(9.0, 3.22) — that fit anchors MISO-West AND South; SOCO's anchors South alone.

DURATION CURVES. Nine DIBAs × three years, 11 percentiles, sign on every row;
every net TWh and percentile matches SOCO-11 §4.3 to the digit from an
independent computation. Zero NaN hours, zero impossible prints (max |mw| 3,150,
so the >20,000 screen is insensitive above ~3,200); grain 8,759 / 8,784 / 8,760,
the 2023 shortfall the DST spring-forward 02:00. SEPA (−1.95 / −2.58 / −2.31
TWh of firm federal-hydro import) is correctly outside the priced blocks and
inside the served schedule — but a priced representation must carry it somehow.

GATE G17 NEVER APPROACHED. No step needs a SOCO price; every anchor is the
NEIGHBOUR's own realized price on the NEIGHBOUR's own side of the seam. No
neighbouring hub, adjusted MISO-South series or cost-stack construction stands
in for a SOCO price anywhere, and none of these files scores a SOCO run. Card
S2 limb (b) / rubric v3.8 untouched.

ROUTED, NOT ACTED ON. (R-1) derive_neighbor_hr_elasticity.py --iso SOCO exits 0
with an EMPTY table — its _NEIGHBOR_LMP_ISO is still the pre-SPP-51 GLOBAL name
map, and SOCO's neighbours are named SOCO_<DIBA> by design (gate G10), so no
SOCO seam can ever resolve through it; the same silent-drop class SPP-51 fixed
in the other producer. (R-2) NEIGHBOR_LMP_ANCHORS has no SOCO key, so
derive_neighbor_hr_by_year.py --iso SOCO exits 1 (fail-closed, working as
designed); the one-line entry is written out in FINDING §A. (R-3) the
hr_by_year rounding gap above. (R-4) FLA hourly.parquet ENDS 2025-01-31 (744 h),
so SOCO_FPL / SOCO_FPC / SOCO_TAL have NO 2025 load shape and cannot be priced
that year — nothing substituted; a fetch, and a SOCO-56 precondition; blocks
nothing in the served keeper. (R-5) the limits, above. (R-7) the served scalar
and eight priced seams are NOT the same quantity: gross throughput roughly
DOUBLES (net 10–13 TWh vs 21–25 gross export / 11–12 gross import), which is
the step change SOCO-56 must screen under rule 29 — its phase 0 is computable
with no LP from soco_seam_diba_duration.csv.

docs/handoffs/FINDING-soco-33-2026-09-16.md.

## soco-34 — 2026-09-16 — SOCO site wiring, nine-region prose, log header, 3 WCAG fixes (zero-LP)

Lane SOCO-34, Opus claude-opus-5, branch claude/soco-34-site-docs-pxkmb5, base
edd40943. FINDING `docs/handoffs/FINDING-soco-34-2026-09-16.md`. No solve, no
src/ edit, no ScenarioConfig field, no matrix cell, no shared record.

THE index.html ARITHMETIC, CHECKED NOT ASSUMED: 47/44/58 ALREADY counted SOCO's
three zones, so index.html needed NO change. 39+5+3=47, 36+5+3=44, 47+9+2=58,
recomputed twice (get_iso_config over SUPPORTED_ISOS, and re-summed off the
committed JSON after the edit). NWPP-35's prose had run two days ahead of the
data; this lane closed the gap rather than moving a number. Both orderings cross
and both are right: NWPP is the 8th builder but 9th matrix column, SOCO the 9th
builder but 8th matrix shard (SOCO-21 landed a day earlier) — which is why
SOCO's lever queue is matrix §5.8, not §5.10 as first written and caught.

THE FOUR CHARTERED DEBTS CLOSED. (a) iso-topologies.json carries a SOCO block —
3 zones summing to exactly 1.000000, 2 links, voll 61900, no interface limits —
with the eight existing blocks byte-unchanged and _meta re-stated at nine; all
nine blocks round-trip against get_iso_config with ZERO per-value mismatches.
(b) data-completeness.html filter now lists all nine. (c) config-reference.html
"the eight serialized" → all nine + the 47/44/58 totals. (d) index.html left
alone, arithmetic reported. Plus SOCO into viz-iso-topology.js
(ISO_ORDER/ISO_COLORS/GEO_HINTS on real geography — MS→AL→GA a chain because
Mississippi reaches the system through Alabama), iso-configs-table.js
(isoOrder/ISO_COLORS/ISO_DESCRIPTIONS), the site.css tab accent,
build_status.ISO_ORDER, keeper_store.DEFAULT_ISO_ORDER,
render_data_dictionary.ISO_ORDER, and the regenerated data dictionary — whose
delta was PROVEN cell-by-cell to be one appended column and nothing else (the
committed matrix was already all-dashes, so the empty code-profile data/clean
cost nothing).

forecast-runs.html PROVEN to render for a region with no forecast runs, by
running the page's own extracted lines against four META shapes: the chip set is
META.isos so SOCO never appears, empty/absent META do not throw. It also fixed a
LATENT BUG — indexOf returns -1 for an unlisted region and -1 < 0, so before the
fix SOCO sorted AHEAD of ERCOT. NWPP still carries that behaviour (routed).

TWO FALSE STATEMENTS CORRECTED against the code in 08-config-reference.md: SOCO's
row said "VOLL $2,000" and the summary said "$2,000 for all eight non-ERCOT
regions". SOCO is $61,900 (iso_configs.py:2348) — the LBNL/DOE ICE-2 customer-mix
derivation, restated with its 8h/24h width and its national-pooled-model
misalignment, and with the note that at ~31x the $2,000 regions' slack penalty
unserved energy dominates a SOCO objective far more sharply. Also corrected
there: MARKET_DESIGN has six keys so SPP/NWPP/SOCO all resolve the build
backstop OFF (the line named only SPP); the PRM registry was missing NWPP 0.144
and SOCO 0.26 (winter); and SOCO entries added to the scarcity, reliability-floor
and interchange mechanism lists (none / none / net EXPORTER + eight default-off
neighbours). multi-iso/README.md: SOCO was "the eighth registered region" and
"stays unregistered until its W2 lane lands" — both now false, re-stamped to the
ninth builder, registered 2026-09-14, cards S1–S12.

THREE ACCESSIBILITY DEFECTS FIXED, ALL PRE-EXISTING AND ALL ACCENT-AGNOSTIC (so
no per-region value is encoded, rule 25, and all nine regions are repaired at
once). The calculator was first validated against FINDING-spp-34 §7 S-2's
committed figures. (1) The dark-section active tab drew its label in the raw
accent: 7 of 9 failed, NEISO 1.69:1 CRITICAL, SOCO 2.39:1 — now #fff at
10.66-12.73:1 with the accent kept on the border. (2) Graph node labels were
drawn in the same accent as the circle they sit on, so ALL NINE failed
(1.63-3.60:1) — now white at 0.95, worst case 8.04:1. (3) dc-chip.active was
white on --hydro at 2.77:1 — now the design system's own --hydro-text at
5.93:1. Where SOCO was already covered it passes best-in-class: .iso-badge
17.19:1 and .badge--iso-soco 6.81:1, the highest of the nine, via SPP-34's
overlay — which matters because white-on-SOCO would have been a 4.47:1
near-miss FAIL.

calibration-log/soco.md HEADER ONLY, entries PROVEN untouched: the entry region
(## soco-10 → EOF) is byte-identical, sha256 11c17984… before and after, 365
lines and 9 headings each time, 121 insertions / 7 deletions with all 7
deletions old header lines. New header matches miso.md's format plus spp/nwpp's
pointers, carries "Next shorthand: soco-35" with the lane-number convention
stated, and fixes the old header's claim that Southern Power is a footprint
member — SOCO-14 returned a documented NO on respondent 186, so the five-set
(2/183/184/107/210) is named instead. It deliberately does NOT replicate spp.md's
rule-22 [R-HOLDOUT] block, removed 2026-09-09; it states instead that no year is
protected, so no SOCO number will be a certified out-of-sample number.

GATES: registry payload parity RED on the same two bundles NWPP-35 reported
(caiso279_ablate_dswcouple_span, soco15_spp_arm) — proven byte-identically RED
via git stash, and my diff touches nothing under results/ or frontend/; one is a
SOCO artifact whose clearing means deleting a solve's results, which rule 31
[R-RETAIN] forbids before the owner rules, so REPORTED not repaired.
check_mechanism_matrix EXIT 0 plain and --base (all warnings self-labelled
pre-existing). ruff format+check clean on 3 files. Dictionary sync: 4 passed /
144 subtests, 1 pre-existing coal-stocks failure identical via stash. Scoring:
41 passed; test_gate_a_provenance fails identically without this diff (NYISO/SPP
superseded-keeper rows from yesterday's promotions). Eleven changed files are
≥300 lines, none shrank, all surgical (rule 27).

ROUTED: (1) CLAUDE.md:19 STILL SAYS "seven ISOs registered" and also
mis-states CAISO as 3 zones (it is 6) — replacement text supplied, deliberately
not edited by a site lane; (2) 00-iso-addition-protocol.md stale in SIX places
incl. line 59 "SOCO NOT REGISTERED" and line 72 "TWO further regions … NOT
registered" — SOCO-10's/NWPP-10's file, rule 5; (3) CHANGELOG.md NOT appended:
sync-docs step 6 says always, plan §8.0 rule 1 forbids a lane touching it — the
plan wins, the desk writes it, conflict flagged rather than silently skipped;
(4) plan line 43's own definition-of-done still says "eight regions"; (5) plan §5
row SOCO-34 → LANDED is the desk's, rule 1; (6) NWPP still missing from four of
the region lists this lane extended plus its site.css tab accent, consequences
measured (fail-safe append / alphabetical tail / inert CSS, but front-sorting in
forecast-runs); (7) keeper_store is stdlib-only so it cannot import
SUPPORTED_ISOS and its "mirrors build_status" comment had already drifted;
(8) keepers/index.json untouched — the first-solve lane adds SOCO at
registration; (9) soco.md:143's stray orphan line sits inside an entry body, the
desk's, re-routed.

## soco-53 — 2026-09-17 — the CT/ST lever is not a price lever

SOCO's one gating C1 failure is not a merit-order defect, and this lane establishes that by measurement rather than argument. Four findings do the work, all of them zero-LP and all of them independent of any solve. First, every offer-curve lever is inert for SOCO by construction: `_SOCO_OFFER_CURVE` sets all four bands to the identity 1.0 on all thirteen groups, so each class collapses to a single flat price block — visible in the keeper's own committed sidecar, where 2023 ST_GAS runs 1.117 / 1.138 / 1.141 / 0.600 TWh across committed, econ_low, econ_high and peak, flat. Every curve-shaped lever therefore routes to a curve that is also all-1.0, and SOCO's only available levers are physics and data levers. Second, the model already over-separates the two classes by 2.8×: the measured CAMPD separation is +0.713 MMBtu/MWh while the model's is +1.983, and CT_PEAKER still over-runs by 8.221 TWh — no cost-side change can close a gap the model is already overshooting, still less turn ~$1.3/MWh into the 7× capacity-factor ratio the real system shows. Third, the real separation is commitment: at unit grain SOCO's gas boilers run 94–144 hour campaigns and start about ten times a year, its combustion turbines run 8–9 hour blocks and start about fifty-eight times a year, and the model gives both classes min_run_hours 0 and min_down_hours 0 while the CT econ and peak tranches — which hold 10.9 of the class's 12.755 TWh — carry zero startup cost. Fourth, the bridge that would supply that physics is inert on SOCO's own data and was refused rather than solved: 68.7 % of boiler downtime gaps exceed 72 hours and account for 98.6 % of all gap-hours, and only 150 unit-hours across three years fall inside the 8 hour ST_GAS min-down. SOCO's boilers do not two-shift. `gas_commitment_bridge` is recorded R and `tranche_startup_amortization` G — the latter because it is the FERC Order-825 fast-start pricing object and SOCO has no clearing price at all, which is rule 1 verbatim.

The arm the lane did solve is the rule 14 repair the evidence pointed to: `measured_ct_heat_rates` on SOCO's own CAMPD derive, nineteen of twenty-six plants and 87.7 % of CT capacity. eGRID publishes one heat rate per plant, so Greene County's nine combustion turbines and two gas boilers carried the identical 10.482689, Calhoun's turbines carried a non-physical 17.099, and the errors run in both directions. The PRECOMMIT registered the effect before the solve — cap-weighted CT heat rate 12.909 → 11.284 and +1,821.3 MW of CT capacity crossing below the marginal ST_GAS plant — and stated plainly that the one gating row would get worse. It did: CT_PEAKER +1.633 / +1.387 / +1.209 TWh with ST_GAS −0.853 / −0.401 / −0.573, so 2023 CT_PEAKER moves +8.221 → +9.854 TWh and C1 goes from one failing row to two, the second being 2023 ST_GAS at −7.34 TWh. Determination is NOT-YET both ways, C2/C4/C6/C8 still pass, C3a/b/c remain unscorable, the DOF ledger is unchanged at three entries and one residual, and every offer band is still exactly 1.0 with `authorized_price_tuning` declared NONE. Sign and mechanism match the prediction, so the construction is confirmed rather than rationalised, and the accurate input is kept under rule 14 rather than reverted.

The comparison itself is clean and that is verified, not assumed: all eight `shared_inputs` content hashes are identical between arm and control, and the shared store rebuilt locally reproduced the same three hashes with no re-solve. SOCO's bench parts were deliberately not rebuilt, because `check_bench_freshness` is red on 44 of 44 parts across every ISO from another lane's edit to a payload source, and rebuilding SOCO's would have destroyed the form-4 comparison. The G-DRIFT audit classified all six changed solve-path files INERT for SOCO, mechanically rather than by assertion.

Two things larger than the lever came out of it. `measured_ct_heat_rates` was unreachable: registered, cache-key-registered, carried True by five ISOs' keepers, and with no CLI flag in the orchestrator every keeper is solved with — now wired along the identical eight-site path the eGRID flags take, byte-identical unset. And the plant-blend defect reaches far beyond CT: 11,777 MW, 26.0 % of SOCO's thermal fleet, sits at nine multi-technology plants, and at eight of them every unit carries one blended heat rate — Barry prices coal, gas CC and gas steam all at 8.994965, and Daniel prices 1,004 MW of coal at 8.399, which no coal unit can attain. The completing mechanism is `egrid_family_heat_rates`, already reachable; its derive was run as evidence and its output deliberately not committed.

The promotion is open and is the owner's. The incumbent keeper is unchanged, nothing was pruned, SOCO's registered year union was enumerated before any prune and is 2023–2025, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. The lane recommends holding and completing the plant-blend repair in one follow-on lane rather than promoting a half-repair now. Record: `docs/handoffs/FINDING-soco-53-2026-09-17.md`.

## soco-53 promotion — 2026-09-18 — the owner ruled, and SOCO's keeper is the measured-CT-heat-rate run

The owner ruled promote, in terms that name this case exactly: *"If structural integrity improves but gates regress that may still be a keeper."* SOCO's keeper is now `2026-09-17-soco53-measured-ct-hr` (bundle `results/calibration/soco53_measured_ct_hr`, recoverable at `3f477ec55ffb2cafc29df6121203c5b8f75611ef`), and `2026-09-16-soco-1-baseline` is superseded and pruned. The lane had recommended holding to complete the plant-blend repair first; that recommendation was overruled and the trade taken deliberately, which is what a promotion decision is.

The cost is stated rather than softened: C1 goes from one failing row to two (2023 CT_PEAKER +9.854 TWh / +4.1pp and 2023 ST_GAS −7.340 TWh / −3.1pp), and C1 all/free from 13/14 · 9/10 to 12/14 · 8/10. Nothing else moves — C2, C4, C6 and C8 still pass, C3a/C3b/C3c remain unscorable because SOCO publishes no price and never will, there are still zero ledgered and zero protective caveats, the DOF ledger is unchanged at three entries and one residual, every offer band is still exactly 1.0 and `authorized_price_tuning` is still declared NONE. The determination is NOT-YET either way, so the promotion neither gained nor lost a determination. The regression was registered in the PRECOMMIT before the solve — +1,821.3 MW of CT capacity crossing below the marginal ST_GAS plant — and delivered at +1.633 / +1.387 / +1.209 TWh, so it is a confirmed prediction rather than a discovered surprise.

It was executed in rule 35's fixed order, each step gating the next. The year union was enumerated over every SOCO sidecar before anything was pruned and is 2023–2025, which the incoming bundle carries in its own single invocation, so no `holdout.keeper` stamp was needed and none was invented. The keeper shard was re-pointed with a structured `superseded.former_keeper` lineage, the status page rebuilt, and `audit_keepers` E1 and E11 both verified green *before* the prune — E11 demonstrably live, since it emits "lineage recipe diff not computable" for NYISO while emitting nothing for SOCO. Only then did `prune_iso_runs.py --iso SOCO --force-uncite` remove the outgoing keeper's three stores together; the guard fired on this lane's own lineage citation, and rule 35(d) names `--force-uncite` as the intended route rather than a safety override, the "looking" being the enumeration and the verification just described. `audit_keepers --check --iso SOCO` now passes with zero failures and the rule 35(f) invariant holds: one registered SOCO run, it is the keeper, and the year set is no smaller.

Because rule 35(a)'s prune destroys E11's baseline — the hazard the plan's gate G21 names, where the guard built to catch a silent de-arm is itself silently disarmed — the diff E11 certified is written into the record instead of being left to a gate that can no longer run it. Of 851 `scenario_config` fields exactly two differ: `measured_ct_heat_rates` False → True, the declared mechanism, and `neiso_coldsnap_derate_dualfuel_unswitched` None → False, a NEISO-only field that did not exist at the superseded run's basis and sits at its default. Zero mechanisms were silently de-armed. The superseded bundle is deleted from the tree and git history is the record, recoverable at `dcb03c6bd346f9ab0d4356d5166b18c4ad42a214`.

What the lane established outlives the arm and is what the next SOCO session should start from: the CT_PEAKER/ST_GAS split is not a cost-side defect at all. Every offer band is the identity 1.0, so each class is a single flat price block and every curve-shaped lever is provably inert for SOCO by construction; the model already over-separates the two classes by 2.8× the measured CAMPD separation and still over-ran; and the real separation is commitment, with boilers running 94–144 hour campaigns and starting about ten times a year against turbines running 8–9 hour blocks and starting about fifty-eight, where the model gives both zero min-run and zero min-down. The open successor is `egrid_family_heat_rates`, the completing plant-blend repair over 26.0 % of SOCO's thermal capacity, whose numbers are already measured. Record: `docs/handoffs/FINDING-soco-53-2026-09-17.md` §7.
