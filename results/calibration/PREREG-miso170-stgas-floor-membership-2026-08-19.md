# PREREG miso-170 — the laid-up-plant MEMBERSHIP repair for MISO's ST_GAS floors

**Committed BEFORE either arm solves.** Session miso-170 (2026-08-19), executing
the miso-169 §5 **ask 2** — *"adjudicate whether the rider's per-unit conduct leg
should gate sub-materiality plants, or whether the MISO ST_GAS floors need the
plant-membership repair the rider is pointing at."* This prereg takes the second
branch: the rider is **right**, the floors are **wrong**, and the repair is a
measured membership correction with zero free parameters.

Keeper under test: **`2026-08-19-miso-169-online-gated`** (`miso169_gated_B`).
Nothing is promoted by this document.

---

## 1. The defect, stated at the grain the instrument found it

The nyiso-143 D-4 **per-unit conduct rider** fails a floor mechanism when a
plant's *own meter* reads zero in at least half the hours that mechanism's floor
binds for it. On the committed MISO keeper it fires **18 times** across 8 plants
and 2 mechanisms:

| year | `reliability_floor × ST_GAS` | `st_gas_mustrun_per_plant × ST_GAS` |
|---|---|---|
| 2023 | 1104, 1891 | 1104, 1131, **1402**, 1702, 1891, 3992, 8054, 8056 |
| 2024 | 1891 | 1131, 8054, 8056 |
| 2025 | 1104 | 1104, 1131, 8056 |

C8 escalates ST_GAS to the grounded-above-budget path in every year (forced
share 32.7 / 34.4 / 46.2 % against the 30 % merchant cap), its D-1 shape leg
PASSES in every year, so **C8's whole failure is this provenance leg**.

The conduct predates the miso-169 mechanism: the bit-identical control fails
identically, and so would the predecessor keeper's dispatch if its diagnostics
were regenerated at HEAD.

## 2. The identification — one census, computed blind to D-4

The population is the **existing, unmodified** mechanism-blind lay-up census
(`scripts/data/derive_campd_bridge_layup_exclusions.py --iso MISO`, the nyiso-140
criterion verbatim): a plant qualifies iff its median CAMPD plant gross load is
**ZERO in every (year, 4-hour block) cell** of 2023–2025 — 18/18 cells. The test
reads only the meter and is computed **without reference to which plants the
floors force or to any D-4 verdict**.

**Result: 15 of 62 covered plants qualify; the nearest non-qualifier sits at
16/18.** Committed at `data/raw/_processed-legacy/campd_bridge_layup_exclusions_MISO.csv`
(+ `_population.csv` for the separation):

> 170 Lake Catherine · 203 McClellan · 992 C. C. Perry K · **1104** Burlington (IA) ·
> **1131** Streeter · 1464 Big Cajun 1 · **1702** Dan E Karn · **1891** Laskin ·
> 2123 Columbia · **3992** Blount Street · 6358 Hutchinson 2 (CC) · 6639 R D Green ·
> **8054** Gerald Andrus · **8056** Waterford 1 & 2 · 58478 LEPA 1 (CC)

**The census selects 7 of the 8 D-4-flagged plants without being shown any of
them.** That agreement is evidence, not fitting.

### 2a. Plant 1402 (Little Gypsy) is DELIBERATELY LEFT IN — named before the solve

1402 does **not** qualify (6/18 zero cells, pooled median 45.0 MW, P(on) = 0.506).
It is an ordinary **cycler**, which is exactly the population a measured operating
floor exists to reproduce — the NYISO plant-7314 case verbatim. Excluding it would
bury an offer/window error inside a membership list (rules 1 `[R-STRUCT]` /
14 `[R-ACCURATE]`), so it stays in, and **its 2023 D-4 row is pre-registered to
survive** (§4).

**Its defect is measured and named here as the successor, not repaired here**
(rule 19 `[R-ONE-MECH]` — do not bundle). The floor's window is the plant's
`online_frac` **pooled over 2023–2025 = 0.508**, while its own per-year metered
online share is **0.2495 / 0.6134 / 0.6548**. In 2023 the floor therefore commits
it across the top 50.8 % of system-load hours against a plant that ran 25 % of
the year — a ~2.3× over-commitment produced by the pooled vintage, not by
membership. **Named successor: per-year (not pooled) `online_frac` for the
per-plant must-run window.** It needs its own identification, its own A/B and its
own DOF answer.

## 3. Two mechanisms, two channels — why the charter's single channel is not enough

The session charter names the nyiso-140 `reliability_floor_plant_exclusions`
machinery. That machinery reaches **only the reliability floor** — 2 of the 18
failures. The other 16 belong to `st_gas_mustrun_per_plant`, which had **no
exclusion channel at all**. This is the nyiso-140 → nyiso-144 story exactly one
mechanism later (rule 19: *enumerate what already floors the same class*), so
this session ships **both halves**:

* **(a) reliability floor — existing machinery, data only.** The census is written
  into `data/raw/reference/reliability_floor_coeffs_MISO.csv`'s optional
  `exclude_plant_codes` column, **mechanically** (a new opt-in
  `--patch-reliability-coeffs` step on the census deriver, so the column can never
  drift from the census and a later coefficient re-derive cannot silently wipe a
  hand-typed list). Each limb receives exactly the laid-up plants carrying its own
  `(zone, plant_class)`; 19 of 78 limbs. **The first 17 columns of the CSV are
  byte-identical** — verified before the solve. Armed by the existing
  `reliability_floor_plant_exclusions`.
