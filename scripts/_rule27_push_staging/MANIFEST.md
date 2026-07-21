# Rule-27 push staging — five oversized files (2026-07-21)

**Why this directory exists.** This session's remote git relay rejects every
`git push` (HTTP 413 / disconnect on any pack size — the CLAUDE.md "Git &
Pushing" failure mode), and the five files below are too large to pass
through a single `mcp__github__push_files` call from a model response
without risking the response-budget truncation incident CLAUDE.md rule 27
documents (the `constants.py` 6,368→33-line clipping). Rather than overwrite
real source files with partial content (forbidden) or lose the work when the
ephemeral container is reclaimed, the five files travel here as a verified,
compressed, byte-exact archive. **The real files on this branch are still at
their `d7dbce9` (pre-lane) state until assembled** — the branch is
import-coherent in that mixed state (the new pipeline modules are additive;
the old orchestrators reference only names the new package still exports),
but the lane is complete only after assembly.

## Contents

Consecutive byte slices of the single-line base64 encoding of
`rule27-bigfiles.tar.gz`, in lexicographic filename order:
`rule27-bigfiles.tar.gz.b64.part00.txt` (one 43,000 B slice), then
`part01-00.txt` … `part08-08.txt` (4,300 B pieces; the final piece
`part08-08.txt` is 348 B). The piece split exists because whole 43,000 B
parts proved unreliable to transcribe through model tool calls (single-
character substitutions, always caught by per-blob verification); 4,300 B
pieces localize any error to a cheap retry. `cat` in lexicographic order
(the `part*` glob below) reproduces the byte stream exactly.

* sha256(concatenated .b64) = `e63fdb8288de639bde860aef960d53fbd3a9d11111423c2fbcdf0372e803966d`
* sha256(decoded .tar.gz)   = `ce56d4f1b3271e941fb1bd4ce343c6bce9efdcf55ac095aa25aae9c112caba88`

Archive members (paths relative to the repo root), with the byte size and
the **git blob SHA each file must have after assembly** (equal to the lane's
local HEAD blobs; verify with `git hash-object <file>`):

| file | bytes | lines | git blob sha |
|---|---|---|---|
| scripts/run_calibration_full.py | 445,217 | 9,166 | `47da38c0033551ffd763d7dd1618fca312817dda` |
| scripts/run_calibration.py | 216,931 | 4,326 | `f737ad31ed3425b1b881ae91292caac25f83b9fe` |
| src/market_sim/runner.py | 108,930 | 2,292 | `7b5912f03db3624cc6ff1c35dcf3b4d1ffc021fc` |
| src/market_sim/pipeline/backcast_config.py | 106,416 | 1,764 | `c877f021b6fa6228ac28d010a3260ee623e143b7` |
| docs/handoffs/orchestrator-unification-plan-2026-07.md | 117,406 | 1,723 | `fd01c9e7a9ad039a85d3dc857db1d507f9b4b358` |

## Assembly (run from the repo root, on this branch, in any environment with a working `git push`)

```bash
cat scripts/_rule27_push_staging/rule27-bigfiles.tar.gz.b64.part*.txt > /tmp/big.b64
sha256sum /tmp/big.b64   # must be e63fdb8288de639bde860aef960d53fbd3a9d11111423c2fbcdf0372e803966d
base64 -d /tmp/big.b64 > /tmp/big.tar.gz
sha256sum /tmp/big.tar.gz  # must be ce56d4f1b3271e941fb1bd4ce343c6bce9efdcf55ac095aa25aae9c112caba88
tar xzf /tmp/big.tar.gz     # extracts the five files onto their real paths
for f in scripts/run_calibration_full.py scripts/run_calibration.py \
         src/market_sim/runner.py src/market_sim/pipeline/backcast_config.py \
         docs/handoffs/orchestrator-unification-plan-2026-07.md; do
  git hash-object "$f"      # must match the table above
done
git add -A && git rm -r scripts/_rule27_push_staging
git commit -m "Assemble rule-27 staged files; remove push staging"
git push
```

After assembly + verification, this directory MUST be deleted in the same
commit. Until then, nothing imports from here and no real file is shadowed.
The regression evidence for the assembled content (two-keeper byte-identity
gate, forecast smoke, fast-suite triage) is recorded in
`docs/handoffs/orchestrator-unification-plan-2026-07.md` §7.3.10 — itself
one of the five staged files, so read it post-assembly.
