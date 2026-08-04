# XISO-4 — queue ratchet, D-5(b) re-key verification, and the two data asks

**Session:** xiso-4, 2026-08-04. **No LP was solved. No mechanism was armed,
tested, proposed or chartered. No keeper moved. No dashboard run was
registered** (rule 15 has nothing to register: a session that spends no solve
produces no run).

**Headline: the backcast lever queue is exhausted, and both standing data asks
stay blocked — one of them now on a sharper, better-evidenced boundary than
before.** §1 and §2 came back clean after repair; §3 produced two real source
assessments, neither of which clears. Three owner decisions and two data asks
gate every remaining backcast route. Nothing here manufactures an arm.

---

## 0. State verified at this session's own head

`origin/main` was `b45fc4e2` at dispatch and `a7966013` when this session
started; it moved to `f53fff65` mid-session and this work is rebased onto that.
Everything below was re-read at head, not taken from the dispatch prompt.

| ISO | keeper shard (verified at head) | determination, **re-derived this session** |
|---|---|---|
| ERCOT | `2026-08-03-ercot158-pool-arm` | **NOT-YET** — `price_mean`, `price_shape`, `price_tail`, `shape` FAIL |
| CAISO | `2026-08-04-caiso164-zonal-loss-surface` | **CALIBRATED-WITH-CAVEATS** — `price_mean`, `price_tail` CAVEAT |
| PJM | `2026-08-03-pjm-151-seam-envelope` | **CALIBRATED** — zero FAIL, zero CAVEAT |
| MISO | `2026-08-04-miso-124-dualfuel-rearm` | **NOT-YET** — `shape` FAIL; `price_mean`/`price_tail` CAVEAT |
| NYISO | `2026-08-04-nyiso-120-c119-scope` | **NOT-YET** — `price_mean` FAIL, `price_tail` CAVEAT |
| NEISO | `2026-08-03-neiso-caiso156-meter-screen` | **CALIBRATED-WITH-CAVEATS** — `price_tail` CAVEAT, `shape` SKIPPED |

Every determination above was reproduced with
`scripts/calibration_verdict.py --run-id <id>` reading **committed artifacts
only** — no solve, no LP, no bundle regeneration. They are not copied from prose.

* `scripts/audit_keepers.py` — **PASS, 0 failures / 0 warnings** at head, so it
  did not displace the scoped work.
* Markers: `complete` = {NEISO, NYISO, PJM}; **`final` is EMPTY**, verified in
  `calibration-complete.json`. NEISO's `locked_test` reads *SPENT, NOT
  RE-GRANTABLE*.
* **Holdout freeze active** (`holdout-freeze.json`, 2026-07-25) and outranks
  every marker. Nothing in this session touched an out-of-training year in any
  mode; all six determinations above are 2023–2025 in-sample.
* **No in-flight branch on this charter id.** `origin/claude/xiso-4-queue-ratchet-iay292`
  existed but sat at `origin/main` with zero commits — checked *before* starting,
  per the concurrent-FFR-3P trap.

---

## 1. Rule-28 header ratchet — REPAIRED (committed)

The dispatch flagged §5.4. **Four of six headers had drifted**, and the §5.5
defect was structural rather than a stale string.

| § | found at head | repaired to |
|---|---|---|
| 5.1 ERCOT | `2026-08-03-ercot158-pool-arm` | already correct, untouched |
| 5.2 CAISO | `2026-08-04-caiso164-zonal-loss-surface` | already correct, untouched |
| 5.3 PJM | `2026-08-03-pjm-147b-chp-heat` — stale | `2026-08-03-pjm-151-seam-envelope` |
| 5.4 MISO | **no live keeper stamp at all**; its only id was the historical `miso-122b` mention, which read as current | live stamp added: `2026-08-04-miso-124-dualfuel-rearm`, NOT-YET |
| 5.5 NYISO | `2026-08-03-nyiso-119-seny-increment` **and** determination `CALIBRATED-WITH-CAVEATS` — both superseded | `2026-08-04-nyiso-120-c119-scope`, **NOT-YET** |
| 5.5 NYISO | **three duplicate `### 5.5` section headers** | two removed, one kept |
| 5.6 NEISO | `2026-08-03-neiso-caiso156-meter-screen` | already correct, untouched |

