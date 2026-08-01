# FINDING — caiso-152: the OASIS RLE parse defect is REAL, FIXED and its effect is MATERIAL — but the corrected input **CANNOT BE SHIPPED**, because the derive fails its own G1 on both arms and **the committed keeper artifact turns out not to be reproducible at all**. NO SOLVE, keeper unchanged

Lever: **not** a mechanism-matrix §5.2 queue item. This is `FINDING-caiso150`
§E1 — filed there, explicitly refused absorption ("the RLE parse defect is the
offer-surface lane's, and is cross-ISO by construction"), and unowned since.
It biases a **LIVE keeper input**, so it was taken as this session's primary
lever.

Pre-registration: `PREREG-caiso152-dam-bid-rle-parse-2026-08-01.md`, committed
and pushed **before any comparison value existed**, plus
`PREREG-caiso152-ADDENDUM-corpus-2026-08-01.md`, committed **before any value
on the widened corpus existed**. Instruments:
`scripts/probes/_caiso152_rle_parse_bias.py` (verify / binshift / density /
curate / derive / compare), outputs `results/calibration/caiso152_*.json|csv`.

Matrix cell `measured_offer_surface` CAISO stays **`K`** — the mechanism is
armed in the keeper and this session neither rejected nor replaced it. What
changed is the standing of its *input*.

---

## §A — the defect, confirmed directly on the raw feed

`scripts/lib/dam_public_bids/caiso.py` keyed every clean row by its range START
stamp and **never read the STOP columns**, while the datatype's own schema
declares the grain as *one row per masked resource × **operating hour** ×
product × breakpoint*. The OASIS disclosure is **run-length-encoded**: a bid
held unchanged across hours is published as ONE row, and a whole-day hold is a
single 24-hour row. Every hour of every multi-hour range was dropped, and the
dropped hours are **exactly the stable-bid ones**.

Measured on the raw CSV, GENERATOR EN curve rows, 2023-01-02: **18,520 raw rows
carry 50,972 real curve-hours — 36.3 % carried**, with **909 rows spanning a
full 24 h**. Over the full corpus (`binshift`, per resource-range with
breakpoints deduped so curves count once each): **8,761,998 ranges carry
18,306,549 curve-hours**, the old parse carried **47.9 %**, 17.3 % of ranges
span more than one hour, and **209,483** rows are 24-hour holds. This
reproduces caiso-150 §E1's 42.8–49.9 % independently.

## §B — the fix, ISO-generic, and verified

A shared `expand_rle(frame, stop_utc)` in `scripts/lib/dam_public_bids/__init__.py`
expands `[start, stop)` to one row per hour **before** `step_idx` is assigned;
`caiso.py` calls it once per row shape with that shape's own STOP column. It
lives in the shared package, not the CAISO module, because every ISO's DAM bid
disclosure is run-length-encoded the same way and CAISO is merely the first
registered spec. Semantics **reuse** the committed caiso-151 expander rather
than re-deriving them: expand to hour slots before any hourly statistic; a null
or non-positive span means "this hour only" and is **never dropped**; the clock
is exact UTC, converted to US/Pacific only downstream, and
`envelopes._caiso_interchange_model_clock` is not applied.

Verified on real data (`verify`): clean GENERATOR EN rows equal the raw
curve-hour count computed independently from the CSV (**50,972 = 50,972**),
**0** duplicate schema keys, hours confined to the trade date. Seven unit tests
cover the expander's edge cases and the curate round-trip. The schema header,
the `interval_start_utc` description and the rendered data dictionary were
corrected to the per-hour grain.

## §C — the ladder's exposure, measured without running the derive

The conditional ladder assigns each resource-hour to a net-load bin **from its
hour**, so under the old parse a multi-hour hold was charged entirely to the
bin of its **range start** — and the OASIS trade day starts at 08:00 UTC, local
midnight. Measured over the full corpus:

**18.0 % of true curve-hours were charged to the wrong net-load bin**, and the
old population systematically under-weights every tight bin:

| net-load bin | old (range starts) | new (curve-hours) | relative under-weight |
|---|---|---|---|
| 0 (loosest) | 0.8501 | 0.8227 | over-weighted +3.3 % |
| 1 | 0.0741 | 0.0872 | **−15.0 %** |
| 2 | 0.0530 | 0.0630 | **−15.9 %** |
| 3 (tightest) | 0.0228 | 0.0270 | **−15.6 %** |

This stands independently of anything the re-derive returns. *(One ex-ante
statement in PREREG §5.2 is corrected here: whole-day holds do not land
exclusively in bin 0 — the bin is a within-year net-load **percentile**, not an
hour of day, so on high-load days local midnight clears bin 0. Measured, 67 %
of 24-hour holds start in bin 0, not ~100 %. The direction of the argument is
unaffected.)*

## §D — the corpus: the caiso-151 balanced sample is the WRONG corpus for this derive

PREREG §3 registered the **358-day seasonally balanced** corpus imported from
the caiso-150/151 intertie lane. It was fetched cleanly (358/358, 119/120/119
per year, 9–10 days per (year, month), **zero holes**) — and **both arms failed
the deriver's own G1 identically** (CT bucket ratio 0.170 vs 0.176). *A defect
that fires the same way with and without the parse fix is not the parse.*

The cause is measured, not assumed (`density`). This derive identifies gas
resources by a **per-resource time-series regression** of the daily body bid on
the citygate daily series (`r ≥ 0.6`, slope ∈ [4, 18] MMBtu/MWh, ≥ 120
resource-days). Classified bucket capacity is strongly monotone in trade-day
count:

| local trade days | resources scored | gas-pass | CC bucket | CT bucket |
|---|---|---|---|---|
| 122 | 257 | 54 | 4,303 MW | 414 MW |
| 179 | 458 | 81 | 5,253 MW | 1,135 MW |
| 358 | 570 | 99 | 7,964 MW | 1,297 MW |

**caiso-150 §B is not contradicted and is not reopened.** The intertie ceiling
is a (month × hour-of-day) **climatology**, which a sparse balanced sample
serves well and a season-biased one wrecks. The offer surface is a per-resource
**daily regression**, which is indifferent to seasonal balance in the way the
climatology is not and sensitive to day *density* in the way it is not. The
corpus was therefore widened to the **full contiguous 2023–2025 span** — what
`fetch_caiso_public_bids.py` produces by default, and what this derive's own
gates presuppose. **1,095 days** fetched (364/366/365; 2023-06-01 is the
documented OASIS archive hole). The widening was registered in the addendum
**before any value on it existed**, is a superset, applies identically to both
arms, and changes no trigger.

## §E — the parse effect: **MATERIAL**, and concentrated entirely in CT_PEAKER

Full corpus, OLD parse vs NEW parse, everything else identical. Population
**29,788,818 → 66,985,503** GENERATOR EN curve rows (680 → 694 resources at
cap ≥ 20 MW). Thresholds are the deriver's **own** frozen `max(0.08, 10 %)`
estimation tolerance, frozen ex ante in PREREG §4.

**T1 — the 6 consumed static band multipliers. FIRES.**

| class | band | old | new | Δ | tol | |
|---|---|---|---|---|---|---|
| CC_REGULAR | econ_low | 1.544 | 1.595 | +0.051 | 0.154 | — |
| CC_REGULAR | econ_high | 1.689 | 1.705 | +0.016 | 0.169 | — |
| CC_REGULAR | peak | 1.710 | 1.709 | −0.001 | 0.171 | — |
| CT_PEAKER | econ_low | 0.745 | 0.681 | −0.064 | 0.080 | — |
| **CT_PEAKER** | **econ_high** | **1.055** | **0.912** | **−0.143** | 0.105 | **FIRES** |
| CT_PEAKER | peak | 1.050 | 1.076 | +0.026 | 0.105 | — |

**T2 — per (class × net-load bin) mean ladder rung. FIRES on ALL FOUR CT bins.**

| class | bin | old | new | Δ | tol | |
|---|---|---|---|---|---|---|
| CC_REGULAR | 0–3 | 3.112 / 3.033 / 3.173 / 3.258 | 3.069 / 2.962 / 3.093 / 3.123 | −0.043 … −0.135 | ~0.31 | — |
| **CT_PEAKER** | **0** | **1.4666** | **1.7776** | **+0.3110** | 0.1467 | **FIRES** |
| **CT_PEAKER** | **1** | **1.4540** | **1.7308** | **+0.2768** | 0.1454 | **FIRES** |
| **CT_PEAKER** | **2** | **1.4724** | **1.7486** | **+0.2762** | 0.1472 | **FIRES** |
| **CT_PEAKER** | **3** | **1.4532** | **1.7576** | **+0.3044** | 0.1453 | **FIRES** |

Two things are worth stating plainly. **CC_REGULAR is unmoved** — every band and
every bin sits inside tolerance, so the median-robustness argument PREREG §5.1
made ex ante holds for CC. **CT_PEAKER is moved hard and uniformly**: the ladder
shifts **+19 to +21 %** in every bin, which is a *level* shift of the CT peak
surface, not a re-shaping of it — the stable-bid hours the old parse discarded
were CT hours, and they price differently from the frequently-rebid ones. The
unarmed `committed` band (rule 19: owned by unit commitment, never a trigger) is
reported for completeness: CC 1.630 → 1.637, CT −0.278 → −0.281.

**No sign is claimed for the eventual λ effect**, and none was registered.

## §F — the blocker: the corrected artifact CANNOT SHIP, and the committed one is NOT REPRODUCIBLE

**Both arms FAIL the deriver's own G1 capacity reconciliation.** CT_PEAKER
bucket ratio **0.235** (old) and **0.280** (new) against a `[0.50, 1.60]` bound;
CC passes at 0.876 / 0.838. The deriver therefore **withholds the consumed
JSONs** — correctly. PREREG §4's third branch governs: **the lane STOPS at the
derive**, the keeper keeps the artifact it has, and **no gate threshold is
retuned to rescue a verdict** (rule 23 `[R-FROZEN-DERIVE]`).

The more serious half is what the OLD arm says. **The OLD arm IS the committed
code path** — the pre-fix parser, the deriver's own default corpus, the
provenance's own CLI settings (`hr_cut` 8.5, `edges` 0.80/0.90/0.97, 5 rungs) —
and it **does not regenerate the committed artifact**:

| | committed (2026-07-19) | OLD arm (this session) |
|---|---|---|
| CC_REGULAR bucket | 13,454 MW, ratio 0.981 | 12,007 MW, ratio 0.876 |
| CT_PEAKER bucket | 10,785 MW, ratio **1.416 PASS** | 1,786 MW, ratio **0.235 FAIL** |
| CC units / CT units | 55 / **102** | 102 / **25** |
| CC_REGULAR econ_low | 1.051 | 1.544 |
| CT_PEAKER econ_high | 1.182 | 1.055 |

So **`caiso_offer_curve_measured.json` and `caiso_offer_surface_condbinned.json`
— a live keeper input, armed in `2026-07-31-caiso-151-firm-selfsched` — cannot
be reproduced from their documented source and script.** The gap is not the
parse (it is present on the pre-fix parser) and not corpus sparsity (the OLD arm
ran on the *full* corpus; density recovers CC, from 7,964 → 12,007 MW, but never
CT, 1,297 → 1,786 MW against a 10,785 MW target). The classified **population**
is different in kind: the committed run found 102 CT units at slope ≥ 8.5, this
one finds 25.

**Two inputs were eliminated as causes.** The citygate daily series is
**byte-identical inside 2023–2025** (the 2026-07-31 back-year append is purely
additive: 680 rows both sides, max |Δ| = 0.0), and the fleet geometry
round-trips exactly (`base_hr` 7.442 / 10.862, `pct_committed` 27.37 / 10.90 —
the committed provenance's own values).

**What cannot be eliminated, and is stated as a limitation rather than a
conclusion:** the repo's git history begins **2026-07-30**, eleven days *after*
the artifact was derived, so the deriver's state at derive time cannot be
diffed. The artifact records no corpus manifest (no day list, no day count, no
row count), so the corpus it used is unknowable. Either way the operative fact
is the same and is not a matter of interpretation: **the artifact is not
reproducible as a matter of record.**

## §G — disposition

- **The parse fix LANDS.** It repairs a violation of the datatype's own declared
  grain, it is ISO-generic, it is unit-tested, and rule 14 `[R-ACCURATE]` keeps
  it regardless of downstream consequences. It is a contract repair, not a
  mechanism, and PREREG §6 registered no reject for it.
- **The parse effect is MATERIAL** — both triggers fire, on CT_PEAKER, at ~2×
  the deriver's own tolerance on all four ladder bins.
- **NO SOLVE WAS SPENT and NOTHING IS REGISTERED** on the dashboard
  (caiso-136/143/144/149/150 pattern). PREREG §9's A/B is not reachable: it
  requires a corrected artifact, and the derive refuses to produce one.
- **Keeper unchanged**: `2026-07-31-caiso-151-firm-selfsched`,
  CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, 2 of 3 ledgered slots,
  protective 0/1. No new field, no flag, no config change.
- **CAISO still holds no rule-22 calibration-complete marker.** No
  out-of-training year was solved, scored or touched, and **no marker was
  written**.
- **A new blocking item is opened and is NOT absorbed here** (§H): the CAISO
  measured offer surface must be re-identified before either half of it can be
  re-derived, because its classifier cannot currently reconstitute the CT
  bucket. That is a charter — a measured re-identification of the gas-coupling
  classifier — not a lever, and it is the prerequisite for shipping the parse
  correction the model demonstrably needs.

**Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` read together here.** The
correct move is *not* to ship a corrected artifact that fails its own
identification gate, and *not* to relax the gate so it passes. It is to keep
the correct parser, leave the keeper's input where it is, and name the root
cause: an armed keeper input whose derive cannot re-identify its own
population.

## §H — DO-NOT-REDO (new, binding)

* **Re-running the parse-bias comparison on a seasonally balanced sample.** §D
  measures why: this derive is a per-resource daily regression and a
  10-days-a-month corpus starves its classifier. Both arms fail G1 there and
  neither number means anything about the parse. The full contiguous span is
  the corpus; `fetch_caiso_public_bids.py` with no arguments regenerates it in
  ~2 h.
* **Relaxing, re-centring or re-scoping G1 — or any of G2–G4 — to make the
  corrected derive writable.** Rule 23 `[R-FROZEN-DERIVE]`: the gates re-run
  only on a source-data change, and a gate retuned to move a verdict is an
  answer key. The CT bucket ratio is 0.235/0.280 against a 0.50 floor; that is
  a 2× miss, not a threshold quibble.
* **Shipping the corrected artifact by any route that bypasses the gate** —
  hand-editing a JSON, blending OLD and NEW values, cherry-picking the CC half
  (which passes G1) and leaving CT on the committed values, or arming
  `caiso_offer_surface_conditional` off a summary CSV. PREREG §6(e) forbids all
  of these by name.
* **Re-deriving the CT band levels against a price residual** to "recover" the
  committed values. The committed CT numbers are not a target to be hit; they
  are an artifact whose provenance §F could not reconstruct.
* **Treating the caiso-150 §H intertie DO-NOT-REDO as reopened.** It is not.
  §D distinguishes the two corpora by estimator type and touches nothing in the
  intertie lane; `caiso_intertie_selfsched_ceiling.csv` was not re-derived, not
  re-measured and not read.
* **Re-litigating caiso-149 §G's refusal of `tranche_startup_amortization` for
  CAISO on the strength of §E's CT movement.** Three independent grounds stand,
  with no reopen condition; a CT ladder that moves +19 % under a *parse
  correction* is not new evidence about fast-start pricing, and the caiso-149
  rule-19 argument rests on the CT econ/peak rows already carrying an
  identified margin — which §F now shows was measured on an unreproducible
  population, a reason for *less* confidence in that surface, not for arming a
  second mechanism on top of it.
* **Quoting any 358-day multiplier as a measurement of CAISO conduct**
  (PREREG addendum §E), or quoting either full-corpus arm's absolute levels as
  the measured CAISO offer surface. Both arms fail G1; only the OLD-vs-NEW
  *difference* is a result, and only §F's reproduction gap is a claim about the
  committed artifact.

Carried forward unchanged: `FINDING-caiso151` §H, `FINDING-caiso150` §H,
`FINDING-caiso149` §G, `FINDING-caiso148` §G, `FINDING-caiso147` §G,
`FINDING-caiso146` §G, `FINDING-caiso144` §G, caiso-143 §I, caiso-142 §H,
caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10.

## §I — carried open items and cross-ISO notes

* **The offer-surface re-identification charter (NEW, blocking, unowned).** The
  CAISO measured offer surface cannot be re-derived until its gas-coupling
  classifier can reconstitute the CT bucket. On the full corpus, 71 resources /
  16,329 MW clear `r ≥ 0.6` but land at slope < 4 MMBtu/MWh — physically too low
  for any thermal unit — which points at the body-price probe
  (`_price_at_frac` at 35 % of a p98-estimated capacity) landing off the SRMC
  body rather than at the classifier's thresholds. That is a measured lead, not
  a diagnosis, and it needs its own session.
* **Cross-ISO by construction.** The expander seam is ISO-generic and CAISO is
  the only registered `dam-public-bids` spec today, so no other ISO's input
  moved (rule 25 `[R-ISO-SCOPE]`). Any ISO added to this datatype inherits the
  correct grain.
* **`_load_bids` memory reduction** (read only the columns the derive uses;
  `trade_date` was loaded and never read). Without it the RLE-expanded 67M-row
  corpus OOMs a 16 GB box. Verified value-neutral: re-running the OLD arm gives
  a **byte-identical** summary CSV and identical G1, static bands, ladder p50
  and row counts. Rule 27 blob verification done after push (773 lines, hash
  match).
* **Two pre-existing test failures**, both reproduced on a clean `origin/main`
  worktree and **not** attributable to this session:
  `test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
  (`regenerate_clean.py` is missing `ira-credit-parameters`) and
  `test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`.
* Unchanged carried items: the caiso-148 Diablo nameplate/uprate basis
  mismatch; `compute_monthly_markup`'s unconditional committed-tranche start
  amortization (six ISOs, owner-scoped charter); CT_CHP's thin CAISO coverage;
  `audit_keepers.py`'s missing E7 staleness check; the caiso-151 §F
  diagnostics-harness plant-set defect; the shared CT heat-rate meter bug.

Next number: caiso-153.
