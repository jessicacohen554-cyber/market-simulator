# PREREG — miso-147: HIGH-PRICE-HOUR DISPATCH COMPOSITION — what the model dispatches vs what MISO's units actually did

**Session:** miso-147, 2026-08-09, branch `claude/miso-147-dispatch-diagnosis-6in9hz`,
off `origin/main` at `772110b`. OWNER CHARTER 2026-08-09 (diagnosis-first): before any
further solves, diagnose the HIGH-PRICE hours/days — the dispatch-composition comparison at
the highest grain the data licenses. **§5.4 queue item 10, SET BY THIS SESSION** (the charter
states it explicitly does not displace items 8 and 9, which stand unmodified).

**This document is pushed BEFORE any adjudicating statistic is computed.**
Everything already read or computed at registration time is disclosed in §10 — the §0
re-verification, instrument availability checks (sidecar class vocabulary, CAMPD reporting
coverage, one dtype finding), and two keeper-config facts that fix the Q3 framing. No
stratum mask, no stratum mean, no composition delta, no trichotomy leg and no merit-order
clear has been computed.

**Solve posture: NO LP. NO SOLVE. NO KEEPER MOVE. NO `ScenarioConfig` FIELD. NO ARM. NO
CELL VERDICT MINTED.** This is a MEASUREMENT charter: it may name a successor lane; it may
not arm one. The single exception the charter licenses — ONE keeper replay for a unit-grain
MODEL question — is pre-committed in §6 to a trigger that this document fixes in advance,
and if spent it is registered the same session (rule 15). The expectation, stated now, is
that it is NOT spent: `fleet_state()` provides unit-grain model availability and marginal
cost without a solve, and the model dispatch questions here are class-grain.

---

## 0. The keeper's state, re-verified from committed artifacts

Re-verified in-session with `scripts/calibration_verdict.py --run-id
2026-08-05-miso-132b-cc-committed` (committed artifacts only, no re-solve, all three years
in ONE invocation), **not** taken from the charter:

* determination **NOT-YET**, rubric **3.1**, scorable years 2023, 2024, 2025;
* **sole FAIL C3a `price_mean`**: 2023 **−0.4 %** PASS (32.72 vs 32.85), 2024 **−6.0 %**
  PASS (30.37 vs 32.30), 2025 **−14.1 % FAIL, MODEL MISS** (39.05 vs 45.46); DA companions
  −4.4 / −8.4 / −15.8 % are SKIPPED diagnostics;
* **C3b PASS** all years: NRMSE **0.075 / 0.112 / 0.191** (2025 headroom 0.009);
* **C3c the sole ledgered caveat** (budget 1 of 1 — SPENT): model 0/6/0 h vs RT actual
  **30/37/88 h** >$200, ACCEPTED MEASURED-INPUT LIMITATION, all three years;
* C1 / C2 / C4 / C6 / C8 **PASS**; C8 ST_GAS grounded above budget at
  **31.9 / 33.1 / 45.1 %** with all binding mechanisms clearing D-4;
* C1 skips all eight classes in 2025 and C2 both families in 2025 on the **preliminary
  EIA-923 vintage** — the blocker year's fuel mix is **UNGATED**; any 2025 fuel-mix
  statement in this session is descriptive vs EIA-930 and labelled so.

The bundle's `metrics.json` is STALE (rubric 3.0, pre-v3.1 statuses) — the scorer is
authoritative, per the charter; this is stated, not re-discovered.

MISO holds **no** `calibration-complete` marker. Rule 22: 2023–2025 only. Nothing in this
document touches a year outside that span.

---

## 1. The object — the two 2025 miss components, and the one that has never been measured

The 2025 −14.1 % C3a miss decomposes (charter, from the keeper P1 sidecar + the miso-137
`*_lw` comparator) into a monthly structure with three facts this session is scoped by:
January and June 2025 are overwhelmingly tail-driven (16 and 21 of the year's 88 >$200
hours); July is the exception, with roughly half its miss in ordinary hours — and that
ordinary-hours summer object is the ONLY one miso-139…146 worked; and **May 2025 is
OVERPRICED (+12.4 %)** — any level device that closes June/July breaks May.

Every prior session in this lane measured the model's own stack (miso-142/143), the offer
corpus (miso-145/146), or instrument universes (miso-144). **None has compared WHO WAS
RUNNING, hour by hour, in the high-price hours — model vs reality.** That comparison is
this session's whole object, in four pre-declared strata, on three instruments whose
universes and bases are fixed in §2/§4 before any number. The output is an adjudication of
where the model's supply in those hours comes from that MISO's did not (and, in May, the
reverse), a first opening of the January object, and a named successor — never an arm.