Two findings worth carrying forward:

**(a) The NYISO drift was a determination error, not just an id error.** The
header asserted CALIBRATED-WITH-CAVEATS while the designated keeper had moved to
**NOT-YET** at nyiso-120 (C3a mean LMP fails 2025 at −10.1 % against ±10 %). A
reader taking the matrix at face value would have read NYISO as passing. The
marker file was already correct; only the prose lied.

**(b) The three duplicate §5.5 headers were merge-race artifacts.** Every other
§5.x section carries exactly one header; NYISO had accumulated three, because
sessions prepended a *new header + STATUS block* instead of re-stamping the one
header. They were byte-identical apart from their keeper clauses, and the STATUS
block immediately below each already records the same keeper transition, so
removing the two lower ones loses no information. (One of them even carried the
note "header keeper id corrected at nyiso-116" — a previous session tried to fix
this and left a duplicate behind instead.)

`MECH_MATRIX.keepers` in `docs/codebase-site/data/mechanism-matrix.js` was
**correct on all six** and was not touched.

### 1a. The guard was widened — stated, not silent

`check_mechanism_matrix.py` validated `MECH_MATRIX.keepers` but **not** the prose
headers. That asymmetry is exactly why this drifted with CI green throughout.
This session added `doc_header_drift()`, which asserts two things per ISO:

1. the §5.x prose header names that ISO's designated keeper id, and
2. there is exactly one §5.x header per ISO (the duplicate-header check).

It is **deliberately weak**: it does not police wording, determination text or
ordering — it catches staleness without dictating prose. Escalation mirrors the
existing keeper-drift discipline exactly: a PR that moves a keeper shard owns
that ISO's prose header (**error**); drift it did not create only **warns**, so
unrelated lanes are not tripped. Both legs were negative-tested (a re-staled PJM
id and an injected duplicate header are each caught; the clean tree passes).

**This is a widening of a CI gate and should be reviewed as one.** It is
reported here rather than left to be discovered.

*Note, not fixed:* 221 pre-existing **anchor** warnings (absolute `scenarios.py`
line numbers) are stale at head from other lanes' edits. They are warnings, exit
0, and by the guard's own design belong to whoever last moved `scenarios.py` —
repairing them here would be scope creep and pure churn.

---

## 2. Rule-22 D-5(b) re-key verification — CLEAN, and independently re-verified

For each ISO holding a `complete` marker, the `keeper` field was checked against
the live shard **and** the recorded `determination` was re-derived by actually
running `scripts/calibration_verdict.py --run-id` on committed artifacts. It was
not merely read out of the file.

| ISO | marker `keeper` | matches shard | recorded determination | re-derived | verdict |
|---|---|---|---|---|---|
| NEISO | `2026-08-03-neiso-caiso156-meter-screen` | ✅ | CALIBRATED-WITH-CAVEATS (re-verified 2026-08-03) | CALIBRATED-WITH-CAVEATS | ✅ match |
| NYISO | `2026-08-04-nyiso-120-c119-scope` | ✅ | NOT-YET (re-verified 2026-08-04) | NOT-YET | ✅ match |
| PJM | `2026-08-03-pjm-151-seam-envelope` | ✅ | CALIBRATED (re-verified 2026-08-03) | CALIBRATED | ✅ match |

`final` is empty; NEISO's spent one-shot config (`locked_test_scored_on`) is
untouched and was not re-keyed, which is correct. **No determination was
rewritten by this session** — nothing was worse, so nothing escalated. §2 is
recorded as checked and clean.

---

## 3. The two data asks — both discharged, neither clears

