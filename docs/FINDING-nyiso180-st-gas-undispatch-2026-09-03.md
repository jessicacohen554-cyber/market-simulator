# nyiso-180 — all four candidate explanations for the un-dispatched in-the-money `ST_GAS` CLOSE, the object's inherited premise is WRONG, and the standing per-generator-dispatch limit is LIFTED

**Session:** nyiso-180, NYISO backcast-calibration track, 2026-09-03.
**Keeper: UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`** (bundle
`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target
grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**NO LEVER OPENED — pre-declared in every branch** (PREREG §4). No parameter
touched, no band swept, no arm built.
**Gates:** `results/calibration/PREREG-nyiso180-st-gas-undispatch.md`, committed
with the probe at `fbf93e50` **before either ran**, including its §0 disclosure
of the eight structural reads held at writing time.
**Machine artifacts:** `results/calibration/_nyiso180_st_gas_undispatch.json`
(gates) and `_nyiso180_ramp_report.json` (post-hoc report); probes
`scripts/probes/nyiso180_st_gas_undispatch.py` and `nyiso180_ramp_report.py`.

---

## 1. The one-paragraph answer

nyiso-179 §6.1 handed forward 3.84 / 9.09 / 3.99 TWh a year of `ST_GAS` that the
model's own offer prices into the money at its own P1 zonal price and that it
does not run, with three named candidate explanations and an instruction to rule
them out in order. **All three close, for zero solves, and a fourth that §6.1
did not name closes with them.** (a) The zonal loss surface is **refuted
structurally**: the `link_loss` coefficient is applied to the receiving-end
incidence of *Flow* columns, so a generator's own energy-balance incidence is
`+1` and there is no `δ_z` on injection at all. (b) A post-solve price transform
is **refuted structurally and on the artifact**: all three overlay terms in
`_system_frame` are ERCOT-gated, so on a NYISO run `price` **is** the raw LP
dual. (c) The capacity/label-basis mismatch is **real but far too small** — the
dual-fuel re-attribution does relabel `ST_GAS` MW into a pooled `oil` class, but
crediting `ST_GAS` with **100 %** of that class moves the median ratio only
0.775 → 0.775 / 0.448 → **0.448** / 0.816 → 0.821, so G1 reads `SURVIVES` on an
exact upper bound. (d) The armed `ramp_limits` envelopes — a candidate §6.1
never named, found by reading the keeper's own flags — cannot be the dominant
term either: the withholding is **sustained, not transient** (2024's longest
unbroken run is **2,650 hours**, 99 % of its withheld hours sit in runs longer
than 6 h) while every `ST_GAS` ramp group traverses cold-to-full in **1.5–3.0 h**.
**And the object's inherited premise is itself wrong:** with eleven mechanisms
armed, an LP generator's optimality condition is its **reduced cost**, not
`mc ≤ price_z`, so "in the money and below its bound" is not by itself an
anomaly. The session's durable deliverable is the **`class_band_hourly`
sidecar**, which lifts the nyiso-172 §2.5 limit that blocked three consecutive
sessions.

---

## 2. The instrument, and the check that had to pass before anything was believed

Zero solves. nyiso-179's validated `build_year()` is reused verbatim per the
brief — `lp_fleet` → `resolve_fuel_prices` → `assemble_mc` on the keeper's own
`run_config.json`. The dual-fuel switch mask needed by G1 is reconstructed
**exactly, with no re-derivation**: `apply_dual_fuel_pricing` writes
`min(gas, oil)` in place, so a switched generator-hour is precisely one where
the pre-min array exceeds the post-min array, and both arrays are already built
by `build_year`.

**The pre-registered instrument check (PREREG §2 G1) passes.** `R_lo` — the
no-oil numerator — must reproduce nyiso-179's published medians within 0.005 or
the gate is void:

| year | published (nyiso-179) | reproduced | |Δ| |
|---|---|---|---|
| 2023 | 0.775 | 0.775 | 0.0001 |
| 2024 | 0.448 | 0.448 | 0.0001 |
| 2025 | 0.816 | 0.816 | 0.0001 |

