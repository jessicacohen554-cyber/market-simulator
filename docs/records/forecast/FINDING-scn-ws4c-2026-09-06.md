# FINDING — SCN-WS4c: the LOAD-HI probes, scored against SCN-WS4b's pre-declaration

**Lane** SCN-WS4c · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws4c-load-hi-probes-o85iyi` · **Data profile** `all` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-scn-ws4c-2026-09-06.md` (pushed before the first solve) ·
**Charter** plan §7 "WS-4" item 4 / readiness plan §3 WS-4 item 4, §3.5, §4 ·
**Campaign** `scn-ws4-probe` — 19 registered arms (15 T0 + 4 T1-F), disjoint from `scn-ws1-probe`

---

## 0. Bottom line

1. **All 19 arms solve clean** (15 T0 at 2026, 4 T1-F at 2026–2030). The STOP gate PASSES on
   every arm; it killed nothing, and it promoted nothing.
2. **Rule 29 phase 0 killed three arms at zero LP cost** and independently reproduced SCN-WS4b's
   pre-declared arithmetic to the decimal, so their readings were testable exactly as written.
3. **The lane's substantive result is about the fossil-average heuristic, and it has a sign.**
   The implied marginal CO2 rate sits **below** the fossil-fleet average in every ISO with
   inframarginal coal (ERCOT 0.73×, PJM 0.77×, MISO 0.65×) and **above** it in every
   gas-dominated ISO (CAISO 1.05×, NYISO 1.05×, NEISO 1.17×). The charter's own expectation —
   "CO2 rises ≈ fossil-average rate × added fossil-served MWh" — is therefore biased **high by
   23–35 % where coal is in the stack and low by 5–17 % where it is not**. The error is not
   noise; it is predictable in advance from one fact about the fleet.
4. **SCN-WS4b's readings score 20 HIT / 3 SPLIT / 3 MISS across the six ISOs** (§3). The three
   misses are the valuable output: CAISO's leakage rung, MISO's I3 timing, and NEISO's backstop
   — the last of which is not a WS-4b error at all but a HEAD change underneath their pin (§4).
5. **G-DRIFT was right, and it mattered — now measured, not argued** (§4). ERCOT's REF T1-F
   reproduces the committed `ff-t1f-d50` bundle *exactly*; NEISO's does **not**, differing by up
   to 2.821 Mt (−18.8 % in 2030) with d50's 50 MW backstop firing gone. Differencing against the
   committed bundle, which is rule 29(b)'s default, would have measured NEISO's entire
   deployment response against a stale reference.
6. **Three of my own PRECOMMIT predictions missed** and are reported at full magnitude (§5),
   including the one that carried the most reasoning behind it.

---

## 1. What was solved

| leg | ISO | cases | years | wall / peak RSS |
|---|---|---|---|---|
| T0 | ERCOT | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 2.0–2.1 min / 3.34–3.52 GB |
| T0 | CAISO | REF · LOAD-HI | 2026 | 7.1–7.7 min / 4.60–4.84 GB |
| T0 | PJM | REF · LOAD-HI | 2026 | 5.9–6.0 min / 8.74 GB |
| T0 | MISO | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 6.3–6.7 min / 9.69–9.76 GB |
| T0 | NYISO | REF · LOAD-HI · LOAD-HI-ORGANIC | 2026 | 2.3–2.6 min / 2.83–3.34 GB |
| T0 | NEISO | REF · LOAD-HI | 2026 | 1.6–2.0 min / 3.18 GB |
| T1-F | ERCOT | REF · LOAD-HI | 2026–2030 | 9.2–10.4 min / 3.91–3.99 GB |
| T1-F | NEISO | REF · LOAD-HI | 2026–2030 | 6.5–6.8 min / 3.24–3.29 GB |

