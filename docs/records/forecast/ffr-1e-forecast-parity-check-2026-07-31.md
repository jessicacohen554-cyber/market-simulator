# FFR-1E — a standing backcast→forecast parity check (FR-22), and the eight gaps it found

**Session:** FFR-1E · **Date:** 2026-07-31 · **Scope:** detector + registry + tests + this doc.
**No LP anywhere. No mechanism wired. No keeper, default, band or dashboard touched.**

---

## 0. Headline

`scripts/check_forecast_parity.py` now sweeps all six ISOs' current keeper
postures — **474 armed mechanisms** — and resolves every one of them to either a
**forecast-orchestrator consumer found in the source** or an **explicit
declaration** in `scripts/lib/forecast_parity_registry.py`. Nothing is
unaccounted; the check exits 0 today and will fail loud the next time a keeper
arms a mechanism the forecast path cannot reach.

The nyiso-102 family — the incident that motivated FR-22 — passes at the
strongest evidence tier, from `runner.py` itself:

```
nyiso_local_selfsupply -> FORECAST_WIRED | orchestrator @ src/market_sim/runner.py:1208
nyiso_li_lcr_tsl       -> FORECAST_WIRED | orchestrator @ src/market_sim/runner.py:1217
nyiso_nyc_lcr_tsl      -> FORECAST_WIRED | orchestrator @ src/market_sim/runner.py:1572
```

Seeding the registry honestly surfaced **eight mechanisms, armed in five of the
six current keepers, that have no forecast-side consumer and no by-design reason
to lack one** (§4). They are FILED, not fixed: this session builds the detector,
per the prompt's explicit "do not wire any mechanism you find missing".

The one adjudicated (b)-case given as a seed — `nyiso_central_east_measured_ttc`,
K-backcast / G-forecast — is not armed in the current NYISO keeper, so it does
not appear in the sweep; its *reasoning* is what the registry's
measured-transmission family cites (§3, first row).

---

## 1. The parity report — all six ISOs

| ISO | keeper | armed | forecast-wired | backcast-only (declared) | alias | inert | **GAP** | **unaccounted** |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| ERCOT | `2026-07-31-ercot145-gas-daily-shape` | 88 | 85 | 1 | 0 | 0 | **2** | **0** |
| PJM | `2026-07-31-pjm-143b-hy-level` | 89 | 81 | 6 | 1 | 0 | **1** | **0** |
| CAISO | `2026-07-31-caiso148-nuclear-availability` | 87 | 82 | 1 | 1 | 1 | **2** | **0** |
| NYISO | `2026-07-31-nyiso105-chp-heat-rates` | 72 | 68 | 2 | 1 | 0 | **1** | **0** |
| NEISO | `2026-07-31-neiso-71-nucavail` | 57 | 53 | 2 | 1 | 0 | **1** | **0** |
| MISO | `2026-07-31-miso-109b-hy-level` | 81 | 73 | 6 | 1 | 0 | **1** | **0** |

Totals: 474 armed → 442 forecast-wired, 18 declared backcast-only, 5 alias,
1 inert, **8 filed gaps, 0 unaccounted**. Evidence tiers behind the 442:
`shared` 355, `orchestrator` 72, `dynamic` 8, `string_key` 7.

Regenerate at any HEAD:

```
python3 scripts/check_forecast_parity.py                    # text, exit 0/1
python3 scripts/check_forecast_parity.py --iso NYISO        # one lane
python3 scripts/check_forecast_parity.py --json             # machine-readable
python3 scripts/check_forecast_parity.py --markdown out.md  # the table above
python3 scripts/check_forecast_parity.py --strict-gaps      # also fail on §4
```

---

## 2. How the detector decides — and what it cannot decide

An **armed mechanism** is any `ScenarioConfig` field whose keeper value differs
from the dataclass default. Defaults are parsed with `ast` from
`config/scenarios.py` (never imported — stdlib only, no `uv sync`, seconds to
run, and it cannot be broken by a config-module import error). A default this
parser cannot evaluate is `UNRESOLVED`, which never compares equal — so the
artifact-path family cannot pass by accident; it carries a registry row.

**(a) forecast-orchestrator consumer**, strongest tier first, all AST-derived:

| tier | what it is |
|---|---|
| `orchestrator` | read in `src/market_sim/runner.py` itself — what the nyiso-102 fix produced |
| `shared` | attribute / `getattr` read in a shared `src/market_sim/**` builder both orchestrators thread their config into |
| `string_key` | the field name as a string constant in a shared builder — the `config_field="pjm_zonal_gas_basis"` channel, where the applier reads the field by a name its caller passes |
| `dynamic` | matches a curated `DYNAMIC_CONSUMERS` pattern — the `getattr(config, f"coal_{stem}_{p}")` family, invisible to a name scan |

Two exclusions do the real work, and both are consequences of the incident:

* **`backcast`-role sources are never evidence** — both calibration entry
  points **and `src/market_sim/pipeline/backcast_config.py`**. That module lives
  under `src/` and is import-reachable from `runner.py`, which is precisely why
  import-reachability is the wrong test: reachable ≠ called. (This is what makes
  `caiso_offer_surface_measured` a gap rather than a pass — §4.)
* **Reads inside `ARCHIVED_FUNCTIONS` are discarded** — today just
  `pipeline/commitment.py::run_commitment_pass`, the archived P2 solve. `runner.py`
  imports it, and its `preserve_min_gen` chain names `nyiso_local_selfsupply`.
  A naive field-reference scan would therefore have reported the nyiso-102
  incident as *wired* from 2026-07-29 onward — one day before the real fix. A
  check that goes green on its own motivating incident is worthless, so that
  read is excluded by name, with the CLAUDE.md P2-is-archived citation.

**Stated limitation, not hidden.** `shared`/`string_key` evidence proves a
shared builder reads the field; it does not prove that specific call sits on a
live forecast call chain. Function-granularity call-graph reachability is the
hardening lever if this class of defect recurs *inside* a shared module. The one
known non-live shared read is the archived P2 pass, excluded explicitly above.

**(b) declarations** are verified against the tree, so the escape hatch cannot
rot: every declared field must be a real `ScenarioConfig` field, covered by
exactly one row, with a one-line reason, citations that exist and name the
field, resolvable parents/alias gates, and — for `BACKCAST_ONLY` — **no**
forecast evidence. A mechanism wired forward later makes its own declaration
fail as stale rather than keeping a permanent exemption
(`test_stale_backcast_only_declaration_is_rejected` pins this).

---

## 3. The registry as seeded (18 declared backcast-only, 5 other rows)

The codebase already had a machine-readable declaration convention, and the
registry cites it rather than inventing a parallel truth. `scripts/run_calibration.py`
carries a banner — *"BACKCAST MEASURED INTERCHANGE OVERLAYS … backcast-only by
design (plan §3.1). None is reachable from the forecast path: the forecast
substitutes are noted per overlay"* — and each overlay sits under

```
# [measured: <source> | forecast substitute: <forward channel>]
```

The checker looks for that annotation above each declared field's backcast read
site and reports which rows carry it, so a row backed by the codebase's own
declaration is visibly distinguishable from one backed only by registry prose.

