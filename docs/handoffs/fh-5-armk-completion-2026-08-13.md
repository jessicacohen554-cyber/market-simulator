# FH-5-ARMK — CAISO Arm K landed; Phase B closes at 12/12

**Session.** FH-5-ARMK `[OPUS]`, branch `claude/caiso-arm-k-fh5-z4wd2n`, off
`origin/main` `5b05f84`. Solve lane. **Complete.**

**Deliverables, all committed and pushed.** Pre-registration
`docs/handoffs/PREREG-fh5-armk-2026-08-13.md` (committed before the solve);
run bundle + sidecar + crossover report; the completion record as
**`fh-5-phase-b-2026-08-11.md` §8**, appended — §1–§7 are byte-untouched (the
diff is 224 insertions, **0 deletions**).

---

## 1. Headline

**`caiso-2021-2025-t1ff-armk-fh5`, runtime key `05289c2965f04734`.** Solved
`[2021, 2023, 2024, 2025]`, bridged `[2022]`, `leakage_violations: []`, holdout
freeze ACTIVE at launch. **I6 rider PASSES** — so the rider now passes on **all
twelve** FH-5 arms, and this arm's reads are quotable.

**No FH-5 adjudicated claim changes.** §4.1's headline survives cell-for-cell.

## 2. The one thing to read carefully

**§4.1's headline survives, but it could not have done otherwise, and the
distinction matters.** The dominance table is computed from **Arm R only** —
`fh5_horizon_table.py` reads `phases["A"]["R"]` / `phases["B"]["R"]` and never
touches an Arm K block. An Arm K result has **no power** to move those 13 cells.
The re-test was run because §4.1 was pre-registered for re-test, and it returned
identical numbers; it is reported as a **null**, not as corroboration. Anyone
quoting "the headline was re-confirmed when the twelfth arm landed" would be
overstating what the instrument can do.

## 3. What the arm does change — §5 gains a CAISO row, and it is a sign flip

CAISO joins MISO as an ISO whose **Arm K lands closer to actual than its own
Arm R**, in two of three years. Arm K has strictly *less* information (forecast
gas, not realized gas), so this is compensation, never skill — and CAISO makes
the mechanism fully legible, because all three years line up:

| Year | AEO2021 gas error | Arm R signed | Arm K signed | K−R price move | \|K\|−\|R\| |
|---|---|---|---|---|---|
| 2023 | **+22.0 %** | −0.1564 | −0.0703 | **+0.0861** | −0.086 *(better)* |
| 2024 | **+34.7 %** | +0.2248 | +0.3700 | **+0.1452** | +0.145 *(worse)* |
| 2025 | **−12.2 %** | +0.4907 | +0.4250 | **−0.0657** | −0.066 *(better)* |

The price move always carries the **sign of the gas error**; whether it helps is
decided purely by which way Arm R's own bias already pointed. This is the phase's
cleanest demonstration that a better-scoring Arm K is not a better forecast.

**A caveat about §5's own metric, worth the manager's attention.** CAISO's
Phase-A 2023 spread of **+0.046** is the smallest number in §5's table and invites
the reading that CAISO is insensitive to the gas vintage. **It is not** — the
signed price move there is **+0.3986**, among the largest in the phase. The
spread is small only because the move carried the error *across zero*
(−0.1765 → +0.2221), so the two absolute values nearly coincide. `|err_K| −
|err_R|` understates the driver effect whenever an arm's bias changes sign. This
refines how §5's table is read and strengthens rather than disturbs its
conclusion. **No edit was made to §5** — the correction lives in §8.5.

Incidentally measured: CAISO gas pass-through (price move ÷ gas error) is stable
at **~0.35–0.55 across two AEO editions and two horizons**. Observation only;
nothing was tuned to it.

## 4. Durable fix shipped: §4's table is now reproducible

§4's table was reproducible **exactly once**, in the container that produced it.
`fh5_horizon_table.py` globs `results/hindcast/…/crossover_score.json`;
`results/` is gitignored and dies with its container, so a fresh container
renders every absent arm as an em dash **without announcing the gap** — a silent
degradation of the program's headline table.

`scripts/probes/fh5_rehydrate_scores.py` (new, 111 lines) closes it. Each
committed sidecar's `score` block **is** that arm's `crossover_score.json`
verbatim, so it writes them back into the path shape the probe globs. It
re-derives nothing — no metric, no parquet, no solve. Validated before use:
rehydrating the 23 sidecars registered *before* this arm reproduces §4.1's 13
rows cell-for-cell and all 14 checkable values of §5's spread table.

## 5. The pin

`3ae7465`'s `src/` and `scripts/` **plus only** the additive CAISO-2021 vintage
delta. `git diff 3ae7465 -- scripts/` **EMPTY**; `src/` differs in `constants.py`
alone (3 hunks, +54/−8, all inside the vintage registry, region byte-identical to
HEAD). Worktree-only, dropped after registration; no commit reverts anyone's work.

