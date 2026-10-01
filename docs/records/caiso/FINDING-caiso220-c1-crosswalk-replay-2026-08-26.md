# FINDING — caiso-220: the funded caiso-217 replay LANDED, SCORED and PROMOTED — the measured generator-hub-membership crosswalk's solve-side effect is finally ON THE RECORD: C3a improves in ALL THREE years (+4.0 / +12.5 / +15.5 vs the keeper's +4.1 / +12.8 / +15.7) and the Path-15 separation machinery ENGAGES in reality's direction (NP15−SP15 > $15 hours 0 → 50/40/17) — but at ~3 % of reality's split magnitude, so **C3a is NOT closed** and the determination stays **NOT-YET**; keeper `2026-08-26-caiso-220-c1-crosswalk` promoted on the owner's in-session instruction as the recipe's honest current score (2026-08-26)

**Charter.** The owner's 2026-08-26 handoff ("CAISO — CLOSE THE C3a LEVEL
OVERRUN IN 2024/2025 … including 'the lever is refuted' if that is what the
measurement says") plus the owner's in-session promotion standard, verbatim:
*"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."* —
the same standard that funded caiso-217. Pre-registration:
`docs/PRECOMMIT-caiso220-c1-crosswalk-replay-2026-08-26.md`, pushed BEFORE
the solve; the gate table is the committed caiso-216 §G table adopted
verbatim. Off-queue statement: the CAISO in-model queue is EMPTY with every
cell adjudicated (caiso-185/200), both ranked C3a successors are
CEII-blocked decisive nulls (caiso-218/219), and the one funded-admissible
solve object was this replay — the caiso-217 registration debt (filed item
8), whose crosswalk has been ACTIVE DATA for every CAISO solve since
`f0dd328` while its solve-side effect stayed unscored.

**Invocation** (precommit §2, executed verbatim): `run_calibration_full.py
--replay-bundle results/calibration/caiso200_h1_memberpanel --out-dir
results/calibration/caiso220_c1_crosswalk` — the keeper's `meta.json` is the
config (251 kwargs via `replay_keeper.build_kwargs`, no `--set`, no legacy
P2), years 2023–2025 sequential, P1 scored. Two environment repairs, both
recipe-neutral and logged: the fresh container's `data/clean` tree rebuilt
via `scripts/regenerate_clean.py` (49/51 datatypes; the 2 failures are
ERCOT/MISO corpus datatypes not on the CAISO path), and the container's
missing IANA tz database installed (`tzdata`; first launch died on
`ZoneInfoNotFoundError: US/Pacific` before any LP was built). Mid-solve
checkpoints were committed per year (the caiso-217 container-death lesson —
and this session's container DID restart mid-report; the bundle survived on
disk and nothing was lost).

## §A — The gate table, scored (every §G row, full magnitude)

| gate | pre-registered | measured on this bundle | verdict |
|---|---|---|---|
| C3a | 2024/2025 toward band, **2023 stays in band** | **+4.0 % / +12.5 % / +15.5 %** (model lw 56.31/38.96/39.76 vs RT 54.17/34.65/34.42; keeper +4.1/+12.8/+15.7) — all three years improve; 2024/2025 still out of ±10 | **held** (close NOT achieved, as pre-registered) |
| C3b | MUST-NOT-REGRESS vs 0.098/0.179/0.182; 2025 margin 0.018 = THE tripwire | **0.100 / 0.177 / 0.180** — 2024/2025 improve, 2025 margin widens to 0.020 (**tripwire did NOT fire**); 2023 regresses **+0.002**, disclosed at full magnitude | **held** (2023 delta disclosed) |
| C8 / D-1..D-4 | unchanged — C1 adds no forcing | C8 PASS every material class (D-2 0.0 % forced on the reported classes) | **held** |
| C6 | attestation regenerated at promotion | `gen_caiso220_attestation.py` — keeper attestation carried, C3c magnitudes re-measured on this bundle's bytes; C6 PASS | **held** (discharges filed item 2's regeneration half for this bundle) |
| DOF | 10/7 + one measured-input row, zero new tunables | **11 entries / 7 residual** — the `caiso-plant-hub-membership crosswalk` row (identification `measured`, zero scalars) added in `build_dof_ledger.py` | **held** |
| LOYO | n/a as identification; rule-20 flip rule if any verdict flips | nothing fitted; **no criterion verdict flips vs the keeper** (C3c stays the ledgered caveat; magnitudes below) | **held** |
| split witness | `_caiso215` re-run: >$15 hours 0 → reported | **50 / 40 / 17 h** vs reality 1,310/1,691/1,347 (`_caiso220_zonal_decomp.py` + committed JSON) | **reported** |

