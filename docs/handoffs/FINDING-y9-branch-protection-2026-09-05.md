# FINDING — Y-9 branch-protection flip: ROUTE 2 (owner click-path required)

**Session:** Y-9 branch-protection flip, audit-program director dispatch, 2026-09-05 21:20Z
**Ruling:** owner ruling R-AP (card J), executing R-AL / R-AH
**Director pin:** `origin/main` cf5425f7 (working tip at session close: 49647dd6)
**Repo:** `jessicacohen554-cyber/market-simulator`, branch `main`
**Outcome:** **ROUTE 2.** The flip was **NOT** applied. `main` is still unprotected.
The owner must perform the click-path in §4.

---

## 1. Before-state (recorded 2026-09-05T21:29:40Z)

Route-1 probe, `GET /repos/jessicacohen554-cyber/market-simulator/branches/main/protection`,
`Authorization: Bearer $GH_TOKEN`:

```
HTTP_STATUS=403
{"message":"GitHub access is not enabled for this session. An org admin must connect the Claude GitHub App for this organization.","documentation_url":"https://docs.anthropic.com/en/docs/claude-code/github-actions"}
```

The dispatch anticipated a 404 (unprotected) as the before-state. The 404 was
never reachable — see §2. The unprotected before-state is instead established
from the sanctioned GitHub path (`mcp__github__list_branches`, same timestamp):

```json
[{"name":"claude/nyiso-192-frontier-adjudication-mo2nrq","sha":"ebfe1c2e0c7d77b7b6512bdee7ee62edbfe275f3","protected":false},
 {"name":"main","sha":"49647dd68f88acc3eeaa5ad7d775de0cd7fb1355","protected":false}]
```

`main` → `"protected": false`. This is the same fact the 404 would have carried.

## 2. Why ROUTE 1 is closed — two independent grounds

The dispatch's route-2 trigger was "the PUT returns 403 (admin scope missing,
expected for an app token)". A 403 did occur, but **it is not that 403**, and the
distinction changes what the owner should conclude:

