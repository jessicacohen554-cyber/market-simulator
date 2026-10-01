# DESIGN — capx D74: the PJM "Steam Oil & Gas" below-cap offer convention — READ FROM THE PUBLISHED RECORD, it is the class's own NO-DEFAULT-CAP limb of Manual 18's sell-offer rule, not an ownership partition and not a level

**Lane:** capx D74 (director r#46), the object `FINDING-capx-d61-2026-09-05.md` §4 card (c) named
and `FINDING-capx-d62-2026-09-06.md` §5.3 / §9 item 2 widened to oil. Branch
`claude/capx-d74-pjm-steam-oil-gsxcx5` (harness-assigned; the dispatch named
`claude/capx-d74-pjm-steam-oil-convention`), fresh off `origin/main` `6887484f`, fast-forwarded to
`2eb65038` (the D58 pre-declaration merge) before this text. **Not D67**: the requirement-operand
lane is `claude/capx-d67-pjm-requirement-operand-18wzjf`, cited by branch. DATA PROFILE `pjm`.
Model Fable. **Date:** 2026-09-06. **ZERO LP.** Pushed BEFORE any mechanism code and before any
solve, with its companion `PRECOMMIT-capx-d74-pjm-steam-oil-convention-2026-09-06.md`.

**NOTHING ARMS.** One `{iso: bool}` gate lands default-off in the D57 family; no scalar field; the
A/B registers suffixed; the owner arms or declines on the pre-stated condition (PRECOMMIT §7).

---

## 0. The design in one paragraph

The object is measured, not argued: in BOTH D62 arms, to the MW, gas-steam is 8,801.9 MW uncleared
and 9.464 GW economically exited, and under the published bar oil adds 3,722.8 MW uncleared and
4.137 GW exited — while PJM's own record (§1) shows the same classes clearing almost entirely at
$50 / $34 / $29 with a median E&AS of $0 and 0 % avoidable-cost recovery. The charter offered two
candidate mechanisms. **Candidate (a), the ownership / self-supply partition, is refused on the
census** (§2): PJM's uncleared steam is **86 % merchant** (sector 2 — Talen's Martins Creek and
Brunner Island, GenOn's Chalk Point, NRG's Joliet, Constellation's Eddystone, Calpine's Edge Moor
…) and only 6 % sector-1 utility, so the D53 sector gate — which already exists and is D58's lane
— reaches ~8 % of the object, and the published record carries no per-unit self-supply list at all
(§1.4). **Candidate (b), sharpened from the published record, is the market's mechanism**: PJM
Manual 18 §5.4.1 lets a seller offer above $0 only on a unit-specific ACR filing *"or … an offer
cap based on the default gross Avoidable Cost Rate of the applicable resource type, **if
available**"*, and §5.4.8.4(B)'s table prints **"NA"** for Steam Oil & Gas through DY 2025/26. So
through the whole hindcast window the class had **no default cap**: absent a unit-specific filing —
an owner-specific, confidential operand the model does not and may not carry (rule 24) — the
class's published default offer is $0, a **price taker**, and by the D54 §3.5 identity a price
taker clears and passes: its exit is its owner's filing (steps 0 / 1b, the channels the model
already carries), never the merchant screen against a bar the market did not publish. D62's own
vintage rule filled that "NA" cell with the 2026/27 value ($64/MW-day → 23.36 $/kW-yr); D62 §5.3
then found that limb is exactly where "the published table does not repair" the class. **D74
replaces that one limb with what the table says**: no default ⇒ $0 offer ⇒ price taker ⇒
screen-exempt, through DY 2025/26; from DY 2026/27, where the table publishes $64, the class takes
the ordinary published-bar path. One mechanism (rule 19), one published boolean per class ×
delivery year, zero DOF, forward-regenerating. **Phase 0 (§4) says what it will do: the 2022/23
price and cleared position do not move at all** (46.78 $/MW-day, 1.0537 — the CT plateau at the
clearing price absorbs the 12.5 GW that leaves the offer stack), **and the uncleared set moves from
steam/oil onto the CT plateau** — the admission cap's budget is conserved, so the composition of
what exits shifts to CT. That is pre-declared as the mechanism's honest consequence, and the
CT plateau at zero E&AS is named, again, as the next object (D61 §1.5, D54 §6 item 1).

