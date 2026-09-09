# PRECOMMIT — caiso-268: fossil `offer_curve_by_group` bands × **0.92**, on the CURRENT keeper, solved as PER-YEAR SHARDS + ONE SPAN

**Session caiso-268, 2026-09-09.** Parent branch `claude/caiso-calibration-shard-launch-l4v8bj`.
**PUSHED BEFORE THE FIRST LP.** Every number in this document is measured from committed
artifacts at **zero LP cost**; no solver has been called at the moment it is committed.

---

## §1 — The owner instruction, verbatim, and how it is read

> *"Run a Caiso calibration session to move offer curve down 8% from current levels and launch
> shards for each year of the run, attach repo to shards and ensure they don't collide on merge"*

Two halves, and both are executed literally:

* **The mechanism** — every fossil `offer_curve_by_group` band multiplier × **0.92**.
* **The execution** — one child session ("shard") per solve year, each with the repository
  attached, each on its own branch, arranged so their pushes cannot conflict (§6).

**"Current levels" is resolved to the LIVE keeper**, `2026-09-09-caiso-fuelvintage-860-gas`
(bundle `results/calibration/caiso_fuelvintage_span`), and **not** to the caiso-267 ×0.92 arm.
The reason is that caiso-267 was **refused** by the owner on 2026-09-09
(`results/calibration/FINDING-caiso267-fossil-offer-8pct-2026-09-09.md` §9, *"DO NOT PROMOTE"*),
so its cut levels are live nowhere: there is exactly one live CAISO offer curve, and it is the
keeper's. The cut is therefore **×0.92, not ×0.92² = 0.8464**. If the owner intended the deeper
compounding cut, this is the sentence to correct, and it must be corrected **before** any shard
finishes — a re-sized factor after a result exists is the swept selection §3(c) forbids.

## §2 — What is different from caiso-267, stated first, because otherwise this is a re-test

Rule 28 `[R-MECH-MATRIX]`'s DO-NOT-REDO discipline is engaged head-on: ×0.92 on the fossil bands
**has been tested before**, on the `caiso260_demand_vintage` recipe, and adjudicated
DO-NOT-PROMOTE. This run is not that run. **The baseline moved on 2026-09-09**, after
caiso-267 was decided:

| | caiso-267's control (`caiso-260`) | **this run's control (the live keeper)** |
|---|---|---|
| keeper id | `2026-09-06-caiso-260-b1-demand` | **`2026-09-09-caiso-fuelvintage-860-gas`** |
| what changed | — | EIA-860 retiree window 2019+ **and the measured monthly gas LEVEL** (armed) |
| C3a mean LMP | **FAIL** in 2024/2025 (+4.37 / +8.89 / +8.25 %) | **PASS**, all three years |
| determination | CALIBRATED | **CALIBRATED**, single ledgered C3c caveat |

The measured-gas promotion moved the very quantity the cut acts on. **caiso-267's finding
therefore does not carry over**, in either direction, and that is the new evidence rule 28
requires before a cell is re-tested.

### §2.1 — The concern, stated once, at full magnitude, and then not re-argued

**The current keeper already PASSES C3a.** The motivation recorded for the original 8 %
instruction was that the fossil curves *"are overshooting significantly"*; on the caiso-260
recipe they were (C3a FAIL in two years of three), but on the live keeper C3a passes in all
three. A cut of this size is the same order as the whole remaining residual, so the two most
likely outcomes are named here, before the solve:

1. **C3a may cross zero and FAIL on the low side.** caiso-267 measured mean |C3a| 7.17 % → 2.82 %
   against a *larger* starting residual; against a smaller one the same cut overshoots.
2. **C4-2025 is the named knife edge.** The keeper's gas NRMSE is **0.298** against a ≤ 0.300
   tolerance. caiso-267's ×0.92 pushed the same number to **0.308**, and that single supporting-tier
   bound is what took it to NOT-YET. It is the single most likely G-NOFLIP failure here too.
3. **The caiso-267 structural objection is unrefuted and is not re-litigated here.** A flat
   multiplier applies in all 8,760 hours and pulled gas in against imports overnight
   (h0–6 gas error +668 → +1,329 MW). Rule 1 `[R-STRUCT]` is what that objection rests on and it
   still stands; this run measures it again on the new baseline rather than assuming it.

