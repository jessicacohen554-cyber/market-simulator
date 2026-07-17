# CX-4 — Data-Center Load Block + Electrification Adder: Design Memo (2026-07, G-34)

> **ℹ️ MECHANISM LANDED (2026-07-17).** Since this memo was written, the DC block has
> been implemented (`ScenarioConfig.datacenter_load_path` off/low/mid/high +
> `constants.DATACENTER_ADDITIONS_MW`; `DATACENTER_ZONE_SHARE` still empty ⇒
> load-share siting). Remaining work — trajectory currency, published siting shares,
> BAU posture decision — is chartered as **FF-1C** in
> `docs/forecast-development-plan-2026-07.md`. The design below stays citable as the
> spec; the "zero DC symbols" verification note reflects the 2026-07-06 tree, not HEAD.

**Status:** design only. No `src/` changes in this deliverable. This memo expands
`docs/handoffs/capacity-economics-plan-2026-07.md` §4 (CX-4) into an implementation-ready
specification and reconciles it with the probability-bounds program's data-center axis
(`docs/handoffs/probability-bounds-plan-2026-07.md` §1.1/§2.1). Implementation belongs to the
capacity-economics lane (which owns `capacity.py`) and the demand pipeline in `runner.py`;
it starts only after this memo is accepted.

**Verified against `origin/main` at branch point (2026-07-06).** Confirmed there are currently
**zero** data-center symbols anywhere in `src/` — the only occurrences of "data center" are two
comments in `constants.py` (lines 709, 747) noting the boom is *implicitly buried* in the
`DEMAND_GROWTH_RATES` near-term rates. This gap is the CX-4 target and also blocks the PB program's
DC axis (PB plan §1.1 marks `datacenter_load_gw` "**new**, gated on PP-3.3's flat-adder mechanism"
— that mechanism is what this memo designs).

---

## 0. Scope guard

**In scope (design targets):** `config/scenarios.py` (`ScenarioConfig` fields + a resolver),
`config/constants.py` (per-ISO trajectory + siting tables), `runner.py` demand assembly
(`_scale_demand` and its call sites), and — for the electrification sketch — a profile-loader
seam.

**Explicitly NOT touched:** `model/capacity.py`. The DC block enters the model as **demand**
(a change to `year_demand`/`peak_demand` in `runner.py`), and the capacity screens pick it up
**for free** through the peak/energy quantities they already consume. This is the crucial
ownership fact that lets CX-4 land without colliding with the capacity lane while it holds
`capacity.py` (§7).

**Rule alignment.** Every number is cited to a published primary source (rule 5). Every tunable
lands in `ScenarioConfig`/`constants.py` and echoes to `run_config.json` (rule 24) — no env-var
knobs, no per-plant dicts, no `getattr` fallbacks. The block is a **scenario axis, not a fitted
adder** (rule 23): its levels come from ISO forecasts and interconnection queues, never from a
backcast residual. Forecast-mode-only by construction; backcast keepers pin measured load (rule 22
holdout discipline preserved — see §6).

---

## 1. Problem statement (current state, verified)

`_scale_demand` (`runner.py:230-245`) applies a single compound scalar to the frozen weather-year
hourly shape:

```python
factor = 1.0
for y in range(config.weather_year, year):
    factor *= 1.0 + _get_growth_rate(config, y)   # resolve_demand_growth_rate
return base_demand * factor                        # base_demand shape (n_zones, T)
```

`_get_growth_rate` → `resolve_demand_growth_rate` reads `DEMAND_GROWTH_RATES[iso][path][era]`
(`constants.py:712-744`), whose near-term entries are annotated *"elevated by data center and
industrial load"* (`constants.py:709`). Three consequences, all structural errors (rule 1 —
wrong mechanism, not a residual to tune):

1. **Wrong shape.** DC load is near-flat (annual load factor ≈ 0.8–0.95); the system weather-year
   shape it inherits is peaky (ERCOT summer LF ≈ 0.55). Growing a flat block with a peaky scalar
   **overstates peak growth and understates energy growth** per MW of DC — exactly backwards for
   the one load type whose defining trait is flatness.
2. **Not separable.** The DC path cannot be varied independently of organic growth — the single
   most-asked forecast scenario question ("what if the AI buildout is half / double?"). It is
   fused into `demand_growth_path`.
3. **No end-use reshaping.** Electrification (heat pumps, EVs) *reshapes* hours (winter-morning
   heat-pump ridge, EV evening) — a scalar on a fixed shape cannot represent it at all. (Audit
   PP-3.3 "end-use reshaping remains a documented limitation".)