**Siblings provably unaffected:** the Arm K config key at this pin is
`4dcb08ecf9fecfc6`, *identical* to the key §1.3 recorded when the CAISO row was
still absent — the cache key hashes the vintage **selector**, not the table. The
additivity claim is measured, not asserted.

Also verified: `score_crossover`, `register_hindcast`, `register_forecast_run`,
`check_forecast_invariants`, `run_capacity_hindcast` and `regenerate_clean` are
**byte-identical between `3ae7465` and HEAD**, so the pin's only reach is `src/`.

## 6. Environment — three items for the manager

1. **The half-dead container recurred (4th+ occurrence).** The clone arrived with
   2,483 staged deletions, a missing worktree and a stale `.git/index.lock`.
   Recovered per the standing recipe before the branch was cut; `data/raw`
   restored to 9.6 GB, worktree to 0 pending, **no blob fetched from the remote**.
   Cost roughly 20 minutes. It is now frequent enough to be worth a root cause.

2. **`git push` fails with HTTP 408/500 under the default HTTP/2 negotiation.**
   Reproduced on a **32 KB, 5-object** pack, so it is **not** pack size — six
   consecutive failures. **`git config http.version HTTP/1.1` fixes it** and every
   push since has succeeded first try. Worth adding to the Git & Pushing section
   of `CLAUDE.md`: without it a lane can wrongly conclude its pack is too large
   and fall back to `push_files`, which **cannot** carry a sidecar (747 lines here,
   over the ≥300-line rule-27 bar).

3. **Stray remote branch to delete: `tmp-transport-probe-armk`.** Created to
   isolate item 2 and left behind because `git push --delete` fails on this
   transport (four attempts) and no branch-delete MCP tool is exposed. It is a
   duplicate of the prereg commit with no PR. One `git push origin --delete
   tmp-transport-probe-armk` from a working client removes it.

4. **`regenerate_clean.py` reported `1/50 datatype(s) failed`, and WHICH one is
   not recoverable from this session's artifacts.** The prereq was run as
   `regenerate_clean.py 2>&1 | tail -40`, so only the last 40 lines were ever
   written and the `[fail]` line was discarded at the pipe. Stated plainly
   because it is a gap in this session's record, not a resolved item.

   **What bounds it.** All 50 known datatypes have non-empty clean output and no
   clean directory is empty, so nothing failed before writing. The only three
   datatypes with no clean directory at all (`benchmark-corridor`,
   `dam-public-bids`, `reserve-requirements`) were each re-run individually and
   all three exit **green** — they are documented no-raw-rows skips, not the
   failure. The failing datatype therefore wrote output and returned non-zero
   afterwards, most likely one ISO inside a per-ISO loop.

   **Why it did not reach this arm.** The solve resolved every input it needed
   and would have failed loudly otherwise: `check_clean_partitions` raises
   `DegradedInputError` for an armed flag whose partition is absent, and neither
   guarded flag (`capacity_deliverability_limits`, `hydro_ror_split`) is armed
   here. All four years solved, all supported metrics scored, and 12 of 14
   invariants pass with the two FAILs matching the Arm R sibling exactly — I7 to
   the megawatt. A full re-run with an untruncated log was launched to identify
   it; if this handoff carries no follow-up line, that re-run did not finish
   inside the session.

   **Process fix for the next solve lane: never pipe `regenerate_clean.py`
   through `tail`.** Redirect the whole log to a file and grep it — the summary
   line reports a failure count without naming the datatype, so the naming line
   is the only record there is.

## 7. Governance close-out

- **Rule 22.** Solve years `{2021, 2023, 2024, 2025}`; 2021 unscored seed, 2022
  bridged; scoring never left 2023–2025. **CAISO needed no `complete`/`final`
  marker and holds none.** Holdout freeze ACTIVE, read at launch, untouched. No
  measured H1-2026 contact.
- **Rule 15.** Hindcast namespace only; backcast registry untouched.
- **Rules 1 / 13 / 14.** Nothing tuned. I7/I9 FAILs, I12 WARN, fuelmix gaps and
  the Arm K compensation all reported at full magnitude and left standing.
- **Rule 28.** No new mechanism, no new `ScenarioConfig` field ⇒ no matrix row
  owed, no verdict cell moved; `check_mechanism_matrix.py` run before push.
- **Rule 23 / E10.** No keeper promoted; no attestation owed.
- **Rule 27.** Opus. §8 was **appended**, never regenerated; the 747-line sidecar
  went over `git push` and every pushed blob was verified byte-identical to local.
  No new GitHub Actions workflow.
- **Rule 12.** One invocation, four solve-years sequential; nothing co-ran.

## 8. What is NOT done

- **Nothing outstanding in this lane.** FH-5 Phase B is 12/12.
- §7's recommendation (do **not** charter a pre-2021 base) is untouched and
  unaffected — this arm adds no evidence either way, and §7.1's blocker (the
  empty hydro-climatology window at base 2020, which degrades **silently**)
  remains open and is still worth fixing on its own merits.
