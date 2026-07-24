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
