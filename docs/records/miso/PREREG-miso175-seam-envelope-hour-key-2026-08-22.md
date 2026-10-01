# PREREG miso-175 — the seam-envelope hour-key rotation repair: control/arm A/B with kills fixed BEFORE any solve

**Session miso-175, 2026-08-22.** Keeper `2026-08-20-miso-173-layup-mask`
(bundle `miso173_layupmask`; determination NOT-YET on C3a-2025 (−11.6 %)
alone, C3c the single ledgered caveat, C6 PASS, C8 PASS all years, **zero D-4
conduct failures**). This document pre-registers, with thresholds fixed BEFORE
any LP is solved, the single-delta A/B that tests the rule-14 `[R-ACCURATE]`
hour-key repair of the ARMED seam deliverability envelope
(`miso_seam_envelope_hour_ending_key`, default off — implementation commit
`ad0f85a`, pushed before this document).

Order of operations, auditable in the commit history: miso-174 §4 (the
defect, reported not fixed) → miso-175 scope 1 (INDEPENDENT re-verification,
`scripts/probes/_miso175_rotation_verify.py` →
`_miso175_rotation_verify.json`, committed at `ad0f85a` — V-1 the −1 h solve
r = 1.0000 / 0.8286 / 1.0000, V-2 the roll-+1 identity, V-3 the MISO-only
gate, V-4 the committed-record cross-check, ALL PASS) → the gated
implementation (`ad0f85a`; OFF path proven byte-identical to pre-edit code on
all 24 year × direction × seam cap arrays, max|diff| = 0; pinned default
cache key `603c2498bf71d21d` unmoved) → the ENGINE-FROZEN instrument
(`scripts/probes/_miso175_hour_key_instrument.py` →
`_miso175_hour_key_instrument.json`, this commit) → **this document,
committed** → control solve → arm solve → the gates (§4) → the adjudication.

---

## 1. The object

`data/eia930/envelopes.py::measured_seam_import_envelope` bucketed the EIA-930
DIBA series on its raw `local_time` stamp and applied the (month ×
hour-of-day) bucket to the model's hour-beginning clock. `local_time` is
**hour-ENDING on MISO's local standard clock** — solved, not assumed: the −1 h
key reproduces the independently-derived BALANCE `TI` series at r = 1.0000 in
2023 AND 2025 (re-verified V-1). So the ARMED p90 cap applied at model hour
*h* was built from the measured population of hour *h−1* — an exact +1 h
rotation of the whole diurnal cap profile (PJM-seam import mean |Δ|
240.9 / 251.1 / 241.4 MW across 2023/24/25; reading the corrected profile one
hour back reproduces the legacy cap to mean |Δ| 1.8 / 1.4 / 2.4 MW; annual
mean level unchanged, PJM 6.232 vs 6.231 GW). It is a DEFECT and not a choice
because it is internally inconsistent with the repo's own conventions: the
seam LADDER derivation reads the SAME parquet with the conversion applied
(`scripts/data/derive_miso_seam_ladders.py:141`), so a correctly keyed price
ladder was applied against a mis-keyed cap. Both armed directions
(`miso_seam_flow_limit`, `miso_seam_export_limit`) and all four
`MISO_SEAM_DIBA` seams are affected.

## 2. The mechanism, and its DOF answer

`ScenarioConfig.miso_seam_envelope_hour_ending_key` (default off; registered
drop-at-default per the nyiso-119 discipline; armed key hashes distinctly).
When set, the loader shifts `local_time` by −1 h BEFORE the year filter and
the bucketing — the ladder derivation's exact convention. **Zero new numeric
parameters**: cap values, percentile (p90), ladder rungs and band grid are
byte-unchanged; only which model hour receives each bucket moves. The DOF
ledger is unchanged (33 entries / 2 residual). MISO-only by the seam-DIBA
gate (V-3: every other ISO returns None).

## 3. The engine-frozen instrument (committed BEFORE this prereg's gates run)

