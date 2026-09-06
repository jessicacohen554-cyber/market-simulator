# FINDING — Y-24: the forecast-invariant declaration ratchet, and the standing backlog routed

**Lane** Y-24, Model Audit & Release-Finalization Program. **Director pin** `b618ed4b`.
**Date** 2026-09-06. **Branch** `claude/y24-invariant-declaration-ratchet-n8lphy`.
**Scope** CI/governance plumbing only. **No solve, no score, no re-score, no registration.**
No invariant definition, threshold, exemption or `curated_subsets` entry was touched; no
verdict, board, keeper shard, marker, freeze, matrix shard, `program-status.json`, `CLAUDE.md`
or workflow job set was written. **This lane declares nothing and adjudicates nothing.**

---

## 1. The object

The CI job **`Forecast-invariant artifact audit`**
(`.github/workflows/ci.yml` → `uv run python scripts/check_forecast_invariants.py --sidecar-dir`)
is a **detector**: it audits sidecars that are *already committed*, so it goes red *after* the
fact. The seam that creates the problem — `scripts/register_forecast_run.py`, the single
registration path for the forecast namespace — had **no declaration check at all**. A lane could
land a sidecar carrying invariant FAILs and nothing refused it.

The consequence is a backlog that has now regressed **four times**:

| Snapshot | Undeclared runs | Note |
|---|---|---|
| FFR-2B, 2026-08-02 | 4 | |
| Y-24 charter, 2026-09-06 | 16 → 17 | the charter cites 17 |
| Y-19 at `origin/main` `5fdd4374` | 20 runs / 33 pairs | Y-19 declared 16; 4 routed deliberately |
| **Y-24 at HEAD `8e3393b1`** | **20 runs / 29 pairs** | Y-19's 4 + **16 fresh registrations** |

Y-19 declared 29 of 33 pairs and **was behind before it merged**: four more runs registered
while it worked. A detector cannot win that race. Only a gate at the seam can.

> **The charter's "17" is now 20.** The charter's routing lists 9 scenario-desk runs; three more
> — `ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}` — registered at
> `29b1c757` (2026-09-06 04:14Z), *after* the charter was written. They are routed to the same
> desk in §4.1, which is why the scenario block below reads **12**, not 9.

---

## 2. What was built

### 2.1 The ratchet — `register_forecast_run.enforce_invariant_declaration_gate`

Called in **both** registration branches of `main()` (`--bundle`, `--summary`), **before the
canonical sidecar is written** and therefore before the registry sidecar, the `runs/<id>.js`
payload and the manifest are regenerated. A refused registration **leaves nothing behind** (the
`mkdir` moved below the gate so not even an empty directory survives).

It mirrors the backcast seam's marker gate exactly — `dashboard_add_run.enforce_registration_marker_gate`
(owner ruling **R-AZ**, lane Y-16) — down to the refusal shape and the standing sentence:

> **There is no bypass flag.** A registration that fails this check is not a registration. The
> remedy is the declaration; if the cause is not understood yet, route it and leave the run
> unregistered — git history is the record (rule 15 `[R-DASHBOARD]`).

A source-level test asserts no `--force` / `--allow-undeclared` / `--skip-invariant` /
`--no-invariant-gate` flag exists on the CLI, so a later lane cannot quietly add one.

### 2.2 One policy module — `scripts/lib/invariant_ledger.py` (new, stdlib-only)

Which rows count as FAILs, and which of them the ledger covers, are defined **once** and read by
both the detector and the ratchet — the same one-module construction `scripts/lib/holdout_policy.py`
gives the two rule-22 marker gates (rule 19 `[R-ONE-MECH]` in spirit). The detector and the
ratchet therefore cannot disagree about a run's FAIL set.

**Stdlib-only is load-bearing, not stylistic.** `register_forecast_run.py --reindex` **IS** the
Pages deploy assembly step (`deploy-pages.yml` runs it under a bare `python3`, with no
dependencies installed). A module-scope import of `check_forecast_invariants` would drag in numpy
and `market_sim` and break the **deploy**, not any test. Verified in a clean interpreter with
numpy/pandas/`market_sim` made unimportable, and by running the deploy command for real:

```
$ python3 scripts/register_forecast_run.py --reindex --site-dir /tmp/_site
[reindex] wrote 79 runs ... assembled manifest.js + program-status.js       # exit 0
```

