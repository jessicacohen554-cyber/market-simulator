# FINDING — SCN-WS5A-LOAD / PJM: WS-4b's sharpest call lands, and my CCS claim dies here

**Lane** SCN-WS5A-LOAD (PJM) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Frozen pin** `1cc45bb2` ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Legs** REF · LOAD-HI (ORGANIC not spent — PJM ships `high := mid` at every DC anchor,
phase 0) · **Scored against** SCN-WS4b §5.3 and SCN-WS4c §3.4.

---

## 0. Bottom line

1. **WS-4b's most specific PJM call is substantially right.** They said the rate-limited
   backstop is the only responding channel, that I7/I12 widen, and — the hard part — that
   **I3, absent at `mid`, appears under LOAD-HI**. It does: REF fails `{I7, I12}` with no I3;
   LOAD-HI fails `{I3, I7, I12}`. Their *timing* is two years late (they said 2029–30; it
   arrives **2027**), so the clause scores **SPLIT**, but the mechanism call is theirs.
2. **PJM FALSIFIES my own CCS mechanism claim, and I report it as a kill, not a caveat**
   (§4). I predicted `gas_cc_ccs` only where a state carbon program exists. PJM has none and
   carries **909.8 MW (REF) / 1,512.8 MW (LOAD-HI)** from 2029. §45Q is a bid offset
   independent of carbon price, so the screen clears without a program.
3. **PJM's CCS units are the worst-rated in the campaign: 0.6063 t/MWh**, ~**15×** what
   `ccs_capture_rate = 0.90` implies and *above* even the unabated `gas_ct` (0.5421).
4. **The two arms carry materially different CCS fleets** (3.50 vs 11.62 TWh), so unlike
   NEISO and NYISO the defect **does not mostly cancel in PJM's delta**.
5. **PJM is the campaign's largest divergence from its committed board key**: energy
   **+5.6 % → +18.0 %**, CO2 373 → 470 Mt against the key's 349 → 382 Mt.

---

## 1. What was solved

Two legs, 10 solve-years, ~97 min. **Wall time is strongly super-linear inside a five-year
window** — 6.5 / 2.3 / 4.7 / 14.0 / **20.9** min per solve-year for 2026–2030, peak RSS
6.7–8.7 GB. That is plan §2.4's late-horizon PJM behaviour arriving early, and it is why
rule 12 runs this ISO alone. ORGANIC not spent: phase 0 measured
`max|LOAD-HI − LOAD-HI-ORGANIC| = 0.0 MW` — PJM now ships `high := mid` at **every** anchor
(the limitation CAISO used to carry, moved here by SCN-LOAD), so the arm is a guaranteed-zero
delta. Note this differs from WS-4b's stated reason ("high = mid *through 2030*, diverges at
2040"); at HEAD it is degenerate at every horizon.

## 2. The headline table

| case | year | CO2 Mt | ΔCO2 | $/MWh | peak GW | margin | unserved TWh | import CO2 Mt | backstop MW |
|---|---|---|---|---|---|---|---|---|---|
| REF | 2026 | 373.20 | — | 41.71 | 167.21 | −0.095 | 0.000 | 0.76 | 0 |
| REF | 2030 | 470.46 | — | 80.74 | 201.52 | −0.165 | 0.078 | 5.85 | 8,956 |
| LOAD-HI | 2026 | 410.55 | **+37.36** | 53.12 | 181.55 | −0.166 | 0.041 | 1.84 | 0 |
| LOAD-HI | 2027 | 460.59 | +66.92 | 112.68 | 198.01 | −0.219 | 1.286 | 3.68 | 0 |
| LOAD-HI | 2028 | 514.12 | +95.49 | 370.18 | 216.66 | −0.273 | 10.005 | 8.69 | 843 |
| LOAD-HI | 2029 | 563.70 | +127.31 | 601.89 | 237.72 | −0.305 | 25.490 | 11.77 | 2,214 |
| LOAD-HI | 2030 | 619.08 | **+148.62** | 1101.46 | 261.46 | −0.336 | **63.688** | **14.95** | 5,900 |

**PJM has the campaign's largest absolute ΔCO2 (+148.6 Mt at 2030)** — but 63.7 TWh of
LOAD-HI's load is shed, so the 2029–2030 figures are slack-bound and understate the
unconstrained response.