| fields | disposition | why (abridged) |
|---|---|---|
| `ercot_gtc_limits_measured` | BACKCAST_ONLY | measured hourly GTC export limits; forward TTC belongs to the static ratings + transmission-expansion registry — the `nyiso_central_east_measured_ttc` adjudication (K-backcast / **G**-forecast) applied to its ERCOT twin |
| `pjm_congestion`, `pjm_measured_interface_limits`, `pjm_east_interface_cut`, `pjm_external_net_position_cut` | BACKCAST_ONLY | measured PJM internal transfer-limit postings, each labelled "backcast overlay" at its call site; same forward owner |
| `miso_seam_flow_limit`, `miso_seam_export_limit`, `pjm_seam_flow_limit`, `pjm_seam_export_limit` | BACKCAST_ONLY | measured per-neighbour flow envelopes; in-code forecast substitute = the seam's `interface_limit_mw` + reference prices |
| `miso_seam_measured_ladder`, `nyiso_import_hub_prices` | BACKCAST_ONLY | measured seam price series; in-code forecast substitute = the gas-elastic reference-price formula |
| `caiso_corridor_flow_limit` | BACKCAST_ONLY | measured EIA-930 corridor p95 envelope; in-code forecast substitute = `caiso_corridor_atc_forward`, which the forecast runner wires instead |
| `carry_operating_mothballs` | BACKCAST_ONLY | gated on `config.mode == "backcast"` **in code**; a forecast must not carry mothballed units |
| `maxgen_emergency_tier_pricing` | BACKCAST_ONLY | its call site states "Backcast-only overlay (D-5): the forecast runner never arms it" |
| `dual_fuel_oil_reattribution` | BACKCAST_ONLY | output attribution only — the mask feeds `_dispatch_frame`; the LP-side consumer (`winter_fuel_inventory` oil-budget rows) is gated on a different flag, so the dispatch is unchanged either way |
| `neiso_oil_burn_budget` | BACKCAST_ONLY | SUPERSEDED reference path (EIA-923 petroleum **receipts** — a measured outcome its own call site marks rule-13 inadmissible); never a forward channel |
| `caiso_gas_floor_frac` → `caiso_gas_commitment_floor` | PARAMETER_OF | scale factor; reported **INERT** because the parent is not armed in the CAISO keeper |
| `miso_seam_envelope_merit_cap` → `miso_seam_flow_limit` | PARAMETER_OF | envelope composition semantics; inherits the parent's disposition |
| `plant_level_fleet` → `use_campd_bins` | FORECAST_ALIAS | the forecast path reaches the same per-plant bins via `fleet.assembly.load_or_synthesize_bins`, gated on `use_campd_bins` + `CAMPD_BINNING_ISOS` (see §5 for the residual asymmetry) |
| the five artifact-path fields | SCENARIO_INPUT | on-disk paths resolved through `config/paths.py`; plumbing, not a mechanism |

---

## 4. FILED FINDINGS — eight armed mechanisms with no forecast-side consumer

Each is armed in a **current keeper**, has no forecast-orchestrator consumer,
and has no by-design reason to lack one. **None is wired by this session.** Each
is one follow-up session (the next D-5), and each should confirm byte-identity
of the backcast before/after, as nyiso-102 did.

| # | mechanism | keeper(s) | why it is a gap, not a design | severity |
|---|---|---|---|---|
| F-1 | `reliability_floor_overrides` | NYISO | the keeper uses it to **disable** the five `NYISO_PEAK_WINDOW_FLOORS_OFF` limbs (owner directive 2026-07-27, the arming condition for `nyiso_gas_commitment_bridge` — rule 19 `[R-ONE-MECH]`, never stacked). The forecast orchestrator never reads the override dict, so a forecast on the keeper config **re-arms the floors the directive removed *and* keeps the bridge** — exactly the stacking the directive forbids | **HIGH** |
| F-2 | `tranche_startup_conditional_runs` | MISO, PJM | condition-keyed fast-start amortization horizon (CAMPD-measured run bands × the hour's net-load percentile). Forward-reproducible by construction — it keys off model-simulated net load, not an outcome | HIGH |
| F-3 | `neiso_winter_fuel_inventory` | NEISO | its own call site calls it the "**forward-derivable** capacity/logistics budget (tank fill + re-supply)" and the keeper path, explicitly against the superseded receipts twin — yet the forecast orchestrator never builds the oil-budget rows | HIGH |
| F-4 | `caiso_storage_shape_anchor` | CAISO | measured p95 hour-of-day charge/discharge **capability** envelope per MW of fleet — a rule-13-admissible capability input that regenerates forward | MED |
| F-5 | `caiso_offer_surface_measured` | CAISO | consumed only in `pipeline/backcast_config.py` — the backcast config builder. Its ERCOT/PJM offer-surface siblings are consumed in the shared `data/fleet/offer_surfaces.py` and pass, which is what makes this one an asymmetry | MED |
| F-6 | `ercot_storage_capability_measured` | ERCOT | measured storage capability envelope; the admissible twin `storage_as_commitment` **is** shared and passes | MED |
| F-7 | `ercot_storage_as_deployment` | ERCOT | measured AS-deployment shaping, same family and same asymmetry as F-6 | MED |
| F-8 | `plant_level_fleet` residual | CAISO, MISO, NEISO, NYISO, PJM | the mechanism itself resolves (FORECAST_ALIAS, §3), but the alias is not exact: the backcast additionally passes `legacy_n_bins=0` so an empty per-plant synthesis keeps per-plant identity instead of falling back to legacy heat-rate bins. The forecast path has no counterpart to that fallback | LOW |

Suggested lane order: **F-1 first** (a live contradiction with a standing owner
directive), then F-2/F-3 (both self-described forward-reproducible), then the
measured-capability family F-4/F-6/F-7 as one session, then F-5 and F-8.

**Adjudication note, F-1..F-7:** these are *forecast-reachability* gaps, not
claims that arming them forward is correct. A follow-up session may legitimately
conclude that a mechanism belongs in (b) instead — in which case the deliverable
is a declaration with its reason, not silence. What must not happen is a keeper
mechanism staying in neither set.

---

## 5. Observations recorded, not acted on

* **`neiso_oil_burn_budget` is armed in the NEISO keeper** while its own call
  site marks it a measured *outcome*, "inadmissible under CLAUDE.md #13 …
  never a keeper". It is dormant only by control flow: the oil-budget block is
  `if neiso_winter_fuel_inventory: … elif neiso_oil_burn_budget: …`, and the
  keeper arms both, so Component A wins and the receipts path never runs. The
  LP is therefore clean, but the posture rests on an `elif`, and
  `run_config.json` records an inadmissible flag as on. Worth a one-line
  cleanup in the next NEISO session; **not** a rule-13 breach as it stands, and
  this session changed nothing about it.
* **`plant_level_fleet`'s alias is not exact** — F-8 above.
* **D-5 and this check are complements, not duplicates.** D-5
  (`scripts/legitimacy_diagnostics.py::run_d5`) scores a curated ~30-row
  mechanism list *inside one bundle's* diagnostics, and is blind to anything
  absent from its registry. This check sweeps the *whole armed posture* of every
  current keeper and requires completeness. Neither subsumes the other; both
  read the same two entry sources, so they agree on the NYISO family.

---

## 6. CI wiring — held until FFR-1D merges

`.github/workflows/ci.yml` is FFR-1D's file this wave (prompt-pack §W1
file-ownership), so this session does **not** touch it. The job to add once 1D
merges, alongside the other stdlib guards (no `uv sync`, seconds):

