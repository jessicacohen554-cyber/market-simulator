# FINDING nyiso-148 — NYISO's committed benchmark part is STALE, and regenerating it flips EVERY registered NYISO run to NOT-YET

**Severity: STOP-THE-LINE. This outranks the session's own lane and is escalated
to the owner rather than resolved here.** Nothing about the model changed; what
changed is the **benchmark the model is scored against**. No determination has
been written anywhere: `calibration-complete.json`, the keeper shard and
`status/NYISO.js` are **untouched** and still read CALIBRATED.

---

## 1. WHAT HAPPENED

`frontend/data/backcast/bench/NYISO/{2023,2024,2025}.json.gz` — the per-(ISO,
year) benchmark parts every NYISO run is scored against — had **not changed
since 2026-08-17** (commit `d985fca`). This session was the first NYISO
registration since then whose bundle carried the benchmark inputs
(`run_calibration_full.py --rebuild-benchmark`, run so `dashboard_add_run.py`
could score at all), so it was the first to **regenerate** the part.

The regenerated part differs materially, and on the regenerated part **every
registered NYISO run flips to `NOT-YET`**:

| run | determination on the 2026-08-17 part | on the regenerated part |
|---|---|---|
| `2026-08-19-nyiso-146c-state-scoped` **(THE KEEPER)** | **CALIBRATED** | **NOT-YET** |
| `2026-08-18-nyiso-144-layup-exclusion` | CALIBRATED | NOT-YET |
| `2026-08-18-nyiso-143-n11tsl-arm` | CALIBRATED | NOT-YET |
| `2026-08-17-nyiso-142-stackdup` | CALIBRATED | NOT-YET |
| `2026-08-19-nyiso-146-control` | — | NOT-YET |

In every case the single new failure is the same one: **C1-2024 `CC_REGULAR`**.
For the keeper it reads **+5.18 TWh, share +4.5 pp** against a ±3 pp share band
(the TWh leg still passes at +5.18 of ±3.98… it does not — both legs fail).

## 2. IT IS NOT CAUSED BY ANYTHING THIS SESSION ARMED — measured, not argued

The obvious suspect is `nyiso_chp_btm_measured`, which nyiso-147 disclosed as
changing the benchmark's `classFull` subtrahend. **It is not the cause.** The
bench part was rebuilt at this HEAD twice, once with the flag ON and once with
it OFF (a scratch copy of the same bundle with the meta flag flipped, registered
into a temporary id and deleted afterwards). The two are **identical on
`classFull` to the last decimal in all three years**:

| 2024 classFull | 2026-08-17 part | HEAD, flag OFF | HEAD, flag ON |
|---|---|---|---|
| CC_REGULAR | 38.039 | **34.060** | **34.060** |
| CC_CHP | 13.471 | **17.017** | **17.017** |
| ST_GAS | 11.071 | **9.913** | **9.913** |
| CT_PEAKER | 2.134 | **1.911** | **1.911** |

The whole delta is **2026-08-17 → HEAD drift**, and none of it is the flag.

## 3. WHERE THE DELTA LIVES — the vintage-reconciliation layer, not the meters

The two parts' per-plant `plants` rows are **identical except for two fields**:
the measured BTM values for Sithe Independence (2.1553 → 0.0) and Empire
(1.012 → 0.0058). Recomputing `classFull` as `Σ (e_ann − btm)` over those rows
gives the **same** answer in both parts:

| 2024 CC_REGULAR | Σ per-plant (e_ann − btm) | declared classFull | implied backfill |
|---|---|---|---|
| 2026-08-17 part | 30.040 | 38.039 | **+8.00** |
| HEAD part | 30.040 | 34.060 | **+4.02** |

So the per-plant meters agree and the **~4 TWh moves entirely inside the
benchmark's EIA-923 vintage-reconciliation / CAMPD-backfill layer**
(`_benchmark_eia923_frame` / `_backfill_eia923_with_campd`). The same pattern
holds for CC_CHP (backfill +1.48 → +0.06) and, smaller, for ST_GAS, CT_PEAKER,
CT_CHP and ST_CHP. The raw EIA-923 parquet on disk is unchanged since
2026-08-17 (`git log` on
`data/raw/_processed-legacy/eia923_monthly_generation.parquet`).

**What this session did NOT establish:** which commit between 2026-08-17 and
HEAD moved the backfill, and whether the new value or the old one is the
correct reconciliation. That is the root-cause question, and it is deliberately
left open rather than guessed at.