## 3. SCORING — WS-4b §5.3, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c |
|---|---|---|---|---|
| **(a)** | the cap-bound backstop `gas_ct` ladder is the **only** responding channel; ~734 / 1,469 / 2,937 / 3,874 MW at `mid` | backstop fires and is the responding channel — REF 0 / 843 / 843 / 3,900 / 8,956 MW; LOAD-HI 0 / 0 / 843 / 2,214 / 5,900. Level and pattern differ from their cited figures | **HIT** (channel), magnitude differs | untestable at T0 |
| **(b)** I7/I12 | widen; I7 to "tens of GW", I12 further negative | REF `{I7, I12}` — **exactly the board's bare key**; LOAD-HI margin −0.166 → −0.336 vs REF −0.095 → −0.165 | **HIT** | HIT at 2026 |
| **(b)** I3 | **"absent at `mid`, expected to appear 2029–2030"** | REF has **no I3**; LOAD-HI **gains I3** — but from **2027** (0.12 % of load, 164 h), reaching 4.24 % by 2030 | **SPLIT** — mechanism right, timing 2 yr early | untestable at T0 |
| **(b)** peak | +7.7 → +27.8 GW | **+14.3 → +59.9 GW** — about 2× their range | magnitude MISS | — |
| **(d)** | `backstop_built` + `unserved_mwh` beside CO2 | both present, both non-zero, both reported | **HIT** | HIT |
| **(e)** | **"up and small"**; exports fall, clamped, no offset; bounded by the 10,500 MW import limit | +1.08 → **+9.10 Mt**, i.e. **2.9 – 6.1 % of ΔCO2**; well inside the ~37 Mt the import limit permits | **HIT** on sign, relative scale and bound — but "small" is *relative*: the absolute line reaches 9.1 Mt | HIT (+0.339 Mt at T0) |

**The peak magnitude miss has the same single cause as ERCOT's and NYISO's:** SCN-LOAD raised
PJM's growth rate, so the LOAD-HI peak runs about twice the increment WS-4b computed on the
older table. Their *mechanism* claims — backstop-only channel, I3 appearing, exports clamped —
all survive; their *levels* do not.

**(c) what a reader may and may not conclude.** *May:* that PJM's rate-limited backstop cannot
keep up with the high case and the residual leaves through slack; the direction and rough size
of the response; that the import line compounds rather than offsets it. *May not:* the
2029–2030 ΔCO2 as an emissions response (63.7 TWh shed); PJM's CO2 **levels** at all — its REF
diverges +18.0 % in energy from the board's key (§6) *and* carries mis-rated CCS from 2029
(§4); a DC attribution (the axis is degenerate here).

## 4. THE FALSIFICATION — my CCS mechanism claim dies in PJM

