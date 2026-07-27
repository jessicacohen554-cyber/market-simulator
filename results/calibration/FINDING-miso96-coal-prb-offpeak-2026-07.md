# FINDING miso-96 — the C7 COAL_PRB off-peak failure is a dated offer-curve regression, not a floor

**Determination: DIAGNOSED, ROOT-CAUSED, NOT FIXED.** No solve, no bundle, no
registration. Keeper unchanged pending the owner's verdict-text decision.

Scored entirely from committed artifacts: the `miso88_egrid_hr` bundle
(`legitimacy_diagnostics.json`, `hourly/`, `run_config.json`), the run payload,
`bench/MISO/`, and `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`.
**No LP re-solve.** Probes: `/tmp` throwaways, listed in §7.

---

## 1. What fails, and why it only just became visible

Commit `ab7ce17` (2026-07-27, rubric v2.8, the ERCOT-121 coal gate-blindness
correction) added the merchant COAL classes to `C7_GATED_CLASSES`. MISO
`COAL_PRB` had been carrying a C7 diurnal-shape failure invisibly in all three
years:

| year | profile r | model off-peak CV | actual off-peak CV | cv_ratio | gate |
|------|-----------|-------------------|--------------------|----------|------|
| 2023 | 0.983 | 0.071 | 0.157 | **0.453** | < 0.50 FAIL |
| 2024 | 0.972 | 0.054 | 0.122 | **0.441** | < 0.50 FAIL |
| 2025 | 0.968 | 0.027 | 0.075 | **0.364** | < 0.50 FAIL |

`shape` is tier=protective, hard=True, so the live determination is **NOT-YET**
against a sidecar that asserts CALIBRATED-WITH-CAVEATS (audit E5). The scorer
got sharper; the keeper did not get worse. Rule 14 `[R-ACCURATE]`: the honest
gate made the verdict worse, so it is root-caused here, not buried.

---

## 2. The handoff's hypothesis is REFUTED — there is no floor

The miso-96 handoff proposed starting at "the floors/must-run/take-or-pay path
for PRB coal" and checking it against rule 17 `[R-FLOOR-WINDOW]`. **D-2 in the
keeper's own committed artifact refutes the floor half outright:**

| year | class | mechanism | forced TWh | class TWh | share |
|------|-------|-----------|-----------|-----------|-------|
| 2023 | COAL | `reliability_floor` | 0.5663 | 173.22 | **0.33%** |
| 2024 | COAL | `reliability_floor` | 0.6019 | 166.00 | **0.36%** |
| 2025 | COAL | `reliability_floor` | 0.4000 | 203.44 | **0.20%** |

That is the *only* mechanism attributed to MISO coal, and it is the sole entry
in all three years. No min-gen floor, no must-run band, no commitment bridge is
binding overnight on MISO coal at any material scale. **Rule 17 has nothing to
bite on** — there is no floor whose window to interrogate. The overnight hold is
**economic**, priced-in through the offer curve.

---

## 3. Which end of the profile fails: the night trough, ~7:1

Hour-of-day profile, normalised to the class mean (2025):

| | HE2 (trough) | HE14 (off-peak top) |
|---|---|---|
| model | 0.938 | 1.015 |
| actual | 0.833 | 1.029 |
| deficit | **−10.5 pp** | −1.4 pp |

The model's off-peak span is 7.9% of mean against a measured 20.5% (2025);
17.7% vs 39.9% (2023). Profile r is 0.968–0.983 — **the diurnal shape tracks;
the amplitude does not**, and the amplitude loss is concentrated almost entirely
in the overnight trough. The real PRB fleet de-loads at night (utilisation
53.6% at HE2 vs 66.2% at HE12, 2025); the model's barely moves (65.9% → 70.9%).

---

## 4. The mechanism: overnight prices sit ~$7 above every PRB tranche

Load-weighted MISO price by hour-of-day, model P1 vs actual RT (body-censored at
$200 so the C3c tail cannot contaminate the comparison):

| window | 2023 model / actual (Δ) | 2024 (Δ) | 2025 (Δ) |
|--------|--------------------------|----------|----------|
| night HE0–3 | 27.19 / 19.42 (**+7.77**) | 24.91 / 18.43 (**+6.49**) | 33.76 / 26.87 (**+6.89**) |
| peak HE16–19 | 34.94 / 35.45 (−0.51) | 33.80 / 35.73 (−1.93) | 42.99 / 50.59 (−7.60) |
| diurnal spread | 7.74 / 16.03 | 8.88 / 17.30 | 9.22 / 23.71 |

The overnight over-pricing is **year-stable at ~+$7 and is not summer-specific** —
it is the annual, all-season figure. At a $33.76 night clearing price every PRB
tranche is inframarginal, so the LP has no economic reason to de-load coal, and
the off-peak profile flattens. The C7 failure is the **generation-side
fingerprint of the diurnal-spread compression already ledgered as C3b**.

This matters for scope: FINDING-miso89 §(2) attributes the compression to a
~10 GW summer-peak fossil under-derate and adjudicates the lane DATA-BLOCKED on
outage grain. That block is a **peak-side** instrument. The night half measured
here is neither summer-specific nor availability-shaped, and is therefore **not
covered by the miso-89 data block.**

