# Branch-protection memo — required checks on `main` (execute at gate G2)

**To:** owner. **From:** DEBUG-A (debug sweep, 2026-08-14).
**Standing decision:** plan §6 decision 3 (signed 2026-08-13) — *enable after
G2, not before*; this memo is the "exact settings steps" half of that
decision. Nothing here is to be executed now.

## Why (one paragraph)

CI on this repo is advisory in effect: ci.yml triggers only on
`pull_request`, and the working pattern merges PRs (and deletes their
branches) faster than the ~7–15 min run completes, which **cancels the
in-flight run** — of ci.yml's 1,840 lifetime runs, the recent record is
wall-to-wall `cancelled`, with the first `completed` run on record landing
2026-08-14 (run 31765772123) only because that PR stayed open. PR #3624
(the nyiso-128 unregistered field) merged 86 s after creation with three
jobs correctly failing — no gate could have stopped it, because no check is
*required*. Both the `cache-key-pin` job header and HOUSE-1 §3 already
request this change; only the owner can perform it (repo settings).

## Exact steps (GitHub UI)

1. **Settings → Branches → Add branch ruleset** (or classic protection rule)
   for branch pattern `main`.
2. Enable **"Require status checks to pass before merging"** and
   **"Require branches to be up to date before merging"** is *optional* —
   recommend OFF initially (merge-queue velocity; the checks re-run on the
   merge commit anyway is NOT true without it, but requiring up-to-date on a
   repo with multiple merges/hour would thrash; revisit after G3).
3. Add these **required status checks** (exact check names as they appear on
   PRs — these are the ci.yml job `name:` values):
   * `Pinned default cache key` — the isolated frozen-surface signal
     (red ⟺ a moved default key; its own header requests required status).
   * `Cache-key registration guard`
   * `Rule-22 quarantine gates`
   * `Rule-28 mechanism-matrix guard`
   * `Ruff lint + format`
   * `Fast test tier` — **defer this one until PERF-A fixes its checkout.**
     The tier's content is green (six ambient reds fixed on the sweep branch;
     6,836/0 locally), but the job currently dies inside `actions/checkout`
     on every CI run (the ~10 GB full checkout it needs for `data/raw` no
     longer survives on GitHub runners — debug-sweep handoff, CI-health
     section). Requiring it today would block every merge on an
     infrastructure failure. Add it the day PERF-A's checkout fix lands.
   * `Structural refactor guards` — green as of this sweep's branch (the
     `gen_caisoNNN` dangling-ref allowlist entry).
   * `File integrity guard` (from `file-integrity-guard.yml`) if it reports
     a check on PRs — it is the rule-27 shrink guard.
4. **Do NOT (yet) require** these two — they are red on main **by design**
   as other lanes' live signals, and requiring them would freeze all merges:
   * `FR-22 backcast->forecast parity` (two armed-but-undeclared fields —
     the parity ledger is where that signal lives, HOUSE-2 §4);
   * `Forecast-invariant artifact audit` (undeclared I7 on three registered
     PJM forecast runs).
   Add each as required the day its lane clears it — that is a
   one-checkbox follow-up, and G2 review should ask whether they are clear.
