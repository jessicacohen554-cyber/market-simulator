# Calibration Log — MISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for MISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — MISO keeper advanced: miso-75 recipe on the gas_daily_shape §3.7 true-date fix (the lane's own follow-up; NOT a miso-N session)

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7 — the worth-doing-regardless correctness fix filed FROM
miso-72, deliberately outside the miso-72 verdict). The miso-75
manitoba-meritcap recipe replayed on the fixed national HH daily shape (+ the
inherited +1h frame fix); `miso_winter_citygate_daily` still supersedes the
Chicago-zone winter cells (rule 19). Annual mean Δ +0.00/+0.10/+0.08, spike-day
relocation only (2024 max |Δ| $60/MWh at h358). Determination unchanged
NOT-YET on the ledgered irreducible {C3a-2025, C3c} tail; C3a-2025 −15.3% →
−15.1%. Keeper → `2026-07-19-miso-gasshape-interpfix` (owner-authorized
in-session); base `2026-07-19-miso-gasshape-interpfix-base` registered.
**The MISO lane's next number stays miso-80**; the congestion question remains
CLOSED (NO-BUILD charter frozen, PR #2555).

## 2026-07-20 — miso-80: direction-symmetric loss surface CHARTERED — VERDICT NO-BUILD (the miso-76 R2 trip is flow-rectification + the M4 congestion offset, and symmetry AMPLIFIES it). Charter-first, docs-only: NO LP, NO solve, NO intake, NO registration; keeper UNCHANGED

**Lane.** The miso-76 loss lane's named successor ("direction-symmetric loss
structure (re-opens the negative-price disposal problem)"), chartered per the
miso-78 precedent — adjudicated at the design layer before any build:
`docs/handoffs/miso-80-direction-symmetric-loss-charter-2026-07.md`.

**Diagnosis (charter §1–§2, from the committed surface + the miso-76
adjudication — no new solve).** An LP loss link prices separation only through
complementary slackness of a FLOWING direction, so the model's separation sign
is slaved to its realized corridor flow — never to the measured gradient. The
East−Indiana 2025 gradient alternates sign 6/6 months (annual net −0.0003);
the model's corridor flows persistently East→Ind, so the one-way clamp
transmitted only the negative-gradient months → the rectified −$0.066 (the R2
trip). A direction-symmetric coefficient makes the positive-gradient months
ALSO price with the model-flow sign — predicted ≈ −$0.13 vs measured total
+$0.033: **R2 trips ~2× harder. The clamp was not the trip's cause; it was
the only thing bounding it.** The B1 undershoot (35–70% transmission) is also
not symmetric-fixable: atypical-direction hours flip to the WRONG sign instead
of clamping to ~0 (annual transmission strictly falls), the reverse charge is
anti-physical at the measured operating point (counter-gradient flow REDUCES
losses — the symmetric coefficient is a linearize-at-zero invention, weaker
provenance than the clamp), and the ceiling itself is the link-conditioned vs
node-property representation gap no loss coefficient escapes.

**Free-disposal composition (charter §3, the session's second question).**
Symmetry halves the circulation-disposal arming threshold (~$0.2/MWh-disposed
vs one-way ~$0.4) — but in MISO the per-zone ε-dump column both bounds duals
≥ −ε and disposes at $0.001/MWh, strictly dominating the channel in every
hour (renewables offer ≥ $0; `negative_renewable_offers` is CAISO-only). A
manageable fence (MISO-only + incompatibility assert), NOT the binding
refutation — §1–§2 refute the candidate first.

**Enumeration (charter §4, pre-registered):** SY-1 symmetric-magnitude —
REFUTED (dominated by the already-rejected one-way mechanism on every axis);
SY-2 signed-both-directions — LP-INADMISSIBLE (coefficient > 1 creates
energy); SY-3 persistence-gated re-derive — not refuted as physics, NOT
CHARTERED (clears R2 only by zeroing the pair, which then fails B1's own band
on that pair — redesigning bands around the known failure is answer-shaped —
and leaves the West/Illinois undershoots untouched). Recorded as reopening
path RO-S3 only.

**Verdict: NO-BUILD — the loss lane is at its representation frontier.**
~Half the persistent wind-belt separation is representable loss physics
(built, merged tier-3 default-OFF, rejected by its own pre-registration); the
remainder and the East cancellation pairs are congestion, data-blocked at
representation (miso-78 fundamental, miso-79). The miso-76 mechanism stays
exactly as merged; the one-way clamp is recorded as the CORRECT conservative
choice. Charter §6 carries a pre-registered gate block (current-keeper recipe,
R1 C3b ≤ 0.20 veto with 2025 headroom 0.002, R2 scored FIRST on East-2025, B1
unchanged, new zero-circulation disposal guard) that binds ONLY if the owner
overrides; §7 pre-registers reopening conditions RO-S1 (M4 reopening →
joint loss+congestion charter), RO-S2 (derive-layer hourly flow/gradient
concordance probe, threshold set a priori), RO-S3 (owner-chartered SY-3 with
band re-charter FIRST).

**Disposition.** Docs-only; nothing to register (rule 15 N/A — no solve);
quarantine untouched. Keeper UNCHANGED (`2026-07-19-miso-gasshape-interpfix`,
NOT-YET, same 2 fails {C3a-2025 −15.1%, C3c}). **Next action is the owner's**
(charter §8, single decision): sign off NO-BUILD (the Midwest-separation lane
closes at its frontier pending RO-S1/S2/S3), override to the §6-gated build,
or redirect (open lanes: D1 Z2/Z7 load split; PJM merit-cap twin). Next
number: miso-81.

## 2026-07-20 — miso-81: phantom-outage regenerate-and-re-audit (ERCOT-79 cross-ISO lane) — MISO HOLDS on the corrected availability envelope; the SHORT extract was stale (+86 net windows, +171 GW-days of 1-5-day coal stops); determination REPRODUCES NOT-YET on the same 2 ledgered fails; miso-80 NO-BUILD signed off in-session

**Lane.** The owner signed off the miso-80 NO-BUILD charter in-session and
directed the recommended next lane: MISO's own regenerate-and-re-audit per the
ERCOT-79 cross-ISO corrected-availability program
(`results/calibration/FINDING-neiso-nyiso-phantom-outage-reaudit-2026-07-19`:
"CAISO and MISO remain their own regenerate-and-re-audit lanes"; NEISO/PJM
HELD, NYISO's marker was WITHDRAWN).

**Staleness audit (all three extracts vs their frozen derivers at HEAD).**
Standard `campd-unit-outages-MISO.csv`: 4,418 → 4,414 windows — 4 rows the
frozen deriver no longer emits after the post-07-14 deriver-lane changes (3×
George Neal North `eia_exact`, 1× TES Filer City `optime_proxy`); the file had
been regenerated 2026-07-14 (miso-65) and was otherwise current. SHORT
`campd-unit-outages-short-MISO.csv`: **205 → 291 windows (+91/−5, +171
GW-days of 1–5-day baseload-coal full stops at
Merom/Cayuga/Monroe/Gibson/Sioux/Sherco, 32/31/28 by year)** — the 2026-07-15
when-operable short-guard change (86918fa) was re-derived for PJM only (rule
24), leaving MISO stale against its own frozen deriver. Maxgen extract:
byte-identical (2,158 rows). Corrected extracts committed BEFORE any solve
(2bd63e4, rule 12); zero parameter changes — rule-14/15 measured-input
correctness.

**Re-audit (run `2026-07-20-miso-81-phantom-outage`, bundle
`results/calibration/miso81_phantom_outage`).** The
`2026-07-19-miso-gasshape-interpfix` keeper recipe replayed VERBATIM
(`replay_keeper`, per-year chain then a merged full-span pass, years
sequential per rule 12) on the corrected envelope, full span 2023–2025.
**Determination REPRODUCES: NOT-YET on exactly the keeper's 2 ledgered fails
{C3a-2025, C3c} — MISO HOLDS.** C3a-2025 −15.1% → **−14.8%** (the added coal
stops tighten supply slightly; 2023/2024 C3a stay PASS); C3c unchanged 0/6/0
vs RT 30/37/88 (the irreducible scarcity tail); C3b PASS every year;
C4/C5a/C6/C7/C8 hold (C8 2025 ST_GAS grounded-above-budget clean pass, same
as the keeper); zero status regressions. The NEISO/PJM fix-in-place pattern —
the MISO keeper's calibration is NOT co-dependent on the stale availability
envelope (contrast NYISO). Registered with attestation + DOF ledger +
`legitimacy_diagnostics.json`; retention pruned miso-70 (top-15).

**Disposition.** Keeper SWAPPED to `2026-07-20-miso-81-phantom-outage`
(2026-07-20, the NEISO fix-in-place precedent — same recipe, corrected
measured inputs, zero status regressions; keepers/MISO.json +
status/MISO.js rebuilt, calibration-keeper-auditor PASS 0 failures /
1 stale-text repair). Executed after the in-session owner directive for
the re-audit lane with the interactive ask channel erroring; trivially
reversible — revert keepers/MISO.json + rebuild the status shard if the
owner prefers the pre-correction keeper. Quarantine untouched (train
years only). With the
re-audit HELD, the MISO frontier path is open: owner may declare the
calibration-complete marker (NEISO precedent — the two fails are the ledgered
irreducible tail), then the holdout ladder (MISO out-of-training intake is at
zero; data-readiness session next, then the 2022 validation one-shot per rule
22/G-19). Next number: miso-82.

## 2026-07-20 — miso-82: MISO documented AT FRONTIER on the ledgered {C3a-2025, C3c} scarcity tail — externally validated (deep-research, 24/25 claims confirmed 3-0) + current-keeper empirical re-confirmation; holdout marker NOT declared (owner declined); forecast-mode VOLL/ORDC change filed; docs-only, NO solve/intake, quarantine untouched

**Lane.** Owner declined to declare the MISO calibration-complete marker or
authorize out-of-training intake this session, and instead asked the sharper
question: *could layering scarcity pricing close C3c, and where are the missing
scarcity hours coming from?* This session answers it, grounds the answer in
primary sources, documents MISO at frontier, and files the forecast-mode ORDC
change. Docs-only — NO LP, NO solve, NO intake, NO registration (rule 15 N/A);
keeper UNCHANGED (`2026-07-20-miso-81-phantom-outage`, NOT-YET on {C3a-2025
−14.8%, C3c 0/6/0 vs RT 30/37/88}).

**Empirical re-confirmation on the current keeper (no re-solve).** Took the
miso-81 keeper's committed `hourly/system_2025.parquet` against the Indiana-Hub
actual tail: in the **88 actual 2025 RT>$200 hours** the model prices **~$50
median / $83 p90 / $157 max** (energy), the reserve adder fires **2 of 88**,
energy+reserve exceeds $200 in **1 of 88**, and there is **zero load-shed**. The
model is an order of magnitude below, not just-under-threshold. The actual DA in
those hours is mostly low (hour 6425 RT $1,598 / DA $99; hour 2274 RT $876 / DA
$52) — ~90% are RT forecast-error transients the DA market never saw either, out
of a perfect-foresight hourly LP's representation by construction. Reproduces the
2026-07-02 bind-gate diagnosis on the current keeper (deliverable reserve ≥11 GW
vs ~4.4 GW requirement in every event hour; LP re-times energy for ≤$23/MWh <
the $200 ORDC step).

**External validation (deep-research pass, 17 primary sources, 24/25 claims
confirmed at 3-0 adversarial votes).** The decisive finding: **MISO's real
scarcity tail is not an emergent marginal-cost outcome even in MISO's own SCED.**
It is an administrative stepped ORDC/RCPF curve (two energy steps $1,100/$2,100
anchored to $3,500 VOLL in the 2023–2025 window; per-product reserve curves spin
$65/$98, reg ~$140, ST up to $500), and that ORDC is itself **derived from a
Monte-Carlo LOLP simulation** over net-load/outage uncertainty in a 10–30 min
window scaled by a $35,000/MWh target cost (MISO Scarcity Pricing White Paper
Mar-2024 §3.2.1). It prices **probabilistic short-term risk** a deterministic
perfect-foresight hourly LP does not contain. ELMP (live 2015) is a pricing-only
convex-hull LP relaxation on single-interval DA(1h)/RT(5min) dispatch. The
generic PCM literature confirms the limitation is universal: 23/23 surveyed
models are hourly+deterministic (arXiv 2101.02303); deterministic perfect-
foresight LPs systematically under-produce the spike tail (PyPSA-Eur arXiv
2606.16486; IOPscience 10.1088/2753-3751/ae3f34); limited-foresight helps only
marginally (SMAPE 21.3→20.8%); scarcity binds rarely (7 shortage days fall-2025,
Potomac IMM). Coverage caveat: no vendor-specific docs for
PLEXOS/Aurora/GE-MAPS/PROMOD/Dayzer/EnCompass/Ascend surfaced (pages
unreliable/paywalled); the 23-model survey is the proxy.

**Conclusion — C3c is at the representation frontier.** "Layering scarcity
pricing" = the NYISO/NEISO post-solve ORDC/RCPF adder; §1 shows it fires ~2 of 88
hours because the model's reserves do not go short, and §2 explains why at the
mechanism level. Reaching the tail would require manufacturing the uncertainty
(an LOLP/forecast-error-inflated requirement or stochastic net-load draw) — out
of representation or a fit to the residual (rule #1/#10 forbid the fitted path).
The reachable structure is already built and adopted per rule #1 (reserve
deliverability miso-39, Midwest sub-regional miso-71, measured requirements
miso-56). No untried admissible pricing layer closes C3c.

**Deliverables.** (1) `docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md`
— the finding (empirical + literature + sources). (2) Pointer added to
`docs/multi-iso/miso-scarcity-tail-diagnosis.md`. (3) Frontier block on
`frontend/data/backcast/keepers/MISO.json` (declared 2026-07-20) + `status/MISO.js`
rebuilt (calibration-keeper-auditor PASS, 0 failures, 1 stale-status repair).
(4) **Forecast-mode note filed** (finding §5): for `mode="forecast"` years
spanning 2025-09-30+, MISO's FERC-approved VOLL rose $3,500 → **$10,000/MWh** with
a new **$6,000/MWh ORDC cap** and floors lowered to **$600/$1,100** — use these,
not the backcast $3,500/$1,100–$2,100 curve; the $35,000 is the LOLP-scaling
target cost, distinct from the $10,000 price cap. Backcast keepers unaffected
(2023–2025 entirely pre-reform).

**Disposition.** Frontier documented; marker NOT declared (owner declined — the
holdout ladder + 2022 one-shot remain a future owner-authorized session, G-19
HOLD in force regardless). MISO out-of-training intake still at zero; the
equivalency-register MISO section stays open (no intake this session). Quarantine
untouched (no out-of-training year read/derived/solved). Next number: miso-83.

## 2026-07-24 — miso-83: gas-offer net-revenue margin — A/B refutes the C3b bar, but OWNER OVERRIDE (rule 1) PROMOTES it as the MISO keeper for structural fidelity; determination downgrades to NOT-YET

**Owner override (2026-07-24).** The A/B below refuted the charter's C3b bar
(the original session verdict was REJECT). The owner then directed, on rule 1
(right market structure first; a structurally-faithful mechanism stays even if
the backcast fit worsens): *"no matter what this should become the keeper, it is
more structurally sound."* The net-revenue margin — a fuel-invariant $/MWh gas
bid with full delivered-fuel tracking on the physical burn — is the more faithful
bid structure than the fuel-scaled multiplier, so the C3b tuning bar does not
veto it. Same cross-ISO decision as ERCOT-100 / CAISO / NYISO-72 the same week
(the net-revenue margin is the go-forward offer form). **Keeper SWAPPED to
`2026-07-24-miso-83-netrev-margin`** (`results/calibration/miso_netrev_margin`);
determination **NOT-YET** (see disposition). The A/B evidence and its refutation
stand exactly as recorded below — the promotion is a rule-1 structural call over
the fit, not a reversal of the finding, and NOTHING was tuned to rescue it
(rule 1/10; the two new FAILs are left unledgered as MODEL MISSes).

Charter rollout of the `gas_offer_net_revenue_margin` mechanism (NEISO keeper
`neiso-61`) to MISO. **Identification already landed** (branch
`claude/gas-offer-net-revenue-isos-1px5vg`, merged to main): MISO `phys_*` keys
on every identifiable gas class of `offer_curve_by_group`
(`pipeline/backcast_config.py`, cited to the measured
`data/raw/reference/miso_campd_marginal_hr_summary.csv` p50s) + anchor **3.0492
$/MMBtu** (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO` = mean of the keeper delivered-gas
overlay 2023–2025 = 2.8392 / 2.4893 / 3.8190; per-plant EIA-923 monthly level +
mean-preserving daily shape). Default-OFF and byte-inert at the fleet level; the
BASE arm (flag off) reproduces the `miso-81-phantom-outage` keeper up to
environmental alternate-optimal drift only (Δmean −0.33/−0.36/−0.42 $/MWh ≈ −1 %,
this box's kernel-string differs from the keeper's solve host — the A/B is
BASE-vs-MARGIN on the *same* box so the drift is common-mode and cancels).

**Structural confirmation (flag-on).** The reform reduces EXACTLY to the
registered band multipliers at anchor gas: the mc-side compression fires on
591 / 597 / 595 gas tranches (2023 / 2024 / 2025) at anchor 3.0492 $/MMBtu
(median fixed margin ≈ 9.7 $/MWh, max 260.4), the markup gas-elasticity going
1 → 0 (fuel-scaled multiplier → fixed $/MWh margin). Two-sided as designed:
below anchor (2023, 2024) the margin FIRMS the offer up; above anchor (2025) it
COMPRESSES it down.

A/B: same-HEAD `replay_keeper` of the `miso81_phantom_outage` recipe — BASE arm
(flag off) vs MARGIN arm (single delta `gas_offer_margin=true`), full 2023–2025,
RT-scored (`scripts/probes/netrev_margin_ab.py`; bundles `miso_netrev_base` /
`miso_netrev_margin`; per-year `--reuse-solved` legs on this 15 GB box, one
fresh year per process — rule 12):

| year | gas vs anchor | C3a base→margin | C3b dur-NRMSE base→margin |
|---|---|---|---|
| 2023 | 2.84 (<, firm)     | −1.8 → −1.3 % | 0.6009 → **0.6033** (worse) |
| 2024 | 2.49 (≪, firm)     | −7.6 → −6.6 % | 0.6243 → **0.6293** (worse) |
| 2025 | 3.82 (>, compress) | −13.0 → −13.4 % | 1.0634 → **1.0737** (worse) |

**A/B verdict (pre-registered refutation): the charter's C3b bar is NOT met.**
The mechanism FAILS "≥ C3b every year" in ALL THREE years (CAISO `caiso-112`
failed 2/3; MISO is worse). Root cause (structural, not a fit miss): MISO's
residual is the *opposite* shape to the NEISO winter-overshoot the mechanism was
built for. MISO's cheap bulk (<$40, ~7.6 k h/yr) is already OVER-priced (BASE
gap +3 to +5 $/MWh) while the mid/upper bands and scarcity tail are UNDER-priced
(the ledgered {C3a-2025, C3c} frontier — `miso-82`; >$300 gap −336/−438/−485).
In the two below-anchor years the margin firms the offer, lifting the
already-too-high trough further; in the above-anchor year it compresses,
pulling the mid bands (80–300, already under actual) further down and NOT filling
the tail (>300 gap unchanged at −335.8/−437.6/−486.5). Either direction moves the
duration curve the wrong way — the two-sided form is confirmed working, it is
simply the wrong lever for MISO's in-sample residual.

**Disposition — OWNER OVERRIDE promotes it to keeper anyway (rule 1); no tuning
(rule 1/10).** Per the owner directive (top of entry), the margin is adopted as
`2026-07-24-miso-83-netrev-margin` for structural fidelity, not fit. A clean
scored keeper bundle was produced (`replay_keeper` of `miso81_phantom_outage` +
`gas_offer_margin=true`, full span, per-year chained; registered via
`dashboard_add_run.py`; attestation adds one **grounded** DOF entry for the
anchor — zero fitted scalars, zero DOF delta otherwise — and inherits miso-81's
{C3a-2025, C3c} + storage caveats; `legitimacy_diagnostics.json` regenerated;
`calibration-keeper-auditor` PASS 0 failures). **Determination NOT-YET — a
downgrade from miso-81's calibrated-with-caveats status.** Two load-bearing gates
flip PASS→FAIL, both MARGINAL single-threshold crossings and both real margin
effects, left **UNLEDGERED as MODEL MISSes** (rule 1/10 forbid rescuing a
determination with caveats): **C1 fuelmix CC_REGULAR 2023** −7.76 → **−8.62 TWh**
(over ±8.0; the below-anchor firming sheds ~0.86 TWh of CC dispatch) and **C3b
price_shape 2025** monthly-NRMSE 0.194 → **0.204** (over the ≤0.20 veto). Part of
each crossing is this slow box's ~1 % alternate-optimal drift vs the keeper's
solve host, but the margin's own effect is real and fit-degrading — kept anyway
per rule 1, NOT tuned. The inherited {C3a-2025 price_mean −16.2 %, C3c price_tail
0/6/0} + storage caveats still apply. The miso-82 scarcity-tail representation-
frontier finding stands in the docs/attestation but is **no longer surfaced as a
keeper headline** while the determination is NOT-YET (the FRONTIER·CALIBRATED
block was removed from `keepers/MISO.json`). The `gas_offer_net_revenue_margin`
flag stays globally default-OFF (armed per-run in this keeper's recipe). 2022
holdout NOT touched (MISO carries no calibration-complete marker; quarantine
untouched).

**Push status (environment limitation — action needed).** The full promotion is
DONE and VERIFIED locally (bundle solved+scored, run `2026-07-24-miso-83-netrev-margin`
registered, attestation + `legitimacy_diagnostics.json` written, `keepers/MISO.json`
swapped, `status/MISO.js` rebuilt to MISO:NOT-YET, `calibration-keeper-auditor`
PASS 0 failures). But the DASHBOARD artifacts could NOT be pushed from this
session: this container's git relay rejects `git push` with HTTP 413 (even at
108 KB), and the API path (`push_files`) can only carry small hand-authored text
— not the generated `runs/<id>.js` payload (~968 KB gzip-base64), `status/MISO.js`
(~49 KB), or the binary bundle/bench. A partial push breaks CI (S1
`build_status --check` needs the bundle to verify status is in sync; parity /
`audit_keepers` need the payload). So ONLY this log entry is pushed from here.
To land the keeper swap on the dashboard, from a git-capable environment commit +
push: `results/calibration/miso_netrev_margin/` (bundle),
`frontend/data/backcast/registry/2026-07-24-miso-83-netrev-margin.json`,
`frontend/data/backcast/runs/2026-07-24-miso-83-netrev-margin.js`,
`frontend/data/backcast/keepers/MISO.json`, `frontend/data/backcast/status/MISO.js`
(+ any changed `bench/MISO/`) — or re-run the promotion in that environment
(`replay_keeper miso81_phantom_outage --set gas_offer_margin=true` full span →
`dashboard_add_run.py` → `keeper_store.py --set MISO <id>` → `build_status.py
--iso MISO`).

Next number: miso-84.

## 2026-07-24 — miso-85: MISO-native published outage overlay REPLACES the CAMPD unit-level derate on the net-revenue-margin keeper — PROMOTED per owner instruction (rule 1), determination NOT-YET; the measured record's fuel-blind grain is the diagnosed, unfixed root cause

**Owner instruction.** *"Re-solve net-revenue-margin with the MISO-native DAM
outage overlay, promote as keeper, run the calibration report, prune the run
explorer to just the new run."* Delivered: keeper **`2026-07-24-miso-85-dam-outage`**
(`results/calibration/miso_dam_outage_margin`), determination **NOT-YET**, MISO
run explorer pruned to this run alone (15 prior runs' registry+payload removed;
the `miso81_phantom_outage` bundle dir is kept on disk as the replay base).

**What was solved.** Two deltas on the `2026-07-20-miso-81-phantom-outage`
recipe via `replay_keeper` (`prb_overrides` channel), full span 2023–2025 in ONE
bundle (rule 16), per-year chained on this 15 GB box (rule 12; ~17.5 min/year):
`gas_offer_margin=true` (the go-forward fuel-invariant $/MWh gas offer form —
miso-83 / ERCOT-100 / CAISO / NYISO-72; anchor 3.0492 $/MMBtu, a measured
constant, untouched) and `miso_native_outage_source=true` (MISO's own published
Multiday Operating Margin OUTAGE record replacing the CAMPD unit-level derate).
**Zero fitted scalars**; the two new DOF entries are both measured-physical.

**The composition decision (the open question the wiring doc left to
calibration) — settled on physical feasibility, never on a residual (rule 10).**
The gate + seam had already landed on main (`infra/dam-outage-wiring-4iso`) in
its as-authored form: all four cause buckets against a fossil-thermal
denominator. That form is **refuted by MISO's own metered output**: EIA-930
daily-max coal+gas generation exceeds the all-cause envelope's implied available
thermal capacity on **12 / 15 / 61 days** of 2023 / 2024 / 2025 (worst +12.7 GW;
July-2025 mean headroom 0.3 GW on a 118 GW fleet, before reserves) — under it the
model cannot reproduce its own C1-validated dispatch. The record is a
whole-registered-fleet total with no fuel identity, and `Planned` (17.6–20.6 GW
mean; 36.4 GW April vs 7.9 GW July) is both the model's own layer (statistical
POF / CAMPD windows / nuclear overlay) and where the non-thermal scheduled work
sits. So the derate now defaults to the **UNPLANNED components** (Derated +
Forced + Unplanned) — the same call the sibling PJM instrument made independently
(`PJM_OUTAGE_DEFAULT_TYPES`). `Derated` peaks in **July–August** (10.5 vs 6.0 GW
in March): an ambient capability derate, what GADS EFORd counts, so it stays in.
Evidence: `scripts/probes/_miso85_outage_composition.py`; doc updated at
`docs/handoffs/miso-native-outage-wiring-2026-07.md` §Composition.

**Determination NOT-YET — a further downgrade from miso-81's
CALIBRATED-WITH-CAVEATS.** C6/C7/C8 PASS (attestation + regenerated
`legitimacy_diagnostics.json`), C2/C3c/C4/C5a PASS. Three FAILs, all left
**UNLEDGERED as MODEL MISSes** (rules 1/10 forbid rescuing a determination with
caveats):

| criterion | miso-81 keeper | miso-85 |
|---|---|---|
| C1 fuel-mix | PASS | **FAIL** — 2023 COAL_PRB **+28.3 TWh** (+5.1pp) / CC_REGULAR **−22.7 TWh**; 2024 +21.1 / −14.8 TWh |
| C3a mean LMP | CAVEAT (ledgered, −16.2 % 2025) | **FAIL** — 2025 **+43.5 %** (opposite direction; not covered by the inherited caveat, so not inherited) |
| C3b duration/shape | PASS | **FAIL** — NRMSE 0.284 / 0.306 / 1.072 |

Dispatch shift vs the miso-81 keeper (2023, TWh): COAL_PRB +27.2, COAL_BIT +3.0,
ST_GAS +3.2, CC_REGULAR −14.4, CC_CHP −5.7, CT_PEAKER −6.9, CT_CHP −2.3,
imports −7.6.

**ROOT CAUSE — measured, price-independent, and OPEN (rule 11).** MISO publishes
outages at region × cause grain with **no unit or fuel identity**, so the only
admissible transform is a **uniform** availability envelope: 0.184 / 0.205 /
0.237 unavailable. The per-unit CAMPD record it replaces measures unavailability
that is emphatically **not** uniform:

| class (GW) | CAMPD measured unavailability 2023 / 2024 / 2025 |
|---|---|
| COAL (44.4) | 0.332 / 0.325 / 0.264 |
| ST_GAS (11.6) | 0.589 / 0.529 / 0.508 |
| CC_REGULAR (28.3) | 0.200 / 0.210 / 0.251 |
| CC_CHP (7.0) | 0.073 / 0.093 / 0.075 |
| CT_PEAKER (22.4) / CT_CHP (2.6) | 0.000 — outside the instrument's coverage |
| *uniform envelope* | *0.184 / 0.205 / 0.237* |

MISO's coal fleet carries far more outage than the fleet average, so a
fleet-uniform rate returns ~5 GW of coal to the merit order that was actually
out; being the cheapest steel in MISO it immediately displaces combined-cycle
gas (the C1 miss). The same uniformity removes ~4–5 GW from a 22.4 GW peaking
fleet the per-unit record never says was out, which is what manufactures the 2025
tail (C3a +43.5 %; model 138 h > $200 vs 38 h actual). This is the
aggregate-grain tradeoff the wiring doc flagged — now measured, not asserted.

**The overlay is KEPT (rule 1) and was NOT tuned (rules 1/10).** No parameter was
moved to rescue the fit, no cause set was picked to improve a residual, and the
CAMPD path was not reinstated. What the published record *does* validate is the
**level and timing**: its unplanned unavailability (0.18–0.24) brackets the CAMPD
stack's own (0.236 fleet-average, 2023), and both of its seasonal signatures
(summer `Derated`, shoulder `Planned`) are exactly what the physics predicts.

**Note for the next session — the two named composition alternatives are both
closed at this grain.** *Residual composition* (measured envelope over what the
per-unit windows already account for) is **inert**: CAMPD already accounts for
27.9 GW mean offline in 2023 vs the record's 21.8 GW unplanned total, so the
residual is zero. *All-cause residual* is **infeasible** (the 12/15/61-day
refutation above). The open lever is therefore **fuel attribution** — a
cross-fuel split of the published total (e.g. CAMPD-derived class outage shares
as the attribution key, with MISO's record setting the total), which is a new
mechanism needing its own charter, not a parameter.

**Rule-22 posture.** LOO within 2023–2025 is degenerate-but-satisfied: the
mechanism has zero free parameters and degrades in **every** year (C1 2023+2024,
C3b all three), so there is no in-sample gain with held-out degradation. The
composition test itself is year-independent (all-cause refuted in each of the
three years separately; unplanned feasible in each). **Holdouts untouched** —
MISO carries no calibration-complete marker; only 2023/2024/2025 were solved,
scored, or read. Next number: miso-86 (used below).

## 2026-07-24 — miso-86: net-revenue gas offer margin on the CAMPD unit-level outage derate — PROMOTED as the MISO keeper; the miso-85 published-outage overlay is REVERTED on grain (owner call), determination NOT-YET

**Owner call (2026-07-24, after the miso-85 result).** *"Okay so miso DAM data we
have is not actually a per plant breakdown? Ok then let's use campd unit layer
for miso outages but net rev margin for offer curves."* Confirmed: MISO's public
Multiday Operating Margin OUTAGE sheet is **region × cause daily MW only** — no
unit, plant, or fuel identity is published, so the overlay can only ever enter as
a uniform fleet envelope. That grain (not the record's accuracy) is what broke
miso-85. Keeper is therefore **`2026-07-24-miso-86-netrev-margin`**
(`results/calibration/miso86_netrev_margin`): the net-revenue margin **kept**,
outages **back on the CAMPD unit-level derate**.

**What was solved.** SINGLE delta on the `2026-07-20-miso-81-phantom-outage`
recipe via `replay_keeper` — `gas_offer_margin=true` — full span 2023–2025 in ONE
bundle (rule 16), per-year chained (rule 12; ~16–17 min/year). No
`miso_native_outage_source`. Zero fitted scalars; the one new DOF entry (the
3.0492 $/MMBtu anchor) is measured-physical and untouched (rule 23).

**Determination NOT-YET — reproduces the miso-83 verdict exactly**, on the same
two marginal crossings, both left **UNLEDGERED as MODEL MISSes** (rules 1/10):
**C1 fuel-mix CC_REGULAR 2023 −8.62 TWh** (band ±8.0; the below-anchor firming
sheds ~0.86 TWh of CC dispatch) and **C3b price_shape 2025 NRMSE 0.204** (veto
≤0.20). C3a-2025 (−16.2 %) and C3c (0 h / 6 h / 0 h > $200 vs 30/37/88 actual)
stay **ledgered caveats**, inherited unchanged from the miso-81 attestation —
same criteria, same direction, same magnitude they were adjudicated on (the
miso-82 externally-validated scarcity-representation frontier). C2/C4/C5a/C6/C7/C8
PASS. `calibration-keeper-auditor` PASS, 0 failures.

**Why the overlay was reverted — and why that is NOT a fit-driven revert (rule 11).**
The published record is *misaligned to our representation*, which is the one
exception rule 11 allows: it is defined on the whole registered fleet with no
fuel identity, while the model needs per-class availability. Its level and timing
are sound (unplanned unavailability 0.184/0.205/0.237 brackets the CAMPD stack's
own 0.236; `Derated` peaks July–August as an ambient derate must; `Planned` peaks
36.4 GW in April). Its **attribution** is not: the per-unit CAMPD record measures
COAL 0.332/0.325/0.264, ST_GAS 0.589/0.529/0.508, CC_REGULAR 0.200/0.210/0.251,
CT 0.000, so the uniform envelope returns ~5 GW of out-of-service coal to the
merit order (C1 COAL_PRB +28.3 TWh / CC_REGULAR −22.7 TWh in 2023) and strips
~4–5 GW off 22.4 GW of peakers nothing says were out (C3a-2025 +43.5 %, 138 model
tail hours vs 38 actual). Full write-up:
`results/calibration/FINDING-miso85-published-outage-grain-2026-07.md`.

**What survives from miso-85** (nothing is un-done that was measured): the
`miso_native_outage_source` gate stays wired and **default-off**; its cause-set
composition stays settled at the UNPLANNED components with the feasibility
evidence (`scripts/probes/_miso85_outage_composition.py`, wiring doc §Composition
— the all-cause form is refuted on 12/15/61 days in 2023/2024/2025 and must not
be re-armed); the miso-85 bundle stays registered on the explorer marked
**(PROBE — REJECTED)** per rule 15, since it is the evidence for this decision.
The open lever is unchanged: a cross-fuel **attribution** split (MISO's record for
*how much*, a measured key for *where*), which needs its own charter.

**Dashboard.** MISO run explorer pruned from 16 runs to **2** — the keeper
`2026-07-24-miso-86-netrev-margin` and the rejected `2026-07-24-miso-85-dam-outage`
probe. All 15 pre-existing MISO runs' registry+payload were removed; the
`miso81_phantom_outage` bundle dir is kept on disk as the replay base.

**Rule-22 posture.** Holdouts untouched — MISO carries no calibration-complete
marker; only 2023/2024/2025 were solved, scored or read. The margin's effect is
scored in every one of the three training years (the miso-83 A/B table), so the
LOO check has no in-sample-gain/held-out-degradation asymmetry to hide. Next
number: miso-87.

## 2026-07-24 — miso-87: root-cause session (no solve). C1 localized to TWO per-plant input defects; C3b localized to the 2025 summer BODY (only ~38 % ledgered); the cross-fuel outage-attribution lever is REFUTED AT CHARTER. Keeper unchanged.

**Owner call (2026-07-24).** Lane B (root-cause the two NOT-YET crossings,
structural only) **plus** the Lane A charter, after the like-for-like level check
below showed Lane A's premise was an artifact. No LP was solved this session, so
nothing is registered and the keeper stays
**`2026-07-24-miso-86-netrev-margin`**, determination **NOT-YET**, unchanged.
Everything below is read off committed artifacts (the keeper's `hourly/`
sidecars, run payload, `bench/MISO/*.json.gz`) plus the measured source records.

**C1 `CC_REGULAR` 2023 −8.62 TWh — NOT the offer bands, NOT the tranche split,
NOT availability.** The miss is per-plant and two plants carry it, plant-matched
on both sides of the scorecard:

| plant (ORIS) | zone | MW | CFm/CFa 2023 | 2024 | 2025 | 3-yr ΔTWh |
|---|---|---|---|---|---|---|
| Riverside Energy Center (55641) | MISO-East | 675 | **0.01**/0.60 | **0.05**/0.57 | **0.01**/0.56 | **−9.87** |
| Cottonwood Energy Co LP (55358) | MISO-South | 1434 | 0.32/0.47 | 0.27/0.48 | **0.05**/0.37 | **−8.42** |

Together **−18.30 TWh / 3 yr (−6.10 TWh/yr)** against a ±8.0 TWh band, while the
rest of the CC fleet brackets the actuals in both directions (Montgomery County
+4.07, Union Power +3.97, Holland +2.61) — not the signature of a class-wide
offer error. Availability is ruled out directly: Riverside's CAMPD unit-outage
derate is **mean 0.687**, so the LP can offer it two-thirds of the year and
declines. Both defects live in one derived table,
`data/raw/_processed-legacy/bin_assignments_MISO.csv`:

1. **Riverside `Plant_Avg_HR_MMBtu_MWh = 14.964`** (solve fleet: 8 tranches,
   HR 13.77→15.68) against a rest-of-fleet min/median/max of **6.25 / 7.41 /
   8.89**, on a plant EIA-860 records as three NGCC generators in service
   **2004**. Physically unattainable for any CC; it prices Riverside near
   $45/MWh where comparable MISO CCs offer ~$20/MWh — above most MISO coal.
2. **Cottonwood `Nameplate_MW = 580.4`** against an EIA-860 operable nameplate of
   **1433.6 MW** (ratio 0.405; the only MISO CC >400 MW below 75 %). Self-refuting
   inside the model's own inputs: 580.4 MW × 8760 h = **5.084 TWh/yr** while the
   benchmark's CAMPD series for that plant records **5.866 TWh in 2023**.

Neither claim appeals to a residual (rules 1/10 not engaged); each is refuted by
a measured record independent of model output, so **rule 11 applies in the
forward direction** — the accurate data should replace these estimates whatever
it does to the fit. Expected direction is in fact *against* C3b (restoring
~1.4 GW of under-offered CC pushes prices down, and C3b-2025 is already a
low-price miss), so the two crossings are **not** jointly closable by this fix
and it must not be adopted on the expectation that it improves the determination.

**Systemic gap.** `cc_capacity_reconcile_<ISO>.csv` guards CC capacity in ONE
direction only — it trims plants whose CAMPD-derived pmax *exceeds* the EIA-860
trusted bound (seven MISO plants trip it every fleet build; 1.03 GW removed from
55380 alone) with no counterpart for capacity far *below* nameplate, and there is
**no plausibility guard on the derived heat rate at all**. Both guards are
data-quality checks against primary sources, not residual-tuned parameters, so
they are rule-23 admissible.

**Provenance still OPEN.** Neither 55641 nor 55358 appears in any
`data/raw/campd-unit-level/*.parquet` in the repo, yet both carry
`Committed_Source = campd` in the bin table and both have a committed benchmark
CAMPD series — Riverside's itself impossible (7.989 TWh on 674.9 MW = CF
**1.35**). The derive script that wrote `bin_assignments_MISO.csv` read a CAMPD
source this session could not locate; that source is where both errors
originate. Auditing it, re-deriving the table citing the source-data correction
(rule 23), adding the two symmetric guards, and a full 2023–2025 re-solve is the
next session's work. Finding:
`results/calibration/FINDING-miso87-c1-per-plant-input-defects-2026-07.md`;
probe `scripts/probes/_miso87_c1_plant_defects.py`.

**C3b 2025 NRMSE 0.204 — a monthly LEVEL miss, and the ledger covers only part
of it.** C3b is a 12-point monthly load-weighted metric (not the hourly duration
curve). 2025 decomposes to **June −$17.7 (31 % of Σ Δ²) + July −$18.5 (34 %)** =
**65 %**; with Jan and Sep, 85 %. Every month but May is negative. The passing
years are diffuse by comparison (2023 no month >27 %, both signs; 2024 peaks 28 %).

The C3a-2025 ledger asserts the annual-mean miss is "the arithmetic tail of the
C3c residual, NOT an independent level error". At monthly resolution that is only
**partly** true. Indiana-Hub RT 2025's 88 hours >$200 do cluster where C3b hurts
(Jun 21, Jul 13, Sep 8, Jan 16) but contribute only **+$7.0 of the −$17.7** June
gap and **+$5.5 of the −$18.5** July gap (≈38 % / ≈30 %). Censor the actual at
$200 and June still reads $50.4 vs the model's $39.7. So **$11–13/MWh per summer
month sits in the BODY, below $200 — outside the C3c ledger's scope, and
currently unledgered.**

Ruled out as causes: the gas anchor (2025 summer citygate Jun $2.72 / Jul $2.95 /
Aug $2.62 is *below* the 3.0492 anchor, so the margin's below-anchor firming
raises summer CC offers — it cannot produce a low-price miss) and the C1 defects
above (they push the same months further down). **Do not close this by widening
the C3c ledger, with a summer multiplier, or with an offer adder** (rules 1/10).
Needs its own charter on 2025 summer body price formation, LOO-scored within
2023–2025. Finding:
`results/calibration/FINDING-miso87-c3b-summer-2025-body-2026-07.md`.

**Cross-fuel outage attribution (the miso-85/86 open lever) — REFUTED AT
CHARTER, before any solve.** Two independent grounds
(`scripts/probes/_miso87_outage_attribution_feasibility.py`):

1. *The motivating residual is a category mismatch.* CAMPD's 27.9 GW is
   all-cause and thermal-only; the record's 21.8 GW is unplanned-only and
   whole-fleet. On a like-for-like all-cause footing, against MISO's actual
   thermal share (**129.7–136.8 GW of 212.6 GW registered = 0.610–0.644**,
   EIA-860 operable BA=MISO), the reconciling share is **0.655 / 0.650 / 0.518**
   for 2023/24/25 — the two records agree to **~1–2 GW** in 2023–2024, and the
   discrepancy **flips sign** in 2025 (published implies 4.5–6 GW *more* thermal
   offline than CAMPD measures). A quantity that is ~zero in two years and
   reverses in the third is the aggregate record's resolution limit, not a
   forward-reproducible signal (rule 13).
2. *No admissible key.* MISO publishes region × cause only — no fuel identity and
   no thermal share. The only per-fuel key in evidence is CAMPD itself, which
   makes the mechanism reduce algebraically to
   `CAMPD_shape × (assumed thermal share ÷ actual share)` — a **scalar level
   knob on an unmeasured assumption** (rule 10; rule 20 would force it into
   `ScenarioConfig` as exactly that). A non-CAMPD key (GADS/EIA-860 class rates)
   fixes the key but then does not need MISO's total at all — a different
   mechanism, different charter.

Lever **closed**. `miso_native_outage_source` posture is unchanged: wired,
default-off, cause set settled at the UNPLANNED components, all-cause still
refuted on physical feasibility (miso-85). What remains genuinely open and is
*not* this mechanism: the **CT coverage hole** — 25.0 GW of MISO peaking capacity
(CT_PEAKER 22.4 + CT_CHP 2.6) carrying CAMPD unavailability of exactly 0.000,
modelled today only by the statistical WEFOR/POF layer. Own charter, own
evidence. Finding:
`results/calibration/FINDING-miso87-cross-fuel-attribution-refuted-2026-07.md`.

**Rule-22 posture.** Holdouts untouched — MISO carries no calibration-complete
marker; only 2023/2024/2025 were solved, scored or read this session, and in fact
no solve was run at all. Next number: miso-88.

## 2026-07-25 — miso-88: C1 CLOSED at its source — the CC_REGULAR volume miss was an eGRID heat-rate boundary contamination (Riverside 55641), not a market-structure problem; keeper PROMOTED on structural fidelity; NOT-YET now on ONE fail (C3b-2025)

**Lane:** LANE 1 of the miso-87 handoff. **Keeper → `2026-07-25-miso-88-egrid-hr`**
(bundle `results/calibration/miso88_egrid_hr`), superseding
`2026-07-24-miso-86-netrev-margin`. **Determination: NOT-YET**, on ONE
load-bearing FAIL instead of two. Charter (written before the solve):
`docs/handoffs/miso-88-egrid-hr-boundary-plan-2026-07.md`.

### The charter revised the handoff on three points before any code changed

1. **`bin_assignments_MISO.csv` is an EXPORT, not a solve input.** Written by
   `scripts/export_iso_bin_assignments.py`; the only column any solve path reads
   is `Mixed_Facility` (`campd_bins.ct_intermediate_plants`).
   `Plant_Avg_HR_MMBtu_MWh` and `Nameplate_MW` are written, never read — the
   handoff's "re-derive that table" step would have changed no LP coefficient.
   The live values come from `eia860_generators.parquet` via
   `fleet/eia860.py::load_fleet_from_csv`.
2. **There was no mystery CAMPD source.** Both plants are in the committed
   extracts (`WI_*.parquet` facility 55641 = 35,040 rows = 4 units × 8760;
   `TX_*.parquet` 55358). The "impossible" Riverside CAMPD series (7.989 TWh on a
   674.9 MW plant) is not corrupt — CEMS facility 55641 covers TWO EIA plants.
3. **Defect 2 (Cottonwood 55358) was NOT LIVE — already fixed.**
   `carry_operating_mothballs` is `True` in the miso-86 keeper, and the live
   fleet carries 55358 at **1153.0 MW (2023) / 1149.1 MW (2024)**, the whole
   plant. Only 2025 under-carries (580.4 MW) and that is the *documented,
   owner-defaulted* accepted gap (no `vintage_2025/`; undercarry plan §10).
   miso-87 read the export table (built with no `year`, so the re-carry never
   applies) and compared net-summer-of-OP against nameplate-of-all-8 — two
   different bases. **No below-nameplate capacity guard was added:** the defect
   does not exist, and such a guard would inflate capacity for genuinely
   mothballed units, which is exactly the judgment the vintage-status oracle
   exists to make on measured evidence.

### Defect 1 (LIVE) — eGRID double-counts West Riverside's heat input

eGRID keys PLNT23 on ORISPL, but CEMS reports co-located plants sharing a stack
under ONE facilityId. **Riverside Energy Center** (EIA 55641, 3 × NGCC, 2004,
534.8 MW net summer) and **West Riverside** (EIA 64020, 2020, 684.2 MW) sit
**454 m apart** and share CEMS facility 55641. So:

| | ORISPL | NAMEPCAP | CAPFAC | PLHTIAN (MMBtu) | PLNGENAN (MWh) | PLHTRT |
|---|---|---|---|---|---|---|
| Riverside | 55641 | 674.9 | 0.599 | **53,017,211** | 3,543,044 | **14,963.7** |
| West Riverside | 64020 | 727.6 | 0.668 | 28,265,611 | 4,259,326 | 6,644.9 |

`PLHTIAN` 53,017,211 is **byte-identical** to the sum of `heatInput` over all
four units of CEMS facility 55641 (both blocks), while `PLNGENAN` covers only
the 674.9 MW EIA plant (eGRID's own `CAPFAC × NAMEPCAP × 8760` = 3.543 TWh
confirms). West Riverside's fuel is counted twice. eGRID's UNT23 sheet says so
outright — 55641 carries CT-01/CT-02 at `UNTYRONL` **2004** and CT-03/CT-04 at
**2019**, while plant 55641 has *no* generator of 2019/2020 vintage, and 64020
reports the same two machines independently from a different source
(`HTIANSRC` = EIA Unit-level Data vs EPA/CAPD). eGRID also flags it in metadata:
55641 has `NUMUNT = 4` against `NUMGEN = 3`.

**Market consequence:** at ~$3/MMBtu the plant offered near **$45/MWh** against
~$20/MWh for comparable MISO CCs — above most MISO coal — so the LP never
committed it. Model CF **0.01 / 0.05 / 0.01** vs actual **0.60 / 0.57 / 0.56**.
Availability was not the cause (CAMPD derate mean 0.687 in 2023). *This is what
the previous two keepers were chasing through offer bands, tranche splits and
availability — none of which were the cause.*

**Boundary-consistent value: 6.880 MMBtu/MWh** (own units CT-01 + CT-02 =
24,376,259 MMBtu over `PLNGENAN` 3,543,044). Cross-validated three independent
ways: sibling subtraction **6.986**; CEMS gross-basis CT-01+CT-02
**6.624/6.642/6.646**; eGRID's own `PLHTRT` for 64020 **6.645**. Rule 11's named
boundary-mismatch exception, reconciled rather than guessed; no appeal to any
model output, so rules 1/10 are not engaged.

### Scope established BEFORE writing the fix — and a general rule REFUSED

A raw envelope screen flags 19 plants / 10.7 GW across six ISOs, but over-selects
badly: most are low-utilisation idle-heat artifacts (Goose Creek CF 0.0001 → HR
102.6; Calumet 0.0008 → 20.6). Adding a `CAPFAC ≥ 0.25` discriminator leaves 5,
of which Riverside is the only one materially over its band (**1.58×**; the rest
1.01–1.09×). A **general** vintage-attribution repair — drop every UNT23 unit
whose vintage matches no EIA-860 generator at its plant — was designed, sized and
**REFUSED**: it touches **47 plants and destroys 25** (French Island → HR 0.011,
Ivanpah 3 → 0.873, V H Braunig → 0.502), because EIA-860's operable snapshot
omits retired units CEMS still reports, so removing their heat input guts the
numerator while `PLNGENAN` stays the whole-plant total.

### The fix — four conditions, the last self-validating, zero tuned parameters

In `fleet/eia860.py::_egrid_boundary_hr_repairs`, applied at the single seam
(`_rows_to_generators`) every read path passes through — canonical snapshot,
per-year vintages, mothball re-carry. Curation keeps writing eGRID's value
verbatim (and cannot be re-run here: its `eia8602024.zip` input is not
committed). Repair only when: (1) `PLHTRT` exceeds
`HEAT_RATE_BINS["gas_ct"]["older"]` = 11.5 — a CC raises steam from its own
topping turbine's exhaust so it cannot be less efficient than a bare
simple-cycle GT of its era, a physics bound off an existing cited constant, not
a fitted multiple; (2) a co-located sibling within 1.0 km reports its own
`PLHTIAN > 0`; (3) the plant carries UNT23 units whose vintage is within 1 yr of
a *sibling* EIA-860 generator vintage and of **none** of its own, leaving ≥1 unit
with positive heat input; (4) **the recomputed rate lands back at or below the
same ceiling** — the repair is accepted only because it resolves an
impossibility.

Condition 4 is what makes it safe. Without it the detector also fires on
**Devon 544** (876.6 → 340.1, garbage either way, already dropped by the
pre-existing 3,000–30,000 Btu/kWh window) and **King City 10294**
(7.855 → 8.998, a *degradation* of an already-plausible value). Both are
correctly rejected — Devon by (4), King City by (1). **Across all six ISOs the
accepted set is exactly `{55641: 6.880}`.** Verified blast radius by diffing the
built fleet with and without: **3 rows, 1 plant, MISO only**; ERCOT/CAISO/PJM/
NYISO/NEISO byte-unchanged, no rows added or removed. 11 new tests; full suite
identical failure set to clean `origin/main` (107 pre-existing failures both
ways, +11 passes = exactly the new tests).

### Result — C1 closed, on ONE fail instead of two

| criterion | miso-86 keeper | **miso-88** |
|---|---|---|
| C1 fuel-mix | **FAIL** | **PASS** ✅ |
| C2 system volume | PASS | PASS |
| C3a mean LMP | CAVEAT (ledgered) | CAVEAT (ledgered, widened) |
| C3b price shape | **FAIL** 0.204 | **FAIL** 0.208 |
| C3c price tail | CAVEAT (ledgered) | CAVEAT (ledgered, unchanged) |
| C4 / C5a / C6 / C7 / C8 | PASS | PASS |

`CC_REGULAR` model−actual improves in **all three years**: 2023 **−6.71 → −4.99**
TWh, 2024 **−2.09 → −0.42**, 2025 **−6.14 → −4.19** (displacement lands on
COAL_PRB, which stays inside its band). Determination **NOT-YET** on
`price_shape` alone.

**Both worsened price crossings were PRE-REGISTERED in the charter §5 before the
solve** as the arithmetic consequence of returning 534.8 MW of cheap CC to the
merit order: C3b-2025 0.204 → 0.208, and the ledgered C3a-2025 caveat widening
−14.8% → −16.6%. They are **KEPT per rules 1/11** — the accurate input stays in
even though it worsens the fit, and the worse fit is a discovered-bug signal to
root-cause separately, **never** to be offset with a tuned adder. The residual is
now a *price-formation* question about 2025 summer body hours
(`FINDING-miso87-c3b-summer-2025-body-2026-07.md`, the miso-87 LANE-2 charter),
not a volume question.

**Promoted on structural fidelity** (rule 1: the keeper is the most faithful run,
not the lowest MAE) — the superseded keeper carries a provably wrong measured
heat rate, and rule 11 forbids reverting to it. **Rule 22 LOO:** the correction
has **zero degrees of freedom** and one value identical in every year, so nothing
is year-specific to overfit, and the C1 gain is uniform across 2023/2024/2025.
Full span in ONE bundle (rule 16). keeper-auditor `--iso MISO`: **PASS, 0
failures**. Registry/payload parity: **MISO clean** (the CAISO/NEISO/PJM entries
in that report are pre-existing).

### Two operational notes for the next session

* **A 3-year single-process solve OOM-kills this container** (15.95 GB RSS on a
  15 GB box, killed mid-2024). The handoff's "one fresh year per process" is
  load-bearing: use the staged `--reuse-solved` recipe, and note the reuse gate
  needs a *completed* prior bundle (it reads `meta.json` + `run_config.json` +
  `system.parquet`), so leg 1 must be a full single-year run. Per-year cost here:
  708 / 749 / 800 s.
* **`scripts/render_calibration_html.py` was committed corrupt on `origin/main`**
  — commit `2668ae0` ("Add per-class model-minus-actual delta heatmap…", PR
  #2866) clobbered it from 1,911 lines to a single stray tool-argument line
  (`1 insertion, 1911 deletions`, nothing else in the commit), breaking pytest
  collection for six test modules. Restored byte-identical to the last-good blob
  at `5499181` (sha256 `49196d4d5811f58a`) per rule 27. The intended feature work
  in that commit never landed and is still missing. `file-integrity-guard.yml`
  did not block it — worth a look.

## 2026-07-26 — miso-90: OWNER DECISION taken — C3b-2025 LEDGERED as instrument-blocked and MISO RE-GATED to CALIBRATED-WITH-CAVEATS; three side lanes resolved, two of them by refuting their own premise

**Lane:** the miso-89 three-way owner decision, plus all three ready side lanes.
**Keeper UNCHANGED — `2026-07-25-miso-88-egrid-hr`.** No solve was run this
session; nothing about the run, its bundle, its config or any solved artifact
changed. **Determination: NOT-YET → CALIBRATED-WITH-CAVEATS**, by scoring alone.

### The decision

The owner chose **options 1 AND 2** (ledger + re-gate, and open the data ask),
and directed all three side lanes.

**C3b-2025 is now ledgered.** The one load-bearing FAIL (monthly load-weighted
price NRMSE 0.208 vs a ≤0.20 veto; 2023 0.081 and 2024 0.129 both PASS) is
documented on the C3c template as an **instrument-blocked measurement gap**, with
miso-89's difference-in-differences as its evidence: model fossil derate at
Jun/Jul HE16–18 is flat across years (+1.76 GW into 2025) while MISO's published
offline record jumps +12.32 GW, breaking a stable ~14.6 GW offset to 24.76 GW —
a ~10 GW under-derate, at normal summer temperatures (zone-mean TMAX 29.6 / 29.2
/ 29.8 °C) with cheap gas. Ledgered per **rule 24** rather than tuned: no
measured source resolves at the needed grain, so the honest outcome is to
document, size and stop. The entry explicitly does **not** license an offer
adder, a summer multiplier, or widening the C3c ledger to absorb it.

**Governance consequence — the budget is now saturated.** Ledgered
non-protective caveats go 2 → **3/3** (C3a, C3b, C3c; `MAX_LEDGERED_CAVEATS = 3`,
the check is `> 3`). **No further load-bearing MISO criterion can be ledgered**
without forcing the determination back to NOT-YET. The next load-bearing miss
must be BUILT, not documented — which is what makes the data ask load-bearing.

keeper-auditor `--iso MISO`: **PASS, 0 failures**. Note MISO still carries **no
calibration-complete marker**, and this re-gate does not create one — declaring
an ISO complete is a separate explicit owner instruction, and the holdout
quarantine stays fully in force.

### Data ask opened (option 2)

`docs/handoffs/miso-outage-grain-data-ask-2026-07.md` — a standing, blocking ask
for MISO outage data at unit or fuel grain. Its acceptance test has four parts,
and the **first is the one that matters**: the source must declare **capability**,
not output. That single criterion rejects CAMPD, EIA-923 and every derivative of
either, which is why the ask is genuinely blocking rather than merely unattempted.

### LANE B' — the CT "coverage hole" is an IDENTIFICATION exclusion, not a data gap

`results/calibration/FINDING-miso90-ct-availability-identification-2026-07.md`.
Taken on its own merits (rule 11), **NO-BUILD**. The 0 % CT measured-derate
coverage is deliberate and documented: *"a CT down-window cannot be certified a
forced outage vs out-of-merit-at-peak"* (`data/outages.py`, enforced at
`_unit_outage_target`). For a peaker, not running is the default state, so
absence of output carries no information about availability — **every
output-derived instrument inherits the defect**. Verified rather than assumed:
the EIA-923 fallback landed 2026-07-24 has **zero CT_PEAKER rows in nine years**
and excludes peakers by the same rule.

Two corrections to the inbound framing: the handoff's "CT_PEAKER + CT_CHP =
25.02 GW at 0.0 % coverage" conflates two classes at two different stages —
CT_PEAKER is never detected (0 rows), while CT_CHP **is** detected (115 rows /
27 plants) and then dropped one stage later. And the live defect that *is*
actionable is separate: `_SUMMER_WEFOR_SHARE = 0.30`, which governs summer
availability for all 22.39 GW of CT_PEAKER, **carries no citation, appears in
neither `docs/parameter-citations.md` nor the keeper's 26-entry DOF ledger**.
Deliberately NOT re-tuned here (that is the rule-24 answer-key move, and doing it
in the session that ledgered C3b would be indistinguishable from tuning to the
ledgered miss). It should be DOF-declared and named as a target of the data ask.

### LANE C' — the memory lever is refuted by measurement

`results/calibration/FINDING-miso90-solve-memory-attribution-2026-07.md`. The
handoff's lead lever — the ~26 unbounded module `lru_cache`s — holds **0.019 GB**
on the MISO path, and a *second* year adds **0.000 GB**, so they cannot be the
mechanism by which the floor rises. The second lever (release fleet objects) is
already done. Attribution of the 1.56 GB floor: ~0.12 imports, ~0.02 caches,
~0.07 accumulators, **~1.35 GB unattributed** — 86 % that no hypothesis on record
covered. Rather than propose a fourth story, this session shipped the
measurement: `src/market_sim/data/cache_control.py` plus per-year retained-heap
telemetry in the runner. `clear_all_caches()` exists but is deliberately **NOT**
wired into the year loop — 0.02 GB against a 1.35 GB gap is not worth the
correctness risk (rule 1: don't add a mechanism that doesn't address the cause).
**The 14.4 GB single-year peak is untouched; the staged `--reuse-solved` recipe
remains necessary.**

### HYGIENE — the integrity guard was already fixed; the gap was a regression test

`file-integrity-guard.yml` was added 2026-07-23, the `2668ae0` truncation landed
2026-07-24, and **two fixes landed 2026-07-25** — after the miso-89 handoff
flagged it. Verified by replaying the current guard against the real `2668ae0`:
exit 1, correct error. What was missing was cover, so the guard had been fixed
twice in one day for bash failure modes invisible to a plain replay. Added
`tests/test_file_integrity_guard.py` (7 cases), which extracts the guard's own
`run:` body from the workflow YAML and replays it under `bash -e`. Validated in
both directions: all pass on the current guard, and the PR #2866 case was
confirmed to **FAIL** against the pre-fix version (exit 0 on a 1,911 → 1 line
truncation, with the documented `((: 0\n0: syntax error`).

### Notes for the next session

* **Test baseline discrepancy, unresolved.** The handoff records 108 pre-existing
  full-suite failures; this branch measures **90** (with the same two collection-
  error modules ignored). Not chased down — the targeted baseline the handoff
  gave for the touched area (`run_calibration_full` importers: **8 failed / 186
  passed**) reproduced exactly, and no failure is in a file this session touched.
  Someone should re-establish the real number.
* **Two cheap follow-ups named, neither taken:** DOF-declare
  `_SUMMER_WEFOR_SHARE` (and audit the `_SUMMER_CLASS_DERATE` literals for
  citations); and run one MISO year to read the new retained-heap telemetry,
  which will say whether the ~1.35 GB is live Python payload or allocator/HiGHS
  side — a different fix entirely. Next number: miso-91.

## 2026-07-26 — miso-91: `SUMMER_WEFOR_SHARE` DOF-declared and RE-HOMED into registry coverage; the three rule violations share one root cause (wrong module), and the parameter governs six classes, not one

**Lane:** 1 of the miso-91 handoff (the governance defect miso-90 named).
**Keeper UNCHANGED — `2026-07-25-miso-88-egrid-hr`.** No solve was run; no value
changed anywhere. **Determination UNCHANGED: CALIBRATED-WITH-CAVEATS**, 3/3
ledgered caveats, keeper-auditor **PASS / 0**. Charter (written before any edit):
`docs/handoffs/miso-91-summer-wefor-dof-charter-2026-07.md`.

### The defect had one root cause, not three

`_SUMMER_WEFOR_SHARE = 0.30` was uncited (rule 5), unregistered, and undeclared
(rule 21). Those are not three oversights — they are one: the constant lived in
`data/fleet/arrays.py` as a module-private literal, and
`scripts/validate_parameters.py` scans only `vars(constants)` + `ScenarioConfig`
defaults, skipping anything private or non-uppercase (`:59-69`). It was invisible
to the registry **three ways over** — wrong module, leading underscore, not
uppercase. That is a **rule 20 `[R-REGISTRY]` violation by location**, and it is
what let the other two persist.

**Fixed at the root, not papered over.** `SUMMER_WEFOR_SHARE` and its sibling
`SUMMER_CLASS_DERATE` now live in `config/fuel_trajectories.py` beside the
`THERMAL_AVAILABILITY` table they modify, public and uppercase, imported into
`constants.py` so the registry covers them permanently. Private aliases remain in
`arrays.py` so the availability builder, the fleet package's re-export contract,
`results/scarcity.py` and the ERCOT derive script are untouched by the move.
**Values byte-identical**, verified: the per-class branch map is unchanged to
12 decimal places before and after.

Worth stating plainly: the WEFOR *magnitude* was always GADS-cited
("Source: NERC GADS by unit type and age"). Only its *seasonal reallocation* was
uncited.

### It governs SIX classes, not CT_PEAKER alone — a correction to miso-90

miso-90 scoped the parameter to "all 22.39 GW of MISO CT_PEAKER". Measured this
session (no LP, keeper flags from `run_config.json`: `outage_source='historic'`,
**`wefor_residual=None`**, `coal_drop_pof=True`, `cc_nameplate_summer_derate=False`),
it reaches **every non-coal thermal class**. COAL is genuinely exempt —
`coal_drop_pof=True` routes it to a branch that drops summer WEFOR outright
(measured delta 0.0000). Summer availability the 0.30 adds vs a no-reallocation
baseline:

| ST_GAS | ST_CHP | CT_PEAKER | CC_REGULAR | CT_CHP | CC_CHP | COAL |
|---|---|---|---|---|---|---|
| +14.70 pp | +5.60 | +4.29 | +3.15 | +3.06 | +2.52 | exempt |

The closed form is exact: `(1 − share) × wefor(age) × (1 − class_derate)`. Against
the committed per-class nameplates (FINDING-miso89 §5) that is **≈3.9 GW** of
MISO summer-peak capability at a uniform age of 18 y, **≈4.6 GW** at 28 y,
**≈5.8 GW** at 38 y. ST_GAS takes the largest slice because its GADS WEFOR base
(0.21) is the highest in the table.

### Declared, NOT re-tuned

Both constants are now in the keeper's DOF ledger (26 → **28** entries, 2 → **4**
residual), each with an open root cause pointing at the data ask; auditor E8
confirms no bare residual. **On the label:** neither was ever *fitted*.
`"residual"` was chosen because it is the strictest existing enforcement
category — E8 requires every residual entry to carry an open root cause — and
each entry says so in terms, so no future reader reads the label as "we tuned
this". The truthful description is *unidentified*: no sweep, derivation or
calibration lineage exists for the 0.30.

The value was deliberately left alone. Its ≈3.9–5.8 GW blast radius is the same
order as the ~10 GW summer-peak under-derate ledgered as C3b the day before, so a
hand-set value here would be an answer key for an already-ledgered miss
(rule 24). Nothing here is a load-bearing criterion miss, so **nothing was
ledgered** — the 3/3 budget is untouched.

**Physics tension, recorded in the code, the citation and the data ask.** For
*planned* outages, shifting maintenance off the peak is well-founded (and the POF
side is separately grounded by the measured `MAINTENANCE_MONTHLY_SHAPE`). For
*forced* outages the reallocation runs **opposite** to the physics — forced
outages correlate *positively* with heat and load. So the open question is
whether the mechanism has the **right sign at all**, not merely the right
magnitude. Recorded as an unverified directional argument, not a citation.

Data ask updated with a new §2a: `SUMMER_WEFOR_SHARE` is now the ask's named
replacement target, with two added acceptance criteria — **E** forced/planned
must be separated (the parameter reallocates WEFOR only), **F** class coverage
must be stated and never silently generalised (per-class deltas differ ~6×).

### Two governance findings, neither repaired here

1. **The parameter registry check is documented as a CI gate and is not one.**
   `docs/parameter-citations.md`'s header states it "fails CI"; `grep -rn
   validate_parameters .github/workflows/` returns **nothing**. It also **already
   fails on `main`** — **48** missing citations when this work started, **49** a
   few hours later, **51** by the final rebase, every increment from another lane
   landing an uncited constant. That drift is itself the point: nothing
   stops the backlog growing. So even a correctly-homed constant lands in a
   pre-existing red backlog. Not wired here (wiring an already-red check just
   breaks CI) and the backlog was **not** mass-registered, though
   `generate_parameter_registry.py` will do it in one run — that would mark
   ~50 other lanes' gaps "documented" as `needs-citation` stubs without anyone
   having sourced them. After registering only this session's constants the
   count returns to its baseline and **none of the MISSING entries are ours**:
   the backlog is neither added to nor papered over. **Owner call.**
2. **`wefor_residual = None` in the MISO keeper**, so the cap at `arrays.py:532`
   never fires. That cap exists specifically to stop the statistical WEFOR
   double-counting the CAMPD overlay for covered classes (coal +
   `_POF_DROP_GROUPS`). With it off, MISO's CC and ST classes carry full
   statistical WEFOR *and* the historic overlay. Whether that is deliberate or a
   latent double-count needs a solve to settle and was outside this charter.
   **Flagged, not diagnosed.**

### Verification

* Determination **CALIBRATED-WITH-CAVEATS**, 3 ledgered caveats — unchanged;
  `status/MISO.js` diff is the timestamp only, every criterion byte-identical.
* `audit_keepers.py --iso MISO` → **PASS / 0 failures**.
* `validate_parameters.py` → the backlog is **untouched by this work**, and the
  invariant to check is that assertion, not a count: **none of its MISSING
  entries are the constants moved here** (all five register cleanly). The count
  itself is not a stable baseline — it read **48** when this lane started, **49**
  a few hours later and **51** after the final rebase, every increment coming
  from other lanes landing new uncited constants. That drift is itself the
  governance finding below: nothing gates the backlog, so it grows. The
  transient +5 was visible only in between (53 after the move, before the five
  registry entries landed). The check cannot reach 0 in this lane.
* New `tests/test_summer_availability_constants.py` — 12 tests, all pass: pins
  both values, the registry-visible home, that the `data.fleet` aliases resolve
  to the canonical objects (never a second literal that could drift), the
  six-governed/COAL-exempt branch map, the closed-form delta, and that the
  reallocation conserves annual outage energy.
* `tests/test_fleet.py` + `test_fleet_facade.py` + the new module: **136 passed**.
* `run_calibration_full` importer modules: **8 failed / 186 passed** — exactly the
  inherited baseline; all 8 are pre-existing `test_pipeline_facade_shims`
  failures, untouched by this session.
* Full suite (`-p no:randomly`, the two usual collection-error modules ignored):
  **93 failed / 5020 passed**. Recorded because the inherited number is disputed
  — the handoff says 108, miso-90 measured 90. No failure is in a file this
  session touched.
* Also **appended a dated addendum** to the keeper attestation's
  `governance.note`, whose opening "DETERMINATION NOT-YET" was overtaken by
  miso-90's re-gate. miso-88's prose is left exactly as written and no assertion
  is modified — the addendum only corrects the stale statement of fact.

### Notes for the next session

* **`git push` was INTERMITTENTLY BROKEN for most of this session, then
  recovered — do not read either state as permanent.** For roughly the first
  two hours every push failed: `git-receive-pack` returned **403** on an empty
  POST and **413** with a body, *including for a zero-object push*
  (`origin/main:refs/heads/<new>`), so it was provably **not** a pack-size
  problem and no client setting helped (`http.postBuffer` large → 413, small →
  502, `--no-thin` → 413). Direct `api.github.com` from bash was refused too
  (403, "GitHub access is not enabled for this session"). The work was therefore
  first delivered as an apply-bundle of patches via `mcp__github__push_files`.
  **After a container restart the identical zero-object push succeeded**, and
  this entry and the code change went up over plain `git push`; the staging
  bundle was then deleted as superseded (rule 25 `[R-DELETE]`) — only the
  charter remains.
  Two takeaways for whoever reads this next: (a) the failure is **transient
  infrastructure**, not policy, so a 413/403 on push means *retry later or use
  `push_files`*, not "the transport is banned"; (b) `push_files` is a genuine
  fallback for small multi-file text commits, but it **cannot** carry a large
  modified source file, because inlining one means reproducing it from the
  model's response — the operation rule 27 forbids. Shipping a patch + an
  idempotent replay script is the safe way through that corner, and it was
  verified by applying the bundle to a clean `origin/main` worktree and
  confirming all nine changed files matched byte-for-byte.
* **The 3/3 budget still binds.** Nothing here consumed or freed a caveat slot.
* **Lane 2 (memory telemetry) is still unread** — it needs one solve-year to say
  whether the ~1.35 GB unattributed floor is live Python payload or
  allocator/HiGHS-side. Untouched by this session.
* Next number: **miso-92**.
## 2026-07-26 — miso-89 (attempted): keeper re-audit on the guard-corrected CAMPD envelope — BLOCKED on container RAM; keeper UNCHANGED (miso-88)

Charter execution (campd-economic-layup-fix-charter §8). The miso-88-egrid-hr
recipe (per-asset reserve columns, 2,550 members) was OOM-killed at 15.9 GB
RSS / 31 GB VM in this session's 15 GB container — twice, including running
alone. Not skipped: the replay needs a ≥24 GB environment; command and clean
partition prerequisites are recorded in
`results/calibration/RESULTS-neiso65-crossiso-reaudit-2026-07.md` §3e. The
corrected extract (755 windows / 3,630 GW-days reclassified 2023–25) is
committed and IS the envelope MISO now solves against, so until this re-audit
runs, the miso-88 keeper's registered numbers describe the pre-adoption
envelope and will not reproduce at HEAD.

## 2026-07-26 — miso-92: the cross-year memory floor is ATTRIBUTED and 35 % of it REMOVED — one 588.9 MB unit-hour frame the year-release `del` never named

**Lane:** 2 of the miso-92 handoff ("read the memory telemetry"; *"do NOT propose
a fourth story — TAKE THE MEASUREMENT"*).
**Keeper UNCHANGED — `2026-07-25-miso-88-egrid-hr`. Determination UNCHANGED:
CALIBRATED-WITH-CAVEATS**, 3/3 ledgered caveats. No scoring criterion moved, so
no ledger slot was consumed or freed. Charter, written before any telemetry line
existed to read: `docs/handoffs/miso-92-memory-attribution-charter-2026-07.md`.
Full evidence: `results/calibration/FINDING-miso92-solve-memory-attribution-2026-07.md`.

### The answer

miso-90's pre-registered decision rule fired on the **LARGE** branch:
`ndarray_gb = 0.69` against its ≥0.50 threshold, so the floor is live Python
payload. The frame-level telemetry added this session then named the site, which
is a single object:

**588.9 MB — 24,694,440 gen-hours × 11 cols** (`year,pass,unit_id,plant_code,
klass,fuel,supply,zone,hour,mw,lmp`) — still bound to the `_dispf` loop variable
*after* being written to `dispatch/<year>_<pass>.parquet`, with nothing left to
read it. The year-release `del` list names nine locals; `_dispf` is not one of
them, so it survived `gc.collect()` and `malloc_trim(0)` — both of which
correctly decline to free a **live** object — and sat underneath the next year's
fleet build and LP. That is why miso-89's `malloc_trim` helped (2.98 → 1.56 GB)
but could not finish: 589 MB of the remainder was live.

The top six retained objects sum to ≈687 MB ≈ the whole 0.68 GB pandas payload —
**fully attributed, no remainder**. The other five are legitimate (three declared
cross-year accumulators at 0.07 GB, two loader frames).

**One `del` at the write site:** cross-year floor **1.53 → 1.00 GB (−35 %)**,
live `in_use` 0.73 → 0.15 GB, retained payload 0.69 → 0.11 GB. **Dispatch
bit-identical** — `max|diff| = 0` on every column of both sidecars and the
unit-hour parquet sha256-identical (73,683,342 bytes both), since the frame is
already on disk and never read again.

**The 14.4 GB single-year peak is UNCHANGED and was never going to change** (the
frame is built after the LP solves). **The staged one-year-per-process
`--reuse-solved` recipe REMAINS REQUIRED.** It does make miso-89's blocked
re-audit cheaper: that OOM was reported at 15.9 GB ≈ the 14.4 GB peak + the
1.53 GB floor, and the same arithmetic now gives ~15.4 GB — a real reduction
toward, but still above, a 15 GB box.

### Two corrections to the record, both by measurement

1. **The `lru_cache` hypothesis is refuted AGAIN, harder.** miso-90 measured it
   on the data-load path (9 caches / 14 entries); a real solve populates **30 /
   38**, including `_eia_hourly_frame` ×4 — plausible suspects by name. Measured
   directly, **all 9 BA extracts × both caches = 0.015 GB**. High entry count,
   negligible payload. So the suspicion that miso-90 had measured the wrong set
   was itself wrong. `clear_all_caches()` stays unwired.
2. **HiGHS is exonerated.** Pre-fix live malloc = `in_use` 0.73 + `mmapped` 0.37
   = 1.10 GB against a 0.69 GB array payload, bounding C-side retention at
   ~0.29 GB — not the ~1.35 GB the hypothesis needed. Post-fix `in_use` collapses
   to **0.15 GB**: essentially all of it was the one Python frame. No
   "destroy the HiGHS model" work is warranted. Settled by the `mallinfo2` line
   added *before* the first read, precisely so the small-ndarray branch would not
   cost a second solve-year.

### The keeper's non-reproduction at HEAD is EXPECTED — a correction to my own draft

Replaying the keeper's 2023 at HEAD does not reproduce it (mean LWP $31.224 →
$30.770; ST_GAS +2.05 TWh, CT_PEAKER −1.16, COAL_BIT +1.10, COAL_PRB −1.08,
import −1.34; 86.7 % of zone-hours differ). This finding's first draft framed
that as a new defect. **It is not** — the miso-89 entry already records that the
guard-corrected CAMPD economic-layup extract (755 windows / 3,630 GW-days
reclassified, PR #2919) is committed and is the envelope MISO now solves against,
so the keeper's registered numbers describe the pre-adoption envelope. What this
lane adds is the **magnitude** of that pending re-audit's change plus a control:
two identical invocations at HEAD give `max|diff| = 0` everywhere, so it is
**input drift, not nondeterminism**. No link to `wefor_residual` is claimed — the
CAMPD change is a sufficient, already-documented explanation.

### Instrument changes (diagnostic only; none can change dispatch)

* `_glibc_arena_gb()` — `mallinfo2` accounting at the release seam, splitting
  non-Python resident into *glibc holding free* vs *C-side still allocated*.
* `cache_control.largest_retained_frames()` — top retained pandas objects with
  shape and column list (a column list identifies a frame's producer on sight).
  Counts `Series` as well as `DataFrame`, for parity with `retained_footprint`.
* Recorded a coverage fact found by a **failing test**, not assumed: DataFrames
  and Series are **GC-tracked**, so `gc.get_objects()` enumerates them directly
  and this reporter has **no running-locals blind spot** — which is exactly why
  `_dispf`, a function local, was visible at all. Pinned by test.
* The telemetry's blanket `except` logged at **debug** (invisible in a normal
  run). Raised to `warning` with `exc_info`, plus a warning when the frame list
  is empty while `retained_footprint` counted pandas objects.

### Verification

* Determination **CALIBRATED-WITH-CAVEATS**, 3 ledgered caveats — unchanged.
* Dispatch bit-identical pre/post fix (§4 of the finding).
* Memory result reproduced across **four** single-year solves.
* `run_calibration_full` importer modules: **8 failed / 186 passed** — the
  inherited baseline. Composition correction: it is **7 `test_pipeline_facade_
  shims` + 1 `test_flag_registry`**, not "all 8 shims" as the handoff states; all
  8 reproduce on a clean `origin/main` worktree, so none is this session's.
* `tests/test_cache_control.py`: **16 passed** (11 inherited + 5 new).
* `ruff format --check` clean on all touched files.

### Notes for the next session

* **Nothing was registered on the dashboard, deliberately.** All four bundles are
  single-year probes; rule 16 permits a one-year solve only as a throwaway
  diagnostic and forbids registering it. No calibration result was produced — the
  keeper's dispatch was reproduced, not re-scored.
* **A governance finding, same shape as miso-91's.** A one-line `NameError` cost
  a full solve-year: the new import was reverted by a post-edit reformat and the
  debug-level `except` hid it. `ruff check --select F821` reproduces it on the
  broken tree and passes on the fixed one — **the repo applies `ruff format` to
  committed Python but does not run `ruff check`**, so an undefined name reaches
  a solve. Not wired here (same reasoning as miso-91: wiring an ungated check is
  its own triage job). **Owner call.**
* **The 3/3 budget still binds.** Untouched by this session.
* **Charter deviation, declared:** the charter fenced this lane from proposing a
  fix. The `del` overran that fence deliberately — the measurement named a
  specific live object at a specific line and the result was *verified* by
  re-running the same telemetry, not argued. Recorded rather than rationalised.
* Next number: **miso-93.**

## 2026-07-26 — miso-93: the keeper does NOT hold on the guard-corrected CAMPD envelope — RE-TUNE REQUIRED, and the drift is 100 % the extract

**Lane:** A of the miso-93 handoff (top-ranked ready item), executing the
`campd-economic-layup-fix-charter-2026-07.md` §5/§8 blast radius for MISO.
miso-89 attempted this and was RAM-blocked; miso-92's 35 % floor reduction is
what made the staged recipe fit. Charter, pre-registered before any result was
read: `docs/handoffs/miso-93-keeper-reaudit-charter-2026-07.md`. Full evidence:
`results/calibration/FINDING-miso93-keeper-reaudit-meritguard-2026-07.md`.

**Registered arm:** `2026-07-26-miso-93-meritguard-a1` (MISO 2023/2024/2025,
one bundle, rule 16; rule 15 — registered whatever the verdict).

### Verdict

**DETERMINATION `CALIBRATED-WITH-CAVEATS` → `NOT-YET`. RE-TUNE REQUIRED**, on a
single newly-failing gate: **C3a-2024 −8.7 % → −10.1 %**, crossing the ±10 %
veto by **0.1 pp**. C1 (free 12/12), C2, C4, C5a, C6, C7, C8 all still PASS;
C3b/C3c stay ledgered (C3b-2025 NRMSE 0.208 → 0.214). **Nothing was tuned and
nothing is licensed to be** — the ledger budget is 3/3 and this lane consumed
and freed none of it.

**The keeper designation was NOT changed.** miso-88 remains designated, now
carrying a measured re-tune trigger; promoting or demoting on a NOT-YET arm is
an owner call, not a session's.

### The isolation — the code is provably inert, the extract is the whole story

The charter flagged that miso-92's attribution of the HEAD drift to CAMPD was an
attribution, not an isolation (`3babe5f..HEAD` touches `offer_surfaces.py` +391,
`renewables.py` +342, `scenarios.py` +220, `runner.py` +129, six more), and
caiso-123 is the precedent for why that matters. One single-year throwaway probe
closed it — 2024 solved at HEAD with the extract reverted to the keeper's blob
`f2b3ec8`:

| arm | 2024 LW price | C3a |
|---|---|---|
| KEEPER (`3babe5f`, pre-guard extract) | $29.470 | −8.68 % |
| A0′ (HEAD, pre-guard extract) | **$29.470** | −8.68 % |
| A1 (HEAD, guard-corrected extract) | $29.024 | −10.06 % |

**Code drift with the extract held fixed: $+0.000 — exactly zero**; A0′
reproduces the keeper's committed sidecar to three decimals. The post-keeper
code surface is **measured MISO-inert**. The guard/extract accounts for 100 % of
the drift (−$0.445, −1.38 pp). Stable across years: −$0.467 / −$0.445 / −$0.396
(2023/24/25). 2024 fails only because it started closest to the veto. MISO does
**not** carry the confounded-A0 defect — the extract axis was verified
single-delta before solving (blob byte-identical across the keeper's own
`git_sha`, changing exactly once, at the guard commit).

### Why prices fall (measured from the two committed blobs, no solve)

The guard **removes 2,424 windows / 11,614 GW-days and adds zero** (−12.8 % of
the envelope), of which **ST_GAS is 8,541 GW-days (73.5 %)** and CC_REGULAR
1,522 (13.1 %). The 2023–2025 slice is **755 windows / 3,630 GW-days**,
reproducing the figure committed with the guard exactly. Gas *steam* priced out
of merit for weeks was being booked as mechanically unavailable; returning it
adds supply and lowers the clearing price. Corroborated in-run: C8 ST_GAS forced
share rises 35.7→39.9 / 36.9→41.1 / 51.1→53.8 %, all still **grounded** (D-4
clean) so C8 PASSes.

Per **rule 11** this is a discovered bug, not a reason to revert: the keeper's
offer curves were silently compensating for an inflated outage envelope — the
NEISO / ERCOT-79 / nyiso-63 condition, milder here (−1.4 pp vs NEISO's −7…−9 %).

### A clean-partition dependency that was silently contaminating MISO replays

**neiso-65 §2's partition table has no MISO row** (MISO never solved there), and
that omission contaminated this session's first launch.
`model/interchange/miso.py::_miso_cil_cel_groups` builds per-zone seasonal
CIL/CEL interface groups from the `capacity-deliverability` partition and, when
it is absent, falls back to **static PY2025-26 summer caps** —
**independently of the `capacity_deliverability_limits` flag, which is `false`
in this keeper.** Reading the flag is not sufficient to conclude the partition
is unneeded. The degraded launch was killed, its bundle deleted, and no number
from it is quoted; every arm here solved with `capacity-deliverability`,
`ramp-capability`, `transfer-interface-limits`, `winter-fuel-inventory`
regenerated first and every log audited (clean). The neiso-65 table is corrected
in this commit.

**Consequence:** miso-92's replay *levels* ($31.224 → $30.770) were measured on
the degraded network and **should not be quoted**; its *delta* (−$0.454) agrees
with this session's 2023 delta (−$0.467) to within $0.02, so its conclusion
stands. The authoritative keeper baseline is its committed `hourly/` sidecar.

### Pre-registration honesty

The charter named C3a-2024 as the single exposure before solving and got the
gate, year, direction, and the C1/C2 hold right. It got the **magnitude wrong**
— estimated ≈−9.4 % and called it inside the band; it landed at −10.1 %,
outside. Recorded rather than narrated afterwards as predicted.

### Verification / ops

* Determination scored from the committed bundle; `audit_keepers.py --iso MISO`
  re-run after registration.
* Memory: miso-92's fix confirmed live on main — floor `resident` 1.04–1.09 GB,
  `in_use` 0.15 GB, peak 14.41–14.54 GB. The staged one-year-per-process
  `--reuse-solved` recipe remains required.
* Four solve-years total (2023, 2024, 2025 + one 2024 isolation probe). The
  probe bundle was **deleted**, per rule 16 — its numbers live in the finding.
* Rule 22 honoured: 2023–2025 only. No marker, freeze active.

### Notes for the next session

* **MISO needs a re-tune charter** scoped to C3a level under a ~1.4 pp
  structural price reduction, with the ledger at 3/3 — so it must close by
  structure, not a ledger slot, and the corrected extract stays in (rule 1).
* Code churn `3babe5f..HEAD` is measured MISO-inert; don't re-establish it.
* Next number: **miso-94.**
## 2026-07-26 — CAMPD charter LANE B (cross-ISO, **no MISO lane number claimed**): the day-grain `R < 0` cut does not replace the guard's window-grain cut

Charter/cross-ISO session — measurement only: no guard change, no extract
re-derive, no LP solve, **no MISO keeper touched**, no dashboard registration.
Full record: `results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md`;
cross-ISO entry in `docs/calibration-log/governance.md`.

MISO's cell of the 180-cell sweep (`--rcc-pctl {0.50, 0.75, 0.90, 0.99}` × `--horizon {24, 48, 72}` ×
2023–2025), scored against **the MISO native outage source (`MISO_Forced + MISO_Planned + MISO_Unplanned`)**:

* **KEPT-extract monthly `r` at the default p90 / h24**, window-grain → day-grain:
  2023 **+0.87 → +0.88** (Δ +0.002), 2024 **+0.80 → +0.81** (Δ +0.005), 2025
  **+0.95 → +0.95** (Δ +0.003). MISO is the candidate's best ISO and it is still
  a coin flip: better in **23/36** cells, median Δ **+0.001** — an order of
  magnitude inside the placebo band. Both cuts clear the placebo in the same
  24/36 cells.
* **The two cuts pick the same windows**: Jaccard 0.93 / 0.89 / 0.94; day-only
  vetoes 11 / 13 / 11 against window-only 7 / 15 / 6, out of ~1,450 windows a
  year.
* **Control passed**: the re-implemented incumbent reproduces MISO's committed
  kept/layup split on 1,445/1,451, 1,502/1,509, 1,448/1,454 windows.

**Nothing in MISO changes.** The merit-order guard stands as the charter §8
verdict adopted it, MISO's committed extract and layup companion are
untouched, and no rule-22 obligation arises because no mechanism change is
proposed. The 3/3 solve budget is untouched (no solve was run). Next number unchanged:
**miso-94**.

## 2026-07-26 — miso-94: LANE A has no structural door for C3a-2024; the guard-corrected extract stales its own downstream outage family

**Lane:** A of the miso-93 handoff (the MISO re-tune), executed through its own
first question. Charter, pre-registered before any solve (magnitude included):
`docs/handoffs/miso-94-outage-family-consistency-charter-2026-07.md`. Full
evidence: `results/calibration/FINDING-miso94-outage-family-consistency-2026-07.md`.

**Registered arm:** `2026-07-26-miso-94-outage-family` (MISO 2023/2024/2025, one
bundle, rule 16; rule 15 — registered whatever the verdict).

### Verdict

**`NOT-YET`.** C3a-2024 **−10.06 % → −10.05 %**, still past the ±10 % veto. C1
(free 12/12), C2, C4, C5a, C6, C7, C8 all PASS; C3b/C3c stay ledgered (C3b-2025
NRMSE 0.214). Ledger budget untouched at 3/3. **The keeper designation was NOT
changed** — miso-88 remains designated; promoting or demoting on a NOT-YET arm is
an owner call.

### The LANE A question, answered — the door does not open onto the offer curve

Rule 23 permits a frozen-derive re-derivation on a source-data change, and the
guard-corrected extract is one. Reading each derivation *before* solving:
**`gas_offer_margin_anchor`** (delivered-gas series only), the **miso-88 `phys_*`
eGRID-HR bands** (CEMS unit-hours with `grossLoad > 0`; outage hours self-exclude),
**`SUMMER_WEFOR_SHARE` / `SUMMER_CLASS_DERATE`** (no derivation exists at all),
**`reliability_floor_coeffs_MISO.csv`**, the CT run-length artifacts, the seam
ladders and the measured reserve requirements — **none consume the std extract**.
The only residual surface, `offer_curve_by_group`, is not a derive.

What *does* consume it: **`campd-unit-outages-short-MISO.csv`**,
**`campd-unit-outages-maxgen-MISO.csv`** and **`thermal_tranches_MISO.csv`** —
all three live in this keeper, and `6a8f285` re-derived none of them.

### What was corrected

* **short** — control PASSES (committed file byte-identical to a HEAD re-derive on
  the pre-guard blob). Guard delta −1 row (F B Culley 1012/2, 2023, 2.2 d, 103.7 MW).
* **maxgen** — guard delta **+18 rows / +1,338 MW / 23.1 GWh** (ST_GAS 1,002,
  CC_CHP 251, CC_REGULAR 85 — the classes the guard returned to merit). The
  re-derive also repairs a **pre-existing rule-19 `[R-ONE-MECH]` violation**: Weston
  4078/3 (369 MW), Sherburne County 6090/1 (729 MW) and F B Culley 1012/3 (287 MW)
  each carried a maxgen derate while a short-extract full stop already covered the
  same unit-hours — ~1,385 MW double-derated inside declared emergencies. The
  committed extract predates the short leg of guard 4 and does not reproduce at HEAD.

### Result and pre-registration honesty

Near-inert on level: **2023 +$0.0001, 2024 +$0.0025, 2025 −$0.0007** vs the miso-93
arm. The charter got the verdict right (it stated outright the arm does **not**
close C3a-2024) and bounded 2024 at |ΔP| ≤ $0.03, but got the **sign wrong** — it
predicted a decrease from the block's net −362 MW; the move is a small increase.
Cause, measured afterwards: the overlays compose **multiplicatively** per
`(plant_code, plant_group)`, so undoing a double-derate on a plant the short
overlay already holds near zero buys back little, while the +735 MW of new
ST_GAS/CC_CHP rows bite in full. The double-count was largely inert in *effect*
while remaining a real correctness violation — corrected on that ground, not on
the residual.

### LANE A's verdict

**No structural door of the required sign and size exists for C3a-2024, and none
was manufactured.** The gap is ~$0.02/MWh (0.06 pp) on a $32 mean; the only surface
that could move it is 72 residual-identified offer-curve scalars, which is not a
derive and has no data change to cite. **Per rule 24 `[R-DOF]`, C3a-2024 is an open
root-cause issue — reported, not tuned.**

### Notes for the next session

* **`thermal_tranches_MISO.csv` is the highest-value next lane** — the only stale
  artifact touching offer-curve *shape* (must-run / committed tranche sizes) rather
  than availability, hence the only remaining candidate with plausible C3a
  magnitude. **Provenance-blocked first:** it does not reproduce at HEAD on its own
  pre-guard input (`committed_pct` differs on 71 plants, max 53.3 pp;
  `nameplate_mw` on 6, max 1,028.6 MW). Establish the reproducing input vintage
  before any A/B — adopting it blind is a confounded arm (the caiso-123 defect).
* **Cross-ISO exposure, flagged not audited:** `6a8f285` adopted the guard for all
  six ISOs and re-derived no downstream artifact for any of them.
* Solve hygiene: all four clean partitions regenerated first; all three logs audited
  clean and every year logged "seasonal CIL/CEL interface caps on 5 zone group(s) …
  static summer fallbacks replaced" (miso-93 correction 1 respected).
* Rule 22 honoured: 2023–2025 only. No marker, freeze active.
* Next number: **miso-95.**

---

## miso-95 — LANE 1 STAGE 1: `thermal_tranches_MISO.csv` is provenance-orphaned, and so is every other ISO's

**Determination `PROVENANCE-BLOCKED`. No solve, no bundle, no registration.**
Keeper unchanged (`2026-07-25-miso-88-egrid-hr`). Evidence:
`results/calibration/FINDING-miso95-thermal-tranches-provenance-2026-07.md`.

The miso-94 handoff pre-registered the rule: if the control does not reproduce,
report and stop (rule 24 `[R-DOF]`). It does not reproduce, so STAGE 2 (the
single-delta A/B on the std outage extract) was **never entered** and no LP ran.

### The axis miso-94 never named, and it reproduces exactly

`derive_thermal_tranches.py` takes non-ERCOT nameplate from `load_fleet_from_csv`
with `apply_cc_summer_guard` at its default **True**. The committed artifacts were
derived with that guard **OFF**: re-deriving with it disabled makes `nameplate_mw`
match on **every row of all five ISOs** (MISO 6 exceptions → 0, PJM 5 → 0,
NYISO 3 → 0, CAISO 2 → 0, NEISO 2 → 0). The 18 exceptions are exactly the CC
plants `_reconcile_cc_pmax_to_nameplate` reconciles.

It is a live defect, not a curiosity: `committed_pct` / `mustrun_pct` / `p25_cf`
are ratios over that nameplate, and the model applies them to the **guarded**
(smaller) pmax — so the min-stable/must-run floor is understated twice, one-sided.
**~1,090 MW of understated CC committed floor across five ISOs, MISO carrying
~766 MW** (Union Power 55380 r = 1.42, Perryville 55620 r = 1.53, Hot Spring
55418 r = 1.34, Attala/Hinds r ≈ 1.47, Ouachita r = 1.39). Rule 11 `[R-ACCURATE]`
item: the accurate input is already in the model and the artifact still quotes the
pre-guard basis at it. A **code** change, so rule 23's data-change trigger never
fired — which is exactly why nothing re-derived.

### What does not reproduce, and why it cannot be recovered here

With the guard axis neutralized, MISO still drifts on `online_hours` (94 rows,
max 17,378 h), `committed_pct` (69, max 53.3 pp) and `p25_cf` (75, max 133.3).
Four arms (guard on/off × HEAD/pre-guard extract × per-unit/primary routing ×
derate-off) isolate three of four axes:

* the `6a8f285` merit-order guard — **measured, and immaterial**: 3 of 94 rows,
  372 of 17,378 hours. The lane's founding premise is true but an order of
  magnitude too small.
* the derate **was** applied (disabling it is strictly worse on every column) but
  was **routed differently** — routing each row to its plant's *primary* fleet
  group instead of the extract's own per-unit `plant_group` moves Brame 6190/COAL
  21,099 → 3,288 against a committed 3,721 and cuts the ISO tail to 3,614. Close,
  not exact.
* a small, two-signed, ubiquitous ±10–400 h residual on ~84 of 198 `ok` rows with
  no outage story and exact `nameplate_mw` — the signature of an upstream CAMPD
  hourly / `parasitic_load_factors.parquet` vintage move. **Not reconstructible**:
  shallow clone (304 commits), raw parquets now span 2018–2026, `git log` on
  `data/raw/campd-unit-level/` returns one merge commit.

Adopting the re-derive would move all of that in one blob — a five-way confounded
arm (the caiso-123 defect) offered against a 0.05 pp C3a-2024 miss.

### Cross-ISO (LANE 2, partially closed)

All five `thermal_tranches_<ISO>.csv` are stale on **both** axes. Schema tells the
generations before any number is compared: only CAISO's has `steam_level_cf`;
NYISO and NEISO also lack `mustrun_online_pct` and `online_frac`; CAISO's max
`online_hours` is 22,760 (a partial year window), which is why its drift is the
smallest. Standing check:
`scripts/probes/miso95_tranche_provenance_sweep.py` (no CAMPD read, seconds). `6a8f285` stripped rows from all six std extracts
(MISO −2,424, PJM −3,246, NYISO −3,037, NEISO −1,294, CAISO −810, ERCOT −3,484).
**`campd-unit-outages-short-PJM.csv` is stale and un-actioned** — a live consumer
(`unit_outage_short_windows`), a one-command re-derive, and its MISO twin's control
*passed* in miso-94, so a clean single-delta A/B is available on it today. Solve-side
exposure is already covered (pjm-129, miso-93/94) and should not be re-run.

### Hygiene

Every swap hash-verified both ways; `f2b3ec8` mounted once and restored to
`c298c68` = `HEAD:data/raw/campd-unit-outages-MISO.csv`. All arms wrote to `/tmp`;
**no file under `data/` was modified.** Rule 22 honoured — `--years 2023 2024 2025`
only, no marker, freeze active.

### Next

The unblock is an owner call, ranked in the finding §4: (1) re-baseline all five
tranche artifacts deliberately, one registered arm per ISO; (2) adopt the
CC-guard sub-axis alone — the only cleanly separable single delta today, known
sign (floors go **up**); (3) stamp a `campd_vintage` provenance header into every
derived artifact, which would have answered this session in one `head -1`.

Next number: **miso-96.**

## 2026-07-27 — miso-96: the C7 COAL_PRB failure is the miso-66 take-or-pay discount, PROVEN by A/B — but removing it overshoots; keeper UNCHANGED, CI still blocked on a verdict-text decision

**Lane:** Part 1 of the miso-96 handoff (unblock the repo-wide CI red).
**Keeper UNCHANGED — `2026-07-25-miso-88-egrid-hr`.** Registered arm:
`2026-07-27-miso-96-sunkfixed-takeorpay` (MISO 2023/2024/2025, ONE bundle,
rule 16), **determination NOT-YET, REJECTED — not promoted.** Full evidence:
`results/calibration/FINDING-miso96-coal-prb-offpeak-2026-07.md`.

### The handoff's hypothesis is refuted, and the real mechanism is dated

The handoff directed the search at "the floors/must-run/take-or-pay path" under
rule 17 `[R-FLOOR-WINDOW]`. **There is no floor.** The keeper's own D-2 attributes
0.20–0.36 % of MISO coal energy to any mechanism (`reliability_floor` alone, sole
entry, all three years). The overnight hold is *economic*.

`cv_ratio` across every MISO bundle carrying a D-1 artifact has a clean
discontinuity at **miso-66**: `miso65_outage_regen` 0.880/1.036/0.470 →
`miso66_coalconduct` 0.462/0.465/0.347, and every later bundle sits at ~0.45.
The miso-65→66 config diff is one delta — `coal_committed_takeorpay_regulated`
armed, which per its own design doc moves **RE PRB committed 9,403 MW from
$28.09 → $5.07/MWh**.

The defect is dimensional: a take-or-pay contract is an **accounting-period
tonnage obligation** — sunk in aggregate, hence a **fixed** cost — but it is
implemented as an unconditional **per-hour marginal** price discount. A plant
that over-fulfils its contract buys its marginal ton at spot, so the contract
should not lower its offer at all. Corroborating: model load-weighted night
(HE0-3) price runs **+$7.77 / +$6.49 / +$6.89** above actual RT (body-censored)
in 2023/2024/2025 — year-stable, not summer-specific — and `COAL_PRB` is the
**only** fossil class the model over-produces overnight while under-producing
every other one.

### The A/B proves the attribution and refutes its own remedy

New default-off gate `coal_committed_takeorpay_sunk_fixed` (removes the
committed-band discount; `_mustrun` keeps the contract, rule 19 `[R-ONE-MECH]`).
Single delta on the miso-93 HEAD-envelope control; hydro and wind byte-identical,
so the blast radius is the coal/gas merit order alone.

| C7 D-1 `COAL_PRB` | control | arm |
|---|---|---|
| 2023 | 0.453 FAIL | **0.792 PASS** |
| 2024 | 0.441 FAIL | **0.985 PASS** |
| 2025 | 0.364 FAIL | 0.438 FAIL |

Prices improve too (C3a-2025 −16.6 → −15.9 %, C3b-2025 NRMSE 0.208 → 0.203, DA
diagnostics 2023 −7.2 → −3.5 %, 2024 −11.0 → −5.3 %). **But C1 fuel-mix FAILS**
(COAL_BIT −18.26/−19.11 TWh, COAL_PRB −8.34/−13.22 TWh) **and C5a CO2 FAILS**
(−10.0 %/−11.1 %). Three fails against the keeper's one — strictly worse, so the
arm is rejected.

**Why, and it is informative:** the discount is doing two jobs. (1) keeping the
unit *committed* — measured and real (SOM Table 7: regulated utilities
self-commit 53–56 % of coal starts); (2) making the whole committed band
*price-insensitive in every hour* — the category error. Deleting the discount
deletes both, so 18–19 TWh of BIT coal is displaced wholesale.

### The lane this identifies (NOT built)

Separate the two jobs with a **minimum-take constraint** over the contract's
accounting period: the unit must take the tonnage (stays committed) but chooses
*when* (still de-loads overnight), and the obligation is priced by the
constraint's **dual** — non-zero only in the hours it binds, which is exactly the
window rule 17 demands, with zero fitted parameters. Two hard constraints make it
multi-session: it is an LP **constraint block** (rule 2 `[R-VECTOR]`), and the
tonnage **must not** come from the same year's measured receipts — that would pin
annual coal to ≈85 % of actual, which rule 13 `[R-MEASURED]` forbids.

### 2025, and what is NOT licensed

2025 still fails at 0.438 (model off-peak CV 0.033 vs measured 0.075): the fleet
barely cycles even with the subsidy gone, in the one year the standing evidence
says the system is ~10 GW tighter at summer peak than the model can see
(FINDING-miso89 §2). That is the already-adjudicated, **data-blocked**
outage-grain gap, not a new phenomenon. NOT re-attacked with a second mechanism
(rule 19); NOT ledgered — C7 is protective and hard, and the ledgered budget is
3/3 saturated regardless.

`coal_committed_takeorpay_sunk_fixed` stays **default-off, probe-refuted-alone**,
on the same footing as the other adjudicated default-off probes in CLAUDE.md. It
is not a fitted knob (it sizes nothing), so rule 26 `[R-DELETE]` does not require
removal, and it is the control arm the minimum-take lane will need.

### CI status — STILL RED, and it is an owner decision

The E5 failure is unchanged: the miso-88 sidecar asserts CALIBRATED-WITH-CAVEATS
while the live verdict is NOT-YET (rubric v2.8 made a real, previously-invisible
COAL_PRB failure visible — rule 14 `[R-ACCURATE]`; the scorer got sharper, the
keeper did not get worse). This session did not manufacture a pass, and the
honest live value is NOT-YET. Restating the keeper's determination is a
governance statement in an owner-decision lane, so the shards were **not**
committed and the sidecar was **not** edited. S1 (all seven status shards stale)
clears with one `build_status.py` run the moment that decision is taken.

Cross-ISO note, reported not actioned: the same rubric v2.8 widening flips
**ERCOT** C7 shape PASS → FAIL (COAL_LIGNITE 2023, r 0.745, cv_ratio 0.294 — the
Oak Grove ceiling pin), dropping its grade 6 → 5 target-grade. ERCOT's keeper
text already says NOT-YET so CI does not fail on it.

* Rule 22 honoured: 2023–2025 only, no marker, freeze active.
* Solve hygiene: all four clean partitions regenerated first; staged
  one-year-per-process `--reuse-solved` chain (14.34 GB single-year peak on a
  15 GB box); `system_2023`/`system_2024` verified byte-identical across the
  chain; logs audited — seasonal CIL/CEL caps loaded on 5 zone groups every year
  (miso-93 correction 1 respected).
* Next number: **miso-97.**

---

## 2026-07-28 — miso-98: the miso-97 CHP sector correction is SOLVED and the arm is **PROMOTED** — the accurate input improves the run (C3b CAVEAT→PASS, ledger 3/3→2/3), the pre-registered CC_CHP degradation happened, and the pre-registered CT_CHP prediction is REFUTED

**Lane:** the miso-97 TASK 4 A/B, pre-registered in FINDING-miso97 §5.1 and left
unrun. **Keeper → `2026-07-27-miso-98b-sectormeasured`** (bundle
`results/calibration/miso98_chp_sector_B`), superseding
`2026-07-25-miso-88-egrid-hr`. Evidence:
`results/calibration/FINDING-miso98-chp-sector-ab-2026-07.md`.

Six year-solves, two registered arms, single delta: the `chp_sector` column of
`thermal_tranches_MISO.csv`, absent (A, `2026-07-27-miso-98a-sectorabsent-control`)
vs the measured EIA-860 sector on 104 rows (B). Both same-HEAD replays of the
miso-88 recipe rebuilt from its `meta.json` — **208 kwargs, zero unmapped**;
`run_config.json`'s `calibration_flags` is a curated ~35-key subset and would
have mis-specified the arm.

### The promotion

| criterion | outgoing miso-88 | **incoming miso-98b** |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C3a mean LMP | CAVEAT | CAVEAT (−2.5 / −7.8 / −15.4 %, better every year) |
| **C3b price shape** | **CAVEAT** (ledgered) | **PASS** (0.077 / 0.121 / 0.198) |
| C3c price tail | CAVEAT | CAVEAT |
| C6 governance | PASS | PASS |
| C7 diurnal shape | FAIL | FAIL |
| determination | NOT-YET | NOT-YET |

**Strict dominance: one ledgered caveat removed, nothing regressed.** The
ledgered-caveat budget goes **3/3 → 2/3** — the C3b-2025 entry is *deleted*, not
re-scoped (rule 26 `[R-DELETE]`), because the criterion now passes on its own
gate. It passes **marginally** (0.198 against ≤0.20) and that is stated, not
smoothed. NOT-YET is unchanged and is decided by C7 COAL_PRB shape — the
miso-96 issue, unrelated to this delta.

Promotion rests on rule 1 `[R-STRUCT]`: an unsourced `merchant = 35.0` default
(the one entry `constants.py` marks *"residual-identified, forecast-risk"*)
replaced by a measured EIA attribute, validated 232/232 against the four peer
ISOs at **exactly 0.0 MW** peer movement. Zero free parameters added, one
removed — a rule-24 `[R-DOF]` **shrink**.

### It is also a correctness fix

Registering the measured arm re-bases the committed MISO benchmark for every
registered MISO run. The outgoing keeper solved on the 35.0 % default, so it was
being scored against a benchmark its own dispatch never used — its C1 CC_CHP
miss inflating to **+7.77 TWh, 97 % of the ±8 TWh gate**, with no change to its
dispatch at all. The promotion puts model and meter back on one BTM basis.

### Pre-registration: one half honoured, one half refuted

* **CC_CHP fits WORSE — predicted** (+4.9 → +11.8 %, 2023). Under rules 1 / 14
  the accurate input stays and the worse fit is the discovered-bug signal. The
  miss stays well inside C1 (+2.52 TWh of an 8 TWh gate). Named root cause: the
  steam-credited eGRID heat rate (§ below).
* **CT_CHP prediction REFUTED** (−21.8 → −33.3 %, 2023). miso-97 §2.1's
  `ρ ≥ f` "structural bound" — and its §6 DO-NOT-REDO line forbidding the
  argument — assumed capacity and the benchmark subtrahend rescale by the *same*
  `(1 − s)`. They do not: `s` applies to **nameplate** on the capacity side
  (ratio 0.531) and to **net generation** on the benchmark side (0.615), and
  MISO's high-BTM CT_CHP plants run at lower capacity factor. Model loses 47.6 %
  of the class, meter loses 38.5 %.
* **ST_CHP** reported, never gated: −4.72 → −3.05 TWh, off the no-sector 90.0
  fallback onto its measured 63.6, inside the peer band.
* **Peers: zero by construction** — the delta is one column of a MISO-only file.

### Two contamination traps, both caught, both DO-NOT-REDO

1. **Four post-solve steps recompute the benchmark from the artifact on disk**
   (`pjm119_merge_year_chain`'s `btm.parquet`, `--rebuild-benchmark`,
   `legitimacy_diagnostics`, `dashboard_add_run`). Arm A post-processed under
   arm B's artifact reported CC_CHP *improving* +38.1 → +11.8 % — the opposite
   of the truth. Post-processing must be staged per arm.
2. **`bench/<ISO>/<year>.json.gz` is shared per ISO-year, not per run.** When a
   delta moves the benchmark the last-registered arm owns it; arm A first scored
   C1 FAIL (+8.11 TWh) purely from that. Arm A's sidecar warns that its rendered
   scorecard carries the keeper's bench.

### TASK 3 (CHP heat rate) — built as a measurement, deliberately NOT armed

`scripts/data/derive_campd_chp_heat_rates.py` implements the caiso-128 §6 design
ISO-generically. Measured for MISO: CC_CHP **83.2 %** MW-covered, model 6.72 vs
measured **9.69** (−30.7 %); CT_CHP 10.4 %; ST_CHP 21.9 % and accurate to
−2.0 %. It confirms caiso-128 §4 — 16 of 19 rows understate, **3 overstate, one
by +68 %** — so the 1.8× topping factor stays unarmed.

**Blocking defect, which is why no `ScenarioConfig` gate is wired:** §6(a)'s
"plant's own same-year measured gross→net ratio" fires on **0 of 19 rows**.
`compute_parasitic_factors` sends every cogen to `class_default` because
EIA-923 net includes host generation CEMS never meters, so 94 % of covered MW
divides by a **2.5 % class constant** against MISO's measured CHP station
service of 8.0 / 23.7 / 30.8 %. The artifact is on a near-**gross** basis;
arming it would be a guess substituted for misaligned real data (rule 14) and an
unsourced constant on the critical path (rule 21). Two charter figures corrected
under the design's own gates: CT_CHP coverage is **10.4 %, not 38 %**; ST_CHP is
**21.9 %, not 0 %**.

* **`--reuse-solved` OOM'd at 15.9 GB** on the three-year assembly stage (the
  2025 LP itself finished, `Solve: 644.063s`); `_load_prior_bundle_tables` holds
  the reused years alongside the fresh one. Use one process per year into one
  bundle dir + `pjm119_merge_year_chain.py`.
* Solve hygiene: four clean partitions regenerated first; every log carries
  `seasonal CIL/CEL interface caps on 5 zone group(s) … static summer fallbacks
  replaced`; chain byte-identity verified; A-arm control reproduces the keeper
  on the classes under test (CC_CHP +1.2 %, CT_CHP −0.6 %), with ST_GAS /
  CT_PEAKER showing the documented post-CAMPD-envelope drift (miso-93 §3).
* Rule 22 `[R-HOLDOUT]` honoured: 2023–2025 only, all three years FRESH in one
  bundle (rule 16 `[R-ALLYEARS]`), no marker, freeze active.
* Next number: **miso-99.**

## 2026-07-28 — miso-99: the CHP heat-rate correction UNBLOCKED and PROMOTED — eGRID publishes the steam credit it removes (`CHPCHTI`), so the gross→net basis miso-98 §6.1 could not obtain is not needed

**Keeper → `2026-07-28-miso-99b-chp-power`** (bundle
`results/calibration/miso99_chp_hr_B`), superseding
`2026-07-27-miso-98b-sectormeasured`. Determination **NOT-YET**, the same
determination and the same criterion profile as the keeper it replaces, decided
by the same C7 COAL_PRB diurnal-shape issue (miso-96) that this delta does not
touch. Full evidence:
`results/calibration/FINDING-miso99-chp-heat-rate-2026-07-28.md`.

**The blocker, and why the answer was to delete the gross basis rather than
estimate it.** caiso-128 §6(a) made the plant's own measured gross→net ratio
non-optional; FINDING-miso98 §6.1 measured it firing on **0 of 19** MISO rows.
Root cause measured here: at a cogen CAMPD's `grossLoad` channel and EIA-923's
net generation cover **different unit sets**, in both directions and by large
margins — Midland CEMS gross 7.89 TWh vs EIA-923 net 9.76 TWh (CEMS misses the
steam turbines), Portside 0.070 vs 0.232, Primient 0.674 vs 0.389. caiso-128's
`g2n` survived only via `clip(1.0, 1.35)`, a hand bound doing the work exactly
where the raw ratio is meaningless. It is therefore **not obtainable**, and it
is also **not the quantity needed**: eGRID's `PLNGENAN` is already the model's
NET denominator and is identical to the EIA-923 combustion net the benchmark
holds out against.

**The measurement.** The eGRID plant sheet carries `PLHTIAN` (heat input
allocated to electricity — the numerator of the rate the model loads) **and
`CHPCHTI`** (heat input allocated to useful thermal output — the credit
itself). So the power-only rate is `(PLHTIAN + CHPCHTI) / PLNGENAN`: the
incumbent input with eGRID's own allocation undone, same source, same vintage,
same denominator, one change, **no gross basis anywhere**. Validated against
independently metered CAMPD heat input at a median ratio **1.00000 on 22 of 25**
CEMS-covered MISO CHP plants (`PLHTIAN` alone: 1.473, 2/25); Midland matches to
3 MMBtu in 86 million. No host double-count: `chp_btm_pct` holds the host out as
a *volume*, this is an *intensity*.

**Scope on turbine physics.** `CC_CHP`/`CT_CHP` only — the add-back charges all
fuel to power, right for a topping cycle and wrong for a boiler-first
back-pressure cogen (MISO `ST_CHP` add-backs reach 435 MMBtu/MWh). Gates are
definitional and frozen: prime mover; unfired-topping thermal share ≤ 0.50 (the
EPA CHP Partnership gas-turbine envelope over eGRID's `T/0.8` displaced-boiler
credit); the repo's existing committed physical bands; a basis check.
**Zero fitted parameters.** The legacy 1.8× hand topping factor is *skipped*
where the measurement covers, never stacked (rule 19);
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` unchanged, MISO NOT added.
MISO: 25 (plant, class) rows applied — CC_CHP **81.8 %** of class MW
(6.70 → 9.16), CT_CHP **37.2 %** (6.39 → 9.43); 72 generators / 6,732 MW.

**The A/B.** Every criterion verdict is identical between the arms and **C3a
improves in all three years** (−6.4/−10.2/−15.4 % → −5.4/−9.1/−14.3 %) with
**no criterion regressing**. The pre-registered kill guard **held**: C3b stays
PASS (0.198 against ≤0.20 — it could have flipped back). C3c is **bit-identical**
(1/6/0 model hours vs 30/37/88) — a CHP cost change does not reach the scarcity
tail, stated as such rather than claimed as improvement.

**The control is an EQUALITY check**, not merely structural agreement: arm A
reproduces the outgoing keeper at **0.0000 % on all 17 classes in all three
years**. All nine `shared_inputs` hashes *and* the benchmark (identical on all
21 class-year rows) match across the arms, so the miso-98 §5 shared-`bench/`
trap is defused by measurement rather than assumption.

**Pre-registered and honoured**, committed before any arm was readable
(FINDING §3) and **correcting the charter's own coverage figure** — CT_CHP is
37.2 % MW-covered, not the 10.4 % the CEMS route implied, so the predicted
CT_CHP degradation is larger than the charter implied. CC_CHP's C1 |err|
improves in all three years (+11.8 → −9.8 %, +11.1 → −10.1 %, +31.7 → −4.9 %);
CT_CHP degrades in 2023/2024 (−33.3 → −38.4 %, −32.9 → −37.8 %) and improves in
2025 (+15.7 → +6.2 %).

**Three adverse movements, kept in and reported (rules 1 / 14):** (a) CT_CHP's
C1 fit degrades as predicted; (b) CC_CHP's diurnal **amplitude** overshoots —
D-1 `cv` 0.026 → 0.141 against an actual 0.066 (`cv_ratio` 0.392 → 2.132) —
although its profile **correlation** improves (0.959 → 0.989 / 0.980 → 0.986 /
0.860 → 0.965); (c) CT_CHP's profile correlation degrades (0.768 → 0.652,
0.084 → −0.104, 0.627 → 0.171). Neither CHP class is D-1-gated, so no gate
moves; all three are named open items, not ledgered caveats. The ledger is
inherited **unchanged at 2/3**.

**COAL_PRB's D-1 FAIL and MISO ST_CHP's −0.79 profile anti-correlation are
UNCHANGED by this delta**, confirming both are orthogonal to CHP heat rates —
the ST_CHP shape lane should not expect this mechanism to have moved its signal.

**A shared-infrastructure blocker fixed on the way.** Registering on post-fix
main crashed in `render_calibration_html.build_payload` with `IndexError: index
11 is out of bounds for axis 0 with size 11`:
`bench_multiclass.map_e923_to_model_classes` (PR #3062) fell back to a
12-vector for a plant with no EIA-923 rows while the render path builds
13-vectors and slices `[1:]`. Fixed with an explicit `empty_len` (default 12, so
every existing caller is byte-unchanged) plus three regression tests. **Not
specific to this run — it would block registration for any ISO carrying such a
plant.**

**Pre-existing red gate, reported not fixed:** `audit_keepers.py --check` shows
S1 stale status parts for PJM/CAISO/NYISO/NEISO. Verified pre-existing by
re-running with this session's changes stashed (the same failure then lists
five ISOs including MISO); this promotion removes MISO from the list. Cause is
main-side — the bench multi-class fix moved every ISO's verdicts and only
MISO's part has been rebuilt. `keepers/README.md` forbids editing another ISO's
lane.

**Solve hygiene.** Four clean partitions regenerated first; every solve log
carries the healthy `seasonal CIL/CEL interface caps on 5 zone group(s) …
static summer fallbacks replaced` tell. `--reuse-solved` NOT used (miso-98 §8
OOM) — one process per year into one bundle, reassembled with
`pjm119_merge_year_chain.py`. Rule 22 honoured: 2023–2025 only, freeze active,
no marker. Rule 16: all three years fresh in one bundle per arm.

Next number: **miso-100.**

## 2026-07-28 — miso-100: the ST_CHP diurnal anti-correlation is CHARACTERIZED to a representation choice (no solve) — the measured wave is ambient temperature (r ≈ −0.96, amplitude predicted by the committed 0.0054/°C slope), the model is flat on every channel that matters, and the class statistic is one refinery vs one anti-phase merchant hump

**Lane:** the bench-collapse FINDING §6.1 follow-up (owner-scoped
characterization; rule 1 structural fidelity — ST_CHP is D-1-ungated and
D-2-exempt, no gate at risk). **No LP, no lever tested, no matrix cell
change. Keeper `2026-07-27-miso-98b-sectormeasured` UNCHANGED by this
session.** *(The miso-99 promotion merged concurrently; the finding carries
over to the new keeper unchanged — `miso99_chp_hr_B`'s own diagnostics read
ST_CHP `profile_r` −0.797/−0.762/−0.771, ST_CHP being out of the miso-99
delta's scope by design.)* Evidence:
`results/calibration/FINDING-miso100-stchp-diurnal-2026-07.md`.

* **The D-1 ST_CHP row is a one-refinery test**: 3 of 9 benched plants carry
  CEMS hourly; the paired actual (0.85–0.93 TWh, ~a fifth of the class's
  5.2/5.5/3.9 TWh EIA-923 actual) is 91–99 % ExxonMobil Beaumont Refinery.
* **The actual's shape is temperature, not host-following**: peak h05–08,
  trough h14–16, amp 3–6.6 %, winter and summer; corr vs a TMIN→TMAX
  diurnal proxy −0.91..−0.99 every year/season; the committed
  `temp_derate_slope_st_gas` 0.0054/°C × the ~11 °C diurnal range predicts
  the amplitude. The winter wave means no hard 15 °C onset.
* **The model is flat by construction** (flat `MECH_CHP_STEAM` floor — the
  ONLY floor on ST_CHP unit-hours, {2: 192,720} census — clipped to
  hour-flat availability; flat report BTM add-back; Beaumont 100 %
  floor-pinned, byte-flat payload), and its entire class hour-of-day signal
  is R S Nelson's 2.5–10 GWh/yr afternoon price-following dispatch —
  anti-phase with the temperature trough, corr −0.795/−0.751/−0.740 by
  itself. `temp_dependent_derate` (MISO cell `U`, OFF here) could not help:
  `iso_zone_tmax` broadcasts daily TMAX **flat within-day** — hour-of-day
  capability resolution does not exist anywhere in the availability chain.
* **Proposed, NOT built** (owner decides on an arm): hour-grain diurnal
  temperature capability for the steam classes — interpolate the curated
  daily TMIN/TMAX into an hourly dry-bulb input for the existing
  temperature-derate ST leg; MISO-derived slope AND onset (pjm-95 refuted
  the committed slopes on PJM's own fleet; rule 25). No new floor (the
  steam-floor clip propagates the shape; rule 19). Pre-stated honestly: the
  scored `profile_r` may stay negative in 2024–25 because Nelson's
  anti-phase hump and the flat add-back are separate channels — not grounds
  to widen the lever (rule 1). Nelson slice conduct / `1393`
  fleet-classification is a separable owner decision.
* Next number: **miso-101.**

## 2026-07-28 — miso-101: the hour-grain diurnal temperature input is BUILT and MISO's OWN slope/onset DERIVED — Beaumont's floored cogen slice goes byte-flat → r +0.96…+0.98 against its own meter, every pre-registered gate passes, and the committed 15 °C hinge is measured FALSE on MISO's fleet

**Lane:** the arm lane FINDING-miso100 §7 proposed and the owner
pre-authorized. **Keeper RECOMMENDED, not performed:
`2026-07-28-miso-101b-tempgrain`.** The shard was deliberately not edited —
a `replay_keeper` bundle carries no `calibration_attestation.json`, so
promoting it would break rule 21 `[R-DOF]` and would silently drop MISO from
`CALIBRATED-WITH-CAVEATS` to `NOT-YET` on a missing governance file rather
than on model quality (the current determination rests on the miso-90 owner
re-gate, caveat budget 3/3). Carrying the attestation forward is the owner's
act; the arm itself adds **zero free parameters**.
Runs: `2026-07-28-miso-101a-control` (control) +
`2026-07-28-miso-101b-tempgrain` (arm), both 2023–2025 in one bundle
(rule 16). Pre-registration committed BEFORE either solve (`4a4cfcf`);
evidence: `results/calibration/FINDING-miso101-stchp-temp-grain-2026-07-28.md`.
Matrix `temp_dependent_derate` MISO **`U` → `K`** (duty (b)).

* **The grain did not exist and now does.** `iso_zone_tmax` broadcasts daily
  TMAX flat within the day, so the derate curve carried zero hour-of-day
  signal even when armed. `iso_zone_hourly_drybulb` reconstructs the within-day
  wave from the same curated daily TMIN/TMAX (two-piece cosine bridge, Parton &
  Logan 1981; anchors validated at lag 0 on MISO conduct). **No new floor, no
  new mechanism** (rule 19): `MECH_CHP_STEAM` already clips to
  `pmax × availability`, so the shape propagates to floored cogens by itself.
* **MISO's own identification refutes BOTH committed parameters.** Within-day
  plant-day fixed-effects regression, 6 CEMS-identifiable MISO cogens 2023–25:
  cap-weighted p50 **0.00141/°C**, ~5× below the literature CC slope
  (0.0076/°C) — MISO's own confirmation of pjm-95 (rule 25). Onset scan finds
  **no 15 °C hinge**: 0.0036/0.0030 per °C in the 5–10/10–15 °C bins
  (r −0.38/−0.28), where `max(0, T − 15)` is identically flat. LOO-stable
  (0.00130/0.00140/0.00153 vs 0.00141). Hence the mean-anchored form —
  level-neutral by construction, claiming only the shape the estimator
  identifies.
* **The metered machine is a gas turbine, not a boiler.** Beaumont is 3 ×
  combined cycle; the only other substantial CEMS cogen meter is a 26 MW CT;
  R S Nelson's CEMS unit is a *coal* boiler and is dropped. miso-100's
  condenser framing was right about temperature, wrong about the slope family —
  and GT physics is precisely why the winter wave survives with no onset.
* **Result — all four pre-registered gates PASS, 3/3 years.** Beaumont's ST_CHP
  slice: byte-flat (amp 0.000000 MW) → trough **h15** = the meter's own trough,
  corr **+0.964 / +0.958 / +0.984**. G2 level neutrality max 0.396 % (bound
  1.0 %); G3 scope containment max 0.068 % (bound 0.1 %). Control reproduces
  the committed keeper `miso99_chp_hr_B` to **0.00000 %** on every class —
  a true single-delta A/B, and proof the five new fields are inert when off.
* **Reported, not gated.** D-1 `profile_r` improves every year: ST_CHP
  −0.797/−0.762/−0.771 → −0.587/−0.647/−0.680 (stays negative exactly as
  pre-registered — Nelson's anti-phase hump and the flat BTM add-back are
  channels the lever does not own, and it was NOT widened); CT_CHP
  +0.652/−0.104/+0.171 → +0.684/−0.033/+0.298. C-series rubric **identical**
  between arms. System mean price +0.003 %.
* **One pre-registered prediction was WRONG.** P6 said the model's within-day
  CV would rise; it **fell** (ST_CHP `cv_ratio` 0.386/1.345/1.019 →
  0.253/1.041/0.664). Cause, unanticipated: the arm's wave is anti-correlated
  with Nelson's merchant afternoon hump, so the class composite partially
  **cancels** — the same cancellation that moves `profile_r` the right way.
  Recorded as wrong; neither class is gated.
* **Scope stated before solving and held:** ST_CHP + CT_CHP only (the two
  tranches the CEMS meter spans; they breathe together at 1.56–1.62 % /
  1.62–1.67 %). ST_GAS/COAL/CC/CT_PEAKER untouched — no MISO identification,
  and pjm-95 makes the literature slopes non-transferable.
* Next number: **miso-102.**

## 2026-07-28 — miso-102: C7 COAL_PRB is OWNED by the regulated committed-band take-or-pay discount (A/B: 2/3 years FAIL→PASS), the arm is REJECTED as structurally incomplete, and my own pre-registered mechanism test P5 is FALSIFIED IN DIRECTION — removing the discount fixes the dispatch wave while making the PRICE wave WORSE

**Keeper UNCHANGED: `2026-07-28-miso-101b-tempgrain`.** Runs
`2026-07-28-miso-102a-control` (`miso102_control_A`) +
`2026-07-29-miso-102b-sunkfixed` (`miso102_sunkfixed_B`), both 2023–2025 in one
bundle (rule 16). Pre-registration committed BEFORE either solve (`5200d16`);
evidence `results/calibration/FINDING-miso102-coalprb-c7-shape-2026-07-28.md`;
reproduction `scripts/probes/miso102_c7_coalprb_diagnosis.py`.
Matrix `coal_takeorpay_committed` MISO cell updated (duty b).

* **Five alternatives refuted from committed artifacts, no solve.** NOT a floor
  (D-2: MISO coal carries exactly one mechanism, `reliability_floor`, at
  0.31/0.35/0.19 % of class energy); NOT a mix effect (D-1 pairs the same keys,
  **0 dropped**, 31/31/30); NOT the benchmark basis; **NOT the miso-101 §5
  cancellation** (off-peak coherence `std(Σ)/Σstd` 0.984/0.981/0.939 model vs
  0.971/0.972/0.922 actual — both in phase, and phase coherence *matches*:
  0.68/0.62/0.55 vs 0.67/0.62/0.53, only amplitude misses); and **SEPARABLE from
  miso-89** — seasonal `cv_ratio` is worst in **winter/shoulder** (0.416/0.457/
  0.488, 0.453/0.411/0.526, 0.374/**0.274**/0.384) in the h0–h14 window, where
  miso-89's instrument is a summer HE16–18 under-derate.
* **Which units.** 100 % of the byte-flat PRB plants are **regulated**, all three
  years (9/8/10 plants, 46/44/50 % of class energy). Pooled 2023–25, all coal
  ranks: ACTUAL within-day CV **regulated 0.197 vs merchant 0.134**; MODEL
  **0.073 vs 0.351** — the model **inverts the measured flexibility ordering by
  4.8×**, and within COAL_PRB the two groups are measured indistinguishable
  (0.262 vs 0.231). The discount's scoping premise has no support in MISO conduct.
* **The A/B proves the attribution.** `cv_ratio` **0.467→0.727** (2023),
  **0.476→0.931** (2024) — both FAIL→PASS; 2025 **0.318→0.364**, still FAIL.
  Coal volume −18.47/−27.22/−7.68 TWh.
* **REJECTED, and pre-registered as a non-keeper before the solve.** C1 goes
  PASS→FAIL (16/16 · free 12/12 → 11/16 · free 7/12); `grade_summary` fails 3→4.
  The rejection is **structural, not gate-driven**: removing the discount deletes
  the category error (an annual tonnage obligation priced as an hourly marginal
  subsidy — rule 17, a discount with no window) **and** a real behaviour
  (regulated self-commitment, SOM Table 7). Rule 1 forbids promoting a mechanism
  that deletes real behaviour exactly as it forbids rejecting a correct one on
  gates. Corroborating tell: COAL_BIT **overshoots** to 2.6–2.8× measured
  off-peak variability — the arm overcorrects rather than restoring conduct.
* **P5 FALSIFIED, IN DIRECTION — the most useful result here.** I pre-registered
  that the arm must WIDEN the off-peak price wave. It **narrows** it every year
  (ratio 0.460→0.377, 0.530→0.418, 0.331→0.311) and pushes the night price
  further from the meter ($27.81→29.96 vs actual $19.42, etc.). The dispatch/price
  amplitude co-movement is a **joint consequence of the discount**, not
  price→dispatch causation. **Consequence: price formation (queue item 3, DA
  virtual depth) is NOT the route to C7**, and the C7 fix makes the price wave
  worse — they are separate misses and must not be pursued as one.
* **Scorecard: 5 hit, 1 missed, 1 falsified, 1 unscoreable.** P1/P2/P6/P7/P8 hit
  (P8: the control reproduces the keeper to **0.00000000 %** on every class in
  every year, mean price bit-identical — a true single delta). P3 **missed on
  magnitude** (2023 −18.47 TWh below the predicted 20–30 band; the miso-101b
  keeper is materially less discount-sensitive than miso-96's miso-88 base).
  P4 **unscoreable** — C5a is not in rubric v2.9's MISO criterion set, and my
  direct CO2 recompute failed on a join dtype, so no number is reported.
* **Lane space after this session.** CLOSED: floor / mix / basis / cancellation /
  miso-89; offer-steepening (coal is already 0.9–2.8× the real fleet's
  price-responsiveness); price formation as the C7 route; blunt removal. STILL
  OPEN: the **minimum-take LP constraint**, whose blocker was **verified not
  assumed** — EIA-923 publishes deliveries, not contract terms, so a same-year
  receipts tonnage would pin annual coal energy to actuals (rule 13). A
  lagged/multi-year-mean tonnage is the only forward-regenerable candidate and
  needs its own charter plus a pin-strength test.
* 2025's residual (0.364, model off-peak CV 0.027 vs measured 0.074) is the
  already-adjudicated data-blocked outage-grain gap (FINDING-miso89 §7), not a
  new phenomenon, and is not re-attacked with a second mechanism.
* Next number: **miso-103.**

## 2026-07-29 — miso-103: the coal minimum-take lane is DATA-BLOCKED — the only forward-regenerable tonnage (lagged/trailing-mean receipts) FAILS the chartered pin-strength test; NO LP built, keeper UNCHANGED, C7 stands with no open admissible lever

**Keeper UNCHANGED: `2026-07-28-miso-101b-tempgrain`.** No run produced, no
bundle, no dashboard registration (nothing to register — ERCOT-127/-130
ex-ante-refusal precedent). Finding:
`results/calibration/FINDING-miso103-coal-mintake-tonnage-2026-07-29.md`.
Reproduction: `scripts/probes/miso103_mintake_pin_strength.py` (~2 min,
committed artifacts only).

* **Charter executed as written** (MISO lever queue item 1, the only C7 route
  miso-102 left open): Stage 1 tonnage admissibility FIRST, no LP. It fails,
  so Stage 2 (the LP constraint block) was never built and no substitute
  mechanism was reached for.
* **(a) Data on disk:** Schedule-5 receipts at monthly plant grain 2018–2025
  (`eia923_monthly_fuel_costs.parquet`) for **39/49** take-or-pay plants — the
  cost-reporting subset, which is exactly the regulated target set (merchant
  fuel costs withheld upstream). Raw `f923_*.zip` absent by design.
  Tons-weighted `contract_share` 0.969 (1.00 at 34/49 plants), so MinTake ≈
  the trailing-mean receipts themselves.
* **(b) Pin-strength: FAIL on every measure and window.** Log-space
  cross-section R² of year-Y burn on the trailing mean **0.87–0.94**, with
  lag-1 / lag-3 / lag-5 equivalent — the lag adds no independence (contract
  persistence IS the autocorrelation). Floor = **0.964 / 1.136 / 0.978×**
  same-year actual tonnage (aggregate), dictating **90.3 / 95.9 / 90.9 %** of
  the target plants' actual CAMPD coal energy. It **binds** vs the
  discount-free miso-102 arm B (22/33/20 of 38 plants; **32/44/20 TWh**
  forced above unconstrained economics) — the constraint, not economics,
  would write annual coal energy ≈ actuals. Rule 13 pin, worse than the
  same-year case miso-96 §7 forbade (~85 %).
* **2024 overshoots outright:** floor 1.136× actual burn (≥100 % at 77 % of
  plants) — a hard ≥ floor forces MORE coal than reality burned; softening it
  needs a fitted penalty price (rule 24).
* **Delta test R² 0.172:** the trailing mean transmits the *level* of the
  measured outcome without the year-specific driver signal — the exact
  inversion of rule 13's admissibility test. **(c)** fails too: a forecast
  year has no measured trailing receipts, so the forward generator would be
  model-simulated prior burn — a different quantity, hence not "the same
  quantity produced for a forward year."
* **DO NOT REDO:** any receipts-derived tonnage variant (window, lag,
  smoothing, scalar shrink) — same answer key or residual-fitted knob.
  **Unblock:** genuinely contractual ex-ante data (FERC Form 580 contract
  minimums, fuel-adjustment-clause filings, IRP fuel-budget exhibits) — a
  data-intake ask, now the second standing MISO ask beside outage grain.
* **C7 COAL_PRB stands failing 3/3 on the keeper with NO open admissible
  lever.** Caveat budget stays 3/3 saturated; C7 is not ledgered.
* Rule 26 duty (b): `coal_takeorpay_committed` MISO cell updated with the
  miso-103 adjudication. Rule 22 honoured — no solve, no out-of-training
  touch (2018–2022 receipts are authorized on-disk intake, read only as
  inputs to a no-LP statistical test).
* Next number: **miso-104.**

## 2026-07-29 — miso-104: the coal minimum-take TONNAGE data ask is OPENED — an ex-ante contractual series exists as a FERC Form 580 field and as public Kentucky contracts, but NOTHING carries it at plant grain across the MISO target set for 2023–2025, so no candidate was testable; keeper UNCHANGED

**Keeper UNCHANGED: `2026-07-28-miso-101b-tempgrain`.** No solve, no run, no
bundle, no dashboard registration, no intake — a sourcing session. Deliverable:
the standing ask
`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` (the second MISO
data ask, beside outage grain). Reproduction of the coverage ledger:
`scripts/probes/miso104_contract_source_coverage.py` (no LP, no network).

* **Charter executed as written** (miso-103 §4): evaluate availability,
  plant-grain mappability and 2020–2025 vintage coverage for (a) FERC Form 580,
  (b) state fuel-adjustment-clause filings, (c) IRP fuel-budget exhibits — and
  run the miso-103 pin-strength battery on **any** series found *before*
  proposing a mechanism charter. **No series reached the threshold of being
  testable, so the battery was not run — not skipped: there is nothing to run
  it on.** That is the finding.
* **Target set quantified:** 39 plants, **26 owners, 12 states**, all EIA-860
  regulated; **94.0 / 80.7 / 89.5 Mt** in 2023/2024/2025. Top five owners
  (Union Electric, Rainbow Energy Center, MidAmerican, DTE Electric, Duke
  Energy Indiana) = 39/44/44 % of tonnage; the tail runs to municipals and
  co-ops under 1 Mt.
* **(a) FERC Form 580 — the RIGHT FIELD, at the WRONG GRAIN.** Q6a collects a
  genuinely ex-ante **"Fuel quantity — Coal (×10³ tons)" per contract**, with
  contract signing and expiration dates and an evergreen flag; Q6b links each
  delivery to a named **Destination Plant** and even reports "Coal (×10³ tons)
  not delivered by end of contract year". Four measured blockers: **(1) grain**
  — the quantity is contract-grain and the plant only appears on delivery rows,
  so pushing it down needs delivered-ton weights, i.e. miso-103's refuted answer
  key; only 1:1 contract↔plant cases are admissible and that share is
  **unmeasured**; **(2) coverage** — Q6 is answered only by holders of a
  *wholesale* 18 CFR 35.14 FAC, **24 respondents nationally across all fuels and
  regions** (ICR IC25-1-000, 2024-12-03; 29 in the 2020 collection), while the
  MISO set recovers fuel through *state retail* clauses; **(3) scope** —
  contracts >1 year only; **(4) vintage** — biennial, each form covering the two
  prior CYs, so the latest filed (2024) covers CY2022–**2023** and CY2024–2025
  arrives with the 2026 form **due 2026-10-30**. Today it spans **one** of three
  training years (rule 16 `[R-ALLYEARS]`). No bulk/API access (eLibrary is a
  Cloudflare-gated SPA; `/eLibraryAPI` probes 404). Cycle confirmed from the
  waiver notices: **DTE Electric** filed for the 2024 form on 2024-10-31
  (90 FR 7691), **PG&E** for the 2026 form on 2026-05-21 (91 FR 32025).
* **(b) State filings — Kentucky is the exemplar and covers 1 of 39 plants.**
  807 KAR 5:056 makes each fossil fuel purchase contract a public filing; the
  Alliance Coal / LG&E–KU agreement **J24007** (executed 2024-01-19) publishes,
  un-redacted, a **Base Quantity table by delivery year 2024–2028** plus
  quarterly nomination minimums, make-up tons and force majeure — exactly the
  datum, fixed years before delivery and with stated conditions under which it
  moves. But the repository covers six Kentucky utilities of which only **Big
  Rivers Electric** is MISO: **D B Wilson = 1.5 / 1.1 / 1.1 %** of target
  tonnage, no cross-section. The large MISO states file it under seal —
  Indiana's public FAC exhibit §VI "Coal Contracts and Inventory" is purely
  qualitative with the specifics in confidential attachments (Cause 38702
  FAC-91, 2023-09-05). **Michigan PSCR** (MCL 460.6j, genuinely ex-ante;
  DTE+Consumers = 12.8 % of 2025 tonnage) is the one remaining unchecked lead.
* **(c) IRP fuel-budget exhibits — REJECTED ON KIND, do not re-attempt.** IRPs
  publish *modelled* burn: another model's forecast of the outcome, which is
  rule 13's forbidden half in a worse form than receipts (not even a
  measurement). Closed on principle, not availability.
* **Also ruled out permanently:** EIA-923 Schedule 2 purchase-type / expiration
  -date subsetting (dates are terms, the quantity on the row is a delivery);
  SEC 10-K purchase obligations (company grain, **dollars**); coal-producer
  "committed and priced tons" (producer grain, no plant key); FERC Form 1 p.402
  (burn, ex post); STB waybill (ex post, no plant id in the public file).
* **The ask is written to be decidable, not aspirational:** a coverage bar
  (**≥15 of 39 plants AND ≥60 % of tonnage in EVERY training year** — below
  that the battery yields no R² and the constraint governs a corner), and the
  pin-strength battery made **binding** with thresholds — level-R² **≥0.80
  FAILS**, no year may put the aggregate floor above actual burn (miso-103's
  2024 was 1.136×), and the **delta test is the one that must PASS**: an
  admissible contractual series shows the **inverse** profile of the receipts
  construction (lower level-R², higher delta-R² than 0.87–0.94 / 0.172). A
  symmetry clause records that a clearing source showing minimums that do **not**
  bind has *refuted* the minimum-take hypothesis — reportable, not discardable.
* **Bounded next experiment (ask §8):** pull the 2024 Form 580 filings for the
  26 target owners from docket IN79-6 and count (i) filers, (ii) Q6 answerers,
  (iii) 1:1 contract↔plant coal contracts and their share of 2023 target
  tonnage. If (iii) clears, the lane is **timing-blocked** — it unblocks when
  the 2026 form lands CY2024–25 — rather than data-blocked.
* **Rule 22 honoured: nothing was intaken.** No new-source authorization was
  requested or granted; nothing written under `data/raw/`; every document read
  in scratch and re-fetchable from the ask's §7 citation table. Rule 26 duty
  (b): `coal_takeorpay_committed` MISO cell updated in-session with this
  outcome. Rule 15: no run produced, nothing to register.
* **C7 COAL_PRB still fails 3/3 with no open admissible lever**; caveat budget
  stays 3/3 saturated and C7 is not ledgered. The lane's continuation is a data
  ask, not a solve.
* Next number: **miso-105.**

## 2026-07-29 — miso-105: MISO's DA virtual lever is REFUSED ex ante on its OWN COMPLETE SUBMITTED BOOK — the source exists and was found, the premise is measured false, and the only channel big enough to move C3b is the curve's own crossing price; NO solve, keeper UNCHANGED

**Keeper UNCHANGED: `2026-07-28-miso-101b-tempgrain`.** No solve, no run, no
bundle, no dashboard registration, no intake. Matrix cell `da_virtual_bids`
× MISO: **U → G**. Evidence:
`results/calibration/FINDING-miso105-da-virtual-attractor-2026-07-29.md`.
Probe: `scripts/probes/miso105_da_virtual_identifiability.py`.

* **The source exists — this is new for the repo.** MISO publishes the
  **submitted** virtual bid/offer curve with a price axis:
  `docs.misoenergy.org/marketreports/YYYYMMDD_bids_cb.zip`, its FERC-Order-719
  masked demand-bid archive on a ~90-day lag, one row per **bid × hour** with
  `PRICE1..9 / MW1..9` plus the cleared `MW` and the clearing `LMP`.
  `Type of Bid` D = DEC / I = INC. Probed span 2023-01-01 → 2026-01-01 all HTTP
  200, 2022-06-01 and earlier 404 — the rolling window is **quarantine-safe by
  construction** (rule 22 needs no authorization question here).
* **Ladder semantics IDENTIFIED from the file, not assumed.** Reading
  `(PRICE_i, MW_i)` as **incremental** blocks and clearing them against the
  row's own LMP reproduces the published cleared MW for **99.36 %** of 207,549
  priced virtual bid-hours (MAE 0.028 MW) against 93.49 % / 0.410 for the
  cumulative reading. The same test proves the ladder is *submitted*: **66.66 %**
  of priced bid-hours carry blocks that did not clear.
* **Provenance proved in BOTH directions** — the strong form nyiso-94 could not
  reach. Cleared `MW` = 16.3 % / 14.9 % of load in 2024 against the IMM's
  published **15.8 % / 14.5 %** (2024 SOM Appendix Table A2), while the submitted
  ladder is **2.49–2.79×** larger. Same table: PJM 5.9 % / 5.6 %.
* **Refused on three MEASURED grounds, not on access.**
  (a) **Premise false.** PJM's lever runs on **+7–11 GW** net DEC at the top
  summer hours; MISO's summer-peak net cleared virtual is **+1.09 / +2.47 /
  −0.34 GW** — negative in 2025, the year C3b fails — and **−158 / +1,336 / −62
  MW** in the RT>$300 tail (6/13/28 hours). MISO's book is **2.7× PJM's as a
  share of load gross and ≈ 0 net**: a convergence and congestion instrument,
  verbatim the IMM (2025 SOM §IV.B — "essential to price convergence",
  **1,694 MW/h** of energy-neutral **matched** pairs).
  (b) **Immaterial where admissible.** The peak-minus-night net differential
  (+1.40 / +1.28 / +0.43 GW) at the keeper's own re-measured summer stack slope
  (**0.54 / 0.56 / 0.64 $/GW**, miso-89 §2 ventile method on the miso-101b
  sidecars) buys **+$0.75 / +$0.72 / +$0.27** of diurnal spread against a
  **$14.6 / $15.9 / $20.5** C3b summer gap — **5.1 / 4.5 / 1.3 %**, shrinking as
  the miss grows.
  (c) **The material channel is inadmissible — a blocker nyiso-94 never reached
  because NYISO had no data to reach it.** The measured net curve's crossing
  price **λ0 reproduces the price its own book cleared at to $0.09 / $1.80 /
  $0.17**, and its stiffness (**0.93 / 0.93 / 0.69 GW per $/MWh**) against the
  model stack's elasticity (**1.85 / 1.79 / 1.56 GW/$**) means arming it supplies
  **31–34 % of every hour's price displacement, and ~63 % at the steepest 2025
  summer ventile**. The model's price would substantially *become* the measured
  book's crossing price — rule 1 `[R-STRUCT]`, and rule 13 `[R-MEASURED]`'s
  forward test dies because whatever regenerates the curve forward must reproduce
  λ0, which **is** the price the model exists to forecast.
* **Rule 19 `[R-ONE-MECH]` — nothing stacked.** D-2 was enumerated from the
  keeper's committed `legitimacy_diagnostics.json` first: `nuclear_mustrun`,
  `chp_steam` (h0–23), `reliability_floor × CT_PEAKER` (h14–21),
  `reliability_floor × ST_GAS` (h0–23), `st_gas_mustrun_per_plant` (h0–23) — all
  D-4 clean, **none a diurnal-price-spread mechanism**. C3b's ledgered root cause
  (the ~10 GW 2025 summer-peak under-derate, miso-89 §7 + the outage-grain data
  ask) is untouched and was not widened, re-scoped or substituted for.
* **Rule 25 `[R-ISO-SCOPE]`.** No parameter crossed a boundary. PJM's `K` is
  **not** re-adjudicated — but the λ0-attractor question is a property of the
  mechanism family that was never asked in PJM's lane, and is recorded as an
  observation for PJM to answer on **PJM's own** data (its λ0-gap, its
  `N ÷ (S+N)`). CAISO/NEISO stay `U`.
* **Rule 22 honoured: nothing was intaken.** No `data/raw/` write — the archive
  carries cleared `MW`/`LMP` alongside the submitted ladder, and parking that in
  the input tree would be a re-armable answer key. Everything is in scratch and
  re-fetchable from the finding's §2. Rule 15: no run produced, nothing to
  register. Rule 26 duty (b): cell updated in-session.
* **Caveat budget UNCHANGED at 3/3** (C3a, C3b, C3c). Nothing ledgered, added,
  widened or re-scoped; C3b's determination stands exactly where miso-90 left it.
* **C3b keeps no open in-model lever.** Its identified driver stays the
  instrument-blocked outage-grain gap (standing data ask), and MISO item 3 is now
  closed alongside items 1–2.
* Next number: **miso-106.**

## 2026-07-30 — miso-106: measured CT loaded heat rates → KEEPER (matrix §5.4 item 4, MISO cell U → K)

Lever picked off the MISO queue head after items 1–3 closed (coal minimum-take
RHS a standing data ask, outage grain instrument-blocked, DA virtual depth
refused ex ante by miso-105 with a DO-NOT-REDO list). Item 4 was the only
remaining entry with a promoted precedent, an in-repo ISO-parameterised
derivation path, and audit value independent of any gate.

**Keeper → `2026-07-30-miso-106b-ct-heatrate`** (bundle
`results/calibration/miso106_ctheatrate_B`), replacing
`2026-07-28-miso-101b-tempgrain`. Owner-authorized in-session. Determination
**NOT-YET** with an **identical criterion profile** to the keeper it replaces
(9 scored / 6 target-grade / 2 ledgered / 1 fail), decided by the same C7
COAL_PRB shape issue this delta does not touch. Ledgered caveats **unchanged at
2/3** (C3a, C3c). Control arm `2026-07-30-miso-106a-ct-hr` registered alongside it.

**Ledger correction, and a standing prose drift worth fixing.** This session
first wrote the budget as "3/3 (C3a, C3b, C3c)", repeating its handoff premise;
the keeper auditor caught it and the artifacts settle it. **miso-98 moved the
ledger 3/3 → 2/3**, *deleting* the C3b-2025 entry under rule 26 `[R-DELETE]`
once the criterion passed on its own gate. Both this bundle's and the outgoing
keeper's `calibration_attestation.json` carry **no `price_shape` exception** and
both score `ledgered: 2`. Yet several MISO log entries *after* miso-98 —
including miso-105's — restate the budget as "UNCHANGED at 3/3 (C3a, C3b,
C3c)". That is stale prose that drifted from the artifact, not a governance
change, and it propagated into this session's handoff prompt. **A successor
should sweep the post-miso-98 entries.** This session consumes and frees
nothing.

