# FINDING — caiso-135: the committed-gas charter is **REFUSED on measured bytes**, and the standing `caiso_ra_min_load_frac = 0.570` disposition is a **BASIS ERROR** that must be withdrawn. The floor is multiplied by **PLANT** capacity, but 0.570 is a per-**TURBINE** turndown; measured on the consuming basis CAISO's own plants sit at **0.289–0.304**, and the keeper's 0.26 is already inside that band. The quantity gate is a verified **NO-OP**. And the belly deficit is not a commitment defect at all: on the same matched plants the model has **as many or MORE CC plants online than reality (1.01–1.13×)** while carrying only **0.74–0.80×** the MW. NO SOLVE, nothing armed (2026-07-28)

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED.** No mechanism armed,
no `ScenarioConfig` field added or changed, **no LP built and no solver called**.
This session is the D-gate charter its brief specified: derive-first, and the
gates decide. They decided **no**.

Instrument (committed): `scripts/probes/_caiso135_committed_gas_charter.py`
(sections A/B/C/D/E/R). It reproduces every number below from the keeper's own
committed `hourly/` + `legitimacy_diagnostics.json` sidecars plus CAMPD CA unit
conduct — no solve. The plant-basis statistic is additionally reproducible from
the standing tool: `scripts/data/derive_campd_gas_commitment_params.py --iso
CAISO --plant-basis` (new flag; the default per-unit invocation is
byte-identical, verified for CAISO **and** NYISO).

---

## §1 — what was asked, and the three answers

`FINDING-caiso134` §7 named the lane by elimination and handed forward two
objects. This session was chartered to run D1–D5 on committed bytes and arm the
lane **if and only if** every gate passed.

| the brief's gate | the answer |
|---|---|
| **D1** derive, don't pick | **FAIL — decisive.** The value is consumed on the **PLANT** basis; the charter's "physical 0.40–0.57" is a per-**TURBINE** statistic. On the consuming basis CAISO measures **0.289–0.304**, and the keeper's **0.26** is already inside the band (§2) |
| **D2** E1/E2 spillover | Not at risk from the *sign* (more min-load supply pushes λ down) — but the lever is **dispatch-near-inert**, already SOLVED at ±60 MW by caiso-119 (§6) |
| **D3** window + driver + forward story | Not reached: D1 refuses the parameter change, and D4 shows there is no second mechanism to declare |
| **D4** one mechanism | PASS structurally (CC_REGULAR is floored by exactly one mechanism) — but object 2, the quantity gate, is a **verified NO-OP** (§4) |
| **D5** forced budget | **PASS** with headroom at every candidate level. D5 is *not* what refuses this lane (§5) |

And the lane itself is re-framed by measurement: the belly gas deficit is **not
an under-commitment** (§7).

## §2 — §A: D1, the decisive gate. The floor is multiplied by PLANT capacity

`model/commitment.py::caiso_ra_mustoffer_min_gen` is explicit in its own
docstring — the floor is

```
target_mw = min(min_load_frac × plant_pmax, pmax[g])
```

> "the floor is the PLANT's minimum stable load (`min_load_frac × plant_pmax`)
> applied on its base tranche, **never a per-tranche fraction**"

and CAISO runs `plant_level_fleet=True` + `use_campd_bins=True`, so the plant
**is** the LP unit. The measured statistic must therefore be the **plant's**
minimum stable configuration.

Both bases, both conditioning conventions, on identical CAMPD CA bytes:

| year | UNIT full-op | **PLANT full-op** | UNIT online | PLANT online | plant/unit |
|---|---|---|---|---|---|
| 2023 | 0.5662 | **0.2891** | 0.3891 | 0.2433 | 0.511 |
| 2024 | 0.5697 | **0.3005** | 0.3863 | 0.2587 | 0.527 |
| 2025 | 0.5720 | **0.3041** | 0.3758 | 0.2188 | 0.532 |

Three things this settles:

1. **The reproduction is faithful.** The UNIT full-op column reproduces
   caiso-119's own derive — 0.565 / 0.570 / 0.570
   (`results/calibration/caiso119_minload_derive.json`) — to within 0.002. The
   conventions are matched, so the **only** difference between 0.570 and 0.29 is
   the **basis**.
2. **The ratio is ~0.52, and that is physics, not noise.** A 2×1 or 3×1
   combined-cycle plant's minimum stable *configuration* is one train at
   minimum, i.e. about half the per-train fraction expressed against full plant
   capacity. It shows up plant by plant: Mountainview holds 0.107 of its
   1,109 MW, Los Esteros 0.069 of 1,001 MW, Delta 0.290 of 870 MW.