Both are explicitly no-solve. Nothing was written under `data/raw/`; every
document was read in a scratch directory, the same assessment-not-intake posture
miso-104 used (ask §5: "miso-104 intook nothing"). **No rule-22 intake occurred,
so no owner authorization was required and none is claimed.**

### 3(a) MISO coal-contract tonnage ask §8 — the Form 580 count is NOT PRODUCIBLE from this environment

The ask's bounded next step is a **count**, not a solve: pull the 2024 Form 580
filings (CY2022–2023) for the 26 target owners from FERC eLibrary docket
**IN79-6** and answer three questions (who filed, who answered Q6, and what
share of 2023 target tonnage sits in single-destination-plant contracts).

**The count could not be produced.** Three retrieval routes were tested; all
close. Two of these are new information relative to miso-104/105.

1. **eLibrary has no machine surface — reconfirmed independently.** Every
   `/eLibrary/*` path returns the same 22,464-byte SPA shell (`/eLibrary/api/search`,
   `/eLibrary/filelist`, `/eLibrary/docketsheet?docket=IN79-6`, and the legacy
   `idmws/search/fercgensearch.asp`); everything else 404s. I fetched all four
   JS bundles at their current hashes and grepped them: the **only** `/api/`
   base is `"/api/v2/"` inside the Datadog RUM SDK (`ddforward`, `datadoghq`).
   miso-104's claim is correct and now re-verified against the *current* bundles.
2. **NEW — the headless-browser fallback the ask names is unavailable here.**
   Ask §8 says the count "needs either a headless-browser session against the
   search UI or an authorized alternative source." Chromium + Playwright are
   installed, but Chromium **cannot traverse this environment's agent proxy at
   all**: `example.com` fails with `ERR_CONNECTION_RESET` identically to
   `elibrary.ferc.gov`, with and without `--proxy-server`/`proxy=`, and the proxy
   logs a `non-CONNECT request` from the browser. This is not a FERC block — it
   is a browser-egress limitation of the session environment. **The ask's own
   escape hatch does not work here.**
3. **NEW — FERC's structured open-data catalog does not carry Form 580.**
   `data.ferc.gov` (a real catalog + developer API, and a surface miso-104/105
   never probed — they only hit `elibrary.ferc.gov`) publishes Forms 1, 552 and
   556 and the Market-Based Rate database. Searching the Electric catalog for
   "580" returns **zero** hits. So there is no bulk/API alternative to eLibrary
   for this form. `www.ferc.gov` is additionally 403 (bot-blocked) from here.

**Status: unchanged (still blocked), but the boundary is now sharper.** It is no
longer "we have not tried the browser" — it is *eLibrary exposes no API, FERC's
open-data catalog does not carry Form 580, and the browser fallback is
environment-blocked.* Retrieval requires either a session with working browser
egress or a human/authorized eLibrary retrieval.

**The decisive point for the owner, which is independent of the count.** The
2026 Form 580 (CY2024–2025) is **due 2026-10-30**. Today is 2026-08-04. So the
CY2024 and CY2025 contract data *does not yet exist*, and the ask **cannot**
clear §2C's "≥15 plants and ≥60 % of tonnage in EACH of 2023/2024/2025" before
late 2026 — **whatever the count says**. Per ask §8, the count decides only
*which kind* of blocked the lane is (timing-blocked vs data-blocked). That makes
the owner decision concrete:

> **Owner decision A.** Spend a human/authorized eLibrary retrieval *now* to
> learn whether the lane is timing-blocked or data-blocked, or simply wait for
> the 2026 form (due 2026-10-30) and run the count once against the full
> 2023–2025 span? Waiting costs nothing that is recoverable today.

**No charter was written.** Ask §4 permits a charter only on a source that
clears §4.1 *and* the §4.2 pin-strength battery; nothing cleared, so per the
dispatch's standing constraint nothing was chartered. Per §6, C7 stays failing
and unledgered. **No receipts variant was re-tested** (miso-103's DO-NOT-REDO
respected).

