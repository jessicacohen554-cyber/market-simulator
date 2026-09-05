# FINDING miso-216 — THE GAS-OFFER MARGIN ANCHOR'S BASIS/CLASS GRAIN: **no grain dominates**, the registered anchor is within **0.25–1.24 %** of the best achievable scalar on the two material classes in 2023–2024, **≥ 87.8 % of the distortion is irreducible by ANY scalar** because it is the fixed-margin FORM's own footprint rather than the anchor's location — and the one axis on which the anchor IS clearly wrong (a systematic **−$10 to −$20/MWh** signed bias on `CT_PEAKER`) is corrected only by grains that cost 3.8–6.9 TWh of that class's energy; **RECOMMENDATION TO THE OWNER: NO CHANGE**, with the strongest counter-argument carried on the packet's face, the miso-215 anchor prerequisite **DISCHARGED**, and a sharper successor named. **NOTHING ARMED, NOTHING MINTED, ZERO SOLVE** (2026-09-05)

**Keeper UNCHANGED at `2026-09-05-miso-213-layering`** (bundle
`results/calibration/miso213_layering_B`), NOT-YET on C3a-2025 alone (−11.747 %), C3c
ledgered 3/3, C6 attested 41/2. **No `ScenarioConfig` field, no registry entry, no matrix
row, no solve, no cell verdict changed.** PREREG
`PREREG-miso216-anchor-basis-grain-2026-09-05.md` pushed **BLIND** at `9fcd69cd`, before any
adjudicating statistic of this session. Probe
`scripts/probes/_miso216_anchor_basis_grain_phase0.py` → record
`results/calibration/_miso216_anchor_basis_grain.json`. Rule 22 `[R-HOLDOUT]`: 2023–2025
only (the probe hard-asserts it).

---

## 0. Verdict in one paragraph

miso-215 handed this lane a concern: the anchor that sizes `apply_gas_offer_margin`'s fixed
margin is an ISO-level Henry-Hub-plus-$0.30 series while the fleet pays a per-plant EIA-923
print, and at class grain the two differ by 0.9–3.3 $/MMBtu on `CT_PEAKER` and `ST_GAS`. This
session priced every admissible identification point against the mechanism's **own** identity
criterion — *at `fuel == anchor` the reformed offer reduces exactly to the registered band
multiplier* — and the concern **does not survive contact with that criterion in the form
miso-215 stated it.** Three findings, in order of importance. **(1) The distortion is almost
entirely irreducible.** `CT_PEAKER`'s capacity-hour mean absolute deviation from the
registered multiplier form is **$21.55 / $15.64 / $15.76 per MWh** at the registered anchor,
and the **best scalar anchor that exists** — searched over a dense grid, not chosen from a
statistic — only reaches $21.29 / $15.57 / $13.84. **87.8–99.5 % of it survives the best
possible choice**, because the deviation is dominated by the *dispersion* of the class's own
delivered fuel, not by where a scalar sits in it. Against `CT_PEAKER`'s own cap-weighted
offer of $58–71/MWh that residue is **24–30 % of the offer**, and it is the price of the
fixed-margin FORM, not of its anchor. **(2) No grain dominates** (K-3 FIRES): on L1 the
per-class-median grain improves 8 of 15 class-years and worsens 7; on L2 it improves 10 and
worsens 4; the per-class-MEAN grain — the one miso-215's §4c table pointed at and the one I
pre-registered as my favourite — is the **worst** of all for `CT_PEAKER`, raising its L1 to
$23.33 / $20.08 / $15.18. **(3) The anchor IS clearly wrong on one axis and only one**:
signed bias. The reformed `CT_PEAKER` offer sits **−$19.51 / −$10.26 / −$15.37 per MWh**
below the registered multiplier form, systematically and in every year (`ST_GAS` −$2.16 /
−$3.57 / −$4.84; `CC_REGULAR` ≈ 0). Correcting that bias needs the class-mean grain, which
costs **3.8–6.9 TWh** of `CT_PEAKER` screen energy on a class already 5–35 % under actual and
pushes the C8 `CT_PEAKER`-2023 forced share above its 0.2044, already over the 0.15 peaker
budget. **Recommendation: NO CHANGE**, with that bias carried on the packet's face as the
strongest argument against the recommendation, because under rule 1 `[R-STRUCT]` "correcting
it hurts the fit" is not an argument. **miso-215's anchor prerequisite is DISCHARGED** — the
coverage-gap arm is unblocked on this ground — and the successor this session names is not
the anchor but the **form**: whether a fixed-margin decomposition is appropriate at all for a
class carrying that much delivered-fuel dispersion. Owner-court, on the mechanism's own cell.
**P-5 is WRONG and P-1's mean leg is WRONG; §8 scores them.**

