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
| 6 | Forecast-program entry (T1-F hindcast, `program-status.json` row, `GOLDEN_ISOS`) — **W6, gated, ROUTED to the capx director**; not part of this desk's done | `frontend/data/forecast/` → **SPP-14 alt-source sweep (P12, r#4)** |
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
| **P13** the N↔S TTC for the first keeper | SPP-20 registered a **48,700 MW placeholder** (North summer capability — cannot bind); no public rating exists (SPP-13); the RTBM archive carries `Real Time Effective Limit` only from **2026-01-28** (SPP-14 §5.4) | pull SPP-53 into W3 as SPP-40's precondition: a Fable derive lane reconciling the 2026→ corridor-flowgate limits (SPP's own rated limits, the ERCOT GTC analogue) into one link TTC, misalignment documented, cross-checked on the 2023–25 corridor binding frequency | FINDING-spp-20 §5 R-6, FINDING-spp-14 §5.4 | **RULED r#5: "Pull SPP-53 into W3 as SPP-40's precondition"** |
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
    SPP-53 N↔S TTC — MOVED INTO W3 at r#5 (P13); see §4 above
    SPP-54 SPS-pocket third zone   ┐ P1 pre-declared levers, RANKED by SPP-12's per-flowgate
    SPP-57 Oklahoma-pocket zone    ┘ binding share + shadow price vs the N↔S corridor  [FABLE]
    SPP-55 VRL-based scarcity design                        [FABLE]
    SPP-56 reserve co-optimisation (M2, LAST)               [FABLE]
                                           ▼
W6  Forecast-program entry — GATED, ROUTED to the capx director (P8)
    SPP-60 T1-F hindcast + program-status.json row + GOLDEN_ISOS + goldens  [FABLE]

