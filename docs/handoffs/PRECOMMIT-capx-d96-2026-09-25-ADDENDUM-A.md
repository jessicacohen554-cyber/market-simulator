# ADDENDUM A to `PRECOMMIT-capx-d96-2026-09-25.md` — the shard launch

**Pushed while the four legs are being prepared, before any of their numbers exist.** No prediction, gate or
scoring rule is changed by this addendum.

## A.1 The four shards, pinned to the PRECOMMIT SHA

`source_revision = 5a48f43787c3ec0d29ae451680ab62a5e53b5156` (full 40 characters, rule 32(c)(1)). Launched
2026-09-25 15:49–15:50Z, concurrently.

| leg | session | out-dir / branch | predicted key |
|---|---|---|---|
| `base` | `session_01XQC64M1Fyvk8VdYo9nuSPq` | `results/ff-t3-neiso-golden/d96/base` / `claude/capx-d96-base` | `dbef1ecac9596c90` |
| `carbon_plus25` | `session_01R11aZwEJg3TssJwag1Pu4V` | `…/d96/carbon_plus25` / `claude/capx-d96-carbon_plus25` | `f66e7b51d3731465` |
| `gasup150` | `session_018uTNBeQ5A2GRzTJZGGQzPb` | `…/d96/gasup150` / `claude/capx-d96-gasup150` | `d3ff933838e3fb12` |
| `gaspm5` | `session_01VcENsyT3dWgkkwq31rME4D` | `…/d96/gaspm5` / `claude/capx-d96-gaspm5` | `8d23ff10a99c4a8a` |

Each prompt carries: H1 (the SHA; no rebase/pull/sync), the container preparation, the exact D92 command
with the leg's one override, H2 (both pins + override + 25 solved years off `run_config.json`), the key
check (a mismatch is reported, never repaired), the rule-34(a) push (`.gitignore` negation + plain
`git add`, slim commit first, parquets second; never `-f` / `-A` / `.`), the named prohibitions, the
success/failure sentence, and the numeric report. D92 §7's operational lesson is in the prompt: **the
shard must not end its turn while a build or solve is still running.**

## A.2 The parent's standing work while they solve (zero LP)

Already done and recorded in the PRECOMMIT: scorer control (NON-PROVENANCE IDENTICAL), both D92 instruments
re-validated at this HEAD, the FC-5 and whole-verdict dry runs over `d94/vre_short`, and the key-provenance
census (245 / 188 / 28 = 16 KNOWN + 10 LAG + 2 UNKNOWN).
