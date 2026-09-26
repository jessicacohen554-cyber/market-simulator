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

## 2026-07-26 — neiso-65: charter verdict executed — guard ADOPTED, extracts committed, freeze HELD; a1 payload landed

Owner verdict (charter §8): ADOPT-AS-IMPROVEMENT + hold the freeze. All six
guard-corrected extracts + layup companions committed (NEISO: 444 windows /
1,083 GW-days reclassified 2023–25, reproduced exactly). The
`2026-07-25-neiso-64-meritguard-a1` bundle regenerated deterministically and
its dashboard payload landed (sidecar byte-identical, all scored criteria
reproduce). NEISO verdict stays FIX-IN-PLACE (neiso-64); keeper unchanged
(neiso-61). Cross-ISO re-audits + the CAISO crosswalk:
`results/calibration/RESULTS-neiso65-crossiso-reaudit-2026-07.md`. The
neiso-63 residual over-count stays open — now corroborated per-resource at
CAISO (1.5–2.3× on the crosswalked active-plant scope).

## 2026-07-26 — neiso-66 / neiso-67: the residual over-count is a DEFINITIONAL SEAM, and it is NOT closable by a detector discriminator — charter's deferred item closed on evidence; freeze-lift now the owner's call

No LP solve, no keeper touched, no out-of-training year touched. NEISO remains
calibration-complete (2026-07-07) and at frontier (2026-07-11); the keeper is
unchanged (neiso-61). Nothing here is calibration work and nothing is
registrable on the dashboard — this lane produced findings, not runs.

**neiso-66 (recorded here retrospectively; the finding was committed 2026-07-26
without a log entry).** The residual CAMPD outage over-count that held the
holdout freeze is neither a detector error nor a publisher reporting gap. It is
a definitional seam: CNOG/ISO-NE publish *unavailability*, the CEMS detector
measures *non-operation*, and the difference is available-but-not-committed
capacity. Both of the re-audit's candidate directions are refuted by
measurement — interior-day CEMS inside the excess windows is 99.8 %
zero-generation and 97 % of windows are complete stops (so no cycling is being
booked as outage), and the excess windows run ~10 days (so they are not missed
intraday forced outages). Confirmed directly against ISO-NE's own published
`uncommitted_available_gen_nonfast_mw`: the residual tracks it at +0.70 to
+0.85 and is anti-correlated with published outages at −0.85 to −0.86. A
CAISO-only defect was corrected on the way (the CNOG `tail(1)` collapse
inflated every published-side ratio ~1.3×; NEISO's daily instrument is
unaffected, so its 1.29–1.36× levels stand).
`results/calibration/FINDING-neiso66-overcount-rootcause-2026-07-26.md`.

**neiso-67 — STEP 2, and it is a NEGATIVE result.** The one remaining
mechanism the finding left untested was commitment economics: does the observed
idle/run split track start-cost recovery over the expected run, per unit? It
does not. Built on measured CAMPD operation + delivered fuel + published
NREL/SR-5500-55433 start costs, with the charter D1 revealed-clearing-cost
reference recomputed **leave-one-out** and the expected run taken as the
best contiguous ≥ min-run block in a day-ahead horizon:

- **per unit it is a coin flip** — median AUC 0.502 / 0.546 / 0.530 (2023/24/25),
  and 0.47–0.57 across all 18 configuration-years swept (RCC p50/p75/p90/p99 ×
  horizon 24/48/72 h). In every one of the 18 it scores **at or below the plain
  marginal spread** it was meant to replace; dividing by the published start
  cost *subtracts* AUC.
- **on the seam population the sign inverts** — booked-out days carry *higher*
  recovery than the same units' running days (×0.81 / ×0.89 / ×0.90, AUC
  0.405 / 0.391 / 0.405), and **89–93 % of seam days already repay the published
  start cost** while the unit stays off for a median ~10 days.
- **the commitment band identifies nothing** — `0 ≤ R < 1`, the only band that
  is new information (the `R < 0` half is the merit guard's own marginal cut),
  scores −0.51 / +0.26 / +0.05 against the published uncommitted series, and in
  all three years correlates *better with published OUTAGES* than with
  UNCOMMITTED. Against the D1 positive control's +0.77 / +0.71 / +0.67, that is
  no signal at all.
- **the instrument is proven live**, so the null is a property of the
  hypothesis: the `R < 0` band tracks published UNCOMMITTED at +0.48 to +0.79 in
  18 of 18 cells.

Probe: `scripts/probes/_neiso67_startcost_recovery.py` (re-runnable, no solve).
Finding: `results/calibration/FINDING-neiso67-commitment-test-2026-07-26.md`.

**Open / next.** (1) **STEP 3 disposition is the owner's decision.** The
recommendation is (b) carry the seam explicitly — option (a), a
commitment-aware second discriminator in the detector, is not buildable on the
evidence and rule 19 `[R-ONE-MECH]` forbids stacking it on the guard.
(2) **The freeze stays ACTIVE.** Its `lifts_when` condition ("the residual is
explained or fixed") is now met on the *explained* branch, but only the owner
lifts it and no session lifts it by inference — see charter §9. (3) Separately
open, and NOT a freeze blocker: whether the seam is better closed on the LP side
(neiso-66 §5b, rule 1) — a different lane on a different instrument, where
`caiso_ra_mustoffer` already owns this capacity's commitment. (4) A live
observation flagged not proposed: the day-grain best-block `R < 0` cut tracks
published UNCOMMITTED at +0.63 to +0.79 where the guard's window-grain
out-of-merit share reaches +0.08 to +0.31 — a possible *replacement* for the
guard's cut, in its existing marginal lane, unvalidated cross-ISO. Next
shorthand: neiso-68.

## 2026-07-26 — neiso-68: LANE A (the LP-side seam question) measured and closed — the keeper LP would NOT decline the seam population

**neiso-68 — the LP-side seam screen, and it is a second NEGATIVE.** The open
item neiso-66 §5b left (do these units belong in the envelope as *available*,
with the LP declining them on its own commitment economics?) is now measured on
the LP's own instrument — the `neiso64_meritguard_a1` keeper replay's committed
hourly price sidecars, scored pass, every panel unit priced at its own zone's
dual. No LP solve; probe `scripts/probes/_neiso68_lp_seam_screen.py`.

- **the seam is in merit against the model's own prices, essentially always** —
  median seam-day in-merit share 100 % at every offer level up to the keeper's
  committed 1.27×; zero-clear days only 1–15 %; 87.7 / 97.6 / 91.9 % of seam
  days repay the published start cost at LP prices (2023/24/25).
- **seam days are indistinguishable from the same units' running days** — AUC
  0.508 / 0.478 / 0.495; the LP's strict decline predictor fires as often on
  days the units actually ran.
- **the LP-decline split fails the D1 identification standard** — r vs
  published UNCOMMITTED +0.58 / +0.51 / +0.65 against placebo p95 +0.73 /
  +0.52 / +0.66 (clears none), identifying only 0.7–1.4 GW of the 5.7–7.9 GW
  idle population.
- **restoration breaks the solution either way** — first-order 15–38 TWh of
  phantom dispatch at fixed keeper prices, against median seam-day spreads of
  +$15–21/MWh that no plausible price feedback (measured restoration effect
  ≈ −$3–4/MWh) can close.
- **the LP price sits ABOVE the detector's RCC on seam days** (+3.8 / +13.9 /
  +10.7 $/MWh) — whatever declines these units in reality is not a price level
  the model fails to see.

The population's behaviour is now measured irreproducible from every allowed
instrument: marginal economics (neiso-66 §4), start-cost recovery (neiso-67),
and the model's own price surface (neiso-68). The envelope deletion is
definitionally impure but **operationally load-bearing** — the only mechanism
in the system producing the observed non-operation. An LP-side closure would be
a new *decline* mechanism (the existing bridges force capacity ON) with no
identified driver, which rules 1/12/19 forbid reaching for.
Finding: `results/calibration/FINDING-neiso68-lp-seam-screen-2026-07-26.md`.

**Open / next.** (1) **STEP 3 disposition remains the owner's decision**, now
with both halves measured: recommendation unchanged and strengthened —
disposition (b), carry the seam explicitly; the charter §7 "Closed with cause"
leg fits. (2) **The freeze stays ACTIVE**; its `lifts_when` condition is met on
the *explained* branch, but only the owner lifts it. (3) The Lane B observation
(day-grain best-block `R < 0` as a possible *replacement* for the guard's
window-grain cut) remains flagged, unvalidated cross-ISO, and untouched by this
session. Next shorthand: neiso-69.

## 2026-07-26 — CAMPD charter LANE B (cross-ISO, **no NEISO lane number claimed**): the day-grain `R < 0` cut does not replace the guard's window-grain cut

Charter/cross-ISO session — measurement only: no guard change, no extract
re-derive, no LP solve, **no NEISO keeper touched**, no dashboard registration.
Full record: `results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md`;
cross-ISO entry in `docs/calibration-log/governance.md`.

NEISO's cell of the 180-cell sweep (`--rcc-pctl {0.50, 0.75, 0.90, 0.99}` × `--horizon {24, 48, 72}` ×
2023–2025), scored against **ISO-NE Morning Report Section 3 `gen_outages_reductions_mw`**:

