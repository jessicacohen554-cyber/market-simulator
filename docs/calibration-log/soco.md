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

---

## soco-53c — 2026-09-19 — the plant-blend repair lands, and its own artifact needed repairing first

SOCO's keeper is now `2026-09-19-soco53c-egrid-family-hr` (bundle `results/calibration/soco53c_family`, recoverable at `c91dde5e4cfbecd4e1da14ebba9209923ef9d500`), and `2026-09-17-soco53-measured-ct-hr` is superseded and pruned. The owner ruled promote on the standing standard that a structural gain with a gate regression may still be a keeper — and the case turned out stronger than that standard required, because the gates did not regress. C1 all 12/14 and free 8/10 on both sides, the same two rows fail, C2/C4/C6/C8 pass on both, zero ledgered and zero protective caveats on both, grade_summary identical, and no row changed status in either direction. The two failing rows moved only in magnitude (2023 CT_PEAKER +9.85 → +10.09 TWh, 2023 ST_GAS −7.34 → −7.36), and C2's ungated 2025 coal row improved from +16.0 % to +12.4 %. Determination is NOT-YET both ways, C3a/b/c remain unscorable because SOCO publishes no price and never will, the DOF ledger is unchanged at three entries and one residual, every offer band is still exactly 1.0 and `authorized_price_tuning` is declared NONE.

The arm is the rule 14 repair of a physically impossible input. eGRID joins heat rate at plant grain, so every generator at a multi-technology plant inherits one generation-weighted blend: Victor J Daniel Jr priced 1,004 MW of coal at 8.399 MMBtu/MWh, which no coal boiler can attain and against which its own meter reads 12.895, and Barry priced 1,118.5 MW of coal, 1,821.2 MW of gas CC and 160 MW of gas steam all at 8.994965. The construction gives each prime-mover family its own heat input over its own net generation from the same eGRID vintage the plant-grain join already reads — zero free parameters, a finer read of the identical source — and it moves 24 generator rows and 6,473.2 MW at four plants.

The lane's real product is that the mechanism's own artifact was wrong at five of its nine SOCO plants, and the existing guard caught only half of it. The derive claims a family rate replaces the blend on the identical net-annual boundary; that is an identity rather than a description, because the plant rate is the same ratio over the union of the families, so it can be checked. Checked, it partitions the nine plants with three orders of magnitude to spare: four recompose at ratio 1.000 and five at 4.05 to 8.40. The five are cogeneration paper mills, and the cause is eGRID's own convention — the plant rate's numerator is steam-credited at a CHP plant while the unit sheet's heat input is raw fuel, so a family rate there charges the host's process steam to the electric output, Pensacola recomposing to 22.537 against a published 5.568. The pre-existing `out_of_window` guard is a per-family plausibility test and caught only the steam halves; the turbine halves landed inside 3,000–30,000 Btu/kWh and were being applied — four rows, 160 MW, onto CT_CHP and CC_CHP, the latter a scored C1 row. That is rule 14's misalignment exception verbatim, so a per-plant `boundary_mismatch` flag now refuses them and SOCO's artifact goes from twelve applied rows to eight. The guard is derive-side and never consumer-side, because a default-on consumer guard would have moved CAISO's keeper fleet from this lane; no `src/market_sim` file is touched. Its tolerance is a rounding allowance incapable of being tuned — every value between 0.001 and 1.8 gives the identical partition over all 26 covered plants in the three ISOs that carry an artifact.

Rule 19 was settled mechanically rather than declared. The family rate applies at frame level in `_rows_to_generators` and `measured_ct_heat_rates` applies inside the row loop gated on CT_PEAKER, so the precedence is measured CAMPD, then eGRID family, then eGRID plant blend — and CT_PEAKER's cap-weighted heat rate is byte-identical at 11.2666 on both sides, meaning Greene County's computed GT family rate of 14.105 and Watson's 21.925 are both entirely overwritten and nothing is priced twice.

The effect was predicted before the solve and confirmed, including the part that is unflattering: the PRECOMMIT registered that CT_PEAKER and ST_GAS would not materially improve, so this arm does not fix SOCO's headline defect. Coal fell 0.665, 1.855 and 1.528 TWh, CC_REGULAR rose 0.468, 1.915 and 1.947, and CT_PEAKER moved only +0.234, +0.399 and +0.157, inside the declared one-TWh falsifier. Two of the lane's own predictions were imprecise and are recorded as such — the coal fall was over-predicted at two to five TWh against 0.7 to 1.9 delivered, and the flagged 2024 CC_REGULAR break did not occur. Why CT barely moves is measured rather than asserted: CC_REGULAR sits at or above 99 % of its own annual maximum in only 44 of the 7,305 hours CT_PEAKER runs in 2023, so the split is a commitment defect and no cost change at four other plants can reach it. The successor is SOCO-53d, a multi-week-campaign commitment mechanism.

A control solve was spent and answered a cross-ISO question. G-DRIFT classified thirteen of fourteen changed solve-path files inert and one live: commit `fba0ecd7` added an emissions-dual re-pricing that runs unconditionally at the end of every solve for every ISO, and its byte-identity claim was a scorer claim over committed artifacts that no re-solve had ever tested. Rule 29(b) earns a control solve for exactly that, so one was spent: the keeper's own recipe re-solved at the pinned SHA reproduces the committed keeper bundle to 0.000000 TWh on every class in every year, with the two run_configs differing by exactly one field sitting at its default. `fba0ecd7` is byte-identical on a real ISO and form 4 was valid. Both bundles also carry the new marginal emission rate — load-weighted mean 0.633, 0.616 and 0.635 tCO2/MWh, with the share of zone-hours at exactly zero immaterial at 0.00, 0.00 and 0.15 %, which corrects this lane's own expectation that SOCO's export-heavy posture would produce a material zero share. Record: `docs/handoffs/FINDING-soco-53c-2026-09-19.md`.

---

## soco-53d — 2026-09-19 — the model runs SOCO's steam boilers like peaking turbines

SOCO's gas boilers start five to ten times a year and are synchronized between 64 % and 92 % of all hours. The model gives every one of them `min_run_hours = min_down_hours = 0`, no committed state at all, and cycles the same plants 10 to 349 times a year in blocks of two to eleven hours median. It is operating a 3,131 MW steam fleet as if it were a peaking fleet, and buying the energy a synchronized boiler's minimum-load block would carry from combustion turbines instead. That is the root cause SOCO-53 named and SOCO-53c could not reach, and this lane arms it: `ScenarioConfig.soco_gas_st_campaign_commitment`, the shared ISO-neutral detector run on `gas_st` alone with exactly two of its legs — the measured minimum-run extension and the online-hours minimum-stable-load state floor.

Three things are refused before the solve, each with its reason rather than by omission. The restart legs stay off because SOCO's boilers do not two-shift — 98.6 % of their measured downtime-hours sit in gaps longer than 72 hours, which is the `R` verdict SOCO-53 already recorded on `gas_commitment_bridge` and which this lane therefore does not re-test. The commitment-real run screen stays off because it asks whether a unit's margin against an LMP repays its startup cost, which is a merchant test on a footprint with no LMP, no offers and no market — the same ground on which `tranche_startup_amortization` is refused here. And no CT leg is armed, because the model already reproduces SOCO's turbine run shape and gets only the number of starts wrong, so a minimum-run floor would push CT the wrong way.

Level, horizon and membership are per-plant measured rows of a new derive artifact built from SOCO's own CAMPD boiler record, with boiler unit types paired to each plant's own model `gas_st` rows by capacity rank. Zero free parameters were added and the DOF ledger is unchanged at three entries and one residual. The derive refuses Barry on its own meter — its two 80 MW boilers are synchronized 6.3 % of the year, standby iron rather than campaign iron — and the committed floors confirm Barry carries zero floored unit-hours in all three years. The campaign-duty gate selects nothing: SOCO's population separates by an order of magnitude, so every value between 0.07 and 0.63 gives the identical partition, and it was declared in the PRECOMMIT and never swept.

The gates improve, and that falsifies this lane's own prediction. The PRECOMMIT declared the failing-row set unchanged; instead the 2023 `ST_GAS` row crosses back into band, from −7.359 TWh and −3.07pp to −6.972 and −2.91 against bands of ±7.19 TWh and ±3.00pp, so C1 goes from two failing rows to one and C1 all/free from 12/14 · 8/10 to 13/14 · 9/10. The pass is narrow — 0.09pp of share margin — and is recorded as narrow rather than banked. 2023 `CT_PEAKER` stays failed at +9.898 TWh, so the headline defect is not fixed, and the PRECOMMIT said so first, having measured before the solve that the floor's marginal class is `CC_REGULAR` in 1,170 of the 3,988 incremental hours against `CT_PEAKER` in only 681. Determination is NOT-YET both ways. Two other predictions are scored honestly as misses: the ST_GAS gain landed just below its declared band in two years, and the forced-share prediction was over-called by roughly a factor of two because the offline estimator summed the floor array rather than reproducing D-2's own construction.

The result that does not depend on a gate is the shape. D-1's `ST_GAS` off-peak coefficient of variation falls from 0.709, 0.864 and 0.608 to 0.545, 0.658 and 0.448, toward the measured 0.281, 0.263 and 0.207, with the ratio staying comfortably above its floor — the signature of replacing turbine conduct with campaign conduct on a class the model was cycling hundreds of times a year against a metered handful. Rule 17 holds by measurement in all twelve plant-years: every delivered binding share lands at or below that plant's own synchronized share, and the floored blocks have a median length of 86 to 459 hours, so what the mechanism places are campaigns rather than gap fills. Rule 20 passes on the budget at forced shares of 0.094, 0.100 and 0.116 against a 30 % cap, and D-4's off-window share is exactly zero in all three years. One changed solve-path file since the keeper's basis was audited INERT mechanically, so no control solve was spent, and over all twenty committed run configs zero cache keys move at the new field's default.

The lane also falsified the premise it was handed. The handoff stated that cost levers are exhausted; on `ST_GAS` they are not, and the predecessor's own arm made it so. `measured_ct_heat_rates` moved `CT_PEAKER` to 11.2666 while `ST_GAS` still rides eGRID at 10.9613, and SOCO's gas-steam fleet measures 10.4223 on its own CAMPD meter — the model is 5.2 % too dear on 3,131 MW, with Gaston out by −0.909 alone. SOCO-53's "the model over-separates the classes by 2.8×" was measured on the pre-arm fleet; at HEAD the model under-separates by 2.3×, which is the sign of the defect. `measured_st_heat_rates` is the exact sibling of SOCO's promoted keeper mechanism, a pure rule-14 repair with zero free parameters, probably the larger lever, and it is routed as SOCO-53e rather than stacked here. The promotion of this run is open and is the owner's; the keeper is unchanged, nothing was pruned, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. Record: `docs/handoffs/FINDING-soco-53d-2026-09-19.md`.

---

## soco-53d promotion — 2026-09-19 — the owner ruled, and SOCO's keeper is the campaign-commitment run

The owner ruled promote, on the standing standard: *"If structural integrity improves but gates regress that may still be a keeper."* The case turned out stronger than that standard required, because the gates did not regress — they improved. SOCO's keeper is now `2026-09-19-soco53d-campaign-commitment` (bundle `results/calibration/soco53d_campaign`; the slim and `hourly/` set committed, the full 33-file bundle including `dispatch/{2023,2024,2025}_P1.parquet` recoverable at `730ae912e0e608695e3425e00daa00ad18138706`), and `2026-09-19-soco53c-egrid-family-hr` is superseded and pruned.

The 2023 `ST_GAS` row crosses back into band, from −7.359 TWh and −3.07pp to −6.972 and −2.91 against bands of ±7.19 TWh and ±3.00pp, so C1 goes from two failing rows to one and C1 all/free from 12/14 · 8/10 to 13/14 · 9/10. The pass is narrow — nine hundredths of a percentage point of share margin — and it is recorded as narrow rather than banked. 2023 `CT_PEAKER` stays failed at +9.898 TWh, so SOCO's headline defect is not fixed, and the PRECOMMIT said so before the solve, having measured that the floor's marginal class is `CC_REGULAR` in 1,170 of the 3,988 incremental hours against `CT_PEAKER` in only 681. Determination is NOT-YET either way, so the promotion neither gained nor lost a determination. C2's ungated 2025 coal row improves from +12.3 % to +12.1 %; C2, C4, C6 and C8 pass on both sides; there are zero ledgered and zero protective caveats on both; and the DOF ledger is unchanged at three entries and one residual, because this lane added no free parameters at all.