**§2.4 budget ledger.** Every ISO came in at or under its anchor except MISO, which was
*faster* (6.3–6.7 min/yr against a 10–13 min anchor) but peaked at **9.7 GB on a 15 GB box** —
which is rule 12's one-at-a-time cap for per-plant multi-zone ISOs being *necessary*, not
cautious. `data/clean` was absent on this container and cost **28 min** to rebuild (55/55
datatypes, zero failures) against the plan's ~55 min anchor.

**Three arms were never solved.** CAISO, PJM and NEISO carry `LOAD-HI == LOAD-HI-ORGANIC`
byte-for-byte in the T1 window, established at phase 0 from the constants; solving them would
have produced a guaranteed-zero delta.

---

## 2. Rule 29 phase 0 — the zero-LP work, and what it bought

Two probes, both run and pushed before any arm was scheduled.

**Part 1, the levers.** Resolved through `apply_iso_scenario_defaults` plus the runner's own
`apply_set_overrides`, so the census cannot drift from what `--set` applies at solve time. It
reproduced WS-4b's block sizes to the decimal — ERCOT 34,566.7 → 103,700.0 MW ("34.6 → 103.7 GW");
the MISO LOAD-HI − ORGANIC gap 170.0 → 5,525.0 MW ("+0.2 → +5.5 GW"); NYISO 991.7 → 4,958.3 MW
("+1.0 → +5.0 GW") — and confirmed `electrification_path` resolves to `off` in all six ISOs.

**Part 2, the realized 8760.** Walked the runner's own demand seam (`load_demand` →
`_scale_demand` → `add_load_layers`) and confirmed WS-4b's central construction claim directly:

| ERCOT 2026 | energy | peak | **minimum** | load factor |
|---|---|---|---|---|
| REF | 544.6 TWh | 93.67 GW | 45.97 GW | 0.664 |
| LOAD-HI | 575.1 | **84.60 (−9.07)** | **55.91 (+9.94)** | 0.776 |
| LOAD-HI-ORGANIC | 575.1 | 99.28 (+5.61) | 48.36 | 0.661 |

The peak falls 9.07 GW while the floor rises 9.94 GW. Across the T1 window ERCOT's load factor
runs 0.776 → 0.970 (2029) before the 2030 tail regime (1,797 TWh / 267.0 GW), reproducing WS-4b
§2.1 to under 0.5 % throughout. Every LOAD-HI / ORGANIC energy pair is identical, confirming the
DC axis moves **shape only** at fixed energy.

*Probe caveat, stated because the numbers are in the record:* this probe omits
`include_interchange=not import_generators`, so its absolute levels for PJM / NYISO / NEISO sit
below the solved runs' (ERCOT, MISO and CAISO match exactly). Both arms use the same convention,
so every **delta** above is unaffected.

---

## 3. THE SCORING — SCN-WS4b's six pre-declared readings

Verdicts are HIT / SPLIT / MISS with the deciding number. **I did not revise WS-4b's document
and did not re-read any case after seeing a number.**

### 3.1 The one-line table

| ISO | (a) mechanism | (b) invariant widening | (d) table line | (e) import line |
|---|---|---|---|---|
| **ERCOT** | **HIT** | **HIT** | **HIT** | **HIT** |
| **CAISO** | untestable at T0 | **HIT** | **HIT** | **SPLIT** |
| **PJM** | untestable at T0 | **HIT** | **HIT** | **HIT** |
| **MISO** | untestable at T0 | **SPLIT** | **HIT** | **HIT** |
| **NYISO** | **HIT** | **SPLIT** | **HIT** | **HIT** |
| **NEISO** | **MISS** | **MISS** | **HIT** | **HIT** |

"Untestable at T0": (a) names the reserve-margin backstop, whose REF first firing is 2027 or
later in every ISO, so a 2026-only arm cannot exercise it. That is a **scope limit of this
lane**, not a verdict on WS-4b — recorded as such rather than scored.

### 3.2 ERCOT — 4 HIT

- **(a) HIT.** `backstop_built_mw` = 0.0 in every year of every arm, T0 and T1-F, as an
  energy-only ISO requires; the 2030 residual leaves through the VOLL slack column exactly as
  the reading says it must.