**One delta:** `measured_ct_heat_rates=True` on a **MISO-derived** artifact —
86 of 168 CT_PEAKER plants, 19,121 of 22,289 MW (85.8 % of class capacity,
≈92–96 % of the class's real energy), zero band exclusions, two-signed (56
cheaper / 30 dearer), capacity-weighted 12.290 → 11.868 but generation-weighted
only −0.1 %. Rule 25: the same flag is a keeper in NYISO (nyiso-89) and PJM
(pjm-137) and **neither ISO's rates, coverage or predicted direction crossed the
boundary**. Zero fitted parameters; DOF ledger 26 entries / **2 residual — the
same two as the outgoing keeper**.

**Two measured input defects repaired (rule 14).** South Fond Du Lac (7203,
326.5 MW) was priced at eGRID **26.544 MMBtu/MWh**, above the physical
simple-cycle ceiling, because its turbines ran at CF ≈ 0.5 % so the annual mean
is start fuel (measured loaded 14.014; one of 5 MISO plants / 445 MW outside
[6, 25]). And 19 plants / 1,651 MW carried a **combined-cycle rate on a peaker**,
which CAMPD's own `unitType` tag separates decisively — Perryville 55620 units
1-1/1-2 `Combined cycle` vs 2-1 `Combustion turbine` (model 6.890 vs measured
10.774); Zeeland 55087 CC1/CC2 `Combustion turbine` matching the model's 318.2 MW
at 8.587 vs measured 10.922.

