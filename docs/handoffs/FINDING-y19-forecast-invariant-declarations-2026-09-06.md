# FINDING — Y-19: the forecast-invariant artifact audit, closed by ident — 29 of 33 undeclared FAILs are disclosed consequences with a finding behind them, and the remaining 4 are ONE undiagnosed defect with four symptoms: at T1-H every verdict key reads `FC-1: SKIPPED "no committed invariant record"` while the sidecar carries a full committed I1–I14 block, so no lane has ever graded the reliability floor it breaches

**Lane:** Y-19, Model Audit & Release-Finalization Program — "Forecast-invariant artifact audit"
(chronic red on `main`; board `docs/handoffs/audit-program-director-board-2026-08.md`).
**Branch:** `claude/y19-forecast-invariant-declarations-hp5l2a`, off `origin/main` `5fdd4374`.
**Date:** 2026-09-06. **Model:** `claude-opus-5`. **Data profile:** `code` (no solve, no LP).

**Refusals honoured.** No solve, no score, no registration, no re-score of any forecast run.
`ff-verdicts.json`, `program-status.json`, every keeper shard, marker and freeze file are
**read-only in this session and unmodified**. No invariant definition, threshold or exemption
was touched — `scripts/check_forecast_invariants.py` is byte-unchanged. The only file changed
is `frontend/data/hindcast/invariant-failures.json` (declarations + one note).

---

## 0. Verdict (one paragraph)

**The gate names 20 runs and 33 (run, ident) pairs — not the 17 the charter carried — across
FOUR idents (I3, I7, I9, I12), not three.** Grouped by ident, **29 of the 33 pairs are disclosed
consequences that a committed record already states**, and they are declared. **All 9 I3, all 10
I12 and all 3 I9 pairs declare; 7 of the 11 I7 pairs declare.** The residual is a single
coherent object: **four T1-H realized-hindcast I7 rows — PJM ×3 and NYISO ×1 — whose FAIL no
lane has ever adjudicated**, because every `t1h` verdict key in `ff-verdicts.json` reads
`FC-1: SKIPPED — "no committed invariant record (summary.invariants / --invariants)"` while the
registered sidecar carries a full 14-row invariant block that the artifact audit *does* read.
The T1-H scoring convention (canonical `--hindcast-score --run-config`, no `--invariants`) is
therefore a **blind spot, not an absence**: the evidence is committed, and nothing scores it.
The proof that this is a live defect and not a bookkeeping quibble is `pjm-t1h-d45r-fixed` and
`nyiso-t1h-d45r`, the one-field siblings of two of the four, which read **`I7 PASS: held`** — so
the FAIL is mechanism-attributable in both cases, and in the PJM case the capx D48 lane
*predicted the opposite* ("I7 still PASS wherever it passes") and recorded that it could not
grade it. **These four are NOT declared.** They are routed, with their one-field attribution, to
the capx director desk; the systemic cause is routed to the forecast-orchestrator desk. A
partially green gate with an honest routed list is the correct outcome here, and it is the one
the evidence supports.

---

## 1. Reproduction — before, with `$?` read directly

Clean worktree at `origin/main` `5fdd4374`, `frontend/data/hindcast` untouched:

```
$ uv run --frozen python scripts/check_forecast_invariants.py \
      --sidecar-dir frontend/data/hindcast
forecast-invariant artifact audit: 47 sidecar(s) with an invariants block,
658 record(s), 39 FAIL(s) declared
forecast-invariant artifact audit FAILED:
  ... 20 lines ...
$ echo $?
1
```

**The charter's census is stale in two ways, and both widen the object rather than narrow it.**
It names *seventeen* runs on *three* idents (I3, I7, I12). The audit at this HEAD names
**twenty** runs on **four** — I9 is the fourth, and it carries three pairs. The three extra runs
are the ERCOT CES premium ladder (`scn-ws2-ladder-{bau,ces-20,ces-40}`), registered by SCN-WS2b
on 2026-09-06 (`c2912cc3`) after the charter was written. Nothing was dropped; three arrived.

