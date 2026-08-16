# miso-160 transfer: apply instructions (for a session WITH working git)

This session ran API-only (no git credentials — the miso-159 situation), so
the miso-160 implementation commit travels as a patch in three verified
pieces. A follow-on session with working git applies it:

```
cd <repo>   # branch claude/miso-backcast-calibration-nk4zhj
cat .claude-transfer/miso160/impl.part1.diff \
    .claude-transfer/miso160/impl.part2.diff \
    .claude-transfer/miso160/impl.part3.diff \
    > .claude-transfer/miso160/implementation.diff
sha256sum -c .claude-transfer/miso160/implementation.diff.sha256
# expected: e0679f232da240eefe1eb8759dc86c74f3795a87878fbe31ca6bb711e95d9733
git apply --index .claude-transfer/miso160/implementation.diff
```

Then the ONE file the patch deliberately omits —
`docs/codebase-site/data/mechanism-matrix.js` (1.19 MB; its diff is
dominated by deterministic anchor-digit churn):

1. Insert the single new base row from
   `.claude-transfer/miso160/matrix-base-row.txt` immediately AFTER the
   `commission_year_cod_fallback` row's closing `},` (three source lines: the
   `{ id: "summer_wefor_share_override", ...` line, the `def:`/`note:` line
   pair, and the closing `},`).
2. `python3 scripts/check_mechanism_matrix.py --fix-anchors`
3. `python3 scripts/check_mechanism_matrix.py`  # must exit 0

Commit, then verify EVERY post-apply blob against
`.claude-transfer/miso160/BLOBS.txt` (`git ls-tree -r HEAD` on the listed
paths; `docs/codebase-site/data/mechanism-matrix.js` must land on
`8e5f437026de49645cd02cc84b2783a766abd6d3` — a mismatch means the insert
point or anchor pass differs; stop and compare). Delete
`.claude-transfer/miso160/` after everything verifies.

Provenance: the PREREG (a96702b) and data-ask amendment (f3e776f4) were
pushed BEFORE construction; the patch is the session's local commit f3c3f90
diffed against f8c93af excluding those two files and the matrix base file.
Piece integrity was verified from the authoring session: remote piece blobs
9b83a95e / f8ebe4bc / 8143d607, whose concatenation was proven byte-identical
to the local implementation.diff by reconstructing the remote split locally
and matching git blob shas.

Still to come from the same session: the FINDING, registry sidecars, bench
updates, calibration log + queue stamp + MISO shard verdict re-stamp, and
the manifest of artifacts that CANNOT travel the API path (run payloads
frontend/data/backcast/runs/*.js ~1.5 MB each; bundle hourly/*.parquet,
binary) with sha256 hashes — those need this container (while it lives) or
a re-solve to regenerate.
