# FINDING — ERCOT-160 (2026-08-04): the ERCOT item-7/item-8 data intakes

**Lane:** cross-ISO backcast calibration, ERCOT lever queue
(`docs/mechanism-testing-matrix.md` §5.1), items **7** and **8**.
**Type:** DATA INTAKE. **No LP solve, no ScenarioConfig field, no mechanism
tested, no matrix cell verdict, no dashboard run, keeper UNCHANGED**
(`2026-08-03-ercot158-pool-arm`). The ERCOT-142/143/145/146/147 precedent: a
session that builds no mechanism mints no cell.

**Queue precedence, stated because it selected this work.** The prompt's item 1
(MISO C7 COAL_PRB) is gated on the miso-104 ex-ante coal-contract tonnage ask
having landed. **It has not** — `docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`
carries a single commit (its original upload) and no commit has touched
`data/raw/` with contract tonnage since. Per the DO-NOT-REDO discipline the
receipts-derived construction (miso-103, cell `R`) was **not** re-attempted.
Precedence therefore fell to ERCOT items 7/8, data-intake first.

---

## 1. Headline

| Item | Part | Verdict |
|---|---|---|
| 8 | (a) CT-scoped full-span 60-Day SCED, 2023–2025 | **EXECUTED** — 2 gaps, both stated below |
| 8 | (b) Texas hub daily gas basis (Waha + HSC/Katy) | **BLOCKED** — licensed source only; owner decision |
| 8 | (c) CT resource→plant crosswalk | **RESHAPED, not built** — the task is smaller and differently shaped than the charter assumed; its ERCOT-side spine is now in-repo |
| 7 | station→area crosswalk prerequisite | **EXECUTED** — ERCOT publishes it; it was simply never fetched |

The one-line result: **item 7's stated blocker is dissolved, item 8(a) is
delivered at 98.7 % of the training span, item 8(b) is the only genuinely
blocked half, and item 8(c) turns out to be an *adjudication* task rather than
the ~150-site identification task the charter sized.**

---

## 2. Item 8(a) — the CT-scoped full-span SCED intake

ERCOT-147 §4 part (1) asked for full-span (all days, all hours) Gen Resource
Data for 2023–2025 restricted to SCLE90/SCGT90, so the CT daily conduct object
could be measured rather than sampled on 82 selected days.

**What was in the way.** `scripts/data/fetch_ercot_60day_sced_gen_resource.py`
could only take an explicit `--delivery-days` list, kept every resource
(~90 MB of CSV per day), and concatenated the whole window before writing —
which is not representable for a ~700-day span. Three additions fixed that,
all scope/plumbing, no derivation:

* `--resource-types SCLE90 SCGT90` — measured on a live day, CTs are **18,816
  of 124,608 rows (15.1 %)**, **0.51 MB** of Parquet against ~90 MB of
  unscoped CSV. This is what makes the span affordable at all.
* `--delivery-range START END` — full-span enumeration.
* `--shard-by-month` / `--skip-existing` — one Parquet per delivery month, so
  resident memory stays at one month and an interrupted span resumes.

The rule-22 holdout guard was **not** relaxed and still binds the new range
path: verified live that `--delivery-range 2025-12-30 2026-01-02` refuses on
the two 2026 delivery days rather than fetching them.

### 2.0 Two ERCOT publication quirks, found by the fetch failing loudly

The first full-span attempt **died on delivery 2024-08-05**, and the failure was
correct: two assumptions the fetcher had always carried are false. Both are
recorded here because any future NP3-965 consumer will hit them.

1. **The member filename is the PUBLICATION stamp, not the delivery day.**
   `60d_SCED_Gen_Resource_Data-04-OCT-24.csv`, inside the 2024-10-04
   publication, carries `SCED Time Stamp` values of `08/05/2024` — delivery =
   publication − 60. Naming an output from the member's own filename would
   **mislabel every day by 60 days**, silently. Delivery day is now read from
   the file's own stamps, with the nominal lag used only as a cheap skip test
   and verified against content before anything is written.
2. **A publication day can carry more than one document, and a document more
   than one delivery day.** 2024-10-04 has *both* the ordinary ~10 MB daily
   document *and* a ~245 MB `Supplemental_60_Day_SCED_Disclosure` holding **32
   members**. The old "most recent document published that day wins" rule
   picked the supplemental and then died on its member count. Supplementals
   are now detected by name, exempted from the nominal-lag skip, and every
   member read for its true delivery days.

**Consequence for method:** the span is scanned by **publication**, not by
delivery day — a delivery-driven loop structurally cannot find a day whose
document does not sit at the nominal lag. Output is **one Parquet per delivery
day**, so a day that never turns up anywhere is visible as a *missing file*
rather than silently absent from inside a month shard, and the run prints the
not-found days grouped into contiguous runs. `fetch_days()`'s original
single-member contract is untouched, so the earlier day-list intakes are
unaffected.

