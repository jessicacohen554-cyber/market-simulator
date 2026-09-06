# PRECOMMIT — SCN-WS4c: the LOAD-HI T0 battery and the two T1-F deployment legs

**Lane** SCN-WS4c · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws4c-load-hi-probes-o85iyi` · **Data profile** `all` ·
**Charter** `docs/forecast-development-plan-2026-07.md` §7 "WS-4" item 4 /
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-4 item 4, §3.5, §4 ·
**Pin** `origin/main` `5fdd4374` (desk pin `3dcf1b22` + the merges since; none on the SCN track) ·
**Rule** 29 `[R-SCREEN]` — this document is pushed BEFORE the first solve and is not revised after it.

**What this lane is.** SCN-WS4b wrote down, before any `LOAD-HI` number existed, how each of
the six ISOs' high case is to be read — mechanism, invariant widening, what the CO2 delta may
and may not say, the exact delta-table line, and the expected import direction
(`docs/handoffs/load-hi-adequacy-reading-2026-09-06.md`; the scoring table is
`FINDING-scn-ws4b-2026-09-06.md` §2). **This lane is the test of that document.** I score each
pre-declared reading HIT / MISS / SPLIT with the number that decides it. I do not revise WS-4b's
document, and a miss is not a reason to re-read the case: the pre-declaration is fixed and I am
the instrument.

---

## 1. The arms, named before the solve

**Screen year: 2026** (T0). It is named here, before the screen runs, and it is the year the
mechanism's own measured footprint is largest per §2 below — not the year with the biggest
residual. Both T1 legs are 5 solve-years (2026–2030) and both T0 and T1-F sit inside the
§2.1b window cap, so no full-solve authorization is implicated.

| # | leg | ISO | cases | solve-years | invocation count |
|---|---|---|---|---|---|
| 1 | T0 | ERCOT | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 3 |
| 2 | T0 | CAISO | REF · LOAD-HI | 2026 | 2 |
| 3 | T0 | PJM | REF · LOAD-HI | 2026 | 2 |
| 4 | T0 | MISO | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 3 |
| 5 | T0 | NYISO | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 3 |
| 6 | T0 | NEISO | REF · LOAD-HI | 2026 | 2 |
| 7 | T1-F | ERCOT | REF · LOAD-HI | 2026–2030 | 2 |
| 8 | T1-F | NEISO | REF · LOAD-HI | 2026–2030 | 2 |

**15 T0 arms + 4 T1-F arms.** Campaign `scn-ws4-probe`, disjoint from SCN-WS1b's
`scn-ws1-probe`. Cases are the committed `configs/scenario_campaign_matrix.yaml` keys, applied
through the runner's own `--set` seam; REF overrides nothing (plan §3.0).

**Why the ORGANIC arm is spent on only three ISOs** — a zero-LP fact, not a judgement: §2.

---

## 2. Rule 29 phase 0 — the zero-LP census, run BEFORE any arm was scheduled

`docs/handoffs/scn-ws4c/phase0_loadhi_census.py` resolves each case through
`apply_iso_scenario_defaults` + the runner's own `apply_set_overrides`, so the census cannot
drift from what `--set` applies at solve time. Output:
`docs/handoffs/scn-ws4c/phase0_loadhi_census.json`.

| ISO | DC block MW 2026 → 2030, LOAD-HI | LOAD-HI-ORGANIC | growth HI / REF | ORGANIC degenerate? |
|---|---|---|---|---|
| ERCOT | 34,566.7 → 103,700.0 | 10,483.3 → 31,450.0 | 11.50 % / 8.50 % | **no** |
| CAISO | 510.0 → 1,530.0 | 510.0 → 1,530.0 | 4.20 % / 2.80 % | **YES** |
| PJM | 5,100.0 → 25,500.0 | 5,100.0 → 25,500.0 | 6.00 % / 3.60 % | **YES** |
| MISO | 1,190.0 → 22,950.0 | 1,020.0 → 17,425.0 | 4.50 % / 3.10 % | **no** |
| NYISO | 1,416.7 → 7,083.3 | 425.0 → 2,125.0 | 2.63 % / 1.22 % | **no** |
| NEISO | 0.0 → 0.0 | 0.0 → 0.0 | 2.20 % / 1.30 % | **YES** |

`electrification_path` resolves to `'off'` in all six ISOs at REF, confirming WS-4b §0 item 1.

**This reproduces WS-4b's pre-declared arithmetic to the decimal** — ERCOT's block 34.6 → 103.7 GW;
the MISO LOAD-HI − ORGANIC block gap 170.0 → 5,525.0 MW ("+0.2 → +5.5 GW"); the NYISO gap
991.7 → 4,958.3 MW ("+1.0 → +5.0 GW"). That agreement is the phase-0 gate for the case set
itself: WS-4b's arithmetic is HEAD's arithmetic, so the readings are testable as written.

**Three arms are killed here, at zero LP cost.** CAISO, PJM and NEISO have `LOAD-HI ==
LOAD-HI-ORGANIC` byte-for-byte in the T1 window, so an ORGANIC arm on them would be a
duplicate solve producing a guaranteed-zero delta. Not spent (WS-4b §3 and FINDING §5 routed
item 2, confirmed independently here).

---

## 3. G-DRIFT — the rule 29(b) code-level drift audit, and its verdict

Rule 29(b) makes the incumbent committed bundle the control and forbids a control solve unless
a **LIVE** hunk earns one. The candidate controls are the committed REF T1-F runs
(`results/ff-t1f-d50/{ercot,neiso}`, basis `a35c9f9bc0d1dc26c76e48566c61ec33dcc7e610`).

`git diff a35c9f9b HEAD -- src/market_sim scripts/run_full_horizon.py scripts/lib`:
**65 files, +5,989 / −610.** Classification of the decisive hunks:

| hunk | verdict | reason |
|---|---|---|
| `config/scenarios.py`: `ccs_retrofit_capex_co2_scaling: bool = True` | **LIVE** | a DEFAULT FLIP (capx D60 / owner ruling Q42, 2026-09-05) landed after the basis. Inert below `ccs_retrofit_available_year` (2028) — so inert for the T0, **live for 2028–2030 of both T1-F legs**, which is exactly the window the deployment response is read in. |
| `model/capacity_evolution/adequacy.py` (+298) | **LIVE** | the reserve-margin backstop — the mechanism WS-4b's reading (a) names for five of six ISOs. ISO-agnostic forecast path. |
| `model/capacity_evolution/retirements.py` (+785) | **LIVE** | the exogenous exit + economic screen path, entered by every forecast year. ISO-agnostic. |
| `model/capacity_evolution/new_entry.py` (+82), `ccs.py` (+185) | **LIVE** | entry ladder and the retrofit screen, both on the T1-F path. |
| `capacity_market_supply_clearing_by_iso` arming (capx D57) | INERT for this lane | PJM-only; neither T1-F leg is PJM. |
| `data/fuel/basis/miso.py`, `miso_*` gates, `nyiso_requirement_*`, `locality_capacity_curves` | INERT | another ISO's branch, or a `ScenarioConfig` flag that is default-off and absent from these legs' recipe. |

**Verdict: LIVE. The committed `ff-t1f-d50` REF is NOT a valid control at HEAD**, and form 4
(differencing against committed numbers) is void for the T1-F legs. Under 29(b)'s own
LIVE-hunk clause a control solve is earned, **and only for the years the leg needs** — so REF is
solved at 2026–2030 for ERCOT and NEISO, and at 2026 for all six T0s. The audit is recorded
here, before the arms are solved, so it cannot be written to fit the result.

*Independent empirical corroboration, free of charge:* the committed `ff-t1f-d50` NEISO 2026 row
(CO2 16.31 Mt, imports 28.54 TWh, lw price $52.13) is byte-identical to SCN-WS0's HEAD-basis
NEISO 2026 REF solve, so 2026 NEISO specifically shows no measured drift. That is one year of
one ISO and does not overturn the audit for 2028–2030, where the D60 default flip bites. **My
own T0 REF 2026 arms re-measure this for all six ISOs at my HEAD, and I will report any
disagreement against these committed rows as a drift finding.**

**Committed REF 2026 rows used only for SIZING the expectations in §4** (never as a control):

| ISO | gen TWh | CO2 Mt | fossil TWh | fossil-avg t/MWh | imports TWh | lw $/MWh | peak GW |
|---|---|---|---|---|---|---|---|
| ERCOT | 546.3 | 189.17 | 310.28 | 0.610 | 0.00 | 34.59 | 93.7 |
| CAISO | 237.3 | 30.51 | 78.92 | 0.387 | 42.07 | 55.32 | 49.8 |
| PJM | 873.0 | 349.09 | 526.50 | 0.663 | −0.95 | 40.12 | 161.0 |
| MISO | 685.9 | 352.99 | 471.16 | 0.749 | 0.00 | 39.26 | 128.5 |
| NYISO | 154.2 | 23.74 | 59.02 | 0.402 | 32.33 | 50.21 | 29.4 |
| NEISO | 117.1 | 16.31 | 42.47 | 0.384 | 28.54 | 52.13 | 24.9 |

---

## 4. What I expect, per ISO — sign, order of magnitude, footprint

**Energy is a growth-path effect; peak is a DC-shape effect.** Because the DC block is
*relocated* (energy-invariant) in every ISO at 2026, `LOAD-HI` and `LOAD-HI-ORGANIC` carry the
**same 2026 energy**; the DC axis moves only the shape. So the 2026 energy delta is
`(1 + g_high)² / (1 + g_mid)²` on the 2024 base:

| ISO | Δ energy 2026 | Δ peak 2026 (LOAD-HI) | all-fossil ceiling on ΔCO2 | my predicted ΔCO2 band |
|---|---|---|---|---|
| ERCOT | +30.6 TWh (+5.6 %) | **−9.0 GW (93.7 → 84.7)** | +18.7 Mt | **+13 to +26 Mt** (+7 to +14 %) |
| CAISO | +6.5 TWh (+2.7 %) | +0.6 GW | +2.5 Mt | **+1.0 to +2.6 Mt** |
| PJM | +41.0 TWh (+4.7 %) | +7.7 GW | +27.2 Mt | **+18 to +30 Mt** |
| MISO | +18.8 TWh (+2.7 %) | +3.5 GW | +14.1 Mt | **+9 to +17 Mt** |
| NYISO | +4.3 TWh (+2.8 %) | +0.2 GW | +1.7 Mt | **+0.7 to +1.8 Mt** |
| NEISO | +2.1 TWh (+1.8 %) | +0.4 GW | +0.8 Mt | **+0.3 to +0.9 Mt** |

**The three predictions in that table that are actually falsifiable, and why I make them:**

1. **ERCOT's implied marginal rate should EXCEED its fossil-fleet average (0.610 t/MWh).** The
   relocated block is 34.6 GW *flat* and 52 % of energy — it is a baseload addition, and
   ERCOT's cheap baseload with headroom is **coal** (95.5 TWh at REF, ~0.95–1.0 t/MWh). So I
   predict `ΔCO2 / Δfossil-MWh` lands in **[1.0, 1.6] × 0.610**, i.e. above the average — which
   is why my band's top (+26 Mt) sits *above* the all-fossil ceiling computed at the average
   rate. The charter's own wording ("CO2 rises ≈ fossil-average rate × added fossil-served
   MWh") is therefore a statement I expect to hold in order of magnitude and to **miss on the
   high side in ERCOT specifically**. If instead the ratio lands below 0.610, the flat block is
   being served by gas rather than coal and my mechanism story is wrong.
2. **ERCOT `unserved_mwh` > 0 at 2026 under LOAD-HI, despite the peak FALLING 9 GW.** This is
   the sharpest thing I can pre-declare. WS-4b calls I3's sign "ambiguous"; I commit to a
   direction. A 34.6 GW flat block raises the *minimum* load far more than it raises the peak,
   so adequacy in the relocate regime becomes an **energy/floor** problem rather than a peak
   problem, and ERCOT has no backstop to build into it. If slack is 0.0 the fleet's floor
   capability is larger than I think and the prediction fails outright.
3. **ERCOT `lw_price` RISES while `max_hourly_price` and `hours_ge_500` FALL.** Load-weighted
   price is dominated by the bulk of hours, which move up the stack; the top-of-stack scarcity
   hours are removed with the 9 GW of peak. A *falling* lw_price would mean the flattening's
   scarcity-rent loss outweighs the bulk-hour cost rise — reportable, and a miss of mine.

For the other five ISOs the peak rises, so the charter's plain reading (CO2 up, price up)
should hold and I predict `lw_price` up in all five, monotone with the energy delta.

**Footprint — where the delta may legitimately land.** Fossil generation classes, imports,
prices, and (curve-ON only) backstop `gas_ct` builds. Zero-CO2 classes (nuclear, hydro, wind,
solar, biomass) may move in ENERGY but must contribute no positive CO2; `by_fuel["import"]`
must be exactly 0.0 in every arm.

---

## 5. The STOP gate — structural, kill-only, never gated on a residual

Checked on every arm. It **may kill an arm; it may never promote one**; it contributes to no
determination; **no check reads a residual or a target metric's accuracy.**

| # | check | kills the arm when |
|---|---|---|
| **S1** | *Identity.* `Σ emissions_by_fuel_mt` = `Σ emissions_by_zone_mt` = `emissions_mt` to 6 dp | the partition does not close — the emissions grain is broken, so no delta from it means anything |
| **S2** | *Direction and magnitude.* For every ISO with Δenergy > 0: ΔCO2 > 0, Δfossil-MWh > 0, and the implied rate `ΔCO2 / Δfossil-MWh` lies within **[0.5, 2.0] × that arm's own fossil-average rate** | the dispatch response has the wrong sign, or an order of magnitude the pre-solve arithmetic cannot produce |
| **S3** | *Footprint confinement.* the CO2 delta is confined to fossil classes and imports; no zero-CO2 class carries a positive CO2 delta; `by_fuel["import"] == 0.0` in both arms | the added load reaches rows it cannot physically reach — the mechanism is not doing what it claims |
| **S4** | *Accounting completeness.* `unserved_mwh` and `import_co2_mt_reported` present and finite on every arm; `backstop_built_mw == 0.0` for **ERCOT** | ERCOT non-zero ⇒ the backstop is armed for an energy-only ISO, a configuration defect (WS-4b (d)) |
| **S5** | *No non-target flip.* no load-bearing forecast invariant flips PASS → FAIL **for a reason unrelated to load** | a defect unrelated to the case has been introduced |

**S5 explicitly does NOT fire on I3 / I7 / I12.** Those are the *target* of this lane: WS-4b
pre-declares they widen, and a widening is the measurement, not a failure. They are disclosed
per case and left where they live (rule 1 `[R-STRUCT]` — I move no knob and propose no fix).

---

## 6. The six WS-4b readings I am about to test, restated so the scoring cannot drift

Scored against the **bare `ff-verdicts.json` keys**, per WS-4b §4. Each is HIT / MISS / SPLIT
with the deciding number.

| ISO | (a) mechanism | (b) invariant widening | (d) table line | (e) import line |
|---|---|---|---|---|
| **ERCOT** | scarcity-priced entry **or nothing**; backstop OFF by design; residual → VOLL slack | {I12, I3}; **non-monotone** — 2026–29 peak below REF so I12 *improves* (artefact), I3 ambiguous; 2030 tail regime | `unserved_mwh` + `backstop_built` = **0.0** + CO2/served MWh + `hours_ge_500` | **exactly 0.0**, both cases, every year — no import node |
| **CAISO** | backstop `gas_ct` (52.6 % share) + ladder | {I12, I7} widen; share > 52.6 %; I3 may re-appear 2029–30 | `backstop_built_mw`/`_mwh` + `unserved_mwh` | **up**, same sign as CO2; ≤ ~7–11 Mt ceiling |
| **PJM** | cap-bound backstop ladder is the only responding channel (43.9 %) | {I12, I7} → I7 misses in **tens of GW**; **I3 expected to APPEAR 2029–30** | `backstop_built` + `unserved_mwh` | **up, small**; bounded by the 10,500 MW SIL |
| **MISO** | backstop (23.0 % CAVEAT) + ladder + D42 exits | {I12, I7} widen; **share crosses 30 % → FAIL** | `backstop_built` + `unserved_mwh` | **0.0 both cases**; a non-zero is a rung activating |
| **NYISO** | backstop armed, never fired | **{} → I7/I12 read BETTER** (artefact); possible I12 exit on the **high** side | `backstop_built` = **0.0**, `unserved_mwh` = **0.0** — printed because non-zero is the finding | **up**, sign + |
| **NEISO** | backstop (1.2 %) + floor retention | {} but thin I7 → backstop **fires**; share 1.2 % → the 10–30 % CAVEAT band | `backstop_built` + `unserved` + the import line **per tranche** | **up early, then saturates**; ≤ ~5 TWh / ≤ ~2.1 Mt |

**A reading that misses is this lane's most valuable output** — it means the pre-declaration was
wrong about the *mechanism*, which is a structural finding. It is reported at full magnitude and
is never a reason to re-read the case or move a parameter.

---

## 7. The leakage line is a deliverable, not a caveat

SCN-WS0 measured that a $25/t carbon arm displaced ~two thirds of NEISO's headline CO2 reduction
across one NYISO seam rung (`NYISO_CT_peak`, +4.32 TWh, +1.85 Mt), invisible to `emissions_mt`.
A LOAD-HI case moves imports in the **opposite** direction, so the import line **compounds** the
in-ISO increase rather than eroding it — the headline *understates* the total.

I report `import_co2_mt_reported` beside `emissions_mt` for **every** ISO as a number, name the
tranche that moves, score it against WS-4b's (e) line, and **write 0.0 with the reason** where
the ISO has no import node (ERCOT) or has zero REF imports (MISO) — that is also a result, not
an omission. NEISO additionally gets the per-tranche table, because its HQ seam is 1–5 TWh from
its 3,850 MW simultaneous limit and the pre-declaration is that it **saturates**.

---

## 8. Budget and scheduling (rule 12 `[R-PARALLEL]`)

Box: 15 GB RAM, 4 cores, ~20 GB free disk. `data/clean` was absent on this container and is
being rebuilt (plan §2.4 hard prerequisite, ~55 min, one-time) — budgeted, and it precedes
every solve.

- **Years sequential within every invocation, always.** The 2026–2030 legs are one invocation each.
- **≤ 2 concurrent invocations, and 1 whenever a per-plant multi-zone ISO (PJM / MISO / CAISO)
  is running** — those are ~8.6 GB each and two cannot co-run on this box. ERCOT (~3.6 GB) and
  NEISO (~3.9 GB) may pair; NYISO may pair with one of them.
- Estimated LP wall: T0 ≈ 80 min, T1-F ≈ 25–40 min (the ERCOT 2030 tail-regime year is the
  unknown — 1,800 TWh against a 12 GW/yr queue cap, so a large slack column).
- **Solves run in-session. No CI runner** (private repo, billed minutes).

---

## 9. Deviations, and what would make me report a miss

**No default moves. No knob moves. No file outside this lane's regions.** I consume
`configs/scenario_campaign_matrix.yaml` and `scripts/report_scenario_deltas.py` (SCN-WS4b's
landed work) without editing them; if a case needs changing I STOP and route to SCN-DESK.

**Any of the following is reported as a miss of THIS document, at full magnitude, with the
reasoning that produced the estimate** — SCN-WS0's precommit predicted "low single-digit
percent" and measured 16.6 %, and recorded the miss; a precommit whose misses go unreported is
not a precommit:

1. a ΔCO2 outside the §4 band for any ISO;
2. ERCOT's implied marginal rate landing **below** its fossil-fleet average;
3. ERCOT `unserved_mwh` = 0.0 at 2026 under LOAD-HI;
4. ERCOT `lw_price` **falling**, or `max_hourly_price` / `hours_ge_500` **rising**;
5. any ISO's import line moving against the sign I predict here.

Misses 2–4 are mine alone and are independent of WS-4b's readings; scoring WS-4b is §6 and is
kept separate, so my own error can never be laundered into a verdict on their document.
