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
