# FINDING — nyiso-165: the AS-reference repair, independently verified, and the cross-ISO cascade scan

**Date:** 2026-09-01 · **Lane:** NYISO calibration · **Shorthand:** nyiso-165
**Rule:** 14 `[R-ACCURATE]`, 25 `[R-ISO-SCOPE]` · **Zero solve.** Raw published
CSVs + committed artifacts only. No keeper, shard, marker, determination,
`ScenarioConfig` field, mechanism or matrix cell changed. No holdout year of any
tier touched; the freeze is untouched.

**Object:** `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`
**Builder:** `scripts/data/process_nyiso_as.py::build_reference`

---

## 0. What this session is, and what it is not

**The repair had already landed.** This session was dispatched to repair
`build_reference`. On arriving at HEAD the repair was already committed —
`9767c870`, *"nyiso-166: repair the committed RT-reserve calibration reference"*
— by a data lane that credits **this session's own earlier §3** as the audit
that found the two defects and deferred the fix
(`docs/FINDING-nyiso166-as-reference-repair-2026-08-31.md`, and the
2026-08-31 nyiso-165 entry in `docs/calibration-log/nyiso.md`).

So nothing was re-repaired. What this session delivers instead:

1. **Independent verification** of the landed repair against the prompt's
   acceptance test, by a path the repairing session did not use (§1–§3) —
   because the audit's blast-radius claim is one to re-verify, not inherit.
2. **One correction to the nyiso-166 record** (§4): its §6 attributes
   *"46 of 65"* to the pre-repair artifact. That is the **defect-A-only**
   figure. The artifact as it actually stood — both defects live, which is the
   basis the false positive was computed from — gives **29 of 65**. No
   conclusion changes; the number's attribution does.
3. **The cross-ISO cascade scan** (§5), which nyiso-166 did not perform. It
   finds **one live sibling defect, in MISO**, and clears PJM, NEISO, CAISO and
   ERCOT with evidence.

## 1. The two defects, and the repaired construction

Both were in `build_reference`, in every column of every year of the artifact.

* **A — the nested duration cascade was SUMMED** (`spin_10 + nonsync_10 +
  op_30`). NYISO's three posted operating-reserve products nest by duration, so
  the posted prices are **cumulative, not incremental**: a 10-minute spinning MW
  earns `spin_10`, never the sum. Re-verified on the committed per-year CSVs —
  `spin_10 ≥ nonsync_10 ≥ op_30` in **100.0000 %** of rows, all three exactly
  equal in 82–84 %. Repaired to the cascade **max**.
* **B — a naive prevailing-Eastern clock on a standard-time index.** The CSV's
  `Time Stamp` is prevailing Eastern; the model's NYISO clock is fixed
  `Etc/GMT+5` (`derive_actual_lmp._STD_TZ`). Measured at HEAD on the WEST
  series, the two indices disagree in **5,712 / 8,760 h (65.2 %)** in each of
  2023/24/25 — the whole DST season, which is where the tail sits. Repaired by
  localizing to `America/New_York` and re-indexing with the repo's own
  `_std_hour_index`.

## 2. Acceptance test — PASSES exactly, on an independent path

The prompt's acceptance test is a property of the **rebuilt reference**. The
measurement of record, `scripts/probes/nyiso164_nyca_shortage_check.py`, reads
the **raw CSVs**; this session instead scored the test directly off the
**committed parquet**, so the two paths share no code below the raw source.

NYCA tier (`nyca_reserve_adder`) in the C3c tail hours (`rt > $300`):

| year | tail h | mean | target | median | max | reserve > LMP | ratio median | target |
|---|---|---|---|---|---|---|---|---|
| 2023 | 10 | **$306.74** | $306.74 ✅ | $248.22 | $761.73 | 0 | **0.573** | 0.573 ✅ |
| 2024 | 13 | **$254.62** | $254.62 ✅ | $239.96 | $552.90 | 0 | **0.536** | 0.536 ✅ |
| 2025 | 42 | **$393.31** | $393.31 ✅ | $403.74 | $1,101.85 | 0 | **0.654** | 0.654 ✅ |
| **total** | **65** | | | | | **0 / 65** ✅ | | |