**Gates.** Every criterion verdict identical to a same-HEAD flag-off control.
C3a improves in all three years (−1.4 → −1.2 %, −6.7 → −6.6 %, −14.3 → −14.2 %);
D-1 CT_PEAKER cv_ratio moves toward 1.0 in 2024 (0.848 → 0.931) and 2025
(0.805 → 1.046); C3c bit-identical (1/6/0 h both arms); D-4 exactly 0.000.

**Four things move the wrong way and it was promoted anyway (rules 1/14).**
(a) C1 CT_PEAKER |err| degrades in all three years — −20.18 → −26.35 %,
+1.31 → −3.63 %, +2.73 → −3.69 % — and **the pre-registration was wrong in
direction for 2024/2025**: it predicted improvement, and the ~1 TWh/yr volume
fall (correct in sign) overshot past zero. All inside the ±8 TWh band.
(b) **D-2 CT_PEAKER forced share rises 11.77 → 14.21 %** (cap 15 %) with forced
**energy up 47 %**, 1.188 → 1.743 TWh: correctly-priced peakers want to run less,
so the h14-21 `reliability_floor` binds harder and now holds up capacity the
corrected economics would shut off. **New open item** — not to be closed by
relaxing the floor or reverting the input. (c) C3b-2025 0.190 → 0.192 inside its
0.20 veto, the pre-registered cost of removing the top of the CT curve.
(d) Zeeland's CTs genuinely run hard (CF 0.532) and pricing them correctly cuts
their model hours — rule 14's named scenario, root cause left open.