`_miso175_hour_key_instrument.json` freezes, from the PRODUCTION loader at
HEAD (never a re-derivation — the miso-173 discipline), for all 24
(year × direction × seam) arrays under BOTH key conventions:

* the **sha256 of each exact float64 cap array** (48 digests) — M-1's basis;
* annual means, mean/max |Δ|, Δ≠0 hour counts;
* the **signed window deltas** mean(corrected − legacy) — M-2(b)'s basis.

The direction structure it freezes (PJM import seam, the dominant one):
the corrected key **LOOSENS the summer-evening (HE18–22) import cap**
(+74.2 / +168.0 / +283.1 MW in 2023/24/25) and **TIGHTENS the summer-morning
(HE07–12) cap** (−74.0 / −229.5 / −180.5 MW), with the annual mean essentially
unchanged (−1.3 / −0.2 / +1.0 MW). The measured import profile RISES into the
evening; the legacy key lagged that rise by one hour. Note the sign: the
repair ADMITS MORE evening import in the hours MISO is tight — it moves the
model's scarce-hour price DOWN if anything, i.e. AWAY from closing C3a-2025.
That is exactly why it can be kept on rule-14 grounds alone (§5) and why no
number it produces may be quoted as scarcity progress.

## 4. The A/B and the gates, with kills fixed NOW

Control and arm are `replay_keeper` single-delta replays of the keeper at
HEAD, run SEQUENTIALLY (rule 12), each `--year 2023 2024 2025` in one
invocation:

```
python3 scripts/replay_keeper.py results/calibration/miso173_layupmask \
  --out-dir results/calibration/miso175_control \
  --note "miso-175 CONTROL: byte-faithful keeper replay at HEAD (new field at default off)"
python3 scripts/replay_keeper.py results/calibration/miso173_layupmask \
  --out-dir results/calibration/miso175_hourkey \
  --set miso_seam_envelope_hour_ending_key=true \
  --note "miso-175 ARM: seam-envelope hour-key repair (single delta)"
```

Scorer: `scripts/probes/_miso175_hour_key_ab.py` →
`results/calibration/_miso175_hour_key_ab.json`. Registration ids:
`2026-08-22-miso-175-control` / `2026-08-22-miso-175-hourkey` (both
registered, rule 15).

* **M-0 CONTROL INERTNESS (KILL).** Every one of the control's 12 scored
  sidecars (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years) is
  value-identical to the committed keeper's (max|diff| = 0 on every shared
  numeric column, identical row sets). Proves the new field and its
  registrations are solve-path inert at default at this HEAD.
* **M-1 CAP EXACTNESS (KILL).** (a) At scoring time the production loader
  regenerates all 48 arrays with sha256 EXACTLY matching the frozen digests
  (24 legacy = what the control consumed; 24 corrected = what the arm
  consumed). (b) The arm's dispatch respects the corrected bounds: per seam
  and hour, P1 gross import ≤ corrected import cap + 1 MW and P1 gross
  export ≤ corrected export cap + 1 MW (from the arm's local
  `unit_hourly` sidecar).
* **M-2 LIVENESS + DIRECTION.** (a) LIVENESS: the arm differs from the
  control in ≥ 1,000 P1 zone-hour price cells summed over the three years
  (of 3 × 61,320). Fewer ⇒ the mechanism is INERT as wired: not promoted,
  cell verdict `I`, keeper unchanged. (b) DIRECTION (KILL if it fails in
  ≥ 2 of 3 years): per year, over
  `B_loose = {Jun–Sep hours where the CONTROL's PJM gross import sits within
  max(1 MW, 1 %) of its legacy cap AND corrected − legacy > +20 MW}`,
  mean(arm − control) of PJM gross import must exceed **−25 MW** (the
  loosened binding cap must not systematically REDUCE import; expected
  positive). A year with |B_loose| < 20 h is reported, not gated —
  composition may shrink the binding set, and the instrument is blind to
  composition by design.
* **M-3 CONDUCT (KILL).** The arm's regenerated `legitimacy_diagnostics.json`
  carries ZERO D-4 conduct failures (the miso-173 headline is preserved) and
  zero NEW D-4 rows vs the regenerated control.