| ident | runs | pairs | what the invariant asserts |
|---|--:|--:|---|
| **I3** | 9 | 9 | unserved (slack ≤ 1e-4 of demand) **and** dump ≤ 2 % of renewable potential |
| **I7** | 11 | 11 | reliability floor: accredited firm ≥ requirement (market-design dependent) |
| **I9** | 3 | 3 | storage integrity: SOC ≥ 0, cyclic close, no simultaneous charge+discharge |
| **I12** | 10 | 10 | reserve margin within `[floor, floor + 15 pp]`, 3 consecutive years to FAIL |
| | **20 runs** | **33** | |

---

## 2. The per-ident cause table

Each ident has one underlying cause per market-design family, exactly as the charter predicted.
"Root cause" and "recorded" are different questions, and this table answers both.

| ident | family | cause | is the FAIL RECORDED? | is the ROOT CAUSE closed? |
|---|---|---|---|---|
| **I3** slack | ERCOT (energy-only) | **FR-6** — the adequacy backstop is disabled for energy-only ERCOT by market design (`resolve_reserve_margin_build_enabled` → False), so a one-pass under-build has no corrective and lands as LP slack at VOLL | **yes** — `FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §§2/5.1; `d4m_note` | **no — open, unowned in code** |
| **I3** slack | MISO (capacity market) | the backstop IS armed and never fires: the D27 25.6 GW coal over-exit, the endogenous S-123-V signature | **yes** — `FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md` §6 | **no — routed to the MISO screen lane** |
| **I3** dump | NEISO T3 golden | out-year renewable dump 2043 2.17 % → 2050 7.74 %: zero storage entry across 25 years against a ~9× VRE buildout | **yes** — `FINDING-capx-t3-neiso-golden-2026-08-30.md` §6.3(2); `FINDING-capx-t3-golden2-2026-09-01.md` §"I3 FAIL" | **no — open** |
| **I7** | MISO T1-H | **the disclosed adequacy price of the Q30 fossil-dates arming** — exogenous exits at scale push MISO below requirement in 2023/2024 before the backstop responds in 2025 | **yes** — `FINDING-capx-d42-fossil-dates-ab-2026-09-02.md` §0 + §7.4(4), "reported, not hidden, and routed" | **no — it is the additions lane's object (D33 §4.1, D39)** |
| **I7** | CAISO 2021 seed | a property of the vintage-2020 seed fleet: `2021: accredited firm ≈44,070 < requirement 50,157 MW`, numerically identical across unrelated arms | **yes** — `fh-5-phase-b-2026-08-11.md` §8.6, "Reported and left standing"; `d18_note` | **no — `d18_note`: "NO LANE OWNS WHY the 2021 seed fleet is 6,087 MW short"** |
| **I7** | t1f forecast legs (CAISO/MISO/PJM) | FR-3 accredited-firm ledger family residual; each leg's FC-1 is a **gating row its own lane read and reported** | **yes** — D46 §4.6; D45 §7.2 P13/P14; `PREDECL-capx-d60` §6.1 P2/P3; D50 §7.1 | **no — open** |
| **I7** | **PJM ×3 + NYISO ×1, T1-H** | **UNDIAGNOSED — §4** | **NO** | **NO — nobody has looked** |
| **I9** | CAISO | storage ε-tiebreak degeneracy at high penetration | **yes** — `docs/forecast-development-plan-2026-07.md` §1.2-8; `d18_note` | **no — routed to lane FF-3C item 2, which has never been run** |
| **I9** | ERCOT CES arms | **pre-registered before the solve** as appearing *only* under the premium, and as a positive machinery signal | **yes** — `PRECOMMIT-scn-ws2b-2026-09-06.md` §G5 | n/a — expected, not a defect |
| **I12** | all | reserve margin below the market-design floor for ≥3 consecutive years; downstream of the same adequacy shortfall I7 measures on the capacity side | **yes** — same citations as the I7 t1f row | **no — open** |

**Nothing in the declared set is absolution.** Every root-cause column above reads "open" or
"routed". A declaration records that the FAIL was *seen and stated*; it closes no lane.

---

## 3. The declared set — 16 runs, 29 pairs, with citations

Each row states the record that discloses **this run's** FAIL. Where the record is a *different*
run, the bridge is stated and is arithmetic, not analogy.

| run | idents | the record that discloses it |
|---|---|---|
| `ercot-2021-2025-realized-t1h-d46` | I3 | **The full 14-row invariant block is byte-identical to the already-declared `ercot-2021-2025-realized-t1h-d4m`** (verified in-session; the D46 axes moved the cache key `f061b264…` → `67d5dcc1…` without moving one invariant digit). Cause + magnitude: `d4m_note`, `FINDING-capx-d4m-ercot-t1h-2026-08-31.md`, `FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §§2/5.1 (FR-6). |
| `ercot-2026-2030-d46-remeasure` | I3, I12 | `FINDING-capx-d46-remeasure-2026-09-03.md` §4.6 (I12 per-year 2027 8.9 / 2028 3.0 / 2029 −2.5 / 2030 −7.1 %, matching the sidecar digit-for-digit); `FINDING-capx-d50-2026-09-04.md` §"FC rows"/§7.1 records the same run as the D50 control with FC-1 `FAIL [I12, I3]`. I3 cause: FR-6. |
| `ercot-2026-2030-d50-ccscapex` | I3, I12 | `FINDING-capx-d50-2026-09-04.md` line 107 and §7.1 table: FC-1 `FAIL [I12, I3]` **byte-identical to the control** — the CCS-capex repair is inert below `ccs_retrofit_available_year`, which is the finding's own P9. |
| `ercot-2026-2030-scn-ws2-ladder-bau` | I3, I12 | `PRECOMMIT-scn-ws2b-2026-09-06.md` §G5, **written and pushed before the first solve**: "The July POC's I3/I12/I14 are known BAU-side ERCOT adequacy failures (F-2) and are **expected in every arm**." |
| `ercot-2026-2030-scn-ws2-ladder-ces-20` | I3, I9, I12 | §G5 as above for I3/I12; **and for I9**: "I9 (storage ε-degeneracy) is expected to appear **only** under the premium and is a positive machinery signal, not a kill." Confirmed by the artifacts: I9 FAILs in `ces-20` and `ces-40` and **PASSES in `bau`** — the pre-registered pattern, exactly. |
| `ercot-2026-2030-scn-ws2-ladder-ces-40` | I3, I9, I12 | as `ces-20`. |
| `miso-2021-2025-realized-t1h-d27` | I3 | `FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md` §6, which states the numbers verbatim ("2024: 29 h, 133.2 GWh, peak 15,224 MW; 2025: 57 h, 143.2 GWh, peak 7,340 MW") **and** pre-states the audit's own reading: "a future lane could score FC-1 without a re-solve — it would read **FAIL** on I3." |
| `miso-2021-2025-realized-t1h-d46` | I7 | Cause: `FINDING-capx-d42-fossil-dates-ab-2026-09-02.md` §0 + §7.4(4) — "reserve margin −1.0 % / −1.5 % in 2023/2024 (**I7 FAIL**, I12 WARN) … reported, not hidden, and routed". Identity: `FINDING-capx-d53-2026-09-05.md` §2.1 P1 + this ledger's `d53_note`, which names this run's row byte-for-byte (2023 119,543 < 121,644; 2024 119,763 < 122,429) and **explicitly leaves it to the records lane**. |
| `miso-2026-2030-d45r-remeasure` | I7, I12 | `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md` §7.2 P14, graded HIT: "I7 joins **four** years (2026–2029, misses 11.4 / 12.1 / 12.6 / 5.7 GW); I12 out of band in four years (−8.1 / −8.6 / −8.9 / −3.6 %)". `PREDECL-capx-d60-2026-09-05.md` §6.1 tabulates the same four rows as the D60 control. |
| `miso-2026-2030-d60-arm` | I7, I12 | `PREDECL-capx-d60-2026-09-05.md` §6.1 **P2/P3/P4, derived from the ratio arithmetic before the solve**: strict upper bounds 123,452 / 124,117 / 125,133 MW (realized 123,292 / 123,956 / 124,971 — under every bound), 2029 "+86 MW at the ceiling" (realized 76 MW short, i.e. still FAIL), and the conclusion "**FC-1 therefore stays `FAIL ['I12','I7']`**". |
| `caiso-2021-2025-realized-t1h-d46` | I7, I9 | I7: `fh-5-phase-b-2026-08-11.md` §8.6 records the identical seed-year row (`44070 < 50157 MW`; this run 44,069 — a 1 MW config-epoch delta against an identical requirement) and dispositions it "Reported and left standing (rules 1/13/14)"; `d18_note` declared the identical row on the pruned twin and states the root cause is **untracked**. I9: `d18_note` + `docs/forecast-development-plan-2026-07.md` §1.2-8, routed to FF-3C item 2 (never run). |
| `caiso-2026-2030-d46-remeasure` | I7, I12 | `FINDING-capx-d46-remeasure-2026-09-03.md` §4.6, CAISO t1f row: "FC-1 FAIL set **shrinks** `[I12, I3, I7] → [I12, I7]`" — the exact failing set now in the sidecar, read as a gating row by the lane that registered it. |
| `neiso-2026-2050-t3-golden2-bau` | I3 | `FINDING-capx-t3-golden2-2026-09-01.md` §"I3 FAIL — out-year renewable dump, same onset, slightly shallower end" and its FC table: "FAIL (I3 dump, onset 2043 identical, terminal 7.74 %)" — the sidecar's terminal value. |
| `neiso-2026-2050-t3-golden3-bau` | I3 | `FINDING-capx-d47-golden3-attestation-2026-09-04.md` §"FC-1 (I3 renewable dump)", attested **byte-identical** to GOLDEN-2's; `FINDING-capx-d46-remeasure-2026-09-03.md` §4.6 GOLDEN-3 row: "FC-1's I3 renewable-dump failure **identical year-by-year**". Cause: `FINDING-capx-t3-neiso-golden-2026-08-30.md` §6.3(2). |
| `pjm-2026-2030-d45r-remeasure` | I7, I12 | `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md` §7.2 P13, graded: "I7 FAIL in **four** years (2027 joins at a **250 MW** miss; 2028 / 2029 / 2030 misses **6,226 / 5,800 / 5,647**); I12 deeper (**−13.5 %** in 2028)". Every one of those five numbers is the sidecar's arithmetic. |
| `pjm-2026-2030-d50-ccscapex` | I7, I12 | `FINDING-capx-d50-2026-09-04.md` §7.1: FC-1 `FAIL ['I12','I7']` — "same failing set" as the control — with the 2028 I12 move −13.5 → −13.8 % recorded at line 204. |

