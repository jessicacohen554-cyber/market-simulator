# ERCOT-64 landing blob (consumed)

`ercot64.patch.xz.b64.part1` carried the ERCOT-64 session diff (69 KB raw,
sha256 `94af63e3284d3b723d1d426db42d2d042817f95a3c070438165e29b89ccf998b`)
past the MCP relay's single-call ceiling; the one-shot
`.github/workflows/ercot64-floorscoped-land.yml` applied it sha-gated on the
runner (branch `claude/ercot-floor-scoped-lsl-5d490o`, landing commit
`1a1c0f4`). The blob was fetched back and byte-verified before the workflow
was pushed. Kept as the audit trail of the landing (the ercot63 precedent);
the patch content is fully represented in the repository history.