Corroborating merit-order evidence (model vs CEMS, class MW, 2025):

| class | Δnight | Δpeak |
|-------|--------|-------|
| **COAL_PRB** | **+537** | −1,712 |
| CC_REGULAR | −972 | −1,864 |
| CT_PEAKER | −2,690 | −3,754 |
| ST_GAS | −1,204 | −1,655 |
| every other fossil class | negative | negative |

`COAL_PRB` is the **only** fossil class the model over-produces overnight. The
model substitutes PRB coal for gas at low load — a merit-order error.

---

## 5. Root cause: a dated regression at miso-66, and the mechanism is real

`cv_ratio` across every MISO bundle carrying a D-1 artifact shows a clean
discontinuity:

| bundle | 2023 | 2024 | 2025 |
|--------|------|------|------|
| `miso65_outage_regen` | **0.880** | **1.036** | 0.470 |
| `miso66_coalconduct` | 0.462 | 0.465 | 0.347 |
| … every later bundle | 0.44–0.47 | 0.43–0.47 | 0.33–0.36 |

The miso-65 → miso-66 config diff is a **single delta**:

```
coal_bit_committed_takeorpay        True → False
coal_committed_takeorpay_regulated  None → True
```

Per the mechanism's own design doc
(`docs/handoffs/miso-coal-conduct-design-2026-07.md` §4, wiring check): arming
the regulated scope moves **RE PRB 9,403 MW from $28.09 → $5.07/MWh**. Nine GW
of PRB committed capacity priced at $5 is inframarginal in every hour of the
year, which is exactly the measured signature.

**The mechanism itself is structurally sound and must not be reverted.**
Take-or-pay coal supply for regulated utilities is real; the scope is carried by
EIA-860 `Regulatory Status` and the discount by each plant's own measured
EIA-923 Schedule-5 contract share — zero fitted scalars, rule-13 admissible,
and the SOM Table 7 evidence says merchants do *not* exercise the discount that
the superseded `coal_bit` scope was handing them. Reverting to miso-65's scope
would trade an accurate input for a residual-friendly one, which rule 14
`[R-ACCURATE]` forbids.

### The actual defect: a volume obligation modelled as an hourly price

Take-or-pay is an **annual/monthly contracted tonnage** obligation. It is
implemented as a **permanent per-hour marginal-price discount** — the committed
tranche passes `1 − contract_share` of its fuel cost in all 8760 hours. Those
are not the same object. A regulated utility that has pre-paid for its coal
still de-loads overnight and burns the contracted tonnage during the day; the
measured CEMS record for these same RE plants shows exactly that (§3). Pricing
the obligation hourly removes the plant's incentive to shift its contracted burn
into the hours the contract does not constrain.

Read against rule 17 `[R-FLOOR-WINDOW]`: the discount has a driver and a forward
story, but **no window** — it binds in every hour, including hours its own driver
evidence (the plants' measured overnight cycling) says the discount should not
determine dispatch. That is the rule-17 defect, relocated from the min-gen path
where the handoff expected it to the offer path where it actually lives.

---

## 6. What this does NOT license

- **Not a revert of `coal_committed_takeorpay_regulated`** (rule 1 `[R-STRUCT]`,
  rule 14 `[R-ACCURATE]`) — a real market behaviour stays in even though it
  worsens this crossing.
- **Not a second mechanism stacked on the same phenomenon** (rule 19
  `[R-ONE-MECH]`) — the fix is a correction to the existing take-or-pay
  representation, not a new overnight coal floor or de-load bridge.
- **Not a tuned discount depth, hour mask, or seasonal multiplier** (rule 13
  `[R-MEASURED]`, rule 24 `[R-DOF]`) — any window must come from the contract's
  own accounting period, not from the cv_ratio residual.
- **Not ledgerable.** C7 is protective and hard. MISO's ledgered budget is
  already 3/3 saturated; the protective budget cannot absorb a hard fail
  regardless. Per the governance note in the miso-96 handoff, the next
  load-bearing miss must be **built**, not documented — and this one is
  protective, which is stricter still.

## 7. Reproduction

Probes (throwaway, `/tmp`, no file under `data/` touched):
`probe_prb.py` (profiles), `probe_prb2.py` (ceiling pin vs floor hold),
`probe_prb3.py` (per-plant envelope), `probe_prb6.py` (diurnal price),
`probe_prb7.py` (class merit error), `probe_prb8.py` (supply stack).
All read committed artifacts only. Rule 22 honoured — 2023–2025 only, no
marker, freeze active.

Secondary observation, reported not actioned: the model's PRB annual-peak
envelope is ~8.4% below the measured fleet peak, broadly (21 of 26 plants), and
the model sits at its monthly-max ceiling in 34.9% of HE18 plant-hours against a
measured 14.6% (2025). That is the **peak** side, is consistent with the miso-89
under-derate, and is covered by the standing outage-grain data ask
(`docs/handoffs/miso-outage-grain-data-ask-2026-07.md`). It is not what fails C7.