- **(b) HIT, and the ambiguity they flagged is resolved as genuinely non-monotone.** REF fails
  I12 in all four years 2027–2030 (8.9 / 3.0 / −2.5 / −7.1 %, reproducing their cited bare-key
  numbers exactly); **LOAD-HI is IN BAND 2027–2029** and fails only in 2030 (−55.8 %). That is
  the relocate-regime artefact they warned must not be read as adequacy, measured. I3's sign
  really does change direction: LOAD-HI is *better* than REF in 2027 (0.04 % vs 0.08 %) and
  *worse* from 2028 (1.35 % vs 0.14 %). The 2030 tail arrives as predicted — **slack in all
  8,760 hours, 53.40 % of load**, `hours_ge_500` exactly **8,760** against their "≈ 8,760",
  with REF's 4,039 h matching their cited figure exactly.
- **(d) HIT.** All four required columns present; backstop 0.0 (no configuration defect);
  CO2 per **served** MWh 0.3463 → 0.3516 t/MWh (ORGANIC 0.3537).
- **(e) HIT.** `import_co2_mt_reported` = **0.0000 exactly**, both cases, every year. Not a
  leakage-free result — a boundary the model cannot see.

### 3.3 CAISO — (e) is a SPLIT, and it is a real finding

- **(b) HIT.** REF I7 miss **2,276 MW** — their cited figure, exactly — widening to **3,861 MW**
  under LOAD-HI (+1,585 MW), inside their "≤ ~5.5 GW" bound; I12 10.4 % → 7.5 %, still out of band.
- **(e) SPLIT.** Direction right, mechanism wrong. Imports **do** rise (+0.271 TWh) — but
  `import_co2_mt_reported` is **0.0000 in both arms** and does not move, because the entire
  increment lands on `WECC_import_DSW_solar_PV` at **EF 0.000**, not on the DSW_CCGT (0.37) /
  DSW_CT (0.55) rungs the reading named. CAISO's modeled import stack has zero-EF headroom, so
  at 2026 high load draws *clean* imports and reports no leakage at all — the mirror image of
  NEISO and NYISO, where the zero-EF rungs sit at firm depth and increments land on 0.428
  fossil rungs. Their ≤ ~7–11 Mt ceiling is not wrong, it is simply never approached.

### 3.4 PJM — (e) HIT, precisely, including the exports clause

- **(b) HIT so far, and earlier than the board.** At `mid` PJM is clean at 2026; under LOAD-HI it
  flips **ALL PASS → I7 FAIL (3,341 MW) + I12 WARN (−10.3 %)** in that year. Their "tens of GW"
  and "I3 appears 2029–30" are 2027–2030 claims this lane's T0 cannot reach.
- **(e) HIT.** `import_co2_mt_reported` 0.4168 → 0.7559 (**+0.339 Mt**), up and small as
  predicted; the movers are `import_scarcity_1` (+0.592 TWh) and `import_scarcity_2` (+0.200);
  and **exports fall** (`export_firm` −1.920 → −1.549 TWh) contributing exactly **0.0 Mt** —
  clamped out of the line with no offset, exactly as the reading says.

### 3.5 MISO — (b) SPLIT on timing

- **(b) SPLIT.** I7/I12 HIT: REF miss **6,175 MW** — their cited figure, exactly — widening to
  **9,622 MW** (+3,447 MW); I12 −4.1 % → −6.6 %. **I3 MISSES on timing:** they said it "may
  re-appear 2029–2030"; it re-appears at **2026**, crossing its threshold on the case (REF
  48,093.8 MWh = 0.0070 % of load, PASS → LOAD-HI 77,034.5 MWh = 0.0109 %, FAIL).
- **(e) HIT.** `import_co2_mt_reported` = 0.0000 in both arms, and MISO carries **no import
  tranches at all** — the firm-import injections are capacity-side, as the reading states.

### 3.6 NYISO — (b) SPLIT because 2026 is too early for the artefact