## 1. Instrument, footing, and what it cannot see

* **Zero solve.** Every number from committed artifacts and the HEAD fleet chain.
* **FOOTING CHECK, pre-registered in PREREG §3 and PASSED EXACTLY.** The probe reproduces
  miso-215's published quantities to the last digit: gas capacity **65,907.1 MW**;
  `CT_PEAKER` remainder **econ-band** cap-weighted markup **3.9059** in all three years
  (miso-215 §4c), `CC_REGULAR` **0.4862**, `ST_GAS` **2.0475 / 2.0473 / 2.0473**. That is
  what establishes the T-1 re-point landed on the miso-213 keeper rather than the miso-210
  control — the `_miso212 → _miso211` module-scope trap that cost miso-214 a whole three-year
  launch, closed here by an assert on `miso_zonal_gas_basis_skip_923_priced`.
* **SCOPE NOTE THAT RECONCILES THE TWO SESSIONS' MARGIN FIGURES.** miso-215 reported
  **econ-band** markups; this session's class-level `markup_hr` spans **every** marked-up
  band (econ + peak + committed) because the mechanism reprices all of them. `CT_PEAKER` is
  3.9059 econ-only → **$11.91/MWh** at the anchor (miso-215's number) and **6.4523** all-band
  → **$19.67/MWh** (this session's). Both are correct; they are different populations, and
  every table below states which it uses.
* **M-0, THE F-3 INSTRUMENT REPAIR, DONE FIRST.** Every mean **and** quantile here is
  capacity-hour weighted on a 0.005 $/MMBtu histogram (one unit of mass = one MW-hour of
  capacity), fixing miso-215's asymmetry (capacity-hour weighted means beside unweighted
  percentiles). The size of that defect is visible in the record's
  `M0_miso215_unweighted_reference` block rather than quietly corrected.
* **Plant-grain model merit is the PRICE-TAKING STATIC SCREEN**, not the LP — the keeper
  ships no `unit_hourly/` or `dispatch/`. miso-214 §1 measured it at **1.41–1.43×** the LP's
  own CT class energy, and it **holds the price fixed, so cross-class backfill is invisible
  to it.** Every A-2 reach is a BOUND and the C1 exposure is an un-instrumented risk.
* **F-4's two-build technique reused, and it confirms at FLEET grain.** A second build per
  year with `dual_fuel_switching=False` puts the share of capacity-hours where the resolved
  price exceeds the no-switch price at **0.000 for every gas class in every year**, and the
  two series diverge at all on only **0.0–1.3 %** of capacity-hours. No class's delivered
  price is inflated by an oil step. (Where they diverge, the no-switch price is *higher* —
  disarming the switch strands some dual-fuel rows on an oil default — so that counterfactual
  is a check, never a "gas print" series in its own right.)
* **A metric identity, disclosed BEFORE it could be used to flatter a conclusion.** L1 mean
  absolute distortion is **minimized at the weighted MEDIAN by construction** and its L2/RMS
  sibling at the weighted **MEAN**; a single-metric packet would have built its own answer
  in. All three (L1, L2, signed bias) are reported at every grain, and the decisive
  comparator is each class-year's **best achievable scalar**, found by grid search rather
  than by picking a statistic.
* **What this instrument cannot do:** it cannot say which grain is *right*. It prices each
  candidate on three axes and reports the consequences. §7 makes that limit the packet's
  content rather than hiding it.

## 2. A-1 — the candidate grains, priced

Capacity-hour weighted over the 2023–2025 window (per-year values in the record):

| grain | window anchor | 2023 / 2024 / 2025 | weighting |
|---|---:|---|---|
| **(a) status quo** — ISO `_gas_series` mean | **3.0492** | 3.0492 (one scalar) | none — a price series |
| **(b)** fleet capacity-hour MEAN | **3.9736** | 4.0418 / 3.3800 / 4.4991 | capacity-hour |
| **(c)** fleet capacity-hour MEDIAN | **3.1425** | 2.9775 / 2.5475 / 3.6675 | capacity-hour |
| **(e)** fleet ENERGY-weighted mean | **3.2417** | 3.0475 / 2.7417 / 3.9604 | screen-dispatch MWh (a bound) |

**(d) per-CLASS**, window, capacity-hour weighted:

| class | capacity MW | MEAN | MEDIAN | energy-weighted MEAN |
|---|---:|---:|---:|---:|
| `CT_PEAKER` | 22,281.8 | **4.7197** | 3.4275 | 3.1102 |
| `CC_REGULAR` | 27,420.1 | 3.3539 | 2.9575 | 3.2494 |
| `ST_GAS` | 10,991.0 | **4.3196** | 3.1725 | 3.5340 |
| `CC_CHP` | 3,620.6 | 3.2592 | 3.1275 | 3.1902 |
| `CT_CHP` | 896.0 | 3.0503 | 2.9025 | 2.9955 |
| `ST_CHP` | 697.6 | 3.9454 | 3.5675 | 3.5405 |

**Two facts worth stating before any argument.** The fleet capacity-hour **MEDIAN** (3.1425)
sits **0.093 $/MMBtu** from the registered anchor, and the energy-weighted fleet mean over
2023 alone lands at **3.0475** against 3.0492 — within **0.0017**. The ISO series is not an
arbitrary basis: on the two weightings that track where the fleet's *energy* and its
*typical hour* actually sit, it is already almost exactly right. The gap opens only on the
capacity-hour **MEAN** (3.9736, +0.92), which is pulled by a fat right tail on the peaking
and steam classes. **K-1 does not fire** (mean 0.92 outside the ±0.35 bar) but it fails only
on the mean leg.

## 3. A-3 — THE DECISIVE MEASUREMENT: the best scalar that exists

The mechanism's own identity is a statement about the reformed offer against the registered
multiplier form. Measured per class-year at the registered anchor, beside the **minimum over
a dense grid** (1.50–9.00 $/MMBtu at 0.02) — i.e. the best any scalar anchor could ever do:

| class | year | L1 @ 3.0492 | L1 **best** | argmin | **excess of registered over best** | L2 @ 3.0492 | L2 best |
|---|---|---:|---:|---:|---:|---:|---:|
| **`CT_PEAKER`** | 2023 | **21.549** | **21.285** | 3.440 | **+1.24 %** | 26.985 | 26.557 |
| | 2024 | **15.638** | **15.567** | 2.840 | **+0.46 %** | 31.125 | 31.094 |
| | 2025 | **15.759** | **13.837** | 3.860 | **+13.89 %** | 20.056 | 17.836 |
| **`ST_GAS`** | 2023 | 3.209 | 3.189 | 2.920 | +0.62 % | 4.594 | 4.582 |
| | 2024 | 5.144 | 5.131 | 2.900 | +0.25 % | 9.687 | 9.580 |
| | 2025 | 4.879 | 3.881 | 4.080 | +25.70 % | 6.761 | 5.592 |
| `CC_REGULAR` | 2023 / 24 / 25 | 0.213 / 0.456 / 0.459 | 0.191 / 0.347 / 0.329 | 2.84 / 2.44 / 3.66 | +11.3 / +31.3 / +39.6 % | 0.291 / 0.996 / 0.718 | 0.280 / 0.979 / 0.575 |
| `CT_CHP` | 2023 / 24 / 25 | 0.735 / 1.141 / 0.916 | 0.647 / 0.741 / 0.727 | 2.76 / 2.32 / 3.46 | +13.5 / +54.0 / +26.0 % | 0.927 / 1.815 / 1.491 | 0.831 / 1.656 / 1.225 |
| `CC_CHP` | 2023 / 24 / 25 | 0.025 / 0.036 / 0.035 | 0.025 / 0.026 / 0.026 | 3.00 / 2.46 / 3.54 | +0.3 / +38.6 / +37.8 % | 0.035 / 0.073 / 0.058 | 0.035 / 0.072 / 0.046 |

**Read the percentages against the dollars.** The large excesses sit entirely on classes
whose absolute distortion is trivial: `CT_CHP`-2024's +54 % is **$1.14 → $0.74**, i.e.
$0.40/MWh on 896 MW. On the two classes that carry the mechanism's weight the registered
anchor is within **0.25–1.24 %** of the best scalar in 2023 and 2024, and the largest dollar
saving available anywhere in the study is **$1.92/MWh** (`CT_PEAKER`-2025) and **$1.00/MWh**
(`ST_GAS`-2025).

**And the residue is the story.** `CT_PEAKER`'s distortion cannot be brought below **$21.29 /
$15.57 / $13.84** by *any* scalar — **87.8 %, 99.5 % and 98.8 %** of the distortion at the
registered anchor survives the best possible choice. Against that class's cap-weighted offer
of **$70.65 / $57.97 / $66.04 per MWh**, the irreducible part is **24–30 % of the offer**.
That is not a property of the anchor. It is the footprint of the fixed-margin **form** on a
class whose own delivered fuel runs p25 2.78 → p75 4.67 with a mean of 5.22 (2023).

## 4. A-3 — the one axis on which the anchor IS wrong: SIGNED BIAS

Cap-weighted mean **signed** deviation, $/MWh, reformed minus registered multiplier form:

| class | @ (a) 3.0492 | @ (c) 3.1425 | @ (e) 3.2417 | @ (d) class MEDIAN | @ (d) class MEAN | @ (b) 3.9736 |
|---|---|---|---|---|---|---|
| **`CT_PEAKER`** | **−19.51 / −10.26 / −15.37** | −18.91 / −9.66 / −14.77 | −18.27 / −9.02 / −14.12 | −17.07 / −7.82 / −12.93 | **−8.74 / +0.52 / −4.59** | −13.55 / −4.29 / −9.40 |
| `ST_GAS` | −2.16 / −3.57 / −4.84 | −1.97 / −3.38 / −4.64 | −1.77 / −3.18 / −4.44 | −1.91 / −3.32 / −4.58 | **+0.44 / −0.97 / −2.23** | −0.27 / −1.68 / −2.94 |
| `CC_REGULAR` | +0.07 / +0.15 / −0.45 | +0.12 / +0.20 / −0.40 | +0.16 / +0.24 / −0.35 | +0.03 / +0.11 / −0.49 | +0.22 / +0.30 / −0.30 | +0.52 / +0.60 / +0.00 |

**This is real and it is one-directional.** On `CT_PEAKER` the reformed offer sits $10–20/MWh
below the form it is meant to reduce to, in every year, on 12.0 GW of marked-up capacity. On
`CC_REGULAR` — 27.4 GW, the class the ISO series effectively tracks — the bias is
indistinguishable from zero. **Only the per-class MEAN grain removes it** (that is the
identity: signed bias is zero at the weighted mean), and that is exactly the grain §3 shows
is worst on L1 and L2 for the same class.

## 5. A-2 — what each grain costs, on the pre-registered protective faces

Static-screen reach, TWh, of moving **only** the anchor (the three uncovered cohorts are
untouched — F-1). **The screen is a 1.41–1.43× bound and is blind to cross-class backfill;
these are bounds, not measurements.** Protective faces pre-registered in PREREG §4 before
measurement: C1 `CC_REGULAR`-2024 at **+7.419** of **±8.00** (0.58 TWh of headroom); C8
`CT_PEAKER`-2023 at **0.2044** against the **0.15** peaker budget, passing only on rule 20's
conditional route.

| grain | Δanchor | `CT_PEAKER` 23/24/25 | `ST_GAS` | `CC_REGULAR` |
|---|---:|---|---|---|
| (a) status quo | 0 | +0.004 / +0.002 / +0.001 | −0.018 / −0.018 / −0.016 | −0.003 / −0.003 / −0.005 |
| (c) fleet median | +0.093 | −0.461 / −0.523 / −0.490 | −0.161 / −0.096 / −0.094 | −0.012 / −0.013 / −0.021 |
| (e) energy mean | +0.193 | −0.939 / −1.063 / −0.981 | −0.275 / −0.174 / −0.153 | −0.020 / −0.020 / −0.031 |
| (d) class median | +0.378 (CT) | −1.762 / −2.001 / −1.936 | −0.200 / −0.122 / −0.114 | +0.005 / +0.006 / +0.011 |
| (b) fleet mean | +0.924 | −3.815 / −4.411 / −4.487 | −0.976 / −0.642 / −0.508 | −0.090 / −0.088 / −0.121 |
| **(d) class MEAN** | **+1.671 (CT)** | **−5.735 / −6.609 / −6.906** | −1.242 / −0.817 / −0.633 | −0.031 / −0.029 / −0.045 |

**Every grain that raises the anchor removes `CT_PEAKER` energy, in all three years, without
exception** — the F-2 mechanism (a fixed $/MWh margin prices UP exactly the low-fuel hours
the class is marginal in) applied to the armed class. `CT_PEAKER` is 5–35 % **under** actual,
so all of this is adverse, and less merchant CT energy raises the C8 2023 forced share above
0.2044. `CC_REGULAR`'s reach never exceeds **0.121 TWh** under any grain — the C1 face is not
materially exposed by the anchor question, which is worth saying plainly since it was
pre-registered as a risk.

## 6. A-4 — cross-ISO exposure, COUNTED from committed artifacts only

Criterion: the margin is **armed** AND the keeper prices the fleet per-plant
(`gas_plant_monthly_fuel_pricing`), which `_gas_series` cannot carry. **No other ISO's fleet
was built, no other ISO's delivered price was measured, and no other ISO's matrix cell is
filled** (rule 25 `[R-ISO-SCOPE]`).

| ISO | margin armed | anchor | basis diff | per-plant 923 | zonal basis | zonal anchor | **basis-grain exposed** |
|---|---|---:|---:|---|---|---|---|
| **ERCOT** | yes | 2.2494 | −0.50 | **NO** | yes | **yes** | **NO** |
| PJM | yes | 3.3483 | +0.67 | yes | yes | no | **YES** |
| CAISO | yes | 4.7964 | +1.20 | yes | no | no | **YES** |
| MISO | yes | 3.0492 | +0.30 | yes | yes | no | **YES** |
| NYISO | yes | 3.9046 | +0.55 | yes | yes | **yes** | **YES** |
| NEISO | yes | 4.0763 | +1.10 | yes | no | no | **YES** |

**Five of six exposed; ERCOT is the exception** — `backcast_config` sets
`gas_plant_monthly_fuel_pricing=(iso != "ERCOT")`, so ERCOT's fleet and its anchor share one
basis, and it is additionally the only ISO besides NYISO whose keeper arms the zone-resolved
anchor. **P-4 RIGHT.** One incidental observation, reported for **PJM's own lane and filled
into no cell of theirs**: PJM's keeper arms `pjm_zonal_gas_basis` while
`gas_offer_margin_zonal_anchor` is off, and a resolved `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`
table for PJM already exists — the nyiso-109 situation, un-adopted. On MISO the same
combination is **moot in a backcast** since miso-213 removed the zonal increment from every
923-priced cell. This is a count, not a verdict.

## 7. THE OWNER PACKET

**The question, in one paragraph.** `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` is the identification
point of `gas_offer_net_revenue_margin`: the mechanism reprices a tranche's markup from a
fuel-scaled multiplier to a fixed margin `markup_hr × anchor`, and claims that at
`fuel == anchor` the reformed offer reduces exactly to the registered band multiplier. On
MISO the anchor is the mean of an ISO-level Henry-Hub-plus-$0.30 series, while the fleet is
priced per plant from EIA-923 — a different basis. Should the anchor be re-identified at
fleet grain, class grain, or on a different weighting? It moves five already-armed MISO gas
classes at once, four other ISOs share the construction, and it is a change to an
identification rather than a re-derivation on new data, so rule 23 does not reach it.

**The grains, side by side.** Primary axis = the mechanism's own identity criterion,
measured on the class where it bites (`CT_PEAKER`); secondary axes named.

| grain | window anchor | CT L1 $/MWh 23/24/25 | CT signed bias | CT screen reach TWh | verdict |
|---|---:|---|---|---|---|
| **(a) status quo** | 3.0492 | **21.55 / 15.64 / 15.76** | **−19.5 / −10.3 / −15.4** | ~0 | within 1.24 % of best on L1 in 23/24; **biased** |
| (c) fleet median | 3.1425 | 21.43 / 15.72 / 15.34 | −18.9 / −9.7 / −14.8 | −0.46 / −0.52 / −0.49 | marginal L1 gain; bias barely moves |
| (e) energy mean | 3.2417 | 21.35 / 15.83 / 14.94 | −18.3 / −9.0 / −14.1 | −0.94 / −1.06 / −0.98 | ditto, slightly larger cost |
| (d) class median | 3.4275 (CT) | 21.29 / 16.11 / 14.36 | −17.1 / −7.8 / −12.9 | −1.76 / −2.00 / −1.94 | best L1 in 23/25, worse in 24 |
| (b) fleet mean | 3.9736 | 21.66 / 17.45 / 13.86 | −13.5 / −4.3 / −9.4 | −3.81 / −4.41 / −4.49 | worse L1 in 23/24 |
| **(d) class MEAN** | 4.7197 (CT) | **23.33 / 20.08 / 15.18** | **−8.7 / +0.5 / −4.6** | **−5.73 / −6.61 / −6.91** | **removes the bias; worst on L1/L2; largest cost** |
| — | *best scalar* | *21.29 / 15.57 / 13.84* | — | — | *the floor no grain beats* |

**What the evidence favours: NO CHANGE.** Three grounds. **(i)** 87.8–99.5 % of the
`CT_PEAKER` distortion is irreducible by any scalar; the best available saves at most
$1.92/MWh on a $58–71/MWh offer, and the registered anchor is within 0.25–1.24 % of that
floor in two of three years. **(ii)** No grain dominates on both L1 and L2 (K-3 FIRES); the
grain that best removes the bias is the worst on both distortion metrics for the very class
it targets. **(iii)** Every bias-correcting grain removes 3.8–6.9 TWh of `CT_PEAKER` screen
energy on a class 5–35 % under actual and raises a C8 forced share already over its budget.

**The strongest argument AGAINST that recommendation, carried on the packet's face.** The
**−$10 to −$20/MWh signed bias on `CT_PEAKER` is real, systematic and one-directional**, and
it is exactly what "mis-identified" means: a mechanism whose reformed offer sits that far
below the form it claims to reduce to is shifted, not identified. Under rule 1 `[R-STRUCT]`,
"correcting it costs 6 TWh and worsens C8" is **not** a reason to keep a wrong structure.
Anyone who reads the identity claim as a statement about the *level* of the class's offer
should conclude the class-mean grain is right and this recommendation is wrong.

**Why I nevertheless recommend NO CHANGE, and where that judgement could fail.** The L1/L2
measurement says the bias correction does not bring the reformed offer *closer* to the
registered form on a typical hour — it re-centres a distribution whose spread it cannot
touch, and on L1 it moves `CT_PEAKER` **away** from the form in two of three years. That
reads the bias as a symptom of the **form** rather than of the anchor. **If the owner reads
the identity as a level statement instead of a typical-hour statement, the recommendation
inverts** — and that is a reading about what the mechanism means, which is the owner's to
make and not settled by any measurement in this record.

**What this lane does under each ruling.**

* **"No change"** → the packet is the record; the anchor prerequisite miso-215 imposed is
  discharged; miso-217 takes the coverage-gap arm (F-1: K-a and K-b already pass) under its
  own prereg, carrying §3's form-footprint measurement as a stated fact.
* **"Re-identify at class grain"** → PREREG §7's arm, built at
  `data/fleet/assembly.py::bins_to_fleet` where `gas_offer_margin_zonal_anchor` already
  resolves (disjoint by construction, rule 19), scorer committed before the solve, with the
  C8 and C1 faces of §5 as pre-registered kills. Expect it to be adverse on C1/C3a and
  promotable only on the owner's structure-over-gates standard.
* **"Re-identify at fleet grain"** → same machinery, grain (b) or (c); (c) is nearly free and
  nearly inert, (b) costs 3.8–4.5 TWh of CT.
* **"The FORM is the question, not the anchor"** → the successor named below, which needs its
  own charter and its own prereg.

**The successor this session names and does NOT charter.** The fixed-margin form's own
footprint: a **24–30 % of offer** mean absolute deviation from the registered multiplier form
on `CT_PEAKER`, irreducible by any anchor, arising because the class's delivered fuel is
dispersed (p25 2.78 → p75 4.67, mean 5.22 in 2023) while the margin is fixed. Whether a
fixed-margin decomposition is appropriate for a class with that much fuel dispersion is a
question about `gas_offer_net_revenue_margin` itself — its own cell, currently `K` — and
re-opening it is an owner decision, not a lane lever. **Named, measured, not chartered.**

## 8. My prior, scored against interest

* **P-1 half WRONG.** Window fleet capacity-hour MEAN is **3.9736**, +0.9244 over the anchor;
  I predicted +0.35 to +0.85 — **outside my own band, and I under-predicted the tail.** The
  MEDIAN leg is **RIGHT** (|diff| 0.0933 against a ±0.30 bar).
* **P-2 partly RIGHT, its decisive clause WRONG.** "Largest on `CT_PEAKER`" RIGHT; "> $8/MWh
  in ≥ 2 of 3 years" RIGHT (all three); "(b) reduces CT by < 25 %" RIGHT (it *increases* it in
  2023/2024). **"Only (d) reduces it by ≥ 50 %" is WRONG and wrong by a wide margin** — (d)
  class-mean makes CT worse, and the *best scalar in existence* reduces it by 1.24 % / 0.46 %
  / 13.89 %. I framed a question about anchor location; the answer is that location is nearly
  irrelevant.
