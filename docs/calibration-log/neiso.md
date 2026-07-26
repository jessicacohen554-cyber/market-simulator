# Calibration Log — NEISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for NEISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — Intake: ISO-NE Morning Report operable-capacity (DAM-equivalent outages/availability)

Data-intake session (no solve, no keeper change). Intaken the ISO-NE **Morning
Report Section 3 Operable Capacity Analysis** — the ISO-NE analogue of ERCOT's
measured DAM class-day availability (`ercot-thermal-dam-availability.csv`): daily
published **Generation Outages and Reductions (Planned + Forced)** and **Total
Available Capacity** MW, 2018-07-01 → present (~2,940 days; parse identity
`H=A+B−C−D+E−F−G` = 0 MW/row). Committed per-year CSVs
`data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv`
(ERCOT-analogue committed-CSV precedent — the API-only push path can't
round-trip binary and carries content inline, so CSV partitioned by year;
`build --parquet` emits a columnar copy locally)
(fetch + build scripts + README + test). New loader
`data.neiso_operable_capacity.neiso_thermal_availability_series` (committed) is
the consumption API; a **default-OFF** gate
`ScenarioConfig.neiso_operable_capacity_availability` + a fleet-builder block
apply the measured fleet thermal availability (`1 − outages/(CSO+EcoMax-above-
CSO)`) by the ERCOT-style bidirectional water-fill, superseding the CAMPD
unit-outage fallback for the covered thermal classes when enabled. The gate +
fleet block ship as `docs/handoffs/patches/neiso-operable-capacity-wiring.patch`
(scenarios.py/fleet.py are ~0.5 MB each — too large for the API push), verified
to apply cleanly onto pristine main and inert when off. Fleet grain only
(ISO-NE publishes no public per-unit outage series). Rule-22 authorization +
registry: `docs/out-of-sample-results-2026-07.md §1.5`; design + admissibility:
`docs/handoffs/neiso-operable-capacity-intake-2026-07.md`. Turning the gate on /
promoting is a future NEISO-lane decision — this session delivers data + opt-in
wiring, verified inert when off.

## 2026-07-19 — gas_daily_shape §3.7 fix A/B: NEISO exactly price-inert (hub overlay supersedes); probes registered

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the neiso-60 keeper recipe the fix is exactly
price-inert in all three years — the AGT hub-basis daily overlay replaces every
covered gas row, so the national HH shape never reaches NEISO dispatch.
Registered `2026-07-19-neiso-gasshape-interpfix`(+`-base`) as the inertness
record; no keeper action.

## 2026-07-23 — neiso-61: gas-offer NET-REVENUE MARGIN form (markup compression) BUILT + A/B'd — C3b improves EVERY training year, the 2022 validation C3a flips FAIL→PASS (+30%-class → +6.3%); KEEPER CANDIDATE, swap awaits the owner

**Charter.** The 2022 holdout rotation (`2026-07-23-neiso-2022-holdout-validation`,
NOT-YET) rejected the multiplicative offer form: every gas band's $/MWh markup
over true MC scales linearly with the fuel bill (`markup = base_HR × (mult−1) ×
gas`), unidentified inside the homogeneous 2023–25 training gas window
(delivered year-means 2.94/3.03/6.26 $/MMBtu) and ballooning at 2022's ~2.9×
delivered gas — the 40–80 bulk over-priced +57.7 $/MWh over 4,546 h while the
fixed scarcity wall never forms the tail. Design FROZEN before the build
(`docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md`); model Fable.

