# Handoff — PJM non-CAMPD availability (the nuclear scarcity blind spot) — 2026-07-16

**Status:** diagnostic-first scoping (no solve until the mechanism is identified
and the gate is pre-committed — rule 1). Grade: Opus/Fable (writes core
infrastructure). Grounding keeper: `2026-07-16-pjm-113-short-only` (PJM keeper,
owner-promoted; the measured short unit-outage overlay). Prior:
`docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md` §7-8.1.

## Why this exists

pjm-113 closed the C3c summer tail only +1 h (17→18 of a needed 26), and the
diagnosis (§8.1) disclosed the boundary as **congestion-surface-bound (§5)** plus
**~1.7 GW of frozen-constant-invisible partial derates (§7)**. Both of those live
in the **CAMPD-covered** coal fleet. This handoff opens a **third, previously
unmeasured contributor**: capacity the outage overlays are *structurally blind to*
because it is **not in CAMPD** at all.

**CAMPD only covers combustion emitters.** The PJM thermal fleet the model
carries (`load_fleet_from_csv("PJM")`) is:

| fuel | GW | units | CAMPD (CEMS)? |
|---|---|---|---|
| gas_cc | 58.8 | 296 | yes |
| gas_ct | 35.9 | 595 | yes |
| coal | 35.4 | 90 | yes |
| **nuclear** | **33.5** | **32** | **NO — blind** |
| oil | 4.4 | 389 | yes |
| **biomass** | **1.7** | 520 | **NO — blind** |

**Nuclear (33.5 GW) is the blind spot that matters for scarcity.** It is firm
baseload; a single unit in a refuel window or a trip removes ~1.1 GW of firm
capacity, and a heat-event trip is a canonical scarcity driver. Two compounding
problems:

1. **PJM nuclear runs on a fleet-wide MONTHLY CF smear** (`constants.NUCLEAR_MONTHLY_CF_BY_YEAR`,
   derived by `scripts/derive_nuclear_monthly_cf.py` as *fleet* net-gen ÷ *fleet*
   pmax ÷ hours-in-month). A month-average, fleet-average number **cannot see** a
   unit-specific refuel/trip landing in a specific scarcity hour — it spreads the
   outage evenly across every hour and every reactor, so in a Jun 24 17:00 tail
   hour the model still shows ~97 % nuclear when reality might be ~90 % (one
   ~1 GW unit fully out). ERCOT already solved exactly this with a per-reactor
   **daily** overlay (`ercot_nuclear_unit_availability` +
   `data/raw/ercot-nuclear-availability.csv`, from the ERCOT 60-Day DAM
   disclosure); PJM has no equivalent.
2. **The §2/§3 phantom decomposition was CAMPD-only** (model coal vs CAMPD coal),
   so any nuclear phantom is **unmeasured** — it does not appear in the +3.0 GW
   coal figure. If PJM nuclear was over-available in the tail hours, that firm MW
   suppresses the scarcity price *on top of* the coal phantom, and nobody has
   looked.

## The data inventory (the question this handoff answers)

**Do we have PJM DAM data or EIA-923 that could reveal outages on non-CAMPD
plants?** Yes — four sources, ranked by fitness for the scarcity-hour question:

