# PRECOMMIT — caiso-262: the CAISO 2022 validation touchpoint (rule 22 `[R-HOLDOUT]`), end to end

**Pushed BEFORE any measurement.** Session caiso-262, 2026-09-07, branch
`claude/caiso-262-backcast-2022-wnukdb`, off `main` `1ee2efba`. Keeper
**`2026-09-06-caiso-260-b1-demand`** (bundle `caiso260_demand_vintage`, sha
`e162147b`), DETERMINATION **CALIBRATED** (rubric v3.6) — **UNCHANGED by this
session, whatever 2022 says** (rule 30(c)).

---

## §0 — What this session is, and what it is not

**IS:** the data intake that closes H-2 (the 2022 scored RT hub price) plus the
four silent-fallback repairs S-1…S-4 and the H-1 demand artifact, and then ONE
rung — the frozen caiso-260 recipe replayed on 2022 under
`--holdout-authorized`, registered and **stamped to the keeper** (rule 30(a)).

**IS NOT:** a calibration session. There is **no rubric failure to tune**
(C1 12/12 free 8/8; C2 PASS; C3a +4.37/+8.89/+8.25 %; C3b 0.083/0.142/0.111;
C4 0.881/0.287, 0.912/0.260, 0.877/0.298; C3c 23/0/0 h vs 47/35/8 — the single
ledgered caveat; C6 attested; C8 PASS). Accordingly this session will introduce:

* **NO `ScenarioConfig` field** (so no new mechanism-matrix row; rule 28(c) is
  not engaged).
* **NO offer-curve band multiplier change** of any kind — the rule 1
  `[R-STRUCT]` / rule 13 `[R-MEASURED]` authorized channel is **NOT USED**, and
  the keeper's `authorized_price_tuning` block stays absent.
* **NO import lever, no floor, no window, no class re-pricing.**
* **NO control solve** (rule 29(b): the keeper's committed bundle IS the
  control; G-CTRL form 4). The one non-scored solve this session runs is the
  **bench scaffold** of §5.1, which is a *construction* step, not a control.
* **NO tuned value anywhere.** Every input landed here is measured, cited, and
  applied by the SAME recipe the 2023–2025 rows were built with (rule 22:
  *what is held out is the SCORE, never the DATA*).

**Rule 22 posture, stated first.** 2022 is **validation tier**
(`holdout_policy.tier_for_year(2022) == "validation"`); the holdout freeze is
tier-scoped to `locked_test` only (`frozen_tiers == {"locked_test"}`); CAISO
holds the `complete` marker declared 2026-09-06, so
`holdout_policy.authorized(marker_doc, "CAISO", "validation") is True`. All
four gates (the CLI year gate, D-6 quarantine, `audit_keepers`, and the R-AZ
registration re-check in `dashboard_add_run.py`) are satisfied **at launch and
must be re-satisfied at registration**. **2019 and H1-2026 are NOT touched, in
any form.** `final` is not held and is not sought.

**A 2022 number is selection evidence, never a skill number** (rule 22), and it
**cannot move the ISO's determination in either direction** (rule 30(c)). If
2022 misses, the miss is DIAGNOSED and any repair is re-trained on 2023–2025 —
never fitted to 2022.

---

## §1 — The order, and why it is not negotiable

| # | phase | why it must precede the next |
|---|---|---|
| 1 | **RTM 2022 sizing + crawl** (§2, §3) | H-2: without the RT hub price, C3a/C3b/C3c cannot be scored in 2022 at all, and the rung would be a volume-only rung the owner explicitly did NOT choose (charter §5/§6). |
| 2 | `postprocess_oasis_downloads.py` → `derive_actual_lmp.py` → `derive_actual_tail.py` (§4) | the C3c benchmark (`actual_tail.json`) reads the parquet the derive writes. |
| 3 | **H-1**: the 2022 bench part → `regen_caiso_bench_cems.py` 2022 → `derive_caiso_supply_consistent_demand.py` (§5) | the keeper runs `caiso_supply_consistent_demand=True`; `_load_caiso_supply_consistent_demand(2022)` raises `FileNotFoundError` without the artifact, so **the rung cannot solve at all** until this lands. |
| 4 | **S-1…S-4** (§6) | each is a *silent* fallback: a 2022 solve without them runs a recipe the keeper was never scored on, with no warning (caiso-259 §2). |
| 5 | **the rung** (§7) | only when 1–4 are complete and asserted. |

