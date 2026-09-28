# FINDING — miso-282 phase 0: the 2021–22 ST_GAS residual is not an in-merit shortfall. No solve earned.

```
LANE    : miso-282 (owner pick on the miso-281 card "2021–22 ST_GAS in-merit gap (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025) — unchanged
TARGET  : C1 ST_GAS 2021 −5.24 / 2022 −5.11 TWh (PASS, band ±8). Not tuned against (rule 1).
LP      : none. Fleet-only rebuilds of the keeper recipe, CEMS hourly, EIA-923, measured hub RT LMP,
          the benchmark EIA-923 frame rebuilt from the keeper bundle's meta.
PROBES  : scripts/probes/_miso282_stgas_fleet.py      per-unit hourly offer / fuel / floor / keeper price
          scripts/probes/_miso282_inmerit_2x2.py      2x2 envelopes {model, hub} price x {model offer, measured cost}
          scripts/probes/_miso282_c1_decomp.py        C1 ST_GAS residual split by population and zone
          scripts/probes/_miso282_standby_delta.py    admit_standby_units fleet delta at keeper prices
OUTPUTS : results/calibration/_miso282_{inmerit_2x2,c1_decomp,standby_delta}.json
```

## 1. Answer

In 2021–22 the South gas steam that the model can dispatch is **not short in merit**. Its in-merit energy
matches measured conduct to within 0.2–0.4 TWh. The residual is three things, none of them 2021–22 specific in kind:

1. **Out-of-merit commitment** above the floors. This is the same object as 2019 (RO-2), and it is present in **every**
   year.
2. **Capacity the fleet does not carry.** Baxter Wilson 1 (545 MW) is EIA-860 `SB` in the 2021 and 2022 vintages,
   so the fleet drops it, while it generated 0.75 / 0.31 TWh.
3. **Non-South plants**, about −0.9 TWh.

What makes 2023–24 look fine is **error cancellation**. In those years the model's South price sits above the
measured hubs in most hours (+$6–9/MWh at night). That lifts in-merit steam 4.6–5.8 TWh above measured, which masks
the same out-of-merit shortfall. In 2021–22 the night premium is still there, but the model also misses the measured
evening peaks, when steam is in merit. The net price effect on steam is therefore about zero, and the shortfall shows.

## 2. Decomposition of C1 ST_GAS (TWh)

C1 = model grid ST_GAS minus benchmark `classFull`. Ninemile 1403 is `OTHER_FOSSIL` on both sides. The three columns
sum to the residual.

| year | C1 resid | no model unit | South | other zones | South: out-of-merit gap | South: in-merit gap | South: price effect |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | −8.00 | −0.58 | −7.50 | −0.53 | −8.11 | +1.13 | +0.94 |
| 2020 | −6.40 | −0.72 | −5.14 | −0.54 | −8.18 | +3.67 | +3.70 |
| **2021** | **−5.24** | **−1.73** | **−2.61** | **−0.90** | −2.27 | **−0.19** | −0.85 |
| **2022** | **−5.11** | **−0.83** | **−3.36** | **−0.92** | −2.24 | **−0.36** | −1.23 |
| 2023 | −0.23 | −0.41 | +0.53 | −0.51 | −2.85 | +4.58 | +4.47 |
| 2024 | −1.90 | −1.05 | +0.02 | −0.96 | −4.70 | +5.80 | +5.56 |
| 2025* | −3.86 | −0.40 | −1.03 | −1.78 | −3.97 | +3.72 | +3.27 |

*2025 is skipped by the rubric (preliminary EIA-923).

Definitions for the three South sub-columns. They use the plant-net EIA-923 basis and hub-covered hours, so they
localize the South term but do not reconcile to it to the MWh.
- **Out-of-merit gap** = model floor − measured energy in hours when the hub was below measured cost.
- **In-merit gap** = model envelope above floor − measured in-merit energy.
- **Price effect** = the envelope at the model price minus the envelope at the hub price, both at the model's own
  offers.

**Reading the table:**
- The in-merit gap tracks the price effect in every year (±1.2 TWh).
- In 2021–22 both are near zero or slightly negative. The model's offers meet about the same hours the hub did.
- On the C1 basis (ex-Ninemile), the out-of-merit gap is −2.2 to −2.8 TWh in 2021–23. This **corrects** miso-281 §4
  (+0.4 / −2.3 / +1.0), which included Ninemile: its 4.7–5.9 TWh floor over-carries its own out-of-merit energy and
  hid the rest.

## 3. Candidate causes tested

