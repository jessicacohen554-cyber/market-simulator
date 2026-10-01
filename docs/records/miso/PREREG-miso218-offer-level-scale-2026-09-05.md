# PREREG miso-218 — THE RATIO-PRESERVING OFFER-LEVEL SCALE (×1.10): an OWNER-REQUESTED, rule-13 DEFAULT-OFF DIAGNOSTIC PROBE that bounds how much of C3a-2025 a pure LEVEL lever can reach, and at what cost to C3a-2023 (2026-09-05)

**Pushed BLIND** — before the solve and before any adjudicating statistic. Keeper
`2026-09-05-miso-217-intermphys` (bundle `results/calibration/miso217_intermphys_B`),
NOT-YET on **C3a-2025 alone (−12.297 %)**, C3c ledgered 3/3, C6 attested 41/2. Branch
`claude/miso-217-intermediate-phys-arm` (this lane's live branch), merged with `origin/main`
`f41d4a44`. Rule 22 `[R-HOLDOUT]`: 2023–2025 only.

---

## 1. What the owner asked, and what this session is running

> *"keeps relative offer curve ratio the same but shifts multipliers up… We have +10 % room
> to keep all 3 years calibrated while maintaining fossil merit order… Kinda seems like it's
> a peaking price miss."*

Executed literally: **every offer-curve band multiplier** (`committed`, `econ_low`,
`econ_high`, `peak`) of **every fossil class** is scaled by **×1.10**. Within-class ratios are
preserved exactly, and because every class scales by the same factor, **fossil merit order is
preserved exactly** for the fuel-scaled component of every unit's marginal cost. Structural
tranche shares (`econ_low_share`, `pct_peaking`) and the measured `phys_*` keys are
**untouched** — the former are not price levers, the latter are measurements.

**No `ScenarioConfig` field is minted.** The scale is applied through the **existing**
operator channel `offer_curve_by_group`, replayed via `replay_keeper --set`, so it is
recorded verbatim in the arm's `run_config.json` and adds no registry surface (rule 24
`[R-REGISTRY]`) and no matrix row (rule 28c not engaged).

## 2. Its status under rule 1 `[R-STRUCT]` and rule 13 `[R-MEASURED]`, declared BEFORE the result

A uniform multiplicative lift on every offer curve, chosen to move a price residual, is a
**fitted level scalar identified against the residual**. Rule 1's second half — *never reach
the right number through a mechanism that isn't real (a fitted adder, a load proxy, a haircut
tuned to the residual)* — forecloses it as a **keeper mechanism**, and rule 13 gives it its
only admissible form: *an explicitly-labelled, default-**off** diagnostic probe; it must never
be enabled in a keeper or quoted as evidence of forecast skill.*

**This session therefore pre-commits: THIS ARM WILL NOT BE PROPOSED AS A KEEPER, whatever the
gates say.** It is run because it answers a real, decision-relevant question the owner posed
and nobody has yet bounded: **how much of C3a-2025 can a pure LEVEL lever reach, and what does
it cost C3a-2023?** That bound is evidence for the lane either way. If the owner reads the
result and directs promotion regardless, that is their call to make with the numbers in hand
and this PREREG's §2 in front of them — not a conclusion this session may reach on its own.

## 3. The arithmetic that already constrains the answer (stated before the solve)

C3a's band is **±10 %** and it is **load-bearing**. The keeper's own faces:

| year | model | actual | C3a | headroom to +10 % |
|---|---:|---:|---:|---:|
| 2023 | 33.210 | 32.850 | **+1.096 %** | **+8.90 %** |
| 2024 | 31.370 | 32.300 | −2.879 % | +13.26 % |
| 2025 | 39.870 | 45.460 | **−12.297 %** | +24.78 % |

