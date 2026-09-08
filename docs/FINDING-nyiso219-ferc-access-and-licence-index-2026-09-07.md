# FINDING nyiso-219 — FERC licence text is **unreachable from this container**. Here is the retrieval index instead, and **one docket covers half the fleet**

**Session:** nyiso-219, NYISO `backcast-calibration` lane. **Date:** 2026-09-07.
**Owner instruction:** *"Go get FERC data"* — the licensed operating ranges that Q1's NID intake
could not serve and that Q2's phase-0 arithmetic is blocked behind.
**ZERO LP.** Keeper `2026-09-07-nyiso-213-summer-seam` untouched; nothing armed, screened, solved
or registered; no `ScenarioConfig` field; no `src/market_sim/` change; no marker moved; no cell
letter changed; no held-out year spent.
**Instrument:** `scripts/probes/nyiso219_ferc_licence_index.py` →
`results/calibration/_nyiso219_ferc_licence_index.{csv,json}`.

---

## 1. The result

**The licence articles could not be fetched, and the deliverable is the index that makes fetching
them cheap.** Every access route was tried and each failure is recorded so nobody repeats it:

| route | outcome |
|---|---|
| `www.ferc.gov` (hydropower licensing pages) | **403** — including with a normal browser `User-Agent` |
| `cms.ferc.gov` (the issued-licences spreadsheet) | **403** |
| `elibrary.ferc.gov` | **reachable**, but a client-rendered Angular app with **no public API** |
| candidate eLibrary REST paths | **false positives.** `eLibrary/api/search` and `eLibrary/api/v1/search` return HTTP 200 — but the body is the SPA's **catch-all `index.html`** (22,464 bytes, confirmed by diffing against the shell). **They are not endpoints.** |
| pre-installed Chromium, driving the SPA | **cannot reach any host** from this container — `example.com` resets identically. Not FERC-specific. |
| the session proxy | **open and healthy** — `selective: false`, no relay failures. **The 403 is FERC's own edge**, not our network. |

Per the environment's standing rule, an organization/edge 403 is **reported, not worked around**.
I did not attempt to defeat FERC's bot protection, and `playwright install` was not run (the
pre-pinned Chromium at `/opt/pw-browsers/chromium-1194` was used instead, and its failure is a
container networking limitation, not a missing browser).

**So the licence articles need a session with working browser egress, or a human with a browser.**

## 2. What IS in hand — and it was already in the repo

ORNL EHA FY2024 carries the **FERC project (docket) number** with licence issue and expiry dates;
the workbook's own Field Descriptions give the source as *"EHA, FERC"*. Joined to everything else
this session measured, that is a complete retrieval index:

| | |
|---|---|
| plants with a FERC docket | **152 of 163** |
| **share of fleet MW covered** | **97.82 %** |
| distinct dockets | **111** |

**The retrieval cost is the headline, and it is small:**

| to cover | distinct dockets to pull |
|---|---:|
| **50 % of fleet MW** | **1** |
| 75 % of fleet MW | **6** |
| 90 % of fleet MW | 30 |

**`P-2216` alone — Robert Moses Niagara — covers 51.89 % of the fleet's MW.** Adding `P-2000`
(St. Lawrence) reaches **71.38 %**. A licence pull that stops after **two documents** already
answers the operating-range question for the plants that dominate every number in this lane.

| plant | MW | % fleet | cum % | **FERC docket** | licence issued | expires | EHA mode | pondage upper bound |
|---|---:|---:|---:|---|---|---|---|---:|
| Robert Moses Niagara | 2,429.1 | 51.89 | 51.89 | **P-2216** | 2007-03-15 | 2057-08-31 | Run-of-river/Peaking | **0.244 h** |
| Robert Moses St. Lawrence | 912.0 | 19.48 | 71.38 | **P-2000** | 2003-10-23 | 2053-09-30 | Peaking | 73.07 h |
| Curtis (+ Palmer) | 59.0 | 1.26 | 72.64 | P-2609 | 2000-04-27 | 2040-04-30 | Intermediate Peaking | 2.02 h |
| Spier Falls | 56.0 | 1.20 | 73.83 | P-2482 | 2002-09-25 | 2042-08-31 | Peaking | 82.80 h |
| Hudson Falls | 44.0 | 0.94 | 74.77 | P-5276 | 1992-12-02 | 2042-11-30 | Run-of-river | 0.16 h |

Full table, all 163 plants, in `_nyiso219_ferc_licence_index.csv`, each row carrying its eLibrary
docket URL alongside nameplate, water source, NID dam ids, storage, head, head basis and the
pondage bound.

## 3. A correction to a number I gave earlier in this session

**I told the owner "99.08 % of fleet MW has a FERC docket". The correct figure is 97.82 %.**

The 99.08 % came from summing MW over **EHA rows**, and EHA lists one row per *powerhouse*, not per
EIA plant — plant 54580 appears twice (Palmer and Curtis), so its 59 MW was counted twice. The
index above aggregates to plant grain first.

**This is the third instance of the same trap in one session**, and it is worth naming as a class
rather than as three separate slips: **an external register keyed at finer grain than the model's
plant, summed without collapsing first.** The other two were NID's `NY00678` (seven structures
repeating one project storage — see `data/raw/nid/README.md` trap 1) and the "78 % vs 84.24 %"
peaking share. Every one of them inflated a coverage or magnitude figure, and every one was caught
by cross-checking against an independently computed number rather than by re-reading the code.

## 4. What this does and does not change

**Does not change:** the pondage conclusion stands untouched — it never depended on FERC. 72.01 %
of scored fleet MW cannot hold one day of its own full output; Robert Moses Niagara holds
**0.244 h** against the LP's **730-hour** budget period. That is measured from NID storage and
stands on its own.

**Does change:** Q2 stays blocked, and now with a named unblock. The charter's Q2 (rule-19 posture,
decided at phase 0) needs a period length; a period length needs the licensed operating range; the
range needs **P-2216 and P-2000**, which are two documents this container cannot fetch but any
browser can.

**A caution I can flag but not resolve here.** Both dominant projects are **international
boundary-water** projects — Niagara under the 1950 Niagara Treaty, the St. Lawrence under the IJC's
Lake Ontario regulation plan — so the instrument that actually binds their water may be a
treaty/IJC order rather than the FERC licence article. `ijc.org` **is** reachable from this
container (HTTP 200) where FERC is not. **I have not verified which instrument governs which
quantity**, and no number from either is asserted anywhere in this session; it is flagged so that a
licence pull does not come back with the wrong document for 71 % of the fleet.

**Rule 21 `[R-DOF]` case 3 is undisturbed:** a period length chosen because it makes a criterion
move remains forbidden. Nothing here chose or swept one.

**No new owner card is opened.** Q1 is discharged with its honest partial result, Q3 is answered,
Q2 remains where the owner put it — at phase 0, now blocked on two named documents rather than on
an open research question.
