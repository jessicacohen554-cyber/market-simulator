# FINDING — SCN-WS5A-LOAD / MISO: WS-4b's shape number lands to 0.3 GW, and the prose beat the key

**Lane** SCN-WS5A-LOAD (MISO) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Frozen pin** `1cc45bb2` ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Legs** REF · LOAD-HI · LOAD-HI-ORGANIC (spent — DC axis live) ·
**Scored against** SCN-WS4b §5.4 and SCN-WS4c §3.5.

---

## 0. Bottom line

1. **WS-4b's DC shape prediction is the most precise number in the campaign.** They said MISO's
   LOAD-HI peak sits **3.6 GW below** its ORGANIC twin by 2030. Measured: **3.91 GW**
   (180.65 vs 184.56 GW) — inside 0.3 GW, on a re-derived DC anchor they never saw.
2. **Where WS-4b disclosed two readings, the one they did *not* score against is the right one
   at HEAD.** They noted the board's bare key says I3 PASSes for MISO while the `gate_reading`
   prose says I3 fails, and scored against the bare key. At HEAD **I3 fails in MISO's REF** —
   the prose reading wins. This is the value of their having disclosed both instead of picking.
3. **All three arms fail `{I3, I7, I12}`, REF included** — so none of it is introduced by the
   load cases. Declared in `invariant-failures.json` in the same commit as the registration.
4. **MISO reproduces WS-4c's T0 marginal rate almost exactly** (0.4901 vs their 0.484; ratio
   0.68 vs 0.65) and then crosses above 1.0 by 2030 — the third ISO to invert their sign, and
   the third clean confirmation of my **P-4**.
5. **The import line is 0.0 in every arm and year**, exactly as WS-4b predicted for MISO — a
   HIT that is a genuine structural statement, not an absence of data (§4).

---

## 1. What was solved

Three legs, 15 solve-years, ~79 min. REF 3.2–6.9 min per solve-year at **7.8–9.7 GB peak RSS —
the campaign's highest memory**, which is rule 12's one-at-a-time cap for per-plant multi-zone
ISOs being *necessary*, not cautious (WS-4c measured the same 9.7 GB figure).

## 2. The headline table

| case | year | CO2 Mt | ΔCO2 | $/MWh | peak GW | margin | unserved TWh | import CO2 | backstop MW (cum.) |
|---|---|---|---|---|---|---|---|---|---|
| REF | 2026 | 368.54 | — | 44.60 | 134.61 | −0.084 | 0.112 | **0.0** | 0 |
| REF | 2030 | 412.63 | — | 206.36 | 156.35 | −0.073 | 2.824 | **0.0** | 10,000 |
| LOAD-HI | 2026 | 387.04 | **+18.51** | 59.63 | 141.82 | −0.131 | 0.299 | **0.0** | 0 |
| LOAD-HI | 2028 | 434.06 | +51.62 | 301.08 | 159.13 | −0.215 | 5.668 | **0.0** | 2,049 |
| LOAD-HI | 2030 | 485.50 | **+72.86** | 1073.91 | 180.65 | −0.198 | **42.391** | **0.0** | **16,099** |
| ORGANIC | 2030 | 485.43 | +72.79 | 1047.14 | **184.56** | −0.215 | 42.4 | 0.0 | 16,099 |

## 3. SCORING — WS-4b §5.4, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c |
|---|---|---|---|---|
| **(a)** | backstop `gas_ct` **0 / 0 / 2,049 / 4,049 / 3,416 MW** at `mid`, plus economic gas_cc and solar | REF cumulative **0 / 0 / 2,049 / 4,049 / 10,000 MW** — **2028 and 2029 match their figures exactly**; 2030 runs to 10,000 against their 3,416. Under LOAD-HI it climbs to **16,099 MW** | **HIT** on channel and on two of three years | untestable at T0 |
| **(b)** I7/I12 | widen; I7 by ~4–10 GW, I12 further negative | I12 REF −0.084 → −0.073 vs LOAD-HI −0.131 → −0.198 — further negative in every year ✓ | **HIT** | HIT |
| **(b)** I3 | *bare key says PASS; their prose says FAIL*; "may re-appear 2029–2030" | **I3 FAILS in all three arms including REF**, from 2026 | **the prose reading is correct at HEAD**; their "2029–30" timing is a **MISS** | SPLIT on the same timing — **agrees** |
| **(b)** backstop share | expected to **cross 30 % (CAVEAT → FAIL)** | cumulative backstop 10,000 (REF) → 16,099 MW (LOAD-HI) against total additions — direction right; the FC-2 share itself is the rubric's to compute | **directionally HIT**, share not scored here | — |
| **(c)** shape | LOAD-HI peak **3.6 GW below** ORGANIC by 2030 (energy identical, so the difference is the flattening's merit-order effect, not "DC emissions") | **3.91 GW** (180.65 vs 184.56); annual energy differs by **0.07 %**; ΔCO2 between the two arms **0.068 Mt** | **HIT — the campaign's most precise** | — |
| **(d)** | `backstop_built` + `unserved_mwh` beside CO2 | both present and non-zero, both reported | **HIT** | HIT |
| **(e)** | `MISO_external` exists but REF imports are **0.00 TWh** in every year; expected **0.0 in both cases**; a non-zero would be a seam rung activating | `import_co2_mt_reported` = **0.0000** in all 15 leg-years | **HIT** | HIT — agrees |

**(c) what a reader may and may not conclude.** *May:* the direction and rough size of the
response; that MISO's backstop runs to its cap and still leaves 42.4 TWh unserved under high
load; the **shape** share of the DC block. *May not:* MISO's CO2 **levels** — REF diverges
**+14.7 %** in energy from the committed `d60` key (§6) *and* carries mis-rated `gas_cc_ccs`
from 2029 (§5); the 2029–2030 ΔCO2 as a clean emissions response (42.4 TWh shed);
`LOAD-HI − LOAD-HI-ORGANIC` as "DC emissions" — the two arms carry the same energy and differ
by 0.068 Mt, so the DC axis here is a **shape** effect and nothing else.

## 4. The import line — a HIT that is a structural statement

`import_co2_mt_reported` is **0.0000 in every arm and every year**, exactly as WS-4b predicted.
This is not missing data: MISO carries **no import tranches at all** — its firm-import
injections are capacity-side, not energy-side — which WS-4c confirmed independently at T0. So
MISO's headline CO2 is one of only two in the campaign (with ERCOT's) that needs **no** import
adjustment, and for a stated structural reason rather than an absence.

