# RESULT — nyiso-223 shard `nyiso223-y2024` (NYISO 2024 hub gap-fill arm)

**Status: SOLVED. Arm bundle `results/calibration/nyiso223_gapfill_2024` (gitignored, on local disk).**
Pinned revision `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` (verified). Date 2026-09-10.

**HEADLINE — the arm's mean-preservation claim SURVIVES contact with the LP.
ZERO classes move more than 0.10 TWh** (largest: ST_GAS +0.033). The mechanism moves
price where it claims to (Dec 22–31 **+$0.82/MWh**) and essentially nowhere else
(annual load-weighted **+$0.069/MWh**, +0.17 %). No criterion flips.

## 0. Hard stops + config signature — ALL PASSED

| Check | Expected | Observed |
|---|---|---|
| `git rev-parse HEAD` | `ce4779ec…23ed99` | match |
| keeper `meta.json` iso | NYISO | NYISO |
| `grep -c nyiso_hub_gap_month_level` | ≥ 4 | 4 |
| `nyiso_hub_gap_month_level` | true | **true** |
| `CC_REGULAR.peak` / `.pct_peaking` | 2.25 / 8.0 | **2.25 / 8.0** |
| `nyiso_gas_commitment_bridge` | true | **true** |
| `nyiso_dynamic_reserve_requirements` | true | **true** |
| `iso` / years | NYISO / [2024] | **NYISO / [2024]** |

Pre-solve gate reproduced the PRECOMMIT to the digit: annual mean **2.7969 → 2.7969**
(identical to 4 dp), Dec 22–31 **3.877 → 4.061**, hours moved **5880**.

Solve: **425 s (7.1 min)**, one invocation, one year.

## 1. BASIS OF THESE NUMBERS — READ THIS BEFORE QUOTING THEM

**These are NOT the registered scorer's output.** `calibration_verdict.py` refuses an
unregistered bundle ("could not resolve a registered run … no registry sidecar"), and
it scores the **dashboard payload** (`frontend/data/backcast/runs/<id>.js`) built by
`dashboard_add_run.py` — which this shard is forbidden to run, and which rule 32
`[R-SHARD]` (d) assigns to the parent anyway. A screen bundle is also never registered
(rule 29 `[R-SCREEN]`).

So every number below is computed **directly from the arm's own committed artifacts**
(`system.parquet`, `hourly/class_hourly_2024.parquet`, `legitimacy_diagnostics.json`)
against the **committed benchmark** (`frontend/data/backcast/bench/NYISO/2024.json.gz`,
read-only), applying the scorer's own definitions read out of
`scripts/calibration_verdict.py`. The keeper is recomputed on the identical basis from
its own committed sidecars, so **every arm-vs-keeper delta is like-for-like**.

Two independent checks confirm the basis is the right one: my keeper C3a reproduces
**+5.33 %** against the stated **+5.3 %**, and my keeper C8 ST_GAS reproduces
**20.90 %** against the stated **20.9 %**. C3b does *not* fully reproduce (mine 0.172
vs the registered 0.179) — see §3.

## 2. C3a — mean LMP

