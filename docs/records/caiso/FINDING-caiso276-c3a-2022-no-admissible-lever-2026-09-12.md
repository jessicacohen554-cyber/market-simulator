# FINDING — caiso-276: C3a-2022 CANNOT BE CLOSED HONESTLY. The charter's own handed-forward object carries 2.6 % of the residual, 2022 is ONE object rather than two, and every remaining channel is spent, inert, wrong-signed or forbidden.

**Session caiso-276, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). ZERO LP SPENT —
no solve, no shard, no arm, no `ScenarioConfig` field, no run registered.
KEEPER UNCHANGED at `2026-09-12-caiso-275-gascoupling`.**

Every number below is measured from **committed artifacts**: the folded 2022 rung
`results/calibration/caiso275_B_gascoupling_2022` (system / class / class-band / storage
hourlies + the unit-level `dispatch/2022_P1.parquet`), the keeper's span bundle, the committed
`bench/CAISO/2022.json.gz`, `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`,
`data/raw/_validation-source/caiso_offer_curve_measured.json`, and the keeper's **own**
re-assembled offer surface via `reconstruct_bundle_fleet` (`fleet_only` — no solve).

Probes: `scripts/probes/_caiso276_belly_phase0.py`, `_caiso276_where_2022_lives.py`,
`_caiso276_clock_check.py`, `_caiso276_implied_hr.py`, `_caiso276_marginal_and_seam.py`.

---

## §0 — THE VERDICT, STATED AS THE CHARTER ASKED

> **No admissible lever exists for C3a-2022.**

The charter's deliverable 5 is the outcome. CAISO **is and remains CALIBRATED** on 2023–2025
with its single ledgered C3c caveat (rule 30(c) `[R-TOUCHPOINT-FOLD]`: a held-out year never
downgrades the ISO). The 2022 rung stays **NOT-YET on `price_mean` alone**.

Four independent findings, any one of which would stop an arm; together they close the
enumeration:

1. **The charter's handed-forward object is killed BEFORE a solve.** caiso-275 named CAISO
   *belly commitment* as the successor object, measured on **2024**. Re-pointed at **2022** it
   carries **+0.250 $/MWh of the +9.579 gap — 2.6 %** — and on the clock the belly **core is
   essentially unbiased** (hod 14 **−0.003**, hod 16 −0.049, hod 13 +0.113). A *perfect* belly
   repair cannot deliver −1.13. (§2)
2. **2022 is ONE object, not two — which falsifies a standing disclosure and removes the
   December lever.** The implied-marginal-heat-rate bias is **+1.024 MMBtu/MWh** across the 12
   months, and **December's +1.337 ranks 3 of 12, only +0.51 sd above the ex-December mean of
   +0.996**. The +$49.51 December gap is that ordinary bias × $37.02 gas. (§3)
3. **The commitment-reach hypothesis has almost no footprint, and all three named candidates
   are inert or wrong-signed at the code level.** Only **647.7 MW of 22,354 MW** of gas capacity
   is idle-while-in-the-money in the residual window. (§4, §5)
4. **Every remaining channel is closed on its own source data**, the offer curve included — and
   for `CT_CHP`, the largest single marginal carrier in the residual window (**28.8 %** of its
   marginal weight), closed on the **OASIS bid file's own provenance**. (§6, §7)

**Nothing here was selected by whether it moves C3a** (rule 1 `[R-STRUCT]`). §2/§3 *measure the
residual's location*, which is the object's description and what caiso-273 was chartered to do;
every **kill** below is a statement about a mechanism's own footprint, absorption arithmetic or
source provenance.

---

## §1 — G-REPRO: the instrument reproduces the committed keeper exactly

| quantity | this session | committed / published |
|---|--:|--:|
| model load-weighted price, 2022 | **94.069** | 94.07 |
| gated actual (`bench.avgLMP.rt_lw`) | 84.49 | 84.49 |
| gap | **+9.579 $/MWh** | +9.58 |
| gap % vs ±10 % band | **+11.337 %** | +11.3 % |
| **$/MWh needed to pass** | **−1.130** | −1.13 |
| total slack, 2022 | 0.000 MWh | — |
| total dump, 2022 | 0.000 MWh | — |

**BASIS RECONCILIATION, stated before any decomposition.** The **gate** is the committed bench
`rt_lw` = 84.49. This session's hourly reconstruction — the committed hourly RT series weighted
by the *model's* zonal demand — returns **83.759**, a **−0.731 $/MWh** weighting-basis artifact,
not a price error. Every decomposition below is therefore used for **SHAPE** (which hours and
months carry the gap) and **never quoted as the gate magnitude**. Where a monthly actual is
needed the committed `rt_lw_mon` is used directly, on the scorer's own `_CUM` calendar rather
than the 730-hour approximation caiso-273 §6.4 disclosed.

`slack = dump = 0.000` in all 8,760 hours: **the 2022 LP is never short and never long.** No
scarcity or oversupply mechanism has any purchase on this year — an ex-ante constraint on every
candidate below.

---