Target-set denominators were re-derived from committed artifacts for the record
(`miso104_contract_source_coverage.py`, no network, no LP): **39 plants, 26
owners**, 93.99 / 80.67 / 89.52 Mt in 2023 / 2024 / 2025.

### 3(b) MISO outage-grain ask — assessed, and the "single best candidate" is now CLOSED

**This is defect-motivated, not gate-motivated, and that is not a softening.**
C3b (`price_shape`) **PASSES** on the current MISO keeper — re-derived this
session, not asserted. MISO's sole FAIL is C7 (`shape`). So this ask does not
gate MISO's determination; it targets a real ~10 GW summer-peak derate defect and
the undeclared `SUMMER_WEFOR_SHARE = 0.30` DOF. Nobody should read it as gate
work.

**Candidate 2 (Potomac Economics MISO SOM) — ASSESSED AND CLOSED on §2B.** The
ask called this "the single best candidate… if a fuel × month series exists it
clears A–D directly." I pulled the **2025 MISO SOM** (152-page body, published
2026-07) and its **Analytic Appendix** (157 pages) and read the outage content:

* **Figure 25** (body): generation outages, **2023–2025**, by **subregion** ×
  outage type.
* **Figure A71** (appendix): monthly average planned and unplanned outage rates,
  2024–2025 plus 3-year annual averages, split *normal planned / short-notice
  planned / short-term unplanned / long-term unplanned*; full outages only, and
  explicitly **excludes partial outages and deratings**.
* **Figures A154–A156**: real-time deratings and forced outages, 2025, by
  **region** (Central / South / North).

Scored against §2: it clears **A** (ticket-based, not output-derived), **C**
(monthly, year-specific, 2023–2025) and **E** (planned vs forced separated). It
**fails B**: there is **no fuel-class resolution of outages anywhere** in either
document. The grain is region × cause × month — *precisely the grain the model
already holds* from the MOM report, and precisely the grain miso-85 and miso-87
already proved cannot be pushed onto units without inventing the attribution.

> **The ask's best candidate does not clear, and it fails on the one criterion
> the ask exists for.** Per ask §3 this closes candidate 2. Do not re-open it,
> and do not re-attempt an attribution rule on it (miso-85/87).

**Candidate 3 (RA / accreditation) — partially visible, does not clear.** SOM
Figure 34 / A119 publishes **UCAP by fuel type × Local Resource Zone**, from the
2025–26 PRA summer and winter seasons; UCAP "account[s] for forced outages and
intermittency." That clears **A, B, D**. It fails **C** and **E**: it is a
two-season *planning* accreditation built on a historical lookback — a rolling
class average, which §2C's own note says "would satisfy B and D but **fail C and
would move nothing**" — and it combines forced outage with intermittency rather
than isolating the forced component (fails E). The SOM also renders only
UCAP/ICAP **shares** in an inset table, not the underlying MW series. Direct
MISO PRA postings could not be checked: `misoenergy.org` and `cdn.misoenergy.org`
both return **403** from this environment (`docs.misoenergy.org` works, which is
why the already-intaken MOM reports are reachable and the PRA results are not).

**Candidate 1 (NERC GADS) — UNRESOLVED, explicitly not refuted.** `nerc.com`
serves the GADS Reports page and the public product family is *Generating Unit
Statistical Brochures*, but the brochure links are JS-rendered and did not
resolve from this environment (same browser-egress limitation as §3(a)). The
ask's own prior — that these are multi-year rolling class averages and therefore
fail C — is **untested**, and I am not recording it as refuted.

**Candidate 4 (MISO data request)** is a stakeholder process, not a fetch;
unchanged.

> **Owner decision B.** Candidate 2 is closed and candidate 3 fails C/E as
> published. The remaining routes are a **MISO data request** (§3 candidate 4 —
> the one path that can be *specified* to meet §2 rather than hoping an existing
> product happens to) or an authorized retrieval environment for candidate 1.
> Which, if either, should be opened?

