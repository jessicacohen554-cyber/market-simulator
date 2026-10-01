# PRECOMMIT — caiso-270: restore the designated keeper's bundle, four per-year shards, ZERO new mechanism

**Session caiso-270, 2026-09-10. Branch `claude/caiso-scarcity-ordc-overlay-8ehxye`. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
Keeper: **`2026-09-10-caiso-269-lateevening-clean`**, **CALIBRATED**, single ledgered C3c. **This does not change it.**
Companion: `docs/FINDING-caiso270-scarcity-ordc-phase0-2026-09-10.md` (the chartered lever, closed by measurement).
**Pushed before the first LP of any shard.**

---

## §1 — WHAT IS BEING SOLVED, AND WHAT IT IS NOT

**This is not an arm.** It is the **re-solve of the designated keeper's own recipe**, year by year, because
**the keeper's bundle exists nowhere** — not in `main`, not on any surviving branch, not on any live disk.
There is **no new mechanism, no new `ScenarioConfig` field, no new threshold, no new free parameter, no
derive re-run, no offer-curve multiplier and no `authorized_price_tuning` block.** The DOF ledger is
unchanged at 9 entries / 6 residual. Nothing about the keeper's determination is in play.

**Why now.** Three reasons, in order:
1. **Owner instruction, 2026-09-10**, verbatim: *"Keep working til you launch an lp with shards per year and
   ensure no collision with other active sessions."*
2. It is **decision (B)** this session already put to the owner (`FINDING-caiso270` §8).
3. **Rule 15 `[R-DASHBOARD]` is currently unsatisfied for CAISO.** A KEEPER bundle must commit its `hourly/`
   sidecars so later sessions read them instead of replaying the solve. CAISO's do not exist.

**The evidence that they do not exist** (all verified, not assumed):
* `frontend/data/backcast/keepers/CAISO.json`, the registry sidecar
  `2026-09-10-caiso-269-lateevening-clean.json` and `scripts/gen_caiso269_attestation.py` all name
  `results/calibration/caiso269_lateevening_span`.
* `git ls-tree -r HEAD results/calibration/caiso269_lateevening_span/` returns **nothing**.
* `.gitignore:1754-1756` ignores `results/calibration/caiso269_lateevening_*/` — added under rule 31
  `[R-RETAIN]` while the run was a screen, **never lifted at promotion**.
* The per-year shard branches are gone or emptied: `claude/caiso269-{2023,2024,2025}-rev3` no longer exist
  on `origin`, and the surviving `claude/caiso269-2022` carries the commit
  *"caiso-269: untrack the shard bundle so this branch is merge-safe (rule 29(c)/32(d))"*, `9e7ad037`.
* This session's own phase 0 therefore ran on the committed **predecessor** bundles instead.

`.gitignore:1754-1756` is **not** touched by this PRECOMMIT; the composite this session produces has its own
path and its retention is decided at registration.

## §2 — THE RECIPE EACH SHARD SOLVES

The keeper is the committed predecessor recipe **plus one flag**, exactly as caiso-269 solved it:

| shard | year | replay bundle (COMMITTED) | recorded `gas_prices` |
|---|--:|---|---|
| Y2022 | 2022 | `results/calibration/caiso_fuelvintage_tp2022` (1-year bundle) | `{"2022": 6.45}` |
| Y2023 | 2023 | `results/calibration/caiso_fuelvintage_span` `--year 2023` | `{"2023": 2.54}` |
| Y2024 | 2024 | `results/calibration/caiso_fuelvintage_span` `--year 2024` | `{"2024": 2.19}` |
| Y2025 | 2025 | `results/calibration/caiso_fuelvintage_span` `--year 2025` | `{"2025": 3.52}` |

2022 replays its **own** committed touchpoint bundle rather than the 3-year span, because `gas_prices` and
`weather_year` are per-year keyed and the span carries no 2022 row — this is the same split caiso-269 used
and it is stated here so the year is not silently replayed against another year's recorded inputs.

## §3 — CARD 0(e): THE ZERO-LP BIND CHECK, RUN BEFORE ANY SHARD LAUNCHED

