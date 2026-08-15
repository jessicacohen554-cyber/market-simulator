# miso-159 transfer staging (temporary — delete at close-out)

This directory exists because the authoring session's container lost its git
transport mid-session (egress-proxy relay restart; credentials unrecoverable
in-shell) while the GitHub MCP path caps per-call payloads well below
`scenarios.py` (908 KB) and the dashboard run payloads (~1.5 MB).

Contents:

* `transfer-pack.txt` — post-apply blob hashes for every file the miso-159
  Phase-0 commits touch, plus the application recipe.
* `edited-files.diff` — the `git apply -p1` diff for the EDITED files
  (scenarios.py, assembly.py, test_campd_bins.py, mechanism-matrix.js, the
  five non-MISO shards).
* The NEW files (probe) are committed directly alongside this pack; the probe
  record `_miso159_cod_vintage_instrument.json` regenerates deterministically
  by running the probe on the full MISO data profile and must reproduce the
  hash pinned in the pack.

Application (executor session with working git):

```bash
git checkout claude/miso-backcast-calibration-9b7449
git apply -p1 .claude-transfer/miso159/edited-files.diff
# write/keep the committed probe; regenerate the probe JSON; then verify:
git hash-object <every path in transfer-pack.txt>   # must match exactly
```

Any hash mismatch is stop-the-line (CLAUDE.md rule 27). Delete this whole
directory in the close-out commit once the real files are landed.