CRITICAL PATH (r#5):  SPP-20 ✔  →  {SPP-30 ✔, SPP-31, SPP-32, SPP-53}  →  SPP-40
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
| **SPP-30** outages + tranches — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-30-2026-09-07.md`; G4 PASS: windows > 0 in every CEMS state holding an SPP fleet unit — OK **1060**, NE **358**, TX 345, MO 339, KS 325, LA 121, AR 51, NM 36, IA 34, ND 34, SD 9. MN/MT zeros are structural and evidenced (MN: no SPP fleet plant files CEMS there; MT: the one plant, Culbertson, is `CT_PEAKER` — peakers carry no overlay); CO has no CEMS file, as §2.1 already records. Coverage **85.3 % of qualifying plants / 97.9 % of qualifying MW**. Five extracts: standard 2721 · short 620 · layup 1089 · e923 18 · partial 85; plus `thermal_tranches_SPP.csv` 118 plant-groups (105 ok, 13 eia923_cf). **Full-year fallbacks: 9**, all `eia923_netzero` and all itemised by unit with the reason — inside the cross-ISO band (MISO 135, PJM 95, CAISO 78, NEISO 56, NYISO 30); the 10th full-year window (Jeffrey Energy Center unit 3 / 2023, 3 MWh gross and 2.8 opTime hours all year, back to 3.04 TWh in 2024) is a **measured** CEMS outage, not a fallback. Class band vs MISO reported not tuned: CT_PEAKER 14.8/16.1, ST_GAS 18.4/20.2, COAL committed 36.0/40.5, COAL mustrun-online 23.0/27.6, CC_REGULAR 32.9/42.4. Rule 25 verified at the offer curve: every ISO-scoped class SPP carries is **1.0 on every band** with no `phys_*` rows, so SPP-40's `authorized_price_tuning`-declares-**none** gate is already satisfiable. **ROUTED to SPP-DESK:** `derive_cc_committed_pct.py` has no `argparse`, hardcodes `["TX"]`+2023 and the ERCOT bin sheet, and writes one un-suffixed global CSV — `--iso SPP` is silently ignored and running it would overwrite **ERCOT's** file while producing nothing for SPP. It is superseded for every non-ERCOT ISO by `derive_thermal_tranches.py` (its own docstring says so), which delivered SPP's committed-%. Drop it from the §5/§8 SPP sequence. `tag_mixed_plants.py` is a no-op for SPP — proven on a scratch copy, both committed reference sheets sha-verified unchanged; `build_offer_curve_overrides.py` writes no file) | OPUS · frozen derives (rule 23) | spp | `data/raw/campd-unit-outages-SPP.csv` (+ `-short`, `-layup`, `-e923` siblings as emitted), `campd-partial-outages-SPP.csv`, SPP rows of the committed-pct / thermal-tranche / bin-assignment CSVs | windows > 0 in every CEMS state incl. OK/NE; zero full-year fallbacks | `FINDING-spp-30-<date>.md` (windows per state-year, units covered %) | `derive_campd_unit_outages.py --iso SPP --years 2023 2024 2025` → `derive_cc_committed_pct.py --iso SPP` → `derive_thermal_tranches.py --iso SPP` → `tag_mixed_plants.py` → `build_offer_curve_overrides.py`; every output header cites source + method |
| **SPP-31** benchmarks | OPUS · execution | spp | `scripts/data/derive_actual_lmp.py` SPP path (system + per-hub zones), `build_calibration_reference.py` (`"SPP":"SWPP"` BA map, eGRID BACODE), `_validation-source/actual_lmp.json` SPP block, `SPP_{2023,2024,2025}_renewable_capacity.csv`, `calibration_reference.json` SPP block, regenerated `frontend/data/backcast/tail/actual_tail.json` + `amplitude/actual_amplitude.json` | SWPP rows present in the shared `eia_demand_profiles.parquet` / `eia_generation_profiles.parquet` (else re-run `convert_eia930.py` and prove non-SWPP rows byte-identical) | `FINDING-spp-31-<date>.md` | other ISOs' blocks **byte-identical** in every shared JSON (json-diff = ∅); SPP `rt`/`rt_mon`/`rt_pct` present 2023–2025; `actual_tail.json` SPP counts at the P6 threshold |
| **SPP-32** zonal shares + wind shape + gas hub | OPUS · data-intake contract execution | spp | `curate_zonal_shares.py` SPP branch + `_SPP_SUBBA_ZONE_GROUPS`; the clean `zonal-shares` rows for SPP; new `scripts/data/build_spp_wind_shape.py` (clone of `build_miso_wind_shape.py`, NASA POWER `WS50M` at EIA-860 wind sites) → `data/raw/spp-wind-shape/spp_<yr>_wind_zone_shape.parquet`; `data/raw/spp_zonal_gas_hub.csv` (MISO csv pattern; EIA delivered-to-EP state series as the Panhandle / NGPL-MidCon proxy) + `data/fuel/hubs.py` wiring; `renewables.py` SPP membership in the wind-zone-shape ISO set (a membership, not a field); SPP reference curtailment rate only if SPP-12 landed a published annual rate | shares sum to 1.0 every hour; the redistribution identity holds to 1e-9 | `FINDING-spp-32-<date>.md` with a G-DRIFT hunk audit classifying every `renewables.py` / `hubs.py` hunk INERT for the six ISOs | `data-intake` skill contract (`write_clean`/`read_clean`, tmp-`CLEAN_DIR` tests); no `ScenarioConfig` field |
| **SPP-33** seam derive — **LANDED 2026-09-07** (`docs/handoffs/FINDING-spp-33-2026-09-07.md`; `data/raw/reference/spp_seam_*.csv` + `spp_seam_SOURCES.md`). `hr_by_year` RT for SPP-51 to arm: MISO 9.82/10.55/9.90 · AECI 10.30/12.08/8.32 · ERCOT 23.70/15.87/10.76. **Three items ROUTED to SPP-DESK** (FINDING §6): R1 `_NEIGHBOR_LMP_ISO` reaches none of SPP's three registered anchors (SPP-20 R-7 — producer NOT edited); R2 the registered `marginal_heat_rate`s divide by bare Henry Hub where the seam prices on `HH + gas_basis` (inert for the keeper, live forward — SPP-51's `spec.py`); R3 `_HR_GAS_ELASTIC`'s global name key BLOCKS SPP↔MISO's forward elasticity (PJM already owns `"MISO"`). ERCOT's registered 820 MW limit is under its own measured ±835 MW clip in 547/128/21 h. EIA-930 sign convention confirmed on SPP's own meter (corr +0.9936…+1.0000) | OPUS · derive only | spp | `derive_neighbor_hr_by_year.py --iso SPP` outputs (MISO from `actual_lmp_hourly_zonal_MISO.parquet` West/South rows; ERCOT from its hourly parquet); SWPP interchange duration curves by DIBA; `data/raw/reference/spp_seam_*.csv` | — | `FINDING-spp-33-<date>.md` — the `hr_by_year` and measured-flow numbers **for SPP-51 to arm** | does NOT edit `spec.py`; numbers reproduce from committed inputs |
| **SPP-34** site + docs | OPUS · execution | code | `docs/codebase-site/js/iso-configs-table.js:16-30,230`, `js/viz-iso-topology.js:16,118`, `css/site.css:402-407`, `data/iso-topologies.json` (regenerate from `get_iso_config`), `forecast-runs.html:90` (add SPP; verify the page tolerates an ISO with no forecast runs), `data-completeness.html:360`, `scripts/render_data_dictionary.py:49`, `docs/codebase/08-config-reference.md`, `docs/README.md`, `index.html` "six ISOs", `docs/calibration-log/spp.md` (header, MISO's format), CHANGELOG | — | `FINDING-spp-34-<date>.md` | `accessibility-audit` skill on touched pages; `sync-docs`; **`ff_readiness_battery.GOLDEN_ISOS` NOT touched** (W6) |
| **SPP-40** first solve → first keeper (PRECONDITIONS r#5: SPP-30, SPP-31, SPP-32 **and SPP-53** landed) | FABLE · novel-object kill-grading, determination, attestation | spp | `results/calibration/spp40_baseline_B/` (+ `hourly/` sidecars), `frontend/data/backcast/{registry,runs}/<id>.*`, `keepers/SPP.json` (new), `keepers/index.json` (+SPP), `status/SPP.js` (`build_status.py --iso SPP`), `bench/SPP/<yr>.json.gz`, `mechanism-matrix/SPP.js` keeper + gates stamp (LAST commit), `docs/calibration-log/spp.md` entry, `PRECOMMIT-spp-40-<date>.md` | `run_calibration.py --iso SPP` smoke on the screen year (fuel-mix only); fleet / offer-array census; PRECOMMIT pushed before any solve | `FINDING-spp-40-<date>.md` | `audit_keepers --check`, `check_registry_payload_parity`, `check_mechanism_matrix`, `check_bench_freshness` all 0; screen bundle DELETED before merge (29c); dashboard renders SPP with its determination; DOF ledger lists zero residual-identified parameters; `authorized_price_tuning` declares **none** (every `offer_curve_by_group` band 1.0 — rule 25) |
| **SPP-53** N↔S TTC derive (W3 since r#5, P13) | FABLE · a TTC is a design object: the reconciliation of parallel flowgate limits into one link rating is adjudication | spp | `data/raw/spp-binding-constraints/rtbm_bc_corridor_limits_2026.parquet` (NEW reduced sidecar: the `n_s_corridor` rows of the 2026-01-28→ 14-column daily files) + README/SOURCES; `src/market_sim/config/iso_configs.py` `_spp_config` TTC value + comment (rule 27); `config/transmission_expansion.py` `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` if the vintage moves; `docs/parameter-citations.md` row | the construction rule is written in the PRECOMMIT BEFORE any limit is read | `PRECOMMIT-spp-53-<date>.md`, `FINDING-spp-53-<date>.md` | no solve; the six keepers' keys unmoved (`solve_surface_register.py --diff`); SPP-40 reads the value |
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
| G18 | portal.spp.org anonymous access withdrawn (measured 2026-09-06: listings `[]`, downloads 404 — an `X-SPP-UI-Token` requirement, FINDING-spp-12 §2) | W1→W2 | SPP-13 probes the FTP public-data route SPP's reference guide names; the working request grammar is recorded in the builder's docstring; fallback = manual rows with the exact calls (FINDING-spp-12 §8) |

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

### W5 — reserved charters (NOT dispatchable until SPP-40 lands; the desk writes each in full when it is)

| Lane | Model | Charter stub (expanded by the desk at issuance) |
|---|---|---|
| SPP-51 `[OPUS]` | pre-declared execution of SPP-33's numbers | arm `hr_by_year` on `INTERFACE_NEIGHBORS["SPP"]` MISO/ERCOT; A/B served vs `--priced-interchange` on the P7 screen year; keeper = control (29b); STOP gate = interchange duration curve sign/magnitude vs EIA-930; matrix cell for the seam mechanism |
| SPP-52 `[OPUS]` | execution | curtailment as a first-class metric (playbook §8.3): reference curtailment rate → the uncurtailed fallback set; report modeled vs reported curtailment; wind-shape arming if SPP-32 left it as an input only |
| SPP-53 `[FABLE]` | TTC is a design object | N↔S TTC from the binding-constraint frequency method (doc 04) via `derive_ttc_limits.py`; rule 14: the measured value stays even if the fit worsens; documents the ITP-vs-link misalignment |
| SPP-54 `[FABLE]` | topology change | the SPS / Texas-Panhandle pocket as a third zone (own sub-BA `SPS`, 12.6 % of load; Lubbock FCA). RANKED against SPP-57 by SPP-12's per-flowgate binding share + shadow price vs the N↔S corridor (P1 as ruled); the higher-ranked pocket is issued first; scored leave-one-year-out (rule 22) |
| SPP-57 `[FABLE]` | topology change | an Oklahoma pocket (OKC/Tulsa split of SPP-South — Osage–Webber $75/MWh and Russett–S.Brown $61/MWh are the market's two highest-value constraints, audit §6.1). Needs a `CSWS` sub-allocation for its load share and a TTC; same ranking test and LOYO scoring as SPP-54 |
| SPP-55 `[FABLE]` | mechanism design | VRL-based scarcity: an in-LP reserve demand curve (closer to MISO's RBDC than to the post-solve ORDC overlay), designed against the SPP tail counts; screen structural only |
| SPP-56 `[FABLE]` | mechanism design, LAST | reserve co-optimisation Reg/Spin/Supp on the `da-mcp`/`rtbm-mcp` measured prices; must first prove non-inertness (MISO precedent) |

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
| SPP-53 | `docs/handoffs/FINDING-spp-53-<date>.md` (+ PRECOMMIT) | — |
| SPP-21 | `docs/handoffs/FINDING-spp-21-2026-09-06.md` | 2026-09-06 |

## 10. Ledger

Live state, scoreboard, rulings, collision register and issuance record:
`docs/handoffs/spp-desk-ledger-2026-09.md`. Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`.