- **(a) HIT.** Backstop armed and never fired: 0.0 MW in all three arms.
- **(b) SPLIT.** The substance HITs — all 14 invariants PASS in all three arms, no backstop, no
  slack. The "I7/I12 read *better*" half is not visible at 2026: the peak is essentially flat
  (+0.2 GW, not falling — the block reaches 35 % of energy only by 2030), so the margin edges
  0.184 → 0.178, marginally *worse*. No high-side I12 exit either. Their claim is a 2029–2030
  statement; this lane's T0 cannot reach it.
- **(d) HIT exactly.** `backstop_built` 0.0 and `unserved_mwh` 0.0, printed because a non-zero
  would have been the finding.
- **(e) HIT, mechanism confirmed precisely.** `NYISO_external_HQ_hydro` is **flat at 7.884 TWh**
  (EF 0, at firm depth) while the increment lands on the 0.428 rungs — `ISONE_tie` +0.259 TWh
  and `eastern_mid` +0.106 — for **+0.1562 Mt**. That is their stated reasoning, reproduced.

### 3.7 NEISO — (a)/(b) MISS on the backstop; (e) the lane's most precise HIT

- **(a) and (b) MISS.** They predicted the thin I7 positions go negative around 2027–2028 and the
  backstop **fires** for the difference, carrying the share from 1.2 % into the 10–30 % CAVEAT
  band. Measured across the full T1-F window: `backstop_built_mw` = **0.0 MW in every year of
  both arms**, and **I7 holds anyway, on its own** — all 14 invariants PASS in all five years of
  both arms, with the reserve margin falling 0.135 → 0.091 but staying positive. §4 shows this
  is not a WS-4b reasoning error: their premise was d50's 50 MW 2029 firing, which HEAD no
  longer produces. The "no I3" half is a HIT.
- **(e) HIT, and it is the most specific prediction in their document.** They said the import
  line rises **early**, on `NYISO_CT_peak` / `NB_north` first, then **saturates** by 2029–2030,
  after which in-ISO gas carries the increment and the in-ISO CO2 delta grows faster:

  | NEISO | 2026 | 2027 | 2028 | 2029 | 2030 |
  |---|---|---|---|---|---|
  | Δ import TWh (HI−REF) | 0.229 | 0.504 | **0.539** | 0.350 | 0.243 |
  | Δ `import_co2` Mt | 0.0788 | 0.1112 | **0.2136** | 0.1428 | 0.1039 |
  | Δ in-ISO CO2 Mt | 0.812 | 1.176 | 1.568 | 1.987 | **2.554** |
  | leakage as % of Δ CO2 | 9.7 % | 9.5 % | 13.6 % | 7.2 % | **4.1 %** |
  | total imports, HI (TWh) | 28.8 | 28.1 | 30.1 | 31.4 | **33.2** (limit 33.7) |

  The import delta peaks at 2028 and falls; total imports fill to 33.2 of the 33.7 TWh/yr
  simultaneous limit; the in-ISO delta accelerates 3.1×; and the movers are `NYISO_CT_peak`
  (3.245 → 7.368 TWh) then `NB_north` activating late (0.004 → 0.080) — both names, in that
  order. Every clause lands.

---

## 4. G-DRIFT: right, and consequential — measured rather than argued

The PRECOMMIT classified the drift from the `ff-t1f-d50` basis (`a35c9f9b`) as **LIVE** on code
grounds — the `ccs_retrofit_capex_co2_scaling` default flip (capx D60 / Q42), inert below 2028
and live for 2028–2030, plus `adequacy.py` (+298), `retirements.py` (+785) and `new_entry.py`
(+82) on the ISO-agnostic forecast path — and therefore **solved** the REF arms instead of
differencing against the committed bundle, per rule 29(b)'s LIVE-hunk clause. Comparing:

| REF T1-F vs committed d50 | 2027 | 2028 | 2029 | 2030 | backstop 2029 |
|---|---|---|---|---|---|
| **ERCOT** | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 = 0.0 |
| **NEISO** | +0.231 | +0.297 | +0.184 | **−2.821** | **50.2 → 0.0** |

