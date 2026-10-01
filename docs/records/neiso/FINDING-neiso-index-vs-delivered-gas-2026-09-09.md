# FINDING — NEISO's 3.2× index-vs-delivered gas gap is a **measurement-basis gap**, not a level defect in the keeper

**Session:** `neiso-fuelvintage-1`, 2026-09-09. **ZERO LP** — four measured series read against each other.
**Verdict: the ISO-NE published Algonquin Citygate index is RIGHT and the keeper keeps it.**
`$15.35/MMBtu` is **not** the New England marginal generator's January-2023 gas cost, and no change to
NEISO's fuel recipe is warranted. It is the fleet's **average delivered cost including transportation
and contract (LNG) charges**; the index is the **marginal commodity price**, which is what a
merit-order offer is built on.

> **⚠ CORRECTION, made in this session before publication.** An earlier draft of this finding
> called the gap a *respondent-composition artifact* — i.e. that N3045's price is computed over a
> thin, unrepresentative panel. **That mechanism is WRONG and is withdrawn**; see §3c. The parallel
> session `neiso-107` measured EIA's **companion volume series** `N3045<ST>2` and found New England's
> delivered-gas volume matches the CAMPD-metered burn to 1.6 %, so N3045's denominator is
> substantially the whole fleet's burn. Their metered leg reproduces **exactly** in this session
> (29,290,427 MMBtu, to the MMBtu — §3c), so the refutation is accepted. **The verdict is unchanged
> and every other line of evidence stands**; what changes is *why* the two series differ. Rule 14 `[R-ACCURATE]`'s misalignment exception is not merely
*invoked* here (as `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §6a did) — it is
**earned, by a physical falsification**.

**Routed from:** `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §6a ("stated, not proven …
a 3.2× gap between two measured series for one quantity is not a closed question"). Closed here.

---

## 1. The question

For NEISO January 2023 two **measured** sources disagree by 3.24×:

| source | Jan-2023 | what it is |
|---|---|---|
| ISO-NE published Algonquin Citygate index (`isone_ma_gas_index_monthly.csv`) | HH 3.273 + basis 1.457 = **$4.73/MMBtu** | the day-ahead spot index ISO-NE itself publishes in its monthly recap |
| EIA `N3045<ST>3` MA/CT/RI/ME/NH blend, capacity-weighted | **$15.35/MMBtu** | "Natural Gas Price Sold to Electric Power Consumers", $/Mcf ÷ 1.036 |

The keeper (`neiso106_offerlevel`) prices gas off the **index**, which is why its 2023 gas series sits
**2.303 $/MMBtu below** the N3045 blend — the largest annual level gap in the whole cross-ISO table.
The open question the parent session routed here: *is $15.34 the marginal generator's January gas cost,
or an artifact?*

**Answer: neither series is wrong. They measure different quantities, and only one of them sets the offer.**

## 2. THE FALSIFICATION — the implied marginal heat rate is thermodynamically impossible

The decisive test needs no judgement about which survey is "better". Divide the month's realised
wholesale price by the candidate gas price; the quotient is the **implied marginal heat rate** the
market would have had to be setting price on. NEISO's most efficient CC is ~6.3 MMBtu/MWh; the best
machine in the world is ~5.6 HHV. **Anything below ~6.3 is not a modelling disagreement, it is a
violation of the second law.**

Monthly mean RT LMP at the ISO-NE hub (`data/raw/lmp-data/NEISO/<year>_smd_hourly.xlsx`, sheet
`ISO NE CA`, column `RT_LMP`), 2019-01 … 2025-12, **84 months**:

| gas series | median implied HR | p05 | p95 | **months below 6.3** | months below 4.0 |
|---|---|---|---|---|---|
| **ISO-NE AGT index** | 11.13 | **7.99** | 19.22 | **0 / 84** | **0** |
| **EIA N3045 blend** | 9.36 | **5.27** | 15.81 | **13 / 84** | **1** |

**January 2023 is the extreme case and it is not close:**

```
RT LMP  = $50.51/MWh
÷ index   $4.73/MMBtu  ->  10.68 MMBtu/MWh   plausible NE marginal HR (CC+CT mix, AS, congestion)
÷ N3045  $15.35/MMBtu  ->   3.29 MMBtu/MWh   IMPOSSIBLE (a ~104%-efficient heat engine)
```

The index never once, in seven years, implies a marginal heat rate a real machine could not deliver.
The N3045 blend does so in **13 of 84 months**. That asymmetry is the finding.

Log-price correlation against the same 84 realised monthly LMPs: **index 0.9324**, N3045 **0.8452**.

## 3. The corroborating evidence, four independent lines

### 3a. January 2023 vs January 2025 — N3045 says they cost the same; the market says 2.7×

| | Jan-2023 | Jan-2025 | ratio |
|---|---|---|---|
| N3045 NE blend | 15.346 | 15.316 | **1.00** |
| ISO-NE AGT index | 4.73 | 16.92 | 3.58 |
| **realised RT LMP** | **$50.51** | **$135.08** | **2.67** |
| NEISO January gas *share* of generation (EIA-930) | **49.3 %** | 46.8 % | — |

N3045 asserts that New England generators paid the same for gas in a mild January and in a cold one
whose power price was 2.7× higher — **and that gas nonetheless ran *harder* in the expensive month**.
Jan-2023's gas share (49.3 %) also exceeds Jan-2022's (44.4 %), the other high-price January. Gas ran
hard in January 2023 because it was **cheap**, which is what the index says and what N3045 denies.

### 3b. The daily prints agree with the index, not with N3045

`data/raw/gas-prices/algonquin_citygate_daily.csv`, January 2023, every committed print:

```
01-04  4.04    01-11  3.38    01-18  3.24    01-25  4.23    01-27  3.22    01-31 13.49
```

Four weeks at **$3.22–$4.23** and a single month-end cold-snap spike (which continues into
02-02 at 28.36). The published monthly index of 4.73 is exactly the average of that shape. There is
no path from these prints to a $15.35 monthly cost of *spot* gas.

### 3c. WITHDRAWN — the "thin panel" reading, and the measurement that refutes it

**This section previously argued that N3045's January-2023 New England price rests on a
one-respondent panel. It does not, and the argument is withdrawn.** It is kept rather than deleted
because the underlying observation is real and a later reader will otherwise re-derive it and reach
the same wrong conclusion.

**What is true.** This repository's own EIA-923 receipt extraction
(`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, the source the F923 receipt
machinery reads) holds, for all of MA/CT/RI/ME/NH/VT in January 2023, **exactly one plant**: 1660
**Potter Station 2**, a 58 MW simple-cycle gas turbine, 28,703 MMBtu at $15.172/MMBtu. Against a
~29-31 million MMBtu New England burn that is **under 0.1 %**. The national sample the same month is
419 plants / 490 million MMBtu, so the thinness is regional to this **extraction**.

**What that is NOT evidence of.** The extraction is a *filtered subset*, not EIA's respondent set.
EIA's published `N3045<ST>3` price has a companion **volume** series, `N3045<ST>2`, and the parallel
NEISO session `neiso-107` fetched it: New England's delivered-gas volume tracks the CAMPD-metered
burn to **1.6 %** (28,728 MMcf = 29,762,208 MMBtu against 29,290,427 MMBtu metered), and the implied
fleet heat rate lands inside a 0.32 MMBtu/MWh band in **36 of 36** months of 2022-2024, with
January 2023 at the median (7.398).

**Their metered leg was re-derived independently here and reproduces to the MMBtu** — summing
`heatInput` over gas-fired units in `data/raw/campd-unit-level/{MA,CT,RI,NH,ME,VT}_2023.parquet` for
January gives **29,290,427 MMBtu** exactly (MA 8,475,796 · CT 13,808,264 · RI 3,800,174 ·
ME 1,609,971 · NH 1,596,222 · VT 0). The volume leg itself could not be re-checked here — the
`N3045<ST>2` series is not committed to this repository — but an instrument whose checkable half
reproduces exactly is accepted rather than argued with.

**So the denominator is essentially the whole fleet's burn, and $15.35 is a real average delivered
cost.** The gap is therefore a **basis** difference, not a sampling one — which is §4, and which the
remaining evidence supports at least as strongly.

### 3d. Cross-state dispersion, read correctly

MA, CT and RI sit on the same Algonquin/Tennessee system and buy the same molecule in the same month.
Their published N3045 prices differ by a great deal:

| month | MA | CT | RI | MA/CT |
|---|---|---|---|---|
| 2023-01 | 24.21 | 9.01 | 9.97 | **2.69×** |
| 2023-05 | 5.61 | 1.82 | 1.69 | **3.07×** |
| 2024-03 | 7.50 | 1.82 | 1.70 | **4.13×** |

**Read under §3c's correction this is not panel noise — it is real, and it is the finding's point.**
A 4.13× spread in the *commodity* between adjacent states on one pipeline in one month is not
possible; a 4.13× spread in **average delivered cost** is, because the states differ in exactly the
things a delivered average includes and a spot index excludes: firm-transportation reservation
charges amortised over whatever volume was actually taken, and **LNG** — Massachusetts is the state
with the Everett Marine Terminal, whose winter cargo cost tracks global LNG rather than Algonquin,
and Massachusetts is the state that prints high. The dispersion is therefore **positive evidence for
the basis reading**, not evidence against the survey.

The same applies to the sign of the wedge. Across 84 months the blend sits a median **1.228×** above
the index — the persistent transport-and-contract component — yet falls **below** it in **10 of 84**
months. A delivered cost cannot be below the spot index it is delivered off *at the same moment*;
it can be below a *later* spot price when the volume was bought forward under contract. Both
directions are what an average-of-contracts series does and neither is what a marginal price does.

## 4. What both series actually measure, stated plainly

- **The ISO-NE AGT index** is the next-day spot price at the constrained hub. It is the **opportunity
  cost of the marginal molecule**, and it is the number a New England generator's offer is built on.
  It is the correct input for an LP whose duals are prices (rule 4 `[R-DUALS]`).
- **N3045** is an **average delivered cost across every purchase a surveyed buyer made**, mixing spot,
  firm-transport reservation charges amortised over whatever volume was actually taken, and — in New
  England specifically — **LNG cargoes** (Everett Marine Terminal), whose winter cost tracks global
  LNG rather than Algonquin. Those are real costs, but they are **contract** costs recovered outside
  the energy offer, and they are averaged over a panel that is not the marginal fleet.

Both are measured. They measure different quantities. The market clears on the first.

## 5. Consequences — what changes, and what does not

1. **Nothing in NEISO's fuel recipe changes.** The keeper's `gas_hub_basis_overlay` (Algonquin via
   the ISO-NE MA index, 12/12 months every year) is correct and keeps priority.
2. **The FINDING §4 ordering is confirmed on evidence, not assumed.** `measured hub index` supersedes
   `state-average monthly` because the hub index is the marginal series. §6a's reading was right; it
   is now proven.
3. **The 2.303 $/MMBtu "level gap" in the cross-ISO table is NOT a NEISO defect** and must not be
   quoted as one. It is the distance between a **marginal** price and an **average delivered** cost —
   two different quantities — and the model is correctly on the marginal one. **The cross-ISO table's
   NEISO rows measure the basis difference, not the model.**
4. **`gas_electric_power_monthly_level` is promoted ON for NEISO anyway** (owner ruling 2026-09-09,
   `xiso-fuelvintage-per-iso-lp-prompts` §A7) and is **provably inert** there — see
   `PRECOMMIT-neiso-fuelvintage-2026-09-09.md` §3. The promotion and this finding are consistent
   precisely *because* the ordering puts the hub index above the seam.
5. **A corroborator is NOT recommended for NEISO.** `ercot-261` built one
   (`derive_ercot_gas_corroborator.py`) to check one measured series against a second where both are
   plausibly marginal. NEISO's case is different: the second series is **not a candidate at all** —
   not because it is unreliable, but because it measures a **different quantity**, and one that fails
   a physical test as a marginal price in 13 of 84 months. Blending an average-delivered series into
   a marginal one would corrupt the series that is already correct. **Recommendation: do not build a
   NEISO copy.** (Stated as a recommendation, not an action, per the handoff. The parallel session
   `neiso-107` reached the same recommendation independently.)
6. **Where MISO's Louisiana hole is concerned this cuts the other way, and is flagged not acted on:**
   MISO's keeper has *no* measured monthly gas level at all, so for MISO a second series is an
   upgrade over a climatological shape. The NEISO result does not transfer (rule 25
   `[R-ISO-SCOPE]`); it only warns that an N3045 state blend must be checked for panel thinness
   before it is trusted as a monthly level. **The implied-heat-rate test in §2 is the cheap,
   ISO-agnostic instrument for doing that, and it is the transferable part of this finding** — and
   §3c is the transferable *caution*: check EIA's own companion volume series `N3045<ST>2`, never
   this repository's filtered EIA-923 extraction, before drawing any conclusion about coverage.

## 6. Reproduce

```
python3 scripts/probes/_neiso_index_vs_delivered_gas.py
```
Reads only committed measured sources: `data/raw/gas-prices/{isone_ma_gas_index_monthly.csv,
algonquin_citygate_daily.csv, eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv}`,
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, `data/raw/ISNE_fueltype.parquet`
and `data/raw/lmp-data/NEISO/<year>_smd_hourly.xlsx`. No LP, no write under `data/raw`.

## 7. Governance

- **Rule 14 `[R-ACCURATE]`:** the accurate input is *kept*, and the estimate is not restored — the
  question was only which of two measured series represents the modelled quantity. The misalignment
  exception applies on its stated terms ("defined on a different boundary … so that using it
  literally would make overall results less reflective of reality"), now with a measurement behind it.
- **Rule 1 `[R-STRUCT]`:** no residual was consulted. The test is a physical bound and a market
  identity; the conclusion would be the same if it made every gate worse.
- **Rule 22 `[R-HOLDOUT]`:** this is unrestricted data inspection across 2019-2025. **No year was
  solved, scored or registered here**, so no marker is engaged — including for 2019, which appears
  only as rows of published measured input, never as a model result.
- **Rule 13 `[R-MEASURED]`:** nothing is pinned to an outcome. The RT LMP series is used as a
  *falsifier of an input*, never as an input; no model quantity is fitted to it.