**The instruction was given and is executed.** The factor is the owner's, it is fixed here, and
nothing below argues for a different one.

## §3 — The rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]` carve-out, condition by condition

This is **NOT** a rule 14 `[R-ACCURATE]` measured-input repair and is never described as one.
caiso-266 §7 measured the CAISO CC bands pooled over 2023–2025 and they point the **other** way
(`committed` 1.030 against an armed 1.000; `econ_low`/`econ_high`/`peak` measured at exactly
their armed values). This is the **authorized price-tuning channel** and nothing else.

* **(a) the channel is the band multipliers ONLY.** Exactly four bands per class move —
  `committed`, `econ_low`, `econ_high`, `peak`. **UNTOUCHED:** every `phys_*` key (measured
  physics), `econ_low_share` and `pct_peaking` (the structural shares), every non-band key. No
  adder, offset, haircut, load proxy or gas discount exists anywhere in this run.
* **(b) ONE config across EVERY scored year.** A single factor, **0.92**; a single override file,
  `results/calibration/_caiso268_fossil92_offer_curve.json`, read byte-for-byte by **all four**
  shards. **No per-year value exists and none will be produced.** This is the condition the
  sharding puts under the most pressure, so it is stated twice: sharding splits the *solve*, never
  the *config*. C6 checks it by exact set equality against each bundle's own scored years, so the
  SPAN bundle — the only registerable one — declares `[2023, 2024, 2025]`.
* **(c) set EX ANTE, declared BEFORE the solve, NEVER swept.** The factor is the owner's, handed
  down in §1 before any solve; this document is committed and pushed **before the first LP**.
  **The factor will not be swept.** If the gates do not land where the owner expects, the RESULT
  reports that at full magnitude — it does **not** try 6 % or 10 %. Trying a second factor to make
  a criterion pass is exactly the fitted-mechanism selection condition (c) forbids.
* **(d) merit-order adjustment across classes is INTENDED, not a defect.** A uniform 0.92
  preserves every *relative* band ratio, so the fossil stack's internal merit order is unchanged;
  what moves is fossil against **non-fossil** (hydro, imports, storage, renewables).
* **(e) declared in the attestation + carried in the DOF ledger.** The SPAN bundle's
  `calibration_attestation.json` carries an `authorized_price_tuning` block naming this ruling
  (**C6 FAILS without it**), and the DOF ledger gains **one** free parameter,
  `fossil_offer_band_scale = 0.92`, whose identification source is *"price residual, authorized
  channel (rules 1/13 amendment 2026-09-05); owner instruction 2026-09-09"* — **never** a measured
  input. Per rule 20 `[R-DOF]`'s cross-reference its presence does not by itself make the residual
  it closes an open root-cause issue; every **other** tuned value still would, and no other exists.

**Rule 25 `[R-ISO-SCOPE]`:** applied as a CLI override on a **CAISO** invocation. It touches no
shared default, no `constants.py` value and no other ISO's curve. It is **not** propagated to
ERCOT, PJM, MISO, NYISO, NEISO or SPP.
**Rule 24 `[R-REGISTRY]`:** the resolved curve is recorded verbatim in each bundle's
`run_config.json` (`scenario_config.offer_curve_by_group`) — on-registry and inspectable. No env
var, no hardcoded dict.

## §4 — The 10 classes and 40 bands that move (measured pre-solve, zero LP)

Resolved against the **live keeper's** `run_config.json`. Verified programmatically: every value
below is exactly `0.92 ×` the keeper's, to 1e-12, and the file is **byte-identical
(md5 `fc46efab534211a96600f8664a8b6779`)** to caiso-267's override — which is itself evidence for
condition (b), since the same 40 numbers are being held.

