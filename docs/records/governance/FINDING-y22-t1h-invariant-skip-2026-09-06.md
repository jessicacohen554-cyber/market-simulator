# FINDING — Y-22: the T1-H FC-1 blind spot is a dead branch in `_invariant_map` — it reads `art["hindcast"]["invariants"]`, but `art["hindcast"]` is the capacity-hindcast **score.json**, which has never carried an `invariants` key in any run (0 of 28); the record lives in a different tree entirely. Repaired, FC-1 reads FAIL on 11 of the 20 T1-H runs. On the PJM/NYISO I7 rows the breach is REAL but its bar is PARTLY WRONG: I7 grades the LP's measured hindcast peak while the floor and backstop defended the screen peak — 1,807 MW of the D57 run's 3,020 MW shortfall is a bar the defending mechanisms were never given. NOT declared; routed.

**Lane:** Y-22, Model Audit & Release-Finalization Program — "T1-H invariant skip".
**Branch:** `claude/y22-t1h-invariant-skip-466y6t`, off `origin/main` `1aab49a0`.
**Date:** 2026-09-06. **Model:** `claude-opus-5`. **Data profile:** `code` (no solve, no LP).

**Refusals honoured.** No solve, no score, no re-score, no registration, no prune. Nothing was
added to `invariant-failures.json`. `ff-verdicts.json`, `program-status.json`, every keeper shard,
marker and freeze file are read-only in this session and unmodified. No invariant definition,
threshold or exemption was touched — `scripts/check_forecast_invariants.py` and
`scripts/forecast_verdict.py` are **byte-unchanged**. This lane changes **no repository file
except this document**: the repair is diagnosed and specified, not applied, because applying it
re-grades registered runs and that is the forecast-orchestrator desk's call, not this lane's.

---

## 0. Verdict

**The lookup that misses is `scripts/forecast_verdict.py:536-539`** — `_invariant_map`'s third
source branch. Its docstring calls the object "a hindcast sidecar", but the object it is handed is
the **capacity-hindcast `score.json`** from the bundle cache. Those are two different files in two
different trees, and `score.json` has never carried an `invariants` key — **0 of 28** such files
under `results/hindcast/**`. The branch has therefore never fired for any run, which is why
**47 of 47** `t1h` verdict keys read `SKIPPED` with one identical detail string while `t1f` (which
passes `--invariants`) and `t3` read real verdicts. It is a **namespace** miss: right key name,
wrong object, wrong tree.

**Repaired, FC-1 is not cosmetic.** Handed the block it already has, FC-1 reads **11 FAIL / 7 PASS
/ 2 CAVEAT** across the 20 T1-H runs, where today all 20 read SKIPPED. FC-1 is `OPTIONAL` at t1h,
and the rubric's own semantics are that absence does not hold but *"a present-and-FAIL optional
category still gates"* — so the repair converts 11 non-gating absences into 11 **gating** FAILs.

**On the substantive half: I7 fails on these runs for a real reason, and the reason is three
things, only the third of which is new.** (A) `capacity_market_clearing` armed for the ISO is the
single field separating every failing run from its passing sibling; it produces economic exit waves
of 3.5–18.1 GW that the sibling does not have. (B) The step-6 adequacy backstop is bounded by the
BLK-10 growth ladder — it built **exactly 1,012.8 MW** in all four PJM runs against gaps ranging
3,020–6,623 MW, i.e. need-independently — and its docstring discloses that a residual carries to
next year, which in a terminal year does not exist. (C) **New, and the reason these rows are not
declarable as they stand:** I7 grades `adequacy_requirement_mw` re-derived from the LP's *measured*
hindcast load, while the reliability floor and the backstop defended the *screen* peak. capx D52's
own ledger comment says these differ "in every hindcast year that is not the weather year", and the
committed `screen_*` fields make it measurable: on `pjm-…-d57-clearing` 2025 the screens defended
148,798 MW while I7 grades 150,605 MW — **1,807 MW, 60 % of that run's entire shortfall, is a bar
the defending mechanisms were never given.** The signature is falsifiable and it holds:
`weather_year` is 2024 in these runs, `screen_peak == measured peak` only in 2024, and NYISO's
curve-ON run **passes 2024 and fails 2023 and 2025** — the two non-weather years.