* **KEPT-extract monthly `r` at the default p90 / h24**, window-grain → day-grain:
  2023 **+0.69 → +0.65** (Δ −0.038), 2024 **+0.61 → +0.61** (Δ −0.007), 2025
  **+0.78 → +0.73** (Δ −0.047). Over NEISO's 36 cells the day cut is better in
  **14/36**, median Δ **−0.006**; the sweep's largest deltas anywhere (−0.09 to
  −0.14, p50/p90 at h48–h72) are NEISO's and run **against** the candidate.
  Lengthening the horizon degrades it monotonically (+0.662 → +0.616 → +0.604
  mean kept-`r` at p90, vs the incumbent's flat +0.693).
* **The flagged observation restated on NEISO's own instrument.** Against
  published `uncommitted_available_gen_nonfast_mw`, the guard's **VETOED** side
  reads **+0.77 / +0.73 / +0.66** and the candidate's **+0.70 / +0.74 / +0.53**.
  neiso-67 §6 item 2's `+0.63…+0.79` vs `+0.08…+0.31` had compared an
  identified-layup series against the guard's **KEPT** series — the two opposite
  sides of one split, not two cuts.
* **The two cuts pick the same windows**: Jaccard 0.92 / 0.97 / 0.94, and the
  candidate's veto set is a strict **subset** of the incumbent's in all three
  years (day-only vetoes 0 / 0 / 0).
* **Controls passed**: the re-implemented incumbent reproduces NEISO's committed
  kept/layup split on 468/471, 466/470, 480/484 windows; the ported machinery
  reproduces neiso-67's idle `R < 0` band (812 MW/+0.70, 1,104/+0.80, 1,071/+0.64)
  and the charter D1 anchors (baseline 1.52×/+0.53, guard-on 1.37×/+0.69,
  vetoed-vs-UNCOMMITTED +0.77).

**Nothing in NEISO changes.** The merit-order guard stands as the charter §8
verdict adopted it, NEISO's committed extract and layup companion are
untouched, and no rule-22 obligation arises because no mechanism change is
proposed. **The freeze stays ACTIVE** — Lane B was never one of its conditions.
Next shorthand is unchanged: **neiso-69**.

## 2026-07-28 — neiso-69: the measured unit-availability window family is REJECTED on PROVENANCE (matrix U→R) — the one derived window belongs to a unit the fleet does not carry, and applying it deletes a unit that never stopped

**Lane:** OFF-QUEUE input-accuracy lever (rule 28a). A rule-14 `[R-ACCURATE]`
measured-availability input in the sense of `measured_ct_heat_rates`, **not** a
member of NEISO's frontier-declared C3c scarcity family; no new charter needed,
and nothing here is framed or promoted as a C3c lever.

**Keeper `2026-07-23-neiso-61-netrev-margin` UNCHANGED.** Both flags stay
default-off. Nothing armed.

**Step 1 — derivation (frozen constants; no guard loosened, no class scope
widened, no gas-CC extension):**

| extract | windows | units | MW-days |
|---|---|---|---|
| `campd-unit-outages-short-NEISO.csv` | **1** (2023 only) | 1 — Merrimack u2 | 691 |
| `campd-partial-outages-NEISO.csv` | **0** | 0 | 0 |

NEISO's entire CEMS coal fleet 2023–25 is one plant (Merrimack, 2364). Raw
annual CF 4–9 %; modelled `COAL_BIT` is 0.10 / 0.13 / 0.20 % of load, 102 MW
peak — an order of magnitude under rule 20's materiality line.

**The stop-branch was NOT taken.** The partial half is a provable no-op (empty
extract → measured `{}` overlay), but the short half is **not** inert: it drives
the coal bin's availability multiplier to **0.0000** across h744–815, where the
standard ≥5-day overlay carries 1.0000. It had to be tested.

**Why it is rejected — the window is unit-mismatched.** Merrimack u2 (345.6 MW)
is `OS` in EIA-860 and the fleet **excludes** it; the `(2364,'COAL')` bin is
**108.0 MW = u1's net summer capacity**, the whole NEISO coal fleet. The
plant-keyed overlay applies u2's window at u2's capacity share against that
denominator (345.6/108.0 → clipped to full derate) and thereby zeroes **u1** —
which per hourly CEMS ran **72 of 72 masked hours** at 103 MW mean and a flat
121 MW through the Feb 3–4 2023 Arctic outbreak, covering **8 of 2023's top-22
prices**. The keeper already tracks u1 to **≈7 %** there. Arming the family
**deletes measured supply** instead of removing a phantom — the inverse of the
PJM case that motivated it.

Contributing cause, ISO-local: the `when-operable CF ≥ 0.55` baseload guard is
degenerate where the standard overlay already books the fleet ~90–97 % offline.
It judged Merrimack on **6–10 % of the year** (u2 2023: 528/8760 h, CF 0.611 on
that sliver vs a true annual 0.046). Operable-hour share 0.06 sits below both
PJM's (median 0.62) and MISO's (0.75) 10th percentile — **no verdict transfers
to their `K` cells (rule 25)**; the per-plant exclusion-share spot-check is left
to those lanes.

**A drift CONTROL arm was required.** The keeper's committed sidecars no longer
reproduce at HEAD (solved at `eede1c4`, 2026-07-23, since squash-merged), so
keeper-relative deltas charge code drift to the mechanism. Both arms registered:
`2026-07-28-neiso-69-control` and `2026-07-28-neiso-69-shortpartial`.

**MECH (arm − control) — 2023-only and gate-neutral:**

* 2023: `COAL_BIT` **−7.5 GWh** → `CC_REGULAR` +6.0, `oil` +1.5; TOTAL +0.0.
* **2024 + 2025: exactly 0.0 for every class and every hour** (no windows;
  both overlays `{}`) — all their apparent movement is drift (CT_PEAKER −89.6 /
  −189.7 GWh, CC_REGULAR +145.8 in 2025).
* Prices: **105 / 8760** hours changed in 2023, **0** in 2024/2025; annual mean
  LMP **+$0.005**, p99 +$0.47, max hourly +$3.25 (h770, Feb-02 02:00 — the one
  day the unit genuinely was off, not the Feb 3 evening peak).
* **Control and arm score criterion-for-criterion identically.** The rejection
  is not fit-motivated in either direction.

**DOF ledger:** zero free parameters, zero residual solves — measured-physical,
mirroring the ercot129 / pjm-113 treatment. The rejection returns both flags to
default-off, so the keeper's ledger is unchanged.

**Observation filed, not chartered:** Merrimack u2 (330.5 MW net summer, `OS`)
carries no LP representation though it generated ~140–260 GWh/yr and ramped to
320 MW in the Feb 3 2023 peak. Genuine representation question, but `COAL_BIT`
is 0.1–0.2 % of load, so it cannot move a gate. No charter, nothing armed.

Next shorthand: **neiso-70**.

## 2026-07-31 — neiso-70: measured CT loaded heat rates PROMOTED (matrix `U`→`K`, new keeper); measured CHP heat rates tested and OPEN (`U`→`O`) — the CHP overshoot locates a missing CC_CHP host-steam floor

**Lane:** rule 14 `[R-ACCURATE]` input-accuracy, two arms off ONE shared
same-HEAD control. **C3c was not targeted and did not move** — bit-identical in
every arm (model 0 h vs RT 15/8/20 h). The frontier declaration stands; neither
§5.6 item 1 nor item 2 was opened.

**New keeper: `2026-07-31-neiso-70-ctheatrate`** (bundle
`neiso70_ctheatrate_B`), replacing `2026-07-23-neiso-61-netrev-margin`.
Full record: `results/calibration/FINDING-neiso70-heat-rate-provenance-2026-07-31.md`;
pre-registration `PREREG-neiso70-heat-rate-provenance-2026-07-31.md`, committed
and pushed at `20ce479` **before either arm solved**.

**Why a control was mandatory (and what it caught).** The outgoing keeper's
`git_sha` `eede1c4` is **not in the repo** — squash-merged away — so no
keeper-relative delta is attributable. Control vs committed keeper drifts by
**912.9 / 963.9 / 1,029.0 MW** on CC_REGULAR (hydro 553–907, oil 528–747,
CT_PEAKER 315–346), and CT_PEAKER's own annual energy drifts −0.048 / −0.090 /
−0.190 TWh. The numerics stack also differs from the keeper's recorded
environment (highspy 1.14.0 vs 1.15.1, pandas 3.0.3 vs 3.0.5, pyarrow 24.0.0 vs
25.0.0 — the repo's committed `requirements.txt` pin is *older* than the stack
the keeper was solved with), so the drift is **code + environment and cannot be
decomposed** with `eede1c4` gone. Every number below is **arm − control**.

**Flag fidelity, discharged BEFORE any solve (the ERCOT-146 hazard).** NEISO
runs the same `use_campd_bins` / `plant_level_fleet` configuration that made the
flag inert in ERCOT, but only `iso == "ERCOT"` reads the curated sheet in
`assembly.load_or_synthesize_bins`; every other ISO **synthesizes** its bins from
the flagged fleet. Verified empirically (`scripts/probes/_neiso70_flag_fidelity.py`):
CT arm moves 31 generators / 910.4 MW, CHP arm 20 / 271.0 MW. Both live.

**Named risk resolved before solving.** The `pinned_classes` label is
**scorer-side D-10, not an LP pin**: CC_CHP carries **no** D-2 forced row in any
year (100 % free) and CT_CHP is 94–97 % free, so a re-price acts directly on
dispatch. What the label *does* cost is scoring reach — CC_CHP is
`excluded_from_free` and CT_CHP is not a scored C1 row — so lever 2 could never
improve the free-class score, and was pre-registered to be reported that way.

### Arm 1 — `measured_ct_heat_rates` → **`K`, PROMOTED**

Artifact: 8 plant rows, **8 applied, ZERO excluded by the physical band**;
75.6 % of class capacity but **100.0 % of the class's own metered CAMPD CT
energy**. Direction is **NEISO's own** and matches no precedent ISO: two-sided
(6 plants / 817 MW cheaper, **2 / 94 MW dearer**), cap-wt **−0.579 MMBtu/MWh
(−5.7 %)**. Adverse selection **present and stated** (covered cap-wt incumbent
HR 10.208 vs uncovered 11.830), mitigated but not erased by every uncovered
plant metering zero CT energy.

* **Every pre-registered gate PASSES; ZERO status changes across all 70 scored
  records.** C1 all 12/12 · free 8/8, C3c bit-identical, determination
  CALIBRATED-WITH-CAVEATS with the same single ledgered caveat, **DOF residual
  count unchanged at 5** (the new ledger entry is `measured`, not fitted).
* CT_PEAKER 0.183 → 0.309 / 0.362 → 0.832 / 1.098 → 1.706 TWh, funded by
  CC_REGULAR (−0.121 / −0.461 / −0.619); total generation moves ≈ 0.005 %.
* **The structural deliverable:** D-2 CT_PEAKER `reliability_floor` forced share
  **collapses 0.3958 → 0.2013, 0.2735 → 0.0736, 0.0680 → 0.0272** — correctly
  priced, the class clears **economically** instead of leaning on its commitment
  floor. **MISO-107 in reverse** (there the same mechanism made MISO's CT floor
  *more* load-bearing, because its CTs had been carrying CC heat rates): same
  mechanism, opposite structural consequence, each ISO on its own fleet.
* C1 CT_PEAKER absolute error improves in **both scored years** (0.282 → 0.156,
  0.292 → 0.177 TWh). 2025 moves further over, **disclosed in the prereg in
  advance, against interest**; its C1 row is SKIPPED on a preliminary EIA-923
  vintage (57 % plant reporting).
* **Reported, not gated:** 2025 CT_PEAKER D-1 `cv_ratio` 0.521 → 0.288. **Not a
  broken protective gate** — C7 `shape` is SKIPPED for NEISO in keeper, control
  and arm alike, `profile_r` stays far above floor (0.930→0.965, 0.982→0.976,
  0.976→0.976), C8 PASSES, and CT_PEAKER is 0.19–1.0 % of load, under rule 20's
  2 % materiality line.

### Arm 2 — `measured_chp_heat_rates` → **`O` (open), NOT promoted, flag stays default-off**

Live (204.6 MW) and accurate (CEMS 4/4 within 1 %, median 1.00000); every gate
passes with **zero criterion regressions**. But it **overshoots the class it
reprices**: CC_CHP 1.334 → 0.703 / 1.254 → 0.910 / 1.216 → 0.539 TWh against
actual 1.072 / 1.124 / 1.194 — over- to under-generating in every year
(|error| 0.224 → 0.369, 0.130 → 0.214, 0.022 → 0.655). Counterweight reported in
full: CC_REGULAR improves markedly (0.471 → 0.156, 0.340 → 0.030), so the
*combined* CC_CHP + CC_REGULAR error actually falls in both scored years.

**Root cause located — structural, not tuning: NEISO's CC_CHP carries NO
`chp_steam` D-2 row at all**, control and arm, all three years (CT_CHP has one
at 2.9/5.3/5.8 %; CAISO's CC_CHP runs 43–47 %). With no host-steam obligation
floor, a **+27.96 %** dearer offer lets those cogens drop out far past what a
real cogen must run to serve its host. The signature confirms it: CC_CHP D-1
`cv_ratio` **explodes** 2.814 → 6.99 / 6.499 → 10.231 / 2.156 → 11.248 while
`profile_r` barely moves — timing right, amplitude blown out.

Stamped **`O`** deliberately: not `K` (the fit on the repriced class degrades,
which blocks *promotion*, never the *input*), not `R` (nothing refuted on the
merits — rule 14 forbids reverting to the eGRID estimate because it fits
better), not `I` (demonstrably live). The mechanism is **structurally
incomplete as armed** — the ERCOT-141 "half a mechanism" pattern.

**DO-NOT-REDO.** Do not re-test the CHP re-price alone, and do not tune the CHP
heat rates toward the CC_CHP residual (rules 1/14/23 — the artifact re-derives
only on a new eGRID vintage). Do not cite lever 2's CT_CHP half as evidence in
either direction: it covers 19.3 % of capacity and **0.0 % of metered energy**
(every covered CT_CHP plant is below the Part-75 boundary), so it is not
identified.

**DOF ledger (rule 21):** zero fitted parameters added. The keeper's ledger
gains one `measured` entry (`measured_ct_heat_rates[NEISO]`), 11 entries total,
`n_residual` **unchanged at 5**.

**Governance.** Years 2023–2025 only; the holdout spend freeze is ACTIVE and
NEISO's locked test is already SPENT (2026-07-07), never re-grantable. All three
bundles registered (rule 15) — control, keeper arm and open arm alike. Both
matrix cells updated with evidence citations (rule 28b) and the NEISO header
re-stamped.

**Open / next.** (1) **neiso-71: derive a measured NEISO CC_CHP host-steam floor
and land it together with `measured_chp_heat_rates`** — one mechanism, not two
(rule 19). (2) `nuclear_unit_availability` needs Millstone 2/3 + Seabrook rows in
`derive_nuclear_availability.NRC_TO_EIA`, which today covers **PJM (31), NYISO
(4) and CAISO (2)** only. (3) §5.6 items 1/2 still require their own owner
charter; item 4 (NG:PS time split) and item 5 (STEP 3 seam) are unchanged.

Next shorthand: **neiso-71.**

---

## neiso-71 — CHP host-steam floor CLOSED (no LP spent); `nuclear_unit_availability` PROMOTED

**New keeper `2026-07-31-neiso-71-nucavail`** (bundle `neiso71_nucavail_B`),
replacing `2026-07-31-neiso-70-ctheatrate`. Determination unchanged:
**CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered C3c caveat, C1 all 12/12 · free
8/8, DOF `n_residual` unchanged at 5.** Pre-registered at `464817e` and pushed
before either arm solved
(`results/calibration/PREREG-neiso71-nuclear-availability-2026-07-31.md`);
evidence `results/calibration/FINDING-neiso71-chp-floor-nuclear-2026-07-31.md`.
Both bundles solved at the **identical frozen HEAD `464817e`**, `dirty: False`,
on the requirements-pinned stack — **no environment drift this session**
(contrast neiso-70).

### Lever A — the CC_CHP host-steam floor: MEASUREMENT-BLOCKED, cell stays `O`

The session's primary lever (matrix §5.6 item 6) asked whether NEISO's CC_CHP
should carry a host-steam floor like CAISO's. **It should not**, and the
screen cost no LP (`scripts/probes/_neiso71_lever_screen.py`).

The floor already exists as the committed WP-3 statistic `steam_level_cf`;
NEISO simply carries a **pre-WP-3 artifact vintage** (neither `steam_level_cf`
nor `p25_allhr_cf`), so `chp_steam_floor_p25` is **inert for NEISO** and
`chp_pmin_cf` is 0.0 on all three CAMPD-visible CC_CHP plants — the mechanical
reason the class has no `chp_steam` D-2 row. Re-deriving on NEISO's own CAMPD
returns **146.1 % of nameplate** for Kendall Square (EIA 1595, 42 % of the
class): **saturated, not measured** — CAMPD facility 1595 unit "4" meters
**278/299/283 MW median** against an EIA-860 CHP nameplate of **213.4 MW
(206.0 summer)**, binding the derivation's 1.5 clip guard in **59.0 %** of
online hours. Armed it would floor Kendall at **195.7 MW / 95.0 % of pmax
year-round (~1.71 TWh/yr)** and **over-close** neiso-70's 0.34–0.68 TWh CC_CHP
shortfall — a fitted parameter (rules 21/24), and one that would have bought a
visibly "better" backcast.

**The structural answer:** NEISO's merchant CC_CHP genuinely carries no
host-steam obligation. The other two CAMPD-visible plants measure **2.2 %** and
**3.6 %** — the statistic self-targeting real cyclers (online 5.5 % / 7.0 % of
hours) — and the non-Kendall CC_CHP floor totals **15.0 MW**. A real fleet
difference from CAISO's flat 43–47 % steam hosts, not a missing mechanism.
**DO-NOT-REDO**: the successor is a **fleet/nameplate lane** (Kendall's capacity
basis, inside the miso-95 provenance-orphaned `nameplate_mw` column), not a
floor lane; every capacity-factor lens inherits the same broken denominator.

### Lever B — `nuclear_unit_availability` → `K`, PROMOTED

The whole code delta is a **three-row identifier crosswalk** (Millstone 2/3 →
EIA 566, Seabrook 1 → EIA 6115; **3,355.4 MW ≈ 22 % of ISO energy**) — no
`src/` change, the seam and loader were already ISO-generic. 3,288 rows,
**365/366/365** coverage, **all 36 months reconcile** inside `WEDGE_TOL` (worst
−0.70 %) so no month is dropped; `--check` byte-for-byte; **zero fitted
scalars** (constants frozen from the ERCOT deriver, rule 23).

What it fixes: in **2025 Millstone 2 never fell below 94 % and Seabrook below
47 % while Millstone 3 took a full refuel**, yet the Apr/May anchor (0.75/0.77)
derates all three alike. NEISO nuclear is `nuclear_mustrun`-pinned at 0.999+, so
the overlay moves the **must-run floor itself** hour-by-hour.

* **Every pre-registered gate PASSES** — G-1 fidelity (3 reactors, 1.000
  coverage), G-2 control integrity (recipe diff `{}`), G-3 liveness
  **1,129/1,842/1,265 MW** (20–37× the 50 MW floor), G-4 single delta
  (`['nuclear_unit_availability']`, proven by construction), G-5 span, and the
  P-1 energy-neutrality KILL check (**−0.0079/−0.0006/−0.0313 TWh** vs 0.05).
* **ZERO criterion status changes** across all nine criteria. C3c
  **bit-identical** (model 0 h vs RT 15/8/20), so the ledger entries carry
  verbatim and no slot is spent.
* **Fit improves:** scored C1 total |error| **2.602 → 2.521 TWh** (12 scored
  rows, 2023+2024; the six 2025 rows are SKIPPED on preliminary EIA-923).
  Mean λ −0.025/−0.024/−0.019. D-2/D-4 PASS both arms, shares moving ≤0.005.

**Reported against interest.** (a) Pre-registered prediction P2's **zonal half
did NOT materialize** — Millstone and Seabrook sit in different zones, but all
four NEISO zones clear at an **identical mean λ** in both arms (no binding
internal congestion at annual-mean grain); only the timing half is confirmed.
(b) **D-1 fails in BOTH arms on the same class/year set** (COAL_BIT 2023–25,
ST_GAS 2023) — pre-existing, not a regression, C7 `shape` SKIPPED for NEISO;
2024 COAL_BIT `profile_r` improves 0.617 → 0.753 while 2023 slips 0.600 →
0.588. (c) The C1 gain is a net: 7 rows improve, 6 worsen, 5 unchanged.

**Process note.** The arm was killed mid-solve and relaunched on a misread:
`bins_to_fleet` builds its own `FleetArrays` from the thermal-tranche list and
logs `overlay: 0 reactor(s)` **before** the runner logs the real `3`. Reading
only the first occurrence mimics the ERCOT-146 inert-flag signature — **read the
LAST occurrence**. ~5 min of compute, no effect on correctness. Follow-up: that
call site should not emit the line at all.

**Governance.** Years 2023–2025 only; the holdout spend freeze is ACTIVE and
NEISO's locked test is already SPENT (2026-07-07), never re-grantable. Both
bundles registered (rule 15); matrix cells + `ev` citations updated and the
NEISO header re-stamped (rule 28b); `audit_keepers --iso NEISO` **0 failures,
0 warnings**.

**Open / next.** (1) **NEISO CC_CHP capacity basis** — Kendall Square metering
278–299 MW against a 206.0 MW model pmax; prerequisite for any future CC_CHP
floor. (2) §5.6 items 1/2 (C3c DA-bid depth, import-side scarcity) still need
their own owner charter. (3) Item 4 (NG:PS hydro time split) and item 5 (STEP 3
seam) unchanged.

Next shorthand: **neiso-72.**

---

## neiso-72 — 2026-07-31 — the PS time split: hydro level goes per-window; PROMOTED keeper `2026-07-31-neiso-72-hy-window`

**Lever:** §5.6 item 4 (handoff Lever B) — the `NG: PS` hydro-pin audit's last
open cell (`hydro_level_923_hy` NEISO `U` → **`K`**; the cross-ISO audit row is
now CLOSED at all six ISOs).

**The defect, measured** (`scripts/probes/_neiso72_ps_window_audit.py`;
`PREREG-neiso72-hydro-ps-window-2026-07-31.md` committed pre-solve): NEISO is
the only ISO filing `NG: PS` at all, from a single measured seam hour —
**2024-11-07 00:00** (zero filed hours 2019-01→2024-11-06). Pre-split `NG: WAT`
carries the full ~1.9 TWh/yr PS block on four independent tests; the decisive
one is confound-free (the seam falls INSIDE November 2024: max 1,873→685 MW,
swing 7.11×→1.79× six days apart, vs 0.77–1.03× for the same cut in the five
no-seam years). The +2.7 %/+10.1 % level gap understates the fold ~8× — a
~1.2–1.6 TWh/yr 930 telemetry under-count of the 923 census cancels against it
(two errors landing near zero, the rule-14 silent-compensation signature).
NEISO PS is endogenous storage (1,865.0 MW), so the pin double-represented its
discharge.

**The fix (design D, owner-adjudicated over flat/splice/subtract-estimated-PS;
owner also asked and got the coverage answer — split data = 1.15 yr, used for
diagnosis, never for the correction):**
`constants.EIA930_PS_SPLIT_COMPLETE_FROM = {"NEISO": 2025}` +
`data/hydro.py::eia930_wat_level_folded` — pin refused per-year before the
first wholly-split year (2023/2024 → the units' own 923 `HY` filings, builder
budgets 8.5762/6.7144 TWh), kept for wholly-split 2025. One source basis per
year. Forecast lane: 923 climatology while the window holds any folded year,
self-un-arming as it rolls past the seam. Zero free parameters.

**A/B** (same-HEAD `10c624e`; control `neiso72_control_A` reproduces the
neiso-71 keeper to 4 decimals): every pre-registered check passed — 2025
bit-identical (`.equals=True`, the KILL check), liveness 632/713 MW, E1 sign
exact (hydro −0.186/−0.654/0 TWh, CC_REGULAR +0.178/+0.583/0, LMP
+$0.050/+$0.159/$0.000). **Every criterion IDENTICAL to the keeper**:
CALIBRATED-WITH-CAVEATS, C1 all 12/12 · free 8/8, same C3c ledger — scorecard
unchanged, structural defect removed. Promoted on owner authorization (the
gates-may-regress clause was not needed).

**Bench-basis note:** the 2024 C1 hydro actual is itself the folded 930 series
(7.3942 exactly); the candidate's paper ratio ≈0.91 sits inside the band, and
≈0.99 against the honest 923 actual. Successor, scorer-side.

**Governance.** Years 2023–2025 only (locked test SPENT, untouched; probe read
2019–2022 raw source, no-LP). Both bundles registered (retention pruned
neiso-60-phantom-outage + neiso-gasshape-interpfix); matrix cells + ev + header
re-stamped; `check_mechanism_matrix.py` integrity OK.

**Open / next.** (1) **Storage-side PS cycling depth** — first measured
gross-cycling series shows ~4× under-cycling (1.932 vs 0.497 TWh, 2025);
dispatch-adder/AS-value lane, never a hydro patch. (2) Handoff **Lever A**:
CC_CHP capacity basis (Kendall Square ~90 MW) — the PRIMARY, untouched here.
(3) Bench hydro 2024 re-base (scorer-side). (4) §5.6 items 1/2 still need
their own charter; item 5 still pending owner decision.

Next shorthand: **neiso-73.**

---

## neiso-73 — 2026-07-31 — Kendall Square capacity basis ADJUDICATED: artifact, no missing capacity; NO LP spent

**Lever:** handoff Lever A (PRIMARY) — the neiso-71 §1 fleet/nameplate
successor. Keeper `2026-07-31-neiso-72-hy-window` **untouched**; no solve, no
bundle, no registration.

**The question:** is the ~90 MW gap between CAMPD facility-1595 unit "4"
gross load (278/299/283 MW median, max 321) and the EIA-860 CC_CHP basis
(213.4 nameplate / 206.0 summer = model pmax) an EIA-860 understatement or an
attribution artifact?

**Verdict — ARTIFACT** (`scripts/probes/_neiso73_kendall_capacity_screen.py`;
`results/calibration/FINDING-neiso73-kendall-capacity-basis-2026-07-31.md`).
CAMPD `grossLoad` on this CHP unit is not gross electrical MW. Five
independent blocks: (E1) max gross 317–323 MW every year 2018–2025 exceeds
the **294.9 MW summed nameplate of every generator ever installed** at 1595
(incl. the retired 1949/1951 steam gens); (E2) implied gross HR
6.36–6.59 mmBtu/MWh (53–54 % HHV) is thermodynamically impossible for a
2002 7FA + 1958 ST, while the 923-net basis reads 9.31–10.07 — right for the
vintage; (E3) 923-net/CAMPD-gross flat at 0.654–0.687 across 96 months × 8
years spanning the 2018 unit-1/2 retirement — a fixed basis transformation,
not station use; (E4) monthly 923 net saturates the 860 winter rating
(209.3 vs 210.3 MW, Dec-2023, 99.5 %); (E5) EIA-860 vintages 2019–2024
identical, no uprate ever filed. Closure: mean gross/net 1.483 ≈ neiso-71's
saturated `steam_level_cf` 1.461 — the statistic was measuring the basis
ratio, not a steam obligation. neiso-71's "broken denominator (nameplate)"
diagnosis corrects to "contaminated numerator (CAMPD gross)". **The EIA-860
basis is correct — no model change; running the chartered A/B (raising pmax)
would have injected capacity two EIA sources refute** (rule 14 in reverse).
The miso-95 `nameplate_mw` orphan is narrowed for this plant, not reopened;
no tranche re-derivation touched.

**Floor-lane consequence (successor, own prereg required):** the neiso-71
DO-NOT-REDO is discharged. Kendall measures a genuine flat steam host on the
NET basis (loading-when-on 184.1/197.4/186.5 MW = 89.4/95.8/90.5 % of pmax,
on-frequency 94.5/91.3/94.0 %) — neiso-71's "no obligation" claim now stands
only for the non-Kendall cogens. Any identification touching 1595 must
de-base or avoid the CAMPD gross channel (contaminates both `steam_level_cf`
and heat rates, ~32 % low); the over-closing hazard (~1.6–1.7 TWh floor
effect vs 0.34–0.68 TWh shortfall) must be declared pre-solve.

**Governance.** Zero parameters; no `ScenarioConfig` field (no matrix row
owed). Matrix: `measured_chp_heat_rates` NEISO cell stays `O` — note + ev
updated, NEISO header re-checked (stale `gates` keeper text refreshed to
neiso-72), §5.6 item 6 stamped. Probe read 2018–2022 raw files no-LP
(rule 22 posture); locked test SPENT, untouched. Levers B (PS cycling
depth) and C (930-hourly 2022 extract rebuild) not taken — both queued.

**Open / next.** (1) **Storage-side PS cycling depth** (measured 1.932 vs
endogenous 0.497 TWh, 2025) — dispatch-adder/AS-value lane, never a hydro
patch. (2) **CC_CHP host-steam floor, NET-basis identification** — now
unblocked, own prereg with the over-closing hazard stated. (3) Lever C:
rebuild `data/raw/eia-930-hourly/{MISO,CISO}` 2022 extracts (session-logged
owner OK). (4) §5.6 items 1/2 still need their own charter; item 5 pending
owner decision. (5) Bench hydro 2024 re-base (scorer-side, flag to owner).

Next shorthand: **neiso-74.**

---

## neiso-74 — 2026-08-01 — PS under-cycling is a PRICE-SHAPE defect: the storage lever is REFUSED at the screen, no LP spent; keeper unchanged

**Lever:** handoff Lever A / §5.6 item 8 (the neiso-72 named successor) —
storage-side PS cycling depth. New matrix row `pumped_storage_cycling_depth`,
NEISO `G` (PJM `G` on its own prior record; the other four stay `U`/`.`, rule 25).
Keeper unchanged at `2026-07-31-neiso-72-hy-window`.

**The premise inverts.** The handoff read the post-split `NG: PS` column as ~4×
under-cycling (measured **1.932 TWh** in 2025 vs the keeper's endogenous
**0.497**) and asked for a storage-side identification. A perfect-foresight
price-taker LP carrying the model's **OWN** physics (1,865.0 MW,
`PUMPED_STORAGE_DURATION_HOURS` 10.0 h → 18.65 GWh, `PUMPED_STORAGE_RTE` 0.80,
cyclic SOC, the rule-9 ε; CSC → HiGHS) discharges **4.301 TWh on measured DA**
and **4.691 TWh on RT** — **2.2× the actual**, not 4× below it. The same LP on
the model's own duals returns **0.370 / 0.339 / 0.612 TWh**, bracketing the
keeper's **0.400 / 0.363 / 0.497**. So the storage block is already optimal for
the price signal it is shown, and **the constrained object is the price shape**
(rule 1 `[R-STRUCT]`: a storage knob here would size a parameter to an upstream
residual).

**The real defect, sized.** Level RIGHT (**+3.9 / +5.0 / +2.8 %** vs DA) and
phase RIGHT (hour-of-day peak **h17** in the model and in DA alike; trough h2).
Amplitude **24–30 % of measured**: mean daily spread **$8.11 / $7.41 / $14.62**
vs DA **$33.85 / $35.29 / $58.27**; daily MAX **−26.2 / −25.3 / −26.2 %**; daily
MIN **+40.8 / +40.0 / +32.6 %**; days clearing the 1.25× RTE hurdle **45 / 43 /
86** of 365 against DA's **364 / 365 / 365**. Attribution: `CC_REGULAR` absorbs
**2,045 MW** (49.7 %) of the **4,117 MW** diurnal demand swing while
`CT_PEAKER` (+209 MW) and `oil` (+99 MW) are **already online at the overnight
trough** — the same offer band is marginal at h02 and h17.

**Measured-input notes.** `NG: PS` is strictly non-negative (5,682 h > +1 MW,
**0 h** < −1 MW), i.e. gross discharge with pumping booked to Demand —
confirming neiso-72's read. The real duty is a wide price-following
afternoon–evening block (online 0.11 of h00–04 rising to 1.00 of h18–23; mean
11 MW at h02 → 728 MW at h18), phase-aligned with the DA curve — not the flat
reserve block an AS story would need. 2024 coverage is 0.148 (post-seam only)
and is not a full-year observation.

**Reported against interest.** (a) The handoff's own premise is inverted, above.
(b) A price-shape fix must **not** be graded on "does PS reach 1.932 TWh": the
real fleet realizes only **45 %** (1.932 / 4.301) of the DA perfect-foresight
optimum, so correcting the amplitude without also representing imperfect
foresight / min-run / head and reservoir limits would push model PS *past* the
actual. (c) **No load-bearing criterion sees this defect** — C3a is a level test
(PASS) and **C3b is a MONTHLY load-weighted price NRMSE**
(`calibration_verdict.py::score_price_shape`), structurally blind to
hour-of-day, while C7/D-1 is SKIPPED for NEISO. Whether the rubric should carry
a diurnal-amplitude criterion is an **owner call** — flagged, not acted on.
(d) **Handoff Lever C is already done**: `data/raw/eia-930-hourly/{MISO,CISO}
hourly.parquet` carry **8,760 rows for 2022 at 100 % column coverage** at this
HEAD (commit `5cd9374`, 2026-07-31), so the miso-110 §4.3 window mismatch is
closed and there was nothing to intake.

**Governance.** Years 2023–2025 only; **no LP solved, no bundle, no dashboard
registration** (rule 15 governs bundles and there is none — the neiso-71 /
neiso-73 disposition). Holdout spend freeze ACTIVE, NEISO locked test SPENT and
untouched; the 2022 row-count census in (d) is an on-disk loader-resolvability
check, permitted no-LP validation under rule 20 `[R-HOLDOUT]`. Matrix row +
`ev` added and the NEISO header re-stamped (rule 28b/c);
`check_mechanism_matrix.py --base origin/main` integrity **OK** (the one warning
is pre-existing CAISO keeper-stamp drift, another lane's).

**DO-NOT-REDO.** No storage-side PS lever at NEISO — dispatch adder, RTE,
duration, or AS value — until the diurnal amplitude defect closes. Evidence:
`results/calibration/FINDING-neiso74-ps-cycling-price-shape-2026-08-01.md`;
probe `scripts/probes/_neiso74_ps_cycling_screen.py`.

**Open / next.** (1) **The diurnal price-amplitude lane** — now NEISO's sized,
measured frontier; the identification class is §5.6 item 1 (DA-bid offer
formation / DA depth; `data/raw/NEISO-AS/da-energy-offers/` currently holds only
a README), which still needs its own owner charter. (2) §5.6 item 2
(import-side scarcity) unchanged, charter required. (3) Item 5 (STEP 3
layup-vs-outage seam) still pending owner decision. (4) Bench hydro 2024 re-base
(scorer-side) unchanged. (5) Rubric question in (c) above, for the owner.

Next shorthand: **neiso-75.**

### 2026-08-01 — xiso-1 answers neiso-74's open question: the amplitude defect is SYSTEMIC (cross-ISO audit, no LP, NEISO unchanged)

neiso-74 asked whether NEISO's 24–30 % diurnal price amplitude was
NEISO-specific. **It is not.** The xiso-1 cross-ISO audit measured all six ISOs
in one construction (keeper `hourly/` sidecars vs the committed hub DA/RT; zero
LP) and every one of the **36** ISO × year × benchmark cells compresses with the
same signature — daily MAX under-priced 36/36, daily MIN over-priced 36/36,
amplitude 19.9–92.2 % of measured, level right to 7.1 % and phase right in 34/36
rows. **NEISO is the most compressed of the six** (27.1 / 23.6 / 29.9 % vs DA);
the audit reproduced neiso-74's NEISO numbers exactly on its swapped loader.
Two consequences for this lane: the neiso-74 **DO-NOT-REDO on storage-side PS
levers stands unchanged**, and the rubric question in neiso-74 (c) is re-filed
as a cross-ISO owner call — no criterion sees hour-of-day amplitude at *any*
ISO, and PJM's keeper is fully `CALIBRATED` at ~34 %. **§5.6 item 1 still needs
its own owner charter; this audit grants none.**
`results/calibration/FINDING-xiso1-diurnal-price-amplitude-is-systemic-2026-08-01.md`;
full entry in `docs/calibration-log/governance.md` (2026-08-01).

Next shorthand: **neiso-75** (unchanged).

## 2026-08-02 — cross-ISO audit touching NEISO (caiso-154): the caiso-153 OLS-attenuation defect is NOT LIVE in NEISO — but its signature is DATA-REAL counterfactually, and one NEW tail-sensitivity exposure on the Limb-B surface is FILED (unarmed; charter-gated)

No-LP input-standing audit, logged in full in `docs/calibration-log/caiso.md`
(caiso-154) and `results/calibration/FINDING-caiso154-xiso-ols-attenuation-not-live-2026-08-02.md`.
NEISO outcomes: (1) `derive_neiso_offer_surface.py` contains no regression —
the caiso-153 family is structurally absent, and
`neiso_offer_surface_conditional` is off in the keeper (neiso-58 dormancy
stands); (2) the committed artifact reproduces to 0.023 % from a fully
refetched corpus at IDENTICAL coverage (353/352/353 days; the 38 absent days
re-error on retry — the documented endpoint gaps); (3) counterfactually, the
caiso-153 attenuation IS data-real on NEISO's corpus (Algonquin max/median
13.0×): OLS slope p50 7.4–8.1 vs TS 9.4–10.2, OLS |L| ~2× TRIM's, and the
630 MW physics-fast-start pool splits 303/327 under OLS where TS puts all of
it ≥8.5 — had NEISO been identified the CAISO way, the misbucketing would
have fired; but every OLS body cell stays ADMISSIBLE ($15.2–15.7 vs $20), so
NOT LIVE on the family's own bar; (4) **NEW FILED EXPOSURE (unowned):** the
tight-bin q0.7/q0.9 rungs of `neiso_offer_surface_condbinned.json` are
levered **+10.1..+13.1 %** by the 34 Algonquin fuel-tail days (Feb-2023
arctic week + the Dec-2025 weekly-anchor $25.00 ffill plateau — one Wednesday
print held 28 days, containing the real 2025-12-08 DA>$300 event): on spike
days, oil-parity/capped offers divide to LOW gas multipliers, so the measured
"fast-start wall" is biased LOW — the ratio analogue of caiso-153
attenuation. FILE-AND-STOP per the pre-registration: the artifact is armed in
no keeper, no number moves anywhere, and any action belongs to the
oil-parity/import/DA-bid charter class the frontier note (§5.6 item 1)
already requires — with the added weight that half the excluded mass is
fuel-series granularity (the weekly-anchor ffill), which any successor must
weigh before reading the 13 % as pure conduct signal.
`measured_offer_surface` NEISO stays `I`; keeper
`2026-07-31-neiso-72-hy-window` untouched; nothing registered.

Next shorthand: **neiso-75** (unchanged).

---

## neiso-75 — 2026-08-02 — the C3c FRONTIER CHARTER: the miss decomposes (systemic amplitude owns the 2025 gate; 2023 is measured-unreachable and routed to the owner); ONE lever chartered with kill rules; NO LP spent, keeper unchanged

**Session type:** charter (matrix §5.6 frontier discipline — "charter required
before any lever"). **No solve, no bundle, no registration.** Keeper unchanged
at `2026-07-31-neiso-72-hy-window`. Deliverable:
`results/calibration/CHARTER-neiso75-c3c-frontier-2026-08-02.md`; decomposition
probe `scripts/probes/_neiso75_c3c_decomposition.py` (imports the xiso-1
loaders — same construction, new statistic) with record
`PROBE-neiso75-c3c-decomposition-2026-08-02.txt`.

**(a) The decomposition.** Each of the 43 missed RT>$300 hours is split into
daily level + within-day deviation and tested against three counterfactuals:
CF-A "gain restored" (the model's own deviation scaled by the year's measured
hod-range ratio — the *systemic-defect* counterfactual), CF-B "shape graft"
(the actual's deviation on the model's day level — the upper bound of every
within-day mechanism), CF-C "level graft" (the actual's day level with the
model's deviation). Loader check reproduces xiso-1's NEISO row exactly.
Results: **CF-A closes 13/43 — all summer, 10 of 20 in 2025, zero winter hours
in any year** (median needed within-day gain 6.8×/32.8×/20.8× vs the systemic
2.9–4.4×). Full-8760 CF-A counts: 14/1/25 — **2025 lands at 25 h inside
[10, 40] with every crossing on the five real event days** (Jun-23/24/25,
Jul-28/29), while 2023's nominal 14 is a mis-timed tail (0 crossings on the
Feb-4 arctic-blast block; over-prints Sep-5..7 — the caiso-144 hazard shape).
The winter block (18 h) splits: 2023 is JOINT level+shape (Feb-4 day level:
model $195 / DA $227 / RT $275; even CF-B closes only 3/10 and CF-C 0/10);
2025's winter days carry the RIGHT day level (Jan-17 model $206 vs RT $196)
and miss only RT morning transients. **The decisive ceiling: the real DA — the
full real book — cleared ≥$300 in 5/5/12 h vs gates ≥8 / ≤18 / ≥10, so the
2023 gate is unreachable by ANY DA-type formation**; 36/43 tail hours are
RT-only (the wedge rubric v2.7 itself classes out of representation). 2024
passes small-count and needs nothing.

**(b) Levers enumerated** (charter §3): L1 DA-book diurnal formation
(`da_virtual_bids` **U→O**, recommended); L2 import-side scarcity (bounded, NOT
chartered — owner fidelity option; `priced_interchange` stays U); L3
declared-window OP-4/M/LCC-2 tiers (`maxgen_emergency_tier_pricing` U — no
registry on disk + rule-19 tension with the armed co-opt; owner option); L4
Limb-A promotion (standing owner decision, closes 1/20); L5 storage-side
(**blocked, xiso-1 standing order**); L6 Limb-B re-arm (`measured_offer_surface`
I stands; charter draws the boundary — the new identification is within-day
movement of the *body* band, never a re-conditioning of the tail rungs); L7
winter fuel-security family (exhausted on record, and §2 shows its target is
majority out-of-representation); L8 tail-tuned adders (forbidden).

**(c) The ONE lever, pre-registered** (charter §4): item 1, supply-conduct
limb first on the on-disk `hbdayaheadenergyoffer` corpus, DA-depth limb behind
its own existence check. Kills: K1 within-day movement ≥ $5/$5/$8 per year
(≈25 % of the measured hod-range gaps $18.93/$22.14/$31.17); K2 conditioning
on hour×net-load×month only, never price; K3 nyiso-94 existence + miso-105
λ0-attractor (≤$2 crossing-price reproduction AND ≥30 % displacement share
kills); K4 caiso-154 fuel-tail exclusion (>15 % relative = fuel granularity);
K5 2025 event-day coverage. **This charter authorizes Phase-0 (measurement,
no LP) ONLY; a solve arm needs its own prereg carrying gates G1–G5**
(amplitude; C3c-2025 count AND placement ≥ half on event days; C3a/C3b/C1
neutrality; ±8 % level band; C3b-flip hard kill; LOYO; no storage co-lever; PS
throughput reported, never graded).

**Reported against interest.** (1) The keeper attestation's 2024 C3c
event-day names are one calendar day early (Jun-17→Jun-18, "Jul-7 Sun"→Jul-8
Mon, Jul-31→Aug-1, Dec-2→Dec-3) — a leap-year dating slip in the ledger prose,
verified against the raw SMD workbook (RT max $2,112.77 = 2024-08-01 HE19);
counts, hours, parquets and scoring are unaffected. To be corrected at the
next attestation regeneration, not edited in place. (2) CF-A's 2023 count
nominally "passes" the gate — the charter rejects it anyway on placement,
against the naive reading of our own counterfactual. (3) The rubric
diurnal-amplitude criterion (neiso-74/xiso-1 owner call) is SURFACED with new
sizing — C3c proxies the amplitude defect in exactly one ISO-year (NEISO-2025)
— and NOT decided; no scorer changed.

**Governance.** Years 2023–2025 only; holdout freeze ACTIVE; NEISO locked test
SPENT and untouched; nothing read outside the training window (rule 22). The
probe feeds nothing back into any solve (rule 13 not engaged). Matrix duties
(rule 28b): `da_virtual_bids` NEISO U→O + ev; `diurnal_price_amplitude` and
`measured_offer_surface` NEISO notes updated (boundary drawn, I stamp stands);
NEISO header re-check stamp; §5.6 header + items 1/2 stamped.
`check_mechanism_matrix.py --base origin/main` run pre-push. No dashboard
registration (rule 15 binds bundles; none exists).

**Open / next.** (1) **Owner:** the §5 routing for C3c-2023 (accept ledgered /
winter-fidelity lane / representation change) + the L1 execution green-light
(Phase-0 is authorized; a veto re-stamps O→U with the charter as standing
prereg) + the standing rubric owner call. (2) **Successor session (on owner
green-light): L1 Phase-0** — run the K1–K5 measurements, stamp the surviving
limb, and (only on survival) write the Phase-1 prereg with G1–G5 numeric bars.
(3) Items 2/5 and the Limb-A promotion decision unchanged.

Next shorthand: **neiso-76.**

---

## neiso-76 — 2026-08-02 — Phase-0 RUN: the chartered DA-bid lever is REFUTED ON BOTH LIMBS with the sign against its own theory; NEISO's amplitude is an over-priced TROUGH, not NYISO's missing reserve; NO LP spent, keeper unchanged

**Session type:** the neiso-75 charter's Phase-0 (§4), measurement only. **No
solve, no bundle, no registration, no `ScenarioConfig` change.** Keeper
unchanged at `2026-07-31-neiso-72-hy-window`. Deliverable:
`results/calibration/FINDING-neiso76-dabid-phase0-2026-08-02.md`; probes
`scripts/probes/_neiso76_dabid_phase0.py`, `_neiso76_demand_limb.py`,
`_neiso76_reserve_content.py` with records `PROBE-neiso76-dabid-phase0-`,
`-demand-limb-`, `-reserve-content-2026-08-02.txt`.

**(a) The chartered Phase-0, run exactly as pre-registered.** Corpus
regenerated with the committed fetcher: **1,063 non-empty day files
(359 / 351 / 353)**, 7.40 M offer rows, non-fast-start band 360 assets.

* **K1 FIRES in all three years.** The frozen statistic — per (asset, day) the
  capacity-weighted mean submitted incremental-segment price over h16–19 minus
  h01–04, PAIRED, capacity-weighted over the band — is **−1.926 / −1.840 /
  −2.274 $/MWh** against bars of **+5 / +5 / +8**. The book is offered
  **cheaper at the peak**. **72.8–73.9 %** of 227,033 paired asset-days are
  bit-flat (p25–p90 exactly $0.00); the band's own hour-of-day offer profile
  spans **$2.20 / $2.51 / $3.67** and *troughs* at HE19–20 against DA hod
  ranges of $25.96 / $28.96 / $44.47. Controls all agree: unpaired identical to
  3 dp, ECONOMIC-only −1.732 / −1.701 / −2.733, the alternate window reading
  −1.645 / −1.695 / −2.040, no single asset worth more than −$0.40 of the
  aggregate. The **fast-start band moves −13.7 to −15.9** — same sign, larger.
* **K2** cannot rescue it: the price-free conditioned surface (net-load bins ×
  month) is negative in 11 of 12 year-bin cells and the best admissible cell
  per year is **−0.391 / −1.378 / −1.487**.
* **K4 fires on 2025** (+24.1 % excluding the 34 Algonquin ≥ $25.00 fuel-tail
  days; 2023 +10.7 %, 2024 +0.0 %) — but toward zero, so it changes no verdict
  and confirms the filed caiso-154 exposure's direction on a fresh statistic.
* **K5 passes**: all five 2025 event days present in the corpus and in the band.
* **K3(i) PASSES — the nyiso-94 blocker does NOT bind at NEISO.**
  `hbdayaheaddemandbid` is a **submitted** priced book (FIXED / PRICE / INC /
  DEC, ≤ 50 (price, MW) segments, 165–219 GWh/day of priced segment MW, all
  four types in every non-empty sampled day). NEISO is the **third** ISO with a
  submitted curve. **K3(ii) does NOT fire**: λ0 median error **$5.29** (bar
  ≤ $2, 27.3 % of 898 hours inside it) and displacement share **12.7 %** median
  (bar ≥ 30 %) — the limb is admissible, not an attractor. It dies on
  **materiality**: net virtual is **−0.41 / −0.25 / −0.24 GW at the peak** vs
  **+0.13 / +0.02 / +0.07** at the trough (a midday virtual-*supply*
  convergence play, −1.34 GW at HE13), so arming it faithfully **subtracts
  $2.76 / $1.37 / $1.60** of diurnal spread; physical demand is 67.6 %
  price-insensitive and the elastic remainder shaves peaks. **Ladder semantics
  identified, not assumed** (the file has no cleared-MW column, so the readings
  were crossed against the published hourly DA cleared demand): cumulative
  brackets it in **0 of 900** hours, incremental-with-INC-netted in **898**.

**(b) NEISO's reserve-content decomposition — it is NOT NYISO's** (rule 25 in
both directions). New gitignored intake `data/raw/NEISO-AS/reserve-prices/`
(RT `finalhourlyreserveprice` ROS TMSR; DA `daasreservedata`), validation-only,
regenerated by the committed probe. The keeper's co-opt dual is **$0.00 in all
26,280 train hours** as attested — but unlike NYISO the *market's* price is
also near-zero: RT TMSR **median $0.00**, p90 $1.21, **> $1 in only
23.4 / 23.4 / 20.7 %** of peak-window hours (NYISO DA spin: **100 %**), and
$200-censoring removes 18–41 % of the peak-window mean (NYISO: ≤ 13 %) — a
scarcity phenomenon, not an everyday one. Reserve owns **33 / 43 / 32 %** of
the missing RT swing (NYISO 97–131 %); DA passthrough slope is **+0.15 / +0.46
/ +0.09** against RT's +0.96 / +1.99 / +1.29. **Structural, measured not
assumed: ISO-NE cleared NO day-ahead reserve product before DASI go-live
2025-03-01** (the DAAS report is header-only for 2025-01/02; first data row
2025-03-01), so 2023–24's DA gap is **100 % energy-side by market design**.
**Energy-basis restatement: the model's PEAK is right to ±$3 and its overnight
TROUGH is $7.6–9.9 TOO DEAR** (energy-only swing 43 / 41 / 49 % of the
reserve-stripped actual). NYISO's defect was missing reserve formation with the
energy side over-priced at *both* ends; NEISO's is an over-priced trough.

**(c) The closure, and what replaces the lane.** No solve arm pre-registered —
the charter's Phase-1 gates G1–G5 are never reached because neither limb
produced a mechanism to gate. The measurement instead names ONE new route, and
it is a **different matrix family** needing **its own charter** (none opened):
the **stack-traversal identification**. The real book crossed at the real
hourly quantity traverses **$17.03 / $21.11 / $24.06** of hod range
(66 / 73 / 54 % of DA), correctly phased at HE20–21, against the keeper's
**$7.03 / $6.82 / $13.30** — while every **constant-quantity** read of the same
book is INVERTED (marginal price at fixed depth peaks overnight, troughs at
HE19). The model's within-day offer *surface* is not the binding constraint;
its stack shape in the **quantity** dimension is the live suspect (a rule-14
`[R-ACCURATE]` comparison against a measured book, not a residual fit).

**Reported against interest.** (1) The charter's theory of change is not merely
unsupported — the measured sign is **opposite** on both limbs; recorded as a
refutation of the lane this session was sent to advance. (2) **K3(ii) did not
fire**; the demand limb passes its own pre-registered kill and is closed on
materiality, a weaker basis, on a 39-day sample rather than the full corpus.
(3) §B3's post-DASI DA reserve differential (117.5 % of that window's missing
DA swing — the largest reserve share measured anywhere here) is quoted **with
its own over-strip disproof**: a naive full strip flips the model to 150.9 % of
the stripped actual, so DASI prices are not an additive LMP component and the
passthrough slope +0.60 is the identified number. (4) The traversal read is
**depth-sensitive** — a flat 3 GW import allowance halves it to 36 / 34 / 31 %,
only 4–7 pp above the keeper — so the direction survives and the magnitude does
not; the crossing-quantity reconciliation is the successor's first task.
(5) The probe reproduces xiso-1's NEISO amplitude row (27.1 / 23.6 / 29.9 % of
DA) exactly from an independent path — a loader check that passed.

