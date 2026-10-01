# FINDING — ercot-216 (Phase-0, read-only): the C3c ledger's OPEN RESIDUAL LANE is **SPENT ON BOTH NAMED CANDIDATES AND MEASURED EMPTY ON THE CURRENT KEEPER** — at the missed tail hours the model reproduces ERCOT's own physical dispatch fuel-by-fuel (max |Δ| 1.4 GW of 72.5 GW; storage within −102/+181 MW of measured BAT) while ERCOT's SCED λ cleared 3–5× higher with RTORPA ≈ $1 and 5.7–7.7 GW of PRC. No admissible lever exists; **Phase-1 NOT entered**, keeper UNCHANGED

**Session ercot-216, 2026-08-17, branch `claude/ercot-216-next-lever-c65bif`.**
Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json` at
session start AND end: **`2026-08-17-ercot215-arm-decontam`** — UNCHANGED;
determination NOT-YET, fail set {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c
the ledgered CAVEAT ×3 (68/181, 22/53, 1/31). **Phase-0 READ-ONLY as
dispatched: no LP, no solve, no year scored, no run registered, no bundle
modified, no `ScenarioConfig` field, no matrix cell verdict minted** (the
ercot-163/170/208/214 no-LP precedent). No precommit was pushed because **no
solve was reached** — the pre-solve gate is what this session did not pass.
Committed probe: `scripts/probes/ercot216_c3c_lane_phase0.py` →
`results/calibration/ercot216_c3c_lane_phase0.json`. Everything below is read
from the keeper bundle's committed `hourly/` sidecars, the committed actual-RT
parquet, the committed NP6-905 ORDC curation, the EIA-930 ERCO extract and the
committed 15-minute RTM settlement-point workbooks — no new data, no measured
input touched.

## 0. VERDICT

The dispatch charters this session **off the closed 2023 price criteria**
(R-A) and onto *"the C3c ledger's own open residual lane — a mechanism that
lands there PASSES C3c on merit and sends the caveat inert"*, naming its two
candidates: **(a)** the AS-vs-energy split of storage capability at scarcity
and **(b)** the CC headroom/capability identification. Measured against
committed artifacts, that clause — carried verbatim on every ERCOT keeper
attestation since 2026-08-05 — is **stale in both limbs**, and the object it
points at is **empty on the current keeper**:

1. **Lane (a) is BUILT, ARMED AND SPENT** (§1). The mechanism the clause names
   is `ercot_storage_as_soc_reserve`, built and A/B-tested at ercot-167,
   promoted to keeper the same day, and its standing re-gate **DISCHARGED
   RG-PASS at ercot-193**; it rides armed on this keeper alongside the whole
   measured-award family. It has **no room left on the object**: at the C3c
   missed hours the model's battery net output is **−102 MW (2024) / +181 MW
   (2025)** against the measured EIA-930 BAT series.
2. **Lane (b) is CLOSED BY A SIGNED RULE** (§2). The CC headroom crosswalk was
   `FILED-UNLICENSED` at ercot-170 (L1 0.3375–0.5111 vs a 0.90 bar) and again
   at ercot-191 on the repaired deriver (**L1 0.3857 FAIL**), which triggered
   the card-Q checkpoint **(Q-B) AUTOMATIC AND FINAL — item 11 CLOSED**.
3. **The residual is not a quantity object at all** (§3). At the missed hours
   the model reproduces ERCOT's measured physical dispatch fuel-by-fuel —
   2023 gas −1,412 MW, coal +378, nuclear −7, renewables +504 on a 72.5 GW
   system, with model demand equal to the 930 generation sum to **0.6 MW** —
   while ERCOT's **own SCED system λ** cleared at p50 **$456.81 / $272.07 /
   $278.53** against the model's **$96.65 / $70.92 / $89.61**, with published
   **RTORPA p50 $0.84 / $1.58 / $0.00** and **PRC p50 5,708 / 6,197 /
   7,727 MW**. Same MW, no reserve scarcity, 3–5× the price: the whole gap is
   in the **energy offer at the clearing point**.
4. **Both mechanism families that could close it are adjudicated shut**, and
   the third route is not a mechanism (§5): offer conduct above marginal cost
   → Door A CLOSED (ercot-211, transfer measured NOT-TRANSFERABLE; storage
   model-free); merit-order depth → item 11 CLOSED on licence, with the
   per-hour telemetered-HSL cap form rule-13-forbidden (ERCOT-159/163);
   hourly resolution → rule 8 `[R-8760]`, quantified in §4 and not a lever.
5. **Phase-1 NOT entered.** No lever is proposed, none is built, and none may
   be built on this record. C3c stands as the ledgered model-class caveat —
   now on a measurement taken on the current keeper rather than an inherited
   exhaustion record.

By-product, reported because it changes numbers other sessions may cite: two
**clock defects in the instrument layer** were found and repaired (§6). They
are probe-side only — no LP input and no scored criterion rides them — but
uncorrected they are GW-scale in exactly this comparison.

## 1. LANE (a) — the storage AS/energy split is armed, and it is empty on the object

**Armed state, read from the keeper's own resolved config**
(`ercot215_decontam_B/run_config.json`):

| flag | keeper |
|---|---|
| `storage_as_commitment` (award POWER reserved off the discharge cap) | **true** |
| `ercot_storage_as_soc_reserve` (award ENERGY reserved — the ercot-162 §2 successor) | **true** |
| `ercot_storage_as_deployment` / `ercot_storage_as_reserve` / `ercot_storage_as_product_credit` | **true** |
| `ercot_storage_capability_measured` | **true** |
| `ercot_storage_rt_offer_surface` | false (`R`, ercot-162) |
| `ercot_storage_as_endogenous` / `ercot_storage_as_duration_gate` | false (forward-lane pair; mutually exclusive with the measured path, rule 13) |

The clause's own words — *"how much of the fleet's telemetered capability is
truly available to energy at the gap hours after its real AS commitments"*
(`FINDING-ercot162` §4) — describe `storage_as_commitment` (power) +
`ercot_storage_as_soc_reserve` (state of charge). Both halves are armed;
ercot-167 built the second one against exactly this object (scarcity-hour
battery discharge 666 → 520 MW against the SCED-measured 423), the owner
promoted it on the standing structural standard, and the standing re-gate was
executed and **DISCHARGED RG-PASS** at ercot-193 on the original gates
verbatim.

**And the object has no room left.** At the C3c missed hours (the hours the
caveat is about), model battery net discharge vs the measured EIA-930 ERCO
`BAT` series:

| year | model net MW | measured BAT MW | Δ |
|---|---|---|---|
| 2023 | 503.5 | — (BAT reporting starts 2024-11-06) | — |
| 2024 | 1,805.0 | 1,907.0 | **−102.0** |
| 2025 | 2,555.4 | 2,374.6 | **+180.8** |

A further AS-vs-energy re-split can only move the model's battery output; it
is already within ±8 % of the measured fleet in both years where a measured
series exists. There is no MW there to buy, in either direction.

## 2. LANE (b) — the CC headroom identification is closed by a signed rule, not by opinion

* **ercot-170 (2026-08-05).** The ~2.7 GW CC headroom object CONFIRMED as a
  *capability* object (attribution identity closes to **0.0000 GW**, term A =
  **102.4 %** of the gap), and the per-unit SCED-train ↔ model-unit crosswalk
  **FAILS its pre-registered licence in both legs** (L1 0.5111, 0.3375 on the
  defensible tiers, vs 0.90; L2 0.1829 vs 0.10) → `FILED-UNLICENSED`, no arm
  nameable, re-pointed to **data intake**.
* **ercot-191 (2026-08-12).** Re-tested on the repaired DAM deriver, bars
  unchanged: **L1 0.3857 FAIL** (defensible-only 0.3560), L2 0.0000 PASS,
  `FILED-UNLICENSED` again; identity error 0.0000 GW, A = 102.6 % of the gap.
  Per the ercot-190 signed rule this read **(Q-B) AUTOMATIC AND FINAL — no
  further ERCOT C3a-2023 spend, item 11 CLOSED**
  (`results/calibration/ercot191_cc_headroom_licence_retest.json`).

This session does not re-open it and does not re-derive it (Q-B FINAL is a
standing ruling, cited and not re-litigated). What §3 adds is only that the
model is **not over-producing** at the hours in question — its gas output at
the missed hours is 0.8–1.4 GW *below* ERCOT's — so the depth object, if it
were ever licensed, would act on capability the model is not currently
dispatching. That is the same price-reach question item 11 owned, and it
remains unlicensed.

## 3. THE MISS POPULATION, MEASURED ON THE CURRENT KEEPER

Basis: actual RT > $200 (rubric §5 ERCOT tail threshold) against the
demand-weighted P1 system price (the standing `_ercot173_ab` convention).
The scorer's own C3c basis is reported beside it and the two are **not**
reconciled — 68/22/1 scored vs 64/17/0 here, a basis difference, disclosed.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| actual tail hours (> $200) | 181 | 53 | 31 |
| model caught / missed / phantom | 64 / **117** / 3 | 17 / **36** / 5 | 0 / **31** / 1 |
| scored C3c (model/actual) | 68 / 181 | 22 / 53 | 1 / 31 |
| model price at missed, p10 / p50 / p90 | 45.31 / **96.65** / 161.99 | 32.65 / **70.92** / 126.52 | 47.23 / **89.61** / 135.05 |
| actual RT at missed, p50 | **442.40** | **266.18** | **250.32** |

**Reality's own price formation at those same hours** (NP6-905 curation —
ERCOT's published RTORPA, PRC and SCED system λ):

| at the MISSED hours | 2023 | 2024 | 2025 |
|---|---|---|---|
| published RTORPA p50 (max) | **$0.84** ($261.76) | **$1.58** ($55.54) | **$0.00** ($36.07) |
| PRC p50 | 5,708 MW | 6,197 MW | 7,727 MW |
| SCED system λ p50 | **$456.81** | **$272.07** | **$278.53** |
| share of hours with λ > 0.8 × RT | **91.5 %** | **91.7 %** | **87.1 %** |

The caught hours are the mirror image and confirm the instrument reads what it
should: RTORPA p50 $31.39 / $41.00 and λ p50 $1,868 / $966 — the model catches
the hours where ERCOT's *reserve* scarcity actually priced, and misses the
hours where ERCOT's *energy* offers did.

**The physical balance at the missed hours** (mean MW; EIA-930 ERCO, both
clocks repaired per §6):

| fuel | 2023 model / actual (Δ) | 2024 | 2025 |
|---|---|---|---|
| gas | 40,859 / 42,271 (**−1,412**) | 35,579 / 36,347 (−768) | 37,564 / 38,331 (−767) |
| coal | 10,934 / 10,557 (+378) | 8,463 / 9,089 (−626) | 8,747 / 8,725 (+22) |
| nuclear | 4,747 / 4,754 (−7) | 3,963 / 4,017 (−54) | 4,757 / 4,901 (−144) |
| renewables | 14,907 / 14,403 (+504) | 10,534 / 9,789 (+744) | 7,941 / 7,450 (+492) |
| storage (net) | 504 / — | 1,805 / 1,907 (−102) | 2,555 / 2,375 (+181) |
| model demand vs 930 gen-sum | 72,543 / 72,543 | 60,855 / 60,329 | 61,717 / 59,670¹ |

¹ the 930 generation sum excludes `BAT` by construction; adding the measured
2,375 MW of battery discharge closes 2025's row to −327 MW.

**Read the two tables together.** At the same hour, on the same system, the
model is dispatching ERCOT's own fuel mix to within a few per cent — every
fuel inside ±8 %, the largest single gap 1.4 GW on a 72.5 GW system — and it
clears at **$70–97** where ERCOT's SCED cleared at **$272–457** with an
essentially zero reserve adder and 5.7–7.7 GW of physical responsive reserve
in hand. Nothing about quantity is left to find: **the missing dollars are in
the offer at the clearing point, not in the MW at the clearing point.**

## 4. THE SUB-HOURLY FACT — supporting, quantified, and NOT sufficient

ERCOT settles RT on 15-minute intervals; the model is hourly by mandate
(rule 8 `[R-8760]`). From the committed RTM settlement-point workbooks
(`HB_BUSAVG`, hours whose hourly mean exceeds $200):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| tail hours on this basis | 180 | 54 | 35 |
| median (max interval / hourly mean) | **1.82** | **1.70** | 1.24 |
| hours whose **median** interval is ≤ $200 | 31 (17 %) | 10 (19 %) | 3 (9 %) |
| hours with min interval < $100 | 62 (34 %) | 13 (24 %) | 3 (9 %) |
| hours containing an interval > $1,000 | 104 | 17 | 5 |
| p50 hourly mean / max interval / min interval | 629 / 1,254 / 161 | 274 / 487 / 154 | 244 / 313 / 186 |

Stated at full strength and no further: in **17 % / 19 % / 9 %** of the actual
tail hours the hour clears the C3c threshold on a *minority* of its intervals —
those hours are unreachable by construction for an hourly LP. The remaining
81–91 % are genuinely high across the hour, so this is a **contributing
model-class fact, not an explanation of the residual**, and it is not offered
as one.

## 5. WHY PHASE-1 WAS NOT ENTERED (the admissibility argument, in full)

To close C3c on merit the model must raise its clearing price at hours where
its MW position already matches reality. Exactly three families can do that,
and each is shut:

1. **Offer conduct above marginal cost** — the direct route, and it is what
   ERCOT actually did (§3: λ carries > 87 % of the price in every year).
   **Door A is CLOSED** (owner, card X / X-1; ercot-211 measured the scarcity
   conduct layer **NOT-TRANSFERABLE**, and for storage the failure is
   model-free). Re-deriving it here would also collide with rule 1
   `[R-STRUCT]` and rule 13 `[R-MEASURED]` — an offer level fitted to the
   price residual is the forbidden form.
2. **Merit-order depth** (less cheap capability under the clearing point) —
   **item 11 CLOSED**, twice unlicensed (§2); its per-hour telemetered-HSL cap
   form is rule-13-forbidden and its aggregate form is `R`
   (`energy_online_capability_cap`, ERCOT-159).
3. **A reserve / ORDC / emergency-tier adder** — foreclosed by the
   measurement, not by governance: reality's RTORPA at these hours is
   **$0.00–1.58 p50** with PRC 5.7–7.7 GW. Any adder mechanism that lifted
   these hours would be re-manufacturing precisely the AS-product
   shortfall-ramp leak that ercot-214 identified and ercot-215 removed
   (116/117 of 2023's deep adder hours contaminated). Re-opening it is barred
   and, on this evidence, wrong. The same measurement disposes of the one
   `U` cell that could be read as an ERCOT tail-price row,
   `maxgen_emergency_tier_pricing` (the MISO declared-window tier floors,
   whose ERCOT analogue would be declared EEA windows): across all **184**
   missed hours the published PRC never falls below **4,132 MW**, and
   **0 hours** sit under ERCOT's own EEA-1 trigger of 2,300 MW (Nodal
   Protocols §6.5.9.4.2). An emergency-tier mechanism has **no window** at
   the hours the residual is made of. `dynamic_reserve_requirements` is
   likewise already owned for ERCOT by the measured AS-plan path
   (`ercot_as_plan_requirement_mw`, level and clock verified against raw
   ASPLANNP433) under rule 19.

The queue is consistent with that. ERCOT's §5.1 lever queue holds **no live,
un-adjudicated in-model item**: item 3 CLOSED at ercot-143 ("DO NOT RE-OPEN"),
item 7 CLOSED-WITH-KEEPER at ercot-165, item 8 CLOSED on an owner data
refusal, item 9's lever is cell `R` (`energy_online_capability_cap`,
ERCOT-155/159), items 10/12/13 EXECUTED, item 11 CLOSED at ercot-191. The
ERCOT shard's **28** `U` cells were read rather than waved past: they
are availability/capability rows, fuel-input rows, forward/capacity-lane rows
or other-ISO-driver rows. Every one of them acts either by **moving MW** — and
§3 measures the model's MW position at these hours as already matching ERCOT's
within ±8 %, so there is nothing there to buy — or by **moving delivered fuel
cost**, and that route is bounded by arithmetic: lifting a CC's SRMC from the
model's $96.65 to ERCOT's $456.81 at a 7.0 MMBtu/MWh heat rate needs about
**+$51/MMBtu** of delivered gas in August 2023, against a ~$2.5 hub. (ERCOT
already arms `ercot_zonal_gas_basis`, `gas_hh_monthly_shape` and
`gas_daily_shape`, so that phenomenon has its owners under rule 19 in any
case.) This session therefore proposes no lever and invents none.

**Filed for the next keeper-promoting session (not done here — a registered
bundle's attestation is not edited after the fact):** the C3c exception's
`OPEN RESIDUAL LANE` clause should be re-worded to record that both named
candidates are spent — (a) armed since ercot-167 and re-gated RG-PASS at
ercot-193, (b) CLOSED at ercot-191 under Q-B — with this finding as the
citation. The exception's *kind*, tier, magnitudes and ledger status are
unaffected; this is the clause's forward-pointer only.

## 6. TWO CLOCK DEFECTS IN THE INSTRUMENT LAYER — found, measured, repaired

Both live in `scripts/probes/ercot98_tail_attribution_measure.py` (the
standing tail-attribution probe). Neither touches an LP input, a derive, a
bench series or a scored criterion — the production EIA-930 path joins on
explicit UTC stamps (`data/eia930/frames.py`, `scripts/data/convert_eia930.py`)
— but both are GW-scale inside a tail-hour comparison.

1. **EIA-930 `period` is the hour-ENDING stamp**; the model's hour index is
   hour-beginning CST. The probe joined them naively, lagging the actuals one
   hour. **Measured, not assumed:** correlating model demand (a measured input
   whose clock is astronomically verified, ercot-166) against the 930
   generation sum at four offsets returns **1.00000 / 0.99933 / 0.94335** at
   +1 h for 2023/2024/2025 — the maximum in every year, and an exact 1.0 in
   2023. Effect on the 2023 missed-hour read: gas **−349 → −1,412 MW**,
   renewables **−1,771 → +504 MW**.
2. **The model runs a fixed non-leap 8760 clock** (rule 8; the same fact the
   ercot-214 probe's `MONTH_DAYS` table encodes), so in a **leap** year every
   model hour from March 1 on is 24 h later in real time than a naive
   `date_range(periods=8760)` label. Uncorrected, 2024's entire tail
   comparison is mis-dated by a day: it read renewables **−9,216 MW** at the
   missed hours (and drove the intermediate reading that ERCOT had ~20 GW of
   wind at hours the model gave ~3 GW). Corrected: **+744 MW**.

Both are repaired in place with citations, and the corrected constructions are
carried in this session's own probe. **Consequence for the record:**
`docs/DIAGNOSIS-ercot-2023-summer-tail-attribution-2026-07.md` §[3]'s
physical-balance numbers were computed on the uncorrected join (2023, so
defect 1 only) and should be read as superseded by §3 above; its other
sections are untouched by this.

## 7. GOVERNANCE

Standing rulings cited and honoured, never re-litigated: **Q-B FINAL** and
**R-A** (this session takes no C3a-2023 spend and reports no C3a/C3b-2023
number as a basis); **ercot-206 B0** (no LOLP-table arming); **ercot-211
Door A CLOSED** (no conduct work — §5 cites it as a closure, does not test
it); **V0/ercot-201 DO-NOT-REDO**; **28a** (the bare netting not re-tested);
the **mid-band spill lane CLOSED** at ercot-215 (not re-opened; the published
two-basis form is not built and is not proposed); the **G-SPUR band-top
blindness** left as an owner gate-revision item. Rule 15: **no run produced,
so nothing to register** (the ercot-163/170/214 no-LP pattern); keeper
UNCHANGED and its dashboard entry untouched. Rule 16: no year solved, so no
span question arises. Rule 22: 2023–2025 only, by construction — the probe
enumerates `YEARS = (2023, 2024, 2025)` and no out-of-training year is read,
scored or registered; ERCOT holds no `complete`/`final` marker and none is
sought. Rule 25: ERCOT only — no other ISO's artifact was read or written.
Rules 5/23/24: no `ScenarioConfig` field, no constant, no derive, no tuning
channel of any kind; nothing was fitted because nothing was built. Rule 28:
**no cell verdict minted** (28(b) — no mechanism was tested) and **28(c) not
engaged** (no new field); duty (a) is discharged in §5 — the queue was read
first, holds no live item, and this session states why it goes no further.
Rule 27: edits local, exact on-disk bytes pushed, pushed files blob-verified.
No new workflows, no cron, no CI job. No PR opened (push-and-stop on the
designated branch).

**Session consumed the ercot-216 shorthand. Next shorthand: ercot-217**
(ercot-199 remains unclaimed).