**Mechanism (`gas_offer_net_revenue_margin` + `gas_offer_margin_anchor`,
ScenarioConfig, default OFF — zero fitted scalars).** Each registered gas band
multiplier decomposes into a MEASURED physical basis (`phys_*` keys on
`_NEISO_OFFER_CURVE`, from the committed CAMPD marginal-HR artifact
`neiso_campd_marginal_hr_summary.csv`: committed → avg_committed_p50 block
burn, econ → marg_econ_{low,high}_p50 incremental burn, peak → physical duct
2.25 for CC / full-output 1.0 for CT/ST) plus a markup, and the markup is
repriced from fuel-scaled to a FIXED $/MWh net-revenue margin at the
train-window delivered-gas anchor (4.0763 $/MMBtu — mean of the model's own
`_gas_series` over 2023–25; `scripts/data/derive_gas_offer_margin_anchor.py`,
rule 23). Offers reduce EXACTLY to the registered multipliers at anchor gas;
off-anchor the physical burn keeps full fuel/oil-parity tracking while
offer/mc compresses toward 1 — both halves of the already-ledgered neiso-45
winter-over/summer-under signature. Implemented as a vectorized
post-`assemble_mc` adjustment on the base cost (P0+P1), `bins_to_fleet` stamps
per-tranche `offer_markup_hr`; bands/ISOs without phys keys are byte-identical
(rule 24), coal sigmoids and `tranche_startup_amortization` untouched
(rule 19). The Potomac-SOM net-revenue construction ports to the offer side as
the derive script's cross-check: the CT scarcity margin ($129.7/MWh) recovers
FOM-only GFC over ~162 scarcity run-hours. Gas-sweep invariance + composition
tests in `tests/test_offer_curves.py` (21 tests).

**Runs (registered, rubric v2.7).** `2026-07-23-neiso-61-netrev-base` (neiso-60
recipe replayed verbatim at HEAD): BYTE-IDENTICAL keeper parity — max hourly
price diff 0.000000 in all three years — zero HEAD drift AND exact flag-off
inertness at full-solve scale. `2026-07-23-neiso-61-netrev-margin` (single
delta `gas_offer_margin=true`, KEEPER CANDIDATE, CWC with the keeper's caveat
census): **C3b duration-shape NRMSE improves EVERY year — 0.133→0.102,
0.194→0.164, 0.152→0.071**; C3a stays inside ±10% all years (+5.2/+7.1/+5.2%
vs base +1.2/+3.3/+9.1% — the high-gas 2025 improves, the below-anchor years
firm); C3c/sysvol/fuelmix/dispatch_corr/co2/forced_share unchanged-PASS. LOYO
(rule 22): the mechanism carries NO per-year parameter; the shape gain holds
in each year independently — the opposite of an overfit trade.

**2022 re-check (LAST, after in-sample+LOYO; `2026-07-23-neiso-61-margin-2022`,
marker-authorized).** C3a mean LMP: **PASS +6.3%** (load-weighted 96.76 vs
actual 91.0) vs the base holdout's FAIL (+30%-class rotation). Duration bands
(hour-matched, equal-hour hub basis): <40 +39.8→+29.4, 40–80 bulk
+57.7→**+38.0**, 80–150 +13.5→**−5.9**, 150–300 −97.1→−113.2, >300
−261.1→−284.2. The bulk/mid rotation closes substantially; the tail worsens
slightly as PRE-REGISTERED — C3b 2022 (0.592) and C3c (0 vs 117 h) stay FAIL,
owned by the separate gas daily→monthly fallback
(`docs/holdout-data-equivalency-register-2026-07.md` §NEISO) and
reserve-scarcity lanes. NO parameter responds to the 2022 result.

**DOF ledger.** Candidate attestation carries the keeper's ledger + two new
MEASURED entries (anchor: derive script; phys keys: CAMPD artifact p50s); the
markup levels are the already-registered surface — only their gas-elasticity
changed (1 → 0). n_entries 10, n_residual unchanged at 5.

**Open / next.** (1) Keeper swap neiso-60 → neiso-61-netrev-margin is the
OWNER's decision (miso-70 precedent) — evidence: strictly better C3b all
years + the 2022 C3a flip, C3a level inside band everywhere, all other gates
unchanged. (2) The remaining 2022 bulk gap (+38) is the gas daily→monthly
fallback item, its own charter. (3) The tail lane (reserve scarcity / 117 h)
unchanged, already at frontier per 2026-07-11. (4) ISO-agnostic rollout:
other ISOs need their own measured phys registries + anchors (rule 24) —
PJM/MISO/NYISO curves already carry measured marginal-HR artifacts. Next
shorthand: neiso-62.

## 2026-07-24 — neiso-62: ISO-NE operable-capacity availability A/B'd — the source RESTORES (not removes) capacity, C3a improves in every year, but it is NOT adopted (fleet-wide denominator on a thermal-only application); the real finding is that the NEISO CAMPD outage extract over-counts thermal outages by ~15 pp