**Cross-check.** Every declared t1f/t3 row is independently corroborated by its committed verdict
key in `ff-verdicts.json` (read-only): `ercot-t1f` `FAIL ['I12','I3']`, `caiso-t1f` and `pjm-t1f`
and `miso-t1f` `FAIL ['I12','I7']`, `neiso-t3` `FAIL ['I3']` (dump). Those lanes read their FC-1.

---

## 4. The routed set — 4 runs, 4 pairs, ONE undiagnosed defect

### 4.1 The defect, stated once

Every `t1h` verdict key in `ff-verdicts.json` — **all of them, across all six ISOs** — carries:

```
FC-1 structural integrity (I1-I14): SKIPPED
  detail: "no committed invariant record (summary.invariants / --invariants)"
  applicability: optional
```

That detail string is **false at the artifact level**. Each of these runs' registered sidecars
*does* carry a committed 14-row I1–I14 block — which is precisely what the forecast-invariant
artifact audit reads, and where it finds the FAILs. The verdict is produced by the canonical
T1-H command (`--hindcast-score` + `--run-config`, no `--invariants`), noted as a deliberate
comparability convention in `FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md` §"Board note".
The consequence is that **for the entire T1-H family, invariant evidence is committed to the
dashboard and never scored by anything except this audit.**

