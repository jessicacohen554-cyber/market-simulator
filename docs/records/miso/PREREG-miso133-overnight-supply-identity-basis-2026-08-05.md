# PREREG miso-133 — the OVERNIGHT SUPPLY IDENTITY's two un-adjudicated rows: ST_GAS bench coverage and the CHP basis

Session miso-133, 2026-08-05, branch `claude/miso-133-calibration-ugnvvp`, off
`origin/main` at `bb01b7e5`. Keeper at entry:
**`2026-08-05-miso-132b-cc-committed`** (bundle `results/calibration/miso132_ccmin_B`),
determination **NOT-YET**, sole FAIL **C7 `COAL_PRB` 2025** (`cv_ratio` 0.338 vs the
0.50 gate; 2023/2024 pass at 0.505 / 0.524), ledgered caveats 2/3 {C3a, C3c}. MISO
holds **NO** `calibration-complete` marker — rule 22 `[R-HOLDOUT]`: **2023–2025 only**,
and this session neither solves, scores, nor READS 2022 / 2019 / 2026 data.

**This document is pushed BEFORE any adjudicating statistic is computed.** Nothing
below is sized on a measured Δ.

**Lane:** charter option (b) — the new-evidence lever screen on
`FINDING-miso130-c7-night-regime-2026-08-05.md` §4's overnight supply identity,
restricted to its **two un-adjudicated rows**. Charter option (a) is NOT taken and the
reason is recorded in §5. **NO LP IS SOLVED.**

---

## §0 Contamination disclosure — every number this session measured or read before writing this file

