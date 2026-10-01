# FINDING — capx D89-R: the charter's premise was stale; D89 had already landed, and its repair verifies clean

**Lane:** capx D89-R (the r#61 re-emission) · **Date:** 2026-09-08 · **HEAD:** `d1b8d1bf` · **ZERO LP** (none spent, none needed).
**Authority:** owner ruling Q61 (2026-09-08, capx ledger §0be.3(b)) — "Charter D89 for capx's own 27; fix none of the other 28."
**Scope:** verification only, plus one stale literal in a comment. No `src/` change, no default moved, no arm, no registration, no mechanism-matrix cell.

## Lead

**The charter's premise — "NEVER DISPATCHED (no branch, no commit, no document, confirmed on a second fetch)" — is false at my HEAD.**
D89 ran and landed via **PR #5642**, branch `claude/d89-test-failures-diagnosis-ttunic`, merged at `e7e492c5`
(commits `0bd0017f`, `73ece848`, `15ee020c`). The charter looked for `claude/capx-d89-d62-d74-reds`, which never existed — see §4.

So this lane did not repair the 27. It **re-derived the diagnosis independently and audited the landed repair**, which is
the useful thing left to do. The result:

- **All 27 are green at my HEAD**, and the classification is **(A) FIXTURE ROT, 27 of 27, zero (B), zero unclassified** —
  reproduced from scratch, not copied.
- The repair is **sound and non-vacuous**, established by a mutation test the first lane did not run (§1.4).
- **D74's self-executing DO-NOT-ARM stands**, on evidence I verified has not moved.
- Wide count at my HEAD: **28 failed** (the first lane measured 30 at `4e4ad90d`). Two closed in between; neither was mine.
- **Fixed 0, newly broken 0** — because there was nothing left to fix. My only edit is a rotting literal in a comment (§6).

## §0 — the 27-row classification table (the deliverable)

**Reproduced at MY HEAD**, not inherited: I checked the three repaired files back to `0bd0017f^` in the working tree
and re-ran the two files, giving **27 failed, 26 passed in 0.53 s** — exactly the charter's denominator, 15 in D62 and
12 in D74, ids identical to the first lane's. Files were then restored (`git status` clean but for §6).

| # | Test | Failing assertion | A/B | Cause | Action |
|---|---|---|---|---|---|
| 1 | `D62::TestVintageRuleFromTheData::test_delivery_years_through_2025_26_read_the_first_column[2021]` | `published_bar_per_kw_yr("PJM", fuel, 2021)` raises before `assert got is not None` | **A** | C1 | R1 |
| 2 | `…_read_the_first_column[2022]` | same, year 2022 | **A** | C1 | R1 |
| 3 | `…_read_the_first_column[2023]` | same, year 2023 | **A** | C1 | R1 |
| 4 | `…_read_the_first_column[2024]` | same, year 2024 | **A** | C1 | R1 |
| 5 | `…_read_the_first_column[2025]` | same, year 2025 | **A** | C1 | R1 |
| 6 | `D62::TestVintageRuleFromTheData::test_delivery_years_from_2026_27_read_the_second_column[2026]` | `published_bar_per_kw_yr("PJM", fuel, 2026)` raises before `assert got is not None` | **A** | C1 | R1 |
| 7 | `…_read_the_second_column[2027]` | same, year 2027 | **A** | C1 | R1 |
| 8 | `…_read_the_second_column[2035]` | same, year 2035 | **A** | C1 | R1 |
| 9 | `…_read_the_second_column[2050]` | same, year 2050 | **A** | C1 | R1 |
| 10 | `D62::TestVintageRuleFromTheData::test_the_na_limb_is_named_not_silent` | `published_bar_per_kw_yr("PJM", "gas_st", 2023)[1] == "first_published"` — raises on the call | **A** | C1 | R1 |
| 11 | `D62::TestVintageRuleFromTheData::test_the_published_bars_are_the_d61_operand` | `resolve_going_forward_bar_per_kw_yr(cfg_armed, fuel, 2022)` raises through the armed gate | **A** | C1 | R1 |
| 12 | `D62::TestVintageRuleFromTheData::test_the_multiplier_does_not_apply_to_the_published_bar` | same resolver, armed gate, `coal`/2022 | **A** | C1 | R1 |
| 13 | `D62::TestReactiveLeg::test_reactive_is_the_published_row` | `assert None == 2199.0 ± 0.002199` (file line 236) | **A** | **C2** | R1 |
| 14 | `D62::TestReactiveLeg::test_offer_equals_exit_identity_on_a_toy_stack` | `resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2022)` raises on the armed leg of the `(None, {"PJM": True})` loop | **A** | C1 | R1 |
| 15 | `D62::TestReactiveLeg::test_reactive_credit_is_once_and_only_when_armed` | `TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'` at `pmax * rate` (file line 270) | **A** | **C2** | R1 |
| 16 | `D74::TestThePredicateIsTheData::test_steam_oil_and_gas_has_no_default_through_2025_26[2022]` | `no_default_cap_class("PJM", "gas_st", 2022)` raises before `is True` | **A** | C1 | R1 |
| 17 | `…_has_no_default_through_2025_26[2023]` | same, year 2023 | **A** | C1 | R1 |
| 18 | `…_has_no_default_through_2025_26[2024]` | same, year 2024 | **A** | C1 | R1 |
| 19 | `…_has_no_default_through_2025_26[2025]` | same, year 2025 | **A** | C1 | R1 |
| 20 | `D74::TestThePredicateIsTheData::test_the_class_reenters_the_screen_when_the_table_publishes[2026]` | `no_default_cap_class("PJM", "gas_st", 2026)` raises before `is False` | **A** | C1 | R1 |
| 21 | `…_reenters_the_screen…[2027]` | same, year 2027 | **A** | C1 | R1 |
| 22 | `…_reenters_the_screen…[2030]` | same, year 2030 | **A** | C1 | R1 |
| 23 | `…_reenters_the_screen…[2040]` | same, year 2040 | **A** | C1 | R1 |
| 24 | `D74::TestThePredicateIsTheData::test_every_class_with_a_published_value_is_screened[2022]` | `no_default_cap_class("PJM", "coal", 2022)` raises before `is False` | **A** | C1 | R1 |
| 25 | `…_every_class_with_a_published_value_is_screened[2025]` | same, year 2025 | **A** | C1 | R1 |
| 26 | `…_every_class_with_a_published_value_is_screened[2026]` | same, year 2026 | **A** | C1 | R1 |
| 27 | `…_every_class_with_a_published_value_is_screened[2030]` | same, year 2030 | **A** | C1 | R1 |

**Cause C1 (25 rows), measured.** `--tb=line` over the pre-repair tree counts **exactly 25** occurrences of
`market_sim.data.avoidable_cost_rate.PublishedBarUnavailable: no published avoidable-cost-rate partition for PJM`
raised at `src/market_sim/data/avoidable_cost_rate.py:193`. The seam's `_read` returns `None` because
`data/clean/capacity-market-avoidable-cost-rate/` — a **DERIVED, gitignored** partition — does not exist in a fresh
checkout, and nothing in the test tier built it.

**Cause C2 (2 rows), measured.** The same missing partition reached through `reactive_offset_per_mw_yr`, which
**degrades to `None`** instead of raising. `--tb=line` counts exactly one `assert None == 2199.0 ± 0.002199` and one
`TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'`. 25 + 2 = 27; **zero unclassified**.

**Action R1 (all 27), as landed.** `@requires_raw(PUBLISHED_ACR_RAW_CSV)` (carries `fulldata` **and** skips honestly when
the tracked CSV is absent) plus `@pytest.mark.usefixtures("published_acr_clean_dir")`, a `tests/conftest.py` fixture that
curates the tracked raw CSV through the **real intake** into a scratch `CLEAN_DIR`. **No assertion was changed.**

**What live source the assertions now read.** `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` (PJM Manual 18
Rev 62 §5.4.8.4(B)), resolved through `scripts.lib.capacity_market_avoidable_cost_rate.raw_dir_for("PJM", paths.RAW_DIR)`
— the intake's own path function, imported not copied — curated by the production script
`scripts/data/curate_capacity_market_avoidable_cost_rate.py`. Nothing was re-frozen to a build artifact.

## §1 — why it is (A), on my own measurements

Four checks. Any one would have caught a (B); checks 1–3 re-derive the first lane's, check 4 is new.

1. **The mechanism path has not moved since D62/D74 landed.** `git log` at my HEAD shows
   `src/market_sim/data/avoidable_cost_rate.py`, `scripts/lib/capacity_market_avoidable_cost_rate/`,
   `scripts/data/curate_capacity_market_avoidable_cost_rate.py` and the raw CSV **all last changed at `3006b645`
   (2026-09-06)** — the merge that brought D62/D74 in — and **nothing since**.
2. **The one later commit on any audited file cannot be the cause.** `src/market_sim/config/capacity_market.py` moved once,
   at `dc96602e` (capx D84). Measured: the diff has **0 removed lines** (purely additive) and matches
   `resolve_capacity_going_forward_bar_published` / `resolve_capacity_no_default_cap_convention` **0 times**.
3. **The repair passes with `data/clean` genuinely absent.** `ls -d data/clean` → no such file on this host, and the two
   files give **53 passed in 1.79 s**. The fixture builds what it needs; the result does not depend on host state.
4. **NEW — the assertions are live, not vacuous.** I perturbed one published value in the tracked CSV
   (`Nuclear – Multi Unit` gross ACR `445 → 999`) and re-ran: **6 failed, 47 passed**. Restored byte-for-byte
   (sha256 `5bec3ce4…` before and after, `git status` clean for `data/raw`). A fixture that built a partition the
   assertions did not actually read would have stayed green — it did not.

**Consequence for D74's DO-NOT-ARM: it stands, on unmoved evidence.** The refusal rests on the assertions in
`TestThePredicateIsTheData`; every one reproduces to the value it was written against, and check 1 shows the code
behind them has not moved a byte.

**Consequence for D62's landed state: unchanged, still default-off.** Verified directly:
`capacity_going_forward_bar_published_by_iso` and `capacity_no_default_cap_convention_by_iso` are both `= None` in
`scenarios.py`, both declare cache-key drop value `"None"`, and **neither appears in `iso_configs.py`** — no ISO arms
either one.

**All four lane behaviours reproduce** (my runs, not quoted):

| Lane | Result at my HEAD |
|---|---|
| fast tier, `-m "not slow and not integration and not fulldata"` | 23 passed, **30 deselected** |
| wide, `data/raw` hydrated, `data/clean` absent | **53 passed** |
| pre-repair files, same host | **27 failed**, 26 passed |
| raw CSV moved aside | 23 passed, **30 skipped** with a named reason (restored, sha256 identical) |

## §2 — the wide-command counts

Command, stated per §0be doctrine — **a red inventory is only as wide as the command that produced it**:

```
uv run python -m pytest tests/unit tests/scoring tests/regression -q -rf
```

Python 3.11.15, `uv sync` at `uv.lock`, no `-m` filter, no `-n` xdist. `data/raw` hydrated (6.3 G), `data/clean` **absent**.

| Run | Result |
|---|---|
| **my HEAD `d1b8d1bf`** | **28 failed**, 7156 passed, 56 skipped, 1 xfailed, 539 subtests passed — 1014.02 s |
| first D89 lane, repaired arm at `4e4ad90d` | 30 failed, 7124 passed |
| **re-run after this lane's edits** | **28 failed**, 7156 passed, 56 skipped, 1 xfailed, 539 subtests passed — 960.16 s |

The charter's step 5 re-run is the third row: the failed-id set is **byte-identical** to my HEAD measurement (`diff` empty), which is the direct evidence that the comment-only edit is inert. **0 of 28 are D62/D74.**

**Fixed 0, newly broken 0 — there was nothing left to fix.** The 27 were already green when I arrived; I proved they
are green *for the right reason* rather than assuming it. Of the D62/D74 set, **0 of 27 appear in my failed list.**

**28, not 30.** Two closed between the two measurements, neither by me:

| Closed red | Closed by |
|---|---|
| `test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned[PJM]` | `203c031e` (spp-49, 2026-09-08) — advanced the pin |
| `tests/scoring/test_gate_a_provenance.py` (1) | the r#61 gate-(a) re-key; the test file itself is unchanged since `3006b645`, so the repair was to the data it reads |

The charter predicted the second ("the gate-(a) red has since been repaired by another lane, so your count may
legitimately be lower"). It is confirmed, and the first is a second such closure the charter did not know about.

## §3 — the other 28: inventoried, not touched

Fixed none of these. Owners named per the charter's routing.

| File / test | Count | Owning desk |
|---|---|---|
| `tests/scoring/test_golden_manifest_provenance.py` | 7 | golden-manifest provenance |
| `tests/regression/test_soundness.py` (`TestEndToEnd`) | 6 | test_soundness end-to-end |
| `tests/unit/results/test_export.py` (`TestExportScenarioJson`) | 4 | results/export |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF readiness battery |
| `tests/scoring/test_forecast_parity.py` | 2 | **MISO** — miso-233 arms three `miso_seam_neighbour_*` fields with no `forecast_parity_registry` declaration |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | **CAISO** — registry 1.166 vs artifact 1.154 |
| `tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none` | 1 | **SPP** — SPP now has an RPS floor, so `get_rps_target("SPP", 2030)` is `0.0`, not `None` |
| `tests/scoring/test_registration_marker_gate.py` | 1 | registration-marker gate |
| `tests/scoring/test_backcast_artifacts.py` | 1 | backcast artifacts |
| `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` | 1 | **capx D84** — `capacity_market` grew `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`, facade not re-exporting it |
| **Total** | **28** | |

**capx D84's remaining obligation.** Of the pair the first lane routed to D84, the solve-surface pin is now **closed**
(spp-49 advanced it). The facade re-export is **still open** and is a one-line addition, not a judgement call. Routed,
not taken.

## §4 — SYSTEMIC: "never dispatched" was a false negative, and it is branch-name-based

The charter states D89 was never dispatched, "confirmed on a second fetch". It had in fact landed hours earlier.
The mechanism is mundane and will recur:

- The charter proposed branch `claude/capx-d89-d62-d74-reds`.
- The harness assigned the running session **`claude/d89-test-failures-diagnosis-ttunic`** and it merged as PR #5642.
- `git branch -r | grep d89` at my HEAD returns **only** `origin/claude/capx-d89-test-diagnosis-x3r6uz` — this
  session's own harness-assigned branch. **The charter's proposed name has never existed as a ref**, for either lane.

**A dispatch check keyed on the charter's proposed branch name therefore cannot ever succeed**, because the harness
mints its own name with a random suffix and ignores the charter's. This is not the r#61 doctrine
("THE QUEUE'S MIDDLE AND TAIL ARE WHERE LANES GO MISSING") — that doctrine says lanes silently *don't start*; here the
lane started, finished, and merged, and the detector could not see it.

**Recommended detector, and it is cheap:** check for the lane's **exit artifact** (`docs/handoffs/FINDING-capx-<id>-*.md`)
or grep the merge subjects (`git log --merges --oneline | grep -i <id>`) — both would have returned the landed D89 on the
first try. Offered to the director; not acted on here beyond §6's ledger annotation.

**Cost of the miss:** one duplicated Opus session. Left uncorrected, the ledger's two "NEVER DISPATCHED" rows would
have produced a third.

## §5 — two factual corrections to `FINDING-capx-d89-2026-09-08.md`

Neither changes its conclusion, which I independently confirm. Both are the class of stale literal this desk exists to catch.

1. **"tracked at 2.5 KB"** (in the finding and in a `test_d62…` comment). Measured: the CSV is **10,661 bytes / 17 rows**,
   and `git log` shows it unchanged since `3006b645` — i.e. it was 10,661 bytes when that sentence was written. Repaired
   forward in §6 by **dropping the size claim**, not by re-freezing today's number.
2. **`git diff 9d9ffacd HEAD` is not reproducible.** `9d9ffacd` is **not a revision in `main`** (`fatal: bad revision`) —
   a branch-local sha that did not survive the merge. The same check re-done against a sha that does exist
   (`3006b645`) reaches the same answer; §1 checks 1–2 state it that way so the next reader can re-run it.

## §6 — what this lane changed

| File | Change |
|---|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 1 line, comment only: "tracked at 2.5 KB" → "tracked in the repo". Drops a literal that was already wrong and would rot again. No code, no assertion, no decorator. |
| `docs/handoffs/capx-director-ledger-2026-08.md` | Annotation on the D89 dispatch-status rows recording PR #5642 and this finding, so the lane is not re-emitted a third time. Factual only; no verdict, no charter, no queue reordered. |
| `docs/handoffs/FINDING-capx-d89r-verification-2026-09-08.md` | This document. |

**Why a new file rather than the charter's `FINDING-capx-d89-2026-09-08.md`:** that path exists and holds the first
lane's record. Overwriting it would destroy the artifact this lane audits. The `-d89r-` name marks the re-emission and
leaves the record intact.

Nothing was skipped, xfailed, weakened or deleted. `ruff check` → **All checks passed**; `ruff format --check` →
**3 files already formatted**.

## §7 — dispositions

- **Rule 28 `[R-MECH-MATRIX]`:** no cell moves. Nothing armed, no default changed, no verdict re-adjudicated.
- **Rule 27 `[R-PUSH]`:** the charter said both test files are "well over 300 lines". Measured: `test_d62…` **295**,
  `test_d74…` **234**, `tests/conftest.py` **195** — all under the threshold, so the protocol does not strictly bind.
  Followed anyway: the one edit was made in place with an anchored patch, exact on-disk bytes pushed, blob fetched back
  and compared on line count and hash.
- **Boundaries honoured:** none of `ccs.py`, `evolve.py`, `data/fleet/arrays.py` or the evolution-ledger writer was read
  or written (D88/D87/D83). No overlap reached.
- **Reported, not acted on:** the first lane's §5 routing stands unchanged — `reactive_offset_per_mw_yr` degrades to
  `None` where every sibling raises. Still not exploitable (an armed gate raises first), still the D62 desk's to change.
