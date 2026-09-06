# FINDING — SCN-WS5A-LOAD / NYISO: the cleanest ISO, and the sharpest anchor diagnostic

**Lane** SCN-WS5A-LOAD (NYISO) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Frozen pin** `1cc45bb2` ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Legs** REF · LOAD-HI · LOAD-HI-ORGANIC (spent — phase 0 measured a live DC axis) ·
**Scored against** SCN-WS4b §5.5 and SCN-WS4c §3.6.

---

## 0. Bottom line

1. **All three arms are structurally clean: 14/14 invariants PASS, zero unserved energy,
   zero backstop firing in every year.** NYISO is the campaign's best-behaved ISO.
2. **The sharpest diagnostic in the campaign of what SCN-LOAD's re-derivation did.** WS-4b's
   **ORGANIC** peak prediction lands within **0.4 GW** (predicted 30.2 → 32.4, measured
   30.22 → 32.77); their **LOAD-HI** peak prediction misses by **3.3 GW** (predicted
   29.6 → 29.0, measured 30.08 → 32.27). The `mid` DC anchor survived SCN-LOAD essentially
   unchanged; the `high` anchor was **retired** (10 GW → 2,567 MW). Same document, same
   method, two anchors — and the verdict splits exactly along which anchor moved.
3. **The DC axis is now nearly degenerate here.** The high−mid gap is **0.851 GW at 2030**
   (WS-4b read ~7 GW), so LOAD-HI and LOAD-HI-ORGANIC differ by only 0.011–0.079 Mt of CO2.
   The ORGANIC arm was correctly spent under phase 0, but it buys very little at HEAD.
4. **CCS exposure confirmed, as predicted from the state-carbon mechanism** (§2): 6,475 MW /
   24.42 TWh by 2030 in REF, contaminating **≈5.29 Mt = 25.3 %** of the reported 2030 level.
5. **NYISO's leakage line is the campaign's largest so far** (§4): imports carry
   10.58 → 12.22 Mt, and the LOAD-HI increment is **+0.12 → +0.96 Mt**, i.e. **7 – 25 % of
   the in-ISO ΔCO2**. Reading `emissions_mt` alone here understates by up to a quarter.

---

## 1. What was solved

Three legs, 15 solve-years. LOAD-HI was the campaign's slowest leg (21m37s); REF ≈2 min/yr;
peak RSS 2.5–3.3 GB. All rc=0.

**Disclosed condition, checked not assumed:** NYISO's `confirmed-retirements` clean partition
is **absent**, and the raw registry declares itself *"DATA NEEDED (zero qualifying rows)"* —
so this is correct behaviour for an empty registry, not a build defect (the other five ISOs
all carry partitions; my `data/clean` built 56/56 with zero failures). Consequence: NYISO's
**step-0 confirmed-exit channel is inert**, and its fossil exits are decided by the step-1
dated channel and the step-3 economic screen alone. That is an upstream data-collection gap,
not this lane's to fix.

## 2. The headline table

| case | year | CO2 Mt | ΔCO2 | $/MWh | peak GW | margin | unserved | import CO2 Mt | backstop |
|---|---|---|---|---|---|---|---|---|---|
| REF | 2026 | 23.692 | — | 50.19 | 29.39 | 0.185 | 0.0 | 10.45 | 0 |
| REF | 2030 | 20.893 | — | 61.22 | 30.10 | 0.201 | 0.0 | 11.68 | 0 |
| LOAD-HI | 2026 | 25.384 | +1.692 | 51.42 | 30.08 | 0.158 | **0.0** | 10.578 | **0** |
| LOAD-HI | 2028 | 27.665 | +3.553 | 55.67 | 31.13 | 0.118 | **0.0** | 11.670 | **0** |
| LOAD-HI | 2030 | 26.234 | **+5.340** | 64.66 | 32.27 | 0.120 | **0.0** | 12.218 | **0** |
| ORGANIC | 2030 | 26.313 | +5.420 | 64.95 | 32.77 | 0.103 | 0.0 | — | 0 |

`gas_cc_ccs` (ruling-S5 flag): **0 MW in 2026–2027; 2,998 → 5,475 → 6,475 MW in 2028–2030**
(REF), generating 10.40 → 24.42 TWh. See §5.

