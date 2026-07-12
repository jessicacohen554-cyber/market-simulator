# ERCOT-62 re-landing provenance

- Patch blob: `diff.patch.xz.b64.part1/2` (sha256 of decoded patch: `2800ef7400af02d4be3e39129140374b990aea46e528f289b6a25945f73e6c54`).
- First landing: branch `claude/ercot-binding-price-formation-2xxap3`, runner commit `fb1b8eb` (workflow `ercot62-reland-session`); PR #2145 closed unmerged.
- Second landing: branch `claude/ercot62-reland2` off post-#2148 main, runner commit `486c92f` (workflow `ercot62-reland2-session`) — byte-identical patch, all post-conditions + mechanism tests passed on the runner.
- Supersedes PRs #2139 and #2145.