---

## §2 — Phase 1a: the RTM group sizing (PROTOCOL, declared before it runs)

### §2.1 What is known before measuring

* `RTM_LMP_GRP` at `version=1` was measured 2026-09-06 (charter §2) at **ONE
  operating hour per request**, 7.5 MB, one component
  `PRC_INTVL_LMP_RTM_01_v1.csv` (~138 MB), OPR_HR 01, 12 five-minute intervals
  × 4 LMP types × ~16.6k nodes.
* The charter §6 and `data/raw/lmp-data/CAISO/README.md` both state the tracked
  Jan-2023 `v3` zips were **"7 groups/day"**. **I record now, before measuring,
  that I believe that claim is FALSE**: the tracked manifest
  (`SHA256SUMS.txt`) carries group numbers `01`…`24` for 2023-01-01 (21 of the
  24 present: 01–18, 20, 23, 24) and 01–08 for 2023-01-02 — i.e. the group
  index is the **operating hour**, and "7 groups/day" is an artifact of how
  many hours were hand-downloaded on some days, not of the delivery. If the
  sizing confirms this, the RTM year is **8,760 requests**, exactly as the
  charter §4 sized it, and the `version=3` hope buys nothing.
* `fetch_caiso_oasis_grp.py` currently issues **one request per trade date**
  for every market, and calls `fold(...)` after each zip. `fold` **skips a
  window whose CSV already exists**, so folding after each hour-zip would
  write the day window from hour 01 alone and silently drop hours 02–24. The
  fetcher therefore **must** be extended to: download all of a day's hour
  groups, then fold ONCE, then delete the zips.

### §2.2 The sizing measurement (ONE trade date, 2022-06-01)

Fixed before it runs, so no result can re-choose it:

* **date** = **2022-06-01** — the date the charter already probed at
  `version=1`, so the v1↔v3 comparison is like-for-like. It is NOT chosen for
  any price property.
* **requests**: `GroupZip?groupid=RTM_LMP_GRP&startdatetime=<UTC of each local
  hour>&version=3&resultformat=6` for local hours 00…23, ≥ 6 s apart.
* **recorded**: for each hour — HTTP status, `Content-Disposition` filename
  (hence the group index the server assigns), payload bytes, member CSV names,
  the member's value-column name (`MW` vs `VALUE` — the fold's
  `usecols=["INTERVALSTARTTIME_GMT","NODE","LMP_TYPE","MW"]` **raises** if it
  is `VALUE`), the `OPR_HR` values present, and the kept-node row count.
* **also recorded**: the same request at `version=1` for hour 00, to confirm
  the two versions deliver the same object.

### §2.3 The decision the sizing drives (fixed ex ante)

| measured | decision |
|---|---|
| v3 delivers **one operating hour** per request (expected) | crawl 24 requests/trade date × 365 = **8,760 requests**; wall ≈ (download + 6 s) × 8,760. Proceed. |
| v3 delivers **>1 hour** per request (e.g. a whole day, or 7 groups covering 24 h) | crawl at the measured group count; re-size and record the saving. Proceed. |
| v3 returns "no data" / an error envelope for 2022 while v1 serves it | crawl at **`version=1`**; record the version choice and its reason. |
| the RTM component's value column is `VALUE`, not `MW` | extend `fold_caiso_oasis_grp_zips._window_frames` to accept either column name and normalise to `MW` (a **schema** repair, not a data change); re-verify the tracked Jan-2023 fold is unaffected. |
| the kept-node set is absent from the RTM component (no `TH_*_GEN-APND`) | **STOP** — file a FINDING, do not crawl. The charter measured TH_SP15 present (48 rows), so this would be new information. |

**The sizing is a STOP gate only.** It cannot promote anything and it looks at
no price.

---

## §3 — Phase 1b: the crawl