* **P-3 RIGHT on both legs.** Every anchor-raising grain reduces `CT_PEAKER` screen energy in
  3 of 3 years; `CC_REGULAR`'s |reach| never exceeds 0.121 TWh against my < 0.5 bar.
* **P-4 RIGHT.** ERCOT is the one unexposed ISO, for the reason I named
  (`gas_plant_monthly_fuel_pricing=(iso != "ERCOT")`); the other four of the other five are
  exposed.
* **P-5 WRONG.** I predicted the evidence would favour **(d) per-CLASS**. It does not: K-3
  fires, no grain dominates on both metrics, and the per-class **MEAN** — the variant
  miso-215's §4c table pointed at — is the **worst** available for `CT_PEAKER` on both
  distortion axes while costing the most energy. My pre-registered counter-argument (a
  rule-21 DOF concern about multiplying two class-fitted quantities) turned out **not** to be
  the reason it fails.
* **P-6 RIGHT and executed.** No owner was present; the fallback is the packet plus a
  hand-off, and nothing was armed.
* **Kills:** K-1 does not fire (fails on the mean leg only, 0.9244 > 0.35); K-2 does not fire
  ($21.55 max ≫ $2); **K-3 FIRES** — no grain dominates on both L1 and L2.

## 9. Reported against interest

