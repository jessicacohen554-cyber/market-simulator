# PRE-COMMIT — ERCOT-119: leg-split the EP rebasis — econ bands per-year, peak kept as the standing wall

**Date** 2026-07-27 · **ISO** ERCOT · **Branch** `claude/ercot-119-econ-rebasis-5nkqnh` ·
**Base** the keeper `results/calibration/ercot115_coal_floor_only`
(`2026-07-26-ercot115-coal-marginal-hr`) · **Slug** `ercot119-econ-rebasis` ·
**Written and pushed BEFORE any ERCOT-119 solve**, with the band-scope mechanism commit
(`ercot_offer_hrmult_ep_rebasis_bands` + `offer_curves.band_margin_anchor`). Charter source:
`FINDING-ercot118-gas-rebasis-2026-07-27.md` §4.2 (the C3c-breach diagnosis) and §5.1 (this
lane's definition).

## 1. What this arm changes (single mechanism delta vs ERCOT-118)

ERCOT-118 proved the per-year EP rebasis's mid-merit contribution is real and directional with
the measured gas level kept (crossing-band elevation +5.18/+5.03/+7.00 → +3.34/+2.79/+5.28,
mid-merit C3a legs −3.1/−6.6/−4.3 pp ALL toward actual, C1 16/16 · free 12/12 held) — and was
rejected in the pre-declared ORDINARY mode because repricing the CC **peak** band to its
per-year p50 (2.546/3.501/2.629) deflated the sub-$200 standing scarcity wall: a within-year
top-of-curve max is structurally smaller than the pooled 4.326 three-year always-posted wall,
draining C3c 72→49 / 13→3 with tail legs −6.9/−6.2 pp. The econ-band legs are the fix; the
peak leg is the breach.

This arm adds a BAND SCOPE to the existing mechanism —
`ScenarioConfig.ercot_offer_hrmult_ep_rebasis_bands: list[str] | None = None` (None = all
artifact bands, the ERCOT-118 behaviour, pinned byte-identical by
`TestBandScope.test_none_scope_is_ercot118_byte_identical`; cache-key-registered, neutral at
default) — and arms it at `["econ_low", "econ_high"]`:

- **Rebased per-year (artifact + the keeper's own `offer_curve_deltas`, composition
  preserved):** CC_REGULAR econ_low/econ_high → 0.572/1.105 (2023), 0.552/1.135 (2024),
  0.610/1.202 (2025); CC_CHP → 0.797/1.642, 0.778/1.672, 0.835/1.738.
- **Kept at the keeper's resolved values:** peak (CC_REGULAR 4.576, CC_CHP 3.748 — the pooled
  wall + the keeper's deltas), every conditional-surface `peak_ladder` rung (the re-stamp
  fires only when "peak" is in scope), and the committed band (0.998/1.029; still absent from
  the artifact, §2).
- **Anchor threading is band-scoped (the mechanism's one new seam):** each rebased band
  carries `margin_anchor_<band>` = the year's EP delivered mean (2.5402/2.1067/3.0655
  $/MMBtu), resolved per tranche by `offer_curves.band_margin_anchor`; the un-rebased peak
  and committed markups stay on the ISO window anchor 2.2494 their pooled multipliers were
  identified at. Every band's (mult, anchor) pair sits on ONE basis — the ERCOT-118
  pre-commit §3 principle, now enforced per band. Markup survival at the rebased values:
  econ_high carries the material markup everywhere (1.105–1.738 vs phys 0.941–0.950);
  econ_low clips at phys for CC_REGULAR in all years (0.552–0.610 vs 0.825) and CC_CHP in
  2024, with marginal CC_CHP survivals 2023/25 (+0.004/+0.042 over 0.793). Consequence for
  G0: the margin log line's "tranches on per-class EP anchors" count must be **below
  ERCOT-118's 337** (its peak-rung anchors are gone).

The committed `offer_curve_dam_hrmults_ep_yearly.json` artifact is NOT re-derived (rule 23 —
its source did not change) and the pooled HH−0.50 artifacts stay frozen as the old-basis
record. Unknown scope names hard-fail in the apply function (rule 25 — a typo is never a
silent no-op). Phase 2 (per-year peak QUANTILE LADDERS — the dispersion, not the p50) is NOT
this arm and happens only if the owner later asks.

## 2. The COMMITTED band — residual pre-registered explicitly, ex ante

Unchanged from the ERCOT-118 pre-commit §2 (data destroyed, not chosen): Min Gen Cost was
dropped by the owner-ordered 2026-07-22 raw slimming, `ercot_dam_offers.parquet` was never
committed and is not rebuildable, all 2023 publications are past the free MIS retention
window, and the credentialed archive was owner-declined. The CC LSL block therefore keeps
pricing ~+$2.6–4.0 above its measured level in 2023/24 in the hours it prices (its markup leg
is inert either way — resolved 0.998 < phys 1.006 clips to 0).

