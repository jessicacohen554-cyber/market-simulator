# FFR-PA — Confirmed-retirements registry re-query; Eddystone §202(c) adjudication

**Date:** 2026-07-31 · **Session:** FFR-PA (Wave P, parallel-anytime intake) of
`docs/forecast-readiness-prompt-pack-2026-07.md` · **Closes:** audit finding
**FR-18** (`docs/forecast-readiness-audit-2026-07.md` §3.4) on its
time-sensitive half · **Bar applied:** `docs/handoffs/confirmed-retirement-plan-2026-07.md`
(a row needs an enforceable public instrument — RTO deactivation acceptance,
consent decree, statute, regulatory order, RMR end).

**Scope discipline:** DATA ONLY. No LP solved, no mechanism, default, threshold
or curve changed, no CI workflow added, nothing registered on any dashboard.
Rule 22 untouched — this is forward registry data for the forecast
confirmed-exit channel, not out-of-training backcast data. No mechanism-matrix
cell was touched (no mechanism was tested).

---

## 1. Headline

The registry moved from vintage 2026-07-05 to **2026-07-31**. Every row in all
six ISOs was re-queried against its own public source.

- **No existing `exit_year` moved, and no row was deleted.**
- **Two additions**, both reversing an earlier pass's hold-out on grounds that
  were internally inconsistent with rows already in the registry:
  **ERCOT V H Braunig 3** (live, `rmr_end` 2027-03) and **MISO J H Campbell
  1–3** (superseded, audit-trail).
- **Eddystone (FR-18):** the current order is **DOE No. 202-26-24**, effective
  2026-05-25 **through 2026-08-22**, verified against the primary document.
  **No successor is published**, so none was recorded.
- One standing gap remains genuinely blocked and is now characterised rather
  than guessed at: **MISO's Attachment Y posting** (site-side WAF).

Only **one** change in this pass can move a default-config forecast result:
the Braunig 3 addition (§3).

---

## 2. FR-18 — the Eddystone §202(c) adjudication

The audit flagged that the DOE order compelling Eddystone 3–4 to run expires
2026-08-22, "flipping a supersession", and asked for the successor state to be
recorded **when published, never speculatively**.

**Primary document read this pass** (`https://www.energy.gov/documents/doe-emergency-order-202-26-24`):

> **Order No. 202-26-24** … *H. This Order shall be effective on May 25, 2026,
> through August 22, 2026, with the exception of applicable compliance
> obligations in paragraph D.* — Issued in Washington, D.C. on this 21st day of
> May 2026.

The order's Background section recites the full chain, which is now written
into both rows' `superseding_instrument`:

| Order | Issued | Runs through |
|---|---|---|
| 202-25-04 | 2025-05-30 | 2025-08-28 |
| 202-25-8 | 2025-08-28 | 2025-11-26 |
| 202-25-10 | 2025-11-25 | 2026-02-24 |
| 202-26-17 | 2026-02-23 | 2026-05-24 |
| **202-26-24** | **2026-05-21** | **2026-08-22** |

**Successor state as of 2026-07-31: NOT YET PUBLISHED.** DOE's 2026 §202(c)
order log is current through **No. 202-26-37** (issued 2026-07-26) and contains
no Eddystone order after 202-26-24. There is therefore nothing to record —
neither renewal, nor lapse, nor supersession. The rows are unchanged and stay
`superseded=true`.

**Consequence and the next action.** Because the counter-instrument is a
90-day rolling order, the registry has a live expiry inside the forecast's
first year. After 2026-08-22 exactly one of two things is true and each has a
different registry edit:

- **renewed** → extend `superseding_instrument` with the new order; rows stay
  `superseded=true`; nothing else changes;
- **lapsed without renewal** → the PJM-approved 2025-05-31 deactivation
  revives and the rows flip to **`superseded=false`**, at which point they
  become 780 MW of *live* confirmed exit already dated in the past, i.e. the
  injector removes them at the first forecast year.

