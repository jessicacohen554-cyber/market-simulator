# HANDOFF — the SHARD LAUNCHER protocol: launch shards, PROVE they are working, report on the owner's **1 / 2** status

**Reusable launcher prompt. Written 2026-09-09 by session caiso-268 SPAN**, whose three sibling
per-year shards were launched and **silently never landed** — the launcher reported them as
"launched" and nobody found out until the span shard checked the remote at the end and found only
its own branch. **This protocol exists so that cannot happen again.** A shard that was created is
not a shard that is working, and "launched" is not a status.

---

## §0 — THE OWNER'S STATUS CODE. Use it everywhere; do not invent a third digit.

| code | meaning |
|---|---|
| **1** | **ARCHIVABLE — the session's work is DONE.** Its deliverable is solved, written, committed and **pushed to its own branch on the remote**, and nothing is left for it to do. Safe to `archive_session`. |
| **2** | **STILL WORKING.** Anything else, without exception. |

**There is no third code, and 2 is not a place to hide.** A shard that is dead, OOM-killed, blocked,
stalled, or never started **is a 2**, and **every 2 must name what it is doing and what it is waiting
on** in the same line. A 2 that says only "still working" is not a report.

**Never write "launched", "spawned", "running" or "in progress" as a status.** Those describe what
*you* did. The code describes what the *shard* has produced. Report **1** only against evidence from
the remote (§4), never against a `create_session` return value.

---

## §1 — FILL THIS IN BEFORE YOU DO ANYTHING ELSE

The rest of this document is mechanism and does not change between sessions. This block is the
science, and it is the only part the owner edits:

```
SESSION NUMBER  : <iso>-<N>                     # e.g. caiso-269 — take the "Next number" from the last log entry
ISO             : <ERCOT|CAISO|PJM|MISO|NYISO|NEISO|SPP>
DATA PROFILE    : <code|shared|ercot|caiso|pjm|miso|nyiso|neiso|all>
MECHANISM       : <one sentence: exactly what changes, and the ONE seam it changes it at>
DECIDED BY      : <owner instruction, VERBATIM, with its date>
YEARS           : 2023 2024 2025            # training tier. Anything else needs §7's marker check FIRST.
BASELINE/CONTROL: <the incumbent keeper's run id + bundle dir>
RUN ID          : <YYYY-MM-DD>-<slug>       # what dashboard_add_run will mint; check it with render_backcast._slug
SHARDS          : one per solve year, PLUS one SPAN shard (§3 — the SPAN is not optional)
```

If any line is blank, **stop and ask**. A shard launched against a blank is a wasted container.

---

## §2 — PIN AN IMMUTABLE COMMIT SHA. A branch name will fail.

Do this **first**, before creating any session:

```bash
git fetch origin main
git rev-parse HEAD          # your PRECOMMIT must already be pushed and reachable from this sha
```

Every shard is created with **`source_revision: <full 40-char sha>`**, never a branch name. The CCR
source-processing worker resolves against a repo view that lags a freshly-created ref, so a
branch-pinned shard dies at clone with `ref_not_found` — this killed **all five** shards of one
previous launch and one of caiso-267's. A merged-then-auto-deleted branch fails the same way.

**The PRECOMMIT is pushed and reachable from that sha BEFORE the first shard is created.** Shards
read their charter from the repo, so a charter that is not in their clone does not exist.

---

## §3 — THE SHARD PLAN, AND WHY THE SPAN SHARD IS MANDATORY

| shard | branch | scope | registerable? |
|---|---|---|---|
| Y\<year\> (one per year) | `claude/<sess>-y<year>` | that year alone | **NO — throwaway probe** |
| **SPAN** | `claude/<sess>-span` | **every year, ONE invocation, sequential** | **YES — the only one** |

**Per-year shards CANNOT be composed into a registerable bundle, and this is measured, not
assumed.** Per-year shards carry **different year-scoped `eia923` / `eia930` / `campd` snapshots**,
so a hand-composed bundle scores one year against another's inputs. The CAISO lane did exactly this
on 2026-09-09 and got a broken **C4 `r=None, NRMSE=8.406`** against a real 0.877 / 0.298
(`docs/RESULT-caiso-fuelvintage-2026-09-09.md` §6a). **Rule 16 `[R-ALLYEARS]`'s "one bundle" also
means ONE INPUT SNAPSHOT.**

So the per-year shards earn their containers by returning **fast, in parallel, with the structural
gates** — any one of them tripping a STOP gate kills the arm before the span finishes — and the SPAN
shard produces the thing that gets registered. **Rule 12 `[R-PARALLEL]`: years inside the SPAN
invocation stay sequential, always.**

