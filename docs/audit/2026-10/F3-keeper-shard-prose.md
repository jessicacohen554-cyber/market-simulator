# F3 — keeper-shard prose vs the v3.13 ISO determination

Audit follow-up, 2026-10-03, branch `claude/audit-followups-2026-10`, HEAD
`d7ff7c20`. Zero LP. Scope: the nine `frontend/data/backcast/keepers/<ISO>.json`
shards, whose current-tense prose predates rubric v3.13
(`scripts/calibration_verdict.py::iso_determination`: the ISO determination is
worst-of over EVERY registered year; a NOT-YET year makes the ISO NOT-YET;
owner instruction 2026-09-30).

## What a shard holds

`scripts/audit_keepers.py` and `scripts/lib/keeper_store.py` read only
`iso`, `keeper`, `config_partition.configs[].{run_id,years,role}`,
`holdout_touchpoint.run_id`, `standing_note.probe_run_id` and
`superseded.former_keeper` structurally; every other key is free prose
(E11 treats the whole shard as a declaration corpus). Unknown top-level keys
are tolerated. `scripts/build_status.py` copies `frontier`, `standing_note`,
`frontier_touchpoint` and `config_partition.{declared,ruling,
iso_determination_ruling,coverage_invariant}` into `status/<ISO>.js`, where
`docs/codebase-site/js/calibration-status.js` renders `ruling`,
`coverage_invariant` and each config `label` in the Notes disclosure.
`config_partition.iso_determination` is overwritten from the live scorer at
build time and never read from the shard. `gates`, `note` and the new
`determination_at_head` key are not copied and not rendered.

## Computed determination at HEAD (parent session, 2026-10-03)

| ISO | keeper | v3.13 determination | failing gates |
|---|---|---|---|
| NEISO | 2026-10-02-w0-neiso | CALIBRATED | none (2019–2025) |
| NYISO | 2026-10-02-w0-nyiso | CALIBRATED | none (2021–2025) |
| MISO | 2026-10-02-w0-miso-fix2 | NOT-YET | fuelmix 2019; price_shape 2021 |
| SOCO | 2026-10-02-w0-soco-fix2 | NOT-YET | fuelmix 2019, 2021 |
| ERCOT | 2026-10-02-closeout-l1-coal-fuel | NOT-YET | fuelmix 2019–2020; price_shape 2019–2020; price_mean 2024 |
| CAISO | 2026-10-02-closeout-caiso-w1-arm2 | NOT-YET | dispatch_corr 2019–2021; fuelmix 2019–2021; price_mean 2021 |
| PJM | 2026-10-02-w0-pjm-fix2 | NOT-YET | fuelmix 2019–2021; price_mean 2022, 2025; price_shape 2022, 2025 |
| NWPP | 2026-10-02-w0-nwpp-fix2 | NOT-YET | dispatch_corr 2023; price_mean 2023–2024; price_shape 2023–2024 |
| SPP | 2026-10-02-w0-spp107r | NOT-YET | price_mean 2019–2020; price_shape 2020; fuelmix 2021–2022; dispatch_corr 2022; price_tail 2023–2025 |

Note: the parent's brief named the SPP keeper `2026-10-02-spp-107-mmu-repair`;
the shard, the registry and `audit_keepers.py` all carry
`2026-10-02-w0-spp107r` (the only SPP sidecar on disk), so that id is used here.

## Per-ISO findings and edits

Historical notes (`promotion_note_*`, `prior_*`, `superseded_*`,
`frontier_history`, `determination_amendment`, dated promotion prose) were
left untouched everywhere; they are records.