The capx D48 lane hit the wall directly and wrote it down —
`FINDING-capx-d48-2026-09-04.md` §"pre-declaration", P6:

> "`adequacy_requirement_mw` 160.9 / 166.8 / 150.6 GW; `reserve_margin` identity moves;
> **I7 still PASS wherever it passes**" → "**HIT** on the rows … **I7 / I12 ungradable
> (FC-1 SKIPPED at t1h — no invariant record, as on the control)**"

So the one lane that reasoned about I7 at T1-H *predicted it would pass*, *could not check*, and
*was wrong*. That is the definition of an undiagnosed defect, and it is why these four are not
declared.

### 4.2 The four rows, each with its one-field attribution

Attribution computed in-session by differencing the registered sidecar `meta` blocks. In two of
the four the FAIL is isolated to a **single posture field**, because a sibling run that differs
in only that field reads `I7 PASS: held`.

| run | I7 detail | one-field delta vs a sibling | sibling's I7 |
|---|---|---|---|
| `pjm-2021-2025-realized-t1h-d45r` | 2025: 138,009 < 144,632 MW (**−6,623**) | `capacity_clearing_posture` `shipped` → `fixed_net_cone` (PJM clearing off) gives **`pjm-2021-2025-realized-t1h-d45r-fixed`** | **PASS: held** |
| `pjm-2021-2025-realized-t1h-d45` | 2025: 138,286 < 144,632 MW (**−6,346**) | `fossil_announced_exits_enabled` False → True gives `…-d45r`; **both FAIL** — the dates channel deepens by 277 MW, it does not cause | FAIL |
| `pjm-2021-2025-realized-t1h-d57-clearing` | 2025: 147,585 < 150,605 MW (**−3,020**) | the D57 supply-clearing arm: supply +9.6 GW and requirement +6.0 GW vs `d45r`, still short | FAIL |
| `nyiso-2021-2025-realized-t1h-d45r-curveon` | 2023: 31,493 < 32,612; 2025: 32,712 < 34,395 MW | `capacity_clearing_posture` `shipped` → `forced_curve` (+ `capacity_market_clearing` on for NYISO) is the **ONLY** delta vs `nyiso-2021-2025-realized-t1h-d45r` | **PASS: held** |

