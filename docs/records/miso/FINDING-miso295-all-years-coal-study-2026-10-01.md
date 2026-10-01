# FINDING — miso-295: all-years MISO coal study. The flat offset is an EIA-930 reporting artifact; real conservation happened only in 2021–22, and no admissible coal row can place it. No solve.

```
LANE    : miso-295 (owner ruling 2026-10-01, miso-294 card: "Do a coal study on all years not just 2021")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none
PROBE   : scripts/probes/_miso295_coal_study.py  (blocks A-E; ~70 s)
OUTPUT  : results/calibration/_miso295_coal_study.json
REUSED  : results/calibration/_miso288_coal_scarcity.json (dark units, unit ceiling ratio, 2019-2024)
SOURCES : Potomac Economics, MISO State of the Market Reports 2020-2024 (report bodies) and the 2019 appendix;
          IMM Quarterly Reports Summer 2025 and Fall 2025. Fetched from potomaceconomics.com; cited, not
          committed, and not a model input. Page numbers are PDF pages.
CELLS   : coal_fuel_inventory K (note added); no verdict moves; no R/I/G cell re-tested (rule 28)
```

## 1. Answer

1. **The flat annual coal offset (+6 to +13 TWh) is not overburn.** It comes from EIA-930. MISO's EIA-930 coal sits
   below EIA-923 net generation of the model-fleet coal plants **in every month of every year**. Against the
   plant-matched EIA-923, the keeper's annual coal error is −2.1 / +0.7 / **+5.3 / +10.3** / −3.4 / −3.3 / −1.6
   TWh for 2019–2025.
2. **Real conservation happened in 2021–22 only.** The IMM documents it from fall 2021 through 2022. The stock
   record agrees: those are the only years in which the pile fell to ~58–61 days on hand **after a summer draw**,
   and the only years with the summer-under / fall-over model signature.
3. **How it was expressed (2021):** the fleet burned hard through summer (Jun–Aug burn exceeded receipts by
   10.3 Mt). It then held the pile flat through the fall instead of rebuilding it, by taking units **offline**,
   not by derating them or running them at lower load. Fall deliveries ran at the prior-years rate, so the trigger
   was the pile level reached after summer, not a delivery shortfall.
4. **The `coal_fuel_inventory` family cannot carry this with admissible inputs.**
   - The keeper's flat `B/12` limb binds in **summer** 2021, when the real fleet did not conserve, and is slack in
     the fall, when it did.
   - A row that binds only in the fall needs the solve year's own post-summer stock level. Rule 13 forbids that
     input.
   - The endogenous alternative is a cumulative pile, which is a perfect-foresight bank. That family has been killed
     four times (miso-287 to miso-290).
   - The real behaviour was also precautionary: the pile was held ~12 days **above** the prior-years minimum that an
     admissible floor would use.
5. **The low-end overshoot (C3a 2020) is not a coal-inventory object.** It is present in the glut years: 2019,
   2020, 2023 and 2024, with 61–138 days on hand and no IMM-noted conservation. In those years keeper coal tracks
   EIA-923 within 1.8 TWh/month, and miso-287 measured the budget dual at ≤ $0.94 of the night residual.

## 2. The flat offset is EIA-930 reporting (block A)

Coal TWh, model-fleet plants (bench per-plant EIA-923 `e_mon`, groups `COAL_*`):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| keeper P1 | 252.4 | 202.0 | 255.4 | 234.5 | 181.5 | 175.6 | 202.1 |
| EIA-923, model-fleet plants | 254.5 | 201.3 | 250.1 | 224.2 | 184.9 | 178.9 | 203.7 |
| EIA-930 MISO (adjusted) | 238.9 | 192.1 | 239.1 | 217.1 | 175.0 | 167.5 | 192.1 |
| **model − EIA-923** | **−2.1** | **+0.7** | **+5.3** | **+10.3** | **−3.4** | **−3.3** | **−1.6** |
| EIA-930 − EIA-923 | −15.6 | −9.2 | −11.0 | −7.1 | −9.9 | −11.4 | −11.6 |