3. **ERCOT's 0.574 agrees with the UNIT column for the same reason.** The
   60-Day-DAM LSL/HSL pairs are published per RESOURCE/train. caiso-119 read
   that agreement as cross-validation of its value; it is in fact confirmation
   that both are per-train — which is the wrong basis for a floor multiplied by
   plant capacity.

**The keeper's 0.26 is not a fitted value below physical turn-down.** It sits
inside the measured plant-basis band [0.219, 0.304] (union of both conventions),
0.03 below the full-op mid-point. caiso-118b's "physical LSL/HSL ~0.40–0.57" —
and this session's own charter premise, which inherited it — is a per-turbine
range.

## §3 — §R: the reality test, because a floor is a claim about what CANNOT happen

A min-load floor asserts the plant cannot sustain less. Measured on the plants
the floor would be applied to, as a fraction of the **model pmax** it multiplies:

| year | online plant-h | < 0.26 | < 0.30 | < 0.3756 | < 0.570 | median |
|---|---|---|---|---|---|---|
| 2023 | 108,161 | 7.5 % | 15.0 % | 21.9 % | **37.2 %** | 0.748 |
| 2024 | 99,111 | 9.2 % | 15.9 % | 20.0 % | **35.7 %** | 0.793 |
| 2025 | 91,752 | 9.4 % | 17.0 % | 22.8 % | **43.0 %** | 0.679 |

A 0.570 floor would be contradicted by CAISO's own fleet in **roughly two of
every five online hours**. That is not a minimum stable load; it is a per-train
number applied to a multi-train denominator. The keeper's 0.26 is the candidate
the measured record actually supports.

## §4 — §B: D4, and object 2 is a verified NO-OP

From the keeper's own committed `legitimacy_diagnostics.json` (no re-solve):

| year | class | mechanism | forced TWh | share |
|---|---|---|---|---|
| 2023 | CC_REGULAR | `ra_mustoffer_bridge` | 3.4867 | 7.21 % |
| 2024 | CC_REGULAR | `ra_mustoffer_bridge` | 3.5111 | 8.25 % |
| 2025 | CC_REGULAR | `ra_mustoffer_bridge` | 3.5208 | 9.89 % |
| 2023–25 | CT_PEAKER | `ra_mustoffer_bridge` | 0.0035 / 0.0046 / 0.0003 | 0.32 / 1.04 / 0.12 % |

CC_REGULAR is floored by **exactly one** mechanism, so a `min_load_frac` change
would have been a rule-19 `[R-ONE-MECH]`-clean *replacement* of that mechanism's
own parameter, not a stack. D4 is the one gate the charter would have passed.

**Object 2 — `caiso_ra_mustoffer_quantity_gate` — cannot bind on this keeper:**

| year | CC_REGULAR pmax | CT_PEAKER pmax | published cap | verdict |
|---|---|---|---|---|
| 2023 | 13,465 MW | 6,740 MW | 19,130 MW | NO-OP |
| 2024 | 11,670 MW | 6,746 MW | 15,566 MW | NO-OP |
| 2025 | 9,580 MW | 6,779 MW | 15,566 MW | NO-OP |

