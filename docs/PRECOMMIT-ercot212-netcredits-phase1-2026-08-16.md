# PRECOMMIT — ercot-212 Phase-1: the reserve-supply-cap credit-netting consistency repair (`ercot_reserve_supply_cap_net_credits`), armed A/B on the keeper recipe

**Session ercot-212, 2026-08-16, branch `claude/ercot-reserve-basis-x3-gjpsh9`.
Pushed BEFORE any solve.** Entered under the Phase-0 viability rule
(`docs/PRECOMMIT-ercot212-reserve-basis-phase0-2026-08-16.md` §4, all of
V1–V5 PASS — `docs/FINDING-ercot212-reserve-basis-phase0-2026-08-16.md` §3).
Keeper: **`2026-08-15-ercot204-rule26-delete`**; the keeper cannot change
in-session — the outcome is a promotion RECOMMENDATION at most (X-3).

## §1 The single delta

One new `ScenarioConfig` boolean, **`ercot_reserve_supply_cap_net_credits`**
(default **False** — keeper-reproducing), registered in
`_CACHE_KEY_OPTIONAL_FIELDS` with a tier tag, matrix row added in this same
landing (rule 28c). When True, in `_ercot_multiproduct_design`, the measured
reserve-supply cap rows are netted by the SAME credit series the ORDC
total-reserve family nets off its requirement, under the SAME gates:

```
net(t)  = lr(t)·[ercot_load_resource_reserve armed]
        + sas(t)·[ercot_storage_as_reserve armed, non-endogenous storage]
cap'(r,t) = max(cap(r,t) − net(t), 0)      # both tiers — the credited MW are online
```

Scope: the **measured-cap branch only** (backcast mode with
`ercot_reserve_supply_forward` off) and only when `ercot_ordc_total_reserve`
is armed (the construction whose requirement carries the credits). The WS-A
forward cap is untouched (it composes storage explicitly and carries no LR
term — Phase-0 finding §3). The credit series are computed ONCE and shared
between the cap netting and the requirement netting, so the two sides cannot
drift.

**Identification (rules 13/20/23): zero fitted scalars.** Every input is an
already-armed measured series or the armed curve. The repair claim is
arithmetic consistency: RTOLCAP/RTOFFCAP telemetry contains the online ESR
and Load-Resource MW the model credits on the demand side (the code's own
documented reading, `spec.py` / `ercot_load_resource_reserve_mw`); the same
MW must not also ride the supply cap, or the marginal level reaches
`cap + credits` — the measured +1.7/+1.0/+2.4 GW wedge of Phase-0 §1. Netting
the AWARD series is a lower bound on the true capability components —
conservative in the direction of under-netting.

## §2 Predictions, stated ex ante (from the Phase-0 out-of-LP construction)

* Cap contact (and hence sidecar `ordc_adder` writing) expands from 42/2/1
  hours toward the real dip set — upper bound 571/190/67 hours
  (cap_all < 10,700, live), the excess over today's set carrying mostly
  sub-$1 values.
* Implied incidence on the armed flat curve at the netted basis
  (min(10,700, RTOLCAP+RTOFFCAP)): **2023 175 h>$1 / 37 h>$100; 2024 45 / 6;
  2025 5 / 0** vs settled published 294/17, 78/4, 14/0. The LP realization
  should land at-or-below these (model headroom can bind below the cap;
  the single-level curve prices the floor at the total, not online, tier).
* **2023 moves and is side-effect-reported at full magnitude under Q-B/R-A
  phrasing, never a basis, never a gate** (X-3): the 42 cap-bound deep-tail
  hours re-price LOWER on the curve (level drops by ~credits ≈ 2.4 GW), so
  the 2023 tail RISES toward actual (C3c tail count 58 → up; C3a-2023 −33.2 %
  → smaller magnitude expected). Under Q-B these are reported, not spent.
* Dispatch effects: in newly cap-bound hours the fleet holds up to ~net(t)
  LESS reserve — freed headroom flows to energy; expected direction is mid-band
  softening and possibly REDUCED shed in the 2023/2024 scarcity hours (G-SHED
  watches the adverse direction; reductions are reported).
