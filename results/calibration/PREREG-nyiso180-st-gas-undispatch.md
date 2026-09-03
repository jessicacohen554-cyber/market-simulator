# PREREG — nyiso-180: why in-the-money `ST_GAS` goes un-dispatched

**Session:** nyiso-180, NYISO backcast-calibration track, 2026-09-03.
**Keeper:** `2026-09-02-nyiso-177-vintage-matched` (`results/calibration/nyiso177_vintage_B1p`),
determination NOT-YET, target grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**Object:** nyiso-179 §6.1 — 3.84 / 9.09 / 3.99 TWh a year of `ST_GAS` that the model's own
offer prices into the money at its own P1 zonal price and that it does not run
(aggregate `R` 0.767 / 0.522 / 0.740; median 0.775 / **0.448** / 0.816 against a 0.70 floor).

**This document is written and committed BEFORE any quantitative measurement of the corrected
ratio, of oil-class MW, or of any ramp binding.** §0 discloses, in full, everything already
established at the time of writing.

---

## 0. DISCLOSURE — everything measured or read before these gates existed

Eight structural reads were performed before this file was written. **All eight are code or
artifact-schema facts. None is a quantitative measurement of the object.** No corrected `R`, no
oil-class MW magnitude, no ramp-binding count, and no per-bin dispatch figure has been computed
or read. The gates below are therefore blind to their own outcomes.

| # | what was read | result |
|---|---|---|
| D1 | `model/lp/rows.py:1448-1465` — the `link_loss` energy-balance correction | Touches ONLY `layout._flow_off + lossy` (Flow) columns. Generator incidence stays `+1`. |
| D2 | `model/interchange/nyiso.py::apply_nyiso_zonal_loss_links` + `spec.py:2376` | Internal chain links only; seam/LCR mechanisms act on generators and are untouched. |
| D3 | `scripts/run_calibration_full.py::_system_frame:1063-1082, 1267-1282` | `price = prices[z] + total_overlay`; all three overlay terms init `None` and are assigned ONLY inside `if iso == "ERCOT":`. |
| D4 | keeper `hourly/system_<year>.parquet` **column list**, all 3 years | `[year, pass, zone, hour, price, slack, dump, demand, reserve_price]` — no `rtordpa_overlay` / `dam_as_overlay` / `ordc_adder`. 6 zones, `pass == P1` only. |
| D5 | `_dispatch_frame:349-460` | Non-ERCOT: `klass = plant_groups[g]` — the SAME field the nyiso-179 probe filters (`fa.plant_group == "ST_GAS"`). Pseudo-units are wind / solar / injected must-run residual classes ONLY. **AND: the dual-fuel re-attribution at `:455-457` overwrites `kcode` to `"oil"` for every (gen, hour) in `oil_switch_mask`.** |
| D6 | keeper `hourly/class_hourly_2025.parquet` **klass list** | `oil` IS present, alongside `ST_GAS`, `ST_CHP`, `CC_*`, `CT_*`, … |
| D7 | keeper `run_config.json` armed flags | `ramp_limits=True`, `nyiso_nyc_lcr_tsl=True`, `nyiso_li_lcr_tsl=True`, `nyiso_seam_deliverability_envelope=True`, `nyiso_local_selfsupply=True`, `nyiso_zonal_loss_surface=True`, `dual_fuel_switching` armed (nyiso-179 G2). |
| D8 | `data/raw/_processed-legacy/campd_ramp_envelopes_NYISO.csv` header + 5 `ST` rows | Artifact EXISTS: 48 `plant` / 26 `sparse` / 3 `class_fraction` rows. ST rows carry envelopes well below capacity (plant 2490: pmax 901 MW, `ramp_up` 390 MW/h). |

**What D1–D4 already settle, structurally, with no gate needed** (these are not claims a
measurement could overturn; they are call-site and ISO-gate facts of the kind nyiso-179 §7.6
used to adjudicate its own G0):

* **§6.1 candidate (a) — the loss surface — is REFUTED.** The loss coefficient is applied to
  the receiving-end incidence entry of lossy **Flow** columns. A generator's own energy-balance
  incidence is `+1`, unscaled. There is no `δ_z` on injection, so `mc ≤ price_z` is the correct
  *energy-balance* comparison for a generator in zone `z`, and the brief's proposed
  `mc ≤ δ_z × price_z` correction does not apply to generators at all.
