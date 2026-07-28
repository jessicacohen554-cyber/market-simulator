# FINDING — caiso-134: the excess midday import is **ONE tranche** (`DSW_surplus_clean`), and **NEITHER side's PRICE is misplaced** — the import rungs sit on their own measured hubs to the cent ($0.00/$4.00/$5.00 wheel, exactly), and the CA replacement band's implied delivered gas tracks the measured SoCal citygate to ±$0.3/MMBtu in 2024-25. The defect is a **QUANTITY/STATE** one on the CA side: on the SAME 81–82 physical plants, the model's gas fleet runs at **0.58–0.63×** reality's own belly utilisation, and **74–86 % of the CA supply that would replace the excess import is OFFLINE capacity** the model would have to START. **The lane is the caiso-118b RA must-offer committed-gas state.** And the counterfactual is priced: tightening the corridor would move CA λ **+$14.40 to +$17.92/MWh the WRONG way** — an independent, quantitative confirmation of caiso-133 §5's refusal.

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED. NOTHING ARMED** — no
mechanism, no flag, no new `ScenarioConfig` field, **no solve of any kind**.
This session is measurement-only on committed bytes, per its charter and the
caiso-127 §5 / standing charter rule: a diagnosis session names a lane, it does
not build a mechanism.

Instrument (committed): `scripts/probes/_caiso134_import_demand_source.py`
(sections A–E). It reproduces every number below from the keeper's own
committed `hourly/` sidecars plus `run_year(fleet_only=True)` — **no LP is
built and no solver is called**.

---

## §1 — what was asked, and the three answers

`FINDING-caiso133` §6 handed C3a-2025 back from the corridor lane and filed one
observation without chartering it: the measured cap binds because the model
*wants* ~2 GW more import than reality took, so the pressure is **upstream of
the corridor**. This session was chartered to find where, and to stop there.

| the brief's question | the answer |
|---|---|
| **1.** Who is the marginal import displacing? | CA `CC_REGULAR` — but **74–86 % of it is OFFLINE**, and buying it costs **+$14.40 to +$17.92/MWh** (§3) |
| **2.** Price or quantity? | **Neither price.** Both sides sit on their own measured anchors (§4, §5). It is a **quantity/state** construction (§6) |
| **3.** The lane | The **CA-internal committed-gas state** — the caiso-118b RA must-offer paradigm, unchanged on this keeper (§7) |

Defect hours throughout: **Sep–Dec, hod 10–15, measured RT ≤ $20** — the
caiso-120/121 convention that caiso-132 and caiso-133 reuse, so every row
composes with them on one basis. n = 192 / 239 / 229 h.

## §2 — §A: the excess is **one tranche**, and it is not the one that is capped

| year | `DSW_surplus_clean` | firm self-scheduled<sup>†</sup> | other | tranche output | dumped at WECC | delivered | measured | **excess** |
|---|---|---|---|---|---|---|---|---|
| 2023 | **2,665** (util 0.551) | 522 | 109 | 3,296 | −70 | 3,226 | 756 | **+2,540** |
| 2024 | **1,995** (0.631) | 2,557 | 346 | 4,898 | −161 | 4,737 | 2,882 | **+2,016** |
| **2025** | **2,638** (0.691) | 2,863 | 66 | 5,569 | −307 | 5,262 | 3,510 | **+2,059** |

<sup>†</sup> `DSW_solar_PV` + `PNW_hydro_base` — held at static contract cost by
`caiso_perhub_firm_base` **and** floored at their shaped capability by
`caiso_firm_import_selfschedule` (must-flow). At util **1.000** in every year
they are a QUANTITY, not a price: no offer change can move them.

Two facts the table settles:

* **The excess IS `DSW_surplus_clean`**, in all three years (2,665 / 1,995 /
  2,638 against an excess of 2,540 / 2,016 / 2,059). Every other economic rung
  is inert here — `DSW_CT` and `WECC_scarcity` are at **0.000** utilisation in
  all three years, `PNW_midC` at 0.007–0.018, `DSW_CCGT` at 0.002–0.098.
