# Capacity-market equilibrium tests (T2.1-T2.5) — 2026-07-12 (P-3B)

**Session.** P-3B of
`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §2
Tier 2, rescoped 2026-07-12 to the ISOs partial-P-3A coverage and the
settled-backcast frontier actually support: **NEISO** (T2.1-T2.4, the
capacity-market case — completed 25/25 in P-3A, backcast frontier-declared)
and **ERCOT** (T2.5 only, the energy-only contrast). PJM (22/25 in P-3A) was
the plan's optional second capacity-market point "if runtime allows" — not
attempted this session; NEISO alone already gives a clean, fully-powered
T2.1-T2.4 result and a PJM replication is a natural, cheap follow-up rather
than a blocker. NYISO/MISO are out per the manager's scoping (NYISO 1/25
thin, MISO 0/25 hard-blocked, per
`docs/handoffs/full-horizon-findings-2026-07-12.md` §3-4).

**Container caveat.** `results/full-horizon/` is a gitignored disposable
solve cache (rule-16 throwaway-baseline spirit), and this session's execution
container started fresh — none of P-3A's actual parquets/ledgers were on
disk, only its committed findings prose. "Reuse the partial P-3A runs" was
therefore executed as a **byte-for-byte re-solve of the identical reference
config** through the same committed, unmodified harness
(`scripts/run_full_horizon.py`), not a literal cache hit. This reproduced to
high precision: 67.6 min / 3.94 GB peak RSS here vs. P-3A's 71.9 min / 3.92 GB;
identical base-year I7 numbers (accredited firm 26,234 < requirement 28,911 MW);
identical 2030 reserve margin (29.3%); identical I3 curtailment ramp shape. This
is the same run, re-derived, not a different one.

**What's active vs. dormant (read this before the results).** Both P-3A and
this session run `capacity_market_clearing=False` (the P-2A recommendation,
`docs/handoffs/capacity-price-validation-2026-07-12.md` §7). The CR-1 sloped
VRR/ICAP/FCA/RBDC demand curve (`MarketDesign.demand_curve`, landed in P-1B) is
**dormant** under this default. The ACTIVE capacity-value mechanism for every
capacity-market ISO is the flat, pre-CR-1 stub:

```
capacity_price_per_firm_mw_yr = net_cone_per_kw_yr * 1000        # $/yr, FLAT
capacity_revenue_per_mw_yr(iso, eford) = capacity_price * (1 - eford)
```

(`market_sim.model.capacity.capacity_revenue_per_mw_yr`,
`MarketDesign.capacity_price_per_firm_mw_yr`,
`config/constants.py:2440-2482`). **T2.1-T2.5 below all target this active
mechanism.** A `capacity_market_clearing=True` run hits the P-2A degeneracy
(accredited position past the curve's zero-cross → $0) and is never scored
here as an equilibrium result — that gate stays off per P-2A/§7's own
recommendation, unchanged by this session.

**Deliverable.** `scripts/run_equilibrium_battery.py` (pushed in a prior
commit this session) + this report + `results/full-horizon/_t2_equilibrium.json`
(machine-readable, gitignored like every other full-horizon cache — regenerate
with the commands below). Reproduce:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 uv run python \
  scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 \
  --out-dir results/full-horizon/neiso
uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
  --out-dir results/full-horizon/neiso-t2-base
uv run python scripts/run_equilibrium_battery.py overbuild --iso NEISO \
  --start-year 2026 --end-year 2030 --out-dir results/full-horizon/neiso-t2-overbuild
uv run python scripts/run_full_horizon.py --iso ERCOT --start-year 2026 --end-year 2030 \
  --out-dir results/full-horizon/ercot-t2-base
uv run python scripts/run_equilibrium_battery.py overbuild --iso ERCOT \
  --start-year 2026 --end-year 2030 --out-dir results/full-horizon/ercot-t2-overbuild
uv run python scripts/run_equilibrium_battery.py score \
  --neiso-full results/full-horizon/neiso --neiso-base results/full-horizon/neiso-t2-base \
  --neiso-overbuild results/full-horizon/neiso-t2-overbuild \
  --ercot-base results/full-horizon/ercot-t2-base --ercot-overbuild results/full-horizon/ercot-t2-overbuild \
  --out-json results/full-horizon/_t2_equilibrium.json
```

