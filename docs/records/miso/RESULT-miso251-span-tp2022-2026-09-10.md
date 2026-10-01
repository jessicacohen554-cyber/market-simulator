# RESULT — miso-251 SPAN shard: the MISO keeper replayed on held-out 2022

```
SHARD           : SPAN (single year, so span == year) of session miso-251
BRANCH          : claude/miso251-tp2022
PINNED SHA      : b69062657498097f1bfb7ed264d77d95403f65e9   (verified, never pulled/rebased)
RUN ID          : 2026-09-10-miso-251-tp2022
BUNDLE          : results/calibration/miso251_tp2022
KEEPER REPLAYED : 2026-09-09-miso-250-ep-gas  (results/calibration/miso_fuelvintage_A)
CHARTER         : docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md
DETERMINATION   : NOT-YET
```

**Headline.** The MISO keeper's frozen recipe, replayed on 2022, reads **NOT-YET** —
for two *independent* reasons, and the second would stand even if the first were
cured: (1) **C6 is UNATTESTED**, because the standing touchpoint-attestation
generator refuses any recipe delta and the PRECOMMIT's declared input degradation
*is* a delta; and (2) **C1, C3a, C3b and C4 all FAIL on merit.** 2022's coal is
+50.8 TWh over actual while gas-CC is −14.7 TWh under, and the model never prices
a single hour above **$95/MWh** in a year with 116 actual RT hours above $200.

**Rule 30(c): this does not touch MISO's headline.** MISO's determination is the
train-tier 2023–2025 verdict (`CALIBRATED`) and nothing else. A held-out year is
iterable model-SELECTION evidence, it cannot certify and it cannot decertify.
Since `[R-HOLDOUT]` was removed (2026-09-09) that is true of every year.

---

## 1. Hard stops — all three PASSED

| # | check | value read | verdict |
|---|---|---|---|
| 1 | `git rev-parse HEAD` | `b69062657498097f1bfb7ed264d77d95403f65e9` | **PASS** |
| 2 | keeper `meta.json` | `iso: MISO`, `years: [2023, 2024, 2025]` | **PASS** |
| 3 | `CC_REGULAR.committed` | `1.1055` | **PASS** |
| 3 | `CT_PEAKER.peak` | `4.4` | **PASS** |
| 3 | `summer_wefor_share_override` | `1.0599` | **PASS** |

Recorded before the first LP in `docs/ADDENDUM-miso251-span-phase0-2026-09-10.md`
and pushed as the heartbeat.

## 2. Config verification (charter step 4) — MACHINE-PROVEN, not asserted

From `results/calibration/miso251_tp2022/run_config.json`:

```
miso_measured_reserve_requirements = false      <- declared delta 1
miso_reserve_online_gated          = false      <- declared delta 2
offer_curve_by_group.CC_REGULAR.committed = 1.1055   (unchanged)
offer_curve_by_group.CT_PEAKER.peak       = 4.4      (unchanged)
summer_wefor_share_override               = 1.0599   (unchanged)
```

Stronger than a spot-check: a full `meta.json` diff of touchpoint against keeper,
excluding provenance keys, returns **exactly**

```
TOP-LEVEL differing keys: ['coal_prb_sigmoid_overrides',
                           'miso_measured_reserve_requirements',
                           'miso_reserve_online_gated']
  coal_prb_sigmoid_overrides -> nested diffs: ['miso_measured_reserve_requirements',
                                               'miso_reserve_online_gated']
  miso_measured_reserve_requirements : True -> False
  miso_reserve_online_gated          : True -> False
```

i.e. the only movement anywhere in the recipe is the two declared flags (the
third entry is merely the container dict that nests them). **Nothing else was
added, dropped, tuned or swept.**

The degradation behaved as the PRECOMMIT §3 predicted — the run fell back to
MISO's own published static RBDC construction, and the solve log prints the
market-wide requirement at **3,382 MW at h0 (MSSC + regulating, flat), 12 ORDC
steps ($200–$3,500)**, matching phase 0's 2022 figure exactly; the two published
zonal families armed at 2,161 MW and 2,982 MW.

## 3. Determination and reasons

```
CALIBRATION DETERMINATION: NOT-YET
  run 2026-09-10-miso-251-tp2022  (MISO: miso 251 tp2022)
  scorable years: 2022
determination basis:
  - governance gate UNATTESTED: no governance attestation in bundle
```