**Downstream blast radius.** Because the capacity screens (`apply_economic_retirements`,
`apply_reserve_margin_build`, `apply_economic_new_entry`) key on `peak_demand` and the hourly
`year_demand` threaded via `prior_results`, an overstated peak inflates the reliability floor and
the reserve-margin backstop, over-building peakers and manufacturing phantom scarcity revenue. The
DC representation error therefore propagates directly into the capacity-economics recalibration
the sibling lane is running — which is why CX-4 is scoped alongside it.

---

## 2. Driver data — per-ISO inventory and rule-13 admissibility

**Rule-13 admissibility test (CLAUDE.md rule 13):** *could this same quantity be produced for a
forward year from forward drivers, and would it respond to changed conditions?* A published ISO
large-load forecast / interconnection queue passes cleanly: it is a **forward-looking projection
keyed to interconnection agreements and in-service dates**, it regenerates every forecast vintage,
and it responds to changed conditions (queue withdrawals, policy, siting). It is an *input*
(a projected load path), never an *outcome* fed back to force a match — so it is admissible even
though it is "measured," and it is admissible in **forecast mode only** (backcast pins actuals).

The distinction that keeps it clean: we ingest the **queue/forecast MW trajectory** (a forward
driver), not any realized post-hoc DC generation. There is no residual-pinning channel here.

### 2.1 Inventory

| ISO | Primary source (forward driver) | Headline published figures | Path anchors (low / mid / high) | Rule-13 |
|---|---|---|---|---|
| **ERCOT** | ERCOT 2025 *Report on Existing & Potential Electric System Constraints and Needs*; ERCOT Large Load Integration program / large-flexible-load (LFL) officer updates; the large-load interconnection queue | Large-load queue **≈ 226 GW** (Nov 2025) vs **63 GW** (end-2024) — ~4× in one year; **~77 %** of large load targets in-service by 2030; ERCOT adjusted peak forecast **≈ 138 GW by 2030**. ~70 %+ of the queue is data centers. | **low** = signed-interconnection-agreement (IA-backed) subset; **mid** = ERCOT contracted/planning subset (the officer "planning" case); **high** = officer high / total credible LFL case | ✅ IA-backed queue regenerates each vintage; responds to withdrawals & SB-6 load-forecast rules |
| **PJM** | PJM 2025 *Long-Term Load Forecast Report* (data-center component is published as an explicit decomposition of the 15-yr forecast) | Data-center-driven **peak growth ≈ 30 GW of ~32 GW total, 2025→2030**; 15-yr summer peak **+70 GW to ≈ 220 GW**; in the 2027/28 BRA forecast **~5,100 MW of a 5,250 MW** y/y increase is DC | **low** = signed-ISA subset; **mid** = published DC component of the base forecast; **high** = PJM high-DC sensitivity | ✅ published DC decomposition, re-issued annually; PJM's stricter 2025 DC vetting shows it responds to conditions |
| **CAISO** | CEC 2024 IEPR *Data Center Forecast* (24-IEPR-03), adopted into the California Energy Demand 2024-2040 forecast CAISO plans to | DC load **+1.8 GW by 2030, +4.9 GW by 2040**; CAISO peak **48.3 GW (2024) → ≈ 68 GW (2040)**, much of the rise attributed to DC | **low** = 0 (see note); **mid** = IEPR DC adder; **high** = IEPR high-DC / CAISO "Large Load Considerations" case | ✅ IEPR adder is a forward scenario input, re-forecast each cycle |
| **NYISO** | NYISO 2025 *Load & Capacity Data Report* ("Gold Book") large-load adjustments | **19 large-load projects, >3 GW** combined seeking interconnection; **>10 GW** targeted in-service by 2031; avg project **≈ 300 MW** (mix of DC + Micron semiconductor fab) | **low** = 0; **mid** = Gold Book large-load adjustment subset; **high** = total large-load queue | ✅ Gold Book large-load adjustment is a forward line item |
| **MISO** | *No published DC decomposition located* in the MISO load forecast at this writing | — | **all paths ship 0** (see §2.2) | n/a until a source is read |
| **NEISO** | ISO-NE CELT forecast — *no clean published DC decomposition located* | — | **all paths ship 0** (see §2.2) | n/a until a source is read |

### 2.2 The "no source ⇒ ship 0" rule (rule 5 / rule 13, non-negotiable)

Where an ISO publishes no clean data-center decomposition (**MISO, NEISO** today), **every path
ships 0 MW** — we do **not** invent a trajectory, and we do **not** leave a `needs-citation`
placeholder that could later be filled with a fitted number. This is the capacity plan's explicit
instruction ("a path with no source ships as 0"). A DC path of 0 there is honest: it says "the
model carries no separately-parameterized DC block for this ISO," and the near-term
`DEMAND_GROWTH_RATES` (which still embed the boom for those ISOs pre-decomposition) continue to
carry it implicitly until a source lands. Adding MISO/NEISO later is a pure data-intake task
(add the anchors + citation, flip nothing else).