**So the binding constraint is 2023, not 2025**, and the arithmetic window on *price* is
**+8.90 %**, not +10 %. A price lift of exactly +8.90 % would leave 2023 at +10.00 % (the
edge), 2024 at +5.83 %, and 2025 at **−4.53 %** — i.e. **2025 does clear inside the band if
the lift lands under ~8.9 %**. A ×1.10 on *multipliers* is **not** a +10 % lift on *price*:
only the fuel-scaled component of the marginal unit's cost moves (`mc = HR × mult × fuel +
vom + emission adders`), so the pass-through is roughly the fuel share of marginal mc — for
MISO's gas-marginal hours ~80–90 %. **The whole question is whether ×1.10 lands under or over
the 2023 ceiling, and that is what this run measures.**

## 4. The standing measurement that argues against the mechanism (miso-202/203)

C3a-2025 is measured to be **entirely a missing scarcity tail in the evening net-load ramp**,
not a level miss: over Jun–Jul the model's **MEDIAN price is HIGHER than actual (37.47 vs
32.73)**, the gap opens only past p90 and explodes at p99 (69.04 vs 238.93), **the top 1 % of
actual hours (15 h) carry 99.9 % of the mean gap**, 13 of those 15 hours fall in h18–h21, and
the model's maximum price in any zone-hour is **$183.22 against an actual $1,669.52** with
0.0 MWh unserved and an ORDC that never climbs its curve. **A uniform level lift closes the
mean by raising a median that is already too high.** The owner's own reading — *"kinda seems
like it's a peaking price miss"* — is exactly what miso-202/203 measured, and it is the
strongest argument against a level lever, not for one.

## 5. My prior, stated before the solve (scored in the finding, against interest)

* **P-1 (pass-through).** The ×1.10 multiplier scale raises the load-weighted mean price by
  **+7.0 % to +9.5 %** in every year — less than 10 %, because vom and emission adders do not
  scale. *Bar: all three years inside that range.*
* **P-2 (the 2023 ceiling — the decisive prediction).** **C3a-2023 EXITS the ±10 % band**,
  landing in **[+8.5 %, +11.5 %]**. If it lands below +10 % the owner's "+10 % room" premise
  survives on the arithmetic and my §3 reading is too pessimistic; I am predicting it does
  not.
* **P-3 (2025).** C3a-2025 lands in **[−6.0 %, −3.0 %]** — i.e. **the level lever DOES clear
  2025's band**. The mechanism works on the number it was aimed at; that is not in dispute
  and is not the objection.
* **P-4 (the shape cost — why the number is not the answer).** **C3b (price shape, NRMSE)
  gets WORSE in at least 2 of 3 years**, because the lift raises a Jun–Jul median that is
  already above actual. *Bar: C3b worse in ≥ 2 of 3 years.*
* **P-5 (the tail is untouched).** **C3c does not improve in any year.** The model's
  hours above $200/MWh are 3 / 7 / 0 against an actual 30 / 37 / 88; a 10 % lift on a
  $183 maximum reaches ~$202. *Bar: C3c hours above $200 rise by ≤ 5 in every year and the
  criterion does not flip to PASS.*
* **P-6 (C1 and C8).** Fossil merit order is preserved by construction, so class volumes move
  little: **no C1 band exit**, and the largest single class-year |Δ| is **< 3.0 TWh**. C8
  `CT_PEAKER` moves by **< 0.03** in every year. *Named risk: `CC_REGULAR`-2024 has only
  **0.053 TWh** of band left after miso-217, so ANY upward CC move exits — this is the single
  most likely way P-6 is wrong.*
* **P-7 (disposition).** **P(this arm is proposed as a keeper) = 0.** See §2. My prediction
  about what the owner should conclude: the run will show a level lever **can** buy C3a-2025
  at the cost of C3a-2023 and C3b, which is the definition of moving the residual rather than
  the model.

## 6. What is measured and reported, either way

The full A/B on the `_miso217_ab_gates.py` pattern against the keeper as control (S-0
inherited, never re-solved): all three C3a faces, C3b by year, C3c hours above $200, the full
24-cell C1 table with band exits, C8 `CT_PEAKER` and `ST_GAS` forced shares, and the
determination. **C3a is reported at full magnitude in both directions and never argued.**

## 7. What ends the session

The finding, the registered run (rule 15 — a probe is registered like any other run), the
`docs/calibration-log/miso.md` entry, the §5.4 queue stamp, and the miso-219 handoff.
**The keeper does not change on this session's own authority.**

Next shorthand: **miso-218**.