| class | committed | econ_low | econ_high | peak |
|---|--:|--:|--:|--:|
| CC_REGULAR | 1.000 → **0.92000** | 1.066 → **0.98072** | 1.072 → **0.98624** | 1.386 → **1.27512** |
| CC_CHP | 1.000 → 0.92000 | 1.066 → 0.98072 | 1.072 → 0.98624 | 1.386 → 1.27512 |
| CT_PEAKER | 0.991 → 0.91172 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| CT_CHP | 1.100 → 1.01200 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| ST_GAS | 0.810 → 0.74520 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| COAL | 0.900 → 0.82800 | 0.950 → 0.87400 | 1.100 → 1.01200 | 1.450 → 1.33400 |
| COAL_BIT | 0.900 → 0.82800 | 0.950 → 0.87400 | 1.100 → 1.01200 | 1.450 → 1.33400 |
| COAL_LIGNITE | 0.950 → 0.87400 | 1.140 → 1.04880 | 1.150 → 1.05800 | 1.550 → 1.42600 |
| COAL_PRB | 0.950 → 0.87400 | 0.770 → 0.70840 | 1.190 → 1.09480 | 1.480 → 1.36160 |
| COAL_WC | 0.850 → 0.78200 | 0.900 → 0.82800 | 1.020 → 0.93840 | 1.200 → 1.10400 |

**Why 10 and not 13.** The offer-curve router reads exactly `CC_CHP`, `CC_REGULAR`, `COAL`,
`COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`, `CT_PEAKER`, `ST_CHP`, `ST_GAS`. The
three `*_INTERMEDIATE` classes present in the keeper's dict are **not read** and the
`--offer-curve-json` validator refuses them (caiso-267 §D.1, learned the hard way). They are also
inert in substance — `cc_intermediate_split` and `ct_intermediate_split` are both `false`, so all
three carry **zero** CAISO energy in every year. `ST_CHP` is readable but has **no entry in the
keeper's resolved curve**, so it is **not added**: adding it would inject a band set the keeper
never had, which is a new parameter rather than a cut of an existing one.

**Which classes actually carry CAISO energy** (keeper P1 `class_hourly` sidecars, TWh,
2023/2024/2025): CC_REGULAR 48.40/46.10/40.33 · CC_CHP 8.48/7.53/7.56 · CT_PEAKER 2.04/1.67/0.79 ·
CT_CHP 1.24/1.23/1.20 · ST_GAS 0.119/0.193/0.022 · COAL 0.090/0.045/0.076. The four COAL_* variants
carry zero; they are declared so the declaration is complete rather than partial.

**Two per-plant bypasses that blunt the cut, disclosed pre-solve.**
`caiso_st_gas_committed_measured` and `caiso_st_gas_peak_measured` are both armed and resolve
those bands **per plant** for `ST_GAS_PEAKER_PLANTS` members, bypassing `offer_curve_by_group`
entirely. The ST_GAS `committed` and `peak` cuts therefore reach only the non-bypassed units.
ST_GAS is 0.02–0.19 TWh — a completeness note, not a material one.

**The `peak_ladder` follows the cut automatically and is NOT a separate parameter.** `CC_REGULAR`
and `CT_PEAKER` carry five equal-capacity rungs that the `caiso_offer_surface_conditional` split
writes as uniform copies of the resolved `peak`; that split runs **after** the override
(`pipeline/backcast_config.py`), so it rebuilds the ladder from the post-override value. Verified
on the live keeper pre-solve: the ladders are `[[0.2, 1.386]×5]` and `[[0.2, 1.154]×5]` — uniform
copies of `peak` in both classes.

**One consequence a reader is owed** (carried forward from caiso-267 §5, re-verified against this
keeper): the cut puts `CT_PEAKER.committed` 0.991 → 0.912 below its own measured
`phys_committed` 0.991, and `CT_CHP.committed` 1.100 → 1.012 below its 1.073. Three more were
already below theirs on the keeper and are deepened. `phys_*` is inert in this recipe
(`gas_offer_net_revenue_margin = false`) and is **not touched**, so no LP row changes — but the
model now offers committed gas below its own measured fuel cost, and that is worth saying.

## §5 — Rule 29 `[R-SCREEN]`: the screen year, the gates, and the control

**SCREEN YEAR = 2023**, fixed here, before any screen runs. It is named on the mechanism's own
**largest measured footprint** — $ of offer re-pricing and raw fossil energy, both maximal in
2023 (caiso-267 §E, recomputed on the same committed sidecars: 60.280 TWh fossil, ~$171.5 M of
offer re-pricing, mean Δmc $2.845/MWh) — and **never** on a residual. The check that matters:
2023 is simultaneously the year with the **smallest** C3a residual, so a residual-driven choice
would have picked a different year. That is the evidence the choice was not residual-driven.