1. **The egress proxy refuses `api.github.com` for this session class outright.**
   The 403 body above is the *agent proxy's* policy denial, not GitHub's. It was
   returned on a `GET`, before any `PUT` was attempted — so no GitHub credential
   was ever evaluated, and **nothing was learned about `$GH_TOKEN`'s admin
   scope**. Per `/root/.ccr/README.md` ("do not retry organization policy
   denials (403/407) — report them instead") and the dispatch's own STOP
   instruction, the probe was not retried and no second credential was tried.
2. **The sanctioned GitHub path exposes no branch-protection tool at all.** The
   `github` MCP server is the only GitHub route this session has (it tunnels via
   `mcp-proxy.anthropic.com`, which bypasses the egress proxy — which is why
   `list_branches` in §1 succeeded where raw `curl` did not). Its toolset has no
   branch-protection, ruleset, or generic-API call. Searched and confirmed: the
   nearest tools are `create_branch`, `list_branches`,
   `update_pull_request_branch`, `enable_pr_auto_merge` — none can set required
   status checks.

So route 1 is unavailable **by environment class**, not by token scope. Re-running
this dispatch in another Claude session will not change the outcome; the flip is
an owner-console act until either the direct API host is allowed or the MCP
toolset grows a protection tool.

Session identity, for the record — `mcp__github__get_me`:
`login: jessicacohen554-cyber, id: 260524936` (the repo owner's own account; the
constraint is the transport, not the identity).

## 3. Check names — verified verbatim against `ci.yml`

A typo in a required check name deadlocks every PR (the name never reports, so it
stays pending forever). All six were verified against the job `name:` values in
`.github/workflows/ci.yml` at 49647dd6 — **exact match, including the `+` and the
capitalisation**:

| Required check name (paste verbatim) | `ci.yml` job key | line |
| --- | --- | --- |
| `Ruff lint + format` | `lint` | 393 |
| `Pinned default cache key` | `cache-key-pin` | 345 |
| `Structural refactor guards` | `refactor-guards` | 541 |
| `Cache-key registration guard` | `cache-key-guard` | 299 |
| `Fast test tier` | `fast-tests` | 416 |
| `Rule-22 quarantine gates` | `quarantine-gates` | 104 |

**Deliberately NOT required** (board Z-2, v26) — do not tick these:
`FR-22 backcast->forecast parity` (line 246) and
`Forecast-invariant artifact audit` (151) are chronically red by design and would
deadlock every PR; `FR-21 forecast-board staleness (WARN only)` (187) and
`Rule-28 mechanism-matrix guard` (278) are advisory; `file-integrity-guard` lives
in its own workflow and is out of scope for this flip.

## 4. ROUTE 2 — the click-path for the owner

In `github.com/jessicacohen554-cyber/market-simulator`:

1. **Settings → Branches → Add branch ruleset** (or **"Add classic branch
   protection rule"**).
2. Branch name pattern: `main`
3. Tick **"Require status checks to pass before merging"**.
4. Leave **"Require branches to be up to date"** **UNTICKED** — strict mode is
   OFF. (Merge cadence is ~15 PRs/hour; strict would serialise it.)
5. Search and add these six, exactly as written:
   - `Ruff lint + format`
   - `Pinned default cache key`
   - `Structural refactor guards`
   - `Cache-key registration guard`
   - `Fast test tier`
   - `Rule-22 quarantine gates`
6. **Save.**

**Nothing else ticked.** "Require conversation resolution" OFF. "Include
administrators" left unchanged. No required reviews, no push restrictions.

Equivalent API body, if the owner runs it from an admin-scoped context elsewhere
(`PUT /repos/jessicacohen554-cyber/market-simulator/branches/main/protection`):

```json
{"required_status_checks":{"strict":false,"contexts":["Ruff lint + format","Pinned default cache key","Structural refactor guards","Cache-key registration guard","Fast test tier","Rule-22 quarantine gates"]},"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null}
```

## 5. NEW — a live gap in the R-AE path-filter remedy, to settle BEFORE clicking

Surfaced while verifying §3; not part of the dispatch, and **not fixed here**
(widening the filter is an owner decision, as `ci.yml`'s own comment block says).

R-AB / R-AE identified the path-filter trap — a workflow skipped by path
filtering leaves its checks *Pending*, so a PR touching only unenrolled paths is
blocked forever once those checks are required — and remedied it by enrolling
three doc paths in `ci.yml`'s `pull_request.paths`:

```
- "docs/handoffs/audit-program-director-board-2026-08.md"
- "docs/model-audit-release-plan-2026-08.md"
- "docs/FINDING-*.md"
```

**`docs/FINDING-*.md` does not match `docs/handoffs/FINDING-*.md`.** In GitHub
path filters a single `*` does not cross `/`. Measured at 49647dd6:

- `docs/FINDING-*.md` — **171** files, enrolled.
- `docs/handoffs/FINDING-*.md` — **76** files, **NOT enrolled** by that glob or
  by any other pattern in the list.

`docs/handoffs/` is the live convention for the current program — the six most
recent findings all sit there (`FINDING-capx-d50…`, `-d53`, `-d56r`, `-d56r2`,
`-d57`, `-d59`, all 2026-09-04/05). **This very file is one of them.** So after
the flip, a records/finding PR carrying only a `docs/handoffs/FINDING-*.md` file
triggers no CI, and its six required checks stay pending forever — precisely the
deadlock R-AE set out to prevent, on the path the program actually writes to.

This PR is unaffected: it is opened *before* the flip, while `main` is still
unprotected. The next one would not be.

**Options for the owner (not exercised here):** add `docs/handoffs/FINDING-*.md`
(and, if wanted, `docs/handoffs/*.md`) to `ci.yml`'s `pull_request.paths` before
clicking Save in §4; or accept the deadlock and merge such PRs administratively.
The `ci.yml` comment block's reasoning against a name-matching passthrough
workflow is untouched by this and still holds.

## 6. Close state

| | |
| --- | --- |
| Route taken | **2** (owner click-path) |
| Flip applied by this session | **No** |
| `GET /branches/main` → `protected` at close | **`false`** |
| Timestamps (UTC) | probe 21:29:40Z · finding written 21:30:47Z · 2026-09-05 |
| Files changed | this file only. No solve, no `ci.yml` edit, no other file. |

`main` remains unprotected until the owner performs §4.
