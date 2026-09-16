# SOCO Addition Program — plan, wave graph, prompt pack (2026-09)

Status: **CHARTERED 2026-09-12.** Owner request, verbatim: *"Use the add spp workstream as a
reference and develop a plan and prompt pack to do whatever iso Hillabee gas plant in Alabama is
in."*

**The answer to the owner's question, measured, not asserted:** Hillabee Energy Center is
**EIA plant 55411**, Tallapoosa County **AL**, 822.8 MW nameplate across three
`Natural Gas Fired Combined Cycle` generators (258.4 + 258.4 + 306.0), operating 2010, and its
balancing authority in `data/raw/eia-860/eia860_plant.parquet` is **`SOCO` — "Southern Company
Services, Inc. - Trans", NERC region SERC**. Hillabee is therefore **not in any RTO/ISO**: it sits
in the Southern Company balancing authority, a vertically-integrated, bilaterally-traded footprint
with no day-ahead market, no LMP, no centralized capacity market and no independent system
operator. The north-Alabama fleet (8,396.4 MW across 16 plants) is **TVA**, a different balancing
authority, and is **out of scope** for this program.

This program adds **`SOCO` as the eighth registered region** in `config/iso_configs._ISO_BUILDERS`.
Everything downstream of that registry calls the key an "ISO"; SOCO is a **balancing authority**,
and the plan says so everywhere rather than pretending otherwise — the distinction is not cosmetic,
it is what makes card **S2** (below) the load-bearing decision of the whole program.

Director: the **SOCO ADDITION DESK** (lane id `SOCO-DESK`) — handoff prompt
`docs/handoffs/soco-desk-handoff-2026-09-12.md`, ledger `docs/handoffs/soco-desk-ledger-2026-09.md`.
**The ledger wins where this plan and the ledger diverge on live state.** This plan owns the
charters (§8) and the decisions (§3); the ledger owns who is running what.

Process authority: `docs/multi-iso/05-backcast-playbook.md` (Phase 0→6, §8 conventions), the
Stage A–H checklist of `docs/multi-iso/00-iso-addition-protocol.md` §1–2, and — as the worked
precedent for every mechanical step of an addition — `docs/multi-iso/spp-addition-plan-2026-09.md`
(the SPP program, chartered 2026-09-06, first keeper 2026-09-07). Where this plan and the playbook
disagree on *SOCO specifics*, this plan wins; on *process*, the playbook wins. Where this plan is
silent on a mechanical step of registration, **the SPP plan's §2.3 / §7 is the default**.

---

## 1. Definition of done

| # | Done means | Surface |
|---|---|---|
| 1 | `"SOCO"` in `config/iso_configs._ISO_BUILDERS`; `get_iso_config("SOCO").validate_topology()` passes; every ISO-keyed registry has a SOCO entry or a documented exclusion | `src/market_sim/` |
| 2 | A **2023–2025** backcast keeper (rule 16 `[R-ALLYEARS]`) scored under card **S2**'s ruling — on the no-price branch it may **never** read `CALIBRATED`, is scored on C1/C2/C4/C6/C8, and names the price gap on its determination basis at full magnitude — and registered on the backcast dashboard **with whatever determination it earns** | `frontend/data/backcast/keepers/SOCO.json`, `backcast-runs.html#iso=SOCO`, `calibration-status.html#iso=SOCO` |
| 3 | `docs/codebase-site/data/mechanism-matrix/SOCO.js` shard live with a cell for every mechanism id; `docs/mechanism-testing-matrix.md` §5.8 SOCO lever queue | matrix (rule 28 `[R-MECH-MATRIX]`) |
| 4 | `docs/calibration-log/soco.md` open; docs/site prose says eight regions; `docs/multi-iso/00` §0/§3 extended | docs |
| 5 | **The seven existing keepers' cache keys never move** at any wave (no new `ScenarioConfig` field, no default flip, no `results/cache.py` edit) | `tests/regression/test_persisted_identity.py`, keeper `run_config.json` |
| 6 | Forecast-program entry (T1-F hindcast, `program-status.json` row, `GOLDEN_ISOS`) — **ROUTED to the capx director, never this desk** (card S10) | `frontend/data/forecast/` |
| 7 | **Every promotion after the first leaves the invariant true**: every registered SOCO run is the designated keeper or stamped to it, and SOCO's registered year set never shrinks — `audit_keepers.py` **E13** green (rule 35 `[R-PROMOTE]`, gate G21) | `frontend/data/backcast/registry/`, `keepers/SOCO.json` |

What this plan does **not** charter: any change to another ISO's seam pricing; any change to the
rubric (card S2 *asks*; only the owner rules); any forecast-namespace write (card S10).

---

## 2. Verified state at charter (2026-09-12, `origin/main` `ab1267e9`)

Everything in §2.1–§2.6 was **measured in the chartering session** off the committed tree or probed
live from it. No number here is recalled or inferred; anything not measured says "pending".

### 2.1 What already exists for SOCO

| Asset | Path | Measured at charter |
|---|---|---|
| EIA-930 SOCO hourly | `data/raw/eia-930-hourly/SOCO hourly.parquet` | **26,304 rows, 2023-01-01 → 2025-12-31 UTC**, 20 columns: `Demand`, `Demand forecast`, `Net generation`, `Total interchange`, `NG: COL/NG/NUC/WAT/SUN/WND/OIL/BAT/PS/SNB/OES/OTH`. Local-date hour counts 8760 / 8784 / **8753** (2025 is **7 hours short** — a curation item, not a blocker) |
| Its annual energy | same | Demand **229.47 / 239.33 / 239.36 TWh** (2023/24/25); net generation 239.63 / 250.16 / 251.68 → SOCO is a **net exporter of 10.2 / 10.8 / 13.0 TWh/yr**. Fuel TWh: gas 129.6 / 126.1 / 125.4 · nuclear **52.4 / 63.0 / 64.2** · coal 38.3 / 40.5 / 44.0 · hydro 8.45 / 6.92 / 5.93 · solar 8.36 / 10.14 / 9.98 |
| EIA-930 SOCO extracts | `data/raw/SOCO_fueltype.parquet`, `SOCO_region.parquet` | present at the `data/raw/` root, classified `shared` by the profile resolver today (§2.3 row "Data profiles") |
| EIA-860 fleet | `data/raw/eia-860/eia860_plant.parquet` + `eia860_generator_operable.parquet` | BA `SOCO`: **335 plants / 786 generators / 70,665.7 MW nameplate.** By state: **GA 41,284.4 · AL 24,494.0 · MS 4,577.7 · FL 309.6 · MA 1.5** (the 1.5 MW "MA" row is a source defect — SOCO-10 adjudicates it). By technology: CC 20,702.8 · coal 12,234.7 · CT 11,676.8 · **nuclear 8,282.4** · solar 5,825.9 · gas ST 3,839.2 · hydro 3,317.6 · wood 1,719.2 · petroleum liquids 1,340.5 · **pumped storage 1,306.6** · batteries 148.7 · **CAES 110.0** · pet coke 90.0 · LFG 61.8 · gas ICE 7.0 |
| CAMPD CEMS unit-level | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **MS present 2019–2026. AL and GA are ABSENT** — the two states carrying 65.8 GW of the 70.7 GW fleet. This is manifest row 1 and the critical path. |
| Timezone | — | SOCO is **America/Chicago** (Alabama/Mississippi) and **America/New_York** (Georgia) — a **two-timezone footprint**, a first for this model. `fetch_eia930_hourly.BA_TIMEZONE` has **no `SOCO` entry**; the committed parquet's `Local time` column was written by some other route and its convention must be established by SOCO-10 before anything reads it |
| Dashboard colour | `docs/codebase-site/css/shared.css`, `js/backcast-runs.js` | **no `--iso-soco`** — SOCO-21 mints it |

### 2.2 What is missing (Stages C–H)

`actual_lmp.json` SOCO block **and the series behind it — see §2.6, this is card S2** ·
`SOCO_<yr>_renewable_capacity.csv` + `calibration_reference.json` SOCO block ·
`campd-unit-outages-SOCO.csv` (needs AL/GA CEMS) · zonal hourly load (§2.5) · inter-zone TTCs ·
per-zone solar shape · zonal gas hub · PRM / VOLL / IRP citations ·
`scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/soco.py`.

### 2.3 The seven-ISO pin — every place that flips at registration (W2 atomicity list)

Measured at `ab1267e9` by counting `"SPP"` occurrences per file, i.e. by reading the *previous*
addition's own footprint. **22 modules under `src/market_sim/` and 9 under `scripts/`.**

| Pin | Path | Action |
|---|---|---|
| Builders + demand loaders | `config/iso_configs.py:1936` `_ISO_BUILDERS` (→ `SUPPORTED_ISOS:1954`); `data/eia930/demand.py:851` `DEMAND_LOADERS` + its import-time assert | **same commit** — the assert rejects loader keys ∉ `SUPPORTED_ISOS` |
| Solve-surface fingerprint | `config/solve_surface.py:75` `SURFACE_ISOS` (hardcoded 7-tuple, pinned == `SUPPORTED_ISOS` by `tests/unit/config/test_solve_surface.py`); `config/solve_surface_declared.py` | add `"SOCO"` in the SAME commit; `scripts/solve_surface_register.py --diff origin/main HEAD` must show **zero moved rows for the seven** |
| Interchange | `model/interchange/spec.py` (12 SPP sites), `model/interchange/registry.py` | SOCO's own `INTERFACE_NEIGHBORS` + served-schedule membership (card S4) |
| Constants | `config/constants.py` (11 SPP sites) — PRM, queue caps, RPS floors, ELCC, tail/amplitude keys | one block, cited per value (rule 5 `[R-NO-MAGIC]`) |
| Capacity market | `config/capacity_market.py` (10 SPP sites) — `MARKET_DESIGN`, `_CURVE_ISOS`, `_CAPACITY_ISOS` | SOCO is **absent** from all three (no capacity market) → `DEFAULT_MARKET_DESIGN`; the absence is documented, not accidental |
| Zone assignment | `data/zone_assignment.py` (5 SPP sites) | `_SOCO_STATE_ZONES` (card S3) |
| **`_ISO_TO_BA_CODE`** — **ADDED r#3→r#4, and it was MISSING from this list** | `data/zone_assignment.py:69` (a 7-key dict pinned to `SUPPORTED_ISOS`), consumed at `:795`, `:1092` and cited from `config/capacity_market.py:482` and `config/constants.py:4384` | `"SOCO": "SOCO"` — the EIA-860 `Balancing Authority Code` and the registry key are the same string here, so it is 1:1 and trivial. **But the key must EXIST**: `:1092` is a bare `_ISO_TO_BA_CODE[iso]` index, so a registered SOCO without it raises `KeyError`, not a fallback. **Credit and cross-program transfer: found by NWPP-10** (PR #6104), which flagged `ISO_TO_BA_CODE` as "the W2 novel change" its own plan had missed; SOCO's §2.3 had missed it too. NWPP's harder case does not apply here — its 17→1 BA map collapses to one arbitrary BA and fails **silently** at 13 `==` call sites, while SOCO is one BA and one code. **SUPERSEDED IN PART at the r#5 check-in (2026-09-14, main `c6c70190`) — the surface MOVED and this row's last clause became a merge hazard.** NWPP-20 (PR #6153) landed a **many-to-one** `data/fleet/models.py::BA_CODE_TO_ISO` (BA → region, 17 NWPP codes) plus a DERIVED `ISO_TO_BA_CODES: dict[str, tuple[str, ...]]`, and **deleted the scalar inverse**, because *"a scalar inverse of a many-to-one map keeps whichever code was inserted last and silently returns 1/17 of a pool (NWPP-10 §3: thirteen `==` call sites failed silently that way before this table existed)"* — its own words, on main. So SOCO's registration now writes **`"SOCO": "SOCO"` into `BA_CODE_TO_ISO`** and lets the derived tuple table serve consumers (`.isin(ba_codes(iso))`); the scalar `data/zone_assignment.py:69` `_ISO_TO_BA_CODE` still exists on main and still needs SOCO's key, because **NWPP deliberately has no entry there** (it is a pool) while SOCO is one BA — the NWPP precedent does NOT discharge that pin, and a lane reading NWPP-20 as the template would skip it and hit the `:1092` `KeyError` this row was added for. See gate **G23** |
| Renewables / fuel / reserves | `data/renewables.py` (5), `config/fuel_trajectories.py` (3), `model/reserves/spec.py` (3) | per card S3/S5 |
| Pipeline + runner | `pipeline/backcast_config.py` (2), `pipeline/kwargs.py`, `pipeline/commitment.py`, `runner.py` | one line each |
| Data leaves | `data/campd.py` (`ISO_STATES["SOCO"]`), `data/eia930/{frames,envelopes,demand}.py`, `data/fleet/models.py`, `data/neighbor_price.py`, `data/transmission_expansion.py`, `config/paths.py` | one key each |
| Tail threshold ×3 | `scripts/calibration_verdict.py`, `scripts/data/derive_actual_tail.py`, `scripts/data/derive_actual_amplitude.py` | all three — **but only if card S2 yields a price series** |
| Multi-year set | `scripts/audit_keepers.py::_MULTI_YEAR_ISOS` | add SOCO (rule 16 `[R-ALLYEARS]` enforcement) |
| Memory classes | `scripts/run_isos_concurrent.py` | add SOCO (KeyError otherwise) |
| Solve workflow dropdown | `.github/workflows/calibration-solve.yml` | add SOCO |
| Matrix | `scripts/lib/mech_matrix.py:61` `ISO_ORDER` + `:65` `ISO_EV_KEY` (SOCO needs a free letter — `S` is taken by SPP; **`O` is free**), `docs/codebase-site/data/mechanism-matrix.js` base `isos`, a new `mechanism-matrix/SOCO.js`, `tests/unit/config/test_mechanism_matrix_shard_migration.py` | SOCO-21, ONE commit (gate G2) |
| Data profiles | `configs/data-profiles.yaml` | token `soco` — **check the trap**: `soco` must not be a substring of any non-SOCO `data/raw` child (measured clean at charter, but SOCO-20 re-measures and adds the unit test, as SPP's `spp` ⊂ `DAMLZHBSPP_*` trap required) |
| Coverage sweeps | `tests/unit/config/test_iso_coverage.py` (`ALL_ISOS = sorted(_ISO_BUILDERS)`) | auto-extends — SOCO must satisfy queue cap, retirement/entry, carbon-`None`, and the **no-import-node** branch |
| ~22 seven-tuple tests | `tests/unit/model/test_capacity.py`, `test_storage.py`, `test_ccs_retrofit.py`, `tests/unit/data/test_fleet.py`, … | extend, or document as deliberate exclusion |

### 2.4 Host reachability, probed 2026-09-12 from this session

| Host | Result | Consequence |
|---|---|---|
| `api.epa.gov` CAMPD bulk, `emissions/hourly/state/emissions-hourly-2023-al.csv` | **200, 187,409,202 bytes** — anonymous, no key | AL/GA CEMS are **session-fetchable**; ~187 MB per state-year × 8 files |
| `www.eia.gov` Grid Monitor six-month sub-BA file | **200, 25,950,536 bytes** | reachable — but see §2.5, SOCO has no sub-BAs in it |
| `api.eia.gov` v2 | needs a project key; **this container has none** (`EIA_API_KEY` unset, no `.env`) | the EIA-930 hourly fetch and delivered-gas rows need a session that carries the key, or the Grid Monitor key-free files |
| `oasis.caiso.com/oasisapi/SingleZip` | **200, real zip** (retried once past a transient 503) | not needed for SOCO; recorded because the NWPP program needs it |
| `southeastenergymarket.com` (SEEM) | **200** | SEEM's public site is reachable. **SEEM publishes no prices** — see §2.6 |
| `eqrreportviewer.ferc.gov` | **200, 1,074,117 bytes** | FERC **EQR** viewer is reachable — the only public transaction-price route into this footprint (card S2 option a) |
| `www.ferc.gov` (Form 714 bulk CSV + its landing page) | **403 on both** | FERC's own static host refuses this egress. **Not a dead end** — see the next row |
| `s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet` | **206 on a range request** | PUDL's ETL of **FERC Form 714 hourly planning-area demand** is reachable and rangeable. This is the zonal-load spine (§2.5) |

### 2.5 Zonal load: there are NO EIA-930 sub-BAs for SOCO — FERC Form 714 is the spine

Measured at charter by downloading `EIA930_SUBREGION_2023_Jan_Jun.csv` (26 MB) and listing every
`(Balancing Authority, Sub-Region)` pair it carries:

```
CISO 4 · ERCO 8 · ISNE 8 · MISO 6 · NYIS 11 · PJM 20 · PNM 9 · SWPP 17
```

**SOCO is not in that list.** Every prior addition (MISO's six zones, SPP's seventeen sub-BAs) got
its zonal load shares from EIA-930 sub-BA demand; **SOCO cannot**. The substitute is **FERC Form
714, Part 3 Schedule 2 — hourly planning-area demand**, which Alabama Power, Georgia Power and
Mississippi Power each file as separate respondents. That is a *measured hourly* series per
operating company, i.e. strictly better than the annual retail-sales share a lesser source would
give, and it is rule-13 `[R-MEASURED]` admissible (it regenerates for a forward year and responds
to changed conditions). Two routes, in preference order: (1) the PUDL parquet (§2.4, reachable);
(2) FERC's own bulk CSV (403 from this egress — a fetch lane retries from a session whose egress
differs, or the owner uploads). SOCO-11 owns this and **must reconcile the three respondents'
hourly sum against `SOCO hourly.parquet::Demand`** before anyone uses it: a share derived from a
series that does not add up to the BA's own metered demand is not a share.

### 2.6 THE PRICE PROBLEM — there is no LMP, and the rubric is built on one

This is the single fact that makes SOCO unlike every ISO in the repo, and it is why card **S2** is
served at sitting #1 rather than sitting #2.

Three of the rubric's four **load-bearing** criteria are price criteria — `scripts/calibration_verdict.py::CRITERIA`
carries `price_mean` (C3a), `price_shape` (C3b) at `TIER_LOAD` and `price_tail` (C3c) at
`TIER_SUPPORT`, against `TIER_LOAD` `fuelmix` (C1) and `sysvol` (C2). Every one of them scores the
model's LP duals against a committed `_validation-source/actual_lmp_hourly_<ISO>.parquet`.

**Southern Company publishes no locational marginal price, no day-ahead clearing price and no
hourly index.** It is vertically integrated: dispatch is cost-based against an IRP, and wholesale
energy moves bilaterally. **SEEM** — the Southeast Energy Exchange Market, live since November 2023
and covering this footprint — is a 15-minute *matching* platform that publishes participation and
matched-volume statistics and, deliberately, **no price**. So the usual benchmark does not exist
and cannot be made to exist by fetching harder.

