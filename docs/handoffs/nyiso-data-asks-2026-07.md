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
> (`scripts/fetch_nyiso_downstate_ldc_transport.py`) and wired per-zone through
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
(`scripts/fetch_nyiso_downstate_gas_basis.py`): EIA N3050NY3 **statewide-NY** monthly
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

## Ask D — secondary (recorded 2026-07-04, winter-spread session; priority 3)

| # | Series | Source | What it unblocks |
|---|---|---|---|
| D1 | NYISO per-interface gross tie flows + ratings (esp. Central-East / UPNY-SENY, and the external ties behind the net-interchange wedge), hourly 2023–25 | NYISO OASIS interface flow postings | The upstate shoulder-collapse diagnosis: real upstate held ~$22–25 via gross two-way tie flows while the model pushes ~830 MW of net imports through the 1,450 MW CE TTC; per-interface data separates gross wheeling from the net wedge |

## Summary table

| Ask | Gates | Register/issue | Lead-time risk |
|---|---|---|---|
| A (LI/NYC LDC delivered gas) | keeper re-solve legitimacy (G-13) | G-13, §4 NYISO row | tariff/PSC digging — medium |
| B (condition-varying reserve requirement) | #1344 scarcity tail (C3a/C3c), rule-20 C8 burn-down | #1344, G-20 | NYISO data request — **longest** |
| C (Iroquois Z2 price/flows) | winter spread, summer over-level | register §4 NYISO row | vendor licence — medium |
| D (per-interface tie flows) | upstate shoulder | 2026-07-04 log | OASIS scrape — short |

**Drop zones on arrival:** A → `data/raw/gas-prices/` (extend the basis CSV schema,
per-LDC rows); B → `data/raw/NYISO-AS/requirements/` (new; schema-first per the
data-intake skill before commit); C1 → `data/raw/gas-prices/`; C2/D1 →
`data/raw/NYISO/`. All intake via the `data-intake` skill (schema + clean seam),
2023–2025 rows only.
