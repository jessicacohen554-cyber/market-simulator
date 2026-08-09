# CAISO-186 — OWNER SITTING: the two decision packets, the repaired DOF ledger, and a third agenda item

**Status: DECISION PREPARATION. No lever proposed, no mechanism built, no cell re-tested.**

* **Keeper UNCHANGED** — `2026-08-09-caiso-184-c1-lpbasis` (NOT-YET; **C3a the sole
  load-bearing FAIL**, +3.7 / +10.5 / +13.1 %). No promotion, no registration.
* **ZERO LP SOLVED. Zero solver calls.** Every number below comes from bytes already
  committed to the repository, plus one re-run of the existing caiso-141 **network** wall
  probe (that probe is a network probe by design).
* **No `ScenarioConfig` field added; nothing under `src/` modified; no data byte written.**
* `calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED** — owner acts.
  CAISO holds **no `complete`** (withdrawn by the owner 2026-08-06 at caiso-178 — it is
  not "held") and **no `final`**; the spend freeze is **ACTIVE**. **2023 / 2024 / 2025
  only**; no out-of-training year was solved, scored, read or registered.
* **C3a was never targeted.** It is reported and bounded here as a *decision input*.
  Nothing in this session is tuned to it (rule 1 `[R-STRUCT]`, rule 13 `[R-MEASURED]`).

Instruments (committed, no LP, no network except where stated):
`scripts/probes/_caiso186os_ps_intake_bound.py` · `_caiso186os_dof_repair.py` ·
re-run of `scripts/probes/_caiso141_water_source_survey.py` (network).
Records: `results/calibration/_caiso186os_ps_intake_bound.json` ·
`_caiso186os_dof_repair.json`.

---

## §0. Two housekeeping facts to read first

**(1) SESSION-NUMBER COLLISION — this document is not the landed `caiso-186`.** The
dispatched label for this sitting is "CAISO-186", but `caiso-186` was *already spent* on a
different, landed session: `FINDING-caiso186-seasonal-capability-2026-08-09.md` (the
`cc_winter_capability_basis` charter, refused before solve). `caiso-187` is likewise
spent (`FINDING-caiso187-wefor-overlay-2026-08-09.md`). The dispatched filename is kept so
the owner finds this where it was promised; all instruments and records this session writes
carry the distinct `_caiso186os_` prefix (`os` = owner sitting) so nothing collides with
those sessions' artifacts. **The next free CAISO session number is 188.**

**(2) THE AGENDA GREW BY TWO WHILE THIS SITTING WAS BEING PREPARED.** The dispatch brief
was written at caiso-185. Since then two further CAISO sessions landed and **both escalated
to the owner**:

| session | outcome | what it escalates |
|---|---|---|
| **caiso-186** | `cc_winter_capability_basis` **built, exact, REFUSED before solve** by its own `G-NOCONTRA` bar | the incumbent nameplate basis is silently absorbing a *second* mechanism — the full statistical CC forced-outage rate stacked on the CAMPD outage overlay |
| **caiso-187** | premise **INVERTED BY MEASUREMENT**; pre-registered **Branch C** fired: *"no LP, escalate to the owner"* | the CAMPD outage overlay removes **24–35 % of CAISO CC capacity-hours** against a **~10 %** published planned-plus-forced expectation, and is **growing 45 % in two years** |

Neither is in this sitting's scope and neither is re-litigated here. They are flagged
because an owner sitting on CAISO's disposition that ignores caiso-187's measurement would
be sitting on incomplete information: a 24–35 % outage removal against a ~10 % published
expectation is a *supply-side* over-removal, and CAISO's load-bearing failure is a
*price-level over-shoot*. Those two facts point the same way. **This is an observation, not
a lever and not a claim** — nothing here tests it, and it must not be treated as adjudicated.

---

# PACKET (a) — THE WALLED INTAKE: buy or don't buy

**RECOMMENDATION: DO NOT BUY IT AS A C3a PURCHASE.** The bound below is decisive and it
changes the answer the caiso-141 record implied. The intake may still be worth buying *for
its own sake* — see §a.5, which is a different question with a different justification.

## §a.1 The wall, RE-VERIFIED at this head — 5 of 5 UNCHANGED

Re-run this session against **live** endpoints, not assumed:

| source | check | result |
|---|---|---|
| **S1** EIA-930 `PS` fuel category | does CISO file it? | API carries `PS`; **CISO rows = 0** — WALL |
| **S2** CAISO Today's Outlook fuel mix | is hydro gross-of-pumping? | hydro prints **−414 MW** on 2025-10-15; vs 930 `WAT` corr **0.950**, mean abs diff **287 MW** → the **same PS-NET feed** — WALL |
| **S3** Outlook `storage.csv` | any PS trace? | columns are `Total / Stand-alone / Hybrid batteries` — **battery-only** — WALL |
| **S4** CDEC hourly telemetry | Helms + Eastwood instrumented? | **CTG 0 / WSN 0 / SHV 0** hourly sensors. Only the DWR facilities report (SNL 3, ORO 9, TAB 3) — WALL |
| **S5** EIA-930 sub-BA | fuel facet? | facets are `parent`/`subba`, data column `value` — **demand-only** — WALL |

The uninstrumented **Helms + Eastwood** share is **1,252.8 MW = 60.3 %** of the model's
2,077.6 MW PS fleet, and **Helms alone can pump ~900 MW — larger than the entire ~700 MW
model belly-pumping signal under adjudication.** A DWR-only series (824.8 MW, 39.7 %, gappy
through most of 2023, and requiring an AF→MWh derivation with plant-specific head/efficiency
parameters) bounds its own plants and nothing more. *(FINDING-caiso141 §A/§B; instrument
`_caiso141_water_source_survey.py`, re-run 2026-08-09.)*

**What is non-public, precisely:** not "hourly CAISO pumped storage" in the abstract — that
number exists — but **an hourly split of PS net output from conventional hydro at
fleet coverage**. Every public feed either nets PS inside a hydro cell (930 `WAT`, Outlook
hydro), omits PS entirely (Outlook storage, LESR), publishes only monthly nets (EIA-923), or
covers ≤ 39.7 % of the fleet (CDEC/DWR).

## §a.2 The routes that exist, with their verification status stated honestly

Only the first row below was verified by measurement in this session. The rest are
**candidate routes carried forward from FINDING-caiso141 §C option 2 and named as
candidates**, not as priced or confirmed channels. **This session made no vendor,
regulatory or commercial enquiry and none should be inferred.**

| route | what it would deliver | verification status |
|---|---|---|
| **public feeds** (S1–S6) | nothing — all five re-checked negative | **VERIFIED CLOSED**, this session |
| **CAISO settlement-quality meter data (SQMD)** | the exact hourly per-resource split | **NOT VERIFIED.** Named in FINDING-caiso141 §C as existing; it is scheduling-coordinator-confidential under CAISO's tariff. Whether any release instrument exists is **unknown to this session** |
| **PG&E / SCE plant records** | Helms + Eastwood, i.e. the missing 60.3 % | **NOT VERIFIED.** FINDING-caiso141 §C records that the 2025 Helms FERC relicensing docket shows the operator **holds** the data; it does not establish that the docket **publishes** it |
| **CPUC / FERC regulatory route** | a compelled or docketed release | **NOT VERIFIED.** Not surveyed by any committed probe |
| **commercial vendor** | a modelled or metered reconstruction | **NOT VERIFIED**, and note rule 13 `[R-MEASURED]`: a vendor *model* of the split is not a measured input and would not be admissible; only metered data would be |

**Cost in owner terms — NOT PRICED HERE, and deliberately so.** No committed artifact
prices any of these routes and this session invented no figure. What can be stated
structurally is the *shape* of the cost: an owner-level data request or purchase, plus a
confidentiality instrument, plus a curation session to bring the series through
`data/dictionary/` and the `write_clean`/`read_clean` seam, plus the C3a re-solve it would
license. **The reason this is left unpriced is §a.3: the bound decides the question before
the price does.**

## §a.3 THE BOUND — and it does not close C3a

Construction, all four legs from the keeper's own committed hourly sidecars
(`results/calibration/caiso184_c1_lpbasis/hourly/`). Each leg is an **upper bound on the
favourable direction**, so their composition is an upper bound too.

**L0 — the instrument reproduces the scored statistic exactly.** Model load-weighted mean
LMP rebuilt from `system_<y>.parquet` against the committed `avgLMP.rt_lw` benchmark:
**+3.70 / +10.53 / +13.12 %** — the keeper's registered C3a to two decimals. Nothing below
rests on a re-derivation that does not reproduce.

**L1 — what has to move.** The fall in the model's load-weighted mean price needed to reach
the rubric's ±10 % C3a band:

| year | model lw | actual `rt_lw` | C3a | **required fall** |
|---|--:|--:|--:|--:|
| 2023 | 56.176 | 54.17 | +3.70 % | **0.000 $/MWh** (PASS) |
| 2024 | 38.299 | 34.65 | +10.53 % | **0.184 $/MWh** |
| 2025 | 38.936 | 34.42 | +13.12 % | **1.074 $/MWh** |

**L2 — the largest thing the intake could possibly move.** The intake grounds the model's
hourly PS water state and nothing else. FINDING-caiso140 §B measures the Sep–Dec belly water
wedge at **+769 / +803 / +793 MW** and states plainly (FINDING-caiso141 §B) that no
instrument can separate it into *PS over-pumping* vs *conventional-hydro under-allocation* —
that separation **is** the decision the intake would make. Both branches are therefore
bounded and the larger is taken:

* **Branch A — all model PS over-pumping.** The correctable supply is the model's own belly
  pumping; it cannot pump less than zero. Measured on this keeper: **644.4 / 668.5 / 687.8 MW**
  (Sep–Dec, hod 10–15), pumping in 284 / 288 / 292 of 732 belly hours.
* **Branch B — all conventional-hydro under-allocation.** The correctable supply is the whole
  measured wedge: **769 / 803 / 793 MW**.

**L3 — the leg that decides it, and that the existing λ(S) instrument structurally omits.**
FINDING-caiso140 §C's walkdown priced **S MW of added *price-taking* supply** — free energy.
**Pumped storage is never free energy.** SOC is cyclic, so removing X MWh of pumping obliges
removing ≈ ηX MWh of discharge; the model's own implied RTE is **0.800** in all three years.
And the two sides sit at opposite ends of the price distribution:

| year | model λ at PS **charge** | model λ at PS **discharge** | spread |
|---|--:|--:|--:|
| 2023 | 14.62 | 56.23 | **+41.60** |
| 2024 | 1.76 | 38.60 | **+36.84** |
| 2025 | 6.87 | 42.41 | **+35.55** |

The charge-side relief lands on hours priced $1.76–$14.62; the *obliged* discharge-side
removal lands on hours priced $38.60–$56.23 **and pushes them up**, in hours that carry more
load weight. The same argument holds for Branch B with a monthly energy budget instead of a
daily cycle. **So the sign of the net level effect is not guaranteed favourable, and the
walkdown's number is not merely an upper bound — it omits the offsetting term entirely.**

**L4 — how much of the gap is even addressable.** Gap contribution on the rubric's
common `rt_lw` weights (the caiso-131 §2 / caiso-140 §A convention), 2025:

| hour set | contribution | share |
|---|--:|--:|
| total (common-weight reconstruction) | +3.705 | 100 % |
| hours where model PS is **pumping** | +0.823 | 22.2 % |
| Sep–Dec belly (hod 10–15) | +0.840 | 22.7 % |
| **hours with NO model PS activity at all** | **+2.641** | **71.3 %** |

*(2023: +1.224 total, +0.861 pumping, +0.723 no-activity. 2024: +3.164 / +1.090 / +1.676.
The common-weight reconstruction weights both sides by measured system load and therefore
does not equal the scored gap, which weights the model side by model demand — the shares,
not the totals, are the object.)*

**THE COMPOSED BOUND.** Taking the *larger* branch, evaluating the *committed* caiso-140 §C
λ(S) curve — which that finding itself declares an **upper bound**, and which was measured
against a **smaller** C3a-2025 gap (+2.904 $/MWh, vs this keeper's +4.516), so quoting it can
only **overstate** the intake's sufficiency — and ignoring L3's offset entirely:

| year | S (max of both branches) | λ(S) upper bound | required | **verdict** |
|---|--:|--:|--:|---|
| 2023 | 769.0 MW | −0.107 $/MWh | 0.000 | already PASS |
| 2024 | 803.0 MW | −0.114 $/MWh | 0.184 | **DOES NOT CLOSE — 62.1 % of it** |
| 2025 | 793.0 MW | −0.112 $/MWh | 1.074 | **DOES NOT CLOSE — 10.4 % of it** |

## §a.4 The finding, stated plainly

**The intake cannot close C3a, and it is not close.** Under the most favourable branch, the
most favourable curve, and with the energy-neutrality offset omitted, it reaches **62 % of
2024's required move and 10 % of 2025's** — and 71 % of the 2025 gap sits in hours where the
model's PS is not even active. Funding it *in order to close C3a* would buy an answer to a
question that is not the question.

**Note what this does NOT say.** It is not a claim that the intake is wrong, unnecessary, or
inadmissible. FINDING-caiso140 §B's water wedge is real, near-constant across three years,
and currently unadjudicable. Rule 14 `[R-ACCURATE]` favours the measured input over the
model's unrestrained arbitrageur on its own terms.

## §a.5 So: buy it or not?

**Not as a C3a purchase — recommendation NO.** If the owner wants it, the justification has
to be **rule 1 `[R-STRUCT]` structural fidelity**: the model currently runs a 2,078 MW
pumped-storage fleet as "one entirely unrestrained arbitrageur" (caiso-127 §B2) whose belly
behaviour no instrument can convict or exonerate, and grounding it is a fidelity gain
regardless of the residual. That is a legitimate reason to buy. It is a **different** reason,
it should be **recorded as that reason**, and — per rule 1 — **the resulting run must not be
judged on whether C3a improves.** On the arithmetic above it mostly will not.

---

# PACKET (b) — THE RUBRIC QUESTION

**RECOMMENDATION: DO NOT AMEND THE RUBRIC. Stay NOT-YET, and spend CAISO's next effort on
§3's repaired DOF ledger.** Reasoning in §b.4.

## §b.1 What the rubric says, and why

Rubric **v3.1** (owner amendment 2026-08-06) restricted ledgering to **C3c alone**
(`calibration_verdict.LEDGERABLE_CRITERIA = {"price_tail"}`, fail-closed: an entry naming any
other criterion is *ignored* and the FAIL stands). Both caveat budgets collapsed as a
consequence — protective **1 → 0**, non-protective **3 → 1**
(`MAX_PROTECTIVE_CAVEATS = 0`, `MAX_LEDGERED_CAVEATS = 1`).

The rubric's stated ground, verbatim in the code comment at
`scripts/calibration_verdict.py:178–193` and in §2 of the rubric:

> C3c is the one criterion with *no published commercial comparable at all*, so a
> documented, exhaustion-cited bound is the honest reporting form for it. Every other
> criterion is scored against a published comparable, and for those **the band *is* the
> certification claim.** *"C3a mean LMP is the case that forced the amendment: a mean-LMP
> miss beyond ±10 % is a `MODEL MISS`, and ledgering it certified a price level the model
> does not reproduce."*

Two further facts the sitting needs:

* **C3a has no commercial-caveat range.** Since v2.3/v2.4 the target band *is* the commercial
  band (±10 %). Inside → clean `PASS`; beyond → `FAIL`. There is no middle tier to fall into.
  The ±10 % is itself already the *loose* end of the citation ladder: the market monitors'
  own competitive re-simulations sit **0–4 %** (CAISO DMM 2021–24, MISO SOM 2023), the SEM
  regulator's criterion for its official PLEXOS model is ±5 %, and ±10 % was adopted as the
  published-commercial envelope (NYISO's accepted GE MAPS 2021 benchmark, −2 % to −17 %
  zonal).
* **The amendment that forbids this was made ABOUT CAISO, three days ago.** Its recorded
  effect at amendment: *"CAISO `2026-08-06-caiso-175-tac-intake` CALIBRATED-WITH-CAVEATS →
  **NOT-YET** (C3a 2024 +11.7 % / 2025 +14.8 %)"*, and CAISO's `complete` marker and frontier
  claim were withdrawn with it.

## §b.2 What an amendment would cost at every OTHER ISO

Measured this session by running `scripts/calibration_verdict.py` at HEAD against all six
designated keepers (committed artifacts only, no solve):

| ISO | keeper | determination | C3a | other FAILs | C3c |
|---|---|---|---|---|---|
| **CAISO** | `2026-08-09-caiso-184-c1-lpbasis` | **NOT-YET** | **FAIL** +10.5 / +13.1 % | — | ledgered CAVEAT |
| **ERCOT** | `2026-08-09-run181-position-tail` | **NOT-YET** | **FAIL** −32.4 % (2023) | C3b 2023/2024 | ledgered CAVEAT |
| **MISO** | `2026-08-05-miso-132b-cc-committed` | **NOT-YET** | **FAIL** −14.1 % (2025) | — | ledgered CAVEAT |
| **NEISO** | `2026-08-06-neiso-87-control` | CALIBRATED-WITH-CAVEATS | PASS | — | ledgered CAVEAT |
| **NYISO** | `2026-08-08-nyiso-132-cf-arm` | CALIBRATED-WITH-CAVEATS | PASS | — | ledgered CAVEAT |
| **PJM** | `2026-08-04-pjm-152-collapse` | **CALIBRATED** | PASS | — | PASS |

Three consequences, each arithmetic rather than argumentative:

1. **It would not be a CAISO amendment. Three ISOs carry a live C3a FAIL** — and the largest
   is **ERCOT at −32.4 %**, a third of the price level. A rule admitting +13.1 % as a
   documentable limitation admits −32.4 % on the same words unless a magnitude bar is
   invented, and a magnitude bar tuned to sit between CAISO and ERCOT is a fitted parameter
   in the governance layer.
2. **MISO flips on the day of the amendment.** MISO's only failing criterion is C3a
   (−14.1 %, 2025). Widening the ledgerable set reclassifies MISO **NOT-YET →
   CALIBRATED-WITH-CAVEATS** immediately, with no work done and no residual closed.
3. **It is necessarily TWO amendments, not one — and the second one is the expensive one.**
   All three NOT-YET ISOs have **already spent their single ledgerable slot on C3c**. Caveats
   aggregate per criterion, so adding a C3a entry gives 2 against `MAX_LEDGERED_CAVEATS = 1`
   and the run still reads NOT-YET on budget. Making the change *effective* therefore also
   requires raising the budget 1 → 2 — **which doubles the excuse capacity of all six ISOs,
   including the three already declared**, and re-opens exactly the "price caveated
   wholesale" failure mode the v2 budget cut and the v3.1 restriction were both written to
   prevent.

## §b.3 The honest dispositions, laid out neutrally

**(i) Stay NOT-YET indefinitely.** Cost: CAISO stays outside the declared set with no date;
the `complete`/`final` ladder stays shut; the 2022 touchpoint and the never-granted
2019/H1-2026 locked test stay unreachable. Benefit: the rubric keeps meaning what it says,
and CAISO's published state stays true — the model over-prices CAISO's mean by 10.5 % and
13.1 % and does not claim otherwise. **This is not "doing nothing":** §3 identifies real,
rule-grounded, non-lever work that is currently blocked only by the ledger being wrong about
its own state.

**(ii) Declare on a narrowed criterion.** i.e. certify CAISO for the uses that do not consume
the absolute price level (class mix C1, family mix C2, price *shape* C3b, dispatch timing
C4) with C3a explicitly **excluded from the claim** rather than *excused* inside it. Cost:
the determination is monolithic today, so this is also a rubric amendment — but a **narrower
and more honest one** than (iii), because it changes *what is claimed* rather than *what may
be excused*, it needs no budget increase, and it inherits to other ISOs as a *scoping*
facility rather than as excuse capacity. Risk, and it is real: a scoped certificate is only
as good as the discipline that keeps downstream users inside the scope, and this program has
no mechanism today for enforcing that.

**(iii) Amend so C3a is ledgerable.** Cost: §b.2 — three ISOs inherit it, MISO flips for
free, it needs a second amendment doubling every ISO's excuse budget, and it reverses an
amendment made about this exact criterion at this exact ISO three days earlier. It is also
the disposition this packet was chartered to guard against, and the guard was right.

**(iv) Fund the walled intake.** Refuted by packet (a): 62 % of 2024's required move, 10 %
of 2025's, before the energy-neutrality offset.

## §b.4 Recommendation, and why it survives third-party review

**Take (i): stay NOT-YET, and redirect CAISO's next session onto §3's repaired ledger.**

The reasoning a reviewer would check, in the order they would check it:

1. **The band is not the problem — the price level is.** ±10 % is already the loosest rung
   on a citation ladder whose tight end is the market monitors' own 0–4 %. A model 13 %
   above actual is not near-passing under a strict rule; it is missing under a generous one.
2. **The rule was written about this case.** v3.1's own comment names C3a-at-CAISO as the
   forcing case. Reversing it now, for the same criterion at the same ISO, on no new
   evidence about the criterion, would read to any reviewer as the band moving to meet the
   model — the thing rule 1 exists to forbid.
3. **The exhaustion claim that would justify a model-class ledger entry is not available for
   C3a.** The `ACCEPTED MODEL-CLASS LIMITATION` kind requires a cited exhaustion record. The
   CAISO in-model *mechanism* queue is empty — but §3 shows the **DOF ledger is not**, and
   that two live fitted limbs sit on the binding path, one of them **exactly where
   FINDING-caiso140 §C measures C3a's residual to be pinned**. An exhaustion claim made over
   an unclosed, mis-stated DOF would not survive review, and rightly.
4. **There is real work left that is not a lever.** That is the whole of §3, and it is a
   rule-20/rule-24 obligation independent of whether it moves C3a.

**Second choice if (i) is unacceptable: (ii), never (iii).** (ii) narrows the claim; (iii)
widens the excuse. Those are not the same act and should not be traded for one another.

---

# §3. THE DOF LEDGER REPAIR

`ASSESSMENT-caiso171-frontier-2026-08-04.md` §3 measured CAISO at **4 ISO-specific residual
DOF entries — the most of any ISO** (NEISO 0, PJM 1, NYISO 2), *"two superseded on the
binding path and one resting on a closure route that does not check out."* That census is a
**2026-08-04 measurement on the caiso-170-era keeper** and has been quoted forward — including
into this session's own dispatch brief — as if current. **Re-derived at HEAD, three of its
four claims have moved.** Instrument `_caiso186os_dof_repair.py`; record
`_caiso186os_dof_repair.json`.

## §3.1 R1 — the census, recomputed at HEAD on today's six keepers

Same `CORE_RESIDUAL` partition as caiso-171's F2, so the comparison is like-for-like:

| ISO | entries | residual | core | **ISO-specific** | marker | the ISO-specific rows |
|---|--:|--:|--:|--:|---|---|
| **CAISO** | 11 | 8 | 5 | **3** | NO | `battery_dispatch_adder`, `WECC_import_simultaneous.cap_mw`, `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` |
| **ERCOT** | 14 | 6 | 3 | **3** | NO | `wefor_residual`, `battery_dispatch_adder`, `CHP_BTM_PCT_BY_SECTOR['merchant']` |
| MISO | 29 | 2 | 2 | 0 | NO | — |
| NEISO | 14 | 5 | 5 | 0 | yes | — |
| NYISO | 36 | 6 | 4 | 2 | yes | `NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']`, `IMPORT_TRANCHES/EXPORT_TRANCHES[NYISO]` |
| PJM | 19 | 6 | 5 | 1 | yes | `wefor_residual` |