* 2025 stays under-produced vs published on counts (5 vs 14) — the
  parameter-keyed residual B0 assigned to the 2025-vintage table; NOT chased
  here (V3: no table arming).

## §3 Kill gates — direction-blind, inherited from the ercot-202/204 family

Measured on the armed member vs the control replay; ANY kill ⇒
REJECTED-AS-ARMED (verdict stands regardless of residual direction):

| gate | rule |
|---|---|
| **G-REPRO** | control replay (flag OFF at HEAD with the new field present) reproduces the keeper's 12 hourly sidecars sha256-identical — proves the field + code path inert-when-off AND the environment right. Kill if any sidecar differs. |
| **G-SHED** | shed (slack) hours must not INCREASE in any year (keeper 4/1/0). Decreases and hour-list changes are reported, not gated. |
| **G-C3c** | the 2023 model tail (scorer basis, actual 181) must not move AWAY from actual; likewise 2024 (22/53) and 2025 (1/31). Movement toward actual is reported, never a promotion basis. |
| **G-SPUR** | spurious mid-band hours (family definition) must not increase by more than 5 in any year (keeper 9/11/0). |
| **G-SPAN** | max per-class annual energy delta ≤ 2.0 % of ISO load in every year. |
| **G-COAL148** | coal-above-ceiling rise ≤ 0.5 TWh in every year (keeper 0.1213/0.1838/0.1095). |
| **G-OWNER** | C3a-2024, C3a-2025, C3b-2024 must remain PASS. |
| **G-DOF** | zero new tuned scalars: ledger `n_residual` stays 6; the new boolean carries no numeric value. |
| **G-D2** | no NEW D-4 off-window-binding failure row (the 3 pre-existing `reliability_floor × CT_PEAKER` rows carry). |

**LOYO:** parameter-free rule (no fitted value exists to identify), so
structurally N/A with per-year deltas reported in its place (ercot-173/188
precedent).

## §4 Execution

* Environment: verified byte-equal to the keeper record (highspy 1.14.0,
  pandas 3.0.3, pyarrow 24.0.0) — `./.venv/bin/python` directly, never
  `uv run` (the ercot-204 lesson).
* Control: `scripts/replay_keeper.py results/calibration/ercot204_rule26_delete
  --out-dir results/calibration/ercot212_control_A` (full span, years
  sequential within the one invocation — rule 12).
* Armed: same + `--set ercot_reserve_supply_cap_net_credits=true`,
  `--out-dir results/calibration/ercot212_netcredits_B`.
* Both runs register on the BACKCAST registry with payloads (rules 15/16; run
  payloads over `git push`), matrix 28b cell verdict + the 28c row in the same
  landing, calibration-log entry under ercot-212.

## §5 Roster effects, named ex ante (the retention directive replaces top-15)

ERCOT's registry currently holds ONE run (the keeper, protected). A live A/B
registers normally → 3 runs, no eviction. If the adjudication is
REJECTED-WHOLESALE, the pair is pruned in this same session with
`scripts/prune_iso_runs.py`; the finding, matrix cell and log entry remain
the durable record either way (dispatch roster duty).

## §6 Decision rule (direction-blind)

Reads ONLY the §3 gates: all live gates PASS ⇒ register both + **RECOMMEND
promotion** (the keeper does not change in-session); any kill gate FAILS ⇒
**REJECTED-AS-ARMED**, register both, prune per §5, cell verdict `R`. Residual
direction — 2023 included — is never consulted by this rule; all residual
moves are reported at full magnitude under the Q-B/R-A phrasing.

## §7 Fences

Rule 22: {2023, 2024, 2025} only, no marker sought. Rule 25: ERCOT only —
the field gates on the ERCOT multiproduct design alone. Rule 27: edits local,
exact bytes pushed, ≥300-line pushed files blob-verified. Rules 5/24: the new
field is registered (ScenarioConfig + cache key + matrix row); no env-var
knob, no off-registry channel. No new workflows; solves run in-session.
`check_mechanism_matrix.py` exit 0 before landing. No PR (push-and-stop; the
owner merges).
