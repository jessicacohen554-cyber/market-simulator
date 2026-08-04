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

Next shorthand: **neiso-80.**