It was executed in rule 35's fixed order, each step gating the next. The year union was enumerated over every SOCO sidecar before anything was pruned and is 2023–2025 on both runs, which the incoming bundle carries in its own single invocation, so no `holdout.keeper` stamp was needed and none was invented. The keeper shard was re-pointed with a structured `superseded.former_keeper` lineage, the status part rebuilt, and `audit_keepers` E1 and E11 both verified green *before* the prune — E11 demonstrably live this time, since the outgoing bundle was still on disk. Only then did `prune_iso_runs.py --iso SOCO --force-uncite` remove the outgoing keeper's three stores together. `audit_keepers --check --iso SOCO` now passes with zero failures and the rule 35(f) invariant holds: one registered SOCO run, it is the keeper, and the year set is no smaller.

Because rule 35(a)'s prune destroys E11's baseline, the diff E11 certified is written into the record rather than left to a gate that can no longer run it. **Of 853 `scenario_config` fields exactly one differs: `soco_gas_st_campaign_commitment`, absent → True, the declared mechanism. Zero mechanisms were silently de-armed** — a cleaner lineage than the SOCO-53 promotion's, which carried a second field arriving at its default.

The promotion was re-audited against a `main` that had moved 27 commits since the solve. Both new solve-path mechanisms — NWPP-42's `measured_coal_heat_rates` and SPP-48's `mid_vintage_exit_carry` — are default-off, absent from both SOCO recipes, and the cache key is stable with them present at default, so both bundles remain reproducible at HEAD and the A/B comparison is untouched. SOCO's bench parts were again deliberately not rebuilt, for the reason SOCO-53c gave: `check_bench_freshness` is red on 31 of 44 parts across every ISO from another lane's edit to a payload source, and rebuilding SOCO's alone would have scored the arm against a different benchmark from its control. Recorded for the owner: on the rebuilt bench the arm reads the same 13/14 · 9/10.

What outlives the arm is the measurement the lane made on the way, and it falsifies the premise the lane was handed. The cost side is not exhausted on `ST_GAS`, and the previous keeper's own mechanism made it so: `measured_ct_heat_rates` moved `CT_PEAKER` to 11.2666 while `ST_GAS` still rides eGRID at 10.9613, and SOCO's gas-steam fleet measures 10.4223 on its own CAMPD meter — the model is 5.2 % too dear on 3,131 MW, with Gaston out by −0.909 alone. SOCO-53's "the model over-separates the two classes by 2.8×" was measured on the pre-arm fleet; at HEAD the model under-separates by 2.3×, which is the sign of the defect. `measured_st_heat_rates` is the exact sibling of this ISO's previous keeper mechanism, a pure rule-14 repair with zero free parameters, probably the larger lever, and it is the open successor. It was not armed here because rule 19 forbids stacking a second mechanism on the same phenomenon in one run — and this keeper's floor binding pattern depends on a cost input known to be wrong in a stated direction, so its binding shares are owed a re-measurement once SOCO-53e lands. Record: `docs/handoffs/FINDING-soco-53d-2026-09-19.md` §8.

## soco-53e — 2026-09-19 — a per-unit meter separates two boilers that share a prime mover, and the lever is a fifth the size it was routed at

A southeastern steam station is routinely a coal boiler and a gas boiler behind one ORIS code, and because both machines are prime mover ST, the eGRID plant rate blends them and so does the prime-mover-family rate this lane's own predecessor armed. Only a per-unit meter can separate two boilers inside one family, and that is what `ScenarioConfig.measured_st_heat_rates` does: the gas-steam sibling of `measured_ct_heat_rates` and `measured_coal_heat_rates`, on the identical seam, the identical identification and the identical artifact schema, default off and byte-identical off. At E C Gaston it moves 1,020 MW of gas steam from a coal-blended 11.5505 to its own metered 11.0744, which independently reproduces the 10.887 eGRID gas-steam sub-family rate SOCO-53c routed as a separate lever — two sources agreeing, so this mechanism subsumes that routing rather than competing with it.

The lane's first act was to correct the number that commissioned it, before spending an LP. SOCO-53d §8.1 routed "+0.539 MMBtu/MWh, +5.2 %, too dear on 3,131 MW, worth $1.5–3.3/MWh", and that figure converted SOCO's boilers at the CT_PEAKER parasitic factor 0.99 where the ST_GAS class factor is 0.95. Phase 0 re-derived from scratch rather than inheriting, reproduced 53d's table to ±0.03 at 0.99 — so the arithmetic was right and the class was wrong — and then settled the basis by measurement rather than convention: SOCO's gas-steam fleet's own metered net/gross over its eight unambiguous plant-years is 0.938 to 0.943, which the committed 0.95 default reproduces to 1.2 % and 0.99 misses by 5.5 %. On the right basis the capacity-weighted level moves 10.9613 to 10.8522, minus one percent, not minus five. The lever is real and it is a fifth the size it was sold at, and that was in the PRECOMMIT before the solve rather than in the write-up after it.

What survives, and is the actual case, is the per-plant structure: Gaston −0.476 on 1,020 MW, Greene County −0.049, Jack Watson −0.053, Yates −0.017, and Barry +1.374 the other way. Barry is applied at full magnitude — two 1954-vintage 80 MW boilers metered at 13.98 over 2,521 steady hours with 98 % of them inside the physical band, a genuinely poor machine run 1.6 % of the time. Rule 14's misalignment exception does not apply because the rate sits on the same boundary as the one it replaces, and the result independently corroborates SOCO-53d's campaign-duty gate refusing Barry at a 6.3 % synchronized share. Membership is a capacity-rank pairing to each plant's own model boiler rows rather than the coal sibling's fuel tag, because CAMPD files Barry unit 4 — a 330 MW boiler — as Pipeline Natural Gas while the model carries it as a 362 MW coal row, so a fuel-tag selection would have priced two 80 MW ST_GAS rows off a boiler the model dispatches as coal. The pairing cannot change an applied number and that is checked rather than asserted: the artifact is at plant grain, and `--check-pairing` re-runs membership under an exact generator-id rule and reports the applied rows identical.

Zero free parameters were added and the DOF ledger is unchanged at three entries and one residual. The physical band is measurably inert — every plausible band moves the capacity-weighted result by less than 0.03 MMBtu/MWh — and the gross-to-net factor is the committed class default, not a value this lane chose. Rule 19 is established mechanically at two grains: twelve of 393 built-fleet rows and twenty of 327 LP rows move, all ST_GAS, with COAL, CT_PEAKER, CC_REGULAR, all three CHP classes and hydro byte-identical at max delta exactly zero. It is a new default-off field rather than a widened `measured_ct_heat_rates`, because widening would arm five other ISOs' keepers on a measurement their lanes never made.

The gates do not move and every scored row improves. Determination NOT-YET both sides, C1 all 13/14 and free 9/10 both sides, C2/C4/C6/C8 passing, zero ledgered and zero protective caveats. 2023 CT_PEAKER stays the single failure at +9.90 to +9.82 TWh, so SOCO's headline defect is not fixed and the PRECOMMIT said so first with the number — a headroom-capped hourly displacement upper bound of +0.066, +0.154 and +0.053 TWh against delivered ST_GAS of +0.090, +0.188 and +0.085. The row the handoff flagged as at risk got safer rather than riskier: the 2023 ST_GAS share margin widens from 0.09pp to 0.12pp against its ±3.00pp band. Nine of nine ex-ante predictions hold, and the reason is worth stating rather than claiming credit for — this lane's object is a cost input whose effect is computable without an LP, so the arm's delivered per-plant marginal costs reproduced the zero-LP offer-array prediction to four decimals, where a commitment floor runs through a P0 pattern no offline estimator reproduces.

Two things are reported against the lane. D-1's shape evidence is mixed — the ST_GAS cv_ratio improves in 2024 and 2025 and degrades in 2023, all six values passing — so this lane claims no shape win where its predecessor could. And the arm creates an asymmetry it does not close: Gaston's coal row still carries the blended rate, now roughly 0.5 MMBtu/MWh too cheap for a coal machine, which `measured_coal_heat_rates` would close with only a SOCO artifact and which is routed rather than absorbed. The rule-17 re-measurement SOCO-53d owed was performed on this bundle's own floors and holds in all twelve plant-years, with Barry still carrying zero floored hours and floored blocks keeping a median of 87 to 459 hours. One further finding for the SOCO desk: `parasitic_load_factors.parquet` has never been derived for SOCO, so every SOCO plant falls back to a class default. The promotion is open and is the owner's; the keeper is unchanged, nothing was pruned, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. Record: `docs/handoffs/FINDING-soco-53e-2026-09-19.md`.

## soco-53e promotion — 2026-09-19 — the owner ruled, and SOCO's keeper is the measured-ST_GAS-heat-rate run

The owner ruled "Promote" on the SOCO-53e candidate, and lane SOCO-53e executed it under rule 35 `[R-PROMOTE]` in the same session. SOCO's keeper is now `2026-09-19-soco53e-measured-st-gas` (bundle `results/calibration/soco53e_st_hr`), superseding `2026-09-19-soco53d-campaign-commitment`, whose three stores — registry sidecar, run payload and bundle — were removed together by `prune_iso_runs.py --iso SOCO --force-uncite` after the incoming keeper had been verified, not before. `--force-uncite` was the intended route rather than a safety override: the only citation blocking the prune was this lane's own `superseded` history block in the keeper shard, which rule 35(d) says stays as the audit trail. The outgoing bundle is recoverable in full at `730ae912e0e608695e3425e00daa00ad18138706`, and git history is the record.

The order rule 35 fixes was followed rather than improvised. The year union was enumerated before anything was deleted — `{2023, 2024, 2025}` across both registered runs, no folded touchpoints and no dangling holdout stamp — and the incoming keeper covers all three in one invocation, so the promotion shrinks nothing. The lineage diff was captured while both bundles were still on disk, which is the evidence the prune destroys: over all 856 `scenario_config` fields the outgoing and incoming recipes differ in three, and only one is solve-affecting, `measured_st_heat_rates` absent to true. The other two, `measured_coal_heat_rates` and `mid_vintage_exit_carry`, did not exist at the outgoing keeper's basis `0b3f2fdc` — nwpp-42 and spp-48 added them afterwards — and sit at their inert defaults, exactly as the PRECOMMIT's G-DRIFT audit had classified them before the solve. `calibration-complete.json` was deliberately not touched: SOCO has never had an entry there, because its determination is NOT-YET rather than complete. The status part was rebuilt, the matrix shard's keeper and gates stamps were rewritten, the `measured_st_heat_rates` cell moved from `O` to `K`, and the §5.8 prose header was re-stamped in the same session, all of which `check_mechanism_matrix` verifies. `audit_keepers --check --iso SOCO` now returns zero failures, with E13 cleared.

The promotion surfaced one defect, and it belongs to this lane rather than to the mechanism. `audit_keepers` E14 fires four times on the new keeper: its solve shard installed unpinned dependencies and ran on highspy 1.15.1, pandas 3.0.6, pyarrow 25.0.1 and pydantic 2.13.5, where `requirements.txt` pins 1.14.0, 3.0.3, 24.0.0 and 2.13.4 and where the control had solved on exactly those pins. The cause is a line in this lane's own shard prompt that said `pip install numpy pandas pyarrow pydantic scipy highspy` instead of `pip install -r requirements.txt`, on a container image that ships without the scientific stack. So the A/B differs in the LP solver version as well as in the mechanism, and that is recorded rather than buried. What bounds it: differencing the arm against the control over all 45 class-years, 28 are exactly 0.0 MWh — bit-identical — across ten classes including nuclear, hydro, wind, solar, biomass and oil, which a solver re-selecting among degenerate optima would not produce in three separate years; and the classes that do move are precisely the ones the mechanism prices, in the predicted direction, with per-plant marginal costs reproducing the zero-LP prediction to four decimals. That is strong evidence and not proof, so a pin-confirm re-solve of the identical config on `pip install -r requirements.txt` was launched in the same session. Two consequences beyond SOCO: every shard prompt in this repo should pin from `requirements.txt`, and the container image no longer carrying the pinned stack is an environment finding for the desk rather than for this ISO.

The keeper itself is unchanged in substance from the candidate: determination NOT-YET (rubric v3.8, PRICE UNSCORED) — SOCO can never read CALIBRATED — C1 all 13/14 and free 9/10, C2/C4/C6/C8 passing, zero ledgered and zero protective caveats, DOF unchanged at three entries and one residual, and zero free parameters added. Every scored C1 row improves and none changes status, with the 2023 ST_GAS row that its predecessor passed by 0.09pp of share margin widening to 0.12pp. 2023 CT_PEAKER remains the single failure at +9.82 TWh, so SOCO's headline defect is still open, and the two things reported against the keeper stand: D-1's ST_GAS shape evidence is mixed rather than a win, and Gaston's coal row is left on the same blended rate and is now roughly 0.5 MMBtu/MWh too cheap, routed to `measured_coal_heat_rates` rather than absorbed. Record: `docs/handoffs/FINDING-soco-53e-2026-09-19.md` §10.

