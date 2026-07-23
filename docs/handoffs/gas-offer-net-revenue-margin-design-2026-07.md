# Gas-offer net-revenue / markup-compression mechanism — frozen design (2026-07-23)

Charter: the NEISO 2022 holdout rotation (run
`2026-07-23-neiso-2022-holdout-validation`) rejected the multiplicative offer
form — the $/MWh markup over true marginal cost of every gas band scales
linearly with the fuel bill (`markup = base_HR × (mult−1) × gas`), which is
unidentified inside the homogeneous 2023–2025 training gas window and balloons
at 2022's ~2.9× delivered gas, over-pricing the whole gas-marginal bulk
(40–80 $/MWh band: model 116.0 vs actual 58.3 over 4,546 h) while the fixed
scarcity wall never forms the tail. Design frozen BEFORE the build (miso-70
pattern); NEISO first, ISO-agnostic plumbing.

## Mechanism (`gas_offer_net_revenue_margin`, ScenarioConfig, default OFF)

Decompose each registered gas offer band multiplier `mult` into a **measured
physical heat-rate basis** `phys` plus a **markup** `mult − phys`, and reprice
the band from the fully fuel-scaled form to a fuel-invariant net-revenue
margin identified at the training-window delivered-gas anchor `P_anchor`:

```
current:   offer(t) = mult × HR_base × fuel(t)                     + VOM + emis(t)
reformed:  offer(t) = phys × HR_base × fuel(t)
                      + max(0, mult − phys) × HR_base × P_anchor    + VOM + emis(t)
```

* The **physical part** (`phys × HR_base`) keeps full fuel tracking — real
  burn (part-load block average, incremental marginal HR, duct-burner ratio)
  must scale with delivered gas, including the dual-fuel oil-parity switch
  (the genuinely gas-linked opportunity-cost piece is KEPT).
* The **markup part** becomes a fixed $/MWh margin — the net-revenue-target
  component (start/no-load hurdles, competitive reach, the scarcity wall)
  that real bidders express in $ terms, not heat-rate multiples. `offer/mc`
  therefore compresses toward 1 as gas rises, and *rises* at cheap gas —
  matching BOTH halves of the already-ledgered within-window signature
  (neiso-45/46/47: flat winter overshoot at $3.5–7.7 AGT gas + summer-evening
  undershoot at $1.8 gas) and the 2022 out-of-window rotation.
* Exact identity at `fuel(t) = P_anchor`: the reformed offer reduces to the
  registered band mult, so the in-sample surface is preserved at the
  identification point (the "compose" answer to charter decision 1 — the
  registered curve IS the anchor-gas calibration; no re-fit).

Implementation is a post-`assemble_mc` vectorized adjustment (both
orchestrators, P0 and P1 — it is the offer curve itself, not a pass markup):

```
mc[g, t] += offer_markup_hr[g] × (P_anchor − fuel_price[g, t])
offer_markup_hr[g] = HR_base(plant) × max(0, mult_band(g) − phys_band(g))
```

computed per tranche in `bins_to_fleet` (CAMPD path) and carried on the
`Generator` (`offer_markup_hr`, default 0.0). No LP structure change; prices
stay LP duals (rule 4); no hourly Python loop (rule 2).

## Scope (charter decision 2)

Gas classes only (`gas_cc`, `gas_ct`, `gas_st`, `gas_cc_ccs` tranches of the
CAMPD offer-curve path). Coal keeps its own gas-keyed supply sigmoid — one
mechanism per phenomenon (rule 19). The legacy (non-CAMPD) tranche path is out
of scope (no phys registry → mechanism inert). Bands without a declared
physical basis are **neutral** (`phys = mult` ⇒ markup 0 ⇒ byte-identical
offers at every gas price) — the rule-24 generic fallback.

## Identification (charter decision 3 — all measured/registered, nothing fit to a residual)

Three ingredient families, each with a named source:

1. **Band multipliers**: the already-registered `offer_curve_by_group` surface
   (NEISO: `_NEISO_OFFER_CURVE`, backcast_config). No new fitted values — the
   mechanism only changes the markup's gas-elasticity from 1 to 0.
