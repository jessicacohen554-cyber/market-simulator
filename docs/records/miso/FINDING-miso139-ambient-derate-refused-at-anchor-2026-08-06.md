# FINDING — miso-139: the ambient capability-derate is NOT "already armed and mis-scoped" — it is armed in an ANCHORING CONVENTION that cannot express the effect the charter needs, at ANY slope; and the whole family's ceiling is 30–39× too small for the object

**Session:** miso-139, 2026-08-06, branch `claude/miso-ambient-derate-scope-e4t0v6`.
Charter lane: the ambient-derate class scope, identified on MISO's own data.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`.** MISO keeper unchanged at **`2026-08-05-miso-132b-cc-committed`**
(bundle `results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso139-ambient-derate-class-scope-2026-08-06.md`,
pushed at **`6263f43d`** BEFORE any adjudicating statistic, with a two-sided
prior carrying **four falsifiable numeric predictions**, the convention decision
rule fixed on basis consistency in advance, and four look-alike traps named with
pre-committed counter-measurements.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss.
No C7 lane chartered, no C7 ledger sought.

---

## 1. Headline

**The pre-committed verdict is `REFUSED-AT-G0`, branch (C)** — *neither
implemented convention is admissible without a mechanism change*. The charter's
framing that this is "a scope + identification question and NOT a new mechanism"
is **falsified**: the mechanism's **anchor** is part of the mechanism, and the
one it is armed in cannot produce the within-summer sign reversal miso-137
demands **for any slope value**.

Three results, each independently sufficient to stop the arm:

1. **G-0 — the armed convention derates BOTH summer windows, and is
   summer-neutral for no positive slope.** In **18 of 18** MISO zone-years the
   summer *night* mean dry-bulb sits **+3.6 to +9.1 °C ABOVE** the zone annual
   mean, so an annual-mean anchor gives `raw < 1` at h00–05 as well as h12–17.
   Measured on the model's own availability matrix, convention (A) moves the
   armed classes' **summer-mean capability by −3.6 to −4.1 % (CT) and −1.8 to
   −1.9 % (CC)** against a `pmax` basis that **is** the EIA-860 net-summer
   rating — a summer LEVEL move, failing the pre-registered ±1 % basis rule.
   The alternative convention (B) *is* summer-neutral and *does* deliver the
   sign reversal, but only by cutting **−6.7 to −6.8 % of CT and −5.3 to −5.4 %
   of CC ANNUAL capability**, concentrated in non-summer — **Trap 1 firing
   exactly as pre-registered** — and by silently re-treating the committed CHP
   classes (−7.7 % annual on CT_CHP).
2. **G-1 — MISO's own identification is 3.2–4.1× below the committed literature
   slopes, and it is stable.** EIA-860 MISO two-point, on the model's own fleet
   and class taxonomy, against MISO's own measured peak-hour dry-bulb pair:
   **CT_PEAKER 0.00363/°C** (literature 0.0126), **CC_REGULAR 0.00192/°C**
   (0.0076), **ST_GAS 0.00033** (0.0054), **COAL 0.00025** (0.0040). Robustness
   across the pre-registered peak-hour set: **0.097–0.228 relative spread**,
   inside the ±0.30 bar. **COAL and ST_GAS are excluded by measurement**, not by
   assumption.
3. **G-2 — the derate is non-binding where it is needed.** In summer h12–17 the
   removal exceeds the class's own idle headroom in **0.1–0.7 % of hours for
   CT_PEAKER and 1.5–4.8 % for CC_REGULAR**; in summer h00–05 it is **0 of 732
   hours in every year**. The model runs its CT fleet at **25–34 % of capability**
   in exactly the window it under-prices by 41 %, holding **11.6–13.3 GW idle**.

**And the family's ceiling is measured, not asserted.** Under the *named
successor* convention — a **summer**-mean anchor, the only one consistent with a
net-summer `pmax` basis — the total summer-afternoon capability removal is
**456–497 MW** against a measured idle cushion of **13.7–18.8 GW**: a
**30–39× shortfall**. The ambient-derate family is quantitatively incapable of
the miso-137 object at any admissible parameter, so building the successor
convention would not change this verdict.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-0** anchoring / double-count (GATING) | **FAIL → branch (C).** (A) fails the ±1 % summer-basis rule for every armed class in every year; (B) passes it but fires Trap 1 (annual capability cut) and re-treats CHP. §4 |
| **G-1** identification, MISO-own (GATING) | **PASSES as an identification** — stable, zero fitted values — and **REFUSES the committed literature slopes for MISO under rule 25**. §5 |
| **G-2** binding (diagnostic, not licensing) | **NON-BINDING** in 95.2–99.9 % of summer h12–17 hours and 100 % of summer h00–05 hours. §6 |
| family ceiling (successor convention) | **30–39× below the cushion.** §7 |

**Stop rule honoured as written.** PREREG §3: *"If G-0 returns (C), the session
reports the anchoring finding and stops before any solve."* It did. G-1 and G-2
were completed anyway because both were chartered as gating prerequisites and
both are reusable by whoever takes the lane next; neither was used to reopen G-0.

---

## 3. §0 corrections, re-verified from committed artifacts

Two charter §0 statements did not survive re-verification against
`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed` at HEAD.
Recorded rather than carried:

* The charter reads *"NOT-YET; sole FAIL C7 shape 2025"*. **C7 is not a scored
  criterion at HEAD** — the standalone gate was retired by the rubric v3.1 owner
  amendment 2026-08-06, and MISO's blocker moved C7 → C3a the same day. The
  **sole FAIL is C3a `price_mean`**, on the scorer's own reason string
  (*"undocumented out-of-tolerance (FAIL) criteria: price_mean"*).
* The charter reads *"ledgered caveats {C3a, C3c}"*. Under v3.1 **C3c is the only
  ledgerable criterion at all**, so the bundle's `price_mean` ledger entry is
  inadmissible and C3a scores as an undocumented FAIL. Ledger budget spent:
  **1 of 1**, on C3c.

C3a re-verified: **2023 −0.5 % PASS · 2024 −5.9 % PASS · 2025 −14.0 % FAIL**
(DA companions −4.4 / −8.3 / −15.6). Neither correction changes the target.

**Rule 22:** `calibration-complete.json` carries `complete` for NEISO, NYISO and
PJM; **MISO is in neither block**. Only 2023/2024/2025 were read this session.

---

## 4. G-0 — the anchor is the mechanism

### 4.1 The measured anchors (G-0(a)) — P1 confirmed 18/18

Zone dry-bulb from `iso_zone_hourly_drybulb`, the identical series the LP
consumes. Deviations of the two miso-137 windows from each candidate anchor, °C:

| year | zone | annual mean | **night − ANNUAL** | aft − ANNUAL | **aft − SUMMER** | **night − SUMMER** |
|---|---|---:|---:|---:|---:|---:|
| 2023 | MISO-West | 10.03 | **+8.63** | +17.69 | +4.76 | −4.29 |
| 2023 | MISO-Indiana | 13.46 | **+5.04** | +14.06 | +4.74 | −4.27 |
| 2023 | MISO-South | 19.78 | **+4.03** | +13.67 | +5.06 | −4.57 |
| 2024 | MISO-South | 19.97 | **+3.64** | +12.43 | +4.63 | −4.17 |
| 2025 | MISO-West | 9.17 | **+9.14** | +17.04 | +4.15 | −3.75 |
| *(all 18 zone-years)* | | | **+3.64 … +9.14** | +12.43 … +17.69 | +4.15 … +5.06 | −3.74 … −4.57 |

**`night − ANNUAL > 0` in 18 of 18 zone-years.** Under an annual-mean anchor the
summer night is derated too. The charter's stated mechanism —

> *"Applied to summer it derates h12–17 … and uprates h00–05 (adding cheap supply
> where the model over-prices). That is the SIGN REVERSAL within one season and
> one fleet that miso-137 demands"*