- Monthly, EIA-930 − EIA-923 runs −0.0 to −1.6 TWh in all 84 months, with no seasonal shape.
- The difference is between two EIA series on two boundaries: a BA-reported hourly series and plant-reported
  annual filings. Its composition is not identified here. It is not a model property.
- The miso-294 Part B "flat +6 to +13 TWh" offset was measured against EIA-930. On the plant-matched basis it
  vanishes outside 2021–22.
- The scored C1 benchmark is already plant-level (bench `classFull`), so no score moves.

Model − EIA-923 coal, TWh by month:

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | −0.9 | −1.8 | −0.2 | +0.1 | +0.2 | +0.2 | −0.1 | +0.4 | −0.1 | +0.6 | −0.1 | −0.3 |
| 2020 | +0.3 | +0.7 | +0.2 | +1.0 | +1.5 | +0.8 | −0.3 | −0.2 | −0.7 | −0.6 | −0.4 | −1.4 |
| **2021** | −0.1 | +0.2 | −0.2 | +0.4 | +0.5 | +1.1 | **−3.3** | **−3.9** | **+1.7** | **+3.6** | **+3.3** | **+2.1** |
| **2022** | −2.1 | +0.6 | +1.7 | +1.6 | +3.3 | +1.4 | **−3.3** | **−2.2** | **+3.0** | **+3.0** | **+2.5** | +0.7 |
| 2023 | −0.5 | −0.2 | −0.2 | −0.2 | +0.6 | +0.8 | −0.2 | −0.2 | −0.5 | −0.7 | −1.0 | −1.2 |
| 2024 | −1.0 | +0.0 | −0.0 | −0.3 | −0.4 | −0.1 | +0.2 | +0.1 | +0.1 | −0.1 | −0.3 | −1.6 |
| 2025 | −1.7 | −0.6 | +0.0 | +0.1 | +0.3 | +0.5 | −1.5 | +0.6 | +0.3 | +0.3 | −0.4 | +0.4 |

## 3. Year by year: the real fleet (blocks C and D, IMM)

The pile is measured on the model-fleet coal plants (EIA-923 Sch. 2 stocks and Page 5 receipts). "Prior rate" is
the keeper budget's receipts rate (mean Y−2..Y−1). "Budget/burn" = (Dec Y−1 stock + prior rate) / actual burn,
i.e. the keeper's annual identity divided by what the fleet actually burned.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| opening stock, days on hand | 71.7 | 107.3 | 104.5 | 71.5 | 87.4 | 128.8 | n/a |
| minimum month-end days (month) | 60.8 (Mar) | 111.7 (Jan) | **57.6 (Sep)** | **61.1 (Aug)** | 88.2 (Jan) | 116.0 (Sep) | n/a |
| receipts − prior rate (Mt) | −17.4 | −31.3 | −8.5 | +6.5 | −4.0 | −20.0 | n/a |
| budget / burn | 1.36 | 1.62 | 1.24 | 1.15 | 1.38 | 1.52 | n/a |
| Jun–Aug burn − receipts (Mt) | −0.1 | +6.3 | **+10.3** | +4.6 | +2.9 | +3.4 | n/a |
| Sep–Nov burn − receipts (Mt) | −3.8 | −3.6 | **−0.4** | −5.5 | −3.1 | −0.7 | n/a |
| IMM on coal conservation | none | none | from fall 2021 | most of 2022 | resolved spring 2023 | none | none |
| model seasonal swing | no | no | **yes** | **yes** | no | no | no |

- **2019.** The pile touched 61 days in March after the January 2019 cold, then rebuilt on receipts. No summer draw
  and no fall hold. The 2019 appendix carries no coal-conservation text (a body URL was not found; the appendix
  was searched).
