# SYNTHESIS — SCN-WS5A-LOAD: the Stage A-LOAD campaign, six ISOs

**Lane** SCN-WS5A-LOAD · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Frozen pin** `1cc45bb2` · **Campaign** `scn-campaign-load-2026-09-06` ·
**16 legs / 80 solve-years, all rc=0** · Per-ISO FINDINGs:
`FINDING-scn-ws5a-load-{ercot,neiso,nyiso,pjm,miso,caiso}-2026-09-06.md` ·
Standing corrections and routes: `STATUS-scn-ws5a-load-2026-09-06.md`.

---

## 0. THIS IS HALF A CAMPAIGN, AND THE HALF IT LEFT OUT IS NOT THE ONLY CONTAMINATED ONE

Ruling S5 split Stage A into a LOAD half (run now) and a POLICY half (held), on the premise
that the load half *"has no `gas_cc_ccs` exposure at all"*. **That premise is false.** Five of
six ISOs carry mis-rated `gas_cc_ccs` in their **reference** case from 2028 — the SCN-WS2b
emission-rate seam, repaired by capx D77 *after* every leg here was solved. The policy half
remains held and this campaign remains half a campaign; what changed is that the half that ran
is not the uncontaminated one it was taken to be. Every CO2 **level** from 2028 in
NEISO / NYISO / CAISO / PJM / MISO is affected; **deltas** mostly survive, and ERCOT is clean.

---

## 1. The six-ISO modeled system

**Total is the six-ISO MODELED SYSTEM, never a national figure.** Outside it: SPP, the
Southeast, and the non-ISO West — roughly a third of US load, not modeled and not estimated.

| year | REF Mt | LOAD-HI Mt | **ΔCO2** | import-attributed Mt (REF → HI) | unserved TWh (REF → HI) |
|---|---|---|---|---|---|
| 2026 | 1,027.0 | 1,129.6 | **+102.6** | 15.75 → 16.98 | 0.49 → 3.00 |
| 2027 | 1,097.0 | 1,250.4 | **+153.4** | 15.44 → 18.63 | 4.85 → 73.88 |
| 2028 | 1,160.0 | 1,334.4 | **+174.3** | 18.85 → 25.34 | 42.13 → 243.47 |
| 2029 | 1,200.8 | 1,426.3 | **+225.5** | 19.96 → 29.40 | 76.90 → 399.45 |
| 2030 | 1,277.4 | 1,529.3 | **+251.9** | 24.51 → **34.84** | 130.14 → **645.05** |

**The three side lines are not decoration.** At 2030 the in-ISO ΔCO2 is +251.9 Mt; imports add
**+10.3 Mt** on top; and **645 TWh of LOAD-HI's load is shed** — about 42 % of the six-ISO
served energy — so the +251.9 Mt is what the fleet emitted *while failing to serve the case*,
not the emissions of serving it. **It is a floor, not a total.**

### 1.1 The DC volume axis is worth almost nothing; its shape is worth everything

`LOAD-HI-ORGANIC` exists in only four ISOs (PJM and NEISO ship `high := mid`). On the **common
four-ISO set** — the comparison the collation tool gets wrong (§6.3):

| year | REF(4) | LOAD-HI(4) | ORGANIC(4) | ΔHI | ΔORG | **shape gap** |
|---|---|---|---|---|---|---|
| 2026 | 637.9 | 702.7 | 702.0 | +64.8 | +64.1 | −0.76 |
| 2028 | 725.6 | 803.4 | 803.2 | +77.8 | +77.6 | −0.21 |
| 2030 | 793.6 | 895.4 | 895.5 | +101.8 | +102.0 | **+0.13** |

**Doubling the data-centre block moves four-ISO CO2 by 0.13 Mt in 2030 — 0.1 % of the load
response.** Yet the same axis moves ERCOT's load-weighted price by ~$44/MWh and MISO's peak by
3.91 GW at *identical energy*. This confirms SCN-WS4c §6 at the horizon: **a campaign that
varies DC volume without varying DC shape is varying the less important axis.**

## 2. Cross-ISO scoring against SCN-WS4b's pre-declaration

