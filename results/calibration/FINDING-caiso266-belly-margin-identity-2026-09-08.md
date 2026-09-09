# FINDING — caiso-266: the shoulder-month object **IS** the belly object — verified by composition, not inferred — and it lives in ~1,000 h/yr in which the market clears **BELOW the carbon+VOM cost of a CAISO CC burning FREE GAS**. The renewable-floor family is killed with zero LP (the model prices *correctly* wherever it spills). The offer-level door reproduces caiso-229's sign closure on the NEW caiso-255/257 classifier. **No mechanism survives Phase 0; no solve is earned. ZERO LP.**

**Session caiso-266, 2026-09-08**, branch `claude/kind-einstein-vd2l4s`.
Pre-registered in `PRECOMMIT-caiso266-belly-margin-identity-2026-09-08.md`,
pushed before M11 and M12 were computed — and whose §0 discloses, against
interest, that the M0–M10 reads preceded it.

Keeper **`2026-09-06-caiso-260-b1-demand`** (`caiso260_demand_vintage`)
**UNCHANGED — CALIBRATED** (rubric v3.6, 8 scored, 0 FAILs, one ledgered C3c
caveat). Touchpoint `2026-09-07-caiso-262-2022-touchpoint` unchanged.
**No LP built, no solver called, no `ScenarioConfig` field, no derive re-run,
no bundle produced, no run registered, no keeper change, no determination
moved.** CAISO's `complete` marker and the tier-scoped holdout freeze are
untouched; **every read stayed inside 2023–2025** (rule 22 `[R-HOLDOUT]`).
G-CTRL **form 4** — the keeper's committed bundle is the control; no control
solve (rule 29(b)).

Instrument: `scripts/probes/_caiso266_belly_margin_identity.py` →
`results/calibration/_caiso266_belly_margin_identity.json`. Every figure below
regenerates from committed bytes in about a minute.

---

## §1 — The result, in five lines

1. **Rule 19 `[R-ONE-MECH]` identity: CONFIRMED by composition.** caiso-265 §6
   disclosure 4 flagged "same object as caiso-121/131/140" as an inference. It
   is now a measurement: the belly-hour bin contributions reproduce caiso-131's
   `actual < $60` term **to two decimals** (+5.735 vs its +5.72 in 2023), and
   the composition of the carrying hours is the standing over-import /
   CC-side lane. It is the same object on a seasonal axis. Work it here.
2. **The whole residual is generated below $20 actual and partly refunded
   above $45.** The `< $20` bins carry **146 % / 119 % / 107 %** of the annual
   C3a gap.
3. **The renewable-floor family is DEAD, and this is a new kill.** Split by the
   model's *own* price regime, the hours in which the model is at its
   renewable/dump floor carry **−0.287 / +0.102 / −0.129 $/MWh** of gaps of
   +1.331 / +2.352 / +1.728. **Where the model spills, it prices correctly.**
   Deepening, graduating or re-deriving the negative-offer floor cannot reach a
   residual that is not there.
4. **The carrying population is ~1,000 h/yr (h6–h15, spring-weighted) in which
   the model is thermal-marginal at $26–29 and the market cleared at $7–10** —
   and in **70.5 % / 81.7 % / 56.2 %** of them the market cleared *below* the
   **carbon + VOM** cost of a CAISO CC with **zero fuel cost**
   ($16.01 / $16.94 / $13.90 per MWh; CARB allowance alone is $12–15/MWh at the
   measured 7.442 heat rate). No fuel price, no heat rate and no admissible band
   multiplier puts a CAISO gas unit on the margin there.
5. **Every named route moves it the wrong way, is already fenced, or is
   arithmetically out of reach.** M11 (pre-registered) reproduces caiso-229's
   sign closure on the *new* classifier; the local-curtailment object
   (caiso-232) makes this residual **worse** if repaired; the over-import is
   **helping** in these hours; storage is fenced by caiso-256 on the correct
   basis. **No PRECOMMIT for a screen is filed and no LP is earned.**

## §2 — M0: the seasonal statement is not a denominator artifact

caiso-265 measured `corr(percentage error, actual price)` = −0.575 over the 36
training months. A constant additive bias would produce that mechanically, and
the object would then be "a level bias", not a seasonal one. It is not:

| statistic (36 training months) | value |
|---|--:|
| `corr(` **absolute $/MWh** `error, actual price)` | **−0.572** |
| `corr(` percentage error `, actual price)` | −0.575 |
| mean absolute error | +2.68 $/MWh |
| range | −4.73 … **+10.62** $/MWh |

