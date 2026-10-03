# G1 — rule 37 `[R-RUBRIC-FREEZE]`: the rubric is frozen between promotions

Audit follow-up, 2026-10-03, branch `claude/audit-rulings-2026-10`. Zero LP.
Owner ruling (this session): *"Freeze the rubric between promotions: a rubric
amendment is a promotion decision, proposed in a PRECOMMIT and ruled on by the
owner, never landed in the same PR as a keeper."* Prompted by
`docs/audit/2026-10/C-data-calibration-governance.md` §5 finding 3
(self-certification: rubric v3.10 → v3.17 in five days, each admitting a named
failing cell to the caveat ledger) and risk (ii); v3.18 and v3.19 (rule-history
§28, §29, both 2026-10-03) are the latest instances of the pattern.

## Files

| file | change |
|---|---|
| `docs/governance/rule-history.md` | §30 (new rule 37, owner ruling verbatim, the v3.10–v3.19 table, scope, requirements, neighbouring rules, enforcement, **CLAUDE.md text**); "Changes to this file" renumbered §30 → §31 with a dated row. Based on `origin/main` `22fb72b1` (which added §28/§29) plus the appended block — on merge, take this branch's version. |
| `docs/calibration-determination-rubric.md` | "Amendment procedure (rule 37)" paragraph at the head of §9 Version history. Based on `22fb72b1` plus the inserted paragraph. |
| `scripts/check_rubric_freeze.py` | NEW CI guard (stdlib-only; `--base <sha>` diff mode, HEAD-only mode prints `diff gate NOT RUN`, `RUBRIC_FREEZE_OVERRIDE` owner override). `ruff check` / `ruff format --check` clean. |
| `.github/workflows/ci.yml` | one step `check_rubric_freeze` after `check_cache_key_registration`, same `--base ${{ github.event.pull_request.base.sha }}` convention. No new workflow. |
| `CLAUDE.md` | NOT edited here — the parent session lands the line below. |

## The CLAUDE.md line (rule 37)

```
37. `[R-RUBRIC-FREEZE]` **The determination rubric is frozen between promotions: a rubric amendment is a promotion decision, proposed in a PRECOMMIT and ruled on by the owner, never landed in the same PR as a keeper.** The rubric (`docs/calibration-determination-rubric.md`, `RUBRIC_VERSION`, every threshold, caveat budget and ledger-admissibility set in `scripts/calibration_verdict.py`) changes only in a PR that changes no keeper designation, keeper shard, status part or `calibration-complete.json`; the PRECOMMIT computes the amendment's effect on every registered ISO zero-LP (`calibration_verdict.py` over the committed bundles) before and after, and the amendment lands only on the owner's ruling, cited in the commit. Enforced by `scripts/check_rubric_freeze.py` in CI (`RUBRIC_FREEZE_OVERRIDE` carries the owner's promotion-with-amendment ruling).
```

## What the guard computes

Over `git diff --name-only <base>...HEAD` (two-dot fallback for a shallow
clone):

* **A, rubric surface** — `docs/calibration-determination-rubric.md`;
  `scripts/calibration_verdict.py` when an added/removed line names
  `RUBRIC_VERSION`, `MAX_LEDGERED_CAVEATS`, `MAX_PROTECTIVE_CAVEATS`,
  `LEDGERABLE_CRITERIA`, `SCOPED_LEDGER_ENTRIES`, `CONFIG_EXCEPTION_ENTRIES`,
  `REFERENCE_COVERAGE_ENTRIES`, `C3C_READING_LABELS`, `C3C_NOT_SCORED`,
  `LAMBDA_REFERENCED_ISOS`, `REFERENCE_DEFINITION_CRITERIA`, the `FUELMIX_*` /
  `SYSVOL_*` / `PRICE_*` / `TAIL_*` / `DISP_*` / `CO2_*` bands,
  `PRICE_MONTH_COVERAGE_MIN`, `PROTECTIVE_MIN_LOAD_FRAC`, `FORCED_SHARE_*_MAX`
  or `CRITERIA` (the constant name `RUBRIC_VERSION` confirmed at
  `origin/main` `22fb72b1`, `scripts/calibration_verdict.py:708`, value
  `"3.19"`); any other `scripts/` or `src/` `.py` file whose diff defines or
  mutates one of those names (a read is not an edit; `scripts/probes/` and
  `scripts/archive/` exempt).
