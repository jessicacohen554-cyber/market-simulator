# Fuel-Forward Trajectory Methodology — sources, grounding, and near-term triangulation (2026-07)

**Session:** FF-G2 (lane L-INP), 2026-07-20 (branch
`claude/henry-hub-fuel-forward-ohbpw0`). **Status of this doc:** standing
methodology reference for every forward fuel-price input the forecast dispatch
and capacity-expansion components consume — the Henry Hub natural-gas path
(`HENRY_HUB_TRAJECTORIES`), the national delivered-coal path
(`COAL_PRICE_TRAJECTORIES`), the delivered-oil path (`OIL_PRICE_TRAJECTORIES`),
and the held-flat nuclear fuel-cycle cost (`NUCLEAR_FUEL_PRICE_HISTORICAL`).
Companion artifacts: the fetch/derive scripts
(`scripts/data/fetch_eia_aeo.py`, `scripts/data/derive_fuel_trajectories.py`),
the benchmark datatype `data/raw/fuel-forward-benchmarks/`, and the consistency
tests `tests/test_fuel_trajectory_consistency.py`.

Everything here is **forecast-only surface**: `resolve_fuel_prices`
(`data/fuel.py`) reads these trajectories only in `mode="forecast"`; backcast
runs price gas from measured overrides, coal from the flat escalation / F923
receipts, and oil from `OIL_PRICE_PER_MMBTU` / F923 receipts. Backcast keepers
are byte-identical to before this session (verified — §7). The mechanical
half of FF-G2 is the **AEO2025 → AEO2026 vintage bump** (CLAUDE.md rule 23,
triggered by the source-data edition change); the research half is this doc.

---

## 1. Design: one agency fundamentals anchor + a published scenario range

Each fuel's forward price is carried as a **low / mid / high** path, selected by
`ScenarioConfig.{gas,coal,oil}_price_path` (default `"mid"`):

- **Mid** = the EIA Annual Energy Outlook **central case** at each projection
  year, a single-source deterministic derivation from the AEO data tables
  (rule 5 / rule 23), not a curated blend. AEO2026 renamed the central case
  "Reference" → **"Counterfactual Baseline"** (`cb2026`); it is the direct
  successor and still the central projection.
- **Low / high** = the AEO's own **High / Low Oil and Gas Supply** side cases
  (`highogs` → "low" price, more supply; `lowogs` → "high" price, less supply).
  The same supply axis moves coal (mining diesel, rail, sector competition) and
  oil, so it is reused rather than inventing independent per-fuel scenario
  levers.

Why the AEO as the anchor (not a futures strip or a cross-source blend): (a) it
is the convention of the reference capacity-expansion models this model is
compared against — ReEDS, Cambium, EPA IPM all source gas from AEO scenarios
(§2); (b) it keeps the mid a *single-source deterministic derivation* rather
than a curated average with hidden weights; (c) it is a coherent
supply-demand-equilibrium path to 2050 (dispatch and capacity evolution need
the full horizon, which no futures strip covers); (d) the near-term is
triangulated against the market-informed STEO and the NYMEX strip as a
**cross-check, not a fit target** (§3, §6).

**Derivation lock.** Coal and oil are deterministic functions of the committed
AEO2026 extract (`tests/test_fuel_trajectory_consistency.py` asserts
`constants == derive_*_trajectory`). Gas forecast years 2026-2050 are likewise
locked; gas 2023/2024/2025 are measured historical actuals held fixed (§4.1).

### Dollar-year basis (edition change, documented)

AEO2026 is published in real **2025$**; AEO2025 was 2024$. The trajectories
carry the AEO's native dollar-year (rule 5, minimal transformation — the same
"keep the AEO's own basis" convention the AEO2025 vintage used). Consequences:

- **Coal** enters the model as a **dollar-year-invariant RATIO** to each ISO's
  own `COAL_PRICE_BASE` anchor (`resolve_annual_coal_price`), so the 2024$→2025$
  change moves *no* delivered coal price — only the AEO's real forward shape
  does. (The anchor year does shift 2024→2025; see §4.2.)
