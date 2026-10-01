# RESULT miso-175 — the seam-envelope hour-key rotation repair: ALL KILLS SILENT, **PROMOTED TO KEEPER**, and the armed envelope's cap now lands on the hour it was measured in

**Session miso-175, 2026-08-22.** Executes
`PREREG-miso175-seam-envelope-hour-key-2026-08-22.md`, committed — with the
ENGINE-FROZEN per-seam cap arrays (48 sha256 digests + signed window deltas,
`_miso175_hour_key_instrument.json`) — **before any solve** (commit `38f5829`;
the gated implementation is `ad0f85a`, the A/B scorer `ac26848`, all pushed
before either LP ran). Control `miso175_control`, arm `miso175_hourkey`, both
`replay_keeper` single-delta replays of the keeper at HEAD,
`--year 2023 2024 2025` sequential, control and arm consecutive on the 15 GB
container (FINDING-miso169 recipe: pins + 8 GB swapfile +
`MARKET_SIM_HIGHS_THREADS=4`; ~16 min/year held).

**Outcome: EVERY PRE-REGISTERED KILL IS SILENT and the mechanism is decisively
live. Promoted to keeper `2026-08-22-miso-175-hourkey` on the arm's own
verdict mapping (PREREG §6) — no owner override needed — on the rule-14
`[R-ACCURATE]` ground ALONE: a more accurately keyed measured input inside an
armed keeper mechanism.** Determination **UNCHANGED at NOT-YET on C3a-2025
ALONE** (−11.65 → −11.80 %), C3c the single ledgered caveat: this promotion
buys measured-input accuracy — the armed cap now lands on the model hour its
population was measured in, on the same key as the price ladder it composes
with — not a determination change.

## 1. The object, re-verified before anything was built (charter scope 1)

The charter ordered miso-174 §4 re-verified, not trusted.
`scripts/probes/_miso175_rotation_verify.py` (record
`_miso175_rotation_verify.json`, committed in the implementation commit):

* **V-1 the hour-key solve** — sweeping shift ∈ [−3, +3] h on the DIBA file's
  `local_time` and correlating the DIBA-sum net import against the
  independently-keyed BALANCE `TI` series: **−1 h wins at
  r = 1.0000 / 0.8286 / 1.0000** (2023/24/25) — exactly the miso-174 numbers,
  with every other shift strictly worse.
* **V-2 the rotation identity** — production caps vs the correctly keyed
  (−1 h) p90 table: PJM import mean |Δ| **240.9 / 251.1 / 241.4 MW at roll 0
  → 1.8 / 1.4 / 2.4 MW at roll +1** (annual level unchanged, 6.232 vs
  6.231 GW in 2023) — an exact rotation, not a level error, and tighter than
  the charter's quoted residual. The EXPORT direction carries the same
  rotation (SPP/South/Manitoba roll-0 ≈ 100–150 MW → ≈ 0–2 MW at roll +1).
* **V-3 the MISO-only gate** — all five other ISOs return `None` (rule 25).
* **V-4 committed-record cross-check** — the re-derived roll-0 diffs match
  the committed miso-174 record within 1 MW on every (year, seam).

## 2. The mechanism (charter scope 2)

`ScenarioConfig.miso_seam_envelope_hour_ending_key` (default off, registered
drop-at-default per the nyiso-119 discipline — the pinned global default key
`603c2498bf71d21d` is byte-stable, verified by
`scripts/check_cache_key_registration.py` and the pin tests; armed key
distinct). When set, `measured_seam_import_envelope` shifts `local_time` by
−1 h BEFORE the year filter and the (month × hod) bucketing — the exact
conversion `derive_miso_seam_ladders.py:141` applies to the same parquet, so
**ladder and cap are now on one key**. Threaded
`inject_miso_seam_flow_limit(hour_ending_key=…)` (both directions, all four
`MISO_SEAM_DIBA` seams) from the `run_year` seam-injection block; CLI
`--miso-seam-envelope-hour-ending-key`. **Zero new numeric parameters** (a
key-convention selector; cap values, p90, ladder rungs and band grid
byte-unchanged); DOF ledger 33 entries / 2 residual, unchanged. The OFF path
was proven byte-identical to pre-edit code on all 24 cap arrays
(max|diff| = 0) before anything else ran.

## 3. The gates, as scored (`_miso175_hour_key_ab.json`)

