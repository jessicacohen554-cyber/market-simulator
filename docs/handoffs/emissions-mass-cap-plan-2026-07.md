# Emissions Mass-Cap / Cap-and-Trade LP Constraint — Design Plan (2026-07-04)

**Source prompt:** `docs/fable-prompt-pack-2026-07.md` F-2 (from `model-audit-prompt-pack-2026-06.md`
PP-2.1). **Companion findings:** `docs/fable-repo-audit-2026-07.md` EM-6 (carbon-price seam),
`docs/model-audit-2026-06.md` §"No CO₂/NOx mass cap". **Extension point:**
`policy/constraints.py::get_active_policy_constraints` returns `[]`.

**Status: implemented, default-off (2026-07-05).** The design below shipped in full across
PRs #1328 / #1353 / #1386; this doc is retained as the design record. See the
**Implementation status** ledger immediately below for what landed where and the (non-blocking)
follow-ons that remain. Read against CLAUDE.md rules 1 (structure first, don't fake the number),
2 (no hour loops), 5 (cite every number), 13/14 (measured data must be forward-reproducible),
9 (one-pass), 22 (holdout quarantine).

**Update (2026-07-05, follow-on pass):** the two deferred items flagged below — PJM fractional
membership and per-state RGGI budgets — are now landed. See the updated ledger and the new
"Follow-ons landed" section below the original list.

---

## Implementation status (2026-07-05)

Everything in this plan is implemented and merged; the mechanism is **default-off** (rule 24) and
cap-off backcast is bit-for-bit today's behaviour (§9.2 gate). Ledger by design section:

| Design section | Landed in | Where |
|---|---|---|
| §3 unified `emission_rate × membership` channel; §6 resolver | ✅ | `policy/cap_and_trade.py` (`resolve_carbon_program`, `CarbonProgramResolution`, `MassCapSpec`, `measured_price`/`projected_price`, `_membership`, `_power_sector_cap`, `_published_power_sector_budget`, `per_generator_membership`) |
| §6 `resolve_carbon_price` → thin `.price_adder` wrapper (EM-6 seam) | ✅ | `policy/carbon.py` |
| §6 `get_active_policy_constraints` returns `[cap_spec]` | ✅ | `policy/constraints.py` |
| §4 vectorized `_build_mass_cap_rows` (rule 2, no hour loop); end-anchored block before RPS; `_n_masscap_rows`; `co2_cap_price = -λ` on `DispatchResult` | ✅ | `model/dispatch.py` |
| §6 gated `ScenarioConfig` fields (`mass_cap_enabled`/`mass_cap_program`/`mass_cap_tons`/`carbon_program_price_path`), default off, in sweep-param dict + `run_config.json` | ✅ | `config/scenarios.py` |
| §5/§7 registry constants, all cited: `CAP_AND_TRADE_PROGRAMS`, `CARB_ALLOWANCE_BUDGET`, `CARB_FLOOR_PRICE`, `RGGI_STATE_CO2_BUDGET` (regional + per-state), `RGGI_MEMBER_STATES_BY_YEAR`, `SHORT_TON_TO_METRIC_TONNE`, `PJM_RGGI_ZONE_SHARE` (populated, per-zone-per-year) | ✅ | `config/constants.py` |
| §5 membership-weighted (per-gen) carbon adder | ✅ | `data/fleet.py::assemble_mc` (accepts `ndarray`) |
| §5 PJM per-unit membership: EIA-860 plant→state crosswalk + per-generator exact test | ✅ | `data/zone_assignment.py::plant_state_lookup`, `policy/cap_and_trade.py::per_generator_membership`, wired at `runner.py`'s `mass_caps` call site |
| §7 data intake (schema + curate + cited raw CSV, incl. per-state RGGI budgets) | ✅ | `data/raw/policy/{carb-cap-schedule,rggi-co2-budgets}/`, `data/dictionary/schema/*.schema.yaml`, `scripts/curate_{carb_cap_schedule,rggi_co2_budgets}.py`, `scripts/derive_pjm_rggi_zone_share.py` |
| §10 call-site threading `get_active_policy_constraints(config, year, zone_names=...)` → dispatch builder | ✅ | `runner.py` |
| §9.1–§9.6 tests incl. trivial binding-cap dual = `(mc_clean−mc_dirty)/(rate_dirty−rate_clean)`, cap-off regression, simultaneous RPS+reserve+cap dual-index, membership vectorization, no-hour-loop assertion, PJM per-unit membership, per-state RGGI budget sums | ✅ | `tests/test_cap_and_trade.py`, `tests/test_dispatch.py::TestMassCapConstraint`, `tests/test_runner.py::TestMassCapPerUnitMembershipWiring` |

**Dispatch wiring is NOT blocked / NOT missing.** The one open question this plan flagged for the
policy-side implementer — whether `dispatch.py` consumes policy constraint rows — is resolved:
`dispatch.py` fully consumes the mass-cap block (`mass_cap_coeffs`/`mass_cap_rhs`/`mass_cap_labels`
args → `_build_mass_cap_rows` → end-anchored dual → `co2_cap_price`), threaded from `runner.py`.
No dispatch-side wiring remains.

**Follow-ons landed (2026-07-05, this pass):**

- **PJM fractional membership** (§5, §11): `PJM_RGGI_ZONE_SHARE` is now populated per zone per year
  (2023/2024/2025), derived by `scripts/derive_pjm_rggi_zone_share.py` from the year-matched
  EIA-860 plant/generator tables (state + operating fossil capacity) and the same PJM zone
  assignment the dispatch model uses (`data.zone_assignment.build_zone_lookup`). Virginia's 1 Jan
  2024 RGGI exit is directly visible in the derived numbers: `PJM_Dominion` (VA+NC) goes from
  0.9881 (2023) to 0.0 (2024/2025). Membership is now **per-unit where the fleet representation
  allows it**: `policy/cap_and_trade.py::per_generator_membership` tests any generator with a real,
  resolvable `plant_code` against its own plant's state exactly (via the new
  `data.zone_assignment.plant_state_lookup`, reading EIA-860's `State` column directly), falling
  back to the zone-level fractional share only for synthetic/aggregate units (legacy equal-width
  heat-rate bins, `plant_code <= 0`) that have no single-site identity. Wired at `runner.py`'s
  `mass_caps` cap_coeffs call site (adder path is unaffected and stays $0 for PJM — no measured
  price series — so this ships numerically inert by default, same as before).
  - **Bug found and fixed in the same pass:** `resolve_carbon_program`'s membership vector was
    sized to the *static* `get_iso_config(iso).zone_names` topology, but `fleet_arrays.zone_idx`
    can index into a *runtime-extended* topology (PJM's external interchange zone, appended by
    `runner.py::apply_interchange_topology`) — an index-out-of-bounds the moment PJM's mass-cap row
    was ever actually exercised end-to-end (never was, until this pass's new runner-level test).
    Fixed by threading an optional `zone_names` override through `resolve_carbon_program` →
    `get_active_policy_constraints`, with `runner.py` passing its already-extended list. Pre-existing
    latent gap, not introduced by this pass; all other ISOs' cap-row paths were equally unexercised
    end-to-end before this fix (their static and runtime zone lists happen to already agree, or they
    have no external-node zone at all in `CAP_AND_TRADE_PROGRAMS`, so the bug was silent).
- **Per-state RGGI budgets** (§7): `RGGI_STATE_CO2_BUDGET` now carries each member state's own
  "CO2 Allowance Base Budget" for 2023-2025 (short tons), sourced directly from RGGI, Inc.'s
  official "Distribution of VYyyyy CO2 Allowances By State" spreadsheets (exact, not an
  ICAP-derived estimate — the regional `"RGGI"` total was also corrected to the exact published sum,
  112,457,784 / 84,162,784 / 81,347,784, up from the prior ~93.0M/69.0M/67.0M approximation).
  `policy/cap_and_trade.py::_published_power_sector_budget` now sums a RGGI ISO's own member
  states (`RGGI_MEMBER_STATES_BY_YEAR` ∩ `program.member_states`) instead of the region-wide
  over-bound — e.g. NYISO's row uses NY's ~$25-27M-ton budget, not the ~10x-larger regional total;
  PJM's row correctly drops Virginia's ~$25.5M-ton contribution after 2023. The regional total
  remains the fallback for years with no per-state breakdown (the 2027-2030 projections, which RGGI,
  Inc. does not publish per-state).

**Non-blocking follow-ons (as designed, still deferred — not gaps):**

- **Forecast adder uses an escalator on the last measured price**, not the `CARB_FLOOR_PRICE`
  series directly (`projected_price`, `escalation_rate`); `CARB_FLOOR_PRICE` is landed as the cited
  floor-band artifact. A future refinement could floor the projection at that band.
- **No banking/borrowing** (§8, by design): the endogenous dual is the power-sector, no-bank,
  single-year scenario allowance price — an upper bound in a tight year, ~0 in a loose one — never a
  point forecast of the banked RGGI/CARB market price. A cross-year bank remains explicitly out of
  scope (breaks rule-9 one-pass year independence).
- **NOx/SO₂ mass cap** (§10, expanded into its own §13 below, W8): out of scope this wave; the
  same builder with `nox_rate` is a trivial follow-on once a NOx budget/price registry lands.
- **The mass-cap row is not reachable from the backcast calibration harness — RESOLVED (2026-07-06,
  Lane L-8, G-29).** `runner.py::run_scenario_iso` (forecast/backcast orchestration) already fully
  threaded `get_active_policy_constraints` into the dispatch builder; the separate backcast
  **calibration** scripts never did, because `scripts/run_calibration_full.py::solve_and_persist`
  calls `scripts/run_calibration.py::run_year` directly (confirmed by reading both — there is only
  ONE dispatch-construction seam, not two), and `run_year` never called
  `get_active_policy_constraints` at all. Fixed by extracting the row-building logic runner.py
  already had inline into a shared helper,
  `policy.constraints.build_mass_cap_dispatch_kwargs(config, year, zone_names, fleet_arrays) -> dict`
  (returns `{}` — no dispatch_kwargs change — when no cap is active, so the default-off harness is
  byte-identical), and calling it from `run_year`'s `dispatch_kwargs` assembly (mirrors runner.py's
  `mass_caps` block exactly, same file/line ownership as the resolver it calls). `run_year` gained
  three new keyword parameters (`mass_cap_enabled`, `mass_cap_tons`, `mass_cap_program`, applied via
  `config.with_overrides(...)` — the file's existing convention for every other gated calibration
  toggle), and `scripts/run_calibration.py`'s own CLI gained matching
  `--mass-cap-enabled`/`--mass-cap-tons`/`--mass-cap-program` flags. Default stays `False`
  everywhere; nothing about a keeper's committed dispatch changes. Unit tests:
  `tests/test_constraints.py::TestBuildMassCapDispatchKwargs` (a mass-cap-enabled backcast
  `ScenarioConfig` actually produces `mass_cap_coeffs`/`mass_cap_rhs`/`mass_cap_labels`; disabled,
  no-program, and quarantined-year configs all still return `{}`). No solve was run to land this —
  it is a pure config/dispatch_kwargs threading change, unit-tested without invoking the LP.
  **Deliberately NOT wired:** `scripts/run_calibration_full.py`'s own ~1000-line argparse block and
  its `solve_and_persist → run_year(...)` call site (the kwargs it forwards) do not yet expose the
  three new parameters — that file's argparse/solve-core surface is large, separately evolving (the
  L-2 lane owns its argparse block for an unrelated `--help`-crash + holdout-gate fix), and touching
  it was out of this pass's scoped file ownership. The recipe below therefore drives
  `scripts/run_calibration.py` directly (a diagnostic run + printed report, not a persisted
  dashboard bundle) rather than the bundle-producing `run_calibration_full.py` — appropriate for a
  PROBE that is explicitly never meant to be a keeper (rule 16). Wiring
  `run_calibration_full.py::solve_and_persist` the same way, if a future session wants a
  dashboard-registrable mass-cap bundle, is a 3-line follow-on: add the same three parameters to
  `solve_and_persist`'s signature, forward them into its `run_year(...)` call (next to
  `negative_renewable_offers`), and add the matching three `argparse` entries next to
  `--negative-renewable-offers` there.

