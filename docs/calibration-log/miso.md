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