## soco-53f — 2026-09-20 — an annual average is not a weighted mean, so the measurement reversed the sign of the premise, and a control solved for one reason closed two other questions

The premise that commissioned this lane was wrong in sign, and the measurement said so before an LP was spent. FINDING-soco-53e §7.1 routed SOCO-53f on the reading that E C Gaston's coal boiler, left on the blended ST family rate 11.5505 after its four gas boilers were repriced, is "roughly 0.5 MMBtu/MWh too CHEAP for a coal machine". Its own meter reads 11.0505 — 0.5000 too DEAR, the magnitude right to four decimals with the sign inverted. The routing treated the plant rate as a weighted mean between two machines, so the coal side had to sit above it; it is not a mean but an eGRID ANNUAL average, PLHTIAN/PLNGENAN, which folds startup fuel, shutdown tails and the offline hours' bank fuel into the number that sets the offer and therefore sits above both machines' operating rates rather than between them. That is the entire thesis of the mechanism, and Gaston is the case that shows it. So the arm is not the asymmetry-closer it was routed as; it is something larger. All six plants get cheaper — Barry −1.8711, Daniel −0.9687, Scherer −0.8690, Gaston −0.5000, Bowen −0.4040, Miller −0.1022 — capacity-weighted 11.5267 to 10.8926, −5.5 %, across 100 % of an 11.5 GW fleet, five times the capacity the gas-steam sibling touched.

No ScenarioConfig field was written and no free parameter added: nwpp-42 shipped the mechanism one day earlier and it was a strict no-op for SOCO until this lane derived SOCO's artifact (campd_coal_heat_rates_SOCO.csv, sha256[:16] efd5926eecc62d8f, 6/6 plants / 11,512.0 MW, 252,093 in-band steady hours at 15 units). A provenance repair landed with it and it changed the number: nwpp-42's deriver read its model_heat_rate_egrid comparison column off the loader-default fleet, which for SOCO is a fleet nobody solves — it reported Barry at 8.9950 and Daniel at 8.3995, the physically impossible plant blends egrid_family_heat_rates exists to remove, and so claimed the measured rates were dearer than the model's. The three provenance flags the gas-steam sibling already takes were added, with a model_recipe column and a guard that the provenance recipe cannot move plant membership; no applied number changes and the 14 committed tests pass unchanged. Rule 19 is machine-verified at two grains: 16 of 393 built-fleet rows and 25 of 327 LP rows move, all COAL, with ST_GAS — repriced by soco-53e one day earlier and sharing plant codes 3 and 26 with this population — byte-identical at max delta exactly 0.000000000000.

The gates do not move and eight of the ten gated non-CHP rows improve. Determination NOT-YET (rubric v3.8, PRICE UNSCORED) on both sides, C1 all 13/14 and free 9/10 on both sides, C2/C4/C6/C8 passing, zero ledgered and zero protective caveats, DOF unchanged at 3/1, and zero C1 status flips on either the committed or the HEAD-rebuilt bench. 2023 CT_PEAKER +9.82 to +9.73 TWh and still the single FAIL, 2024 CT_PEAKER +6.38 to +5.81, 2024 COAL_BIT −1.15 to −0.55, 2023 COAL_PRB −2.33 to −2.13, 2024 COAL_PRB −3.57 to −3.44, CC_REGULAR +2.63 to +2.60 and +5.12 to +5.03; against 2023 ST_GAS −6.88 to −6.93 and 2024 −5.21 to −5.28. The PRECOMMIT registered the 2023 ST_GAS row as a coin flip in both directions, its 0.369 TWh displacement bound against a 0.288 TWh margin; it survived, margin 0.288 to 0.250. SOCO's headline defect is untouched, as the PRECOMMIT said first with the number: 2023's displaced class is 64 % ST_GAS and only 9 % CT_PEAKER, so the arm closes about half a percent of a nine-TWh failure. The rule-17 re-measurement holds in all twelve plant-years and the binding shares fall or hold in every one, Barry keeping zero floored hours and floored blocks a median of 64 to 342 hours.

A control this lane had to solve for its own A/B closed two open governance questions, and they may outlast the arm. First, SOCO's keeper E14 dependency drift is cosmetic: a seventh shard re-solved the control recipe for 2023 on the keeper's off-pin set (highspy 1.15.1 / pandas 3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5) and the result is bit-identical — 0 of 131,400 class-hourly cells, 0 of 26,280 price cells, 0 of 26,280 marginal-emission cells. FINDING-soco-53e §10.3 left that bounded because its pin-confirm was abandoned; it is now closed. Second, rule 36's "unmeasured outside MISO" year-grouping cost is measured at SOCO and is zero: the year-isolated control reproduces the keeper's annual class generation to exactly 0.000000 MWh on all 45 class-years and its scored C1 rows reproduce the keeper's registered numbers exactly, with only intra-class timing moving (279/364/32 hours of 8,760, every cell offset within its own class, mostly budget-pinned hydro) and prices by at most 0.141 $/MWh. That is one ISO's answer and transfers to none.

Reported against the lane. Prediction P9 was falsified: the marginal emission rate was predicted to rise and fell in all three years (0.6263 to 0.6255, 0.6090 to 0.5921, 0.6369 to 0.6161), because the prediction reasoned about which machine produces the energy where the marginal rate is set by which machine sets the price — cheaper coal runs inframarginally and hands the margin to a combined cycle rather than taking it from a peaker. Eleven of twelve predictions hold; that one does not, and it is scored as a miss. D-1 trades a verdict in 2024 (COAL_BIT FAIL to pass, COAL_PRB pass to FAIL, neither gating since no COAL class is forced). The arm adds +1.5632 TWh to a 2025 coal excess whose cause is SOCO-53b's hydro input hole — 0.327 TWh modelled against 6.012 measured — not coal pricing. The committed COAL parasitic default 0.93 does not reproduce SOCO's own meter (0.866–0.928 on the four single-fuel sites); it is used anyway because it is the same factor the benchmark's net actual is built with, and the consequence is stated: the applied rates are biased low by 1.5 to 5.9 %, so the cheapening is if anything understated. And the benchmark moved under this lane: the HEAD-rebuilt EIA-923 carries nyiso-240's repair, which adds +2.616 TWh to SOCO's benchmark across 126 rows, while campd and eia930 rebuild byte-identical — the decomposition is exact, because the control's dispatch is identical to the keeper's, so none of that difference is this mechanism.

Routed and larger than this lever: coal_prb_proxy_own_iso as SOCO-53g. SOCO's three PRB plants — Miller, Daniel and Scherer, 55 % of its coal capacity — are priced off the hand-curated ERCOT-only reporter pool at 1.8228/1.7520/1.6147 $/MMBtu against their own 2.6711/2.4982/2.4610, an under-pricing of about $9.7/MWh against this lane's $2.95 and in the opposite direction, so this arm makes coal cheaper on three plants the model already prices far too cheap on fuel. Seven per-year shards under rule 36, each pushing a full 16-file bundle, composed at zero LP with no re-solves; every leg recoverable by immutable SHA and recorded in .gitignore, so a promotion costs nothing. The promotion is open and is the owner's. Record: `docs/handoffs/FINDING-soco-53f-2026-09-20.md`.

## soco-53g — 2026-09-20 — the $9.7/MWh defect that never reaches the LP, and a cell that was already adjudicated

FINDING-soco-53f §9 item 1 commissioned this lane on a measured claim: SOCO's three PRB plants, 6,361.5 MW and 55 % of its coal capacity, priced off the hand-curated ERCOT-only reporter pool at 1.8228/1.7520/1.6147 $/MMBtu against their own 2.6711/2.4982/2.4610 — an under-pricing of 47–52 %, about $9.7/MWh, "three times SOCO-53f's lever, in the opposite direction". Both pooled numbers are correct and reproduce to four decimals. The inference from them is wrong, and for a structural reason: neither pool reaches the LP. In the calibration path apply_coal_supply_pricing writes the proxy onto SOCO's 15 PRB tranche rows and apply_plant_monthly_fuel_prices overwrites it three lines later with each plant's own filed EIA-923 monthly delivered cost, 8,760 of 8,760 cells on every one of those rows in 2023 and 2024. The model prices Miller at 2.1886, Daniel at 3.8505 and Scherer at 3.3945. Rule 14 was already being honoured at SOCO, one layer further down. The mutation-sequence decomposition is exact: step 2 moves 15 rows by 0.958/0.832/1.054 $/MMBtu, step 3 returns 0.000000000000, 0.000000000000 and 0.649940697470.

The solve confirmed the zero-LP prediction and exceeded it. 2023 and 2024 are byte-identical to the keeper — the same sha256 on floors/, dispatch/<y>_P1.parquet, system.parquet and unit_hourly, solved independently in separate containers at a different HEAD whose solve-surface fingerprint had moved, which is itself the cleanest confirmation of the G-DRIFT audit this lane could have produced. 2025 differs in 4 of 657,000 class-hour cells: a 2.2 MW degenerate tie swap between a Georgia CT_PEAKER tranche and a 2.2 MW hydro unit at identical marginal costs, in hours 8098 and 8217 — December, not January — netting to exactly 0.0 MWh. Annual class generation is 0.000000 TWh apart on all 45 class-years, system.parquet is identical in all three years so prices and marginal_emission_rate (0.6255/0.5921/0.6161) do not move at all, and all 21 C1 rows reproduce the keeper's exactly on both the committed and the HEAD-rebuilt bench. Determination NOT-YET (rubric v3.8, PRICE UNSCORED), identical to the keeper on every criterion, grade, caveat count and DOF entry: C1 FAIL on one row of fourteen (2023 CT_PEAKER +9.73 TWh / +4.0pp), C2/C4/C6/C8 PASS, C1 all 13/14 · free 9/10, 0 ledgered and 0 protective caveats, DOF 3/1, zero ScenarioConfig fields and zero free parameters. Rule 17 re-measured on this bundle's own floors npz with a tool first validated against the keeper's fifteen cells: holds in all twelve plant-years, every cell identical, Barry still zero floored hours.

The offer does move and no MW follows. 2,976 unit-hours of Victor J Daniel Jr's four coal tranches carry +7.7512 $/MWh — mean equal to min equal to max — across all 744 January-2025 hours, the one plant-month where SOCO has no measured price of its own, because Daniel filed no January receipt and the nearby-plant fallback did not reach it. Daniel's armed mc of 27.37 $/MWh is still about 29 below the January mean system price of 56.29, so it stays deeply inframarginal. Prediction P3 is falsified in substance: I predicted the lift would displace 0.000–0.141 TWh of COAL_PRB and it displaced exactly 0.000000, because I never checked where those rows sat relative to the price. That check was one join away in the committed bundle and I read both files in the same session for other purposes. It is the same class of error 53f's P9 made — reasoning about a machine's cost without asking where the cost sits relative to the price that clears — and it is now two lanes running. Seven of eight predictions held, including byte-identity in both gated years.

Recorded against the lane, and it leads the write-up: the matrix cell was ALREADY adjudicated I by NWPP-41 on 2026-09-17, and this lane read it only after launching its shards, which rule 28(a) and the SessionStart hook both forbid. 53f routed the lane without checking it either, so the miss is two lanes deep. What makes the work admissible rather than a redo is that it produced new evidence and that evidence corrects the cell: NWPP-41 censused at the plant-YEAR grain and concluded "nothing to arm unless a SOCO PRB plant stops reporting", and that sentence is falsified — all three SOCO plants do file every year, and Daniel still skips one month. The grain that matters is the plant-MONTH, and even that is an upper bound, since Scherer also missed a month and the nearby fallback covered it. Re-censused cross-ISO at the plant-month grain and routed, never adjudicated (rules 25/28(d)): MISO 38 PRB plants and 484 missing plant-months, SPP 29 and 216, NWPP 9 and 180, ERCOT 7 and 181, PJM 2 and 72, SOCO 3 and 2 — so the docstring's "MISO (12), PJM (2), SPP (3–5)" understates the populations badly, and only 2 of the 7 hand-curated COAL_PLANT_SUPPLY plants file anything at all. The recommendation to the owner is NOT to promote this run, on the ground that the standing "structure improves, gates regress" rule does not reach it — the gates do not regress and structural integrity does not measurably improve — but to arm the mechanism as a declared posture in backcast_config.py beside NWPP if it is wanted, for which this run is already the complete three-year A/B evidence. Three per-year shards under rule 36, each pushing a full 16-file bundle, composed at zero LP with no re-solves; every leg recoverable by immutable SHA and recorded in .gitignore, so a promotion costs nothing. All three shards archived. Record: `docs/handoffs/FINDING-soco-53g-2026-09-20.md`.