---

## 1. Verdict (lead)

| Test | Status | One-line finding |
|---|---|---|
| **T2.1** identity | **PASS** | Capacity value = `net_cone x (1-EFORd)` exactly, every year, no exceptions. |
| **T2.2** oscillation | **FAIL** | T2.2a (price time-invariant) PASSes trivially; T2.2b (RM oscillates around net-CONE's implied target) FAILs — RM is monotone across all 25 years, zero sign changes. |
| **T2.3** hysteresis | **PASS** | I5 (no retire-reenter) and I13 (cobweb) both PASS on the NEISO 25-year run. |
| **T2.4** NEISO overbuild | **FAIL** (gated items) | Capacity value does NOT collapse (T2.4a FAIL, expected); entry DOES fall via the energy-price channel (T2.4b PASS); retirements do NOT resume — zero in both runs (T2.4c FAIL, report-only); LW price falls (T2.4d PASS). |
| **T2.5** ERCOT overbuild | **PASS** | Capacity value stays $0 in both runs (negative control); scarcity hours and LW/max price all fall under the same +10 GW shock. |

**Headline.** The active (fixed-price) capacity mechanism is exactly what it
says it is: a constant. T2.1 proves the identity holds bit-exact across 25
years of wildly varying reserve margin; T2.2/T2.4a show that constant produces
no restoring force and no collapse under a direct +10 GW shock. The system
still shows *some* equilibrating response — entry slows in NEISO (T2.4b) via
energy-price cannibalization, not the capacity price — but the clean
textbook property (price signals scarcity, entry/exit respond, system
converges) is entirely absent on the capacity side. **NEISO's thermal fleet
retires exactly zero MW over the ENTIRE 25-year reference horizon** (not just
the 5-year probe window — see §6), even as reserve margin climbs to 67.5% and
VRE curtailment reaches 28% of potential: the flat capacity payment alone
appears sufficient to keep the existing thermal fleet solvent indefinitely,
regardless of how long the system gets. **ERCOT's energy-only design, by
contrast, shows both channels working** — the same +10 GW shock triggers
11.7 GW of retirement in the very first post-shock year (§7) *and* eliminates
its 2029 scarcity event outright. This is the clearest evidence yet for the
audit's central prediction: *an entry/retirement loop driven by a
non-responsive capacity price cannot equilibrate* — and it is a capacity-side
problem specifically, not a general model failure (ERCOT's own adequacy
channel works).

---

## 2. Method

Config: `ScenarioConfig(mode="forecast", capacity_market_clearing=False)`,
every other field default (`use_campd_bins=True`, the ISO default) — identical
to the P-3A reference run. NEISO's full run covers 2026-2050 (25 years, the
complete P-3A horizon); the four overbuild-probe runs cover a shorter
2026-2030 window (5 years — 1 injection year + 4 post-shock years), matching
the Tier-1 ladders' own runtime-bounded window.

**The +10 GW overbuild probe.** A single synthetic `gas_cc` block (+10,000 MW,
one unit, sited at each ISO's default new-entry zone) is injected at
`start_year` (2026) through the same production seam real EIA-860 planned
units use — `evolve_fleet` step 3 ("known additions",
`data.fleet.load_planned_additions`). The injection is a diagnostic-only,
in-process monkeypatch of `market_sim.runner.load_planned_additions`
(mirrors `run_driver_battery._apply_probe_patches`'s established off-registry
probe convention: never persisted, confined to the process, restored
immediately after the solve — see script docstring). `gas_cc` was chosen as a
neutral, common new-entrant thermal tech; the SAME tech/size hits both ISOs so
the NEISO/ERCOT comparison is an apples-to-apples shock. Verified in a 1-year
smoke test before the real runs: the injection adds exactly +10,000 MW of
thermal capacity and nothing else (confirmed again in the real runs, §6).

**Known limitation.** The "known additions" pathway does not write into the
ledger's `thermal_additions`/`builds_thermal_mw` field (that field reflects
only the *economic* new-entry screen, a separate step) — so the injection
year's own `builds_thermal_mw` row reads unchanged (0 in both baseline and
overbuild), and the +10 GW only shows up as a capacity-*level* shift
(`thermal_mw`/`capacity_by_fuel_mw["gas_cc"]`, confirmed exactly +10,000 MW).
This is a pre-existing model characteristic (known additions and economic
entry are logged differently by design), not a probe bug; all tables below
report the injection year using the capacity-level numbers and reserve the
`builds_thermal_mw` comparison for post-shock years, where it is unaffected.

