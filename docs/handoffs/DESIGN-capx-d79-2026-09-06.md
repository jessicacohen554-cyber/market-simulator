# DESIGN — capx D79: a solve-surface fingerprint in the cache key (phase 0, the design memo)

**Lane:** capx D79 · **Model:** Fable · **Branch:** `claude/capx-d79-cache-fingerprint-fr9e0i` (off
`origin/main` `ccbf802e`, rebased to `d962a90c` before push) · **Date:** 2026-09-06
**Charter:** director ledger r#47 card D79 + prompt pack §D79 — *"inventory the solve-affecting
tables, compare fingerprint / tree-hash / mechanical epoch / hybrid, blast radius, recommend one
as a director card"*. **ZERO LP. NO CODE.** Every number below is computed from committed
artifacts and `origin/main` history; the measurement scripts ran in the session scratchpad and
are not committed (§9 gives the method so each figure re-runs).

---

## 0. Verdict (one paragraph)

**Recommend the hybrid (d), in one specific shape: a per-name, per-ISO-projected VALUE
fingerprint of the registry modules that drops each name at its frozen registration-time hash —
the (b′-1) construction transplanted from `ScenarioConfig` fields to `constants.py` tables — plus
the epoch ledger made mechanical as SCOPED epoch ids that enter the key only for the configs
their prose "INVALIDATED" clause names.** It lands at **zero key moves** (every name is at its
declared hash, every epoch list is empty), so it does not need a re-key event and does not
collide with the D65-B-R batch, whose seven pre-declared keys are **not yet on the board** at
HEAD (§5.4). It would have caught SCN-LOAD automatically and D77 through the entry D77 already
wrote; it would **not** have caught D55, and nothing short of a source-tree hash does — and that
hash fires on **207 of the last 30 days' 225 `src/market_sim` merges, on 28 of 31 days**, even
with docstrings stripped (§4.2). The cost the recommendation carries, measured over the same
window: an ISO's forecast keys move **2–7 times per 30 days** (ERCOT 5, CAISO 3, PJM 2, MISO 5,
NYISO 5, NEISO 7), every one of them a real solve-affecting value change; a naive "hash every
table" fingerprint would instead have moved **every ISO's keys 41 times**, 25 of them for pure
table additions (§4.1). Backcast keys carry the same fingerprint (§4.5).

---

## 1. What the key sees today, restated in one table

`ScenarioConfig.cache_key()` (`scenarios.py:17711`) hashes `asdict(self)` minus registered
fields at their frozen declared default, plus retired fields at their last value, paths folded to
sentinels. Three things it cannot see, and the three incidents map onto them exactly:

| surface | in the key? | incident | how it was found | ledger entry |
|---|---|---|---|---|
| `ScenarioConfig` fields, defaults, flips | **yes** (since D24-R (b′-1)) | — | — | key advances 2026-08-04 / 09-02 / 09-03 / 09-05 / 09-06c |
| `constants.py` / `capacity_market.py` / `fuel_trajectories.py` values | **no** | SCN-LOAD `ad45b0e4`: `DEMAND_GROWTH_RATES` / `DATACENTER_ADDITIONS_MW` / `ELECTRIFICATION_LAYERS` re-derived; every T1-F peak moved | D67, D60-R4, D72-prehunk — each by re-solving | **owed, routed to SCN-DESK, not written** |
| solve-path source | **no** | D55 `_floor_retention_merit` class-constant form; NEISO 2027 exit set 33 → 40 rows | D65 §3c, by re-solving | **none** |
| solve-path source | **no** | D77 `Generator.ccs_capture_fraction` composition; NEISO CO2 −48 % at 2030 | SCN-WS2b, by reading a ledger | 2026-09-06b, "NO KEY MOVES" |

The ledger in `results/cache.py` holds 21 entries (2026-08-02 → 2026-09-06e): 5 key advances,
16 same-key invalidations. Of the three D79 incidents, **one has an entry, one is owed, one was
never recognised as an invalidation by the lane that made it.** That ratio is the measured
recall of the human-read ledger on exactly the class it exists for, and it is what §4.3 prices.

---

## 2. INVENTORY — what the solve path reads (by import graph, not memory)

Method (§9.1): an AST walk of every module under `src/market_sim` plus the four runner scripts,
recording every `from <registry> import NAME` and every `<alias>.NAME` attribute read against
the module-level UPPERCASE definitions of the five config registry modules; each consumer
module is then mapped to a region of the architecture.

### 2.1 Census

| defining module | names | direct solve-affecting | config-transitive | reporting-only | ensemble-only | unread |
|---|---|---|---|---|---|---|
| `config/constants.py` | 145 | 125 | 5 | 1 | 7 | 7 |
| `config/capacity_market.py` | 101 | 64 | 37 | 0 | 0 | 0 |
| `config/fuel_trajectories.py` | 37 | 28 | 9 | 0 | 0 | 0 |
| `config/ercot_envelopes.py` | 17 | 1 | 1 | 15 | 0 | 0 |
| `config/iso_configs.py` | 10 | 2 | 0 | 0 | 0 | 8 |
| **total** | **310** | **220** | **52** | **16** | **7** | **15** |

