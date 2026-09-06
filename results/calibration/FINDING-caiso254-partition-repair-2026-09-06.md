# FINDING — caiso-254: the CT bucket **is** contaminated, the partition separates it cleanly, and the derive's OWN physical-sanity gate then **REFUSES** the result. **G-BIMODAL PASSES; G4 FAILS on the separated ST_GAS bucket (peak 1.196 inverted 0.350 BELOW econ_high 1.546); NOTHING IS WRITTEN, NOTHING IS ARMED, KEEPER UNCHANGED.** 6 of 7 predictions hold — including P-2 reproducing the frozen artifact *exactly* — and the seventh was never reached because no LP was spent. Two structural findings the session did not go looking for: the pooled CT bucket's 30 % capacity excess **collapses to 3 %** when the high-HR mode is separated, and the ST_GAS half of the repair is **provably inert in the LP** whatever its bands say.

**Session caiso-254, 2026-09-06.** Branch
`claude/caiso-253b-backcast-calibration-3i1wj1`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) **UNCHANGED**, DETERMINATION **CALIBRATED**. Pre-registration:
`PRECOMMIT-caiso253b-offer-surface-contamination-2026-09-06.md` (merged, PR
#4927) + `ADDENDUM-caiso254-partition-repair-screen-2026-09-06.md`, the latter
pushed **before G-BIMODAL was scored**. Rule 22 `[R-HOLDOUT]`: 2023–2025 only;
no `complete`/`final` marker; freeze ACTIVE. **ZERO LP SPENT.**

---

## §1 — THE REGISTERED GATES, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| **P-1** | corpus re-fetches to 1,095 / 1,096, `2023-06-01` the one genuine OASIS hole | 1,095 / 1,096, missing exactly `20230601` ("NO DATA in the OASIS archive") | **HOLDS** |
| **P-2** | frozen buckets reproduce to ±3 resources and ±5 % capacity (46 CC / 100 CT) | `CC_REGULAR` **46 / 11,935 MW**, `CT_PEAKER` **100 / 9,950 MW** — **EXACT on all four legs** | **HOLDS** |
| **P-3** | **G-BIMODAL**: antimode ∈ [10.9, 12.5] with 1.5–4.5 GW above | antimode **11.738**, **2.559 GW** above | **PASS** |
| **P-4** | de-contaminated `CT_PEAKER.econ_low` falls into [1.03, 1.12] from 1.145 | **1.103** | **HOLDS** |
| **P-5** | a separated `ST_GAS.econ_low` RISES above 1.145 | **1.563** | **HOLDS** (but see §3 — it cannot reach the LP) |
| **P-6** | the CC bucket is materially unchanged (±0.01 on all three bands) | **1.066 / 1.072 / 1.386 — identical to the digit** | **HOLDS** |
| **P-7** | net first-order price effect under ±$1.0/MWh, sign not predicted | — | **NOT REACHED** (no solve; §4) |

**6 hold, 0 falsified, 1 never reached.** P-2's exactness is also the verdict on
this session's instrument correction (§5.1): the three divergences found by code
inspection were the entire gap.

---

## §2 — WHAT THE PARTITION DOES, AND THE GATE THAT REFUSES IT

The measured second cut lands at **11.738 MMBtu/MWh** — located as the CT-side
capacity-density antimode inside the window fixed from published fleet heat
rates, exactly the way `hr_cut = 8.5` was located in its own valley.

### §2.1 — G1: the contamination is confirmed on CAPACITY, independently of any price

| bucket | pooled (frozen) | separated | own fleet | ratio before → after |
|---|--:|--:|--:|---|
| `CC_REGULAR` | 11,935 MW | 11,935 MW | 13,708 | 0.871 → **0.871** (untouched) |
| `CT_PEAKER` | 9,950 MW | **7,391 MW** | 7,616 | **1.306 → 0.970** |
| `ST_GAS` | *(absorbed into CT)* | **2,559 MW** | 2,859 | — → **0.895** |

The frozen artifact's own provenance flags that 1.306 excess and names the
steamers as the suspect. Separating at the measured antimode collapses a **30 %
excess to 3 %**, and the separated mode reconciles against the 2,859 MW steamer
fleet at 0.895. **This is the strongest evidence the object produced, and it
contains no price at all.**

### §2.2 — The bands, and G4's refusal

| class | committed | econ_low | econ_high | peak | G4 |
|---|--:|--:|--:|--:|---|
| `CC_REGULAR` | 1.030 | 1.066 | 1.072 | 1.386 | PASS |
| `CT_PEAKER` | 1.162 | **1.103** | **1.146** | **1.154** | PASS |
| `ST_GAS` | 1.367 | **1.563** | 1.546 | **1.196** | **FAIL** |

G1 PASSES for all three; **G2 cut-robustness PASSES** with *both* cuts perturbed
at the unchanged ±0.25; G3 LOYO is computed; **G4 physical sanity FAILS on
`ST_GAS`**: its `peak` (1.196) sits **0.350 BELOW** its `econ_high` (1.546),
against a 0.05 flatness tolerance. That is an **inverted offer curve** — the
top-of-curve capacity measured cheaper than the middle — which is precisely what
G4 exists to catch.

**⇒ The derive REFUSED to write the consumed JSONs. Nothing is armed. The frozen
2026-08-02 artifact stands, verified in place after the run.**

Also disclosed by the run itself: `ST_GAS.committed` has **no sample at all in
2024 and 2025** (its window is 6.6 % of capacity). That band is unarmed, so it
is reported null rather than fabricated — see §5.3.

---

## §3 — THE STRUCTURAL FINDING: the ST_GAS half is PROVABLY INERT IN THE LP

Traced **before** any solve. `data/offer_curves._offer_curve_for_group` opens
with an unconditional bypass:

```python
if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
    return None
```

and **CAISO's entire ST_GAS fleet is that set** — plants 315 (AES Alamitos,
1,142.0 MW), 335 (AES Huntington Beach, 225.8 MW), 350 (Ormond Beach,
1,491.0 MW) = 2,858.8 MW, the whole class in `bin_assignments_CAISO.csv`.
Measured, not read: with the `ST_GAS` band set to an unmissable **99.0**, all
three plants return `None`; a control class on the same config returns its curve.

