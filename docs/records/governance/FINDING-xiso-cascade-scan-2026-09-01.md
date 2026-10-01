# FINDING — xiso-cascade: the nested-cascade instrument rule carried to all five other ISOs; MISO's live sum defect MEASURED and REPAIRED, the other four verified CLEAN

**Date:** 2026-09-01 · **Lane:** cross-ISO instrument audit (backcast track) ·
**Shorthand:** xiso-cascade
**Rule carried:** nyiso-166 §2 (`docs/FINDING-nyiso166-as-reference-repair-2026-08-31.md`) —
**a reserve cascade nested by duration/quality posts CUMULATIVE prices, so a
reserve MW earns the cascade MAX, never the SUM.** · **Zero solve.** Committed
artifacts + committed raw only. No LP, no holdout spend, no mechanism, no
`ScenarioConfig` field, no keeper/shard/marker/matrix-cell change, no
determination moved.

---

## 0. Result

Every reserve/AS **price-aggregating** construction in ERCOT, PJM, MISO, CAISO
and NEISO was enumerated and adjudicated against the rule, with the nesting
**measured on committed data** wherever committed data exists (never inherited
from the nyiso-165 §5 preliminary scan, which this session re-verifies and in
two places corrects).

| ISO | cascade in the published data? (measured here) | any construction sums it? | verdict |
|---|---|---|---|
| **MISO** | **yes** — `GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP` in **100.0000 %** of **554,904 cells** (2023–2026 × DA+RT × all 9 zone rows) | **yes — two live instruments, three committed records, six prose sites** | **DEFECT CONFIRMED and REPAIRED (§3)** |
| **PJM** | **yes** — Sync ≥ Non-Sync ≥ Secondary in **100.0000 %** (2023–2025, RTO **and** MAD locales, 52,608 h) | no — every consumer is per-product or MW; the model *constructs* the cascade from constraint shadows (§4) | **CLEAN** |
| **NEISO** | nests **by design** (TMSR ⊂ 10-min-total ⊂ 30-min-total); no posted-price artifact is committed (window CSVs gitignored) | no — the one posted-price reader uses **TMSR alone**, deliberately | **CLEAN** (code-level; §2.1) |
| **CAISO** | **yes, structurally** — `ru ≥ sr ≥ nr` in **100.0000 %** of the committed DAM sample, but priced-degenerate (`nr` $0 in 100 %, `sr` $0 in 99.79 % of intervals) | no — the one price sum is **nested-REGION** stacking, and the regional postings are measured to be **incremental adders** (§2.3) | **CLEAN** |
| **ERCOT** | **no** — no consistent product ordering exists: best pair 93.6 %, and orderings **flip across years** (`ecrs ≥ regup` 65 % in 2023 → `regup ≥ ecrs` 94 % in 2025) | n/a — and the one committed aggregate, `binding_mcpc`, is already a per-hour **MAX** | **NOT IN THIS CLASS** |

