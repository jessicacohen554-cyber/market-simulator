# FINDING — SCN-WS5A-LOAD / NEISO: ruling S5's premise is false at HEAD

**Lane** SCN-WS5A-LOAD (NEISO) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Frozen pin** `1cc45bb2` ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Legs** REF · LOAD-HI (ORGANIC not spent — `DATACENTER_ADDITIONS_MW["NEISO"] == {}`,
phase 0) · **Scored against** SCN-WS4b §5.6 and SCN-WS4c §3.7.

---

## 0. Bottom line

1. **RULING S5's LOAD/POLICY SPLIT RESTS ON A PREMISE THAT IS FALSE AT HEAD.** The desk held
   the policy half because Stage A-LOAD supposedly "has **no `gas_cc_ccs` exposure at all**"
   (r#6 am.1, verbatim). **NEISO's load legs carry 8,832.9 MW / 16.72 TWh of `gas_cc_ccs` in
   the REFERENCE case by 2030**, and the SCN-WS2b emission-rate defect is live on all of it.
2. **Quantified: NEISO's 2030 CO2 level is overstated by ≈5.60 Mt — 41.9 % of its own
   reported total** (§2). The retrofitted units emit at **0.3719 t/MWh**, *higher* than the
   unabated `gas_cc` they replaced (0.3666), where `ccs_capture_rate = 0.90` and the spec
   requires `emission_rate_co2 *= (1 − capture_rate)` ⇒ ≈0.0367.
3. **The mechanism is identified and it predicts the rest of the campaign** (§2.2): the
   retrofit screen is armed by *any* carbon signal, and NEISO/NYISO/CAISO carry **state
   carbon programs** (RGGI/CARB) that resolve whether or not a campaign case sets a carbon
   override. ERCOT/PJM/MISO carry none. ERCOT measured **zero** CCS, as this predicts.
4. **Two of SCN-WS4c's NEISO verdicts reverse at HEAD** (§3): their (a)/(b) MISS becomes a
   partial HIT — the backstop **does** fire under LOAD-HI (50.2 MW, 2029) — and their (e),
   "the most precise prediction in WS-4b's document", no longer holds: the import line goes
   **negative** in 2028–2029.
5. NEISO is otherwise the campaign's cleanest ISO: **14/14 invariants PASS in both arms**,
   zero unserved energy in every year.

---

## 1. What was solved

| leg | years | wall / solve-year | peak RSS |
|---|---|---|---|
| REF | 2026–2030 | ≈1.1 min | ≈2.8 GB |
| LOAD-HI | 2026–2030 | ≈1.1 min | ≈2.8 GB |

Two legs, 10 solve-years, ~11 min. ORGANIC not spent: phase 0 measured
`max|LOAD-HI − LOAD-HI-ORGANIC| = 0.0 MW` in every year, so it is a guaranteed-zero delta.

## 2. THE S5 FINDING — `gas_cc_ccs` in a load-only campaign

### 2.1 What is on the books, and what it emits

NEISO 2030, from the committed by-fuel table:

| case | fuel | capacity GW | generation TWh | emissions Mt | **implied t/MWh** |
|---|---|---|---|---|---|
| REF | `gas_cc` | 2.494 | 13.752 | 5.042 | 0.3666 |
| REF | **`gas_cc_ccs`** | **8.833** | **16.717** | **6.217** | **0.3719** |
| LOAD-HI | `gas_cc_ccs` | 8.803 | 16.894 | 6.306 | 0.3732 |

**The decisive test is absolute, not comparative.** `ccs_capture_rate = 0.90` on any gas-CC
fleet implies a post-retrofit rate of **≤ ~0.05 t/MWh**. NEISO's retrofitted class measures
**0.3719** — about **10× too high** — which no unit mix can explain. That is the
selection-robust statement, and it matches SCN-WS2b's per-unit measurement (`fuel_type` flips
✓, `heat_rate` rises ×1.12 ✓, `emission_rate` never reduced ✗).

*A comparative framing I initially used and now withdraw as unsound:* that the retrofitted
class emits **more** than the unabated residual (0.3719 vs 0.3666). It is true here, and
striking, but it is **confounded by unit selection** — the retrofit screen picks units
economically, so the retrofitted and residual classes are not comparable populations. NYISO
makes the confound concrete: there the retrofitted class measures **0.2578** against an
unabated residual of **0.4135**, i.e. *lower*, while still being ~6× above what 90 % capture
implies. The absolute test holds in both ISOs; the comparative one does not travel.