## 3. SCORING — WS-4b §5.5, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c |
|---|---|---|---|---|
| **(a)** | backstop armed, **never fires**; economic entry carries it | `backstop_built_mw` = **0.0** in all three arms, all five years | **HIT** | HIT — agrees |
| **(b)** substance | 14/14 PASS at `mid`; no backstop, no slack | **14/14 PASS in all three arms**; `unserved_mwh` = 0.0 throughout | **HIT** | HIT |
| **(b)** shape/artefact | peak **flat-to-falling** (29.6 → 29.0 GW) as the block reaches 35 % of energy, so I7/I12 read **better** than REF; possible **high-side** I12 exit 2029–30 | peak **rises** 30.08 → 32.27 GW, **above** REF in every year; margin **worse** than REF (0.158 → 0.120 vs 0.185 → 0.201); **no** high-side exit | **MISS** | SPLIT ("not visible at 2026") → at the horizon it is **reversed**, not merely invisible |
| **(d)** | `backstop_built` (expect 0.0) + `unserved` (expect 0.0) printed, *because a non-zero is the finding* | both 0.0, both printed | **HIT** | HIT — agrees |
| **(e)** | import line **UP**, sign +; HQ_hydro at firm depth so increments land on 0.428 rungs | +0.124, +0.345, +0.304, **+0.962**, +0.535 Mt — positive in all five years | **HIT** | HIT — agrees |

**The (b) shape miss is fully attributable, and that is the finding.** WS-4b's arithmetic was
correct on the constants it was written on; the `high` DC anchor has since been retired —
`constants.py` says so in its own words: *"The former high (10 GW by 2031) was the raw
interconnection QUEUE … a different quantity from the forecast."* At 2,567 MW the block is
**35 % → 11 % of energy**, far too small to flatten the peak below REF. The control that
proves it is their own ORGANIC row, which used the `mid` anchor SCN-LOAD left alone and lands
within 0.4 GW.

**(c) what a reader may and may not conclude.** *May:* that NYISO meets high load without
shedding a MWh or firing the backstop; the direction and size of the in-ISO response; that
the marginal rate sits just above fleet average. *May not:* any 2028–2030 CO2 **level**
(§5); that `LOAD-HI − LOAD-HI-ORGANIC` measures "DC emissions" — at HEAD the two arms differ
by ≤0.079 Mt, so the DC axis is nearly degenerate here; a total without the import line, which
carries up to a quarter of the delta (§4).

## 4. The leakage line — the campaign's largest so far

| year | Δ in-ISO CO2 Mt | Δ `import_co2_mt_reported` Mt | leakage as % of Δ |
|---|---|---|---|
| 2026 | +1.692 | +0.124 | 7.3 % |
| 2027 | +2.474 | +0.345 | 13.9 % |
| 2028 | +3.553 | +0.304 | 8.6 % |
| 2029 | +3.894 | **+0.962** | **24.7 %** |
| 2030 | +5.340 | +0.535 | 10.0 % |

Absolute import CO2 runs **10.45 → 12.22 Mt** against in-ISO emissions of 20.9 – 27.7 Mt —
imports carry roughly **40–50 %** as much CO2 as NYISO emits itself. Sign is **+** in every
year, compounding the in-ISO increase exactly as WS-4b's (e) says. Compare NEISO, where the
same line **changes sign** (§3(e) of the NEISO FINDING): the two RGGI ISOs behave differently
at the seam, so leakage sign is not a regional constant.

## 5. `gas_cc_ccs` — the S5 flag, second confirmation

The prediction registered in the NEISO FINDING (§2.2) — that the retrofit screen is armed by
a **state carbon program**, independent of any campaign carbon override — is confirmed a
second time. NYISO carries RGGI and shows CCS; ERCOT carries none and shows zero.

| NYISO 2030 REF | generation TWh | emissions Mt | implied t/MWh |
|---|---|---|---|
| `gas_cc` | 27.785 | 11.490 | 0.4135 |
| **`gas_cc_ccs`** | **24.423** | **6.295** | **0.2578** |
| `gas_ct` | 2.024 | 1.089 | 0.5382 |

