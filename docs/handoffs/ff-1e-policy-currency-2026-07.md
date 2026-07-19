# FF-1E-policy — FF-0D policy-currency fixes (2026-07)

**Session.** Wave-1 lane **L-INP** of the Forecast Finalization Program, the
**item-2** remainder of FF-1E — the FF-0D §4 *policy-currency fixes* that the
entry-cost session (#2515/#2518) did not touch. Its FF-1E doc §4 verified the
policy layer but landed **no source change** ("no citable delta found… bounded
follow-up"); this session did the primary-source research and **landed the
cited refresh** the audit routed here (rule 23). Branch
`claude/ff-0d-policy-currency-lr9p1y` off `origin/main` (37d3923).

**Scope guard.** Cited-values-only. Every changed number is in the committed
diff with a primary-source citation (rules 5/13/23). The RPS/ACP layer is
**forecast-only** — `pipeline/backcast_config.py` hardcodes `rps_enabled=False`,
and `STATE_RPS_ACP`/`STATE_RPS_FLOORS` are imported **only** by `policy/rps.py`,
whose `get_rps_*` lookups `runner.py` calls **only** under `if config.rps_enabled`
— so every change here is **backcast byte-identical by construction** (proof §4).

---

## 0. Headline

| Item | Verdict | Action |
|---|---|---|
| IRA / OBBBA fields (§1) | **CURRENT** | verified vs statute + FF-0D §4.1 + intake CSV; **no change** |
| MA Class I RPS ACP (§2) | **STALE → fixed** | `$67.62 → $40/MWh` (225 CMR 14.08 — 2021 reset); feeds NEISO |
| NEISO regional ACP (§2) | **refreshed** | `STATE_RPS_ACP["NEISO"] 65.0 → 50.0` (re-blend on corrected MA + NH/ME/RI) |
| PJM load weights (§2) | **refreshed** | comment weights → primary Monitoring Analytics **2024** annual (OH/VA up, KY added) |
| CAISO ACP (§2) | **CURRENT** | `$50/MWh` confirmed (Pub. Util. Code §399.15); citation hardened |
| NYISO ACP (§2) | **nuance** | Tier-1 ACP **eliminated after CY2024**; `$40` KEPT as ceiling proxy, documented |
| PJM ACP + floor knots (§2) | **CURRENT** | `$45` and 0.185/0.23/0.30/0.33 verified within Tier-3 tolerance; kept |
| Confirmed retirements (§3) | **CURRENT** | re-query: no new binding instrument → **no additions** |

Only **two runtime deltas**: `STATE_RPS_ACP["NEISO"] 65→50`, and the PJM-floor +
ACP **comment/provenance** refresh. Both forecast-only.

---

## 1. IRA / OBBBA (§4.1) — verified CURRENT, no change

All fields exact-match FF-0D §4.1, 26 U.S.C., and the intake store
`data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv` (programmatic
cross-check, this session):

| Field | Value | Statute |
|---|---|---|
| `ira_wind_solar_last_year` | 2027 | §45Y/§48E OBBBA cliff (BOC<2026-07-04 + ISD≤2027-12-31) |
| `ira_45u_last_year` | 2032 | §45U(e) terminates after 2032-12-31 |
| `ira_h2_45v_last_year` | 2027 | §45V BOC ≤ 2027-12-31 (OBBBA cut from 2033) |
| `ira_ccus_45q_last_year` | 2032 | §45Q(d)(1) BOC-before-2033 proxy; OBBBA §70522 preserved 45Q |
| `ira_other_clean_{full,75,50,end}` | 2033/2034/2035/2036 | §45Y(d)/§48E(e) step-down |
| `ira_45q_credit_window_years` | 12 | §45Q(a)(3)-(4) |
| `ira_ptc_wind` | 26.0 | inflation-adjusted §45 wage-compliant |
| `ira.py` credit values | 45V $3/kg · 45Q $85/tCO2 · 45U 1.5¢/kWh (0.3×5) · 2.5¢ threshold · 16% phase-down | §45V / §45Q / §45U(a)(b)(2)(d)(1) |

**45Y/48E primary confirmation (§4.2)** remains a MANUAL DOWNLOAD — the
2033–2036 steps are triangulated from two secondary OBBBA alerts; `federalregister.gov`
still returns a bot-wall in this environment (unchanged from FF-0D/FF-1E). Not a
suspected error; a provenance upgrade for a later authorized pull.

## 2. State RPS / ACP (§4.3) — refreshed to cited published schedules

Primary sources fetched this session (verbatim quotes/values in the diff comments):

- **MA Class I RPS ACP = $40/MWh, Compliance Year 2023+ (then CPI-adjusted)** —
  225 CMR 14.08(3)(a)(2), verbatim: *"…$60 per MWh in Compliance Year beginning
  in 2021, $50 per MWh in Compliance Year 2022, and $40 per MWh, beginning in
  Compliance Year 2023."* A 2021 reform **reset the rate DOWN** the $60/$50/$40
  glide from the pre-2021 CPI-escalated series (which topped ~$71.57). **The code's
  `$67.62` was stale** (an old CPI-escalated value). (law.cornell.edu/regulations/massachusetts/225-CMR-14-08)
- **CT Class I $55, NH Class I $62.24 (2024)/$63.29 (2025), ME Class I $50 (max),
  RI RES $83.37 (2024)** — Conn. Gen. Stat. §16-245a; NH DoE RPS compliance
  (½-CPI); 35-A M.R.S. §3210; RI PUC ACP rate.
- **NEISO** re-blend (MA/CT/NH/ME/RI over ISO-NE load shares MA≈48/CT≈24/NH≈9/
  ME≈9/RI≈6/VT≈4 %) ⇒ **≈$50/MWh** → `STATE_RPS_ACP["NEISO"] 65.0 → 50.0`. The
  old $65 was driven entirely by the stale MA $67.62.
- **CA §399.15 = $50/MWh per deficient REC** — CPUC RPS enforcement. Confirms
  `STATE_RPS_ACP["CAISO"] = 50.0`. Unchanged; citation hardened.
- **NY CES Tier 1 ACP eliminated after CY2024** — NYSERDA: *"no ACPs will be
  collected for compliance year 2025 onward."* Post-2024 the obligation is a
  cost-recovery charge (net REC procurement ÷ statewide load), not a $/MWh buyout.
  `STATE_RPS_ACP["NYISO"] = 40.0` **KEPT** as the forward REC-price-ceiling proxy
  (historical Tier-1 order-of-magnitude, consistent with index-REC net cost);
  a strike-derived ceiling is flagged as a bounded follow-up.
- **PJM load-by-state weights → Monitoring Analytics 2024 annual (primary)**
  (`PJM_Load_by_State_2024_20250716.XLS`, parsed this session): OH 20.1 / PA 18.9 /
  VA 17.6 / IL 11.6 / NJ 9.6 / MD 7.8 / WV 4.6 / KY 3.0 / IN 2.75 / DE 1.5 /
  DC 1.25 / MI 0.56 / NC 0.55 / TN 0.21 %. The prior comment **understated OH
  (14→20) and VA (14→18) and omitted KY (3%)** — all low/no-RPS load. Re-blending
  the per-state renewable-tier schedules on the corrected weights reproduces the
  **2030 knot at ~0.22** — within Tier-3 tolerance of the existing **0.23**, which
  is KEPT (the OH/KY-down and VA-up corrections offset). **PJM ACP $45 kept** —
  verified reasonable (MD refreshed to ~$30 declining to $22.35 by 2030, MD PSC
  CY2024 RPS report; VA ~$47, PA/OH ~$45); a full per-state re-blend of the knots
  and the load-weighted ACP is a bounded intake (the PJM-EIS comparison publishes
  its tables as page images — no clean machine read this session).

Floor **percent** trajectories (CAISO SB100, NYISO CLCPA, NEISO MA-CES blend)
were re-confirmed unchanged against statute (FF-0D §4.3 verdict holds).

## 3. Confirmed retirements (§4.4) — re-query, no additions

Targeted re-query 2026-07-19 of the FF-0D-flagged pending items:

- **PJM Brandon Shores 1-2 + H.A. Wagner 3-4 (2031 RMR extension):** as of
  June 2026 the Talen/PJM joint filing to extend the RMR through **May 2031**
  is **still PENDING FERC** (PJM requested a decision by early August 2026 —
  Maryland Matters 2026-06-11). Not yet binding; `exit_year` correctly held at
  2029. No change (the `pjm.csv` note already states this).
- **New 2026 DOE §202(c) orders (R.M. Schahfer, J.H. Campbell, F.B. Culley in
  MISO; a PJM gas unit):** these **compel continued operation** — retirement
  **deferrals / counter-instruments**, not new confirmed exits. None create a
  binding exit to add; none of the affected units are confirmed-exit rows.
- **PJM Eddystone 3-4 §202(c) chain:** current order 202-26-24 through
  2026-08-22; still `superseded=true`. No change.

Per rule 5 and the confirmed-exit definition (an enforceable public instrument
with an `instrument_date`), **no rows were added or changed** — matching FF-0D's
disposition. The registry stays a next-intake-vintage re-query list.

## 4. Backcast byte-identity + verification

- **Structural proof.** `STATE_RPS_ACP`/`STATE_RPS_FLOORS` are imported only by
  `policy/rps.py` (grep-confirmed; the `federal_ces.py` hit is a docstring
  reference). `get_rps_target`/`get_rps_acp` are called only at `runner.py:1297-98`
  under `if config.rps_enabled and not federal_ces_suppresses_state_rps(config)`.
  `backcast_config(...)` hardcodes `rps_enabled=False` (forecast default is
  `True`). So no backcast solve reads these constants — every change here is
  **byte-identical in backcast by construction** (same guarantee FF-1E used for
  the entry-cost changes; both are forecast-only).
- **Scope of the runtime delta.** The only value change is `NEISO 65→50`, a
  per-ISO dict entry that enters **only** the NEISO forecast RPS-escape-column
  cost; `test_rps_iso_returns_acp_ceiling` confirms CAISO/NYISO/PJM/ERCOT
  unchanged — the "moves only what it should" evidence at the unit level. A
  full before/after forecast dual-solve smoke was judged unnecessary for a
  single transparent, per-ISO, forecast-only parameter (FF-1E already ran a
  NEISO forecast smoke on this seam); it is left as the documented optional.
- **Tests.** `TestGetRPSACP` + `TestGetRPSTarget` + the dispatch RPS-mechanism
  and driver-directionality RPS tests pass (27 tests). `test_capacity.py`'s
  NEISO assertion updated `65.0 → 50.0` with the citation rationale in-test (the
  only test that pinned the corrected constant; the `rps_acp_price=65.0` fixtures
  in `test_dispatch.py`/`test_driver_directionality.py` are mechanism inputs, not
  value assertions — untouched).

*Produced 2026-07-19 (FF-1E-policy, Opus). Closes FF-0D §7.2 P2 policy items
(§4.3 RPS/ACP refresh, §4.4 confirmed-retire re-query) and verifies §4.1/§4.2.*
