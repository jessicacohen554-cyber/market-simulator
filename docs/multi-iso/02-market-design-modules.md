# Market-Design Modules & LP Modularity Assessment

Status: **planning** (catalogue), with the first module now landed in code.
This catalogues the market-design features that must become toggleable modules
so each ISO runs with *exactly* the mechanisms it actually has, and assesses
how modular the dispatch LP already is for that.

> **Landed:** a per-ISO `MARKET_DESIGN` registry (`config/constants.py`,
> `MarketDesign(capacity_market=...)`, `DEFAULT_MARKET_DESIGN` = energy-only)
> is the first concrete realization of this catalogue. Its initial consumer is
> the **storage new-entry capacity value** (methodology spec §5.5): ERCOT
> energy-only pays no capacity stream, while PJM/NYISO/ISO-NE/CAISO pay
> `net_cone × ELCC(duration) × saturation derate`. ISOs absent from the
> registry fall back to energy-only, preserving the defaults-off principle.
> Future capacity/RA modules (M1 below) should read this same registry.

Guiding principle (from `claude.md`): every module **defaults to off** so
ERCOT's calibrated, energy-only behaviour is untouched unless its modules are
explicitly selected. An ISO's profile (Section 3) is just the set of modules
it turns on.

---

## 1. LP modularity assessment — what's already modular vs. what needs structure

### Already modular (no LP structural change needed)
- **Topology.** `n_zones`, `n_storage`, `n_links`, the node-link `incidence`
  matrix and per-link `ttc` are all parameters of `VariableLayout` /
  `build_constraints` / `build_variable_bounds`. Any zone/link count works.
- **VOLL.** Per-ISO scalar already on `ISOConfig.voll`, threaded into the
  objective. (CAISO 2000, ERCOT 5000, etc. already differ.)
- **Cost adders.** Carbon/NOx/SO2 prices and EAC credits enter via marginal-
  cost assembly (`assemble_mc`) and the cost vector — pure objective changes.
- **Annual RPS.** One constraint row + dual = REC price, already wired
  (`_build_rps_row`, `policy/rps.py`, `STATE_RPS_FLOORS`).
- **Emerging tech / new fuels as generators or storage.** Per the methodology
  spec §1.5, a new technology is a data/parameter extension: a `Generator`
  (thermal block) or `StorageUnit` reusing existing variable classes. Oil,
  biomass, gas_st all fit the thermal-block mould (see doc 03 Pack F).

### Needs structural extension (new variable blocks or constraint families)
- **Operating reserves / ancillary services.** No reserve variables exist.
  Co-optimized energy+reserves requires new per-zone (or per-ISO) variable
  blocks (Reg-Up/Dn, Spin, Non-Spin) in `VariableLayout`, reserve-procurement
  constraints, and a headroom coupling (`P[g,t] + Reserve[g,t] ≤ pmax`). This
  is the single largest LP change. **Recommended approach:** add an optional
  reserve block guarded by a layout flag, kept zero-width when off, so the
  existing column math is unchanged for ERCOT-style runs.
- **Hydro energy budgets.** Hydro is fuel code 6 but dispatches as a flat
  thermal block with no inter-temporal energy limit. A faithful hydro needs a
  budget constraint (Σ_t P_hydro[g,t] ≤ monthly_energy[g,month]) plus min/max
  MW — a new constraint family keyed to a generator subset. Smaller change
  than reserves; reuses the per-generator P variables.
- **Capacity / resource-adequacy revenue.** *Not* an LP change — it lives in
  `capacity.py`'s retirement/entry economics (Section 2 below).

### Where per-ISO config must grow
`ISOConfig` today holds only `zones`, `links`, `voll`. To carry module
settings it should gain optional fields (all defaulting to off/None):
`reserve_requirements`, `capacity_mechanism`, `hydro_budget_source`,
`carbon_program` (RGGI / CA-CAT default price), `import_nodes`,
`rps_scheme`. `ScenarioConfig` already carries the scenario-level knobs
(EAC prices, rps_enabled, carbon_price); module *enable* flags should be
derivable from `ISOConfig` so a backcast of an ISO automatically uses that
ISO's real mechanisms.