---

## 1. The one-sentence problem

Today RGGI/CARB carbon enters dispatch as an **exogenous $/tCO₂ adder that is applied ISO-wide in
backcast years and is exactly zero in forecast years** (`policy/carbon.py::resolve_carbon_price`;
EM-6). We want (a) forecast years to carry carbon in the merit order through the *same* structure as
the backcast, and (b) the option to represent a genuine **mass budget** whose **dual is the
endogenous allowance price** — the IPM-parity mechanism — without faking the RGGI/CARB number with a
power-only cap that would never bind.

---

## 2. The decision that shapes everything: economy-wide programs are priced, not capped

RGGI and CARB are **multi-sector, banked** allowance markets. The published allowance budget covers
the *whole capped economy* (CARB: electricity + large industry + fuels; RGGI: fossil power ≥25 MW
across all member-state emissions), and a very large **allowance bank** smooths the price across
years. Consequences that are non-negotiable for a faithful model (rule 1):

1. **A power-sector-only mass-cap row over one ISO's fossil fleet would essentially never bind**
   against the economy-wide (or region-wide multi-state) budget, so its dual would be ~0 — nowhere
   near the observed $28–35 (CARB) / $13–24 (RGGI) clearing prices. The real price is set *exogenously*
   to any single ISO's power model, by a market this model does not contain.
