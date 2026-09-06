# FINDING — SCN-WS5A-LOAD / CAISO: the arm two lanes said not to solve, and it mattered

**Lane** SCN-WS5A-LOAD (CAISO) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Frozen pin** `1cc45bb2` ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Legs** REF · LOAD-HI · **LOAD-HI-ORGANIC (spent against two prior lanes' advice)** ·
**Scored against** SCN-WS4b §5.2 and SCN-WS4c §3.3.

---

## 0. Bottom line

1. **The ORGANIC arm was worth solving, and two lanes said it wasn't.** WS-4b recorded CAISO as
   `high := mid` and WS-4c declined to solve it — *"solving them would have produced a
   guaranteed-zero delta"*. Measured: **ΔCO2 −0.011 → −0.113 Mt and Δpeak −0.40 → −1.92 GW at
   identical energy.** Small, but definitively non-zero. Their claim was correct at their pin
   and stale at HEAD, because SCN-LOAD read the CEC Form 1.1c *Local Reliability Scenario*
   after it (`high` 4,240 MW vs `mid` 1,622 MW at 2030). **The zero-LP phase 0 paid for itself.**
2. **WS-4c's one CAISO SPLIT resolves at the horizon, in WS-4b's favour.** WS-4c measured the
   import line flat at 2026 because the increment landed on a **zero-EF solar rung**. At the
   horizon that headroom exhausts and the line moves: **+0.633 Mt at 2030**, first motion in
   that year exactly. This was **my registered prediction P-6 for CAISO** and it lands (§5).
3. **CAISO's backstop ladder binds and I3 appears** — WS-4b's conditional (*"I3 may re-appear
   in 2029–2030 if the ladder binds"*) fires one year early, at 2028, with the ladder running
   to 14,695 MW.
4. **CAISO carries the campaign's largest CCS fleet (45.16 TWh) at its lowest implied rate
   (0.1496 t/MWh)** — still ~**4×** what 90 % capture implies. Contamination ≈**5.04 Mt = 16.2 %**
   of its 2030 level (§4), and the spread across ISOs forces a sharper statement of the defect.
5. **CAISO has the campaign's smallest energy divergence from its board key** (+0.9 → +2.5 %)
   yet a **+20.7 %** CO2 divergence — a gap that is itself the retrofit fleet.

---

## 1. What was solved

Three legs, 15 solve-years, ~65 min. REF 2.5–11.5 min per solve-year at 4.2–4.7 GB peak RSS
(the 11.5 min first year is fleet build; later years settle at ~2.7). All rc=0.

## 2. THE PHASE-0 VINDICATION

| year | LOAD-HI CO2 | ORGANIC CO2 | Δ | LOAD-HI peak | ORGANIC peak | Δ GW | energy |
|---|---|---|---|---|---|---|---|
| 2026 | 34.301 | 34.312 | −0.011 | 51.61 | 52.01 | **−0.40** | identical |
| 2028 | 40.118 | 40.185 | −0.067 | 55.62 | 56.78 | **−1.16** | identical |
| 2030 | 41.390 | 41.503 | **−0.113** | 60.14 | 62.06 | **−1.92** | identical |

Energy is invariant between the arms and the peak is **lower** under LOAD-HI — the flat block's
shape signature, precisely the relocate mechanism. The effect is real, modest, and would have
been recorded as zero had this lane inherited the prior conclusion instead of re-measuring.

**The general lesson, stated for the record:** WS-4b and WS-4c were both *correct at their own
pins*. What changed underneath them was an owner-ruled data intake (S4/D-4). A pre-declaration
chain is only as current as its constants, and re-running the zero-LP census is cheap enough
(~90 s) that inheriting a degeneracy claim is never worth the saving.

## 3. SCORING — WS-4b §5.2, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c |
|---|---|---|---|---|
| **(a)** | backstop `gas_ct` sized to the requirement gap, ladder-capped; REF builds **1,396** / 2,793 / 2,181 / 1,855 MW in 2027–30 | LOAD-HI ladder 0 / **1,396.4** / 4,189.2 / 9,774.8 / 14,695.3 MW — the 2027 figure matches **exactly**; it then runs far past their REF path as the gap widens | **HIT** | untestable at T0 |
| **(b)** | I12 + I7 at `mid`; I7 misses widen ≤ ~5.5 GW; backstop share rises above 52.6 %; **I3 may re-appear 2029–30 if the ladder binds** | REF `{I7, I12}` = the board's bare key; **both load arms gain I3**, from **2028** (4,955 MWh → 106,163 MWh by 2030), ladder at 14,695 MW | **HIT**, timing one year early | HIT at 2026 |
| **(d)** | `backstop_built_mw`/`_mwh` + `unserved_mwh` beside CO2 | all present; backstop non-zero from 2027, unserved non-zero from 2028 | **HIT** | HIT |
| **(e)** | import line **UP**, same sign as CO2; ceiling ~7–11 Mt if the whole 7,500 MW headroom were used | **0.000 through 2029, then +0.633 Mt at 2030** — up, same sign, two orders inside their ceiling | **HIT at the horizon** | **SPLIT** at T0 → **resolves** |

**The (e) resolution is the campaign's cleanest example of a T0 verdict that needed the
horizon.** WS-4c's SPLIT was not a WS-4b error: they measured that CAISO's marginal import rung
at 2026 is `WECC_import_DSW_solar_PV` at **EF 0.000**, so imports rose (+0.271 TWh) while the
CO2 line did not. Their inference — that the ceiling *"is not wrong, it is simply never
approached"* — held only while the zero-EF headroom lasted. It lasts through 2029 and is gone
by 2030. Both lanes were right about different years.

**(c) what a reader may and may not conclude.** *May:* the direction and size of the response;
that CAISO's backstop ladder binds and sheds load past 2028; the shape share of the DC block
(§2); that leakage begins at 2030 and is small. *May not:* CAISO's CO2 **levels** — 16.2 % of
the 2030 figure is mis-rated CCS (§4); the 2029–2030 ΔCO2 as a clean emissions response
(106 GWh shed, small but non-zero); a deployment forecast — CAISO is a **HOLD** ISO whose REF
carries I7 and I12.

## 4. `gas_cc_ccs` — the campaign's largest fleet, and a sharper statement of the defect

| CAISO 2030 REF | TWh | Mt | t/MWh |
|---|---|---|---|
| `gas_cc` | 53.090 | 20.206 | 0.3806 |
| **`gas_cc_ccs`** | **45.161** | **6.754** | **0.1496** |
| `gas_ct` | 7.386 | 3.535 | 0.4786 |
| `import` | 46.125 | 0.000 | 0.0000 |

CAISO retrofits **2,903 → 8,687 MW** (2028 → 2030) under CARB — the large-and-early pattern,
completing the corrected mechanism at **6 of 6 ISOs**. Contamination: intended
45.161 × ~0.038 = **1.72 Mt**; measured **6.754 Mt**; overstatement ≈**5.04 Mt = 16.2 %** of
CAISO's 31.16 Mt.

**What the four-ISO spread forces me to say more carefully.** The implied CCS rate is
**0.1496 (CAISO) · 0.2578 (NYISO) · 0.3719 (NEISO) · 0.6063 (PJM)** — a **4× spread**, and the
ratio to each ISO's own unabated `gas_cc` runs **0.39 / 0.62 / 1.01 / 1.56**. A uniform
"emission rate never reduced" defect would not produce that. So the honest claim is **not**
that capture is never applied; it is the absolute one, which every ISO satisfies:

> `ccs_capture_rate = 0.90` implies **≤ ~0.05 t/MWh** on any gas-CC fleet. Every measured
> retrofit class sits **4× to 15×** above that. No ISO's retrofit fleet emits at anything close
> to the declared capture rate.

Unit selection within each class plausibly explains the *spread*; nothing explains the *level*.
All 16 legs solved at `1cc45bb2`, **before** capx D77 landed, so every figure here describes
the pre-repair seam.

## 5. The implied MARGINAL rate, and my predictions

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | ratio |
|---|---|---|---|---|---|
| 2026 | +2.995 | +7.150 | 0.4189 | 0.3886 | 1.08 |
| 2028 | +6.799 | +16.109 | 0.4221 | 0.3717 | 1.14 |
| 2030 | +10.231 | +24.055 | 0.4253 | 0.3606 | 1.18 |
| *WS-4c T0* | *+2.544* | *+6.28* | *0.405* | *0.387* | *1.05* |

- **P-2 HIT.** All rates (0.419–0.425) inside ±25 % of WS-4c's 0.405 → [0.304, 0.506].
- **P-3 HIT.** Gas-dominated ratio stays **≥ 1.0** in every year (1.08 → 1.18), as predicted.
- **P-6 HIT — the most specific prediction I registered.** I wrote: *"CAISO is the open one …
  I predict that at the horizon CAISO's zero-EF headroom is **exhausted** and the line becomes
  **positive by 2029–2030** — the first year it moves is the number to report."* It moves at
  **2030**, +0.633 Mt, having been exactly 0.000 in every prior year.
- **P-4 SPLIT.** The ratio rises 1.08 → 1.18 but was already above 1.0, so the "drift toward
  1.0" framing does not apply to a gas ISO; the direction is right, the framing was coal-shaped.
- **P-5 MISS.** Fossil share of Δenergy 0.96 / 0.96 / 0.96 / 0.95 / 0.95 — flat, not falling.

## 6. STOP gate — PASS

S1 CO2 and price rise ✓ · S2 ratio 1.08–1.18 inside [0.5, 2.0] ✓ · S3 footprint confined to
fossil classes; `import` emissions 0.000 in the by-fuel table (the reported-only line is
separate) ✓ · S4 identity — the two load arms' energy is identical to 0.1 TWh ✓ · S5 both load
arms gain I3, which is WS-4b's own predicted mechanism, not a collateral flip ✓. Killed nothing.

## 7. Routed

1. **CAISO is in card D-10's re-solve set** (r#10 already names it) — 45.16 TWh of mis-rated
   `gas_cc_ccs`, 16.2 % of its 2030 level.
2. **The CCS rate spread (4×) across ISOs is unexplained** and is not what a uniform
   never-reduced rate predicts. Whoever owns the D77 verification should check that the repair
   lands uniformly, using these four pre-fix rates as the before-picture.
3. **`caiso-2026-2030-d46-remeasure` is stale at HEAD** — +2.5 % energy but **+20.7 % CO2** at
   2030, the divergence concentrated in the retrofit fleet rather than in load.

## 8. Duties

No default moved, no knob moved, no `ScenarioConfig` field added; **DOF ledger: zero**.
Campaign YAML, reporting/collation/registration scripts, `ccs.py`, all of `src/`: read only.
`program-status.json`, `ff-verdicts.json`, backcast namespace: untouched. Invariant FAILs
declared in the same commit as the registration. Rule 15/§7.5 forecast namespace only; rule 27
verified; rule 29(c) no screen/control bundle; backcast byte-identity untouched.