## soco-54 — 2026-09-20 — SOCO's gas steam was priced out of its own merit order by a contract multiplier, and removing it closes C1

**Keeper UNCHANGED** at `2026-09-20-soco53f-measured-coal-hr`; nothing pruned. Registered
`2026-09-20-soco54-marginal-gas-basis` (bundle `results/calibration/soco54_marginal_gas`) as a
**candidate; promotion is OPEN and is the owner's** (rule 31 `[R-RETAIN]`). Full 2023–2025 span, one
shard per year (rule 36), composed at zero LP; G-DRIFT all-INERT so form 4 stood and **no control
solve was spent**.

**The arm is one field turned OFF** — `gas_plant_monthly_fuel_pricing` back to its own shipped
default. **Zero new fields, zero free parameters**, DOF 3 entries / 1 residual unchanged.

**RULE 28(a) FIRST.** `gas_commitment_bridge` (`R`), `tranche_startup_amortization` (`G`),
`coal_prb_proxy_own_iso` (`I`) all left untouched; the arm sits on a `U` cell.

**THE ROUTED LEVER WAS REFUSED EX ANTE ON MEASUREMENT.** The campaign floor already holds SOCO's
boilers online 659–7,234 h/yr **pinned at a median 6–14 % of capacity**, out of merit in 65–93 % of
those hours (Yates 2023: online 659 h, in-merit in 7.3 %). In-merit-but-off `ST_GAS` headroom is
**0.0727 TWh against a −6.935 TWh gap**. A start cost amortizes to ≈$1.28/MWh against a $17.44/MWh
distance, on turbines running 62–74 % CF in blocks up to 760 h.

**THIS CORRECTS THE 53/53c/53e/53f DIAGNOSIS.** "No cost-side lever can close it" was derived from
**heat rates alone** and holds there. The separation that binds is **FUEL PRICE**: eight SOCO plants
file one common monthly shape × a plant-constant multiplier in **all three years** at CV ≤ 0.00081,
and the multipliers **reprice** — Yates 1.8279 → 1.1669 → 0.7959 against Hartwell, whose own 2023
print sits below Henry Hub in 11 of 12 months. The model burned **4×–160×** the gas these plants
procured. Rule 14's misalignment clause governs; the fall-back is **measured-to-measured** (realized
Henry Hub + SOCO's own EIA-923 basis, SOCO-20).

**RESULT — BOTH BENCHES, BECAUSE THEY DISAGREE ON ONE ROW.** Committed: arm
**`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`**, C1 **14/14 · free 10/10** — SOCO's ceiling, first time
— vs keeper `NOT-YET` / 13/14. Fresh: both `NOT-YET` / 13/14, failing row **moves** from 2023
`CT_PEAKER` to 2024 `CC_REGULAR`. **On both benches 2023 `CT_PEAKER` CLOSES**: 14.261 → 10.668 TWh
(actual 4.534), +4.05pp → **+2.55pp** against ±3.00pp. **The ceiling rests on 0.05 TWh** — 2024
`CC_REGULAR` at +7.417 of ±7.47, which PRECOMMIT P4 pre-registered as this arm's risk at 81 % of its
margin. C2/C4/C6/C8 PASS; C3a/b/c UNSCORABLE; 0 ledgered, 0 protective.

**Plant grain 2023:** Hartwell 1.728 → 0.111 (0.207), Hawk Road 2.209 → 0.228 (0.569), Doyle 1.038 →
0.072 (0.054), McIntosh 0.682 → 0.053 (0.017), Greene Co 0.574 → 1.196 (1.314). **Against the lane:**
Tenaska Georgia 1.412 → **2.690** (0.237) is made worse; Jack Watson 2.355 → 1.256 (3.270) moves the
wrong way; Yates still at 36 % of actual. **Rule 17 holds in all fifteen plant-years** and Yates's
commitment goes from **11× under to 1.7× under**. D-1 **3 failures → 2**.

**THREE OF TWELVE PREDICTIONS FALSIFIED** and §6 leads with them: P1's band too tight (−2.45 vs
**−3.592**), P8's coal band too tight (<1.0 vs **+1.481** `COAL_PRB`), P12's forced-share direction
wrong (it **rises**, 0.0855 → 0.1375, C8 still passing wide). All three are second-order
consequences of one modelling error — cheaper gas steam changes the P0 pattern the floor is detected
from.

**Post-registration audit (`calibration-keeper-auditor --iso SOCO`) caught a published-text defect
and it was MINE.** My shard prompts omitted `--note`, so `replay_keeper` fell back to its default
`model_changes_note` ("BTM-basis re-solve … adding btm.parquet") and `dashboard_add_run` copied it
verbatim into the registry sidecar's `definition` — describing a different mechanism entirely. Baked
into all three legs at solve time; 53f's shards passed `--note` and its sidecar is correct. The
sidecar was rewritten from the attestation's machine-verified governance block, with two clauses of
the auditor's draft tightened first (its "coal … unchanged at max |Δ| 0.000000000000" is a
marginal-COST statement that reads as a dispatch claim — 2023 `COAL_PRB` moves +1.481 TWh — and the
determination shift is bench-dependent and must not be asserted bare). **Every shard prompt should
pass `--note`.**

**Gates:** matrix PASS; `audit_keepers` **E13 × 2** (two unruled candidates — 53g's and this one,
**re-raised not cleared**) + E11 (pruned predecessor); parity RED **locally only** (six gitignored
leg dirs, 0 tracked on HEAD); `check_cache_key_registration` and `check_bench_freshness` RED at HEAD,
not this lane's. **Nothing was deleted.** All three shards archived. **Promotion question put to the
owner.**

**PROMOTED 2026-09-20, same session, on the owner's ruling** (*"If so plz promote"*). SOCO's keeper is
now `2026-09-20-soco54-marginal-gas-basis`. Rule 35 `[R-PROMOTE]` in order: year union `{2023,2024,2025}`
enumerated **before** any delete and fully covered by the incoming bundle; keeper shard re-keyed and
`build_status.py --iso SOCO` rebuilt; **E1 verified clean on the incoming run**; then the outgoing
`2026-09-20-soco53f-measured-coal-hr`'s three stores pruned via `--force-uncite` (the intended route —
the dangled citation is this promotion's own provenance field), bundle recoverable at
`e7c57737145fb763bd623580de3f4bb8bce7f860`. `calibration-complete.json` needed no re-key — SOCO has
never had an entry and none was invented. Matrix re-stamped: shard keeper + gates, §5.8 header, and
`gas_plant_monthly_pricing` **O → K**. **`2026-09-20-soco53g-prb-own-iso` was `--keep`-listed and NOT
swept up — it is still unruled, E13 still fires for it, and it needs its own ruling.**
**Gate limitation routed:** `audit_keepers` E5's `_DET_TOKENS` has no `PHYSICALLY-CALIBRATED` entry, so
a price-unscored ISO cannot state its determination in a sidecar definition at all — naming the live
verdict matches the bare `CALIBRATED` substring and naming the superseded one matches `NOT-YET`. The
definition is recipe-only, as the outgoing keeper's also was; extending `_DET_TOKENS` is the scoring
desk's.

## soco-55 — 2026-09-20

TWO results; the first is a DATA decision this desk owed and it outranked the lever.

(1) THE BENCH. check_bench_freshness was RED for SOCO ALONE repo-wide -- 44 parts
checked, 3 STALE (a hard ::error) against 41 warning-level engine drift on every
other ISO. Rebuilt at HEAD (zero LP, 37 s) and the incumbent keeper
2026-09-20-soco54-marginal-gas-basis re-scored on it: 2024 CC_REGULAR crosses
+7.417 -> +7.505 TWh against a +/-7.47 band, on a -0.088 TWh change in that row's
benchmark ACTUAL, so C1 reads 13/14 and SOCO'S PUBLISHED HEADLINE MOVES OFF ITS
CEILING TO NOT-YET. PRECOMMIT-soco-54 P4 pre-registered exactly that row at 81 %
of its margin. NO DISPATCH MOVED: every keeper hourly sidecar is byte-identical to
the day it was solved and its 297 KB run payload re-renders byte-identical -- only
the benchmark moved, and the ceiling reading had rested on a bench that could not
be reproduced from the builder at HEAD. check_bench_freshness now reads 0 STALE.
The keeper's per-plant layer, believed lost with the SOCO-54 shard branches, was
RECOVERED AT ZERO LP: the refs are gone but the objects are still on the remote,
and git fetch origin <40-char-sha> retrieved all three legs; composed, they
reproduce the committed keeper's twelve hourly sidecars BYTE-FOR-BYTE.

(2) THE LEVER. Run 2026-09-20-soco55-peryear-gas-basis (bundle
results/calibration/soco55_peryear_basis), a registered CANDIDATE the owner has NOT
ruled on; the keeper is unchanged and nothing was pruned. ONE delta:
gas_basis_differential_measured_by_year = true. GAS_BASIS_DIFFERENTIAL['SOCO'] =
0.64 is the 2024 value applied to every year and its own comment calls it a
"forward-year / fallback value only", but SOCO-54 promoted that fallback onto
SOCO's PRIMARY backcast gas path -- so 2023 carried +0.15 $/MMBtu (~+$1.65/MWh) on
every SOCO gas unit. SOCO-54 declared the imprecision against itself and ROUTED the
repair; this lane took it on the source-data citation (rule 23), re-deriving at HEAD
and reproducing SOCO-20's committed comment exactly: +0.4931 / +0.6395 / +0.6540,
registered at the 2dp every other GAS_BASIS_DIFFERENTIAL row carries -- a convention
fixed BEFORE the solve, whose declared consequence is that 2024 is byte-identical.

THE RESULT IS AGAINST THE LANE AND THE INPUT IS KEPT ANYWAY. The 2023 residual gets
LARGER: CT_PEAKER 10.668 -> 11.413 TWh (actual 4.503; share +2.56 -> +2.87pp of a
+/-3.00pp cap, headroom collapsing 0.44 -> 0.13pp), COAL_PRB 21.722 -> 20.443
(22.151), CC_REGULAR 112.126 -> 112.312 (107.960); only ST_GAS improves, 3.986 ->
4.293 (10.442). Every row still PASSES, C1 stays 13/14 with the SAME single failing
row, determination NOT-YET -- which PRECOMMIT-soco-55 P7 pre-registered verbatim.
Rule 14 [R-ACCURATE] is the governing text: a worse fit after an accurate input is a
DISCOVERED BUG, not a reason to revert to an estimate that was silently compensating.

WHAT IT LOCALIZES, the lane's real product: 95 % of the 1.279 TWh coal displacement
is ONE PLANT -- 6002 James H Miller Jr, 15.838 -> 14.626 against a 15.701 actual --
and about half the energy it sheds lands on merchant turbines already far above their
actuals (55409 Calhoun +0.115 vs 0.026; 55061 Tenaska Georgia +0.111 vs 0.238; 7709
Dahlberg +0.109 vs 0.243) while the other half lands correctly on 2049 Jack Watson
(+0.147 toward 3.270, partially repairing SOCO-54's routed miss) and 728 Yates
(+0.087 toward 2.239). THE NAMED SUCCESSOR IS THE CT_PEAKER / COAL_PRB MERIT ORDER,
NOT THE GAS BASIS.

GOVERNANCE. ZERO free parameters (n_residual unchanged at 1); ONE new default-off
ScenarioConfig gate, registered in _CACHE_KEY_OPTIONAL_FIELDS at "False" in the same
commit as the field so NO pre-existing cache key moves; declared in
solve_surface_declared at its live hash (SOCO 182 -> 183 rows, moved_rows {}); the
SCALAR machine-verified UNTOUCHED at 0.64, because this lane GATES it rather than
editing it. Rule 19 at two grains before the solve: the six GAS classes move on
fuel_prices AND mc_base, every other class at max |delta| EXACTLY 0.000000000000 in
all three years, and 2024 is 0.000000000000 at BOTH grains -- confirmed byte-identical
on all eight 2024 artifacts including dispatch/2024_P1.parquet and floors/2024_P1.npz.
Rule 25: the measured table carries a SOCO row AND NOTHING ELSE, machine-verified.
ALL FOURTEEN pre-registered predictions HELD; the declared #1 risk (2023 CT_PEAKER
crossing to FAIL) materialised SHORT of a flip and is reported at full magnitude.
C2/C4/C6/C8 PASS, C3a/b/c UNSCORABLE, 0 ledgered and 0 protective caveats, rule 17
holds in all fifteen plant-years, D-1 carries the same three COAL_BIT failures as the
keeper. Three shards, one year each (rule 36), pinned to 2a790121, 2.60-2.65 GiB peak
and 107-118 s each; all three ARCHIVED after fetch + checkout + verify.