## 4. WHY THIS MATTERS BEYOND ONE KEEPER

* **A C1 verdict is not reproducible from a bundle alone.** It depends on which
  run last supplied the shared per-(ISO, year) bench part, and that part is
  refreshed only when a registering bundle happens to carry benchmark inputs.
  Two sessions registering the same bundle in different orders can score it
  differently.
* **The staleness is silent.** Nothing warns that a part predates the builder
  that would produce it. The parts are described as "byte-deterministic … they
  only show up in `git status` when the benchmark genuinely changed", which is
  true — but it also means a part can sit un-refreshed for weeks while the
  builder moves underneath it.
* **It is probably not NYISO-only.** The mechanism — a shared bench part
  refreshed opportunistically — is ISO-agnostic. This session measured **only
  NYISO** and asserts nothing about the other five (rule 25); checking them is
  part of the escalation, not part of this finding.

## 5. WHAT THIS SESSION DID, AND DELIBERATELY DID NOT DO

**Did:**
* Kept the regenerated bench part committed. Rule 14 `[R-ACCURATE]`: a worse fit
  after an input is refreshed is a discovered bug, and reverting to the stale
  part would bury the error back inside an inaccurate input.
* Measured the flag-independence (§2) and localized the delta (§3).
* Corrected this session's own affected claims — `ASSESSMENT-nyiso148-frontier`
  §1 and `RESULT-nyiso148-chp-layup-duty` D-K5 — rather than leaving them
  standing on a superseded benchmark.

**Did NOT:**
* **Write any determination anywhere.** Rule 22 D-5(b): a re-verified
  determination that is worse **stops and escalates to the owner; it is never
  silently written**. `calibration-complete.json`, `keepers/NYISO.json` and
  `status/NYISO.js` are byte-untouched and still assert CALIBRATED.
* Revert the bench to hide the discrepancy.
* Promote, demote, or re-key anything.
* Guess at the root cause or "fix" the backfill.

**Consequence, stated plainly:** `scripts/audit_keepers.py --iso NYISO` now
FAILS with three findings (E5 sidecar text, M1b marker determination, S1 stale
status) because the recorded text asserts CALIBRATED while the live verdict
reads NOT-YET. **That failure is TRUE and is the intended signal.** It must be
resolved by the owner's ruling on §6, not by editing the text to match.

## 6. THE ESCALATION — what the owner is asked to rule

1. **Which benchmark is authoritative** for NYISO 2023–2025: the regenerated one
   (what today's builder produces from today's data) or the 2026-08-17 one that
   every current keeper text was written against?
2. **If the regenerated one:** NYISO's keeper determination becomes NOT-YET on
   C1-2024 `CC_REGULAR` and the lane needs a re-calibration charter. The
   `complete` marker's authorization would also need re-examination, since it
   asserts a determination that no longer holds.
3. **Root cause:** which change between 2026-08-17 and HEAD moved the
   EIA-923 backfill by ~4 TWh on CC_REGULAR-2024, and is the new reconciliation
   right? This is a lane-sized investigation and should be chartered before any
   re-calibration, so the lane is not tuned against a moving target.
4. **Cross-ISO:** the same opportunistic-refresh mechanism exists for every ISO.
   A sweep — regenerate each ISO's bench part at HEAD and re-score its keeper,
   **without committing** — would size the exposure. This session did not run it
   (rule 25: NYISO lane files only).

## 7. REPRODUCTION

```
# the regenerated part is committed at HEAD; the stale one is on origin/main
git show origin/main:frontend/data/backcast/bench/NYISO/2024.json.gz > /tmp/old.gz
python - <<'PY'
import gzip, json
old = json.loads(gzip.decompress(open('/tmp/old.gz','rb').read()))['bench']['classFull']
new = json.loads(gzip.decompress(open('frontend/data/backcast/bench/NYISO/2024.json.gz','rb').read()))['bench']['classFull']
print({k: (old[k], new[k]) for k in ('CC_REGULAR','CC_CHP','ST_GAS')})
PY
python scripts/calibration_verdict.py --run-id 2026-08-19-nyiso-146c-state-scoped
python scripts/audit_keepers.py --iso NYISO
```

---

# ADDENDUM — the owner's ruling, the cross-ISO sweep, and the mechanism fix

**Owner ruling, 2026-08-21 (session nyiso-148, `AskUserQuestion`):**

1. **"Regenerated is authoritative."** The regenerated benchmark stands; NYISO's
   keeper determination becomes NOT-YET; the root cause is chartered *before*
   any re-calibration so the lane is not tuned against a moving target.