**Charter.** Evaluate and, if warranted, adopt the ISO-NE "DAM-equivalent"
operable-capacity availability overlay
(`neiso_operable_capacity_availability`, wired 2026-07-19, never armed by any
run) for the NEISO keeper. Model Opus.

**STEP 0 — the gate was off-registry.** The gate existed in `ScenarioConfig`
and was applied in `data/fleet/arrays.py`, but no calibration entry point
exposed it, so no run could arm it or record it in `run_config.json`
(rule 24). Threaded through `solve_and_persist` → `run_year` →
`ScenarioConfig` exactly like `neiso_winter_fuel_mustrun` (tri-state
`bool | None`), plus the `--neiso-operable-capacity-availability` flag and the
`meta.json` entry. Ships as `docs/handoffs/patches/neiso-operable-capacity-cli-flag.patch`
(both files are in the size class the push API cannot carry inline —
`run_calibration_full.py` 464 KB, `run_calibration.py` 233 KB — and rule 27
forbids a regenerated full-file push); verified to apply onto pristine
`origin/main` and reproduce both files byte-for-byte.

**A0 — inert when off (`2026-07-24-neiso-62-opcap-a0`).** Verbatim
`--replay-bundle` of the `neiso-61-netrev-margin` keeper recipe at HEAD with
the gate absent: **max hourly LMP diff 0.0000000000 in all three years**,
zone-mean LMP identical to 4 dp (38.9364 / 44.0783 / 71.3163). The STEP-0
plumbing is provably inert at its default, so every A1 delta is the gate alone.

**A1 — the gate on (`2026-07-24-neiso-62-opcap-a1`). Direction is RESTORE, not
remove.** The overlay fires **restore-364 / remove-0** (2023): ISO-NE's own
published outage rate is far BELOW the model's CAMPD-derived one, so it *adds*
thermal capacity rather than stripping phantom capacity. Pooled cap-weighted
thermal availability **0.584 → 0.840 annual, 0.567 → 0.898 DJF** — ~4,458 MW
annual / ~5,779 MW winter restored on a 17,438 MW thermal fleet. Mechanism
attribution (fleet-only rebuilds): the winter gas cold-snap derate is NOT
involved (−0.02 pp); with the CAMPD extract alone disabled the model sits at
0.862/0.893, i.e. **the entire 28-pp gap is the CAMPD unit-outage derate.**

| criterion | A0 / keeper | A1 |
|---|---|---|
| C1 fuel-mix | PASS, 12/12 (free 8/8) | PASS, 12/12 (free 8/8) |
| C2 system volume (gas) | PASS (2025 +2.6%) | PASS (2025 +2.6%) |
| **C3a mean LMP (vs RT, LW)** | +5.2 / +7.1 / +5.2 % | **−5.2 / −1.0 / −2.9 %** |
| C3b duration NRMSE | 0.102 / 0.164 / 0.071 | 0.103 / **0.143** / 0.079 |
| C3c tail (>$300, RT) | 0h vs 15/8/20h — ledgered | 0h — unchanged, ledgered |
| C4 gas dispatch r | 0.910 / 0.916 / 0.863 | 0.911 / 0.917 / **0.885** |
| C5a CO2 vs eGRID | −2.5 / −2.3 / +4.9 % | −3.1 / −2.8 / +4.2 % |
| C8 forced share (CC_REGULAR) | 0.4 / 0.7 / 0.5 % | 0.9 / 1.6 / 1.3 % |
| determination | CALIBRATED-WITH-CAVEATS | CALIBRATED-WITH-CAVEATS |

So the fit **improves**: mean |C3a| deviation 5.8 % → 3.0 %, better in every
year; C3b/C4/C5a roughly neutral (2024 shape and 2025 dispatch-r improve).
The one cost is the upper tail thinning — h>$200 **70→26** (2023) and
**102→42** (2025) — though the $300 C3c gate reads 0h either way.

