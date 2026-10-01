# FINDING — SCN-FIX1: the scenario desk's invariant declarations, and the campaign collation's common-set repair

**Lane** SCN-FIX1 · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-fix1-records-collate-n3rt-heca49` ·
**Pin** `6c5773a2` (`origin/main`, PR #5119 merge) ·
**Charter** Scenario Readiness Desk ledger r#10 §0 ·
**LP solves** ZERO. No run was solved, scored, re-scored or registered; no keeper, marker,
board, verdict, freeze file, threshold, invariant definition or default was touched.

---

## 0. Bottom line

1. **The Y-24 forecast-invariant backlog is now the capx track's alone.** All **22** `scn-`
   runs / **34** (run, ident) pairs are declared in
   `frontend/data/hindcast/invariant-failures.json`, each named to the finding that already
   read and reported it. `check_forecast_invariants.py --sidecar-dir` goes from **30**
   undeclared runs to **8** — exactly the non-`scn-` set, unchanged.
2. **It is 22, not the charter's 18.** Four more `scn-` runs registered between the charter's
   r#10 pin and mine (§1.2). The charter's rule — declare the `scn-` ids, leave the rest —
   decides them, so all four are declared.
3. **Sixteen baseline lines are pruned in the same commit, and that is required, not
   discretionary.** A declaration is the real record, so
   `invariant_ledger.stale_baseline_entries` turns the matching
   `registration_ratchet_baseline` line into an audit problem the moment the declaration
   lands. Declaring without pruning would have traded 22 red lines for 16 different ones.
4. **The collate defect is worse than the routed measurement, and the routed case was not the
   worst case.** On the whole committed campaign tree the system-scope `LOAD-HI` 2030 delta
   **changes sign** — naive **−243.8556 Mt**, common-set **+168.7787 Mt** — because MISO has
   landed a `REF` leg and no `LOAD-HI` leg yet. So the defect is not confined to a
   legitimately degenerate arm: **any campaign read while it is still filling in hits it**,
   and the STATUS doc's +5.4620 vs +18.8300 is the mild version.
5. **The repair is a strict no-op on well-formed rows.** Where coverage already matched, the
   number does not move (`LOAD-HI` on the STATUS doc's three-ISO set: +20.1555 before and
   after). All 14 pre-existing collate tests pass unchanged.

---

## 1. The declaration table

### 1.1 What was declared, id → idents → finding

Every ident below is exactly what `check_forecast_invariants.py --sidecar-dir` prints for
that id at pin `6c5773a2` — no more, no fewer (a stale declaration fails the checker too).
**No declaration is absolution** — the ledger's own standing "rules 1/11" clause: an invariant
FAIL is a root-cause finding, never a threshold widening. Every root cause below stays open and
belongs to the lane that owns it.

| # | run id | idents | the finding that owns it |
|---|---|---|---|
| 1 | `caiso-2026-2026-scn-ws4-probe-t0-load-hi` | I7 | `FINDING-scn-ws4c` §3.3(b) — REF floor miss **2,276 MW** (WS-4b's cited figure exactly) widening to **3,861 MW** under LOAD-HI, inside their stated ≤ ~5.5 GW bound |
| 2 | `caiso-2026-2026-scn-ws4-probe-t0-ref` | I7 | same, the REF arm of that pair |
| 3 | `caiso-2026-2027-scn-ws1-probe-carb` | I7 | `FINDING-scn-ws1b` §3.8 — see §1.3, the one weak citation here |
| 4 | `caiso-2026-2027-scn-ws1-probe-ref` | I7 | same |
| 5 | `ercot-2026-2026-scn-ws4-probe-t0-load-hi-organic` | I3 | `FINDING-scn-ws4c` §5 MISS 2 — the peaky arm **sheds 143,390.9 MWh over 26 h at VOLL and fails I3** while LOAD-HI's unserved is exactly 0.0; ERCOT 2026 adequacy is a *peak* problem, not a floor problem |
| 6 | `ercot-2026-2027-scn-ws1-probe-carb` | I3 | `FINDING-scn-ws1b` §3.3 — **0.68 % of load, 641 h, 4,621.8 GWh** |
| 7 | `ercot-2026-2027-scn-ws1-probe-ref` | I3 | `FINDING-scn-ws1b` §3.3 — REF 0.06 % of load, 55 h; I3 **FAILs in both arms**, so it is not the carbon lever's |
| 8 | `ercot-2026-2030-scn-campaign-load-2026-09-06-ref` | I12, I3 | `FINDING-scn-ws5a-load-ercot` §0 item 1 (I3) + item 4 (I12) |
| 9 | `…-scn-campaign-load-2026-09-06-load-hi` | I12, I3 | same |
| 10 | `…-scn-campaign-load-2026-09-06-load-hi-organic` | I12, I3 | same |
| 11 | `ercot-2026-2030-scn-ws4-probe-t1f-ref` | I12, I3 | `FINDING-scn-ws4c` §3.2(b) — I12 out of band all four years 2027–2030 (**8.9 / 3.0 / −2.5 / −7.1 %**, reproducing WS-4b's cited bare-key numbers exactly); I3 0.08 % at 2027 rising to the 2030 tail, **slack in all 8,760 hours, 53.40 % of load** |
| 12 | `ercot-2026-2030-scn-ws4-probe-t1f-load-hi` | I3, I7 | same §3.2(b) for I3 (better than REF in 2027, worse from 2028). **I7 is not named by ident there** — see §1.4 |
| 13 | `miso-2026-2026-scn-ws4-probe-t0-ref` | I7 | `FINDING-scn-ws4c` §3.5(b) — REF floor miss **6,175 MW**, again WS-4b's figure exactly |
| 14 | `miso-2026-2026-scn-ws4-probe-t0-load-hi` | I3, I7 | same — widening to **9,622 MW**; I3 arrives on the **case** arms only |
| 15 | `miso-2026-2026-scn-ws4-probe-t0-load-hi-organic` | I3, I7 | same |
| 16 | `miso-2026-2027-scn-ws1-probe-ref` | I3, I7 | `FINDING-scn-ws1b` §3.6 — "MISO carries I3 (19 h / 41 h of slack, 0.02–0.03 % of load) and I7 in **both** arms" |
| 17 | `miso-2026-2027-scn-ws1-probe-carb` | I3, I7 | same |
| 18 | `pjm-2026-2026-scn-ws4-probe-t0-load-hi` | I7 | `FINDING-scn-ws4c` §3.4 — the 2026 T0 LOAD-HI arm flips **ALL PASS → I7 FAIL (3,341 MW) + I12 WARN**, so I7 alone |
| 19 | `pjm-2026-2027-scn-ws1-probe-ref` | I7 | `FINDING-scn-ws1b` §3.4 — "its one invariant failure (I7, accredited firm capacity below requirement) is a **capacity-accreditation** shortfall carried identically by both arms, not a dispatch collapse" |
| 20 | `pjm-2026-2027-scn-ws1-probe-carb` | I7 | same |
| 21 | `pjm-2026-2030-scn-campaign-load-2026-09-06-ref` | I12, I7 | `FINDING-scn-ws5a-load-pjm` §0 — "REF fails `{I7, I12}` with no I3" |
| 22 | `pjm-2026-2030-scn-campaign-load-2026-09-06-load-hi` | I12, I3, I7 | same — "LOAD-HI fails `{I3, I7, I12}`"; the I3 appearance is the lane's **target** phenomenon, pre-registered by WS-4b, not a collateral flip |

Grouped by ident, with the cause named once:

- **I3 on ERCOT (7 rows)** — the standing **FR-6** energy-only scarcity-slack cause at
  campaign scale: the **G-S4 forecast REF adequacy collapse**. The shipped ERCOT forecast
  posture is in deep shortage (`FINDING-scn-ws5a-load-ercot` §0 item 1: unserved
  **0.38 → 127.2 TWh** = 14.7 % of 2030 load, load-weighted price **$91 → $4,438/MWh**,
  `hours_ge_500` 74 → 7,962 of 8,760). Every ERCOT delta in the campaign is a difference
  between arms that are **both shedding at VOLL from ~2027**.
- **I3 on MISO (4 rows)** — as `FINDING-scn-ws4c` §3.5(b) and `FINDING-scn-ws1b` §3.6 report
  it: small in magnitude (0.02–0.03 % of load, 19–41 h), present in **both** arms of the
  paired probe, and arriving on the **case** arms of the T0 probe — which is why
  `miso-…-t0-ref` declares I7 alone.
- **I3 on PJM (1 row)** — `FINDING-scn-ws5a-load-pjm` §0, the predicted appearance under
  LOAD-HI against a REF that has none.
- **I12 on the ERCOT campaign legs (3 rows)** — `FINDING-scn-ws5a-load-ercot` §0 item 4, a
  clean **MISS** reported at full magnitude: WS-4b predicted LOAD-HI's peak 9–18 GW *below*
  REF and I12 therefore to "improve or pass"; measured, the peak is **above** REF in all five
  years (110.6 vs 104.1 GW … 215.8 vs 161.8 GW) and I12 is uniformly **worse**. Cause
  identified there (the retired 122 GW DC anchor), not tuned away.
- **I12 on `ercot-…-t1f-ref` and the two PJM campaign legs** — §3.2(b) and
  `FINDING-scn-ws5a-load-pjm` §0 respectively, per-year values in the table above.
- **I7 on CAISO / MISO / PJM / ERCOT (11 rows)** — the reliability floor. In every case the
  finding that owns it reports the miss **in both arms of its pair**, so no I7 row here is
  attributable to the lever the probe was testing.

### 1.2 Why 22 and not the charter's 18

The charter enumerated 18 `scn-` ids at the desk's r#10 pin. At mine (`6c5773a2`) the audit
prints **22**. The four extra registered in between and are `scn-` ids, so the charter's own
rule — "`scn-` run ids ONLY … the `scn-` lines must be gone and the count of remaining lines
must equal the capx set you named" — decides them:

| new since the charter pin | idents | registering lane |
|---|---|---|
| `caiso-2026-2027-scn-ws1-probe-carb` | I7 | SCN-WS1b-r2 |
| `caiso-2026-2027-scn-ws1-probe-ref` | I7 | SCN-WS1b-r2 |
| `pjm-2026-2030-scn-campaign-load-2026-09-06-load-hi` | I12, I3, I7 | SCN-WS5A-LOAD |
| `pjm-2026-2030-scn-campaign-load-2026-09-06-ref` | I12, I7 | SCN-WS5A-LOAD |

This is the ratchet's own documented failure mode reproducing once more (Y-19 declared 16 of
20 and was behind before it merged, because four registered while it worked). It is not a
problem here — both lanes are still live and each of the four is squarely covered by its own
lane's committed finding — but it is the reason the count in a charter is a floor, not a
target.

### 1.3 The one weak citation, named rather than buried

`caiso-2026-2027-scn-ws1-probe-{carb,ref}` are the only two rows whose finding reports the
failure **by count** rather than **by ident**: `FINDING-scn-ws1b` §3.8's comparison line reads
"CAISO's 1/1" (1 FAIL / 1 WARN) without saying which. Two things make the declaration sound
anyway, and both are stated in the ledger note rather than left implicit:

1. §3.8's substantive result is that the pair is an **exact identity** — Δ CO2 and Δ lw_price
   `0.000000` to six decimals, every by-fuel and by-zone row identical, `unserved_mwh` 0.0 in
   all four arms. So the FAIL is provably carried **identically by both arms** and is not the
   carbon lever's, whatever it is.
2. The ident the audit prints is **I7**, and §3.3 measures the reliability floor on the same
   ISO at the same posture (2,276 MW at REF). Same seam.

That is a citation to a *reported* failure, which is what the ledger asks for. It is not as
tight as the other 20 and is flagged as such.

### 1.4 One ident whose finding does not name it

`ercot-2026-2030-scn-ws4-probe-t1f-load-hi` carries **I7** alongside I3, and
`FINDING-scn-ws4c` §3.2 discusses ERCOT's I12 and I3 without naming I7. ERCOT is energy-only,
so I7 there is the **retirement-bounded nameplate floor** (`check_i7_reliability_floor`'s
energy-only branch — evolution must not over-retire below the floor relative to where the year
started), a different quantity from the absolute accredited floor the CAISO/MISO/PJM rows fail.
Declared because the audit prints it and the arm's own finding is the record of that arm; the
*mechanism* is not adjudicated here and is not this lane's to adjudicate.

### 1.5 The baseline prune

Sixteen of the 22 also held a `registration_ratchet_baseline` line. The baseline is **not** an
adjudication (`scripts/lib/invariant_ledger.py`: it forgives at the registration seam only,
never in the CI audit) and it **may only shrink**: `stale_baseline_entries` reports a line as
stale precisely when "a desk has since DECLARED it … the declaration is the real record and the
baseline line is dead weight that would silently forgive a future regression on the same
ident." So the prune is mandatory, not discretionary — declaring without it swaps 22 red lines
for 16 different ones.

Pruned: exactly the (run, ident) pairs declared, and no others — the 16 rows listed in the
ledger's `scnfix1_note`. The remaining six had no baseline line (they registered after Y-24
took its baseline, §1.2 plus `miso-2026-2027-scn-ws1-probe-{carb,ref}`) and are declared
outright.

### 1.6 The audit, re-run

At pin `6c5773a2`, before:

```
forecast-invariant artifact audit: 95 sidecar(s), 1330 record(s)
30 undeclared runs — 22 `scn-`, 8 non-`scn-`
```

After both edits, on the same sidecar set:

```
forecast-invariant artifact audit: 95 sidecar(s) with an invariants block, 1330 record(s), 79 FAIL(s) declared
forecast-invariant artifact audit FAILED:
  - caiso-2026-2030-d60-arm: FAILs ['I12', 'I7'] …
  - neiso-2026-2050-t3-golden3-d60: FAILs ['I3'] …
  - nyiso-2021-2025-realized-t1h-d45r-curveon: FAILs ['I7'] …
  - pjm-2021-2025-realized-t1h-d45: FAILs ['I7'] …
  - pjm-2021-2025-realized-t1h-d45r: FAILs ['I7'] …
  - pjm-2021-2025-realized-t1h-d57-clearing: FAILs ['I7'] …
  - pjm-2021-2025-realized-t1h-d62-pubbar: FAILs ['I7'] …
  - pjm-2026-2030-d60-arm: FAILs ['I12', 'I7'] …