**The four (now five) T1-H rows are NOT declared. The gate stays red at 6.** Declaring a shortfall
whose bar is partly wrong would record a supply-side defect for a measurement seam, which is the
misattribution the ledger exists to prevent.

---

## 1. The lookup that misses, quoted at the line

### 1.1 The branch

`scripts/forecast_verdict.py`, `_invariant_map` — the whole source resolution, lines 529-539:

```python
    rows: list | None = None
    inv = art.get("invariants")
    if isinstance(inv, list):                                    # 1: --invariants
        rows = inv
    elif isinstance(art.get("summary"), dict) and isinstance(    # 2: full-horizon summary
        art["summary"].get("invariants"), list
    ):
        rows = art["summary"]["invariants"]
    elif isinstance(art.get("hindcast"), dict) and isinstance(   # 3: <- THE DEAD BRANCH (536)
        art["hindcast"].get("invariants"), list
    ):
        rows = art["hindcast"]["invariants"]                     #    (539)
```

and its docstring, line 525, naming the object it believes it is reading:

```
    hindcast sidecar's embedded ``invariants`` (keyed ``ident``). Returns ``None``
```

### 1.2 Why the branch is dead: `art["hindcast"]` is not the hindcast sidecar

| | what the docstring names | what `art["hindcast"]` actually is |
|---|---|---|
| file | the registration sidecar | the capacity-hindcast score |
| path | `frontend/data/hindcast/<run_id>.json` | `results/hindcast/<run_id>/<ISO>/<cache_key>/score.json` |
| written by | `register_hindcast.py::build_sidecar` (152-160) | `score_capacity_hindcast.py` |
| carries `invariants`? | **yes — 14 rows, keyed `ident`** | **no — 0 of 28 files** |

Three lines fix the identification, and they agree with each other:

```
scripts/forecast_verdict.py:359     "hindcast": _load_json(args.hindcast_score),
scripts/forecast_verdict.py:1999    ap.add_argument("--hindcast-score", dest="hindcast_score",
                                                    help="hindcast score.json (FC-3)")
scripts/forecast_verdict.py:45      --hindcast-score results/hindcast/<run_id>/score.json \   (usage block, T1-H)
```

`--hindcast-score` is the FC-3 input and nothing else. The T1-H canonical command supplies exactly
`--hindcast-score` and `--run-config` — no `--summary`, no `--invariants` — so branches 1 and 2 are
`None` by construction and branch 3 is the only one that can fire. It cannot, because the file it
tests has no such key. Verified by enumeration over the whole tree:

```
$ python - <<'PY'   # read-only census
  score.json files under results/hindcast/** WITH an 'invariants' key: 0
  score.json files under results/hindcast/** WITHOUT:                 28
PY
```

The record the audit reads is produced on a different code path at a different time — at *hindcast
registration*, from the dispatch cache — and lands in the dashboard data tree the verdict scorer is
never pointed at:

```python
# scripts/register_hindcast.py, build_sidecar, 152-160
        invariants = [
            {"ident": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
            for r in CI.run_single(cache_dir)
        ]
    out = { "run_id": run_id, "meta": meta, "score": score, "invariants": invariants, ... }
```

That list is keyed `ident` — **byte-identical in shape to branch 1's `--invariants` input**, which
is why the repair needs no new parsing, only the right object.

### 1.3 The proof it has never fired, across the whole board

`frontend/data/forecast/ff-verdicts.json`, FC-1 category status by tier (read-only):

| tier | PASS | CAVEAT | FAIL | **SKIPPED** | how FC-1 is fed at this tier |
|---|--:|--:|--:|--:|---|
| t1f | 6 | 3 | 23 | **0** | `--invariants` / `--summary` → branch 1 or 2 |
| t3 | 0 | 0 | 8 | **0** | `--summary` → branch 2 |
| t1x | 1 | 0 | 1 | **13** | mixed |
| **t1h** | 0 | 0 | 0 | **47** | branch 3 only — **never fires** |