**One LP per container.** Rule 12's "~2 simultaneous" cap is measured **too generous for a per-plant
ISO on a 15 GB box** — caiso-267 §8.2 OOM-killed at 7.5 GB RSS running two. Each shard owns its own
container, so cross-shard parallelism is free; **within** a container it is one at a time.

---

## §4 — LIVENESS. THIS IS THE PART THAT WAS MISSING, AND IT IS NOT OPTIONAL.

`create_session` returning an ID proves **nothing**. A shard is proven working only by evidence it
produced. Three checkpoints, each with a deadline and a defined action:

### T+10 min — DID IT CLONE?
```
mcp__Claude_Code_Remote__get_session(session_id)
```
Check `status` and that it is past initialization. **A shard still not started at T+10 is DEAD** —
almost always `ref_not_found` (§2). **Do not wait it out.** Re-pin the sha, relaunch, and report the
shard **2 — DEAD at clone, relaunched at \<time\>**.

### T+25 min — HAS IT PUSHED ITS OWN HEARTBEAT?
**Every shard prompt must require an early push** — its own ADDENDUM/gate doc, before its first LP
(which the G-DRIFT / pre-registration duty requires anyway, so this costs nothing extra):

```bash
git ls-remote --heads origin 'claude/<sess>-*'
```

**A branch on the remote is the ONLY acceptable proof of life.** This is the exact check caiso-268
never made until the end. A shard with no branch at T+25 is **2 — no heartbeat**; interrupt it,
read its transcript, and either steer it or relaunch it.

### Every ~20 min thereafter — IS IT STILL MOVING?
Re-run the `ls-remote` and `get_session` sweep. A shard whose branch sha has not moved across **two
consecutive sweeps** while `get_session` shows it idle is stalled: steer it with `SendMessage`
(load via `ToolSearch("select:SendMessage")`), or `interrupt_session` then steer.

**Do not poll with `sleep` in a tight loop.** Use `send_later` to wake yourself, or a foreground
`until <check>; do sleep 60; done`. **Never end your turn with a shard on 2 and no scheduled
wake-up** — that is precisely how three shards were lost.

---

## §5 — DISJOINT WRITE SETS. Collisions are prevented by prohibition, not by hope.

Put this table in **every** shard prompt, filled in for that shard:

* **Every shard may write ONLY**: its own bundle dir, and its own uniquely-named docs
  (`docs/RESULT-<sess>-<shard>-*.md`, `docs/ADDENDUM-<sess>-<shard>-*.md`). Nothing else.
* **NO shard may write**: `.gitignore` · the shared override/config file · the PRECOMMIT ·
  `CLAUDE.md` · anything under `src/` or `scripts/` · any **other** shard's bundle or docs.
* **ONLY the SPAN shard may write the shared per-ISO surfaces**, and only after its own solve:
  `frontend/data/backcast/registry/*` · `runs/*` · `bench/<ISO>/*` · `keepers/<ISO>.json` ·
  `status/<ISO>.js` · `docs/codebase-site/data/mechanism-matrix/<ISO>.js` ·
  `docs/calibration-log/<iso>.md`. **The bench part is the sharp one**: any solve rewrites
  `bench/<ISO>/<year>.json.gz`, so three year-shards committing bench parts collide on all three
  files at once. Year shards are forbidden from committing it.
* **Rule 25 `[R-ISO-SCOPE]`**: no shard touches another ISO's keeper shard, matrix shard, status part
  or calibration log.
* Every shard merges `origin/main` before pushing and resolves **only in its own files**.

---

## §6 — CONTAINER PREP. Front-load this or you will burn four launches on it.

caiso-268 lost ~20 minutes to four sequential cold-start failures. Put this verbatim in every shard
prompt that runs an LP:

```bash
python3 scripts/hydrate_data.py --profile <PROFILE>
python3 scripts/prepare_solve_container.py            # provisions the 8 GiB swap — do NOT skip
eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"

# pinned to the keeper's meta.json "environment" block — read it, do not copy these blindly
pip install -q highspy==<v> numpy==<v> scipy==<v> pandas==<v> pyarrow==<v> pydantic==<v> pyyaml
pip install -q openpyxl        # eGRID .xlsx sheet reads — the solve dies at fleet build without it
pip install -q tzdata          # zoneinfo has no US/Pacific etc. in this image

PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py
```

**That last line is the one people miss.** `data/clean/` is derived and gitignored, so a fresh
container starts empty and the solve **hard-fails by design** (`DegradedInputError`) rather than
silently re-arming a retired fitted scalar — the caiso-157 / caiso-188 guard doing its job. If the
recipe arms `capacity_deliverability_limits`, rebuild the partition first.
`python scripts/regenerate_clean.py` rebuilds the whole tree if you need more than one partition.