So an `ST_GAS` entry in `caiso_offer_curve_measured.json` **reaches zero CAISO
plants**. Consequences, stated so they cannot be quietly widened later:

* the ST_GAS leg is a correctness fix **in the artifact** — it stops
  `_ungrounded` asserting ST_GAS is priced off the CT bucket, which was the
  false statement the parent PRECOMMIT §1 objected to — and is **inert in the
  model**. Those plants' committed and peak bands already come from the
  caiso-239 / caiso-240 **per-plant measured registries** through this same
  bypass: rule 19 `[R-ONE-MECH]` working as designed;
* **P-5 is therefore artifact-only** and must never be quoted as a dispatch
  effect, however large 1.145 → 1.563 looks;
* the **CT_PEAKER de-contamination is the entire model-visible effect**, and it
  is the half that passes G4.

**Had this surfaced after a solve** it would have read as "the repair didn't
move ST_GAS" rather than the truth, which is that it *cannot*.

---

## §4 — WHY NO SOLVE WAS SPENT, AND THE DECISION THAT IS NOT MINE

The addendum's §2 order is: G-BIMODAL → repair → re-freeze → phase-0 census →
screen → full span. **The chain stops at "re-freeze", because the derive's own
pre-registered gate refuses the artifact.** No phase-0 census, no screen, no
bundle — so P-7 is unscored and the rule-29 screen was never entered.