— **is arithmetically false for the convention the mechanism is armed in.** The
genuine uprate leg lands in non-summer. The sign reversal *is* available about a
**SUMMER** anchor (`aft − SUMMER` positive, `night − SUMMER` negative in all 18),
which is precisely the convention the code does not offer.

### 4.2 The capability integrals (G-0(b,c,d))

Built with the model's **own** `generators_to_fleet_arrays` →
`_availability_matrix`, so the trailing `np.clip(availability, 0, 1)` and every
overlay are the code's, not a reimplementation. Class capability
(`pmax × availability`) relative to the same-config control:

| year | convention | class | annual | **summer** | summer aft | **summer night** | non-summer |
|---|---|---|---:|---:|---:|---:|---:|
| 2023 | **A** MISO slope | CT_PEAKER | 1.0005 | **0.9630** | 0.9464 | **0.9780** | 1.0192 |
| 2023 | **A** MISO slope | CC_REGULAR | 0.9990 | **0.9818** | 0.9725 | **0.9901** | 1.0098 |
| 2025 | **A** MISO slope | CT_PEAKER | 1.0009 | **0.9592** | 0.9431 | **0.9738** | 1.0217 |
| 2025 | **A** MISO slope | CC_REGULAR | 1.0000 | **0.9810** | 0.9722 | **0.9889** | 1.0114 |
| 2023 | *(A) literature — DIAGNOSTIC ONLY* | CT_PEAKER | 0.9967 | *0.8717* | *0.8139* | *0.9237* | *1.0590* |
| 2023 | **B** MISO slope | CT_PEAKER | **0.9323** | 1.0000 | 0.9833 | **1.0148** | **0.8985** |
| 2023 | **B** MISO slope | CC_REGULAR | **0.9475** | 0.9999 | 0.9906 | **1.0081** | **0.9149** |
| 2023 | **B** MISO slope | CT_CHP *(committed cell)* | **0.9234** | 1.0128 | 1.0128 | 1.0128 | **0.8810** |
| 2023 | *(B) literature — DIAGNOSTIC ONLY* | CT_PEAKER | *0.9730* | *1.0000* | *0.9369* | *1.0558* | *0.9596* |