---

## 3. T2.1 — capacity-value-to-net-CONE identity (NEISO, active path)

For every one of NEISO's 25 solved years, `capacity_revenue_per_mw_yr("NEISO",
eford, config, reserve_position=None)` was compared against the independent
arithmetic `net_cone_per_kw_yr x 1000 x (1-eford)` for five representative
EFORD values (0.0, 0.05, and the registered `gas_cc`/`gas_ct`/`coal`/`nuclear`
EFORDs). **Zero mismatches at any EFORD, any year.**

| Quantity | Value |
|---|---|
| Capacity price (EFORd=0) | **$95,000.0 /firm-MW-yr**, every year 2026-2050 |
| Price identical across all 25 years | **True** (bit-exact, `round(.,6)`) |
| Reserve margin range over the same 25 years | **5.0% to 67.5%** |
| Arithmetic mismatches found | **0** |

**Verdict: PASS.** The code does exactly what the mechanism is documented to
do — $95,000/firm-MW-yr is `NEISO`'s registered `net_cone_per_kw_yr=95.0 x
1000` (`config/constants.py`), and it is paid identically whether the system
is 5% short or 67.5% long. This is the direct, structural confirmation that
the active mechanism has **no channel** through which the fleet it prices
can talk back to the price.

---

## 4. T2.2 — long-run oscillation statistics (NEISO 2026-2050)

**T2.2a (capacity value time-invariant, CV < 0.1%): PASS** — CV = 0.0 exactly
(restates T2.1 as a dispersion statistic).

**T2.2b (reserve margin oscillates around net-CONE's implied target — the
textbook equilibrium property fixed-price stubs cannot exhibit): FAIL.**

| Statistic | Value |
|---|---|
| Reserve-margin mean / stdev | 42.1% / 16.0pp |
| Min / max | 5.0% (2026) / 67.5% (2050) |
| I12 band (planning floor, +15pp) | [15.7%, 30.7%] |
| Years inside the band | **4 / 25 (16%)** — only 2027-2030 |
| Year-over-year sign changes | **0** |
| Final 5 years monotone non-decreasing | **True** |

Reserve margin does not oscillate even once — it climbs from 5.0% to 67.5%
**strictly monotonically, every single year**, and never returns toward the
planning band after passing through it in 2027-2030. There is no restoring
force of any kind visible in the 25-year trajectory; this is a one-way
divergence, not a damped or noisy oscillation around an attractor. Combined
with T2.1's identity, the mechanism cause is unambiguous: the capacity price
that is supposed to supply that restoring force is a constant.

---

## 5. T2.3 — hysteresis (I5/I13 reuse, NEISO 2026-2050)

| Invariant | Status | Detail |
|---|---|---|
| I5 (no retire-and-reenter) | **PASS** | ok |
| I13 (cobweb / lumpy build alternation) | **PASS** | smooth |

**Verdict: PASS.** Unlike CAISO/ERCOT/PJM in the P-3A run (which WARN on I13),
NEISO's 25-year build pattern shows no full/zero alternation — consistent
with the picture above: NEISO isn't oscillating at all, cleanly or lumpily,
it is monotonically diverging. (I3/I7/I10/I12/I14 also reproduce P-3A's
findings exactly: I12 FAILs every year outside 2027-2030 per §4 above; I7
FAILs the 2026 base year, accredited firm 26,234 < requirement 28,911 MW;
I3 curtailment climbs from 3.6% of renewable potential in 2034 to 28.0% by
2048; I10 WARNs a single REC-dual oscillation 2048→2049 (65→$0.001) as VRE
finishes clearing the RPS target; I14 WARNs 10.3-13.0% negative-price hours
2037-2050 from VRE oversupply.)

---

## 6. T2.4 — +10 GW exogenous overbuild, NEISO

| Year | RM base | RM +10GW | LW $ base | LW $ +10GW | Thermal build base | Thermal build +10GW | Renew build (both) | Retire base | Retire +10GW |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2026 (inject) | 5.0% | **43.0%** | 46.20 | 36.96 | 0 (+10,000 MW level shift, see §2) | — | 0 | 0 | 0 |
| 2027 | 17.8% | 42.9% | 44.63 | 36.97 | 3,299 | **0** | 3,000 | 0 | 0 |
| 2028 | 21.8% | 42.8% | 44.70 | 38.25 | 1,000 | **0** | 3,000 | 0 | 0 |
| 2029 | 25.6% | 42.7% | 44.92 | 40.03 | 1,000 | **0** | 3,000 | 0 | 0 |
| 2030 | 29.3% | 42.6% | 45.40 | 41.98 | 1,000 | **0** | 3,000 | 0 | 0 |

| Sub-test | Status | Gate | Detail |
|---|---|---|---|
| T2.4a capacity value collapses | **FAIL** | yes | price_base = price_over = $95,000.0/firm-MW-yr — unchanged, by construction (T2.1). |
| T2.4b entry falls post-shock | **PASS** | yes | Cumulative 2027-2030: base 18,299 MW vs. overbuild 12,000 MW (economic thermal entry drops to **zero** every post-shock year; renewable entry, which doesn't see the capacity price at all, is unchanged at 3,000 MW/yr in both). |
| T2.4c retirements resume | **FAIL** | *report-only* | 0 MW either run, every year — see the full-horizon cross-check below. |
| T2.4d energy price falls | **PASS** | yes | Mean LW price: base $45.17 vs. overbuild $38.84/MWh. |

**The zero-retirement result is not a short-window artifact — it holds over
NEISO's entire 25-year reference horizon.** Independently of this probe,
NEISO's full 2026-2050 baseline run (§3-§5's substrate) retires **exactly 0 MW
of thermal capacity in all 25 years**, even as reserve margin climbs to 67.5%
and VRE curtailment reaches 28% of potential. **Mechanism hypothesis:** the
flat $95,000/firm-MW-yr capacity payment (paid on UCAP regardless of system
length, T2.1) is large enough relative to NEISO's thermal fleet's FOM-only
going-forward cost that `net_revenue >= going_forward_cost`
(`apply_economic_retirements`, `capacity.py:1400`) holds for every unit, every
year, independent of the energy margin term — i.e., the capacity term alone
may be carrying the sign of the inequality. This is a distinct, and arguably
more consequential, symptom of the same root cause T2.1/T2.2 identify, and it
is a natural next quantitative check for the P-2A/CR prerequisite chain (a
per-fuel `capacity_revenue / going_forward_cost` ratio report would confirm or
refute this directly — not attempted here, findings only).

**The entry response is real, and it is NOT running through the capacity
price** — post-shock thermal entry drops from 6,299 MW (base, 2027-2030
cumulative) to 0 MW (overbuild) purely because the lower energy price
(cannibalization from the extra 10 GW) makes new thermal entry's *energy*
margin insufficient, while the identical, unchanged capacity payment
contributes nothing to that signal. Renewable entry is completely unaffected
(3,000 MW/yr in both runs) because it doesn't see either price. So there is a
live, partial equilibrating channel in this system — it just runs entirely
through the energy market, not the capacity market the audit is examining.

---

## 7. T2.5 — same overbuild, ERCOT (energy-only contrast)

| Year | RM base | RM +10GW | LW $ base | LW $ +10GW | hrs≥$500 base/+10GW | hrs≥$2000 base/+10GW | max $ base | max $ +10GW |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2026 (inject) | 14.9% | 25.6% | 23.73 | 20.86 | 0 / 0 | 0 / 0 | 42.7 | 35.2 |
| 2027 | 12.5% | 12.6% | 24.01 | 24.79 | 0 / 0 | 0 / 0 | 41.5 | 256.1 |
| 2028 | 11.1% | 12.9% | 25.74 | 28.02 | 0 / 0 | 0 / 0 | 44.1 | 257.8 |
| 2029 | **7.1%** | 15.4% | 38.01 | 30.44 | **13 / 0** | **13 / 0** | **5,000** | 257.3 |
| 2030 | 9.0% | 20.6% | 29.16 | 31.58 | 0 / 0 | 0 / 0 | 49.9 | 257.7 |

| Sub-test | Status | Gate | Detail |
|---|---|---|---|
| T2.5a capacity value $0 in both (negative control) | **PASS** | yes | $0.00 both runs — ERCOT is registered energy-only (`MARKET_DESIGN["ERCOT"].capacity_market=False`), unaffected by anything else in this test. |
| T2.5b scarcity hours fall | **PASS** | yes | hrs≥$500: 13→0; hrs≥$2000: 13→0 (both entirely from the 2029 event, below). |
| T2.5c LW/max price fall | **PASS** | yes | Mean LW $28.13→$27.14/MWh; max-of-max $5,000→$258. |

**The headline number: the +10 GW shock eliminates ERCOT's 2029 scarcity
event outright.** Baseline ERCOT reproduces the exact 2029 scarcity signature
from the full P-3A 2026-2050 reference run (13 hours ≥$500, 13 hours ≥$2000,
max price = VOLL $5,000, RM 7.1% — matching
`full-horizon-findings-2026-07-12.md` §6's own #2064 table row for 2029
precisely) — direct confirmation this 5-year probe's baseline is the same
model behavior as the full run, not an artifact of the shorter window. Under
the +10 GW overbuild, that exact event disappears completely: 0 scarcity
hours at either threshold, max price collapses to $257.

**Supplementary observation — ERCOT's retirement screen resumes hard, unlike
NEISO's.** Not one of the three pre-registered T2.5 sub-tests, but directly
visible in the same trajectory data: in 2027, the overbuild run retires
**11,740 MW** of thermal capacity vs. baseline's 1,854 MW — nearly
reabsorbing the entire +10 GW shock in a single year (post-retirement thermal
capacity: 77,950 MW overbuild vs. 77,836 MW baseline — almost exactly
converged). This is the ERCOT-side mirror of NEISO's T2.4c null result, and it
is the clearest evidence in this battery that **the two market designs'
adequacy signals really do differ in kind, not just degree**: ERCOT's
economic retirement screen sees the energy-price collapse directly (no
capacity payment to offset it) and retires hard; NEISO's screen sees the same
kind of energy-price collapse but the unchanged $95,000/firm-MW-yr capacity
payment apparently absorbs it, and nothing retires. (Entry in ERCOT does not
show a clean monotone suppression the way NEISO's did — by 2029-2030 the
overbuild run is again building *more* thermal than baseline, 4,345/8,000 MW
vs. 1,345/5,000 MW — consistent with ERCOT's baseline being chronically
under-built by load growth rather than oversupplied, per
`full-horizon-findings-2026-07-12.md` §5-6; the 2027 retirement effectively
resets the fleet, and normal load-growth-driven entry resumes from there. This
was not a pre-registered claim and is reported for completeness, not scored.)

A minor, honestly-reported nuance: LW price is not uniformly lower in the
overbuild run every year (2027/2028/2030 show it $0.78-2.42/MWh *higher* than
baseline, even as scarcity and max price fall sharply). Mechanism hypothesis:
this is ordinary one-pass dynamic divergence, not noise — once year-1 prices
differ, the overbuild run's own subsequent economic entry/retirement
decisions diverge from baseline's (visible in the build/retire columns
above), so by year 2 the two runs are no longer "baseline + 10 GW" but two
independently-evolved fleets with different unit mixes setting price in
different hours. The aggregate/peak metrics (mean LW price, max price,
scarcity hours) are unambiguous; the year-by-year path is not required to be
monotone for a one-pass evolution model, and isn't.

---

## 8. Ranked issues / mechanism hypotheses

Every item below routes to the existing P-2A/CR prerequisite chain (rules
1/11/14 — findings only, no fix attempted here).

1. **No restoring force in the active capacity mechanism (T2.1 + T2.2b).**
   Root cause: `capacity_market_clearing=False` makes
   `capacity_revenue_per_mw_yr` a pure function of `(iso, eford)`, invariant
   to reserve position by construction. Fix path: the existing P-2A
   prerequisite chain — #1532 accreditation-basis adjudication (P-2B),
   accredited-position calibration (retirement-miss fix + CR-3.1 marginal-ELCC,
   landed for renewables per P-2C but not sufficient alone, see item 2), and
   per-forecast-year net-CONE anchoring, before `capacity_market_clearing`
   is a safe default flip.
2. **Capacity value never collapses under a direct +10 GW shock (T2.4a).**
   Same root cause as #1; this is the shock-test confirmation of the
   trajectory-level finding.
3. **NEW: zero thermal retirements over NEISO's entire 25-year reference
   horizon (T2.4c, cross-checked against the full run in §6).** Not
   previously flagged by P-3A (which reported the *reserve-margin* overshoot
   but not this retirement-side null result explicitly). Hypothesis: the
   flat capacity payment alone may be large enough vs. FOM-only going-forward
   cost to keep `net_revenue >= going_forward_cost` for the entire thermal
   fleet regardless of energy margin — worth a direct per-fuel
   `capacity_revenue / going_forward_cost` ratio check as a fast, cheap
   follow-up (no LP solve required, a pure `ScenarioConfig`+registry
   calculation) before the next capacity-economics session.
4. **Entry DOES respond — through the energy market, not the capacity
   market (T2.4b, and ERCOT's post-2027 rebound in §7).** A genuine partial
   equilibrating channel exists in both ISOs; it just bypasses the mechanism
   this audit is evaluating. Not a bug — worth noting as the reason the
   full-horizon trajectories aren't a *complete* divergence (P-3A's own
   finding that entry does eventually slow, just too late and too little to
   prevent the RM overshoot).
5. **ERCOT's own adequacy mechanism (energy/ORDC scarcity price feeding the
   SAME economic retirement screen) works cleanly (T2.5, all PASS) and
   responds on BOTH margins (retirement resumes hard, §7) where NEISO's
   responds on neither.** This is the plan's central hypothesis, directly
   confirmed by a controlled, identical-shock, cross-ISO comparison rather
   than inferred from two different endogenous trajectories (which is what
   P-3A's original full-horizon comparison had to rely on).
6. **Minor: one-pass trajectory divergence produces non-monotone year-by-year
   LW price under overbuild in ERCOT (§7).** Not a bug; a documented property
   of one-pass capacity evolution once two runs' prices diverge. No action
   needed, flagged for anyone reproducing this test who might otherwise read
   a single year's price increase as a contradiction.
7. **Methodological note: the "known additions" injection doesn't log into
   `builds_thermal_mw` (§2).** Pre-existing model characteristic (known
   additions and economic entry are logged at different steps), not a probe
   defect; documented so a future reproduction doesn't misread the injection
   year's build column.

---

## 9. What this session did / did not do

- **Did:** built `scripts/run_equilibrium_battery.py` (pushed in a prior
  commit); re-solved the NEISO 2026-2050 reference forecast (25/25 years,
  confirmed reproducing P-3A to high precision); ran two baseline-vs-+10GW
  overbuild probe pairs (NEISO and ERCOT, 2026-2030); scored T2.1-T2.5 against
  expectations pre-registered before the runs; found the zero-NEISO-retirement
  result and the ERCOT 2027 mass-retirement contrast, neither of which were
  explicit pre-registered sub-tests but both directly relevant and reported
  honestly as supplementary observations.
- **Did not:** touch any model code, threshold, or offer curve (rules 1/11/14);
  run a `capacity_market_clearing=True` diagnostic (out of scope per the
  manager's framing — would only hit the known P-2A degeneracy); attempt PJM
  (optional, skipped for time); solve or score any 2022/H1-2026 data (rule
  22 — forecast-mode probes only); register anything on the backcast
  dashboard (forecast probes never are).
- **Data provenance:** `results/full-horizon/{neiso,neiso-t2-base,neiso-t2-overbuild,ercot-t2-base,ercot-t2-overbuild}/full_horizon_summary.json`
  (gitignored, disposable per rule 16) and the collated
  `results/full-horizon/_t2_equilibrium.json` (same), all regenerable via
  the reproduce commands in the header. `scripts/run_equilibrium_battery.py`
  is the committed, reusable deliverable.