**Pre-solve prediction, so the screen has something to falsify.** Mean Δmc on 2023 fossil energy
is $2.845/MWh, so λ should fall by an amount of order $2–3/MWh in gas-marginal hours, and fossil
energy should *rise* modestly as fossil displaces imports and hydro at the margin. A move an order
of magnitude away from that, or in the wrong direction, means the mechanism is not doing what its
own arithmetic says.

**The gates are STRUCTURAL and STOP-ONLY. They may KILL the arm; they may NEVER promote it, and
none of them references the target residual** (a gate reading *"did C3a improve"* would be exactly
the selection rule 1(c) forbids, one year at a time):

* **G-IDENT** — the arm differs from the control by the offer curve and **nothing else**: demand,
  renewables, hydro, imports, outages and fleet capacity byte-identical. Any other moved input
  **STOPS** the shard.
* **G-FOOT** — the response is confined to the rows the mechanism claims: fossil classes and the
  prices they set. Non-fossil *capacity* and *availability* unchanged (their dispatch may move —
  that is the merit order working).
* **G-DIR** — |Δλ| lands in **[$0.5, $8.0]/MWh** and is **negative** (a cut cannot raise the annual
  mean price). Outside that band, arithmetic and LP disagree and the shard STOPS to find out why.
* **G-NOFLIP** — no **non-target load-bearing** criterion flips PASS → FAIL (C1, C2, C3b, C6, C8).
  **C3a is the target and is exempt in both directions.** **C3c is exempt** — rubric v3.6, already
  the keeper's single ledgered caveat. **C4 is supporting tier and is NOT a G-NOFLIP stop** — it is
  measured, reported at full magnitude, and carried to the owner as the promotion question (§2.1
  item 2 names it in advance so a post-hoc reading cannot be presented as a prediction).

**G-CTRL: form 4 is CLAIMED, and NO CONTROL SOLVE IS SPENT.** Rule 29(b) makes the keeper's
committed bundle the control. The keeper is **four days old at most** (registered 2026-09-09,
`git_sha 873f7564`), so unlike caiso-267 — which faced a 94-file / +46,838-line drift it honestly
refused to classify — the drift surface here is small enough to audit. **G-DRIFT is executed by the
SPAN shard as its Card 0**, before its first LP: `git diff 873f7564 HEAD` over `src/market_sim`,
`scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference`, **every changed hunk classified INERT with its
reason cited, or LIVE**. All INERT ⇒ form 4 holds and the committed keeper is the control. **A LIVE
hunk is the only thing that earns a control solve**, and then only for the years the screen needs.
A "files changed, therefore void" heuristic with no audit behind it is not a reason to spend an LP.

## §6 — The shard plan, and why there are FOUR and not three

**The user's instruction is executed literally — one shard per solve year.** A fourth shard is
added because the per-year shards **cannot** produce a registerable bundle, and that is measured,
not assumed.

### §6.1 — The measured reason hand-composition is refused

`docs/RESULT-caiso-fuelvintage-2026-09-09.md` **§6a** records this lane trying exactly the
compose-from-shards route four hours ago and getting a **broken measurement**: T1 (2023-2024) and
T2 (2025) carried **different year-scoped `eia923` / `eia930` / `campd` snapshots**, so the composed
bundle scored 2025 against T1's inputs and C4-2025 came back **`r=None, NRMSE=8.406`** against the
keeper's 0.877 / 0.298. That lane re-solved as one invocation, C4 then passed, and it recommended
the handoff's §A1 sharding guidance be amended to say so.

**This PRECOMMIT adopts that recommendation as a binding constraint: rule 16 `[R-ALLYEARS]`'s "one
bundle" also means ONE INPUT SNAPSHOT, and hand-composition across per-year shards is not
equivalent to it.** Registering a hand-composed bundle here would repeat a defect this lane has
already found and fixed.

### §6.2 — What each shard is for

| shard | branch | years | bundle | registerable? |
|---|---|---|---|---|
| **Y2023** (also the rule-29 SCREEN) | `claude/caiso268-y2023` | 2023 | `caiso268_fossil92_y2023` | **NO** — probe |
| **Y2024** | `claude/caiso268-y2024` | 2024 | `caiso268_fossil92_y2024` | **NO** — probe |
| **Y2025** | `claude/caiso268-y2025` | 2025 | `caiso268_fossil92_y2025` | **NO** — probe |
| **SPAN** | `claude/caiso268-span` | 2023 2024 2025, **ONE invocation, sequential** | `caiso268_fossil92_span` | **YES — the only one** |

