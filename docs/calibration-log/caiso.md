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