Read: CLAUDE.md; `docs/mechanism-testing-matrix.md` §5.4 stamps miso-132(b) /
miso-132(a) / miso-131 / miso-130 / miso-129; `FINDING-miso130-c7-night-regime-2026-08-05.md`;
`FINDING-miso127-overnight-gas-composition-2026-08-04.md` §1/§7;
`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §8/§9;
`scripts/probes/_miso127_overnight_gas_composition.py`;
`scripts/probes/_miso130_c7_night_regime.py`; `scripts/lib/bench_multiclass.py`;
`scripts/lib/backcast_artifacts.py`; `scripts/render_calibration_html.py::_btm_share`;
the keeper bundle's `run_config.json` and `hourly/` **file list**.

Numbers already in hand from those documents (none recomputed here):

* C7 `COAL_PRB` `cv_ratio` **0.505 / 0.524 / 0.338**, gate 0.50; 2025 needs ×1.479.
* miso-128 factorisation: `R_tot` 0.952, `R_dfrac` 0.354 — the defect is *organisation*.
* miso-130 §4 overnight supply identity, with each row's adjudication status:
  seam hole −1.0 to −1.5 GW (**SPENT**); `CC_REGULAR` ~−0.5 GW (trough volume **REFUSED**,
  miso-115); **CHP nominal −1.7 GW flat (BASIS-DISPUTED)**; **`ST_GAS` unmatched bench
  gap, size unknown (HANDED OFF)**. The last two are this screen's entire scope.
* miso-127-parallel §7a matched-share table: `COAL_PRB` 0.960/0.968/0.975,
  `CC_REGULAR` 0.931/0.935/0.954, `CT_PEAKER` 0.845/0.865/0.823,
  **`ST_GAS` 0.605/0.611/0.629** (7.5–8.3 TWh/yr unmatched), and its three named
  candidate causes (sub-CEMS units / bench-vs-LP class assignment / no bench entry),
  explicitly **not** adjudicated there.
* miso-127-parallel §7b: bench CHP series carry the whole-plant host-steam add-back,
  so CHP "coverage" computes to 1.45–1.78 and is not comparable to `class_hourly`.
* miso-127-parallel §1: on matched machines the model runs **less** overnight gas than
  the market in 3 of 3 years (−931.2 / −593.8 / −697.5 MW).
* miso-130 §5: model CC night 17.8–18.8 GW vs day 18.5–20.0 GW; the day-anchored
  night-off bridge pool is 3 plants/1,601 MW (2023) and **0/0** (2024, 2025).

**Structural facts this session measured before writing this file** (cardinalities and
schema only — no coverage, gap, level or shape statistic was computed):

* keeper payload `2026-08-05-miso-132b-cc-committed.js` carries **419** plant keys in
  each of 2023/2024/2025, of which **69 / 69 / 71** are `code:KLASS` slice keys;
* committed bench `frontend/data/backcast/bench/MISO/<y>.json.gz` carries **240 (2023) /
  237 (2025)** plant keys, of which **49 / 51** are slice keys;
* bench `group` census 2025: `CT_PEAKER` 94, `CC_REGULAR` 40, `COAL_PRB` 31, `ST_GAS` 23,
  `COAL_BIT` 15, `CC_CHP` 14, `ST_CHP` 9, `CT_CHP` 8, `COAL_LIGNITE` 2, `OTHER_FOSSIL` 1;
* the payload plant record carries **no class field** (`m`, `m_ann`, `m_mon`, `r`,
  `nrmse`, `cap`) — the class of a *bare*-keyed payload plant is available only from the
  bench `group` (bench plants) or the model's own fleet assembly (all plants). This is
  the construction fact that makes §1's model-side keying necessary and is why
  miso-127's bench-side iteration could not see the unbenched machines at all;
* the MISO dispatch fleet assembles at HEAD under the keeper's `run_config.json` in this
  container: 2,923 units for 2025, 1,891 carrying the `_p<code>_<suffix>` tranche form.

---

## §1 THE CONSTRUCTIONS — declared before measurement

All three read committed artifacts only: the keeper's registered payload, the committed
bench parts, the keeper bundle's `hourly/class_hourly_<year>.parquet`, and a **no-LP**
fleet assembly at HEAD under the keeper's own `run_config.json`.

### 1a. C-1 — the model-side class map (the thing miso-127 did not have)

miso-127 iterated the **bench** key set, so a model plant with no bench entry was
invisible to it by construction. This screen iterates the **model** side:

* payload key → `(plant_code, klass_or_None)` via `bench_multiclass.parse_key`;
* a `code:KLASS` slice key carries the model class directly;
* a bare key's class comes from the fleet assembly's plant → class map (unit-id class
  prefix over the assembled dispatch fleet, per year);
* a bare key that the assembly resolves to **zero** or to **more than one** class is
  **UNRESOLVED** — reported in its own bucket, never silently assigned.

### 1b. C-2 — the four-way decomposition of each model class's own energy

For model class `K` and year `y`, partition `Σ m_ann` over the payload keys whose model
class is `K` into exactly four disjoint buckets:

| bucket | definition |
|---|---|
| **M** matched | same key in bench, `group == K`, `campd` present, `nodata` false |
| **X** class mismatch | same key in bench, `group != K` (receiving-group histogram reported, MW-weighted) |
| **N** bench hole | same key in bench, `group == K`, but `campd` absent or `nodata` true |
| **U** unbenched | key absent from the bench entirely |

The denominator for coverage is the **full** model class from
`hourly/class_hourly_<year>.parquet` (P1), exactly as miso-127's P2 requires.

**Construction-validity residual, declared as a gate:**
`ρ = (M+X+N+U)/class_hourly_annual − 1`. A class with `|ρ| > 0.05` is **REPORTED but
NOT GATED** — its buckets are descriptive and carry no verdict (the miso-127 P2 pattern,
adopted verbatim so a payload/LP bookkeeping difference cannot masquerade as a finding).

### 1c. C-3 — the CHP grid-delivered basis

The comparable measured basis for a CHP class is the bench `campd` hourly series scaled
by `grid_frac = 1 − btm/e_ann` per plant, where `btm` and `e_ann` are **committed bench
fields**. This is byte-for-byte the same construction the report path already uses
(`render_calibration_html.py:2175`, `_grid_frac = 1.0 - _btm_share(...)`), so the fix is
a basis alignment to an existing committed quantity, **not** a new estimate and **not**
a free parameter.

---

## §2 THE PRE-REGISTERED BARS — declared before any of the above is computed

### S-1 — what the `ST_GAS` gap IS (primary class: `ST_GAS`; every gas class reported)

Let `G = X + N + U` (the unmatched model energy). Verdicts, on `ST_GAS`, requiring the
same verdict in **≥2 of 3** years:

* **H-X — BOOKKEEPING ARTIFACT:** `X/G ≥ 0.50`. Consequence if it fires: the `ST_GAS`
  row of the miso-130 §4 identity is **STRUCK** as an artifact of class assignment, and
  the class-grain gas statement miso-114 asked for is unblocked on a union-class basis.
* **H-U — NO BENCH COUNTERPART:** `U/G ≥ 0.50`. Triggers the follow-on **S-1b** below;
  no verdict is read from H-U alone.
* **H-N — BENCH-SIDE DATA HOLE:** `N/G ≥ 0.50`. Consequence: the gap is a bench build
  defect, owned by the bench chain, not by the LP.
* **MIXED:** none reaches 0.50. Then **no single verdict is taken**; the split itself
  becomes the lane's specification and is handed on as such.

### S-1b — if H-U fires, is "sub-CEMS threshold" a real explanation?

miso-127-parallel §7a called sub-threshold units "implausible on its own for machines of
this size" but never measured it. Bar, declared now: take the assembled model capacity of
the **U** plants (fleet assembly, no LP) and compute the share of that capacity on
plants whose assembled `pmax` is **< 25 MW** (the CAMPD Part 75 reporting threshold).

* `< 25 MW` share **≥ 0.50** ⇒ sub-threshold is **SUPPORTED**; the U machines are
  presumed real-but-unmeasurable and the identity's `ST_GAS` row is closed as
  *not determinable from CEMS by construction*.
* `< 25 MW` share **< 0.50** ⇒ sub-threshold **FAILS**; the gap escalates to a
  roster/crosswalk defect and is handed off as a named, un-chartered item.

### S-2 — the CHP basis

On the matched CHP machines, corrected annual coverage
`= Σ(campd × grid_frac) / Σ(model)`:

* lands in **[0.90, 1.10]** in ≥2 of 3 years ⇒ basis **RESOLVED**; miso-130 §4's CHP row
  is restated with a real signed MW number in place of "nominal −1.7 GW, basis-disputed";
* lands outside ⇒ basis **PARTIALLY RESOLVED**; the residual is named and quantified and
  the row stays disputed with that residual attached.

### S-3 — the restated overnight supply identity (the adjudicating statistic)

July, night = hour-of-day 0–5 (miso-130's own window), model − measured MW by class on
the corrected basis over the widest determinable machine set, with the `ST_GAS` and CHP
rows resolved per S-1/S-2.

**Pre-registered two-sided prior — the sign is genuinely unknown:**

* if the `ST_GAS` gap is **X**, miso-127's matched result stands and the model's
  overnight non-coal deficit **holds** (≈−0.6 to −0.9 GW), leaving miso-130's
  coal-fills-the-night root cause intact;
* if the gap is **U with S-1b supported**, the model is running gas the bench cannot
  see, the deficit **narrows**, and the root-cause narrative weakens;
* if the gap is **U with S-1b failed**, part of the model's overnight gas may be
  unverifiable capacity, in which case the deficit could **invert** on that slice — which
  would reverse the direction of any future lever built on it.

All three are reportable outcomes. **None of them closes C7**, and this pre-registration
does not treat any of them as a success condition.

### S-4 — the SLACK measurement, before anything is built (the miso-132(a) lesson, ungated)

Descriptive, never gated: the keeper's own July-night dispatch per gas class from
`class_hourly` against that class's assembled availability-scaled capacity — the
overnight headroom that any "add non-coal night supply" lever would have to work
through. **Coherence check, declared now:** if a class's keeper night dispatch exceeds
the probe's assembled available capacity, that class's headroom leg is marked
**CONTAMINATED** and is not relied on (exactly the miso-132(a) S-3 disclosure).

---

## §3 KILLS — pre-registered, in order

* **KILL-1 — nothing is sized on any Δ measured here.** No `ScenarioConfig` field is
  added, no arm is built, no run is registered, no keeper moves. Any lever this screen
  licenses is **NAMED, NOT CHARTERED** (the miso-130 precedent).
* **KILL-2 — no adjudicated cell is re-opened** (rule 28(a)): seam price/ceiling/floor
  classes, take-or-pay/period-budget/minimum-take, within-band slope, offer granularity /
  `smoothing_n`, reserve online-gating, self-commitment forcing removal, the CC committed
  band, `coal_mustrun_online_pmin`. No fitted trough adder, no 2025-specific lane.
* **KILL-3 — rule 22.** 2023–2025 only; no 2022 / 2019 / H1-2026 solve, score or read.
* **KILL-4 — standing inheritance.** Any future charter arising from this screen carries,
  from this document: C1 16/16, `COAL_BIT` no-overshoot, a declared D-4 binding window,
  LOYO within 2023–2025, a same-HEAD zero-delta control arm, and a two-grain firing proof
  (miso-126).
* **KILL-5 — construction gate.** A class with `|ρ| > 0.05` carries no verdict.
* **KILL-6 — no basis shopping.** The CHP `grid_frac` is taken from the committed bench
  `btm`/`e_ann` fields as-is. If the correction does not resolve the row, the residual is
  reported; no alternative add-back is searched for until one lands in [0.90, 1.10].

---

## §4 What would have STOPPED this lane

Declared for symmetry with miso-132 §1d: this screen would have been abandoned before
measurement if (a) the payload had carried its own class field, making miso-127's
bench-side iteration already model-complete — it does not; or (b) the bench had carried
no `btm`/`e_ann` fields, leaving the CHP basis unresolvable from committed artifacts — it
carries both; or (c) `ST_GAS`'s share of MISO energy had been immaterial — its unmatched
slice alone is 7.5–8.3 TWh/yr.

## §5 Why charter option (a) is not taken

Option (a)'s Form 580 count was attempted and found **not producible from a standard
session** one day before this one (`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`
§9, xiso-4, 2026-08-04): eLibrary exposes no machine surface, FERC's open-data catalog
does not carry Form 580, and the browser fallback is environment-blocked. This session
re-probed the one cheap discriminator — `elibrary.ferc.gov/eLibrary/docketsheet?docket=IN79-6`
returns the **same 22,464-byte SPA shell** — confirming §9 rather than re-deriving it
(rule 28(a) DO-NOT-REDO). §9's scheduling point is independent and decisive: the 2026
Form 580 covering CY2024–2025 is not due until **2026-10-30**, so the §2C bar ("≥15
plants AND ≥60 % of tonnage in EACH of 2023/2024/2025") **cannot** clear before late
2026 whatever the count returns. Option (a) is therefore blocked on environment for its
first half and on the calendar for its consequence; option (b) is taken instead. The
Michigan PSCR lead is left **unspent and unchanged** — it is not touched here, so a
future session inherits it intact.

## §6 Rule duties this session will discharge

Rule 15: **no run is produced** (no LP is solved), so there is nothing to register on the
dashboard; the deliverables are this PREREG, the probe, its JSON record and the FINDING.
Rule 28(b): the cells this screen touches are stamped in the same session, together with
the §5.4 queue stamp. Rule 22: 2023–2025 only. Rules 19/21/24/25: no mechanism is added,
no parameter is derived, no tuning channel is created, and every conclusion is MISO's
alone — the bench/payload construction facts are MISO-scoped and transfer to no other ISO
without that ISO's own measurement.