2. Therefore **the faithful representation of RGGI/CARB inside this power model is an exogenous
   allowance-price adder** — measured in backcast, projected in forecast — **not** an endogenous
   power-only cap dual. Reaching the observed price via a fabricated power-only cap that binds would
   be exactly the "right number through a mechanism that isn't real" that rule 1 forbids.
3. The **endogenous mass-cap row (dual = price)** is nonetheless the correct, wanted mechanism — but
   it faithfully represents a **power-sector-specific mass budget**: EPA 111(d)/CSAPR, a
   counterfactual "power sector alone must meet this tonnage," or a user scenario cap. That is the
   IPM parity gap PP-2.1 names, and it is real where a power-only budget is the actual binding
   instrument.

**So we build both, as two price *sources* feeding one carbon-cost channel, and we are explicit about
which source represents which real instrument.** This is the core design and it is what lets backcast
and forecast share one structure (§4).

---

## 3. One structure: the `emission_rate × membership` carbon-cost channel

Every path routes carbon through the same two fleet quantities already in `FleetArrays`:
`emission_rate` (tCO₂/MWh, `fleet.py:347`) and a new **per-generator membership weight**
`m[g] ∈ [0,1]` (§5). The effective carbon cost on member generator `g` is always

```
carbon_cost[g,t] = emission_rate[g] · m[g] · p_allowance
```

The *only* thing that differs across modes is **where `p_allowance` comes from**:

| Mode / instrument | `p_allowance` source | How it enters the LP |
|---|---|---|
| Backcast, RGGI/CARB | **measured** auction price (`STATE_CARBON_PRICE_BY_ISO`) | mc adder (price known ex-ante) |
| Forecast, RGGI/CARB | **projected** program price path (floor/ECR escalator + trajectory) | mc adder (price known ex-ante) |
| Any mode, power-sector cap (111/CSAPR/scenario) that binds | **endogenous LP dual** of the mass-cap row | constraint row (price solved) |

The adder path multiplies `m[g]·emission_rate[g]` into `assemble_mc`'s existing `carbon_price` term.
The row path puts `m[g]·emission_rate[g]` as the **row coefficient** on each member column; the KKT
stationarity condition then makes the member generator's shadow marginal cost
`mc[g] + λ·m[g]·emission_rate[g]` — i.e. the dual `λ` *is* the endogenous allowance price, identical
in units and meaning to the adder's `p_allowance`. This is exactly how the existing RPS row's dual is
the REC price (`dispatch.py:_build_rps_row`, `rps_shadow_price`).

**Exactly one source is active per (program, ISO, year, solve).** The resolver (§6) picks it; a
member generator's carbon cost is never double-counted. Cap-off + measured-price is bit-for-bit
today's behaviour (§9 regression gate).

This *is* the EM-6 seam fix's structural home: forecast carbon stops being zero because the resolver
routes forecast RGGI/CARB to the projected adder (and, if a power-sector cap is configured, to the
dual). Sequencing (§11): if W0-P1 lands a bare forward program-price first, this work adopts *that*
value as its projected-adder source — there must be exactly one forward program-price path in the
repo, owned here.

---

## 4. LP row: `_build_mass_cap_rows` (vectorized, rule 2)

One inequality row per active power-sector cap (usually one per ISO-year):

```
Σ_{g ∈ members} Σ_t  m[g] · emission_rate[g] · P[g,t]   ≤   cap_tons
```

Built as a single COO block cloned from `_build_rps_row` (`dispatch.py:342`) — **no hour loop**:

```python
T, vph = layout.T, layout.vars_per_hour
member_idx = np.flatnonzero(member_mask)                    # g: member thermal gens
hours = np.arange(T)[:, None]                                # t
cols = (hours * vph + layout._p_off + member_idx).ravel()    # T · n_member entries
coef = np.tile(m[member_idx] * emission_rate[member_idx], T) # same order as cols
row  = sp.coo_matrix((coef, (np.zeros_like(cols), cols)),
                     shape=(1, layout.total_columns)).tocsr()
# row_lower = -inf, row_upper = cap_tons   (a ≤ inequality)
```

Multiple simultaneous caps (e.g. a CO₂ cap and a NOx cap, or two overlapping budgets) → stack a
`(k, total_columns)` block; still no Python loop over hours, at most a short loop over the ≤2–3 caps.

**Row placement & dual recovery.** Append the mass-cap block **after the import-node rows and
immediately before the RPS row** (`dispatch.py:1675`), so the block is end-anchored:
`[ … | mass_cap (k) | rps (0/1) | reserve (n_res) ]`. Then:

- mass-cap duals: `row_dual[-(self._n_reserve_rows + rps_present + k) : -(self._n_reserve_rows + rps_present)]`
  (when the RPS/reserve tails are absent those terms are 0).
