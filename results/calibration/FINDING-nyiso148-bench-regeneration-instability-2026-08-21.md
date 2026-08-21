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