**The tempting move, and why I did not take it.** The ST_GAS bands are LP-inert
(§3), so the artifact could be written with the CT-side repair alone — dropping
ST_GAS from the JSON — delivering the whole model-visible benefit while shipping
no inverted curve. That option is **real and may well be right**, but choosing it
*after* watching G4 fail is exactly the gate-shopping the PRECOMMIT's stop rule 4
forbids ("no gate is re-run to a pass or redefined after its result"). It is an
**owner decision**, and if taken it must be pre-registered before the artifact is
written, not adopted here.

**RAISED, NOT TAKEN — the owner's call:**
1. **Adopt the CT-side repair only** (write CC + CT, omit the G4-failing ST_GAS
   bucket, with the omission and this finding cited in provenance). Delivers the
   1.306 → 0.970 G1 repair and the measured `CT_PEAKER` bands; ships nothing
   inverted; ST_GAS keeps reading the pooled CT bucket exactly as today, which is
   the status quo the bypass makes inert anyway.
2. **Refuse the whole partition** and leave the frozen artifact and its disclosed
   contamination note standing, as the PRECOMMIT's own FAIL branch prescribes.
3. **Investigate the inversion first** — is the steamers' measured top-of-curve
   genuinely below their middle (an RMR/RA conduct story worth its own object),
   or an artefact of a 15 %-of-capacity peak window on a 25–30-resource bucket?

Your standing ruling — *"if structural integrity improves but gates regress that
may still be a keeper"* — is recorded and would bear on option 1. It does **not**
decide it: the regression here is in a **protective estimation gate on the input
itself**, not a rubric criterion on a run, and no run exists.

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **INSTRUMENT CORRECTION, made before any scoring.** The committed G-BIMODAL
   probe did not reproduce the derive on three points, all found by reading the
   derive's source against the probe — never by comparing to the 46/100 target:
   `cap` was the p98 of *hourly maxima* where the derive takes the p98 of *every
   segment row*; cross-year pooling used `max` where the derive takes the
   earliest year's cap; `min_mw` used the unfiltered store. P-2's **exact**
   reproduction is the evidence the corrections were right and complete.
2. **A PARTIAL-CORPUS VERDICT WAS SEEN, AND IT DISAGREED.** Before the coverage
   guard existed, a smoke test scored G-BIMODAL on **296 days of 2023 alone** and
   returned antimode 11.357 with **4.93 GW** above it — **FAIL**, 488 resources,
   CC 65 / 16.742 GW, CT 85 / 9.083 GW. That artifact was deleted immediately and
   is recorded here in full. The registered window [10.9, 12.5] and bracket
   [1.5, 4.5] GW were **not touched**, then or since — knowing that 4.93 sat just
   above a 4.5 ceiling makes widening it precisely the gate-shopping stop rule 4
   forbids. The guard now refuses an under-covered corpus, and the pooled
   population gives the opposite verdict, which is the whole reason the guard
   matters.
3. **A MISLEADING LOG LINE OF MY OWN**, found by reading this session's output:
   the derive printed `(unimodal - NOT split)` when `--no-st-split` was passed,
   conflating an operator choice with a measurement. The run was correct and only
   its report was wrong, but a future reader of that log would have been told the
   CT population is unimodal — the opposite of what G-BIMODAL measured. Fixed.
4. **`_wquantile` raised on an empty sample**, which killed the first three-way
   run. It now returns NaN — the correct answer for the quantile of nothing —
   **and** `main` hard-fails if any *consumed* band is non-finite, so a class
   whose armed bands cannot be estimated can never ship as if measured. Making
   the quantile tolerant *without* that guard would have been a silent hazard.
5. **A new INTAKE path was added to a frozen derive** (`--from-reduced-store`),
   because `curate_dam_public_bids` needs ~14.3 GB for one year against a 15 GB
   box. It is licensed by measurement, not by argument: a `--no-st-split` run
   over that store reproduced the frozen artifact's consumed values **exactly** —
   every band, both G1 numbers, both ladder p50s — with only the timestamp and
   new provenance fields differing.