**The selection-robust test:** `ccs_capture_rate = 0.90` implies **≤ ~0.05 t/MWh** on any
gas-CC fleet. Measured **0.2578** — about **6× too high**. (The comparative reading, that the
retrofitted class is *lower* than the unabated residual here while *higher* in NEISO, is
confounded by which units the screen picked and is not used; the absolute test is what
travels. The NEISO FINDING was amended to the same standard.)

**Contamination:** intended ≈24.423 × 0.041 = **1.00 Mt**; measured **6.295 Mt**;
overstatement **≈5.29 Mt = 25.3 %** of NYISO's reported 2030 total of 20.893 Mt. 2026–2027
are clean; 2028–2030 are not. The **delta** is better protected than the level — the two arms
carry near-identical retrofit fleets — but not perfectly (REF 6,475 vs LOAD-HI 6,621 MW).

## 6. The implied MARGINAL rate — WS-4c's NYISO result holds

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | ratio |
|---|---|---|---|---|---|
| 2026 | +1.692 | +3.876 | 0.4364 | 0.4043 | 1.08 |
| 2027 | +2.474 | +5.607 | 0.4412 | 0.4045 | 1.09 |
| 2028 | +3.553 | +8.098 | 0.4388 | 0.4066 | 1.08 |
| 2029 | +3.894 | +9.002 | 0.4326 | 0.4081 | 1.06 |
| 2030 | +5.340 | +12.559 | 0.4252 | 0.3708 | 1.15 |
| *WS-4c T0* | *+1.637* | *+3.88* | *0.422* | *0.402* | *1.05* |

**This is the one ISO where WS-4c's marginal-rate finding survives the horizon intact** —
implied rate within 0.02 t/MWh of their T0 value in every year, ratio above 1.0 throughout,
exactly as a gas-dominated stack predicts. Contrast ERCOT, where the sign inverted under
shortage. (2028–2030 fleet averages inherit §5's defect; the ratios there are indicative.)

## 7. My own predictions

- **P-2 HIT.** All five rates (0.4252–0.4412) inside ±25 % of 0.422 → [0.317, 0.528].
- **P-3 HIT.** Ratio ≥ 1.0 in every year (1.06–1.15), as predicted for a gas-dominated ISO.
- **P-5 MISS.** Fossil share of Δenergy: 0.91, 0.86, 0.91, 0.80, 0.91 — no monotone fall.
- **P-6 HIT.** Import line rises, sign + in all five years.
- **G-DRIFT §2.2 HIT (the most precise).** Predicted NYISO REF −0.1 % vs the committed key;
  measured **−0.1 % → −0.2 %**.

## 8. STOP gate — PASS

S1 CO2 and price rise ✓ · S2 ratio 1.06–1.15 inside [0.5, 2.0] ✓ · S3 footprint confined to
fossil classes; nuclear/hydro/solar/wind Δ = 0.000; `by_fuel["import"]` emissions 0.0 ✓ ·
S4 identity — LOAD-HI and ORGANIC energy differ by ≤0.001 TWh, invariance holds ✓ ·
S5 all three arms 14/14 PASS, nothing flips ✓. Killed nothing, promoted nothing.

## 9. Routed

1. **`gas_cc_ccs` in a load-only campaign, second ISO** — reinforces the NEISO routing that
   ruling S5's "no CCS exposure" premise is false. Two of two state-carbon ISOs confirm it.
2. **NYISO's confirmed-retirement registry is empty ("DATA NEEDED")**, so step 0 is inert for
   this ISO in every forecast run, not just this campaign. Data-collection item.
3. **Leakage sign is not a regional constant** — NYISO's import line is + in all five years
   while NEISO's flips negative in 2028–2029, both RGGI. Worth a seam-level look by whoever
   owns interchange.

## 10. Duties

No default moved, no knob moved, no `ScenarioConfig` field added; **DOF ledger: zero**.
Campaign YAML, `report_scenario_deltas.py`, `register_forecast_run.py`, `ccs.py` and all of
`src/`: read only. `program-status.json`, `ff-verdicts.json`, backcast namespace: untouched.
Rule 15/§7.5 forecast namespace only; rule 27 verified; rule 29(c) no screen/control bundle;
backcast byte-identity untouched.