```yaml
  forecast-parity-guard:
    name: FR-22 backcast->forecast parity
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      # FR-22: a mechanism armed in an ISO's keeper posture must have a
      # forecast-orchestrator consumer or an explicit backcast-only-by-design
      # declaration (scripts/lib/forecast_parity_registry.py). The nyiso-102
      # gap (three NYISO downstate mechanisms wired only in the backcast
      # orchestrator) was found by accident; this makes it a gate. Stdlib-only,
      # no LP. Filed gaps (ffr-1e findings doc §4) report but do not fail —
      # --strict-gaps flips that once they are closed.
      - name: check_forecast_parity
        run: python3 scripts/check_forecast_parity.py
```

Path filters to extend on the same edit: `src/market_sim/**`,
`scripts/run_calibration*.py`, `scripts/lib/forecast_parity_registry.py`,
`frontend/data/backcast/keepers/**`.

---

## 7. Files

| file | change |
|---|---|
| `scripts/check_forecast_parity.py` | new — the no-LP detector (AST scan, evidence tiers, keeper sweep, text/JSON/markdown reports) |
| `scripts/lib/forecast_parity_registry.py` | new — the committed declaration registry + source roles + archived-function exclusions + dynamic-consumer patterns |
| `tests/scoring/test_forecast_parity.py` | new — 22 tests, trivial-first (synthetic config source, synthetic one-field keeper postures) through the real six-keeper sweep, the nyiso-102 regression, and the stale-declaration guard |
| `docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md` | this doc |

## 8. What this session did NOT do

* **Wired nothing.** The eight gaps are filed, not fixed (prompt: "that is a
  follow-up finding with its own session — this session builds the detector").
* **No solve, no LP, no cache read** anywhere; nothing in `src/market_sim/`
  changed, so every keeper and every forecast run is byte-identical by
  construction.
* **No `ci.yml` edit** (FFR-1D owns it this wave) — §6 carries the job verbatim.
* **No mechanism-matrix cell change**: no mechanism was tested, proposed or
  armed, and no `ScenarioConfig` field was added or deleted (rule 28 duties a–d
  are not triggered).
* **No dashboard registration** (rule 15): no run was produced.