That flip is a real forecast change, and nothing in the repo will notice the
date passing. It is the concrete motivation for the cadence proposal in §6.

**One defect fixed while in the row:** `superseding_instrument_date` was
**null** on both Eddystone rows. `load_announced_reversal_plants` gates
reversal suppression on that column, dropping any plant whose date is null
when an `as_of` cutoff is supplied — so plant 3161 was silently excluded from
reversal suppression in every as-of-gated hindcast. It is now `2025-05-30`
(the first order's date, i.e. when the reversal became knowable). Byron/Dresden
already carried theirs correctly (2021-09-15); Eddystone was the outlier.

---

## 3. Row changes, per ISO

### PJM — 14 rows (8 live), no date moved

| Item | Outcome |
|---|---|
| Eddystone 3–4 | §2 above. Unchanged, citations upgraded, successor pending. |
| Brandon Shores 1–2, Wagner 3–4 | **2031-05 extension still PENDING FERC.** Talen and PJM filed for it; reporting dated 2026-06-11 confirms it was un-approved then, and no granting order was found as of 2026-07-31. `exit_year` stays **2029-05** — the FERC-approved 2025-05-01 settlement is the only binding instrument. The bar records instruments, not pending requests. |
| Wagner 4 (additional) | **DOE Order No. 202-26-25** (issued 2026-05-21, effective 2026-05-22 through 2026-08-19) keeps Wagner Unit 4 available notwithstanding the **run-hour cap in its environmental permit**. This relieves an *operating restriction*, not a retirement date, so it is **not** a counter-instrument: logged in the row's notes, `exit_year` and `superseded` untouched. Worth knowing it exists — it is easy to mistake for an Eddystone-style supersession. |
| Rockport 1 | Consent decree unchanged. **WATCH:** the Indiana Attorney General announced on **2026-07-31** a motion to intervene in the consent-decree proceedings seeking to block the 2028 closure; I&M's replacement ~1.5 GW Rockport gas plant is before the IURC with a decision expected early 2027. A filed motion is not a decree modification — nothing changes unless the S.D. Ohio court modifies Paragraph 140. |
| Rockport 2 | Date re-confirmed at 2028-12-31 (IURC Cause No. 45546, settlement filed 2021-09-13, order approved 2021-12-08). Its `source_url` pointed at S&P Global, which is paywalled and now returns **HTTP 403**; replaced with AEP's own retrievable ELG required posting, titled for the plant's *permanent cessation of coal combustion by 12-31-2028*. (The S&P headline's "by 2029" is loose phrasing for an end-of-2028 deadline, not a competing date.) |
| Kincaid 1–2, Byron 1–2, Dresden 2–3 | Re-queried, unchanged. |

**New PJM candidates seen and held out** (PJM Generator Deactivation Notices
page, accessed 2026-07-31): **Cardinal Unit 3** (notice document posted
2026-07-30) and **West Lorain 1A/1B** (2026-06-19). PJM's bar is a notice *past
reliability review with a confirmed date and no RMR*; a freshly filed notice is
not that, so both stay announced-grade. Also recorded, because they show the
counter-instrument channel is live: deactivation-notice **withdrawal** letters
posted 2026-07-07/08 for Aurora CT1–CT10 / University Park, Fisk / Powerton /
Waukegan, Rockford CT11/CT12/CT21 and Zion CT1–CT3. None of these plants had a
row, so nothing changed.

### ERCOT — 3 rows (3 live); **V H Braunig 3 ADDED**

This is the one substantive addition, and the only change in the pass that can
move a default-config forecast result. **Flagging it explicitly for the owner
because it reverses a documented decision.**

The 2026-07-05 pass held Unit 3 out with this reasoning: *"Opposite instrument:
ERCOT and CPS Energy executed a binding RMR Agreement … keeping the unit IN
SERVICE — the inverse of a retirement."* That reasoning does not survive
contact with the rest of the registry:

- it would equally exclude **Brandon Shores 1–2 and H.A. Wagner 3–4**, which
  are in the registry as `rmr_end` rows keyed to their RMR's end date;
- the plan §4.3 directs the opposite in as many words — *"ERCOT: Braunig 1–3
  (NSO filed; unit 3 under an RMR-type agreement — `rmr_end` class for the
  agreement's end …)"*;
- the datatype README's own instrument bar reads *"RMR **end** date where an
  RMR exists"*;
- and the `rmr_end` confirmation class exists precisely for this shape: a
  filed exit instrument whose date an RMR defers.

Both primary documents were read this pass:

- **ERCOT market notice M-C031324-01** — three NSOs received **2024-03-13** for
  `BRAUNIG_VHB1`, `BRAUNIG_VHB2`, `BRAUNIG_VHB3`, indefinite suspension
  effective 2025-03-31.
- **ERCOT / CPS Energy Standard Form RMR Agreement, V.H. Braunig Unit 3**,
  Section 2 Specific Terms — *Start Date: March 2, 2025 · Stop Date: March 1,
  2027 · RMR Unit: V.H. Braunig, unit 3, BRAUNIG_VHB3*, 400 MW contract
  capacity; Section 3 Term runs 0000 on the Start Date to 2400 on the Stop
  Date.

Row: plant 3612, generator 3, 417.0 MW (EIA-860 nameplate; the RMR contracts
400 MW), `exit_year=2027`, `exit_month=3`, class `rmr_end`, `instrument_date`
2025-02-24. Under the injector's annual convention (`exit_month <= 6` →
`exit_year`), the unit leaves the fleet from 2027. EIA-860 status is `OA`
(out of service, expected back within the year), consistent with RMR standby
rather than merchant operation.

**Watch, deliberately not pre-empted:** ERCOT's San Antonio South Reliability
Project II — the transmission fix that ends the local need — is not expected in
service before 2027-06 (reported range 2027-06 to 2029-05), so an RMR extension
past 2027-03 is plausible. The bar records instruments, not expectations; if an
extension is executed, the row's `exit_year` moves then. This is the same
posture the registry already takes on Brandon Shores' pending 2031 extension.

### MISO — 7 rows (4 live); **J H Campbell 1–3 ADDED as superseded**

The 2026-07-05 pass held Campbell out reasoning *"No binding retirement date
currently exists — the opposite of confirmed."* That is the definition of a
**superseded** row, not of an absent one. The binding date does exist —
**MPSC Case No. U-21090**, order issued **2022-06-23** approving Consumers
Energy's contested IRP settlement, retirement date **2025-05-31** — and is
overridden by a rolling DOE §202(c) chain: 202-25-3 (2025-05-23) → 202-25-7 →
202-25-9 → 202-26-16 → **202-26-22, currently through 2026-08-16**, under
litigation. That is precisely the Eddystone pattern the schema's `superseded`
flag was designed around, and leaving it unrepresented meant the registry's two
worked counter-instrument cases were treated inconsistently across ISOs.

Rows: plant 1710, generators 1/2/3 at 265.2 / 378.8 / 916.8 MW (EIA-860
nameplates), `superseded=true`, `superseding_instrument_date` 2025-05-23.

**Behaviourally inert at the default config**, by construction: the loader
drops superseded rows, so the economic screen governs exactly as before; and
Campbell is coal, so the announced channel is a no-op for it while
`forecast_fossil_retirement_economic=True`. The value is (a) the audit trail
the plan §2.2 requires for counter-instruments, and (b) plant 1710 becoming
fully-superseded, so `load_announced_reversal_plants` suppresses the stale
EIA-860 `planned_retirement_year=2026` for a plant that is demonstrably still
running under federal compulsion — the Byron/Dresden failure mode, in advance.

**Attachment Y cross-check — attempted, still blocked, now characterised.**
See §5.

### CAISO — 10 rows (8 live), no date moved, every citation upgraded

Re-verified against a 2026-vintage primary source, the **SACCWIS Final 2026
Report**. Its compliance-date table lists **Alamitos 3/4/5** (1,141 MW),
**Huntington Beach 2** (227 MW) and **Ormond Beach 1/2** (1,491 MW) each with
an OTC Policy final compliance date of **Dec. 31, 2026** and owner status
*"Plans to comply by Dec. 31, 2026"*. **No extension beyond 2026-12-31 is
recommended or adopted anywhere in that report.** The dates stand.

This matters more than a routine confirmation: the previous pass explicitly
warned that SWRCB had extended these dates twice before and to re-verify. It
has not extended them a third time, and 2.86 GW of CAISO capacity is now
5 months from a binding exit inside the forecast's first year. A Q4 2026
re-query should capture actual compliance or a late amendment.

Diablo Canyon: the same report gives the plant's OTC final compliance date as
**October 31, 2030**, consistent with the SB 846 / D.23-12-036 authorized-
operation end dates the rows already carry. Unchanged.

### NEISO — 2 rows, unchanged

Merrimack 1–2 re-queried: the 2024 CWA consent decree deadline (2028-06) is
unchanged, and the station ceased operating entirely 2025-09-12, ahead of it.
Noted in-row: the EIA-860 spine still carries self-reported
`planned_retirement_year` 2027 (Unit 1, status OP) and 2028 (Unit 2, status OS)
— the decree, not the owner's plan, is the instrument.

**Structural watch for the next vintage:** ISO-NE's capacity-auction reform
replaces the four-year-ahead de-list-bid construct with a one-year deactivation
notification. When it takes effect, this ISO's row in the README instrument
table ("Retirement / Permanent De-List Bid **cleared** in an FCA") stops
matching any real instrument and must be restated.

### NYISO — 0 rows; **still an honest zero, re-researched**

Checked against the 2026 Gold Book deactivation pipeline (Table IV-5, which
grew from 48 MW of summer capability in the 2025 edition to **1,307 MW** in the
2026 edition) and the NYISO planning status reports.

**Danskammer** is the one genuinely new candidate and the closest any NYISO
unit has come to the bar — and it is held out. Its deactivation notice (filed
2025-12, requesting 2026-08-01) produced a NYISO determination that is
conditional in **both** directions: it may deactivate on the requested date
only if the identified Lower Hudson Valley solutions are in service and
demonstrating capability by then, and it may **not** deactivate before
**2027-01-15** absent them — and if those projects slip it "would need to
remain in service" for LHV needs arising in **2029 and 2030**. There is no date
at which the instrument *requires* the unit offline, which is what a
confirmation class asserts; retention past 2027 is an explicitly contemplated
outcome, not a tail risk. Danskammer HoldCo also filed Chapter 11 on
2026-06-10.

The other pipeline entries are unchanged from the previous pass:
Gowanus 2–3 / Narrows 1–2 carry a 2029-05-01 date but are marked **retained**;
Far Rockaway GT1/GT2's withdrawal is confirmed effective 2026-05-01 with the
units retained under a LIPA capacity purchase agreement; Pinelawn remains in
the deferred/must-run pattern.

**Zero remains the correct row count for NYISO.**

---

## 4. Verification

- `PYTHONPATH=.:src python scripts/data/curate_confirmed_retirements.py` —
  clean, all rows pass the EIA-860 spine cross-check (identity + nameplate
  within 5 %):
  `CAISO 10 rows/8 live · ERCOT 3/3 · MISO 7/4 · NEISO 2/2 · NYISO skipped
  (0 rows) · PJM 14/8`.
- `pytest tests/unit/data/test_confirmed_retirements.py
  tests/curation/test_curate_confirmed_retirements.py` → **28 passed**.
- `pytest tests/unit/model/test_capacity.py -k "Confirmed or confirmed or
  reversal or announced"` → **21 passed**.
- Loader read-back after curation confirms the intended behaviour:
  ERCOT now returns 3 live exits including `plant 3612 gen 3 → 2027-3, 417 MW`;
  MISO's reversal-plant set is now `{1710}` (Campbell) alongside 4 unchanged
  live Monroe exits; PJM's reversal set is unchanged at `{869, 3161, 6023}`.
- Every URL cited in a changed row was fetched this pass. The two `source_url`
  values that return HTTP 403 to a plain client are recorded as such: the MPSC
  news release (readable in a browser; the existing Monroe row uses the same
  host) and the replaced S&P link (paywalled — swapped out, §3).

*Note for whoever runs this next in a fresh container:* this session's
container had **none** of the repo's Python dependencies installed
(`pip install -r requirements.txt`, plus `pytest`, was needed before anything
would import). Worth knowing before concluding a script is broken.

---

## 5. What is still blocked — MANUAL DOWNLOADS NEEDED

Never guessed around; each blocker was probed and characterised.

| Source | Blocker (verified 2026-07-31) | Unblocks |
|---|---|---|
| **MISO Attachment Y** / approved retirements-and-suspensions posting | `www.misoenergy.org` returns **HTTP 403 on every path tried, with and without a browser User-Agent**. This is a site-side WAF block, not a proxy fault: the agent proxy reports no relay failures and `cdn.misoenergy.org` serves fine over the same path. As substitutes, two CDN-hosted MISO planning documents were pulled and read — the **PY 2026-2027 LOLE Study Report** and the **MTEP25 Report**. Both confirm MISO *consumes* Attachment Y approvals ("MISO obtained information on generating resources with approved suspensions or retirements (as of June 1, 2025) through MISO's Attachment Y process") but **neither publishes the unit-level list**. No route to it exists from this environment. | The standing never-done cross-check. Until it lands, MISO coverage is "what a state PUC order or consent decree made public", **not** "everything MISO has approved" — and MISO holds the largest near-term coal-exit cluster of any modelled ISO. |
| **PJM tabular deactivation list** (unit, MW, requested/actual dates) | Renders client-side and partly behind `pjmsignin`; only the document-index page is machine-readable. The linked `deactivation-mothballed-units.xlsx` *is* retrievable but contains only mothballed units (currently none). | Adjudicating Cardinal 3 and West Lorain 1A/1B against real deactivation dates rather than document-posting dates. |
| **ISO-NE nonprice-retirement / de-list-bid tracker** | No current edition linked from the FCM qualification pages reachable here; the copy cited by the previous pass self-reports **2024-02-28** as its last update. | Re-checking the de-list candidates held out for want of an EIA-860 identity match. |

---

## 6. Proposed re-query cadence (PROPOSAL — not adopted, not built)

FFR-PA was asked to *propose, don't build*, a quarterly cadence line for the
plan. Nothing was automated and no workflow was added (runner minutes are
owner-billed).

The case for it is concrete rather than hygienic. This pass found **three**
registry-relevant expiries falling inside the next five months, none of which
anything in the repo would notice:

- **2026-08-16** — Campbell's DOE order,
- **2026-08-22** — Eddystone's DOE order (FR-18),
- **2026-12-31** — CAISO's 2.86 GW of OTC compliance dates actually binding.

A stale registry does not fail loudly: it silently keeps compelling or
releasing capacity on a lapsed instrument, and the `accessed` stamp is the only
evidence.

Proposed line for `docs/handoffs/confirmed-retirement-plan-2026-07.md` §7:

```
* **Quarterly re-query cadence (proposed 2026-07-31, FFR-PA; owner decision
  pending).** Re-query every ISO's rows against its public source once a
  quarter (target: first two weeks of Jan / Apr / Jul / Oct), refresh every
  row's `accessed` stamp whether or not the row changes, and bump the README
  vintage. Between quarters, re-query on demand whenever a row's own
  counter-instrument has a dated expiry — the rolling DOE §202(c) orders
  (Eddystone, Campbell) expire on ~90-day cycles and each expiry can flip a
  supersession, and a compliance date that actually binds (CAISO OTC,
  2026-12-31) needs a pass immediately after it passes. The registry carries
  the expiry dates it must be re-queried against in `superseding_instrument`;
  a quarterly pass that skips a row whose expiry has passed is not a pass.
  Deliberately manual: this is a human-in-the-loop curation datatype (plan
  §4.2) whose sources are PDFs, dockets and WAF-protected postings, and CI
  runner minutes are owner-billed — the cadence is a scheduling discipline for
  session prompts, not a job.
```

Two smaller follow-ups this pass surfaced, offered without acting on them:

1. **A staleness check is cheap and would have caught the null
   `superseding_instrument_date`.** A curation-time assertion that every
   `superseded=true` row carries a `superseding_instrument_date` would have
   failed on Eddystone since the column landed. (Not added here: it changes
   the curation contract, which is outside a data-only session.)
2. **The registry has no machine-readable expiry field.** Expiry dates live in
   `superseding_instrument` prose today, which is why no automation can flag
   them. A `superseding_instrument_expiry` column would make the cadence
   checkable rather than remembered — a schema-v3 question for the owner, not
   a change to make in passing.

---

## 7. Files changed

| File | Change |
|---|---|
| `data/raw/confirmed-retirements/pjm.csv` | 14 rows re-stamped; Eddystone 3–4 counter-instrument chain + `superseding_instrument_date`; Brandon Shores / Wagner pending-extension status; Wagner 4 DOE 202-26-25 note; Rockport 2 `source_url` replaced; header gains the 2026-07-31 pass block incl. held-out candidates and the PJM manual-download note. |
| `data/raw/confirmed-retirements/ercot.csv` | **+1 row (V H Braunig 3, `rmr_end` 2027-03)**; Braunig 1–2 re-stamped; header block. |
| `data/raw/confirmed-retirements/miso.csv` | **+3 rows (J H Campbell 1–3, `superseded`)**; gains the `superseding_instrument_date` column; Monroe 1–4 re-stamped; header block incl. the Attachment Y blocker. |
| `data/raw/confirmed-retirements/caiso.csv` | 10 rows re-stamped against the SACCWIS Final 2026 Report; header block. |
| `data/raw/confirmed-retirements/neiso.csv` | Merrimack 1–2 re-stamped; header block incl. the ISO-NE de-list → deactivation-notification structural watch. |
| `data/raw/confirmed-retirements/nyiso.csv` | Header block only — zero rows, re-researched (Danskammer adjudication). |
| `data/raw/confirmed-retirements/README.md` | Vintage → 2026-07-31; new per-ISO status section; MANUAL DOWNLOADS NEEDED table; fixed two stale statements (curation script path, and `confirmed_exits_enabled` described as default-OFF when it has defaulted ON since 2026-07-05). |
| `docs/handoffs/confirmed-retirement-plan-2026-07.md` | §7: the proposed cadence line added, marked PROPOSED / owner decision pending. |
| `docs/handoffs/ffr-pa-confirmed-retirements-refresh-2026-07-31.md` | This document. |

`data/clean/confirmed-retirements/` was regenerated locally to run the checks;
it is derived and gitignored, so it is not part of the commit.

---

## 8. Open items for the next pass

1. **Re-query Eddystone immediately after 2026-08-22** and Campbell after
   2026-08-16. Both are 90-day rolling orders; both flip a supersession.
2. **CAISO OTC** — re-query in Q4 2026; 2.86 GW binds 2026-12-31 and the
   dates have been extended twice before.
3. **MISO Attachment Y** — needs a human with browser access (§5). This is the
   largest remaining coverage gap in the registry.
4. **PJM** — adjudicate Cardinal 3 and West Lorain 1A/1B once PJM's
   reliability determinations publish; re-check the Brandon Shores / Wagner
   2031 extension at FERC.
5. **ERCOT** — re-check whether Braunig 3's RMR is extended past 2027-03 as
   San Antonio South Reliability Project II's in-service date firms up.
6. **Rockport** — track the Indiana AG's motion to intervene; only a court
   order modifying Paragraph 140 changes the row.
7. **ISO-NE** — restate the instrument bar when the de-list-bid construct is
   replaced by deactivation notification.