What that means concretely, and what the desk must NOT do: a neighbouring market's hub price
(MISO-South, PJM AD, TVA's nonexistent one) is **not** SOCO's price, and substituting one would be
exactly the "load proxy" rule 13 `[R-MEASURED]` forbids — the dispatch validated would not be the
dispatch forecast. The desk refuses that route in advance so no lane proposes it.

The two live options, and the reason both go to the owner as one card:

- **(a) Build a measured bilateral price series from FERC EQR.** Electric Quarterly Reports are
  public, transaction-level, and every seller into the Southern footprint files them with product
  name, delivery point, begin/end datetime, quantity and **price**. A footprint-hourly volume-
  weighted index over short-term firm/non-firm energy transactions at Southern delivery points is a
  genuine *measured market price*, regenerates forward, and responds to conditions — rule-13
  admissible. It is also a heroic ETL with real risk: EQR's product taxonomy is messy, monthly and
  capacity products must be excluded, and thin hours may not clear at all. **This is the desk's
  recommendation, run as its own lane (SOCO-13) with a hard STOP gate: if the index cannot be
  reconciled against an independent public anchor, it is not used.**
- **(b) Score SOCO without price.** C3a/C3b/C3c become UNSCORED. Under rubric v3.6 unscored criteria
  **downgrade** (rule 22 `[R-C3C]`'s budget text: "every OTHER caveat route — … unscored criteria,
  data-blocked years — still downgrades"), so a SOCO run could never read `CALIBRATED` however good
  its physical fit. Making that honest requires an **owner rubric amendment** creating a
  determination class for a non-market region scored on C1/C2/C4/C6/C8 alone. Only the owner can
  make it; the desk will not invent one.

The recommendation is **(a) attempted, (b) requested in parallel**, so the program is never blocked
on the ETL and never quietly ships a price claim it cannot support.

**RULED 2026-09-13 (desk r#2): both.** The owner took the recommendation as served — SOCO-13 is
chartered with its STOP gate, **and** the fallback class is ruled in advance: a SOCO run with no
price benchmark reads a determination naming its own basis (e.g. `PHYSICALLY CALIBRATED — price
unscored, no public price exists`), scored on C1/C2/C4/C6/C8, **never `CALIBRATED`**, with the
price gap on the determination basis at full magnitude. Full ruling text and its five binding
consequences: §3 card S2. What the ruling does **not** do is write the scorer — that is card
**S11**, and until it lands `scripts/calibration_verdict.py` carries no branch that can express
this determination, so W4 cannot score. Gate **G17** is untouched: a neighbouring market's hub is
still refused.

---

## 3. The owner cards S1–S12

Recommendation first and labelled; rulings appended to each row **verbatim** and numbered in the
ledger §2. **S1 and S2 are served at sitting #1** (S2 gates the whole scoring design and its answer
changes what W1 even fetches). S3–S9 are served at **sitting #2**, after W1's evidence lands —
the SPP precedent ("let the Phase-0 audit decide the topology") applies.

| Card | Question | Recommendation to present | Evidence it needs | Ruling |
|---|---|---|---|---|
| **S1** the key | Register the region as `SOCO`, `SOUTHERN`, or `SERC-SE`? | **`SOCO`** — it is the EIA-930/EIA-860 balancing-authority code, it is already the filename convention on disk (`SOCO hourly.parquet`, `SOCO_fueltype.parquet`), and it is *honest*: the docs then say "balancing authority", never "ISO". `SERC-SE` is refused: SERC-SE is a NERC assessment area containing TVA, Duke and others that this program does not model | §2.1 | **RULED 2026-09-13 (desk r#2), owner, verbatim: "SOCO (Recommended) — The EIA-930/EIA-860 balancing-authority code. Already the on-disk filename convention (`SOCO hourly.parquet`, `SOCO_fueltype.parquet`), so no crosswalk is invented. Lets every doc say 'balancing authority' rather than 'ISO'."** The key is `SOCO`; `ISO_EV_KEY["SOCO"] = "O"` and the shard filename `SOCO.js` follow from it |
| **S2** THE RUBRIC / PRICE CARD | SOCO has no LMP and never will (§2.6). What is the price benchmark, and what may a SOCO run be *called*? | **BOTH: (a) charter SOCO-13 to build the FERC-EQR footprint hourly index with a STOP gate, AND (b) rule now on what a run reads if (a) fails** — the desk's proposal for (b) is a determination that names its own basis (e.g. `PHYSICALLY CALIBRATED — price unscored, no public price exists`), scored on C1/C2/C4/C6/C8, never `CALIBRATED`, with the price gap on the determination basis at full magnitude. Refuse a neighbouring-hub proxy outright | §2.6; SOCO-13's reconciliation | **RULED 2026-09-13 (desk r#2), owner, verbatim: "Both: build the EQR index AND rule the fallback class now (Recommended) — Issue SOCO-13 to build a footprint-hourly volume-weighted price index from FERC EQR transaction data, with a STOP gate registered before any data is read; AND rule now that if it fails, a SOCO run reads a determination that names its own basis (e.g. PHYSICALLY CALIBRATED — price unscored, no public price exists) scored on C1/C2/C4/C6/C8, never CALIBRATED, with the price gap on the determination basis at full magnitude."** Consequences, binding on every later lane: **(i)** SOCO-13 is UNBLOCKED and was issued at r#2; **(ii)** a SOCO run may **never** read `CALIBRATED` on the no-price branch, and the price gap is reported at full magnitude on the determination basis — never suppressed, never caveated away; **(iii)** the fallback class is scored on **C1/C2/C4/C6/C8 only**; **(iv)** gate G17 stands unchanged — a neighbouring hub is still refused, ruling or no ruling; **(v)** the exact label wording and the `scripts/calibration_verdict.py` amendment that implements the class are **card S11** — the ruling authorizes the class, it does not write the scorer |
| **S3** topology | 1 zone (copperplate) vs **3** (Alabama Power / Georgia Power / Mississippi Power) | **3 zones with Tier-3, documented, non-binding TTCs** — the exact SPP-20 precedent. The OpCo split is real structure (rule 1 `[R-STRUCT]`: a real structure enters regardless of fit), the load side is measurable per OpCo (§2.5) and the fleet splits cleanly on state FIPS; what does *not* exist is a published internal transfer limit, so the TTCs register Tier-3 and **cannot bind**, and their derivation becomes the first pre-declared structural lever (SOCO-54). Note plainly: with no zonal price (card S2) there is **no zonal price benchmark**, so the zones are validated on load and dispatch, not on spread | SOCO-10 fleet-by-state; SOCO-11 FERC-714 reconciliation | **RULED 2026-09-13 (desk r#3), owner: **3 zones now on the six-respondent sum"** — over the desk's own recommendation, which was 1 zone. **The evidence had inverted the charter's recommendation**: SOCO-10 predicted the three OpCos *structurally* cannot sum to the BA (Georgia Power's winter peak 16,284 MW vs the BA's 47,368 MW), and SOCO-11 measured it — **73.2 %**, short 61.4 / 66.2 / 64.2 TWh (26.8 / 27.7 / 26.8 %) in every hour of every year, shape right (r ≈ 0.99), level short. The six-respondent sum (+ Oglethorpe 107, MEAG 210, Southern Power 186) closes to **1.63 / 1.50 / −0.03 %**, and the **PowerSouth + Tallahassee falsifier OVERSHOOTS** (−2.28 / −2.41 / −4.15 %), so the enumeration discriminates on BA membership rather than minimising a residual. **Binding conditions, because the desk's stated risk does not vanish with the ruling: (i)** PUDL carries **no county attribution** for Oglethorpe, MEAG or Southern Power, so **gate G22** makes a cited BA-membership basis a hard precondition on SOCO-32 — lane **SOCO-14** exists to produce it; **(ii)** zones are named **geographically** (`SOCO_AL` / `SOCO_GA` / `SOCO_MS`), never for an operating company (SOCO-10: Georgia Power owns 241.6 MW in Alabama; Oglethorpe + MEAG own 7.1 GW in Georgia that is not Georgia Power's), and the six respondents therefore do **not** map 1:1 onto three zones — that mapping is SOCO-32's declared construction; **(iii)** the split is **never sold as improving accuracy** — with non-binding Tier-3 TTCs 3-zone and 1-zone SOCO produce the same dispatch until a TTC binds, and there is no zonal price, spread or congestion archive to validate against, ever. It is chosen for structure (rule 1 `[R-STRUCT]`). **RE-RULED 2026-09-14 (desk r#5), owner: "FIVE respondents — the fully-cited set (Recommended)".** **Gate G22 FAILED as designed and the card returned.** SOCO-14 cited **Oglethorpe (107) YES** (NERC/SERC public compliance audit **NCR01248** p. 3 — GSOC's Balancing Authority is Southern Company Services–Transmission, EIA BA code `SOCO`/18195; 37 of 38 member EMCs coded `BA=SOCO` in EIA-861 2024; **154/154** member counties inside the BA's 252-county footprint; EIA-861 winter peak 10,489 MW == the 714 series' 2024 maximum) and **MEAG (210) YES** in MEAG's own words (Annual Information Statement FY2024, pp. 25–26, placing its Territorial Load inside "the Southern Company Balancing Authority Area"; 48/49 Participants `BA=SOCO`; 51/51 counties; summer peak 2,399 MW == the 714 maximum). **Southern Power (186) is a documented NO** — nothing found establishes where its FERC-714 *planning-area load* sits; the IIC and EIA-860's 11-of-53 plants support **generation in the footprint**, which is not the load claim. **The registered set is therefore the FIVE fully-cited respondents** — AP + GP + MP + 107 + 210 — with residual **3.03 / 2.92 / 1.26 %**, in preference to the six-respondent 1.63 / 1.50 / **−0.03 %**. The owner's reasoning as served: a slightly larger residual with a cited basis beats a smaller one resting on an uncited component (rule 13 `[R-MEASURED]`), and the 2025 six-respondent residual going **negative** is the overshoot SOCO-11's own falsifier was built to detect. 186's 3.211 / 3.401 / 3.084 TWh (1.3–1.4 % of BA demand) is **excluded and named on the first keeper's determination basis**, never absorbed |
| **S4** seams | SOCO is a net exporter of 10.2–13.0 TWh/yr (§2.1). Served schedule or priced neighbours? | **Served measured EIA-930 `Total interchange`** for the first keeper (the PJM/NYISO/NEISO/SPP precedent, playbook §8.2, rule-13 admissible). Priced `NeighborInterface`s (TVA, MISO-South, Duke/CPLE, the Florida BAs, Santee Cooper) registered **default-off** and validated later. **Rule 25 `[R-ISO-SCOPE]`: this desk never touches how MISO or PJM price their side of any seam** | SOCO-11 DIBA duration curves | **RULED 2026-09-13 (desk r#3), owner: **served measured EIA-930 interchange for the first keeper**, the desk's recommendation. SOCO-11 measured the cleanest interchange book in the corpus — **zero NaN hours** on any of nine DIBAs in any year (SWPP: 97/361/936), per-seam legs agreeing with the BA book to **0.001 / 0.001 / 0.017 TWh**, net export **+10.155 / +10.832 / +13.038 TWh** confirming the charter, and 24,100 of 26,294 hours *exactly* equal. Priced `NeighborInterface`s (TVA, MISO-South, Duke/CPLE, the Florida BAs, Santee Cooper) register **default-off** for lever SOCO-56, with SOCO-12's published transfer capability (MISO-South 1,791 S / 2,374 W MW; TVA 480/478 MW; 11 more rows) as their input. Rule 25 `[R-ISO-SCOPE]` absolute: this desk never touches how MISO or PJM price their side |
| **S5** scarcity / VOLL | SOCO has no offer cap and no scarcity pricing — there is no market to cap | **No ORDC, no scarcity seed.** VOLL is the LP's slack penalty and must still be a cited number: propose an economic VOLL from a published Southeast value-of-service study or the DOE/LBNL ICE calculator, **not** the $2,000 FERC-831 ceiling every market ISO in this repo carries (831 caps *offers*; SOCO takes no offers). If no citable value survives Phase 0, fall back to $2,000 **with the misalignment stated on the field** | SOCO-10 registry-values table | **RULED 2026-09-13 (desk r#3), owner: **DOE/LBNL ICE calculator on the SERC/Southeast class mix**, the desk's recommendation. FERC Order 831's $2,000 caps **offers** and SOCO takes none, so carrying it would import a market construct this footprint does not have. SOCO-20 derives and cites it per value; if no citable value survives, it falls back to $2,000 **with the misalignment stated on the field**. The Brattle ERCOT figure is cited as **method, never value** (rule 25) |
| **S6** capacity / adequacy | No capacity market. What is the reliability floor's requirement? | **Absent from `MARKET_DESIGN`, `_CURVE_ISOS`, `_CAPACITY_ISOS`** (→ `DEFAULT_MARKET_DESIGN`, `capacity_market=False`, the ERCOT/SPP branch). `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"]` comes from the Alabama Power / Georgia Power **IRP** filings and the SERC assessment, cited per value and per season (the footprint is winter-peaking in some years — Phase 0 measures which) | SOCO-10 IRP transcription | **RULED 2026-09-13 (desk r#3), owner: **winter 26.0 % as the scalar, misalignment documented**, the desk's recommendation. SOCO is **winter-peaking in 2 of 3 backcast years** — 47,368 MW 2024-01-17 07:00 and 46,490 MW 2025-01-22 08:00 against 45,558 MW 2023-08-25 16:00, and in 2025 summer sits 0.25 % below winter. 26.00 % is Southern's own published long-term **Winter** Target Reserve Margin (2024 Reserve Margin Study, Executive Summary RECOMMENDATIONS; summer 20.00 %; short-term −0.5 %). `PLANNING_RESERVE_MARGIN_BY_ISO` holds one scalar per ISO, so the seasonal structure is **stated on the field**, not hidden. Extending the registry to seasonal for every ISO was offered and **declined as an ISO-addition act** — it stays available as its own chartered lane | 
| **S7** the CAES unit | McIntosh (AL), EIA 7063 unit 1, **110.0 MW nameplate but a 25 MW summer/winter RATING** `Natural Gas with Compressed Air Storage`, operating 1991 — the only unit of its kind in the US fleet, and the model has no CAES class | **Map to a gas CT with the misalignment documented on the mapping** (it burns gas on discharge; 0.16 % of the footprint). Refuse a new technology class for one unit — that would be a new solve-affecting object, a matrix row and a cache-key risk (gate G8) for 25 MW | SOCO-10 | **RULED 2026-09-13 (desk r#3), owner: **map to a gas CT at the 25 MW rating**, the desk's recommendation as corrected by SOCO-10. The charter carried the **nameplate**; the source itself states a **25 MW** summer/winter rating, a **77 % derate**, which puts the unit at **0.035 %** of the footprint rather than 0.16 %. A CAES technology class is refused for one 25 MW unit |
| **S8** mid-window nuclear commissioning | **Vogtle 3 (1,114 MW) operating 2023-07 and Vogtle 4 (1,114 MW) operating 2024-04** — both *inside* the backcast window; measured nuclear generation steps 52.4 → 63.0 → 64.2 TWh across the three years | The fleet must be **per-year vintage-gated** so 2023 carries Vogtle 3 from July and 2024 Vogtle 4 from April. Phase 0 must establish that the existing vintage machinery (`data/raw/eia-860/vintage_<yr>/`) resolves a **within-year** COD, and if it resolves only to a year, the misalignment is documented and its energy error quantified before any solve | SOCO-10 | **ANSWERED, and the answer is worse than the card assumed — SUPERSEDED BY CARD S12.** SOCO-10 measured that the machinery does not resolve a within-year COD *and does not resolve the year either* for a brownfield addition: `cod_ramp.effective_cod` always prefers the plant's capacity-weighted mean COD for the ONLINE date, so Vogtle reads `load_cod_map()[649] -> (2005, 5)` and both new units are online **all 12 months of 2023**. Card **S12** carries the ruling |
| **S9** `TAIL_THRESHOLD` | $200 / $300 / n-a | **RESOLVED 2026-09-14 (desk r#5) — n/a, and no card was needed.** SOCO-13 returned **NO**, so no price series exists, so there is no tail to threshold: the three `TAIL_THRESHOLD` edits gate **G6** contemplated are **deliberately skipped and the skip is documented**, exactly as G6 pre-specified. Original text: **Deferred to after card S2.** With no price series there is no tail to threshold; with an EQR index the threshold is set from the *measured* distribution, never chosen to make C3c pass (rule 1 `[R-STRUCT]`) | SOCO-13 | — |
| **S10** W6 routing | who charters forecast-program entry | **ROUTE to the capx director** with a card once a keeper exists; this desk never writes `program-status.json` / `ff-verdicts.json` / `GOLDEN_ISOS` | — | — |
| **S11** who implements S2's determination class | Card S2 is ruled, but the class does not exist in `scripts/calibration_verdict.py` yet. Who charters the scorer amendment — this desk, or whoever owns the rubric? | **This desk charters it as SOCO-22 `[FABLE]`, scoped to ADDING a determination branch that no existing ISO can reach** (predicate: the ISO has no `actual_lmp.json` block, so C3a/C3b/C3c are unscored), with a byte-identity proof over all seven registered keepers' verdicts as its exit. Reason: it is a SOCO blocker (W4 cannot score without it), it is one file, and the alternative — routing it to a desk that has no reason to prioritise it — is how R-a sat open. **Refuse any version that touches an existing criterion's tiering, budget or threshold.** If you would rather the rubric owner do it, say so and the desk routes it instead | card S2 (ruled) | **RULED 2026-09-13 (desk r#3), owner: **this desk charters it as SOCO-22 `[FABLE]`**, the desk's recommendation. Scope is an **added branch keyed on the ABSENCE of an `actual_lmp.json` block** — no existing ISO can reach it, and it therefore serves NWPP's card N2 with the same amendment instead of producing two. Exit: a **byte-identity proof over all seven registered keepers' verdicts**. Any version touching an existing criterion's tiering, budget or threshold is refused. Issued r#3 |
| **S12** the COD-seam defect (raised as R-4 by SOCO-10; not anticipated in the charter) | `cod_ramp.effective_cod` **always** prefers a plant's capacity-weighted mean COD over a generator's own `Operating Month` for the **online** date — the per-unit preference exists only for **retirement** (the Homer City seam). Brownfield additions at multi-vintage plants are therefore online from the plant's mean COD. Measured by calling the live code: `load_cod_map()[649] -> (2005, 5)`, so Vogtle 3 **and** 4 are online all 12 months of 2023/24/25; `[56] -> (2023, 9)`, so a **greenfield** plant does ramp — the defect is brownfield-only | **Charter a cross-ISO repair lane BEFORE SOCO-20**: prefer the unit's own online date, symmetric with the retirement seam `effective_cod` already contains — the unit's `Operating Month` is the measured input and the plant mean the estimate, so rule 14 `[R-ACCURATE]` points there. A/B across all eight footprints as **its own lane, never inside SOCO-20**, because it moves **results (not cache keys)** for all seven registered keepers | SOCO-10 §2; measured EIA-923 unit CFs (Vogtle 3 **88.6 %** Jul–Dec 2023, Vogtle 4 **89.1 %** Apr–Dec 2024) | **RULED 2026-09-13 (desk r#3), owner: **charter the cross-ISO repair lane before SOCO-20**, the desk's recommendation. Magnitude, measured: phantom **+12.979 TWh** nuclear in 2023 (**+24.8 %** on 52.435) and +2.167 TWh in 2024 (+3.4 %); a 2023 SOCO backcast would read **≈65.41 TWh** of nuclear, **above the measured 2025 value of 64.17**, *inverting* the observed 52.4 → 63.0 → 64.2 commissioning step and displacing ~13 TWh of gas one-for-one. Barry A3 adds 774 MW ten months early (2.3–4.6 TWh) and is **not independently checkable until `AL_2023` lands** — it now has. Blast radius across all eight footprints (units with 2023–2025 CODs whose plant-collapsed COD year is earlier): **SOCO 3,040.3 MW** · SPP 1,127.4 · ERCOT 1,091.4 · CAISO 1,037.2 · MISO 927.4 · PJM 177.2 · NYISO 72.9 · NEISO 50.0 — **SOCO 2.7× the next-worst**, and Vogtle 3/4 the two largest trapped units in the national fleet. Issued r#3 as **SOCO-15 `[FABLE]`**; **CLOSED r#5 — the repair is on `main` (`9398000d`, PR #6127) and SOCO-20 is cleared.** SOCO-10's floor stands regardless of outcome: **the bias is stated on SOCO's first keeper's determination basis** |

Defaults recorded here so no lane re-litigates them (no card): `_MULTI_YEAR_ISOS` gains SOCO in W2
(rule 16 — a single-year SOCO keeper is refused from day one); `ISO_EV_KEY["SOCO"] = "O"` (`S` is
SPP's); the memory class is registered `per_plant=True, co_opt=False, peak_gb=<measured in SOCO-40>`;
**no import node** (SOCO's seams are served schedules, so neither `IMPORT_TRANCHES` nor
`IMPORT_ZONE` gets a SOCO key — gate G7).

---

## 4. Wave graph

```
W1  Phase 0/1 — zero-LP, ADDITIVE files only (parallel; disjoint: docs / data+fetch scripts)
    ┌────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────────┐
    │ SOCO-10 data audit +   │ │ SOCO-11 EPA CAMPD AL/GA  │ │ SOCO-12 IRP / SERC / SEEM  │
    │ registry-values table  │ │ + FERC-714 + interchange │ │ PDF sweep + fuel prices    │
    │ [OPUS] shared          │ │ [OPUS] shared            │ │ [OPUS] shared              │
    └───────────┬────────────┘ └────────────┬─────────────┘ └─────────────┬──────────────┘
                │        ┌──────────────────┴───────────────────┐         │
                │        │ SOCO-13 FERC EQR price index [FABLE] │         │
                │        │  (card S2 option a — STOP-gated)     │         │
                │        └──────────────────┬───────────────────┘         │
                └───────────────────┬───────┴─────────────────────────────┘
                                    ▼   DESK SITTING #2 — cards S3…S9 served with W1 evidence
W2  Registration — THE PIN FLIP (one PR)          ∥  matrix shard
    ┌─────────────────────────────────────────┐   ┌────────────────────────────┐
    │ SOCO-20 register + topology + every     │   │ SOCO-21 8th matrix shard   │
    │ registry + profile token  [FABLE]       │   │ + §5.8 queue + colour      │
    └──────────────────┬──────────────────────┘   └────────────────────────────┘
                       ▼   (every W3 derive calls get_iso_config("SOCO") — W3 is gated by W2 itself)
W3  Phase 2 derivation (parallel; each lane owns only its outputs)   ∥  site/docs wiring
    SOCO-30 outages + tranches │ SOCO-31 benchmarks │ SOCO-32 zonal shares + solar shape + gas hub
    SOCO-33 seam derive        │ SOCO-34 site JS/CSS/docs prose + log header
                       ▼
W4  First-ever solve → FIRST KEEPER → dashboard flip (ONE lane, ONE shard, ONE span — rule 32)
    SOCO-40  [FABLE]  --year 2023 2024 2025, one bundle, one registration
                       ▼
W5  Lever queue (pre-declared): SOCO-54 inter-OpCo TTC derive · SOCO-55 VOLL/adequacy ·
    SOCO-56 priced seams · SOCO-57 CAES/PS representation
W6  Forecast-program entry — ROUTED to the capx director (card S10)
```

---

## 5. Lane table

Column key — **Model**: `[FABLE]` = adjudication (topology / market-object design, the pin flip, the
price-benchmark construction, the first-keeper determination); `[OPUS]` = execution of a committed
recipe (census, fetch, frozen derives, shard emission, site wiring, pre-declared solves). **Sonnet
never** (rule 27 `[R-PUSH]`). **Profile** = the `DATA PROFILE:` line (`soco` exists only after
SOCO-20 lands; before that, `shared`).

| Lane | Model · why | Profile | Owns | Zero-LP gate | Exit check |
|---|---|---|---|---|---|
| **SOCO-10** audit | OPUS · census against the MISO/SPP audit recipe; recommends, never decides | shared | `docs/multi-iso/soco-data-audit.md` (NEW); `00-iso-addition-protocol.md` §0 row + §3; `01-data-needs-and-upload-manifest.md` SOCO rows | — | fleet census by BA `SOCO` off EIA-860 (plants/MW by fuel vs Southern's published totals); state list vs `campd-unit-level/` present → missing `<ST>_<yr>`; SOCO 930 span + defect screen; **registry-values table with a citation per value**; the two-timezone finding resolved |
| **SOCO-11** CEMS + load + interchange | OPUS · reproducible fetches through existing scripts | shared | `campd-unit-level/{AL,GA}_{2023..2026}.parquet` + README/SHA256SUMS rows; `zone-specific-demand/SOCO/` (NEW); `eia-930-interchange/SOCO interchange hourly.parquet`; `scripts/data/fetch_*` **additive keys only** | — | 8 CEMS files schema-identical to a sibling; FERC-714 three-respondent hourly sum **reconciled against `SOCO hourly.parquet::Demand`** (state the residual); DIBA duration curves per counterparty per year |
| **SOCO-12** documents | OPUS · fetch + transcription against a manifest | shared | `data/raw/soco-planning/` (NEW: IRP, SERC assessment, SEEM public reports, NRC status); `gas-prices/eia_delivered_gas_{AL,GA,MS}_monthly_2023-2025.csv` | — | every transcribed value carries URL + page/table; a 403/404 is recorded with its exact URL and STOPS that item — no value from memory |
| **SOCO-13** the price index | **FABLE** · card S2 option (a); this is *construction of a benchmark*, the most adjudication-heavy lane in the program | shared | `data/raw/ferc-eqr/` (NEW); `scripts/data/build_soco_eqr_price_index.py` (NEW); `_validation-source/actual_lmp_hourly_SOCO.parquet` **only if the STOP gate passes** | **STOP gate, pre-registered in its PRECOMMIT before any data is read**: product-taxonomy filter fixed ex ante; hourly coverage ≥ a stated floor; the index reconciled against an independent public anchor; a stated failure mode. **A gate written after seeing the series is a fitted benchmark and is refused** | either a committed series with its reconciliation table, **or** a documented NO — both are successful outcomes |
| **SOCO-14** BA membership | OPUS · a documents question, the same class SOCO-12 discharged | shared | `data/raw/zone-specific-demand/SOCO/` BA-membership citations (append-only to `SOURCES.md`); `docs/handoffs/FINDING-soco-14-*` | — | a **cited, documented** basis for Oglethorpe (107), MEAG (210) and Southern Power (186) being inside the `SOCO` BA — or a documented NO. **Gate G22**; card S3's ruling rests on it |
| **SOCO-15** COD seam | **FABLE** · a cross-ISO `src/` repair that moves seven keepers' RESULTS | code | `model`/`data` `cod_ramp.effective_cod` online-date preference + its tests; the eight-footprint A/B; `docs/handoffs/PRECOMMIT-soco-15-*` + `FINDING-soco-15-*` | zero-LP census FIRST (the mask diff per footprint, computed before any solve) | the online date prefers the unit's own `Operating Month`; **cache keys byte-identical for all seven** (results may move, keys must not — gate G8); per-ISO delta reported at full magnitude |
| **SOCO-22** rubric class | **FABLE** · a scorer amendment every ISO's verdict path reads | code | `scripts/calibration_verdict.py` — ONE added determination branch keyed on the absence of an `actual_lmp.json` block; its tests; `FINDING-soco-22-*` | — | **byte-identical verdicts for all seven registered keepers**; the new branch unreachable by any of them; serves NWPP's card N2 too |
| ~~**SOCO-20** registration~~ **LANDED r#6, graded PASS** | **FABLE** · the pin flip | shared→soco | every §2.3 row, ONE PR (#6152, merged as *"Register SOCO as the **ninth** region"*) | full test suite + `solve_surface_register.py --diff` **0 moved rows for all eight** incumbents | `_ISO_BUILDERS` is nine keys; seven keepers' `cache_key()` byte-identical; **every** remaining test failure carries a same-tree control that fails identically on main's code |
| **SOCO-21** matrix shard | OPUS | code | `mechanism-matrix/SOCO.js`, base `isos`, `ISO_ORDER`/`ISO_EV_KEY`, `mechanism-matrix.html` tag, shard-migration test, dashboard colour | `scripts/check_mechanism_matrix.py` | ONE commit (gate G2) |
| ~~**SOCO-30**~~ outages + tranches | OPUS · frozen derives | soco | **LANDED r#8 — GRADED PASS** (PR #6179/#6181). Six artifacts, 1,119 windows; **gate G4 both legs PASS**; three defects routed | G4 legs 1 & 2 | `FINDING-soco-30-2026-09-16.md` |
| ~~**SOCO-31**~~ benchmarks | OPUS · frozen derives | soco | **LANDED r#8 — GRADED PASS** (PR #6185). **Gate G9 = EXACTLY ZERO**, verified by the desk from the diff: `calibration_reference.json` **+295 / −1**, the sole deletion the `generated` stamp | non-SOCO diff = ∅ (G9) | `FINDING-soco-31-2026-09-16.md` |
| ~~**SOCO-32**~~ zonal shares + solar shape + gas hub | OPUS · frozen derives | soco | **LANDED r#10 — GRADED PASS** (PR #6205/#6208). Shares reproduced on the model clock, residual **3.03 / 2.92 / 1.18 %**; card S3 honoured exactly (the six-set *not rebuilt, not evaluated, not tuned toward*); solar shape from **measured irradiance at all 482 plant-years**, r = 0.988/0.975/0.933 at shift +0 h, **nothing pinned**; **G8 holds — 0 values moved** | shares sum to 1.0; five-respondent basis (card S3) | `FINDING-soco-32-2026-09-16.md` |
| ~~**SOCO-33**~~ seam derive | OPUS · derive only | soco | **LANDED r#8 — GRADED PASS** (PR #6180). Net-exporter sanity PASSES on both clocks; **G17 never approached**; the headline is the **interface limits**, 7 of 8 would refuse 36–42 % of measured flow | G19 sign convention verified | `FINDING-soco-33-2026-09-16.md` |
| ~~**SOCO-34**~~ site + docs | OPUS | code | **LANDED — PR #6191, merged 2026-09-16 04:43:09 UTC**, five minutes after the r#8 pin (which is why r#8 read it unmerged, correctly, and r#9 did not — ledger E-10). **GRADED PASS** by content. `iso-topologies.json` now carries all nine regions; `index.html`'s 47/44/58 was **checked and found already correct** | `check_registry_payload_parity` | `FINDING-soco-34-2026-09-16.md` |
| **SOCO-40** first solve | **FABLE** · first-keeper determination | soco | **ISSUED r#9 + ADDENDUM r#10 — DISPATCHABLE NOW.** ORCHESTRATOR; it never runs an LP (rule 32(a)): a screen shard on one year, then ONE span shard, ONE `--year 2023 2024 2025`, ONE bundle; both shards PUSH their bundles (rule 34(a)). No `--commitment` (P2 is archived and the flag now errors) | **GATE G4 FULLY DISCHARGED**: SOCO-30 ✓ SOCO-31 ✓ SOCO-32 ✓ | keeper registered with whatever determination it earns — `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` at best, **never `CALIBRATED`** |

---

## 6. Fetch / upload manifest

Every row is a **fetch first**; the manual fallback fires only on a documented block (the SPP
charter's owner ruling O-3 carries over).

| # | Item | Target path | Session-fetchable? | Lane | Manual fallback |
|---|---|---|---|---|---|
| 1 | CAMPD hourly CEMS **AL, GA** 2023–2025 (+2026 partial) | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **YES — probed 200 anonymous, 187 MB/state-year** (`api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-<yr>-<st>.csv`; `fetch_campd_unit_level.py --year Y --states AL GA`) | SOCO-11 | EPA CAMPD bulk page |
| 2 | FERC Form 714 hourly planning-area demand (Alabama/Georgia/Mississippi Power) 2023–2025 | `data/raw/zone-specific-demand/SOCO/` | **YES via PUDL** (`s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet`, probed 206). **FERC's own host 403s from this egress** | SOCO-11 | FERC 714 bulk CSV, or owner upload |
| 3 | SOCO BA-to-BA interchange 2023–2025 | `data/raw/eia-930-interchange/SOCO interchange hourly.parquet` | **YES** — `fetch_eia930_interchange.py --ba SOCO` **(needs `EIA_API_KEY`; unset in the charter container)** | SOCO-11 | EIA Grid Monitor CSV (key-free) |
| 4 | EIA delivered-to-electric-power gas, AL GA MS monthly | `data/raw/gas-prices/eia_delivered_gas_<ST>_monthly_2023-2025.csv` | **YES** — EIA API v2 (project key) | SOCO-12 | EIA dnav |
| 5 | **A price series for SOCO** | `_validation-source/actual_lmp_hourly_SOCO.parquet` | **UNKNOWN — this is card S2.** FERC EQR viewer probed 200; the ETL is SOCO-13's STOP-gated job. SEEM publishes no price | SOCO-13 | none exists; if (a) fails, card S2 option (b) governs |
| 6 | Southern IRP / SERC assessment / SEEM public reports / NRC licence status (Farley, Hatch, Vogtle) | `data/raw/soco-planning/`, `data/raw/nuclear-license-status/soco.csv` | likely — PDFs on public sites | SOCO-12 | owner uploads |
| 7 | Southern long-term load forecast (needs a real edition + vintage ≥ 2020 for `load_forecast/soco.py`) | `data/raw/load-forecast/soco/soco.csv` | from the IRP filings | SOCO-12 | **owner uploads — a W2 PRECONDITION** (gate G12) |
| 8 | Confirmed retirements (SOCO-area instruments: consent decrees, Plant Barry/Miller coal, Georgia PSC orders) | per registry `data/raw/…` | partial | SOCO-12 | owner uploads |
| 9 | Holdout years 2019–2022 of rows 1–4 | same paths | yes, same routes | after W4 | — |

---

## 7. Hard gates — how this goes wrong

| # | Failure | Wave | Mitigation |
|---|---|---|---|
| G1 | Pin flips half-way: `_ISO_BUILDERS` without `DEMAND_LOADERS` (import-time assert), or `SURFACE_ISOS` left at seven | W2 | ONE PR; §2.3 is the SOCO-20 checklist |
| G2 | Matrix atomicity: base `isos` + shard + `ISO_ORDER` + `ISO_EV_KEY` + html tag must land together; a shard missing an id hard-errors; every later lane must emit **8** cell lines | W2, forever | SOCO-21 single commit; cross-desk notice; every W3+ charter says "8 shards" |
| G3 | `data-profiles.yaml` token collision on `soco` | W2 | re-measure the trap at SOCO-20's base sha + a unit test |
| G4 | Solving before outages / benchmarks / zonal shares exist (an unscorable copperplate) | W3→W4 | SOCO-40 PRECONDITIONS: `git log origin/main --grep=SOCO-3[012]` all landed. **STATUS r#10: FULLY DISCHARGED — SOCO-30, SOCO-31 AND SOCO-32 ALL LANDED, so SOCO-40 is dispatchable.** (The r#8 reading, kept for the record:) **TWO OF THREE DISCHARGED, ONE OUTSTANDING.** SOCO-30 landed (its own two legs PASS: windows > 0 in every CEMS state-year — AL 196/206/240, GA 115/118/155, MS 21/31/37 = 1,119; and the 8 full-year rows are ALL the `eia923_netzero` structural fallback, **no unit fell back for want of data**). SOCO-31 landed. SOCO-32 had not been dispatched at that pin; it **LANDED at r#10** (PRs #6205/#6208) with its shares reproduced on the model clock and gate G8 holding at 0 moved values, which closes this gate. The gate is doing its job: without SOCO-32 there are no zonal shares, no solar shape and no gas hub, which is the unscorable copperplate this row names |
| G5 | C6: `authorized_price_tuning` must be declared **even as NONE**; DOF ledger must exist; any band ≠ 1.0 in SOCO's generic fallback breaks rule 25 `[R-ISO-SCOPE]` | W4 | charter states it. **Note for SOCO specifically**: the rule-1 offer-curve carve-out exists to tune *market offers*. SOCO takes no offers — its dispatch is cost-based — so a SOCO band ≠ 1.0 needs a much stronger story than an RTO's, and the desk's posture is **bands stay 1.0 unless the owner rules otherwise** |
| G6 | C3c needs `TAIL_THRESHOLD["SOCO"]` in three files + a regenerated `actual_tail.json` | W2 + W3 | **RESOLVED r#5 — the skip branch fired.** SOCO-13's STOP gate read **NO**, so card S2 yielded no series and **the three edits are deliberately skipped**, which is this gate's own pre-specified alternative and is documented here and at card S9. Nothing to regenerate |
| G7 | `test_iso_coverage` sweeps: `QUEUE_CAP_PER_TECH_GW["SOCO"]`, carbon-`None`, "if `IMPORT_TRANCHES` then `IMPORT_ZONE`" | W2 | no import node ⇒ neither key ⇒ `build_import_generators("SOCO") == []` |
| G8 | **Seven keepers' cache keys move** (a new `ScenarioConfig` field, a default flip, a `results/cache.py` edit) | W2, W3 | forbidden through W4; byte-identity proof is SOCO-20's exit; G-DRIFT audit before any comparison |
| G9 | Shared regenerated files (`actual_tail.json`, `actual_amplitude.json`, `eia_demand_profiles.parquet`) alter other ISOs' rows | W3-31 | `build_reference()` already MERGES per `--isos` (SPP gate G9's structural fix); non-SOCO diff = ∅ as an exit check. **OUTCOME r#8: PASS, and the desk re-measured it from the diff rather than reading the claim.** `git diff` over SOCO-31's commits gives `calibration_reference.json` **+295 / −1**, and the sole deletion is the `generated` date stamp; the three new capacity CSVs are +37 each. **One file legitimately carries non-SOCO deltas and the lane proved they are `main`'s, not its own**: `audit_eia923_completeness.audit()` loops over `_ISO_BUILDERS` and has no `--isos` filter, so `eia923_2025.json` gained an **NWPP** block (NWPP-31 never ran this audit) and a one-plant **SPP** `COAL_BIT`/`COAL_PRB` prior-year move with **no `status` and no `gate` change**. The lane ran a CONTROL — `origin/main`'s `scripts/` restored, `data/clean` removed, the audit re-run — and it is **byte-identical** to the committed file. Suppressing the NWPP block would have committed a file the script does not produce. Routed to the NWPP and SPP lanes |
| G10 | Neighbour-name collision in `data/neighbor_price._HR_GAS_ELASTIC` (keys are GLOBAL) | W2 | SOCO's neighbours are `TVA` / `MISO` / `DUKE` / `FLORIDA`; assert uniqueness |
| G11 | `run_isos_concurrent.py` KeyError; `calibration-solve.yml` dropdown lacks SOCO | W2 | in SOCO-20 |
| G12 | `load_forecast/soco.py` cannot register without a real edition/vintage | W1→W2 | **MET 2026-09-13 by SOCO-12 §0.1** — edition `Budget 2025 (B2025) / 2025 IRP`, vintage **2025**, horizon 2025–2044, 60 rows committed at `data/raw/load-forecast/soco/soco.csv`, parsing and `validate_tidy`-clean through the package's own `parse_unified_csv` (dry-run; the lane did not write SOCO-20's file). **The qualification is material and is NOT a G12 failure:** the forecast is **Georgia Power**, not the footprint — every `System` cell is **REDACTED** in the public disclosure, and **Alabama Power files no public IRP because Alabama has no IRP statute** (SOCO-12 §5). So the datatype covers ~half the footprint by peak and **a SOCO-wide forward peak is a CONSTRUCTION SOCO-20/SOCO-32 must declare** — nothing is grossed up. The measured SOCO-wide peak **history** (SOCO-12 §1.3) is the better evidence and is committed |
| G13 | Bundle bytes stranded, or a dead bundle dir left in `results/calibration/` → parity gate RED (rule 29(c)) | W4 | **The `.gitignore` is the PARENT's tree, never the shard's** (rule 34 `[R-SHARD-PROMOTABLE]` (a), corrected 2026-09-12). The SHARD **pushes its bundle to its own branch** — append a `.gitignore` NEGATION for its own out-dir, then a **PLAIN `git add`, never `git add -f`** (the `-f` form is what the auto-mode classifier refuses, and the refusal hardened a shard's permission state in miso-255) — and the bundle **must include `dispatch/<year>_P1.parquet`** or registration raises `FileNotFoundError`. The PARENT keeps per-year dirs out of `main` (rule 32(d)) by fetching, composing and committing only the composite. **Never `rm`** (rule 31 `[R-RETAIN]`, the ercot-255 incident). This gate is live evidence, not theory: `check_registry_payload_parity` is RED at the r#2 pin on another ISO's `caiso279_ablate_dswcouple_span` |
| G14 | Live writers on the same dicts (capx D-lanes on `capacity_market.py`; SCN on `constants.py`; the SPP/MISO lanes on `interchange/spec.py`) | W2 | append-last + rebase-last; desk collision check at issuance (ledger §4) |
| G15 | Desk grades a lane LOST on absence; reads green CI as proof | desk | handoff §0.3 |
| G16 | SOCO appears on the forecast board before W6, or anyone but the capx director writes it | W2+ | MUST-NOT-TOUCH line in every charter |
| G17 | **The price gap gets papered over** — a lane substitutes a neighbouring hub, an "adjusted" MISO-South series, or a cost-stack "price" and calls it the actual | every wave | §2.6 is quoted in every charter that touches scoring; card S2 is the only route |
| G18 | A `DATA PROFILE: code` session sees `integration` tests red for an unbuilt `data/clean`, or a cold first pass of `tests/curation` reporting a spurious failure | every lane | build `data/clean` (`scripts/regenerate_clean.py`) before the gates; read a first-pass curation failure as cold-start until re-run |
| G22 | **Card S3's three zones rest on a six-respondent sum whose BA membership is uncited** — PUDL gives 100 % county containment for Alabama Power (59/59), Georgia Power (155/155) and Mississippi Power (23/23), and **none at all** for Oglethorpe, MEAG or Southern Power, because G&T cooperatives and joint-action agencies have no retail territory of their own | W1→W3 | **A cited BA-membership basis is a HARD PRECONDITION on SOCO-32** — lane **SOCO-14** produces it. Until it lands, no zonal load share is derived (rule 23 `[R-FROZEN-DERIVE]`). If SOCO-14 returns a documented NO, the ruling's own premise is gone and card S3 returns to the owner rather than being worked around. The `PowerSouth + Tallahassee` falsifier (which **overshoots**, −2.28 / −2.41 / −4.15 %) is what makes the six-respondent set evidence rather than curve-fitting, and it is quoted wherever the sum is used. **OUTCOME r#5: G22 FAILED and the gate did its job.** SOCO-14 cited 107 and 210 from primary sources and returned a **documented NO on 186**; the card went back to the owner rather than being worked around, and the owner re-ruled to the **five fully-cited respondents** (§3 card S3). **The gate is now DISCHARGED for the five-set** — every component of the registered sum carries a primary-source BA-membership citation — and **SOCO-32 is unblocked on that basis and no other**. If a later lane wants 186 back in, it needs the load-side citation SOCO-14 could not find, and the card returns again |
| G19 | **Two-timezone footprint** (AL/MS Central, GA Eastern) silently mis-bins an hour, and a DST transition doubles or drops one | W1→W3 | SOCO-10 establishes the committed parquet's convention **before** anything reads it; every derived series states its timezone; the 2025 7-hour shortfall (§2.1) is explained, not padded |
| G20 | **A shard's container is reclaimed with the only copy of a result on it, or an idle shard blocks the next lane's concurrency** | W4, W5 | Rule 33 `[R-SHARD-ARCHIVE]`, added 2026-09-12 and not in the charter text. The trigger to archive is **"the parent has it"**, not "the shard finished": fetch the branch, check out the bundle, verify the config signature — **and verify retrievability first**, `git ls-tree -r <shard sha> -- <bundle path>` must return **more than zero files** (rule 34(d)); zero means the bytes are on a container only and the correct report is *not promotable without a re-solve, cost stated*. Record recovery by **full 40-char SHA, never a branch name** (33(d)). A branch carrying a bundle a promotion would register **stays until the owner rules** (33(f)(3) + rule 31). Branch deletion may simply be **refused — HTTP 403 measured 2026-09-12**, and the misleading symptom is `send-pack: unexpected disconnect` then `Everything up-to-date`; a session that cannot delete **says so and leaves the branch** rather than reporting a cleanup it did not perform |
| G21 | **A promotion leaves the superseded keeper registered, or shrinks the ISO's year set** | W5 onward | Rule 35 `[R-PROMOTE]`, added 2026-09-12 and not in the charter text. The **promoting session** prunes the outgoing keeper's **three stores** (`registry/<id>.json`, `runs/<id>.js`, its bundle dir) via `scripts/prune_iso_runs.py --iso SOCO` — this SUPERSEDES rule 15's "pruned at the next registration" timing. Order is fixed and each step gates the next: **enumerate the year union over every SOCO sidecar and write it into the PRECOMMIT BEFORE pruning** (35(b) — the delete destroys the only mechanical record); the incoming keeper must **cover that union**, in its own bundle or in a run stamped to it under rule 30 `[R-TOUCHPOINT-FOLD]` (a) — a dangling `holdout.keeper` reads as unstamped and the year drops off the report silently (35(c)); **promote, verify with `audit_keepers.py` E1, THEN delete** (35(e)); `--force-uncite` is the **intended** route past the governance-mention guard, not an override (35(d)). Invariant, checked by `audit_keepers.py` **E13**: after a promotion every registered SOCO run is the designated keeper or stamped to it, and the year set is no smaller (35(f)). **This gate is live evidence, not theory:** `check_gate_a_provenance` is RED at the r#2 pin because NYISO's 2026-09-12 promotion did not sweep — the exact failure this rule was written out of, observable in another program the day after the rule landed. **EXTENDED at the r#5 check-in: the PRUNE AND THE LINEAGE GUARD CONTEND, and rule 35(e) names only E1.** `audit_keepers` **E11** (keeper-lineage recipe fidelity over the full `solve_and_persist` kwarg surface) fires only *"whenever a shard records a structured lineage (`superseded.former_keeper`) **and both bundles are on disk**"* — so rule 35(a)'s prune of the outgoing keeper's **bundle dir** destroys E11's baseline. Measured live at main `c6c70190`: NYISO carries `! E11: lineage recipe diff not computable: former keeper 2026-09-13-nyiso231-anchor-span has no resolvable bundle on disk`. It degrades to a **WARN, not a FAIL** — which is the hazard, because the guard built to catch the nyiso-108→155 **silent de-arm** is itself silently disarmed. **SOCO's first promotion (W5) therefore runs the lineage diff BEFORE the prune**: rule 35(e)'s verify step is `audit_keepers.py` **E1 *and* E11**, both green on the incoming keeper, and only then `prune_iso_runs.py --iso SOCO`. If E11 cannot be computed, say so in the RESULT rather than letting a WARN stand in for a check that did not run |
| G23 | **A rebase re-arms a construction another region deleted as a silent-failure bug.** SOCO-20's branch (base `7e6978ee`, cut BEFORE NWPP-20 merged) writes `ISO_TO_BA_CODE: dict[str, str] = {iso: ba for ba, iso in BA_CODE_TO_ISO.items()}` — a **scalar inverse** of the map NWPP-20 then made many-to-one and whose scalar inverse it deleted by name. Taking "SOCO's side" on `data/fleet/models.py` at the merge would map `NWPP` → whichever of its 17 BAs sorts last (`NEVP`) and **silently return 1/17 of the pool** at every consumer — rule 26 `[R-DELETE]`: a deleted defective construction must not return as a merge artifact, and rule 25 `[R-ISO-SCOPE]`: SOCO's registration may not change NWPP's behaviour | W2 | **SOCO-20's rebase is NOT mechanical and must not be done by taking either side wholesale.** On `fleet/models.py` take **main's** structure (many-to-one + derived `ISO_TO_BA_CODES`) and add only the one row `"SOCO": "SOCO"` with its census comment; **delete** the branch's scalar-inverse line. The 8 `data/raw/eia-860/**/eia860_generators.parquet` binary conflicts are **derived artifacts, not data**: `scripts/data/process_eia860.py` on main filters on `BA_CODE_TO_ISO`, so re-running the curation step on top of merged main regenerates both regions' rows — no re-fetch, no judgment call, and **never** a hand-merge of a parquet. Verify by census: the rebuilt table must carry NWPP's 939 plants / 1,930 generators **and** SOCO's 335 / 786 (§2.2 of each audit). Measured at the check-in: **55 conflict markers across 25+ files** on PR #6152. **OUTCOME r#6: the hazard did NOT materialize, and clause (3) was WRONG.** (i) The scalar inverse is safe on main — NWPP-20 had already replaced it with a GUARDED comprehension (`{iso: codes[0] for iso, codes in ISO_TO_BA_CODES.items() if len(codes) == 1}`), so a pool is excluded by construction rather than collapsed; SOCO-20 rebased onto that and inherited it, and SOCO (1:1) keeps its scalar fast path. (ii) **This gate said the parquet step was mechanical — "no judgment call". It is not.** SOCO-20 ran `process_eia860.py --rescope-from-parquet` as prescribed and it was **NOT additive**: its last line rewrites the RAW rebuild whenever columns differ, which DROPPED the eGRID `heat_rate` join (8,101 populated rows on the canonical table), ADDED `planned_retirement_month`, reordered `balancing_authority_code`, and admitted one non-SOCO PJM row (60781). The suite caught it. **The correct recipe, now proven, is stronger than this gate's census**: rebuild each table as **main's committed frame byte-for-byte in main's column order and dtypes, plus the new region's rows only**, join the new rows' `heat_rate` from the committed eGRID PLNT23 cache under `EGRID_HR_WINDOW_BTU_KWH`, and assert **the non-new slice `.equals()` main's frame** per file — an identity check, not a count. The script defect is routed as **R-l**, unpatched, with the committed tables repaired |

---

## 8. Prompt pack

House style: every prompt implicitly begins — *Read `CLAUDE.md` freshly and in full;
`docs/multi-iso/05-backcast-playbook.md`; this plan (§1–§3, §7 and your §5 row are your charter);
`docs/multi-iso/spp-addition-plan-2026-09.md` §2.3/§7 as the mechanical precedent; the mechanism
matrix. Fresh branch off latest `origin/main`; rebase before pushing; zero solves until your
PRECOMMIT is pushed (where you solve at all).* And ends — *Push by pack size (CLAUDE.md "Git &
Pushing"; HTTP/1.1 retry on 408/500); fetch-back verify every pushed file ≥ 300 lines (rule 27);
no CI workflows (private repo, billed minutes); no `ScenarioConfig` default moves; never touch
`frontend/data/forecast/`, any other ISO's keeper shard, log or matrix shard; if you must touch a
file outside your regions, STOP and route to SOCO-DESK in your FINDING. Findings to
`docs/handoffs/FINDING-soco-<id>-<date>.md` — and NOTHING ELSE shared (§8.0).*

### 8.0 COLLISION RULES (standing — pasted into every lane session)

Inherited verbatim in substance from the SPP plan §8.0, which was written after ten lanes collided
on the same shared tables:

1. **A lane touches NO shared record.** Not this plan, not the ledger, not
   `docs/calibration-log/soco.md`, not `CHANGELOG.md`, not the shard's `keeper`/`gates` stamp, not
   `docs/mechanism-testing-matrix.md`. The DESK writes every one of those at its next refresh, from
   the lane's FINDING. A lane's record is ONE new file — its FINDING (+ PRECOMMIT) — and the FINDING
   carries a `## Log entry` section in `soco.md`'s format that the desk appends verbatim.
2. **The only shared file a lane may edit is its OWN CELL LINE in `mechanism-matrix/SOCO.js`** (and,
   under rule 28(c), one `·` cell line per foreign shard when it adds a field).
3. **Rebase, never merge-in.** `git fetch origin main && git rebase origin/main`, re-run the gates,
   `git push --force-with-lease` on your own branch.
4. **One PR per lane**, opened when the lane is DONE.
5. **Data and code regions stay disjoint by construction** (FILES YOU OWN); a second lane needing
   the same file is the desk's sequencing error — STOP and route.
6. **A lane that may produce a PROMOTABLE run asks the promotion question INSIDE its own session,
   while the bundle is alive** (rule 31 `[R-RETAIN]`; the container is ephemeral).
7. **Every solve runs in a shard; the lane session never runs an LP** (rule 32 `[R-SHARD]`), and a
   registrable run is **ONE shard, ONE `--year 2023 2024 2025` invocation, ONE bundle**
   (rule 32(b) — slim per-year fan-out is banned). The shard **pushes its bundle to its own
   branch** (rule 34 `[R-SHARD-PROMOTABLE]` (a)) — `printf '\n!results/calibration/<out-dir>/**\n'
   >> .gitignore`, then `git add .gitignore && git add results/calibration/<out-dir>`: a **PLAIN
   `git add`, NEVER `git add -f`** (the `-f` form is refused by the auto-mode classifier as
   [Modify Shared Resources], and in miso-255 the refusal hardened the shard's permission state
   until even the plain add was denied — costing a re-solve). The bundle **MUST include
   `dispatch/<year>_P1.parquet`** or registration raises `FileNotFoundError`. **`.gitignore` is the
   PARENT's tree, never the shard's** — a charter that tells a shard to gitignore or omit its
   bundle is a defect in the charter, and the desk owns that defect. **A shard prompt never
   passes `--no-container-preflight`** and reports its `container preflight:` and `memory peak:`
   lines (rule 32(c)(8)).
8. **Archive a shard the moment the parent has its bytes, not when the shard finishes** (rule 33
   `[R-SHARD-ARCHIVE]`): fetch → check out → verify, and only then archive. Verify retrievability
   before archiving anything — `git ls-tree -r <shard sha> -- <bundle path>` must return more than
   zero files (rule 34(d)). Record recovery by **full 40-char SHA, never a branch name** (33(d)).
   Never archive a running shard; never delete a branch carrying a bundle whose promotion the
   owner has not ruled on (33(f)(3) + rule 31 `[R-RETAIN]`). Branch deletion may be refused —
   **HTTP 403 measured 2026-09-12** — and a session that cannot delete says so.
9. **A promotion is not done until the outgoing keeper's three stores are gone and the incoming
   keeper carries every year SOCO has run** (rule 35 `[R-PROMOTE]`, gate G21). Enumerate the year
   union into the PRECOMMIT **before** pruning; promote, verify (`audit_keepers.py` E1), then
   `prune_iso_runs.py --iso SOCO`. **SOCO only** — never another ISO's shard.

### W1 — Phase 0/1 (issuable now; SOCO-10/11/12 are parallel, SOCO-13 needs only card S2's ruling)

#### SOCO-10 `[OPUS]` — data audit + registry-values table + protocol correction

```
You are lane SOCO-10. MODEL: Opus claude-opus-5 — a census against a defined recipe (the MISO and
SPP data audits); you RECOMMEND, you never decide topology and you never edit src/.
DATA PROFILE: shared.  Branch stem: claude/soco-10-audit-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/05-backcast-playbook.md §1 (Phase 0) and §8;
docs/multi-iso/soco-addition-plan-2026-09.md (§1-§3, §5 row SOCO-10, §6, §7 - and §2.6 IN FULL,
because the price problem changes what an audit must recommend); docs/multi-iso/spp-data-audit.md
and miso-data-audit.md (YOUR TEMPLATES - status table columns item/source/status
got|blocked|partial/file path/notes, then one section per item, then a copy-paste manual manifest);
docs/multi-iso/00-iso-addition-protocol.md §0-§3.

PRECONDITIONS: none (W1 is additive). SOCO-11/12/13 run in parallel - you consume nothing from
them; where you need a number they will fetch, write "pending SOCO-11/12/13", never a guess.

FILES YOU OWN: docs/multi-iso/soco-data-audit.md (NEW); docs/multi-iso/00-iso-addition-protocol.md
(§0 SOCO row + the §3 "seven ISOs" sentence ONLY); docs/multi-iso/01-data-needs-and-upload-
manifest.md (SOCO rows ONLY).
FILES YOU MUST NOT TOUCH: anything under src/, scripts/, configs/, tests/, frontend/, data/;
05-backcast-playbook.md; any other ISO's audit; this plan; the ledger.

TASK - write docs/multi-iso/soco-data-audit.md:
(1) FLEET CENSUS off the committed EIA-860 parquets (data/raw/eia-860/eia860_plant.parquet joined
    to eia860_generator_operable.parquet on Plant Code, BA code SOCO - do NOT call
    get_iso_config("SOCO"), it does not exist yet). CONFIRM OR CORRECT the charter's numbers:
    335 plants / 786 generators / 70,665.7 MW; GA 41,284.4 / AL 24,494.0 / MS 4,577.7 / FL 309.6 /
    MA 1.5. ADJUDICATE the 1.5 MW "MA" row and the six FL plants (in-footprint or source defect?)
    and state the rule you applied. Reconcile against Southern Company's own published fleet
    totals with a page cite. Then diff the state list against data/raw/campd-unit-level/<ST>_<yr>
    present -> the missing list (expected {AL, GA} x {2023,2024,2025}; MS is present 2019-2026).
(2) EIA-930: "SOCO hourly.parquet" span/columns/per-year demand TWh/per-fuel TWh/interchange sign
    convention. CONFIRM the charter's numbers and EXPLAIN the two defects it found: 2025 carries
    8,753 local-date hours (7 short - which hours, and why), and "NG: PS" is NaN in 17,647 of
    26,304 hours despite 1,306.6 MW of pumped storage in the fleet. Run the repo's existing
    median-ratio defect screen over every NG: column and report what it flags.
(3) TIMEZONE - a first for this model: the footprint spans America/Chicago (AL, MS) and
    America/New_York (GA), and fetch_eia930_hourly.BA_TIMEZONE has NO SOCO entry. Establish what
    convention the COMMITTED parquet's "Local time"/"Local date" columns actually use (evidence,
    not assumption - check DST transitions and the hour-count arithmetic), and state the convention
    every downstream series must adopt. This is gate G19 and it is yours to close.
(4) THE REGISTRY-VALUES TABLE - one row per value SOCO-20 will need, each with a primary citation
    (URL + page/table) or "pending SOCO-12": planning reserve margin by season (Alabama Power and
    Georgia Power IRPs, SERC assessment), VOLL (card S5 - propose an economic value with a cite;
    note explicitly that FERC Order 831's $2,000 caps OFFERS and SOCO takes none), state->zone map
    candidate, load-share fallback, gas basis proxy (Transco Zone 4 / Southern Natural Gas; EIA
    state delivered-to-EP series as the proxy), coal price basis, nuclear monthly CF candidates
    (Farley, Hatch, Vogtle 1-4), queue caps by tech, state RPS floors (AL/GA/MS have none - say so
    with the DSIRE cite rather than leaving the row blank), LTLF edition + vintage, eGRID vintage,
    TRANSMISSION_BASE_STATIC_VINTAGE candidate. NEVER invent a number: a cell is a cited value or
    "pending".
(5) VOGTLE 3/4 (card S8): confirm from EIA-860 that unit 3 is 1,114 MW operating 2023-07 and unit 4
    1,114 MW operating 2024-04, then establish whether the repo's fleet-vintage machinery
    (data/raw/eia-860/vintage_<yr>/) resolves a WITHIN-YEAR commercial operation date or only a
    year. If only a year, QUANTIFY the energy error each way against the measured nuclear steps
    (52.4 -> 63.0 -> 64.2 TWh) and recommend the handling. Do the same for Barry A3 (774 MW CC,
    operating 2023-11).
(6) ZONE RECOMMENDATION (recommend, do not decide - the desk serves card S3 from this): 1 zone vs
    3 (Alabama Power / Georgia Power / Mississippi Power). Say what the data you can see supports,
    what evidence SOCO-11 must supply, the FIPS mechanics of each option, and - the part that
    matters - what a zone split can and cannot be VALIDATED against when no zonal price exists.
(7) MANUAL MANIFEST: copy-paste block of every item you could not source, with exact URLs.
Then CORRECT docs/multi-iso/00-iso-addition-protocol.md §0 (add a SOCO row saying "not registered -
see soco-addition-plan-2026-09.md") and the §3 sentence that counts the registered ISOs.

RULES THAT BITE: 5 [R-NO-MAGIC], 13 [R-MEASURED] (every value a reproducible physical/market
input), 14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (you derive nothing), 27 [R-PUSH], 28 (you test no
mechanism; no matrix cell moves).
EXIT: the audit doc, the two corrections, docs/handoffs/FINDING-soco-10-<date>.md. Report to the
owner with the census table, the missing-CEMS list and the timezone finding FIRST.
```

#### SOCO-11 `[OPUS]` — EPA CAMPD (AL/GA) + FERC-714 zonal load + interchange

```
You are lane SOCO-11. MODEL: Opus claude-opus-5 - reproducible fetches through existing scripts; no
design choices. DATA PROFILE: shared.  Branch stem: claude/soco-11-fetch-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md (§2.4, §2.5, §5
row SOCO-11, §6 rows 1-3); docs/multi-iso/miso-data-audit.md Item 1 (the CAMPD procedure) and
docs/multi-iso/spp-addition-plan-2026-09.md §6 row 1 (the same route, run for four states);
scripts/data/fetch_campd_unit_level.py and fetch_eia930_interchange.py docstrings;
data/raw/campd-unit-level/README.md + SHA256SUMS.txt conventions;
data/raw/zone-specific-demand/MISO/SOURCES.md (your SOURCES template).

PRECONDITIONS: none. SOCO-10/12/13 are parallel; you own no file they own.
FILES YOU OWN: data/raw/campd-unit-level/{AL,GA}_{2023,2024,2025,2026}.parquet (+ README/SHA256SUMS
rows); data/raw/zone-specific-demand/SOCO/ (NEW dir + SOURCES.md);
data/raw/eia-930-interchange/"SOCO interchange hourly.parquet" (+ README row); ADDITIVE keys only
in scripts/data/fetch_eia930_interchange.py / fetch_eia930_hourly.py (a SOCO BA_TIMEZONE entry -
and read SOCO-10's timezone finding first, or write BOTH zones' handling explicitly).
FILES YOU MUST NOT TOUCH: any existing raw file (data/raw is immutable); src/; configs/; tests/;
docs/multi-iso/soco-data-audit.md (SOCO-10's).

TASK, in this order, each its own small commit:
(1) CEMS: for Y in 2023 2024 2025 (then 2026 partial):
    python scripts/data/fetch_campd_unit_level.py --year Y --states AL GA
    The bulk route was probed 200 anonymous at charter and each state-year CSV is ~187 MB, so plan
    the disk: fetch, convert, verify, and delete the intermediate CSV before the next one. Verify
    the arrow schema equals a sibling (e.g. MS_2024) - the fetcher asserts it - and record
    rows/facilities/units per file. Update README + SHA256SUMS.
(2) ZONAL LOAD - the FERC Form 714 spine (plan §2.5). SOCO has NO EIA-930 sub-BAs (measured at
    charter: the sub-BA product covers CISO/ERCO/ISNE/MISO/NYIS/PJM/PNM/SWPP and nothing else), so
    the source is FERC Form 714 Part 3 Schedule 2 hourly planning-area demand for the Alabama
    Power, Georgia Power and Mississippi Power respondents. Route 1 (probed 206, rangeable):
    s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet
    Route 2 (probed 403 from the charter egress, retry from yours): FERC's own bulk CSV.
    THE GATE ON THIS ITEM: the three respondents' hourly sum must be reconciled against
    data/raw/eia-930-hourly/"SOCO hourly.parquet"::Demand - report the annual residual, the
    correlation and the max hourly delta, and state the timezone alignment you applied. A share
    derived from a series that does not add up to the BA's own metered demand is NOT a share: if
    the reconciliation fails, land the raw data with the failure documented and STOP, do not
    rescale anything to close it (rule 13 [R-MEASURED]).
(3) INTERCHANGE: fetch_eia930_interchange.py --ba SOCO for 2023-2025 -> the DIBA series (TVA, MISO,
    Duke, the Florida BAs, Santee Cooper, and every other counterparty). NOTE: this needs
    EIA_API_KEY, which was UNSET in the charter container - if yours has none, use the key-free
    Grid Monitor interchange files and say so in your SOURCES.md. In the FINDING: a net-interchange
    duration-curve summary per counterparty per year with the sign convention stated (the charter
    measured SOCO as a net EXPORTER of 10.2/10.8/13.0 TWh in 2023/24/25 - confirm or correct).
Anything that returns 403/404: record the exact URL + status in the FINDING's blocked table and
STOP that item - no transcription from memory, no secondary-source values.
RULES THAT BITE: 13 [R-MEASURED], 14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (fetch, do not derive),
26 [R-DELETE], 27 [R-PUSH] (parquets are binary - git push by pack size; split by state-year if a
pack is refused; never push_files a parquet), 28.
EXIT: docs/handoffs/FINDING-soco-11-<date>.md with the got/blocked table, per-file row counts and
schema checks, the FERC-714 reconciliation table, and the DIBA duration summaries. Report to the
owner: which of {AL,GA} x {2023,2024,2025} landed, and the FERC-714 reconciliation residual, FIRST.
```

#### SOCO-12 `[OPUS]` — IRP / SERC / SEEM / NRC documents + fuel prices

```
You are lane SOCO-12. MODEL: Opus claude-opus-5 - fetch + transcription against a manifest.
DATA PROFILE: shared.  Branch stem: claude/soco-12-docs-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md (§3 cards S5/S6/
S8, §5 row SOCO-12, §6 rows 4, 6-8); data/raw/spp-planning/README.md (YOUR TEMPLATE for a planning
corpus: a README carrying the verified source-URL table, the re-fetch command, the retention status
and SHA256SUMS.txt); scripts/lib/nuclear_license_status/ and load_forecast/ (the spec shape a
registry module must satisfy - note test_specs_declare_an_edition_and_a_vintage).

PRECONDITIONS: none.
FILES YOU OWN: data/raw/soco-planning/ (NEW); data/raw/nuclear-license-status/soco.csv (NEW);
data/raw/load-forecast/soco/soco.csv (NEW); data/raw/gas-prices/eia_delivered_gas_{AL,GA,MS}_
monthly_2023-2025.csv + SOURCES_soco_gas.md.
FILES YOU MUST NOT TOUCH: src/; scripts/lib/*/ (the registry MODULES are SOCO-20's - you supply
their DATA); tests/; any other ISO's data.

TASK:
(1) PLANNING CORPUS: the most recent Alabama Power and Georgia Power IRP filings, the SERC
    reliability assessment covering this footprint, Southern Company's fleet/capacity disclosures,
    and SEEM's public reports. Transcribe into the README's values table, each with URL + page:
    planning reserve margin BY SEASON (the footprint may be winter-peaking in some years - say
    which, with the evidence), the peak-load history, the resource plan, and any published
    transfer limit between the operating companies (card S3 needs this; if none is public, say so
    explicitly - that is the finding, and it is what makes the TTC Tier-3).
(2) SEEM: establish, with citations, EXACTLY what SEEM publishes. The charter's finding is that it
    publishes participation and matched-volume statistics and NO price. Confirm or correct it -
    this bears directly on card S2 and a wrong answer here misdirects the whole program.
(3) NRC: licence expiry + any SLR status for Farley 1-2, Hatch 1-2, Vogtle 1-4 -> soco.csv in the
    shape scripts/lib/nuclear_license_status/ expects.
(4) LTLF: a real long-term load forecast with an EDITION and a VINTAGE (>= 2020) from the IRPs.
    This is a W2 PRECONDITION (gate G12) - if no citable edition exists, say so loudly in your
    FINDING's first paragraph, because it blocks registration.
(5) GAS: EIA API v2 monthly delivered-to-electric-power gas price for AL GA MS 2023-2025 (the MISO
    citygate-proxy pattern, data/raw/gas-prices/SOURCES_miso_citygate.md). Name the pipeline basis
    the footprint actually prices against (Transco Zone 4 / Southern Natural Gas) and whether a
    public daily/monthly index for it is reachable.
(6) CONFIRMED RETIREMENTS: enforceable public instruments for SOCO-area fossil exits (consent
    decrees, Georgia PSC orders, Alabama PSC filings, announced Plant Barry / Miller coal dates).
    The admissibility bar is CLAUDE.md's step-0 bar: an enforceable public instrument with a date.
Anything blocked: exact URL + status in the FINDING, then STOP that item.
RULES THAT BITE: 5 [R-NO-MAGIC], 13, 14, 27, 28.
EXIT: docs/handoffs/FINDING-soco-12-<date>.md with the got/blocked table and the transcribed values
table. Report the LTLF availability and the SEEM price answer FIRST - those two are what the desk
needs to move.
```

#### SOCO-13 `[FABLE]` — the FERC EQR price index (card S2 option a; STOP-gated)

```
You are lane SOCO-13. MODEL: Fable - this lane CONSTRUCTS A BENCHMARK, which is the most
adjudication-heavy act in an ISO addition: every later price criterion is scored against what you
build, so a fitted or ill-founded index would corrupt the whole program invisibly. DATA PROFILE:
shared.  Branch stem: claude/soco-13-eqr-price-<4 chars>.
Read CLAUDE.md freshly and in full - rules 1 [R-STRUCT], 13 [R-MEASURED] and 14 [R-ACCURATE] are
the whole of your charter; docs/multi-iso/soco-addition-plan-2026-09.md §2.6 IN FULL, §3 card S2,
§5 row SOCO-13; scripts/data/build_spp_lmp_reference.py (the shape of a price-reference builder in
this repo); data/raw/_validation-source/actual_lmp_hourly_SPP.parquet's schema
(year/hour/zone/rt/da) and the cross-check gate SPP-14 applied to it.

ONLY START AFTER the owner has ruled card S2. If S2 is unruled, STOP and say so.

THE PROBLEM: Southern Company publishes no LMP, no day-ahead price and no hourly index, and SEEM
publishes no price. The one public, transaction-level, measured price source covering this
footprint is FERC's Electric Quarterly Reports (EQR): every seller files, per transaction, the
product name, delivery point, begin/end datetime, quantity and price. Your job is to decide
whether a defensible footprint-hourly price index can be built from it, and either build it or
document why not. BOTH outcomes are a successful lane.

WRITE THE PRECOMMIT FIRST, PUSH IT, AND ONLY THEN TOUCH THE DATA. The PRECOMMIT fixes, ex ante:
  (a) the SELLER/BUYER and DELIVERY-POINT filter that defines "the SOCO footprint";
  (b) the PRODUCT filter - which EQR product names count as short-term wholesale energy and which
      are excluded (capacity, transmission, monthly/annual block, booked-out, index-priced);
  (c) the AGGREGATION - volume-weighted or median, how a multi-hour block is allocated to hours,
      how a thin hour is handled (carried, NaN, or dropped - and NEVER interpolated toward
      anything the model produces);
  (d) THE STOP GATE, as pass/fail numbers, not adjectives: a minimum hourly coverage over
      2023-2025; a maximum share of hours resting on fewer than N transactions; and a
      RECONCILIATION against at least one INDEPENDENT public anchor (candidates to evaluate:
      EIA's published wholesale spot-price series for the region, the implied cost stack from
      EIA-923 monthly fuel receipts and heat rates as a boundedness check, and any published
      SEEM or Southern disclosure SOCO-12 finds) - with the tolerance stated as a number;
  (e) what you will do if the gate FAILS: land nothing to _validation-source, write the NO.
A GATE WRITTEN OR LOOSENED AFTER SEEING THE SERIES IS A FITTED BENCHMARK AND IS REFUSED. Say so in
the PRECOMMIT in your own words, so the record shows you knew.

THEN: fetch EQR (eqrreportviewer.ferc.gov was probed 200 at charter; ferc.gov's static host 403s
from at least one egress - record exactly what worked), build
scripts/data/build_soco_eqr_price_index.py, and run your own gate.

FILES YOU OWN: data/raw/ferc-eqr/ (NEW, with a README in the spp-planning template);
scripts/data/build_soco_eqr_price_index.py (NEW); data/raw/_validation-source/
actual_lmp_hourly_SOCO.parquet (ONLY if the gate passes); docs/handoffs/PRECOMMIT-soco-13-<date>.md
and FINDING-soco-13-<date>.md.
FILES YOU MUST NOT TOUCH: src/; any other _validation-source file; actual_lmp.json (SOCO-31's);
tests/; this plan; the ledger.

RULES THAT BITE: 13 [R-MEASURED] - the index must be a reproducible market input that would
regenerate for a forward year, never an outcome fitted to anything the model produces; 14
[R-ACCURATE] - if the real data makes the eventual backcast look worse, that is a discovered bug
elsewhere, not a reason to adjust the index; 1 [R-STRUCT] - you are FORBIDDEN to evaluate your
index by whether it improves any residual, because no model run exists yet and none may be used;
23 [R-FROZEN-DERIVE]; 27 [R-PUSH].
EXIT: FINDING with the PRECOMMIT's gate table filled in with measured values, the reconciliation
table, and a one-line verdict: SERIES LANDED or NO, with the reason. Report the verdict FIRST.
```

### W2 — registration (issued at sitting #2 after S3–S9 are ruled; SOCO-21 may go first, it is disjoint)

#### SOCO-20 `[FABLE]` — the pin flip

```
You are lane SOCO-20. MODEL: Fable - this is the registration adjudication: one PR that makes the
model's seven-region world an eight-region world, and every registry that hard-codes seven must
move in it or the import-time asserts fail. DATA PROFILE: shared (you create the `soco` profile).
Branch stem: claude/soco-20-register-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md §2.3 (YOUR
CHECKLIST - work it row by row and report it back row by row), §3 (the RULED cards - implement the
rulings, never your own preference), §7 gates G1-G3, G5-G12, G19; docs/multi-iso/soco-data-audit.md
(SOCO-10's registry-values table is the SOURCE of every number you register - a value not in it and
not cited in your own docstring is a rule 5 [R-NO-MAGIC] violation);
docs/handoffs/FINDING-spp-20-*.md and src/market_sim/config/iso_configs.py::_spp_config IN FULL -
that function is your worked template, docstring conventions included.

PRECONDITIONS, verify each and STOP if any is unmet: cards S1, S3-S8 RULED (quote each ruling in
your PRECOMMIT); SOCO-10 and SOCO-11 merged; manifest row 7 (a real LTLF edition + vintage) landed
by SOCO-12 - gate G12 makes this hard.

ONE PR. Work §2.3 top to bottom. The atomicity that bites: _ISO_BUILDERS + DEMAND_LOADERS +
SURFACE_ISOS must be in the SAME commit (two import-time asserts and one pinned-tuple test).

THE PROOF THAT MATTERS (gate G8): the seven existing keepers' cache keys must not move. Run
`python scripts/solve_surface_register.py --diff origin/main HEAD` and show ZERO moved rows for
ERCOT/CAISO/PJM/MISO/NYISO/NEISO/SPP; declare only the names whose SOCO projection is new. Then
re-derive at least two committed keepers' cache_key() and show them byte-identical. No new
ScenarioConfig field, no default flip, no results/cache.py edit - if you believe you need one,
STOP and route to SOCO-DESK.

WHAT MAKES SOCO DIFFERENT FROM EVERY PRIOR REGISTRATION, and must be visible in the code:
 - It is a BALANCING AUTHORITY, not an ISO. Say so in _soco_config's docstring, in one sentence,
   with the Hillabee/plant-55411 provenance and the TVA exclusion.
 - NO capacity market: absent from MARKET_DESIGN, _CURVE_ISOS, _CAPACITY_ISOS - document the
   absence as deliberate rather than leaving it to be read as an oversight.
 - NO import node: neither IMPORT_TRANCHES["SOCO"] nor IMPORT_ZONE["SOCO"] (gate G7).
 - Offer-curve bands stay 1.0 (gate G5): the rule 1 [R-STRUCT] carve-out authorizes tuning MARKET
   OFFERS, and SOCO takes none.
 - TWO TIMEZONES (gate G19): register what SOCO-10 established, and comment it.
 - TTCs are Tier-3 and CANNOT BIND (card S3), with the misalignment stated on the link exactly as
   _spp_config states SPP's.
 - TAIL_THRESHOLD: register it only if SOCO-13 landed a series; if not, skip all three copies and
   document the skip where a reader will hit it (gate G6).

FILES YOU MUST NOT TOUCH: frontend/data/forecast/**; any other ISO's keeper shard, log or matrix
shard; docs/codebase-site/data/mechanism-matrix/** (SOCO-21's); this plan; the ledger.
EXIT: get_iso_config("SOCO").validate_topology() green; the full unit+curation suites green;
the §2.3 checklist reported row by row with its verification; the cache-key proof; FINDING-soco-20.
```

#### SOCO-21 `[OPUS]` — the eighth matrix shard, the ev key, the colour

```
You are lane SOCO-21. MODEL: Opus claude-opus-5 - a mechanical emission against a validated schema.
DATA PROFILE: code.  Branch stem: claude/soco-21-matrix-<4 chars>.
Read CLAUDE.md rule 28 [R-MECH-MATRIX] in full; docs/mechanism-testing-matrix.md;
scripts/lib/mech_matrix.py; docs/codebase-site/data/mechanism-matrix/SPP.js (your template - the
seventh shard, emitted by lane SPP-21); scripts/check_mechanism_matrix.py.

ONE COMMIT (gate G2 - a shard missing an id hard-errors, and a half-landed matrix breaks every
lane's rule-28 duty in every ISO):
 - docs/codebase-site/data/mechanism-matrix/SOCO.js - a cell for EVERY mechanism id in the base
   file, all `U` (untested) except where a mechanism is structurally n/a for SOCO, which is `·`
   with its reason (no capacity market, no import node, no reserve co-optimisation, no offer-curve
   tuning channel);
 - the base file's `isos` list; scripts/lib/mech_matrix.py ISO_ORDER and ISO_EV_KEY (use "O" - "S"
   is SPP's); the mechanism-matrix.html tag; tests/unit/config/
   test_mechanism_matrix_shard_migration.py's expected set;
 - the dashboard colour: a --iso-soco token in docs/codebase-site/css/shared.css and its use in
   js/backcast-runs.js, following the --iso-spp precedent;
 - docs/mechanism-testing-matrix.md §5.8: the SOCO lever queue, seeded from this plan's W5 list
   (SOCO-54 inter-OpCo TTC, SOCO-55 VOLL/adequacy, SOCO-56 priced seams, SOCO-57 CAES/PS).
Verify with scripts/check_mechanism_matrix.py and paste its OUTPUT, not its exit code (gate G15).
FILES YOU MUST NOT TOUCH: any other ISO's shard CELL VALUES (you add SOCO's column, you never edit
another ISO's verdict); src/; frontend/data/**.
EXIT: FINDING-soco-21 with the checker output and the shard's cell census (n ids, n `U`, n `·`).
```

### W3–W6 — charters issued at the sittings that unblock them

The desk issues these against the SPP program's own W3/W4 charters, which are committed and worked
(`docs/multi-iso/spp-addition-plan-2026-09.md` §8 W3/W4). The SOCO deltas each charter must carry:

- **SOCO-30** (outages + tranches) — AL/GA CEMS only landed in W1; the per-plant binning recipe is
  `docs/binning-methodology.md`; **the CAES unit's mapping is card S7's ruling**, applied here.
- **SOCO-31** (benchmarks) — **LANDED 2026-09-16, `FINDING-soco-31-2026-09-16.md`.** `build_reference --isos SOCO` **merges**, so non-SOCO rows must diff
  to ∅ (gate G9); `actual_lmp.json` gets a SOCO block **only if SOCO-13 landed a series**, and the
  determination-side consequence of it not landing is card S2's ruling, applied here.
- **SOCO-32** (zonal shares, solar shape, gas hub) — shares from FERC-714 (§2.5), **not** sub-BA;
  no wind in the footprint worth shaping; gas hub per SOCO-12's basis finding.
- **SOCO-33** (seam derive) — served EIA-930 `Total interchange` (card S4).
- **SOCO-34** (site + docs) — **NINE**-region prose (not eight — NWPP registered the same day and took
  the eighth slot), `docs/calibration-log/soco.md` header, **plus the four items SOCO-20 §7 routed here**
  (`docs/multi-iso/README.md` prose, `build_status.ISO_ORDER`, `keeper_store`, `render_data_dictionary`,
  `frontend/data/backcast/keepers/index.json` display order). **AND — added r#7 — the explicit debt
  NWPP-35 left for this lane and cited in place, which did not exist when W3 was issued at r#6.**
  NWPP-35 swept the shared site prose to nine regions but correctly did NOT serialize SOCO (rule 25
  `[R-ISO-SCOPE]`), and said so in the artifact rather than leaving it to be discovered:
  `docs/codebase-site/data/iso-topologies.json` `_meta.description` reads *"_ISO_BUILDERS carries NINE
  registered regions at 2026-09-14 (… SPP NWPP SOCO); eight are serialized here. SOCO registered the same
  day as NWPP and its block is owed by the SOCO desk's own site lane, not by this one."* So SOCO-34 owes,
  specifically: (a) SOCO's block in `iso-topologies.json` (keys are currently the eight without SOCO) and
  the `_meta.description` updated once it lands; (b) SOCO's filter entry at
  `docs/codebase-site/data-completeness.html:364`, where the same debt is marked in a code comment;
  (c) `config-reference.html:404`, which reads *"the **eight** serialized into `iso-topologies.json`
  render below"* and becomes nine; (d) a CHECK, not an assumption, that `index.html:297`'s
  *"Nine regions, 47 zones (44 carry load), 58 transmission links"* already counts SOCO's three zones —
  if it does not, the count is wrong in the other direction and this lane fixes it. **This is a debt
  handed over cleanly by another program's lane, not a collision** — the citation is in the artifact.
- **SOCO-40** (first solve) — **ONE shard, ONE `--year 2023 2024 2025`, ONE bundle** (rule 32(b));
  the shard pushes its bundle to its own branch by the §8.0 rule 7 mechanics — `.gitignore`
  negation then a **plain `git add`, never `git add -f`**, bundle including
  `dispatch/<year>_P1.parquet` (rule 34(a) as corrected 2026-09-12). PRECOMMIT states the price
  posture from card S2's ruling **before** the solve — on the no-price branch the run may never
  read `CALIBRATED` and the price gap is reported at full magnitude. The parent verifies
  retrievability (`git ls-tree`, rule 34(d)) before archiving the shard (rule 33), asks the
  promotion question **in-session while the bundle is alive** (rule 31 `[R-RETAIN]`), and states
  in the RESULT where each bundle is and what a promotion would cost from that state (34(e)).
  **Year set:** SOCO's first keeper is 2023–2025 and that IS the union, so rule 35(c) is
  satisfied trivially — but manifest row 9 (holdout years 2019–2022) changes that the moment it
  lands: from then on **every** SOCO solve batch covers the union, one shard per year (rule
  34(c)), and any year not stamped to the keeper drops off the ISO's report silently.

### W3 issuance r#6 (2026-09-14, pinned `d54cd9c5`) — the five charters, written out r#7

Issued against SPP's committed W3 charters (`docs/multi-iso/spp-addition-plan-2026-09.md` §8, SPP-30…34)
with the SOCO deltas above applied. Every charter ends with the pack's EXIT boilerplate **including the
`## Log entry` line** — ledger E-6: the two lanes that shipped without one were both desk-drafted charters
that omitted it.

#### SOCO-30 `[OPUS]` — unit outage windows + thermal tranches (frozen derives)

```
You are lane SOCO-30. MODEL: Opus claude-opus-5 — frozen derives on a committed recipe (rule 23).
DATA PROFILE: soco.  Branch stem: claude/soco-30-outages-tranches-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md §5 row SOCO-30, §7 G4
and G19; docs/multi-iso/05-backcast-playbook.md §0 items 2 and 4, §3 (dependency order); the docstrings of
scripts/data/derive_campd_unit_outages.py, derive_thermal_tranches.py, scripts/tag_mixed_plants.py (under
scripts/, not scripts/data/), build_offer_curve_overrides.py; docs/binning-methodology.md;
data/raw/campd-unit-outages-MISO.csv header (your output template); FINDING-soco-10 (the census, the
timezone convention, the three measured defects) and FINDING-soco-11 (which CEMS state-years landed).

PRECONDITIONS (git log origin/main --grep=SOCO-20 and --grep=SOCO-11; STOP if unmet): SOCO-20 LANDED —
get_iso_config("SOCO") works, SOCO is the NINTH registered region; AL and GA CEMS 2023-2025 present
alongside the MS_2024 template SOCO-11 matched schema-equal.
FILES YOU OWN: data/raw/campd-unit-outages-SOCO.csv (+ -short/-layup/-e923 siblings exactly as the derive
emits them), data/raw/campd-partial-outages-SOCO.csv, the SOCO rows of the thermal-tranche / bin-assignment
outputs (data/raw/reference/custom-bin-assignments.csv rows for SOCO plants — append, never reorder).
FILES YOU MUST NOT TOUCH: any other region's rows; src/; the derive scripts themselves (if one needs a SOCO
branch, that is a src-adjacent change — STOP and route to SOCO-DESK); ScenarioConfig.
RUN, in this order, each its own commit: derive_campd_unit_outages.py --iso SOCO --years 2023 2024 2025 →
derive_thermal_tranches.py --iso SOCO → scripts/tag_mixed_plants.py → build_offer_curve_overrides.py.
GATES: window count > 0 in every CEMS state (AL, GA, MS); ZERO full-year fallbacks (a unit falling to the
fallback is reported BY UNIT with the reason); committed-% and tranche distributions summarised by class
against MISO's as a sanity band (report, NEVER tune — rule 1). Every output header cites source + method +
the CEMS vintage.
SOCO DELTAS, ruled and binding:
 - CEMS COVERAGE IS 91.6 % OF FOSSIL MW, not 100 % (FINDING-soco-10). State the uncovered 8.4 % by plant
   and class in the FINDING; do NOT pad it, do NOT infer a window for it (rule 13).
 - THE CAES UNIT IS SETTLED — card S7: McIntosh (plant 7063) is a 25 MW gas CT at its real rating, not the
   110 MW nameplate, and the storage loader already skips it (SOCO-20 §4). Bin it as a CT. Do not re-open.
 - TWO TIMEZONES (gate G19, CLOSED by SOCO-10): the committed convention is America/Chicago, DST-aware,
   hour-ending. AL/MS are Central and GA is Eastern in the real footprint; the convention is already chosen
   and you INHERIT it — every window you emit states its timezone, and you never re-decide it.
 - Vogtle 3 (COD 2023-07) and Vogtle 4 (2024-04) come online mid-window. Their availability is a COD, not
   an outage: SOCO-15's repair handles the online mask. Do not emit an "outage" for a unit that did not
   exist yet — that is the phantom SOCO-15 removed.
RULES THAT BITE: 13 [R-MEASURED], 14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (nothing re-derives against a
residual — there is no residual yet, SOCO has never been solved), 27 [R-PUSH] (CSV outputs by git push;
SHA/row counts in the FINDING), 28 [R-MECH-MATRIX] (no cell moves — you arm nothing).
EXIT: docs/handoffs/FINDING-soco-30-<date>.md (windows per state-year, units covered %, the uncovered-MW
list, fallback list, class summaries), ending with a `## Log entry` block in the format the other SOCO
FINDINGs use — the desk appends it VERBATIM to docs/calibration-log/soco.md and cannot write it for you;
plan §5 row → LANDED. Report to the owner: coverage % by state first.
```

#### SOCO-31 `[OPUS]` — the scoring benchmarks, on the NO-PRICE branch

```
You are lane SOCO-31. MODEL: Opus claude-opus-5 — execution on committed inputs. DATA PROFILE: soco.
Branch stem: claude/soco-31-benchmarks-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md §5 row SOCO-31, §7 G6,
G9, G17, and §3 card S2 (the price ruling); scripts/data/build_calibration_reference.py,
derive_actual_tail.py, derive_actual_amplitude.py, scripts/audit_eia923_completeness.py;
docs/calibration-determination-rubric.md (what C1-C4 read) AND scripts/calibration_verdict.py's rubric
v3.8 header; FINDING-soco-13 (the price VERDICT) and FINDING-soco-22 (the v3.8 class SOCO-13's NO created).

PRECONDITIONS: SOCO-20 LANDED. STOP if not.
**THE DEFINING CONSTRAINT — READ THIS BEFORE ANYTHING ELSE. SOCO HAS NO PRICE BENCHMARK AND YOU WILL NOT
BUILD ONE.** Southern Company publishes no LMP and never will; SEEM publishes matched volumes, no price.
SOCO-13 built the FERC-EQR index behind a pre-registered ex-ante STOP gate and the gate read **NO** —
three of five gates failed (D2.2 every year at 3.66/2.69/2.64 % against a ≥ 5 % bar; D3.1 +54.2/+72.1 % in
2024/25 against ±15 %; D4.2 in 2025) and NO BAR MOVED AFTER THE SERIES WAS SEEN. Therefore:
 - `data/raw/_validation-source/actual_lmp.json` gets **NO SOCO BLOCK**. Its ABSENCE is load-bearing: it is
   the key rubric v3.8 reads to classify SOCO as `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`. Adding an empty
   or placeholder SOCO block BREAKS the classifier. Leave the file's SOCO-shaped hole exactly as it is.
 - TAIL_THRESHOLD and amplitude: SOCO-20 SKIPPED all three tail/amplitude registrations deliberately. Keep
   them skipped. Do not register a threshold for a region with no price series.
 - **GATE G17 IS ABSOLUTE AND IT BINDS YOU**: you may NEVER substitute a neighbouring market's hub — not
   MISO-South, not a PJM or TVA proxy, not an EIA state average dressed as a price. If you find yourself
   reaching for one, STOP and route to SOCO-DESK. The desk has refused this twice and logged both refusals.
FILES YOU OWN: scripts/data/build_calibration_reference.py (SOCO in its region map, BA "SOCO", eGRID
BACODE "SOCO"), data/raw/_validation-source/SOCO_{2023,2024,2025}_renewable_capacity.csv,
calibration_reference.json (SOCO block ONLY), frontend/data/backcast/completeness/eia923_<yr>.json
(regenerated). ALSO YOURS, routed by SOCO-20 §7: `scripts/data/curate_demand_profile.MODEL_ISOS` gains SOCO.
FILES YOU MUST NOT TOUCH: actual_lmp.json (see above); any other region's block or row (your exit check is
that their content is BYTE-IDENTICAL); src/market_sim/.
GATE (zero-LP, first): SOCO rows exist in the shared eia_demand_profiles.parquet /
eia_generation_profiles.parquet that build_calibration_reference reads; if not, re-run convert_eia930.py and
prove every non-SOCO row byte-identical before proceeding.
BUILD: build_calibration_reference.py for SOCO 2023-2025 → audit_eia923_completeness.py. Target figures to
reconcile against (plan §2.1, FINDING-soco-10): demand 239.6 / 249.5 / 252.6 TWh; net EXPORT +10.16 / +10.81
/ +13.03 TWh — SOCO is a net exporter every year and the benchmark must show it; fuel TWh gas 129.6/126.1/
125.4, nuclear 52.4/63.0/64.2, coal 38.3/40.5/44.0, hydro 8.45/6.92/5.93, solar 8.36/10.14/9.98.
TWO MEASURED-DATA CONSTRAINTS YOU MUST STATE, NOT FIX (both already routed):
 - **R-i — SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in EIA-930 for 2023 and most of 2024.**
   `NG: PS`/`BAT`/`SNB`/`OES` are a taxonomy cut-over at 2024-07-15, and `NG: WAT` never goes negative
   before it (min +32 MW) — so PS charging was not folded into hydro, it was NOT REPORTED. This is a hard
   constraint on the **C1 `fuelmix`** benchmark, not a bug to fix and not a hole to fill. It must be stated
   on SOCO's first keeper's determination basis, so write it into your FINDING in the words you want quoted.
 - **R-h / the loader-seam spike screens**: SOCO NG: OIL 2023 (1 h) / 2024 (7 h) and the four ~70 GW NG: NG
   hours in 2025 (against a 36,336 MW gas fleet). Documented in FINDING-soco-10. **Propose NO new constant**
   — setting a threshold after seeing the outliers is a fitted threshold (rule 23). Report them.
RULES THAT BITE: 13 [R-MEASURED] (benchmarks are measured OUTCOMES used ONLY as the score, never as an
input), 14, 23, 27 (fetch-back verify anything ≥ 300 lines), 28 (no cell moves).
EXIT: docs/handoffs/FINDING-soco-31-<date>.md with the SOCO benchmark table (per year: load TWh, gen by
class TWh, net interchange) and the json-diff proof that no other region moved; a section headed "what
cannot be scored and why" carrying the price posture and R-i verbatim; and a `## Log entry` block in the
format the other SOCO FINDINGs use — the desk appends it VERBATIM and cannot write it for you. Plan §5 row
→ LANDED. Report to the owner: the benchmark table, then the unscorable list.
```

#### SOCO-32 `[OPUS]` — zonal shares + per-zone SOLAR shape + zonal gas hub

```
You are lane SOCO-32. MODEL: Opus claude-opus-5 — the data-intake skill's contract on committed inputs.
DATA PROFILE: soco.  Branch stem: claude/soco-32-zonal-solar-gas-<4 chars>.
Read CLAUDE.md freshly and in full; invoke the data-intake skill; docs/multi-iso/soco-addition-plan-2026-09.md
§5 row SOCO-32, §2.5 (the FERC-714 spine), §7 G8/G9/G17, **and §3 card S3 — READ THE RULING IN FULL BEFORE
YOU DERIVE ANYTHING**; docs/multi-iso/05-backcast-playbook.md §8.1, §8.3; scripts/data/curate_zonal_shares.py
(_MISO_SUBBA_ZONE_GROUPS as the shape), src/market_sim/data/fuel/hubs.py, src/market_sim/data/renewables.py;
FINDING-soco-11 (the FERC-714 respondent table and its falsifier), FINDING-soco-14 (the BA-membership
citations — and the documented NO), FINDING-soco-12 (the gas basis finding).

PRECONDITIONS: SOCO-20 and SOCO-11 and SOCO-14 LANDED. STOP if not.
**HARD PRECONDITION — CARD S3, RE-RULED BY THE OWNER AT r#5. THE ZONAL SHARES ARE THE FIVE FULLY-CITED
FERC-714 RESPONDENTS. SOUTHERN POWER (RESPONDENT 186) IS EXCLUDED.** Shares SOCO_AL 0.3510 / SOCO_GA 0.5842
/ SOCO_MS 0.0648; residual 3.03 / 2.92 / 1.26 % by year. SOCO-20 already registered exactly these.
WHY, so you do not "improve" it: the six-respondent set has a SMALLER residual (1.63 / 1.50 / **-0.03** %)
and the owner chose the five-set anyway, because SOCO-14 could cite 107 and 210 from primary sources and
returned a **documented NO on 186** — a cited basis beats a smaller residual (rule 1 `[R-STRUCT]`), and that
NEGATIVE 2025 value is the overshoot SOCO-11's PowerSouth+Tallahassee falsifier was built to detect. **Do
not rebuild the shares on six respondents. Do not tune the residual.** If you believe 186 belongs in, you
need the load-side citation SOCO-14 could not find — STOP and route to SOCO-DESK; the card returns to the
owner, it is not yours to re-decide.
FILES YOU OWN: scripts/data/curate_zonal_shares.py (SOCO branch + the SOCO respondent→zone grouping,
mirroring MISO's shape); the SOCO rows of the clean zonal-shares datatype; NEW
scripts/data/build_soco_solar_shape.py (**SOLAR, not wind** — SOCO has no wind worth shaping: the footprint's
wind is ~0 and forecast-mode derive_cf_profile on an all-zero wind series is already routed to W6/capx, not
you); data/raw/soco-solar-shape/soco_{2023,2024,2025}_solar_zone_shape.parquet + README/SOURCES;
data/raw/soco_zonal_gas_hub.csv per SOCO-12's basis finding (MISO's csv schema) + SOURCES;
src/market_sim/data/fuel/hubs.py (SOCO wiring — extend the registry, **NO if-iso ladder**);
src/market_sim/data/renewables.py (SOCO membership in the zone-shape region set); tests under
tests/curation and tests/unit/data for the new SOCO paths (tmp-CLEAN_DIR fixtures — never a raw path CI
does not sparse-checkout, G17).
FILES YOU MUST NOT TOUCH: ScenarioConfig (no field; G8); results/cache.py; any other region's rows.
GATES: zonal shares sum to 1.0 every hour; the redistribution identity holds to 1e-9; solar shapes reconcile
to the EIA-930 SOCO aggregate within the builder's documented tolerance — **level never pinned** (rule 13);
the hub csv has 36 rows per zone-month set. G-DRIFT: in the FINDING, classify EVERY hunk you add to
renewables.py and hubs.py as INERT for each of the other EIGHT regions with the reason (SOCO-keyed branch /
registry entry), and re-run tests/regression/test_persisted_identity.py.
SOCO DELTAS: shares come from FERC-714 (§2.5) — **there is no EIA-930 sub-BA product for SOCO**, so do not
go looking for one; the three zones are geographic (AL/GA/MS) and the plant→zone lookup SOCO-20 registered
resolves 413 plants (GA 299 / AL 97 / MS 17) with plant 67241 (MA) REJECTED. The CC pmax reconciliation
warnings on plants 6073 / 7897 / 55382 / 57037 are yours to report, not to silence.
RULES THAT BITE: 2 [R-VECTOR] (no hour loops — numpy over the parquet), 5 [R-NO-MAGIC], 13, 14, 23, 24
[R-REGISTRY], 25 [R-ISO-SCOPE], 27 (renewables.py and hubs.py are ≥ 300 lines — Edit tool, fetch-back
verify), 28 (no cell moves — you arm no mechanism; shape membership is an INPUT, not a lever).
EXIT: docs/handoffs/FINDING-soco-32-<date>.md (share table by zone-year WITH the five-respondent basis and
its residual quoted, solar-shape reconciliation stats, hub provenance, the G-DRIFT table) ending with a
`## Log entry` block in the format the other SOCO FINDINGs use — the desk appends it VERBATIM and cannot
write it for you; plan §5 row → LANDED.
```

#### SOCO-33 `[OPUS]` — seam numbers (derive only, no arming)

```
You are lane SOCO-33. MODEL: Opus claude-opus-5 — derive only; you arm nothing. DATA PROFILE: soco.
Branch stem: claude/soco-33-seam-derive-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md §5 row SOCO-33 and §3
card S4 (the seam ruling); scripts/data/derive_neighbor_hr_by_year.py and derive_neighbor_hr_elasticity.py;
src/market_sim/model/interchange/spec.py INTERFACE_NEIGHBORS["SOCO"] as SOCO-20 registered it (default-off);
FINDING-soco-11 (the SOCO DIBA interchange series, confirmed to the charter within 0.001 TWh).
PRECONDITIONS: SOCO-20 and SOCO-11 LANDED.
CARD S4 AS RULED: the first keeper uses **served, MEASURED EIA-930 `Total interchange`**. You DERIVE the
numbers; a later lane arms them. SOCO is a **net exporter every year** (+10.16 / +10.81 / +13.03 TWh) — a
seam derive that comes out net-importing is wrong, and that is your first sanity check.
FILES YOU OWN: the derive outputs for --iso SOCO, data/raw/reference/soco_seam_*.csv (hr_by_year,
elasticity, DIBA duration-curve summaries) + SOURCES. FILES YOU MUST NOT TOUCH: interchange/spec.py (a later
lane arms what you derive); any neighbour's side of a seam (rule 25 — TVA's, MISO-South's and the
Southeastern utilities' objects are theirs); ScenarioConfig.
RUN: derive_neighbor_hr_by_year.py --iso SOCO --years 2023 2024 2025; the elasticity derive; the SOCO
net-interchange duration curves per DIBA per year **with the sign convention stated explicitly** (SOCO's
two-timezone footprint makes an unstated convention a silent error — gate G19).
**GATE G17 BINDS YOU TOO**: SOCO has no price series (SOCO-13 read NO). A neighbour-heat-rate derive that
requires a SOCO price is not available to you — if the producer demands one, STOP and route to SOCO-DESK
rather than substituting a neighbouring hub. Derive what the measured interchange supports and say plainly
what it does not.
RULES THAT BITE: 13, 23, 25 (SOCO's numbers from SOCO's data; nothing mirrored from another region's fitted
seam), 27, 28 (no cell moves).
EXIT: docs/handoffs/FINDING-soco-33-<date>.md with the hr_by_year table and the duration summaries, labelled
"for a later lane to arm", plus a `## Log entry` block in the format the other SOCO FINDINGs use — the desk
appends it VERBATIM and cannot write it for you; plan §5 row → LANDED.
```

#### SOCO-34 `[OPUS]` — codebase-site + docs prose + the log header

```
You are lane SOCO-34. MODEL: Opus claude-opus-5 — execution. DATA PROFILE: code.
Branch stem: claude/soco-34-site-docs-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/soco-addition-plan-2026-09.md §5 row SOCO-34 and the
§8 W3 SOCO-34 delta (it lists your owed items by file and line); docs/codebase-site/js/iso-configs-table.js,
viz-iso-topology.js, css/site.css (the data-iso tab rules), data/iso-topologies.json, forecast-runs.html
(ISO_ORDER), data-completeness.html; scripts/render_data_dictionary.py; docs/codebase/08-config-reference.md;
docs/README.md; index.html; docs/handoffs/FINDING-nwpp-35-2026-09-14.md (the lane that swept this surface to
nine regions the day SOCO registered, and cited what it left you).
PRECONDITIONS: SOCO-20 LANDED — get_iso_config("SOCO") drives iso-topologies.json.
**THE COUNT IS NINE, NOT EIGHT.** NWPP registered the same day and took the eighth slot; SOCO is the NINTH.
**NWPP-35 ALREADY SWEPT THE SHARED PROSE TO NINE and correctly did NOT serialize SOCO (rule 25). It cited
the debt in the artifacts — these four are yours:**
 (a) `docs/codebase-site/data/iso-topologies.json` — SOCO's block. Its keys are currently the eight WITHOUT
     SOCO, and its `_meta.description` says so verbatim: *"eight are serialized here. SOCO registered the
     same day as NWPP and its block is owed by the SOCO desk's own site lane, not by this one."* Regenerate
     SOCO's block from get_iso_config and UPDATE that description once it lands.
 (b) `docs/codebase-site/data-completeness.html` ~L364 — SOCO's filter entry; the same debt is marked there
     in a code comment.
 (c) `docs/codebase-site/config-reference.html` ~L404 — reads "the **eight** serialized into
     iso-topologies.json render below"; becomes nine.
 (d) `docs/codebase-site/index.html` ~L297 reads "Nine regions, 47 zones (44 carry load), 58 transmission
     links". **CHECK whether 47 already counts SOCO's three zones — do not assume either way.** If it does
     not, the count is wrong in the other direction and you fix it. Report the arithmetic.
ALSO YOURS, routed by FINDING-soco-20 §7: `docs/multi-iso/README.md` nine-region prose;
`scripts/build_status.py` ISO_ORDER; `keeper_store`; `scripts/render_data_dictionary.py`. Add SOCO to every
hardcoded region list named in plan §5 row SOCO-34 (ISO_ORDER, ISO_COLORS/DESCRIPTIONS, isoOrder, the
`.tabs__tab[data-iso="SOCO"]` rule using `--iso-soco`, the ISOS array). Prove forecast-runs.html renders with
a region that has NO forecast runs. Regenerate the data dictionary. Update 08-config-reference.md's zone
table and per-region mechanism lists for SOCO.
**`docs/calibration-log/soco.md` ALREADY EXISTS AND CARRIES LANDED LOG ENTRIES — DO NOT CREATE OR CLOBBER
IT.** The SOCO desk created it at r#3 and has appended every lane's `## Log entry` verbatim since. Your job
is the HEADER ONLY (match docs/calibration-log/miso.md's format) plus the "Next shorthand" line. Any edit
that removes an existing entry is a stop-the-line event.
FILES YOU MUST NOT TOUCH: `scripts/ff_readiness_battery.py` GOLDEN_ISOS and anything under
frontend/data/forecast/ (W6, routed to the capx director as card S10); the mechanism-matrix shards
(SOCO-21's, LANDED); frontend/data/backcast/ (the first-solve lane's); ANY keeper shard;
`frontend/data/backcast/keepers/index.json` (the first-solve lane adds SOCO at registration, not you).
Run the accessibility-audit skill on every page touched; run sync-docs at the end.
RULES THAT BITE: 15 [R-DASHBOARD] (dashboard text is GENERATED from sidecars — never hand-write a status),
25 [R-ISO-SCOPE], 26 [R-DELETE], 27 (several ≥ 300-line files — Edit tool, fetch-back verify), 28 (no cell
moves).
EXIT: docs/handoffs/FINDING-soco-34-<date>.md (file → change table, the index.html zone arithmetic, the
accessibility-audit output), ending with a `## Log entry` block in the format the other SOCO FINDINGs use —
the desk appends it VERBATIM to the log and cannot write it for you; plan §5 row → LANDED.
```

### W4 issuance r#9 (2026-09-16, pinned `a2dc6d3a`) — the first-ever SOCO solve

Issued against SPP's committed W4 charter (`docs/multi-iso/spp-addition-plan-2026-09.md` §8, SPP-40
L1257) with the SOCO deltas §8's W3–W6 bullet already carries, **plus four corrections SPP-40's text
cannot carry because they postdate it**: (i) `--commitment` is an ARCHIVED P2 flag and now **errors**
without `--enable-legacy-p2` (`run_calibration_full.py:9014`) — SOCO-40 never passes either; (ii) rules
32–35 landed 2026-09-09/12, so the lane is an **orchestrator that never solves** and every solve goes to
a shard that **pushes its bundle**; (iii) the determination class is rubric **v3.8**'s no-price branch,
which did not exist when SPP-40 was written; (iv) SOCO's zonal shares are the **five**-respondent set.

#### SOCO-40 `[FABLE]` — phase 0, the rule-29 screen, the 2023–2025 bundle, the first keeper

```
You are lane SOCO-40. MODEL: Fable claude-fable-5-1 — the first-ever SOCO solve is a novel object:
kill-grading its screen, writing its attestation and DOF ledger, and promoting the first keeper of a
region with NO PRICE BENCHMARK are determination consequences, not execution.
DATA PROFILE: soco.  Branch stem: claude/soco-40-first-keeper-<4 chars>.  Pin: origin/main a2dc6d3a.

Read CLAUDE.md freshly and IN FULL — rules 1 [R-STRUCT], 12 [R-PARALLEL], 13 [R-MEASURED],
15 [R-DASHBOARD], 16 [R-ALLYEARS], 20 [R-FORCED-BUDGET], 21 [R-DOF], 22 [R-C3C], 29 [R-SCREEN],
31 [R-RETAIN], 32 [R-SHARD], 33 [R-SHARD-ARCHIVE], 34 [R-SHARD-PROMOTABLE] and 35 [R-PROMOTE] each
bind specific lines below. Then: docs/multi-iso/soco-addition-plan-2026-09.md §1, §3 cards S2/S3/S4/
S5/S6/S7/S12, §5 row SOCO-40, §7 gates G4 G5 G6 G13 G17 G19 G20 G21; docs/multi-iso/05-backcast-
playbook.md §6; FINDING-soco-30/31/32/33 (all four; 30/31/33 are on main, 32 lands before you start);
FINDING-soco-13 (the price VERDICT) and FINDING-soco-22 (the v3.8 class it created);
docs/calibration-determination-rubric.md AND scripts/calibration_verdict.py's rubric v3.8 header;
scripts/run_calibration_full.py --help; the calibration-report skill; scripts/build_status.py,
dashboard_add_run.py, check_registry_payload_parity.py; frontend/data/backcast/keepers/README.md
(promotion protocol) and keepers/SPP.json (the shard shape a new region's first keeper takes);
docs/calibration-log/soco.md (your format — twelve entries, newest last) and one recent
PRECOMMIT-*.md for the PRECOMMIT form.

PRECONDITIONS — `git log origin/main --grep=SOCO-32`; STOP AND REPORT if unmet:
SOCO-30 LANDED (outages + tranches), SOCO-31 LANDED (benchmarks), **SOCO-32 LANDED** (zonal shares,
solar shape, gas hub). All three are gate G4. SOCO-33 is NOT a precondition — card S4 ruled the first
keeper's seams SERVED, not priced. SOCO-34 is NOT a precondition — it is site prose; if it has not
merged, say so in your FINDING and register anyway.
Ask SOCO-DESK whether another per-plant solve is running before you launch (rule 12).

**THE DEFINING CONSTRAINT — READ IT BEFORE YOU PLAN ANYTHING. SOCO HAS NO PRICE BENCHMARK, YOU WILL
NOT BUILD ONE, AND THE ABSENCE IS LOAD-BEARING.** Southern Company publishes no LMP and never will;
SEEM publishes matched volumes, no price. SOCO-13 built a FERC-EQR candidate behind a STOP gate
pre-registered before any data was read and the gate read **NO** — three of five failed and no bar
moved after the series was seen. Therefore:
 - `data/raw/_validation-source/actual_lmp.json` HAS NO SOCO BLOCK and MUST NOT GAIN ONE. Its absence
   is the key `calibration_verdict._price_reference_absent("SOCO")` reads. **An empty or placeholder
   block BREAKS the classifier.** Verified on main at issuance: the file's top-level keys are the
   seven price-carrying ISOs and the string `SOCO` appears nowhere in it. Leave it exactly so.
 - Your determination is rubric v3.8's `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` or
   `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`. **It may NEVER read `CALIBRATED`**, whatever
   the run does. You are scored on **C1 / C2 / C4 / C6 / C8**. C3a / C3b / C3c are **UNSCORABLE, NOT
   FAILED** — do not report them as failures and do not let them consume a caveat slot.
 - **GATE G17 IS ABSOLUTE.** You may never substitute a neighbouring market's hub — not MISO-South,
   not a TVA or PJM proxy, not an EIA state average, not a cost-stack "price" of your own. If you find
   yourself reaching for one, STOP and route to SOCO-DESK. The desk has refused this three times and
   logged every refusal.
 - TAIL_THRESHOLD and amplitude stay SKIPPED (gate G6's pre-specified branch, card S9 n/a). SOCO-31
   verified the skip BY EXECUTION — both derives emit zero SOCO rows. Do not register a threshold.

**RULE 32 [R-SHARD]: YOU ARE AN ORCHESTRATOR AND YOU NEVER RUN AN LP.** Not in the foreground, not
under nohup, not "just the smoke". Phase-0 census, the PRECOMMIT, composition, scoring and
registration are YOURS and are zero-LP. Every solve goes to a shard launched with
`create_session`, and every shard prompt carries, or the shard is wasted:
 1. `source_revision` = a **FULL 40-CHARACTER SHA** you pushed and pinned — never a branch name;
    "`git rev-parse HEAD` must equal <sha>" is the shard's first hard stop. The shard NEVER rebases,
    NEVER `git pull`s, NEVER "syncs".
 2. `source_url` = this repo; the prompt names `DATA PROFILE: soco`.
 3. Its own `--out-dir`, its own branch, and it commits ONLY its own bundle path
    (`git add .gitignore && git add <out-dir>`, then `git status --short` showing nothing outside it).
 4. **RULE 34(a): THE SHARD PUSHES ITS BUNDLE — a prompt telling it to gitignore or omit the bundle
    is a DEFECT IN THE PROMPT.** It appends a `.gitignore` **NEGATION** for its own out-dir
    (`printf '\n!results/calibration/<out-dir>/**\n' >> .gitignore`) and uses a **PLAIN `git add`,
    NEVER `git add -f`** (the `-f` form is what the auto-mode classifier refuses, and that refusal
    hardened a shard's permission state in miso-255). The bundle MUST include
    `dispatch/<year>_P1.parquet` or registration raises `FileNotFoundError`. **This applies to the
    SCREEN shard too** (rule 34(b): you cannot know a screen is only a screen until the owner rules).
 5. Hard stops the shard can check itself: the pinned SHA; `get_iso_config("SOCO")` resolving with
    three zones on shares **0.3510 / 0.5842 / 0.0648**; **no `--commitment`, no `--enable-legacy-p2`,
    no `--run-p2`** anywhere in its command line. A shard that sees otherwise STOPS and does not push.
 6. What to REPORT in numbers in its final message — the parent may never read its disk — including
    the `container preflight:` and `memory peak:` log lines the runner emits.
 7. FORBID BY NAME: `git add -A`, `git add .`; `dashboard_add_run.py`, `build_manifest.py`,
    `build_status.py`, `prune_iso_runs.py`, anything under `frontend/data/backcast/**`; any edit under
    `src/` or `scripts/`; opening a PR; deleting any result (rule 31).
 8. Put this sentence in the prompt: "A shard that stops with a clear report is a SUCCESS; a shard
    that repairs infrastructure is a FAILURE."
 9. Memory: the shard runs the runner UNMODIFIED, never passes `--no-container-preflight`, and names
    no memory recipe of its own — `ensure_solve_container` does the cgroup read and the swapfile.

FILES YOU OWN: `results/calibration/soco40_baseline_B/` (+ `hourly/` sidecars);
`frontend/data/backcast/registry/<id>.json` + `runs/<id>.js`; `keepers/SOCO.json` (**NEW** — this
region has no keeper shard yet); `keepers/index.json` (**+ "SOCO"** — SOCO-34's charter explicitly
leaves this line to you; rebase last, and note NWPP is also absent, which is NOT yours to add);
`status/SOCO.js` (generated by `build_status.py --iso SOCO`); `bench/SOCO/<yr>.json.gz`;
`docs/codebase-site/data/mechanism-matrix/SOCO.js` (keeper + gates stamp — the LAST commit, after the
final rebase); `docs/calibration-log/soco.md` (your `## Log entry`, appended by the DESK — you write
it into your FINDING, you do not edit the log); `docs/handoffs/PRECOMMIT-soco-40-<date>.md` and
`FINDING-soco-40-<date>.md`.
FILES YOU MUST NOT TOUCH: `actual_lmp.json` (above); any other region's shard / status / bench / log /
keeper file (rule 25); `frontend/data/forecast/**` and `ff_readiness_battery.py` (W6, the capx
director's — card S10); `ScenarioConfig` defaults; `offer_curve_by_group` bands — **every SOCO band
stays 1.0 and this keeper declares NO authorized price tuning**. SOCO-30 already proved that
satisfiable: `build_offer_curve_overrides --iso SOCO --list` reads 1.0 on
committed/econ_low/econ_high/peak for all 13 classes, no `phys_*` rows, delta JSON `{}`.
Gate G5 note: SOCO is a **cost-based BA that takes no offers**, so a band ≠ 1.0 would need a far
stronger story than an RTO's. The desk's posture is bands stay 1.0 unless the OWNER rules otherwise.

DO, IN THIS ORDER:

(0) **PHASE 0 — ZERO-LP, IN THIS SESSION.** Fleet census (plants, MW by class, CHP hosts removed),
    zone census (three zones carrying load, shares summing to 1.0), offer-array census, and the
    served-interchange census. **Reconcile one inconsistency the desk found and did not resolve for
    you, because you are the lane that measures it**: `run_isos_concurrent.py:151` registers
    `IsoMemoryClass("SOCO", peak_gb=6.0, per_plant=True, co_opt=False)`, while `plant_level_fleet`
    defaults **False** and is not set in `_soco_config`, and SOCO is **absent** from
    `CAMPD_BINNING_ISOS` (`{ERCOT, CAISO, NEISO, NYISO, PJM, MISO}`). State which fleet path your
    solve actually takes, measured by calling the code — not inferred from either registry. If they
    disagree, that is a FINDING and a route, never a silent fix. (SOCO's absence from
    `CAMPD_BINNING_ISOS` is the NORM for a new region — NWPP's own ISOConfig docstring records the
    identical posture under owner ruling N8, and SPP is absent too. Do not add SOCO to it: that is
    `src/`, a declared solve-surface value, a gate-G8 cache-key move, and not this lane's call.)
    Fix structural absurdities (a class with no units, a zone with no load) by ROUTING to the owning
    lane — never by tuning.
    **WRITE AND PUSH `PRECOMMIT-soco-40-<date>.md` BEFORE ANY SOLVE.** It states:
      (a) **THE PRICE POSTURE, BEFORE THE SOLVE** — the v3.8 class, the criteria scored, that
          `CALIBRATED` is unreachable, and that the price gap is reported at FULL MAGNITUDE on the
          determination basis rather than treated as absent.
      (b) **THE SCREEN YEAR, NAMED BEFORE THE SCREEN RUNS, ON A STRUCTURAL CRITERION AND NEVER ON A
          RESIDUAL** — there is no residual: SOCO has never been solved. The criterion is *the year
          that exercises the most novel objects at once on the cleanest measured input*. The desk's
          own reading, which you may override in the PRECOMMIT with your phase-0 reason, is **2024**:
          it carries the span's winter peak (47,368 MW), has both Vogtle units in service for three
          quarters of it, and its EIA-930 balance identity `NG − D − TI` is **exactly zero in every
          hour** — where 2025 has 633 nonzero hours, a −0.6963 TWh residual, a one-hour partial post
          at `min_mw` 12,638 MW, and an incomplete peaker census (SOCO-31 §4.3–§4.5). Screening on
          2025 risks grading a data artifact as a structural failure.
      (c) **THE STRUCTURAL STOP GATE**, pre-registered and falsifiable: the served export is served
          (SOCO is a net EXPORTER every year — +10.16 / +10.81 / +13.03 TWh — and a run that comes out
          net-importing is wrong); no unserved energy outside a stated tolerance; no negative-price
          absurdity; fuel classes within an order of magnitude of SOCO-31's committed benchmark;
          Vogtle 3 and 4 OFF before their CODs (2023-07 and 2024-04) and ON after. **It may kill the
          arm; it may never promote one, and it never reads a residual** (rule 29).
      (d) Wall-clock and peak-GB to be measured; and the statement **"control = none; this bundle
          becomes the rule-29(b) control for every later SOCO lane."**
(1) **SCREEN — ONE SHARD, ONE YEAR** (rule 29(a)), out-dir `results/calibration/_soco40_screen`,
    pushed to its own branch per rule 34. Grade against the STOP gate ONLY. **A kill is the session's
    RESULT and the remaining years are never spent** — report and stop.
(2) **FULL SPAN — ONE SHARD, ONE `--year 2023 2024 2025` INVOCATION, ONE BUNDLE** (rules 16 + 32(b);
    years sequential inside it, rule 12), served interchange per card S4, out-dir
    `results/calibration/soco40_baseline_B`. **Slim per-year fan-out is BANNED** — it cannot be
    recomposed and always ends in a re-solve. Generate `legitimacy_diagnostics.json` and
    `calibration_attestation.json`: the DOF ledger names every free parameter with its identification
    source (**expected: zero residual-identified values**), and `authorized_price_tuning` is declared
    **NONE** — C6 FAILS without the declaration even when the answer is none (gate G5).
    Score with `calibration_verdict.py` AFTER the final rebase.
(3) **REGISTER** (calibration-report skill / `dashboard_add_run.py`): id `2026-09-<dd>-soco-1-baseline`;
    `keepers/SOCO.json` new, with every field `keepers/README.md` requires; `keepers/index.json`
    += "SOCO"; `build_status.py --iso SOCO`; bench parts; **`hourly/` sidecars committed** —
    `class_hourly_<year>.parquet`, `system_<year>.parquet` and `reserve_family_<year>.parquet`
    (rule 15), so later SOCO sessions read the keeper instead of replaying it.
    **Whatever the determination reads, it is the keeper, because it is the most structurally
    faithful SOCO run that exists** (rule 1) — and it is reported at full magnitude with every failing
    criterion named. **THE DETERMINATION BASIS MUST CARRY ALL FIVE OF THESE, in your own words:**
      - **the price gap** — no public SOCO price exists, C3a/C3b/C3c unscored, SOCO-13's NO cited;
      - **R-i** — SOCO's **1,306.6 MW of pumped storage is UNOBSERVABLE in EIA-930** for 2023
        (0 of 8,760 hours) and 99.7 % of 2024, and `NG: WAT` never goes negative before the
        2024-07-15 taxonomy cut-over, so PS charging was not folded into hydro, it was NOT REPORTED.
        A hard constraint on the **C1 `fuelmix`** benchmark — never a hole to fill;
      - **card S3's exclusion of Southern Power (respondent 186)** from the zonal shares, and the
        residual it leaves (3.03 / 2.92 / 1.26 %);
      - **card S12 / SOCO-15's COD bias**, whose floor stands regardless of outcome;
      - **R-v** — 2025 carries no `eia923_incomplete` flag (ratio 0.9533) but its peaker census does
        not: 6 of 23 `CT_PEAKER` plants and 1 of 6 `CC_CHP` have filed, so no SOCO pair is
        gate-eligible and a 2025 gas-split comparison defers to EIA-930.
    Stamp the SOCO matrix shard (keeper id + open gates) as the LAST commit.
(4) **GATES BEFORE PUSH**, all exit 0: `audit_keepers.py --check` (**E1 and E13** — E13 is rule 35(f)'s
    invariant and you are its first SOCO test), `check_registry_payload_parity.py`,
    `check_mechanism_matrix.py`, `check_bench_freshness.py`, `check_golden_manifest.py`; then the
    `calibration-keeper-auditor` agent `--iso SOCO`.
    **Two of these are RED on `main` for reasons that are not yours** and you must not read them as
    your own regression or try to fix them: `check_gate_a_provenance` (NYISO + SPP superseded markers)
    and `check_registry_payload_parity`, whose two unmapped dirs are CAISO's
    `caiso279_ablate_dswcouple_span` **and SOCO's own `soco15_spp_arm`** — the latter is a SOCO-15
    bundle that reached `main`, is routed as desk item **R-p**, and is **awaiting the owner's
    retention ruling**. DO NOT DELETE IT (rule 31 [R-RETAIN]). Report the gate's exit with the
    unmapped list named, and say which entries are pre-existing.

SOCO DELTAS, ruled and binding — do not re-open any of these:
 - **Card S4**: seams are the SERVED, MEASURED EIA-930 `Total interchange`. All eight priced
   `NeighborInterface` blocks are DEFAULT-OFF and inert until `reference_price_interface` is armed,
   which this keeper does not do. **SOCO-33 measured that seven of eight registered
   `interface_limit_mw` values would refuse 35.6 / 39.0 / 41.7 % of measured flow if armed** — that is
   lever SOCO-56's precondition (desk item R-t), it does NOT bite this keeper, and you state in one
   line that your run does not read those limits.
 - **Card S7**: McIntosh (plant 7063) is a **25 MW gas CT**, not the 110 MW nameplate, and the storage
   loader already skips it. Settled.
 - **Card S5**: VOLL is the DOE/LBNL ICE value SOCO-20 registered (61,900 $/MWh), not $2,000.
 - **Card S6**: adequacy is the **winter 26.0 %** scalar with the misalignment documented.
 - **Gate G19**: two timezones, one clock — `America/Chicago`, DST-aware, hour-ending. Inherited from
   SOCO-10, verified by SOCO-33's shift test. Every series you emit states its clock; you never
   re-decide it.
 - **No capacity market, no import node, no AS design** — `reserves.spec` refuses SOCO by name, and
   `build_import_generators("SOCO") == []`. A reserve or capacity result for SOCO is a bug, not a
   finding.
 - **Year set**: 2023–2025 IS the union today, so rule 35(c) is satisfied trivially and there is no
   outgoing keeper to prune (rule 35(a) is a no-op for a first keeper). If manifest row 9 (holdout
   2019–2022) has landed by the time you run, **every** batch covers the union — one shard per year,
   rule 34(c) — and an unstamped year drops off the report silently (rule 30(a)).

**RULE 31 [R-RETAIN] — THE PROMOTION QUESTION IS ASKED IN-SESSION, WHILE THE BUNDLES ARE ALIVE.**
Before you archive any shard: verify retrievability with `git ls-tree -r <shard sha> -- <bundle path>`
and require **more than zero files** (rule 34(d)); zero means the bytes are on an ephemeral container
and the honest report is *not promotable without a re-solve, cost stated*. Record recovery by **full
40-char SHA, never a branch name** (rule 33(d)). Archive each shard only once you have fetched,
checked out and VERIFIED its bundle (rule 33(a)), never while it is running, and sweep before you
finish (33(e)). **Never delete a result** — not the screen bundle, not a control — until the owner has
ruled; `.gitignore` in YOUR tree, never `rm`, is what discharges rule 29(c). State in the RESULT where
each bundle is and what a promotion would cost from that state (34(e)).

RULES THAT BITE: 1 [R-STRUCT] (a keeper for STRUCTURE, never for MAE — and there is no price MAE here
at all), 12, 13, 15, 16, 20 [R-FORCED-BUDGET] (report C8 by class), 21 [R-DOF], 27 [R-PUSH] (the run
payload is ≥ 457 KB → **`git push`, never `push_files`**; hash-verify the sidecar), 28 [R-MECH-MATRIX]
(stamp SOCO's shard ONLY), 29, 31, 32, 33, 34, 35.

EXIT: the registered keeper visible at `docs/codebase-site/backcast-runs.html#iso=SOCO`;
`docs/handoffs/FINDING-soco-40-<date>.md` carrying the determination, the per-criterion table (with
C3a/C3b/C3c marked UNSCORABLE, not failed), the STOP-gate table, the DOF ledger, wall-clock and
peak-GB, the shard retrievability line, and a recommendation (not a change) re-ordering the §5 lever
queue by what this bundle showed; plan §5 row → LANDED; plan §1 rows ticked. The FINDING ends with a
`## Log entry` block in the format the twelve entries in `docs/calibration-log/soco.md` use — **the
desk appends it VERBATIM and cannot write it for you.**
Report to the owner: the determination and the criterion table FIRST, then the promotion question.
```


#### SOCO-40 ADDENDUM `[FABLE]` — issued r#10 (2026-09-16, main `680d1d82`), to be pasted BENEATH the charter above

```
ADDENDUM to lane SOCO-40, issued after SOCO-32 landed. Everything in the charter above stands; these
four items are added or corrected. Read them before you write your PRECOMMIT.

(1) **GATE G4 IS NOW FULLY DISCHARGED — the charter's PRECONDITION block is satisfied.** SOCO-30, SOCO-31
    AND SOCO-32 are all on main (PRs #6179/#6181, #6185, #6205/#6208). Verify it yourself anyway —
    `git log origin/main --grep=SOCO-32` — and STOP if you cannot. SOCO-34 also landed (PR #6191), so
    the charter's "if it has not merged, register anyway" clause is moot.

(2) **A SIXTH LINE FOR THE DETERMINATION BASIS — SOCO `NG: OIL` IS A RULE-14 FALSE POSITIVE ALREADY IN
    YOUR BENCHMARK.** The EIA-930 `NG:` unit-slip screen DELETES a real SOCO cold-snap oil run:
    2024-01-17 03:00-09:00, Winter Storm Heather — 155 -> 530 -> 660 -> 762 -> 801 -> 350 MW of
    `NG: OIL`, a coherent peaker start, ramp and shutdown tracking SOCO's winter peak hour for hour,
    whose 07:00 hour IS the 47,368 MW BA winter peak this program has quoted since the charter. 801 MW
    against 47,123 MW of net generation is entirely possible. The screen fires only because a
    near-zero-baseline series has no operating scale — median 0.0 MW, p99.9 71.7 MW — so its robust
    peak is meaningless. **SOCO 2024 `NG: OIL` reads 0.0056 -> 0.0012 TWh: 4.4 GWh of real generation
    deleted.** Found and published by NWPP-37 (`e1e8d809`, `FINDING-nwpp-37-2026-09-16.md` §6), which
    censused the two regions SPP-41 could not.
    **What this means for you, precisely:** your C1 `fuelmix` oil benchmark is biased LOW in 2023-24,
    and a model that dispatches that oil correctly will score as over-generating oil against it. **State
    it on the determination basis; do NOT correct the benchmark, do NOT exclude the hours, and do NOT
    tune anything toward or away from it** (rules 13 and 1). It is pre-existing, it is not yours to fix
    — a repair needs a floor on the anchor or a minimum-baseline eligibility test and both change the
    statistic — and it is routed as desk item R-w.
    **The contrast matters and you should not generalise from it:** the SOCO `NG: NG` flags are
    unambiguous and correct — 70,683 MW of gas in an hour whose entire net generation is 32,574 MW, four
    such hours in 2025. A single fuel cannot exceed the total. The screen is right there and wrong on
    oil; say which is which rather than distrusting the screen as a whole.

(3) **THE SHARD HARD-STOP SIGNATURE IS STILL `0.3510 / 0.5842 / 0.0648` AND IT STAYS — BUT KNOW WHAT
    OBJECT YOU JUST VERIFIED.** Since SOCO-32 landed, those are the STATIC FLEET-MW FALLBACK in
    `_soco_config`, which fires only if the clean parquet AND the raw file are both absent. The
    operative hourly shares are the MEASURED ones: **0.2978 / 0.6442 / 0.0580** (three-year mean;
    per-year AL 0.3022/0.2974/0.2939, GA 0.6382/0.6450/0.6493, MS 0.0596/0.0576/0.0568). Keep the hard
    stop — it is a cheap config-identity check and it is still literally correct — and report BOTH in
    your phase-0 census, so nobody reads the fallback as the share your solve used. Re-keying the static
    value is desk item R-x(2) and is NOT yours.

(4) **YOUR BENCHMARK IS NOT STALE, and here is the proof so you do not spend a phase-0 check on it.**
    NWPP-37 moved the `NG:` screen from three per-reader call sites to the frame constructors in the
    same window SOCO-31 landed. `build_calibration_reference`'s own output is **byte-identical** — its
    per-member screen and the new placement agree — so SOCO-31's `calibration_reference.json` block
    stands and no registered keeper's C1/C4 moves. The one SOCO series that moved is
    `measured_gas_floor_profile` (2025 `gas_floor` -19,759 MWh), and **no SOCO solve path reads it
    today**. If your own census disagrees with any of that, STOP and route it — do not reconcile it
    quietly.
```

---

## 9. Findings index

| Lane | FINDING | Landed |
|---|---|---|
| charter | this plan + `docs/handoffs/soco-desk-handoff-2026-09-12.md` + `soco-desk-ledger-2026-09.md` | 2026-09-12 |
| SOCO-10 | `docs/handoffs/FINDING-soco-10-2026-09-13.md` + `docs/multi-iso/soco-data-audit.md` — census 336/788/**70,667.2 MW**, MA rejected / FL kept, **gate G19 CLOSED** (`America/Chicago`, DST-aware, hour-ending), CEMS gap **91.6 %** of fossil MW, and the **card S12 COD defect** | 2026-09-13 (PR #6091) |
| SOCO-11 | `docs/handoffs/FINDING-soco-11-2026-09-13.md` — 8/8 CEMS AL/GA landed schema-equal to `MS_2024`; **FERC-714 reconciliation gate FAILED at 73.2 %**, nothing rescaled; interchange confirms the charter to 0.001 TWh | 2026-09-13 (PR #6083) |
| SOCO-13 | `FINDING-soco-13-2026-09-13.md` + `PRECOMMIT-…` — **VERDICT NO**; D2.2 fails every year (3.66 / 2.69 / 2.64 % vs ≥ 5 %), D3.1 fails 2024/25 (+54.2 / +72.1 % vs ±15 %), D4.2 fails 2025; **no bar moved after the series was seen**, nothing landed to `_validation-source`, G17 intact | 2026-09-14 (PR #6129) |
| SOCO-20 | `docs/handoffs/FINDING-soco-20-2026-09-14.md` + `PRECOMMIT-soco-20-2026-09-14.md` — **SOCO REGISTERED AS THE NINTH REGION**; `_ISO_BUILDERS` + `DEMAND_LOADERS` + `SURFACE_ISOS` in ONE commit (gate G1), **G8 holds** (0 moved rows for all eight incumbents; seven keepers' `cache_key()` byte-identical), two seam repairs each proved a no-op for the seven, and the **`--rescope-from-parquet` non-additivity caught by the suite and repaired before push** — script defect ROUTED, not patched | 2026-09-14 (PR #6152) |
| SOCO-14 | `FINDING-soco-14-2026-09-13.md` — **gate G22 FAIL, 2 of 3 cited**: Oglethorpe and MEAG YES from primary sources, **Southern Power a documented NO**; card S3 returned and re-ruled to the five-respondent set | 2026-09-14 |
| SOCO-15 | `FINDING-soco-15-2026-09-13.md` + `PRECOMMIT-…` — the COD-seam repair on `main` (`9398000d`, PR #6127); **all three exit conditions MET**, eight-footprint A/B with both directions at full magnitude; **SOCO-20 CLEARED** | 2026-09-14 (PR #6135) |
| SOCO-21 | `FINDING-soco-21-2026-09-13.md` — the **eighth** matrix shard, one commit; 327 ids = 168 `U` + 159 `·`; keeper/gates empty by design, **no verdict minted** | 2026-09-14 |
| SOCO-22 | `FINDING-soco-22-2026-09-13.md` + `PRECOMMIT-…` — rubric **v3.8**; **all seven keepers re-score byte-identically** (the only diff on 54 verdict files is `rubric_version` 3.7 → 3.8, declared in the PRECOMMIT before the edit); `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, never `CALIBRATED`; **NWPP has already adopted it** | 2026-09-14 |
| SOCO-12 | `docs/handoffs/FINDING-soco-12-2026-09-13.md` — **gate G12 MET**; SEEM corrected (live **Nov 2022**; its **auditor** publishes a monthly price series; FERC settlement 2026-01-05 will oblige hourly posting); PRM 26 % W / 20 % S; NRC ×8; delivered gas | 2026-09-13 (PR #6092) |
| SOCO-31 | `docs/handoffs/FINDING-soco-31-2026-09-16.md` — **the scoring benchmarks; GATE G9 PASSES with the non-SOCO diff measured as EXACTLY ZERO** (eight regions byte-identical, 39/39 CSVs byte-identical, whole-file +295/−1 with the one deletion the `generated` stamp); SOCO 2023–2025 demand 229.47 / 238.70 / 239.56 TWh and a **net EXPORT of +10.16 / +10.81 / +13.03 TWh every year**; `actual_lmp.json` UNTOUCHED and the G6 skip **verified by execution** (both derives emit zero SOCO rows), G17 upheld; **R-i stated for the determination basis** — 1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930 for 2023 and 99.7 % of 2024 | 2026-09-16 |
| SOCO-30 | `docs/handoffs/FINDING-soco-30-2026-09-16.md` — **1,119 outage windows** over AL/GA/MS × 2023–25, six artifacts, no flag or constant changed; **gate G4 leg 1 PASS** (no state-year zero) and **leg 2 PASS** (8 full-year rows, ALL the `eia923_netzero` structural fallback, **zero measured full-year CEMS outages**); coverage re-measured **95.95 %** of the 50,004.8 MW CEMS-eligible fossil footprint and **the charter's 91.6 % premise corrected — it was the MISSING share before SOCO-11 landed AL/GA**; Vogtle emits zero rows; three defects routed | 2026-09-16 (PR #6179/#6181) |
| SOCO-33 | `docs/handoffs/FINDING-soco-33-2026-09-16.md` — the seam derive, six files, **derive only**. Net-EXPORTER sanity PASSES on both clocks (+10.156 / +10.807 / +13.032 TWh served; +10.155 / +10.832 / +13.039 summed over nine DIBA legs, every residual explained); **G19 sign convention VERIFIED by a shift test**, not asserted; **G17 never approached** — every anchor is the neighbour's own price on the neighbour's own side. **HEADLINE: seven of eight registered `interface_limit_mw` values are contradicted by SOCO's own meter** — arming them would refuse **35.6 / 39.0 / 41.7 %** of measured flow | 2026-09-16 (PR #6180) |
| SOCO-34 | `docs/handoffs/FINDING-soco-34-2026-09-16.md` — **LANDED, PR #6191.** SOCO wired into the site's nine-region surface; `index.html`'s 47 / 44 / 58 **checked rather than assumed and found already correct** (39+5+3, 36+5+3, 47+9+2), measured two independent ways; NWPP-35's four cited debts all discharged; the calibration-log header refreshed with **all nine existing entries intact** | 2026-09-16 (PR #6191) |
| SOCO-32 | `docs/handoffs/FINDING-soco-32-2026-09-16.md` — zonal load shares on the model clock (**AL 0.3022 / GA 0.6382 / MS 0.0596** in 2023; residual **3.03 / 2.92 / 1.18 %**, SOCO-11's five-respondent diagnostic reproduced independently); a NEW per-zone solar-shape builder on **measured all-sky irradiance at all 482 plant-years** reconciling to `NG: SUN` at **shift +0 h, r = 0.988 / 0.975 / 0.933** with **nothing pinned**; a 9-row zonal gas hub from per-plant EIA-923 with **no applier armed**; **G8 HOLDS — `solve_surface_register --diff` 0 moved / 0 added / 0 removed**, and 3 of 54 renewable-shape cells move, all `SOCO\|solar`; **card S3 honoured exactly** — the six-respondent set not rebuilt, not evaluated, not tuned toward; 51 new tests and **all 9 suite failures carrying same-tree controls**; **R-q ANSWERED with a measured refusal** | 2026-09-16 (PR #6205/#6208) |

## 10. Ledger

`docs/handoffs/soco-desk-ledger-2026-09.md` — live state, scoreboard, rulings, routed items,
collision register, issuance record, errors against interest.