Actual basis `rt_lw` = **38.12 $/MWh** (RT load-weighted; the basis that reproduces the
keeper's stated +5.3 %).

| | model LW mean | vs actual | band ±10 % |
|---|---|---|---|
| keeper | 40.1499 | **+5.33 %** | PASS |
| **arm** | **40.2188** | **+5.51 %** | **PASS** |
| delta | **+0.0689** | **+0.18 pp** | |

## 3. C3b — monthly load-weighted price NRMSE

| | NRMSE (my reconstruction) | limit |
|---|---|---|
| keeper | 0.172 | 0.20 |
| **arm** | **0.174** | 0.20 |
| **delta** | **+0.002** | |

**Caveat, stated plainly:** my reconstruction gives the keeper **0.172**, the registered
scorer **0.179** — a −0.007 basis gap (the payload's `pMon`/`dMon` zone aggregation is
not exactly reproducible from `system.parquet`). **The delta is the reliable quantity,
the absolute level is not.** Carrying the +0.002 delta onto the registered basis puts
the arm at **≈0.181 vs the 0.20 limit** — still passing, margin narrowing from 0.021 to
0.019. This is the tightest cell you flagged and it stays tight; it does **not** break.
Only the parent's registered scoring can confirm the absolute value.

## 4. C3c — price tail / scarcity

| | hours any zone > $300 | actual | max zonal price |
|---|---|---|---|
| keeper | **0** | 13 | $217.86 |
| **arm** | **0** | 13 | **$217.67** |

As predicted, no hour appears — the model's ceiling is **27.4 % below** the $300 bar and
the arm moves it *down* $0.19. C3c remains the lone failing criterion, ledgered as an
accepted model-class limitation under rule 22 `[R-C3C]`. **Unchanged by the arm.**

## 5. C1 — per-class TWh vs actual

Volume band = min(max(2 % ISO load, 3 % actual gen), 8 TWh) = **3.980 TWh**.
Actual total gen 132.681 TWh.

| class | actual | keeper | arm | keeper miss | arm miss | verdict |
|---|---|---|---|---|---|---|
| CC_REGULAR | 34.060 | 36.975 | 36.947 | +2.915 | **+2.887** | PASS (tightest cell) |
| CC_CHP | 17.017 | 19.566 | 19.547 | +2.548 | **+2.529** | PASS |
| ST_GAS | 9.913 | 8.544 | 8.578 | −1.369 | **−1.336** | PASS |
| ST_CHP | 0.872 | 1.129 | 1.135 | +0.257 | **+0.263** | PASS |
| CT_PEAKER | 1.911 | 0.371 | 0.368 | −1.540 | **−1.543** | PASS |

Every class in band. CC_REGULAR is the tightest cell as expected (2.887 of 3.980) and
the arm **improves** it, along with CC_CHP and ST_GAS; ST_CHP and CT_PEAKER worsen by
≤0.006 TWh. All movements are noise-scale. *(Volume leg only — the 3.0 pp share leg is
computed inside the payload and is not reconstructible here.)*

## 6. C8 — forced share by class (D-2), 2024

| class | keeper | arm | delta | cap | verdict |
|---|---|---|---|---|---|
| ST_GAS | 20.90 % | **20.75 %** | −0.15 pp | 30 % | PASS |
| CC_REGULAR | 0.33 % | **0.34 %** | +0.01 pp | 30 % | PASS |
| hydro | 28.68 % | **28.69 %** | +0.01 pp | 30 % | PASS |
| ST_CHP | 28.35 % | 28.25 % | −0.10 pp | exempt | exempt |
| CC_CHP | 0.30 % | 0.39 % | +0.08 pp | exempt | exempt |
| CT_CHP | 0.10 % | 0.10 % | −0.00 pp | exempt | exempt |

Arm mechanism split: `reliability_floor × ST_GAS` 20.56 %, `nyiso_gas_commitment_bridge`
ST_GAS 0.19 % / CC_REGULAR 0.34 %, `hydro_min_flow` 28.69 %, `chp_steam` on the CHP
classes. Every non-exempt class well under budget.

## 7. December split — equal-hour mean model price

| window | keeper | arm | delta |
|---|---|---|---|
| **Dec 22–31** (target) | 51.7005 | **52.5225** | **+0.8219** |
| **Dec 1–21** (control) | 53.5208 | **53.3155** | **−0.2053** |

**This is the mechanism's signature.** The gap fill raised Dec 22–31 gas by
+0.184 $/MMBtu (+4.7 %) and the LP turns that into **+$0.82/MWh in exactly that window**,
while the untouched Dec 1–21 control moves −$0.21. Direction and order of magnitude both
match the pre-solve delta — the screen's structural gate is satisfied.

## 8. ITEM 8 — THE FALSIFICATION TEST: no class moves > 0.10 TWh

Model-vs-model, needs no actuals. **ZERO classes exceed the 0.10 TWh threshold.**

| class | keeper | arm | delta |
|---|---|---|---|
| ST_GAS | 8.5443 | 8.5777 | **+0.0334** |
| CC_REGULAR | 36.9751 | 36.9470 | **−0.0281** |
| CC_CHP | 19.5658 | 19.5467 | −0.0191 |
| CT_CHP | 1.1946 | 1.2047 | +0.0101 |
| ST_CHP | 1.1290 | 1.1350 | +0.0060 |
| CT_PEAKER | 0.3705 | 0.3676 | −0.0029 |
| oil | 0.4434 | 0.4419 | −0.0015 |
| import | 20.7057 | 20.7058 | +0.0001 |
| hydro / nuclear / wind / solar / biomass / OTHER / COAL_* | — | — | **0.0000** |
| **TOTAL** | 152.1795 | 152.1775 | **−0.0020** |

Largest single move **+0.0334 TWh (ST_GAS)** — a third of the threshold. Total system
generation moves −0.002 TWh (−0.0013 %). **The arm redistributes 5,880 hours of hub gas
price without redistributing energy between classes.**

## 9. Determination

**Reconstructed: CALIBRATED**, on the same footing as the keeper — C3c the lone failing
criterion, ledgered under rule 22 `[R-C3C]`; C3a, C3b, C1 and C8 all PASS with every
delta at noise scale.

**Two honest qualifications:**
1. **This is not the registered determination** and must not be quoted as one — see §1.
   Only the parent, after registration, can produce it.
2. **C6 governance is unscoreable here**: the arm bundle carries **no
   `calibration_attestation.json`** (the keeper does). C6 is a protective-tier criterion
   and a failing/unattested C6 would block rule 22's C3c reclassification. The
   attestation is a registration-time artifact the parent owns, so C6 is *pending*, not
   passing.

**D-4 off-window binding FAILs — but it fails IDENTICALLY IN THE KEEPER, so it is NOT
attributable to the arm.** Same two plants in both: `reliability_floor × ST_GAS` plant
2480 (0.0002 TWh, 23 binding hours, measured median 0.0 MW) and
`nyiso_gas_commitment_bridge × CC_REGULAR` plant 54574. The arm **reduces** the latter
(keeper 0.0029 TWh / 89 h → arm 0.0021 TWh / 70 h). It does not reach C8 because rule 19
`[R-FORCED-BUDGET]`'s D-4 provenance leg binds only on a class **above** its cap, and
every non-exempt class is far below (§6) — which is why the keeper scores C8 PASS with
the same rows. Pre-existing issue, unchanged, worth its own lane.

## 10. THE ENVIRONMENT BLOCKER — this cost ~45 min and WILL hit your other shards

`data/clean` **did not exist** in this container. It is gitignored ("DERIVED,
disposable"), and `hydrate_data.py --profile nyiso` does not build it — it reported
*"FULL clone — hydrating changes nothing."* The shard SETUP block ends at hydration, so
a shard launched this way has raw data and no curated data.

Two solves died in ~5 s each before any LP, each naming a different missing partition:

1. `nyiso_li_lcr_tsl=True but no published Long Island transfer_security_limit for
   delivery year 2024/2025 … available areas: []`. The raw row **exists** (940 MW); the
   loader reads *clean*. Fixed with `curate_capacity_deliverability.py --isos NYISO`.
2. `nyiso-interface-flows` clean partition missing.

Both loaders **raise rather than degrade** because their mechanisms are armed in the
keeper recipe — correct (a mechanism must never silently no-op), but it makes every
clean datatype a hard prerequisite. Datatype 2 was not the last, so the fix was the
full tree: **`regenerate_clean.py` took 2,246 s (37.4 min)**, 54/56 datatypes OK.

**Two datatypes failed and you should know about both:**
- **`lmp` (exit 1)** — crashes in `parse_caiso_file` on a **CAISO** file, and because
  `curate()` runs its CAISO loop first, the whole script dies before reaching NYISO,
  PJM or NEISO. `data/clean/lmp/` does not exist at all. It did **not** block this
  shard (scoring reads the committed bench, not clean LMP), but it is a real
  cross-ISO breakage in a shared script.
- **`emissions-unit-annual` (exit −9)** — OOM-killed.

`regenerate_clean.py` exposes **no `--isos` and no `--years` filter**, so it rebuilds all
seven ISOs across all years; per-ISO scoping exists one layer down (individual curate
scripts take `--isos`). **Recommended fix: add a NYISO-scoped clean build to the shard
SETUP block, or pre-build `data/clean` in the parent.** Note also that NYISO raw carries
only **6 months** of 2024 `realtime_zone` zips, so a full-year NYISO LMP curation would
be incomplete regardless.

## 11. Retention (rule 31 `[R-RETAIN]`) — THE PROMOTION QUESTION

**Nothing was deleted.** `results/calibration/nyiso223_gapfill_2024/` is intact, already
gitignored, and was **not** committed (rule 29 `[R-SCREEN]` (c) is discharged by
`.gitignore`, not by `rm` — the ercot-255 lesson).

**This container is ephemeral: the bundle does NOT survive session reclamation.** The
arm is a clean structural result — mechanism does what its arithmetic says, no class
moves > 0.10 TWh, no criterion flips — so **if you want it promoted, the parent must
compose and register it before this session ends.** I am not judging promotion; that is
the owner's call. If it is lost, re-solving 2024 costs **~7 min of LP plus ~40 min of
`data/clean` rebuild** unless the environment is fixed first.

No file under `src/` or `scripts/` was edited. No bundle was committed. No PR opened.
