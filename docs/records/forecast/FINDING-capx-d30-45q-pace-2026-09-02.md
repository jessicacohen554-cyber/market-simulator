# FINDING — capx D30: the 45Q conversion pace is the cap, and the cap is cleared by two fixed-cost legs the model's own ATB basis does not support

**Session:** D30 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d30-45q-pace`, the Phase-0 characterization of the D25 §6.4 routed question
(`FINDING-capx-d25-fc5-dispositions-2026-09-01.md` §6.4 / §4.3 mechanism 5).
**Date:** 2026-09-02 · **HEAD at launch:** `07472e7c` · **Zero solves** — every number below is
read from committed artifacts (five bundle evolution ledgers + summaries, the GOLDEN-2 FC-6
arm summaries, `run_config.json`) or reconstructed analytically from the screen's own code
(`model/capacity_evolution/ccs.py::apply_ccs_retrofit`) at the committed config values.
**Docs only** — no mechanism, no `ScenarioConfig` field, no matrix cell, no keeper / board /
verdict / marker edit; rule 28 duties fire in the repair lane this finding recommends, not here.

**Headline (the adjudication).** **DEFECT-CANDIDATE, on the fixed-cost legs — not on 45Q.**
The screen's arithmetic implements spec §5.6 faithfully, the §45Q leg is valued at statute
over the statutory window, and the cap binds in every conversion year of every dispositioned
ISO — so the modelled pace *is* `ccs_retrofit_max_gw_per_year`, exactly as D25 suspected.
What clears the bar with carbon at zero is one leg pushing (45Q at ≈ $29/MWh captured-tonne
basis, against ≈ $17/MWh of added variable cost) and two legs *not pulling* that should:
(i) `fixed_om_gas_cc_ccs` (25) sits **below** `fixed_om_gas_cc` (30) since the G-32 ATB flip
raised the host CC's FOM 12 → 30 and left the "host + capture island" value at 25, so the
retrofit is *paid* $5,000/MW-yr in fixed-cost savings instead of charged the capture island's
O&M; and (ii) `ccs_retrofit_capex_kw` (900, dollar-year unstated, `needs-citation`) is 59 % of
the capture-island increment the model's own new-build CCS carries on the ATB-2024 2026$ basis
($3,104.7 − $1,583.3 = $1,521/kW) — the very "≈ $900/kW increment makes the capture island look
nearly free" defect FF-1E repaired for new-build and explicitly left in place for the retrofit
screen. On shipped values a cleared PJM F-class retrofit pays back in **7.1 years** against the
12-year credit window at full baseload (≈ 5 years of headroom; §3); put **either** fixed-cost
leg on the model's own ATB basis and the marginal retrofit moves to the window edge (break-even
in-merit hours 5,045 → 8,395 / 8,818 of 8,760); put **both** on it and no 45Q-only retrofit ever
pays back (§3.4). The capacity-revenue leg is absent from the screen by construction (state-
invariant MW), so the D31 STOP seam does not bite (§7). **Routing: a repair-lane charter**,
identified from ATB 2024 (in-repo) and the NETL NGCC-retrofit cost study — never from the
AEO corridor (§6).

---

## 1. Charter discipline (what this lane did and did not do)

- **Read:** D25 §6.4 + §4.3 m5; spec §5.6; CLAUDE.md step 2; `parameter-citations.md`
  (every 45Q / capture / EAC row); `national-ces-eac-premium-plan-2026-07.md` §11 (the owner
  resolution the screen implements); `ces-ci-crediting-audit-2026-07.md` §3–§4.4 (the 45Q
  statute record); `ff-1e-entry-cost-atb-wiring-2026-07.md` (the new-build CCS basis fix);
  `fom-scarcity-defaults-flip-2026-07-07.md` (G-32); D23 §2 (the resolved carbon path);
  D27 (the refreshed MISO T1-H baseline); GOLDEN-2 §7.1 (the fuel-cost penalty measured live).
- **Decomposed** from committed ledgers: `results/ff-t1f-s6-pjm/ledger` (PJM, primary),
  `results/ff-t1f-s123/verify` (MISO), `results/ff-t1f-extcap/nyiso` (NYISO),
  `results/ff-t1f-s4b-ara/neiso` (NEISO t1f), `results/ff-t3-neiso-golden/bau` (NEISO golden,
  2026–2050) and the golden's four FC-6 arm summaries.
- **Not done, by charter:** no parameter, threshold, cap or credit value moved; no repair; no
  arming decision; nothing identified from the corridor distance (rule 13 `[R-MEASURED]` and
  D25's own line — the AEO divergence *motivates* the question, every number in §3–§5 is the
  model's own config or a primary-source citation check).

## 2. The screen as implemented (the object being characterized)

`apply_ccs_retrofit` (step 2 of `evolve_fleet`, before the economic-retirement screen) values,
for every `gas_cc` unit with ≥ 15 of its 40 book years left, three attainable margins over the
prior year's hourly capacity-screen price signal (`prior_results.price_signal`, which at the
committed defaults IS the raw prior-year zonal duals), per MW-yr with `avail = 1 − EFORd`:

```
mc_unabated  = hr·gas + vom + er·carbon
mc_post      = hr·(1+0.12)·gas + vom + 8 + er·(1−0.9)·carbon + 0.9·er·15
m_unabated   = Σ_t max(0, p − (mc_unabated − attr_unabated)) · avail
m_window     = Σ_t max(0, p − (mc_post − attr_post − q45))   · avail      q45 = 85 · 0.9·er
m_post       = Σ_t max(0, p − (mc_post − attr_post))         · avail
uplift_window = m_window − m_unabated − ΔFOM      ΔFOM = (25·1.0 − 30·1.0)·1000 = −5,000 $/MW-yr
uplift_post   = m_post   − m_unabated − ΔFOM
```

A unit converts when `uplift_window > 0` and the two-segment undiscounted payback
(`capex / uplift_window` if recovered inside `min(12, remaining_life)` years, else spill into
`uplift_post`) is **shorter than its remaining life**; candidates rank shortest-payback first
up to 3,000 MW/ISO/yr; `attr_*` is 0 in every committed bundle (`federal_ces_enabled=false`,
`eac_price_gas_cc_ccs=0`); `carbon` is the D23-resolved signal (0 in PJM/MISO; RGGI
$29.83/t (2028) → $67.18/t (2040) in NEISO/NYISO). Retrofit capex follows the shared CCS
Wright curve (`learning_rate` 0.10 per doubling from a 2 GW reference, +1.5 GW/yr global,
plus the ISO's own retrofits fed back). The converted unit keeps its `pmax_mw` (no parasitic
derate) and the screen carries **no capacity-revenue term** ("state-invariant for the same MW
and nets out" — the docstring's own words). The `retrofit_log` that carries the full
decomposition per unit (`margin_*`, `q45_usd_per_mwh`, `payback_years`, `delta_fom_per_mw_yr`)
is **not persisted**: the evolution ledger writes only `{unit_id, mw, from_fuel, to_fuel}`
(`results/evolution_ledger.py` schema) and the runner logs one average line. §3 is therefore
an analytic reconstruction at the committed config values, exact in every leg except
utilization, which enters as the unabated in-merit hours `H` (no forecast bundle commits
hourly prices — §8).

## 3. Leg decomposition, PJM primary (carbon = 0: 45Q alone)

### 3.1 Per-MWh legs — the in-window bid offset

Delivered gas = Henry Hub `mid` + ISO basis (`fuel_trajectories.py`: PJM +0.67, NEISO +1.10);
`er = 0.057 · hr` (`FUEL_CO2_FACTOR_PER_MMBTU`), captured `c = 0.9·er`. F-class host
(hr 6.7, er 0.382, c 0.344 t/MWh):

| ISO | year | gas $/MMBtu | carbon $/t | **45Q** `85·c` | carbon avoided `c·carbon` | fuel penalty `0.12·hr·gas` | VOM adder | transport `15·c` | Δ variable cost | **net offset, in window** | net offset, post window |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PJM | 2028 | 4.34 | 0 | **29.22** | 0 | 3.49 | 8.00 | 5.16 | 16.65 | **+12.57** | −16.65 |
| PJM | 2029 | 4.51 | 0 | 29.22 | 0 | 3.63 | 8.00 | 5.16 | 16.78 | +12.43 | −16.78 |
| PJM | 2030 | 5.15 | 0 | 29.22 | 0 | 4.14 | 8.00 | 5.16 | 17.30 | +11.92 | −17.30 |
| NEISO | 2028 | 4.77 | 29.83 | 29.22 | 10.25 | 3.84 | 8.00 | 5.16 | 16.99 | +22.48 | −6.74 |
| NEISO | 2030 | 5.58 | 34.15 | 29.22 | 11.74 | 4.49 | 8.00 | 5.16 | 17.64 | +23.31 | −5.90 |

Reading: with carbon at zero the retrofitted unit bids **$12.6/MWh below its unabated self
for 12 years and $16.7/MWh above it afterwards**. The 45Q leg is the only positive leg; it
is a per-tonne credit, so a dirtier host earns more of it (PJM 2028: H-class +11.34,
F-class +12.57, older 7.5-hr +15.03 $/MWh) — the "efficient hosts win" ranking in the code
comment is not what a per-tonne credit implies, and shortest payback in practice goes to
whichever host has the most in-merit hours. (Cf. the PJM 2028 conversion list: 8 of the 26
rows are `CC_CHP_*` tranches, several under 5 MW — §5 row 4.)

### 3.2 Per-MW-yr uplift and the fixed-cost legs

`uplift_window(H) = net offset · H · 0.95 − ΔFOM`. Exact when the unit is in merit `H`
hours in both states; a lower bound otherwise (the lower in-window bid clears extra
partial-margin hours). At `H = 8,760` it is the exact ceiling:

| leg | PJM 2028, $/MW-yr | source of the number |
|---|---:|---|
| 45Q credit stream, ceiling | `29.22 × 8760 × 0.95` = **+243,200** | `CCUS_45Q_CREDIT_PER_TON` 85 × captured |
| Δ variable cost, ceiling | `16.65 × 8760 × 0.95` = −138,600 | hr penalty + VOM adder + transport |
| = net in-window energy uplift, ceiling | **+104,600** | |
| ΔFOM (capture island going-forward fixed cost) | **+5,000** (a *saving*) | `fixed_om_gas_cc_ccs` 25 − `fixed_om_gas_cc` 30, ×1.0 multipliers |
| uplift_window ceiling | **109,600** | |
| retrofit capex, 2028 (learning-adjusted) | 783,000 | 900 × (5.0/2.0)^−0.152: tracker 2 + 1.5×2 GW |
| **payback at H = 8,760** | **7.1 yr** | vs 12-yr window, vs ≥ 15-yr remaining life |

Capex path with the ISO's own 3 GW/yr fed into the shared tracker: 2028 $783/kW · 2029
$710 · 2030 $670 · 2031 $642 · 2032 $621 (from the base $900 with no dollar-year). The
tracker's global leg is `GLOBAL_ANNUAL_DEPLOYMENT_GW["gas_cc_ccs"] = 1.5 GW/yr worldwide` —
one ISO's retrofit cap alone is twice the model's own world build rate (§5 row 9).

### 3.3 Payback against utilization, and the headroom (charter item 2)

Payback (years) of the F-class PJM retrofit by unabated in-merit hours `H`
(∞ = never recovers inside the window and the post-window uplift is negative):

| variant | year | H=5,000 | 6,000 | 7,000 | 8,000 | 8,760 | break-even H for payback = 12 (2028) |
|---|---|---:|---:|---:|---:|---:|---:|
| **shipped** (ΔFOM −$5k, capex $900) | 2028 | ∞ | 10.2 | 8.8 | 7.8 | **7.1** | **5,045 h** |
| shipped | 2030 | 10.9 | 9.2 | 7.9 | 7.0 | 6.4 | |
| ΔFOM at the ATB increment (+$35k) | 2028 | ∞ | ∞ | ∞ | ∞ | 11.2 | 8,395 h |
| capex at the ATB capture-island increment ($1,521) | 2028 | ∞ | ∞ | ∞ | ∞ | ∞ (12.1 → spills into a negative post-window uplift) | 8,818 h |
| both fixed-cost legs on the ATB basis | 2028 | ∞ | ∞ | ∞ | ∞ | ∞ | 12,167 h (> 8,760: never) |
| HR penalty 16 % (`CCUS_PARAMS` B31B) | 2028 | ∞ | 11.2 | 9.7 | 8.5 | 7.8 | 5,560 h |

**Headroom on shipped values:** a host that is in merit ≥ 5,045 h/yr unabated (58 % of hours)
clears the 12-year window in 2028; at baseload it clears with ~5 years to spare, and the
ceiling falls to 6.4 yr by 2030 as learning cuts the capex. The PJM price signal in these
years is flat (2027 load-weighted $39.18, max hourly **$60.0**, zero hours ≥ $100 — the
committed summary), so an F-class CC at `mc ≈ 6.7×4.34 + 2 ≈ $31/MWh` is in merit most
hours: the cleared set is the near-baseload CC fleet, and the marginal (cap-displaced)
candidate is not near the bar. The economics question D25 posed — "how far above the bar is
the marginal retrofit" — answers: **far, on the shipped fixed-cost legs; at or below it on
the model's own ATB basis.** The two ATB-basis rows are *citation-consistency checks* (the
values already in `NEW_ENTRY_COSTS`), not proposed parameters — §6 says what a repair is
identified from.

### 3.4 The non-PJM carbon leg, for completeness

NEISO/NYISO add ≈ $10–12/MWh of avoided RGGI cost in-window (2028–2030), which is why their
post-window offset is only −$6/MWh and turns positive once RGGI passes ≈ $48/t (2035): the
golden's 2040 conversion of the 3,000 MW new-build block fires with **q45 = 0** (2040 >
`ira_ccus_45q_last_year`) on the carbon leg alone — the sign-correct response D23 cleared,
and consistent with this decomposition. GOLDEN-2 §7.1 measured the fuel-penalty leg live:
under `gas_price_factor=1.5` the NEISO CCS fleet stalls at 9,847 vs 13,135 MW — the
penalty `0.12·hr·gas` scales with gas, exactly the third leg above.

## 4. Cap-binding census (charter item 2)

`ccs_retrofits` rows summed per ledger year, against the 3,000 MW cap (greedy pack, so a
binding year reads 2,994–3,000):

| ISO · bundle | 2028 | 2029 | 2030 | 2031 | 2032 | 2033–39 | 2040 | CC fleet 2027 → share converted by 2030 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| PJM `ff-t1f-s6-pjm` | **2,998.5** (26 rows) | **2,998.8** (9) | **2,998.0** (10) | — | — | — | — | 59,719 MW → 15.1 % |
| MISO `ff-t1f-s123/verify` (provisional, §7) | **2,998.9** (14) | **2,998.7** (30) | **2,994.0** (17) | — | — | — | — | 35,612 → 25.2 % |
| NYISO `ff-t1f-extcap` | **2,999.6** (38) | **3,000.0** (19) | **2,997.8** (11) | — | — | — | — | 11,199 → 80.3 % |
| NEISO `ff-t1f-s4b-ara` | **2,999.9** (20) | **2,999.4** (23) | **2,997.5** (15) | — | — | — | — | 10,750 → 83.7 % |
| NEISO golden `ff-t3-neiso-golden/bau` | **2,999.7** (25) | **2,998.7** (26) | **2,999.5** (12) | 1,776.5 (18) | 1,000.0 (1) | 0 | 3,000.0 (1) | 11,009 → 100 % of the eligible pool by 2032 |

**Yes: the cap binds in every conversion year in every dispositioned ISO for 2028–2030**, so
the 2030 corridor value (~9 GW everywhere, D25 §4.3 m5) is `3 × cap` with no ISO-specific
economics in it at all — the identical ~9.0 GW across four ISOs of very different size is
the signature of a binding rate limit, not of a screen discriminating. The NEISO golden shows
what happens past the pool: 2031 converts 1,776.5 of the 2,011 MW still unabated (pool-
limited, not cap-limited; the 235 MW residue never converts), then **2032 converts the 1,000
MW `gas_cc_h_class_Central` block the entry screen built unabated in 2031** — a new-build CC
whose *own* CCS variant the entry screen rejected at the ATB $1,521/kW increment is retrofitted
one year later at the $621/kW learning-adjusted retrofit capex. That is the two cost bases
arbitraging each other inside one model year (§5 row 6), and the clearest single artifact of
the defect. The FC-6 arms reproduce the census under perturbation: `carbon_plus25` and
`gaspm5` bind identically in 2028–2030; `gasup150` slips to 2,974 / 2,929 MW in 2029–2030
(the fuel-penalty leg) and stalls at 9,847 MW.

Two rows the census cannot see: ERCOT and CAISO (no committed t1f summary — D25 §2), and
every year ≥ 2031 outside NEISO (the t1f windows end at 2030).

## 5. Citation audit of the legs (charter item 3)

| # | value | where | citation on record | supports the screen's use? |
|---|---|---|---|---|
| 1 | `CCUS_45Q_CREDIT_PER_TON` = 85 $/t | `policy/ira.py` | 26 U.S.C. §45Q(a),(h) as amended by IRA §13104: $17 × 5 prevailing-wage multiplier, geologic storage (ces-ci audit §4.4); OBBBA §70522 preserved it | **Yes** — at statute, prevailing-wage assumed. Two unmodelled statutory features, neither pace-relevant on their own: the amount is inflation-indexed from 2027 (base 2025), so a real-2026$ constant is the right reading; and the credit is a *tax* credit (transferability §6418 at a market discount; elective pay §6417 for five years only for taxable owners) taken here at 100 ¢/$ |
| 2 | `ira_45q_credit_window_years` = 12 | `scenarios.py` | §45Q(a)(3)-(4), 12 years from placed-in-service | **Yes** — clipped to remaining life, two-segment payback |
| 3 | `ira_ccus_45q_last_year` = 2032 | `scenarios.py` | §45Q(d)(1) begin-construction before 2033-01-01 (commit-year gate; never truncates an earned stream) | **Yes as a gate.** Caveat: conversion is instantaneous (placed-in-service = commit year, no FEED/outage/build interval), so a 2032 commit earns 2032–2043 where a real 2032 start would earn from ≈ 2035 |
| 4 | `ccs_retrofit_capture_rate` = 0.90 | `scenarios.py` | NETL Rev 4 (2022) Case B31B (ces-ci audit §3) | **Yes.** §45Q(d)(2)(A) also requires ≥ 18,750 t/yr and ≥ 75 % capture design for an electricity-generating facility: 90 % satisfies the rate; the tonnage is a *facility*-level test the tranche-level fleet cannot express (PJM 2028 converts `CC_CHP_PJM_ComEd_p50326_committed` at 1.4 MW) — immaterial to MW, material to provenance |
| 5 | `ccs_retrofit_hr_penalty` = 0.12 | `scenarios.py` | "NETL Rev 4, 2021" (comment) — while `CCUS_PARAMS["gas_cc_ccs_90"]["heat_rate_penalty"]` = 1.16 cites the same B31B case | **Split** — one source, two values; the retrofit takes the more favorable. Sensitivity small (7.1 → 7.8 yr, §3.3) |
| 6 | `ccs_retrofit_capex_kw` = 900 $/kW | `scenarios.py` | "NETL 2021, Sargent & Lundy 2022. Lower than greenfield (~$1,400/kW) because host plant exists" — `parameter-citations.md` flags `needs-citation`; dollar-year unstated | **No.** (a) The rationale is inverted: a retrofit capture island costs *more* per kW than the greenfield increment (space, tie-ins, derate), not less; (b) the model's own new-build CCS carries the increment at **$1,521/kW** (ATB 2024, 2026$), set by FF-1E precisely because "≈ $900/kW increment … made the capture island look nearly free", with the retrofit screen recorded as "unaffected" — the un-repaired half of that fix |
| 7 | `fixed_om_gas_cc_ccs` = 25 vs `fixed_om_gas_cc` = 30 $/kW-yr | `scenarios.py` | "CC + capture island going-forward fixed cost (host CC O&M + capture O&M). Source: NETL Rev 4 / NREL ATB CCS" | **No.** A host-plus-island figure cannot be below the host: G-32 (2026-07-07) flipped the host 12 → 30 to ATB 2024 and left this field, so ΔFOM is **−$5,000/MW-yr** (a saving) where the same ATB basis in `NEW_ENTRY_COSTS` gives 71.1 − 36.1 = **+$35/kW-yr**. Also lowers the retrofitted unit's later retirement bar |
| 8 | `co2_transport_storage_cost` = 15 $/t | `scenarios.py` | "NETL 2022, Gulf Coast basis" | **Not for these ISOs.** Plan §11 item 6 already listed transport/storage geography as unmodelled ("Gulf-Coast ERCOT favorable vs heterogeneous PJM"); New England and New York have no onshore saline storage at all. One number in every ISO is a rule-25 `[R-ISO-SCOPE]` concern in the other direction — a non-neutral generic |
| 9 | `ccs_retrofit_max_gw_per_year` = 3 GW/yr/ISO | `scenarios.py` | "engineering judgment — EPC capacity constraint" (plan §11 item 6: "the 3 GW/yr/ISO cap's provenance" not modelled) | **Uncited** — and since the cap binds, the pace's provenance is exactly this value's. Internally, `GLOBAL_ANNUAL_DEPLOYMENT_GW["gas_cc_ccs"]` = 1.5 GW/yr *worldwide* while each ISO retrofits 3 GW/yr |
| 10 | `ccs_retrofit_min_remaining_life` = 15, book life 40 | `scenarios.py`, `retirements.py` | "avoids retrofitting units near retirement" | Uncited design choice; not pace-relevant while the cap binds |
| 11 | `ccs_retrofit_vom_adder` = 8 $/MWh; `EFORD["gas_cc"]` = 0.05 | | NETL 2022; NERC GADS | **Yes** |
| 12 | hurdle: undiscounted two-segment payback < remaining life | spec §5.6 | Plan §11 "defect 3" (undiscounted vs the new-build LCOE at WACC) — flagged, not resolved by Q1–Q4 | **Design choice on record**, not a defect — but it is asymmetric with the new-build CCS screen (45Q levelized at `CRF(life)/CRF(window)`), which is the other half of why the 2031 → 2032 arbitrage in §4 can happen |
| 13 | no parasitic derate (`pmax_mw` unchanged) | `ccs.py` | none — the state-invariance claim rests on it | Simplification: B31B's parasitic load is a ~14 % net-output loss the capacity/AS side never sees; secondary to the pace |

## 6. Adjudication and routing (charter item 4)

**Is cap-saturated conversion the intended reading of spec §5.6?** The spec and the owner
resolution (plan §11, 2026-07-17) intend exactly two things: that a retrofit fires whenever
it *beats staying unabated and clears its windowed payback against remaining life*, and that
"retrofits are now possible in BAU" under 45Q. Both are true of the implementation, and
nothing in the spec asserts, predicts or excludes cap saturation — the cap is a throughput
limit with cap-displaced units re-screening. So the *mechanism* is the intended reading;
the *pace* is the intended reading **only if the legs are valued as cited**, and §5 rows 6–7
show the two legs that decide the margin are not. **Verdict: DEFECT-CANDIDATE**, naming the
defective legs as `fixed_om_gas_cc_ccs` (sign-inverted ΔFOM after G-32) and
`ccs_retrofit_capex_kw` (pre-ATB basis, unstated dollar-year, inverted rationale), with
`co2_transport_storage_cost` (Gulf-Coast in every ISO) and the split HR penalty as secondary
rows in the same family. The 45Q leg is **closed with the spec cite**: statute rate, statute
window, statute deadline, correctly stacked, correctly gated.

**What a repair is identified FROM (never the corridor):**
1. **ΔFOM** — the ATB 2024 basis already in `NEW_ENTRY_COSTS` (gas_cc_ccs 71.1 vs gas_cc 36.1
   $/kW-yr, 2026$), i.e. re-derive `fixed_om_gas_cc_ccs` as host + capture-island FOM on the
   same ATB extract G-32 used for the host — an in-repo primary source.
2. **Retrofit capex** — the NETL NGCC-retrofit cost study (the "Cost and Performance of
   Retrofitting NGCC Units for Carbon Capture" series) for the retrofit-specific TPC and its
   dollar-year, reconciled to the ATB capture-island increment as the floor; Sargent & Lundy
   2022 if the comment's citation can be located. Whatever it is, it carries a dollar-year.
3. **Transport/storage** — a per-ISO value from the NETL FECM CO2 Transport Cost Model and
   the DOE NATCARB / USGS storage-resource assessments (basin-specific; "no onshore storage"
   is a legitimate value for New England/New York that the current scalar cannot express).
4. **HR penalty** — one B31B number for both CCS representations.
5. **Reporting** — persist the `retrofit_log` decomposition into the ledger the way FFR-5A
   persisted the retirement bar rows (`pipeline_events`), so the next lane reads margins
   instead of reconstructing them (§8).
The 3 GW/yr cap and the 15-year life floor stay where they are: uncited, but the charter
forbids moving them, and once the fixed-cost legs are on a cited basis the cap may stop
binding on its own — which is the honest test of whether its provenance matters.

**Scoring discipline for the repair lane:** this screen fires from 2028, so no backcast or
T1-H year can score it — D27's refreshed MISO T1-H (2021–2025) carries **zero** retrofits by
construction (`ccs_retrofit_available_year` = 2028; verified in every ledger of
`results/hindcast/miso-2021-2025-realized-t1h-d27`). The only admissible validation is
citation fidelity (rule 14 `[R-ACCURATE]`) plus the FC-6 driver-response signs, so the
repair must be a data/citation change with zero DOF, and its effect on the corridor is
reported afterwards, never targeted. Rule 28 duties (matrix row/cells for any new field)
fire in that lane.

## 7. The two seams

- **MISO / D31.** The MISO rows in §4 are S-123-V's; D31 (the MISO capacity-revenue repair,
  in flight, awaiting the Q24 PRA/RBDC files per the director ledger r#28) may re-solve them.
  They are marked provisional. Because the cap binds with years of headroom, D31 moving the
  MISO price signal cannot plausibly move the *census* verdict — but the row values are D31's
  to confirm. D27's T1-H re-measure is the current MISO baseline and is cited as such; it is
  silent on this mechanism (above).
- **The capacity-revenue leg.** It is not the driver: the retrofit screen has no capacity
  term, by construction. The pace is decided entirely by the energy-margin uplift and the two
  fixed-cost legs. No D31 handoff is needed; the one capacity-adjacent observation (row 13,
  the missing parasitic derate) belongs to the retrofit repair lane, not to D31's curve
  census.

## 8. What the PJM-primary scope could not see (honest statement)

1. **No per-unit decomposition is committed.** The screen computes it (`retrofit_log`) and
   throws it away at the ledger; the runner keeps one average. Every $/MW-yr figure in §3 is
   reconstructed from the committed config, exact in the credit, cost and FOM legs, and a
   lower bound in utilization (the in-window bid clears more hours than the unabated one).
   The ceiling row (H = 8,760) is exact.
2. **No hourly prices are committed for any forecast bundle**, so the marginal (cap-
   displaced) unit's actual in-merit hours are unknown; the flat PJM signal (max $60, zero
   hours ≥ $100) is the summary-level evidence that the cleared set is near-baseload.
3. **The eligible pool is not enumerated** — a `code`-profile lane has no fleet data, so the
   share of PJM's 59.7 GW that is ≥ 15 years from end of life is unmeasured; the census
   shows the pool is far larger than 3 × cap in PJM/MISO and exhausted by 2032 in NEISO.
4. **ERCOT / CAISO** have no committed t1f summary (D25 §2) and are outside the census.
5. **The transport-geography row (§5 row 8)** is a provenance finding, not a quantified one:
   this lane did not value the Northeast's storage gap, only noted that a Gulf-Coast scalar
   cannot.

---

*Produced 2026-09-02 (D30, Fable, zero solves, docs only). The only committed deliverable is
this finding; the reconstruction script lives in the session scratchpad and every input it
reads is named in §1–§3. Routing: repair-lane charter (§6); D31 handoff not required (§7).*