* `scripts/data/fetch_caiso_oasis_grp.py --market rtm --start 2022-01-01 --end
  2022-12-31 --sleep 6`, extended per §2.3, run as a **background job with a
  recorded PID**, resumable (a day whose window CSV exists is skipped),
  **extract-and-discard** (each hour zip deleted after the day folds; peak disk
  ≈ 24 × 7.5 MB ≈ 180 MB, well inside the ~20 GB allowance).
* **DST is handled by instants, not by an hour counter**: the day's requests
  step 1 h at a time from local midnight to the next local midnight, so
  2022-03-13 issues 23 requests and 2022-11-06 issues 25. A fixed
  `range(24)` would silently lose or duplicate an hour.
* **AUP**: ≥ 6 s between requests, exponential back-off, the existing
  non-zip/HTML "Acceptable Use Policy" detection. A date that exhausts its
  retries is recorded MISSING and the crawl continues.
* **Budget declared:** up to 8,760 requests / ≈ 65 GB transferred (never
  retained) / ≈ 24 h. If the elapsed rate implies the crawl cannot finish in
  this session, the session **hands off with the crawl running and the window
  CSVs staged**, and does not fake a partial year (§8 STOP-3).

---

## §4 — Phase 2: fold → aggregate → derive, with byte-identity assertions

### §4.1 Snapshot BEFORE (the answer key for every assertion below)

`sha256` of **every** file in `data/raw/lmp-data/CAISO/` matching
`CAISO_{dam,rtm}_hourly_{2023,2024,2025,2026}.csv`, plus
`data/raw/_validation-source/actual_lmp.json`,
`data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`,
`frontend/data/backcast/tail/actual_tail.json`, and
`data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet`. Written
to `/tmp/.../caiso262_before.json` and quoted in the FINDING.

### §4.2 The steps

1. `postprocess_oasis_downloads.py --stage-dir <scratch>` →
   `CAISO_rtm_hourly_2022.csv`.
   **A-1 (hard):** every `CAISO_dam_hourly_{2023..2026}.csv` and
   `CAISO_rtm_hourly_{2023..2026}.csv` is **sha256-identical** to §4.1.
   Rationale: `_merge_write` writes only the years the new windows produce,
   and the PST trade-date attribution (`ts − 8 h`) keeps 2022-12-31's hours in
   2022 — but the assertion is what proves it, not the reasoning.
   **A-2 (hard):** `CAISO_rtm_hourly_2022.csv` carries the same node set and
   column schema as `CAISO_rtm_hourly_2023.csv`, and ≥ `CAISO_MIN_HOURS`
   (6,500) hours in which all three hubs are present.
2. `derive_actual_lmp.py --years 2022 --isos CAISO`.
   **A-3 (hard):** `actual_lmp.json` differs from §4.1 in **exactly one**
   key path — `CAISO["2022"]` added; every other ISO-year parses equal.
   **A-4 (hard):** `actual_lmp_hourly_CAISO.parquet` — the 2023/2024/2025/2026
   rows are **row-identical** (same order, same float32 bits) to §4.1; only
   `year == 2022` rows are added. (The file's own sha256 will change; that is
   expected and is not the assertion.)
   **A-5 (hard):** every OTHER ISO's `actual_lmp_hourly_*.parquet` is
   sha256-identical (the `--isos CAISO` scoping must actually scope).
3. `derive_actual_tail.py` (marker-gated; CAISO is in `complete`).
   **A-6 (hard):** `actual_tail.json` differs in exactly one key path —
   `isos.CAISO["2022"]` added; every other (ISO, year) row parses equal.

### §4.3 The DA half, restated

The 2022 **DAM** aggregate and the 2022 intertie parquet rows landed in
caiso-261 and are **already committed**. This session does not re-fetch, re-fold
or re-write them; `derive_actual_lmp.py --years 2022` will read the committed
`CAISO_dam_hourly_2022.csv` and emit the `da` half of the 2022 record alongside
the new `rt` half, which is why the derive is run **once**, after RTM lands
(caiso-261 closing addendum deliberately deferred it for exactly this reason).

---

## §5 — Phase 3 (H-1): the 2022 supply-consistent demand artifact

### §5.1 The circularity, named, and how it is broken