**Size of the error, NEISO 2030 REF:** intended 16.717 TWh × (0.3666 × 0.10) = **0.61 Mt**;
measured **6.22 Mt**; overstatement **≈5.60 Mt**, against a reported ISO total of
**13.368 Mt** — **41.9 %**. The retrofit fleet first appears in **2028** (2.98 GW) and grows
to 5.90 GW (2029) and 8.83 GW (2030), so 2028–2030 are all affected.

### 2.2 Why the desk's premise failed, and what it predicts

S5 reasoned from the **credit** channel: the CES credits `gas_cc_ccs` at 0.95, my cases arm
no CES, therefore no exposure. But the defect is in **dispatch**, not crediting, and the
**retrofit screen** is armed by any resolved carbon signal — including a *state program*
that exists independently of the campaign:

| ISO | `STATE_CARBON_PRICE_BY_ISO` | predicted `gas_cc_ccs` | measured |
|---|---|---|---|
| NEISO | **RGGI** | yes | **8,833 MW @2030** ✓ |
| NYISO | **RGGI** | yes | *(pending)* |
| CAISO | **CARB** | yes | *(pending)* |
| ERCOT | none | no | **NONE** ✓ |
| PJM | none | no | *(pending)* |
| MISO | none | no | *(pending)* |

This is exactly the asymmetry capx D50 measured and published — *"at carbon 0 the repair
closes the screen (ERCOT 3.79 GW → 0 …) and under RGGI it does not (NEISO 12.79 → 12.38 GW)"*
— so the evidence that S5's premise was wrong **already existed in the capx record** when the
ruling was written. Registered here as a falsifiable prediction for the three pending ISOs.

### 2.3 What it does and does not invalidate

- **NEISO's CO2 LEVELS for 2028–2030 are not quotable.** 41.9 % of the 2030 figure is
  emissions from units the model believes are capturing 90 % of their CO2.
- **The DELTA is mostly protected but NOT fully.** Both arms carry near-identical retrofit
  fleets (REF 8,833 MW vs LOAD-HI 8,803 MW), so most of the defect cancels — but
  **+0.089 Mt of the 2030 ΔCO2 of +1.408 Mt rides on defective units, i.e. 6.3 %**. Deltas
  are usable with that stated; they are not defect-free.
- **2026–2027 are clean** — the retrofit fleet is empty before 2028.

## 3. SCORING — WS-4b §5.6, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c |
|---|---|---|---|---|
| **(a)** | backstop **fires** under LOAD-HI, share 1.2 % → the 10–30 % CAVEAT band | it **does** fire — but only **50.2 MW, first in 2029**; REF stays 0.0. Direction right, magnitude far short of a CAVEAT-band share | **SPLIT** | MISS → **reverses** |
| **(b)** | 14/14 PASS at `mid`; I7 holds by construction; I12 in band; **no I3** | **14/14 PASS in both arms**; `unserved_mwh` = **0.0** in every year of both | **HIT** | MISS → **reverses** |
| **(d)** | `backstop_built` + `unserved` + import line **per tranche** beside CO2 | all present and reported | **HIT** | HIT |
| **(e)** | import line rises **early** (≤ ~2.1 Mt) then **saturates**; sign **+** | +0.032, +0.072, **−0.066**, **−0.012**, +0.061 Mt — **sign flips negative in 2028–2029** | **MISS** | HIT → **reverses** |

**On the (e) reversal.** WS-4c called this "the most specific prediction in their document"
and scored every clause of it a HIT (+0.079 → +0.214 peaking 2028, then falling, all
positive). At HEAD the line is an order of magnitude smaller and changes sign. The plausible
cause is §2's retrofit fleet: 8.8 GW of `gas_cc_ccs` re-orders the in-ISO merit stack, so the
seam is drawn differently. I did not isolate it — doing so needs a no-CCS counterfactual,
which is the held policy half's work, not this lane's. Recorded as an attribution limit.

**(c) what a reader may and may not conclude.** *May:* the direction and rough size of the
in-ISO response; that NEISO meets high load without shedding a single MWh. *May not:* any
2028–2030 CO2 **level** (§2.3); that the import line's sign is settled (it reverses a
previously-HIT prediction and is not root-caused); that 50.2 MW of backstop validates
WS-4b's CAVEAT-band expectation.

