# MISO Phase B — owner manifest & keeper recommendation (2026-07-15)

Session `claude/miso-phase-b-execution`. This is the hand-off: what shipped, the
**keeper recommendation**, the two items that need your call, and exactly what
still needs a disk-reading push (the ephemeral container is reclaimed at session
end, so anything not on the branch or regenerable is lost).

## 1. Keeper recommendation (rule 15 — your call)

**ADOPT the p25 mechanism; HOLD the keeper swap.** miso-67
(`st_gas_mustrun_p25_level`) is the most structurally-faithful MISO ST_GAS
representation to date — the measured VLR *dispatch* level (p25-of-online CF),
not the LSL. Mechanism-only (probe − same-box base) it flips **ST_GAS-2024
FAIL→PASS (+2.28 TWh)**, grounds its forced share (C8, D-1/D-4 clean), and holds
the C3b-2025 veto (0.187 ≤ 0.20). It belongs in the model.

**But two separable issues keep the registered run NOT-YET, and neither is the
mechanism** — so a swap now would put an honest-but-not-improved *determination*
on the keeper:

1. **CC_REGULAR-2023 is a current-main regression.** The same-box base (miso-66
   recipe, current code, p25 OFF) is **14/16** — CC_REGULAR-2023 FAILs (−11.23)
   WITHOUT p25. The registered miso-66 (15/16) was solved at `5c7ed9c`; **293
   `src/scripts/data` files changed** on main since. The current-main MISO base
   has regressed CC_REGULAR-2023; p25's own footprint on it is only −1.04. This
   is its own lane (bisect the 293-file drift), independent of miso-67.
2. **The price-formation lane did not pay off.** The July North-up separation
   miso-67 was hoped to unlock is real but **negligible** (N−S spread 0.33→0.42
   vs the measured ~$21.5; S→N flow +0.1 GW); C3a-2025 actually went −0.47
   (the inframarginal floor lowers the level). C3c is unchanged (needs M-2,
   which is F4-blocked — see §3).

Registering miso-67 records the structural gain honestly without masking either
open item. Promote it once (1) is understood and (2)'s tail is unblocked.

## 2. What is on the branch (pushed via `push_files`)

| item | form | commit |
|---|---|---|
| Issue-1 display fix (wedge + CHP unfold) | patch `01-*.patch` | fd54a20 |
| M-1 F4 findings memo | full doc | f8aecb5 |
| mechanism (scenarios + fleet) | patches `02/03-*.patch` | 6674dab |
| attestation generator | full script `scripts/archive/gen_miso67_attestation.py` | fa40f84 |
| dof-ledger + reserve citation | patches `04/06-*.patch` | fa40f84 |
| per-year+reuse probe | full script `scripts/probes/_miso67_stgas_vlr_level.py` | eb3b1bf |

Apply the source patches to `origin/main`:
`git apply docs/handoffs/miso-phase-b-patches/0{2,3,4,6}-*.patch` (01 is the
site display fix; 05 is the calibration-log entry — see the local combined
patch `00-COMBINED-*.patch` for all of them in one).
(NOTE: the pushed probe script's docstring shows a doubled backslash where a
single line-continuation was intended in the shell-usage example — cosmetic, in
a comment; the script runs correctly.)

## 3. What is NOT on the branch — needs your disk-reading push OR regeneration

The registration DATA is on the container's local disk and **will be lost** when
the session ends. `push_files` cannot carry it (Data-API write is org-403; the
payload is ~1 MB and the bench is binary). Two options:

- **A — push from the container now** (if you can reach it this session): push
  the whole bundle + sidecar + payload + bench via git / a disk-reading uploader:
  - `results/calibration/miso67_stgas_vlr_level/` (slim JSONs; dispatch/parquets
    are gitignored and not needed)
  - `frontend/data/backcast/registry/2026-07-15-miso-67-stgas-p25.json` (sidecar,
    with `market_story`)
  - `frontend/data/backcast/runs/2026-07-15-miso-67-stgas-p25.js` (~1 MB payload)
  - `frontend/data/backcast/bench/MISO/{2023,2024,2025}.json.gz` (only if changed;
    I reverted local bench edits so the committed bench is untouched)
- **B — regenerate** (clean-room): apply the source patches, then run the probe
  driver (per-year+reuse, RAM ≤16 GB — a single 3-year process OOMs):
  ```
  P=scripts/probes/_miso67_stgas_vlr_level.py
  python $P main --out-dir R/y2023 --years 2023
  python $P main --out-dir R/y2024 --years 2023,2024 --reuse-solved R/y2023
  python $P main --out-dir R/final --years 2023,2024,2025 --reuse-solved R/y2024
  python scripts/dashboard_add_run.py --label "miso 67 stgas p25 level" --bundle R/final
  python scripts/build_dof_ledger.py R/final --iso MISO
  python scripts/archive/gen_miso67_attestation.py
  python scripts/legitimacy_diagnostics.py --bundle R/final --iso MISO --json-out R/final/legitimacy_diagnostics.json
  ```
  KEEP THE WORKING TREE CLEAN during the solve — an untracked file poisons the
  prior bundle's whole-tree `git.dirty` flag and `--reuse-solved` refuses,
  forcing a 3-year OOM (gitignore any transient output dirs).

## 4. M-1 / M-2 / composed probe — F4 deferred (access item, not a knob)

The max-gen event registry cannot be authoritatively built this session:
**OASIS `Capacity_Emergency_Historical_Information.pdf` is proxy-unreachable
(502); `cdn.misoenergy.org` is 403**; and the **2024 MISO SOM (primary) says no
emergency was declared in Jan 2024** (Winter Storm Heather), contradicting the
design's assumed Jan-2024 window (the arctic-blast Max Gen Emergency is
Jan-24-**2026**, out of window). Per the pre-declared F4 discipline, M-2 + the
composed probe are deferred, not force-built. **To unblock:** allowlist
`oasis.oati.com` / `cdn.misoenergy.org` or drop the primary MISO
emergency-declaration decks into `data/raw/miso-maxgen-events/`, then
re-adjudicate the Jan-2024 window. Full detail:
`docs/handoffs/miso-phase-b-m1-maxgen-findings-2026-07.md`.

## 5. Verification done this session

- Issue-1: recompute from committed payload/bench reproduces the triage table
  exactly (wedge +24.6/+20.5/+5.0); node render confirms header + CHP sub-rows;
  the pushed patch fetch-backs byte-identical and applies to the exact hash.
- miso-67 mechanism: 9 unit tests (off-state byte identity, cheapest-first,
  pmax×availability clip, never-pins) + 149-test fleet regression, all green;
  off-state provably byte-identical.
- Probe: 6 solves (base + main × 3 years), per-year+reuse, all clean-tree.
- Registration: DOF 20/2, C8 grounded-PASS, parity OK, manifest rebuilt.

## 6. Open lanes handed off

1. **CC_REGULAR-2023 current-main regression** (bisect the 293-file drift since
   `5c7ed9c`; the MISO base is 14/16 on current main).
2. **Price-formation lane** (the S→N separation channel is too weak; the tail is
   F4-blocked on the OASIS registry) — needs §4 unblocked, then M-2 + composed.
3. **Local commit authors** were `fawkesjosi@gmail.com` (they never git-pushed;
   the branch's actual commits are `push_files`-authored `noreply@anthropic.com`).
