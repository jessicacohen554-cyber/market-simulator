# ERCOT multi-product AS co-optimization — overlay-replacement plan (2026-07)

**Date:** 2026-07-04
**Scope:** the flagship forward-methodology gap (G1 of
`docs/forecast-methodology-gaps-2026-06.md`): the forward analogue of the
measured ERCOT DAM-AS overlay (`ercot_dam_as_overlay_series`,
`results/scarcity.py:536`). This is a **design/plan document — no model code
changed.** Companion prompt pack:
`docs/handoffs/ercot-as-coopt-prompts-2026-07.md`.
**Reads first:** `docs/ercot-multiproduct-as-coopt-2026-06.md` (run159),
`docs/ercot-as-forward-requirement-2026-06.md` (G3 / run163),
`docs/ercot-as-aware-commitment-2026-06.md` (run160, rejected),
`docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md` (run161),
`docs/ercot-load-resource-rrs-forward-2026-06.md` (G4 / run165), and the two
2026-07-03 calibration-log entries: **ercot27** (rejected AS-aware P2 probe) and
**ercot32** (current keeper, `2026-07-03-ercot32-ordc-total-rtolcap`).

---

## 1. Objective

Make the endogenous multi-product AS co-optimization — not the measured binding
DAM AS MCPC read from disk — the mechanism that forms ERCOT's AS-scarcity price
signal, proven by a **backcast 2023–2025 in which the co-opt REPLACES the
measured DAM-AS overlay**, scored on the same C1–C5 benchmarks as ercot32.
Keeper decision per CLAUDE.md #1: the structurally-faithful run wins even if a
metric dips; every dip is root-caused, never closed by re-tuning a mechanism to
the residual.