### 2.3 The load factor (the one physical constant)

`datacenter_load_factor = 0.85` — flat hourly capacity factor of the block.

- **LBNL 2024 *United States Data Center Energy Usage Report*** (Shehabi et al., LBNL, Dec 2024):
  documents large-DC utilization; the report's 2024 estimate is **192 TWh (4.7 % of US
  electricity)** rising toward **464 TWh by 2028 (reference case)** — a near-flat-load profile is
  the report's operating assumption for hyperscale facilities.
- **EPRI 2024 *Powering Intelligence*** white paper: data-center annual load factor range
  **0.8–0.95** by facility type; 0.85 is a defensible central value for a mixed AI/cloud fleet.

0.85 is a **cited physical parameter, frozen** (rule 23 analogue): it moves only when LBNL/EPRI
update, never against a residual. It is exposed as a `ScenarioConfig` field so a scenario can
stress it (e.g. 0.95 for an all-hyperscale-AI world), but its default is source-anchored.

---

## 3. Representation design

### 3.1 Hourly shape — flat, with a documented cooling-weighted successor

**Decision: ship the flat block.** The block adds a constant
`dc_mw × datacenter_load_factor` MW to every hour of every simulated zone (allocated by §3.3).
Rationale:

- It is the **structurally correct first-order fix** (rule 1): the dominant error today is that DC
  load is grown with the system's peaky shape; a flat block removes exactly that error. LBNL/EPRI
  both characterize hyperscale DC as near-flat, so flat is the *faithful* shape, not a
  simplification of convenience.
- It is honest about what we know: published DC forecasts give **MW/energy trajectories**, not
  8760 profiles. Inventing an hourly DC shape beyond "flat at load factor 0.85" would be
  unsourced (rule 5).

**Cooling-weighted variant — documented successor, NOT shipped now.** Real DC load has a mild
weather dependence (chiller/cooling load rises with ambient temperature), so the true profile is
"flat + a small cooling ripple correlated with the weather year." Design note for a later wave:
a `datacenter_shape: str = "flat" | "cooling_weighted"` field selecting a normalized
temperature-response profile (block MW modulated ±~5–10 % by the weather-year temperature series
already loaded for the ISO), keeping annual energy fixed. **Deferred** because (a) it is a
second-order correction to a load type whose *defining* trait is flatness, and (b) it needs a
sourced cooling-fraction/temperature-sensitivity per ISO we do not yet have. Flat is the default
either way; this is the block's documented remaining limitation until a source lands.

### 3.2 `ScenarioConfig` fields (rule 24 — all echo to `run_config.json`)

```python
# --- Data-center load block (CX-4). Forecast-mode-only; "off" = today, byte-identical. ---
datacenter_load_path: str = "off"        # "off" | "low" | "mid" | "high"
                                         # Deterministic scenario-matrix axis (PB-1 §1.1).
                                         # Selects the per-ISO cumulative-MW trajectory from
                                         # constants.DATACENTER_ADDITIONS_MW. "off" leaves demand
                                         # byte-identical to today.
datacenter_percentile: float = 0.5       # Continuous PB-2 sampler lever (0.0=low,0.5=mid,1.0=high),
                                         # mirroring demand_growth_percentile / tech_cost_percentile.
                                         # Neutral 0.5 ⇒ the path selection governs; only takes
                                         # effect when the sampler moves it off 0.5.
datacenter_load_factor: float = 0.85     # Flat hourly CF of the block. LBNL 2024 US Data Center
                                         # Energy Usage Report; EPRI 2024 Powering Intelligence
                                         # load-factor range 0.8-0.95. Frozen physical input.
```

**Naming reconciliation (resolves the PB-plan divergence — important).** The PB plan names the
lever `datacenter_load_gw` (a raw per-ISO GW quantity with a triangular marginal). This memo
**supersedes that name** with the **`path` + `percentile` pair**, for three reasons:

1. It is the **exact pattern already in the codebase** for the two sibling load/cost axes —
   `demand_growth_path`/`demand_growth_percentile` and `tech_cost_path`/`tech_cost_percentile` —
   resolved through the existing `_effective_percentile` + `_interpolate_low_mid_high` helpers
   (`scenarios.py:3625-3659`). Reusing it means **zero new resolver machinery** and one obvious
   place for the sampler to reach.
2. A single scalar GW hides the per-ISO structure. The trajectory is a **{year: cumulative MW}**
   curve per ISO (different anchor years, different shapes), which a `path` key selecting a table
   entry represents naturally and a scalar cannot.
3. It keeps the deterministic matrix (PB-1 §1) and the continuous sampler (PB-2 §2.1) on **one
   set of fields** — the whole point of the `path`+`percentile` convention (matrix sets the path,
   sampler sets the percentile, both default to mid).

