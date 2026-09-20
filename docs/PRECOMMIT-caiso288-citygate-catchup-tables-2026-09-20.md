# PRECOMMIT caiso-288 — the 2022 C3a miss is a GAS-SERIES COVERAGE DEFECT: EIA published the Dec-22..30 2022 citygate prints and the CAISO scraper discarded them

**Lane:** CAISO calibration · **Date:** 2026-09-20 · **Keeper UNCHANGED**
`2026-09-19-caiso-287-mer-keeper` (bundle `caiso287_mer_span`; 2022 folded as
`2026-09-19-caiso-287-mer-2022`, bundle `caiso287_instr_2022`). **LP spent so far: ZERO.**
Predecessors: `docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md` (which handed this
object up), `docs/FINDING-nyiso234b-the-gas-series-was-published-2026-09-14.md` (which found and
repaired the SAME scraper defect in the sibling NYISO fetcher).

This document fixes **the measurement, the gates, the pre-registered band and every named
outcome before a single LP is solved.** Nothing in §5 is computed yet.

---

## 0. THE OBJECT, AND WHAT PHASE 0 FOUND

The handoff sent this lane at the 2022 C3a miss (**model $94.074 vs RT load-weighted $84.49,
+11.3 %**) — the only load-bearing failure anywhere in the CAISO set. Phase 0 (zero LP, over the
committed keeper sidecars, `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet` and the
committed bench) decomposed it, and the answer is **not** where the three predecessor sessions
were looking.

**(a) It is not a belly object.** On the model's own net load (demand − wind − solar):

| net-load decile | d0 (belly) | d1–d4 (shoulder) | d9 (peak) |
|---|--:|--:|--:|
| share of the +$10.32/MWh gap | **3.6 %** | **62.8 %** | −4.0 % |

The caiso-285/286/287 belly lane, had it closed completely, would have reached **3.6 %** of this
rung's failure.

**(b) It is concentrated in December, and inside December in NINE DAYS.** December carries
**38.4 %** of the annual gap; **Jan–Nov alone is +9.90 %, inside the ±10 % band.** Within
December the miss is **Dec 23–31**, which carry **47.1 %** of the *annual* gap between them:

| Dec 2022 day | 22 | 23 | 25 | 27 | 29 | 30 | 31 |
|---|--:|--:|--:|--:|--:|--:|--:|
| model $/MWh | 447.9 | 401.5 | 361.1 | 430.2 | 432.1 | 407.1 | 414.2 |
| actual DA | 486.9 | 317.4 | 282.2 | 296.2 | 181.9 | 130.0 | 118.7 |
| actual RT | 495.4 | 291.0 | 195.4 | 191.6 | 169.9 | 103.2 | 98.6 |
| model − RT | −47.5 | **+110.5** | **+165.7** | **+238.6** | **+262.2** | **+303.9** | **+315.7** |

Through Dec 22 the model tracks the market (and mostly sits *below* it). From Dec 23 the market
collapses and **the model does not.**

