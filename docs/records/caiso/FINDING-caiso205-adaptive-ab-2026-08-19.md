# FINDING — caiso-205: the adaptive-expectation storage offer's CAISO leg, built and A/B'd at full magnitude on owner order — **ALL pre-registered gates PASS, arm byte-identical 2023/2025 and near-inert 2024 (floor max $14.5), cell stays I, NOT a keeper candidate** — the caiso-204 G-BOOT wall confirmed to the dollar (2026-08-19)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED.** Owner order:
caiso-205 charter branch 1 (Phase-1 entry over the caiso-204 recorded Phase-0
FAIL — the ercot-188/213/215/221 pattern), selected explicitly in-session.
Pre-registration: `PRECOMMIT-caiso205-adaptive-ab-2026-08-19.md`, committed
and pushed before either solve was launched; no bar moved after a result was
read (the one scorer correction — G-REPRO's extra-files clause exceeding the
precommit bar — is §C).

## §A — What was built (the single delta)

`caiso_storage_adaptive_expectation` (ScenarioConfig, default off,
CAISO-gated; the ERCOT field untouched, rule 25) + the two rule-23 frozen
constants `caiso_adaptive_half_life_days = 30.0` /
`caiso_adaptive_beta = 0.5945` — FROZEN at the caiso-204 identification per
the charter. Two-pass P1 through the existing `p1_storage_discharge_cost`
seam: pass-1 solves the incumbent recipe; the model's OWN daily max CA
demand-weighted P1 energy dual (pure lambda — CAISO's scored backcast price
IS the energy-only dual, caiso-137b; zero measured content, rule 13) yields
daily events at ≥ $200; trailing EWMA (30 d half-life, 120-d window,
per-year reset) × β, clipped to [0, 1], is P_hat(d); pass-2 — THE scored
pass — floors BATTERY discharge (PS excluded per the caiso-204 S4
classifier) at max(vom, P_hat × $1,000 park cap) in h18–21 PT only. Audit
sidecar `hourly/adaptive_<year>.parquet`. Registered in the same commit:
cache-key/TIER_TAGS entries, D-5 MechanismSpec, DOF-ledger entry, matrix
family-row def naming (rule 28c, checker clean).

## §B — The A/B, measured (`caiso205_gates.json`)

Control = zero-delta `replay_keeper` of the keeper
(`2026-08-19-caiso205-ctl-headbase`); arm = single `--set` delta
(`2026-08-19-caiso205-arm-adaptive`); both full-span 2023–2025, years
sequential (rule 12; the two invocations were serialized after the cgroup
OOM — §D).