## §2 — THE HANDED-FORWARD OBJECT IS KILLED PRE-SOLVE

caiso-275 §1 measured, **in 2024**, that the real market keeps 7.2 GW of gas online in the
lowest net-load decile and *exports* while the model runs 1.5 GW and *imports*, and handed
CAISO commitment forward as the successor object. **That instrument re-pointed at 2022 says the
object is not there.**

### 2a — by net-load decile, ex-December (8,016 h)

| decile | net load MW | model | actual | gap | **annual contribution** | gas MW | import MW | solar MW |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **0** | 5,644 | 17.14 | 13.73 | +3.41 | **+0.250** | 2,013 | 2,745 | 11,802 |
| 1 | 10,344 | 51.38 | 33.94 | +17.44 | **+1.466** | 3,156 | 4,937 | 10,889 |
| 2 | 14,223 | 65.30 | 49.77 | +15.53 | **+1.414** | 4,477 | 5,998 | 8,939 |
| 3 | 17,123 | 71.00 | 62.63 | +8.37 | +0.725 | 5,085 | 7,210 | 3,985 |
| 4 | 18,811 | 70.50 | 64.27 | +6.22 | +0.529 | 6,382 | 7,419 | 2,296 |
| 5–7 | 20,130–22,930 | — | — | +4.39…+5.17 | +0.433/+0.401/+0.493 | — | — | — |
| 8 | 24,910 | 87.63 | 80.31 | +7.33 | +0.746 | 11,820 | 6,207 | 1,258 |
| 9 | 30,086 | 136.52 | 137.43 | **−0.91** | **−0.113** | 16,677 | 4,947 | 1,753 |

**Decile 0 — the belly, the object caiso-275 named — carries +0.250 of the +9.579 (2.6 %).**
The carriers are deciles 1–2 (+2.880 together, 45 % of the ex-December total), which sit at
10.3–14.2 GW of net load with 8.9–10.9 GW of solar still on: the **ramp shoulders of a
high-solar day**, not the belly floor.

### 2b — by hour-of-day, ex-December (the sharper cut)

| hod | model | actual | gap | contribution | gas MW | solar MW |
|--:|--:|--:|--:|--:|--:|--:|
| 6 | 77.90 | 66.94 | +10.96 | **+0.460** | 8,668 | 4,363 |
| 7 | 68.03 | 54.02 | +14.01 | **+0.598** | 6,258 | 8,269 |
| 8 | 60.32 | 43.38 | +16.95 | **+0.700** | 4,239 | 10,509 |
| 9 | 55.37 | 41.30 | +14.07 | **+0.561** | 3,969 | 11,359 |
| 12 | 55.60 | 49.69 | +5.92 | +0.241 | 4,661 | 11,570 |
| 13 | 58.74 | 56.04 | +2.69 | +0.113 | 5,125 | 11,371 |
| **14** | 63.82 | 63.88 | **−0.06** | **−0.003** | 5,780 | 10,666 |
| 16 | 83.33 | 84.40 | −1.07 | −0.049 | 8,816 | 5,172 |
| **17** | 100.67 | 115.31 | **−14.64** | **−0.699** | 10,942 | 1,784 |
| 19 | 111.31 | 93.62 | +17.70 | **+0.846** | 13,172 | 35 |
| 20 | 100.05 | 84.35 | +15.70 | **+0.727** | 12,599 | 21 |

* **hod 6–9 (+2.319) and hod 19–22 (+2.462) carry 69 %** of the ex-December within-subset gap.
* **The belly core hod 10–16 is essentially unbiased** — hod 14 is **−0.003**, hod 16 −0.049.
* **hod 17 carries a LARGE NEGATIVE (−0.699):** the model **under**-prices the market's own peak
  hour by $14.64. The actual price peaks at **hod 17** while model *and* measured demand peak at
  **hod 18** — the market prices the solar-drop **ramp**, which a perfect-foresight LP has no
  mechanism to price. That is a restatement of the existing C3c model-class limitation, not a
  new lever, and its sign is **against** closing C3a.

**A mechanism confined to the belly cannot reach a residual that lives in the shoulders and
partly cancels at hod 17.** This kill is arithmetic on the keeper's committed solution and cost
no LP.

### 2c — the clock hypothesis is falsified, so the shoulder signature is real

A one-hour misalignment between the committed actual series and the model's hour index would
manufacture exactly a shoulder-over / peak-under signature. It is ruled out three ways:

| check | result | verdict |
|---|---|---|
| C-1 model demand vs measured EIA-930 demand | argmax lag **−1 h** (0.97131 vs 0.96743 at 0 h) | margin 0.004 — a shape asymmetry, not an offset; **both peak hod 18** |
| C-2 committed actual RT LMP vs measured demand | argmax lag **0 h** (0.30714) | **PASS** — the actual-price series is on the measured clock |
| C-3 shift sweep, ±3 h (**reported, never used to choose an alignment**) | **lw bias +10.310 at 0 h, +10.528 at +1 h** | **the C3a bias is INVARIANT to shift, and the pearson-argmax shift makes it WORSE** |