---

## 2. The capacity-market gap (most important fidelity item after topology)

`capacity.py::apply_economic_retirements` computes:

```
net_revenue        = Σ_t price[zone,t]·dispatch[g,t] + attribute (EAC) revenue
going_forward_cost = fixed_om_per_kw_yr · fom_multiplier
retire if net_revenue < going_forward_cost for N consecutive years
```

This is **correct for energy-only ERCOT** but wrong for the five capacity-
market ISOs: in PJM/NYISO/ISO-NE/MISO a thermal unit earns a **capacity
payment** that can keep it solvent even with negative energy margin. Omitting
it makes the model **over-retire** thermal capacity in those ISOs and
under-state reserve margins.

The module ("Capacity/RA revenue") adds a `capacity_revenue` term to
`net_revenue` (and to `estimate_expected_revenue` for new entry). It is an
**accounting layer in `capacity.py`, not an LP change**, and is exogenous —
a per-ISO capacity price ($/MW-day or $/kW-yr) times the unit's qualifying
(derated/UCAP) capacity. This mirrors how EAC revenue is already added.

> **Landed (2026-06-04).** `capacity.capacity_revenue_per_mw_yr(iso, eford)`
> implements M1 as a first cut: `net_cone_per_kw_yr × 1000 × (1 − EFORd)`
> (UCAP proxy), gated on `MARKET_DESIGN[iso].capacity_market`, added to both
> the retirement `net_revenue` and the new-entry thermal revenue. The price
> anchor is the per-ISO net-CONE already in the registry (PJM ~$100/kW-yr);
> BRA/auction clearing prices can refine it later. Energy-only ERCOT earns
> zero (registry flag off), so its retirement/entry economics are unchanged.

| ISO | RA mechanism | Construct | Capacity-price source |
|-----|--------------|-----------|-----------------------|
| ERCOT | none (energy-only + ORDC) | — | n/a (module **off**) |
| PJM | RPM (Reliability Pricing Model) | annual, locational (LDAs) | BRA clearing $/MW-day |
| NYISO | ICAP | seasonal, locational | spot/strip $/kW-mo |
| ISO-NE | FCM (Forward Capacity Market) | annual | FCA clearing $/kW-mo |
| MISO | PRA (Planning Resource Auction) | **seasonal** (4 seasons) | PRA clearing $/MW-day |
| SPP | RA requirement (no central market) | obligation, bilateral | admin/CONE proxy |
| CAISO | RA program (bilateral + CPM) | monthly/annual | admin/CONE proxy |

---

## 3. Per-ISO market-design profile (which modules turn on)

Legend: ● on (modeled) · ◐ simplified/exogenous · ○ off (mechanism absent)

| Module | ERCOT | CAISO | PJM | NYISO | ISO-NE | MISO | SPP |
|--------|:-----:|:-----:|:---:|:-----:|:------:|:----:|:---:|
| Energy-only LP (base) | ● | ● | ● | ● | ● | ● | ● |
| Zonal transmission (TTC) | ● | ◐ | ● | ◐→● | ◐→● | ● | ● |
| Capacity/RA revenue | ○ | ◐ | ● | ● | ● | ● | ◐ |
| Operating reserves | ◐ (ORDC) | ◐ | ◐ | ◐ | ◐ | ◐ | ◐ |
| Scarcity / VOLL | ● ($5000) | ● ($2000) | ● ($2000) | ● ($2000) | ● ($2000) | ● | ● |
| Hydro energy budget | ○ (small) | ● | ◐ | ● | ◐ | ◐ | ◐ |
| Pumped storage | ○ | ● | ● | ● | ● | ◐ | ○ |
| State/zonal RPS-CES | ◐ | ● (60% RPS) | ● (13-state) | ● (CES 70%) | ● | ◐ | ◐ |
| Carbon program | ○ | ● (CA-CAT) | ◐ (RGGI partial) | ● (RGGI) | ● (RGGI) | ○ | ○ |
| Import/export nodes | ○ | ● (WECC) | ● | ● (HQ/PJM/NE/IESO) | ● (HQ/NYISO) | ● | ● |
| Oil / dual-fuel units | ○ | ○ | ◐ | ● | ● | ◐ | ○ |
| Biomass/MSW/refuse | ○ | ◐ | ● | ● | ● | ● | ◐ |

