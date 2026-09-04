# FINDING — Y-4: caiso-241's two undischarged duties + the ci.yml path-filter trap

**Date:** 2026-09-04 · **Lane:** `claude/y4-caiso241-duties-nvcroc` · **Pin:** `a8464861`
**Executes:** owner rulings **R-AB / R-AE** (2026-09-04); board
`docs/handoffs/audit-program-director-board-2026-08.md` v24, item Y-4 + the
path-filter addendum. The two duties are the caiso-241 promoting lane's
(R-T; R-X route), discharged here under the standing audit-lane exception
(#4488 / v23 job 0 precedent).
**PR:** #4688, merged to `main` as `69194725`.
**Scope discipline:** no solve · no score · no registration · no keeper shard,
marker or freeze file · no matrix edit · no test change · no edit to the
ERCOT/PJM/NEISO/MISO/NYISO stamp rows.

---

## 1. Job 1 — CAISO gate-(a) re-key: ALREADY DISCHARGED, no commit made

The board's context was taken at `b168260e`. **At this lane's pin it was already
repaired.** The CAISO `gate.a_keeper_marker` in
`frontend/data/forecast/program-status.json` cites
`2026-09-03-caiso-241-b1-ctpeaker` — re-keyed at `26c67788` by the capx director
desk (refresh #33) under the standing re-key duty of owner ruling Q34, card C-5,
from `2026-09-03-caiso-240-b1-stgas`. The verdict is `fail` before and after:
CAISO's determination is NOT-YET and it is absent from the `complete` block, so
gate (a) is closed on the marker either way.

Verified rather than assumed — **`python3 scripts/check_gate_a_provenance.py`
→ exit 0**, output `gate-(a) provenance OK (6 row(s) checked: keeper identity +
marker state match the backcast store; no determination read)`, captured
directly (`cmd > f 2>&1; echo $?`, not piped). CI's own `FR-21` job re-ran the
same script and its `check_gate_a_provenance` step concluded **success**.
`program-status.json` was therefore NOT touched by this lane — the correct
outcome for a stamp-only duty someone else had already performed, and the reason
`tests/scoring/test_gate_a_provenance.py::test_live_board_passes` was already
green at the pin.

## 2. Job 2 — `caiso_ct_peaker_committed_measured` filed as `GAP`

The surviving half of the board's context: the field is armed in the CAISO
keeper (`results/calibration/caiso241_b1_ctpeaker_committed/run_config.json`,
`scenario_config.caiso_ct_peaker_committed_measured = True`) with no
forecast-orchestrator consumer and no registry row, reddening
`tests/scoring/test_forecast_parity.py::test_all_six_keepers_resolve`.

**Disposition chosen: `GAP`, under the R-X route. Why, in one line: the code
already forecloses `BACKCAST_ONLY`.** The field is deliberately absent from
`scenarios._BACKCAST_ONLY_OVERLAY_FIELDS` and its docstring states the positive
claim — `avg_committed_p50` is a measured *physical* heat-rate ratio that
regenerates for a forward year from CAMPD conduct and responds to fleet change,
so it is rule-13 `[R-MEASURED]` admissible in **both** modes. Its caiso-240
sibling `caiso_st_gas_peak_measured` **is** registered there, on the stated
ground that it arms measured **bid** conduct keyed to one year's OASIS record;
the physical/bid split is the registry's own discriminator and this field sits on
the physical side. A `BACKCAST_ONLY` row would assert a non-regenerability the
code denies, on no evidence — and the checker does not verify that claim, so it
would have been this lane's word alone. `PARAMETER_OF` is unavailable too: the
block requires no other CAISO offer-surface flag armed, is band-disjoint from all
of them (`committed` only), and is applied last so it wins over them. `GAP` is
what remains, and the closest sibling `caiso_offer_surface_measured` is already a
filed GAP on the identical reason.

Fork measured at the pin: the only consumers are `pipeline/backcast_config.py`
(role `backcast` in `SOURCE_ROLES`) and the two calibration CLIs; `runner.py`
never names the field and nothing else under `src/market_sim/` does either.
Finding: `docs/FINDING-caiso-ct-peaker-committed-measured-parity-2026-09.md`.

`_FR22_OPEN_UNACCOUNTED` was **not** extended; no other row was touched.

## 3. Job 3 — path-filter trap: ci.yml filter WIDENED, passthrough workflow REJECTED

**The passthrough workflow was not added, and the reason is GitHub's own
documentation.** *Handling skipped but required checks* gives two rules: a
workflow **skipped by path filtering** leaves its checks `Pending` and blocks the
PR; a **job** skipped by a *conditional* reports `Success`. The documented
workaround is narrower than the proposal — the second workflow must carry *the
same `name:` key and the same required job names*, with the inverse path filter.
A passthrough job named `Required checks (path-filtered CI did not run)` shares
its name with none of the six required `ci.yml` jobs, so it would add a
**seventh** always-green check while the six still never report: docs-only PRs
stay blocked. It cannot achieve the goal, so per the lane's own instruction it
was not built.

Building the name-matching version instead is a different proposition and was not
taken either: it needs an inverse filter maintained in lockstep with `ci.yml`'s
list, and it makes six jobs report green having tested nothing — a false green by
construction. That is an owner decision, not a lane's.

**Taken instead:** three paths added to `ci.yml`'s `pull_request.paths` —
`docs/handoffs/audit-program-director-board-2026-08.md`,
`docs/model-audit-release-plan-2026-08.md`, `docs/FINDING-*.md`. Deliberately
**not** `docs/**`: running the suite on every docs PR is the runner-minute cost
the repo CI policy exists to avoid. Cost ≈ 10 min per records or finding PR. The
required set is untouched and no job is weakened. The accurate alternative, for
the owner: the only way to keep the filter narrow *and* unblock those PRs is to
drop the `paths:` filter and give each job a conditional so it runs-and-skips —
which is the "jobs themselves report Success" limb of the same GitHub rule, and a
larger change than this lane's mandate.

## 4. CI evidence — run **2382**, id **33852931713**, head `d94a6423`

Both jobs relevant to the two duties are green; the two reds are main content.

| job | conclusion |
|---|---|
| **Fast test tier** | **success** — `7869 passed, 34 skipped, 2 xfailed, 23 warnings in 577.98s (0:09:37)`, zero failures |
| **Ruff lint + format** | **success** |
| **FR-21 forecast-board staleness (WARN only)** | **success** (its `check_gate_a_provenance` step: success) |
| Pinned default cache key | success |
| Structural refactor guards | success |
| Cache-key registration guard | success |
| Rule-28 mechanism-matrix guard | success |
| Rule-22 quarantine gates | **failure — not this lane's.** `audit_keepers --check` fails on ONE shard, NYISO `2026-09-04-nyiso-185-family-hr`: `E11: UNDECLARED keeper-recipe change(s) … fossil_announced_exits_enabled (False -> True)`. CAISO reads `all checks passed`. Landed by the nyiso-185 promotion; this lane may not touch keeper shards. |
| FR-22 backcast->forecast parity | **failure, but the row landed.** `SUMMARY: 6 keeper posture(s); 2 unaccounted, 13 filed gap(s), **0 registry failure(s)**, 0 error(s)`. CAISO is off the failure list; the two unaccounted are exactly the pinned pair (`ercot_storage_as_soc_reserve`, `nyiso_seam_deliverability_envelope`). Gaps 12 → 13 is this lane's row. Not in the owner's flip set. |
| Forecast-invariant artifact audit | failure — pre-existing main red, not in the flip set |

Local, before the push: `check_gate_a_provenance.py` exit 0;
`check_forecast_parity.py` reports the CAISO row as `GAP` with the finding cited
and CAISO `UNACCOUNTED 0`; `uv run pytest tests/scoring/test_forecast_parity.py
tests/scoring/test_gate_a_provenance.py -q` → **34 passed, 1 xfailed**;
`ruff check` + `ruff format --check` clean on the edited registry.

**Rule 27 `[R-PUSH]`:** both edited files are ≥300 lines (`ci.yml` 590,
`forecast_parity_registry.py` 579). Blob-verified against the pushed ref —
`edf3f2fde2dc8a1c74147c01f89b913025e54aaa` and
`556354536dc9bcaf5f5e4232ede07f9e58ea629d`, both matching local `git hash-object`
byte-for-byte. `program-status.json` was not written, so it needed no verify.

## 5. Two process notes, recorded against interest

1. **PR #4688 was auto-merged to `main` before its CI run finished.** The
   push-to-PR-to-merge automation did not wait; run 2382 was still in progress at
   merge. The lane's evidence is therefore *post-merge* evidence. Nothing in it
   changed the verdicts above, but a required-check flip would have prevented
   this merge — which is an argument for the flip, not against it.
2. **The branch was deleted on merge and re-created by a second push**, which is
   why the first `create_pull_request` call failed `PullRequest.head (invalid)`
   and the second failed `No commits between main and …`: #4688 already existed
   and had merged. No work was lost or duplicated.

## 6. Flip instruction for the owner

On merge, the required set is the six `ci.yml` jobs — this lane added no job:

> Fast test tier · Ruff lint + format · Pinned default cache key · Structural
> refactor guards · Cache-key registration guard · Rule-22 quarantine gates

**Leg 2 is CLAIMED on this run**: run 2382's `Fast test tier` job concluded
**success** (`7869 passed, 34 skipped, 2 xfailed`, zero failures) — the criterion
is a completed `ci.yml` run whose fast-tier job succeeds, and this is one. Both
tests named in the board's Y-4 context are green on this run.

**TWO of the six are red on `main` content as of `8a18e9e1`, and BOTH belong to
NYISO lanes, not this one.** Flipping the required set before they clear would
block every PR.

1. **`Rule-22 quarantine gates`** — the NYISO `E11` of §4
   (`fossil_announced_exits_enabled` undeclared on `2026-09-04-nyiso-185-family-hr`).
   The nyiso-185 promotion lane's; this lane may not touch keeper shards.
2. **`Fast test tier`** — **NEW, and it appeared AFTER the run-2382 evidence
   above.** `tests/unit/data/test_egrid_identity_heat_rates.py::TestCommittedArtifact::test_single_row_and_loyo_envelope`
   fails `AssertionError: 2 != 1`. Cause, traced to the commit: `2ba0a29b`
   (nyiso-186, merged to `main` as PR #4693 → `8a18e9e1`) re-derived
   `egrid_identity_heat_rates_NYISO.csv` to add the merged-identity row
   (57664 ↔ eGRID 55375, the Astoria Energy split) and did **not** update the
   test asserting `len(df) == 1`. Artifact/test drift, reproduced locally on the
   merged tree. This lane's diff touches neither the artifact nor the test, and
   a test change is forbidden to it — the fix is the nyiso-186 lane's.

**What this does and does not do to §4's leg-2 claim.** Run 2382's `Fast test
tier` concluded **success**, and that remains a true statement about that run at
that pin — leg 2's criterion was met and is not withdrawn. What has changed is
flip *readiness*, which is a statement about `main` now: the fast tier is red on
`main` content as of `8a18e9e1`, so the leg-2 evidence is a snapshot, not a
standing guarantee. Reporting it otherwise would misrepresent the gate.

The two duties this lane owed are discharged; both remaining blockers are other
lanes'.
