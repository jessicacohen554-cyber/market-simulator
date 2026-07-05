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

---

## Implementation status (2026-07-05)

Everything in this plan is implemented and merged; the mechanism is **default-off** (rule 24) and
cap-off backcast is bit-for-bit today's behaviour (§9.2 gate). Ledger by design section:

| Design section | Landed in | Where |
|---|---|---|
| §3 unified `emission_rate × membership` channel; §6 resolver | ✅ | `policy/cap_and_trade.py` (`resolve_carbon_program`, `CarbonProgramResolution`, `MassCapSpec`, `measured_price`/`projected_price`, `_membership`, `_power_sector_cap`, `_published_power_sector_budget`) |
| §6 `resolve_carbon_price` → thin `.price_adder` wrapper (EM-6 seam) | ✅ | `policy/carbon.py` |
| §6 `get_active_policy_constraints` returns `[cap_spec]` | ✅ | `policy/constraints.py` |
| §4 vectorized `_build_mass_cap_rows` (rule 2, no hour loop); end-anchored block before RPS; `_n_masscap_rows`; `co2_cap_price = -λ` on `DispatchResult` | ✅ | `model/dispatch.py` |
| §6 gated `ScenarioConfig` fields (`mass_cap_enabled`/`mass_cap_program`/`mass_cap_tons`/`carbon_program_price_path`), default off, in sweep-param dict + `run_config.json` | ✅ | `config/scenarios.py` |
| §5/§7 registry constants, all cited: `CAP_AND_TRADE_PROGRAMS`, `CARB_ALLOWANCE_BUDGET`, `CARB_FLOOR_PRICE`, `RGGI_STATE_CO2_BUDGET`, `SHORT_TON_TO_METRIC_TONNE`, `PJM_RGGI_ZONE_SHARE` | ✅ | `config/constants.py` |
| §5 membership-weighted (per-gen) carbon adder | ✅ | `data/fleet.py::assemble_mc` (accepts `ndarray`) |
| §7 data intake (schema + curate + cited raw CSV) | ✅ | `data/raw/policy/{carb-cap-schedule,rggi-co2-budgets}/`, `data/dictionary/schema/*.schema.yaml`, `scripts/curate_{carb_cap_schedule,rggi_co2_budgets}.py` |
| §10 call-site threading `get_active_policy_constraints(config, year)` → dispatch builder | ✅ | `runner.py` |
| §9.1–§9.6 tests incl. trivial binding-cap dual = `(mc_clean−mc_dirty)/(rate_dirty−rate_clean)`, cap-off regression, simultaneous RPS+reserve+cap dual-index, membership vectorization, no-hour-loop assertion | ✅ | `tests/test_cap_and_trade.py`, `tests/test_dispatch.py::TestMassCapConstraint` |

**Dispatch wiring is NOT blocked / NOT missing.** The one open question this plan flagged for the
policy-side implementer — whether `dispatch.py` consumes policy constraint rows — is resolved:
`dispatch.py` fully consumes the mass-cap block (`mass_cap_coeffs`/`mass_cap_rhs`/`mass_cap_labels`
args → `_build_mass_cap_rows` → end-anchored dual → `co2_cap_price`), threaded from `runner.py`.
No dispatch-side wiring remains.

**Non-blocking follow-ons (as designed, deferred — not gaps):**

- **PJM fractional membership ships OFF** (§5, §11): `PJM_RGGI_ZONE_SHARE = {}`, so PJM membership
  resolves all-zeros and the PJM RGGI adder is a no-op. Populating it needs the EIA-860 plant-
  coordinate → state → RGGI-membership-by-year crosswalk intake (§7) — a data step, not a code gap.
- **Per-state RGGI budgets** (§7): only the regional `RGGI` total is landed; a RGGI ISO's row uses
  the region-wide over-bound (correctly slack) until the per-state allowance-distribution table is
  intaken.
- **Forecast adder uses an escalator on the last measured price**, not the `CARB_FLOOR_PRICE`
  series directly (`projected_price`, `escalation_rate`); `CARB_FLOOR_PRICE` is landed as the cited
  floor-band artifact. A future refinement could floor the projection at that band.
- **No banking/borrowing** (§8, by design): the endogenous dual is the power-sector, no-bank,
  single-year scenario allowance price — an upper bound in a tight year, ~0 in a loose one — never a
  point forecast of the banked RGGI/CARB market price. A cross-year bank remains explicitly out of
  scope (breaks rule-9 one-pass year independence).
- **NOx/SO₂ mass cap** (§10): out of scope; the same builder with `nox_rate` is a trivial follow-on.

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