**One instrument premise was checked rather than assumed**, because getting it
wrong would have corrupted every ITM figure in both sessions: the committed
`system_<year>.parquet` carries **six** zones while `get_iso_config("NYISO")`
carries **five**. The probe maps a generator by NAME through
`zones[fa.zone_idx[g]]`, so it is correct only if the solve-time zone list keeps
the base five in order. It does: `apply_interchange_topology`'s `extend_node`
step **appends** the external zone (`spec.py:2176`, docstring "*append* the
ISO's external import/export zone"), leaving indices 0–4 untouched. The measured
`ST_GAS` zone distribution corroborates — NYC 3,525 MW / Capital_Hudson
2,879 MW / Long Island 2,349 MW / Upstate_West 150 MW, the known downstate
concentration, with none stranded in the external node.

---

## 3. (a) THE ZONAL LOSS SURFACE — **REFUTED, STRUCTURALLY**

§6.1 proposed that the correct test might be `mc ≤ δ_z × price_z`. **It is not,
and the proposed correction does not apply to generators at any magnitude.**

`build_constraints` applies the loss coefficient as a sparse subtraction whose
column indices are `layout._flow_off + lossy` — **Flow columns only**
(`lp/rows.py:1448-1465`). The comment states the mechanism exactly: it scales
"the RECEIVING-end incidence entry of each lossy one-way link from +1 to
`1 - link_loss[l, t]`". A generator's own incidence in its zone's energy-balance
row is `+1`, unscaled. `apply_nyiso_zonal_loss_links` confirms the same scoping
from the other end — internal chain links only, with the seam mechanisms, import
generators and every LCR/TSL cap explicitly untouched because they "act on
generators/availability rather than these links".

So the loss physics separates *zonal duals from each other*; it never stands
between a generator and its own zone's dual. `mc ≤ price_z` is the correct
energy-balance comparison. §6.1's bound ("a few percent, but not zero") was
generous: the right figure is **exactly zero**.

## 4. (b) A POST-SOLVE PRICE TRANSFORM — **REFUTED, TWICE OVER**

There **is** a transform in the writer — `price = prices[z] + total_overlay`
(`run_calibration_full.py:1282`) — so the candidate was not idle. But
`total_overlay` sums three terms (`rtordpa_overlay`, `dam_as_overlay`,
`ordc_adder`), **all three initialized `None` and assigned only inside
`if iso == "ERCOT":`** (`:1080`). On any NYISO run the sum is identically zero
and `price` **is** `result.prices[z]`, the raw LP energy-balance dual.

Corroborated on the artifact, independently: `_system_frame` writes each audit
column iff its overlay is not `None`, and **none of the three appears in any of
the keeper's three years** — the committed schema is
`[year, pass, zone, hour, price, slack, dump, demand, reserve_price]`.

## 5. (c) THE CAPACITY/LABEL-BASIS MISMATCH — G1 **`SURVIVES`**: real, and an order of magnitude too small

This candidate turned out to be a **genuine defect in the committed artifact**,
which is why it needed a gate rather than a code read. `_dispatch_frame:455`
overwrites a switched generator-hour's class code to `"oil"`, and
`dual_fuel_oil_reattribution = True` on this keeper. `class_hourly`'s `ST_GAS`
therefore **undercounts the class** by exactly the oil-switched MWh, while the
ITM denominator counts every bin in every hour — a bias in the observed
direction. `oil` is a POOLED class (every dual-fuel class relabels into it), so
the gate takes the strict upper bound: credit `ST_GAS` with **all** of it.

| year | mean ITM | mean `oil` | median `R_lo` | median `R_hi` (all oil credited) | aggregate `R_lo` → `R_hi` | hours with any switch |
|---|---|---|---|---|---|---|
| 2023 | 1,786 | 17 | 0.775 | 0.775 | 0.767 → 0.777 | 24 |
| 2024 | 2,141 | 48 | **0.448** | **0.448** | 0.522 → 0.545 | 72 |
| 2025 | 1,544 | 144 | 0.816 | 0.821 | 0.740 → 0.834 | 192 |

**G1 = `SURVIVES`.** Even the exact upper bound leaves 2024 at 0.448 against the
inherited 0.70 floor. Switching occurs in only **24 / 72 / 192 hours of 8,760**,
and the relabelled energy is ~1–9 % of the gap. The defect is real and worth
fixing on its own terms — §8 fixes it — but it is **not** the explanation.

## 6. (d) THE RAMP ENVELOPES — G2 `INCONCLUSIVE` by its own one-sided bar, and materially refuted as the DOMINANT term by the post-hoc report

Reading the keeper's armed flags surfaced a candidate §6.1 did not name:
`ramp_limits = True`, and `build_ramp_groups` puts NYISO's `ST_GAS` bins in
**11 measured two-sided plant-group hourly ramp envelopes**.

**G2 was declared ONE-SIDED before it ran** (PREREG §2), because the rows are
per (plant, bucket) group while the committed artifact is a class aggregate —
the identical structure that invalidated nyiso-113's K3/K4 gates against
`system`'s summed `reserve_price`. It reads
**`INCONCLUSIVE — PENDING SIDECAR`**: the class delta never reaches 0.95 × the
3,822 MW aggregate up-envelope in any year (max observed 1,449 / 2,278 /
2,085 MW). **That is NOT an exoneration and is not reported as one.**

**A post-hoc REPORT (`_nyiso180_ramp_report.json`, moves no bar, changes no
verdict) settles it on the merits anyway**, by asking the ramp hypothesis' own
question — is the withholding *transient*, as a ramp constraint implies, or
*sustained*?

| year | hours withholding >10 % | share of year | median run | **max run** | share of withheld hours in runs > 6 h |
|---|---|---|---|---|---|
| 2023 | 6,008 | 0.686 | 7 h | 137 h | 0.852 |
| 2024 | 7,911 | 0.903 | 16.5 h | **2,650 h** | 0.990 |
| 2025 | 5,144 | 0.587 | 5 h | 270 h | 0.814 |

Against that, every one of the 11 `ST_GAS` ramp groups traverses **cold-to-full
in 1.5–3.0 h** (median 2.39 h; up-envelope 0.34–0.65 of group capacity). **A
ramp row bounds the RATE of change, not the LEVEL.** It can hold a group below
its bound for a few hours after a step up in value; it cannot hold a roughly
constant ~1,000 MW level gap open for 2,650 consecutive hours, because doing so
would require the demanded trajectory to exceed the envelope every hour without
end. **The ramp rows are therefore not the dominant term**, whatever their
per-group duals do in individual transition hours.

## 7. THE PREMISE ITSELF IS WRONG — and this is the session's most durable correction

nyiso-179 §6.1 reasons from *"In a pure LP, capacity with `mc` strictly below its
own zone's dual and below its bound should run."* **That premise does not hold
on this keeper**, and it is why the object looked anomalous.

An LP generator's optimality condition is its **reduced cost**:

    rc[g,t] = mc[g,t] − price_z[t] − Σ_r ( dual_r × coef of P[g,t] in row r )

which collapses to `mc − price_z` **only for a generator whose sole row is the
energy balance**. The keeper arms eleven mechanisms (G3), and the honest
inventory of which ones actually put an `ST_GAS` `P` column in a row beyond the
balance is narrower than the flag list suggests — that narrowing is itself a
result:

| armed mechanism | does it hold an `ST_GAS` column below its bound? |
|---|---|
| `ramp_limits` | **YES** — 11 groups carry `ST_GAS` members (§6) |
| reserve shared-headroom rows | **YES in principle** — but nyiso-179 R2 measured families binding in only 21 / 11 / 38 h of 8,760 |
| `reliability_floor`, `nyiso_gas_commitment_bridge` | **NO — opposite sign.** Both are `min_gen` FLOORS, i.e. LOWER bounds; they push dispatch UP and *inflate* `R` (nyiso-179 R4 saw exactly this) |
| `nyiso_nyc_lcr_tsl`, `nyiso_li_lcr_tsl`, `nyiso_seam_deliverability_envelope` | **NO** — act on links / import generators, not on `ST_GAS` columns |
| `nyiso_zonal_loss_surface` | **NO** — Flow columns only (§3) |
| `local_capacity_constraints` | **NO ROWS** — `False` on this keeper |
| `hydro_dispatch_envelope` | **NO** — hydro units only |

So "in the money and below its bound" is **not by itself an anomaly**, and the
`R < 1` signature is not per se a defect. What *is* still unexplained is
narrower and better posed: **a sustained ~1,000 MW level gap, present in 59–90 %
of hours, whose only surviving named carriers are LP degeneracy at a price
plateau and the reserve rows** — the first of which nyiso-179's own R1 bounds
loosely (excluding capacity within \$5/MWh lifts 2024's median `R` from 0.448 to
0.678, so a large share of the gap IS thin-margin capacity) and the second of
which its R2 bounds tightly.

## 8. DELIVERABLE — the `class_band_hourly` sidecar (the nyiso-172 §2.5 limit, LIFTED)

Per-generator model dispatch was in **no keeper artifact in any ISO**. That
limit blocked nyiso-178's G1, nyiso-179's G1/G3, and was binding for a third
consecutive session. It is now lifted.

`hourly/class_band_hourly_<year>.parquet` carries
`(year, pass, klass, band, hour, mw, mw_oil)`. The per-unit-hour frame it
aggregates **is already written every solve** and merely gitignored, so this is
an aggregation choice, not new plumbing. It is general, not an `ST_GAS` special
case.

**Sized before it was built, as pre-declared (PREREG §3), on the real NYISO
fleet (478 LP generators, 11 bands, 6 plant groups, 35 distinct (klass, band)
pairs):**

| grain | rows / year | verdict |
|---|---|---|
| per-unit-hour | **4,187,280** | too large to commit, and grows with fleet size |
| **per-(klass, band)-hour** | **306,600** | committed — 13.7× smaller, and **bounded by classes × bands, not by fleet size**, so it stays committable in ERCOT/PJM where per-plant fleets are far larger |

**Two keys, because one is not enough.** `band` is the LP tranche suffix (the
last underscore token of `unit_id` — each a single token containing no
underscore, so the split is exact). `klass` is the **PRE-re-attribution** plant
group, carried through the unit-hour frame as a new `klass_base` column captured
before the dual-fuel overwrite — because `class_hourly`'s own `klass` cannot
serve, for exactly the reason §5 measured. `mw_oil` carries the re-attributed
portion, so the `class_hourly` view is exactly reproducible in both directions
and no information is lost.

Four regression tests cover the schema/band split, the pre-re-attribution
invariant, the `class_hourly` round-trip, and the older-bundle fallback (the
writer returns `None` on a frame predating `klass_base`, so replaying an older
bundle skips the sidecar rather than failing). **No LP row, price, or dispatch
value is touched.**

### 8.1 TWO CONSTRUCTION DEFECTS IN THE SIDECAR, both found before it was reported

Disclosed in the nyiso-179 §8 discipline. **In both cases the INSTRUMENT was
replaced and no threshold or claim moved** — neither defect touches a gate, and
the gate record (`_nyiso180_st_gas_undispatch.json`) was frozen before either
was found.

**(1) Caught by the test suite.** Wiring the writer into the *reuse* call site
broke two `tests/regression/test_reuse_solved.py` cases, whose fixture writes
1-byte dispatch stubs. The existing `class_hourly` writer is called only when
its output is absent and the fixture pre-stubs it, so it never read them; the
new writer did. **The writer's own docstring already claimed a fail-open
contract for a frame predating `klass_base`** — the fix extends that contract
to a frame that cannot be read as parquet at all, scoped to the schema probe
alone so a genuine aggregation bug still raises.

**(2) Caught by the artifact's OWN OUTPUT, on the first real NYISO year, before
any of it was reported.** The `band` column carried values like `Hudson`,
`GEN1`, `tie`, `scarcity`, `Ontario`, `01-8N`. Taking the last underscore token
is correct for a CAMPD-binned thermal tranche, but **most LP columns are not
tranches** — import pseudo-generators, hydro, wind/solar zone pseudo-units and
legacy equal-width bins carry ids whose last token is a zone name, a unit number
or a corridor label. The artifact reported **59 distinct "bands" and 893,520
rows** for one year against **11** real bands. `_tranche_band` now matches the
**closed vocabulary** instead (the same set as
`legacy_bins._coal_tranche_rank`), and a non-tranche column buckets to `""` so
the class aggregate stays exact. **Had this shipped unfixed, every future
band-level reader would have silently mixed real tranches with invented ones** —
the same class of silent trap as nyiso-179 PREREG §8.1's `econ_low`/`econlo`
vocabulary error.

## 9. Honest expected value — what is NOT delivered

* **The object is NOT explained.** Four candidates are closed; the sustained
  ~1,000 MW gap is not attributed. What the session delivers is a **correctly
  posed** question in place of a mis-posed one (§7), which is a smaller claim
  than an answer.
* **G2 is not an exoneration**, by its own pre-declared construction. The
  persistence report argues strongly that the ramp rows are not the *dominant*
  term; it does not show they never bind, and per-group ramp duals remain
  unmeasured.
* **The sidecar does NOT reach per-group grain.** `(klass, band)` settles
  band-level questions — which part of the offer stack ran — and was chosen
  because it is size-stable across ISOs. The `ramp_limits` rows live at
  (plant, bucket) grain, which this artifact **cannot** see. Naming that limit
  is part of the deliverable, not a caveat on it.
* **Nothing here moves C1-2023, C3a-2025 or C3c.** The keeper's determination,
  target grade and fail set are unchanged, and no gate here bears on them.
* **The lane wall stands and was not tested against.** nyiso-179 §7 puts 62.4 %
  of the 2025 top-decile deficit downstream of C3a-2025, which is owner-court.
  **This session bottomed out against that wall and stopped, as instructed.** No
  lever was manufactured in order to have shipped one.
* **The `mw_oil` correction changes no score.** It fixes an artifact's class
  attribution, not the LP; every metric in `metrics.json` is untouched.

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — no residual consulted in choosing what to measure;
  no mechanism adopted or rejected on whether it moved a fit.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals. No measured outcome
  entered any input.
* **Rule 14 `[R-ACCURATE]`** — no accurate input traded for an estimate.
* **Rule 19 `[R-ONE-MECH]`** — §7's inventory is this rule executed: every armed
  mechanism that could do the job was enumerated and adjudicated **before**
  anything new was contemplated. Seven of eleven were ruled out on sign or
  scope.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched.**
  The ramp envelopes, `THERMAL_AVAILABILITY`, every offer band and every hr-mult
  were READ and never written or swept. Nothing re-derived.
* **Rule 22 `[R-HOLDOUT]`** — every year read is 2023 / 2024 / 2025. NYISO is
  absent from both `complete` and `final`; **no marker was requested**; the
  holdout spend freeze is untouched.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable.** The sidecar adds an artifact
  column, not a knob; nothing it writes can change a solve.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only. No other ISO's tranche or outage
  artifacts read or written; only the NYISO matrix shard edited. The sidecar is
  ISO-agnostic by construction and carries no NYISO-specific logic.
* **Rule 27 `[R-PUSH]`** — `run_calibration_full.py` was edited in place (Edit
  tool / targeted local replace), never regenerated from response content, and
  the pushed blob is verified against local.
* **Rule 28 `[R-MECH-MATRIX]`** — cells annotated in §11.

## 11. Matrix (rule 28 b)

NYISO shard only. **No verdict moves**: `offer_curve_by_group` stays `K`,
`dual_fuel_switching` stays `K`, `zonal_gas_basis` stays `K`,
`gas_hub_basis_overlay` stays `K`, `st_gas_committed_measured_bypass` stays `.`.
`ramp_limits` is annotated with this session's evidence — it was **tested and
not adjudicated as a lever**, and its cell records the one-sided G2 plus the
persistence report.

## 12. Handed forward

1. **DO NOT re-open §6.1's candidates (a), (b) or (c).** (a) and (b) are
   structural refutations that no measurement can overturn; (c) is refuted on an
   exact upper bound. DO-NOT-REDO.
2. **`ramp_limits` is not the dominant term** (§6). Re-open only with per-group
   dispatch AND a mechanism for a *level* gap, not a rate one.
3. **THE OBJECT, RE-POSED (§7).** Not "why doesn't in-the-money capacity run" —
   that is not an anomaly under a reduced-cost condition — but **"what carries a
   sustained ~1,000 MW level gap in 59–90 % of hours"**. The two surviving named
   carriers are LP degeneracy at a price plateau (nyiso-179 R1: excluding
   capacity within \$5/MWh lifts 2024 from 0.448 to 0.678) and the reserve rows
   (nyiso-179 R2 bounds these tightly). **Degeneracy is the stronger of the two
   and is the one a successor should take first** — and note it would make the
   signature an artifact of the ITM statistic rather than a dispatch defect.
4. **THE SIDECAR IS AVAILABLE** for any run solved at or after this commit.
   Band-level dispatch no longer needs a replay. Its grain limit is per-group,
   named in §9.
5. **THE LANE STAYS BLOCKED ON C3a-2025.** Unchanged and re-affirmed.
6. **UNCHANGED and not opened:** C3c (SUPPORTING, not lone); the
   measured-availability family, the merit guard and an `ST_GAS` duty curve
   (nyiso-178 DO-NOT-REDO); `gas_st_startup_cost` (nyiso-172, two refusals);
   `gas_st_committed_hr_mult` (nyiso-179 G0, structurally unreachable); the
   missing rung.