**Governance.** Years 2023–2025 only; holdout spend freeze ACTIVE; NEISO's
locked test SPENT and untouched; nothing outside the training window read
(rule 22). No LP, no keeper change, no bundle, no dashboard registration
(rule 15 binds bundles; there is none). Every measured price is a validation
target and enters no solve, no loader and no derive (rule 13). Two new raw
sources documented + gitignored with committed regenerators
(`NEISO-AS/reserve-prices/`, `NEISO-AS/da-demand-bids/`). Matrix duties
(rule 28b): `da_virtual_bids` NEISO **`O` → `R`** (tested & rejected, no solve
spent — distinct from MISO's/NYISO's ex-ante `G`); `diurnal_price_amplitude`
NEISO **`U` → `O`** (a lever was tested and refuted **and** a new unadjudicated
route is named — hence `O`, not the PJM/MISO/NYISO `G`);
`measured_offer_surface` stays `I` and `energy_reserve_coopt` stays `K`, both
notes extended; NEISO header re-stamped; §5.6 header + item 1 stamped SPENT and
new items 5b/5c added. `check_mechanism_matrix.py --base origin/main`
integrity **OK**. Environment note: `regenerate_clean.py` failed 1 of 50
datatypes (`partial-outages`, exit −6) — not read by anything in this session.

**Open / next.** (1) **Owner:** the charter §5 routing for C3c-2023 is
unchanged and now harder-edged (the real DA book is *flatter* than the model's,
which strengthens §2.4); C3c-2025 keeps its neiso-75 sizing and loses its
route; the **stack-traversal charter** is requested; the standing rubric
amplitude-criterion call now has a **second ISO's decomposition that disagrees
with NYISO's**. (2) §5.6 item 2 (import-side scarcity) and item 5 (STEP 3 seam)
unchanged, charters required. (3) Limb-A promotion decision unchanged.

**DO-NOT-REDO.** Do not re-measure the supply-conduct limb (flat, negative,
73 % bit-flat; re-conditioning it on anything price-shaped is barred by K2) and
do not re-open the DA-depth limb without new evidence overturning the net-short
measurement. The neiso-74 storage DO-NOT-REDO and the xiso-1 standing order are
untouched.

## neiso-77 — 2026-08-03 (via caiso-159) — **THE CT HEAT-RATE METER SCREEN IS PROMOTED TO KEEPER** (`2026-08-03-neiso-caiso156-meter-screen`), score-identical to neiso-72 on every criterion, D-gate flag and D-row verdict; `complete` marker re-keyed with re-verification

**Keeper NEISO -> `2026-08-03-neiso-caiso156-meter-screen`** (bundle
`neiso_c156_meter_screen_B`). Determination CALIBRATED-WITH-CAVEATS, verified
IDENTICAL to the neiso-72 incumbent — all 9 criteria (1 ledgered C3c caveat, C7
unscored-protective as since neiso-70, 0 FAILs), grade summary (8/7, ledgered 1),
C1 headline (all 12/12 free 8/8), all six D-gate pass flags and all 54 D-row
verdicts. The neiso-72 hydro-window mechanism and the C3c frontier declaration
are carried forward unchanged; no C3c evidence moved in either direction and no
new caveat slot is spent.

**NINE ScenarioConfig fields differ from the incumbent and ALL NINE ARE SCHEMA
DRIFT, not a config change** (`caiso_firm_import_selfsched_clip`,
`coal_prb_committed_split`, `crossover_solve_year_weather`,
`demand_growth_vintage`, `ercot_dam_availability_gas_event_cap`,
`gas_offer_margin_anchor_by_zone`, `gas_offer_margin_zonal_anchor`,
`miso_coal_night_floor`, `pjm_rggi_allowance_pricing`): each was ADDED to
ScenarioConfig after the neiso-72 solve and is recorded at its declared default
— seven False, two None — the incumbent simply predates the field. The arm
declares 671 keys against the incumbent's 662, and there are ZERO value
differences on the 662 shared keys.

CORRECTED ON THE RECORD: this entry first said SEVEN. The count was wrong
because the diff was wrong — `a.get(k) != b.get(k)` collapses "key absent" and
"key present with value None", hiding the two None-valued fields. Caught by the
NEISO keeper auditor, not by the promoting session. Substance unaffected (all
nine are drift; still zero value diffs), but the method is now
`config_drift()` in scripts/gen_caiso159_attestation.py: sentinel-based and
absence-aware, it COMPUTES the count and field list into the attestation
(`config_drift_vs_incumbent`) rather than taking them from prose, and RAISES on
any shared-key value difference. Against the NYISO pair it isolates exactly
`nyiso_li_locational_reserve` — the guard would have stopped that promotion by
itself.

**What changed:** the CONTENT of the shared CT heat-rate artifact (caiso-158's
hour-grain band screen). Cap-weighted applied rate 9.6291 -> 9.8006 MMBtu/MWh
net over 7/7 plants; the committed artifact's md5 `293c6f6c52be...` matches the
K1 arm-B pin recorded at solve time. P1 CT_PEAKER energy 0.3088->0.2877 /
0.8433->0.7566 / 1.7174->1.6163 TWh, up to 150.4 MW in one class-hour and 2,566
of 8,760 hours changed in 2025 — live, and score-neutral. Load-weighted lambda
+0.045/+0.055/+0.083 % of level, far inside the 1.0 pp trigger.

**K6 — the correction is not driven by drops.** NEISO is the tightest of the six
ISOs here because it drops one unit (63559); recomputing the applied-map delta
with that unit RETAINED at its screened rate still gives +0.1319 against the
shipped +0.1715 — 23.1 % divergence against a pre-committed 25 % bar, same sign.
Meter hygiene, not selection.

**Rule 22 D-5(b):** NEISO holds a `complete` (validation-tier) marker, so the
entry is re-keyed to this run with a fresh determination re-verification from
committed artifacts (no solve). `locked_test_scored_on`
(`2026-07-07-neiso53-winter-fuelsec-coldsnap`) is deliberately NOT re-keyed —
that SPENT one-shot stands as taken. `keeper_at_declaration` preserved. The
holdout spend freeze is ACTIVE and unspent; 2023-2025 only (rule 16).

Zero free parameters (DOF ledger unchanged at 12 entries / 5 residual, asserted
by the generator rather than trusted). Promoted on rule 14 [R-ACCURATE], not on
a fit claim — the scorecard did not move in either direction.
Evidence: `results/calibration/FINDING-caiso159-ct-heat-rate-promotion-2026-08-03.md`.

Next shorthand: **neiso-78.**

---

## neiso-78 — 2026-08-03 — RULE-28(c) COLUMN CLOSED (10 absent / 8 armed-with-no-cell → 0), and the census surfaced a live defect: `neiso_oil_burn_budget` is armed on every NEISO bundle ever registered and is UNREACHABLE on all of them

**Session type:** governance/registry census, **no LP, no solve, no bundle, no
dashboard registration, no `ScenarioConfig` change, no default altered, no
derive re-run.** Keeper unchanged at `2026-08-03-neiso-caiso156-meter-screen`.
Deliverable:
`results/calibration/FINDING-neiso78-matrix-census-close-2026-08-03.md`; probe
`scripts/probes/_neiso78_oil_budget_reachability.py` with records
`PROBE-neiso78-matrix-gap-census-` and
`PROBE-neiso78-oil-budget-reachability-2026-08-03.txt`.

**Shorthand note.** The session prompt was issued as *neiso-77*; that shorthand
had already been consumed by caiso-159's cross-lane promotion entry above, so
this work is filed as **neiso-78** per this log's own ledger. (The prompt's
keeper id was stale for the same reason — see below.)

**(0) Fork.** The prompt's Fork A (§5.6 item 5b, the neiso-76 stack-traversal
charter) **requires an owner green-light and none was in hand**, so under §5.6
frontier discipline it stays unopened. Fork B directs the session to the
highest-value **non-owner-gated** box. **ERCOT was checked first and does not
offer one** — it is the only NOT-YET ISO, but item 9 needs owner authorization
(uncharered structural LP change), item 8's intake is explicitly three-part
owner-authorized, and item 7's intake has **no source on disk** (`data/raw`
carries nodal curtailment corpora for CAISO/MISO/NYISO and nothing nodal for
ERCOT). §5.7's `matrix_gap_census` row records that the five non-NYISO columns
"are their own lanes' work (rule 25/28(d))"; NEISO's share was 10, and rule
28(c) is explicit that a mechanism missing from the matrix "is an unregistered
tuning channel in spirit (rule 24)".

**(a) The close.** `mechanism_matrix_gap_sweep.py --iso NEISO`: absent
**10 → 0**, armed-with-no-cell **8 → 0**, prose-only 0, live-but-invisible
**1 → 0**. **NEISO is the third closed column** after NYISO (nyiso-114) and
ERCOT (ercot-156). All ten closed as **literal registrations on three existing
family rows' `def`s** — the nyiso-114 escape-hatch template — so **no row was
added, no cell verdict was flipped, and no `U` was minted** (rule 25 bars a
census from adjudicating, and none needed it: each owning row already carried
the right verdict). `gas_coldsnap_derate` (NEISO `K`) took the three NERC-
anchored derate sub-scalars; `winter_fuelsec_posture` (`K`) took the six
winter/oil fields; `dam_availability_rebasis` (`R`, neiso-62) took
`neiso_operable_capacity_availability`, whose `def` had carried the truncated
stem `neiso_operable` that no literal-match census can resolve. Ratchet
baseline regenerated **shrink-only** (exactly the ten); the full six-ISO sweep
confirms **no other column grew** (CAISO 0/5, ERCOT 0/14, MISO 11/17, NYISO
0/0, PJM 15/18). CI gates pass.

**(b) A fourth, CROSS-ISO gap found while closing them.** The shared,
solve-affecting `GATED CHANGE` flag `unit_partial_outage_windows` had **no
matrix mention at all**: its owning row `unit_outage_short_windows` named it
only as a bare parenthetical line number. Registered literally; NEISO cell `R`
(neiso-69) unchanged. **Every line number encountered in the four `def`s was
stale** — `:2138`→`:2878`, `:2286`→`:3026`, `:7771`/`:7796`→`:9419`/`:9444`.

**(c) THE LIVE DEFECT.** Two of the eight armed-with-no-cell fields are bool
gates the keeper arms **away from a `False` default** —
`neiso_winter_fuel_inventory` and `neiso_oil_burn_budget` — the nyiso-112
live-but-invisible shape. Both feed the **same** LP builder
(`model/lp/rows.py::_build_oil_budget_rows`) via the same `oil_*` kwargs, so
rule 19 `[R-ONE-MECH]` asks whether the keeper **double-counts** the winter
oil-burn constraint. **It does not, and the reconciliation is already in the
wiring:** `scripts/run_calibration.py:4250` is a single `if`/`elif` whose `if`
gate is the successor and whose `elif` gate is the superseded limb — proven
**mechanically** (the probe parses with `ast` and asserts the two gates are the
test and the `orelse` test of *one* `If` node; two independent `if`s would
double-count), not read off the comment. Bundle census: **15/15** NEISO bundles
arm both, and the F923 limb is reachable in **0 of the 120** committed bundles
across all six ISOs. It is NEISO's backcast default
(`backcast_config.py:1549`), which is why it reads as armed, and it has
**never once built a row**.

**Reported against interest.** The field's own `scenarios.py` docstring calls
it "not a keeper path" — **false as written** against the current keeper, where
it is `True`. It is *unreachable*, not *unarmed*, and the distinction matters:
it would begin building rows the moment a bundle turned its successor off.

**(d) FILED NOT FIXED, routed to the owner.** `neiso_oil_burn_budget` is a
rule-26 `[R-DELETE]` candidate — armed-by-default *and* rule-13-inadmissible on
its own docstring's account (EIA-923 petroleum **receipts**, a measured
deliveries-to-tank outcome with no forward analogue). It joins nyiso-115's
`campd_facility_outages` as the **second rule-26 candidate** in the same
cross-lane queue and they should be decided together. Not done here because
deletion touches a **NEISO backcast default** — a solve-affecting recipe change
to 15 bundles' recorded configs — which is not a census's call. Second, smaller
filing: `check_mechanism_matrix.py` could assert that a `scenarios.py:N`
reference in a `def` resolves to a line actually defining a field; bare line
numbers rot silently and are invisible to the ratchet.

**(e) Keeper-id correction.** The prompt and §5.6's header both named
`2026-07-31-neiso-72-hy-window`. The shard designates
**`2026-08-03-neiso-caiso156-meter-screen`** (neiso-72 SUPERSEDED-NOT-RETRACTED
at caiso-159). §5.6's header and body line are corrected; every number in this
entry is read against the current keeper.

**Governance.** 2023–2025 only; **no year outside the training window was
read**. Holdout spend freeze untouched; NEISO's locked test remains SPENT and
untouched (rule 22). No mechanism adopted, demoted or re-scoped; no parameter
introduced or re-derived; the NEISO frontier declaration and the C3c owner
routing (CHARTER-neiso75 §5) are exactly where neiso-76 left them. **This
licenses nothing.**


---

## neiso-79 — 2026-08-03 — THE CROSSING QUANTITY IS RECONCILED: neiso-76 §D's 66/73/54 % traversal falls to 30/37/38 % once the real book is crossed at the real quantity — DIRECTION survives, MAGNITUDE does not; and ISO-NE publishes NO day-ahead cleared external series anywhere

**Session type:** measurement/intake prerequisite for matrix §5.6 item **5b**.
**NO LP, no solve, no bundle, no dashboard registration, no `ScenarioConfig`
change, no default altered, no derive re-run, no cell verdict stamped.**
Keeper unchanged at `2026-08-03-neiso-caiso156-meter-screen`. Deliverables:
`results/calibration/PREREG-neiso79-crossing-quantity-2026-08-03.md` (committed
BEFORE any statistic was computed),
`FINDING-neiso79-crossing-quantity-2026-08-03.md`, probe
`scripts/probes/_neiso79_crossing_quantity.py`, record
`PROBE-neiso79-crossing-quantity-2026-08-03.txt`.

**HARD STOP OBSERVED.** Item 5b needs an owner green-light and none was in
hand, so under §5.6 frontier discipline this session landed the prerequisite
and stopped. No lever, no arm, no G-gate on the magnitude.

**(a) THE REAL DATA GAP, ANSWERED: ISO-NE publishes no day-ahead CLEARED
external-transaction or net-interchange series, anywhere public.** Verified
against the full ISO Express Pricing / Grid / Load & Demand report trees and
the Web Services v1.1 endpoint list: every interchange report on the Grid tree
is real-time/actual (*Real-Time Actual Scheduled Interchange*, *External
Interface Metered Data*, and the 15- and 5-minute variants), Load & Demand's
only DA cleared quantity is *Hourly Day-Ahead Cleared Demand*, and Pricing's
only external report is the **submitted** book. The API adds
`/actualinterchange`, `/hourlybainterchange`, `/fiveminuteexternalflow` — all
actual — and `/hbimportexport`, the same submitted report. **EIA-930
interchange was NOT substituted** (actual net interchange is a different
quantity at a different grain from DA scheduled imports — the rule-14
`[R-ACCURATE]` grain-misalignment trap); `derive_neiso_import_tranches.py` is
untouched.

**(a′) The available input turned out to be BETTER than the missing one.** New
gitignored corpus `data/raw/NEISO-AS/da-import-export/` (README + committed
fetcher `scripts/data/fetch_neiso_da_import_export.py`; 1,090 day-files, 13
empty postings, 0 unpublished): the submitted DA import-offer/export-bid book,
`Direction` × `Transaction Type` (`DISPATCHABLE` priced / `FIXED`
self-scheduled) × price × MW. Imports enter ISO-NE's DA market **as priced
supply offers**, so crossing them jointly with the internal book clears import
depth **endogenously** — which **removes the free depth parameter entirely**
rather than re-assuming neiso-76's flat 3 GW. Ladder semantics identified from
the file (645 of 1,280 keys multi-row ⇒ incremental block widths), not assumed.

**(b) The construction, frozen in the prereg.** ISO-NE's DA balance makes the
internal book's crossing quantity `q*(λ) = Q_cleared_dem − Q_imp(λ) − Q_inc(λ)`
**price-dependent** — a fixed point, not a lookup — so the probe crosses the
**combined** supply book (internal offers + import offers + INC virtuals)
against the published cleared-demand line. The composition of that published
series was **identified, not assumed** (the miso-105 discipline): C1/C4
refuted in every year; **C2 and C3 are statistically indistinguishable** at
NEISO because cleared exports (~1–2 GW) and INC virtual supply (~1.3–1.9 GW)
nearly cancel. C2 wins 2023–24, C3 wins 2025 ⇒ **UNIDENTIFIED between them**,
both reported.