```

**Eight lines, all of them the capx set named in §3.1.** No `scn-` line, and no
stale-baseline line.

---

## 2. The collate repair

### 2.1 The defect

`scripts/collate_scenario_campaign.py::build_delta_table` built one long frame of ISO-scope
and system-scope rows and merged the reference case's levels onto it by `(scope, year)`. For
the `six-ISO modeled system` scope that made the delta

> *(sum over the case's ISOs)* − *(sum over the reference case's ISOs)*

with **nothing restricting the two sums to the same system**. Found by SCN-WS5A-LOAD in
pre-flight and routed rather than fixed (that lane's charter says consume, never modify);
`STATUS-scn-ws5a-load-2026-09-06.md`, "Routed defect".

It is structural, not a partial-campaign transient. PJM and NEISO ship
`LOAD-HI == LOAD-HI-ORGANIC` byte-for-byte, so their ORGANIC arm is **correctly never
solved**; at full completion `REF` and `LOAD-HI` cover 6 ISOs while `LOAD-HI-ORGANIC` covers
4. Any campaign with a legitimately degenerate arm hits it.

### 2.2 The repair, system-scope only

- Both operands are restricted to `isos(case) ∩ isos(reference_case)` before summing.
- The row is **labelled with that intersection**: `delta_isos`, `delta_n_isos`.
- Where the intersection is a strict subset of either side, **the row says so in its own
  column**: `delta_coverage` reads `full` when nothing was dropped, else e.g.
  `COMMON-SET ONLY (MISO+PJM+NEISO in REF but not in LOAD-HI-ORGANIC)`.
- Disjoint coverage emits **NaN**, never a computable-looking number over mismatched systems.
- `emissions_mt` and `emissions_mt_ref` are restricted the same way, so
  `delta = emissions_mt − emissions_mt_ref` holds **within the row** for a reader who
  subtracts. The unrestricted campaign level is unchanged and stays in
  `campaign_emissions_system.csv` beside its own `isos` / `isos_missing` columns.
- The markdown snapshot carries the two new columns and one sentence saying what they mean.

Per-ISO rows keep their arithmetic exactly (an ISO scope has only ever compared like with
like) and gain the same three columns so the table has one schema. `report_scenario_deltas.py`
is untouched, as are `discover_summaries`, `side_lines_for_run`, `build_iso_frame` and
`build_system_frame`. The tool still never solves, tunes, or changes a threshold.

### 2.3 Before / after, on the committed `results/scn-campaign-load-2026-09-06/` artifacts

System scope, 2030, Mt CO2:

| ISO set read | case | naive (pre-repair) | common-set (post-repair) | `delta_isos` |
|---|---|---|---|---|
| STATUS doc's `{ERCOT, NEISO, NYISO}` | `LOAD-HI-ORGANIC` | **+5.4620** | **+18.8300** | ERCOT+NYISO |
| STATUS doc's `{ERCOT, NEISO, NYISO}` | `LOAD-HI` | +20.1555 | **+20.1555** | ERCOT+NYISO+NEISO |
| whole committed tree (5 ISOs) | `LOAD-HI-ORGANIC` | −877.6276 | **+18.8300** | ERCOT+NYISO |
| whole committed tree (5 ISOs) | `LOAD-HI` | **−243.8556** | **+168.7787** | ERCOT+PJM+NYISO+NEISO |

Four things this table says:

1. **The STATUS doc's routed measurement reproduces exactly** — +5.4620 → +18.8300, an error
   of −13.368 Mt which is precisely NEISO's REF 2030 level, a **71 % understatement**.
2. **The repair is a strict no-op where coverage already matched** — `LOAD-HI` on the
   three-ISO set does not move.
3. **The routed case was the mild one.** On the whole committed tree the `LOAD-HI` system
   delta **changes sign**, −243.8556 → +168.7787, because MISO has landed a `REF` leg and no
   `LOAD-HI` leg yet. A reader would have taken a 169 Mt *increase* for a 244 Mt *decrease* —
   the campaign's headline answer, inverted, on a case with no degenerate arm at all.
4. **So the defect is not confined to degenerate arms.** Any campaign read while it is still
   filling in hits it, which is every campaign, mid-flight, including this one at every
   check-in the desk has taken.

The mitigation the STATUS doc noted still holds and is why this was catchable: the tool always
emitted `isos` / `isos_missing`, so the coverage was disclosed. It was a wrong number beside
honest metadata. It is now a right number that carries its own metadata.

### 2.4 Tests

`tests/scoring/test_collate_scenario_campaign_common_set.py`, 17 tests, trivial-first per
CLAUDE.md's testing pattern:

1. **Fabricated, hand-computed** (`TestCommonSetOnFixtures`) — three ISOs in `REF`, two in the
   case, shaped like the real defect: naive **+5.0**, common-set **+15.0**, the error exactly
   the dropped ISO's REF level. Asserts the answer, that the naive form is *not* emitted, the
   intersection label, the coverage sentence, that a full-coverage row reads `full` and
   differences to zero, that the row's own arithmetic closes, that the system delta equals the
   sum of the common ISOs' deltas, the cumulative column, per-ISO rows unaffected, and the
   markdown surfacing.
2. **Disjoint coverage** (`TestNoCommonIso`) — NaN and a `NO DELTA` reason, never a zero.
3. **Regression on committed artifacts** (`TestScnCampaignLoadRegression`) — reproduces the
   STATUS doc's +5.4620 / +18.8300 / −13.368 from `results/scn-campaign-load-2026-09-06/`,
   plus the whole-tree sign flip. Skips cleanly if the artifacts are ever pruned.

All **14** pre-existing tests in `tests/scoring/test_collate_scenario_campaign.py` pass
unchanged — including `test_system_delta_is_the_sum_of_the_iso_deltas` and
`test_reference_rows_difference_to_zero`, which the repair must not disturb and does not.
`ruff check` and `ruff format --check` clean on both files.

---

## 3. Left for other desks

### 3.1 The eight capx-track ids this lane does NOT declare

| run id | idents | routed by Y-24 to |
|---|---|---|
| `caiso-2026-2030-d60-arm` | I12, I7 | CAPX DESK |
| `pjm-2026-2030-d60-arm` | I12, I7 | CAPX DESK |
| `neiso-2026-2050-t3-golden3-d60` | I3 | CAPX DESK |
| `pjm-2021-2025-realized-t1h-d62-pubbar` | I7 | CAPX DESK |
| `nyiso-2021-2025-realized-t1h-d45r-curveon` | I7 | FORECAST-ORCHESTRATOR DESK |
| `pjm-2021-2025-realized-t1h-d45` | I7 | FORECAST-ORCHESTRATOR DESK |
| `pjm-2021-2025-realized-t1h-d45r` | I7 | FORECAST-ORCHESTRATOR DESK |
| `pjm-2021-2025-realized-t1h-d57-clearing` | I7 | FORECAST-ORCHESTRATOR DESK |

They are not the scenario desk's runs, and the four T1-H rows are additionally **Y-19's
explicitly undiagnosed set** — every `t1h` verdict key reads `FC-1: SKIPPED — "no committed
invariant record"` while the sidecar carries a full I1–I14 block, so no lane has ever
adjudicated the failure. Declaring an undiagnosed FAIL is the silent landing the gate exists
to prevent. `forecast-invariant-artifacts` stays **red on exactly these eight** until their
desks adjudicate them, and is green on every `scn-` row.

