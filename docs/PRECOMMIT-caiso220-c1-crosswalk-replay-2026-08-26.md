# PRECOMMIT — caiso-220: the funded caiso-217 replay (caiso-200 keeper recipe + the measured generator-hub-membership crosswalk), scored and REGISTERED under the committed caiso-216 §G gate table

_2026-08-26 · CAISO backcast lane, session caiso-220. Charter: the owner's
2026-08-26 handoff ("CAISO — CLOSE THE C3a LEVEL OVERRUN IN 2024/2025 …
Deliverable: a registered CAISO run across 2023-2025 with its precommit, its
matrix cell update, and an honest verdict — including 'the lever is refuted'
if that is what the measurement says"). Pushed BEFORE the solve is launched;
no gate number from this solve exists at the time of this commit._

---

## 1. The lever, and why the session goes off-queue

**The lever is C1 — the measured generator-hub-membership crosswalk**
(`data/raw/reference/caiso-plant-hub-membership.csv`, 446 plants / 41.1 GW,
landed at `f0dd328` by caiso-217 and ACTIVE as data for every CAISO solve
since via the `zone_assignment` CAISO first-check), **tested by the one
funded 3-year solve of FINDING-caiso216 §G Ask 2** — the caiso-200 keeper
recipe replayed byte-for-byte with the crosswalk as the only delta.

**Off-queue statement (handoff method step 1).** The CAISO in-model lever
queue is EMPTY with every cell adjudicated (caiso-185, re-confirmed
caiso-188/200; matrix §5.2 header). The two ranked C3a successors are both
decisive nulls blocked on the same CEII rating object (caiso-218 §F.3b,
caiso-219 §F.3a). The ONLY admissible, already-funded solve object in the
lane is this replay: the caiso-217 session's funded solve COMPLETED
IN-CONTAINER BUT NEVER LANDED (FINDING-caiso217 §D–§F, written by caiso-218;
filed item 8 — the rule-15 registration debt), so the crosswalk's solve-side
effect is **UNSCORED on the record while every future CAISO solve carries
it**. That state is untenable under rule 15 and rule 14 alike, and the
owner's 2026-08-26 charter — a registered 2023–2025 run targeting C3a, with
the honest-refutation clause — funds exactly this repair. Nothing else is
armed; no cell at R/I/G is re-tested.

**Rule-13 admissibility** was adjudicated at caiso-216 §F.1 (published
registry, quantity-side, zero free parameters, forward analogue) and is not
re-argued here. **Rule 25:** every input is CAISO's own (`ATL_PNODE_MAP`,
EIA-860, CAISO DAM outage resource names). **Rule 21/24:** zero new
tunables, no new `ScenarioConfig` field — the crosswalk is data on the
existing zone-assignment layer.

## 2. Invocation, pre-registered

Through the sanctioned recipe-replay channel (identical to caiso-217 §C):

    python3 scripts/run_calibration_full.py \
      --replay-bundle results/calibration/caiso200_h1_memberpanel \
      --out-dir results/calibration/caiso220_c1_crosswalk \
      --note "caiso-220: the funded caiso-217 replay (registration-debt repair) - caiso-200 keeper recipe, crosswalk auto-active as data, caiso-216 SG gate table"

Years default to the bundle's own `[2023, 2024, 2025]` (rule 16), sequential
within the run (rule 12). Recipe = the keeper's `meta.json` byte-for-byte
(`replay_keeper.build_kwargs`); the crosswalk enters as data through the
committed first-check; **nothing is armed, changed, or tuned**. P1 is
scored. Container-death insurance (the caiso-217 failure mode): per-year
hourly sidecars are committed and pushed as checkpoints as each year lands.

## 3. Pre-registered expectations (sign and magnitude, from committed bytes only)

* **C3a direction: DOWN in 2024/2025, small.** In an S→N-bound hour the
  south (61 % of load) decouples down from the pooled band. The committed
  realized-membership table (`_caiso217_realized_membership.json`) puts the
  input-side bound-hour count at **121 / 480 / 742** h (2023/24/25) over the
  armed 5,400 MW Path-15 S→N rating — an order below reality's split-hour
  vector [1,310 / 1,691 / 1,347] — so the expected C3a move is a **fraction
  of a point, NOT a close**: expected 2024 ≈ +12.3 to +12.8 %, 2025 ≈ +15.2
  to +15.7 % (needed: ≤ +10 %). The caiso-217 session's own lost-scored
  claim (+4.0 / +12.5 / +15.5; SECONDARY evidence, never a baseline) sits
  inside this window and is what this solve either reproduces or corrects.