**(c) THE RESULT.** 864 operating days in all three books, 20,733 hours
(300 / 288 / 276 days — 2023 `OK`, 2024–25 `UNDER-SAMPLED` but above the
prereg's 200-day floor).

| year | corrected hod range | share of measured DA | n76 §D at demand | n76 at demand−3 GW | keeper |
|---|--:|--:|--:|--:|--:|
| 2023 | $7.71 (HE21) | **29.7 %** | 65.6 % | 36.4 % | 27.1 % |
| 2024 | $10.63 (HE19) | **36.7 %** | 72.9 % | 33.6 % | 23.5 % |
| 2025 | $16.78 (HE19) | **37.7 %** | 54.1 % | 30.9 % | 29.9 % |

**THE CONTROL IS WHAT MAKES THIS A STATEMENT ABOUT THE QUANTITY.** The same
probe, same 864 days, crossing the internal book alone at EIA-930 demand —
neiso-76 §D's own construction — gives **68.6 / 79.8 / 59.3 %**, at or **above**
their full-corpus anchors in every year, and **37.4 / 36.9 / 33.2 %** at
demand−3 GW against their 36.4 / 33.6 / 30.9 %. The sample is not depressing
the traversal; if anything it flatters it. The fall to 30 / 37 / 38 % is the
**crossing quantity and nothing else**. The measured DA import depth is
**~4–4.4 GW** plus 1.3–1.9 GW of INC — so §D was crossing the book ~4–5 GW too
deep, in a materially flatter part of the stack. **neiso-76's own 3 GW
sensitivity was the right instinct and the correct endogenous depth confirms
its pessimistic end.**

**Kill rules (pre-registered before the numbers existed).** **KQ1 does NOT
fire** (0/3 at-or-below keeper) — the traversal lane is **not refuted**; the
real book does traverse more than the model's. **KQ2 FIRES** (3/3 below 40 %)
— the corrected read is **DIRECTION-ONLY**, and the neiso-76 §D magnitude must
not be quoted as surviving. **KQ3 FIRES on 2025** ($11.12 vs the $10.00 bar;
2023 $7.86 and 2024 $8.33 clear it), so the three-year headline share is
**WITHHELD** per the prereg — honoured rather than reinterpreted. **KQ4 does
NOT fire**: removing the import book recovers **49.6 / 61.0 / 49.4 %**
(19.9 / 24.3 / 11.6 pp), i.e. the import reconciliation carries the bulk of the
correction and is the mechanical explanation of the whole finding.

**Reported against interest.** (i) The **MT variant was mine and is refuted**:
`Must Take Energy` averages ~4.6 GW/h and looked like a first-order omission,
but every unit-hour carrying it is `MUST_RUN` with a ladder already spanning
EcoMax (seg/EcoMax p25 1.00), so those MW are a **subset** — adding them would
double-count — and re-pricing them to the floor (the faithful reading)
**worsens** the identification in all three years. Disclosed post-hoc per KQ5,
reported both ways, changes no verdict. (ii) The crossing sits a median
**$7.8–11.0 BELOW** the posted DA; that is structural (a merit-order energy
crossing omits commitment cost, reserve co-optimization, congestion, losses)
and is reported as a bound on what the construction can explain, not tuned
away. A no-load-cost bound was built and then **discarded as undefendable**
rather than shipped. (iii) A DA reserve reservation — which would have
flattered this lane — was refused on neiso-76 §B3's **measurement** that ISO-NE
cleared no DA reserve product at all before DASI go-live 2025-03-01. (iv) The
corpus is 864 of 1,095 days because the ISO Express endpoint throttles a
sustained bulk pull; the fetch order was made **stratified** (`--stride`) so
every partial pull is seasonally unbiased, and the control above converts that
caveat into a measured statement.

**Owner routing — what this gives the item-5b decision.** The
quantity-dimension suspicion is **not refuted**, but the margin over the
keeper is **+2.6 / +13.2 / +7.8 pp**, not the 38–49 pp §D's headline implied. A
perfect stack-traversal lever would therefore recover **at most about a third
to a half** of NEISO's diurnal amplitude gap and **cannot close C3c-2025**
(which neiso-75 sized as the one gate the amplitude lane could close);
neiso-75 §2.4 already established it cannot close C3c-2023 at all. **The honest
recommendation this session can support: charter item 5b only if the target is
amplitude FIDELITY, not the C3c gate.** C3c-2023 stays routed to the owner
(CHARTER-neiso75 §5), untouched.

**DO-NOT-REDO.** Do not re-quote neiso-76 §D's 66/73/54 % — that read is now
measured to cross the book ~4–5 GW too deep and its magnitude is superseded.
Do not substitute EIA-930 interchange for DA scheduled imports. Do not
re-measure this reconciliation: the probe re-runs it from the committed
fetchers at zero LP cost.

**Governance.** 2023–2025 only; **no year outside the training window was
read**. NEISO's locked test remains SPENT and untouched; the holdout spend
freeze is ACTIVE and unspent (rule 22). Rule 13: every price is a validation
target and enters no solve. Rule 28: **no mechanism was tested, so no cell
verdict is stamped and no `U` is minted** — `da_virtual_bids` NEISO stays `R`
(neiso-76) and the tranche family is not stamped; §5.6 item 5b gains the
reconciliation result and stays **charter-requested, NOT opened**.
**This licenses nothing.**

---

## neiso-80 — the CHP dark-fuel scope gate lands; Stony Brook's steam part was never missing (2026-08-04)

**NO LP. NO SOLVE. NO RUN REGISTERED** (rule 15 `[R-DASHBOARD]`, stated
explicitly rather than left implied). **Keeper UNCHANGED** at
`2026-08-03-neiso-caiso156-meter-screen`. Both of NEISO's cross-ISO queue items
were adjudicated from committed EIA-860 / eGRID / CAMPD artifacts plus one
fleet-loader diff.

Prereg `results/calibration/PREREG-neiso80-chp-scope-gate-and-steam-part-2026-08-04.md`
(commit `e89d08b5`, pushed **before** any arm and before any adjudicating
statistic); finding
`results/calibration/FINDING-neiso80-chp-scope-gate-and-steam-part-2026-08-04.md`;
probe `scripts/probes/_neiso80_stonybrook_presence.py`; record
`_neiso80_stonybrook_presence.json`.

**Item 1 — the miso-122 dark-fuel scope gate, APPLIED at NEISO; the cell STAYS
`O`.** NEISO's `chp_power_only_heat_rates` artifact was the last of the three
dark-fuel-carrying ISOs still written pre-gate-3 (19 columns, no
`dark_fuel_share`); miso-122 re-derived only MISO's and nyiso-120 only NYISO's,
each handing NEISO's off with a number under rule 25. Re-derived at
`--vintage 2023`, all five pre-registered properties hold — **P1** the artifact
has exactly one caller and it is flag-gated; **P2** six frozen columns
bit-identical on all 40 rows, only `(1595, CC_CHP)`'s `heat_rate` moves and only
downward, flag census unchanged 22/12/5/1; **P3** reproduces to 4 dp
(`dark_fuel_share` 0.012142, **9.5584 → 9.4423**); **P4** `cems_vs_egrid_total`
1.0, in band; **P5** exactly one file changed. Measured on NEISO's own CAMPD the
share is **0.012142 / 0.009584 / 0.014798** across 2023/24/25 — the hand-off
series 1.21/0.96/1.48 % exactly — so the gate is a stable physical feature of the
plant, not a one-year artifact (2023 is the committed vintage and the only
applied one; no vintage mixing).

**The item is SCORE-INERT ON THE DESIGNATED KEEPER BY CONSTRUCTION, NOT BY
MEASUREMENT:** the keeper's `run_config` records
`measured_chp_heat_rates=false`, so the artifact is not read on its solve path
at all. No solve is owed and none could show otherwise. **Ceiling pre-declared,
then measured:** the gate walks the repriced seam +36.08 % → +35.31 % (CC_CHP
only, 3 rows / 378.2 MW: +36.72 % → +35.81 %) — **2.15 %, about one part in
forty-six, of the seam move that produced the neiso-70 `CC_CHP` overshoot.** It
cannot and does not flip the cell and was never offered as a route. Rule 23
`[R-FROZEN-DERIVE]` citation is the **miso-122 gate-3 scope change on measured
grounds**, never a residual; rule 14 `[R-ACCURATE]` governs in both directions.

**Item 2 — `cc_steam_part_capacity` NEISO `U` → `I`.** 6081 Stony Brook `CA1`,
96.0 MW `DFO`: **presence resolves `REPRESENTED`, not `MISSING`.** The
pre-registered **Q4 falsifier fires** —
`_map_fuel_type("Petroleum Liquids", "DFO", "CA")` returns **`oil`, not
`None`** — so the fuel map never drops the row and **`6081_CA1` is already in
the fleet at 96.0 MW**. Q3 passes (predicate matches: uc `CC1`, three `NG`/`CT`
siblings, all 1981), which is the miso-126 1004 Edwardsport pattern exactly: the
repair only ever *restores* a row the fuel map drops. **Inertness proven at the
loader grain, not inferred** (miso-126 §4's discipline mirrored): with
`CC_STEAM_PART_REPAIR_ISOS` patched to `{MISO, NEISO}` and the flag armed, the
NEISO fleet is **byte-identical** — 431 generators both sides, 0 added /
0 removed / 0 changed. **NEISO is NOT added to `CC_STEAM_PART_REPAIR_ISOS`.**
Q5/Q6 are not reached, both being downstream of a `MISSING` verdict that did not
occur.

**Why the TOTALS test could not decide it — a real limit of the miso-125/126
presence test, recorded rather than worked around.** Stony Brook carries
**10.9 MW** of rows a thermal fleet loader legitimately never loads (`5051S`
6.9 MW PV solar + `BS#1`/`BS#2` 2.0 MW blackstart IC sets), so the plant total
sits 10.9 MW above the fleet's in **both** directions and
**446.6 − 10.9 = 435.7 == the fleet total exactly**. Both capacity bases agree
(zero NaN-summer rows), so miso-126's hand-off is **reproduced, not
overwritten**. Totals decide a *dropped* row; at a plant with
legitimately-excluded rows the question must move to **row grain**. The two
tests are complements, not substitutes.

**NAMED SUCCESSOR, gathered but deliberately NOT adjudicated and NOT stamped.**
`6081_CA1` sits in the LP as a 96.0 MW **`oil`** generator with an empty
`plant_group` while its three `CC1`-block `CT` siblings are
`CC_REGULAR`/`gas_cc`, and CAMPD meters the block's fuel as **Pipeline Natural
Gas** at units 001/002/003 (`unitType` "Combined cycle") with **no CAMPD unit
for `CA1` at all** — miso-126's own ONE METER, ONE RATE picture. That is a
**classification/repricing** question in a different matrix family and needs its
own charter with its own measured identification. Sizing note stated so it is
not oversold: the plant meters only 73–91 GWh/yr gross, so it is a correctness
question before it is a magnitude one.

**DO-NOT-REDO.** Do not re-test `cc_steam_part_capacity` at NEISO — it is `I`
and the proof is a byte-identical armed fleet, not an argument. Do not re-open
`measured_chp_heat_rates` NEISO on the gate-3 correction: its `O` blocker is
unchanged (the neiso-70 `CC_CHP` overshoot, closed by neiso-71 as a REAL FLEET
DIFFERENCE — NEISO's merchant `CC_CHP` genuinely carries no host-steam
obligation — whose DO-NOT-REDO stands). Do not re-derive a `CC_CHP` host-steam
floor for NEISO. Kendall's capacity basis stays ADJUDICATED-ARTIFACT (neiso-73);
item 1 changed a *heat rate*, not a capacity.

**Governance.** 2023–2025 only; **no year outside the training window was read
and no solve was run at all**. NEISO's locked test remains SPENT and untouched;
the holdout spend freeze is ACTIVE and unspent (rule 22). Rule 25
`[R-ISO-SCOPE]`: only NEISO's artifact was re-derived and only NEISO's cells are
stamped — PJM's and CAISO's CHP artifacts stay un-gated and handed off, and
CAISO 54912 Martinez stays CAISO's. Rule 28b: **both tested cells are stamped in
this session**, the inert verdict included. Rule 28c: no new `ScenarioConfig`
field. Rule 27 `[R-PUSH]`: exact on-disk bytes; blob-verified after push.

Next shorthand: **neiso-81.**

## neiso-84 — the 2022 VALIDATION TOUCHPOINT is SPENT: price level and shape DEGRADE out-of-sample, everything else HOLDS (2026-08-05)

**What was run.** NEISO's designated keeper recipe
(`2026-08-05-neiso-83-ca1-reclass`, CALIBRATED-WITH-CAVEATS on 2023–2025),
frozen and replayed on the held-out year 2022 via
`replay_keeper.py --years 2022 --holdout-authorized`. **Zero recipe deltas** —
no `--set`, no `--offer-curve-json`, no config edit — so the rule 20 `[R-DOF]`
ledger is carried onto the touchpoint attestation byte-identical (14 entries,
5 residual-identified). **No parameter was identified, re-identified or
re-fitted on 2022, and no 2022 result fed back into any input.** Registered
`2026-08-05-neiso-2022-touchpoint`.

**Authorization.** The touchpoint is the intended use of NEISO's `complete`
marker (validation tier). It was spent under a **narrow owner lift** of the
2026-07-25 holdout spend freeze (owner, 2026-08-05: "lift, spend, re-arm"),
scoped to the PJM and NEISO 2022 touchpoints alone, and the freeze is
**RE-ARMED in the same session** — see `holdout-freeze.json` history. NEISO's
locked test (2019 + H1-2026) is **SPENT since 2026-07-07 and was NOT re-opened**;
`final` remains empty.

**Result, as scored — NOT-YET on 2022 against CALIBRATED-WITH-CAVEATS
in-sample.** The split is the point, not the label:

| | criterion | in-sample | 2022 |
|---|---|---|---|
| **DEGRADED** | C3a mean LMP | PASS | **FAIL +14.7 %** |
| **DEGRADED** | C3b price duration/shape | PASS | **FAIL NRMSE 0.620** |
| CARRIED | C3c price tail (RT) | CAVEAT | FAIL — model 0 h vs actual 117 h |
| HELD | C1 fuel-mix (grid-delivered) | PASS | PASS (6/6, free 4/4) |
| HELD | C2 system volume | PASS | PASS |
| HELD | C4 dispatch correlation | PASS | PASS |
| HELD | C6 governance | PASS | PASS |
| HELD | C8 forced-energy share | PASS | PASS |

So the **quantity** side of the model travels to an unseen year intact —
fuel mix, system volume, hourly dispatch correlation and the forcing budget all
hold — and the **price** side does not. Model load-weighted λ is $104.57
against a measured RT $84.92. C3c is NOT new evidence: it is the keeper's
existing ledgered caveat (the energy-only LP forms no >$300 tail) travelling
unchanged, and 2022's 117 actual tail hours simply make the same gap bigger.

**What this is NOT.** Validation tier is **ITERABLE model-SELECTION evidence**.
+14.7 % is **not** a certified out-of-sample skill number and must never be
quoted as one.

**AVAILABILITY-ENVELOPE PARITY IS VERIFIED — corrected 2026-08-05.** An earlier
draft of this entry carried the envelope defect as a reason to discount the two
degradations. That was too broad and is withdrawn. 2022 is built from the SAME
uniform 2018–2026 CAMPD detector regeneration as 2023–2025 (one pass, not a
separate holdout derive), carries the SAME merit-order guard (layup windows are
disjoint from the standard extract — 0 of 3,189 NEISO windows overlap), was
solved against the **byte-identical** layup artifact the keeper used
(`unit_outages_layup-cb80c81b7c2b`), and sits in family with the tuned years on
every volume measure (1.98 M MW-days vs a 2023–2025 range of 1.23–2.19 M;
median window 13 d vs 10–15 d). The residual over-count behind the freeze is
therefore **baked into the tuned years too**. Correct reading: it discounts the
**absolute level** of the in-sample and holdout scores alike, but **not** the
in-sample→holdout **delta**, which is measured like-for-like. **The C3a/C3b
degradations are not explained by the holdout year having worse data.**

**No re-tune was performed.** Rule 22's response to a validation miss is to send
the issue back to 2023–2025; this session only measured and reported. 2022 is a
strongly atypical year for NEISO (measured RT $84.92 against the 2023–2025
range, with a Jan $148.66 / Dec $121.40 gas-driven winter), so the natural first
question for whoever picks this up is whether the level miss is a fuel-passthrough
behaviour that only shows at extreme gas, not an offer-curve level error.

**Governance.** No mechanism was tested, so no mechanism-matrix cell moves
(rule 28b) and no `ScenarioConfig` field was added (rule 28c). The keeper is
UNCHANGED and no marker was re-keyed — a touchpoint is not a promotion. Rule 16
`[R-ALLYEARS]` is not engaged: it governs keepers, which must span 2023–2025;
this is a single held-out year, which is the shape the `complete` marker
authorizes. Run explorer pruned 16 → 6 on owner instruction, keeping the keeper,
the touchpoint and every run cited by `calibration-complete.json` or
`keepers/NEISO.json`.

Next shorthand: **neiso-85.**

## 2026-08-06 — RECORD CORRECTION (owner decision D-23): NEISO's locked test was NEVER GRANTED, not "SPENT" — every prior entry below that says otherwise is superseded by this one

**GOVERNANCE lane. NO solve, NO scoring, NO year touched, NO grant of anything.**
Committed artifacts only. This entry is a **correct-by-addendum**: the historical
entries it supersedes are left exactly as written, because what they recorded is a
faithful account of what the governance record said at the time. It was the record
that was wrong.

**THE CORRECTION.** The marker file, CLAUDE.md rule 22, and a chain of session
records asserted that NEISO's 2019 + H1-2026 locked-test one-shot "was scored ONCE
with the frozen neiso-53 config on 2026-07-07 and STANDS", and therefore that it was
**SPENT and never re-grantable**. **That claim is false.** The record now reads
**NEVER GRANTED**.

**THE ARTIFACT SEARCH** — reproduced independently at this session's HEAD before any
file was edited, and **extended beyond neiso-87's search to the full git history**:

| evidence | result |
|---|---|
| NEISO registry sidecars declaring a 2019 or H1-2026 solve year | **none** — all 27 NEISO sidecars *ever committed* (including retention-pruned ones, recovered from their pre-deletion blobs) declare years drawn only from {2022, 2023, 2024, 2025} |
| `frontend/data/backcast/bench/NEISO/` | 2022–2025 only |
| `actual_tail.json` NEISO | 2022–2025 — **no 2019 row exists to score against** |
| the memo cited as the authorization (`docs/handoffs/neiso-calibration-complete-memo-2026-07.md`) | **zero mentions of 2019**; its 2026-07-07 owner decision authorized a one-shot on **2022** (pre-dating the 2026-07-31 tier split, when "one-shot" still meant the validation year), and execution was **HELD the same day** pending the G-19 register |
| what `locked_test_scored_on` actually named | `2026-07-07-neiso53-winter-fuelsec-coldsnap` — a **TRAIN-tier 2023–2025 config id**, not a 2019 run |

Independently corroborated by the third-party peer review
(`docs/third-party-peer-review-2026-07.md` §6.3 item 1): *"On the evidence, no holdout
year has ever been solved, and the 'scored once and stands' claim is documentation
drift that should be corrected before it is ever cited as an out-of-sample result."*

**WHAT THIS CHANGES, AND WHAT IT EMPHATICALLY DOES NOT.** It changes *which question
is open* — from "may a spent one-shot be re-granted" (which forecloses it) to "should a
never-granted one-shot be granted now". **It grants nothing.** NEISO remains absent
from `final`; `holdout_policy.authorized(NEISO, locked_test)` still returns **False**
(re-verified this session); the holdout spend freeze is still **ACTIVE** and outranks
both marker blocks. **NEISO's `final` readiness answer is unchanged and is still NOT
YET** — neiso-87 §3 finds 2019 **unsolvable at HEAD** (`eia_demand_profiles.parquet`
carries NEISO 2021–2025 only, so the LP cannot be constructed), three further scoring
inputs absent, and — decisively — that 2019 **cannot discriminate** on the criterion
NEISO's frontier is declared on: the real market had **zero** RT hours over $300 in
2019, so C3c returns a free small-count PASS whatever the model does.

**ENTRIES IN THIS LOG SUPERSEDED BY THIS CORRECTION** (text left intact; read each one
with this entry attached — in every case the *substantive* rule-22 posture the entry
was asserting is unaffected, since all of them were declaring that they had spent **no**
out-of-training year, which remains true):

| § | entry | the superseded phrase |
|---|---|---|
| L702 | `neiso-70` (2026-07-31) | "locked test is already SPENT (2026-07-07), never re-grantable" |
| L803 | `neiso-71` | "locked test is already SPENT (2026-07-07), never re-grantable" |
| L860 | `neiso-72` | "locked test SPENT, untouched" |
| L921 | `neiso-73` | "locked test SPENT and untouched" |
| L991 | `neiso-74` | "NEISO locked test SPENT and untouched" |
| L1255 | `neiso-76` | "locked test SPENT and untouched" |
| L1442 | `neiso-78` | "locked test remains SPENT and untouched" |
| L1574 | `neiso-79` | "locked test remains SPENT and untouched" |
| L1673 | `neiso-80` | "locked test remains SPENT and untouched" |
| L1700 | `neiso-84` (2026-08-05) | "locked test (2019 + H1-2026) is **SPENT since 2026-07-07 and was NOT re-opened**" |

Note that `neiso-84`'s own headline — *"the 2022 VALIDATION TOUCHPOINT is SPENT"* — is
**correct and untouched**: 2022 is validation tier and was genuinely spent. Only its
*locked*-tier clause is superseded.

**FILES CORRECTED IN THIS SESSION** (live record; the ~22 `results/calibration/`
per-run session records that repeat the claim are **historical artifacts and were
deliberately NOT rewritten**): `frontend/data/backcast/calibration-complete.json`
(`locked_test`, `locked_test_note`, `locked_test_scored_on` → `…_WITHDRAWN`,
`phantom_reaudit_2026_07_19`, `determination`, `keeper_rekey_policy`, `final._note`),
`CLAUDE.md` rule 22, `frontend/data/backcast/holdout-freeze.json`,
`frontend/data/backcast/keepers/NEISO.json` (+ regenerated `status/NEISO.js`),
`frontend/data/backcast/registry/2026-08-05-neiso-2022-touchpoint.json`,
`docs/mechanism-testing-matrix.md`, `docs/calibration-best-so-far-neiso.md`,
`docs/FINDING-nyiso104-c3c-frontier-and-tiered-holdout-2026-07-31.md`,
`docs/forecast-readiness-prompt-pack-2026-07.md`, and correction addenda in
`docs/calibration-log/{neiso,nyiso,pjm}.md`. Full record:
`docs/handoffs/neiso-record-correction-2026-08-06.md`.

**Authorization / citation chain.**
`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
`docs/third-party-peer-review-2026-07.md` §6.3 item 1 → **owner decision D-23, SIGNED
at the 2026-08-06 sitting Addendum X.6** (session-logged authorization for this
correction). `scripts/audit_keepers.py --iso NEISO` PASSES (0 failures, 0 warnings)
after the edits.

## 2026-08-07 — neiso-89: the `final` prerequisites — three closed, and the keeper-drift bisect returns a NEGATIVE result

Prerequisite/diagnosis session. **No mechanism tested, no cell verdict moved (rule 28d), no
`ScenarioConfig` field (rule 28c not engaged), keeper UNCHANGED
(`2026-08-05-neiso-83-ca1-reclass`), nothing registered, and no out-of-training year solved,
scored or registered.** Every solve is in-sample and a rule-16 throwaway diagnostic probe.
Full record: `results/calibration/ASSESSMENT-neiso89-final-prereqs-2026-08-07.md`. Tasks 1a/1b/3 merged as PR #3693; this entry is the remainder, rebased onto main. **Item 5 below ran concurrently with neiso-90 (PR #3700, merged first) and is superseded in its detail by it — where they differ, neiso-90 governs.** The bisect (item 3) is unique to this session.

**1. Data prep (rule 22 as rewritten — unrestricted, not a spend).** NEISO **2019 and 2020**
now carry `calibration_reference.json` blocks and `NEISO_<y>_renewable_capacity.csv`, on the
same F3 closure pjm-160 built for PJM 2019 (`curate_demand_profile.curate_pre_window`, which
writes each ISO's pre-window `demand-profile` partition from that ISO's own `DEMAND_LOADERS`
adapter). Applied to BOTH pre-window years, not 2019 alone. **NEISO 2020 is included where
PJM's is excluded**: measured over the per-BA series, NEISO 2019/2020 are 8,760 h with 0 NaN
and **0 hours flagged**, max/median 1.82 and 1.93 against the screen's empirical 2.1 bound
(PJM 2020 peaks at 192,229 MW). Merge, not replace, and **verified before the write**: an
11/11 pre-flight replay of the committed NEISO 2021-2025 + PJM 2019-2025 demand blocks, every
pre-existing ISO-year block byte-frozen by md5, all 29 pre-existing CSVs byte-identical by
`cmp`. New blocks are coherent — solar 1,365.6 → 1,670.4 → 2,215.1 → 2,923.9 MW across
2019/2020/2021/2023, nuclear 29.8 → 25.6 TWh across Pilgrim's mid-2019 retirement.

**2. `actual_tail.json` NEISO 2019 is an INTERLOCK, not a gap.** The recorded blocker
(`CONSIDERED_HOLDOUT_YEARS = (2022, 2026)`) is not what holds it: 2019 is locked-test tier,
`final` is EMPTY for every ISO, so the tier gate refuses it whatever that tuple says. The
cross-ISO impact review enumerated the tuple's real effect — it withholds the VALIDATION
ladder — so the tuple was **DELETED** rather than widened (rule 26 `[R-DELETE]`: removed, not
emptied, so it cannot be re-armed), leaving the tier marker as the **sole** gate. Six rows
newly emitted: NEISO/NYISO/PJM × {2020, 2021}, every one validation-tier for an ISO that
already holds the validation marker; **zero** locked-tier rows unlocked for anyone. All 18
in-sample rows and all 4 pre-existing 2022 rows md5-identical; keeper re-scores unchanged
(CALIBRATED-WITH-CAVEATS, C3c sole caveat, C1 12/12 · free 8/8); `audit_keepers --iso NEISO`
0/0; `tests/scoring/test_holdout_year_gate.py` 27 passed (two tests rewritten with the reason
in their docstrings, plus two new ones pinning that the deletion did not weaken the gate).

**3. THE BISECT (owner decision D-88.3): NEGATIVE — there is nothing in the commit range.**
Replaying the keeper's 2025 recipe at its own sha `f8f803dd` and at HEAD `c710d17e` — **373
commits apart, same data root** — gives **byte-identical** `class_hourly`, `system`, `storage`
and `reserve_family`, and **0 of 8,760 hours** of price difference. neiso-87 §4.0's premise
("the cause lies in ~50 commits after 243b4ab1") is refuted by measurement. Five candidates
eliminated: **code** (above); **inputs** (`neiso87_control_A`'s content-addressed
`shared_inputs` hashes are identical to the keeper's on campd/eia923/eia930 and all five
outage artifacts); **solver version** (`neiso87_control_A` ran highspy 1.14.0, the keeper's
own, and still diverges); **cross-year LP warm-start** (full 2023-25 chain with
`replay_keeper`'s pin removed → 2025 bit-identical to xyear-OFF, 2023/2024 prices
bit-identical to the keeper, the 2024 primal move being the documented zero-aggregate
marginal-tie reshuffle at total gen Δ = 0.0 GWh); and **a missing gitignored
`data/clean/hydro-plant-modes` partition** (curated, then inert). Four independent solves —
three code versions, two chain lengths, both warm-start settings, two clean-cache states —
agree with one another **to the bit** and all differ from the committed bundle by the
identical 731-hour January pattern (mean −3.9372, max |Δλ| 25.5244 $/MWh). **The committed
bundle is the outlier**; the residual cause is solve-time state the bundle does not record.
August's separate −3.7250 component in the post-edit arms is neiso-87's own committed
`NEISO,2025,8` basis correction, not drift. Recommended fix, **not taken** (re-registering the
designated keeper is promotion-class, with rule-15 registration, `audit_keepers` M1 and the
rule-22 D-5(b) determination re-verification attached): re-solve and re-register at HEAD,
`--year 2023 2024 2025`, expected 2025 mean λ **69.399** against the registered 70.0493.

**4. The CAMPD outage-detector vintage split DOES NOT EXIST.**
`campd-unit-outages-NEISO.csv` does not exist in `59f8bc30^`; that commit (2026-07-24)
**creates** it — git status `A`, 4,484 insertions / 0 deletions — covering 2018-2026 in one
derivation, and `6a8f285c` (2026-07-26) removes exactly 1,294 layup windows whose companion
file spans 2018-2026 (138/173/146/209/161/104/153/187/23), so the guard ran on all nine years
in one pass. 4,484 − 1,294 = 3,190 = the current line count. Detector fingerprint uniform (the
5.00-day floor is exactly the minimum in every year; no median-duration cliff at 2022/2023),
and the register's own counts (573/656/587/606/502, "committed 968 rows") match nothing in the
current file (434/483/441/397/340, 981). The entry was true when written and describes a
predecessor artifact. Register corrected; **neither offered remedy is needed — no
reconstruction, no re-derivation, no keeper-input change, no re-audit.** Rule 25: the NYISO row
carries the same stale premise and is left for the NYISO lane, with the method flagged.

**5. `final`: DO NOT DECLARE — and the reason has changed for the better.** The input blockers
are closed; what remains is neiso-87 §3.3, now standing alone: 2019 had **ZERO** actual RT
hours > $300, so C3c — NEISO's declared frontier, its one chartered lever refuted at Phase-0
(neiso-76) — returns a free small-count PASS and **cannot discriminate**. Spend the one-touch
year after the C3c lane resolves. One bounded input asymmetry is reported and deliberately not
closed: `parasitic_load_factors` has no per-year rows before 2022 (2021 included, so it is not
a `final` prerequisite), and its deriver rewrites a **cross-ISO** file and recomputes the pooled
`year==0` row every keeper consumes — a cross-ISO decision with a re-audit attached. `final`
stays EMPTY, the freeze stays ACTIVE, and `enforce_holdout_year_gate` was verified still
refusing NEISO 2019/2020/2022 while allowing 2023-2025. Carried forward for the owner,
unwritten: `holdout-freeze.json`'s 2026-08-06 **`history`** entry still repeats the false SPENT
claim that its own `lift_scope` field already corrects.

## 2026-08-09 — KEEPER RE-KEYED to `2026-08-06-neiso-87-control` on owner instruction (reproducibility re-key; the stated rationale did NOT hold and is recorded)

**Session:** neiso-keeper-87-control · **Branch:** `claude/neiso-keeper-87-control-sed8d2`
**Keeper:** `2026-08-05-neiso-83-ca1-reclass` → **`2026-08-06-neiso-87-control`**
**NO SOLVE. NO LP CONSTRUCTED. NO MECHANISM TESTED, no lever opened, no matrix cell verdict
minted (rule 28d), no holdout year of either tier touched.** Every number below is computed
from committed artifacts — the two bundles' own `hourly/` sidecars, their run payloads, and
`calibration_verdict.py --run-id`.

**1. WHAT WAS ASKED, AND WHY ITS STATED REASON DOES NOT HOLD.** The instruction was to switch
the NEISO keeper to the neiso-87 control because "its fleet r is significantly better than the
current keeper". Measured from the two committed run payloads' `fuelRows` — the exact values
C4 scores:

| year | keeper gas r / NRMSE | 87-control gas r / NRMSE | coal r |
|---|---|---|---|
| 2023 | 0.919 / 0.118 | 0.919 / 0.118 | 0.383 → 0.383 |
| 2024 | 0.930 / 0.110 | 0.930 / 0.110 | 0.481 → 0.481 |
| 2025 | 0.880 / 0.160 | **0.882 / 0.158** | 0.245 → 0.246 |

2023 and 2024 are **bit-identical**. 2025 moves **+0.002 in r**, against a `DISP_R_FLOOR` of
0.70 both runs clear with room, and inside the **0.918–0.931** band spanned by *every* NEISO
run ever registered. There is no material fleet-r difference, and the promotion is **not**
made on one. (The genuinely large fleet-r move in this lane belongs to a different pair: the
2022 touchpoint, where the neiso-86 gas-basis repair took gas r 0.809 → 0.880. That is
validation tier and can never be a keeper, rule 16.)

**2. THE REASON THAT DOES HOLD — reproducibility.** The superseded bundle is a
**NON-REPRODUCIBLE OUTLIER**, established by the neiso-91 bisect (owner decision D-88.3) and
recorded in the entry immediately above: four independent solves across three code versions,
two chain lengths and both warm-start settings agree **to the bit** and all differ from the
committed `neiso83_ca1reclass_B` bundle by the same 731-hour January-2025 pattern. This keeper
is on the reproducible side of that split. Measured here directly from the two bundles'
`hourly/system_<year>.parquet` (scored pass P2; P1 identical in direction and magnitude):

| year | zone-hours differing | keeper mean λ | 87-control mean λ | Δ | max abs Δλ |
|---|---|---|---|---|---|
| 2023 | **0 of 43,800** | 38.4902 | 38.4902 | 0.0000 | 0.0000 |
| 2024 | **0 of 43,800** | 43.7081 | 43.7081 | 0.0000 | 0.0000 |
| 2025 | 3,655 of 43,800 | 70.0868 | 69.7524 | −0.3344 | 25.5244 |

Per-class energy moves in 2025 only: `oil` −0.0773 TWh against `CC_REGULAR` +0.0710 /
`CT_PEAKER` +0.0044 TWh, total generation conserved to +0.0007 TWh; 2023 and 2024 have **zero**
classes moving. On the scored criteria the 2025 row moves **C3a +3.0 % → +2.5 %**, **C2 gas
+2.6 % → +2.8 %**, **C4 gas r 0.880 → 0.882**. Both directions are reported: C3a and C4 improve
marginally, C2 degrades marginally, and **no criterion changes status**.

**3. DETERMINATION RE-VERIFIED, RULE 22 D-5(b) SATISFIED.**
`calibration_verdict.py --run-id 2026-08-06-neiso-87-control` (committed artifacts only, no
solve) → **CALIBRATED-WITH-CAVEATS**, 0 FAILs, 1 ledgered caveat (C3c price tail / scarcity, RT
hourly), C1 all 12/12 · free 8/8, grade summary scored 8 / target-grade 7 / commercial-grade 0
/ ledgered 1 — **criterion for criterion identical** to the superseded keeper. The re-verified
determination is **not worse**, so the promotion proceeds without an owner escalation and
`calibration-complete.json`'s NEISO entry is re-keyed in the same commit (`audit_keepers --iso
NEISO` M1a: FAIL → PASS, 0 failures / 0 warnings). C3c is bit-unchanged (model 0 hours >
$300/MWh in both runs, all three years), so **no new caveat slot is spent** and the 2026-07-11
frontier declaration carries forward untouched — re-checked on the new keeper's own
`reserve_family_<year>.parquet`: `shortfall_mw` = 0.0 and `held_mw` ≥ requirement in every one
of 157,680 family-hours at the published static requirements, RCPF co-optimization still
**dormant**.

**4. TWO DEFECTS IN THE PROMOTED RUN, DISCLOSED HERE RATHER THAN LEFT TO BE FOUND.**

- **(a) It carries a SUPERSEDED measured input — rule 14 `[R-ACCURATE]`, bounded to one month
  of one year.** This run was solved as **arm A** of the neiso-87 Aug-2025 basis A/B, i.e.
  deliberately on the stale `NEISO,2025,8` interpolation **+0.04**, while HEAD carries the
  measured **−0.38** (ISO-NE Massachusetts gas index, August-2025 recap published 2025-10-02,
  $2.53/MMBtu in both table and narrative) — committed by neiso-87 itself. The size is
  measured, not estimated, from that A/B's own record: arm B gives August-2025 mean λ 43.7004
  against this run's 47.4254 (−3.7250) and 2025 annual mean λ **69.3990** against **69.7149**.
  **So a fully-current re-solve is the run that should hold this slot** — exactly the entry
  above's standing recommendation (expected 2025 mean λ 69.399). Arm B was never committed or
  registered and reproducing it needs a solve, which this session did not run. **OPEN ITEM for
  the next NEISO session that solves:** re-solve this recipe at HEAD, `--year 2023 2024 2025`,
  register it, re-key this shard to it.
- **(b) Its C8 evidence was produced at promotion, not at registration.** The bundle was
  registered without `legitimacy_diagnostics.json`, so **C8 forced-energy share scored
  SKIPPED** — an unscored *protective* criterion, which would have been a determination
  regression against the superseded keeper's C8 PASS. It was generated in this session
  (`scripts/legitimacy_diagnostics.py --bundle results/calibration/neiso87_control_A --iso
  NEISO --years 2023 2024 2025`), reading this bundle's own committed artifacts and run
  payload with floors reconstructed via `run_year(fleet_only=True)` — **no LP solve**. C8 then
  **PASSES** on its own data: every *material* class inside its rule 20 `[R-FORCED-BUDGET]`
  cap in every year (largest material forced share CC_REGULAR 0.0039 / 0.0082 / 0.0074 against
  a 0.30 limit), and the three over-cap rows (COAL 0.337 in 2023, CT_PEAKER 0.224 in 2023,
  ST_GAS 0.245 in 2025) are all immaterial classes below the 2 %-of-load gating floor. **D-4
  off-window binding PASSES on every floor-year row** (`offwindow_twh` 0.0 throughout); D-5
  parity, D-9 overlay quarantine and D-10 free-class rescore all PASS. The bundle's
  `metrics.json` was rewritten from the same scorer (`--write-metrics`) so the committed
  artifact and the live verdict agree. **D-1 diurnal shape carries the same class-level gate
  failures the lane has carried throughout** (COAL_BIT off-peak CV all three years, 2023 ST_GAS
  profile r, 2025 CT_PEAKER off-peak CV); the standalone C7 gate that scored them was RETIRED
  at rubric v3.1, and they do not reach C8's grounded-above-budget escalation because no
  material class is above its cap.

**5. CARRIED FORWARD UNCHANGED, because the recipe is unchanged.** `cc_steam_part_reclass`,
`measured_chp_heat_rates`, the neiso-caiso156 CT heat-rate meter screen, the neiso-71
per-reactor nuclear availability overlay and the neiso-72 hydro window all carry forward —
a programmatic diff of the two `run_config` scenario blocks returns **no differing key**. So
does the neiso-83 open root-cause issue (`campd-unit-outages-NEISO.csv` routing plant 6081's
DIESEL peakers to `plant_group=CC_REGULAR` because `oil` carries no plant_group at all), the
CC_CHP under-production residual, and the 2025 C1 CC rows SKIPPED on the preliminary EIA-923
vintage. **And so does the neiso-84 escalation:** this bundle carries `meta.json`
`commitment=true`, persists passes P1 and P2 and is **scored on P2**, exactly as the superseded
keeper was — NEISO remains the only ISO of six running the archived P2 pass. Neither resolved
nor worsened here; it needs a re-solve and should be settled in the same session that closes
(4a).

**6. Holdout posture unchanged.** `final` stays EMPTY, the freeze stays ACTIVE, the 2022
validation touchpoint block is untouched, and this session solved nothing at all.

## 2026-08-09 — Site retention: NEISO reduced to the keeper + the same recipe on 2022

**Session:** neiso-keeper-87-control · **Owner directive.** No solve, no LP, no mechanism, no
holdout spend. Keeper UNCHANGED (`2026-08-06-neiso-87-control`).

**The rule applied, in the owner's words:** keep the keeper for the training years and the same
keeper recipe on 2022; *"if the 2022 holdout was a NOT-YET then any runs after that. But if the
keeper is resolved and 2022 passes then just keep that on the site."* Both conditions hold for
NEISO — the keeper is CALIBRATED-WITH-CAVEATS on 2023–2025, and `2026-08-06-neiso-2022-corrected-basis`
is **CALIBRATED-WITH-CAVEATS on 2022 with every criterion HELD out-of-sample except C3c carried**
(stamped this session from committed artifacts, no re-solve). So NEISO keeps **two** runs where PJM,
whose 2022 touchpoint is NOT-YET, keeps four.

**Pruned (6)** via `scripts/prune_iso_runs.py --force-uncite`, each removing the registry sidecar,
the `runs/<id>.js` payload and the `results/calibration/<bundle>/` directory together:
`2026-07-31-neiso-72-hy-window`, `2026-08-03-neiso-caiso156-meter-screen`,
`2026-08-04-neiso81-chpheatrate`, `2026-08-05-neiso-83-ca1-reclass`,
`2026-08-05-neiso-83-control-zerodelta`, and the superseded `2026-08-05-neiso-2022-touchpoint`.

**Five of those are still named as evidence** in `keepers/NEISO.json` and
`calibration-complete.json` — the keeper genealogy, the neiso-83 zero-delta control, the promotion
comparisons. Those citations now point at runs that are no longer on the site. That is deliberate
and on the owner's instruction, it is **recorded rather than hidden** (`site_retention_note` in the
shard, `site_retention_2026_08_09` in the marker), and the narrative text is left **verbatim and
un-retracted** because it is the record of how the determination was reached. Nothing that
constitutes the evidence was deleted: every `FINDING-*` / `PREREG-*` / `ASSESSMENT-*` document
under `results/calibration/`, the A/B records, this log, and the mechanism-matrix cells are all
retained by the prune tool by design, and the runs themselves remain in git history.

**`holdout_touchpoint` re-keyed** from the superseded `2026-08-05-neiso-2022-touchpoint`
(NOT-YET; C3a and C3b degraded) to `2026-08-06-neiso-2022-corrected-basis`
(CALIBRATED-WITH-CAVEATS). **Not a re-tune and not a fit bought with a parameter:** the two runs
are the same frozen recipe and the only difference is the repaired measured input — neiso-85
diagnosed the hub-basis series as seasonally inverted (EIA N3050MA3 LDC purchase-portfolio
average), neiso-86 replaced it with the measured ISO-NE MA gas index. This is rule 22's touchpoint
loop working exactly as written: the touchpoint surfaced an **object**, the fix was a data repair
with **zero free parameters**, and nothing was ever fitted to 2022.

**NOT DONE, and it is not a judgement call — it is blocked.** The directive also asks that the
keeper and its 2022 be **one 2022–2025 bundle**. That needs a fresh combined solve, and the gate
refuses it, measured this session rather than assumed:

```
enforce_holdout_year_gate([2022,2023,2024,2025], 'NEISO', holdout_authorized=True)
  -> REFUSED: --year [2022] is under an ACTIVE HOLDOUT SPEND FREEZE (declared 2026-07-25)
enforce_holdout_year_gate([2023,2024,2025],      'NEISO', holdout_authorized=True)  -> ALLOWED
```

`holdout-freeze.json` is ACTIVE (re-armed 2026-08-06 immediately after the narrow single-purpose
lift that produced the corrected-basis run) and outranks the `complete` marker for **every** ISO,
`--holdout-authorized` notwithstanding. Lifting it is an owner action. Two things are worth
weighing before it is lifted for this purpose: (a) the freeze's own stated reason is still open —
the CAMPD detector books sustained economic layup as mechanical outage in all six ISO extracts, so
the availability envelope every keeper is calibrated against is expected to move; and (b) a single
bundle scored as one determination **merges a validation-tier year into the keeper's headline**,
which is the one thing rule 22 says a validation number must never become ("selection evidence,
never a certified out-of-sample skill number"). Until then the site carries the two runs and the
Run Explorer composes them into a single 2022–2025 year selector on the keeper, with the 2022
entry labelled `validation holdout` and its provenance banner naming the source run.

---

## 2026-08-13 — neiso-92: the 2021 readiness proof comes back **NOT CLEAN** — nuclear availability is the blocker, and it is not on anyone's list

**NO LP. NO SOLVE. NO SCORE. NO REGISTRATION.** Phase-1 data-readiness proof only — rule 22 channel 1,
which the holdout spend freeze does not cover. The freeze was verified **ACTIVE** at HEAD `cfb8127`
and was **not lifted and not modified**. 2019, H1-2026 and the `final` block were not touched.
Full record: `results/calibration/ASSESSMENT-neiso92-2021-readiness-2026-08-13.md`.

**Session shorthand corrected.** The prompt opened as "neiso-89"; that ordinal is taken
(`ASSESSMENT-neiso89-final-prereqs-2026-08-07.md`, plus neiso-90 and neiso-91 are on the record), so
this session is **neiso-92**. The prompt also anticipated a neiso-88 combined 2022–2025 keeper
bundle: **it has not landed** — the registry still holds exactly two NEISO runs and the keeper shard
still designates `2026-08-06-neiso-87-control`, so per the prompt's own fallback that is the recipe
graded here.

### Verdict: do not solve 2021 yet

Four inputs grade **DEGRADED** against the 2022–2025 standard. One is severe enough on its own to
reproduce the **neiso-85 failure mode** — a single absent measured input, month-concentrated and
systematic in sign, that would dominate the residual so the spend measures a data gap rather than
forecast skill.

**The two inputs the prompt flagged as highest-risk both came back clean**, which is worth stating
plainly because it is where the effort was expected to land:

- **Demand is a dense, real 8760** — 0 NaN, 0 zeros, 0 duplicate hours, mean 13,377 MW, `normalized`
  summing to 1.000119. Its one artifact hour (**2021-11-07 01:00 = 2,598 MW**, the DST fall-back
  duplicate) is *smaller than what the training window carries*: tuned year **2024 has three
  outright zero-MW hours**. Not partial, not backfilled.
- **The gas basis is fully on the measured index** — 12/12 months of 2021 on the ISO-NE MA gas index,
  each with its own newswire recap URL, zero proxy rows. Reproduced through the keeper's own config
  (`scripts/probes/_neiso92_2021_gas_chain.py`, a re-point of the neiso-85 decomposition onto the
  designated keeper since that probe's source bundle was pruned): **winter/summer 2.207**, in family
  with 2020 2.030 / 2022 2.104 / 2023 2.390 / 2024 3.778 / 2025 4.808, and nothing like the **0.397
  inversion** neiso-85 caught. EIA-923 12/12 receipts, hub overlay 100.0 % of hours — identical
  coverage to every tuned year.

Fourteen further inputs graded EQUIVALENT on measured evidence (outage windows from the uniform
2018–2026 detector pass: 397 windows / 2.23M MW-days / median 12.2 d, inside the tuned band;
emission rates 77.5 % measured vs 78.2–79.3 %; LMP actuals 8760 rows with the same single NaN 2023
carries, and the **chronological clock verified** by load–price correlation 0.459 inside the tuned
0.327–0.586 band with identical peak-hour alignment; CAMPD all six states; EIA-930 140,160 rows;
weather 365 days × 4 zones 0 NaN; renewables byte-identical schema; eGRID2021 present; the
year-invariant derived params).

### The blocker: nuclear availability has **no measured layer at all** outside 2023–2025

`data/raw/nuclear-availability-NEISO.csv` covers **2023-01-01 … 2025-12-31 only**, and its fallback
anchor `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` covers **2023/2024/2025 only**. Both measured layers are
absent for every validation-ladder year. `nuclear_unit_availability_series` returns `{}` and
`data/fleet/arrays.py:248` falls through — **silently, with no warning** — to the static climatology
`NUCLEAR_MONTHLY_CF['NEISO']`, mean 0.982.

Sized against EIA-930 ISNE `NUC` on the 3,389 MW fleet (method validated: the committed anchor tracks
that reconstruction to 0.007–0.016 in every year it exists):

| year | actual mean CF | static fallback | phantom nuclear | worst month |
|---|---|---|---|---|
| 2020 | 0.858 | 0.942 | **+2.51 TWh** | Apr +1.18 |
| **2021** | **0.911** | **0.942** | **+0.96 TWh** | **Oct +1.25** |
| 2022 | 0.922 | 0.942 | **+0.61 TWh** | May +0.80 |

**October 2021 is the problem.** Real nuclear CF was **0.425** — a deep refuelling outage — against a
fallback holding the fleet near 0.92. That is **~1,900 MW of phantom baseload running all month**,
≈ **1.25 TWh ≈ 14 % of October load**, displacing gas at the margin in exactly the month 2021's
autumn gas ramp was building (Oct delivered gas $4.75/MMBtu, Oct RT LMP $55.9 → Dec $59.4).

Three further DEGRADED rows: the **interchange seam tranches**
(`IMPORT/EXPORT_TRANCHES_BY_YEAR['NEISO']` 2023–2025 only, so 2021 silently takes the pooled
2023–2025 seam supply curve on a fleet where imports are a large share of supply),
**`eia860_chp_by_year.parquet`** (2023–2025 only; 2021 classified on the latest vintage snapshot),
and **parasitic load factors** (NEISO carries 2022–2025 rows but no 2021).

### A prompt premise corrected

`bench/NEISO/2021.json.gz` is indeed absent, and the prompt read that as a prerequisite to build.
It is not: `render_backcast._write_bench_part` derives the part from **the registering bundle's own
committed input snapshots**, so it is an **output of registration**, produced automatically when a
2021 run is registered and then read by the scorer. Its rubric-v2.4 `_lw` fields live in
`bench.avgLMP` and are computed at render time from the LMP actuals + demand, both of which 2021 has.
**Nothing needed building, and nothing was built.**

### What this says about the already-spent 2022 touchpoint

Gaps 1, 2 and 4 **also applied to 2022**, spent twice and currently the designated
`holdout_touchpoint` (`2026-08-06-neiso-2022-corrected-basis`): **+0.61 TWh of phantom nuclear**
(Apr/May, against real refuelling at CF 0.700 / 0.625) and the pooled seam curve. The shard's
**"AVAILABILITY-ENVELOPE PARITY IS VERIFIED"** claim is true *as scoped* — it is explicitly about the
uniform CAMPD **fossil**-outage detector, and that verification stands — but it does not cover the
nuclear envelope, and the nuclear gap is recorded nowhere in that block. **Nothing is retracted here
and no committed artifact was edited.** 2022 is validation tier and therefore iterable: the right
disposition is to re-spend it *after* the fix, alongside 2021 — not to re-interpret it now.

### The fix path, and why no lift should be requested yet

All four gaps are closable by **data prep alone**, and every upstream source is already on disk —
`data/raw/nrc-reactor-status/2021PowerStatus.txt` exists (2018–2026 all present), and **NYISO already
carries 2018–2025 from the same deriver**, so `derive_nuclear_availability.py` is proven over this
span. Under rule 22 as amended 2026-08-06 — *"what is held out is the SCORE, never the DATA"* — that
prep needs **no marker and no freeze lift**.

Sequence, in order: (1) extend the nuclear anchor + per-reactor extract, the seam tranches, the CHP
vintage table and the parasitic factors across **2019–2025 in one pass**, not for 2021 alone; (2)
**re-solve the keeper at HEAD across 2023–2025** on the corrected envelope — this also closes the
keeper's disclosed defect (i), the stale Aug-2025 basis row — and confirm the in-sample determination
is not degraded; (3) only then request a lift naming **2021 + 2022** as one validation re-spend.
Steps 1–2 change the availability envelope and therefore the in-sample result, so re-training must
precede re-reading the touchpoint — rule 22's touchpoint loop, step 3.

**Next shorthand: `neiso-93`** (the envelope-repair intake: gaps 1–4 across 2019–2025, no solve).


## 2026-08-14 — neiso-93: the four 2021-readiness gaps CLOSED across 2019–2025, the keeper re-solved in-sample and PROMOTED — and a NEW 2019-only blocker found

**Scope:** data prep for 2019–2025 + an **IN-SAMPLE** (2023–2025) re-solve. **No out-of-training
year was solved, scored or registered** — not 2019, 2020, 2021, 2022 or H1-2026. The holdout spend
freeze was verified **ACTIVE** at HEAD and is **untouched**; no lift was requested and none was
needed (rule 22 as amended 2026-08-06: *"what is held out is the SCORE, never the DATA"*). The
`final` block and every locked-test artifact are untouched. **Nothing was tuned to any year's fit.**

**All four neiso-92 gaps CLOSED.** Every producer was **reproduce-checked against the years it
already owned before being extended**, and the values it already carried were verified unmoved.

**Gap 1 — nuclear availability (the blocker).** Both `--check` modes passed first (anchor: *"committed
table matches the EIA-923 derivation"*; NRC overlay: *"reproduces **byte-for-byte**"*). The anchor
gains 2019–2022 and the per-reactor overlay goes **3,288 → 7,670 rows**. **Cross-validated against
EIA-930 ISNE `NUC` hourly telemetry** — independent of the EIA-923 the anchor is built from —
at **|mean CF diff| 0.002 / 0.003 / 0.001** for 2020/2021/2022, **tighter than the committed tuned
years** (2023 0.001, 2024 0.004, 2025 0.007). All three expected refuelling windows appear and each
resolves to a single reactor: **Oct-2021 0.43 (930: 0.426) = Seabrook at plant CF 0.03**, visible in
the daily extract as **0.0 from Oct 7–31**, back to full Nov 12 — a five-week outage the static
climatology was covering at CF ≈ 0.92. The consumer now returns 3 real reactor series × 8760 h where
it returned `{}`.

**Gap 2 — seam tranches. Two blockers, not one**, and the second was not on the assessment's list
(patched into it this session). The NYISO proxy producer's source zips are absent from the repo
(gitignored/regenerable) — re-fetched 84/84 from MIS, rebuild **frame-identical** to the committed
parquet before widening. The EIA-930 route needs an `EIA_API_KEY` **this environment does not have**;
rather than stop, a **keyless `--source bulk`** route was added to the fetcher over EIA's Grid
Monitor archive — *the same family `fetch_eia930_bulk_long.py` already uses* — and proved equivalent
to the committed API extract over 2023–2025 (**mean identical to full float32 precision**; the only
18 non-identical rows are the DST fall-back hour's two ambiguous rows in opposite order). Both
ladders now span 2019–2025. **The year texture the pooled curve was erasing is large:** mean HQT
import runs **−1,576/−1,559/−1,532/−1,541 MW** across 2019–2022 against **−1,204/−694/−315** in
2023–2025 — HQ delivered ~5× as much in 2019 as in 2025 — so the early years' `HQ_PhaseII` rungs
price **below** their anchor where 2025's prices **+$51.9 above** it.

**Gap 3 — CHP by vintage.** The builder reads release zips **this clone does not carry**; a
vintage-dir source was added and **reproduces 2023/2024 plant-for-plant and flag-for-flag**.
Materiality, now measured rather than assumed: **exactly one** NEISO plant is classified differently
by the 2019–2022 vintages than by 2025.

**Gap 4 — parasitic load. THE SPEC WAS WRONG AND THE GAP IS BIGGER.** The assessment's *"NEISO
carries 2022–2025 but no 2021"* reads the file's **TOTAL** row counts as NEISO's (they sum to its
2,113). By plant-id intersection the file holds ERCOT 130/130, PJM 410/411, MISO 280/485, NYISO
27/106 and **ZERO NEISO plants in ANY year — the tuned years included**. Fixing only 2019–2021 would
have left NEISO inconsistent across the span, so the derive covers **2019–2025**. A destructive-write
hazard was found and fixed en route: the script rewrites the whole **shared** output, so a scoped
back-fill would have **silently deleted every other ISO's rows** (rule 25) — `--merge` added, and all
2,113 committed rows verified byte-identical after.

**Phase B — the keeper re-solved IN-SAMPLE and PROMOTED.** `2026-08-14-neiso-93-envelope`
(`results/calibration/neiso93_envelope_A`), 2023–2025 in one invocation, years sequential. A
**zero-delta** `replay_keeper.py` replay of the incumbent's own `meta.json` — the recipe reproduced
from the committed artifact rather than retyped. **Determination CALIBRATED-WITH-CAVEATS, criterion
for criterion IDENTICAL** to the superseded keeper (C1/C2/C3a/C3b/C4/C6/C8 PASS, C3c the sole
ledgered caveat, C1 all 12/12 · free 8/8, **0 FAILs**), so the rule 22 D-5(b) worse-determination
stop does not fire. It **closes the superseded keeper's disclosed defect (i)**, executing that
keeper's own standing recommendation: **2025 mean λ 69.7337 → 69.4178**, 2024 essentially
bit-identical, 2023 −0.011. Gap 4 is why the tuned years move at all — the nuclear *anchor* is
unchanged there. `audit_keepers --iso NEISO` **0 failures, 0 warnings**; matrix integrity, keeper
stamps and §5.x headers all OK.

**A NEW 2019-ONLY BLOCKER, FOUND AND NOT FIXED.** Pilgrim (**EIA 1590** — the committed comment cited
**6098**, which is *Big Stone*, a South Dakota coal plant) ran **Jan–May 2019 for 2.177 TWh** before
retiring 31 May 2019 and is **absent from the EIA-860 operable snapshot** the model fleet is built
from. **A 2019 solve is short ~2.18 TWh of nuclear regardless of the extended overlay.** EIA-930
shows it directly: Jan–May 2019 telemetry implies a 3,355 MW-fleet CF of **1.18–1.20** (impossible),
and the 923-vs-930 gap collapses to 0.003–0.005 from **June onward, exactly when Pilgrim stops**.
2020–2022 are unaffected. This is the direct analogue of NYISO's Indian Point caveat and is
**material to the `final` question**, which stays **NOT GRANTED**.

**2021 IS STILL NOT SOLVED, AND THAT IS CORRECT.** This session made it solvable; spending it needs
its own owner lift. Evidence:
`results/calibration/FINDING-neiso93-envelope-repair-2026-08-14.md`.

**Next shorthand: `neiso-94`.**

---

## 2026-08-15 — neiso-94: `final` stays **DO NOT GRANT**, and the 2019 Pilgrim gap is **repairable, cross-ISO, and disqualifying**

**Session `neiso-94`** (the shorthand neiso-93 named). **Keeper unchanged: `2026-08-14-neiso-93-envelope`.**
Freeze **VERIFIED ACTIVE at HEAD** and never engaged. **NO year was solved, scored or registered, in
or out of sample**; no LP was constructed. `holdout-freeze.json`, `calibration-complete.json` and the
`final` block are untouched. NEISO's locked test remains **NEVER GRANTED and NEVER SPENT** (D-23).

Full record: `results/calibration/ASSESSMENT-neiso94-final-readiness-2026-08-15.md`.
Charter opened: `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`.

### The Pilgrim adjudication — answered on measurement, not restated

neiso-93 sized the gap from EIA-923 at 2.177 TWh and left it as a caveat. This session re-derives it
by an independent route — an **envelope self-test** that integrates the committed per-reactor nuclear
overlay against the model fleet's own pmax and compares to EIA-930 ISNE `NUC` telemetry. Because the
overlay is a *fraction applied to units already in the fleet*, this isolates fleet-membership error
and tests neiso-93's whole extension in the same pass.

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| gap TWh | **−2.123** | +0.030 | +0.066 | −0.001 | −0.012 | +0.075 | +0.151 |

**The repaired envelope reproduces actual nuclear to ±0.15 TWh in every year 2020–2025 and is short
2.123 TWh in 2019 alone** — a 14–70× outlier against its own noise floor. It corroborates neiso-93's
extension from a collection the anchor does not use and isolates 2019 in the same measurement.
Monthly, the gap is **−593/−666/−670/−651/−390 MW** for Jan–May and **±15 MW** from June: a step
function at Pilgrim's retirement month against a 670 MW nameplate. A CF mis-derivation cannot produce
that shape; a missing generator can, and only that.

**(a) REPAIRABLE — YES, with zero new mechanisms and zero free parameters.** `cod_ramp.monthly_online_mask`
(`cod_ramp.py:326-357`) already handles `retirement_year == run_year` (online through the retirement
month) and `< run_year` (all-off); the retiree-injection path (`process_eia860.build_within_window_retirees`
→ `eia860_generator_retired_within_window.parquet` → `runner.py:1208-1212`, backcast-only) already
exists and was built for Mystic — the identical shape of problem. **The single blocker is one
constant**, `process_eia860.py:74 RETIREMENT_WINDOW_START = 2023`, whose own comment says "bump only
if the supported window moves" — and the window moved to 2019–2025 by the 2026-08-06 rule-22
amendment. Pilgrim's exact record is already on disk in `vintage_2019/eia860_generator_retired_and_canceled.parquet`
(`1590`, ret. 2019-05, 670 MW, BA→NEISO), in a file no fleet code reads.

**(b) ISO-AGNOSTIC — YES, and it decides the disposition.** The constant is global and the builder
maps every plant through `BA_CODE_TO_ISO` in one pass; lowering it 2023→2019 adds **264 plants /
21,467.5 MW across all six ISOs** (PJM 83/8,125; MISO 83/6,683; NYISO 15/3,418; CAISO 49/1,362;
ERCOT 13/966; NEISO 21/914, of which **Pilgrim is 670 MW = 73 %**). **NYISO's Indian Point is
confirmed the same defect with the same fix** — plants 2497 (IP2, 2020-04, 1,299 MW) and 8907 (IP3,
2021-04, 1,012 MW) are in the added set, i.e. the `~2,060 MW` its `NUCLEAR_MONTHLY_CF_BY_YEAR`
caveat calls permanent. **So it fails the "provably NEISO-local" test on measurement and NO PATCH
WAS LANDED**; the charter's gate is proving bit-identical 2023–2025 dispatch for all six ISOs (the
added units retire before 2023 so availability is zero, but the ramp leaves `pmax` intact, so
capacity-denominated code — binning, heat-rate joins, class denominators — must be proven unmoved,
not assumed).

**(c) DISQUALIFYING for the locked test — YES.** NEISO 2019's C1 fuel-mix volume band is
`min(2 % × 118.28 TWh load, 8) = ±2.366 TWh`, so **the gap is 91 % of the entire C1 error budget
before the model makes its first mistake**. Worse than the size is where it lands: `nuclear` is a
pinned class C1 never scores, and demand is a measured backcast input, so energy balance exports
2.146 TWh of Jan–May energy onto the **C1-scored gas row and the seam imports**, where it is
indistinguishable from model error. It also biases the *one* test 2019 could ever carry —
neiso-90's specificity test, where at actual = 0 h the small-count guard FAILs any model tail
> 10 h — toward manufacturing phantom scarcity. A disclosable limitation is one a reader can price;
this one cannot be priced from the scored output, and the tier is touch-once.

### The prerequisite audit at HEAD: exactly one row moved

`scripts/probes/neiso90_final_prereq_audit.py` re-run at the post-neiso-93 HEAD differs from the
committed neiso-90 output in **one row**: parasitic-load factors **463 → 544 plants** (gap 4). All 15
other rows are byte-identical, **including both GAPs** (`actual_tail.json` 2019, still the
self-healing tier gate and still the ordering hazard; `capacity_actuals_neiso.csv`, still not a
prerequisite). That is the expected signature rather than a null result: gaps 1–3 changed inputs'
*content*, not their *availability*, which is what the probe measures.

**A neiso-90 conclusion is corrected by that one row.** neiso-90 §2 dismissed the parasitic gap as
year-independent (correct — the only solve-path consumer reads the pooled `year == 0` map) and
concluded *"Nothing is disadvantaged"* (wrong — the shared file held **zero NEISO plants in any
year**, tuned years included). It is the one neiso-93 change that moves the in-sample result.

**Exactly one neiso-90 reason survives and it is the load-bearing one — 2019 cannot exercise C3c** —
plus both subordinate conditions (re-run `derive_actual_tail.py` first; H1-2026 independently
hard-blocked, `actual_lmp_hourly_NEISO.parquet` still carrying **no 2026 rows**). **neiso-93's four
closures retired none of it, and could not have**: all four are model-side inputs, while every
surviving reason is a property of the actuals or of the tier gate.

**What neiso-93 DID retire, verified on the keeper's own artifacts.** The prior keeper's disclosed
defect (i) — the stale Aug-2025 gas-basis row — is **CLOSED**: `neiso93_envelope_A/hourly/system_2025.parquet`
gives **2025 P1 mean λ 69.3989**, against the superseded keeper's 69.7149 and the **69.399** the old
shard predicted for a fully-current re-solve, with gap 2's in-sample 44.48 → 44.47 seam correction
carried in the same run. **So "the keeper is not current with HEAD" is retired as a precondition** —
the one direction neiso-93 moved the `final` question favourably.

### C3c discrimination: still holds, and the matter stops there

Re-read from the committed actuals: 2019 RT max **$261.35**, **0** hours > $300 — a $38.65 miss on
the whole year. C3c compares a model tail to an *actual* tail, so nothing neiso-93 landed could
touch it. At HEAD the outcome is still the worse branch — a **SKIP** (no `actual_tail` 2019 row) —
which caps the determination and names C3c unscored. Per the prompt's instruction no alternative
route was manufactured; the Pilgrim finding is an *additional* disqualifier, not a substitute route.

### Recommendation

**DO NOT GRANT `final`.** Two independent reasons: the **permanent** one (2019 cannot exercise C3c,
unchanged since neiso-87 and not addressable by any future work) and the **repairable** one (the
Pilgrim gap). neiso-90's trigger carries forward unchanged — the C3c lane arming a tail-forming
mechanism, at which point 2019 becomes a specificity test — plus **one added hard precondition**:
close the Pilgrim gap first, else that specificity test runs on a fleet biased toward inventing the
scarcity it tests for. Granting `final` is an owner act; nothing here declares, grants or prepares a
grant.

### Secondary finding, reported not fixed

The keeper shard's **`disposition_note` is byte-unchanged across the neiso-93 promotion** while
`keeper`, `prior_keeper_note` and `note` all changed. Under the current keeper it therefore still
names the wrong superseded run (`2026-08-05-neiso-83-ca1-reclass` rather than
`2026-08-06-neiso-87-control`) and still discloses defect (i) as live on "THIS KEEPER" — which the
same keeper's own sidecars show is closed. Over-conservative rather than over-claiming, and the
determination is unaffected, but a reader of the shard alone would draw a false conclusion. Left for
the `calibration-keeper-auditor` / the next NEISO session, per the neiso-90 §6 posture.

**Next shorthand: `neiso-95`.** The NEISO lane item is **gap 3's downstream check** and the
`disposition_note` repair above; the fleet-vintage charter is **not** a NEISO lane item and should be
assigned as its own cross-ISO session.

---

## 2026-08-15 — neiso-95: the `frontier` and `complete` declarations RE-VERIFIED on the current keeper, the stale `disposition_note` REPAIRED, and gap 3 confirmed **coverage-only**

**Session `neiso-95`** (the shorthand neiso-94 named). **Keeper unchanged:
`2026-08-14-neiso-93-envelope`** — no promotion, no re-key of `keeper`, **NO RUN PRODUCED**.
Full record: `results/calibration/ASSESSMENT-neiso95-declaration-recheck-2026-08-15.md`.

**Freeze VERIFIED ACTIVE at HEAD** (`active: true`, re-armed 2026-08-06, scope `isos: ALL`, tiers
`[validation, locked_test]`) and never engaged. **No year of any tier was solved, scored or
registered.** No LP was constructed. `holdout-freeze.json` and `calibration-complete.json` are
**unedited**. The only 2019–2022 reads are of **inputs**, unrestricted under rule 22 as amended
2026-08-06. NEISO's locked test remains **NEVER GRANTED and NEVER SPENT**.

### `frontier` HOLDS — re-established on the current keeper's own sidecars, not carried forward

The 2026-07-11 declaration had been made two keepers ago and `carried_forward_through` stopped at
the neiso-87 keeper. Re-verified from `neiso93_envelope_A/hourly/` (`neiso95_declaration_recheck.py`):
**C3c model tail = 0 hours > $300/MWh in 2023, 2024 and 2025 on BOTH passes**, recomputed under the
pinned `render_calibration_html._tail_hours` definition and agreeing with the committed payload's
`ordc.hoursGt200.model` (0/0/0 vs RT actuals 15/8/20). **It is not a near miss**: the whole-run
maximum of the max-across-zones price is **248.97 / 218.24 / 280.85 $/MWh** on P1 — the model never
reaches the threshold in any hour of any year, closest by $19.15. That is the dual-fuel oil-parity
cap showing up directly in the price distribution, i.e. a **formation** gap, not a magnitude one.
`reserve_family_<year>.parquet` — the only artifact in which a locational family's binding is
observable — carries `shortfall_mw = 0.0`, `held_mw ≥ requirement` and `dual = 0.0` (max |·| 1.42e-14,
floating-point noise) in **all 157,680 family-hours** at the published static 1,800 / 1,200 / 600 MW requirements, so the in-LP ISO-NE RCPF
co-optimization is **DORMANT**. **No C3c evidence moved in either direction** — the superseded
keeper's own sidecars recompute to the same 0 h on both passes, so neiso-93's envelope repair (which
did move prices) left the frontier basis bit-unchanged. `frontier.carried_forward_through` re-stamped.

### `complete` reproduces, and M1 passes

`calibration_verdict.py --run-id 2026-08-14-neiso-93-envelope` (committed artifacts only, **no
solve**) returns exactly the marker's recorded re-verification: **CALIBRATED-WITH-CAVEATS, 0 FAILs,
1 ledgered caveat (C3c), C1 all 12/12 · free 8/8, grade summary `{scored 8, target 7, commercial 0,
ledgered 1, fails 0}`**. So the D-5(b) re-key neiso-93 performed is **reproducible, not merely
asserted**. `audit_keepers.py --iso NEISO`: **0 failures / 0 warnings**, check M1 included.

**One stale clause reported and deliberately NOT edited.** The `complete` entry's `locked_test` field
still argues "2019 is UNSOLVABLE at HEAD" as part of its reasoning — a claim **withdrawn** by
neiso-88/neiso-90 and re-confirmed withdrawn by neiso-94 §3.2. The conclusion it supports is
unaffected (neiso-94's two live reasons are elsewhere). Left alone because this session's authority
over that file is the D-5(b) re-key verification, not a rewrite of the owner's `locked_test`
reasoning. Flagged for the owner / a governance lane.

### The stale `disposition_note` — REPAIRED (neiso-94 §6 closed)

Confirmed byte-unchanged across the neiso-93 promotion while `keeper`, `prior_keeper_note` and
`note` all changed, so under the current keeper it named the wrong superseded run
(`2026-08-05-neiso-83-ca1-reclass` rather than `2026-08-06-neiso-87-control`) and disclosed defect (i)
as live on "THIS KEEPER". Rewritten for the actual current keeper; **the superseded text is preserved
verbatim in `prior_keeper_note`**, labelled with why it moved — it remains a correct description of
`2026-08-06-neiso-87-control` as promoted. Exactly three fields changed (17 of 20 leaf fields
byte-identical, key order preserved); `build_status.py --iso NEISO` rebuilt `status/NEISO.js`
(`shared.js` unchanged). **The `calibration-keeper-auditor` re-checked the repair independently
(`--iso NEISO`): PASS, 0 failures, 0 warnings, 0 repairs needed** — it reproduced every claim from the
committed artifacts (including the un-rounded P1 maxima 248.9682 / 218.2412 / 280.8542) and confirmed
at the JSON-value level that the shard diff touches exactly the three intended fields. Its one
refinement is adopted: the reserve `dual` is zero to floating-point noise (max |·| 1.42e-14), stated
that way rather than rounded. **Two of the four disclosed defects are now closed with measurement:**
**(i)** the stale `NEISO,2025,8` gas-basis row — 2025 P1 mean λ **69.3989** vs the superseded
**69.7149** and the **69.399** predicted (2023 38.4324 → 38.4215, 2024 essentially bit-identical);
**(ii)** the C8 evidence gap — this bundle's `legitimacy_diagnostics.json` was committed in the
**registration commit itself** (`2cf773c`), so C8 PASSes on artifacts that shipped with the run.
**(iii)** and **(iv)** carry forward and were **re-checked at HEAD rather than assumed**:
`campd-unit-outages-NEISO.csv` still routes plant **6081** Stony Brook units **004/005** (the DIESEL
peakers) to `plant_group=CC_REGULAR`, 74 rows each; and this bundle's `meta.json` still carries
`commitment: true` / `passes ["P1","P2"]` — **NEISO remains the only ISO of six on the archived P2
pass**, neiso-84's escalation neither resolved nor worsened, **still open for the owner**. **(v)** the
2019 Pilgrim gap is recorded as a 2019-only blocker that **does not touch 2023–2025**
(`RETIREMENT_WINDOW_START = 2023` makes every affected plant availability-zero in the training
window); it belongs to the six-ISO charter, not this lane.

### Gap 3 downstream: **coverage changed, the tuned years did not**

`neiso95_gap3_chp_downstream.py`, three legs. **(A)** The 2023/2024/2025 partitions of
`eia860_chp_by_year.parquet` are **plant-for-plant byte-identical** to the pre-extension blob
(12,477 / 13,371 / 14,189 plants; CHP=Y 879 / 861 / 848; index and values identical) — all 52,596 new
rows land in 2018–2022. **(B)** `data.chp._chp_by_plant(dir, year)` returns that year's own row for
all eight covered years, and differs from the 2025-era snapshot on 45/37/31/23/20/15/5/**0** plants
for 2018→2025 — the monotone decay to exactly 0 at the snapshot vintage confirms the path is live,
not silently falling back. **(C)** The classification the **solve path** consumes is vintage-correct
per year: `run_calibration.py` passes the solve year at **both** fleet-sourcing branches (the
per-plant bin synthesis at `year=year`, and `build_base_fleet(..., vintage_year=year)`). The
extension is materially live where intended — **NEISO plant 10726 Masspower (3 CC units, 245 MW) is
`chp=Y` through 2022 and `chp=N` from 2023**, so 2019–2022 now carry it as CC_CHP where the snapshot
would have mis-classed it CC_REGULAR; it is the whole CC_CHP 739.0 → 494.0 MW step.

**One latent seam found, reported, NOT fixed.** `fleet.eia860._dual_fuel_plant_groups` takes **no
year parameter at all** and keys its `(plant_code, plant_group)` pairs off the un-yeared snapshot CHP
flag, so a plant whose vintage flag differs from the snapshot can silently lose its dual-fuel pairing
— which matters for an ISO whose winter price formation runs on dual-fuel oil parity. **It is
provably inert for this keeper**: of the nationally-differing plants in the tuned years (15 / 5 / 0),
**none is in the NEISO fleet** in any year, and NEISO's 47 / 49 / 49 matched dual-fuel pairs are all
correctly keyed. In 2019–2022 it would reach exactly one plant — Masspower again. ISO-generic, needs
its own scoped change plus a six-ISO in-sample proof.

### No run, by design

Items 1–4 left **no in-sample delta**, so the prompt's item-5 condition did not fire: no solve, no
registration, rule 15 and rule 16 not engaged. The changes are text and stamps in a keeper shard and
cannot change a solve.

**Data blocker, recorded not chased:** the `final` grant's H1-2026 half stays hard-blocked —
`data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet` carries 2018–2025 and **no 2026 rows**,
`bench/NEISO/` holds 2022–2025. That intake is unrestricted under rule 22 but was not this session's
task.

**Next shorthand: `neiso-96`.** No NEISO tuning lever is open — the frontier is declared and the
cross-ISO lever queue was cleared at neiso-80/81, so further C3c work needs a NEW measured
identification and its own charter. The standing NEISO lane items are the two owner escalations
(**the archived-P2 pass** and the **6081 outage plant_group routing**), both of which need a re-solve;
the `_dual_fuel_plant_groups` vintage seam and the `complete`-entry stale clause above are reported
and unowned. The **fleet-vintage/Pilgrim charter is NOT a NEISO lane item** and should be assigned as
its own cross-ISO session.

---

## 2026-08-15 — neiso-96: H1-2026 actuals **LANDED**, the C3c deriver **PRIMED**, and the `final` block recommended for a **SPLIT**

**Session `neiso-96`** (the shorthand neiso-95 named; verified, no divergence). **Keeper unchanged:
`2026-08-14-neiso-93-envelope`** — no promotion, no re-key, **NO RUN PRODUCED**. Full record:
`results/calibration/ASSESSMENT-neiso96-h12026-intake-2026-08-15.md`.

**Freeze VERIFIED ACTIVE at HEAD** (`active: true`, re-armed 2026-08-06, scope `isos: ALL`, tiers
`[validation, locked_test]`) — checked twice, at session start and again after the rebase onto
`834f761` — and **never engaged**. This session is a **DATA INTAKE**, which rule 22 as amended
2026-08-06 leaves unrestricted and which needs no marker: *"what is held out is the SCORE, never the
DATA."* **No year of any tier was solved, scored or registered.** `holdout-freeze.json` and
`calibration-complete.json` are **unedited**; `tail/actual_tail.json` is **byte-unchanged**. NEISO's
locked test remains **NEVER GRANTED and NEVER SPENT**. `frontier`/`complete` were **not** re-verified
— done at neiso-95, not repeated.

### The intake: H1-2026 landed, and the previously-owned years are provably UNMOVED

The SMD hourly workbooks the producer reads are served **only behind a CAPTCHA-gated ISO Express
form** (established this session; every `2026_smd_hourly.xlsx` path probed 404s), so no committed
script can refresh them — that is why the H1-2026 half was blocked. But ISO-NE publishes **the same
nine SMD pricing locations** through the **ungated** daily historical-report tree
(`histRpts/da-lmp/WW_DALMP_ISO_<date>.csv`, `histRpts/rt-lmp/lmp_rt_final_<date>.csv`). New downloader
`scripts/data/fetch_neiso_smd_zonal_lmp.py` reduces ~4.9 MB/day of all-node report to ~8 KB/day of
zonal series; 181/181 operating days fetched, **39,087 rows** (= 181 × 9 × 24 less the 9 spring-forward
rows — the arithmetic closes).

**The reproduce-check came first (neiso-93 discipline).** All eight owned years rebuilt from their own
workbooks: **md5 `3323efe038ab1bdb33382764eff4bfd0` before and after — byte-identical**, `git status`
clean, `DataFrame.equals` True over 70,080 rows. That md5 is also the blob at `origin/main` after the
rebase, and the 2018–2025 rows were re-verified byte-unmoved **again** after the 2026 merge.

**The two routes are ONE input, measured not asserted** (`neiso96_smd_route_equivalence.py`): on the 11
sampled days where both sources agree how many hours the day HAD, **2,640 cells, 0 float32 mismatches
— identical at the precision the parquet stores.** The worst float64 delta is 4.5e-13 and is an Excel
*storage* artifact (openpyxl returns `16.580000000000002`; the CSV publishes the settled decimal), not
a price disagreement.

**2026 block:** 8,760 dense rows, coverage **0.4958** (matching the partial-2026 blocks CAISO/NYISO/
MISO already carry), rt mean **$78.82**, max **$776.59**, and **126 actual RT hours > $300** —
concentrated Jan 90 h / Feb 35 h / Jun 1 h, a winter event. **Cross-checked against the same weather:**
NYISO's committed H1-2026 carries 86 h > $300, MISO 150 h > $200. `actual_lmp.json` gained **exactly
one** entry (`NEISO/2026`); every pre-existing entry across all six ISOs is byte-identical.

### UNPLANNED FINDING — the 2018–2023 SMD workbook vintage is DST-naive (reported, NOT repaired)

The only days the two routes disagree on are DST days, and the comparison isolates the cause to the
**workbook**. ISO-NE changed its shape mid-archive: **2024–2025 publish the true 23 (spring) / 25
(fall-back, with the repeated `02X` hour) and agree with the daily reports EXACTLY — 0 mismatches on
all four sampled DST days. 2018–2023 publish a flat 24 rows on every calendar day.** The producer's
positional clock is right for the new vintage and wrong for the old: on fall-back the workbook
collapses the repeated hour into its two-instance mean (2021-11-07 hub DA `52.43` = mean of the
market's `50.79`/`54.06`) and the day runs an hour short; on spring-forward it carries an extra row and
the rest of the day is displaced an hour late, spilling into the next date — visible as **exactly 1
duplicate timestamp in each of 2018–2023 and 0 in 2024–2025**. **Not repaired: 2023 is a tuned year, so
correcting it moves an in-sample SCORING TARGET and needs its own authorization and re-solve.**
Recorded with its measurement in `data/raw/lmp-data/README.md`.

### `bench/NEISO/` cannot be extended by an intake — a finding, not a shortfall

A bench part is **an output of REGISTERING A RUN, not a data artifact**: `write_bench_part` is called
only from `render_backcast`, off `render_calibration_html.build_payload(runs, …)`, which loops the
**bundle's** years and reads the bundle's own input snapshots **and `system.parquet` (model output)**.
The registry proves it exactly — NEISO's registered runs cover `{2022} ∪ {2023,2024,2025}` and the
bench dir holds **precisely** those four years, while 2018–2021 have committed actuals and **no bench
part**. **A 2026 bench part is produced BY a grant, not required before one**; creating it would mean
solving and registering H1-2026, the forbidden operation. Not attempted.

### `derive_actual_tail.py` re-run — output BYTE-UNCHANGED, and the hazard quantified

Re-run after the intake: **no diff**. NEISO still emits 2020–2025. The 2026 data is now **present** and
the tier gate **still refuses it** (locked_test, `final` empty) — 2019 and 2026 both `False`, 2018
fails closed. **The gate holds.** Against an **in-memory** marker (nothing written, no grant implied)
the row a grant would unlock is `{threshold 300, da_gt 140, rt_gt 126, coverage 0.496, hours 8760}`.
**neiso-90's ordering hazard is now an ordering REQUIREMENT rather than a data gap:** before this
session a grant + re-run would still have produced nothing for 2026 and C3c would have scored SKIPPED,
spending the touch-once year on a verdict silent on the criterion the frontier is declared on. The
requirement stands as step one of any grant; what changed is that satisfying it now works.

### `final` readiness, re-answered (updates neiso-94 §5): **DO NOT GRANT — but SPLIT the block**

**Retired:** the H1-2026 *data* blocker (neiso-94 §3.2's "independently hard-blocked"). **Survives,
untouched:** (1) **2019 cannot exercise C3c** — re-confirmed at HEAD, RT max **$261.35** vs $300,
**0 hours**, a property of the 2019 market; (2) the **Pilgrim** gap, still the six-ISO charter's.

**A new blocker occupies the place the old one vacated, and it is NOT NEISO's.** With a target in hand
the solvability question became answerable for the first time and was measured
(`neiso96_h12026_solvability.py`): H1-2026 is **NOT solvable at HEAD**. `demand` **ERRs**, and
structurally — the raw `ISNE_region_2026.parquet` exists and spans Jan–Jul, but
`eia930.frames._eia_hourly_frame` returns `None` unless the extract is a **full `HOURS_PER_YEAR`
series**, so a half-year is rejected before any ISO's loader sees it, and the fallback
`eia_demand_profiles.parquet` carries **2021–2025 only** and raises. **The gate is in shared code and
blind to ISO: every BA — ISNE, NYIS, CISO, MISO, PJM, ERCO — fails it for 2026 while four return 8,760
for 2025.** The model cannot build a partial-year solve for anybody. Four further per-year gaps:
`henry_hub` and `backcast_config` `KeyError: 2026`, no `calibration_reference` 2026 block, no
`renewable_capacity` file (and hydro is OK in name only — 5 plants / 0.04 TWh vs 168 / 8.55). **By
contrast 2019/2020/2021 demand all resolve OK** — the 2019-unsolvable claim stays withdrawn; it is
**H1-2026** that is unsolvable, because it is half a year.

**The halves are SEPARABLE and the split is recommended.** Neither of neiso-94's live reasons applies
to H1-2026: it exercises C3c **decisively** (126 actual RT tail hours vs 2019's zero) and Pilgrim
retired in 2019 so is correctly absent from a 2026 fleet. 2019's blockers are **permanent and
NEISO-specific**; H1-2026's are **structural, six-ISO and tractable**. Holding them in one block gates
a year that CAN answer the open C3c question behind one that provably never can. **RECOMMENDATION
ONLY — the split, like the grant, is the owner's call and nothing here declares either.**

### Escalations re-measured at HEAD — both OPEN, neither resolvable without a re-solve

**(i)** **NEISO is still the only ISO of six on the archived P2 pass**, measured on all six keepers'
own `meta.json`: NEISO `commitment=true, passes ["P1","P2"]`; CAISO/ERCOT/MISO/NYISO/PJM all
`commitment=false, passes ["P1"]`. neiso-84 neither resolved nor worsened. **(ii)** plant **6081**
Stony Brook units **004/005** still route to `plant_group=CC_REGULAR`, **74 rows each** — unchanged —
and the **mechanism is now confirmed rather than carried forward**: the `plant_group` enum at
`fleet/__init__.py:188` has **no oil or diesel member at all**, and `derive_campd_unit_outages.py:1112`
keys the map by **plant code**, so the diesel peakers inherit the CC units' group. Should be settled
together in one re-solve.

### No in-sample delta ⇒ no run

The tuned years are byte-unmoved (verified twice), `actual_lmp.json` gained one entry and changed no
other, `actual_tail.json` is byte-unchanged — and decisively, **nothing landed is a solve input at
all**: the actuals parquet is a scoring target no LP reads. Rules 15/16 not engaged. *(Incidental:
upstream #3982 pruned the **superseded** `neiso87_control_A/hourly/*.parquet`, so neiso-95 §1.5's
counterfactual is no longer re-runnable from those files; its conclusion is recorded and unaffected.)*

**Next shorthand: `neiso-97`.** No NEISO tuning lever is open — the frontier is declared and the
cross-ISO lever queue stays cleared, so further C3c work needs a NEW measured identification and its
own charter. Standing NEISO lane items remain the **two owner escalations** above, both needing a
re-solve and best settled together. **NOT NEISO lane items**, all now with measured evidence attached:
the **partial-year solve gate** (`HOURS_PER_YEAR`, six-ISO — the H1-2026 half's blocker), the
**2018–2023 SMD workbook DST defect** (touches in-sample 2023, so it needs authorization and a
re-solve), the **fleet-vintage/Pilgrim charter**, and the reported-and-unowned
`_dual_fuel_plant_groups` vintage seam and the `complete`-entry stale clause.

---

## neiso-97 — 2026-08-17 — the SMD DST-naive workbook repair, and the keeper re-solved at the corrected instrument (audit row O8; KEEPER PROMOTED)

**Branch** `claude/neiso-smd-dst-naive-repair-8b2eez` · **Charter** `docs/audit/third-party-audit-2026-08.md`
§8 row O8, served as an in-session owner card (the debug-sweep §A.2 two-card pattern) and **SIGNED:
option A (repair + full-span re-solve), promotion PRE-SIGNED on not-worse**. Full record:
`docs/FINDING-debug-b-neiso-smd-clock-2026-08-17.md`.

### The defect, measured from committed bytes before the card was served

Every 2018–2023 SMD workbook publishes a **flat 24 rows on every calendar day** (all 9 sheets;
2024–2025 publish the true 23/25). Adjudicated against the market's own daily hourly-LMP reports
(5 truth years × 9 sheets × 2 markets, **0 mismatches** under the winning mapping): the spring
phantom at position 1 is the **mean of its neighbours** (exact to the cent, every sheet, every truth
year); the fall-back repeated-hour pair is **collapsed to its mean**; every later value sits an hour
off; the fall day's true last hour is the single NaN each year carries. Committed-parquet blast
radius: **562 hub cells** (46–47 per market-year, in-sample 2023 included), max **$40.17/MWh**,
every cell inside the derived mechanism window. **No affected cell reaches $138.65** → the C3c $300
tail is untouched by construction; annual means move ≤ $0.008 — the repair cannot buy a score
(rules 13/14).

### The repair (byte-verified per the PJM input-clock §2a protocol — PASS on every check)

Vintage-aware placement in `derive_actual_lmp._neiso_sheet_series` + a **day-scoped** daily-report
overlay in `neiso_zone_hourly` (only a day the workbook cannot represent is taken from the report
route; the twelve DST truth days fetched to the committed `smd-zonal-lmp/` intake home; 2018-03-11's
RT report is a genuine upstream 31-byte stub — that spring day is fully recovered by re-placement,
nothing fabricated). Non-affected cells identical every row; displaced cells == pristine at the
corrected offset; the pair == published truth; one NaN per market-year **filled with the measured
value**, zero introduced; 2024/2025/2026 blocks byte-identical. `curate_lmp` got the same per-day
rule. Applied consistently 2018–2023 (rule 22: the data, never the score); **no out-of-training year
solved/scored/registered, freeze ACTIVE**. The 2022 touchpoint stands as scored on the pre-repair
instrument.

### The re-solve, and the promotion

`2026-08-17-neiso-97-dstrepair` (bundle `neiso97_dstrepair_A`): `replay_keeper` zero-delta re-solve
of the neiso-93 recipe, 2023–2025 in ONE invocation, all years fresh. **Dispatch BIT-IDENTICAL to
the incumbent's committed sidecars — every year, every sidecar, both passes, zero differing cells**
(the instrument moved, the model did not; probe `_neiso97_arm_vs_incumbent_sidecars.json`).
Determination **CALIBRATED-WITH-CAVEATS, criterion for criterion identical** (0 FAILs, sole ledgered
C3c caveat, C1 all 12/12 · free 8/8, grade 8/7/0/1); D-5(b) re-verified **before** the re-key;
attestation premises all computed (`gen_neiso97_dstrepair_attestation.py`), DOF (7/5) and exceptions
(7) ledgers carried verbatim, asserted. Keeper/status/complete-marker re-keyed; `audit_keepers --iso
NEISO` **PASS 0/0** (auditor agent: zero repairs needed); rule-28 re-stamps on the NEISO shard and
the §5.6 prose header (`check_mechanism_matrix.py` green); neiso-93 pruned from the site per the
lane's standing keeper+touchpoint directive (`--force-uncite`; bundle travels with the prune, the
durable evidence is the finding + committed probe records). **O5 (legacy P2) deliberately untouched**
— the replay stays like-for-like so the input repair is unconfounded; it remains the lane's open
owner escalation, still best settled together with the Stony Brook outage-routing fix.

### Ambient defects fixed or filed in passing (none O8's)

**Fixed:** `origin/main` HEAD carried a SyntaxError in `scripts/run_calibration.py` (duplicate
`run_year` kwarg from two racing merges) — every calibration solve of every ISO was blocked; fixed on
this branch, fast lane 18F/32E → **6,907 passed / 0 failed**. **Filed:** registry/payload parity is
RED on main for two stranded MISO-160 sidecars (MISO lane's, rule 25); the committed
`actual_lmp.json` NEISO 2024/2025 entries were stale (healed here, proven code-invariant); D-1
actual-side third-decimal drift vs the incumbent's committed diagnostics (ambient, `legitimacy_diagnostics.py`
never reads the LMP series). **NYISO cross-ISO disclosure:** its keeper arms
`nyiso_import_hub_prices=True` and solves on this parquet's DA hub series — 47 of its 2023 input
cells changed (max $20.12); filed for the NYISO lane, not acted on.

**Next shorthand: `neiso-98`.** No NEISO tuning lever is open — the frontier declaration was
re-verified on the strongest basis yet (measured bit-identity to the re-verified incumbent). The
lane's standing items are unchanged: the two owner escalations (legacy-P2 scoring basis = audit row
O5, and the Stony Brook 6081 outage routing), best settled together in one re-solve; the 2018–2023
SMD DST defect is **CLOSED** (this session).

---

## neiso-98 — 2026-08-17 — the frontier and `complete` declarations re-verified on the neiso-97 keeper's OWN artifacts; `final` still NOT YET; O5 sharpened

**Session `neiso-98`** (the shorthand neiso-97 named). **Keeper UNCHANGED:
`2026-08-17-neiso-97-dstrepair`** — no promotion, no re-key, **NO LP, NO RUN PRODUCED, NOTHING
REGISTERED**. Full record:
`results/calibration/ASSESSMENT-neiso98-frontier-verification-2026-08-17.md`.

**Freeze VERIFIED ACTIVE at HEAD** and **never engaged**. No year of any tier was solved, scored or
registered. `holdout-freeze.json` and `calibration-complete.json` are **unedited**. The only
2019–2022 reads are of **measured input series with no model side** — unrestricted under rule 22 as
amended 2026-08-06 ("what is held out is the SCORE, never the DATA"). NEISO's locked test remains
**NEVER GRANTED and NEVER SPENT**.

### `frontier` HOLDS — re-established directly, closing the transitive loop

neiso-97 re-verified the declaration **by measured bit-identity** to `2026-08-14-neiso-93-envelope`,
whose own basis neiso-95 had established directly — sound, but the same promotion **pruned** the
neiso-93 bundle, so the chain terminated in an artifact no longer in the repo (confirmed absent at
HEAD). Both legs are now re-derived from `neiso97_dstrepair_A/hourly/`
(`neiso98_declaration_recheck.py`). **C3c model tail = 0 hours > $300/MWh in 2023, 2024 and 2025 on
BOTH passes**, under the pinned `render_calibration_html._tail_hours` definition and agreeing with
the registered payload's `ordc.hoursGt200.model` (0/0/0 vs RT actuals 15/8/20). **Not a near miss,
now stated on both passes**: the whole-run max of the max-across-zones price is 248.97 / 218.24 /
280.85 on P1 and 249.50 / 256.93 / 280.85 on P2 — never reached in any hour of any year on either
pass, closest by **$19.15** (2025, 93.6 % of $300, identical on both). That is the dual-fuel
oil-parity cap in the price distribution: a **formation** gap, not a magnitude one.
`reserve_family_<year>.parquet` carries `shortfall_mw = 0.0` and `held_mw ≥ requirement` in **all
157,680 family-hours**, max `|dual|` 1.42e-14 (2024 P1 `ne_30min_total`, floating-point noise), at
requirements **checked against `NEISO_RCPF_PRODUCTS`** rather than read off the artifact
(1,800 / 1,200 / 600 MW, all three matching in all six year-pass blocks) — the RCPF co-opt is
**DORMANT**. **No C3c evidence moved and no lever was opened.**

### The shard's pass-basis inconsistency — RESOLVED: the scored pass is **P2**

`frontier.reverified` (neiso-84) said P2 and quoted 249.50 / 256.93 / 280.85; `carried_forward_through`
(neiso-95) quoted 248.97 / 218.24 / 280.85, the **P1** maxima. Both are correct arithmetic on
different passes; the shard had been carrying both without saying so, an 18 % spread on 2024.
Decided on the current keeper's own bytes by neiso-84's two routes, **agreeing in all three years**
(`neiso98_scored_pass_identity.py`): the payload's `HQ_import` mean λ (the zone with no actual
counterpart, hence the model mean — NEISO's five zones clear at one λ here) matches **P2** to
0.001–0.003 against P1 errors 0.0585 / 0.0130 / 0.0411; and the payload's `gmModel` per-class annual
TWh matches **P2** at 0.0714 / 0.0717 / **0.0003** TWh against P1's 0.0992 / 0.0795 / 0.0106 — 2025
decisive alone. **The declaration does not turn on this** (the tail is 0 h on both passes), so it is
a documentation defect, repaired in the shard rather than left for a reader to trip over.

### `complete` reproduces, and M1 passes

`calibration_verdict.py --run-id 2026-08-17-neiso-97-dstrepair` (committed artifacts only, **no
solve**) returns exactly the marker's recorded re-verification: **CALIBRATED-WITH-CAVEATS, 0 FAILs,
1 ledgered caveat (C3c), C1 all 12/12 · free 8/8, grade summary `{scored 8, target 7, commercial 0,
ledgered 1, fails 0}`** — so the D-5(b) re-key neiso-97 performed is **reproducible, not merely
asserted**. `audit_keepers.py --iso NEISO`: **PASS, 0 failures / 0 warnings**, check M1 included.
C2 still waits on the final 2025 EIA-923 vintage (2025 C1 CC rows SKIPPED by design; nothing
estimated around it).

### `final` readiness, re-answered (updates neiso-96 §4): **NOT YET — and this grants nothing**

**2019 half — still NO, now confirmed ON THE REPAIRED INSTRUMENT.** The neiso-94/96 measurement
predates the neiso-97 repair, which touched 2019 (47 RT + 46 DA cells, max |Δ| $19.48/$19.54).
Re-measured: **RT max $261.35, 0 hours > $300** — bit-unchanged, as the finding's $138.65
max-affected bound predicts, so the claim survives its own instrument change. Coverage 0.9999 →
**1.0000** (the one NaN per market-year filled with the market's published value — an independent
confirmation of the repair's NaN accounting at HEAD). **2019 cannot exercise C3c**, the criterion
the frontier is declared on. Second live reason unchanged: the **Pilgrim** fleet-vintage gap
(~2.18 TWh), the **cross-ISO charter's**, a hard precondition, not a NEISO lane item. **The stale
clause neiso-95 flagged is now measured false at HEAD rather than withdrawn by argument** and is
**still left unedited**: the `complete` entry's `locked_test` claims "2019 is UNSOLVABLE at HEAD
(`eia_demand_profiles.parquet` carries NEISO 2021-2025 only)". The premise about that *fallback*
file is true, but the **primary** path resolves —
`eia930.frames._eia_hourly_frame('ISNE', y)` returns **8,760 rows for 2019/2020/2021/2022/2023**.
The conclusion it supports is unaffected. Flagged for the owner, second session running.

**H1-2026 half — still NO, and the blocker is NOT NEISO's.** The partial-year gate is live at HEAD,
measured directly: `_eia_hourly_frame('ISNE', 2026)` returns **None**, `ISNE_region.parquet` holding
13,460 rows for 2026 against 35,040 for a full year against `len(df) != HOURS_PER_YEAR`. Shared
code, blind to ISO — **the model cannot build a partial-year solve for anybody**. neiso-96's
recommendation to **SPLIT** the block stands unchanged; the split, like the grant, is the owner's.

**The ladder now runs entirely on the repaired instrument — and a 2022 re-iteration is NOT worth
requesting.** The corrected 2018–2023 SMD instrument covers every ladder year (2020/2021/2022), so a
future authorized touchpoint iteration measures against the repaired series. The like-for-like
caveat is real — the standing `2026-08-06-neiso-2022-corrected-basis` was scored pre-repair — but
the repair **provably cannot move its determination**: 2022's max affected cell is **$138.65**
against the $300 threshold so the 117-hour actual tail is bit-identical (`actual_tail.json`
byte-unchanged); 47 of 8,760 RT cells move, bounding the annual-mean effect at ~$0.06/MWh and
measured at ≤ $0.008; and neiso-97 measured the model side bit-identical. A re-iteration would
reproduce the standing record essentially by construction, at the cost of an owner lift, a
three-year solve and a registration. **Recommendation: reserve the next 2022 spend for after a
change that actually moves the model side** — settling O5 and the Stony Brook routing in one
re-solve. Worth recording for whoever plans it: **of the whole ladder only 2022 exercises C3c
decisively** (117 RT hours > $300); 2021 offers 2 and **2020 offers none at all** — 2020 is
C3c-degenerate in the same way 2019 is, which neiso-96 did not report.

### Escalations re-measured at HEAD — both OPEN, and O5 is now SHARPER

**(i) O5.** Measured on all six designated keepers' own `meta.json`: CAISO `caiso-197`, ERCOT
`ercot213`, MISO `miso-160`, NYISO `nyiso-140`, PJM `pjm-162` all `commitment=false` / `passes
["P1"]`; **NEISO `commitment=true` / `passes ["P1","P2"]`** — still the sole ISO of six, neither
resolved nor worsened across three keeper generations. The pass-identity result above adds the part
that bites: **the registered payload, and therefore every published NEISO number and the scored
determination, is rendered from P2**, the archived pass CLAUDE.md says no keeper uses. Materiality
small on the means (+0.058 / +0.011 / +0.038 $/MWh) but **+18 % on the 2024 annual maximum**
($218.24 → $256.93), a price-formation statistic. Resolving it needs a re-solve decision — the
owner's — best settled together with (ii) so the two are not confounded. **(ii)** plant **6081**
Stony Brook units **004/005** still route to `plant_group=CC_REGULAR`, **74 rows each**, unchanged.
**(iii) NYISO disclosure LIVE, and RE-POINTED**: the neiso-97 finding filed it against
`2026-08-08-nyiso-133-cod-arm`, but NYISO has promoted twice since — the current keeper
`2026-08-16-nyiso-140-layup-exclusion` still carries `nyiso_import_hub_prices=true`, so it still
prices its ISONE_tie tranche off the repaired NEISO DA hub series. **Rule 25: filed, not acted on —
NYISO's call.**

### One text defect reported, deliberately NOT repaired

All **7** entries of the NEISO keeper's exceptions ledger open with *"CARRIED FORWARD from the
incumbent keeper unchanged in substance. **caiso-159** promotes an INPUT CORRECTION with zero free
parameters…"* — a CAISO session attributing NEISO's carry-forward. The **substance is true of
neiso-97** (it is precisely an input correction with zero free parameters and spent no new slot);
only the attribution is wrong. Traced to `scripts/archive/gen_caiso159_attestation.py`; present at
HEAD in the keeper attestation (7×) and `status/NEISO.js`; entered the NEISO lane **no later than
neiso-95** (`edca6f5`), so it predates neiso-97, whose generator carried the ledger **verbatim and
asserted that it did** — correct behaviour. The 2022 touchpoint's attestation is clean. **Not
repaired**: the attestation records what was asserted at promotion, and editing it retroactively
would falsify that record. It changes no number, criterion or determination. Reported for the owner
— the posture neiso-95 took with the `locked_test` clause.

### No run, by design

Text and stamps only (`keepers/NEISO.json` two leaves — `frontier.reverified` and
`carried_forward_through`, 18 of 20 leaves byte-identical and key order preserved; `status/NEISO.js`
rebuilt; this log; audit row O5). Nothing here can change a solve. Rules 15/16 not engaged. Rule 28:
no mechanism was tested and no cell verdict moved, and the NEISO matrix shard's keeper/gates stamps
already read `2026-08-17-neiso-97-dstrepair` (rule 28d).

**Next shorthand: `neiso-99`.** No NEISO tuning lever is open — the frontier is declared and now
re-verified on its own artifacts; DO-NOT-REDO applies to every `R`/`I`/`G` cell in the NEISO matrix
shard. Further C3c work needs a NEW measured identification and its own charter; **this session
found none it could name from committed artifacts and therefore requests none.** The lane's standing
items are the **two owner escalations** (O5, now sharpened, and the Stony Brook 6081 routing), best
settled together in one re-solve. **Not NEISO lane items:** the partial-year solve gate (six-ISO),
the fleet-vintage/Pilgrim charter (cross-ISO), the `_dual_fuel_plant_groups` vintage seam, the
`complete`-entry stale clause and the ledger attribution defect.

## 2026-08-17 — neiso-99: BOTH standing owner escalations CLOSED in one re-solve — the keeper moves off the archived P2 pass (audit row O5) and the Stony Brook 6081 outage routing is repaired; determination UNCHANGED, no gate traded

**New keeper `2026-08-17-neiso-99-joint-p1`**, superseding `2026-08-17-neiso-97-dstrepair`
(superseded-not-retracted). Two arms registered (rule 15), both `--year 2023 2024 2025` in ONE
invocation (rule 16), years sequential (rule 12), both at the same HEAD. Prereg
`results/calibration/PREREG-neiso99-p2basis-routing-2026-08-17.md`, pushed **before either arm
solved**. Full record: `results/calibration/ASSESSMENT-neiso99-p2basis-routing-2026-08-17.md`.

**The two defects, settled together so they could not be confounded** (exactly as neiso-98 §4
recommended):

1. **O5 — the keeper was SCORED on the archived P2 pass.** NEISO was the only ISO of six; neiso-98
   proved the registered payload was *rendered from* P2. Three keeper generations carried it with
   no operator decision anywhere, because `run_replay_bundle` / `replay_keeper.main` rebuild kwargs
   from `meta.json` **after** the CLI's P2 gate runs on parsed args. The keeper now persists
   `["P1"]` alone; `enforce_legacy_p2_kwargs` gates the **reconstructed** recipe at both entry
   points and **hard-fails** rather than silently rewriting it.
2. **The Stony Brook routing defect** (filed open by neiso-83, re-confirmed at HEAD by -95/-96/-98).
   `_resolve_unit_group`'s `fac_group` short-circuit — a pjm-75 conservatism, not a physical claim —
   handed plant 6081's two **Diesel Oil** combustion turbines (83 MW each, 74 windows each) to the
   `CC_REGULAR` bin, derating a **305.1 MW combined cycle they are not in** for **48.7 % of the 2024
   and 56.0 % of the 2025 capacity-year** — years in which the CC units 001/002/003 have **no
   windows of their own at all**. 1595 Kendall S6, 568 Bridgeport BHB4 and 1588 Mystic MJ-1 the same
   way; 236 rows removed.

**The discriminator is measured, and the measurement stopped a much worse fix.** Routing on
`unitType` alone would have been wrong: across all six ISOs' committed extracts, **35** CAMPD units
filed "Combustion turbine" sit in a non-CT bin and **27 are gas-fired members of a genuine block
that must keep inheriting it** (Sand Hill SH1–SH7, Colorado Bend, Glenarm, Zeeland, Ravenswood,
Bethpage). The guard is conjunctive on `unitType` **and** the unit's own liquid-only
`primaryFuelInfo` — it selects exactly the 8 real peakers and none of the 27. **Zero free
parameters** (a predicate over a closed CAMPD fuel vocabulary).

**Extract diff, accounted to the row:** 3,189 → 2,932, **0 added**; 257 dropped = **236 the fix** +
**21** reclassified standard→layup in 2019/2020/2026 only, the latter reproduced by a **pre-fix
control re-derivation at HEAD** and therefore ambient drift. All 2,932 survivors byte-identical on
every column; **within 2023–2025 the only change is the 236 rows**. The BLOAT-S2-untracked CAMPD
**2018 vintage was re-fetched first** per the corpus README (5/6 states byte-identical to
`SHA256SUMS`; `CT_2018` carries an EPA revision).

**The movement is decomposed, not conflated.** Arm A `2026-08-17-neiso-99-basis-p1` (PROBE,
basis-only, solved on the pre-fix extract via a `MARKET_SIM_DATA_ROOT` shadow root) is
**BIT-IDENTICAL to the superseded keeper's own persisted P1** in `system` / `class_hourly` /
`reserve_family`, all three years — **0 differing cells of 192,720 rows per year**. **P2 never fed
back into P1; it was only ever what got published.** Basis leg: mean λ −0.0575 / −0.0110 / −0.0378
$/MWh and the **2024 annual maximum $256.93 → $218.24** (P2 stood **+17.7 %** above P1 on that
price-formation statistic — reported at full magnitude, not tuned around). Routing leg: a further
−0.0162 / −0.0133 / −0.1112 $/MWh with the annual maxima **unmoved**.

**One pre-registered expectation is REFUTED and recorded as such.** P3 predicted the routing arm
would be driven by Stony Brook and would *raise* `CC_REGULAR`. It is driven by **Kendall**, and
`CC_REGULAR` **falls** (CC_CHP +0.0532 / +0.0644 / +0.0221 TWh against CC_REGULAR −0.0535 / −0.0605
/ −0.0026, CT_PEAKER −0.0014 / −0.0035 / −0.0193). Reason, already on this lane's record: 6081's
heat rate **10.6062** sits above **97.5 %** of NEISO's `CC_REGULAR` capacity (cap-weighted p50
7.340) — deep out of merit whether available or not, the same fact neiso-83 measured at the same
plant. Restoring an expensive block changes its **availability**, not much of its **dispatch**.

**Determination UNCHANGED at CALIBRATED-WITH-CAVEATS**, criterion for criterion identical to the
superseded keeper (0 FAILs, C3c the sole ledgered caveat, C1 all 12/12 · free 8/8, grade 8/7/0/1/0),
re-verified per rule 22 D-5(b) on committed artifacts **before** the re-key landed. **NO GATE WAS
TRADED** — and the prereg had declared in advance, with the model already *below* actual mean λ in
all three years, that a C3a/C3b degradation was expected and would be **accepted** under rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]`; in the event none had to be. `audit_keepers.py --iso NEISO`:
**PASS, 0 failures / 0 warnings**.

**Frontier RE-ESTABLISHED on the new keeper's own sidecars** (`neiso99_declaration_recheck.py`,
which imports neiso-98's helpers verbatim so the pinned tail definition is shared) — **mandatory**,
because unlike every NEISO keeper change since neiso-93 this one is *not* a dispatch no-op. C3c
model tail **0 h > $300/MWh in all three years on the now-sole P1 pass**, agreeing with the
payload's `ordc.hoursGt200.model` 0/0/0 vs RT actuals 15/8/20; annual maxima 248.9682 / 218.2412 /
280.8542, closest approach short by **$19.15** — **bit-unchanged** from the superseded keeper's own
P1, so **no C3c evidence moved in either direction**. RCPF co-optimization **DORMANT** in all
**78,840** family-hours at the published statics (1,800 / 1,200 / 600 MW), `|dual|` max **exactly
0.0** — the prior keeper's 1.42e-14 residue was P2's own degeneracy noise and left with the pass.
**No C3c lever was opened** (rule 28a).

**Rule 22:** no out-of-training year solved, scored or registered; the spend freeze stays **ACTIVE**
and was never engaged; the measured-input repair is applied to every year consistently. NEISO's
locked test remains **NEVER GRANTED and NEVER SPENT**. No 2022 re-iteration requested.

**Filed for other lanes, NOT acted on (rule 25 `[R-ISO-SCOPE]`):** the same guard would drop
mis-routed liquid-fuel CT rows at **PJM** 593 Edge Moor 10 (33 rows), **MISO** 2001 New Ulm 7 (114)
and 8056 Waterford 4 (103), and **NYISO** 2516 Northport UGT001 (42). Only NEISO's extract is
re-derived here. **Not a NEISO item, reported in passing:**
`scripts/check_registry_payload_parity.py` fails at HEAD on `results/calibration/ercot215_control_A`
(bundle mapping to no retained sidecar) — the ERCOT lane's.

**Audit row O5 is CLOSED**; the neiso-83 Stony Brook root-cause issue is CLOSED.

## 2026-09-06 — neiso-102: the status card was showing 2022 TWICE with different determinations — the stale hand-authored `holdout_touchpoint` is removed and the class is guarded (E12). ZERO LP minutes; no verdict moved

*(The log skips neiso-100/101; both filed ASSESSMENTs under `results/calibration/` — the
declaration re-assessment and the 2019 input-preparedness audit — and neither promoted or solved.)*

**Two defects, one live and one latent. Nothing solved, scored, registered or promoted; no mechanism
tested; no matrix cell verdict moved.** Full record:
`results/calibration/FINDING-neiso102-holdout-records-integrity-2026-09-06.md`.

### A — the contradiction on the live card

`keepers/NEISO.json` carried a hand-authored `holdout_touchpoint` naming
`2026-08-06-neiso-2022-corrected-basis` — **pruned** on 2026-09-05 under the ercot-248 keeper-only
retention directive (rule 15) and superseded on the same year by the registered
`2026-09-05-neiso-2022-touchpoint-k99`, whose sidecar declares `supersedes` on it.
`build_status.py:574` copies the block through **unvalidated** and `calibration-status.js:406`
renders it, so the live Calibration Status card printed 2022 twice:

| Panel | 2022 determination | Run link |
|---|---|---|
| hand-authored `holdout_touchpoint` (printed FIRST) | `CALIBRATED-WITH-CAVEATS` | **dead — absent from registry** |
| derived `holdout_ladder` | **`CALIBRATED`** | live |

Worse than a dead link: neiso-100 (`_neiso100_touchpoint_staleness.json`) had already measured that
run's recipe as diverging from the current keeper on **4 of 7 data axes**, so the block quoted a
result taken on a *different recipe* than the keeper it sat beneath.

**Removed, not re-authored** (rule 30 `[R-TOUCHPOINT-FOLD]`(b) — "never hand-author a block that
would go stale the moment a rung is re-spent"), and the status part rebuilt. The derived ladder
strictly dominates it and now stands alone: **2020 `NOT-YET`** (price_mean), **2021 `CALIBRATED`**,
**2022 `CALIBRATED`** (C3c ledgered, rubric v3.6) — per-year, each naming a live run.
**NEISO was the LAST of the six ISOs carrying such a block**; PJM's went one day earlier
(pjm-166, `3001f913`), and the other four never had one.

**Rule 30(c): the ISO's determination is UNCHANGED at `CALIBRATED`** — the train-tier (2023–2025)
verdict, which a held-out year never moves. The `NOT-YET` 2020 rung beside it is not a contradiction.

### B — the detection gap, and why the obvious guard was wrong

`audit_keepers.py` was **structurally blind**: `grep -c holdout_touchpoint` at HEAD → **0**. Genuine
gap, not a re-check of E1/E6/M1.

The chartered guard — "every shard-referenced run id must exist" — **would have redded `main`.** A
census found **19 dangling structured ids, and 18 are historical citations pruned BY DESIGN**:
ERCOT's `config_partition.configs[].source_run_id` ×2, and NYISO's `de_designation_history`,
`frontier_withdrawn_*` and a 10-deep `superseded…chain.former_keeper` genealogy. NEISO's own
`site_retention_note` states the posture: *"citations … may now point at runs no longer on the site —
deliberately … NOTHING IS RETRACTED."*

So **E12** is scoped to what the SITE RENDERS AS A LINK, derived from the render sites rather than
hand-picked: `config_partition.configs[].run_id`, `holdout_touchpoint.run_id`,
`standing_note.probe_run_id` (`keeper` is E1's already). Genealogy and prose are out of scope
permanently and on purpose. A regression test pins the scope against `calibration-status.js` so a
newly-rendered pointer cannot silently re-open the hole. **E12 fires on the pre-fix NEISO shard only
(1 finding) and is clean on all six post-fix**; it lands AFTER the fix in the same commit because CI
runs the audit across every ISO.

### Records & verification

`keepers/NEISO.json` (−22), `status/NEISO.js` (rebuilt), `calibration-complete.json`
`complete.NEISO.site_retention_2026_08_09` (**dated append; 0 keys added, 0 removed, pure**),
`scripts/audit_keepers.py` (+E12), `tests/scoring/test_audit_keepers_pointers.py` (new, 9 tests).
The `complete` append closes two now-stale claims: the "same keeper recipe on 2022" run is itself
pruned, and the "single combined 2022-2025 bundle NOT yet done" is **MOOT** — rule 30(a)'s fold
delivers that reading with no combined solve, and the freeze has named `scope.tiers=['locked_test']`
alone since 2026-08-26. Its pointer names `status/NEISO.js` as the ladder's home, **not** the shard
(pjm-166's auditor pass wrote the latter and needed `e7f990bd` to correct it).

`audit_keepers --check` unscoped **PASS 0/0**; 9 + 53 tests pass; parity OK (14 runs / 47 bundles);
mechanism-matrix guard exit 0; `scripts/audit_keepers.py` blob re-fetched from GitHub and verified
byte-identical at 1109 lines (rule 27).

**Next shorthand: `neiso-103`.** No NEISO tuning lever is open — the frontier is declared and the
training window is done at zero failing criteria; DO-NOT-REDO applies to every `R`/`I`/`G` cell in
the NEISO matrix shard. The 2020 `NOT-YET` rung is **reported, not chased** (rule 30(c)); whether
2020's inputs are as prepared as 2021/2022's is a phase-0 question this session did not open.
`final` remains **NEVER GRANTED** for NEISO and NOT YET on the merits.

## 2026-09-06 — neiso-103: 2020's inputs ARE at parity — the rung's lone C3a FAIL is a relative-band DENOMINATOR effect, not a readiness shortfall. ZERO LP minutes; no verdict moved

**Phase 0 only. Nothing solved, scored, registered or promoted; no mechanism tested; no matrix cell
verdict moved; keeper shard untouched.** Full record:
`docs/handoffs/FINDING-neiso103-2020-input-readiness-2026-09-06.md`.

The lane question (opened, not answered, by neiso-102): is NEISO's 2020 input set as prepared as
2021's and 2022's? **It is — on all 24 keeper-consumed input families, at parity or better.** The
audit is a discriminating one by construction: 2020 and 2021 were solved in **one bundle, one
frozen recipe, one HEAD** (`2026-09-05-neiso-2020-2021-touchpoints`, `6619fb4a`) and diverge in
verdict, so an input equally degraded in both cannot explain the split. **Nothing was found that is
short in 2020 and not in 2021.** Three families are *richer* in 2020 than in-sample: F923 delivered
fuel (50 rows vs 27/27/32), `plant_emission_rates_v2` (189 vs 174/162/156), parasitic-factor
coverage (100 % vs 99/99/100 %).

### A — the rung's `NOT-YET` is the denominator

C3a is a pure ±10 % *relative* band (`score_price_mean` → `err = _pct(model, actual)`;
`PRICE_MEAN_TOL = 0.10`), with no absolute-dollar floor. On absolute error the two rungs rank the
other way round:

| year | tier | model | actual RT (lw) | **abs err** | rel | C3a |
|---|---|---:|---:|---:|---:|---|
| **2020** | touchpoint | 28.59 | 25.14 | **+3.45** | **+13.7 %** | **FAIL** |
| **2021** | touchpoint | 52.11 | 47.77 | **+4.34** | +9.1 % | PASS |
| 2022 | touchpoint | 90.60 | 91.15 | −0.55 | −0.6 % | PASS |
| 2023/24/25 | keeper | 39.29/44.04/71.39 | 38.10/41.68/70.23 | +1.19/+2.36/+1.16 | +3.1/+5.7/+1.7 % | PASS |

**The year that FAILS is closer to its actual, in dollars, than the year that PASSES.** 2020's
+$3.45 would PASS at all five other years' price levels; 2021's +$4.34 would FAIL at 2020's
(+17.3 %). Swap the price levels and the verdicts swap. 2020 misses by **$0.94/MWh** ($3.45 against
the $2.51 that ±10 % allows on a $25.14 base — the cheapest year in the record).

**The score is not challenged and rule 30(c) is untouched.** `NOT-YET` stands; the band *is* the
certification claim. What is retired is only the *inference* that 2020 is worse-prepared or
worse-modelled than the rungs that pass. NEISO's headline remains the train-tier verdict,
**CALIBRATED**.

### B — the two structural candidates, both cleared by internal controls

**Year-agnostic fleet statics** (`thermal_tranches_NEISO.csv` / `bin_assignments_NEISO.csv`; deriver
default `--years 2024`, committed vintage recorded UNKNOWN). Share of each year's actual CAMPD
generation they cover: 2019 90.35 / **2020 91.58** / 2021 93.80 / **2022 91.72** / 2023 94.80 /
2024 95.51 / 2025 97.08 %. **2020 and 2022 are twins, and 2022 scores `CALIBRATED` with C3a at
−0.6 %** — so the statics' vintage cannot be what fails 2020. The uncovered mass is dominated by
plant 1588 in *every* year, in-sample included. NEISO coal points the wrong way too: 0.32 % of CAMPD
generation in 2020 against 1.14 % in 2021, both far under rule 19's 2 % floor.

**`eia_demand_profiles.parquet` holds zero NEISO rows for 2019–2020** (the register grades this
MISSING/HIGH, "no dispatch is possible"; the pjm-160 block claims it CLOSED). Neither is operative
for NEISO: `load_demand` resolves `DEMAND_LOADERS['NEISO']` **first**, so the parquet is never
reached in any year. `_load_neiso_hourly_demand` returns a clean 8760 for 2019–2025 (2020 mean
13,161 MW, 1.6 % below 2021 — the COVID depression, present because the demand is measured). Graded
**INERT**, not missing.

### C — a probe that failed, a control that killed it

Recorded because it nearly became a finding. `load_renewable_profiles('NEISO', 2020, …)` raises
`ValueError: No EIA-930 data for ISO 'NEISO' in year 2020`, and `eia_generation_profiles.parquet`
really does hold 0 rows before 2021 for all six ISOs; it reproduced with the keeper's own 794-field
config, and `git log 6619fb4a..HEAD` shows `renewables.py` / `data/eia930/` unchanged since the
solve. **The control:** the identical raise occurs for **ERCOT 2020** — an approved
`WEATHER_YEAR_POOL_BY_ISO` year — and ERCOT 2023 returns the hardcoded `RENEWABLE_INSTALLED_MW`
constants (42,000/38,000 MW), i.e. `_eia860_monthly_capacity` returns `None` for every ISO/fuel in
this checkout. The probe measured the environment, not the model. **Settled on output evidence
instead:** the committed 2020 bundle matches measured EIA-930 ISNE to −0.3 % wind / −0.3 % solar /
−0.2 % nuclear. (neiso-102's test-quality lesson, inverted: a probe that *fails* also needs its
negative control before it is written down.)

### D — records

Dated correction block appended to `docs/holdout-data-equivalency-register-2026-07.md` §NEISO
(existing rows left as the historical record, per that file's own convention): five NEISO rows are
stale at HEAD, all in the closed direction — driver-demand model profile (still absent, now graded
INERT), `calibration_reference` (2019–2025 all present), `NEISO_<year>_renewable_capacity.csv`
(120 rows every year), `actual_tail` (2020–2025 present), Algonquin daily basis (45 prints in 2020,
in family with in-sample 30–49).

**Noted, not acted on:** this session's own handoff prompt states NEISO 2019 is unsolvable partly
for "no demand rows before 2021" — contradicted by `ASSESSMENT-neiso101-2019-input-prep-2026-08-18.md`
(*"`load_demand("NEISO", 2019)` returns a full `(5, 8760)` array"*), by this session's measurement,
and structurally by 2020 having solved with the same partition absent. **Nothing follows**: NEISO's
`final` readiness is owner-closed on other grounds, and the locked test is frozen for every ISO
(`scope.tiers = ['locked_test']`).

**Next shorthand: `neiso-104`.** No NEISO lever is open. The 2020 rung is **closed as an
input-readiness question** — do not re-audit it. The one object the audit surfaced is a level bias,
not a 2020 one: the model runs high in **5 of 6 years, mean +$1.99/MWh**, present at
+$1.19/+$2.36/+$1.16 in 2023/2024/2025. If it is ever worked it is an **in-sample** object, which is
where rule 22 step 3 requires the fitting to happen. This session opens nothing.

## 2026-09-06 — neiso-106: the fossil offer-level scalar RE-DERIVED on the measured full-span pass-through — keeper → `2026-09-06-neiso-106-fossil-offer`, CALIBRATED, and the rule-29 screen-year defect is PROVEN with a receipt

**One full-span LP invocation (2023 · 2024 · 2025) plus the 2020/2021/2022 touchpoints. No screen,
no control solve.** Full record:
`results/calibration/FINDING-neiso106-offer-level-rederived-2026-09-06.md`; pre-registration
`PREREG-neiso106-offer-level-rederived-2026-09-06.md` (committed `773411e5`, **before the solve**);
governance addendum `ADDENDUM-neiso106-prereg-collision-2026-09-06.md`.

### A — what moved

The scalar on the 12 fossil markup bands, **0.93391 → 0.95470** (a 6.609 % cut → **4.530 %**), and
nothing else: same channel, same bands, same target, same recipe. **Only the coefficient in the
sizing division changed** — from the pass-through the neiso-104 screen measured on **one year**
(0.5247, 2025) to the **full-span 0.76550** measured directly off the superseded keeper's own three
in-sample price moves. The target is the same **+3.4678 %** in-sample geometric-mean price bias
fixed in `PREREG-neiso104` §3.1 before any LP ran (reproduced here at 0.034674, and still divided at
the declared value). `0.034678 / 0.76550 = 4.530 %`.

### B — the landing, pre-registered before the solve and hit to 0.02 pp

| year | pre-cut | superseded keeper | **this keeper** | pre-registered |
|---|---:|---:|---:|---:|
| 2023 | +3.131 % | −3.361 % | **−1.338 %** | −1.319 % |
| 2024 | +5.664 % | −0.019 % | **+1.764 %** | +1.768 % |
| 2025 | +1.647 % | −1.893 % | **−0.769 %** | −0.779 % |

In-sample geometric-mean bias **−1.767 % → −0.124 %** (pre-registered −0.119 %); MAE
**1.758 % → 1.290 %**. Against the pre-cut neiso-99 basis: **+3.467 % → −0.124 %** and
3.481 % → 1.290 %.

**Determination `CALIBRATED`, criterion for criterion identical to the superseded keeper** (0 FAILs;
C1 all 12/12 · free 8/8; C2/C3a/C3b/C4/C6/C8 PASS; C3c the same lone ledgered caveat), D-5(b)
re-verified on committed artifacts before the re-key. **The PREREG's named live risk did not fire**:
C3b price duration/shape PASSES, as the bracketing argument expected — 0.95470 lies strictly between
two configurations that both scored C3b PASS on these same three years.

### C — the finding, which outlives the scalar

**Pass-through is YEAR-dependent, tracking delivered gas inversely and monotonically** — 1.3055 at
$1.98/MMBtu (2020), 0.9525 at $2.93, 0.8138 at $3.07, 0.7061 at $4.50, 0.5269 at $6.24 (2025),
0.4126 in 2022: a **3.2× spread**. **It is NOT depth-dependent**: 2025, the only year solved at two
cut depths, reads 0.5254 at 4.53 % against 0.5269 at 6.609 %, ratio **1.0029** over a 46 % change in
depth — which refutes the depth-linearity hazard `PREREG-neiso105` §3 named.

**Rule 29 `[R-SCREEN]` selects the screen year by largest absolute footprint**, which for a
multiplier on `HR × fuel` is the highest-gas year, which is the **lowest** pass-through year. **The
receipt**: neiso-104 declared 0.765 from an across-year gas elasticity and recorded that
identification **REFUTED** when its 2025 screen measured 0.525; the full-span figure is **0.7655** —
right to within 0.07 %. What was wrong was reading a one-year screen as a measurement of the span.
**Filed as an owner ask (`PREREG-neiso106` §7); no rule was amended by this lane.**

**Bit-level cross-check, found in the solve log rather than looked for:** this arm's 2025 solve is
**bit-identical** to the neiso-104 screen arm that rule 29(c) required deleted — P0 objective
3,554,608,783.6457 to 13 significant figures, 188,740 / 59,473 simplex iterations on both passes —
despite four package-version deltas. It reconstructs a deleted result inside a registrable bundle
and upgrades `ADDENDUM-neiso104-env-correction`'s "4 dp on load-weighted price" to bit-identity on
the LP itself.

### D — governance, stated rather than assumed

This is the **third** sizing of this scalar (4.53 % → 6.609 % → 4.530 %), and `PREREG-neiso105` §3
pre-committed it would not move again in either direction. That lane-level stop rule is **overridden
by owner direction, not reasoned away** — though neiso-105's own matrix stamp had already drawn the
line, calling a full-span re-derivation *"legitimate (the target never moved)"* and only a resize
against the gates illegitimate, which is the side this lane is on. `PREREG-neiso106` §6
**pre-commits this as the third and LAST sizing**: the coefficient has now been measured on the full
span at two depths, so no fourth is legitimate in either direction; a further miss is reported and
the next move is structural.

G-CTRL form 4 with **no control LP spent**, validated by a G-DRIFT audit run before the arm (keeper
sha `8b2c890d` **asserted** to resolve — the clone is shallow and an unresolvable anchor makes
`git diff` silently report no drift — and all 12 changed solve-path files classified INERT).
Ledgered as **one** DOF free parameter under rule 21 `[R-DOF]` / owner ruling R-AY, identification
source the **ruling**. No `ScenarioConfig` default moved; no other ISO touched.

### E — holdout

The 2020/2021/2022 validation touchpoints were re-run on the **frozen, already-promoted** recipe and
re-stamped to the keeper (rule 30(a)/(b), run `2026-09-06-neiso-106-touchpoints-2020`) — **nothing is
fitted to a held-out year**: the scalar was identified on the 2023–2025 in-sample bias alone and
promoted before any touchpoint was solved (rule 22 step 3/4).

| year | pre-cut | superseded keeper | **this keeper** | **predicted before the solve** | C3a |
|---|---:|---:|---:|---:|---|
| 2020 | +13.707 % | +3.897 % | **+6.964 %** | +6.983 % | PASS |
| 2021 | +9.079 % | +3.989 % | **+5.588 %** | +5.590 % | PASS |
| 2022 | −0.601 % | −3.311 % | **−2.466 %** | −2.458 % | PASS |

**All three land within 0.02 pp of a value predicted from that year's own measured pass-through
before the LP ran** — the same accuracy the in-sample years showed. **All six years 2020–2025 now
PASS C3a**, and the bundle scores `CALIBRATED` with **0 degraded criteria** against the in-sample
column (7 held, C3c carried). That is the strongest evidence this session produced that the
coefficient is a **measured physical response and not a fitted one**: the per-year model is
predictive *out* of the training window at in-sample accuracy — six years, one config, six hits —
which the training years alone could not have shown. The superseded touchpoint runs are **pruned**
under rule 15 keeper-only retention. Rule 30(c) untouched: NEISO's determination is its train-tier verdict, and a
held-out year can neither certify nor decertify it. **The touch-once locked test (2019 / H1-2026) is
UNTOUCHED and remains frozen for every ISO.**

### F — what this does NOT close

C3c is untouched and remains the lone ledgered caveat at the same magnitude (model 0 h > $300/MWh
vs RT actuals 15 / 8 / 20 h); the 2026-07-11 frontier designation stands, and nothing in a markup
scalar can reach a scarcity tail. The diurnal price amplitude gap is unchanged and large
(26.4 / 22.4 / 32.7 % of measured hod range, band-free/reported-only under v3.5) — a level scalar
cannot move a shape. Two diagnostic rows got **worse** and are disclosed in the FINDING §3 rather
than left in a JSON file: a D-4 off-window row at 26 MW plant 54605 worth **0.0001 TWh**, and three
D-2 forced shares that all moved *toward* their caps; C8 still PASSES because every class involved
is immaterial under rule 20's own 2 %-of-load floor, and the D-4 row is not worked because working
it would be chasing four parts in a billion. **And one defect was found that is NOT NEISO's to
fix and was NOT fixed**: the Calibration Status **per-year ladder** renders `NOT-YET` on every year
of both NEISO's *and MISO's* `CALIBRATED` keepers, because `build_status.build_years` scores each
year in isolation and the rule 1(b) `years_held` exact-set check is then compared against a
one-year *display* subset. The check is right; the caller is asking a run-level question about one
row. It is **pre-existing** (identical at the neiso-105 promotion on `main`), it leaves every
run-level determination correct, and its fix lands in the shared scorer and would change MISO's
published page — which a NEISO lane must not do (rule 25 `[R-ISO-SCOPE]`). Escalated with a
measured blast radius and a proposed one-line fix in
`results/calibration/FINDING-neiso106-per-year-ladder-governance-defect-2026-09-06.md`.

**Next shorthand: `neiso-107`.** No NEISO lever is open, and **the offer-level lane is CLOSED by its
own pre-committed stop rule** — do not re-size this scalar. The live objects are unchanged: C3c
(frontier declared, needs a new measured identification and its own charter) and the diurnal
amplitude gap (needs its own charter; see the neiso-76 adjudication before proposing anything).

## neiso-108 — 2026-09-09 (session `neiso-fuelvintage-1`)

**KEEPER PROMOTED → `2026-09-09-neiso-108-fuelvintage`, DETERMINATION CALIBRATED.** Two changes
promoted on the **owner ruling of 2026-09-09**, verbatim: *"these should be promoted as keepers on
both 860 and gas shape counts regardless of inertness."* (a) `gas_electric_power_monthly_level`
→ `True` — the one config delta against neiso-106; (b) the flagless 2019-2022 retiree-window
widening (`RETIREMENT_WINDOW_START` 2023 → 2019, commit `7934e92c`) that reached `main` under it.
**Zero new free parameters.** The neiso-106 `authorized_price_tuning` declaration (0.95470 on 12
`offer_curve_by_group` markup bands) is carried forward **unchanged** — neither re-sized nor
re-swept, and the offer-level lane stays closed by its own stop rule.

**THE SESSION'S HEADLINE IS A ZERO-LP RESULT, NOT THE PROMOTION.**
`docs/FINDING-neiso-index-vs-delivered-gas-2026-09-09.md` closes the one cross-ISO discrepancy the
fuel-vintage program had not resolved. NEISO's 3.24× January-2023 gap between the ISO-NE published
Algonquin index ($4.73/MMBtu) and the EIA `N3045` MA/CT/RI/ME/NH blend ($15.35) is a
**measurement-basis gap** — an average delivered cost including transportation and
contract (LNG) charges versus the marginal commodity price — falsified **physically** as a marginal
price: across 84 months
(2019-01…2025-12) the implied marginal heat rate (monthly mean ISO-NE hub RT LMP ÷ gas price) never
once falls below **7.99** MMBtu/MWh on the index, while the N3045 blend drives it below NEISO's
**6.3** CC floor in **13 of 84** months and to **3.29** in Jan-2023 — a ~104 %-efficient heat
engine. Four corroborations: N3045 prices Jan-2023 and Jan-2025 the same (15.346 vs 15.316) while
the market priced them $50.51 vs $135.08/MWh and gas ran *harder* in the cheap month (49.3 % vs
46.8 % share); the Algonquin daily prints read $3.22-4.23 for four weeks of Jan-2023; the entire
MA/CT dispersion inside one month reaches **4.13×** on the same pipeline, which the *commodity*
cannot do but an **average delivered cost** can (firm-transport charges and Everett LNG, and
Massachusetts is the state that prints high). **CORRECTED BEFORE PUBLICATION:** an earlier draft
called this a respondent-composition artifact on the strength of this repository's EIA-923
*extraction* holding one New England plant that month; the parallel session `neiso-107` measured
EIA's companion **volume** series `N3045<ST>2` at 1.6 % of the CAMPD-metered burn and refuted it,
and their metered leg reproduces **exactly** here (29,290,427 MMBtu). The verdict and every other
line of evidence are unchanged; the *mechanism* is corrected.
Log-price correlation with realised LMP: index **0.9324**, N3045 **0.8452**. **Consequence:** rule
14 `[R-ACCURATE]`'s misalignment exception is **earned**, not merely invoked — the hub index keeps
priority because it is the marginal series — and the 2.303 $/MMBtu "level gap" the cross-ISO table
reports for NEISO 2023 **measures the survey panel, not the model**. An ercot-261-style
corroborator is **recommended against** for NEISO and was not built.

**BOTH PROMOTED CHANGES ARE PROVABLY INERT ON 2023-2025** — measured at zero LP *before* the solve
(rule 29 `[R-SCREEN]` clause (0)), reported as a property of the result rather than as a reason to
withhold. The gas seam writes **0 of 22,837,320** fuel cells, and a full-payload sweep of all **38**
arrays `run_year(fleet_only=True)` returns (**38,518,653** numeric cells) finds **not one** that
differs — the LP is literally the same LP, so the scheduled LP screen was **cancelled, not
skipped**. The retiree window injects 59/59/61 rows carrying 1,696.374/1,696.374/1,697.490 MW of
nameplate at **exactly 0.0000000000** effective MW-h and moves **no** shared row's `pmax`,
`availability` or `mc_base`. **Charter task 3 discharged for NEISO at the input layer** — stronger
than the dispatch A/B the charter specified, and it was at real risk:
`FINDING-pjm-retiree-window-redistribution-2026-09-09.md` proved the "zero effect by construction"
claim FALSE for PJM (720 MW of May-2020 coal redistributed onto live siblings at W H Sammis) and put
NEISO's exposure at 521.5 MW (Mystic). **NEISO's realised leak is 0.0 MW.** Also verified per §A5
item 2: the whole-plant channel and `partial_plant_exit_carry` share **zero** (plant, unit) keys and
zero plants (69 vs 24 ISNE rows).

**HEAD DRIFT, REPORTED AT FULL MAGNITUDE.** The incumbent's `git_sha 70ee7fca` does **not resolve**
(the 2026-08-16 history rewrite) and its bundle predates capx D79, so rule 29(b)'s G-DRIFT audit
cannot be run literally — as the PJM lane also found. **No control solve was spent**, and none is
informative: the arm-vs-control comparison at HEAD is a proven identity across all 38 payload
arrays. So every difference against neiso-106's committed numbers is HEAD drift from other lanes,
and none is attributable to either promoted change: max |class-hour delta| 426.95 MW (2023) /
371.44 MW (2024), concentrated in `CC_REGULAR` and **hydro** (the budget-constrained flat-cost
variable whose intertemporal placement is a numerical tie); annual class energy moves ≤ 0.00067 TWh
on 52.7 TWh (13 ppm); mean |price delta| 0.0039 / 0.0055 $/MWh on means of 36.72 / 42.07; slack and
dump exactly 0.0 both sides. **Alternate optima of the same LP.**

**VALIDATION TOUCHPOINTS 2020 / 2021 / 2022** — `2026-09-09-neiso-108-fuelvintage-touchpoints`,
`--holdout-authorized` under NEISO's `complete` marker, stamped to the keeper under rule 30
`[R-TOUCHPOINT-FOLD]`. **CALIBRATED, and every criterion HELD** in-sample → holdout: C1/C2/C3a/C3b/
C4/C6/C8 PASS → PASS, C3c CAVEAT → CAVEAT (rubric v3.6). Per-year ladder: 2020 CALIBRATED, 2021
CALIBRATED, 2022 CALIBRATED. The retiree window is **live** here (+956.0 / +949.0 / +201.3 MW).
Rule 30(c): a held-out year never downgrades NEISO, and rule 22 makes these numbers iterable
selection evidence, never a certified out-of-sample skill claim. **This supersedes**
`2026-09-05-neiso-2022-touchpoint-k99` and `2026-09-06-neiso-106-touchpoints-2020`, both pruned.

**CHARTER TASK 4 DISCHARGED.** The standing `constants.py` caveat on
`NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` — *"a 2019 solve is short ~2.18 TWh of nuclear regardless of
this overlay"* — is **RETIRED, its premise now false**. `monthly_online_mask(1972, 12, 2019, 5, y)`
gives Pilgrim exactly **5** online months in 2019 and **0** in every year 2020+, and the committed
CF row applied to the restored **4,029.0 MW** Jan-May fleet lands at **13.042 TWh** against
EIA-923's **13.002 TWh** actual — **+0.040 TWh**, where the pre-fix 3,355.4 MW fleet was
**−2.140 TWh**. The row is left **unchanged** and needs no re-derivation; the +0.3 % residual and
the exact re-derived row are recorded in the constants comment for whoever eventually spends 2019.
**No 2019 solve, score or registration** — 2019 is locked-test tier, `final` empty, freeze ACTIVE;
every number is EIA-923 / EIA-860 data inspection plus the COD-ramp mask.

**Governance.** `complete.NEISO` re-keyed with its rule-22 D-5(b) determination re-verification
(CALIBRATED, not worse). Forecast gate-(a) stamp re-keyed **in this same session** (R-T / Q34).
Site retention swept to keeper + folded twin. **Inherited and named, not buried:** NEISO's
`perfb-stage0` golden captures `neiso99_joint_B` and was *already* stale against neiso-106; the
R-AI re-capture obligation applies to this lane and is **not** discharged here.

**Next shorthand: `neiso-109`.** No new NEISO lever is open. The live objects are unchanged — C3c
(frontier declared; needs a new measured identification and its own charter) and the diurnal
amplitude gap. **Do not re-open the index-vs-delivered question without new measured evidence: it
is adjudicated, with a physical falsification behind it.**

## neiso-107 — 2026-09-09 (session `neiso-fuelvintage-1`)

**Two deliverables: the gas index-vs-delivered gap SETTLED (zero LP), and the 2019-2022 retiree
window solved across the training span and the validation ladder.** Docs:
`docs/FINDING-neiso-gas-index-vs-delivered-2026-09-09.md` (the fuel investigation, read first) and
`docs/RESULT-neiso-fuelvintage-1-2026-09-09.md` (everything else).

### A — the index is right, and NEISO has no gas level gap

The xiso lane handed NEISO the one discrepancy the program had not resolved: for Jan-2023 the
ISO-NE published Algonquin index reads **$4.73/MMBtu** and the EIA `N3045` MA/CT/RI/NH/ME blend
reads **$15.35** — 3.2×, and the reason NEISO's series was recorded as **+2.303 $/MMBtu below
measured**, the largest level gap in the cross-ISO table. Settled by four independent zero-LP tests:

1. **Small-denominator hypothesis REFUTED.** The `N3045` *volume* series is **98.4 %** of
   CAMPD-metered burn (29.76 vs 29.29 million MMBtu, Jan-2023) and implies a **7.33-7.65
   MMBtu/MWh** fleet heat rate in every month of 2022-2024. `$15.35` is the average delivered cost
   of essentially *all* the gas the fleet burned.
2. **The index is corroborated** by an independent publisher (NGI daily AGT: $3.22-4.23 through
   Jan-2023, spiking 01-31).
3. **The market falsifies the delivered series as a marginal cost.** It implies a market heat rate
   below the **6.3 MMBtu/MWh** best-CC physical floor in **7 of 35 months** (Jan-2023: **3.29**);
   the index never once does (min 7.39). In dollars: the merchant fleet would have burned
   **$449.6M** of fuel in Jan-2023 to earn **$203.2M** of energy revenue.
4. **There is no model gap.** The keeper's gas series reproduces the published index in **73 of 84
   months exactly**. The 2.303 is a reference-choice artifact.

Both series are real and measure different things: `N3045` is EIA-923 Schedule-2 delivered cost
*including transportation* — an **average total cost** whose wedge over the index is
winter-concentrated (DJF mean +3.80, other months +0.83) — while the merit order prices the
**marginal** commodity. Rule 14 `[R-ACCURATE]`'s misalignment exception, now evidenced.

`gas_electric_power_monthly_level` proven **EXACTLY inert** (0.000000000 $/MMBtu, all seven years;
the hub overlay repriced **463/463** gas generators in **12/12** months). **SHARD F was cancelled.**
Matrix cell `O` → **`I`**. A NEISO copy of the ercot-261 corroborator is **recommended against**:
public EIA-923 gas receipts for 2023 are **2 municipal plants** in MA and **zero** in
CT/RI/NH/ME/VT — ~0.1 % of the fleet's burn (TX: 37 plants).

### B — the retiree window: registered, every band unchanged

`2026-09-09-neiso-107-retiree-window` (2023-2025) and `2026-09-09-neiso-107-holdout-touchpoints`
(2020-2022, `--holdout-authorized` under the `complete` marker). Both **CALIBRATED**, 8 scored /
0 fails / the same lone ledgered C3c — **identical to the incumbent keeper**. Zero free parameters.

Touchpoints vs the committed prior touchpoint bundle (G-CTRL form 4, no control solve): annual mean
price **falls −0.190 / −0.281 / −0.101 $/MWh**, 2022 immaterial (−0.0020 TWh; max hourly Δprice
4.31 vs 117.27 / 94.40) — both pre-registrations hold, and the charter's "large 2022 move is a BUG"
did not occur. `ST_GAS` **+333/+355/+142 GWh** against `CC_REGULAR` **−599/−307/−141 GWh`: the
restored steam and CT units (Mystic 7, Essential Power MA, Capitol District, Pawtucket) taking load
off the CC fleet. Stamped to the keeper; `build_status --iso NEISO` in sync; every criterion **HELD**.

### C — what this does NOT close

**Charter task 3's literal bar was NOT met and is reported, not waved through.** Max |class-hour
delta| vs the committed keeper is **426.95 / 371.44 / 442.34 MW**, not 0.000000. Root-caused: the
added units are dispatch-inert (all 44 read `cap_mw` 0.000 and 0.000 GWh in every training year,
and the 24 added plants are **disjoint** from the operable snapshot — ADDITION 1's overlap
assertion verified), `demand`/`slack`/`dump`/`reserve_price` are bit-identical, net class energy
moves **3e-9 to 3e-6** of the total and the annual mean price **1-3 parts in 100,000**, and
`hydro`'s net delta is **exactly zero** across 1,192 tied hours under its binding monthly budget.
That is **alternate-optimum reshuffling of a degenerate LP**. Two perturbation channels are
disclosed and deliberately **not separated by a control solve** (rule 29(b)): the 44 units enter
`FleetArrays` at `pmax > 0` with availability 0 — the channel the charter itself predicted — and
HEAD drift (solve-surface fingerprint `531e4805` → `9d35c270`, 195 → 197 rows). If bit-identity is
wanted as a standing invariant the fix is to drop zero-availability-all-year units from the LP
column set, which is a **shared-path** change no single ISO's lane should make.

**A second gap, routed not absorbed:** the window restores **774.1 of 956.0 MW** in 2020
(788.3/949.0 in 2021; 199.1/201.3 in 2022). The ~101 MW difference is plants carrying zero capacity
all year, almost all **waste-to-energy, landfill gas, biomass, small hydro and wind** — classes
driven by measured budgets/CFs rather than unit capacity, so possibly by design. 0.4 % of the
fleet; named so it is not lost.

**Charter task 4 done:** the `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` 2019 caveat is retired — the
shortfall goes **−2.119 TWh → −0.061 TWh** with Pilgrim restored. What is not closed is written
into the comment: the row's denominator is still the 2-plant fleet, so Jan-May carries a shape
error (April worst, +130 GWh). Re-deriving is **deferred on purpose** — the constant is on the
solve surface and would re-key every ISO to repair a year that is frozen and unsolvable. **2019 and
H1-2026 were not touched.**

**Next shorthand: `neiso-108`.** The offer-level lane stays CLOSED. The fuel lane is now CLOSED
too — the index-vs-delivered question is answered and `gas_electric_power_monthly_level` is
adjudicated `I`; do not re-open either without new evidence (rule 28 DO-NOT-REDO). The live objects
are unchanged: C3c (frontier, needs its own charter) and the diurnal amplitude gap.
**OPEN FOR THE OWNER: whether to promote `2026-09-09-neiso-107-retiree-window` as the keeper.**

## 2026-09-19 — neiso-112: the marginal emission rate for all six years, solved one-year-per-shard, and promoted

**KEEPER → `2026-09-19-neiso112-mer-year-isolated`** (bundle
`results/calibration/neiso112_mer_span`), superseding
`2026-09-16-neiso110-dualfuel-derate-scope` on the owner ruling of 2026-09-19
("Promote when they land"). **DETERMINATION CALIBRATED**, criterion for criterion
identical to the superseded keeper: 8 scored, **0 fails**, the same lone ledgered
C3c, grade 7 / 0 / 1, rubric v3.8, all six years scorable.

**WHY THERE WAS A SOLVE AT ALL.** `marginal_emission_rate` — the emissions dual,
dCO2/d(demand) at the solve's own optimal basis — landed in `fba0ecd7`, after the
incumbent's `git_sha c0916408`. It is an LP dual, so no committed sidecar carried it
and none could be post-processed into it. The marginal-abatement page
(`docs/codebase-site/marginal-abatement.html`) had NEISO among the eight grids
reporting pending.

**NO MECHANISM WAS TESTED AND NO CELL VERDICT MOVES (rule 28d).** The recipe is the
incumbent's, reconstructed by `replay_keeper.py` from its own `meta.json`: zero
`ScenarioConfig` choices changed, zero free parameters added, DOF ledger carried
byte-identical, the `authorized_price_tuning` scalar neither re-sized nor re-swept.

**WHAT WAS NEW: THE STRUCTURE OF THE SOLVE.** On the owner's instruction the same day
— *"launch a single shard for each year of the solve bc warm start has been proven to
no longer be neutral and therefore shouldn't be used for backcast"* — each of the six
years was solved **alone, in its own shard container** (rule 36
`[R-YEAR-ISOLATION]`), then composed at zero LP by the new
`scripts/probes/_neiso112_compose_span.py`. That composer refuses to write a span
unless every leg's `scenario_config` is identical outside the two year-scoped fields;
measured at composition: **856 fields, only `gas_price_override` and `weather_year`
varying**, one shared solve-surface fingerprint `9d35c270c69e9eee` — the same the
incumbent recorded.

**THE RESULT THAT MATTERS BEYOND THIS LANE: the MISO year-grouping defect does NOT
reproduce in NEISO.** The six year-isolated solves reproduce the incumbent's single
six-year invocation with prices **bit-identical** (max |Δprice| 1.42e-14 to 5.68e-14
$/MWh; **0 of 262,800** zone-hour cells past $0.01/MWh), demand identical at
0.00e+00, and annual class energy identical to <5e-7 TWh. Rule 36 (f) records that
artifact's size as *unmeasured outside MISO*; for NEISO it is now **measured at nil**
in price and annual energy, where MISO's 2022 moved 24.18 TWh and 43,160 of 70,080
price cells (~$500 M of objective). The mechanism is the MER distribution itself —
see below.

**REPORTED AT FULL MAGNITUDE, NOT ROUNDED AWAY.** At the hourly grain **1.19–1.55 %**
of class-hours (1,460–1,897 of 122,640) differ by >0.1 MW, the largest single
class-hour by **402.6–587.5 MW**, among CC_REGULAR / hydro / oil / CT_PEAKER /
CC_CHP — alternate-optimum reshuffling of a degenerate LP at an unchanged objective
and unchanged prices, the same signature and magnitude **neiso-107 already recorded
and root-caused against this keeper** (426.95 / 371.44 / 442.34 MW). A limitation
carried rather than implied away: the MER is a *basis-dependent* dual, so in those
~1.3 % of tied hours the reported value is one of several valid one-sided
derivatives, and with no incumbent MER to difference against **the size of that
ambiguity is unmeasured**.

**THE DELIVERABLE.** 43,800 zone-hours per year, **zero nulls**, all six years, in the
committed `hourly/system_<year>.parquet`:

| year | load-wtd | p10 | median | p90 | max | wind-wtd | solar-wtd |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 0.5182 | 0.363 | 0.574 | 0.649 | 1.000 | 0.5144 | 0.5285 |
| 2021 | 0.4967 | 0.348 | 0.461 | 0.653 | 1.000 | 0.4848 | 0.5004 |
| 2022 | 0.4893 | 0.343 | 0.454 | 0.668 | 1.000 | 0.4849 | 0.4882 |
| 2023 | 0.5417 | 0.368 | 0.580 | 0.673 | 1.168 | 0.5285 | 0.5371 |
| 2024 | 0.5588 | 0.379 | 0.581 | 0.675 | 1.319 | 0.5476 | 0.5630 |
| 2025 | 0.5296 | 0.360 | 0.575 | 0.671 | 1.568 | 0.5157 | 0.5253 |

tCO2/MWh. **This is a gas-on-the-margin ISO and the photographic negative of MISO's
coal margin**: p90 **0.65–0.68** against MISO's 0.94–1.02, and **0.00–0.01 %** of
zone-hours with a non-emitting unit marginal against MISO's 13–23 %. With no coal
tranche to swap into there is no second vertex to land on, which is *why* the
year-grouping artifact is absent here. Wind's avoided rate sits **below** the
load-weighted mean in all six years (−0.4 % to −2.4 %; it blows in lower-margin
hours) and solar's at or just above it in five of six — both gaps small because the
marginal fuel barely changes, which is the real market fact an ISO-NE abatement
calculation starts from.

**TWO THINGS FOUND ON THE WAY, recorded rather than smoothed over.** (1) A bug in
this session's own composer — it copied leg-2020's `run_config.json` as the base
config, so `calibration_flags.years` read `[2020]` against a six-year `meta.json`;
`audit_keepers` E3 caught it and it is fixed **at the source**. The MISO analogue has
the same shape and is left to the MISO lane (rule 25). (2) Rebuilding the benchmark
reproduced the incumbent's `campd` and `eia930` artifacts to the **identical content
hash**, but `eia923` hashed differently at an identical `btm_backfill_year` — a
source-data vintage change in the intervening three days. **No scored criterion
moved**; noted so the hash difference is never later read as a model change.

**NOT THIS LANE'S, but named so the owning lanes see it:**
`check_registry_payload_parity.py` is RED on
`results/calibration/caiso279_ablate_dswcouple_span` and
`results/calibration/soco15_spp_arm`, both **tracked on `origin/main` with 34 files
each** — a pre-existing CI red for the CAISO and SOCO lanes, untouched here.

**COST AND RETENTION.** Six containers, ~3–4 min of LP each, peak cgroup 4.74–4.84
GiB against the 13.34 GiB ceiling; no shard neared the 20-minute stop or needed swap.
All six archived after their bytes were fetched, checked out and verified (rule 33
(a)/(e)); their branches are kept as the durable copy of the per-year legs, with full
recovery SHAs in `.gitignore` and in
`docs/RESULT-neiso112-mer-year-isolated-2026-09-19.md` §5.

**OPEN GATES CARRIED, UNCHANGED:** C3c (ledgered; frontier), the neiso-109 winter-oil
root-cause issue, and the neiso-111 reserve-supply scoping finding. **Next shorthand:
`neiso-113`.**

## neiso-113 — 2026-09-24 — G-DRIFT + bench refresh (zero LP)

G-DRIFT `fda9ece3..40f4ed7a`: every solve-path hunk INERT for NEISO; the only live change
is benchmark-side (`ad42fe43`, EIA-923 dual-fuel oil re-attribution). NEISO bench parts
regenerated (6 STALE → 0), keeper re-scored: **CALIBRATED unchanged, 0 status flips**,
largest move C1 2022 ST_GAS actual 0.302 → 0.212 TWh. `docs/RESULT-neiso113-bench-refresh-2026-09-24.md`.
**Next shorthand: `neiso-114`.**

## R-NEISO — 2026-09-25 — PROMOTED `2026-09-24-r-neiso-inputs-2019` (owner: "yes promote")

The hydro-5 recipe re-solved 2019–2025 (one shard per year) on the audit-ordered corrected backcast
inputs: year-matched EIA-860, measured CAMPD coal/ST/CC heat rates, CAMPD gas sub-5-day outages,
mid-vintage and partial-plant exit carries. Offer curves byte-identical, zero free parameters.
Train tier 2023–2025 **CALIBRATED** (C3c ledgered); full span **NOT-YET** on C1 CC_REGULAR
2019/2021/2022 (−4.66/−3.17/−3.12 TWh) — restored coal and ST_GAS over-dispatch, open successors.
Outgoing keeper `2026-09-22-hydro-5-neiso-ror` pruned (rule 35); year set 2020–2025 → 2019–2025.
Record: `docs/handoffs/r-neiso/RESULT-r-neiso-2026-09-24.md`.

## neiso-114 — 2026-09-25

KEEPER → `2026-09-25-neiso114-coal-mustrun-measured` (arm A; R-NEISO recipe + `coal_mustrun_requires_measured_row`, zero DOF), 2019–2025, one shard per year at pinned `9db30b45`. C1 CC_REGULAR 2019 −4.66 → −3.54, 2021 −3.17 → −2.88 (FAIL → PASS), 2022 −3.12 unchanged; all other criteria PASS; train tier CALIBRATED. Root cause: NEISO CAMPD artifacts derived on the canonical 2025ER fleet, so restored coal plants took the unmeasured 45 % must-run default. Successors: Merrimack delivered coal price (2022), ST_GAS bands on the corrected class (arm B, unsolved), tranche re-derive. Outgoing keeper prune pending (classifier-denied). Record: `docs/handoffs/neiso114/RESULT-neiso114-2026-09-25.md`.

## neiso-115 — 2026-09-25 — PROMOTED `2026-09-25-neiso114-arm-b-stgas` (standing ruling)

neiso-114 arm B completed (seven single-year legs, rule 36), composed at zero LP into `neiso114b_span`, attested
(ST_GAS bands on the corrected class, ledgered, ex ante, never swept) and scored against arm A: no criterion
changes status in any year; CC_REGULAR 2019 −3.54 → −2.87, 2021 −2.88 → −1.98, 2022 −3.12 → −3.03, 2023 −1.25 → −0.59;
ST_GAS over-dispatch roughly halved; mean-LMP bias +0.1–0.9 pp (all PASS). Train tier CALIBRATED; full span NOT-YET
(C1 CC_REGULAR 2019/2022). Arm A and `2026-09-24-r-neiso-inputs-2019` pruned (rule 35). Record:
`docs/handoffs/neiso114/RESULT-neiso114-2026-09-25.md` §6. **Next shorthand: `neiso-116`.**

## neiso-116 — 2026-09-26 — bench refresh + phase 0 on the C1 CC_REGULAR misses (zero LP)

Keeper bundle rebuilt from its seven neiso-115 legs (fetched by SHA) and re-registered: NEISO bench parts
6 STALE → 0, keeper re-scored with **0 status flips** (full span NOT-YET, train tier CALIBRATED; only C2 2021
actual 60.07 → 60.11 TWh moved). G-DRIFT `9db30b45` → `f30e3704`: every LP input array identical in all seven
years — keeper is the control. Phase 0: Merrimack's coal is domestic NAPP (import-price option moot); its
delivered cost is published 2019–20 (≈ 3.13 $/MMBtu); a price correction moves 2022 by ≤ ~0.5 TWh, while the
EIA-923 yard budget (`coal_fuel_inventory` plant grain, NEISO U) cuts 2.21 TWh there. Tranche deriver drops coal
rows at HEAD (COAL-SUB) and cannot see the restored ST_GAS plants; the committed-basis mechanism is
non-selective and its NEISO artifact predates the fleet correction. Owner rulings requested; no solve.
Record: `docs/handoffs/neiso116/PRECOMMIT-neiso116-2026-09-26.md`. **Next shorthand: `neiso-117`.**

## neiso-117 — 2026-09-26 — PROMOTED `2026-09-26-neiso-117-coal-yard` (owner ruling)

Owner rulings on PRECOMMIT-neiso116 §5: arm `coal_fuel_inventory_plant_grain` ALONE (per-coal-yard annual EIA-923
budget rows, no pooled monthly limb — new gate `resolve_coal_budget_arms`, `(MISO, NEISO)`), no Provport, placeholder
coal price kept, tranche/committed-basis deferred. Seven single-year shards; the first 2025 leg was infeasible
(Schiller's winter fuel-security floor vs a zero-coal yard) → `reconcile_floors_to_yard_budget` (floors scaled to the
yard's own budget; inert 2019–2024) and 2025 re-solved. Result: no criterion changes status; C1 CC_REGULAR 2022
−3.03 → PASS, 2019 −2.87/−4.0 pp → −2.35/−3.5 pp (share still FAIL); CO2 2022 CAVEAT → PASS. Train tier CALIBRATED;
full span NOT-YET on 2019 share only. `neiso114-arm-b-stgas` pruned (rule 35). Record:
`docs/handoffs/neiso117/RESULT-neiso117-2026-09-26.md`. **Next shorthand: `neiso-118`.**

## neiso-118 — 2026-09-26 — PROMOTED `2026-09-26-neiso-118-canal-ct` (Canal 3 heat rate)

Phase 0: 2019's CT_PEAKER excess (+1.18 TWh) is Canal 3 (1599) at an impossible 3.95 MMBtu/MWh — eGRID-2019's
boundary-broken plant rate, because the measured-CT derive's `union_fleet` kept each unit's LATEST vintage class and
Canal 3 is oil in 2023–2025. Owner ruling "CT only": class-preserving `union_fleet(klass=)`, NEISO CT artifact
re-derived (+Canal 3 rows only, pooled 10.76). Seven single-year shards (first launch cloned `main`; relaunched with an
explicit SHA checkout). Result: C1 CC_REGULAR 2019 −3.46 pp FAIL → −2.3 pp PASS; C3a price_mean 2019 +9.3 % → +10.03 %
PASS → FAIL ($0.01 over). Full span NOT-YET on that one line; train tier CALIBRATED. `neiso-117-coal-yard` pruned
(rule 35). Record: `docs/handoffs/neiso118/RESULT-neiso118-2026-09-26.md`. **Next shorthand: `neiso-119`.**