The PB triangular `(min = signed-agreement queue, mode = ISO forecast, max = total active queue)`
maps **directly** onto the low/mid/high anchors of `DATACENTER_ADDITIONS_MW` (§2.1 "Path anchors"
column): low = signed-IA subset, mid = ISO forecast/planning case, high = total credible queue.
The sampler then draws `datacenter_percentile` and `_interpolate_low_mid_high` reproduces the
triangular's support. (A pure triangular vs the piecewise-linear percentile differ only in the
*density* between anchors, not the support; if the PB lane wants the exact triangular density it
samples `datacenter_percentile` from a Beta/triangular-shaped marginal rather than uniform — a
sampler-side choice, no change here.) **Action for the PB lane:** update PB plan §1.1/§2.1 to cite
`datacenter_load_path`/`datacenter_percentile`; retire the `datacenter_load_gw` name.

### 3.3 `constants.py` tables

```python
DATACENTER_ADDITIONS_MW: dict[str, dict[str, dict[int, float]]]
# {iso: {path: {year: cumulative_MW}}}. Piecewise-linear between anchor years, flat after the
# last anchor. Anchors read from the §2.1 published tables (NOT invented). Every ISO/path with
# no published source ships {} (⇒ 0 MW every year). Each ISO block carries an inline citation
# to its exact source table + retrieval date; parameters.json tier-2, modeled flag OFF.

DATACENTER_ZONE_SHARE: dict[str, dict[str, float]]
# {iso: {zone: share}}, shares sum to 1.0 per ISO. Default = the ISO's zonal load_share
# (iso_configs.py Zone.load_share). Override ONLY where siting is published:
#   ERCOT — skew to North (Oncor) + West per the LFL queue geography in the ERCOT
#           Large Load Integration reports.
#   PJM   — skew to Dominion (DOM) zone per the PJM 2025 LTLF zonal DC decomposition.
# Physical siting data (published queue geography), not a tunable.
```

**Anchor extraction is an implementation step, not this memo.** This memo deliberately does **not**
hard-code per-year MW anchors — doing so from secondary reporting would risk unsourced numbers
(rule 5). The implementer reads the exact anchor MW from the §2.1 primary tables (e.g. ERCOT LFL
officer update MW-by-year; PJM LTLF Table of DC component by zone; CEC 24-IEPR DC forecast +1.8 GW
2030 / +4.9 GW 2040; NYISO Gold Book large-load adjustment) and records each with a citation
comment. The headline figures in §2.1 are the sanity envelope those anchors must sit inside.

### 3.4 Mechanics (`runner.py`, after `_scale_demand`)

Insertion point is **`runner.py:648`** — immediately after `year_demand = _scale_demand(...)` and
**before** `peak_demand = float(year_demand.sum(axis=0).max())` (line 649), so peak, energy, and
every capacity mechanism downstream pick the block up automatically:

```python
year_demand = _scale_demand(base_demand, config, year)
year_demand = _add_datacenter_block(year_demand, config, iso, year, zone_names)  # NEW, no-op when "off"
peak_demand = float(year_demand.sum(axis=0).max())
```

with (new helper, `runner.py`, vectorized — rule 2, no hour loop):

```python
dc_mw = resolve_datacenter_mw(config, iso, year)          # interp on DATACENTER_ADDITIONS_MW at
                                                          # the effective percentile (mirrors
                                                          # resolve_demand_growth_rate). 0.0 when
                                                          # path=="off" or no ISO/path entry.
block_mw = dc_mw * config.datacenter_load_factor          # flat energy-basis MW
shares = np.array([DATACENTER_ZONE_SHARE[iso].get(z, ...) for z in zone_names])  # (n_zones,)
year_demand = year_demand + (block_mw * shares)[:, None]  # broadcast add over all T hours
```

`resolve_datacenter_mw` lives in `scenarios.py` beside `resolve_demand_growth_rate`, reusing
`_effective_percentile(config.datacenter_load_path, config.datacenter_percentile)` and
`_interpolate_low_mid_high` on the low/mid/high `{year: MW}` curves (linearly interpolated in
*year* first, then across paths by percentile). `"off"` short-circuits to 0.0.

**Foresight-component-1 interaction (already landed).** The entering-year known-peak substitution
(`runner.py:640-649`, capacity plan §2.3.1) computes `peak_demand` from the *current* year's
`year_demand`. Because the DC block is added **before** line 649, the known peak the retirement
floor and reserve-margin backstop consume **already includes the DC block** — no extra wiring. The
lookahead re-price helper (`_lookahead_reprice_signal`, `runner.py:299+`, default-off) calls
`_scale_demand` on `next_year` at line 324; the implementer threads the same `_add_datacenter_block`
there so the lookahead's net-load also sees the block (one-line change, same helper).

