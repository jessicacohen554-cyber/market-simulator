# NEISO: the index-vs-delivered gap is SETTLED — the Algonquin index is right

**Session:** `neiso-fuelvintage-1`, 2026-09-09. **Zero LP.** **Scope: NEISO only.**
**Closes:** the named open question of
`docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §6a
("a discrepancy this session did NOT resolve, stated not absorbed").

## 0. Bottom line

For January 2023 two measured gas series disagree by 3.2x: the ISO-NE published
Algonquin Citygate index reads **$4.73/MMBtu** and the EIA `N3045` MA/CT/RI/NH/ME
delivered-to-electric-power blend reads **$15.35/MMBtu**. Four independent tests,
all zero-LP:

| # | test | result |
|---|---|---|
| 1 | Is `$15.34` a **small-denominator artifact**? | **NO — REFUTED.** The `N3045` volume series is 98.4 % of the CAMPD-metered burn. |
| 2 | Is the **index** right? | **YES.** Corroborated by an independent commercial print (NGI daily AGT). |
| 3 | What does the **market** say? | **The index.** The delivered series implies a physically impossible market heat rate in 7 of 35 months. |
| 4 | Does the model have a level gap? | **NO.** The keeper reproduces the published index in **73 of 84 months exactly**; the "2.303 $/MMBtu gap" is a reference-choice artifact. |

**Both series are real measurements of different quantities.** `N3045` is the
plants' own **average delivered cost including all transportation charges**;
the AGT index is the **marginal commodity price**. A merit-order offer prices the
marginal, never the average. Rule 14 `[R-ACCURATE]`'s misalignment exception is
invoked explicitly and is now *evidenced* rather than asserted.

**Operational consequences:** `gas_electric_power_monthly_level` stays **OFF** for
NEISO — proven **exactly inert** (§7). The planned SHARD F ordering-check solve is
**cancelled as unnecessary** (§7). A NEISO copy of the ercot-261 corroborator is
**recommended against**, on measurement (§8).

## 1. What each series measures

- **`isone_ma_gas_index_monthly.csv`** — ISO-NE's own published monthly average
  natural-gas price for New England (Algonquin Citygate), from the ISO-NE monthly
  wholesale-market recaps. This is the series NEISO's keeper prices gas on, through
  `gas_hub_basis_overlay`.
- **`N3045<ST>3`** — EIA's monthly price of natural gas sold to electric power
  consumers. Per EIA's own series definition page
  (`https://www.eia.gov/dnav/ng/TblDefs/ng_pri_sum_tbldef2.asp`), the electric-power
  price for **2007-current is collected on Form EIA-923, "Power Plant Operations
  Report"** — i.e. it is the **plants' reported delivered fuel cost**, which EIA-923
  Schedule 2 defines to include all costs of purchasing *and delivering* the fuel to
  the plant. (The *city gate* series `N3050` comes from a different survey —
  EIA-857/EIA-910 — and is not comparable in level.)

## 2. Test 1 — the small-denominator hypothesis is REFUTED

