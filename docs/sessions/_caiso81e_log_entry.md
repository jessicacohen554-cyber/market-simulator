### 2026-07-13 — NYISO + NEISO — nyiso-62 / neiso-59 (fleet_to_bins CC-HR re-gate, caiso-78 blast radius): keeper recipes re-solved VERBATIM on the fixed base_hr — NYISO C3a+C3b CAVEAT→PASS (target grade 6→8), NEISO C2 CAVEAT→PASS (7→8), zero fails — **both PROMOTED to keeper** (caiso-78 precedent: same rule-14 code fix, LOYO-exempt); PJM leg (pjm-106) re-running on a swap-enabled runner after a 7 GB runner OOM

The caiso-78 entry flagged the PJM/NYISO/NEISO keepers "must re-gate on the
fixed code ... not silently re-solved" — they were solved while
`fleet_to_bins` deflated every CC plant's base heat rate by its own
net-summer/nameplate ratio (under `cc_nameplate_summer_derate`, ON for all
three). This is that follow-up (caiso-81 session, lane E): each keeper
recipe re-solved VERBATIM via `replay_keeper.build_kwargs` off its
`meta.json` (`scripts/probes/_fleet_to_bins_regate.py`) plus a fresh
zero-forcing twin (rebuilt canonically from the keeper meta — the old twins'
metas do not record the ablation kwargs), registered as NEW probe pairs so
the A/B vs the committed keepers stays on record. Zero recipe changes, zero
new parameters; LOYO-exempt per the caiso-78 precedent (code-level,
year-invariant measured-input correction).

- **nyiso-62** (`2026-07-13-nyiso-62-cc-hr` + twin) vs the nyiso-61 keeper:
  **C3a mean-LMP CAVEAT→PASS, C3b price-shape CAVEAT→PASS** (the corrected
  within-CC merit order fixes the price formation the deflated HRs were
  scrambling); C1/C2/C4 PASS hold, C5a CAVEAT holds, protectives hold
  (C8 note: 2024 ST_GAS grounded-above-budget 39.6 % — the same grounded
  pass the keeper carried at 32.1 %). Target grade 6→8 (of 10 scored),
  ledgered 3→1, fails 0. Determination CALIBRATED-WITH-CAVEATS (unchanged).
- **neiso-59** (`2026-07-13-neiso-59-cc-hr` + twin) vs the neiso-56 keeper:
  **C2 sysvol CAVEAT→PASS** (partly the v2.5 preliminary-family re-score);
  all other statuses hold, fails 0. Target grade 7→8, commercial-band 1→0.
  Determination CALIBRATED-WITH-CAVEATS (unchanged).
- **PROMOTED (this entry): keepers** `2026-07-11-nyiso-61-downstate-import`
  → `2026-07-13-nyiso-62-cc-hr` and `2026-07-09-neiso-56-reserve-coopt` →
  `2026-07-13-neiso-59-cc-hr`. Rule-1 basis identical to the caiso-78
  promotion: of two same-recipe runs, the one on the corrected measured HR
  basis is strictly more structurally faithful, and here every gate also
  holds or improves. Twins clean (NOT-YET as expected). Owner review
  invited; both solved+registered on CI runners
  (caiso81-fleet-to-bins-regate, run 29267506581).
- **PJM leg in flight:** the PJM matrix job OOM'd the 7 GB hosted runner at
  the per-gen reserve co-opt LP build (39 R columns × 2396 units; a
  session-container rerun of the identical twin recipe was OOM-killed at
  16 GB RSS and completed only with swap). Re-running as
  `caiso81-pjm-regate-v2` on a 20 GB-swapfile runner, registering as
  **pjm-106** — a concurrent session minted `2026-07-13-pjm-105-symmetric-net`
  while the first launch was in flight, so 105 is claimed. Its re-gate
  adjudication lands as its own entry.