Verdict scorer (`calibration_verdict.py --run-id
2026-08-26-caiso-220-c1-crosswalk`): **NOT-YET**, 8 criteria, ONE
load-bearing FAIL — C3a alone; C1 12/12 (free 8/8), C2/C4 PASS, C3c the
single ledgered caveat (guard (a) of the standing rule correctly silent —
C3a also fails). Also disclosed at full magnitude:

* **C3c re-measured magnitudes**: 2023 0 h/47 (unchanged), 2024 **1 h → 0 h**,
  2025 0 h vs actual 8 h (not gated; DA companion 0 h vs 0 h). The 2025
  model max zonal λ is $69.73 vs the keeper's higher top — the pooled
  scarcity top thins slightly where the south decouples; within the
  ledgered model-class limitation, no verdict change.
* **D-A (reported-only, band-free)**: amplitude 66.6/72.2/87.8 % of measured
  vs the keeper's 67.0/73.3/89.2 %; phase flags IDENTICAL (2023/2024 OK,
  2025 OFF on both runs — peak h22 vs h18); hod r +0.966/+0.968/+0.976.
  The precommit's regression check passes: the crosswalk left amplitude and
  phase essentially alone. (No `lmpDeltaHr` decode anywhere in this lane —
  the sentinel hazard did not arise.)
* **C5a co2 (reported-only)**: −11.2 % / −6.6 % / −7.6 %.
* The 2024-only partial-close pre-registration was not reached (2024 did
  not clear); **NOT-YET stands** exactly as pre-registered.

## §B — What the crosswalk did (the split witness, per-zone)