`derive_caiso_supply_consistent_demand.py` reads
`frontend/data/backcast/bench/CAISO/2022.json.gz` (the CEMS anchors + the
per-plant hourly CEMS series + `classFull`). `regen_caiso_bench_cems.py` can
only **amend** an existing part — it opens `part_path` and reads
`obj["bench"]["plants"]`. Bench parts are written by
`render_calibration_html.build_payload` → `render_backcast._write_bench_part`,
which needs a **solved bundle** (it reads `system.parquet` and the bundle's own
`inputs/` snapshots). So: the artifact needs the part, the part needs a solve,
and the solve needs the artifact.

**The break, declared here:** the bench year payload is **actuals only** —
`plants` (CAMPD × the fleet group map), `e930` (EIA-930), `classFull` (EIA-923
− BTM), `avgLMP` (measured LMP), `storage` (EIA-930), `co2` (eGRID/CAMPD). Its
only run-dependence is the **fleet**, not the demand input. So a **bench
scaffold solve** — the keeper recipe with `--no-caiso-supply-consistent-demand`
and nothing else changed — produces a bundle from which the canonical builder
writes an actuals-correct 2022 part.

**Scaffold discipline (binding):**
* it is **never scored, never registered, never quoted as a 2022 result**, and
  its only surviving output is `bench/CAISO/2022.json.gz`;
* the bundle is **DELETED before the PR merges** (rule 29(c));
* it is not a control solve and establishes no drift claim (rule 29(b) stands);
* **G-BENCH (hard):** after the real rung of §7 solves, the 2022 bench part is
  rebuilt from the **rung's** bundle and must be **byte-identical** to the
  scaffold's. If it is not, the scaffold contaminated the artifact chain →
  re-derive the demand artifact from the rung's part and re-solve the rung
  once; if it still differs, **STOP** and file a FINDING.

### §5.2 The 2022 guards, pre-registered

`regen_caiso_bench_cems.py` `_CEMS_GUARD[2022]` and
`derive_caiso_supply_consistent_demand.py` `_ANNUAL_GUARD[2022]` are new
entries. Neither may be a number chosen to make the derive pass. Fixed now:

* **`_CEMS_GUARD[2022]`** — declared as `(lo, hi)` = the 2022 CEMS bench-gas
  total the CAMPD 2022 extract itself produces, ± 0.5 TWh, **computed and
  written down BEFORE the regen runs**, from `rcf._campd_hourly_frame(2022,
  "CAISO", …)` over the gas groups. It is a *reproduction* guard (does this
  runner decode the same CAMPD bytes?), exactly as the 2023–2025 entries are —
  the FINDING §3 windows are ±0.5 TWh around the measured value.
* **`_ANNUAL_GUARD[2022]` — G-DEMAND-2022, a WEDGE guard, not a level guard.**
  A level window for a never-derived year could only be fitted to that year's
  own output, which is worthless. Instead: let
  `wedge(y) = 930 CISO Demand-identity (NetGen − TI) annual total − derived
  demand annual total`. Measured on the committed artifacts for 2023/2024/2025
  **before** the 2022 derive runs, this gives `W23, W24, W25`. The
  pre-registered 2022 admissible band is
  **`wedge(2022) ∈ [−1.5 TWh, max(W23, W24, W25) + 1.5 TWh]`**, converted to
  the `_ANNUAL_GUARD` (lo, hi) form the script already checks. It is computable
  ex ante, is not fitted to 2022, and catches precisely the failure it must
  (a corrupt `NG: NG` cell, a missing CEMS block, a clock slip). **Direction
  reported, not gated:** the `NG: NG` corruption onset is ~2024-05 (caiso-80
  FINDING §6), so 2022's wedge is *expected* to sit near 2023's (+10.4 TWh)
  rather than 2025's (+18.5 TWh); if it does not, that is a finding to report,
  not a reason to move the band.
* The existing guards are **untouched**: `_ANCHOR_TOL` (the decoded-CEMS-vs-
  committed-anchor reproduction, 0.1 TWh), `demand.min() > 0`, and
  `_PARITY_TOL` (the uncapped-reconcile parity check).

### §5.3 The derive rewrites everything — the assertion that makes it safe

