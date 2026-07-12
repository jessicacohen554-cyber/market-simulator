# FINDING — caiso-79 STEP-0: the Greater Bay LCT import cap CANNOT bind on energy — the NP15 → GREATER_BAY split is REFUTED ex-ante (no solve); the CT lane's driver is local *commitment*, not an import-limited pocket (2026-07-12)

**STEP-0 for the caiso-79 CT_PEAKER local-commitment granularity lane**
(docs/handoffs/caiso-79-next-run-plan-2026-07-12.md §3, the caiso-70/71/78
decide-before-solving method). Diagnostic:
`scripts/probes/_caiso79_step0_greaterbay_bind.py` (measured inputs only —
Final LCT report parameters, CAMPD hourly, PGE-TAC / EIA-930 hourly load,
the committed caiso-78 payload decode; no LP, derives nothing).

## 1. Data completion (committed with this FINDING)

* `data/raw/capacity-deliverability/caiso/caiso.csv`: Greater Bay
  `peak_load` rows — **11,136 / 11,081 / 11,992 MW** (2023/24/25, Final LCT
  Table 3.3-29 / 3.3-27 "Load + Losses + Pumps") — plus the NP26 zonal
  forecast rows (20,748 / 20,867 / 21,140 MW, Table 3.2-1), same schema as
  the committed LA Basin / SDGE / SP26 rows.
* `data/raw/reference/lcr_area_membership_CAISO.csv`: Greater Bay membership
  (77 plants, 6,969 MW) via `scripts/derive_lcr_membership.py` — county rule
  for the five core Bay counties plus the LCT §3.3.5.1 **substation-rule**
  overrides: the Moss Landing bus is IN the area ("Los Banos is out Moss
  Landing is in" — Monterey county), and the Lambie SW Sta is IN (the three
  Solano LM6000 peakers). Existing LA Basin / SDGE rows byte-unchanged.
* Measured import capability, the plan's gate quantity:
  `import_cap = peak_load − LCR` = **3,824 / 3,752 / 4,551 MW** —
  34/34/38 % of pocket peak (between LA_BASIN's never-binding 61 % and
  SDGE's binding 30 %), so the ex-ante test below was genuinely open.

## 2. The ex-ante bind test — the cap cannot bind

Pocket hourly load = measured PGE-TAC hourly × the LCT planning share
(GB ÷ NP26: 0.531/0.567 for 2024/25; 2023's committed TAC file covers
January only, so 2023 uses EIA-930 CISO demand × the whole-CAISO share
0.228 — the two bases agree to ~±350 MW p50 on 2024/25). In-pocket supply
split CT_PEAKER vs non-CT on the committed bench-part class map (16 CAMPD
gas plants: CT 1,362 MW — Marsh Landing, Mariposa, Gilroy PP, the Lambie
trio, Riverview; non-CT 5,970 MW — Moss Landing, Delta, Russell City,
Metcalf, Gateway, Los Medanos, Los Esteros, DVR, Gilroy cogen); non-CEMS
resources (battery / MUNI-QF / wind / DR) at the LCT table's own At-Peak
credits (1,616 / 1,912 / 2,254 MW).

| residual (evening HE18-23) | 2023 | 2024 | 2025 |
|---|---|---|---|
| **resid_B** = load − cap − non-CT thermal at 93 % **capacity** − credit: share > 0 | **0.0 %** | **0.1 %** (max +20 MW) | **0.0 %** (max −1,650) |
| resid_B **without any battery credit**, all hours: share > 0 | 0.0 % | 0.4 % (max +1,002) | 0.0 % |
| resid_A = load − cap − non-CT at **actual** output − credit: share > 0 | 3.2 % | 10.8 % | 1.2 % |
| measured GB CT ON share (evening) | **42.6 %** | **28.8 %** | **22.1 %** |
| measured GB CT evening p90 (MW) | 402 | 309 | 87 |

Reading, in the lane's own terms:

1. **The strong form fails everywhere.** With every non-CT resource maxed,
   the pocket needs CT in ≤ 0.1 % of hours (a single ~20 MW-deep hour in
   2024; ~35 h/yr at ≤ 1 GW even with the whole battery fleet zeroed). An
   `NP15 → GREATER_BAY` link capped at the measured 3.8–4.6 GW would
   essentially never bind — it cannot move 3–4 TWh/yr of CT, cannot form
   the 2024/25 local C3c tail, and cannot fix the C7 CT shape. The LA_BASIN
   lesson repeats one level down: an LCT requirement is an N-1-1
   contingency construct at 1-in-10 peak, not an average-conditions energy
   wall.
2. **Reality's own CT commitment is NOT energy-cap-driven either.** The
   measured GB CTs are ON in 22–43 % of evening hours while even
   resid_A — reality's own non-CT dispatch — is positive in only 1–11 % of
   them. Real Bay-Area CT starts are contingency positioning / local-RA
   commitment (RMR, exceptional dispatch, minimum-online constraints), the
   caiso-71 §3 conclusion now with the import-cap alternative measured and
   eliminated.
3. **The model already serves the pocket with comparable local thermal.**
   caiso-78 payload GB thermal evening p50 3,149/3,203/2,917 MW vs measured
   3,325/2,866/2,318 (CT+non-CT) — the miss is the *mix* (model CC vs real
   CT starts), not the import share, consistent with the caiso-78 STEP-0
   offer-ordering finding.

## 3. Fork taken (plan §3): do NOT build the split

Per the pre-registered fork, the topology build (caiso-79a) is dead — a
structurally-unreal import wall tuned tight enough to force CT would be a
rule-1 violation, and the honest cap is inert. **No caiso-79 solve was run
this session** (STEP-0 gates the LP). The lane redirects to an explicit
**measured local-commitment driver** on the pocket's named CT units — design
doc filed owner-visible at
`docs/handoffs/caiso-local-commitment-driver-design-2026-07.md` (window +
driver + forward story + the `D4_WINDOWS` entry plan, rules 12/17/18/19),
for owner review BEFORE any solve.

## 4. Files

* `scripts/probes/_caiso79_step0_greaterbay_bind.py` — the diagnostic.
* `data/raw/capacity-deliverability/caiso/caiso.csv` — GB/NP26 peak_load rows.
* `data/raw/reference/lcr_area_membership_CAISO.csv` +
  `scripts/derive_lcr_membership.py` + `market_sim/data/local_capacity.py`
  (GREATER_BAY constant, county map, substation overrides) — membership.
  Greater Bay is deliberately NOT registered as a `LocalCapacityAreaSpec`,
  so every solve-path consumer (`load_lcr_parameters`,
  `apply_caiso_local_import_limits`, the local-capacity floor) is unchanged
  — the intake is scorer/solve-inert by construction.
* `docs/handoffs/caiso-local-commitment-driver-design-2026-07.md` — the
  redirect design.