**(c) A gas unit is marginal in 89.7 % of December hours** (committed `marginal_emission_rate`
sidecar, caiso-287's append). So the December price *is* the CAISO gas price.

Every figure in this section, in §3 and in §4 is produced by
`scripts/probes/caiso288_phase0.py` into the committed
`results/calibration/_caiso288_phase0.json`, from committed artifacts and the production
delivered-gas loader. Nothing here is hand-computed.

## 1. THE DEFECT — established, not hypothesised

The keeper prices CAISO gas off the measured daily CA-Composite citygate spot
(`caiso_citygate_spot_level` + `caiso_citygate_spot_coverage` + `caiso_citygate_flow_date`, all
`True`), read from `data/raw/gas-prices/caiso_citygate_daily.csv`.

**That file has no print between 2022-12-21 and 2023-01-05.** Run through the *production*
loader (`fuel.hubs._caiso_hub_daily_gas_prices`, keeper flags, plus
`CAISO_CITYGATE_TRANSPORT_ADDER`), the model therefore burns gas at a **flat
$54.05/MMBtu on every flow day from Dec 22 to Dec 31 2022** — the forward-fill of the Dec-21
print of $53.59, the single highest print of the year, struck at the peak of the western gas
crisis.

**The prints were published the whole time.** EIA issues no Natural Gas Weekly Update during the
Christmas/New Year weeks — `archivenew_ngwu/2022/12_29/` and `archivenew_ngwu/2023/01_05/` both
return **HTTP 404** — and when it resumes, the catch-up page carries the skipped weeks as
**additional live tables**. The `2023-01-12` page carries **three**:

| table | flow week | Cal. Comp. Avg ($/MMBtu) |
|---|---|---|
| 1st | Jan 5 – Jan 11 | 16.55 / 17.09 / 18.42 / 18.76 / 17.63 — *in the committed CSV* |
| 2nd | Dec 29 – Jan 4 | **15.00 / 15.31 / Holiday / 23.66 / 18.37** — discarded |
| 3rd | **Dec 22 – Dec 28** | **32.16 / 36.93 / Holiday / 26.78 / 20.86** — discarded |

The line that lost them, `scripts/data/fetch_caiso_citygate_daily.py:128`:

```python
m = re.search(r"<table.*?</table>", seg, flags=re.S)   # the FIRST table only
```

`re.search`, not `re.finditer` — **character-for-character the defect nyiso-234b found and
repaired in `fetch_transco_daily_spot.py` on 2026-09-14.** This is the CAISO half of it. The
model burns **$54.05/MMBtu on days the market measured $15.00–$36.93**.

**This is a rule 14 `[R-ACCURATE]` / rule 23 `[R-FROZEN-DERIVE]` re-derivation cited to a
SOURCE-COVERAGE DEFECT, never to a residual.** The defect was found by decomposing the residual
in space and time; it is *adjudicated* on the source, and §5 pre-registers that the repair stays
in whichever way the gates move.

## 2. THE REPAIR — scraper-side, zero free parameters, CAISO-scoped

1. **`parse_spot_table` reads every live table**, not the first (`re.finditer`), with the
   segment window widened 24 k → 60 k so a three-table catch-up page fits, and each row tagged
   with its table's `week`.
2. **G-DUP, a new guard.**  EIA itself re-served a stale table: the `2025-12-04` page carries
   **2024's** Thanksgiving week (3.60/3.36/3.52/3.18/3.45) under **2025** dates. A value vector
   that exactly reproduces another week's is not a measurement, and the two cannot be told apart
   from this source, so **BOTH are refused** — the deliberately conservative choice, at a cost of
   5 days in 2024 and 5 in 2025, stated here rather than discovered later. (A silent stale print
   is worse than a gap: a gap is visible.)
3. **The regenerated `caiso_citygate_daily.csv`** is the only data artifact this arm changes.

**Rule 25 `[R-ISO-SCOPE]` is satisfied by inspection:** `parse_spot_table` is imported by exactly
one other module, `fetch_pge_socal_citygate_daily.py`, which builds a **CAISO** series
(`caiso_zonal_gas_basis`, default off and off in this keeper). `fetch_miso_citygate_daily.py`
does not import it. **No other ISO's input moves.** Zero `ScenarioConfig` fields are added, no
constant changes, no multiplier is touched, no `offer_curve_by_group` band moves, and no
`authorized_price_tuning` block is claimed.

**A disclosed coupling, NOT repaired here (rule 19 `[R-ONE-MECH]`, one change per arm).**
`scripts/data/derive_caiso_offer_surface.py::_gas_staircase` reads the same CSV. Its estimation
window is **2023–2025**, so **December 2022 — the decisive block — is outside it entirely** and
the 2022 arm is uncontaminated. The 2023–2025 moved days (~87 of ~1,095 pooled days) sit inside
it; the surface is a cap-weighted median over the pooled span and is **NOT re-derived in this
session**. Named as a follow-on, with its footprint stated, not absorbed.

## 3. THE FOOTPRINT — measured on the production loader before any solve

**G-FETCH PASSED** (§5): the repaired fetcher re-read all **244** weekly pages of 2021–2026 with
**0 fetch failures**, reproduced every one of the **1,156** committed prints in that range
**byte-for-byte** (max |Δ| 0.000000 on both columns), **dropped none**, and **added 85** —
`git diff --stat` independently reads `1 file changed, 85 insertions(+)`, zero modifications.
**G-DUP refused exactly 10 rows across the 2 predicted weeks** and nothing else.

`data/raw/gas-prices/caiso_citygate_daily.csv`: 1,806 → 1,891 rows.
sha256 **pre** `925555422185ea1f…` → **post** `301472621ed1f53d…` (the shard hard stop).

Delivered citygate ($/MMBtu) through the production loader, control vs treatment:

| year | hours moved | mean Δ | max +Δ | max −Δ |
|---|--:|--:|--:|--:|
| 2022 | 648 | −0.565 | +3.46 | **−38.59** |
| 2023 | 624 | +0.033 | +7.11 | −1.92 |
| 2024 | 792 | −0.057 | +0.02 | −2.25 |
| 2025 | 672 | −0.014 | +0.49 | −0.58 |

The 2022 movement is three contiguous blocks, and **they do not all point the same way**:

| block | days | Δ gas $/MMBtu |
|---|--:|---|
| 2022-05-06 .. 05-12 | 7 | −1.52 .. −0.25 |
| 2022-11-18 .. 11-28 | 11 | **+0.39 .. +3.46** (against the residual) |
| 2022-12-23 .. 12-31 | 9 | **−16.66 .. −38.59** (the object) |

## 4. THE PRE-REGISTERED BAND — fixed here, before the solve

At the CAISO CC_REGULAR cap-weighted base heat rate **7.44 MMBtu/MWh**
(`derive_caiso_offer_surface._fleet_geometry`), on 2022:

* **Dec 23–31** (216 h, 2.25 % of load, a fossil unit marginal in **94.9 %**):
  ΔMC **−$185.57/MWh**, against an observed model−RT of **+$216.04/MWh** on the same hours.
* **Nov 18–28** (264 h, 2.68 % of load, fossil-marginal 73.1 %):
  ΔMC **+$15.26/MWh**, against an observed model−RT of only **+$2.30/MWh**.
* **May 6–12** (168 h): ΔMC −$1.9 to −$11.3/MWh, a block the gap census did not predict — it
  comes from a second live table on a *regular* (non-catch-up) page, and is reported rather than
  filtered out.

| limb | construction | 2022 model $/MWh | C3a |
|---|---|--:|--:|
| **LOWER** | the price does not move at all | 94.074 | **+11.34 %** (FAIL) |
| **UPPER** | full pass-through in every moved hour with a fossil unit marginal | 90.2869 | **+6.861 %** (PASS) |

**The band on the annual load-weighted mean is −$3.788/MWh, and the FAIL/PASS boundary lies
inside it.** The arm is therefore genuinely capable of failing to close the gate, and that
outcome is named in §5. Aggregated over all moved hours:

| direction | hours | % of load | mean Δ gas | mean Δ MC | fossil-marginal | observed model−RT |
|---|--:|--:|--:|--:|--:|--:|
| gas **down** (May + Dec) | 384 | 3.94 % | −14.301 | **−106.401** | 80.47 % | **+129.633** |
| gas **up** (Nov) | 264 | 2.68 % | +2.051 | **+15.259** | 73.11 % | **+2.299** |

The down-block's marginal-cost relief is **82 % of the miss measured on those same hours** and
cannot overshoot into an under-price; the up-block's is **6.6×** the miss on its hours and
therefore makes November worse. Neither ratio was tuned to — both fall out of the measured
prints.

## 5. THE GATES, AND EVERY OUTCOME, NAMED BEFORE THE ANSWER IS COMPUTED

**G-SRC — the prints exist.** The two skipped Thursdays return 404 **and** the catch-up page
carries ≥2 live `Cal. Comp. Avg` tables. Recovered values are never invented, interpolated or
reconciled; they are read from EIA's own table. *(Already measured; recorded here.)*

**G-FETCH — REPRODUCTION. A failure STOPS THE SESSION and is reported as a defect**, never
worked around. The repaired fetcher, run over 2021–2026, must reproduce **every** committed
print in that range **byte-for-byte**; the only admissible diff is **additions**. If any existing
value moves, that is a second defect — reported, and the session stops before any solve.

**G-DUP — the stale-table guard refuses exactly the 2024-11 and 2025-11 weeks and nothing else.**
Any further refusal is reported.

**G-FOOT — the delivered gas array moves ONLY on recovered days**, 0 moved hours elsewhere, at
the per-year counts of §3.

**G-CTRL — form 1, a paired control at the SAME HEAD.** HEAD has moved 2,062 insertions across
18 solve-path files since the keeper's `git_sha` `92b8e4db`, so form 4 (differencing against the
keeper's committed numbers) would conflate this arm with that drift. Both arms are therefore
solved at one pinned HEAD, differing in the citygate CSV and nothing else. **This is why the
shard count is eight and not four**, and the cost is accepted rather than argued away.

**G-DIR — the honesty gate, pre-registered so it cannot be reported as a surprise.** The Nov
18–28 2022 block moves gas **UP** by $2.05/MMBtu and therefore moves **AGAINST** the residual.
The repair is **not uniformly favourable**, which is the signature of a measured input rather
than a fitted one. A session report that omits the November leg is incomplete.

### 5.1 The outcomes

* **(A) C3a-2022 lands inside ±10 %.** The rung's sole load-bearing failure closes. Reported with
  the November cost at full magnitude.
* **(B) C3a-2022 improves but stays outside ±10 %.** Reported. **The repair stays in.**
* **(C) C3a-2022 is unchanged or worse.** **The repair still stays in**, and the lane reports that
  the gas series was not the carrier and hands the object on.
* **(D) A 2023 / 2024 / 2025 gate flips adversely.** Reported at full magnitude. **The repair
  stays in.** Rule 14 `[R-ACCURATE]` is explicit and this lane pre-commits to it here: a worse fit
  from accurate data is a **discovered bug elsewhere**, never a licence to restore the estimate.

**In no outcome does this session revert the repair, sweep a value, re-derive the offer surface
against a gate, or arm or disarm any mechanism.** Nothing is promoted by this session; promotion
is the owner's act and the question is surfaced, not pre-empted (rule 31 `[R-RETAIN]`).

## 6. THE SHARDS — eight, one per (arm × year), all pinned to ONE SHA

**THE PARENT NEVER SOLVES** (rule 32 `[R-SHARD]` (a)). **One year per shard, one container each**
(rule 36 `[R-YEAR-ISOLATION]` (a)) — a backcast year carries no cross-year state, and the parent
composes the per-year bundles at zero LP. **Every registered year is solved** (rule 34
`[R-SHARD-PROMOTABLE]` (c)); the CAISO registered year union, enumerated from
`frontend/data/backcast/registry/*.json` **before** anything is pruned (rule 35 `[R-PROMOTE]`
(b)), is **{2022, 2023, 2024, 2025}**.

| shard | arm | year | bundle |
|---|---|---|---|
| 1–4 | **treatment** — repaired citygate CSV | 2022 / 2023 / 2024 / 2025 | `caiso288_gasfix_<year>` |
| 5–8 | **control** — committed citygate CSV | 2022 / 2023 / 2024 / 2025 | `caiso288_ctrl_<year>` |

Each shard: full 40-char `source_revision` and `source_url` as **create_session parameters**;
`DATA PROFILE: caiso`; its own `--out-dir` and branch; **pushes its whole bundle** including
`dispatch/<year>_P1.parquet` by `.gitignore` negation plus a **plain** `git add` (rule 34 (a) and
its 2026-09-12 `-f` correction); never touches `frontend/data/backcast/**`,
`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, `src/`,
`scripts/`, never opens a PR, never deletes a result, never rebases or pulls.

## 7. COST, stated before it is spent

Eight CAISO per-plant years at ~20–25 min each, in eight containers, concurrently. **The parent
spends zero LP**: the decomposition, the footprint, the band, the scoring, the differencing and
the composition are all arithmetic over committed artifacts. Shards run the runner unmodified,
never pass `--no-container-preflight`, and report the `container preflight:` and `memory peak:`
lines from the nested cgroup (rule 32 (c)(8)).

## 8. WHAT THIS SESSION REFUSES, named so it can be checked

* **No sweep.** No threshold, horizon, multiplier or fraction is varied against any gate.
* **No offer-curve tuning.** `offer_curve_by_group` is carried byte-identical; no
  `authorized_price_tuning` block is claimed.
* **No re-point of C3a at DA.** Withdrawn by a prior session and it stays withdrawn — even though
  phase 0 measures the model at only **+2.10 % against DA** and **74 % of the 2022 miss is the
  DA−RT spread**. That measurement is reported as context and is **not** a proposal.
* **No re-opening of the caiso-287 §8 closed list** (the surplus decommit screen, the gap-fusing,
  the CC start cost) — closed with evidence, and nothing here is new evidence against them.
* **The `startup_aware` drop-rate admissibility question stays with the owner** (caiso-287 §5).
  This session neither disarms nor defends it.

## 9. TEST BASELINE — taken BEFORE the change, as the handoff requires

`tests/iso/caiso` + `tests/unit/data`, **2,571 passed / 6 failed** with the repair applied. The
**same six** fail on clean `main` with the three changed files stashed (verified by
`git stash push -- <the three paths>`, not by `git stash` on committed work — the handoff's
inherited trap): `test_caiso_per_hub_intertie::test_tranches_placed_in_hub_zone`,
`test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact`,
`test_fleet::test_neiso_includes_mystic_cc`, both
`test_gas_offer_zonal_anchor_vintage` cases, and
`test_soco_zonal_gas_hub::test_no_applier_is_armed_for_soco`. **This change introduces zero new
failures.**

**One test constant DOES move, and it moves AGAINST the residual**:
`test_caiso_citygate_spot_level::test_jan_2023_levelled_at_daily_spot`, Jan-2023 delivered
**$16.58 → $17.33**. The committed series had no print before 2023-01-05, so Jan 1–4 were
back-filled from the $16.55 Jan-5 print; they now carry their own measured prints (Jan-3 $23.66,
Jan-4 $18.37), which are **higher**. Updated in place with that provenance as a rule 23
`[R-FROZEN-DERIVE]` source-coverage re-derivation — it is a 2023 constant and the residual under
repair is a 2022 object, so it cannot be a fit either way.

## 10. SHARD LEDGER — launched 2026-09-20, all pinned to `35adf93cfcde5020f484b0a1057c5ad9a9115434`

Recorded here so recovery is by immutable SHA and session id, never by branch name (rule 33
`[R-SHARD-ARCHIVE]` (d)).

| arm | year | session | branch | replays | CSV sha256 (hard stop 2) |
|---|--:|---|---|---|---|
| gasfix | 2022 | `session_01S2ipYQrSSVgWRcqK17tbdA` | `claude/caiso-288-gasfix-2022` | `caiso287_instr_2022` | `301472621ed1f53d…` |
| ctrl | 2022 | `session_019E9iMscoGuq8Yumqx3ho1g` | `claude/caiso-288-ctrl-2022` | `caiso287_instr_2022` | `925555422185ea1f…` |
| gasfix | 2023 | `session_01LfUH99Zb2q4iTi3otyPLNu` | `claude/caiso-288-gasfix-2023` | `caiso287_mer_span` | `301472621ed1f53d…` |
| ctrl | 2023 | `session_011TcvBAviY12FqtuoJzr37i` | `claude/caiso-288-ctrl-2023` | `caiso287_mer_span` | `925555422185ea1f…` |
| gasfix | 2024 | `session_01GboWf4P9hsFyNCcbfhxeBN` | `claude/caiso-288-gasfix-2024` | `caiso287_mer_span` | `301472621ed1f53d…` |
| ctrl | 2024 | `session_015BULUxuanZK1VEzY7pEPhJ` | `claude/caiso-288-ctrl-2024` | `caiso287_mer_span` | `925555422185ea1f…` |
| gasfix | 2025 | `session_01TWg1SXar5RBXCYMmPFSS9P` | `claude/caiso-288-gasfix-2025` | `caiso287_mer_span` | `301472621ed1f53d…` |
| ctrl | 2025 | `session_01CxCtguctnLb2ZQ2dJggiEm` | `claude/caiso-288-ctrl-2025` | `caiso287_mer_span` | `925555422185ea1f…` |

The treatment arm carries the repaired CSV the pinned SHA commits (1,892 lines). The control
arm restores the pre-repair CSV from `bcd83731` (1,807 lines) and commits **only** its bundle,
leaving that restore unstaged — so the two arms differ in one data file and nothing else. Each
shard pushes its **full** bundle including `dispatch/<year>_P1.parquet` (rule 34 (a)); the
parent composes, scores, differences and registers at zero LP (rule 32 (a), (d)).