---

## 4. Why no lever was tested (rule 28, DO-NOT-REDO)

Re-checked at head; the dispatch's reading holds. Every per-ISO queue in
`docs/mechanism-testing-matrix.md` §5 is blocked:

* **ERCOT §5.1** — the only NOT-YET ISO and the highest-value target, but its
  live queue is item 9 (**UNCHARTERED**, owner authorization required) plus items
  7 and 8 (data-intake first). Per the dispatch I **asked rather than chartered**,
  and did **not** substitute a different ERCOT lever to avoid asking (see §5).
* **MISO §5.4** — C7 COAL_PRB is the sole failing criterion and is
  non-ledgerable (budget saturated at 3/3). Both routes dead: receipts variants
  ruled inadmissible at miso-103, no ex-ante contractual series at plant grain
  (miso-104), and §3(a) above does not change that.
* **CAISO §5.2 / PJM §5.3** — no failing criterion; CAISO's caveats are
  data-blocked, PJM's `state_carbon_pricing` sits at `O` PENDING OWNER.
* **NYISO §5.5** — route-exhausted at nyiso-110, pending the owner amplitude call.
* **NEISO §5.6** — C3c frontier declared, its one lever refuted at neiso-76.

**No cell marked `R`/`I`/`G` was re-tested, and no new evidence was claimed
against one.** No matrix cell status changed this session, because **no mechanism
was tested** — the only matrix edits are the §1 header stamps. Rule 28(b) has
nothing to record; rule 28(c) has nothing to register (no `ScenarioConfig` field
added).

---

## 5. The three owner decisions and two data asks that gate every remaining route

This is the finding. The backcast lever queue is exhausted of buildable in-model
levers; what remains is gated on decisions and data, not on engineering.

**Owner decisions (open):**

1. **ERCOT item 9** — UNCHARTERED successor to the ERCOT-158 commitment-state
   finding, and the highest-value non-blocked backcast target (ERCOT is the only
   NOT-YET ISO with an un-adjudicated named successor). **Requires owner
   authorization to charter.** Not chartered here.
2. **PJM `state_carbon_pricing`** — solved at pjm-146, cell `O`, PENDING OWNER.
3. **NYISO amplitude criterion** — the peak-half distribution route is
   exhausted at nyiso-110; the lane waits on the owner's amplitude-criterion call.

Also standing and untouched: **G.5** and **D-9** remain open owner decisions
(not pre-empted); **D.1** (HOLD PROMOTION, FIND ROOT CAUSE) stands; **D-1/D-2**
stay ARMED; the **D-8** mechanisms stay default-off; **FH-4/FH-5** stay BLOCKED;
the **holdout freeze** stays active.

**Data asks (both blocked, per §3):**

4. **MISO coal-contract tonnage** — decision A above (retrieve now vs wait for
   the 2026 Form 580, due 2026-10-30). Cannot clear §2C before late 2026
   regardless.
5. **MISO outage grain** — decision B above (MISO data request vs authorized
   retrieval environment for NERC GADS). Candidate 2 now closed.

**Cross-cutting environment blocker, new this session:** browser egress does not
work in this session type. It blocks the Form 580 count *and* the NERC GADS
brochure assessment. Any session chartered to discharge either needs an
environment where a headless browser can reach the public internet — worth
knowing before one is scheduled, rather than after.

---

## 6. What this session did NOT do

* No LP solved; no bundle produced; no dashboard registration (rule 15 has no
  run to register).
* No parameter moved, no band widened, no damper unarmed, nothing tuned in
  response to any score (rules 1/11/14).
* No mechanism chartered, proposed or armed; no matrix cell verdict changed.
* No out-of-training year touched in any mode; no marker spent; freeze respected.
* No data intaken; nothing written under `data/raw/`.
* No keeper promoted; no determination rewritten.