* **2023 stays in band** (expected ≈ +4.0 to +4.1 %; headroom −$7.4 down /
  +$5.9 up). The 2023 bound count (121 h) is 3–6× below 2024/25 — the
  caiso-215 2023-safe geometry.
* **C3b**: expected ≈ baseline (0.098 / 0.179 / 0.182), small improvements
  in 2024/2025 plausible (secondary claim 0.100 / 0.177 / 0.180). The 2025
  composition watch (margin 0.018) is THE tripwire per the committed gate
  table.
* **Split witness**: model NP15−SP15 > $15 hours moves 0 → nonzero but
  far below reality (secondary claim ~50/40/17 h; the direction, not the
  magnitude, is the structural deliverable).
* **D-A (rubric v3.5, REPORTED-ONLY)**: the crosswalk moves zonal
  allocation, not diurnal shape — amplitude/phase expected ≈ unchanged from
  67.0 / 73.3 / 89.2 % of measured. Any material amplitude move is reported
  as an unexpected regression signal. (D-A cannot gate and is not treated as
  a gate; if any probe decodes `lmpDeltaHr`, the −32768 sentinel is masked
  and the day dropped.)

## 4. The gate table (committed at caiso-216 §G — adopted verbatim, not restated)

C3a scored ×3 with 2023 in band; **C3b MUST-NOT-REGRESS vs
0.098/0.179/0.182** (a 2025 trip reads as the §F.3c export-absorption
diagnosis, NOT a C1 refutation); C8/D-1..D-4 unchanged (C1 adds no forcing);
C6 re-attested at any promotion (discharges filed item 2); DOF 10/7
unchanged + one measured-input identification row (crosswalk source + join
method), zero new tunables; LOYO n/a as parameter identification (nothing
fitted), rule-20 flip rule applies unchanged; split witness
(`_caiso217_zonal_decomp.py`) run against the landed bundle. All deltas
reported at full magnitude whatever their sign.

## 5. STOP rules and verdict pre-registration

1. **No number from this solve feeds any input change.** Whatever the
   result, nothing is re-tuned, re-derived, re-sized or re-solved this
   session (one invocation; a clean-input-guard relaunch of the SAME
   unchanged invocation, caiso-217 §C precedent, is not a re-solve).
2. **The run is REGISTERED whatever the outcome** (rule 15 — keeper or
   rejected probe), with the caiso-216 partial-close pre-registration
   carried verbatim: **a 2024-only C3a pass is NOT a determination flip;
   NOT-YET stands unless 2025 clears with 2023 in band.** Expected outcome,
   stated honestly in advance: **NOT-YET stands** with C3a reduced by
   fractions of a point, and the deliverable is the scored, registered,
   honest record — the registration-debt repair — not a manufactured close.
3. **If C3a-2023 exits the band**: the run is registered as a REJECTED
   probe, the keeper stays `2026-08-17-caiso-200-h1-memberpanel`, and the
   C1 data stays (rule 14 — the crosswalk is measured; a worse fit is a
   discovered-bug signal, recorded for the lane, never a reason to revert
   measured data).
4. **If C3b-2025 regresses past 0.182**: recorded as the pre-registered
   §F.3c export-absorption diagnosis firing (the caiso-216 gate table's own
   reading), not a C1 refutation; no contingency is armed this session —
   the diagnosis goes to the owner.
5. **Keeper decision — pre-registered proposal, owner decides.** Under the
   owner's caiso-217 promotion standard (2026-08-23, verbatim: "If
   structural integrity improves but gates regress that may still be a
   keeper"), if 2023 stays in band and no protective gate (C6/C8) fails,
   this run is PROPOSED as keeper on rule-14 structural grounds: the
   measured crosswalk is active in the data layer at HEAD, so the committed
   caiso-200 bundle no longer reproduces at HEAD, and the replay is the
   recipe's honest current score. Any gate regression is disclosed at full
   magnitude in the proposal. THE OWNER MERGES; if the owner declines, the
   run stands as a registered candidate and the keeper is unchanged.

## 6. Record obligations (executed this session, success or failure)

Rule 15: dashboard registration (registry sidecar + run payload + bench)
committed and pushed this session. Rule 26/28b: the CAISO shard ONLY —
`path15_load_split` and `measured_interface_limits` evidence + the tested
verdict of the C1 solve stamped; §5.2 caiso-220 block; no other ISO's shard
touched. `docs/calibration-log/caiso.md` caiso-220 entry;
FINDING-caiso220 with the full gate table against these pre-registrations.
The DOF-ledger stale-text item (filed item 1, `offer_curve_by_group`
"identification: residual" vs measured-since-2026-08-02) is corrected in the
attestation IF this run is promoted, per its filing.
