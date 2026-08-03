# Calibration Log — CAISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for CAISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — gas_daily_shape §3.7 fix A/B on the caiso-97 recipe: 2025-only, small; probes registered, no keeper action

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the caiso-97 recipe the fix is price-identical in
2023/2024 (the measured citygate daily overlay supersedes the national HH
shape) and small in 2025 (mean −$0.04, 207 hours >|$1|, max |Δ| $22).
Registered `2026-07-19-caiso-gasshape-interpfix`(+`-base`) as probes only —
the CAISO keeper advanced to caiso-102-hourfix mid-session (PR #2563), so no
keeper recommendation from this A/B; the fix itself is on main and any future
CAISO solve carries it.

## 2026-07-19 — CAISO — caiso-103: BOTH residual lanes traced to the same structural class (DA-fixed volumes the single-market LP re-optimizes at the RT margin) — belly ALLOCATION mechanism designed (M1, owner-gated, NOT solved); evening Q1 margin decomposed to the FIRM IMPORT BLOCKS price-setting at contract cost (M-EVE-1 ask filed); caiso-92 re-derive: consumed values BYTE-IDENTICAL (issue #2562 item 3 closed)

**Runs:** NONE registered (derive-first, charter discipline). One
same-machine repro solved (`caiso102_repro_A`, gitignored, un-registered per
the FINDING-caiso92b protocol) — reproduces the caiso-102-hourfix keeper
ladder DIGIT-FOR-DIGIT (belly +6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1,
overnight +0.8/−0.0/+1.4). Keeper stays `2026-07-19-caiso-102-hourfix`,
determination NOT-YET, fail set {C3c, C4, C5a(2024 CAVEAT)}.

**Arc 1 — belly allocation design (priority 1, owner-gated BEFORE any
solve).** New committed instrument `scripts/probes/_caiso103_alloc_stats.py`
measured the design statistics from the storage-report IFM layer: the
fleet-normalized DA-allocation shape is FLEET-SIZE-INVARIANT (pairwise
r ≥ 0.994 across a 4.4 → 15.4 GW fleet; belly-core per-hod CV ≤ 0.06); the
overnight second cycle does NOT fleet-scale (0.334/0.360/0.357 TWh flat
absolute, per-fleet-MWh falling 0.049 → 0.022, and it is DA-scheduled); the
RD book is system-sized (per-MW award falling 0.17 → 0.09). Mechanism M1
designed — the DA-allocation-profile charge schedule (per-day scheduled-
volume variable S[d]; fleet floor rows `Chg[h,d] ≥ alloc_share[hod]×S[d]`;
day cap `Σ_h Chg ≤ S/da_frac` with the measured DA-share 0.840/0.799/0.760)
— volume-holding BY CONSTRUCTION (the property whose violation rejected the
caiso-100 adder), margin-re-pricing (the hour-grain charge stops bidding the
belly up; the LP keeps pricing only the 16-24 % the real RT margin
re-times). M2 (window-share bands) documented as weaker fallback; M3
(AS-obligation SOC term) measured-DEFERRED on the fleet-scaling evidence.
Ask: `docs/handoffs/caiso-103-belly-allocation-ask-2026-07-19.md` — PENDING.

**Arc 2 — evening Q1 margin decomposition (priority 2).** New committed
instrument `scripts/probes/_caiso103_evening_margin.py` on the repro: in the
deepest evening resid-quartile the marginal supply is the IMPORT node in
97-100 % of hours (3.6-4.3 GW interior), the corridors are NEVER saturated
(5-6 GW headroom), CC headroom is 0.2 GW, battery envelope binds only
37/16/8 % of Q1 hours, and Q1 λ stops a median +1.3/+3.6/+13.1 $/MWh BELOW
the model's own CT rung entry (ann-mean 59/47/55). Hub separation is the
smoking gun: actual CAISO RT clears at/above the measured tie LMP (median
−0.7/+2.6/+4.8 vs max(MALIN, PALOVRDE)) while model λ sits 8-40 $ BELOW the
same hubs. Tranche attribution: the price-setters are the two FIRM/
CONTRACTED blocks (`PNW_hydro_base` $28 / `DSW_solar_PV` $48 static Tier-3
contract costs under `caiso_perhub_firm_base`), interior in 96-100 % of Q1
hours with 1.7/2.5/2.3 GW of contracted capability economically WITHHELD —
the code's own comment documents these blocks as inframarginal price-takers
(CPUC D.20-06-028 RA must-offer; "CAISO's clearing price stays domestic even
while 3-6 GW imports flow"), so the elastic contract-cost offer contradicts
the mechanism's own driver. The λ under-price and the aligned-clock evening
under-import (−0.5/−0.3/−1.4 TWh) are ONE defect. Fix candidate M-EVE-1
(price-taking −ε/$0 bids on the existing caiso-73 shaped availability;
DELETES two fitted scalars from the price path) — NOT built; ask:
`docs/handoffs/caiso-103-evening-firm-import-ask-2026-07-19.md` — PENDING.
NOT a CT floor (caiso-91b untouched), NOT an import throttle (flow rises
toward measured).

**Arc 3 — caiso-92 offer-surface re-derive (priority 3, rule 23 citing
issue #2562).** OASIS corpus refetched (1,095 zips; 2023-06-01 absent in
the archive itself), curated, derive re-run through the fixed loader: every
estimation gate PASSES and every CONSUMED statistic is BYTE-IDENTICAL —
only the provenance timestamp/script-path changed (committed as the
record). The 2025 +1h net-load mispairing is immaterial at the condbinned
grain (within-year percentile ranks + per-resource yearly medians + the
0.80/0.90/0.97 edges absorb an off-by-one). No verdict flip → no LOYO, no
B-leg, keeper untouched. Issue #2562 item 3 CLOSED (comment posted); the
PJM/MISO items remain their lanes' work.

**Issue #2546:** no owner ruling appeared; carried unchanged.

**Structural theme (the session's finding):** both remaining λ-ladder
residual lanes are the SAME class of defect — a DA-fixed/contracted volume
(battery charge on the demand side, firm import contracts on the supply
side) that the single-market LP lets re-optimize elastically against the RT
margin, propping the belly UP and pinning the tight evening DOWN. The two
pending asks are the two sides' structural corrections.

Next number: caiso-104.

## 2026-07-20 — CAISO — caiso-104: BOTH caiso-103 asks executed and the belly ALLOCATION family REFUTED — M1 solved twice (v1 zero-charge composition defect; v2 conduct-faithful but belly-λ INERT, REJECTED on pre-registered gates); M-EVE-1 adjudicated INERT before any solve (the caiso-77 must-flow floor is LIVE in the keeper — the caiso-103 "withheld GW" attribution was a proxy artifact); DAM-outage corpus intaken; keeper UNCHANGED

Owner rulings obtained in-session: M1 GRANTED, M-EVE-1 GRANTED (with the
pre-measurement mandate), da_frac forward = latest-year carry, #2546
delegated → recommendation recorded on the issue (defer as-is this session;
delete + re-gate as a dedicated follow-up). Keeper stays
`2026-07-19-caiso-102-hourfix` (NOT-YET; ladder unchanged: belly
+6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4 — the
fresh same-machine `caiso102_repro_A` reproduces it digit-for-digit). Full
record: `results/calibration/FINDING-caiso104-m1-meve1-execution-2026-07-20.md`.

**Arc 1 — M-EVE-1 (evening): adjudicated INERT, no leg.** The pre-measurement
(`_caiso104_firm_negative_hub.py`, a-priori rule) fixed the bid constant at
$0 (5/6 corridor-years show curtailment conduct in negative-hub hours; the
PNW corridor flips to net EXPORT). But the pin-check
(`_caiso104_firm_pin_check.py` on the fresh A-leg) found both firm blocks
PINNED at `dispatch == min_gen == pmax × availability` in 1.0000 of capable
hours in all three years — the caiso-77 floor (`caiso_firm_import_
selfschedule=True`) is live in the keeper recipe (also in the keeper's own
recorded scenario_config), so the granted bid swap is provably byte-inert
and FINDING-caiso103 §3's "interior / 1.7-2.5 GW withheld" attribution was
an artifact of its unit-year-p99 interior proxy on pinned month-varying
dispatch. Owner ruling on the evidence: RE-CHARTER the evening lane — a
follow-up re-decomposes Q1 with a pin-aware method (bounds from floors npz +
fleet_only caps, never the p99 proxy); the floor→$0-bid replacement (which
the §1 conduct measurement supports and the live floor contradicts) is a
candidate for that re-charter. The evening residual and the hub-separation
defect (model λ 8-40 $ below the measured hubs in Q1) remain REAL and OPEN.

**Arc 2 — M1 (belly): built, solved twice, REFUTED.** Full implementation
committed (rule-23 derive `derive_caiso_charge_allocation.py` → 24-value
hod shares + da_frac 0.8399/0.7994/0.7603, reproducing FINDING-caiso102 §1
exactly; `ScenarioConfig.caiso_charge_allocation_schedule`, default off;
`dispatch._build_storage_alloc_rows` — the ask's per-day S[d] eliminated
exactly by Fourier-Motzkin into per-day fleet-charge floor rows, no layout
change; 11 new tests + 167 regression green). B-leg v1
(`2026-07-20-caiso-104-m1-v1`): battery charge collapsed 4.7/8.6/13.0 TWh →
ZERO — root-caused to a COMPOSITION defect (trace v1 shares of 1e-5..3e-3
in hods where the caiso-99 envelope's charge cap is exactly 0 make any
positive daily volume infeasible); support rule fixed A PRIORI
(SUPPORT_MIN_SHARE = 0.005, renormalized). B-leg v2
(`2026-07-20-caiso-104-m1-v2`): the mechanism did everything it claimed
mechanically — floors bind in 0.50-0.65 of charging-day×active-hod slots,
charge reallocates toward overnight/pm-shoulder, volume holds within
+3.5/+6.1/+3.9 % — and the belly λ still did not move (+6.0→+5.9 /
+6.6→+6.6 / +4.3→+4.1). REJECTED on pre-registered gates 1 (belly must fall
all three years) and 3 (2024 volume +6.1 % vs ±5 %); evening/overnight/C1/
C3c protections all held. Structural reading: the measured DA bundle is
itself ~72 % belly, so the marginal stored MWh still prices mostly at belly
duals — allocation CANNOT decouple a price effect that comes from the
volume being priced at the RT margin at all. The belly lane has now refuted
BOTH conduct-supported families (bid-cost: caiso-100/101; allocation:
caiso-104); the FINDING §3b re-charter pointer is the DA-vs-RT price basis
itself (reality's charge clears at DA prices, the backcast scores RT λ —
measure the charge-weighted DA-RT belly wedge before proposing anything).

**Arc 3 — DAM-outage intake (owner-directed) opened.** CAISO's daily
Curtailed and Non-Operational Generator prior-trade-date reports fetched
and committed: 1,094/1,096 trade days 2023-2025 (2 real publication gaps;
dual filename conventions handled), consolidated to per-MRID windows
(`caiso-dam-outage-windows.parquet`: 794k episodes, 1,548 resources).
Remaining stages handed off: RESOURCE ID → ORIS crosswalk (rule-19 design
decision: exclude AMBIENT_DUE_TO_TEMP episodes — that phenomenon is owned
by `temp_dependent_derate`), schema/clean_io intake, unit-level
DAM-before-CAMPD loader precedence (CAMPD stays the fallback per the owner
directive), single-delta A/B.

Registered: `2026-07-20-caiso-104-m1-v1`, `2026-07-20-caiso-104-m1-v2`
(both PROBE/REJECTED); retention pruned caiso-85/-87/-89. Housekeeping
note: `check_registry_payload_parity.py` flags pre-existing gaps in OTHER
lanes (nyiso-65 sidecar + NYISO/NEISO keeper payloads) — not touched per
per-ISO lane isolation; their lanes should repair them.

Next number: caiso-105.

## 2026-07-20 — CAISO-105: belly DA/RT basis wedge measured (third family CLOSED, no mechanism), pin-aware Q1 re-decomposition lands BOTH windows on the intertie supply curve; floor→$0-bid NOT filed; DAM-outage crosswalk committed

**Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED; measurement-only session —
no mechanism armed, no B-leg, nothing registered.** Fresh same-machine
`caiso102_repro_A` reproduces the keeper ladder digit-for-digit (belly
+6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4). Full
record: `results/calibration/FINDING-caiso105-basis-pin-decomp-2026-07-20.md`.

**Arc 1 — belly price-basis wedge (caiso-104 §3b re-charter): MEASURED and
CLOSED.** `_caiso105_da_rt_basis.py`: the charge-weighted DA−RT belly wedge
is +3.6/+1.1/−0.3 (IFM weights; RTD +4.6/+1.7/+0.1; model-charge
+4.8/+2.1/+0.3) against a belly residual of +6.0/+6.6/+4.3 — wrong magnitude
AND wrong year-shape (wedge shrinks to ≈0 by 2025, residual persists; wedge
smallest in 2024 where the residual peaks). DA sits slightly ABOVE RT in the
belly, so re-basing the LP's charge to DA could not pull the model down.
Derive-first verdict: NO mechanism, no ask. All three storage-conduct
families are now closed (bid-cost caiso-100/101; allocation caiso-104;
price-basis caiso-105) — the belly residual is NOT a storage-charge artifact.

**Arc 2 — pin-aware Q1 re-decomposition (caiso-104 owner re-charter):
executed with true LP bounds** (floors npz min_gen + fleet_only caps;
`_caiso105_evening_q1_pin.py`). EVENING Q1: CA λ is EQUALIZED to a WECC node
in 76/100/97 % of hours — the price-setter is the elastic hub-priced import
rung (import interior 217-811 MW; thermal interior tens of MW; battery
envelope bound only 8-36 %; λ +9.6/+10.4/+12.3 below the cheapest available
CT offer). The caiso-103 "withheld firm GW" attribution is definitively
replaced. BELLY Q1 (over-price tail, --window belly): the model imports
+3740/+3271/+4215 MW avg vs measured +1106/+487/+1837 in exactly those hours
(import tranche interior in 78-91 %, 1.8-2.3 GW; battery discharge ZERO;
measured RT < 0 in 22-56 % of the hours vs model 5-25 %). UNIFIED DIAGNOSIS:
the WECC intertie supply is hub-anchored and too elastic in both directions —
belly imports too deep at hub prices (props λ above the surplus-collapsed
RT), evening margin hub-equalized (holds λ below the hub-separated RT). Next
mechanism family (owner-ask territory, rule-1 guardrail — measured
condition-derived depth/direction, never a fitted throttle): condition the
intertie depth on the observable surplus/tightness state, both directions
(the WEIM clean-transfer tranches already carry the conditioning machinery).

**Arc 3 — floor→$0-bid replacement NOT filed.** The pre-measured candidate
(caiso-104 §1) fails its own efficacy test on the fresh bytes: the Q1
price-setter is the economic import rung, not the pinned firm blocks; the
forced negative-λ firm MWh (PNW 2.9/7.8/4.6 TWh/yr) coincide with a BOUND
corridor and high CA λ (curtailment CA-inert), and the only CA-visible slice
(DSW 20-90 GWh in negative-CA-λ belly hours) would raise deep-negative belly
hours — worsening the +6 over-price. Un-promoting part of caiso-77 for
zero-to-adverse gain is refused; the $0-bid form stays available for a future
intertie redesign.

**Arc 4 — DAM-outage intake: crosswalk stage DONE** (caiso-104 handoff §3):
`derive_caiso_dam_resource_crosswalk.py` +
`data/raw/reference/caiso-dam-resource-crosswalk.csv` — 139 thermal resources
→ 88 plants (token matcher + non-thermal/sub-15-MW exclusion + 10 EIA-860
hand-verified prefix pins + 6 false-positive excludes; details in the
FINDING §5). Remaining: schema-first clean_io intake, rule-19 ambient
exclusion, DAM-before-CAMPD loader precedence, single-delta A/B — dedicated
session.

Next number: caiso-106.

## 2026-07-20 — CAISO-106: intertie-elasticity MEASURED (derive-first); evening exhaustion is admissible + owner ask drafted, belly held back

Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4,
C5a(2024 CAVEAT)}); no mechanism armed, no leg registered. Executed the
caiso-105 intertie-elasticity re-charter: MEASURE the state-conditioned
conduct before proposing any LP form (rule 1). Instrument (committed):
`scripts/probes/_caiso106_intertie_elasticity.py` — pure raw-data (EIA-930
CISO corridor interchange + WECC hub DA LMP + CA actual LMP + EIA-930
net-load), NO solve, conditioned on net-load (quintiles + FIXED GW bands) and
hub-negative state, with the caiso-81/86/87 CV/LOYO honesty gates.

**Arc 1 — EVENING intertie EXHAUSTS (admissible).** Measured TOTAL net import
saturates and BACKS OFF as CAISO tightens: fixed-band p50 ~5.1-5.4 GW / p95
~7.6-8.6 GW around net-load 20-30 GW, declining to ~4.5 / ~6.6-7.0 GW in the
tightest band [30,45) GW — the West is ramping-tight at CAISO's sunset too, so
the import margin is spent, not elastic. Every populated fixed-band p50/p95
PASSES (CV 0.02-0.20); the year-relative tightest-quintile p95 ceiling
7055/6875/7555 MW, CV 0.040, LOYO ≤ 7.8 %. This is the rung behind the evening
under-price (−5.8/−4.9/−1.1): the model fills the evening margin with elastic
hub-equalized import (caiso-105 §2: CA λ = a WECC node in 76/100/97 %, 10-12 $
below CT entry) instead of climbing the domestic rung. Drafted owner ask
`docs/handoffs/caiso-106-evening-intertie-exhaustion-ask-2026-07-20.md`
(M-EVE-EXH-1: a measured net-load-conditioned evening net-import CEILING) with
pre-registered estimation + A/B + LOYO gates and explicit kill conditions —
then **WITHDRAWN by its own binding check** (Arc 3): the ceiling is inert for
the evening.

**Arc 2 — BELLY surplus-collapse is real but NOT year-stable (held back).**
Direction unanimous: deepest net-load quintile TOTAL net import mean
−2078/−2207/−1174 MW, export share 91/92/80 % (hub-negative: export 73/70/45 %,
measured RT<0 66/78/65 %) — the corridor REVERSES to export where the model
imports +3-4 GW at hub prices (caiso-105 §4). But the DEPTH fails every gate:
year-relative deepest-quintile p95 CV 0.531 (LOYO 28-416 %); even the FIXED-band
p50 response drifts (CV 0.33-0.37). Root cause: belly conduct depends on the
WEST-WIDE surplus state that CAISO net-load doesn't observe (same CA net-load
pairs with a flush or a tighter West), compounded by 2025 non-stationarity
(belly net-load reaches −7.2 GW). The evening escapes this because at sunset the
West is correlated-tight, so CAISO tightness proxies the neighbor. Verdict
(rule 1): no LP form on an unstable measurement — the belly needs a west-wide
observable (candidate: the Palo Verde / Malin hub LEVEL) as a follow-on lane.

**Arc 3 — binding check INVERTS the ask (single-year 2024 diagnostic).**
Keeper-recipe repro (`caiso106_binding_2024`, un-registered) model TOTAL net
import vs the measured envelope (`_caiso106_binding_analysis.py`): EVENING model
+4165 MW mean (p95 +5745) — LESS than measured +4557, far below the measured
p95 ~7-7.6 GW → the volume ceiling is SLACK in every band → the ask's KILL
condition #1 fires. The evening under-price is a PRICE/merit-order defect (the
marginal import prices at hub-equalized, 10-12 $ below reality's marginal
supply), NOT a volume-exhaustion defect. BELLY model +3619 vs measured +994
(+2.6 GW over-import) → the ceiling BINDS in the deep-surplus bands — but that
arm's depth is the one that FAILED year-stability (Arc 2). So the volume lever
belongs to the belly (unstable depth) and the evening needs a PRICE lever
(inelastic exhaustion premium) — two distinct lanes, neither ready to file. The
drafted ask is WITHDRAWN (no mechanism on refuted evidence); re-charter in the
ask doc §7 (EVENING measured RT-over-hub premium; BELLY hub-LEVEL-conditioned
depth). Derive-first holds: measure each before any ask.

**Arc 4 — DAM-outage intake (priority 3):** advanced on main by PR #2669
(`src/market_sim/data/caiso_outages.py` + tests + loader-wiring) while this
lane ran — not duplicated here. #2546 delete+re-gate remains a dedicated-session
item.

Full record: `results/calibration/FINDING-caiso106-intertie-elasticity-2026-07-20.md`.
Next number: caiso-107.

## 2026-07-20 — CAISO-107: both re-chartered intertie lanes NOT READY on any CAISO-observable state — evening premium wrong-signed + unstable, belly depth NOT stabilized by hub level; lane re-charters onto import supply-curve pricing; keeper UNCHANGED

Executes the caiso-106 re-charter (ask doc §7), derive-first, measurement-only.
Keeper `2026-07-19-caiso-102-hourfix` (NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)})
UNCHANGED; ladder unchanged (belly +6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1,
overnight +0.8/−0.0/+1.4); no mechanism armed, no solve, nothing registered.
Instrument (committed): `scripts/probes/_caiso107_intertie_recharter.py` — pure
raw-data, reuses the caiso-106 primitives (`_load`, windows, fixed net-load
bands, CV/LOYO gate).

**LANE 1 — EVENING RT-over-hub premium: WRONG-SIGNED + year-unstable → NOT
filed.** Measured mean(CA RT − DA hub) in the evening, conditioned on the
observable tightness, is NEGATIVE in exactly the state the mechanism targets:
tight ([20,45) GW) mean RT − max(hub) = −17.1 $/MWh (positive in 0 % of tight
band-years), RT − min(hub) = −9.3 (positive 11 %) — CA RT prints BELOW the DA
hub when CAISO is tight because the DA hub spikes with the correlated-tight West
(PALO DA $145/$96/$64 vs CA RT $78/$62/$54 in [30,45)). An exhaustion premium
lifting the marginal import ABOVE the hub would push tight-hour λ the wrong way.
It also fails stability: tightest-quintile premium −73/−31/−8 (max-hub, CV 0.72,
LOYO ≤ 559 %) and −34/−21/−6 (min-hub, CV 0.57); per-band $ gate FAILs every
tight band (CV 0.31–0.62) and sign-flips across transition bands. Confound: the
hub is DAY-AHEAD, CA RT is real-time, and the evening CA DA−RT basis is large
(+7.7/+8.5/+43.3 in tight bands) — a clean premium can't even be defined against
a DA hub. Reconciles with caiso-103 §6 ("RT ≈ at/above hub"): that was measured
in the MODEL's Q1 under-price hours (a model-residual state, unobservable in raw
data), not the tightest net-load; on the observable it's wrong-signed.

**LANE 2 — BELLY depth on hub LEVEL: NOT stabilized (CV WORSE than net-load) →
NOT filed.** Belly p50 TOTAL net import by PALO/min-hub LEVEL band is CV 0.49–1.62
— worse than the net-load conditioning that already failed (caiso-106 §3, CV
0.33–0.37). Same hub level pairs with net EXPORT in 2023 and +900–1300 MW net
IMPORT in 2024/25 ([−2,8) band); the p95 ceiling also fails (CV 0.16–0.29). The
hub−CA basis is CV 0.71–0.89 with import-side bands sparse — also FAIL. Root:
the DA hub level is itself non-stationary (2025 more solar/EDAM) and the CA belly
transfer depends on the full west-wide balance a single hub price doesn't
summarize.

**Unifying read + re-charter.** Both defects are model-λ-formation problems whose
corrective quantity is only cleanly defined against the MODEL's own state, not
any raw CAISO observable — the caiso-103 §6 root cause is the static-priced FIRM
import blocks ($28/$48 contract proxies under `caiso_perhub_firm_base`) pinning
λ below the hub when marginal. The right-signed lever is import SUPPLY-CURVE
re-pricing (marginal firm/import rung prices at the live endogenous hub dual,
forward-reproducible by construction), NOT a conditioned raw-data envelope.
EVENING exhaustion-premium lane CLOSED; BELLY volume-ceiling remains right-signed
but has no admissible identification (held pending a west-wide surplus-QUANTITY
observable or a belly-tranche re-pricing). Neither filed.

Full record: `results/calibration/FINDING-caiso107-intertie-recharter-2026-07-20.md`.
Next number: caiso-108.

---

## caiso-108 (2026-07-20) — P0 GATE ATTRIBUTION: the keeper's blockers are an import/gas VOLUME defect, not the price ladder — intertie-reprice lane STOPPED, keeper UNCHANGED

**Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET). No solve, no
mechanism armed, nothing registered.** The caiso-108 charter required a P0 gate
attribution BEFORE any P1 intertie build, to break the four-session
measure→refute loop. P0 done; the P1 condition ("only if C3c/C4/C5a are shown to
be intertie/ladder-driven") is FALSE, so the chartered P1 is not executed.

**The three failing gates all root to ONE cause.** Scored from committed
artifacts (`scripts/calibration_verdict.py`): FAIL = C3c (scarcity tail,
SUPPORT), C4 (gas hourly corr, SUPPORT), C5a (CO2, **LOAD** — the only
load-bearing fail). Decoding the keeper's run payload, every year the model
**over-imports 6–10 TWh and under-dispatches gas 5–14 TWh** (2023 gas −13.66 TWh
/ net-import +8.28; 2024 −6.61 / +9.65; 2025 −5.40 / +6.35), a near 1:1
substitution. Imports carry zero CO2 in the model → the substitution IS the
−11% C5a miss (scaling model CO2 to the actual gas TWh lands on the actual, so
C5a is a gas-VOLUME not a rate problem). C4 fails on NRMSE/level (r 0.84–0.91
good, level low) — the high-r/low-level signature of uniform economic
under-dispatch. C3c under-forms because cheap firm imports cap peak λ below the
$200 band.

**The chased ladder residual lives in PASSING gates.** C3a (mean LMP) and C3b
(shape) both PASS. The belly +6/evening −5 $/MWh ladder caiso-104/105/106/107
chased is a shape wiggle whose belly-over/evening-under cancel in the mean — not
a keeper blocker. Four sessions tuned a residual inside already-passing gates.

**Why the chartered P1 would not flip a failing gate.** The chartered P1 reprices
the marginal firm-import rung to the live hub, gated on the evening residual. But
(1) it is a PRICE change and the blockers are VOLUME — in the belly (where the
+2.6 GW over-import that dominates the annual gap sits) the live hub is
low/negative, so repricing "to the live hub" leaves the firm rung cheap midday →
belly over-import and CO2 unchanged; and (2) the evening residual is in passing
C3a/C3b, so zeroing it leaves C5a (LOAD) + C4 failing. Pre-registering
"evening resid → 0" as the P1 primary gate would reproduce the loop.

**Re-charter (caiso-109):** the import/gas substitution itself — why the model
prefers 6–10 TWh of imports over CA gas — scored on **C5a / C4 / C3c**, NOT the
±5 $/MWh ladder. Lever family still plausibly the firm-import supply curve
(caiso-103 §6 static $28/$48 firm blocks too cheap/available), but as a
VOLUME/availability lever. Derive-first first measurement: is the gas
under-dispatch economic (import offer stack underprices gas) or physical (gas
fleet clips its ceiling)? DO-NOT-REDO adds: the evening firm-rung PRICE reprice
gated on the evening residual — targets a passing gate, cannot move C5a.

Full record: `results/calibration/FINDING-caiso108-gate-attribution-2026-07-20.md`.
Next number: caiso-109.

## caiso-109 (2026-07-21) — P0 ECONOMIC-VS-PHYSICAL: gas under-dispatch is ECONOMIC (physical closed), but the chartered firm-rung lever is REFUTED — the over-import is the BELLY/daytime clean-import DEPTH; owner-ask raised, keeper UNCHANGED

**Session 2026-07-21 (CAISO-109 — P0 diagnosis, NO SOLVE; keeper
`2026-07-19-caiso-102-hourfix` (NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)})
UNCHANGED, no mechanism armed, nothing registered.** Model & actual gas hourly
reconstructed from committed artifacts only — the keeper's own per-plant
dispatch (`plants[].m`), the CAISO CEMS bench (`plants[].campd`), and the
keeper-proxy `caiso104_m1_B` (gas within 0.25 %) for hourly LMP/import. No solve
needed. Instrument: `scripts/probes/_caiso109_econ_vs_physical.py`.

**VERDICT — ECONOMIC. Physical is ruled out on the bytes.** In the
under-dispatched gas hours (66–70 % of all hours): model gas is at >90 % of its
own annual peak in **0.0–0.4 %** of them (never pinned), gas peaks at 18–19 GW
vs 26 GW nameplate (26–31 % headroom even at the annual peak), CEMS ran the gas
fleet **1.27–1.31×** higher there (the capacity physically existed), and the
model LMP is below the cheapest CA CCGT MC in 37–66 % (gas priced out). The LP
CHOSE imports over available CA gas.

**The substitution is ~1:1 on the CEMS basis (the caiso-108 −13.66 was the
corrupted 930 NG cell).** On the honest CEMS gas actual (`gas_cems_grid +
gas_cogen_grid`): gas gap −8.2/−6.6/−5.4 TWh ≈ net-import over +8.3/+9.7/+6.4 TWh.
Solar is model-*over*, so the excess import displaces **gas, not solar**. Closing
the ~8 TWh over-import recovers the gas → closes C5a.

**PIN STATE — firm rung PINNED and NOT the culprit (chartered lever refuted twice).**
`caiso_firm_import_selfschedule=True` floors both firm tranches at
`min_gen == pmax × availability`, so their $28/$48 price is inert bookkeeping —
an offer-price change is byte-inert (the charter's KILL). And decomposition shows
the pinned firm floor is only **69–89 % of actual imports**, correctly shaped
(backs off midday), and does **not** over-import; a firm-floor availability derate
would deepen the evening/overnight under-import and miss the belly. Both the
firm-rung price form and the firm-floor availability form are dead.

**WHERE the over-import lives — the BELLY/daytime clean-import DEPTH.** Over-import
by window: overnight +0.1/+0.6, **belly (h10–15) +2.1/+2.5**, evening −0.0/−0.3 GW
(slightly UNDER). It sits above the pinned firm floor (low midday) — the economic
import layer runs +2.4/+2.7 GW in the belly vs actual ≈0.5 GW, de-committing
~1.0–1.2 GW of midday gas. The armed belly supply is the clean-depth tranches
(daytime-clean caiso-94 capability 4994/5563/5770 MW; surplus/overnight-clean),
priced at the **raw hub with EF 0 (zero carbon)** — so midday a zero-carbon import
undercuts CA gas (which also pays the CARB adder).

**This is caiso-106/107's belly defect, whose CA-observable derivation caiso-107
already refuted.** caiso-107 L2 tried the belly depth on CA **price** observables
(net-load / PaloVerde hub level / hub−CA basis) — all fail year-stability (CV
0.33–1.62). Its §2 root cause: the CA belly transfer depends on the full
**west-wide surplus QUANTITY** (WECC solar+hydro+load), which no CA price
summarizes. caiso-107 tested prices, not a west-wide surplus quantity — the one
un-refuted lever class.

**Owner-ask (raised, no form armed pending grant):** the chartered firm-rung
lever family is refuted; the belly-depth-on-CA-price lever is refuted (caiso-107).
Which P1 direction — (A) a **west-wide surplus-QUANTITY** constraint on the
daytime/surplus clean-import capability (structural, forward-regenerable, the
untested observable class; scope: new mechanism + likely a WECC-neighbor EIA-930
intake); (B) a **midday gas commitment/min-load** floor (keep the ~1.2 GW of
midday gas online, less belly room for imports; risk C8 forced-energy); or (C)
file P0 and re-charter west-wide surplus as its own structural charter
(caiso-110)? Per derive-first, no form is armed without a grant on a specific LP
construction.

**DO-NOT-REDO carried forward:** firm-rung offer-price reprice (pinned,
byte-inert); firm-floor availability derate (firm floor is not the culprit;
deepens evening/overnight under-import); belly-depth re-derivation on any CA
price observable (caiso-107 L2); any residual-fitted throttle/haircut on the
depth (rule 1/23/25).

**P1-A (owner GRANTED the west-wide surplus-quantity gate) — DERIVE-FIRST KILL.**
Before building, measured whether a west-wide surplus QUANTITY stabilizes the
belly import depth (`_caiso109_westwide_surplus.py`, pure EIA-930 BALANCE, all 66
BAs already on disk; no fetch, no LP). Conditioning the measured CISO belly (hod
10–14) net import on the WECC-West (Region NW+SW) aggregate solar / solar
penetration / net-gen surplus — at p50, at the p95 ceiling, and inside CAISO's
own solar-peak — **every signal FAILS the CV≤0.20/LOYO≤0.25 gate**, the second
observable class to fail after caiso-107's CA prices. Signature: a monotone
CA-side year-drift — belly net import rises +743→+1234→+1868 MW (~+560/yr) at
EVERY fixed west-surplus level (CA belly solar +1.5 GW/yr, storage ~2×), a drift
no import-supply observable removes. Also the relationship is POSITIVE (West
flush → CAISO imports MORE, physically correct), so the "shrink depth when West
flush" hypothesis is backwards; the over-import is a LEVEL/non-stationarity
defect. Verdict (rule 1): lever (A) NOT filed — the belly transfer is endogenous
to the co-evolving CA+West fleets; no conditioned depth gate is forward-stable.
Redirect re-raised to owner: (1) endogenous WECC import node (structural, the
right fix, a MAJOR multi-session charter — EIA-930 BALANCE data shown on disk);
(2) midday gas commitment/min-load (P0 §6 B, one-session, risks C8); (3) file +
re-charter as caiso-110. No form armed pending grant. Full record:
`results/calibration/FINDING-caiso109-westwide-surplus-derive-2026-07-21.md`.

**Owner GRANTED (2) build the endogenous WECC node — foundation delivered this
session (LP wiring + A/B = caiso-110).** Design/handoff:
`docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md` — replace the
static clean-depth tranches at the existing `WECC_import` node (already carries
the COI/Path-46 ties) with a real neighbor that clears endogenously against
CAISO, so the belly transfer co-evolves with both fleets (the only forward-stable
form, given both conditioned-depth levers are killed). Data foundation committed:
`data/dictionary/schema/wecc-west-supply.schema.yaml` +
`scripts/data/derive_wecc_west_supply.py` (EIA-930 BALANCE Region NW+SW → clean
`wecc-west-supply` frame via `write_clean`; verified West demand ~54–57 GW, solar
6.8/9.5/11.8 GW belly-peaked & growing, net export +2.2 GW). Foundation finding:
the reduced "measured-surplus supply curve" (Option B) is DEGENERATE — West
renewables never exceed its ~55 GW demand, so the export is a price/congestion
outcome, not a surplus threshold ⇒ the full co-optimized zone (Option A) is the
build. No core LP touched (rule 26/27; the wiring is caiso-110). Keeper UNCHANGED.

Full record: `results/calibration/FINDING-caiso109-gas-underdispatch-economic-2026-07-21.md`.
Next number: caiso-110.

## caiso-111 (2026-07-21) — FRESH-LOOK SCOPING: the belly over-import has TWO structural drivers (NEW export-floor asymmetry + import-depth pricing), BTM/demand-netting is clean, solar is Lever-D under-curtailment, granularity is not the lever; field survey shows every CAISO model uses a bidirectional/endogenous West and none publishes error bars as tight as our C-gates; endogenous WECC node (caiso-110) REINFORCED; keeper UNCHANGED

**Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4,
C5a(2024 CAVEAT)}); measurement-only, NO SOLVE, nothing registered.** Research/
scoping charter (derive-first). Instrument (committed):
`scripts/probes/_caiso111_belly_attribution.py` — full belly energy-balance
attribution from committed artifacts + raw EIA-930/HSL (keeper-proxy
`caiso104_m1_B` hourly + the caiso-109 CEMS-basis gas reconstruction). Full
record: `results/calibration/FINDING-caiso111-belly-drivers-and-field-survey-2026-07-21.md`.

**R1 — BTM/solar/demand.** (a) Demand basis CLEAN: the keeper's
supply-consistent series is EIA-930 metered demand (already net of ~15+ GW BTM
PV), reconstructed CEMS-anchored (caiso-80), dispatched against FOM-only supply
— BTM is single-netted, not double-netted or missing. Not a driver. (b) The P0
"solar +2.5–3 TWh over" is exactly `model − delivered` (+2.48/+2.54/+3.04 TWh)
= Lever-D UNDER-curtailment: `caiso_solar_deliverability` is ON but curtails
only 0.03/0.63/0.44 TWh vs actual 2.51/3.17/3.48; k=0.15/floor=0.50 under-shoots
~4–40×. Real, independent, supporting lever (secondary in magnitude, +0.8 GW
belly). (c) NEW **export-floor asymmetry**: reality net-EXPORTS in 1235/963/799
hrs/yr (14.1/11.0/9.1 %, mostly the Apr–Jul belly), but the model's
`WECC_import` node is inject-only (min net import = 0 MW), so it imports where
reality exports. Belly wedge (model−actual net import) +2.58/+2.63/+2.24 GW
decomposes ~half **export-hours** (+1.37/+1.38/+0.94, of which reality<0 "floor"
part +0.69/+0.53/+0.38) + ~half **import-hours** (+1.21/+1.25/+1.30). In belly
export-hours the model is +3.2–4.3 GW off (actual −1.66 vs model +1.6/+2.6/+1.9).
Model oversupply dumps 1.7 TWh WECC_PNW + 0.5 TWh WECC_DSW, **0 in every CA
zone** → tie phenomenon, not CA-locational. TWO drivers, not one; the
export-floor is reachable by neither the import-depth lanes nor the killed
observable-conditioning lanes.

**R2 — zone granularity NOT the lever.** Residual is system-level (gas
under-dispatch uniform across 66–70 % of hours, caiso-109; model dump 0 in every
CA zone; the defect is the tie sign/price). Finer intra-CA granularity cannot
move it. No zone should be added.

**R3 — measured inputs.** Highest-value = measured delivered West hub LMP (Palo
Verde/Malin), largely already on disk (`measured_import_hub_prices`), the exact
input the caiso-110 West-MC fix needs — DMM 2024 corroborates the level (DSW $31
/ PNW $49). WEIM GHG-attribution filed 2nd; CEC BTM PV not needed (R1a); RA
must-offer / 60-day disclosure low-value.

**R4 — how others run CAISO + acceptable results.** Every production/academic
model (WECC ADS/GridView nodal; CPUC RESOLVE/E3 + Astrapé SERVM zonal; PLEXOS
WECC nodal; NREL Cambium/ReEDS) uses a **bidirectional, endogenously-cleared**
WECC import (hurdle-rate zonal or full nodal — ADS hurdle rates both ways,
RESOLVE explicit 5,000 MW export limit) and **un-nets BTM PV** (gross load + DG,
or supply-side ELCC). Our inject-only static-tranche node is the outlier on both
counts. NONE publishes backcast error bars as tight as our C-gates: ADS
validates procedurally (unserved-load tally), RESOLVE on the input side (scale
to CEC forecast), PLEXOS uses MAE/RMSE/SMAPE as tools with no threshold; the one
quantitative academic dispatch backcast (PyPSA-Eur, arXiv 2606.16486) accepts
~21 % price SMAPE as good AND shows the SAME gas-under-dispatch signature we
have. **Our gates are ambitious, not loose — keep them;** the field lesson is to
adopt the bidirectional/endogenous West structure the export-floor points to.

**R5 — endogenous WECC node REINFORCED.** It fixes BOTH halves: bidirectional
tie (export-floor) + endogenous West price (depth). The export-floor is a second
symptom of the same missing structure; import pricing stays central (import-hours
half). Field-standard; West price DMM-corroborated.

**Recommended next single-delta A/B — L1a (bidirectional-tie diagnostic) before
the full West-MC build:** give the existing tie an export path priced at the
measured West hub, isolating the export-floor half without the endogenous
fleet's 84-min tie-pinned degeneracy. Pre-registered (single-delta vs fresh
`caiso102_repro_A`, 3 years one bundle, in-session): PRIMARY C5a → 0 (gas rises,
no overshoot >+7 %); net import → 28.9/32.4/36.2 TWh with belly export hours
appearing; C4 NRMSE<0.30 r≥0.70; C3c up; GUARD C3a/C3b STAY PASS; C8 budget;
rule-22 LOYO. KILL → escalate to L1b (caiso-110 West-MC fix + ε flow_cost) if
the import-hours depth keeps C5a failing. Supporting: L2 re-derive Lever-D k to
curtail the measured 2.5–3.5 TWh. NO-GO: zone granularity. KILLED: CA-price /
west-surplus-quantity depth gates (caiso-107/109).

Next number: caiso-112.

## caiso-112 (2026-07-21) — export-floor ROOT-CAUSED to a P1-bridge min_gen clamp (a genuine bug, not a missing sink); fix wired behind `caiso_wecc_export_floor` (default off, byte-identical off); un-clamp A/B UNBOUNDED → L1a′ chartered; keeper UNCHANGED

*(Housekeeping 2026-07-26: this entry and caiso-113 below were merged to main
by PR #2792 on 2026-07-22 and then lost to a later full-file overwrite of this
log — the "phantom merge" the caiso-114/116 handoff notes flagged. Restored
verbatim from the PR head blob, `13ccbc6b`.)*

**Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.** The caiso-111 "export-floor"
(model min net import = 0, the tie can never reverse) was ROOT-CAUSED to a genuine
bug, NOT a missing export sink: the per-hub keeper already builds two priced
measured-hub export legs (`WECC_PNW_export_MALIN` / `WECC_DSW_export_PALOVRDE`,
`pmin = -corridor TTC`) that clear correctly in P0 (−1103 MW belly export), but the
scored P1 pass runs on the RA must-offer bridge, whose shared floor tail
`pipeline.commitment._bridge_floored_fleet` did `new_min_gen = np.maximum(base_min_gen,
bridge_floor)`; for the export legs `base = -TTC`, `bridge_floor = 0`, so
`np.maximum(-TTC, 0) = 0` clamped the export bound to zero in every scored hour →
min net import = 0 (proven by P0 primal, LP col-lower dump −4800 in P0 vs 0.000 in
P1, and HiGHS reduced-cost). Fix: new `ScenarioConfig.caiso_wecc_export_floor`
(default False) threads `preserve_negative_min_gen` into `_bridge_floored_fleet` —
raise `min_gen` only where `bridge_floor > 0`, else keep the base (negative export)
bound, so the legs net-export in P1 as they already do in P0. Byte-identical off the
flag (verified). The minimal un-clamp A/B (different machine, handoff) recovers the
export-floor but is UNBOUNDED: the legs also wheel the caiso-77 must-flow firm
imports back out, so net link flow never reverses, the corridor export ENVELOPE
never binds, and the legs over-export ~16 TWh gross vs the measured ~1.5 → 2024 gas
+7.6 % (trips the +7 % guard) and mean λ 29.9→38.7. Chartered L1a′ (bound the leg
dispatch at the measured p95 net-export envelope) as the single-delta successor.
Full record: `docs/handoffs/caiso-112-export-floor-handoff-2026-07-21.md`.

Next number: caiso-113.

## caiso-113 (2026-07-22) — export-floor L1a′: bound the un-clamped export legs at the measured p95 net-export envelope; single-delta A/B (3yr, same-machine, in-session); B RECOVERS the export-floor + fixes the over-correction but BREAKS the C3a guard (over-price) and leaves C5a failing → REJECTED, keeper UNCHANGED, escalate to L1b

**Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}).**
Continuation of caiso-112: the minimal un-clamp over-exports (~16 TWh gross) because
the corridor `caiso_corridor_flow_limit` export cap is a LINK-level (net-flow) bound
that never binds while the firm imports keep net flow positive. **L1a′ bound (single
delta vs the un-clamp):** new injector
`model.interchange.caiso.inject_caiso_wecc_export_leg_envelope` (in
`apply_caiso_seam_injections`, gated by the SAME `caiso_wecc_export_floor`) tightens
EACH export leg's own hourly `min_gen` from `-TTC` up to `-(measured p95 net-export
envelope)` — the SAME `measured_corridor_flow_envelope(direction="export")` ceiling
the corridor groups use — so the leg net-exports at most the measured surplus per
hour and collapses to ~0 in the evening ramp. No fitted value (rule 13/25); composes
with the P1 bridge `preserve_negative_min_gen`; byte-identical off the flag. 7 tests
(`tests/test_caiso_export_leg_envelope.py`); the bug fix + the bound stay in the tree
regardless of the keeper decision. Confirmed active in the scored solve (per-year
"export legs capped" log). A = `_caiso102_repro_A` (flag off) reproduces the keeper
digit-for-digit (2024 net 42.03 / gas 54.4). Registered B =
`2026-07-22-caiso-112-export-floor`.

**A/B (same-machine, in-session, 3yr one bundle — rule 16):**

| year | actual net | A net | B net | gas tgt | A gas | B gas | B gas% | B net-exp TWh | B belly-exp hrs |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 28.9 | 37.2 | 32.9 | 74.2 | 60.6 | 63.5 | −14.5% | 0.89 | 355 |
| 2024 | 32.4 | 42.0 | 37.3 | 61.0 | 54.4 | 56.7 | −7.0% | 0.30 | 165 |
| 2025 | 36.2 | 42.5 | 40.6 | 51.6 | 46.2 | 46.7 | −9.4% | ~0.2 | 127 |

**What the bound ACHIEVES:** recovers the export-floor (belly export present; NET
export 0.3–0.9 TWh, the measured order of magnitude, NOT the un-clamp's ~16 TWh
gross), FIXES the over-correction (2024 gas +7.6 %→ −7.0 %, NO year over the +7 %
guard), and moves net import + gas toward actual/target every year. C5a CO2 improves
(2023 −11.1 %→ −7.0 % CAVEAT, 2024 −9.1 % CAVEAT→ PASS, 2025 −12.1 %→ −11.2 %).

**What KILLS it — the C3a guard.** Official scores (`calibration_verdict`):
A fail set {C3c, C4, C5a} (C3a PASS); **B fail set {C3a, C3c, C4, C5a}** — B ADDS a
C3a failure (mean LMP over-price +11.5 % 2024 / +12.7 % 2025). The pre-registered
gate GUARD C3a stays PASS is VIOLATED. Root: the export legs price at the FIXED
measured West hub, so exporting the belly surplus pulls CA λ UP to the hub — the same
fixed-hub pricing that under-prices imports over-prices exports. C5a still fails 2025
(−11.2 %): the import-hours DEPTH half is untouched by an export bound (net import
stays ~4–5 TWh over actual). C4 marginally better (NRMSE 0.333→0.328, still >0.30).

**Decision (owner direction 2026-07-21): REJECTED.** B does not clear (C3a guard
broken; C5a import-depth remains) → keeper stays `2026-07-19-caiso-102-hourfix`;
B is a rejected probe on the dashboard (`2026-07-22-caiso-112-export-floor`). Per the
pre-registered KILL, **escalate to L1b — the endogenous WECC West node
(caiso-110 West-MC fix)** — which addresses BOTH open halves at once: it clears the
West price ENDOGENOUSLY (collapsing in surplus) instead of pinning to the fixed hub,
so the belly export no longer over-prices (fixes C3a) AND the import depth
co-evolves with the West fleet (the C5a import-hours half). The caiso-112 bug fix +
the L1a′ bound remain in the tree (default off, byte-identical off) as the
bidirectional-tie foundation L1b builds on.

Next number: caiso-114.

## caiso-114 (2026-07-23) — L1b endogenous WECC-West node (Option A), West gas priced at the MEASURED intertie hub (hub-alone): fixes C5a + C3c and the tie clears INTERIOR (caiso-110 flood/degeneracy resolved), but BREAKS the C3a guard via an EVENING over-price → REJECTED probe; keeper 2026-07-19-caiso-102-hourfix UNCHANGED

*(Housekeeping 2026-07-26: merged from
`docs/handoffs/caiso114-calibration-log-entry.md`.)*

**The build.** Wired caiso-110 Option A: `WECC_import` becomes a real co-optimized
WECC-West neighbor zone (own measured demand + a reduced import-priced fleet from
the `wecc-west-supply` frame), superseding the static import tranches / per-hub
split / clean-depth injectors (rule 18). Gate `caiso_endogenous_wecc_node`
(default off, byte-identical off). THE caiso-110 fix (`build_wecc_west_thermal_mc`):
the West GAS units (gas_cc/gas_ct) are re-priced hour-varying at the MEASURED
delivered West intertie hub — the tie-capacity-weighted MALIN(4800)+PALOVRDE(10623)
blend — via an `mc_base` override; coal keeps its physical PRB vom. HUB-ALONE, no
CARB adder: hub+CARB over-corrected the 2024 diagnostic (net import -3.1 TWh, gas
96.4 — tie flipped to net export) because the measured intertie LMP is the price
imports actually CLEARED at and CA gas is already CARB-priced, so hub-alone
competes evenly. 0 fitted params (rule 1/13/25); 7 tests.

**A/B (single delta, 3 yr one bundle, same-machine).** A = caiso102_repro_A
(flag off). B = caiso110_endog_B (registered 2026-07-23-caiso-114-endogenous-west).

| year | net import B (actual) | gas A→B (actual) | tie interior |
|------|----------------------|-------------------|--------------|
| 2023 | 32.3 (28.9) | 60.6→64.4 (74.2) | 63.8 % |
| 2024 | 31.7 (32.4) | 54.4→62.6 (61.0) | 73.2 % |
| 2025 | 37.1 (36.2) | 46.2→50.3 (51.6) | 68.3 % |

The tie clears INTERIOR every year (no flood / no tie-pinned degeneracy — the
caiso-110 84-min KILL is RESOLVED; solves ~9-10 min/yr).

**Verdict (NOT-YET, fail {C1, C3a, C4}) vs keeper NOT-YET {C3c, C4, C5a}:**
- FIXES C5a (CO2, the keeper's load-bearing fail → PASS) — the PRIMARY goal.
- FIXES C3c (scarcity tail → PASS).
- still fails C4 (gas hourly NRMSE 0.35-0.45, r 0.78-0.87 — both keeper and B).
- BREAKS C3a (mean LMP +11.0/+15.6/+10.5 %, the must-stay-PASS guard).
- BREAKS C1 (2023 CC_REGULAR -4.7 TWh — the high-hub-year under-gas).

**C3a diagnosis (no re-solve) — the over-price is ENTIRELY EVENING; belly IMPROVES.**
Zonal-mean LMP by hour, A→B: evening (18-21) **+18/+12/+4** $/MWh (2023/24/25);
belly (10-14) **-5/-2/-1** $/MWh. The design's self-limiting belly thesis HELD
(belly not over-imported/over-priced, unlike L1a''s fixed-hub belly over-price).
The regression: the measured intertie hub over-states the marginal EVENING export
price to CA — in interior-tie evening hours the West sets CA's import-zone LMP at
its own internal evening-scarcity hub ($56+), above where West energy actually
cleared to CA on the margin.

**Determination: REJECTED probe** (pre-registered gate: promote iff C3a STAYS PASS
and C5a→0; C3a did not). Keeper stays 2026-07-19-caiso-102-hourfix. But L1b is the
first mechanism to fix C5a via a forward-stable ENDOGENOUS structure (not a fitted
depth — caiso-107/109 killed those) with the tie interior, so the STRUCTURE is
right; only the West-node EVENING clearing is wrong.

**Next (caiso-115): refine the West-node evening clearing, do NOT fall back to a
fixed hub (charter KILL).** The belly/overnight are correct; the evening West offer
is too high as CA's marginal setter. Candidates (derive-first, single delta each):
(a) the evening hub embeds a WECC-wide scarcity CA's own ORDC should price, not the
import — test decoupling the West evening offer from the internal hub scarcity tail;
(b) the tie should BIND in the evening (West at export limit, CA gas marginal)
rather than the West setting an interior price — test an ε flow_cost / evening TTC;
(c) revisit the MALIN/PALOVRDE evening blend. Also close C1 2023 + C4. rule-22 LOYO
before any promotion.

## caiso-115 (2026-07-23) — FRESH-LOOK DIAGNOSIS: C4 is NOT the intractable frontier — decomposed, it is ~75 % sub-ceiling day-to-day scatter (a mild reduced-network limit) + ~25 % fixable diurnal structure that is the SAME belly-import (C5a) + evening-displacement (C3c) defect; the keeper already PASSES C4 in 2/3 years on the clean CEMS basis and its sole fail (2023) is a benchmark-basis artifact; C5a-fix and C3a-guard ARE separable; keeper UNCHANGED

*(Housekeeping 2026-07-26: merged from
`docs/handoffs/caiso115-calibration-log-entry.md`. NUMBER COLLISION: two
parallel 2026-07-23 sessions both took caiso-115 — this fresh-look diagnosis
and the netrev-margin keeper promotion further below. Both entries kept
verbatim; ordinals are never renumbered.)*

**Measurement-only, NO SOLVE, nothing registered.** Keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}). The
caiso-114 handoff's fresh-look charter: answer (A) can C5a-fix + C3a-guard
coexist, and (B) what is C4, with measurement not another tweak. All from
committed artifacts + raw EIA-930 via `scripts/probes/_caiso115_c4_freshlook.py`
(no LP; keeper-proxy `caiso104_m1_B` for the model hourly, reproduces the keeper
C4 gas digit-for-digit). Full record:
`results/calibration/FINDING-caiso115-c4-freshlook-and-separability-2026-07-23.md`.

**Inv 1a — cross-ISO C4 benchmark: the gate is NOT mis-specified, CAISO is a
marginal-NRMSE outlier, not a broken one.** Scoring every ISO keeper's gas
`dispatch_corr` (r≥0.70, NRMSE≤0.30): ERCOT 0.07–0.08, PJM 0.10–0.11,
MISO 0.15–0.20, NEISO 0.12–0.17, NYISO 0.17–0.21 — all PASS comfortably;
**CAISO 0.26–0.33 is the sole outlier**, FAIL 2023 only. But CAISO's gas **r
(0.836–0.908) is in-family** with the import/hydro peers (NYISO 0.804–0.888) —
the *shape* is fine, the *magnitude* is high. The handoff's "maybe the gate is
mis-specified for a reduced-network model" is REFUTED: nobody hovers near the
line, including import-heavy NYISO/NEISO.

**Inv 1b — C4 is TIMING, not volume; ~75 % is irreducible scatter.** Reproducing
the gate's CEMS-basis gas series and decomposing the residual: the flat annual
volume bias (the −8/−7/−5 TWh gas deficit that *is* C5a) is only **13–18 %** of
the C4 SSE — so **fixing C5a barely moves C4** (refutes caiso-108's "C4 moves
once C1/C5a are fixed"; explains the caiso-114 paradox where L1b fixed the volume
yet C4 stayed bad). A *perfect* hour-of-day fix leaves NRMSE 0.221–0.251; a
perfect hod×month fix leaves 0.202–0.225 — **~75 % of C4 is day-to-day scatter**,
the reduced-model floor (invariant to the cogen/fill approximations; sits right
at the peer-worst NYISO 0.207). The removable ~25 % is two real signatures:
**CC_REGULAR under-dispatch belly+overnight** (−1.0 to −1.3 GW belly; imports
substitute = C5a) and **CT_PEAKER evening under-run** (0.2–0.9 vs 1.7–3.3 TWh, a
3.3–6.8× under-run = C3c).

**2023 fail is a BENCHMARK-BASIS artifact (escalation).** CEMS-anchor onset is
2024, so 2023 — the only C4-failing year — is scored on the EIA-930 NG cell
(0.333 FAIL). On the *same CEMS basis as 2024/25* it is **0.271 → PASS**. The two
bases differ ~0.06 NRMSE > the 0.033 fail margin; 2023 was kept on 930 "for
continuity — the two agree there" (bench-basis FINDING 2026-07-12 §5.2), true at
the annual level but NOT at the hourly grain. Moving 2023 to CEMS (scorer-only,
no re-solve) would make the keeper pass C4 all three years.

**Inv 1c + Inv 3 — the evening circle.** The model fills the evening ramp (17–21)
with maxed CC + over-hydro + over-import, capping the CA price at $43–65 (below
the scarcity tail → C3c FAIL) so the CT peaker fleet stays idle despite available
capacity (model annual max 3.4–4.6 GW) — the under-run is ECONOMIC. Against raw
EIA-930: hydro annual matches but the model **over-concentrates it into the
evening (+0.5–0.65 GW)** and under-runs the belly; the **belly over-import
(+1.9–2.5 GW)** is the dominant C5a/C4-belly driver (confirms caiso-109). The
keeper's `hydro_dispatch_envelope` (p95) is **already ON** — it cut the
over-hydro from ~1.5 GW (caiso-72 STEP-0) to ~0.5 GW, but p95 is a loose ceiling
the perfect-foresight LP saturates every evening; `caiso_firm_import_shape`
(caiso-72 #2) is off. Storage is NOT the current driver (keeper runs
`storage_vintage_ramp` + `caiso_storage_shape_anchor`; the caiso-98 flat-8-GW
oversizing is already corrected). Network granularity is not the systematic lever
(caiso-111; dump=0 in every CA zone) — it may underlie the scatter floor but that
part is sub-ceiling and untestable without a nodal build.

**DECISION FRAMING (the handoff's ask).** C5a (belly over-import) = **(i) fixable
mechanism** — belly-scoped import-volume correction, separable from the evening.
C3c + C4-evening-CT = **(i) fixable mechanism, hard multi-lever refinement** —
tighten `hydro_dispatch_envelope` and/or arm `caiso_firm_import_shape`; disclosed
risk = over-tightening over-prices the evening (exactly L1b's C3a break, which
raised the evening with *expensive imports* instead of *domestic peakers*).
C4 bulk (day-to-day scatter) = **(iii) mild representational limitation** (~0.22
floor, sub-ceiling; a belly+evening fix moves C4 ~0.27 → ~0.23, passing).
2023 C4 fail = **(ii) benchmark-basis artifact** — escalate the CEMS-vs-930 2023
basis. **Question A: YES, separable** — belly-volume (hod 10–15) and evening-price
(hod 17–21) are different hours/mechanisms; L1b broke C3a only because the
endogenous West coupled them (fixed belly volume AND re-set the evening price to
the West hub). **Question B: C4 is not the ballgame** — ~75 % a mild reduced-net
limit + ~25 % the same import/evening defect as C5a/C3c; keeper passes 2/3 years
on the clean basis.

**Recommended next single-delta (owner to select; derive-first).** Two separable
forward-stable A/B deltas vs a fresh `caiso102_repro_A`, 3 yr one bundle, LOYO:
(1) **belly** — endogenous West or physical belly-import cap, gated C5a→0 with
**C3a STAYS PASS**; (2) **evening** — tighten the hydro envelope / arm the shaped
firm-import base, gated C3c-tail-up + CT-evening-up with **C3a STAYS PASS** (2023
tail watched, rule 1). DO-NOT-REDO carried: firm-rung reprice (pinned, caiso-109);
belly-depth on CA-price/west-surplus observables (caiso-107/109); fixed-hub West
fallback (caiso-114 KILL); gating the evening on the ±5 $/MWh ladder inside
passing C3a/C3b (caiso-108).

Next number: caiso-116.

## caiso-116 (2026-07-23) — EXECUTE-THE-BELLY-LANE, DERIVE-GATED: candidate (a) (the endogenous WECC-West node) CANNOT be evening-scoped to keep C3a while fixing C5a — the modeled West (EIA-930 NW+SW) net-exports only ~19 TWh/yr but CAISO imports 29-36, and L1b matched CA's import VOLUME only by over-generating that ~9-17 TWh/yr gap as gas exported at the intertie hub (the marginal unit that breaks C3a); C5a-fix and C3a-guard are COUPLED through that proxy over-export, so BOTH scopings fail by derivation; the fleet-bound delta was built + tested then reverted (over-corrects C5a + infeasible); keeper UNCHANGED

*(Housekeeping 2026-07-26: merged from
`docs/handoffs/caiso116-calibration-log-entry.md`.)*

**Derive-first gate, mechanism built-then-refuted, NO SOLVE, nothing registered.**
Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}).
The caiso-115 handoff chartered this session to EXECUTE the belly (C5a) lane by
building one pre-registered single delta — candidate (a), the caiso-114
endogenous WECC-West node, evening-scoped so the West does not set CA's evening
LMP. A derive-first pass (rule #1, before committing a mechanism) uncovered a
DATA-SCOPE gap the caiso-114/115 handoffs did not anticipate. Full record +
reproduction: `results/calibration/FINDING-caiso116-endogenous-datascope-2026-07-23.md`
/ `scripts/probes/_caiso116_endogenous_datascope_derive.py` (no LP).

**Inv 1 — the data-scope gap (load-bearing).** Modeled West net-export capability
(`wecc-west-supply` net_export_mw = EIA-930 NW+SW net gen − demand) vs CAISO net
import (raw EIA-930 CISO): **19.4/18.9/19.2 TWh** West vs **28.8/31.9/36.0 TWh**
CA → GAP **9.3/13.0/16.9 TWh**, WIDENING as CA's import demand grows. L1b
(`caiso110_endog_B`) matched CA's volume (32/32/37 TWh) ONLY by having the West
over-generate that gap as gas exported at the measured intertie hub — LOW in the
belly (the C5a fix worked) but HIGH in the evening where it is the marginal unit
and SETS CA's import-zone LMP (+$4-18, the C3a break). The over-export is a proxy
for CA's true out-of-region imports; pricing it at the hub (marginal) breaks C3a.

**Inv 2 — the West cannot supply CA in any block.** West exportable-gas surplus
(gas_mw − own-load gas need) vs CA net import, GW: belly 0.5-1.2 vs 0.7-1.9;
evening 0.7-1.8 vs 3.3-3.9; night 3.3-3.5 vs 5.3-6.2. The West's surplus is
almost all gas, tracks the tie shape (~0 belly / +2 evening / +4 night) but is
far below CA's actual import everywhere.

**Inv 3 — bounding the West is INFEASIBLE.** The modeled West itself net-imports
**22/23/24 % of hours** (net_gen < demand, worst shortfall ~7.3 GW) from WECC
regions outside the modeled NW+SW aggregate and the single CA tie. So the
fleet-bound scoping (cap West thermal at measured output — which WOULD force CA
gas marginal and preserve C3a) cannot be solved cleanly: no CA-connected backstop
represents the West's real (eastern) imports without either under-pricing (cheap
export) or over-inflating CA gas (CA→West in the West's own peak). The gap bites
both directions.

**Inv 4 — empirical anchor.** Committed `caiso110_endog_B/metrics.json`: C5a
**PASS**, C3c **PASS**, C3a **FAIL** (C3b PASS, C4 FAIL) — the coupling, measured.

**Inv 5 — min-hub under-fixes C3a.** The price-temper scoping (offer West gas at
min(MALIN,PALOVRDE) vs the tie-weighted blend; caiso-114 note c) shaves only
**$7.1/$2.5/$1.2** off the evening offer vs the +$4-18 break — the break is the
West gas BECOMING MARGINAL at the hub, not the hub's level. Refuted.

**Determination.** C5a-fix and C3a-guard are **coupled** through the West's
~13-18 TWh proxy over-export; candidate (a) is **NOT viable for the belly lane**
as built. This SHARPENS caiso-115: the belly-volume (hod 10-15) and evening-price
(hod 17-21) lanes separate in HOURS, but the endogenous node re-couples them
through the volume gap (L1b broke C3a because it HAD to over-export gas at the
hub to hit CA's volume, not merely because it re-priced the evening).

**Mechanism built then reverted.** `caiso_wecc_west_thermal_shaped` (cap West
coal/gas availability at measured `coal_mw`/`gas_mw` — the fleet-bound scoping,
the cleanest rule-13-admissible knob, same measured-availability class as the
node's VRE/hydro shaping) was implemented in `wecc_west_fleet.py` + wired +
unit-tested (2 tests), then **reverted**: the derive shows it over-corrects C5a
(bounding the West to 19 TWh under-supplies CA's 29-36 → +9-17 TWh more CA gas,
past the +7 % gate) and is infeasible (Inv 3). Rule #1 forbids solving through a
mechanism that isn't real; the design is preserved in the FINDING (re-buildable
in minutes once the scope is reconciled). Keeper stays `2026-07-19-caiso-102-hourfix`.

**Next (caiso-117), redirect — reconcile the West import scope, or hand the
evening to CA's own scarcity (in preference order):**
1. **Close the data-scope gap:** broaden the modeled West beyond NW+SW (or add
   the West's own eastern/Baja import as an inframarginal price-taker to
   `wecc-west-supply`) so its net-export capability matches CA's 29-36 TWh. Then
   L1b's over-export becomes REAL and inframarginal → CA gas sets the evening →
   `_thermal_shaped` becomes feasible and C3a-preserving.
2. **Do the EVENING lane first/jointly** (the caiso-115-named lane): tighten CA's
   OWN evening scarcity (`hydro_dispatch_envelope` lower percentile / daily
   budget; arm `caiso_firm_import_shape`) so CA's domestic peakers set the evening
   price and the West import becomes inframarginal by comparison. The belly and
   evening lanes are COUPLED — work them together, not separately.
3. **Fall back to candidate (b), belly-HOUR-scoped and West-physically grounded:**
   a belly-only cap at the West's measured belly deliverability (~1-2 GW, a
   West-side physical quantity — Inv 2 — NOT CA's residual flow) fixes the belly
   over-import while leaving the evening untouched (C3a preserved). Must be
   belly-scoped (an all-hours net-export cap hits the same gap → over-corrects
   C5a) and level-tied to physical capability, not the residual (rule 13 /
   caiso-107/109).

**DO-NOT-REDO (added):** endogenous-node fleet-bound scoping (thermal-shaping) on
the NW+SW frame — over-corrects C5a + infeasible until scope reconciled;
min-hub / MALIN-PALOVRDE re-weight — under-fixes C3a (marginality, not level).
Carried: fixed-hub West fallback (caiso-114 KILL); belly-depth on CA-price /
west-surplus-quantity observables (caiso-107/109); firm-rung reprice (pinned,
caiso-104/109).

Next number: caiso-117.

## 2026-07-23 — caiso-115: gas-offer net-revenue margin → PROMOTED CAISO KEEPER (owner directive, rule 1/11)

Charter rollout of the `gas_offer_net_revenue_margin` mechanism (NEISO keeper
`neiso-61`) to CAISO. **Identification landed** (branch
`claude/gas-offer-net-revenue-isos-1px5vg`): CAISO `phys_*` keys on all five gas
classes (`_CAISO_OFFER_CURVE`, cited to the measured
`caiso_campd_marginal_hr_summary.csv` p50s) + anchor **4.7964 $/MMBtu**
(`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, mean of the keeper delivered-gas overlay
2023–2025 = 6.95/3.37/4.06). Byte-inert flag-off (947 gas tranches marked up
flag-on, heat rates identical / markups zero flag-off).

A/B: same-HEAD `replay_keeper` of the `caiso-102-hourfix` recipe — BASE arm
(flag off) vs MARGIN arm (single delta `gas_offer_margin=true`), full 2023–2025
(`scripts/probes/netrev_margin_ab.py`). My RT duration-NRMSE probe:

| year | gas vs anchor | C3a base→margin | RT dur-NRMSE base→margin |
|---|---|---|---|
| 2023 | 6.95 (≫, compress) | −6.8 → −7.2 % | 0.390 → 0.411 |
| 2024 | 3.37 (<, firm)     | −9.4 → −6.9 % | 0.429 → 0.445 |
| 2025 | 4.06 (≈, neutral)  | −3.9 → −2.7 % | 0.292 → 0.288 |

**Verdict: PROMOTED to CAISO keeper — `2026-07-23-caiso-netrev-margin-keeper`
(owner directive 2026-07-23; rule 1 + rule 11).** The margin arm's **rubric
verdict is IDENTICAL to the caiso-102 keeper**: NOT-YET with the SAME C1–C8
status (C3a `price_mean` PASS, **C3b `price_shape` PASS**, and the pre-existing
`price_tail`/`dispatch_corr`/`co2` FAILs are CAISO's ledgered frontier, not
introduced here). Keeper auditor PASS 0/0. My stricter duration-NRMSE probe
shows a small shape dip in the two high-gas years — that dip is the **removal of
the multiplicative form's masking**, not an offer-form defect: the old
`mult × HR × fuel` curve over-priced gas offers at above-anchor gas, silently
compensating for CAISO's ledgered missing scarcity/import mid-tail (C3c FAIL,
caiso-107/109/111). The structurally-correct fuel-INVARIANT net-revenue form
(how real bidders express an above-cost offer — a $/MWh target, not a heat-rate
multiple) EXPOSES that root cause rather than papering over it (rule 11), and
keeps all six ISOs on one offer approach (rule 1). Zero fitted scalars: the
markup LEVELS are the already-registered `offer_curve_by_group` surface, only the
markup's gas-elasticity changes 1→0; anchor derived, phys basis measured. Zero
DOF delta vs caiso-102 (attestation carried forward + the measured-input note).
Closing the mid-tail stays the separate ledgered import/scarcity lane
(caiso-107/109/111). caiso-102 stays on the dashboard as the prior keeper /
same-box multiplicative-form comparison; 2022 holdout not touched (NOT-YET, not a
CALIBRATED promotion). Bundle `caiso_netrev_margin`.

## caiso-117 (2026-07-24) — belly-hour West-physical import cap BUILT + 3-yr A/B: fixes the belly VOLUME (import → toward measured, gas +1.9/+2.9/+2.3 TWh, C5a improves, evening untouched by construction) but BREAKS C3a in 2025 (+8.6 % → +13.2 %) by worsening the pre-existing belly PRICE over-pricing — belly-volume and belly-PRICE lanes are COUPLED; mechanism stays built default-OFF; keeper UNCHANGED

*(Housekeeping 2026-07-26: compact entry added from
`results/calibration/FINDING-caiso117-belly-cap-c3a-coupling-2026-07-24.md` —
this session's entry was never appended to the log.)*

*(Correction 2026-07-26, fast-tier triage: "mechanism stays built default-OFF"
below is FALSE for main — the caiso-117 session pushed only LEG 1 (probe +
unit tests + FINDING, PRs #2828/#2835); the mechanism source
(`caiso_belly_import_cap`, `CAISO_BELLY_HOURS`/`CAISO_BELLY_EXPORT_PERCENTILE`,
`build_caiso_belly_import_cap_group`, `measured_west_belly_export_cap`) was
never pushed and the session branch is deleted, so it is unrecoverable from
git. `tests/test_caiso_belly_import_cap.py` fails collection on main as an
orphan. Escalation D1 in `docs/handoffs/fast-tier-triage-2026-07-26.md`:
rebuild from the FINDING's Inv-2 spec when the joint belly delta goes live, or
explicitly drop the tests as rejected-probe residue.)*

*(**Resolution 2026-07-26 (owner decision, fast-tier escalation follow-through):
DROP.** `tests/test_caiso_belly_import_cap.py` is C-DELETED as rejected-probe
residue — it guarded source that main never carried, and rebuilding the
mechanism standalone is exactly what the FINDING's DO-NOT-REDO forbids. The
FINDING's **Inv-2 section is the rebuild recipe** and now carries the matching
correction; `scripts/probes/_caiso117_belly_cap_derive.py` (the derive half)
did land and stays on disk. The belly price-formation lane (caiso-118 redirect
#1) re-implements the flag, the two constants and both builders from that spec
when the joint delta goes live, and owns its own unit tests.)*

Executed the caiso-116 redirect #3: `caiso_belly_import_cap` (ScenarioConfig,
default False) — a belly-scoped (hod 10-15, `np.inf` outside) simultaneous
interface group over both per-hub corridor links, capped hour-by-hour at the
per-(month × belly-hod) **p90 of the West's measured net export**
(`wecc-west-supply`, a West-side physical quantity, rule 13; p90 is the
tightest percentile that never under-cuts CA's measured belly import — GATE-B).
6/6 unit tests; byte-identical off. Full 3-yr A/B vs a fresh keeper replay:
belly import 3.07/3.88/3.74 → 2.05/2.44/2.22 GW (measured 0.65/1.34/1.77),
never below measured; gas +1.9/+2.9/+2.3 TWh; evening import +0.02 GW / price
+$0.8 (the caiso-114 L1b evening leak does NOT recur); C3b/C3c intact. KILL:
C3a rises +2 to +4.6 pp every year (all from the belly) — 2023/24 absorb it,
2025 (+8.6 % base) goes to **+13.2 % FAIL**. Root (Inv 4): the model belly is
PRICE-over-priced even before the cap (2024 belly $26.3 vs actual DAM $14.9;
marginal = hub-priced import ~$26, not reality's curtailed-solar ~$0-15);
capping imports promotes gas (~$28) to the margin and worsens it. Rule-1
signature: a structurally-correct mechanism surfacing a different root cause.
**Redirect: the belly PRICE-FORMATION fix is the new load-bearing lane; the cap
re-arms only JOINTLY with it.** DO-NOT-REDO: the belly cap as a standalone
single delta; tightening the CA-side corridor p95 envelope (CA-side flow
observable, rule 13).

## 2026-07-24 — caiso-118 BELLY PRICE-FORMATION derive: both suspects REFUTED; the belly over-price + over-import are ONE defect (the model UNDER-COMMITS belly gas). NO SOLVE, nothing registered. Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a})

*(Housekeeping 2026-07-26: merged from
`docs/handoffs/caiso-118-belly-price-log-entry.md`. NOTE: this entry's
"actual belly gas 8.5/9.6/10.5 GW" headline and the ~8-10 GW floor charter it
redirects to were REFUTED the same day by caiso-119 R1 — the "actual" was the
corrupted EIA-930 `NG: NG` cell caiso-109 had condemned; the honest hole is
~0.5-1.3 GW (CEMS basis). The DIRECTION (under-committed belly gas) survives.
Kept verbatim as the historical record; see the caiso-119 entry below.)*

**Derive-first (rule #1), measurement-only, register nothing** (the caiso-115/116/117
precedent). Full finding: `results/calibration/FINDING-caiso118-belly-price-undercommit-2026-07-24.md`.
Reproduction: `scripts/probes/_caiso118_belly_price_derive.py` (no LP; keeper-proxy
`caiso104_m1_B` hourlies + raw EIA-930 CISO + `load_renewable_profiles` +
`measured_import_hub_prices` + `measured_corridor_flow_envelope`).

**Charter:** the caiso-117 redirect — make the model belly clear near actual ~$15
(from ~$26) before re-arming the belly VOLUME cap, testing one of two named
suspects: (1) a curtailable-solar $0 marginal rung, or (2) pricing belly imports
at the measured (low) belly hub.

**Both suspects refuted; a third, unifying mechanism identified.**

- **Suspect 1 (solar rung) — REFUTED.** `caiso_solar_endogenous_spill` is ON, so
  the deliverability derate is already SKIPPED and the LP gets full solar
  potential. Measured belly solar spill is only **0.5–2.0%** — solar is already at
  its bound (inframarginal). No suppressed pool; a $0 rung is inert; re-enabling
  the derate would REMOVE solar and RAISE the belly. The model even dispatches MORE
  utility solar than reality generates (47.2 vs 44.6 TWh).
- **Suspect 2 (belly-hub import reprice) — REFUTED/COUPLED.** The model's OWN
  solved WECC border duals are already low in the belly (PNW $2.6–6.3, DSW
  $14.6–28.7) and the belly hub series it reads is already DSW $10.5 (2024). The
  cheap border is corridor-CAPPED (import at/near the corridor belly cap) and the
  next economic import tranche ($36 ladder) is above CA's domestic gas, so CA
  clears at gas. Repricing the remaining tranches down is a VOLUME lever (worse
  C5a) — not a C5a-neutral price lever.
- **The lever — the committed-gas belly STATE.** Killer comparison (model vs
  actual belly gas): 2023 4.3 / **8.5 GW**, 2024 3.7 / **9.6 GW**, 2025 2.9 /
  **10.5 GW**. Reality runs **2–3.6× MORE** belly gas than the model yet clears
  LOWER ($15 vs $26) — its committed gas bids min-load DOWN (must-take, never
  marginal), so the belly clears at curtailed solar / the min-load block. The
  model economically backs gas off to a ~2 GW duck trough and OVER-IMPORTS (3.1–3.9
  vs actual 0.7–1.8 GW), so full-MC gas/import sets $26. **C3a-belly-overprice and
  C5a-belly-overimport are the SAME defect** (the missing committed STATE), not two
  coupled-and-opposed lanes. The keeper's `caiso_ra_mustoffer` bridge floors only
  3.2–3.7 TWh/yr (~1.5 GW belly) vs reality's ~10 GW — under-committed by ~5–6 GW.
  This is the ERCOT-63 result ("the model needs the STATE, not the PRICE").

**Why this explains the caiso-117 coupling.** The belly VOLUME cap fixes C5a but
breaks C3a (2025 +8.6 → +13.2%) because it cuts imports and lets **full-MC** gas
fill (raising the belly). With the committed min-load bid-down STATE in place,
cutting imports and running committed gas at its bid-down min-load fixes BOTH — the
volume cap and the price lane stop fighting.

**Redirect (caiso-119).** Single physics-grounded C5a-neutral-or-better delta:
raise the CAISO committed-gas belly floor to the MEASURED committed level (CEMS /
CAISO 60-Day DAM disclosures — the ERCOT-63 template: measured committed-CC min-load
p50 × the P0-committed belly fleet), extending `caiso_ra_mustoffer` /
`caiso_ra_p1_floor_fleet` toward reality's ~8–10 GW. Gate: belly LMP → ~$15, belly
gas → 8–10 GW, belly import → ~1.3 GW (C5a↑), C3a STAYS PASS all years incl 2025,
C3b↑, evening untouched. Guardrails: cited D-4 window + C8 forced-energy budget (at
~10 GW commitment CC_REGULAR exceeds the 30% merchant cap → needs the rule-14 v2.2
grounded-above-budget escalation, D-4 off-window clean + D-1 shape faithful; score
it, don't assert it). KILL if the level is residual-fitted (rule 13), forces gas in
hours the disclosures say the fleet is off (rule 12), or breaks the evening. THEN
re-arm `caiso_belly_import_cap` jointly; LOYO within 2023–2025 before promotion.

**DO-NOT-REDO (added):** curtailable-solar $0 belly rung / re-enabling the solar
deliverability derate (solar 98% absorbed; inert / raises price); repricing belly
imports to the border hub as a belly-PRICE lever (border already cheap +
corridor-capped; pulls volume, worse C5a).

## 2026-07-24 — caiso-119: the caiso-118/118b headline REFUTED on the bytes (corrupted EIA-930 `NG: NG` re-used after caiso-109 condemned it); lane re-scoped to the measured min-load, SOLVED and found near-inert; new attributed defect CT_PEAKER PRICED OUT; keeper UNCHANGED

**Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED** (NOT-YET, fail
{C3c, C4, C5a}). One three-year single-delta A/B solved; nothing promoted.
Records: `results/calibration/FINDING-caiso119-gas-basis-adjudication-2026-07-24.md`
and `FINDING-caiso119-minload-ab-result-2026-07-24.md`. Gates pre-registered
before either arm finished: `results/calibration/caiso119_ab_pregistered_gates.md`.

**R1 — the caiso-118/118b chain is void on magnitude.** Its entire redirect
(floor the belly-committed fleet toward reality's ~8-10 GW) rested on one
comparison: "actual belly gas 8,461 / 9,633 / 10,537 MW vs model 4,260 / 3,721 /
2,947" (2.0x / 2.6x / 3.6x). The MODEL side reproduces; the ACTUAL side is
**EIA-930 CISO `NG: NG` at local hod 10-15** — the same raw 930 gas cell
caiso-109 had already condemned ("the caiso-108 -13.66 was the corrupted 930 NG
cell") and replaced with the CEMS basis. Three independent tests kill it:
T1 LEVEL 1.28 / 1.40 / 1.53x metered CEMS grid gas, the excess drifting upward
every year; T2 SHAPE belly/evening 0.71 -> 0.93 -> **1.20 (INVERTED by 2025** —
claiming CAISO burns more gas in the solar belly than on the evening ramp),
against a rock-stable CEMS 0.52 / 0.53 / 0.53; T3 BALANCE the 2025 claim
(10,537 MW) **overfills** the belly residual (9,838 MW) before a single MW of
battery charging. On the CEMS basis the model's ANNUAL gas is within 1-3 %
(1.03 / 1.03 / 0.99) and the defect is a ~1 GW **diurnal redistribution** —
short 0.5-1.3 GW over hod 8-17, long 0.5-1.2 GW over hod 18-23, duck 0.40 vs
measured 0.53. caiso-118b's DIRECTION survives; its size was ~5x overstated, and
the chartered floor would have forced 5-6 GW of phantom generation (rule 1/13).

**R2 — the honest single delta, solved: `caiso_ra_min_load_frac` 0.26 -> 0.570.**
The keeper's 0.26 is below any physical CC turn-down and below the code default
0.40. MEASURED from CEMS (per-unit p05 of `grossLoad/pmax` over fully-online
`opTime == 1.0` hours, cap-weighted p50 across CC units with >=500 op hours):
**0.565 / 0.570 / 0.570** across 2023-25 — stable to 1 %, and ERCOT's
independently-derived 60-Day-DAM analogue is **0.574**. Arms
`caiso119_base_A` (same-HEAD replay, no delta) vs `caiso119_minload_B`.
**11 of 15 pre-registered gates pass; NO KILL gate tripped in any year; PRIMARY
P1 (belly gap closed >=40 %) FAILS all three.** Belly gas moves -28 / +59 /
+52 MW (8-10 % of the gap at best), direction right in 2024/25.

**R3 — WHY it is inert, from the arms' own `floors/<year>_P1.npz` records.**
Floored MW by mechanism (2024, annual / belly): `firm_import` 3,304 / 1,220;
`nuclear_mustrun` 2,077 / 2,077; `chp_steam` 924 / 924 (1,266,096 cells);
**`ra_mustoffer_bridge` 387 -> 424 / 951 -> 1,046 (24,463 cells)**. The RA bridge
— the ONLY mechanism this parameter governs — owns **24,463 of 1,324,067 floored
cells (1.8 %)** and ~0.4 GW annual-average; the 1.27 M-cell bulk is structural,
D-2-exempt `chp_steam`. Its level is also CAPPED, so +119 % on the fraction gave
**+0.7 %** floored MW per cell, and belly floored MW moved +95 MW — almost
exactly the +59 MW of gas observed. Nothing unexplained. Merchant forced share is
~7 %, far inside the C8 30 % cap: there was never a C8 risk, because there was
never 10 GW of forcing to add.

**Disposition (pre-registered, honoured).** The measured **0.570 is KEPT**
(rule 14 — the accurate input stays even when the fit does not improve; now
demonstrably safe across three years with no KILL) but **NOT promoted** (fails
its primary gate). It is never tuned back toward 0.26 (rules 13/18/25 — that is
how 0.26 got there). The belly-commitment lane is **downgraded, not redirected**:
the true hole is ~250-600 MW grid-delivered, too small to drive C5a/C4.

**R4 — NEW attributed defect: CT_PEAKER is PRICED OUT (cause C).** Model 0.436
TWh vs 4.33 TWh actual (2024) — 10 %. Attributed against all three candidates
from `caiso119_base_A/dispatch/2024_P1.parquet`: all 44 bench peaker facilities
present (80 plants / 834 tranches) so NOT absent; fleet peak 3,542 MW with
588/834 tranches producing so NOT derated; therefore **priced out**. Per plant
model/actual TWh: Panoche 0.019 / 1.42, Sentinel 0.077 / 0.48, Walnut Creek
0.082 / 0.32. Invisible to C1 because its band is absolute (min(2 % of gen,
8 TWh) ~ 5 TWh), so a -4 TWh miss on a 4.3 TWh class passes at a 12.7x relative
error. ~4 TWh of missing energy vs ~250-600 MW for the whole belly hole, and the
most plausible live explanation for the standing **C3c tail FAIL** (a model that
never starts its peakers cannot form a peaker-set tail). **This rescues the
caiso-118b commitment thesis aimed at the right class** — CAISO's RA must-offer
covers peakers, and Panoche is exactly the out-of-market-committed capacity that
obligation exists to hold. GUARDRAIL: only a real obligation-keyed mechanism with
a cited D-4 window is admissible; marking peaker offers down until 4 TWh appears
is rule-1/13 forbidden.

**R5 — the other two chartered threads are settled, no work needed.** RA/LSE
must-offer: NOTHING TO WIRE — `CAISO_RA_MUSTOFFER_GAS_MW` (19,130 / 15,566 /
15,566 MW, DMM) is already in `constants.py` and the quantity gate is a measured
NO-OP (bridged CC fleet 13.7-13.8 GW pmax, inside the published obligation every
year). DAM outages: intaken and wired (`caiso_dam_outages`, default off,
DAM-first/CAMPD-fallback), but the crosswalk is 34 of 90 rows accepted -> 29
plants / 9.78 GW, all CC, **zero peakers**; worth its own rule-14 single-delta
arm, but outage episodes are multi-day and the defect is diurnal, so it cannot
touch R4.

**DO-NOT-REDO (new).** (a) **EIA-930 CISO `NG: NG` as a CAISO gas actual, in any
window** — refuted on level, shape and balance; the actual is the CEMS basis.
(b) Any belly-gas floor sized to 8-10 GW — the target is fabricated. (c)
`caiso_ra_min_load_frac` as a belly-volume lever — 1.8 % of floored cells, level
capped. (d) Quoting the ~99 % floor-binding rate as evidence about commitment —
it is `chp_steam` + `nuclear_mustrun`, both structural and D-2 exempt. (e)
Per-class CAISO work keyed on `bench.plants[].group` — stale for repowered units
(AES Alamitos 315 / Huntington Beach 335 are labelled ST_GAS but their CEMS units
are post-2020 CCGT repowers; the scored `classFull` puts them in CC_REGULAR,
ST_GAS actual is 0.12 TWh in 2024). Use `classFull`.

**Operational note.** HEAD drift is NOT inert for CAISO: replaying the keeper
recipe at current HEAD vs the committed keeper sidecars gives max hourly class
diff 3.2 GW (total energy 0.01 %) — marginal-tie reshuffling. Always solve a
fresh same-HEAD control arm; never A/B against the committed keeper.

**Method note.** caiso-118 and caiso-118b were both derive-first, no-solve
sessions that read as fully evidenced, and the whole chain — headline, mechanism
diagnosis, redirect charter, guardrails — inherited one unvalidated series.
Before a measured "actual" is allowed to SIZE a mechanism: check its level
against an independent meter, its shape against the physics, and its fit against
the energy balance. All three took minutes here and all three failed.

Next number: caiso-120.

## caiso-120 (2026-07-26) — FRESH-EYES REGIME SPLIT on the netrev keeper's own committed sidecars: the belly defect is CONCENTRATED in the actual market's SURPLUS regime (RT ≤ $20, ~half of belly hours) where reality is a hub-priced NET EXPORTER and the model is a 2.6–3.5 GW importer priced $7–14 ABOVE the hub; the firm-regime half is a pure ~2 GW VOLUME error with NO price signature; log restored (112→118 recovered); keeper UNCHANGED

**Measurement-only, NO SOLVE, nothing registered, no mechanism armed.** Keeper
`2026-07-23-caiso-netrev-margin-keeper` UNCHANGED — fresh re-score at HEAD:
NOT-YET, fail **{C3c, C4 (2023 ONLY), C5a}**, C6/C7/C8 PASS (the bundle's
committed `metrics.json` predated its own attestation/diagnostics files and
said C6 UNATTESTED; refreshed via `--write-metrics`, the live status shard was
already correct). Instrument (committed):
`scripts/probes/_caiso120_price_regime.py` — keeper hourly sidecars + measured
RT LMP + measured MALIN/PALOVRDE hub + raw EIA-930 CISO; no gitignored input.
Full record:
`results/calibration/FINDING-caiso120-belly-regime-split-2026-07-26.md`.

**The new fact — split belly hours (hod 10-15) by the ACTUAL price regime.**
In the SURPLUS half (measured RT ≤ $20; n = 810/1116/1077): actual RT
$2.8/−5.2/−0.1 **≈ the raw min-hub** ($5.3/−6.7/−0.8 — reality is
hub-equalized, net-EXPORTING in 57/51/40 % of these hours, mean interchange
≈ 0 to −0.4 GW), while the model imports **2.14/3.35/3.13 GW** (a 2.6–3.5 GW
signed error — it never net-exports one hour in any year; the caiso-112
`caiso_wecc_export_floor` fix is in the tree but default-off and ABSENT from
the keeper recipe) and clears **$4–14 ABOVE the min-hub** (+$11.5/+12.2/+7.3
vs actual). In the FIRM half (RT > $20): the model's price is nearly RIGHT
(+$3.8/+2.0/+1.5) but it still imports 3.6/4.5/4.4 GW vs measured
0.9/2.3/2.4 — a ~2 GW volume error with no price signature, the SILENT half
of C5a (displacing the gas reality runs at approximately the right price).
Distribution grain: the model DOES now form a negative belly tail (2024
belly ≤$0 18.7 % vs actual 27.4 %; all-hours 525 vs 868 h); the compression's
mass error is the >$35 share (35–65 % vs actual 20–39 %).

**What this reframes.** (1) The caiso-117 C3a break was not "volume vs price
opposed" — it was the missing surplus-regime price behaviour (export at the
hub / curtailment-marginal): cap imports without it and full-MC gas sets λ
where reality prints hub-negative. (2) The caiso-113 L1a′ C3a break was the
same lesson from the export side (fixed-hub export pricing in ALL hours;
the regime split says export conduct is a SURPLUS-regime behaviour, where the
hub is low/negative and prints the RIGHT price by construction). (3) The
firm-regime ~2 GW over-import is the caiso-118b committed-state lever at its
HONEST size (caiso-119: ~0.5–1.3 GW diurnal + CT_PEAKER 4 TWh evening) — no
price-side mechanism can see it. **Gate implication for the joint belly
delta: score REGIME-CONDITIONAL quantities** — (i) surplus regime: signed
interchange goes long (net-export hours appear toward the measured 40–57 %),
λ − min-hub → ~0; (ii) firm regime: import → measured 0.9–2.4 GW with gas
filling; C3a then holds by construction instead of two errors cancelling. A
belly delta gated on aggregate import volume alone will reproduce the
caiso-113/117 breaks. **Attribution limit:** WHICH unit sets the model's
surplus-regime λ (min-hub + $8–14; candidates: the carbon-paying import rung
— border adder ≈ $13–16 ≈ the wedge —, gas at a floor, storage-charge
opportunity cost) needs the dispatch parquet → a keeper replay is justified
for that question (rule-15 clause) and is the FIRST step of the joint-delta
session.

**Housekeeping executed.** (a) THIS LOG RESTORED: caiso-112/113 entries
(merged to main by PR #2792 2026-07-22, then lost to a full-file overwrite —
the "phantom merge") recovered verbatim from the PR head blob; caiso-114 /
caiso-115(fresh-look, NUMBER COLLISION with the netrev promotion noted) /
caiso-116 merged from their handoff docs; compact caiso-117 + verbatim
caiso-118 entries added. The log now runs 103→120 unbroken. (b) Keeper bundle
`metrics.json` refreshed (stale-snapshot repair, verdict unchanged).

**Open items carried (unchanged priority):** C4-2023 CEMS-basis escalation
(scorer-only, would clear C4 — caiso-115 fresh-look, still unactioned);
`caiso_ra_min_load_frac` 0.26 still in the keeper recipe (measured 0.570 is
"KEPT" by the caiso-119 disposition but lives only in the rejected probe —
the next keeper candidate must carry it, rule 14/18); CT_PEAKER priced out
(caiso-119 R4, the C3c lane's live lever, obligation-keyed + D-4 window).

## caiso-121 (2026-07-26) — EXECUTED the three standing cheap wins: (1) OWNER RULING moves CAISO 2023 C4 to the CEMS basis → **C4 PASSES all three years, keeper fail set {C3c, C4, C5a} → {C3c, C5a}**; (2) the surplus-regime belly λ is ATTRIBUTED — set by the EF-0 `DSW_surplus_clean` tranche, and **59–101 % of the wedge is DSW→CA corridor congestion, not the rung's price** (border-carbon and committed-gas candidates both REFUTED; family selected = corridor/export-path); (3) the measured min-load 0.570 solved as a keeper candidate and registered — **NOT promoted**, blocked by a STOP-AND-REPORT side finding: re-solving the keeper's OWN recipe at HEAD **FAILS C3a-2025 (+11.49 % vs the committed keeper's +9.97 %)**

Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED (shard untouched).
Two 3-year solves this session: `caiso121_repro_A` (control replay, keeper
recipe exactly — gitignored, NOT registered, FINDING-caiso92b protocol) and
`caiso121_minload_keeper_B` (single delta, registered as
`2026-07-26-caiso-121-minload-keeper`). Full record:
`results/calibration/FINDING-caiso121-surplus-marginal-attribution-2026-07-26.md`.
Instrument (committed): `scripts/probes/_caiso121_surplus_marginal.py`.

**(1) C4-2023 benchmark basis — ESCALATED AND GRANTED (owner ruling, this
session).** `EIA930_NG_CORRUPT_ONSET["CAISO"]` 2024 → 2023. The original onset
kept 2023 on the EIA-930 NG cell "for continuity — the two agree pre-onset";
they do not. Three-source level test on the keeper's committed bytes for 2023:
**EIA-923 67.20 TWh** and **CAMPD CEMS + non-CEMS cogen 68.74 TWh** — two
independent measured sources agreeing within **2.3 %** — against the
fold-in-deflated **930 cell at 74.23 TWh, +10.5 % over 923 and +8.0 % over
CEMS**, far outside the 3 % `VINTAGE_RECONCILE_FRAC` deadband and the same
standard that condemned the cell for 2024+. Deflated-930 over EIA-923 runs
**+10.5 % (2023) → +21.1 % (2024) → +32.8 % (2025)**: a monotone ramp, so any
onset is a threshold on a continuum, not a step at 2024-05. Scorer-only (no
re-solve; C2's gas anchor path was never year-gated, so only C4's gas hourly
fit changes basis) and every CAISO bundle re-scores in place — the rule-20 C8
precedent. Effect: C4 gas 2023 **r 0.838 / NRMSE 0.329 FAIL → r 0.881 / 0.263
PASS**, the best of its three years. Keeper metrics + `status/CAISO.js`
rebuilt; determination still NOT-YET. Closes the caiso-115 fresh-look
escalation, carried unactioned since 2026-07-23.

**(2) Surplus-regime marginal-unit attribution — caiso-120 Inv 4 ANSWERED.**
caiso-105's pin-aware method (bounds = `floors/<y>_P1.npz` `min_gen` +
`run_year(fleet_only=True)` caps; a pinned/at-bound unit cannot set λ, a
strictly interior one's offer EQUALS its zone's λ) re-pointed at the caiso-120
regime split. **The setter is `DSW_surplus_clean`** — the caiso-87 WEIM clean
surplus-depth tranche — strictly interior in **52.8 / 61.6 / 84.1 %** of
surplus-regime belly hours carrying **1.2 / 2.1 / 2.1 GW**.
- **Border-carbon rung REFUTED:** the winning tranche is **EF 0 and pays no
  border carbon at all**; the carbon-paying rungs are interior 0.9–6.3 % and
  the cheapest offers $78–81/MWh, ~10× the surplus λ. The adder-≈-wedge match
  was coincidence and does not even track sign across years.
- **Committed gas REFUTED as the price-setter:** CC_REGULAR interior
  **4.9 / 4.8 / 1.3 %** carrying 1–4 MW, and **62–72 % PINNED** — a volume
  mechanism, not a price-setter. Hydro is co-marginal at 14–22 MW.
- **THE LOAD-BEARING RESULT (all terms on one mask, so they sum exactly):**

  | yr | min-hub | model WECC_DSW λ | model CA λ | wedge | = node−hub | + congestion | congestion share |
  |---|---|---|---|---|---|---|---|
  | 2023 | $5.26 | $5.20 | $9.65 | +$4.39 | −$0.06 | **+$4.45** | **101 %** |
  | 2024 | −$6.65 | −$1.52 | $6.88 | +$13.53 | +$5.13 | **+$8.40** | **62 %** |
  | 2025 | −$0.80 | $2.51 | $7.20 | +$8.00 | +$3.31 | **+$4.68** | **59 %** |

  The model's own southern node is priced approximately RIGHT (−$0.06/+$5.13/
  +$3.31 from the measured min-hub; the marginal tranche's offer goes negative
  in 2024 exactly as the hub does). **59–101 % of the belly over-price is
  DSW→CA corridor congestion rent — CA cannot reach its own correctly-priced
  import node.** The northern node is stranded and drowning (WECC_PNW λ
  −$2.22/−$3.12/−$7.80, negative in 31/52/59 % of surplus hours, 2025 median
  −$20.00, its firm `PNW_hydro_base` block self-scheduled at-cap 47–65 %), and
  **both export sinks dispatch exactly 0.00 MW in all 26,280 hours of
  2023–2025**.
- Physical stack corroboration (model − actual, surplus belly): imports
  **+2578/+3461/+2606 MW**, solar **+1596/+1233/+1563** (the model curtails too
  little — 11/43/41 % of hours), hydro **−1114/−948/−856**, gas
  **−859/−784/−636**, storage charging **+1967/+2049/+2244**.
- **Family SELECTED for the later joint belly delta: corridor / export-path in
  surplus** (owns the majority of the wedge and is the only candidate that also
  explains the missing net-export sign) — the corridor's export-direction
  deliverability envelope (measured p95 net-export, median ~0 GW on the DSW
  leg, derived from *evening* net-import behaviour then applied to midday) and
  a *surplus-scoped* `caiso_wecc_export_floor` (the caiso-113 L1a′ rejection
  was a fixed hub in ALL hours). **Clean-tranche depth demoted to second
  order** (priced near-correctly; at-cap only 0.7/20.8/3.5 % of surplus hours).
  **Committed-state dropped.** NOTHING ARMED — arming either sub-lever is a
  separate owner ask, LOYO-scored before promotion. Pre-registered gates stay
  the caiso-120 REGIME-CONDITIONAL ones, now with **CA λ − WECC_DSW λ → ~0**
  named explicitly as the term carrying the majority of the error.

**(3) Min-load 0.570 (rule-14 execution of the caiso-119 KEPT disposition) —
REGISTERED, NOT PROMOTED.** Single delta `caiso_ra_min_load_frac` 0.26 →
0.570; zero fitted parameters added, one removed. Verdict **NOT-YET, fail
{C3a (2025 only, +11.3 %), C3c, C5a}**; C1/C2/C3b/C4/C6/C7/C8 PASS. The
disposition was pre-registered before any score existed — promote iff
same-or-smaller fail set and no new FAIL — and C3a is a new fail, so: **not
promoted.** The attestation also corrects the netrev keeper's inaccurate
description of 0.26 as "CEMS-measured min-load"; the DOF ledger is unchanged
in count and strictly improved in quality.

**THE BLOCKING SIDE FINDING (§0a of the finding) — the C3a failure is NOT the
delta.** The same-HEAD control arm — identical recipe, **no delta** — also
fails C3a-2025, and *worse*:

| C3a mean LMP | 2023 | 2024 | **2025** |
|---|---|---|---|
| committed keeper | +3.49 % PASS | +8.44 % PASS | **+9.97 % PASS** |
| control arm A (no delta, HEAD) | +4.01 % PASS | +9.36 % PASS | **+11.49 % FAIL** |
| arm B (min-load 0.570, HEAD) | — | — | **+11.30 % FAIL** |

The keeper clears C3a-2025 by **0.03 pp**; HEAD drift since its recorded sha
`abb0fcd` consumes that four times over (CA λ **+0.47/+0.88/+1.35 %**,
CC_REGULAR to −1.24 %, import to +0.93 % — uniformly in the direction that
worsens C5a). Isolated against its own control the min-load delta is
near-inert and its C3a effect is a **0.19 pp IMPROVEMENT** (CC_REGULAR
−0.209/+0.048/+0.031 TWh, CA λ +0.31/−0.25/−0.11 %, belly-surplus gas
−102/+24/−32 MW), reproducing caiso-119's measurement at current HEAD. So the
measured 0.570 stays **KEPT** and is still the value the next keeper must
carry (rules 13/14/18 — never tuned back toward 0.26, whatever the residual
does).

**⚠ CAISO LANE BLOCKED UNTIL THIS IS FIXED: no CAISO delta can be promoted,
because ANY re-solve at HEAD fails C3a-2025.** The keeper's headline C3a PASS
is a property of its committed 2026-07-23 bytes, not of its recipe. Next
CAISO session's FIRST task: bisect `abb0fcd..HEAD` for the commit that moved
CAISO λ. Until then every CAISO C3a-2025 comparison is basis-sensitive and
must carry a same-HEAD control arm — the caiso-119 note, now with a gate flip
behind it rather than a metric wobble.

**Operational note (rule 12).** Two concurrent CAISO per-plant 3-year solves
OOM-killed on the **2025** year (15.2 GW storage fleet; 7.8 GB RSS each on a
15 GB box). Arm B was re-run solo. For CAISO, treat 2025 as single-solve-only
on a 15 GB box — rule 12's "cap at ~2 simultaneous" is the ceiling, and 2025
is over it.

**Open items carried.** CT_PEAKER priced out (caiso-119 R4, the C3c lane's
live lever — obligation-keyed RA must-offer commitment for peakers, D-4 window
required); the joint belly delta (family now selected, gates pre-registered,
owner-gate required); `caiso_ra_min_load_frac` 0.570 still not in the keeper
recipe — blocked by the C3a regression above, not by its own merits.

## 2026-07-26 — caiso-120: keeper re-audit on the guard-corrected CAMPD envelope — RE-TUNE REQUIRED (2025 C3a flips); keeper UNCHANGED. Plus: the resource crosswalk lands, and the instrument reading transforms

Charter execution (campd-economic-layup-fix-charter §8: ADOPTED-AS-IMPROVEMENT,
freeze HELD). Two results this session:

**Keeper re-audit** (`2026-07-26-caiso120-meritguard-a1`, the
caiso-netrev-margin keeper recipe replayed verbatim on the adopted
guard-corrected extract, 2023–2025 one bundle; A0 = the keeper). Restoring
laid-up capacity RAISES CAISO model prices slightly (RA must-offer commitment
interaction, not a scarcity margin): C3a +3.5→+3.6 %, +8.4→+9.2 %, and 2025
+10.0→+11.1 % — a PASS→FAIL flip on a load-bearing criterion. Uniform-direction
drift, LOYO clean, but the flip is the charter-§5 rule-11 condition: re-tune in
this lane. First solve of this arm was discarded and re-run — the fresh
container lacked the `capacity-deliverability` clean partition and
`capacity_deliverability_limits=True` degraded silently to "no limits"
(replay-reproduction checklist: RESULTS-neiso65-crossiso-reaudit §2).

**Resource crosswalk (charter STEP D).** The reviewed
`caiso-resource-eia-crosswalk.csv` goes 34 accepted rows / 29 plants → 58 / 44
of 55 (~20.9 GW), incl. 3 wrong-plant remaps (Alamitos EC→62115, Huntington
Beach EP→62116, Harbor Cogen→50541) and 8 generator-missed rows (Alamitos
steam, Redondo, El Segundo EC). New probe
`_neiso65_caiso_crosswalk_score.py` scores CAMPD-vs-CNOG per-plant on the
crosswalked scope (mrid-deduped — the raw parquet repeats 5.23×). Headline: on
the 34 active plants the extract runs **1.85–2.28× published, 1.52–2.13× after
the guard** — the residual over-count is now measured per-resource at a second
ISO and the whole-fleet-scope excuse is gone. CNOG's big non-operational
blocks (Ormond 1,194 MW, Alamitos steam 927 MW published means) are
mothball/RMR states the model owns via fleet status, not the outage overlay —
excluded from the active-plant scope by construction. Placebo stays inside p95
(shape null); the substance is the level axis. Full numbers:
`results/calibration/RESULTS-neiso65-crossiso-reaudit-2026-07.md` §4.

## caiso-122 (2026-07-26) — the C3a-2025 HEAD regression is **NOT attributed**: `src/market_sim/` is EXHAUSTED and **every state of the CAISO outage extract is REFUTED by solve** (absent / pre-layup / HEAD); the keeper's recorded provenance is **unusable as a bisect anchor** (`git_sha` unreachable, `timestamp` keeps only the original DATE across a replay); STEP 2's measured min-load 0.570 arm scored against a same-HEAD control — **registered, NOT promoted**; keeper UNCHANGED, lane STILL BLOCKED

**(1) The prescribed bisect could not be run, and why that matters.** caiso-121
asked for `abb0fcd..HEAD` over `src/market_sim/`. `abb0fcd` resolves to no
object even after `git fetch --unshallow` (8,839 commits, all origin refs) — a
session-local commit on a branch that did not survive to main. The timestamp
fallback is also unsound: `replay_keeper.py:324` writes
`orig_ts[:10] + new_ts[10:]`, restoring the original **date** and keeping the
**replay's time-of-day**, so a keeper replayed days later still reads
`2026-07-23T22:29:35`. **A committed keeper carries no field that identifies
the basis of its own bytes.** This is a governance defect beyond this lane —
every future "why did this keeper move?" hits the same wall. Recommend a
`basis_sha` written at bundle-write time and never restored by replay.

**(2) The drift is real, reproducible and monotone in year.** Fresh 3-year
same-HEAD control vs the committed keeper (CA demand-weighted λ):

| year | keeper | control | Δ |
|---|---|---|---|
| 2023 | 55.6158 | 55.8950 | +0.502 % |
| 2024 | 37.5464 | 37.9179 | +0.989 % |
| 2025 | 38.0221 | 38.5585 | **+1.411 %** |

caiso-121 measured +0.47/+0.88/+1.35 %; this reproduces it independently. Class
signature: CC_REGULAR −0.456 TWh, import +0.395 TWh — less gas, more imports,
higher λ.

**(3) What was eliminated, by measurement not argument.** `src/market_sim/` is
exhausted: every commit in the window is ISO-scoped elsewhere or gated off, the
one naming CAISO (`31035427f`) reads `caiso_dam_outages` which is
`bool = False`, and `42747a969` (the CAISO resource→EIA crosswalk, 34→58 rows /
~20.9 GW) is consumed **only** by that same default-off path. The outage-extract
family is exhausted by four 2025 solves:

| arm | extract | CA λ 2025 |
|---|---|---|
| committed keeper | — | 38.0221 |
| extract hidden | 0 rows | 36.4778 |
| pre-layup (`6a8f285c5^`) | 5,139 rows | 38.6290 |
| HEAD control | 4,329 rows | 38.5585 |

**No outage state reproduces the keeper**; it sits 0.54–0.61 below all of them.

⚠ **This contradicts the parallel caiso-120 entry above, and the disagreement
should be settled before either is relied on.** That session attributes the
2025 C3a move (+10.0 → +11.1 %) to adopting the guard-corrected extract, from
an A0-vs-A1 pair in which **A0 is the committed keeper's bytes**. Measured here
with a *same-HEAD control* on both sides, swapping HEAD's extract for its
pre-guard content is worth only **−0.07 /MWh (−0.18 %)** — nowhere near the
+1.4 % drift. The two are reconcilable if A0-vs-A1 is picking up the same
unattributed basis drift documented in item (2) *on top of* the guard change,
which is precisely the trap the caiso-119/121 standing note warns about (never
A/B against the committed keeper). If that is right, the charter-§5 "re-tune
required" trigger rests on a confounded comparison and should be re-measured
against a same-HEAD control before any re-tune is undertaken.
A mid-session hypothesis that the keeper had solved with the extract *absent*
was **refuted** on the keeper's own committed sidecar: CC_CHP hourly correlates
**r=0.99343** with the overlay-ON arm and only **r=0.575** with the overlay-OFF
arm (6,742 of ~6,950 derated hours shared). The extract's own sensitivity is
nonetheless large and worth recording: **λ 2.08 /MWh, CC_CHP 2.12 TWh**.

**(4) STEP 2 — min-load 0.570, rule-14 execution. REGISTERED, NOT PROMOTED.**
Single delta `caiso_ra_min_load_frac` 0.26 → 0.570; zero fitted parameters
added, one removed. Both arms at one pinned basis; control NOT registered
(FINDING-caiso92b).

| C3a mean LMP | 2023 | 2024 | 2025 | fail set |
|---|---|---|---|---|
| control A (no delta) | +4.0 % PASS | +9.4 % PASS | **+11.5 % FAIL** | {C3a, C3c, C5a} |
| arm B (0.570) | +4.3 % PASS | +9.1 % PASS | **+11.3 % FAIL** | {C3a, C3c, C5a} |

Identical fail sets; C3b PASS all years and **improves** in 2025 (0.155 →
0.152). Class deltas reproduce caiso-121 to three decimals (CC_REGULAR
−0.2088/+0.0483/+0.0313 TWh). **Third independent measurement that this delta is
inert-to-slightly-favourable.** Not promoted: C3a-2025 fails in the control too
and by *more*, so that failure is the drift and not the delta — but with the
drift unattributed, banking an unexplained regression into the lane's reference
run is an owner call. 0.570 stays **KEPT** and is still the value the next
keeper must carry (rules 13/14/18) — never tuned back toward 0.26.

**(5) Where the next session should cut.** Not another blind solve. Both
`src/market_sim/` and the outage extract are closed. Diff the *constructed LP
inputs* (FleetArrays, CF profiles, fuel series, floors, interchange/hub series)
between HEAD and a pre-drift basis, find the array that moved, then solve once
to confirm. The pre-drift basis must be established by measurement — the
keeper's recorded metadata cannot supply it (item 1).

**Operational notes.** `git push` returned **HTTP 413** on a pack of 5 objects;
the API transport (`push_files`) was used for the text deliverable and
blob-verified byte-identical. The drift-test wrapper deadlocked on a
self-matching `pgrep -f "chain.sh"` — guard against self-match in chained
watchers. CAISO stayed single-solve-only throughout (rule 12 + the caiso-121
note); five LP solves ran strictly sequentially.


## caiso-123 (2026-07-26) — C3a-2025 BASIS DRIFT ATTRIBUTED (derive-first, two probe solves): it IS the CAISO outage extract, in the states caiso-122 never tested — the extract was **derived-not-committed until 07-24**, the keeper solved on a session-local **partial** derivation no full derivation regenerates, and the 07-24 backfill committed a heavier full derivation (CC_REGULAR +618/+688 MW avg removed 2024/25) that every later solve reads; same-HEAD extract A/B isolates **+1.24 % λ / CC_REGULAR −0.49 TWh / import +0.42 TWh**; the caiso-120 "guard-corrected extract" re-tune trigger is **WITHDRAWN-AS-STATED** (guard's own isolated effect −0.18 %, favourable) and re-derived onto the extract-content change; `basis_sha` governance fix landed; keeper UNCHANGED, nothing registered

**Full record: `results/calibration/FINDING-caiso123-c3a-drift-attribution-2026-07-26.md`.**
Instrument (committed): `scripts/probes/_caiso123_extract_repro.py`. Two
single-year throwaway probe solves (rule-16 diagnostic clause, gitignored
`results/probes/`, NOT registered — FINDING-caiso92b protocol): arm K = keeper
recipe at HEAD with the extract pinned to the pre-backfill blob `e40847c`;
arm C = same-HEAD control on the HEAD extract. Capacity-deliverability clean
partition regenerated first and its load verified in both logs (the
RESULTS-neiso65 §2 silent-degrade trap).

**(1) Basis established by measurement, not metadata.** `caiso119_base_A`'s
committed hourlies (keeper recipe, no delta, at f28340b = 2026-07-24) already
carry the full drift (λ-2025 +1.55 %, CC_REGULAR −0.44 TWh, import
+0.41 TWh) — one day after the keeper solved. Config surface clean
(run_config deep-diff), shared-input hashes identical. The only
CAISO-solve-relevant data change in the window: `campd-unit-outages-CAISO.csv`,
**created 07-24** (PR #2842, light partial 4,497 rows, blob `e40847c`) then
**"re-derived in full" on owner instruction** (PR #2844, +642 rows — ALL
2023–25 windows, 504 CC_REGULAR, 1 % overlap = genuinely new detections;
5,139 rows, blob `3dc01fae`), then guard-split 07-26 (4,329 rows).

**(2) The load-bearing discovery.** Before 07-24 the unit-outage extracts
were DERIVED-NOT-COMMITTED — no `campd-unit-outages*.csv` main extract exists
anywhere in the keeper's merged tree (`2895bbe75`), for any ISO. The keeper's
overlay (caiso-122's r=0.99343 refutation stands — it was present) came from
its own container's derivation, whose bytes died with the container. That
derivation was PARTIAL: the keeper-era script re-run on byte-identical raw
reproduces the FULL detection (in-window mass = `3dc01fae` to 0.1 MW), which
the keeper's λ sits +1.60 % away from. The keeper's envelope is
e40847c-class (CC_CHP hourly MAD **2.4 MW** vs arm K, 16.4 MW vs the heavy
arm) — and **no full derivation, old script or new, guard on or off,
regenerates an envelope that light**. The keeper's C3a-2025 PASS rests on a
non-reproducible input state (rule 13 `[R-MEASURED]` reproducibility
failure baked into the committed keeper).

**(3) The ladder and the confirm.** λ-2025 strictly monotone in in-window
derate mass across seven solved states: absent 36.48 < arm K (e40847c)
37.73 (−0.24 % vs keeper, ≈C3a +9.7 pass-class) < **keeper 37.82** < arm C
(HEAD guard) 38.20 (+1.00 %, ≈C3a +11.1 FAIL) < base_A/full 38.41–38.63
(+1.4…+1.6 %). Same-HEAD extract isolation (C − K): **+1.24 % λ,
CC_REGULAR −0.49 TWh, import +0.42 TWh** — the drift's signature, from the
extract content alone.

**(4) TASK-1 SETTLEMENT — the caiso-120 ⇄ caiso-122 contradiction.** Both
sessions measured correctly and attributed wrongly: caiso-120's A0/A1
(+10.0→+11.1 %) compared the keeper's light-partial-envelope bytes against
the committed FULL envelope — the "A0 = keeper by construction" method note
held for the guard *flag*, not the extract *file*, which #2842/#2844 had
replaced two days before the guard landed. caiso-122's −0.18 % correctly
isolated the guard step alone. **The charter-§5 CAISO "RE-TUNE REQUIRED"
trigger is WITHDRAWN AS STATED** (the guard adoption per se moved CAISO
*toward* passing) **and RE-DERIVED**: the keeper's C3a-2025 PASS was
calibrated against a non-reproducible partial envelope; on any honest full
derivation it fails by ~+1.1 pp (rule-11 class: the light envelope was
silently compensating). Charter lane notified (governance.md 2026-07-26
entry; RESULTS-neiso65 §6.2 corrected in place — it cited caiso-122's
refuted first revision). NYISO's re-audit cell is unaffected (#2842/#2844
touched only the CAISO extract). **Do NOT re-tune on the confounded
A0-vs-A1 number.**

**(5) Residual flagged, not chased.** A second, smaller basis motion since
de62eb1 (~−0.2…−0.5 pp λ, CC_REGULAR ≈ −0.8 / import ≈ +0.8 TWh common to
both arms; direction helps C3a, worsens C5a-volumes). Candidates: the
de62eb1..HEAD 16-file src window (miso-91 SUMMER_* re-home verified
value-identical; renewables itertuples refactor MISO/forecast-scoped;
scenarios/bounds/runner diffs nominally other-ISO), earlier sessions'
container/partition state (their arms are uncommitted and gone), vertex
wander. Open, with `basis_sha` anchors now available.

**(6) Rules 1/13/14 guardrail, stated for the record.** Restoring a light
extract to recover the keeper's C3a PASS is forbidden — the light envelope
is an accident of an incomplete derivation, not a derivable state of the
measured input. The honest envelope is the full derivation; its absolute
level is the open over-count question (freeze ACTIVE, neiso-66). Whether
CAISO re-tunes offers against a disputed input or waits on the freeze lane
is an owner/charter sequencing call. Nothing armed this session.

**(7) Governance closure (the reason task 2 was hard).** `basis_sha` —
`merge-base(HEAD, origin/main)`, the newest origin-durable ancestor of the
solving tree — is now stamped fresh at every bundle write
(`run_calibration_full.solve_and_persist` meta + `run_config.git`);
`replay_keeper` ignores it on input (STRICT mapper) and never restores it
(factored `_restore_display_date` rewrites only the timestamp's date
prefix, preserving the dashboard run id). `tests/test_basis_sha_provenance.py`
pins the contract (8/8 pass; the 8 pre-existing HEAD failures in
`test_pipeline_facade_shims`/`test_flag_registry` reproduce at pristine
HEAD and are unrelated). RECOMMENDED next: extend `shared_inputs`
content-hashing to the derived outage extracts so a bundle pins the exact
extract bytes it solved on.

**DO-NOT-REDO (new):** re-solving the extract states (the seven-state
ladder is complete: absent / e40847c / keeper / guard / full, plus the two
de62eb1 arms); recovering the keeper's exact extract bytes (unrecoverable —
derived-not-committed, session-local, bracketed by measurement); any
light-extract restoration as a fix path.

**Open items carried:** min-load 0.570 promotion (owner call, caiso-122
§6); belly delta (family selected caiso-121, ARMING IS AN OWNER ASK,
caiso-120 regime-conditional gates, rule-22 LOYO); the §5 residual; the
charter-lane re-tune-vs-freeze sequencing decision.

Next number: caiso-124.

## caiso-124 (2026-07-26) — HYDRO MIN-FLOW FLOOR lane BUILT (owner-flagged) and A/B'd against gates pre-registered before the solve: the mechanism eliminates the parks-at-zero pathology outright (h<10 MW 270/692/604 → 0), closes 83–91 % of the belly hydro deficit, halves the diurnal MAE and corrects the amplitude error (cv_model/cv_meas 1.44 → 0.98) — and is **KILLED AS WRITTEN by its own K3 shape gate in 2025** (profile r 0.985 → 0.977) plus a P1-2025 miss (172 h < 100 MW vs < 150). Registered as a rejected probe; keeper UNCHANGED. TASK 2: the caiso-123 §5 residual's `src/market_sim/` window is now CLOSED BY MEASUREMENT — only container/partition state and vertex wander survive

**Full record: `results/calibration/FINDING-caiso124-hydro-min-flow-floor-2026-07-26.md`;
gates: `results/calibration/PREREG-caiso124-hydro-min-flow-floor-2026-07-26.md`
(committed BEFORE arm B solved, commit `353d88e`).**
**Runs:** `2026-07-26-caiso-124-hydro-minflow` (arm B) registered — a REJECTED
probe, registered per rule 15. Arm A `caiso124_control_A` (same-HEAD control,
FINDING-caiso92b protocol) NOT registered. Both 3-year (rule 16), one
invocation, sequential, `basis_sha 4094bbe`, seam import cap 16,055 MW
affirmatively logged in both.

**(1) The mechanism.** ONE registered switch `ScenarioConfig.hydro_min_flow_floor`
(default off) adds the **lower half of the measured two-sided hydro capability
envelope** whose upper half — the caiso-72 p95 (month × hod) `hydro_dispatch_envelope`
ceiling — the keeper already carries. The budget family caps monthly *energy*
with no lower bound, so the economic LP parks the fleet at 0 MW: the keeper does
so for **270/692/604 h** and sits under 100 MW for ~0.9–1.3 k h/yr, against a
measured fleet whose hourly p5 is **954/876/738 MW** and which never approaches
zero (run-of-river inflow + FERC-licence minimum releases). Level = the per-month
exceedance percentile of measured EIA-930 `NG: WAT`, `HYDRO_MIN_FLOW_PERCENTILE
= 100 − HYDRO_ENVELOPE_PERCENTILE = 5` — the **exact mirror of the ceiling's**,
so **ZERO new free parameters** (Q95, the standard hydrological low-flow index
licence conditions are written against). Bucket = the **MONTH ALONE**,
deliberately not (month × hod): a diurnal floor pins the measured outcome
(rule 13) and measures out at ~75 % of the annual budget vs 36–46 %
month-constant. Allocated per plant pro-rata by its own share of the month's
budget — exact per-plant feasibility, faithful zonal geography of the water, no
added LP degeneracy. `MECH_HYDRO_MIN_FLOW`, non-thermal, ablated in D-3, D-4
window `h0-23` cited.

**(2) What it fixed, every year.** h<10 MW 270/692/604 → **0**; belly (hod 9–15)
gap **−587/−610/−548 → −98/−54/−84 MW**; hod-profile MAE **366/348/343 →
168/148/169**; diurnal amplitude cv_model/cv_meas **1.44 → 0.98** (2024) and
**1.42 → 1.05** (2025); measured-budget utilisation 98.7/94.5/97.0 % →
**99.2/96.8/99.1 %** (arm A was *declining* up to 5.5 % of the measured water).
D-2 `hydro × hydro_min_flow` forces 5.42/4.92/4.18 TWh = **22.4/22.4/19.8 %** of
class, D-4 off-window share **0.0000**, C7 + C8 PASS.

**(3) Why it is KILLED anyway.** K3 (profile r ≥ control's) tripped in 2025:
**0.985 → 0.977**. Measured cause: with the monthly budget a hard cap the belly
lift must be paid for, and the LP paid partly out of the evening peak — arm A's
2025 evening was already right (+7 MW), so B's peak lands 250–390 MW *below*
measured and its max shifts hod 20 → 21. A 24-point correlation is dominated
jointly by amplitude and peak placement, so **the gate penalised the amplitude
correction it should have rewarded** (r −0.008 against cv_ratio 1.42 → 1.05).
That is a finding about the gate, NOT a licence to ignore it: K3 was written
before the solve, it tripped, the delta is KILLED as scored, and no gate was
moved or re-scored against a substitute. Choosing a corrected shape gate (the
natural pair being the rubric's own D-1 `cv_ratio` + `profile_r`, as C7 scores
them — C7 PASSES in arm B) is an OWNER decision; the bundles support a re-score
with no re-solve via `scripts/probes/_caiso124_minflow_ab.py`.

**(4) Rubric, reported not gated (rule 1).** Arm B: C1/C2/C3b/C4/C7/C8 PASS,
C3a **FAIL on 2025 only (+10.9 %)**, C3c FAIL, C5a FAIL −11.0/−10.2/−13.5 %,
C6 UNATTESTED (a replay carries no attestation). **C3a-2025 is the attributed
extract basis, not the delta** — arm A's own λ reads **+1.035 %** above the
keeper (55.7159/37.8424/38.4156 vs 55.6158/37.5464/38.0221), reproducing
caiso-123's ≈+11.1 % control class; the floor is neither credited nor debited
for it. The floor's own λ effect is **−0.31/−0.85/−0.19 %** (toward the actual).
**C5a moves the wrong way** (−0.3/−0.1/−1.7 pp vs keeper), part of it the
delta's own +0.11/+0.52/+0.46 TWh of zero-carbon hydro displacing gas — reported
as a cost, never as a rejection ground (rule 1). **S3 REFUTED:** removing
0.3 GW from the evening peak creates **zero** h>$200 scarcity hours (0 in both
arms) — the "over-saved evening water suppresses the tail" story does not
survive.

**(5) Disposition.** Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED;
nothing armed; promotion an owner call regardless (PREREG §6) and still behind
the neiso-66 extract over-count freeze and the caiso-123 §6 re-tune-vs-wait
question. The mechanism stays in the tree default-off (byte-identical when off;
11 tests pin the derivation, mirror identity, shape-freedom, allocation,
feasibility, `min_gen` wiring, off-path inertness and the rule-12 window). **The
question the numbers actually pose** is the side-effect, not the level: both arms
are 150–310 MW **too high overnight** (arm A hod 0: 3354 vs 3044 measured, 2025)
— a pre-existing defect the floor cannot touch and the only place the belly lift
could have come from without cutting the peak. A caiso-125 lane should attack the
overnight over-supply (the p95 ceiling does not bind overnight; hydro carries no
water-value term), then re-test the floor on top.

**(6) TASK 2 — the caiso-123 §5 residual: the `src/market_sim/` window is CLOSED
BY MEASUREMENT.** Every one of the 18 files in `de62eb1..HEAD` is now eliminated
by execution or by the keeper's own recorded config, not by inspection:
`lp/bounds.py` ORDC widths evaluate to the identical array on the static branch;
the miso-91 `SUMMER_*` re-home literals verified identical; `_plant_emission_rate_map`
`iterrows`→`itertuples` **measured equal** on both live artifacts (130 / 0 pooled
rows, all four columns int64/float64); `load_plant_tranche_config` **unreached**
(the keeper's `plant_tranche_config_path` is `null`, and no on-disk artifact
carries its schema); `_add_proposed_capacity` — the one renewables hunk on a
nominally ISO-generic wind/solar capacity path, which caiso-123 scoped as
"MISO/forecast" — is **CAISO-unreached by measurement** (`_ISO_HOME_STATES`
contains only ERCOT, so it returns before the loop; executed for CAISO
solar+wind 2025, contribution **0.000 MW-months**), its extraction also measured
identical; `pipeline/solve.py`'s cross-year gate takes the identical env-var
branch at `xyear_warmstart=None` and `replay_keeper` pins the env var to 0 in
every arm; `backcast_config.py` is one ERCOT-only line; `data/cache_control.py`
is read-only diagnostics (`clear_all_caches` never called implicitly). **Only
container/partition state and alternate-optimal vertex wander survive.** Arm A
additionally bounds the newest sub-window: same recipe, `3253345` → `4094bbe`
moves λ-2025 by ≈ **+0.04 pp** (arm C +1.00 % vs arm A +1.035 %, each against
its own formula's keeper) — the residual is NOT accumulating from main's churn.
Recommendation carried: extend `shared_inputs` content-hashing to the derived
outage extracts **and the clean `capacity-deliverability` partition** — the one
solve input a bundle currently records nothing about, and the only surviving
code-external candidate a future session could still close.

**(7) Incidental, NOT this lane's to fix.**
`tests/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`
fails at pristine HEAD on the `availability` + `min_gen` hashes: the golden was
captured at `2f4cbc3` (07-24) and `6a8f285` (neiso-65 guard-corrected CAMPD
extracts) then changed `data/raw/campd-unit-outages.csv`, which sets ERCOT
availability — and `min_gen`, clipped to `pmax × availability`. Needs
re-capturing under that owner-authorized data change, by whoever owns it (never
to silence a gate). Also pre-existing:
`test_hydro.py::TestCAISOHydroBudget::test_zones_resolve_to_caiso_topology`
(asserts CAISO hydro zones ⊆ {NP15, ZP26, SP15}; the topology now carries
LA_BASIN/SDGE/SP15_rest), plus the 8 known `test_pipeline_facade_shims` /
`test_flag_registry` failures. Latent hazard noticed, untouched:
`src/market_sim/data/fleet/__init__.py` defines `Generator` **and**
`FleetArrays` **twice** (157/254 and 496/591, differing only in blank lines);
the later win at runtime and the new field was added to both, but the
duplication is exactly the class of file damage rule 27 exists for.

**DO-NOT-REDO (new):** re-deriving the min-flow level (frozen, rule 21 — the
percentile is the ceiling's mirror; re-derive only when the EIA-930 source
extends); re-running the (month × hod) floor variant (measured at ~75 % of the
annual budget = a measured-outcome pin, rule 13); re-scoring caiso-124 against a
substitute shape gate without owner authorization; re-eliminating any
`de62eb1..HEAD` src candidate in item (6).

**Open items carried:** min-load 0.570 promotion (owner call, caiso-122 §6); the
belly delta family (export-path/corridor, selected caiso-121, ARMING IS AN OWNER
ASK); the caiso-124 shape-gate disposition (item 3); the overnight over-supply
lane (item 5); the charter-lane re-tune-vs-freeze sequencing decision.

Next number: caiso-125.
## 2026-07-26 — CAMPD charter LANE B (cross-ISO, **no CAISO lane number claimed**): the day-grain `R < 0` cut does not replace the guard's window-grain cut

Charter/cross-ISO session — measurement only: no guard change, no extract
re-derive, no LP solve, **no CAISO keeper touched**, no dashboard registration.
Full record: `results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md`;
cross-ISO entry in `docs/calibration-log/governance.md`.

CAISO's cell of the 180-cell sweep (`--rcc-pctl {0.50, 0.75, 0.90, 0.99}` × `--horizon {24, 48, 72}` ×
2023–2025), scored against CNOG on the reviewed resource→plant crosswalk, **revision-aware build only** (neiso-66 §1 — `tail(1)` and raw-sum are both wrong):

* **KEPT-extract monthly `r` at the default p90 / h24**, window-grain → day-grain:
  2023 **+0.78 → +0.78** (Δ −0.001), 2024 **+0.77 → +0.77** (Δ +0.003), 2025
  **+0.85 → +0.85** (Δ +0.005). Over CAISO's 36 cells the day cut is better in
  **19/36**, median Δ **+0.000** — a coin flip at zero effect size.
* **Neither cut clears the placebo on CAISO** (6/36 cells each): at p90/h24 the
  kept-`r` sits below the proportion-matched p95 in all three years
  (+0.78 vs +0.81, +0.77 vs +0.81, +0.85 vs +0.85). That is a property of the
  CAISO instrument/scope, unchanged by the grain of the cut, and it is the same
  reading the charter already carries.
* **The two cuts pick the same windows**: Jaccard 0.77 / 0.91 / 0.86, with the
  candidate a strict **subset** of the incumbent in all three years (day-only
  vetoes 0 / 0 / 0).
* **Control passed**: the re-implemented incumbent reproduces CAISO's committed
  kept/layup split on 529/530, 531/533, 626/628 windows on the crosswalked
  active-plant scope (34 plants, published mean 2,963 MW — consistent with
  neiso-66 §1's revision-aware 2,925 MW).

**Nothing in CAISO changes.** The merit-order guard stands as the charter §8
verdict adopted it, CAISO's committed extract and layup companion are
untouched, and no rule-22 obligation arises because no mechanism change is
proposed. Open CAISO items (min-load 0.570, the belly delta, the charter-lane
re-tune-vs-freeze sequencing) are untouched. Next number unchanged: **caiso-125**.

## caiso-125 (2026-07-26) — OVERNIGHT HYDRO OVER-SUPPLY attributed by measurement, charter premise INVERTED (the p95 ceiling BINDS overnight, 83–85 % of hours — the overnight level IS the envelope level); every chartered lever REFUTED derive-first; the honest driver = fleet SHAPEABILITY HETEROGENEITY (RoR split — greedy proxy fixes overnight AND belly AND evening at once, ARMING IS AN OWNER ASK) + the evening–overnight spread compression; diagnostic probe: the overnight excess displaces GAS (C5a-aligned); keeper UNCHANGED, nothing armed, nothing registered. Plus: derived solve inputs (outage extracts + capacity-deliverability partition) now content-pinned into shared_inputs (caiso-123 §5 closed)

**Full record:
`results/calibration/FINDING-caiso125-overnight-hydro-attribution-2026-07-26.md`.
Instruments (committed): `scripts/probes/_caiso125_overnight_attribution.py`
(sections A–I on the two committed caiso-124 bundles + raw EIA-930/923 — no
solve), `scripts/probes/_caiso125_nightcap_probe.py` (rule-16 diagnostic
runner + pair analyzer). Keeper `2026-07-23-caiso-netrev-margin-keeper`
UNCHANGED; charter Task 2 (re-score caiso-124's shape gate) NOT executed — no
owner authorization exists, so caiso-124 stays KILLED as scored.**

**(1) Premise inversion.** caiso-124 §5 carried "the p95 ceiling does not bind
overnight". Measured on `caiso124_control_A`: overnight bind share
**0.830/0.824/0.849** (highest of any window with `late`), 0 hours above cap in
26,280, model mean percentile-rank **0.80–0.82** inside the measured
(month × hod) bucket distribution. The LP rides any overnight cap it is given
(overnight λ 40–58 $ > the month's marginal water value in ~83 % of overnight
hours); under bang-bang budget dispatch the envelope percentile IS the dispatch
level in every ridden window. The measured overnight distribution is
water-year-invariant (mean 2758–2810 / p95 3334–3382 MW across 24.4→21.3 TWh),
so no admissible re-derivation narrows it (rule 21).

**(2) Refutations, all by measurement or structure, no solve spent on any.**
(ii) water-value adder: budget BOUND 7/5/8 of 12 months (allocation-inert
there — the objective shifts by c×E); slack months are the negative-λ spring
where an adder declines belly water first — it cannot touch overnight before
emptying the belly (λ ordering: overnight 40–58 vs belly 22–40). Weekly budget
grain: greedy proxy (validated on arm A to 29–61 MW) moves overnight only
−20…−41 MW — scarcity is paid from the belly, overnight stays cap-pinned
(nightly tracking r 0.69–0.78 → 0.78–0.82 is its real, different, effect).
(iii) import/storage displacement: overnight the model also over-imports
+0.7–1.3 GW and its storage nets +148/+165/+421 MW *discharging* where the
real stack pumps/charges — co-symptoms; the hydro component itself is
cap-pinned (an input property, not displacement). PS boundary pollution of
`NG: WAT` (EIA-923 CISO PS net −529/−139/+102 GWh): monthly regression slope
−1.31/−2.51/+0.09, r −0.48/−0.44/+0.06 — modulates the 2023–24 pump months,
but the intercept **+215/+233/+307 MW** persists at zero PS activity; the LP's
envelope row is already like-for-like (hydro + PS net ≤ cap), and no on-disk
or cleanly-fetchable source resolves the PS hod shape.

**(3) The two real drivers.** (a) **Spread compression** (the caiso-103→108
evening λ lane): model evening−overnight spread +9.0/+5.0/+2.8 $/MWh vs
implied real ≈ +15.6/+9.9/+5.3 — water and battery discharge prefer overnight
at half the real premium; this is why arm B paid the belly floor from the
evening (the K3 kill). Not fixable hydro-side (rule 1). (b) **Shapeability
heterogeneity**: all 160–171 model hydro units shape freely (degenerate water
values, the fleet moves as one bang-bang block); reality is ~half
run-of-river/canal. Greedy RoR-split proxy (CF ≥ 0.45): overnight
3099/3061/3066 → 2596/2502/2590 (bias-corrected ≈ 2750–2950 ≈ measured
2758–2815), belly 1306/926/744 → **1877/1302/1156** (measured 1893/1536/1292 —
near-measured with NO floor), evening ≈ measured. One structure, all three
windows. **NOT armable in-repo:** ORNL EHA 2024 `Mode` is NaN on 100/201 CISO
plants (4.66 of ~6.7 GW, all the large reservoirs) and a CF threshold is a
free parameter (rule 24/13); rule 19 requires reconciling with the min-flow
floor (same driver — the floor's Q95 is the fleet-aggregate shadow of the RoR
base, 35.7–46.3 % vs the split's 42.7–60.7 % of budget). **Owner ask:
per-plant operational-mode intake + floor-reconciled RoR-split design, LOYO
per rule 22.** The caiso-124 floor was NOT re-tested on top — with no
overnight delta armed that would be a caiso-124 redo; its re-test belongs
inside the reconciled RoR family.

**(4) Diagnostic probe (rule-16 single-year 2025 pair, gitignored, never
registered; clamp = overnight hod0-6 envelope p95 → bucket mean, an
explicitly-labelled rule-13 outcome pin for attribution only).** Fresh HEAD
control reproduces the committed `caiso124_control_A` 2025 **digit-for-digit**
(hydro 20.68 TWh / overnight 3066 / λ 36.5750) — the `4094bbe..HEAD` window is
CAISO-inert, no basis caveat. Clamped − control: overnight hydro **−422 MW**,
filled by **gas +254** (60 %), import +116, storage +53; the freed water
spreads near-uniformly (morning +181 / belly +121 / shoulder +125 / evening
+129 — §3a's indifference, confirmed); annual gas **+0.322 TWh** (the C5a
direction), CA λ −0.49 % (toward actual), overnight λ +0.41 $. An honest
overnight fix is C5a-, C3a- and shape-aligned at once — the rubric case for
the §3b owner ask.

**(5) Task 3 delivered — derived-input provenance closed.** Bundles now pin
the per-ISO CAMPD unit-outage extract family AND the clean
`capacity-deliverability` partition into the content-addressed `shared_inputs`
store at solve time (`scripts/lib/bundle_io.write_derived_solve_inputs`,
wired in `run_calibration_full.solve_and_persist`; replay ignores the block —
`_IGNORE` — so the STRICT mapper is untouched; 2 new tests in
`tests/test_bundle_io.py`, 12/12 pass). Closes the caiso-123 §5 / caiso-124
§7 recommendation: of the residual's surviving candidates only
alternate-optimal vertex wander now lacks a pin. Recommended (not built,
parallel-lane blast radius): a per-tech storage hourly sidecar so instruments
can score the like-for-like `hydro + PS net` aggregate the LP constrains.

**DO-NOT-REDO (new):** re-measuring the overnight bind share/percentile-rank
(instrument committed); any hydro discharge water-value adder, constant or
budget-scoped; the weekly/finer hydro budget grain as an overnight lever; the
envelope/floor percentile re-derivation against this residual; a CF-threshold
RoR split without the external classifier intake; re-solving the nightcap
clamp (attribution complete — it is an outcome pin, never a mechanism).

**Open items carried:** min-load 0.570 promotion (owner call); the belly delta
family (export-path/corridor, caiso-121); the caiso-124 shape-gate disposition
(owner); the RoR-split owner ask (this session, item 3b); the charter-lane
re-tune-vs-freeze sequencing decision.

Next number: caiso-126.

## caiso-126 (2026-07-27) — RoR-SPLIT LANE EXECUTED (the caiso-125 §4c owner ask): external classifier intaken (EHA+HILARRI, energy-weighted RoR share is ~10-12 %, NOT the premise's ~half — that was plant-count), the floor-reconciled family BUILT (zero DOF, default off, byte-inert proven digit-for-digit) and A/B'd against gates pre-registered before the solve: every window moves toward measured — overnight 2-3× beyond the fixed-λ prediction (the reservoir-pool water-value feedback is REAL), belly −583/−611/−549 → −92/−58/−83 MW, parks-at-zero → 0, amplitude error −80…−87 % — and the family is KILLED as armed by pre-registered K1 EVENING STARVATION (2024 −376 MW; the caiso-125 §4b spread compression paying the belly from the evening peak) + the formal K4 nameplate-clip clause. Keeper UNCHANGED; B registered as a rejected probe

**Full record: `results/calibration/FINDING-caiso126-ror-split-2026-07-27.md`;
gates: `results/calibration/PREREG-caiso126-ror-split-2026-07-27.md` (committed
`08d8113`, BEFORE arm B solved). Runs: `2026-07-27-caiso-126-ror-split` (arm B,
PROBE/REJECTED, rule 15; retention pruned caiso-97-evening-trim). Arm A
`caiso126_control_A` NOT registered (FINDING-caiso92b protocol) — it reproduces
the committed `caiso124_control_A` DIGIT-FOR-DIGIT (max hourly hydro delta
0.000 MW), proving the new default-off code byte-inert on the keeper recipe.**

**(1) Task 1 — classifier intake.** New `hydro-plant-modes` clean datatype
(schema-first, `scripts/data/curate_hydro_plant_modes.py`): ORNL EHA FY2024
`Mode` (raw committed under `data/raw/ornl-eha/`) completed for the 100
Mode-NaN CISO plants by categorical HILARRI v4 (`data/raw/hilarri/`)
reservoir-association / canal-type / Corps-dam-ownership rules — NO numeric
threshold (rule 13/24), frozen against residuals (rule 21), validated
residual-blind at 86/97 plants / 84.7 % of labeled MW. FC_Dock propagation
measured useless (0/100); EHA FY2023 carries the identical gap. CISO: 195
plants, 84 RoR-class — but **energy-weighted only 12.5/11.1/10.3 % of the
budget**: the caiso-125 "~half run-of-river" premise was plant-COUNT; the CF ≥
0.45 proxy's 43-61 % had mostly flat-lined high-CF SHAPEABLE plants (wet-year
headroom, which the LP already represents per-plant).

**(2) Task 2 — the mechanism** (`hydro_ror_split`, default off, cache-key
neutral): RoR-class plants fixed at their own monthly water
budget[g,m]/hours[m] (min_gen == availability cap, `MECH_HYDRO_ROR_FLAT`,
non-thermal, D-4 h0-23); rule-19 reconciliation makes it ONE family with the
caiso-124 floor — the reservoir class carries exactly (Q95 − RoR base)+, total
forced base = the frozen Q95, never stacked, no RoR unit carries both stamps
(test-pinned; 7 mechanism + 4 intake tests). Bundles now pin the classifier
partition into `shared_inputs`.

**(3) Task 3 — the A/B** (PREREG-caiso124 format, same-HEAD arms, chained).
B − A: overnight gap +311/+249/+308 → **+160/+92/+211** (P1 PASS 2024 only —
but improved every year, 1.2-3× the fixed-λ greedy prediction recorded in
PREREG §3: the split raises the reservoir pool's marginal water value into the
overnight λ band, the channel caiso-125 §1-§3 proved no within-envelope lever
reaches); belly → **−92/−58/−83** (P2 PASS); D-1 PAIR gate (profile_r ≥ 0.8 +
amplitude, the corrected caiso-124 form) PASS all years incl. 2025 where raw r
dips 0.985 → 0.977 — the trap the pair gate was built for; parks-at-zero
270/692/604 → **0**; gas **+0.35/+0.36/+0.18 TWh** and λ
**−0.50/−1.24/−0.22 %** (both toward actual — S1 confirms the caiso-125 §5
probe's direction, at ~5 % of the C5a deficit: the overnight excess was a live
but MINOR C5a contributor; import/gas substitution remains the main line).
**KILLED as armed**: **K1** evening starvation (B −251/**−376**/−264 vs A
+126/−114/+5; 2024 breaches ±300) — the forced base holds belly+overnight near
reality and the LP pays for it out of the evening peak because its
evening−overnight premium is compressed ~2× (caiso-125 §4b); same channel as
caiso-124's K3, now caught by an explicit window kill. NOT fixable hydro-side
(rule 1/13). **K4** (formal): nameplate-clip 1.335/1.269 % > 1 % — fired
pre-solve; the control shares the identical under-delivery (EIA-930 uniform
scale factor inflating small-plant budgets past nameplate-hours); gate stands
as scored per the caiso-124 discipline, fix = ISO-generic budget-scaling lane.
D-4 off-window 0.0000 both mechanisms; C8 PASS; rubric (reported): NOT-YET,
fail {C3a-2025 (attributed extract basis; the family's own λ is
toward-actual), C3c, C5a}. LOYO (rule 22): zero fitted parameters ⇒ per-year
consistency is the record — improvements hold in every year independently;
the evening degradation is same-signed in all three (systematic, not
single-year).

**(4) Disposition.** Keeper UNCHANGED; mechanism + classifier stay in-tree
default-off as the structurally-correct hydro representation awaiting its
prerequisite; **the caiso-124 floor's re-test is COMPLETE inside this family**
(belly fix survives reconciliation; its evening payment is attributed to the
spread compression, not the floor's level). **Priority follow-up: the evening
λ-formation lane (caiso-103→108 hub-separation/spread) — it now blocks the
ENTIRE hydro family; once landed, this family re-tests with one flag.** Minor:
the K4 budget-scaling data fix; the 4 pondage-peaker classifier FNs (~2 % of
budget, rule-21 frozen until a new vintage).

**DO-NOT-REDO (new):** CF/residual-derived RoR classification (the intake
replaces it); re-running this A/B at the current spread compression; moving
K1/P1 bounds post-hoc; a hydro-side evening floor to offset the starvation
(rule-13 pin); re-measuring the clip loss.

**Open items carried:** min-load 0.570 promotion (owner); the belly delta
family (export-path/corridor, caiso-121); the caiso-124 shape-gate disposition
(owner; note the pair-gate form is now field-tested here); the charter-lane
re-tune-vs-freeze sequencing decision; the evening λ-formation re-charter
(now this lane's blocker).

**(5) ADDENDUM — OWNER PROMOTION (same session, later).** The owner authorized
promotion on the "performs better or is more structurally sound" criterion;
measured before acting: the evening starvation is **λ-neutral** (evening λ
+0.09/−0.01/+0.05 — the import rung sets the evening price, so K1 is a
volume-shape cost of removing the unphysical compensator, rule 14's exact
case), and the prior keeper's C3a-2025 PASS is the caiso-123 NON-reproducible
partial-extract artifact (its honest same-HEAD control also reads ≈+11 %).
**Keeper → `2026-07-27-caiso-126-ror-split`** (rule 1: most structurally
faithful, kills recorded not erased; attestation written with the zero-DOF
ledger carry, C6 attested; exceptions ledger deliberately EMPTY — C3a-2025
stays an honest FAIL while the neiso-66 freeze holds). Status: NOT-YET, fail
{C3a-2025, C3c, C5a}; `audit_keepers --iso CAISO` PASS. The as-armed prereg
verdict stands as scored (FINDING §8). The caiso-127 evening λ-formation lane
now fixes the spread compression ON TOP of the honest hydro base.

Next number: caiso-127.

## caiso-127 (2026-07-27) — the evening premium is not primarily UNDER-PRICED, it is ARBITRAGED FLAT: the model's own storage is interior-discharging in BOTH windows on 53/54/76 % of days and LP optimality pins the two λ equal (measured gap +2.64/+0.36/+0.41 vs a no-arbitrage prediction of 0.00); the charter's nominated candidate is refuted as a FIRST delta by that construction; owner ask filed, keeper UNCHANGED

**Measurement-only session** (the prompt's owner gate: instruments / rule-16
diagnostic probes at most). Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED;
no mechanism armed, no A/B, nothing registered. **TASK 3 was not executable** —
it is conditional on an in-session owner grant on a specific construction and
no such grant exists in this session; the ask is filed instead.

Instrument (committed): `scripts/probes/_caiso127_evening_formation.py`
(sections A–E + B2). Full record:
`results/calibration/FINDING-caiso127-evening-formation-2026-07-27.md`.
Owner ask: `docs/handoffs/caiso-127-storage-arbitrage-ask-2026-07-27.md`.

### §A — the ladder re-based on the promoted keeper, and the framing that breaks

| year | overnight resid | evening resid | spread model | spread actual | compression |
|---|---|---|---|---|---|
| 2023 | −0.09 | **−5.16** | +8.90 | +13.97 | +5.07 (64 % of measured) |
| 2024 | +1.73 | −2.35 | +4.85 | +8.93 | +4.08 (54 %) |
| 2025 | **+2.81** | +0.41 | +2.76 | +5.17 | +2.40 (53 %) |

The compression reproduces, but "the evening is under-priced" is **2023's story
only**: by 2025 the evening LEVEL is right (+0.41) and the whole compression is
an OVERNIGHT OVER-price. The lane's target is the **spread**, not the evening
level — a candidate scoped to lift the evening alone cannot fix 2025 and would
break its already-correct level.

### §B — the load-bearing finding: the spread is a fixed point of the storage arbitrage

The keeper's storage is neither power- nor energy-bound: 54–56 % of the caiso-99
evening discharge cap, at that cap in only 5.7/7.7/15.0 % of evening hours,
0.36–0.50 cycles/day — and the **overnight is a DISCHARGE window** (net
+157/+188/+453 MW, discharging in 30/31/43 % of overnight hours). So the
operative bound is not the round-trip wedge (+15.17/+12.13/+12.56 at the
model's own overnight levels) but the degenerate discharge-to-discharge **zero**
wedge: a fleet interior in discharge in two windows of one SOC episode carries a
common marginal water value, so λ_evening − λ_overnight = 0 by optimality.

Measured (day-paired, strict interiority both windows): pinned on **192/197/276
of 365 days**, gap **+2.64 / +0.36 / +0.41 $/MWh**. The stratification is the
whole compression:

| year | pinned days (model/actual spread) | NOT-pinned days |
|---|---|---|
| 2023 | +7.36 / +13.66 | +10.60 / +14.32 |
| 2024 | +2.30 / +4.92 | +7.85 / +13.63 |
| 2025 | +1.69 / +4.87 | **+6.11 / +6.09** |

**On 2025's 89 non-pinned days the model reproduces the measured spread
essentially exactly.** Dose–response across the build-out: pinned share
0.53→0.54→0.76 as the fleet goes 7.6→11.4→15.2 GW, model spread
+8.90→+4.85→+2.76.

**Consequence, and the reason this reorders the lane.** Steepening the evening
supply rung raises λ_evening; the unbound storage shifts discharge out of the
overnight and the two λ re-equalize at a HIGHER COMMON LEVEL. The spread does
not open and the overnight over-price worsens — i.e. **the caiso-113/114 C3a
failure is a predictable property of any evening-scoped supply-side candidate,
not bad luck.** The charter's nominated leading candidate (a caiso-114
refinement) is therefore **not the first delta**; it stays admissible only
behind the storage pin.

### §B2 (gate D0) — battery vs pumped storage

The KKT argument is technology-blind, but which technology is interior decides
which mechanism family is admissible: the caiso-99 anchor binds batteries only,
so the LP's 2,078 MW / 20,776 MWh of pumped storage is its one unrestrained
arbitrageur. The committed slim bundle could not separate them
(FINDING-caiso125 §6.4); this session added the per-tech sidecar and replayed
the keeper to produce it — the replay reproduces the committed bundle
**digit-for-digit** (class max |Δ| 0.000 MW / 122,640 rows; zonal price max
|Δ| 0.0000 $/MWh / 61,320 rows, every year), so the sidecars are the keeper's
own and are committed into its `hourly/`.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **pinned days — li_ion** | **0.384** | **0.479** | **0.668** |
| pinned-day gap — li_ion | +2.45 | +1.62 | +1.27 $/MWh |
| pinned days — pumped storage | 0.074 | 0.132 | 0.077 |
| pinned-day gap — pumped storage | +5.71 | +0.48 | −5.18 $/MWh |
| overnight net — li_ion / PS | +98 / +58 MW | +104 / +85 | +365 / +89 |

**The BATTERY fleet carries the pin; pumped storage does not** — the battery
share rises with the build-out on a gap tightening toward zero, PS's has no
trend and does not converge, and PS discharges overnight in 5–8 % of hours vs
the battery's 28–41 %. The ask is aimed at the right resource. Live caveat, not
a blocker: PS carries no shape restraint of any kind in the model and
contributes +58/+85/+89 MW of the overnight excess — a smaller, separate lane.

On the clean battery-only basis the throughput comparison **inverts** the
aggregate reading: model li_ion discharge 4.06/7.62/11.46 TWh vs the measured
LESR RTD 5.67/10.04/12.06 — the LP **under**-cycles the battery by 28/24/5 %
while over-discharging the overnight by +151/+99/+98 MW. Both at once is the
diagnosis: **too little energy moved overall, too much of it placed overnight.**
The defect is the POSITION, not the volume — which is why every volume-priced
instrument (the caiso-100/101 adder, a cycle cap) is aimed at the wrong
quantity.

### §C/§D/§E — the supply side, measured anyway

The evening marginal rung is a **CC_REGULAR / import tie on a near-continuous
stack**: an offer brackets λ in 96–97 % of evening hours, and the next rung
above λ is a median **+0.59 $/MWh** away. The overnight is set by the *same two
classes* — there is no distinct evening rung, which is the structural reason the
two windows equalize so easily. To lift λ by the year's compression delta the
(λ, λ+δ] band holds 1856/1444/867 MW/h of free capacity that must be called or
re-priced through (45/33/19 % of the model's own evening import). Against CEMS,
the evening gas VOLUME is close (+399/+451/+561 MW) but the COMPOSITION is not:
the model over-runs CC_REGULAR (+578/+572/+431) and under-runs CT_PEAKER
(−561/−714/−241), and reality reaches/exceeds the model's own cheapest-available
CT offer 1.3–1.6× as often (0.442/0.204/0.131 vs 0.334/0.130/0.084). Real, but
second-order for THIS lane — on the pinned days it changes the spread by ~0 by
construction — and it belongs to the C5a/C1 composition lane (rule 1: offer
level LAST).

### §Ask (TASK 2) — filed, not built

`docs/handoffs/caiso-127-storage-arbitrage-ask-2026-07-27.md`. Surviving
candidate: the **DA/RT allocation on the DISCHARGE side** — the two-sided
rule-19 reconciliation of M1 (`caiso_charge_allocation_schedule`), same source,
same Fourier-Motzkin per-day construction, volume left endogenous, zero new free
parameters. Closed in the memo, so the ask is not a redo: the **entire AS-award
family** (caiso-74's power-derate and SOC-sustain legs, plus the reg-down form
newly refuted here by arithmetic on the curated award series — overnight upward
award 334–713 MW against 2.1–3.1 GW of remaining headroom), a positive
`battery_dispatch_adder` (caiso-100/101, rejected on the throughput guard), a
cycle-count cap (slack at 0.36–0.50 cycles/day), and re-deriving the caiso-99
envelope (rule 21, and useless — the model uses 5–11 % of the overnight cap).
Derive-first gates D0–D4 and the pre-registered A/B kills (C3a guard;
two-sided ±15 % throughput; D-4) are in memo §5/§6. **PRIMARY of the eventual
A/B is the charter's own test**: the keeper's disclosed evening hydro
starvation (−251/−376/−264 MW) heals to within ±150 MW with NO hydro-side
change.

### Infrastructure landed (write-only / default-off, keeper unaffected)

- **`hourly/storage_<year>.parquet`** — the per-tech storage sidecar
  FINDING-caiso125 §6.4 recommended (`year, pass, tech, hour, charge_mw,
  discharge_mw`); write-only and solve-invariant. Without it a slim bundle
  cannot separate battery from pumped storage, which is exactly gate D0.
- **SECONDARY — `hydro_budget_nameplate_aware`** (ScenarioConfig, default off):
  the FINDING-caiso126 K4 root cause. `load_hydro_budget` applies the monthly
  LEVEL target with a UNIFORM fleet-wide scale, which pushes small plants above
  nameplate-hours; the LP cannot deliver that energy and silently clips it.
  Measured on the keeper's own inputs (no solve): **130 / 341 / 26 GWh =
  0.533 / 1.502 / 0.123 %** of the CAISO fleet budget undeliverable in
  2023/24/25, over 67/42/26 plant-months. The gate water-fills instead — each
  plant-month capped at its physical ceiling, the excess re-allocated to the
  plants that can deliver it, iterating to convergence, month total met exactly
  wherever attainable and the shortfall LOGGED where it is not.
  Byte-identical below the bound (unit-tested); ISO-generic (the defect is in
  the shared level-pinning path). **Built, tested, NOT armed** — it is not
  byte-identical on CAISO, so arming it is an owner grant plus its own A/B.

### DO-NOT-REDO (new)

Re-measuring the ladder/spread/compression on this keeper; re-measuring storage
interiority, the hod profile or the pinned/non-pinned stratification; proposing
an evening-scoped supply-side repricing as a STAND-ALONE first delta (refuted by
construction on the pinned days); any hydro-side or offer-curve adder tuned to
the spread residual (the spread is a fixed point the LP re-equalizes);
re-deriving or loosening the caiso-99 p95 discharge envelope against this
residual (rule 21, and slack by 89–95 % where the defect lives); re-testing any
AS-award form against this defect (§Ask).

Next number: caiso-128.

### ADDENDUM (same session, later) — OWNER GRANT on the caiso-127 ask

The owner granted the §Ask in-session. Terms, recorded verbatim in
`docs/handoffs/caiso-127-storage-arbitrage-ask-2026-07-27.md` §Status:

1. **S1 (DA/RT allocation on the DISCHARGE side) GRANTED** as the next single
   delta, conditional on derive gates D1–D3. **D3 is a hard kill-before-solve**
   — an ex-ante-slack floor kills the family with no LP solved (the caiso-74
   lesson).
2. **The caiso-114 refinement is NOT funded** as a first delta; re-judged after
   S1 lands, against the non-pinned-day residual.
3. **`hydro_budget_nameplate_aware` arms in its OWN single-delta A/B** — never
   bundled with S1; cross-ISO blast radius checked before any keeper.
4. **Pumped storage flagged, not built** (no shape restraint of any kind,
   +58/+85/+89 MW of the overnight excess) — report only.

Promotion is NOT granted and stays a separate owner act after rule-22 LOYO.
Keeper remains `2026-07-27-caiso-126-ror-split`. Next number: caiso-128.

---

## caiso-128 (2026-07-27) — the CT offer-accuracy lane: **lead REFUTED**, the CT heat rate is right; the real defect is CHP

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. Derive/measurement session
— no mechanism armed, no A/B, nothing registered.** Full evidence:
`results/calibration/FINDING-caiso128-heat-rate-provenance-2026-07-27.md`.
Instrument (committed): `scripts/probes/_caiso128_heat_rate_source_audit.py`.

### The lead, and why it does not survive measurement

The owner lead was that the CT classes' offer heat rates are 27–54 % above their
own measured CEMS rates, with the `HEAT_RATE_BINS` fuel × vintage fallback the
suspect. Both halves are refuted:

* **Provenance.** EIA-860 carries no heat rate at all;
  `process_eia860._join_egrid_heat_rate` fills it from eGRID PLNT23 `PLHTRT`.
  **89 % of CAISO CT_PEAKER capacity carries a real eGRID rate** — the bin
  fallback is an 11 %-of-MW tail. (The lead's reading of
  `_egrid_boundary_hr_repairs` as CC-scoped is correct, but nothing turns on it.)
* **The gap decomposes into two non-defects.** ~1.147× of it is
  `caiso_offer_curve_measured.json`'s `CT_PEAKER.econ_low` — the cap-weighted
  median of the fleet's own **OASIS DAM bids** (real conduct, reproduces
  "Sentinel 11.00 → 11.28" exactly). The rest is a **net-vs-gross basis
  artifact**: eGRID `PLHTRT` is heat per **NET** MWh and the LP dispatches net
  MW, while CEMS reports **gross** load.

### The corrected measurement (NET basis) — CT_PEAKER is accurate everywhere

Model offer base rate vs CEMS annual rate on the model's own net basis, 2024,
cap-weighted:

| | CAISO | ERCOT | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| **CT_PEAKER** | **0 %** | −3 % | −0 % | 0 % | +1 % | +1 % |
| CC_REGULAR | −2 % | −4 % | −2 % | −3 % | −2 % | −16 % |
| COAL | — | +1 % | +1 % | −1 % | — | — |
| ST_GAS | **+15 %** | +1 % | +6 % | +2 % | +7 % | — |
| **CC_CHP** | −13 % | **−38 %** | −19 % | **−33 %** | −22 % | **−35 %** |
| **CT_CHP** | **+40 %** | **−62 %** | −12 % | −33 % | −30 % | — |
| **ST_CHP** | — | — | **−56 %** | −41 % | — | — |

Against the *loading-conditional* net rate CT_PEAKER reads **−2 to −11 %**, i.e.
if anything slightly too **cheap**. The gross→net ratio is measured same-year per
plant and validated by two independent derivations agreeing to three decimals
(CAISO CT_PEAKER 2023: 1.193 generation-based vs 1.195 heat-rate-based), which
also proves eGRID's heat input is CEMS's — no boundary mismatch inflates it.

### Why the registered PRIMARY was unreachable anyway

1. **The CT offer is bid-pinned.** `mult` was derived as
   `bid / (base_HR_class × gas)`, so the product round-trips the measured bid by
   construction; re-basing without re-deriving would offer **below** a measured
   bid (a rule-13 regression), and re-basing with the re-derive is offer-neutral.
2. **The within-class CF tilt is flat** — Spearman rank corr(CF, error) = +0.026.
3. **A per-plant measured bid is impossible** — the OASIS ids are masked
   (`derive_caiso_offer_surface.py`: *"the charter's 'plant?' resolves to NO"*).

CT under-dispatch is therefore a **λ-side / rung-continuum** question, already
owned by FINDING-caiso127 §4 and gated behind the storage pin (§2 there).

### What survives: CHP, filed as a design (§6), NOT built

`chp._correct_chp_steam_credit_hr` uses hand factors (`CAISO_EOR_TOPPING_FACTOR`
1.8 for CT_CHP, 1.15 for CC_CHP) and only for `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`
(CAISO, PJM). A universal factor is wrong in both directions at once — it
over-corrects where armed (+40 %) and is absent where not (−12 to −62 %). Each
plant's CEMS `heatInput / grossLoad` **is** its power-only rate, so the
measurement is on disk (rule 14). Design filed in §6: one ISO-generic gate,
CHP-scoped, gross→net reconciled, zero fitted parameters, the `emission_rates.py`
forward story, default off. **Not built** — CAISO CT_CHP is only **17 %**
CEMS-covered, and widening beyond CHP would trigger the paired
`caiso_offer_curve_measured.json` re-derive, which needs an owner call.

Coverage/stability of the candidate input (CAISO): ST_GAS 100 %, CC_REGULAR 84 %,
CT_PEAKER 79 %, CC_CHP 51 %, **CT_CHP 17 %**; cross-year `r` 0.90–0.999 and
median per-plant CV **0.9 %** — a stable physical property, forward-derivable.

### DO-NOT-REDO (new)

Re-testing the bin fallback as the CT cause; **comparing a model/eGRID heat rate
to a CEMS gross-basis rate without the gross→net reconciliation** (this is the
trap that produced the headline); treating the 1.147/1.182 tranche lift as a
modelling error; re-measuring the provenance chain, the cross-ISO net-basis
table, coverage/stability, the CF tilt or the gross→net ratios; proposing a
per-plant measured DAM bid for CAISO; re-basing `base_HR` for CT_PEAKER or
CC_REGULAR without re-deriving the bid multipliers; pre-registering any
heat-rate change against `CT_PEAKER energy → 3.30 TWh` or against C5a; treating
CT under-dispatch as an offer-level defect.

The owner-granted **S1** (DA/RT allocation on the discharge side) is untouched
and remains the funded next delta; the recommended order's item (a) is now
closed as refuted, so S1 moves to the front.

Next number: caiso-129.

---

## caiso-129 (2026-07-27) — S1 (DA/RT allocation, DISCHARGE side): **KILLED AT THE DERIVE GATES**, no LP solved

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. NO SOLVE, no mechanism
built, nothing registered.** This is the owner grant executing as written: D3
was granted as a **hard kill-before-solve** gate and it fired (the caiso-74
lesson held — the arithmetic refuted the mechanism before any LP was built).
Full evidence:
`results/calibration/FINDING-caiso129-s1-discharge-allocation-gates-2026-07-27.md`.
Instrument (committed): `scripts/probes/_caiso129_s1_gates.py`. The live
rule-23 derive `scripts/data/derive_caiso_charge_allocation.py` is UNTOUCHED
and no artifact was regenerated.

### D1 — the statistic exists (PASS)

Discharge side of the same LESR `EN` rows, sign flipped: `da_frac_dis`
0.7957 / 0.8015 / 0.7782; evening(17-21) share 0.807 / 0.780 / 0.734;
belly(10-14) exactly 0.000; **overnight(0-6) 0.090 / 0.100 / 0.108**.

### D2 — stability FAILS (kill)

Min pairwise `r` on `alloc_share_dis` = **0.9726** against the ≥ 0.99 gate
(r(2023,2025) is the miss). The **charge-side control through the identical
code path passes: 0.9919** (share basis) / **0.9935** (fleet-normalized basis,
matching FINDING-caiso103 §1A's "≥ 0.994" to rounding) — so the failure is the
measurement, not the probe's basis. Stated honestly: the **CV limb is
non-discriminating** (the charge side also exceeds 0.20, at 0.392), so the
verdict rests on the r limb alone. The instability is a monotone
fleet-growth drift, not noise: hod 22 share 0.032→0.049→0.071, hod 23
0.014→0.018→0.040, evening block 0.807→0.780→0.734 — which also removes the
latest-year-carry forward story on this side.

### D3 — the binding pre-check FAILS structurally (the load-bearing result)

Against the keeper's own committed `hourly/storage_<year>.parquet` li_ion P1
surface (no replay). Three independent refutations:

1. **Scale-invariant slackness.** Residual overnight allowance =
   `(1 − da_frac_dis × s_non_overnight) × D[d]` = **0.271 / 0.274 / 0.302 ×
   D** vs a keeper overnight position of **0.094 / 0.053 / 0.088 × D** — i.e.
   **2.87× / 5.15× / 3.45× free for ANY day total**, so the refutation does
   not depend on the keeper's volume. `da_frac_dis` would have to be
   **0.989 / 1.045 / 1.018** to make the allowance merely *equal* the keeper's
   own overnight (impossible in two of three years; measured 0.778–0.802).
2. **Wrong sign.** The measured shape's 9–11 % overnight share makes the floor
   *force* overnight discharge — binding on **59–77 % of days at hod 0/5/6**,
   adding **+65 / +146 / +192 MW/h** against a defect needing **151 / 99 /
   98 MW REMOVED**.
3. **General form.** A floor can only ADD volume to an hour; the defect is an
   over-position. This kills the allocation-floor family for this defect, not
   just this shape — **including an evening-only-scoped variant**, since the
   allowance in (1) counts only non-overnight floors and is unchanged by
   dropping the overnight limb.

### What survives

The defect is unchanged and still load-bearing (FINDING-caiso127 §2's pin on
192/197/276 of 365 days is still the whole compression). Every *shaped*
instrument in the space is now refuted from one side or the other: floors
cannot remove (this session), the AS power/SOC upper bounds are slack
(caiso-74), the p95 cap is 89–95 % slack where the defect lives (caiso-99),
and the price instruments move volume not position (caiso-100/101). The
honest remaining diagnosis is the ask's own fallback — **candidate S2, the
DA/RT two-settlement separation** (the LP's single-market perfect-foresight
arbitrage itself), which per the memo is a structural change of a different
size and must be **chartered separately**, not approximated by a shaped floor.

### DO-NOT-REDO (new)

Re-filing S1 in any shaped-floor form (re-derived shape, altered support
threshold, evening-only scoping, raised `da_frac_dis`); re-measuring the
discharge allocation statistic or its stability; re-checking whether a floor
can reduce an over-position (it cannot, by form); treating the D2 CV limb as
discriminating; regenerating the charge-allocation artifact with discharge
columns.

The rest of the caiso-127 grant is untouched: the caiso-114 refinement stays
unfunded as a first delta, `hydro_budget_nameplate_aware` still arms in its
OWN single-delta A/B, pumped storage stays flagged-not-built. Promotion was
not granted and the keeper is unchanged.

Next number: caiso-130.

---

## caiso-130 (2026-07-27) — `hydro_budget_nameplate_aware`: the energy lands (P2 PASS all years), the **evening does not** — KILLED by K2-2024, and it is a rule-14 result

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED.** Arm B registered as a
REJECTED probe (`2026-07-27-caiso-130-nameplate-aware`), arm A as its control
(`2026-07-27-caiso-130-control`); both on the dashboard (rule 15). Full
evidence: `results/calibration/FINDING-caiso130-hydro-budget-nameplate-aware-2026-07-27.md`.
Gates frozen pre-solve at `26259a2`
(`PREREG-caiso130-hydro-budget-nameplate-aware-2026-07-27.md`). Scorer
`scripts/probes/_caiso130_nameplate_ab.py`; no-LP derives
`_caiso130_nameplate_blast_radius.py` / `_caiso130_nameplate_precheck.py`.

**Basis clean:** arm A reproduces the committed keeper **digit-for-digit** (max
delta 0.000000 MW, all 14 classes, all three years), so `2a01de8..HEAD` is
CAISO-inert and the A/B carries no basis caveat.

### Gate 0 — cross-ISO blast radius (the grant's own precondition), answered first

The flag is **NOT CAISO-scoped by construction**: it sits in the shared
`data.hydro` level-pinning branch, so it is live wherever a run pins a monthly
hydro level. Undeliverable share of the in-LP hydro budget, 2023/24/25:
**PJM 5.51/3.62/6.72 %**, MISO 1.30/2.12/0.87 %, CAISO 0.53/1.50/0.12 %,
NEISO 0.81/0.91/0.28 %; **ERCOT and NYISO pin no level ⇒ strict no-op,
verified bit-equal**. Arming it here still changes no other keeper (per-run
config field, default off, no shared derived artifact); rule 25 holds without
scoping work because the mechanism carries no ISO-fitted constant at all. The
forward path pins through the same branch on every hydro ISO. **PJM's ~10×
exposure is reported, not acted on** — separate A/B, separate owner act.

### The result

**P2 PASS, all three years** — the mechanism's own identity check. Re-allocation
fired at 130.2/352.7/26.3 GWh over 70/52/27 clipped plant-months with **0.0 GWh
physically unattainable**; annual hydro rises +14.5/+37.5/+2.8 MW = **98/96/93 %
of full delivery**. The undeliverable-energy defect (FINDING-caiso126 K4) is
closed: 0 MWh / 0 plant-months above the bound. Zero new free parameters.

**K2 KILL (2024)** — overnight |gap| 92 → 152 MW against a +50 MW bound. The
attribution is the load-bearing result: the LP spreads the freed water almost
**flat with an overnight tilt**, landing **35.5/46.5/25.9 % in the overnight**
against **15.7/11.3/31.9 % in the evening**. Evening movement +10.9/+20.4/+4.3
MW against a pre-registered no-feedback ceiling of +64.8/+172.5/+13.2 — feedback
ratios **0.17×/0.12×/0.33×** (caiso-126's water-value feedback ran the other
way, 1.2–3× *above* its proxy). Two structural causes: the water-fill routes
overflow to the plant-months with nameplate headroom left, whose headroom sits
in the hours they were not already running flat out; and the evening premium is
too compressed (the caiso-127 storage pin) for the LP's own λ surface to reward
concentrating water in h17-21.

**P1 FAIL 2023/24** (evening moved less than 25 % of its own ceiling). The 2025
"PASS" is an artifact of that year's tiny ceiling and is **not** quotable as a
partial win. P3/P4/K1/K3/K4/K5 all clean — C3a improves toward actual every year
(3.73→3.63, 7.70→7.56, 8.50→8.49 %), belly improves every year, D-4 off-window
0.0000, rubric identical (NOT-YET both arms). Gas −0.080/−0.266/−0.022 TWh
moves **C5a the wrong way** — second-order against a 6–8 TWh gap, recorded as a
real cost.

**Pre-registered ex ante, so it cannot be spun after:** this delta could never
have delivered the caiso-127 charter's "evening heals to ±150 MW" — the
arithmetic ceiling is 4–20× short of the gap. That was recorded as
not-applicable, not as a gate this run failed.

### Disposition — rule 14, read the right way

The accurate input made the fit worse, which rule 14 `[R-ACCURATE]` names as a
signal that **something else was being silently compensated**: the uniform
scale's nameplate clip was quietly removing 0.13–0.35 TWh/yr and offsetting part
of the model's known overnight hydro excess. So K2 is a **discovered defect
elsewhere**, not evidence against the nameplate bound; reverting to the uniform
scale would bury the error back inside an inaccurate input. The flag stays in
the tree **default-off, unreverted and undeleted**, a one-flag re-test once the
evening λ-formation lane lands — the same standing as the RoR family itself.

### rule-22 LOYO

Zero fitted parameters ⇒ LOYO reduces to per-year gate consistency. P2 holds in
every year (98/96/93 %); the evening under-delivery is same-signed in every
year; the overnight worsens in every year (+17.7/+60.0/+2.5 MW) and the K2
breach is confined to 2024 only because 2024 carries 2.6× the re-allocation of
2023 and 13× that of 2025 — **a systematic mechanism property scaled by the
delta's own size, not a single-year artifact** (the caiso-126 K1 structure).

### DO-NOT-REDO (new)

Re-arming the flag on the CAISO keeper against this residual in any scoped form
(per-window/class/plant restriction of where overflow is re-allocated);
re-measuring the cross-ISO blast radius or per-ISO undeliverable shares;
re-measuring the delta's energy budget, destination split, or evening ceiling;
re-solving the A/B to confirm direction (arm A is byte-identical to the keeper);
reverting to the uniform fleet-wide scale as an improvement (rule 14).

### The caiso-127 grant is now fully spent

Item 1 (S1) killed at the derive gates (caiso-129); item 3 (this session) killed
at the A/B gates; item 2 (the caiso-114 refinement) stays **unfunded** and still
gated behind the storage pin; item 4 (pumped storage) stays **flagged, not
built**. Every hydro-side candidate now converges on the same blocker — this
session is the sharpest evidence yet: a **zero-DOF** mechanism hands the LP
free, physically deliverable, evening-capable energy and the LP puts a plurality
of it in the overnight instead. **Newly raised, not built: the PJM
nameplate-clip ask** (3.6–6.7 % of its hydro budget, no CAISO-style evening pin).

Next number: caiso-131.

### ADDENDUM (same session, later) — OWNER PROMOTION of caiso-130

The owner promoted arm B in-session on an explicitly stated criterion: *"if
structural integrity improves but gates regress that may still be a keeper"*
(rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`). **CAISO keeper is now
`2026-07-27-caiso-130-nameplate-aware`**, superseding
`2026-07-27-caiso-126-ror-split`.

The promotion rests on three facts, none of them a fit:

1. **The rubric is IDENTICAL to the same-HEAD control** — C1/C2/C3b/C4/C7/C8
   PASS, C3a/C3c/C5a FAIL, C6 UNATTESTED, determination NOT-YET in both arms.
   **No scored criterion regresses.** What regressed is the overnight *window
   diagnostic* and this session's own pre-registered A/B gates (K2/P1), not the
   keeper scorecard.
2. **It closes a real physical defect with zero DOF** — 130.2/352.7/26.3 GWh/yr
   of monthly hydro budget that exceeded nameplate-hours and was silently
   clipped by the LP's own `pmax` bound; 0 MWh remains above the bound.
3. **Rule 14 in terms** — the accurate input made the overnight fit worse
   *because* the uniform scale's silent clip had been compensating for the
   model's own overnight hydro excess. Reverting would bury the error back
   inside an inaccurate input.

**The as-armed REJECTED verdict is recorded, not erased** (PREREG §4-§5,
FINDING §3-§4): K2-2024 fired and P1 failed 2023/24. The exposed overnight
regression is an **OPEN ROOT-CAUSE ITEM** — the caiso-127 evening λ-formation /
storage-arbitrage pin — **never a ledgered exception and never bought by a
tuned value** (exceptions ledger stays empty).

Precedent is exact: the superseded keeper `caiso-126-ror-split` was itself
promoted from a REJECTED probe on the same rule 1/14 grounds.

Keeper hygiene complete: DOF ledger seeded (11 entries, `build_dof_ledger.py`),
governance attestation re-attested carrying caiso-126's verbatim,
`keepers/CAISO.json` + `status/CAISO.js` rebuilt, and
`scripts/audit_keepers.py --iso CAISO` **PASSES clean** (0 failures, 0
warnings). Determination unchanged at **NOT-YET** (C6 governance gate, C3a/C3c/
C5a).

Next number: caiso-131.

## caiso-131 (2026-07-27) — DIAGNOSIS: C3a-2025 and C3c are **NOT one defect — they do not even share a year**. C3c fails **2023/2024 only** (2025 already PASSES on the rubric's small-count rule, actual 8 h < 10); C3a fails **2025 only**. C3c is a **supply-surplus** defect (min dispatchable headroom 12.2/12.7/13.1 GW over all 8760 h), NOT an offer ceiling (stack tops out at $1,266/$687/$1,632) and NOT a reserve-dual defect (the LOLP overlay IS armed and inert *because* of the surplus). The (λ, $200] band is **12.6–12.8 GW** deep — 52 % of the available gas fleet — which kills every quantity-side candidate before a solve. C3a-2025 is **Sep–Dec (81 % of the gap)** and **57 % of it is DSW→CA corridor congestion**, reproducing caiso-121 on the current keeper. NO SOLVE, nothing registered; keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED

**Measurement-only session (charter step 3: diagnose, then FILE the ask).** No
LP was built or solved, no mechanism was armed, nothing was registered. Step 4
(prereg + A/B) was conditional on the diagnosis landing a candidate with a real
driver; §2 of the memo shows the kill-before-solve envelope kills every
candidate now on the table, so the deliverable is the FINDING plus the ask —
the caiso-127/129 discipline.

Full record:
`results/calibration/FINDING-caiso131-tail-and-c3a-decomposition-2026-07-27.md`.
Owner ask with derive-first gates:
`docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`.
Instrument (committed):
`scripts/probes/_caiso131_tail_and_level_decomp.py` (sections A–E; committed
sidecars + committed bench/tail parts + a no-LP `run_year(fleet_only=True)`
reconstruction — never a replay).

**(1) The determination basis is three ISO-YEARS, not two criteria.** Scored on
the rubric's own basis and reproducing it digit-for-digit (C3a-2025 **+10.91 %**
vs the rubric's +10.9 %):

| year | C3a | band margin | C3c | required |
|---|---|---|---|---|
| 2023 | +3.22 % PASS | **+$3.67/MWh** | 0 h vs 47 h **FAIL** | ≥ 24 h |
| 2024 | +8.00 % PASS | **+$0.69/MWh** | 0 h vs 35 h **FAIL** | ≥ 18 h |
| 2025 | **+10.91 % FAIL** | **−$0.31/MWh** | 0 h vs 8 h **PASS** | — |

C3c-2025 passes on `TAIL_SMALL_COUNT = 10` (`|0 − 8| ≤ 10`); the scorer prints
no gated row for it because passing rows are not printed. **No year fails both
criteria.**

**(2) The "one defect / belly-to-tail redistribution" hypothesis is REFUTED**
three independent ways: different years (above); different months (January is a
**negative** C3a contributor in all three years — −0.31/−0.35/−0.23 — while
carrying 24/47 and 26/35 of the tail hours; C3a-2025 is Sep–Dec at +$2.36 of
+$2.90); and different magnitudes (belly excess +5.72/+4.36/+4.12 against a
tail deficit of −1.41/−0.80/−0.25, 3–6× apart and opposite in sign). What IS
true is that the price *distribution* is compressed — the model's absolute max
zonal price is **$192.3/$155.3/$94.3**, never reaching $200 in any hour — but
that is a shared symptom, not a shared mechanism.

**(3) The practical payoff of the refutation: the two are SEPARABLE.** Closing
C3c costs the C3a mean only **+$0.60 (2023)** and **+$0.36 (2024)** against
+$3.67 and +$0.69 of band headroom, and 2025 needs no tail at all. Three
binding design constraints follow, and they are the pre-solve envelope for any
C3c candidate: **2025 spillover ≤ +$0.00** (it has negative band room),
**2024 off-tail spillover ≤ +$0.30**, and the candidate must be **narrow in
hours** (~24/18 hours, nothing else). This is the quantified form of the
caiso-127 §1 trap.

**(4) The C3c three-way discriminator — (a) surplus, not (b) reserve dual, not
(c) offer ceiling.**
- **(c) REFUTED:** the offer stack's top is **$1,266/$687/$1,632/MWh** and the
  fleet offers 732/248/250 MW/h above $200 — **3,749/9,570/108 MW in the
  measured tail hours themselves**. The rungs exist; the LP never climbs them.
  **No offer-curve work can close C3c.**
- **(b) TRUE BUT DERIVED:** `reserve_price` is identically 0.00 in all 61,320
  zone-hours of every year (`caiso_reserve_coopt` off), and the published LOLP
  overlay **is armed** on the keeper (`caiso_scarcity_pricing=True`, so the
  persisted prices already include it) yet produces nothing — it cannot, since
  R never approaches MCL = 1,400 MW.
- **(a) THE CAUSE:** dispatchable headroom (gas+import+hydro) has a **minimum
  over all 8,760 hours of 12,173 / 12,689 / 13,137 MW**, `slack` is zero
  everywhere, and in the measured tail hours the model holds 22.6/27.5/24.2 GW.
  **Cross-ISO:** this is the same class as the standing PJM/ERCOT lead, and
  CAISO is its sharpest instance — `results/scarcity.py`'s own PJM HONESTY GATE
  says total-fleet headroom is indefensible and PJM moved to a plant-level
  ONLINE measure; **CAISO's overlay still uses total headroom.**

**(5) The kill-before-solve arithmetic.** The band `(λ, $200]` in the measured
tail hours holds **12,609 / 12,816 / 21,372 MW**, split gas_cc 2.7/2.8, gas_ct
5.2/5.2, gas_st 1.3/0.4, import 3.4/4.4 GW — 52 % of the available gas fleet,
no dominant limb. **No physically-grounded quantity-side derate removes it**
(an OFO curtails single-GW quantities; the measured corridor leaves only
1.6/2.8 GW of deliverable import headroom). Scale-invariant, the caiso-129
§3(a) form.

**(6) What the measured tail actually is.** Not a summer-evening net-peak
phenomenon: 2023 is **24/47 hours in January** at hod 6–7, 2024 **26/35 in
January** including one 16-hour run, 2025 all 8 at hod 5–9 in Jan/Mar/Apr.
2023/24 are **winter GAS events** — citygate at the **90th/99th percentile**
($11.25/$10.41 vs year means $5.20/$2.43) at unremarkable load (p88/p78) and
ramp (p76/p69) percentiles. The model's gas passthrough *works* there (CC offers
$103/$121 vs year means $61/$42; CT $145/$164) and λ still stops at $112/$123.
The real market was pricing **gas deliverability**, which the LP does not
represent. 2025's 8 hours have **no measured driver at all** (gas p57, load p65,
ramp p71) — RT-only formations, the MISO/NEISO anatomy.

**(7) C3a-2025, and what is different about 2025.** 2025 is the year with the
largest storage fleet (15.2 GW, 13.60 TWh discharged vs 6.00/9.85), the most
solar (52.5 TWh), the least gas (45.3 TWh), a higher run gas price (3.52 vs
2.54/2.19) — and **no citygate spike whatsoever** (max **$5.61** vs $24.29 and
$17.34). That last fact is *why* its measured tail is 8 hours and why C3c-2025
passes; it is a quiet year, not a modelling success. The C3a residual is
Sep–Dec (81 %), in the surplus/belly regime, and the caiso-121 attribution
**holds on the current keeper**: Sep–Dec 2025 CA λ $46.19 vs actual $39.44
(+$6.75), of which **CA − WECC_DSW congestion is +$3.87 (57 %)**, with WECC_PNW
stranded at $4.97. Required move: **−$0.31/MWh**, 0.8 % of the model level.

**(8) The real coupling.** The two criteria are not one defect but share one
structural object — the WECC import node / DSW→CA corridor — and **pull it in
opposite directions**: C3c needs the marginal import rung re-priced *up*,
C3a-2025 needs the corridor rent removed (CA λ pulled *down* toward its node).
**caiso-114** is the only mechanism on record to have achieved a CAISO C3c PASS,
and it did so by re-pricing that node — breaking C3a with an evening over-price
of +18/+12/+4 $/MWh. That breakage is now explained in advance (the
FINDING-caiso127 §1 storage fixed point) and priced by (3)'s envelope
($2–4/MWh against $0.69 and −$0.31). **caiso-114 is not re-armable as-is**, and
its original C5a justification was removed from the rubric by v2.9.

**(9) The ask, filed not built** (memo §3–§6), ranked:
**A1 (primary)** arm the caiso-121 corridor / export-path family in surplus —
load-bearing, diagnosed, needs only −$0.31/MWh; D-gates D1 (cross-year `r ≥
0.99` on the export envelope, the gate that killed S1), D2 (binds in ≥ 50 % of
the Sep–Dec surplus hours carrying the term), D3 (sign check: a floor that only
adds cannot reduce a congestion rent), D4 (C3a-2023/24 + C1/C2/C3b/C4/C6/C7/C8
guards). **A2** re-specify the CAISO LOLP overlay's reserve measure to the
plant-level ONLINE basis PJM already uses — zero new free parameters, a rule-14
correction, offered as a structural correction with an honest expectation that
its C3c yield is small; **blocked on a `unit_hourly` sidecar** the slim bundle
does not carry (the caiso-127 storage-sidecar precedent is the right fix).
**A3** a data-intake ask for the **SoCalGas OFO declaration record** — the only
route that could make C3c-2024 reachable without a fitted threshold (a citygate
> $8/MMBtu trigger reaches 27 h in 2023 but **17 h in 2024** against 18 needed;
moving the threshold to clear it is a fitted value, rules 13/24). **A4** the
honest fallback: ledger C3c as an ACCEPTED MEASURED-INPUT LIMITATION — the
disposition MISO and NEISO already carry, on evidence stronger than either;
**C3c is failing or ledger-caveated in all six ISOs**, and CAISO holds 0
ledgered caveats against a budget of 3. Owner call, and **not** a substitute
for A1.

**DO-NOT-REDO (new, binding):** re-testing the belly-to-tail redistribution
hypothesis; treating C3c as a three-year failure or C3a as multi-year; any
offer-curve / heat-rate work aimed at C3c; any quantity-side derate aimed at
λ > $200; re-arming `caiso_endogenous_wecc_node` as a C3c fix; deriving a
citygate threshold that makes C3c-2024 clear; "fixing" C3a-2025 via the extract
basis (including the +$0.77/+$0.48/+$0.81 weight-basis term the FINDING reports
— frozen, reported, not actionable); and re-measuring anything in FINDING
§1/§2/§4/§5/§6/§7, all of which the committed instrument carries without a
solve.

Next number: caiso-132.

## caiso-132 (2026-07-28) — DERIVE-GATE ADJUDICATION of ask A1 (the caiso-121 corridor / export-path family in surplus): **KILLED before any solve.** The DSW→CA corridor congestion carrying C3a-2025 is **import-direction** rent — across all 2023–2025 the corridor's export-direction bound is the ACTIVE constraint in **2 of 52,560 corridor-hours (0.0038 %)**, and in **0.000** of the Sep–Dec 2025 surplus hours carrying the +$3.87 term, on **both** legs. A1's limb (a), the export-direction deliverability envelope, is **not a new mechanism — it is already armed on the keeper** and is provably inert; limb (b), a surplus-scoped export floor, has the **WRONG SIGN** and reproduces the measured caiso-113 C3a break. NO LP built or solved, nothing registered; keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED

**Keeper UNCHANGED** (NOT-YET, fail {C3a-2025, C3c}). Derive-gate-only session
per the charter's step 1 ("ANY of D1–D3 failing KILLS A1 for the cost of a
derive — that outcome is a complete, publishable session"). Steps 2–3 (prereg,
A/B) are **not reached**: no solve was authorized and none was run, so there is
no bundle and no dashboard registration (the caiso-131 precedent). Full record:
`results/calibration/FINDING-caiso132-corridor-export-gates-2026-07-28.md`.
Instrument (committed): `scripts/probes/_caiso132_corridor_export_gates.py`
(sections D0/D1/D2/D3/E). Mechanism matrix updated in-session (rule 26): new row
`caiso_corridor_export_path` = **R** for CAISO, and the `import_hub_pricing`
note re-stamped.

**Method — binding direction read off the LP's OWN duals, with no solve.** The
slim bundle carries no flow sidecar, but for a corridor link bounded
`-export_cap ≤ f ≤ +import_cap`, LP optimality gives
`λ_terminus − λ_corridor = μ_import − μ_export` with both multipliers
non-negative and complementary. **The sign of the measured zonal spread IS the
binding direction** (`> +tol` import-bound, export bound STRICTLY slack;
`< −tol` export-bound; `|·| ≤ tol` neither), `tol = $0.50/MWh` (caiso-105).
Both λ series are in the committed `system_<y>.parquet`. The instrument
reproduces FINDING-caiso131 §7 **digit-for-digit** before measuring anything new
(2025 CA λ **46.19**, DSW **42.33**, CA−DSW **+3.87**, PNW **4.97**).

**The four gates:**

| gate | asked | result | verdict |
|---|---|---|---|
| **D0** (scope, added here) | is the export bound EVER active? | **2 / 52,560** corridor-h | **FAIL, family-wide** |
| D1 | export envelope hod shape, cross-year `r ≥ 0.99` | DSW **0.9577**, PNW **0.9879** | FAIL (non-discriminating) |
| D2 | export bound binds in ≥ 50 % of Sep–Dec 2025 surplus h | **0.000** both legs | **FAIL** |
| D3 | must REDUCE CA λ − WECC_DSW λ | **100 %** of defect rent is import-bound | **FAIL** |

D0 subsumes D2/D3: the export-direction bound is essentially never the active
constraint anywhere in the scored record, so **no** export-direction mechanism
can change this LP in **any** hour of **any** year — scoping, threshold and
window are all irrelevant. The 2 export-bound hours are both 2023 WECC_DSW
(model hours 2361/2697, hod 09, mid-April) at exactly −$20.00, the negative-price
floor — not in 2025, not in Sep–Dec, not in the belly.

**D1 fails, and it fails NON-DISCRIMINATINGLY — stated plainly.** The
import-direction **control** limb, which IS armed and load-bearing, fails the
same gate (DSW 0.9802, PNW 0.9797). Unlike caiso-129 — where the accepted charge
side cleared 0.9919 against a failing discharge side at 0.9726 and the gate
genuinely discriminated — here it rejects the armed control as readily as the
candidate. **No weight is placed on D1**; the kill rests on D0/D2/D3, which are
exact and direction-specific. Carried forward as a caution: the `r ≥ 0.99`
standard was identified on a storage allocation share and does not transfer
unexamined to a corridor ATC envelope, whose hod shape legitimately moves with
the neighbours' own solar build.

**Limb (a) is already armed.** The keeper carries `caiso_corridor_flow_limit=True`
with `caiso_corridor_atc_forward` falsy, so `run_calibration.py` takes the
measured branch, builds `corridor_export_env` and passes it to
`build_caiso_corridor_flow_groups(export_envelope=…)`, emitting the asymmetric
group `(idx, import_cap, False, export_cap)`. Re-arming it is a **no-op** and any
A/B against it would produce a byte-identical B.

**Quantity-side corroboration** (Sep–Dec surplus belly): corridor import ceiling
utilisation **0.760 / 0.824 / 0.929** — pressed hard against the import side and
rising — while the export ceiling is non-zero in 100 % of those hours and
untouched. Independent data, same conclusion as the duals.

**The finding underneath the kill: the stranding is PNW, not DSW.** On one
basis, CA − PNW is **+37.40 / +45.58 / +41.22** against CA − DSW's
**+3.54 / +2.36 / +3.87**, and in the 2025 defect hours the PNW leg is
import-bound in **76.4 %** of hours vs DSW's 44.1 %. The northern leg's measured
import envelope is also the small one (mean **1,714 MW** in 2025 vs DSW's 4,885)
on a corridor whose physical rating is several times that.

**§E forward pointer, OBSERVATION ONLY (not a candidate, not chartered).** The LP
bounds ONE signed link at the p95 of measured NET import; CAISO's northern
corridor is nearly balanced in net (−63/+236/+543 MW) while carrying 604–867 MW
gross import AND 323–667 MW gross export, flowing **both ways at once in 61–73 %**
of hours (DSW 81–84 %). Four live objections stand (FINDING §8): it is a
separate topology family needing its own charter; the model already over-imports
the surplus belly by **+2,606 MW** (caiso-121), so buying import headroom is
rule-1/rule-14 refused on its face; it must clear the ask memo §2 **E1 (2025
spillover ≤ +$0.00)**; and it sits where caiso-113 was rejected and caiso-114 is
not re-armable.

**What this changes.** C3a-2025 **keeps its diagnosis and loses its selected
family** — FINDING-caiso131 §7's attribution is reproduced unchanged, but
caiso-121's family selection for it is refuted, so C3a-2025 is now a diagnosed
defect with **no selected mechanism**. The ask memo's remaining items (A2 LOLP
reserve measure, A3 SoCalGas OFO intake, A4 ledger C3c) are unaffected — none
was contingent on A1. **C3c was not touched**, per the charter.

**DO-NOT-REDO (new, binding):** re-proposing the corridor / export-path family
for CAISO C3a in ANY form (envelope, surplus/window/regime-scoped floor) —
scoping cannot rescue a mechanism whose bound is slack everywhere; re-arming the
corridor export envelope as if it were new (already armed, no-op); re-measuring
the binding-direction census, the defect-hour rents, the CA−DSW/CA−PNW ladder or
the net-vs-gross decomposition (the committed instrument carries all of them
without a solve); quoting the `r ≥ 0.99` hod gate against a corridor ATC envelope
without its control limb; and treating §8's net-vs-gross measurement as a funded
candidate.

Next number: caiso-133.

## caiso-133 (2026-07-28) — the binding CAISO import limit is **the corridor deliverability group, ALONE**: the link's own TTC and the `WECC_import_simultaneous` seam row are **structurally unreachable in all 26,280 corridor-hours of 2023–2025, in BOTH directions**, and their solved duals are **exactly 0.000 in every hour**. 100 % of the defect-hour congestion rent is charged by a MEASURED envelope — and in the very hours it binds the model already carries **+2.0 to +2.5 GW MORE import than actually flowed**, so it is not the inaccurate input. **C3a-2025 handed back as unreachable from the corridor lane, no candidate manufactured.** Plus two new write-only sidecars proved byte-inert (`max |delta| = 0`), which unblocks ask A2's D1 — and D1 **passes**

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED. Nothing armed** — no
mechanism, no flag, no new `ScenarioConfig` field. The one solve was a no-delta
keeper replay whose only purpose was the byte-identity proof; registered as the
control arm `2026-07-28-caiso-133-sidecar-control` (rule 15). Full evidence:
`results/calibration/FINDING-caiso133-binding-limit-separation-2026-07-28.md`.
Instruments: `scripts/probes/_caiso133_binding_limit_separation.py` (A/B/C/D),
`scripts/probes/_caiso133_sidecar_invariance.py`.

### Part 1 — two write-only sidecars, and the proof they cannot touch the LP

`hourly/unit_hourly_<y>.parquet` (per-LP-unit `mw` **and** `cap_mw` = the LP's
own `pmax × availability` bound) and `hourly/network_<y>.parquet` (per-link and
per-interface-group `mw`, `dual`, `limit_up`, `limit_dn`). Both under `hourly/`,
so a KEEPER bundle carries them.

**Byte-identity, exact.** The keeper recipe replayed at this session's HEAD
reproduces the committed keeper with `max |delta| = 0` on `class_hourly.mw` and
on every `system` column (price / slack / dump / demand / reserve_price), all
three years — not a tolerance, zero. The LP-side additions (the interface row
block's offset out of `build_constraints`; the interface row duals and flow
reduced costs sliced out of the HiGHS solution) add no row, bound or coefficient.

**Size nearly bit.** The first build wrote `unit_hourly_2023` at 12.60 MB, of
which the tiled `0..8759` `hour` ramp alone was **11.12 MB** (PLAIN int32, 88 %
of the file) against 1.04 MB for `mw` + `cap_mw`. `DELTA_BINARY_PACKED` on that
one column (lossless) takes it to **1.74 MB** and the 3-year bundle from ~38 MB
to **5.2 MB**. Pinned by a regression test — losing it silently re-inflates every
future keeper.

### Part 2 — the separation, answered two independent ways that agree exactly

**§A, no LP at all.** A limit can carry a positive dual only if it is attainable.
Each leg's flow is bounded above by its own corridor cap, and that cap never
reaches the link's TTC (max ratio 0.801 / 0.672 / 0.721 across the years) nor do
the two legs' caps sum to the published MIC (max 0.600 / 0.581 / 0.667) — **0
hours out of 26,280, in both directions**. So the corridor group is the only
limit that can *ever* bind. The caiso-132 §2 ambiguity is closed analytically,
from bytes that were already committed when caiso-132 was written.

**§B, the measured duals.** The zero-cost flow column's stationarity gives
`λ_to − λ_from = −z_link − Σ_g s(g,link)·y_g` exactly, each term one limit's
rent. On the Sep–Dec surplus belly: **100.0 % corridor group, 0.00 link TTC,
0.00 seam row** on both legs in all three years (2023 PNW 17.16 / DSW 8.99; 2024
21.71 / 6.31; **2025 35.33 / 9.02**), identity closing to 3.4e-06 $/MWh. Three
exact reconciliations: the rents match FINDING-caiso132 §6 digit-for-digit; the
corridor group's binding-hour share read off its *dual* reproduces caiso-132 §3's
census read off the *spread sign* (2023 PNW 0.5281, DSW 0.3765); and the link/seam
duals are nonzero in **0 of 8,760** hours.

**§C, rule 14 — the limit is not the inaccurate input.** Against the same EIA-930
bytes and (month × hod) bucketing the cap is *built* from, in the defect hours:
model import 3,296 / 4,898 / 5,569 MW against measured 756 / 2,882 / 3,510 MW —
**+2,540 / +2,016 / +2,059 MW**, reproducing caiso-121's +2,606 MW over-import on
the current keeper. The cap is not too tight; on the hours that matter it is if
anything too generous. Relaxing it is rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`
refused, and FINDING-caiso132 §8's net-vs-gross observation is *priced* by this
(its objection (ii) measured on the exact hours it would act on), not rehabilitated.

**The hand-back.** The corridor congestion carrying C3a-2025 is real, is
import-direction, and is charged entirely by a correct measured input. There is
nothing to fix and no slack limit to tighten — **the corridor lane is closed for
C3a-2025 and no candidate was manufactured.** Filed as an observation only: the
cap binds because the model *wants* ~2 GW more import than reality took, so the
pressure is **upstream of the corridor**, in whatever makes CA's own midday
supply expensive enough to pull it.

### Part 1's dividend — ask A2's D1 is unblocked, and it PASSES

D1 (ask §4) was recorded BLOCKED on exactly this data. Plant-level ONLINE
*thermal* headroom: min 704 / 701 / 670 MW, **p10 1,201 / 1,119 / 1,021 MW**
against a 5 GW gate and the 12–13 GW total-headroom surface FINDING-caiso131 §4
measured — inside the LOLP's live range (MCL 1,400 MW, σ 2,500 MW). **D1 does not
kill A2.** Two honest qualifications: (i) the ask's premise that CAISO "evaluates
`reserve_headroom` on total fleet headroom" does not match the code —
`caiso_scarcity_overlay` already passes `reserves_online_mw=r_online` into
`ordc_adder`'s half-hour term; what is large is `reserves_total` (online +
offline + import headroom), the full-hour term; (ii) the number is the online
*thermal* component only — a lower bound on `r_online`, which also carries storage
and curtailed-renewable headroom no committed sidecar holds. A2's D2/D3 are NOT
run here; arming A2 remains a separate owner ask.

### Also measured: the `capacity_deliverability_limits` seam half is INERT in the backcast

At 16,055 / 16,452 / 16,148 MW the published MIC sits above the sum of both legs'
own measured envelopes (max 9,631 / 9,557 / 10,777 MW), so the seam row's dual is
exactly 0.000 in every hour of every year. This bounds what the flag's part (a)
can do in a **backcast**; it says nothing about the forecast lane, where the
corridor envelope is not the binding object. Mechanism matrix updated (rule 26).

### DO-NOT-REDO (new, binding)

Re-measuring which CAISO import limit binds by any route (§A settles it
analytically, §B confirms it from the duals, and they agree exactly); proposing
to relax, widen or re-derive the corridor import envelope to close C3a-2025 (the
model already over-imports those hours by +2.0–2.5 GW against measured flow);
re-deriving C3a-2025 as a transmission defect at all (the binding object is a
correct measured input — the pressure is upstream); re-running the sidecar
byte-identity proof (`max |delta| = 0`, committed); re-measuring ask A2's D1 (the
committed instrument re-runs it in seconds); and dropping the
`DELTA_BINARY_PACKED` encoding on the sidecars' `hour` column.

Next number: caiso-134.

## caiso-134 (2026-07-28) — the excess midday import is **ONE tranche** (`DSW_surplus_clean`), and **NEITHER side's PRICE is misplaced**: the import rungs sit on their own measured hubs **to the cent** ($0.00 / $4.00 / $5.00 wheel, all three years) and the CA replacement band's implied delivered gas tracks the measured SoCal citygate to −$1.70 / +$0.29 / +$0.13 $/MMBtu. The defect is **QUANTITY/STATE on the CA side**: on the SAME 81–82 physical plants the model's gas fleet runs at **0.58–0.63×** reality's own belly utilisation, and **74–86 % of the CA supply that would replace the excess import is OFFLINE**. **Lane = the caiso-118b RA must-offer committed-gas state.** Tightening the corridor is priced at **+$14.40 to +$17.92/MWh the WRONG way**

**Derive-first, NO SOLVE, nothing armed, nothing registered.** Keeper
`2026-07-27-caiso-130-nameplate-aware` UNCHANGED (NOT-YET, fail {C3a-2025, C3c}).
Full evidence:
`results/calibration/FINDING-caiso134-import-demand-source-2026-07-28.md`.
Instrument: `scripts/probes/_caiso134_import_demand_source.py` (§A–§E), run
entirely off the keeper's committed `hourly/` sidecars (the caiso-133 dividend)
plus `run_year(fleet_only=True)` — no LP built, no solver called.

Chartered by `FINDING-caiso133` §6's hand-back: the corridor cap binds because
the model *wants* ~2 GW more import than reality took, so the pressure is
upstream. Defect hours are the standing caiso-120/121 set (Sep–Dec, hod 10–15,
measured RT ≤ $20; n = 192 / 239 / 229).

### §A — the excess is one tranche, and it is not the one that is capped

`DSW_surplus_clean` carries **2,665 / 1,995 / 2,638 MW** against a corridor
over-import of **+2,540 / +2,016 / +2,059 MW**. Every other economic rung is
inert: `DSW_CT` and `WECC_scarcity` at **0.000** utilisation in all three years,
`PNW_midC` 0.007–0.018, `DSW_CCGT` 0.002–0.098. The two firm rungs
(`DSW_solar_PV`, `PNW_hydro_base`) are at util **1.000** — self-scheduled
must-flow, a quantity no offer change can move. Crucially the marginal tranche
is **INTERIOR at 55 / 63 / 69 %** of its own measured WEIM depth, so **its depth
is not the binding object** (the corridor group is, caiso-133 §3/§4).

*Side observation, filed not chartered:* **70 → 161 → 307 MW** of self-scheduled
firm PNW hydro is **DUMPED** at the `WECC_PNW` node because the PNW corridor cap
cannot carry it; `λ_WECC_PNW` collapses to a **median −$26.00** against a
measured MALIN print of **+$26.23**. A real interaction between
`caiso_firm_import_selfschedule` and `caiso_corridor_flow_limit`, growing yearly.

### §B — who it displaces, and the priced counterfactual

Per-hour CA replacement ladder (headroom below λ excluded — the LP already took
what it could there): replacing the excess costs **+$17.92 / +$14.40 /
+$15.90 /MWh** at the margin, taking CA λ **23.42 → 41.34**, **17.49 → 31.89**,
**26.31 → 42.21** against actuals of $9.36 / $8.75 / $9.06. So **tightening the
corridor makes C3a strictly worse** — the mirror of caiso-133 §5's refusal,
now priced, which closes **both** directions of the corridor lane with numbers.
And the block is **20.5 / 26.4 / 13.9 % ONLINE**: 74–86 % of it is capacity the
model would have to START.

### §C/§D — both prices check out against their own anchors

**Import:** every rung reproduces `inject_caiso_per_hub_intertie_prices`'s
`hub + wheel + border × EF/EF_unspec` to the cent, all three years —
`DSW_overnight_clean` / `DSW_daytime_clean` **+0.00** (raw hub),
`DSW_surplus_clean` **+4.00** (its OATT wheel), `PNW_midC` **+5.00**. Neither
"offered too low" nor "too deep" survives (and a deeper cheap rung moves λ the
wrong way anyway).

**CA:** the 2025 replacement band's offer $43.45 = fuel $30.04 + VOM $2.00 +
`gas_offer_net_revenue_margin` $3.96 (9.1 %, at its registered $4.7964 anchor) +
CA cap-and-trade $7.44. Implied delivered gas **$4.07 vs the measured SoCal
citygate $3.94** (2024 +$0.29; 2023 **−$1.70**, i.e. the model *below* the
print — the sign flips, so this is print cadence, not inflation).

### §E — the CA quantity, on the honest CEMS basis

The raw EIA-930 CISO `NG` cell is unusable as a midday anchor
(`FINDING-caiso-c2c4-bench-basis-930ng`: a fabricated noon-peaked block from
~2024-05; it prints 79.0 TWh of 2025 CAISO gas against the bench's honest 51.6).
Against **matched-plant CAMPD hourly CEMS**, each side normalised by its own
annual mean:

| year | plants | model belly util | CEMS belly util | shape ratio | deficit | vs excess |
|---|---|---|---|---|---|---|
| 2023 | 82 | 0.442 | 0.767 | **0.575** | −1,574 MW | 62 % |
| 2024 | 81 | 0.448 | 0.746 | **0.600** | −1,263 MW | 63 % |
| 2025 | 81 | 0.527 | 0.834 | **0.632** | −1,081 MW | 53 % |

The real fleet runs at 75–83 % of its own annual average in these hours; the
model at 44–53 %. That one shape defect is **53–63 % of the corridor
over-import**, level-free, with the compensating excess in the evening (Sep–Dec
h19 util 1.83 model vs 1.45 CEMS). And the model has **no zero-cost margin**:
solar curtailment is **0.41 / 0.69 / 0.01 %**, wind **0.00 %** — re-confirming
`FINDING-caiso118`'s suspect-1 refutation on the current keeper.

### The verdict

By elimination on measured anchors, the only object left is **how much CA gas is
COMMITTED in the belly** — `FINDING-caiso118b`'s RA must-offer paradigm. This
session reproduces it on the **current** keeper, on the **honest CEMS basis**
(caiso-118's "2–3.6×" is **1.6–1.7×** shape-normalised plant-for-plant), and
localises it to the exact C3a-2025 defect hours. The two objects caiso-118b named
are unchanged on this keeper four sessions later: `caiso_ra_min_load_frac` =
**0.26** (physical ~0.40–0.57) and `caiso_ra_mustoffer_quantity_gate` = **False**
(`CAISO_RA_MUSTOFFER_GAS_MW` wired as a CAP, never as the commitment DRIVER).
**Nothing is proposed** — chartering a candidate is a separate owner act and must
clear the ask memo §2 envelope, above all E1 (2025 ≤ +$0.00, −$0.31 of room).
Directional prior only: more committed belly gas pushes belly λ *down* (E1's
favourable direction) but also moves the evening, where §E shows the model
already over-runs gas ~25 % — that is where the pre-check belongs.

Rule 20: 2023–2025 only. Rule 26: no mechanism tested, so no matrix cell moves.
Ask A2's D2/D3 were NOT reached (the optional second item).

### DO-NOT-REDO (new, binding)

Re-measuring which tranche carries the over-import (§A); proposing to re-derive /
deepen / trim the `dsw_*_clean` depths for C3a-2025 (the marginal tranche is
interior at 55–69 %, so depth is slack); repricing ANY CAISO import tranche
against the residual (every rung matches its own hub to the cent — a proposal
must first show the hub series or wheel wrong against its own source); proposing
CA gas is offered too high as the C3a-2025 lever (fuel tracks citygate, sign
flips across years); **tightening** the corridor envelope (priced at +$14–18/MWh
the wrong way); using the raw EIA-930 CISO `NG` or `Demand` cell as a midday
anchor for CAISO gas or load (both corrupt for this purpose — use matched-plant
CAMPD CEMS and the caiso-80 supply-consistent series); and re-measuring belly
solar/wind curtailment as a $0-rung candidate.

Next number: caiso-135.

---

## caiso-135 (2026-07-28) — the committed-gas charter is **REFUSED on measured bytes, before any solve**: the RA floor is multiplied by **PLANT** capacity, but the standing `caiso_ra_min_load_frac = 0.570` is a per-**TURBINE** turndown; on the consuming basis CAISO measures **0.289–0.304**, so the keeper's **0.26 is already inside the band** and caiso-118b's "fitted below physical" premise is refuted. The quantity gate is a **verified NO-OP**. And the lane's premise falls: on the same 28 matched plants the model has **1.01–1.13× reality's online CC plant count** at **0.74–0.80× its MW** — a LOADING defect on already-committed plants, not an under-commitment. Keeper UNCHANGED, **nothing armed, no solve**

Full record: `results/calibration/FINDING-caiso135-committed-gas-charter-2026-07-28.md`.
Instrument: `scripts/probes/_caiso135_committed_gas_charter.py` (§A/B/C/D/E/R,
no LP built, no solver called).

**D1 (decisive) — derive, don't pick.** `caiso_ra_mustoffer_min_gen` floors
`min_load_frac × plant_pmax` ("the floor is the PLANT's minimum stable load …
never a per-tranche fraction"), and CAISO is `plant_level_fleet=True`, so the
measured statistic must be the **plant's** minimum stable configuration. Both
bases, both conventions, identical CAMPD CA bytes:

| year | UNIT full-op | **PLANT full-op** | UNIT online | PLANT online | plant/unit |
|---|---|---|---|---|---|
| 2023 | 0.5662 | **0.2891** | 0.3891 | 0.2433 | 0.511 |
| 2024 | 0.5697 | **0.3005** | 0.3863 | 0.2587 | 0.527 |
| 2025 | 0.5720 | **0.3041** | 0.3758 | 0.2188 | 0.532 |

The UNIT column **reproduces caiso-119's own 0.565/0.570/0.570** to within 0.002,
so the conventions are matched and the only difference is the **basis**. The
~0.52 ratio is the 2-train CC signature (a plant's minimum stable *configuration*
is one train at min). ERCOT's 0.574 agrees with the UNIT column because
60-Day-DAM LSL/HSL pairs are **also per-train** — corroboration of the basis, not
of the value. Reality test: a 0.570 floor is contradicted by CAISO's own plants
in **35.7–43.0 %** of online plant-hours, 0.3756 in ~20–23 %, 0.26 in 7.5–9.4 %.

**GOVERNANCE — the caiso-121/122 disposition is WITHDRAWN AS STATED.** "The
measured 0.570 is KEPT … and is still the value the next keeper must carry" is a
basis error and must not be carried forward. Rule 14 `[R-ACCURATE]` is *served*
by the withdrawal: the accurate input is the plant-basis statistic and the
estimate being displaced is the per-turbine one. Identification source for any
future value is the new
`data/raw/_processed-legacy/campd_gas_commitment_params_plant_CAISO.csv`
(**0.259** pooled cap-weighted p50), never the per-unit artifact. No re-solve is
warranted to move 0.26 — it is inside the band and the family is near-inert.

**D2 / D5 — not the refusal.** D5 passes with headroom (CC_REGULAR forced share
7.2/8.3/9.9 % → 10.0/10.5/12.4 % at 0.30, cap 30 %). E1/E2 were never at risk
from the *sign* (min-load supply pushes λ down, and the model's evening CC plants
already sit at 0.90–0.93 loading, far above any candidate floor). The lever is
**already SOLVED and near-inert**: caiso-119's A/B moved belly gas −28/+59/+52 MW
for a 2.2× larger delta, because the RA bridge owns **1.8 % of floored cells**.

**D4 — object 2 is a measured NO-OP.** CC_REGULAR is floored by exactly one
mechanism (`ra_mustoffer_bridge`), so a parameter change would have been rule-19
clean. But the bridged CC fleet is **13,465 / 11,670 / 9,580 MW** against a
published cap of **19,130 / 15,566 / 15,566 MW**, and the gate sheds
cheapest-startup-first — CT (0.1–1.0 % forced share) goes first. The gate cannot
remove one bridged CC plant. The **DRIVER** reframe fails separately: must-OFFER
is a bid-insertion duty, not must-stay-online (the code's own G-61 adjudication
already named the conflation) — rule 1 `[R-STRUCT]`.

**THE REFRAME (the finding that closes the lane).** On the same 28 matched CC
plants, in caiso-134's own defect window, one shared online convention:

| year | model online | CEMS online | on ratio | model MW | CEMS MW | MW ratio |
|---|---|---|---|---|---|---|
| 2023 | 13.9 | 13.0 | **1.072** | 3,695 | 4,638 | **0.797** |
| 2024 | 11.7 | 10.4 | **1.129** | 2,749 | 3,670 | **0.749** |
| 2025 | 10.1 | 10.0 | **1.011** | 2,699 | 3,637 | **0.742** |

The model has **as many or more** CC plants online than reality and runs each one
lower. A min-load floor is the wrong instrument by construction: **the plants it
would commit are already committed.** Energy above min-load is an economic
dispatch outcome, so no commitment mechanism reaches this defect. This corrects
caiso-118b's *causal* claim, as caiso-134 §7 already corrected its magnitude.
(No conflict with caiso-134 §3's "74–86 % offline": that ladder ranks the
cheapest replacement across all CA classes and is dominated by CT_PEAKER and by
CC plants **reality also has off**.)

**Code (additive, byte-safe).** `derive_campd_gas_commitment_params.py` gains
`--plant-basis`; the default per-unit path is verified **byte-identical** for
CAISO and NYISO (whose 0.523132 / 0.239362 are shipped bridge parameters). No
`src/market_sim/` change. Rule 22: 2023–2025 only. Rule 28: the
`gas_commitment_bridge` row's CAISO note + evidence updated (cell stays K — the
bridge itself remains the armed keeper mechanism; the quantity sub-flag is
recorded INERT). No dashboard registration due — no run was produced.
Ask A2's D2/D3 again NOT reached; A2 is now the strongest remaining candidate.

### DO-NOT-REDO (new, binding)

Raising `caiso_ra_min_load_frac` toward 0.40–0.57 as a CAISO lever (per-turbine
range applied to a plant denominator; contradicted in ~2 of 5 online hours);
re-deriving it on the per-unit basis, or citing ERCOT 0.574 / NYISO 0.523 as
corroboration of a CAISO plant-basis value (they agree because they are also
per-train — rules 5 `[R-NO-MAGIC]` / 25 `[R-ISO-SCOPE]`); re-solving the
`min_load_frac` A/B to reach C3a-2025 (SOLVED at ±60 MW by caiso-119 for a 2.2×
larger delta); arming `caiso_ra_mustoffer_quantity_gate` as a cap (verified
no-op, all three years); wiring `CAISO_RA_MUSTOFFER_GAS_MW` as a commitment
DRIVER / obligation floor (must-offer ≠ must-run, and §7 removes the premise);
and proposing that the CAISO belly deficit is an under-COMMITMENT of gas plants
— any future belly-gas candidate must address per-plant LOADING above min-load
and state why a commitment mechanism could reach a defect on already-committed
plants.

Next number: caiso-136.

---

## caiso-136 (2026-07-28) — the measured unit-availability window family (`unit_outage_short_windows` + `unit_partial_outage_windows`) is **STRUCTURALLY UNDERIVABLE for CAISO**, adjudicated **INERT**: the detector is COAL-ONLY and CAISO's entire coal fleet is **2 units / 50.0 MW** (0.16 % of capacity, 0.04–0.07 % of keeper energy) at **one facility absent from CAMPD entirely** — the CA extract carries 108–109 facilities with **ZERO coal-fuelled rows**. Both derives return **0 windows**. STOPPED at the lane task's own Step-1 branch point — no A/B, no solve, keeper UNCHANGED

Full record: `results/calibration/FINDING-caiso136-unit-availability-windows-2026-07-28.md`.

**Step 1, run as specified.** `derive_campd_unit_outages.py --iso CAISO
--short-windows` and `--partial-windows`, years 2023 2024 2025 → **0 windows, 0
units, 0 MW-days** in both. Artifacts committed with headers and no rows: the
negative result is the record and stops a future session re-running the intake.

**Why it is zero — structural, not a guard threshold.** (a) CAISO's coal fleet
is `10684_TG8` + `10684_TG9`, 25 MW each, zone ZP26 — one facility (Argus Cogen,
Trona CA). (b) Facility 10684 is **absent from the CA unit-level extract in all
three years and from the facility-level extract too**; the CA fuel mix is
104–105 Pipeline Natural Gas, 2 Natural Gas, 1 Other Gas, 1 Wood, and **zero**
coal-fuelled rows in any year. There is no series to filter, so no guard setting
could change the outcome. (c) Even a perfect window could not matter — CAISO COAL
energy in the keeper is 0.0935 / 0.0517 / 0.0830 TWh, i.e. **0.067 / 0.038 /
0.065 %** of 140.1 / 136.8 / 127.4 TWh.

**No guard was touched** (rule 23 `[R-FROZEN-DERIVE]`): CF ≥ 0.55 baseload guard,
plateau constants and coal-only class scope unchanged, and the detector was
**not** extended to gas CC — the layup confound (economic single-train CC
operation is indistinguishable from a partial outage in CF) needs its own
charter, not a workaround for an empty coal extract.

**The adjudication is CAISO's own, not a port of ERCOT-126** (rule 25
`[R-ISO-SCOPE]`). The two refusals differ in kind: ERCOT's units and CEMS series
exist and the windows are derivable but *unhelpful*; CAISO's are **underivable**.
That matters for re-opening — ERCOT's could move on a better gate, CAISO's only
if CAISO gains a CEMS-reporting coal unit.

Rule 28 duty (b) discharged in-session: `unit_outage_short_windows` CAISO cell
**U → I** (cells `IUKKIR` → `IIKKIR`; the concurrent NEISO `R` (neiso-69) and NYISO `I` (nyiso-93) preserved untouched, rule 25) with this finding cited. Steps 2–3 not
reached by the task's own branch point, so **no dashboard registration is due**
(rule 15 applies to completed runs) and no DOF entry (nothing armed). Rule 22:
2023–2025 only. No `src/market_sim/` change.

### DO-NOT-REDO (new, binding)

Re-running the `--short-windows` / `--partial-windows` intake for CAISO (0
windows; the committed empty artifacts are the record); loosening the CF ≥ 0.55
guard, plateau constants or coal-only scope to obtain CAISO windows (rule 23,
and futile — the denominator series does not exist); extending the detector to
CAISO gas CC as a workaround (own charter, layup confound unresolved); and
citing ERCOT-126 as the reason CAISO's cell is `I` (independent refusals,
different in kind).

Next number: caiso-137.

## caiso-137 (2026-07-28) — ask **A2 CLOSES as a no-defect**; the storage tier under it is a real rule-14 defect that **fails D2 on E1 structurally** and cannot close C3c

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED** (NOT-YET, fail set
{C3a-2025, C3c}). **No LP was built, no solver called, nothing armed**, no
`ScenarioConfig` field added. Derive-first, as the brief required.
Evidence: `results/calibration/FINDING-caiso137-a2-lolp-reserve-measure-2026-07-28.md`.
Instrument: `scripts/probes/_caiso137_lolp_reserve_measure.py` (§A–§F).

**STEP 1 — A2 as written is CLOSED (option d).** `FINDING-caiso133` §7 had
already flagged that the ask's premise did not match the code; the correction
runs deeper — none of the ask's live readings survives.
`results/scarcity.py:2002-2024` already splits online/offline through
`_online_plant_mask` and passes `reserves_online_mw=r_online` into `ordc_adder`.
(a) `reserves_total = r_online + r_offline` **is** the published two-half-hour
RTORPA form, `r_offline` being offline quick-start 30-minute non-spin — no
defect. (b) **MOOT**: `caiso_scarcity_import_headroom` is **False** on the
keeper, so `import_headroom` enters **no tier at all**. (c) **NO**: the code
already carries storage and curtailed-VRE headroom in `r_online`;
caiso-133's "missing" was about the *sidecar*, not the code. A rule-1
`[R-STRUCT]` judgement against the code, not the residual.

**The decomposition A2 was blocking on** (new, all three years): `r_online` p10
= 8,748 / 10,499 / 13,124 MW, of which **storage is 5.7–11× the thermal leg**
(thermal p10 1,201/1,119/1,021 MW — caiso-133's D1 was a lower bound by roughly
an order of magnitude, exactly as it warned). **Curtailed VRE is identically ~0**
in all 26,280 hours: the LP carries a `Dump` column, so surplus renewables are
dumped, not curtailed below potential. *Correction to `FINDING-caiso131` §4*:
the overlay is **nearly** inert, but not for the stated reason — with σ = 2,500
the Gaussian tail still reaches ~4σ, so the reconstructed adder is $0.14 /
$0.016 / $0.0004 dw-mean and exceeds $10/MWh in 20 hours of 2023.

**The real defect (rule 14 `[R-ACCURATE]`, filed NOT armed).** `runner.py:2088`
passes `storage.power_cap` — the per-unit **December nameplate**
(`storage.py:401`, `power_cap_mw = monthly_p[-1]`) — which `reserve_headroom`
broadcasts to a **constant** hourly series. The LP dispatches against the hourly
`storage_power_cap` carrying the COD vintage ramp. Phantom online reserve:
**3,049 / 3,567 / 4,317 MW max**, 1,854–2,277 MW mean, in **83–92 % of hours**,
up to **51 % of `r_online`**. Corroborated by the repo disagreeing with itself —
`derive_ordc_overlay.py:200` and `derive_caiso_scarcity_overlay.py:119` (the
derivers written to *reproduce* these overlays) both read the **hourly** cap.
Basis unambiguous: COD-ramped ≡ LP cap, `max |Δ| = 0.000000 MW` all years, so
no caiso-99 shape-anchor double-count to weigh (rule 19).

**D3 PASS** — VOLL $2,000 / MCL 1,400 / σ 2,500 / shift 0.0 unchanged at their
published values; no new field, threshold or multiplier (one array swapped for
another at one call site).

**D2 FAILS on E1 — structurally.** Δ annual dw-mean LMP = **+$2.4926 / +$0.5542
/ +$0.0668**; E1 (2025 ≤ +$0.00) **FAIL**, E2 (2024 ≤ +$0.30) fails at face
value. A measure-shrinking correction can only *raise* the adder, so **E1 fails
for the whole family by construction**, verified across a 0–5,000 MW sensitivity
sweep. **No solve authorized; none run.**

**Honest limits, measured not asserted.** The rebuild is a
`run_year(fleet_only=True)` approximation (1,800–1,808 units vs the keeper's
1,619), so `r_online` is reconstructed. Bounded two ways: (i) the LP's own dump
floor (λ_z ≥ −dump_cost) pins the realised adder to **exactly 0** in 2,774 /
4,251 / 2,771 hours — the reconstruction is spurious in only 152/133/7 of them,
biased high by 6.5–23 %, implying `r_online` understated by ~0.2–0.9 GW; (ii) the
δ-sweep. **E2 is therefore recorded INDETERMINATE**, not FAIL — it flips to PASS
from δ = 500 MW, inside the measured error band.

**And it does not buy C3c.** On the scorer's own basis (`_tail_hours`, max zonal
LMP > $200; CAISO has no `scarcity.parquet` so the fallback applies): **16 h in
2023** against the 24–94 h band and **0 h in 2024** against 18–70 h — at δ = 0,
the *most generous* point. Every correction pushes `r_online` up and the count
**down**: 0 h at every δ > 0. The `FINDING-caiso131` §5 band arithmetic holds —
this corrects the measure, it does not remove the 12.6–12.8 GW band.

**Disposition.** A2 closed; its replacement filed with its measurement, **not**
armed. Arming is a separate owner act to be decided on rule-1/14 structural
grounds — *not* on the residual in either direction. It would need CAISO-scoped
call-site handling so ERCOT is byte-identical (`runner.py:1996` carries the same
argument — rule 25 `[R-ISO-SCOPE]`), the full three-year A/B with both arms
registered (rules 15/16), and the §5 bounds rerun against the arm's own solved
reserves.

Rule 28 duty (b) discharged in-session: `ordc_scarcity_overlay` CAISO cell stays
**K** (armed, unchanged — nothing was flipped) with the caiso-137 adjudication
added to its note + `ev`; other ISOs' cells preserved verbatim (rule 25). **No
dashboard registration is due** — rule 15 applies to completed *runs*, and this
session produced no bundle. Rule 22: 2023–2025 only.

### DO-NOT-REDO (new, binding)

Re-specifying A2 as options (a)/(b)/(c) (all three adjudicated against the code);
re-measuring the CAISO overlay's `r_online` decomposition (committed, no-solve
instrument); proposing the flat-nameplate storage tier as a **C3c** candidate
(16 h max against a 24 h floor, 0 h at every other sweep point); re-running the
**E1** pre-check for any measure-*shrinking* correction to this overlay (E1 fails
the family by construction, not this candidate in particular); and re-deriving
which storage cap the overlay should use (COD-ramped ≡ LP cap to 0.000000 MW,
and both derivers already use the hourly cap).

Next number: caiso-138.

### CORRECTION (caiso-137b, 2026-07-29) — two secondary caiso-137 claims WITHDRAWN; the primary result stands

Filed the next session-day, before any further work. Evidence:
`results/calibration/FINDING-caiso137b-overlay-reachability-2026-07-29.md`.
Instrument: `scripts/probes/_caiso137b_overlay_reachability.py`.

**STANDS: ask A2 closes as a no-defect** (the caiso-137 entry's §1). The
overlay's measure basis is already plant-level ONLINE; options (a)/(b)/(c) are
each refuted against the code. Re-verified by the correction instrument.

**WITHDRAWN 1 — the overlay never runs in a CAISO backcast.**
`caiso_scarcity_overlay` has exactly one call site,
`src/market_sim/runner.py:2085` (the FORECAST path). The calibration path
contains **zero** imports of `market_sim.runner` (AST-verified), and its only
price writer, `_system_frame`, builds `total_overlay` from **ERCOT terms alone**.
So a CAISO keeper's persisted price is the **energy-only LP dual**, the realised
adder is **exactly $0.00 in every hour**, and `caiso_scarcity_pricing=True` is a
**stored no-op** in this lane. The caiso-137 entry's "realised adder $0.14 /
$0.016 / $0.0004" and its **entire D2 E1/E2 table** are withdrawn — they priced a
spillover onto a backcast LMP the mechanism cannot reach. (Corroborated: the
keeper's min zonal price is exactly −$26.001 in 2,774/4,251/2,771 hours; a
uniform positive adder would break that exactness. caiso-137 §5.1 read the
152/133/7 disagreements as reconstruction error — the correct explanation is that
the adder is identically zero.)

**WITHDRAWN 2 — there is no flat-nameplate defect.** `runner.py:993-999`
REPLACES `storage.power_cap` with the COD-ramped 2-D array before any solve, so
the overlay's third argument is already the hourly in-service cap and
`reserve_headroom` takes its `cap.ndim == 2` branch. The 1-D nameplate caiso-137
measured belongs to `scripts/run_calibration.py`'s `fleet_only` helper, which
assigns the ramped cap to a **separate local** (line 3741). The "phantom 3,049 /
3,567 / 4,317 MW", its rule-14 framing, the "codebase disagrees with itself"
corroboration and the rule-25 ERCOT scope note are all withdrawn. *Lesson: a
claim about what a call site passes must be traced from the call site, never
inferred from a reconstruction helper that reproduces the same LP inputs by a
different route.*

**WHAT THIS LEAVES — sharper than what it removes.** CAISO has **no
scarcity-pricing mechanism in the backcast lane at all**: the in-LP co-opt is off
(and inert when armed, caiso-131 §4), the LOLP overlay is forecast-path only, and
with no `scarcity.parquet` the render falls back to `_tail_hours` on the
energy-only duals. **That is the honest reason CAISO's C3c is 0/0/0** — not an
armed overlay failing to fire, but nothing pricing scarcity in the scored lane.
It sharpens caiso-131 §4 (R is irrelevant; the code never evaluates it here) and
relocates ask A4: any future C3c work must first decide whether CAISO should
*have* a backcast scarcity mechanism — a charter question, not a tuning one.
Rule 24 `[R-REGISTRY]`: a flag that reads as armed in `run_config.json` while
being structurally incapable of changing the run is a provenance trap, and is
what produced two different wrong readings of it.

**KEEPER: no candidate, nothing promoted.** Arming any storage-tier flag is
**provably inert** in a backcast (Δ = exactly 0 on every scored series), and an
inert flag is matrix code `I`, not a keeper. Keeper remains
`2026-07-27-caiso-130-nameplate-aware`, NOT-YET, {C3a-2025, C3c}. No dashboard
registration due — rule 15 applies to completed runs; no bundle was produced.
Rule 28 duty (b): the `ordc_scarcity_overlay` CAISO cell is corrected to record
backcast unreachability. Rule 22: 2023–2025 only.

### DO-NOT-REDO (caiso-137b, binding)

Treating `caiso_scarcity_pricing` / `caiso_scarcity_import_headroom` as live in a
CAISO **backcast** (byte-identical by construction — do not solve an A/B on
them); re-proposing the flat-nameplate storage-tier defect; quoting caiso-137's
realised-adder numbers, phantom MW or D2 E1/E2 table (all withdrawn — the
`r_online` decomposition and dump-floor bound survive only as technique and as a
forecast-path characterisation); and re-deriving CAISO's 0/0/0 C3c as a
scarcity-*mechanism* failure rather than the absence of one.

Next number: caiso-138.

---

## caiso-138 (2026-07-29) — the WECC_PNW firm-hydro dump is CHARTERED, FIXED and the fix PROMOTED: the caiso-77 must-flow floor (corridor-split DMM level × TOTAL-system shape) collides with the corridor's own correct envelope and the residual — **1.09/1.71/0.97 TWh/yr, 98.6–100 % of the PNW dump** — had no outlet because the design's export sink is **deleted in every scored P1 pass** by the bridge seam's zeros-floor max-composition. Reconciliation = `caiso_firm_import_envelope_clip` (pointwise min of the two measured series, **zero new DOF**); A/B vs a **byte-identical** control passes every pre-registered gate (E1/E2 = **+0.0000**, rubric unchanged) and the node reprices **−26.00 → +40.79/+37.46/+41.83** vs measured MALIN same-hours **+52.67/+41.22/+41.77**. NEW KEEPER: `2026-07-29-caiso138-envelope-clip`

Diagnose-first per the charter; all D-gates passed on committed bytes before any
solve. Full record: `results/calibration/FINDING-caiso138-pnw-firm-dump-2026-07-29.md`
(§A–§G); instrument `scripts/probes/_caiso138_pnw_firm_dump.py` (no LP, no
solver); pre-registration `PREREG-caiso138-firm-envelope-clip-2026-07-29.md`
(committed and pushed before arm B solved). Arms registered:
`2026-07-29-caiso138-control` (byte-identical to the caiso-130 keeper on prices
and dumps, all years) and `2026-07-29-caiso138-envelope-clip` (KEEPER, owner
promotion in-session under the stated criterion; rubric NOT-YET, fail
{C3a-2025, C3c} — identical to control by construction, since the CA-side LP is
byte-identical: max CA per-zone-hour |Δprice| = 0.0000).

**The charter's central question — floor, cap, or composition — is answered
"composition", with three proven objects:**

1. **The collision (D1/D2).** Per-hour identities on committed bytes:
   `dump = firm + midC − flow`, `flow ≡ cap` in 100 % of dump hours; the α
   component (firm shaped capability > corridor cap) carries 100/99.5/98.6 %
   of the PNW dump energy. The filed 70/161/307 MW reproduces exactly on
   caiso-134's window basis (70.2/160.9/307.2). The β remainder is a
   DIFFERENT defect (dump-cost formula guards only wind/solar mc, so
   hub-priced tranches with mc < −$26 generate-to-dump: DSW 0.522/0.021 TWh
   in 2024/25, `DSW_surplus_clean`-dominated) — filed, its own lane.
2. **The P1 sink deletion (infrastructure defect, FILED, not fixed blind).**
   `pipeline/commitment.py::_bridge_floored_fleet` composes every P1-native
   bridge floor as `np.maximum(base_min_gen, zeros_floor)` — for negative-pmin
   export sinks max(−TTC, 0) = 0, deleting their absorption range from the
   scored pass. Explains caiso-132 §3's "globally inert" export bound (the LP
   was never ABLE to export — D0's census stands, its interpretation is
   corrected), and P0/P1 solve different economies. Violates the invariant
   documented at `data/fleet/arrays.py` (min_gen zeros-init block). Cross-ISO
   blast radius (generic priced-node sinks + the ERCOT/NYISO bridges through
   the same seam) — each ISO re-gates in its own lane. The NAIVE fix is
   refused for CAISO: the terminus λ sits below the measured hub in 20–57 %
   of hours (mean positive gap $1.28–8.54/MWh), so an unguarded sink U-turns
   DELIVERED firm energy out of the market, voiding caiso-77 and failing E1.
3. **Charter ask (a), answered NO at the energy scale.** The floor forces
   `level × 8760` of energy: **9.20/13.38/13.44 TWh** of PNW firm against a
   measured corridor net of **−0.55/+2.06/+4.73 TWh** (net-importing hours
   only 4.65/5.77/7.05) — the DMM RA "Imports" row is a capacity-showing
   quantity, mis-converted to a round-the-clock energy base by the unit-mean
   shape; ~1 GW-mean of phantom northern import all year, upstream fuel for
   the caiso-121/133 belly over-import. E1-adverse to shrink — handed to the
   upstream CA-supply lane, NOT armed here.

Matrix: new row `caiso_firm_envelope_clip` = K (CAISO), header re-stamped.
Rule-22 LOYO note: the mechanism carries no fitted parameter and its CA-side
effect is exactly zero in every year — nothing to overfit. Rule 20: derive
scripts untouched. Rule 24: one new `ScenarioConfig` flag, registered.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso138 §G)

Re-measuring the dump/α–β split/collision identity/forced-vs-measured energy/
U-turn set (the committed probe carries all of them); re-arming the export
sinks naively or any hub-resale sink bound beyond the stranded residual as a
CAISO lever; quoting caiso-132 D0 as "the model does not want to export";
re-deriving the PNW firm level/shape basis as a quick fix (upstream lane); and
treating the β dump as part of this lane.

Next number: caiso-139.

## caiso-139 (2026-07-29) — the caiso-138 β defect is CHARTERED, FIXED and the fix PROMOTED: the dump-cost guard was an **incomplete enumeration**, not a wrong price. Widened to its own stated domain (`dump_cost_full_offer_domain`, **zero new DOF**), the 0.531/0.035 TWh of phantom generate-to-dump tranche revenue is eliminated **exactly**, the CA-side LP is **byte-identical** (E1/E2 = **+0.0000**, max per-zone-hour |Δ| = **0.0000**), and the WECC nodes reprice from the −$26.001 dump optimum to **hub + OATT wheel + ε — the marginal delivered import offer, exact to $0.0000 in 100 % of all 212 former dump hours**. NEW KEEPER: `2026-07-29-caiso139-dump-guard-offer`

Arms `2026-07-29-caiso139-control` (`caiso139_control_A`) and
`2026-07-29-caiso139-dump-guard-offer` (`caiso139_dumpguard_B`), both
`--year 2023 2024 2025`, same pushed HEAD, arms sequential. Control is
byte-identical to the caiso-138 keeper on prices and dumps in all three years —
which also proves the flag-**off** code path byte-identical on the full solve
path. Full derivation: `FINDING-caiso139-dump-cost-blindspot-2026-07-29.md`;
prereg `PREREG-caiso139-dump-cost-offer-domain-2026-07-29.md` (pushed before
either arm solved); instruments `scripts/probes/_caiso139_dump_cost_blindspot.py`
(D-gates) and `_caiso139_dumpguard_ab.py` (gate scorer).

1. **The defect is an enumeration bug.** `build_cost_vector`'s own comment states
   the invariant — the dump price must exceed any production credit, else the LP
   generates purely to dump — but the minimum ran over
   `(wind_mc, solar_mc, −storage_eac)` ONLY. CAISO's per-hub import tranches are
   priced at their own measured hub, and Palo Verde crashes to **−$58.24/MWh**
   (2024) / −$36.26 (2025), i.e. **$3.69–32.24/MWh of pure generate-to-dump
   profit**. D2 attributes it exactly in BOTH directions: every dump hour carries
   a producible offer below −dump_cost (5/5, 175/175, 8/8, 24/24), no dump hour
   lacks one, and 2023 — the one year with no row below the guard — has no dump.
2. **D3 made E1/E2 analytic, not estimated.** CA zones never dump (0 zone-hours,
   all years), min CA λ −20.000 sits above −dump_cost, and the corridor is at cap
   in **100 %** of every affected hour. Dump's reduced cost is `dump_cost + λ`,
   so raising it leaves a column already at its lower bound. The caiso-134 SSB
   replacement-ladder was not invoked and **could not be** — its trigger
   (corridor flow moving) cannot fire when the flow is cap-bound throughout.
3. **The rejected alternative (rule 14).** Flooring the import offers at
   −dump_cost — the `virtual_bids._inc_offer_floor` treatment — is refused: it is
   "representation-exact" for PJM only because it never binds there (min INC rung
   ≈ −$1.3 vs a ≈ −$27 floor), whereas here it would rewrite measured hub prices
   (−58.24 → −26.00). The guard was what was wrong, so the guard is what moved.
4. **The `pmax > 0` producible mask is load-bearing.** Export sinks sit BELOW the
   producible minimum (2024: −58.2407 vs −58.2387); their negative price is a
   willingness-to-pay on a WITHDRAWAL, not a production credit, so dropping the
   mask would inflate the guard off a credit that does not exist.
5. **Cross-ISO settled ex ante (rule 25).** Every keeper's own fleet, all three
   years: ERCOT −2.84/+1.40/+1.40; MISO/NEISO/NYISO/PJM +1.40. No non-CAISO
   keeper is within **$24/MWh** of the guard, so the repair is CAISO-only in
   effect. PJM's virtual layer is settled analytically and more strongly than by
   measurement: DEC rows are `pmax 0` (outside the mask) and INC rungs are
   ALREADY floored at `min_credit + ε ≥ −dump_cost + ε`. Ships flag-gated
   default-off anyway (ISO-agnostic LP infrastructure), registered in the
   cache-key drop list so the pinned default stays `603c2498bf71d21d`.
6. **Latent break caught.** `solve_dispatch` has an explicit signature, and
   `pipeline/solve.py`'s non-warm path plus the archived P2 path reach the LP
   through it with the same `dispatch_kwargs` mapping — an armed run on either
   would have raised on an unexpected keyword instead of solving.

**Promotion (owner grant in-session 2026-07-29: "Promote").** Keeper shard
`frontend/data/backcast/keepers/CAISO.json` → `2026-07-29-caiso139-dump-guard-offer`;
`status/CAISO.js` rebuilt (`build_status.py --iso CAISO`, NOT-YET). Rule 21
[R-DOF]: the DOF ledger is carried forward VERBATIM from the caiso-138 keeper
(11 entries, 9 residual) — this mechanism adds none. `legitimacy_diagnostics.json`
regenerated on the new bundle: its **`gates` block is IDENTICAL** to the prior
keeper's; the only movement is sub-0.25 pp `load_share` (the phantom dumped
energy leaving the denominator) and a 2 MWh float shift in `hydro_min_flow` —
every verdict unchanged.

Matrix: new row `dump_cost_full_offer_domain` — CAISO `K`, every other ISO `I`
measured-inert ex ante. Rule-22 LOYO
note: no fitted parameter and a CA-side effect of exactly zero in every year —
nothing to overfit. Rule 20: derive scripts untouched. Rule 24: one new
`ScenarioConfig` flag, registered.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso139 §G)

Re-measuring the β dump / its per-node-per-tranche split / the offer-below-guard
attribution / the CA-dump & CA-λ census / the cross-ISO guard census (the
committed probe carries all of them); re-proposing the offer-floor repair as a
CAISO lever (rule 14, §D); dropping the `pmax > 0` producible mask; re-testing
the widened guard in ERCOT/MISO/NYISO/NEISO/PJM as a fit lever (measured inert
ex ante in all five); quoting the remaining WECC node-vs-hub gap ($4–5/MWh) as a
pricing defect (it is exactly the published OATT wheel + ε, verified to $0.0000
in 100 % of hours); and treating the P1 export-sink deletion seam as settled by
this lane (untouched — still FINDING-caiso138 §D's cross-ISO lane).

Next number: caiso-140.

## caiso-140 (2026-07-30) — C3a-2025 DIAGNOSED TO CLOSURE ARITHMETIC and the solve KILLED at the D-gates: the "belly over-price" is a Sep–Dec ALL-low-price-hours residual (belly band = only 26 % of the gap); its supply state is EXACTLY ledgered on the keeper's own demand identity — gas ride-through **+1,477 MW (74 %)** of the Sep–Dec belly import wedge, water/PS **+793 MW** (the caiso-130 hydro-gap basis missed the model's own ~700 MW PS belly pumping 10×), reality curtailment −453 MW — and the D3 walk-down shows the belly λ PINNED by a **2.7–3.0 GW economic-import parity plateau**, so the only admissible floor instrument delivers **less than half** the −$0.31 the gate needs. NO SOLVE, NOTHING ARMED

Charter: close C3a-2025 (the last CAISO gate with a diagnosed defect and no
selected mechanism), diagnose-first on the caiso-139 keeper's committed
sidecars, D1–D4 kill-before-solve. The gates fired at D4 — the caiso-129
pattern, executed as designed. Keeper `2026-07-29-caiso139-dump-guard-offer`
UNCHANGED (NOT-YET, fail {C3a-2025, C3c}); no dashboard registration due
(rule 15 applies to completed runs — the caiso-134/135 disposition).

Instruments (committed, no LP, no solver):
`scripts/probes/_caiso140_belly_supply_state.py` (D1 month×hod residual map +
D2 exact ledger + drill-down) and `scripts/probes/_caiso140_d3_walkdown.py`
(counterfactual λ(S) from the sidecars + the fleet-only offer reconstruction).
Full record: `results/calibration/FINDING-caiso140-belly-supply-state-2026-07-30.md`.

1. **D1 corrects the "belly" shorthand.** Sep–Dec carries +2.35 of the +2.90
   (caiso-131 reproduced), but the belly band 10–15 is only **+0.75 (26 %)**;
   overnight (+0.72) and the 7–9/16/22–23 shoulders (+0.95) carry as much. A
   belly-scoped candidate reaches ≤ 38 % of the residual by construction.
2. **D2 is an EXACT ledger, not an estimate.** The keeper's demand is BUILT
   from measured supply (caiso-80), so (model import − measured import)
   decomposes per-hour into named CA supply wedges with **closure 0.0**.
   Sep–Dec belly 2025: import wedge +1,989 MW = gas +1,477 (74 %) + water/PS
   +793 (40 %) + other +332 − solar −453 (reality curtails; the model does
   not) − battery −131. Overnight: gas +886 of import +1,133. The water wedge
   is **+769/+803/+793 MW in all three years** — the caiso-130 disclosure
   (−92/−58/−83) compared conventional hydro against the PS-blind 930 WAT
   cell; like-for-like the model's unrestrained 2,078 MW PS fleet pumps ~700 MW
   through the belly (caiso-127 §B2's "entirely unrestrained arbitrageur").
3. **D3 is the reachability map.** Defect hours split ~45 % corridor-priced
   (DSW group bound, dual mean −$18.4 when bound) / ~55 % parity-priced (CA λ
   = WECC_DSW node λ EXACTLY, spread p50 0.00). Economic import mean 2,705 MW
   (p50 3,038); at S = 3 GW of added CA supply, 51–61 % of hours never leave
   the plateau. λ(S) upper bounds (elastic absorption disclosed): belly
   S=1,500 → C3a −0.313; the FULL measured wedge (~2.3–2.6 GW belly + 0.9
   night) → −0.5..−0.7 vs the −0.31 needed. E1/E2 structurally favourable
   (supply additions only move λ down). **Every partial lever ≤1.5 GW is
   arithmetically insufficient — instrument-agnostic.**
4. **D4 KILLS the solve.** The measured ride-through mixture (62–74 % of
   evening-full-config CC plant-days ride the belly at p50 0.67–0.78; 20–29 %
   drop below 0.30) refutes any class-flat/fleet-quantile floor (caiso-135 §3
   reality test); the only admissible form — per-plant own-p25, the
   mustrun_p25 family, stable across years (cap-wtd belly 0.356/0.331/0.337,
   night 0.579/0.604/0.554) — adds only **+757/+304 MW** (2025 belly/night,
   0.68 CAMPD match) ≈ **−0.13 C3a upper bound, less than half the gate**.
   The water half has NO in-repo hourly instrument (930 WAT PS-blind, 923
   monthly, LESR battery-only). Bridging by a tuned value is rule 21/24
   forbidden → STOP and file.
5. **Asks filed, not built:** A1 the per-plant ride-through conduct floor
   (reconciled INTO the RA bridge level, rule 19) — only jointly with A2/A3
   and under an owner rule-13 grant; A2 DATA INTAKE: an hourly PS /
   conventional-hydro split (OASIS/CDEC) to ground the +793 MW water wedge;
   A3 the P1 export-sink seam (caiso-138 §D, owner-chartered) — this session
   prices it: the plateau is that seam wearing a price (2023 defect hours:
   reality imported +50 MW; the model 3,226).

Matrix (rule 28): `cc_mustrun_per_plant` CAISO `.` → **R** and
`netload_drag_floors` CAISO `U` → **R**, both ex-ante with FINDING citations;
CAISO column header re-stamped. `check_mechanism_matrix.py` integrity OK.
Rule 22: 2023–2025 only.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso140 §G)

Re-measuring the residual map / exact ledger / walk-down / conduct p25s /
kill-check (both probes carry them); belly-only scoping for C3a-2025; quoting
the caiso-130 hydro-gap basis as the water state; using 930 WAT as a
conventional-hydro anchor without the PS caveat; class-flat or fleet-quantile
committed-CC loading floors; the per-plant own-p25 floor as a STANDALONE
C3a-2025 closer; re-testing single-component supply additions ≤1.5 GW against
C3a-2025 (the plateau kill is instrument-agnostic).

Next number: caiso-141.

## caiso-141 (2026-07-30) — the A2 water-state intake is **WALLED**: no public source separates CAISO pumped-storage from conventional hydro at hourly grain for 2023–2025 — Helms (1,053 MW, 50.7 % of the fleet) and Eastwood (199.8 MW) have **no public hourly telemetry anywhere**, and every hourly hydro series CAISO or EIA publishes is the same single PS-NET EMS feed. NO INTAKE, NO MECHANISM, NO SOLVE — filed per the charter's stop-if-walled discipline

Charter: FINDING-caiso140 §E ask A2 — ground the +793 MW Sep–Dec belly water
wedge with a measured HOURLY PS / conventional-hydro instrument, then (only
if it lands) run the joint A1+A2 D-gates for C3a-2025. It does not land.
Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED (NOT-YET, fail
{C3a-2025, C3c}); the joint D-gates were NOT run and the A1 rule-13 grant
question was NOT posed (both were conditioned on the split being measured).
Full record: `results/calibration/FINDING-caiso141-water-intake-walled-2026-07-30.md`;
instrument: `scripts/probes/_caiso141_water_source_survey.py` (a NETWORK
probe — re-runs every check against the live endpoints and prints
unchanged-WALL / CHANGED per source).

1. **Six source families, each checked to a verdict on live bytes:**
   EIA-930 carries a `PS` fuel category but **CISO files 0 rows** under it;
   Today's Outlook fuel mix (the Renewables Watch successor) prints
   **negative belly hydro** (−414 MW, 2025-10-15) and matches 930 `WAT` at
   corr 0.95 / |diff| 287 MW hour-ending-aligned — the SAME net-of-pumping
   EMS feed, not a split; the Outlook storage page is battery-only; **CDEC
   has ZERO hourly sensors at Courtright/Wishon (Helms) and Shaver
   (Eastwood)** — PG&E/SCE don't report hourly telemetry; the EIA-930 sub-BA
   route is demand-only by schema; OASIS `ENE_SLRS` is system totals and no
   OASIS queryname publishes per-fuel actuals. Daily-grain publications (DWR
   SWP / USBR CVO daily ops) and monthly 923 fail the hourly requirement by
   design.
2. **The partial (DWR-only) instrument doesn't resolve the fleet.** The
   CDEC-instrumentable DWR share is 824.8 MW = 39.7 % (itself gappy — San
   Luis hourly storage was out 2022-07→2024-01 — and needing an AF→MWh
   derivation); the uninstrumented Helms+Eastwood share is **1,252.8 MW =
   60.3 %**, and Helms alone can pump ~900 MW — larger than the whole
   ~700 MW signal under adjudication. A bound did fall out: the net feed
   shows ≥400 MW of real net fleet pumping in some belly hours — a bound,
   NOT a split (the caiso-140 PS-caveat clause governs).
3. **Owner decision filed (§C):** (i) A3 export-sink seam first (caiso-138
   §D — the wall removes its only competing data-first route); (ii) obtain
   the non-public hourly data (CAISO settlement-quality / PG&E plant
   records — owner-level action); (iii) accept C3a-2025 as
   diagnosed-unclosed (the nyiso-97 C3c disposition). Re-open conditions are
   mechanical and probe-checked (§E): CISO starts filing 930 `PS`/`BAT`, a
   CAISO PS trace appears, PG&E/SCE telemetry lands in CDEC, or non-public
   data arrives.
4. **Matrix (rule 28): no cell changes** — no mechanism proposed, tested, or
   adjudicated; no `ScenarioConfig` field, no curated datatype, no
   solve-affecting change. Rule 22: no out-of-training year touched.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso141 §G)

Re-surveying the six source families without a §E trigger (run the probe
instead); intaking a DWR-only hourly instrument as the fleet adjudicator;
deriving an hourly PS shape from monthly 923 / the model's own arbitrage /
any assumed allocation (the forbidden fabricated shape); quoting the
negative-hydro bound as a split; re-posing the A1 rule-13 grant standalone.

Next number: caiso-142.

## caiso-142 (2026-07-30) — the A3 export-sink seam: the **infrastructure defect is REAL and FIXED** (flag-gated, default-off, surgical) but the **mechanism cannot be a C3a-2025 lever on ANY basis** — an export sink is an **absorption column**, so restoring it can only weakly **RAISE** every zonal λ while the charter needed the import-parity plateau pushed **DOWN**. The export leg is priced **below** the plateau's own marginal-import λ by exactly the corridor's OATT wheel + 2ε (DSW defect p50 **+$4.002**, night **+$0.002**), and the **simultaneous interface group binds in 0 of 26,280 corridor-hours**. D3 KILL before solve — NO ARM, NO A/B, keeper unchanged

Charter: FINDING-caiso140 §E ask A3, selected by the owner after caiso-141
walled A2 — restore the P1 export outlet the RA-bridge seam deletes
(FINDING-caiso138 §D) on a principled sink basis and re-price the C3a-2025
plateau. Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED (NOT-YET,
fail {C3a-2025, C3c}); no LP built, no solver called, no bundle, no dashboard
registration due. Full record:
`results/calibration/FINDING-caiso142-export-sink-seam-2026-07-30.md`;
instrument: `scripts/probes/_caiso142_export_sink_basis.py` (§A exercises the
real bridge functions on the reconstructed 2025 keeper fleet; §B–§F read
committed bytes only).

1. **The seam, reproduced on the real functions, and FIXED (§A).**
   `_bridge_floored_fleet` composes `max(base_min_gen, bridge_floor)` over a
   zeros-initialised floor, so both export sinks
   (`WECC_PNW_export_MALIN` −4,800 / `WECC_DSW_export_PALOVRDE` −10,623) went
   to `min_gen = 0` and were pinned off in every scored P1 pass — the exact
   failure `arrays.py::_compose_min_gen_floors` guards against in its own
   zeros-init. New gate `caiso_p1_export_sink_seam` (**default off**,
   byte-identical, cache-key registered, threaded from the CAISO RA path only
   so no other ISO's recipe shifts) restores the range: **2 rows differ, 0
   others**, availability byte-identical, and **17,520 spurious
   `MECH_RA_MUSTOFFER` sink row-hours → 0**. Two further consequences filed:
   P0 and P1 solve structurally different economies, and the RA bridge's own
   decommit screen credits up to **15.4 GW** of export absorption the scored
   pass cannot use.
2. **The mechanism is the WRONG SIGN, structurally (§C — the kill).** An
   absorption column (`pmin ≤ P ≤ 0`) can only ADD demand; permitting `D ≥ 0`
   of withdrawal at a node is a `+D` RHS move and an LP's balance dual is
   nondecreasing in its RHS, so **every** CA λ moves weakly UP. C3a-2025 is a
   +$2.90 **over**-price, so the chartered effect is unreachable by
   construction — the basis question is **moot for the chartered effect**.
   Both escape channels measured dead: (a) direct — the plateau's λ *is* a
   delivered-import price and the export leg sits below it by
   `wheel + carbon + 2ε` every hour (`DSW_surplus_clean` marginal in 85–91 %
   of defect hours → p50 +$4.002; the wheel-free `DSW_overnight_clean`
   marginal overnight → +$0.002), in-the-money in only **0.4/8.3/8.4 %** of
   defect hours; (b) indirect — releasing shared interface headroom needs the
   **simultaneous** group to bind and it binds in **0 h** of all three years
   (max │dual│ 0.00; flow p50 3.9–4.7 GW vs limit 16.0–16.5 GW) while every
   congested regime is bound by the corridor's OWN ATC group.
3. **E1 ceiling if armed anyway (§D).** C3a moves **+9.379/+7.860/+3.865**
   (as-built `hub−ε`) and **+7.745/+5.698/+2.139** (netback) — every basis
   worse. Zero fitted values swept: there is no value to sweep. The measured
   export envelope (already each corridor group's `limit_dn`) removes ~95–99 %
   of the DSW U-turn exposure (DSW export capability is **0 MW in
   7,201/7,172/7,260 h**), leaving the PNW leg where the caiso-138 §E U-turn
   lives.
4. **An admissible third basis EXISTS and half of it is already armed (§E).**
   Bound = `min(link TTC, measured export-direction envelope)` — armed today
   via `caiso_corridor_flow_limit`. Price = `hub − wheel_out − ε` — a
   zero-DOF symmetry correction (the as-built leg wheels out for FREE while
   the import leg on the same corridor pays the OATT charge); **specified, NOT
   built**. This also **un-confounds caiso-132 §3**: its "provably inert"
   export-envelope census was measured on a fleet that could not export at
   all; the bound was armed and correct with nothing to bound. Its R verdict
   stands on the stronger §C sign argument.
5. **Cross-ISO exposure MEASURED, and the caiso-138 §D list CORRECTED (§F).**
   Only **CAISO and NYISO** are exposed (absorption row AND a P1-native bridge
   armed). **ERCOT is NOT** — its keeper builds **0 interchange rows**, so the
   shared composer has no absorption row to collapse. NYISO IS (one −600 MW
   sink + `nyiso_gas_commitment_bridge` armed in
   `2026-07-29-nyiso-99-demandfix`) and enters `U` for its own lane (rule 25).
   PJM/MISO/NEISO carry 40/32/3 absorption rows but arm no such bridge —
   latent.
6. **Matrix (rule 28):** new row `caiso_p1_export_sink_seam` (CAISO **R**,
   ERCOT **I**, NYISO/PJM/MISO/NEISO **U**); `caiso_corridor_export_path`
   note corrected per §E. **C3a-2025 is now DIAGNOSED-UNCLOSED with an EMPTY
   in-model lever queue** — A1 standalone < half the gate, A2 walled, A3 the
   wrong sign; what remains is owner-level (non-public hourly PS data, or
   accept it as diagnosed-unclosed per the nyiso-97 C3c disposition). Rule 22:
   no out-of-training year touched.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso142 §H)

Proposing ANY export/absorption mechanism as a fix for a model **over**-price
(the sign argument covers every price basis, bound, corridor, and "surplus
export"/"wheel-out" variant — state the sign before proposing); quoting the
plateau as "the export-sink seam wearing a price" (caiso-140 §C bullet 3's
mechanism claim is **WITHDRAWN**; its arithmetic stands); re-measuring the
no-trade band, wheel table, marginal-rung identification, group-binding
census, E1 ceiling, export envelope or cross-ISO census (run the probe);
re-testing the shared-headroom release channel in any form; re-deriving the
admissible sink basis; naming ERCOT in the export-sink blast radius;
re-opening A1 on the grounds that A3 landed.

Next number: caiso-143.

### caiso-142 ADDENDUM (same session, owner grant) — the seam arm SOLVED and **NOT PROMOTED**: the restored outlet is **node-level RESALE, not export**, so caiso-138 §E was right and the §I "the link bound retires it" reasoning is **WITHDRAWN**

Owner grant 2026-07-30 ("if structural integrity improves but gates regress that
may still be a keeper") turned the arm live. Prereg
`PREREG-caiso142-export-sink-seam-2026-07-30.md` pushed and the scorer
`scripts/probes/_caiso142_arm_gates.py` committed **before** the arms landed.
Arms `2026-07-30-caiso142-control` / `2026-07-30-caiso142-seam-sink-live`
(bundles `caiso142_control_A` / `caiso142_seam_B`, `--year 2023 2024 2025` one
invocation each, sequential, same `basis_sha 9e393a9`).

1. **P2 FAILS — the decisive gate.** B's export energy exceeds the corridor's
   measured export-direction envelope in **4 of 6 corridor-years** (PNW 2024
   10.030 vs 9.722 TWh; PNW 2025 7.040 vs 6.352; DSW 2023 2.033 vs 1.552;
   DSW 2024 2.207 vs 1.659), and the sink transacts in
   **99/1,463/734/1,422/1,393/948 CLOSED-envelope hours** — while the
   corridor-group limit violation is **0.0000 MW**.
2. **Why: it is RESALE, not export.** In those hours the net corridor **link**
   flow is **≥ 0 in 100.0 %** of hours (PNW p50 exactly 0.0 MW) while same-node
   import tranches inject ~2,100 MW and the sink absorbs ~1,800 MW; the node
   identity `import_inject + sink = link_flow` holds to **0.0002 MW**. A sink
   trading against injections at its OWN node is invisible to every link and
   group constraint, so the pmin=pmax firm must-flow block is U-turned out of CA
   and booked as hub resale — **exactly FINDING-caiso138 §E**, now CONFIRMED.
   **§I is WITHDRAWN**: `limit_dn` bounds the net LINK flow, not the sink's
   withdrawal, and reading it as the sink's bound was a topology error.
3. **Cost.** PNW delivered flow collapses **1,067→311 / 1,402→263 / 1,462→668
   MW** mean; C3a rises **+3.401/+4.172/+2.649** (inside the pre-registered
   ceilings, so P4 held); **C3a-2024 leaves the ±10 % band (+8.00 % →
   +20.06 %)**; and the scored fail set swaps a **load-bearing** gate for a
   supporting one: **{C3a, C3c} → {C3a, C3b}** (C3b price-shape PASS→FAIL; the
   C3c FAIL→PASS is phantom-resale price inflation entering the tail, NOT
   scarcity formation — caiso-137b: CAISO has no scarcity mechanism in the
   scored lane).
4. **P3 passed as written but is NOT a structural win.** PNW corridor net │err│
   9.90→3.28 / 10.22→0.24 / 8.07→1.12 TWh — achieved through the same phantom
   channel (a phantom import cancelled by a phantom export), which rule 1
   [R-STRUCT] forbids as reaching the right number through a mechanism that is
   not real. The prereg's P3 was too weak to separate them; recorded, not
   argued away.
5. **Control integrity EXACT (P6).** Arm A: max │Δprice│ = 0, max │Δdump│ = 0 vs
   the committed keeper in all three years / 7 zones, D-1 rows bit-identical,
   and determination/governance/fail set reproduce the keeper's — which also
   proves the seam fix's flag-OFF path byte-identical on the full solve path.
6. **Disposition.** **Keeper UNCHANGED** (`2026-07-29-caiso139-dump-guard-offer`).
   The seam fix stays in the code, **default-off**. Both arms registered
   (rule 15). Matrix row `caiso_p1_export_sink_seam` stays **R**, now with a
   solved-A/B citation. What a future arm needs first, in order: (a) a
   **NODE-level** net-interchange export constraint (`model/lp/rows.py:1416`
   machinery) bounded by the measured envelope — without it no sink bound is
   enforceable; (b) the re-based export price (measured PNW netback
   −3.56/−8.30/−7.40, DSW +3.69/+4.39/+4.49 vs the raw hub; `hub − ε` is the
   SOURCED WEIM/EDAM basis, so the defect is its LEVEL not its provenance);
   (c) only then the caiso-138 §C firm-block energy overreach, whose phantom
   import the sink is laundering.
   **⚠ CORRECTED by caiso-143 (below): (a) does not exist and (b) is not
   derivable, so the order is just (c).** (a) is algebraically redundant with the
   corridor group's `limit_dn` and no LP row of any granularity can make a sink
   sound while the must-flow block injects at the same node (non-convex soundness
   set); (b) is unidentifiable without a fitted value on PNW and **wrong-signed on
   DSW**, where `hub − ε` in fact **under**-prices the outlet by ~$4.4.

### DO-NOT-REDO (addendum, binding)

Re-arming the export sink on ANY price basis or bound before a **node-level**
export constraint exists (§J: link/group limits cannot bound same-node resale;
**caiso-143 strengthens this to: never, since no such constraint exists**);
citing `limit_dn` / the measured export envelope as the sink's bound; quoting
this arm's C3c FAIL→PASS as scarcity progress; quoting its PNW corridor-net
improvement as structural gain.

Next number: caiso-143.

---

## caiso-143 (2026-07-30) — **both** prerequisites the caiso-142 arm named are REFUSED at the design gate. The node-level export constraint is **algebraically redundant** with the corridor bound already armed — and worse, a **sound** export sink is **NOT LP-REPRESENTABLE**: the soundness set is non-convex, its tightest linear surrogate is infeasible while the must-flow block forces 27.2 TWh, and its convex hull permits exactly the resale it would forbid. The export price re-basis is **not identifiable without a fitted value** (and `hub − ε` **under**-prices DSW by ~$4.4, correcting caiso-142 §I). NO SOLVE, NO ARM, **NO NEW FIELD**, keeper unchanged

**Keeper UNCHANGED:** `2026-07-29-caiso139-dump-guard-offer` (NOT-YET, fail
{C3a-2025, C3c}). Full record: `FINDING-caiso143-node-export-constraint-2026-07-30.md`;
instrument `scripts/probes/_caiso143_node_export_gates.py` (no LP, no solver).

1. **D1a — the chartered row is REDUNDANT, not weak.** Every priced per-hub
   corridor node has `load_share = 0.000`, exactly **one** link out and **zero**
   links in, and its solved `slack` = `dump` = **0.0000 MW in every hour of every
   year in BOTH committed bundles** (keeper and `caiso142_seam_B`). Its energy
   balance is therefore the exact identity `Σ_g P[g,t] ≡ link_flow[t]`, so a row
   bounding the node's net export interchange is **the same linear combination**
   as the corridor group's bound — which is already `limit_dn` ==
   `measured_corridor_flow_envelope(direction="export")`, **max diff 0.000000 MW**
   over all six corridor-years. caiso-142 §J measured the consequence from the
   other side: net link flow ≥ 0 in **100.0 %** of the resale hours, i.e. the row
   is slack in exactly the hours D1 asked it to bind. (The cited machinery,
   `rows.py:1416`, is also a **monthly** net-throughput band, not an hourly
   directional bound.)
2. **The channel's origin is the must-flow block, not the sink.** Only **2 of 9**
   interchange injection rows are price-insensitive — `PNW_hydro_base`
   (**11.668 TWh** forced) and `DSW_solar_PV` (**15.564 TWh**), floored at
   `min_gen = pmax × availability` by the caiso-77 self-schedule injector. Every
   economic tranche costs `hub + wheel + ε` against the sink's `hub − ε`, so
   buy-to-resell loses `wheel + 2ε` (wheels $2/$4/$5/$6) — **an all-economic node
   cannot resell at all, whatever the sink's bound.**
3. **D1c — the one non-redundant linear form is refused for a stronger reason.**
   A **gross** absorption bound (`S ≥ −envelope`, a column bound) does pin the
   sink to 0 in the closed hours, but leaves resale in **31.7–51.4 %** (PNW) /
   **7.4–39.8 %** (DSW) of transacting hours — exactly the hours where the forced
   block alone equals or exceeds the corridor's measured export capability
   (`F ≥ E` and `I_A ≥ E` coincide to 0.1 pp in all six corridor-years, so the
   residual is *entirely* the must-flow block). In PNW 2024/2025 the net-flow
   floor is **positive** (+67.6 / +46.4 MW): the corridor stays a net importer at
   full permitted absorption. And it would make the pre-registered **P2 gate —
   the only gate that detected the defect — pass by construction**, which is
   rule 1 [R-STRUCT] in its sharpest form.
4. **D2 — arm B's own committed bytes corroborate §J.** From `class_hourly`'s
   signed `import` class: the sink transacted in **5,022/6,284/5,137**
   corridor-hours while the seam was a **net exporter in only 1,546/981/409**
   (**30.8 / 15.6 / 8.0 %**).
5. **D3 — the bounded arm still leaves the C3a-2024 band.** Apportioning arm B's
   realised move by the absorption a closed-hour bound removes: **+2.296 /
   +2.648 / +0.957** $/MWh, against C3a-2024's remaining **$0.69** headroom —
   **3.8×**. **D4: zero fitted values.**
6. **The price re-basis is NOT derivable.** Measured export-hour spread
   (`actual CAISO RT − raw hub`, real net-export hours): PNW p50
   **−3.56/−8.30/−7.40** — a **$4.74** across-year range against the import
   basis's **$1.25**, a **$7.70–10.48** season/depth cell range and a 2023 sign
   flip (winter +5.80 vs summer −3.49); DSW p50 **+3.69/+4.39/+4.49** — stable
   ($0.80 range) but the **wrong sign**. *Honest counter-evidence recorded:* the
   import basis was read off a distribution with a **comparable IQR**
   (9.6–28.2), so dispersion alone is no objection; instability, congestion
   structure and sign are. **This corrects caiso-142 §I part 2 / PREREG-caiso142
   §0.4:** `hub − ε` over-prices **PNW** but **UNDER**-prices **DSW by ~$4.4**,
   so "over-prices on **both** corridors" is wrong and a DSW re-basis would make
   the sink *more* aggressive. A hub-priced sink also cannot reproduce **62–72 %**
   of reality's DSW export hours at any level (CA clears *above* Palo Verde
   there) — those exports are contractual, not price-driven.
7. **The deeper result — no such constraint exists.** Soundness
   (`−S ≤ max(0, −flow)`) is **non-convex**: `flow = +2,100 / S = 0` and
   `flow = −500 / S = −500` are both sound, their midpoint
   `flow = +800 / S = −250` is **resale**. An LP feasible region is convex, so no
   rows at any granularity express it; the exact condition is a disjunction
   (MIP — forbidden); its tightest linear surrogate `−S ≤ −flow` reduces via the
   node identity to `F + I_econ ≤ 0`, **infeasible** while `F > 0`; and its convex
   hull contains the resale points.
8. **Disposition — the dependency INVERTS.** No code change, **no
   `ScenarioConfig` field**, no cache-key entry (a flag for a non-existent
   mechanism is dead code, rules 24/26). caiso-142 §J's prerequisite order
   (1) node constraint → (2) re-basis → (3) firm elasticity is corrected to:
   **(a) caiso-138 §C firm-block elasticity — the only real prerequisite;
   (b) then re-examine whether any sink is wanted, using the net bound already
   armed** — because with `F = 0` the resale channel is precluded by the
   **objective** (§B's wheel arithmetic: buy-to-resell always loses), so nothing
   is left to constrain. *(Not because the surrogate becomes usable: at `F = 0` it
   collapses to `I_econ = 0`, which would forbid legitimate imports too.)* caiso-138 §E's refusal is re-confirmed a second time, now as a
   **model-class impossibility** rather than a measurement outcome. New matrix row
   `caiso_node_export_constraint` (CAISO **G**); `caiso_p1_export_sink_seam` and
   `caiso_corridor_export_path` notes corrected.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso143 §H)

Proposing a node-level (or any) LP constraint to make an export sink sound (§F:
non-convex, surrogate infeasible, hull permits the resale — covers hourly,
monthly, node, link, grouped, net and gross forms); citing `rows.py:1416` as the
machinery for a directional export bound (it is a monthly band, and a node net
bound is redundant); arming a gross absorption bound at the measured envelope (it
makes P2 pass by construction while ~half the resale persists); re-basing the
export leg off the measured export-hour spread (unidentifiable on PNW,
wrong-signed on DSW); saying `hub − ε` over-prices the outlet on "both
corridors"; re-measuring any of §A–§F; reading arm B's per-corridor flows from its
bundle (its `network_*`/`unit_hourly_*` sidecars are gitignored — caiso-142 §J is
the binding per-corridor record).

Next number: caiso-144.

---

## caiso-144 (2026-07-30) — lever-queue item 1 (the owed in-LP co-opt test) is **DISCHARGED EX ANTE**: the builder the queue said to complete is **already complete in source**, and on the caiso-139 keeper's own committed bytes the completed design never goes short in any hour of any year — **exactly inert, DO NOT SOLVE**. The caiso-137b overlay charter is **ANSWERED NEGATIVE by measurement** (timing overlap with reality's tail ≤ 1/90 hours). The actual C3c tail is a **winter-morning fuel/cold-snap tail** the model already prices at its armed daily-spot SRMC ceiling. **C3c's in-model queue is EMPTY on every route; both blocked gates now sit on owner-level dispositions.** NO SOLVE, NO ARM, NO NEW FIELD, keeper unchanged

**Keeper UNCHANGED:** `2026-07-29-caiso139-dump-guard-offer` (NOT-YET, fail
{C3a-2025, C3c-2023/24}). Full record:
`FINDING-caiso144-coopt-dormancy-c3c-frontier-2026-07-30.md`; instrument
`scripts/probes/_caiso144_coopt_dormancy_gates.py` (no LP, no solver — reads
the keeper bundle's committed hourlies, the committed actual RT LMP series,
the raw OASIS AS_REQ CSVs, and the design constants from source).

1. **The queue premise was stale.** `_caiso_design` already carries the
   storage RS columns (ASSOC SOC gate) and the hydro pergen membership
   (`CAISO_HYDRO_RAMP10_FRAC` backfill) — "issue #1492 design constraints 2/3,
   completed" in its own docstring. Only Regulation stays walled as a build
   (no forward-derivable requirement series), and it is *measurable* (OASIS
   AS_REQ `RU_REQ_MIN_MW`), which is all the bounding needs.
   `docs/multi-iso/caiso-reserve-coopt.md` §gaps re-synced to source.
2. **§B dormancy proof, no solve.** At the keeper's solved dispatch the
   completed design's requirement (`max(MSSC 2,240 MW, 6 % load)`) is covered
   with strictly positive family-level slack in EVERY hour: T2 (+hydro) min
   **+854 / +1,485 / +2,114 MW** (2023/24/25), thermal-only T1 min +285 with
   **0 short hours in every year**, and the max-measured-RegUp sensitivity's
   only 2 sub-zero hours (Aug-16-2023 evening, −346/−58 MW) carry
   **2.6–3.0 GW** of excluded storage-RS headroom. Storage is excluded from
   every supply tier, so each slack is a strict lower bound. Costless reserve
   columns + strictly positive shortfall penalties ⇒ every optimum of the
   armed LP has zero shortfall, and with strict family slack the balance rows
   price zero — prices/volumes are the keeper's. C3c contribution: exactly 0
   hours. Matrix `energy_reserve_coopt` CAISO **U→I**, `reserve_pergen` CAISO
   **U→I**; header re-stamped (caiso138→caiso139, missed at promotion).
3. **§C the decisive cross-check.** In reality's RT >$200 hours (47/35/8) the
   completed pool is slack by **+1,568 / +1,632 / +8,310 MW minimum**
   (means ~10 GW). No reserve co-optimization at any completion level can
   price reality's scarcity hours while the model's own reserve state there
   is GW-deep — the rule-19 in-LP owner question is closed on state, not
   granularity.
4. **§D overlay charter answered NO.** The forecast-path LOLP overlay
   reproduced on the keeper's bytes with `r_online` deliberately UNDER-stated
   (adder over-estimated): settlement >$200 in 151/71/48 hours — but
   overlapping the ACTUAL tail in **1/47, 0/35, 0/8**. The model-tight hours
   (Apr–Nov) are not reality's tail hours; wiring the overlay closes nothing
   and invents a mis-timed tail (2025 would flip its small-count PASS toward
   an invented-tail FAIL). Backcast lane keeps NO scarcity overlay;
   forecast-lane `K` untouched.
5. **§E what the tail is.** Winter-morning dominated: Jan 24/47 (2023, the
   citygate blowout; hod 6–9), Jan 26/35 (2024, the national freeze), 8
   Jan/Mar/Apr mornings (2025). Model max-zonal λ there: mean $112/$123/$50 vs
   actual RT mean $310/$283/$326. With `caiso_citygate_spot_level` +
   `caiso_citygate_flow_date` both armed the model already prints the measured
   daily-fuel SRMC ceiling ($150–181 at Jan-2023's $16–18/MMBtu); the wedge
   above is the probabilistic/administrative RT premium the MISO/NEISO C3c
   ledgers already name — now with CAISO's own hour-level corroboration.
6. **Disposition map (§F).** C3c-23/24: in-model queue EMPTY on every route
   (offer rungs caiso-131 §10; reserve tiers §B/§C; overlay §D; fuel grain
   §E). Live: **A3** (SoCalGas OFO declaration-record intake, unfunded — the
   one path to an unfitted C3c-2024 trigger; re-verified absent from
   `data/raw/`) and **A4** (owner ledger as ACCEPTED MEASURED-INPUT
   LIMITATION, MISO/NEISO precedent, 0/3 budget used). C3a-2025 untouched
   (caiso-142/143 state). Ledgering C3c alone leaves C3a-2025 as the sole
   NOT-YET blocker.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso144 §G)

Solving any CAISO backcast A/B on `energy_reserve_coopt`/`caiso_reserve_coopt`
at any completion increment (re-open only if a future keeper's committed
hourlies show the §B slack approaching zero — the probe re-runs in seconds);
proposing any backcast-lane scarcity-overlay wiring for CAISO; re-deriving the
C3c tail as summer-evening scarcity; fuel-grain work aimed at C3c.

Next number: caiso-145.

## caiso-145 (2026-07-30) — **OWNER DISPOSITION of both blocked gates: CAISO is CALIBRATED-WITH-CAVEATS.** With the in-model lever queue EMPTY on every route for C3c (caiso-144) *and* for C3a-2025 (caiso-141/142/143), the owner ADOPTED caiso-131 **A4** for C3c-2023/24 and the caiso-141 **A2 data wall** for C3a-2025 as ACCEPTED MEASURED-INPUT LIMITATIONS. Three ledger entries written to the keeper's attestation; determination **NOT-YET → CALIBRATED-WITH-CAVEATS** (2 of 3 non-protective ledgered slots, 0 of 1 protective, **0 FAILs**). NO SOLVE, NO ARM, NO NEW FIELD, NO CELL VERDICT CHANGED — keeper, config and bytes all unchanged

**Keeper UNCHANGED:** `2026-07-29-caiso139-dump-guard-offer` (bundle
`results/calibration/caiso139_dumpguard_B`). This is a **disposition, not a
lever**: no LP was built, no solver called, nothing armed, no `ScenarioConfig`
field added, no bundle produced, and no mechanism-matrix cell verdict changed.
The change is **scorer-only** — the exceptions ledger in the existing bundle's
`calibration_attestation.json` — so the verdict re-derives from committed bytes
and every earlier keeper re-scores in place.

### The decision (owner, put at session open per the disposition charter)

Both questions were posed before any work, with the standing alternatives
(adopt / hold / fund the intake). Both were answered **adopt**:

| gate | disposition | basis |
|---|---|---|
| **C3c-2023/24** | ADOPT caiso-131 §9 **A4** ledger | caiso-144 §C/§D/§E; MISO `miso101` + NEISO `neiso61` precedent |
| **C3a-2025** | ADOPT ledger on the **A2 wall** | caiso-141 (walled), caiso-140 §D (A1 short), caiso-142 §H / caiso-143 (family rejected on sign) |

### What was written

Three entries in `calibration_attestation.json` `exceptions`, ERCOT-76
`"ADOPTED LEDGER (owner, 2026-07-30 …)"` format extended with the MISO/NEISO
`metric`/`classification` keys, **per-year** as the rubric matches them:

1. **`price_tail` 2023** — model 0 h vs RT actual 47 h. Hour-set decomposition
   in the entry (caiso-144 §E): 24/47 in January (hod peak 6–7 AM, 16/47 in
   hod 6–9 — the Dec-2022/Jan-2023 citygate blowout), 12 Jul–Aug evenings,
   rest scattered singles; model max zonal λ $181 (mean $112) vs actual RT max
   $907 (mean $310).
2. **`price_tail` 2024** — model 0 h vs RT actual 35 h. 26/35 in January (the
   national freeze / MLK storm), 4 in July; model max λ $155 (mean $123) vs
   actual max $897 (mean $283); LOLP-overlay overlap with these hours **0**.
3. **`price_mean` 2025** — model $38.14 vs RT actual $34.39 = **+10.9 %**
   (band ±10 %, so 0.9 pt beyond band); 2023 (+3.2 %) and 2024 (+8.0 %) PASS
   on the same basis, so the caveat is **2025-only**.

Both C3c entries share one reason block citing the MISO Scarcity Pricing White
Paper (Mar-2024 §3.2.1) probabilistic-RT anatomy — a real ISO's tail price is
an administrative/probabilistic construct over 10–30 min net-load and outage
uncertainty, not an emergent marginal-cost outcome — plus CAISO's own
hour-level corroboration: **§C** 1.6–10.5 GW of deliverable reserve slack in
reality's own RT>$200 hours (storage RS excluded, so a strict lower bound),
**§D** the over-stated LOLP adder overlapping that tail in ≤1 of 90 hours over
three years, **§E** the winter-morning fuel/cold-snap tail already priced to
the armed daily-spot SRMC ceiling ($150–180 at Jan-2023's measured
$16–18/MMBtu, with `caiso_citygate_spot_level` + `caiso_citygate_flow_date`
both armed; observed model max zonal λ there $181). The C3a entry cites the caiso-141 wall (Helms 1,053 MW + Eastwood
199.8 MW = **60.3 %** of the PS fleet with no public hourly telemetry; every
public hourly hydro series is the same PS-NET EMS feed), A1's arithmetic
shortfall (≤ −0.13 of the −0.31 needed), and the export/absorption family's
sign refusal.

### Verdict change (`scripts/calibration_verdict.py`, re-run on committed bytes)

```
NOT-YET                                  →  CALIBRATED-WITH-CAVEATS
C3a mean LMP            FAIL             →  CAVEAT [ledgered]  (2025, ACCEPTED MEASURED-INPUT LIMITATION)
C3c price tail          FAIL             →  CAVEAT [ledgered]  (2023 + 2024, same)
grade_summary: fails 2, ledgered 0       →  fails 0, ledgered 2
budget: protective 0/1, non-protective ledgered 2/3
```

C1/C2/C3b/C4/C6/C7/C8 all unchanged and passing. One non-protective ledger
slot remains.

### Artifacts updated (all committed)

- `results/calibration/caiso139_dumpguard_B/calibration_attestation.json` —
  the three ledger entries (`free_parameters` verified byte-unchanged; the DOF
  ledger is untouched because no free parameter was added). `governance` takes
  one **additive, dated appendix** to `attested_by`: the caiso-139 promotion
  record still reads "fail set {C3a-2025, C3c} unchanged, NOT-YET", which was
  and remains a correct statement about *that A/B's* pre-registered P2 gate —
  it is left **intact**, with the appendix recording that the determination has
  since changed with no change to the run's bytes. Rewriting another session's
  attestation to match a later verdict is not a repair; dating it is.
- `.../metrics.json` — regenerated by the scorer itself
  (`calibration_verdict.py --write-metrics`), never hand-edited.
- `frontend/data/backcast/keepers/CAISO.json` — the stale
  "so the rubric is unchanged: NOT-YET, fail {C3a-2025, C3c}" tail removed
  from `note`; new `disposition_note` records the adoption, the evidence and
  the two owner-funded intakes that could reopen either caveat.
- `frontend/data/backcast/status/CAISO.js` — rebuilt (`build_status.py --iso
  CAISO`), now reads `CAISO:CALIBRATED-WITH-CAVEATS`.
- `docs/codebase-site/data/mechanism-matrix.js` — header stamped with
  caiso-145; `gates.CAISO` rewritten from two blockers to the two ledgered
  caveats. **No cell verdict touched** (no mechanism tested), no other ISO's
  column touched (rule 25).

### Standing limits on this disposition

- Neither caveat is **ever** closable by an offer adder, scarcity adder,
  haircut or any value tuned to the residual (rules 1 `[R-STRUCT]` /
  13 `[R-MEASURED]`). A ledger records a limit; it does not license a fit.
- The only routes that reopen either are **owner-funded intakes**, both
  unfunded at adoption: the **SoCalGas OFO declaration record** (C3c — the one
  path to an unfitted C3c-2024 trigger) and **non-public hourly pumped-storage
  data** (C3a).
- The caiso-131 §8 interaction still binds: no C3c mechanism may later be
  re-opened that would spend C3a-2025's negative headroom. This ledger does
  not license one.
- **CALIBRATED-WITH-CAVEATS is a rubric determination, not the rule-22
  calibration-complete marker.** No marker was written for CAISO in this
  session, so every out-of-training year (2022, 2019, ≤2021, H1-2026) remains
  quarantined for CAISO — solve, scoring and registration alike. Writing that
  marker is a separate owner act.

### DO-NOT-REDO (new, binding)

- **Re-litigating either ledgered caveat as an open mechanism lane.** Both are
  adjudicated ACCEPTED MEASURED-INPUT LIMITATIONS on owner disposition with
  the in-model queues measured empty; a successor proposing a C3a-2025 or
  C3c-2023/24 lever must first present **new evidence against a named
  caiso-140/141/142/143/144 DO-NOT-REDO cell**, not a new framing of a closed
  one.
- Carried forward unchanged: every DO-NOT-REDO in FINDING-caiso144 §G,
  caiso-143 §H, caiso-142 §K, caiso-141, caiso-138 §G, caiso-137b §6,
  caiso-131 §10.

## caiso-146 (2026-07-31) — the CT class was **mispriced by eGRID's plant-average ANNUAL heat rate**, and CAISO's own CAMPD artifact says so **one-sidedly**: 41 of 43 plants cheaper, cap-weighted **−10.7 %**. Armed as a single-flag rule-14 swap with **zero fitted parameters**, it moves CT_PEAKER **26→42 / 10→15 / 11→19 %** of actual while every criterion verdict holds and the protective C7 number with the least headroom **improves**. **NEW KEEPER: `2026-07-31-caiso146-ct-heat-rates`.** Also: the heat-rate route to caiso-119 R4 is **closed by measurement**, and the outgoing keeper's committed bytes are found **not to reproduce at HEAD**

**Keeper `2026-07-29-caiso139-dump-guard-offer` → `2026-07-31-caiso146-ct-heat-rates`**
(CALIBRATED-WITH-CAVEATS both sides; 0 FAILs; the **same** two owner-adopted
caveats carried forward unchanged in substance — no new caveat, no new slot).
Records: `results/calibration/FINDING-caiso146-measured-ct-heat-rates-2026-07-31.md`,
`PREREG-caiso146-ct-heat-rates-2026-07-31.md` (committed+pushed **before either
arm solved**, `abaa952`). Arms: `2026-07-31-caiso146-control` /
`2026-07-31-caiso146-ct-heat-rates`. Lever queue §5.2 item 6, cell `U` → `K`.

**The defect.** eGRID publishes ONE plant-average ANNUAL heat rate per plant and
`eia860._rows_to_generators` hands it to every combustion turbine. For a peaker
that is wrong twice: an annual average blends startup fuel and part-load tails
into the number that sets the offer, and at a mixed facility it is not even the
right technology's rate. **Glenarm (422) is defect #2 in the flesh** — 4
`CT_PEAKER` units (138.4 MW) **and** 2 `CC_REGULAR` units (84 MW) on one eGRID
10.3895, where CAMPD tags GT3/GT4 `Combustion turbine` and GT5 `Combined cycle`.

**The artifact (STEP 1, no LP).** 43 plant rows, **all `flag=="ok"`** — zero
excluded by the physical band. Coverage **76.8 % of class capacity but 99.9 % of
the class's own metered CAMPD CT energy** (8.015/8.025 TWh): the 90 uncovered
plants are the Part-75 reporting boundary (median **2.2 MW**, **zero** metered CT
energy — nothing to swap in), and there is **no adverse selection** (covered
cap-wt eGRID HR 10.819 vs uncovered 11.004). **CAISO's direction is ONE-SIDED
and that differs from both precedents** (NYISO: errors both ways; PJM: net
**+**0.229): 41 plants / 5,649 MW cheaper vs **2 / 198 MW dearer**, cap-wt
**−1.159 MMBtu/MWh (−10.7 %)**, gen-wt −0.884. Largest moves are the lowest-CF
peakers, exactly as the start-fuel defect predicts (Grapeland 15.5477→9.5563,
Center 14.5803→9.5251).

**Result.** CT_PEAKER **1.088→1.727 / 0.423→0.634 / 0.272→0.455 TWh** vs actual
4.128/4.326/2.374 — **26→42 %, 10→15 %, 11→19 %** — inside the prereg's
predicted +0.1–0.8 TWh band. Displaced: CC_REGULAR −0.399/−0.130/−0.093
(94→93 / 94→93 / 90→90 % of actual, a ~1 pp cost against a 5–16 pp gain), ST_GAS
(better in 2 of 3 years), imports. Every criterion verdict **unchanged** vs a
same-HEAD zero-delta control. C3a improves in all three years (+3.6→+2.8,
+8.2→+7.8, **+11.3→+11.0 %**); **C3c BIT-UNCHANGED** (0 h both arms).
**Protective gates improve:** C7 CT_PEAKER `profile_r` 0.903/0.951/**0.837** →
0.885/0.936/**0.864** — 2025, the outgoing keeper's most exposed number at 0.036
of headroom and the prereg's flagged risk, **rises**; `cv_ratio`
2.635/2.048/2.087 → 1.613/1.805/2.172 moves *toward* measured off-peak
variability; C8 forced share 0.0032/0.0104/0.0012 → 0.0016/0.0055/0.0007 against
a 0.15 cap. All six pre-registered K-gates pass, including **K6**: excluding the
Delano broken-meter row the class move keeps its sign at 80/84/66 % of size.

**caiso-119 R4 ANSWERED, and the heat-rate route to it CLOSED.** R4 attributed
CT_PEAKER to "priced out" and set the guardrail that *marking peaker offers down
until 4 TWh appears is rule-1/13 forbidden*. This lever clears it by
construction — the magnitude is set by the meter, not the gap, and the prereg
predicted the gap would **not** close before the solve. All three plants R4 named
rise (Sentinel 0.227→0.360, Walnut Creek 0.223→0.329, Panoche 0.063→0.088 in
2023). **A mispriced offer was PART of the defect but only part:** fully
re-priced, the class still reaches only 42/15/19 %, so the residual 2.4–3.7 TWh
is **not** a heat-rate defect — the same conclusion nyiso-89 reached, derived
independently on CAISO's data.

**Ledger discipline (prereg §8).** C3a-2025 moved **0.3 pp** (+11.3→+11.0 %),
inside the 1.0 pp materiality trigger fixed **before** the solve, so no
leave-one-year-out re-scoring was required. The movement is **reported, never
tuned toward**, and is **not** offered as justification; the lever was selected
off the §5.2 queue on caiso-119's CT finding and closes **neither** ledgered
caveat. The two caveats remain the **owner's** act of 2026-07-30 (caiso-145),
re-stated against this bundle with magnitudes re-measured. **CAISO still holds
NO rule-22 marker; 2023/2024/2025 only.**

**OPEN ITEM — the outgoing keeper's committed bytes no longer reproduce at
HEAD.** The zero-delta control diverged from the committed caiso-139 keeper by
up to **2.1/1.7/3.2 GW** on a class-hour, netting a **CC_REGULAR ↔ import** swap
of +0.45/+0.46/+0.85 TWh at **identical total generation** (3 dp) and CA λ
+$0.19/+$0.06/+$0.14. **It does NOT touch CT_PEAKER** (+0.007/0.000/0.000), so
the A/B — an order of magnitude larger, with both arms at the same HEAD — is
unaffected; this is exactly why a same-HEAD control was solved rather than a
keeper-relative comparison (neiso-69 precedent). Promotion **re-bases CAISO onto
HEAD** so the committed bytes reproduce again. Cause **unidentified**: 15 commits
touched `src/market_sim/` between `fa9971b` and `db02071`; bisecting needs full
solves, so it is filed rather than guessed.

**Cross-cutting side finding, deliberately NOT acted on.** Sub-6.0 MMBtu/MWh
loaded **meter** hours bias the *shared* CT derive low in **every** ISO measured
— CAISO 3.46 % of loaded hours / **+0.114**, NYISO 2.45 % / +0.122, PJM 1.55 % /
+0.081, MISO 0.30 % / +0.014 MMBtu/MWh energy-weighted
(`scripts/probes/_caiso146_hourly_hr_integrity.py`). An hour-grain screen would
move **three committed keepers'** inputs, so it needs its own charter, not a
CAISO calibration session (rules 24/25).

**Housekeeping.** §5.2 queue item 5 was stale — it asked for
`unit_outage_short_windows` to be derived for CAISO, but that cell was already
`I` (caiso-136: CAISO's coal class is CEMS-invisible, Argus Cogen absent from
CAMPD entirely, both derives return 0 windows). Struck with its reason and
re-open condition. The old item 6 is split: the CHP half survives as the new
item 7 (`measured_chp_heat_rates`), and `nuclear_unit_availability` is added as
item 8.

**DO-NOT-REDO (caiso-146).**
- **Do not re-derive `campd_ct_heat_rates_CAISO.csv` against a residual** (rule
  24 — source-data change only, and the commit must cite it).
- **Do not add a CAISO-scoped heat-rate multiplier, band or exclusion.** The
  error is plant-specific source noise; no scalar substitutes, and a CAISO-only
  screen on a shared derive is a rule-25 breach.
- **Do not re-open "CT_PEAKER is priced out" as a heat-rate question** — it is
  measured and answered. Successor levers must be obligation-keyed with a cited
  D-4 window, never an offer markdown sized to the gap.
- **Do not treat the hour-grain meter screen as a CAISO lane** — it is
  cross-cutting and touches three committed keepers.
- **Do not quote the C3a improvement as evidence for this mechanism**, and do
  not propose it as a C3a-2025 or C3c lever.
- **The keeper-reproducibility drift is not this lever's defect** and must not be
  re-litigated as one; if investigated it is a reproducibility lane over
  `fa9971b..db02071` scoped to the CC ↔ import margin.
- Carried forward unchanged: every DO-NOT-REDO in FINDING-caiso144 §G,
  caiso-143 §H, caiso-142 §K, caiso-141, caiso-138 §G, caiso-137b §6,
  caiso-131 §10, and the caiso-145 bar on re-litigating either ledgered caveat.

Next number: caiso-147.

---

## caiso-147 (2026-07-31) — CAISO's CHP was priced by a **steam-credited** eGRID rate that the model then multiplied by an **off-registry hand factor**, and the derive built to fix it was **blinded by that very factor** — excluding 59 of 65 rows / 3,089 of 3,186 MW, i.e. precisely the population the mechanism exists to correct. Gate fixed ISO-generically before any solve; the swap is **two-sided and opposite** (CC_CHP +19.6 % dearer, CT_CHP −14.6 % cheaper) and moves **CC_CHP 117/120/108 → 108/108/102 %** of actual with **no class moving away from actual**. **NEW KEEPER: `2026-07-31-caiso147-chp-heat-rates`**

Lever: mechanism-matrix §5.2 CAISO queue **item 7**, `measured_chp_heat_rates`
(cell `U` → `K`). Prereg `PREREG-caiso147-chp-heat-rates-2026-07-31.md`,
committed and pushed at `b1b5e5f` **before either arm solved**. Full evidence:
`results/calibration/FINDING-caiso147-measured-chp-heat-rates-2026-07-31.md`.

### What the lever is, and why CAISO's version differs from MISO's

For a cogen, eGRID does not publish total fuel per net MWh — it first removes
the fuel it attributes to useful thermal output, so `PLHTRT` is a
**steam-credited** rate, not the rate the machine turns fuel into power. The
measurement puts eGRID's own removal back on the same net denominator:
`heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN`. No gross-to-net factor is involved
— which is exactly what blocked the CEMS route (`FINDING-miso98` §6.1). Zero
fitted parameters.

**CAISO is the first hand-factor ISO to take this lever.** It sits in
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`, so its incumbent was *not* eGRID's
credited rate (MISO's case) but that rate × an **off-registry hand factor**
(× 1.8 for a sub-8.0 CT_CHP, `max(× 1.15, 6.3)` for a sub-6.0 CC_CHP) — one
universal topping factor that caiso-128 §3 measured **over**-correcting CAISO
CT_CHP by +40 % while five ISOs sat 12–62 % **under**. So this is a rule-21/24
retirement of a hand number as well as a rule-14 `[R-ACCURATE]` accuracy swap.

### The derive defect (found by no-LP probe BEFORE any solve)

The shipped derive gave CAISO **14 `ok` rows / 1,117 MW**, `basis_mismatch = 65`.
The `_BASIS_TOL` gate asks *"is the incumbent this eGRID row, or a boundary
repair / bin fallback?"* but compared against the **shipped** rate — which in a
hand-factor ISO **is** credited × 1.8 / × 1.15. Measured: CT_CHP median ratio
**1.800**, CC_CHP **1.150**, the constants exactly. Loading the fleet twice
partitions it: **59 of 65 rows / 3,089 of 3,186 MW excluded by the hand factor
alone**; the remaining 6 rows / 96.5 MW are the genuine repairs the gate exists
to catch. **The gate was excluding precisely the population the mechanism exists
to fix.**

Fixed by comparing at the **replacement seam** (after the eGRID join and
boundary repairs, before the hand factor — which is what
`apply_measured_chp_heat_rates` actually overwrites, since it runs first and
hands the hand factor its `skip_ids`). New default-`True`
`apply_chp_steam_credit_correction` kwarg on `load_fleet_from_csv`. Zero
parameters introduced; the 6 genuine mismatches still fail; **MISO re-derives
identical on every applied value** (still 6,732 MW, exactly miso-99's figure).
**This defect is latent in PJM too** — the other hand-factor ISO, never derived.

### The artifact

92 (plant, class) rows / 4,668.6 MW; **30 applied / 2,371.8 MW**. CC_CHP 11/21
rows at 67.2 % of class capacity but **100.0 % of the class's own metered CAMPD
energy**; CT_CHP 19/71 at 28.2 % / 35.4 % (thin **and** adversely selected —
covered cap-wt credited 7.167 vs excluded 6.377 — stated as a limitation, not
claimed as identification; the class is 0.7 % of generation). CEMS validation
**13/13 within 1 %, median 1.00000** — better than MISO's 19/22. 44 rows /
1,914 MW correctly excluded as `not_unfired_topping` (median `thermal_share`
0.598 vs the 0.50 EPA-envelope ceiling; the rate they would otherwise take has
median 14.52, max **58.4** MMBtu/MWh). **Two-sided and opposite:** CC_CHP cap-wt
6.779 → 8.108 (+19.6 %), CT_CHP 11.935 → 10.196 (−14.6 %).

### Result (single flag, vs a same-HEAD zero-delta control)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **CC_CHP** | 9.025 → 8.353 · 117 → **108 %** | 8.126 → 7.337 · 120 → **108 %** | 7.754 → 7.317 · 108 → **102 %** |
| CC_REGULAR | +0.504 · 93 → **94 %** | +0.649 · 93 → **95 %** | +0.387 · 90 → **91 %** |
| CT_PEAKER | 42 → 43 % | 15 → 15 % | 19 → 20 % |
| CT_CHP | +0.029 · 73 → 74 % | +0.012 · 76 → 77 % | +0.002 · 115 → 115 % |

Total generation moves only +0.003 / +0.006 / +0.004 TWh (~0.002 % of a ~210 TWh system) — pure reallocation, **no material
class moves away from actual**. All three pre-registered predictions confirmed,
including **P2** (CT_CHP barely moves despite getting cheaper, because 95–97 % of
it is already pinned at its `chp_steam` floor) — which independently corroborates
the D-2 floor attribution. Mechanism verified **live first**: max |Δ| on a CHP
class-hour 229.8/278.9/144.7 MW vs a 50 MW inertness floor.

**Every criterion verdict unchanged.** Determination **CALIBRATED-WITH-CAVEATS**,
0 FAILs, the **same 2 of 3** ledgered slots (owner's caiso-145 act carried
forward, magnitudes re-measured, **no new disposition**), protective 0/1. C3c
**bit-identical** (0 h both arms). C3a-2025 **+11.0 → +11.2 %**, a 0.2 pp
**adverse** move inside the prereg's 1.0 pp trigger — reported, never tuned
toward, and not a reason to revert an accurate input (rules 1/14).

**Protective gates unchanged** where they bind: CT_PEAKER C7 `profile_r`
0.885/0.936/0.864 → 0.881/0.934/0.864, C8 forced share 0.0016/0.0055/0.0007 →
0.0016/0.0054/0.0007 vs a 0.15 cap. **C7 shape improves markedly on the repriced
classes**: CT_CHP `profile_r` 0.817/0.801/**0.393** → 0.959/0.937/**0.852**,
CC_CHP 0.968/0.969/0.988 → 0.983/0.982/0.989.

**Stated rather than buried:** CC_CHP's `chp_steam` forced share **rises**
0.435/0.470/0.461 → 0.557/0.629/0.592 — the arithmetic consequence of the
correction working (the class contracts toward a fixed measured steam floor as
its economic tranche is priced out of merit). No gate engaged; CHP is C8-exempt
by class.

### Framing correction, binding on all future CHP sessions

`CC_CHP`/`CT_CHP` are exempt from **both** C7 (`D1_GATED_CLASSES`) and C8
(`D2_EXEMPT_CLASSES`) by **explicit class list** — stated rationale
"host-steam-pinned duty" — **not** by the 2 % materiality floor. A CHP class
above 2 % of load is **still ungated**. CHP D-1/D-2 numbers are diagnostics,
never a passed gate; the binding protective gates belong to the classes that
absorb the displaced energy.

### DO-NOT-REDO (new, binding — full list in FINDING-caiso147 §G)

1. **Do not re-derive `chp_power_only_heat_rates_CAISO.csv` against a residual**
   (rule 23 — only a new eGRID vintage, and the commit must cite it).
2. **Do not add a CAISO-scoped CHP heat-rate multiplier, band or exclusion.**
   `_MAX_THERMAL_SHARE`, the physical bands and `_BASIS_TOL` are definitional.
   The hand factor this retired is exactly the kind of number not to reintroduce.
3. **Do not re-open `not_unfired_topping` as a coverage lever** — those 44 rows
   are boiler-first cogens reaching 58.4 MMBtu/MWh; the gate is physics.
4. **Do not quote CHP C7/C8 as passed gates** (see the framing correction above).
5. **Do not treat C3a-2025's +0.2 pp as a defect to close.** It is the mechanical
   consequence of pricing a class correctly, inside the pre-registered trigger,
   and C3a-2025 remains the owner's ledgered caveat on the caiso-141 A2 wall.
6. All prior CAISO DO-NOT-REDO sections remain binding and untouched.

## 2026-07-31 — CAISO — caiso-148: `nuclear_unit_availability` PROMOTED (matrix §5.2 item 8, `U` → `K`) — measured per-reactor daily NRC availability replaces the fleet-month smear on 100 % of the nuclear fleet; S2 closes in every year, every criterion verdict unchanged

**Runs:** `2026-07-31-caiso148-nuclear-availability` (KEEPER) +
`2026-07-31-caiso148-control-zerodelta` (same-HEAD zero-delta control, no
attestation). Prereg `PREREG-caiso148-nuclear-availability-2026-07-31.md`,
committed and pushed **before either arm solved**. Evidence
`FINDING-caiso148-nuclear-availability-2026-07-31.md`.

**Ex-ante wall check first (the reason item 5 cost no solve).** The handoff
required settling whether item 8 shares the coal-only CEMS detector that made
`unit_outage_short_windows` INERT at caiso-136. **It does not, and they share no
input:** this lever reads the NRC daily Power Reactor Status report, and nuclear
units carry no CO₂ and are not CEMS reporters in **any** ISO, so CEMS visibility
is structurally irrelevant to it everywhere.

**Derive.** No source change was needed to arm CAISO — the `arrays.py` seam and
`outages.py` loader were already ISO-generic; the entire code delta is a two-row
identifier crosswalk (`Diablo Canyon 1/2 → (6099, 1/2)`). Deriver constants
frozen from ERCOT and untouched (rule 23); PJM and NYISO extracts reproduce
byte-for-byte (rule 25). Artifact: 1,886 rows / 2 reactors = Diablo Canyon 1+2
(2,240 MW, NP15) = **100 % of CAISO nuclear capacity and unit count**; 18 windows
including three refuels. Coverage 365/365, 366/366, 212/365 days (31 of 36
months).

**The five dropped 2025 months are correct, and the cause was measured rather
than assumed.** Each holds a real event whose non-event pool is already saturated
at 100 %, so the capped fixed-point cannot scale *up* to an anchor EIA-923
clipped at 1.0. EIA-930 shows CISO nuclear peaking at 2,281/2,279/2,309 MW
against the model's 2,240 MW EIA-860 nameplate — Diablo runs up to **+3.1 % above
nameplate**, so NRC-%thermal × nameplate cannot express a full-power month and
posting that level would delete real capability. Disclosed in the prereg before
the solve; in 2025 only the October U2 refuel carries measured timing.

**Independent validation.** EIA-930 CISO metered hourly, 942 covered days: r_day
**0.9807**, bias −1.8/+13.7/+20.0 MW on a 2,240 MW fleet. The nyiso-98 EIA-930
zero-block artifact was screened for and does **not** occur in CISO (23 exact-zero
hours 2023, 0 in 2024/25, vs NYISO's 1,179/380/117) — a CAISO-specific finding.

**Gates.** Build-time: G1 +0.184/+0.145/+0.133 (≥ +0.10), G2 retention
100.1/100.2/100.1 % (≥ 70 %; PJM's was negative), G3 ≤ 0.0746 % (< 0.5 %).
In-solve: R3 the overlay **binds** (4,368/3,672/2,232 h > 1 MW, max |Δ|
1,075/893/963 MW); R4 **energy-neutral** (+0.0001/−0.0240/−0.0445 %) so it posts
timing, not a level. **S2 closes in every year** — nuclear r_day vs metered
0.7873/0.8473/0.8550 → **0.9709/0.9921/0.9878**, matching the extract prediction
to four decimals.

**Result.** Every criterion verdict identical to the control; determination
**CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8**, same **2 of 3**
ledgered slots, protective **0/1**. Displacement small and on the marginal
classes (CC_REGULAR −85.6/−35.8/−13.8 GWh, imports +36.0/+31.7/+16.4, CT_PEAKER
+46.1/+2.7/+6.0). Price +$0.015/−$0.036/+$0.018 per MWh. **Binding protective
gates hold and the most exposed improves**: CT_PEAKER C7 profile_r
0.881/0.934/0.864 → 0.881/0.933/**0.866**; C8 0.0016/0.0054/0.0007 →
0.0015/0.0059/0.0007 vs a 0.15 cap. C3a max move **0.1 pp** (trigger 1.0 pp, did
not fire); C3c bit-identical. Nuclear is exempt from **both** C7 and C8 by
explicit class list, so no nuclear D-1/D-2 number is quoted as a passed gate.

**Carried item RESOLVED for CAISO:** the keeper-reproducibility drift open since
caiso-146 does **not** affect the caiso-147 keeper — the zero-delta control
reproduces the committed bundle **bit-exactly** (max |class-hour| delta 0.000 MW
all three years, CA λ identical to four decimals). caiso-147's re-basing onto
HEAD closed it for CAISO; the program-wide charter is unaffected.

**Not a reserve/MSSC test.** The handoff framed Diablo as the MSSC setting
CAISO's entire reserve requirement. Checked and **it does not hold for this
keeper**: `energy_reserve_coopt`, `caiso_reserve_coopt` and `as_reserve_formula`
are all `False` and `caiso_scarcity_pricing`'s MCL is a static 1,400 MW tariff
constant. No dynamic MSSC channel exists in this A/B; the live channels are
within-month re-timing (primary) and the scarcity overlay's `reserve_headroom`
(second-order). Do not cite caiso-148 as reserve-floor evidence.

**Open item filed, not absorbed:** a Diablo nameplate/uprate basis
reconciliation (EIA-860 net summer capacity vs licensed thermal power) would
recover 2025 coverage and is the honest fix — but it is a fleet-representation
change, outside a calibration session's scope, and likely touches other ISOs'
uprated units.

**DO-NOT-REDO** (full list `FINDING-caiso148` §G): do not re-derive the artifact
against a residual; do **not** loosen `WEDGE_TOL` / raise `SCALE_CLIP` / lift the
per-day cap to "fix" the dropped months (each would post a level the basis
under-expresses); do not cite this session on reserve/MSSC; do not re-open the
benign "0 reactor(s)" log line; do not attribute the pre-existing ST_GAS
2024/2025 D-1 FAILs to this lever; do not treat the CISO EIA-930 screen as
transferable. **CAISO still holds NO rule-22 calibration-complete marker** —
2023/2024/2025 only were solved and no marker was written. Matrix §5.2 live queue
is now items **2, 3, 4**.

## 2026-07-31 — CAISO — caiso-149: `tranche_startup_amortization` REFUSED EX ANTE (matrix §5.2 item 4, `U` → `G`) — the mechanism is the Order-825 **fast-start pricing** object and **CAISO does not have fast-start pricing**: it recovers those costs as **Bid Cost Recovery uplift settled OUTSIDE the LMP**. Separately sufficient: **92.9 % of the targeted capacity already carries a MEASURED CAISO DAM bid** plus a fuel-invariant margin **2.2×–7.9×** the candidate. NO SOLVE, NO ARM, NO NEW FIELD, keeper unchanged

**Runs:** NONE. No LP ran, no bundle was produced, nothing registered on the
dashboard (rule 15 registers *completed runs*; the caiso-136 / caiso-144
pattern). **Keeper unchanged:** `2026-07-31-caiso148-nuclear-availability`,
determination CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 free 8/8, the same 2 of
3 non-protective ledger slots, protective 0/1.

**Charter and the DO-NOT-REDO discipline.** Matrix §5.2 item 4 listed
`tranche_startup_amortization` untested in CAISO (`U`). The handoff bound this
session to read the two standing adjudications first — NYISO `R` (nyiso-96, rule
1, after a registered A/B) and ERCOT `G` (ERCOT-145, rule 19, ex ante) — and to
state what makes CAISO different from both before arming anything. Phase 0 was
run as no-LP with an explicit no-solve-closure exit. It closes: **the A/B is not
licensed.** Full record:
`results/calibration/FINDING-caiso149-tranche-startup-2026-07-31.md`; probe
`scripts/probes/caiso149_tranche_startup_phase0.py`.

**Ground 1 — rule 1 `[R-STRUCT]`, dispositive alone: the pricing rule does not
exist in this market.** The mechanism is, by its own source docstring, the
"Order 825 analogue": it amortizes a fast-start unit's start cost into the
**price-setting energy bid** so the cost reaches the LMP, and it changes nothing
else (`min_run`/`min_down` stay 0 — "bid markup only, no new UC coupling",
`data/fleet/assembly.py`). **CAISO does not have fast-start pricing**, and did
not at any point in 2023–2025; it recovers exactly those costs as **Bid Cost
Recovery**, a make-whole uplift settled outside the price — so it never enters
the energy-balance dual the model prices on (rule 4 `[R-DUALS]`). CAISO's own
Department of Market Monitoring says so twice, nine years apart:

- **FERC Docket RM17-3, 2017-02-28** — *"CAISO sets locational marginal prices
  based on marginal production costs. CAISO provides bid cost recovery payments
  made to compensate resources for any discrete commitment costs that are not
  recovered through marginal cost pricing."* (DMM opposed being required to
  adopt fast-start pricing; FERC never finalized RM17-3 as a generic rule.)
- **Body of State Regulators, 2025-01-10** — *"If energy revenues do not cover
  full startup and minimum load bid costs after being committed, unit receives
  bid cost recovery (BCR) payments"*, and on status: *"CAISO is examining the
  **possibility** of some form of FSP in the WEIM"* — a candidate enhancement
  **mid-calibration-window**, not a rule. The same deck sizes it: fast-start BCR
  was $19M/$33M/$27M in 2021/22/23 = 12/13/10 % of total CAISO BCR. It remains a
  Phase-2 Price-Formation-Enhancements item in 2026.

This satisfies METHOD step 1's independent-validation requirement: the market
monitor is independent of **both** inputs the supporting legs consume (the OASIS
Public Bid Data the offer-surface derive reads, and the CAMPD extracts the
run-length derive reads). The four `K` cells are the four ISOs that **have** the
rule — rule 25 in action, in the cleanest form the matrix has produced.

**Ground 2 — rule 19 `[R-ONE-MECH]`, sufficient alone: the rows are occupied.**
Enumerated on the keeper's own `run_config.json`. Every `_committed` tranche in
every ISO is *already* amortized by `compute_monthly_markup` at the
**unconditional** P0→P1 seam (`pipeline/solve.py:254`), flag or no flag; the
flag's marginal object is only the CT `econ*`/`peak*` and CC `peak*` extension.
Those rows carry `caiso_offer_surface_measured` (the cap-weighted medians of the
CAISO fleet's **own submitted DAM energy bids**, OASIS Public Bid Data,
carbon/VOM-netted) decomposed by `gas_offer_net_revenue_margin` (anchor 4.7964
$/MMBtu) into physical marginal HR × delivered fuel **+ a fixed, fuel-invariant
$/MWh margin** — structurally the same object an amortized start cost is:

| group | band | MW | margin $/MWh | vs candidate |
|---|---|---:|---:|---:|
| CT_PEAKER | econ_low | 3,289 | 22.16 | 5.75× |
| CT_PEAKER | econ_high | 2,964 | 22.69 | 5.89× |
| CT_PEAKER | peak | 533 | 8.42 | 2.19× |
| CT_CHP | econ_low / econ_high | 199 / 199 | 30.26 / 30.06 | 7.86× / 7.81× |
| CT_CHP | peak | 96 | 20.21 | 5.25× |
| CC_REGULAR | peak | 472 | 0.00 | — |
| CC_CHP | peak | 56 | 0.00 | — |

The candidate's own reach is **$3.85/MWh**, measured on CAISO's own CEMS: the
new rule-23 artifact `data/raw/_processed-legacy/campd_ct_run_lengths_CAISO.csv`
(`derive_campd_ct_run_lengths.py --iso CAISO`; **50 plants + a pooled ISO-class
fallback, 26,623 measured start-to-stop runs**, class median run **4.0 h**, mean
6.47, p90 10.0) crossed with the NREL class start costs the mechanism amortizes
($12.3/$24.5/$19.0 per MW) — cap-weighted **$3.85**, median $4.10, range
$0.09–9.50. **92.9 % of the 7,808 MW targeted is occupied.** The two zero-margin
rows (6.8 %) do not rescue it: `CC_REGULAR peak`'s multiplier **1.333 is the
measured DAM bid**, sitting *below* the 2.250 physical F-class duct ratio — the
CAISO CC fleet measurably offers its duct band below its own physical duct cost,
so a markup there moves the model **away** from measured conduct; `CC_CHP peak`
is registered exactly at physical and is host-steam-pinned.

**Ground 3 — rule 14 `[R-ACCURATE]`: ERCOT's reopen route is already spent
here.** ERCOT-145 could name a reopen condition because ERCOT's incumbent is a
**fitted** multiplier set: *retire the fit by measured re-identification, and the
start component then enters as one term of that identification*. **In CAISO that
re-identification already happened** — `caiso_offer_surface_measured` is it, and
its result **is** the incumbent. There is no fit left to retire, and the only
rule-19-clean form would swap a measurement for a model, which rule 14 forbids
outright. That is what makes CAISO's refusal **strictly stronger** than ERCOT's,
and why it carries **no offer-side reopen condition at all**.

**What makes CAISO different from each precedent.** *vs NYISO:* nyiso-96's
rejection was **conduct**-based (its CT fleet demonstrably does not add a start
markup to SRMC) in a market that **has** the rule — the question there was
identification, and the owner ultimately promoted it. CAISO fails the **prior**
question. *vs ERCOT:* same rule-19 regime (rows occupied, markup does not clip to
zero — CAISO is **not** in the four-keeper-ISO "sits at/below physical" regime),
but for the opposite reason: ERCOT's occupant is fitted, CAISO's is measured.

**Direction reported, and explicitly NOT the ground (rule 1).** The arm makes the
CT econ/peak bands dearer, and CT_PEAKER already sits at 1.832/0.659/0.471 TWh
against actual 4.128/4.326/2.374 (44/15/20 %) — the nyiso-96 signature from a far
worse base. Recorded so no successor mistakes the refusal for a fit argument: it
would not have licensed a rejection on its own, and would not have licensed an
arming either. It does **not** reopen caiso-119 R4, whose guardrail (a real
obligation-keyed mechanism with a cited D-4 window) is untouched — and an offer
markup is the wrong sign for R4 besides.

**Filed, not absorbed (out of scope).** `compute_monthly_markup` amortizes the
NREL start cost into the P1 bid of every `_committed` tranche **unconditionally,
in all six ISOs**. Ground 1's reasoning about BCR-not-LMP touches that seam in
principle, but it is architecture-level (the two-pass P0→P1 bid-cost structure
that *defines* P1, spec §1.6), it would move six keepers at once, and it is a
spec question rather than a per-ISO lever. Surfaced for an owner-scoped
cross-ISO charter; **do not absorb it into a CAISO lever session** (rule 25).

**DO-NOT-REDO** (full list `FINDING-caiso149` §G): do **not** propose
`tranche_startup_amortization` for CAISO again — the cell is `G` on three
independent grounds with **no reopen condition**, and the four `K` cells are not
evidence for CAISO (rule 25); do not invent a CC-peak-only scope for the flag (a
new mechanism needing its own row and identification, rule 28c — and that
incumbent is measured too); do not strip `caiso_offer_surface_measured` or the
`gas_offer_net_revenue_margin` decomposition to "make room" for the amortization;
do not re-derive `campd_ct_run_lengths_CAISO.csv` against a residual (rule 23 —
only a CAMPD data update, and the commit must cite it); do not cite this session
as evidence about the *cause* of CAISO's CT under-production; do not open the
`compute_monthly_markup` committed-row seam from a CAISO lever session. **CAISO
still holds NO rule-22 calibration-complete marker** — every read in this session
was confined to 2023–2025 and **no marker was written**. Matrix §5.2 live queue
is now items **2 and 3** only.

---

## caiso-151 (2026-07-31) — lever-queue item 2 **BUILT and PROMOTED**: the caiso-77 firm must-flow floor is now clipped at CAISO's own measured price-insensitive intertie ceiling. All four frozen derive gates PASS; every criterion verdict unchanged and both protective gates PASS, at a **pre-registered, knowingly accepted E1-adverse** cost. New keeper `2026-07-31-caiso-151-firm-selfsched`

**Keeper CHANGES: `2026-07-31-caiso148-nuclear-availability` -> `2026-07-31-caiso-151-firm-selfsched`**
(CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, same 2 of 3 ledgered
slots, protective 0/1). Full evidence:
`results/calibration/FINDING-caiso151-firm-selfsched-clip-2026-07-31.md`;
prereg `PREREG-caiso151-firm-selfsched-clip-2026-07-31.md` (committed+pushed
before either arm solved).

### The build caiso-150 specified

caiso-150 proved the defect direction-free and specified the mechanism but
deliberately did not build it. This session built it: `min_gen[t] =
min(pmax x availability[t], ceiling[t])`, the system ceiling allocated across
firm tranches pro rata by their own shaped capability so **no allocation
parameter** is introduced. It clips the **FLOOR and never the CAPABILITY** —
above the measured ceiling the import is still available, merely price-ELASTIC,
so it goes to the LP as economic capability instead of forced. **Zero new DOF**;
composes with the caiso-138 envelope clip as a SECOND pointwise min on its own
flag (rule 19).

### The derive — all four gates declared ex ante, all PASS

357 balanced trade days, 1,574,341 resource-hours, zero archive holes. The
caiso-150 corpus was gitignored and its container gone, so this is an
**independent re-fetch**.

| gate | measured | threshold |
|---|---|---|
| G1 year-stability CV | 0.042 | <= 0.20 |
| G2 LOYO level | 4.6 / 8.4 / 4.6 % | <= 25 % |
| G3 LOYO shape (288 buckets) | 19.3 / 12.3 / 18.6 % | <= 25 % |
| G4 coverage | 288 / 288 | 288 |

It reproduces caiso-150 independently: unclassifiable 94.54 % (94.91 %), swing
1.52x (1.49x), overnight 3,388-3,542 MW (3,381-3,443). Per-year levels FLAT at
3,886/4,241/3,886 MW while the DMM RA level steps 2,323 -> 3,371 — the
caiso-138 §C signature re-measured on conduct.

### The A/B

Forced totals reproduce caiso-150 §A exactly. Forcing removed
0.919/4.548/5.495 TWh (4.9/16.7/19.6 %), binding 2,006/4,068/4,469 h — within
~5 % of a prediction made on a different corpus. But only 0.042/1.099/0.628 TWh
of import energy actually **stops flowing**: the rest flows on economics, which
is the mechanism working as designed (forced -> elastic, not deleted).
Displacement is import -> CC_REGULAR ~1:1. Every criterion verdict UNCHANGED;
CT_PEAKER C7 0.881/0.933/0.866 -> 0.881/0.932/0.865, C8 far under the 0.15
peaker cap, CC_REGULAR C8 forced share FALLS.

### The cost, paid knowingly

Registered E1-ADVERSE before either arm solved, and CONFIRMED: overnight lambda
+$0.043/+$0.376/+$0.224, and because CAISO's model lambda already sits ABOVE the
RT actual the **C3a miss GROWS** +3.01->+3.06 / +8.05->+8.68 / +11.23->+11.72 %
(+0.045/+0.626/+0.494 pp). All below the 1.0 pp prereg trigger, so not built
upon — but the 2025 movement is 10x caiso-148's and lands on a ledgered caveat,
so it is stated rather than left to be found. It does NOT reopen C3a-2025.
Rule 1 governs: a structurally-correct mechanism stays in when the fit worsens,
and is never adopted because a residual moved. Rule 22 LOYO is discharged at the
derive stage (G2/G3) — there is no fitted parameter to overfit.

### CORRECTION to caiso-150 §A (and to this session's own first claim)

Adding the `D4_WINDOWS` entry for `MECH_FIRM_IMPORT` is **necessary but NOT
sufficient**: the `firm_import` row still does not appear in either arm's
`legitimacy_diagnostics.json`. The diagnostics harness scores a PLANT-aggregated
matrix keyed on CAMPD plant ids, and the intertie tranches carry `plant_code 0`
with an empty `plant_group`, so they are dropped from the `all_pids` matrix that
D-1/D-2/D-4 all score. Run D-4 on the unaggregated LP rows and the row appears
at once (firm_import, 15.4689 TWh floored, 2024, h0-23, off-window 0.000, pass).
The binding cause is the **plant-set restriction**, not the missing window.
ISO-generic (it equally hides MISO Manitoba and NYISO HQ) — **FILED, NOT
ABSORBED**; diagnostics lane.

### DO-NOT-REDO (caiso-151, binding)

* Re-deriving `caiso_intertie_selfsched_ceiling.csv` against a residual, or
  retuning any of the four frozen gates to move a verdict (rule 23).
* Re-litigating the E1-adverse cost as a rejection ground. Revisit the ROOT
  CAUSE of CAISO's over-priced lambda; do not revert the clip to recover C3a.
* Arming this clip on the caiso-138 envelope-clip flag, or replacing one with
  the other — they reconcile different objects and compose (rule 19).
* Clipping CAPABILITY instead of the FLOOR.
* Attempting the import/export split of intertie self-schedules by any route
  (caiso-150 §H carried forward; wall re-confirmed at 94.54 %).
* Quoting the midday ratio as under-forcing.
* Citing the D4_WINDOWS entry as evidence the floor is gate-visible — it is not.
* Absorbing the diagnostics-harness defect into a CAISO lever session.

Next number: caiso-152.

## caiso-150 (2026-07-31) — lever-queue item 2's only live prerequisite (`caiso-138 §C` **firm-block elasticity**): the design gate **OPENS**. The firm must-flow floor's **shape basis measures the wrong object**, proved **direction-free** against CAISO's own as-submitted DAM bids — an independent source the mechanism had never been checked against. **NO SOLVE, no arm, no new field, keeper unchanged**

**Keeper `2026-07-31-caiso148-nuclear-availability` UNCHANGED**
(CALIBRATED-WITH-CAVEATS, 0 FAILs). Nothing registered — the
caiso-136/143/144/149 pattern. Full evidence:
`results/calibration/FINDING-caiso150-firm-import-elasticity-2026-07-31.md`;
instrument `scripts/probes/_caiso150_firm_import_elasticity.py` (§A–§C, no LP
beyond one `run_year(fleet_only=True)` reconstruction).

### The lever, and why it was on-queue

caiso-143 §H inverted the export-lane dependency and left **exactly one** live
prerequisite for item 2: caiso-138 §C firm-block elasticity — is the forced firm
import injection `F` price-insensitive at all? `F` is
`inject_caiso_firm_import_selfschedule` (caiso-77), which pins both firm
tranches' `min_gen` at their **full** shaped capability in every hour.

### §A — the mechanism as built

Forced **18.856 / 27.232 / 27.989 TWh** (mean 2,152 / 3,109 / 3,195 MW) over
7,693 / 7,994 / 8,151 hours; **every** forced hour is must-flow. 2024 reproduces
caiso-143 §B's 11.668 + 15.564 TWh exactly. **`MECH_FIRM_IMPORT` is in both
`NON_THERMAL_MECHS` and `MECH_ABLATION_KEPT` and has no `D4_WINDOWS` entry** — a
19–28 TWh/yr floor invisible to the C8 forced-share budget *and* the D-4
off-window check. No gate has ever window-tested it.

### §B–§C — the independent source and the result

The floor's rule-17 declaration cites the CPUC D.20-06-028 RA import **must-offer**
obligation and "the DMM revealed self-scheduled base", but its shape comes from
EIA-930 realised **net corridor interchange** — the sum of a broadly flat
price-insensitive core and a large price-elastic economic layer. CAISO OASIS
**Public Bid Data** measures the price-insensitive position *directly* and is
independent of **both** inputs the floor consumes. Corpus fetched this session:
**374 seasonally balanced trade days, 1,618,533 (resource × hour) records.**

Direction-free result — the floor forces more price-insensitive import than
CAISO's **entire** measured price-insensitive intertie position (both directions
unsigned, plus every import bid at ≤ $0/MWh) in:

| year | hours | share | energy above ceiling | share of forced |
|---|---|---|---|---|
| 2023 | 2,094 | 23.9 % | 0.969 TWh | 5.1 % |
| 2024 | 4,132 | 47.2 % | 4.634 TWh | 17.0 % |
| 2025 | 4,284 | 48.9 % | 5.705 TWh | 20.4 % |

Concentrated **overnight (h22–h05, 2024 ratios 1.24–1.39)**, and it **scales with
the level** (5.1 → 17.0 → 20.4 % as the DMM RA level steps 2,323 → 3,371 MW while
measured conduct stays flat) — the caiso-138 §C signature re-measured on
**conduct** instead of flow.

**Two honesty limits recorded up front.** (a) **Direction is not identifiable**:
a self-scheduling resource submits no economic curve and the feed carries no
direction field, so 1,141 of 1,452 resources carrying **94.91 %** of
self-scheduled MW are unclassifiable — only the one-sided ceiling is measurable,
and the midday ratio 0.26–0.34 must **not** be read as under-forcing (midday is
exactly where CAISO export self-schedules peak). (b) **Seasonal balance is
load-bearing**: a winter-only corpus read `ss_all` 2,291 MW and nearly flat vs
the balanced 3,449 MW peaking in the evening — it would have overstated the
headline ~50 % and mislocated the peak.

### Not struck by caiso-138 §G

§G struck re-deriving the PNW firm **level/shape basis "as a quick fix"** because
the basis "is real". This is new evidence, from a source never used in this lane,
that the basis measures a **different quantity** than the mechanism claims —
rule-28a re-entry on new evidence. Nothing §G struck is reopened: no level
re-derive, no naive sink re-arming, no β-dump work. **E1-adversity is unchanged
and stated ex ante**: any reconciliation removes forced cheap overnight import,
so overnight λ rises (rule 1 governs — not a reason to reject, not a reason to
adopt before it is properly derived).

### Mechanism SPECIFIED, deliberately NOT built

`caiso_firm_import_selfsched_clip` — pointwise min of the floor and the measured
(month × hod) self-schedule ceiling. Direction-free (uses only an upper bound, so
it can only remove unsupported forcing, never add any), **zero new DOF**,
structurally the accepted caiso-138 envelope-clip pattern, and it *reconciles*
the caiso-73 shape rather than stacking on it (rule 19). Prerequisites before any
arm: its own **rule-23 frozen derive with CV/LOYO honesty gates**, a `D4_WINDOWS`
entry, a cache-key registration, and a matrix row (rule 28c). Building it in the
tail of this session would have been exactly the rushed floor rules 1/17/19 exist
to prevent.

### Filed, not absorbed (two defects found in passing)

1. **`scripts/lib/dam_public_bids/caiso.py` never expands OASIS run-length
   ranges** — it keys rows by `TIMEINTERVALSTART_GMT` alone and does not read the
   STOP columns. GENERATOR EN curves: 5,514 rows vs 12,878 true curve-hours
   (2023-01-15), 6,628 vs 14,036, 9,195 vs 18,414 — the clean datatype carries
   **43–50 %** of real resource-hours and drops exactly the **stable-bid** ones.
   `derive_caiso_offer_surface.py` groups on `(resource_seq, interval_start_utc)`
   with no hour weighting, so the keeper input `caiso_offer_surface_measured` is
   derived from a biased population. **The directional effect on the fitted band
   prices is NOT measured here** — that is the offer-surface lane's job.
   Cross-ISO by construction (ISO-generic seam).
2. **A silent keeper-reconstruction trap.** CAISO's three firm-import flags have
   no CLI flag and no top-level `meta.json` key; they reach the solve only via the
   generic override channel whose meta name is **`coal_prb_sigmoid_overrides`**
   (→ `run_year(prb_overrides=)`). A probe omitting that rename rebuilds the fleet
   with the **entire 27 TWh must-flow block absent** while every other CAISO
   mechanism still arms, so the fleet looks correct. `run_config.json` is truthful
   and `replay_keeper.py` is correct — the hazard is for probe authors.

### Matrix

New row **`caiso_firm_selfsched_floor`**, CAISO cell **`O`** (chartered, in play,
verdict not yet reached); `caiso_firm_envelope_clip`'s note cross-referenced.
Integrity check passes.

### DO-NOT-REDO (new; full list `FINDING-caiso150` §H)

Re-measuring the OASIS self-schedule ceiling, its RLE expansion, or the
direction wall; attempting the import/export split of intertie self-schedules by
any route (curve monotonicity — the population has no curve; masked-id crosswalk
— masking is the disclosure's purpose; EIA-930 correlation — it contaminates the
independence the finding rests on); quoting the midday ratio as under-forcing;
re-running on a season-biased corpus; re-deriving the PNW firm **level**;
building the clip without its frozen derive and honesty gates, or arming it on
the caiso-138 flag (rule 19); absorbing either §E defect into a CAISO lever
session.

**CAISO still holds NO rule-22 calibration-complete marker** — every read was
confined to 2023–2025 and **no marker was written**. Matrix §5.2 live queue after
this session: item 2 (prerequisite now *answered*, build pending) and item 3.

Next number: caiso-151.

## caiso-152 (2026-08-01) — the OASIS **RLE parse defect** (caiso-150 §E1, unowned since) is REAL, is FIXED ISO-generically, and its effect on the keeper's measured offer surface is **MATERIAL** — the CT_PEAKER ladder moves **+19–21 % in every net-load bin**, ~2× the deriver's own tolerance. But the corrected input **CANNOT BE SHIPPED**: the derive fails its **own G1** on BOTH arms, and the OLD (committed) code path on the deriver's OWN default corpus **does not reproduce the committed keeper artifact at all**. **NO SOLVE, no arm, no new field, keeper unchanged**

Full evidence:
`results/calibration/FINDING-caiso152-dam-bid-rle-parse-2026-08-01.md`; prereg
`PREREG-caiso152-dam-bid-rle-parse-2026-08-01.md` + the corpus addendum
`PREREG-caiso152-ADDENDUM-corpus-2026-08-01.md`, both committed and pushed
before the values they govern existed. Probe
`scripts/probes/_caiso152_rle_parse_bias.py`.

### The defect, and the fix

`scripts/lib/dam_public_bids/caiso.py` keyed every clean row by its range START
stamp and never read the STOP columns, while the datatype's schema declares the
grain as one row per masked resource × **operating hour** × product ×
breakpoint. OASIS is run-length-encoded, so every hour of every multi-hour range
was dropped — **exactly the stable-bid hours**. Raw CSV, GENERATOR EN,
2023-01-02: **18,520 rows carry 50,972 curve-hours (36.3 % carried)**, 909 of
them 24-hour holds. Full corpus: 8,761,998 ranges carry 18,306,549 curve-hours,
the old parse carried **47.9 %**, 209,483 rows are 24-hour holds.

Fixed with a shared `expand_rle()` in the `dam_public_bids` package (ISO-generic
— every ISO's DAM disclosure is RLE-encoded; CAISO is only the first registered
spec), called per row shape with that shape's own STOP column before `step_idx`.
Semantics **reuse** the committed caiso-151 expander. Verified: clean rows ==
independently counted raw curve-hours, 0 duplicate schema keys, hours confined
to the trade date; 7 unit tests; schema + rendered dictionary corrected.

### The ladder's exposure, measured with no derive

**18.0 %** of true curve-hours were charged to the **wrong net-load bin** (a
multi-hour hold was charged entirely to its range start). The old population
under-weights every tight bin by **15–16 %** relative: bin1 0.0741 vs 0.0872,
bin2 0.0530 vs 0.0630, bin3 0.0228 vs 0.0270.

### The corpus: the caiso-151 balanced sample is the WRONG corpus here

On the registered 358-day balanced corpus (fetched clean, zero holes) **both
arms failed G1 identically** — a defect firing the same way with and without the
fix is not the parse. Measured cause: this derive is a **per-resource
time-series regression**, and its bucket capacity is strongly monotone in
trade-day count (CT 414 → 1,135 → 1,297 MW at 122 / 179 / 358 days). **caiso-150
§B is not reopened** — the intertie ceiling is a (month × hod) climatology, this
is a daily regression; different estimators, different corpus requirements.
Widened to the full contiguous span (**1,095 days**, 364/366/365) and registered
in the addendum before any value on it existed.

### The parse effect: MATERIAL, entirely in CT_PEAKER

Population 29.8M → 67.0M GENERATOR EN curve rows. Thresholds are the deriver's
**own** frozen `max(0.08, 10 %)`.

* **T1 FIRES** — CT_PEAKER `econ_high` **1.055 → 0.912** (Δ −0.143, tol 0.105).
  CT `econ_low` 0.745 → 0.681 and `peak` 1.050 → 1.076 stay inside tol.
  **CC_REGULAR is unmoved** on all three bands (max |Δ| 0.051 on tol 0.154) —
  the median-robustness argument registered ex ante holds for CC.
* **T2 FIRES on ALL FOUR CT_PEAKER bins** — **+0.311 / +0.277 / +0.276 /
  +0.304** against a ~0.146 tol: a uniform **+19–21 % level shift** of the CT
  peak surface, not a re-shaping. CC inside tol in every bin.

### The blocker, and the bigger finding

**Both arms FAIL the deriver's own G1** (CT bucket ratio **0.235** old /
**0.280** new against a ≥ 0.50 bound), so it correctly withholds the consumed
JSONs. PREREG §4's third branch governs: **the lane STOPS at the derive**, the
keeper keeps its artifact, **no threshold is retuned** (rule 23).

And the OLD arm **is** the committed code path on the deriver's **own default
corpus** — yet it does not regenerate the committed artifact: CC `econ_low`
**1.544 vs 1.051**, CT bucket **1,786 MW vs 10,785**, **25 CT units vs 102**,
and **G1 FAILS where the committed artifact records it PASSING at 1.416**. So
`caiso_offer_curve_measured.json` / `caiso_offer_surface_condbinned.json` — a
LIVE keeper input — **is not reproducible from its documented source**. Gas is
byte-identical inside 2023–25 and fleet geometry round-trips exactly; what
cannot be checked is the deriver's state at derive time (repo history begins
2026-07-30, eleven days *after* the artifact) and the corpus it used (the
artifact records no manifest).

### Disposition

Parse fix **LANDS** (contract repair; rule 14 keeps it regardless). Parse effect
**MATERIAL**. **NO SOLVE spent, nothing registered** — PREREG §9's A/B is
unreachable because it needs a corrected artifact the derive refuses to produce.
Keeper unchanged (`2026-07-31-caiso-151-firm-selfsched`, CALIBRATED-WITH-CAVEATS,
0 FAILs, C1 12/12 · free 8/8, 2 of 3 slots, protective 0/1). Matrix cell
`measured_offer_surface` CAISO stays **`K`** with its evidence re-cited — the
mechanism was neither rejected nor replaced; its *input's standing* changed.

**NEW BLOCKING CHARTER, not absorbed here:** the CAISO measured offer surface
needs a **re-identification of its gas-coupling classifier** before either half
can be re-derived. Measured lead (not a diagnosis): 71 resources / 16,329 MW
clear `r ≥ 0.6` but land at slope < 4 MMBtu/MWh — physically impossible for a
thermal unit — pointing at the body-price probe (`_price_at_frac` at 35 % of a
p98-estimated capacity) landing off the SRMC body, rather than at the
thresholds.

### DO-NOT-REDO (new; full list `FINDING-caiso152` §H)

Re-running the comparison on a seasonally balanced sample (§D: it starves the
classifier and both arms fail G1 there); relaxing/re-centring/re-scoping G1 or
any of G2–G4 to make the corrected derive writable (rule 23 — the CT ratio is a
2× miss, not a threshold quibble); shipping the corrected artifact by any route
that bypasses the gate (hand-edit, OLD/NEW blend, CC-only cherry-pick, arming
the ladder off a summary CSV); re-deriving CT band levels against a price
residual to "recover" the committed values; treating caiso-150 §H as reopened
(the intertie ceiling was not re-derived, re-measured or read); re-litigating
caiso-149 §G on the strength of the CT movement; quoting any 358-day multiplier,
or either arm's absolute levels, as a measurement of CAISO conduct — only the
OLD-vs-NEW *difference* and §F's reproduction gap are results.

**CAISO still holds NO rule-22 calibration-complete marker** — every read was
confined to 2023–2025 and **no marker was written**. Matrix §5.2 live queue after
this session: item 3, plus the new offer-surface re-identification charter.

Next number: caiso-153.

## 2026-08-02 — CAISO — caiso-153: the offer-surface gas-coupling classifier IS re-identifiable — the defect is the ESTIMATOR, not the body probe; all four FROZEN gates pass, reproducibility is restored, KEEPER PROMOTED

**Runs:** BOTH arms registered — `2026-07-31-caiso153-control` (same-HEAD
zero-delta control) and `2026-07-31-caiso153-reid-b` (**NEW KEEPER**,
CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, 2 of 3 ledgered
non-protective slots, protective 0/1). Keeper
`2026-07-31-caiso-151-firm-selfsched` → `2026-07-31-caiso153-reid-b`.
Prereg `PREREG-caiso153-offer-classifier-reid-2026-08-01.md`, committed and
pushed **before any classifier value on this session's corpus existed**.
Evidence `results/calibration/FINDING-caiso153-offer-classifier-reid-2026-08-02.md`.

**Lever:** mechanism-matrix §5.2 **item 9**, opened NEW/BLOCKING/unowned at
caiso-152. Now **CLOSED**; item 3 (S2 DA/RT two-settlement) is CAISO's only
live queue item.

**The charter.** `FINDING-caiso152` §F left an ARMED KEEPER INPUT
unreproducible: `caiso_offer_curve_measured.json` /
`caiso_offer_surface_condbinned.json` could not be regenerated from their own
script and corpus (25 CT units against the recorded 102; G1 CT 0.235 FAILING
where the artifact records 1.416 PASSING), which also blocked caiso-152's
`dam-public-bids` grain correction from shipping.

**caiso-152 §I's body-probe lead is REFUTED, on measurement.** A pre-PREREG
raw-CSV check found `_price_at_frac` falls back to the first step on only
8.5 % of curve-hours, on near-flat curves — disclosed in PREREG §2 as a
partial refutation, which is why the grid got a second axis. On the frozen 3×3
(body probe × slope estimator) over the full contiguous **1,095-day** corpus,
the body axis moves the implied non-fuel adder **$4.8 and flips nothing**;
the estimator axis moves it **$25.8 and flips everything**.

**The defect is ESTIMATOR ATTENUATION.** The CA-composite citygate reaches
**$24.29/MMBtu** in January 2023 against a 2023–25 median near $3–4, so a
pooled OLS slope is levered on a few days of one month of one year and
attenuates toward zero for any resource that did not track that spike
proportionally — a different CA hub, a monthly index, a cost-verified DEB on a
lagged index — **with its correlation intact**. That is exactly the
`r ≥ 0.6` / slope < 4 MMBtu/MWh signature caiso-152 §I reported as physically
impossible for a thermal unit. All three OLS cells are inadmissible
($32.7–37.5/MWh implied non-fuel adder against a $2.0–3.5 VOM, slope p50
~6.0); all six Theil-Sen / TRIM cells are admissible ($9.6–12.7, slope p50
9.2–10.4). The sub-4-slope population falls **32 resources / 10,880 MW → 13 /
2,692 MW**.

**Selection was declared EX ANTE and is BLIND to both the derive gates and the
committed artifact** (PREREG §5): physical level-identity admissibility
applied FIRST — precisely because shrinking every slope toward zero would
otherwise win outright — then out-of-sample split-half slope stability on an
alternating-gas-rank split. Winner **`P035_TS`** keeps the INCUMBENT body
probe (`BODY_FRAC` 0.35) and changes ONLY the slope estimator to Theil-Sen: a
one-line shipped diff in `derive_caiso_offer_surface.py`.

**No gate moved.** `hr_cut` stays 8.5 and G1–G4 stay frozen (rule 23). The
**unmodified** deriver then passes all four: G1 CC 0.871 / CT 1.306 (against
0.876 / 0.235 on the incumbent), G2 PASS, G3 estimation-LOYO PASS on all six
consumed stats in every held-out year, G4 PASS.

**Two corroborations the selection rule never saw.** (1) The re-derived static
bands reproduce the COMMITTED artifact within tolerance everywhere (max Δ
+0.053 on CC peak against a 0.133 tolerance) — which **explains §F**: the
committed artifact was derived with a correctly-identified classifier and the
deriver drifted to the attenuated OLS form in the eleven days before the
repo's git history begins. (2) The **shipped** deriver regenerates the
promoted artifact exactly — reproducibility restored.

**A/B.** No `ScenarioConfig` field changed; the delta is file CONTENT, so the
arms ran sequentially with the artifacts swapped and both files hashed per
arm. CC_REGULAR ladder **+0.451…+0.688** per net-load bin, CT_PEAKER
**−0.317…−0.370**, largely offsetting (system prices +0.17/+0.22/+0.17
$/MWh). **Every criterion verdict UNCHANGED** against control and against the
caiso-151 keeper; C7/C8 PASS on both arms.

**Promoted knowing it costs fit** (rule 1 `[R-STRUCT]` + rule 14
`[R-ACCURATE]`): DA MAE +0.052/+0.060/+0.043 $/MWh on a $12.998/$8.696/$7.093
base, RT MAE +0.088/+0.102/+0.093, C3a-2025 +9.42 → +9.92 % (+0.50 pp,
load-weighted system basis, reported as PREREG §7 required and below the 1.0 pp
trigger its predecessor fixed). C3c bit-identical. It is adopted because the
incumbent classifier assigned **16,329 MW** of gas-coupled capacity a marginal
heat rate below 4 MMBtu/MWh — not because a residual moved.

**Also:** the measured offer surface gains its **first DOF ledger entry**
(identification `measured`) — it had been armed since caiso-51 with none, and
its `root_cause` records §F's defect as CLOSED. caiso-152's parse correction
ships with this keeper. **CAISO still holds NO rule-22 calibration-complete
marker**: 2023/2024/2025 only, no out-of-training year touched, no marker
written.

**DO-NOT-REDO (binding, new).** Do NOT re-test the body probe as the cause
(§B settles it across all three estimators; `BODY_FRAC` stays 0.35). Do NOT
re-rank the estimator grid with a different metric, and do NOT drop
admissibility so a lower-instability inadmissible cell wins. Do NOT move
`hr_cut` off 8.5 on the strength of the re-identified slope density — out of
scope, not examined, and G2 is the frozen test (it PASSES). Do NOT re-derive
either half against the price residual to recover the +0.05 $/MWh MAE. Do NOT
quote any OLS arm's absolute band or ladder levels as measured CAISO conduct.
Do NOT treat §D's reproduction of the committed bands as licence to chase
committed values — it is a blind corroboration, never a target. Full list:
`FINDING-caiso153` §G.

**Environment note for successors:** the `dam-public-bids` corpus is
gitignored and dies with the container; `fetch_caiso_public_bids.py` with no
arguments regenerates it in ~3 h. Background processes do NOT survive session
idle here — the fetch was reaped mid-run and had to be resumed in foreground
chunks.

## 2026-08-02 — CROSS-ISO — caiso-154: the caiso-153 OLS-attenuation defect is NOT LIVE in PJM or NEISO — the estimator family is structurally absent; the counterfactual transplant is refuted on PJM and data-real-but-admissible on NEISO; all three committed artifacts REPRODUCE; one NEW NEISO tail-sensitivity exposure filed

Adjudicates the `FINDING-caiso153` §H cross-ISO lead. **No LP; nothing
registered; no derive modified; no artifact rewritten; keepers unchanged**
(CAISO `2026-07-31-caiso153-reid-b`, PJM `2026-07-31-pjm-143b-hy-level`,
NEISO `2026-07-31-neiso-72-hy-window`). Pre-registered
(`PREREG-caiso154-xiso-ols-attenuation-2026-08-02.md`, pushed before any
estimator value on the session's corpora existed; no addendum needed).
Explicitly NOT a re-test of the adjudicated `measured_offer_surface` cells
(PJM `R`, NEISO `I`) — an input-standing audit, the caiso-152/153 class.
Rule-22 state re-verified and corrected against the handoff prompt: PJM and
NEISO each hold a `complete` marker; CAISO none; no `final` anywhere; the
holdout spend freeze is ACTIVE. Instrument:
`scripts/probes/_caiso154_ols_attenuation_xiso.py` (imports the caiso-153
core — `_fit`/`_score_resources` — parameterized by ISO, not forked).

**The verdict, in four measured layers** (full write-up:
`results/calibration/FINDING-caiso154-xiso-ols-attenuation-not-live-2026-08-02.md`):

1. **L1 structural (disclosed ex ante in the PREREG): FALSE in both ISOs.**
   No PJM/NEISO offer-surface derive contains ANY regression estimator — all
   three artifacts are per-unit median-of-daily-ratio ladders with physics
   segmentation. §H's "same family" premise was imprecise: the shared element
   is the fuel normalization, not the estimator. Neither top-of-curve surface
   is armed in its keeper; the one live artifact is the PJM midcurve.
2. **M2 counterfactual transplant of the CAISO classifier, on each ISO's own
   corpus + fuel (full refetch: PJM 36/36 months; NEISO 1,058 days — the
   committed coverage exactly).** PJM: REFUTED — every OLS body-probe cell
   admissible ($6.3–7.8 |L| vs the $20 bar), slope p50 moves <0.75 OLS→TS,
   the impossible r≥0.6/slope<4 set does NOT deflate under TS, and the
   hr-cut split misbuckets 6–11 GW of physics-CC under EVERY estimator; OLS
   costs only split-half precision (1.9–2.8 vs 0.2–0.45; 53 % of regressor
   variance sits in 11 Jan-2024/-25 days). NEISO: the caiso-153 signature IS
   data-real in miniature (slope p50 7.4–8.1 OLS → 9.4–10.2 TS; |L| ~2×
   TRIM's; the 630 MW physics-fast-start pool splits 303/327 under OLS where
   TS puts all of it ≥8.5 — the CT-bucket collapse reproduced) — but every
   OLS body cell stays ADMISSIBLE ($15.2–15.7), so the family's own bar
   would not have tripped even transplanted.
3. **M4 reproducibility (anti-caiso-152, never before run for these lanes):
   ALL THREE artifacts reproduce** — the ARMED PJM midcurve BYTE-IDENTICALLY
   (1,152/1,152 leaves), PJM top to 0.016 % and NEISO top to 0.023 % (the
   declared injected-basis rounding; the recorded fleet bundles are absent
   from the container, so the fleet-replay leg is blocked and reported).
4. **M3 tail-exclusion at the pre-registered 10 % bar:** PJM ROBUST (max
   4.8 %). **NEISO TRIPS: 4/42 consumed leaves move +10.1..+13.1 %** —
   the q0.7/q0.9 rungs of net-load bins 1–3 RISE when the 34 fuel-tail days
   are excluded (Feb-2023 arctic week + the Dec-2025 plateau, where the
   Algonquin series holds a single Wednesday $25.00 print ffilled for 28
   days). The tight-bin "fast-start wall" is attenuated LOW by
   oil-parity/capped offers divided by spike gas — the ratio analogue of
   caiso-153. Filed as a NEW unowned NEISO exposure, FILE-AND-STOP per the
   PREREG: unarmed artifact (neiso-58 dormancy stands), no keeper moved,
   actionable only through the oil-parity/DA-bid charter NEISO's frontier
   note already requires.

Matrix duties done in-session: cross-ISO header block + `measured_offer_surface`
ev/note appended for P and Q (cells stay `KKRUUI`);
`check_mechanism_matrix.py` green. Cross-reference stubs in
`docs/calibration-log/pjm.md` and `docs/calibration-log/neiso.md`.

**DO-NOT-REDO (caiso-154, binding — full list `FINDING-caiso154` §H):** do
not quote any M2 cell as measured PJM/NEISO conduct in absolute terms (only
contrasts, gate populations, confusions); do not re-run the counterfactual
grid to "select" an estimator for PJM/NEISO — nothing consumes a slope there,
and a slope-based identification would be a NEW mechanism owing its own
charter that inherits the measured warning that hr-cut misbuckets PJM under
every estimator; do not treat the NEISO §F exposure as licence to re-derive
the NEISO surface (tail-excluded, re-normalized, or re-estimated) outside its
charter; do not read the M4 reproductions as a standing guarantee (they
certify current artifacts against current endpoints); do not re-litigate the
PJM `R` / NEISO `I` mechanism verdicts on anything here. Environment note:
the PJM/NEISO offer corpora are gitignored and die with the container —
refetch ≈65 min (PJM) / ≈3.5 h (NEISO) with one fetcher per year (a
shared-years invocation races year-scoped ones on the same files).

Next number: caiso-155.

## caiso-155 — 2026-08-02 — the diagnostics-harness PLANT-SET defect (caiso-151 §F): FIXED, plus two more harness defects the census found; no keeper verdict moved

AUDIT/SCORER session, not a mechanism lever (rule 28a): no cell re-tested, no
mechanism armed, no ScenarioConfig field, ZERO LP registered, no marker, no
dashboard registration (the caiso-136/143/144/149/150/152/154 no-solve
disposition — one aborted, discarded replay year notwithstanding). Record:
`results/calibration/FINDING-caiso155-diagnostics-plant-set-2026-08-02.md`;
probe `scripts/probes/_caiso155_plant_set_census.py`; pre-registration + two
addenda, each committed before the numbers they govern. Matrix audit row
`diagnostics_plant_set` (cells `IIOIII`) + §5.7 entry, in-session (rule 28b).

1. **Defect 1 (the charter defect)** — `aggregate_floors_by_plant` dropped
   every `plant_code <= 0` row, so interchange firm-import floors were
   invisible to D-2/D-4 (the caiso-151 D4_WINDOWS row was necessary, not
   sufficient). Fixed ISO-generically: floored pseudo-units ride as
   `u:<unit_id>` rows under a pre-registered floor-energy convention
   (dispatch := min_gen on every path — path-independent, and the CAISO
   number is exactly the caiso-151 §C exposure statistic); unfloored
   pseudo rows stay excluded; class `""` + non-thermal exemptions keep
   C7/C8 structurally invariant (unit-tested). CAISO census: the two firm
   tranches carry **17.938 / 22.684 / 22.494 TWh** — caiso-151 §C to the
   3rd decimal, reproduced by two independent reconstructions.
2. **Defect 2 (found by the census)** — the floors REBUILD dropped the
   generic override channels; CAISO's firm trio rides ONLY there
   (caiso-150 §E2's trap, measured on the G-06 path), and the unthreaded
   rebuild HALLUCINATED MISO's pre-miso-74 Manitoba block. Fixed:
   `REBUILD_META_RENAMES` (test-pinned to `replay_keeper._REMAP`).
3. **Defect 3 (exposed by the A1b gate)** — G-06 subtracted only the RA
   bridge; the whole P0-pattern bridge family is unrebuildable
   (nyiso109 false-FAIL by 5.31/3.14 pp averted). Fixed: `BRIDGE_MECHS`.

**Re-gate outcome:** NO committed artifact regenerated — the rebuild fails
A1b (solve-state floors would be lost) and an in-place caiso153 replay
failed D-13 with a measured degenerate-vertex signature (system duals
byte-identical, class/storage dispatch shuffled ≤2 GW; committed bytes
restored; NYISO replay declined on the same dependence). Every keeper's
criterion profile and determination is UNCHANGED (xiso-3 production-rubric
baseline == exit state; stop rule S1 never fired). The visibility lands
automatically on every future in-session artifact generation.

**DO-NOT-REDO (caiso-155, binding — full list FINDING §G):** do not quote
the census MISO 6.36/4.65/1.96 TWh as keeper exposure (the unthreaded
rebuild's hallucination — MISO's keeper has NO firm floor, miso-74 seam);
do not re-measure by hand (re-run the fix-aware probe); do not narrow
BRIDGE_MECHS back to the RA leg; do not regen a keeper artifact from the
fleet_only rebuild when its floors carry bridge/solve-state mechanisms; do
not read pseudo-row floor-energy TWh as at-floor dispatch (different
statistics — caiso-151 §F's 15.47 vs this session's 22.68, CAISO 2024).

Next number: caiso-156 (the CT heat-rate meter-screen charter, PRE-REGISTERED AND UNEXECUTED) / caiso-158.


## caiso-157 — 2026-08-02 — **TWO ABSENT DERIVED CLEAN PARTITIONS SILENTLY RE-ARMED A RETIRED FITTED IMPORT SCALAR ACROSS FIVE KEEPER PROMOTIONS.** Fixed, guarded, and promoted: keeper `2026-08-02-caiso157-partition-restore-b`. The seam's binding hours go 757/472/857 -> **0/0/0** and its congestion rent -$187.2M/-$15.1M/-$26.9M -> **exactly 0.000**. THE PRICE GATE DID NOT CLOSE (C3a-2025 +12.2 % -> +12.0 % against a +/-10 % band) and no closure is claimed

OFF-QUEUE by design, and the reason is stated per rule 28a: the lever came from a
PROVENANCE AUDIT run before any price statistic was read, not from the lever queue
(whose live items were item 3 and the pre-registered, unexecuted caiso-156 charter).
Prereg `PREREG-caiso157-derived-partition-restore-2026-08-02.md`, committed before any
arm solved. Probes `_caiso157_partition_audit.py` (transcript committed) and
`_caiso157_arm_compare.py`. Class: input-integrity defect fix (the caiso-152/153/155
class) — no matrix cell re-tested, no new `ScenarioConfig` field, **no config value
changed in any arm** (K3 verified). Rules 14 `[R-ACCURATE]`, 20 `[R-DOF]`,
24 `[R-REGISTRY]`.

**1. The defect.** `data/clean` is derived-and-gitignored, so it dies with the
container and every environment rebuilds it. Two partitions the CAISO keeper's armed
flags require were absent at solve time, and both loaders degrade gracefully — the
mechanism silently no-ops while the run's `meta` still advertises it.
`meta.shared_inputs` pins exactly these derived inputs
(`bundle_io.write_derived_solve_inputs`, whose docstring calls this *"the
silent-degrade trap"*). Auditing all 131 bundles on disk: **24 of 34 armed
(bundle, mechanism) pairs degraded, every one CAISO**; pinned through caiso-142
(2026-07-30), absent from caiso-146 (2026-07-31), so the keepers promoted at
**caiso-146, -147, -148, -151 and -153** all ran with `hydro_ror_split` and
`capacity_deliverability_limits` armed-but-inert. **The same check on every other
ISO's designated keeper is clean — the defect is CAISO-exclusive.**

**2. Why it is a governance defect.** With deliverability Part A a no-op the import
node falls back to `WECC_import_simultaneous.cap_mw = 7,500 MW`, a **residual**-identified
scalar the keeper's own DOF ledger calls *"Not in the keeper binding path"* and that
`iso_configs.py` carries expressly *"so this fallback cannot silently re-become the
binding import limit"*. Measured on the control's own **LP duals**, that claim was
FALSE: binding **757 / 472 / 857 h** with **-$187.2M / -$15.1M / -$26.9M** of rent,
p95/p99/max import all exactly 7,500.000 MW, **18.0 % of Sep-Dec 2025** pinned. The
accurate input is the published branch-group MIC, **16,055 / 16,452 / 16,148 MW**.

**3. Result.** Arm B restores both partitions: seam binding **0/0/0 h**, rent
**0.000**, and the constraint returns to the MEASURED corridor envelopes (2023 binding
2,850 -> 3,360 and 3,116 -> 3,273). **The price gate did NOT close**: C3a improves in
every year but only slightly (2023 +3.4 -> +3.1 %, 2024 +9.3 -> +9.2 %, 2025
+12.2 -> +12.0 %; needed <= +10.0 %), because the measured envelopes bind almost as
soon as the fitted seam relaxes — realised substitution is +0.456/+0.153/+0.398 TWh of
import against -0.398/-0.157/-0.398 TWh of CC_REGULAR. Determination
CALIBRATED-WITH-CAVEATS, unchanged, 0 FAILs, same 2 of 3 ledgered slots; no gate
regressed; C7/C8/D-4/D-2 PASS. D-1's ST_GAS FAIL rows are bit-comparable to the
control's and pre-existing on an immaterial class. **Promoted on structural-integrity
grounds** (rules 1/14): the accurate input goes in because it is accurate, and would
equally have gone in had the residual worsened.

**4. Unpredicted result worth recording — the RoR half is very nearly INERT at fleet
level.** Pinning 904.6 MW (13.5 % of the EHA fleet) flat moves the 2023 diurnal profile
from night 2,972 -> 2,966 MW, evening 3,781 -> 3,779, cv 0.489 -> 0.489. The armed
`hydro_min_flow_floor` already held that overnight level, so the split re-attributes
WHICH plants supply it (the accurate D-2 attribution) rather than changing shape. **It
does not resolve the caiso-125 overnight bang-bang signature** — that stays live.

**5. Root-cause guard shipped.** `market_sim.data.input_completeness.check_clean_partitions`,
called at `pipeline.year.run_year_solve` (the single per-year seam both orchestrators
share), RAISES instead of degrading when an armed mechanism's partition is absent. No
`ScenarioConfig` field, no threshold, no tunable; a no-op for every default-off flag.
7 unit tests over a tmp `CLEAN_DIR`. Widening it to other armed-flag/partition pairs is
FILED, not absorbed.

**6. DOF ledger corrected, not quietly fixed.** The `WECC_import_simultaneous.cap_mw`
row now records that its non-binding claim was FALSE for caiso-146..153 with the
measured counts, and re-verifies it TRUE on this bundle from this bundle's own duals.

**DO-NOT-REDO (caiso-157, binding — full list FINDING §F):** do not re-test partition
restoration as a price lever (its effect is measured and small); do not read this as
reopening C3a-2025 or C3c (both remain the owner's caiso-145 ledger, no closure
claimed — though caiso-140's "economic import-parity plateau" premise is corrected on
the record for 18 % of those hours); do not quote the RoR split as a shape fix; do not
widen the guard by analogy; do not treat the bundle sweep as the durable record
(retention pruned caiso138/caiso139 during this session — the committed probe
transcript is permanent); do not assume other ISOs need this fix (measured: they don't).

## caiso-159 — 2026-08-03 — **THE CT HEAT-RATE METER SCREEN IS PROMOTED TO KEEPER** (`2026-08-03-caiso156-meter-screen-b`), score-identical to caiso-157 on every criterion, D-gate flag and D-row verdict; and a **COMMITTED MERGE-CONFLICT CORRUPTION INSIDE THE NYISO KEEPER'S BUNDLE** was found and repaired first

**Keeper CAISO -> `2026-08-03-caiso156-meter-screen-b`** (bundle
`caiso156_meter_screen_B`). Determination CALIBRATED-WITH-CAVEATS, verified
IDENTICAL to the caiso-157 incumbent — all 9 criteria, grade summary (9/7,
ledgered 2, 0 fails), C1 headline (all 12/12 free 8/8), all six D-gate pass
flags and all 58 D-row verdicts. ZERO ScenarioConfig deltas vs the incumbent
(field-by-field diff), and `meta.shared_inputs` pins the same two derived
partitions, so the caiso-157 silent-degrade trap is not re-armed.

**What changed:** the CONTENT of the shared measured CT heat-rate artifact,
corrected at caiso-158 — the derive's declared physical band [6.0, 25.0]
MMBtu/MWh now applies PER LOADED HOUR instead of only to the plant aggregate.
Zero new parameters, zero ScenarioConfig surface. Artifact cap-weighted applied
rate 9.6603 -> 9.8362 MMBtu/MWh net over 43/43 plants, zero units dropped.

**Live and score-neutral are different claims.** P1 CT_PEAKER energy
1.9217->1.6599 / 0.7132->0.6370 / 0.5333->0.4157 TWh, up to 601.6 MW in one
class-hour and 4,117 of 8,760 hours changed in 2023 — while flipping zero
criteria and zero D-gates. Load-weighted lambda +0.195/+0.099/+0.111 % of level
against a pre-committed 1.0 pp escalation trigger, so no LOYO is owed. The
promotion rests on rule 14 [R-ACCURATE], not on a fit claim: the incumbent was
solving against an artifact diluted low by physically impossible meter hours,
and the corrected input would equally have gone in had the residual worsened.
REPORTED NOT HIDDEN: the ledgered C3a-2025 caveat moves ADVERSELY +0.11 pp —
immaterial against the bar, and not a reason to revert an accurate input.

**The blocker was mechanical, not evidentiary.** A probe bundle carries no
rule-21 attestation, so C6 scored UNATTESTED and ledgered caveats could not
downgrade FAIL -> CAVEAT. `scripts/gen_caiso159_attestation.py` carries the
incumbent's attestation forward with every magnitude RE-MEASURED from the arm's
own sidecars, pins the artifact's md5/coverage, and RAISES if the DOF ledger
moves (it does not: 11 entries / 9 residual, unchanged).

**Stop-the-line, done first:** eight committed JSON files across three NYISO
bundles carried live conflict markers on main, including the designated NYISO
keeper `nyiso113_lilocational_B`. Worse than the markers, git auto-merged the
NON-conflicting regions from the wrong side, so the keeper's committed
scorecard claimed `governance: UNATTESTED` and grade 8/7 when the truth is PASS
and 9/8. Repaired by whole-blob restore (markers are not the whole defect).
Blast radius measured: the run payload embeds no scorecard and `status/NYISO.js`
re-runs the scorer, so the dashboard never showed a wrong number.

DO-NOT-REDO: do not re-open whether the band belongs at hour grain (caiso-158);
do not read "zero criterion flips" as inert (thousands of hours move); do not
hand-resolve a rename/rename conflict in bundle JSON — restore whole blobs.
Holdout untouched (2023-2025 only, no LP ran, spend freeze unspent).
Evidence: `results/calibration/FINDING-caiso159-ct-heat-rate-promotion-2026-08-03.md`.

Next number: caiso-160.

## 2026-08-03 — CAISO — caiso-161: the CAISO mechanism-matrix column CLOSED (31 absent + 2 prose-only + 18 armed-no-cell → 0/0/0); ZERO new rows, ZERO mechanism verdicts; six keeper fields found ARMED-BUT-PROVABLY-INERT and two never-adjudicated rule-14 candidates queued — NO LP, keeper unchanged

**Session number:** this entry is **caiso-161**, not caiso-160. The previous
entry's footer reads "Next number: caiso-160"; the handoff prompt for this lane
named caiso-161, so **caiso-160 is deliberately left UNCLAIMED** rather than
risk colliding with an in-flight session. The gap is intentional, not a lost
entry.

**No LP, no solve, no registration** (rule 15 has nothing to register — no
bundle was produced). Keeper UNCHANGED at `2026-08-03-caiso156-meter-screen-b`.
Rule 22: **no year touched at all**, holdout spend freeze unspent.

The rule-28(c) census lane, after NYISO (nyiso-114) and ERCOT (ercot-156).
`scripts/mechanism_matrix_gap_sweep.py --iso CAISO` went **31 absent / 2
prose-only / 18 armed-on-the-keeper-with-no-cell → 0 / 0 / 0**; ratchet baseline
`docs/codebase-site/data/mechanism-matrix-gaps.json` CAISO **31 → 0**, no other
ISO's list grew (`--write-baseline` re-swept all six).

**How.** All 33 fields closed as **literal sub-scalar registrations** on 10
existing family rows (`gas_commitment_bridge`, `import_hub_pricing`,
`solar_deliverability`, `measured_offer_surface`, `gas_hub_basis_overlay`,
`storage_measured_anchors`, `measured_interface_limits`,
`reference_price_interface`, `ordc_scarcity_overlay`, `legacy_p2`) plus
`lcr_tsl_published`. **Zero new rows.** Cell changes: **exactly two**, both
rule-28(d)-admissible — audit row `matrix_gap_census` CAISO `O → K`, and
`lcr_tsl_published` CAISO `. → U` (a census may mint a `U` and nothing else).
Every mechanism row's `cells` and every `fc:` string is otherwise byte-unchanged.
All verdict-bearing text added is **transcription with citations** of
adjudications already on the record (caiso-74 storage-AS INERT + the
caiso-127/129 family refutation; caiso-104 M1 charge-allocation REJECTED;
caiso-137b DO-NOT-REDO on the scarcity import-headroom leg; caiso-84/-87/-90/
-93/-94/-97 keeper legs) — never a new judgement.

**Mechanical cause of most of the gap: abbreviated short-forms in a row's
`def`.** The coverage test matches literally. Four ARMED keeper fields sat in
`gas_commitment_bridge` written as `caiso_ra_startup_bridge / _bridge_decommit /
_bridge_startup_aware / _startup_trajectory / _bridge_curtailment_release`, so
`caiso_ra_bridge_decommit`, `caiso_ra_bridge_startup_aware`,
`caiso_ra_startup_trajectory` and `caiso_ra_bridge_curtailment_release` read
absent while three of them shape the keeper; `solar_deliverability` had the same
defect (`_endogenous_spill`). **Write registrations as full literals** — this
session's own census note reproduced the bug once and was corrected.

**THE FINDING THAT MATTERS FOR EVERY FUTURE CAISO SESSION: a CAISO
`run_config.json` is NOT an inventory of what is armed.** Six of the 18
"armed on the keeper" fields are non-default in all 19 bundles yet **unreadable
by any code path** in the keeper's configuration — verified at every call site,
not inferred from prose: `caiso_gas_floor_frac` 0.80 (sole read inside
`if caiso_gas_commitment_floor:`, which is `False` —
`scripts/run_calibration.py:2964-2969`); `caiso_solar_deliverability_k` 0.15 +
`caiso_solar_deliverability_floor` 0.50 (both derate call sites skip when
`caiso_solar_endogenous_spill` is on, which it is — `runner.py:1556-1570` gates
on `not _endogenous_spill`, `scripts/run_calibration.py:272-283` early-returns
on the spill branch **before** the derate); `caiso_solar_shape_nl_hi_pct` 30.0 +
`caiso_solar_shape_nl_lo_pct` 10.0 (sole read `inject_caiso_import_solar_shape`,
gated on `caiso_import_solar_shape`, `False` on the keeper).

**FILED FOR THE OWNER (not acted on): `caiso_gas_floor_frac` is the rule 26
`[R-DELETE]` shape.** It is the fitted scalar of the *retired,
rule-13-inadmissible* measured-outcome NG:NG midday gas floor that the RA
must-offer bridge replaced (`scenarios.py:2706` "Step-1 replacement for the
measured-outcome gas floor"; `:2740` "the removed NG:NG floor"), still shipped
at 0.80 by the **standard** CAISO backcast recipe
(`pipeline/backcast_config.py:1499`) and by ~40 committed probe drivers — i.e.
it propagates into every new CAISO run by default. "A deprecated parameter that
still parses is a re-armable answer key." Removing a `ScenarioConfig` field is a
mechanism change, which a census lane may not make (rule 28(d)).

**TWO NEW QUEUE ITEMS — surfaced, NOT tested** (rule 14 `[R-ACCURATE]`
measured-over-estimate candidates, default-off, armed in zero bundles,
adjudicated in no log entry, finding or cell anywhere):
`caiso_asymmetric_path_ratings` (published WECC Path Rating Catalog directional
limits for the internal N-S paths — Path 15 3,265 MW N→S vs 5,400 S→N, Path 26
4,000 N→S vs 3,000 S→N — against the symmetric TTC estimates whose loose
directions let the LP equalise the zones, Path 15 never binding and NP15==ZP26
byte-identical all years, and ship SP15 midday solar north past the real
3,000 MW Path-26 limit) and `caiso_per_year_import_caps` (per-year published LCT
pocket caps LA_BASIN 12,008/15,224/15,174 and SDGE 1,436/2,074/2,071 MW against
the static 2023 bake `scenarios.py:8955` itself calls "the deferred end state").
Queued in `docs/mechanism-testing-matrix.md` §5.2. A session taking either
**pre-registers it as its own single-delta arm and pushes the prereg BEFORE
solving**, rule 16 (2023-2025 in ONE bundle).

**Left open, deliberately:** the 5 shared-stem fields CAISO's keeper arms with
no row (`ct_drag_cap`, `ct_drag_intercept`, `ct_drag_slope_per_gw`,
`cc_outage_derate_from_top`, `chp_steam_floor_p25`) are non-ISO-prefixed and
armed across multiple ISOs' keepers — a **cross-ISO hygiene lane**, not one
column's session. Baseline `shared_armed_on_keeper` CAISO unchanged at 5; the
"CAISO 0" claim is exact for the ISO-stem ratchet, which is what CI enforces.

Also corrected: `docs/mechanism-testing-matrix.md` §5.2's heading keeper id had
gone stale at `2026-07-31-caiso148-nuclear-availability` (the
`check_mechanism_matrix.py` stamp guard covers the `.js` header only, so prose
drift is invisible to CI — the nyiso-116 class of staleness).

DO-NOT-REDO: do not re-run the CAISO census expecting new gaps (closed — the
per-ISO JSON is `results/calibration/_matrix_gap_sweep_CAISO.json`); do not read
a non-default `caiso_*` entry in a `run_config.json` as evidence a mechanism is
armed without checking its gate; do not close the 5 shared-stem fields in a
CAISO lane. No `R`/`I`/`G` cell was re-tested (`energy_reserve_coopt` `I` with
its caiso-144 DO-NOT-SOLVE, `cc_mustrun_per_plant` `R`, `wecc_endogenous_node`
`R`, `caiso_corridor_export_path` `R`, `caiso_p1_export_sink_seam` `R`,
`netload_drag_floors` `R` all untouched).
Evidence: `results/calibration/FINDING-caiso161-matrix-column-closure-2026-08-03.md`.

## caiso-162 — per-year LCT pocket import caps: a WIRING DEFECT, then a small real lever (2026-08-03)

**Mechanism** `caiso_per_year_import_caps` · **matrix** `lcr_tsl_published`
CAISO `U` -> `O` · **keeper UNCHANGED** at `2026-08-03-caiso156-meter-screen-b`.

**Registered:** `2026-08-03-caiso162-control` (arm A, flag off,
`caiso162_control_A`) and `2026-08-03-caiso162-per-year-import` (arm B v2, flag
on, `caiso162_peryear_import_caps_v2`).

**HEADLINE — the mechanism had NO CALL SITE IN THE BACKCAST LANE.**
`apply_caiso_local_import_limits` was invoked only from `runner.py:1627` inside
`run_scenario_iso`, the FORECAST path; a calibration solve reaches the LP via
`run_calibration.py::run_year` -> `pipeline.solve.run_energy_solve` and never
called it (the symbol appeared nowhere in `scripts/` or
`src/market_sim/pipeline/`). The field was therefore unreachable from EVERY
backcast — including via the `ScenarioConfig` field directly, the route
caiso-161 assumed worked when it minted the cell `U`.

**How it was caught.** Arm B v1 recorded `caiso_per_year_import_caps=true` in
its own `run_config.json` and came back BYTE-IDENTICAL to the flag-off control
in all three years. On prices that is a clean `INERT` read — it would have
written a FALSE `I` (a DO-NOT-REDO code) on a mechanism that had never executed.
The FLOWS falsified it: B v1's pocket links topped out at exactly 12008.00 /
1436.00 MW, the static caps. **Standing lesson, generalising caiso-161 lesson
(a): a `run_config.json` recording a mechanism as armed is NOT evidence the LP
saw it — confirm a CALL SITE EXISTS ON THE LANE BEING SOLVED, and verify on a
flow/observable rather than on price.**

**Second defect, self-inflicted.** Prereg section 7 asserted 2023 must match THE
KEEPER byte-for-byte. The keeper (sha `69e0e30`) is 13 `src/market_sim` commits
behind this session's basis, several solve-affecting, so keeper-vs-treatment
measures HEAD drift plus the arm. Withdrawn in ADDENDUM A and replaced by a
same-HEAD control. Scale of the drift: arm A scores C3a-2025 at +12.1% where the
committed keeper scores +12.2% — comparable to the effect under test, so without
arm A the lever's whole signal would have sat inside the drift.

**Measured (arm A vs arm B v2, same head, single flag delta).** Flows: 2024
LA_BASIN 12008 -> 13319, SDGE 1436 -> 2074 (binding at the published cap); 2025
LA_BASIN 12008 -> 14405, SDGE 1436 -> 2071. Load-weighted mean LMP: 2023
BYTE-IDENTICAL (provable no-op — the zero-delta control, PASSED), 2024 -0.1670%
of level, 2025 -0.1236%. C3a-2025 +12.1% -> +12.0%. ZERO gate flips on all nine
criteria. Zonal signature is the mechanism's own: SDGE (binds 11.5% of hours)
-0.958/-0.626 $/MWh while LA_BASIN barely moves despite carrying 83% of the MW
loosening (binds 0.7% of hours) — reproducing the pre-registered pre-check.

**Ceiling held.** Prereg section 3 pre-committed that removing the pocket premium
ENTIRELY moves 2025 by at most $0.084/MWh (0.22% of level) against the
$0.76/MWh needed for the +-10% band; realised -$0.0477/MWh, 57% of the ceiling.
PARTIAL CREDIT against the pre-registered bars; the PASS bar was pre-registered
as unattainable and was not attained.

**Governance note the owner asked for.** The caiso-141 A2 pumped-storage wall was
NOT reopened. Bound on what this lever could have taken from it: <=0.22 pp of a
12.2 pp residual, under 2% — **the A2 attribution is NOT materially undermined.**

**Disposition (rule 14, pre-committed before the result).** The published input
is measured, same-convention and forward-reproducible; it beats the frozen 2023
estimate REGARDLESS of fit and is neither reverted nor parked. Zero free
parameters, no new caveat, no ledger slot. The cell is `O` not `K` only because
promotion is a separate governance act (a replay probe bundle carries no
`calibration_attestation.json`). **RECOMMENDED FOR PROMOTION** — LOYO-clean by
construction (2023 a no-op, 2024 and 2025 both improve).

**DO-NOT-REDO:** do not re-test that the mechanism works, and do not propose it
for C3a-2025 (ceiling ~11% of the gap). `caiso_asymmetric_path_ratings` remains
the untested caiso-161 queue item and gets its own arm.

Evidence: `results/calibration/FINDING-caiso162-per-year-import-caps-2026-08-03.md`,
`PRECHECK-caiso162-per-year-import-caps-2026-08-03.md`,
`PRECHECK-caiso162-ADDENDUM-A-samehead-control-2026-08-03.md`.

---

## caiso-163 — asymmetric WECC path ratings (2026-08-03) — **KEPT, PROMOTED**

**Keeper → `2026-08-03-caiso163-asym-path-ratings`** (control
`2026-08-03-caiso163-control-asymoff`). Determination **CALIBRATED-WITH-CAVEATS**,
carried over unchanged: 2 ledgered / 0 FAILs / protective 0 of 1, no new slot spent.
`audit_keepers.py --iso CAISO` PASS (0 failures, 0 warnings).

**Mechanism.** `caiso_asymmetric_path_ratings` — CAISO's two INTERNAL north–south
paths move from the **symmetric** TTC estimate the reduced topology ships
(`iso_configs.py:369-378`: Path 15 5,400 MW, Path 26 4,000 MW) to their
**published WECC Path Rating Catalog directional ratings**: Path 15
(Midway–Los Banos) **3,265 N→S / 5,400 S→N**, Path 26 (Midway–Vincent)
**4,000 N→S / 3,000 S→N**. Each shipped `ttc_mw` was only ONE direction's rating,
leaving the reverse direction up to **65 % too loose**. Rule 14 `[R-ACCURATE]`
measured-over-estimate; **zero free parameters** (all four numbers already
committed in `CAISO_PATH_DIRECTIONAL_RATINGS`; nothing swept, no residual
consulted; DOF ledger carried verbatim at 11 entries / 9 residual, asserted by
`scripts/gen_caiso163_attestation.py`).

**Wiring, checked BEFORE solving — and the answer differed from caiso-162's.**
The backcast call site already existed: `interchange/spec.py:1988` inside
`apply_interchange_topology`, reached from `run_calibration.py:2037` in the
`priced_interchange` branch the CAISO keeper takes. A no-LP probe
(`scripts/probes/caiso163_wiring_probe.py`) replayed the calibration lane's exact
topology sequence and resolved **2 directional limits to non-empty LP flow-column
groups** in all three years. What was missing was only the CLI/kwarg channel,
wired across **seven** sites (five in `run_calibration_full.py` plus the argparse
flag, and the two `run_calibration.py` sites caiso-162 lost a solve to).

**No zero-delta year exists** — the published ratings are year-invariant, so every
solve year is live. The prereg replaced the free control with a **pre-solve
structural assertion**, passing before either arm solved: with the flag off,
`apply_caiso_asymmetric_path_limits` returns the **SAME OBJECT** (identity, not
equality). That is what licenses arm A as a clean control.

**Liveness — on FLOWS, never on prices (the caiso-162 lesson, applied ex ante).**

| path · year | control max N→S | h over cap | control max S→N | h over cap | arm h over ANY cap |
|---|---:|---:|---:|---:|---:|
| Path 15 · 2023/24/25 | 4,119 / 4,443 / 4,597 | **294 / 450 / 380** | 5,400 / 5,400 / 5,400 | 0 / 0 / 0 | **0 / 0 / 0** |
| Path 26 · 2023/24/25 | 4,000 / 4,000 / 4,000 | 0 / 0 / 0 | 3,514 / 4,000 / 2,946 | **6 / 11 / 0** | **0 / 0 / 0** |

The incumbent configuration moved power **past a published WECC rating in 1,141
path-hours**; under the keeper that is **zero in every hour of every year**, and
the paths bind as real paths do (Path 15 N→S 307/489/411 h; Path 26 N→S
1,656/1,987/2,213 h — roughly a quarter of hours, the midday solar belly).

**Structural gates.** Path 15 binds at all for the first time: hours with
NP15 ≠ ZP26 go **3 → 237**, **0 → 414**, **1 → 284**, and the 2024
byte-identity breaks. Level effect nil: **−0.0036 % / −0.0147 % / +0.0102 %**.
**Zero gate flips** — all nine criteria identical to the control, C3a-2025
unchanged at **+12.0 %**, protective C6/C7/C8 PASS.

**THE ROOT-CAUSE ISSUE THIS OPENS — the session's real finding.** S3/S4 move
marginally the **wrong** way and the published ratings **stay in anyway**, exactly
as the prereg §4.4 pre-committed before any arm solved. Prereg §3 also registered,
before solving, that the two legs push the ISO mean in **opposite** directions and
predicted **no** sign; the solve resolves it — the Path-15 N→S leg dominates,
trapping cheap northern energy in NP15. But the magnitudes are what matter: the
**real** Path 15 separates NP15 from ZP26 in **~100 %** of hours by
**+5.95 / +8.58 / +5.73 $/MWh**, against this keeper's **−0.077 / −0.109 /
−0.084**; NP15 − SP15 goes −1.168/−0.913/−0.770 → −1.226/−0.983/−0.822 against a
measured **+2.34 / +7.99 / +6.01**. So the published ratings are **NOT** the
binding cause of the model's missing north–south basis — fixing them recovers
~1 % of it. Under rules 14 and 1 `[R-STRUCT]` that is a **discovered bug**, not a
revert: the symmetric estimate was silently absorbing a defect that lives
elsewhere. **Named open successor (hypothesis, NOT adjudicated, no solve spent):**
the reduced **two-link N–S topology and zonal aggregation**, which cannot
reproduce hourly Path-15 congestion whatever the ratings are. It needs its own
pre-registration and its own arm. No compensating adder, haircut or offset was
added to hide the gap (rules 1/13), and the gap is **not** claimed as closed.

**NOT A C3a ARM** and must not be reported as one — C3a-2025 is unchanged and the
level effect is 0.01 %.

**Governance.** Config drift is **exactly one field** against **both** the
incumbent and the same-HEAD control, with zero schema drift on either side. The
four owner-decision default flips (D-1/D-2/D-3a) were already carried by the
incumbent so they do not even appear as a drift; asserted anyway on both grounds
(forecast-gated, unreachable at `mode="backcast"`; identical across arms). CAISO
holds **no** `complete` marker, so no `calibration-complete` re-key (rule 22
D-5(b) applies to `complete` ISOs only) and no marker written; the **holdout spend
freeze is ACTIVE** — 2023/2024/2025 only (rule 16, one invocation and one bundle
per arm, years sequential, in-session).

**Correction to the caiso-161 census's premise, recorded not buried.**
"NP15==ZP26 byte-identical all years" holds for **2024 only** — 2023 and 2025
differ in 3 and 1 hours (max |Δ| 1.14 and 4.29 $/MWh). The finding that Path 15
essentially never bound is unchanged; the prereg's gates were written against the
measured 0.034 % / 0 % / 0.011 % rather than against zero.

**DO-NOT-REDO:** do not re-test `caiso_asymmetric_path_ratings` (keeper). The
caiso-161 lever queue is now **empty of never-adjudicated items**.

Evidence: `results/calibration/FINDING-caiso163-asymmetric-path-ratings-2026-08-03.md`,
`PRECHECK-caiso163-asymmetric-path-ratings-2026-08-03.md`.

Next number: caiso-164 (caiso-160 unclaimed, see above).
