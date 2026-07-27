# FINDING — caiso-118 BELLY PRICE-FORMATION: both handoff suspects REFUTED — the model belly clears at gas (~$26) not solar (~$15) because it UNDER-COMMITS belly gas, not because solar is suppressed (it is 98% absorbed) or imports are mispriced (the WECC border is already cheap but corridor-capped). Reality runs 2–3.6× MORE belly gas than the model yet clears at ~$15 — the committed gas bids its min-load DOWN (must-take, never marginal), so the belly clears at curtailed solar / the min-load block; the model economically backs gas off to a ~2–4 GW duck trough and OVER-IMPORTS to fill, so full-MC gas/import sets the belly at ~$26. C3a-belly-overprice and C5a-belly-overimport are ONE defect (the missing committed-gas STATE), not two coupled-and-opposed lanes. Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}) (2026-07-24)

**Derive-first, NO SOLVE, nothing registered** (the caiso-115/116/117 precedent).
Keeper unchanged. This session was chartered (the caiso-117 redirect) to make the
model belly clear near actual ~$15 before re-arming the belly VOLUME cap, by
testing one of two named suspects: (1) a curtailable-solar $0 marginal rung, or
(2) pricing belly imports at the measured (low) belly hub. A derive-first pass
**refutes both** and identifies a third, unifying mechanism. All numbers
reproduce from committed artifacts + raw EIA-930 via
`scripts/probes/_caiso118_belly_price_derive.py` (no LP). The keeper carries no
`hourly/` sidecar, so the model work uses the same-machine keeper-proxy
`caiso104_m1_B` (reproduces the keeper belly price digit-for-digit: 2024 model
belly $26.17 vs the caiso-117 handoff's keeper $26.3).

---

## Headline

The caiso-117 handoff framed the belly over-price as a **supply-price** problem —
either solar can't set the belly dual (suspect 1) or imports are priced too high
(suspect 2). The derive shows it is a **commitment-STATE** problem, and the
smoking gun is a single comparison:

| year | model belly gas | ACTUAL belly gas | model belly LMP | actual belly LMP |
|---|---|---|---|---|
| 2023 | 4,260 MW | **8,461 MW** (2.0×) | $42.5 | ~$15 |
| 2024 | 3,721 MW | **9,633 MW** (2.6×) | $26.2 | $14.9 |
| 2025 | 2,947 MW | **10,537 MW** (3.6×) | $24.4 | ~$15 |

**Reality runs 2–3.6× MORE gas through the belly than the model, yet clears
LOWER ($15 vs $26).** That is only possible if reality's belly gas is COMMITTED
and bidding its min-load DOWN (avoidable cost ≈ $0) — inflexible must-take while
the unit is on for the evening ramp, so its bid never sets the margin; the belly
then clears at curtailed solar / the min-load block (~$15). The model does the
OPPOSITE: it economically de-commits that gas (CC_REGULAR backs down to a
~2 GW duck trough at h10–11) and OVER-IMPORTS to fill the belly (3.1–3.9 GW model
vs 0.7–1.8 GW actual), so full-MC gas / the marginal import tranche sets the
belly at ~$26. This is the exact pattern ERCOT-63 proved
(`DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §5–7): **"the model needs
the STATE, not the PRICE."**

C3a-belly-overprice and C5a-belly-overimport are therefore **the same defect** —
the missing committed-gas belly STATE — not two coupled-and-opposed lanes fighting
over the import corridor. One mechanism fixes both (rule 15).

---

## Inv 1 — the model belly clears at the domestic full-MC gas / marginal-import blend, ~$10–27 above actual

CA load-weighted belly (hod 10–15) price, keeper-proxy `caiso104_m1_B`:

| year | model belly | model evening | actual belly | CA-zone spread |
|---|---|---|---|---|
| 2023 | $42.5 | $67.1 | ~$15 | uniform ($39.4 all zones) |
| 2024 | $26.2 | $43.6 | $14.9 | uniform ($19–23) |
| 2025 | $24.4 | $44.3 | ~$15 | uniform ($17–22) |

- The belly is over-priced by **+$10 to +$27**; the evening is UNDER-priced
  (they partially cancel in the annual C3a mean — the compression caiso-102/112
  named).
- **All CA zones clear uniformly** in the belly (no internal congestion) — a
  system-wide marginal unit, not a zonal artifact. This re-confirms caiso-111
  (dump = 0 in every CA zone; zone granularity is not the lever) and kills any
  zonal-granularity belly delta by construction.
- The marginal unit tracks the **residual after cheap supply** (Inv 3), not gas
  price: 2025 has the HIGHEST gas ($3.52) yet the LOWEST belly ($24) — because it
  has the most solar and the smallest residual, so the marginal unit is a cheap
  import, not gas. In 2023 (least solar, biggest residual) the belly is highest
  ($42, above CC_REGULAR's ~$32 MC — a peaker/scarcity rung).

## Inv 2 — SUSPECT 1 REFUTED: solar is ~98% absorbed; a $0 curtailable-solar rung is inert

`caiso_solar_endogenous_spill` is ON in the keeper, so the pre-LP deliverability
derate is **already SKIPPED** — the LP gets the FULL solar potential and may spill
it endogenously (the intended "solar becomes marginal in oversupply, crashing the
dual" mechanism the handoff's suspect 1 asks for is **already armed**). Measured
belly spill:

| year | solar dispatched | solar potential | belly SPILL | hrs spilling |
|---|---|---|---|---|
| 2023 | 11,333 MW | 11,393 MW | **60 MW (0.5%)** | 98 / 2190 |
| 2024 | 13,513 MW | 13,793 MW | **280 MW (2.0%)** | 500 / 2190 |
| 2025 | 15,047 MW | 15,287 MW | **240 MW (1.6%)** | 539 / 2190 |

Solar is **already at its upper bound** (98–99.5% absorbed) — there is NO
suppressed solar pool for a "$0 curtailable rung" to unlock. Adding one is inert
(solar is inframarginal, at bound), and RE-enabling the deliverability derate
would REMOVE solar (cap it below potential) and RAISE the belly price — the wrong
direction. The model even dispatches **MORE** utility solar than reality
generates (2024: 13.5 vs 12.4 GW belly; annual 47.2 vs 44.6 TWh), so it is not
solar-short. **Suspect 1 is refuted with data.**

## Inv 3 — the belly is oversupplied by ~4 GW (storage charge + export), yet prices at gas

| year | belly demand | residual after cheap* | belly import | belly gas | total supply − demand |
|---|---|---|---|---|---|
| 2023 | 22,886 | 6,144 | 3,075 | 4,260 | — |
| 2024 | 23,352 | 4,497 | 3,889 | 3,721 | **+4,038 (charge+export)** |
| 2025 | 21,850 | 1,865 | 3,757 | 2,947 | — |

\*cheap = solar + wind + nuclear + hydro + biomass.

The model belly is **supplied beyond demand by ~4 GW** (storage charging +
export) yet still prices at full-MC gas. Reality charges its batteries from
curtailed in-state solar / the committed-gas min-load (~$0–15); the model charges
from full-MC gas ($26) because its belly gas is NOT committed at a bid-down
min-load — the charging demand pulls incremental full-MC gas onto the margin.

## Inv 4 — SUSPECT 2 REFUTED/COUPLED: the WECC border is ALREADY cheap but corridor-capped; repricing is a VOLUME lever

The model's OWN solved WECC import-node duals in the belly are **already low**;
the CA belly sits ~$20–36 ABOVE the PNW border:

| year | model WECC_PNW | model WECC_DSW | CA belly | corridor belly cap | model import |
|---|---|---|---|---|---|
| 2023 | $6.3 | $28.7 | $42.5 | 3,896 MW | 3,075 MW |
| 2024 | $4.0 | $14.6 | $26.2 | 4,261 MW | 3,889 MW |
| 2025 | $2.6 | $16.0 | $24.4 | 4,411 MW | 3,757 MW |

- The cheap border energy ($2.6–6.3 PNW) does **not** set the CA belly because
  the corridor is **at/near its cap** (2023: 3,075 of 3,896; the cheap firm +
  DSW-clean tranches fill it) and the next AVAILABLE economic import tranche
  (PNW_midC $36 ladder / measured hub $24.8–33.9) is priced **above** CA's
  domestic gas ($24–30). So the model imports up to what's economic and clears CA
  at domestic gas — the border price is the firm/self-scheduled node basis, not an
  economic import CA can tap.
- The suspect-2 premise ("belly imports priced at the annual hub ~$26, not the low
  belly hub") is **false**: the belly hub series the model reads is already
  DSW $10.5 / PNW $28.6 (2024), and the DSW clean-depth tranches are already
  armed at it. Repricing the remaining economic tranches DOWN to the border would
  pull **more** import in — a **VOLUME lever** that worsens C5a (the coupling the
  caiso-117 handoff warned of). It is not a C5a-neutral price lever.

**Suspect 2 is refuted (border already cheap) / coupled (repricing = volume).**

## Inv 5 — the unifying mechanism: the model UNDER-COMMITS belly gas

The killer comparison (Headline), with the demand/solar context:

| year | belly gas M/A | belly demand M/A | belly solar M/A | net-import M/A |
|---|---|---|---|---|
| 2023 | 4,260 / **8,461** | 22,886 / 24,117 | 11,333 / 10,725 | 3,075 / **651** |
| 2024 | 3,721 / **9,633** | 23,352 / 25,650 | 13,513 / 12,443 | 3,889 / **1,341** |
| 2025 | 2,947 / **10,537** | 21,850 / 26,536 | 15,047 / 13,852 | 3,757 / **1,766** |

Reality serves a HIGHER belly demand (24–27 GW vs the model's 22–23) with LESS
solar and only ~0.7–1.8 GW of imports — the balance is **8.5–10.5 GW of committed
gas** — and still clears at ~$15. That much gas cannot be marginal-priced at $15
unless it is **committed and bidding its min-load below $15** (must-take while on
for the evening ramp). The model runs a THIRD of that gas, bids it at full MC, and
imports 2–3 GW MORE to fill — so gas/import at full offer sets the belly at ~$26.

The model's committed-gas belly floor is **far too low**. The keeper's
`caiso_ra_mustoffer` bridge (the CAISO P1-native commitment bridge) floors only
**3.2–3.7 TWh/yr** of gas (D-2 `ra_mustoffer_bridge`, ~1.5 GW belly-average) —
vs reality's ~10 GW committed belly gas. The bridge under-commits the belly by
~5–6 GW.

---

## Decision framing — both suspects out; the lever is the committed-gas belly STATE

**Suspect 1 (curtailable-solar rung) — REFUTED.** Solar is 98% absorbed with
endogenous spill already ON; no suppressed pool; a $0 rung is inert; the derate
would raise the price.

**Suspect 2 (belly-hub import reprice) — REFUTED/COUPLED.** The border is already
cheap ($2.6–6.3 PNW) and corridor-capped; the belly hub the model reads is already
$10.5 DSW; repricing the remaining economic tranches is a VOLUME lever (worse
C5a), not a C5a-neutral price lever.

**The load-bearing lever — the committed-gas belly commitment STATE.** Reality's
belly clears at ~$15 with 10 GW of gas because that gas is COMMITTED (min-load
bid-down, must-take, never marginal). The model backs gas off to a ~2 GW trough
and over-imports, so full-MC gas/import sets $26. Committing the gas reality shows
stays on — flooring the CAISO merchant gas-CC fleet at its measured committed
belly min-load — makes that gas INFRAMARGINAL (must-take), which:

1. pushes the marginal unit DOWN to curtailed solar / the min-load block (~$15) →
   **C3a-belly fixed**; and
2. serves the belly from committed domestic gas → **displaces the over-import**
   (3.9 → ~1.3 GW toward actual) → **C5a fixed**.

**ONE mechanism, both gates** (rule 15). It is C5a-neutral-or-better (a state
floor, not an import ADD), physics-grounded (min-load HR + start-up cost + evening
spread; the committed level is MEASURED from CEMS / CAISO 60-Day disclosures, not
fitted to the residual — rule 13/18), and forward-reproducible. This is the CAISO
analogue of `ercot_gas_commitment_bridge` (ERCOT-63), which proved the STATE alone
(not a price markdown) closes the trough.

### Why this also explains the caiso-117 coupling

caiso-117 found the belly VOLUME cap fixes C5a but BREAKS C3a (belly +8.6 →
+13.2% in 2025). The reason is now clear: the cap cuts imports but lets **full-MC
gas** fill the hole (raising the belly price), because the committed min-load
bid-down STATE is missing. With the commitment bridge, cutting imports and running
committed gas at its bid-down min-load fixes BOTH — the volume cap and the price
lane stop fighting. The belly-price fix is a **precondition** for the volume cap,
exactly as the handoff anticipated — but the fix is the committed-gas STATE, not
solar or import price.

### Redirect (caiso-119) — build the committed-gas belly floor toward the measured level, then re-arm the volume cap jointly

Single, physics-grounded, C5a-neutral-or-better delta (its own build session —
touches the commitment path in core files, so mind rule 27 / the push gap):

1. **Raise the CAISO committed-gas belly floor to the MEASURED committed level.**
   Derive the belly committed-CC min-load from CEMS / CAISO 60-Day DAM disclosures
   (the ERCOT-63 template: measured committed-CC LSL/HSL cap-weighted p50 min-load
   × the units the P0 pattern shows stay on through the belly). Extend/retune
   `caiso_ra_mustoffer` / `caiso_ra_p1_floor_fleet` so the belly-committed fleet
   is floored toward reality's ~8–10 GW (net of what is already economically
   committed), NOT to a residual-fitted level.
   - **Gate:** model belly LMP → toward $15 (from ~$26); belly gas → toward the
     measured 8–10 GW; belly import → toward actual ~1.3 GW (C5a improves);
     C3a STAYS PASS all years incl. 2025; C3b improves; evening UNTOUCHED (the
     floor is belly-scoped — the caiso-117 A/B already showed the belly lever
     leaves the evening clean).
   - **Guardrails (rules 12/14/18):** the floor needs a cited D-4 window (the
     measured committed belly hours) and must clear the C8 forced-energy budget —
     at ~10 GW belly commitment CC_REGULAR will exceed the 30% merchant cap, so it
     takes the rule-14 v2.2 grounded-above-budget escalation (D-4 off-window
     clean + D-1 diurnal shape faithful). Reality's 10 GW belly gas IS the
     grounded window, so a clean grounded PASS is expected — but it must be scored,
     not asserted. **KILL** if the committed level is fitted to the price/volume
     residual rather than measured (rule 13), or if it forces gas in hours the
     disclosure evidence says the fleet is off (rule 12), or breaks the evening.
2. **THEN re-arm `caiso_belly_import_cap` jointly** — *note (2026-07-26): "re-arm"
   means **RE-IMPLEMENT**. The caiso-117 mechanism never reached main (its
   session branch is deleted); the spec in FINDING-caiso117 §Inv-2 is the
   rebuild recipe, and `tests/test_caiso_belly_import_cap.py` was C-deleted as
   an orphan, so this lane also owns the mechanism's unit tests.* With the belly committed and
   clearing ~$15, the volume cap no longer inflates C3a (gas is now bid-down
   committed, not full-MC marginal) → belly volume (C5a) + belly price (C3a) land
   together. LOYO within 2023–2025 before any promotion (rule 22).

## DO-NOT-REDO (added this session)

- **Curtailable-solar $0 belly rung / re-enabling the solar deliverability derate**
  — solar is 98% absorbed (endogenous spill on); the rung is inert and the derate
  raises the belly price (Inv 2).
- **Repricing belly imports to the measured/border hub as a belly-PRICE lever** —
  the border is already cheap and corridor-capped; repricing pulls VOLUME and
  worsens C5a (Inv 4). Not a C5a-neutral price lever.
- Carried: belly VOLUME cap as a STANDALONE (caiso-117); endogenous WECC-West
  node (caiso-114/116); belly-depth on any CA-price / west-surplus-QUANTITY
  observable (caiso-107/109); fixed-hub West fallback (caiso-114); firm-rung offer
  reprice (caiso-104/109); zone granularity for the systematic residual
  (caiso-111).

Full reproduction: `scripts/probes/_caiso118_belly_price_derive.py` (NO LP;
committed keeper-proxy `caiso104_m1_B` hourlies + raw EIA-930 CISO + the LP's own
`load_renewable_profiles` potential + `measured_import_hub_prices` +
`measured_corridor_flow_envelope`).
