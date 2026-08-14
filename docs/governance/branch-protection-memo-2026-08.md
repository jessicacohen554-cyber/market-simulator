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