**ERCOT reproduces d50 exactly** — CO2 to three decimals, every load-weighted price, every
backstop row — so for ERCOT the drift is inert *in effect*, and form 4 would have been valid.
**NEISO does not.** It differs by up to 2.821 Mt (−18.8 % in 2030), its price differs in every
year from 2027, and d50's 50.2 MW backstop firing in 2029 is gone. Had the lane taken rule
29(b)'s default, NEISO's whole deployment response would have been measured against a stale
reference — and the NEISO scoring in §3.7 would have been scored against a mechanism HEAD no
longer runs.

Two things follow, and both are honest rather than self-congratulatory. The audit cost seconds
and was **correct**; and it was correct for a reason the code diff could establish but its
*magnitude* could not — the ERCOT half of the same call bought nothing but ~10 min of LP. A
code-level audit tells you whether to spend, not how much the spend was worth.

**Routed:** the board's NEISO bare key `neiso-2026-2030-d50-ccscapex` is **stale as a description
of HEAD** — a −2.8 Mt 2030 decarbonization improvement and the loss of the 2029 backstop firing.
This is a records item for the capx director (`program-status.json` / `ff-verdicts.json` are
forbidden to every SCN lane); root-causing it across the adequacy / retirements / entry hunks is
their queue, not this lane's.

---

## 5. My own PRECOMMIT: three misses, reported at full magnitude