**Two corrections to the standing narrative, both retirements of a stale number:**

* **CAISO is at 3, not 4.** `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` — caiso-171's *"the one that
  matters, and its stated closure route does not check out"* — was **CLOSED at caiso-172**
  and now carries `identification: "measured"`: the PG&E TAC load split across Path 15 is
  derived by `scripts/data/derive_caiso_path15_load_split.py` from two published OASIS Atlas
  reports (`ATL_LDF` per-pnode load distribution factors inside `DLAP_PGAE-APND`, 1,668
  pnodes summing to exactly 100.000, joined by substation to `ATL_PNODE_MAP`'s authoritative
  `TH_NP15_GEN` / `TH_ZP26_GEN` membership), day-weighted over every live effective window;
  per-year ZP26 0.11644 / 0.11554 / 0.11600, backcast mean **0.116049**, superseding the
  0.86/0.14 estimate that put 17 % too much PG&E load in ZP26. **Retire the "4".**
* **CAISO is no longer "the most of any ISO".** **ERCOT also carries 3.** caiso-171's table
  did not include ERCOT; the claim was true of the five ISOs it measured and is not true of
  the six. **Retire "the most of any ISO measured"** — CAISO is *tied for the most*.

## §3.2 R2 — the surviving three, re-derived against the keeper's own wiring

