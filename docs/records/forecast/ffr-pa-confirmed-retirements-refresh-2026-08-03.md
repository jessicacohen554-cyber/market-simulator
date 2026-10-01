# FFR-PA — Confirmed-retirements registry refresh; FR-18 Eddystone adjudication

**Date:** 2026-08-03 · **Session:** FFR-PA refresh (data only, no LP solve) ·
**Base:** `origin/main` 98ad9c1 · **Branch:** `claude/confirmed-retirements-refresh-i9q0ha`
**Predecessor:** `docs/handoffs/ffr-pa-confirmed-retirements-refresh-2026-07-31.md`
(registry vintage 2026-07-31 — three days before this pass, not the 2026-07-05
vintage the session prompt assumed).

## 0. Headline

**Zero rows changed exit behaviour.** No row added, deleted, or moved; every
`exit_year`, `exit_month`, `confirmation_class` and `superseded` flag in all six
ISOs is byte-identical to `HEAD` (verified field-by-field, §6). What changed:
36 `accessed` stamps advanced to 2026-08-03, one citation was strengthened on
primary-document evidence, and **two newly-discovered MISO §202(c)-deferred coal
clusters were adjudicated and held out**.

**FR-18 (Eddystone §202(c)): the successor state is NOT YET PUBLISHED.** DOE
Order No. 202-26-24 remains operative through **2026-08-22** — 19 days out. The
honest entry is *pending*; nothing was recorded speculatively in either
direction, and the rows stay `superseded=true`.

The substantive result of this pass is the MISO half: the Attachment Y
cross-check is still blocked, but the blocker is now **correctly characterised**
(it is two different blockers, and the OASIS one is not what the previous pass
assumed), and the gap now has **named targets and a MW figure** instead of being
an abstraction.

## 1. FR-18 — Eddystone, adjudicated

| Item | Finding (2026-08-03) |
|---|---|
| Operative order | **No. 202-26-24**, issued 2026-05-21, effective 2026-05-25 **through 2026-08-22** |
| Successor | **NOT PUBLISHED.** DOE's 2026 §202(c) log is current through **No. 202-26-37** (2026-07-26) and carries no Eddystone order after 202-26-24 |
| Registry action | **None.** Rows unchanged at `superseded=true`; `exit_year`/`exit_month` already carry the underlying 2025-05-31 PJM-approved deactivation date |
| Next action | **Re-query immediately after 2026-08-22.** Renewal → extend `superseding_instrument`. Lapse without renewal → the deactivation revives and the rows flip to `superseded=false` |

Two independent checks were run so the "not published" claim is not a single
fetch: DOE's 2026 order log enumerated in full, and DOE's PJM-specific §202(c)
landing page. Neither shows a successor.

**A numbering trap, recorded so the next pass does not fall into it.** Searching
for the next order numbers surfaces **202-26-38, 202-26-39, 202-26-40** — these
are the DOE **natural-gas (NG) order series**, a different docket line, not
§202(c) electric orders. They are not an Eddystone successor and must not be
read as one.

**One provenance improvement, no behaviour change.** DOE's PJM §202(c) landing
page discloses two procedural orders in the Eddystone chain that the citation had
omitted: **No. 202-25-4A** (2025-08-01, *Notice of Denial of Rehearing by
Operation of Law*) and **No. 202-25-4B** (2026-01-10, *Order Addressing Arguments
Raised on Rehearing*). Both are now written into `superseding_instrument`. They
record that the chain **survived rehearing** — materially strengthening the
counter-instrument — while extending and terminating nothing. (Note also that DOE
renders the first order as `202-25-4` where this registry carries `202-25-04`;
same order.)

## 2. MISO — the substantive half

### 2.1 Two §202(c)-deferred coal clusters found, and both HELD OUT

Found by enumerating the DOE 2026 §202(c) log **end to end** instead of searching
it for the two plants already registered. The MISO IMM's 2025 State of the Market
presentation corroborates the scale independently: *"the DOE directed 2.2 GW of
coal-fired resources to remain online"* in MISO — which Campbell's 1,560.8 MW
alone does not account for.