The gate drops bridged plants **cheapest-startup-first** (the RUC de-commitment
order), and CT starts ($12–25/MW) are below CC ($35–50/MW), so CT is dropped
first — and CT carries 0.1–1.0 % of its class as forced energy, so dropping it
is worth ~0. After CT, the kept CC fleet is under the published cap in **every**
year. The gate cannot remove one bridged CC plant. This confirms the
`ScenarioConfig` comment's 2026-07-07 G-61a measurement on the *current* keeper,
with more headroom than then (caiso-130's nameplate reconciliation shrank CC pmax).

**And the DRIVER reframe does not rescue it.** caiso-118b proposed wiring
`CAISO_RA_MUSTOFFER_GAS_MW` as an obligation *floor* rather than a cap. Two
independent refusals: (a) the code's own G-61 adjudication already named the
error — "the model bridges LESS capacity than reality obligates, so G-61's
over-commitment is **not** a quantity-scope error; the conflation of
must-**OFFER** with must-stay-**online** is"; a must-offer obligation is a
bid-insertion duty, not a must-run, so modelling it as an online floor is a
mechanism that is not real (rule 1 `[R-STRUCT]`); and (b) §7 below shows the
model does not lack committed plants in the first place.

## §5 — §C: D5 passes, and is not the refusal

Projected CC_REGULAR forced share at the plant-basis candidate 0.30, using an
upper bound that credits the floor on **every** online plant-hour:

| year | forced now | class TWh | share now | added TWh | share then | cap | verdict |
|---|---|---|---|---|---|---|---|
| 2023 | 3.487 | 48.37 | 7.21 % | 1.475 | 9.96 % | 30 % | PASS |
| 2024 | 3.511 | 42.56 | 8.25 % | 1.070 | 10.50 % | 30 % | PASS |
| 2025 | 3.521 | 35.61 | 9.89 % | 1.024 | 12.41 % | 30 % | PASS |

Rule 20 `[R-FORCED-BUDGET]` is comfortably clear at every candidate level. It is
worth stating plainly: **this lane does not die on forcing budget or on
spillover — it dies on the derive.**

## §6 — §D: D2, and the magnitude the charter did not know was already solved

The binding projection (upper bounds — the detector floors only *bridged* plants
across detected gaps, and the RA bridge owns just **1.8 % of ~1.33 M floored
cells**, `FINDING-caiso119` §1):

| year | window | online plant-h | load p50 | add MW @0.30 | add MW @0.570 |
|---|---|---|---|---|---|
| 2023 | belly | 10,162 | 0.272 | 352 | 1,909 |
| 2023 | evening | 36,049 | 0.901 | 70 | 392 |
| 2025 | belly | 7,392 | 0.442 | 176 | 1,082 |
| 2025 | evening | 27,071 | 0.934 | 59 | 326 |

Two reads:

* **The sign is favourable and E1/E2 were never the binding risk.** Price-taking
  min-load supply pushes λ *down*, and the evening column is the smallest — the
  model's evening CC plants already sit at 0.90–0.93 loading, far above any
  candidate floor, so a raised floor barely touches the hours caiso-134 §6 warned
  about.
* **The lever is already SOLVED and near-inert.** `FINDING-caiso119` ran the A/B:
  0.26 → 0.570 — a delta **2.2× larger** than anything the plant basis would
  justify — moved belly gas by **−28 / +59 / +52 MW**, closing 8–10 % of the gap
  at best. At the correctly-derived ~0.30 the delta is ~5× smaller again. There
  is no version of this parameter change that reaches C3a-2025.

## §7 — §E: the reframe. The belly deficit is a LOADING defect, not a commitment defect

caiso-118b's paradigm asserts the model commits too *few* gas plants. Measured on
the **same 28 matched CC plants**, in caiso-134's own defect window (Sep–Dec,
hod 10–15), with one shared online convention so neither side is advantaged:

| year | plants | model online | CEMS online | **on ratio** | model MW | CEMS MW | **MW ratio** |
|---|---|---|---|---|---|---|---|
| 2023 | 28 | 13.9 | 13.0 | **1.072** | 3,695 | 4,638 | **0.797** |
| 2024 | 28 | 11.7 | 10.4 | **1.129** | 2,749 | 3,670 | **0.749** |
| 2025 | 28 | 10.1 | 10.0 | **1.011** | 2,699 | 3,637 | **0.742** |

**The model has as many or MORE CC plants online in the belly than reality does,
and runs each one lower.** The ~940 MW belly deficit — which reproduces
caiso-134 §6's shape-normalised −1,081 to −1,574 MW on a different construction
— is entirely per-plant *loading* on plants that are **already committed**.

This is the finding that closes the lane rather than merely refusing its
parameter. A min-load floor is the wrong instrument by construction: **the plants
it would commit are already committed.** Energy *above* min-load is an economic
dispatch outcome, not a commitment-state one — so no commitment mechanism,
however specified, reaches this defect.

It also corrects caiso-118b's headline a second time. caiso-134 §7 already
corrected its "2–3.6× more belly gas" to 1.6–1.7× on the honest CEMS basis; this
corrects its *causal* claim — the shortfall is not uncommitted capacity.
(No contradiction with caiso-134 §3's "74–86 % of the replacement block is
OFFLINE": that ladder ranks the *cheapest replacement supply* across all CA
classes, and is dominated by CT_PEAKER and by CC plants **reality also has
off**. Restricted to the CEMS-matched CC fleet, the online counts match.)

## §8 — the verdict, and a standing disposition that must be withdrawn

**The charter is REFUSED. Nothing is armed.** D1 fails on basis, object 2 is a
measured no-op, and §7 removes the lane's premise.

**Governance action (rule 14 `[R-ACCURATE]`, rule 23 `[R-FROZEN-DERIVE]`).**
caiso-119/121/122 left a standing disposition that must not be carried forward:

> "the measured **0.570** is KEPT ... and is still the value the next keeper must
> carry" — `docs/calibration-log/caiso.md` caiso-121 §(3), caiso-122 §(4)

