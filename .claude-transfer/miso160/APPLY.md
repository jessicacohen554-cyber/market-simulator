# miso-160 transfer: apply instructions (for a session WITH working git)

This session ran API-only (no git credentials — the miso-159 situation), so
the miso-160 implementation commit travels as a patch. A follow-on session
with working git applies it:

```
cd <repo>   # branch claude/miso-backcast-calibration-nk4zhj, at the commit
            # that added this directory (or later, if only registration
            # artifacts followed)
sha256sum -c .claude-transfer/miso160/implementation.diff.sha256
git apply --index .claude-transfer/miso160/implementation.diff
python3 scripts/check_mechanism_matrix.py --fix-anchors   # regenerates the
            # mechanism-matrix.js base-row anchor digits my local commit
            # carried (the base file is 1.19 MB and its anchor churn is
            # deterministic, so it is deliberately NOT in the patch); then
            # ADD THE ONE NEW BASE ROW from matrix-base-row.txt after the
            # commission_year_cod_fallback row (see below) BEFORE running
            # --fix-anchors, and re-run scripts/check_mechanism_matrix.py
            # to exit 0.
git add -A && git commit
# Verify EVERY post-apply blob against BLOBS.txt:
git ls-tree -r HEAD --format='%(objectname) %(path)' | grep -Ff <(cut -d' ' -f2- .claude-transfer/miso160/BLOBS.txt) | diff - .claude-transfer/miso160/BLOBS.txt
# (mechanism-matrix.js blob 8e5f437026de49645cd02cc84b2783a766abd6d3 is the
#  expected result of row-insert + --fix-anchors at this tree; a mismatch
#  means the insert point or anchor pass differs — stop and compare.)
rm -r .claude-transfer/miso160   # after everything verifies
```

Order of operations that produced the patch (for the record): the PREREG
(a96702b) and data-ask amendment (f3e776f4) were pushed BEFORE construction;
the patch is the local commit f3c3f90 diffed against f8c93af EXCLUDING those
two already-pushed files and EXCLUDING docs/codebase-site/data/mechanism-matrix.js
(anchor churn; see above).

Still to come from the same session (later commits in this directory or
direct pushes): the FINDING, registry sidecars, bench updates, calibration
log + queue stamp + shard re-stamp, and the list of artifacts that CANNOT
travel the API path at all (run payloads frontend/data/backcast/runs/*.js
~1.5 MB each; bundle hourly/*.parquet, binary) with their sha256 hashes —
those need this container (while it lives) or a re-solve to regenerate.