| ISO | key | was | now |
|---|---|---|---|
| SPP | `gates` (top-level, current-tense, but described the pruned spp-100 keeper) | "CALIBRATED (rubric at HEAD) on the designated 2023-2025 span; 2019-2022 NOT-YET, reported not gating (rule 30(c)). Keeper 2026-09-28-spp-100-chp-scope …" | "NOT-YET at v3.13 (worst-of over every registered year, scripts/calibration_verdict.py::iso_determination), recomputed 2026-10-03 at d7ff7c20: price_mean 2019-2020; price_shape 2020; fuelmix 2021-2022; dispatch_corr 2022; price_tail 2023-2025. Keeper 2026-10-02-w0-spp107r …" (form (a)) |
| SPP | `prior_gates_spp100` (new, end of file, the shard's own `prior_gates_<id>` convention) | — | the verbatim former `gates` text, preserved as the record |
| SPP | `config_partition.coverage_invariant` (rendered on the status page) | "… they gate nothing (rule 30(c))" | "… every one of them gates (rubric v3.13, rule 30(c) as amended 2026-09-30: a held-out year that misses downgrades the ISO)" |
| SPP | `config_partition.configs[0].label` (rendered) | "… this span alone determines SPP's ISO-level headline (rule 30(c))" | "… one of the scopes SPP's ISO-level headline folds over, worst-of (rubric v3.13)" |
| MISO | `determination_at_head` (new, form (b)) | — | "NOT-YET at v3.13 (…), recomputed 2026-10-03 at d7ff7c20: fuelmix 2019; price_shape 2021. …" The owner-ruling block `config_partition.iso_determination: "CALIBRATED"` / `iso_determination_ruling` (declared 2026-09-14) is left as the record it is; the new key says it is superseded by v3.13 and that `build_status.py` overwrites the published value. |
| MISO | `config_partition.coverage_invariant` (rendered) | "… they are excluded from the ISO-level fold by rule 30(c) and gate nothing" | "… since rubric v3.13 (rule 30(c) as amended 2026-09-30) they gate the ISO-level fold like every scope" |
| MISO | `config_partition.configs[0].label` (rendered) | "… this span alone determines MISO's ISO-level headline (rule 30(c))" | "… one of the scopes MISO's ISO-level headline folds over, worst-of (rubric v3.13)" |
| ERCOT | `determination_at_head` (new, form (b)) | — | "NOT-YET at v3.13 (…), recomputed 2026-10-03 at d7ff7c20: fuelmix 2019-2020; price_shape 2019-2020; price_mean 2024. …" The owner-signed `standing_note` (2026-08-26, X-2) and `config_partition.iso_determination_ruling` (ercot-246, 2026-08-31) stay as records; the key says their train-tier-only rationale is superseded. |
| ERCOT | `config_partition.coverage_invariant` (rendered) | "The ISO determination is the TRAIN-TIER verdict only (rule 30(c))." | "Since rubric v3.13 (rule 30(c) as amended 2026-09-30) the ISO determination is the worst over every designated scope, validation tier included." |
| ERCOT | `config_partition.configs[2].label` (rendered) | "Rule 30(c): never gates the ISO headline." | "Rubric v3.13 (rule 30(c) as amended 2026-09-30): gates the ISO headline like every scope." |
| NEISO | — | `neiso119_promotion_note` already reads "full span 2019-2025 NOT-YET -> CALIBRATED"; `note` carries no determination; `r_neiso_promotion_note` (2026-09-25, "full span NOT-YET") is dated history | no edit |
| NYISO | — | `determination_note` reads "ISO NOT-YET -> CALIBRATED" for the current span; the 30(c) sentence sits under its explicit "PRIOR:" marker | no edit |
| CAISO | — | `disposition_note` already states "DETERMINATION NOT-YET under rubric v3.13 (ISO determination covers every registered year)" with the same fail set | no edit |
| SOCO | — | `promotion_note_soco96` (dated 2026-09-30) reads NOT-YET; `note` carries no determination | no edit |
| PJM | — | `promotion_note` reads "training span 2023-2025 NOT-YET"; `frontier.note` names the 2026-07-30 keeper as CALIBRATED but is an owner-declared, dated designation (never gating) | no edit |
| NWPP | — | only `iso`, `keeper`, `note`; no determination claim | no edit |

JSON mechanics: `object_pairs_hook=OrderedDict`, each file's own indent
(SPP 1 space, ERCOT/MISO 2) and escaping (SPP `ensure_ascii=False`, ERCOT/MISO
`\u` escapes) preserved, trailing newline preserved; `git diff` touches only
the edited strings and the appended keys.

## Status parts

Because `coverage_invariant` and the config labels are copied into
`status/<ISO>.js`, the three parts were rebuilt
(`python3 scripts/build_status.py --iso SPP MISO ERCOT` → `[SPP:NOT-YET,
MISO:NOT-YET, ERCOT:NOT-YET]`); `status/shared.js` was byte-identical.

## Check results

- `python3 scripts/audit_keepers.py --check` (all nine, before the edit):
  PASS, 0 failures, 2 warnings (E11 on NYISO and SOCO: former keeper bundle
  retention-pruned, pre-existing).
- `python3 scripts/audit_keepers.py --check --iso SPP MISO ERCOT` (after the
  edit and the status rebuild): PASS, 0 failures, 0 warnings — E1–E15, M1, S1,
  H1 all green.
- `python3 scripts/check_registry_payload_parity.py`: "registry/payload parity
  OK (9 runs checked, 9 bundle dirs swept, 0 known-unsynced tolerated)",
  before and after.
- Render path: `determination_at_head`, `gates` and `prior_gates_spp100` are
  referenced by neither `scripts/build_status.py`,
  `docs/codebase-site/js/calibration-status.js` nor `js/bc-data.js`
  (grep count 0), so they cannot break a page; the edited
  `config_partition` strings are rendered through `esc()` as before.