`reasons[]` carries that single line. It is **not** the only failure, merely the
one the basis names: `grade_summary` reads `scored 5, target_grade 1,
commercial_grade 0, ledgered 0, fails 4`.

## 4. Per-criterion result

| criterion | tier | status | magnitude |
|---|---|---|---|
| **C1** fuelmix | load-bearing | **FAIL** | 4 classes out of band (table below) |
| **C2** sysvol | load-bearing | PASS | *delegated* — see §4.1 |
| **C3a** price_mean | load-bearing | **FAIL** | model $60.55 vs actual RT $69.87 = **−13.3 %** (band ±10 %) |
| **C3b** price_shape | load-bearing | **FAIL** | NRMSE **0.279** |
| **C3c** price_tail | supporting | **SKIPPED** | no committed RT actual tail for MISO-2022 (§6.2) |
| **C4** dispatch_corr | supporting | **FAIL** | coal r = **0.741**, NRMSE = **0.325** |
| **C6** governance | protective | **UNATTESTED** | no attestation in bundle (§6.1) |
| **C8** forced_share | protective | PASS | CT_PEAKER 24.9 % grounded above budget |

Reported-only: **C5a CO2 +14.0 %** (FAIL, but REPORTED-ONLY since rubric v2.9 —
contributes no status, no caveat budget, no reason line). **D-A** diurnal
amplitude SKIPPED (no committed measured hod profile for 2022).

`D-10 free-class C1: C1 all 4/8 · free 2/6`, pinned/excluded `CC_CHP`, `ST_CHP`.
`caveats.ledgered` is **empty** — C3c did not reach the ledger because it was
skipped for want of a benchmark, not scored and excused.

### 4.1 Why C2 reads PASS while its own classes fail

C2's PASS here is **structural delegation, not a clean volume result.** For a
fully-reported EIA-923 vintage (both MISO families are complete in 2022)
`score_sysvol` records `status: PASS` **by construction** and hands gating to
C1, writing the breaches into its own magnitude field. Its two records read:

| family | model TWh | actual TWh | delta | magnitude string |
|---|---|---|---|---|
| gas | 161.16 | 175.75 | −14.59 | `C1 flags: CC_REGULAR, CT_PEAKER` |
| coal | 273.88 | 223.05 | **+50.83 (+22.8 %)** | `C1 flags: COAL_PRB, COAL_BIT` |

Band: `per-class ±min(max(2.0 % ISO-load, 3 % actual-gen), 8 TWh) = ±8.00 TWh
& ±3 pp share (via C1)`. **A reader must not quote C2 PASS as evidence 2022's
volumes are sound.**

### 4.2 C1 rows as scored

| class | verdict | volume | share |
|---|---|---|---|
| CC_REGULAR | **FAIL** | −16.41 TWh | −3.4 pp (volume/share out of band) |
| CT_PEAKER | **FAIL** | +8.14 TWh | +1.1 pp (volume out of band) |
| COAL_PRB | **FAIL** | +37.09 TWh | +4.4 pp (volume/share out of band) |
| COAL_BIT | **FAIL** | +13.44 TWh | +1.5 pp (volume out of band) |

### 4.3 C8 note (carried verbatim)

> C8 2022 CT_PEAKER: grounded above budget — 24.9 % forced (4.7751 of 19.1746 TWh)
> — above the 15 % cap but GROUNDED: all binding mechanisms clear D-4; profile
> r 0.987 (≥0.8) & off-peak CV ratio 0.939 (≥0.5) (rebuilt floors exclude the
> P1-dependent RA bridge — share is a lower bound).