`RESULT-caiso269` §7 made this a standing phase-0 item after a missing reprice entry cost that session eight
shard-years. **Run here, on BOTH replay bundles, at zero LP cost:**

| check | measured |
|---|---|
| recorded override bag | `coal_prb_sigmoid_overrides`, **37 keys**, on both bundles; `caiso_dsw_surplus_clean` / `_overnight_clean` / `_daytime_clean` / `caiso_firm_import_shape` / `_selfschedule` all `True`; the arm **absent** (so the flag is what adds it) |
| **G-IDENT, pre-solve** | applying the fully-resolved recorded config with the flag yields **exactly ONE differing `ScenarioConfig` field: `caiso_dsw_lateevening_clean`** — on `caiso_fuelvintage_tp2022` AND on `caiso_fuelvintage_span` |
| **resolver parity** | `get_interchange_spec(...).caiso_lateevening_clean` **False → True** on both bundles, while siblings `caiso_daytime_clean` / `_overnight_clean` / `_surplus_clean` stay **True → True**. Reproduces `ADDENDUM-caiso269` §A4's table exactly |
| **the caiso-269 defect-4 trap** | `CAISO_DSW_LATEEVENING_CLEAN_NAME` is in `_CAISO_DSW_CLEAN_DEPTH_TRANCHES` (`model/interchange/caiso.py:80-85`), so the tranche reprices at the raw hub and is **not** left on the $180 placeholder |
| guard suite | `tests/iso/caiso/test_caiso_lateevening_clean.py` — **9 passed, 3 subtests passed** |

## §4 — THE PRE-REGISTERED PREDICTION, AND THE ONE GATE

**G-DRIFT is already recorded** in `FINDING-caiso270` §1: every changed hunk between the keeper's arm SHA
`8a4912486cd2a7b6ce9a91cbfaeef03c861f4732` and HEAD is classified **INERT for CAISO** across eleven files
(MISO benchmark leaves only — 197 of 198, zero CAISO; SPP-gated curtailment ceiling; the NYISO-gated
`nyiso_hub_gap_month_level`, whose `hubs.py` hunk leaves the CAISO `_caiso_hub_daily_gas_prices` leg
untouched; eleven PJM ORISPL codes in `ST_GAS_PEAKER_PLANTS`).

**⇒ G-REPRO, the session's ONE gate, pre-registered before the solve: each re-solved year reproduces the
keeper's PUBLISHED C3a to ≤ 0.05 pp.**

| year | keeper C3a (published) | keeper C3b | keeper C4 gas NRMSE |
|---|--:|--:|--:|
| 2022 | **+12.90 %** | 0.2402 | *(unvalidated instrument, no claim)* |
| 2023 | **+4.33 %** | 0.0827 | 0.287 |
| 2024 | **+8.54 %** | 0.1391 | 0.256 |
| 2025 | **+7.87 %** | 0.1070 | 0.294 |

This gate is **STOP-only and it cannot promote anything.** It has exactly two outcomes, both stated now:

* **Reproduction.** The keeper's bundle is restored, rule 15's sidecar requirement is satisfiable, and
  G-DRIFT's INERT classification is confirmed **by measurement** rather than by code reading — which is
  strictly stronger than the audit, at no extra LP cost.
* **Non-reproduction.** Then G-DRIFT's INERT classification is **falsified**, and *that* is the session's
  finding. It will be reported as a defect at full magnitude and the drifting hunk identified. **It will not
  be repaired by re-classifying the drift after seeing the result**, and no number from a non-reproducing
  bundle will be quoted as a keeper number.

No other criterion is gated. Nothing here reads a residual, and no gate can turn this into a promotion.

## §5 — SHARD PLAN (rule 32 `[R-SHARD]`). THE PARENT NEVER SOLVES

Four shards, **ONE YEAR EACH**, all pinned to this PRECOMMIT commit's full 40-character SHA.

| shard | year | branch | out-dir |
|---|--:|---|---|
| Y2022 | 2022 | `claude/caiso270-keeper-2022` | `results/calibration/caiso270_keeper_2022/` |
| Y2023 | 2023 | `claude/caiso270-keeper-2023` | `results/calibration/caiso270_keeper_2023/` |
| Y2024 | 2024 | `claude/caiso270-keeper-2024` | `results/calibration/caiso270_keeper_2024/` |
| Y2025 | 2025 | `claude/caiso270-keeper-2025` | `results/calibration/caiso270_keeper_2025/` |