That disposition is **WITHDRAWN AS STATED**. 0.570 is a correct *per-turbine*
measurement and a wrong *per-plant* parameter; promoting it would assert a
minimum CAISO's own plants sit below in ~2 of every 5 online hours (§3). Rule 14
is not violated by this withdrawal — it is served by it: the accurate input is
the plant-basis statistic, and the estimate being displaced is the per-turbine
one. The identification source for any future keeper value is
`data/raw/_processed-legacy/campd_gas_commitment_params_plant_CAISO.csv`
(**0.259** pooled, cap-weighted p50; 0.289–0.304 on the full-operation
convention), never the per-unit artifact.

**No re-solve is warranted to move 0.26.** It is inside the measured band, and
§6 prices the whole parameter family as near-inert. If a future keeper touches
it for an unrelated reason, ~0.29–0.30 is the defensible value; on its own it is
not worth a solve.

## §9 — what this does and does not change

* **Keeper unchanged**, determination NOT-YET, fail set **{C3a-2025, C3c}**. No
  mechanism armed, no field changed, no solve — so **no dashboard registration is
  due** (rule 15 applies to completed runs; nothing was produced to register).
  Same disposition as caiso-134 §8.
* **Rule 28 `[R-MECH-MATRIX]`:** `caiso_ra_mustoffer_quantity_gate` moves to
  **`I` (inert)** for CAISO — measured no-op, this finding §4. No other cell's
  verdict moves; `caiso_ra_mustoffer` itself stays the armed keeper mechanism.
* **Code:** one additive, byte-safe change —
  `scripts/data/derive_campd_gas_commitment_params.py --plant-basis`. The default
  per-unit path is verified byte-identical for CAISO and for NYISO (whose
  0.523132 / 0.239362 are shipped bridge parameters). No `src/market_sim/` change.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. No year outside the training window
  was solved, scored or probed.
* **C3c untouched** — separate lane (asks A2/A3/A4). Ask A2's D2/D3 were again
  not reached; its re-specification (the two caiso-133 §7 corrections) remains
  open, and is now the strongest remaining candidate for the next session.

## §10 — DO-NOT-REDO (new, binding)

* **Raising `caiso_ra_min_load_frac` toward 0.40–0.57 as a CAISO lever.** §2: that
  range is a per-TURBINE turndown; the parameter is multiplied by PLANT capacity,
  where CAISO measures 0.289–0.304. §3 prices the error — a 0.570 floor is
  contradicted by CAISO's own plants in ~2 of 5 online hours. Any future proposal
  must cite the `_plant_` artifact, not the per-unit one.
* **Re-deriving `caiso_ra_min_load_frac` on the per-unit basis, or citing
  ERCOT 0.574 / NYISO 0.523 as corroboration of a CAISO plant-basis value.** §2:
  those agree with the UNIT column *because they are also per-train*. Rule 25
  `[R-ISO-SCOPE]` — and, here, rule 5 `[R-NO-MAGIC]`: a measured value must be
  defined on the basis its consumer multiplies.
* **Re-solving the `min_load_frac` A/B to reach C3a-2025.** §6: SOLVED by
  caiso-119 at a 2.2× larger delta for ±60 MW of belly gas, because the RA bridge
  owns 1.8 % of floored cells. The plant-basis delta is ~5× smaller again.
* **Arming `caiso_ra_mustoffer_quantity_gate` as a cap.** §4: verified NO-OP on
  the current keeper in all three years, with the RUC drop order making the CT
  headroom irrelevant.
* **Wiring `CAISO_RA_MUSTOFFER_GAS_MW` as a commitment DRIVER / obligation
  floor** (the caiso-118b reframe). §4: must-OFFER is a bid-insertion duty, not
  must-stay-online — the code's own G-61 adjudication already named the
  conflation — and §7 removes the premise it was built on.
* **Proposing that the CAISO belly deficit is an under-COMMITMENT of gas
  plants.** §7: on the same 28 matched plants the model has 1.01–1.13× reality's
  online plant count and 0.74–0.80× its MW. Any future belly-gas candidate must
  address per-plant LOADING above min-load, and must state up front why a
  commitment mechanism could reach a defect on already-committed plants.

Carried forward unchanged: everything in `FINDING-caiso134` §9 (above all — the
corridor lane is CLOSED for C3a-2025 in BOTH directions, the `dsw_*_clean` depth
family is refuted for this defect, every import rung is priced exactly on its own
measured hub, "CA gas is offered too high" is closed on the fuel anchor, and the
raw EIA-930 CISO `NG`/`Demand` cells are never a midday anchor),
`FINDING-caiso133` §9, `FINDING-caiso132` §10, `FINDING-caiso131` §10,
`FINDING-caiso130` §7, `FINDING-caiso129` §6 and `FINDING-caiso127` §7.

Next number: caiso-136.
