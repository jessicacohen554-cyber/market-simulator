# docs/sessions — frozen historical session notes

Archive of dated session/investigation notes whose findings are **resolved and
absorbed** into code, keepers, `CHANGELOG.md`, and `docs/calibration-log.md`.
Nothing here is a living reference: treat these as point-in-time records, and
do not update them except to add closing pointers at archival time.

- `multi-iso/` — 27 notes moved out of `docs/multi-iso/` in the 2026-07 docs
  reorg, per the file-by-file triage in
  `docs/handoffs/multi-iso-triage-2026-07.md`. The living multi-ISO
  protocol/reference set (and its index) remains in `docs/multi-iso/README.md`.

## Archived by `phase-refactor/stale-refs-docs` (2026-07-19)

Merged staging log-entries and executed one-shot session prompts moved out of
`docs/` root:

- **Merged staging files** — `_caiso79_bench_rework_log_entry.md`,
  `_caiso79_step0_log_entry.md`, `_caiso80_log_entry.md`, `_caiso81_log_entry.md`,
  `_caiso81e_log_entry.md`, `_pjm112_input_clock_log_entry.md`,
  `_pjm_phase_drift_log_entry.md`, `_rubric25_log_entry.md`, plus the two
  `_caiso79_*.patch.xz.b64` payloads. Their content is absorbed into the merged
  branches / `docs/calibration-log.md`.
- **Executed session prompts** — `dam-offer-curve-tuning-session-prompt.md`,
  `ercot-2025-overshoot-session-prompt.md`, `ercot-lmp-cooling-session-prompt.md`,
  `ercot-offer-curve-merit-order-session-prompt.md`,
  `spatial-ruc-session-prompt.md` (each carries a `RECORD` status banner).

In-text repo paths inside archived notes (e.g. `docs/multi-iso/...`) may
pre-date the move; the notes are intentionally not rewritten.
