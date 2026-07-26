# Infrastructure gap — dashboard run payloads cannot traverse the API-only push path, and six runs are already silently stranded

> **STATUS 2026-07-26: option 1 ADOPTED — rule amended, policy gap closed;
> the stranded set is NOT backfillable and is now tracked.** See the
> "2026-07-26 resolution" section at the bottom. The text above it is the
> 2026-07-25 record, kept as written.

**Found 2026-07-25 during the caiso-119 session, while registering a probe run.**
Not a modelling issue; an infrastructure/governance one. Needs an owner decision.

## The gap

`CLAUDE.md` → "Git & Pushing (API-only — never `git push`)" mandates
`mcp__github__push_files` for every commit, because `git push` over this remote
rejects large packs with HTTP 413.

`mcp__github__push_files` takes file **content inline in the tool call**. A
backcast run payload — `frontend/data/backcast/runs/<id>.js` — is a single-line
base64-gzip blob:

```
window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};
window.BC.runGz["<id>"]="H4sIAAAAAAACA+y9a3faOtQu+lcy3q+rm2XA3PY3G5s7JOaSlp5xxhlt0kBCWtrSLiB77P9+JPkmG0sCjA…"
```

Typical size **~400 KB–1 MB** (the 60 currently-tracked payloads total ~51.6 MB;
the caiso-119 one is 434,784 bytes). That is far past what an agent can emit in a
single tool call, so **the mandated push path has no viable route for a run
payload.**

## Consequence — it is failing silently, and has been

The `calibration-report` skill warns: never push a sidecar without its payload,
because `build_manifest.py` skips a payload-less sidecar **silently** (no error,
no warning) — the run is on record but permanently invisible in the Run Explorer.

That is exactly what the gap produces, because the sidecar (669 bytes) pushes
fine while the payload does not. Current state on `main`:

| run | sidecar tracked | payload tracked |
|---|---|---|
| `2026-07-22-caiso-112-export-floor` | yes | **no** |
| `2026-07-23-caiso-114-endogenous-west` | yes | **no** |
| `2026-07-23-neiso-2022-holdout-validation` | yes | **no** |
| `2026-07-23-pjm-116-netrev-base` | yes | **no** |
| `2026-07-23-pjm-117-netrev-margin` | yes | **no** |
| `2026-07-24-pjm-118-netrev-level` | yes | **no** |

Reproduce with `python scripts/check_registry_payload_parity.py` (it reports all
six, plus the keeper line below).

**`2026-07-24-pjm-118-netrev-level` is the current PJM keeper**
(`frontend/data/backcast/keepers/PJM.json`), so the live PJM keeper's run report
does not render. The parity checker says so explicitly:

```
keepers/PJM.json: keeper '2026-07-24-pjm-118-netrev-level' has no
                  runs/2026-07-24-pjm-118-netrev-level.js payload
```