* **That tranche is INTERIOR** — 55 / 63 / 69 % of its own measured WEIM depth.
  **Its depth is therefore NOT the binding object**; the corridor group is
  (caiso-133 §3/§4, settled analytically *and* from the duals). A proposal to
  re-derive the clean-tranche depths cannot reach this defect: the LP is not
  short of depth, it is short of corridor.

**Side observation, recorded not chartered.** Tranche output is not delivered
flow: **70 / 161 / 307 MW** of self-scheduled firm PNW hydro is **DUMPED** at
the `WECC_PNW` node because the PNW corridor cap cannot carry it, and
`λ_WECC_PNW` collapses to a **median −$26.00/MWh** (mean −$10.03 in 2025) while
the measured MALIN hub prints **+$26.23**. That is a real interaction between
`caiso_firm_import_selfschedule` (a must-flow floor) and
`caiso_corridor_flow_limit` (a cap derived from *total* measured corridor net
import, not the firm block's own share). It is growing — 70 → 161 → 307 MW —
and it is filed here as an observation with no charter, exactly as
caiso-133 §6 filed its own.

## §3 — §B: who the marginal import displaces, and what it would cost

The CA replacement ladder: every CA unit's unused headroom, sorted by its own LP
offer, per defect hour. Headroom priced *below* λ is excluded — the LP already
took what it could there, so what remains is held back by another row (the hydro
monthly budget, storage SOC) and is not replacement supply.

**2025 (CA λ = $26.31, excess = 2,059 MW), mean MW/h:**

| offer − λ | ONLINE | OFFLINE | total | cumulative | top classes |
|---|---|---|---|---|---|
| +$0 … +$2 | 28 | 291 | 319 | 319 | CC_REGULAR 181, hydro 113 |
| +$2 … +$5 | 75 | 589 | 664 | 983 | CC_REGULAR 412, hydro 225 |
| +$5 … +$10 | 107 | 1,588 | 1,695 | **2,678** | **CC_REGULAR 1,653** |
| +$10 … +$20 | 34 | 1,653 | 1,686 | 4,365 | CC_REGULAR 1,548 |
| +$20 … +$50 | 193 | 7,678 | 7,871 | 12,236 | CT_PEAKER 3,585 |

Solved per hour rather than off the band means:

| year | CA λ | excess | **replacement cost at the margin** | CA λ would become | **ONLINE share** |
|---|---|---|---|---|---|
| 2023 | 23.42 | 2,540 | **+$17.92** (med +18.05, p90 +35.05) | 41.34 | 20.5 % |
| 2024 | 17.49 | 2,016 | **+$14.40** | 31.89 | 26.4 % |
| **2025** | **26.31** | **2,059** | **+$15.90** | **42.21** | **13.9 %** |

Two load-bearing reads:

1. **Tightening the corridor is quantitatively the wrong direction.** Against a
   measured actual of $9.06 (2025), CA λ is already +$17.24 too high in these
   hours; forcing the model to import only what reality imported would take it
   to **$42.21**, i.e. +$33 over actual. caiso-133 §5 refused the corridor
   relaxation on rule 1 / rule 14 grounds; this prices the *opposite* move and
   refuses it on the same grounds. **Both directions of the corridor lane are
   now closed with numbers.**
2. **The replacement supply is not expensive because its fuel is expensive — it
   is expensive because it is OFF.** Only **13.9 %** (2025) of the block the LP
   would have to buy is headroom on an already-running unit. The other 86 % is
   capacity the model would have to START, and an offline unit's first MW carries
   its whole offer, while a committed unit's min-load block is a price-taker.
   That is the signature of a commitment-state defect, and it is what §4/§5 then
   confirm by elimination.

## §4 — §C: the IMPORT side is priced **exactly** on its own measured hub

Rule 13 `[R-MEASURED]` is explicit that a claim the import rungs are wrong must
be made against **their own source**, never against the residual. Measured, in
the defect hours, LP offer minus that rung's own measured hub print:

| tranche | 2023 | 2024 | 2025 | what it should be |
|---|---|---|---|---|
| `DSW_overnight_clean` | **+0.00** | **+0.00** | **+0.00** | raw hub, no wheel |
| `DSW_daytime_clean` | **+0.00** | **+0.00** | **+0.00** | raw hub, no wheel |
| **`DSW_surplus_clean`** | **+4.00** | **+4.00** | **+4.00** | hub + OATT wheel |
| `PNW_midC` | +5.00 | +5.00 | +5.00 | hub + OATT wheel |
| `DSW_CCGT` | +16.22 | +17.04 | +14.38 | hub + wheel + border carbon (EF 0.37) |
| `DSW_CT` | +22.17 | +23.38 | +19.43 | hub + wheel + border carbon (EF 0.55) |
| `WECC_scarcity` | +20.14 | +21.08 | +18.01 | hub + wheel + border carbon (EF 0.428) |
| export legs | −0.00 | −0.00 | −0.00 | hub − ε |

Every rung reproduces `inject_caiso_per_hub_intertie_prices`'s formula
`hub + wheel + border × EF/EF_unspec + ε` **to the cent, in all three years**.
The marginal rung — `DSW_surplus_clean` — is the measured Palo Verde print plus
its $4.00 OATT wheel and nothing else (EF 0, so no border carbon). The two firm
rungs sit at static contract cost ($28 / $48) *and* are self-scheduled must-flow,
so their price cannot bind by construction.

**Neither "offered too low" nor "too deep" survives.** Too low is refuted above.
Too deep is refuted by §2: the tranche is interior at 55–69 %, so its depth is
slack — and in any case a *deeper* cheap rung would push λ **down**, which is the
opposite of the C3a-2025 defect's sign.

## §5 — §D: the CA side is **not** offered too high against its own fuel anchor

The replacement band's offer, decomposed into its own parts (capacity-weighted
over the band's gas-burning headroom), against the **measured SoCal citygate
weekly print**:

| year | band | offer | = fuel | + VOM | + net-rev margin | + carbon | **implied gas** | **measured citygate** | Δ |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | +$5…+$10 | 43.95 | 28.04 | 2.00 | 4.65 | 9.27 | **3.68** | **5.38** | **−1.70** |
| 2024 | +$5…+$10 | 37.53 | 20.23 | 2.03 | 4.08 | 11.20 | **2.69** | **2.40** | **+0.29** |
| **2025** | **+$5…+$10** | **43.45** | **30.04** | **2.00** | **3.96** | **7.44** | **4.07** | **3.94** | **+0.13** |

* The **fuel input tracks its own measured anchor** — +$0.13/MMBtu in 2025
  (≈ +$0.97/MWh at HR 7.43), +$0.29 in 2024, and **−$1.70 in 2023** (the model
  *below* the weekly print). The sign flips across years, so this is print-cadence
  noise, not a systematic inflation.
* The **`gas_offer_net_revenue_margin` term is $3.96/MWh — 9.1 % of the offer**
  in 2025 (and only $0.15, 0.4 %, on the *online* CC_REGULAR block). It is the
  measured CAMPD offer conduct at its registered anchor ($4.7964/MMBtu), not a
  residual-fitted adder.
* The **carbon term ($7.44) is the CA cap-and-trade allowance leg**
  (`state_carbon_pricing`), a published price.

Every part of the CA offer is anchored to something measured, and the total is
where those parts put it. **"CA's midday supply is offered too high" is refuted.**

## §6 — §E: the CA side's **quantity** is where the defect is — measured on the honest basis

The raw EIA-930 CISO `NG` cell **cannot** be used as a midday anchor:
`FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12` showed it carries a fabricated
noon-peaked, solar-shaped block from ~2024-05 (it prints 79.0 TWh of 2025 CAISO
gas against the bench's honest CEMS-grid + cogen 51.6 TWh). So this compares
against **CAMPD hourly CEMS on the SAME physical plants**, each side normalised
by its **own annual mean**, which makes the comparison level-free:

| year | plants | model belly util | **CEMS belly util** | **shape ratio** | shape-normalised deficit | vs import excess |
|---|---|---|---|---|---|---|
| 2023 | 82 | 0.442 | 0.767 | **0.575** | **−1,574 MW** | 62 % of +2,540 |
| 2024 | 81 | 0.448 | 0.746 | **0.600** | **−1,263 MW** | 63 % of +2,016 |
| **2025** | **81** | **0.527** | **0.834** | **0.632** | **−1,081 MW** | **53 % of +2,059** |

("util" = defect-hour mean ÷ that side's own annual mean. The deficit is
`CEMS_defect × (model_annual / CEMS_annual) − model_defect`, i.e. what the model
would run in these hours if it merely reproduced the real fleet's own belly
shape at the model's own gas level.)

**The real CAISO gas fleet runs at 75–83 % of its own annual average in these
hours. The model runs at 44–53 %.** That single shape defect accounts for
**53–63 %** of the corridor over-import, level-free — and the hour-of-day profile
shows the compensating excess sits in the evening (Sep–Dec h19 util 1.83 model
vs 1.45 CEMS in 2025; h22 1.80 vs 1.44). The model's gas is too *peaky*: it backs
the fleet off midday and over-runs it at night, which is the duck-curve
exaggeration caiso-118 named.

**And the model has no zero-cost margin to price the belly with.** Solar
curtailment in the defect hours is **0.41 % / 0.69 % / 0.01 %** and wind is
**0.00 %** in all three years. Every renewable MW is at its cf × cap bound and
inframarginal, so nothing in the model's own stack can set a near-zero belly
price the way curtailed solar sets reality's $9.06.

## §7 — the verdict: the lane is the committed-gas STATE, and it is caiso-118b's

By elimination on measured anchors — import price exact (§4), import depth slack
(§2), CA fuel anchored (§5), CA renewables at cap (§6) — the only object left is
**how much CA gas is COMMITTED in the belly**, and §3 confirms it directly from
the LP: 74–86 % of the replacement supply is offline.

This is not a new hypothesis. It is **`FINDING-caiso118b`'s RA must-offer
commitment paradigm**, and this session's contribution is to (a) reproduce it on
the **current** keeper (caiso-118/118b ran on `2026-07-19-caiso-102-hourfix`),
(b) re-measure it on the **honest CEMS basis** rather than the corrupt EIA-930
NG cell caiso-118 used (its "2–3.6× more belly gas" is **1.6–1.7×** shape-normalised
plant-for-plant, so the effect is real but smaller than first reported), and (c) localise
it to the **exact C3a-2025 defect hours** and tie it one-for-one to the corridor
over-import.

**The two objects caiso-118b named are still exactly as it left them** on this
keeper's `run_config.json`, four sessions later:

| object | keeper value | caiso-118b's reading |
|---|---|---|
| `caiso_ra_min_load_frac` | **0.26** | physical LSL/HSL is ~0.40–0.57 |
| `caiso_ra_mustoffer_quantity_gate` | **False** | `CAISO_RA_MUSTOFFER_GAS_MW` (19.1/15.6/15.6 GW, DMM Annual Report) is wired only as a CAP, never as the commitment DRIVER |

**Nothing is proposed here.** Chartering a candidate in this lane is a separate
owner act, and it must clear the ask memo §2 envelope — above all **E1
(2025 spillover ≤ +$0.00)**, with only −$0.31 of band room. One directional note
for whoever writes that charter, offered as a prior and **not** as a gate: more
committed belly gas adds price-taking min-load supply, which pushes the belly λ
**down**, which is E1's favourable direction — but the same mechanism moves the
**evening**, where §6 shows the model already over-runs gas by ~25 %, and that is
where an E1/E2 pre-check would have to be run.

## §8 — what this does and does not change

* **Keeper unchanged**, determination NOT-YET, fail set **{C3a-2025, C3c}**. No
  mechanism armed, no `ScenarioConfig` field added, no gate re-scored, **no
  solve** — so no dashboard registration is due (nothing was produced to
  register; rule 15 applies to completed runs).
* **The corridor lane stays closed in BOTH directions** for C3a-2025 — caiso-133
  §5 refused relaxing it; §3 here prices tightening it at +$14.40 to +$17.92/MWh
  the wrong way.
* **The clean-tranche depth family is refuted for this defect** (§2: interior at
  55–69 %, so depth is slack) — which also re-refutes, on the current keeper, the
  caiso-106/107 depth lane for the C3a-2025 hours specifically.
* **C3c was not touched** — separate lane (asks A2/A3/A4). Ask **A2's D2/D3 were
  not run**; the optional second item was not reached, and A2's re-specification
  (the two caiso-133 §7 corrections) remains open.
* **Rule 20 `[R-HOLDOUT]`**: 2023–2025 only. No year outside the training window
  was solved, scored or probed. **Rule 26 `[R-MECH-MATRIX]`**: no mechanism was
  tested, so no cell's verdict moves; the matrix is unchanged by design.

## §9 — DO-NOT-REDO (new, binding)

* **Re-measuring which tranche carries the corridor over-import.** §2: it is
  `DSW_surplus_clean` in all three years, with `DSW_CT` and `WECC_scarcity` at
  exactly 0.000 utilisation and `PNW_midC` / `DSW_CCGT` under 10 %. The committed
  instrument re-runs it with no solve.
* **Proposing to re-derive, deepen or trim the `dsw_*_clean` import DEPTHS to
  close C3a-2025.** §2: the marginal tranche is INTERIOR at 55–69 % of its own
  measured depth, so the depth is slack and cannot be the binding object; and a
  deeper cheap rung moves λ the wrong way.
* **Proposing to reprice ANY CAISO import tranche against the residual.** §4:
  every rung reproduces its own measured hub plus its registered wheel and border
  carbon **to the cent** in all three years. A reprice proposal must first show
  the *hub series* or the *wheel* wrong against its own source.
* **Proposing that CA gas is offered too high (heat rate, margin, fuel level) as
  the C3a-2025 lever.** §5: the replacement band's implied delivered gas tracks
  the measured SoCal citygate to −$1.70 / +$0.29 / +$0.13 $/MMBtu — the sign flips
  across years — and the net-revenue margin is 9.1 % of the offer at its
  registered anchor. This is additionally already closed for C3c by
  `FINDING-caiso131` §10.
* **Tightening the corridor import envelope (the mirror of caiso-133 §9).** §3
  prices it: +$17.92 / +$14.40 / +$15.90 /MWh onto a λ that is already
  +$14.06 / +$8.74 / +$17.24 too high.
* **Using the raw EIA-930 CISO `NG` cell (or `Demand` cell) as a midday anchor
  for CAISO gas or load.** Both are corrupt for this purpose —
  `FINDING-caiso-c2c4-bench-basis-930ng` (the fabricated noon-peaked block) and
  the `caiso_supply_consistent_demand` / caiso-80 owner-signed replacement. Use
  matched-plant CAMPD CEMS and the supply-consistent series, as §6 does.
* **Re-measuring belly solar/wind curtailment as a candidate for a $0 marginal
  rung.** §6: 0.41 / 0.69 / 0.01 % solar and 0.00 % wind. This re-confirms
  `FINDING-caiso118`'s suspect-1 refutation on the current keeper.

Carried forward unchanged: everything in `FINDING-caiso133` §9 (above all, the
corridor lane is CLOSED for C3a-2025 and the binding envelope is a correct
measured input), `FINDING-caiso132` §10, `FINDING-caiso131` §10,
`FINDING-caiso130` §7, `FINDING-caiso129` §6 and `FINDING-caiso127` §7. Notably
still binding: `caiso_endogenous_wecc_node` is not re-armable; the
allocation-floor and AS-award families are CLOSED; the extract basis is frozen
(caiso-123 / neiso-66 ACTIVE) and C3a-2025 is a GUARD, never a tuning target.

Next number: caiso-135.