**NOT ADOPTED — and the reason is structural, never the residual (rule 1).**
The consumed fraction is `1 − C/(A+B)` where the numerator (Section 3 line C)
is **generation** outages but the denominator (A+B = CSO + EcoMax-above-CSO,
~30,264 MW in 2023) spans the **whole obligated fleet** — nuclear, hydro,
renewables, DR and import obligations — while the fraction is applied to the
**thermal subset alone** (17,438 MW). The PJM analogue in this repo divides its
measured outage MW by *fossil-thermal capacity*, not the full fleet. Re-basing
the published outage MW onto the model's thermal denominator gives
**0.737 / 0.761 / 0.777** (2023/24/25) against the as-implemented
0.849 / 0.858 / 0.863 — the implementation **over-restores by ~11 pp**.
Adopting it as-built would be reaching a better number through a mechanism
that is not (yet) the real one; rule 14's boundary-mismatch clause prescribes a
**reconciled** version of the real data instead. Note the reconciliation has an
irreducible ambiguity — line C is published as a single figure, so the
non-thermal (notably nuclear-refuel) share cannot be split out, and the honest
thermal-availability band is **[0.737, 0.849]**. Picking a point inside that
band is a free parameter and needs an owner call, not a session default
(rules 20/24).

**HEADLINE FINDING — the probe's real deliverable.** Even the *most
conservative* reconciliation (0.737, attributing 100 % of published generation
outages to thermal) sits **~15 pp / ~2,700 MW above the model's 0.584**. The
NEISO CAMPD unit-outage extract derates **40 % of the thermal capacity-year**
(2023: CC_REGULAR alone 5,804 MW-yr on a 15,534 MW fleet = 37 % unavailable);
window durations are median 13 d / mean 22 d with none under 2 d — the
**economic-layup** signature, *not* the ERCOT-79 daily-cycling one the
2026-07-19 re-audit screened for. So the extract still over-counts thermal
outages after that re-audit, and the keeper's offer curves are **co-dependent**
on the over-count: relieving it moves LMP −7 to −9 % and halves the h>$200
tail. That is the **ERCOT-79 / nyiso-63 condition** (rule 11: the estimate was
silently compensating for something else), and it puts a question over the
NEISO frontier (2026-07-11) and calibration-complete marker (2026-07-07) that
this probe does not itself resolve.

**Open / next.** (1) **Reconcile the denominator** — re-base
`neiso_thermal_availability_series` onto a thermal capacity basis (the PJM
construction), owner to settle the [0.737, 0.849] band, then re-A/B; that is
the version that could be adopted. (2) **Re-audit the NEISO CAMPD extract for
economic layup**, the root cause under rule 11 — the detector cannot currently
distinguish a laid-up CC from an outaged one. (3) Keeper unchanged:
`2026-07-23-neiso-61-netrev-margin` stands; no parameter in this session
responded to any residual. (4) STEP C (2022 validation re-solve with outage
data) **NOT run** — no owner authorization for an out-of-training solve was
given this session; the stale zero-outage `2026-07-23-neiso-61-margin-2022`
therefore still stands un-superseded and should not be trusted. Locked test
(2019 + H1-2026) untouched. Next shorthand: neiso-63.

## 2026-07-24 — neiso-63: CAMPD extract re-audit — the over-count is ECONOMIC LAYUP booked as outage, and it is a DETECTOR-WIDE systematic (all six ISOs), not a NEISO bug

**Charter.** Owner-authorized root-cause re-audit opened by `neiso-62`: the
ISO-NE operable-capacity A/B showed the model deleting ~4,458 MW annual /
~5,779 MW winter of thermal capacity that ISO-NE's own accounting says is
operable, with LMP moving −7 to −9 % when relieved — the rule-11 condition. No
solve, no keeper change, no parameter touched. Model Opus. Full evidence:
`results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md`.

**Verdict: the detector books sustained economic layup as mechanical outage.**
Four independent signatures, all from committed artifacts, no LP:

1. **Seasonal anti-correlation.** Detector ÷ ISO-NE published (Section 3 line C):
   autumn **1.06 / 0.96 / 0.86×** (2023/24/25) but winter **2.58 / 2.76 / 1.76×**.
   ISO-NE's profile is the textbook maintenance shape — low in both peak seasons,
   high in the shoulders; the detector matches it exactly where real maintenance
   dominates and diverges hardest where New England CCs are priced out by winter
   basis.
2. **Simultaneity.** Jan 2023: **31 of 58 `CC_REGULAR` units (53 %, 6,645 MW)**
   flagged out at once, against 2,929 MW published across *all* generation. July
   carries the fewest (11 units). Common-mode, not idiosyncratic.
