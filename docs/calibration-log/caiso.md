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