1. **This finding materially SOFTENS my own previous session's framing, and I say so at full
   volume.** miso-215 §4c measured the margin's **level** against a class statistic and
   reported the armed `CT_PEAKER` margin as installed "35–52 % below what the mechanism's own
   identity requires". That table is arithmetically correct and its reading was too strong:
   measured against the identity criterion itself, **no scalar anchor recovers more than
   12.2 % of the deviation on that class**, and the registered anchor is within 1.24 % of the
   best available in 2023. The honest summary is that miso-215 found a real *bias* and
   over-attributed it to the *grain*.
2. **The L1 metric's minimizer is the weighted median by construction**, so a packet built on
   L1 alone would have manufactured the median grain's advantage. That is why all three
   metrics and the grid-searched best scalar are reported. It is also why "(d) class median
   improves 8 of 15 class-years on L1" is **not** quoted as evidence for it.
3. **Every A-2 number is a static-screen bound, 1.41–1.43× the LP, blind to cross-class
   backfill.** The −6.9 TWh at grain (d)-mean is a bound on a bound; the LP's own response
   could be materially smaller. The direction is robust (every grain that raises the anchor
   removes CT energy in every year); the magnitude is not.
4. **The 2025 column is the weakest year's actuals** (preliminary EIA-923 vintage, C1
   SKIPPED) and it is also the year where the best-scalar gain is largest (13.9 % on CT,
   25.7 % on ST). If the case for changing the grain rests anywhere, it rests on 2025 — the
   year whose actuals are least settled. Stated so a reader can discount it.