REPORTED, NOT TAKEN: other ISOs DO carry constant-multiplier contract families.
Measured zero-LP with SOCO-54's own method (largest set of reporting plants whose
monthly delivered-price ratio series is flat at CV <= 0.001), 2023/2024/2025: SPP
6/63, 50/60, 50/54 -- on a keeper that ARMS gas_plant_monthly_fuel_pricing; ERCOT
9/20, 10/23, 26/26; SOCO 7/24, 8/25, 8/26; MISO 7/102, 7/98, 6/100; PJM 6/26, 6/25,
6/23; NWPP 3/28, 4/29, 3/26; NYISO and CAISO NONE in any year; NEISO void at 1
reporting plant. Rules 25 / 28(d): no other ISO's cell is filled and no verdict
transfers.

GATES. check_bench_freshness 0 STALE (cleared by this lane). check_mechanism_matrix
--base origin/main PASS, "1 new field(s) all registered". audit_keepers --iso SOCO:
E13 fires for the SEVENTH consecutive lane on 2026-09-20-soco53g-prb-own-iso, an
unruled candidate -- RE-RAISED, NOT CLEARED, and the owner is asked for a ruling;
E11 expected; S1 went stale on the bench rebuild and WAS repaired.
check_registry_payload_parity RED LOCALLY / GREEN IN CI on this session's own
gitignored bundles, all verified check-ignore-clean with 0 tracked files -- no result
deleted. check_cache_key_registration still RED at HEAD for PPA_COST_RECOVERY_YR and
REGIONAL_RENEWABLE_CF; this lane declared its OWN name only. tests/unit/config +
tests/regression/test_persisted_identity.py fail 11 at origin/main and 11 with this
change, measured both ways in a clean worktree: ZERO new failures.

PROMOTION IS OPEN AND IS THE OWNER'S (rule 31). Recommendation: PROMOTE, on rules 1
and 14 and explicitly NOT on the residual, which got worse. Cost from the current
state: ZERO re-solves. Record: docs/handoffs/PRECOMMIT-soco-55-2026-09-20.md,
docs/handoffs/FINDING-soco-55-2026-09-20.md.

## soco-55 PROMOTION — 2026-09-20

OWNER RULED, verbatim: "Is this a recommended keeper candidate? If so plz promote.
If structural integrity improves but gates regress that may still be a keeper."

SOCO's KEEPER IS NOW 2026-09-20-soco55-peryear-gas-basis (bundle
results/calibration/soco55_peryear_basis, 17 committed slim files). Rule 35
[R-PROMOTE] executed in the promoting session, in order: (b) the year union
{2023,2024,2025} enumerated over all three registered SOCO sidecars BEFORE any
delete; (c) the incoming keeper covers that union in ONE composed span, so the
promotion SHRINKS NOTHING; (e) the new designation written and audit_keepers
re-run -- resolving the incoming keeper's three stores -- BEFORE prune_iso_runs
touched anything; (a) the outgoing keeper 2026-09-20-soco54-marginal-gas-basis
then had its THREE STORES deleted together via prune_iso_runs.py --iso SOCO
--force-uncite (registry sidecar, runs/<id>.js, results/calibration/
soco54_marginal_gas), recoverable from git history at the SOCO-55 branch point.

2026-09-20-soco53g-prb-own-iso was DELIBERATELY NOT PRUNED (passed to --keep).
The ruling names the recommended candidate, which was this lane's; it does not
dispose of soco53g. Rule 31 [R-RETAIN] forbids deleting it and rule 30(a) forbids
stamping it, so audit_keepers E13 still fires ONCE -- down from twice -- and is
RE-RAISED, not cleared. The lane's recommendation stands: decline it, and let the
next promoting session prune it.

ON THE OWNER'S STANDARD, STATED PRECISELY BECAUSE THIS CASE IS NOT THE ONE IT
ANTICIPATES: the ruling contemplates structural gain paid for by a gate
regression. HERE THE GATES DO NOT MOVE AT ALL -- determination NOT-YET, C1 13/14,
C2/C4/C6/C8 PASS, C3a/b/c UNSCORABLE, 0 ledgered and 0 protective caveats,
grade_summary identical on both sides of the A/B -- and the single failing row is
2024 CC_REGULAR, in a year this keeper's delta is PROVABLY INERT in. What
regresses is the 2023 RESIDUAL (CT_PEAKER +6.165 -> +6.910 TWh against actual,
COAL_PRB -0.429 -> -1.708, CC_REGULAR +4.166 -> +4.352; only ST_GAS improves), and
rule 14 [R-ACCURATE] is why it is kept rather than reverted: a worse fit after an
ACCURATE input is a DISCOVERED BUG. The promotion buys STRUCTURE and a NAMED
SUCCESSOR OBJECT -- the CT_PEAKER / COAL_PRB merit order at 6002 James H Miller Jr
-- not a gate.

REBASED ONTO origin/main (27 upstream commits) BEFORE PROMOTING, and the numbers
re-verified across them: both runs re-score to their committed metrics.json
byte-for-byte, same determination, same single failing row. Two conflicts, both
mechanical -- 66 mechanism-matrix.js hunks differing ONLY in stale line-number
anchors (verified programmatically 66/66; this lane's new base row sat outside
every conflict region), and one additive tail collision in
_CACHE_KEY_OPTIONAL_FIELDS where SPP-66 and xiso-8 appended to the same HOUSE-3
slot, resolved by KEEPING BOTH SIDES.

CORRECTION FORCED BY THE REBASE, stated rather than left to be discovered: the
shards were solved at pinned SHA 2a7901215f5f8d78835cf3e314caffe06d8c656b, which
the rebase makes no longer an ancestor of this branch. The pin remains an accurate
record of what the shards cloned -- provenance, not a durability claim -- but a
reader should not expect to find it in the branch history. Nothing about the
solves changed.

RE-STAMPED IN THE PROMOTING SESSION (rule 28 [R-MECH-MATRIX]): the SOCO matrix
shard's keeper + gates line and the §5.8 prose header, both of which the matrix
gate turned RED on the promotion and both now GREEN. status/SOCO.js rebuilt
(SOCO:NOT-YET). calibration-complete.json carries NO SOCO entry -- confirmed, not
assumed -- so nothing to re-key there.

POST-PROMOTION GATES: check_mechanism_matrix --base origin/main GREEN including
keeper stamps and §5.x prose headers; check_bench_freshness 0 STALE;
audit_keepers holdout/marker/status all pass with the one expected E13 and the
expected E11. check_registry_payload_parity RED LOCALLY on eight of this session's
own gitignored working bundles (all verified check-ignore-clean, 0 tracked files)
plus results/calibration/nwpp44_takeorpay_2025 -- which is NWPP-44's, already on
origin/main at ee276d87, touched by none of this lane's commits, and REPORTED not
touched (rule 25 [R-ISO-SCOPE]).

DO NOT CITE PHYSICALLY-CALIBRATED (PRICE UNSCORED) FOR ANY SOCO RUN GOING FORWARD:
the bench that produced that reading was stale and was rebuilt this session.
Record: docs/handoffs/FINDING-soco-55-2026-09-20.md §12.

## soco-56 — 2026-09-20

THE HANDOFF'S LEAD LEVER IS REFUSED ON MEASUREMENT, EX ANTE. 2024 CC_REGULAR is
NOT marginal energy: 112.028 of 112.414 TWh -- 99.66 % -- is produced AT FULL
AVAILABILITY, 86.1 % of its unit-hours are at cap, and the whole class holds
5.268 TWh of idle headroom all year. In ZERO of 8,760 hours is the cheapest idle
COAL_PRB or ST_GAS unit cheaper than the marginal RUNNING CC (mean gaps +7.04 and
+8.15 $/MWh), and the fleet-median CC mc sits $7.00/MWh BELOW the clearing price.
Closing the 9.46 TWh the C1 rows ask for needs ~$5/MWh of merit-order movement
against 8.616 TWh of in-reach coal+steam headroom, while the same $5 band holds
20.594 TWh of CT_PEAKER headroom on a class already 1.9x its actual. Three more
levers refused ON SIGN and recorded so no successor spends a solve: the handoff's
own parasitic-load item, coal_takeorpay_from_data (makes coal MORE expensive) and
coal_fuel_inventory (a coal CEILING) -- all the wrong way for a COAL_PRB already
4.1 TWh short.

THE DEFECT FOUND INSTEAD IS A DATA DEFECT TRACED TO PRIMARY SOURCES.
data/raw/campd-unit-outages-SOCO.csv routes Barry (plant 3) units 1, 2 and 4 to
CC_REGULAR through the deriver's plant-level fac_group short-circuit. CAMPD files
all three as unitType "Tangentially-fired" -- BOILERS, never "Combined cycle" --
and EIA-860 files 1 and 2 as Natural Gas Steam Turbine, 4 as Conventional Steam
Coal. They are mostly idle (17.01 / 10.08 / 152.02 GWh in 519 / 303 / 1,539 h of
2024) and that idleness is charged as a 20.3 pp forced outage on Barry's
COMBINED-CYCLE block for 342 / 353 / 298 days of 366. THE CONSEQUENCE IS PHYSICAL:
the model's availability ceiling sits BELOW the plant's own measured CAMPD output
in 8,548 of 8,760 hours of 2024, by up to 1,513 MW and 5.080 TWh (2023: 5.031,
2025: 4.598); availability p50 1,028 MW against a measured output p50 of 1,624 MW;
full capacity reached in 144 hours where every peer CC reaches it in 1,800-2,160.
SAME DEFECT AS pjm-75 (Chesterfield) AND miso-200 (Ninemile Point), both already
adjudicated. It also resolves the standing "Barry unit 4 is a COAL model row CAMPD
files as Pipeline Natural Gas" item IN FAVOUR OF CAMPD -- the unit measurably
burns gas; EIA-860's BIT is stale.

THE LEVER -- campd_per_unit_attribution, cell U -> O. SOCO's own -perunit-
companion derived in-lane from SOCO's own CAMPD + EIA-860 (rules 25 / 28(d): NYISO's
verdict transfers to nothing). It re-routes 3 unit rows / 48 window rows of 1,119,
ALL at facility 3, machine-verified in gen_soco56_attestation._verify_extracts.
SCOPE, BECAUSE THE BASE ROW SAYS "ONE GATE OVER BOTH ARTIFACTS": ONLY THE OUTAGE
HALF FIRES -- thermal_tranche_csv_for_iso("SOCO", per_unit=True) returns the
INCUMBENT thermal_tranches_SOCO.csv, no -perunit- tranche companion existing, which
is exactly why rule 19 at three grains reads fuel_prices and mc_base at global
max |delta| EXACTLY 0.000000000000 in all three years while availability moves
exactly 2 of 128 (plant, group) keys, both plant 3. A SUCCESSOR THAT DERIVES THAT
TRANCHE COMPANION ARMS THE OTHER HALF SILENTLY UNDER THIS SAME FLAG.

THE RESULT IS AGAINST THE LANE AND THE INPUT IS KEPT ANYWAY. The gates DO NOT MOVE
-- NOT-YET, C1 13/14 all / 9/10 free, C2/C4/C6/C8 PASS, C3a/b/c UNSCORABLE, 0
ledgered and 0 protective, grade_summary identical on both sides -- and the single
failing row, 2024 CC_REGULAR, goes +7.505 -> +10.178 TWh of a +/-7.466 band and
+2.81 -> +3.88 pp of a +/-3.00 pp cap: it now fails BOTH legs where the keeper
failed one. PRECOMMIT-soco-56 P1 and P2 pre-registered exactly that from a zero-LP
greedy re-stack, with a +1.5 to +4.5 TWh band the measured +2.673 lands inside.
FIFTEEN OF FIFTEEN pre-registered predictions HELD. Rules 1 [R-STRUCT] and 14
[R-ACCURATE] govern: a model that cannot reproduce a 1.8 GW plant's measured output
in 97.6 % of a year is not modelling that plant, whatever the class total reads.

WHAT IT BUYS IS PHYSICS. Barry's CC availability 8.323 -> 13.352 TWh against a
measured 13.361 (0.07 %) in 2024 and 8.091 -> 12.606 against 12.566 (0.32 %) in
2025 -- and DELIBERATELY NOT in 2023, where unit 8's 345-day commissioning outage
is a genuine CC outage the crosswalk correctly leaves in place (4.471 vs 7.303).
That asymmetry is the mechanism's signature; a lever that repaired all three years
to their actuals would be a fit. 2025's VOLL slack falls 8,930.2 -> 7,907.2 MWh, and
the keeper's thinnest row -- 2023 CT_PEAKER at 0.13 pp of headroom -- gets 3.7x
safer (2.87 -> 2.52 pp).