*(Full 3-year × 4-convention table in `_miso139_derate_gates.json`. A control-side
validation: under (A) the CHP rows are byte-identical to control, confirming the
scope change touches only what it should.)*

**Convention (A) — REFUSED on the pre-registered rule.** The rule was fixed
before any measurement: *adopt the convention whose summer-hours mean capability
equals the class's net-summer basis to within ±1 %*, because `pmax` **is** that
rating (`eia860.py:998`). Measured, (A) moves it by **−3.6/−3.6/−4.1 % (CT)** and
**−1.8/−1.7/−1.9 % (CC)**. That is a **summer level move**, not a reshape.

**And it is structural, not parametric.** Since `T̄_summer > T̄_annual` in all
18 zone-years,

```
mean( 1 − s·(T − T̄_annual) )  over summer  =  1 − s·(T̄_summer − T̄_annual)  <  1   for every s > 0
```

so **(A) is summer-neutral only at `s = 0`** — the mechanism switched off. The
measurement bears the algebra out: at `s = 0.00363` the CT summer mean is 0.963,
at the literature `s = 0.0126` it is 0.872, both consistent with the measured
`T̄_summer − T̄_annual ≈ 10.2 °C`. **No slope, measured or literature, can make
the armed convention express a capacity-neutral summer reshape.** That is why
this is a mechanism question and not a scope question.

**Convention (B) — REFUSED on Trap 1, which fired exactly as pre-registered.**
(B) passes the summer rule by construction (`summer_rel` 0.9998–1.0001) and does
deliver the sign reversal (CT afternoon 0.983, **night 1.015**). But its
unconditional rescale, `_anchor / mean(raw[summer])` (`arrays.py:864-867`),
applies to the **whole year**, so with MISO's small measured slope it becomes a
flat **−10.1 % non-summer cut on CT** and **−8.5 % on CC**, i.e. **−6.8 % and
−5.3 % of annual capability**. The PREREG pre-committed: *"If the arm removes net
annual capability, it is reported as a level lever regardless of what C3a does."*
It does, so it is.