Reading the table top-down for an ISO gives its build scope. Notable points:
- **NYISO & ISO-NE** are the richest: hydro budgets, oil/dual-fuel, RGGI
  carbon, capacity markets, big imports (Hydro-Québec). Highest fidelity cost.
- **CAISO** needs hydro (seasonal), CA cap-and-trade, 60% RPS, WECC imports —
  much of the import scaffolding already exists.
- **PJM** is the big zonal + RPM + multi-state-RPS build.
- **MISO** adds the seasonal capacity construct and the MISO-South transfer
  constraint; large coal+wind fleet.
- **SPP** is energy + RA-obligation (no central capacity market) + heavy wind;
  closest to ERCOT in market design, simplest market-design layer.

---

## 4. Module catalogue (build units)

Each row is a self-contained module with a prompt pack in doc 03.

| ID | Module | LP impact | Lives in | Toggle | Default |
|----|--------|-----------|----------|--------|---------|
| M1 | Capacity/RA revenue accounting | none (economics) | `capacity.py` | `ISOConfig.capacity_mechanism` | off |
| M2 | Operating-reserve co-optimization | **new var block + rows** | `dispatch.py`, new `model/reserves.py` | layout flag | off |
| M3 | Hydro energy budget | new constraint family | `dispatch.py`, `data/hydro.py` | `ISOConfig.hydro_budget_source` | off |
| M4 | Import/export nodes & interchange | uses existing flow vars + priced offers | `iso_configs.py`, `dispatch.py` | `ISOConfig.import_nodes` | off |
| M5 | State/zonal RPS & CES | extra constraint rows (per scheme) | `policy/constraints.py`, `policy/rps.py` | `ISOConfig.rps_scheme` | single annual |
| M6 | Carbon program (RGGI / CA-CAT) | cost adder (existing) | `policy/carbon.py`, `iso_configs.py` | `ISOConfig.carbon_program` | none |
| M7 | Scarcity / ORDC adder | objective/price adder | `dispatch.py`, `policy/` | per-ISO | VOLL slack only |
| M8 | Seasonal RA timing (MISO/ISO-NE) | none (accounting calendar) | `capacity.py` | `ISOConfig.capacity_mechanism.season` | annual |

Build order recommendation: **M3 (hydro)** and **M4 (imports)** first — they
unblock CAISO/NYISO realism and reuse existing variable classes; **M1
(capacity revenue)** next — pure economics, unblocks PJM/NYISO/NEISO/MISO
retirement fidelity; **M5/M6** (policy) are low-risk adders; **M2 (reserves)**
last — the only deep LP surgery, and ERCOT can be calibrated without it first.

---

## 5. Faithfulness guardrails

- An ISO must not silently inherit a mechanism it lacks. SPP has no central
  capacity market → M1 runs in ◐ "obligation/CONE-proxy" mode or off, never
  in full RPM mode.
- ERCOT regression: with all module toggles at default-off, ERCOT results
  must be **bit-for-bit unchanged**. Every module PR includes an ERCOT
  no-change test.
- Exogenous vs endogenous: capacity prices, RGGI/CA-CAT prices, and import
  offers are **exogenous inputs with citations** (append to
  `parameter-citations.md`), not solved by the model — consistent with how
  EAC prices already work.
- Reserves (M2) are the only module that changes the LP column count; it must
  preserve the no-Python-loop and struct-of-arrays rules, and keep the reserve
  block zero-width when the ISO/scenario doesn't request reserves.