C-3 is the load-bearing one: the *whole* level residual survives every alignment, so **no clock
or alignment repair can close C3a-2022.** (Choosing the shift that minimised the residual would
have been fitting the instrument to the answer; the sweep is reported for magnitude only.)

---

## §3 — 2022 IS **ONE** OBJECT: a gas-proportional marginal-offer bias. The December lever does not exist.

Implied marginal heat rate = load-weighted price ÷ the model's own capacity-weighted delivered
gas price, model against the committed monthly actual:

| month | gas $/MMBtu | model | actual | HR model | HR actual | **HR bias** | gap $ |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | 5.43 | 55.23 | 43.52 | 10.174 | 8.017 | **+2.157** | +11.71 |
| 2 | 5.24 | 50.65 | 38.96 | 9.667 | 7.436 | **+2.231** | +11.69 |
| 3 | 5.20 | 47.67 | 43.56 | 9.176 | 8.385 | +0.792 | +4.11 |
| 4 | 7.11 | 59.18 | 49.76 | 8.326 | 7.001 | +1.325 | +9.42 |
| 5 | 8.91 | 66.39 | 58.76 | 7.454 | 6.597 | +0.857 | +7.63 |
| 6 | 8.36 | 75.13 | 70.77 | 8.984 | 8.463 | +0.521 | +4.36 |
| 7 | 7.84 | 79.55 | 71.80 | 10.142 | 9.154 | +0.988 | +7.75 |
| 8 | 9.75 | 103.20 | 96.77 | 10.587 | 9.927 | +0.660 | +6.43 |
| 9 | 8.91 | 125.17 | 123.41 | 14.047 | 13.849 | +0.198 | +1.76 |
| 10 | 6.54 | 69.85 | 64.33 | 10.683 | 9.839 | +0.844 | +5.52 |
| 11 | 8.70 | 86.22 | 82.92 | 9.914 | 9.535 | +0.379 | +3.30 |
| **12** | **37.02** | **291.71** | **242.20** | 7.881 | 6.543 | **+1.337** | **+49.51** |

* **Mean bias +1.024, sd 0.642** — which reproduces caiso-270 §4's cross-ISO/cross-year mean of
  **+1.01** on 2022's own numbers, from a different construction.
* **December's +1.337 ranks 3 of 12 and is +0.51 sd above the ex-December mean (+0.996).**
  $1.337 \times 37.02 = \$49.5$ — **the whole December gap, to the dollar.**
* Normalising by gas **halves the dispersion**: the raw monthly gap has CV **1.26**, the
  gas-normalised form CV **0.627**.

**Two consequences, both binding on the charter.**

1. **caiso-273 §6.3's standing disclosure "2022 is two objects, not one" is FALSIFIED by
   measurement.** There is no separate December phenomenon: December is an ordinary month for the
   bias multiplied by a gas price 3.7× the year's mean, exactly as caiso-270 §4 said and as the
   caiso-276 charter §3 anticipated. **There is therefore nothing for a December-scoped lever to
   repair**, and such a lever would be month- and year-scoped, which rule 1 condition (b)
   refuses.
2. **The residual scales WITH gas, so it is not a non-fuel adder.** A VOM or carbon error
   divides by gas and must shrink in December; the measured December bias is *above* the
   ex-December mean. The residual lives in the `heat_rate × multiplier` product of whatever
   tranche is marginal — which is precisely the set of terms §6 shows is measured and spent.

**Carbon verified anyway, since it was the one unexamined term:**
`STATE_CARBON_PRICE_BY_ISO["CAISO"][2022] = 28.45 $/t` against the four 2022 CARB auction
settlements ($29.15 / $30.85 / $27.00 / $26.80, mean **$28.45**). **Exact.** Closed.

---

## §4 — THE THREE NAMED CANDIDATES: ALL INERT OR WRONG-SIGNED, ESTABLISHED AT THE CODE LEVEL

Read as code paths, not docstrings (charter §2). **None of the three can lower the 2022 price,
and none needed a solve to establish that.**

| candidate | consumer | verdict | why, at full magnitude |
|---|---|---|---|
| `caiso_lcr_commitment_credit` | `pipeline/commitment.py:2144`, **inside `run_commitment_pass`** | **INERT — structurally unreachable** | `run_commitment_pass` **is the archived P2 pass**, hidden behind `--enable-legacy-p2`; "No keeper uses it; it is not part of any default or recommended configuration" (CLAUDE.md *Dispatch & Commitment*). The keeper is scored on **P1**, so the flag cannot execute. **Second, independent** reason: the limb also requires `p1.lcr_dual is not None`, i.e. `local_capacity_constraints = True`, which is **False** on the keeper. |
| `caiso_ra_bridge_curtailment_release` | `pipeline/commitment.py:336–369` | **WRONG-SIGNED** | It computes `release_hours = curtail > EPS` and **removes** the bridge floor in those hours. It can only ever *reduce* committed belly gas — the **opposite** of the 5.7–7.6 GW belly deficit it would be armed to close, and the opposite of what lowers the belly price. Also gated on `renewable_potential_mw is not None`. |
| `caiso_ra_mustoffer_quantity_gate` | `pipeline/commitment.py:221–232` → `apply_ra_mustoffer_quantity_gate` | **INERT in 2023–25 and INADMISSIBLE in 2022** | The gate only ever **CAPS** (drops bridged plants cheapest-startup-first), so it can only *reduce* belly gas — wrong-signed. It was already measured a **no-op at HEAD** (bridged CC 13.7–13.8 GW inside the published 19,130 / 15,566 / 15,566 MW). **And `CAISO_RA_MUSTOFFER_GAS_MW` has NO 2022 row**: the code falls through to `max(keys)` = the **2025** vintage, i.e. it would price a 2022 obligation off a later publication — a vintage violation. A 2022 arm needs a 2022 DMM digitisation that does not exist. |