**What I claimed** (NEISO FINDING §2.2, repeated in NYISO's): the retrofit screen is armed by
a **state carbon program**, so `gas_cc_ccs` appears in NEISO / NYISO / CAISO and **not** in
ERCOT / PJM / MISO. ERCOT, NEISO and NYISO confirmed it; I reported "3/3 confirming".

**PJM kills it.** No state carbon program, and:

| PJM `gas_cc_ccs` | 2028 | 2029 | 2030 |
|---|---|---|---|
| REF | 0 | 909.8 MW / 3.50 TWh | 909.8 MW / 3.50 TWh |
| LOAD-HI | 0 | **1,512.8 MW / 11.62 TWh** | **1,512.8 MW / 11.62 TWh** |

**Why I was wrong.** `ccs.py` values the retrofit as *"the incremental uplift over the best
unabated state, with the certificate and §45Q … as bid offsets"* — and **§45Q is a federal
credit, independent of any carbon price**. A carbon program drives *magnitude*, not arming. I
over-read capx D50's "at carbon 0 the repair closes the screen" as a general condition when it
is one ISO's measured result.

**Corrected mechanism, as measured across four ISOs:** a carbon program ⇒ retrofit is **large
and early** (NEISO 8,833 MW, NYISO 6,475 MW, both from 2028); §45Q alone ⇒ **small and late**
(PJM 909.8 MW from 2029); ERCOT ⇒ **zero**, so 45Q alone is not sufficient everywhere.
*Hypothesis, not a claim:* ERCOT's REF sits at $4,438/MWh in shortage, so unabated CC margin
may make the **incremental** retrofit uplift negative there. Untested here.

**The rate, and why PJM is the worst case.**

| PJM 2030 REF | TWh | Mt | t/MWh |
|---|---|---|---|
| `coal` | 213.964 | 220.396 | 1.0301 |
| `gas_cc` | 464.277 | 180.381 | 0.3885 |
| **`gas_cc_ccs`** | **3.498** | **2.121** | **0.6063** |
| `gas_ct` | 114.295 | 61.963 | 0.5421 |

90 % capture implies **≤ ~0.039 t/MWh**; measured **0.6063** is **~15×** that, and *above* the
unabated peaker. Contamination is small in level terms — ≈1.99 Mt against 470.5 Mt, **0.42 %**
— because PJM's retrofit fleet is small. **But the delta is worse off than NEISO's or
NYISO's**: the arms carry 3.50 vs 11.62 TWh of CCS, so the defect does **not** mostly cancel.

## 5. The implied MARGINAL rate — P-4 vindicated where ERCOT split it

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | ratio |
|---|---|---|---|---|---|
| 2026 | +37.358 | +72.372 | 0.5162 | 0.6352 | **0.81** |
| 2027 | +66.919 | +115.328 | 0.5802 | 0.6171 | 0.94 |
| 2028 | +95.490 | +155.394 | 0.6145 | 0.6082 | 1.01 |
| 2029 | +127.315 | +204.302 | 0.6232 | 0.5950 | 1.05 |
| 2030 | +148.623 | +232.736 | 0.6386 | 0.5958 | **1.07** |
| *WS-4c T0* | *+20.084* | *+39.54* | *0.508* | *0.663* | *0.77* |

WS-4c's T0 ratio (0.77, coal diluting the marginal rate down) holds at 2026 (0.81) and then
**crosses above 1.0 from 2028** — the same inversion ERCOT showed, and for the same reason:
as load grows the marginal unit becomes the peaker, not the CC. **This is the clean case for
my P-4**, which predicted a monotone rise toward 1.0: measured **0.81 → 0.94 → 1.01 → 1.05 →
1.07**, monotone in every step.

## 6. Divergence from the committed board key — the campaign's largest

| PJM REF vs `pjm-2026-2030-d45r-remeasure` | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| energy Δ % | +5.6 | +8.5 | +11.6 | +14.7 | **+18.0** |
| CO2 HEAD / key (Mt) | 373 / 349 | 394 / 353 | 419 / 362 | 436 / 365 | **470 / 382** |

My G-DRIFT §2.2 predicted **+11.6 %** at 2030; measured **+18.0 %** — right in sign and order,
**understated by 6.4 pp**. Recorded as a partial miss of my own arithmetic. The board's PJM key
is stale as a description of HEAD by more than either NEISO's or ERCOT's.

## 7. My own predictions

- **P-2 near-HIT (4 of 5).** Band ±25 % of 0.508 → [0.381, 0.635]. Measured 0.5162 ✓ 0.5802 ✓
  0.6145 ✓ 0.6232 ✓ **0.6386 ✗** — outside by 0.6 %.
- **P-3 MISS** (second time). Predicted the coal-ISO ratio stays < 1.0; it crosses at 2028.
- **P-4 HIT** (first clean one). Monotone rise 0.81 → 1.07.
- **P-5 SPLIT.** Fossil share of Δenergy 0.95 / 0.93 / 0.90 / 0.91 / 0.88 — a mild fall, in the
  predicted direction but not the entry-driven collapse I argued for.
- **P-6 HIT.** Import line up and small relative to the delta, as predicted.
- **CCS mechanism claim: FALSIFIED** (§4).

## 8. STOP gate — PASS

S1 CO2 and price both rise ✓ · S2 ratio 0.81–1.07 inside [0.5, 2.0] ✓ · S3 footprint confined
to fossil classes; nuclear/hydro/VRE Δ carry no CO2 ✓ · S4 identity n/a (ORGANIC degenerate) ·
S5 LOAD-HI gains I3, which is the **target** phenomenon WS-4b predicted, not a collateral flip;
no non-target load-bearing criterion changed ✓. Killed nothing.

## 9. Routed

1. **The CCS scope claim is wider than the NEISO/NYISO FINDINGs stated** — see §4 and the
   correction recorded in `STATUS-scn-ws5a-load-2026-09-06.md`. Any ISO whose §45Q economics
   clear can carry mis-rated `gas_cc_ccs`; it is not a state-carbon-program phenomenon.
2. **`pjm-2026-2030-d45r-remeasure` is stale as a description of HEAD** — +18.0 % energy,
   +88 Mt CO2 at 2030. Records item for the capx director.
3. **PJM's five-year wall time is super-linear inside the T1 window** (20.9 min for 2030
   alone). Anyone budgeting a PJM campaign from a T0 anchor will under-budget by ~2×.

## 10. Duties

No default moved, no knob moved, no `ScenarioConfig` field added; **DOF ledger: zero**.
Campaign YAML, `report_scenario_deltas.py`, `collate_scenario_campaign.py`,
`register_forecast_run.py`, `ccs.py` and all of `src/`: read only. `program-status.json`,
`ff-verdicts.json`, backcast namespace: untouched. Rule 15/§7.5 forecast namespace only;
rule 27 verified; rule 29(c) no screen/control bundle; backcast byte-identity untouched.