### 3.5 Decomposition discipline — the critical co-change (double-count guard)

`DEMAND_GROWTH_RATES` near-term rates **currently include** the DC boom (`constants.py:709`
comment). Landing the block **without** re-deriving organic growth double-counts DC. Therefore,
**in the same change** (rule 1 — right structure, not a residual patch), the implementer must
re-derive the near-term `DEMAND_GROWTH_RATES` entries as **organic-ex-DC** rates under a
**2030 energy-continuity constraint**, per ISO:

```
organic_ex_DC_rate  such that  (organic energy @2030)  +  (mid DC block energy @2030)
                               ≈  (current mid total energy @2030)
```

i.e. the mid-path total 2030 energy is held **invariant** across the refactor (the block just
*relocates* the DC portion from the scalar into the explicit flat block, correcting its shape).
Sources for the ex-DC split: EIA STEO ex-data-center electricity growth, and the same ISO forecast
documents' organic vs DC decomposition (PJM LTLF publishes both; ERCOT LTLF separates LFL). Each
ISO's decomposition is documented in the `constants.py` comment and `parameter-citations.md`. Only
the **near** era is re-derived (the transition year is 2030, `DEMAND_GROWTH_TRANSITION_YEAR`); the
long era is unaffected (DC pipeline matures ≈ 2030). MISO/NEISO, which ship a 0 DC block, keep
their current rates unchanged (no double-count to remove).

**This is the one place CX-4 must touch a shared constant that the capacity lane also reads.** See
§7 for the sequencing that avoids the collision.

---

## 4. Electrification shape adder — design sketch (default off, W2-P3-optional)

Per the capacity plan §4.3, this is **plumbing-only-if-cheap**, else a documented limitation. Design:

```python
electrification_shape_path: str = "off"   # "off" | "reference" | "high"
```