Read from `results/calibration/caiso184_c1_lpbasis/run_config.json`, not assumed:
`capacity_deliverability_limits=True`, `caiso_per_hub_intertie=True`,
`caiso_perhub_firm_base=True`, `caiso_per_year_import_caps=True`,
`caiso_firm_import_selfschedule=True`, **`caiso_firm_import_selfsched_clip=True`**,
`caiso_import_hub_prices=False`, `caiso_bidir_intertie=False`,
`battery_dispatch_adder=5.0`, `pumped_storage_dispatch_adder=None`.

### ROW 1 — `WECC_import_simultaneous.cap_mw = 7500.0` · **the ledger text CHECKS OUT. RE-STATE, do not retire.**

`capacity_deliverability_limits` is **True** on the keeper, so the published branch-group MIC
seam limit (16,055 / 16,452 / 16,148 MW) replaces the fitted 7,500, and caiso-157 measured it
binding in **0 / 0 / 0 hours**. Genuinely superseded on the backcast binding path.

**Repaired statement:** this is **not** a backcast residual and should not be counted as one.
It is a **forecast-path residual**: `capacity_deliverability_limits` is GATED default-**off**,
so the fitted 7,500 still caps forecast-mode imports (issue #1373, O-1 forecast/backcast
parity). Identification source: none — it is a fitted scalar, and the code's own block
comment says so and says *"do not re-tune this value to the residual."* **Stays OPEN as a
forecast-parity root-cause item.**