1. **PJM `energy_market_offers` (DataMiner2) — the strongest, and already
   scripted.** `data/raw/pjm-energy-offers/` (README only; gitignored — ~1-2 GB,
   PJM non-member redistribution restriction). One row per **unit_code × operating
   hour**, carrying **`avg_ecomax`** (the unit's offered economic-max MW) plus the
   offer curve and `no_load_cost`/`avg_ecomin`. `avg_ecomax` **is a measured
   availability signal for every dispatchable unit that offers into the DAM —
   including nuclear and non-CEMS gas** — at **unit-hourly** grain, which CEMS
   fundamentally cannot provide for non-emitters. Infrastructure exists:
   `scripts/fetch_pjm_energy_offers.py` (2023-2025, ~4 months in arrears, public
   Ocp-Apim key) → `scripts/curate_energy_offers.py` → `data/clean/energy-offers/PJM/`.
   Currently consumed **only for the offer PRICE surface**
   (`derive_pjm_offer_midcurve.py`, `derive_pjm_offer_surface.py`); the
   **quantity/ecomax (availability) side is untouched.**
   **In-model precedent:** `outages.ercot_thermal_dam_availability_series`
   already treats ERCOT's offered **HSL** as measured availability — `avg_ecomax`
   is the identical concept on PJM's feed.

2. **EIA-923 monthly (on disk) — coarse but free.**
   `data/raw/_processed-legacy/eia923_monthly_generation.parquet` is **plant-month**
   net gen (per `plant_id`, `netgen_<month>_mwh`, `prime_mover`, `fuel_type`),
   17 PJM nuclear plants in 2025. A refuel window shows as a clear monthly dip
   (Dresden 2025: …Sep 646, **Oct 500, Nov 227**, Dec 694 GWh). This is a cheap
   upgrade of nuclear from the current *fleet*-month smear to a **plant**-month
   envelope (a refuel is localized to the right reactor), but it is still MONTHLY
   — it catches a refuel that overlaps a scarcity month, not a 3-day heat-event
   trip. Complements, does not replace, source 1.

3. **NRC daily Power Reactor Status Reports (gettable, NOT on disk) — cleanest
   nuclear-only.** NRC publishes daily **% power per reactor** for every US unit —
   public, ISO-agnostic, the exact analogue of ERCOT's nuclear overlay but from a
   universal source. Daily grain (finer than 923, coarser than the hourly offer
   feed), and unambiguously *physical* (no economic-withholding confound). Would
   need a new `fetch_nrc_reactor_status.py`; a reactor at 0 %/reduced % on a day =
   outage/derate → a `campd-nuclear-availability-PJM.csv` window set, consumed like
   the ERCOT nuclear overlay.

4. **EIA-930 hourly by fueltype (on disk) — aggregate cross-check only.**
   `data/raw/PJM_fueltype.parquet` (long: `period, iso, fueltype, value_mwh`)
   carries system nuclear generation hourly. Not unit-level, but a dip in total
   PJM nuclear in a tail hour corroborates a unit being down — useful to
   *validate* sources 1-3, not to build the overlay.

## How it could help the C3c scarcity tail

Replace the fleet-month nuclear smear with a **unit-daily/hourly measured
availability** overlay (the ERCOT `ercot_nuclear_unit_availability` pattern),
sourced from `avg_ecomax` (source 1) and/or NRC daily status (source 3), with the
923 plant-month envelope (source 2) as the low-effort first cut. Removing phantom
nuclear firm capacity **in the exact hours a reactor was down** tightens the
margin where the tail lives — and per-unit this is *larger and firmer* than the
coal short-outages leg A already captured. The same `avg_ecomax` extract
generalizes to **non-CEMS gas** (a second blind slice), so this is one datatype
that closes multiple availability gaps.

## Admissibility (rule 13) and caveats — read before building

* **`avg_ecomax`-as-availability is admissible** — a measured physical
  availability event, forecast-native (WEFOR/refuel-schedule analogue), responds
  to changed conditions, and has the in-model ERCOT-HSL precedent. **NOT** output
  pinning (it is the *offered* capability, not realized MWh).
* **Economic-withholding confound.** Offered ecomax can be below physical max for
  market reasons, not just outage. This is the same ambiguity the CAMPD
  in-merit / revealed-availability filter handles. **Cleanest first target is
  NUCLEAR**, a price-taker whose ecomax ≈ physical availability with negligible
  withholding; a gas-peaker extension needs an in-merit-style guard (do not ship
  the peaker slice without it — rule 1/#12).
* **Nuclear self-scheduling.** PJM nuclear often self-schedules rather than
  submitting an offer curve; verify on the *real* fetched data whether
  self-scheduled reactors populate `avg_ecomax` in `energy_market_offers`, or
  whether their availability must come from NRC/923 instead. (First diagnostic
  task below.)
* **PJM redistribution restriction** (`docs/data-licensing.md` §4). The raw
  energy-offers corpus is gitignored for this reason. Any committed artifact must
  be a **derived availability window set** (per-unit derate windows), not raw
  offers — the same posture the committed offer-surface derivations already take.

## Suggested session shape (diagnostic-first, rule 1)

1. **Measure the nuclear phantom, no-LP** (a probe like
   `_pjm_c3c_summer_tail_decomp.py`): in the 22 summer 2025 tail hours, compare
   the model's applied nuclear availability (`NUCLEAR_MONTHLY_CF_BY_YEAR` × pmax)
   against measured unit availability from `avg_ecomax` (fetch a few months) and/or
   NRC daily status and the EIA-930 nuclear aggregate. Quantify the phantom-nuclear
   MW in those hours. **If it is negligible, stop and disclose** — the tail is then
   confirmed congestion-bound (§5), not availability-bound, and no overlay is
   warranted.
2. If material, **pre-commit a gate** (never the residual): a build-time
   provenance check (recovered MW ≥ threshold in the tail hours) + a solve gate
   mirroring pjm-112 (C3c-2025 into band; small-count caps hold; no PASS criterion
   flips; LOYO), then build the overlay as `unit_nuclear_availability` (PJM) on the
   ERCOT pattern, default-off, one zero-DOF measured input.
3. Confirm the self-schedule question (caveat above) *before* choosing the source;
   fall back NRC/923 → ecomax as the data dictates.

**Guardrails:** 2023-2025 only (rule 22); PJM-scoped (rule 24); zero fitted
scalars (the availability comes straight from the measured feed — rule 13/20/23);
the congestion-surface lane (§5, West/Panhandle-style topology split) stays a
separate charter; do not chase the winter tail here.
