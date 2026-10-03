# G3 — one fixed schema for `calibration_attestation.json`

Owner ruling 2026-10-03; closes finding 4 of `C-data-calibration-governance.md`
(lane-named blocks indistinguishable from drift; `authorized_price_tuning` at
top level in NYISO only; the rule-21 ledger shape read by E8 alone).
Branch `claude/audit-rulings-2026-10`, zero LP.

## 1. Inventory (branch base, before migration)

Every bundle: `schema = "calibration-attestation/v1"`, `governance` = 4 bool
assertions + `attested_by` (+ lane extras), `free_parameters` = dict
`dof-ledger/v1` {schema, seeded, n_entries, n_residual, entries[]} — NOT a
list; every entry carries `name`/`where`/`identification`/`lineage_solves`/
`source`, and `value` XOR `n_scalars` XOR neither (curated tables), `root_cause`
on residual rows, optional `note`. `exceptions` is a list everywhere.

| bundle | disclosures | top-level `authorized_price_tuning` | gov.authorized_price_tuning | lane-named keys |
|---|---|---|---|---|
| closeout_caiso_w1_a2_span | {} | absent | null | — |
| closeout_ercot_l1_span | absent | absent | null | — |
| w0_miso_span | {note} | absent | declared (6 fields) | hydro5, miso267/268/271/272/273/275/277/278/279/280, rmiso, rmiso_arm_b |
| w0_neiso_span | {note, neiso109} | absent | declared | neiso109/110/112/114/117/118/119, hydro5, r_neiso (+ `exceptions_dropped`) |
| w0_nwpp_span | 6 keys | absent | null | `lane`, `bundle`, `switches` (provenance) |
| w0_nyiso_span | absent | **null** | null | `exceptions_note` |
| w0_pjm_span | absent | absent | null | `delta_vs_incumbent` |
| w0_soco_span | 12 keys | absent | null | — |
| w0_sppr_span | 7 keys | absent | declared | r_spp, spp85/86/94/98/99/100, spp107EXR, w0_spp107r |

Existing checks: E8 (ledger present, residual rows have root causes), E10
(governance bools, `exceptions` list, WARN on missing `schema`).
`promote_keeper.attest` writes governance + `exceptions: []` + `disclosures: {}`
then runs `build_dof_ledger.py`, which REPLACES `free_parameters` wholesale
(hand notes carried). Nothing emitted a top-level `authorized_price_tuning`.

## 2. The schema

`data/dictionary/schema/calibration_attestation.document.yaml` — deliberately
`*.document.yaml`, not `*.schema.yaml`: `clean_io.load_schema` and
`tests/curation/test_data_dictionary_sync.py::test_every_schema_has_a_section`
enumerate `*.schema.yaml` as Parquet column contracts (`columns:` required), so
the task's literal filename would have broken the dictionary sync test.

Required top-level keys: `schema` (== `calibration-attestation/v1`),
`governance` (4 bools + non-empty `attested_by`; `authorized_price_tuning`
null or object), `free_parameters` (dict with `schema`, `entries[]`; each
entry `name`/`where`/`identification`/`source`; residual ⇒ `root_cause`),
`exceptions` (list of objects with `criterion`; `year` optional — NEISO's
span-wide governance entry has none), `authorized_price_tuning`
(`{"declared": bool}`, must agree with whether `governance.authorized_price_tuning`
is a well-formed 6-field declaration), `disclosures` (dict or list),
`lane_blocks` (names of every non-schema top-level key; unlisted extra = FAIL,
listed-but-absent = FAIL). Optional known keys: `lane`, `bundle`, `switches`,
`exceptions_note`, `exceptions_dropped`, `delta_vs_incumbent`, any `rubric*`
stamp (v3.19 rubric tolerance).