* **B, keeper surface** — `frontend/data/backcast/keepers/*.json`,
  `frontend/data/backcast/status/*.js`,
  `frontend/data/backcast/calibration-complete.json`, `results/calibration/**`.

A and B both non-empty → exit 1 naming both lists and rule 37; otherwise 0.
`RUBRIC_FREEZE_OVERRIDE=<owner ruling citation>` (set on the CI step by the
owner's promotion-with-amendment PR only; never a workflow default) prints the
collision and the citation and exits 0.

Known limit, stated: `status/shared.js` carries the rubric reference and every
`status/<ISO>.js` carries `rubric_version`, so an amendment PR must NOT rebuild
the status parts; the promotion PR that follows re-keys them under rule 35.

## Hand-test output

```
$ python3 scripts/check_rubric_freeze.py
rubric-freeze: diff gate NOT RUN — pass --base <sha> to check that the rubric surface and the keeper surface do not change together (CLAUDE.md rule 37 [R-RUBRIC-FREEZE])
exit=0

$ python3 scripts/check_rubric_freeze.py --base b32201af        # keeper re-keys only
ok: 33 changed file(s) vs b32201af; keeper surface changed, never both (CLAUDE.md rule 37 [R-RUBRIC-FREEZE])
exit=0

$ python3 scripts/check_rubric_freeze.py --base 94c1be04        # v3.13 → HEAD: v3.14–v3.17 beside the re-keys
rubric-freeze guard FAILED (CLAUDE.md rule 37 [R-RUBRIC-FREEZE])

  A — rubric surface changed (2 file(s)):
    docs/calibration-determination-rubric.md: (the rubric document)
    scripts/calibration_verdict.py: C3C_NOT_SCORED, CONFIG_EXCEPTION_ENTRIES, CRITERIA, LAMBDA_REFERENCED_ISOS, LEDGERABLE_CRITERIA, MAX_LEDGERED_CAVEATS, REFERENCE_DEFINITION_CRITERIA, RUBRIC_VERSION
  B — keeper surface changed (1922 file(s)):
    frontend/data/backcast/calibration-complete.json
    frontend/data/backcast/keepers/CAISO.json
    … (keepers/*.json, status/*.js, results/calibration/**)
    … and 1902 more

  The rubric is frozen between promotions. A rubric amendment is a
  promotion decision: propose it in a PRECOMMIT with its zero-LP effect
  on every registered ISO (calibration_verdict.py over the committed
  bundles, before and after), land it on the owner's ruling cited in
  the commit, in a PR that changes no keeper designation, keeper shard,
  status part or calibration-complete.json. Split this PR: rubric
  amendment first, promotion second. Only the owner's
  promotion-with-amendment ruling, passed as RUBRIC_FREEZE_OVERRIDE by the CI
  step, carries both in one PR.
exit=1

$ RUBRIC_FREEZE_OVERRIDE="hand test only: owner ruling 2026-10-03, not a real override" \
    python3 scripts/check_rubric_freeze.py --base 94c1be04 | tail -3
  RUBRIC_FREEZE_OVERRIDE set by the CI step — owner's promotion-with-amendment ruling: hand test only: owner ruling 2026-10-03, not a real override
  The commit message must cite the same ruling; the reviewer checks.
exit=0
```

Before the probes exemption and the definition-only match, the same `94c1be04`
run also listed `scripts/gen_nwpp40_attestation.py`, `gen_nwpp41_attestation.py`,
four `scripts/probes/*` files and `scripts/promote_keeper.py` in A on reads of
`TAIL_THRESHOLD` / `LEDGERABLE_CRITERIA`; those are reads, not amendments, and
no longer count.

`ruff check scripts/check_rubric_freeze.py`: All checks passed.
`ruff format --check`: 1 file already formatted.
