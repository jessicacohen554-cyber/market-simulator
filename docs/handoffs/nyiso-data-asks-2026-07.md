# NYISO data asks — 2026-07 (Wave-3 lane L-11)

**Filed:** 2026-07-06, lane L-11 (gap register §5 Wave 3), first work item per the
register's own instruction: "File the LI/NYC delivered-gas + Iroquois Z2 data asks
immediately (longest external lead time)."
**Scope:** the three external data acquisitions that gate NYISO calibration-complete —
G-13 (keeper stale-vs-HEAD until the CT offer level is grounded in delivered fuel),
issue #1344 (endogenous downstate scarcity formation, data-blocked on a
condition-varying reserve requirement), and the register's Iroquois Zone-2 ask —
plus two smaller secondary asks recorded by the 2026-07-04 winter-spread session.
**Years:** 2023–2025 ONLY. Rule 22 quarantine: **do not** acquire 2022 or any 2026
data (H1-2026 is a designated holdout; its intake happens only as step 1 of the
one-shot validation after NYISO's calibration-complete marker exists). If a vendor
bundles full-history files, strip holdout years at the drop zone before commit.
*(Amended 2026-07-10: the owner explicitly authorized full **2018–H1-2026**
acquisition for these asks, overriding the H1-2026 deferral above —
intake-only, no LP, no scoring; session-logged and itemized in
`docs/out-of-sample-results-2026-07.md` §1.2. The quarantine on solving/scoring
out-of-training years is unchanged.)*

Admissibility: every series below is a measured physical/market **input** (delivered
fuel price, published requirement, scheduled pipeline flow, interface rating) that
would regenerate for a forward year from forward drivers — rule-13-admissible. None
is a market *outcome* to be pinned (rule 13's forbidden half); the measured reserve
**prices** we already hold stay validation-side only.

---

> **FULFILLED 2026-07-07 (via free web sourcing, not the paywalled asks below).**
> The blocking half of Ask A — a grounded downstate interruptible delivered-gas
> curve — was obtained free from the National Grid tariff archive. The peakers are
> **non-firm transportation** customers (KEDLI PSC No. 1 SC-7→SC-19; KEDNY SC-22),
> so their delivered fuel = the Transco Z6 NY daily commodity (already in the
> model) **+ the LDC non-firm transportation delivery rate**, which both LDCs
> publish monthly in their *Statement of Non-Firm Demand Response Sales and
> Transportation Rates* (`statnfdr` PDFs). Intaken as
> `data/raw/gas-prices/nyiso_downstate_ldc_transport_monthly.csv`
> (`scripts/data/fetch_nyiso_downstate_ldc_transport.py`) and wired per-zone through
> the `nyiso-downstate-gas` datatype v2 (KEDNY SC-22 → NYC, KEDLI SC-19 → Long
> Island). This is the *correct rate class* the ask below was reaching for, and
> supersedes the statewide-N3050NY3 stand-in. It resolves the G-13 offer-grounding
> block. The remaining sub-asks (A1–A5, esp. daily kero/ULSD frames A4 and the
> restricted per-plant A5) stay open only as optional sharpening — the transport
> delivery rate is inherently monthly/rate-case, so monthly is its native cadence.
> What could NOT be free-sourced: Con Edison 2023–24 GCF (purged from coned.com)
> and any paywalled Platts/NGI daily citygate — neither is needed for the
> transport construction.

## Ask A — LI/NYC LDC citygate / interruptible delivered-gas prices (G-13; priority 1)

**Why.** Commit `0c6c833` de-leaked the ERCOT-fitted CT/CC offer bands to neutral 1.0,
leaving the documented open root cause "a NYISO-grounded CT econ ramp." The
2026-07-04 log entry records: LI/NYC peakers over-run ~2.5× actual (CT 4.9 vs 2.13 TWh
in 2024) and "every NYISO solve is blocked until the CT offer level is grounded."
The residual over-runners are the LM6000 fleets (Bayonne, Equus, Edgewood,
Glenwood Landing) currently priced at the Transco Z6 NY *pipeline hub* — but these
non-firm peakers buy interruptible gas at the **LDC city gate**, a materially higher
delivered index.

**What we already have (the stand-in to be superseded).**
`data/raw/gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv`
(`scripts/data/fetch_nyiso_downstate_gas_basis.py`): EIA N3050NY3 **statewide-NY** monthly
citygate minus Transco Z6 NY, floored at 0. It is measured and admissible but
(a) statewide — one number blends upstate LDCs with the Con Ed / National Grid
downstate systems the peakers actually sit on; (b) monthly — misses the cold-snap
daily blowouts that set winter offers; (c) an average of firm+interruptible sales —
not the interruptible rate class the peakers face. PR #1442's `nyiso 52
floor-rederive-ctgas` probe used it and got CT_PEAKER volume near-exact; the ask is
what replaces it with the *right boundary*.

**Exact series requested (2023-01 through 2025-12):**

| # | Series | Source | Granularity |
|---|---|---|---|
| A1 | Con Edison (NYC, Zone J) delivered gas cost to interruptible/temperature-controlled electric-generation customers — the SC-9/SC-13 (or successor) rate-class delivered $/therm, incl. monthly gas adjustment clause factors | Con Edison gas tariff leaves + monthly GAC/MRA statements, NY PSC filings | monthly (daily GAC if published) |
| A2 | National Grid KEDNY (NYC) and KEDLI (Long Island, Zone K) equivalent interruptible electric-generation delivered rates | National Grid tariff leaves + monthly cost-of-gas statements, NY PSC | monthly |
| A3 | NYC/LI-resolution citygate price (if a sub-state split exists) to replace statewide N3050NY3 | EIA NG price file footnote query, or S&P Platts "New York city-gates" daily index | daily preferred, monthly acceptable |
| A4 | Kerosene/ULSD frames for the dual-fuel LM6000s: NY Harbor ULSD spot (have basis access via EIA) **plus** the actual winter-2023/24/25 delivered kero premium reported for NYC peakers if any SOM/DPS filing carries it | EIA PET series (free) + NYISO SOM fuel-cost appendix | daily/monthly |
| A5 | Any per-plant delivered-fuel-cost rows for Bayonne / Equus / Edgewood / Glenwood Landing that exist in restricted EIA-923 Schedule 2 (these merchants are non-reporters in the public file — confirm or refute) | EIA-923 restricted schedule request | monthly |

**What it unblocks.** G-13 (the top NYISO row of the register): a grounded downstate
CT delivered-fuel curve → the CT offer level stops being the open root cause → the
stale-vs-HEAD keeper can be re-solved and a legitimate keeper candidate exists.
Consumed at the `fuel.py` delivered-price seam exactly like the F923/citygate series
(forward story: LDC tariffs + hub forwards regenerate the premium; it responds to
tight winters). Also retires the summer-premium approximation flagged in the
fetch-script docstring.

> **PARTIALLY FULFILLED 2026-07-08 → 2026-07-10 (free web sourcing; B1 confirmed
> request-only).** Findings and landings, in the ask's own structure:
>
> - **B1 (continuous as-enforced series): confirmed NOT freely published.** No
>   MIS/OASIS posting carries the requirement as scheduled into RTD/RTC
>   (dataset-by-dataset probe of `mis.nyiso.com/public` 2026-07-10), and the
>   Dynamic Reserves project — which will post condition-varying requirements —
>   is a forward market design, not deployed for the backcast window. B1 stays
>   open **only** as the formal NYISO Market Operations data request.
> - **B2 (event-log reconstruction): FULFILLED, wider than asked.** The MIS
>   public message logs (P-35 Real-Time Events, P-25 Operational Announcements)
>   are intaken 2018-01–2026-06 (owner-authorized expanded window, see
>   `docs/out-of-sample-results-2026-07.md` §1.2) as
>   `data/raw/NYISO-AS/requirements/{realtime-events,oper-messages}/`
>   (`scripts/data/fetch_nyiso_operating_events.py`) and parsed into the
>   `nyiso-operating-events` clean datatype: 444 Thunderstorm-Alert
>   transitions, 1,100 reserve pick-ups, 4,170 out-of-merit reliability
>   commitments (incl. explicit "FOR TSA" commits), 28 emergency
>   transactions, system-state changes.
> - **B3 (published requirement schedule): FULFILLED — and it rewrites the ask's
>   premise.** The dated "Locational Reserve Requirements" postings
>   (Wayback-bounded v2020/v2021/v2026, PDFs + hand transcription →
>   `nyiso-reserve-requirements` datatype) show the SENY 30-minute requirement
>   is an explicit **hourly step schedule** since v2021 (in force all of
>   2023–2025): 1,300 HB0–5 / 1,550 HB6 / **1,800 HB7–21** / 1,550 HB22 /
>   1,300 HB23 — so the static 1,300 MW the RCPF overlay enforces is the
>   overnight floor, **500 MW low in every peak hour** before any
>   condition-varying increment. During TSAs the NYC 10T/30T and SENY 30T
>   requirements drop to **zero** (v2021+) — the TSA scarcity channel is
>   out-of-merit NYC commitment (visible in the B2 OOM log), not a
>   requirement step-up as this ask assumed. LI carries its own published
>   products (120 MW 10T; 270/540 MW 30T off/on-peak). NYC rose to 625/1,250
>   only in 2026 (between 2026-02-14 and 2026-07-10 — after the training
>   years). Closes the `TODO(SENY-MW)` line (see the 2026-07-10 addendum in
>   `docs/nyiso-rcpf-overlay.md`).
> - **B4 (DAM requirements): not separately posted either; folded into the B1
>   data request.**
>
> Net: the in-LP hourly-requirement channel can now be driven by measured
> data — deterministic published shape (B3) + TSA/event windows (B2) — with
> only the residual condition-varying component (largest-contingency changes,
> forecast-uncertainty adders) waiting on the B1 request.
>
> **ADDENDUM 2026-07-10 (same session): the B2+B3 reconstruction is BUILT and
> committed.** `scripts/data/derive_nyiso_reserve_requirements_hourly.py` derives
> `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{2023,2024,2025}.csv`
> — the exact loader contract of `data/nyiso_reserve_requirements.py`
> (`nyiso_dynamic_reserve_requirements`) — as published LRR base (SENY hourly
> steps) × (1 − TSA-window hour fraction) for the TSA-zeroed rows; 7 in-LP
> families per year (NYCA 3, East 10T, SENY 30T, NYC 10T/30T; LI logged as
> dropped — no in-LP family). TSA windows from the B2 logs with two documented
> repairs (explicit ends always trusted — genuine overnight TSAs lack the
> start-of-day ACTIVE attestation; missing-end starts close at their first
> unattested midnight). Sanity: SENY peak-hour mean ≈ 1,750–1,775 MW vs the
> 1,300 MW static overlay; TSA zeroing touches 185/227/120 h in 2023/24/25.
> Loader-verified end-to-end (no LP solve — rule-22 session constraint). The
> derived series remains a lower bound on the as-enforced requirement in
> non-TSA hours until the B1 request lands. Next session: flip
> `nyiso_dynamic_reserve_requirements` on, re-solve 2023–2025, keeper-candidate.

## Ask B — condition-varying downstate reserve-requirement series (#1344; priority 1)

**Why.** The #1344 blocker, verbatim from the downstate-reserve handoff: the model's
static published requirements (NYCA 2,620/1,310/655; East 1,200; SENY ~1,100; NYC
1,000/500 MW) never bind — NYC holds 2–3× the requirement even in the hours reality
prices at >$300 — and both the online-proxy (path A) and commitment-gated (path B)
mechanisms were empirically refuted **at the measured static requirement**. The
missing measured input is the requirement NYISO actually enforces in real time,
which *rises with conditions* (thunderstorm alerts, forecast uncertainty, gas
contingencies, largest-source changes). We hold the measured reserve **prices**
(`data/raw/NYISO-AS/`, 2023–25 RT+DA, all 11 zones) — those stay the validation
target and must never become an input.

**Exact series requested (2023–2025):**

| # | Series | Source | Granularity |
|---|---|---|---|
| B1 | Effective (as-enforced) locational operating-reserve requirements by product × region — 10-min spin / 10-min total / 30-min total × NYCA / East / SENY / NYC (and LI if separately enforced) — as scheduled into RTD/RTC | NYISO Market Operations data request; check first whether the OASIS/EBB "reserve requirements" posting archive or the Dynamic Reserves project's published historical dataset covers 2023–25 | 5-min or hourly |
| B2 | Failing B1 as a continuous series: the event log to reconstruct it — (i) Thunderstorm Alert declarations (start/end timestamp, the NYC 10-min non-sync / 30-min requirement step applied), (ii) loss-of-gas-supply and major-emergency operating notices with reserve actions, (iii) seasonal/interim locational requirement resets (the "Locational Reserve Requirements" posting history), (iv) largest-single-contingency changes if logged | NYISO operations announcements archive + Ancillary Services Manual appendices + OATT filings | event timestamps |
| B3 | The published SENY 30-min MW requirement per capability year (closes the `TODO(SENY-MW)` placeholder at `docs/nyiso-rcpf-overlay.md:134` — our 1,100 MW is a nesting-midpoint stand-in, the $500 penalty is sourced) | NYISO OATT Rate Schedule 4 / locational reserve requirement filings | per capability year |
| B4 | DAM locational reserve requirements for the same products/regions if they differ from RT (we hold DAM AS **prices** already) | same as B1 | hourly |

**What it unblocks.** Issue #1344's endogenous RCPF/scarcity price formation. The
LP seam is already built and waiting: `ReserveFamily.requirement` is a per-hour
`(T,)` array (`config/reserve_config.py`) and every NYISO family already carries
its RCPF shortfall steps in-LP — the mechanism work in this lane adds the
ScenarioConfig-gated hourly-requirement channel; B1/B2 is the measured series that
makes the downstate families bind in the hours reality was short. Forward story:
the requirement regenerates as (published static base + condition rules applied to
forward weather/contingency states) — it responds to changed conditions by
construction. Without B1/B2 the >$300 downstate tail (C3c 10/12/42 h actual vs
0/0/7 modeled) stays a ledgered limitation; manufacturing it any other way is
forbidden (rules 13/26 — the CC econ_high 1.21 re-arm is the named anti-pattern).

> **STATUS 2026-07-10.** **C1 (Z2 price):** the NYISO SOM per-hub table was
> checked first as instructed — it carries Iroquois Z2 only as an **annual**
> average (the monthly values are vector charts, not tables), and the MMU
> footnotes the underlying indices as **Platts-sourced**, so the daily/monthly
> series is CONFIRMED a licence ask (NGI/ICE/Platts). The free annual level
> IS intaken: `nyiso-som-hub-fuel-annual` (2018–2025, 5 gas hubs + 3 oils,
> from the 2020/2022/2023/2024/2025 SOM Figure A-6 tables;
> `data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv`) — enough to re-level
> the flat-annual Z2 reconstruction against a measured annual, not enough to
> fix its intra-year shape. **C2 (Iroquois EBB flows): BLOCKED, not
> paywalled** — the postings are free and FERC-mandated, but every Iroquois
> host (`iroquois.com`, `iol.iroquois.com`) sits behind an Imperva/Incapsula
> bot-wall that this sandbox cannot (and should not try to) pass; the PipeRiv
> mirror is subscription-gated, and Wayback holds only the ExtJS app shell.
> Fulfillment route: a human browser session on
> `iol.iroquois.com/Infopost/Pages/Default.php` (Operationally Available
> Capacity + Scheduled Quantities, CSV export, date-range query) or an
> emailed request to Iroquois scheduling — both short-lead manual steps.

## Ask C — Iroquois Zone 2 (register ask; priority 2)

**Why.** The NYISO zonal gas overlay reconstructs Iroquois Z2 (the Capital/east-NY
marginal hub) from an annual Transco spread because no free monthly/daily Z2 series
exists (EIA's free tables carry Transco Z6 NY and Algonquin but not Iroquois Z2 —
`docs/nyiso-backcast-residual-attribution-2026-06.md` §4d/§4e). The flat-annual
reconstruction over-levels summer (2023/24 Jul–Aug ≈ +$10) and caps winter blowouts
at the Algonquin ceiling by construction (`fuel.nyiso_reconciled_reference_monthly`).

**Exact series requested (2023–2025):**

| # | Series | Source | Granularity |
|---|---|---|---|
| C1 | Iroquois Zone 2 hub spot gas price (daily midpoint; monthly index acceptable as a floor ask) | NGI, ICE, or S&P Platts (all paywalled — this is a purchase/licence ask), or the NYISO SOM per-hub monthly table if the MMU will share the underlying series | daily preferred |
| C2 | Iroquois Gas Transmission scheduled deliveries/flows at Zone 2 delivery meters (Athens, Dover, South Commack / LI laterals), i.e. the pipeline EBB posted scheduled quantities — free, FERC-mandated postings | Iroquois EBB informational postings archive | daily by cycle |

C2 is both (a) the free fallback conditioning variable if C1 stays paywalled — flow
against posted operational capacity marks the constrained days whose winter spread
the reconstruction currently smears annually — and (b) validation for the Z2 winter
scarcity events independent of any price vendor.

**What it unblocks.** The nyiso-42/43 winter-spread line: removes the reconstructed
summer over-level, grounds the east-NY winter marginal fuel without the Algonquin
ceiling approximation, and closes attribution-doc fix #1(b). Secondary contribution
to Ask A (the Z2-served CTs price off Z2, not Transco).

> **FULFILLED 2026-07-10 (free, wider than asked).** NYISO MIS P-32
> "ExternalLimitsFlows" (5-minute per-interface flow + positive/negative
> limits, internal interfaces AND all external ties) intaken 2018-01–2026-06,
> hourly-aggregated (documented reconciliation) →
> `data/raw/NYISO/interface-flows/` (`scripts/data/fetch_nyiso_interface_flows.py`)
> and the `nyiso-interface-flows` clean datatype (~157.7k rows/year, 18
> interfaces; 19 from 2026 when CHPE appears). Covers Central-East, Total
> East, UPNY CONED, Moses South, Dysinger East, West Central, SPR/DUN-SOUTH
> plus every external schedule (HQ, NE, OH, PJ, NPX 1385/CSC, PJM
> HTP/Neptune/VFT) with posted limits — the posting has no separate
> "UPNY-SENY" row; that boundary is spanned by TOTAL EAST / UPNY CONED
> (crosswalk to be documented at the consumer).

## Ask D — secondary (recorded 2026-07-04, winter-spread session; priority 3)

| # | Series | Source | What it unblocks |
|---|---|---|---|
| D1 | NYISO per-interface gross tie flows + ratings (esp. Central-East / UPNY-SENY, and the external ties behind the net-interchange wedge), hourly 2023–25 | NYISO OASIS interface flow postings | The upstate shoulder-collapse diagnosis: real upstate held ~$22–25 via gross two-way tie flows while the model pushes ~830 MW of net imports through the 1,450 MW CE TTC; per-interface data separates gross wheeling from the net wedge |

## Summary table

| Ask | Gates | Register/issue | Status (2026-07-10) |
|---|---|---|---|
| A (LI/NYC LDC delivered gas) | keeper re-solve legitimacy (G-13) | G-13, §4 NYISO row | **FULFILLED 2026-07-07** (free, National Grid tariff archive) |
| B (condition-varying reserve requirement) | #1344 scarcity tail (C3a/C3c), rule-20 C8 burn-down | #1344, G-20 | **B2+B3 FULFILLED free** (events 2018–H1-2026 + dated LRR schedule incl. SENY hourly steps) **and the hourly loader-contract series is DERIVED** (`NYISO_reserve_requirements_{2023..2025}.csv`, ready for `nyiso_dynamic_reserve_requirements`); B1/B4 = NYISO data request only |
| C (Iroquois Z2 price/flows) | winter spread, summer over-level | register §4 NYISO row | C1 **annual level free** (SOM 2018–2025); daily/monthly = confirmed licence ask. C2 free-but-bot-walled → manual browser/email step |
| D (per-interface tie flows) | upstate shoulder | 2026-07-04 log | **FULFILLED 2026-07-10** (MIS P-32, hourly, 2018–H1-2026) |

**Drop zones on arrival:** A → `data/raw/gas-prices/` (extend the basis CSV schema,
per-LDC rows); B → `data/raw/NYISO-AS/requirements/` (new; schema-first per the
data-intake skill before commit); C1 → `data/raw/gas-prices/`; C2/D1 →
`data/raw/NYISO/`. All intake via the `data-intake` skill (schema + clean seam),
2023–2025 rows only.