selects a per-ISO **additive normalized hourly profile** (winter-morning + evening heat-pump ridge
+ EV evening charging peak, normalized to 1 TWh/yr) scaled by an annual TWh trajectory
`ELECTRIFICATION_TWH[iso][path][year]`. Sources: **NREL Electrification Futures Study**
reference/high cases; ISO heating-electrification studies where published (e.g. ISO-NE, NYISO).
Applied **additively** to `year_demand`, identically to the DC block (add, don't scale). Unlike the
DC block it is **not flat** — it reshapes hours, which is precisely the capability a scalar lacks.

**Recommendation: ship only the config field + profile-loader *interface* (a stub that returns a
zero profile for "off") in the implementation wave; defer the sourced profiles.** The DC block is
the material, near-term, certain input error (flat, huge, in-queue); electrification is smaller and
later-horizon. If the loader interface is not trivially cheap, skip it and carry the audit's PP-3.3
"end-use reshaping remains a documented limitation" note forward. Either way, **the DC block does
not depend on it.**

---

## 5. Interaction with capacity evolution and the PB-2 sampler

### 5.1 Capacity evolution (the entry/retirement screens see the load)

- **Entry screens** (`apply_economic_new_entry`) see the higher net load through the price signal
  and the peak; a real DC-driven load ramp **pulls economic entry forward** — the intended effect.
- **Retirement floor & reserve-margin backstop** consume `peak_demand`, which now includes the DC
  block (§3.4). Whether **retirement responds correctly** depends on the **floor-fidelity rebuild
  the capacity lane is building** (capacity plan §3.2, accredited-basis floor). Under the *old*
  raw-nameplate floor, more peak just retains more nameplate indiscriminately. Under the *new*
  accredited floor with the CO₂ tie-break, a DC-driven requirement increase is met by the cheapest
  firm adequacy first — the economically meaningful response. **CX-4 is therefore correctly
  sequenced *after / alongside* the floor rebuild**: the DC block's capacity-side effect is only
  faithful once the floor it feeds is accredited. This memo does not re-open the floor design; it
  flags the dependency.
- **Emissions direction (capacity plan §4.4, restated):** at *equal total annual energy* (the
  honest post-decomposition comparison) the flat block shifts growth from peak into all hours →
  more overnight mid-merit gas_cc (and surviving coal) → **CO₂ up slightly per TWh**, price shape
  flattens, scarcity-driven CT/storage entry signal weakens. Versus a naive "DC via higher uniform
  scalar," the flat block gives **lower peak** → less peaker over-build and less phantom scarcity
  rent. The high-DC path grows total energy → **CO₂ up in absolute terms** until entry catches up
  — the direct interaction with the foresight item (both land in one tornado refresh).

### 5.2 PB-2 uncertainty sampler (the datacenter axis distribution)

- The block **is** the "DC axis" PB-1 §1.1 and PB-2 §2.1 anticipated. With the fields in §3.2:
  - **PB-1 deterministic matrix:** the `LOAD-HI`/`CORNER-HI-EMIT` cases set
    `datacenter_load_path="high"` (or a dedicated `DC-HI` side case); `REF` uses `"mid"`. This
    replaces the PB plan's stopgap ("until PP-3.3 lands, LOAD-HI is the documented proxy") with a
    real independent axis.
  - **PB-2 continuous sampler:** the DC dimension samples `datacenter_percentile` on
    `[0, 1]`. The PB plan's **triangular(min=signed queue, mode=forecast, max=total queue)** marginal
    is realized by drawing the percentile from a triangular-shaped marginal (mode at 0.5) and letting
    `_interpolate_low_mid_high` map it onto the low/mid/high MW anchors (§3.2 reconciliation). The
    low/high anchors are the queue support bounds (assumption analogous to the load-growth A-3
    "published low/high are range bounds, not tail quantiles").
  - **Correlation.** In the Gaussian-copula sampler, the DC axis should carry a **positive
    correlation with the load-growth axis** (both are demand-side; a high-DC world is more likely a
    high-organic-growth world) — a disclosed judgment input in the sampler's correlation matrix,
    not hardcoded here. Flagged for the PB lane to set with a cited/So-stated value.
- **Decomposition consistency for the sampler.** Because organic growth was re-derived ex-DC
  (§3.5), the load-growth axis and the DC axis are now **separable** — the sampler can move them
  independently without the double-count that fusing them would cause. This separability is the
  concrete deliverable CX-4 hands the PB program.

---

## 6. Validation — hindcast / holdout-safe check of the load block

The block is **forecast-mode-only**; a backcast pins measured load, so the block is `"off"` in every
scored keeper and there is **no dispatch-solve validation** of it. What we *can* and *should* do is
validate the **block construction** against large-load actuals — a no-LP, holdout-safe check.

**Holdout discipline (rule 22, strict).** Use **2023–2025 large-load actuals ONLY.** **No contact
with 2022 or H1-2026** — no solve, no scoring, no data intake — consistent with the holdout memo.
The validation is **no-LP** (loader/arithmetic checks), so it does not even approach the
solve-quarantine line.

### 6.1 Construction checks (unit / analytic — CLAUDE.md testing pattern, trivial-first)

1. **Off-path identity.** `datacenter_load_path="off"` ⇒ `year_demand` byte-identical to today
   (hash the array before/after the new call). This is the single most important test — it proves
   zero blast radius on every existing forecast/backcast.
2. **Additivity.** On-path adds *exactly* `dc_mw × load_factor × zone_share` to **every hour of
   every zone**; energy and peak deltas match the closed-form (`ΔEnergy = block_mw × 8760`,
   `Δpeak = block_mw` since the block is flat). Analytic — no solve.
3. **Zone shares sum to 1.0** per ISO; default equals `iso_configs` `load_share`; overrides
   documented and summing to 1.
4. **Interpolation.** `resolve_datacenter_mw` reproduces hand-computed piecewise-linear values at
   anchor and between-anchor years, and at percentile 0/0.5/1 reproduces low/mid/high.
5. **Backcast guard.** A config validator **raises** on `mode="backcast"` with a non-`"off"` DC
   path (the block must never enter a scored backcast).

### 6.2 Historical plausibility check (no-LP, holdout-safe, 2023–2025 only)

Confront the *mid trajectory anchors* against **2023–2025 realized large-load additions** where an
ISO published them (ERCOT reports large-load energization; PJM/NYISO report interconnected large
loads). This is a **sanity confrontation of the input path**, not a model score:

- Check the mid anchors for 2023/2024/2025 sit within the observed realized-plus-signed band (the
  block should not over- or under-shoot what actually energized in the in-sample years).
- Report the check in the implementation's DC-block section; **it never tunes the anchors** (rule
  23 — anchors come from the forecast tables, the historical check only flags a gross mismatch that
  would indicate a source-reading error). A mismatch is a *bug to investigate in the source
  reading*, not a knob to turn (rule 14 logic).

There is deliberately **no forecast-accuracy claim** here: the block is a forward input, and its
skill is only measurable once the capacity hindcast (PP-0.3 / W2-P5) exists and the 2026+ actuals
mature — both out of scope and holdout-protected.

---

## 7. Staged implementation plan + file ownership (collision-free with the capacity lane)

**The ownership problem.** The capacity lane holds `capacity.py`. CX-4 must not touch `capacity.py`
— and it doesn't need to (§0: the block is demand, screens read it for free). The **only** shared
files are `constants.py` (DC tables + `DEMAND_GROWTH_RATES` re-derivation) and `scenarios.py`
(`ScenarioConfig` fields + resolver). Sequencing below keeps CX-4 in `runner.py`/`scenarios.py`/
`constants.py` and out of `capacity.py`, with the one genuinely-shared edit (`DEMAND_GROWTH_RATES`)
isolated to a single small stage the two lanes coordinate on.

