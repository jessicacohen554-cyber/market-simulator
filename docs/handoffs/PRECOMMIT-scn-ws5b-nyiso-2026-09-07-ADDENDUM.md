# ADDENDUM 1 to PRECOMMIT-scn-ws5b-nyiso-2026-09-07 — the artifact route, the run ids, and the shard launch

**Written and pushed with the first two shards in flight and BEFORE any leg has returned.**
Nothing here is revised by a result. It records three things the parent PRECOMMIT could not:
a **conflict between this lane's charter and `.gitignore` at HEAD** and how it is resolved, the
**run ids and registration commands pre-declared** so registration cannot drift, and the
**shard launch record**.

---

## 1. THE CHARTER AND `.gitignore` DISAGREE ABOUT WHERE A STAGE-B BUNDLE LIVES. Recorded, resolved, routed.

**The charter's `FILES YOU OWN` names `results/scn-campaign-stageb-2026-09-07/NYISO/**` — and at
HEAD that entire tree is GITIGNORED**, by a rule added before this lane started
(`.gitignore`, final block):

> `# SCN-WS5B Stage-B campaign bundles (rule 29 clause (c) / rule 31 [R-RETAIN]):`
> `# kept OUT of the repo, never off local disk. The PRECOMMIT/FINDING carry every`
> `# number cited; git history is the record for the bytes.`
> `results/scn-campaign-stageb-2026-09-07/`

Verified, not assumed: `git check-ignore -v` on a Stage-B summary path returns
`.gitignore:1441`.

**This is not a defect and it is not overridden.** It is the exact form rule 31 `[R-RETAIN]`
prescribes ("what discharges the delete-before-merge duties is `.gitignore`, not `rm`"), it is
consistent with the three sibling blocks added the same day (capx D84, ercot-256, miso-243), and
`register_forecast_baseline.build_sidecar`'s own docstring already calls
`full_horizon_summary.json` **"the (gitignored) full_horizon_summary.json"** — i.e. the tool has
always expected the committed record to be the **sidecar**, not the results tree. Stage A's
committing of `results/scn-campaign-policy-2026-09-06/NYISO/<CASE>/` was the exception to the
tool's own convention, not the rule.

**Resolution — the mirror, and why it exists at all.** The committed deliverable is unchanged:
the `frontend/data/hindcast/<run-id>.json` sidecar, which is self-contained and is what the run
explorer, the audit and `check_forecast_invariants.py` read. But **each leg is solved in its own
S16 shard container, which dies**, and `register_forecast_run.py --summary` needs the summary
file *on disk at the coordinator*. So every shard copies exactly two files —
`full_horizon_summary.json` and `run_config.json`, a few KB — to

```
docs/handoffs/scn-ws5b-nyiso/<CASE>/
```

and commits **those**. No shard runs `git add -f`, and **no shard edits `.gitignore`**. The
mirror is the lane's transport and its provenance attachment (the same convention this lane's
Stage-A `docs/handoffs/scn-ws5a-policy-nyiso/score_gates_2026-09-06.json` used); it is **not** a
second copy of a bundle — the bundle itself, all of it, stays on local disk in each shard,
undeleted, per rule 31.

**ROUTED to SCN-DESK, not decided here:** the charter's `FILES YOU OWN` line and the `.gitignore`
block are in tension for any future Stage-B lane. This lane follows the **`.gitignore` rule at
HEAD** because it is the later instruction, it is rule-31-grounded, and it matches the tool's own
docstring. If the desk wants Stage-B slim files committed under `results/` the way Stage A's were,
that is a one-line ignore-rule change and a re-commit — **but this lane will not make it**, because
`.gitignore` is outside its declared regions.

---

## 2. Run ids and registration commands — pre-declared

`register_forecast_baseline.build_sidecar` builds the id as
`run_id = f"{iso.lower()}-{start}-{end}-{label}"` (`:184`), which is what produced Stage A's
`nyiso-2026-2030-scn-campaign-policy-2026-09-06-<slug>`. Stage B therefore registers as:

| leg | **pre-declared run id** | key (PRECOMMIT §4) |
|---|---|---|
| REF | `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-ref` | `f1a2ef17634b0467` |
| CAP-STATE-TIGHT | `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-cap-state-tight` | `462d197ef1f9e023` |
| CES-P60 | `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-ces-p60` | `ddff74e2738eaf96` |
| CES-T80 | `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-ces-t80` | `fc3ad07981d95d84` |
| ALL-CLEAN | `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-all-clean` | `774db75da9f4d95a` |

```
python3 scripts/register_forecast_run.py \
  --summary docs/handoffs/scn-ws5b-nyiso/<CASE>/full_horizon_summary.json \
  --label scn-campaign-stageb-2026-09-07-<slug> --kind scenario
```

Every leg's invariant FAILs are declared in `frontend/data/hindcast/invariant-failures.json`
**in the same commit as its sidecar**, then `scripts/check_forecast_invariants.py --sidecar-dir`
is run and **this lane quotes its own EXIT code** in the FINDING. The `--kind` and any
`--extra-meta` actually used are reported as used; if `--kind scenario` is not an accepted value
at HEAD, the accepted value is reported rather than silently substituted.

**Open observation to be checked at registration, not now** (Stage-A §9 item 5): whether
`meta.set_overrides` lands as `null` on the `--set`-constructed `CES-P60` leg. Reported as
observed; `SCN-FIX3` owns any repair.

---

## 3. Shard launch record

| shard | leg | session | launched |
|---|---|---|---|
| **S-1** | `CAP-STATE-TIGHT` | `session_01NGJCYY3dnspeh8qvmadnzj` | 2026-09-08T05:41:29Z |
| **S-2** | `REF` | `session_01DfnnL7pj4rt9YhRbb1UgDV` | 2026-09-08T05:42:02Z |
| S-3 | `CES-P60` | *(launched as S-1/S-2 return; S14 caps SCN-track concurrency at 2)* | |
| S-4 | `CES-T80` | *(queued)* | |
| S-5 | `ALL-CLEAN` | *(queued)* | |

Each shard was issued the same standing prompt: solve its one named case, **STOP on a cache-key
mismatch against §4 and change nothing**, mirror-and-commit the two slim files, never delete the
bundle (rule 31), and write in **no** directory but its own two. Every shard prompt cites S18 by
name as the sole authorization for `--full-solve-authorized`.

**`CARB-MID` has no shard** — killed at phase 0 on the 25-year identity of PRECOMMIT §3, and the
substitution question is routed to SCN-DESK there. **25 solve-years are not spent.**

---

*Pushed before any leg returned. Parent: `docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md`.*