Every one of the 47 carries the same string, with no exceptions:

```
"detail": "no committed invariant record (summary.invariants / --invariants)"
```

A 100 % miss confined to exactly the one tier that depends on exactly the one untested branch is
not a distribution of run properties. It is a dead code path.

### 1.4 Why it was never caught

`tests/scoring/test_forecast_verdict.py::FC1Tests` has six tests. Every one of them passes
`"t1f"` as the tier, and they cover branch 1 (`_art(invariants=…)`) and branch 2
(`_art(summary=…)`) — including a test named `test_summary_embedded_id_key` for branch 2's
key-shape quirk. **No test ever populates `hindcast`.** The one branch that exists solely to serve
t1h is the one branch with no test, at the one tier no FC-1 test exercises.

### 1.5 The second seam: the register script holds both facts at once

`scripts/register_forecast_run.py::build_entry` reads the verdict and the invariants into the same
scope, four lines apart, and writes them into the same dict:

```python
    verdict = verdicts.get(vkey) if vkey else None      # 714  -> fc["FC-1"] == "SKIPPED"
    fc = _fc_summary(verdict)                           # 715
    ...
    invariants = _full_invariants(sidecar)              # 718  -> 14 rows
    ...
        "fc": fc,                                       # 752
        "has_score": has_score,                         # 753
        "has_invariants": bool(invariants),             # 754
        "has_ledger": bool(year_summary),               # 755
        "n_inv": len(invariants),                       # 756
```

So each registry entry for these runs asserts, simultaneously, `fc["FC-1"] = "SKIPPED — no
committed invariant record"` and `has_invariants: true, n_inv: 14`. The contradiction is not
buried across two systems; it is adjacent keys in one object.

---

## 2. What FC-1 reads once it can see the record

Method (read-only, nothing written): `scripts/forecast_verdict.py` imported **unmodified**;
each sidecar's own `invariants` list passed through the branch-1 key shape, which §1.2 establishes
is the same shape; `score_fc1` called at tier `t1h`. This is arithmetic on committed artifacts, not
a re-score — no verdict, sidecar, payload or registry file was written.

| population | today | once FC-1 reads the record |
|---|---|---|
| all 52 sidecars with a committed block | — | **27 FAIL / 19 PASS / 6 CAVEAT** |
| the T1-H family (`kind=hindcast`, 20 runs) | **20 SKIPPED** | **11 FAIL / 7 PASS / 2 CAVEAT** |

The 11 T1-H FAILs, across five ISOs:

| ISO | run | FC-1 |
|---|---|---|
| CAISO | `caiso-2021-2025-realized-t1h-d46` | FAIL `['I7','I9']` |
| ERCOT | `ercot-2021-2025-realized-t1h-d46` | FAIL `['I3']` |
| ERCOT | `ercot-2021-2025-realized-t1h-d4m` | FAIL `['I3']` |
| MISO | `miso-2021-2025-realized-t1h-d27` | FAIL `['I3']` |
| MISO | `miso-2021-2025-realized-t1h-d46` | FAIL `['I7']` |
| MISO | `miso-2021-2025-realized-t1h-d53-sectorgate` | FAIL `['I7']` |
| NYISO | `nyiso-2021-2025-realized-t1h-d45r-curveon` | FAIL `['I7']` |
| PJM | `pjm-2021-2025-realized-t1h-d45` | FAIL `['I7']` |
| PJM | `pjm-2021-2025-realized-t1h-d45r` | FAIL `['I7']` |
| PJM | `pjm-2021-2025-realized-t1h-d57-clearing` | FAIL `['I7']` |
| PJM | `pjm-2021-2025-realized-t1h-d62-pubbar` | FAIL `['I7']` |

plus two CAVEATs (`neiso-…-t1h-d45r`, `nyiso-…-t1h-d45r`, both `WARN ['I12']`).

**This changes gating, not only display.** `APPLICABILITY["FC-1"]["t1h"] = OPTIONAL` (line 125),
and the rubric's own definition of that token (line 99) is:

> `OPTIONAL` — scored if artifacts present; absence recorded, does NOT HOLD; a
> present-and-FAIL optional category still gates ("failed evidence never promotes").

Today's SKIPPED is an *absence* and does not hold. A repaired FC-1 FAIL is *present-and-FAIL* and
**does** gate. Eleven T1-H runs across five ISOs would acquire a gating category they have never
had. That is why this is worth a specified repair rather than a string edit, and why applying it is
the orchestrator desk's decision (§4.2) rather than this lane's.

---

## 3. The I7 verdict per run, with its cause

### 3.1 It is not a checker artifact — checker and model agree exactly

Every ledger year carries the model's own `adequacy_requirement_mw`. Recomputing the checker's
`resolve_adequacy_requirement_mw(cfg, iso, peak, year)` from each run's committed
`run_config.json` reproduces it to **delta 0.000 MW in every year of every run**, and reproduces
each sidecar's committed I7 detail string digit-for-digit. The D-1 checker repair holds: the
checker and the ledger grade the same bar. §3.4 is about a *third* bar — the one the mechanisms
actually defended.

### 3.2 The per-year reconstruction (committed evolution ledgers, read-only)

`accredited = peak × (1 + reserve_margin)`; `requirement` as above. **Bold = I7's failing years.**

| run | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| `pjm-…-d45` | 148,559 ≥ 130,295 | 151,599 ≥ 128,566 | 137,419 ≥ 133,371 | **138,286 < 144,632 (−6,346)** |
| `pjm-…-d45r` | 148,039 ≥ 130,295 | 146,228 ≥ 128,566 | 137,426 ≥ 133,371 | **138,009 < 144,632 (−6,623)** |
| `pjm-…-d45r-fixed` *(sibling, PASSES)* | 148,039 | 146,228 | 146,900 | 149,836 ≥ 144,632 (+5,204) |
| `pjm-…-d57-clearing` | 186,643 ≥ 163,023 | 172,353 ≥ 160,904 | 172,627 ≥ 166,810 | **147,585 < 150,605 (−3,020)** |
| `pjm-…-d62-pubbar` *(new since Y-19)* | 186,643 ≥ 163,023 | 170,771 ≥ 160,904 | 171,451 ≥ 166,810 | **145,855 < 150,605 (−4,750)** |
| `nyiso-…-d45r-curveon` | 36,145 ≥ 33,382 | **31,493 < 32,612 (−1,119)** | 32,578 ≥ 31,300 | **32,712 < 34,395 (−1,683)** |
| `nyiso-…-d45r` *(sibling, PASSES)* | 36,145 | 34,745 | 35,829 | 36,439 ≥ 34,395 (+2,044) |

### 3.3 Cause (A) — the trigger is `capacity_market_clearing`, and it is one field

Y-19 attributed the two passing siblings to `capacity_clearing_posture`. Differencing all seven
sidecar `meta` blocks sharpens it to the field that actually gates the mechanism:

| run | `capacity_market_clearing` for its own ISO | I7 |
|---|---|---|
| `pjm-…-d45` / `-d45r` / `-d57-clearing` / `-d62-pubbar` | **True** (`by_iso: {PJM: True}`) | FAIL |
| `pjm-…-d45r-fixed` | **False** (`by_iso: None`, posture `fixed_net_cone`) | **PASS** |
| `nyiso-…-d45r-curveon` | **True** (`by_iso: {NYISO: True}`, posture `forced_curve`) | FAIL |
| `nyiso-…-d45r` | **False** (`by_iso` carries no NYISO key) | **PASS** |

Perfect separation, both directions, both ISOs. The mechanism is visible in the retirement ledgers:
the endogenous clearing price enters the going-forward screen and an exit wave follows.

| run | economic retirements, 2023 | 2024 |
|---|---|---|
| `pjm-…-d45` | — | **86 units / 18,137 MW** |
| `pjm-…-d45r` | — | **47 units / 11,659 MW** |
| `pjm-…-d45r-fixed` *(clearing OFF)* | **0** | **0** (4 announced / 244 MW only) |
| `pjm-…-d57-clearing` | **151 units / 4,384 MW** | 8 / 441 MW |
| `pjm-…-d62-pubbar` | 10 units / 1,200 MW | 0 |
| `nyiso-…-d45r-curveon` | **21 units / 3,496 MW** | 0 |
| `nyiso-…-d45r` *(clearing OFF)* | **0** | 0 |