**Pre-registered residual:** even on full success, the 2023/24 crossing-band elevation is
expected to retain roughly **+$2.8–3.3** (the ERCOT-118 finding §4.3's attribution of the
un-rebasable committed block plus the untouched CT/ST/coal-passthrough surfaces). The ≤$2.0
charter line of ERCOT-118 is therefore NOT re-registered here — the decomposed gate (a) below
is the achievable econ-leg yardstick. A print materially BELOW ~+$1.0 in 2023/24 would exceed
what the scoped mechanism can explain and is grounds to investigate before celebrating, not
evidence of skill. The committed band remains a DATA decision for the owner (credentialed
ERCOT archive vs partial 2024/25 Min-Gen-Cost intake vs accept the residual); this lane does
not fetch, transform, or approximate it.

## 3. The arm (single solve, three years, one invocation — R-ALLYEARS)

`replay_keeper` on the ercot115 keeper with exactly three `--set` deltas (the ERCOT-116/118
joint-arm gate protocol — the measured coal envelope is ARMED, never re-tuned around):

```
python scripts/replay_keeper.py results/calibration/ercot115_coal_floor_only \
  --out-dir results/calibration/ercot119_econ_rebasis_joint \
  --set ercot_thermal_dam_availability_coal=true \
  --set ercot_offer_hrmult_ep_rebasis=true \
  --set 'ercot_offer_hrmult_ep_rebasis_bands=["econ_low","econ_high"]' \
  --note "<arm note>"
```

Full span 2023 2024 2025 via meta, ONE invocation, years sequential (rule 12). Keeper
`offer_curve_deltas` and every other keeper flag unchanged. The list-valued `--set` is JSON
and routes through BOTH channels (solve kwarg + prb_overrides); the stomp WARNINGs and the
recorded `run_config.json` are checked for channel agreement.

**G0 (armed and biting), checked before scoring:**

- `coal econ marginal-HR floor` 3/3 and `COAL plant-grain redistribution` 3/3 (the keeper's
  own overlays).
- `ERCOT DAM offer hr-mult EP rebasis` 3/3 with `scope=econ_low,econ_high` and EXACTLY 4 band
  replacements per year (2 classes × 2 econ bands — the line must name ONLY the scoped
  bands; a 6-band line means the scope silently failed, voiding the arm).
- The margin line's `tranches on per-class EP anchors` count present and **< 337**.
- `run_config.json` records `ercot_offer_hrmult_ep_rebasis: true`,
  `ercot_offer_hrmult_ep_rebasis_bands: ["econ_low", "econ_high"]`, the scoped curve (econ
  rebased, peak 4.576/3.748 kept, `margin_anchor_econ_*` keys only — no class-wide
  `margin_anchor`, no `margin_anchor_peak`).
- BITE — coal moves > 0.5 TWh vs the keeper in at least one year (the envelope leg;
  ERCOT-118 measured +1.2/+2.7/+10.2 TWh).