| ISO | (a) mechanism | (b) invariants | (d) table line | (e) import line |
|---|---|---|---|---|
| **ERCOT** | HIT | **MISS** (+ SPLIT on 2030 magnitude) | HIT | HIT |
| **NEISO** | SPLIT | HIT | HIT | **MISS** |
| **NYISO** | HIT | **SPLIT** | HIT | HIT |
| **PJM** | HIT | HIT + SPLIT (I3 timing) | HIT | HIT |
| **MISO** | HIT | HIT + MISS (I3 timing) | HIT | HIT |
| **CAISO** | HIT | HIT | HIT | **HIT at the horizon** (WS-4c's SPLIT resolves) |

**16 HIT · 4 SPLIT · 3 MISS · 1 combined.** The pattern is sharp and has one cause:

- **Every *mechanism* call survived.** Which channel answers the load — energy-only scarcity in
  ERCOT, the rate-limited backstop in PJM, the ladder in CAISO/MISO, the never-firing backstop
  in NYISO, the import seam in NEISO — was right in all six.
- **Every *level* call that depended on the DC `high` anchor failed.** ERCOT's tail regime,
  NYISO's peak flattening, PJM's peak increment. SCN-LOAD (ruling S4) re-derived the anchor
  after WS-4b's pin, so those were computed on retired numbers.
- **NYISO isolates the cause beyond argument**: WS-4b's *ORGANIC* peak prediction (which uses
  the `mid` anchor SCN-LOAD left alone) lands within **0.4 GW**; their *LOAD-HI* prediction
  (which uses the retired `high` anchor) misses by **3.3 GW**. Same document, same method.

**Where a T0 verdict and a horizon verdict differ, three times:** WS-4c's ERCOT (b) HIT becomes
a MISS; their NEISO (a)/(b) MISS becomes a partial HIT (the backstop *does* fire under LOAD-HI,
50.2 MW at 2029); their CAISO (e) SPLIT resolves to a HIT at 2030. In each case both lanes were
right about their own year.

## 3. Does WS-4c's implied-marginal-rate split hold at the horizon? **No.**

WS-4c measured a clean 3–3 split at T0: below fleet average wherever coal is inframarginal
(ERCOT 0.73×, PJM 0.77×, MISO 0.65×), above it in gas-dominated stacks (CAISO/NYISO 1.05×,
NEISO 1.17×). At 2030:

| ISO | ΔCO2 Mt | implied t/MWh | fleet avg | **ratio 2030** | WS-4c T0 | sign |
|---|---|---|---|---|---|---|
| ERCOT | +13.4 | 0.5435 | 0.5579 | **0.97** | 0.73 | holds (barely) |
| CAISO | +10.2 | 0.4205 | 0.3176 | **1.32** | 1.05 | holds |
| PJM | +148.6 | 0.6386 | 0.5958 | **1.07** | 0.77 | **INVERTS** |
| MISO | +72.9 | 0.6476 | 0.6338 | **1.02** | 0.65 | **INVERTS** |
| NYISO | +5.3 | 0.4252 | 0.3708 | **1.15** | 1.05 | holds |
| NEISO | +1.4 | 0.4030 | 0.4076 | **0.99** | 1.17 | **INVERTS** |

**The coal/gas separation is a T0 phenomenon.** By 2030 every ratio sits in **0.97 – 1.32**,
clustered at or just above 1.0, and the three coal ISOs have all crossed. The mechanism is
visible in the by-fuel deltas: coal is inframarginal and *stays* inframarginal (ERCOT's coal
moves +0.00 TWh in every year), so as load grows the marginal unit becomes the **peaker**, and
a peaker is dirtier than the CC-weighted average. WS-4c's heuristic is therefore **conditional
on headroom**, not on fuel mix — a sharpening of their §6, not a contradiction.

**Practical consequence for attribution:** at T0 the fossil-average heuristic was biased
high by 23–35 % with coal; at the horizon it is biased **low** by 2–32 % almost everywhere. A
large-load attribution using fleet-average rates is wrong in *both* regimes, in opposite
directions, and the implied marginal rate is computable from the two arms any campaign already
solves.

## 4. The leakage line, six ISOs