And the probe of record still returns its committed verdict against the rebuilt
file: re-run at HEAD, `_nyiso164_nyca_shortage_check.json` is **byte-identical**
to the committed record (sha256 `3de5022512540c64…`), verdict
*"CONFIRMED — NYISO's C3c ledger stands"*, kill-gate clause 1 firing on 0/65.

**The artifact is byte-reproducible.** Regenerating it from the raw CSVs at HEAD
reproduces sha256
`60be007f34b3599d735d87eb71842e9309ec174ee18f71b9f7577647d0a52156` exactly, with
no working-tree diff.

`tests/test_nyiso_as_reference_repair.py`: **9 passed**.

## 3. Blast radius — re-verified, and proved rather than read

Every reader of the filename across `scripts/` and `src/` (grep, exhaustive):

| reader | armed at HEAD? | output changes? |
|---|---|---|
| `derive_nyiso_rcpf_overlay._actual_as_reserve` (call site line 628) | yes, when the overlay is run | **no** — feeds `print()` only; the written `scarcity*.parquet` is built from the model's `adder`/`nyca`/`loc` |
| `derive_nyiso_rcpf_overlay._actual_zone_reserve` (call site line 706) | yes, same | **no** — same, the per-zone report table |
| `scripts/probes/c3c_q2_nyiso_nyca_shortage.py` | **SUPERSEDED / DEFECTIVE**, retained unrepaired | its committed JSON is frozen and deliberately not re-run |
| `tests/test_nyiso_as_reference_repair.py` | yes (data-backed cases skip unhydrated) | passes |
| **any scorer, verdict, gate, or LP path** | **none exists** | — |

**Proof, not assertion.** Reading call sites establishes intent; to establish
fact, the reference was moved out of the tree and the scored path re-run against
its absence:

```
scripts/calibration_verdict.py --run-id 2026-08-30-nyiso-159-loss-surface
   reference present vs absent → byte-identical output   (NOT-YET)
scripts/audit_keepers.py --iso NYISO
   reference present vs absent → byte-identical output   (PASS: 0 failures, 0 warnings)
```

A file whose presence or absence cannot change the output is not an input to it.
The keeper `2026-08-30-nyiso-159-loss-surface` re-verifies **NOT-YET** on exactly
{C3a-2025, C3c}, unchanged. **No committed verdict or determination moves**, so
the 2026-08-30 cross-lane re-grade rule is not engaged. The file was restored
byte-identical (sha unchanged) and the working tree is clean.

## 4. Correction to the nyiso-166 record — the "46 of 65" is defect-A-only

nyiso-166 §6 reads: *"on the summed basis it 'exceeded' LMP in 46 of 65 — which
is precisely how nyiso-165 reached the opposite verdict."* Reconstructing all
four combinations from the raw CSVs (the retired code taken from
`9767c870^`):

| basis | ceiling test | tail means 2023 / 2024 / 2025 |
|---|---|---|
| **pre-repair, both defects live** (what the artifact actually was) | **29 / 65** | $313.78 / $274.10 / $925.33 |
| defect A only — summed, clock already fixed | **46 / 65** | $669.48 / $682.93 / $1,143.61 |
| defect B only — max, clock broken | 7 / 65 | $155.16 / $110.08 / $320.44 |
| **repaired, both fixed** | **0 / 65** | $306.74 / $254.62 / $393.31 |

So 46/65 is the *as-if-half-repaired* figure, not the artifact's. Two smaller
notes in the same sentence: the false positive did not fail a ceiling test at
all — `_c3c_q2_nyiso_nyca_shortage.json` records **56 of 65** tail hours as
"NYCA-short" at the `≥ $40` threshold (9/10, 9/13, 39/42 by year), a
shortage-threshold count, not a ceiling comparison. The direction, the size class
and every conclusion are unaffected; the repaired basis is 0/65 on all readings.
Recorded here rather than by editing nyiso-166's finding, which stands as that
session's own record.