---

## 1. PHASE 0 (1) — the published record, by source doc + page

Every document was fetched this session and hashed; the hashes match the identity records the
repo already carries (`data/raw/capacity-market/auction-supply/pjm/README.md`; D54 §8; D61's
`d61/som-sources-2026-09-05.md`). None of the payloads is committed (the publication-PDF corpus
posture); every figure below is quoted with its page.

| doc | sha256 (16) | bytes |
|---|---|---:|
| PJM Manual 18 Rev 62 (`m18.ashx`) | `f188c587d5e00112` | 1,854,750 |
| 2022/2023 BRA Report | `ca9d51b9246e988e` | 844,297 |
| 2023/2024 BRA Report | `ef82660e4204c414` | 585,093 |
| 2024/2025 BRA Report | `00ddf7c9c8fcbda6` | 762,397 |
| 2025/2026 BRA Report | `6d47fb09d2052b10` | 1,834,375 |
| 2027/2028 BRA Report | `d2280c610b96dcbb` | 952,518 |
| Monitoring Analytics SOM 2022 §5 | `051a2793270b3363` | 1,765,766 |
| SOM 2023 §5 | `098beec520811d17` | 1,820,482 |
| SOM 2024 §5 | `45b31316e4633e4b` | 1,964,127 |
| SOM 2025 §5 | `0756fe4cfe813345` | 3,164,427 |

### 1.1 The rule (Manual 18 Rev 62)

- **§5.4.1, printed p.125 (PDF p.126):** *"A Capacity Market Seller submitting a sell offer for an
  existing Generation Capacity Resource … greater than $0/MW-Day must seek a unit-specific
  exception request for such sell offer by submitting Avoidable Cost Rate data to IMM and PJM 120
  days prior to the RPM Auction, or may, at its election, utilize an offer cap based on the default
  gross Avoidable Cost Rate of the applicable resource type, **if available**."*
- **§5.4.8.4(B), printed p.143–144 (PDF p.144–145):** the default-gross-ACR table — *"(ii) if
  available, the default gross ACR of the applicable resource type shown in the table below"* —
  prints **Steam Oil & Gas: "NA"** in the *Through the 2025/2026 Delivery Years* column and
  **$64/MW-day** in the *2026/2027 and Subsequent* column. This is the row already intaken at
  `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` (the README records the NA cell as
  "dropped, not guessed").

**Reading.** For DY 2022/23–2025/26 the class had no elective default. A seller of a steam or oil
unit could offer above $0 only by filing unit-specific ACR data; otherwise its offer was $0.

### 1.2 How many sellers actually filed — the IMM's offer-cap statistics (all resource types)

| BRA | resources offered | default-ACR caps | unit-specific ACR caps | **price takers (existing, $0)** | source |
|---|---:|---:|---:|---:|---|
| 2023/2024 | 1,003 | 612 (61.0 %) | 72 (7.2 %) | **271 (27.0 %)** | SOM 2022 §5 Table 5-14, p.331–332 (PDF p.33–34) |
| 2024/2025 | 964 | 715 (74.2 %) | 21 (2.2 %) | **205 (21.3 %)** | SOM 2023 §5 Table 5-14, p.329 (PDF p.35) |
| 2025/2026 | 1,119 | 729 (65.1 %) | 46 (4.1 %) | **303 (27.1 %)** | SOM 2024 §5 Table 5-16, p.312–313 (PDF p.34–35) |
| 2026/2027 | 1,293 | 735 (56.8 %) | 26 (2.1 %) | **450 (34.8 %)** | SOM 2025 §5 Table 5-18, p.345 (PDF p.41) |
| 2027/2028 | 1,351 | 929 (68.8 %) | 7 (0.5 %) | **363 (26.9 %)** | SOM 2025 §5 Table 5-18, p.345 |