2. **"Sweep and fix the mechanism."** Size the exposure across all six ISOs
   **and** change the refresh rule so a bench part can never silently outlive
   the builder that produced it.

Both are executed below. §§1–5 above are unchanged.

## 8. THE RULING, LANDED

The determination was written into exactly the three places that asserted the
superseded one, and nowhere else (commit `3e69981`):

* `frontend/data/backcast/registry/2026-08-19-nyiso-146c-state-scoped.json` —
  the promoted determination restated as prose, the live **NOT-YET** recorded
  with its cause.
* `frontend/data/backcast/calibration-complete.json` — `complete.NYISO.determination`
  restated; the prior value preserved in `determination_at_prior_rekey`; a new
  `marker_reexamination_open` field records the second thing the ruling opened —
  **whether validation-tier authorization should survive a NOT-YET
  determination**. The marker is deliberately **left in place**, not withdrawn:
  withdrawal is a separate owner decision, and it authorizes nothing spendable
  today because the holdout spend freeze outranks every marker.
* `frontend/data/backcast/status/NYISO.js` — rebuilt; reads NOT-YET.

**The run remains NYISO's designated keeper.** It is still the most structurally
faithful NYISO run and no successor exists; it is now a NOT-YET keeper.
`audit_keepers --iso NYISO` passes 0/0 again.

## 9. THE SWEEP — five of six ISOs are exposed

Probe `scripts/probes/_nyiso148_bench_staleness_sweep.py`; record
`_nyiso148_bench_staleness_sweep.json`. **Read-only** — nothing regenerated,
nothing committed.

A faithful regeneration of every ISO's part would need each ISO's raw data
hydrated and a bundle carrying benchmark inputs — hours of solve for a sizing
question, and this session holds the `nyiso` data profile. The sweep instead
measures the exposure at the resolution git already carries: **a part is
POTENTIALLY STALE iff the code that produces it changed after the part was last
written.** That is an **upper bound**, and it is reported as one.

| ISO | part last written | builder-script commits since | engine commits since | verdict |
|---|---|---:|---:|---|
| **NYISO** | **2026-08-21** | 0 | 0 | **current** (regenerated this session) |
| CAISO | 2026-08-17 | 0 ungated | **22** | POTENTIALLY STALE |
| ERCOT | 2026-08-17 | 0 ungated | **22** | POTENTIALLY STALE |
| MISO | 2026-08-17 | 0 ungated | **22** | POTENTIALLY STALE |
| NEISO | 2026-08-17 | 0 ungated | **22** | POTENTIALLY STALE |
| PJM | 2026-08-17 | 0 ungated | **22** | POTENTIALLY STALE |

**Five of six ISOs sit on parts that predate 22 engine commits.** Only NYISO is
confirmed by actual regeneration.

Two refinements that keep the bound honest rather than alarmist:

* **The one builder-script commit since 2026-08-17 is provably gated and is
  annotated as such.** `01db36d` (nyiso-147) changes `_btm_share` only behind
  `meta["nyiso_chp_btm_measured"] and meta["iso"] == "NYISO"`, so it can move
  NYISO's two measured-BTM per-plant fields and nothing else. **It explains
  neither the ~4 TWh NYISO `classFull` drift nor any non-NYISO part** — which is
  why the root cause in §6 item 3 stays OPEN and is not pinned on it.
* **The exposure is carried by the ENGINE, not the scripts.** The builder
  imports `src/market_sim/` for the plant→class map, the CHP shares and the
  EIA-923 reconciliation. That is consistent with §3, which localized NYISO's
  delta to the vintage-reconciliation/backfill layer rather than to the meters.

## 10. THE FIX — a content-derived stamp, a checker, and a loud scorer alarm

Three pieces, designed so the signal survives being useful:

**(a) `scripts/lib/bench_stamp.py` — the fingerprint.** Every part now carries
`meta.builderFingerprint`, a hash over the source of the scripts that compute
and write it. **Content-derived only**: a timestamp or a HEAD sha would rewrite
every part on every registration and destroy the byte-determinism that keeps
concurrent registrations conflict-free — the very property that let the
staleness hide. Same code + same data ⇒ same bytes, and the stamp is verified
to move **nothing else**: re-rendering NYISO's parts through the stamped writer
left `classFull` identical in all three years.