| cause | test | verdict |
|---|---|---|
| Gas price / basis in the $3.9 / $6.4 gas years | model plant delivered gas vs EIA N3045 delivered-to-electric-power (LA/MS/AR) | **No.** 2022: model $6.2–7.5, LA $6.72, MS $6.22, AR $6.59. 2021 LA/MS are withheld; model $3.8–4.4 vs HH $3.91. |
| `gas_offer_net_revenue_margin` anchor per year | 2021 / 2022 anchors 4.02 / 6.59 = own-year HH mean | **No.** The econ offer equals 1.0 × HR × gas at the anchor in every year. The offer-side envelope loss (model offer vs measured cost) is −1.3 to −3.1 TWh in **every** year and is smaller in 2021–22 (−1.8 / −1.5) than in 2019–20 or 2023. |
| Model HR vs CEMS | measured net HR (CEMS heat input / net) | Model 11.6–12.3 vs CEMS 10.3–11.0 at Sabine / Lewis Creek / Ninemile, in all years. Noted as a standing observation, not specific to 2021–22. The comparison is marginal offer vs average cost, so it is not a clean defect signal. |
| Dual-fuel oil cap / reattribution | benchmark vs raw EIA-923 ST-NG per plant | Small: +0.36 / +0.20 TWh at plant 1743 (East) in 2021 / 22. |
| Relative merit vs CC / coal and model price vs hubs | 2x2 envelopes; price differences by hour | **This is the year pattern.** Model − LA hub annual: +3.4, +4.2, +2.0, −0.2, +4.3, +3.8, +1.3. Night hours (h0–5) run +5 to +13 in every year. In 2021–22 the model misses the measured evening peaks (2022 h15–18: −10 to −14; 2021 h16–21: −2 to −6), which is exactly when steam is in merit. These are price-formation misses, already the C3b 2021 / C3a 2022 routed objects. |
| Fleet membership | benchmark ST_GAS at plants with no model ST_GAS unit | −1.73 / −0.83 TWh in 2021 / 22, of which Baxter Wilson 2050 is −0.75 / −0.31 (EIA-860 `SB` in the 2021–22 vintages, retired 3/2023). |

## 4. The one structural lever found: `admit_standby_units` (MISO cell `U`)

This is the existing ISO-agnostic, zero-DOF mechanism (NWPP-NEXT-5; NWPP keeper). It admits EIA-860 `SB` units by
status alone and is rule-13 admissible. Zero-LP fleet delta at the keeper's own prices:

| year | +MW | +envelope TWh | ST_GAS | COAL_PRB (Taconite Harbor 10075) | CC_CHP (10745) | CT_PEAKER |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 1,594 | 2.20 | 0.00 | 0.90 (0.66) | 1.08 | 0.13 |
| 2020 | 1,588 | 2.11 | −0.01 | 0.80 (0.57) | 1.13 | 0.10 |
| 2021 | 2,038 | 2.38 | **0.38** | 1.14 (0.90) | 0.73 | 0.11 |
| 2022 | 2,006 | 2.06 | **0.08** | 1.01 (1.01) | 0.86 | 0.10 |
| 2023 | 1,494 | 1.87 | 0.45 | 0.00 | 1.22 | 0.16 |
| 2024 | 1,446 | 2.06 | 0.48 | 0.00 | 1.37 | 0.14 |
| 2025 | 1,246 | 1.67 | 0.37 | 0.00 | 1.25 | 0.03 |

(Another ~770–870 MW of `SB` oil / IC units each year add ~0 TWh.)

**What it would and would not do:**
- **It barely reaches this lane.** ST_GAS rises by at most 0.38 / 0.08 TWh against −5.2 / −5.1 TWh.
- **It carries a known structural cost in MISO.** Taconite Harbor 10075 (2 × 84 MW) has been economically idled since
  2016: EIA-923 shows 0 MWh and CEMS shows zero load in every hour of 2021. Admitted as ordinary available capacity,
  it would run 0.6–1.0 TWh/yr of phantom coal in 2019–22, into a COAL_PRB class that already reads +4.5 / +4.7 TWh.
- **The outage extracts do not cover it.** They were derived on the OP population, and none of the three MISO
  extracts has a row for 10075.
- A faithful MISO arm therefore also needs its outage / layup extract re-derived on the admitted population. That is
  the SPP-99 companion pattern, and it is a build, not a flag flip.

**Verdict: no solve earned in this session.** The cell stays `U`, with this sizing recorded.

## 5. Routing

- **Out-of-merit South steam, every year:** `scuc_load_pocket_commitment` (`·`, RO-2). The sizing is now corrected to
  the C1 basis: −8.1 / −8.2 / −2.3 / −2.2 / −2.8 / −4.7 / −4.0 TWh for 2019–2025.
- **Model South price premium over the measured hubs** (night +$5–13, all years): a price-formation object. It
  inflates in-merit steam in 2019–20 and 2023–25 and masks the out-of-merit shortfall there. It has no matrix cell
  yet; it is proposed as the next MISO zero-LP lane.
- **`SB` capacity** (Baxter Wilson 2021–22; the Taconite Harbor idle-unit trap): `admit_standby_units` plus an
  outage-extract companion on the admitted population. This is a build lane if the owner wants it.
- **Rubric:** unchanged. C1 ST_GAS 2021–22 PASS. The full span stays NOT-YET on the three owner-ruled routed misses.
  **No frontier.**

## 6. Owner ruling (2026-09-28)

Next lane: **"South price premium probe (Recommended)"**. This is a zero-LP phase 0 on two things:
- why the model's MISO-South price sits above the measured LA / MS / AR hubs at night (+$5–13/MWh, every year);
- why it misses the measured evening peaks in 2021–22.

No solve this session. No frontier, because the full span still fails on the three routed misses.

