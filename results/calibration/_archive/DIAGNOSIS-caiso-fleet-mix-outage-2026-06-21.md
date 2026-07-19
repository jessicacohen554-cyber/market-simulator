# CAISO outage re-gate + fleet-mix/commitment audit (2026-06-21)

Branch: `claude/caiso-fleet-mix-outage-ec8jp8`. Two threads from the "back to
basics" handoff: **TASK 1** re-gates the keeper on the net-load-filtered
outages; **TASK 2** is a first-principles audit of why the CAISO fleet mix is so
off (right total gas, wrong units). Diagnosis-first: no model knob was changed.

Validators (both committed):
- `scripts/caiso_lmp_validate.py BUNDLE` — load-weighted P2 LMP vs actual DA.
- `scripts/caiso_fleet_mix_validate.py BUNDLE` — **new** this session. Per-class
  annual volume (model vs EIA-923-raw AND EIA-930-scaled `classFull`) + per-
  hour-of-day gas dispatch (model classes vs EIA-930 gas) + evening-ramp panel.

Keeper reconciliation: the confirmed best-so-far is **caiso-15 keeper-repro**
(the all-flags config: `--commitment --priced-interchange --hydro-backfill-year
2024 --hydro-eia930-monthly --gas-hub-basis-overlay --caiso-import-gas-coupling
--caiso-import-solar-shape`; gas commitment floor ON@0.80 by default). caiso-13
"voll-ccsteam" is an older parallel lineage (no gas-coupling/solar-shape/overlay)
— superseded. The re-gate was done on the caiso-15 config.

---

## TASK 1 — outage re-gate (caiso-18)

**Method.** Byte-faithful re-solve of the caiso-15 config, changing ONLY the
outage input. Two solves on this branch's code for a clean same-code A/B:
- `caiso_keeper_oldoutage_2024` — pre-fix CSV (1987 events, `git show 3d898bf`).
  Reproduces the documented caiso-15 baseline **exactly** (mean 42.00, p50 46.80,
  p95 63.73, neg 407 @ 91.9%) — confirms the config is faithful.
- `caiso_keeper_newoutage_2024` — net-load-filtered CSV (1067 events, commit
  b0c41cb; CAISO outage GW-days −37%). **Registered as caiso-18.**

**LMP result (2024, direction + magnitude).** The cooler outages COOL the body,
no tail/peak regression:

| metric | OLD (caiso-15) | NEW (caiso-18) | Δ |
|---|---|---|---|
| mean | 42.00 | **41.17** | **−0.83** |
| residual mean | +6.15 | +5.32 | −0.83 |
| p50 | 46.80 | 46.34 | −0.46 |
| p95 | 63.73 | 62.96 | −0.77 |
| neg<0 count | 407 | 408 | +1 |
| neg precision | 91.9% | 91.9% | flat |
| neg recall | 49.5% | 49.7% | +0.2pp |

**The cooling is localized OVERNIGHT** (h00–04 residual each ~−1.1: e.g. h02
+10.35→+9.21). That is the gas-bound **+44% overnight block** the prior diagnosis
flagged — more available CC (fewer outages) lowers the marginal gas-set price.
The **midday import floor** (h10–14, ~+12.5; PNW_hydro_base-bound) and the
**under-priced evening ramp** (h18–21) are unchanged — orthogonal to outages,
exactly as predicted. So the re-gate is a clean, grounded structural win on the
half of the body that is gas-bound; it does nothing to the import-bound midday or
the evening shape (those need the diurnal import-price lever, below).

**Verdict: adopt as keeper.** Cools the body $0.83 toward actual with the
negative tail, precision and peaks all preserved, grounded purely in the
corrected (net-load-filtered) outage input — no fitting.

> Not yet done: 2025 (and, once OASIS backfills it, 2023) cross-checks are a
> follow-up solve each. 2025 ran even hotter historically, so the same overnight
> cooling should help there too — worth confirming before flipping the default.

---