**G3 failed as pre-registered and is recorded as a fail.** Bit-identity of the
control to the committed keeper was never obtainable: main had moved **21 files
/ 1,312 insertions under `src/market_sim/`** since the keeper's code basis, and
the threshold was written without checking that. The control instead establishes
a measured noise floor — total generation **+0.000000 %** in all three years,
mean LMP within **$0.0001**, worst per-class annual **0.00630 %** — and every
claimed movement is orders of magnitude above it. *Successors: check
`git diff <keeper basis>..HEAD -- src/market_sim/` before pre-registering a
bit-equality control.*

**Execution.** A single-process three-year solve was **OOM-killed at 15.9 GB**
on a 15 GB box; both arms were rebuilt one fresh year per process, chained with
`--reuse-solved` into one 2023–2025 bundle (rules 12/16), as miso-96/98 did.
`--reuse-solved` carries `dispatch/` forward but **not** the derived
`hourly/class_hourly_*` sidecars — regenerated by the solver's own groupby and
verified by reproducing the solver's 2025 sidecar exactly first. That gap is a
candidate fix in the reuse path. Rule 22: 2023–2025 only, no holdout touched.

Evidence: `results/calibration/FINDING-miso106-measured-ct-heat-rates-2026-07-30.md`;
pre-registration committed before either arm was solved:
`results/calibration/PREREG-miso106-measured-ct-heat-rates-2026-07-30.md`.