**The mechanism of that artifact, measured rather than assumed.** The
non-anchored branch is calibrated in **form** to literature-sized slopes: at
`s = 0.0126` the hinge curve's summer mean already sits near `1 − SUMMER_CLASS_DERATE`,
so the rescale is nearly inert. Measured, CT's non-summer cut goes
**−10.1 % (MISO slope) → −4.0 % (literature slope)**, a 2.5× reduction — the
predicted direction, but **it does not vanish**: even at literature slopes (B)
still removes 2.5–2.7 % of annual capability. I registered the stronger claim in
advance and it is only partly borne out; recorded as such.

**(B) also re-treats the committed CHP classes** — CT_CHP annual **0.9234**,
identically under both slope sets, because `temp_derate_mean_anchored` is a
single global bool. PREREG §3: *"I will not silently re-treat CHP."* Honoured.

---

## 5. G-1 — MISO's own identification (rule 25), and two measured exclusions

`slope_k = (C_winter − C_summer) / (C_summer · (T_sum_peak − T_win_peak))`, with
class membership and fleet scope from the model's own loader, EIA-860 Net
Summer/Winter capability, and the peak pair load-weighted on the same hourly
dry-bulb the LP consumes. Zero free parameters.

Measured MISO peak-hour dry-bulb pair (top-1 % of in-window load, °C):
**2023 33.88 / −6.70 · 2024 32.59 / −12.70 · 2025 32.77 / −12.00**.

| class | n | summer MW | winter MW | agg spread | unit p50 | share exactly flat | **slope /°C (top-1 %, 3-yr mean)** | committed literature | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **CT_PEAKER** | 516 | 22,289 | 25,806 | +0.1578 | +0.0875 | 0.409 | **0.00363** | 0.0126 | **3.5×** |
| **CC_REGULAR** | 131 | 24,927 | 27,005 | +0.0834 | +0.0816 | 0.214 | **0.00192** | 0.0076 | **4.0×** |
| **ST_GAS** | 39 | 10,991 | 11,147 | +0.0141 | +0.0015 | 0.436 | **0.00033** | 0.0054 | **16×** |
| **COAL** | 108 | 42,799 | 43,265 | +0.0109 | **+0.0000** | **0.528** | **0.00025** | 0.0040 | **16×** |
| *CC_CHP* | 85 | 7,036 | 7,890 | +0.1212 | +0.1429 | 0.212 | *0.00279* | — | — |
| *ST_CHP* | 98 | 1,932 | 1,933 | +0.0008 | +0.0000 | 0.806 | *0.00001* | — | — |

**Stable.** The pre-registered robustness set {top-0.5 %, top-1 %, top-5 %,
peak-day} moves every class's slope by **0.097–0.228 relative** — inside the
±0.30 refusal bar. (The spread is common across classes within a year because
only the ΔT denominator varies; the class term factors out.)

**Rule 25 discharged.** The committed literature slopes are **not armable for
MISO** — they are 3.5–16× above what MISO's own fleet registers. This is MISO's
second independent confirmation of pjm-95's non-transferability finding, and it
agrees in direction with the committed CHP identification (0.00141 from CAMPD
within-day conduct, ~9× below the literature CT value).

**Two exclusions, by measurement not assumption.** **COAL** — unit-p50 spread
exactly **0.0000** with **52.8 %** of units exactly flat, reproducing miso-138's
EIA-860 reading at a different grain: coal correctly carries **no** ambient
derate. **ST_GAS** — p50 +0.0015, 43.6 % exactly flat, slope 0.00033/°C, i.e.
indistinguishable from zero. Neither is a candidate.

**One cross-check disagreement, reported not resolved.** EIA-860 puts **ST_CHP**
at a spread of +0.0008 (80.6 % exactly flat) against the committed CAMPD
within-day estimate of 0.00141/°C. The two instruments measure different things —
a registration rating for a steam cogen is limited by host steam, not ambient —
so the registration route is plausibly blind here. **This session does not
re-adjudicate the committed CHP cell**; it is flagged for whoever next touches
`derive_campd_temp_derate_params.py`.