---

## §7 — GOVERNANCE EVERY SHARD CARRIES

* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 is training tier and needs nothing. **Any other year needs
  that year's marker** in `calibration-complete.json` (`complete` for 2020–2022, `final` for
  2019 / H1-2026) **at launch AND again at registration** (owner ruling R-AZ). If a shard thinks it
  needs a holdout year, it **stops and asks**. No shard grants itself one.
* **Rule 29 `[R-SCREEN]`** — zero-LP phase 0 first; screen year named in the PRECOMMIT **before** the
  screen runs, chosen on the mechanism's **own measured footprint**, never on the residual. Gates are
  **STOP-ONLY**: they may kill an arm, never promote one, and none may read the target residual.
* **Rule 29(b) G-CTRL form 4** — the incumbent keeper's committed bundle is the control and **no
  control solve is spent**, but only after a **G-DRIFT** audit classifies every changed hunk on the
  backcast path INERT-with-reason or LIVE, pushed **before the first LP**. Two cheap corroborations
  worth doing every time: check the keeper's `git_sha` actually resolves (one CAISO keeper's did
  not), and recompute the ISO's capx-D79 **solve-surface fingerprint** at HEAD against the block the
  keeper recorded — an exact match is stronger evidence than a control solve and costs seconds.
* **Rule 15 `[R-DASHBOARD]`** — the SPAN bundle is registered **whatever it says**, keeper or
  rejection, **in the session that produced it**. Per-year probes are never registered.
* **Rule 27 `[R-PUSH]`** — the run payload (~400 KB–1 MB) exceeds `push_files`' ~457 KB cap, so it
  goes over `git push`; a sidecar pushed without its payload is **silently invisible** in the Run
  Explorer. After any push touching a file ≥300 lines, **fetch the blob back and compare line count +
  hash** before doing anything else. On HTTP 408/500 set `git config http.version HTTP/1.1` and retry
  **before** concluding anything about pack size.
* **Rule 31 `[R-RETAIN]`** — **NEVER `rm -rf` a bundle.** `.gitignore` is what discharges
  delete-before-merge; `rm` is not. Nothing is deleted until the owner has ruled on promotion.
* **Rule 28 `[R-MECH-MATRIX]`** — the SPAN shard alone updates the mechanism's cell in **its own
  ISO's** shard, in the same session, rejections included.

---

## §8 — HOW YOU REPORT OUT

**While shards are in flight**, every message you send the owner leads with the board — nothing else
above it:

```
SHARD STATUS
  Y2023   2  — LP on P1, ~8 min in, branch claude/<sess>-y2023 @ a1b2c3d
  Y2024   2  — DEAD at clone (ref_not_found), relaunched 16:412 on sha 3ac68ff
  Y2025   1  — solved, gates PASS, RESULT pushed, branch landed
  SPAN    2  — 2024 of 3 solving, branch claude/<sess>-span @ e4f5a6b
  LAUNCHER 2 — polling; next sweep 16:55
```

Then, and only then, whatever else you have to say.

**Poll until every shard reads 1.** A shard reaching 1 gets `archive_session` — that is what the code
means and it is the point of having it. **Report 1 for yourself last**, and only when: the SPAN
bundle is registered and pushed, its RESULT doc is pushed, the matrix cell and calibration log are
updated, every blob ≥300 lines is verified, every child session is archived, and the promotion
question below has been put.

**Then close with the promotion question — separately from the board**, because it is a different
question and must not be answered with the same digit:

> **PROMOTION (rule 31 `[R-RETAIN]`, put explicitly).** The bundle is on local disk in an
> **ephemeral container and will not survive this session**; its committed slim set is pushed, so a
> promotion needs **no re-solve** — only the gitignored `dispatch/` parquets go with the container.
> **(a) promote** / **(b) do not promote** / **(c) something else**. My recommendation is \<one
> line, with the structural reason, not the scorecard\>. I have not promoted it and will not without
> an explicit ruling; and I will not re-cut the parameter to make a gate pass — that is the
> fitted-mechanism selection rule 1 `[R-STRUCT]` condition (c) forbids.

**Never let the session end with an unasked promotion question or a shard on 2.**

---

## §9 — THE FAILURE THIS PROTOCOL EXISTS TO PREVENT, STATED ONCE

caiso-268 launched four shards. One — the SPAN — did its job. The other three were reported as
launched and **were never checked again**. At the end the span shard ran `git branch -r | grep
caiso268` and found **only its own branch**. Three containers' worth of LP were spent on nothing, and
the cross-check the charter asked for could not be performed. **Nobody was lying; nobody had looked.**

§4 is the entire remedy: **a branch on the remote, or it is a 2.**