The armed bridge itself is real and working: D-2 attributes **4.1209 TWh** of forced CC_REGULAR
energy to `ra_mustoffer_bridge` in 2022 (7.75 % of the class, **PASS** against the 30 % rule-20
budget). The question the charter posed was its **reach**, and §5 answers it.

---

## §5 — THERE IS NO COMMITMENT REACH TO FIND, AND NO SEAM BINDING

### 5a — bound census (keeper's own assembled `mc_base` and `pmax × availability`)

| window | hours | price | gas cap MW | gas disp MW | **idle & in-the-money** | at bound MW | headroom MW |
|---|--:|--:|--:|--:|--:|--:|--:|
| shoulder hod 6-9 / 19-22, ex-Dec | 2,672 | 81.85 | 22,354 | 8,846 | **647.7** | 8,599 | 13,508 |
| belly core hod 10-16, ex-Dec | 2,338 | 63.53 | 22,353 | 5,666 | **500.9** | 5,050 | 16,686 |
| December | 744 | 291.71 | 25,335 | 7,666 | **631.6** | 7,363 | 17,668 |

"Idle & in-the-money" = a live gas tranche dispatching ≤1 % of its bound **while its own
assembled offer sits more than $0.25 below the clearing price** — capacity the market could have
used at that price and the model did not. **It is 647.7 MW of 22,354 MW (2.9 %) in the window
that carries the residual.** The model is **not** materially failing to commit in-the-money
capacity, so a wider RA must-offer reach has almost nothing to act on. Simultaneously there are
13.5 GW of headroom, so the efficient fleet is **not exhausted** either: the headroom above λ is
simply priced above λ.

### 5b — the seam is not binding, in any window

| window | import cap MW | import disp MW | headroom MW | utilisation | **hours ≥ 99 %** |
|---|--:|--:|--:|--:|--:|
| shoulder, ex-Dec | 16,371 | 5,559 | 10,812 | 0.3401 | **0** |
| belly core, ex-Dec | 15,440 | 4,607 | 10,833 | 0.3041 | **0** |
| December | 15,899 | 6,769 | 9,130 | 0.4263 | **0** |
| all 8,760 | 16,189 | 6,107 | 10,082 | 0.3726 | **0** |

**Import utilisation is 30–43 % and the corridor envelope binds in ZERO hours of 2022.** The
model is emphatically not import-constrained, which kills the "clears deeper because the seam is
exhausted" reading and independently corroborates caiso-275 Arm A from a fifth direction.

> **[CORRECTED IN PLACE 2026-09-13 — caiso-279 + caiso-280. The numbers above are each
> individually right; the bolded conclusion is FALSE for the object that actually binds.]**
>
> This table measures **PHYSICAL LINK** utilisation (`WECC_DSW>SP15_rest` 0.595,
> `WECC_PNW>NP15` 0.241 on Dec 29–31, against static TTCs of 10,623 / 4,800 MW). It does
> **not** measure the per-corridor **interface-group envelope**, which is a different LP row and
> is at utilisation **1.000**. caiso-279 measured the group rows from the arm A
> `hourly/network_2022.parquet`: `grp:+WECC_PNW>NP15` and `grp:+WECC_DSW>SP15_rest` sit at
> `limit_up` for **72/72 hours** of Dec 29–31 with duals **−285.41** and **−261.94** $/MWh,
> and bind **40.1 %** / **43.4 %** of all 8,760 hours and **95.4 %** / **92.1 %** of Dec 23–31.
> So "binds in ZERO hours" should read **"the physical links bind in zero hours; the measured
> import envelope binds in 93.1 % of Dec 23–31"**, and on those hours λ is set by an envelope
> shadow price rather than by any generator's offer.
>
> **caiso-280 then measured whether that envelope is WRONG, and it is not — the sign is the
> other way.** Against EIA-930 CISO BA-to-BA interchange, over Dec 23–31 the model imports
> **7,337.9 MW** against CAISO's actual **5,564.6 MW** net / **6,098.4 MW** gross — the model is
> **+1,773.3 MW (+31.9 %) over actual net and +1,239.5 MW over actual gross**, in 84.3 % of
> window hours, **267.7 GWh** over the 9 days. The envelope binds *above* what the market
> delivered. So §5b's headline claim — "the model is emphatically not import-constrained" —
> survives **in its consequence** (import quantity is not the route to the 2022 residual) while
> being wrong **in its mechanism** (the seam does bind; it simply binds generously). Full
> measurement: `docs/RESULT-caiso280-the-envelope-binds-above-the-actuals-2026-09-13.md`.