* **M-4 C8 (KILL).** C8 PASS in all three years on the arm (the keeper's
  grounded-above-budget path for 2025 ST_GAS is an allowed PASS form).
* **M-5 RECORD FLIPS (KILL).** Over the verdict scorer's 67 records
  (statuses at (criterion, record-index) grain), ZERO PASS → non-PASS flips,
  arm vs the committed keeper.
* **M-6 AGAINST-INTEREST (KILL).** C3a-2023 stays within **±3.0 %** (keeper
  +1.22 %; the miso-156 computed 2023 regression bound) AND C3a-2024 stays
  within ±10 % with an adverse (more-negative) move ≤ **1.5 pp** (keeper
  −4.07 %). C3a-2025 is reported at full magnitude and NOT gated — §5.

## 5. The honest ceiling, stated BEFORE any solve (charter item 4)

**C3a-2025 is CLOSED END TO END as a model-class limit** — the RT-only half
by the miso-163 owner ruling, the DA-foreseen half by
`FINDING-miso171-reserve-requirement-decomposition-2026-08-20.md` §6. This
repair is a rule-14 `[R-ACCURATE]` accuracy repair of a measured input inside
an armed keeper mechanism and **may be kept on that ground ALONE**. It must
NOT be sold as, or tuned toward, closing C3a-2025, and no number it produces
may be quoted against that gate. The expected price effect is SMALL — the cap
level is unchanged, only its diurnal placement moves — and the frozen
direction (§3) if anything ADMITS more scarce-evening import, i.e. runs
AGAINST the C3a-2025 residual. Any C3a-2025 movement in either direction is
disclosed, never claimed.

## 6. Verdict mapping, fixed now

* All kills silent AND M-2(a) live → **promote the arm to keeper**
  `2026-08-22-miso-175-hourkey` on the rule-14 ground alone (a more
  accurately keyed measured input in an armed mechanism), whatever the fit
  deltas; matrix: `seam_flow_envelopes` stays `K` (strengthened),
  `miso_seam_envelope_hour_ending_key` MISO cell `O` → `K`; keeper shard
  re-key + `audit_keepers --iso MISO` in-session.
* M-2(a) inert → keeper unchanged; cell `O` → `I` with the record.
* Any KILL fires → arm REJECTED-AS-ARMED; keeper unchanged; cell `O` → `R`
  with the record and the firing gate named.
* In every outcome BOTH runs are registered (rule 15) and the cell is
  stamped in-session (rule 28b).

## 7. Governance and disclosed conditions

* Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the
  holdout spend freeze is untouched; no marker re-key is owed (MISO has no
  `complete` entry). LOO is vacuous for the same argued reason as miso-172
  arm 2 / miso-173: zero free parameters — there is nothing to identify, so
  no year can have identified it.
* **Disclosed, not created here:** (a) the committed-vs-regenerated
  diagnostics exposure (standing owner item; every gate compares
  regen-control to regen-arm through the same path at the same HEAD);
  (b) the cross-ISO STALE-BENCHMARK stamp-absence flag
  (`check_bench_freshness`; caiso-210 measured it as stamp-absence, not
  drift) — the A/B compares both arms against the SAME committed bench, so
  no gate depends on the stamp;
  (c) the 2024 EIA-930 DIBA↔BALANCE internal inconsistency (r = 0.8286 at
  the solved key; miso-174 §5) — the DIBA product is the envelope's own
  source series under BOTH conventions, so the key repair is orthogonal to
  it; disclosed on any 2024-specific number.
* Rule 19 `[R-ONE-MECH]`: this changes the KEY of the one existing envelope
  mechanism; no new mechanism, floor, or stacked channel. Rule 26: nothing
  deleted; the legacy key remains the default for replay fidelity.
* Rule 25: MISO-only (V-3). The PJM analogue (a DIFFERENT measured source,
  the PJM tie-line file) is handed forward to PJM's lane, not inspected here.
