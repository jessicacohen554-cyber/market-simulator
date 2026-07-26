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