Holdout hygiene was re-verified on the new path: a span whose end is past
`--max-delivery-date` is refused, and a harvested member is kept only if its
delivery day is inside the requested range — so a supplemental bundle spilling
into a quarantined year cannot smuggle a day in.

### 2.1 Coverage, and the two gaps

| Span | Source | Grain |
|---|---|---|
| delivery 2022-12-31 … 2024-01-09 | `data/raw/ercot/SCED/` (ERCOT-157 owner re-upload, 315 shards) | all resources, all hours |
| delivery 2024-01-24 … 2025-12-31 | `data/raw/ercot/SCED-CT/` (this session) | CT only, all hours |

**Combined: 1,081 of the 1,095 training days (98.7 %).**

* **Gap 1 — delivery 2024-01-10 … 2024-01-23 (14 days), UNREACHABLE.** The MIS
  rolling window's earliest listed publication is 2024-03-24 (measured
  2026-08-04) → earliest reachable delivery 2024-01-24, which lands 14 days
  after the committed corpus ends. The fetcher reported all 14 as `NOT LISTED`;
  none was fabricated or interpolated. Closing it needs the credentialed
  `data.ercot.com` archive, which is **owner-declined**
  (`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E). **This gap grows over
  time** — the window rolls forward, so a later re-run recovers fewer early-2024
  days, never more.
* **Gap 2 — delivery ≥ 2026-01-01 not fetched, by design.** The MIS window
  reaches ~2026-06-04, but H1-2026 is the locked-test tier and the holdout
  spend freeze is active (rule 22). Refused by the guard, not by omission.

Storage: the shards are **gitignored** with a committed README + `SHA256SUMS.txt`
(the `data/raw/pjm-zonal-lmp/` precedent) — ~360 MB is past what the push path
carries and the command that regenerates them is in the README verbatim.

---

## 3. Item 8(b) — the Texas hub daily gas basis: BLOCKED

ERCOT-147 §4 part (2) explicitly said "licensing must be checked before
promising it". Checked on both free paths the repo already reads, and recorded
as a reproducible probe (`scripts/probes/ercot160_texas_hub_daily_screen.py`,
record `results/calibration/ercot160_texas_hub_screen.json`) so it is not
re-litigated from memory.

**EIA's Natural Gas Weekly Update spot table** — the page the four committed
citygate scrapers use. On a real archive page (2025-07-17):

| Hub | Mentions anywhere on the page |
|---|---|
| Henry Hub | 10 |
| New York | 10 |
| Chicago | 6 |
| Cal. comp | 6 |
| Algonquin | 3 |
| **Waha** | **0** |
| **Katy** | **0** |
| **Agua Dulce** | **0** |
| **Carthage** | **0** |
| Houston Ship | 1 |
| Permian | 1 |

A daily table row cannot be present at **zero** mentions — Chicago, which *is*
a row, scores 6. The single "Houston Ship" and "Permian" hits are narrative
petrochemical prose quoting a **weekly average** ethane-to-gas premium, not a
daily print. This re-measures what `docs/data-licensing.md` §5 already states
the table's columns to be.

**ERCOT's own MIS product catalog** — 5,773 products; 6 mention fuel; **none is
a price series**. They are FFSS award notification, FFSS deployment/recall, RMR
fuel-supply option selection, the Fuel Mix dashboard, the 7-Day Event Trigger
posting, and the Exceptional Fuel Cost submission report. ERCOT's settlement
Fuel Index Price is **not** posted as a data product.

**Verdict: BLOCKED — the series exists only behind NGI / Platts / Argus.** That
is an owner licensing decision, and it is compounded by the still-unresolved
`docs/data-licensing.md` §5 finding on the NGI-sourced series the repo already
carries. Logged as blocked. **Not** inferred as zero, and **not** substituted
with Henry Hub — ERCOT-147 §3's whole point is that 63–67 % of CT capacity's
daily p50 sits below its own sheet-HR × HH burn, so a Henry Hub stand-in would
assume away the exact confound the intake exists to resolve.

**Consequence for the lever, stated plainly.** ERCOT-147 §4 says "only with
(1)+(2) on disk can a future lane even TEST whether a stable conduct object
exists". (1) is now on disk; (2) is not. **The CT-band re-identification stays
blocked**, and this session does not claim otherwise.

---

## 4. Item 7 — the station→area crosswalk: the blocker was never real

Item 7 records that a station→area crosswalk "does not exist in-repo". True —
but ERCOT **publishes** one, free and unauthenticated, and it had simply never
been fetched: **NP4-160-SG "Settlement Points List and Electrical Buses
Mapping"** (`reportTypeId=10008`), found in ERCOT's own product catalog.

Intaken to `data/raw/ercot-network-model/` (1.2 MB, **committed**, members
written as exact published bytes with a sha256 each — ERCOT ToU §5 permits
redistribution only if contents are unmodified):

* `Settlement_Points_*.csv` (19,287 rows) — `ELECTRICAL_BUS`, `SUBSTATION`,
  `SETTLEMENT_LOAD_ZONE`, `RESOURCE_NODE`, `HUB`, `VOLTAGE_LEVEL`,
  `PSSE_BUS_NAME/NUMBER`. **This is the station→area crosswalk.**
* `Resource_Node_to_Unit_*.csv` (1,624 rows) — `RESOURCE_NODE` →
  `UNIT_SUBSTATION` + `UNIT_NAME`, the generator-side spine.
* plus `NOIE_Mapping`, `CCP_Resource_Names`, `Hub_Name_AND_DC_Ties`.

**Vintage limit, which constrains what may be concluded.** MIS retention is
~31 days (3 versions listed), so only the **current** network-model version
(published 2026-07-29) is ever reachable — there is no 2023/2024/2025 vintage
to fetch and there never will be on this path. That is exactly why it is
**committed rather than gitignored**: an un-committed vintage is lost
permanently. Substation→zone assignments are structural and slow-moving, but a
resource node commissioned or retired between a backcast year and this vintage
will not line up, so **any consumer must report its own match rate against its
target year** rather than inherit the numbers below.

---

## 5. Item 8(c) — the CT crosswalk is a different job than the charter assumed

`scripts/probes/ercot160_ct_target_population.py` censuses every CT resource in
the corpus and joins it to `data/raw/reference/ercot-dam-plant-crosswalk.csv`.
No model, no LP, no derivation, no free parameter, no threshold.

**A grain error, corrected.** The crosswalk's `site` column is **not one
grain**. For `CC_REGULAR` it holds a site prefix (`RIONOG`, settlement point
`RIONOG_CC1`); for `CT_PEAKER` it holds the **full resource name**
(`VICTPORT_CTG01`). Measured: **165/165 CT rows match a corpus RESOURCE name,
0/165 match a site prefix.** So ERCOT-146 §3 / ERCOT-147 §3's "165 CT_PEAKER
sites, 6 accepted" counts **resources**, and the "~150-site hand crosswalk"
sizing is wrong in kind.

**What the census actually finds** (final numbers in
`results/calibration/ercot160_ct_population.json`; see §5.1):

* the corpus publishes far fewer CT **sites** than the resource count suggests;
* the large majority of CT resources — and of CT capacity — **already have a
  candidate crosswalk row**; only 6 are accepted;
* a minority have **no row at all** (`corpus_resources_absent_from_crosswalk`),
  and these are visibly industrial-cogen heavy (DOWGEN, FORMOSA), which is a
  target-population question in its own right, not a matching failure.

**So the remaining work splits two ways, and only the smaller half is
identification:** adjudicating existing candidate rows (accept / reject), and
freshly identifying the handful with no row. Both now stand on a published
spine — §4's mapping resolves resource → substation → load zone — leaving
**substation → EIA plant code** as the one genuine judgement step. NP4-160-SG
carries no EIA identifier and cannot be made to.

This session **did not build the crosswalk**. Building it would be work whose
only consumer — the CT-band re-identification — remains blocked on §3, and
ERCOT-147 §3 already recorded that the crosswalk is "buildable but pointless
while §2 stands". What this session did is make the job correctly sized and
correctly shaped for whoever charters it.

### 5.1 Census numbers (full corpus)

See `results/calibration/ercot160_ct_population.json` / `.csv` — regenerated
against the completed full-span corpus, so the counts there supersede any
intermediate figure quoted during the session.

---

## 6. What did NOT happen (guard rails)

* **No LP solve.** No dashboard registration (rule 15 attaches to a completed
  run; none was produced). No bundle, no scoring.
* **No matrix cell verdict** (rule 28(b) attaches to a tested mechanism; none
  was tested). No new `ScenarioConfig` field, so rule 28(c) does not fire.
  The §5.1 lever-queue entries for items 7 and 8 are re-stamped.
* **No holdout touched.** Every fetched delivery day is in 2023–2025; the two
  2026 days a naive range would have taken were refused by the guard, live.
* **Keeper unchanged**, DOF ledger unchanged, gate verdicts unchanged.
* **No estimate substituted for a blocked measurement** (rule 14): §3 is logged
  BLOCKED, not filled with Henry Hub.

---

## 7. Successors

1. **Item 8(b) is an owner licensing decision** — NGI / Platts / Argus for
   Waha + HSC/Katy daily, on top of the unresolved §5 finding for the NGI
   series already in-repo. Until it lands, the CT-band re-identification stays
   blocked and the fitted CT_PEAKER multipliers remain attributed DOF.
2. **Gap 1 (14 days) is owner-declined-archive territory** and it widens with
   time; nothing in-session can close it.
3. **Item 7 is now unblocked on data** and can proceed to its actual object,
   the ERCOT-121 under-curtailment gap, against a published station→area
   mapping — carrying §4's vintage caveat.
4. **Item 8(c), if chartered**, is an adjudication of existing candidate rows
   plus a small fresh-identification tail, on §4's spine, with substation →
   EIA plant code as the only judgement step.
