# SPP Addition Program — plan, wave graph, prompt pack (2026-09)

Status: **CHARTERED 2026-09-06.** Owner request, verbatim: *"Develop a comprehensive plan to add
SPP as an iso to the model, from backcast testing, measured data needs & fetching, to downstream
html integration etc. … establish a workflow for an SPP model addition desk to act as workstream
director and follow the refresh protocol similar to the other workstream directors in the repo.
Make sure the plan assigns fable vs opus to different prompts and tasks."*

Director: the **SPP ADDITION DESK** (lane id `SPP-DESK`) — handoff prompt
`docs/handoffs/spp-desk-handoff-2026-09-06.md`, ledger `docs/handoffs/spp-desk-ledger-2026-09.md`.
**The ledger wins where this plan and the ledger diverge on live state.** This plan owns the
charters (§8) and the decisions (§3); the ledger owns who is running what.

Process authority: `docs/multi-iso/05-backcast-playbook.md` (Phase 0→6, §8 conventions) and the
Stage A–H checklist of `docs/multi-iso/00-iso-addition-protocol.md` §1–2. Where this plan and the
playbook disagree on *SPP specifics*, this plan wins; on *process*, the playbook wins.

---

## 1. Definition of done

| # | Done means | Surface |
|---|---|---|
| 1 | `"SPP"` in `config/iso_configs._ISO_BUILDERS`; `get_iso_config("SPP").validate_topology()` passes; every ISO-keyed registry has an SPP entry or a documented exclusion | `src/market_sim/` |
| 2 | A **2023–2025** backcast keeper (rule 16 `[R-ALLYEARS]`) scored under rubric v3.6 and registered on the backcast dashboard **with whatever determination it earns, reported at full magnitude** | `frontend/data/backcast/keepers/SPP.json`, `backcast-runs.html#iso=SPP`, `calibration-status.html#iso=SPP` |
| 3 | `docs/codebase-site/data/mechanism-matrix/SPP.js` shard live with a cell for every mechanism id; `docs/mechanism-testing-matrix.md` §5.7 SPP lever queue | matrix (rule 28) |
| 4 | `docs/calibration-log/spp.md` open; docs/site prose says seven ISOs; `docs/multi-iso/00` §0/§3 corrected | docs |
| 5 | **The six existing keepers' cache keys never move** at any wave (no new `ScenarioConfig` field, no default flip, no `results/cache.py` edit) | `tests/regression/test_persisted_identity.py`, keeper `run_config.json` |
| 6 | Forecast-program entry (T1-F hindcast, `program-status.json` row, `GOLDEN_ISOS`) — **W6, gated, ROUTED to the capx director**; not part of this desk's done | `frontend/data/forecast/` |