The companion **volume** series `N3045<ST>2` ("Natural Gas Deliveries to Electric
Power Consumers", MMcf) was fetched for all five New England states and converted at
EIA's 1.036 MMBtu/Mcf, then divided by EIA-930 `ISNE` NG generation:

| year | implied fleet heat rate from the N3045 volume, MMBtu/MWh |
|---|---|
| 2022 | 7.33 – 7.63 (12/12 months) |
| 2023 | 7.40 – 7.64 (12/12 months) |
| 2024 | 7.39 – 7.65 (12/12 months) |

Every month of 2022-2024 lands inside a 0.32 MMBtu/MWh band centred on a physically
correct New England gas-fleet heat rate. **January 2023 reads 7.398 — the median.**

Cross-checked against an independent *metered* instrument: **CAMPD** unit-level gas
heat input for the five states, January 2023 = **29,290,427 MMBtu**, against the
N3045 delivered volume of 28,728 MMcf = **29,762,208 MMBtu** — agreement to
**1.6 %**.

**The denominator is the whole fleet's burn.** `$15.35/MMBtu` is the
volume-weighted average delivered cost of essentially *all* the gas New England's
power fleet burned that month. It is not an artifact and it is not thin.

## 3. Test 2 — the index is independently corroborated

`data/raw/gas-prices/algonquin_citygate_daily.csv` (NGI's Daily Gas Price Index, via
EIA's Natural Gas Weekly Update — a *commercial* index, a different publisher from
ISO-NE) prints for January 2023: **4.04, 3.38, 3.24, 4.23, 3.22**, with the month's
high at **13.49 on 01-31** as the early-February Arctic outbreak priced in (02-02
reads 28.36). A month sitting in the **$3.2-4.2** range with one end-of-month spike
averages to ISO-NE's published **$4.73**. **Two independent publishers agree.**

## 4. Test 3 — the market's own verdict, and it is not close

Implied market heat rate = (NEISO RT LMP monthly average) / (candidate gas price).
Actuals from `frontend/data/backcast/bench/NEISO/<year>.json.gz`.

| | AGT index | EIA delivered |
|---|---|---|
| median implied market heat rate | 11.69 | 9.55 |
| **months below 6.3 MMBtu/MWh** (the best CC in the fleet — a *physical floor*) | **0 / 35** | **7 / 35** |
| minimum | 7.39 | **3.29** (2023-01) |

A monthly average LMP cannot sit below the marginal unit's own fuel cost for a whole
month. On the delivered series, **January 2023 implies 3.29 MMBtu/MWh — roughly half
the physical heat rate of the most efficient machine in New England.** The other six
impossible months are 2022-02, 2022-12, 2023-02, 2023-03, 2023-12, 2024-01 — all
winter. On the index, **no month in three years is even close to the floor.**

**The same thing in dollars, January 2023:**

| | fuel bill | energy revenue | gross margin |
|---|---|---|---|
| AGT index $4.73 | $138.5 M | $203.2 M | **+$64.6 M** |
| EIA delivered $15.35 | $449.6 M | $203.2 M | **−$246.4 M** |

(29,290,427 MMBtu of CAMPD-metered burn; 4,023 GWh of EIA-930 `ISNE` NG generation
sold at the $50.51/MWh RT average.) New England's gas fleet is essentially all
merchant, with no per-MWh cost recovery. **A $246 M one-month loss did not happen.**

## 5. What the wedge actually is

The wedge (delivered − index) is **winter-concentrated**, which is the signature of
an *average total cost* rather than a *marginal commodity cost*:

- **DJF mean +3.80 $/MMBtu, max +10.62** (2023-01)
- **all other months mean +0.83 $/MMBtu**

EIA-923 Schedule 2's delivered cost includes transportation. In the most
transport-constrained gas market in the country, a generator's winter delivered cost
carries firm-capacity reservation charges, LNG and peaking supply — **fixed and
pre-committed costs that are sunk at the moment of offer.** The marginal cost of the
next MMBtu is what the plant can buy (or resell) it for at the citygate, which is the
index. That the wedge nearly vanishes in summer, when the constraint does not bind,
is the confirming asymmetry.

Sign check against a market where capacity is ample: PJM's delivered series sits
**below** its hub (the xiso FINDING §3 table, 2023: model 3.255 vs measured 2.485).
The wedge is a constraint premium, not an accounting constant.

**Stated at the gate, not absorbed:** this section explains the wedge's *shape* and
*direction*. It is not a full decomposition into transport / LNG / pre-purchase
components; wedge x volume is not constant month to month, so it is not a single flat
demand charge. Tests 1-4 do not depend on the decomposition — they establish which
series the offer follows, which is the question the model has to answer.

## 6. NEISO has no gas level gap. The 2.303 was the wrong reference.

The xiso FINDING §3 table scores each ISO's model gas series against `N3045` and
records NEISO 2023 as **+2.303 $/MMBtu, the largest level gap in the cross-ISO
table.** Scored against the series the keeper is actually (and correctly) built on:

- Model annual 2023 **2.9365** vs the published index's 2.9725 simple monthly mean —
  the residual difference is month-length weighting, not level.
- Month by month, 2019-2025 (84 months, index published in all 84):
  **73 exact matches (≤ $0.005), 11 within a few cents (max $0.23, 2024-11).**

**The keeper's NEISO gas price *is* the ISO-NE published index.** The 2.303 measures
the index-vs-delivered wedge of §5, not a model defect. The cross-ISO table's NEISO
rows should be read that way.

## 7. The fuel seam is EXACTLY inert for NEISO — proven, no LP spent

`ScenarioConfig.gas_electric_power_monthly_level` A/B on the keeper's own config
(`results/calibration/neiso106_offerlevel/run_config.json`), differencing the ISO gas
series:

```
2019..2025:  max |arm - base| on _gas_series  =  0.000000000 $/MMBtu   (all seven years)
```

Both of the flag's call sites are covered:

1. `trajectories.py::_electric_power_level_series` (the coal-sigmoid reference) — the
   A/B above, exactly zero.
2. `resolve.py:152` (the gas units' own price) — the seam's write is superseded by
   `apply_hub_basis_overlay`, which for NEISO covers **12/12 months in every year
   2019-2025** and, measured in the live solve log, repriced **463 of 463 gas
   generators in 12/12 months** (2023) and 444/444 (2020).

ADDITION 3's census, from the same solve: only **14 of 463** gas generators are
priced from their own F923 print in 2023 (24 of 444 in 2020) — and all 463 are
overwritten by the hub overlay afterwards. So the arm is inert for **two
independent** reasons.

**Pre-registered prediction "C3b unchanged to three decimals" is discharged by the
stronger claim: the fuel input array is bit-identical, so every criterion is.**
**SHARD F (the one-year ordering-check solve) is cancelled as unnecessary** — an LP
cannot add information to an exact-zero input delta.

## 8. The ercot-261 corroborator does NOT transfer to NEISO — recommend against

ercot-261 corroborates the `N3045TX3` survey print against **EIA-923 Schedule-5
quantity-weighted TX plant receipts** — same population, same estimator, a different
instrument. That instrument does not exist in New England. Public EIA-923 monthly
gas receipts, 2023:

| state | plants reporting | quantity |
|---|---|---|
| TX | 37 | 511,302,928 |
| MS / GA / LA / NC (regulated, vertically integrated) | 19 / 14 / 18 / 14 | 359-402 M each |
| **MA** | **2** | **318,247** |
| **CT, RI, NH, ME, VT** | **0** | **none** |

The two MA reporters are **`1660` Potter Station 2** (Town of Braintree, a municipal
utility) and **`6081` Stony Brook** (Massachusetts Municipal Wholesale Electric Co) —
both publicly owned, which is why their costs are not confidential. In January 2023
the entire public New England sample is plant `1660` at $15.172/MMBtu on 28,703 units
— and CAMPD records **zero heat input** for that plant that month, so the receipt is
an inventory purchase, not a burn. The sample is ~0.1 % of the fleet's gas.

`hubs.py` already records the reason in code ("*deliberate for NEISO, where only two
plants report*"); this section supplies the measurement behind it. **A NEISO
corroborator would test a complete series against a 0.1 % sample. Do not build one.**

## 9. Governance

- **Rule 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`.** Nothing was rescaled, offset or
  tuned. The conclusion is a *choice between two measured series*, decided on
  structure (marginal vs average cost) and corroborated by four independent tests,
  none of which is the target residual. The market-clearing test (§4) uses actual
  LMPs as a **physical-consistency check on an input**, not as a fit target: it asks
  whether a candidate fuel price is arithmetically possible, and no model output
  enters it.
- **Rule 1 `[R-STRUCT]`.** No mechanism was selected by whether it improved a
  residual. The seam is refused because it is **exactly inert**, not because it
  scored badly.
- **Rule 21 `[R-DOF]`.** Free parameters introduced: **zero**.
- **Rule 29 `[R-SCREEN]` clause (0).** The zero-LP phase-0 gate killed the arm before
  a solve, which is the clause working as designed.
- **Rule 22 `[R-HOLDOUT]`.** No year was solved, scored or registered by this
  document. Every series read here is an input.

## 10. Data added

`N3045<ST>2` volume workbooks for MA/CT/RI/NH/ME (and `N3050MA3`, `N3035MA3` for the
§1 definition check) were fetched from EIA's key-free dnav history workbooks
(`https://www.eia.gov/dnav/ng/hist_xls/<series>m.xls`, the SPP-11 route) and used
**read-only, in this analysis only**. They are not committed and no consumer reads
them: nothing in the solve path changed.