---

## 2. Facts and definitions fixed BEFORE registration

**(a) The strata — built once, from the ACTUAL RT series only, never pooled.** Actual =
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet` RT (system reference =
INDIANA.HUB), densified to 8760 by `_miso137_c3a_gap_decomposition.actual_hourly` — the
committed C3a instrument. Per year y ∈ {2023, 2024, 2025}, on hours with finite actual:

* **S3 (tail):** actual RT > $200. Reported, NEVER gating, composition-only (§7 TRAP 2).
* **S2 (near-tail):** $100 < actual RT ≤ $200.
* **S1 (ordinary-elevated, PRIMARY):** actual RT ≤ $200 AND actual RT ≥ q90, where q90 is
  the 0.90 quantile (numpy linear interpolation) of the year's ≤$200 population — "top
  decile of hours with actual ≤ $200", the charter's words. Thresholds committed in the
  footing JSON. S1 and S2 can overlap; the overlap count is printed wherever both appear.
* **S0 (sign-reversal control):** ALL May-2025 hours (744), with the ordinary/tail split
  reported inside it. May 2023/2024 run as `MAYCTRL` — same mask, control label.
* "Ordinary" everywhere = actual RT ≤ $200 (boundary inclusive), the miso-146 G-F2
  convention.

**(b) One weight (TRAP 7).** Every stratum/window mean in this session is weighted by the
C3a weight — the keeper sidecar's own per-hour total demand
(`_miso143_stack.sidecar_price(year)[1]`), whose equality with the deriver's measured
demand weight was verified by miso-137 G-0 on the committed artifact. The `*_lw` comparator
is NOT re-derived (DO-NOT-REDO); the hourly actual series and the committed weight are
consumed as-is. An unweighted companion column may appear only as a labelled
non-adjudicating sensitivity.

**(c) The three instruments, their universes and bases — fixed here (TRAP 1, TRAP 4).**

* **MODEL (class grain, NET):** keeper P1 sidecars, `class_hourly_<y>.parquet` — verified
  17 klasses in all three years: CC_CHP, CC_REGULAR, COAL_BIT, COAL_LIGNITE, COAL_PRB,
  CT_CHP, CT_PEAKER, OTHER, ST_CHP, ST_GAS, biomass, hydro, **import**, nuclear, oil,
  solar, wind — plus `storage_<y>.parquet` and `system_<y>.parquet`. The model universe
  INCLUDES the ~17 GW of import tranches (miso-144's lesson); their capability is
  registered in G-F3 and named on every table that carries them.
* **ACTUAL, full universe (fuel grain, NET):** EIA-930 MISO BA,
  `eia930.actuals.load_eia_hourly_benchmark("MISO", y)` — coal, gas, nuclear, wind, solar,
  oil, hydro, other, battery, pumped_storage, net_gen, interchange (EIA convention:
  positive = net EXPORT). Covers everything CAMPD cannot; carries no unit identity.
* **ACTUAL, fossil subset (unit grain, GROSS):** CAMPD unit-level hourly,
  `data/raw/campd-unit-level/<ST>_<y>.parquet`, read DIRECTLY (never via
  `campd.load_campd_hourly`, whose facility-level preference would silently collapse IL
  and TX to facility grain), states from `campd.states_for_iso("MISO")`, restricted to
  `plant_id ∈ zone_assignment.build_zone_lookup("MISO")` — the repo's own canonical
  crosswalk (the pipeline's `_iso_plant_ids` path). One dtype fact found at availability
  check and fixed here: the raw parquet stores `facilityId` as **str**; it is cast to int
  before the crosswalk join (the reader's own `_normalize_campd` convention). Unit→family
  mapping via `bench_multiclass.unit_family(unitType, primaryFuelInfo)` → {CC, CT, ST_GAS,
  ST_COAL}. CAMPD is GROSS: every cross-side subtraction converts to NET via
  `campd.plant_hourly_net` with `compute_parasitic_factors` (the pipeline's own
  `_campd_hourly_frame` composition); GROSS is used only inside CAMPD-only state readings
  (ON/OFF, headroom), labelled at the point of use. **One basis per comparison, stated at
  the point of use — never mixed.**

**(d) CAMPD coverage, checked at availability time (disclosed §10):** per-month
reporting-unit counts are flat within quarters and NO month in 2023/2024/2025 falls below
95 % of its year's median (2025: 639/639/639/660/660/660/653/653/653/630/630/630). The
planned excluded-months guard therefore fires on ZERO months; CAMPD 2025 is complete
through Q4. Ever-ON MISO unit counts 582/573/563; MISO-filtered gross 438.5/439.9/451.2
TWh (raw-side availability totals, not an adjudicating statistic).

**(e) DA is never used.** Every price in this session is the measured RT actual or the
model's P1 price. The DA book, DART premia, and any DA-based statistic are out of scope.

**(f) Two keeper-config facts that fix the Q3 framing (read at registration, §10):** the
keeper's `meta.json` carries `miso_winter_citygate_daily: true` and `dual_fuel_switching:
true` **inside the replayed override channel** (the top-level `miso_winter_citygate_daily`
is false; the override channel is what `fleet_state` replays). The January candidates
"gas deliverability / citygate basis" and "dual-fuel switching" are therefore adjudicated
as **armed-but-possibly-insufficient**, never as missing mechanisms.

**(g) Import/interchange sits ONLY in the full-universe pair.** CAMPD has no import
analogue; the model's `import` klass is compared only against −(EIA-930 interchange), and
every fossil-subset table states that imports are outside its universe.

---

## 3. G-F — footing gates, checked AFTER this push and BEFORE any probe (HARD STOP)

* **G-F0 (the charter's monthly table, 2025).** The charter's monthly decomposition was
  measured at miso-146 from committed artifacts but **is itself committed nowhere in the
  repo** (verified by exhaustive search at availability time). The charter's numbers are
  therefore THE reproduction target, from the same committed instruments (keeper P1
  sidecar price/demand + miso-137 hourly actual, C3a weight), per month of 2025:
  * all-hours deficit ($/MWh): Jan **−9.44** · Feb **−2.99** · Mar **−1.73** · Apr
    **−2.24** · May **+4.22** · Jun **−17.36** · Jul **−17.88** · Aug **−3.49** · Sep
    **−8.81** · Oct **−2.70** · Nov **−3.15** · Dec **−5.50** — each to ≤ **$0.005**;
  * ordinary-hours deficit (actual ≤ $200): **−3.82 / +0.12 / +0.04 / −0.28 / +5.39 /
    −3.31 / −8.61 / −1.47 / −1.35 / −1.74 / −2.05 / −3.69** — each to ≤ **$0.005**;
  * hours > $200 per month: **16/4/4/4/3/21/13/5/8/2/3/5**, summing to exactly **88** —
    counts exact;
  * percentages (Jan −18.3 % … May +12.4 % …) reported with denominator = the month's
    C3a-weighted actual mean; a % mismatch > 0.05 pp with matching $ is a DENOMINATOR
    CONVENTION note (both denominators reported), never a bar move.
  One pre-registered disambiguation, fixed now: a month missing by ≤ $0.02 triggers a
  re-check of the ≤/< boundary convention at exactly $200 and of NaN-hour handling, with
  both readings reported — a disclosure, not a moved bar. A genuine miss ⇒
  `BRANCH-INSTRUMENT-FAIL`.
* **G-F1 (TRAP 7).** Reproduce miso-142/143's six committed window deficits on the single
  C3a weight — **−4.750 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435** (W1 = Jun+Jul
  h8–20 and JJA h12–17, × 2023/2024/2025) — to ≤ **$0.01**, reusing the miso-146 G-F1
  implementation, cross-checked against `results/calibration/_miso143_footing.json`.
* **G-F2 (the 88, footing-only).** The 2025 count of actual RT > $200 hours equals **88**,
  matching the C3c ledger's own committed footing (the `price_tail/2025` entry in the
  keeper attestation's `exceptions`). Used ONLY as an instrument cross-check; every S3
  reading downstream is a composition statistic, never the tail's price arithmetic
  (DO-NOT-REDO).
* **G-F3 (universe registration, TRAP 1).** Committed to the footing JSON before any
  subtraction: per year — strata hour counts and S1 thresholds; model fleet capability by
  klass INCLUDING the import tranches (from `fleet_state`, no solve); CAMPD MISO unit
  count and Σ p99-gross by family; the per-month coverage table of §2(d). Every later
  table cites these universes.

Any G-F failure ⇒ `BRANCH-INSTRUMENT-FAIL`: bars are NOT moved, the failed reading is
reported at full magnitude, and the instrument reports gaps only.

---

## 4. The instruments and decision arithmetic, fixed a priori

### 4.1 Pair A — model vs EIA-930, full universe, NET, bucket grain

Bucket map (asserted against the sidecar klass set at load; no unmapped klass may read
zero silently — the TRAP-4-of-miso-143 guard):

| bucket | model klasses | EIA-930 |
|---|---|---|
| coal | COAL_BIT + COAL_LIGNITE + COAL_PRB | coal |
| gas (merchant / CHP / total) | CC_REGULAR+CT_PEAKER+ST_GAS / CC_CHP+CT_CHP+ST_CHP / sum | gas |
| nuclear / wind / solar / hydro / oil | same-named klass | same |
| other_bio | OTHER + biomass | other |
| storage | storage sidecar (discharge − charge) | battery + pumped_storage |
| net_import | import | −interchange |
| demand (control row) | system sidecar Σ demand | Demand |

Per stratum the BA-identity residual |net_gen − Demand − interchange| (C3a-weighted mean)
is printed as the **noise floor**: no Pair-A delta smaller than it is asserted. The gas
row carries the standing BTM/CHP caveat (930's NG includes behind-the-meter CHP the model
holds out as btm steam). Universe statement on every table: model includes import
tranches and storage; 930 generation excludes imports (they sit in interchange).

### 4.2 Pair B — model fossil vs CAMPD families, NET, class grain

Family map: CC ↔ CC_REGULAR+CC_CHP · CT ↔ CT_PEAKER+CT_CHP · ST_GAS ↔ ST_GAS+ST_CHP ·
ST_COAL ↔ COAL_BIT+COAL_LIGNITE+COAL_PRB. Each table prints: model MW (NET), CAMPD MW
(NET via §2(c) parasitic conversion), Δ, own-side shares, unit counts (model: fleet rows
with in-stratum capability > 0, count + Σ pmax; actual: CAMPD units with grossLoad > 0,
count + Σ p99-gross), and the CAMPD coverage ratio (family NET ÷ 930 same-fuel MW, same
stratum) so the fossil-subset universe is stated on every row. The class split stays
inside CAMPD (TRAP 5): nothing here conditions on, or exports to, the masked offer corpus.

### 4.3 Q2 — the available / mispriced / absent trichotomy

Per fossil family F, stratum S, year — C3a-weighted means over the stratum's hours:

Model side (from `fleet_state(y)`, no solve): capability `AV_F = Σ pmax·availability`;
in-merit-at-the-REAL-price capability `E_F = Σ pmax·availability·1[mc_base ≤ actual_h]`;
dispatch `M_F` = sidecar family MW (NET).

Actual side (CAMPD, GROSS within this block, labelled): per-unit rating proxy `cap_u` =
the unit's own-year **p99 grossLoad** (p95 companion reported — the §5 named nuisance);
`ON_F` = Σ gross over units with grossLoad > 0; committed headroom `HR_F` = Σ max(0,
cap_u − gross) over ON units; recallable `OFF_cyc_F` = Σ cap_u over units OFF in-hour but
ON within ±24 h; dark `OFF_dark_F` = Σ cap_u over units OFF the entire calendar month.
System-grain bound: MISO_Forced + MISO_Unplanned (+ MISO_Derated, shown separately) from
`data/raw/miso-generation-outages/miso_outages_estimated_<y>.csv` on the stratum's days —
aggregate only, never class-attributed.

Decision on `Δ_F = M_F − A_F` (A_F = CAMPD NET mean), with the materiality floor fixed
now: **floor_F = max(300 MW, 0.05 · A_F)** — a neutral scale rule, not tuned to any
outcome; the same formula serves Pair-A buckets. For Δ_F > floor_F (model runs what
reality didn't): **leg (i) available-but-undispatched** iff Δ_F ≤ (HR_F + OFF_cyc_F)·pf_F
(pf_F = family parasitic factor, keeping NET basis), sub-split ≤HR (pure price-formation)
vs needing OFF_cyc (commitment); **leg (iii) absent-from-real-fleet** iff Δ_F > (HR_F +
OFF_cyc_F + OFF_dark_F)·pf_F, cross-checked against the outage-CSV bound; between ⇒
MIXED, both shares printed. For Δ_F < −floor_F (reality ran what the model didn't): model
availability deficit iff AV_F < A_F, else the model prices it out (E_F vs A_F — an offer
object). Rule 14 `[R-ACCURATE]` governs a leg-(iii) outcome: units genuinely OFF that the
model holds available is a measured availability defect, and the accurate input wins even
if the fit worsens — but per rule 13 the CORRECTION would be an availability INPUT with a
forward story, never a dispatch pin (§9).

### 4.4 Leg (ii) — dispatched-but-mispriced, identified by the marginal census

`_miso143_stack.clear_many` over S0/S1/S2 hours (S3 composition only), at BOTH bracket
endpoints (lo = `mc_base`, hi = mc_base + `markup_ceiling` — the miso-143 P0→P1
convention; verdicts must hold at both endpoints or be stated on the conservative side),
against the sidecar's own thermal requirement in each hour. **P-8 instrument gate** (§5)
runs first; a stratum failing it gets NO marginal reading, only the gap report.
Quantity-agree hours = hours where every Pair-B family satisfies |Δ_F,h| ≤ max(300 MW,
0.05·A_F,h). If the C3a-weighted price deficit in the quantity-agree subset persists at
≥ the P-3 bar, the object is offer level/slope — the miso-142 flat-stack / miso-145
missing-wall lineage, named as such, feeding queue item 9, not a new family.

### 4.5 Q3 (January 2025) and the S0 driver block — every candidate ×12 months, both signs

1. **Operating state:** CAMPD Jan tail-hour ON MW and ON-unit counts per family vs Jan
   non-tail hours, vs model M_F and AV_F in the same hours.
2. **Forced outage vs model availability:** outage-CSV Forced+Unplanned (+Derated shown
   separately) on tail days vs the model's implied thermal outage Σ pmax·(1−availability).
3. **Gas cost at the cold snap:** the gas-class marginal-cost distribution in Jan tail
   hours from `fleet_state(2025)` fuel prices (the citygate overlay is ARMED per §2(f) —
   the question is sufficiency) vs the marginal unit's mc in those hours (§4.4).
4. **Dual-fuel proxy:** CAMPD oil-primary vs gas-primary unit ON states in tail hours —
   labelled a proxy (CAMPD carries no hourly fuel-switch field).
5. **Winter reserve:** `reserve_family_2025.parquet` dual / shortfall_mw in Jan tail
   hours — did the model's winter reserve requirement bind at all?
Output: candidate table {gas_deliverability, dual_fuel, forced_outage_vs_availability,
winter_reserve} × {evidence, size, month pattern, sign consistency} — **named, never
armed**. The same ×12-month driver tables carry the S0 (May) block: model May
availability take vs reality's May outage take (the spring-maintenance hypothesis) and
the demand control (C3a weight vs 930 Demand), so Q4's drivers are read from the same
instrument that reads January's, both signs, no season-shopping (TRAP 8).

---

## 5. Predictions, with numeric bars fixed now

| id | prediction | bar | gating? |
|---|---|---|---|
| **P-1** | **Materiality.** In S1-2025 at least one fossil bucket/family shows \|Δ\| ≥ floor (§4.3 formula) on BOTH pairs where it exists; prior direction: coal, model > actual. Other side: every fossil \|Δ\| < floor in EVERY stratum ⇒ the composition gap is immaterial and the charter's close-branch fires. | floor_F = max(300 MW, 0.05·A_F) | **GATING** — selects the branch; this is the session's question |
| **P-2** | **Identity.** For the largest-\|Δ\| fossil family in S1-2025 the trichotomy resolves: leg (i) ≥ 60 % of Δ ⇒ dispatch/commitment object; leg (iii) ≥ 60 % ⇒ availability object. | 60 % | **GATING** — names the successor lane |
| **P-3** | **Persistence.** The C3a-weighted S1-2025 deficit in quantity-agree hours is ≥ 50 % of the full-S1 deficit ⇒ the offer/slope object persists independent of composition (miso-142/145 lineage). Other side: ≤ 25 % ⇒ the deficit rides on composition. Between ⇒ both objects, both reported. | 50 % / 25 % | **GATING** — the leg-(ii) alternative successor |
| **P-4** | **2025-specificity.** For every bucket material in S1-2025, \|Δ\| in S1-2023 and S1-2024 is ≤ 0.5 × the 2025 value. | 0.5× | **GATING for the scope sentence only** |
| **P-5** | **January (prior).** On Jan-2025 tail days, real Forced+Unplanned outage MW exceeds the model's implied thermal outage take by ≥ 2,000 MW; and model in-merit-at-real-price fossil capability exceeds CAMPD ON+recallable by ≥ 2,000 MW. | 2,000 MW | reported, not gating — candidate naming (Q3) |
| **P-6** | **May (prior).** In S0 ordinary hours the model's clearing offer at the lo endpoint exceeds actual RT by ≥ $3/MWh on the C3a-weighted mean, and the model's May thermal availability take is ≤ 0.5 × reality's May outage take (spring maintenance under-modelled). | $3 / 0.5× | reported, not gating — the sign-reversal control characterizes, it does not gate |
| **P-7** | **Tail echo.** The two largest S1-2025 fossil deltas keep their signs in S3-2025. | signs only | reported, **NEVER gating** (TRAP 2; charter: S3 may not motivate an arm) |
| **P-8** | **Instrument.** Per stratum (S0/S1/S2, each year), the lo-endpoint merit-order clear reproduces keeper P1: median \|p̂ − P1\| ≤ $4.00 and r ≥ 0.85 (the miso-143 bars). | $4.00 / 0.85 | **GATING (instrument)** — a failing stratum yields no marginal reading |

**Why P-1/P-2/P-3/P-8 gate and the rest do not, stated before any number:** P-1, P-2 and
P-3 test the object's existence and identity — they ARE the charter's question, and the §6
branches key on them. P-8 tests the instrument that P-3 and leg (ii) depend on. P-4 gates
only the "this is 2025-specific" sentence, which the scope of any successor needs. P-5 and
P-6 are candidate-naming priors for months this program has never studied — either can
fail for reasons external to the dispatch object (a demand-side January; a fuel-side May)
and their failure would itself be the finding. P-7 characterizes the ledgered tail, which
the charter bars from gating anything.

### Two-sided prior

**The prior:** the S1-2025 composition gap is real and material, led by coal (model >
actual) — the keeper's own promotion note names "the model still fills the seam/CHP/
ST_GAS night hole with cheap coal" — with leg (i)/commitment the dominant identity: MISO's
coal was committed away or cycling where the model's is free to run, i.e. the cheap supply
existed physically but was not offered/committed at the hours in question.

**The prior on the other side is not decorative, and on the evidence it is the more likely
outcome:** miso-142 measured the summer object as a supply-curve SLOPE defect with
quantities approximately right ($0.64/GW model vs $2.15 actual), and miso-145 found the
real book CHEAPER at matched position, not dearer. If that extends to S1, every fossil
|Δ| sits under its floor, P-3 lands high, and the verdict is BRANCH-OFFER-OBJECT — the
value of this session then being that it CLOSES the dispatch-composition family for the
level miss and hands the object to queue item 9 with the composition alibi measured.

**Most likely nuisance, named in advance:** the CAMPD p99-gross rating proxy. A unit
derated all year re-scales its own p99 and hides real headroom (HR_F too small ⇒ leg (iii)
inflated); a unit with rare peaks does the reverse. Counter-measurements: the p95
companion column on every HR_F/OFF_* table; the outage-CSV system bound as an independent
absent-capacity check; and Pair A, which carries no rating proxy at all — a leg-(iii)
verdict must be consistent with both before it is quoted. Second nuisance: the BA-boundary
mismatch (model import tranches vs 930 interchange; BTM CHP in 930's gas) —
counter-measured by the demand control row and the per-stratum noise floor (§4.1).

---

## 6. Pre-committed branches

* **`BRANCH-DISPATCH-OBJECT`** — P-1 passes and P-2 resolves leg (i). Successor named: a
  commitment/availability-of-cheap-supply lane (how MISO's real commitment kept cheap
  supply out of these hours and whether an admissible, forward-storied input reproduces
  it). OWNER DECISION; no arm here.
* **`BRANCH-AVAILABILITY-OBJECT`** — P-1 passes and P-2 resolves leg (iii), consistent
  with the outage bound and Pair A. Successor named: a measured-availability/outage data
  charter (rule 14 input correction with a forward story — e.g. class-level seasonal
  forced-outage rates re-derivable from multi-year GADS/CAMPD history), never a dispatch
  pin. OWNER DECISION; no arm here.
* **`BRANCH-OFFER-OBJECT`** — P-1 fails everywhere or P-3 lands ≥ 50 %. The dispatch-
  composition family is CLOSED for the level miss; the object returns to queue item 9
  (measured_offer_surface, unchanged constraints: cannot be class-conditioned, must
  replace-or-subsume `gas_offer_margin`, rule 19). This session adds the measured
  composition alibi item 9 currently lacks.
* **`BRANCH-NOT-A-DISPATCH-OBJECT`** (charter-mandated close): every fossil |Δ| < floor
  in every stratum AND P-3 ≤ 25 % — the tail is not a dispatch object and the charter
  closes with the composition question answered in the negative, at full magnitude.
* **`BRANCH-INSTRUMENT-FAIL`** — any §3 gate fails. Gaps only; bars unmoved.
* **Mixed outcomes:** S1-2025 (PRIMARY) decides the branch; S0/S2/S3 and January inform
  the naming and the caveats, never the branch.
* **Replay pre-commitment:** the ONE licensed keeper replay is spent ONLY if P-2 is
  INDETERMINATE at class grain — leg shares within ±10 pp of each other — AND the
  blocking question is unit-grain on the MODEL side (which model units carry the phantom
  MW). If spent: swap enabled first, single invocation `--years 2023 2024 2025`, zero
  deltas, registered the same session (rule 15). Otherwise the license lapses unspent and
  the FINDING says so.

---

## 7. Look-alike traps (charter numbering), each with its counter-measurement

* **TRAP 1 — THE UNIVERSE (miso-144).** *Counter:* G-F3 registers every universe (model
  incl. 17 GW import tranches; CAMPD fossil-only unit counts + Σp99; 930 BA totals)
  before any subtraction; every table states both sides' universes with MW and counts; no
  subtraction crosses universes (import only in Pair A; fossil-only tables say so).
* **TRAP 2 — THE 88-HOURS ARITHMETIC (DO-NOT-REDO).** *Counter:* the 88 appears only as
  G-F0/G-F2 footing cross-checks; every S3 reading is composition (who ran), never price
  arithmetic (how much short); P-7 is signs-only and never gates.
* **TRAP 3 — CEMS/DISPATCH BRIDGING (rule 13).** *Counter:* adjudicated in §9 BEFORE any
  candidate is named; no CAMPD quantity enters the LP, no per-unit model↔CAMPD join is
  built, and every successor is constrained to input-with-forward-story form.
* **TRAP 4 — THE INSTRUMENT CROSSING (GROSS vs NET).** *Counter:* §2(c) fixes the basis
  rule — NET via the pipeline's own parasitic conversion for every cross-side
  subtraction; GROSS only inside CAMPD-only state readings; the basis is printed at the
  point of use on every table.
* **TRAP 5 — CLASS BY THE BACK DOOR.** *Counter:* the class split lives entirely inside
  CAMPD (which carries fuel/unitType — legitimate HERE); the masked offer corpus is not
  read at all this session; no CAMPD class result is exported to it, and the miso-138
  refutation is not imported against CAMPD.
* **TRAP 6 — FIXING THE NUMBER.** *Counter:* no parameter of any kind is derived in this
  session; every bar above is fixed before measurement; a failing bar is reported at full
  magnitude (the miso-145/146 precedent); the floor formula is a neutral scale rule
  stated in §4.3.
* **TRAP 7 — WEIGHTS.** *Counter:* §2(b) — one weight (C3a's own) for every mean; G-F0
  reproduces the monthly table and G-F1 the six window deficits before any verdict.
* **TRAP 8 — SEASON-SHOPPING.** *Counter:* the strata are fixed in §2(a) before any
  reading; every candidate table (§4.5) reports all 12 months and both signs; May is a
  standing counter-case — any candidate that does not report its May effect is not
  quoted (charter: "a mechanism that does not report its May effect has not been
  measured").

---

## 8. Kill gates

No LP is solved and no mechanism is armed, so **no kill gate can be reached**. They are
restated so the claim is checkable rather than assumed: C3b-2025 NRMSE ≤ 0.200 (currently
0.191, headroom 0.009); C3a 2023/2024 stay PASS (−0.4 / −6.0 %); **May 2025 must not
worsen** (+12.4 % over — the charter makes this an explicit gate on any successor arm, and
every candidate here reports its May effect); C1/C2 stay PASS on gated years with 2025
UNGATED (preliminary EIA-923 — 2025 fuel-mix statements are descriptive vs EIA-930 and
labelled); C8 — no material class's forced share rises and no D-4 window breaks (ST_GAS
45.1 % grounded is the live escalation; floors are NOT this lane's lever, miso-144); C3c
ledger 1 of 1 SPENT — S3 is reported, never gating, and may not motivate an arm; **the
fail set must remain ⊆ {C3a}**. At the end of the session each is re-stated as
*untouched*, with the reason (no solve), not as *passing*.

---

## 9. Rule-13 admissibility, adjudicated in advance (TRAP 3 — binding on every candidate)

**The measurement is admissible.** Comparing the keeper's committed dispatch to CAMPD's
measured operating states and EIA-930's fuel series is a diagnosis of the model's supply
in specific hours; nothing it produces enters the LP, no `ScenarioConfig` field is added,
and no per-unit CAMPD series is joined onto a model unit as a target.

**What any successor may and may not be, fixed here:** pinning a unit or class to its
observed CEMS/930 generation, bridging commitment to CEMS states, or sizing ANY parameter
off the price/volume residual is a measured OUTCOME overlay — forbidden, and already
DO-NOT-REDO ("CEMS/dispatch bridging"). The admissible form is an INPUT correction with a
forward story (rule 14): a unit-availability input (e.g. seasonal/class forced-outage
rates derived from multi-year history, regenerable for a forward year and responsive to
changed conditions — the CEMS-emission-rate precedent) or a fuel-price input (e.g. a
citygate basis series extended by the same formula that already generates it). **The
admissibility test is the charter's: could the same quantity be produced for a forward
year from forward drivers, and would it respond to changed conditions?** If it cannot, it
is a finding, not a lever. Any offer-side successor additionally states how it replaces
or subsumes `gas_offer_margin` (armed, cell K) per rule 19 — never stacks.

---

## 10. Full disclosure — everything read or computed before this registration

**Read:** the owner charter (miso-147) in full; `PREREG-miso146-intermittent-screen-
2026-08-09.md` in full (the template); the §5.4 LIVE QUEUE stamp (miso-146) and items 8/9
verbatim in `docs/mechanism-testing-matrix.md`; `FINDING-miso145-offer-conduct-2026-08-09.md`
and `FINDING-miso146-intermittent-screen-2026-08-09.md` (headlines and committed numbers);
`FINDING-miso142-summer-stack-is-too-flat-2026-08-08.md` (the six window deficits' origin)
and `FINDING-miso143-…-2026-08-08.md` §footing (their 3-dp pinning);
`scripts/probes/_miso143_stack.py` and `scripts/probes/_miso137_c3a_gap_decomposition.py`
in full (the reused instruments); `scripts/lib/bench_multiclass.py` (unit_family /
unit_class_hourly); `src/market_sim/data/campd.py` (reader, ISO_STATES, plant_hourly_net,
parasitic factors), `src/market_sim/data/zone_assignment.py` (build_zone_lookup),
`src/market_sim/data/eia930/actuals.py` (load_eia_hourly_benchmark);
`data/raw/miso-generation-outages/_SOURCE.md` and the 2025 CSV header; the keeper
`meta.json` (two override-channel flags, §2(f)) and `calibration_attestation.json`
`exceptions` (the C3c ledger text and its 88-hour footing); `frontend/data/backcast/
keepers/MISO.json` (promotion note); `docs/calibration-log/miso.md` (miso-144/145/146
entries); CLAUDE.md in full. Codebase reconnaissance for this registration (file
inventories, schema/format identification, prior-session conventions) was performed by
read-only exploration subagents; everything they surfaced that this document relies on is
cited above.

**Computed (reference-side and availability only, no adjudicating statistic):**

1. **§0 re-verification** — `calibration_verdict.py --run-id
   2026-08-05-miso-132b-cc-committed` (text and `--json`), summarized in §0.
2. **Sidecar availability** — klass vocabulary per year (17 klasses incl. `import`,
   identical all three years), row counts (148,920 P1 rows/year), 8,760 distinct hours.
3. **CAMPD availability/coverage** — file inventory (34 states × 2018–2026, 2023–2025
   complete); the §2(d) per-month reporting-unit counts, ever-ON unit counts and
   MISO-filtered gross TWh; the `facilityId` str-dtype finding and its fix (§2(c)). No
   stratum restriction, family split, ON/OFF state reading or model comparison was
   computed.
4. **Outage CSV format** — header row and `_SOURCE.md` (daily, region × cause, aggregate
   grain, 366 rows for 2025).
5. **Environment** — venv creation, `pip install -e .` (×2), pandas 3.0.5 / pyarrow
   25.0.0 / numpy 2.4.6.
6. **Concurrent-session check at open** — zero open PRs; remote branches carry no other
   MISO session (ercot-181 and neiso-keeper-87 only).

**No stratum mask, no stratum mean or threshold, no composition delta, no trichotomy
leg, no ON/OFF state aggregate, no marginal-census clear and no window statistic beyond
the §0 scorer output has been computed at the time this document is pushed.**