This also means rule 15 ("a run is not done until its bundle and dashboard files
are committed and pushed") is currently unsatisfiable for any new run by an
agent following the API-only rule.

## RESOLVED for caiso-119 — `git push` works at this size (measured 2026-07-25)

**Owner authorized `git push` for this case, and it succeeded with no 413.** The
434,784-byte payload pushed cleanly; the remote blob sha matches the local one
byte-for-byte (`be4ed6a318b8ab9c1576149508e4126e28d94fc9`), and
`2026-07-24-caiso-119-minload-measured` renders in the Run Explorer.

So **option 1 below is confirmed, not merely plausible**: the HTTP 413 applies to
large *packs*, not to a single ~400 KB blob. A dashboard registration pushed as
its own small commit on an up-to-date base is well inside the limit.

Caveat on what was actually measured: one ~434 KB payload in a commit whose other
files are small text, pushed onto a freshly-fetched base so the pack carried only
this session's objects. It does NOT license `git push` for a bundle directory
(`caiso119_base_A` alone is 120 MB of parquet/npz) or for a divergent branch that
would pack hundreds of megabytes. The rule's original rationale still holds there.

## caiso-119 status (why this note exists)

The caiso-119 probe `2026-07-24-caiso-119-minload-measured` is registered and
committed **locally** (sidecar + 434 KB payload + refreshed manifest + the
automatic top-15 CAISO prune). It was deliberately **not** pushed sidecar-only —
that would have made it a seventh invisible run. It awaits whichever remedy is
chosen below. *(2026-07-26: resolved — the 434,784 B payload is on main and
the run renders.)*

## Options for the owner

1. **Carve out `git push` for `frontend/data/backcast/runs/`.** ✅ **MEASURED AND
   WORKING** (see above) — a 434 KB payload pushed with no 413. The cheapest fix,
   and now the recommended one: amend the CLAUDE.md "API-only" rule to permit
   `git push` for dashboard registration commits specifically, keeping the API
   path for everything else.
2. **Let the Pages deploy regenerate payloads**, as it already regenerates
   `manifest.js`/`benchmark.js`/`completeness.js` from the sidecars. Payloads are
   a pure function of the bundle (`scripts/render_backcast.py`), so this is
   structurally the same move — but it requires the deploy to see the bundles,
   which the current sparse checkout does not fetch.
3. **Chunked append.** Rule 27 already contemplates moving a large file "in
   pieces… append chunks across multiple commits and verify the blob after each".
   Workable today with no infrastructure change, but costs ~8 pushes and a very
   large token budget per run — bad as a standing workflow.

Whatever is chosen, **backfilling the six stranded payloads should come with it**,
starting with the PJM keeper. They regenerate from their bundles without a
re-solve via `scripts/regen_dashboard.py`.

## Guardrail until it is fixed

Do **not** push a registry sidecar whose payload you cannot push in the same
commit. A payload-less sidecar is worse than an unregistered run: it looks
registered, passes every gate that reads the registry, and is invisible to the
only surface that matters. Run
`python scripts/check_registry_payload_parity.py` before every dashboard push —
the CI gate that used to enforce this was removed 2026-07-14. *(2026-07-26:
the gate was in fact restored 2026-07-20 inside the durable `ci.yml`
quarantine-gates job and is verified wired at HEAD — see the resolution
section below.)*

## 2026-07-26 resolution — option 1 ADOPTED; backfill blocked; stranded set tracked

**Option 1 is ADOPTED** (owner approval relayed in the session brief).
CLAUDE.md's "Git & Pushing" section was rewritten in this lane (branch
`claude/market-sim-payload-backfill-edl64j`, commit `5bcc59d`, base
`origin/main` @ `19b0b91`): the API-only mandate is lifted, the transport is
chosen by **pack** size, `git push` is the required transport for run
payloads, `push_files` stays preferred for small multi-file commits with its
~457 KB per-payload cap documented, and rule 27 blob verification explicitly
covers both transports. `git push` remains not licensed for bundle
directories or divergent hundreds-of-MB packs.

### The gap grew while the rule stood

Six stranded runs above (2026-07-25) → **nine** at main `19b0b91`
(2026-07-26): the three new casualties are `2026-07-24-neiso-62-opcap-a0`,
`2026-07-24-neiso-62-opcap-a1`, and `2026-07-24-pjm-119-overlay-restore` —
the last was the PJM keeper from its 2026-07-24 promotion until the
2026-07-25 `pjm-121-cc-belt` promotion, i.e. the live PJM keeper's report was
invisible for a day. (The session brief put the count at 11; the measured
value at both `6a65339` and `19b0b91` is 9 — the parity checker's output is
the authority.) No current keeper is payload-less: PJM's keeper is now
`2026-07-25-pjm-121-cc-belt`, whose payload is committed.

### Backfill result: 0 of 9 regenerable — every stranded payload needs a re-solve