- The RPS index becomes `-1 - self._n_reserve_rows` **unchanged** (mass-cap sits *before* RPS, so
  RPS's distance from the end is unaffected) — but the implementer MUST add a `self._n_masscap_rows`
  field and assert the end-anchor arithmetic in a test, because this is the fragile part.

Sign: HiGHS min problem, `≤` row → dual `λ ≤ 0` in the raw read; report `p_allowance = -λ` ($/tCO₂,
non-negative) exactly as the code negates/keeps other duals per row sense. **Emit the reported
allowance price back onto `DispatchResult`** as `co2_cap_price` (list, one per cap), mirroring
`rps_shadow_price`. Downstream (`results/`, dashboard) reads it as the endogenous carbon price.

**Imports / leakage in the row.** Import nodes and inter-zone flow columns get **zero** coefficient —
the cap is on *in-region* emissions, and imported energy's emissions occur outside the capped
region (correct RGGI/CARB accounting). The leakage channel (a cap raises in-region price → pulls in
uncapped imports) is thereby *represented*, not suppressed: the LP will substitute toward imports up
to the transmission limits. CARB's border carbon adjustment on unspecified WECC imports
(`CARB_UNSPECIFIED_IMPORT_EF = 0.428`, `transmission.py::wecc_border_carbon_adder`) stays as the
leakage *price* on imports and, under the unified resolver, reads the **same** `p_allowance` so it
tracks the dual when the cap path is active. Boundary limitation to document: the dominant real RGGI
leakage path (RGGI states importing coal power from non-RGGI PJM/MISO) mostly lies *outside* each
modeled ISO's intra-ISO transmission, so within-model leakage is a lower bound — state it in the
methodology note, do not patch it with an adder.

---

## 5. Zone → state → membership mapping (`m[g]`)

The model has no per-generator state; zones are multi-state roll-ups (`iso_configs.py`). Membership is
therefore a **per-zone fraction** `m_zone[z] ∈ [0,1]` = the share of that zone's fossil generation
physically inside the program's member states, broadcast to generators by `fleet.zone_idx`:
`m[g] = m_zone[fleet.zone_idx[g]]`. This is forecast-reproducible (state boundaries are fixed) and
vectorized. Cases:

| ISO | Program | Membership | Notes |
|---|---|---|---|
| **CAISO** | CARB | `m_zone = 1.0` all in-state zones; WECC_import node = 0 | Whole ISO ≈ California. Clean. Matches today's ISO-wide adder exactly. |
| **NYISO** | RGGI (NY) | `m_zone = 1.0` all zones | Entire ISO is New York, a RGGI state. Clean. |
| **NEISO** | RGGI (6 NE states) | `m_zone = 1.0` all in-region zones; HQ import node = 0 | All six New England states are RGGI members. Clean. |
| **PJM** | RGGI (partial) | **fractional per-zone**, sourced from EIA-860 in-zone capacity by state | Multi-state roll-up zones spanning RGGI + non-RGGI. See below. |
| **ERCOT / MISO** | none | n/a | No entry — resolver returns no program. |

For CAISO/NYISO/NEISO, `m_zone ≡ 1.0`, so the adder path reproduces the current ISO-wide behaviour
identically (§9 gate). **These three are the clean v1 targets.**

**PJM is fractional and staged.** PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member
through 2023 and exited 1 Jan 2024; PA's entry is enjoined/uncertain) and non-members (OH, IN, KY,
WV, IL, most of PA). The zones are multi-state roll-ups — e.g. `PJM_EMAAC` = NJ+DE+Philadelphia-PA
(RGGI NJ/DE mixed with non-RGGI PA); `PJM_SWMAAC` = MD (RGGI); `PJM_Dominion` = VA+NC (RGGI 2023 only,
0 from 2024). A clean 0/1 zone map is impossible. **Design: `m_zone[z]` = the RGGI-member share of
zone z's fossil *capacity*, computed from EIA-860 plant coordinates → state → RGGI-membership-by-year,
crosswalked to model zones** (rule 14: real data misaligned to our zone boundaries → reconciled
fractional version, documented, not a guess). Because VA's exit and PA's non-entry make the
PJM-RGGI-share cap **loose** over 2023–2025 (RGGI's PJM-state budget vastly exceeds modeled PJM
fossil emissions once you net the non-member majority), the **PJM cap effectively does not bind** and
the faithful representation is again the *adder* at the RGGI price, membership-weighted. **v1 ships
PJM with the fractional adder OFF by default** (needs the EIA-860→state crosswalk intake, §7) and
documents it as the one non-clean case; the mass-cap *row* over PJM is a scenario/analysis tool, not
a keeper default.

Store `m_zone` per (ISO, program, year) in a small registry constant (§7), never a hardcoded per-plant
dict in a `data/` module (rule 24).

---

## 6. The resolver — one function, one active source

Replace the ad-hoc `resolve_carbon_price` fall-through with a program-aware resolver. Proposed home:
`policy/cap_and_trade.py` (new), consumed by `policy/carbon.py` and `policy/constraints.py`.

```
resolve_carbon_program(config, year) -> CarbonProgramResolution | None
    # returns, for the ISO's active program in `year`:
    #   .membership  : m_zone vector (len n_zones)   — always
    #   .price_adder : float | None                  — set on the ADDER path
    #   .cap_spec    : MassCapSpec | None            — set on the ROW path
    # with the invariant: exactly one of price_adder / cap_spec is non-None.
```

Selection logic (deterministic, driven only by `config` + published schedules — no residual tuning):

```
program = CAP_AND_TRADE_PROGRAMS.get(config.iso)          # None → no carbon program
if program is None:                                        #        (ERCOT/MISO)
    return None
membership = program.membership(year)                      # m_zone, per §5

if config.mass_cap_enabled and program.power_sector_cap(year) is not None:
    # ROW path: a genuine power-sector budget (111/CSAPR/scenario) is configured.
    return ...(cap_spec = MassCapSpec(members, membership, cap_tons))
# else ADDER path — the faithful RGGI/CARB representation:
if config.mode == "backcast":
    price = measured_price(program, year)   # STATE_CARBON_PRICE_BY_ISO; None outside series
else:  # forecast
    price = projected_price(program, year)  # floor-escalator + trajectory, §7  (fixes EM-6)
if config.carbon_price != 0:                # explicit scenario override still wins (unchanged)
    price = config.carbon_price
return ...(price_adder = price)
```

`resolve_carbon_price` becomes a thin wrapper returning `.price_adder` (backward compatible for the
scalar-adder call sites at `runner.py:378,585`), and `assemble_mc` receives the membership-weighted
adder (`m_zone`-broadcast) instead of a bare scalar so a fractional-membership adder is expressible.
`get_active_policy_constraints` returns `[cap_spec]` (or `[]`) so the dispatch builder appends the
row. **Both call sites, one resolver — the seam is closed by construction.**

`config.mass_cap_enabled` default **False** (rule: gated new mechanism; cap-off = today). New
`ScenarioConfig` fields (all in the registry, rule 24, and in `run_config.json`):
`mass_cap_enabled: bool = False`, optional `mass_cap_program: str | None` (override which program's
power-sector budget to bind), `carbon_program_price_path: str | None` (name a projected forecast
path). No env-var knobs, no `getattr` literals in the offer path (rule 24).

---

## 7. Data intake (rule 13 — forecast-reproducible)