| Unit | EIA-860 identity | MW | DOE §202(c) chain |
|---|---|---|---|
| R M Schahfer 17 | plant 6085, gen 17, status OP | 423.5 | 202-25-12 (2025-12-23) → 202-26-19 (2026-03-23) → **202-26-29** (2026-06-18, eff. 2026-06-22 **through 2026-09-19**) |
| R M Schahfer 18 | plant 6085, gen 18, status OP | 423.5 | same chain |
| F B Culley 2 | plant 1012, gen 2, status OP | 103.7 | 202-25-13 → 202-26-20 (2026-03-23) → **202-26-30** (2026-06-18, eff. 2026-06-22 **through 2026-09-19**) |

**Why held out.** This is a *bar* question, not a sourcing question. A
`superseded` row still requires an underlying **binding** instrument — that is
precisely what separates Eddystone (PJM-approved deactivation) and Campbell
(MPSC Case No. U-21090) from an announcement that a DOE order happens to have
overridden. For Schahfer and Culley the underlying exit is **announced-grade**,
on the primary documents themselves:

* **DOE Order No. 202-25-12** (Schahfer), Background: *"Unit 17 and Unit 18 are
  both slated to cease operations in December 2025"* — footnoted to *"U.S. Energy
  Information Administration, Form EIA-860, Schedule 3: Generator Data (2024)"*,
  i.e. to the **owner's self-reported planned date**.
* **DOE Order No. 202-26-20** (Culley), Background: *"Unit 2 was slated to cease
  operations in December 2025"* — same EIA-860 Schedule 3 footnote.
* **"Attachment Y" appears zero times** in all three DOE orders read in full
  (202-25-12, 202-26-19, 202-26-20), zero times in the Illinois Commerce
  Commission's comments in FERC Docket **EL26-36** on the Schahfer order, and
  zero times in the Organization of MISO States' motion to intervene/stay at DOE.
* **IURC Cause No. 46198** (order issued 2025-09-24) was pulled and read directly.
  It does **not** order the Schahfer retirement: it is a CPCN / build-transfer
  order for NIPSCO's **Templeton Wind Project** that merely *recites* the date in
  witness testimony (*"Units 17 and 18 will retire on December 31, 2025"*).
  Indiana IRPs are acknowledged, not approved. NIPSCO had already moved the date
  once unilaterally (2023 → 2025), which is what a company plan does and an
  instrument does not.

**Behaviourally this costs nothing at the default config.** Both plants are coal,
so with `forecast_fossil_retirement_economic=True` the announced channel is a
no-op for them either way and the economic screen governs.

**The honest caveat, stated rather than buried.** MISO's tariff requires advance
Attachment Y notice before retiring a resource, so for a December-2025 exit these
units very likely *did* file, and MISO very likely *did* approve. That inference
is deliberately **not acted on** — the bar takes instruments, not likelihoods —
but it is exactly why the cross-check below matters: if those approvals exist,
this registry is currently missing **950.7 MW** of confirmed MISO exits.

### 2.2 Attachment Y cross-check — attempted again, still blocked, blocker re-characterised