### 5c — what IS marginal, and the λ-in-a-gap share

| window | matched load share | **λ in a gap** | marginal HR (lw) | top marginal carriers |
|---|--:|--:|--:|---|
| shoulder, ex-Dec | 0.186 | **0.814** | **9.129** | `CT_CHP:econc00` 0.179, `CC_REGULAR:committed` 0.164, `CT_CHP:econc01` 0.110, `import:midC` 0.109 |
| belly core, ex-Dec | 0.164 | 0.836 | 7.922 | `CC_REGULAR:committed` 0.199, `import:clean` 0.163, `import:midC` 0.138 |
| December | 0.093 | 0.907 | 7.892 | `CC_REGULAR:econc01` 0.216, `econc05` 0.142, `committed` 0.141 |
| all 8,760 | 0.186 | 0.814 | 8.529 | `CC_REGULAR:committed` 0.171, `import:midC` 0.138, `CT_CHP:econc00` 0.108 |

Two things matter. **λ sits in a gap in 81–91 % of load weight** — no partially-loaded tranche
prices the hour — which reproduces caiso-272 §3.1's finding from a sixth direction. And the
shoulder window's marginal HR is **9.129** against 7.9 in the belly core and December: the
residual-carrying window is the window where the model clears into its **least efficient**
marginal tranches, and **`CT_CHP` is 28.8 % of that window's marginal weight** (econc00 +
econc01). That is the one candidate the standing record left open — and §6 closes it.

---

## §6 — THE OFFER CHANNEL IS SPENT, **INCLUDING `CT_CHP`** — closed on the OASIS file's own provenance, which CORRECTS caiso-273 §4(b)

caiso-273 §4(b) recorded, honestly, "one genuine unmeasured assumption … the armed config
applies the **CT_PEAKER** ladder verbatim to **CT_CHP and ST_GAS**, which have no measured band
set of their own", and dismissed it **on weight**, citing ST_GAS's 0.79 %. §5c shows the weight
argument was aimed at the wrong class: **CT_CHP carries 28.8 % of the shoulder's marginal weight
and 16.6 % over all 8,760 hours.** So the transfer had to be examined on its merits. It was, and
the answer is stronger than caiso-273's:

`data/raw/_validation-source/caiso_offer_curve_measured.json` → `_provenance.classifier`:

* `classes: [CC_REGULAR, CT_PEAKER, ST_GAS]`, `consumed_classes: [CC_REGULAR, CT_PEAKER]`
* **`contamination_note`: "CT bucket may include the 2.9 GW OTC/RMR ST_GAS steamers and priced
  CT_CHP; CC bucket may include CC_CHP. Same-fuel near-SRMC bidders; … masked ids preclude
  per-plant mapping."**

**`CT_CHP` IS ALREADY INSIDE THE MEASURED CT BUCKET.** Applying the CT ladder to CT_CHP is
therefore **applying a measured surface to a class it was measured over — the correct treatment,
not an ungrounded extrapolation.** And because the OASIS Public Bid Data are 90-day-lag **masked**,
a separate CT_CHP ladder is **structurally un-derivable from this source** — not merely
un-derived. (Independently: `data/raw/caiso-public-bids/` is a converted corpus whose payload is
9.7 KB of README at tip; recovery is re-fetch only, and a re-fetch returns masked ids too.)

**So caiso-273's conclusion stands and its stated reason is superseded**: the channel is spent
for CT_CHP on provenance, not on weight. `caiso_offer_surface_measured_ungrounded` — the flag
that performs this merge — is **already armed** on the keeper, and it is the *correct* posture.

**The one measured-but-unconsumed object, reported in full because it exists — and it is
wrong-signed.** ST_GAS's own measured ladder is derived and not consumed. Consuming it under
rule 14 `[R-ACCURATE]` would make ST_GAS offers **more expensive**, pushing price **UP**:

| band | ST_GAS measured (2023/24/25) | armed (transferred CT_PEAKER) |
|---|---|---|
| econ_low | **1.849 / 1.294 / 1.523** | 1.103 / 1.102 / 1.140 |
| econ_high | **1.628 / 1.217 / 1.389** | 1.132 / 1.184 / 1.167 |
| committed | 1.367 / **NaN / NaN** | 1.231 / 1.173 / 1.079 |

Three reasons it is not this session's lever, in order: it moves C3a the **wrong way**; its
`committed` band is **NaN in 2024 and 2025**, so it cannot be the "ONE config across EVERY
scored year" rule 1 condition (b) requires; and ST_GAS carries **0.332 TWh** in 2022 and appears
in the top-8 marginal census of **no** window. It is a legitimate future structural item under
rules 14/23 — **and it must never be selected on this residual.**