The clearing-OFF siblings retire **nothing** economically in any year. This half is real, it is
mechanism-attributable, and it is what D48 predicted would not happen: *"I7 still PASS wherever it
passes"* → *"I7 / I12 ungradable (FC-1 SKIPPED at t1h)"*.

### 3.4 Cause (B) — the backstop fires and is capped need-independently

The step-6 adequacy backstop resolves **ON** for capacity-market ISOs and it did fire — the 2025
PJM ledgers carry a `"source": "reserve_backstop"` addition. Its size is the finding:

| run | 2025 I7 gap | backstop built |
|---|--:|--:|
| `pjm-…-d45` | 6,346 MW | **1,012.8 MW** |
| `pjm-…-d45r` | 6,623 MW | **1,012.8 MW** |
| `pjm-…-d57-clearing` | 3,020 MW | **1,012.8 MW** |
| `pjm-…-d62-pubbar` | 4,750 MW | **1,012.8 MW** |

Identical to the tenth of a MW across gaps that differ by 2.2×. It is not sizing on need; it is
the BLK-10 growth ladder: `entry_rate_caps_mw["gas_ct"] = ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) ×
prior-max annual gas_ct build` = 2.0 × 506.4 MW (`runner.py:2254-2259`; `entry_rate_limits=True` in
every one of these runs). `apply_reserve_margin_build`'s docstring discloses the trade and cites the
measurement behind it:

> a deficit larger than the year's deliverable throughput carries to next year's screen … the
> measured RC-1A/BLK-10 signature (PJM 2025: 6.43 GW pre-R-NEW, 2.5 GW post-R-NEW, vs actual
> 0.447 GW)

**In the terminal year of a hindcast there is no next year to carry into.** So an absolute per-year
invariant and a deliberately multi-year-paced backstop cannot both be satisfied at the horizon
edge. That is a disclosed design trade, not a bug — but nobody has ever had to reconcile it with
I7, because I7 has never been graded at T1-H.

The step-3 reliability floor is not the gap here and should not be blamed for it: `floor_retained`
is empty in every year of every run, correctly — in 2024 the exit waves land **above** the year's
requirement (d45 +4,048, d45r +4,055 MW), and in 2025 only one 1 MW announced unit retires. The
2025 breach is created by requirement growth, not by retirement: peak +7,439 MW **and** 2025 being
PJM's first published-FPR delivery year, which lifts the requirement/peak ratio 0.8710 → 0.9008
(+4,784 MW on the d45 family basis).

### 3.5 Cause (C) — **NEW**: I7 grades a bar the defending mechanisms were never given

`runner.py:2094-2104` says it in the code, as a capx D52 observability note:

> the ledger's ``peak_demand_mw`` / ``adequacy_requirement_mw`` below are re-derived from the LP's
> own (in a hindcast: measured) load, so **in every hindcast year that is not the weather year they
> are NOT the values the screens saw**

The reliability floor (`_apply_reliability_floor`, `retirements.py:2379`) and the backstop
(`adequacy.py:896`) both resolve their requirement on the **screen** peak. I7 grades the ledger's
**measured** peak. The D57/D62 bundles are late enough to carry the D52 `screen_*` fields, so the
gap is measurable rather than argued:

| `pjm-…-d57-clearing` | screen peak | screen requirement *(what the floor + backstop defended)* | ledger peak | ledger requirement *(what I7 grades)* | bar gap |
|---|--:|--:|--:|--:|--:|
| 2023 | 147,800 | 161,117 | 147,605 | 160,904 | +213 |
| **2024** *(weather year)* | **153,121** | **166,810** | **153,121** | **166,810** | **0** |
| 2025 | 158,633 | 148,798 | 160,560 | 150,605 | **+1,807** |