* **(b) per-plant must-run floors — one new gated flag,
  `ScenarioConfig.mustrun_plant_exclusions`** (default OFF, registered in the
  cache-key optional set + defaults ledger in the same commit; global default
  cache-key pin `603c2498bf71d21d` verified UNMOVED, the armed variant hashes
  distinctly). It reads the SAME census — lay-up is a property of the SITE, so one
  identification serves every mechanism that floors it — and gates **both**
  seams: the committed-tranche block and the `st_gas_mustrun_p25_level` block,
  which reads the measured artifact directly and would otherwise leave the
  correction silently inert on this keeper.

**Rule 21 `[R-DOF]`: ZERO new free parameters.** Both halves add a plant-code SET
produced by a conduct test; no scalar is introduced, swept or tuned.

## 4. Predicted effect — computed from the CONTROL's own committed rows, before the solve

D-4's per-plant `floored_twh` sums EXACTLY to D-2's per-mechanism `forced_twh`
(verified: 2023 `st_gas_mustrun_per_plant` = 7.7824 both ways), so the shed is
predictable from committed artifacts. Holding the rest of the dispatch fixed, the
15-plant census removes:

| year | reliability_floor | st_gas_mustrun | **total shed** | ST_GAS forced_twh | forced_share |
|---|---|---|---|---|---|
| 2023 | 0.0081 | 0.4963 | **0.5044 TWh** | 7.9595 → 7.455 | 32.7 % → ~31.3 % |
| 2024 | 0.0026 | 0.7505 | **0.7531 TWh** | 8.4275 → 7.674 | 34.4 % → ~32.3 % |
| 2025 | 0.0062 | 0.7791 | **0.7853 TWh** | 10.5208 → 9.736 | 46.2 % → ~44.3 % |

**ST_GAS therefore stays ABOVE the 30 % cap in all three years**, so C8 keeps
running through the grounded-above-budget escalation and the verdict keeps
turning on D-4 provenance — which is the point. This lever buys legitimacy, not
budget headroom.

**Expected price/volume movement: ~nil.** Every flagged plant is individually far
below the 2 % materiality line, and the shed energy is ~0.5–0.8 TWh against a
~24 TWh class.

**HONEST CEILING, stated before the solve: this cannot change the determination.**
C3a-2025 is a load-bearing FAIL closed by the miso-163 owner ruling as a
model-class limit. The run reads NOT-YET whatever C8 does.

## 5. Pre-registered gates

**K-0 — CONTROL INERTNESS (prerequisite, not a gate).** The control, solved on the
patched tree with the patched CSV and **both flags OFF**, must reproduce the
committed keeper **BIT-IDENTICALLY** on every scored sidecar of every year
(numeric max|diff| = 0, non-numeric equal). Any non-zero delta is a stop-the-line:
it means the code change or the CSV column is not inert at its default. The arm is
not read until K-0 passes.

**K-1 — MEMBERSHIP EXACTNESS (kill).** In the armed run's D-4 rows, **no** census
plant carries a `reliability_floor` or `st_gas_mustrun_per_plant` row in any year
(zero residuals), and **every** non-census plant that had a row still has one
(zero stray losses).

**K-2 — LIVENESS (kill).** The measured fall in D-2 ST_GAS `forced_twh` lands
within **±50 %** of the §4 prediction (0.5044 / 0.7531 / 0.7853 TWh). Far below ⇒
the exclusion never reached the mechanism (the "provably inert" failure mode);
far above ⇒ it removed more than the census.

**K-3 — CONDUCT FAILURES (kill).** D-4 per-unit conduct FAILs fall **18 → 1**,
the survivor being 2023 `st_gas_mustrun_per_plant` × plant **1402**, with **ZERO
new failures** on any mechanism, class or year. A new failure is a kill.

**K-4 — C8, the objective (not a kill, pre-declared both ways).** ST_GAS C8 reads
**PASS (grounded above budget)** in **2024 and 2025**. **2023 is pre-registered as
an EXPECTED FAIL** on plant 1402. If 1402's row also clears (its binding-hour set
can move under redispatch), C8 passes in all three years. **Under no circumstance
is 1402 added to the census to buy 2023** — that is the rules-1/14 line this
prereg exists to hold.

**K-5 — NO GATED FLIP (kill).** Over the full `calibration_verdict.py` output at
record grain, no (criterion, key, year) record flips PASS → FAIL. C1 / C2 / C3a /
C3b / C4 included.

**K-6 — SHAPE PRESERVED (kill).** ST_GAS D-1 `profile_r` ≥ 0.80 and `cv_ratio`
≥ 0.50 in every year — the gates C8's escalation reads. Removing mothballed-plant
forcing must not break the class's diurnal shape; if it does, C8 fails on shape
even with clean provenance, and the correction would have traded one defect for
another.

## 6. Decision rule

* **K-0 fails** → stop the line, fix the inertness defect, nothing is registered
  as a candidate.
* **Any of K-1 / K-2 / K-3 / K-5 / K-6 fails** → the arm is REJECTED, registered
  as a rejected probe (rule 15), and its cell recorded `R` with the failing gate.
* **All kills silent** → the arm is a **candidate keeper on rule 1
  `[R-STRUCT]`**: it stops manufacturing ~2.0 TWh over three years at plants whose
  own meter says they were mothballed, at zero DOF and with no fit claim. The
  determination stays NOT-YET either way (§4), so the promotion recommendation
  rests on structural fidelity alone — exactly the standing owner posture *"if
  structural integrity improves but gates regress that may still be a keeper."*
* **K-4's 2023 branch** is reported as-measured and never re-litigated by moving
  the membership test.

Both runs are registered (rule 15), all three years in one invocation each
(rule 16), 2023–2025 only (rule 22 — MISO holds neither `complete` nor `final`).