COSTS, AT FULL MAGNITUDE. The three re-routed units (709.9 MW) land on Barry's
146.5 MW ST_GAS bin whose EIA-860 basis (306.2 MW) is smaller, so that bin's
availability clips to ~0.02 -- a NEW over-derate, bounded by measurement at
<= 0.0023 / 0.0000 / 0.0071 TWh (in merit 18 / 3 / 88 h of 8,760) and costing no
forced energy (plant 3's rule-17 share is 0.000 on both sides, margin 0.0632). The
correct repair is unit_outage_extract_basis_share or unit_outage_st_capacity_basis
and is ROUTED, NOT STACKED (rule 19). D-1 gains ONE failure -- 2024 COAL_PRB
cv_ratio 0.532 -> 0.463 of a 0.50 gate -- against six D-1 metrics that improve;
D-1 is REPORTED, not gated. Rule 17 holds in all fifteen plant-years; C8 ST_GAS
share 0.129 / 0.131 / 0.147 against the 0.30 cap. ZERO free parameters: DOF 6
entries / 1 residual, unchanged; the field was already in
_CACHE_KEY_OPTIONAL_FIELDS at "False" so no pre-existing key moves and
moved_rows("SOCO") == {}.

THE NAMED SUCCESSOR, AND AN INFERENCE THIS LANE TESTED AND REFUTED. Barry's
spurious derate was SILENTLY COMPENSATING for a real merchant-CC over-dispatch: the
2024 CC per-plant ratio spans 0.49x (Barry) to 2.45x (Tenaska Lindsay Hill), and
every plant above 1.35x runs at 0.97-1.00 of its model availability while its
measured CF is 0.22-0.59. THE OWNERSHIP READING DOES NOT HOLD -- on EIA-860 Utility
Name, Southern-affiliated CC is 79.602 vs 80.851 TWh (0.985x) against non-Southern
32.814 vs 29.397 (1.116x), but Southern-affiliated CT_PEAKER is 2.219x against
non-Southern 1.705x, i.e. the tilt runs the OTHER way in the class SOCO-55 read it
in. So the successor's object is PER-PLANT CC ALLOCATION -- heat rate, offer
surface, availability -- not a merchant/utility partition. It also matters for the
FORECAST: a forecast year carries NO CAMPD outage overlay, so the compensation is
not there and the backcast's flattering CC number is a backcast-only artifact.

KEEPER UNCHANGED at 2026-09-20-soco55-peryear-gas-basis; nothing pruned. The run
2026-09-20-soco56-perunit-outage is registered as a CANDIDATE and ITS PROMOTION IS
OPEN AND THE OWNER'S (rule 31 [R-RETAIN]); the lane's recommendation is TO PROMOTE,
on structure and not on the residual. A SECOND RULING IS ASKED FOR:
2026-09-20-soco53g-prb-own-iso has now fired audit_keepers E13 for the NINTH
consecutive lane; the standing recommendation is to DECLINE it so the next
promoting session may prune it. Records:
docs/handoffs/PRECOMMIT-soco-56-2026-09-20.md,
docs/handoffs/FINDING-soco-56-2026-09-20.md, scripts/gen_soco56_attestation.py,
scripts/probes/soco56_compose_span.py.

## soco-56 PROMOTION — 2026-09-20

OWNER RULED ("Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper").
SOCO'S KEEPER IS NOW 2026-09-20-soco56-perunit-outage. Unlike SOCO-55, whose coda
had to record that the ruling's second sentence did NOT describe its case, THIS
PROMOTION IS THE RULING'S HARDER LIMB EXACTLY: structure improves and a gate row
REGRESSES -- 2024 CC_REGULAR +7.505 -> +10.178 TWh of a +/-7.466 band and +2.81 ->
+3.88 pp of a +/-3.00 pp cap, failing BOTH legs where the outgoing keeper failed
one. PRECOMMIT-soco-56 P1/P2 pre-registered that before the solve.

Rule 35 [R-PROMOTE] executed IN ORDER: (b) the year union {2023, 2024, 2025} was
enumerated over ALL THREE SOCO sidecars BEFORE anything was deleted; (c) the
incoming keeper covers it in one composed span, so the promotion SHRINKS NOTHING;
(e) the designation was written, build_status rebuilt and audit_keepers re-run to
resolve the incoming keeper's three stores BEFORE prune_iso_runs touched anything;
(a) the outgoing keeper's three stores were then deleted together via
--force-uncite, which rule 35(d) names as the INTENDED route here. Its bundle is
recoverable from git history at this branch point.

2026-09-20-soco53g-prb-own-iso was deliberately NOT pruned (--keep). The ruling
names THE RECOMMENDED CANDIDATE, which is this lane's, and does not dispose of
soco53g; rule 31 forbids deleting it and rule 30(a) forbids stamping it, so E13
fires ONCE -- down from two -- and is RE-RAISED. The standing recommendation is to
DECLINE it so the next promoting session may prune it.

audit_keepers E11 (the silent-de-arm guard) flagged meta.composed_from moving
['soco55_arm_*'] -> ['soco56_arm_*']. NOT a de-arm and not solve-affecting: it is
the provenance list of the per-year shard bundles rule 36 [R-YEAR-ISOLATION] (a)
REQUIRES be re-solved per year, so it cannot carry across a promotion and renames
at every sharded keeper. Declared in promotion_note_soco56; E11 now passes. A
successor promoting a sharded keeper on ANY ISO will hit the same guard and owes
the same declaration.

G-DRIFT re-run against the refreshed origin/main: the only solve-path change since
this lane's pin is SPP-67's vre_reference_rate_year_own -- default False,
registered in _CACHE_KEY_OPTIONAL_FIELDS at "False" in the same commit, gating
SPP-only wind-curtailment code. INERT for SOCO on two grounds (another ISO's
branch; a default-off flag absent from the recipe), and SOCO dispatches 0.000 TWh
of wind in every year. Form 4 holds.

Post-promotion: check_mechanism_matrix GREEN with keeper stamps matching every
shard (SOCO shard keeper + gates and the §5.8 header re-stamped, cell
campd_per_unit_attribution O -> K); build_status --iso SOCO in sync;
audit_keepers holdout/marker/status all pass with the one expected E13.
calibration-complete.json carries NO SOCO entry, confirmed not assumed.
Record: docs/handoffs/FINDING-soco-56-2026-09-20.md §12.

## soco-hydro-4 — 2026-09-22

Hydro dispatch physics, two single-delta PROBE arms off keeper soco58_warm_committed, 7 year-isolated
shards (2025 on a SOCO-53b backfill repair control). Registered 2026-09-22-soco-h4-hydro-min
(hydro_min_flow_floor) and 2026-09-22-soco-h4-hydro-ror (hydro_ror_split); both NOT-YET on the keeper's
own C1 row, no status flip anywhere. G1/G2 pass every leg (annual hydro 0.0000 %). Zero-MW hours -> 0
under ARM 2 in all years; top-decile share closes 33-43 % of the gap to measured (ARM 1: 11-16 %).
Lane recommends ARM 2 on driver grounds; owner ruling open. Routed: 2025 model demand +10 % over
EIA-930 at peak (ARM 2's 2 scarcity hours); SOCO-53b owned by SOCO-59; stale PS-folded hydro actual in
committed bench parts; D-2 blind to hydro floors. Matrix cells hydro_min_flow_floor / hydro_ror_split
U -> O. Record: docs/handoffs/RESULT-soco-hydro-4-2026-09-22.md.

## soco-hydro-4 promotion — 2026-09-23

Owner ruling ("Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.") -> KEEPER 2026-09-22-soco-h4-hydro-ror
(hydro_ror_split + 2025 hydro_backfill_year=2024). Year union before prune: 2023-2025 (all four SOCO
sidecars); the incoming keeper covers it. audit_keepers E1 passed before the prune. Pruned via
prune_iso_runs.py --force-uncite: 2026-09-22-soco58-warm-committed (outgoing) and
2026-09-22-soco-h4-hydro-min (ARM 1, not promoted). 2026-09-20-soco53g-prb-own-iso deliberately kept
(--keep), as in every prior SOCO promotion: its disposal awaits an owner ruling, so E13 fires for it
alone. build_status --iso SOCO rebuilt; matrix shard re-stamped (hydro_ror_split O -> K).

## soco-61 — 2026-09-24

A 313 MW CC TURBINE THAT DID NOT RUN IN 2024 WAS MODELLED FULLY AVAILABLE.
Tenaska Lindsay Hill (55271) CT3 filed all 8,784 CAMPD hours of 2024 dark (0
operating hours; 642 / 308 GWh in 2023 / 2025). The per-unit outage deriver
skips a never-producing unit and the eia923_netzero hook is plant-grain, so the
keeper carried it fully available and the plant ran +1.73 TWh over EIA-923.

PHASE 0 MEASURED THE THREE ROUTED LEADS FIRST. The big over-dispatched CC
plants (E B Harris, H A Franklin, Central Alabama) run BELOW their measured
capability -- economic, not availability. Coal runs at 0.35-0.70 of its model
availability -- merit order, no availability lever. ST/CC fuel separation still
has no forward-regenerable input. Lindsay Hill was the only over-dispatched CC
plant whose model capability exceeded what it delivered.

THE REPAIR: new field campd_dark_unit_year_windows + deriver flag
--dark-unit-years (categorical, zero free parameters): one full-year window
when a unit's own id is dark every hour of the year, produced in an adjacent
year, and a peer ran. The -perunitdark- extract is the -perunit- extract
re-derived BYTE-IDENTICALLY plus one row.

RESULT (run 2026-09-24-soco61-dark-unit, PROMOTED, three year-isolated shards
composed at zero LP): 2023/2025 identical to the keeper; 2024 Lindsay Hill
3.485 -> 1.651 TWh (actual 1.752). No status moved: C1 14/14 / free 10/10,
C2/C4/C6/C8 PASS, C3 unscorable, grade 5/5/0, DOF 13/1. 2024 CC_REGULAR +4.43 ->
+3.14 TWh, share +2.7 -> +2.2 pp (margin 0.3 -> 0.8 pp); CC per-plant
sum|model-923| 11.07 -> 9.28 TWh; C4 2024 coal NRMSE 0.240 -> 0.235. WORSE:
2024 CT_PEAKER +1.73 -> +2.36 TWh. 12/12 predictions in band.

ROUTED: 2023 ST_GAS / CT_PEAKER are now the thinnest rows (0.7-0.8 pp); the CC
economic over-dispatch (E B Harris +2.0, H A Franklin +1.5) has no admissible
input. Outgoing keeper 2026-09-23-soco60-boundary-span pruned (rule 35). E13 for
2026-09-20-soco53g-prb-own-iso still unruled (recommendation: decline).
Records: docs/handoffs/PRECOMMIT-soco-61-2026-09-24.md,
docs/handoffs/FINDING-soco-61-2026-09-24.md, scripts/gen_soco61_attestation.py,
scripts/probes/soco61_compose_span.py, scripts/probes/_soco61_phase0.py.

## soco-62 — 2026-09-24

THE 2023 CT_PEAKER / ST_GAS SPLIT IS BOILER COMMITMENT, AND NO ADMISSIBLE INPUT
REACHES IT -- ZERO LP SPENT. Keeper 2026-09-24-soco61-dark-unit unchanged.

Phase 0 on the keeper's own per-plant legs (recovered at zero LP from the
SOCO-61 shard SHAs). 2023 CT+ST total is right (13.36 vs 13.62 TWh); the split
is wrong. At the four campaign-duty plants the ST deficit (4.68 / 4.32 TWh in
2023 / 2024) is 66 % / 79 % COMMITMENT HOURS (Watson 5,111 vs 8,451 synced h;
Yates 4,607 vs 7,739; Gaston 2,453 vs 4,888) -- but a floor at the registered
campaign level can add at most 0.61 / 0.82 TWh even at full measured sync. The
LP never finds a committed boiler economic above its floor: CTs at 34.4-35.3
$/MWh sit at or below boilers at 34.9-37.5, and the real separators (CT start
costs, boiler incremental HR) are closed by tranche_startup_amortization G and
the G5 identity bands. Lead 2: no SOCO start-cost input other than the G'd
object. Lead 3: nothing 2023-specific -- excess spread over ~15 CT plants, none
dark, zones never separate, nuclear matches; 2023 has 2,160 hours in the CT/ST
price band vs 676 in 2024 (Vogtle 4). Side leads closed: CT loaded vs
operating HR basis +1.13 % only; SOCO parasitic factors misaligned to a HR
conversion (16/24 rows out of band). No lever taken, no shard, no registration.

OWNER QUESTIONS: (1) may SOCO carry MEASURED incremental-HR phys_* bands while
price bands stay 1.0 (the only admissible route to the split)? (2) decline
2026-09-20-soco53g-prb-own-iso (E13)? Leftover refs for the owner:
claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-62-2026-09-24.md,
scripts/probes/_soco62_phase0.py.

## soco-63 — 2026-09-24

MEASURED INCREMENTAL-HR BANDS MOVE THE CT/ST SPLIT THE WRONG WAY -- PHASE 0
ONLY, ZERO LP. Owner G5 ruling blank, so no field, no solve, _SOCO_OFFER_CURVE
untouched. Keeper 2026-09-24-soco61-dark-unit unchanged.

Framing: phys_* keys are consumed only by gas_offer_net_revenue_margin (OFF in
SOCO), so "measured phys_* bands" are inert; a real arm must replace the
multiplier bands. CEMS IO-slope derivation at UNIT grain (committed per-unit
HR artifacts as class map; own-average normalization), cap-weighted p50:
CT_PEAKER marg 0.759/0.754 of average, ST_GAS 0.942/0.990, CC 1.007/1.185,
COAL 0.930/0.969; committed 1.078/1.080/1.032/1.043; CT coverage 91.7 %.
Non-selective form, greedy re-stack on the keeper legs (arm minus greedy
control): CT offer 34.00 -> 27.65 $/MWh below boilers 34.77; 2023 CT_PEAKER
+5.23 -> +18.48 TWh FAIL, 2023 ST_GAS -7.60 FAIL, 2024 CT_PEAKER +14.76 FAIL;
C4 2024 coal NRMSE 0.235 -> 0.290; per-plant CT error 8.68 -> 19.62 TWh. x0.5
and x2 same direction. Refused ST-only diagnostic reaches +0.44 of 5.50 TWh.
Rule 14 fails: in a start-cost-free LP the average HR is the only carrier of CT
no-load fuel; incremental HR is admissible only jointly with a CT start/no-load
carrier (tranche_startup_amortization, G).

OWNER QUESTIONS: (1) any new evidence to reopen tranche_startup_amortization
(G) for SOCO jointly with measured incremental-HR bands? (recommendation: do
not open G5 for incremental-HR bands alone) (2) decline
2026-09-20-soco53g-prb-own-iso (E13)? Leftover refs for the owner:
claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-63-2026-09-24.md,
scripts/probes/_soco63_phase0.py.

## soco-64 — 2026-09-24

MEASURED EVIDENCE FOR A CT START COST, AND WHY IT DOES NOT ANSWER THE G REASON
-- PHASE 0 ONLY, ZERO LP. Owner reopen ruling blank: no field, no solve,
_SOCO_OFFER_CURVE untouched. Keeper 2026-09-24-soco61-dark-unit unchanged.

(a) No-load heat input: derive_unit_bands' c0 sits at LSL, not P=0; evaluated
at P=0 the no-load share of full-load input (cap-wtd p50) is CT 0.17 quad /
0.22 linear (18/74 quad negative), ST 0.05, CC 0.28 quad vs 0.01 linear, coal
0.06 -- CT/CC are extrapolations from 60-100 % of HSL. (b) CEMS conduct: CT
56 starts/unit-yr, 9 h median runs, 58 % of CT energy in runs <12 h; ST 9 /
263 h, CC 19.5 / 105 h, coal 7 / 439 h. Model CT tranches run 8-10 h (matches);
ST econ tranches cycle ~10 h on a committed boiler. (c) Start cost chosen ex
ante = the NREL table already live (CT $20/MW); fuel-only measured $3.6/MW is a
lower bound. (d) Greedy restack on keeper legs: arm B (field's own scope, CT
econ/peak + CC peak) 2023 CT +5.23 -> +2.78, ST -5.50 -> -3.29 TWh (margins
1.83/1.66 pp), per-plant CT 8.68 -> 6.86, ST 5.35 -> 3.36; C4 flat/better;
x0.5/x2/v3 same direction. Non-selective arm A does not move ST (ST econ pays a
bigger amortized start than CT). Joint arm J (SOCO-63 bands + no-load) FAILS
2023 CT (+7.18, margin -0.01): CT joint band 0.98 = identity, CC carries the
extrapolated no-load. (e) KEEPER CENSUS: the same NREL markup is ALREADY LIVE
on 18 CT _committed (median $4.82, max $20/MWh) and 18 CC _committed tranches.
(f) (a)-(c) do NOT answer SOCO-53's G reason (a market-design category, not an
evidence gap). The census does bear on it: the keeper already runs the object;
either the G is wrong as stated or the keeper is inconsistent. Consistent-G arm
Z (strip committed markup): 2024 CC_REGULAR margin 0.81 -> 0.66.