The backfill option 1 anticipated ("they regenerate from their bundles
without a re-solve via `scripts/regen_dashboard.py`") is NOT available for
any of the nine. `render_calibration_html.build_payload` (what
`regen_dashboard.py` / `render_backcast.py` run) reads each bundle's
`dispatch/<year>_P*.parquet` + `system.parquet` at render time — gitignored
heavy intermediates (`.gitignore` §8; dispatch alone is ~80 MB/year) that
exist only on the machine that ran the solve. Every originating container is
gone and the remote has no other branches carrying them. Per-run state at
`19b0b91`, verified 2026-07-26:

| run | bundle on main | blocker |
|---|---|---|
| `2026-07-22-caiso-112-export-floor` | `caiso112_export_floor_B` — metrics-only | no `meta.json`, no dispatch/system parquet |
| `2026-07-23-caiso-114-endogenous-west` | `caiso110_endog_B` — metrics-only | same |
| `2026-07-23-neiso-2022-holdout-validation` | `neiso_2022_holdout_validation` — metrics-only | same |
| `2026-07-23-pjm-116-netrev-base` | `pjm_netrev_base` — ABSENT, 0 commits | bundle never pushed |
| `2026-07-23-pjm-117-netrev-margin` | `pjm_netrev_margin` — ABSENT, 0 commits | bundle never pushed |
| `2026-07-24-neiso-62-opcap-a0` | `neiso_opcap_a0` — ABSENT, 0 commits | bundle never pushed |
| `2026-07-24-neiso-62-opcap-a1` | `neiso_opcap_a1` — ABSENT, 0 commits | bundle never pushed |
| `2026-07-24-pjm-118-netrev-level` | `pjm_netrev_retune` — slim | no dispatch/system parquet |
| `2026-07-24-pjm-119-overlay-restore` | `pjm119_overlay_restore` — slim | no dispatch/system parquet |

Re-solves are out of scope for the no-solve session that closed this note, so
the nine ids are tracked in
`scripts/lib/known_unsynced_keepers.py::UNSYNCED_RUN_PAYLOADS` (the
CI-restoration precedent): `check_registry_payload_parity.py` reports them as
explicit warnings and exits 0, and any NEW sidecar-without-payload still
fails loudly.

Per-id resolution, owner's choice per run: **(a)** re-solve the full rule-16
year span in a solve-capable session, re-register via `calibration-report`,
push the payload over `git push`, and delete the id from the tracked set; or
**(b)** for superseded probes (the pjm-116/117/118/119 netrev lineage is
superseded by the all-pass pjm-121 keeper), prune the sidecar via
`dashboard_add_run.py`'s three-store retention. The NEISO 2022 holdout
validation run carries governance weight (rule 22 validation tier); if
re-solved it needs `--holdout-authorized` and a session log entry.

### Owner decisions (2026-07-26, same session)

- **PRUNED (8):** the pjm netrev lineage (pjm-116, pjm-117, pjm-118,
  pjm-119 — superseded by pjm-121) and the four probes (caiso-112,
  caiso-114, neiso-62-opcap-a0, neiso-62-opcap-a1). Sidecars deleted plus
  their four surviving bundle dirs (`caiso112_export_floor_B`,
  `caiso110_endog_B`, `pjm_netrev_retune`, `pjm119_overlay_restore`),
  mirroring the three-store retention semantics — verified first that no
  payload ever existed, no bundle is shared by another registration, and
  none of the ids is in `_protected_run_ids()`. Their adjudications remain
  in the FINDING docs and per-ISO calibration logs.
- **AUTHORIZED:** a NEISO 2022 re-solve of
  `2026-07-23-neiso-2022-holdout-validation` (`--holdout-authorized`,
  rule 22 validation tier — this entry is the session log of that
  authorization). It stays the SINGLE tracked id in
  `known_unsynced_keepers.py` until its payload lands; parity now reads
  "OK (70 runs checked, 1 known-unsynced tolerated)".

### Pack-size measurements (2026-07-26)

No 413 was hit and no ceiling was found this session — its pushes were
KB-scale packs on freshly-fetched bases. Two size facts extend the original
434,784 B measurement:

- The largest single-blob payload on main is now **1,993,945 B**
  (`runs/2026-07-25-pjm-121-cc-belt.js`, commit `e19ed03`, PR #2905, in the
  same commit as a ~607 KB bench part) — ~4.6× this note's original
  measurement. `push_files`' per-payload cap cannot have carried that file,
  and no 413 is on record for it.
- The full-bundle / divergent-branch negative case remains unmeasured and
  unlicensed; nothing here tests it.

### CI gate — verified re-armed, nothing to wire

`check_registry_payload_parity` runs in `.github/workflows/ci.yml`
(quarantine-gates job) on every PR touching the gated paths, tolerating only
the tracked known-unsynced ids. The gate was restored 2026-07-20 with ci.yml
itself (the 2026-07-14 removal was the wholesale workflow sweep); verified
wired at `19b0b91` — no change needed.