### ROW 2 — `battery_dispatch_adder = 5.0` · **LIVE; the ledger's closure route is SPENT; new bounding evidence is missing from the ledger.**

The ledger's `root_cause` names the forward-valid replacement as *"the measured AS power
reservation (`storage_as_commitment`) + an ATB-derived degradation cost."* **Both halves are
spent:**

| half | adjudication |
|---|---|
| measured AS power reservation | `caiso_storage_as_reservation` probe-adjudicated **INERT** (caiso-74); the whole AS-award family then refuted by arithmetic (caiso-127/129) |
| ATB-derived degradation cost | built at $14.25/MWh, A/B-solved, **REJECTED** on caiso-100's pre-registered two-sided ±15 % throughput guard (caiso-100/101). On today's committed constants the same formula returns **$22.63** (capex 285 → 452.6 $/kWh) — **further** in the rejected direction, so refused *a fortiori* |

**Repaired statement.** The ledger's `root_cause` points at a closed route and is **STALE**.
It also omits identification evidence that now exists: caiso-176 read CAISO's **own** Daily
Energy Storage Report `bid_stack` — committed since 2026-07-11, recorded in its own README as
*"retained but not curated"* — and bounded the fleet's discharge reservation price at
**≤ $15/MWh in all three years**. That is a **model-free upper bound** that independently
corroborates the caiso-101 rejection and admits the incumbent $5.00.