The error is larger **in dollars** where prices are lower. The seasonal
ordering is structural. (Worst: 2024-05 +$10.59, 2023-05 +$10.62, 2024-04
+$7.51. Best: 2023-07 −$4.73, 2024-07 −$2.05 — the model is *cheap* in
mid-summer.)

## §3 — M1: where the gap is generated, and the hole in the distribution

Decomposed on the actual-price axis, on ONE weight vector (the model's own
hourly demand) applied to both sides, so the bins sum to the printed gap:

| actual-price bin | 2023 contrib | 2024 | 2025 |
|---|--:|--:|--:|
| `< $0` | +0.491 | **+1.328** | +0.557 |
| `$0–10` | +0.473 | +0.546 | +0.476 |
| `$10–20` | +0.981 | +0.919 | +0.821 |
| `$20–30` | +1.212 | +1.201 | +1.065 |
| `$30–45` | +1.789 | +1.049 | +1.197 |
| `$45–60` | +0.789 | −0.589 | −0.937 |
| `$60–100` | −2.044 | −0.931 | −1.048 |
| `> $100` | −2.361 | −1.172 | −0.404 |
| **annual gap** | **+1.331** | **+2.352** | **+1.728** |

The `< $20` bins alone carry **+1.945 / +2.793 / +1.854** — 146 % / 119 % /
107 % of the gap — and the `> $45` bins refund −3.62 / −2.69 / −2.39. This is
caiso-131 §2's distribution compression, re-measured on the current keeper.

**The hole.** The market spends **625 / 739 / 723** hours in `[$0, $15)`; the
model spends **251 / 259 / 279** — about 2.6× fewer. The model's price
distribution is bimodal (floored, or thermal-marginal at $25–40) against a
continuous one, which is caiso-232's diagnosis reproduced on the price axis.

## §4 — M3: the floor kill — where the model spills, it is RIGHT

Splitting every hour by the model's own regime — **F**: every zone at or below
the renewable/dump floor (the model is spilling); **M**: some CA zone floored;
**G**: every CA zone priced off a positive dual:

| | hours | contrib | model | actual |
|---|--:|--:|--:|--:|
| **2023 F** | 337 | **−0.287** | −15.38 | −5.72 |
| 2023 M | 195 | +0.105 | 21.45 | 15.81 |
| **2023 G** | 8,228 | **+1.513** | 58.48 | 55.53 |
| **2024 F** | 609 | **+0.102** | −15.36 | −18.16 |
| 2024 M | 191 | +0.218 | 16.63 | 6.39 |
| **2024 G** | 7,960 | **+2.032** | 40.46 | 37.53 |
| **2025 F** | 528 | **−0.129** | −13.26 | −11.23 |
| 2025 M | 396 | +0.230 | 19.99 | 13.94 |
| **2025 G** | 7,836 | **+1.626** | 39.89 | 37.65 |

**The F regime contributes essentially nothing, and is NEGATIVE in two of three
years.** The armed `negative_renewable_offers` floor (−$20 solar / −$26 wind,
matrix cell `K`) does its job where it engages: the model's spill-hour mean is
−$15.4 / −$15.4 / −$13.3 against actuals of −$5.7 / −$18.2 / −$11.2.

**This kills a whole candidate family before a solve, and it is the most
intuitive family** — deepen the floor, graduate the single-step curtailment
offer into a continuous curve, re-derive `renewable_keep_running_value`. Every
one of them changes the price **only in hours where a renewable is marginal**,
and those hours carry no residual. A future session should not spend an LP
here.

## §5 — The composition of the carrying hours, the rule-19 identity, and a basis trap I fell into

**The population.** Regime **G** *and* actual `< $20`: **1,001 / 1,222 / 1,020
hours**, carrying **+2.025 / +2.450 / +1.671** — i.e. more than the whole
annual gap, in 11–14 % of the year. Concentrated at **h6–h15** (peak
contribution at h7–h9, ≈ nothing at h17–21) and in **Mar–Jun** (2024: 1,274 of
1,980 sub-$20 hours). Model **dump is 0.000 MW in every one of them** — the
model is never spilling here.