| gate | bar | result |
|---|---|---|
| G-REPRO | every committed keeper hourly sidecar sha256-identical in control | **PASS 9/9** (class_hourly/storage/system × 3; the replay's extra network_/unit_hourly_ files have no keeper counterpart — reported, not gated, §C) |
| G-CAP | no arm-introduced above-$2,000 zone-hour | **PASS** (0) |
| G-SHED | arm shed hours ⊆ control's | **PASS** (none anywhere) |
| G-BAT | battery discharge arm/control ∈ [0.80, 1.25] | **PASS** (1.000 / 0.9921 / 1.000) |
| G-D2 | D-5 attribution row present; no new D-4 rows vs control | **PASS** (row present; D-4 row sets identical — the chp_steam D-4 delta vs the KEEPER's committed JSON is diagnostics-code vintage, present in control and arm alike) |
| G-DOF | ledger delta = exactly the two frozen constants | **PASS** (10 → 11, delta `caiso_adaptive_half_life_days / caiso_adaptive_beta`, measured-physical) |
| MUST-NOT-REGRESS | C3b ≤ 0.20 all years; C8 PASS; C6 attested | **PASS** (scorecards symmetric: control = arm = keeper on every criterion) |

**G-ADA signature (reported, never gated).** 2023: 0 pass-1 spike days,
P_hat ≡ 0, floor ≡ 0 → **arm byte-identical to control** (system sidecar
sha256-equal). 2025: same. 2024: 1 spike day, P_hat max 0.0145, floor max
**$14.5** in 188 Sep/Oct window-hours (> the $5 battery vom, < every
clearing level) → near-inert: battery discharge ratio 0.9921, C3a
12.92 → 12.90 % (side-effect line only — inadmissible as acceptance
evidence either way, caiso-203 ruling), model tail hours 1 → 1. This is the
caiso-204 G-BOOT prediction ($14.5 max floor, byte-identical 2023/2025)
measured exactly.

**Verdict (the precommit's fixed rule):** all gates pass AND the arm is
byte-identical / dispatch-inert → **cell stays I — armed-and-inert at full
magnitude, Phase-1 confirmed.** **NOT a keeper candidate and promotion NOT
recommended**: the arm adds no structure on this keeper's path — the
mechanism is a conduct amplifier whose trigger the keeper's own tail deficit
never fires (the caiso-202 §B compression; tail formation stays the
adjudicated model-class wall). Structural integrity did not improve; there
is nothing here for the "gates regress but structure improves" clause to
weigh. Keeper stays `2026-08-17-caiso-200-h1-memberpanel`; both A/B members
registered per rule 15/16.

## §C — Corrections and notes against interest

1. **G-REPRO scorer correction (pre-read of the gate, post-read of nothing
   else):** the scorer's first draft failed G-REPRO for `network_` /
   `unit_hourly_` files the replay writes but the keeper's committed slim
   set never included. The PRECOMMIT bar is committed-set identity only; the
   clause exceeded it and was removed, extras now reported. All 9 committed
   sidecars were sha-identical in both scorer versions. The precommit's "12
   files" enumeration was also wrong about the set (no reserve_family
   sidecars exist on this energy-only keeper — 9 files); absence is
   symmetric on both sides, as the precommit's own parenthetical provided.
2. **2024 is NOT byte-identical** — the $14.5 floor is a real objective
   perturbation (188 window-hours, −0.79 % battery discharge). "Near-inert"
   is the measured description; the direction-blind gates, not the
   smallness, are what admit it.
3. The keeper-vintage `legitimacy_diagnostics.json` differs from both fresh
   bundles on one D-4 row (chp_steam plant 10034) — a diagnostics-code
   evolution since 2026-08-17, identical in control and arm, so G-D2's
   arm-vs-control basis is unaffected. Flagged here so the next keeper
   promotion regenerates the keeper's diagnostics at HEAD rather than
   discovering this as a surprise.

## §D — Session mechanics recorded

- First launch died on the strict input-completeness guard (`data/clean`
  empty in a fresh container; `capacity_deliverability_limits` needs its
  partition) — fixed by curating the partition; `regenerate_clean.py` also
  run (3/50 unrelated datatypes failed: emissions / emissions-unit-annual /
  egrid — none consumed by this recipe's guard; CO2 is reported-only).
- Concurrent control+arm+regen breached the session cgroup's ~13.3 GiB
  memory cap (control OOM-killed); the solves were serialized. Rule 12's
  parallel-invocation default is subordinate to the box's real memory
  ceiling — on this container class, ONE CAISO 3-year invocation at a time.

## §E — Record changes

- Pair registered: `2026-08-19-caiso205-ctl-headbase` /
  `2026-08-19-caiso205-arm-adaptive` (both NOT-YET, C3a sole FAIL — the
  keeper's own scorecard, unchanged).
- Matrix (CAISO shard): `ercot_storage_adaptive_expectation` cell **stays
  I**, evidence extended with the caiso-205 full-magnitude stamp; §5.2
  caiso-205 block added. Base-row def names the CAISO leg fields (rule 28c).
- `caiso205_gates.json` committed unrewritten; attestations name the owner
  order; DOF ledgers rebuilt (control 10, arm 11).
- Keeper, markers, holdout freeze: UNCHANGED. Lane returns to rest
  (caiso-201 Q1) — the caiso-202/203/204 DO-NOT-REDO lists all carry
  forward, now joined by: **do not re-run this A/B** (the pair is the
  full-magnitude record; new evidence = a keeper whose own path spikes).

Next number: caiso-206.