2. **Physical basis `phys_*` (new per-band registry keys, NEISO values)**: the
   ISO's own measured CAMPD heat-rate artifact
   `data/raw/reference/neiso_campd_marginal_hr_summary.csv`
   (`scripts/data/derive_campd_marginal_hr.py --iso NEISO`, frozen rule-23
   derive; the same artifact the registered curve's econ bands were grounded
   on 2026-07-06):
   * committed band → `avg_committed_p50` (the min-load block's average burn:
     the physical content of a capacity block is its average heat rate);
     where the registered committed bid sits BELOW the measured block average
     (price-taker cogen/steam bands: CC_CHP 1.15 < 1.399, ST_GAS 0.79 < 2.394)
     the markup clips to 0 — no compression, no negative margin.
   * econ bands → `marg_econ_low_p50` / `marg_econ_high_p50` (incremental
     output prices at incremental burn), interpolated across the n-slice
     smoothing ramp at each slice's own multiplier position.
   * peak band → CC classes: the registered 2.25 IS the measured physical
     F-class duct-burner ratio (markup 0 — the duct tranche keeps full fuel
     scaling); CT/ST classes: 1.0 (full-output physical bound, conservative
     — the 4.0 CT wall was set against the $-denominated ISO-NE offer cap,
     so everything above base burn is a $ scarcity margin).
3. **Anchor `P_anchor`**: the mean of the model's own merit-order delivered-gas
   series (`data.fuel.trajectories._gas_series` — measured EIA HH monthly ×
   measured AGT hub basis, the series the mults were calibrated against) over
   the training window 2023–2025: **NEISO 4.0763 $/MMBtu** (year means
   2.9365 / 3.0304 / 6.2621). Derive:
   `scripts/data/derive_gas_offer_margin_anchor.py` (frozen against residuals;
   re-derives only when the gas source workbooks change). Registered in
   `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO`; resolved onto
   `ScenarioConfig.gas_offer_margin_anchor` at config build so the bundle's
   `run_config.json` records it (rule 25).

Resulting NEISO fixed margins at the anchor ($/MWh, `markup × HR_base × 4.0763`):

| class | committed | econ_low | econ_high | peak |
|---|---|---|---|---|
| CC_REGULAR (HR 7.48) | 0.163 → 4.97 | 0.146 → 4.45 | 0.210 → 6.40 | 0 (duct physical) |
| CC_CHP (HR 6.859) | 0 (below block avg) | 0.197 → 5.51 | 0.250 → 6.99 | 0 (duct physical) |
| CT_PEAKER (HR 10.603) | 0.365 → 15.78 | 0.255 → 11.02 | 0.300 → 12.97 | 3.0 → 129.69 |
| ST_GAS (HR 12.755) | 0 (below block avg) | 0.158 → 8.22 | 0.159 → 8.27 | 0 |
| CT_CHP | 0 (neutral curve, n=1 — not identifiable) | 0 | 0 | 0 |