Immaterial-class skips: COAL 0.1 % of load (D-2 reads 0.1 % forced), ST_GAS 1.9 %
(**D-2 reads 25.6 % forced** — below the 2 % materiality floor so not gated, but
worth the parent's eye), hydro 1.6 % (0.0 % forced).

## 5. The numbers the charter asked for

### 5.1 System price

| | model | actual |
|---|---|---|
| load-weighted mean LMP | **$60.55/MWh** | **$69.87/MWh** (RT) |
| simple mean LMP | $59.52/MWh | $69.90/MWh (DA) |
| C3a delta vs RT | **−13.3 %** | — |

The scorer's benchmark string is `vs RT (LEGACY equal-hour basis)` — MISO-2022
carries no `rt_lw` load-weighted bench field, so C3a fell to the legacy
equal-hour rung of the v2.4 basis ladder. Flagged, not worked around.

### 5.2 RT > $200 hour counts

| threshold | model (system LW hourly) | actual RT |
|---|---|---|
| > $100 | **0** | 1,034 |
| > $200 | **0** | **116** |
| > $500 | 0 | 11 |
| > $1000 | 0 | 1 |
| max | **$95.19** | $1,082.57 |
| p99 | $86.85 | $238.67 |

Zone-hours above $200: **0 of 70,080**. Load shed (slack): **0.0 MWh**. Reserve
price positive in only **6** hours of 8,760.

Actual counts are computed here from the committed
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet` (Indiana-Hub
reference), whose 2022 coverage is **RT 7,560/8,760 = 86.3 %**, DA 8,232/8,760 =
94.0 % — so the true 2022 counts are *higher* than the table. The ratio is
**0.00×**, materially worse than the keeper's own 0.03× / 0.19× / 0.12× on
2023/2024/2025.

### 5.3 Generation TWh by class, model vs actual

| class | model | actual | delta | model share % | actual share % | Δpp |
|---|---:|---:|---:|---:|---:|---:|
| CC_CHP | 16.820 | 18.954 | −2.134 | 2.57 | 2.95 | −0.37 |
| CC_REGULAR | 110.833 | 125.567 | −14.734 | 16.95 | 19.52 | −2.57 |
| COAL | 0.367 | 0.000 | +0.367 | 0.06 | 0.00 | +0.06 |
| COAL_BIT | 81.286 | 67.843 | **+13.443** | 12.43 | 10.55 | +1.89 |
| COAL_LIGNITE | 6.380 | 6.457 | −0.077 | 0.98 | 1.00 | −0.03 |
| COAL_PRB | 185.846 | 148.752 | **+37.093** | 28.42 | 23.12 | +5.30 |
| CT_CHP | 5.632 | 7.513 | −1.880 | 0.86 | 1.17 | −0.31 |
| CT_PEAKER | 22.268 | 14.125 | +8.143 | 3.41 | 2.20 | +1.21 |
| OTHER | 12.523 | 12.523 | 0.000 | 1.92 | 1.95 | −0.03 |
| OTHER_FOSSIL | 0.000 | 8.976 | −8.976 | 0.00 | 1.40 | −1.40 |
| ST_CHP | 3.183 | 4.988 | −1.805 | 0.49 | 0.78 | −0.29 |
| ST_GAS | 16.284 | 12.113 | +4.171 | 2.49 | 1.88 | +0.61 |
| biomass | 8.709 | 8.709 | 0.000 | 1.33 | 1.35 | −0.02 |
| hydro | 9.244 | 10.598 | −1.354 | 1.41 | 1.65 | −0.23 |
| import (net) | −21.711 | 0.000 | −21.711 | −3.32 | 0.00 | −3.32 |
| nuclear | 86.608 | 91.353 | −4.745 | 13.25 | 14.20 | −0.96 |
| oil | 0.000 | 0.384 | −0.384 | 0.00 | 0.06 | −0.06 |
| solar | 4.541 | 4.541 | 0.000 | 0.69 | 0.71 | −0.01 |
| wind | 105.062 | 99.920 | +5.142 | 16.07 | 15.53 | +0.54 |
| **TOTAL** | **653.876** | **643.314** | **+10.562** | | | |

(Model column is the P1 `class_hourly_2022` sum; the actual column is the bench
`classFull`. The C1/C2 scorer works on grid-delivered net-of-BTM figures, which is
why its gas family reads 161.16 rather than this table's raw sum — both are given
rather than reconciled silently.)

### 5.4 Solve wall-clock

Wall clock **12 min 14 s** (01:56:49 → 02:09:03 UTC). Engine-reported
`total = 706.0 s`, decomposed `data_prep 43.5 s · solve_p0 430.4 s · markup 19.0 s ·
solve_p1 151.9 s · results_write 61.2 s`. P0 cold: 329,569 simplex iterations,
objective 8,470,157,436.05. P1 warm: 96,631 iterations, objective 8,627,651,730.31.
Peak RSS 13.31 GB against the prepared 23.7 GiB (15.7 RAM + 8 swap). **Inside the
20-minute shard cap** (rule 32 `[R-SHARD]` (b)).

## 6. Three findings the parent must rule on

### 6.1 BLOCKER — the touchpoint attestation generator refuses a declared degradation

`scripts/gen_touchpoint_attestation.py` exists precisely for this case, but it
exits **2** with `RECIPE IDENTITY FAILED — the touchpoint is not the keeper's
recipe`, listing exactly the two declared flags. That is the tool working as
designed: its docstring says a touchpoint's C6 PASS must be *"backed by a machine
check rather than by prose"*, and it admits no channel for a
degradation that a purged upstream source **forces**.

So C6 cannot be attested for this rung by any route available to a shard. I did
**not** hand-write an attestation: fabricating the one artifact whose entire
purpose is to be machine-verified would defeat the check and would be a
governance forgery, not a fix. I also did not edit the generator — rule 32
(c) 6 forbids a shard touching `scripts/`, and *"a shard that repairs
infrastructure is a FAILURE."*

**The decision is the owner's**, and it is a real one: either the generator gains
a declared-degradation channel (a `--declared-degradation key=value` allow-list
that records the delta in the attestation instead of refusing it, so the machine
check still binds on everything else), or **no MISO year before 2023 can ever be
attested**, and the holdout ladder is closed for MISO by construction rather than
by evidence. Note this is not MISO-specific in principle — any ISO whose measured
overlay post-dates its holdout years hits the same wall.

### 6.2 C3c could not be scored — the 2022 tail artifact is not built

C3c SKIPPED: `no committed RT actual tail for this ISO-year
(frontend/data/backcast/tail/actual_tail.json — run scripts/data/derive_actual_tail.py)`.
The input it needs **does exist** (§5.2 computes the counts from it directly), so
this is one derive away. I did not run it: `frontend/data/backcast/**` is a shared
generated tree my charter forbids me to write beyond the registration paths.

Materially this changes nothing about the determination — C3c is supporting-tier,
and under rubric v3.6's out-of-training limb it would read CAVEAT on 2022
regardless. But the rung currently reports a **skip where a −100 % miss belongs**,
and §5.2 is the honest number.

### 6.3 The 2022 sub-BA zonal load shares are on disk but unreachable

The solve logged:

```
WARNING: MISO sub-BA load file covers 2022 only partially (7/8760 hours); skipping
```

`scripts/data/curate_zonal_shares.py::parse_miso_shares` **hardcodes**
`miso_subba_demand_2023-2025.csv` and filters it to the requested year; for 2022
only the 7 UTC-boundary rows survive, so it returns `None` and the run falls back
to **sample-average zone shares**. But `data/raw/zone-specific-demand/MISO/`
already contains `miso_subba_demand_2022.csv` with **full-year coverage — 8,757
distinct periods, all six sub-BAs, 2022-01-01T00 → 2022-12-31T23**. (2018–2021
per-year files are there too.)

So the owner's instruction to the parent — *"ensure all data needed is populated
in the repo to run holdout years 2020-2022"* — **was satisfied**; the loader
simply cannot see it. Consequence for this rung: total MISO demand is correct
(EIA-930 metered, 653.2 TWh / 116.4 GW peak per phase 0), but the **allocation
across the six zones uses a flat sample average instead of 2022's own hourly
shape** — a different demand basis than the 2023–2025 training years enjoy, which
plausibly touches congestion, zonal price formation, and therefore C3a/C3b/C4.

**This is a one-line loader change, and it is the parent's to make (`scripts/`).**
Until it lands, 2022's price criteria are being scored on a degraded zonal input
that nobody declared — I am flagging it rather than letting the rung's price
failures be read as pure model error.

## 7. Diagnosis of the merit-order miss (evidence, not a lever)

Not a lever, not tested, not proposed as a config change — offered because §5.3's
shape is systematic rather than noisy.

The single largest regime difference between 2022 and every calibration year is
**gas price**:

| year | Henry Hub $/MMBtu | role |
|---|---|---|
| **2022** | **6.45** | this holdout rung |
| 2023 | 2.54 | keeper training |
| 2024 | 2.19 | keeper training |
| 2025 | 3.52 | keeper training |

2022 gas is **1.8×–2.9×** the entire regime in which the keeper's
`offer_curve_by_group` band multipliers were identified. The observed error is
exactly what an offer surface calibrated at $2–3.5 gas produces at $6.45 gas:
coal **+50.8 TWh** over, gas-CC **−14.7 TWh** under — a merit-order inversion
of about the right magnitude and precisely the right sign. Coal's PRB sigmoid
passthrough is far flatter in fuel price than the gas classes' delivered-fuel
pass-through, so as gas triples, modelled coal displaces gas faster than the real
market's coal did (real coal was supply-constrained in 2022 — rail and
inventory — in a way the LP has no representation of).

The price miss is consistent with the same story: **−13.3 %** mean with a
**$95.19 annual maximum**. A fleet that meets load with too much cheap coal
prices too low and never reaches the scarcity tail.

**Rule 1 `[R-STRUCT]` explicitly forbids the obvious response.** Re-fitting the
band multipliers so 2022 lands is per-year fitting; condition (b) of the
2026-09-05 carve-out requires **ONE config across EVERY scored year**, and
condition (c) forbids selecting a factor against a gate. If anything here is
real, it is a **structural** gap — a fuel-price-responsive coal supply constraint
with a forward story — and it needs its own charter, its own PRECOMMIT and its
own G-CTRL, not a multiplier nudge.

## 8. Ladder status (PRECOMMIT §5)

Rung 1 (2022) did **not** read `CALIBRATED`, so §5.1's "proceed" condition is not
met. **2021 and 2020 remain independently blocked** by the §2.3 scoring-side gap
(no `actual_lmp.json` MISO block and no `calibration_reference.json` MISO for
2020), which no LP can cure — an unscored load-bearing criterion downgrades, so
neither rung could read `CALIBRATED` whatever the model did. **No LP was spent on
either**, per §5.2 and rule 29 `[R-SCREEN]`'s economy. The one thing that unblocks
them is `MISO_PRICING_API_KEY`, absent from environment and repo.

Whether to open a 2022 diagnostic screen (§5.3) is the parent's and owner's call,
and §6.3 should be fixed **before** any such screen — otherwise it would be
diagnosing a zonal-input artifact.

## 9. Retention (rule 31 `[R-RETAIN]`)

`results/calibration/miso251_tp2022` is **on local disk and gitignored**, and it
is committed to this branch with `git add -f` exactly as the charter directs, so
it survives independently of the container. **Nothing was deleted.** No `rm` was
run against any result.

**The promotion question is open and is asked here explicitly:** this rung is a
NOT-YET touchpoint. It should be *registered and folded* under rule 30(a) rather
than promoted, but the fold stamp (`stamp_touchpoint_holdout.py`), the status
rebuild (`build_status.py --iso MISO`), the keeper text, the calibration log and
the mechanism-matrix stamp are all **the parent's**, explicitly forbidden to this
shard. They are owed and not yet done.

### 9.1 What was committed, and why not the whole 213 MB

The charter's step 6 says `git add -f results/calibration/miso251_tp2022`. Taken
literally that stages **213 MB**, because `-f` also forces past `.gitignore`'s
deliberate §8 slim-bundle rules — which exclude `dispatch/` (101 MB),
`hourly/unit_hourly_*.parquet` (102 MB), `floors/`, and the top-level
`*.parquet` mirrors, and whose stated rationale is precisely *"dispatch/<year>_P1.parquet
alone is ~80 MB and would trip the remote's 413 push limit."* CLAUDE.md's Git &
Pushing section says the same in its own words: `git push` *"remains NOT licensed
for a full bundle directory … or for a divergent branch that would pack hundreds
of MB."*

So this commit carries the **slim bundle — byte-for-byte the same file set the
MISO keeper itself has tracked**:

```
hourly/{class_hourly, class_band_hourly, reserve_family, storage, system}_2022.parquet
legitimacy_diagnostics.json · meta.json · metrics.json · run_config.json
```

**3.5 MB staged, 13 files, nothing outside the charter's allowed paths.** That
satisfies rule 15 `[R-DASHBOARD]`'s keeper-sidecar requirement (`class_hourly` +
`system` + `reserve_family` all present), so a later diagnostic session reads this
rung's class-dispatch and price hourlies without replaying the solve.

Two consequences stated rather than buried:

* **The unit-grain layer is NOT committed.** `.gitignore` makes it opt-in per
  bundle for *"a lane that WILL interrogate a bundle at unit grain"*; this shard
  was not chartered to, and it is 102 MB against a 413-prone remote. If the
  parent wants the §7 merit-order diagnosis pursued unit-by-unit, that layer must
  be opted in deliberately — **and it only exists on this container's disk**
  (rule 31 `[R-RETAIN]`: nothing was deleted, but nothing ephemeral survives
  reclamation either).
* **Nothing was deleted.** All 213 MB remain on local disk for as long as this
  container lives.