5. **Disable owner bypass** for the ruleset (or accept that the 86-second
   pattern continues under bypass — HOUSE-1 §3's caveat). Recommend:
   bypass ON only for "Repository admin" + emergencies, and treat any
   bypass merge as a governance event to be noted in the session log.
6. Merge-queue note: if merges start waiting on the ~8-min fast tier, the
   PERF-A ci.yml sparse-checkout work (plan §3/WS3 item 5) is the wallclock
   lever — checkout is most of the cost — not weakening the required set.

## What this buys

The three incident classes on record become impossible to merge silently:
a moved pinned cache key (#3624's class), a truncated core file (rule 27's
incident class, via the integrity guard), and a red fast tier
(the six-ambient-reds class this sweep just cleared). The two by-design
reds stay visible on every PR without blocking anyone, and graduate to
required as their lanes close them.

---

## APPENDIX — dated check-name refresh, 2026-09-01 (owner ruling **R-P**)

**Status of the standing decision:** plan §6 decision 3 (signed 2026-08-13) said
*enable after G2, not before*. **Owner ruling R-P (2026-09-01, second sitting)
AMENDS that decision on new evidence: FLIP NOW, FAST GATES ONLY.** The evidence
the owner cited: **#4515 merged over a red hard gate**, and the seven
audit-program gate scripts have held green across 60+ PR windows. The memo body
above is unchanged and remains the settings procedure; this appendix replaces
only its §3/§4 **check-name lists**, which have drifted since 2026-08-14.

**The flip itself is the owner's `Settings` action.** No lane performs it, and
nothing in this repository can: it is not a YAML change. This appendix exists so
the names pasted into the ruleset are the ones that actually appear on PRs today.

### The refreshed lists — exact `name:` values, verified against `ci.yml` at `f45766e4`

**REQUIRE** (7 + the shrink guard):

| check name (as it appears on a PR) | source | note |
|---|---|---|
| `Rule-22 quarantine gates` | `ci.yml:75` | also carries **`check_registry_payload_parity`** and **`check_golden_manifest`** (`:118`) — requiring this one covers the board's undercounted seventh gate |
| `Rule-28 mechanism-matrix guard` | `ci.yml:249` | rule 26 enforcement |
| `Cache-key registration guard` | `ci.yml:270` | |
| `Pinned default cache key` | `ci.yml:316` | ⚠️ **RED at this pin — see the blocker below** |
| `Ruff lint + format` | `ci.yml:364` | ⚠️ **RED at this pin — see the blocker below** |
| `Structural refactor guards` | `ci.yml:512` | ⚠️ **RED at this pin — see the blocker below** |
| `FR-21 forecast-board staleness (WARN only)` | `ci.yml:158` | 🆕 **ADDED BY R-P. NAMING CAVEAT, READ IT:** the display name still says *WARN only*, but since R-J this job **carries the HARD `check_gate_a_provenance` step** (`ci.yml:213`). The name is stale, the job is not. Do not skip it on the strength of its title. |
| `file-integrity-guard` | `file-integrity-guard.yml` | the rule-27 shrink guard — ⚠️ **path-filtered; see the second blocker** |

**DO NOT REQUIRE:**

| check name | why, re-verified 2026-09-01 |
|---|---|
| `Fast test tier` | memo §3 deferral stands. **And it is now red on content, not only on checkout**: run 2278 (#4535) ran the tier to completion in 8.5 min and it **FAILED**. |
| `FR-22 backcast->forecast parity` | **re-verified red at `f45766e4`: `check_forecast_parity` exit 1, 7 armed-but-undeclared fields** (ERCOT ×3, NYISO ×2, CAISO ×1, MISO ×1). A live calibration-desk signal, exactly as memo §4 describes. One of the seven, `caiso_offer_surface_measured_ungrounded`, is the caiso-231 keeper promotion of 2026-09-01. |
| `Forecast-invariant artifact audit` | unverified; stays out until its own lane clears it. Red on run 2278. |

### 🔴 BLOCKER 1 — THREE OF THE SEVEN PROPOSED REQUIRED CHECKS ARE **RED ON `main` RIGHT NOW**

Measured against **run 2278**, the most recent *completed* `ci.yml` run at this
pin (#4535, head `d9c5d4b1`), and reproduced locally against base-branch content:

| proposed required check | run 2278 |
|---|---|
| Rule-22 quarantine gates | 🟢 success |
| Rule-28 mechanism-matrix guard | 🟢 success |
| Cache-key registration guard | 🟢 success |
| FR-21 forecast-board staleness | 🟢 success |
| **Pinned default cache key** | 🔴 **failure** |
| **Ruff lint + format** | 🔴 **failure** — 5 errors: three `F821` undefined names in `src/market_sim/runner.py` (`entry_walks`, `entry_reserve_adders`, `build_nyiso_link_loss`) and two dead-code lints in `scripts/gen_caiso197_attestation.py` |
| **Structural refactor guards** | 🔴 **failure** at *facade re-export + persisted-identity tests* |

**Flipping the ruleset with the list as written would freeze every merge on this
repository immediately** — the precise outcome memo §4 was written to prevent,
now arriving through §3 instead of §4.

**The evidence R-P cites is real but is about a different set of seven.** "Seven
gates holding green" is the **seven audit-program gate scripts** — `audit_keepers`,
`check_registry_payload_parity`, `check_mechanism_matrix`,
`check_forecast_staleness`, `check_bench_freshness`, `check_gate_a_provenance`,
`check_golden_manifest` — every one of which exits **0** at `f45766e4`. Those seven
are **not** the seven CI *jobs* this appendix proposes to require. Four of the
proposed jobs are the green ones; three are jobs no audit-program script covers.

**Recommended sequencing, offered to the owner and decided by nobody else:**
require the **four green checks now** (they close the #3624 incident class, the
rule-27 shrink class and the rule-22/26 classes on day one), and add the other
three **the day their lanes go green** — the same one-checkbox follow-up memo §4
already prescribes for FR-22 and the invariant audit. That executes R-P's
*"flip now, fast gates only"* without the freeze.

### 🟠 BLOCKER 2 — `file-integrity-guard` IS PATH-FILTERED AND WILL BLOCK DOCS-ONLY PRs FOREVER

Its `pull_request` trigger filters to `src/**`, `scripts/**`, `CLAUDE.md`,
`model-methodology-spec.md`, `.github/workflows/**`. A PR touching none of those
— **every records-lane PR, this one included** — never reports the check at all,
and GitHub treats a required check that never reports as *pending*, not as
*passed*. Memo §3's *"if it reports a check on PRs"* qualifier is doing real work
here and must not be dropped: either require it **and** widen its path filter (or
add an always-run no-op job), or leave it unrequired.

### Execution state at `f45766e4` — observed, not assumed

**The flip is NOT live at this pin.** Observable evidence, from the merge record
rather than from repository settings (which a lane cannot read): **#4535 was
created 17:54:17Z and merged 17:54:33Z — 16 seconds**, while its own `ci.yml`
run did not complete until **18:04:18Z**, ten minutes later, with six jobs
failing. **#4534 merged 6 seconds after creation.** No required-status-check
ruleset was in force for either. The 86-second pattern the memo body describes is
therefore still live and is now a **16-second** pattern.

*(Recorded by the audit-program records lane v19b at pin `f45766e4`. This lane
performed no settings action, and none is within its power.)*