**(b) `scripts/check_bench_freshness.py` — the gate, in two tiers.**
*HARD (exit 1)*: the part's fingerprint differs from HEAD's, or is absent
(predating the stamp) — the part provably was not written by the builder that
would run now. *SOFT (reported, never gates)*: the fingerprint matches but
engine commits have landed since the part was committed. The split is
deliberate — folding the engine into the hash would mark every part stale after
any lane's edit, and a signal that always fires is a signal nobody reads.

**(c) The scorer says so out loud.** `calibration_verdict.py` now prints a
`[!] STALE BENCHMARK` line to stderr, naming the parts and the fix, whenever it
scores a run against a part the builder at HEAD did not write. It **warns and
never fails** — the scorer's job is to report what the committed artifacts say;
(b) is the gate. Verified in both directions: silent on NYISO (fresh), loud on
PJM (stale), and the verdict itself is untouched.

**What is deliberately NOT done: the checker is NOT wired into CI as a hard gate
in this session.** Nineteen of twenty committed parts are stale right now, so
gating would red-light every PR in the repo for defects that only each ISO's own
lane can fix (regenerating a part needs that ISO's data and a bundle). The
sequence has to be: each ISO regenerates its part and re-verifies its keeper,
*then* the gate goes on. Wiring it in is the owner's call once that is done, and
it is one line in the existing CI checks job.

## 11. WHAT REMAINS OPEN AFTER THIS SESSION

1. **Root cause** — which change moved the EIA-923 backfill (CC_REGULAR-2024
   +8.00 → +4.02 TWh), and which reconciliation is correct. Chartered **before**
   NYISO re-calibration. Not pinned on `01db36d`, which §9 rules out.
2. **Five ISOs to regenerate and re-verify** — CAISO, ERCOT, MISO, NEISO, PJM,
   each in its own lane with its own data (rule 25), each ending in a keeper
   re-verification like NYISO's.
3. **Turn on the gate** once (2) is done.
4. **NYISO's `complete` marker** — whether validation-tier authorization
   survives a NOT-YET determination (`marker_reexamination_open`).

---

# ADDENDUM 2 (nyiso-149, 2026-08-22) — §11 item 1 is RESOLVED, and two of this finding's inferences are corrected

The chartered root-cause session landed
(`FINDING-nyiso149-bench-root-cause-2026-08-22.md`, evidence record
`_nyiso149_bench_reconcile_closure.json`). Both parts reconstruct EXACTLY, every
gas/coal class, all three years, from ONE shared e923 frame. What it changes in
THIS document's record:

* **§2's conclusion ("none of it is the flag") is WITHDRAWN.** The drift IS
  `01db36d`'s flag, through the one channel §2's test could not see:
  `rebuild_benchmark` does not rebuild `btm.parquet`, so both scratch rebuilds
  shared the armD bundle's flag-ON btm frame. The flag's benchmark channel is
  the btm subtrahend; holding it fixed made flag-on and flag-off render
  identically. §9's `01db36d` gated-note ("cannot … touch the classFull
  reconciliation layer") is wrong at one remove for the same reason: the commit
  never touches the reconcile code — it moves the reconcile's INPUT across the
  ±3% deadband (sector carve: gas family −10.5% vs EIA-930 → scaled ×1.117;
  measured: −2.7% → in deadband, no scale; 2024 figures).
* **§3's localization ("the ~4 TWh moves entirely inside the … backfill
  layer") was a residual attribution, not a measurement of that layer.** The
  benchmark EIA-923 frame is hash-identical across the whole window
  (`920c8b8bc1b1`, the shared-input name every registered NYISO bundle meta
  declares): `_benchmark_eia923_frame` / `_backfill_eia923_with_campd` never
  moved. The "implied backfill" delta is the family reconcile's pro-rata smear
  (+3.98 TWh onto CC_REGULAR-2024) compensating the carve's over-subtraction.
* **§1's "unchanged since 2026-08-17" has a sharper reading**: nyiso-147's
  registration (`d1a298d`, 08-20) re-rendered the flipped parts on its own
  container and committed none of them; this session's registration was the
  first to COMMIT the flip, not the first to produce it.
* **The RULING (owner, Addendum §8) is now grounded in mechanism**: the
  regenerated reconciliation is CORRECT — the measured subtrahend is the
  plants' own meters, and only under it does EIA-923+CAMPD agree with EIA-930
  unscaled — and it is made durable by the nyiso-149 pin (`btm_bench_twh`:
  bench basis measured-when-artifact-exists, flag-independent; run add-back
  basis unchanged), so a future flag-off registration can no longer flip the
  committed parts back. §11 items 2–4 remain open.