| gate | verdict | measurement |
|---|---|---|
| **M-0** control inertness | **PASS** | 12/12 scored sidecars, all years, max\|diff\| = 0.0 vs the committed keeper; the control's regenerated `legitimacy_diagnostics` matches the keeper's committed artifact gate-for-gate |
| **M-1a** cap exactness | **PASS** | all 48 regenerated cap arrays sha256-identical to the frozen instrument — the solves consumed exactly the frozen object |
| **M-1b** bound respect | **PASS** | the arm never exceeds a corrected cap by more than 1 MW, any seam, any hour, either direction |
| **M-2a** liveness | **LIVE** | **95,828** differing P1 zone-hour price cells over the three years (bar: 1,000) |
| **M-2b** direction | **PASS 3/3** | over `B_loose` (Jun–Sep control-binding hours whose corrected PJM import cap is ≥ +20 MW looser; n = 68/300/43), mean arm−control gross import **+113.8 / +220.9 / +272.1 MW** — the frozen sign, every year |
| **M-3** conduct | **PASS** | ZERO D-4 conduct failures on the arm; zero new non-pass rows vs the regenerated control — the miso-173 headline is preserved |
| **M-4** C8 | **PASS** | all years; 2025 ST_GAS grounded above budget at 32.3 % forced, profile_r 0.982, cv_ratio 1.533 (the keeper's grounded form) |
| **M-5** record flips | **PASS** | 67 records, **ZERO** PASS → non-PASS flips vs the committed keeper |
| **M-6** against-interest | **PASS** | C3a-2023 +1.219 → **+1.230 %** (band ±3.0); C3a-2024 −4.068 → **−4.064 %** (adverse move 0.00 pp) |

## 4. What moved, and the direction that proves the honesty of the ground

The frozen instrument predicted, before any solve, that the corrected key
**LOOSENS the summer-evening (HE18–22) PJM import cap** (+74.2 / +168.0 /
+283.1 MW) and tightens the morning — the measured import profile rises into
the evening and the legacy key lagged it one hour. The solve confirmed it:
more evening import in exactly the hours MISO is tight, and
**C3a-2025 moved AGAINST the model, −11.648 → −11.795 %**. That is the
pre-registered expectation working as designed: this repair was never a
scarcity lever, could not have been sold as one, and is kept because the
armed measured input is now *accurate* — the cap applied at model hour *h* is
built from the measured population of hour *h* (rule 14), on the same clock
as the Q-Q price ladder it composes with.

## 5. Reported against interest

* **C3a-2025 worsens 0.15 pp** (−11.65 → −11.80 %). Disclosed at full
  magnitude; the miso-163 owner ruling and the miso-171 decomposition close
  that lane as a model-class limit and nothing here claims against it —
  including this worsening, which is the accurate input's honest price.
* **C3c's 2025 tail count moves 3 → 2 h** (vs actual 88) — the loosened
  evening import shaves one modelled tail hour. Same ledgered caveat in kind;
  disclosed, not absorbed.
* **The 2024 EIA-930 internal inconsistency** (DIBA↔BALANCE `TI` r = 0.8286
  at the solved key vs 1.0000 in 2023/2025; miso-174 §5) attaches to any
  2024-specific number; the DIBA product is the envelope's own source series
  under BOTH conventions, so the key repair is orthogonal to it.
* **The bench restamp is stamp-only, measured**: registration re-rendered
  MISO's three bench parts through the builder at HEAD and the bench CONTENT
  is byte-identical — only `builderFingerprint: ded4ca25749a` was added.
  The caiso-210 "stamp-absence, not drift" conclusion is now MEASURED for
  MISO, and MISO's STALE-BENCHMARK flag resolves.
* **The committed-vs-regenerated diagnostics exposure** is unchanged in kind
  and disclosed, not created here; this session's regen-control additionally
  reproduced the keeper's committed artifact gate-for-gate.

## 6. Governance and housekeeping

* Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the
  spend freeze untouched; no marker re-key owed. LOO vacuous (zero free
  parameters — the key was solved against the independently-keyed BALANCE
  `TI` series, never any year's residual).
* Rule 28: base row + cell line in every ISO shard landed in the
  implementation commit; MISO's cell stamped `K` with this evidence;
  `seam_flow_envelopes` stays `K`, strengthened; no other ISO's verdict
  touched (rule 25 — the five other shards carry `.`, MISO-only by the
  seam-DIBA gate).
* Rule 15: runs `2026-08-22-miso-175-control` / `2026-08-22-miso-175-hourkey`
  both registered; retention pruned `2026-08-13-miso-155-control-p0` and
  `2026-08-15-miso-159-cod-vintage` (top-15 sweep working as designed).
* Cross-ISO, handed forward NOT assigned (rule 25): whether PJM's
  seam-envelope analogue (`pjm_seam_flow_limit` — a DIFFERENT measured
  source, the PJM tie-line file) carries the same hour-key convention is
  PJM's lane's call.

## 7. The four standing OWNER items, restated not decided

Carried forward unchanged from miso-171/172/173/174; this session raises
them and decides none:

1. **The C8 provenance-materiality floor** — the rubric hole (no materiality
   floor inside C8's provenance leg) remains unrepaired; miso-173's mask
   cleared the plant-990 instance only as a side effect.
2. **The committed-vs-regenerated diagnostics exposure** (MISO and PJM,
   measured) — unchanged in kind; this session's regen-control matching the
   committed artifact is one clean data point, not a repair.
3. **`RHO_CLIP` 0.5 vs the measured MISO rho 0.1764** (nyiso-144) — still
   the owner escalation; no new claim here.
4. **MISO's determination posture** — C3a-2025 is the SOLE failing
   criterion, documented end to end as a model-class limit (miso-163 ruling +
   FINDING-miso171 §6), on a keeper with ZERO D-4 conduct failures, C6
   attested, C8 PASS all years, and C3c the single ledgered caveat. Whether
   `NOT-YET` should be adjudicated to a declaration is an OWNER question —
   riper than ever: miso-174 closed the last named OPEN cell, and miso-175
   has now also repaired the last named measured-input defect inside an
   armed keeper mechanism.

## 8. Reproduction

```
python3 scripts/probes/_miso175_rotation_verify.py        # scope-1 verification
python3 scripts/probes/_miso175_hour_key_instrument.py    # the frozen instrument
python3 scripts/replay_keeper.py results/calibration/miso173_layupmask \
  --out-dir results/calibration/miso175_control --note "..."
python3 scripts/replay_keeper.py results/calibration/miso173_layupmask \
  --out-dir results/calibration/miso175_hourkey \
  --set miso_seam_envelope_hour_ending_key=true --note "..."
python3 scripts/probes/_miso175_hour_key_ab.py            # the gates
python3 scripts/calibration_verdict.py --run-id 2026-08-22-miso-175-hourkey
```