**What they are made of** (mean MW):

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model λ / actual | 29.28 / **9.40** | 26.04 / **6.81** | 26.45 / **10.39** |
| model solar / metered CISO solar | 9,266 / 8,051 | 10,418 / 8,383 | 12,056 / 9,931 |
| model import / metered CISO net import | 4,027 / **2,400** | 4,343 / **2,628** | 4,387 / **2,780** |
| model battery charge / metered `NG: OTH` | 1,211 / 799 | 2,174 / 1,725 | 3,589 / 2,926 |
| model pumped-storage charge | 1,093 | 845 | 955 |
| LA_BASIN − WECC_DSW (model's own nodes) | **+6.03** | **+11.38** | **+9.78** |

Over-import, over-delivered solar (the missing *local* curtailment, caiso-232 /
caiso-216) and a binding DSW→CA corridor: **that is the caiso-121 / -131 §7 /
-140 lane, in the hours that carry the residual.** Rule 19 is satisfied on the
evidence, not on the signature.

### §5.1 — CORRECTION AGAINST INTEREST: the EIA-930 gas-basis trap

**I made an error here and I am recording it because a future session will hit
the same wall.** Comparing the model's gas dispatch to EIA-930 `NG: NG` for
CISO reads:

> model 2,130 / 2,459 / 2,351 MW vs "measured" **5,722 / 7,131 / 7,826 MW** —
> the model is 3.6–5.5 GW short of belly gas.

**That number is wrong.** `NG: NG` is the whole CISO *balancing authority's*
gas; the model's fleet is the committed **85-plant CAMPD panel** the run is
actually scored against. On the correct panel (§6) the model's belly gas is
right to within **+381 / +183 / −72 MW**. This is the same class of error
caiso-256 named in caiso-255b (the all-tech-vs-PS-excluding storage basis), and
it points the same way: **the interesting hypothesis was the artifact.**

## §6 — M10: the commitment state — same energy, one third the committed fleet

On the bench's own 85-plant CAMPD gas panel (27.2–27.8 GW nameplate), in the
carrying hours:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| measured **online capacity** | **7,204** | **7,080** | **5,952** MW |
| measured generation | 2,511 | 2,641 | 2,278 MW |
| measured **loading when online** | **0.349** | **0.373** | **0.383** |
| model gas dispatch | 2,130 | 2,459 | 2,351 MW |
| measured − model generation | **+381** | **+183** | **−72** MW |
| model gas at binding floors | 813 | 1,004 | 1,103 MW |
| *(CC_REGULAR)* measured online / model gen | 5,036 / 1,127 | 5,659 / 1,543 | 4,580 / 1,447 |

**The volume is right; the commitment is not.** CAISO's meters show ~6–7 GW of
gas online in the belly at **35–38 % loading** — a fleet held on at minimum
load for the evening ramp, which is *price-taking*. The model makes the same
energy from a much smaller committed set running higher up its own curve, so
its marginal MW is a **cost-based CC economic rung**.

This is why the two markets price $16–20 apart on identical gas volumes, and it
is a **conduct** difference, not a quantity one. It also **reproduces caiso-229
Door B's closure independently**: forcing the measured online set on at its
measured loading yields ≈ 2.5 GW of energy against the model's existing
2.1–2.5 GW — a net move of a few hundred MW, against a stack that would need
GW to shift λ by $19.

## §7 — M11 (PRE-REGISTERED): the offer-level door is CLOSED, on the new classifier

Re-asked under rule 28(a) only because the classifier changed: caiso-254/255
found the CT bucket contaminated by gas steamers, re-cut it at the measured
heat-rate antimode, and caiso-257 promoted that re-cut. That is new evidence
about the *instrument*, so the door is legitimately re-opened for one read.

| CC_REGULAR band | keeper armed | measured pooled 2023–25 | below armed? | per-year measured |
|---|--:|--:|:--:|---|
| `committed` | 1.000 | **1.030** | no | 1.042 / 1.022 / 1.071 |
| `econ_low` | 1.066 | **1.066** | no (equal) | 1.063 / 1.027 / 1.085 |
| `econ_high` | 1.072 | **1.072** | no (equal) | 1.060 / 1.099 / 1.098 |
| `peak` | 1.386 | **1.386** | no (equal) | 1.306 / 1.503 / 1.457 |

**Verdict CLOSED — 0 of 4 pooled bands sit below the armed value.** Three are
*exactly* the armed value (the keeper is already on the measured surface); the
fourth, `committed`, is measured **above** it, so a measured-faithful repair
moves the belly price **UP**. caiso-229's sign closure reproduces, and the
classifier re-cut that moved every CT band left the CC bands where they were.

**Reported at full magnitude, and why it is not a route:** `econ_low` is below
the armed value in 2 of 3 *per-year* readings (1.063, 1.027). A per-year
multiplier is inadmissible — rule 1 `[R-STRUCT]` condition (b) requires ONE
config across every scored year — so it cannot be selected, and picking a
pooled value that split the difference would be selecting on the residual,
which condition (c) refuses. The pooled number is the admissible one and it is
already armed.

## §8 — M12: my pre-registered kill bar FAILED; the substantive kill is the carbon floor

**The pre-registered rule did not fire, and I record that as a failure rather
than re-cutting it.** §4 of the PRECOMMIT set the bar at "MW to be displaced
> 2× the economic gas available". Measured: **1.62 / 1.69 / 1.88×**. Under my
own rule the offer channel is *not* closed on that arithmetic.

The kill comes from a statistic I did **not** pre-register, and it is much
stronger:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| CARB allowance (run basis) | $33.03/t | $35.23/t | $28.06/t |
| CC **carbon + VOM at ZERO fuel** (0.057 t/MMBtu × 7.442 + $2 VOM) | **$16.01** | **$16.94** | **$13.90** /MWh |
| CT_PEAKER equivalent | $23.95 | $25.31 | $20.87 /MWh |
| actual clearing price, carrying hours | **$9.40** | **$6.81** | **$10.39** |
| **share of carrying hours below the CC zero-fuel floor** | **70.5 %** | **81.7 %** | **56.2 %** |
| share below $0 | 16.7 % | 23.6 % | 12.8 % |

**VERIFIED, because this leg is load-bearing:** the keeper actually charges this
cost. `run_config.json` carries `state_carbon_pricing: true` with
`carbon_price: 0.0` (no federal/scenario carbon on top), and
`STATE_CARBON_PRICE_BY_ISO["CAISO"]` is **exactly** the $33.03 / $35.23 / $28.06
the measured offer surface's own `carbon_basis` uses — so the floor above is
inside the model's gas offer, not only inside reality's. **Sensitivity:** the
0.057 t/MMBtu factor is the committed surface's; at EPA's 0.05306 for pipeline
gas the floor is **$15.04 / $15.91 / $13.08** and the shares move to
**65.0 / 76.5 / 51.7 %** (measured, not estimated). The conclusion does not turn
on the factor.

**In the majority of the hours that carry the entire C3a residual, the market
cleared below what a CAISO combined-cycle costs with its fuel given away free.**
California cap-and-trade alone puts a $12–15/MWh floor under every CA gas
offer. There is no fuel price, no heat rate and no band multiplier of any
magnitude that puts a CAISO gas unit on the margin at that price — so the
model's only route to reality's belly price is a **non-thermal** margin, i.e.
the spill regime, which §4 shows it reaches too rarely and prices correctly
when it does.

That is the honest shape of the residual: reality's belly is priced by
**price-taking supply below its own cost floor** (self-scheduled Pmin gas held
for the evening ramp, RA/RMR obligation, self-scheduled imports), which a
cost-based LP has no admissible mechanism to represent.

## §9 — Three routes that a future session will reach for, and why each fails

1. **Represent the missing local curtailment** (caiso-232's named object:
   1.97 / 2.96 / 2.91 TWh/yr of solar the 3-zone network cannot strand).
   **It moves this residual the WRONG way.** As a derate
   (`caiso_solar_deliverability`) it *reduces* delivered solar, so more gas is
   needed and λ rises. As sub-zonal topology it is `caiso_fsno_subzonal_topology`,
   verdict **R**, and caiso-230's DO-NOT-REDO item 2 is the structural reason:
   C3a is a zone-hour load-weighted mean, so a mean-preserving zonal
   redistribution moves dispersion, not λ. The object is real and is a C3b /
   D-A lane; it is not this one.
2. **Relax the binding DSW→CA corridor** so CA reaches its own cheaper import
   node (the spread is +$6.03 / +$11.38 / +$9.78 in exactly these hours).
   **Closed on the measured volume**: the model already imports **+1,627 /
   +1,715 / +1,608 MW** more than CISO's metered net interchange in these
   hours, and **+8.9 / +8.5 / +3.4 TWh** more across the year. Letting more
   import in cannot be a rule 14 `[R-ACCURATE]` repair when the meters say the
   model over-imports already. The over-import is *helping* λ here; correcting
   it makes this residual worse.
3. **Storage.** Fenced by caiso-256 on the correct battery-only basis: the model
   **under**-discharges (0.94 / 0.94 / 0.94 of metered), and every candidate —
   `battery_dispatch_adder`, a cycling/degradation cost, `storage_daily_cycling`,
   an SOC/duration bound — moves battery volume the wrong way. What survives is
   a **shape** statement, reported not proposed: the model charges its (correct)
   annual battery energy in **2,526 / 2,613 / 2,781** hours against the meters'
   **4,754 / 4,790 / 4,392**, and over-charges the carrying hours by
   **+412 / +450 / +663 MW**. That is the perfect-foresight concentration
   signature and it belongs to the unfunded S2 storage-shape item (caiso-127,
   caiso-201), not to a new lever.

## §10 — Disclosures against interest

1. **The precommit was late.** M0–M10 ran before it existed; the PRECOMMIT §0
   says so in full. Only M11/M12 are pre-registered tests. Mitigating, but not
   excusing: no mechanism was selected on M0–M10, two of them are kills, and
   one is the self-caught error in §5.1.
2. **My pre-registered M12 bar failed** (§8). The kill rests on an
   unregistered statistic. It is arithmetic on published CARB prices and the
   committed measured heat rate rather than a chosen threshold, but a reader
   should weight it as a post-hoc statistic, not as a passed test.
3. **§5.1 is my own error, found and corrected in-session.** It would have
   supported a much more interesting conclusion ("the model is 3.6–5.5 GW short
   of belly gas"); on the correct panel that conclusion evaporates.
4. **The demand side is NOT compared.** The keeper's demand is the caiso-80
   supply-consistent series, a different construction from EIA-930 `Demand`;
   the two differ by 1.5–4.0 GW in these hours and I make no claim from that
   difference. It is a basis gap, not a measured error.
5. **"The market clears below cost" is inference from two measured numbers**
   (the CARB-implied floor and the cleared price), not a reading of anyone's
   bids. The committed `caiso-public-bids` corpus could test it directly on the
   thermal side; I did not fetch it (it is a gitignored corpus, re-fetch only).
6. **The `< $20` cut is not a natural boundary.** It is the top of the M1 bin
   ladder, fixed before the regime split was computed, and the conclusions are
   stated on the bins as well as on the cut so a reader can move it.
7. **I installed pandas/pyarrow/numpy** into this container (absent at session
   start) to read parquet. No solve stack was used; no LP was built.

## §11 — Queue

1. **The renewable-floor family is CLOSED** (§4). Do not spend an LP on floor
   depth, a graduated curtailment offer curve, or a re-derived
   `renewable_keep_running_value` for this residual.
2. **The offer-level door is CLOSED on the current classifier** (§7). It
   re-opens only if the *measured surface* moves, never on the residual.
3. **The object's honest name is a conduct limitation** (§6, §8): reality's
   belly price is set below the cost floor of the fleet a cost-based LP can
   represent. The one instrument that could turn that from inference into
   measurement is the **thermal side of the committed OASIS `PUB_DAM_GRP`
   corpus** — caiso-178 landed the storage side and caiso-231/242/254/255 the
   gas *classification*; nobody has read what CAISO's gas fleet actually **bids
   at Pmin in the belly**. If those bids are at or below $0, the object is
   named, measured and permanently closed as a model-class limitation; that is
   an owner **funding** question (a corpus re-fetch), not a lever.
4. **Carried unchanged:** the 2021 rung is double-blocked (a 60-day RTM gap
   2021-08-02..09-30 plus a `CAISO_PARTIAL_YEARS` amendment CAISO cannot grant
   itself); `check_bench_freshness` engine drift on the CAISO 2023/24/25 bench
   parts; caiso-265 §4's `rt_lw` retrofit, still INERT until a 2022 re-solve
   rewrites the bench part (C3a would move +21.1 % → +13.3 % **with no code
   change in its diff** — the NYISO-148 silent-part failure mode).
5. **The caiso-265 §3 reading stands and is sharpened:** the CAISO C3a pass is
   carried by its load-weighting. The monthly structure is wrong, the reason is
   now located to ~1,000 hours and sized, and no admissible in-model repair
   exists at this grain.

**No keeper change. No `ScenarioConfig` field. No offer-curve channel used. No
determination changed. No mechanism-matrix VERDICT moved — evidence appended to
the two cells this session measured (`negative_renewable_offers`,
`gas_offer_curve_tranches`) per rule 28(b). Next number: caiso-267.**

## §12 — Reproduction

`python3 scripts/probes/_caiso266_belly_margin_identity.py` →
`results/calibration/_caiso266_belly_margin_identity.json`. Zero LP; committed
inputs only (the keeper's `hourly/` sidecars, the committed actual-LMP
reference, the committed `bench/CAISO/<y>.json.gz` CAMPD panel, the EIA-930
`CISO hourly` extract, the committed measured offer surface, the keeper's
`run_config.json`).