OWNER QUESTIONS: (1) reopen tranche_startup_amortization for SOCO as a
cost-based start cost scoped by measured CEMS run length (arm B, NREL $20/MW,
no new scalar)? recommendation yes, on the cost re-characterization only; if
no, rule on arm Z for consistency. (2) decline 2026-09-20-soco53g-prb-own-iso
(E13)? Leftover refs for the owner: claude/soco61-arm-*, claude/soco60-arm-*,
claude/soco60-armB-*. Records: docs/handoffs/FINDING-soco-64-2026-09-24.md,
scripts/probes/_soco64_phase0.py.

## soco-65 — 2026-09-24

KEEPER START-MARKUP CENSUS ON ALL THREE YEARS -- NO/BLANK BRANCH, ZERO LP.
Owner reopen ruling blank: no field, no solve. Keeper
2026-09-24-soco61-dark-unit unchanged.

Census (solved P1 mc - fleet_only mc_base, minus the same-plant econ/peak
sibling; fleet rebuilt at the keeper's own sha 1d7edc1b because HEAD's
heat-rate-vintage drift moves mc_base; reproduces SOCO-64's 2023 CT median
$4.82 exactly). In EVERY year 2023/2024/2025: CT_PEAKER _committed 18/18
marked (median $4.82 / $9.23 / $6.67, max $20/MWh; $0.85/0.46/0.36 M in the
objective), CC_REGULAR _committed 18/18 (max $50; $10.2/14.0/23.1 M), plus
CT_CHP 3/3 and CC_CHP 3/3 _committed (chp_startup_covered off). Every
econ/peak tranche, all ST and all coal: exactly 0. The carrier is the core
P1 bid-cost compute_monthly_markup, not the tranche_startup_amortization
field (which only extends it to CT econ/peak + CC peak).

G reason (SOCO-53 §2.4, quoted) and the keeper are inconsistent in all three
years. OWNER QUESTION: (i) strip the _committed markup to honour G (SOCO-64
arm Z: 2024 CC_REGULAR margin 0.81 -> 0.66; 2023 CT/ST 0.73/0.66), or (ii)
amend G to "market PRICING use refused; cost-based start in the objective
admissible" (no change; arm-B reopen then separately authorizable)?
Recommendation (ii). (2) decline 2026-09-20-soco53g-prb-own-iso (E13)?
Leftover refs: claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-65-2026-09-24.md,
scripts/probes/_soco65_census.py.
## r-soco — 2026-09-24

SOCO RE-SOLVED ON THE CORRECTED BACKCAST INPUTS (audit AUDIT-backcast-inputs-860-heatrate-outage
§5.3.8, after F1 #6572 + F2 #6569). Keeper soco61 + year-matched EIA-860 (2023/2024 vintages, 2025
canonical), measured CHP heat rates, CAMPD short-coal / short-gas / partial outage families;
multipliers unchanged. Three year-isolated shards, composed at zero LP.

RESULT (run 2026-09-24-r-soco-corrected-inputs, PROMOTED 2026-09-25 on the owner's ruling "Yes promote"; soco61 + soco53g pruned per rule 35): determination
unchanged (PHYSICALLY-CALIBRATED, PRICE UNSCORED); C1 14/14 free 10/10, C2/C4/C6/C8 PASS, grade
5/5/0, DOF n_residual 1. Better: 2024 CC_REGULAR +2.19 -> +1.09 pp; CHP on EIA-923 every year.
Worse: 2024 CT_PEAKER +0.98 -> +1.85 pp (+2.17 TWh); 2025 unserved 267.4 -> 813.8 MWh; 2025 ST_GAS
forced share 18.3 -> 20.2 %.

2019-2022 NOT SOLVABLE: SOCO has no pre-2023 EIA-930 / FERC-714 / seam / gas-hub / solar-shape /
renewable-capacity inputs (addition plan manifest row 9 never landed) - routed as an intake lane.
Residual class-table CTs Dahlberg 7709 / Hartwell 54538 (1,045 MW) are an EPA<->EIA facility-id
crosswalk defect (CAMD 7765 / 70454) - routed. Records: docs/handoffs/r-soco/.

## Y-31 — 2026-09-25 — owner ruling R-BB: `2026-09-20-soco53g-prb-own-iso` DECLINED

**Ruling** (director board v43, 2026-09-25, card Y-29 §2): *decline + prune*
`2026-09-20-soco53g-prb-own-iso` — rule 31 `[R-RETAIN]` trigger (i), the owner has ruled. This
closes the SECOND RULING SOCO-56 asked for and every SOCO promotion since SOCO-54 carried forward
with `--keep`.

- **The prune was already done.** The R-SOCO promotion (commit `adf4498a`, 2026-09-25) pruned
  soco53g together with soco61 under rule 35. `prune_iso_runs.py --iso SOCO --dry-run` in this
  lane shows one registered SOCO run, the keeper `2026-09-24-r-soco-corrected-inputs`, and
  nothing to prune. No file was deleted by this lane.
- **E13:** `audit_keepers --check` PASS, 0 failures. SOCO E13 is clean. The one SOCO warning is
  the E11 lineage note: soco61's bundle has already been retention-pruned.
- The ruling makes the decline explicit on the record. Git history holds the pruned run.

## r-soco-b2 — 2026-09-25

SOCO BA BOUNDARY SETTLED AND 2019-2025 SOLVED. FINDING: the former Gulf Power plants AND load sat inside
SOCO's EIA-930 BA until hour-ending UTC 2022-07-13 12:00 (FERC-714 residual -1,700 MW step; Gulf Power
185's last filed hour; hourly CEMS fit b_gulf 0.83-0.89 -> 0.014). Owner ruling (C) "dated exit", hour
grain: constants.ISO_BA_EXITS dates R-SOCO-B's R2 (fleet hour mask from row 4637 of 2022; benchmark July
2022 by CAMPD in-BA share; vintage_2022 +2 Santa Rosa rows via --admit-plant). Only SOCO's key moves.

Seven year-isolated shards at 422915ca, composed at zero LP. E2 exact (2024/2025 = old keeper 0.0000
TWh; 2023 = R-SOCO-B leg 0.0000). B1 930/923 fossil 0.982/0.991/0.982/0.985/1.002/0.981 (2019-2024),
B2 passes every year.

RESULT (run 2026-09-25-r-soco-b2-boundary, PROMOTED 2026-09-25 on the owner's standing ruling;
2026-09-24-r-soco-corrected-inputs pruned per rule 35): C1/C2/C4/C8 PASS 2019-2022 + 2024, C6 PASS,
C3 UNSCORABLE; lone miss 2023 C1 CT_PEAKER +7.22 TWh / +3.0pp (tol 7.26 / 3pp) -> NOT-YET (was
PHYSICALLY-CALIBRATED). Promoted on structure (rules 1/14). Unserved 0 in 2019-2024, 813.8 MWh 2025
(inherited). Next lever: 2023 CT_PEAKER over-dispatch. Records: docs/handoffs/r-soco/{FINDING,PRECOMMIT,
RESULT}-r-soco-b2-*.md. Leftover refs for the owner: claude/rsocob2-2019..2025, claude/rsocob-2021,
claude/r-soco-b-hold (superseded, never lands), claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.

## soco-67 — 2026-09-25

2023 CT_PEAKER OVER-DISPATCH ATTRIBUTED AND PARTLY CLOSED; PROMOTED. G-DRIFT (measured, zero LP): every LP input
bit-identical at HEAD vs keeper sha 422915ca in all seven years (corrected in RESULT §4: the COAL-SUB relabel is
live for 2019/2020 class REPORTING, not dispatch). Attribution: the +7.2 TWh 2023 CT excess sits at five GA/AL IPP
CTs (Tenaska GA, Calhoun, Walton, Baconton, Washington Co.) cycled daily by the model; CC_REGULAR is at its
availability ceiling in 6,922 h and every CT hour; measured CC output exceeds model CC availability 4.0 TWh (class) /
9.1 TWh (plant). One ceiling is a rule-19 double count: Barry unit 8 (747 MW, absent from CAMPD before 2023-10-01,
first output 2023-12-12) carried a 2023-01-01..12-12 outage window while the COD ramp already held its A3 block
(COD 2023-11) offline. New gated field unit_outage_precod_clip (zero free parameters) clips such a window to its
bin's EIA-860 COD month.

