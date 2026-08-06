# FINDING nyiso-129 — the solar-basis treatment is PROMOTED on structure at the cost of the determination; and its named successor lever is REFUTED as specified, with the real object identified

**Keeper CHANGED** → `2026-08-06-nyiso-128-solar-basis` (bundle
`results/calibration/nyiso128_treatment`), superseding
`2026-08-06-nyiso-128-control`. **Determination CALIBRATED-WITH-CAVEATS →
NOT-YET, carried openly.** No new run was solved: both arms already existed and
were registered at nyiso-128, and every number below comes from committed
artifacts, published inputs, or the scorer read at this HEAD (rubric **v3.1**).

**Rule 22:** 2023–2025 only. No out-of-training year was solved, scored, read or
registered; the holdout spend freeze was checked and not touched.

---

## 1. The owner ruling, and the recommendation it answered

> *"Is this a recommended keeper candidate? If so plz promote. If structural
> integrity improves but gates regress that may still be a keeper."*
> — owner, session nyiso-129, 2026-08-06

The session's recommendation was **YES**, on rules 1 `[R-STRUCT]` and 14
`[R-ACCURATE]`. nyiso-128b had escalated the arm rather than promoting it,
because rule 22 D-5(b) stops a promotion whose re-verified determination is
worse. That stop **did fire**; the owner is its escalation target and released
it. The downgrade is therefore recorded, not laundered.

## 2. What is now armed, and what it buys

`nyiso_solar_market_generator_basis` — a rule 14 input repair, **zero free
parameters** (`n_residual` unchanged at 6), correcting a **double count**:
EIA-860's NY utility-scale population carries ~2 GW of distribution-connected
NY-Sun community solar that is not a NYISO market generator and whose output is
already netted out of the EIA-930 `NYIS` demand series used as load (`NG: SUN`
identically zero, 8,760/8,760 h). Capacity basis becomes NYISO's own Gold Book
Table III-2a registry: 15 units, 573.4 MW.

Scored at HEAD under rubric v3.1:

| | control (superseded keeper) | **treatment (new keeper)** |
|---|---|---|
| C3a mean LMP | PASS +6.2 / −1.7 / −7.0 % | **PASS +8.8 / +0.8 / −3.2 %** |
| C1 / C2 / C3b / C4 / C6 / C8 | PASS | **PASS** |
| C3c tail | CAVEAT (2024, 0.17×) | **FAIL 2023 (2.20×)** + caveat 2024 (0.25×) |
| determination | CALIBRATED-WITH-CAVEATS | **NOT-YET** |

C3a improves 3.8 pp in 2025 and 2.5 pp in 2024 — the two years furthest out —
and 2023 worsens 2.6 pp but stays in band; the pre-registered adverse case
(2023 crossing +10 %) did not materialise. The removed solar is replaced by
**in-state thermal**, not imports (JJA h16–h18 2025: CT_PEAKER +109 MW, ST_GAS
+365 MW, CC_REGULAR +142 MW against solar −1,218 MW; import p50 +52 / 0 /
+42 MW).

## 3. The cost, LOCALIZED — and why rule 14 says keep it anyway

C3c-2023 goes 18 h → 22 h against a measured 10 h (2.20×). This session did not
accept that as diffuse. Counting the tail straight off both arms' committed
`hourly/system_2023.parquet` sidecars:

* **Every one of the 22 tail hours is Long Island.** Hours of day h14–h19.
  Dates: 08-21, and the **Sept 4–9 heat wave** (09-04, 09-05, 09-06, 09-07,
  09-09).
* **All four hours the treatment adds are in that episode**: 09-04 16h,
  09-07 15h, 09-09 14h, 09-09 15h. None is removed.
* **Zone K is where the arm bites hardest in proportion**: it removes
  **97.7 MW of 152.1 MW** of Long Island solar (54.4 MW registered), against a
  system-wide removal that leaves the LI scarcity ladder exposed. Measured
  sensitivity in the added hours: the control carries ~800 MW more system solar
  and prices Long Island at $286.4; the treatment prices it at $386.7 — one to
  two steps up the published Zone-K ladder.

Rule 14 states the reading in its own words: a more accurate input that makes
the fit worse is a **discovered bug elsewhere**, not a reason to revert — *"the
estimate was silently compensating for it."* The phantom Zone-K solar was
masking an over-tight Long Island representation. That is now the ISO's named
successor lever, and the queue was **EMPTY** before this session.

### 3a. And the over-tightness has a measured owner

Read straight off both arms' committed `hourly/network_2023.parquet`, **both** of
Long Island's import paths are pinned at their bound in **100 % of the 22 tail
hours**, in both arms:

| link | median `limit_up` | at bound, all hours | at bound, tail hours | flow in tail hours |
|---|---:|---:|---:|---:|
| `NYC>Long_Island` | 1,650 MW | **26.5 %** | **100 %** | **325 MW** |
| `NYISO_external>Long_Island` | 1,012 MW | 99.9 % | **100 %** | 849 MW |

The 325 MW is not the link's TTC — it is the **published capacity-market LCR
import limit** for Long Island (2023/24 = 325 MW, 2024/25 = 275 MW), applied by
the armed `nyiso_li_lcr_tsl` as an in-window **hourly energy** cap on the
NYC→Long_Island link. `model/interchange/nyiso.py` already documents that
boundary mismatch in its own docstring. So Zone K enters every scarcity hour
with **both** import paths saturated and its in-zone fleet as the only
respondent — which is exactly why removing 97.7 MW of Zone-K afternoon solar
walks the price up the ladder, and why the same removal upstate does not.

