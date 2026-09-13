# SOCO calibration log

Per-region continuation of `docs/calibration-log.md` (frozen archive) for the **SOCO balancing
authority** — Southern Company (Alabama Power, Georgia Power, Mississippi Power, Southern Power),
NERC SERC, **not an RTO/ISO**. Program: `docs/multi-iso/soco-addition-plan-2026-09.md`; desk ledger
`docs/handoffs/soco-desk-ledger-2026-09.md`.

Entries are appended **verbatim** by the SOCO ADDITION DESK from each lane's FINDING `## Log entry`
section (plan §8.0 rule 1 — a lane never writes this file). Newest last.

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