`derive_caiso_supply_consistent_demand.py` takes **no arguments** and rewrites
`caiso_supply_consistent_demand_{2023,2024,2025}.csv` + `provenance.json` on
any invocation.

**A-7 (hard):** after extending `YEARS` to include 2022 and running it, the
2023/2024/2025 CSVs are **sha256-identical** to their pre-run state, and
`provenance.json` differs in exactly one key path (`years["2022"]` added).
If any 2023–2025 byte moves → **STOP-1** (§8): `git checkout` the four files,
report, and do not proceed.

---

## §6 — Phase 4: the four silent fallbacks (S-1…S-4), each cited

Rule 22 as amended 2026-08-06: **a measured input is applied consistently
across ALL years.** These are not "2022 inputs"; they are the 2022 rows of
tables that already carry 2023–2025 by the same recipe. Rule 23
`[R-FROZEN-DERIVE]`: each re-derivation commit cites the source-data change.

| id | object | recipe — FROZEN, identical to the committed years | gate |
|---|---|---|---|
| **S-1** | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` (today: **absent** → `state_carbon_price()` returns `None` → the CARB allowance cost is **$0/t** for every in-state fossil unit in 2022, ~$11–12/MWh on a CC and **merit-order distorting** — the NYISO-134 D-1 defect, CAISO edition) | the **simple mean of that calendar year's four CA–Québec joint auction current-auction settlement prices**, `$/metric tonne as published` — the identical recipe the committed comment documents for 2023/2024/2025 (`fuel_trajectories.py:1184-1186`). Each of the four 2022 quarterly prices must be **individually attributed to a named CARB source** before the mean is taken; `ww2.arb.ca.gov` blocks automated fetches (the `carbon-auction-results` README documents 403/405/503 on every pattern), so attribution is by CARB's own press-release text, exactly as the committed 2023–2025 rows were. **The four prices are transcribed, never inferred**, and the four rows are added to `data/raw/policy/carbon-auction-results/carbon-auction-results.csv` alongside the mean. | if any of the four cannot be attributed to a named source → the row is **NOT written**, S-1 is reported OPEN on the rung, and the 2022 carbon cost is stated at the gate as a known recipe difference. No estimate, no interpolation. |
| **S-2** | `IMPORT_TRANCHES_BY_YEAR["CAISO"][2022]` (today: falls to the **static** ladder — a different firm block) | the DMM **2022** Annual Report RA-import capability table, the same basis and the same table as the committed 2023 / 2024 rows. | if the DMM 2022 report is not fetchable from this environment (the 2024 report 404s on the caiso.com pattern — caiso-261 FINDING §7 #4), S-2 is **reported OPEN** and the static fallback is **stated on the rung**, never silently taken. A chart-read is not a substitute. |
| **S-3** | `CAISO_DSW_{OVERNIGHT,DAYTIME,SURPLUS}_CLEAN_DEPTH_BY_YEAR[2022]` (today: falls to the STATIC pooled 2023–2025 depths) | `derive_caiso_overnight_clean_depth.py` / `derive_caiso_daytime_clean_depth.py` / `derive_caiso_pnw_surplus_depth.py` on 2022 — **now derivable**, because caiso-261 landed the 2022 MALIN / PALOVRDE rows of `wecc_intertie_lmp_hourly_CAISO.parquet` (H-3 CLOSED). caiso-259 §2 listed S-3 as *not* derivable; that is superseded by the H-3 landing, and the change is a source-data update, cited. | each derive's **own** committed gates must pass unmodified. A gate FAIL → the 2022 depth is **not written**, the static fallback is stated on the rung, and a FINDING records the failure. **No gate is relaxed** (rule 23). |
| **S-4** | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` + `nuclear-availability-CAISO.csv` 2022 windows (today: static seasonal pattern + EFORD; Diablo's 2022 refuel timing absent) | `derive_nuclear_monthly_cf.py --isos CAISO --years 2022` (EIA-923 2022 present) then `derive_nuclear_availability.py --iso CAISO --years 2022` (`nrc-reactor-status/2022PowerStatus.txt` present). | **A-8 (hard):** each derive's 2023–2025 outputs are unchanged (sha256 / row-identity), exactly as A-3/A-4. |
| S-5 | `CAISO_RA_MUSTOFFER_GAS_MW` | — | **INERT** on this keeper (`caiso_ra_mustoffer_quantity_gate=False`). No action, verified not assumed. |
| S-6 | `caiso-dam-outages` | — | **INERT** (`caiso_dam_outages=False`). No action, verified not assumed. |

**Every S-item that lands OPEN is named on the rung's registry note and in the
FINDING as a recipe difference between 2022 and the training years** — the
touchpoint is only honest if the reader knows which inputs were the keeper's
and which were fallbacks.

---

## §7 — Phase 5: the rung

* `scripts/run_calibration_full.py` on the **FROZEN caiso-260 recipe** — the
  `run_config.json` of `caiso260_demand_vintage`, reproduced flag-for-flag,
  with **only** `--year 2022 --holdout-authorized` and a new `--out-dir`
  differing. One year, one bundle, one invocation. (Rule 16 `[R-ALLYEARS]` is
  not engaged: a touchpoint is a held-out year replayed on a keeper that
  already carries its full 2023–2025 span, not a single-year keeper.)
* **A-9 (hard):** before the solve, the arm's resolved `ScenarioConfig` is
  diffed against the keeper's `run_config.json`; the ONLY differences permitted
  are the year, the out-dir, and fields that are year-keyed lookups (the S-1…S-4
  tables). Any other difference → **STOP-2**.
* Then, in order: `scripts/dashboard_add_run.py` (which re-asks the marker gate
  at registration, R-AZ); `scripts/stamp_touchpoint_holdout.py --run-id <id>
  --keeper-id 2026-09-06-caiso-260-b1-demand` (rule 30(a) — **the stamp is what
  folds the run into the keeper's report; an unstamped touchpoint is a second
  card for the same config**); `scripts/build_status.py --iso CAISO` (rule
  30(b): the per-year holdout ladder, derived, never hand-authored);
  `scripts/audit_keepers.py --iso CAISO`; the `calibration-keeper-auditor`
  agent; `scripts/check_registry_payload_parity.py`.
* **Rule 30(c), restated as a binding instruction to myself:** whatever 2022
  scores, `keepers/CAISO.json` `keeper`, its `note`, and
  `calibration-complete.json` `complete.CAISO.determination` are **NOT edited**.
  The ISO's headline is the train-tier verdict. A degraded rung is REPORTED on
  the status page's holdout ladder and in the assessment doc, and nowhere else.
* **Rubric v3.6:** on an out-of-training year the C3c standing rule drops its
  lone-failure condition, so C3c reads CAVEAT in 2022 whatever else 2022 does.
  That is the scorer's behaviour, not a claim about 2022, and it is stated
  rather than relied on.

---

## §8 — STOP RULES (each is STOP-only; none has a branch that tunes)

* **STOP-1 — any 2023–2026 input changes.** Any assertion A-1…A-8 failing is a
  stop-the-line event: `git checkout` the moved file(s), verify the restore
  against §4.1, report in the FINDING, and do not proceed past that phase. **No
  assertion is downgraded to a warning, and no tolerance is widened to make one
  pass.**
* **STOP-2 — recipe drift.** A-9 failing (the arm is not the keeper's recipe)
  stops the rung. The fix is to reproduce the recipe, never to accept the drift
  and note it.
* **STOP-3 — the crawl cannot finish.** If the RTM year is incomplete when the
  session must end, the session hands off with the crawl running, the windows
  staged, and the PRECOMMIT/FINDING carrying the measured rate. **A partial
  RTM year is NEVER folded into `CAISO_rtm_hourly_2022.csv` and passed off as
  the year** — `CAISO_MIN_HOURS = 6500` is the floor `derive_actual_lmp` itself
  enforces, and it is not lowered, and `CAISO_PARTIAL_YEARS` is **not**
  extended to 2022 (2026 is in that set because its window is short by
  *publication*; a half-crawled 2022 is short by *fetch*, which is exactly the
  case the guard exists to refuse).
* **STOP-4 — a source cannot be attributed.** Any S-item whose value cannot be
  traced to a named primary source is left OPEN and stated, never estimated.
* **STOP-5 — G-BENCH fails twice** (§5.1): stop and file a FINDING.
* **STOP-6 — the sizing surprises.** §2.3's last row.

**No STOP rule has a branch that changes a model parameter, relaxes a gate, or
selects an input by what it does to 2022.**

---

## §9 — DO-NOT-REDO, carried in full

`caiso-261 §9`, `caiso-260 §9`, `caiso-258 §10`, `caiso-257 §10` and every
section they carry stand **in full**. Named explicitly because they are within
arm's reach of this session:

1. The **hod 22–23 import object is CLOSED** as a data-intake object. If 2022
   shows the same import deficit, that is a REPORTED observation and **not** a
   licence to re-open it, and specifically not a licence to reach for the G-26
   public-bid surface (caiso-252 §7 #2; caiso-261 §9 #5).
2. **Panoche / the CT volume miss** is a DECLARED PERMANENT RESIDUAL (owner
   ruling 2026-09-06). No floor, pin, class re-pricing or window may be built
   to reach it, in 2022 or any year.
3. Never re-adjudicate the DMM §17 native-load need as an intake; never read
   the 2023 ceiling-minus-floor room as un-carried volume; never propose the
   CPUC RA showings as "beyond" the DMM row; never wire DMM Fig 4.2 / 1.53 or
   EIA-930 net interchange as an input.
4. The **whole-plant-off days** (Moss Landing 91, Otay Mesa 121) — DO-NOT-REDO.
5. **S2 (two-settlement), the per-zone hourly sidecar, and the G-26 public-bid
   surface are OTHER sessions' chartered lanes.** This session does not touch
   them (handoff, explicit).

---

## §10 — DISCLOSURES AGAINST INTEREST (opened now; appended to as they arise)

1. **I contradict two committed documents before measuring.** The charter §6
   and the `lmp-data/CAISO/README.md` correction paragraph both say
   `RTM_LMP_GRP` `version=3` was "7 groups/day"; I predict in §2.1 that it is
   one operating hour per request and that the tracked corpus shows group
   indices 01–24. If the sizing proves *me* wrong, §2.3 already binds me to the
   measured answer, and the record will say so.
2. **The bench-scaffold solve is a solve of a held-out year that is not the
   rung.** It is authorized (validation tier, `complete` marker) and it is
   never scored — but a reader is entitled to know that 2022's LP is entered
   twice, once on a demand input that is NOT the keeper's. G-BENCH is the
   check that this cannot leak into the artifact chain; it is a check, not a
   proof, until it runs.
3. **`_ANNUAL_GUARD[2022]` is weaker than the 2023–2025 entries.** Those are
   ±1.5 TWh around a level the caiso-80 FINDING §6 registered independently;
   mine is a one-sided wedge band derived from the other three years. It will
   catch a gross input failure and will not catch a subtle one.
4. **S-1's four CARB prices will be attributed via press-release text, not a
   primary PDF**, because the domain blocks this environment. That is the same
   provenance the committed 2023–2025 rows carry, and it is weaker than a
   downloaded settlement-results PDF.
5. **The session may not finish.** The RTM crawl alone is budgeted at ~24 h. If
   it does not complete, no rung exists and this PRECOMMIT plus the crawl state
   is the deliverable. I will not compress the crawl by lowering
   `CAISO_MIN_HOURS`, by sampling hours, or by substituting RTPD (a 15-minute
   basis change the charter §4 already refused under rule 14).

---

## §11 — DELIVERABLES

This document (pushed first); the RTM sizing record; the
`fetch_caiso_oasis_grp.py` RTM hour-group extension; the crawl summary JSON;
`CAISO_rtm_hourly_2022.csv`; the 2022 rows of `actual_lmp.json` /
`actual_lmp_hourly_CAISO.parquet` / `actual_tail.json`; the 2022 bench part;
`caiso_supply_consistent_demand_2022.csv`; the S-1…S-4 landings (or their
stated OPEN status); the rung bundle + its registration + the rule-30(a) stamp
+ the rebuilt status part; a FINDING carrying every number this session cites;
the `docs/calibration-log/caiso.md` entry; and — only if a mechanism is
actually tested, which none is planned — a rule-28 CAISO matrix-shard touch.

**Next number: caiso-263.**
