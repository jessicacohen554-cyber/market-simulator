# ADDENDUM to PRECOMMIT-caiso269 — three defects found by the shards, the re-pin, and what it cost

**Session caiso-269, 2026-09-10.** Amends `docs/PRECOMMIT-caiso269-lateevening-clean-2026-09-10.md` §6.
Written and pushed **before the rev2 shards' first LP**, so nothing here can be shaped by a result.

## §A1 — The pin moved: `a1513509` → `70fdc53b` → **`3f0d8b84`**

The PRECOMMIT §6 shard table names `a1513509c66b8682b5fadc5a2e273bd825ff3499`. **The four shards launched
on it all failed before reaching an LP**, on three separate defects. The operative pin for every rev2 shard
is **`3f0d8b84db0ec459c211eb57836fbb34cec9ec09`**. Nothing else in the PRECOMMIT changes: same arm, same
depth constants, same gate, same screen year (2025), same gates, same predictions — the mechanism was never
touched, only its CLI plumbing.

## §A2 — Defect 1 (PRE-EXISTING on `main`): the `--replay-bundle` path was broken for EVERY ISO

`run_replay_bundle()` still declared `holdout_authorized: bool` as a **required positional with no
default**, while the 2026-09-09 `[R-HOLDOUT]` removal deleted the argument from its only call site and the
body never referenced it. Every `--replay-bundle` invocation, for every ISO, therefore raised `TypeError`
before any LP. Verified pre-existing by reading `origin/main:scripts/run_calibration_full.py` (line 8698),
not this branch.

Removed the dead parameter rather than defaulting it — rule 26 `[R-DELETE]`: a parameter that still parses
is a re-armable answer key — and corrected the docstring line still claiming the year span was
*"holdout-gated either way (rule 22)"*. Statically verified after the fix: the call site binds with **0
missing required parameters and 0 unknown keywords**.

## §A3 — Defect 2 (PRE-EXISTING on `main`): `--help` crashed

`scripts/run_calibration_full.py --help` raised `ValueError: unsupported format character ')' at index
1002`. Three argparse help strings carried a literal unescaped `%`, which argparse expands:
`--caiso-st-gas-peak-measured`, `--nyiso-ct-peaker-bands-measured`,
`--nearby-fuel-price-zone-donor-guard`. Escaped to `%%`; **rendered help text is unchanged**. `--help` now
exits 0. Verified pre-existing by stashing this branch's diff and reproducing on `main`.

This is a drive-by repair of another lane's help text, and it is declared as such: it is three
character-level escapes with no behavioural surface, it is in a file this lane was already repairing, and
a broken `--help` cost two of the four attempt-1 shards their whole budget.

## §A4 — Defect 3 (MINE, and it is the important one): the flag was wired to the wrong channel

The first wiring passed `caiso_dsw_lateevening_clean` as a direct `solve_and_persist` / `backcast_config`
keyword. **`backcast_config` takes 36 explicit parameters and NO `**kwargs`, and carries a parameter for
none of the CAISO DSW clean-depth flags.** The keeper arms `caiso_dsw_surplus_clean` /
`_overnight_clean` / `_daytime_clean` and the whole `caiso_firm_import_*` family through the recorded
**generic override bag** — `prb_overrides`, recorded as `coal_prb_sigmoid_overrides`, applied by
`ScenarioConfig.with_overrides(**bag)`. The direct keyword would have raised `TypeError` at config build.

Rewired to the **caiso-252 `caiso_dsw_daytime_evening_trim` precedent**, which `run_replay_bundle` already
documents in place: the override **copies** the recorded bag and edits the copy, never the recipe dict. The
flag is now **REPLAY-ONLY with `default=None`**, so absent it keeps the bundle's own value and the replay
path stays byte-identical.

**Proven end-to-end at ZERO LP cost, against the keeper's own committed `run_config.json`:**

| check | measured |
|---|---|
| recorded bag carries the sibling flags | `caiso_firm_import_shape`, `_selfschedule`, `_envelope_clip`, `_selfsched_clip`, `caiso_dsw_surplus_clean`, `_overnight_clean`, `_daytime_clean` all `True`, `_daytime_evening_trim` `False` — 37 keys total |
| **G-IDENT, pre-solve** | applying the bag with the arm yields **exactly ONE differing `ScenarioConfig` field: `caiso_dsw_lateevening_clean`** |
| siblings unchanged | `caiso_dsw_daytime_clean` / `_overnight_clean` / `_surplus_clean` / `caiso_firm_import_shape` / `_selfschedule` / `caiso_per_hub_intertie` all identical control vs arm |
| resolver parity | `get_interchange_spec(...).caiso_lateevening_clean` **False → True**, in step with its already-armed sibling `caiso_daytime_clean` (True in both arms) |

## §A5 — What the shard reports were worth, stated plainly

**All four attempt-1 shards reported a blocker; none diagnosed it correctly, and one proposed a repair that
would have been wrong.** Y2025 called line 8702 "an erroneous `--replay-bundle` flag" (it is the
`def run_replay_bundle(` line). Y2024 named the holdout flag but proposed confirming the commit rather than
removing the orphaned parameter. Y2022 reached "delete three mis-wired kwargs", which is directionally
right. **Y2023 was right in substance** — it named the missing config forward — though its proposed fix
(add the field to `backcast_config` and `run_year`) is the opposite of the correct one: the field must NOT
be added there, because none of its siblings is.

Every claim above was re-verified against the source in the parent before any edit; none was acted on as
given. That is the intended posture (rule 32 `[R-SHARD]` (c)(6)-(7): a shard reports, the parent owns
`src/` and `scripts/`), and it worked — the shards' value was the *signal that something was wrong*, which
is exactly what a 20-minute stop-and-report is for.

## §A6 — Cost, stated rather than buried

Four shard containers spent ~9-13 minutes each and produced **no LP and no artifact** — the attempt-1
fleet is a total loss, and their four sessions are archived. No result was deleted (rule 31
`[R-RETAIN]`); there was none to delete. The rev2 fleet is four fresh shards on `3f0d8b84`.

**The honest lesson for the next lane:** the PRECOMMIT verified that the arm was correct and that it was
byte-identical off, but it did **not** verify that the CLI could deliver it. A single zero-LP bind check —
apply the recorded bag, count the differing `ScenarioConfig` fields — would have caught defect 3 before a
single shard launched, and would have caught defects 1 and 2 as soon as the replay path was exercised at
all. That check is now in §A4 and should be a standing phase-0 item for any lane adding a solve flag.