---

## 6. G-2 — binding, and what it says about the object

Measured on the keeper's **own committed hourly sidecars** (P1 class dispatch)
against the model's own class capability. *Binding* is defined as the derate
removal exceeding the class's own unloaded headroom in that hour, so the class is
actually forced down; a removal inside headroom eats slack and cannot move the
marginal unit. Convention (A), MISO slopes:

| year | class | window | capability MW | dispatch MW | **headroom MW** | removal MW | **binding hours / 732** |
|---|---|---|---:|---:|---:|---:|---:|
| 2023 | CT_PEAKER | summer h12–17 | 17,764 | 4,504 | **13,260** | 953 | **3 (0.4 %)** |
| 2024 | CT_PEAKER | summer h12–17 | 17,750 | 4,725 | **13,025** | 924 | **5 (0.7 %)** |
| 2025 | CT_PEAKER | summer h12–17 | 17,653 | 6,070 | **11,583** | 1,004 | **1 (0.1 %)** |
| 2023 | CC_REGULAR | summer h12–17 | 21,782 | 20,125 | 1,658 | 598 | **11 (1.5 %)** |
| 2024 | CC_REGULAR | summer h12–17 | 20,983 | 19,755 | 1,228 | 547 | **35 (4.8 %)** |
| 2025 | CC_REGULAR | summer h12–17 | 19,935 | 18,476 | 1,459 | 553 | **11 (1.5 %)** |
| 2023–25 | both | **summer h00–05** | — | — | 16.3–17.4 GW / 2.7–4.9 GW | 197–463 | **0 (0.0 %)** |

**P4 confirmed far past its stated confidence.** I predicted non-binding in ≥60 %
of window hours; measured **95.2–99.9 %**.

**The reusable half — and it is an independent corroboration of miso-137.** The
model runs its CT_PEAKER fleet at **25.4 / 26.6 / 34.4 %** of capability in
summer h12–17, holding **11.6–13.3 GW idle**, in the very window it under-prices
by 41 %. Its CC fleet is tight (92–94 % loaded, 1.2–1.7 GW headroom) but the
peakers behind it are not. **MISO's summer-afternoon problem is not a capability
shortage — the model has ample quantity and the wrong price.** Any lever that
works by removing MW must first traverse ~12 GW of idle peakers before it reaches
the marginal unit.

---

## 7. The ceiling of the WHOLE family — why the successor would not change this

The named successor convention is a **summer**-mean anchor: the only one
consistent with a net-summer `pmax` basis, and the one that delivers the sign
reversal (§4.1). Building it is a mechanism change this session is not chartered
to make — but its **reach is bounded from measured inputs alone**, before anyone
writes it:

```
swing_aft(k) = slope_k · (T̄_aft − T̄_summer)        derate, afternoon
swing_night(k) = slope_k · (T̄_summer − T̄_night)    uprate, night
```

| year | CT swing (aft) | CT removal | CC swing (aft) | CC removal | **total removal** | **measured idle cushion** | **ratio** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 1.70 % | 302 MW | 0.90 % | 196 MW | **497 MW** | **17,544 MW** | **35.3×** |
| 2024 | 1.65 % | 294 MW | 0.87 % | 184 MW | **477 MW** | **18,828 MW** | **39.4×** |
| 2025 | 1.62 % | 286 MW | 0.86 % | 171 MW | **456 MW** | **13,720 MW** | **30.1×** |