The per-year shards are **throwaway diagnostic probes** (rule 29 clause (2)): never registered,
never a keeper, never quoted as a keeper number. They earn their LP by returning fast, in parallel,
with the structural gates — a 2025-only solve answers in a fraction of the span's wall clock, and
any shard tripping G-IDENT / G-FOOT / G-DIR kills the arm before the span finishes. Their bundles
are **gitignored** in the same commit as this document, which is what discharges rule 29(c)'s
delete-before-merge duty **in full**; per rule 31 `[R-RETAIN]` they are **never `rm`'d** — the
ercot-255 incident is why.

All four shards run **concurrently**. Rule 12 `[R-PARALLEL]`'s ~2-simultaneous cap is a
**per-container RAM** limit and each shard owns its own container (handoff §A1 states this
explicitly), so it does not bind across them; **years within the SPAN invocation stay sequential,
always**, and the SPAN shard is forbidden from parallelizing its year loop.

### §6.3 — Non-collision on merge: the mechanism, not the hope

Every shard is pinned to **one immutable commit SHA** (never a branch name — handoff §A4: the CCR
source-processing worker resolves against a repo view that lags a freshly-created ref, which failed
all five shards of the previous launch with `ref_not_found`). Each shard branches to its own name
and merges `origin/main` before pushing (§A8).

Collisions are prevented by **disjoint write sets**, declared here and repeated in every shard
prompt:

* **Every shard may write ONLY**: its own bundle dir (`caiso268_fossil92_<its own suffix>/`) and
  its own uniquely-named doc (`docs/RESULT-caiso268-<shard>-2026-09-09.md`,
  `docs/ADDENDUM-caiso268-<shard>-*.md`). Nothing else.
* **NO shard may write** — this is the collision surface, and it is closed by prohibition:
  `.gitignore` · `results/calibration/_caiso268_fossil92_offer_curve.json` · this PRECOMMIT ·
  `CLAUDE.md` · anything under `src/` or `scripts/` · any **other** shard's bundle or doc.
* **ONLY the SPAN shard may write the shared CAISO surfaces**, and only after its own solve:
  `frontend/data/backcast/registry/*` · `frontend/data/backcast/runs/*` ·
  `frontend/data/backcast/bench/CAISO/*` · `frontend/data/backcast/keepers/CAISO.json` ·
  `frontend/data/backcast/status/CAISO.js` · `docs/codebase-site/data/mechanism-matrix/CAISO.js` ·
  `docs/calibration-log/caiso.md`. The **bench part is the sharp one**: any CAISO solve rewrites
  `bench/CAISO/<year>.json.gz`, so three year-shards committing bench parts would collide on all
  three files at once. They are forbidden from committing it.
* **Rule 25 `[R-ISO-SCOPE]`**: no shard writes another **ISO's** keeper shard, matrix shard, status
  part or calibration log. CAISO only.

## §7 — Governance carried into every shard

* **Rule 15 `[R-DASHBOARD]`** — the SPAN bundle is registered **whatever it says**, keeper or
  rejection, in the session that produces it. The per-year probes are never registered.
* **Rule 22 `[R-HOLDOUT]`** — 2023, 2024 and 2025 are **all training tier**. No marker, no
  `--holdout-authorized`, no freeze question arises. **No shard may solve, score or register 2019,
  2020, 2021, 2022 or H1-2026**; if one thinks it needs a holdout year, it stops and asks.
* **Rule 31 `[R-RETAIN]`** — **nothing solved is deleted.** Gitignore discharges delete-before-merge;
  `rm` does not. The promotion question is put to the owner **explicitly** before the session ends,
  together with the statement that the bundles live on local disk in ephemeral containers.
* **Rule 28 `[R-MECH-MATRIX]`** — `offer_curve_by_group` is an existing matrix row; **the SPAN shard
  alone** updates its CAISO cell with this session's evidence. No new `ScenarioConfig` field is
  created, so duty (c) does not fire.
* **Rule 27 `[R-PUSH]`** — no source file ≥ 300 lines is rewritten by any shard. The only code
  touched in this commit is a `.gitignore` block.
* **Rule 12 `[R-PARALLEL]`** — separate invocations concurrent, years sequential within one.

**Next number: caiso-269.**
