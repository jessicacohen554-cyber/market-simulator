# FF-2B — apply-spec (SUPERSEDED 2026-07-19)

**This file is obsolete.** It was a fallback written while the large source
files (constants.py 345 KB / capacity.py 204 KB) could not be transported —
`push_files` requires full inline content and corrupted on reproduction, and the
direct git-data API was proxy-blocked. That blocker is **resolved**: a clean
**source-only `git push`** (exact on-disk bytes, no inline regeneration, small
pack — no result parquets) landed the real edits and they were blob-verified
byte-identical local↔remote (rule 27).

The actual source change is in the diff — see:
- commit **96eac04** ("FF-2B: adequacy-basis closure …") on branch
  `claude/neiso-adequacy-basis-ff2b-subcny`:
  - `src/market_sim/model/capacity.py` — `_firm_import_mw(iso)` resolver + call site.
  - `src/market_sim/config/constants.py` — NEISO Net ICR PRM (FCA 17), NEISO DR
    fraction, CAISO/NEISO firm-import credits (all cited, none tuned).
  - `tests/test_capacity.py` — `TestFF2BAdequacyBasis` (4 tests).
- Full findings: `docs/handoffs/ff-2b-adequacy-basis-2026-07.md`.

Note: the runner.py `UNSET`-import fix listed in the old spec is **already on
main** (commit `de29a45`), so FF-2B touches no runner.py.