The caiso-215 instrument re-run on this bundle (committed
`_caiso220_zonal_decomp.json`; the caiso-202 §A control reproduces:
CA-wide 2023 +2.5 % on the probe's lw convention):

* **The model now splits at Path 15 in reality's direction.** NP15−SP15
  > $15: **0 → 50/40/17 h**; belly-only mean split +$1.42/+$0.76/+$0.83 vs
  reality's +$17.8/+$21.2/+$12.2. The caiso-216 rule-1 witness generalizes:
  given measured membership, the armed S→N ratings bind and the machinery
  separates — reality's ORDER (2023 < 2024, 2025 smallest >$15 count on
  both sides' belly geometry), ~3 % of reality's magnitude.
* **Per-zone C3a moves the right way in every zone.** 2024: NP15 −6.6 % →
  **−3.5 %**, LA_BASIN +27.1 → **+23.6 %**, SDGE +22.1 → **+18.8 %**,
  SP15_rest +23.8 → **+20.4 %** (ZP26 +16.8 → +18.0 %, the one adverse
  zone — it now prices with the south more of the time, which is itself
  reality's structure, caiso-215 §D.3). 2025: NP15 +2.0 %, south
  +14.9/+22.2/+16.3/+18.8 %. 2023: NP15 −2.9 %, south +4.2 to +8.8 %.
* **The residual attribution is unchanged and now measured on the arm
  itself**: the remaining gap is the caiso-215 §F H4 south-belly
  surplus-pricing regime — sub-zonal strandedness the 5-zone pool cannot
  form — whose two lever routes are the caiso-218/219 decisive nulls,
  both blocked on the same CEII rating object (filed item 9). The
  crosswalk was never sized to close it (caiso-216 S2 upper bound
  342/742/1,143 h vs reality 1,310/1,691/1,347); it is the allocation
  HALF of the answer, landed and honest.

## §C — Promotion (owner act, pre-registered decision rule)

Precommit §5.5: 2023 in band ✓, C6/C8 PASS ✓ → PROPOSED as keeper on
rule-14 structural grounds; the owner's standing in-session instruction
("If so plz promote…") executes it. **Keeper:
`2026-08-17-caiso-200-h1-memberpanel` → `2026-08-26-caiso-220-c1-crosswalk`.**
The decisive structural fact: the crosswalk is ACTIVE DATA at HEAD for
every CAISO solve, so the caiso-200 bundle no longer reproduces at HEAD —
the promoted run is the same recipe's honest current score with the
measured membership replacing the lat-cut/county-lift estimate
[R-ACCURATE]. Disclosed regressions carried into the keeper note at full
magnitude: C3b-2023 +0.002; C3c-2024 magnitude 1 h → 0 h; D-A amplitude
−0.4/−1.1/−1.4 pp. CAISO holds no `complete` marker, so no
`calibration-complete.json` re-key is due (rule 22 D-5(b) n/a).

## §D — Record changes

* Bundle + registration + promotion committed and pushed this session:
  `results/calibration/caiso220_c1_crosswalk/` (slim files + the
  {class_hourly, storage, system} ×3 keeper sidecars),
  `frontend/data/backcast/registry/2026-08-26-caiso-220-c1-crosswalk.json`,
  `runs/2026-08-26-caiso-220-c1-crosswalk.js` (blob-verified after push),
  `bench/CAISO/{2023,2024,2025}.json.gz` (re-stamped — discharges filed
  item 5, the three HARD-STALE parts), `keepers/CAISO.json` +
  `status/CAISO.js`.
* `scripts/gen_caiso220_attestation.py` (the E10 series continues);
  `scripts/build_dof_ledger.py` crosswalk row (committed at `2d9823f`);
  the `offer_curve_by_group` ledger row annotated on this bundle —
  discharges filed item 1 (the stale "identification: residual" text for
  CAISO's measured CC/CT bands) at the promotion, as filed.
* Matrix (rule 28b, CAISO shard only): `path15_load_split` evidence + the
  caiso-220 tested outcome appended (cell stays K — the gen-side program
  is now solve-verified); `measured_interface_limits` evidence appended
  (the armed ratings now BIND 50/40/17 h on the scored path); shard
  keeper/gates stamps re-stamped; §5.2 caiso-220 block added. NO cell
  verdict moves (K cells confirmed K; nothing new tested to a different
  verdict).
* `docs/calibration-log/caiso.md` caiso-220 entry; this FINDING.
* Filed items after this session: item 1 DISCHARGED, item 2 discharged for
  the PROMOTED bundle (the caiso-200 bundle's own stale
  `legitimacy_diagnostics.json` is moot — it is no longer the keeper),
  item 5 DISCHARGED, item 8 (the registration debt) **DISCHARGED — this
  session**. Still open: item 3 (caiso-205 pair sites), item 4 (promoting
  sessions re-measure the whole scorecard — done here, carried as standing
  duty), item 6 (`zonal_gas_basis: K` unsupported cell — untouched, still
  due a caiso-203-style re-adjudication), item 7 (`solar_deliverability`
  K-text leg note), item 9 (both C3a successors CEII-blocked).

## §E — DO-NOT-REDO (adds; caiso-202 §I, caiso-215 §I, caiso-216 §I, caiso-218/219 §F carry whole)

* **Re-solving the caiso-200 recipe expecting a different C3a** — this
  bundle IS that solve at HEAD; the crosswalk's effect is now committed
  measurement (+0.1–0.3 pp per year, 50/40/17 split hours).
* **Re-running the split witness on this bundle** — committed JSON.
* **Treating the caiso-217 secondary numbers as unverified** — every one
  (C3a +4.0/+12.5/+15.5, C3b 0.100/0.177/0.180, split 50/40/17) is now
  reproduced as committed measurement; cite caiso-220, not the handoff.
* **Proposing the crosswalk's completion (more movers) as a C3a lever
  without new membership evidence** — the E3-tier join was
  precision-audited (caiso-217 §A); the S2 upper bound already showed the
  full-allocation ceiling (342/742/1,143 h) is ~⅓ of reality's split
  hours. The gap is strandedness, not allocation recall.

Next number: caiso-221.