### 4.3 Why the prior PJM declaration does not cover these

`d18_note` declared `pjm-2021-2025-realized-verified-exits` I7 at **138,286 < 139,850 MW**, with
a named open defect on the *supply* side (the RC-1B nuclear-phantom chain and PJM's coal economic
screen). The supply number is **unchanged** — `t1h-d45` reads the identical 138,286 MW. What
moved is the **requirement**: 139,850 → 144,632 (D45-R / D48 basis work) → 150,605 (D57), so the
shortfall widened **1,564 → 6,346 → 6,623 MW**, roughly 4×, under three successive
requirement-basis changes that no lane graded against I7. Declaring these rows under the old
citation would attribute a requirement-side movement to a supply-side defect. That is not what
the ledger's `how_to_update` asks for, and it is the misattribution `d18_note` itself was careful
to avoid on `dominant_open_causes.I3`.

### 4.35 PJM T1-H I7 is a RECURRING residual, not a new arrival

`.github/workflows/ci.yml`'s header records an empirical sweep dated **2026-08-14** naming this
job's then-red as "**three PJM runs with undeclared I7**". Those were a *different generation* of
runs (`k162`, `exante-control`, `verified-exits`); D-18 declared all three on 2026-08-31, and the
2026-09-05 keeper-only prune deleted their sidecars and, per `how_to_update`, their declarations
with them. The D45 / D45-R / D57 generation then re-introduced **three PJM I7 rows** — the same
count, the same ISO, the same invariant, against a requirement that has since moved twice.

That is the argument for routing rather than declaring. A fourth records pass would close the
gate for a third time on a seam that has re-opened after each of the previous two, and would say
nothing about why PJM's accredited firm capacity sits below its requirement at the T1-H posture
in every generation of the run. The desk question in §4.4 is the one that ends the cycle.

### 4.4 Routing