| Stage | Files (owner: **demand lane** unless noted) | Depends on |
|---|---|---|
| **CX4-0** Config surface | `scenarios.py` (3 fields §3.2 + `resolve_datacenter_mw` beside `resolve_demand_growth_rate`), reusing existing `_effective_percentile`/`_interpolate_low_mid_high` | none — additive, defaults make it a no-op |
| **CX4-1** Constants tables | `constants.py` (`DATACENTER_ADDITIONS_MW`, `DATACENTER_ZONE_SHARE`, anchors read from §2.1 sources with citations; MISO/NEISO ship `{}`) | CX4-0 |
| **CX4-2** Runner assembly | `runner.py` (`_add_datacenter_block` helper + call at line 648; thread into `_lookahead_reprice_signal`) | CX4-0/1 |
| **CX4-3** Decomposition co-change (**coordinate with capacity lane**) | `constants.py` `DEMAND_GROWTH_RATES` near-era re-derivation (§3.5) + `parameter-citations.md` | CX4-1/2; **must land as one commit**, and the capacity lane must be told the near rates changed (they read them via `resolve_demand_growth_rate`) |
| **CX4-4** Backcast validator + tests | `scenarios.py` validator; `test_runner.py`/`test_scenarios.py` (§6.1) | CX4-2 |
| **CX4-5** (optional) Electrification interface | `scenarios.py` field + profile-loader stub only if trivially cheap; else doc note | independent |
| **CX4-6** PB-axis wiring (**hand to PB lane**) | PB plan §1.1/§2.1 name update; sampler DC marginal + correlation entry | CX4-0..4 |

**Collision-avoidance specifics:**

- **`capacity.py` untouched** — the demand lane never opens it. The capacity lane's floor rebuild
  and CX-4's demand block compose through `peak_demand`/`year_demand` with **no shared code**.
- **`constants.py` / `scenarios.py` are appended, not restructured** — CX-4 adds new tables/fields
  at the end of the relevant sections; the only *edit* to an existing constant is
  `DEMAND_GROWTH_RATES` in CX4-3, which is a small, well-bounded, coordinated change. If the two
  lanes are active simultaneously, CX4-3 rebases onto the capacity lane's `constants.py` state (or
  vice-versa) — a trivial merge because they touch different dicts.
- **Landing order vs the capacity lane:** CX-4's *capacity-side faithfulness* depends on the
  accredited floor (§5.1), so CX-4 should **merge after or concurrently with** the floor rebuild,
  but its code has **no build dependency** on it — CX4-0..4 can be written and tested against
  today's floor (the tests are demand-arithmetic, floor-agnostic). Recommend: land CX4-0..2 early
  (pure additive, no-op by default), hold CX4-3 (the shared re-derivation) until the capacity lane
  signals `constants.py` is quiet, then land CX4-3/4 together.

---

## 8. Test plan (implementation acceptance — restates §6.1 as the checklist)

Trivial-first (1-gen/1-zone/24 h scaled up):

1. **Off-path byte-identity** of `year_demand` (hash) — every existing run unchanged.
2. **On-path additivity** analytic: `+dc_mw × LF × share` every hour/zone; energy/peak deltas
   closed-form.
3. **Zone shares** sum to 1.0; default = `load_share`; overrides documented.
4. **`resolve_datacenter_mw`** interpolation (year + percentile) vs hand-computed; `"off"` ⇒ 0.
5. **Backcast + non-off path ⇒ validator raises.**
6. **Decomposition continuity:** mid-path total 2030 energy invariant across the CX4-3 refactor
   (organic-ex-DC + mid block ≈ prior mid total), per ISO.
7. **`parameters.json`** entries for `datacenter_load_factor` + the trajectory sources present and
   cited (CI `validate_parameters.py` green); tier 2, `modeled` off.
8. Existing `test_runner.py` / `test_scenarios.py` green throughout.

---

## 9. DOF ledger / parameter table (rule 21 — identification sources, none from a residual)