(The 2022/23 BRA's own table is in the 2021 SOM §5, not fetched; the four BRAs bracketing the
window suffice for the structural point.) **A fifth to a third of PJM's existing generation
resources offer as price takers at $0 in every BRA, and at most 21–72 resources of ALL types hold
unit-specific ACR caps** — against 115 gas-steam and 421 oil units in the model's stack. The IMM
does not publish the split by resource type (its unit-type tables are "consolidated consistent with
confidentiality rules", SOM 2025 §5 fn 232, p.362). So the published record **cannot say which
steam unit filed**; it CAN say the class had no default cap and that the price-taker route is the
majority non-default route.

### 1.3 What cleared — the BRA reports' by-type tables (UCAP MW; "Gas" is CC + CT + ST, not separable)

RPM only — 2024/2025 BRA Report **Table 7, p.12**; RPM + FRR — **Table 9, p.14**; the 2025/26 and
later rows from the 2027/2028 BRA Report **Table 6, p.14** (RPM + FRR, post-ELCC basis).

| DY | class | RPM offered | RPM cleared | RPM uncleared | RPM+FRR offered | **FRR-committed = T9 − T7** | FRR share |
|---|---|---:|---:|---:|---:|---:|---:|
| 2022/23 | Oil | 2,419 | 2,271 | 148 | 2,674 | 255 | 9.5 % |
| | Distillate Oil (No.2) | 2,977 | 2,696 | 281 | 3,178 | 201 | 6.3 % |
| | Gas (all) | 75,526 | 69,292 | 6,234 | 85,562 | 10,036 | 11.7 % |
| 2023/24 | Oil | 1,901 | 1,820 | 81 | 2,350 | 449 | 19.1 % |
| | Distillate | 2,684 | 2,645 | 39 | 2,894 | 210 | 7.3 % |
| | Gas (all) | 74,552 | 70,978 | 3,574 | 85,217 | 10,665 | 12.5 % |
| 2024/25 | Oil | 2,150 | 1,899 | 251 | 2,493 | 343 | 13.8 % |
| | Distillate | 2,592 | 2,490 | 102 | 2,776 | 184 | 6.6 % |
| | Gas (all) | 73,714 | 71,489 | 2,225 | 85,469 | 11,755 | 13.8 % |
| 2025/26 | Oil (RPM+FRR) | — | — | — | 578 / 578 cleared | — | — |
| | Distillate (RPM+FRR) | — | — | — | 2,408 / 2,408 | — | — |
| | Gas (RPM+FRR) | — | — | — | 66,354 / 66,354 | — | — |

Two validation observables (rule 13 — compared against, never entered): **PJM's whole published
uncleared "Gas" fleet in 2022/23 is 6,234 MW UCAP, of all gas types, where the model's uncleared
gas-STEAM alone is 8,802 MW**; and **PJM's uncleared oil + distillate is 429 / 120 / 353 MW across
the three years, against the model's 2,996 (control) / 3,723 (D62 arm) MW.** The oil class cleared
94–98 % of what it offered.

### 1.4 What the record CANNOT separate — stated, per rule 14, not proxied

| quantity the charter asked for | separable? | what exists |
|---|---|---|
| **FRR share of steam** | **NO** — "Gas" is one row (CC + CT + ST) in every BRA table; FRR by type is derivable only at that grain (11.7–13.8 %) | Table 9 − Table 7 |
| **FRR share of oil** | YES at class grain: 9.5 / 19.1 / 13.8 % (heavy oil), 6.3 / 7.3 / 6.6 % (distillate) | Table 9 − Table 7 |
| **self-supplied share of steam / oil** | **NO** — no BRA table or SOM table reports self-supply by resource type; the SOM's Table 5-10 (2025 §5, p.328) reports load OBLIGATION by LSE class (EDCs + affiliates 56.4–57.8 %), not resource-level self-supply | none |
| **must-offer-at-zero share of steam / oil** | **NO per-type split** (confidentiality); YES as a structural fact (the class has no default cap, §1.1) and as an all-type statistic (21–35 % of existing resources are price takers, §1.2) | M18 p.144; SOM Tables 5-14/5-16/5-18 |
| **a per-unit FRR / self-supply list** | **NO** — not published; the BRA reports give FRR commitments by zone/entity totals (Table 5, p.10) only | none |

The charter said: *"if the published record cannot separate it, STOP and say so"*. It cannot
separate the self-supply / FRR fraction of steam, and this design does not proxy one. What it
CAN separate, and what candidate (b) rests on entirely, is the class-level published fact of §1.1:
**100 % of the Steam Oil & Gas class was without a default cap through DY 2025/26** — one boolean
per class × delivery year, read from a table the repo already carries.

---

## 2. PHASE 0 (2) — the model-side census that decides between the candidates (zero LP)

Instrument: the D62-arm and D57-arm-A committed ledgers joined to the EIA-860 `vintage_2020`
plant table on `Generator.plant_code` (D53 design §10's two id shapes); the D58 pre-declaration
(`PREDECL-capx-d58-2026-09-06.md` §2.1) reproduces the fleet-by-sector table to the MW.

### 2.1 Who owns the uncleared steam and oil (DY 2022/23, the D57 arm A stack, accredited MW)

| class | in stack | uncleared | sector 1 (utility) | sector 2 (IPP) | sectors 3–7 (CHP / self-gen) |
|---|---:|---:|---:|---:|---:|
| gas_st | 12,525 firm with oil | **8,801.9** | 717.2 (8.1 %) | **7,565.2 (86.0 %)** | 519.5 (5.9 %) |
| oil | | 2,996.5 (control) / 3,722.8 (D62 arm) | 412.1 / 725.3 | 2,420.4 / 2,821.4 | 164 / 176 |

The eight largest uncleared steam plants — Martins Creek 1,581 (Talen), Brunner Island 1,312
(Talen), Chalk Point 1,100 (GenOn), Joliet 29 964 (NRG/Midwest Gen), Eddystone 707 (Constellation),
Edge Moor 660 (Calpine), Shawville 548, Clinch River 428 (AEP, the one utility plant) — are seven
merchant sellers and one FRR utility. **Candidate (a) reaches 8 % of the object.**

### 2.2 The economic exits the two arms execute, by sector (nameplate MW, whole window)

| | gas_st sector 1 / 2 / 3–7 | oil sector 1 / 2 / 3–7 |
|---|---|---|
| D57 arm A (control) | 771.2 / **8,134.6** / 558.7 | — |
| D62 arm | 771.2 / **8,134.6** / 558.7 | 805.9 / **3,134.9** / 195.7 |

### 2.3 The real exits, by sector (committed target, 2021–2025)

gas_st 2,701.7 MW: sector 1 **891.4** (Yorktown 3, 882 — Dominion), sector 2 **1,794.0** (Joliet 29
units 7–8 at 660 each and Joliet 9 unit 6 at 360 — NRG; McKee Run 3, 114); oil 612.5 MW: sector 2
549.9 (61 small units; H.A. Wagner 1 132.8 the largest), sector 1 38.5. **The merchant steam that
really exited — 1.8 GW — is a fifth of the merchant steam the model exits (8.1 GW).**

### 2.4 The verdict on candidate (a)

An ownership partition is the right mechanism for the 8 %, and it already exists (`retirement_
sector_gate`, D53; its PJM leg is D58, pre-declared today at `3d37b8b5`). Building a second
partition on the same attribute here would be two mechanisms for one phenomenon (rule 19). The
self-supply / FRR flag the charter appended to it has no published per-unit source (§1.4) and, on
this census, could add at most AEP's Clinch River + Big Sandy (≈ 670 MW, already sector 1). **The
86 % is merchant, and merchant steam cleared at $50 with $0 E&AS** — which only the class's offer
rule explains.

---

## 3. THE MECHANISM — one object, stated so the build has no design choices left

### 3.1 The rule

For a screened thermal unit `g` in screen year `Y` (pricing DY `Y/Y+1`) under an ISO whose
published-bar gate (D62) is ON:

> **If the published default-gross-ACR table carries NO value for `g`'s resource class in the
> column the fixed vintage rule selects for DY `Y/Y+1`** (today: "Steam Oil & Gas" for DY ≤
> 2025/26, i.e. the limb `avoidable_cost_rate._row_for` reports as basis `"first_published"`),
> then the class's published default cap is **no cap**, `g`'s published default offer is **$0**
> (a price taker on its accredited MW `A_g` inside `Q_0`, exactly as every screen-exempt unit
> enters the D57 stack — D54 §3.2), and `g` is **exempt from the merchant screen** in that year
> (it joins the `exempt_unit_ids` seam by class × delivery year, decided nowhere else: its exit
> is its owner's filing, steps 0 / 1b).
> Otherwise `g` is screened exactly as D62 screens it (the published bar, the reactive leg).

Two consequences that are the rule's own, not choices:

- **The D54 §3.5 identity is preserved by construction.** A price taker clears; a cleared unit
  passes; an exempt unit is not in `margins` and cannot fail. Keeping the unit in the screen with
  offer $0 and a borrowed bar would make it clear at $46.78 (15.9 $/kW-yr on `A_g`) and FAIL a
  23.36 $/kW-yr bar — the identity broken, which the charter forbids. Exempt-and-price-taker is
  the only construction in which "offers $0" and "stays" agree.
- **It regenerates forward from the table (rule 13).** At DY 2026/27 the class reads $64/MW-day and
  re-enters the screen on the ordinary published-bar path; a future Manual 18 revision that
  publishes an earlier default changes `pjm.csv`, not the code. The predicate is evaluated per
  delivery year from the intaken table — never from a result.

### 3.2 What it is NOT

- **Not a level.** No weight, share, threshold, adder or haircut: one published boolean per
  class × delivery year. The ATB estimate (35 / 25 $/kW-yr) and D62's borrowed 23.36 are both
  numbers for a cell the market printed "NA"; rule 14 prefers the measured fact — that no default
  existed — over either estimate, and the exit decision goes to the channel the market actually
  uses for such a unit (the owner's filing).
- **Not a second partition.** D53/D58 decides WHO faces the screen (ownership); D74 decides what
  the published cap IS for those who do. A sector-1 steam unit is exempt under either gate and
  is counted once (the union at `exempt_unit_ids`).
- **Not D62's vintage rule re-chosen on a result.** D62 fixed "NA ⇒ first published value" ex
  ante and reported it as the unrepaired seam; D74 reads the same cell as the manual reads it —
  "if available" — and the choice is argued from §1.1's text, from §1.2's statistics and from
  §2.1's ownership census, all published, none a residual. The 2022/23 price does not move under
  it (§4), so it cannot have been selected on the price.

### 3.3 The gate (D57 family, rule 24 / 25)

`ScenarioConfig.capacity_no_default_cap_convention_by_iso: dict[str, bool] | None = None` — the
FIFTH member of the per-ISO capacity-gate family, resolved through ONE predicate
`config/capacity_market.py::resolve_capacity_no_default_cap_convention(config, iso)`, which
**requires the published-bar gate ON for the ISO** (the convention is a limb of the published
table; over an ATB bar there is no "NA" cell — the resolver returns False and logs once, the
D57-requires-curve pattern). Registered in `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` at `"None"`,
`TIER_TAGS` 1, coerced to `None` in a plain backcast, CLI `--capacity-no-default-cap-convention`
(+ `--no-`) on both harnesses, recorded in `run_config.json` through the resolved predicate beside
the raw mapping. **No scalar field exists and none may be added.** Generic in form, PJM-scoped by
data: an ISO with no intaken table has no "NA" cell and the gate is inert by construction.

### 3.4 Seam

`retirements.py::apply_economic_retirements`, the candidate loop: beside `if g.unit_id in
exempt_unit_ids: continue`, a second exemption `if no_default_armed and
no_default_cap_class(iso, g.fuel_type, year): <census>; continue`, with
`data/avoidable_cost_rate.py::no_default_cap_class(iso, fuel, delivery_year) -> bool` the one
predicate that reads the table (True iff the class has published rows but none in the DY's
vintage column). Because `_settle_capacity_supply_clearing` builds `Q_0 = accredited_total −
Σ A_g(screened)`, every exempted unit lands in `Q_0` at $0 with no second line of code (I1 holds
structurally). Ledger: one additive block `no_default_cap_price_takers = {year, units, mw,
mw_by_fuel, classes}` per screen year (`event_sink` → `evolve.py` `events`), off the gate absent
and every ledger byte-identical. `resolve_going_forward_bar_per_kw_yr` is untouched (no exempt
unit reaches it), so D62's `first_published` limb remains the D62-only posture's behaviour.

### 3.5 DOF ledger — zero

| number | source |
|---|---|
| which classes / delivery years have no default cap | `pjm.csv` (M18 §5.4.8.4(B), p.144), the D62 vintage rule's own "NA" limb |
| the offer of such a unit ($0) | M18 §5.4.1 (p.125): "greater than $0/MW-Day must … if available" |
| the exit channel of such a unit | steps 0 / 1b — the owner's filed instrument / date (existing) |

---

## 4. PHASE 0 (3) — the arm's own arithmetic before any solve (`docs/handoffs/d74/phase0-2026-09-06.{py,json}`)

**S0 — the committed D62 arm reproduced through the code path** (its ledger stacks re-cleared by
`clear_capacity_supply_stack` on `capacity_supply_curve(cfg, "PJM", year)`): 2022/23 46.7823 /
1.0537, 2023/24 54.7221 / 1.0521, 2024/25 188.5726 / 1.0226, 2025/26 451.6100 / 0.9545 —
|Δprice| ≤ 0.00024 $/MW-day, |Δposition| = 0.0000 pt in all four years. The D62 arm key resolves to
`b98060898fceb3da` at HEAD (matched) and the bare key to `aef81c84c4609c76` (matched; D58 §5 and
D67 §1(b) read the same values).

**S74 — the no-default-cap classes moved into `Q_0`** (every other offer byte-identical):

| DY | Q_0 MW (S0 → S74) | price $/MW-day | ratio vs published | cleared position | uncleared firm MW by fuel |
|---|---|---:|---:|---:|---|
| 2022/23 | 30,577.9 → **43,102.7** (+8,801.9 ST, +3,722.8 oil) | **46.7823 → 46.7823** | 0.936 → 0.936 | **1.0537 → 1.0537** (+0.27 pt) | coal 238 · CC 2,052 · ST 8,802 · oil 3,723 · CT 3,086 → coal 238 · CC 2,052 · **CT 15,539** |
| 2023/24 | 32,652.3 → 33,768.1 (+1,115.8 ST) | 54.72 → **52.61** | 1.603 → 1.541 | 1.0521 → 1.0526 (−0.26 pt) | coal 94 · ST 1,116 → coal 232 · CC 846 |
| 2024/25 | 27,959.7 (no ST/oil left in the stack) | 188.57 (identical) | 6.520 | 1.0226 | — |
| 2025/26 | 24,000.2 | 451.61 (cap, identical) | 1.673 | 0.9545 | — |

**Reading.** In 2022/23 the published-bar CT plateau sits exactly at the clearing price (every CT
offers $46.78 with zero E&AS — D62 §4.2), so the curve still crosses inside it: the price and the
cleared position are **unchanged to the fourth decimal**, and the 12,524.7 MW that left the offer
stack re-appears as CT uncleared (3,086 → 15,539; ±300 MW of tie-order on the plateau between the
reconstruction and the solve). In 2023/24 the price falls $2.11 and the position rises 0.05 pt.
**No offer-side operand of this class can move 2024/25 or 2025/26** (D61 §2d item 1, re-confirmed:
nothing of the class is left in those stacks; the census channel is the only route, §5).

**The admission cap's budget is conserved.** D62's 2022 screen admitted (`decided`) 12,659.7 MW
nameplate — gas_st 8,264.7 + oil 4,136.5 + coal 258.5 — and capped 6,927.3 (CC 2,160.1, CT
3,567.4, ST 1,199.8). Under D74 the ST/oil candidates do not exist; the pool is coal 258 + CC 2,160
+ CT ≈ 16,500 nameplate, the cap re-fills cheapest-firm-first (D58 §2.3's mechanic, measured on
this same floor), and ≈ 12–13 GW of it is admitted — necessarily ≈ 9.5–10.5 GW of CT, executed on
the CT lag. **The mechanism moves the over-exit, it does not remove it**, because the CT plateau
with zero E&AS is the D54 §6 item 1 / D61 §1.5 object and this lane does not touch it.

---

## 5. Pre-declared signs (the PRECOMMIT carries the graded form and the STOPs)

| quantity | D62 arm (committed) | **D74 arm, predicted** | direction |
|---|---|---|---|
| 2022/23 price · position | 46.78 · 1.0537 | **46.78 ± 0.05 · 1.0537 ± 0.001** | unchanged |
| 2022/23 uncleared | ST 8,802 · oil 3,723 · CT 3,236 | **ST 0 · oil 0 · CT 15,200–15,900** | moved |
| 2022 `pipeline_events` rows at Steam Oil & Gas units | 535 decided / 119 capped incl. ST+oil | **ZERO** | — |
| 2022 admitted (`decided`) MW | 12,659.7 (ST + oil + coal) | **11.5–13.5 GW, of which CT 8.5–11 GW** | re-filled |
| 2023/24 price · position | 54.72 · 1.0521 (−0.31 pt) | ratio DOWN ≈ 0.06, position UP ≈ 0.05 pt (relative to the HEAD D62-posture control) | |
| 2024/25 R · non-screened Q_0 | 166,810.0 · 27,959.7 | **identical to the MW** | STOP if not |
| 2024/25 census · price | 170,576.6 · 188.57 | census **+0.5 to +3.5 GW** (ST/oil retained 12.4 GW nameplate minus CT executed ≈ 9.5–10.5 GW); price **DOWN**, toward the bare control's 165.84 | via the census only |
| FC-3 `retire.total_gw` | 20.144 (actual 15.062) | **17.5–20.5** — no sign claimed | composition, not level |
| FC-3 gas_st | 10.297 (+281 %) | **0.8–2.0** (dated only; actual 2.702) | under-exit now |
| FC-3 oil | 4.188 (+584 %) | **≤ 0.10** (actual 0.613) | |
| FC-3 gas_ct | 0.000 | **8–11 GW** (actual 0.808) | the displaced over-exit |
| FC-3 gas_cc / coal | 0.075 / 5.575 | 0.1–2.3 / 5.3–6.0 | |
| unit recall ≥ 300 MW | 11/20 | **8/20 = 0.40** (the three Joliet steam units fall out of the fuel-MW pool; Yorktown 3 stays reachable only through the dated pool) | down |
| release precision, economic | 0.171 | **falls** (the admitted CT is 0.8 GW real) | down |
| FC-2 additions | unchanged | **unchanged** (entry is a price taker at an unchanged 2022/23 price) | |
| determination | HOLD | **HOLD** | |

Rule 14's sign line, stated: FC-3 is expected to get **worse on composition where it was already
failing** (gas_ct), better where D62 was worst (oil, gas_st), and the total is not predicted in
either direction. **None of that is the criterion.** The mechanism is adjudicated on structure —
the identity, the footprint, the published rule — and a worse band would be the expected
signature of a stack whose CT plateau sits at the clearing price with zero E&AS, not evidence
against the class's own offer rule.

---

## 6. Successors named (not built)

1. **The CT plateau at the clearing price** — the zero-E&AS CT fleet offers exactly the published
   bar and whichever units the walk reaches past the crossing fail. D61 §1.5 named the operand
   (the model's CT E&AS is near the record's for the wrong reason); D74 makes it the whole
   uncleared set. Its home is the price-formation tail (C3c) / the E&AS pro-forma, not a cap lane.
2. **The `oil` crosswalk.** D62 maps every model `oil` unit to Steam Oil & Gas; PJM classes oil
   CTs and diesels under Combustion Turbine ($50 default) and reports them as "Distillate Oil
   (No.2)". Under D74 the whole model oil class is a price taker through 2025/26 — consistent with
   the record's 94–98 % cleared, but by the crosswalk's aggregation rather than by class. A split
   of `oil` into steam vs CT/diesel is a fleet-taxonomy question for the D62 crosswalk, not for
   this lane, and is not re-mapped inside this A/B (rule 29: one mechanism per A/B).
3. **D58** (ownership) composes with this gate and is the right home for the 8 %.

## 7. Governance attestation (as designed; re-attested in the FINDING)

Rule 1 — structure first: the class's published offer rule, chosen on the manual's text and the
ownership census, pre-declared to leave the price unmoved. Rules 13 / 14 — the predicate is a
published market-design fact that regenerates per delivery year from the intaken table; every
BRA / SOM figure above is a validation observable; the self-supply / FRR fraction of steam is
reported as NOT separable and not proxied. Rule 19 — one mechanism: the "NA" limb; the sector
gate is left to D58; no floor, no adder. Rule 21 — zero DOF. Rule 24 — no scalar field. Rule 25 —
PJM's table, PJM's cell; every other shard gets `U` or `·`. Rule 28 — base row + six cells in the
build PR. Rule 29 — screen year named in the PRECOMMIT from §4's footprint; structural STOP gates;
screen/control bundles deleted before merge.