- **2020 / 2023 / 2024.** Glut years: 88–138 days on hand all year. Receipts fell below the prior rate by up to
  31 Mt with no conservation, because stocks absorbed it. The IMM is silent on conservation (2020) or says supply
  issues had resolved (2023 SOM p.27, p.113; 2024 SOM p.71: *"By late 2023, coal supply constraints had fully
  eased"*).
- **2021.** IMM (2021 SOM p.21 and p.82): higher output *"throughout the summer of 2021 until fuel limitations and
  other supply chain issues compelled many coal resources to begin conserving coal and running less"*, with
  reference levels set in IMM consultation. p.35: conservation is among the non-fuel drivers of the 2021 price
  rise.
- **2022.** IMM (2022 SOM p.18, p.32, p.79 Fig. 26): conservation *"in late 2021 that persisted through most of
  2022"*, easing from fall 2022, on ~11–22 GW (miso-288). 2023 SOM p.113 gives the purpose: *"to ensure that they
  would have sufficient fuel inventory going into the winter months"*.
- **2025.** No plant-level coal-stocks file exists yet (the EIA-923 2025 release carries no `Page 2 Coal Stocks
  Data`; see `data/raw/coal-stocks/README.md`). The Summer and Fall 2025 IMM quarterlies mention no coal
  conservation. The model shows no swing.

**2021, what the units did (CAMPD gross, coal units at model-fleet plants):**

| | online GW Aug → Nov | Δ | loading-when-on, Nov |
|---|---|---:|---:|
| 2019 | 48.4 → 40.3 | −8.1 | 0.76 |
| 2020 | 46.4 → 33.0 | −13.4 | 0.74 |
| **2021** | 50.0 → 31.5 | **−18.5** | 0.74 |
| 2022 | 43.8 → 32.1 | −11.7 | 0.72 |
| 2023 | 39.6 → 30.8 | −8.8 | 0.70 |
| 2024 | 38.7 → 27.7 | −11.0 | 0.70 |

- The 2021 fall cut came from units **offline**. Loading-when-on stayed normal.
- miso-288's derate signature is absent: dark units in Oct/Nov 2021 were 21/27 against 20/26 in 2019, and the unit
  ceiling ratio was 0.94/0.90.
- CAMPD cannot separate an economic decommitment from an outage. The IMM's account (an opportunity-cost reference
  adder makes the unit uneconomic) is consistent with the data.

**The fall 2021 hold was not a delivery shortfall.** Receipts were 11.3 / 10.6 / 10.7 Mt in Sep–Nov against the
keeper's prior-years rate of 11.1 Mt/month. The pile was low because summer burn ran 10.3 Mt over receipts. The
fleet then burned about what it received (Sep–Nov net −0.4 Mt) instead of the usual 3–6 Mt fall rebuild.

**The gas mirror.** Model gas sits 1–3 TWh/month below plant-matched EIA-923 in every year (a baseline not
investigated here). In Sep–Nov 2021 the gap widens to −4.5 / −6.8 / −6.2 TWh. The coal excess (+1.7 / +3.6 / +3.3)
matches roughly half to two-thirds of the widening. Model − actual zone-resolved price in 2021, $/MWh (monthly mean / night h0–5 mean):

| | Jul | Aug | Sep | Oct | Nov |
|---|---:|---:|---:|---:|---:|
| all hours | +3.2 | +4.1 | −7.9 | **−14.9** | −11.3 |
| night | +8.4 | +9.6 | −1.9 | −10.2 | −8.9 |

## 4. Can the `coal_fuel_inventory` family carry it?

**No, not with admissible inputs.** Every part of this argument is measured; no R/I/G cell was re-tested.

1. **The keeper puts the rent in the wrong months.**
   - The pooled flat `B/12` limb holds keeper 2021 coal flat at 24.0–24.5 TWh from Jun to Sep (miso-287 §3), while
     the real fleet ran over that level in Jul/Aug (model −3.3 / −3.9 TWh vs EIA-923).
   - From Sep to Dec the limb is slack, because fall burn sat well under the cap.
   - 2022 is the same, with the cap binding May–Sep (miso-288).