* **§6.1 candidate (b) — a post-solve price transform — is REFUTED, twice over.** Structurally:
  all three overlay terms are ERCOT-gated, so on any NYISO run `total_overlay ≡ 0` and
  `price` **is** `result.prices[z]`, the raw LP energy-balance dual. On the artifact: none of
  the three audit columns is present in any year, and `_system_frame` writes each iff its
  overlay is not `None`.

**These two refutations are recorded as findings, not gates**, precisely because they were
established before this file existed. Nothing below depends on them being re-derived.

### 0.1 The premise this session inherits, and questions

nyiso-179 §6.1 reasons from: *"In a pure LP, capacity with `mc` strictly below its own zone's
dual and below its bound should run."* **D7 shows that premise does not hold on this keeper.**
An LP generator's optimality condition is its **reduced cost**

    rc[g,t] = mc[g,t] − price_{z(g)}[t] − Σ_r ( dual_r × coef of P[g,t] in row r )

which reduces to `mc − price_z` **only for a generator whose sole row is the energy balance.**
On this keeper `ramp_limits`, the NYC/LI LCR-TSL rows, the seam deliverability envelope and the
reserve shared-headroom rows are all armed, and each puts `P[g,t]` in additional rows whose
duals do **not** appear in the zonal price. A unit with `mc < price_z` can therefore sit below
its bound at a perfectly optimal, non-negative reduced cost.

**This is a correction to the object's framing, established by code reading (D7), and it is
reported as such — it is not scored by any gate below.** It is also why G2 is declared
one-sided in advance.

---

## 1. What is under test

Two live candidates remain. Each gets one gate.

* **(c) — a capacity/label-basis mismatch (D5, D6).** `class_hourly`'s `ST_GAS` `mw` is the sum
  of LP `P` columns whose `klass` code is `ST_GAS` **after** the dual-fuel re-attribution has
  moved every oil-switched (gen, hour) to `klass == "oil"`. The nyiso-179 numerator therefore
  **undercounts** `ST_GAS` dispatch by exactly the oil-switched MWh, while its `ITM`
  denominator counts every `ST_GAS` bin in every hour. This depresses `R` in the observed
  direction. `oil` is a POOLED class (any dual-fuel class relabels into it), so exact
  attribution needs per-unit dispatch — which is the session's other deliverable.
* **(d) — a binding LP row other than the energy balance (D7, D8).** Chiefly the armed
  `ramp_limits` plant-group hourly ramp envelopes: measured, two-sided, and (D8) materially
  below group capacity.

---

## 2. Gates

### G1 — (c), the oil-relabelling bound. **CAN FAIL, BOTH WAYS.**

Statistic and floor are **INHERITED from nyiso-179 and not chosen here**: the median hourly
ratio, floor **0.70**, plus the aggregate `Σ model / Σ ITM` reported alongside, exactly as
nyiso-179 reported both.

Let `ITM(t)` be nyiso-179's denominator, recomputed by the SAME `build_year()` instrument
(reused verbatim, per the brief). Define two EXACT bounds on the class's true dispatch:

* `N_lo(t) = ST_GAS_mw(t)` — nyiso-179's numerator. A strict LOWER bound (it omits every
  relabelled hour).
* `N_hi(t) = ST_GAS_mw(t) + oil_mw(t)` — a strict UPPER bound (it attributes the ENTIRE pooled
  oil class to `ST_GAS`, which over-credits by whatever CC/CT/ST_CHP contributed).

`R_lo` must reproduce nyiso-179's published 0.775 / 0.448 / 0.816 (median) to within 0.005 —
**an instrument check that CAN FAIL**; if it does not reproduce, the instrument is wrong and
G1 is recorded `INSTRUMENT FAILURE` with no verdict on the object.

**Verdict:**
* **`ARTIFACT`** iff median `R_hi ≥ 0.70` in **all three** years. The relabelling alone can
  arithmetically account for the signature; the un-dispatched-MW object is then substantially a
  measurement artifact of the numerator's class basis, not a dispatch defect.
* **`SURVIVES`** iff median `R_hi < 0.70` in **any** year. Then even crediting `ST_GAS` with
  100 % of the pooled oil class leaves the signature intact, and (c) is REFUTED as its
  explanation.