**It BOUNDS but does not IDENTIFY: every value in (0, 15] survives.** Under rule 20
`[R-DOF]` the row therefore **stays residual and stays an OPEN ROOT-CAUSE ISSUE** — it must
never be closed by choosing a value inside the bound, because a value chosen inside a bound
is a tuned value. **Ledger action: replace the stale `root_cause` route with the caiso-176
bound + the two spent halves.** No value changes.

### ROW 3 — `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` · **THE LEDGER TEXT DOES NOT CHECK OUT. This is where the "closure route that does not check out" label has moved.**

The committed text reads: *"CAISO's keeper supersedes the fitted ladder with measured hub
prices on the binding path but the static ladder remains the fallback."* **That is true of
one of the row's four limbs.** `inject_caiso_per_hub_intertie_prices` writes `mc[row, :]` and
**nothing else** — it repriced no capacity — and its `firm_base` branch **explicitly skips**
`CAISO_FIRM_IMPORT_TRANCHES` (`continue  # firm/contracted block … keeps its static ladder
price`), which the keeper arms (`caiso_perhub_firm_base=True`).

Split into limbs (R3):

| limb | tranches | identification | status on the keeper's binding path |
|---|---|---|---|
| **firm capacity** | `PNW_hydro_base`, `DSW_solar_PV` | **MEASURED**, per-year | **CLOSED** — DMM Annual Report system RA capacity "Imports" row (2,323 / 3,371 MW; 2025 carries 2024, an **open data gap** until the DMM 2025 annual report lands) × published Maximum Import Capability per branch group |
| **spot price** | `PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity` | superseded | **CLOSED on the backcast path** — repriced hour-by-hour to the measured Malin / Palo Verde hub + OATT wheel + CARB adder. *Two disclosed conditions:* the injector returns `False` and leaves static placeholders when no measured hub series exists for the year (e.g. the 2023 OASIS gap), and the **forecast path has no measured hub series at all** |
| **firm price** | `PNW_hydro_base` $28.0, `DSW_solar_PV` $48.0 | **RESIDUAL** — labelled `STATIC-FITTED-PENDING-MEASURED` in the spec itself (audit C-6 / issue #1350), identical in all three years | **LIVE** — see below |
| **spot capacity** | `PNW_midC` 1800, `DSW_CCGT` 1800, `DSW_CT` 2200, `WECC_scarcity` 3000 MW | **RESIDUAL** — no primary source cited in the provenance block; the by-year comment states plainly that *"only the two firm-block capacities vary by year. Spot tranches and all prices are identical to the static ladder"*, and FINDING-caiso82 §3 names these four MW **verbatim** as the registered G-26 / issue #1350 / audit C-6 gap | **LIVE AND BINDING** — see below |

**Why the firm PRICES are live, and why the argument that retired them no longer holds.**
caiso-77 retired them on a specific ground, still in the code docstring: with
`caiso_firm_import_selfschedule` setting `pmin = pmax`, *"the tranche can never set the
margin, so its ladder $/MWh becomes pure inframarginal contract-cost bookkeeping — the two
G-26 static-fitted-pending-measured firm prices stop influencing dispatch."* **That argument
no longer holds in full.** caiso-151's `caiso_firm_import_selfsched_clip` — **armed on this
keeper** — caps the *floor* (not the capability) at CAISO's measured price-insensitive
intertie ceiling, and the docstring says what happens above it: *"above the measured
price-insensitive ceiling the import is still available, it is simply price-ELASTIC, so it
must be offered to the LP as economic capability rather than forced."* Offered **at exactly
these two static prices**. FINDING-caiso150 §C/§F measures the un-floored volume at
**0.969 / 4.634 / 5.705 TWh in 23.9 / 47.2 / 48.9 % of hours** (2023/24/25), *"growing with
the DMM RA level."* **A correct mechanism fix silently re-armed a fitted price.** Nobody did
anything wrong — the interaction was simply never re-checked against the ledger.

**Why the spot CAPACITIES are the limb that matters most.** The hub-price injector never
touches a capacity, and nothing else does either: these four depths total **8,800 MW** of
economic import supply with **no cited primary source**. FINDING-caiso140 §C measures the
Sep–Dec belly λ as **PINNED by a 2.7–3.0 GW economic-import plateau** on which **51–61 % of
defect hours never move**, with economic (non-firm) import in those hours at **mean 2,705 MW
/ p50 3,038 MW**. **That plateau is this depth ladder.** A fitted, uncited scalar sitting
exactly where the load-bearing criterion's residual is pinned is the single most consequential
unclosed DOF CAISO carries — and the ledger currently describes the row it lives in as
"superseded."

## §3.3 The repaired CAISO ledger, as it should read

| row | count as | live fitted scalars on the **backcast binding path** | disposition |
|---|---|--:|---|
| `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` | **RETIRED from the residual census** | 0 | **CLOSED — measured** (caiso-172) |
| `WECC_import_simultaneous.cap_mw` | **forecast-path residual**, not backcast | 0 | OPEN — forecast/backcast parity, issue #1373 |
| `battery_dispatch_adder` | ISO-specific residual | **1** | OPEN root-cause. Bounded ≤ $15/MWh (caiso-176), **not identified**. `root_cause` text needs replacing |
| `IMPORT_TRANCHES[CAISO]` — firm capacity | closed | 0 | CLOSED — measured, per-year (DMM RA × published MIC) |
| `IMPORT_TRANCHES[CAISO]` — spot price | closed on backcast | 0 | CLOSED on backcast; **live on forecast** (no measured hub series forward) |
| `IMPORT_TRANCHES[CAISO]` — **firm price** | **ISO-specific residual (was mis-stated as superseded)** | **2** | OPEN root-cause — re-armed onto the margin by `caiso_firm_import_selfsched_clip`; 0.97 / 4.63 / 5.71 TWh/yr exposure |
| `IMPORT_TRANCHES[CAISO]` — **spot capacity** | **ISO-specific residual (was mis-stated as superseded)** | **4** | OPEN root-cause — 8,800 MW uncited depth, co-located with C3a's pinned residual |

**Headline: the row count falls 4 → 3, but the live fitted-scalar count on the backcast
binding path is 7, not the ~1 the ledger currently implies.** The census got better and the
substance got worse, and both halves of that belong in front of the owner.

## §3.4 What this licenses, and what it does NOT

**It does not license a lever, and this session builds nothing.** No `ScenarioConfig` field,
no derive, no solve, no cell verdict.

What it does establish is that CAISO has **non-lever work that is a standing obligation
under rules 20 `[R-DOF]` and 24 `[R-REGISTRY]`**, independent of C3a: two ledger rows that
describe their own state incorrectly.

**The prior art must be stated accurately, because it constrains what is left.** Audit C-6 /
issue #1350 was closed for four ISOs by measured Q–Q seam derivations
(`derive_neiso_import_tranches.py`, `derive_nyiso_import_tranches.py`,
`derive_miso_seam_ladders.py`, `derive_pjm_seam_ladders.py`). **CAISO got a deriver too** —
`scripts/data/derive_caiso_import_tranches.py`, the caiso-83 lane — but it derives **PRICES
only**, its own docstring saying *"only the PRICES are re-derived here"*, and **it was run and
it FAILED its pre-registered honesty gates**: the full ladder failed year-stability on
`DSW_solar_PV` (CV 0.99, caiso-86), and the four-rung `--partial` form then failed **LOYO**
(worst held-out rung error **30.5 %** against a 25 % bar, caiso-86b), as did its gas-indexed
implied-heat-rate variant. **The measured-ladder-PRICE lane is CLOSED and must not be
re-opened without new evidence** (rule 28 DO-NOT-REDO). That closure covers the firm prices
too — `PNW_hydro_base` was one of the four rungs that failed.

So the two live limbs stand in **different** positions and the sitting should not conflate
them:

* **spot capacity — never attempted, and explicitly filed as the open gap.**
  FINDING-caiso82 §3 says so verbatim: *"The spot tranche capacities (1800/1800/2200/3000 MW)
  are the registered G-26 / issue #1350 / audit C-6 gap: STATIC-FITTED-PENDING-MEASURED, with
  the MISO_SEAM_LADDER_BY_YEAR / NEISO measured Q-Q derivations named as the closure
  pattern."* Its supporting evidence — measured south-corridor depth-in-surplus p95
  **4.7 / 5.4 / 5.5 GW**, year-stable — is banked as *stability* evidence, **not** as the
  derivation, and no derive script has ever produced these four numbers. **This is the open
  route.**
* **firm price — a closure route was tried and failed on an honesty gate.** It stays open as
  a root-cause issue with **no currently-viable named replacement**, which is exactly what
  rule 20 says such a residual is. It must not be closed by picking a value.

**Two guardrails on how that work must be framed, and they are not optional:**

1. **It is rule 14 `[R-ACCURATE]` work, not a C3a lever.** The justification is that a fitted,
   uncited 8,800 MW depth ladder and two fitted contract prices should be measured because
   measured is better. **Whether it moves C3a is unknown and must not be the reason to do
   it.** If it makes C3a worse, rule 14 is explicit: the accurate input stays and the worse
   fit is a discovered bug (rule 1 `[R-STRUCT]` — a real behaviour stays in even if it makes
   the fit worse).
2. **It is not a re-test of an adjudicated cell.** No matrix cell covers the *provenance of
   the CAISO import depth ladder*; the DO-NOT-REDO list is a mechanism list. Closing a DOF by
   replacing a fitted input with a measured one is not a mechanism test and does not touch
   the empty lever queue — the queue stays empty and this session did not add to it.

---

# §4. THIRD AGENDA ITEM — FFR-4E **E-2**, the `caiso_storage_nqc_accreditation` arming decision

**This is an OWNER ARMING DECISION, put here so it is on the same agenda. It is NOT armed by
this session, and FFR-4E's refused capacity-price anchor is NOT re-opened.**

**What is decided.** `ScenarioConfig.caiso_storage_nqc_accreditation` is **built, measured,
and ships default-OFF**. It carries CAISO's **own published** battery accreditation as a
whole-class ratio on a nameplate basis:
`STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"] = 13,365 / 15,448.4 = 0.865138`.
Rule 14 `[R-ACCURATE]` favours the ISO's published accreditation over the generic duration
curve. The construction was chosen and pre-registered *before* the row-4 read, on three
stated grounds: CAISO publishes **no** storage duration table (the CY2026 NQC report's
`2026 Tech Factors` tab has no battery row — batteries are accredited at demonstrated
capability); the published ratio is NQC/NDC while the model's multiplicand is nameplate; and
a whole-class ratio **replaces** `_elcc_for_duration` rather than stacking on it (rule 19
`[R-ONE-MECH]`).

**What arming costs — stated, not minimised.** Arming **MOVES THE DESIGNATED BACKCAST
KEEPER** (FFR-4E §4.2, measured on the keeper's own recipe and measured fleet):

| year | fleet MW | `storage_firm_mw` at HEAD | **gate ON** | **Δ** |
|---|--:|--:|--:|--:|
| 2023 | 9,570.0 | 5,963.668 | 8,414.1 | **+2,450.5 MW** |
| 2024 | 13,208.9 | 8,003.698 | 11,562.3 | **+3,558.6 MW** |
| 2025 | 17,526.0 | 10,318.168 | 15,297.2 | **+4,979.0 MW** |

So arming requires a **CAISO keeper re-solve and re-gate under rules 15 and 16** — a control
+ treated pair, **2023 + 2024 + 2025 in one bundle per arm**, years sequential and arms
sequential (rule 12), both registered on the backcast dashboard with
`legitimacy_diagnostics.json` generated so C8 stays scored, and every pre-registered gate
re-run. That is **its own session in the CAISO lane**, exactly as its VRE sibling
`caiso_nqc_accreditation` was (owner decision D.1). It is not a flag flip.

**Gate-off inertness is proved, so there is no deadline pressure.** G-INERT passes *exactly*
— gate-off equals the pre-FFR-4E value in all three keeper years, **not "within tolerance",
equal** — pinned by
`tests/unit/model/test_storage_whole_class_accreditation.py::KeeperInertnessTest`. The field
is registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`, the pinned default cache key
**`603c2498bf71d21d` is unmoved**, and there is **no cache epoch**: no cached bundle in any
ISO is orphaned. The owner can take this decision whenever, at zero carrying cost.

**Explicitly out of scope, and staying out.** **E-1** — FFR-4E's finding that FC-2 row 4's
residual is an **entry-economics** object (economic thermal entry is a single invariant
2,000 MW block and storage entry is 0.0 MW across the whole horizon, in **both** arms;
adequacy is met administratively regardless of the accreditation ledger) — is a **separate
future charter on its own rule-14 merits**. The **capacity-price anchor route is
owner-declined under D-15** and is neither read, quoted, nor re-opened here, and no row-4
improvement via that route is claimed.

---

# §5. THE SITTING AGENDA, IN ONE PLACE

| # | decision | this session's recommendation | the number that decides it |
|---|---|---|---|
| **1** | Fund the walled hourly PS water-state intake? | **NO as a C3a purchase.** YES only if justified on rule-1 structural fidelity, with C3a explicitly **not** the acceptance test | upper bound covers **62.1 %** of 2024's required move and **10.4 %** of 2025's — before the energy-neutrality offset, which may reverse the sign |
| **2** | May CAISO be declared `CALIBRATED-WITH-CAVEATS` on a **C3a** ledger entry? | **NO — do not amend.** Stay NOT-YET and spend the next session on §3. Second choice (ii) narrowed claim; never (iii) | it would take **two** amendments (`LEDGERABLE_CRITERIA` **and** the budget 1 → 2), inherit to **ERCOT −32.4 %** and **MISO −14.1 %**, flip MISO for free, and reverse a 3-day-old amendment made about this exact criterion at this exact ISO |
| **3** | Arm `caiso_storage_nqc_accreditation`? | **Owner's call — no session recommendation.** Not armed here | arming moves the keeper **+2,450.5 / +3,558.6 / +4,979.0 MW** and costs a full A/B re-solve + re-gate; gate-off is **exactly** inert, so there is no cost to deferring |
| **4** | *(for information)* the repaired DOF ledger | census **4 → 3** rows; but **7** live fitted scalars on the backcast binding path, where the ledger implies ~1. Two rows describe their own state incorrectly | `battery_dispatch_adder` 1 · firm prices 2 (0.97 / 4.63 / 5.71 TWh/yr re-armed by the clip) · spot capacities 4 (**8,800 MW uncited**, co-located with C3a's pinned 2.7–3.0 GW plateau) |
| **5** | *(for information)* caiso-186 and caiso-187 both escalated | not in scope; flagged so the sitting is not held on stale information | caiso-187: the outage overlay removes **24–35 %** of CC capacity-hours vs a **~10 %** published expectation, **growing 45 % in two years** |

---

# §6. WHAT CHANGED ON THE RECORD

* **Keeper unchanged.** No promotion, no registration, no bundle. Rule 15 does not fire —
  nothing was solved.
* **DOF ledger unchanged in the committed attestation** (`n_entries` 11 / `n_residual` 8).
  This document specifies the repair; **writing it into a keeper attestation requires a
  bundle**, so it lands with the next CAISO run that produces one. The two `root_cause`
  rewrites (`battery_dispatch_adder`, `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`) are the
  concrete edits, and both are text-only — **no value moves**.
* **Matrix (rule 28): NO CELL VERDICT MOVES.** No mechanism was proposed, tested or
  adjudicated; no `ScenarioConfig` field was added; duty (b) does not fire. §5.2 carries a
  session block recording this sitting.
* **Two stale numbers RETIRED, both from `ASSESSMENT-caiso171-frontier` §3, and neither
  should be re-quoted:** CAISO's ISO-specific residual DOF count is **3, not 4**, and CAISO
  is **tied with ERCOT**, not *"the most of any ISO measured"*.
* **Rule 22:** 2023–2025 only. No out-of-training year solved, scored, registered or read.
  Both markers untouched; the freeze is untouched and remains ACTIVE.
