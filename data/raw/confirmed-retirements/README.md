# Confirmed-retirements registry (raw)

Hand-curated, per-ISO extracts of **binding** retirement instruments — the
retirement analogue of the additions pipeline's U/V/TS construction-committed
statuses. Only confirmed exits (units already offline, or future exits bound by
an enforceable public instrument) belong here. **Announced** retirements
(EIA-860 planned dates, IRP/press announcements) do NOT — they stay with the
economic-retirement screen (`model.capacity.apply_economic_retirements`).

Each ISO's rows live in `<iso>.csv` in the canonical schema
(`data/dictionary/schema/confirmed-retirements.schema.yaml`). The curation
script (`scripts/data/curate_confirmed_retirements.py`) validates every row
against the EIA-860 fleet spine (plant/generator must exist; `capacity_mw`
within 5 % of nameplate; `exit_year >= 2023`) and writes the clean partition.
The consumption seam is
`market_sim.data.confirmed_retirements.load_confirmed_exits`, feeding
`model.capacity.apply_confirmed_exits` — **forecast-mode only**, gated on
`ScenarioConfig.confirmed_exits_enabled` (**default ON** since the 2026-07-05
owner sign-off; plan §7).

## Binding instruments, per ISO

| ISO | Binding instrument (confirmation) | Public source to re-query |
|---|---|---|
| PJM | Deactivation request past reliability review with a confirmed date and no RMR; RMR **end** date where an RMR exists | PJM "Generator Deactivations" posting (XLSX) |
| MISO | Attachment Y retirement request **approved** (suspensions excluded — reversible) | MISO generator-retirements / Attachment Y status posting |
| NYISO | Generator Deactivation Notice completed per OATT; state (DEC/PSC) orders | NYISO deactivation-notices posting; Gold Book (announced-grade cross-check) |
| ISO-NE (NEISO) | **Two-regime bar (restated 2026-08-31, NEISO-RC-R R1(iii))** — FCM era: Retirement De-List Bid / Non-Price Retirement Request **Approved** (or unconditional "retire regardless" election) per the retirement tracker; RMR/cost-of-service agreement **end** dates (`rmr_end`, e.g. Mystic 8/9's 165 FERC ¶ 61,267). CAR era (FERC accepted CAR-PD 2026-03-30, ER26-925, effective 2026-03-31): a **submitted one-year deactivation notification** under the reformed §III.13. **Permanent** De-List Bids are capacity-market-only exits and are NEVER instruments in either regime | ISO-NE retirement tracker (`retirement_tracker_external.xlsx`) + the CAR deactivation-notification posting surface once live |
| CAISO | State instruments: SWRCB OTC compliance dates, CPUC/CEC decisions (SB 846 Diablo Canyon) | SWRCB OTC compliance-schedule table; CPUC/CEC dockets |
| ERCOT | Notification of Suspension of Operations (NSO) accepted, RMR review concluded **without** an agreement; permanent suspensions | ERCOT market notices / suspension-retirement notices |
| SPP | **State commission orders** (NMPRC / OCC / KCC / MPSC / NPSC / PUCT — the footprint is largely vertically integrated, so the binding act is the regulator's, not the RTO's), federal consent decrees, statutes. SPP runs no deactivation-acceptance process (`rto_deactivation` never expected). An EIA-860 date, an IRP filing or a board resolution that *defers* a date is announced-stage, not an instrument. First curated 2026-09-07 (SPP-60): Tolk 1/2 (NMPRC 22-00286-UT, 2023-10-19; deferred to 2029-03 by the 2026-05-07 IRP approval). Candidates held out with reasons in the file header (North Omaha 4/5, Lawrence 4/5, Northeastern 3, Pirkey, Horseshoe Lake) | NMPRC / OCC / KCC dockets; utility rate-case and IRP orders |
| all | Federal consent decrees & court-approved settlements (EPA/DOJ NSR); dated state statutes (IL CEJA, coal phase-outs); PUC settlement/securitization orders | court dockets, state PUC dockets, statute text |

**Counter-instruments** (RMR/must-run agreements, DOE §202(c) orders,
deactivation-request withdrawals, statute amendments) remove or defer
confirmation. A row hit by one is marked `superseded=true` with its
`superseding_instrument` cited — kept for audit; the loader ignores it and the
unit reverts to the economic screen.

## Vintage

**Registry vintage: 2026-08-03** (FFR-PA refresh pass; every row's `accessed`
stamp carries it). Previous vintages 2026-07-31, 2026-07-05. See
`docs/handoffs/ffr-pa-confirmed-retirements-refresh-2026-08-03.md` for the
per-ISO findings, the FR-18 Eddystone §202(c) adjudication, the Schahfer /
Culley hold-out, and the proposed quarterly re-query cadence.

## Status — 2026-08-03 refresh pass (current)

**Zero rows changed exit behaviour.** No row was added, deleted, or had its
`exit_year` moved. Every row's `accessed` stamp advanced to 2026-08-03, one
citation was strengthened, and two new candidates were adjudicated and held
out. In a registry that bypasses the reliability floor, a pass that correctly
changes nothing is a result, not a non-event.

- **PJM** (14 rows, 8 live) — **Eddystone 3–4 (FR-18): successor state STILL
  NOT PUBLISHED.** The DOE 2026 §202(c) log remains current through
  No. 202-26-37 (2026-07-26) with no Eddystone order after No. 202-26-24, which
  stays operative **through 2026-08-22 (19 days out)**. The honest entry is
  *pending*; nothing was recorded speculatively and the rows stay
  `superseded=true`. (Trap noted for the next pass: a numbering search surfaces
  "202-26-38/39/40" — those are the DOE **natural-gas** order series, not
  §202(c) electric, and are not a successor.) Provenance strengthened only:
  DOE Orders **No. 202-25-4A** (2025-08-01, denial of rehearing by operation of
  law) and **No. 202-25-4B** (2026-01-10, order addressing rehearing arguments)
  added to the chain — they show it survived rehearing, and change no field.
  **Brandon Shores / Wagner's 2031-05 extension is still un-approved at FERC**,
  so those four rows stay 2029-05 — but this is now the registry's
  most-likely-to-move row: PJM asked FERC to decide by **early August 2026**.
  Cardinal 3 and West Lorain 1A/1B stay held out (deactivation letters posted,
  **no reliability determination** — PJM's page is unchanged since 2026-07-30).
- **MISO** (7 rows, 4 live) — Campbell's DOE No. 202-26-22 has **no published
  successor** and expires **2026-08-16 (13 days out)**, the nearest expiry in
  the registry. **Two §202(c)-deferred coal clusters the prior passes never
  saw were found and HELD OUT: R M Schahfer 17 & 18 (846 MW) and F B Culley 2
  (103.7 MW).** Both are held out on a *bar* question, not a sourcing one: a
  `superseded` row still needs an underlying **binding** instrument, and DOE's
  own orders source these units' exit dates to **EIA-860 Schedule 3** — the
  owner's self-reported plan. IURC Cause No. 46198 was read directly and does
  not order the Schahfer retirement (it is a Templeton Wind CPCN order that
  merely recites the date in testimony). See the Attachment Y note below.
- **ERCOT** (3 rows, 3 live) — re-queried, **unchanged**. Braunig 3's RMR term
  is still Start 2025-03-02 / Stop 2027-03-01 with no extension executed.
- **CAISO** (10 rows, 8 live) — re-queried, **unchanged**. OTC final compliance
  stays 2026-12-31 for all six OTC units (2.86 GW binding in ~4 months). The
  NRC's April 2026 Diablo Canyon licence renewals to 2044/2045 were found and
  **deliberately not applied**: SB 846's statutory ceiling (2029/2030) is the
  instrument, and under Addendum E licence dates are not an exit channel.
- **NEISO** (2 rows) — re-queried, **unchanged** (consent decree, 2028-06).
- **NYISO** (0 rows) — **still an honest zero.** Danskammer remains held out:
  its determination fixes no date requiring the unit offline. Near-term watch —
  its **2026-08-01 contingency date has just passed**.

### MANUAL DOWNLOADS NEEDED — 2026-08-03 update

The MISO blocker is **re-characterised** this pass: it is two *different*
blockers on two hosts, and the OASIS half is not what the previous pass assumed.

| Source | Blocker (verified 2026-08-03) | What it would unblock |
|---|---|---|
| **MISO Attachment Y** approved-retirements posting + per-request Attachment Y Study Reports | **Two distinct blockers.** (a) `www.misoenergy.org` → HTTP **403** on every path (site-side WAF); `cdn.misoenergy.org` 403s on directories but **serves individual documents fine**, which is how this pass read MISO's LOLE, MTEP and IMM materials — none publishes the unit list. (b) `www.oasis.oati.com` → **not a WAF: TLS chain validation failure** (`unable to get local issuer certificate`), identical with the system trust store and with the agent-proxy CA bundle, and the proxy reports no relay failures — so it is the OATI origin's own chain. TLS verification is never disabled, so the route is closed. This pass **confirmed OASIS is the canonical home** by locating a real published example (`…/MISOdocs/Presque_Isle_Att_Y_Study_Report_2014-08-15_PUBLIC.pdf`); that named document is blocked by the same TLS failure, so the block is total. | The standing never-done cross-check — now with **named targets**: query **Schahfer 17/18 (plant 6085)** and **Culley 2 (plant 1012)** first. If either carries an approved Attachment Y *retirement*, it becomes a `superseded=true` row on the Campbell pattern and this registry is currently missing **950.7 MW** of confirmed MISO exits. |
| PJM tabular generator-deactivation list | Unchanged: renders client-side and partly behind `pjmsignin`; only the document index is machine-readable. `deactivation-mothballed-units.xlsx` is retrievable but lists only mothballed units (currently none). | Adjudicating Cardinal 3 and West Lorain 1A/1B against real deactivation dates rather than document-posting dates. |
| ISO-NE nonprice-retirement / de-list-bid tracker | Unchanged: no current edition linked from the reachable FCM qualification pages; the cited copy self-reports 2024-02-28. | Re-checking the de-list candidates held out for want of an EIA-860 identity match. |

## Status — 2026-07-31 re-query pass (superseded by the pass above; retained for the audit trail)

Two rows changed exit behaviour, both by **adding** a row a prior pass had held
out; **no existing `exit_year` moved** and no row was deleted.

- **PJM** (14 rows, 8 live) — **Eddystone 3–4 (FR-18) adjudicated**: the
  operative counter-instrument is DOE Order **No. 202-26-24** (issued
  2026-05-21, effective 2026-05-25 **through 2026-08-22**), verified against
  the primary document's Ordering Paragraph H. **The successor state is NOT
  YET PUBLISHED** — DOE's 2026 §202(c) log is current through No. 202-26-37
  (2026-07-26) and carries no later Eddystone order — so nothing was recorded;
  the rows stay `superseded=true`. **Re-query immediately after 2026-08-22.**
  Brandon Shores/Wagner's 2031-05 RMR extension is **still pending FERC**, so
  those rows stay at 2029-05. Wagner 4 additionally carries DOE Order
  No. 202-26-25 (through 2026-08-19), which relieves a permitted run-hour cap,
  not a retirement date — logged, not treated as a counter-instrument.
  Rockport 1–2 unchanged, with a watch on the Indiana AG's 2026-07-31 motion to
  intervene in the consent-decree proceedings (a motion is not a modification).
- **ERCOT** (3 rows, 3 live) — **V H Braunig 3 ADDED** as an `rmr_end` row at
  2027-03 (417 MW). The 2026-07-05 pass held it out reasoning that an RMR keeps
  a unit *in* service; that reasoning would equally exclude PJM's Brandon
  Shores/Wagner rows and contradicts both the plan §4.3 and this README's own
  bar ("RMR end date where an RMR exists"). NSO (M-C031324-01, 2024-03-13,
  covering VHB1/2/3) and the executed RMR agreement (Start 2025-03-02, Stop
  2027-03-01) were both read as primary documents. **This is the only change
  in this pass that can move a default-config forecast result.**
- **MISO** (7 rows, 4 live) — **J H Campbell 1–3 ADDED as `superseded=true`**
  rows (MPSC Case No. U-21090, order 2022-06-23, retirement 2025-05-31;
  overridden by the DOE §202(c) chain now running through 2026-08-16). The
  previous pass excluded them for having "no binding retirement date" — which
  is what a superseded row *is*. Behaviourally inert at the default config;
  the value is the audit trail plus reversal suppression of a stale EIA-860
  announced date for a plant still running under federal compulsion.
  **Attachment Y cross-check attempted and still blocked** — see MANUAL
  DOWNLOADS NEEDED.
- **CAISO** (10 rows, 8 live) — all dates re-verified against a 2026-vintage
  primary source, the **SACCWIS Final 2026 Report**: Alamitos 3/4/5,
  Huntington Beach 2 and Ormond Beach 1/2 all still carry an OTC final
  compliance date of **2026-12-31** with owner status "Plans to comply", and
  no extension beyond it is recommended or adopted. Diablo Canyon's OTC final
  compliance date (2030-10-31) is consistent with the SB 846 / D.23-12-036
  dates already carried. Nothing changed; the citations are now stronger.
- **NEISO** (2 rows) — Merrimack 1–2 unchanged. Structural watch: ISO-NE's
  capacity-auction reform replaces de-list bids with a deactivation
  notification, which will require restating this ISO's row in the instrument
  table below.
- **NYISO** (0 rows) — **still an honest zero, re-researched not carried
  forward.** The one genuinely new candidate, **Danskammer**, is held out: its
  deactivation notice (filed 2025-12, requesting 2026-08-01) produced a NYISO
  determination that is conditional in both directions — it may not deactivate
  before 2027-01-15 absent in-service solutions, and if those slip it must
  remain in service for 2029/2030 Lower Hudson Valley needs. No date the
  instrument *requires* the unit offline means no confirmation class fits.
  (Danskammer HoldCo also filed Chapter 11 on 2026-06-10.) Gowanus/Narrows are
  retained, Far Rockaway's withdrawal is confirmed effective 2026-05-01.

### MANUAL DOWNLOADS NEEDED (blocked sources — never guessed around)

| Source | Blocker (verified 2026-07-31) | What it would unblock |
|---|---|---|
| MISO Attachment Y / approved retirements-and-suspensions posting | `www.misoenergy.org` returns **HTTP 403 to every path**, with and without a browser User-Agent — a site-side WAF block, not a proxy fault (the agent proxy reports no relay failures and `cdn.misoenergy.org` serves fine over the same path). The CDN-hosted PY 2026-2027 LOLE Study Report and MTEP25 Report were pulled and read as substitutes: both confirm MISO *consumes* Attachment Y approvals but neither publishes the unit list. | The standing never-done cross-check. Until it lands, MISO coverage here is "what a state PUC order or consent decree made public", **not** "everything MISO has approved". |
| PJM tabular generator-deactivation list (unit, MW, requested/actual dates) | The table renders client-side and partly behind `pjmsignin`; only the document-index page is machine-readable. The linked `deactivation-mothballed-units.xlsx` *is* retrievable but lists only mothballed units (currently none). | Adjudicating newly-filed notices (Cardinal 3, West Lorain 1A/1B) against real deactivation dates rather than document-posting dates. |
| ISO-NE nonprice-retirement / de-list-bid tracker | No current edition is linked from the FCM qualification pages reachable here; the copy cited by the previous pass self-reports 2024-02-28 as its last update. | Re-checking the de-list candidates held out for want of an EIA-860 identity match. |

## Status (2026-07-05, second intake pass — superseded by the pass above; retained for the audit trail)

- **PJM** — seeded (`pjm.csv`, 10 rows): Rockport 1 (federal NSR consent decree,
  2028) + Rockport 2 (separate Indiana IURC Cause No. 45546 order, 2028 — split
  from a single mis-attributed citation in the first pass), Kincaid 1–2 (IL
  CEJA statute, 2030), Brandon Shores 1–2 + H.A. Wagner 3–4 (`rmr_end`, 2029 —
  a further extension to 2031 is pending, not yet FERC-approved), Eddystone
  3–4 (`superseded` by DOE 202(c) — worked counter-instrument; exit_year
  corrected 2026→2025 in this pass).
- **ERCOT** — seeded (`ercot.csv`, 2 rows): V H Braunig 1–2 (binding NSO,
  effective 2025-03-31 — confirmed by ERCOT's Board declining to RMR them).
  V H Braunig 3 stays held out — the *opposite* of retiring: it's under a
  binding RMR agreement (2025-03 to 2027-03) keeping it in service. Spruce /
  Sommers remain announced-grade (economic screen).
- **MISO** — seeded (`miso.csv`, 4 rows): DTE Monroe 1–4 (Michigan PSC Case
  No. U-21193 settlement — Units 3–4 by 2028, Units 1–2 by 2032). Direct fetch
  of MISO's own Attachment Y posting failed (TLS/access errors); a human with
  browser access should cross-check this posting directly at the next intake
  vintage. Everything else in the ~13.5 GW EIA-860-flagged 2026–2028 coal
  cluster was investigated and held out (announced/IRP-stage/contested/fuel-
  conversion — see `miso.csv` header for the full per-plant list).
- **NYISO** — still `DATA NEEDED` (`nyiso.csv`, 0 rows): every forward-looking
  deactivation notice found (Far Rockaway, Gowanus/Narrows, Pinelawn) has been
  reversed via a NYISO reliability determination (returned to service or
  withdrawn) — see `nyiso.csv` header. Honest zero, not an unresearched gap.
- **NEISO** — seeded (`neiso.csv`, 2 rows): Merrimack Station 1–2 (2024 Clean
  Water Act consent decree, 2028-06 — the plant actually ceased operating
  entirely 2025-09-12, ahead of the decree deadline). The ISO-NE de-list-bid
  tracker's other forward candidates could not be matched to a current
  EIA-860 plant/generator identity (tracker itself flags 2024-02-28 as its
  last update) and were excluded rather than seeded on an unverified match.
- **CAISO** — seeded (`caiso.csv`, 10 rows): AES Alamitos 3–5 / AES Huntington
  Beach 2 / Ormond Beach 1–2 (SWRCB OTC Resolution 2023-0025, 2026-12-31), and
  Diablo Canyon 1–2 (SB 846 + CPUC D.23-12-036, 2029/2030) plus its two
  `superseded` rows carrying the plant's earlier 2016-settlement exit dates —
  the worked `superseded` audit-trail example for this datatype.

**Every row above passed `scripts/curate_confirmed_retirements.py`'s EIA-860
spine cross-check (identity + MW within 5 %) against the real fleet spine.**
All instruments were independently re-verified via web research on
2026-07-05. Two rows had carried an explicit in-row caveat where a specific
docket/decision number could not be independently confirmed via secondary
sources (Rockport 1's civil action number; Diablo Canyon's CPUC decision
number) — both were resolved in a primary-document confirmation pass on
2026-07-05: Rockport 1's citation was checked directly against the filed
Fifth Joint Modification (Case 2:99-cv-01250-EAS-KAJ Doc #438), confirming
Consolidated Cases C2-99-1182/C2-99-1250 and its Paragraph 140 exit date;
Diablo Canyon's D.23-12-036 was checked directly against a CPUC decision in
R.23-01-007 that quotes D.23-12-036 verbatim, confirming the decision number
and both units' authorized-operation end dates. See the `pjm.csv`/`caiso.csv`
row notes for the full citations. Both rows are now on primary-document
footing and neither caveat remains.

**The default-flip to `confirmed_exits_enabled=True` is now unblocked on data
grounds for all six ISOs (five seeded + NYISO's honest zero) and the two
outstanding primary-document caveats have been resolved (2026-07-05) — the
flip has been executed per the owner's sign-off (plan §7).**