`--reindex` never reaches the gate. It must keep assembling over the standing backlog, and it does.

### 2.3 The baseline — the ratchet gates **inflow only**

The ledger gains a second, independent block:

| Block | Meaning | Read by |
|---|---|---|
| `declared_failures` | An **adjudication**. The desk states the FAIL is understood and names the finding that owns it. | detector **and** ratchet |
| `registration_ratchet_baseline` | **NOT an adjudication.** The 20 runs / 29 pairs already registered when the gate landed. | **ratchet only** |

This asymmetry is the design's load-bearing property:

* A baselined pair **passes the registration gate** — the ratchet changes no already-registered
  run and holds no lane responsible for somebody else's backlog.
* A baselined pair **stays RED in the CI audit** — `undeclared_failures()` ignores the baseline
  unless the caller opts in, and only the gate does. Declaring an undiagnosed FAIL is precisely
  the silent landing the gate exists to prevent (Y-19's ruling), so the routing keeps its teeth.

**The baseline may only SHRINK**, the same property the Y-20 mechanism-matrix gap ratchet has. A
new run id is never in it, so inflow is gated; and `stale_baseline_entries()` turns a superseded
line into an audit problem — the run is gone, the ident no longer FAILs, or a desk has since
declared it — so closing a backlog row also prunes its baseline line instead of leaving a live
forgiveness token behind.

### 2.4 The two legacy direct writers are no longer a bypass

`scripts/register_hindcast.py` and `scripts/register_forecast_baseline.py` each have their own
`main()` + `__main__` and **write `frontend/data/hindcast/<id>.json` directly** before delegating
the namespace rebuild to `register_forecast_run`. Left alone they would be open doors around the
ratchet — a gate with a documented back door is cosmetic. Both now call the same gate at the same
point (before any write). This is a small, deliberate extension beyond the charter's letter,
made because the charter's *object* ("no registering lane can land a sidecar with FAILs and have
nothing refuse it") is not met without it.

### 2.5 Verification run before push

| Check | Result |
|---|---|
| `pytest tests/scoring/test_invariant_declaration_ratchet.py` | **22 passed** |
| `pytest tests/scoring tests/regression -n auto -m "not slow and not integration and not fulldata"` | 1899 passed, 8 skipped, **1 pre-existing failure** † |
| `ruff check scripts/ tests/` | All checks passed |
| `ruff format --check` (the 6 files this lane touches) | 6 files already formatted ‡ |
| `python scripts/check_forecast_invariants.py --sidecar-dir` (the CI job's exact command) | exit 1, **20 problems — byte-identical to pre-change** |
| `python3 scripts/register_forecast_run.py --reindex` (bare interpreter, deploy path) | exit 0, 79 runs |

† `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` —
`market_sim.config.capacity_market` grew `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO` /
`resolve_capacity_adequacy_requirement_published` without a facade re-export. **Pre-existing on
`main`**: it fails identically with this lane's changes stashed. This lane touches nothing under
`src/market_sim/`; it belongs to the capx lane that moved those names.

‡ `ruff format --check` over the whole tree reports 3 files needing reformat —
`scripts/gen_nyiso198_attestation.py`, `tests/scoring/test_holdout_render_parity.py`,
`tests/unit/model/test_capacity.py`. All three are pre-existing on `main` and untouched here.

**The audit's output is unchanged, run for run.** The refactor onto the shared module is
behaviour-preserving, and the baseline makes nothing green.

---

## 3. What this lane deliberately did NOT do

It **did not declare** a single one of the 20. Declarations belong to the registering desk: only
that desk can name the finding that owns the FAIL, and a declaration written by a records lane
that has not diagnosed the cause is the silent landing the gate exists to stop. §4 routes them.

---

## 4. Routing — 20 runs / 29 (run, ident) pairs, to three desks

All rows measured at HEAD `8e3393b1` from the committed sidecars. `added` is the commit that
first landed the sidecar. **Remedy in every case:** add `"<run_id>": [idents]` under
`declared_failures` in `frontend/data/hindcast/invariant-failures.json`, in the same commit as the
finding that owns the FAIL — **and prune the run's `registration_ratchet_baseline` line in the
same edit**, or the audit will report it as superseded.

### 4.1 SCENARIO DESK — 12 runs / 19 pairs

The nine `*-scn-ws4-probe-*` runs (charter set) plus the three `scn-campaign-load` runs that
registered after the charter was written.

| Run | Idents | Added | Measured |
|---|---|---|---|
| `caiso-2026-2026-scn-ws4-probe-t0-load-hi` | I7 | `b57c0307` 02:43Z | 2026: firm 55,030 < req 58,891 MW |
| `caiso-2026-2026-scn-ws4-probe-t0-ref` | I7 | `b57c0307` | 2026: firm 55,030 < req 57,306 MW |
| `ercot-2026-2026-scn-ws4-probe-t0-load-hi-organic` | I3 | `b57c0307` | 2026: slack 0.02 % (26 h, 143.4 GWh, peak 15,449 MW) |
| `ercot-2026-2030-scn-ws4-probe-t1f-load-hi` | I3, I7 | `1fd49d86` 02:53Z | I3 2030: slack **53.40 %** (8760 h, 959,708.9 GWh); I7 2027: thermal 78,210 < floor 78,334 MW |
| `ercot-2026-2030-scn-ws4-probe-t1f-ref` | I12, I3 | `1fd49d86` | I3 2030: slack 2.34 %; I12 2029/2030 −2.5 / −7.1 % |
| `miso-2026-2026-scn-ws4-probe-t0-load-hi` | I3, I7 | `b57c0307` | slack 0.01 %; firm 123,292 < req 132,914 MW |
| `miso-2026-2026-scn-ws4-probe-t0-load-hi-organic` | I3, I7 | `b57c0307` | slack 0.01 %; firm 123,292 < req 133,025 MW |
| `miso-2026-2026-scn-ws4-probe-t0-ref` | I7 | `b57c0307` | firm 123,292 < req 129,467 MW |
| `pjm-2026-2026-scn-ws4-probe-t0-load-hi` | I7 | `b57c0307` | firm 151,384 < req 154,725 MW |
| `ercot-2026-2030-scn-campaign-load-2026-09-06-ref` | I12, I3 | `29b1c757` 04:14Z | I3 2030: slack 12.88 %; I12 2030 −25.3 % |
| `ercot-2026-2030-scn-campaign-load-2026-09-06-load-hi` | I12, I3 | `29b1c757` | I3 2030: slack **37.83 %** (8760 h); I12 2030 **−43.1 %** |
| `ercot-2026-2030-scn-campaign-load-2026-09-06-load-hi-organic` | I12, I3 | `29b1c757` | I3 2030: slack **37.83 %**; I12 2030 **−49.2 %** |

**Flagged for the desk, not adjudicated here.** The three `scn-campaign-load` arms and
`ws4-probe-t1f-load-hi` are a different magnitude class from every other row in this backlog: slack
reaches 8,760 h — *every hour of the year* — at 37–53 % of load, with the reserve margin at
−43 % to −49 %. The ERCOT I3 rows already declared elsewhere are the standing FR-6 energy-only
cause (`dominant_open_causes.I3`; the adequacy backstop is disabled for energy-only ERCOT by
market design, so a one-pass under-build has no corrective and lands as LP slack at VOLL). Whether
FR-6 *at this magnitude* is the same finding, or a load-scenario premise that has outrun the
fleet the run is allowed to build, is the desk's call and is **exactly** the question a
declaration must answer rather than paper over. It should be settled before these are declared.

### 4.2 CAPX DESK — 4 runs / 6 pairs

| Run | Idents | Added | Measured |
|---|---|---|---|
| `caiso-2026-2030-d60-arm` | I12, I7 | `14f860fb` 02:26Z | I7 2026–2028: firm 55,030/54,936/57,589 < req 57,306/58,671/60,082 MW; I12 2026–2028: 10.4 / 7.7 / 10.2 % vs band [15.0 %, 30.0 %] |
| `pjm-2026-2030-d60-arm` | I12, I7 | `e9d8263b` 03:06Z | I7 all five years, 2030: firm 168,299 < req 189,450 MW; I12 2026→2030: −9.5 → −16.5 % |
| `pjm-2021-2025-realized-t1h-d62-pubbar` | I7 | `aa5c339c` 02:22Z | 2025: firm 145,855 < req 150,605 MW |
| `neiso-2026-2050-t3-golden3-d60` | I3 | `7ed062ba` 03:57Z | dump leg, not slack: 2043 2.36 % → 2050 7.97 % of renewable potential |

Both `d60-arm` runs look like the case `PREDECL-capx-d60-2026-09-05.md` §6.1 P2/P3/P4 pre-derived
from ratio arithmetic *before* the solve ("FC-1 therefore stays FAIL [I12, I7]") — if so the
declaration is a citation, not new work. `neiso-2026-2050-t3-golden3-d60` is the same dump leg
already declared for GOLDEN-2/GOLDEN-3 (`FINDING-capx-t3-golden2-2026-09-01.md`;
`FINDING-capx-d47-golden3-attestation-2026-09-04.md`; cause
`FINDING-capx-t3-neiso-golden-2026-08-30.md` §6.3(2)) at a slightly different terminal value
(7.97 % here vs 7.74 %), so it needs the D60 arm's own citation rather than a transfer.
`-t1h-d62-pubbar` is a **new supply level** (145,855 MW) against the D57-era 150,605 MW
requirement — it is *not* covered by `d18_note` and shares the open cause of §4.3.

### 4.3 FORECAST-ORCHESTRATOR DESK — 4 runs / 4 pairs (already routed by Y-19, re-routed by Y-22)

| Run | Idents | Added | Measured |
|---|---|---|---|
| `nyiso-2021-2025-realized-t1h-d45r-curveon` | I7 | `cf5425f7` 2026-09-05 14:05Z | 2023: 31,493 < 32,612; 2025: 32,712 < 34,395 MW |
| `pjm-2021-2025-realized-t1h-d45` | I7 | `cf5425f7` | 2025: 138,286 < 144,632 MW |
| `pjm-2021-2025-realized-t1h-d45r` | I7 | `cf5425f7` | 2025: 138,009 < 144,632 MW |
| `pjm-2021-2025-realized-t1h-d57-clearing` | I7 | `cf5425f7` | 2025: 147,585 < 150,605 MW |

**Unchanged from Y-19, and still open.** These four are the *undiagnosed* rows Y-19 deliberately
left undeclared. The systemic cause it named: every T1-H verdict key in `ff-verdicts.json` reads
`FC-1: SKIPPED — "no committed invariant record"` while the registered sidecar **does** carry a
full 14-row I1–I14 block — the one the audit reads. The T1-H scoring convention (canonical
`--hindcast-score --run-config`, no `--invariants`) is a **blind spot, not an absence**, and
`FINDING-capx-d48-2026-09-04.md` P6 is the proof it is live: it recorded "I7 / I12 ungradable"
and was wrong. Y-19 also established the question is answerable from committed artifacts **with
no solve** — the FAIL is one-field attributable in two of the four
(`pjm-...-t1h-d45r-fixed` and `nyiso-...-t1h-d45r` both read `I7 PASS: held`).

`pjm-2021-2025-realized-t1h-d62-pubbar` (§4.2) is a **fifth instance** of the same T1-H pattern
that registered after Y-19 snapshotted; it is routed to capx because that desk registered it, but
the systemic FC-1-blind-at-T1-H cause is this desk's.

---

## 5. Files changed

| File | Change |
|---|---|
| `scripts/lib/invariant_ledger.py` | **new**, stdlib-only. The one policy module. |
| `scripts/register_forecast_run.py` | `enforce_invariant_declaration_gate` + the call in both `main()` branches. |
| `scripts/check_forecast_invariants.py` | `audit_sidecars` delegates FAIL/declared logic to the shared module; adds the baseline-staleness check. Output unchanged. |
| `scripts/register_hindcast.py` | gate call before its direct sidecar write; the lazy `RF` import hoisted to bind once. |
| `scripts/register_forecast_baseline.py` | gate call before its direct sidecar write. |
| `frontend/data/hindcast/invariant-failures.json` | `registration_ratchet_baseline` (20 runs / 29 pairs) + `y24_note`. Additive: 73 insertions, 1 deletion. |
| `tests/scoring/test_invariant_declaration_ratchet.py` | **new**, 22 tests. |

## 6. What is still open after this lane

1. **The 20 declarations.** Routed in §4; the CI job stays red until the desks land them. This is
   the intended state, not a defect.
2. **The magnitude question in §4.1.** ERCOT slack at 8,760 h / 37–53 % of load may or may not be
   the FR-6 finding; the scenario desk should settle it before declaring.
3. **The FC-1-blind-at-T1-H cause** (§4.3), open since Y-19 and now with a fifth instance.
4. **The pre-existing `test_constants_facade` failure** (§2.5 †) — capx lane's, not this one's.
