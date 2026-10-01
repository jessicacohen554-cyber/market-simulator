# ADDENDUM to PRECOMMIT-spp-27 — the registration seam, declared BEFORE the span solve

**Lane** SPP-27 · **Charter** `docs/handoffs/PRECOMMIT-spp-27-commitment-grain-2026-09-10.md` ·
**Written and pushed before any span LP.**

## The collision, stated plainly

Rule 32 `[R-SHARD]` (c)6 forbids a shard from running `dashboard_add_run.py`, and (d) says
registration happens **once, in the parent, after the shards land**. Rule 15 `[R-DASHBOARD]`
requires the run to be registered **in the session that produced it**.

Those two compose only when the parent can reach the bundle. **Here it cannot.**
`scripts/render_calibration_html.py` — which `dashboard_add_run.py` drives through
`render_backcast.generate` — reads the FULL bundle (`system.parquet`, the `inputs/` frames,
`storage.parquet`, the scarcity frames), not the slim files. A full SPP span bundle is hundreds of
MB of parquet, which the repo's own Git & Pushing rule states is **not licensed** for `git push`
("NOT licensed for a full bundle directory … the original 413 rationale still holds there"). So the
bundle physically cannot travel from the shard's container to the parent's.

## The resolution, and why it is the narrow one

**The SPAN shard registers, as the SOLE writer, and the parent owns everything else.**

Rule 32(c)6's stated rationale is concurrency — *"shared generated files — five shards writing them
WILL collide"*. **There is exactly one registerable shard in this lane** (the screen bundle is a
throwaway probe rule 29(2) forbids registering), so there is no concurrency for the prohibition to
protect against. What the span shard is instructed to commit is **exactly what rule 15 names as the
deliverable and nothing else**:

- its bundle's slim files + `hourly/` sidecars (`git add -f`, the family being gitignored),
- `frontend/data/backcast/registry/<id>.json`,
- `frontend/data/backcast/runs/<id>.js`,
- the changed `frontend/data/backcast/bench/SPP/` parts.

It is **forbidden** `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, any
`keepers/<ISO>.json`, and anything else under `frontend/data/backcast/**`. It runs
`dashboard_add_run.py` with **`--no-prune`**: rule 31 `[R-RETAIN]` says nothing is removed while the
promotion question is open, and which run is SPP's keeper is precisely that question.

**The parent still owns the seam** (rule 32(d)): the scoring read-out, the rule-28 matrix cell, the
calibration-log entry, the RESULT document, and the promotion question put to the owner. The parent
runs **no LP** at any point, as rule 32(a) requires.

## Also pushed before the span solve

`scripts/gen_spp27_attestation.py` — keeper 8's DOF ledger inherited unchanged (`n_entries` 3,
`n_residual` 2) plus the `mustrun_window_commitment_grain` switch block, with
`authorized_price_tuning` replayed **verbatim** at 0.93 and not re-cut. It exists in the parent and
is pushed **now** rather than after the solve for one reason: rule 32(c)6 forbids the shard from
editing `scripts/`, so the script must be at the shard's pinned SHA for the shard to run it.
`replay_keeper.py --out-dir` does not propagate `calibration_attestation.json`, so without it the
span scores **C6 UNATTESTED** for a plumbing reason rather than a governance one.

Smoke-tested in the parent against a throwaway output directory: ledger reads
`n_entries=3 n_residual=2`, entries `offer_curve_by_group`, `offer_curve_smoothing`,
`wefor_multiplier` — keeper 8's, unchanged.