**Solve-affecting = 272 (220 direct + 52 transitive).** The 52 "config-transitive" names are
read only by other config modules, and every one of them feeds a solve-affecting table:
37 are `capacity_market.py`'s private curve pieces (`_PJM_VRR_CURVE*`, `_NEISO_FCA*`,
`_MISO_RBDC*`, `_NYISO_ICAP_CURVE`, …) composed into the public capacity-demand tables;
9 are the coal-sigmoid scalars behind the delivered-coal construction; and **5 are
`constants.py` names read through `config/scenario_resolvers.py` — `DEMAND_GROWTH_RATES`,
`DEMAND_GROWTH_RATES_VINTAGES`, `DEMAND_GROWTH_TRANSITION_YEAR`, `TECH_COST_MULTIPLIERS`,
`ATB_TECH_WACC_REAL`.** The SCN-LOAD table is in this class: `runner.py:405` resolves it per
year through `resolve_demand_growth_rate(config, year)` and nothing about it is stored on the
config, which is why the incident left every key unmoved. A value fingerprint must therefore
hash the **public composed values**, not the consumer list — a private curve piece that moves
shows up as its public table moving, and a transitive read is indistinguishable from a direct
one at the value level.

**Reporting-only (16)** is entirely the ERCOT RTOLCAP / online-capacity scarcity-overlay
family in `ercot_envelopes.py` plus `ERCOT_LR_RRS_AVAILABILITY_HOD`, all consumed by
`results/scarcity.py` alone. **Ensemble-only (7)** is the `STRUCTURAL_PRIOR_*` /
`STATMODE_PROBE_RUNS` set read by `structural_prior.py`. **Unread (15)**: 7 `constants.py`
names with no consumer anywhere in `src` or the runner scripts (`EAC_PRICE_REFERENCE`,
`MMBTU_PER_BBL_RESIDUAL`, `NYISO_HYDRO_TREATY_MIN_FLOW`, `VOLUNTARY_NATIONAL_SALES_MWH`,
`VOLUNTARY_NATIONAL_SHARE_OF_RETAIL_SALES`, `WEATHER_YEAR_POOL`, `WEATHER_YEAR_POOL_BY_ISO`)
and 8 `iso_configs.py` privates (`_ISO_BUILDERS`, `_STEAM_CLASSES`, …) that are read by name
inside their own module's builders. Those 7 are rule-26 candidates and are **routed**, not
touched.

### 2.2 The forecast solve path's tables, by mechanism (the charter's list, answered)

Region tags are the consumer module's region; *FORECAST-ONLY* means every consumer is capacity
evolution or forecast demand shaping, so the table is inert in a backcast.