3. **Repeat events.** Median **7 separate "outages" per unit-year** (max 15),
   **mean 153 d out = 42 % of the year**. No CC breaks fifteen times a year.
4. **The filter's own premise.** `filter_revealed_outages` keeps a span that is
   down through ≥24 local high-load hours, and separately any ≥5-day full stop —
   whose docstring states the assumption *"economic idling backs down but does
   not fully stop for weeks"*. That is false for a NEISO CC in a high-basis
   winter, so **both** surviving branches keep exactly the wrong windows.

**Two candidate fixes TESTED and RULED OUT** (recorded so they are not rebuilt).
*Unit-level frequency filtering*: keeping only units with ≤3 windows/yr fixes the
shape (monthly r +0.53→+0.84, +0.47→+0.75, +0.70→+0.96) but destroys the level
(410 vs 4,575 MW) — **the contamination is window-level, not unit-level**, which
is the binding constraint on any repair. *Common-mode discrimination*: at every
τ ∈ [0.30, 0.50] the seasonal correlation is **worse than no filter at all**;
genuine shoulder maintenance is itself clustered. Leading remaining candidate is
a **merit-order guard** (delivered fuel price × heat rate — rule-13 admissible,
and the detector already carries class economic guards) — a mechanism change
needing its own charter, frozen design, and LOYO (rule 22); deliberately not
attempted here.

**Cross-ISO: every extract carries it.** CC capacity-year booked as outage —
ERCOT 24 %, MISO 23 %, PJM 23 %, CAISO 37 %, NEISO 39 %, **NYISO 46 %** (PJM COAL
42 %) against a real CC EFOR + planned norm of ~10–15 %. The 2026-07-19
phantom-outage re-audit missed this because it screened the ERCOT-79
*daily-cycling* fingerprint, a different failure mode. Escalated to
`governance.md` — this is a cross-ISO item, and the four DAM-first gates wired
2026-07-24 give CAISO/MISO/NEISO/PJM a published instrument to run the same
check against at no solve cost.

**Open / next.** (1) The merit-order guard is the fix charter. (2) The neiso-62
denominator band [0.737, 0.849] is now **secondary** — fix the detector first and
let the operable-capacity series serve as the validation instrument it suits
(fleet-grain cannot carry per-unit availability). (3) Keeper unchanged:
`2026-07-23-neiso-61-netrev-margin`. (4) Frontier (2026-07-11) and
calibration-complete marker (2026-07-07) are **open questions, not withdrawn** —
unlike nyiso-63 the determination held and the fit improved; recommend freezing
further holdout spending until the extract settles. (5) STEP C (2022 validation)
still **not run** and now explicitly deferred behind the extract fix; the stale
zero-outage `2026-07-23-neiso-61-margin-2022` remains un-superseded and should
not be trusted. Locked test untouched. Next shorthand: neiso-64.

## 2026-07-25 — neiso-64: CAMPD merit-order guard — built, validated cross-ISO, keeper re-audited (fix-in-place)

STEPS 1–4 of `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`.
Model Opus. Keeper **unchanged** (`2026-07-23-neiso-61-netrev-margin`).

**Design frozen first (charter §3a, owner sign-off).** The out-of-merit test is
the unit's measured **SRMC** (CAMPD heat rate × delivered fuel price) against
**RCC(t)** — the capacity-weighted p90 SRMC of the units *measured running* that
hour; a window is economic layup when it is out of merit for ≥90 % of its hours.
The self-referential variant (window fuel price vs a percentile of the unit's
own running-hour prices) was probed and **rejected with cause**: the heat rate
cancels out of a within-unit percentile, so it sees only the fuel-blowout half of
out-of-merit — it left NEISO JJA at 1.93× and its 2024 gain sat *inside* the
placebo band. Cross-unit ranking is what puts the heat rate back. D2 reclassify
(labelled `campd-unit-outages-layup-<ISO>.csv`, no loader reads it), D3 one
ISO-agnostic rule (class enters only as physics — cogeneration excluded via
measured `steamLoad`, fuel selects the price series), D4 thin data is inert and
fail-safe (Henry Hub never substitutes for a missing ISO basis).

