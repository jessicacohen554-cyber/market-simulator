# FINDING — capx D74: the PJM "Steam Oil & Gas" no-default-cap price-taker convention — BUILT, GATED DEFAULT-OFF, and MEASURED at HEAD against same-HEAD controls

**Lane:** capx D74 (director r#46). Branch `claude/capx-d74-pjm-steam-oil-gsxcx5`, fresh off
`origin/main` `6887484f`, fast-forwarded to `2eb65038` before the design; base for every solve
`64477801` (the build commit). DATA PROFILE `pjm`. Model Fable. **Not D67.**
**Binding charter:** pack §D74 + `FINDING-capx-d61-2026-09-05.md` §4 card (c) +
`FINDING-capx-d62-2026-09-06.md` §5.3 / §9 item 2 + `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`
§3.5. **Design:** `DESIGN-capx-d74-pjm-steam-oil-convention-2026-09-06.md` (pushed `cafb14d1`
before any code). **Pre-registration:**
`PRECOMMIT-capx-d74-pjm-steam-oil-convention-2026-09-06.md` (same commit; Addendum A in the build
commit `64477801`, before the first solve). **Instruments:** `docs/handoffs/d74/phase0-2026-09-06.{py,json}`
(zero LP), `screen-gate-2026-09-06.py` → `screen-2026-09-06.json`, `full-window-2026-09-06.json`.
**Nothing arms in this lane.**

---

## 0. The answer in one paragraph

**PJM's own rule for the "Steam Oil & Gas" class through DY 2025/26 is that it had no default
sell-offer cap (Manual 18 §5.4.8.4(B) prints "NA"; §5.4.1 allows an offer above $0 only on a
unit-specific filing "or … the default gross ACR of the applicable resource type, if available"),
and PJM's uncleared steam in the model is 86 % merchant — so the object D61 §4 card (c) named is
neither an ownership partition (D53/D58's lane reaches ~8 % of it) nor a level: it is the class's
own no-default-cap limb of the table D62 already reads.** Built as one default-off `{iso: bool}`
gate in the D57 family with zero scalar fields, the convention makes such a unit a $0 price taker
in the D57 stack and exempt from the merchant screen in that year (its exit is its owner's filing),
and the D54 §3.5 identity holds by construction. Measured at HEAD against same-HEAD controls
(form 4 void on D67's LIVE hunk): the footprint is pure (834 / 834 offers identical, zero pipeline
rows at any steam/oil unit, `R` and the non-class `Q_0` identical to the MW in every delivery year),
the solve lands on its own re-clear arithmetic to 0.0001 $/MW-day, and **the 9.46 GW steam / 4.14 GW
oil over-exit is gone (gas_st 10.297 → 0.833 GW, oil 4.188 → 0.051 against 2.702 / 0.613 actual)**.
What replaces it is the thing the convention exposes rather than creates: **the admission cap
re-fills from the CT plateau that sits at the clearing price with zero E&AS, 6.888 GW of CT exits
against 0.808 actual**, recall 11 → 8 of 20, economic release precision 14.8 → 2.6 %, and — through
that exit's timing — the 2024/25 census rises 6.05 GW and the price falls 270.99 → 82.69 $/MW-day
(9.37× → 2.86× the published), taking FC-2 `gas_cc` PASS → FAIL. `retire.total_gw` reads a band
PASS (15.689 vs 15.062) that is composition, not skill, and is named as such. **Five of the
fifteen pre-declared signs miss** — three because the PRECOMMIT computed them on the pre-hunk
committed stack, two on the propagation's magnitude — and STOP 7 fires on the literal RSS number
on every HEAD leg identically. **§8 is DO-NOT-ARM AS IT STANDS, on the D62 precedent: the
mechanism is the market's own rule and stays in; arming it alone moves the over-exit onto the CT
plateau (D54 §6 item 1, D61 §1.5), which is routed ahead of it.**

---

## 1. What was built (PRECOMMIT §1, as pre-registered)

| # | piece | where |
|---|---|---|
| 1 | `capacity_no_default_cap_convention_by_iso: dict[str, bool] \| None = None` — the FIFTH per-ISO capacity gate, resolved through ONE predicate `config/capacity_market.py::resolve_capacity_no_default_cap_convention`, which REQUIRES the D62 published-bar gate ON for the ISO (a limb of that table; over the ATB proxy there is no "NA" cell — returns False, logs once). **No scalar field.** Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_DEFAULTS` at `"None"`, `TIER_TAGS` 1, coerced to `None` in a plain backcast; CLI `--capacity-no-default-cap-convention` (+ `--no-`) on both harnesses, recorded in `run_config.json` through the resolved predicate beside the raw mapping; re-exported through the `constants` facade like its siblings. **Not armed:** no `_pjm_config` override. | `config/scenarios.py`, `config/capacity_market.py`, `config/constants.py` |
| 2 | **THE PREDICATE.** `data/avoidable_cost_rate.py::no_default_cap_class(iso, fuel, delivery_year)`: True iff the ISO's published table carries `gross_acr` rows for the fuel's class but NONE in the column the fixed D62 vintage rule selects for that delivery year — exactly the limb `_row_for` reports as basis `"first_published"` (PJM "Steam Oil & Gas" through DY 2025/26). Adds no number. | `data/avoidable_cost_rate.py` |
| 3 | **THE SEAM.** `retirements.py::apply_economic_retirements`, the candidate loop: beside the `exempt_unit_ids` exemption, a unit whose class has no published default for the delivery year is skipped before `margins`; `_settle_capacity_supply_clearing`'s own `Q_0 = accredited − Σ A_g(screened)` puts its accredited MW in the price-taking block (I1 structural; the D54 §3.5 identity by construction). `resolve_going_forward_bar_per_kw_yr` untouched. | `retirements.py` |
| 4 | **LEDGER.** Additive `no_default_cap_price_takers` block per screen year (units, MW, accredited MW, by fuel, unit ids, basis); absent off the gate. | `retirements.py`, `evolve.py` |
| 5 | Tests (25), the `VERDICT_MAP` entry, the matrix base row + six shard cells. | `tests/`, `scripts/`, `docs/codebase-site/data/` |

### 1.1 The class × delivery-year rule — fixed in the PRECOMMIT before any solve (rule 21)

`pjm.csv` (Manual 18 Rev 62 §5.4.8.4(B), printed p.143–144): Steam Oil & Gas has **no default gross
ACR for DY ≤ 2025/26** and **$64/MW-day from DY 2026/27**. Model `gas_st` and `oil` both map to that
class (the D62 crosswalk, unchanged). So the convention applies to `gas_st` and `oil` in screen years
2022–2025 and to nothing else; from screen year 2026 every class has a default and the gate is inert
by the table. Asserted from the data by test (`TestThePredicateIsTheData`).

---

## 2. Phase 0 — the published record and the census (design §1–§2, zero LP)

**(1) The published record, by source doc + page** (ten documents fetched and hashed; every hash
matches the identity records already in the repo). What it SEPARATES and what it does not:

| quantity the charter asked for | separable? | source |
|---|---|---|
| the class's default cap | **YES — NONE exists through DY 2025/26**: Manual 18 Rev 62 §5.4.8.4(B), printed p.143–144, prints "NA" for Steam Oil & Gas in the *Through 2025/2026* column and $64/MW-day from 2026/27; §5.4.1 (p.125) allows an offer above $0 only on a unit-specific ACR filing "or … the default gross ACR of the applicable resource type, **if available**" | M18 |
| must-offer-at-zero (price takers), all types | YES in aggregate: 27.0 / 21.3 / 27.1 / 34.8 / 26.9 % of existing generation resources in the 2023/24–2027/28 BRAs; at most 21–72 resources of ALL types held unit-specific ACR caps | SOM 2022 §5 Table 5-14 p.331–332; 2023 Table 5-14 p.329; 2024 Table 5-16 p.312–313; 2025 Table 5-18 p.345 |
| must-offer-at-zero, by resource type | **NO** (confidentiality — SOM 2025 §5 fn 232, p.362) | — |
| FRR share of oil | YES: heavy oil 9.5 / 19.1 / 13.8 %, distillate 6.3 / 7.3 / 6.6 % (2022/23–2024/25), Table 9 − Table 7 | 2024/25 BRA Report Tables 7 (p.12) and 9 (p.14) |
| FRR share of steam | **NO** — "Gas" is one row (CC + CT + ST); FRR by type is derivable only at that grain, 11.7–13.8 % | idem |
| self-supplied share of steam / oil | **NO** — no BRA or SOM table reports self-supply by resource type; SOM Table 5-10 (2025 §5, p.328) reports load obligation by LSE class, not resources | — |
| a per-unit FRR / self-supply list | **NO** — not published (FRR commitments are zone/entity totals, BRA Table 5, p.10) | — |

Reported as NOT separable and **not proxied** (rule 14). Two validation observables the record
does give (rule 13, compared against, never entered): PJM's whole uncleared "Gas" fleet in 2022/23
was 6,234 MW UCAP of all gas types, where the model's uncleared gas-STEAM alone is 8,802; and the
oil + distillate classes cleared 94–98 % of what they offered (uncleared 429 / 120 / 353 MW across
the three years) where the model leaves 2,996 (control) / 3,723 (D62 arm) MW uncleared.

**(2) The model-side census** (committed ledgers joined to EIA-860 `vintage_2020` on
`plant_code`; D58 §2.1 reproduces the fleet table to the MW): of the 8,801.9 MW of gas-steam
uncleared in DY 2022/23, **7,565.2 MW (86 %) is sector 2 (merchant)** — Martins Creek 1,581 and
Brunner Island 1,312 (Talen), Chalk Point 1,100 (GenOn), Joliet 29 964 (NRG), Eddystone 707
(Constellation), Edge Moor 660 (Calpine), Shawville 548 — and 717.2 MW (8 %) sector 1 (AEP's Clinch
River and Big Sandy, an FRR entity). The real steam that exited (2,701.7 MW) is 1,794 MW merchant
(Joliet 29/9) and 891 MW utility (Yorktown 3). **So the charter's candidate (a), an ownership /
self-supply partition, reaches ~8 % of the object; it already exists as `retirement_sector_gate`
(D53) and its PJM leg is D58's, pre-declared the same morning.** Candidate (b), sharpened from the
manual's own "if available" limb, is the market's mechanism — design §3.

**(3) The arm's arithmetic before any solve** (`d74/phase0-2026-09-06.py`): S0 reproduces the
committed D62 arm clearing through the code path to |Δprice| ≤ 0.00024 $/MW-day and 0.0000 pt in
all four delivery years (STOP 1 not fired). S74 — the class moved into `Q_0` — predicts DY 2022/23
**46.7823 $/MW-day, position 1.0537, UNCHANGED**, `Q_0` 30,577.9 → 43,102.7 MW, uncleared coal 238 /
CC 2,052 / **CT 15,539** (from 3,086 in the same reconstruction; the ledger's 3,235.7 differs by
plateau tie-order); DY 2023/24 54.72 → 52.61 at 1.0526; 2024/25 and 2025/26 identical.

---

## 3. G-DRIFT (rule 29(b)) — **LIVE, carried from D67; form 4 void; controls at HEAD**

The charter's `5bb70047` (the D57 landing) and `a30696a0` (the D57 solve) both resolve after the
shallow clone was deepened; `f0e050e820c1159a` is a cache key. Both committed controls (D57 arm A,
the D62 arm) carry the **pre-hunk** screen peaks — `screen_peak_demand_mw` 137,706.8 / 142,664.3 /
147,800.2 / 153,121.0 / 158,633.4, identical to the digit in both — and the LIVE hunk D67 §2.2
measured is at HEAD unchanged (`DEMAND_GROWTH_RATES["PJM"]["mid"]["near"] = 0.064645`). **Form 4 is
void for both; same-HEAD controls are earned and were solved** for the screen span and, per the
D67 §7.1 precedent, for the full span. The config axis is clean (bare `aef81c84c4609c76`, D62 arm
`b98060898fceb3da` at HEAD, both matched; every ISO's default / backcast / T1-H key unmoved by this
lane — PRECOMMIT Addendum A.2). Every hunk since the D62 landing `aa5c339c` (29 files) is INERT for
this recipe — hunk-level on the seam files (`retirements.py`: D67's gated requirement resolver only;
`adequacy.py`, `avoidable_cost_rate.py` unchanged), by class elsewhere (PRECOMMIT §2's table),
including #5033's P1 basis seed (env-gated `"0"`, and `xyear_warmstart` is an explicit bool on the
forecast harness — D58 §6's grounds, re-verified at `solve.py:473-477`) and `data/datacenter.py`
(a new read-only helper; Addendum A.3). The committed ledgers remain valid as READS of what those
solves did, which is all phase 0 used them for.

---

## 4. THE SCREEN — DY 2022/23 (span 2021–2022), three legs at HEAD `64477801`

Screen year named in the PRECOMMIT §4 as the year the class's uncleared MW is largest in the D62
arm ledgers (12,524.7 MW vs 1,115.8 / 0 / 0). Three legs, PJM solo, sequential, each under the HEAD
guard: **arm** (published bar + this gate, key `cfa43af80d3b4923`), **control-P** (published bar,
`efc626966c2b5892`), **control-B** (bare, `fdba733e592eb425`) — every key as pre-computed in
Addendum A. Every number: `docs/handoffs/d74/screen-2026-09-06.json`,
`screen-reclear-2026-09-06.json`. *(One procedural disclosure: the original runner's guard tripped
after control-P because a docs-only commit — the re-clear instrument, `be313ecd → 18213f28`,
`docs/handoffs/d74/screen-reclear-2026-09-06.py` alone, no solve-path file — moved HEAD while it
solved; control-B was relaunched under a fresh guard. No solve-path byte changed between the
three legs.)*

**HEAD's requirement is the LIVE hunk's.** Both controls at HEAD screen DY 2022/23 on
`screen_peak_demand_mw` 135,090.6 and `requirement_mw` **146,816.5**, against the committed
bundles' 142,664.3 / 155,047.5 — exactly D67's −7,574 MW peak × the 1.0868 FPR. Everything below is
therefore measured arm-vs-control at the SAME requirement; the committed D62 numbers are read only
as the pre-hunk reference.

### 4.1 The clearing

| | control-B (bare, HEAD) | control-P (D62 posture, HEAD) | **arm** | committed D62 arm (pre-hunk) |
|---|---|---|---|---|
| price $/MW-day · ratio vs $50.00 | 67.7602 · 1.355 | 46.7823 · 0.936 | **41.2745 · 0.825** | 46.7823 · 0.936 |
| cleared position · Δ vs 1.0510 | 1.0483 · −0.27 pt | 1.0537 · +0.27 pt | **1.0551 · +0.41 pt** | 1.0537 · +0.27 pt |
| `how` | marginal offer (oil) | marginal offer (CT) | **curve sets price between offers** | marginal offer (CT) |
| `Q_0` price takers MW | 30,577.9 | 30,577.9 | **43,102.7** (= 30,577.9 + 12,524.8) | 30,577.9 |
| offers / uncleared | 1,370 / 676 | 1,370 / 651 | **834 / 487** | 1,370 / 649 |
| uncleared firm MW by fuel | coal 5,376 · CC 9,341 · ST 8,802 · oil 3,723 | coal 238 · CC 2,052 · **CT 11,689** · ST 8,802 · oil 3,723 | coal 238 · CC 2,052 · **CT 24,244** | coal 238 · CC 2,052 · CT 3,236 · ST 8,802 · oil 3,723 |
| `requirement_mw` · `census_mw` | 146,816.5 · 181,435.1 | 146,816.5 · 181,435.1 | **identical** | 155,047.5 · 181,435.1 |

### 4.2 The gate, leg by leg (PRECOMMIT §4; arm vs control-P)

| leg | question | result |
|---|---|---|
| **G1** | the arithmetic | **LITERAL MISS, STRUCTURAL PASS.** The pre-declared "price within ±0.05 and position within ±0.001 of control-P (the plateau absorbs it)" does NOT hold: −5.51 $/MW-day and +0.0014. The reason is the LIVE hunk, not the mechanism: at HEAD's requirement control-P clears only **12,555 MW of the 24,244 MW CT plateau** (the committed pre-hunk stack cleared 21,008), and the class moves **12,524.8 MW** into `Q_0` — 30 MW short of the whole cleared plateau — so the crossing falls off the plateau's lower edge and the curve sets the price at the quantity just below it. The structural question the gate asks — does the solve land on its own pre-solve arithmetic — is answered by re-clearing **control-P's own HEAD ledger** with the class in `Q_0` (`screen-reclear-2026-09-06.py`): **41.2746 / 1.0551 / curve-between-offers vs the arm's 41.2745 / 1.0551 / curve-between-offers — 0.0001 $/MW-day, 0.00000 pt**, and `Q_0` reproduced to 0.0 MW. Both readings are reported; the pre-declared number was computed on a requirement the hunk had already moved, and this lane does not re-read the literal miss as a pass — it is graded MISS in §6. |
| **G2** | footprint confined | **PASS** — 834 offers in the arm's stack, **834 identical** to control-P's for the same unit (offer and accredited MW), 0 changed, 0 new; **0 gas_st / oil units** in the arm's stack; `requirement_mw`, `census_mw`, `screen_peak_demand_mw`, `entry_decided_mw_by_tech` (solar 2,440.6 / wind 1,500.0), `renewable_additions`, `floor_retained` (0) and every `announced` exit row identical |
| **G3** | the identity (I2) | **PASS** — 487 uncleared offers = 487 `decided` / `entry_capped` rows, to the unit, both directions empty (no ULP boundary case this time: the price sits between offers, not on a plateau) |
| **G4** | the convention's own identity | **PASS** — zero `pipeline_events` rows at any gas_st / oil unit; the `no_default_cap_price_takers` block carries 536 units, 13,600.96 MW nameplate, **12,524.79 MW accredited** (gas_st 8,801.94 + oil 3,722.85 — the control-P stack's class MW to the kW), delivery year 2022/2023 |
| **G5** | no non-target load-bearing flip | **PASS** — entry, renewables, peak, requirement, floor identical; the 2022 `retirements` rows differ only in their `economic` members (control-P: gas_st 8,264.7 + oil 4,136.5; arm: gas_cc 2,160.1) — the admission cap's re-fill, §4.3 |

### 4.3 Composition in the screen year — the admission cap re-fills, as pre-declared

| `pipeline_events` MW (nameplate) | control-P (HEAD) | **arm** |
|---|---|---|
| `decided` | coal 258.5 · gas_st 8,264.7 · oil 4,136.5 = **12,659.7** | coal 258.5 · gas_cc 2,160.1 · **gas_ct 10,117.3** = **12,535.9** |
| `entry_capped` | gas_cc 2,160.1 · gas_ct 12,476.4 · gas_st 1,199.8 | gas_ct 15,673.8 |
| `executed` (2022) | gas_st 8,264.7 · oil 4,136.5 | gas_cc 2,160.1 |

The budget is conserved to 1 % (12,659.7 → 12,535.9 MW admitted) and re-fills from the remaining
pool exactly as PRECOMMIT §6 item 4 said: CT 10,117.3 MW inside the declared 8.5–11 GW, the whole
CC candidate block (2,160.1) admitted where control-P capped it, coal identical. The retention order
is the floor's own (cheapest-firm CT retained first, so the admitted CT is the tail of the plateau).

### 4.3b Control-B at HEAD — the shipped posture's own screen year, for the record

Control-B (bare, HEAD) clears DY 2022/23 at **67.76 $/MW-day (1.355×), position 1.0483 (−0.27 pt)**
with coal 5,376 / CC 9,341 / ST 8,802 / oil 3,723 MW uncleared; its 2022 `pipeline_events` admit
coal 5,843.8 + gas_st 7,333.7 and cap CC 10,283.2 / gas_st 2,130.8 / oil 4,136.5 (executed gas_st
7,333.7). Against the committed pre-hunk D57 arm A (76.10 · 1.0462; CC 2,052 uncleared) the LIVE
hunk alone moves the shipped posture −8.34 $/MW-day and +7.3 GW of CC uncleared — D67 §2.2's
measurement, seen from the clearing. It is the reason no pre-hunk committed bundle is a control here.

### 4.4 Resource envelope

Arm 495.6 s wall, peak RSS **9.88 GB**; control-P 510.0 s, **9.86 GB**; control-B 439.6 s, **9.88 GB**.
The D57 envelope is 14 min / 9.3 GB: every HEAD leg sits 6 % above 9.3 GB **identically**, so the
excess is HEAD's (the eGRID memo / the larger fleet path), not the arm's — STOP 7 is graded on that
reading in §7.

---

## 5. THE FULL WINDOW — 2021–2025 realized, ONE bundle per leg, all three at HEAD `d1aa877f`

**Arm** `results/hindcast/pjm-2021-2025-realized-t1h-d74-nodefaultcap/PJM/81ad0918abafe6d8/` — the
D57 recipe + `--capacity-going-forward-bar-published` + `--capacity-no-default-cap-convention`, one
`--start-year 2021 --end-year 2025` invocation, years sequential (solved 2021, 2023, 2024, 2025;
2022 the rule-22 bridge). **Control-P** (`280e7de3a9a0d1c8`) and **control-B** (`15a723ba3b6dc856`)
solved at the same HEAD, never registered, deleted before merge. *(The screen legs ran at
`64477801`; the branch was then restarted from `origin/main` `d1aa877f` — the D74 build had merged
as PR #5114 — before the full-window legs. The delta `18213f28..d1aa877f` on the PJM solve path is
MISO gas-basis code, results/cache prose and capx D65b's declared re-identification of
`ccs_retrofit_vom_adder` (8.0 → 2.95, read only by `apply_ccs_retrofit`, which returns before 2028):
INERT here, but it moves EVERY key — the pre-computed `b88464cb…` / `aef81c8…` / `b98060…` family
became `81ad0918…` / `15a723ba…` / `280e7de3…`, attributed to that flip, not this lane. All three
full-window legs solve at the new HEAD, so the A/B is internally consistent.)* Every number:
`docs/handoffs/d74/full-window-2026-09-06.json`. **Registered SUFFIXED** on the forecast namespace as
`pjm-t1h-d74-nodefaultcap` (`VERDICT_MAP`; sidecar
`frontend/data/hindcast/pjm-2021-2025-realized-t1h-d74-nodefaultcap.json`; report
`docs/hindcast-reports/pjm-2021-2025-realized-t1h-d74-nodefaultcap-2026-09-06.md`; the bundle's slim
set carved out of `.gitignore` as D57/D62's are); verdict **HOLD** (FC-3 recall band FAIL;
`docs/handoffs/d74/forecast-verdict-arm-2026-09-06.json`). The bare `pjm-t1h` stays D57 arm A.

### 5.1 The clearing, per delivery year (arm vs control-P, same HEAD)

| DY | control-B (bare) | control-P (D62 posture) | **arm** | published |
|---|---|---|---|---|
| 2022/23 price · ratio · position | 67.76 · 1.355× · 1.0483 (−0.27 pt) | 46.78 · 0.936× · 1.0537 (+0.27 pt) | **41.27 · 0.825× · 1.0551 (+0.41 pt)** | 50.00 · 1.0510 |
| 2023/24 | 67.76 · 1.985× · 1.0490 (−0.62 pt) | 46.78 · 1.371× · 1.0540 (−0.12 pt) | **46.78 · 1.371× · 1.0540 (−0.12 pt)** — identical | 34.13 · 1.0552 |
| 2024/25 | 166.48 · 5.757× · 1.0275 (−2.80 pt) | 270.99 · 9.370× · 1.0097 (−4.58 pt) | **82.69 · 2.859× · 1.0460 (−0.95 pt)** | 28.92 · 1.0555 |
| 2025/26 | 451.61 (cap) · 1.673× · 0.9423 (−6.26 pt) | 451.61 (cap) · 1.673× · 0.9179 (−8.70 pt) | **451.61 (cap) · 1.673× · 0.9607 (−4.42 pt)** | 269.92 · 1.0049 |

`R` is **identical to the MW in every year** (146,816.5 / 156,782.0 / 166,810.0 / 152,912.3), and
so is the NON-CLASS part of `Q_0` (30,577.9 / 32,652.3 → the arm's 36,375.1 in 2023 is control-P's
own 2023 value, since the arm's 2023 `Q_0` 45,177.1 − class 8,802 = 36,375.1; 27,959.7 / 24,000.2
in 2024 / 2025 — every one equal to control-P's): **STOP 5's identity holds** (§7). What moves is
the class's own MW inside `Q_0` and, from 2023 on, the census.

**2022/23** is §4. **2023/24 is identical to the cent** — the CT plateau holds the price in both arms
(the arm has 14,446 MW of CT uncleared, control-P 1,902 + 1,116 of steam). **2024/25 is where the
mechanism's propagation lands**: every offer clears in both arms and the curve is read at the
census; control-P's census is 168,431 MW (its 2022–2023 exits took out 9.46 GW of steam and 4.14 GW
of oil), the arm's is **174,481 MW (+6,050)** — the class retained minus the 6.89 GW of CT the
re-filled cap executed in 2023 — and on the downward-sloping VRR curve that is **270.99 → 82.69
$/MW-day (9.37× → 2.86× the published)**, through the census channel ALONE. 2025/26 stays at the cap
in both, the position −8.70 → −4.42 pt.

### 5.2 What the arms retire (economic, executed, GW) and what that does to FC-3

| | control-B | control-P | **arm** |
|---|---|---|---|
| economic exits by fuel | gas_st **9.464** · coal 1.189 · gas_cc 0.975 | gas_st **9.464** · oil **4.137** · gas_cc 2.258 | **gas_ct 6.888** · gas_cc 2.258 · gas_st **0** · oil **0** |
| `retire.total_gw` (actual 15.062) | 18.171 (+20.6 %, FAIL) | 22.402 (+48.7 %, **FAIL**) | **15.689 (+4.2 %, PASS)** |
| coal / gas_cc GW (actual 10.299 / 0.434) | 6.764 / 1.049 | 5.575 / 2.333 | 5.575 / 2.333 (identical) |
| gas_st GW (actual 2.702) | 10.297 (+281 %) | 10.297 (+281 %) | **0.833 (−69 %)** — dated exits only |
| oil GW (actual 0.613) | 0.051 (−92 %) | 4.188 (+584 %) | **0.051 (−92 %)** |
| gas_ct GW (actual 0.808) | 0.000 | 0.000 | **6.888 (+752 %)** — the displaced over-exit |
| unit recall ≥ 300 MW | 13/20 = 0.65 (FAIL) | 11/20 = 0.55 (FAIL) | **8/20 = 0.40 (FAIL)** |
| `false_retire` GW · share | 8.211 · 45.2 % | 13.070 · 58.3 % | **7.979 · 50.9 %** |
| release precision, economic / all | 0.121 / 0.419 | 0.148 / 0.382 | **0.026 / 0.411** |
| LOYO recall folds | 8 (0.667) / 11 (0.579) / 13 (0.684) — FAIL ×3 | FAIL ×3 | 6/12, 8/19, 8/19 — FAIL ×3 |
| T-R10a / b · BLK-10 | PASS / PASS · 1.013 GW | PASS / PASS · 1.013 GW | PASS / PASS · 1.013 GW |

**The band PASS on `retire.total_gw` is composition, not skill, and this lane says so first.**
15.689 GW lands within 4.2 % of the actual 15.062 because 6.888 GW of CT that did not retire
(actual 0.808) replaces 13.6 GW of steam and oil that did not retire either (actual 3.3), while the
10.3 GW of coal that DID retire is still under-found by 4.7 GW. The economic release lands at real
exit plants for **2.6 %** of its MW (control-P 14.8 %), and recall falls to 8/20 exactly as
pre-declared — the three Joliet steam units leave the fuel-MW pool. Rule 14: the total's band is
NOT evidence for the mechanism, and its composition is the CT plateau's, reported at full
magnitude.

### 5.3 FC-2, CO2

| FC-2 (GW; actual) | control-P | **arm** |
|---|---|---|
| gas_cc additions (8.525) | 8.118 **PASS** | **4.118 FAIL** |
| wind / solar / gas_ct / storage (1.619 / 13.066 / 0.442 / 0.283) | 3.000 / 9.762 / 1.013 / 0.000 | identical |
| shares | wind FAIL · solar FAIL · gas_cc PASS · gas_ct PASS · storage PASS | wind FAIL · **solar PASS** · **gas_cc FAIL** · gas_ct PASS · storage PASS |

**A non-target load-bearing criterion flips PASS → FAIL — FC-2 `gas_cc` — and it is the
mechanism's propagation, not a second seam:** the entry screen is a price taker at the clearing
price (D54 §4.4), and the arm's 2024/25 price is 82.69 where control-P's is 270.99, so 4.0 GW of
CC entry that control-P's dear price admitted is not admitted. Reported because the flip is real;
the solar share flips FAIL → PASS by the same arithmetic on the denominator. **CO2** 275.11 / 277.42
/ 325.26 Mt (arm) vs 275.00 / 277.36 / 325.09 (control-P): +0.04 to +0.05 %, unmoved.


### 5.5 The gate across the full span (arm vs control-P; `full-window-gate-2026-09-06.json`)

| DY | offers identical / changed | uncleared = pipeline rows | class rows | ledger block (accredited MW) |
|---|---|---|---|---|
| 2022/23 | 834 / 0 | 487 = 487 | 0 | 536 units · 12,524.79 |
| 2023/24 | 756 / 0 | 209 vs 212 — the 3 extra rows are the D62 §4.3 ULP boundary cases (`CT_CHP_PJM_EMAAC_p52149_econ`, `_p54829_econ`, `CT_PEAKER_PJM_ATSI_p2933_peak`, all `entry_capped`, none exits) | 0 | 115 · 8,801.94 |
| 2024/25 | 196 / 461 | 0 = 0 | 0 | 123 · 12,524.79 |
| 2025/26 | 196 / 461 | 0 = 0 | 0 | 123 · 10,673.27 (ELCC-class basis from 2025/26) |

The 2023 screen prices on the 2021 dispatch (2022 is the bridge), so its offers are identical to
the unit; from 2024 the screens price on a dispatch whose fleet differs (the arm keeps 13.6 GW of
steam/oil and loses 6.9 GW of CT in 2023), so 461 offers move — the propagation, not a second seam,
and none of the class is in any stack in any year.

### 5.4 Resource envelope

Arm 889.2 s, peak RSS 9.87 GB; control-P 801.4 s, 9.87 GB; control-B 746.9 s, 9.88 GB. Identical across
legs; 6 % above the D57 envelope's 9.3 GB on every HEAD leg (§4.4, §7).

---

## 6. Against the pre-declared signs (PRECOMMIT §6), graded at full magnitude

| # | pre-declared | measured (arm vs control-P, same HEAD) | grade |
|---|---|---|---|
| 1 | 2022/23 price and position UNCHANGED (±0.05 / ±0.001) | 46.78 → **41.27**, 1.0537 → **1.0551** | **MISS** — the LIVE hunk's requirement moved the CT plateau's cleared portion to 12,555 MW and the class moves 12,525 (§4.2); the structural form (re-clear of control-P's own stack) reproduces the arm to 0.0001 |
| 2 | 2022/23 uncleared: gas_st → 0, oil → 0, CT → 15,200–15,900 | gas_st **0**, oil **0**, CT **24,244** | **HIT / HIT / MISS** (the same cause: control-P at HEAD already has 11,689 uncleared CT, not 3,236) |
| 3 | 2022 pipeline rows at gas_st / oil units: ZERO | **0** | **HIT** |
| 4 | 2022 admitted re-fills to 11.5–13.5 GW, of which CT 8.5–11 | **12,535.9**, CT **10,117.3** | **HIT** |
| 5 | 2023/24 ratio down ≈ 0.04–0.08, position up ≈ 0.03–0.07 pt | **identical** (46.78, 1.0540) | **MISS** — the CT plateau holds the price at HEAD; the re-clear of the committed stack (pre-hunk) had predicted the fall |
| 6 | 2024/25–2025/26: R and non-class `Q_0` identical to the MW; census +0.5 to +3.5 GW; price DOWN via the census alone | R identical, non-class `Q_0` identical; census **+6,050 MW**; price **270.99 → 82.69, down** | **HIT on the identity and the direction, MISS on the magnitude** (the CT exits execute in 2023, one year earlier than the steam/oil they replace would have compounded) |
| 7 | FC-3: gas_st 0.8–2.0 · oil ≤ 0.10 · gas_ct 8–11 · coal 5.3–6.0 · gas_cc 0.1–2.3 · total 17.5–20.5 (no sign) · recall 8/20 · economic precision falls | gas_st **0.833** · oil **0.051** · gas_ct **6.888** · coal 5.575 · gas_cc 2.333 · total **15.689** · recall **8/20** · precision 0.148 → **0.026** | **HIT / HIT / NEAR-MISS (−1.1 GW below the band) / HIT / NEAR-MISS (+0.03) / MISS (below the band, because the CT exits are 6.9 not 8–11) / HIT / HIT** |
| 8 | FC-2 identical; CO2 ±0.3 %; HOLD | FC-2 `gas_cc` **flips PASS → FAIL** through the 2024/25 price; CO2 +0.05 %; HOLD | **MISS / HIT / HIT** |

**8 HIT · 2 NEAR-MISS · 5 MISS.** Three of the five misses share one cause the PRECOMMIT computed on
the wrong stack — the pre-hunk committed ledger rather than a same-HEAD control, which did not
exist until the screen solved it — and the other two are the propagation's magnitude (the CT exits
land a year earlier and 1.1 GW smaller than declared, and the 2024/25 census moves twice the
declared band). None is flattering: the arm's 2022/23 price moved AWAY from the published $50.

---

## 7. STOPs (PRECOMMIT §8)

| # | STOP | outcome |
|---|---|---|
| 1 | Phase-0 mismatch | **NOT FIRED** — 0.00024 $/MW-day, 0.0000 pt (§2) |
| 2 | bare / D62 key moved by THIS lane | **NOT FIRED** — both unmoved at the build HEAD with the field absent, `None`, and `{"PJM": False}` (Addendum A.2); the later move of every key is capx D65b's declared flip on `origin/main`, measured and attributed (§5) |
| 3 | any other ISO's key moved | **NOT FIRED** — all six ISOs' default / backcast / T1-H keys unmoved (Addendum A.2) |
| 4 | a residual-selected convention | **NOT FIRED** — §1.1 fixed before any solve, asserted from `pjm.csv` by test, not revisited |
| 5 | `R` or non-class `Q_0` moving in any DY; the 2024/25 price moving other than through the executed-exit census delta | **NOT FIRED** — `R` and the non-class `Q_0` identical to the MW in all four years; the 2024/25 census moved +6,050 MW (the class retained minus the CT executed) and the price by that channel alone. The magnitude exceeds the pre-declared band (§6 item 6) and is reported as a MISS there, not re-read into the STOP |
| 6 | a scalar not in `pjm.csv` | **NOT FIRED** — no scalar field exists; `check_cache_key_registration` green |
| 7 | wall / RSS beyond the D57 envelope (14 min / 9.3 GB) | **FIRED ON THE LITERAL NUMBER, NOT ATTRIBUTABLE TO THE ARM** — every HEAD leg (arm, control-P, control-B; screen and full) peaks at 9.86–9.88 GB, identically, and the arm's wall (889 s) sits between the two controls' (801 / 747 s). The 6 % excess is HEAD's, measured on the controls; recorded, not absorbed |
| 8 | any gas_st / oil unit in a pipeline row of a DY ≤ 2025/26, or absent from `Q_0` | **NOT FIRED** — zero such rows in every screen year; the ledger block carries the class's accredited MW to the kW in each |

### 7.1 The registration gate's I7 declaration (lane Y-24's ratchet)

`register_hindcast.py` refused the arm until its one invariant FAIL was declared: **I7 (reliability
floor), 2025: accredited firm 146,897 < requirement 152,912 MW.** It is declared in
`frontend/data/hindcast/invariant-failures.json` in the same commit, and the finding it belongs to
is the **2025/26 short position of every PJM T1-H leg** — the D66 census / D67 requirement object,
not this mechanism's: control-B is shorter (144,083), control-P shorter still (140,357), and the
committed D57 arm A / D62 arm sidecars carry the same I7 FAIL undeclared (147,585 / 145,855 <
150,605). The arm is the LEAST short of the three HEAD legs because it retains the class. The
BLK-10 backstop fires its 1,012.8 MW of gas_ct in 2025 on every leg identically. The pre-existing
undeclared capx ids (`pjm-2021-2025-realized-t1h-d45`, `-d45r`, `-d57-clearing`, `-d62-pubbar`,
and the d60 / golden3 rows the SCN-FIX1 charter lists) are the audit track's / D60-R4's to declare
with their own diagnoses and are left untouched here.

---

## 8. §8 RECOMMENDATION — **DO NOT ARM, as it stands**; the mechanism stays in

**What the measurement establishes.** The class's no-default-cap convention is PJM's own published
rule (§2), it is one limb of the table the model already reads, it carries zero free parameters,
and the build does exactly what the design says: the seam is pure (G2), the identity holds (G3),
the class leaves the screen and enters `Q_0` to the kW (G4), `R` and the non-class `Q_0` never move
(STOP 5), and the solve reproduces its own re-clear arithmetic to 0.0001 $/MW-day (G1 structural).
It removes the two composition defects D62 §8 named — the 9.46 GW steam over-exit that survived
every D61/D62 scenario and the 4.14 GW oil over-exit the published bar created — and it moves the
2024/25 clearing 9.37× → 2.86× the published price through the census alone. Under rule 1 a
structurally-correct mechanism is never rejected because a residual moved, and this one is not:
**it stays built, gated, tested and in the matrix.**

**Why it is still DO-NOT-ARM as it stands.** Three things, in order of weight:

1. **The pre-stated flip condition (PRECOMMIT §7) is not met on its own text.** Condition (a)
   asked for entry rows identical to control-P's on the full span; FC-2 `gas_cc` flips PASS → FAIL
   because the arm's 2024/25 price is 82.69 where control-P's is 270.99. That is the mechanism's
   propagation through capacity evolution, not a second seam — but the condition was written
   before the solve and this lane does not re-read it to pass. (D62's STOP 5 was recorded the same
   way.)
2. **Arming it alone moves the over-exit onto the CT plateau.** The admission cap's budget is
   conserved; with steam and oil out of the candidate pool it re-fills from the 24 GW of CT that
   offer exactly the published bar on zero E&AS, and 6.888 GW of CT exits against 0.808 actual —
   economic release precision 2.6 %. That plateau is D54 §6 item 1 / D61 §1.5's object (the model's
   CT E&AS is near the record's for the wrong reason: a thin price tail against a pro-forma that
   captures the whole price-duration integral), and it is a price-formation / E&AS lane's, not a
   cap lane's. Arming D74 before it makes the CT plateau the whole failing set.
3. **Five pre-declared signs miss** (§6), and though none is flattering and three trace to the
   pre-hunk stack the PRECOMMIT was computed on, a lane that promotes past its own misses is the
   thing rule 29 exists to stop.

**Draft owner card text** *(the director's to serve or not; nothing here arms anything)*:

> **Card — capx D74: arm the Steam-Oil-&-Gas no-default-cap convention for PJM?**
> D74 built `capacity_no_default_cap_convention_by_iso` (GATED default-off, zero DOF, no scalar
> field; requires the D62 published bar) and measured it at HEAD against same-HEAD controls.
> **For:** it is Manual 18's own rule for a class with no default cap ("if available", §5.4.1;
> "NA" through DY 2025/26, §5.4.8.4(B)); PJM's uncleared steam is 86 % merchant so no ownership
> partition reaches it; the seam is pure and the identity holds; gas_st exits 10.30 → 0.83 GW
> (actual 2.70) and oil 4.19 → 0.05 (actual 0.61); the 2024/25 price 9.37× → 2.86× the published.
> **Against:** the admission cap re-fills from the zero-E&AS CT plateau — gas_ct exits 0 → 6.89 GW
> (actual 0.81), recall 0.55 → 0.40, economic precision 14.8 → 2.6 %, FC-2 `gas_cc` PASS → FAIL
> through the lower 2024/25 price; 5 of 15 pre-declared signs miss. **The lane's own recommendation
> is DO-NOT-ARM as it stands**, and to route the CT plateau (the zero-E&AS operand, D61 §1.5) and
> D58 (ownership) first, then re-run this A/B on top. **The alternative the owner may prefer:**
> arm on structure now (rule 1 — the rule is the market's, and the CT displacement is a defect of
> the plateau, not of the convention), accepting that FC-3's composition becomes the CT plateau's
> until that seam is repaired. Either way the class's exits then come from the owner-filed channel
> (steps 0 / 1b), which found 0.83 of the 2.70 GW that really left — the dated-cohort gap D44
> already names.

---

## 9. What this lane does NOT close, and what it routes

1. **The CT plateau at the clearing price** — 24.2 GW of CT offering exactly the published bar on
   zero E&AS. D74 makes it the whole uncleared set in 2022/23 (24,244 MW) and the cap's only
   re-fill pool. Its home is the price-formation tail / the E&AS pro-forma (D61 §1.5, C3c), not a
   cap lane. First successor.
2. **The `oil` crosswalk** (design §6.2): model `oil` folds oil CTs and diesels into PJM's steam
   class through D62's mapping; PJM classes those under Combustion Turbine ($50) and reports them
   as "Distillate Oil (No.2)". A split is a fleet-taxonomy question for the D62 crosswalk; not
   re-mapped here.
3. **The PRECOMMIT's controls.** Three of five misses trace to signs computed on the pre-hunk
   committed stack because no same-HEAD control existed before the screen. A lane whose form 4 is
   void should compute its brackets on the screen's own control leg and add them as a PRECOMMIT
   addendum BEFORE the full window — stated as procedure for the next lane, not re-done here.
4. **The steam / oil dated cohort.** With the class off the merchant screen, its exits are the
   owner-filed channel's: 0.833 GW found of 2.702 (Joliet 29/9 and Yorktown 3 are 2,562 MW of it).
   That is D44's undated-cohort gap, now the class's only channel.
5. **D58** (ownership) composes with this gate for the 8 % that is sector-1; its own A/B is the
   place for that verdict.
6. **Every other ISO stays `U` / `·`** (rule 25): no other registry ISO publishes an elective
   technology-class default table with a class printed "NA", so there is no cell to read.

## 10. Governance attestation

**Rule 1** — structure first: the class's published offer rule chosen on Manual 18's text and the
ownership census; the price pre-declared not to move; the arm refused promotion on its own
pre-stated condition and its misses, never on the residual, and the mechanism kept. **Rule 5** — no
magic numbers. **Rules 13 / 14** — the predicate is a published market-design fact evaluated per
delivery year from the intaken table; every BRA / SOM figure is a validation observable; the
self-supply / FRR fraction of steam is reported NOT separable and not proxied. **Rule 19** — one
limb of one published table; ownership left to D53/D58; no floor, no adder; the same
`exempt_unit_ids` seam. **Rule 21** — zero DOF. **Rule 22** — 2021–2025 realized hindcast, forecast
mode; no out-of-training year solved or scored. **Rule 24** — no scalar field; both harness flags;
`run_config.json` through the resolved predicate. **Rule 25** — PJM's table, PJM's cell. **Rule
27** — every ≥300-line file edited locally, exact bytes pushed, the remote head verified equal to
the local commit after each push. **Rule 28** — base row + six cells in the build commit (merged
as PR #5114); PJM's cell re-stamped with the measured verdict here; `check_mechanism_matrix.py`
green. **Rule 29** — phase 0 zero-LP first; the screen year named from the footprint before any
solve; structural STOP-only gates, graded on their text; controls at HEAD earned by a LIVE hunk;
screen and control bundles deleted before merge (clause (c)), this document carrying every number.
**Nothing armed.**