CC_REGULAR (1.066 / 1.072 / 1.386) and CT_PEAKER (1.103 / 1.146 / 1.154) remain **exactly** on
the measured surface (caiso-273 §4(b)), so resizing either moves *away* from CAISO's own bid
data — refused by rule 14.

---

## §7 — THE SWEEP IS EXHAUSTIVE, NOT ANECDOTAL: 27 unarmed CAISO-scoped flags, none admissible

Every CAISO-scoped boolean that is `False` on the keeper, screened against the §3 object (lower a
**gas-proportional marginal-offer level**, system-wide, every month, every year, admissibly):

| group | fields | disposition |
|---|---|---|
| **already adjudicated** (rule 28(a) DO-NOT-REDO) | `caiso_import_solar_shape` (**R**, caiso-275 Arm A), `caiso_import_hub_prices` (**I**, provably inert — DO-NOT-ARM), `caiso_zonal_gas_basis` (**R**, caiso-221/215), `caiso_p1_export_sink_seam` (**R**), `caiso_ra_mpb_capacity_anchor` (**O**, capacity-price) | closed; not re-tested |
| **rule-13 FORBIDDEN** | `caiso_gas_commitment_floor` | an energy floor pinned to the measured EIA-930 `NG: NG` outcome; refused absolutely |
| **wrong-signed — RAISES price** | `caiso_reserve_coopt`, `caiso_commitment_posture`, `caiso_reserve_online_scoped`, `caiso_locational_as_families`, `caiso_scarcity_import_headroom` (shortfall duals sum **into** the LMP; `caiso_reserve_coopt`'s own docstring says the build **over-states** scarcity ex-ante), `caiso_solar_cap_at_delivered` (cuts solar), `caiso_corridor_atc_forward` + `caiso_dsw_daytime_evening_trim` (cap/trim import depth), `caiso_dam_outages` (adds outages), `caiso_charge_allocation_schedule` + `caiso_storage_as_reservation` + `caiso_storage_adaptive_expectation` (constrain storage arbitrage) | cannot lower the level |
| **inert in a backcast** | `caiso_nqc_accreditation`, `caiso_storage_nqc_accreditation` | forecast capacity-screen objects |
| **commitment family** | `caiso_ra_mustoffer_quantity_gate`, `caiso_ra_bridge_curtailment_release`, `caiso_lcr_commitment_credit` | §4 — inert or wrong-signed |
| **topology, and the seam is measured NOT binding (§5b)** | `caiso_endogenous_wecc_node`, `caiso_fsno_subzonal_topology`, `caiso_reference_price_seam`, `caiso_intertie_reference_price` | 0 hours at ≥99 % utilisation; Arm A closed the import-offer route to the belly |

**`caiso_zonal_gas_basis`, corroborated rather than re-tested.** Its CAISO cell is already **R**
(mean-zero as a C3a instrument, sign-flipping spread). This session adds the 2022-specific datum
the existing evidence lacked: the measured N–S spread in **2022 is +0.085 $/MMBtu — the smallest
of the six covered years** (2020 −0.161, 2021 −0.902, 2023 −0.491, 2024 +0.539, 2025 −0.184).
So 2022 is the year of the mechanism's **weakest** measured footprint, and under rule 29
`[R-SCREEN]` the screen year would have to be 2021 (data-blocked) or 2024 — **never 2022**.
Verdict unchanged; evidence appended.

And the two physical terms the §3 object would have to live in are measured and armed: heat rates
(`egrid_family_heat_rates`, `measured_ct_heat_rates`, `measured_chp_heat_rates`) and gas prices
(`gas_daily_shape`, `gas_hub_basis_overlay`, `gas_monthly_actuals`,
`gas_plant_monthly_fuel_pricing`, `f923_gas_price_plausibility_screen`).

**Conclusion: there is no channel left that could deliver −1.13 $/MWh on 2022 admissibly.**

---

## §8 — TWO CORRECTIONS TO THE STANDING RECORD

1. **caiso-273 §6.3 — "2022 is two objects, not one" is FALSIFIED.** December's HR bias ranks
   3 of 12 and is +0.51 sd above the ex-December mean; the whole December gap is the ordinary
   bias × $37.02 gas (§3). This **confirms** caiso-270 §4 and removes the December half of the
   caiso-276 charter's §3 framing.
2. **caiso-273 §4(b)'s "genuine open untested transfer" is NOT a transfer for `CT_CHP`.**
   CT_CHP is inside the measured CT bid bucket by the source's own contamination note, and masked
   ids make a separate ladder un-derivable (§6). caiso-273's *conclusion* stands; its *reason*
   (weight) is superseded by provenance — which matters, because the weight argument cited
   ST_GAS's 0.79 % while CT_CHP carries 28.8 % of the residual window's marginal weight.

Both corrections **strengthen** the standing "offer channel is spent" position. Neither changes
any keeper, determination, gate or registered number.

---

## §9 — DISCLOSURES AGAINST INTEREST

1. **C3a-2022 IS NOT CLOSED.** The rung stays **NOT-YET** at +11.337 % against the ±10 % band.
   Rule 30(c): the ISO's determination is the train-tier verdict and is untouched — CAISO reads
   **CALIBRATED**. This session delivers a refusal, not a repair.
2. **§3 characterises; it does not diagnose.** "A gas-proportional marginal-offer bias of
   ~+1 MMBtu/MWh" says where the residual lives and which term it must live in. It does **not**
   name the missing supply, and a session that treated it as a diagnosis would be selecting a
   mechanism on a hunch — the same warning caiso-273 §6.1 attached to its own §5.
3. **The residual is not year-scoped and is therefore not a 2022 defect.** caiso-270 measured the
   same bias in 40 of 48 **CAISO** months and caiso-273 §1 measured a near-constant +2.70 $/MWh
   adder in 2023–2025 (CV 0.095). **2022 is the year the standing bias crosses the band because
   its gas price is highest, nothing more.** Closing it therefore means closing a **standing
   CAISO** object, not a held-out-year object — which is exactly why no admissible year-invariant
   lever is available for it.

   > **CORRECTION 2026-09-12 (caiso-277), against this session.** As first written this paragraph
   > said "40 of 48 **ISO-months**" and called the object **program-level**. **caiso-270 §4 says
   > "all 48 months of 2022-2025" and it is CAISO ONLY** — 4 years × 12 months of one ISO. Nothing
   > cross-ISO had ever been measured. caiso-277 measured it over all 288 ISO-months of all 24
   > registered keeper-years in all 7 ISOs, and **the program-level reading is FALSIFIED**: pooled
   > dHR is positive in only 59.0 % of ISO-months with a mean of **+0.037** (i.e. zero), and on
   > the common 2023–2025 window **CAISO is the ONLY significantly positive ISO** (+0.534,
   > t = +4.03) while **ERCOT (−0.625, t = −2.54) and PJM (−0.717, t = −2.87) are significantly
   > NEGATIVE** and four ISOs are indistinguishable from zero. The object is **CAISO-specific**.
   > This paragraph's "not a 2022 defect" claim SURVIVES — CAISO's positivity holds on 2023–2025
   > without its 2022 rung — but "program-level" does not.
   > `docs/FINDING-caiso277-the-bias-is-caiso-specific-2026-09-12.md` §0/§4.
4. **A correction against my own earlier reading, recorded because it nearly became a false
   finding.** An intermediate measurement appeared to show pumped storage pumping 1.6 GW at
   hod 18. That was a **mislabelled print header in my own probe**, not a model defect: the
   column was li-ion *discharge*. Verified against the writer (`_storage_frame`, a direct read of
   `result.storage_charge` / `storage_discharge` with no swap) and against all four years — the
   **net** storage shape is correct everywhere (charge hod 8–15, discharge hod 17–22; evening net
   discharge 1,618 / 2,452 / 4,453 / 5,730 MW in 2022/23/24/25, tracking real fleet growth).
   **Storage is not the object.**
5. **A real but wrong-signed vintage gap, stated so it is not mistaken for a lever.**
   `data/raw/reference/caiso-storage-shape-envelope.csv` covers **2023–2025 only**. For 2022
   `model/storage.py:1083` takes `max((y for y in env_years if y <= year), default=env_years[0])`
   → the generator is empty → **2022 silently borrows the 2023 envelope**. The docstring
   documents only the *above*-span case ("a solve year beyond the derived span reuses the latest
   measured year's shape"); the **below**-span `default` branch is undocumented. A 2022 fleet
   dominated by commissioning ramps plausibly had a *lower* p95 capability than 2023's, so the
   correct envelope would make the model's 2022 batteries **less** capable, **raising** the
   evening price — **against** closing C3a. Deriving a 2022 row is a legitimate rule-14/23
   data-intake item for a future session; it is **not** a C3a lever and must not be armed as one.
6. **`CAISO_RA_MUSTOFFER_GAS_MW` has no 2022 row** and falls through to the 2025 vintage (§4).
   Latent, not live — the gate is off on the keeper — but it would be a vintage violation the
   moment anyone armed the gate on 2022.
7. **The probe's hourly actual basis differs from the gate's by −0.731 $/MWh** (§1). Declared
   before any decomposition; every shape conclusion is robust to it, and no gate number is quoted
   from it.
8. **The 2,040-hour 2023 WECC intertie LMP coverage gap** (charter §5) was **not** repaired here —
   it is a real data-intake defect and it remains open. It is a 2023 object and could not bear on
   C3a-2022.
9. **The charter's §4 "free strengthening" was not available.** Re-testing the keeper's own G-2 on
   a wide-basis year requires a year with both a wide within-year gas basis spread and full hub
   coverage. This session intaked no data and unlocked no year, so 2022 remains the keeper's only
   discriminating year — the caiso-275 limitation stands **unchanged and unmitigated**.
10. **Rule 15 `[R-DASHBOARD]` produces no duty here**: zero LP, so there is no bundle and no run
    to register, keeper or rejected probe. Same posture as the zero-LP caiso-273/274 sessions.
11. **No 2020/2021 work.** They remain data-**blocked**, not skipped (caiso-274). Scorable years
    are 2022–2025.

---

## §10 — THE PROMOTION QUESTION, PUT EXPLICITLY (rule 31 `[R-RETAIN]`)

**There is nothing to promote, and nothing was deleted.**

* **No solve was run**, so **no bundle was produced** — the rule-31 "artifacts will not survive
  this ephemeral container" hazard does not arise for anything this session made. The only new
  artifacts are five probe scripts and five small JSON outputs under `results/calibration/`,
  reproducible from committed data in minutes.
* **Nothing was removed from local disk.** The caiso-275 per-year shard bundles
  (`caiso275_B_gascoupling_{2022,2023,2024,2025}`), the `_span` composite and the retained
  predecessor `caiso271_egrid_family_{2022,span}` are all **untouched**.
* **The keeper is unchanged** at `2026-09-12-caiso-275-gascoupling`, so
  `calibration-complete.json` and the forecast `program-status.json` gate-(a) row need **no
  re-key** (that duty attaches to a promotion, and there is none).

**The questions that are genuinely the owner's, not this session's:**

1. **Accept the refusal?** C3a-2022 stays NOT-YET on `price_mean` alone. Under rule 30(c) that
   costs the ISO nothing. The alternative — closing −1.13 $/MWh through a wrong-signed,
   provably-inert, vintage-violating or forbidden mechanism — is what rules 1/13/14 exist to
   prevent, and §0's four findings are each independently sufficient to refuse.
2. **Re-point the object?** §3 says the residual is a **standing, gas-proportional marginal offer
   bias present in 40 of 48 CAISO months**, not a CAISO-2022 defect — and §5c hands a starting
   instrument (**λ in a gap in 81–91 % of load weight**; shoulder marginal HR 9.129 vs 7.9
   elsewhere).

   > **CORRECTION 2026-09-12 (caiso-277) — THIS RECOMMENDATION IS WITHDRAWN.** As first written it
   > read "the honest venue is a **cross-ISO** marginal-offer-formation charter, not a CAISO
   > held-out-year lane", on the mistaken premise corrected at §9.3. caiso-277 ran that
   > measurement before any charter was acted on and **falsified its premise**: pooled over 288
   > ISO-months the bias is mean **+0.037** (zero), and on the common 2023–2025 window CAISO is
   > the **only** significantly positive ISO (t = +4.03) while ERCOT and PJM are significantly
   > NEGATIVE. Six ISOs run the same ISO-agnostic LP and none carries this bias. **The venue is
   > CAISO**, and the successor is a CAISO ablation census over CAISO's own armed distinctives —
   > not a program-level charter. Everything else in this section, and the whole refusal in §0–§7,
   > is unaffected: none of the four kills depended on the cross-ISO premise.
   > `docs/FINDING-caiso277-the-bias-is-caiso-specific-2026-09-12.md` §4b/§4c/§6.
3. **Two small data-intake items**, both offered and neither armed, both **wrong-signed for C3a**
   so neither can be read as a lever: a **2022 row** for the storage shape envelope (§9.5), and
   a **2022 DMM must-offer quantity** if the quantity gate is ever wanted on that year (§9.6).
   A third, from the charter and genuinely open: the **2,040-hour 2023 WECC intertie LMP** gap
   (§9.8).
4. **`ST_GAS`'s own measured ladder** (§6) is a real rules-14/23 fidelity item — derived,
   committed, unconsumed. It raises price, has NaN bands in two of three years, and is
   immaterial by weight. If it is ever done, it must be chartered **on the data** and never on
   this residual.

---

## §11 — RULE LEDGER

| rule | discharge |
|---|---|
| 1 `[R-STRUCT]` | No lever selected. §2/§3 measure the residual's *location*; every kill is a footprint, absorption or provenance statement. No arm, so no residual-driven selection was possible. |
| 13 `[R-MEASURED]` | `caiso_gas_commitment_floor` refused by name (§7). No adder/haircut/proxy proposed. |
| 14 `[R-ACCURATE]` | Two measured-over-estimate items surfaced (§9.5, §6) and **both reported with their sign against C3a**, so neither can be read as a residual repair. |
| 15 `[R-DASHBOARD]` | Zero LP ⇒ no bundle, no registration duty (§9.10). |
| 16 `[R-ALLYEARS]` | No solve, so no single-year bundle exists to mis-register. |
| 28(a) `[R-MECH-MATRIX]` | DO-NOT-REDO honoured: the five adjudicated cells (§7 row 1) were **not** re-tested; `zonal_gas_basis` gets corroborating evidence, not a new verdict. |
| 28(b) | CAISO shard cells `gas_commitment_bridge` and `zonal_gas_basis` re-stamped **this session**, with this doc as the citation. |
| 29 `[R-SCREEN]` | Phase 0 done first and it **killed the arm before any solve** — the outcome the rule is written to produce. |
| 31 `[R-RETAIN]` | Nothing deleted; promotion question asked explicitly (§10). |
| 32 `[R-SHARD]` | **The parent spent ZERO LP** and launched no shard, because zero-LP work stays in the parent by clause (a). |
