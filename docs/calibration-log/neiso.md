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