| ISO | REF import CO2 2030 | Δ under LOAD-HI | as % of ΔCO2 | note |
|---|---|---|---|---|
| NYISO | 11.68 Mt | **+0.54** (peak +0.96 at 2029) | 7 – 25 % | largest relative leakage |
| PJM | 5.85 Mt | **+9.10** | 2.9 – 6.1 % | largest absolute |
| NEISO | 6.32 Mt | +0.06 (**sign flips negative 2028–29**) | 4 – 14 % | saturates at the seam |
| CAISO | 0.00 Mt | **+0.63, first motion at 2030** | 6 % | zero-EF headroom exhausts |
| ERCOT | 0.00 | 0.00 | — | **no import node** — a boundary, not a clean result |
| MISO | 0.00 | 0.00 | — | **no import tranches** — capacity-side injections |

**Leakage sign is not a regional constant.** NEISO and NYISO are both RGGI and behave
oppositely; CAISO's line is flat for four years then moves. Any six-ISO CO2 figure read without
this line understates by up to **10.3 Mt** at 2030.

## 5. Honest-unfit, per ISO — what may not be quoted

- **ERCOT** — levels unquotable at every year, deltas only 2026–27. REF itself sheds 127 TWh by
  2030 at $4,438/MWh with `hours_ge_500` = 7,962/8,760. From 2028 both arms price at the VOLL
  ceiling, so ΔCO2 measures fleet saturation. **CCS-clean.**
- **PJM** — levels unquotable (REF +18.0 % energy vs its board key; mis-rated CCS from 2029);
  63.7 TWh shed under LOAD-HI. Deltas usable with the CCS caveat, which here does **not**
  cancel (arms carry 3.50 vs 11.62 TWh).
- **MISO** — levels unquotable (+14.7 % vs key; **I3 now fails in REF** where the key has it
  passing); 42.4 TWh shed, backstop at its cap.
- **CAISO** — HOLD ISO (REF carries I7 + I12); 16.2 % of the 2030 level is mis-rated CCS.
- **NYISO** — structurally the cleanest (14/14 PASS, zero unserved) but **25.3 %** of its 2030
  level is mis-rated CCS; its confirmed-exit channel is inert (empty registry, "DATA NEEDED").
- **NEISO** — 14/14 PASS, zero unserved, and **41.9 %** of its 2030 level mis-rated — the
  campaign's worst contamination on its cleanest ISO.

**Every ISO:** `emissions_mt` is read with `unserved_mwh` and `import_co2_mt_reported` beside
it, never as a total.

## 6. What this campaign found that nobody pre-declared

1. **Ruling S5's premise is false** (§0) — routed, and capx D77 landed the repair.
2. **ERCOT's shipped forecast REF is in permanent shortage at HEAD** — not a load-case artefact,
   an ISO-specific consequence of SCN-LOAD raising its growth 7.9 → 13.48 %/yr. NEISO's and
   NYISO's REFs are clean, so this is not systemic.
3. **A collation defect** — `collate_scenario_campaign.py` differences sums over *different* ISO
   sets when coverage is incomplete; the system-scope ORGANIC delta reads +5.46 Mt where the
   common-set answer is +18.83 Mt (a 71 % understatement on the three-ISO partial). Routed to
   SCN-FIX1; §1.1 uses the common set.
4. **A registration defect** — `run_id` is `iso-start-end-LABEL` with no case component, so N
   cases under one label silently collapse onto one sidecar. Caught before it reached the
   record; repaired to WS-4c's convention.
5. **The CCS rate spread is unexplained** — implied rates 0.1496 / 0.2578 / 0.3719 / 0.6063
   across CAISO / NYISO / NEISO / PJM, ratios 0.39–1.56 against their own unabated `gas_cc`.
   Not what a uniform never-reduced rate predicts. Useful as D77's before-picture.

## 7. My own pre-registered predictions, scored