## 5. Cross-ISO cascade scan — the generalizable instrument rule

**The rule, stated precisely.** The distinction that matters is *what is being
added*:

* Summing the **shadow prices of distinct nested constraints** is **correct** —
  a marginal MW qualifying for all of them relieves all of them. This is exactly
  what `results/rcpf.py::rcpf_product_prices` does to build its `"adder"`, and
  it is *the mechanism that generates a cumulative posted price*.
* Summing **published cumulative product prices** is **wrong** — that price
  already contains the lower products' shadow prices, so the sum double- or
  triple-counts.

Both halves are live in this repo, which is why the rule has to be stated on the
*provenance* of the number and not on the word "nested". NYISO's own
nested-**region** stacking (NYCA + East + SENY + NYC inside one posted zonal
price) is real and was never the defect — it is the duration products *within*
one posting that are not additive.

Scan of every ISO's reserve-price construction. NYISO is the only ISO with a
committed `actual_as_reserve_*` reference, so the question asked of the other
five is whether their code aggregates a published cascade the same way.

| ISO | cascade in the published data? | verdict |
|---|---|---|
| **NYISO** | yes — `spin_10 ≥ nonsync_10 ≥ op_30`, 100.0000 % | **defect found, REPAIRED** (nyiso-166; verified §2) |
| **MISO** | yes — `GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP`, **100.0000 %** in DA and RT, all of 2023/24/25 | **SAME DEFECT, LIVE — MISO's open item** (below) |
| **PJM** | yes — `SR ≥ NSR ≥ Secondary`, **100.0000 %**, 2023/24/25 | **clean** — nothing sums them |
| **NEISO** | yes by design — TMSR ⊂ total-10-min ⊂ total-30-min | **clean** — the cascade top is used alone |
| **CAISO** | not a cumulative duration cascade | **clean** |
| **ERCOT** | no — separate per-service MCPCs | **not in this class** |

### MISO — the live sibling defect (REPORTED, NOT REPAIRED)

`scripts/probes/_miso171_reserve_product_decomposition.py::stage4_mcp`, lines
205–206:

```python
vals["regspin"] = round(vals["reg"] + vals["spin"], 2)
vals["total"]   = round(vals["reg"] + vals["spin"] + vals["supp"], 2)
```

`reg`/`spin`/`supp` are MISO's published `GENREGMCP` / `GENSPINMCP` /
`GENSUPPMCP`. Measured on the committed MISO-AS parquets, `GENREGMCP ≥
GENSPINMCP ≥ GENSUPPMCP` holds in **100.0000 %** of rows in every year and both
markets (8,760–8,784 rows each) — the identical cumulative-cascade signature
NYISO carries. The cleared price a MW earns is `GENREGMCP`; `total` double- and
triple-counts.

Magnitude, and it concentrates in the tail exactly as at NYISO:

| year | market | sum/max, all hours | hours cleared > $50 | sum/max there |
|---|---|---|---|---|
| 2023 | RT | 1.25× | 44 | **2.08×** |
| 2024 | RT | 1.25× | 72 | **2.20×** |
| 2025 | RT | 1.24× | 230 | **1.85×** |
| 2025 | DA | 1.30× | 47 | **1.96×** |

The summed values are in the committed record
`results/calibration/_miso171_reserve_product_decomposition.json` — e.g.
`da_foreseen/rt_mcp/total = $181.40` where the cleared price is
`reg = $76.88` (**2.36×**), and `scarce47/rt_mcp/total = $97.62` against
$46.44 (**2.10×**).

**Two mitigations, stated so MISO's lane can size this correctly.** The
per-product fields (`reg`, `spin`, `supp`) are recorded *alongside* the summed
ones and are correct, so the record is recoverable without a re-solve; and a grep
of `docs/` finds **no prose citation of any summed figure** — no finding,
calibration log or determination quotes `total` or `regspin`. This is a
defective field in a committed probe record, not (on the evidence here) a
conclusion resting on it.