**Built default-OFF and proven byte-inert at full extract scale.** A complete
2018–2026 re-derive with `--merit-order-guard` absent reproduces **every**
committed extract blob exactly (NEISO `a95c0928`, CAISO `3dc01fae`, NYISO
`181fefb9`, ERCOT `b4b48f5a`, PJM `5283f5c6`, MISO `f2b3ec8e`). Ships as
`docs/handoffs/patches/campd-merit-order-guard-{lib,deriver}.patch` (rule 27 —
both files clear the 300-line bar); apply lib first.

**Validated against the published instruments, no solve** (full tables:
`results/calibration/RESULTS-neiso64-merit-order-guard-2026-07.md`). Graded on a
same-GW-days placebo, so a guard that merely subtracts capacity cannot pass:
ERCOT **3/3**, NEISO 2/3 (2025 exactly at p95), MISO 2/3, PJM 1/3 (its baseline
r is already +0.90 — no room), CAISO **0/3**, NYISO no instrument. NEISO level
1.52/1.57/1.22× → **1.36/1.29/0.92×**, monthly r +0.53/+0.47/+0.70 → **+0.71/
+0.61/+0.78**. **Positive control**: ISO-NE publishes the layup population
separately (`uncommitted_available_gen_nonfast_mw`), and the guard sorts the two
window sets into exactly those two buckets — KEPT tracks published outages
(+0.71/+0.61/+0.78) and is near-orthogonal to uncommitted (+0.08/+0.28/+0.31);
VETOED does the reverse (−0.26/+0.01/+0.24 vs **+0.77/+0.71/+0.67**).
**2024 is the hardest year in every ISO** — mild winter, low basis, so the
fuel-cost signal is weakest exactly where the over-count is worst. **ERCOT gains
an anchor** (owner, this session): `ercot-thermal-dam-availability.csv`
(`rating − live`), with the caveat that DAM offered capacity itself conflates
outage with non-offering. **NYISO alone stays unverified.**

**STEP 4 — keeper re-audit, `2026-07-25-neiso-64-meritguard-a1`.** The keeper
recipe replayed verbatim on the corrected envelope, 2023–2025 one bundle. A0 is
the keeper itself (the guard is byte-inert off, so an A0 re-solve is the keeper
by construction). **C3a +5.2/+7.1/+5.2 % → +3.4/+6.0/+3.2 %; C3b NRMSE
0.102/0.164/0.071 → 0.085/0.157/0.057** — both load-bearing price criteria
improve in **every** year, nothing regresses, C3c tail unchanged at 0 model
h>$300. LOYO is met by construction: no year traded against another. C1/C2/C4/
C5a/C8 all PASS. **Verdict: fix-in-place, not re-tune** — the anticipated
ERCOT-79/nyiso-63 co-dependency does *not* bite here; relieving the over-count
improves the offer curves rather than breaking them. Bundle determination
NOT-YET on C6 governance UNATTESTED only (a candidate arm carries no DOF-ledger
attestation; C3c reads FAIL rather than the keeper's ledgered CAVEAT for the
same reason, on an identical underlying 0 h).

**Push limits, stated rather than papered over.** The corrected extracts, their
`-layup` companions, the run payload `runs/<id>.js` (372 KB) and the bundle's
parquet sidecars **could not be pushed** — the API-only path carries content
inline and cannot round-trip files that size or binary at all. Committed here:
the registry sidecar, `metrics.json`, the two patches, the scorer, the results
doc. Everything else is deterministic from committed inputs and regenerates
with the two commands in the results doc §5. **The run is
registered-by-sidecar but will not render on the dashboard until `runs/<id>.js`
lands via a git-push path.**

**Open / next.** (1) Charter verdict is the owner's: the guard is a genuine
measured improvement, **not a closure** — NEISO 2023–24 still runs 1.29–1.36× a
*whole-fleet* published total on a thermal-only extract, so a residual
over-count survives. (2) **Highest-value follow-up: a CAMPD↔CAISO resource
crosswalk.** CAISO's report is per-resource, so a crosswalk turns the weakest
instrument into per-unit ground truth — the strongest validation available
anywhere in this charter. (3) 2024's weak fuel-cost signal is the mechanism's
known limit. (4) Holdout freeze **remains in force** — no validation or
locked-test year was solved, scored or registered. Next shorthand: neiso-65.