**Net-revenue cross-check (the Potomac-SOM construction ported to the offer
side — retirements.py::apply_economic_retirements asks "does the margin cover
going-forward cost?"; the offer asks "what bid recovers the target margin?")**:
the CT_PEAKER scarcity margin of ~$130/MWh recovers a FOM-only going-forward
cost of `fixed_om_gas_ct = 21 $/kW-yr` over ~162 expected scarcity run-hours
(21,000 / 129.7), inside the observed NEISO true-peaker duty band (CAMPD
CT_PEAKER fleet runs a few hundred hours; the top *peak band* engages in the
tightest subset), and the committed hurdle $15.8/MWh is the start/no-load
amortization magnitude. Printed by the derive script; a documentation
cross-check, never a tuning channel.

## Composition (one mechanism per phenomenon, rule 19)

* `tranche_startup_amortization` (keeper ON): prices the fuel-invariant
  fast-start start/no-load component as its own P1 adder. The registered band
  mults were calibrated WITH it on, so the markup converted here is the
  residual band-level component — no double count; the two remain separate
  registered mechanisms.
* Dual-fuel oil-parity cap: `apply_dual_fuel_pricing` mutates `fuel_prices`
  BEFORE `assemble_mc`, so the compression keys on the post-switch delivered
  price — a unit on oil bids `phys × oil_parity + margin`. The gas-linked
  resale-opportunity piece stays in the physical term.
* Coal PRB/supply sigmoids, EAC credits, ORDC/scarcity overlays, reserve
  co-optimization: untouched (disjoint rows / post-solve layers).
* Emission accounting already books CO2 at the plant's physical `base_hr`,
  never the bid-tranche HR — unchanged.

## Validation plan (frozen, in order)

1. Trivial 1-gen gas sweep $2→$7 (tests/test_offer_curves.py): flag OFF →
   `offer − true_mc` scales linearly with gas; flag ON → scarcity margin
   invariant to machine precision, identity at `fuel = anchor`.
2. In-sample NEISO 2023+2024+2025, one bundle (rule 16), single-delta replay
   of the neiso-60 keeper recipe (meta.json + `gas_offer_margin: true`) with a
   same-HEAD base replay as drift control. Expectation: stays ~within the
   keeper C3a/C3b envelope (delivered-gas year means 2.94/3.03/6.26 straddle
   the 4.08 anchor: 2023/2024 offers firm slightly, 2025 compresses slightly).
3. LOYO within 2023–2025 (rule 22): the mechanism carries zero per-year
   parameters; evidence = per-year C3 deltas vs the keeper — no year may
   degrade materially to buy another.
4. ONLY THEN the NEISO 2022 validation re-check (iterable tier, marker
   present, `--holdout-authorized`), replaying the holdout recipe + flag.
   Target: the 40–80 bulk gap (+57.7) shrinks toward 0; C3a mean moves most;
   C3c tail only partially (the gas daily→monthly fallback and
   reserve-scarcity lanes are separate charters — not conflated here).
   Recorded whatever it is; NO parameter responds to the 2022 result.
5. Every solve registered on the backcast dashboard (rule 14).

## Refutation criteria (pre-registered)

* In-sample C3a leaves the keeper's ±10 % band in any training year, or C3b
  duration-curve fit degrades materially in a year the keeper passed →
  mechanism stays default-off, finding ledgered (rule 1: the structure is
  kept as a registered, documented option; the level calibration would then
  need a root-cause pass, not a refit of the margins to the residual).
* 2022 bulk gap widens or is unchanged → the bulk overshoot is NOT (only) the
  offer form — re-open the gas daily→monthly fallback / import-pricing lanes
  before any further offer work.

## Adoption status (per ISO)

* **NEISO — ADOPTED, keeper on** (`neiso-61`, 2026-07-23). Anchor 4.0763.
* **CAISO — ADOPTED as the go-forward offer form** (owner directive, rule #1,
  2026-07-23; `docs/handoffs/caiso-netrev-adoption-log-entry.md`). Anchor 4.7964.
  caiso-112's in-sample replay tripped refutation criterion 1 (C3b duration fit
  degrades 0.390→0.411 / 0.429→0.445 in the two high-gas years) — but per that
  same criterion's rule-1 clause the structure is the correct one and the level
  miss is a *root-cause* problem, not an offer-form one: the band table shows
  CAISO's 80–480 $/MWh mid/upper-tail is under-priced in BOTH forms (the
  import/scarcity residual, caiso-107/109/111/116), and the net-rev form merely
  stops the HR multiplier's fuel-scaled markup from partially masking it at high
  gas. Owner packaging: the CAISO keeper is **not** re-promoted standalone (would
  regress C3b in isolation); the next keeper solve carries `--gas-offer-margin`
  **jointly** with the import/scarcity (C3c) lane so the tail is priced correctly
  before the compression applies. No code default flipped (would break the current
  keeper's byte-identity replay); the flag stays off in the registered keeper until
  the joint re-keeper. This resolves criterion 2's "re-open the import-pricing
  lanes before any further offer work" as: keep the correct offer form, move the
  import lane, then re-keeper.
* **ERCOT / PJM / MISO / NYISO — identification landed** (`379a9b3`), flag
  default-off; adoption pending each ISO's own A/B.

## DOF ledger delta

New free parameters: NONE fitted. `P_anchor` (measured, derive script),
`phys_*` per band (measured CSV p50s / physical bounds, cited above), margins
= registered mults − phys (derived identity). The flag itself is a structural
form switch. Ledger entries land in the candidate bundle's
`calibration_attestation.json` free_parameters block at registration.