| Parameter | Default | Identification source (NOT a residual) | Frozen? |
|---|---|---|---|
| `datacenter_load_path` | `"off"` | scenario selector (structural) | n/a (axis) |
| `datacenter_percentile` | `0.5` | PB-2 sampler lever; neutral = no effect | n/a (axis) |
| `datacenter_load_factor` | `0.85` | LBNL 2024 US DC Energy Usage Report; EPRI 2024 Powering Intelligence (0.8–0.95) | ✅ moves only on source update |
| `DATACENTER_ADDITIONS_MW[iso][path]` | per §2.1 | ERCOT LTLF/LFL queue; PJM 2025 LTLF DC component; CEC 24-IEPR DC forecast; NYISO 2025 Gold Book large-load; MISO/NEISO = `{}` (no source) | ✅ re-read on new forecast vintage |
| `DATACENTER_ZONE_SHARE[iso][zone]` | `load_share` (default) / published siting | ERCOT LFL queue geography; PJM LTLF zonal DC split; else zonal load_share | ✅ physical siting data |
| `DEMAND_GROWTH_RATES` near (re-derived) | organic-ex-DC | EIA STEO ex-DC growth; ISO forecast organic/DC decomposition; 2030 energy-continuity | ✅ source-derived |
| `electrification_shape_path` (sketch) | `"off"` | NREL Electrification Futures Study ref/high (when sourced) | n/a (axis) |

**Ablation twin (rule 21):** the `datacenter_load_path="off"` run **is** the zero-forcing ablation
of the block — the acceptance run reports emissions/price with the block on vs off, so the block's
effect is always measured, never assumed.

---

## 10. Open questions / documented limitations

1. **MISO / NEISO ship 0** until a published DC decomposition is read — a data-intake follow-up,
   not a modeling gap to paper over (§2.2).
2. **Cooling-weighted hourly shape** deferred; flat is the sourced default. Documented successor in
   §3.1 (needs a per-ISO cooling-sensitivity source).
3. **Electrification profiles** deferred (interface-only recommendation, §4); PP-3.3 "end-use
   reshaping remains a documented limitation" carries forward until sourced.
4. **Forecast-skill validation** of the block awaits the capacity hindcast (PP-0.3/W2-P5) and
   matured 2026+ actuals — both holdout-protected and out of scope (§6).
5. **PB correlation** between the DC axis and the load-growth axis is a disclosed sampler judgment
   input for the PB lane to set with a stated value (§5.2).
6. **Anchor MW values** are extracted at implementation from the §2.1 primary tables with per-ISO
   citations — this memo fixes the *sources and structure*, not the literal MW (rule 5: no
   secondary-source numbers hard-coded).

---

## Primary sources cited

- **LBNL** — Shehabi et al., *2024 United States Data Center Energy Usage Report*, Lawrence Berkeley
  National Laboratory, Dec 2024 (192 TWh / 4.7 % 2024; 464 TWh 2028 reference).
  https://eta.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report
- **EPRI** — *Powering Intelligence: Analyzing Artificial Intelligence and Data Center Energy
  Consumption*, EPRI, 2024 (load-factor 0.8–0.95; up to 9 % US generation by 2030).
  https://www.epri.com / powering-intelligence.epri.com
- **ERCOT** — *2025 Report on Existing and Potential Electric System Constraints and Needs* (Dec
  2025); ERCOT Large Load Integration / large-flexible-load officer updates (queue ≈ 226 GW Nov
  2025 vs 63 GW end-2024; ≈ 138 GW 2030 adjusted peak).
  https://www.ercot.com/services/rq/large-load-integration
- **PJM** — *2025 Long-Term Load Forecast Report* (data-center component; ≈ 30 GW DC peak growth
  2025–2030; +70 GW / 220 GW 15-yr summer peak).
  https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2025-load-report.pdf
- **CEC / CAISO** — *2024 IEPR Data Center Forecast* (24-IEPR-03), California Energy Demand
  2024-2040 (+1.8 GW DC by 2030, +4.9 GW by 2040; peak 48.3→~68 GW).
  https://www.energy.ca.gov/sites/default/files/2025-03/Data_Center_Forecast_Final_ada.pdf
- **NYISO** — *2025 Load & Capacity Data Report ("Gold Book")* (19 large-load projects > 3 GW;
  > 10 GW by 2031; avg ≈ 300 MW).
  https://www.nyiso.com/documents/20142/2226333/2025-Gold-Book-Public.pdf
- **EIA** — *Short-Term Energy Outlook* (ex-data-center electricity growth, for the §3.5
  decomposition); *Annual Energy Outlook 2025* (electrification context).
  https://www.eia.gov/outlooks/steo/ , https://www.eia.gov/outlooks/aeo/
- **NREL** — *Electrification Futures Study* reference/high cases (electrification adder sketch, §4).
  https://www.nrel.gov/analysis/electrification-futures.html

---

*Produced 2026-07-06 (G-34, design only, Opus). Code anchors verified against `origin/main` at the
branch point. Supersedes the PB plan's `datacenter_load_gw` lever name with
`datacenter_load_path`/`datacenter_percentile` (§3.2). Implementation belongs to the
capacity-economics + demand lanes per the §7 staging; no `src/` changes in this deliverable.*