**Environment parity:** fresh container; the gtc-limits clean partition is absent so the
solver falls back to `static TTC kept` — the SAME fallback state the ercot115 keeper and the
ercot116/117/118 arms were solved under (like-for-like; verified in the solve log 3/3).
highspy pinned 1.14.0, pandas 3.0.3, pyarrow 24.0.0 per the family setup. Comparisons to all
four baselines are therefore state-matched. Known pre-existing failures on clean origin/main,
reported not chased (this lane touches neither):
`tests/regression/test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
(30065460 vs pinned edbc1b1 — also verified unchanged by this branch's mechanism commit, i.e.
the new field is cache-neutral at default) and the 8
`tests/iso/ercot/test_ercot_offer_surface_cleared_share_steam_rt.py` failures (the test file
references `ercot_offer_surface_cleared_share_rt_steam_path` /
`ercot_shoulder_online_span_steam`, ScenarioConfig fields that do not exist on main).

## 4. Scoring — fixed before the solve

1. `scripts/probes/ercot116_seasonal_shape.py` **VERBATIM** (keeper =
   `ercot115_coal_floor_only`, arm = this bundle) — G1/G2/G3/BITE as coded.
2. `scripts/probes/ercot118_gas_rebasis_score.py` **VERBATIM** (same yardstick construction:
   crossing-band elevation, C3c, C1 counts, the G3-trap C3a decomposition), with `--also`
   `ercot116_coal_avail_on_keeper` `ercot117_gas_basis_probe` `ercot118_ep_rebasis_joint` —
   all on disk, no extra solves — to isolate the leg-split's own contribution under the
   identical envelope and against both the full-surface ablation and the full (peak-included)
   rebasis.
3. No new scorer, no threshold edits. Its §F pre-registered ≤$2.0 line is superseded for this
   arm by gate (a) below (declared here, before solving; §2 states why).

## 5. PRE-REGISTERED GATES (decomposed, achievable — fixed now)

- **(a) Crossing-band retention.** The arm's [15,25) elevation retains ≥ 80 % of the
  ERCOT-118 arm's drop vs the keeper in EVERY year: keeper +5.18/+5.03/+7.00, ERCOT-118
  +3.34/+2.79/+5.28 (drops −1.84/−2.24/−1.72), so the gate is **≤ +3.71 (2023) / +3.24
  (2024) / +5.62 (2025)**.
- **(b) C3c preservation — the leg-split's whole point.** C3c within **±5 h of the keeper in
  EVERY year** (keeper: 72/13/1 of RT 181/53/31).
- **(c) C1 held.** 16/16 · free 12/12, exactly the keeper's counts.
- **(d) G1/G2 pass** (the envelope shape gates) in every year, as coded in
  `ercot116_seasonal_shape.py`.

**THE G3-C3a TRAP, adjudicated in advance — carried over VERBATIM from the ERCOT-118
pre-commit §5:** G3 is run exactly as coded and reported. If it fails **solely** via C3a
moving toward actual in the $10–40 bands — the `ercot118_gas_rebasis_score.py` decomposition
splits each year's ΔC3a into the actual-$[10,40) mid-merit leg vs the tail leg, and prints
whether the band moved TOWARD actual — that outcome is **pre-declared ESCALATE-TO-OWNER**
with the decomposition: not a revert signal, not grounds to edit the gate, not
self-promotion. **Any other G3 failure mode** (C3c breach, or a C3a move away from actual,
or a tail-carried delta) **is an ordinary rejection.**

Registered expectations, falsifiable (beyond the four gates):

- **P1.** The mid-merit ΔC3a legs stay toward actual in every year, magnitude comparable to
  ERCOT-118's (−3.1/−6.6/−4.3 pp) — the econ legs owned that movement, and they are
  unchanged here.
- **P2.** The tail legs SHRINK in magnitude vs ERCOT-118's (−6.9/−6.2/−2.9 pp) in every year
  — they were the peak-deflation signature, and the peak wall is restored.
- **P3.** The committed-band residual keeps the 2023/24 elevation above ~+$1.0 (§2 — a lower
  print is an investigation trigger, not a win).

## 6. Decision rule (fixed now)

- Gates (a)–(d) all pass and G3 fails only in the pre-declared C3a-toward-actual mode (or
  passes) → this is the shape-clean Phase A variant. Write the FINDING and **recommend to
  the owner JOINTLY:** (1) re-arming the measured coal envelope (the ERCOT-116 exit
  criterion), (2) promoting the scoped rebasis, and (3) the committed-band data decision
  (credentialed ERCOT archive vs partial 2024/25 Min-Gen-Cost intake vs accepting the
  residual ~+$2.8–3.3 in 2023/24). **STOP for owner sign-off** —
  `frontend/data/backcast/keepers/ERCOT.json` is never touched without it (the ercot-115
  process-breach lesson).
- Any C3c breach (gate (b) fails) → **ordinary rejection**, finding records it, keeper
  unchanged.
- Gate (a) misses with (b)–(d) holding → NOT-YET finding; the residual owner is named from
  the decomposition (committed band per §2, or a genuinely smaller econ-leg contribution
  than ERCOT-118 measured), never tuned around.
- Register the completed solve on the dashboard the same session whatever the outcome
  (rule 15 R-DASHBOARD): `legitimacy_diagnostics.py` → `dashboard_add_run` →
  `build_manifest` → `check_registry_payload_parity`; slim-bundle commit (hourly/ + meta +
  metrics + run_config + legitimacy_diagnostics, not dispatch/); run payload over `git push`
  with blob verification; expect ~1 auto-prune under the top-15 retention.

## 7. Declared-not-counted

No price-MAE argument in either direction. The C3a deepening vs the keeper (if any) is the
designed exposure of the keeper's netted scarcity-LOW error (ERCOT-117/118), reported via the
decomposition — not evidence against the rebasis direction and not a number this arm is
graded on outside the pre-declared trap adjudication. CLOSED and not reopened here:
everything in the ERCOT-116/117/118 closed lists, the pooled HH−0.50 artifacts (frozen),
`ercot_zonal_gas_basis` ablations as fixes, the West/Panhandle topology split, and the
holdout years 2022/2019/≤2021/H1-2026 (rule 22 — no solve, no scoring, no registration
touches them; this arm's `--year` span is exactly {2023, 2024, 2025}).