5. **`ST_CHP` carries no marked-up tranche at all** (`markup_hr` 0.0000 on 697.6 MW), so it
   appears in A-1 and is absent from A-2/A-3. Not an omission — the mechanism does not reach
   it.
6. **The class-level `markup_hr` here spans every marked-up band while miso-215's spans the
   econ band only.** `CT_PEAKER` is 3.9059 econ-only against 6.4523 all-band, so this
   session's $19.67/MWh margin and miso-215's $11.91/MWh are the same quantity on different
   populations. Quoting one against the other would be an error and §1 states which is which.
7. **The dual-fuel counterfactual is a check, not a series.** Where the two builds diverge
   (0.0–1.3 % of capacity-hours) the no-switch price is *higher*, by up to $198/MMBtu on
   individual rows stranded on an oil default. That is a property of disarming the switch,
   not evidence about the resolved price, and nothing here is computed from it beyond the
   zero-share check.

## 10. Governance

Rule 15 `[R-DASHBOARD]`: **zero-solve session — no run produced, none registered**; the
deliverables are this finding, the PREREG, the probe, its JSON record, the log entry, the
§5.4 queue stamp and the MISO shard cells. Rule 22 `[R-HOLDOUT]`: 2023–2025 only (the probe
hard-asserts it). Rule 16 `[R-ALLYEARS]`: all three training years measured in one pass.
Rule 25 `[R-ISO-SCOPE]`: only `docs/codebase-site/data/mechanism-matrix/MISO.js` is edited;
**no field added, so no base row and no other shard is touched** (rule 28c not engaged).
**A-4 counts other ISOs' exposure from committed artifacts and fills no cell of theirs**; the
PJM zonal-anchor observation in §6 is handed to PJM's lane, not adjudicated here. Rule 28(b):
the one cell this session produced evidence about — `gas_offer_net_revenue_margin` (cell
UNCHANGED at `K`; evidence about the mechanism's IDENTIFICATION and its FORM footprint, not a
re-verdict) — is updated in this session. Rule 13 `[R-MEASURED]`: the EIA-923 print path is
read as a DIAGNOSTIC only; no measured outcome is fed back as an input. Rule 23
`[R-FROZEN-DERIVE]`: no derive script run and no artifact rewritten — `GAS_SERIES_FLAGS` and
the anchor registry are read, never re-derived. Rule 24 `[R-REGISTRY]`: no new tunable.
Rule 19 `[R-ONE-MECH]`: the arm PREREG §7 designs (if ever ruled) resolves at the same seam
as `gas_offer_margin_zonal_anchor` so the two can never stack. Rule 27 `[R-PUSH]`: every file
edited locally and blob-verified after push; **no source file changed at all this session**.
DO-NOT-REDO honoured: `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
`miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
`miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (**I — the ZONAL
grain, untouched; this session's BASIS/CLASS grain is a different question**),
`zonal_gas_basis` (K), `measured_offer_surface` (R) are neither re-tested nor re-opened. The
CT commitment-bridge family (closed at miso-214) and the intermediate-cohort `phys_*`
borrowing and dual-fuel confound (closed at miso-215) are not re-opened. The
average-vs-marginal delivered-cost convention (miso-212 §8) stays OWNER-COURT and is
**adjacent to but distinct from** this question — it asks which cost basis an offer uses;
this asks where a fixed margin is identified. The D-2 5(i) seam-response object and the South
price separation (miso-211 D-3 / miso-213 O-4) are untouched.

**The miso-214 standing result is not undone.** 62–70 % of the CT energy the model misses was
produced by the real market **below the plant's own delivered cost, at the market's own
price**, and is **not reachable by any offer or price mechanism**. Nothing in this session's
anchor arithmetic is presented as closing the CT class's gap.

Next shorthand: **miso-217**.