Code: `scripts/lib/attestation_schema.py` — `load_schema()`, `validate(att)`,
`migrate_dict(att)` / `migrate(path)` (additive, idempotent, preserves key
order, indent 2, the file's own `\uXXXX` escaping and trailing newline), CLI
`--migrate` / `--check`. Tests: `tests/scoring/test_attestation_schema.py` (5).

## 3. Wiring

* `scripts/audit_keepers.py` **E16** (FAIL): validates the same `att` E8/E10
  load; message names the migrate command.
* `scripts/promote_keeper.py::attest` step 3: after `build_dof_ledger.py`,
  `attestation_schema.migrate(path)` then `validate` → `SystemExit` on a
  violation (so the step-8 audit never meets an E16 FAIL of its own making).
* `scripts/build_dof_ledger.py::_entry`: `source` now always emitted (was
  `if source:`), so a regenerated ledger cannot drop a schema-required key.
  `--check` confirmed `free_parameters current` on PJM/SPP/MISO/ERCOT.

## 4. Per-bundle migration (all additive; `git diff` = insertions + trailing commas)

| bundle | changes |
|---|---|
| closeout_caiso_w1_a2_span | + `authorized_price_tuning: {declared: false}`, + `lane_blocks: []` |
| closeout_ercot_l1_span | + `disclosures: {}`, + apt declared false, + `lane_blocks: []` |
| w0_miso_span | + apt **declared true**, + `lane_blocks` (13 names) |
| w0_neiso_span | + apt **declared true**, + `lane_blocks` (9 names) |
| w0_nyiso_span | `authorized_price_tuning: null` → `{declared: false}`, + `disclosures: {}`, + `lane_blocks: []` |
| w0_pjm_span | + `disclosures: {}`, + apt declared false, + `lane_blocks: []` |
| w0_soco_span | + apt declared false, + `lane_blocks: []` |
| w0_sppr_span | + apt **declared true**, + `lane_blocks` (9 names) |
| w0_nwpp_span | **skipped** — deleted on `origin/main` (replaced by `nwppnext22b_span`) |

No `free_parameters` entry or exception was edited; no required key was
missing from any entry, so no null placeholders were written.

## 5. Check outputs

* `audit_keepers.py --check` (all ISOs): FAIL 1 — only
  `NWPP 2026-10-02-w0-nwpp-fix2 E16` (bundle skipped per the coordinator);
  `--iso ERCOT CAISO PJM MISO NYISO NEISO SPP SOCO`: **PASS**, 2 pre-existing
  WARNs (SOCO E11 former bundle pruned; one E14).
* `check_registry_payload_parity.py`: OK (9 runs, 9 bundle dirs).
* `ruff check` / `ruff format --check`: clean on every touched file.
* `.venv/bin/python -m pytest tests/scoring/test_attestation_schema.py
  test_audit_keepers_attestation_shape.py test_promote_keeper.py
  test_build_dof_ledger_coal_sigmoids.py`: 37 passed.

## 6. Remaining gaps / for the parent

1. After merging `origin/main`, re-run
   `python3 scripts/lib/attestation_schema.py --migrate results/calibration/*/calibration_attestation.json`
   (idempotent) so `nwppnext22b_span` and the re-touched CAISO/PJM attestations
   conform; then `audit_keepers.py --check` must read 0 failures.
2. `authorized_price_tuning.declared` is derived from
   `governance.authorized_price_tuning` well-formedness; the three declaring
   lanes (MISO, NEISO, SPP) keep their prose block in `governance` — the
   top-level key is the explicit flag, not a copy.
3. `docs/codebase/` and the RUNBOOK do not yet mention E16 / the migrate
   command (sync-docs at wrap-up).
4. The exceptions-ledger entry shape beyond `criterion` still varies by lane
   (`kind`/`reason`/`rationale`/`classification`…); normalising it is a
   separate ruling.

## Re-run on merged main (2026-10-03, parent session)

Migration re-run idempotently on the nine bundles on `main` @ `7cbdde87`
(`closeout_soco_2_span` and `nwppnext22b_span` replaced the W0 SOCO/NWPP
bundles; `w0_nwpp_span` is gone). All nine validate; `audit_keepers --check`
PASS; registry parity OK; 141 related tests pass under `.venv`.

**Finding surfaced by the schema.** `authorized_price_tuning.declared` is
`true` only for MISO, NEISO and SPP. CAISO, ERCOT, SOCO, NWPP, NYISO and PJM
carry no well-formed `governance.authorized_price_tuning` block although every
keeper's `free_parameters.entries` marks `offer_curve_by_group` as
`identification: residual`. Rule 1(e) requires the band channel to be declared
in the attestation. Owner item: each of those six lanes owes a declaration
(or a ruling that the bands predate the 2026-09-05 channel and are grandfathered
with that stated).