That makes the successor lever **specific and pre-registrable**: whether a
*deliverability* planning quantity should be the hourly energy transfer cap in
the hours the C3c tail forms. It is an existing armed mechanism to reconcile
(rule 19 `[R-ONE-MECH]`), not a new floor to stack.

**The 2023 exception stays WITHHELD.** The miss is an *over*-production; the
ledgered C3c caveat's own classification licenses only an under-production
(*"five-zone representation cannot form the sub-zonal scarcity"*). It is
in-training, so the 2026-08-06 C3c standing rule — out-of-training only — does
not reach it. The FAIL stands at full magnitude; ledger budget stays **1 of 3**.

## 4. The named successor lever is REFUTED AS SPECIFIED — ex ante, no solve spent

nyiso-128b named the next object as *"re-identify the registered fleet's CF from
EIA-860 tracking mix + latitude"*, on the premise that the registered fleet's
~0.20 CF against the model's ~0.133 blend is a **geometry** difference. Measured
with exactly the machinery the premise named (capacity-weighted EIA-860 tracking
mix and centroid latitude through `renewables._clearsky_poa_by_tech`):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| whole NY fleet — single-axis share | 0.299 | 0.450 | 0.473 |
| registered subset — single-axis share | 0.309 | 0.608 | 0.608 |
| whole NY fleet — centroid latitude | 42.56 °N | 42.69 °N | 42.68 °N |
| registered subset — centroid latitude | 42.25 °N | 42.54 °N | 42.54 °N |
| DC:AC ratio, whole / registered | 1.365 / 1.338 | 1.353 / 1.340 | 1.353 / 1.340 |
| **clear-sky POA ratio (registered ÷ whole)** | **1.0041** | **1.0322** | **1.0276** |

The two populations sit at the **same latitude** and differ only modestly in
tracking share, and the registered fleet's DC:AC ratio is **lower**. Geometry
buys CF 0.133 → **0.137**, not → 0.20. The lever as named is **inert**, and rule
26 `[R-DELETE]` forbids parking an inert knob default-off. **No solve was spent
finding this out.**

## 5. The real object, newly identified

`RENEWABLE_AVG_CF["NYISO"]["solar"] = 0.15` is a **self-declared Tier-3
approximation** — `constants.py` carries `needs-citation: verify against EIA-923
ISO totals before quoting a forecast` on that very block — realized at ~0.133
after the nyiso-75 donor repair and clipping. Against it, the 2026 Gold Book
publishes the 2025 Net Energy of each registered unit:

| | measured |
|---|---|
| registered fleet 2025 net energy | **981.8 GWh** over 573.4 MW |
| **fleet CF 2025** | **0.1955** |
| per-unit CF range | 0.158 (Albany County 1) – 0.222 (East Point) |

So the CF gap is real (~0.133 model vs ~0.196 measured) but it is a **CF-LEVEL
defect on a different input**, with its own identification, not a geometry
correction. That is the successor lever's true object (rule 19 `[R-ONE-MECH]`:
its own prereg).

**Reported against interest:** this session's own extraction of the 2026 Gold
Book totals **981.8 GWh**, where nyiso-128 quoted **1,081.8 GWh** — exactly
100 GWh apart. The successor session must reconcile the two before sizing
anything, because the difference moves the 2025 over-removal from 0.33 TWh to
**0.23 TWh** and shrinks the "unearned" share of the C3a-2025 gain accordingly.
Nothing in this promotion depends on which is right: both leave the arm short in
the tightening direction, and neither is a free parameter.

## 6. Verification

* `scripts/calibration_verdict.py --run-id 2026-08-06-nyiso-128-solar-basis` →
  **NOT-YET**, sole FAIL `price_tail` 2023. Committed artifacts only, no solve.
* `scripts/audit_keepers.py --iso NYISO` → **PASS 0 failures, 0 warnings**
  (E4 definition rewritten from the auto-placeholder; M1b marker determination
  re-keyed and re-verified per rule 22 D-5(b)).
* Evidence record: `results/calibration/_nyiso129_cf_identification.json`,
  probe `scripts/probes/_nyiso129_cf_identification.py` (all three measurements
  reproducible, no solve).

## 7. What the next session inherits

1. **Long Island scarcity over-production** (C3c-2023, 22 h vs 10 h, one Sept
   heat wave, entirely Zone K) — the newly named lever, and the ISO's route back
   to CALIBRATED-WITH-CAVEATS.
2. **The NYISO solar CF level** (§5) — a rule 14 accuracy defect on
   `RENEWABLE_AVG_CF`, needing its own prereg and the 981.8 / 1,081.8 GWh
   reconciliation first.
3. **The frontier block is now doubly stale.** It lapsed at nyiso-120, nyiso-127
   §3 recommended re-declaration over a third amendment, and the determination
   has now moved again. A frontier/`complete` re-declaration is **not**
   appropriate while NYISO reads NOT-YET; it becomes assessable again once
   item 1 lands. The nyiso-127 §5 four-item decision package — including the
   phantom DOF entry `GAS_AVAILABILITY_FACTOR[NYISO] = 0.866`, ledgered as
   living in `constants.py` but present nowhere in `src/market_sim/` — remains
   open and untouched.
