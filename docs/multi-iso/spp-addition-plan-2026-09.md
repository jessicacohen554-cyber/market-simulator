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
| 5 | **The six existing keepers' cache keys never move** at any wave (no new `ScenarioConfig` field, no default flip, no `results/cache.py` edit) | `tests/regression/test_persisted_identity.py`, keeper `run_config.json` → **SPP-14 alt-source sweep (P12, r#4)** |
| 6 | Forecast-program entry (T1-F hindcast, `program-status.json` row, `GOLDEN_ISOS`) — **T1-H registered 2026-09-07 (SPP-60, owner ruling Q59): `spp-2021-2025-realized-t1h-spp60` on the forecast namespace, verdict key `spp-t1h` (FC-3 FAIL, HOLD, at full magnitude); board row legs (b)/(c) filled from the measured result; `GOLDEN_ISOS` pending the capx director** (the battery's parts a/b/c reported in `FINDING-spp-60-2026-09-07.md` §5, never asserted) | `frontend/data/forecast/` → `frontend/data/hindcast/spp-2021-2025-realized-t1h-spp60.json`, `ff-verdicts.json::spp-t1h`, `program-status.json::isos.SPP` |
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
| CAMPD CEMS unit-level | `data/raw/campd-unit-level/<ST>_<yr>.parquet` 2019–2026 | present: KS ND SD AR LA MO TX IA MN MT · **missing: OK NE NM** — **CORRECTED by SPP-10 (audit §2.4): no EIA-860 plant with BA `SWPP` is in WY** (Wyoming files under `WAUW`); `CO` IS in the footprint (19.5 MW solar, no CEMS units). SPP-11 landed OK/NE/NM/WY × 2023–2026 anyway; the WY files are inert for SPP. `campd.ISO_STATES["SPP"]` = the 14-state list of audit row 21, WY excluded, CO retained |
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
| **Solve-surface fingerprint (capx D79, landed 2026-09-06)** | `config/solve_surface.py::SURFACE_ISOS` is a hardcoded six-tuple pinned equal to `SUPPORTED_ISOS` by `tests/unit/config/test_solve_surface.py:114`; `solve_surface_declared.py` holds per-ISO declared hashes | add `"SPP"` to `SURFACE_ISOS` in the SAME commit as `_ISO_BUILDERS`; run `scripts/solve_surface_register.py --diff origin/main HEAD` and confirm **zero moved rows for the six ISOs** (ISO projection: an SPP key added inside an ISO-keyed table changes only SPP's row); `--declare` the names whose SPP projection is new (an undeclared row stays out of the key; CI check 5 requires the declaration in the adding PR) |
| Neighbour namespace | `data/neighbor_price.py::_HR_GAS_ELASTIC` keys are GLOBAL (`"SPP"`, `"PJM"` are MISO's seams) | SPP's neighbours named `MISO` / `ERCOT` (free); assert uniqueness |
| ~22 six-tuple tests | `tests/unit/model/test_capacity.py:3436`, `test_storage.py:177,1797`, `test_ccs_retrofit.py:1491`, `tests/unit/data/test_fleet.py:820,1531,2654`, … | extend, or document as deliberate exclusion (capacity-market subsets `_CURVE_ISOS`/`_CAPACITY_ISOS`; carbon `PATH_ONLY_ISOS`) |

### 2.4 Host reachability, probed 2026-09-06 from a session

| Host | Result | Consequence |
|---|---|---|
| `api.epa.gov` CAMPD bulk (`x-api-key: DEMO_KEY`) | 200 | OK/NE/NM/WY CEMS are **session-fetchable** (`scripts/data/fetch_campd_unit_level.py --year Y --states OK NE NM WY`; MISO LA_2023 precedent) |
| `api.eia.gov` v2 | 200 | sub-BA demand (`fetch_eia930_subba_demand.py`), interchange (`fetch_eia930_interchange.py --ba SWPP`), state delivered-gas series |
| `portal.spp.org` | 200 on pages; file-browser API answers `[]` on every listing and the LMP builder's download paths now **404** | **RESOLVED 2026-09-06 by SPP-12 — the API form did NOT move.** The grammar is unchanged and `fsName` is still the page slug; both calls now require an `X-SPP-UI-Token`, and an anonymous caller gets `200 []` / `404` on every product although each is still `isPublic: true` (an invented `fsName` **404s** where a real one **200s**, which is what makes it an authorization outcome and not a bad key). Rows 5–9 **BLOCKED** pending a Marketplace credential. Untried route: SPP's documented **FTP** public-data transport. FINDING §2 |
| `spp.org` | 200 | ITP / Planning Criteria / Market Protocols / LTLF / MMU PDFs |
| `pubftp.spp.org` (SPP's documented programmatic route — *SPP Public Data Access* v3.0 p. 2; **anonymous**, user `anonymous` / password = an email address, *Markets Public Data Guide v35* p. 11) | **transport-blocked at the session egress** (SPP-13, 2026-09-06): a `CONNECT :21` tunnel opens but no FTP banner ever arrives and the relay closes it; identical for control hosts `ftp.gnu.org:21` / `ftp.debian.org:21`; :443/:990 reset after ClientHello; `WebFetch` refuses `ftp:` | **Rows 5–9 need a session whose egress relays port 21, or an owner-side pull** — no credential is missing. Full path layout per product: `data/raw/spp-planning/README.md` §6. FINDING-spp-13 §1 |
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
| **P1** topology | 2 zones (SPP-North / SPP-South) vs 3 (+ the SPS / Texas-Panhandle pocket) | Register **2 zones** in W2 (`_SPP_STATE_ZONES`: ND SD NE MN MT IA KS MO WY → North; OK TX NM AR LA → South, sub-BA-refined where the audit says a state straddles); the SPS pocket becomes the pre-declared first structural lever **SPP-54** — promoted to W2 only if SPP-12 measures SPS-tie binding share ≥ N↔S share. Rationale: N→S wind export is SPP's system-level corridor and is hub-scorable today (N/S hub spread is a measured zonal benchmark); the SPS pocket is real (persistent negative SPS prices, largest curtailment share) but needs a second TTC (OASIS-blocked) and an SPS price series whose availability is unverified. Rule 1: a real structure enters regardless of fit — hence the pre-declared lever rather than a permanent omission | mean / p90 \|SPPNORTH−SPPSOUTH\| by year (SPP-12); binding-constraint share SPS-tie vs N↔S (SPP-12); sub-BA energy shares (SPP-11) | **RULED r#2 (2026-09-06): "2 zones now; two ranked levers"** — register SPP-North/SPP-South in W2; pre-declare BOTH the SPS/Texas-Panhandle pocket (SPP-54) AND an Oklahoma pocket (SPP-57); SPP-12's per-flowgate binding share + shadow-price value vs the N↔S corridor RANKS them; the ranking test is this ruling |
| **P2** MISO seam from SPP's side | MISO already prices SPP from its side; no cross-ISO reconciler exists | **Per-ISO, independent (rule 25).** First keeper serves the **measured EIA-930 `Total interchange` schedule** (`_SCALAR_INTERCHANGE_ISOS` += SPP — the PJM/NYISO/NEISO precedent, playbook §8.2, rule 13-admissible). A priced `NeighborInterface("MISO")` off `actual_lmp_hourly_zonal_MISO.parquet` (MISO-West/South rows) is registered as the **forward** mechanism, default-off, validated in SPP-51 with `--priced-interchange`. The RDT wheel nets to zero at the SPP boundary and is ignored | SWPP↔MISO DIBA duration curve (SPP-11) | **RULED r#2: "Served schedule first, priced seam default-off"** — first keeper serves measured EIA-930 Total interchange; `NeighborInterface("MISO")` and `("AECI")` (the largest measured counterparty, +2.0…+2.6 TWh/yr export) registered default-off, anchored to measured prices; SPP-51 validates |
| **P3** ERCOT DC ties | import node vs neighbour vs ignore | `NeighborInterface("ERCOT")`, 820 MW (the same CDR ratings ERCOT's map cites), border zone `SPP-South`; **inert** under the served schedule, armed with P2's priced seams in SPP-51. No import node (≈1.5 % of peak) | SWPP↔ERCO flows (SPP-11) | **RULED r#2: ACCEPTED** — `NeighborInterface("ERCOT")`, 820 MW, border SPP-South, default-off |
| **P4** reserves | arm co-optimisation now or defer | **Defer.** M2 is last (playbook §5); MISO's co-opt was inert at its zone count and its tail question closed negative — SPP must prove non-inertness on its own data (rule 25). Shard cells `U`; SPP-56 queued last | — | **RULED r#2: ACCEPTED** — deferred; cells `U`; SPP-56 last |
| **P5** scarcity seed | seed ORDC `default_scenario_overrides` like NEISO? | **No seed at registration.** `voll=2000.0` (FERC 831 offer cap; doc 02). SPP's scarcity is VRL / reserve-shortage-driven — a different object from NEISO's winter-gas overlay — and is designed by SPP-55 (Fable) after a committed control exists. Seeding flips `test_iso_config.py:531` and is therefore a ruling, never a default | `actual_tail.json` SPP counts at $200 and $300 (SPP-31 — reported at sitting #2 as a forecast from the hourly parquet) | **RULED r#2: ACCEPTED** — no seed; `voll=2000.0`; SPP-55 designs VRL later |
| **P6** `TAIL_THRESHOLD` | $200 or $300 | **$200** (summer-heat / winter-storm regime like ERCOT/MISO, not NE city-gate gas), in all three copies | tail counts at both | **RULED r#2: $200** (all three copies) |
| **P7** first-solve screen (rule 29) | there is no keeper, so 29(b) "keeper is control" is vacuous | **Control = none.** The first full 2023–2025 bundle IS the baseline and becomes every later SPP lane's 29(b) control. Screen year = the year with the **largest mean \|N−S\| hub spread** (a zero-LP, residual-blind statistic — the only structure beyond copperplate is the N↔S link, and its footprint is the spread). STOP gate structural only: link binds in the measured direction/season; fuel-mix within order of magnitude of EIA-923; no unserved energy / negative-price absurdities. Never "did C3a pass". Screen bundle deleted before merge (29c) | spread by year (SPP-12) | **RULED r#2: "Control = none; screen 2024, structural STOP gate only"** — SPP-12's hourly per-hub mean/p90 overrides 2024 if it disagrees; PRECOMMIT states the hub-spread limitation (Nebraska vs central-Oklahoma two-point spread, audit §6.1) |
| **P8** W6 routing | who charters forecast-program entry | **ROUTE to the capx director** with a card once a keeper exists; this desk never writes `program-status.json` / `ff-verdicts.json` / `GOLDEN_ISOS` | — | **RULED r#2: ROUTE to the capx director after a keeper exists** |
| **P10** `voll` value (SPP-12 correction to P5's citation) | SPP's posted Safety-Net Energy Offer Cap is **$1,000/MWh** (Market Protocols 119 §8.2.5 pp. 356–357); $2,000 is Order 831's hard ceiling for cost-verified offers | register **$2,000** = the highest price a dispatchable cost-verified SPP offer can reach (the NEISO reading of Order 831); the comment cites BOTH numbers; SPP-55 revisits shortage pricing against the VRLs ($250/MW spinning, $50,000/MW power balance) | FINDING-spp-12 §6 | **RULED r#3: "$2,000 — the cost-verified ceiling"** |
| **P11** unblocking portal rows 5–9 + the N↔S TTC (row 11) | the portal needs an `X-SPP-UI-Token`; SPP's *System Interfaces Stakeholder Reference Guide* names an untried **FTP public-data route**; the 2025 ITP Assessment Report carries no transfer-capability table (ITP Manual v3.3 is the next candidate) | charter **SPP-13** (Opus probe lane: FTP route for rows 5–9; ITP Manual / 20-Year Assessment sweep for the N↔S capability + SPS tie ratings); W2 proceeds in parallel; SPP-20 registers the N↔S TTC **Tier-3 with the misalignment documented** (doc 04 convention, rule 14) if SPP-13 has not landed a number first; the SPP-54/57 ranking waits for the flowgate archive | FINDING-spp-12 §2, §6, §8 | **RULED r#3: "Charter SPP-13 probe lane; W2 proceeds in parallel"** |
| **P12** rows 5–9 after SPP-13: the route is anonymous FTP (`pubftp.spp.org`, user `anonymous`) blocked ONLY by the session egress (port 21); row 11 is NDA/CEII, not public | owner-side pull vs defer vs NDA | the desk recommended an owner-side pull of the 36 monthly LMP files + the RTBM daily binding-constraint files | FINDING-spp-13 §1, §4, §6 | **RULED r#4: "Try to find the data somewhere else"** → lane **SPP-14**; W3/W4 proceed regardless; row 11 stays Tier-3 in SPP-20. **CLOSED 2026-09-06 — and the premise was wrong.** SPP-14 swept the candidate list and found the data at SPP itself: `portal.spp.org`'s download and listing calls are both anonymous over plain HTTPS. No owner-side pull, no NDA and no third-party mirror is needed for rows 5–9. The `gridstatus` client reading these URLs with a bare `pd.read_csv` was the tell. `FINDING-spp-14-2026-09-06.md` §1 |
| **P1 — RANKING APPLIED r#5** (a desk act under the ruled test, no card) | SPP-14's four-group table (FINDING-spp-14-…-session-b §5.2): `oklahoma_internal` binds 60–68 % of hours at $188–331/MWh mean \|shadow\|; `n_s_corridor` 52–63 % at $140–227; `sps_tie` 26–34 % at $52–70 — in ALL three years, on BOTH legs | — | FINDING-spp-14 §5 | **APPLIED r#5: SPP-57 (Oklahoma pocket) outranks SPP-54 (SPS pocket); the SPS tie never reaches the N↔S share, so SPP-54 does not clear the README's test and stays queued behind SPP-57** |
| **P13** the N↔S TTC for the first keeper | SPP-20 registered a **48,700 MW placeholder** (North summer capability — cannot bind); no public rating exists (SPP-13); the RTBM archive carries `Real Time Effective Limit` only from **2026-01-28** (SPP-14 §5.4) | pull SPP-53 into W3 as SPP-40's precondition: a Fable derive lane reconciling the 2026→ corridor-flowgate limits (SPP's own rated limits, the ERCOT GTC analogue) into one link TTC, misalignment documented, cross-checked on the 2023–25 corridor binding frequency | FINDING-spp-20 §5 R-6, FINDING-spp-14 §5.4 | **RULED r#5: "Pull SPP-53 into W3 as SPP-40's precondition"** — **EXECUTED 2026-09-07 (SPP-53): `ttc_mw = 3,400 MW`**, the binding-hours-weighted median first-contingency transfer of the corridor's 12 identified flowgates (2026 limit-at-bind ÷ a hub-transfer shift factor identified from SPP's 2023–25 prices; construction fixed in `PRECOMMIT-spp-53-2026-09-07.md` §2.1 before any limit was read; rule-14 misalignment stated on the link; `FINDING-spp-53-2026-09-07.md`) |
| **P9** EIA-930 SWPP defective hours (raised by the audit §3.4) | a 100× unit slip on 2023-06-12 21:00 inflates `NG: WND` by 3.6 TWh (caught on demand, not on fuel-mix columns); two low-side demand dropouts (2025-06-21 05:00 = 1,505 MW; 2024-07-19 00:00) no screen catches | benchmark-side fix in SPP-31 (existing median-ratio test applied to `NG:` columns when building benchmarks, six ISOs byte-identical); the low-side demand screen is a repo-wide defect with cache-key risk → ROUTED to the audit track; SPP-40's PRECOMMIT names the two hours; no new `ScenarioConfig` parameter in W2–W4 | audit §3.4 | **RULED r#2: "Benchmark-side fix in SPP-31; demand-side routed"** |

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
W2  Registration — THE PIN FLIP (one PR)         ∥  matrix shard            ∥  SPP-13 probe (P11, r#3)
    ┌──────────────────────────────────────┐   ┌────────────────────────┐   ┌───────────────────────────┐
    │ SPP-20 register + topology + every   │   │ SPP-21 7th matrix shard│   │ SPP-13 portal FTP route + │
    │ registry  [FABLE] shared→spp         │   │ + §5.7 queue [OPUS]    │   │ N↔S TTC / SPS tie ratings │
    └──────────────────┬───────────────────┘   └────────────────────────┘   │ from ITP docs [OPUS] shared│
                       │                                                     └───────────────────────────┘
    (SPP-14 [OPUS], P12 r#4: alt-source sweep for rows 5–9 over HTTPS — parallel with W2/W3, never a W3/W4 precondition)
    (SPP-15 [OPUS], r#4 am.1: back-year intake 2019–2022 of the SPP-11 products — LANDED 2026-09-06, all four items; feeds W5's holdout ladder)
    WHY NOTHING ELSE RUNS BEFORE SPP-20 MERGES: every W3 derive (outages, tranches, benchmarks, zonal shares,
    wind shape) calls get_iso_config("SPP") — measured r#4 am.1 — so W3 is gated by registration itself, not by the desk.
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
    + SPP-53 [FABLE] N↔S TTC derive (P13, r#5) — pulled from W5 into W3; SPP-40's FOURTH precondition
    W3 ALL LANDED 2026-09-07 (SPP-30/31/32/33/34 + SPP-53).
W4  First-ever solve → FIRST KEEPER → dashboard flip (one lane)
    r#6: SPP-40 OWNER-LAUNCHED 2026-09-07 with all four preconditions verified at the pin.
    r#7: SPP-40 LANDED 2026-09-07 — FIRST SPP KEEPER `2026-09-07-spp-1-baseline` (NOT-YET, owner direction P14;
         the 2024 screen killed on a 22-h direction tie, the full span then run). DoD rows 1–5 MET; row 6 routed.
W4b Input repairs (parallel, ZERO DOF, issued r#7) — the three score/input defects SPP-40 named, then ONE re-baseline
    SPP-41 [FABLE] EIA-930 spike screen → loader seam (v2, both the bench AND the wind-input path; LANDED 2026-09-07)
    SPP-36 [OPUS]  coal supply class — LANDED 2026-09-07 (29/29 SPP coal plants classed: 27 prb, 2 lignite, 0 generic;
                   reported klass COAL 19,196.7 MW/29p → COAL_PRB 17,634.4/27p + COAL_LIGNITE 650.0→2,210.0/3p, bare COAL to zero)
    SPP-37 [OPUS]  SPP-35's six leftovers (gitignore, three more 'six ISOs' files, stale JS, badge, CHANGELOG)
    SPP-42 [OPUS]  after SPP-36 + SPP-41: `--hydro-backfill-year 2024` (four-keeper precedent) + full-span RE-BASELINE → keeper-2 candidate
    r#8: W4b ALL LANDED 2026-09-07. KEEPER-2 `2026-09-07-spp-2-crosswalk-hydro` (SPP-42, NOT-YET; C3a/C3b-2025 → PASS,
         unserved 2,007 → 89 MWh, C5a −67 % → −3 %). SPP-41's seam landed AFTER keeper-2 was solved → keeper-2's 2023
         wind INPUT (+27 GWh) and bench/SPP/2023 (wind 106.634) still carry the slip.
W4c Re-baseline on the screened input (issued r#8)
    SPP-43 [OPUS]  keeper-2's recipe re-solved through the SPP-41 seam → keeper-3 candidate; prunes keeper-1/-2 (rule 15);
                   closes the 'UNSCORED pending SPP-41' lines; R-15 reference-hydro vintage; N-1/N-2 prose; plant 6193 census
    SPP-38 [OPUS]  the 15 SPP-era red tests at HEAD (campaign configs / six-ISO set assertions) — LANDED 2026-09-07:
                   only FOUR were SPP's; 2 red remain (miso-233's parity-registry debt, R-1) — never GOLDEN_ISOS / program-status
    ∥ SPP-41 [FABLE] fuel-spike screen → loader seam (SPP-31 §5a; C4-2023 blocker; src/ edit) — LANDED 2026-09-07
    ∥ SPP-35 [OPUS]  seven-ISO prose sweep + badge contrast — LANDED 2026-09-07
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │ SPP-40 smoke → rule-29 screen (P7) → 2023-25 bundle → register → keepers/    │
    │ SPP.json + index.json + status/SPP.js + bench/SPP + shard stamp + log entry   │
    │ [FABLE] spp                                              ═══ DEFINITION OF DONE ═══
    └──────────────────────────────────────┬───────────────────────────────────────┘
                                           ▼
W5  Calibration loop — §5.7 lever queue, ONE lever = ONE lane = ONE PR, sequential, keeper is control
    SPP-51 seams (P2/P3 priced, --priced-interchange A/B)  [OPUS]
    SPP-52 HSL / curtailment as first-class metric          [OPUS]
    SPP-53 N↔S TTC — MOVED INTO W3 at r#5 (P13); see §4 above
    SPP-57 LANDED r#8: 2025 SCREEN KILLED (both union-rated FCITC links inert — N↔OK 6,500 at bound 2.5 %, OK↔S 6,700 never);
           topology NOT landed; design + instruments landed (f5926636, spp57/). → SPP-57b ISSUED r#8 (R-12: constituent sets re-declared)
    SPP-57b LANDED (2026-09-07): 2025 SCREEN KILLED — N↔OK 3,400 live 23.5 % (93 % N→OK); OK↔S 10,700 (sps_tie alone) never binds:
           the residual bubble EXPORTS into Oklahoma vs an OK→S-loaded identification (R-17 → SPP-54 first); topology NOT landed (7bfe047d)
    SPP-44 ISSUED r#8 [FABLE]: the CT/CC/ST gas split as a P1-native commitment-bridge question (SPP-42 §7; rules 18/19 first)
    r#9: SPP-43 LANDED → KEEPER-3 (owner ruling in-session; leg (i) bit-identity STOPped, three legs met; keeper-1/-2 pruned).
         SPP-57b KILLED (N↔OK 3,400 live 23.5 %/93 % N→OK; OK↔S 10,700 never — the sps_tie link is DIRECTIONALLY misaligned
         with the residual bubble, R-17 → SPP-54 first). SPP-38 LANDED (4 of 15 were SPP's). SPP-44 RUNNING (screen 2023).
         OWNER-LAUNCHED, off-desk: SPP PRICE FAMILY (uniform offer-curve quadruple KILLED on its structural leg while
         improving C3a/C3b — the miss is LOAD-driven; C3c → SPP-55; C1-2024 → SPP-44) and the capx Q59 BOARD ROW (§2.1b,
         written from backcast artifacts; the T1-H half ROUTED TO THIS DESK → SPP-60 is now ours).
    ISSUED r#9: SPP-45 [OPUS] board-row re-key + records · SPP-58 [FABLE] second ψ identification (prerequisite for any
         SPS-tie rating) · SPP-54 [FABLE] SPS pocket (design now; rate + solve after SPP-58) · SPP-51 [FABLE] priced seams ·
         SPP-60 [FABLE] T1-H recipe + forecast intake (Q59). HELD: SPP-55 until SPP-44 lands (28c shard collision).
    r#10: SPP-44 LANDED — 2023 screen KILLED (CC window agreement 0.694 < 0.76; D-4 unit-conduct FAIL at five laid-up
         plants); the bridge fires 0.41 TWh against a 4.2 TWh measured committed-state gap — SPP's gas problem is units
         the model NEVER STARTS, not units it stops (R-17 → SPP-46 queued: a measured commitment-STATE input on ST_GAS, or
         a per-class band under the carve-out). Field landed default-off; cells U → R. SPP-55 hold LIFTED → ISSUED r#10.
    SPP-54 SPS-pocket third zone   ┐ P1 pre-declared levers, RANKED by SPP-12's per-flowgate
    SPP-57 Oklahoma-pocket zone    ┘ binding share + shadow price vs the N↔S corridor  [FABLE]
    SPP-55 VRL-based scarcity design                        [FABLE]
    SPP-56 reserve co-optimisation (M2, LAST)               [FABLE]
                                           ▼
W6  Forecast-program entry — GATED, ROUTED to the capx director (P8)
    SPP-60 T1-F hindcast + program-status.json row + GOLDEN_ISOS + goldens  [FABLE]

CRITICAL PATH (r#10):  keeper-3 ✔  →  SPP-58 ψ₂ → SPP-54 rating/solve  ∥  SPP-51  ∥  SPP-55 (scarcity, now unblocked)  ∥  SPP-60 (T1-H)  ∥  SPP-45 (gate-(a))
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
| **SPP-12** portal/spp.org fetch — **LANDED 2026-09-06** (`docs/handoffs/FINDING-spp-12-2026-09-06.md`; portal BLOCKED, spp.org served, addendum r#2 (A)+(B)+(C) discharged) | OPUS · API re-discovery + transcription against a manifest | shared | `build_spp_lmp_reference.py` (`--per-hub` → `_validation-source/actual_lmp_hourly_zonal_SPP.parquet`); `data/raw/spp-hourly-load/`, `spp-genmix/`, `spp-binding-constraints/`, `spp-or-mcp/`, `spp-hsl/` (each with README + SOURCES); `data/raw/spp-planning/` PDFs or transcriptions (ITP, Planning Criteria PRM, Market Protocols VRL/offer cap, LTLF, MMU SOM) | listings return non-empty; a 2025 monthly file range-fetches | `FINDING-spp-12-<date>.md` with the reachable/blocked table and **the P1/P7 numbers** (hub spread by year; SPS-tie vs N↔S binding share) | anything still blocked becomes a manual-manifest row (§6) with the exact URL; never a guessed value |
| **SPP-13** portal FTP route + N↔S TTC — **LANDED 2026-09-06** (`docs/handoffs/FINDING-spp-13-2026-09-06.md`; FTP route = `ftp://pubftp.spp.org`, ANONYMOUS, **egress-blocked** from a session; row 11 swept — NOT public, ratings are an NDA/CEII GlobalScape workbook naming `SPPSPSTIES` / `SPSNMTIES`; two real GenMix payloads + monthly peaks landed from SPP's v35 sample zip; spread + binding-share tables NOT obtainable) | OPUS · transport probe + document sweep against a fixed list; no design choice | shared | payloads under `data/raw/spp-hourly-load/`, `spp-genmix/`, `spp-binding-constraints/`, `spp-or-mcp/`, `spp-hsl/` (if the FTP route serves them); `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` (via `build_spp_lmp_reference.py --per-hub` — implemented, never run live); `data/raw/spp-planning/` transcriptions (ITP Manual v3.3 / 20-Year Assessment: N↔S transfer capability, SPS tie ratings) | a listing that returns entries, or a documented refusal | `FINDING-spp-13-<date>.md` | every number page-cited; the P1 ranking table (SPP-54 vs SPP-57) if the archive lands; the hourly mean/p90 spread if the LMP lands; otherwise the exact refusal per route |
| **SPP-14** alternative sources for rows 5–9 (chartered r#4, P12) — **LANDED 2026-09-06: no alternative was needed. `portal.spp.org` is NOT credential-walled — both file-browser calls answer anonymously over plain HTTPS and honour `Range`; SPP-12's `200 []` reproduces only for `path=` EMPTY and its download 404s were folder paths. Rows 5/6/7/9 SERVED (row 7 complete and gap-free 2023–2025), row 8's archive pulled and the four-group table COMPUTED, cross-check gate PASS at 0.0000 %. `docs/handoffs/FINDING-spp-14-2026-09-06.md`** | OPUS · source sweep against a fixed candidate list with a fixed cross-check; no design choice | shared | payloads under `data/raw/spp-lmp-alt/` (NEW; hub / settlement-location hourly DA+RT), `spp-binding-constraints/`, `spp-hourly-load/`, `spp-genmix/`, `spp-or-mcp/` (README + SOURCES rows per source); `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` ONLY if a landed series reproduces the committed system-hub parquet within the stated tolerance | each candidate host answers over HTTPS; a landed LMP series reproduces the committed `actual_lmp_hourly_SPP.parquet` annual RT means ($23.47 / $23.31 / $27.11) within 1 % | `FINDING-spp-14-<date>.md` | per-source table (host · product · span · licence · reachable · reproduces SPP's own figures?); the per-hub spread and four-group tables if the archive lands; the residual manifest otherwise |
| **SPP-15** back-year intake 2019–2022 — **LANDED 2026-09-06** (all four items GOT, blocked table empty; `docs/handoffs/FINDING-spp-15-2026-09-06.md`) | OPUS · the SPP-11 recipe re-run on four earlier years; zero design | shared | `data/raw/campd-unit-level/{OK,NE,NM}_{2019..2022}.parquet`; `data/raw/zone-specific-demand/SPP/spp_subba_demand_<yr>.csv` ×4 (the MISO per-year shape); `data/raw/eia-930-interchange/"SWPP interchange hourly.parquet"` widened to 2019–2025 with the 2023–2025 rows proven byte-identical; `data/raw/gas-prices/eia_delivered_gas_{OK,KS,TX,NM}_monthly_2019-2022.csv` | schema-equal to the 2023–2025 siblings | `FINDING-spp-15-2026-09-06.md` | DONE: 12 CEMS parquets (OK/NE/NM × 2019-2022), schema == `KS_2024` all 12, WY correctly excluded; 4 per-year SWPP sub-BA files (17 sub-BAs each, reconciling to **1.000000–1.000416** of the BA `Demand`, first stamp `<Y>-01-01T07` in every year incl. 2019); interchange widened 268,177 → 618,817 rows with the 2023-2025 slice **proven byte-identical** (same 268,177 rows, same sha256 `243889469b96…` before and after — no separate back-year file needed); 4 delivered-gas CSVs whose cut reproduces all four committed `_2023-2025.csv` files byte-identically. Producers unmodified; nothing solved, scored or registered; `--holdout-intake SPP` records this charter's dispatch for 2022. **Four source defects reported and NOT filled, all routed:** 2019 sub-BA 96-h gap + the early-year interchange null cliff (2,040/2,256 h in 2019/2020, ~50 % Sat ~49 % Fri) + two impossible `AECI` prints at 2020-03-17 that sign-flip SWPP's 2020 system net (−9.77 vs +0.97 TWh) + **`N3045OK3` publishes nothing 2015-2021**, so OK gas exists for only 2022/2023/2024 of 2019-2025. **Open, routed to the desk:** the `campd-unit-level/README.md` "Fetching" section still claims the fetcher requires a `calibration-complete` marker for a holdout intake; the code and rule 22 both say it does not — left untouched as outside this lane's rows. |
| **SPP-20** register — **LANDED 2026-09-06** (`docs/handoffs/FINDING-spp-20-2026-09-06.md`: six keepers unmoved — 0 moved surface rows, persisted identity 23/23, MISO `fleet_only` rebuild 87/87 arrays identical; the N↔S TTC is a declared NON-BINDING placeholder pending SPP-13; routed: D79 ledger new-ISO-row limb, `spp.csv` `basis=coincident`, parameter-registry regeneration) | FABLE · topology + market-object choices + the pin flip + rule-27 core scope | shared → spp | see §2.3 list + `_spp_config()`, `zone_assignment.py` (`_ISO_TO_BA_CODE`, `_LARGEST_ZONE`, `_EGRID_VINTAGE`, `_SPP_STATE_ZONES`, `_spp_zone`), `campd.py::ISO_STATES`, `eia930/frames.py::_ISO_TO_HOURLY_BA`, `eia930/demand.py` (`_load_spp_hourly_demand`, `DEMAND_LOADERS`, `_SCALAR_INTERCHANGE_ISOS`), `renewables.py::RENEWABLE_ZONE_ALLOCATION`, `transmission_expansion.py::TRANSMISSION_BASE_STATIC_VINTAGE`, `fleet/models.py::BA_CODE_TO_ISO`, `capacity_market.py` all-six dicts, `constants.py` all-six dicts, `fuel_trajectories.py` three dicts, `interchange/registry.py::INTERCHANGE_INJECTIONS["SPP"]`, `interchange/spec.py::INTERFACE_NEIGHBORS["SPP"]` (no `IMPORT_ZONE`/tranches), `scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/spp.py`, `configs/data-profiles.yaml`, `docs/multi-iso/README.md` "seven" | `validate_topology()`; fleet census equals SPP-10's; `hydrate_data.py --list` shows the `spp` profile owning `SWPP*` and NOT `DAMLZHBSPP_*`; `pytest tests/unit/config tests/curation tests/unit/data -q`; `python scripts/ci_refactor_guards.py`; `check_mechanism_matrix.py` (no field added ⇒ nothing owed) | `FINDING-spp-20-<date>.md` = registry entry table (dict → value → citation) + the six-keeper byte-identity proof | **six keepers unmoved**: replay-hash MISO's keeper fleet/offer arrays (the one ISO whose code names SPP) + goldens + `test_persisted_identity` for the rest; `test_iso_config` scarcity checkpoint still `["ERCOT","NEISO"]` unless P5 ruled otherwise; **no new `ScenarioConfig` field** |
| **SPP-21** matrix shard — **LANDED 2026-09-06** (`docs/handoffs/FINDING-spp-21-2026-09-06.md`; seventh shard live, 305 cells 162 `U` / 47 fc-only `U` / 96 `.`, guard exit 0, 33/33 matrix tests, 7 columns rendered. Two owner-authorized out-of-region edits, both disclosed in the FINDING: 4 six-ISO test assertions, and a one-line `mechanism-matrix-assemble.js` repair for a pre-existing anchor mismatch that had left the rendered page blank since 2026-08-11) | OPUS · mechanical shard emission + queue transcription | code | `docs/codebase-site/data/mechanism-matrix.js:1460` `isos:`; new `data/mechanism-matrix/SPP.js` (a cell for EVERY id: `U` where ISO-applicable, `·` where n/a, `keeper: ""`); `data/mechanism-matrix-assemble.js:29` `EV_KEY` `SPP:'S'`; `mechanism-matrix.html:113-118` script tag; `scripts/lib/mech_matrix.py` `ISO_ORDER` / `ISO_EV_KEY` / `ISO_FIELD_STEMS["SPP"]=("spp",)`; `docs/mechanism-testing-matrix.md` §2 similarity note + new **§5.7 SPP lever queue** (cross-cutting 5.7 → 5.8) | `python scripts/check_mechanism_matrix.py` exit 0 (shard covers exactly the base id set) | `FINDING-spp-21-<date>.md` | **ONE commit**; `pytest tests/unit/config/test_mechanism_matrix_*.py`; 7-column `file://` preview; a one-line cross-desk notice appended to the capx and SCN ledgers: "7 shards from now on — every rule-28(c) cell line includes SPP" |
| **SPP-30** outages + tranches — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-30-2026-09-07.md`; G4 PASS: windows > 0 in every CEMS state holding an SPP fleet unit — OK **1060**, NE **358**, TX 345, MO 339, KS 325, LA 121, AR 51, NM 36, IA 34, ND 34, SD 9. MN/MT zeros are structural and evidenced (MN: no SPP fleet plant files CEMS there; MT: the one plant, Culbertson, is `CT_PEAKER` — peakers carry no overlay); CO has no CEMS file, as §2.1 already records. Coverage **85.3 % of qualifying plants / 97.9 % of qualifying MW**. Five extracts: standard 2721 · short 620 · layup 1089 · e923 18 · partial 85; plus `thermal_tranches_SPP.csv` 118 plant-groups (105 ok, 13 eia923_cf). **Full-year fallbacks: 9**, all `eia923_netzero` and all itemised by unit with the reason — inside the cross-ISO band (MISO 135, PJM 95, CAISO 78, NEISO 56, NYISO 30); the 10th full-year window (Jeffrey Energy Center unit 3 / 2023, 3 MWh gross and 2.8 opTime hours all year, back to 3.04 TWh in 2024) is a **measured** CEMS outage, not a fallback. Class band vs MISO reported not tuned: CT_PEAKER 14.8/16.1, ST_GAS 18.4/20.2, COAL committed 36.0/40.5, COAL mustrun-online 23.0/27.6, CC_REGULAR 32.9/42.4. Rule 25 verified at the offer curve: every ISO-scoped class SPP carries is **1.0 on every band** with no `phys_*` rows, so SPP-40's `authorized_price_tuning`-declares-**none** gate is already satisfiable. **ROUTED to SPP-DESK:** `derive_cc_committed_pct.py` has no `argparse`, hardcodes `["TX"]`+2023 and the ERCOT bin sheet, and writes one un-suffixed global CSV — `--iso SPP` is silently ignored and running it would overwrite **ERCOT's** file while producing nothing for SPP. It is superseded for every non-ERCOT ISO by `derive_thermal_tranches.py` (its own docstring says so), which delivered SPP's committed-%. Drop it from the §5/§8 SPP sequence. `tag_mixed_plants.py` is a no-op for SPP — proven on a scratch copy, both committed reference sheets sha-verified unchanged; `build_offer_curve_overrides.py` writes no file) | OPUS · frozen derives (rule 23) | spp | `data/raw/campd-unit-outages-SPP.csv` (+ `-short`, `-layup`, `-e923` siblings as emitted), `campd-partial-outages-SPP.csv`, SPP rows of the committed-pct / thermal-tranche / bin-assignment CSVs | windows > 0 in every CEMS state incl. OK/NE; zero full-year fallbacks | `FINDING-spp-30-<date>.md` (windows per state-year, units covered %) | `derive_campd_unit_outages.py --iso SPP --years 2023 2024 2025` → `derive_thermal_tranches.py --iso SPP` → `tag_mixed_plants.py` → `build_offer_curve_overrides.py`; every output header cites source + method |
| **SPP-31** benchmarks — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-31-2026-09-07.md`: SPP 2023–2025 in `actual_lmp.json` (RT $23.47 / $23.31 / $27.11, reproducing SPP-14's gate to the cent; per-hub `zones` keyed by TRADING HUB with the node-cluster comment in every record), `calibration_reference.json` + eGRID `BACODE=SWPP`, tail (RT >$200: 42 / 59 / 68 h; >$300: 15 / 16 / 32 h) and amplitude (RT hod range $29.53 / $37.37 / $47.12). **P9 closed in the benchmark builder: SPP 2023 wind 106.6345 → 103.0488 TWh**, exactly two series move across all seven ISOs × 2021–2025. **Every pre-existing ISO block byte-identical, proven three ways** (committed vs HEAD-rebuild vs SPP-31), which exposed two PRE-EXISTING staleness findings that are NOT this lane's: CAISO's renewables block predates the 2026-09-05 EIA-860 vintage_2024 + hub-crosswalk intake (spliced out, routed), and ERCOT's amplitude gained three already-authorized years (kept — additive, reported-only, and the tail part already had them). **BLOCKING FOR SPP-40: the `NG:` screen does NOT reach the C4 `bench/` path** — `run_calibration_full._eia930_frame_generic` is unscreened, so SPP 2023 C4 would score wind against a +3.5857 TWh benchmark until FINDING §5a lands. Routed: the `src/actuals.py` generalization; `curate_demand_profile.MODEL_ISOS` excluded SPP (one-line out-of-region fix made and disclosed — without it `load_demand_meta('SPP',2023)` returned peak_mw 3,621,097 MW); the `build_calibration_reference` sys.path seam bug; CAISO staleness) | OPUS · execution | spp | `scripts/data/derive_actual_lmp.py` SPP path (system + per-hub zones), `build_calibration_reference.py` (`"SPP":"SWPP"` BA map, eGRID BACODE), `_validation-source/actual_lmp.json` SPP block, `SPP_{2023,2024,2025}_renewable_capacity.csv`, `calibration_reference.json` SPP block, regenerated `frontend/data/backcast/tail/actual_tail.json` + `amplitude/actual_amplitude.json` | SWPP rows present in the shared `eia_demand_profiles.parquet` / `eia_generation_profiles.parquet` (else re-run `convert_eia930.py` and prove non-SWPP rows byte-identical) | `FINDING-spp-31-<date>.md` | other ISOs' blocks **byte-identical** in every shared JSON (json-diff = ∅); SPP `rt`/`rt_mon`/`rt_pct` present 2023–2025; `actual_tail.json` SPP counts at the P6 threshold |
| **SPP-32** zonal shares + wind shape + gas hub — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-32-2026-09-07.md`: all gates PASS — shares sum to 1.0 with `max|Σ−1| = 0.000e+00` in all three years, redistribution identity **2.05e-16 relative**, wind shape reconciles to SPP's own metered wind at hourly r 0.833–0.848 / seasonal r 0.907–0.984; **six keepers unmoved** — 0 solve-surface values moved, persisted identity 23/23, no `ScenarioConfig` field (G8), 17-hunk G-DRIFT audit all INERT ×6; 40 new tests on synthetic tmp-`CLEAN_DIR` fixtures (G17). **Measured, and opposite to the MISO intuition: SPP-South is the nocturnal wind zone** (night/aft 1.04/1.06/1.03 vs North 0.97/0.96/0.91) — docstrings corrected to the measurement. FINDING-spp-14's WACM/PRPA/WAUW "hole" **CLOSED, measured**: the 17 sub-BAs reconcile to SWPP system demand within 0.03 %, so the omitted members are absent from both sides of the ratio. Reference curtailment rate **both legs measured** — 8.49/10.56/9.90 %, mean 9.65 %, ~2× MISO's — and the metered denominator independently resolves SPP-12's inconsistent-year-label ambiguity. Gas hub committed **2022–2024 only**: `N3045OK3` is unpublished for 2025 and the TX/NM blend was measured and REJECTED ($1.10/MMBtu off OK in 2024). SPP-20's R-2 `basis=coincident` routing discharged. Routed: 3 CAISO test files red on `main` (pre-existing, confirmed two ways), MISO-branch/builder consolidations, the gas 2025 decision) | OPUS · data-intake contract execution | spp | `curate_zonal_shares.py` SPP branch + `_SPP_SUBBA_ZONE_GROUPS`; the clean `zonal-shares` rows for SPP; new `scripts/data/build_spp_wind_shape.py` (clone of `build_miso_wind_shape.py`, NASA POWER `WS50M` at EIA-860 wind sites) → `data/raw/spp-wind-shape/spp_<yr>_wind_zone_shape.parquet`; `data/raw/spp_zonal_gas_hub.csv` (MISO csv pattern; EIA delivered-to-EP state series as the Panhandle / NGPL-MidCon proxy) + `data/fuel/basis/meanzero.py` wiring (r#6: the SPP basis rows landed there, not in `hubs.py` — E-5); `renewables.py` SPP membership in the wind-zone-shape ISO set (a membership, not a field); SPP reference curtailment rate only if SPP-12 landed a published annual rate | shares sum to 1.0 every hour; the redistribution identity holds to 1e-9 | `FINDING-spp-32-<date>.md` with a G-DRIFT hunk audit classifying every `renewables.py` / `hubs.py` hunk INERT for the six ISOs | `data-intake` skill contract (`write_clean`/`read_clean`, tmp-`CLEAN_DIR` tests); no `ScenarioConfig` field |
| **SPP-33** seam derive — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-33-2026-09-07.md`; `data/raw/reference/spp_seam_*.csv` + `spp_seam_SOURCES.md`). `hr_by_year` RT for SPP-51 to arm: MISO 9.82/10.55/9.90 · AECI 10.30/12.08/8.32 · ERCOT 23.70/15.87/10.76. **Three items ROUTED to SPP-DESK** (FINDING §6): R1 `_NEIGHBOR_LMP_ISO` reaches none of SPP's three registered anchors (SPP-20 R-7 — producer NOT edited); R2 the registered `marginal_heat_rate`s divide by bare Henry Hub where the seam prices on `HH + gas_basis` (inert for the keeper, live forward — SPP-51's `spec.py`); R3 `_HR_GAS_ELASTIC`'s global name key BLOCKS SPP↔MISO's forward elasticity (PJM already owns `"MISO"`). ERCOT's registered 820 MW limit is under its own measured ±835 MW clip in 547/128/21 h. EIA-930 sign convention confirmed on SPP's own meter (corr +0.9936…+1.0000) | OPUS · derive only | spp | `derive_neighbor_hr_by_year.py --iso SPP` outputs (MISO from `actual_lmp_hourly_zonal_MISO.parquet` West/South rows; ERCOT from its hourly parquet); SWPP interchange duration curves by DIBA; `data/raw/reference/spp_seam_*.csv` | — | `FINDING-spp-33-<date>.md` — the `hr_by_year` and measured-flow numbers **for SPP-51 to arm** | does NOT edit `spec.py`; numbers reproduce from committed inputs |
| **SPP-34** site + docs — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-34-2026-09-07.md`; four routed items R-3/R-4/R-5/R-8 of FINDING-spp-20 §5 CLOSED; five stale "six ISOs" claims in `CLAUDE.md` / the spec / `codebase/README.md` / `user-manual.md` ROUTED as S-1) | OPUS · execution | code | `docs/codebase-site/js/iso-configs-table.js:16-30,230`, `js/viz-iso-topology.js:16,118`, `css/site.css:402-407`, `data/iso-topologies.json` (regenerate from `get_iso_config`), `forecast-runs.html:90` (add SPP; verify the page tolerates an ISO with no forecast runs), `data-completeness.html:360`, `scripts/render_data_dictionary.py:49`, `docs/codebase/08-config-reference.md`, `docs/README.md`, `index.html` "six ISOs", `docs/calibration-log/spp.md` (header, MISO's format), CHANGELOG | — | `FINDING-spp-34-<date>.md` | `accessibility-audit` skill on touched pages; `sync-docs`; **`ff_readiness_battery.GOLDEN_ISOS` NOT touched** (W6) |
| **SPP-40** first solve → first keeper — **LANDED 2026-09-07: FIRST SPP KEEPER `2026-09-07-spp-1-baseline`** (PRs #5425/#5434/#5446/#5447; `FINDING-spp-40-2026-09-07.md`). Rule-29(a) 2024 screen KILLED on the pre-registered direction leg (877 N→S / 899 S→N at bound, a 22-h tie); full span solved under owner direction (P14) and registered. **Determination NOT-YET** at full magnitude: C1 FAIL (CT_PEAKER +6.7/+10.3 TWh; coal rows fail by the class crosswalk, §7.3), C3a +14.1 % / in band / +21.7 %, C3b 0.24–0.28, C3c 0/3/24 h vs 42/59/68; C2, C4, C6, C8 PASS. Link live 20 % of hours, N→S-dominant in 2023 (1,702/275) and 2025 (1,245/373); mean |S−N| spread ~$1 vs $12–17 measured; 7–9 negative hours vs ~1,000; 0.0 % wind re-curtailment; 2025 unserved 2,007 MWh (hydro vintage 0.02 vs 8.8 TWh). Rule-25 COAL band breach found and neutralised pre-solve (`_SPP_OFFER_CURVE`). **This bundle is the rule-29(b) control for every later SPP lane.** Routed R-1…R-8 assigned r#7 (§8 W4b) | FABLE · novel-object kill-grading, determination, attestation | spp | `results/calibration/spp40_baseline_B/` (+ `hourly/` sidecars), `frontend/data/backcast/{registry,runs}/<id>.*`, `keepers/SPP.json` (new), `keepers/index.json` (+SPP), `status/SPP.js` (`build_status.py --iso SPP`), `bench/SPP/<yr>.json.gz`, `mechanism-matrix/SPP.js` keeper + gates stamp (LAST commit), `docs/calibration-log/spp.md` entry, `PRECOMMIT-spp-40-<date>.md` | `run_calibration.py --iso SPP` smoke on the screen year (fuel-mix only); fleet / offer-array census; PRECOMMIT pushed before any solve | `FINDING-spp-40-<date>.md` | `audit_keepers --check`, `check_registry_payload_parity`, `check_mechanism_matrix`, `check_bench_freshness` all 0; screen bundle DELETED before merge (29c); dashboard renders SPP with its determination; DOF ledger lists zero residual-identified parameters; `authorized_price_tuning` declares **none** (every `offer_curve_by_group` band 1.0 — rule 25) |
| **SPP-53** N↔S TTC derive (W3 since r#5, P13) — **LANDED 2026-09-07: `ttc_mw = 3,400`** | FABLE · a TTC is a design object: the reconciliation of parallel flowgate limits into one link rating is adjudication | spp | `data/raw/spp-binding-constraints/rtbm_bc_corridor_limits_2026.parquet` (NEW reduced sidecar: the `n_s_corridor` rows of the 2026-01-28→ 14-column daily files) + README/SOURCES; `src/market_sim/config/iso_configs.py` `_spp_config` TTC value + comment (rule 27); `config/transmission_expansion.py` `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` if the vintage moves; `docs/parameter-citations.md` row | the construction rule is written in the PRECOMMIT BEFORE any limit is read | `PRECOMMIT-spp-53-2026-09-07.md`, `FINDING-spp-53-2026-09-07.md` | no solve; the six keepers' keys unmoved (`solve_surface_register.py --diff`); SPP-40 reads the value. **Delivered:** FCITC construction (limit-at-bind ÷ a shift-factor identified from SPP's own hub spread × shadow prices) → 3,400 MW; vintage → 2026; rule-14 misalignment stated in the link comment; the 14-column schema actually begins 2026-03-17 / 04-01, not 01-28 (FINDING §3); the S→N-loaded set reads 4,206 MW by the same rule |
| **SPP-41** EIA-930 spike screen → the loader seam — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-41-2026-09-07.md`: ONE screen at `eia930.actuals._screen_fuel_spike_columns`, every reader inherits it, builder copy deleted; census over 7 ISOs × 2019–2026 × every series: exactly SPP 2023 wind 106.6345 → 103.0488 and NYISO 2024 `other` 3.3846 → **3.3197** (not the projected 3.3486 — the seam screens the RAW column before gap-fill, SPP-31's copy screened after it; FINDING §2.3) on the bench path, SPP 2023 wind alone on the input path; seven keeper `cache_key()`s unmoved; `calibration_reference.json` rebuild byte-identical; no bench part regenerated — NYISO 2024's would move only its unread `e930.other` (fold = 0 both ways), SPP 2023's is keeper-2's (SPP-42 solved BEFORE the seam landed — re-render command + R-9/R-10 answers in FINDING §5/§8); **routed:** SPP 2023 `Net generation` h3907 still carries the slip (report lines only; co-flag proposal, FINDING §7a)) (SPP-31 §5a + SPP-40 §4 wind-input path; issued r#6, re-issued v2 r#7, same stem) | FABLE · a `src/` seam edit under gates G8/bench-freshness: which consumers move and whether any keeper's C4 bench moves is an adjudication | code | `src/market_sim/data/eia930/actuals.py::load_eia_hourly_benchmark` (the screen moves in), `scripts/data/build_calibration_reference.py` (`_screen_fuel_spikes` becomes a thin call or is deleted — rule 26, one mechanism), its tests; `frontend/data/backcast/bench/<ISO>/<yr>.json.gz` ONLY where the proof says a series moves (expected: NYISO 2024 `other` only, and only if that part is regenerated) | zero-LP: the SPP-31 §3.2 two-series table reproduced from the seam (SPP 2023 wind 106.6345 → 103.0488; NYISO 2024 other 3.3846 → 3.3486; every other ISO×year×series byte-identical); `cache_key()` unmoved for all seven ISOs | `FINDING-spp-41-<date>.md` | `check_bench_freshness`, `check_golden_manifest`, `ci_refactor_guards`, `pytest tests/unit/data` all 0; no `ScenarioConfig` field; no solve |
| **SPP-35** seven-ISO prose sweep + badge contrast — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-35-2026-09-07.md`; the five S-1 claims go to seven with SPP appended last at 2 zones — except `user-manual.md:646`, where `git check-ignore` over all seven shows `results/SPP/` is NOT ignored, so the line states the measured six-of-seven position and the `.gitignore` one-liner is ROUTED. `.iso-badge` routed onto shared.css's tinted `.badge--iso-*` pattern in both rules: **7/7 now pass WCAG AA at 17.35-19.13:1**, from 5 FAIL + NYISO 4.35 marginal FAIL, measured in Chromium on painted pixels over both badge code paths, no new hue. O-4/O-6 docstrings brought to the SPP-53 position. Six items ROUTED, §5 of the FINDING: the `.gitignore` gap; THREE more stale six-ISO prose sites SPP-34's sweep missed (root `index.html` x3, `README.md:121`, `market-sim-build-plan.md:9`); O-6's code half; `policy-scarcity.html`'s CAISO badge at 4.47:1; `iso-configs-table.js:32`'s placeholder TTC sentence; the CHANGELOG question) | OPUS · execution of an enumerated list | code | `CLAUDE.md:19`, `model-methodology-spec.md:13,719`, `docs/codebase/README.md:22`, `docs/user-manual.md:646` (S-1); `docs/codebase-site/config-reference.html:209` + `css/bc-pages.css:125` (S-2 → the tinted `.badge--iso-*` pattern already in `shared.css`); the two SPP-20 doc items O-4 / O-6 | — | `FINDING-spp-35-<date>.md` | `accessibility-audit` on the badge (every ISO ≥ 4.5:1); `sync-docs`; no `src/`, no `frontend/data/`, no shard |
| **SPP-36** coal supply class for SPP (SPP-40 R-7; issued r#7) — **DELIVERED BY SPP-42 (2026-09-07, `FINDING-spp-42-2026-09-07.md` §1)**: `coal_supply_SPP.csv` landed (27 prb / 2 lignite, 0 unclassified, 19,846.7 MW), `_SPP_OFFER_CURVE` extended to every coal key (rule 25), zero-LP census byte-identical on every LP input in all three years; the same tag also stops the benchmark's CAMPD backfill mis-firing on untagged coal plants (~2 TWh/yr of spurious ST_GAS actual) | OPUS · one frozen derive on a committed recipe (rule 23), CLI verified against `--help` by the desk (E-5 note) | spp | `data/raw/_processed-legacy/coal_supply_SPP.csv` (NEW, the per-ISO file `coal.coal_supply_class` step 2 merges) + its FINDING; nothing else | zero-LP: `fleet_only` census of MW moving `COAL` → `COAL_PRB` / `COAL_LIGNITE` / `COAL_BIT`; six keepers' solve surface 0 moved | `FINDING-spp-36-<date>.md` | every SPP coal plant classed or itemised with the reason; no solve; the keeper's INPUT moves (re-baseline SPP-42 absorbs it) | · **INDEPENDENTLY CORROBORATED by lane SPP-36** (`docs/handoffs/FINDING-spp-36-2026-09-07.md`), which re-derived the file from the committed recipe and reached the **byte-identical** artifact (sha256 `f922f8f04a02994a084a54f50d1444a7b00b24b`, 29 rows) — two lanes, one derive, same bytes. Its four gates: **(a)** 29/29 EIA-860 fleet coal plants classed, 0 generic; the 30th dispatch-fleet coal plant (7902 Pirkey, `LIG`, retired 2023-03) is a retiree-window unit caught by resolution **step 3** and already read `COAL_LIGNITE`, step 4 empty (flag off); per-year stability **0 disagreements in 87 plant-year comparisons** (2025 alone drops 3 plants on the preliminary EIA-923 vintage — why the committed file is the all-years run). **(b)** family sum reproduces §7.3 exactly (2023 model **70.521** vs actual **71.693 TWh**); the file moves the MODEL side by the whole 70.5 TWh and the ACTUAL side by ≤**0.045 TWh** (0.000 in 2023) with the family total byte-identical every year — a re-attribution inside the coal family, never a change to its total. **(c)** zero-LP `fleet_only` on the keeper's own recipe: bare `COAL` **19,196.7 MW/29 plants → 0.0/0**, `COAL_PRB` **0 → 17,634.4/27**, `COAL_LIGNITE` 650.0 → **2,210.0/3**; 17,634.4 MW (**88.9 %** of SPP coal) enters the PRB take-or-pay / sigmoid passthrough physics for the first time (measured physics, rule 13, NOT a band); tranche rows 128 → 214 at conserved capacity except one 4.65 MW plant (54211, −2.40 MW = 0.012 %) whose six-slice econ ramp falls under `MIN_TRANCHE_CAPACITY_MW` — pre-existing, ISO-agnostic, `src/` untouched, **routed R-9**. **(d)** `solve_surface_register.py --diff` **0 moved** (297→297 names) and zero plant-code overlap on all nine checks (3 other `coal_supply_*.csv` + all 6 other ISOs' whole EIA-860 fleets), so rule 25 holds. Also routed **R-10** (3.178 TWh of 2023 coal at plant 6193, inside the bench population but outside the fleet coal set) |
| **SPP-37** SPP-35's six leftovers — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-37-2026-09-07.md`; all six routed items closed except **R-3**, which the charter routes elsewhere. `.gitignore:277` `/results/SPP/` — `git check-ignore` exit 0, which also discharges the `user-manual.md:646` caveat SPP-35 had to write. The last **five** stale six-ISO prose sites in three files go to seven with SPP appended LAST (root `index.html` :7/:34/:153, `README.md:121`, `market-sim-build-plan.md:9` + the same bullet's zone-count list). `policy-scarcity.html`'s own `.iso-badge` CAISO cell alpha 0.15 → 0.12: **3/3 now pass WCAG AA** — CAISO 4.57, PJM 5.12, NYISO 4.66, measured in Chromium on painted pixels over the page as served, so **10 of 10** site badges pass with SPP-35's seven. AGAINST INTEREST: the CAISO before-column reads **4.50** as Chromium paints it, not SPP-35's 4.4786 arithmetic — the pre-fix cell sat exactly ON the threshold. `js/iso-configs-table.js:32`'s "non-binding placeholder" replaced by SPP-53's 3,400 MW rule-14 reconciled corridor limit. ONE CHANGELOG entry covers SPP-35 + SPP-37. Routed: `user-manual.md:646`'s now-stale measurement; `market-sim-build-plan.md:11`'s pre-existing CAISO 3 / MISO 3 zone counts; four live-prose six-ISO statements outside every site surface, enumerated in FINDING §6.1a — the grep gate is **zero on the enumerated files and every site surface**, not zero repo-wide) | OPUS · enumerated edits | code | `.gitignore` (`/results/SPP/`), root `index.html` ×3, `README.md:121`, `market-sim-build-plan.md:9`, `docs/codebase-site/policy-scarcity.html` CAISO badge alpha, `js/iso-configs-table.js:32`, `CHANGELOG.md` | — | `FINDING-spp-37-<date>.md` | `git check-ignore results/SPP/x` true; repo-wide "six ISOs" prose = 0 outside historical comments; every badge ≥ 4.5:1 |
| **SPP-42** hydro-2025 repair + RE-BASELINE → keeper-2 candidate (SPP-40 R-8; issued r#7, PRECONDITIONS SPP-36 + SPP-41 landed) — **LANDED 2026-09-07 as `claude/spp-42-coal-hydro` (Fable), chartered as R-7 + R-8 in ONE lane; SPP-41 had NOT landed (verified on `origin/main` 40b54ce7 — no branch, commit or FINDING), so C1/C4-2023 wind stays UNSCORED. SECOND SPP KEEPER `2026-09-07-spp-2-crosswalk-hydro` (bundle `spp42_crosswalk_B`, NOT `spp42_repaired_B`), determination NOT-YET, nothing flipped PASS→FAIL: 2025 unserved 2,007 → 89 MWh, C3a-2025 +21.7 → +7.2 %, C3b-2025 0.283 → 0.189, C5a −67 → −3 %. The 2025 screen's literal "unserved → 0" gate leg was NOT met (89 MWh in SPP-South behind the bound link) and the lane proceeded on rule 14 — FINDING §2.3. NEW routed item: stuck EIA-930 SWPP Demand runs (698 h in 2025). Record `FINDING-spp-42-2026-09-07.md`; log spp-3** | OPUS · a pre-declared recipe (four-keeper precedent) with a pre-declared promotion rule; any ambiguity STOPs and reports | spp | `results/calibration/spp42_repaired_B/` (+ `hourly/`), registry/runs sidecars, `keepers/SPP.json`, `status/SPP.js`, `bench/SPP/`, SPP shard stamp, `docs/calibration-log/spp.md`, `PRECOMMIT-/FINDING-spp-42` | zero-LP: 2023/2024 hydro budgets byte-identical on/off; 2025 budget census (0.02 → ~8.8 TWh); G-DRIFT from keeper-1's `git_sha` naming SPP-36/41 hunks LIVE by design | `FINDING-spp-42-<date>.md` | one `--year 2023 2024 2025` invocation; determination at full magnitude; keeper-1 pruned (rule 15) only if the promotion rule fires; `audit_keepers`, parity, matrix, bench all 0 |
| **SPP-57** Oklahoma pocket — third zone (P1 first lever; issued r#7) — **LANDED 2026-09-07: SCREEN KILLED** (`FINDING-spp-57-2026-09-07.md` §5 — both chain links inert at the union-rated FCITC TTCs; topology NOT landed; design + sidecars + the CSWS split landed for a re-issue with the corridor-only 3,400 MW N↔OK rating and an SPS-tie-based OK↔S rating) | FABLE · topology + two link TTCs are design objects | spp | `_spp_config` (zone + links), `zone_assignment.py` SPP maps, `curate_zonal_shares.py` `_SPP_SUBBA_ZONE_GROUPS` (+ the CSWS sub-allocation), `renewables.py` zone allocation, wind-shape per zone, `basis/meanzero.py` rows, a NEW reduced sidecar of the `oklahoma_internal` flowgate rows, tests; `PRECOMMIT-/FINDING-spp-57` | zero-LP: hub-spread identification (OKC/Tulsa hubs vs North/South) from SPP-14's per-hub parquet; FCITC TTCs by the SPP-53 construction declared BEFORE any limit is read; six keepers' keys unmoved | `FINDING-spp-57-<date>.md` | rule-29 screen on 2025 (largest `oklahoma_internal` footprint), STOP gate with **ex-ante dominance thresholds** (E-6); LOYO; keeper = control; PROMOTION IS A CARD (P15), never the lane's act |
| **SPP-43** re-baseline on the screened wind input (SPP-41 route (b); issued r#8) | OPUS · keeper-2's recipe byte-for-byte, one flag-free re-solve through the landed seam; promotion rule pre-declared | spp | `results/calibration/spp43_screened_B/` (+ `hourly/`), registry/runs sidecars, `keepers/SPP.json`, `status/SPP.js`, `bench/SPP/`, SPP shard stamp, log spp-5, `PRECOMMIT-/FINDING-spp-43`; the "UNSCORED pending SPP-41" lines; `docs/user-manual.md:646` + `market-sim-build-plan.md:11` (SPP-37 N-1/N-2) | zero-LP: table 0b reproduced (only SPP 2023 wind moves, −27 GWh); G-DRIFT from keeper-2's `git_sha 33034499`: the SPP-41 seam LIVE for 2023 only, every other hunk INERT | `FINDING-spp-43-<date>.md` | 2024/2025 objectives IDENTICAL to keeper-2 (the identity the seam predicts); 2023 moves only through wind; C1/C4-2023 wind SCORED for the first time; keeper-1 and keeper-2 pruned at registration (rule 15) if the rule fires |
| **SPP-38** the 15 SPP-era red tests at HEAD (SPP-41 §6/§7f; issued r#8) — **LANDED 2026-09-07** (`FINDING-spp-38-2026-09-07.md`). **Only FOUR of the fifteen were SPP's** (three campaign-config rows + the `isos_missing` set; a fifth row is half SPP's) — the other eleven are three unrelated defects that were red in the same files: a **stale skip guard** left when SCN-WS5A-RESOLVE deleted all sixteen `full_horizon_summary.json` artifacts (`c29f6107`, 5 tests — guard now names the artifact it reads, they SKIP; the SCN-FIX1 fixture tests are untouched and green), an **unbuilt `data/clean`** partition (3 tests, **no edit** — `curate_confirmed_retirements.py` fixes them), and **NYISO marker drift** from nyiso-209 / nyiso-213 (3 tests, incl. 2 that appeared AFTER SPP-41 measured — HEAD was 18 red, not 16). The two SPP REF bases set **four keys each** (mode/iso/start/end), so there is no SPP-specific value and no tuned number. **Rule 22 STOP did not fire**: `test_registration_marker_gate` failed on a hand-kept ISO allowlist, not the gate — `registration_refusals` returns `[]` for all seven committed sidecars, the extra ISO is **NYISO, which holds `complete`**, and SPP has no holdout registration at all; the gate, freeze, markers and tier map are untouched. **2 RED REMAIN and are NOT closable from this lane's files (R-1)**: miso-233 (`caa2936e`) armed `miso_seam_neighbour_{anchored_ladder,hourly_ladder,hourly_spp}` in the MISO keeper with no row in `scripts/lib/forecast_parity_registry.py` — a rule-13 adjudication the MISO desk owes (the sibling `miso_seam_measured_ladder` precedent says BACKCAST_ONLY, but this lane must not write it). Also routed: R-2 restore-or-re-roll the deleted campaign summaries (SCN desk), R-3 build `data/clean` before the gates, R-4 `collate_scenario_campaign.SYSTEM_LABEL` is now false prose (`scripts/`), R-5 annotate SPP-41 §7f's attribution | OPUS · enumerated repairs in the SPP-20 pattern (extend the set, add the seventh config, or DOCUMENT the exclusion) | code | `configs/scenarios/spp_scenario_base_*.yaml` (NEW, cloned from the six in form), the six-ISO assertions in `test_collate_scenario_campaign*`, `test_ff_readiness_battery`, `test_forecast_parity`, `test_registration_marker_gate`, `test_scenario_campaign_configs` | — | `FINDING-spp-38-<date>.md` | `pytest tests/unit/data tests/scoring -q` → 0 failed except the CAISO one (SPP-31 §5e, not ours); `GOLDEN_ISOS`, `program-status.json`, `ff-verdicts.json` UNTOUCHED (W6) |
| **SPP-57b** Oklahoma pocket, re-issue with the constituent sets re-declared ex ante (SPP-57 R-12; issued r#8) — **LANDED 2026-09-07: SCREEN KILLED** (`FINDING-spp-57b-2026-09-07.md` §0 — N↔OK 3,400 (`n_s_corridor` alone) LIVE 23.5 % / 93 % N→OK; OK↔S 10,700 (`sps_tie` alone, OK→S-named by the rule, not the desk's expected 3,000–4,000) NEVER binds because the residual bubble exports INTO Oklahoma in every hour above the median while the ties identify OK→S-loaded — directionally misaligned, no rating fixes it; re-curtailment 0.00 %; unserved 89 → 444 MWh; topology NOT landed; design commit `7bfe047d`; R-17 → SPP-54 re-ranked ahead of any third re-issue) | FABLE · same design objects, the construction corrected on the lane's own evidence | spp | as SPP-57 (cherry-pick `f5926636`), `PRECOMMIT-/FINDING-spp-57b`, the screen bundle (TEMPORARY), `results/calibration/spp57b_okpocket_B/` if the screen clears, the SPP shard cell | zero-LP: N↔OK = `n_s_corridor` set alone = 3,400 MW (already derived, live N→OK-dominant 2,065 h in the killed screen's own flows); OK↔S = `sps_tie` set alone on (p_S − p_OK), derived by the FCITC rule BEFORE any limit is read; `oklahoma_internal` EXCLUDED from both | `FINDING-spp-57b-<date>.md` | same screen year (2025), same STOP gate and thresholds as SPP-57; control keeper-2 for the screen (seam INERT in 2025), keeper-3 for the full span if landed; promotion = card P15 |
| **SPP-44** the CT/CC/ST gas split as a P1-native commitment-bridge question (SPP-42 §7, desk R-q; issued r#8) — **LANDED 2026-09-07: SCREEN KILLED** (`FINDING-spp-44-2026-09-07.md` §4 — the field `spp_gas_commitment_bridge`, four MEASURED plant-basis constants (0.209 / 0.090; 15 / 5 h), the rule-18 gate, matrix row + 7 cells and tests landed default-off with every keeper key unmoved; the 2023 screen against a LIVE-hunk control KILLED on legs (i) CC window agreement 0.694 < 0.76 and (iii) D-4 unit-conduct FAIL at five laid-up plants; the bridge reaches 0.41 TWh of a 4.2 TWh measured committed-state gap because the model never STARTS these plants; cells `spp_gas_commitment_bridge` and `gas_commitment_bridge` U → R; R-17 routes the object to the band channel / a measured commitment-STATE input under a new PRECOMMIT) | FABLE · a mechanism lane: rule-19 enumeration, rule-18 physics gate, a new ISO-exclusive `ScenarioConfig` field with its matrix row | spp | `derive_campd_gas_commitment_params.py --iso SPP` outputs, `ScenarioConfig.spp_gas_commitment_bridge` (default off, drop value preserved), the bridge's SPP branch beside NYISO's, matrix row + a cell in EVERY shard (rule 28c), tests, `PRECOMMIT-/FINDING-spp-44` | zero-LP: the measured CAMPD min-load-when-on and run-length statistics per class; six keepers' keys unmoved (drop-value proof); footprint by year from CAMPD conduct → screen year | `FINDING-spp-44-<date>.md` | rule-29 screen with an ex-ante structural gate (bridged energy lands in the hours CAMPD says the class is on; C8 forced share reported by class; never C1/C3a); promotion = card P15 |
| **SPP-45** forecast-board row re-key + records (gate-(a) F-5; issued r#9) | OPUS · enumerated | code | `frontend/data/forecast/program-status.json` SPP row (`gate.a_keeper_marker` + determination text → keeper-3, the Q34 standing-duty form MISO's re-key lane used), `FINDING-spp-41` §7f annotation (SPP-38 R-5), `FINDING-spp-42` `keeper_previous` note | — | `FINDING-spp-45-<date>.md` | `check_gate_a_provenance.py` 0; nothing else in `frontend/data/forecast/` touched |
| **SPP-58** the second, independent shift-factor identification ψ₂ (issued r#9; SPP-57 R-14, SPP-57b R-19/R-20) | FABLE · an identification design: it must not use the hub-spread × shadow-price regression | spp | `docs/handoffs/spp58/` instruments, `PRECOMMIT-/FINDING-spp-58`, `data/raw/spp-binding-constraints/` sidecar rows if a new extract is needed; `_spp_config` `ttc_mw` ONLY if the pre-declared disagreement band is crossed (then a card) | zero-LP throughout; the declared band and the constituent set fixed before ψ₂ is computed | `FINDING-spp-58-<date>.md` | no solve; six keepers' keys unmoved; the SPS-tie T* width (10,705 vs 3,850) resolved or declared unresolvable |
| **SPP-54** the SPS / Texas-Panhandle pocket as a third zone (P1's second lever; issued r#9: design now, rating + solve after SPP-58) — **LANDED 2026-09-07: DESIGN COMPLETE on design commit `8d427adc`; NO SOLVE** (`FINDING-spp-54-2026-09-07.md` §0 — pocket = NM + a 42-county SPS Texas set, `SPS → SPP-SPS` with no sub-allocation, shares 0.5125 / 0.3616 / 0.1259; census 6.8 GW thermal + 4.65 GW wind vs 3.0–6.4 GW load; the South↔SPS link declared South→SPS-named and NOT in conflict with the bubble balance, rating rule fixed, number waits for SPP-58 ψ₂; R2 = 10,476 MW; the R-18 wind reconciliation passes its identity legs at 6e-16 and **STOPs on C-3 at h8509 (+440 → −545 MW)** — the builder's six-site MEAN LEVEL is load-bearing in the redistribution (North +1.4–1.9 TWh/yr, 75–85 % from the residual South's own sample), routed R-21 to the desk; topology NOT landed on main, solve path restored) | FABLE · topology + one link are design objects | spp | as SPP-57b's file list with `SPP-SPS` in place of `SPP-Oklahoma`; `PRECOMMIT-/FINDING-spp-54`; screen bundle (TEMPORARY) | zero-LP: the SPS bubble census (SPS sub-BA load, 4.65 GW wind, thermal), the measured SPS-vs-residual price table (SPP-57 R-13), the per-zone wind reconciliation SPP-57b R-18 asks for; link direction declared from the sps_tie set's own binding direction | `FINDING-spp-54-<date>.md` | screen year = largest `sps_tie` footprint, named ex ante; STOP gate with the E-6 thresholds; control = keeper-3; promotion = card P15 |
| **SPP-51** priced seams MISO / AECI / ERCOT (P2's forward mechanism; issued r#9) | FABLE · carries SPP-33's R1 anchor map, R2 `HH + basis` correction and the ERCOT 820-vs-±835 clip adjudication | spp | `config/interchange/spec.py` SPP blocks (`hr_by_year`), the neighbour-anchor producer (`derive_neighbor_hr_by_year.py` per-ISO anchor map — SPP-33 R1), tests, SPP shard cell for the seam mechanism, `PRECOMMIT-/FINDING-spp-51` | zero-LP: the offer-array delta of the priced seam vs served; SWPP interchange duration curves by DIBA (SPP-33) as the footprint | `FINDING-spp-51-<date>.md` | A/B served vs `--priced-interchange` on the screen year; STOP gate = modelled interchange duration curve sign/magnitude vs EIA-930; MISO's own seam constants untouched (rule 25); promotion = card P15 |
| **SPP-60** the SPP T1-H recipe + forecast data intake — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-60-2026-09-07.md`; T1-H `spp-2021-2025-realized-t1h-spp60` registered, verdict `spp-t1h` HOLD / FC-3 FAIL at full magnitude; gap table closed: `capacity_actuals_spp.csv` built, `confirmed-retirements/spp.csv` first rows (Tolk 1/2), the 2020-vintage `eia860_generators.parquet` lacked every SWPP row and was extended with the six-BA rows preserved byte-for-byte; `load_forecast/spp.py` already carried a real edition (2025 ITP) — the 2026 ITP vintage is routed) | FABLE · a forecast recipe is a design object; the intake gaps are adjudications | spp | `scripts/lib/load_forecast/spp.py` (a real edition + vintage — manifest row 11), the SPP rows of confirmed-retirement / planned-addition / queue-cap / fuel-trajectory registries, the T1-H hindcast bundle + sidecar via `register_forecast_run.py`, legs (b)/(c) of the SPP board row (after SPP-45), `PRECOMMIT-/FINDING-spp-60` | zero-LP first: the gap table (what T1-H reads vs what SPP has), the load-forecast edition census | `FINDING-spp-60-<date>.md` | backcast keeper untouched; `GOLDEN_ISOS` only if the readiness battery admits it (report, never assert); rule 22: the crossover window is forecast-mode, no measured H1-2026 actuals |
| **SPP-55** VRL-based scarcity (P5's deferred object; issued r#10 once SPP-44's 28c edit merged) — **LANDED 2026-09-07: KILLED AT ZERO LP** (`FINDING-spp-55-2026-09-07.md` — the object is SPP's published Contingency Reserve Demand Curve $275/$550/$1,100 (not the VRLs), registered as the SPP entry of the shared `energy_reserve_coopt` gate with NO new field; keeper-3's reserve-eligible headroom never falls to the 1.5 GW requirement in any measured shortage hour, so the row cannot bind — INERT, cell U → I; 1/0/0 of the C3c hours coincide with reserve shortage; no solve spent, nothing registered) | FABLE · mechanism design: an in-LP reserve demand curve on SPP's own published VRL steps; kill-grading is adjudication | spp | `config/reserve_config.py` SPP entry (requirements + the VRL step curve, every number cited to SPP-12's Exhibit 4-1 / Planning Criteria), ONE new ISO-exclusive `ScenarioConfig` gate if the reserve machinery needs one (default off, drop value declared) + matrix row + a cell in EVERY shard (28c), tests, `PRECOMMIT-/FINDING-spp-55`, screen bundle (TEMPORARY), `results/calibration/spp55_vrl_B/` if the screen clears, the SPP shard cells it moves | zero-LP: rule-19 enumeration (SPP has NO scarcity mechanism, zero slack/dump — price-family §1.3); the measured target (42 / 59 / 68 h > $200 at ordinary load, 79–93× gas); footprint by year from the `spp-or-mcp` RTBM MCP files (hours the spinning MCP sits at/above the $250 VRL step) → screen year | `FINDING-spp-55-<date>.md` | STOP gate structural (the reserve row binds in the measured shortage hours; the price response has the VRL's own order; no non-target flip); never C3c-gated; control = keeper-3; promotion = card P15 |
| **SPP-51…57** | per §4 (SPP-51 → **FABLE** since r#6: it carries SPP-33's R2 anchor correction and an ERCOT limit-vs-clip decision, both adjudications; SPP-58 added — see §8 W5) | spp | one lever each | rule-29 screen, keeper = control | `FINDING-spp-5N-<date>.md` | one PR each; shard cell moves in the same PR (rule 28b) |
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
| 5 | Per-hub SPPNORTH / SPPSOUTH DA + RT hourly 2023–2025 | `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` | **LANDED (SPP-14).** 52,560 rows, `year/hour/zone/rt/da`, 2023–2025, from `portal.spp.org` over anonymous HTTPS; `build_spp_lmp_reference.py --per-hub` run **UNMODIFIED**. **Rule-14 cross-check gate PASS**: the NaN-skipping two-hub mean reproduces the committed `actual_lmp_hourly_SPP.parquet` annual RT means to **0.0000 %** (23.4732/23.3135/27.1112), corr **1.000000**, max abs hourly Δ 0.0001. Default sidecar byte-identical. **P7 mean/p90 \|N−S\| computed** — the 2024 ruling STANDS on both, with the margin and the below-first-place ordering qualified (FINDING §3.3) | SPP-12 → SPP-13 → **SPP-14** | — |
| 6 | SPP hourly load by area (portal `hourly-load`) | `data/raw/spp-hourly-load/` **SALVAGE 2026-09-07 (PR #5342 merged in): 36 monthly `HOURLY_LOAD-YYYYMM.csv` 2023–2025 are ALSO landed here** **COMPLETENESS MEASURED 2026-09-07: 5 of 26,304 hours are absent (0.019 %)** — three DST-transition instants (2023-03-12, 2024-03-10, 2024-11-03) and one real 2-hour publication gap (2023-05-24 03:00–04:00 UTC); 32 of 36 months exact. Files are as-served; a curation step must reindex onto a complete hourly axis rather than assume `days × 24`. Detail: `data/raw/spp-hourly-load/README.md`. — wide format, the 17 sub-BA tokens as columns, `MarketHour` in UTC. The 2023/2024 monthlies are byte-identical members of the two zips above (all 24 verified), kept for a uniform 2023–2025 globbable shape; **do not glob the zips and the CSVs together or 2023–2024 double-counts**. 2025 is monthly-only (no year-zip exists yet). | **SERVED (SPP-14)** — `hourly-load-2023.zip`, `hourly-load-2024.zip` from `portal.spp.org` anonymously. 2025 is not yet a year-zip at SPP (it zips a year ~2 yr on) and is served as 365 daily files on the same route. SPP changed this product's format 2026-03-24 (wide → long); 2023–2025 are wide | SPP-12 → SPP-13 → **SPP-14** | — |
| 7 | SPP generation mix (portal `generation-mix-historical`; wind delivered) | `data/raw/spp-genmix/` | **LANDED COMPLETE 2023–2025 (SPP-14).** `GenMix_2023.csv` / `GenMix_2024.csv` / `GenMix_2025.csv`, 105,120 / 105,408 / 105,120 rows = 365×288 / 366×288 / 365×288 five-minute intervals — **zero missing slots in any year**. These **supersede** SPP-13's v35-sample files under rule 14 (`GenMix_2024_SPP.csv` starts 2024-02-15, 14.4 % missing; `GenMixYTD_SPP.csv` 10.8 % missing, stops 2025-12-16); pruning those two is routed to SPP-DESK. Values are MW, not percentages | SPP-12 → SPP-13 → **SPP-14** | — |
| 8 | DA / RTBM binding-constraint archive (flowgates; P1 evidence + SPP-53 TTC input) | `data/raw/spp-binding-constraints/` **SALVAGE 2026-09-07 (PR #5342 merged in): the roll-ups are now LANDED, not just parsed in-session** — `RTBM-BC-YEARLY-{2023,2024}.csv.zip` + 12 `RTBM-BC-MONTHLY-2025MM.csv.zip`. All 2023–2025 files carry the 10-column schema; the 14-column schema with `Real Time Effective Limit` / `Interconnect` begins 2026-01-28, so SPP-53's measured limit is unobtainable for this window. | **THE SPP-54 vs SPP-57 RANKING NOW HAS ITS MEASURED INPUT (SPP-14).** Whole RTBM archive pulled anonymously (58.7 + 70.1 + 25.0 MB of zips → 1.68 GB of yearly rollups) and parsed in-session; four-group table for 2023–2025 in FINDING-spp-14 §5. **SPP-57 (Oklahoma) > SPP-54 (SPS) on BOTH legs in ALL THREE years, on both membership bases**; SPS also clears the README's own promotion test. Group spec UNCHANGED; membership derived from SPP's own `From Area`/`To Area` codes in the now-landed `Flowgates.csv` (823) + `Temp_Flowgate.csv` (3,298). Payload deliberately not committed (charter: table in the FINDING). ⚠️ **SCHEMA CORRECTION: the served 2023–2025 files have only 10 columns — NO `Real Time Effective Limit`** (it appears from 2026-04), so this archive **cannot** supply SPP-53's limit for the calibration span; SPP-53 stays Tier-3 (FINDING §6) | SPP-12 → SPP-13 → **SPP-14** | — |
| 9 | DA / RTBM operating-reserve MCPs (`da-mcp`, `rtbm-mcp`) — SPP-56 input only | `data/raw/spp-or-mcp/` **SALVAGE 2026-09-07 (PR #5342 merged in): the RTBM MCP annual roll-ups ARE now landed** — `RTBM_MCP_{2023,2024,2025}.csv.zip` — superseding the "deliberately not landed" note above, plus the 365 daily `da-mcp-2025/DA-MCP-2025MMDD0100.csv` files. PR #5342's own `DA-MCP-{2023,2024}.zip` were DROPPED in the salvage: byte-identical to the `da-mcp-{2023,2024}.zip` already here and differing only in filename case, which collides on a case-insensitive filesystem. | **SERVED (SPP-14)** — `da-mcp-2023.zip`, `da-mcp-2024.zip` landed. RTBM MCP reachable on the same route and deliberately not landed (~47 MB/yr, ~141 MB for the span, for a row scoped to SPP-56): `fetch_spp_alt_portal.py --product rtbm-mcp`. 2025 is per-month for both | SPP-12 → SPP-13 → **SPP-14** | — |
| 10 | Wind curtailment (portal or MMU State of the Market annual %) | `data/raw/spp-hsl/spp_wind_curtailment_annual.csv` | **LANDED** from 3 MMU ASOM editions with page cites — avg hourly MW 2019/2022/2023/2024/2025. ⚠️ **SPP publishes no percentage**; the share rows are labelled derived with their formula. Portal `ver-curtailments` (5-min) still blocked | SPP-12 | owner transcribes annual % + page cite |
| 11 | N↔S transfer capability / SPS tie ratings | cited in `_spp_config` | ❌ **SWEPT (SPP-13) — NOT PUBLIC.** ITP Manual v3.3, 2022 20-Year Assessment Report + Manual, and the ITP Postings folder (781 docs) all read: none states an N↔S or SPS-tie MW. The ITP Constraint Assessment transmittals name the interfaces **`SPPSPSTIES` / `SPSNMTIES`** but their ratings are in an NDA/CEII GlobalScape workbook. **Rule 14 governs: SPP-20 registers a Tier-3 reconciled estimate with the misalignment documented** (P11). The measured substitute is the RTBM BC archive's `Real Time Effective Limit` (row 8) | SPP-12 → SPP-13 → SPP-20 | owner with an SPP NDA reads the workbook, or SPP-53 derives it from row 8 |
| 12 | PRM, VRL table, offer cap | `docs/multi-iso/spp-data-audit.md` values table; transcribed in `data/raw/spp-planning/README.md` | **LANDED.** ⚠️ **Two corrections to this row's own premises:** PRM is **16 %** summer East 2026–28 (17 % 2029) + **36–38 % winter**, not 15 %, and East/West carry **separate** BAA PRMs — there is no system-wide SPP PRM. Offer cap is **$1,000/MWh** (the $2,000s are virtual + import/export). Full Exhibit 4-1 VRL table transcribed | SPP-12 → SPP-10 | owner uploads the two PDFs |
| 13 | SPP long-term load forecast (needs a real edition + vintage ≥ 2020 for `load_forecast/spp.py`) | `data/raw/load-forecast/spp/spp.csv` | **LANDED — W2 precondition MET.** 4 `annual_peak_mw` rows (61.7/66.5/69.8/76.4 GW for 2026/2029/2034/2044), edition `2025 ITP` vintage 2025. ⚠️ **SPP publishes no standalone LTLF**; peak only, 4 study years, and the year↔value pairing is a documented chart read | SPP-12 | owner uploads the LTLF — **a W2 PRECONDITION** |
| 14 | Confirmed retirements (SPP-area instruments), NRC licence (Wolf Creek, Cooper), ITP transmission projects | per registry `data/raw/…` | **NRC LANDED** by SPP-12 under the r#2 addendum → `data/raw/nuclear-license-status/spp.csv` (Wolf Creek exp. 2045-03-11 SLR *announced only*; **Cooper exp. 2034-01-18 — inside the horizon — SLR under review, NOT granted**). Confirmed retirements + ITP **NO** | SPP-11 / SPP-12 | owner uploads the ITP project list |
| 15 | Holdout years 2019–2022 of items 1–5 | same paths | ✅ **SERVED for items 1–4 by SPP-15, 2026-09-06** (`docs/handoffs/FINDING-spp-15-2026-09-06.md`): CEMS OK/NE/NM, per-year sub-BA demand, interchange widened to 2019-2025 under a byte-identity proof, delivered gas OK/KS/TX/NM. Rule-22 DATA PREP — **no marker was needed or claimed**, because what is held out is the score, never the data; the *spend* (solve/score/register) remains gated. Item 5 (LMP) is not in SPP-15's scope and stays open behind SPP-12/13/14. | SPP-15 | — |

---

## 7. Hard gates — how this goes wrong

| # | Failure | Wave | Mitigation |
|---|---|---|---|
| G1 | Pin flips half-way: `_ISO_BUILDERS` without `DEMAND_LOADERS` (import-time assert) or the reverse; six-set test; "SPP" unknown-ISO fixture; stale `ci_refactor_guards` entry | W2 | ONE PR; the §2.3 atomicity list is the SPP-20 charter's checklist |
| G2 | Matrix atomicity: base `isos` + shard + `EV_KEY` + html tag + `mech_matrix.py` must land together; a shard missing an id hard-errors; every later lane must emit 7 cell lines | W2, forever | SPP-21 single commit; cross-desk notice; every W3+ charter says "7 shards" |
| G3 | `data-profiles.yaml` token collision (`spp` ⊂ `DAMLZHBSPP_*`) | W2 | delimiter-bounded tokens + a unit test asserting the ERCOT zips stay ERCOT-owned and `SWPP hourly.parquet` is SPP-owned |
| G4 | Solving before outages / benchmarks / zonal shares exist (an un-scorable copperplate) | W3→W4 | SPP-40 PRECONDITIONS: `git log origin/main --grep=SPP-3[012]` all landed |
| G5 | C6: `authorized_price_tuning` must be declared even as NONE; DOF ledger must exist; any band ≠ 1.0 in SPP's generic fallback breaks rule 25 | W4 | charter states it |
| G6 | C3c needs `TAIL_THRESHOLD["SPP"]` in three files and a regenerated `actual_tail.json` | W2 + W3 | three edits in SPP-20; SPP-31 regenerates — **MET 2026-09-07**: `actual_tail.json` carries `thresholds.SPP = 200.0` and SPP 2023–2025 (RT >$200: 42 / 59 / 68 h) |
| G7 | `test_iso_coverage` sweeps: `QUEUE_CAP_PER_TECH_GW["SPP"]`, carbon-`None` path, and "if `IMPORT_TRANCHES["SPP"]` then `IMPORT_ZONE["SPP"]`" | W2 | no import node ⇒ neither key ⇒ `build_import_generators("SPP") == []` (the ERCOT/MISO branch) |
| G8 | **Six keepers' cache keys move** (a new `ScenarioConfig` field, a default flip, a `results/cache.py` edit) | W2, W3-32 | forbidden through W4; wind shape via set membership not a field; byte-identity proof is SPP-20's exit; G-DRIFT audit in SPP-32 |
| G9 | Shared regenerated files (`actual_tail.json`, `actual_amplitude.json`, `eia_demand_profiles.parquet`) alter other ISOs' rows | W3-31 | non-SPP diff = ∅ as an exit check; last commit after rebase — **MET 2026-09-07 and now STRUCTURAL**: `build_reference()` MERGES instead of replacing (new `--isos` flag), so an ISO not built keeps its committed block byte-for-byte and a future ISO-addition lane physically cannot move another ISO's rows. Verified three ways (committed vs HEAD-rebuild vs SPP-31), which is what separated the two PRE-EXISTING drifts (CAISO renewables, ERCOT amplitude) from this lane — see `FINDING-spp-31-2026-09-07.md` §4 |
| G10 | Neighbour-name collision in `_HR_GAS_ELASTIC` | W2 | names `MISO` / `ERCOT` + uniqueness assert |
| G11 | `run_isos_concurrent.py` KeyError; `calibration-solve.yml` dropdown lacks SPP | W2 | in SPP-20 |
| G12 | `load_forecast/spp.py` cannot register without a real edition/vintage (`test_specs_declare_an_edition_and_a_vintage`) | W1→W2 | manifest row 13 is a W2 PRECONDITION |
| G13 | Screen bundle left in `results/calibration/` → parity gate RED (29c) | W4 | "delete before merge" line |
| G14 | Live writers on the same dicts (capx D-lanes on `capacity_market.py`; SCN on `constants.py` load dicts; miso-230 on `interchange/spec.py`) | W2 | append-last + rebase-last; desk collision check at issuance (ledger §4) |
| G15 | Desk grades a lane LOST on absence; reads green CI as proof (the matrix guard is not merge-blocking) | desk | handoff §0 |
| G16 | SPP appears on the forecast board before W6, or anyone but the capx director writes it | W2+ | MUST-NOT-TOUCH line in every charter |
| G17 | CI sparse checkout (`ci.yml:467-534`) lacks an SPP raw path a unit test reads | W3 | tests use tmp-`CLEAN_DIR` fixtures; a raw path needed ⇒ same PR, Opus/Fable (workflow edit) |
| G18 | portal.spp.org anonymous access withdrawn (measured 2026-09-06: listings `[]`, downloads 404 — an `X-SPP-UI-Token` requirement, FINDING-spp-12 §2) | W1→W2 | SPP-13 probes the FTP public-data route SPP's reference guide names; the working request grammar is recorded in the builder's docstring; fallback = manual rows with the exact calls (FINDING-spp-12 §8) |
| G19 | A `DATA PROFILE: code` session running `pytest tests/unit/data tests/scoring` sees three `integration` tests red for an unbuilt `data/clean`, and a cold first pass of `tests/curation` can report a spurious failure that does not reproduce warm (SPP-38 §5 R-3 — how SPP-41 §7f mis-attributed eleven tests) | every lane | build `data/clean` (`scripts/regenerate_clean.py`) before running the gates, and read a first-pass curation failure as cold-start until re-run |

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

#### SPP-12 ADDENDUM (issued r#2, 2026-09-06 — paste into the RUNNING SPP-12 session; it widens the FINDING, never the file set)

```
SPP-12 ADDENDUM from SPP-DESK (r#2). Two additions, both inside your existing charter's spirit:
(A) NRC LICENCE STATUS — Wolf Creek (EIA 210, KS) and Cooper (EIA 8036, NE): fetch the licence
    expiry / renewal status from the NRC info-finder into data/raw/nuclear-license-status/spp.csv
    in the SAME unified-CSV shape as the six existing ISO files there (+ a SOURCES row). SPP-11
    routed this to the desk because neither lane owned the path; it is yours now. The spec module
    scripts/lib/nuclear_license_status/spp.py stays SPP-20's.
(B) BINDING-SHARE TABLE — add a FOURTH flowgate group. Card P1 was RULED "2 zones now; two ranked
    levers": the SPS/Texas-Panhandle pocket (SPP-54) AND an Oklahoma pocket (SPP-57) are both
    pre-declared, and YOUR table ranks them. Groups: N↔S corridor · SPS-tie · OKLAHOMA-INTERNAL
    (Osage–Webber Tap, Russett–South Brown, the OKC/Tulsa FCA flowgates — audit §6.1 names them)
    · other. Report per year: share of RT binding hours AND mean shadow price per group.
(C) P7 CONFIRMATION — report mean and p90 |SPPNORTH − SPPSOUTH| per year explicitly; the desk ruled
    2024 the screen year on the MMU's published +$12 on-peak DA spread, and your hourly number
    overrides it if it disagrees. Say so in one line in your FINDING.
Everything else in your charter is unchanged. Rule 13/14/23/27/28 as issued.
```

#### SPP-13 `[OPUS]` — the FTP public-data route + the N↔S transfer capability (chartered r#3 under ruling P11)

```
You are lane SPP-13. MODEL: Opus claude-opus-5 — a transport probe and a document sweep against a
fixed list; you choose nothing, you record what each route returns. DATA PROFILE: shared.
Branch stem: claude/spp-13-portal-ftp-ttc-h2vk.
Read CLAUDE.md freshly and in full; docs/multi-iso/spp-addition-plan-2026-09.md §2.4, §3 P1/P11 (as
ruled), §5 row SPP-13, §6 rows 5–9 and 11; docs/handoffs/FINDING-spp-12-2026-09-06.md IN FULL (§2 the
verified request grammar and the UI-token diagnosis; §5 the four-group binding-share spec; §6 the
document candidates for row 11; §8 the exact blocked calls); data/raw/spp-planning/README.md and the
System Interfaces Stakeholder Reference Guide it tracks (the "FTP for the programmatic retrieval of
Public Data" sentence and the "SPP Public Data Access" guide it names);
scripts/data/build_spp_lmp_reference.py (--per-hub exists, fixture-tested, never run live);
data/raw/spp-binding-constraints/README.md (the grouping you must NOT change — it was fixed before the
data so it cannot be fitted to the answer, rule 1).

PRECONDITIONS: SPP-12 LANDED (PR #5285). Parallel with SPP-20 and SPP-21; you own no file they own.
FILES YOU OWN: payload files under data/raw/spp-hourly-load/, spp-genmix/, spp-binding-constraints/,
spp-or-mcp/, spp-hsl/ (each dir already has README + SOURCES from SPP-12 — append rows, never rewrite);
data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet (NEW, via --per-hub, ONLY if the LMP
monthly files are reachable; the default single-hub parquet must stay byte-identical — prove it);
data/raw/spp-planning/ (new transcriptions + README rows for row 11);
scripts/data/build_spp_lmp_reference.py ONLY to add an FTP transport behind a flag, if the route works
(Edit tool, exact bytes, ≥300 lines — fetch-back verify; default behaviour unchanged).
FILES YOU MUST NOT TOUCH: src/; configs/; tests/; any SPP-20 or SPP-21 file; docs/multi-iso/spp-data-audit.md.

TASK, in this order:
(1) FTP ROUTE (zero data first): locate the "SPP Public Data Access" reference guide on www.spp.org
    (Stakeholder Center > User Guides, APIs & Integrations > Technical Reference Documents > Public
    Data); read the FTP host, path layout and whether anonymous access is offered. Probe ONE listing.
    Record the exact host/path/credential requirement and the status in the FINDING. If the route
    needs credentials the repo does not hold, STOP the payload items and go to (3).
(2) IF THE ROUTE IS OPEN — pull, 2023–2025, in this priority: (a) DA + RTBM monthly LMP by settlement
    location → run build_spp_lmp_reference.py --per-hub → actual_lmp_hourly_zonal_SPP.parquet; report
    mean and p90 |SPPNORTH − SPPSOUTH| per year (P7: the 2024 ruling stands unless this number
    disagrees — say which); (b) da-binding-constraints + rtbm-binding-constraints → compute, in the
    FINDING only, per year: share of RT binding hours AND mean shadow price while binding for the four
    groups the README fixes (n_s_corridor · sps_tie · oklahoma_internal · other) — THIS RANKS SPP-54
    vs SPP-57 under ruling P1; (c) hourly-load by area; (d) generation-mix-historical; (e) da-mcp /
    rtbm-mcp. Every payload lands raw and immutable with a README row (schema, span, timezone) and a
    SOURCES row. Binary files by git push, pack-sized commits.
(3) ROW 11 — the N↔S transfer capability and the SPS tie ratings, from www.spp.org (fully reachable):
    sweep, in order, the ITP Manual v3.3 (/Documents/77209/), the 20-Year Assessment Report
    (/Documents/69814/) and its Manual (/Documents/59716/), then the ITP Postings folder (?id=31491).
    Transcribe any transfer-capability / interface-rating table with page cites into
    data/raw/spp-planning/ (+ README row). If none states an N↔S MW figure, say so per document —
    SPP-20 then registers a Tier-3 reconciled estimate with the misalignment documented (P11).
Every blocked URL → the blocked table with status. No value from memory; no derived percentage
without its formula and `derived=yes`.
RULES THAT BITE: 1 (the grouping is fixed before the data), 13, 14, 23, 26, 27 [R-PUSH], 28 (no
cell moves).
EXIT: docs/handoffs/FINDING-spp-13-<date>.md with: the route table (host, credential requirement,
status per product); the per-hub spread table (or "not obtainable — <reason>"); the four-group
binding-share table (or the same); the row-11 result per document; the residual manual manifest.
Plan §5 row → LANDED; §6 rows 5–9/11 statuses updated in the same PR. Report to the owner: the route
verdict first, then the SPP-54/57 ranking if you have it.
Push by pack size (CLAUDE.md Git & Pushing); fetch-back verify every pushed file ≥300 lines; no CI
workflows; no default moves; if you must touch a file outside your regions, STOP and route to
SPP-DESK in your FINDING.
```

#### SPP-14 `[OPUS]` — alternative HTTPS sources for SPP LMP / binding constraints / load / gen-mix / MCP (chartered r#4 under ruling P12)

```
You are lane SPP-14. MODEL: Opus claude-opus-5 — a source sweep against a fixed candidate list with a
fixed cross-check; you choose nothing, you record what each source serves and whether it reproduces
SPP's own published figures. DATA PROFILE: shared.  Branch stem: claude/spp-14-alt-sources-w6dp.
Read CLAUDE.md freshly and in full (rules 13, 14, 23, 27); docs/multi-iso/spp-addition-plan-2026-09.md
§3 P12 (as ruled), §5 row SPP-14, §6 rows 5–9; docs/handoffs/FINDING-spp-13-2026-09-06.md IN FULL (§1
the FTP folder/file grammar and the verified product SCHEMAS — a third-party copy must match them;
§3 the four-group binding-share spec; §5 what already landed from the v35 sample zip);
docs/handoffs/FINDING-spp-12-2026-09-06.md §4 (the ASOM annual hub means — your cross-check);
data/raw/spp-binding-constraints/README.md (grouping fixed before the data — never change it);
scripts/data/build_spp_lmp_reference.py (its parse of the monthly-SL wide format; the committed
system-hub parquet's annual RT means are $23.47 / $23.31 / $27.11 for 2023/24/25).

PRECONDITIONS: SPP-13 LANDED (PR #5314). Parallel with SPP-20 (RUNNING — touch none of its files).
FILES YOU OWN: NEW data/raw/spp-lmp-alt/ (payloads + README + SOURCES); README/SOURCES rows appended
under data/raw/spp-binding-constraints/, spp-hourly-load/, spp-genmix/, spp-or-mcp/ (+ payloads there
if a source serves the SAME product SPP publishes, byte-comparable to the schemas SPP-13 recorded);
data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet ONLY under the gate below.
FILES YOU MUST NOT TOUCH: src/; configs/; tests/; scripts/ (except a NEW scripts/data/fetch_spp_alt_*.py
producer if a source is reproducible — never edit build_spp_lmp_reference.py); actual_lmp_hourly_SPP.parquet;
any SPP-20 file; docs/multi-iso/spp-data-audit.md.

TASK — sweep, in this order, and STOP at each on a documented refusal:
(1) gridstatus.io hosted API (https://api.gridstatus.io — HTTPS; check whether a key-free tier exists
    and what its row limits are; datasets of interest: SPP day-ahead hourly LMP by location, SPP RT
    LMP (5-min and hourly), SPP binding constraints, SPP load by area, SPP fuel mix, SPP reserve
    MCPs). Record the licence terms verbatim; a source whose terms forbid redistribution lands as a
    DERIVED sidecar only (the parquet), never the raw pull.
(2) The open-source `gridstatus` Python package's SPP client: read its source for the endpoints it
    hits; if any is an HTTPS host other than portal.spp.org / pubftp.spp.org, probe it.
(3) LCG Consulting EnergyOnline (https://www.energyonline.com — public SPP LMP pages), and any other
    HTTPS mirror that republishes SPP's monthly-SL or daily-BC files verbatim (search spp.org's own
    CDN/S3 hostnames referenced in the portal bundle main.*.js; Kaggle/Zenodo/GitHub mirrors of
    "SPP LMP" 2023–2025 — cite the uploader and the file hash).
(4) The SPP MMU: any ASOM appendix, quarterly or monthly report on www.spp.org that tabulates hub
    prices at monthly or finer grain (a monthly N/S spread series is a partial substitute for P7's
    mean; it can NOT substitute for the p90 — say so).
(5) EIA / FERC: confirm and record that neither publishes SPP LMP or flowgate data (one line each).
CROSS-CHECK GATE (rule 14, before any landed LMP series is used for anything): rebuild the system
hub as the NaN-skipping mean of SPPNORTH_HUB and SPPSOUTH_HUB on the model's 8760 local calendar and
compare to the committed actual_lmp_hourly_SPP.parquet: annual RT mean within 1 % AND hourly
correlation ≥ 0.999 for each of 2023–2025. A series that fails is landed as evidence with the
mismatch stated and is NEVER promoted to actual_lmp_hourly_zonal_SPP.parquet. A series that passes
→ write the per-hub parquet (year/hour/zone/rt/da, zone = SPPNORTH_HUB / SPPSOUTH_HUB) and report
mean and p90 |N − S| per year (P7: the 2024 ruling stands unless this disagrees — say which).
BINDING CONSTRAINTS: if any source serves SPP's RTBM daily BC files (14-column schema, FINDING-spp-13
§3), compute per year, in the FINDING only, share of RT binding hours AND mean shadow price while
binding for the four fixed groups (n_s_corridor · sps_tie · oklahoma_internal · other) — this ranks
SPP-54 vs SPP-57 under ruling P1 — and note the `Real Time Effective Limit` distribution on the
N↔S-corridor flowgates for SPP-53.
Every blocked or licence-refused source → the table with status and the verbatim terms. No value from
memory; no derived percentage without its formula and `derived=yes`.
RULES THAT BITE: 1 (the grouping is fixed), 13 [R-MEASURED] (a third-party copy is admissible only as
SPP's own published series, reproduced — hence the gate), 14, 23, 26, 27 [R-PUSH] (binary payloads by
git push in pack-sized commits; any new producer script < 300 lines or fetch-back verified), 28 (no
cell moves).
EXIT: docs/handoffs/FINDING-spp-14-<date>.md with: the per-source table (host · product · span ·
licence · reachable · reproduces?); the cross-check table; the per-hub spread table (or "not
obtainable — <reason>"); the four-group table (or the same); the residual manifest. Plan §5 row →
LANDED; §6 rows 5–9 statuses updated in the same PR. Report to the owner: which rows now have a
reachable source, first.
Push by pack size (CLAUDE.md Git & Pushing); fetch-back verify every pushed file ≥300 lines; no CI
workflows; no default moves; if you must touch a file outside your regions, STOP and route to
SPP-DESK in your FINDING.
```

#### SPP-14 ADDENDUM (issued r#4 am.1 — paste into the SPP-14 session; widens the file set by three measured files)

```
SPP-14 ADDENDUM from SPP-DESK (r#4 am.1). FINDING-spp-13 §5 found three measured files in SPP's own
v35 guide zip on www.spp.org (HTTPS, reachable — the zip URL is in data/raw/spp-planning/SOURCES.md)
that SPP-20 and SPP-32 can consume. Land them raw under data/raw/spp-planning/ with README + SOURCES
+ SHA256SUMS rows, as its own commit BEFORE the sweep in your charter:
(A) SL_to_Pnode_to_Zone_with_Area.csv (~32 MB) — every settlement location → NODE_AREA → reserve
    zone: the measured SL→area map for SPP-20's sub-BA/zone grouping and SPP-32's zonal shares.
    One commit by git push; if the pack exceeds the remote's limit, gzip it and say so in the README.
(B) Hub_Definitions.csv — the SPPNORTH_HUB / SPPSOUTH_HUB node weightings: the exact definition of
    the two hubs the committed price benchmark is built from (SPP-40's PRECOMMIT cites it for the
    "two-point spread" limitation).
(C) TieFlows_Sep2025.csv — one month of 1-minute tie flows by neighbour: SPP-33/51 seam evidence.
In your FINDING, add one table: for (A), the count of settlement locations per NODE_AREA and which
EIA-930 sub-BA token each area maps to (a join key SPP-32 will need — report, do not decide).
Everything else in your charter is unchanged.
```

#### SPP-15 `[OPUS]` — back-year intake 2019–2022 of the SPP-11 products (chartered r#4 am.1; rule-22 data prep)

```
You are lane SPP-15. MODEL: Opus claude-opus-5 — the SPP-11 recipe re-run on four earlier years; you
make no design choice. DATA PROFILE: shared.  Branch stem: claude/spp-15-backyears-q3nf.
Read CLAUDE.md freshly and in full — rule 22 [R-HOLDOUT] entire, and especially "WHAT IS HELD OUT IS
THE SCORE, NEVER THE DATA": data intake needs no per-ISO/per-window marker; only SOLVING, SCORING or
REGISTERING an out-of-training year is the spend. You do none of those. docs/multi-iso/
spp-addition-plan-2026-09.md §5 row SPP-15, §6 row 15; docs/handoffs/FINDING-spp-11-2026-09-06.md IN
FULL (the four producers, their flags, the schema checks, the sub-BA naming and span-boundary
lessons); data/raw/campd-unit-level/README.md (the holdout-intake row convention SPP-11 added);
data/raw/zone-specific-demand/MISO/ (the per-year back-file shape: miso_subba_demand_2019.csv …
_2022.csv — mirror it for SPP); the producers' docstrings.

PRECONDITIONS: SPP-11 LANDED. Parallel with SPP-20 (RUNNING) and SPP-14 — you own no file they own.
The owner's dispatch of this charter is the explicit authorization the fetcher's --holdout-intake
flag records; cite this charter (plan §8 SPP-15, r#4 am.1) in every README row you add.
FILES YOU OWN: data/raw/campd-unit-level/{OK,NE,NM}_{2019,2020,2021,2022}.parquet (12 files) + README
rows (WY is NOT in the SPP footprint — audit §2.4 — do not fetch it); data/raw/zone-specific-demand/
SPP/spp_subba_demand_{2019,2020,2021,2022}.csv (per-year files, the MISO shape) + SOURCES rows;
data/raw/eia-930-interchange/"SWPP interchange hourly.parquet" WIDENED to 2019–2025 (the producer
rewrites the file: prove the 2023–2025 rows are byte-identical to the committed file before and after
— row count, sha256 of the 2023–2025 slice — and record both in the FINDING; if the producer cannot
widen without touching the committed rows, land a SEPARATE "SWPP interchange hourly 2019-2022.parquet"
and say so); data/raw/gas-prices/eia_delivered_gas_{OK,KS,TX,NM}_monthly_2019-2022.csv + SOURCES rows.
FILES YOU MUST NOT TOUCH: any existing raw file except the interchange parquet under the proof above;
src/; configs/; tests/; scripts/ (the producers are used as-is; if one cannot serve a back year
without a code change, STOP that item and record it — do not edit the producer).

TASK, in this order, each its own small commit, pack-sized (git push; never push_files a parquet):
(1) CEMS: for Y in 2019 2020 2021 2022: python scripts/data/fetch_campd_unit_level.py --year Y
    --states OK NE NM --holdout-intake SPP. Verify schema == KS_2024.parquet for each; rows /
    facilities / units per file in the FINDING; README rows in SPP-11's convention.
(2) SUB-BA DEMAND: fetch_eia930_subba_demand.py --iso SPP --years 2019 … 2022, one file per year (NO
    --combine — mirror MISO's back-year files). NOTE the EIA API's own coverage of this product starts
    2019-01-01 (the producer docstring) — 2019 may be partial; report the first stamp. The 2026 sub-BA
    renaming does not bite a back year (the producer writes each year in its own era's naming — say
    which naming each file carries). Cross-check Σ sub-BAs vs the BA Demand column of
    "SWPP hourly.parquet" per year (SPP-11 §3.3 got 0.9995–0.9999).
(3) INTERCHANGE: fetch_eia930_interchange.py --ba SWPP --source bulk --years 2019 2020 2021 2022
    (+ 2023 2024 2025 if the producer only writes a whole file) under the byte-identity proof above.
    DIBA duration summary per year in the FINDING (same table shape as SPP-11 §4.1).
(4) GAS: the dnav workbook route SPP-11 used (hist_xls/N3045<ST>3m.xls) for 2019–2022; the same
    N3045OK3 gap SPP-11 hit may recur — record it, never fill it.
Anything that returns 403/404 or an empty body: the blocked table with the exact URL and status. No
value from memory. No solve, no score, no registration, no calibration-complete.json edit, no
touchpoint stamp — this lane produces INPUTS and nothing that reads them.
RULES THAT BITE: 13, 14, 22 (data prep is unrestricted; the spend is not yours), 23, 26, 27 [R-PUSH].
EXIT: docs/handoffs/FINDING-spp-15-<date>.md with the got/blocked table, per-file schema/row checks,
the sub-BA completeness ratios per year, the interchange byte-identity proof, and the DIBA summaries;
plan §5 row → LANDED; §6 row 15 → served. Report to the owner: which of {OK, NE, NM} × {2019–2022}
landed, first.
Push by pack size (CLAUDE.md Git & Pushing); fetch-back verify every pushed file ≥300 lines; no CI
workflows; no default moves; if you must touch a file outside your regions, STOP and route to
SPP-DESK in your FINDING.
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
RULINGS APPLIED (r#2, 2026-09-06 — ledger §2 P1–P9 are verbatim and BIND this lane):
- P1: zones = SPP-North / SPP-South. State map per audit §5 rows 4/5: North = ND SD NE MN MT IA KS
  MO CO; South = OK TX NM AR LA; **WY is NOT in the footprint** (no SWPP plant — audit §2.4);
  campd.ISO_STATES["SPP"] = ("AR","CO","IA","KS","LA","MN","MO","MT","ND","NE","NM","OK","SD","TX").
  Sub-BA grouping for load shares: North = EDE INDN KACY KCPL LES MPS NPPD OPPD SECI SPRM WAUE WR;
  South = CSWS GRDA OKGE SPS WFEC (EDE straddles at 1.8 % — state which side and why).
  PRM 0.15 (Planning Criteria Rev 4.1A §4, audit row 1); voll 2000 (Order 831, row 2);
  STATE_RPS_FLOORS["SPP"] all-zero on the ERCOT precedent with the real row routed to the forecast
  lane (row 13) and no ACP (row 14); _EGRID_VINTAGE is a shared scalar — no SPP entry (row 17).
- P2/P3: INTERFACE_NEIGHBORS["SPP"] = MISO + AECI + ERCOT (820 MW, border SPP-South), all
  DEFAULT-OFF; _SCALAR_INTERCHANGE_ISOS += "SPP" (served schedule, positive = net export).
- P4/P5: no reserve spec, no scarcity seed. P6: TAIL_THRESHOLD["SPP"] = 200 in all three files.
- D79 (landed after this charter was written): add "SPP" to config/solve_surface.py::SURFACE_ISOS
  in the SAME commit as _ISO_BUILDERS (test_solve_surface pins the two tuples equal); run
  `uv run python scripts/solve_surface_register.py --diff origin/main HEAD` and record ZERO moved
  rows for the six ISOs in the FINDING; `--declare` the names whose SPP projection is new.
- State in the FINDING that `_screen_demand_spikes` now fires on SPP 2023 (the 100× hour) and on no
  other ISO, so its docstring's "no-op on every training year" promise needs the SPP exception
  written in (audit §3.4). Do NOT add a low-side screen (P9 routed it).
RULINGS APPLIED (r#3, 2026-09-06 — from FINDING-spp-12 and cards P10/P11; where these differ from the
r#2 block above, THESE WIN):
- P10: voll = 2000.0 — the Order 831 cost-verified ceiling. The comment MUST cite both numbers:
  SPP's posted Safety-Net Energy Offer Cap is $1,000/MWh (Market Protocols 119 §8.2.5 pp. 356–357);
  $2,000 is the hard ceiling for cost-verified offers. SPP-55 revisits against the VRLs.
- PRM: PLANNING_RESERVE_MARGIN_BY_ISO["SPP"] = 0.16 — the live East BAA summer Base PRM (Planning
  Criteria v5.0A §4 p. 10; 17 % from 2029; winter 36 %/38 %; the West BAA is 19 %/40 % and is NOT
  the RTO footprint this model represents). The constant is consumed only by the forecast-lane
  adequacy floor, so the live vintage is the right one; cite the PY2023–25 15 % (Rev 4.1A) as
  history in the comment. If the registry carries a winter leg for any ISO, populate SPP's too.
- N↔S TTC (P11): if FINDING-spp-13 has landed a transfer-capability figure, use it and cite it. If
  not, register a TIER-3 RECONCILED ESTIMATE with the misalignment documented in the comment and in
  docs/parameter-citations.md, and open it as a root-cause item in your FINDING (rule 14; doc 04
  "all link MW start Tier 3 — verify"). Do NOT block the PR on it. State the basis; the MMU's
  ">6,000 MW SPP↔MISO AC interties" is a SEAM number, not the internal corridor — do not borrow it.
  The TransferLink is symmetric by construction, which is right: the MMU records the hub spread
  REVERSING sign for 6–8 months of 2025 (north-hub congestion).
- LTLF: data/raw/load-forecast/spp/spp.csv carries FOUR annual_peak_mw rows (2026/2029/2034/2044,
  edition "2025 ITP", vintage 2025, a chart read — SOURCES.md caveat). scripts/lib/load_forecast/
  spp.py must interpolate between them and DECLARE the interpolation (piecewise-linear on peak;
  say so in the module docstring and the registry row); no energy series exists — say so.
  DEMAND_GROWTH_RATES["SPP"] follows (peak CAGR ≈ 1.2 %/yr is a DERIVATION — label it).
- NRC: scripts/lib/nuclear_license_status/spp.py over the landed data/raw/nuclear-license-status/
  spp.csv (Wolf Creek 2045-03-11; Cooper 2034-01-18 — inside the horizon, SLR under review).
- transmission_expansion/spp.py: the 2025 ITP Assessment Report project list (§4.6, §7.3.9, Table
  7.1) is the source; TRANSMISSION_BASE_STATIC_VINTAGE["SPP"] = 2025 (the ITP vintage) unless the
  TTC source SPP-13 finds carries a different one — cite whichever you use.
- COLLISIONS at issuance (r#3 pin 992760ec): capacity_market.py last written 17:11 UTC (capx D75-R),
  constants.py 21:39 (D75-R facade), interchange/spec.py 21:34 (miso-231 seam ladder), iso_configs.py
  21:58 (capx D75-R-ARM). capx D76 / D78 / D81 and miso-232 are LIVE. Append-last, rebase-last; if a
  rebase shows one of these dicts changed under you, re-append and re-run the byte-identity proof.
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
of scripts/data/derive_campd_unit_outages.py, derive_thermal_tranches.py,
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
2025 → derive_thermal_tranches.py --iso SPP →  [r#6: derive_cc_committed_pct.py REMOVED — ERCOT-only legacy, FINDING-spp-30 §5] →
scripts/tag_mixed_plants.py → build_offer_curve_overrides.py. GATES: window count > 0 in every CEMS state
incl. OK and NE; ZERO full-year fallbacks (a unit falling to the fallback is reported by unit with
the reason); the committed-% and tranche distributions summarised by class vs MISO's as a sanity
band (report, never tune). Every output header cites source + method + the CEMS vintage.
RULINGS APPLIED (r#5, 2026-09-07): SPP-20 LANDED (PR #5329) — get_iso_config("SPP") is live (2 zones,
SPP-North 0.5125 / SPP-South 0.4875); campd.ISO_STATES["SPP"] is the 14-state list. SPP-15 landed
2019–2022 CEMS for OK/NE/NM — derive the TRAINING years only (--years 2023 2024 2025) per this charter;
the back years are a later intake batch, not yours. The legacy-binning fleet SPP-20 built is 1,012
thermal units / 56,036.9 MW; your tranche outputs are what move SPP-40 onto the per-plant CAMPD path.
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
P9 (RULED r#2): the committed SWPP hourly file carries a 100× unit slip at 2023-06-12 21:00 that
inflates NG: WND by ~3.59 TWh. When you build the generation benchmark, apply the SAME median-ratio
test _screen_demand_spikes uses (2.5× the annual median) to every NG: column and interpolate the
flagged hour — inside the benchmark builder, never in data/raw. PROVE the six registered ISOs'
benchmark blocks are byte-identical afterwards (they have no such hour). Report the 2023 SWPP wind
TWh before and after. The two LOW-side demand hours (2025-06-21 05:00, 2024-07-19 00:00) are NOT
yours — routed to the audit track; list them in the FINDING as known artifacts only.
RULINGS APPLIED (r#5, 2026-09-07): SPP-20 LANDED; TAIL_THRESHOLD["SPP"] = 200 exists in all three files.
SPP-14 LANDED the per-hub parquet data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet
(52,560 rows; zone = SPPNORTH_HUB / SPPSOUTH_HUB — hub names, NOT model zones; cross-check gate passed
byte-identical) and Hub_Definitions.csv under data/raw/spp-planning/ (the node weightings of the two
hubs). Build actual_lmp.json's SPP zonal entries FROM the per-hub parquet, keyed by hub name, and state
in the block's comment field that a hub is a node cluster (Nebraska / central Oklahoma), not a zone
average — SPP-40's PRECOMMIT cites this. ALSO YOURS (routed by SPP-14): the README row for the new
parquet in data/raw/_validation-source/README.md.
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
RULINGS APPLIED (r#5, 2026-09-07): SPP-20 LANDED with the P1 zone grouping (North = EDE INDN KACY KCPL
LES MPS NPPD OPPD SECI SPRM WAUE WR; South = CSWS GRDA OKGE SPS WFEC; load shares 0.5125 / 0.4875 from
SPP-11's sub-BA energy). THREE MEASURED INPUTS LANDED SINCE YOUR CHARTER — use them, cite them: (a)
data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv + the NODE_AREA ↔ EIA-930 sub-BA join table
(FINDING-spp-14-2026-09-06.md §8) — the measured settlement-location → area map; state which side any
straddling area (EDE) lands on and why; (b) data/raw/spp-hourly-load/HOURLY_LOAD-YYYYMM.csv ×36 (SPP's
own hourly load by control zone, UTC; the control zones ARE the sub-BA tokens) — cross-check the EIA-930
sub-BA shares against it per year and report the max hourly divergence; (c) data/raw/spp-genmix/
GenMix_{2023,2024,2025}.csv (complete 5-minute wind delivered = WIND_MKT + WIND_SELF, UTC) — the
reconciliation target for the NASA-POWER wind shape AND, with data/raw/spp-hsl/
spp_wind_curtailment_annual.csv (ASOM average hourly curtailment MW), BOTH legs of the reference
curtailment rate are now measured: rate_y = curtailed_MWh / (delivered_MWh + curtailed_MWh), derived=yes
with the formula — register it for SPP in the uncurtailed-fallback set with the citation. ALSO YOURS
(routed by SPP-20 R-2, one word): data/raw/load-forecast/spp/spp.csv `basis=coincident` is outside the
datatype vocabulary {net, gross, unspecified} and makes parse_iso("SPP") raise — correct it to
`unspecified`, add a SOURCES note, and prove `curate_load_forecast.py` runs for SPP.
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
RULINGS APPLIED (r#5, 2026-09-07): SPP-20 LANDED INTERFACE_NEIGHBORS["SPP"] = MISO + AECI + ERCOT, all
default-off, anchored (MISO) on the West+South ZONAL rows of actual_lmp_hourly_zonal_MISO.parquet.
SPP-20 R-7: derive_neighbor_hr_by_year.py's _NEIGHBOR_LMP_ISO maps neighbour "MISO" to the MISO SYSTEM
file, not the zonal anchor the registration names — derive against the anchor SPP-20 registered; if the
producer cannot without a src/scripts change, STOP that item and route it (never edit the producer).
SPP-15 widened the SWPP interchange parquet to 2019–2025 (2023–25 rows byte-identical) — derive the
training years only. SPP-14 landed data/raw/spp-planning/TieFlows_Sep2025.csv (one month of 1-minute
tie flows by neighbour): use it ONLY as a sign/magnitude sanity check on the EIA-930 DIBA series. Note
for SPP-51: miso-233 (MISO lane) has since registered `miso_seam_neighbour_hourly_spp` on MISO's side —
a MISO object, rule 25; cite, never edit.
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
RULINGS APPLIED (r#5, 2026-09-07): SPP-20 LANDED — get_iso_config("SPP") drives iso-topologies.json now.
FOUR ROUTED ITEMS FROM FINDING-spp-20 §5 ARE YOURS: R-3 the parameter registry — `scripts/validate_
parameters.py` reports +33 uncited rows, exactly the new SPP rows; regenerate / cite them in
docs/parameter-citations.md (every SPP value with its audit-§5 citation) and report the before/after
count; R-4 `scripts/hydrate_data.py` split-child exact match — a split-directory child named exactly
`SPP` / `spp` (zone-specific-demand/SPP, load-forecast/spp) is not claimed by the substring tokens: add
exact-name matching for split children + a unit test (hydrate_data.py is ~400 lines: Edit tool,
fetch-back verify); R-5 docs/multi-iso/00-iso-addition-protocol.md §0/§3 must now say SPP IS registered
(2 zones, seam TTC Tier-3 pending SPP-53) — SPP-10's "not registered" correction is stale; R-8
`scripts/data/export_lce_lmp._DUMMY_BASE_LMP` gains an SPP row and tests/unit/results/
test_export_lce_lmp.py is extended to seven. Also: keepers/index.json is NOT yours (SPP-40 adds SPP at
registration); forecast-runs.html must render with SPP present and no forecast runs.
RULES THAT BITE: 15 (dashboard text is generated from sidecars — do not hand-write status),
26, 27 (several ≥ 300-line files — Edit tool, fetch-back verify), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-spp-34-<date>.md (file → change table, audit output); plan §5 row → LANDED.
```

#### SPP-53 `[FABLE]` — the N↔S corridor TTC from SPP's own rated flowgate limits (moved into W3 at r#5 under ruling P13)

```
You are lane SPP-53. MODEL: Fable claude-fable-5-1 — a TTC is a market/physical design object; turning
parallel flowgate ratings into ONE pipe-and-bubble link limit is adjudication, and it edits a ≥300-line
core file (iso_configs.py — Edit tool, exact bytes, fetch-back verify). DATA PROFILE: spp.
Branch stem: claude/spp-53-ns-ttc-f6dz.
Read CLAUDE.md freshly and in full (rules 1, 5, 13, 14 [R-ACCURATE] — its misalignment clause is the
whole of this lane —, 23, 27, 29(b) G-DRIFT); docs/multi-iso/spp-addition-plan-2026-09.md §3 P1 (as
APPLIED r#5), P11, P13 (as ruled), §5 row SPP-53, §7 G8; docs/multi-iso/04-transmission-zones-and-
congestion.md (the binding-frequency method and the ERCOT WESTEX/PNHNDL precedent — GTC limits ARE
link TTCs there); docs/handoffs/FINDING-spp-20-2026-09-06.md §3 (the 48,700 MW placeholder row and
why it cannot bind) and §5 R-6; docs/handoffs/FINDING-spp-14-2026-09-06-session-b.md §5 IN FULL (the
four-group rules, `docs/handoffs/spp14/groups.py`, the corridor constituents by hours — Franklin 161 kV
transformer, Viola transformer, First Creek–Roanridge, Smoky Hills–Summit, Nashua, Jayhawk–Franklin —
and §5.4: the 14-column schema with `Real Time Effective Limit` exists from 2026-01-28 ONLY);
data/raw/spp-binding-constraints/README.md + Flowgates.csv + Temp_Flowgate.csv (SPP-14 landed SPP's two
flowgate registries — check FIRST whether they carry ratings); scripts/data/fetch_spp_alt_portal.py
(SPP-14's producer for portal files); iso_configs.py _spp_config (the link you will re-rate).

PRECONDITIONS (git log origin/main --grep=SPP-20 / SPP-14): both LANDED. Parallel with SPP-30/31/32/33/34
— you own none of their files. Nothing solves in this lane.
FILES YOU OWN: NEW data/raw/spp-binding-constraints/rtbm_bc_corridor_limits_2026.parquet — the REDUCED
sidecar (the LMP-sidecar precedent: the multi-GB daily pulls are not committed; only the corridor rows
are): every `State ∈ {BINDING, BREACHED, ACTIVATED}` row of the 2026-01-28 → latest daily RTBM BC files
whose constraint falls in `n_s_corridor` under groups.py's rules, with `Constraint Name`, `Monitored
Facility`, `Contingent Facility`, `Source Limit`, `Real Time Effective Limit`, `Initial Effective
Limit`, `Interconnect`, `GMTIntervalEnd` — plus a README row (fetch command, span, row count, sha256)
and SOURCES; src/market_sim/config/iso_configs.py — the `_spp_config` N↔S TransferLink `ttc_mw` and its
citation comment ONLY; src/market_sim/config/transmission_expansion.py TRANSMISSION_BASE_STATIC_VINTAGE
["SPP"] ONLY if your source vintage differs from 2025; docs/parameter-citations.md (one row);
docs/handoffs/PRECOMMIT-spp-53-<date>.md, FINDING-spp-53-<date>.md.
FILES YOU MUST NOT TOUCH: anything else in iso_configs.py (SPP-20's registration stands); ScenarioConfig;
the four-group rules in groups.py / the README (fixed before the data — rule 1); any other ISO's file;
the matrix shards (no mechanism is tested; a TTC value is an input).

DO, in this order:
(0) PRECOMMIT FIRST — write and push it BEFORE reading a single limit value. It states: (a) the
    construction rule for turning per-flowgate effective limits into one link TTC (choose and JUSTIFY
    one: the rating of the corridor's dominant defining flowgate as the ERCOT-GTC analogue; or a
    simultaneous-transfer construction over the parallel Kansas paths; or the hour-wise minimum over
    flowgates binding together — state which physical reading of a pipe-and-bubble link each one is,
    pick one, and name what would make you reject it); (b) the misalignment you are documenting under
    rule 14: the limits are 2026 ratings applied to 2023–2025, and a flowgate limit is a monitored-element
    rating under a contingency, not a corridor transfer capability; (c) the CROSS-CHECK, residual-blind:
    the 2023–2025 corridor binding frequency (52–63 % of hours) and the 2024 spread must be consistent
    with a link that CAN bind — a TTC above the corridor's plausible peak transfer (bounded by the
    zonal load/generation imbalance implied by SPP-11's sub-BA energy split and the North fleet) is
    rejected as still-a-placeholder; (d) the STOP conditions: no daily file reachable, or Flowgates.csv
    already carrying a corridor rating that makes the archive pull unnecessary.
(1) Flowgates.csv / Temp_Flowgate.csv: read them for rating columns first. If SPP publishes the
    corridor flowgates' ratings there, that is the source and the archive pull in (2) is a cross-check.
(2) Pull the 2026-01-28 → latest daily RTBM BC files with SPP-14's producer to the scratchpad; extract
    the corridor rows (groups.py rules, unchanged) into the reduced sidecar; report per corridor
    flowgate: n intervals, median / p10 / p90 of `Real Time Effective Limit`, `Source Limit`, and how
    often the effective limit sits below the source limit (derates).
(3) Apply the PRECOMMIT's construction rule → ONE ttc_mw with its citation comment (rule 5), the
    vintage, the misalignment statement, and the rejected alternatives. Cross-check per (0c). Run
    `uv run python scripts/solve_surface_register.py --diff origin/main HEAD` → zero moved rows for the
    six ISOs (iso_configs.py is not a surface module, but prove it); `get_iso_config("SPP").
    validate_topology()`; `pytest tests/unit/config -q`.
Never tune the value to any price or flow residual — there is no SPP residual yet and there must not
be one in this lane; the construction rule is declared before the data and the number falls out of it.
RULES THAT BITE: 1, 5, 13, 14, 23, 24, 25, 26, 27 [R-PUSH], 28 (no cell moves).
EXIT: PRECOMMIT + FINDING (the per-flowgate limit table, the construction, the number, the cross-check,
the G8 proof), the re-rated link in iso_configs.py, the citations row; plan §5 row → LANDED and §3 P13
row's ruling cell annotated with the value. Report to the owner: the TTC, its construction and its
misalignment statement, first. SPP-40 reads it.
Push by pack size (CLAUDE.md Git & Pushing); fetch-back verify every pushed file ≥300 lines; no CI
workflows; no default moves; no solve; if you must touch a file outside your regions, STOP and route to
SPP-DESK in your FINDING.
```

### W4 — first solve → first keeper (issued the sitting after SPP-30/31/32 AND SPP-53 merge)

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

PRECONDITIONS (git log origin/main --grep=SPP-3 and --grep=SPP-53; STOP if unmet): SPP-30, SPP-31, SPP-32
AND SPP-53 LANDED (P13: the N↔S link must carry SPP-53's derived TTC, never SPP-20's 48,700 MW
placeholder — check the value in _spp_config before the smoke).
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
    becomes the 29(b) control for every later SPP lane". The PRECOMMIT ALSO states (P7 as ruled):
    (i) the hub spread is a Nebraska-vs-central-Oklahoma two-point spread, not a zonal price
    difference (audit §6.1), so it screens the link's direction/season and is never read as a zonal
    price validation; (ii) the two known low-side EIA-930 hours (2025-06-21 05:00 = 1,505 MW,
    2024-07-19 00:00) as 1-in-8,760 artifacts the loader does not yet screen (P9 routed).
    PUSH IT before solving.
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

#### SPP-40 ADDENDUM `[FABLE]` — issued r#6 (2026-09-07) into the running SPP-40 session

```
SPP-40 ADDENDUM (desk sitting r#6, 2026-09-07). Paste into the running SPP-40 session. Nothing here
changes your charter's order of work; it fixes six facts your charter could not know.

(1) C4 FOR SPP 2023 IS NOT QUOTABLE YET. FINDING-spp-31 §3.3/§5a: the NG: spike screen lives only in
    build_calibration_reference.py; run_calibration_full._eia930_frame_generic calls
    load_eia_hourly_benchmark UNSCREENED, so your e930.parquet → bench/SPP/2023.json.gz carries the
    h3907 wind artifact (3,589,445 MW; +3.5857 TWh; ~1.25 pp spurious fuel-mix error). Lane SPP-41
    (Fable, running in parallel) moves the screen into the loader. YOU: solve and register exactly as
    chartered; in FINDING-spp-40 and the log entry report C4-2023 as "UNSCORED pending SPP-41" with the
    3.5857 TWh figure named, never as a number; 2024/2025 C4 are clean (no SPP series moves there).
    After SPP-41 merges, the desk re-runs render_calibration_html on your committed run dir to
    regenerate bench/SPP/2023 and re-scores — no re-solve (the LP never reads the benchmark).
(2) THE LINK. _spp_config ttc_mw = 3,400 (SPP-53, FCITC construction, PRECOMMIT-spp-53 §2.1). The
    S→N-loaded set reads 4,206 MW by the same rule (FINDING-spp-53 §3) — the link is registered
    SYMMETRIC at 3,400. Your STOP gate "link binds in the measured direction" is now evaluable: the
    measured direction is N→S in the binding-hours-weighted majority (SPP-14 §5.2 n_s_corridor). Report
    binding hours by direction and season; do NOT change the value (rule 14; asymmetry is W5 SPP-58).
(3) THE HUB SPREAD is a two-point spread (Nebraska vs central Oklahoma); P7's 2024 screen year stands
    on the hourly per-hub measure (RT mean |N−S| 17.23 in 2024 vs 12.13 / 15.18).
(4) TWO KNOWN LOW-SIDE DEMAND HOURS remain unscreened (P9 routed, R-f): 2025-06-21 05:00 = 1,505 MW
    and 2024-07-19 00:00. Name them in the PRECOMMIT as 1-in-8,760 artifacts; no screen parameter.
(5) INPUTS AS LANDED: outages campd-unit-outages-SPP.csv (+ -short/-layup/-e923, partial);
    thermal_tranches_SPP.csv (118 plant-groups) — derive_cc_committed_pct was NOT run (ERCOT-only);
    zonal shares in clean/ (Σ = 1.0 exactly); wind shape data/raw/spp-wind-shape/ (South is the
    nocturnal zone — measured); gas basis 2022–2024 only in data/fuel/basis/meanzero.py (2025
    unpublished — state which fallback the 2025 solve took, from the run's own log, never patch it);
    oil excluded; every SPP offer band 1.0 with no phys_* rows (authorized_price_tuning: none).
    Interchange is SERVED (P2) — SPP-33's hr_by_year numbers are for SPP-51, not you.
(6) RULE 12: the desk knows of no other per-plant solve at your launch; re-ask before the full span.
```

### W4b — input repairs + re-baseline (issued r#7; SPP-41/36/37 parallel, SPP-42 after 36+41)

#### SPP-41 `[FABLE]` — v2 (r#7): the EIA-930 spike screen moves into the loader — bench path AND wind-input path

```
You are lane SPP-41 (v2, re-issued r#7 — v1 was never launched; this block REPLACES it). MODEL: Fable
claude-fable-5-1 — a src/ seam edit whose consequence set (which consumers move, whether any registered
keeper's benchmark OR input moves, cache-key neutrality) is an adjudication. DATA PROFILE: code (widen
to `shared` only to regenerate a bench part). Branch stem: claude/spp-41-fuel-spike-seam-k2mr.
Read CLAUDE.md freshly and in full (rules 13, 14, 19, 21, 24, 26, 27, 28c); FINDING-spp-31 §3 (the
screen, the two-series effect, §3.3 the gap) and §5a; FINDING-spp-40 §4 second bullet (the SAME h3907
slip reaches the model's delivered wind profile: CF 0.96 at local index 3909, +27 GWh, 0.024 % of 2023
SPP wind potential) and §7.1 (C1/C4-2023 wind UNSCORED pending you); scripts/data/build_calibration_
reference.py:575-700 (_screen_fuel_spikes + constants); src/market_sim/data/eia930/actuals.py IN FULL —
it holds BOTH consumers: the benchmark loader load_eia_hourly_benchmark (:201, NG: WND at :306) and the
delivered-profile read at :99 (the wind/solar profile path the LP actually consumes); the sibling
_screen_demand_dropouts in demand.py; every downstream consumer: scripts/run_calibration_full.py:1854
_eia930_frame_generic, scripts/render_calibration_html.py, scripts/data/derive_import_tranches.py:83,
scripts/verify_holdout_intake.py:71; scripts/check_bench_freshness.py; docs/testing.md.

PRECONDITIONS: SPP-31 and SPP-40 LANDED (git log origin/main --grep). The SPP keeper
2026-09-07-spp-1-baseline exists; you never touch results/ or any run dir. SPP-42 (the re-baseline)
waits on you — it re-renders bench/SPP/2023 and re-solves with the repaired input; you do NEITHER.
FILES YOU OWN: src/market_sim/data/eia930/actuals.py, scripts/data/build_calibration_reference.py
(the screen's old home), tests under tests/unit/data/ for both, docs/handoffs/FINDING-spp-41-<date>.md,
and ONLY the bench parts your proof shows move (expected: none — see (3)). MUST NOT TOUCH: ScenarioConfig
/ constants / cache.py (G8); any run dir; keepers/, status/, registry/, runs/, bench/SPP/; demand.py's
screen (rule 19 — the demand dropout is R-f's phenomenon); any shard; renewables.py.

DO, in order:
(0) ZERO-LP PROOF FIRST, two tables committed in the FINDING before any edit:
    (a) BENCH path: all 7 ISOs × 2021–2025 × every series load_eia_hourly_benchmark returns, TWh
        before/after. Expected (SPP-31 §3.2): EXACTLY two movers — SPP 2023 wind 106.6345 → 103.0488
        (h3907) and NYISO 2024 other 3.3846 → 3.3486 (h6759–6763).
    (b) INPUT path: the same census on the delivered-profile read (:99) — every ISO × year × wind/solar,
        GWh and max-CF before/after. Expected: SPP 2023 wind −27 GWh (index 3909) and NOTHING else.
    A third mover on either path is a STOP: report and ask the desk before editing.
(1) ONE mechanism, ONE seam (rules 19/26): apply the screen where actuals.py reads the EIA-930 frame,
    so both consumers inherit it; delete _screen_fuel_spikes from build_calibration_reference (it
    imports the screened loader). The screen stays parameter-free and registry-free (rule 24): the
    2.5× robust-scale rule and the p99.9 anchor are measured-artifact detection with SPP-31's
    provenance docstring; rule-13 test stated in the docstring (regenerates for any forward year
    from the series itself). Fuel columns only — never Demand.
(2) CONSEQUENCE AUDIT, measured: (a) cache_key() unmoved for every ISO's committed keeper run_config
    (data is not in the key; prove by key diff); (b) check_bench_freshness on every committed part —
    the only candidate is NYISO 2024 (`other` is unscored; state whether the part's bytes change);
    (c) calibration_reference.json rebuild byte-identical to HEAD; (d) verify_holdout_intake and
    derive_import_tranches outputs byte-identical for every ISO; (e) the INPUT side: state in one
    line per ISO that no keeper other than SPP's has a moved input (from table 0b) — SPP's moves by
    27 GWh and SPP-42 absorbs it by re-solving; you do not.
(3) If (2b) shows NYISO 2024's part changes: regenerate that ONE part from NYISO's committed keeper
    run dir (render_calibration_html, no solve), re-score with calibration_verdict.py --run-id,
    state the verdict delta (expected none). Run dir not on disk → report, leave it, the desk routes.
(4) bench/SPP/2023: DO NOT regenerate — SPP-42 owns the re-render and re-score. Put the exact
    command in the FINDING.
GATES before push: pytest tests/unit/data tests/scoring -q; ci_refactor_guards.py; check_bench_
freshness.py; check_golden_manifest.py; check_mechanism_matrix.py — all 0. No ScenarioConfig field
(G8) → no matrix row.
RULES THAT BITE: 13, 14 (the artifact is a data defect, not a residual), 19, 21, 24, 26, 27 (both
files ≥300 lines → Edit locally, git push, fetch-back hash verify), 28c.
EXIT: FINDING-spp-41 with tables 0a/0b, the five consequence-audit results, the SPP-42 re-render
command; plan §5 row → LANDED; a pointer appended to SPP-31 §5a. Owner report: the two tables first.
```

#### SPP-36 `[OPUS]` — coal supply class for SPP (SPP-40 R-7)

```
You are lane SPP-36. MODEL: Opus claude-opus-5 — one frozen derive on a committed recipe (rule 23);
the desk verified the CLI against --help (it takes --iso and writes the per-ISO file). DATA PROFILE:
spp. Branch stem: claude/spp-36-coal-supply-class-t3kp.
Read CLAUDE.md freshly and in full; FINDING-spp-40 §7.3 first bullet (the defect: the benchmark scores
SPP coal as COAL_PRB / COAL_LIGNITE from EIA-923 fuel types while the model dispatches ONE `COAL` class,
`coal_supply` empty on every SPP plant except 0.58 TWh of lignite — C1's coal rows fail by construction
and C5a carries COAL_PRB = 0.0, ~70 Mt of coal CO2 dispatched but not counted); the docstring of
scripts/data/derive_coal_supply.py (it reads f923 Schedule-5 receipts, assigns each plant its dominant
rank, writes data/raw/_processed-legacy/coal_supply_<ISO>.csv, which market_sim.data.coal.
coal_supply_class merges at resolution step 2); src/market_sim/data/coal.py:143-171 (the four-step
resolution order — note step 3, the EIA-860 retiree fallback, and that `coal_takeorpay_SPP.csv` ALREADY
exists in the same directory — state its provenance in your FINDING, do not regenerate it);
src/market_sim/config/plant_taxonomy.py COAL_CODE_TO_SUPPLY and COAL_SUPPLY_TO_CLASS; the existing
coal_supply_{MISO,PJM,NEISO}.csv headers (your output template); FINDING-spp-30 (which SPP coal plants
carry CEMS windows).

PRECONDITIONS: SPP-40 LANDED (the keeper exists; its FINDING names the defect). FILES YOU OWN:
data/raw/_processed-legacy/coal_supply_SPP.csv (NEW), docs/handoffs/FINDING-spp-36-<date>.md, your plan
§5 row. MUST NOT TOUCH: src/ (if the derive needs an SPP branch, STOP and route); any other ISO's
file; coal_takeorpay_SPP.csv; ScenarioConfig; any run dir, sidecar, shard.
RUN: python3 scripts/data/derive_coal_supply.py --iso SPP  (all release years; then --year 2023 /
2024 / 2025 separately as a stability check, reported not written). GATES: (a) every coal plant in
the SPP EIA-860 fleet (BA SWPP) is classed, or itemised with the reason it is not (no receipts →
which fallback step 3/4 will catch it, or it stays `COAL` — say which); (b) the class energy
reconciles: from the committed keeper's hourly/ sidecars and the EIA-923 by-plant coal generation,
model-vs-actual by supply class after the reclass (report, never tune) — the sum must reproduce the
family-level 70.5 vs 71.7 TWh SPP-40 §7.3 states; (c) ZERO-LP consequence: an on-recipe
run_year(fleet_only=True) for 2023 before/after — MW and unit count moving COAL → COAL_PRB /
COAL_LIGNITE / COAL_BIT, and which plants now enter the PRB take-or-pay / sigmoid passthrough physics
(assembly.py:1184, :1926 — measured physics, rule 13, NOT a band); (d) six keepers: solve_surface_
register.py --diff 0 moved (the file is SPP-keyed by plant code; prove no other ISO's plant appears).
State plainly: the SPP keeper's INPUT moves — SPP-42 re-solves; you do not solve.
RULES THAT BITE: 13, 14, 23 (source data, not a residual, is the reason this exists), 25 (no band
touched), 27.
EXIT: FINDING-spp-36 with gates (a)–(d) as tables; plan §5 row → LANDED. Owner report: the reclass
census (MW by class before/after) first.
```

#### SPP-37 `[OPUS]` — SPP-35's six leftovers

```
You are lane SPP-37. MODEL: Opus claude-opus-5 — enumerated edits, no design. DATA PROFILE: code.
Branch stem: claude/spp-37-leftovers-q7hn.
Read CLAUDE.md freshly and in full (rule 27: README.md / market-sim-build-plan.md / index.html may be
≥300 lines — Edit locally, git push, fetch-back verify); FINDING-spp-35 §5 (R-1…R-6, your whole
scope) and §3 (the badge pattern it landed); FINDING-spp-53 §6 (the 3,400 MW figure for R-5).
PRECONDITIONS: SPP-35 and SPP-53 LANDED. FILES YOU OWN (exactly these): R-1 `.gitignore` — add
`/results/SPP/` after line 276 beside the six; R-2 root `index.html` (:7 meta, :34 hero, :153 footer),
`README.md:121`, `market-sim-build-plan.md:9` — "six ISOs … NEISO" → seven with SPP appended LAST
("SPP (2 zones)"); R-4 `docs/codebase-site/policy-scarcity.html` CAISO `.iso-badge` alpha 0.15 → 0.12
(4.47 → 4.58:1; no hue change); R-5 `docs/codebase-site/js/iso-configs-table.js:32` — the SPP
description's "non-binding placeholder" → the SPP-53 reconciled 3,400 MW FCITC figure (cite
FINDING-spp-53); R-6 `CHANGELOG.md` — ONE entry covering SPP-35 + this lane; docs/handoffs/
FINDING-spp-37-<date>.md. MUST NOT TOUCH: src/, scripts/, frontend/data/, any shard, docs/codebase-
site/config-reference.html (SPP-35's), the historical "all six ISOs" comments in config/scenarios.py.
GATES: `git check-ignore results/SPP/x` prints the path; `grep -rn "six ISOs\|six-ISO" --include=*.md
--include=*.html --include=*.js .` lists ONLY historical/log lines (paste the residue in the FINDING);
accessibility-audit on policy-scarcity.html — every badge ≥ 4.5:1; `git diff --stat` shows only the
files above. SPP-35's R-3 (the registry generator's iso_configs limb) is NOT yours — routed.
RULES THAT BITE: 26, 27. EXIT: FINDING-spp-37; plan §5 row → LANDED. Three commits: R-1+R-2, R-4+R-5, R-6.
```

#### SPP-42 `[OPUS]` — the 2025 hydro vintage repair + the full-span RE-BASELINE (keeper-2 candidate)

```
You are lane SPP-42. MODEL: Opus claude-opus-5 — a pre-declared recipe (the repair four keepers already
arm) solved on the keeper's own recipe, with a PRE-DECLARED promotion rule; anything the rule does not
decide STOPs and reports to the desk — you never adjudicate. DATA PROFILE: spp.
Branch stem: claude/spp-42-hydro-rebaseline-w8nd.
Read CLAUDE.md freshly and in full (rules 12, 13, 14, 15, 16, 20, 21, 22, 27, 28b, 29); FINDING-spp-40
§7 entire (the keeper, its determination table, §7.3 second bullet: 2025 hydro budget 0.02 TWh from the
EIA-923 preliminary vintage vs 8.8 TWh actual → 2,007 MWh unserved in six named hours, 19 h > $200,
the +21.7 % C3a-2025) and PRECOMMIT-spp-40 (the recipe — yours is IDENTICAL except the one flag);
the mechanism-matrix row `hydro_vintage_input_repair` (docs/codebase-site/data/mechanism-matrix.js —
its note: every ISO's 2025 923 hydro vintage is truncated; CAISO/PJM/MISO/NEISO keepers arm
`--hydro-backfill-year 2024`; NYISO's owner decision was report-not-arm because its hydro is 18 % of
generation and the arm moved all three years there) and SPP's cell in mechanism-matrix/SPP.js;
scripts/run_calibration_full.py --help (`--hydro-backfill-year`); FINDING-spp-36 and FINDING-spp-41
(the two input repairs you carry); frontend/data/backcast/keepers/README.md (promotion + prune
protocol); scripts/prune_iso_runs.py; the calibration-report skill; docs/calibration-log/spp.md.

PRECONDITIONS (git log origin/main --grep, STOP if unmet): SPP-36 LANDED and SPP-41 LANDED. Ask the
desk whether another per-plant solve is running (rule 12; SPP is per_plant, 5.3 GB peak).
FILES YOU OWN: results/calibration/spp42_repaired_B/ (+ hourly/), registry/<id>.json + runs/<id>.js,
keepers/SPP.json, status/SPP.js, bench/SPP/{2023,2024,2025}.json.gz, mechanism-matrix/SPP.js
(keeper + gates stamp + the hydro_vintage_input_repair cell — LAST commit), docs/calibration-log/spp.md
(entry spp-3), PRECOMMIT-spp-42-<date>.md, FINDING-spp-42-<date>.md. MUST NOT TOUCH: any other ISO's
files; ScenarioConfig defaults; offer bands (all 1.0 — rule 25); calibration-complete.json; the
hydro loader's code.

DO, in order:
(0) PRECOMMIT, pushed BEFORE any solve: the recipe = keeper-1's run_config.json + `--hydro-backfill-year
    2024` and nothing else; G-DRIFT from keeper-1's git_sha to your base — classify every hunk; the
    SPP-36 (coal class) and SPP-41 (wind-input screen, −27 GWh 2023) hunks are LIVE for SPP BY DESIGN
    (this is a re-baseline, not a lever A/B — say so); every other hunk INERT with reason. ZERO-LP:
    build_hydro_fleet on/off for 2023, 2024, 2025 — 2023/2024 budgets BYTE-IDENTICAL (the flag only
    touches the truncated year; assert), 2025 budget before/after (expect 0.02 → ~8.8 TWh; the SPP
    2025 923 retention % beside the six ISOs' table in the matrix note). Rule 29: 2023/2024 are
    unchanged by construction, so the object exists in ONE year — the screen and the full span are
    the same solve (rule 29's year-scoped exemption; state it). THE PROMOTION RULE, declared here:
    promote to keeper-2 iff (i) the 2023/2024 hydro budgets are byte-identical to keeper-1's, (ii)
    2025 unserved energy is 0 MWh, OR every remaining unserved hour is named with a cause that is
    not hydro, (iii) no load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL in any year for a
    reason other than the coal reclass changing what C1 scores (which is REPORTED, never a fail
    reason), and (iv) the DOF ledger is unchanged (3 entries, 1 residual, 0 tuned). If (i)–(iv)
    hold, keeper-1 is pruned (rule 15 keeper-only retention). If any is ambiguous: register the run,
    do NOT touch keepers/SPP.json, and STOP with the table — the desk serves a card.
(1) FULL SPAN: one invocation --year 2023 2024 2025 --hydro-backfill-year 2024 --out-dir
    results/calibration/spp42_repaired_B (years sequential). Generate legitimacy_diagnostics.json,
    calibration_attestation.json (authorized_price_tuning NONE). Score after the final rebase.
(2) RE-RENDER + RE-SCORE the inherited gap: the run's own bench/SPP/2023 now carries the screened
    loader (SPP-41) — report C1/C4-2023 wind SCORED for the first time, with the before/after wind
    actual (106.6345 → 103.0488 TWh).
(3) REGISTER (id 2026-<mm-dd>-spp-2-repaired-inputs); apply the promotion rule; build_status --iso
    SPP; bench parts; hourly sidecars; shard: keeper/gates stamp + hydro_vintage_input_repair cell
    (U → K if promoted; U → R/I/O with the evidence if not — rule 28b); log entry spp-3.
(4) GATES before push: audit_keepers --check, check_registry_payload_parity, check_mechanism_matrix,
    check_bench_freshness, check_golden_manifest — all 0; calibration-keeper-auditor --iso SPP.
RULES THAT BITE: 1 (structure, not MAE — the repaired input stays even if a band worsens, rule 14),
12, 13 (an inflow budget regenerates forward — admissible; declared, never banked as skill), 15,
16, 20, 21, 22, 27 (run payload → git push; sidecar hash-verified), 28b, 29 (year-scoped exemption
stated), 30 (no touchpoint).
EXIT: keeper-2 on backcast-runs.html#iso=SPP if the rule fired, else the registered run + the STOP
table; FINDING-spp-42 with the determination table beside keeper-1's (full magnitude), the hydro
budget census, the unserved-hour table, the G-DRIFT classification; plan §5 row → LANDED. Owner
report: determination + the two tables first.
```

#### SPP-35 `[OPUS]` — seven-ISO prose sweep + ISO-badge contrast

```
You are lane SPP-35. MODEL: Opus claude-opus-5 — execution of an enumerated edit list; no design.
DATA PROFILE: code.  Branch stem: claude/spp-35-seven-iso-prose-v8jd.
Read CLAUDE.md freshly and in full (rule 27 binds: CLAUDE.md and the spec are core files ≥300 lines —
Edit locally, push the on-disk bytes, fetch-back verify); FINDING-spp-34 §7 (S-1, S-2, S-3);
FINDING-spp-20 §5 items O-4 and O-6; docs/codebase-site/css/shared.css (.badge--iso-* and
.iso-btn.active--* — the accessible variants that already exist); the accessibility-audit and
sync-docs skills.

PRECONDITIONS: SPP-34 LANDED and SPP-20 LANDED (git log origin/main --grep=SPP-34 / --grep=SPP-20).
FILES YOU OWN (edit exactly these): S-1 — CLAUDE.md:19 (the "six ISOs" sentence + enumeration →
seven, SPP appended LAST in the list with "2 zones"), model-methodology-spec.md:13 and :719,
docs/codebase/README.md:22, docs/user-manual.md:646; S-2 — docs/codebase-site/config-reference.html:209
and css/bc-pages.css:125 (route .iso-badge onto the tinted-background pattern for ALL seven; never
pick new hues); O-4 / O-6 exactly as FINDING-spp-20 §5 enumerates them (a docstring and the registry
generator's prose, both doc-only); docs/handoffs/FINDING-spp-35-<date>.md. FILES YOU MUST NOT TOUCH:
src/ (if O-4 turns out to be a src/ docstring, STOP and report the line — the desk decides),
frontend/data/, any shard, scripts/, data-completeness.html (S-3 is an evidence job, not yours),
the "all six ISOs" comments inside config/scenarios.py (historical statements, correct as history).
GATES: accessibility-audit on config-reference.html (every ISO badge ≥ 4.5:1 — report all seven
ratios before/after); sync-docs reports no new drift; git diff --stat shows ONLY the files above.
RULES THAT BITE: 26 (delete the stale sentence, don't hedge it), 27.
EXIT: FINDING-spp-35 with the before/after ratio table and the five S-1 diffs; plan §5 row →
LANDED. One commit for S-1 (core files), one for S-2, one for O-4/O-6.
```

### W4c — the screened-input re-baseline + the red-test sweep (issued r#8)

#### SPP-43 `[OPUS]` — keeper-2's recipe re-solved through the SPP-41 seam → keeper-3 candidate

```
You are lane SPP-43. MODEL: Opus claude-opus-5 — one re-solve of a committed recipe with a pre-declared
promotion rule; anything the rule does not decide STOPs and reports. DATA PROFILE: spp.
Branch stem: claude/spp-43-screened-rebaseline-p2vq.
Read CLAUDE.md freshly and in full (rules 12, 13, 14, 15, 16, 20, 21, 22, 27, 28b, 29); FINDING-spp-41
§0, §1b (table 0b — the INPUT path: SPP 2023 wind is the ONLY moved series, −27 GWh at index 3909), §5
(route (b), the one this lane takes) and §8 (R-10: keeper-2's bench/SPP/2023 carries wind 106.634 because the
run-side builder took the wind class from EIA-930 under the 0.90 completeness test); FINDING-spp-42 entire
(keeper-2: recipe, §3.1 determination, §3.3 the crosswalk's benchmark-side effect, §6 R-9/R-10/R-11);
FINDING-spp-36 §3.2 note (plant 6193: 3.178 TWh of 2023 coal in the bench population but outside the
EIA-860 fleet coal set — R-10 there); FINDING-spp-57 §8 R-15 (calibration_reference.json's 2025 hydro actual
is still the EIA-923 preliminary 0.02 TWh); FINDING-spp-37 §5 N-1/N-2; results/calibration/spp42_crosswalk_B/
meta.json (THE recipe: years 2023–2025, hydro_backfill_year 2024, hydro_eia930_monthly True, git_sha 33034499)
and run_config.json; frontend/data/backcast/keepers/README.md; scripts/prune_iso_runs.py --help;
docs/calibration-log/spp.md (spp-3 is the format).

PRECONDITIONS (git log origin/main --grep, STOP if unmet): SPP-41 LANDED (PR #5497) and SPP-42 LANDED
(PR #5471). Ask the desk whether another per-plant SPP solve is running (rule 12; 5.3 GB peak).
FILES YOU OWN: results/calibration/spp43_screened_B/ (+ hourly/), registry/<id>.json + runs/<id>.js,
keepers/SPP.json, status/SPP.js, bench/SPP/{2023,2024,2025}.json.gz, mechanism-matrix/SPP.js (keeper +
gates stamp — LAST commit), docs/calibration-log/spp.md (entry spp-5), the "UNSCORED pending SPP-41"
lines in the log and FINDING-spp-40 §7.1 / FINDING-spp-42 §1 (append a one-line pointer to your FINDING,
never rewrite them), docs/user-manual.md:646 and market-sim-build-plan.md:11 (N-1 / N-2: seven-of-seven
gitignored; CAISO 6 / MISO 6 zone counts), PRECOMMIT-spp-43-<date>.md, FINDING-spp-43-<date>.md.
MUST NOT TOUCH: any other ISO's files; ScenarioConfig defaults; offer bands (1.0 — rule 25); the seam
(actuals.py); the builder; calibration-complete.json; keeper-2's committed bundle bytes.

DO, in order:
(0) PRECOMMIT, pushed BEFORE the solve. The recipe = keeper-2's meta.json flags exactly
    (--year 2023 2024 2025 --hydro-backfill-year 2024 --hydro-eia930-monthly) and NOTHING else; the only
    thing that changed under it is the loader seam. ZERO-LP: reproduce FINDING-spp-41 table 0b for SPP
    (wind/solar 2023–2025 GWh + max-CF before/after the seam at HEAD) — expect SPP 2023 wind −27 GWh, all
    else byte-identical. G-DRIFT from 33034499 to your base over the rule-29(b) file set: the SPP-41 seam
    hunk is LIVE for SPP 2023 ONLY (INERT for 2024/2025 by table 0b); classify every other hunk with its
    reason. Rule 29: the object exists in one year, so the screen and the full span are the same solve
    (state the exemption). THE PROMOTION RULE, declared here: promote to keeper-3 iff (i) the 2024 and 2025
    P1 objectives are IDENTICAL to keeper-2's (meta/metrics; the seam moves no 2024/2025 input — this is
    the identity check, and a difference is a STOP that names a hidden mover), (ii) 2023 moves ONLY where
    wind can move it (report the class deltas; coal/gas ± within what 27 GWh can displace), (iii) no
    load-bearing criterion flips PASS → FAIL vs keeper-2 in any year, (iv) DOF ledger unchanged. If
    (i)–(iv) hold, keeper-1 AND keeper-2 are pruned at registration (rule 15 keeper-only retention;
    prune_iso_runs.py --iso SPP). Any ambiguity: register, do NOT touch keepers/SPP.json, STOP with the
    table — the desk serves a card.
(1) FULL SPAN: one invocation, --out-dir results/calibration/spp43_screened_B, years sequential. Generate
    legitimacy_diagnostics.json and calibration_attestation.json (authorized_price_tuning NONE). The
    fresh solve writes e930 through the screened loader, so bench/SPP/<year> regenerates with no extra
    step — verify bench/SPP/2023 wind reads 103.049 (or the EIA-923 total if the 0.90 test no longer
    fires; state which, per SPP-41 §8) and that the 2023 classFull total lands near 284.6, not 288.2.
(2) SCORE after the final rebase: C1/C4-2023 wind is SCORED for the first time — report it beside
    keeper-2's UNSCORED line. Determination at full magnitude beside keeper-2's table (FINDING-spp-42 §3.1).
(3) REGISTER (id 2026-<mm-dd>-spp-3-screened-input); apply the rule; build_status --iso SPP; bench
    parts; hourly sidecars (rule 15); shard keeper/gates stamp (no cell moves — no mechanism was tested);
    log entry spp-5; the pointer lines; N-1 / N-2.
(4) ZERO-LP REPORTS (no fix, no tuning): (a) R-15 — what calibration_reference.json carries for SPP 2025
    hydro and which builder rule (EIA-923 preliminary vs the EIA-930 swap other renewables get) decides
    it; a proposed one-rule repair for the desk, not applied; (b) plant 6193 — is it in the EIA-860 SWPP
    fleet, and if not why the bench population carries 3.178 TWh of its 2023 coal (state the crosswalk row).
GATES before push: audit_keepers --check, check_registry_payload_parity, check_mechanism_matrix,
check_bench_freshness, check_golden_manifest — all 0; calibration-keeper-auditor --iso SPP.
RULES THAT BITE: 1, 12, 13, 14, 15 (prune, do not archive), 16, 20, 21, 22, 27 (run payload → git push;
sidecar hash-verified), 28b, 29 (year-scoped exemption stated), 30.
EXIT: keeper-3 on backcast-runs.html#iso=SPP if the rule fired (else the registered run + STOP table);
FINDING-spp-43 with the identity check (i), the determination table beside keeper-2's, the C1/C4-2023
wind score, and the two zero-LP reports; plan §5 row → LANDED. Owner report: the identity check and the
determination table first.
```

#### SPP-38 `[OPUS]` — the 15 SPP-era red tests at HEAD

```
You are lane SPP-38. MODEL: Opus claude-opus-5 — enumerated test repairs in a precedent's pattern.
DATA PROFILE: code. Branch stem: claude/spp-38-seventh-iso-tests-n6wr.
Read CLAUDE.md freshly and in full (rules 22, 26, 27, 28); FINDING-spp-41 §6 and §7f (the 16 failures at
HEAD, reproduced with the lane's tree stashed: ONE is CAISO's — test_caiso_st_gas_peak_measured, SPP-31 §5e,
NOT yours — and FIFTEEN are SPP-era: test_collate_scenario_campaign*, test_ff_readiness_battery,
test_forecast_parity, test_registration_marker_gate, test_scenario_campaign_configs — missing
configs/scenarios/spp_scenario_base_*.yaml, six-ISO set assertions, "every registered holdout run must
belong to a complete ISO"); FINDING-spp-20 §4 (the precedent: 15 six-tuple tests extended, 3 DOCUMENTED
exclusions — capacity-market / carbon families SPP does not have); plan §1 row 6 and §8 W6 (the forecast
program is ROUTED to the capx director: GOLDEN_ISOS, program-status.json, ff-verdicts.json are NEVER yours);
the six existing configs/scenarios/<iso>_scenario_base_*.yaml (form); docs/testing.md.

PRECONDITIONS: SPP-41 LANDED (its §6 is your list). FILES YOU OWN: the failing test files named above
(assertions only — a six-ISO tuple becomes seven, or the test gains a DOCUMENTED SPP exclusion in the SPP-20
form with the reason in the assertion message), NEW configs/scenarios/spp_scenario_base_*.yaml cloned in
form from the six (every value SPP-specific or the shared default — cite; NO tuned number), and
docs/handoffs/FINDING-spp-38-<date>.md. MUST NOT TOUCH: src/; frontend/data/; any shard; GOLDEN_ISOS;
program-status.json; ff-verdicts.json; the CAISO test; any registry sidecar; the registration-marker
GATE itself (if test_registration_marker_gate fails because an SPP run is registered without a
`complete` marker, that is the test being RIGHT about rule 22 — report what it asserts and STOP on that
one; never weaken a holdout gate).
DO: for each of the 15, one of three outcomes, tabulated in the FINDING: EXTENDED (seven-set), CONFIG
ADDED (the yaml, with its provenance), or EXCLUDED (documented in the assertion, with the reason — e.g.
SPP has no forecast-program row until W6). Then `pytest tests/unit/data tests/scoring -q` → the CAISO
failure is the ONLY red. Also run tests/unit/config and tests/curation to prove nothing else moved.
GATES: check_mechanism_matrix.py 0 (no ScenarioConfig field); ci_refactor_guards.py 0; check_golden_manifest.py
unchanged from HEAD.
RULES THAT BITE: 22 (never weaken a holdout gate), 26 (delete a dead six-ISO assertion, do not hedge
it), 27, 28c (no field → no row).
EXIT: FINDING-spp-38 with the 15-row outcome table; plan §5 row → LANDED. Owner report: the table first.
```

#### SPP-57b `[FABLE]` — the Oklahoma pocket, re-issued with the constituent sets re-declared ex ante (SPP-57 R-12)

```
You are lane SPP-57b. MODEL: Fable claude-fable-5-1 — the same design objects as SPP-57, with the link
construction corrected on that lane's own evidence; kill-grading is adjudication. DATA PROFILE: spp.
Branch stem: claude/spp-57b-oklahoma-pocket-sets-h3km.
Read CLAUDE.md freshly and in full (rules 1, 12, 13, 14, 16, 19, 21, 22, 24, 25, 27, 28, 29); FINDING-spp-57
ENTIRE — §0 (why the arm died: the union rule pooled the oklahoma_internal group into the N↔OK set, and
those western-Oklahoma delivery elements identify on BOTH spreads, inflating both pipes to 6,500 / 6,700
past any flow the bubbles produce), §2 (the CSWS split, a measured EIA-861 PSO/SWEPCO value — REUSE, do
not re-derive), §3 (the three-point spread, ψ, the T* tables tstar_n_ok.csv / tstar_ok_s.csv: corridor-only
3,355 ≈ SPP-53's 3,400; sps_tie constituents SPPSPSTIES 3,602 / Potter County 3,850 / 10,705 /
SPSNMTIES 11,409), §5.3 (the killed screen's own flows: at 3,400 the N↔OK link is at/over bound 2,065 h,
1,931 N→OK / 134 OK→N; an OK↔S link near 3,400 would be at/over bound 622 h, 603 S→OK), §7 (what is
landed vs reverted; the three-zone implementation is commit f5926636 — cherry-pick it), §8 R-12 (your
charter's construction) and R-14 (the ψ double-attribution SPP-58 owns — you do not fix ψ, you avoid the
set that exposes it); PRECOMMIT-spp-57 (form); FINDING-spp-41 table 0b (the seam moves NO 2025 series, so
keeper-2 is a valid 2025 control after SPP-41 — G-DRIFT states it).

PRECONDITIONS: SPP-57 LANDED (PR #5496, its instruments under docs/handoffs/spp57/), SPP-42 LANDED (keeper-2
2026-09-07-spp-2-crosswalk-hydro, your screen control). SPP-43 (keeper-3, the screened-input re-solve) is
running in parallel: your 2025 SCREEN differences against keeper-2 (INERT seam in 2025); your FULL SPAN,
if the screen clears, differences against keeper-3 if it has landed by then, else against keeper-2 with
the 2023 wind-input hunk declared LIVE and the 2023 column caveated. Ask the desk about concurrent
per-plant solves (rule 12).
FILES YOU OWN: exactly SPP-57's list (the cherry-picked f5926636 files; iso_configs _spp_config with a
third Zone and TWO links; zone_assignment / curate_zonal_shares / renewables / wind shape / meanzero
SPP entries; tests), PRECOMMIT-/FINDING-spp-57b, the screen bundle (TEMPORARY), results/calibration/
spp57b_okpocket_B/ if the screen clears, the SPP shard cell you move. MUST NOT TOUCH: any other ISO's
config, maps or shard; ScenarioConfig (no field — a zone is topology, G8); offer bands; keepers/SPP.json
(promotion = card P15, the DESK's act); calibration-complete.json; docs/handoffs/spp57/ (SPP-57's record —
write your own spp57b/).

THE CONSTRUCTION, declared in the PRECOMMIT before any limit or price is read (this is the whole
difference from SPP-57):
(B′) N↔OK is rated by the `n_s_corridor` flowgate set ALONE — i.e. SPP-53's already-derived 3,400 MW,
     unchanged, symmetric; the killed screen shows it live and N→OK-dominant at that rating. OK↔S is rated
     by the `sps_tie` set ALONE on the (p_S − p_OK) spread, both directions reported, the symmetric link
     carrying the data-named (S→OK) direction; derive it by the SPP-53 FCITC rule (limit-at-bind ÷ ψ,
     binding-hours-weighted median) from SPP-57's limits_2026_oklahoma_by_constraint.csv and
     spread_identification.csv BEFORE reading the result — expected order 3,000–4,000 from the
     constituents' T*, but the rule decides, not the expectation. The `oklahoma_internal` group is EXCLUDED
     from BOTH sets and the exclusion rule is written down: its elements identify on both spreads (SPP-57
     §3.3), so they are the intra-pocket object a bubble cannot hold, not a link.
(A/C/D) unchanged from SPP-57 — reuse the CSWS split, the shares, the identification table, the
     registries and the census from f5926636; re-run validate_topology, solve-surface diff (0 moved for the
     six), persisted identity, and the fleet_only three-zone census.
SCREEN (rule 29): year = 2025, same as SPP-57 (largest oklahoma_internal footprint — the reason is
unchanged), named here. STOP gate IDENTICAL to SPP-57's (E-6 thresholds): (i) each link live (at bound
≥ 5 % of hours) and in the data-named direction ≥ 55 % of at-bound hours; (ii) the sign of each modelled
zonal spread matches the measured hub spread on the annual mean (OK−N sign of +0.15; S−OK sign of +11.29);
(iii) re-curtailment > 0, magnitude REPORTED; (iv) no unserved beyond keeper-2's h8507; (v) fuel families
within [0.1×, 10×] (hydro reads against the reference's 0.02 — SPP-57 R-15 — state it, it is not a miss).
Control = keeper-2 (29b form 4) after a G-DRIFT audit. The gate may kill, never promote, never reads
C3a/C3b. A kill is the session's result: report and stop; the remaining years are not spent.
FULL SPAN only if the screen clears: one --year 2023 2024 2025 invocation; LOYO reported; DOF ledger
(the CSWS split is a MEASURED value; zero tuned scalars); delete the screen bundle before the PR (29c);
register as a CANDIDATE (rule 15); stamp the SPP shard cell you moved; do NOT edit keepers/SPP.json.
RULES THAT BITE: 1, 12, 13, 14 (the 3,400 corridor value stays whatever the fit does), 16, 19, 21, 22,
24, 25, 27, 28b, 29(a)(b)(c).
EXIT: PRECOMMIT pushed before any read; FINDING-spp-57b with the construction (B′), the OK↔S T* table,
the STOP-gate table beside SPP-57's, the LOYO table if the span ran, and the P15 recommendation; plan §5
row → LANDED. Owner report: the STOP-gate table first.
```

#### SPP-44 `[FABLE]` — the CT / CC / ST gas split as a P1-native commitment-bridge question

```
You are lane SPP-44. MODEL: Fable claude-fable-5-1 — a mechanism lane: a new ISO-exclusive ScenarioConfig
field, a rule-18 physics gate, a rule-19 enumeration, and a screen whose kill-grading is adjudication.
DATA PROFILE: spp. Branch stem: claude/spp-44-gas-commitment-bridge-r5tc.
Read CLAUDE.md freshly and in full (rules 1, 5, 12, 13, 17, 18, 19, 20, 21, 24, 25, 27, 28 — 28c BINDS: a
new field needs its matrix row + a cell in EVERY shard in the same PR — 29); the "Dispatch & Commitment"
section (the three P1-native bridges; nyiso_gas_commitment_bridge is your template: ISO-exclusive,
default off, eligibility by unit physics — min-down 4–12 h, $35–50/MW starts, the 1-h CT classes NEVER
bridged — two per-class min_load_fracs MEASURED by the WP-3 loading-when-on construction, plus the
minimum-run-duration leg); FINDING-spp-42 §7 (the object: C1-2024 CC_REGULAR −8.6 / CT_PEAKER +9.9 TWh, the
same sign pattern in 2023 at CT +6.1 / CC −4.6 / ST −7.8; and the rule-19 enumeration already done there —
legitimacy_diagnostics shows 0.0 % forced energy on every SPP class, no floor, bridge or posture armed,
CT clears purely on SRMC with neutral bands); FINDING-spp-40 §5 R-6; scripts/data/derive_campd_gas_commitment_
params.py --help and docstring (--iso SPP; the measured min-load-when-on and run-length statistics);
model/commitment.py (caiso_ra_mustoffer_min_gen, the shared detector) and pipeline/solve.py (the P0→P1
seam); the NYISO bridge's tests; docs/codebase-site/data/mechanism-matrix.js row nyiso_gas_commitment_bridge
and every shard's cell line (form); docs/mechanism-testing-matrix.md §5.7 (SPP's queue); FINDING-spp-30
(SPP's thermal tranches: CC/ST/CT classes and min-down / startup physics as landed).

PRECONDITIONS: SPP-42 LANDED (keeper-2 is your control) — and SPP-43 may promote keeper-3 mid-lane: your
screen year's control is whichever keeper is current at your PRECOMMIT; re-pin and re-audit G-DRIFT if it
moves before the solve (SPP-57's addendum A is the form). Ask the desk about concurrent per-plant solves.
FILES YOU OWN: the derive's SPP outputs (data/raw/reference/ or wherever the NYISO run wrote its, same
place), src/market_sim/config/scenarios.py (ONE new field: spp_gas_commitment_bridge, bool, default False,
with the frozen cache-key drop value so the seven committed keepers' keys are UNMOVED — prove by key diff),
the bridge's SPP branch in model/commitment.py / pipeline/solve.py beside NYISO's (ISO-exclusive; shared
detector; NO class-name tuple — physics parameters only, rule 18), scripts/run_calibration_full.py flag,
tests, docs/codebase-site/data/mechanism-matrix.js (the new row) + a cell line in EVERY ISO shard (`·` n/a
for the six, `U` → your verdict for SPP — the one deliberately non-parallel edit; rebase LAST and re-run
check_mechanism_matrix), docs/mechanism-testing-matrix.md §5.7 entry, PRECOMMIT-/FINDING-spp-44, the
screen bundle (TEMPORARY), results/calibration/spp44_bridge_B/ if the screen clears. MUST NOT TOUCH: any
other ISO's branch or shard cells beyond the one `·` line each; NYISO's bridge; offer bands (rule 25 — a
bridge is a floor, never a multiplier); keepers/SPP.json (promotion = card P15); reliability_floor_overrides
(SPP has none armed — rule 19: enumerate, do not stack).

DO, in order:
(0) MEASURE FIRST, zero-LP, in the PRECOMMIT before any solve: derive_campd_gas_commitment_params.py --iso SPP
    --years 2023 2024 2025 → per-class min_load_frac (CC, ST_GAS) and run-length distributions, with the
    unit-physics eligibility census (which SPP units clear the rule-18 gate; how many MW; CT classes
    excluded by physics, never by name). The mechanism's FOOTPRINT by year = the measured hours of eligible
    units loading-when-on below the P0 economic dispatch would run them; the SCREEN YEAR is the year that
    footprint is largest — named here, NEVER the year with the biggest C1 residual. The STRUCTURAL STOP gate,
    ex ante: (i) bridged energy lands inside the hours CAMPD says the class is on (D-4-style window
    agreement ≥ a declared share); (ii) the class-level P1 dispatch moves in the direction the physics
    implies (CC/ST up, CT down) by an order of magnitude consistent with the bridged MW-hours; (iii) C8
    forced share by class REPORTED (rule 20 budget: > 30 % is a fail for a material class); (iv) no
    load-bearing criterion other than the target flips PASS → FAIL; it never reads C1 or C3a. Rule 17: state
    the driver, the window and the forward story for the floor. Rule 21: the two min_load_fracs enter the DOF
    ledger as MEASURED (source: the derive), never fitted. G-DRIFT vs the control's git_sha.
(1) IMPLEMENT the field + branch + tests + matrix row/cells; prove the seven keys unmoved and every non-SPP
    ISO's fleet/offer byte-identical (the NYISO bridge's own tests are the pattern).
(2) SCREEN on the named year; grade against the gate only; a kill is the result.
(3) FULL SPAN only if it clears; LOYO reported; delete the screen bundle before the PR; register as a
    CANDIDATE; stamp the SPP shard cell (U → K / R / I / O with evidence); do NOT edit keepers/SPP.json.
GATES before push: check_mechanism_matrix.py (row + 7 cells) 0; pytest tests/unit/config tests/unit/pipeline
tests/unit/model -q; tests/regression/test_persisted_identity.py; solve_surface_register.py --diff 0 moved
for the six; audit_keepers --check; parity.
RULES THAT BITE: 1, 5, 12, 13, 17, 18, 19, 20, 21, 24, 25, 27 (scenarios.py is core and huge — Edit locally,
git push, fetch-back verify), 28c, 29(a)(b)(c).
EXIT: PRECOMMIT pushed before any solve; FINDING-spp-44 with the measured parameters, the eligibility
census, the footprint-by-year table (why the screen year), the STOP-gate table, LOYO if the span ran, the
P15 recommendation; plan §5 row → LANDED; §5.7 queue entry. Owner report: the measured parameters and the
STOP-gate table first.
```

### W5 issuance r#9 — after keeper-3 (SPP-45 records · SPP-58 · SPP-54 · SPP-51 · SPP-60)

#### SPP-45 `[OPUS]` — the forecast-board row re-key (gate-(a) red on SPP) + two record annotations

```
You are lane SPP-45. MODEL: Opus claude-opus-5 — three enumerated edits. DATA PROFILE: code.
Branch stem: claude/spp-45-board-rekey-records-c8vm.
Read CLAUDE.md freshly and in full (rules 15, 22, 27); scripts/check_gate_a_provenance.py (its output at HEAD:
"SPP: gate.a_keeper_marker cites SUPERSEDED keeper 2026-09-07-spp-2-crosswalk-hydro; the current designated
keeper is 2026-09-07-spp-3-screened-input — re-key the row against the live keeper (audit board F-5)");
frontend/data/forecast/program-status.json — the SPP row (~line 459, written by the capx Q59 lane from backcast
artifacts only) AND the MISO row's `corrected_by` line (~line 295: the Q34 standing re-key form — keeper id AND
determination text re-keyed to the live designate, with the origin/main sha); frontend/data/backcast/keepers/
SPP.json; FINDING-spp-43 §2 (keeper-3's determination — NOT-YET on the same four criteria) and ADDENDUM A;
FINDING-spp-38 §5 R-5 (SPP-41 §7f's attribution: eleven of the fifteen were not SPP's).

PRECONDITIONS: SPP-43 LANDED (PR #5526; keeper-3 promoted). FILES YOU OWN: the SPP row of
frontend/data/forecast/program-status.json ONLY (every other row and every other file in that namespace is the
capx director's — touch nothing else there), docs/handoffs/FINDING-spp-41-2026-09-07.md (ONE appended
annotation under §7f pointing at FINDING-spp-38 §0/§5 R-5: "eleven of these fifteen were three unrelated
defects; four were SPP's" — append, never rewrite), docs/handoffs/FINDING-spp-42-2026-09-07.md (ONE appended
line under §4: the `keeper_previous` field was dropped at SPP-43's prune, ADDENDUM A), FINDING-spp-45-<date>.md.
DO: (1) re-key the SPP row's `gate.a_keeper_marker.detail` to keeper-3 (id, bundle results/calibration/
spp43_screened_B, promoted 2026-09-07 by owner ruling, FINDING-spp-43 ADDENDUM A, determination NOT-YET, marker
complete=false final=false) and add a `corrected_by` line in the MISO row's form with your origin/main sha;
change NO other field of the row — legs (b)/(c) stay as written (no forecast evidence; SPP-60 owns them);
(2) the two annotations; (3) run python3 scripts/check_gate_a_provenance.py → EXIT 0, and
scripts/register_forecast_run.py --reindex (local preview only, commit nothing it generates) to prove the row
still parses. GATES: gate-(a) 0; audit_keepers --check 0; git diff --stat shows exactly three files + your FINDING.
RULES THAT BITE: 15, 22 (the row's `complete`/`final` stay false — no marker is claimed), 27.
EXIT: FINDING-spp-45 with the before/after `detail` text; plan §5 row → LANDED. One commit.
```

#### SPP-58 `[FABLE]` — the second, independent shift-factor identification ψ₂

```
You are lane SPP-58. MODEL: Fable claude-fable-5-1 — an identification design; the whole lane is the
construction, and it is adjudicated before any number is read. DATA PROFILE: spp.
Branch stem: claude/spp-58-psi-second-identification-j6tw.
Read CLAUDE.md freshly and in full (rules 5, 13, 14, 21, 23, 27); PRECOMMIT-spp-53 §2.1 (the FCITC rule:
T* = limit-at-bind ÷ ψ, binding-hours-weighted median; ψ_f identified by regressing the hub spread on the
flowgate's shadow price — the FIRST identification); FINDING-spp-53 §3/§6 (3,400 N↔S; the S→N-loaded set
4,206; O-1/O-2 identification width 2,645–11,121); FINDING-spp-57 §3.3 (the double attribution: intra-Oklahoma
delivery elements identify as loaded on BOTH spreads because their binding makes the OKC hub dearer) and §8
R-14; FINDING-spp-57b §2.2 (the sps_tie T* table: one transformer, two constraint names, ψ 0.047 vs 0.132 →
T* 10,705 vs 3,850; LOYO 8,395–14,796) and §7 R-19/R-20; docs/handoffs/spp57/ and spp57b/ (every instrument:
psi_regression_oks.py, aggregate_ttc.py, limits_2026_oklahoma_by_constraint.csv, spread_identification.csv);
data/raw/spp-binding-constraints/ (the 2026 RTBM daily files: constraint name, monitored element,
contingency, limit, shadow price, and whatever FLOW / marginal-value columns the 14-column schema carries —
read the README before assuming a column is absent); FINDING-spp-14 §5/§8.2 (the NODE_AREA ↔ sub-BA join;
the per-settlement-location price parquet); docs/multi-iso/04 (TTC methods).

PRECONDITIONS: SPP-57b LANDED (PR #5527). No solve in this lane — ever. FILES YOU OWN: docs/handoffs/spp58/
(your instruments + outputs), PRECOMMIT-/FINDING-spp-58, a reduced sidecar under data/raw/spp-binding-
constraints/ (+ README/SOURCES/SHA256SUMS rows) only if ψ₂ needs a column the SPP-53/57 sidecars did not
keep, and `iso_configs._spp_config` `_ns_corridor_ttc` ONLY under the band rule below. MUST NOT TOUCH: any
other ISO's files; ScenarioConfig; any keeper, sidecar, shard cell verdict (evidence text on
`measured_interface_limits` is allowed); the price-regression instruments of SPP-57/57b (read, do not edit).

THE CONSTRUCTION, in the PRECOMMIT before any ψ₂ is computed:
(1) ψ₂ must be identified WITHOUT the hub-spread × shadow-price regression. Choose and declare ONE of:
    (a) the constraint's own binding-hour physics — the RTBM row's flow-at-bind against the zonal net
    interchange the model's two/three bubbles would carry (a flow-on-flow slope, price-free); (b) a
    published SPP shift-factor / PTDF product (ITP, Marketplace constraint report) if any is public — cite
    it or record its absence; (c) a topology-derived PTDF from a reduced DC network built from public
    line data (EIA-860/HIFLD), with its misalignment stated. State why the choice is independent of (1)'s
    price channel and what it is blind to.
(2) The constituent sets are the ones already declared: n_s_corridor (SPP-53), sps_tie (SPP-57b),
    oklahoma_internal (excluded from links by SPP-57b — you re-examine ONLY whether ψ₂ also finds them
    double-attributed; you do not re-rate a link on them).
(3) THE DISAGREEMENT BAND, declared now: T*₂ for N↔S is compared with 3,400; if |T*₂ − 3,400| / 3,400 ≤ the
    band you declare (and justify from SPP-53's own LOYO spread 3,681/… — cite it), 3,400 STANDS and the
    finding is a confirmation; if outside, you do NOT edit `ttc_mw` — you STOP and the desk serves a card
    with both identifications side by side. The same rule for the S→N-loaded reading (4,206) and for the
    sps_tie T* (the 10,705-vs-3,850 width is the object: ψ₂ either collapses it or shows it is real).
(4) Every number is reported with its LOYO spread (2023/2024/2025 pooled-minus-one), as SPP-53 did.
DELIVERABLES: PRECOMMIT (construction, sets, band) pushed BEFORE computing; FINDING-spp-58 with ψ₁ vs ψ₂
per constituent, T*₁ vs T*₂ per set, the LOYO spreads, the double-attribution re-examination, and the
SPS-tie width verdict (the input SPP-54 is waiting for — say in one line what SPP-54 may use); plan §5
row → LANDED; SPP shard `measured_interface_limits` evidence appended (cell stays O). RULES THAT BITE: 5,
13 (a shift factor is physics — it regenerates forward), 14, 21 (ψ₂ is MEASURED, not a free parameter),
23, 27. EXIT: no solve, no keeper touched. Owner report: the ψ₁/ψ₂ table first.
```

#### SPP-54 `[FABLE]` — the SPS / Texas-Panhandle pocket as a third zone (P1's second lever)

```
You are lane SPP-54. MODEL: Fable claude-fable-5-1 — topology and one link are design objects; kill-grading is
adjudication. DATA PROFILE: spp. Branch stem: claude/spp-54-sps-pocket-v2kq.
Read CLAUDE.md freshly and in full (rules 1, 12, 13, 14, 16, 19, 21, 22, 24, 25, 27, 28, 29); plan §3 P1
(as ruled; the r#5 ranking put SPP-57 first — SPP-57 and SPP-57b are now both KILLED and their R-17
sends the residual-South question HERE); FINDING-spp-57b ENTIRE — §0 (the sps_tie set identifies ONLY
OK→S-loaded constituents: the ties bind on imports INTO the Panhandle; the residual South is DEARER than
the Oklahoma hub on every annual mean; the model's residual bubble — SPS's 4.65 GW of wind + SWEPCO's
AR/LA/east-Texas thermal against a 5–11 GW load — EXPORTS, so an OK→S-named link cannot be live at any
rating ≥ 3,400: "a bubble-composition defect that no link rating on the current three bubbles can reach"),
§7 R-17 (yours), R-18 (the per-zone wind-shape rebuild lowered the OK+S region's own generation in
h8507–h8508 and raised unserved 89 → 444 MWh — a per-zone wind reconciliation against the EIA-930 SWPP
profile in the Dec-21 stuck-demand window is owed BEFORE any three-zone solve), R-20 (do NOT rate an SPS
link on the SPP-57b ψ table — SPP-58's ψ₂ is your rating input); FINDING-spp-57 §2 (the CSWS split —
reuse), §8 R-13 (SPS reads DEARER than the Oklahoma hub, +4.74 / +12.07 on the 2024–2025 annual mean, with
a two-sided hourly distribution — your design starts from that table, not from P1's "persistently
negative" prose); FINDING-spp-14 §5 (sps_tie: 0.258 / 0.342 / 0.282 binding share at $52 / $70 / $59 —
2024 is the largest footprint); FINDING-spp-32 §2 (SPS is its own EIA-930 sub-BA — no sub-allocation
needed, unlike CSWS); the three-zone implementation commits f5926636 / 7bfe047d (cherry-pick the
registry/zonal-share/wind-shape scaffolding, re-pointed from SPP-Oklahoma to SPP-SPS); FINDING-spp-43
(keeper-3 is your control — recipe in results/calibration/spp43_screened_B/meta.json).

PRECONDITIONS: SPP-43 LANDED (keeper-3). SPP-58 is running in parallel: your DESIGN, census and wind
reconciliation run NOW; your link RATING waits for FINDING-spp-58 (its one-line "what SPP-54 may use"); your
SOLVE waits for the rating. SPP-44 is solving in parallel — ask the desk before any solve (rule 12).
FILES YOU OWN: `_spp_config` (SPP-North / SPP-South / SPP-SPS + ONE new link South↔SPS beside the N↔S 3,400
link, which stays), zone_assignment.py SPP maps (NM + the Panhandle counties → SPP-SPS), curate_zonal_shares.py
(`SPS` → SPP-SPS; CSWS stays South, whole), renewables.py SPP allocation, the wind-shape builder's per-zone
site set, basis/meanzero.py SPP rows (SPS on the NM/Panhandle proxy — cite), tests, docs/handoffs/spp54/,
PRECOMMIT-/FINDING-spp-54, the screen bundle (TEMPORARY), results/calibration/spp54_sps_B/ if the screen
clears, the SPP shard cell you move. MUST NOT TOUCH: any other ISO's config, maps or shard; ScenarioConfig
(no field — topology, G8); offer bands (1.0); keepers/SPP.json (promotion = card P15); the N↔S 3,400 value
(rule 14 — SPP-58 owns any question about it).

DESIGN, zero-LP, in the PRECOMMIT before any limit, ψ or price is read:
(A) THE POCKET: SPP-SPS = the SPS sub-BA (TX Panhandle + NM). Census: SPS load share by year (EIA-930
    sub-BA), its fleet (wind MW, thermal MW by class, from EIA-860 BA=SWPP filtered to the SPS NODE_AREA /
    state-county set), and the residual South after removing it. Σ shares = 1.0 every hour; the
    redistribution identity to 1e-9.
(B) THE LINK: South↔SPS, ONE link, rated from SPP-58's ψ₂ on the sps_tie set (limit-at-bind ÷ ψ₂, the
    SPP-53 median rule) — the rule and the set declared now, the number filled in when SPP-58 lands.
    DIRECTION: declared from the ties' own binding direction (imports INTO the Panhandle bind — OK→S-loaded,
    SPP-57b §0) AND from the SPS bubble's own balance (wind 4.65 GW vs its load): state which way the pocket
    is expected to flow in the hours the ties bind, ex ante, and what the measured SPS-dearer-than-OK price
    table (R-13) implies for the sign of the zonal spread. If the two expectations conflict, say so — that
    conflict IS the object.
(C) THE WIND RECONCILIATION (R-18): the rebuilt per-zone wind shapes summed and reconciled to the EIA-930
    SWPP profile, hourly, all three years, with the Dec-21-2025 stuck-demand window itemised; a mismatch
    > a declared tolerance is a STOP before any solve (the pocket must not manufacture unserved energy).
(D) EVERY REGISTRY gains SPP-SPS; validate_topology; six keepers' solve surface 0 moved; fleet_only
    three-zone census.
SCREEN (rule 29): year = 2024 — the largest sps_tie footprint (0.342 share, $70), named here, NEVER the
year with the biggest residual. STOP gate with the E-6 thresholds: (i) the South↔SPS link live (at bound
≥ 5 % of hours) and in the declared direction ≥ 55 % of at-bound hours; (ii) the sign of the modelled
SPS−South spread matches the measured SPS−OK-hub sign on the annual mean (R-13's table, 2024 +4.74);
(iii) re-curtailment > 0, REPORTED; (iv) unserved ⊆ the control's own hours (keeper-3, 2024: 0 MWh — so
any unserved is a STOP); (v) fuel families within [0.1×, 10×] (hydro against the reference's vintage —
state, not a miss). Control = keeper-3 (29b form 4) after G-DRIFT. The gate may kill, never promote,
never reads C3a/C3b. FULL SPAN only if the screen clears; LOYO; DOF ledger (zero tuned; the CSWS split
and ψ₂ are measured); delete the screen bundle before the PR (29c); register as a CANDIDATE; stamp the
SPP shard cell; do NOT edit keepers/SPP.json — report; the desk serves P15.
RULES THAT BITE: 1, 12, 13, 14, 16, 19, 21, 22, 24, 25, 27, 28b, 29(a)(b)(c).
EXIT: PRECOMMIT pushed before any read; FINDING-spp-54 with the census, the wind reconciliation, the
rating (with SPP-58's ψ₂ cited), the STOP-gate table beside SPP-57b's, LOYO if the span ran, the P15
recommendation; plan §5 row → LANDED. Owner report: the STOP-gate table first.
```

#### SPP-51 `[FABLE]` — the priced seams (MISO / AECI / ERCOT), P2's forward mechanism

```
You are lane SPP-51. MODEL: Fable claude-fable-5-1 — three adjudications ride this lane (the anchor map,
the HH+basis heat-rate correction, the ERCOT limit-vs-clip), plus a screen. DATA PROFILE: spp.
Branch stem: claude/spp-51-priced-seams-t4nb.
Read CLAUDE.md freshly and in full (rules 1, 12, 13, 14, 19, 21, 24, 25, 27, 28, 29); plan §3 P2 (as ruled:
served schedule first, priced seam default-off; SPP-51 validates) and P3 (ERCOT 820 MW default-off
neighbour); FINDING-spp-33 ENTIRE — the `hr_by_year` RT numbers (MISO 9.82 / 10.55 / 9.90 · AECI 10.30 /
12.08 / 8.32 · ERCOT 23.70 / 15.87 / 10.76), §4 (R2: the registered marginal_heat_rates divide by bare
Henry Hub where the pricing formula uses HH + gas_basis; corrections 10.09 / 10.23 / 16.78), §2/§6 R1 (the
`_NEIGHBOR_LMP_ISO` anchor map reaches none of SPP's three anchors — the producer emits one wrong-anchor row
silently; §A carries the anchor-correct arithmetic), §5/§6 R3 (`_HR_GAS_ELASTIC`'s global name key blocks
SPP↔MISO forward elasticity — PJM owns "MISO"; FORWARD-ONLY, inert for the keeper: REPORT, do not fix —
desk R-n), the ERCOT 820 MW limit under its own measured ±835 MW clip in 547 / 128 / 21 h, and the
SWPP interchange duration curves by DIBA (your footprint); FINDING-spp-20 §5 R-7 (the producer STOP
instruction — now lifted for THIS lane: you MAY edit the producer's anchor map, per-ISO, no other ISO's
row); config/interchange/spec.py SPP blocks and INTERFACE_NEIGHBORS["SPP"]; the MISO keeper
2026-09-07-miso-233-spp-hourly (MISO's own priced SPP seam — rule 25: read its constants, NEVER edit them;
its shard is not yours); scripts/run_calibration_full.py --help (`--priced-interchange`); the matrix row
for the priced-seam mechanism and SPP's cell (U); FINDING-spp-43 (keeper-3 = control; recipe in
spp43_screened_B/meta.json).

PRECONDITIONS: SPP-43 LANDED (keeper-3). SPP-44 and possibly SPP-54 solve in parallel — ask the desk before
any solve (rule 12). FILES YOU OWN: config/interchange/spec.py SPP blocks ONLY (`hr_by_year`, the corrected
marginal heat rates with the HH+basis derivation cited, the ERCOT limit decision), the per-ISO anchor map in
scripts/data/derive_neighbor_hr_by_year.py (+ an explicit failure where it used to `continue` silently — SPP-33
R1), tests, the SPP shard's cell for the priced-seam mechanism, PRECOMMIT-/FINDING-spp-51, the screen bundle
(TEMPORARY), results/calibration/spp51_seams_B/ if the screen clears. MUST NOT TOUCH: any other ISO's
spec.py block or anchor row; neighbor_price.py's `_HR_GAS_ELASTIC` key (R3 is reported, not fixed);
ScenarioConfig (the flag exists); keepers/SPP.json (promotion = card P15); offer bands.

DO, in order:
(0) PRECOMMIT before any solve: the three adjudications written out — (a) the anchor map entry per SPP
    neighbour with the settlement location / hub each anchors to and why; (b) the HH+basis correction:
    which heat rate the pricing formula actually multiplies (cite the line) and the corrected values;
    (c) ERCOT: keep the registered 820 MW or move to the measured ±835 clip — rule 14 decides, the
    misalignment (DC-tie rating vs metered flow) stated either way. Then the ZERO-LP footprint: the
    served-vs-priced offer-array delta per neighbour per year, and the SWPP interchange duration curves
    (SPP-33) — the SCREEN YEAR is the year of largest measured seam footprint (MWh through the three
    seams), named here, never the year with the biggest C3a residual. STOP gate, structural: (i) the
    modelled interchange duration curve per seam has the measured sign in ≥ 55 % of hours and its annual
    net within an order of magnitude of EIA-930 DIBA; (ii) the priced seam's flow responds to the
    neighbour price in the declared direction (import when the neighbour is cheaper) — a slope sign test,
    ex ante; (iii) no non-target load-bearing criterion flips PASS → FAIL; it never reads C3a/C3b.
    G-DRIFT vs keeper-3's git_sha.
(1) IMPLEMENT the spec.py SPP blocks + anchor map + tests; prove the six keepers' keys unmoved and MISO's
    seam constants byte-identical (rule 25).
(2) SCREEN: keeper-3's recipe + `--priced-interchange` on the named year; grade against the gate only; a
    kill is the result. Report beside it, never gated: C3a/C3b/C3c, the hourly seam flows vs measured.
(3) FULL SPAN only if it clears; LOYO; delete the screen bundle before the PR; register as a CANDIDATE;
    stamp the SPP shard cell (U → K / R / I / O with evidence); do NOT edit keepers/SPP.json.
RULES THAT BITE: 1, 12, 13, 14, 19, 21 (hr_by_year values are MEASURED — the DOF ledger says so), 24, 25,
27 (spec.py is core: Edit locally, git push, fetch-back verify), 28b, 29(a)(b)(c).
EXIT: FINDING-spp-51 with the three adjudications, the footprint table (why the screen year), the STOP-gate
table, LOYO if the span ran, the P15 recommendation; plan §5 row → LANDED. Owner report: the three
adjudications and the STOP-gate table first.
```

#### SPP-60 `[FABLE]` — the SPP T1-H recipe + forecast data intake (owner ruling Q59 routed the T1-H half to this desk)

```
You are lane SPP-60. MODEL: Fable claude-fable-5-1 — a forecast recipe is a design object and every intake
gap is an adjudication. DATA PROFILE: spp. Branch stem: claude/spp-60-t1h-recipe-w3pd.
Read CLAUDE.md freshly and in full (rules 13, 15 — the FORECAST dashboard paragraph: the SINGLE
register_forecast_run.py path, the generated namespace, NEVER the backcast registry — 22 — forecast-mode
2026+ is permitted; no measured H1-2026 actuals; the crossover window 2024–H1 2026 is scored in forecast
mode against actuals as a DIAGNOSTIC — 27, 28); the Capacity Evolution section (steps 0–7 and which gate
owns which step); docs/forecast-development-plan-2026-07.md (the tier ladder, T1-H's definition, §2.1b's
legs (a)/(b)/(c), §7.5); docs/handoffs/capx-director-ledger-2026-08.md §0bb(a) (Q59, verbatim: "SPP
onboarding split — the board-row half here, the T1-H recipe half routed to the SPP desk") and the SPP row
of frontend/data/forecast/program-status.json (its legs (b)/(c) read "no forecast evidence"; SPP-45 re-keys
leg (a) — you fill (b)/(c) only with MEASURED results); plan §6 manifest rows 11–15 (LTLF edition, queue
caps, RPS floors, PRM, confirmed retirements) and §7 G13 (`load_forecast/spp.py` needs a real edition +
vintage); scripts/lib/load_forecast/spp.py and its six siblings; scripts/lib/confirmed_retirements/spp.py,
nuclear_license_status/spp.py, transmission_expansion/spp.py (SPP-20 placeholders — what each returns
today); FINDING-spp-12 §7 (Cooper 2034 SLR under review; Wolf Creek 2045 — R-g); the most recent MISO T1-H
PRECOMMIT/FINDING (`git log --grep=T1-H -- docs/handoffs | head`) as the recipe template and the readiness
battery (`ff_readiness_battery.py`, GOLDEN_ISOS); FINDING-spp-43 (keeper-3's recipe is the backcast base).

PRECONDITIONS: SPP-43 LANDED (keeper-3); SPP-45 LANDED before you write anything into the board row (until
then, your board edits wait — everything else proceeds). FILES YOU OWN: scripts/lib/load_forecast/spp.py
(a real SPP LTLF edition + vintage, cited — manifest row 11), the SPP rows/modules of the
confirmed-retirement / nuclear-licence / transmission-expansion / planned-additions / queue-cap /
fuel-trajectory registries (SPP entries only), data/raw/ intake dirs for those (README/SOURCES/SHA256SUMS,
raw immutable), the T1-H hindcast bundle + its sidecar under frontend/data/hindcast/ via
register_forecast_run.py, the SPP board row's legs (b)/(c) (after SPP-45; measured verdicts only),
PRECOMMIT-/FINDING-spp-60. MUST NOT TOUCH: the backcast keeper, its recipe, any backcast registry/sidecar/
bench/shard; GOLDEN_ISOS (report what the readiness battery says — the desk carries it to the capx
director); any other ISO's forecast rows; ScenarioConfig defaults; calibration-complete.json.

DO, in order:
(0) THE GAP TABLE, zero-LP, in the PRECOMMIT: every input a T1-H hindcast reads (walk the MISO T1-H
    recipe and the capacity-evolution steps 0–7), and for SPP: EXISTS (cite) / PLACEHOLDER (what SPP-20
    left) / MISSING. For each MISSING or PLACEHOLDER: the public source (SPP LTLF / ITP Load Forecast
    edition and vintage ≥ 2020; SPP GI queue reports; SPP Planning Criteria PRM 0.16 — already registered;
    RPS floors by state; EIA-860 proposed pipeline for SWPP; the instruments SPP-12 §7 found), fetched in
    this lane if a session can reach it (rule 22: data intake needs no authorization), else a manual
    manifest row. Rule 13 on every input: it must regenerate for a forward year.
(1) THE RECIPE: keeper-3's backcast recipe in forecast mode over the crossover window (2024–H1 2026,
    forward drivers, NO measured H1-2026 actuals), then the T1-H span the forecast plan defines — declared
    in the PRECOMMIT with every default it inherits and every SPP-specific value cited; the memory class
    (per_plant, ~5.3 GB/yr); G-DRIFT vs keeper-3.
(2) THE HINDCAST SOLVE (years sequential; ask the desk before starting — rule 12), scored on the forecast
    rubric's own legs, reported at full magnitude whatever it reads; register via register_forecast_run.py
    ONLY; --reindex locally to prove the row renders; commit the sidecar, never the generated namespace.
(3) LEGS (b)/(c) on the board row from the registered result (the Q34 form); the readiness battery run
    and its verdict REPORTED (GOLDEN_ISOS untouched); every intake defect routed with its owner.
RULES THAT BITE: 13, 15 (forecast namespace, single path), 22 (crossover = forecast mode; no H1-2026
backcast), 27 (any ≥300-line file → Edit locally, git push, verify), 28 (a forecast-lane mechanism cell
moves in the SPP shard's fc column only).
EXIT: FINDING-spp-60 with the gap table, the recipe, the hindcast legs table, the battery verdict; plan §5
row → LANDED; plan §1 row 6 updated to "T1-H registered; GOLDEN_ISOS pending the capx director". Owner
report: the gap table and the legs table first.
```

#### SPP-55 `[FABLE]` — VRL-based scarcity: an in-LP reserve demand curve on SPP's own published steps (issued r#10)

```
You are lane SPP-55. MODEL: Fable claude-fable-5-1 — a mechanism design (which reserve object, on which
published curve, in which LP row family) and a kill-graded screen. DATA PROFILE: spp.
Branch stem: claude/spp-55-vrl-scarcity-d7xm.
Read CLAUDE.md freshly and in full (rules 1, 4, 5, 12, 13, 17, 19, 21, 24, 25, 27, 28 — 28c BINDS if you add a
field: matrix row + a cell in EVERY shard — 29); plan §3 P4 ("defer reserve co-optimisation — M2 LAST", still
binding: you are NOT SPP-56; you build ONE scarcity demand curve, not a three-product co-opt priced on
measured MCPs) and P5 ("no scarcity/ORDC seed at registration; SPP-55 designs the VRL-based mechanism after a
keeper exists" — the keeper exists: keeper-3); FINDING-spp-12 "VRL steps" (Exhibit 4-1: Resource Capacity
$100,000/MW · Global Power Balance $50,000/MW · Resource Ramp $5,000/MW · Operating Constraint $1,500/MW,
non-escalating · M2M = MISO's shadow price · Spinning Reserve $250/MW — "the binding ceiling in an SPP shortage
is the $250/MW spinning VRL and the $50,000/MW power-balance VRL"); FINDING-spp-price-family §1.3 (your measured
target: the >$200 hours — 42 / 59 / 68 — sit at ORDINARY load (only 3 / 5 / 3 in the top-5 % load hours), at
market heat rates 79–93× gas, in a model with no scarcity mechanism and zero slack/dump — C3c is a separate
object from the load-driven level miss, unmoved by any band) and §6; data/raw/spp-or-mcp/ (RTBM_MCP_2023–2025,
da-mcp — the measured per-reserve-zone MCPs; README: manifest row 9, "SPP-56 input only" under P4 — you may
READ them for the footprint and the gate, never price a product on them); src/market_sim/config/
reserve_config.py (how every other ISO's reserve requirements and demand-curve steps are registered — the
MISO RBDC entry is your closest template; ERCOT's ORDC is a post-solve overlay and is NOT the pattern);
the matrix rows ordc_scarcity_overlay, energy_reserve_coopt, dynamic_reserve_requirements,
reserve_family_dual_sidecar and SPP's cells (all U or ·); CLAUDE.md rule 15's reserve_family sidecar
paragraph (the ONLY artifact in which a reserve family's binding is observable); FINDING-spp-44 §2 (rule 19:
nothing floors SPP's gas fleet; no scarcity, no floor, no bridge armed) and §6 R-17/R-18 (the gas-split
object is NOT yours — do not let a reserve requirement become a back-door commitment floor: if the curve's
main effect is to start ST_GAS plants, say so and stop); FINDING-spp-43 (keeper-3's recipe in
spp43_screened_B/meta.json = your control); SPP-12/SPP-13 transcriptions of SPP's Planning Criteria and
Market Protocols (reserve requirement definitions: contingency reserve = largest single contingency, the
spin share, regulation).

PRECONDITIONS: SPP-43 LANDED (keeper-3 = control); SPP-44 LANDED (PR #5535 — its 28c every-shard edit is
merged, so yours will not collide; rebase LAST and re-run check_mechanism_matrix). Ask the desk before any
solve (rule 12; SPP-54 / SPP-51 / SPP-60 may be solving).
FILES YOU OWN: reserve_config.py's SPP entry ONLY (requirements by product, the VRL step curve — every
$/MW and MW cited to SPP's own publication and its page), at most ONE new ISO-exclusive ScenarioConfig gate
(default off, `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` drop value declared; seven keys unmoved by key diff),
the LP-side wiring ONLY if the existing reserve row family cannot express a stepped demand curve for SPP
(state which existing family you use FIRST; a new family is a STOP-and-report, not a build), tests, the
matrix row (if a field) + a cell line in EVERY shard, docs/mechanism-testing-matrix.md §5.7, PRECOMMIT-/
FINDING-spp-55, the screen bundle (TEMPORARY), results/calibration/spp55_vrl_B/ if the screen clears, the
SPP shard cells you move. MUST NOT TOUCH: any other ISO's reserve entry, branch or cells beyond one `·`
line; offer bands (rule 25); keepers/SPP.json (promotion = card P15); the ORDC post-solve overlay path
(rule 19 — one scarcity mechanism per ISO, and yours is in the LP); reliability_floor_overrides; the
SPP-44 bridge field (it stays default-off, R).

DO, in order:
(0) DESIGN + MEASURE, zero-LP, in the PRECOMMIT before any solve: (a) rule-19 enumeration — every
    mechanism that could price scarcity or reserves in SPP today (expected: none armed; ORDC overlay `·`;
    co-opt off) and the statement that the curve REPLACES nothing and STACKS on nothing; (b) THE OBJECT:
    which reserve product carries SPP scarcity in the LP — the contingency/spinning requirement with the
    $250/MW spinning VRL as the first step and the $50,000/MW power-balance VRL as the ceiling (a two-step
    demand curve in the reserve balance row, MISO-RBDC form), requirement = SPP's own published rule
    (largest single contingency; the spin share) regenerating from the fleet each year (rule 13);
    (c) THE FOOTPRINT by year from the measured RTBM MCPs: hours the spinning MCP ≥ the $250 step (reserve
    shortage hours) and hours the energy price carries the power-balance VRL; the SCREEN YEAR = the year
    with the largest measured shortage-hour footprint, named here, NEVER the year with the biggest C3c
    residual; (d) rule 17 for the row: driver (SPP's own VRL), window (the shortage hours the curve may
    price), forward story (VRLs are tariff parameters; requirements regenerate from the fleet); (e) THE
    STOP GATE, structural: (i) the reserve row binds (dual > 0) in ≥ a declared share of the MEASURED
    shortage hours and in ≤ a declared share of non-shortage hours (window agreement, both sides);
    (ii) when it binds, the energy price rises by the order of the VRL step (the reserve_family sidecar's
    dual against $250 / $50,000 — the identity the design asserts); (iii) no ST_GAS / CC commitment
    side-effect beyond what the requirement's MW implies (the SPP-44 R-17 guard: the curve prices
    scarcity, it does not start plants — report ΔE by class); (iv) no non-target load-bearing criterion
    flips PASS → FAIL; it NEVER reads C3c or C3a. G-DRIFT vs keeper-3's git_sha. (f) DOF ledger: every
    step and requirement MEASURED (published), zero tuned.
(1) IMPLEMENT: the reserve_config SPP entry, the gate if needed, tests (seven keys unmoved; every other
    ISO's reserve rows byte-identical), matrix row/cells.
(2) SCREEN on the named year (keeper-3's recipe + the gate); grade against the STOP gate only from the
    screen's reserve_family_<year>.parquet and system sidecars; a kill is the result. Report beside it,
    never gated: hours > $200 vs 42/59/68, the C3c row, load-weighted price, unserved.
(3) FULL SPAN only if it clears; LOYO; delete the screen bundle before the PR (29c); register as a
    CANDIDATE; stamp the SPP shard cells (U → K / R / I / O with evidence); do NOT edit keepers/SPP.json.
GATES before push: check_mechanism_matrix.py 0; pytest tests/unit/config tests/unit/model tests/unit/pipeline
-q; tests/regression/test_persisted_identity.py; solve_surface_register.py --diff 0 moved for the six;
audit_keepers --check; parity.
RULES THAT BITE: 1, 4 (prices are duals — the VRL enters as a demand-curve step, never as an adder),
5, 12, 13, 17, 19, 21, 24, 25, 27 (reserve_config.py / scenarios.py are core: Edit locally, git push,
fetch-back verify), 28c, 29(a)(b)(c).
EXIT: PRECOMMIT pushed before any solve; FINDING-spp-55 with the design (a)–(f), the footprint table,
the STOP-gate table, the reserve-dual identity check, LOYO if the span ran, the P15 recommendation;
plan §5 row → LANDED. Owner report: the footprint table and the STOP-gate table first.
```

### W5 — the lever queue (DISPATCHABLE since r#7 — SPP-40 landed; SPP-57 issued r#7 in full below the table)

| Lane | Model | Charter stub (expanded by the desk at issuance) |
|---|---|---|
| SPP-51 `[FABLE]` — **ISSUED r#9** (charter above) | it carries three SPP-33 adjudications: R1 the `_NEIGHBOR_LMP_ISO` anchor map, R2 the `HH + gas_basis` heat-rate correction (10.09 / 10.23 / 16.78 vs the registered values), and ERCOT's 820 MW limit under its own measured ±835 MW clip in 547/128/21 h; `hr_by_year` RT to arm: MISO 9.82/10.55/9.90 · AECI 10.30/12.08/8.32 · ERCOT 23.70/15.87/10.76 | arm `hr_by_year` on `INTERFACE_NEIGHBORS["SPP"]` MISO/ERCOT; A/B served vs `--priced-interchange` on the P7 screen year; keeper = control (29b); STOP gate = interchange duration curve sign/magnitude vs EIA-930; matrix cell for the seam mechanism |
| SPP-52 `[OPUS]` | execution | curtailment as a first-class metric (playbook §8.3): reference curtailment rate → the uncurtailed fallback set; report modeled vs reported curtailment; wind-shape arming if SPP-32 left it as an input only |
| SPP-53 | — | **LANDED in W3** (P13). Its successor lever is SPP-58 below |
| SPP-54 `[FABLE]` — **DESIGN LANDED 2026-09-07, NO SOLVE** (FINDING-spp-54: C-3 wind-reconciliation STOP → R-21 desk card; rating after SPP-58; solve half re-issued from `8d427adc` once both are cleared) | topology change | the SPS / Texas-Panhandle pocket as a third zone (own sub-BA `SPS`, 12.6 % of load; Lubbock FCA). RANKED against SPP-57 by SPP-12's per-flowgate binding share + shadow price vs the N↔S corridor (P1 as ruled); the higher-ranked pocket is issued first; scored leave-one-year-out (rule 22) |
| SPP-57 `[FABLE]` — **screen KILLED r#8** (FINDING-spp-57); **SPP-57b ISSUED r#8** (charter in W4c above, R-12 construction) | topology change | an Oklahoma pocket (OKC/Tulsa split of SPP-South — Osage–Webber $75/MWh and Russett–S.Brown $61/MWh are the market's two highest-value constraints, audit §6.1). Needs a `CSWS` sub-allocation for its load share and a TTC; same ranking test and LOYO scoring as SPP-54 |
| SPP-55 `[FABLE]` — **ISSUED r#10** (SPP-44 merged, hold lifted; charter above); its measured target is FINDING-spp-price-family §1.3 (spikes at ordinary load, 79–93× gas, no scarcity mechanism, zero slack) | mechanism design | VRL-based scarcity: an in-LP reserve demand curve (closer to MISO's RBDC than to the post-solve ORDC overlay), designed against the SPP tail counts; screen structural only |
| SPP-56 `[FABLE]` | mechanism design, LAST | reserve co-optimisation Reg/Spin/Supp on the `da-mcp`/`rtbm-mcp` measured prices; must first prove non-inertness (MISO precedent) |
| SPP-58 `[FABLE]` — **LANDED 2026-09-07** (`FINDING-spp-58-2026-09-07.md`; PRECOMMIT pushed first): ψ₂ = a DC-network PTDF/OTDF on public HIFLD geometry + EIA-860 plants, price-free. OUTSIDE the declared 1.92× band on EVERY object — N→S like-for-like 11,022 vs 3,400 (ψ₁'s drop-2024 fold), S→N 13,175 vs 4,206, `sps_tie` **1,600 vs 10,705** — so `ttc_mw` is UNTOUCHED and the desk holds the card (R-21/R-22). Potter County width COLLAPSED (ψ₂ ratio 1.19, OTDF > PTDF, the reverse of ψ₁). Double attribution is REAL physics (all 3 resolved `oklahoma_internal` elements load on both transfers). Franklin 161/69 (44 % of the corridor's hours) is UNRESOLVABLE — no sub-115 kV public line data (R-23). **SPP-54's rating input: 1,600 MW** (the ties are the cut-set, K3 = 1.000) | TTC asymmetry is a design object | the N↔S link as an ASYMMETRIC pair — N→S 3,400 / S→N 4,206 MW by SPP-53's own FCITC rule (FINDING-spp-53 §3) — with a SECOND, independent shift-factor identification (the first used SPP's 2023–25 hub spread × shadow prices; the second must not) so ψ is not a one-source number; rule 14; keeper = control; LOYO; ranked after SPP-57 |
| SPP-59 `[OPUS]` (reserved r#6) | consolidation, zero-behaviour | SPP-32 R-3/R-4/R-5: fold MISO's `_reference_curtailment_rate` branch into the provider table, one ISO-generic wind-shape builder, move `_SPP_SUBBA_ZONE_GROUPS` beside MISO's in `eia930/zonal_shares.py`; byte-identity of every output is the gate; needs the MISO lane's consent (their files) — held until the MISO calibration lane is idle |

#### SPP-57 `[FABLE]` — the Oklahoma pocket as a third zone (P1's first lever; issued r#7)

```
You are lane SPP-57. MODEL: Fable claude-fable-5-1 — a topology change and two link TTCs are design
objects, and the screen's kill-grading is adjudication. DATA PROFILE: spp.
Branch stem: claude/spp-57-oklahoma-pocket-m4rt.
Read CLAUDE.md freshly and in full (rules 1, 12, 13, 14, 16, 19, 21, 22, 24, 25, 27, 28, 29); plan §3
P1 (as ruled + the r#5 ranking), §7 G8/G13; FINDING-spp-14 §5 (the four-group flowgate table: the
`oklahoma_internal` group — OSAGE_OG / WEBBTAP4 / RUSSETT / SBROWN, or both areas ∈ {OKGE, CSWS, GRDA,
WFEC} — binds 4,713 / 4,698 / 5,822 h at $261.55 / $263.58 / $311.80 mean |shadow| in 2023/24/25, vs
the N↔S corridor's 0.555 / 0.516 / 0.631 share) and §8.2 (the NODE_AREA ↔ sub-BA join); FINDING-spp-40
§3 and §7.2 (three readings of the same object: ~$1 modelled vs $12–17 measured |S−N| spread, 0.0 %
wind re-curtailment vs 8.5–10.6 % reference, 7–9 negative hours vs ~1,000 — "the two bubbles cannot
hold what SPP's Oklahoma-internal constraints do"); PRECOMMIT-/FINDING-spp-53 (the FCITC construction
and its reduced sidecar of the n_s_corridor rows — your two new links use the SAME construction on
the oklahoma_internal rows, declared before any limit is read); FINDING-spp-32 §2 (zonal shares,
`_SPP_SUBBA_ZONE_GROUPS`: South = CSWS, GRDA, OKGE, SPS, WFEC) and §3 (per-zone wind shape); FINDING-
spp-20 (every registry SPP-20 touched — each needs a third-zone entry); iso_configs._spp_config;
zone_assignment.py's SPP maps; docs/multi-iso/04 (TTC method) and 05 §6.

PRECONDITIONS: SPP-40 LANDED (keeper-1 exists). SPP-42 (the repaired-input re-baseline) is running in
parallel: your DESIGN and every zero-LP step run NOW; your SOLVE waits until SPP-42 lands (or the desk
tells you it stopped), because the control is the keeper CURRENT AT YOUR PRECOMMIT and a control whose
inputs are about to be repaired makes the differencing unreadable. Re-pin and re-audit G-DRIFT if the
keeper moves between PRECOMMIT and solve.
FILES YOU OWN: src/market_sim/config/iso_configs.py `_spp_config` (a third Zone + two TransferLinks,
the N↔S link retired or re-rated per your construction — state which and why), zone_assignment.py
SPP state/sub-BA → zone maps, scripts/data/curate_zonal_shares.py `_SPP_SUBBA_ZONE_GROUPS` + the CSWS
sub-allocation, renewables.py SPP zone allocation, the wind-shape builder's per-zone site set, data/
fuel/basis/meanzero.py SPP rows, a NEW reduced sidecar data/raw/spp-binding-constraints/rtbm_bc_
oklahoma_limits_2026.parquet (+ README/SOURCES), tests, PRECOMMIT-/FINDING-spp-57, the screen bundle
(TEMPORARY), results/calibration/spp57_okpocket_B/ if the screen clears, and the SPP shard's cell for
the topology/interface mechanism you move. MUST NOT TOUCH: any other ISO's config, maps or shard;
ScenarioConfig (NO new field — a zone is topology, G8); offer bands (1.0 — rule 25); keepers/SPP.json
(promotion is card P15 — the DESK's act, never yours); calibration-complete.json.

DESIGN, all zero-LP, all in the PRECOMMIT before any limit or price is read:
(A) THE POCKET. `SPP-Oklahoma` = OKGE + GRDA + WFEC + the Oklahoma share of CSWS (AEP-PSO); the rest
    of CSWS (SWEPCO: AR/LA/TX) + SPS stay `SPP-South`. CSWS spans four states, so its sub-allocation is
    a rule-14 misalignment: identify the PSO/SWEPCO split from a measured series (EIA-861 retail sales
    by utility-state, or the CSWS load by NODE_AREA if SPP-14's join reaches it) and DOCUMENT it as a
    reconciled measured value, never a guess. Load shares from the same EIA-930 sub-BA hourly series
    SPP-32 used; Σ = 1.0 every hour; the redistribution identity to 1e-9.
(B) THE LINKS. Two links, North↔Oklahoma and Oklahoma↔South, each rated by the SPP-53 FCITC
    construction on the `oklahoma_internal` flowgate set (limit-at-bind ÷ a shift factor identified
    from SPP's own OKC/Tulsa-vs-North/South hub spread × shadow prices). Write the construction rule,
    the flowgate membership rule and the direction convention FIRST, then read the limits. The rule-14
    misalignment (parallel flowgates collapsed into one link) stated on each link.
(C) THE IDENTIFICATION. From SPP-14's per-hub parquet: mean/p90 |Oklahoma − North| and |Oklahoma −
    South| by year; the N↔S two-point spread SPP-40 §3 could not hold is now a three-point object —
    state the expected sign and season of each link's binding from the flowgate data, ex ante.
(D) EVERY REGISTRY: each SPP-20 dict gains the third zone (renewable allocation, wind shape, gas
    basis, state→zone, sub-BA→zone, transmission vintage); `validate_topology` passes; six keepers'
    solve surface 0 moved; `fleet_only` census per zone (plants, MW by class, wind/solar MW) before
    any solve.
SCREEN (rule 29): year = 2025 — the largest `oklahoma_internal` footprint (5,822 h, 0.665 share,
$311.80), named here, NOT the year with the largest residual. STOP gate, structural, with EX-ANTE
DOMINANCE THRESHOLDS (desk E-6 — a strict inequality killed SPP-40 on a 22-hour tie): (i) each new
link is live (at bound ≥ 5 % of hours) and binds in the flowgate-named direction in ≥ 55 % of its
at-bound hours; (ii) the sign of each modelled zonal spread matches the measured hub spread on the
annual mean; (iii) wind re-curtailment > 0 (the pocket must trap something) — magnitude REPORTED, never
gated; (iv) no unserved energy beyond the hours SPP-42's FINDING already names; (v) fuel classes within
[0.1×, 10×] of EIA-923. Control = the keeper current at your PRECOMMIT (29b, form 4) after a G-DRIFT
audit. The gate may kill, never promote, and never reads C3a/C3b.
FULL SPAN only if the screen clears: one --year 2023 2024 2025 invocation; LOYO (rule 22) reported —
every year's criterion table beside the control's, full magnitude; DOF ledger (expected: the CSWS
split is a MEASURED value, not a free parameter — say where it came from; zero tuned scalars).
Delete the screen bundle before the PR (29c). Register the full-span run (rule 15) as a CANDIDATE;
stamp the SPP shard cell you moved; do NOT edit keepers/SPP.json — report and the desk serves P15.
RULES THAT BITE: 1 (this is a structural mechanism: it stays if it is real even if a band worsens),
12 (≤ 2 per-plant solves — coordinate with SPP-42 through the desk), 13, 14, 16, 19, 21, 22, 24,
25, 27, 28b, 29(a)(b)(c).
EXIT: PRECOMMIT pushed before any read of limits or prices; FINDING-spp-57 with the design (A)–(D),
the STOP-gate table, the LOYO table vs the control, and the P15 recommendation (candidate / not);
plan §5 row → LANDED. Owner report: the STOP-gate table and the spread identification first.
```

### W6 — routed

SPP-60 `[FABLE]`: T1-F hindcast, `program-status.json` SPP row, `GOLDEN_ISOS`, goldens — **chartered by the
capx director** after a card (P8). This desk never writes it.

---

## 9. Findings index (append as they land)

| Lane | FINDING | Landed |
|---|---|---|
| SPP-10 | `docs/handoffs/FINDING-spp-10-2026-09-06.md` / `docs/multi-iso/spp-data-audit.md` | 2026-09-06 (PR #5254) |
| SPP-11 | `docs/handoffs/FINDING-spp-11-2026-09-06.md` | 2026-09-06 (PRs #5239, #5243, #5247) |
| SPP-12 | `docs/handoffs/FINDING-spp-12-2026-09-06.md` | 2026-09-06 (PR #5285) |
| SPP-13 | `docs/handoffs/FINDING-spp-13-2026-09-06.md` | 2026-09-06 |
| SPP-14 | `docs/handoffs/FINDING-spp-14-2026-09-06.md` | **LANDED** (incl. the r#4 am.1 addendum: items A/B/C were already landed by the parallel SPP-14 session, PR #5335, and are verified at HEAD rather than duplicated; the NODE_AREA↔EIA-930 sub-BA join table is FINDING §8.2 — all 17 tokens match 1:1, but reserve zone 21's `WACM`/`PRPA`/`WAUW` (232 SLs) have no sub-BA token at all) — the portal route is anonymous HTTPS; rows 5/6/7/9 served, row 8's four-group table computed (SPP-57 > SPP-54, both legs, all years), gate PASS 0.0000 %; row-8 schema correction removes SPP-53's effective-limit input for 2023–2025 |
| SPP-15 | `docs/handoffs/FINDING-spp-15-2026-09-06.md` | 2026-09-06 |
| SPP-53 | `docs/handoffs/FINDING-spp-53-2026-09-07.md` (+ `PRECOMMIT-spp-53-2026-09-07.md`) | **LANDED** 2026-09-07 — N↔S `ttc_mw` 48,700 (placeholder) → **3,400 MW** (FCITC construction, fixed ex ante; rule-14 misalignment on the link); sidecar `rtbm_bc_corridor_limits_2026.parquet` landed; vintage 2026; six keepers' keys unmoved |
| SPP-21 | `docs/handoffs/FINDING-spp-21-2026-09-06.md` | 2026-09-06 |
| SPP-30 | `docs/handoffs/FINDING-spp-30-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5378) — outage windows in every CEMS state with an SPP unit (OK 1060, NE 358); 9 itemised full-year fallbacks; `derive_cc_committed_pct` dropped from the SPP sequence |
| SPP-31 | `docs/handoffs/FINDING-spp-31-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5389) — SPP benchmarks 2023–25; P9 closed in the builder (wind 106.6345 → 103.0488 TWh); §5a C4-path gap → SPP-41 |
| SPP-32 | `docs/handoffs/FINDING-spp-32-2026-09-07.md` | **LANDED** 2026-09-07 (PRs #5396, #5399) — zonal shares (Σ = 1 exactly), wind shape (South nocturnal), gas basis 2022–24, curtailment 9.65 % both legs; six keepers unmoved |
| SPP-33 | `docs/handoffs/FINDING-spp-33-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5377) — `hr_by_year` for SPP-51; R1/R2/R3 routed (R1+R2 → SPP-51 Fable; R3 → desk) |
| SPP-34 | `docs/handoffs/FINDING-spp-34-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5388) — site wiring; S-1/S-2 → SPP-35 |
| SPP-40 | `docs/handoffs/FINDING-spp-40-2026-09-07.md` (+ `PRECOMMIT-spp-40-2026-09-07.md`) | 2026-09-07 — screen 2024 graded (direction tie fired the pre-registered STOP); full span solved and registered as the FIRST SPP KEEPER under owner direction; C1/C4-2023 wind UNSCORED pending SPP-41; rule-25 coal-band correction landed
| SPP-41 | `docs/handoffs/FINDING-spp-41-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5497) — ONE screen at the `eia930.actuals` seam; exactly the two SPP-31 series move on the bench path and one on the input path; seven cache keys unmoved; landed AFTER keeper-2 was solved → SPP-43 |
| SPP-36 | `docs/handoffs/FINDING-spp-36-2026-09-07.md` (artifact delivered by SPP-42, `FINDING-spp-42-2026-09-07.md` §1) | **LANDED** 2026-09-07 — `coal_supply_SPP.csv`, 27 prb / 2 lignite, 0 generic. SPP-42 landed the artifact; SPP-36 re-derived it byte-identically and carries the gate evidence: bare `COAL` 19,196.7 MW → 0, 88.9 % of SPP coal into the PRB passthrough physics, six keepers' solve surface **0 moved**, zero cross-ISO plant-code overlap. R-9 (econ-ramp tranche guard, `src/`) and R-10 (plant 6193 fleet population) routed |
| SPP-37 | `docs/handoffs/FINDING-spp-37-2026-09-07.md` | **LANDED** 2026-09-07 (PR #5474) — R-1/R-2/R-4/R-5/R-6 closed; N-1/N-2 → SPP-43; R-3 still routed |
| SPP-42 | `docs/handoffs/FINDING-spp-42-2026-09-07.md` | **LANDED** 2026-09-07 — SECOND SPP KEEPER `2026-09-07-spp-2-crosswalk-hydro` (NOT-YET; crosswalk + hydro repair; SPP-41 not landed at the time; stuck-demand runs routed) |
| SPP-57 | `docs/handoffs/FINDING-spp-57-2026-09-07.md` (+ `PRECOMMIT-spp-57-2026-09-07.md`, `docs/handoffs/spp57/`) | **LANDED 2026-09-07 — SCREEN KILLED (rule 29(a), 2025):** the three-zone Oklahoma-pocket arm with FCITC-rated chain links (N↔OK 6,500 / OK↔S 6,700 MW) is INERT — neither link live, S−OK sign mismatch, 0.0 % re-curtailment. Full span not spent; nothing registered; topology NOT landed (solve path restored to keeper-2's two zones). Design (CSWS split 0.5216 / 0.5383 from EIA-861, the three-point spread identification, both T* tables, the census) and two new sidecars landed for the re-issue; corridor-only N↔OK 3,400 is live in the screen's own flows (2,065 h) |
| SPP-43 | `docs/handoffs/FINDING-spp-43-2026-09-07.md` | **LANDED** 2026-09-07 — `2026-09-07-spp-3-screened-input` REGISTERED, **NOT promoted**: the pre-declared promotion rule's leg (i) (2024/2025 P1 objectives identical to keeper-2's) is NOT met, so the lane registered and STOPped per its own rule; legs (ii)/(iii)/(iv) all MET. keeper-2 stands, nothing pruned, `keepers/SPP.json` / `status/SPP.js` / the SPP shard UNCHANGED. Determination NOT-YET on the same four criteria. **C1/C4-2023 wind SCORED for the first time** (+10.68 %, the value 2024/2025 already read — the seam restores the year-invariant 1.106808 curtailment gross-up identity that the h3907 artifact was breaking in 2023 alone); `bench/SPP/2023` wind 106.634 → 103.049, `classFull` 288.201 → 284.616 (**wind class alone** — discharges SPP-41 §8 R-10). Zero-LP reports delivered for R-15 (a one-rule, zero-parameter repair reaching 5 cells in 4 ISOs) and plant 6193 (Harrington IS in the fleet, as `gas_st`; EIA-860 vintage_2023 has all three units `SUB`). **Card R-16 was SERVED IN-SESSION and the owner ruled PROMOTE** — `2026-09-07-spp-3-screened-input` is the **THIRD SPP KEEPER**; keeper-1 and keeper-2 PRUNED (rule 15 keeper-only retention, no `--force-uncite`, no dangling citation), `keepers/SPP.json` re-keyed, `status/SPP.js` rebuilt, SPP shard keeper+gates stamps updated with **no cell verdict moved** (no mechanism tested); all gates re-run green. Remaining rubric failures are inherited and untouched: the 2024 CT/CC/ST gas split (C1, C3a-2023) and the price-shape family (C3b / C3c / spread / negative hours). |
| SPP-38 | `docs/handoffs/FINDING-spp-38-2026-09-07.md` | **LANDED 2026-09-07** (4 of 15 were SPP's; 2 red open as R-1, miso-233's parity-registry debt) |
| SPP-44 | `docs/handoffs/FINDING-spp-44-2026-09-07.md` (+ `PRECOMMIT-spp-44-2026-09-07.md`, `docs/handoffs/spp44/`) | **LANDED 2026-09-07 — SCREEN KILLED (rule 29(a), 2023):** `spp_gas_commitment_bridge` built, measured (plant basis 0.209 / 0.090, min-run 15 / 5 h, LOYO-stable), fired (0.41 TWh) and killed on window agreement (0.694 vs 0.76) + D-4 unit-conduct (five laid-up plants); field landed default-off, cells U → R; no candidate for P15; R-17…R-20 routed |
| SPP-57b | `docs/handoffs/FINDING-spp-57b-2026-09-07.md` (+ PRECOMMIT, `spp57b/`) | **LANDED** 2026-09-07 (PRs #5513/#5527) — 2025 screen KILLED: N↔OK 3,400 live 23.5 % / 93 % N→OK; OK↔S 10,700 never (directionally misaligned, R-17 → SPP-54); topology not landed |
| SPP PRICE FAMILY (owner-launched, off-desk) | `docs/handoffs/FINDING-spp-price-family-2026-09-07.md` (+ PRECOMMIT) | **LANDED** 2026-09-07 (PRs #5533/#5534) — the uniform `offer_curve_by_group` quadruple KILLED on its structural leg (level moved −9 %, stack did not steepen) while improving C3a/C3b; `R` for SPP as a uniform quadruple; C3c → SPP-55; C1-2024 → SPP-44 |
| capx Q59 board row (capx director's lane) | `frontend/data/forecast/program-status.json` SPP row (PR #5528) | **LANDED** 2026-09-07 — §2.1b row from backcast artifacts only; T1-H half routed to this desk → SPP-60; row now cites keeper-2 (gate-(a) RED) → SPP-45 |
| SPP-45 | `docs/handoffs/FINDING-spp-45-<date>.md` | issued r#9 |
| SPP-58 | `PRECOMMIT-spp-58-2026-09-07.md` / `FINDING-spp-58-2026-09-07.md` | **LANDED 2026-09-07** — ψ₂ outside the band on every object; `ttc_mw` untouched; card R-21/R-22 |
| SPP-54 | `docs/handoffs/FINDING-spp-54-2026-09-07.md` (+ `PRECOMMIT-spp-54-2026-09-07.md`, `docs/handoffs/spp54/`) | **LANDED 2026-09-07 — DESIGN COMPLETE, NO SOLVE:** the SPS pocket implemented on design commit `8d427adc` (topology not on main); the R-18 wind reconciliation STOPPED pre-solve at h8509 (the builder's six-site level rule, R-21 → desk); the link rating waits for SPP-58 ψ₂ (R2 = 10,476 MW) |
| SPP-51 | `PRECOMMIT-/FINDING-spp-51-<date>.md` | issued r#9 |
| SPP-60 | `docs/handoffs/PRECOMMIT-spp-60-2026-09-07.md`, `docs/handoffs/FINDING-spp-60-2026-09-07.md` | **LANDED** 2026-09-07 — gap table + T1-H `spp-2021-2025-realized-t1h-spp60` registered (`spp-t1h`: HOLD, FC-3 FAIL); board legs (b)/(c) filled; six routed items (FINDING §4) |
| SPP-55 | `docs/handoffs/FINDING-spp-55-2026-09-07.md` (+ `PRECOMMIT-spp-55-2026-09-07.md`, `docs/handoffs/spp55/`) | **LANDED 2026-09-07 — KILLED AT ZERO LP (rule 29 step 0):** the SPP Contingency Reserve family built on SPP's published $275/$550/$1,100 curve and RSG requirement rule (six published constants, one measured share), registered under `energy_reserve_coopt` (no new field); keeper-3's headroom is below the requirement in 0/1/0 hours and in no measured shortage hour → INERT, cell U → I; the C3c tail is a 5-minute RT object (1/0/0 overlap); no candidate for P15; R-21…R-25 routed |
| SPP-35 | `docs/handoffs/FINDING-spp-35-2026-09-07.md` | **LANDED** 2026-09-07 — S-1/S-2 + O-4/O-6 closed; six items routed (FINDING §5) |

## 10. Ledger

Live state, scoreboard, rulings, collision register and issuance record:
`docs/handoffs/spp-desk-ledger-2026-09.md`. Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`.