- **Gas and oil** enter as absolute levels, so the ~2.2% dollar-year restatement
  is a real (if small) part of their level change. For gas the dollar-year
  effect is dwarfed by the genuine modeled increase (§5): the mid 2026 rises
  $2.74 → $3.88, of which only ~$0.06 is the dollar-year.
- **Nuclear** is NOT re-derived by the AEO bump (its EIA Uranium Marketing
  source did not update — rule 23), so it stays in its own real-2024$ basis.
  The resulting cross-fuel mix (gas/coal/oil 2025$, nuclear 2024$) is a ~2.2%
  inconsistency that is immaterial: nuclear fuel is a small share of nuclear MC
  and nuclear is rarely marginal. Documented here rather than papered over.

## 2. How the field sources fuel-price forwards

Surveyed 2026-07-20; links are to the operative public documents. The pattern is
consistent: a **national-lab/agency fundamentals path (AEO) as the anchor**,
with commercial practice **splicing an exchange futures strip over the near
term**.

| Model / practice | Fuel-forward source | Near- vs long-term | Citation |
|---|---|---|---|
| **EIA NEMS / AEO** (the anchor itself) | Fundamentals **market equilibrium** — the Natural Gas Market Module solves supply/demand/network for the Henry Hub benchmark each projection year; the Oil & Gas Supply Module feeds supply functions. Not a futures strip. | Long-horizon to 2050; near-term calibrated toward STEO but mechanism is fundamentals | [NGMM doc](https://www.eia.gov/outlooks/aeo/nems/documentation/ngmm/pdf/NGMM_AEO2025.pdf) · [AEO2026 NGMM assumptions](https://www.eia.gov/outlooks/aeo/assumptions/pdf/NGMM_Assumptions.pdf) |
| **NREL ReEDS** | **AEO scenario** gas points (Reference / High / Low OGS), made price-responsive to ReEDS's own electric-sector gas demand; coal/uranium from AEO Reference, inelastic | AEO trajectory + supply elasticity | [ReEDS doc (OSTI 1915250)](https://www.osti.gov/servlets/purl/1915250/) |
| **NREL Cambium** | **AEO-based**, inherited via ReEDS | same demand-responsive AEO treatment | [Cambium 2023 doc](https://docs.nrel.gov/docs/fy24osti/88507.pdf) |
| **EPA IPM (Power Sector Platform v6)** | Gas price **endogenous** via ICF's Gas Market Model co-iterated with IPM; historically AEO-adapted pre-2030 and AEO-consistent for scenario framing | GMM/IPM co-solve a HH path + power-sector demand | [IPM v6 doc](https://www.epa.gov/power-sector-modeling/documentation-epas-power-sector-modeling-platform-v6) · [Natural Gas chapter](https://www.epa.gov/system/files/documents/2024-04/chapter-8-natural-gas.pdf) |
| **Commercial — Aurora / PLEXOS decks** | In-house fundamentals suites; in practice **near-term anchored to traded forward curves, long-term to fundamentals** ("reconciles short-term market behavior with long-term economics") | Futures-anchored near-term spliced into fundamentals | [Aurora](https://auroraer.com/products/power-renewables) · [Energy Exemplar](https://www.energyexemplar.com/aurora) (splice mechanics proprietary — not fully verifiable) |
| **Consultancy / bank (Brattle, E3, LBNL, S&P Platts)** | **Explicit splice**: NYMEX Henry Hub forward near-term into AEO fundamentals long-term, + locational basis. Brattle's ERCOT study used AEO for base/high but **replaced near-term years with actual Henry Hub forward prices** + a Texas basis; LBNL formalizes AEO-vs-NYMEX-forward comparison | Futures strip near-term → AEO long-term, + basis | [Brattle ERCOT](https://www.brattle.com/wp-content/uploads/2017/10/6065_exploring_natural_gas_and_renewables_in_ercot_part_iii_shavel_weiss_fox-pennerf.pdf) · [LBNL (OSTI 948129)](https://www.osti.gov/servlets/purl/948129) |
| **ISO IMM State-of-the-Market** (ERCOT/Potomac, PJM/Monitoring Analytics) | **Realized daily gas index** prices for the review year — retrospective, NOT a forward forecast | backward-looking only | [Potomac 2024 SOM](https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-State-of-the-Market-Report.pdf) |

**Alignment statement & house-style verdicts** (per forecast plan §4):

- **AEO fundamentals path as the anchor — ADOPTED.** Same anchor as ReEDS,
  Cambium, IPM (renewables/gas framing). Keeps the mid single-source and
  full-horizon.
- **AEO High/Low OGS as the low/high range — ADOPTED.** Every surveyed model
  carries an explicit scenario axis; this is the AEO's own.
- **Futures-strip near-term splice — ADAPTED, held as a cross-check, NOT
  default-adopted.** It is the standard *commercial* pattern (Brattle, LBNL,
  Aurora/PLEXOS), but the model's after-refresh AEO2026 near-term already sits
  within ~$0.2/MMBtu of the STEO market-informed reference (§3), so a blend
  would move the near term marginally and is a findings-first owner call (§6),
  not an automatic import. If adopted, the blend must be **formulaic and
  forward-reproducible** (rule 13): a strip/STEO weight decaying into the AEO
  over a fixed window, regenerable for any vintage — never a hand-tuned adder.
- **ISO IMM fuel references — REJECTED as a forward source.** They are
  retrospective realized-price reports; they belong to the backcast/measured
  layer, not the forward trajectory.

The model's own departure from the commercial pattern — no near-term futures
splice — is now a *small* gap (the vintage bump closed most of it), documented
in §6 as a live owner decision rather than a silent omission.

## 3. Near-term triangulation (2026-2028): AEO2026 vs STEO vs NYMEX strip

Benchmarks are **context only, never fit targets** (rule 1). Sources snapshotted
into `data/raw/fuel-forward-benchmarks/` (sha256-pinned; STEO July-2026 vintage,
API-fetched):

Henry Hub, $/MMBtu (AEO paths are the pre-basis model input):

| year | AEO2025 mid (OLD, 2024$) | **AEO2026 mid (NEW, 2025$)** | STEO Jul-2026 (nominal) | AEO2026−STEO |
|---|---|---|---|---|
| 2026 | 2.74 | **3.88** | 3.67 | +0.21 |
| 2027 | 2.62 | **3.62** | 3.49 | +0.13 |
| 2028 | 2.73 | **3.67** | — (STEO horizon ends 2027) | — |

**Finding.** The AEO2025 mid was demonstrably low near-term — ~$0.9/MMBtu
*below* the STEO for 2026. The AEO2026 bump not only closes that gap but
slightly *overshoots* it: AEO2026's `cb2026` 2026 ($3.88) is ~$0.2 *above* the
STEO ($3.67). Two caveats kept transparent: (a) STEO is nominal and AEO is real
2025$, but for 2026 the deflator is negligible; (b) among the AEO2026 cases the
`cb2026` central case runs a touch hot for 2026 (other side cases print
$3.70-3.74) — we use `cb2026` because it is the designated central projection
(no cherry-picking, rule 5). Net: **after the refresh the near-term
AEO-vs-market gap is within noise and has flipped sign**, which materially
weakens (does not eliminate) the case for a near-term blend (§6 owner box).

**NYMEX strip — open manual pull.** The current full CME Henry Hub futures strip
is bot-walled/licensed and the free EIA futures feed (`RNGC1..RNGC4`) is stale
(latest print 2024-04-05, recorded in the datatype so the staleness is
auditable). It is a **MANUAL DOWNLOAD** row in the datatype README — never
guessed (rule 5). The STEO stands as the market-informed near-term reference in
the meantime.

## 4. Per-fuel grounding

### 4.1 Natural gas — `HENRY_HUB_TRAJECTORIES`

- **Source:** AEO2026 Table 13 Henry Hub spot, real 2025$/MMBtu, via
  `fetch_eia_aeo.py --aeo-year 2026` → `derive_gas_trajectory`.
- **Forecast years 2026-2050:** the three AEO2026 cases (`highogs`/`cb2026`/
  `lowogs`). Mid rises $3.88 (2026) → a ~$5.4 plateau (2040-41) on LNG-export
  growth and rising marginal production cost, declining to $4.64 (2050).
- **Historical actuals 2023/2024/2025 (2.54 / 2.19 / 3.52):** measured EIA Henry
  Hub spot annual averages, identical across paths (a realized price has no
  scenario branching), **held fixed across the vintage bump**. AEO2026's own
  2025 base-year value ($3.47) is discarded in favour of the measured $3.52
  because the **backcast neighbor-price seam** (`data/neighbor_price.py`) reads
  these ≤2025 values — keeping them fixed is what preserves backcast
  byte-identity (§7).
- **Hindcast paths** (`hindcast_realized`, `hindcast_asknown_aeo2021`):
  untouched (backcast/hindcast surface).
- **Consumed by:** `resolve_annual_gas_price` (dispatch + capacity LCOE),
  `data/neighbor_price.py::neighbor_gas_price` (forecast neighbor gas), the
  PB-1 `gas_price_factor` uncertainty lever, and the AEO-spread sigma floor in
  `uncertainty.py` (whose 2050 low/high spread widened — §5).

### 4.2 Coal — `COAL_PRICE_TRAJECTORIES`

- **Source:** AEO2026 Table 15 national delivered-to-electric-power coal, real
  2025$/MMBtu → `derive_coal_trajectory`.
- **Mechanism:** a **dollar-year-invariant real-growth RATIO** applied to each
  ISO's own `COAL_PRICE_BASE` delivered-cost anchor
  (`resolve_annual_coal_price`) — a single national series can't resolve ERCOT
  lignite vs PJM Appalachian vs MISO PRB+ILB basin economics (rule-14
  misalignment exception), so only the AEO's real *shape* is borrowed, not its
  level. The dollar-year basis therefore never touches a delivered price.
- **Anchor-year shift 2024 → 2025:** AEO2026 starts at 2025 (AEO2025 started
  2024), so the ratio now renormalizes to `trajectory[2025]`. This is a ~1-2%
  reanchoring of the forecast coal level (the ratio denominator moved one year),
  recorded in the delta ledger (§5). It is arguably more correct — the base
  anchor now aligns to the model's near-start year.
- **Forecast-only:** backcast coal uses the flat `COAL_PRICE_ESCALATION`
  fallback or F923 measured receipts, never this table (§7).

### 4.3 Oil — `OIL_PRICE_TRAJECTORIES`

- **Source:** AEO2026 Table 12 electric-power distillate + residual fuel oil,
  each converted $/gal → $/MMBtu via EIA heat contents (0.1385, 0.1497
  MMBtu/gal) and averaged, real 2025$/MMBtu → `derive_oil_trajectory`.
- **Level:** mid eases from $17.5 (2026) to ~$17-18 mid-horizon, up to $19.8
  (2050) — modestly below the prior AEO2025 path (§5). Starts at 2025.
- **Forecast-only:** backcast oil uses `OIL_PRICE_PER_MMBTU` / F923 Petroleum
  receipts. Oil rarely sets price (peaker economics), so the change is
  second-order.

### 4.4 Nuclear — `NUCLEAR_FUEL_PRICE_HISTORICAL` (UNCHANGED)

- Built from the EIA Uranium Marketing Annual Report front-end fuel-cycle prices
  via the standard LWR fuel-cycle formula (real 2024$/MMBtu, held flat forward).
  **Not re-derived by the AEO bump** — its source did not update (rule 23). Read
  in both backcast and forecast, so leaving it byte-identical is required for
  backcast identity.

### 4.5 Delivered-basis adders — F923 re-check (`GAS_BASIS_DIFFERENTIAL`)

The rule-13 admissibility test, applied verbatim: *"could this same quantity be
produced for a forward year from forward drivers, and would it respond to
changed conditions? If yes, it is a legitimate input even in backcast mode."*
The per-ISO delivered-gas basis adders (ERCOT −0.50, CAISO +1.20, PJM +0.67,
NYISO +0.55, NEISO +1.10, MISO +0.30 $/MMBtu) are each a **measured EIA-923 /
EIA-NG-Weekly delivered basis** (Henry Hub → burner-tip), held constant across
the horizon, forward-reproducible, and responsive to regional supply — they
**pass** the test and are already the grounded (not fitted) layer. FF-G2 does
**not** re-derive them: the vintage bump is a Henry Hub *level* change, and the
basis is a separate F923-grounded overlay (the richer per-zone monthly basis
CSVs in `data/raw/*_zonal_gas_hub.csv` carry the measured detail). No basis
value changes this session.

## 5. Delta ledger (AEO2025 → AEO2026 vintage bump)

Mid path unless noted. Gas/oil in native dollar-year ($/MMBtu); coal shown as
the real-growth shape (ratio mechanism, level unchanged by dollar-year).

| input | before (AEO2025) → after (AEO2026) | why |
|---|---|---|
| gas mid 2026 | 2.74 → **3.88** (+1.14) | AEO2026 fundamentals + near-term market reality (STEO ~3.67); ~$0.06 of the lift is the 2024$→2025$ restatement, the rest is a real modeled increase |
| gas mid 2027 / 2028 | 2.62 / 2.73 → **3.62 / 3.67** | same |
| gas mid 2030 / 2040 / 2050 | 3.08 / 4.27 / 4.80 → **4.48 / 5.36 / 4.64** | higher mid-horizon plateau, slightly lower 2050 |
| gas low 2050 | 2.83 → **2.75** | High OGS case |
| gas high 2050 | 9.75 → **13.67** | Low OGS case much higher — widens the model's implied gas-uncertainty band (below) |
| `uncertainty.GasMarginal` AEO 2050 σ floor | ~0.555 → **~0.843** | mechanical consequence of the wider low/high 2050 spread (log P10/P90 half-spread); a forecast-only PB lever, test updated |
| coal anchor year | 2024 → **2025** | AEO2026 starts 2025; ratio renormalizes (~1-2% reanchor) |
| coal real forward shape | AEO2025 Table 15 → **AEO2026 Table 15** | new vintage; delivered level still set by per-ISO `COAL_PRICE_BASE` × ratio |
| oil mid 2026 / 2030 | 18.41 / 19.22 → **17.53 / 17.78** | AEO2026 slightly lower distillate+residual path |
| oil / coal first year | 2024 → **2025** | AEO2026 horizon start |
| nuclear | **unchanged** | source (EIA UMAR) not updated (rule 23) |
| dollar-year basis (gas/coal/oil) | 2024$ → **2025$** | AEO2026 edition; coal ratio-invariant, gas/oil ~2.2% |
| central-case id | `ref2025` → **`cb2026`** | EIA renamed Reference → Counterfactual Baseline |

Behavioral direction: near-term forecast gas prices rise materially (correcting
a demonstrated low bias), mid-horizon gas rises, the gas-uncertainty band
widens (honest AEO scenario spread), oil eases slightly, coal moves only on its
real shape. All forecast-only; no backcast run changes (§7). Downstream note:
`data/neighbor_price.py` forecast neighbor gas rides `HENRY_HUB_TRAJECTORIES`,
so forecast neighbor prices see the same +~$1/MMBtu near-term lift (× the
neighbor's marginal heat rate); nothing in that module changed.

## 6. Near-term reconciliation posture — OWNER DECISION (findings-first, no default flip)

Per forecast plan §7.6 this session **implements nothing beyond the AEO2026
refresh** without the owner's pick. The finding: the vintage bump alone closed
the near-term gap (AEO2026 mid 2026 $3.88 vs STEO $3.67, +$0.21 — was −$0.93
under AEO2025). Options:

> **Option A — status quo (RECOMMENDED): pure AEO2026 annual paths.** Keep the
> refreshed AEO2026 trajectories as-is. The near-term now sits within ~$0.2 of
> the STEO market reference — inside the month-to-month revision noise of either
> source — so a blend buys little. Single-source, fully derivation-locked, no
> new machinery. *Cost:* the model does not track the exchange strip's exact
> near-term shape (a small, sign-flipped residual vs STEO).
>
> **Option B — formulaic near-term blend.** Splice a market reference
> (STEO annual, or the NYMEX calendar strip once the manual pull lands) over the
> first 12-24 months, decaying linearly into the AEO by a fixed horizon (e.g.
> full weight at 2026, zero by 2028). Reproducible for any vintage → rule-13
> admissible. *Cost:* new machinery + a second source to maintain; and post-bump
> it would pull the near term *down* ~$0.2, a marginal, ambiguous-benefit
> change. Would need its own consistency test and a forecast probe.

Recommendation: **Option A.** The refresh already delivered the near-term
correction FF-1E's audit chartered; a blend is now a low-value complication.
Benchmarks and strips remain context, never fit targets, regardless of the pick.

## 7. Verification

- **Consistency tests** (`tests/test_fuel_trajectory_consistency.py`, new — 10
  tests): gas forecast years == `derive_gas_trajectory`; gas ≤2025 historical
  actuals fixed (and ≠ AEO2026's own 2025 base); coal/oil == their derivations;
  coal/oil anchor year 2025; nuclear unchanged & 2024-terminal; AEO2026 raw is
  2025$; low<mid<high at 2050.
- **Affected value-tests updated** (forecast-value assertions tied to the old
  vintage, not backcast identity): `test_uncertainty.py::test_floor_widens_back_years`
  (σ floor 0.555 → 0.843, AEO2026 2050 spread) and
  `test_fuel.py::test_dual_fuel_caps_only_above_parity_hours` (the below-parity
  fixture hour lowered below the new oil level).
- **Full suite:** `pytest -q` — result recorded in the session handoff.
- **Backcast byte-identity:** structurally guaranteed and asserted — the only
  backcast reader of any refreshed trajectory is the neighbor-price seam reading
  gas ≤2025, which is unchanged; coal/oil trajectories are forecast-only
  (`resolve_fuel_prices` mode gate); nuclear is untouched. Demonstration in the
  handoff (`docs/handoffs/ff-g2-fuel-forward-2026-07.md`).
- **T0 forecast probe (optional, ≤5 solve-years):** ERCOT 2026 single-year
  before/after — result in the handoff.

## 8. Maintenance rules

- **Re-derive only on a source update** (a new AEO edition), never on a residual
  (rules 13/23). Each vintage bump lands as: `fetch_eia_aeo.py --aeo-year <N>`
  (add the edition's central-case scenario id to `SCENARIOS_BY_AEO` after
  verifying it against the API's `facet/scenario` listing — never guess) →
  `derive_fuel_trajectories.py --aeo-year <N>` → paste the printed blocks
  (gas: forecast years only, keep the historical actuals) → tests assert
  equality.
- **Keep the AEO's native dollar-year**; record any dollar-year change in the
  delta ledger. Coal is ratio-invariant; gas/oil carry the restatement.
- **Historical gas actuals (≤ START_YEAR−1)** are measured spot averages — they
  update only when a new realized annual average is published, and stay
  identical across all scenario paths and vintages (they anchor the backcast
  seam).
- **Benchmarks/strips are context, never fit targets** (rule 1). Refresh the
  STEO snapshot and re-pin its sha256 when triangulating a new vintage; land the
  NYMEX strip via the datatype's MANUAL-download row.
- **Out of scope, left to the owner:** the FC-5 external-corridor pin is on
  AEO2025 (chosen by FF-0F) — this refresh does not move it; the AEO2026 vintage
  is now available should the owner re-pin the corridor. Backcast fuel (F923
  delivered overlay) is untouched by construction.