A precommit whose misses go unreported is not a precommit (SCN-WS0's precedent).

**MISS 1 — ERCOT's implied marginal rate, the prediction with the most reasoning behind it.**
I predicted the ratio would land in **[1.0, 1.6] × 0.610**, arguing that a 34.6 GW *flat* block
is a baseload addition and ERCOT's cheap baseload with headroom is coal. Measured: **0.447
t/MWh, 0.73×** the fleet average. The reasoning under-weighted that **ERCOT's coal is already
near-baseload in REF and has essentially no headroom** — it moves 95.545 → 95.578 TWh (+0.033),
so 73 % of the CO2 increase is gas_cc, 18 % gas_ct, 9 % gas_st and 0.2 % coal. "Flat block →
coal" was right about the *shape* of the demand and wrong about the *state of the stack*. The
ratio is inside STOP-gate S2's [0.5, 2.0] band, so the gate passed; this is a finding, not a kill.

**MISS 2 — ERCOT unserved energy at 2026, and the miss inverts the mechanism.** I predicted
`unserved_mwh` > 0 under LOAD-HI despite the falling peak, reasoning that the relocated block
raises the floor 9.94 GW and ERCOT has no backstop, so adequacy becomes a floor problem.
Measured: LOAD-HI unserved is **exactly 0.0** with every invariant passing, while
**LOAD-HI-ORGANIC — the peaky arm, at identical energy — sheds 143,390.9 MWh over 26 hours at
VOLL** and fails I3. Adequacy in ERCOT 2026 is a **peak** problem, not a floor problem: a
55.9 GW floor is still far under the fleet's ~93 GW REF capability, so raising the floor is
free; raising the peak to 99.3 GW is not. This resolves at 2026 the sign WS-4b called ambiguous
— though §3.2 shows the ambiguity is real across the window, since LOAD-HI's I3 overtakes REF's
from 2028.

**MISS 3 — MISO's CO2 band, at the boundary.** Predicted +9 to +17 Mt; measured **+8.992**, low
by 0.008 Mt (0.09 %). Recorded as a miss rather than rounded into a hit.

**What held.** CO2 magnitudes HIT in five of six ISOs; "price rises" HIT in all six; the
footprint stayed confined to fossil classes and imports in every arm; `by_fuel["import"]` was
0.0 everywhere; and ERCOT's `backstop_built` was 0.0 as a configuration check.

---

## 6. The result that is not in anyone's pre-declaration

**The fossil-average heuristic has a signed error, and the sign is knowable in advance.**

| ISO | Δ CO2 Mt | Δ fossil TWh | implied rate | fleet average | ratio | coal inframarginal? |
|---|---|---|---|---|---|---|
| ERCOT | +13.687 | +30.63 | 0.447 | 0.610 | **0.73** | yes (95.5 TWh, flat) |
| PJM | +20.084 | +39.54 | 0.508 | 0.663 | **0.77** | yes (227 TWh) |
| MISO | +8.992 | +18.58 | 0.484 | 0.749 | **0.65** | yes (292 TWh) |
| CAISO | +2.544 | +6.28 | 0.405 | 0.387 | **1.05** | no (0.36 TWh) |
| NYISO | +1.637 | +3.88 | 0.422 | 0.402 | **1.05** | no |
| NEISO | +0.812 | +1.81 | 0.450 | 0.384 | **1.17** | no |

A clean 3–3 split. Coal is inframarginal, so it does not answer added load and its high rate is
diluted **out** of the marginal response; in a gas-dominated stack the marginal unit is a CT
dirtier than the CC-weighted average. So "fossil-average rate × added fossil-served MWh"
overstates by 23–35 % where coal is in the stack and understates by 5–17 % where it is not.
For attributing emissions to a new large load this is the difference between a defensible
number and a systematically wrong one, and it costs nothing to correct — the marginal rate is
already computable from the two arms the campaign solves anyway.

**And the largest measured effect of the data-centre axis is not emissions at all — it is
shape.** ERCOT LOAD-HI and LOAD-HI-ORGANIC carry near-identical CO2 (202.85 vs 203.94 Mt) at
identical energy, and load-weighted prices of **$36.23 vs $80.34** with reserve margins of
0.271 vs 0.083 and unserved energy of 0.0 vs 143.4 GWh. Whether the same data-centre energy
arrives flat or peaky is worth ~$44/MWh and the entire adequacy verdict, while being worth
about 1 Mt of CO2. Any campaign that varies DC *volume* without varying DC *shape* is varying
the less important axis.

---

## 7. The honest-unfit line, per ISO

**Never quote a HOLD ISO's mix as a result.** Every number here is a **delta between two arms
that share that ISO's live FC-1 defects**, and the defects do not cancel out of a level:

- **CAISO** (I7 2,276 MW, I12 10.4 % at REF) and **PJM** (I7/I12 from 2027 at `mid`, and at 2026
  under LOAD-HI) are HOLD. Their deltas are usable; their levels are not.
- **MISO** carries I7 6,175 MW and I12 −4.1 % at REF *and now I3 on the case*. Its ΔCO2 is
  measured under binding slack in both arms, so it is understated by the shed energy in each.
- **ERCOT** 2030 under LOAD-HI is **not an emissions response** and is not quoted as one: 53.40 %
  of load is shed in all 8,760 hours. The CO2 figure there is the fossil fleet at full output
  beside ~960 TWh of unserved energy.
- **NYISO** and **NEISO** are clean (14/14 PASS in every arm), and are the two ISOs whose levels
  can be read — subject to §4's finding that NEISO's REF has itself moved since the board's key.
- **Every ISO**: `emissions_mt` is read with `unserved_mwh` and `import_co2_mt_reported` beside
  it, never as a total. The six-ISO leakage table is §3 and §6; where it is 0.0 the reason is
  stated (ERCOT no import node; MISO no import tranches; CAISO a zero-EF marginal rung).

---

## 8. Routed to SCN-DESK (not executed — outside this lane's regions)

1. **`neiso-2026-2030-d50-ccscapex` is stale as a description of HEAD** (§4): −2.821 Mt in 2030
   and the 2029 backstop firing gone. Records item for the capx director; `program-status.json`
   and `ff-verdicts.json` are forbidden to every SCN lane.
2. **The charter names a `demand_growth_path` matrix cell that has no row.** The base matrix
   carries `demand_growth_vintage` (the hindcast as-of vintage, a different mechanism) and no row
   for the growth path itself, though the growth path is what drives the entire LOAD-HI energy
   delta. Rule 28(b) leaves a mechanism this lane tested with nowhere to record it. Minted here
   as a base row plus one cell line per shard (rule 28(c)'s deliberately non-parallel edit) —
   flagged because minting a row for a *pre-existing* field is a structural act the desk may
   prefer to own.
3. **(a) is untestable in a 2026 T0 for the four curve-ON ISOs** whose REF backstop first fires
   in 2027 or later. If the desk wants WS-4b's mechanism half adjudicated for CAISO / PJM / MISO,
   it needs T1-F legs for them — three more 5-year invocations, ~30 / ~30 / ~33 min.
4. **The DC axis's shape half is under-instrumented relative to its importance** (§6). The
   campaign varies DC volume; the measured price and adequacy effects come almost entirely from
   shape. A `datacenter_load_factor` axis would separate them; that is a D-2 levels question.

---

## 9. Duties and byte-identity

- **No default moved, no knob moved, no `ScenarioConfig` field added, no LP row changed.** Every
  arm is the shipped posture plus one or two `--set` overrides from the committed campaign YAML.
- **No file outside this lane's regions was written.** `configs/scenario_campaign_matrix.yaml`
  and `scripts/report_scenario_deltas.py` (SCN-WS4b's landed work) were **consumed, not edited**;
  `config/constants.py`, `data/datacenter.py`, `policy/*`, `model/lp/*`, `config/scenarios.py`,
  `scripts/register_forecast_run.py` and `program-status.json` were read only. `.gitignore` took
  one appended campaign block, the same shape SCN-WS0 and SCN-WS1b each added for their own.
- **Backcast byte-identity:** untouched. This lane is forecast-mode only and moved no default,
  so every backcast keeper key is unchanged.
- **Rule 27:** no existing source file ≥300 lines was rewritten. The only file this lane authored
  above that length is its own PRECOMMIT/FINDING pair.
- **Rule 29(c):** no screen or control bundle was produced — the 19 arms are registered
  forecast-namespace runs, kept and registered normally.
- **Rule 15 / §7.5:** all 19 arms registered through `scripts/register_forecast_run.py` into the
  forecast namespace under campaign `scn-ws4-probe`; the backcast registry was never touched.

---

## 10. Stage A

**This landing removes this lane's blocker on Stage A.** The charter framed what remains as
"card D-3, plus SCN-WS1b and SCN-WS2b landing"; **that is stale as of SCN-DESK r#5 (2026-09-06)
and is corrected here rather than repeated.** D-3 was ruled **S1 = YES** — the voluntary
clean-demand axis is admissible — so it *schedules* Stage A rather than blocking it, and D-2 was
ruled **S3**, making the §3.5 table the committed default (no number moved, so no re-solve is
owed, and this lane's `LOAD-HI` = growth high + DC high is now an owner-committed level rather
than an illustrative one).

**Stage A's critical path at this commit is: SCN-WS1b + SCN-WS2b landing, and SCN-WS3b → SCN-WS3c
landing.** With WS-4c landed, the Load-HI column of the readiness scorecard is closed on every
criterion. Still open, and named because they bite on how this lane's numbers may be quoted:
**D-3c** (the voluntary eligible set), **D-6** (attribute netting), and **D-5** (the Stage-B
grant, held until Stage A's cost table exists).

**One D-2-adjacent question this lane makes concrete, for the record rather than as a request.**
S3 committed `LOAD-HI` = growth high + DC high, and at that anchor ERCOT's energy goes 800 →
1,800 TWh in a single year (2030), which is why 53.40 % of its load is shed in all 8,760 hours.
That is the committed level behaving exactly as its arithmetic says it will, not a defect — but
§6's result is that the DC block's **shape** drives the price and adequacy answer far harder than
its volume does, and the campaign currently has no shape axis. Whether one is wanted is an owner
question, and it is a cheaper one than re-levelling the volume.