The previous pass recorded a single blocker ("`misoenergy.org` WAF-403; OASIS
TLS/access errors"). That is **two different blockers**, and the second one is
not what was assumed:

| Host | Blocker (verified 2026-08-03) |
|---|---|
| `www.misoenergy.org` | HTTP **403** on every path tried (site-side WAF), re-confirmed on both the Attachment Y dashboard page and the generator-interconnection path. |
| `cdn.misoenergy.org` | **403 on directory paths but serves individual documents normally** — a 4.5 MB LOLE study PDF pulled clean over the same route. This is how MISO's LOLE, MTEP and IMM materials were read this pass. **None publishes the unit-level list.** |
| `www.oasis.oati.com` | **Not a WAF.** TLS **chain validation failure**: `SSL certificate problem: unable to get local issuer certificate`, identically with the system trust store **and** with the agent-proxy CA bundle (`/root/.ccr/ca-bundle.crt`); the proxy reports no relay failures, so it is the OATI origin's own chain. TLS verification is never disabled, so the route is closed from here. |

**New and useful:** this pass **confirmed OASIS is the canonical home** of the
posting by locating a real published example —
`https://www.oasis.oati.com/woa/docs/MISO/MISOdocs/Presque_Isle_Att_Y_Study_Report_2014-08-15_PUBLIC.pdf`
("ATTACHMENT Y STUDY REPORT", marked PUBLIC). That **named document** is blocked
by the same TLS failure as the directory index, so the block is total rather than
a listing-permissions artifact. The target is no longer a guess about where the
data lives.

> **MANUAL DOWNLOAD NEEDED** — MISO's Attachment Y approved
> retirements-and-suspensions posting and the per-request Attachment Y Study
> Reports, pulled by a human with browser access from `www.misoenergy.org` or the
> OASIS document root above. **First two queries when it lands: Schahfer 17/18
> (plant 6085) and Culley 2 (plant 1012).** If either carries an approved
> Attachment Y *retirement* request, it becomes a `superseded=true` row on the
> Campbell pattern.

### 2.3 Registered MISO rows

Monroe 1–4 unchanged (no amending MPSC order). Campbell 1–3: successor to DOE
No. 202-26-22 **not published**; the order expires **2026-08-16** — the nearest
expiry anywhere in the registry.

## 3. Per-ISO re-query results

| ISO | Result | Detail |
|---|---|---|
| **PJM** | Unchanged (+1 citation) | Eddystone pending (§1). **Brandon Shores 1–2 / Wagner 3–4: the 2031-05 RMR extension is still un-approved at FERC**, so the rows stay 2029-05 — but this is now the registry's most-likely-to-move row: PJM asked FERC to decide by **early August 2026**, i.e. the window is open now. Wagner 4's DOE 202-26-25 (run-hour-cap relief, *not* a retirement counter-instrument) expires 2026-08-19 with no successor. Rockport 1–2 unchanged; the Indiana AG's motion to intervene is still a motion. Kincaid, Byron, Dresden unchanged. |
| **MISO** | Unchanged (2 hold-outs) | §2. |
| **ERCOT** | **No change** | Braunig 1–2 unchanged. Braunig 3's RMR term still Start 2025-03-02 / Stop 2027-03-01, **no extension executed or Board-approved**. (ERCOT materials render the same term as "March 3, 2025 through March 2, 2027" — the same agreement, not a different date.) Spruce/Sommers still announced-grade. |
| **CAISO** | **No change** | OTC final compliance still **2026-12-31** for Alamitos 3/4/5, Huntington Beach 2, Ormond Beach 1/2 — no extension beyond the 2023 SWRCB amendment. **2.86 GW binds in ~4 months.** Diablo Canyon unchanged — see §4. |
| **NEISO** | **No change** | Merrimack 1–2: consent decree still requires closure no later than 2028-06-01; station ceased operating 2025-09-12. Two corroborating non-instrument facts: Granite Shore cleared no capacity for June 2026–May 2028, and ISO-NE reports no formal retirement request on file — consistent with this row resting on the consent decree rather than a de-list bid. |
| **NYISO** | **Honest zero, held** | Danskammer remains held out — the determination fixes **no date at which the instrument requires the unit offline** (notice filed Dec 2025; reporting describes it as targeting 2027-01-14, with deactivation barred before 2026-08-01 and retention contemplated into mid-January 2027, or further for 2029/2030 LHV needs). Chapter 11 (2026-06-10) is distress, not an instrument. **No row was manufactured to make the ISO look covered.** |

**Watch, new and near-term (NYISO):** Danskammer's **2026-08-01 contingency date
passed two days before this pass**. Whether the Lower Hudson Valley solutions
entered service on time determines whether it may now deactivate or is held to
mid-January 2027. This is the single likeliest source of NYISO's first row.

## 4. Governance notes

**Nuclear (Addendum E, signed 2026-08-03).** The NRC approved Diablo Canyon's
operating-licence **renewals** in April 2026, relicensing the units to 2044/2045.
This was found and **deliberately not applied**, for two independent reasons,
recorded in `caiso.csv` so a later reader does not mistake the omission for an
oversight: (1) these rows' instrument is a California **statute** (SB 846), which
caps authorized operation at 2029-10-31 / 2030-10-31 regardless of the federal
licence, and the statutory ceiling did not move; (2) under owner decision **DB-A**
licence expirations are **ignored entirely** as an exit channel, so no nuclear row
may be sourced from a licence date in either direction. **No nuclear row was added
from a licence date.**

**Holdout policy (rule 22).** Untouched. This session ran **no LP solve of any
kind**, scored nothing, and registered nothing on any dashboard. Data intake is
explicitly not frozen (channel 1).

**Rule 27.** No file ≥300 lines was rewritten from generated content; all edits
were local (Edit tool / a round-trip-verified CSV script) and pushed as exact
on-disk bytes. The CSV rewrite path was proven byte-identical on a no-op
round-trip of all six files before any field was touched.

**No GitHub Actions workflow was created.** The cadence proposal (§5) is
deliberately prose and deliberately manual.

## 5. Re-query cadence — PROPOSED amendment (not adopted, not built)

The 2026-07-31 pass proposed a quarterly cadence; it is already in the plan's §7
as PROPOSED. This pass did not duplicate it — it **amended** it, because this
pass produced concrete evidence that the existing formulation is incomplete.

**The gap: it is refresh-only, and therefore blind to new counter-instruments.**
The proposed cadence re-queries *the rows the registry already has*. Schahfer and
Culley have no rows, so no expiry of theirs would ever have been checked; they
were found only by enumerating the DOE §202(c) log **in full**. Three prior passes
missed them.

**The amendment: every quarterly pass runs two legs.**

1. **Refresh** — every existing row against its own source; stamp `accessed`
   whether or not it changed; bump the README vintage.
2. **Discovery** — enumerate, end to end and independent of what is registered,
   the small number of registries that *create* confirmations and
   counter-instruments: the DOE §202(c) order logs (both year pages, read as a
   full list), each RTO's deactivation/retirement posting, and the ISO-specific
   state channels. Record what was enumerated and found nothing, so a later pass
   can distinguish "checked, empty" from "never checked".

**The expiry calendar this pass leaves behind**, in date order:

| Date | Item |
|---|---|
| **2026-08-16** | Campbell — DOE 202-26-22 |
| **2026-08-19** | Wagner 4 — DOE 202-26-25 (run-hour relief) |
| **2026-08-22** | **Eddystone — DOE 202-26-24 (FR-18)** |
| **2026-09-19** | Schahfer 17/18 + Culley 2 — DOE 202-26-29 / 202-26-30 (watch only; held out) |
| **2026-12-31** | **CAISO OTC — 2.86 GW, the first date in the registry that actually binds** |

Plus one trigger that does not fit a quarterly rhythm at all: **FERC's pending
decision on the Brandon Shores / Wagner 2031-05 RMR extension**, requested for
early August 2026, which would move four PJM rows from 2029-05 to 2031-05. A
decision window is as much a re-query trigger as an expiry — and neither is
visible to any code in the repo today.

The two smaller follow-ups the previous pass raised still stand and were not
acted on here (both change the curation/schema contract, outside a data-only
session): a curation-time assertion that every `superseded=true` row carries a
`superseding_instrument_date`, and a machine-readable
`superseding_instrument_expiry` column.

## 6. Validation

| Check | Result |
|---|---|
| CSV round-trip fidelity (before any edit) | **byte-identical on all six files** — the rewrite path cannot silently re-quote unrelated fields |
| `scripts/data/curate_confirmed_retirements.py` (EIA-860 spine: identity + MW within 5 %) | **5 partitions written, all rows pass** — CAISO 10 (8 live), ERCOT 3 (3), MISO 7 (4), NEISO 2 (2), PJM 14 (8); NYISO correctly skipped (0 rows) |
| `tests/unit/data/test_confirmed_retirements.py` + `tests/curation/test_curate_confirmed_retirements.py` | **28 passed** |
| `tests/unit/model/test_capacity.py` | **209 passed** |
| `load_confirmed_exits` per ISO | PJM 8, MISO 4, ERCOT 3, CAISO 8, NEISO 2, NYISO 0 — **identical to pre-change** |
| Behavioural diff vs `HEAD` on `exit_year`/`exit_month`/`confirmation_class`/`superseded`/`capacity_mw` | **0 added, 0 removed, 0 changed, all six ISOs** |

## 7. Files changed

| File | Change |
|---|---|
| `data/raw/confirmed-retirements/pjm.csv` | 14 rows re-stamped + per-row re-query notes; Eddystone 3–4 `superseding_instrument` gains the 202-25-4A/4B rehearing history; header gains the 2026-08-03 pass block (FR-18 adjudication, NG-series numbering trap, Brandon Shores decision window, Cardinal 3 / West Lorain still held out). |
| `data/raw/confirmed-retirements/miso.csv` | 7 rows re-stamped + notes; header gains the Schahfer/Culley discovery and hold-out with primary-document reasoning, and the re-characterised two-host Attachment Y blocker with named targets. |
| `data/raw/confirmed-retirements/ercot.csv` | 3 rows re-stamped + notes; header gains the no-change block. |
| `data/raw/confirmed-retirements/caiso.csv` | 10 rows re-stamped + notes; header gains the no-change block and the Diablo Canyon NRC-relicensing deliberate-non-application note. |
| `data/raw/confirmed-retirements/neiso.csv` | 2 rows re-stamped + notes; header gains the no-change block. |
| `data/raw/confirmed-retirements/nyiso.csv` | Header only (0 rows): Danskammer re-adjudicated, 2026-08-01 contingency watch added. |
| `data/raw/confirmed-retirements/README.md` | Vintage → **2026-08-03**; new current status section; MANUAL DOWNLOADS NEEDED table updated with the re-characterised MISO blocker; 2026-07-31 section demoted to audit trail. |
| `docs/handoffs/confirmed-retirement-plan-2026-07.md` | §7 cadence bullet **amended** (discovery leg + expiry calendar), still PROPOSED / owner decision pending. |
| `docs/handoffs/ffr-pa-confirmed-retirements-refresh-2026-08-03.md` | This document. |

`data/clean/confirmed-retirements/` was regenerated locally to run the checks; it
is derived and gitignored, so it is not part of the commit.

## 8. Open items for the next pass

1. **Re-query Eddystone immediately after 2026-08-22** (FR-18) and **Campbell
   after 2026-08-16**. Both flip a supersession. Beware the NG-series numbering
   trap (§1).
2. **Brandon Shores / Wagner** — check FERC now; the decision was requested for
   early August 2026 and would move four rows to 2031-05.
3. **MISO Attachment Y** — the manual download, with Schahfer 17/18 and Culley 2
   as the first two queries (§2.2). Largest remaining coverage gap: 950.7 MW.
4. **Schahfer / Culley** — re-query their DOE chain after **2026-09-19**; if
   either lapses and the unit actually retires, the exit arrives via EIA-860
   rather than this registry, which is the correct path for an announced exit.
5. **NYISO Danskammer** — did the LHV solutions enter service by 2026-08-01?
   Likeliest source of NYISO's first row.
6. **CAISO OTC** — pass immediately after 2026-12-31; 2.86 GW binds.
7. **Rockport** — only an S.D. Ohio order modifying Paragraph 140 changes the row.
8. **ISO-NE** — restate the instrument bar when the de-list-bid construct is
   replaced by deactivation notification.