## 4. The implied MARGINAL rate

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | ratio |
|---|---|---|---|---|---|
| 2026 | +0.444 | +1.040 | 0.4273 | 0.3839 | 1.11 |
| 2027 | +0.644 | +1.397 | 0.4614 | 0.4116 | 1.12 |
| 2028 | +1.041 | +2.748 | 0.3788 | 0.3974 | 0.95 |
| 2029 | +1.258 | +3.093 | 0.4068 | 0.4072 | 1.00 |
| 2030 | +1.408 | +3.494 | 0.4030 | 0.4076 | 0.99 |
| *WS-4c T0* | *+0.812* | *+1.81* | *0.450* | *0.384* | *1.17* |

**Caveat that binds this table:** from 2028 the fleet average is itself computed over a fossil
fleet containing 8.8 GW of mis-rated `gas_cc_ccs`, so the 2028–2030 *ratios* inherit §2's
defect. The 2026–2027 rows are clean.

## 5. My own predictions

- **P-2 HIT.** All five implied rates (0.379–0.461) inside ±25 % of WS-4c's 0.450 →
  [0.338, 0.563].
- **P-3 SPLIT.** Predicted the gas-ISO ratio stays **≥ 1.0**. Measured 1.11, 1.12, then
  0.95 / 1.00 / 0.99 — it dips just below from 2028, in the years §2's defect contaminates.
- **P-5 SPLIT.** Fossil share of Δenergy: 0.87, 0.78, 1.11, 1.01, 0.95 — falls then rises,
  not the monotone fall predicted.
- **P-6 MISS.** Predicted the NEISO import line rises. It rises, then goes **negative**
  (§3 (e)).
- **G-DRIFT §2.2 energy prediction HIT:** predicted NEISO REF −2.3 % vs the committed key;
  measured **−1.1 % → −3.2 %**.

## 6. STOP gate — PASS

S1 CO2 and price both rise ✓ · S2 ratio 0.95–1.12, inside [0.5, 2.0] ✓ · S3 footprint confined
to fossil classes, `import` emissions 0.0, nuclear/hydro/solar/wind Δ = 0.000 ✓ · S4 identity
n/a (ORGANIC not spent) · S5 both arms 14/14 PASS, no criterion flips ✓. Killed nothing.

## 7. Independent reproduction of WS-4c's routed NEISO staleness

WS-4c routed `neiso-2026-2030-d50-ccscapex` as stale. Measured here, at a different pin, on
this lane's own REF:

| NEISO REF CO2 vs committed d50 | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| Δ Mt | −0.476 | −0.500 | −0.953 | −1.326 | **−1.609** |
| Δ % | −2.9 | −2.8 | −5.7 | −8.6 | **−10.7** |

Same direction, same growing divergence, and **REF's backstop is 0.0 in every year** — the
d50 50 MW 2029 firing is gone here too. Two lanes, two pins, one verdict: the board key is
stale. (The firing has *moved to the LOAD-HI arm*, §3(a).)

## 8. Routed (not executed)

1. **RULING S5 SHOULD BE RE-PUT TO THE OWNER.** Its load/policy split assumed Stage A-LOAD has
   no `gas_cc_ccs` exposure; §2 measures 8.8 GW of it in NEISO's *reference* case, mis-rated,
   contaminating 41.9 % of a reported CO2 level. The split still buys something real — no
   *crediting* exposure — but "uncontaminated half" is not what it bought. The desk owns the
   ruling; this lane reports the measurement.
2. **The capx CCS repair now gates more than the policy half.** It gates every CO2 **level**
   from 2028 in every state-carbon-program ISO, including load-only runs.
3. **`neiso-2026-2030-d50-ccscapex` stale** — independently reproduced (§7).
4. **The registration `run_id` collapse** (`iso-start-end-LABEL`, no case component) — see the
   ERCOT FINDING §8.3.

## 9. Duties

No default moved, no knob moved, no `ScenarioConfig` field added; **DOF ledger: zero** free
parameters. `configs/scenario_campaign_matrix.yaml`, `report_scenario_deltas.py`,
`register_forecast_run.py`, `model/capacity_evolution/ccs.py` and everything under `src/`:
**read only**. `program-status.json`, `ff-verdicts.json`, the backcast namespace: **untouched**.
Rule 15/§7.5 forecast namespace only; rule 27 pushes fetch-back verified; rule 29(c) no screen
or control bundle; backcast byte-identity untouched.