| # | prediction | result |
|---|---|---|
| **P-1** | ERCOT stays in the **relocate** regime; WS-4b's tail does not reproduce | **HIT** — energy deltas identical between arms (22.978 vs 22.984 TWh), no tail |
| **P-2** | implied rate within ±25 % of WS-4c's T0 value | **3 HIT / 3 MISS** (NEISO, NYISO, CAISO hit; ERCOT, MISO, PJM miss) |
| **P-3** | coal ISOs stay < 1.0, gas ISOs ≥ 1.0 | **MISS ×3** — all three coal ISOs cross above |
| **P-4** | ratio drifts **up** toward 1.0 as the stack tightens | **HIT ×3** (PJM, MISO clean monotone; ERCOT split) |
| **P-5** | fossil share of Δenergy **falls** with entry | **MISS ×5** — flat or rising; with backstops capped and slack binding, essentially all added energy is fossil-served |
| **P-6** | leakage: NEISO/NYISO up, ERCOT/MISO 0.0, PJM up-and-small, **CAISO positive by 2029–30** | **HIT** except NEISO's sign flip — CAISO's first motion is **exactly 2030** |
| — | **CCS armed by a state carbon program** | **FALSIFIED by PJM** — §45Q is a bid offset independent of carbon price; corrected in `STATUS` |
| — | G-DRIFT §2.2 energy divergence | **direction 6/6**; magnitude exact on NYISO (−0.1 vs −0.2 %) and NEISO, understated on ERCOT (+22.4 predicted vs +16.5), PJM (+11.6 vs +18.0), MISO (+9.4 vs +14.7) |

## 8. CARD D-5 — the Stage-B grant, with the cost table its charter requires

D-5 has been held since r#5 pending *"Stage A's cost table"*. **It now exists, measured.**

| ISO | legs | solve-yrs | wall min | **min/solve-yr** | peak RSS GB |
|---|---|---|---|---|---|
| NEISO | 2 | 10 | 10.9 | **1.09** | 3.49 |
| ERCOT | 3 | 15 | 19.5 | **1.30** | 4.10 |
| NYISO | 3 | 15 | 60.8 | **4.06** | 3.80 |
| CAISO | 3 | 15 | 65.0 | **4.33** | 4.87 |
| MISO | 3 | 15 | 78.5 | **5.23** | **9.65** |
| PJM | 2 | 10 | 79.0 | **7.90** | **8.90** |
| **TOTAL** | **16** | **80** | **313.7** | **3.92** | — |

**Stage A-LOAD cost: 5.23 h of LP**, plus ~20 min for `data/clean` (one-time per container) and
~35 min of zero-LP analysis/registration. On one 15 GB / 4-core box, with rule 12 honoured
(≤2 concurrent, 1 whenever PJM/MISO/CAISO runs), **wall-clock was ~4.7 h**.

**Three cautions for scaling this to Stage B.**
1. **PJM's wall time is super-linear inside a five-year window** — 6.5 / 2.3 / 4.7 / 14.0 /
   **20.9** min for 2026–2030. Budgeting a PJM campaign from a T0 anchor under-budgets by ~2×.
2. **MISO peaks at 9.65 GB on a 15 GB box.** Rule 12's one-at-a-time cap is necessary, not
   cautious, and it is what serialises the three most expensive ISOs.
3. **A three-case campaign is 16 legs, not 18** — PJM and NEISO ship degenerate DC axes. But
   **do not inherit that**: CAISO's degeneracy claim was stale and its ORGANIC arm carried a
   real (if small) effect. Re-run the ~90 s phase-0 census every time.

**Recommendation, and it is a recommendation only — D-5 is the owner's card.** Stage A-LOAD
cost 5.23 h of LP for six ISOs × 3 cases × 5 years. A Stage B of comparable shape is affordable
on one box in a session. What should gate it is **not** cost but the D77 re-solve (card D-10):
13 of 16 legs here carry mis-rated CCS, so a Stage B built on these numbers inherits it.

## 9. Duties

No default moved, no knob moved, no `ScenarioConfig` field added across all six ISOs; **DOF
ledger: zero free parameters**. `configs/scenario_campaign_matrix.yaml`,
`report_scenario_deltas.py`, `collate_scenario_campaign.py`, `register_forecast_run.py`,
`ccs.py` and all of `src/`: **consumed, never edited**. `program-status.json`,
`ff-verdicts.json` and the backcast namespace: **untouched**. All 16 arms registered into the
forecast namespace under one campaign with `reference_case: REF`; all 16 invariant FAIL sets
declared. Rule 27: every ≥300-line push fetch-back verified. Rule 29(c): no screen or control
bundle produced. **Backcast byte-identity: untouched** — this lane is forecast-mode only.