Y-19's own note records that two of the four are **one-field attributable from committed
artifacts with no solve** (`pjm-…-t1h-d45r-fixed` and `nyiso-…-t1h-d45r` both read
`I7 PASS: held`), so the capx desk's half is answerable at zero LP whenever it is picked up.

### 3.2 Ruff — the charter's named red is already GREEN; two others are red on main

The charter names `scripts/data/derive_caiso_offer_surface.py` (the owner's caiso-254 file) as
a standing Ruff red to report. **At my pin it is clean.** It was repaired on main by
`824f9567` ("Port the base-branch ruff-format fix so this PR's CI can be read"); `ruff check`
and `ruff format --check` both pass on it.

`ruff check .` is **clean repo-wide** at `6c5773a2`. `ruff format --check .` is **red on two
files**, both pre-existing on `origin/main` (verified by re-running the check against a clean
`origin/main` checkout) and both outside this lane's regions:

| file | owner |
|---|---|
| `scripts/run_calibration.py` | core infrastructure — not this lane's (rule 27 `[R-PUSH]`) |
| `src/market_sim/data/fuel/basis/miso.py` | MISO calibration lane (`miso-224`, commits `7fa9f096` / `cde54404`) |

Reported, not touched. CI's lint job runs both commands (`.github/workflows/ci.yml` lines
411/413), so this job is red on `main` for a reason unrelated to SCN-FIX1 and will stay red on
this PR until one of those lanes formats its file. **Routed to SCN-DESK** for onward routing —
one is core infra and one is another ISO's lane, so neither is a scenario-desk fix.