What this plan does **not** charter: any change to how MISO prices its SPP seam (the MISO lane's), any
holdout-year (2019–2022) solve for SPP (rule 22 — the `complete` marker is an owner act), any
reserve co-optimisation before a keeper exists (M2 is last, playbook §5).

---

## 2. Verified state at charter (2026-09-06, `origin/main` `b22b91c3`)

### 2.1 What already exists for SPP

| Asset | Path | Notes |
|---|---|---|
| EIA-930 SWPP hourly | `data/raw/eia-930-hourly/SWPP hourly.parquet` | 2015-07 → 2026-05; Demand, Net generation, Total interchange, `NG: COL/NG/NUC/WAT/SUN/WND/OIL/BAT/OTH` |
| EIA-930 SWPP extracts | `data/raw/SWPP_fueltype.parquet`, `SWPP_region.parquet` | per-BA extracts |
| SPP hub LMP actuals | `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` | 2023–2025, `year/hour/rt/da`, 8760 rows/yr, mean of `SPPNORTH_HUB`/`SPPSOUTH_HUB` |
| Its builder | `scripts/data/build_spp_lmp_reference.py` | reads the `portal.spp.org` file-browser API (see §2.4 — the API has moved) |
| CAMPD CEMS unit-level | `data/raw/campd-unit-level/<ST>_<yr>.parquet` 2019–2026 | present: KS ND SD AR LA MO TX IA MN MT · **missing: OK NE NM WY** |
| Dashboard colour | `docs/codebase-site/css/shared.css:84,1051,1139`; `js/backcast-runs.js:122` | `--iso-spp: #14B8A6` already reserved |
| SPP as MISO's neighbour | `model/interchange/spec.py:1046-1069` (`NeighborInterface("SPP")`), `:1139` (`MISO_SEAM_DIBA["SPP"]`), `:1247+` ladders; `data/neighbor_price.py:117` | **keep** — the MISO keeper depends on it |
| ERCOT↔SPP DC ties | `config/constants.py:4591-4605` `ERCOT_DC_TIE_ZONE_MAP["SWPP"]` (Monticello 600 / Oklaunion 220 MW) | ERCOT-side only |
| Timezone maps | `scripts/data/fetch_eia930_hourly.py:53`, `convert_eia930.py:61` (`SWPP → America/Chicago`) | already correct |

### 2.2 What is missing (Stages C–H)

`actual_lmp.json` SPP block · `SPP_<yr>_renewable_capacity.csv` + `calibration_reference.json` SPP
block · `campd-unit-outages-SPP.csv` (needs OK/NE CEMS) · zonal hourly load · N↔S TTC · wind
curtailment / HSL · per-zone wind shape · zonal gas hub · PRM / VRL / VOLL / LTLF citations ·
`scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/spp.py`.

### 2.3 The six-ISO pin — every place that flips at registration (W2 atomicity list)

| Pin | Path | Action |
|---|---|---|
| Builders + demand loaders | `iso_configs.py:1578` `_ISO_BUILDERS`; `data/eia930/demand.py:788-805` `DEMAND_LOADERS` + import-time assert | **same commit** — the assert rejects loader keys ∉ `SUPPORTED_ISOS` |
| Unknown-ISO fixture | `tests/curation/test_curate_load_forecast.py:149` uses `"SPP"` as the *unregistered* example | re-point to `"TVA"` |
| Six-set test | `tests/curation/test_curate_load_forecast.py::test_every_model_iso_is_registered` | 7-set |
| CI guard allowlist | `scripts/ci_refactor_guards.py:129-139` (allowlists the missing `load_forecast/spp.py`) | **DELETE the entry** (rule 26 `[R-DELETE]`), cite audit Y-21 |
| Coverage sweeps | `tests/unit/config/test_iso_coverage.py` (`ALL_ISOS = sorted(_ISO_BUILDERS)`) | auto-extend — SPP must satisfy queue cap, retirement/entry, carbon-`None`, and the no-import-node branch |
| Scarcity-seed checkpoint | `tests/unit/config/test_iso_config.py:514-531` (`["ERCOT","NEISO"]`) | untouched unless card P5 rules to seed |
| Matrix shard set | `tests/unit/config/test_mechanism_matrix_shard_migration.py:108,118` (base `isos` == `mm.ISO_ORDER`) | W2 SPP-21 |
| Tail threshold ×3 | `scripts/calibration_verdict.py:606`, `scripts/data/derive_actual_tail.py:57`, `derive_actual_amplitude.py:71` `ISOS` | all three |
| Multi-year set | `scripts/audit_keepers.py::_MULTI_YEAR_ISOS` | add SPP (rule 16 enforcement) |
| Memory classes | `scripts/run_isos_concurrent.py:119-126` | add SPP (KeyError otherwise) |
| Solve workflow dropdown | `.github/workflows/calibration-solve.yml:57` | add SPP |
| Data profiles | `configs/data-profiles.yaml` `isos:` tokens + `profiles:` | **token trap**: `spp` ⊂ `DAMLZHBSPP_*.zip` (ERCOT settlement-point zips). Tokens must be delimiter-bounded: `[swpp, "_spp.", "-spp.", "/spp/"]` + a unit test |
| Neighbour namespace | `data/neighbor_price.py::_HR_GAS_ELASTIC` keys are GLOBAL (`"SPP"`, `"PJM"` are MISO's seams) | SPP's neighbours named `MISO` / `ERCOT` (free); assert uniqueness |
| ~22 six-tuple tests | `tests/unit/model/test_capacity.py:3436`, `test_storage.py:177,1797`, `test_ccs_retrofit.py:1491`, `tests/unit/data/test_fleet.py:820,1531,2654`, … | extend, or document as deliberate exclusion (capacity-market subsets `_CURVE_ISOS`/`_CAPACITY_ISOS`; carbon `PATH_ONLY_ISOS`) |

### 2.4 Host reachability, probed 2026-09-06 from a session

| Host | Result | Consequence |
|---|---|---|
| `api.epa.gov` CAMPD bulk (`x-api-key: DEMO_KEY`) | 200 | OK/NE/NM/WY CEMS are **session-fetchable** (`scripts/data/fetch_campd_unit_level.py --year Y --states OK NE NM WY`; MISO LA_2023 precedent) |
| `api.eia.gov` v2 | 200 | sub-BA demand (`fetch_eia930_subba_demand.py`), interchange (`fetch_eia930_interchange.py --ba SWPP`), state delivered-gas series |
| `portal.spp.org` | 200 on pages; file-browser API answers `[]` on every listing and the LMP builder's download paths now **404** | the API form has moved since the builder ran → SPP-12 **re-discovers it from the portal pages' JS** before fetching; manual manifest is the fallback |
| `spp.org` | 200 | ITP / Planning Criteria / Market Protocols / LTLF / MMU PDFs |
| `oasis.oati.com/SWPP` | blocked | TTCs come from ITP report transcription (rule 14 reconciled estimate) until a binding-constraint archive lands |

### 2.5 Zonal load is session-fetchable

`scripts/data/fetch_eia930_subba_demand.py` pulls EIA-930 **sub-BA** hourly demand from the key-free
Grid Monitor six-month files; MISO's six zones were cut on this product (`miso-data-audit.md` Item 2,
`curate_zonal_shares.py::_MISO_SUBBA_ZONE_GROUPS`). EIA publishes ~17 SWPP sub-BAs (CSWS, EDE, GRDA,
INDN, KACY, KCPL, LES, MPS, NPPD, OKGE, OPPD, SECI, SPRM, SPS, WAUE, WFEC, WR). SPP-11 adds
`SUBBA_NAMES["SPP"]`. This makes any zone split up to sub-BA granularity **data-feasible on the load
side**, which is why topology is a card and not a default.

### 2.6 Stale doc

`docs/multi-iso/00-iso-addition-protocol.md` §0 (row "SPP · 2 zones (N/S) · SWPP") and §3 claim SPP is
registered. It is not. SPP-10 corrects both in place.

---

## 3. The eight decisions — owner cards P1–P8

Served by the desk at **sitting #2**, after W1's evidence lands (owner ruling, this charter: *"Let the
Phase-0 data audit decide"* the topology). Recommendation first and labelled; rulings appended to each
row verbatim and numbered in the ledger §2.

| Card | Question | Recommendation to present | W1 evidence it needs | Ruling |
|---|---|---|---|---|
| **P1** topology | 2 zones (SPP-North / SPP-South) vs 3 (+ the SPS / Texas-Panhandle pocket) | Register **2 zones** in W2 (`_SPP_STATE_ZONES`: ND SD NE MN MT IA KS MO WY → North; OK TX NM AR LA → South, sub-BA-refined where the audit says a state straddles); the SPS pocket becomes the pre-declared first structural lever **SPP-54** — promoted to W2 only if SPP-12 measures SPS-tie binding share ≥ N↔S share. Rationale: N→S wind export is SPP's system-level corridor and is hub-scorable today (N/S hub spread is a measured zonal benchmark); the SPS pocket is real (persistent negative SPS prices, largest curtailment share) but needs a second TTC (OASIS-blocked) and an SPS price series whose availability is unverified. Rule 1: a real structure enters regardless of fit — hence the pre-declared lever rather than a permanent omission | mean / p90 \|SPPNORTH−SPPSOUTH\| by year (SPP-12); binding-constraint share SPS-tie vs N↔S (SPP-12); sub-BA energy shares (SPP-11) | — |
| **P2** MISO seam from SPP's side | MISO already prices SPP from its side; no cross-ISO reconciler exists | **Per-ISO, independent (rule 25).** First keeper serves the **measured EIA-930 `Total interchange` schedule** (`_SCALAR_INTERCHANGE_ISOS` += SPP — the PJM/NYISO/NEISO precedent, playbook §8.2, rule 13-admissible). A priced `NeighborInterface("MISO")` off `actual_lmp_hourly_zonal_MISO.parquet` (MISO-West/South rows) is registered as the **forward** mechanism, default-off, validated in SPP-51 with `--priced-interchange`. The RDT wheel nets to zero at the SPP boundary and is ignored | SWPP↔MISO DIBA duration curve (SPP-11) | — |
| **P3** ERCOT DC ties | import node vs neighbour vs ignore | `NeighborInterface("ERCOT")`, 820 MW (the same CDR ratings ERCOT's map cites), border zone `SPP-South`; **inert** under the served schedule, armed with P2's priced seams in SPP-51. No import node (≈1.5 % of peak) | SWPP↔ERCO flows (SPP-11) | — |
| **P4** reserves | arm co-optimisation now or defer | **Defer.** M2 is last (playbook §5); MISO's co-opt was inert at its zone count and its tail question closed negative — SPP must prove non-inertness on its own data (rule 25). Shard cells `U`; SPP-56 queued last | — | — |
| **P5** scarcity seed | seed ORDC `default_scenario_overrides` like NEISO? | **No seed at registration.** `voll=2000.0` (FERC 831 offer cap; doc 02). SPP's scarcity is VRL / reserve-shortage-driven — a different object from NEISO's winter-gas overlay — and is designed by SPP-55 (Fable) after a committed control exists. Seeding flips `test_iso_config.py:531` and is therefore a ruling, never a default | `actual_tail.json` SPP counts at $200 and $300 (SPP-31 — reported at sitting #2 as a forecast from the hourly parquet) | — |
| **P6** `TAIL_THRESHOLD` | $200 or $300 | **$200** (summer-heat / winter-storm regime like ERCOT/MISO, not NE city-gate gas), in all three copies | tail counts at both | — |
| **P7** first-solve screen (rule 29) | there is no keeper, so 29(b) "keeper is control" is vacuous | **Control = none.** The first full 2023–2025 bundle IS the baseline and becomes every later SPP lane's 29(b) control. Screen year = the year with the **largest mean \|N−S\| hub spread** (a zero-LP, residual-blind statistic — the only structure beyond copperplate is the N↔S link, and its footprint is the spread). STOP gate structural only: link binds in the measured direction/season; fuel-mix within order of magnitude of EIA-923; no unserved energy / negative-price absurdities. Never "did C3a pass". Screen bundle deleted before merge (29c) | spread by year (SPP-12) | — |
| **P8** W6 routing | who charters forecast-program entry | **ROUTE to the capx director** with a card once a keeper exists; this desk never writes `program-status.json` / `ff-verdicts.json` / `GOLDEN_ISOS` | — | — |

Two further defaults that need no card, recorded here so no lane re-litigates them: `_MULTI_YEAR_ISOS`
gains SPP in W2 (rule 16 — a single-year SPP keeper is refused from day one); the SPP profile's
memory class is registered `per_plant=True, co_opt=False, peak_gb=<measured in SPP-40>`.

---

## 4. Wave graph

```
W1  Phase 0/1 — zero-LP, ADDITIVE files only (parallel; disjoint: docs / data+fetch scripts)
    ┌──────────────────────┐ ┌────────────────────────────┐ ┌────────────────────────────────┐
    │ SPP-10 data audit +  │ │ SPP-11 EPA CAMPD + EIA     │ │ SPP-12 portal.spp.org +        │
    │ doc 00 correction    │ │ sub-BA/interchange/gas     │ │ spp.org PDFs (API re-discovery)│
    │ [OPUS] shared        │ │ [OPUS] shared              │ │ [OPUS] shared                  │
    └──────────┬───────────┘ └─────────────┬──────────────┘ └───────────────┬────────────────┘
               └──────────────────┬────────┴──────────────────────────────┘
                                  ▼   DESK SITTING #2 — cards P1…P8 served with W1 evidence
W2  Registration — THE PIN FLIP (one PR)                       ∥  matrix shard (disjoint files)
    ┌────────────────────────────────────────────┐   ┌──────────────────────────────────────┐
    │ SPP-20 register + topology + every registry│   │ SPP-21 7th matrix shard + §5.7 queue │
    │ [FABLE] shared→spp                         │   │ [OPUS] code                          │
    └──────────────────────┬─────────────────────┘   └──────────────────────────────────────┘
                           ▼
W3  Phase 2 derivation (parallel; each lane owns only its outputs)   ∥  site/docs wiring
    ┌───────────┐ ┌───────────┐ ┌────────────────┐ ┌───────────┐   ┌──────────────────────┐
    │ SPP-30    │ │ SPP-31    │ │ SPP-32 zonal   │ │ SPP-33    │   │ SPP-34 site JS/CSS/  │
    │ outages + │ │ bench-    │ │ shares + wind  │ │ seam      │   │ docs prose + log hdr │
    │ tranches  │ │ marks     │ │ shape + gas hub│ │ derive    │   │ [OPUS] code          │
    │ [OPUS] spp│ │ [OPUS] spp│ │ [OPUS] spp     │ │ [OPUS] spp│   └──────────────────────┘
    └─────┬─────┘ └─────┬─────┘ └───────┬────────┘ └─────┬─────┘  (SPP-33 is NOT a W4 precondition)
          └─────────────┴───────┬───────┴───────────────┘
                                ▼
W4  First-ever solve → FIRST KEEPER → dashboard flip (one lane)
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │ SPP-40 smoke → rule-29 screen (P7) → 2023-25 bundle → register → keepers/    │
    │ SPP.json + index.json + status/SPP.js + bench/SPP + shard stamp + log entry   │
    │ [FABLE] spp                                              ═══ DEFINITION OF DONE ═══
    └──────────────────────────────────────┬───────────────────────────────────────┘
                                           ▼
W5  Calibration loop — §5.7 lever queue, ONE lever = ONE lane = ONE PR, sequential, keeper is control
    SPP-51 seams (P2/P3 priced, --priced-interchange A/B)  [OPUS]
    SPP-52 HSL / curtailment as first-class metric          [OPUS]
    SPP-53 N↔S TTC from binding-constraint frequency        [FABLE]
    SPP-54 SPS-pocket third zone (P1 pre-declared lever)    [FABLE]
    SPP-55 VRL-based scarcity design                        [FABLE]
    SPP-56 reserve co-optimisation (M2, LAST)               [FABLE]
                                           ▼
W6  Forecast-program entry — GATED, ROUTED to the capx director (P8)
    SPP-60 T1-F hindcast + program-status.json row + GOLDEN_ISOS + goldens  [FABLE]

CRITICAL PATH:  SPP-11 (OK/NE CEMS)  →  SPP-20  →  SPP-30  →  SPP-40
```

Sequencing rules (playbook §8.5): lanes inside a wave are parallel because their files are disjoint by
construction; waves are sequential; W2's two lanes are parallel only because SPP-21 touches nothing under
`src/`. The desk holds any lane whose surface a live capx / SCN / per-ISO calibration lane is writing
(ledger §4).

---

## 5. Lane table

Column key — **Model**: `[FABLE]` = adjudication (topology / market-object design, the pin flip, the
first-keeper determination, novel-object kill-grading, scarcity/reserve/TTC design); `[OPUS]` =
execution of a committed recipe (census, fetch, frozen derives, shard emission, site wiring, pre-declared
solves). Sonnet never (rule 27 — every W2+ lane writes core scope; W1 lanes touch `scripts/data/` which
is Opus territory by the r#20 economy rule). **Profile** = the `DATA PROFILE:` line
(`configs/data-profiles.yaml`; `spp` exists only after SPP-20 lands).

| Lane | Model · why | Profile | Owns | Zero-LP gate | FINDING | Exit check |
|---|---|---|---|---|---|---|
| **SPP-10** audit — **LANDED 2026-09-06** (`docs/multi-iso/spp-data-audit.md`; `FINDING-spp-10-2026-09-06.md`) | OPUS · census against the MISO audit recipe; recommends, never decides | shared | `docs/multi-iso/spp-data-audit.md` (new); `00-iso-addition-protocol.md` §0 row + §3; `01-data-needs-and-upload-manifest.md` SPP rows | — | `FINDING-spp-10-<date>.md` = the audit doc | fleet census by BA `SWPP` off EIA-860 parquet (plants / MW by fuel vs SPP published totals); distinct plant states vs `campd-unit-level/` present → missing `<ST>_<yr>` list; SWPP 930 spans; **registry-values table** with a citation per value |
| **SPP-11** EPA/EIA fetch — **LANDED 2026-09-06** (all four items GOT, blocked table empty; `docs/handoffs/FINDING-spp-11-2026-09-06.md`) | OPUS · reproducible fetches with existing scripts | shared | `data/raw/campd-unit-level/{OK,NE,NM,WY}_{2023,2024,2025,2026}.parquet`; `data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv` + `SOURCES.md`; `data/raw/eia-930-interchange/SWPP interchange hourly.parquet`; `data/raw/gas-prices/eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv` + SOURCES; edits: `fetch_eia930_subba_demand.py` (`SUBBA_NAMES["SPP"]`), `fetch_eia930_interchange.py` only if not BA-parametrised | arrow schema equal to sibling files (the CAMPD fetcher already asserts this) | `FINDING-spp-11-2026-09-06.md` | DONE: 16 CEMS parquets (OK/NE/NM/WY × 2023-2026), schema == `KS_2024` all 16; SWPP sub-BA 447,049 rows / 17 sub-BAs / 0 interior gaps, reconciling to 0.9995-0.9999 of the BA `Demand`; SWPP interchange 268,177 rows / 11 DIBAs; four state delivered-gas series. READMEs/SOURCES rows added; no existing raw file rewritten. **`SHA256SUMS.txt` deliberately not extended** — its header scopes it to the untracked 2018 files, and these are tracked. Env carries NO `EPA_API_KEY`/`EIA_API_KEY`, so each credentialled route used its key-free EIA equivalent (documented in place). **Open, routed to the desk:** §6 row 14's NRC intake has no owning lane (charter TASK stops at item 4, no NRC path in FILES YOU OWN) — assign it. |
| **SPP-12** portal/spp.org fetch | OPUS · API re-discovery + transcription against a manifest | shared | `build_spp_lmp_reference.py` (`--per-hub` → `_validation-source/actual_lmp_hourly_zonal_SPP.parquet`); `data/raw/spp-hourly-load/`, `spp-genmix/`, `spp-binding-constraints/`, `spp-or-mcp/`, `spp-hsl/` (each with README + SOURCES); `data/raw/spp-planning/` PDFs or transcriptions (ITP, Planning Criteria PRM, Market Protocols VRL/offer cap, LTLF, MMU SOM) | listings return non-empty; a 2025 monthly file range-fetches | `FINDING-spp-12-<date>.md` with the reachable/blocked table and **the P1/P7 numbers** (hub spread by year; SPS-tie vs N↔S binding share) | anything still blocked becomes a manual-manifest row (§6) with the exact URL; never a guessed value |
| **SPP-20** register | FABLE · topology + market-object choices + the pin flip + rule-27 core scope | shared → spp | see §2.3 list + `_spp_config()`, `zone_assignment.py` (`_ISO_TO_BA_CODE`, `_LARGEST_ZONE`, `_EGRID_VINTAGE`, `_SPP_STATE_ZONES`, `_spp_zone`), `campd.py::ISO_STATES`, `eia930/frames.py::_ISO_TO_HOURLY_BA`, `eia930/demand.py` (`_load_spp_hourly_demand`, `DEMAND_LOADERS`, `_SCALAR_INTERCHANGE_ISOS`), `renewables.py::RENEWABLE_ZONE_ALLOCATION`, `transmission_expansion.py::TRANSMISSION_BASE_STATIC_VINTAGE`, `fleet/models.py::BA_CODE_TO_ISO`, `capacity_market.py` all-six dicts, `constants.py` all-six dicts, `fuel_trajectories.py` three dicts, `interchange/registry.py::INTERCHANGE_INJECTIONS["SPP"]`, `interchange/spec.py::INTERFACE_NEIGHBORS["SPP"]` (no `IMPORT_ZONE`/tranches), `scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/spp.py`, `configs/data-profiles.yaml`, `docs/multi-iso/README.md` "seven" | `validate_topology()`; fleet census equals SPP-10's; `hydrate_data.py --list` shows the `spp` profile owning `SWPP*` and NOT `DAMLZHBSPP_*`; `pytest tests/unit/config tests/curation tests/unit/data -q`; `python scripts/ci_refactor_guards.py`; `check_mechanism_matrix.py` (no field added ⇒ nothing owed) | `FINDING-spp-20-<date>.md` = registry entry table (dict → value → citation) + the six-keeper byte-identity proof | **six keepers unmoved**: replay-hash MISO's keeper fleet/offer arrays (the one ISO whose code names SPP) + goldens + `test_persisted_identity` for the rest; `test_iso_config` scarcity checkpoint still `["ERCOT","NEISO"]` unless P5 ruled otherwise; **no new `ScenarioConfig` field** |
| **SPP-21** matrix shard | OPUS · mechanical shard emission + queue transcription | code | `docs/codebase-site/data/mechanism-matrix.js:1460` `isos:`; new `data/mechanism-matrix/SPP.js` (a cell for EVERY id: `U` where ISO-applicable, `·` where n/a, `keeper: ""`); `data/mechanism-matrix-assemble.js:29` `EV_KEY` `SPP:'S'`; `mechanism-matrix.html:113-118` script tag; `scripts/lib/mech_matrix.py` `ISO_ORDER` / `ISO_EV_KEY` / `ISO_FIELD_STEMS["SPP"]=("spp",)`; `docs/mechanism-testing-matrix.md` §2 similarity note + new **§5.7 SPP lever queue** (cross-cutting 5.7 → 5.8) | `python scripts/check_mechanism_matrix.py` exit 0 (shard covers exactly the base id set) | `FINDING-spp-21-<date>.md` | **ONE commit**; `pytest tests/unit/config/test_mechanism_matrix_*.py`; 7-column `file://` preview; a one-line cross-desk notice appended to the capx and SCN ledgers: "7 shards from now on — every rule-28(c) cell line includes SPP" |
| **SPP-30** outages + tranches | OPUS · frozen derives (rule 23) | spp | `data/raw/campd-unit-outages-SPP.csv` (+ `-short`, `-layup`, `-e923` siblings as emitted), `campd-partial-outages-SPP.csv`, SPP rows of the committed-pct / thermal-tranche / bin-assignment CSVs | windows > 0 in every CEMS state incl. OK/NE; zero full-year fallbacks | `FINDING-spp-30-<date>.md` (windows per state-year, units covered %) | `derive_campd_unit_outages.py --iso SPP --years 2023 2024 2025` → `derive_cc_committed_pct.py --iso SPP` → `derive_thermal_tranches.py --iso SPP` → `tag_mixed_plants.py` → `build_offer_curve_overrides.py`; every output header cites source + method |
| **SPP-31** benchmarks | OPUS · execution | spp | `scripts/data/derive_actual_lmp.py` SPP path (system + per-hub zones), `build_calibration_reference.py` (`"SPP":"SWPP"` BA map, eGRID BACODE), `_validation-source/actual_lmp.json` SPP block, `SPP_{2023,2024,2025}_renewable_capacity.csv`, `calibration_reference.json` SPP block, regenerated `frontend/data/backcast/tail/actual_tail.json` + `amplitude/actual_amplitude.json` | SWPP rows present in the shared `eia_demand_profiles.parquet` / `eia_generation_profiles.parquet` (else re-run `convert_eia930.py` and prove non-SWPP rows byte-identical) | `FINDING-spp-31-<date>.md` | other ISOs' blocks **byte-identical** in every shared JSON (json-diff = ∅); SPP `rt`/`rt_mon`/`rt_pct` present 2023–2025; `actual_tail.json` SPP counts at the P6 threshold |
| **SPP-32** zonal shares + wind shape + gas hub | OPUS · data-intake contract execution | spp | `curate_zonal_shares.py` SPP branch + `_SPP_SUBBA_ZONE_GROUPS`; the clean `zonal-shares` rows for SPP; new `scripts/data/build_spp_wind_shape.py` (clone of `build_miso_wind_shape.py`, NASA POWER `WS50M` at EIA-860 wind sites) → `data/raw/spp-wind-shape/spp_<yr>_wind_zone_shape.parquet`; `data/raw/spp_zonal_gas_hub.csv` (MISO csv pattern; EIA delivered-to-EP state series as the Panhandle / NGPL-MidCon proxy) + `data/fuel/hubs.py` wiring; `renewables.py` SPP membership in the wind-zone-shape ISO set (a membership, not a field); SPP reference curtailment rate only if SPP-12 landed a published annual rate | shares sum to 1.0 every hour; the redistribution identity holds to 1e-9 | `FINDING-spp-32-<date>.md` with a G-DRIFT hunk audit classifying every `renewables.py` / `hubs.py` hunk INERT for the six ISOs | `data-intake` skill contract (`write_clean`/`read_clean`, tmp-`CLEAN_DIR` tests); no `ScenarioConfig` field |
| **SPP-33** seam derive | OPUS · derive only | spp | `derive_neighbor_hr_by_year.py --iso SPP` outputs (MISO from `actual_lmp_hourly_zonal_MISO.parquet` West/South rows; ERCOT from its hourly parquet); SWPP interchange duration curves by DIBA; `data/raw/reference/spp_seam_*.csv` | — | `FINDING-spp-33-<date>.md` — the `hr_by_year` and measured-flow numbers **for SPP-51 to arm** | does NOT edit `spec.py`; numbers reproduce from committed inputs |
| **SPP-34** site + docs | OPUS · execution | code | `docs/codebase-site/js/iso-configs-table.js:16-30,230`, `js/viz-iso-topology.js:16,118`, `css/site.css:402-407`, `data/iso-topologies.json` (regenerate from `get_iso_config`), `forecast-runs.html:90` (add SPP; verify the page tolerates an ISO with no forecast runs), `data-completeness.html:360`, `scripts/render_data_dictionary.py:49`, `docs/codebase/08-config-reference.md`, `docs/README.md`, `index.html` "six ISOs", `docs/calibration-log/spp.md` (header, MISO's format), CHANGELOG | — | `FINDING-spp-34-<date>.md` | `accessibility-audit` skill on touched pages; `sync-docs`; **`ff_readiness_battery.GOLDEN_ISOS` NOT touched** (W6) |
| **SPP-40** first solve → first keeper | FABLE · novel-object kill-grading, determination, attestation | spp | `results/calibration/spp40_baseline_B/` (+ `hourly/` sidecars), `frontend/data/backcast/{registry,runs}/<id>.*`, `keepers/SPP.json` (new), `keepers/index.json` (+SPP), `status/SPP.js` (`build_status.py --iso SPP`), `bench/SPP/<yr>.json.gz`, `mechanism-matrix/SPP.js` keeper + gates stamp (LAST commit), `docs/calibration-log/spp.md` entry, `PRECOMMIT-spp-40-<date>.md` | `run_calibration.py --iso SPP` smoke on the screen year (fuel-mix only); fleet / offer-array census; PRECOMMIT pushed before any solve | `FINDING-spp-40-<date>.md` | `audit_keepers --check`, `check_registry_payload_parity`, `check_mechanism_matrix`, `check_bench_freshness` all 0; screen bundle DELETED before merge (29c); dashboard renders SPP with its determination; DOF ledger lists zero residual-identified parameters; `authorized_price_tuning` declares **none** (every `offer_curve_by_group` band 1.0 — rule 25) |
| **SPP-51…56** | per §4 | spp | one lever each | rule-29 screen, keeper = control | `FINDING-spp-5N-<date>.md` | one PR each; shard cell moves in the same PR (rule 28b) |
| **SPP-60** | FABLE · **capx director charters it** (P8) | spp | `program-status.json` SPP row, `ff-verdicts.json`, `GOLDEN_ISOS`, goldens | — | — | routed, never issued by this desk |

---

## 6. Fetch / upload manifest

Owner ruling at charter: *"The plan should include sessions that fetch the data."* Every row is therefore
a **fetch first**; the manual fallback fires only on a documented block.

| # | Item | Target path | Session-fetchable? | Lane | Manual fallback |
|---|---|---|---|---|---|
| 1 | CAMPD hourly CEMS OK NE NM WY, 2023–2025 (+2026 partial) | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **YES** — `fetch_campd_unit_level.py --year Y --states OK NE NM WY` (DEMO_KEY) | SPP-11 | EPA CAMPD bulk page → same files |
| 2 | SWPP sub-BA hourly demand 2023–2025 | `data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv` | **YES** — `fetch_eia930_subba_demand.py --iso SPP --years …` after `SUBBA_NAMES["SPP"]` | SPP-11 | SPP Marketplace hourly load by area (login) |
| 3 | SWPP BA-to-BA interchange 2023–2025 | `data/raw/eia-930-interchange/SWPP interchange hourly.parquet` | **YES** — `fetch_eia930_interchange.py --ba SWPP` | SPP-11 | EIA Grid Monitor CSV |
| 4 | EIA delivered-to-electric-power gas, OK KS TX NM monthly | `data/raw/gas-prices/eia_delivered_gas_<ST>_monthly_2023-2025.csv` | **YES** — EIA API v2 (project key) | SPP-11 | EIA dnav |
| 5 | Per-hub SPPNORTH / SPPSOUTH DA + RT hourly 2023–2025 | `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` | **PROBE** — portal API moved (§2.4); re-discover, then `build_spp_lmp_reference.py --per-hub` | SPP-12 | Marketplace monthly LMP files |
| 6 | SPP hourly load by area (portal `hourly-load`) | `data/raw/spp-hourly-load/` | **PROBE** | SPP-12 | Marketplace |
| 7 | SPP generation mix (portal `generation-mix-historical`; wind delivered) | `data/raw/spp-genmix/` | **PROBE** | SPP-12 | Marketplace |
| 8 | DA / RTBM binding-constraint archive (flowgates; P1 evidence + SPP-53 TTC input) | `data/raw/spp-binding-constraints/` | **PROBE** (`da-binding-constraints`, `rtbm-binding-constraints` exist as fsNames) | SPP-12 | OASIS (login) — blocked |
| 9 | DA / RTBM operating-reserve MCPs (`da-mcp`, `rtbm-mcp`) — SPP-56 input only | `data/raw/spp-or-mcp/` | **PROBE** | SPP-12 | Marketplace |
| 10 | Wind curtailment (portal or MMU State of the Market annual %) | `data/raw/spp-hsl/spp_wind_curtailment_annual.csv` | **PROBE** spp.org MMU SOM PDF | SPP-12 | owner transcribes annual % + page cite |
| 11 | N↔S transfer capability / SPS tie ratings | cited in `_spp_config` | **NO** (OASIS blocked) — transcribe from the ITP report PDF on spp.org; rule-14 reconciled estimate documented | SPP-12 → SPP-20 | owner uploads the ITP PDF |
| 12 | PRM (15 % since PY2023; winter PRM from 2026), VRL table, offer cap | `docs/multi-iso/spp-data-audit.md` values table | **PROBE** spp.org Planning Criteria / Market Protocols | SPP-12 → SPP-10 | owner uploads the two PDFs |
| 13 | SPP long-term load forecast (needs a real edition + vintage ≥ 2020 for `load_forecast/spp.py`) | `data/raw/load-forecast/spp/spp.csv` (+ source PDF) | **PROBE** spp.org | SPP-12 | owner uploads the LTLF — **a W2 PRECONDITION** |
| 14 | Confirmed retirements (SPP-area instruments), NRC licence (Wolf Creek, Cooper), ITP transmission projects | per registry `data/raw/…` | NRC **YES** (shared); ITP **NO** | SPP-11 / SPP-12 | owner uploads the ITP project list |
| 15 | Holdout years 2019–2022 of items 1–5 | same paths | YES, **only as a rule-22 intake batch** after a `complete` marker — W5+ | — | — |

---

## 7. Hard gates — how this goes wrong

| # | Failure | Wave | Mitigation |
|---|---|---|---|
| G1 | Pin flips half-way: `_ISO_BUILDERS` without `DEMAND_LOADERS` (import-time assert) or the reverse; six-set test; "SPP" unknown-ISO fixture; stale `ci_refactor_guards` entry | W2 | ONE PR; the §2.3 atomicity list is the SPP-20 charter's checklist |
| G2 | Matrix atomicity: base `isos` + shard + `EV_KEY` + html tag + `mech_matrix.py` must land together; a shard missing an id hard-errors; every later lane must emit 7 cell lines | W2, forever | SPP-21 single commit; cross-desk notice; every W3+ charter says "7 shards" |
| G3 | `data-profiles.yaml` token collision (`spp` ⊂ `DAMLZHBSPP_*`) | W2 | delimiter-bounded tokens + a unit test asserting the ERCOT zips stay ERCOT-owned and `SWPP hourly.parquet` is SPP-owned |
| G4 | Solving before outages / benchmarks / zonal shares exist (an un-scorable copperplate) | W3→W4 | SPP-40 PRECONDITIONS: `git log origin/main --grep=SPP-3[012]` all landed |
| G5 | C6: `authorized_price_tuning` must be declared even as NONE; DOF ledger must exist; any band ≠ 1.0 in SPP's generic fallback breaks rule 25 | W4 | charter states it |
| G6 | C3c needs `TAIL_THRESHOLD["SPP"]` in three files and a regenerated `actual_tail.json` | W2 + W3 | three edits in SPP-20; SPP-31 regenerates |
| G7 | `test_iso_coverage` sweeps: `QUEUE_CAP_PER_TECH_GW["SPP"]`, carbon-`None` path, and "if `IMPORT_TRANCHES["SPP"]` then `IMPORT_ZONE["SPP"]`" | W2 | no import node ⇒ neither key ⇒ `build_import_generators("SPP") == []` (the ERCOT/MISO branch) |
| G8 | **Six keepers' cache keys move** (a new `ScenarioConfig` field, a default flip, a `results/cache.py` edit) | W2, W3-32 | forbidden through W4; wind shape via set membership not a field; byte-identity proof is SPP-20's exit; G-DRIFT audit in SPP-32 |
| G9 | Shared regenerated files (`actual_tail.json`, `actual_amplitude.json`, `eia_demand_profiles.parquet`) alter other ISOs' rows | W3-31 | non-SPP diff = ∅ as an exit check; last commit after rebase |
| G10 | Neighbour-name collision in `_HR_GAS_ELASTIC` | W2 | names `MISO` / `ERCOT` + uniqueness assert |
| G11 | `run_isos_concurrent.py` KeyError; `calibration-solve.yml` dropdown lacks SPP | W2 | in SPP-20 |
| G12 | `load_forecast/spp.py` cannot register without a real edition/vintage (`test_specs_declare_an_edition_and_a_vintage`) | W1→W2 | manifest row 13 is a W2 PRECONDITION |
| G13 | Screen bundle left in `results/calibration/` → parity gate RED (29c) | W4 | "delete before merge" line |
| G14 | Live writers on the same dicts (capx D-lanes on `capacity_market.py`; SCN on `constants.py` load dicts; miso-230 on `interchange/spec.py`) | W2 | append-last + rebase-last; desk collision check at issuance (ledger §4) |
| G15 | Desk grades a lane LOST on absence; reads green CI as proof (the matrix guard is not merge-blocking) | desk | handoff §0 |
| G16 | SPP appears on the forecast board before W6, or anyone but the capx director writes it | W2+ | MUST-NOT-TOUCH line in every charter |
| G17 | CI sparse checkout (`ci.yml:467-534`) lacks an SPP raw path a unit test reads | W3 | tests use tmp-`CLEAN_DIR` fixtures; a raw path needed ⇒ same PR, Opus/Fable (workflow edit) |
| G18 | portal.spp.org API drift (measured 2026-09-06: listings `[]`, downloads 404) | W1 | SPP-12 re-discovers from page JS; records the working form in the builder's docstring; fallback = manual rows |

---

## 8. Prompt pack

House style (scenario plan §7, desk §5). Every prompt implicitly begins: *Read `CLAUDE.md` freshly and in
full (rules 1, 13, 21, 22, 29, 30 were amended 2026-09-05/06); `docs/multi-iso/05-backcast-playbook.md`;
this plan (§1–§3, §7 and your §5 row are your charter); the mechanism matrix
(`docs/mechanism-testing-matrix.md` + every shard you touch). Fresh branch off latest `origin/main`; rebase
before pushing; zero solves until your PRECOMMIT is pushed (where you solve at all).* And ends: *Push by pack
size (CLAUDE.md "Git & Pushing"; HTTP/1.1 retry on 408/500); fetch-back verify every pushed file ≥ 300 lines
(rule 27); no CI workflows (private repo, billed minutes); no `ScenarioConfig` default moves; no
holdout-year solve (rule 22); never touch `frontend/data/forecast/`, any other ISO's keeper shard, log or
matrix shard; if you must touch a file outside your regions, STOP and route to SPP-DESK in your FINDING.
Findings to `docs/handoffs/FINDING-spp-<id>-<date>.md`; update this plan's §5 row status and the ledger
pointer in the same PR.* Model labels: `[FABLE]` / `[OPUS]`.

### W1 — Phase 0/1 (issuable now; the three lanes are parallel)

#### SPP-10 `[OPUS]` — data audit + registry-values table + doc 00 correction

```
You are lane SPP-10. MODEL: Opus claude-opus-5 — a census against a defined recipe (the MISO data
audit); you RECOMMEND, you never decide topology or edit src/. DATA PROFILE: shared.
Branch stem: claude/spp-10-audit-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/05-backcast-playbook.md §1 (Phase 0) and §8;
docs/multi-iso/spp-addition-plan-2026-09.md (§1–§3, §5 row SPP-10, §6, §7);
docs/multi-iso/miso-data-audit.md (YOUR TEMPLATE — status table columns item/source/status
got|blocked|partial/file path/notes, then one section per item, then the copy-paste manual manifest);
docs/multi-iso/00-iso-addition-protocol.md §0–§3; docs/multi-iso/01-, 02-, 04- SPP sections.

PRECONDITIONS: none (W1 is additive). SPP-11 and SPP-12 run in parallel — you consume nothing from
them; where you need a number they will fetch, write "pending SPP-11/12" rather than a guess.

FILES YOU OWN: docs/multi-iso/spp-data-audit.md (NEW); docs/multi-iso/00-iso-addition-protocol.md
(§0 SPP row + §3 SPP text ONLY); docs/multi-iso/01-data-needs-and-upload-manifest.md (SPP rows ONLY).
FILES YOU MUST NOT TOUCH: anything under src/, scripts/, configs/, tests/, frontend/, data/;
docs/multi-iso/05-backcast-playbook.md; any other ISO's audit.

TASK — write docs/multi-iso/spp-data-audit.md:
(1) FLEET CENSUS off the committed EIA-860 parquet (data/raw/eia-860/, BA code SWPP — do NOT call
    get_iso_config("SPP"), it does not exist yet): plant count and MW by fuel/prime mover vs SPP's
    published fleet totals (cite the SPP source and its page); distinct plant STATES with MW; diff the
    states against data/raw/campd-unit-level/<ST>_<yr>.parquet present (2023–2025) → the missing
    <ST>_<yr> list, expected {OK, NE, NM, WY} × 3 — confirm or correct.
(2) EIA-930: data/raw/eia-930-hourly/"SWPP hourly.parquet" span, columns, per-year demand TWh,
    per-fuel NG TWh, interchange sign convention, BAT column presence; SWPP_fueltype/region.parquet.
(3) PRICE: actual_lmp_hourly_SPP.parquet 3×8760 check; note it is the N/S hub MEAN (no zonal
    series yet — SPP-12's job); note actual_lmp.json has NO SPP block (SPP-31's job).
(4) THE REGISTRY-VALUES TABLE — one row per value SPP-20 will need, each with a primary citation
    (URL + page/table) or "pending SPP-12 PDF": planning reserve margin (SPP Planning Criteria; 15 %
    since PY2023, winter PRM from 2026 — verify), VOLL/offer cap (FERC 831 $2,000 — SPP Market
    Protocols), VRL steps (Market Protocols reserve demand curves), state→zone map candidate
    (ND SD NE MN MT IA KS MO WY | OK TX NM AR LA; name any straddling state and the sub-BA that
    resolves it), EIA-930 sub-BA→zone grouping candidate (the ~17 SWPP sub-BAs), load-share
    fallback from sub-BA annual energy (pending SPP-11), gas basis proxy (Panhandle Eastern / NGPL
    MidCon; EIA state delivered-to-EP series as the proxy), coal price base (PRB delivered, EIA-923),
    nuclear monthly CF candidates (Wolf Creek, Cooper — EIA-923), queue caps by tech (SPP GI queue
    public reports), state RPS floors in the footprint (KS/MO/NM/etc. — cite DSIRE/statute), LTLF
    edition + vintage (pending SPP-12), eGRID vintage, TRANSMISSION_BASE_STATIC_VINTAGE candidate.
    NEVER invent a number: a cell is a cited value or "pending".
(5) ZONE RECOMMENDATION (recommend, do not decide): 2 zones N/S vs 3 zones with the SPS/Texas-
    Panhandle pocket — what the data you can see supports, what P1 evidence SPP-11/12 must supply,
    and the FIPS/sub-BA mechanics of each option. The desk serves card P1 from this.
(6) MANUAL MANIFEST: copy-paste block of every item you could not source, with exact URLs.
Then CORRECT docs/multi-iso/00-iso-addition-protocol.md: the §0 SPP row must say "not registered —
see spp-addition-plan-2026-09.md"; §3's "All seven ISOs are registered" sentence must be fixed. Add
the SPP rows to doc 01 where they are missing or stale.

RULES THAT BITE: 13 [R-MEASURED] (every value must be a reproducible physical/market input),
14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (you derive nothing), 27 [R-PUSH] (docs are text — push_files
or git push, fetch-back verify the audit if ≥ 300 lines), 28 (you test no mechanism; no cell moves).
EXIT: the audit doc, the two corrections, docs/handoffs/FINDING-spp-10-<date>.md (may be a pointer
to the audit's §status table), plan §5 row status → LANDED. Report to the owner with the census
table and the missing-CEMS list first.
```

#### SPP-11 `[OPUS]` — EPA CAMPD + EIA fetches (the critical-path lane)

```
You are lane SPP-11. MODEL: Opus claude-opus-5 — reproducible fetches through existing scripts; no
design choices. DATA PROFILE: shared.  Branch stem: claude/spp-11-fetch-epa-eia-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md (§2.4, §2.5, §5 row
SPP-11, §6 rows 1–4, 14); docs/multi-iso/miso-data-audit.md Item 1 (the CAMPD DEMO_KEY procedure that
worked for LA_2023) and Item 2 (the sub-BA route); scripts/data/fetch_campd_unit_level.py,
fetch_eia930_subba_demand.py, fetch_eia930_interchange.py docstrings; data/raw/campd-unit-level/README.md
and SHA256SUMS.txt conventions; data/raw/zone-specific-demand/MISO/SOURCES.md (your SOURCES template).

PRECONDITIONS: none. SPP-10 and SPP-12 are parallel; you own no file they own.
FILES YOU OWN: data/raw/campd-unit-level/{OK,NE,NM,WY}_{2023,2024,2025,2026}.parquet (+ README/SHA256SUMS
rows); data/raw/zone-specific-demand/SPP/ (NEW dir: spp_subba_demand_2023-2025.csv + SOURCES.md);
data/raw/eia-930-interchange/"SWPP interchange hourly.parquet" (+ README row);
data/raw/gas-prices/eia_delivered_gas_{OK,KS,TX,NM}_monthly_2023-2025.csv + SOURCES_spp_gas.md;
scripts/data/fetch_eia930_subba_demand.py (ADD SUBBA_NAMES["SPP"] ONLY — the MISO block is untouched);
scripts/data/fetch_eia930_interchange.py ONLY if it is not already BA-parametrised (it takes --ba).
FILES YOU MUST NOT TOUCH: any existing raw file (data/raw is immutable); src/; configs/; tests/;
docs/multi-iso/spp-data-audit.md (SPP-10's).

TASK, in this order, each its own small commit:
(1) CEMS: for Y in 2023 2024 2025: python scripts/data/fetch_campd_unit_level.py --year Y
    --states OK NE NM WY (DEMO_KEY header as in the MISO Item-1 procedure; a real EPA key if the
    environment carries one). Then 2026 partial. Verify arrow schema == a sibling (e.g. KS_2024) —
    the fetcher asserts it; record rows / facilities / units per file. Update README + SHA256SUMS.
(2) SUB-BA DEMAND: add SUBBA_NAMES["SPP"] = the SWPP sub-BA code→display-name map for the
    2023–2025 file vintage (read the names off the Grid Monitor file header — never guess; EIA
    renamed sub-BAs in 2026, see the module docstring). Run --iso SPP --years 2023 2024 2025 (dry-run
    first). Write SOURCES.md with the file URLs, vintage, timezone convention, row counts, and the
    sub-BA list with annual energy TWh per sub-BA (this is P1 evidence — put the table in your FINDING).
(3) INTERCHANGE: fetch_eia930_interchange.py --ba SWPP for 2023–2025 → the DIBA series
    (MISO, ERCO, and every other counterparty). In the FINDING: net-interchange duration curve
    summary per DIBA per year (sign convention stated) — P2/P3 evidence.
(4) GAS: EIA API v2 monthly delivered-to-electric-power gas price for OK KS TX NM, 2023–2025
    (the MISO citygate-proxy pattern, data/raw/gas-prices/SOURCES_miso_citygate.md).
Anything that returns 403/404: record the exact URL + status in the FINDING's blocked table and STOP
that item — no transcription from memory, no secondary-source values.
RULES THAT BITE: 13 [R-MEASURED], 14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (fetch, do not derive),
26, 27 [R-PUSH] (the parquets are binary — git push by pack size; if a single commit's pack exceeds
what the remote takes, split by state-year; never push_files a parquet), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-11-<date>.md with the got/blocked table, per-file row counts and
schema checks, the sub-BA energy table, and the DIBA duration summaries; plan §5 row → LANDED.
Report to the owner: which of {OK, NE, NM, WY} × {2023, 2024, 2025} landed, first.
```

#### SPP-12 `[OPUS]` — portal.spp.org + spp.org: API re-discovery, per-hub LMP, market products, planning PDFs

```
You are lane SPP-12. MODEL: Opus claude-opus-5 — fetch + transcription against a manifest; the ONE
judgment you exercise is re-discovering a moved API, and you record the working form rather than
choosing anything. DATA PROFILE: shared.  Branch stem: claude/spp-12-fetch-portal-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md (§2.4 — the 2026-09-06
probe: portal.spp.org file-browser listings return [] and the builder's download paths 404; §5 row
SPP-12; §6 rows 5–13); scripts/data/build_spp_lmp_reference.py IN FULL (its docstring documents the
API form that worked and the range-fetch-inside-zip trick for archived years);
docs/multi-iso/data-acquisition-report.md §SPP.

PRECONDITIONS: none. Parallel with SPP-10/11; you own no file they own.
FILES YOU OWN: scripts/data/build_spp_lmp_reference.py (a --per-hub flag + the repaired API form in the
docstring; the default single-hub output must stay byte-identical for 2023–2025 — prove it);
data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet (NEW: year/hour/zone/rt/da for
SPPNORTH_HUB and SPPSOUTH_HUB); NEW dirs each with README.md + SOURCES.md:
data/raw/spp-hourly-load/, spp-genmix/, spp-binding-constraints/, spp-or-mcp/, spp-hsl/,
spp-planning/ (PDFs or page-cited transcriptions: ITP report, Planning Criteria PRM, Market Protocols
VRL + offer cap, LTLF, MMU State of the Market). FILES YOU MUST NOT TOUCH: actual_lmp_hourly_SPP.parquet
(re-generate ONLY to prove byte-identity, then discard the copy); src/; configs/; tests/;
docs/multi-iso/spp-data-audit.md.

TASK:
(0) API RE-DISCOVERY (zero data): open https://portal.spp.org/pages/rtbm-lmp-by-location and
    /pages/hourly-load; read the page JS for the current file-browser endpoint form (fsName, path
    encoding, headers such as Referer/Origin, any token). Confirm with ONE listing that returns
    entries and ONE range-fetch of a small monthly file. Record the working form in the builder's
    docstring with the date. If the portal now REQUIRES a Marketplace login, STOP the portal items,
    write the manual-manifest rows with exact URLs, and continue with (4).
(1) PER-HUB LMP: --per-hub → actual_lmp_hourly_zonal_SPP.parquet, same 8760 local-clock calendar
    as derive_actual_lmp.py. In the FINDING: mean and p90 |SPPNORTH − SPPSOUTH| per year, and the
    sign (which hub is higher, by season) — THIS IS THE P1 AND P7 EVIDENCE.
(2) PORTAL PRODUCTS, 2023–2025: hourly-load (by area), generation-mix-historical (wind delivered
    is the HSL denominator), da-binding-constraints + rtbm-binding-constraints (monthly), da-mcp +
    rtbm-mcp (reserve clearing prices). Raw files land under their dirs untouched; a README states
    schema, span, timezone; SOURCES the URLs. From the binding-constraint archive compute, in the
    FINDING only: share of RT binding hours by flowgate GROUP — N↔S corridor flowgates vs SPS-tie
    flowgates vs other — per year. That number decides card P1.
(3) CURTAILMENT: any portal curtailment/HSL product; else the MMU State of the Market annual wind
    curtailment % (spp.org PDF) transcribed with page cite → spp-hsl/spp_wind_curtailment_annual.csv.
(4) PLANNING PDFs from spp.org: ITP report (N↔S transfer capability, SPS tie ratings — transcribe the
    table with page numbers), Planning Criteria (PRM by planning year), Market Protocols (VRL steps,
    offer cap), LTLF (edition, vintage, the peak/energy table → data/raw/load-forecast/spp/spp.csv in
    the shape of load-forecast/miso/miso.csv; this is a W2 PRECONDITION), MMU SOM.
Every blocked URL → the blocked table with status code. No value from memory.
RULES THAT BITE: 13, 14, 23, 26, 27 [R-PUSH] (build_spp_lmp_reference.py is ≥ 300 lines — Edit tool,
exact bytes, fetch-back verify), 28 (no cell moves). Binary files by git push, pack-sized commits.
EXIT: docs/handoffs/FINDING-spp-12-<date>.md with the reachable/blocked table, the working API form,
the hub-spread table, the binding-share table, and the manual manifest rows that remain; plan §5 row →
LANDED. Report to the owner: hub spread by year and the binding share first — the desk serves P1 on them.
```

### W2 — registration (issued at sitting #2 after P1–P8 are ruled; SPP-21 may go first, it is disjoint)

#### SPP-20 `[FABLE]` — register SPP: topology + every registry + the pin flip (ONE PR)

```
You are lane SPP-20. MODEL: Fable claude-fable-5-1 — topology and market-object design choices,
the six-ISO pin flip, and rule-27 core scope (iso_configs.py, constants.py, capacity_market.py,
demand.py, spec.py are all ≥ 300-line core files: Edit tool, exact bytes, fetch-back verify every
push). DATA PROFILE: shared at start; hydrate spp once your data-profiles.yaml commit exists.
Branch stem: claude/spp-20-register-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md (§2.3 THE ATOMICITY
LIST — it is your checklist; §3 rulings P1–P8 as recorded in the ledger §2 — they BIND you; §5 row
SPP-20; §7 G1–G3, G6–G8, G10–G12); docs/multi-iso/spp-data-audit.md (the registry-values table —
every value you enter carries its citation from there); FINDING-spp-11 and FINDING-spp-12;
docs/multi-iso/00-iso-addition-protocol.md Stages A–C; iso_configs.py _miso_config() and _neiso_config()
(templates); data/eia930/demand.py _load_miso_hourly_demand (template); scripts/lib/load_forecast/miso.py
+ scripts/lib/datatype_registry.py; the SPP shard docs/codebase-site/data/mechanism-matrix/SPP.js if
SPP-21 has landed (cite it; do not edit it).

PRECONDITIONS (verify with git log origin/main --grep=SPP-1; STOP if unmet): SPP-10, SPP-11, SPP-12
LANDED; ledger §2 carries rulings P1–P8; data/raw/load-forecast/spp/spp.csv exists with a real edition
and vintage (G12). Read the ledger §4 collision register: if a capx lane holds capacity_market.py or a
SCN lane holds the constants.py load dicts mid-PR, HOLD and say so.

FILES YOU OWN (the §2.3 list, in full): iso_configs.py (_spp_config + _ISO_BUILDERS), zone_assignment.py,
campd.py::ISO_STATES, eia930/frames.py, eia930/demand.py, renewables.py::RENEWABLE_ZONE_ALLOCATION,
transmission_expansion.py, fleet/models.py::BA_CODE_TO_ISO, capacity_market.py (the eight all-six dicts),
constants.py (the all-six dicts), fuel_trajectories.py (three dicts), interchange/registry.py +
interchange/spec.py (new "SPP" blocks ONLY — the MISO-side SPP seam is untouchable),
scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/spp.py,
configs/data-profiles.yaml, scripts/calibration_verdict.py (PINNED_CLASSES_BY_ISO, TAIL_THRESHOLD),
scripts/data/derive_actual_tail.py, derive_actual_amplitude.py, scripts/audit_keepers.py
(_MULTI_YEAR_ISOS), scripts/run_isos_concurrent.py, .github/workflows/calibration-solve.yml (the
dropdown line only), scripts/ci_refactor_guards.py (DELETE the spp.py allowlist entry — cite Y-21),
tests/curation/test_curate_load_forecast.py (7-set; unknown-ISO fixture → "TVA"), the ~22 six-tuple tests
(extend or document as deliberate exclusion), tests/unit/config/test_iso_config.py (a NEW SPP topology
case; the scarcity checkpoint untouched unless P5 ruled to seed), docs/multi-iso/README.md ("seven").
FILES YOU MUST NOT TOUCH: results/cache.py; ScenarioConfig (NO NEW FIELD — rule 24 is satisfied by
registries, and a field moves every keeper's cache key, G8); any keeper shard; frontend/; the matrix
shards (SPP-21's; your PR adds no ScenarioConfig field so rule 28(c) owes nothing — say so in the
FINDING); MISO's SPP seam constants; the forecast board.

BUILD, exactly as the rulings say:
- _spp_config(): the P1-ruled zones with cited load shares (fallback from SPP-11's sub-BA energy
  table), the N↔S TransferLink at the ITP-transcribed capability (rule 14: cite the misalignment if
  the ITP number is a path, not our link), voll=2000.0 (FERC 831), default_scenario_overrides per P5
  (expected: none). No import node: IMPORT_ZONE/IMPORT_TRANCHES/EXPORT_TRANCHES carry no SPP key
  (G7); INTERFACE_NEIGHBORS["SPP"] = the P2/P3 NeighborInterface("MISO") + ("ERCOT") blocks with the
  measured hourly-LMP anchors named, DEFAULT-OFF via reference_price_interface (REFERENCE_PRICE_DEFAULT_ISOS
  untouched); INTERCHANGE_INJECTIONS["SPP"] = (apply_reference_price_seam_injections,) which self-gates.
  _SCALAR_INTERCHANGE_ISOS += "SPP" per P2 (served measured EIA-930 Total interchange).
- zone_assignment: _ISO_TO_BA_CODE["SPP"]="SWPP", _LARGEST_ZONE, _EGRID_VINTAGE, _SPP_STATE_ZONES
  (FIPS state → zone per P1) + _spp_zone(); every SWPP plant resolves to a real zone, none dropped
  (test). campd.ISO_STATES["SPP"] = the audit's state list.
- Every all-six dict gains SPP as its LAST entry with a citation comment (rule 5); MARKET_DESIGN
  deliberately ABSENT (energy-only fallback = SPP's RA-obligation reality — document in a comment);
  capacity-market-only registries deliberately absent with the exclusion stated in their README.
- data-profiles.yaml: isos.SPP.tokens = [swpp, "_spp.", "-spp.", "/spp/"] + profiles.spp; a unit test
  that DAMLZHBSPP_2023.zip stays ERCOT-owned and "SWPP hourly.parquet" is SPP-owned (G3).
- TAIL_THRESHOLD["SPP"] = the P6 value in all three files; _MULTI_YEAR_ISOS += SPP; memory class
  IsoMemoryClass("SPP", peak_gb=<state your estimate and mark it measured-in-SPP-40>, per_plant=True,
  co_opt=False).
- Neighbour-name uniqueness assert in neighbor_price.py (G10). No hour loops anywhere (rule 2).
PROOF BEFORE PUSH: get_iso_config("SPP").validate_topology(); the fleet census equals SPP-10's;
python scripts/hydrate_data.py --list; pytest tests/unit/config tests/curation tests/unit/data -q;
python scripts/ci_refactor_guards.py; python scripts/check_mechanism_matrix.py --base origin/main;
tests/regression/test_persisted_identity.py 14/14; AND the six-keeper byte-identity proof: for MISO
(the one ISO whose code names SPP) reproduce the keeper's fleet_only/offer-array hashes on your
branch vs origin/main; for the other five, the pinned config keys + goldens. Put the table in the
FINDING. ONE PR, commits in dependency order, every dict key appended LAST after a final rebase.
RULES THAT BITE: 1, 5, 19, 24, 25 [R-ISO-SCOPE] (every SPP band multiplier 1.0; nothing copied from
another ISO's fitted values), 26, 27, 28 (no cell moves; state that no field was added), 30.
EXIT: docs/handoffs/FINDING-spp-20-<date>.md = the registry entry table (dict → value → citation),
the byte-identity table, the deliberate-exclusion list, the test census; plan §5 row → LANDED.
Report to the owner: "SPP is registered; six keepers unmoved (table)" first.
```

#### SPP-21 `[OPUS]` — the seventh mechanism-matrix shard + §5.7 SPP lever queue (ONE commit)

```
You are lane SPP-21. MODEL: Opus claude-opus-5 — mechanical shard emission and queue transcription
from this plan; no verdict is minted (every cell is U or ·). DATA PROFILE: code.
Branch stem: claude/spp-21-matrix-shard-<4 chars>.
Read CLAUDE.md freshly and in full (rule 28 [R-MECH-MATRIX] in particular);
docs/multi-iso/spp-addition-plan-2026-09.md §4 (W5 queue), §5 row SPP-21, §7 G2;
docs/mechanism-testing-matrix.md §1 (the binding protocol), §2, §5 (every ISO's queue — §5.6 NEISO
is your format template); docs/codebase-site/data/mechanism-matrix.js (base rows + the isos: list
at ~L1460); one existing shard in full (MISO.js); data/mechanism-matrix-assemble.js;
scripts/lib/mech_matrix.py; scripts/check_mechanism_matrix.py;
tests/unit/config/test_mechanism_matrix_shard_migration.py and test_mechanism_matrix_keeper_stamp.py.

PRECONDITIONS: none — this lane is disjoint from SPP-20 and may land before it (the matrix guard reads
the base file's isos list, not _ISO_BUILDERS). Check ledger §4: the shards are written by several
lanes a day — rebase immediately before your single commit.
FILES YOU OWN: docs/codebase-site/data/mechanism-matrix.js (the isos: list ONLY); NEW
docs/codebase-site/data/mechanism-matrix/SPP.js; data/mechanism-matrix-assemble.js (EV_KEY: SPP:'S');
docs/codebase-site/mechanism-matrix.html (the SPP.js script tag beside the six); scripts/lib/mech_matrix.py
(ISO_ORDER, ISO_EV_KEY["SPP"]="S", ISO_FIELD_STEMS["SPP"]=("spp",)); docs/mechanism-testing-matrix.md
(§2 one paragraph on where SPP sits in the similarity analysis — closest to ERCOT/MISO; NEW §5.7 SPP
with the W5 queue SPP-51…56 exactly as the plan's §4 states them, each with its gate and its
pre-declared promotion condition; renumber the cross-cutting section 5.7 → 5.8 and fix its
in-document references); a one-line notice appended to docs/handoffs/capx-director-ledger-2026-08.md
§0 top entry and docs/handoffs/scenario-desk-ledger-2026-09.md §0 top entry: "SPP shard exists from
<sha> — seven shards; every rule-28(c) cell line now includes SPP".
FILES YOU MUST NOT TOUCH: any other ISO's shard cell values; any base-row text; src/; tests/ (if
test_mechanism_matrix_shard_migration needs a 7-ISO expectation, that is one assertion line — say so).

BUILD: generate SPP.js from the base id set with a small script (commit the script under
scripts/probes/ ONLY if the repo's probes policy admits it; otherwise inline it in the FINDING):
every mechanism id gets a cell — U where the mechanism is applicable to an ISO with SPP's design
(energy-only, RA obligation, no capacity market, no carbon program, reserves co-opt not yet armed),
· where n/a (capacity-market clearing, RGGI/CA cap-and-trade, ISO-specific bridges), with the
evidence field citing this plan §3/§4; keeper: "" and gates: "" (no keeper). Cell ORDER must match
the base isos list (the CI guard asserts it). Then python scripts/check_mechanism_matrix.py must
exit 0 and the pytest matrix tests pass; open mechanism-matrix.html via file:// and confirm seven
columns. ONE COMMIT for all of it (G2).
RULES THAT BITE: 25 (a verdict in one ISO never fills another — hence U everywhere), 26, 27
(mechanism-matrix.js and the .md are ≥ 300 lines — Edit tool, fetch-back verify), 28(b)/(c).
EXIT: docs/handoffs/FINDING-spp-21-<date>.md (cell census: n_U, n_na, by mechanism family), plan §5
row → LANDED. Report to the owner: guard exit code + cell census.
```

### W3 — derivation (issued the sitting after SPP-20 merges; the four spp lanes are parallel; SPP-34 too)

#### SPP-30 `[OPUS]` — unit outage windows + committed % + thermal tranches (frozen derives)

```
You are lane SPP-30. MODEL: Opus claude-opus-5 — frozen derives on a committed recipe (rule 23).
DATA PROFILE: spp.  Branch stem: claude/spp-30-outages-tranches-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md §5 row SPP-30, §7 G4;
docs/multi-iso/05-backcast-playbook.md §0 items 2 and 4, §3 (the dependency order); the docstrings
of scripts/data/derive_campd_unit_outages.py, derive_cc_committed_pct.py, derive_thermal_tranches.py,
scripts/tag_mixed_plants.py (under scripts/, not scripts/data/), build_offer_curve_overrides.py; docs/binning-methodology.md; data/raw/
campd-unit-outages-MISO.csv header (your output template); FINDING-spp-11 (which CEMS state-years landed).

PRECONDITIONS (git log origin/main --grep=SPP-20 and --grep=SPP-11; STOP if unmet): SPP-20 LANDED
(get_iso_config("SPP") works); OK and NE CEMS 2023–2025 present.
FILES YOU OWN: data/raw/campd-unit-outages-SPP.csv (+ -short/-layup/-e923 siblings exactly as the
derive emits them), data/raw/campd-partial-outages-SPP.csv, the SPP rows of the committed-pct /
thermal-tranche / bin-assignment outputs (data/raw/reference/custom-bin-assignments.csv rows for SWPP
plants — append, never reorder). FILES YOU MUST NOT TOUCH: any other ISO's rows; src/; the derive
scripts themselves (if one needs an SPP branch, that is a src-adjacent change — STOP and route);
ScenarioConfig.
RUN, in this order, each its own commit: derive_campd_unit_outages.py --iso SPP --years 2023 2024
2025 → derive_cc_committed_pct.py --iso SPP → derive_thermal_tranches.py --iso SPP →
scripts/tag_mixed_plants.py → build_offer_curve_overrides.py. GATES: window count > 0 in every CEMS state
incl. OK and NE; ZERO full-year fallbacks (a unit falling to the fallback is reported by unit with
the reason); the committed-% and tranche distributions summarised by class vs MISO's as a sanity
band (report, never tune). Every output header cites source + method + the CEMS vintage.
RULES THAT BITE: 13, 14, 23 [R-FROZEN-DERIVE] (nothing re-derives against a residual — there is no
residual yet), 27 (CSV outputs by git push; SHA/row counts in the FINDING), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-30-<date>.md (windows per state-year, units covered %, fallback list,
class summaries); plan §5 row → LANDED. Report to the owner: coverage % by state first.
```

#### SPP-31 `[OPUS]` — the scoring benchmarks (actual_lmp.json, calibration_reference.json, tail, amplitude)

```
You are lane SPP-31. MODEL: Opus claude-opus-5 — execution on committed inputs. DATA PROFILE: spp.
Branch stem: claude/spp-31-benchmarks-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md §5 row SPP-31, §7
G6, G9; scripts/data/derive_actual_lmp.py (add the SPP path — read how MISO's zonal variant is wired),
build_calibration_reference.py, derive_actual_tail.py, derive_actual_amplitude.py, scripts/audit_eia923_completeness.py;
docs/calibration-determination-rubric.md (what C1–C4 read); FINDING-spp-12 (the per-hub parquet).

PRECONDITIONS: SPP-20 LANDED (TAIL_THRESHOLD["SPP"] exists in all three files); SPP-12 LANDED
(actual_lmp_hourly_zonal_SPP.parquet). STOP if either is missing.
FILES YOU OWN: scripts/data/derive_actual_lmp.py (SPP path), scripts/data/build_calibration_reference.py
(SPP in its ISO map, BA "SWPP", eGRID BACODE), data/raw/_validation-source/actual_lmp.json (the SPP
block ONLY), data/raw/_validation-source/SPP_{2023,2024,2025}_renewable_capacity.csv,
calibration_reference.json (SPP block ONLY), frontend/data/backcast/tail/actual_tail.json and
amplitude/actual_amplitude.json (REGENERATED — as your LAST commit after a final rebase),
frontend/data/backcast/completeness/eia923_<yr>.json (regenerated). FILES YOU MUST NOT TOUCH: any other
ISO's block or row in those files (your exit check is that their content is byte-identical); src/.
GATE (zero-LP, first): SWPP rows exist in the shared eia_demand_profiles.parquet /
eia_generation_profiles.parquet that build_calibration_reference reads; if not, re-run
convert_eia930.py and prove every non-SWPP row byte-identical before proceeding.
BUILD: derive_actual_lmp.py --iso SPP → actual_lmp.json SPP block (da, rt, da_mon, rt_mon, *_pct; and
the zonal hub entries in the shape MISO uses) → build_calibration_reference.py for SPP 2023–2025 →
derive_actual_tail.py and derive_actual_amplitude.py (regenerate; report SPP tail counts at $200 AND
$300 for the record) → scripts/audit_eia923_completeness.py.
RULES THAT BITE: 13 (benchmarks are measured outcomes used ONLY as the score, never as an input),
14, 27 (derive_actual_lmp.py is ≥ 300 lines — Edit tool, fetch-back verify), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-31-<date>.md with the SPP benchmark table (per year: load TWh,
gen by class TWh, avg RT/DA, monthly RT, tail counts, amplitude) and the json-diff proof that no
other ISO moved; plan §5 row → LANDED. Report to the owner: the benchmark table.
```

#### SPP-32 `[OPUS]` — zonal shares + per-zone wind shape + zonal gas hub (data-intake contract)

```
You are lane SPP-32. MODEL: Opus claude-opus-5 — the data-intake skill's contract executed on
committed inputs; the only new script is a clone. DATA PROFILE: spp.
Branch stem: claude/spp-32-zonal-wind-gas-<4 chars>.
Read CLAUDE.md freshly and in full; invoke the data-intake skill; docs/multi-iso/spp-addition-plan-2026-09.md
§5 row SPP-32, §7 G8, G17; docs/multi-iso/05-backcast-playbook.md §8.1, §8.3; docs/multi-iso/
miso-data-audit.md Items 2, 4, 5 (your three templates); scripts/data/curate_zonal_shares.py
(_MISO_SUBBA_ZONE_GROUPS), scripts/data/build_miso_wind_shape.py IN FULL, data/raw/miso_zonal_gas_hub.csv
+ src/market_sim/data/fuel/hubs.py (how MISO's hub csv is wired), src/market_sim/data/renewables.py
(the wind-zone-shape ISO set and _UNCURTAILED_FALLBACK_ISOS); FINDING-spp-11 (sub-BA file),
FINDING-spp-12 (curtailment rate, if any).

PRECONDITIONS: SPP-20 and SPP-11 LANDED. STOP if not.
FILES YOU OWN: scripts/data/curate_zonal_shares.py (SPP branch + _SPP_SUBBA_ZONE_GROUPS, mirroring
MISO's); the SPP rows of the clean zonal-shares datatype; NEW scripts/data/build_spp_wind_shape.py
(clone of the MISO builder: NASA POWER WS50M at EIA-860 SWPP wind sites, turbine power curve,
reconciled to the EIA-930 SWPP aggregate — level never pinned) → data/raw/spp-wind-shape/
spp_{2023,2024,2025}_wind_zone_shape.parquet + README/SOURCES; data/raw/spp_zonal_gas_hub.csv (the
EIA state delivered-to-EP series from SPP-11 as the Panhandle / NGPL-MidCon proxy, MISO's csv schema)
+ SOURCES; src/market_sim/data/fuel/hubs.py (SPP wiring — the MISO branch is your template; NO if-iso
ladder, extend the registry); src/market_sim/data/renewables.py (SPP membership in the wind-zone-shape
ISO set; SPP reference curtailment rate ONLY if SPP-12 landed a published annual rate — cite it);
tests under tests/curation and tests/unit/data for the new SPP paths (tmp-CLEAN_DIR fixtures — never
a raw path CI does not sparse-checkout, G17).
FILES YOU MUST NOT TOUCH: ScenarioConfig (no field; G8); results/cache.py; any other ISO's rows or
branches in the files above.
GATES: zonal shares sum to 1.0 every hour; the redistribution identity holds to 1e-9; wind shapes
reconcile to the 930 aggregate within the builder's documented tolerance; the hub csv has 36 rows
per zone-month set. G-DRIFT: in the FINDING, classify EVERY hunk you add to renewables.py and hubs.py
as INERT for each of the six ISOs, with the reason (SPP-keyed branch / registry entry), and re-run
tests/regression/test_persisted_identity.py.
RULES THAT BITE: 2 (no hour loops — numpy over the parquet), 5, 13, 14, 23, 24 [R-REGISTRY], 27
(renewables.py and hubs.py are core files ≥ 300 lines — Edit tool, fetch-back verify), 28 (no cell
moves — you arm no mechanism; the wind-shape membership is an input, not a lever).
EXIT: docs/handoffs/FINDING-spp-32-<date>.md (share table by zone-year, wind-shape reconciliation
stats, hub csv provenance, the G-DRIFT table); plan §5 row → LANDED.
```

#### SPP-33 `[OPUS]` — seam numbers for SPP-51 (derive only, no arming)

```
You are lane SPP-33. MODEL: Opus claude-opus-5 — derive only; you arm nothing. DATA PROFILE: spp.
Branch stem: claude/spp-33-seam-derive-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md §3 P2/P3 (as ruled),
§5 row SPP-33; scripts/data/derive_neighbor_hr_by_year.py and derive_neighbor_hr_elasticity.py;
src/market_sim/model/interchange/spec.py INTERFACE_NEIGHBORS["SPP"] (as SPP-20 registered it —
default-off); FINDING-spp-11 (the SWPP DIBA interchange series).
PRECONDITIONS: SPP-20 and SPP-11 LANDED.
FILES YOU OWN: the derive outputs for --iso SPP (MISO anchored to actual_lmp_hourly_zonal_MISO.parquet
MISO-West/South rows; ERCOT to actual_lmp_hourly_ERCOT.parquet), data/raw/reference/spp_seam_*.csv
(hr_by_year, elasticity, DIBA duration-curve summaries) + SOURCES. FILES YOU MUST NOT TOUCH:
interchange/spec.py (SPP-51 arms the numbers you derive); MISO's SPP seam; ScenarioConfig.
RUN: derive_neighbor_hr_by_year.py --iso SPP --years 2023 2024 2025; the elasticity derive; the
SWPP net-interchange duration curves per DIBA per year with the sign convention stated.
RULES THAT BITE: 13, 23, 25 (SPP's numbers from SPP's data; nothing mirrored from MISO's fitted
seam), 27, 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-33-<date>.md with the hr_by_year table and the duration summaries,
labelled "for SPP-51 to arm"; plan §5 row → LANDED.
```

#### SPP-34 `[OPUS]` — codebase-site + docs prose + calibration-log header

```
You are lane SPP-34. MODEL: Opus claude-opus-5 — execution. DATA PROFILE: code.
Branch stem: claude/spp-34-site-docs-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md §5 row SPP-34;
docs/codebase-site/js/iso-configs-table.js, viz-iso-topology.js, css/site.css (the data-iso tab rules),
data/iso-topologies.json, forecast-runs.html (ISO_ORDER at ~L90), data-completeness.html (~L360);
scripts/render_data_dictionary.py; docs/codebase/08-config-reference.md; docs/README.md; index.html;
docs/calibration-log/miso.md (header format for the new spp.md); CHANGELOG.md top entry format.
PRECONDITIONS: SPP-20 LANDED (get_iso_config("SPP") drives iso-topologies.json).
FILES YOU OWN: exactly the list in plan §5 row SPP-34. FILES YOU MUST NOT TOUCH:
scripts/ff_readiness_battery.py GOLDEN_ISOS and anything under frontend/data/forecast/ (W6, routed);
the matrix shards (SPP-21's); frontend/data/backcast/ (SPP-40's); any keeper shard.
BUILD: add SPP to every hardcoded ISO list named in the row (ISO_ORDER, ISO_COLORS/DESCRIPTIONS,
isoOrder, the .tabs__tab[data-iso="SPP"] rule using --iso-spp, the ISOS array); regenerate
iso-topologies.json from get_iso_config; prove forecast-runs.html renders with an ISO that has no
forecast runs; regenerate the data dictionary; update 08-config-reference.md's zone table and
per-ISO mechanism lists for SPP; fix every "six ISOs" phrase in docs/README.md, index.html,
data-pipeline.html; create docs/calibration-log/spp.md with the header + "Next shorthand: spp-1";
CHANGELOG entry. Run the accessibility-audit skill on every page touched; run sync-docs at the end.
RULES THAT BITE: 15 (dashboard text is generated from sidecars — do not hand-write status),
26, 27 (several ≥ 300-line files — Edit tool, fetch-back verify), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-34-<date>.md (file → change table, audit output); plan §5 row → LANDED.
```

### W4 — first solve → first keeper (issued the sitting after SPP-30/31/32 merge)

#### SPP-40 `[FABLE]` — smoke, rule-29 screen, the 2023–2025 bundle, registration, the dashboard flip

```
You are lane SPP-40. MODEL: Fable claude-fable-5-1 — the first-ever SPP solve is a novel object:
kill-grading its screen, writing its attestation and DOF ledger, and promoting the first keeper are
determination consequences. DATA PROFILE: spp.  Branch stem: claude/spp-40-first-keeper-<4 chars>.
Read CLAUDE.md freshly and in full (rules 1, 12, 13, 15, 16, 20, 21, 22, 29, 30 bind every line
below); docs/multi-iso/spp-addition-plan-2026-09.md §1, §3 P7 (as ruled), §5 row SPP-40, §7 G4, G5,
G13; docs/multi-iso/05-backcast-playbook.md §6 (the loop: smoke first, structural before knobs);
FINDING-spp-30/31/32; docs/calibration-determination-rubric.md; scripts/run_calibration.py and
run_calibration_full.py --help; the calibration-report skill; scripts/build_status.py, dashboard_add_run.py,
prune_iso_runs.py, check_registry_payload_parity.py; frontend/data/backcast/keepers/README.md
(promotion protocol) and keepers/MISO.json (shard shape); docs/calibration-log/miso.md (a recent
entry as the format); one recent PRECOMMIT-miso*.md (the PRECOMMIT form).

PRECONDITIONS (git log origin/main --grep=SPP-3; STOP if unmet): SPP-30, SPP-31, SPP-32 LANDED.
SPP-33 is NOT a precondition (seams are served, not priced, in this keeper — P2). Ask the desk whether
another per-plant solve is running before you start (rule 12: ≤ 2 concurrent per-plant LPs).

FILES YOU OWN: results/calibration/spp40_baseline_B/ (+ hourly/ sidecars), the screen bundle
(TEMPORARY — deleted before merge), frontend/data/backcast/registry/<id>.json + runs/<id>.js,
keepers/SPP.json (NEW), keepers/index.json (+ "SPP" — the one line every ISO shares; rebase last),
status/SPP.js (generated), bench/SPP/<yr>.json.gz, docs/codebase-site/data/mechanism-matrix/SPP.js
(keeper + gates stamp — LAST commit after final rebase), docs/calibration-log/spp.md (entry spp-1),
docs/handoffs/PRECOMMIT-spp-40-<date>.md and FINDING-spp-40-<date>.md.
FILES YOU MUST NOT TOUCH: any other ISO's shard/status/bench/log; frontend/data/forecast/;
calibration-complete.json (SPP holds no marker and you spend nothing); ScenarioConfig defaults;
offer_curve_by_group bands (every SPP band stays 1.0 — rule 25; this keeper declares NO authorized
price tuning).

DO, in order:
(0) ZERO-LP: run_calibration.py --iso SPP smoke (fuel-mix only) on each of 2023–2025; fleet census
    (plants, MW by class, CHP hosts removed) and offer-array census; fix structural absurdities
    (a class with no units, a zone with no load) by routing to the owning lane — never by tuning.
    Write PRECOMMIT-spp-40: the P7 screen year (largest mean |N−S| hub spread from FINDING-spp-12,
    named BEFORE any solve), the expected sign/season of N↔S link binding, expected order of
    magnitude of fuel-mix vs EIA-923, the STRUCTURAL STOP gate (link binds in the measured
    direction; no unserved energy; no negative-price absurdity; fuel classes within order of
    magnitude), wall-clock/peak-GB to be measured, and the statement "control = none; this bundle
    becomes the 29(b) control for every later SPP lane". PUSH IT before solving.
(1) SCREEN: run_calibration_full.py --iso SPP --year <screen year> --commitment --out-dir
    results/calibration/_spp40_screen. Grade against the STOP gate ONLY — it may kill, never
    promote, and never reads a residual. A kill = report and stop; the remaining years are not spent.
(2) FULL SPAN: ONE invocation --year 2023 2024 2025 --commitment (years sequential — rule 12),
    served interchange per P2, --out-dir results/calibration/spp40_baseline_B. Generate
    legitimacy_diagnostics.json and calibration_attestation.json (the DOF ledger: every free
    parameter with its identification source; expected: zero residual-identified values;
    authorized_price_tuning: none). Score with calibration_verdict.py AFTER the final rebase.
(3) REGISTER (calibration-report skill / dashboard_add_run.py): id 2026-<mm-dd>-spp-1-baseline;
    keepers/SPP.json with the keeper id and the shard fields keepers/README.md requires; keepers/
    index.json += "SPP"; build_status.py --iso SPP; bench parts; hourly sidecars committed (rule 15).
    Whatever the determination reads — CALIBRATED, CALIBRATED-WITH-CAVEATS or NOT-YET — it is the
    keeper because it is the most structurally faithful SPP run that exists, and it is reported at
    full magnitude with every failing criterion named. Stamp the SPP shard (keeper id + open gates)
    as the LAST commit. Log entry in docs/calibration-log/spp.md. DELETE the screen bundle before
    the PR (rule 29c); the PRECOMMIT/FINDING carry every number you will ever cite from it.
(4) GATES before push: audit_keepers --check, check_registry_payload_parity, check_mechanism_matrix,
    check_bench_freshness, check_golden_manifest — all exit 0; run the calibration-keeper-auditor
    agent --iso SPP.
RULES THAT BITE: 1 [R-STRUCT] (the run is a keeper for structure, never for MAE), 12, 13, 15, 16, 20
[R-FORCED-BUDGET] (report C8 by class), 21 [R-DOF], 22 (2023–2025 only), 27 (run payload ≥ 457 KB →
git push, never push_files; hash-verify the registry sidecar), 28(b) (stamp your ISO's shard only),
29(a)(b)(c), 30 (no touchpoint here).
EXIT: the registered keeper visible at backcast-runs.html#iso=SPP; FINDING-spp-40 with the
determination, the per-criterion table, the STOP-gate table, wall-clock/peak-GB, and the §5.7 lever
queue re-ordered by what this bundle showed (a recommendation to the desk, not a change); plan §5
row → LANDED; plan §1 rows 2–4 ticked. Report to the owner: determination + criterion table first.
```

### W5 — reserved charters (NOT dispatchable until SPP-40 lands; the desk writes each in full when it is)

| Lane | Model | Charter stub (expanded by the desk at issuance) |
|---|---|---|
| SPP-51 `[OPUS]` | pre-declared execution of SPP-33's numbers | arm `hr_by_year` on `INTERFACE_NEIGHBORS["SPP"]` MISO/ERCOT; A/B served vs `--priced-interchange` on the P7 screen year; keeper = control (29b); STOP gate = interchange duration curve sign/magnitude vs EIA-930; matrix cell for the seam mechanism |
| SPP-52 `[OPUS]` | execution | curtailment as a first-class metric (playbook §8.3): reference curtailment rate → the uncurtailed fallback set; report modeled vs reported curtailment; wind-shape arming if SPP-32 left it as an input only |
| SPP-53 `[FABLE]` | TTC is a design object | N↔S TTC from the binding-constraint frequency method (doc 04) via `derive_ttc_limits.py`; rule 14: the measured value stays even if the fit worsens; documents the ITP-vs-link misalignment |
| SPP-54 `[FABLE]` | topology change | the SPS / Texas-Panhandle pocket as a third zone, promoted only on the P1 pre-declared condition (SPS-tie binding share) and scored leave-one-year-out (rule 22) |
| SPP-55 `[FABLE]` | mechanism design | VRL-based scarcity: an in-LP reserve demand curve (closer to MISO's RBDC than to the post-solve ORDC overlay), designed against the SPP tail counts; screen structural only |
| SPP-56 `[FABLE]` | mechanism design, LAST | reserve co-optimisation Reg/Spin/Supp on the `da-mcp`/`rtbm-mcp` measured prices; must first prove non-inertness (MISO precedent) |

### W6 — routed

SPP-60 `[FABLE]`: T1-F hindcast, `program-status.json` SPP row, `GOLDEN_ISOS`, goldens — **chartered by the
capx director** after a card (P8). This desk never writes it.

---

## 9. Findings index (append as they land)

| Lane | FINDING | Landed |
|---|---|---|
| SPP-10 | `docs/handoffs/FINDING-spp-10-<date>.md` / `docs/multi-iso/spp-data-audit.md` | — |
| SPP-11 | `docs/handoffs/FINDING-spp-11-<date>.md` | — |
| SPP-12 | `docs/handoffs/FINDING-spp-12-<date>.md` | — |

## 10. Ledger

Live state, scoreboard, rulings, collision register and issuance record:
`docs/handoffs/spp-desk-ledger-2026-09.md`. Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`.