**What "replace" means precisely.** ercot32's `calibration_flags` carry
`ercot_dam_as_overlay=True` (post-solve $/MWh adder from the measured
`binding_mcpc`, 2024+ hours, threshold $150). The target run sets it **False**
and lets the already-built P1 multi-product co-opt stack — plus the new pieces
below — form the same scarcity endogenously. The RTORDPA overlay
(`ercot_rtordpa_overlay`, 2023's out-of-market deployment pricing) is a
**separate, legitimate BACKCAST-BRIDGE (G2)** and is *not* in scope to remove:
its forward analogue is RTC+B itself, and it is already regime-gated off
forward.

## 2. Current state — what is already built (do not rebuild)

The June docs describe a design; most of it has since landed. The staged prompts
must start from this inventory, not from G1's original text.

| Component | Flag / anchor | Status | Evidence |
|---|---|---|---|
| Multi-product stack (RegUp/RRS/ECRS/NonSpin, additive shared headroom, fast/all tiers) | `ercot_multiproduct_as_coopt`; `dispatch._build_reserve_rows` (`headroom_eligible/products/extra_cap`) | **BUILT, in keeper** | run159; ercot32 |
| Lumped ORDC total-reserve family (RTORPA) layered on the products | `ercot_ordc_total_reserve` (ALL-CLASS family, `balance_reserve_class=-1`) | **BUILT, in keeper** | ercot32 |
| ECRS conservative-deployment design (2023-06-10 → 2024-07-31 at-cap step) | `ercot_ecrs_conservative_deployment` | **BUILT, in keeper** | ercot27 WS2 research |
| Measured RTOLCAP/RTOFFCAP reserve-supply cap + ORDC-regime additive adder | `ercot_reserve_supply_cap`; `scarcity.ercot_rtolcap_supply_cap_mw` | **BUILT, in keeper — backcast-only** (returns `None` forward) | run161; ercot32 |
| Forward AS requirement formulas (G3) | `ercot_as_forward_requirement`; `scarcity.ercot_as_forward_requirement_mw` | **BUILT, default-off** (keeper reads measured ASPLANNP433 — admissible) | run163 |
| Endogenous storage energy-vs-AS split (G5) | `ercot_storage_as_endogenous` | **BUILT, default-off — rejected from keeper pending duration gates** (holds 2.1–2.4× measured award) | run164; ercot32 root cause (1) |
| Measured storage AS treatment (cap-dock + requirement netting + credit, internally consistent) | `storage_as_commitment` + `ercot_storage_as_reserve` + `ercot_storage_as_product_credit` | **in keeper** (the ercot30 blow-up documents why netting must accompany docking) | ercot32 |
| Load-resource RRS-UFR credit, mode-aware (G4) | `ercot_load_resource_reserve`; `scarcity.ercot_load_resource_reserve_credit_mw` | **BUILT, in keeper** — backcast = measured NP3-911 (admissible input), forecast = enrollment forward | run165 |
| AS-aware P2 commitment | `ercot_as_aware_commitment` | **BUILT, SHELVED** — rejected probe | run160; **ercot27** |
| Measured DAM-AS overlay | `ercot_dam_as_overlay` (calibration flag) | **in keeper — the thing this plan retires** | ercot32 |
| HSL uncurtailed potential, ERCOT 2024/25 | `renewables.hsl_potential_mw`; `_UNCURTAILED_FALLBACK_ISOS` | **measured, 2026-07-06** — owner manually uploaded NP4-732/737 (wind/solar) covering 24/24 months of both years; G7 gross-up no longer used for ERCOT 2024/25 | P4 remainder — **CLOSED, superseded 2026-07-06 (see WS-E and `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`)**. The credentialed API-key route is still permanently closed (owner will not procure a `data.ercot.com` key) — this landed via the owner manually downloading through the Data Access Portal UI instead, a different and already-authorized mechanism |

**The current keeper (ercot32) is P1-only** — `passes=["P1"]`, no commitment of
any kind. That is a settled decision (ercot27 verdict), not an open question.

## 3. Diagnosis first: why ercot27 failed, and the failure-mode ledger

The task's rule: design against the ercot27 failure mode **explicitly**. The
2026-07-03 log entry decomposes it; two distinct failures were in play, and four
more from the sibling probes belong in the same ledger. Every design item in §4
must name which of these it is guarded against.

### 3.1 The ercot27 post-mortem

**F1 — the exact-coverage adequacy artifact (broad price elevation, no
scarcity-month signal).** The AS-aware P2 pass floored committed capacity at
`energy + AS requirement` — **~1.0× online-reserve coverage** — where the
measured RTOLCAP series shows the real system holds **~2×** the requirement
online in ordinary hours. With coverage pinned near 1.0, the shared-headroom
dual elevates **every** month (+$11.5/yr 2023, +$1.7 2024, +$2.0 2025) while
adding **nothing** to the scarcity months it was aimed at (Jun 2023 −13.9 →
−12.9; Aug −88.7 → **−90.2**). The Feb-2023 +$42.5 elevation — with ECRS not yet
live — isolates the artifact to the floor, not to any real AS mechanism. The
within-bundle P1-vs-P2 comparison proved the genuine scarcity-month improvement
(Jun −$23.5 → −$13.9) was **already in P1** (ECRS no-release step + product
carve-outs); P2 contributed only the artifact.

**F2 — dropping the lumped total-reserve family.** ercot27's multi-product swap
removed the published RTORPA total-reserve ORDC curve, collapsing the deep tail
(Aug-2023 −$88.7 vs keeper −$46; >$1,000 h 28 vs 61). ercot32 settled the fix:
**products AND the lumped total family together, in the P1 LP.**

### 3.2 The wider ledger (sibling probes)

**F3 — the bimodal commitment screen (run160).** Any commitment-state mechanism
that re-scopes reserve supply is bimodal with no grounded middle: a gentle
(idle-only) screen leaves headroom abundant → under-fire ($21 May); an
aggressive (energy-margin) screen forces the committed fast fleet to back-fill
decommitted energy → evening fast-headroom collapse → VOLL over-fire ($188+
May). Threading the target between them requires tuning the screen **to the
price** — forbidden (#1/#11).

**F4 — online-gating is a generation subsidy.** `R − ρ·ΣP ≤ 0` ties reserve to
online *output*: on a tight evening (large ΣP) it grants **more** reserve and
suppresses scarcity — the opposite of the intent. Ruled out for ERCOT's
additive form (run159 doc).

**F5 — overlay/adder double-counting (run161, 2023 May +$72 vs $31).** A new
scarcity channel layered on a year another overlay already carries
double-counts. The one-event-one-channel audit (min-overlap probe, ercot27
entry: RTORDPA∧reserve-dual ≈ $0.2k) is the guard and must be re-run on every
candidate.

**F6 — chasing a DA-boundary premium on an RT-scored benchmark.** ercot32's
root cause (4): the 2024 Jan +12.5 / May +7.8 shape residuals the overlay
"carries" are the **DAM-vs-RT settlement boundary** (overlay hours realized DA
≈ $599/$511 vs RT ≈ $205/$316). An RT-scored co-opt **should not** reproduce
them; ex-overlay Jan-2024 = −2.1. Any gate that asks the endogenous co-opt to
hit the overlay-on numbers on an RT benchmark is asking it to fit a settlement
artifact.

**F7 — the discretionary-procurement uplift (run163).** On the May-2024 acute
evenings ERCOT manually procured ~8.8 GW of up-AS where every driver
relationship predicts ~7.4 GW. That uplift is operator discretion with **no
forward-driver analogue**; reproducing it would mean keying the requirement off
the realized tight days — a measured-outcome pin (#12). It is a *documented
residual*, permanently.

### 3.3 The design consequence

The forward analogue must be **P1-only** and must shape the **reserve-supply
definition** (the RTOLCAP track run161 proved structurally faithful), never the
commitment state (F1/F3) and never via output-coupled gating (F4). The supply
definition must reproduce the measured **~2× coverage distribution** — not ~1.0×
— *before* it is allowed to price anything (the anti-F1 gate, §6 G-3). The
scoring protocol must separate RT-supported scarcity from the DA-boundary and
discretionary components the overlay carries (F6/F7), which the endogenous run
is **expected and entitled to miss**.

## 4. What actually remains to build

With §2 in hand, the genuine gaps between "keeper with overlay" and
"overlay-off endogenous stack + fully forward-native path" are exactly four,
plus a scoring protocol:

### WS-A — Forward online-responsive supply: the RTOLCAP analogue (the new core build)

`ercot_rtolcap_supply_cap_mw` reads the **measured**
`ercot_<year>_ordc_reserves_hourly.parquet` and returns `None` (uncapped) when
no file covers the year — so the supply re-scope that makes the whole ORDC-era
stack fire is **backcast-only today**. This is now the largest measured lever on
the AS path and the piece with **no forward analogue at all**.

**Design: a derived committed-share × ramp-capability construction** (preferred)
with a statistical-regression fallback:

```
RTOLCAP_fwd(t)  = Σ_c online_share_c(q_nl(t), hod(t), season(t)) × ramp10_cap_c(year)
                  + online_storage_power(t)
RTOFFCAP_fwd(t) = Σ_{c∈quick-start} offline_share_c(·) × ramp10_cap_c(year)
```

* `online_share_c` — per responsive class `c`, the share of installed capacity
  historically online as a function of the **net-load percentile**, hour-of-day
  and season, derived from the committed CAMPD unit extracts (online = CF > 0
  hours) — the same derive-script family as `MAINTENANCE_MONTHLY_SHAPE` /
  the ST_GAS drag. **Rule 23 applies:** the derive script re-runs only on source
  data updates, never on a residual.
* `ramp10_cap_c` — the class's 10-minute ramp capability per online MW, from
  unit physics (ramp rates already in the fleet arrays), regenerating as the
  fleet evolves.
* Both shares are functions of the model's **own forecast net-load**, so the
  cap regenerates forward and responds to changed conditions (more VRE → deeper
  midday net-load troughs → fewer units online → lower RTOLCAP → scarcity
  incidence rises): the admissibility test (#10) passes.

**Anti-F1 identification gate (hard):** the formula's coefficients are fit to
the **measured RTOLCAP/RTOFFCAP MW series** (a quantity, like G3's ASPLANNP433
fit) and the fitted formula must reproduce, on 2023–2025: (a) annual mean level
within ±10% (measured 13.5/16.7/19.1 GW), (b) the p10/p50/p90 band, and (c) the
**coverage ratio** distribution (RTOLCAP ÷ total AS requirement, median ~2×).
A construction that lands near 1.0× coverage is the ercot27 artifact and is
rejected *at the validation script*, before any dispatch run.

**Anti-F3/F4 guard:** the construction never reads the LP's own commitment or
output state (no P-coupled terms, no P2). It is an exogenous formula of forward
drivers, exactly parallel to the G3 requirement seam.

**Seam:** a mode-aware selector in `ercot_rtolcap_supply_cap_mw` mirroring
G4's `ercot_load_resource_reserve_credit_mw` — backcast returns the measured
series (unchanged, byte-identical); forecast (or an explicit
`ercot_reserve_supply_forward=True` probe flag) returns the formula. The
formula-in-backcast swap is the run-163-style one-delta validation.

### WS-B — Storage AS duration gates (finish G5, retire the measured award)

ercot32 root cause (1): the endogenous split holds **2.1–2.4× the measured
battery AS award** because it lacks the published per-product duration
requirements (ECRS 2-h, Non-Spin 4-h sustained; Nodal Protocols §3.17.3/8.1).
Add the LP-linear, vectorized duration gate linking cleared storage AS to SOC —
schematically `Σ_p dur_p × R_storage[p,t] ≤ SOC[t]` alongside the existing
power-cap competition — so a 1-h battery cannot sell 4-h Non-Spin on its full
power. Validation is a **quantity** comparison (modeled vs measured 60-Day DAM
award MW, target ~0.8–1.3×), never a price. Once the split validates, the
keeper's measured treatment (`storage_as_commitment` +
`ercot_storage_as_reserve` + `ercot_storage_as_product_credit`) is replaced by
`ercot_storage_as_endogenous` **as one consistent swap** — the ercot30 blow-up
is the standing warning against mixing the two treatments (measured docking
without requirement netting over-withholds; the endogenous swap must remove
docking, netting *and* credit together).

### WS-C — Requirements (G3): already built; carry the honest residual

The forward formulas are built and validated (run163: total up-AS 0.94/0.98/1.02×
measured). Backcast keepers **keep reading measured ASPLANNP433** — a published
procurement quantity that passes the admissibility test, exactly like fuel
prices. No new build. Two carried items:

1. The 2024 acute-evening discretionary uplift (F7) and the 2023
   over-procurement are **documented residuals** of the forward formula — never
   to be chased with coefficients (rule 23; coefficients re-derive only when
   ASPLANNP433 source data updates).
2. Scenario expression of recurring conservatism belongs in the existing
   `rtcb_reliability_deployment_mw`-style scenario knob family — an explicit
   scenario input, not a fitted default.

### WS-D — Load-resource RRS (G4): done

run165 closed it (backcast = measured NP3-911, an admissible input; forecast =
enrollment trajectory × availability shape). Integration only: the stage-4 run
inherits `ercot_load_resource_reserve=True` unchanged.

### WS-E — HSL completion remainder (P4) — **SUPERSEDED, INTAKE COMPLETE (2026-07-06)**

> **Update 2026-07-06: measured HSL landed, both years complete.** The
> permanent-closure decision below was specifically about the *credentialed
> API-key* route (`data.ercot.com`/`api.ercot.com` subscription key) — the
> owner still will not procure one, and that path is re-verified closed
> (identical 302/401 gate as every prior attempt). What changed is the
> owner manually downloaded the NP4-732/737 reports through the Data
> Access Portal **UI** (not the API) and uploaded them to the repo across
> two rounds — a different, already-authorized mechanism the closure
> decision did not rule out. Coverage is now 24/24 months for both wind
> and solar, both years; `scripts/build_ercot_hsl.py --year 2024 2025`
> builds cleanly (see `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`
> for the full validation, including a `_read_csvs` fix for ERCOT's actual
> zip-of-zips archive shape, and a flagged solar-vs-EIA-923 divergence kept
> as-is per rule 14). **The G7 gross-up fallback is retired for ERCOT
> 2024/25** — `hsl_potential_mw` now reads the measured parquets directly.
> The `ercot34` keeper itself was solved and promoted before this data
> landed; whether re-solving it against measured HSL moves the result is
> being probed as `ercot38` (see `docs/calibration-log.md`).
>
> **Follow-up 2026-07-06: bug fix on the committed parquets.** The
> "24/24-month, builds cleanly" parquets above were built from a
> corrupted 96-hour ERCOT source window (2024-08-20..23, both fuels —
> physically-impossible system-wide values baked into every repost);
> fixed via a cited, narrow known-bad-window exclusion, plus an unrelated
> 2025-schema HSL-column-preference fix. Both years rebuilt; wind
> cross-check tightened to +0.1%/−0.2%. Full detail:
> `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`.

> **Original closure (2026-07-05, retained for context — no longer the
> operative guidance for the UI-upload path):** the NP6 HSL *API* intake
> was closed for good: the owner was not procuring a `data.ercot.com` /
> `api.ercot.com` subscription key, so the `401 missing subscription key`
> block on the Data Access Portal was permanent, not a transient egress
> failure. The G7 reference-curtailment-rate gross-up was the standing
> approach for ERCOT 2024/25 HSL under that constraint. The
> `scripts/build_ercot_hsl.py` builder always transparently ingested an
> NP6 upload landing by another route — which is exactly what happened.

ERCOT 2024/25 still have **no NP6 HSL parquet**; `hsl_potential_mw` falls back
to the reference-curtailment-rate gross-up (G7). Relevance to this plan: the AS
requirement drivers (`ercot_as_forward_drivers`: net-load, `sigma_fe`,
`ramp_up`) and the WS-A net-load-percentile shares are built from the wind/solar
series — with curtailment baked into delivered CF, 2024/25 drivers understate
VRE variability precisely in the oversupply hours that set ECRS/NonSpin sizing.
Remainder to complete:

1. Intake the published NP6-732/737 wind+solar production (HSL) reports for
   ERCOT 2024/2025 via the data-intake contract (`scripts/build_*` →
   `data/raw/ercot/`, schema-first). **Egress caveat:** ERCOT MIS fetches have
   been 403-blocked before (NP6-576-ER, ercot27 WS3); if blocked, document the
   attempt and keep the G7 fallback — the fallback is already
   forward-admissible, so this is a fidelity upgrade, not a blocker.
   **Done — landed 2026-07-06 via a manual UI upload** (the credentialed API
   route stayed blocked, see the box above). Full 24/24-month coverage both
   fuels, both years; `build_ercot_hsl.py --year 2024 2025` builds cleanly.
   Full record: `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`.
2. Confirm the dispatch hands uncurtailed potential to the LP for 2024/25 and
   curtailment stays endogenous (the G7 wiring), and that the AS driver series
   are the dispatch-consistent ones. **Confirmed** — `hsl_potential_mw` now
   returns the measured series for `(ERCOT, 2024/25)` (raw parquet read
   directly, no clean-tree regeneration needed); `_forecast_uncurtailed_cf`
   is no longer consulted for these pairs. A modeled-vs-reported curtailment
   diagnostic and AS-driver delta against the retired gross-up are now
   possible but have not been run — open for a future session.

### WS-F — Scoring protocol: separate what the overlay actually carries

Before any keeper decision, the overlay must be decomposed **on the current
main** (stage 0): for each overlay-active hour, split the adder into
(i) RT-supported scarcity (RT price also elevated), (ii) the DA-boundary
premium (realized DA ≫ RT — F6), (iii) hours coincident with the
discretionary-procurement uplift (F7). Components (ii)+(iii) are the overlay's
**non-reproducible share** — the endogenous run's target is component (i) plus
the held months, scored against **RT** actuals with the DA diagnostic row
(ercot27 WS4 machinery) reported alongside. Without this decomposition, the
greenlight gate is category-confused (it was, in the original G1 text: the ~$45
May figure mixes DA and RT).

## 5. What is explicitly OUT of scope

* **The P2 / AS-aware-commitment route** — shelved by the ercot27 verdict.
  Stage prompts must not resurrect it "to fix headroom" (F1/F3).
* **The broad-May 2024 energy-base miss** — re-attributed by run161/ercot32 to
  the CC over-run / ST_GAS+CT_PEAKER merit-order track. An AS mechanism must
  not paper over it (#1); a
  broad-May residual in the stage-4 run is expected and carries that
  attribution.
* **2023 out-of-market scarcity (RTORDPA)** — stays on its G2 bridge; retiring
  it is the RTC+B regime gate's job, not this plan's.
* **Retuning offer curves, ORDC curve shapes, or demand-curve prices to the
  residual** — the demand-curve prices are VOLL-anchored market-design
  schedules; scarcity *incidence* must come from requirement × supply.

## 6. Validation protocol (stage 4) — the overlay-replacement run

**Run design.** `ercot40` (next free label): the **ercot32 recipe exactly**
(same offer curves, same measured requirements, same G4 credit, same total
family + products + ECRS design, P1-only, `--year 2023 2024 2025`, one bundle)
with precisely these deltas:

1. `ercot_dam_as_overlay = False` (the replacement under test);
2. WS-A forward supply **in backcast** (`ercot_reserve_supply_forward=True`) —
   the one-delta proof the supply formula carries the measured cap's role;
3. WS-B endogenous duration-gated storage AS replacing the measured
   treatment (docking+netting+credit off, endogenous on — one consistent swap).

If (2) and (3) individually pass their stage gates but the combined run
misbehaves, register intermediate single-delta probes to attribute (the run163
pattern). All probes and the final run go on the dashboard in-session (#15),
all years in one bundle (#16).

**Gates (all vs RT actuals, DA diagnostic reported alongside):**

| # | Gate | Pass condition | Guards against |
|---|---|---|---|
| G-1 | Acute-day reproduction | May-2024 8/24/26 dw LMP within ±25% of RT actual; 2023/2025 acute days ≥ ercot32 ex-overlay levels | the original G1 target, on the right (RT) benchmark |
| G-2 | Hold the held months | 2025 monthly MAE ≤ ercot32 + $1; Aug-2024, 2023-H2 within ±$3 dw of ercot32 | over-fire (F3-aggressive mode) |
| G-3 | No broad elevation | no month gains > +$5 dw vs ercot32-ex-overlay where measured RTOLCAP p50 > ORDC curve reach (~11.3 GW); Feb-2023 specifically ≈ unchanged | **F1 — the ercot27 artifact** |
| G-4 | Tail structure | h>$200 / h>$1000 counts within ercot32's ratio band of RT actuals; deep tail (>$500) not collapsed vs ercot32 | F2 (total family intact) |
| G-5 | Quantity fidelity | WS-A formula: level ±10%, coverage-ratio median ~2×, corr vs measured RTOLCAP reported; WS-B split 0.8–1.3× measured award; cleared AS by product vs ASPLANNP433 | identification on quantities, never price |
| G-6 | One event, one channel | RTORDPA ∧ reserve-dual overlap ≈ $0 (re-run the ercot27 min-overlap audit) | F5 |
| G-7 | Attribution ledger | every residual vs ercot32 mapped to {DA-boundary (F6), discretionary uplift (F7), energy-base (out of scope), genuine miss} | category-confused keeper decisions |

**Rules compliance:** forced-energy budget (#20) unchanged by this work; DOF
ledger + zero-forcing ablation twin registered alongside (#21) — the WS-A
coefficients and WS-B duration constants enter the ledger with their
identification sources (RTOLCAP series; Nodal Protocol durations); structural
promotion is scored leave-one-year-out within 2023–2025 (#22); 2022/H1-2026
remain untouched; no new tunable outside `ScenarioConfig`/`constants.py` (#24).

**Keeper decision (rule #1, written down before the run):** promote the
overlay-off run if G-3/G-5/G-6 pass and every G-1/G-2/G-4 miss carries a named
root cause in the G-7 ledger — **even if C3a/C3b worsen vs ercot32**, because
the endogenous run carries strictly more real market structure (the DAM
co-optimization ERCOT actually ran, rather than its measured settlement
residue). The overlay itself is then demoted to an explicitly-labelled
diagnostic (default-off in keepers, retained for the F6/F7 decomposition), and
the DA-boundary + discretionary components become documented MODEL
MISS/attribution rows in the attestation, exactly as ercot32 documented its
ex-overlay 2024 tail. If G-3 or G-6 **fail**, the run is a rejected probe
(registered per #15) and the failure is a new ledger entry — never a reason to
add a tuned mechanism.

## 7. Build order

| Stage | Work | Depends on | Effort |
|---|---|---|---|
| 0 | Overlay decomposition + ercot32-ex-overlay re-baseline on current main (WS-F) | — | S |
| 1 | WS-A forward RTOLCAP/RTOFFCAP supply formula + one-delta backcast probe | 0 | M-L |
| 2 | WS-B storage duration gates + one-delta endogenous-storage probe | 0 (parallel with 1) | M |
| 3 | WS-E NP6 HSL 2024/25 intake (egress-permitting) | — (parallel) | **CLOSED PERMANENTLY 2026-07-05** — owner will not procure a data.ercot.com key; G7 fallback is the standing approach, do not re-attempt |
| 4 | Integration run `ercot40`, gates G-1…G-7, keeper decision, dashboard | 1+2 (+3 if landed) | **RUN 2026-07-06 as `ercot34`** ("ercot40" label was taken by the WS-A probe) — overlay-off + WS-A forward supply, WS-B swap NOT taken (its stage-2 gate landed 0.54–0.61× vs the 0.8–1.3× band; §4 WS-B conditions the swap on validation, so the measured storage treatment stays and WS-B is the carried open G-5 item). Gate scores: calibration-log 2026-07-06 entry; dashboard `2026-07-06-ercot34-stage4-overlay-off` (+ the `ercot35` replay-metagap A/B arm). **PROMOTED TO KEEPER 2026-07-06 (owner sign-off)** — G-3/G-5/G-6 passed, all G-1/G-2/G-4 misses root-caused per §6's written rule; attestation + DOF ledger + zero-forcing twin registered; the DAM-AS overlay is demoted to the F6/F7 diagnostic per §6. Stage 5 (forward-mode proof: 2026+ RTC+B run, zero measured AS reads) is now the plan's only open stage. **Caveat discovered en route (G-12):** every replay-based stage artifact (ercot33 ex-overlay baseline, ercot40 WS-A probe, 32-head-regate) solved WITHOUT the keeper's four un-persisted ERCOT gas-geography flags (`ercot_zonal_gas_basis`, `ercot_west_netload_gas_shape`, `ercot_west_gas_delivered_floor=0.4`, `oil_primary_bin_fuel` — present in the keeper's resolved run_config.json, absent from meta.json), so their absolute levels are config-shifted vs the keeper; their INTERNAL A/B conclusions (WS-A formula-vs-measured Δdw ≤ $0.11; the WS-F decomposition, which is payload arithmetic, not a solve) stand. ercot34 restores the four flags via `--set`. |
| 5 | Forward-mode proof: 2026+ RTC+B forecast run, zero measured AS reads, ensemble sanity | 4 | S-M |

Stages 1, 2 and 3 are independent — run their solves as parallel invocations
per CLAUDE.md #12 (separate `--out-dir`s, ≤2 concurrent per-plant runs); years
within any invocation stay sequential.

The ready-to-paste prompts are in
`docs/handoffs/ercot-as-coopt-prompts-2026-07.md`, one per stage.