| item | to | what is owed |
|---|---|---|
| the four rows in §4.2, with their one-field attribution | **capx director desk** (`docs/handoffs/capx-director-ledger-2026-08.md`) — D45 / D45-R / D48 / D57 registered them | Adjudicate each: is the reliability-floor breach a real consequence of the clearing / requirement-basis posture (in which case declare it with its finding), or a defect in the requirement construction those lanes introduced? The PJM `-fixed` and NYISO curve-OFF siblings both PASS, so the question is answerable from committed artifacts — **no solve is needed**. |
| the systemic cause in §4.1 — T1-H FC-1 blindness | **forecast-orchestrator desk** | Either score FC-1 at T1-H off the committed block (the evidence is already there — D27's board note says so explicitly), or make the SKIPPED detail string tell the truth. Today a T1-H registration can commit a FAIL that only this audit will ever see. Note the comparability constraint D27 §"Board note" records: FC-1 is `optional` at T1-H by design, so this is a scoring-convention decision, not a bug fix. |

**Not routed and not this lane's to touch:** the root causes behind the *declared* rows — FR-6
(ERCOT energy-only slack), FR-3 (accredited ledger), the CAISO 2021 seed shortfall, FF-3C item 2
(storage ε-degeneracy), the MISO additions lane. All remain open in their own lanes, exactly as
before this commit.

---

## 5. Gate reading, before and after, with `$?` read directly

```
BEFORE  (origin/main 5fdd4374, ledger unmodified)
  $ uv run --frozen python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast
  forecast-invariant artifact audit: 47 sidecar(s) with an invariants block, 658 record(s), 39 FAIL(s) declared
  forecast-invariant artifact audit FAILED:  -> 20 undeclared runs, 33 pairs
  $ echo $?
  1

AFTER   (this commit)
  $ uv run --frozen python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast
  forecast-invariant artifact audit: 47 sidecar(s) with an invariants block, 658 record(s), 39 FAIL(s) declared
  forecast-invariant artifact audit FAILED:
    - nyiso-2021-2025-realized-t1h-d45r-curveon: FAILs ['I7'] are not declared ...
    - pjm-2021-2025-realized-t1h-d45:            FAILs ['I7'] are not declared ...
    - pjm-2021-2025-realized-t1h-d45r:           FAILs ['I7'] are not declared ...
    - pjm-2021-2025-realized-t1h-d57-clearing:   FAILs ['I7'] are not declared ...
                                             -> 4 undeclared runs, 4 pairs (the routed set, §4)
  $ echo $?
  1
```

**Read the banner counter correctly: it does not move, and should not.** "39 FAIL(s) declared"
is a mislabel in `check_forecast_invariants.py` — the number is
`sum(len(v) for v in observed.values())`, i.e. the total FAIL pairs *observed across all 47
sidecars*, not the declared ones. It was 39 before (6 already declared + the 33 undeclared) and
is 39 after, because this lane changed no run's evidence. What moved is the failing-run list:
**20 → 4**, and `declared_failures` **5 → 21 runs / 6 → 35 pairs**.

**Exit 1 is the intended outcome, not a failure to finish.** 29 of 33 pairs are closed with a
citation apiece; the remaining 4 stay red **on purpose**, because declaring an undiagnosed FAIL
is precisely the silent landing this gate exists to prevent. The audit's own message says the
declaration must come "with the finding it belongs to"; for these four there is no such finding,
and manufacturing one would be worse than a red gate. The gate goes green when the capx director
desk adjudicates §4.2 — and the honest count is now **4 open rows, each with a named owner and a
zero-LP question**, in place of 20 rows with none.

---

## 6. What this lane did not do

- **No invariant was relaxed, reworded or exempted.** `scripts/check_forecast_invariants.py` is
  byte-unchanged; no threshold in `Thresholds` was read as adjustable. `curated_subsets` is
  untouched — the coverage escape hatch was not used to hide anything.
- **No verdict, board, keeper, marker or freeze file was written.** `ff-verdicts.json`,
  `program-status.json` and `frontend/data/backcast/**` were opened read-only for corroboration.
- **No run was solved, scored, re-scored, registered or pruned.**
- **No `dominant_open_causes` entry was rewritten.** One key is ADDED (`I9`'s existing per-run
  pointer is left as is); the `I3` correction landed by D-18 stands unmodified.

---

## 7. Genealogy

This is the fourth records pass on this ledger, and it deliberately follows the shape of the
first three rather than inventing one: FFR-2B (2026-08-02, five rows), D-18 (2026-08-31, the
thirteen pre-existing rows, "this lane ADJUDICATES NOTHING and FIXES NOTHING"), and the
2026-09-05 keeper-only prune, which deleted fourteen declarations whose sidecars were pruned and
thereby re-opened the gate on the successor runs. What is new here is the **routed** half:
D-18 declared every row it found, including ones it called honestly untracked. This lane declines
to declare four, on the charter's test — a declaration is a record of a *known and explained*
property, and where the only record predicted the opposite, there is nothing to record yet.