Rule 32(b): a single CAISO year is the **smallest indivisible unit** — rule 12 `[R-PARALLEL]` forbids
parallel years inside one invocation and the solve has no sub-year shard seam — so the per-year shard is the
finest subdivision available. Expected ~12–20 min per year (rule 12's ~35–70 min for a 3-year CAISO replay).
A shard that reaches 25 minutes with no written bundle **stops and reports**; it never pushes a half-written
bundle (rule 27 `[R-PUSH]`).

Per-year bundle dirs stay **out of `main`** (rule 32(d)): each lives only on its own shard branch, no shard
opens a PR, and the parent composes them into ONE bundle for registration.

## §6 — COLLISION REGISTER (the owner's explicit requirement)

Concurrent sessions at launch, enumerated from the live session list rather than assumed:

| session | ISO | its branches / paths | collides? |
|---|---|---|---|
| **SPP-62 SPAN shard — 2023/2024/2025, register** | SPP | `spp62_*` bundles, `frontend/data/backcast/**` for SPP, `keepers/SPP.json`, `mechanism-matrix/SPP.js` | **No** — different ISO; and no shard of mine may touch `frontend/**` at all |
| **nyiso223-promo-2025 — artifacts** | NYISO | `claude/nyiso223-*`, NYISO registry/keeper/matrix | **No** — different ISO |
| **caiso-269 shard Y2024 rev3** | **CAISO** | branch `claude/caiso269-2024-rev3`, out-dir `results/calibration/caiso269_lateevening_2024/` | **No** — disjoint branch names and disjoint out-dirs from every shard in §5 |

Four further guarantees, each structural rather than by convention:

1. **Branch names** `claude/caiso270-keeper-<year>` are unique across every branch on `origin`
   (`git ls-remote --heads` at launch: `claude/caiso269-2022`, `claude/caiso269-lateevening-clean`,
   `claude/nyiso223-lane-doc-rescue`, `claude/nyiso223-y2024-r2`, `claude/nyiso223-y2025`,
   `claude/pjm-d4-2-code`, `main`).
2. **Out-dirs** `results/calibration/caiso270_keeper_<year>/` do not exist in `main` or on any branch.
3. **`results/calibration/_shared/CAISO/` is CONTENT-ADDRESSED** (`<name>-<content_hash>.parquet`,
   `scripts/lib/bundle_io.py:148-162`) and per-ISO, so two shards writing the same input write the **same
   filename with the same bytes** — concurrent writers cannot conflict, and no other ISO's session writes
   under `CAISO/`.
4. **Every shard commits ONLY its own bundle path plus `_shared/CAISO/`**, verified by requiring
   `git status --short` to show nothing outside them before the commit.

The **parent** re-fetches `origin/main` immediately before any registration, so SPP-62's and nyiso-223's
registrations land first and are merged rather than raced.

## §7 — WHAT SHARDS ARE FORBIDDEN (rule 32(c)(6), named explicitly in every prompt)

`git add -A` and `git add .`; `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
`prune_iso_runs.py`, `register_forecast_run.py`, and **anything at all under
`frontend/data/backcast/**`**; any edit under `src/` or `scripts/`; `git rebase`, `git pull`, any "sync";
opening a pull request; and deleting any result (rule 31 `[R-RETAIN]` — gitignore, never `rm`).

> **A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE.**

## §8 — WHAT IS NOT DONE HERE

No mechanism is armed, proposed or tested. The `+1 heat-rate-point` residual `FINDING-caiso270` §4 names is
**not** attacked — picking a lever off it without its own charter and its own external driver is the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, and this session does not do it. No other ISO's
keeper shard, matrix shard, status part or calibration log is touched (rule 25 `[R-ISO-SCOPE]`). No year
outside 2022–2025 is solved; `[R-HOLDOUT]` was removed 2026-09-09 so no year needs authorization and
`--holdout-authorized` does not exist. 2020/2021 remain blocked on DATA.
