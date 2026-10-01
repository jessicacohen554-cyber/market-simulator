# FINDING nyiso-216 — 54034 Rensselaer's sign flip is a **zone** effect, but not the zone the question anticipated: the zonal **gas basis**, not the zonal LMP. `cc_reserve_duty_split`'s protection is `(2.25−1) × HR_base × F_local`, so it scales with the local fuel price — one cause for **both** halves of nyiso-215's "un-levelled" observation. The cohort is coherent in conduct and **MARGINAL on its own rule**

**Session:** nyiso-216, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-n1kwem`, on `main` at `71e62675`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **keeper unchanged; nothing promoted, armed,
screened or registered, no marker moved.**
**Pre-registration:** `results/calibration/PREREG-nyiso216-rensselaer-counterexample.md`, committed
and pushed at `1b3795e5` **before P1–P5 were measured** and not edited since.
**Machine record:** `results/calibration/_nyiso216_rensselaer_counterexample.json`.
**Instrument:** `scripts/probes/nyiso216_rensselaer_counterexample.py`.
**ZERO LP: no solve was spent.** Every fleet rebuild is `fleet_only=True`; every price is the
keeper's own committed P1 sidecar (rule 29(b) form 4 — **no control solve**). Nothing under
`results/calibration/` needs deleting before merge under 29(c).

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED** with **zero**
failing criteria across 2023–2025, C3c the lone ledgered caveat. Nothing below was selected because
a residual moved (rule 1 `[R-STRUCT]`); no residual was consulted at any point, and the 2022
held-out rung is named nowhere as a target (rule 22 `[R-HOLDOUT]`).

---

## 0. The result in one paragraph

nyiso-215 §4 named, and did not pursue, an intra-cohort counter-example: **54034 Rensselaer Cogen**
runs `cc_reserve_duty_split` the **opposite** way to the cohort's other six in all three years —
implied economic on-share 0.0038 / 0.0064 / 0.0098 against a measured online share of 0.0635, the
highest in the cohort — while the six over-run. This session asked whether that sign flip is a
**zone**, a **heat-rate**, or a **fleet-representation** effect. **It is a zone effect, and it is
not the zone channel the question anticipated.** The zonal **LMP** channel is excluded decisively:
a 2×2 swap of {54034, the capacity-weighted six} × {Capital_Hudson, Upstate_West} on the keeper's
own committed P1 prices puts **99.7 %–103.2 % of the gap on the cost leg in all three years**, with
the price leg **negative** every year (P2, §2). The driver is not the heat rate either — **my
pre-registered prediction was wrong**: 54034's base heat rate is **8.8975**, *below* the
cohort's capacity-weighted **9.1090**, so the heat-rate term is **negative**. The whole gap is the
**delivered fuel price** — `F_A / F_B = 1.75 / 1.61 / 2.10` — and it is not idiosyncratic to the
plant: **every** `gas_cc` unit in Capital_Hudson pays ~$5.23/MMBtu in 2025 against ~$2.21 in
Upstate_West (D4, §4). 54034 is an *ordinary Capital_Hudson combined cycle*; the cohort is six
Upstate_West plants plus one across a **2.4× zonal gas basis**. The unifying mechanism, verified as
a numerical identity to 1e-3 (D2): the class peak multiplier buys out-of-merit protection of
`(2.25 − 1) × HR_base × F_local`, so **protection is proportional to the local fuel price** —
$56.24/MWh at 54034 against $27.41 for the six in 2025. That is a **single cause for both halves**
of nyiso-215's "un-levelled" finding: over-correction where gas is dear, erosion where gas is cheap
and the price level has risen. On membership the answer splits: 54034's measured *conduct shape* is
cohort-like (**P5 COHERENT**), but on the rule's **own** statistic it is **above** the 0.10
threshold in 2025 (**0.11792**) — **P4 reads MARGINAL, my prediction of ROBUST failed**, and the
pooled 2023–2025 `duty_stat` of 0.0635 is what hides it. **Nothing is built, armed, sized or
recommended**; §7 hands the owner evidence for card (vii) and chooses nothing.

---

## 1. P1 — reproduction bar: **FIRES**, and the one LIVE G-DRIFT hunk is discharged by execution

Declared: for all seven cohort plants in all three years, the implied on-share reproduces
nyiso-215's committed record to **≤ 0.005 absolute** and `mc_peak` hour-mean to **≤ 2.0 %
relative**; **VOID** on any breach.

Measured over all **21** plant-years: **zero breaches**, maximum absolute on-share difference
**5 × 10⁻⁶**, maximum relative `mc_peak` difference **0.001 %**.

This is what discharges the single **LIVE** hunk of the G-DRIFT audit (§8): `data/eia930/actuals.py`'s
`_screen_fuel_spike_columns` (lane SPP-41) screens EIA-930 `NG:` unit-slip hours for **every** BA
and can therefore move the C1/C4 benchmark. On the quantities this session actually cites — the
NYISO fleet rebuild and its marginal costs — it is inert **by execution**, not by reading, and the
independent check agrees: `scripts/probes/nyiso196_rebuild_checks.py --year 2024` reproduced its
committed record **byte-identically** with `git status --porcelain -uno` **empty**. **This session
does not re-solve and does not re-score C1 or C4**, so the benchmark half of that hunk is passed
forward, not absorbed: a NYISO lane that re-solves or re-scores C1/C4 still owes it a check.

## 2. P2 — the swap decomposition: **FIRES, COST in 3 of 3**, and the zonal-LMP channel is excluded

`S(c, z)` is the share of the 8,760 committed P1 hours in which cost `c`'s `mc_peak` sits at or
below zone `z`'s LMP. `price_leg + cost_leg = G` identically by construction; the measured
`legs_sum_minus_G` is **0.0** in every year.

| year | S(A,CH) | S(A,UW) | S(B,CH) | S(B,UW) | **G** | price leg | cost leg | **r = cost/G** | class |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| 2023 | 0.00377 | 0.00228 | 0.17938 | 0.05042 | 0.04665 | **−0.00148** | 0.04814 | **1.0318** | COST |
| 2024 | 0.00639 | 0.00468 | 0.27256 | 0.20142 | 0.19502 | **−0.00171** | 0.19674 | **1.0088** | COST |
| 2025 | 0.00982 | 0.00822 | 0.72659 | 0.63057 | 0.62075 | **−0.00160** | 0.62235 | **1.0026** | COST |

**Verdict: COST, 3 of 3. The prediction holds.** The declared "hurts" limb — `price_leg ≤ 0` in
≥ 2 of 3 years — **also holds, 3 of 3**, and the declared *defeat* limb (`price_leg ≥ +0.10` in
≥ 2 years) does **not** fire: the price leg never exceeds **0.17 pp** in magnitude against cost legs
of 4.8 / 19.7 / 62.2 pp.

**The zonal-LMP channel is excluded in the strong direction, not merely the weak one.** `S(B,CH) >
S(B,UW)` in every year (0.179 vs 0.050; 0.273 vs 0.201; 0.727 vs 0.631): Capital_Hudson is the
**more** favourable zone to be priced into. Moving 54034 to Upstate_West would push it **further**
out of merit, not less. Whatever the sign flip is, it is not the zone's price distribution.

## 3. P3 — the cost driver: **my prediction FAILED, the "hurts" limb FIRED at full strength, and the gate VOIDS on its own identity bar**

Three separate outcomes, all reported as written and none restated.

**(a) The gate VOIDS.** The declared four terms — `HR`, `FUEL`, `OTHER`, `COV` — were required to
close on `Δ` to **< $0.01/MWh**. Measured residual: **$0.0079** (2023, closes), **$0.0017** (2024,
closes), **$0.0463** (2025, **does not**). *One year misses, so **P3 VOIDS on its literal terms.***
The terms the declared four omit are `assemble_mc`'s `nox_rate × nox_price` (54034's `nox_rate` is
1.2 × 10⁻⁴) and the post-assembly offer adjusters `run_calibration` applies after `assemble_mc` —
the 2025 run logs both a dual-fuel switching cap on 312 gas tranches and a gas offer net-revenue
margin compression. **This session did not isolate which of them produces the 2025 residual and
does not claim to have.** The residual is **0.09 % of Δ**; it cannot move a term measured at 106 %,
so the *measurement* below is robust by three orders of magnitude — but that is a statement about
the measurement, not a rescue of the gate.

**(b) The prediction failed.** I predicted **HEAT-RATE** in ≥ 2 of 3 years. Measured: **FUEL in 3
of 3**, and the heat-rate term is **negative** in every year.

| year | Δ | HR term | **FUEL term** | OTHER | COV | share HR | **share FUEL** | class |
|---|---:|---:|---:|---:|---:|---:|---:|:--|
| 2023 | 26.292 | −1.226 | **28.408** | −0.894 | −0.004 | −0.047 | **1.081** | FUEL |
| 2024 | 18.590 | −1.069 | **21.265** | −1.607 | −0.001 | −0.058 | **1.144** | FUEL |
| 2025 | 50.480 | −1.776 | **53.642** | −1.410 | −0.023 | −0.035 | **1.063** | FUEL |

**(c) The declared "hurts" limb fired — and not partially.** I declared: *"If the fuel term reaches
≥ 0.25 in any year, then part of 54034's out-of-merit position is a **zonal gas basis** effect — a
price-side story wearing a cost-side coat — which partially reinstates the zone as a cause even if
P2 reads COST."* It fires in **all three** years at **1.08 / 1.14 / 1.06**. The zone is not
partially reinstated; on the evidence of §4 it is the **whole** cause, reached through a channel
P2 was not built to see. **My preferred answer is defeated by a limb I pre-declared, and the
defeat is the finding.**

**Reported, not gated, exactly as declared:** the implied *base* heat rates (`HR / 2.25`) are
7784 **8.4209**, 50744 **8.5581**, 54592 **8.6749**, **54034 8.8975**, 54593 **9.4976**, 10621
**9.5487**, 10620 **9.7010**, against a capacity-weighted cohort **9.1090**. **54034 sits in the
middle of the cohort and 2.3 % BELOW its capacity-weighted mean.** Its physics is unremarkable.

## 4. D1–D2, D4 (POST-HOC DIAGNOSTICS, labelled): the object is the zonal gas basis, and the mechanism is an identity

**These moved no gate.** They were computed after P1–P5 and are labelled as such in the record.

**D4 — the fuel price is the zone's, not the plant's.** 54034 is `fuel_type = gas_cc`, the **same**
fuel type as all six others. Its 2025 delivered price of **5.0564 $/MMBtu** is exactly the
**minimum of its own zone's `gas_cc` population**:

| zone (2025) | n `gas_cc` units | mean $/MMBtu | min | max |
|---|---:|---:|---:|---:|
| **Capital_Hudson** | 64 | **5.2296** | 5.0564 | 5.5602 |
| Long_Island | 31 | 5.1864 | 5.0564 | 5.5602 |
| NYC | 61 | 3.7055 | 3.7055 | 3.7055 |
| **Upstate_West** | 80 | **2.2071** | 2.0966 | 2.5387 |

**54034 is an ordinary Capital_Hudson combined cycle.** The cohort's other six are all
Upstate_West. The run's own log states the channel: *"NYISO zonal gas basis (2025): 481 gas units
shifted by zone hub offset (min −3.08, max 0.00 $/MMBtu vs Capital_Hudson)"* — Capital_Hudson is
the reference hub and Upstate_West carries the discount. **The Capital_Hudson / Upstate_West
`gas_cc` ratio is 2.37× in 2025.** *(No claim is made here about NYC, whose mean sits below
Capital_Hudson's; a daily-series mean does not decompose into a single offset and this session did
not measure that.)*

**D2 — the mechanism is an identity, and it is verified numerically.** The class peak multiplier
buys out-of-merit protection of `(2.25 − 1) × HR_base × F_local`. Therefore

> **protection(A) / protection(B) = (F_A / F_B) × (HR_base,A / HR_base,B)**

| year | protection A | protection B (cap-wt) | ratio | fuel ratio | base-HR ratio | product | abs err |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | **36.449** | 21.346 | 1.7075 | 1.7479 | 0.9768 | 1.7073 | 2 × 10⁻⁴ |
| 2024 | **30.829** | 19.608 | 1.5722 | 1.6095 | 0.9768 | 1.5722 | 3 × 10⁻⁵ |
| 2025 | **56.237** | 27.410 | 2.0517 | 2.0995 | 0.9768 | 2.0507 | 1 × 10⁻³ |

Since the base-heat-rate ratio is 0.9768 and constant, **the protection ratio simply *is* the
fuel-price ratio.**

**This is one cause for both halves of nyiso-215 §4's "un-levelled" observation**, which that
session measured but could not explain and explicitly declined to attribute:

* **Over-correction at 54034.** Capital_Hudson gas is 2.1× Upstate_West's, so the multiplier buys
  2.05× the protection — $56.24/MWh — while the zone's LMP is only **1.10×** Upstate_West's
  ($59.49 vs $53.91). Cost outruns price and the plant leaves merit entirely (implied 0.0098
  against a meter of 0.1179).
* **Erosion across the six.** Upstate_West gas is cheap, so the multiplier buys only $27.41/MWh,
  and the zone's LMP level has risen **120 %** since 2023 — so the fixed cost offer is overtaken
  and the implied share runs to 0.63.

**A multiplier fixed in heat-rate space maps to $/MWh through the local fuel price, which varies
2.4× across NYISO zones and ~1.4× across the three years.** The mechanism is not mis-levelled in
one direction at one plant; it is **un-levelled along two axes, and both are the same axis** —
`F_local`.

## 5. P4 — membership on the rule: **my prediction FAILED. MARGINAL, and the "hurts" limb fired**

Declared: **ROBUST** if 54034's pooled online share and **all three** per-year shares are below
0.10, on `derive_reserve_duty_cc`'s **own** construction; **MARGINAL** if pooled is below but any
year is at or above; **FAILS** if pooled is at or above.

Measured, CAMPD on both sides, plant-summed, threshold `max(1.0 MW, 0.05 × pooled p99.5 HSL =
3.95 MW)`:

| | 2023 | 2024 | **2025** | pooled |
|---|---:|---:|---:|---:|
| 54034 online share | 0.04189 | 0.03085 | **0.11792** | 0.06353 |

**Verdict: MARGINAL. The prediction of ROBUST failed and the declared "hurts" limb fired.** On the
rule's own statistic 54034 is **above** the 0.10 threshold in 2025 — it is not a duty-role plant
that year — and `cc_reserve_duty_split` nonetheless routes its whole capacity to the peak band in
2025 regardless. The pooled 2023–2025 `duty_stat` of 0.0635 is exactly what conceals it. This is
the same pooled-denominator seam nyiso-215 §8 flagged from the other side (*"the cohort CSV's
`duty_stat` is a single pooled figure, so all of the ratio's year-to-year movement comes from the
model side"*) — here it moves the **membership**, not just the comparison.

**The verdict is basis-robust, and that was checked before any weight was put on it.** The
per-year share is identical (**0.11792**) whether the online threshold uses the derive's pooled
p99.5 HSL or 2025's own; and **CAMPD 2025 is complete — 8,760 hours for every cohort plant** — so
this is a measurement, not a partial-vintage artifact. It is deliberately **not** an EIA-923 number:
EIA-923 2025 is the preliminary vintage and returns 0.0 for these plants, which is *undefined*,
never a measurement.

**The reproduction bar reproduced**, as disclosed in the PREREG and claimed no credit for: the
nearest non-member above 54034 is 56188 Pinelawn at **0.1700**, so the 0.0635 → 0.1700 population
gap straddling 0.10 is real and the threshold is not knife-edge *on the pooled statistic*.

**D3 (post-hoc, beyond P4's declared 54034-only scope):** across all six CEMS cohort members,
**54034 is the only one that crosses the threshold in any year** — but the direction is shared.
**Every** member's 2025 online share is the highest of its three years, by 2.0× to 4.8×
(10620 0.0077→0.0195, 10621 0.0222→**0.0903**, 50744 0.0063→0.0541, 54034 0.0419→**0.1179**,
54592 0.0335→0.0667, 54593 0.0167→0.0460). **10621 reaches 0.0903 — within 10 % of the
threshold.** The pooled statistic understates 2025 duty for the *whole* cohort; 54034 is simply
the member where that first changes an answer.

## 6. P5 — behavioural coherence: **COHERENT on the declared limbs**, with an ungated statistic outside range and said so

Declared limbs, on CAMPD 2023–2025 pooled, against the range spanned by the **five** other CEMS
members (**7784 Allegany is excluded — it has no CEMS record**, which is why it is the cohort's one
`e923_pooled_cf` row; stated, not silent):

| statistic | 54034 | others' range | inside? |
|---|---:|---|:--|
| intensity when on (mean gross load ÷ p99.5 HSL) | **0.86537** | 0.77252 – 0.90782 | **yes** |
| mean run length (contiguous online hours) | **37.133** | 9.697 – 38.741 | **yes** |

**Verdict: COHERENT. The prediction holds and the "hurts" limb did not fire.** When 54034 runs, it
runs like its cohort — same loading intensity, same block duration. Its divergence is entirely on
the model side.

**Disclosed rather than absorbed:** a **third** statistic I measured and **reported but did not
gate on** — the pooled online share — **is outside** the other five's range: **0.06353** against
**0.01217 – 0.04695**. 54034 is the cohort's busiest member by a clear margin. I did not include it
in P5's classification, the classification stands as written, and I am not restating it; but a
reading of "coherent" that ignored it would be incomplete. Its mean run length, **37.133 h**, is
also inside the range only at its top edge (54592's 38.741 h). **The honest summary is: 54034's
conduct *shape* is cohort-like; its conduct *level* is the cohort's highest and, in 2025, outside
the rule.**

## 7. What this is evidence FOR — and what it deliberately does not decide

**It is evidence for nyiso-215 §6, the owner's pending card (vii)** — "should a duty-role cohort's
offer position be expressed in **cost** space (a heat-rate multiplier, as now) or in
**price-percentile** space?" — and it sharpens that card in one specific way that was not available
when it was written:

> nyiso-215 established that a cost-space multiplier erodes **across time** as the price level
> rises, and observed a sign flip at one plant it could not explain. This session shows the sign
> flip has the **same** cause as the erosion. Protection is `(2.25 − 1) × HR_base × F_local`
> (D2, exact to 1e-3), so it varies with the local fuel price — **2.4× across NYISO zones**, on top
> of ~1.4× across the three years. The cost-space basis is therefore not merely time-varying; it
> is **zone-varying**, in a market whose gas basis the model represents from measured data.

**And the measured input is not the defect.** A Capital_Hudson combined cycle genuinely does pay
more for gas than an Upstate_West one; the zonal basis is measured, and rule 14 `[R-ACCURATE]`
protects it. **Nothing here proposes to weaken, haircut or rescale it** — that would be the error
nyiso-212 already refused for `unit_outage_extract_basis_share`. The finding is about the
**mechanism's sensitivity** to a correct input, not about the input.

**Deliberately not decided, and deliberately not sized.** No successor form is built, armed,
screened, sized or recommended. In particular:

* **`2.25` is not moved** — nyiso-194 killed the CC_REGULAR peak band UP on shape, nyiso-195 killed
  the econ ramp DOWN to its `phys_*` basis on direction, `phys_peak == peak`, and rule 1's
  carve-out conditions are not met. A successor must give the duty-role cohort its **own** basis or
  route it elsewhere; this session names neither.
* **The seven pending owner rulings are untouched and none is prejudged**, cards (vi) and (vii)
  included. This session opens **no eighth card**: P4's MARGINAL verdict and D3's pooled-statistic
  observation are reported **into** card (vii)'s record, because the pooled denominator and the
  cost-space level are the same mechanism's two faces, and splitting them into a new card would
  invite the owner to decide one without the other.
* **Sizing invites choosing**, and the choice is not this lane's.

## 8. Governance, environment, and things found on the way

* **Rule 29 `[R-SCREEN]`:** step 0 only. **No screen, no control, no bundle, no LP.** Nothing to
  delete before merge under 29(c). **G-DRIFT** was audited hunk-by-hunk in the PREREG §3
  (`51f2fc2d` → `71e62675`, **14 files, +9,523 / −23** — three files more than nyiso-215 audited,
  and the new ones audited here rather than inherited): **thirteen INERT** with reasons stated per
  file (SPP/CAISO/ERCOT branches; CAISO 2022 rows; a default-off ERCOT flag absent from the
  keeper's recipe; the `capacity_screen_peak_measured_hindcast` flip, whose `__post_init__`
  coercion restores the frozen `False` for the keeper's `hindcast = False` config and whose
  consumer a `mode="backcast"` run never enters), **one LIVE** — `data/eia930/actuals.py` — and it
  is **discharged by execution**, not reading, in §1.
* **Rule 22 `[R-HOLDOUT]`:** training tier only — 2023–2025 meters and the keeper's own fleet and
  sidecars. **No out-of-training year was solved, scored or registered.** `complete` / `frontier`
  and the locked-test freeze are untouched; **2020/2021 stay unspent and were not this session's
  spend**; `final` remains never granted. No promotion contemplated, so D-5(b) does not attach.
* **Rule 15 `[R-DASHBOARD]`:** no run produced, nothing to register, keeper-only retention
  untouched.
* **Rule 23 `[R-FROZEN-DERIVE]`:** `derive_reserve_duty_cc.py` was **AUDITED, never re-derived** —
  no source data changed and this probe writes no derive artifact. P4's per-year shares are the
  derive's own construction applied one year at a time; the CSV is not rewritten.
* **Rule 28 `[R-MECH-MATRIX]`:** `cc_reserve_duty_split` is registered on the `offer_curve_by_group`
  base row; NYISO's shard cell is stamped in this session with this audit, failed predictions
  included.
* **Rule 25 `[R-ISO-SCOPE]`:** nothing crosses an ISO boundary. Every number is NYISO's.
* **Environment, measured at HEAD `71e62675`:** `data/clean` built with
  `curate_capacity_deliverability.py` + `curate_nyiso_interface_flows.py` only. Keeper `cache_key`
  **re-measured at this HEAD is `95d4d8d167373eb7`** (committed `solve_surface.fingerprint`
  `48353917f7510af3` at `git_sha 51f2fc2d`); no solve was spent, so it is recorded, not used.
  Test set run this session, **named rather than inherited** —
  `tests/scoring/test_gate_a_provenance.py`,
  `tests/unit/data/test_cc_summer_derate_reconciled_basis.py`,
  `tests/scoring/test_holdout_render_parity.py`, `tests/unit/data/test_campd_bins.py` —
  **75 passed, 0 failed**. `ruff format --check .` reads **1,405 files already formatted** and
  `ruff check` passes. **No pre-existing failure was found at this HEAD**, re-measured rather than
  inherited.
* **The stale-`metrics.json` trap nyiso-215 documented is unchanged and was not walked into**: the
  keeper bundle's committed `metrics.json` still reads `determination: NOT-YET` on a stale in-run
  "no governance attestation in bundle" reason while `scripts/calibration_verdict.py --run-id`
  returns **CALIBRATED**. It is systemic across six bundles in five ISOs and is **not repaired
  here** — out of this lane.
* **Still no unit test covers `cc_reserve_duty_split`'s split behaviour** (nyiso-215's finding,
  re-checked). This session does **not** add one, for the reason nyiso-215 gave and which P4
  strengthens: a guard encoding the *current* membership would now lock in a pooled-statistic
  defect this session has measured, not just the two-basis one nyiso-215 measured.

## 9. Reported at full magnitude

* **Two of five pre-registered predictions FAILED**, and both failures are the finding rather than
  a footnote: **P3** predicted HEAT-RATE and measured **FUEL, 3 of 3**, with the heat-rate term
  **negative** every year; **P4** predicted ROBUST and measured **MARGINAL**. Both of the
  corresponding "hurts" limbs — declared precisely so they could defeat my preferred answer —
  **fired**, P3's in all three years at 1.06–1.14 against a 0.25 bar.
* **P3 additionally VOIDS on its own identity bar** (2025 residual $0.0463 against a declared
  $0.01), and **the gate was not rewritten after the number was seen.** The residual is 0.09 % of
  Δ and cannot flip a 106 % term, but that is a statement about the measurement, not a rescue of
  the gate. **The source of the residual was not isolated and is not claimed.**
* **Every partition was checked exhaustive before the numbers were read, and every outcome landed
  inside one** — the defect nyiso-215 disclosed in its own P2 did not recur here.
* **P5's classification is COHERENT and a statistic I measured but did not gate on is outside
  range** (pooled online share 0.06353 vs 0.01217–0.04695). Disclosed in §6 rather than absorbed;
  the classification stands as written and is not restated.
* **P2's exclusion of the zonal-LMP channel is strong but it is an exclusion, not the answer.**
  P2's construction could not have seen the fuel channel — the cost side is a single scalar to it.
  The answer came from P3, which is the gate whose prediction failed. **Had P3 not been
  pre-registered with an exact-identity decomposition, P2 alone would have licensed the wrong
  conclusion — "not the zone" — and this session would have reported it.** That is worth stating.
* **The implied economic on-share is an upper bound** (nyiso-215's construction, reused unchanged):
  it ignores reserves, ramping, min-up and outages, and `mc_base` excludes the P1 startup markup.
  D2's protection figures are offer-side arithmetic, **not realised dispatch**.
* **`duty_stat` is pooled while every model quantity here is per-year**, so the P4/D3 comparison is
  the pooled statistic against per-year meters — which is exactly the seam §5 reports, and is
  stated rather than used silently.
* **Nothing here is dispatch evidence at plant grain.** Every dispatch number is class- or
  band-level from committed sidecars, or offer-side arithmetic. A plant-grain answer needs a replay
  this session did not spend, and nothing claimed requires one.
* **7784 Allegany is excluded from P5** for want of a CEMS record, and **54034 is boundary-clean**
  (nyiso-214's census) — so every measured-side statistic cited for it states its basis, per
  nyiso-214's boundary discipline.

*(nyiso-216, 2026-09-07. Zero LP. The gates were written and pushed before the census; three fired,
two failed their predictions and both declared "hurts" limbs fired, and one of those additionally
voided on its own identity bar and was reported as written. The object moved from "is the sign flip
a zone, a heat-rate, or a fleet-representation effect" — answered: a zone effect, through the gas
basis rather than the LMP, which was none of the three as I had framed them — to a single identity
that explains both halves of nyiso-215's un-levelled cohort, handed to the owner's existing card
rather than levered into a form.)*
