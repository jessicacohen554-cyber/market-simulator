# Infrastructure gap — dashboard run payloads cannot traverse the API-only push path, and six runs are already silently stranded

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
chosen below.

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
the CI gate that used to enforce this was removed 2026-07-14.