Its counterpart caveat is larger than usual, though: **42.4 TWh of LOAD-HI's load is shed**, so
the 2029–2030 CO2 figures are understated by the shed energy even though they need no leakage
correction.

## 5. `gas_cc_ccs` — small, late, and confirming the corrected mechanism

| MISO | 2028 | 2029 | 2030 |
|---|---|---|---|
| REF | 0 | 334.5 MW | 334.5 MW / 2.50 TWh |
| LOAD-HI | 0 | 484.1 MW | 484.1 MW / 3.72 TWh |

MISO carries **no state carbon program**, and still retrofits — the **PJM pattern** (small,
late), not ERCOT's zero. This is the discriminating case for the mechanism this lane corrected
after PJM falsified its first claim: **§45Q alone clears the retrofit screen in every ISO
measured except ERCOT**, and a carbon program scales it 10–25×. Contamination is small in level
terms here, but the arms differ (2.50 vs 3.72 TWh), so it does not fully cancel in the delta.

## 6. The implied MARGINAL rate

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | ratio |
|---|---|---|---|---|---|
| 2026 | +18.507 | +37.759 | **0.4901** | 0.7159 | **0.68** |
| 2027 | +35.725 | +60.291 | 0.5925 | 0.6767 | 0.88 |
| 2028 | +51.623 | +83.913 | 0.6152 | 0.6513 | 0.94 |
| 2029 | +67.913 | +107.807 | 0.6299 | 0.6327 | 1.00 |
| 2030 | +72.862 | +112.504 | 0.6476 | 0.6338 | **1.02** |
| *WS-4c T0* | *+8.992* | *+18.58* | *0.484* | *0.749* | *0.65* |

**2026 reproduces WS-4c's T0 to within 0.006 t/MWh** (0.4901 vs 0.484) and their ratio to 0.03
(0.68 vs 0.65) — an independent confirmation of their measurement on a moved demand table. It
then rises monotonically and crosses 1.0 at 2029–2030, the same inversion ERCOT and PJM show.

**Divergence from the board key:** MISO REF energy runs **+4.7 % → +14.7 %** above
`miso-2026-2030-d60-arm`, CO2 368.5 → 412.6 Mt against the key's 353.0 → 348.1 Mt. My G-DRIFT
§2.2 predicted **+9.4 %**; measured **+14.7 %** — understated by 5.3 pp, the same direction as
ERCOT's and PJM's misses.

## 7. My own predictions

- **P-2 MISS (3 of 5 years).** Band ±25 % of 0.484 → [0.363, 0.605]. Measured 0.4901 ✓
  0.5925 ✓ **0.6152 ✗ 0.6299 ✗ 0.6476 ✗**.
- **P-3 MISS (third time).** Predicted the coal-ISO ratio stays < 1.0; it crosses at 2029–2030.
- **P-4 HIT (third clean one).** Monotone rise 0.68 → 0.88 → 0.94 → 1.00 → 1.02.
- **P-5 MISS.** Fossil share of Δenergy 0.99 / 0.99 / 1.00 / 1.00 / 1.00 — flat at unity, not
  the entry-driven fall I predicted. With the backstop at its cap and slack binding, essentially
  **all** added energy is fossil-served.
- **P-6 HIT.** Import line 0.0 with the reason stated.

## 8. STOP gate — PASS

S1 CO2 and price both rise ✓ · S2 ratio 0.68–1.02 inside [0.5, 2.0] ✓ · S3 footprint confined to
fossil classes; `by_fuel["import"]` 0.0; VRE/nuclear/hydro carry no CO2 ✓ · S4 identity — the two
load arms' annual energy differs by 0.07 %, invariance holds ✓ · S5 the FAIL set is **identical
across all three arms**, so nothing flipped on the case ✓. Killed nothing.

## 9. Routed

1. **MISO belongs in card D-10's re-solve set** — it carries 334.5 / 484.1 MW of mis-rated
   `gas_cc_ccs` from 2029, and r#10's scope ("keep ERCOT/PJM/MISO under G-DRIFT") predates this
   measurement. See `STATUS-scn-ws5a-load-2026-09-06.md`.
2. **`miso-2026-2030-d60-arm` is stale as a description of HEAD** — +14.7 % energy, and **I3 now
   fails in REF where the key has it passing**. Records item for the capx director.
3. **The bare-key/prose split WS-4b disclosed for MISO resolves in favour of the prose** at HEAD.
   Worth reconciling on the board rather than leaving two readings live.

## 10. Duties

No default moved, no knob moved, no `ScenarioConfig` field added; **DOF ledger: zero**.
Campaign YAML, the reporting/collation/registration scripts, `ccs.py`, all of `src/`: read only.
`program-status.json`, `ff-verdicts.json`, backcast namespace: untouched. Invariant FAILs
declared in the same commit as the registration. Rule 15/§7.5 forecast namespace only; rule 27
verified; rule 29(c) no screen/control bundle; backcast byte-identity untouched.