2. **The annual identity never binds on the real burn.** Budget/burn is 1.15–1.62 in every year. A fleet-wide
   annual row cannot produce the fall hold.
3. **A row that binds only in the fall needs the post-summer pile level.**
   - That level is the solve year's own stock path, which embeds the burn. Rule 13 refuses it
     (`ScenarioConfig.coal_fuel_inventory` comment; NEISO precedent).
   - Same-year receipts (NWPP-NEXT-9) would not help either: 2021 fall receipts were at the prior rate.
4. **The endogenous route is the cumulative pile, which is a perfect-foresight bank.** A binding fall row prices
   every earlier hour equally and starves winter (miso-289 §4: Jan–Apr 13 TWh under bench; miso-290 §5). That
   family is closed.
5. **Even the level is not identifiable from prior years.**
   - miso-289's admissible floor for 2021 is a MW-weighted d_min of 46.1 days.
   - The real fleet stopped at 57.6 days, ~11.5 days (≈ 4.4 Mt at 2021's burn rate) above it.
   - A floor at d_min would let the LP burn that coal. Holding the pile above it is a **precautionary** choice made
     under delivery uncertainty (the IMM cites rail and reagent limits), which a deterministic year-LP does not have.

So the 2021–22 behaviour is a **sequential decision under uncertainty**: information arrived mid-year, and the fleet
reacted to its own realized pile. The family can carry quantity; it cannot carry that timing. This is the same
structural limit miso-290 named, now shown to be the one that binds in **both** years where conservation occurred
and absent in the five where it did not.

## 5. Relation to the low-end overshoot (C3a 2020)

- Keeper − actual night (h0–5) price is positive in every month of 2019, 2020, 2023 and 2024, at +0.9 to +8.8
  $/MWh (2020: +3.1 to +6.6).
- These are the glut years, with no conservation. The keeper's coal tracks EIA-923 within 1.8 TWh/month, and the
  budget dual contributes +$0.27 to +$0.94 of the night residual (miso-287 §2).
- The overshoot therefore sits in the **offer stack at low load**: miso-287 measures the P0 stack $3.2–6.5 above
  the hub at night (2019 / 2020 / 2023 / 2024). It is not coal inventory.
- 2022 (summer nights +11.8 to +16.8) and 2025 (+1.93 budget residual, Jul night +12.6) are where the budget dual
  does contribute. Both are already recorded (miso-287).

## 6. Side check: 2022 RT coverage (no defect)

- The zonal hub archive's 2022 RT stops at hour 7559 (2022-11-11). The raw corpus is 315/365 days, and
  `data/raw/lmp-data/MISO/README.md` documents this ("2022 staging is INCOMPLETE").
- Committed `rt_lw_mon` therefore reads Nov $35.5 and Dec $22.1 (one hour).
- **The scorer masks it:** `calibration_verdict.py` reads `rt_cov` (Nov 0.365, Dec 0.0013) and restricts both
  sides of C3a/C3b to the ten fully staged months (lines 2382–2428).
- The miso-294 scores stand. In this probe, the 2022 Nov/Dec price rows are partial or empty and are not quoted.

## 7. What follows

- **No admissible mechanism follows**, so no PRECOMMIT is written. The coal budget-grain line stays CLOSED.
- **C3b 2021 is unchanged:** 0.201 against the 0.20 cap.
  - Its Feb component is Uri (routed).
  - Its Sep–Nov component is now measured as IMM-documented precautionary conservation that a deterministic LP
    cannot represent with forward-regenerable inputs.
  - It is still a failure (owner, 2026-09-28: routed misses are failures).
- **The live structural object is C3a 2020:** the low-load offer stack, present in every year.
- **Where MISO stands.** Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span **NOT-YET** on C1
  ST_GAS 2019 (routed), C3a 2020 (+11.6 %) and C3b 2021 (0.201). **No frontier.**

## Retrievability

No solve. The probe, its JSON output and this record are all in this PR.