**1,807 MW of the 3,020 MW shortfall — 60 % — is a bar the mechanisms never saw.** The signature is
falsifiable and it holds: `weather_year: 2024` in these runs, the two bars coincide **only** in
2024, and NYISO's curve-ON run **passes 2024 and fails 2023 and 2025** — the two non-weather years,
with zero backstop build in either, consistent with screens that saw no gap. (The d45/d45r/NYISO
bundles pre-date D52 and carry no `screen_*` fields, so the gap is inferable there but not
measurable from committed artifacts; that is itself an argument for §4.2's item 3.)

I7's docstring claims *"Checker and model now measure the same quantity"*. True of checker vs
ledger (§3.1). **False of ledger vs screens in any hindcast year that is not the weather year** —
and every one of the six failing years across these runs is a non-weather year.

### 3.6 The verdict per run

| run | I7 | is the breach real? | cause |
|---|---|---|---|
| `pjm-…-d45` | FAIL 2025, −6,346 | **partly** | (A) 18.1 GW exit wave 2024 + FPR basis step + peak growth; (B) backstop capped 1,012.8; (C) bar gap present, unmeasurable pre-D52 |
| `pjm-…-d45r` | FAIL 2025, −6,623 | **partly** | as d45, +277 MW from the dates channel — deepens, does not cause |
| `pjm-…-d57-clearing` | FAIL 2025, −3,020 | **partly — 60 % is bar** | (C) measured 1,807 MW; residual ~1,213 MW real, (A)+(B) |
| `pjm-…-d62-pubbar` | FAIL 2025, −4,750 | **partly** | as d57, same screen bars |
| `nyiso-…-d45r-curveon` | FAIL 2023 −1,119, 2025 −1,683 | **partly** | (A) 3,496 MW exit wave 2023; backstop never fires; both failing years are non-weather, the passing year is the weather year |

**Not a phantom, and not declarable as it stands.** Every failing run genuinely ends the year below
its own ledger requirement, and (A) is a live signal about arming `capacity_market_clearing` that
no lane has graded. But part of each shortfall is measured against a bar the defending mechanisms
were never handed, and declaring the row would file that measurement seam under a supply-side
cause — the same misattribution Y-19 refused when it declined to declare these under `d18_note`.

---

## 4. What is owed, and to whom

### 4.1 Not declared

The T1-H I7 rows stay undeclared and the gate stays red at 6. §3.5 is a finding about the
*measurement*, so a declaration written today would have to name a cause that §3.5 shows is only
partly the cause. Rule 15's discipline holds: git history is the record; this document is the
finding.

### 4.2 Routed

| # | item | to | what is owed |
|---|---|---|---|
| 1 | **The dead branch, §1.** `_invariant_map` line 536-539 reads `art["hindcast"]["invariants"]` from a file that never has one. | **forecast-orchestrator desk** | Decide the repair and who applies it: either load the registration sidecar (`frontend/data/hindcast/<run_id>.json`) as a fourth source, or add `--invariants` to the canonical T1-H command, or make the SKIPPED string tell the truth. §2 is the blast radius: **11 T1-H runs across five ISOs acquire a gating FC-1 FAIL**, so this is a re-grade of registered runs, not a string fix. Add the missing branch-3 test at tier `t1h` whichever way it lands (§1.4). |
| 2 | **Cause (C), §3.5 — I7 grades the measured peak, the floor and backstop defend the screen peak.** | **capx director desk** (D52 owns the seam) | Adjudicate which bar I7 *should* grade in a hindcast. Zero-LP: the D57/D62 `screen_*` fields already carry both. If the screen bar is the right one, four of the five rows shrink and one may clear; if the measured bar is right, the mechanisms need the measured peak. Either way the two must be the same bar before an I7 row at T1-H means what it says. |
| 3 | **`screen_*` backfill.** The d45/d45r/NYISO bundles pre-date D52 and cannot be differenced. | **capx director desk** | Note only: any future T1-H registration should carry the `screen_*` block so an I7 row is decomposable without a re-solve. No re-solve is requested here. |
| 4 | **Cause (A), §3.3 — `capacity_market_clearing` is the one field, exit waves 3.5–18.1 GW.** | **capx director desk** | Y-19's routing stands and is now sharpened from `capacity_clearing_posture` to `capacity_market_clearing` per ISO, with the exit-wave counts. D48's *"I7 still PASS wherever it passes"* is refuted on committed artifacts. |
| 5 | **Cause (B), §3.4 — absolute per-year I7 vs the multi-year-paced backstop at the horizon edge.** | **forecast-orchestrator desk** | A rubric question, not a bug: decide whether I7's terminal year is gradable at T1-H at all when the backstop is rate-limited by design. Do not resolve it by weakening I7. |
| 6 | **`caiso-2026-2030-d60-arm`** (registered 2026-09-06, after Y-19) — FC-1 `FAIL ['I12','I7']`, undeclared. | **records lane** | **Not this lane's object.** It is `t1f`: its FC-1 was scored, is visible in `ff-verdicts.json` (`caiso-t1f` reads `FAIL ['I12','I7']`), and its lane read it. An ordinary declaration with the D60 finding, not a blind spot. |

### 4.3 Two arrivals since Y-19

Y-19 named 4 runs at `5fdd4374`; at `1aab49a0` the gate names **6**. Neither is a regression in
this lane's object, and both are stated above: `pjm-2021-2025-realized-t1h-d62-pubbar` is a **fifth**
T1-H I7 row in the same family and is treated as part of the object throughout this document
(§3.2/§3.4/§3.6), and `caiso-2026-2030-d60-arm` is the t1f records gap of §4.2 item 6.

This also strengthens Y-19 §4.35's argument against a records pass: the PJM T1-H I7 residual has
now re-appeared in a **fourth** generation of runs (`k162`/`exante`/`verified-exits` → `d45`/`d45r`
→ `d57` → `d62`), against a requirement that has moved three times, and it has still never been
graded by anything but this audit.

---

## 5. Reproduction

```
$ git rev-parse --short HEAD
1aab49a0

$ uv run --frozen python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast
forecast-invariant artifact audit: 52 sidecar(s) with an invariants block, 728 record(s), 42 FAIL(s) declared
forecast-invariant artifact audit FAILED:
  - caiso-2026-2030-d60-arm:                     FAILs ['I12', 'I7'] are not declared ...
  - nyiso-2021-2025-realized-t1h-d45r-curveon:   FAILs ['I7'] are not declared ...
  - pjm-2021-2025-realized-t1h-d45:              FAILs ['I7'] are not declared ...
  - pjm-2021-2025-realized-t1h-d45r:             FAILs ['I7'] are not declared ...
  - pjm-2021-2025-realized-t1h-d57-clearing:     FAILs ['I7'] are not declared ...
  - pjm-2021-2025-realized-t1h-d62-pubbar:       FAILs ['I7'] are not declared ...
$ echo $?
1
```

Unchanged from `origin/main` — this lane declares nothing and repairs nothing, so the gate reading
is identical before and after. **Red is the correct state until item 1 or item 2 of §4.2 lands.**

Every number in §2 and §3 is reconstructed read-only from committed artifacts —
`frontend/data/hindcast/*.json` sidecars, `results/hindcast/<run>/**/evolution_<year>.json`
ledgers, `results/hindcast/<run>/run_config.json`, and `scripts/forecast_verdict.py` imported
unmodified — with no file written and no solve, exactly as Y-19 computed its own attribution.

## 6. What this lane did not do

- **Did not declare the four (five) rows.** `frontend/data/hindcast/invariant-failures.json` is
  untouched. Green was not the deliverable.
- **Did not weaken, reword or exempt I7 or FC-1.** `check_forecast_invariants.py` and
  `forecast_verdict.py` are byte-unchanged; no threshold, no `curated_subsets` entry, no
  applicability token moved.
- **Did not apply the §1 repair.** It re-grades 11 registered runs across five ISOs and converts a
  non-gating absence into a gating FAIL; that is the orchestrator desk's call (§4.2 item 1).
- **Did not touch** `ff-verdicts.json`, `program-status.json`, any keeper shard, marker or freeze
  file; did not solve, score, re-score, register or prune any run.
