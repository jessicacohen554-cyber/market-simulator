# ERCOT AS co-opt overlay-replacement — staged prompt pack (2026-07)

Ready-to-paste handoff prompts, one per stage of
`docs/handoffs/ercot-as-coopt-plan-2026-07.md`. Each is self-contained: drop it
into a fresh Claude Code session on this repo. Ordered 0→5; stages 1/2/3 are
mutually independent, stage 4 needs 1+2, stage 5 needs 4.

**Shared rules every prompt inherits (CLAUDE.md):** right structure first, tune
the level second (#1); no Python loops over hours in LP construction (#2);
measured data only as a reproducible forward-regenerating input, never an
outcome pinned to the residual (#10/#12/#13); a structurally-correct mechanism
stays even if it worsens a metric — root-cause the dip, never revert for the
residual (#1/#11); every completed run registered on the dashboard and
committed in the same session (#15); all scoreable years in one bundle (#16);
DOF ledger + ablation twin for keepers (#21); derive scripts frozen against
residuals (#23); no off-registry tuning channels (#24). **P2 / AS-aware
commitment is SHELVED (ercot27 verdict) — do not resurrect it in any stage.**

---

## Stage 0 — Overlay decomposition + ex-overlay re-baseline

```
Re-baseline the ERCOT keeper without the measured DAM-AS overlay and decompose
what the overlay actually carries, BEFORE any new mechanism is built. This is
WS-F / stage 0 of docs/handoffs/ercot-as-coopt-plan-2026-07.md (read it first,
plus the ercot32 and ercot27 entries in docs/calibration-log.md dated
2026-07-03).

Context: the current ERCOT keeper is 2026-07-03-ercot32-ordc-total-rtolcap
(bundle results/calibration/ercot32_statmode_2026-07). Its calibration_flags
carry ercot_dam_as_overlay=True (post-solve adder = measured binding DAM AS
MCPC, results/scarcity.py:ercot_dam_as_overlay_series, 2024+ hours, threshold
$150). ercot32's root cause (4) already showed overlay hours realized DA ~
$599/$511 vs RT ~ $205/$316 (Jan/May 2024) — a DAM-vs-RT settlement boundary an
RT-scored co-opt should NOT reproduce.

Task:
1. Solve the ercot32 recipe EXACTLY (same run_config.json / calibration_flags,
   P1-only, --year 2023 2024 2025, one bundle) with the single delta
   ercot_dam_as_overlay=False. Register it on the dashboard as a probe
   ("ercot33 ex-overlay baseline" or next free label) — this is the clean
   baseline every later stage compares against.
2. Decompose every overlay-active hour of the keeper into:
   (i) RT-supported scarcity — RT actual also elevated (>$150) that hour;
   (ii) DA-boundary premium — realized DA >> RT (failure mode F6);
   (iii) hours within the May-2024 discretionary-procurement uplift windows
   (run163 finding: measured up-AS ~8.8 GW vs driver-formula ~7.4 GW on the
   acute evenings — failure mode F7). Report the $-share of the overlay's
   annual dw-LMP contribution in each bucket, per year and per month
   (2024/2025; 2023 is inert, from_year=2024).
3. Write the numbers into a short FINDING file in results/calibration/ and cross
   link it from the plan doc. The (ii)+(iii) share is the overlay's
   non-reproducible component — the stage-4 gates treat it as out of target.

Honesty gate: this is measurement, not calibration. No flag other than the
overlay changes; no retuning. Deliverable: the ex-overlay probe on the
dashboard + the decomposition table, committed and pushed in-session.
```

---

## Stage 1 — WS-A: forward online-responsive supply (the RTOLCAP analogue)

```
Build the forward analogue of ERCOT's measured RTOLCAP/RTOFFCAP reserve-supply
cap — the last AS-path lever with NO forward analogue. Read first:
docs/handoffs/ercot-as-coopt-plan-2026-07.md §3-§4 (WS-A and the failure-mode
ledger F1-F7), docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md, and
scarcity.ercot_rtolcap_supply_cap_mw (results/scarcity.py:1080 — note it
returns None when no measured parquet covers the year, so forward years run
UNCAPPED today and the whole ORDC-era supply re-scope goes inert).

Design (derived committed-share x ramp-capability):
  RTOLCAP_fwd(t)  = sum_c online_share_c(netload_pctile(t), hod(t), season(t))
                    x ramp10_cap_c(year)  +  online_storage_power(t)
  RTOFFCAP_fwd(t) = sum_{c in quick-start} offline_share_c(...) x ramp10_cap_c
- online_share_c: per responsive class, share of installed capacity online as a
  function of net-load percentile / hour / season, derived from the committed
  CAMPD unit extracts by a NEW derive script (scripts/data/derive_*, the
  MAINTENANCE_MONTHLY_SHAPE / ST_GAS-drag family). Rule #23: it re-derives only
  on source-data updates — cite the data in the script header.
- ramp10_cap_c: 10-minute ramp capability per online MW from the fleet arrays'
  unit physics — regenerates as the fleet evolves.
- Coefficients/constants in constants.py (ERCOT_RTOLCAP_FWD_*), flag
  ercot_reserve_supply_forward (default off) in ScenarioConfig (#24).
- Seam: make ercot_rtolcap_supply_cap_mw mode-aware exactly like
  ercot_load_resource_reserve_credit_mw (G4): backcast -> measured parquet
  (byte-identical); forecast, or the probe flag on -> the formula. Vectorized,
  no per-hour Python loop.

HARD identification gate BEFORE any dispatch run (anti-F1, the ercot27
artifact): a validation script (scripts/validate_ercot_rtolcap_forward.py,
mirror of validate_ercot_as_forward_requirement.py) comparing formula vs
measured RTOLCAP/RTOFFCAP on 2023-2025 must show (a) annual mean within +/-10%
(measured ~13.5/16.7/19.1 GW), (b) sane p10/p50/p90 band, (c) coverage ratio
(RTOLCAP / total AS requirement) with median ~2x. A construction landing near
1.0x coverage is the ercot27 exact-coverage artifact -> rejected at the script.
Anti-F3/F4: the formula never reads the LP's commitment/output state and never
couples reserve to P (no R - rho*P rows).

Then the one-delta backcast probe (run163 pattern): the stage-0 ex-overlay
baseline recipe + ercot_reserve_supply_forward=True (measured cap -> formula,
the ONLY delta), --year 2023 2024 2025, register on the dashboard. Gate: the
formula-capped run tracks the measured-capped baseline (annual dw within
~$2, acute days and tail counts close), differences root-caused in the writeup.

Tests: trivial case first (1 gen, 1 zone, 24 h); formula responds to drivers
(deeper net-load trough -> lower cap); backcast byte-identical with the flag
off; coverage-ratio gate unit-tested. Deliverable: derive script + seam + 
validation script + probe on the dashboard + a docs/ handoff note, committed
in-session. Honesty gate: fit to the measured RTOLCAP QUANTITY series only —
nothing on the path reads LMP/RTSPP/MCPC/RTORPA.
```

---

## Stage 2 — WS-B: storage AS duration gates (finish G5)

```
Add the published per-product duration requirements to the endogenous storage
energy-vs-AS split so it can replace the measured battery AS-award treatment in
the ERCOT keeper. Read first: docs/handoffs/ercot-as-coopt-plan-2026-07.md
WS-B, docs/ercot-storage-as-endogenous-2026-06.md (G5, run164), and the ercot32
calibration-log entry root causes (1) and (2).

The gap: ercot_storage_as_endogenous holds 2.1-2.4x the measured battery AS
award (2023: 2,625 vs 1,249 MW mean) because nothing stops a short-duration
battery from selling long-duration products — ERCOT requires ECRS sustained 2 h
and Non-Spin 4 h (Nodal Protocols; cite exact sections in
docs/parameter-citations.md). Build the LP-linear, VECTORIZED duration gate
linking cleared storage AS to state of charge (schematically
sum_p dur_p * R_storage[p,t] <= SOC[t], alongside the existing power-cap
competition in the shared-headroom rows — adapt to the actual variable layout
in model/dispatch.py; durations from constants.py, e.g.
ERCOT_AS_PRODUCT_DURATION_H). No per-hour Python loop (#2).

Validation is a QUANTITY comparison (scripts/probes/storage_as_split.py):
modeled endogenous split vs measured 60-Day DAM award MW, per year — target
0.8-1.3x mean. Never a price fit.

Then the one-delta probe: the stage-0 ex-overlay baseline recipe with the
measured storage treatment swapped for the endogenous one AS ONE CONSISTENT
SWAP — storage_as_commitment, ercot_storage_as_reserve AND
ercot_storage_as_product_credit all off; ercot_storage_as_endogenous on. The
ercot30 blow-up (+87% 2023) documents what mixing the treatments does: docking
the cap without netting the requirement over-withholds thermal — never mix.
--year 2023 2024 2025, register on the dashboard, compare to the stage-0
baseline (annual/monthly dw, acute days, tail, C5 storage metrics).

Tests: duration gate binds for a 1-h battery offered 4-h NonSpin (trivial 24-h
case first); split ratio in band; flag-off byte-identical; RTOLCAP-cap
interaction unchanged (cleared storage AS still counts under the cap — RTOLCAP
includes online batteries). Deliverable: the gate + probe on the dashboard + a
docs/ handoff note, committed in-session.
```

---

## Stage 3 — WS-E: HSL completion remainder (NP6 2024/25 intake)

```
Complete the ERCOT HSL intake for 2024/2025 (the P4 remainder). Read first:
docs/handoffs/ercot-as-coopt-plan-2026-07.md WS-E,
docs/forecast-methodology-gaps-2026-06.md G7, and
src/market_sim/data/renewables.py (_UNCURTAILED_FALLBACK_ISOS,
_reference_curtailment_rate, hsl_potential_mw): ERCOT 2024/25 have no NP6 HSL
parquet, so the dispatch runs on the G7 reference-rate gross-up fallback.

Task:
1. Attempt to fetch the published ERCOT NP6-732/737 wind+solar production
   (HSL) reports for 2024 and 2025 and intake them through the data contract
   (data-intake skill: schema-first, raw download under data/raw/ercot/,
   builder script scripts/build_* mirroring the existing HSL builder for
   2023). EGRESS CAVEAT: ERCOT MIS has 403-blocked before (NP6-576-ER,
   ercot27 WS3) — if blocked, document the attempt (docs/ + the plan doc) and
   stop; the G7 fallback is already forward-admissible, so this is a fidelity
   upgrade, not a blocker for stage 4.
2. If the data lands: confirm hsl_potential_mw now prefers the built parquet
   for 2024/25, the LP receives uncurtailed potential as the renewable upper
   bound, and curtailment stays ENDOGENOUS (never scale potential so delivered
   lands on actuals — the resolved anti-pattern, #12). Report the
   modeled-vs-reported curtailment ratio as a DIAGNOSTIC (#11).
3. Note the AS interaction for the stage-4 writeup: the AS requirement drivers
   (scarcity.ercot_as_forward_drivers) and the WS-A net-load shares are built
   from wind/solar series; with real HSL the 2024/25 drivers reflect true VRE
   variability in oversupply hours. Quantify the driver delta (sigma_fe,
   ramp_up percentiles) old-vs-new; if material, the ERCOT re-solve happens in
   stage 4, not here.

Deliverable: the intake (or the documented blocked attempt), schema + builder +
tests per the data contract, committed in-session.
```

---

## Stage 4 — Integration: the overlay-replacement run (ercot40)

```
Run the overlay-replacement backcast: the endogenous multi-product AS co-opt
stack REPLACING the measured DAM-AS overlay, scored on the same benchmarks as
the keeper. Read FIRST and follow exactly:
docs/handoffs/ercot-as-coopt-plan-2026-07.md §5 (out of scope) and §6 (run
design, gates G-1..G-7, pre-committed keeper decision), plus the stage-0
FINDING decomposition and the stage-1/-2 probe writeups.

Run design ("ercot40" or next free label): the ercot32 recipe EXACTLY (P1-only,
measured ASPLANNP433 requirements — admissible; ercot_load_resource_reserve,
ercot_ordc_total_reserve, ercot_ecrs_conservative_deployment, gas_hh_monthly
_shape etc. all unchanged) with ONLY these deltas:
  1. ercot_dam_as_overlay=False
  2. ercot_reserve_supply_forward=True   (stage 1, formula in backcast)
  3. measured storage treatment -> ercot_storage_as_endogenous (stage 2's
     one-consistent-swap)
--year 2023 2024 2025, one bundle (#16). ercot_rtordpa_overlay STAYS (G2
bridge — out of scope). If the combined run misbehaves where the single-delta
probes passed, bisect with intermediate probes and register them (#15).

Score gates G-1..G-7 from the plan §6 verbatim (RT benchmark, DA diagnostic row
alongside): acute-day reproduction; hold 2025/Aug-2024/2023-H2; NO broad
elevation (the anti-ercot27 gate G-3 — Feb-2023 unchanged, no month gains >+$5
where measured RTOLCAP p50 exceeds the ORDC curve reach); tail structure
intact; quantity fidelity; one-event-one-channel min-overlap audit vs RTORDPA;
full G-7 attribution ledger mapping every residual vs ercot32 to {DA-boundary
F6, discretionary uplift F7, energy-base (out of scope), genuine miss}.

Keeper decision — pre-committed in the plan, apply it, don't relitigate:
promote if G-3/G-5/G-6 pass and every G-1/G-2/G-4 miss has a named root cause
in the ledger, EVEN IF C3a/C3b worsen vs ercot32 (#1). On promotion: overlay
demoted to explicitly-labelled default-off diagnostic; DOF ledger lists the
WS-A/WS-B constants with identification sources; register the zero-forcing
ablation twin (#21); structural promotion scored leave-one-year-out within
2023-2025 (#22 — holdouts 2022/H1-2026 untouched). If G-3 or G-6 fail:
rejected probe, registered, failure added to the plan's ledger — do NOT add a
tuned mechanism to pass.

Deliverable: the bundle + attestation + dashboard registration (+ keeper swap
and calibration-keeper-auditor run if promoted), calibration-log entry, docs
synced, all committed and pushed in-session (#15). Push via
mcp__github__push_files per CLAUDE.md (avoid the 413 loop).
```

---

## Stage 5 — Forward-mode proof (RTC+B, zero measured AS reads)

```
Prove the ERCOT AS path is fully forward-native: a forecast-mode run in the
RTC+B regime with every AS input regenerating from forward drivers. Read
first: docs/handoffs/ercot-as-coopt-plan-2026-07.md stage 5, and the mode-aware
seams: ercot_as_forward_requirement_mw (G3), ercot_load_resource_reserve_credit
_mw (G4), ercot_rtolcap_supply_cap_mw forward branch (WS-A),
ercot_storage_as_endogenous (G5+WS-B).

Task:
1. Run a forecast-mode ERCOT scenario (mode="forecast", first forecast year,
   ercot_market_regime -> "rtcb") with the stage-4 stack + the forward
   branches ON: ercot_as_forward_requirement=True, forward LR enrollment,
   forward RTOLCAP formula, endogenous storage AS. Confirm the DAM-AS and
   RTORDPA overlays are regime-gated inert (they already are for year >= 2026).
2. AUDIT zero measured AS reads on the forecast path: no
   ASPLANNP433/NP3-911/60-Day-DAM/ordc_reserves parquet is opened in forecast
   mode (assert via a test that monkeypatches the loaders to raise, or an
   strace-style probe) — the CLAUDE.md #10 admissibility proof.
3. Sanity-check forward response direction on a 2-scenario A/B (higher VRE
   build): AS requirements rise (G3 drivers), RTOLCAP_fwd falls in trough
   hours (WS-A), scarcity incidence rises, storage tilts between energy and AS
   with fleet growth (G5 saturation). Directions only — no calibration.
4. Optional: one ensemble sweep (market-sim ensemble, WEATHER_YEAR_POOL) to
   confirm the AS stack is stable across weather draws.

Deliverable: the audit test committed, a short docs/ note recording the
forward-response A/B directions, and a /sync-docs pass updating the
methodology spec's G1 status (flagship gap CLOSED, with the F6/F7 residuals
documented). No dashboard registration (forecast runs aren't backcast bundles);
commit in-session.
```