Three datatypes, all under `data/raw/policy/` with a schema in `data/dictionary/schema/` and a
`curate_*.py` producing validated Parquet in `data/clean/` (follow the **data-intake** skill: schema
first, `write_clean`/`read_clean` seam, per-ISO registry, tmp-`CLEAN_DIR` tests). None touches 2022 /
H1-2026 (rule 22).

1. **`policy/rggi-co2-budgets`** — RGGI regional & per-state annual CO₂ allowance budgets (short
   tons/yr), the CCR (Cost Containment Reserve) and ECR (Emissions Containment Reserve) trigger price
   schedules, and the minimum reserve (floor) price. Source: RGGI, Inc. "Allowance Distribution" /
   Model Rule updated cap trajectory (published to 2030, then the fixed ~2.9 %/yr real decline;
   third-program-review schedule). The **power-sector cap row** for a RGGI ISO uses that ISO's
   member-state budget sum; the **projected adder** for forecast uses the floor/ECR escalator as the
   price ceiling/floor band. Cite the exact table (rule 5).
2. **`policy/carb-cap-schedule`** — CARB annual allowance budget (MMT CO₂e, declining per the 2022
   Scoping Plan / the amended post-2030 cap-decline) and the **Auction Reserve (floor) price** with
   its statutory 5 %+CPI annual escalation. The floor escalator is the natural **forecast allowance
   price** for CAISO (prices have hugged the floor+premium band). Source: CARB Cap-and-Trade
   Regulation §95870–95911 and the annual auction-reserve-price notice.
3. **Measured prices** already exist: `STATE_CARBON_PRICE_BY_ISO` (`constants.py:1263`) for
   2023–2025 backcast — keep as the backcast adder source; extend forward only as *realized* data
   lands (never into holdout years).

Registry constants (in `constants.py`, cited): `CAP_AND_TRADE_PROGRAMS` (ISO → program def:
member states, membership-fraction source, measured-price ref, projected-path ref, power-sector-cap
ref), `RGGI_STATE_CO2_BUDGET`, `CARB_ALLOWANCE_BUDGET`, `CARB_FLOOR_PRICE`, and
`PJM_RGGI_ZONE_SHARE` (the §5 fractional map, from the EIA-860→state crosswalk).

---

## 8. Banking / borrowing (LP-only simplification — decided: none in v1)

**No banking, no borrowing.** Each year's cap is enforced independently within that year's solve. The
runner solves years sequentially with no allowance-bank state threaded in `prior_results`, and rule 9
(one-pass, no within-year iteration) plus the sequential year loop (rule 12) forbid the multi-year
coupled program a true bank needs. Documented consequences:

- The **endogenous dual is the "no-bank, this-cap-binds-this-year" allowance price** — an *upper
  bound* on the true banked price in a tight year, and it drops to ~0 in a loose year rather than
  being held up by bank scarcity value. It is a **scenario/analytic price** ("what would clear if the
  power sector alone met this tonnage this year with no bank"), **not a point forecast of the RGGI/CARB
  market price** — which is precisely why RGGI/CARB themselves use the *measured/projected adder*
  path, where the banked reality is already embedded in the observed price.
- This is the honest reason the two-source design (§2) exists: banking is exactly what makes the
  real programs' price exogenous to a single-year power LP.
- **Future extension (out of scope, noted):** a cross-year bank could be a single carry scalar
  `bank[y] = bank[y-1] + cap[y] − emissions[y]` threaded through `prior_results`, priced by a simple
  Hotelling rule — but it breaks one-pass year independence and needs its own design; do not
  smuggle it in.

**Rule-13 admissibility note (W8 follow-on, filed explicitly per the 2026-07 gap register
G-29/W8 item).** A cross-year bank is not merely deferred for LP-mechanics convenience (rule 9) —
it also fails CLAUDE.md rule 13's admissibility test on its own terms, which is a second,
independent reason never to smuggle one in later as a "just thread `prior_results`" patch:

- **The test:** could this quantity be produced for a forward year from forward drivers, and would
  it respond to changed conditions? A bank *balance* is a genuine physical/market state (RGGI and
  CARB both publish participant-level banked-allowance totals), so in principle a bank-balance
  *input* could pass the test if it were sourced from the published program-wide bank statistics
  (RGGI's Auction Reserve/CCR reports show the total bank; CARB's Cap-and-Trade quarterly reports
  do too) and *held exogenous* — never solved as a function of this model's own single-ISO,
  single-sector dispatch.
- **What would fail it:** a bank recursion computed as `bank[y] = bank[y-1] + cap[y] −
  emissions[y]` using **this model's own emissions** is not a forward-reproducible measured input —
  it is an *outcome* of the very dispatch the bank is meant to influence, threaded back into next
  year's price. That is a self-referential residual by construction (worse than rule 1's ordinary
  "fitted adder" case, because it compounds year over year), and it has no forward analogue: a real
  utility's bank balance depends on the ENTIRE regulated economy's multi-sector emissions, not one
  ISO's power-sector LP. A single-ISO model computing "its own" bank balance would silently invent a
  bank that has no relationship to the real RGGI/CARB bank.
- **The only rule-13-admissible form**, should a future design want a bank at all: read the
  *published, whole-program* bank-balance series as an external, un-modified time series (like
  `STATE_CARBON_PRICE_BY_ISO` today) and use it only to justify the **adder path's** trajectory
  shape (e.g. a bank-drawdown-consistent price escalation), never to feed an endogenous single-ISO
  mass-cap dual. This is consistent with §2's core finding: the adder path is the faithful
  representation of a banked, multi-sector market; the row path's dual is honestly a power-sector,
  no-bank scenario price and should stay that way rather than gain a fake bank state.