| mechanism | tables (defining module) | lane |
|---|---|---|
| demand growth + vintages | `DEMAND_GROWTH_RATES`, `DEMAND_GROWTH_RATES_VINTAGES`, `DEMAND_GROWTH_TRANSITION_YEAR` (constants, via `scenario_resolvers`) | FORECAST-ONLY |
| data-centre / electrification / voluntary demand | `DATACENTER_ADDITIONS_MW`, `DATACENTER_ZONE_SHARE`, `ELECTRIFICATION_LAYERS`, `HEAT_PUMP_BALANCE_POINT_C`, `VOLUNTARY_*` ×5 (constants) | FORECAST-ONLY |
| adequacy requirement + accreditation | `PLANNING_RESERVE_MARGIN_BY_ISO` (+`_ICAP_TO_UCAP_RATIO`), `ADEQUACY_*` ×4, `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO`, `NET_ICR_*`, `NYCA_*` ×3, `FORECAST_POOL_REQUIREMENT*`, `THERMAL_ACCREDITATION_*`, `THERMAL_ELCC_CLASS_RATING_BY_ISO`, `HYDRO_ACCREDITATION_CREDIT_BY_ISO`, `DEMAND_RESPONSE_SUPPLY_*`, `LOCALITY_*` ×2, `NYISO_LOCALITY_UDR_ICAP_MW` (capacity_market) | FORECAST-ONLY |
| ELCC / NQC curves, storage ELCC | `RENEWABLE_ELCC_CURVES_BY_ISO`, `RENEWABLE_NQC_CURVES_BY_ISO`, `RENEWABLE_CAPACITY_CREDIT(_BY_ISO)`, `STORAGE_ELCC_*` ×5 (capacity_market) | FORECAST-ONLY / storage both |
| capacity market | `MARKET_DESIGN`, `DEFAULT_MARKET_DESIGN`, `MARKET_DESIGN_VINTAGES` + the composed demand curves and net-CONE pieces (capacity_market) | both (dispatch reads `MARKET_DESIGN` for AS revenue; evolution for the price) |
| entry, queue caps, learning | `NEW_ENTRY_COSTS`, `TECH_COST_MULTIPLIERS`, `ATB_TECH_WACC_REAL`, `QUEUE_CAP_GW`, `QUEUE_CAP_PER_TECH_GW`, `GLOBAL_ANNUAL_DEPLOYMENT_GW`, `WRIGHT_REFERENCE_GW`, `CCUS_PARAMS`, `GEOTHERMAL_PARAMS`, `HYDROGEN_TURBINE_PARAMS`, `OFFSHORE_WIND_PARAMS` (constants) | FORECAST-ONLY (offshore CF both) |
| CCS constants | `FUEL_CO2_FACTOR_PER_MMBTU`, `CO2_RATES`, `HEAT_RATE_BINS` (constants; the retrofit reference host is derived from these) | both |
| storage entry / base fleet | `STORAGE_BASE_FLEET_MW`, `STORAGE_ANNUAL_BUILD_CAP_MW`, `STORAGE_DEPLOYMENT_CEILING_MW`, `STORAGE_TECH*` ×4, `STORAGE_MEASURED_BASE_FLEET_ISOS`, `PUMPED_STORAGE_*` (capacity_market / constants) | both |
| retirement thresholds | **none in the registries** — `retirement_years_*`, `coal_fom_multiplier`, `retirement_execution_lag_*` are `ScenarioConfig` fields and already keyed; the registry side is `EFORD`, `VOM`, `NOX_RATES` (both lanes) | — |
| carbon / RPS / clean tiers | `CARBON_PRICE_PATHS`, `STATE_CARBON_PRICE_BY_ISO`, `CAP_AND_TRADE_PROGRAMS`, `RGGI_*`, `CARB_*`, `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE`, `STATE_RPS_*`, `RPS_ELIGIBLE_FUELS_BY_ISO`, `MISO_*_REGIONS`, `WIND_PTC_STATUTORY_USD_PER_MWH` (fuel_trajectories / capacity_market / constants) | both |
| fuel | `HENRY_HUB_TRAJECTORIES`, `GAS_BASIS_DIFFERENTIAL`, `GAS_MONTHLY_SEASONALITY`, `COAL_PRICE_*`, `PRB_*`, `OIL_PRICE_*`, `NUCLEAR_FUEL_PRICE_HISTORICAL`, `BIOMASS_PRICE_PER_MMBTU` (fuel_trajectories) | both |
| availability / fleet physics | `THERMAL_AVAILABILITY`, `SUMMER_CLASS_DERATE`, `MAINTENANCE_MONTHLY_SHAPE`, `NUCLEAR_MONTHLY_CF(_BY_YEAR)`, `CORRELATED_OUTAGE_CURVE`, `COAL_MAX_CF_BY_PLANT`, `*_COMMITMENT_PARAMS`, `*_STARTUP_PARAMS`, `MIN_STABLE_PCT_PHYSICAL` | both |
| renewables base pools | `RENEWABLE_INSTALLED_MW`, `RENEWABLE_AVG_CF`, `OFFSHORE_WIND_*` (constants) | both (forecast seeds from the pool) |
| interchange / TTC | `NYISO_INTERFACE_TTC_BY_*`, `MISO_RDT_*`, `MISO_RPE_DEMAND_VALUE`, `ERCOT_GTC_LINK_MAP`, `PJM_INTERFACE_LINK_MAP`, `CARB_UNSPECIFIED_IMPORT_EF` | both |
| ancillary | `AS_REVENUE_PER_KW_YR_BY_ISO`, `AS_SATURATION_REF_GW_BY_ISO`, `ERCOT_AS_SATURATION_EXPONENT` | both |
| backcast offer channel | `COAL_*_BY_ISO` ×7, `GAS_OFFER_MARGIN_ANCHOR_BY_*`, `CC_COMMITTED_OFFER_LEVEL_BY_ISO`, `PJM_MEASURED_INTERNAL_TTC`, `*_SEAM_FLOW_PERCENTILE` — read only by `run_calibration*.py` | BACKCAST-ONLY |

The full 310-row classification is reproducible from §9.1; it is not reproduced here because a
list that long goes stale the week it is committed, and the fingerprint's own diff tool (§6.3)
is the durable form of it.

### 2.3 Registries OUTSIDE the five config modules — scope boundary, stated

`grep` for module-level `*_BY_ISO` / `*_CURVE` / `*_MW` definitions finds further registries in
`model/reserves/spec.py` (20: the ERCOT AS floor/cap MW, MISO RDC, CAISO spin curves),
`model/interchange/spec.py` (5), `config/plant_taxonomy.py` (2), `config/entry_config.py` (1),
`pipeline/flags.py`, `pipeline/offer_curve_base/generic.py`, `data/maxgen_events.py`
(`MODEL_TZ_BY_ISO`), `results/scarcity.py` (2, reporting) and `data/nyiso_par_attribution.py`
(`PAR_REGISTRY`). Two properties decide phase-1 scope: **importable standalone** (the four
config registry modules import nothing but each other and stdlib — verified at every one of the
51 window merges, §4.1 — while `reserves/spec.py` and `interchange/spec.py` import
`data.fleet`) and **no import-time file read** (the four have none; `iso_configs.py` builds
`RELIABILITY_FLOOR_REGISTRY` from `data/raw/reference/reliability_floor_coeffs_<ISO>.csv` at
import, `scarcity.py` has 3 reads, `nyiso_par_attribution.py` 1). Phase 1 hashes the four
standalone modules plus the three pure-value ones (`plant_taxonomy`, `entry_config`,
`offer_curve_base/generic`); the reserve and interchange spec registries are **phase 2**
(hash their literals by AST extraction, or split them out — a design choice not made here), and
the floor-coefficient CSVs are a **data-basis** question routed to the rule-23 re-derive
discipline, not a code fingerprint.