**Repaired nothing.** Rule 25 `[R-ISO-SCOPE]`: a NYISO verdict never fills
MISO's cell. This enters MISO's lane as an open item, to be adjudicated on
MISO's own data by MISO's own session — which must also check the fields'
downstream use, a question this scan did not open.

### PJM, NEISO, CAISO, ERCOT — cleared, with evidence

* **PJM** carries the cascade (100.0000 % monotone, all three years) but nothing
  sums it. The sibling C3c probe `scripts/probes/c3c_q1_pjm_phantom_audit.py`
  pins a **single** product (`SERVICE = "PR"`) and explicitly documents the
  incremental-vs-total distinction in its `FAMILY_LOCALE` comment — *"the
  model's MAD family is the INCREMENTAL nested row, while the published MAD
  `mcp` is the TOTAL subzone price"*. `derive_pjm_ordc_overlay.py` validates
  each service's own maximum against its own penalty rung (SR/PR/30MIN as
  1×/2×/3× $850, Manual 11 §4.4.1) — per-product, never pooled.
* **NEISO** is the closest structural analogue (TMSR ≥ TMNSR ≥ TMOR) and is
  handled correctly *and deliberately*: `scripts/probes/_neiso76_reserve_content.py`
  uses **TMSR alone**, with the reasoning stated in its docstring — *"TMSR is
  the top of ISO-NE's cascade — a spin provider's price internalises the lower
  products"*. Model-side, `NEISO_RCPF_PRODUCTS` sums the three **demand-curve**
  prices, which is the correct half of the rule. (The RT/DA window CSVs are
  gitignored per that corpus's README, so NEISO's evidence here is code-level;
  an empirical monotonicity check needs a `--fetch`.)
* **CAISO**'s AS products are not a cumulative duration cascade (spin/non-spin
  clear as separate products; in the 2023 DAM sample non-spin is $0 throughout,
  so the ordering is degenerate rather than informative). The one place prices
  are added — `caiso_storage_as_revenue_phase0.py`, `sys_p + min(np_p, sp_p)` —
  is **nested-region** stacking (system + regional), the legitimate half.
  `_caiso71`'s `spin_evening + nonspin_evening` sums **MW requirements**, which
  are separately procured and do add.
* **ERCOT** publishes an independent MCPC per service; a resource providing RRS
  earns the RRS MCPC only. The sums that exist (`regup + rrs + ecrs` in
  `ercot102_as_holdout_attribution.py`, `derive_ercot_storage_as_products.py`)
  are **MW quantities** across distinct awards, which is correct. Not in this
  class.

## 6. The probe stays superseded

`scripts/probes/c3c_q2_nyiso_nyca_shortage.py` is untouched in substance: its
arithmetic is not fixed, its `SUPERSEDED` JSON key stands, and its frozen record
`results/calibration/_c3c_q2_nyiso_nyca_shortage.json` was not re-run. A finding
that documents a false positive ships with the construction that produced it.
Only a cross-reference to this verification and the cross-ISO scan was added to
its header.

## 7. Mechanism matrix — duty (a) discharged, no cell moves

`docs/codebase-site/data/mechanism-matrix/NYISO.js` checked. Nothing was tested,
armed or adjudicated and no `ScenarioConfig` field was added, so duties (b) and
(c) are not triggered and **no shard is edited**. The adjudicated cells stand as
read: `nyiso_ordc_measured_step_span` **K**, `nyiso_li_locational_reserve` **K**,
`nyiso_east_reserve_families` **I**, `energy_reserve_coopt` **K**.

## 8. Honest expected value

For NYISO this moves **nothing** and was never going to: it confirms a repair
that was already correct, and upgrades "the audit says nothing scored reads this
file" from a claim to a demonstrated fact. The one substantive addition is §5 —
a generalizable instrument rule stated on the provenance of the number, one live
sibling defect in MISO sized at ~2× in precisely the scarcity hours where a
C3c-class conclusion would be drawn, and four ISOs cleared with their evidence
rather than by assumption.