## TASK 2 — fleet-mix / commitment audit

### The smoking-gun table reproduced (and hypothesis 4 RESOLVED)

`caiso_fleet_mix_validate.py` reproduces the handoff's per-class table **exactly**
against the raw EIA-923 benchmark (2024, OLD-outage keeper, TWh):

| class | model | EIA-923 | Δ923 | EIA-930-scaled | Δ930% |
|---|---|---|---|---|---|
| CC_REGULAR | 51.85 | 45.99 | **+5.86** | 57.47 | −10% |
| CC_CHP | 8.83 | 13.17 | **−4.34** | 16.46 | −46% |
| CT_CHP | 7.05 | 4.72 | +2.33 | 5.89 | +20% |
| CT_PEAKER | 0.16 | 4.33 | **−4.17** | 5.41 | **−97%** |
| ST_GAS | 3.19 | 0.08 | **+3.10** | 0.10 | +3060% |
| GAS TOTAL | 71.07 | 68.28 | **+2.79 (+4%)** | 85.33 | −17% |

**Hypothesis 4 (the unresolved EIA-923=68 vs EIA-930=85 gas gap) is resolved.**
The 17-TWh gap is **not a real gas discrepancy** — it is EIA-930's `NG: NG` (gas)
for CISO **silently absorbing geothermal + biomass**, which EIA-930 reports for no
other fuel category for CISO. The codebase already knows this
(`eia_loader.measured_gas_floor_profile` docstring: *"NG: NG … for CISO silently
absorbs geothermal/biomass … gas generation is still validated against EIA-923,
not this series"*). Quantified from the bundle's own EIA-923:
- EIA-923 `OTHER` (geothermal) 8.08 + `biomass` 4.41 = **12.5 TWh** of the 17.0
  gap; the residual ~4.5 TWh is the preliminary 2024 EIA-923 vintage under-count.

**Consequence — a real CAISO scorecard artifact.** The dashboard's `classFull`
benchmark (`render_calibration_html.py`) scales every gas class **up to the
EIA-930 gas total (85)** whenever EIA-923 < 0.97×EIA-930. For CISO that scale-up
folds the 12.5 TWh of geothermal/biomass into the gas-class benchmark, inflating
each class ~25% and making the per-class gas volume gates fail spuriously ("only
1/8 thermal classes pass"). The **right** CAISO gas benchmark is raw EIA-923, and
against it the model is **+4% total** — a modest, genuine overage. *(Fix not
applied this session — diagnosis-first. The clean fix is to exclude
geothermal/biomass from the EIA-930 gas target for CISO in the vintage-reconcile
scale-up, or skip the scale-up for CISO. Flagged for a follow-up.)*

### Where/when the +4% gas is mis-allocated (the real defect)

The total is ~right vs EIA-923; the **split and the shape** are wrong, and they
are the SAME defect as the evening under-price. Per-hour-of-day (mean MW, OLD
keeper):

- **CC_REGULAR runs near-FLAT ~6000–6500 MW every hour** (overnight ≈ evening).
  It behaves like must-run, not a dispatchable mid-merit unit.
- **CT_PEAKER is ~0 all day** (9 MW even in the evening peak) vs 4.33 TWh real.
- The model's **total gas is flat ~6500–7200 MW** while EIA-930 gas ducks from
  ~8700 overnight up to ~11400 in the evening (h19). Model gas is UNDER EIA-930
  in every hour (−2200 overnight … −5000 at the solar shoulders … −4400 evening).
  ~1600 MW of that under-ness is the geothermal/biomass EIA-930 folds into gas;
  the rest is a genuine **evening under-ramp**.
- **Evening ramp (evening h17–21 minus overnight h00–04) is delivered by
  CC_REGULAR (+81 MW) and ST_GAS (+74 MW); CT_PEAKER contributes +9 MW.** The
  model meets the evening ramp with must-run CC creep + steam instead of the fast
  peakers real CAISO starts — and the model gas ramps only ~+115 MW evening vs
  EIA-930's ~+2500 MW, so the balance is met by (flat) imports/storage. That flat
  evening gas is exactly why the evening LMP is flat ~$49 vs actual $57–66.

### Root cause: a COMMITMENT / merit-order error (hypothesis 1), proven by TASK 1

The outage re-gate is the decisive test. Fewer outages → MORE thermal available.
If the peaker-under were an availability problem, peakers would come online. They
do the **opposite**:

| class | OLD | NEW (fewer outages) | Δ |
|---|---|---|---|
| CC_REGULAR | 51.85 | 53.03 | **+1.18 (more over-run)** |
| CT_PEAKER | 0.16 | 0.03 | **−0.13 (→ ~0)** |
| ST_GAS | 3.19 | 2.76 | −0.43 (better) |
| GAS total | 71.07 | 71.85 | +0.78 (+4%→+5%) |

With more CC available the commitment leans **even harder on CC** and the peaker
all but disappears. So CC-over / peaker-under is a **commitment/merit-order
property, not an availability one.** The RA must-offer gas floor
(`inject_caiso_gas_commitment_floor`, 0.80×EIA-930 `NG: NG` midday) fills the
midday floor **cheapest-first by heat rate** → CC (low HR) absorbs the floor and
stays online → it is already warm for the evening ramp and economically ramps up,
so peakers never start. ST_GAS improving under the re-gate (3.19→2.76) is
consistent: more available CC displaces the must-run steam the floor would
otherwise hold (hypothesis 2 is a secondary, smaller effect).

**This is the headline for the next build:** the mix fix is a commitment/offer
change that lets fast peakers (not CC creep / must-run steam) meet the evening
ramp — which would also RAISE the evening LMP toward $57–66 (improving the shape
and p95-peak), though it nudges the mean back up, so it trades against the body.

### Hypotheses status

- **H1 (CC over / peakers under = commitment/merit-order):** CONFIRMED (the
  re-gate test above; the cheapest-first gas-floor fill mechanism). Primary.
- **H2 (ST_GAS running ~retired steam):** secondary — ST_GAS 3.19 TWh vs EIA-923
  0.08; improves to 2.76 under the re-gate. The gas floor excludes gas_st, so the
  3 TWh is economic/must-run dispatch of near-retired steam, not the floor.
  Worth a COD/retirement-mask check but it is the smaller mass.
- **H3 (CC_CHP under / CT_CHP over = class mapping):** unaddressed; CC_CHP −4.34,
  CT_CHP +2.33 vs EIA-923 looks like an EIA-860 group mis-split (CC_CHP vs
  CT_CHP) — a fleet-mapping check, independent of commitment.
- **H4 (EIA-923 vs EIA-930 gas gap):** RESOLVED above — geothermal/biomass
  absorption + preliminary vintage; EIA-923 is the right benchmark; the +4% is
  real and modest; the EIA-930 scale-up is a scorecard artifact for CISO.

---

## Next levers (grounded, for after this diagnosis)

1. **Commitment/offer fix for the evening ramp (H1)** — let peakers, not CC creep
   / must-run steam, meet h17–21. Improves the peaker volume gate AND raises the
   evening LMP. Mind the body trade-off.
2. **Diurnal import PRICE shape** (now unblocked: OASIS fetch scaffolding exists —
   `scripts/fetch_caiso_oasis.py`, `fetch_caiso_intertie_lmp.py`, and the
   `--caiso-import-hub-prices` flag already wired to
   `data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet`). Prices
   the import tranches on measured Mid-C/Palo-Verde hub shape — the only lever
   that lowers the midday import floor (+60% block) AND lifts the evening without
   the −$20 over-collapse. Keep opt-in; note the forecast proxy.
3. **CISO scorecard scale-up fix (H4)** — exclude geothermal/biomass from the
   EIA-930 gas target so the per-class gas gates score against EIA-923.
4. **OASIS 2023 LMP backfill** — adds 2023 LMP gating (currently fuel-mix only).