---

## 3. What each surface would have said about the three incidents

| | D55 (code: float ordering) | SCN-LOAD (constants) | D77 (code: `Generator` attribute) |
|---|---|---|---|
| (a) value fingerprint | **miss** | **catch** — 3 names, all 6 ISOs (`DEMAND_GROWTH_RATES` every row; `DATACENTER_ADDITIONS_MW` 5 rows; `ELECTRIFICATION_LAYERS` 3 rows) | **miss** |
| (b) source-tree hash | catch | catch | catch |
| (c) mechanical epoch | miss — never ledgered | miss — entry routed, not written | **catch** — entry 2026-09-06b exists; mechanised it re-keys `mode=forecast` ∧ horizon ≥ 2028 |
| (d) hybrid | miss | catch (via a) | catch (via c) |

D55 is the honest residual of every option but (b): the lane believed the change was
arithmetic-identical, so no declaration was ever going to be made. The only mechanical detector
of an *unrecognised* code change is a hash of the code, and §4.2 prices it.

---

## 4. THE MECHANISM — four options, each measured on the 2026-08-07 → 2026-09-06 window

The window holds **1,453 first-parent merges** on `origin/main`; **225** touch `src/market_sim`
on **28 of 31 days**; **241** touch `check_forecast_staleness.py`'s `SOLVE_AFFECTING_PATHS`;
**64** touch one of the five config registry modules (`constants.py` 38, `capacity_market.py`
24, `iso_configs.py` 15, `fuel_trajectories.py` 2, `ercot_envelopes.py` 0), **51** one of the
four standalone ones.

### 4.1 (a) `constants_fingerprint` — canonical-JSON hash of the registry values

Measured by importing the four standalone modules at each of the 51 merges and at its first
parent (`git archive` of just those files into a temp tree, subprocess import, canonical JSON:
dataclass → `asdict`, dict keys sorted, `frozenset` sorted, `float` → `repr`), per name:

| of the 51 registry-touching merges | count |
|---|---|
| no value-level change at all (comment / docstring / formatting) | **10** |
| additions or removals of names only, no existing value moved | **25** |
| an EXISTING solve-affecting value moved | **16** |
| import error at any sha | 0 |
| a value that fails canonicalisation, at any sha | **0** (of ~300 names × 102 snapshots) |