6. **G-DRIFT, keeper `fa23c1f7` → HEAD, is complete and every hunk INERT**, across
   nine deltas audited as `main` advanced. Three touched files a CAISO backcast
   genuinely reads and were each measured rather than argued: the carbon price
   (exactly 33.03 / 35.23 / 28.06, twice, because `carbon.py` moved twice);
   `DEMAND_GROWTH_RATES["CAISO"]`, which **moved** and **is selected** by the
   backcast config — inert only because the compounding span is empty (factor
   exactly 1.000000000000, arrays identical); and the eGRID mirror + boundary-HR
   memo, re-verified after they changed a second time. One LIVE hunk exists
   (`import_co2_tons` now clamps CAISO's export sinks) and is confined to `co2`,
   which is not in `CRITERIA` — so G-CTRL form 4 stands, no control solve was
   spent, and this session did not difference `co2` against the keeper.
7. **The rule-21 zero-DOF claim was verified against the code before the gate ran**,
   not asserted: all six ST_GAS operands already exist (`base_hr` 11.847,
   `fleet_mw` 2,858.8, `pct_committed` 6.617, `pct_peaking` 15.0 from the bin
   assignments; `econ_low_share` 0.50 from the model's own geometry; `VOM` 4.0
   from `constants.VOM["gas_st"]`, the same table `gas_cc` 2.0 / `gas_ct` 3.5 come
   from). The second cut is located, never swept.
8. **G1_BOUNDS were not tuned to admit the result.** `CT_PEAKER` keeps the band it
   already had and `ST_GAS` inherits it. Both pass with room (0.970, 0.895); the
   repair did not need the allowance.
9. **The phase-0 estimator was built and null-validated but never used** — F = 0.0
   exactly, X = 0, 0 of ~1,450 gas tranches moved on all three years. It is
   committed and ready for whichever option §4 takes.
10. **ZERO LP was spent and no run was produced**, so rule 15 `[R-DASHBOARD]` is
    not engaged and there is nothing to register.

---

## §6 — DO-NOT-REDO ADDS

1. **Never re-score G-BIMODAL on a partial corpus.** The gate now refuses one,
   and §5.2 is why: 2023-only gives a different population *and* the opposite
   verdict.
2. **Never quote the ST_GAS band move (1.145 → 1.563) as a dispatch effect.**
   `ST_GAS_PEAKER_PLANTS` bypasses those three plants out of
   `offer_curve_by_group` entirely (§3); the number is artifact-only.
3. **Never relax G4's flatness tolerance, or drop the ST_GAS bucket from the
   artifact, on the strength of this session's result.** Either may be right;
   both are owner decisions that must be pre-registered *before* the artifact is
   written (§4).
4. **Never re-derive the CAISO offer surface from the clean tree on this box** —
   it needs ~14.3 GB for one year. Use `--from-reduced-store`, whose equivalence
   is measured in §5.5.
5. caiso-253 §7, caiso-252 §7 and §12, caiso-251 §8, caiso-250 §7, caiso-249 §7,
   caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7, caiso-244 §7,
   caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8,
   caiso-230 §9, caiso-229 §10, caiso-169, caiso-168 §8 stand in full.

---

## §7 — QUEUE

1. **The §4 decision** — CT-only adoption, full refusal, or investigate the
   inversion. Owner's call; nothing proceeds without it.
2. **The ST_GAS peak inversion** as its own object if §4 option 3 is taken: is
   the steamers' measured top-of-curve genuinely below their middle (an RMR/RA
   conduct story) or an artefact of a 15 %-of-capacity window on 25–30 resources?
3. Carried unchanged: the `complete` marker (**raised, not granted** — CAISO's
   determination is CALIBRATED and it holds no marker); the stale
   `program-status.json` top-level CAISO keeper stamp (**ask before touching**);
   the C3a weight basis; the per-zone storage/class sidecar; the DMM 2025
   RA-import basis; Panoche.

**No run registered (none produced), no keeper change, no artifact written, no
`ScenarioConfig` field, no `complete` declaration.**

**Next number: caiso-255.**