RESULT (run 2026-09-25-soco67-precod-clip, seven year-isolated shards at b2397ae0, PROMOTED on the owner's standing
ruling; 2026-09-25-r-soco-b2-boundary pruned per rule 35): Barry CC 2023 availability 4.38 -> 7.20 TWh (solved
7.15; 923 net 7.34); 2023 CC +2.14, CT -1.27, COAL_PRB -0.51, ST_GAS -0.30 TWh; other years dispatch-identical.
2023 C1 CT_PEAKER +7.22/+3.0pp FAIL -> +5.95/+2.5pp PASS; C1-C8 all PASS (C3 unscorable) -> PHYSICALLY-CALIBRATED
(PRICE UNSCORED). Next lever: CC capability basis (6.76 / 7.67 TWh residual 2023/2024). Records:
docs/handoffs/r-soco/{FINDING,PRECOMMIT,RESULT}-soco-67-2026-09-25.md. Leftover refs for the owner:
claude/soco67-2019..2025.

## soco-68 — 2026-09-25

CC CAPABILITY LEAD RE-ATTRIBUTED; SUMMER-DERATE DOUBLE COUNT REPAIRED; PROMOTED ON STRUCTURE. G-DRIFT (measured, zero LP,
labels now hashed): every LP input bit-identical at HEAD vs keeper sha b2397ae0 in all seven years. Decomposition: of the
5.7-9.0 TWh/yr plant-grain CC excess only 0.2-0.6 TWh is CEMS above LP pmax (the routed "capability basis"); ~90% is
CEMS inside pmax but above derated availability, and its largest parameter-free part is the flat Jun-Sep
SUMMER_CLASS_DERATE (CC 10%, CT 12.5%) re-applied on a pmax that is already the EIA-860 net-summer rating (CT 93-100%,
CC 62-76% of capacity) - the miso-141 double count. Armed the existing registered field summer_derate_basis_aware
(zero free parameters): only summer availability moves on 167-172 units.

RESULT (run 2026-09-25-soco68-summer-basis, seven year-isolated shards at 34f3d4aa, PROMOTED on the owner's standing
ruling; 2026-09-25-soco67-precod-clip pruned per rule 35): CC_REGULAR +1.48..+2.50, CT_PEAKER -0.55..-1.38, ST_GAS
-0.34..-0.72, coal -0.07..-0.62 TWh/yr; 2025 unserved 813.8 -> 0 MWh. 2023 C1 CT_PEAKER +5.95/+2.5pp -> +4.60/+1.9pp;
2024 +4.52/+1.8pp -> +3.15/+1.3pp. ONE REGRESSION: 2019 ST_GAS -7.28/-2.8pp PASS -> -7.94/-3.1pp FAIL -> NOT-YET
(C2/C4/C6/C8 PASS, C3 unscorable). Next lever: ST_GAS under-dispatch (commitment hours, soco-62 §3). Records:
docs/handoffs/r-soco/{FINDING,PRECOMMIT,RESULT}-soco-68-2026-09-25.md. Leftover refs for the owner:
claude/soco68-2019..2025.

## soco-69 — 2026-09-26

ST_GAS DEFICIT DECOMPOSED; UNMEASURED COAL MUST-RUN SLAB WITHDRAWN; PROMOTED ON STRUCTURE, GATES REGRESS. G-DRIFT
(measured, zero LP): every LP input bit-identical vs keeper sha 34f3d4aa; solve-SHA diff (one default-off miso-273
field) INERT. Decomposition (per plant, exact hour partition vs CEMS): the ST_GAS deficit (7.6/5.6/6.6/5.7/5.5/4.9/5.2
TWh 2019-2025) is MERIT ORDER - available boilers $1-10+/MWh above the clearing price, synced boilers only at their
committed tranche - not availability (0.08-0.36 TWh/yr). Displacer: coal 2019-2022 (+4.4..+9.5 TWh), CT 2023-2024
(start-cost channel, G). The coal excess sat on the default 45% / $4.50 must-run slab at every coal plant absent from
thermal_tranches_SOCO.csv (all but Bowen/Miller/Scherer), 3.99/7.34/4.72/0.23/0.67/1.09/0.93 TWh of it binding while
the plant's own CEMS was offline (Wansley 6.28 TWh/yr vs 1.82/0.14/1.11 actual). Armed the existing registered field
coal_mustrun_requires_measured_row (zero free parameters; PJM/NEISO K, SOCO U -> K).

RESULT (run 2026-09-26-soco69-coal-mustrun-measured, seven year-isolated shards at ccaa94e0, PROMOTED on the owner's
standing ruling; 2026-09-25-soco68-summer-basis pruned per rule 35): COAL_BIT -1.1..-12.3, CC_REGULAR +0.9..+5.5,
CT_PEAKER +0.3..+5.3, ST_GAS +0.07..+1.48 TWh/yr; unserved 0 every year; removed set == census. 2019 ST_GAS -3.09pp
FAIL -> -2.49pp PASS. REGRESSIONS: 2019 COAL_BIT +0.81 -> -3.83pp FAIL (the unmeasured BIT plants' $37-50 econ cost,
masked by the slab); C4 coal NRMSE 2020 0.230 -> 0.347, 2023 0.216 -> 0.316 FAIL. Grade 5/4/1 -> 5/3/2, NOT-YET.
Next lever: measured coal rows (commitment) for Barry/Gaston/Crist/Wansley/Daniel; CT start-cost owner question
re-raised. Records: docs/handoffs/r-soco/{FINDING,PRECOMMIT}-soco-69-2026-09-25.md, RESULT-soco-69-2026-09-26.md.
Leftover refs for the owner: claude/soco69-2019..2025, claude/soco68-2019..2025.

## soco-70 — 2026-09-26

MEASURED COAL ROWS FOR THE FIVE UNCOVERED PLANTS; PROMOTED; GATES IMPROVE. G-DRIFT (measured, zero LP): every LP input
bit-identical vs keeper sha ccaa94e0 at 7df4a1f3 and at the rebased head (data drift on main since: other-ISO or
default-off, INERT). Census: thermal_tranches_SOCO.csv (derived --years 2024, facility attribution) carried COAL rows only
for Bowen/Miller/Scherer - Barry/Gaston/Daniel's coal output went to their CC/ST_GAS row, Crist/Wansley stopped coal before
2024; after soco-69 they ran 2.16 vs 13.50 TWh EIA-923 (2019). Repair (data only, zero free parameters, rule 23 source
change = span now 2019-2025): derive_thermal_tranches.py --coal-unit-coverage appends one COAL row per uncovered plant from
its own CEMS coal units (incumbent statistics; 60 prior rows byte-identical; sha 7b7f5f27 -> ab5ec265). Must-run 48.0%
Gaston / 34.9% Daniel, 0% Barry/Crist/Wansley. The per-unit tranche companion was deliberately NOT derived (gas-only
crosswalk; SOCO-56 note).

RESULT (run 2026-09-26-soco70-coal-rows-measured, seven year-isolated shards at e3cea99b, PROMOTED on the owner's standing
ruling; 2026-09-26-soco69-coal-mustrun-measured pruned per rule 35): every other unit's hourly cap_mw byte-identical;
measured-plant must-run identical; unserved 0. Gaston +0.85..+1.75, Daniel +0.08..+1.67 TWh/yr; COAL_BIT +0.61..+1.31,
CT_PEAKER -1.32..+0.18, ST_GAS -0.38..+0.03. C4 coal NRMSE 2020 0.347 -> 0.285, 2023 0.316 -> 0.268 FAIL -> PASS; 2019
COAL_BIT -3.83 -> -3.4pp still FAIL (Barry/Crist/Wansley cycle, must-run 0, their committed band keeps the coal start
markup); D-2 FAIL -> PASS. Grade 5/3/2 -> 5/4/1, NOT-YET. Records:
docs/handoffs/r-soco/{PRECOMMIT,RESULT}-soco-70-2026-09-26.md. Leftover refs for the owner: claude/soco70-2019..2025.

## soco-71 — 2026-09-26

COAL HEAT-RATE ARTIFACT RE-DERIVED OVER ITS DECLARED WINDOW; PROMOTED; FAILING ROW IMPROVES. G-DRIFT (measured, zero LP):
every LP input bit-identical vs keeper sha e3cea99b; code/data drift on main INERT (default-off fields, other ISOs'
artifacts). Decomposition of 2019 COAL_BIT (Barry/Crist/Wansley): not availability, not the start markup (stripping it
entirely caps at ~+0.4 TWh) — the cyclers' base offer is above the 2019 price in 78-97% of their CEMS-synced hours. Fuel
matches own-plant F923 receipts (<3%). Heat rate did NOT: campd_coal_heat_rates_SOCO.csv never read AL/FL/GA 2019-2022
CAMPD (pooled rows = 2023-2025 sums) and its latest-record union dropped Crist 641 (neiso-118 defect; now
union_fleet(klass=COAL)). Re-derived, unchanged estimator, all 30 committed rows byte-identical (sha 369a58ba -> a5579637),
zero scalars; Wansley 2019 12.75 -> 10.92, Crist 11.24 -> 10.55, Bowen 10.24 -> 10.67.

RESULT (run 2026-09-26-soco71-coal-hr-window, seven year-isolated shards at ae5fb43a; 2020/2024 re-solved on the pinned
dependency set after their first shards installed highspy 1.15.1; PROMOTED on the owner's standing ruling;
2026-09-26-soco70-coal-rows-measured pruned per rule 35): COAL_BIT +0.87/+1.52/+2.00/-0.19 TWh 2019-2022; 2023-2025
byte-identical; unserved 0. 2019 COAL_BIT -3.45 -> -3.09pp (-8.43 TWh vs +/-7.64) still FAIL, the only failing row; C4 PASS
every year; D-1 2020 COAL_BIT r 0.284 -> 0.779. Grade 5/4/1, NOT-YET. Records:
docs/handoffs/r-soco/{PRECOMMIT,RESULT}-soco-71-2026-09-26.md. Leftover refs: claude/soco71-2019..2025,
claude/soco71b-2020, claude/soco71b-2024, claude/soco70-2019..2025.

## soco-72 — 2026-09-26

GAS BASIS EXTENDED OVER THE KEEPER'S WINDOW; PROMOTED ON STRUCTURE; GATES REGRESS. G-DRIFT (measured, zero LP): every LP
input bit-identical vs keeper sha ae5fb43a; code drift on main = two default-off fields (SPP-86, R-ERCOT-7) INERT; no
data/ change. 2019 price-side decomposition (zero LP, soco-71 legs): in the cyclers' CEMS-synced/model-off hours the
marginal gas units were offered +$0.27/MMBtu ABOVE their own F923 receipts; no import node (demand = EIA-930 net
generation), so imports cannot displace coal. The defect: GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] held only
SOCO-55's 2023-2025 rows, so 2019-2022 fell through to the 2024 scalar 0.64. SOCO-55's construction, unchanged
(reproduces 2023-2025 byte-for-byte): 0.27 / 0.32 / 0.30 / 1.20; zero fitted parameters. Pre-registered to deepen the
failing row.

RESULT (run 2026-09-26-soco72-gas-basis-window, seven year-isolated shards at 19159a0c; PROMOTED on the owner's standing
ruling, PRECOMMIT §7 held; 2026-09-26-soco71-coal-hr-window pruned per rule 35): 678 gas econ/peak tranche-years at the
census mc +/-$0.01; 2023-2025 byte-identical; unserved 0. COAL_BIT -2.83/-1.65/-2.56/+0.56, COAL_PRB -4.78/-1.26/-0.85/+0.04,
CT_PEAKER +4.73/+1.91/+0.40/-0.24 TWh 2019-2022 (LP ~3x the greedy). 2019 COAL_BIT -3.09 -> -4.24pp (-11.26 TWh) still
FAIL; NEW C4 FAIL 2020 coal NRMSE 0.276 -> 0.304; D-1 FAILs 3 -> 4. Grade 5/4/1 -> 5/3/2, NOT-YET. Conclusion: 2019
COAL_BIT is coal COMMITMENT (the cyclers ran multi-day campaigns through hours priced below their own cost), not an
input error. Records: docs/handoffs/r-soco/{PRECOMMIT,RESULT}-soco-72-2026-09-26.md. Leftover refs: claude/soco72-2019..2025,
claude/soco71-2019..2025, claude/soco71b-2020, claude/soco71b-2024, claude/soco70-2019..2025.