So a fingerprint over the whole surface fires on **41 of 51**, and **all 25 addition-only
merges move every ISO** — a new `*_BY_ISO` table carries a row per ISO, so under naive hashing
"add a default-off mechanism's table" re-keys the program, which is precisely D24 §7's option-(a)
failure (*"the schema grew 604 → 765 fields in five weeks; under (a) each addition would have
re-keyed every config"*) reappearing one layer down. **Two refinements change the picture
completely, and both are measured:**

* **ISO projection.** A dict whose top-level keys are all ISO names is hashed per row; a name
  carrying an ISO token (`ERCOT_…`, `NYISO_…`) is scoped to that ISO; everything else is shared.
  Of the 31 changed-name events in the 16 value merges: **23 by-ISO rows, 7 ISO-token, 1
  shared**. Per-ISO firing over 30 days: **ERCOT 5 · CAISO 3 · PJM 2 · MISO 5 · NYISO 5 ·
  NEISO 7**, against 16 for the unprojected whole. Every one of the 16 is a named repair
  (the SCN-LOAD re-derivation, the NEISO FCA / MISO RBDC curve repairs, the adequacy operand
  rows, the NYISO TTC and carbon rows, `QUEUE_CAP_PER_TECH_GW["ERCOT"]`, …), i.e. **zero
  spurious fires among the value changes.**
* **Drop at the frozen registration hash — (b′-1) for tables.** Each name (each ISO row of a
  by-ISO table) has a declared hash recorded when it is registered; the key payload carries a
  name only when its live hash differs from the declaration. A NEW table is registered at its
  hash in the PR that adds it (CI check, the exact shape of `check_cache_key_registration`
  check 1), so **additions move no key**; a value change moves the keys of the ISOs whose rows
  moved, permanently (declarations are append-only and never edited, check 4's rule); a revert
  returns to the declared hash and to the pre-change key, which is correct because it is the
  same model. Landing moves **zero** keys.

What (a) catches: any value change in the hashed modules, automatically, scoped. What it
invalidates spuriously: nothing measured — a value change to a table the ISO's own path never
reads under its posture (a gated-off mechanism's table) still moves that ISO's keys; the 30-day
sample contains no such case, and the cost if one occurs is a cache miss, never a wrong answer.
What it cannot see: code (§3), and the registries outside its module scope (§2.3).

### 4.2 (b) a solve-path source-tree hash

Measured three ways over the same window, on the first-parent diff of each merge:

| definition | merges | days with ≥1 |
|---|---|---|
| any file under `src/market_sim` touched | **225** | 28 / 31 |
| ≥1 touched `.py` whose AST differs with docstrings stripped (comment/docstring-only churn removed) | **207** | 28 / 31 |
| the AST-differing file is on the forecast-evolution path (`capacity_evolution/`, `capacity.py`, `datacenter.py`, `voluntary_demand.py`, `scenario_resolvers.py`, `runner.py`) | **53** | 16 / 31 |
| the AST-differing file is one of the three that carried D55 and D77 (`retirements.py`, `ccs.py`, `campd_bins.py`) | **31** | 12 / 31 |

Most-churned files: `scenarios.py` 116, `constants.py` 35, `runner.py` 34, `capacity_market.py`
20, `data/fleet/assembly.py` 20, `data/fleet/arrays.py` 20, `retirements.py` 16. A tree hash
re-keys every bundle in the program roughly **seven times a day**; narrowing it to the files
that actually carried the two code incidents still re-keys **every other day**, and narrowing
further is guessing which file the next D55 lives in. It also breaks the property every
committed key relies on — that a key is reproducible from a recorded config — because the
reproduction would need the exact tree. **Rejected.** Its one legitimate descendant is the
per-lane G-DRIFT audit rule 29(b) already requires, which is (b) done by a reader with the
hunk in front of them; §6.4 proposes making that audit's *existence* mechanical without
making its *verdict* mechanical.

### 4.3 (c) the human-read epoch ledger + denylist, made mechanical

The ledger's own docstring refuses a global `CACHE_EPOCH` for the right reason: a single token
in the key re-keys every config including the backcast keepers, and a token outside the key is
inert. The mechanical form that survives that objection is a **scoped** epoch: each entry
declares in code what its prose already declares — `mode`, `isos`, and the horizon predicate
(`reaches_year`, the "whose horizon reaches 2028" clause the ledger states on six lines across
the 2026-08-31 → 2026-09-06e entries) — and
the key carries the ids of the epochs whose scope matches the config. A backcast-only entry
(2026-08-04c's CAISO storage seed) touches no forecast key; a forecast-≥2028 entry touches no
backcast and no 2026-2027 hindcast. The existing `CONTAMINATED_CACHE_KEYS` denylist stays as
it is: it refuses specific *bundles*, which is a different job from re-keying a *class*.

What (c) catches: exactly what a lane declares. Measured recall on this window's three
incidents: **1 of 3** (D77). What it invalidates spuriously: nothing — scope is declared per
entry. Its failure mode is silence, and the window shows silence twice.

### 4.4 (d) the hybrid — (a) automatically, (c) for code hunks

(a) as §4.1 with both refinements, plus (c) as §4.3. Catches 2 of 3 incidents on this window
(§3), moves zero keys at landing, fires 2–7 times per ISO per 30 days on measured value changes
and once per declared code epoch. **This is the recommendation**, with the build spec in §6.

### 4.5 Two scope decisions inside (d), decided here

* **Backcast keys carry the fingerprint too.** 9 of the 16 value changes were to both-lane
  tables (`MARKET_DESIGN`, `NUCLEAR_MONTHLY_CF_BY_YEAR`, `ERCOT_GTC_LINK_MAP`, the NYISO TTC
  tables, `STATE_CARBON_PRICE_BY_ISO`, `AS_REVENUE_*`, `RENEWABLE_AVG_CF`) and a keeper replay
  through the calibration lane's own `results/<ISO>/<key>` cache is the same hazard. The cost
  is that a forecast-only change (7 of 16) also moves the ISO's backcast key: a cache miss in a
  session container, never a wrong answer, and committed keeper bundles are files. A lane-scoped
  surface (drop FORECAST-ONLY names from backcast keys) would need a maintained lane registry
  that rule 24's "derived, never set" spirit argues against; it is available later as a declared
  `FORECAST_ONLY_NAMES` frozenset if backcast churn proves costly, and it is not in phase 1.
* **No mode/horizon predicate on (a).** A table change is hashed whatever the run's horizon;
  the horizon predicate belongs to (c), where a human has already stated it.

---

## 5. BLAST RADIUS and the landing moment

### 5.1 What is committed, counted

| population | count |
|---|---|
| committed `run_config.json` | 146 (61 forecast namespace, 18 `results/calibration`, 7 `run-config-debt`, rest probes/handoffs) |
| `frontend/data/hindcast` sidecars | 106, of which 105 carry a 16-hex `cache_epoch`, 100 distinct |
| `results/**/meta.json` carrying `cache_key` | 82 |
| cache-shaped bundle dirs (`config.yaml` beside parquet) | 27 |
| `ff-verdicts.json` rows | 105, of which 36 are `-pre-*` preserved priors |
| 16-hex literals in tests | 65 across 34 files (some are dated prose measurements); D60's one re-key touched **26 files** |
| bare keys re-pinned by D65-B-R PRECOMMIT Addendum C | 14 (6 ISOs × forecast/backcast + the two global pins `547053bdfccd4264` / `f61891696e671969`) |

### 5.2 Keys moved at landing, per option

| option | forecast default | bare backcast | 14 bare keys | on-disk caches orphaned | pins to advance |
|---|---|---|---|---|---|
| (a) naive whole-surface | moves | moves | 14/14 | all | ~26 files |
| (a) with frozen registration hashes | **0** | **0** | **0/14** | none | none |
| (b) | moves, and again at the next merge | same | 14/14, ~7×/day | all, continuously | untenable |
| (c) scoped epochs, empty at landing | 0 | 0 | 0/14 | none | none |
| **(d) as recommended** | **0** | **0** | **0/14** | **none** | **none** |

The merge gate is the D24-R one, re-run: apply the new key to every committed `run_config.json`
(146) and assert 0 moved (`capxd24r_cache_key_no_op_check.py`'s shape, committed record).

### 5.3 The `-pre-*` convention is unchanged, and becomes more honest

`-pre-<lane>` is a **verdict-row** convention in `ff-verdicts.json` (36 rows today): the bare
recipe label (`neiso-t1f`) keeps the live verdict and the displaced verdict is preserved whole
under `neiso-t1f-pre-d60`. It is keyed by recipe, never by cache key, so nothing in it moves.
What changes is the stamp: `forecast_provenance` reads `cache_epoch` off the run's own
artifacts and never recomputes it, so a row scored before the fingerprint keeps its old key
(historical record, exactly as D60 §7 treats the hex-less t1x stamps) and a row scored after
carries a key that encodes the surface. D24 §9.3's standing complaint — `cache_epoch` is
non-identifying, two postures at one key and one posture at two keys — is closed in the one
direction a key can close it: two runs of one recipe on two surfaces now hash differently, and
the sidecar says which table moved (§6.2, the `solve_surface` stamp).

### 5.4 When to land — Q47's logic, applied to what is actually on `main`

Q47's "one re-key event" exists because a batch pre-declares its realized keys in a PRECOMMIT and
a key that moves under it fires the batch's STOP; two re-key events a day apart mean one of them
lands mid-batch. Measured at HEAD `0336ccd8`: the D65-B-R finding is merged as a **checkpoint
with §0 / §5 / §6 unfilled**, its branch is deleted, and **none of its seven pre-declared batch
keys** (`9b9e5a48e3ca5c8e`, `c3519b861f920bbe`, `f62431376dd9df03`, `17770cdad3230938`,
`43cee1c9558ab859`, `74359fedbf2eadd6`, `0fc42cb56c24d544`) appears on any board sidecar; the
newest stamps are the SCN load-campaign rows at `9fe7e906` (08:37Z). So the batch the charter
names as the natural moment has not registered on `main` yet, and D67-ARM, D78-R and D81 are
queued to pre-declare behind it.

Because the recommended shape moves **no key at landing**, it does not need that moment and
does not collide with it: it can land now, and the in-flight batch's pre-declared keys hold
exactly as long as no registry row of its ISO moves before each leg solves — which is the
condition under which those keys *should* hold. If a row does move mid-batch, the leg's
realized key differs from its pre-declaration and the STOP fires **correctly**, which today it
would not. The one ordering constraint is the opposite of Q47's: land **before** D67-ARM / D78-R
/ D81 write their PRECOMMITs, so their pre-declared keys are computed under the fingerprint and
carry the `solve_surface` stamp from the first solve.

If the director prefers the explicit form (the fingerprint always in the payload, no frozen
registration hashes — simpler code, self-describing keys), then Q47's logic applies in full and
the landing is the next program-wide re-key event, after D65-B-R registers. §6 specifies the
frozen-hash form; the explicit form is the same code minus the declaration ledger and its
two guard checks.

---

## 6. RECOMMENDATION — (d), and the phase-1 build spec

### 6.1 Files and functions (nothing here is written in phase 0)

| file | change | rule 27 |
|---|---|---|
| **NEW** `src/market_sim/config/solve_surface.py` (< 300 lines) | `SURFACE_MODULES` (the seven §2.3 modules); `canonical(value)`; `surface_rows(iso) -> dict[name, hash]` (ISO-projected, `lru_cache` per process); `moved_rows(iso) -> dict[name, hash]` (rows whose hash ≠ their declaration); `SolveEpoch` dataclass (`id`, `modes`, `isos`, `reaches_year`, `cause`) + `SOLVE_EPOCHS: tuple` (append-only, **empty at landing**); `applicable_epochs(config) -> list[str]`; `surface_stamp(iso, config) -> dict` for sidecars | new file |
| **NEW** `src/market_sim/config/solve_surface_declared.py` | `DECLARED: dict[str, str \| dict[str, str]]` — the frozen registration hash per name (per ISO row for by-ISO tables), one line per name, **append-only**, generated by the register script, never hand-edited | new file |
| `src/market_sim/config/scenarios.py::cache_key` | after the retired-field re-insertion, before path folding: `moved = moved_rows(self.iso)`; `if moved: payload_dict["__solve_surface__"] = moved`; `ep = applicable_epochs(self)`; `if ep: payload_dict["__solve_epochs__"] = ep`. Dunder keys cannot collide with a field, survive `_normalize_cache_key_paths` untouched (no path prefix), and are invisible to `config_disagreements` (which iterates `asdict`, not the payload). ~10 lines, Edit tool, blob-verified | ≥300 lines: edit, never rewrite |
| `src/market_sim/results/cache.py` | `save_result` writes `solve_surface.json` beside `config.yaml` (iso, moved rows, epochs, full fingerprint, git sha); module docstring gains the paragraph that says the key now sees the surface, and the ledger's future same-key entries name their `SolveEpoch` id. The 2026-09-06b (D77) entry is the first to be back-filled as an epoch **only if** the director wants pre-landing bundles re-keyed — otherwise it stays prose and the epoch list starts empty | ≥300 lines: edit |
| `src/market_sim/pipeline/persist.py`; `scripts/run_full_horizon.py:829`; `scripts/run_capacity_hindcast.py:2470`; `src/market_sim/results/export.py:383` | every site that writes `"cache_key"` also writes `"solve_surface": surface_stamp(...)` | small edits |
| `scripts/lib/forecast_provenance.py` | `PROVENANCE_FIELDS += ("solve_surface",)`, read from the artifact exactly as `cache_epoch` is, never recomputed | small edit |
| `scripts/check_cache_key_registration.py` | **check 5** (FAILS the PR, `--base`): every module-level UPPERCASE name in `SURFACE_MODULES` present at HEAD has a `DECLARED` entry; **check 6** (FAILS): `DECLARED` and `SOLVE_EPOCHS` are append-only — an edited hash or a removed id fails unless the name left the module (rule 26, retired at its last hash exactly as `_CACHE_KEY_RETIRED_FIELDS`); **check 7** (WARN): a `**Epoch <date>` heading added to `cache.py`'s ledger with no matching `SolveEpoch` id and no "KEY ADVANCE" marker | extend |
| **NEW** `scripts/solve_surface_register.py` | `--declare NAME [NAME…]` appends declarations at the live hash; `--diff <sha-or-worktree> [<sha>]` prints the per-ISO changed rows between two trees — the mechanised form of G-DRIFT's "`constants.py` FIRST" step (D65-B-R Addendum C §1b) | new file |
| `tests/regression/test_persisted_identity.py` | the two config pins are computed under a fixture that pins `moved_rows` to `{}` (so they keep measuring config identity alone); a new `PINNED_SURFACE_ROWS_BY_ISO` block pins `surface_rows(iso)` for the six ISOs with the same dated-cause-block discipline — a registry value change now fails **this** pin, and the cause block IS the ledger entry the lane owes | ≥300 lines: edit |

### 6.2 What a bundle records afterwards

```
results/<ISO>/<key>/
  year_2027.parquet
  config.yaml            # unchanged: asdict(config)
  solve_surface.json     # {iso, fingerprint, moved: {name: hash | {iso: hash}}, epochs: [...], git_sha}
```
`run_config.json` / `meta.json` / every board sidecar carry `solve_surface` beside `cache_key`.
Key reproducibility, which every re-key event so far has eroded, is restored in the stronger
form: `key = f(config, moved rows, epochs)` with all three recorded.

### 6.3 Tests (phase 1 delivers these with the code)

* `tests/unit/config/test_solve_surface.py` — canonicalisation is order-independent and
  type-faithful (dataclass, `frozenset`, tuple vs list, `float` repr, `Enum`, nested dicts);
  ISO projection rule (by-ISO dict → rows, ISO-token name → that ISO, else shared); a
  docstring/comment edit leaves every row unmoved; a value edit to `X["MISO"]` moves MISO's
  fingerprint and no other ISO's; a new name with a declaration moves nothing, without one
  fails check 5; a revert restores the declared hash and the pre-change key; `SolveEpoch`
  scope predicates (`modes`, `isos`, `reaches_year` against `end_year` / horizon) including the
  backcast-inert case; append-only guard cases mirroring D24-R's (edit → breach, add → clean,
  remove-with-name → clean, remove-alone → breach).
* `tests/unit/results/test_cache_solve_surface.py` — `save_result` writes the sidecar;
  `solve_surface.json` and `config.yaml` agree; a bundle solved on surface S1 is not addressed by
  a config on S2 (different key), and IS addressed after a revert to S1.
* `tests/regression/test_persisted_identity.py` — both config pins unmoved at landing (the
  fixture); six surface pins with cause blocks; the path-invariance test extended to the
  surface (a relocated checkout hashes identically — the surface has no paths).
* The merge gate: the D24-R no-op probe over all 146 committed run configs reads **0 moved**,
  committed as `capxd79-solve-surface-no-op-record.json`.
* CI: checks 5–7 run through the existing `check_cache_key_registration` step (already passes
  `--base`); no new workflow.

### 6.4 The D55 class — what phase 1 does and does not do about it

Nothing in (d) detects an unrecognised code change, and the memo does not claim otherwise. The
cheapest guard that is not (b) is process, not hashing: a **WARN-level CI check** that a PR
whose AST-level diff touches a forecast-evolution-path file (§4.2's third row: 53 merges / 16
days) must either append a `SolveEpoch` or carry an explicit inert attestation (a PR label, the
`file-integrity-guard.yml` `intentional-shrink` pattern) — the G-DRIFT audit's *existence*
made mechanical, its *verdict* left to the reader with the hunk in front of them. It is
offered as a card option, not folded into phase 1, because ~2 attestations a day is real
friction and the owner should price it.

---

## 7. DIRECTOR CARD — what needs a decision

| # | decision | recommendation |
|---|---|---|
| 1 | Adopt (d) as §6 specifies — per-name, ISO-projected value fingerprint with frozen registration hashes + scoped epochs | **ADOPT** |
| 2 | Landing form: frozen-hash (zero keys move; lands now, before D67-ARM / D78-R / D81 pre-declare) vs explicit (all keys move; lands at the next batch) | **frozen-hash, now** |
| 3 | Backcast keys carry the fingerprint | **yes** (§4.5) |
| 4 | Back-fill D77's 2026-09-06b as the first `SolveEpoch` (re-keys forecast ≥2028 bundles solved before it) or start the epoch list empty | **empty** — the D65-B-R batch is the re-solve; an epoch would re-key bundles that are being replaced anyway |
| 5 | The §6.4 attestation guard (WARN) | owner's call; recommend WARN for 30 days, then measure |
| 6 | Phase 2 scope: `reserves/spec.py` + `interchange/spec.py` registries; the floor-coefficient CSVs under rule 23 | route to a later card |

Owner-tier because it changes what every key in the program means (rule 24: a derived
component, never settable — no env var, no CLI flag, no `ScenarioConfig` field), touches two
≥300-line core files (rule 27), and adds two append-only ledgers (rule 26: a retired name keeps
its last hash; an epoch is never removed). It is **not a mechanism** (rule 28 not triggered —
no `ScenarioConfig` field, no matrix row; the D24-R precedent). Assign phase 1 to Opus or
Fable (rule 27, core infrastructure).

---

## 8. Governance attestation (phase 0)

| gate | reading |
|---|---|
| LP | **zero** — no solve, no bundle, no `--out-dir` |
| code | **none** — one new document; no source, test, script, registry, board, keeper, shard, marker or matrix file touched |
| rule 22 `[R-HOLDOUT]` | nothing year-scoped read or written |
| rule 24 `[R-REGISTRY]` | no tunable proposed; the fingerprint is derived from the registries, never set |
| rule 25 `[R-ISO-SCOPE]` | the projection keeps each ISO's key sensitive to its own rows; nothing transferred |
| rule 27 `[R-PUSH]` | no existing file edited; the phase-1 spec names its two ≥300-line edits and forbids rewriting them |
| rule 28 `[R-MECH-MATRIX]` | not triggered — cache plumbing, no mechanism, no cell |
| clone | deepened `--filter=blob:none --unshallow` to reach the window (the D24 precedent); read-side git under `GIT_NO_LAZY_FETCH=1` except the deliberate `git archive` / `git show` of registry and source blobs at historical shas |

---

## 9. Method — every number above, re-runnable

1. **Inventory (§2).** `ast.parse` every `.py` under `src/market_sim` plus
   `scripts/run_{full_horizon,capacity_hindcast,calibration,calibration_full}.py`; collect
   module-level `Assign`/`AnnAssign` UPPERCASE targets in the five config registry modules
   (definitions, with the value node's kind); collect `ImportFrom` names from those modules,
   `from market_sim.config import <module>` aliases and `<alias>.NAME` `Attribute` reads
   (consumers, relative imports resolved); map consumer modules to regions by path prefix
   (`model.capacity_evolution` / `model.capacity` → FORECAST-EVOLUTION; `data.datacenter` /
   `policy.voluntary_demand` → FORECAST-DEMAND; `results.*` → REPORTING; `ensemble` / `matrix` /
   `uncertainty` / `structural_prior` → ENSEMBLE; `config.*` → CONFIG; the rest of `model` /
   `data` / `pipeline` / `policy` / `runner` → both-lane solve). 310 definitions, 0 unresolved
   attribute reads.
2. **Value fingerprint history (§4.1).** For each first-parent merge in
   `git log --since=2026-08-07 --first-parent origin/main -- <the four registry files>` (51):
   `git archive <sha> src/market_sim/__init__.py src/market_sim/config/{__init__,constants,capacity_market,fuel_trajectories,ercot_envelopes}.py`
   into a temp tree for `<sha>` and `<sha>^1`; in a subprocess with `PYTHONPATH=<tree>/src`,
   import the four modules and emit `{name: sha256(canonical JSON)[:16]}` — canonical =
   `dataclasses.asdict` for dataclass instances, sorted dict keys, sorted `frozenset`, `repr`
   for floats, `Enum.value`, `str(Path)`; classes and callables skipped. Diff parent vs merge
   per name; "existing value moved" = changed ∧ not added ∧ not removed.
3. **ISO projection (§4.1).** Same snapshots, with each name emitted as `by-iso` (dict whose
   top-level keys ⊆ {ERCOT, CAISO, PJM, MISO, NYISO, NEISO}: per-row hashes), `iso-token`
   (name starts with / contains `_<ISO>_`), or `shared`; a merge "moves ISO i" if any name's
   projected hash for i differs. Run once over existing-value changes (16 merges) and once
   including additions/removals (41).
4. **Source churn (§4.2).** For each first-parent merge touching `src/market_sim` (225):
   `git diff --name-only <sha>^1 <sha> -- src/market_sim`; for each `.py`, `ast.dump` of both
   sides with module/class/function docstrings stripped; count merges with ≥1 differing file,
   and with a differing file under the forecast-evolution path set / the three incident files.
5. **Census (§5.1).** `git ls-files '*run_config.json'`, `'results/**/config.yaml'`,
   `'results/**/meta.json'`; `frontend/data/hindcast/*.json` provenance blocks;
   `ff-verdicts.json` keys; `grep -o '"[0-9a-f]\{16\}"'` over `tests/`; the seven D65-B-R
   batch keys grepped over the sidecars.