### 3.3 Not done, deliberately

- **No plan §5.1 edit.** SCN-WS-1b-r2's open PR #5101 holds those rows.
- **No mechanism-matrix shard edit.** Nothing here is a mechanism: the ledger edit is records
  and the collate change is post-processing arithmetic with no `ScenarioConfig` field, no
  solve path and no cache key.
- **No sidecar, `results/**`, `src/`, audit-script or `report_scenario_deltas.py` edit** — all
  named LIVE or out-of-region by the charter.

---

## 4. Files touched

| file | change |
|---|---|
| `frontend/data/hindcast/invariant-failures.json` | +22 keys under `declared_failures`; −16 stale `registration_ratchet_baseline` lines (the same pairs); +`scnfix1_note`. No existing declaration edited or deleted; no threshold, `curated_subsets` entry or narrative note altered. |
| `scripts/collate_scenario_campaign.py` | system-scope delta on the common ISO set; new `order_isos`, `_coverage_note`, `_system_delta_rows`, `_iso_delta_rows`; `build_delta_table` rewritten around them; `COVERAGE_FULL`; markdown snapshot gains the two columns. |
| `tests/scoring/test_collate_scenario_campaign_common_set.py` | **new**, 17 tests (§2.4). |
| `docs/handoffs/FINDING-scn-fix1-2026-09-06.md` | this document. |

Two commits, in that order, each pushed and — for the two files ≥300 lines — verified by
fetch-back against the remote blob (rule 27 `[R-PUSH]`): `scripts/collate_scenario_campaign.py`
648 lines and `tests/scoring/test_collate_scenario_campaign_common_set.py` 345 lines, both
sha256-identical local vs `origin`. No CI workflow added; no default moved; no solve of any
kind.