*(cushion = the two armed classes' own idle headroom + unloaded coal capability
in the same hours; all from the keeper's committed sidecars.)*

**The ambient-derate family's maximum summer-afternoon reach in MISO is ~0.5 GW
against ≥13.7 GW of idle capability that would absorb it.** The parameter debate
(literature 0.0126 vs MISO-measured 0.00363) is therefore **moot**: even at the
literature slope the CT afternoon swing would be ~5.9 %, ~1.04 GW, still an order
of magnitude inside the cushion — and that slope is refused on MISO's own data
anyway. **Building the successor convention would not change this verdict.** It
may still be worth building for its own sake (it is the physically correct
treatment and it would remove a real basis inconsistency), but it is **not a
lever for the miso-137 object** and must not be chartered as one.

---

## 8. My prior, scored against interest

| prediction | stated | measured | verdict |
|---|---|---|---|
| **P1** summer night above the annual anchor in all 18 zone-years | conf. 0.90 | **18/18**, +3.64 … +9.14 °C | **RIGHT** |
| **P2** (A) double-derates against the net-summer basis | conf. 0.80 | CT −3.6…−4.1 %, CC −1.7…−1.9 % | **RIGHT** |
| **P3** MISO slope in 0.0015–0.0040 for CT vs 0.0126 | conf. 0.70 | **0.00363**, in range; ratio 3.5× (predicted 3–8×) | **RIGHT** |
| **P4** non-binding in ≥60 % of summer h12–17 hours | conf. 0.60 | **95.2–99.9 %** | **RIGHT, and badly under-stated** |
| net: P(arm licensed and solved) | 0.45 | refused at G-0 | **too high** |

**Where I was wrong, recorded.** (a) My claim that the non-anchored rescale is
inert at literature slopes is **overstated** — measured, it still removes 2.5–2.7 %
of annual capability there (§4.2). (b) My "other side" #1 — *"convention (B) may
be both admissible and exactly right"* — was **half right in the way that
mattered**: (B) *is* the physically correct within-summer reshape and it *does*
deliver the sign reversal I doubted the mechanism could produce. It failed for a
reason I had not anticipated (the year-round rescale), not for the reason I
leaned on. (c) My "other side" #3 — *"a small MW removal is not a small price
effect"* — is the one I most expected to lose to, and §7 is what settles it: the
cushion is 30–39×, not 2–3×, so the argument does not reach.

---

## 9. Which traps fired

* **TRAP 1 (level cut in shape clothing) — FIRED, on convention (B)**, and the
  pre-committed counter-measurement (the annual capability integral) is what
  caught it. Without it, (B)'s clean `summer_rel ≈ 1.0000` and textbook sign
  reversal would have read as a pure reshape. It is a **−6.8 % annual capability
  cut**.
* **TRAP 4 (convention shopping) — ARMED AND HELD.** The decision rule was fixed
  on basis consistency before any measurement; (A) was refused by a rule written
  before its number was known, and no convention was re-selected afterwards.
* **TRAP 3 (reporting h12–17 alone) — HELD.** h00–05 appears beside h12–17 in
  every table above, and it is where (A)'s failure is most visible.
* **TRAP 2 (tail channel) — NOT REACHED.** No solve, so no C3a movement to
  decompose.

---

## 10. What this licenses — nothing armed, and one honest successor

**No lever is licensed and none is proposed.** Concretely for the next session:

1. **The ambient-derate family is CLOSED as a candidate for the miso-137
   compression object** — not on fit, not on identification (the identification
   *succeeded*), but on **reach**: 30–39× too small, measured (§7). Re-testing it
   needs new evidence about the cushion, not about the slope.
2. **A real, bounded, non-lever defect is named:** the merchant classes carry a
   flat `SUMMER_CLASS_DERATE` (CC 10 %, CT 12.5 %) on top of a `pmax` that is
   already the EIA-860 **net-summer** rating, while MISO's own registration data
   puts the true summer↔winter capability spread at **+8.3 % (CC)** and
   **+15.8 % (CT)** — i.e. the flat derate and the basis are not obviously
   consistent. That is a rule 14 `[R-ACCURATE]` basis question with its own
   evidence and its own PREREG, **not** a price lever, and it should not be
   chartered as one.
3. **The successor convention** (per-class summer-mean anchor, no year-round
   rescale, selectable so the committed CHP identification is untouched) is
   specified above and is a **mechanism change** — rule 19/24, an owner call. Its
   value is basis correctness, and §7 already says what it will not buy.
4. **The object stands where miso-137 left it**, now with one more measured
   constraint: in summer h12–17 the model holds **11.6–13.3 GW of idle CT** and
   is short **price**, not quantity. A quantity mechanism has to get through that
   cushion first, and the next candidate should be **bounded against it before a
   solve is spent**.

---

## 11. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…138 precedent). Keeper unchanged.
**Rule 28(b) `[R-MECH-MATRIX]`** — `temp_dependent_derate` MISO **stays `K`**:
the cell's verdict is the committed **cogen** scope and this session did not
touch it. The **merchant** scope was tested and REFUSED at G-0; the cell's note
and `ev.M` citation are amended in this session to record that, and a §5.4 queue
stamp is written. No other ISO's cell moved (rule 28(d)).
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds no
`calibration-complete` marker. No out-of-training year was read, solved, scored
or registered.
**Rule 13 `[R-MEASURED]`** — every input is a physical or registration quantity
(zone dry-bulb, EIA-860 capability ratings, metered demand) entering as a
forward-reproducible formula; no estimator saw a price, a benchmark or a model
output. The keeper's committed sidecars were read for dispatch and headroom
only, never fed back.
**Rules 1 / 21 / 24** — nothing sized to any residual; no window or magnitude
from miso-137 entered any construction (its windows are used only to *localise*
reporting); no tuning channel created; nothing written under `data/raw/`.
**Rule 19 `[R-ONE-MECH]`** — no mechanism added. The existing treatments of the
same phenomenon (`SUMMER_CLASS_DERATE`, `gt_ambient_derate`,
`cc_nameplate_summer_derate`, `coal_nameplate_summer_derate`,
`COAL_SUMMER_MAX_CF`) were enumerated and are reconciled in §10(2), not stacked.
**Rules 20 / 23 / 25** — no free parameter added; no derive script re-run against
a residual; no non-MISO slope armed for MISO and no other ISO's artifact touched.
**Owner directive** — no C7 work.

---

## 12. The generalisable lesson — **A MECHANISM'S ANCHOR IS PART OF THE MECHANISM; BOUND ITS REACH BEFORE DEBATING ITS PARAMETER**

The charter's premise was that this was cheap: the mechanism is *already armed*,
so re-scoping it is a scope-and-identification question, not a mechanism change.
That premise failed twice over.

**First, the anchor.** An armed mechanism carries a **basis** — here, the
temperature the curve pivots about — and that basis is not a setting of the
mechanism, it *is* the mechanism. The annual-mean anchor cannot express a
within-summer sign reversal at **any** slope, because summer is above the annual
mean by construction. A re-scope inherits the convention, and a convention can be
structurally incapable of the effect you are re-scoping toward.

**Second, the reach.** The session's obvious debate was the parameter — literature
0.0126 against MISO's measured 0.00363, a 3.5× argument worth a rule-25 refusal.
That debate was **moot before it started**: the family's maximum reach in the
target window is ~0.5 GW against ≥13.7 GW of idle capability, so *no* value in
that range does anything. Bounding a mechanism's ceiling against the model's own
measured slack costs one probe and settles what a parameter argument cannot.

*Before spending a solve on a mechanism's parameter, check that its convention
can express the effect at all, and bound its reach against the cushion it has to
cross. An armed mechanism is not an available one.*

Family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain signature
is not a class-grain defect* → miso-132(a) *a missing rule is not a binding one*
→ miso-133 *measure the slack, on one basis* → miso-134 *binding is not
licensing* → miso-135 *the right quantity at the wrong grain is the wrong source*
→ miso-136 *an absence claim is a measurement, not a premise* → miso-137 *a
threshold is a hypothesis, not a definition* → miso-138 *measure an
identification's ceiling where the answer is known* → **miso-139 *a mechanism's
anchor is part of the mechanism; bound its reach before debating its
parameter***.

---

**Probes** `scripts/probes/_miso139_derate_gates.py`,
`scripts/probes/_miso139_g2_binding.py`,
`scripts/probes/_miso139_successor_bound.py` ·
**Records** `results/calibration/_miso139_derate_gates.json`,
`_miso139_g2_binding.json`, `_miso139_successor_bound.json` ·
**PREREG** `results/calibration/PREREG-miso139-ambient-derate-class-scope-2026-08-06.md` @ `6263f43d`.
