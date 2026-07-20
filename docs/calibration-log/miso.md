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

**Disposition.** Keeper swap to the corrected-envelope bundle recommended
(owner-only, pending). Quarantine untouched (train years only). With the
re-audit HELD, the MISO frontier path is open: owner may declare the
calibration-complete marker (NEISO precedent — the two fails are the ledgered
irreducible tail), then the holdout ladder (MISO out-of-training intake is at
zero; data-readiness session next, then the 2022 validation one-shot per rule
22/G-19). Next number: miso-82.