**The distinction the rule turns on, preserved throughout** (nyiso-166 §2):
summing the **shadow prices of distinct nested constraints** is CORRECT — that
sum is what *generates* one cumulative posted price (`results/rcpf.py`, the LP's
cross-family dual sum, PJM's `pjm_reserve_cascade_mcp` all do exactly this).
What is WRONG is summing the **published cumulative product prices**, which
double/triple-counts the shared shadows. Likewise **MW are not prices**: cleared
MW of distinct products are disjoint awards and genuinely add (every "reg+spin+
supp" MW sum in the repo is legitimate and untouched).

## 1. Method

1. **Enumerate, then adjudicate.** All AS/reserve-price-touching constructions
   found by token sweep (product names, MCP fields, endpoint names, price
   columns) over `src/`, `scripts/`, `tests/`, then read call-site by call-site.
   Consumer claims were re-verified, never inherited — which is how §3.2's
   correction to the prior scan's blast-radius claim was found.
2. **Measure the nesting on committed data** (a data property of the raw file
   alone — the nyiso-166 §5 posture: data prep, not a holdout spend; the 2026
   partial files are measured as data properties only, nothing model-side is
   scored against them).
3. **Repair only what is measured defective, one ISO per finding** — executed
   for MISO only, under the nyiso-166 acceptance-test pattern (§3.4).

## 2. The four clean ISOs — constructions enumerated

### 2.1 NEISO (checked first and hardest, per charter)

ISO-NE is the closest structural analogue of the NYISO defect (TMSR ≥ TMNSR ≥
TMOR by design). Constructions found:

| construction | aggregates prices? | adjudication |
|---|---|---|
| `model/reserves/spec.py::NEISO_RCPF_PRODUCTS` + `results/rcpf.py::rcpf_adder` (post-solve overlay, `derive_neiso_rcpf_overlay.py`) | sums per-product **demand-curve (shadow) prices** | **correct half** — the construction that *generates* the cumulative price |
| `spec.py::_neiso_design` (LP co-opt) | three **distinct nested constraint families**; LP sums their duals | **correct half** by construction |
| `scripts/probes/_neiso76_reserve_content.py` (the only reader of posted TMSR/TMNSR/TMOR prices in the repo) | reads all three, **uses TMSR alone** — "TMSR is the top of ISO-NE's cascade — a spin provider's price internalises the lower products" | **correct** (top ≡ max wherever the cascade is intact) |
| `scripts/lib/reserve_requirements/neiso.py`, `data/neiso_reserve_requirements.py` | MW requirements | not prices |

No committed artifact carries ISO-NE posted reserve prices (the
`data/raw/NEISO-AS/reserve-prices/` window CSVs are gitignored, regenerable via
`--fetch`), so there is nothing to measure a magnitude on and no empirical
monotonicity check without a fetch; the verdict is code-level and does not
depend on the empirical cascade holding (TMSR-alone is the spin
opportunity-cost proxy under either outcome). **Nothing sums the cascade.**

**One suspected sibling defect, REPORTED not repaired** (unmeasured — the data
is not committed): `_neiso76_reserve_content.py::_hour_index` maps the RZPD
CSV's (local date, hour-ending) **positionally** onto the model's fixed 8760
clock. If the CSV clock is prevailing local (ISO-NE reports are), this is the
nyiso-166 **defect-B** class (naive prevailing clock on a standard-time index):
DST-season hours land one slot off against `actual_lmp_hourly_NEISO.parquet`'s
fixed-standard clock. Effect would be a mild smear of the probe's 4-hour
peak/trough window means, not a sign flip. **Routed to NEISO's lane** to
measure on a fetch before any re-run of that probe is quoted.

### 2.2 PJM

Cascade measured at **100.0000 %** monotone (Sync ≥ Non-Sync ≥ Secondary; RTO
and MAD locales; 2023–2025; `data/raw/PJM-AS/ancillary_services_<y>.parquet`,
`unit == "Price"`, current rows). Constructions:

| construction | adjudication |
|---|---|
| `results/scarcity.py::pjm_reserve_cascade_mcp` | **the canonical correct construction**: per-product constraint shadows via `pjm_reserve_demand_price`, summed along the Manual-11 §4.4.1 substitution cascade (SR = SP_sr+SP_pr+SP_30 …), and `energy_adder = out["SR"]` — the richest cascade, i.e. the MAX, never a sum of posted prices |
| `derive_pjm_ordc_overlay.py::validate_mcp` | measured check **per service** against each service's own posted MCP |
| `scripts/probes/c3c_q1_pjm_phantom_audit.py` | pins `SERVICE = "PR"` (single product) and documents the incremental-vs-total distinction |
| `data/fleet/withholding.py` (`_CLEAN_AS_UP_MW_COLS`), `build_pjm_as_withholding.py` | **MW award** sums (disjoint assignments; additive) |
| `report_pjm_posture_gate.py` | online target = SR+REG cleared **MW**; SR **MCP alone** for direction |
| `_pjm138_mec_gap_shape.py` | per-service, per-locale, "reported separately rather than pooled", with the nested RTO ⊃ MAD locale relationship stated |
| clean-AS price columns (`curate_ancillary_services.py`, `*_price_usd_per_mw`) | **write-only** — no code consumer reads them |

### 2.3 CAISO

Two structural questions, both **measured** on the committed
`data/raw/CAISO-AS/asprc_{ru,sr,nr}_ALL_*.csv` (DAM, 2023 span):

* **The product cascade exists**: `ru ≥ sr` and `sr ≥ nr` in **100.0000 %** of
  system-region intervals (downward substitution) — so the rule APPLIES to
  CAISO, and any future construction summing `ru+sr+nr` posted prices would be
  the MISO defect. It is priced-degenerate today (`nr` $0 in 100 %, `sr` $0 in
  99.79 %; 19 priced spin hours in the sample).
* **The regional postings are incremental ADDERS, not totals**: in **6 of 6**
  hours where the parent `AS_CAISO` spin price cleared > $1, the nested
  `AS_NP26` row posted **$0** — impossible if regional rows were totals
  (a sub-region total can never sit below its parent's). This empirically
  grounds the one price sum in the repo:
  `caiso_storage_as_revenue_phase0.py`'s `sys_p + min/max(np_p, sp_p)` — **the
  same product** summed across **nested regions**, i.e. distinct constraint
  shadows: the legitimate half, computed per product inside a per-product loop
  (award MW × own product's price). `_caiso71`'s `spin_evening +
  nonspin_evening` sums **MW requirements**. Nothing sums across products.

### 2.4 ERCOT

Measured on the committed `data/raw/ercot/ercot_<y>_dam_as_mcpc_hourly.parquet`
(2023–2025): **no consistent pairwise ordering** among `regup/rrs/ecrs/nonspin`
MCPCs — the most consistent pair peaks at 93.6 % and orderings flip across
years (`ecrs ≥ regup` 65.3 % in 2023 vs `regup ≥ ecrs` 93.6 % in 2025). ERCOT's
per-service demand curves clear independent prices that internalise nothing —
**not a cumulative cascade**; a sum of ERCOT MCPCs would be wrong for a
different reason (no MW earns two products at once), and nothing computes one.
The committed aggregate `binding_mcpc` is already the per-hour **MAX** (built
so by `build_ercot_dam_as_mcpc.py`), the measured-AS overlay
(`results/scarcity.py`) consumes exactly that column, the retirement screen's
reserve signal is `reserve_price_by_family.max(axis=1)` (`runner.py` — max
across parallel products, correct), and `regup + rrs + ecrs` sums in
`ercot102_as_holdout_attribution.py` / `derive_ercot_storage_as_products.py`
are **MW**.

## 3. MISO — the live defect, measured, blast-radius-enumerated, repaired

### 3.1 The defect

Two live instruments summed the three published generator ASM MCPs:

* `scripts/probes/_miso167_summer_scarcity_instrument.py` —
  `asm_sum = GENREGMCP + GENSPINMCP + GENSUPPMCP`, emitted as
  `miso_asm_mcp_sum` and divided into the energy gap as
  `asm_share_of_energy_gap_pct` — **the "$484.87 = 118.8 % of the energy gap"
  headline**.
* `scripts/probes/_miso171_reserve_product_decomposition.py::stage4_mcp` —
  `regspin = reg + spin`, `total = reg + spin + supp`.

MISO's products nest by substitution (BPM-002: reg clears spin, spin clears
supplemental), so the posted prices are cumulative — measured here at
**100.0000 % of 554,904 cells** (2023–2026 × DA+RT × all 9 zone rows; the DEM*
triple is likewise monotone, reported informationally). Unlike NYISO the three
are essentially **never all equal** (reg carries its own increment), so the
sum overstates by 1.1–1.3× in the body and **~1.8–2.5× in the tail** rather
than a clean 3×.

### 3.2 Blast radius — wider than the preliminary scan recorded

nyiso-165 §5 reported this defect with the mitigation *"a grep of `docs/` finds
no prose citation of any summed figure"*. **That claim is FALSE** — it grepped
for the field names; the prose cites the VALUE. `$484.87`, quoted as *"MISO's
OWN published RT ASM MCP"*, appears in:

1. `results/calibration/FINDING-miso167-summer-scarcity-anatomy-2026-08-18.md` §3 — the origin headline, *"accounts for 118.8 % of the energy gap"* (2023 120.9 %, 2024 19.2 %);
2. `results/calibration/PREREG-miso167-online-gated-reserve-supply-2026-08-18.md` §1 — evidence context for the `miso_reserve_online_gated` pre-registration;
3. `results/calibration/FINDING-miso171-reserve-requirement-decomposition-2026-08-20.md` §5 — plus its own summed "$222.37 / DA total" table column and the "**~71 % synchronised / ~29 % supplemental**" price shares computed off the sum;
4. `results/calibration/FINDING-miso178-c3a2025-anatomy-and-lever-plan-2026-08-23.md` §3 — *"still ≈120 % of the energy gap"*;
5. `docs/mechanism-testing-matrix.md` — the MISO lever-queue narrative ("WHAT IT IS");
6. `docs/calibration-log/miso.md` — the miso-167 and miso-171 entries.

And a **third committed record** carries the summed fields: `_miso178_c3a2025_anatomy.json`
(its `m167_repoint` re-ran the m167 instrument, inheriting the construction, at
the miso177_rho_B bundle — share 119.8 % against that bundle's $404.68 gap).

**What does NOT consume it — verified call-site by call-site:** no scorer, no
solve path, no keeper gate, no matrix CELL. PREREG-miso167's kill and promotion
gates (K-PRE-A/B, K-1…K-5) are MW- and criterion-based; the
`reserve_deliverability_scoping` **K** cell and the miso-171 sub-regional
**INERT** adjudication rest on H_on/requirement **MW** (which genuinely add);
`report_miso_posture_gate.py` reads `GENSPINMCP` alone. **No committed
determination moves** — the 2026-08-30 cross-lane re-grade rule is not engaged.

### 3.3 Corrected magnitudes

On the m167 instrument's own basis (its scarce sets, its −2 h CST alignment),
reproduced exactly and then corrected (per-hour cascade top = `GENREGMCP` in
every scarce hour of every year, probe-verified):

| year | scarce h | energy gap | summed "MCP" | **corrected top** | sum/top | share of gap: was → **is** |
|---|---:|---:|---:|---:|---:|---|
| 2023 | 11 | $298.71 | $361.10 | **$144.63** | 2.50× | 120.9 % → **48.4 %** |
| 2024 | 14 | $302.32 | $58.07 | **$31.88** | 1.82× | 19.2 % → **10.5 %** |
| 2025 | 47 | $408.24 | $484.87 | **$193.30** | 2.51× | 118.8 % → **47.3 %** |

m171 stage-4 (loader EST alignment): scarce-47 RT `total` $97.62 → top
**$46.44**; DA-foreseen RT $181.40 → **$76.88**; the RT>$200 block $222.37 →
**$93.14**. Market-wide sum/top runs 1.08–1.26× all-hours and 1.17–1.90× in
top>$50 tails, per year and market (full table in the acceptance record).

**What the corrections do to the standing narrative** (prose corrected in
place, §3.5): the miso-167 headline *"MISO's own reserve market prices the
whole gap"* becomes *"…prices roughly HALF the gap"*; the miso-171 §5 share
emphasis **inverts** — of the true published price, the supplemental-level
content (offline-quick-start-earnable, ungateable) is **68.2 %** and the
synchronised-only increment (top − supp, the gateable structure) **31.8 %**,
not "71 % synchronised / 29 % supplemental"; and one comparison flips sign —
the armed gate's DA-foreseen regspin dual ($25.81) sits **above** the measured
DA sync-only increment ($19.43), not conservatively below a summed $60.63.
Both corrections **strengthen** the standing miso-178 closure a fortiori (less
of the gap is reserve-priced; less of the reserve price is gateable), and the
promoted mechanism itself (`miso_reserve_online_gated`) stands on its
structural grounds and MW-based gates, untouched.

### 3.4 The repair (rule 14 `[R-ACCURATE]`, nyiso-166 acceptance pattern)

* **Both live instruments corrected** to per-hour cascade-top aggregation —
  `_miso167…::cascade_top` (emits `asm_top` / `miso_asm_mcp_top`; the share
  headline follows it) and `_miso171…::cascade_price_stats` (emits `top` and
  `sync_only_increment`); the summed fields are **deleted**, not kept (rule 23
  `[R-DELETE]`). `_miso178…py` inherits the fix transitively (it re-runs m167's
  stages).
* **The three committed records are annotated, not regenerated** — their input
  bundles (`miso160_wefor_B`, `miso170_layup_B2`, `miso169_gated_A`) are pruned
  from the tree, so regeneration is impossible; each record keeps its original
  fields as the frozen record and now opens with a dated
  `CORRECTION_2026-09-01_xiso-cascade` key carrying the corrected values
  (inserted programmatically from the acceptance record, never typed).
* **Acceptance test** — `scripts/probes/_xiso1_miso_asm_cascade_check.py`, an
  **independent construction** (its own implementations of both instruments'
  hour mappings, no import of either): reproduces every committed summed value
  **exactly** (n, sum, per-product means; every `reproduces` flag True in
  `results/calibration/_xiso1_miso_asm_cascade_check.json`), verifies
  top == `GENREGMCP` in every scarce hour, then emits the corrections the
  JSON keys carry.
* **Regression test** — `tests/test_miso_asm_cascade.py` (7 tests, passing)
  pins: the cascade invariant on every committed year × market (if it ever
  fails, the products are no longer cumulative and the aggregation must be
  re-derived from the posting convention, not patched); cascade MAX end-to-end
  synthetically ($100/$100/$100 → $100 never $300; $90/$50/$25 → $90 never
  $165); the summed fields stay deleted; and the CORRECTION keys stay present
  and self-consistent.

### 3.5 Records touched

Prose corrected in place with dated notes (originals preserved): the four
`results/calibration/` docs of §3.2, the `docs/mechanism-testing-matrix.md`
MISO narrative, the two quoted `docs/calibration-log/miso.md` passages, plus a
new dated **xiso-cascade** entry in `docs/calibration-log/miso.md`. The
mechanism-matrix **shard** (`docs/codebase-site/data/mechanism-matrix/MISO.js`)
needed **no edit** — its cell narratives cite the m171 record on the MW basis
only.

## 4. The model-side constructions, adjudicated for completeness

All four model-side aggregation seams implement the CORRECT half and are
untouched: `results/rcpf.py::rcpf_adder` (NYISO/NEISO overlays) sums
per-product demand-curve shadows; the LP's `model.py` sums **distinct** family
balance-row duals into `system.reserve_price` (per-family kept alongside —
and for ERCOT's parallel products the screens consume the **max**, not the
sum); `results/scarcity.py::pjm_reserve_cascade_mcp` sums shadows along the
substitution cascade and hands the energy LMP the top; `runner.py`'s
`reserve_price_signal = rp.max(axis=1)`.

One comparability note for the MISO lane, not a defect: `_miso167`'s model-side
`model_dual_mean/max` report the **max across families**, which mildly
UNDERSTATES the model's own cumulative reserve price against the (corrected)
measured top — conservative in the direction that survives the correction.

## 5. Corrections to the prior scan's record (nyiso-165 §5)

1. Its MISO mitigation *"no prose doc cites a summed figure"* is **refuted** —
   six prose sites cite `$484.87` (the mechanism matrix included), one a
   pre-registration; and a third committed record (`_miso178…json`) carries the
   fields. The open item it filed is now **repaired**, with the consumer check
   it deferred ("the fields' downstream use, a question this scan did not
   open") executed here.
2. Its tail ratios ("2.08/2.20/1.85× in hours cleared >$50") do not reproduce
   under this session's tail definition (top > $50: 1.80/1.85/1.47×) — the
   direction and order of magnitude agree; this session's figures are the ones
   in the committed acceptance record, with the definition stated.
3. Its PJM / NEISO / CAISO / ERCOT verdicts are **confirmed**, now with
   measurements where it had code reads: PJM re-measured at both locales; CAISO
   regional-adder semantics and product monotonicity measured (its "not a
   cumulative duration cascade" is sharpened to "monotone but priced-degenerate,
   and nothing sums it"); ERCOT's non-cascade demonstrated (ordering flips
   across years) rather than asserted.

## 6. Guardrails discharged

Zero solves; no `ScenarioConfig` field; no mechanism tested, so no matrix cell
moves (session-start duties (b)/(c) not triggered, duty (a) discharged by
reading the MISO shard); no keeper, shard, marker, or holdout year touched; no
new workflow. The repair moves **no committed determination** (§3.2), so the
2026-08-30 cross-lane re-grade rule is not engaged. Repair confined to one ISO
(MISO), per charter; rule 25 honoured — no verdict transferred between ISOs,
each measured on its own data.

## 7. Open items routed

* **NEISO lane:** measure the suspected `_neiso76_reserve_content.py`
  positional-clock sibling (§2.1) on a `--fetch` before quoting any re-run of
  that probe's window means. Report-only here; unmeasured because the window
  CSVs are deliberately not committed.
* **MISO lane:** none from this defect — repair complete. (Optional
  comparability note §4 if model-vs-measured reserve LEVELS are ever re-quoted.)
* **PJM / CAISO / ERCOT lanes:** nothing. CAISO carries the standing note that
  its cascade is real and monotone, so the rule applies the day anyone sums
  `ru/sr/nr` posted prices.
