# ERCOT-65 session-diff landing blob (relanded, pinned)

`ercot65.patch.xz.b64.part1` is the ERCOT-65 session diff — the
`wind_ptc_vintage_offers` PTC vintage-scoping build (config field +
statutory constants, EIA-860 eligible-share loader, ira dispatch-offer
builder, both orchestrators + forecast runner, unit tests, probe scripts,
parameter-registry regen), the wtx run_config recorder-fidelity fix + the
ercot63 keeper/ablation record corrections + DOF-ledger entry, and the
ERCOT-65 docs (diagnosis §9, calibration-log entry, CLAUDE.md, CHANGELOG,
methodology-spec §1.2) — as one `git diff <PINNED_MAIN>..HEAD` patch,
xz-9 + base64.

The changed files total ~4.4 MB (past the MCP relay ceiling), so the
84 KB patch (31 KB b64) rides this blob and the one-shot
`.github/workflows/ercot65-negepoch-land.yml` applies it sha-gated
(sha256 `0b72f39be26ac027cb439310ad2323a1fa6ec2a684bc09384633e210e254793b`)
on the `claude/ercot-negative-price-epoch-368q8q` branch.

**Pinned base (reland fix):** the first landing attempt (PR #2201) merged
only this blob's README before the lander ran, and the lander then FAILED
because it merged *latest* `origin/main`, which had drifted past the
patch's base (`run_calibration_full.py` / `parameters.json` moved). This
reland regenerates the patch against a PINNED main sha
(`80114cd20890126ebf5c720722bbdacc7c6d19f4`) and the workflow merges that
exact sha, so main advancing during the run can never break the apply.