Reported alongside, not gated: the per-hour `ST_GAS` share of oil-switched capacity
`s(t)`, reconstructed from `resolve_fuel_prices`' own switch mask (zero solve), and the
resulting mid estimate `R_mid`. **`s(t)` is an estimate and is explicitly NOT allowed to decide
the verdict** — only the two exact bounds are.

### G2 — (d), the ramp envelope. **ONE-SIDED BY CONSTRUCTION. CAN ONLY IMPLICATE.**

Declared before running, and this is a limitation of the instrument, not a softened bar: the
ramp rows are **per (plant, CC/CT/ST bucket) group**, and the committed artifact is a **class
aggregate**. A per-group row can bind in an hour where the class aggregate is far from any
bound — the identical structure that made nyiso-113's K3/K4 gates invalid against
`system`'s summed `reserve_price` (CLAUDE.md rule 15). **A class-aggregate test can therefore
IMPLICATE the ramp rows but can NEVER exonerate them.**

Build the NYISO ST-bucket group envelopes with `build_ramp_groups` (zero solve). Let `RU_agg`
be the summed up-envelope over groups containing at least one `ST_GAS` member. Measure
`f = share of hours with Δ ST_GAS_mw(t) ≥ 0.95 × RU_agg`.

**Verdict:**
* **`RAMP-IMPLICATED`** iff `f ≥ 0.05` in any year.
* **`INCONCLUSIVE — PENDING SIDECAR`** otherwise. **This is explicitly NOT an exoneration**,
  and must not be reported as one.

### G3 — the row inventory. **REPORT, CANNOT FAIL.**

Enumerate, from code, every armed LP row family in which an `ST_GAS` `P` column carries a
nonzero coefficient on this keeper. Establishes the §0.1 correction concretely. Reported.

---

## 3. Deliverable D — the per-generator dispatch sidecar (the standing prerequisite)

Independent of every gate above. `class_hourly` is already a groupby of an existing per-unit
`dispatch/<year>_<pass>.parquet` frame (D5) that is gitignored, so the sidecar is an
aggregation choice, not new plumbing.

**Pre-declared scope:** a GENERAL sidecar under the existing `hourly/` writer in
`scripts/run_calibration_full.py`, never an `ST_GAS` special case. It must be sized before it
is built, and the size measured and reported. If the general per-unit-hour artifact is too
large to commit, the pre-declared fallback is the **per-(klass, band)-hour** aggregation —
which is what settles §6.1 — and the size of BOTH is reported honestly.

**Pre-declared honesty condition:** the sidecar changes what future sessions can measure. It
must NOT change the LP, any price, or any dispatch. Any keeper replay used to produce it must
reproduce the committed keeper's prices bit-identically, and that is checked and reported.

---

## 4. Stop conditions

* **S1 — G1 `ARTIFACT`.** The object is substantially a numerator-basis artifact. **No lever is
  opened.** The deliverable is the correction, the sidecar, and the matrix/queue update.
* **S2 — G1 `SURVIVES` and G2 `RAMP-IMPLICATED`.** The object is named as a ramp-envelope
  binding. **No lever is opened this session:** the envelope is a measured input and rule 23
  `[R-FROZEN-DERIVE]` re-derives only on a source-data or defect change, which no result here
  would supply.
* **S3 — G1 `SURVIVES` and G2 inconclusive.** The object stands unexplained. **No lever.** The
  sidecar is the deliverable and the successor's instrument.

**In every branch the answer is NO LEVER**, and that is pre-declared rather than discovered.
The brief's lane-level constraint is accepted as binding: 62.4 % of the 2025 top-decile deficit
is downstream of C3a-2025, which is owner-court. **If this work bottoms out against that wall,
the finding says so and stops. No lever will be manufactured in order to have shipped one.**

## 5. Governance

Rule 1 — no residual consulted in choosing what to measure. Rule 13 — nothing pinned to
actuals; measured series are comparison bases only. Rule 15 — a solve, if any, is registered.
Rule 16 — 2023 / 2024 / 2025 in one bundle. Rule 21/23 — zero parameters touched, nothing
re-derived. Rule 22 — training years only; NYISO holds neither marker and none is requested.
Rule 24 — no new tunable. Rule 25 — NYISO artifacts only. Rule 27 — no ≥300-line file
rewritten from response content.
