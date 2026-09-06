# FINDING — G-3: rule 21 `[R-DOF]` cross-reference to the authorized price-tuning channel (R-AY)

**Lane:** G-3 (rule-amendment series; not the board's older G-3 item), Model Audit &
Release-Finalization Program. **Date:** 2026-09-06 (dispatched 00:20Z).
**Ruling executed:** **R-AY** — audit-program director sitting 2026-09-06 ~00:15Z, card
"DOF / C6", the recommended option taken verbatim: *"Count them in the DOF ledger, C6 passes
under the declaration."*
**Base pin:** `144eabe3` (origin/main at lane start). Main moved to `976a3e6d` during the lane
(#4905–#4909, including `32f8de52`, the NYISO gate-(a) re-key); the branch was re-pinned onto
`976a3e6d` before commit so the pack carries only this lane's objects. Main touched none of the
three files this lane edits between the two pins (`git diff --stat 144eabe3 976a3e6d` on them is
empty).
**Branch / PR:** `claude/g3-rule-21-price-tuning-xref-mfav8w`, PR #4912. *(Dispatch-vs-repo difference,
recorded per the standing test: the dispatch named `claude/g3-rdof-price-tuning-xref-h8n4pc`; the
session's harness assigned `…-rule-21-price-tuning-xref-mfav8w` and forbids pushing elsewhere, so
that is the branch.)*
**Model:** Fable (rule 27 `[R-PUSH]` scope: `CLAUDE.md`, `rule-history.md`,
`calibration_verdict.py` — all ≥300 lines, Edit tool only, blob-verified after push, §6).

## 0. Result in one paragraph

Rule 21 `[R-DOF]` gained the one clause R-AY asked for; `docs/governance/rule-history.md` gained
§13 (rule 21's first section; §12 on merge went to main's same-day rule 30 entry) cross-linked both ways with §11; `score_governance`'s docstring
carries the R-AY citation beside the rule 1 citation with **no scoring logic changed**. The live
case verifies as the ruling assumes on two of three readings and shows one gap on the third: the
MISO keeper's attestation carries a well-formed `authorized_price_tuning` block, sets
`no_fit_to_price_residuals` to `false` deliberately and nonetheless scores C6 PASS /
CALIBRATED on committed artifacts — but the ×1.10 lift is **not** a distinct DOF-ledger row with
a ruling-identified source; it rides the pre-existing `offer_curve_by_group` row (identification
`residual`) plus a `dof_entry` pointer string inside the governance block. The attestation was
not edited (it is the calibration desk's artifact); the gap is routed in §4. Nothing this lane
was forbidden to touch was touched: no keeper shard, marker, attestation, registry sidecar,
matrix shard, board or plan.

## 1. What changed (three files, all docs/docstring; zero solve-path or scoring-path change)

1. **`CLAUDE.md` rule 21 `[R-DOF]`** — one clause appended after the 2026-07-14 amendment,
   cited to R-AY. It states three things and no more: (i) an `offer_curve_by_group` band
   multiplier tuned on price through the rules 1/13 authorized channel IS a ledgered free
   parameter whose identification source is the ruling itself — *"price residual, authorized
   channel (rules 1/13 amendment 2026-09-05)"* — not a measured input; (ii) it is reported at
   full magnitude on the determination basis; (iii) its presence does NOT by itself make the
   residual it closes an "open root-cause issue" under rule 21, while every OTHER tuned value
   still does and no gate moves. Conditions (a)–(e) are not restated; they live in rule 1.
2. **`docs/governance/rule-history.md`** — new **§13** (rule 21 had no section; this is its
   first — it took §13 on merge behind main's same-day §12, rule 30 `[R-TOUCHPOINT-FOLD]`), with the ruling verbatim, what the clause does and does not say, the enforcement
   status, and the live-case reading. §11 (rules 1/13) gained a forward pointer to §13; §13
   points back to §11 throughout. "Changes to this file" renumbered to §14 (no external
   reference cited §12 or §13 — checked by grep over `*.md,py,js,json,yaml,yml`). Changelog row added.
3. **`scripts/calibration_verdict.py::score_governance`** — a docstring paragraph adding the
   R-AY citation beside the existing rule 1 `[R-STRUCT]` carve-out citation. The function body
   is byte-identical. `calibration_verdict.py` is not in `bench_stamp.BUILDER_SOURCES`
   (`render_calibration_html`, `render_backcast`, `backcast_artifacts`, `bench_stamp`), so the
   docstring edit cannot move the bench builder fingerprint (§10's docstring limit does not
   apply here).

## 2. The live case — three readings, verbatim, adjudicating nothing

Artifact: `results/calibration/miso220_nonsteamlift_B/calibration_attestation.json` (the
dispatch wrote `miso220_nonsteam_lift*`; the on-disk name has no underscore between "nonsteam"
and "lift" — dispatch-vs-repo difference recorded). Registry sidecar
`frontend/data/backcast/registry/2026-09-05-miso-220-nonsteam-lift.json` → `bundle:
results/calibration/miso220_nonsteamlift_B`, years `[2023, 2024, 2025]`. Keeper shard
`frontend/data/backcast/keepers/MISO.json` → `keeper: 2026-09-05-miso-220-nonsteam-lift`.
Promotion commit `743b3dc0` *"miso-220: PROMOTE — keeper -> 2026-09-05-miso-220-nonsteam-lift,
determination CALIBRATED"* — its body states the dependency plainly: *"Keeper only because of
the same-day owner ruling: C6 passes on the authorized_price_tuning declaration, and without the
rule amendment governance fails and this reads NOT-YET."*

**(i) `authorized_price_tuning` block — PRESENT and well-formed** (every field
`AUTHORIZED_TUNING_FIELDS` requires; channel is the one authorized channel; `set_ex_ante` and
`not_swept` both `true`; `years_held` covers every scored year):

```json
"authorized_price_tuning": {
  "channel": "offer_curve_by_group",
  "ruling": "owner ruling 2026-09-05: 'the offer curve multipliers are meant to allow us to tune on price & adjust merit order… as long as it's the same config across the 3 years'; steam gas scoped to ST_GAS + ST_GAS_INTERMEDIATE by the owner's follow-up answer the same day",
  "value": "x1.10 on committed/econ_low/econ_high/peak for 11 non-steam fossil classes; ST_GAS and ST_GAS_INTERMEDIATE held byte-identical; phys_* and econ_low_share/pct_peaking untouched in every class",
  "years_held": [2023, 2024, 2025],
  "set_ex_ante": true,
  "not_swept": true,
  "prereg": "results/calibration/PREREG-miso220-nonsteam-offer-lift-2026-09-05.md @ e1a2eb01",
  "merit_order_effect": "intended and measured: _miso220_liveness.json S-3 records 121 non-steam tranches crossing above the steam-gas median at the mid-year probe hour",
  "dof_entry": "offer_curve_by_group non-steam fossil lift (1.10), identified by owner ruling"
}
```

The `value` string was checked against the bundles, not taken on trust: every band
(`committed`/`econ_low`/`econ_high`/`peak`) of every one of the 11 non-steam classes in
`miso220_nonsteamlift_B/run_config.json` is exactly 1.1× the same band in the miso-217 control
bundle `miso217_intermphys_B/run_config.json`; `ST_GAS` and `ST_GAS_INTERMEDIATE` are 1.0×; no
other key of any class differs. `e1a2eb01` resolves to a commit.

**(ii) The ×1.10 lift in the DOF ledger — NOT a distinct free-parameter row with a
ruling-identified source.** `free_parameters` reads `n_entries: 41`, `n_residual: 2`, and the
attestation's own `attested_by` text says *"No ScenarioConfig field minted, no matrix row,
ledger 41/2 unchanged."* The two residual-identified rows are `offer_curve_by_group` and
`offer_curve_smoothing`, unchanged from the predecessor. The `offer_curve_by_group` row, verbatim
minus its per-class key listing:

```json
{
  "name": "offer_curve_by_group",
  "where": "run_config.scenario_config.offer_curve_by_group",
  "identification": "residual",
  "lineage_solves": ">=39 solves (audit §5.1 + miso-39)",
  "n_scalars": 92,
  "source": "per-group HR-band multipliers — the rule-#1-sanctioned offer-curve tuning surface (audit C-8/C-11/C-13)",
  "root_cause": "identified in-sample only (2023-2025); no held-out validation exists — open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 statistical-mode gap reported on the Calibration Status page"
}
```

No ledger entry names the lift, the value 1.10, the ruling, or the source string
*"price residual, authorized channel (rules 1/13 amendment 2026-09-05)"*. The only place the
lift is identified by the ruling is the governance block's `dof_entry` string above — a pointer
to a ledger row that does not exist as such. Reading: the multipliers ARE the
`offer_curve_by_group` row, so the lift is "in the ledger" in the loose sense that the row
covers the same 92 scalars; but R-AY's specific requirement — a ledgered free parameter
*identified by the ruling rather than by a measured source* — is not met on the ledger's face.
The miso-220 finding (`results/calibration/FINDING-miso220-nonsteam-offer-lift-2026-09-05.md`
line 146) asserts *"(e) declared in the attestation and carried as a DOF free parameter"*; the
declaration half is true, the carried-as-a-row half is the gap. **Not edited** — routed, §4(a).

**(iii) `governance.no_fit_to_price_residuals` reads `false`, and C6 scores PASS.** The
governance block's four assertions, verbatim:

```json
"levers_trace_to_measured_input": false,
"no_fit_to_price_residuals": false,
"no_pinning_to_actuals": true,
"outage_filter_exogenous_net_load": true,
```

set so deliberately by `ed07a641` *"miso-220: the arm's attestation cannot carry the keeper's
no_fit_to_price_residuals claim"*. The committed verdict, re-derived from committed artifacts
only (`scripts/calibration_verdict.py --run-id 2026-09-05-miso-220-nonsteam-lift`, no solve):

```
CALIBRATION DETERMINATION: CALIBRATED
[✓] PASS    PROT  C6 governance gate
determination basis:
  - 1 ledgered caveat(s) (measured-input or model-class) — REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity (RT hourly)
```

and the C6 row's `magnitude` (the `--json` output) ends with the scoped-assertion note the
scorer appends when the declaration validates: *"…; authorized price tuning declared on
offer_curve_by_group = x1.10 on committed/econ_low/econ_high/peak for 11 non-steam fossil
classes; ST_GAS and ST_GAS_INTERMEDIATE held byte-identical; phys_* and
econ_low_share/pct_peaking untouched in every class"*, with `machine_issues: []`. So the lift is
reported at full magnitude on the C6 row, as R-AY requires, even though it is not on the ledger
as its own row.

## 3. The scorer already implements condition (e)'s declaration half — where

`scripts/calibration_verdict.py`:

- `AUTHORIZED_TUNING_FIELDS` / `AUTHORIZED_TUNING_CHANNEL` (≈2647–2658) name the six required
  fields and the one authorized channel.
- `_authorized_tuning_finding` (≈2661–2699) validates a declaration: missing/malformed →
  FAIL; incomplete → FAIL; wrong channel → FAIL; `set_ex_ante` or `not_swept` not asserted →
  FAIL (rule 1 (c)); `years_held` ≠ scored years → FAIL (rule 1 (b)).
- `score_governance` (≈2702–2800): `false_asserts` is computed over all four assertions; **only
  when every false assertion is one of the two scoped ones** (`no_fit_to_price_residuals`,
  `levers_trace_to_measured_input`) does it consult `_authorized_tuning_finding`, and only a
  validating declaration clears them. A false scoped assertion with no declaration, or with a
  malformed one, stays a FAIL (*"attestation false: …"*). A declaration present when neither
  scoped assertion is false is validated anyway and a malformed one becomes a machine issue.
  `no_pinning_to_actuals`, `outage_filter_exogenous_net_load` and the forbidden-flag check are
  never reached by the carve-out.

**So "C6 FAILS without the declaration block" is implemented**, and pinned by
`tests/scoring/test_calibration_verdict.py::AuthorizedPriceTuningTests` (§11 of rule-history).
`audit_keepers.attestation_shape_finding` (≈384–400) mirrors the declaration check.

**What is NOT machine-checked: the DOF-ledger half of condition (e).** `audit_keepers` check
E8 (≈797–835) validates only that a `free_parameters` ledger exists and that every
`identification == "residual"` row carries a non-empty `root_cause`. It does not look for a
ruling-identified row, and a row with any other `identification` string passes E8 without a
`root_cause`. This lane changed no scoring or audit logic; whether the ledger half should
become a check is routed, §4(b).

## 4. Gaps routed (nothing adjudicated, nothing edited outside the three files)

- **(a) MISO keeper attestation carries no ruling-identified ledger row for the lift** (§2(ii)).
  Route: **calibration desk, MISO lane.** The fix is the desk's — an entry in
  `free_parameters.entries` (e.g. name `offer_curve_by_group non-steam fossil lift`, value
  `1.10`, identification *"price residual, authorized channel (rules 1/13 amendment
  2026-09-05)"*, source = the ruling, `n_entries` 41 → 42) — and it is a re-attestation of the
  keeper's committed bundle, not a solve. Whether the desk instead treats the existing
  `offer_curve_by_group` row as the carrier and amends its `source` is the desk's call; R-AY's
  text ("count them in the DOF ledger") reads as a distinct count.
- **(b) The ledger half of condition (e) has no machine check** (§3). Route: **audit program
  director** — a candidate E8 extension (a well-formed `authorized_price_tuning` declaration
  requires a ledger row whose identification names the ruling) is a one-function change in
  `audit_keepers.py`, out of this lane's DO-NOT scope ("change any verdict or scoring path").
- **(c) R-AY is not yet in the repo record.** The board's newest ruling label is R-AX; no file
  in `docs/` or `results/calibration/*.md` mentions R-AY. This finding and rule-history §12 quote
  the ruling from the dispatch verbatim. Route: **director** — the board is out of this lane's
  scope ("edit the board or the plan").
- **(d) `check_gate_a_provenance` was RED at the pin `144eabe3`**: *"NYISO: gate.a_keeper_marker
  cites SUPERSEDED keeper '2026-09-05-nyiso-192-astoria-panel'; the ISO's current designated
  keeper is '2026-09-06-nyiso-196-extract-basis'"*. Not this lane's; repaired on main by
  `32f8de52` (*"Gate-(a) re-key … NYISO row -> 2026-09-06-nyiso-196-extract-basis"*), which is
  why the branch was re-pinned onto `976a3e6d` (§5 shows the after-reading).
- **(e) `check_bench_freshness` is RED at both pins:** `frontend/data/backcast/bench/ERCOT/2022.json.gz`
  *"is STALE — carries builder fingerprint b2f21b9a00d3 but HEAD's is 4254168edcfe"* (24 parts
  checked, 1 STALE, 23 with engine drift — the drift is WARN-only). The part was committed by
  `f1561c2d` *"ercot-249/250: register the 2022 validation touchpoint, both keeper configs"*
  (2026-09-05) carrying the **pre-R-AS** fingerprint, i.e. it was stamped after the §10 re-stamp
  with the superseded digest. Untouched by this lane and by main between the pins. Route:
  **ERCOT desk** (regenerate per the gate's own instruction) and **director** (not on the board).
- **(f) `tests/scoring` is not fully green at the pin, independent of this lane:** 5 failures
  at `144eabe3` before and after the edits (identical sets) — four in
  `test_ff_readiness_battery.py` (`test_walk_inputs_trivial_single_year`,
  `test_resolve_report_no_hard_fail_full_horizon`,
  `test_ercot_confirmed_horizon_is_reported_not_failed`,
  `test_build_registration_scorecard_no_iso_gate_open`) and
  `test_gate_a_provenance.py::test_live_board_passes` (the (d) red, as a test). None touches
  `calibration_verdict`. §5 records the after-re-pin reading; whatever remains red there is
  routed to the director as pre-existing at `976a3e6d`.

## 5. Gate readings at the PR head (re-pinned on `976a3e6d`; local, `uv run --frozen`, `$?` of the script itself)

| gate | at pin `144eabe3` (before edits) | at PR head (`976a3e6d` + this lane's edits) |
|---|---|---|
| `scripts/audit_keepers.py --check` | 0 — `PASS: 0 failure(s), 0 warning(s)` | **0** — `PASS: 0 failure(s), 0 warning(s)` |
| `scripts/check_registry_payload_parity.py` | 0 — `OK (14 runs checked, 47 bundle dirs swept)` | **0** — same |
| `scripts/check_gate_a_provenance.py` | **1** — NYISO marker cites superseded nyiso-192 (§4(d)) | **0** — `OK (6 row(s) checked …)` — repaired on main by `32f8de52`, not by this lane |
| `scripts/check_mechanism_matrix.py --base origin/main` | 0 | **0** — prose headers match, gap + shared ratchets OK |
| `scripts/check_forecast_staleness.py` | 0 (WARN-only) | **0** — two standing WARNs (fresher hindcast sidecars; 25/101 verdict stamps undated), neither this lane's |
| `scripts/check_bench_freshness.py` | **1** — `bench/ERCOT/2022.json.gz` STALE (§4(e)) | **1** — identical reading: `24 part(s) checked, 1 STALE, 23 with engine drift`. **Pre-existing at both pins, untouched by this lane, routed §4(e).** |
| `scripts/check_golden_manifest.py` | 0 | **0** — `golden-manifest: OK` (50 manifests, 91 entries) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | **0 / 0** — `All checks passed!` / `1338 files already formatted` |
| `pytest tests/scoring -q` | 5 failed / 1328 passed (§4(f)) | **4 failed / 1349 passed**, 3 skipped, 1 xfailed, 54 subtests passed. The gate-(a) test now passes. The four `test_ff_readiness_battery.py` failures are **environmental**: every one asserts on `InputResolution(iso='ERCOT', name='confirmed_retirements', status='MISSING', detail='clean partition unbuilt (data/clean is gitignored) …')` — this session hydrated `DATA PROFILE: code`, so `data/clean` is unbuilt. The module does not import `calibration_verdict`; the failure set is identical before and after the edits. |

**Net: six of seven gates exit 0; the seventh (`check_bench_freshness`) is red on `main` at
both pins on an ERCOT bench part this lane may not touch. The dispatch's "all seven gates …
exit 0" is therefore NOT met on the seventh, and could not be met by this lane without
regenerating an ERCOT bench part (a dashboard artifact) — stated here rather than worked
around.** `AuthorizedPriceTuningTests` and every other `test_calibration_verdict.py` test pass.

### 5.1 After merging main `76886c2e` (merge commit `f8c90cac`; conflict-resolution refresh)

Main gained rule 30 `[R-TOUCHPOINT-FOLD]` (`17b9294f`), which took rule-history **§12**; the
rule 21 section moved to **§13** and "Changes to this file" to **§14**, with every pointer in this
lane repointed (CLAUDE.md rule 21, the §11 forward pointer, the changelog row, the scorer
docstring, this finding). Re-run on the merged tree: `audit_keepers`, `check_registry_payload_parity`,
`check_gate_a_provenance`, `check_mechanism_matrix`, `check_forecast_staleness`,
`check_golden_manifest` and `ruff check` all exit 0; `check_bench_freshness` is still red on the
same pre-existing `bench/ERCOT/2022.json.gz` part; `tests/scoring` still shows only the same four
environmental `test_ff_readiness_battery.py` failures (1349 passed). One new red surfaced from
main, not from this lane: `ruff format --check` flagged `scripts/calibration_verdict.py` on a
three-line `_reclassify(...)` call at ≈1113 that `17b9294f` committed unformatted — identical on
`origin/main` itself. Because CI's format job would fail this PR on it and the file is already in
the lane's diff, `ruff format` was applied to that file here; `ast.dump` of the module is identical
before and after, so it is whitespace only. `ruff format --check .` then exits 0.

## 6. Rule 27 blob verification after push

Push transport: `git push -u origin claude/g3-rule-21-price-tuning-xref-mfav8w` (small text-only pack;
first try, no HTTP/1.1 fallback needed). Remote `refs/heads/…` = local HEAD = `2286675d`. Each file
was then fetched back from GitHub at that commit (`get_file_contents` by sha) and compared to the
on-disk bytes after stripping the MCP envelope prefix; the envelope's reported git blob SHA was
compared to local `git hash-object` as well.

| file | lines remote / local | sha256 (16) remote / local | git blob remote / local | |
|---|---|---|---|---|
| `CLAUDE.md` | 703 / 703 | `d6d055d0fe4c53c8` / same | `cd1375a365c7` / same | MATCH |
| `docs/governance/rule-history.md` | 880 / 880 | `ea8e97ecf603da06` / same | `4fc9589a87c9` / same | MATCH |
| `scripts/calibration_verdict.py` | 3359 / 3359 | `56e973f819ce0208` / same | `a7239531472b` / same | MATCH |

The finding itself is a new file under 300 lines and is outside rule 27's verification duty.

**Re-verified after the merge refresh (push `20b7a1a6`, `git push`, first try):**

| file | lines remote / local | sha256 (16) remote / local | git blob remote / local | |
|---|---|---|---|---|
| `CLAUDE.md` | 742 / 742 | `b5a567723707917e` / same | `89c1d3016d15` / same | MATCH |
| `docs/governance/rule-history.md` | 933 / 933 | `26d5f7c6bf940258` / same | `517ff143218b` / same | MATCH |
| `scripts/calibration_verdict.py` | 3445 / 3445 | `dab8fc56b46bf6ed` / same | `0e192c21ff5a` / same | MATCH |


## 7. Standing-test log — every dispatch claim, checked

| dispatch claim | checked against | reading |
|---|---|---|
| rules 1/13 amendment on main at `4545300d`, PR #4855 | `git log` | `4545300d` *"Rules 1/13: the registered offer-curve band multipliers are an authorized price-tuning channel"*; merged by `80695cb2` = PR #4855 ✔ |
| rule 1 condition (e) wording | `CLAUDE.md` rule 1 | *"carries the value as a free parameter in the DOF ledger (rule 21 `[R-DOF]`), identified by the ruling rather than by a measured source"* ✔ |
| rule 13's one-exception clause | `CLAUDE.md` rule 13 | present, *"ONE EXCEPTION, and only one"* ✔ |
| rule-history §11 is the rules 1/13 entry | file | ✔; rule 21 had no section — §12 created |
| rule 21 at CLAUDE.md line ~113 | file | line 113 ✔ |
| bundle `miso220_nonsteam_lift*` | `results/calibration/` | on disk as `miso220_nonsteamlift_B` (no underscore) — recorded |
| keeper `2026-09-05-miso-220-nonsteam-lift`, promoted `743b3dc0` | keeper shard + `git log` | ✔ both |
| `no_fit_to_price_residuals` set FALSE deliberately, `ed07a641` | attestation + `git log` | ✔ both |
| scorer ~lines 2714–2761 read/scope the two assertions | file | docstring 2712–2725, scoping 2756–2775 ✔ |
| "x1.10 lift" | run_config ratio vs miso-217 control | 1.1× on 4 bands × 11 classes; steam gas 1.0×; nothing else moved ✔ |
| branch `claude/g3-rdof-price-tuning-xref-h8n4pc` | harness | assigned `claude/g3-rule-21-price-tuning-xref-mfav8w` — recorded, header |