- **Conclusion: no code changes recommended.** The current design (no banking, §8's existing text)
  is both the LP-simplicity-correct choice (rule 9) and the rule-13-admissible choice. This
  subsection exists so the "no banking" decision is documented with its own admissibility argument
  rather than only a one-line "out of scope" note, per this lane's task scope.

---

## 9. Tests & the exactness gate

Per PP-2.1 and CLAUDE.md testing pattern (trivial case first):

1. **Trivial binding cap (1 gen? use 2):** 1 zone, 2 thermal gens (cheap-dirty vs expensive-clean),
   24 h, cap set between "all dirty" and "all clean" emissions. Assert (a) the cap binds (emissions =
   cap to tolerance), (b) the dual `p_allowance` equals the analytic switching price
   `(mc_clean − mc_dirty)/(rate_dirty − rate_clean)`, (c) member dispatch shifts by the expected
   amount. This is the "dual equals expected switching price" gate PP-2.1 requires.
2. **Cap-off exactness (regression):** for each of CAISO/NYISO/NEISO, a backcast year with
   `mass_cap_enabled=False` reproduces the current run **bit-for-bit** (same objective, prices,
   emissions) — because the adder path with `m_zone≡1` is algebraically today's ISO-wide adder.
   This is the "cap-off reproduces today's results exactly" gate.
3. **Seam closure (EM-6):** a forecast year now carries a non-zero carbon adder (measured→projected)
   for CAISO/NYISO/NEISO; assert `resolve_carbon_program(...).price_adder > 0` where a program exists.
4. **Membership vectorization:** `m[g]` is `m_zone[zone_idx[g]]`; assert import/flow columns have zero
   cap coefficient; assert no `for t in range(...)` in the builder (mirror the existing rule-2 test).
5. **Dual index arithmetic:** with RPS on + reserve on + mass-cap on simultaneously, assert each of
   the three end-anchored duals lands on its own row (the fragile §4 arithmetic).
6. **PJM fractional adder:** a synthetic 2-zone PJM-like case with `m_zone=[1.0, 0.0]` charges carbon
   only to zone-0 fossil; verify the zone-1 merit order is unchanged.

---

## 10. What this is NOT (scope guards)

- **Not** a fitted match to observed allowance prices — the measured price is a *reproducible input*
  (rule 13), and the endogenous dual is a *scenario* price (§8), never tuned to a residual (rule 1).
- **Not** a multi-sector allowance market — the endogenous dual is power-sector-only and is honestly
  labelled as such (§2).
- **Not** a capacity-evolution change — this is a dispatch-layer constraint. (In backcast there is no
  capacity evolution; the cap-row affects only dispatch, exactly like RPS.)
- **Not** a new NOx/SO₂ system — the row is CO₂-first; a NOx mass cap is the same builder with
  `nox_rate` and is a trivial follow-on once EM-1/EM-2's unit bug is fixed, but it is out of this
  scope.
- **Not** a holdout touch — no 2022/H1-2026 solves, scoring, or data intake (rule 22).

---

## 11. Sequencing

1. **After / alongside the EM-6 seam fix (W0-P1).** If W0-P1 lands a forward program-price first,
   consume its value as this design's projected-adder source (§3, §6) — do not create a second
   forward carbon path. If W0-P1 has not landed, this work *is* the seam fix's home and defines the
   projected path in `policy/cap_and_trade.py`; W0-P1 then adopts it.
2. Land the **adder unification + membership** first (closes EM-6, passes the §9.2 exactness gate,
   zero behavioural change with cap off) — this is the low-risk core.
3. Land the **mass-cap row + dual** second (the PP-2.1 IPM-parity mechanism), default off, validated
   on the trivial binding case.
4. **Data intake** (§7) can proceed in parallel via the data-intake skill; the row is inert until the
   cap schedules land.
5. PJM fractional membership last (needs the EIA-860→state crosswalk); ships OFF.

---

## 12. Files touched (implementation map)

| File | Change |
|---|---|
| `policy/cap_and_trade.py` *(new)* | `CarbonProgramResolution`, `MassCapSpec`, `resolve_carbon_program`, `measured_price`/`projected_price`, membership resolution |
| `policy/carbon.py` | `resolve_carbon_price` → thin wrapper over resolver's `.price_adder`; docstring update |
| `policy/constraints.py` | `get_active_policy_constraints` returns `[cap_spec]` from the resolver |
| `model/dispatch.py` | `_build_mass_cap_rows`; append block before RPS (§4); `_n_masscap_rows`; `co2_cap_price` on `DispatchResult`; thread `mass_caps` arg through `run_dispatch`/model class |
| `data/fleet.py::assemble_mc` | accept membership-weighted (per-gen) carbon adder (already `np.ndarray|float`; broadcast `m_zone[zone_idx]·price`) |
| `config/scenarios.py` | `mass_cap_enabled`, `mass_cap_program`, `carbon_program_price_path`; register in the sweep-param dict |
| `config/constants.py` | `CAP_AND_TRADE_PROGRAMS`, `RGGI_STATE_CO2_BUDGET`, `CARB_ALLOWANCE_BUDGET`, `CARB_FLOOR_PRICE`, `PJM_RGGI_ZONE_SHARE` (all cited) |
| `data/raw/policy/{rggi-co2-budgets,carb-cap-schedule}/` + schemas + `curate_*.py` | §7 intake (data-intake skill) |
| `runner.py` | call-site: pass `get_active_policy_constraints(config, year)` into the dispatch builder alongside `rps_target` |
| `results/` + dashboard | surface `co2_cap_price` as the endogenous carbon price where a cap binds |
| tests | `test_constraints.py`, `test_cap_and_trade.py`, `test_dispatch.py` (dual index), extend `test_carbon.py` |

---

## 13. NOx mass-cap follow-on (W8, filed explicitly per the 2026-07 gap register)

Out of scope for this wave (§10), filed here as its own section (rather than the one-line ledger
bullet it was previously scattered across) so a future implementer has a starting design and this
lane's admissibility judgment on record.

### 13.1 What a NOx cap-and-trade row would represent

The only NOx cap-and-trade program that actually covers plants in this model's six ISOs is EPA's
**Cross-State Air Pollution Rule (CSAPR) ozone-season NOx trading program** (the successor to the
NOx Budget Trading Program) — a **seasonal** (May 1–Sep 30 ozone season, not full-year) allowance
market with state-level budgets, covering most PJM/MISO/NYISO/NEISO-footprint states (CSAPR does
not cover ERCOT or CAISO — Texas and California are outside CSAPR's ozone-transport regions).
`_build_mass_cap_rows` (§4) generalizes directly: swap the coefficient basis from
`emission_rate` (CO2) to `fleet_arrays.nox_rate`, and swap `CAP_AND_TRADE_PROGRAMS`'s CO2-program
registry for a parallel `NOX_PROGRAMS` (state membership × EPA-published seasonal allowance
budget, tons NOx).

### 13.2 The structural wrinkle CO2 does not have: the cap is seasonal, not annual

RGGI/CARB CO2 caps run the full calendar year, so `_build_mass_cap_rows`'s "one row, all 8760
hours" form (§4) applies unmodified. CSAPR's NOx budget applies **only** to the ozone season
(May–September, ≈ 3,672 of 8,760 hours) — the row must sum member-generator NOx emissions over
**only those hours**, not the full year. This needs one addition to the builder: an optional
`hour_mask` (boolean, length `T`) that zeroes the column-selection outside the covered season,
rather than the unconditional `hours = np.arange(T)` the CO2 row uses today. Still fully vectorized
(rule 2) — `hours = np.arange(T)[hour_mask]` before the same `np.tile`/`ravel` construction — no
new Python loop.

### 13.3 Rule-13 admissibility

**Passes the test, with an honesty caveat that differs from CO2's.** EPA's per-state CSAPR
allowance budgets are published, forward-reproducible (a future year's budget is a matter of public
record, not a fitted quantity), and respond to changed conditions (EPA periodically re-allocates
budgets; a state's membership can change under a new CSAPR update rule) — same shape of argument as
RGGI's/CARB's published CO2 budgets (§7). The row's membership mask (which generators sit in
CSAPR-covered states) is exactly analogous to the CO2 row's per-generator membership
(`per_generator_membership`, §5) and can reuse the same EIA-860 plant→state machinery.

**The caveat: unlike CO2, there is today no measured NOx allowance PRICE series in this repo**
(`STATE_CARBON_PRICE_BY_ISO` has no NOx analogue), and CSAPR's ozone-season NOx allowance price has
historically been thin/volatile with periods of near-collapse (unlike RGGI/CARB CO2, which have
sustained, actively-traded clearing prices this model's CO2 adder path measures directly). That
means — mirroring §2's reasoning for why a power-only CO2 cap would be fake — there is currently no
adder-path measured price to validate a NOx row's endogenous dual against, and no existing
"NOx price is real and load-bearing" claim this repo makes anywhere today. **Recommendation:** build
the row (§13.1–13.2) as a genuine, cited, rule-13-admissible mechanism, but ship and describe it
purely as a **scenario/counterfactual tool** ("what would a tightened/hypothetical CSAPR-style NOx
budget cost this fleet"), default off, never claimed as a calibration or validation mechanism the
way §14's CO2 RGGI probe is — there is no honest observed-price target to score it against today.
If EPA CSAPR auction/secondary-market NOx price data becomes available and is added to the repo,
this recommendation should be revisited (it would then support the same adder-vs-row structure CO2
has).

### 13.4 Files (sketch, unbuilt)

Same shape as the CO2 wiring: `config/constants.py::NOX_PROGRAMS` (state membership + EPA ozone-
season budget, cited), `policy/cap_and_trade.py::resolve_nox_program` (or generalize
`resolve_carbon_program` to a `pollutant` parameter spanning `"co2"`/`"nox"`), `model/dispatch.py`
gains the `hour_mask` parameter on `_build_mass_cap_rows`, `policy/constraints.py::
get_active_policy_constraints` grows a second, independent `MassCapSpec` in its returned list when
a NOx program is configured (the dual-index arithmetic in §4/§9.5 already handles multiple stacked
caps). No SO2 equivalent is proposed: the Title IV Acid Rain SO2 allowance market has traded near
$0/ton for the past decade (post-MATS-rule oversupply), so an SO2 mass-cap row would almost never
bind — the same "fake mechanism" trap §2 already ruled out for a power-only CO2 cap.

---

## 14. RGGI dual-vs-auction-price validation probe — runnable recipe (2026-07-06, Lane L-8)

**Purpose.** With the G-29 wiring above landed, this is now runnable (it was not, before this
lane): compare the mass-cap row's endogenous dual (`co2_cap_price`) against the observed RGGI
auction clearing price, for a RGGI ISO where the row is configured to bind at (close to) the
publicly reported regional/member-state emissions level. This is a **diagnostic probe**, never a
keeper input and never run in this session (rule 12/16 — this section is a spec, not a solve
report).

### 14.1 Which ISO-years

**NYISO, 2023–2024** (single-state RGGI member — `m_zone ≡ 1.0` everywhere, §5's "clean v1
target" — so the row's membership is exact with no fractional-PJM complication). Use the
already-registered `nyiso-41-hub-prices` keeper's config as the base (`results/calibration/
nyiso41_hubprices/run_config.json`) so every other lever (offer curves, floors, etc.) matches a
known-good backcast; do **not** use a year outside 2023–2025 (rule 22 — 2022/H1-2026 stay
quarantined). NEISO 2023–2024 is a reasonable second ISO for the same probe (also `m_zone≡1.0`,
6-state RGGI region) if a cross-ISO check is wanted; CAISO is a CARB (not RGGI) probe and would
compare against the CARB auction settlement price instead (a separate, equally valid probe with the
same recipe, swapping the RGGI reference series for CARB's).

### 14.2 Which config

Using the new `scripts/run_calibration.py` CLI (this lane's G-29 wiring):

```
uv run python scripts/run_calibration.py \
  --iso NYISO --year 2023 2024 --hours 8760 \
  --mass-cap-enabled \
  --mass-cap-tons <TARGET_TONS>
```

**Reading the dual.** `main()`'s `_report_year` does not print `co2_cap_price` (it predates this
lever and reports the usual price/generation/CO2 diagnostics only), so the CLI's stdout alone will
not show the allowance price — a probe script should instead call `run_year(...)` directly (as
`main()` does internally) and read the returned `result.co2_cap_price` (a `list[float]`, one entry
per active cap; `result` is P1 unless `--commitment` is passed, matching the "P1 is the main run"
convention). This is a ~10-line wrapper around the existing `run_year` call in `main()`, not a new
mechanism.

`<TARGET_TONS>` should be set to a level **near the modeled fleet's own realized in-region fossil
CO2 emissions for the year** (read from the `nyiso-41-hub-prices` keeper's own registered CO2
total on the dashboard/`legitimacy_diagnostics.json` C5a row — NOT the full published RGGI
regional/member-state budget, which is loose by design and would leave the row inert, per §2's
finding that a power-sector-only row against the real published budget essentially never binds).
The point of the probe is a **counterfactual "what if the power sector alone had to hit its own
historical tonnage"** — deliberately NOT the real RGGI cap — so the row is guaranteed to bind at
(or just above) that level, giving a nonzero, interpretable dual to compare against the observed
auction price. Sweeping `<TARGET_TONS>` from slightly-below to
slightly-above the realized tonnage traces out the row's dual-vs-tightness curve, which is the
useful diagnostic output (not a single number).

Omitting `--mass-cap-tons` instead pulls the real published per-state RGGI budget
(`_published_power_sector_budget`, §7) — expected, per §2, to leave the row **slack** (dual ≈ 0):
running that config too is a useful negative-control leg of the same probe, confirming the "a
power-only row against the real budget doesn't bind" claim empirically rather than just by
argument.

### 14.3 What counts as pass / what the probe teaches

This is explicitly **not a pass/fail gate** — there is no rule-13-admissible reason to expect the
row's no-bank, power-sector-only dual to equal the banked, multi-sector RGGI auction price (§2, §8);
a probe that "matched" would be a coincidence, not evidence of anything, and must not be read as
validating the mechanism. What the probe legitimately establishes:

1. **Sanity check on the mechanism itself:** at the realized-tonnage target, the dual should be
   **positive and of a plausible order of magnitude** relative to the measured RGGI price
   (§14.2's config) — a dual of $0 or a nonsensical (e.g. negative, or many-orders-of-magnitude-off)
   value would indicate a wiring bug (dual sign, row placement, unit conversion), not a real
   modeling finding. This is the practical value of running it: an end-to-end sanity check on
   `_build_mass_cap_rows`'s dual recovery (§4) against a real-scale ISO-year, which the trivial
   2-gen unit test (§9.1) cannot exercise (real fleet size, real offer curve, real co-optimized
   reserve/RPS/storage rows stacked alongside the cap row per §9.5's dual-index arithmetic).
2. **The negative control (§14.2, no explicit `--mass-cap-tons`):** confirms the row stays slack
   against the real published budget, i.e. that §2's central design argument ("a power-sector-only
   row against the real RGGI/CARB budget would never bind") is empirically true for this model's
   fleet, not just asserted from first principles.
3. **NOT evidence for or against calibration quality.** The dual-vs-tonnage sweep (§14.2) is a
   property of this ISO's own fleet-wide CO2 marginal abatement cost curve, which is an interesting
   number to have on record but is not compared against any external "correct" curve — there is no
   such published series to check it against.

**Registration.** If run, register as a dashboard PROBE (rule 15), never a keeper candidate (rule
16 — this is explicitly a diagnostic, not a calibration run), with a sidecar note stating the
`--mass-cap-tons` value(s) swept and both legs (bound-to-realized-tonnage and negative-control).

---

## Implementation prompt (paste into a fresh session)

```
Implement the emissions mass-cap / cap-and-trade LP constraint per
docs/handoffs/emissions-mass-cap-plan-2026-07.md. Read that plan and CLAUDE.md first
(rules 1, 2, 5, 9, 13/14, 22, 24). Work on branch phase-2/emissions-mass-cap. Do NOT
solve, score, or intake any 2022 or H1-2026 data (rule 22).

Build in this order, each with tests green before the next:

1. Unified carbon resolver + membership (closes EM-6, zero behavioural change cap-off):
   - New policy/cap_and_trade.py: CarbonProgramResolution, MassCapSpec, and
     resolve_carbon_program(config, year) returning membership (m_zone vector) plus
     EXACTLY ONE of price_adder / cap_spec, per plan §6. Invariant-assert that.
   - CAP_AND_TRADE_PROGRAMS registry in constants.py: CAISO→CARB, NYISO→RGGI(NY),
     NEISO→RGGI(6 NE states) with m_zone≡1.0; PJM→RGGI with a fractional m_zone
     (PJM_RGGI_ZONE_SHARE, default-off adder). ERCOT/MISO → no entry. Cite every value
     (rule 5); no off-registry knobs (rule 24).
   - Rewire policy/carbon.py::resolve_carbon_price to return resolver.price_adder
     (backward-compatible scalar for runner.py:378,585). Forecast RGGI/CARB now returns
     the PROJECTED program price (CARB floor escalator / RGGI floor-ECR band, §7), not 0.
   - assemble_mc (data/fleet.py): accept the membership-weighted adder
     (m_zone[zone_idx]·price) — it already types carbon_price as ndarray|float.
   - GATE: mass_cap_enabled=False + backcast reproduces current CAISO/NYISO/NEISO runs
     BIT-FOR-BIT (plan §9.2). This must pass before step 2.

2. Mass-cap row + endogenous dual (PP-2.1 IPM parity, default off):
   - dispatch.py::_build_mass_cap_rows cloned from _build_rps_row (VECTORIZED, no hour
     loop, rule 2): coefficient m[g]·emission_rate[g] on member P[g,t] columns, ≤ cap.
     Import/flow columns get zero coefficient (plan §4 leakage).
   - Append the block after import-node rows, immediately before RPS (plan §4). Add
     self._n_masscap_rows; recover duals end-anchored; report co2_cap_price = -λ on
     DispatchResult. Add the simultaneous RPS+reserve+cap dual-index test (§9.5).
   - policy/constraints.py::get_active_policy_constraints returns [cap_spec] from the
     resolver; thread it through runner.py into the dispatch builder alongside rps_target.
   - New ScenarioConfig fields: mass_cap_enabled=False, mass_cap_program=None,
     carbon_program_price_path=None; register in the sweep-param dict; appear in
     run_config.json (rule 24).
   - GATE: the trivial 1-zone/2-gen/24h binding-cap test — cap binds and the dual equals
     (mc_clean−mc_dirty)/(rate_dirty−rate_clean) (plan §9.1).

3. Data intake (data-intake skill, schema-first): data/raw/policy/rggi-co2-budgets and
   carb-cap-schedule → schema + curate_*.py + clean parquet + tmp-CLEAN_DIR tests (§7).
   The row stays inert until schedules land; land the code path with a small fixture
   first if the published tables aren't in-repo yet.

Honesty constraints (rule 1): the endogenous dual is a POWER-SECTOR, NO-BANK, scenario
allowance price (plan §2, §8) — RGGI/CARB themselves use the measured/projected ADDER,
because their real price is set by a banked multi-sector market this model does not
contain. Do NOT fabricate a power-only cap that binds just to reproduce the observed
$/ton, and do NOT tune anything to a residual. No banking/borrowing (§8) — document it.
PJM ships with the fractional adder OFF (needs the EIA-860→state crosswalk).

Deliverables: the code above, all tests in plan §9, a short CHANGELOG entry, and a
/sync-docs pass on model-methodology-spec.md (emissions/policy sections) +
docs/codebase/05-policy.md. Commit and push (small source-only commits may use git push;
per the 413 workflow switch to mcp__github__push_files if a push 413s). If any backcast
run is produced, register it on the dashboard (rule 15). Do not open a PR unless asked.
```
