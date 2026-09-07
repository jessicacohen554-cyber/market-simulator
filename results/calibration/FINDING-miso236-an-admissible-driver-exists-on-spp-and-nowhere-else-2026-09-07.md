# FINDING miso-236 — the missing seam variation is a **MISSING MEASURED INPUT on SPP**, **PREDOMINANTLY IDIOSYNCRATIC on South**, **UNREACHABLE on Manitoba** (no US-BA record exists), and the model's PJM residual is **not** the diurnal-template artifact the handoff hypothesised — the real seam's residual is a template too

**Zero LP. No arm, no screen, no bundle, no registration, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22:
2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was solved, scored
or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration: `PREREG-miso236-neighbour-state-and-the-idiosyncratic-residual-2026-09-07.md`,
pushed at `92de849b` before any adjudicating quantity.** The two supplementary measurements are
governed by `ADDENDUM-miso236-sizing-and-the-spp-limb-2026-09-07.md`, pushed at `98516b69`
**before the numbers it governs**; that addendum also labels its one census disclosure as
**post-hoc** and shows arithmetically that it moves nothing. Every decision rule applied below was
fixed in one of those two documents; none was written after seeing a number.

Probe: `scripts/probes/_miso236_neighbour_state_residual_phase0.py` →
`results/calibration/_miso236_neighbour_state_residual_phase0.json`.

**Basis (PREREG §0b).** The price `P` is the **Indiana-hub RT** series (the lane's scored basis);
every OLS regressor is the **Indiana-hub DA** series (the basis the seam ladders were Q-Q derived
against). They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's
measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

---

## 0. The provenance gate cleared EXACTLY — the instrument is miso-235's, not a different one

PREREG §1 required this session's own code path to reproduce miso-235's `sigma_measured_mw` and
`sigma_resid_measured_mw` for all four seams and all three years to within 0.5 MW, on pain of
publishing nothing. **Maximum absolute deviation across all 24 values: 0.00 MW.** PJM
1,615.4 / 1,568.2; SPP 577.3 / 576.8; South 856.2 / 855.8; Manitoba 819.1 / 777.6 (2023 shown;
every year exact). So what follows decomposes miso-235's residual, not a lookalike.

## 1. The data question the handoff ordered settled FIRST — settled, and it splits four ways

> *"does a measured non-price series with a forward analogue exist for MISO's DIBAs —
> scheduled/net-scheduled interchange, tie or neighbour outage windows, neighbour state? Settle
> that BEFORE proposing anything."*

**Scheduled / net-scheduled interchange: NO, and not fetchable.** `data/raw/MISO/` holds only
Potomac SOM/IMM PDFs; there is **no MISO scheduled- or net-scheduled-interchange series in this
repository**, and misoenergy.org's workbooks are allowlist-blocked at HTTP 403
(`docs/multi-iso/miso-data-audit.md`). The only per-DIBA MISO seam series the repo holds is the
EIA-930 **actual** interchange — which is the **outcome** the LP computes and is therefore
inadmissible as an input under rule 13 `[R-MEASURED]` (PREREG §2c named it in advance).

**Neighbour state: YES for three seams, NO for the fourth**, from a source already on disk.
`data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet` carries 62 US balancing authorities with
hourly adjusted demand and net generation by fuel, on both a local and a UTC clock.

| seam | DIBAs | in EIA-930 BALANCE | absent | covered share of seam GROSS flow (2023/24/25) | **instrument?** |
|---|---|---|---|---|---|
| PJM | PJM, IESO | **PJM** | IESO | 0.816 / 0.836 / 0.841 | **YES** |
| SPP | SWPP, SPA | **SWPP, SPA** | — | 1.000 / 1.000 / 1.000 | **YES** |
| South | SOCO, TVA, AECI, LGEE, SIKE | **SOCO, TVA, AECI, LGEE** | — | 1.000 / 1.000 / 1.000 | **YES** |
| **Manitoba** | MHEB | **none** | **MHEB** | 0.000 / 0.000 / 0.000 | **NO** |

Hourly coverage of the covered BAs on the fixed 8,760 grid is **0.9999–1.0000** in every year.

**`SIKE` is nominal presence only** (ADDENDUM §C, declared post-hoc and shown inert): a `SIKE` BA
row exists from 2025-06-01 but carries **0 of 5,137** finite adjusted-demand values, so it
contributes nothing to any hour; and it carries 0.00000 / 0.00000 / 0.00006 of the South seam's
gross flow, so the covered share reads 1.000 / 1.000 / 0.99994 without it. **The South block is in
substance SOCO + TVA + AECI + LGEE.**

**Manitoba's leg is answered by DATA ABSENCE, not by a statistic.** MHEB is a Canadian entity
outside EIA's US-BA universe (as is IESO, which is why the PJM seam's coverage is 82–84 % rather
than 100 %). No neighbour-state series for the Manitoba seam exists in this repository, and none
is reachable from the sources it holds. §2 was therefore not computed for Manitoba, exactly as the
PREREG required.

## 2. THE ADJUDICATION — the three-way split of the measured residual

Two nested OLS blocks on `r_meas,s(t)` (the miso-235 §3 residual, reproduced exactly per §0), all
regressors z-scored, on the same `ok` mask: **Block B = MISO's OWN state** (net load, VRE — the
information the keeper *already has*), **Block A = NEIGHBOUR state** (the covered DIBAs' net load
and VRE — information the keeper does *not* have). The **gated** Block A is the **no-hydro**
pair, fixed in PREREG §2b before any value was seen, because neighbour hydro is dispatchable and
can itself respond to the tie.

| seam | year | `R²_B` MISO own | `R²_AB` | **`ΔR²_A`** (gated) | unexplained | `ΔR²_A` + hydro (reported) |
|---|---|---:|---:|---:|---:|---:|
| **PJM** | 2023 | 0.1243 | 0.2945 | **0.1701** | 0.7055 | 0.2099 |
| | 2024 | 0.0891 | 0.1369 | **0.0478** | 0.8631 | 0.0531 |
| | 2025 | 0.1802 | 0.3440 | **0.1638** | 0.6560 | 0.1910 |
| **SPP** | 2023 | 0.1765 | 0.5011 | **0.3246** | 0.4989 | 0.3540 |
| | 2024 | 0.1916 | 0.4388 | **0.2472** | 0.5612 | 0.2949 |
| | 2025 | 0.1608 | 0.2747 | **0.1140** | 0.7253 | 0.1252 |
| **South** | 2023 | 0.0453 | 0.1612 | **0.1158** | 0.8388 | 0.1390 |
| | 2024 | 0.0388 | 0.1147 | **0.0759** | 0.8853 | 0.0848 |
| | 2025 | 0.0501 | 0.1032 | **0.0531** | 0.8968 | 0.1847 |

Bars fixed ex ante: **ADMISSIBLE** iff `ΔR²_A ≥ 0.10` in all three years; **NO DRIVER** iff
`< 0.05` in all three; **MIXED** otherwise. **PREDOMINANTLY IDIOSYNCRATIC** iff unexplained
`≥ 0.75` in all three years.

| seam | **driver verdict** | **idiosyncratic?** | fragile? |
|---|---|---|---|
| **SPP** | **ADMISSIBLE NEIGHBOUR-STATE DRIVER IDENTIFIED** | No (0.499 / 0.561 / 0.725) | **No** |
| PJM | MIXED (2024 falls to 0.0478) | No | No |
| **South** | MIXED | **YES — 0.8388 / 0.8853 / 0.8968** | No |
| Manitoba | **NO INSTRUMENT — answered by data absence** | — | — |

**The fragility leg confirms the SPP result rather than qualifying it.** Fitting the block on one
year and evaluating on the other two gives a mean out-of-year `ΔR²_A` of **0.2235** against a mean
in-year **0.2286** — a ratio of 0.98 against a 0.5 fragility bar. The SPP increment is **not** a
per-year fit artifact. (PJM 0.0942 / 0.1272; South 0.0766 / 0.0816 — neither fragile either, but
neither reads ADMISSIBLE.)

### 2a. Which member carries SPP — and it is NOT the weak limb (ADDENDUM §B, reported not gated)

| seam | year | neighbour net load | neighbour VRE | neighbour hydro |
|---|---|---:|---:|---:|
| SPP | 2023 | **+0.3245** | **+0.2743** | +0.0023 |
| | 2024 | **+0.2456** | **+0.1929** | +0.0070 |
| | 2025 | **+0.1139** | **+0.0994** | +0.0000 |
| PJM | 2023 | +0.1681 | +0.0018 | +0.0992 |
| | 2024 | +0.0315 | +0.0281 | +0.0147 |
| | 2025 | +0.1632 | +0.0344 | +0.0497 |
| South | 2023 | +0.1068 | +0.0225 | +0.0042 |
| | 2024 | +0.0733 | +0.0121 | +0.0005 |
| | 2025 | +0.0528 | +0.0071 | **+0.0710** |

**SPP's increment rests entirely on the two cleanly-admissible members** — SWPP+SPA net load and
SWPP+SPA wind/solar — with hydro contributing **0.0023 / 0.0070 / 0.0000**, i.e. the conservative
gate cost SPP nothing. The weak limb is where the PREREG predicted it would be and where it
matters least: PJM 2023/2025 (+0.0992 / +0.0497) and South 2025 (+0.0710, the drought year), both
**excluded from every gated value**.

### 2b. Sizing — REPORTED, NOT GATED, and explicitly NEVER a tuning target (ADDENDUM §A)

`σ_supply = √(ΔR²_A) × σ_resid,measured`, against that seam's residual-σ gap
(`σ_resid,model − σ_resid,measured`), both from the committed miso-235 JSON:

| seam | year | `σ_supply` (MW) | residual-σ gap (MW) | share of gap |
|---|---|---:|---:|---:|
| **SPP** | 2023 | **328.6** | −349.9 | **0.939** |
| | 2024 | **341.7** | −440.1 | **0.776** |
| | 2025 | **207.5** | −408.9 | **0.508** |
| South | 2023 | 291.2 | −531.8 | 0.548 |
| | 2024 | 240.0 | −476.5 | 0.504 |
| | 2025 | 230.1 | −686.6 | 0.335 |
| PJM | 2023 / 2024 / 2025 | 646.8 / 329.7 / 654.0 | **−78.4 / +112.9 / −23.7** | *not meaningful* |

**PJM's share column is arithmetically explosive and is disclosed as meaningless rather than
quoted**: miso-235 established PJM's residual σ is already right-sized (ratio 0.95 / 1.07 / 0.98),
so the denominator is near zero and 8.25 / 2.92 / 27.59 says nothing about PJM. Only the SPP and
South rows carry meaning.

**This is an UPPER BOUND on what a perfect use of the block could contribute, and the ADDENDUM
fixed in advance that no successor may size, scale or tune a mechanism to make a modelled σ land
on it** (rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]`). It says whether an object is worth
chartering, never what value to give it.

## 3. Q-B — the handoff's item-3 hypothesis is **PARTIAL**: half of it holds and half of it fails

The handoff named, and explicitly did not measure, this: *"the envelope is a deterministic diurnal
template — price-aligned by construction — where the real seam's non-spread variation is
idiosyncratic. Measure it; do not assume it."* Measured, as a 12 × 24 = 288-cell (month × hod)
block, on the degrees-of-freedom **adjusted** R² fixed in PREREG §3:

| seam | year | `R²_tmpl(r_model)` | `R²_tmpl(r_measured)` | ratio |
|---|---|---:|---:|---:|
| **PJM** (gated) | 2023 | **0.5719** | 0.3899 | 1.47 |
| | 2024 | **0.5779** | 0.4354 | 1.33 |
| | 2025 | **0.5474** | 0.5172 | **1.06** |
| SPP | 2023 / 2024 / 2025 | 0.3104 / 0.2474 / **0.1567** | 0.2565 / 0.2230 / 0.1377 | 1.21 / 1.11 / 1.14 |
| South | 2023 / 2024 / 2025 | 0.3645 / 0.3481 / 0.3332 | 0.1788 / 0.1625 / 0.3735 | 2.04 / 2.14 / 0.89 |
| Manitoba | 2023 / 2024 / 2025 | 0.6036 / 0.5207 / 0.2869 | **0.7380 / 0.7205 / 0.6594** | 0.82 / 0.72 / **0.44** |

**PJM verdict: PARTIAL.** The hypothesis's **first half is CONFIRMED** — the model's PJM residual
*is* majority-diurnal-template, clearing the pre-registered `≥ 0.50` leg in all three years. Its
**second half is REFUTED** — the ratio bar was 3.0 and the measured value is 1.47 / 1.33 / **1.06**,
because **the real PJM seam's residual is a diurnal template too** (0.39 / 0.44 / 0.52), and in
2025 almost exactly as much of one as the model's. On the pre-registered rule this closes nothing
and licenses nothing; what it does is **remove the envelope template as the explanation** for
miso-235 §4b's finding that the model's PJM residual is 2.5–4.6× more price-aligned than the
measured one. That defect survives with its named cause eliminated.

**The Manitoba row is the sharpest single number in the table and it points the other way.** The
**measured** MHEB seam is *more* diurnally templated than the model's, in every year and by a
widening margin (0.7380 / 0.7205 / 0.6594 against 0.6036 / 0.5207 / **0.2869**). The one seam with
**no** neighbour-state instrument is also the one whose measured residual is most nearly a
deterministic seasonal-diurnal object — reachable, in principle, from the `(month × hod)` envelope
the model **already carries**. Reported, not chartered; §5.3 hands it forward.

SPP's template verdict is **REFUTED** (model 0.1567 < the 0.25 bar in 2025) and South's is
**PARTIAL**; both are reported, not gated (PREREG §3 gates PJM only).

## 4. What the split MEANS — three different objects, and only one is a missing input

Read across §2 and §3, MISO's interchange σ deficit is not one defect:

1. **SPP — a MISSING MEASURED INPUT, and an admissible one.** Neighbour net load and neighbour VRE
   explain **32 / 25 / 11 %** of the measured residual over and above everything MISO's own state
   explains, hold up out-of-year, rest on the clean limbs, and could account for **94 / 78 / 51 %**
   of the seam's residual-σ gap. This is the first admissible object the lane has for the deficit
   miso-235 measured.
2. **South — PREDOMINANTLY IDIOSYNCRATIC.** 84 / 89 / 90 % of its measured residual is explained
   by neither MISO's state nor its neighbours'. **No measured-state input of this class can close
   it**, which is a *closure* on this route (PREREG §2b D-4) and an independent corroboration of
   miso-234's routing of South upstream to the South-gas price-out lane.
3. **Manitoba — UNREACHABLE by this route.** No US-BA record exists for MHEB, and the sources this
   repository holds contain none. §3 says its measured residual is instead unusually deterministic.
4. **PJM — neither, and its σ was never the problem.** miso-235 established PJM's σ and residual σ
   are right-sized within 5 %; this session removes the diurnal template as the explanation for
   *which hours* its residual lands in. That object is still open and still has no named cause.

**A cross-cutting fact worth carrying: MISO's OWN state — which the keeper already has — explains
4–19 % of every seam's measured residual, and the model reproduces none of it.** `R²_B` is
0.1243 / 0.0891 / 0.1802 (PJM), 0.1765 / 0.1916 / 0.1608 (SPP), 0.0453 / 0.0388 / 0.0501 (South),
while the model's seam flow is by construction a function of its own bus price and a deterministic
envelope. That is an **unused** input, not a missing one, and it is a different kind of finding
from §4.1 — cheaper to reach and requiring no new data at all.

## 5. What is handed forward — NAMED, and NOT CHARTERED

No lever is proposed and nothing here licenses one. The PREREG fixed that before the numbers.

1. **THE SUCCESSOR'S OBJECT IS THE SPP SEAM'S NEIGHBOUR-STATE CHANNEL** — the first admissible,
   non-fragile, cleanly-limbed measured driver this lane has found for the σ deficit. Its rule-13
   `[R-MEASURED]` argument was fixed in PREREG §2c before the numbers: neighbour net load and
   neighbour VRE are produced for a forward year by the **identical construction the model already
   performs for its own zones** (a weather-year load shape scaled by growth, plus VRE capacity ×
   CF), applied to a neighbouring balancing authority — a driver, not an outcome. **What is still
   unsettled and is the successor's first zero-LP question:** what *form* an admissible mechanism
   would take, given §6.4 below. Nothing here charters one.
2. **SOUTH'S NEIGHBOUR-STATE ROUTE IS CLOSED** on this session's own pre-registered rule (D-4,
   predominantly idiosyncratic in all three years). South stays where miso-234 routed it —
   upstream, in the South-gas price-out lane (`gas_marginal_commodity_pricing` **O** /
   `gas_variable_transport` **O**, owner-court). The standing refusals
   `miso_south_firm_export_block` **G** (miso-182/185) and `miso_south_export_ladder_rt_tail`
   **R** (miso-184) are **corroborated on a third independent instrument** and never re-tested
   (rule 28(a)).
3. **MANITOBA'S RESIDUAL IS A DETERMINISM QUESTION, NOT A DATA QUESTION** (§3): its measured
   residual is 66–74 % a `(month × hod)` object while the model's has collapsed to 29 % by 2025,
   and the model already carries a measured `(month × hod)` envelope. Whether that is reachable is
   a zero-LP successor measurement. **`miso_manitoba_seam` stays CLOSED as already-armed**
   (miso-235 §3) and is **not** re-opened as a missing mechanism.
4. **PJM'S RESIDUAL PRICE ALIGNMENT SURVIVES WITH ITS NAMED CAUSE ELIMINATED** (§3). The handoff's
   hypothesis is PARTIAL: the model's residual is a template, but so is the real seam's, so the
   template is not what makes the model's residual 2.5–4.6× more price-aligned. Open, and now
   without a candidate explanation.
5. **Nothing licenses a re-derive or a damping factor** on the PJM or SPP `delta_k` ladders, which
   are derived, frozen and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`). A factor
   swept against this residual is the rule 1 `[R-STRUCT]` fitted mechanism, whatever §2b says.
6. **C3c** is untouched and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification **and an owner ruling**; no LP is authorized there and none
   was sought.
7. **The CC_REGULAR 2024→2025 shape emergence** is untouched and stays where miso-234 filed it.

## 6. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number is a solve result.
2. **`R²` here is descriptive variance share, not skill.** The only out-of-sample statistic in the
   session is the fragility leg (§2), and it is reported as such.
3. **"Non-price" is defined OPERATIONALLY, and this matters for what a successor would build.**
   `r_meas` is what is orthogonal to that seam's own **pre-registered price regressor** — a single
   hub-pair spread. The neighbour-state increment is therefore variation that spread does not
   capture; it is **not** a claim that the channel is economically non-price. Neighbour net load
   plausibly moves the tie *through* the neighbour's own scarcity and internal congestion, which a
   single-hub spread cannot resolve. **This does not affect rule-13 admissibility** (which asks
   whether the quantity regenerates from forward drivers, not whether the channel is economic) but
   it does change what §5.1's successor might be building — possibly a better neighbour price
   representation rather than a new non-price input. Stated because assuming the former would be
   the error this session exists to prevent.
4. **The model-side residual is a RECONSTRUCTION number** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839), and every §3 model column is labelled as
   one. 2024 remains the loosest year, which is also the year PJM's `ΔR²_A` collapses to 0.0478 —
   the two are reported together and neither is presented as explaining the other.
5. **The PJM seam's neighbour-state census is 82–84 %, not 100 %**, because IESO has no US-BA
   record. PJM's MIXED verdict is measured on that partial cover and is not restated as complete.
6. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
7. **MISO has no failing gate**, and nothing here proposes trading a passing one. There is no
   rubric failure anywhere in the program and this session did not invent one.

## 7. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; nothing was proposed or selected, and
§2b's sizing is declared un-targetable in advance. Rule 12 `[R-PARALLEL]`: no LP was solved;
nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement only; no measured outcome enters any solve,
and PREREG §2c fixed both the admissibility argument and the named inadmissible forms (the DIBA
interchange series itself, neighbour Net Generation as a whole, and any noise term or variance
inflator) **before** the numbers. Rule 14 `[R-ACCURATE]`: no input changed. Rule 15
`[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO keeps exactly one
registered run and the keeper's `hourly/` sidecars stay committed. Rule 19 `[R-ONE-MECH]`: no
mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO
holds no `complete` marker and no out-of-training year was solved, scored or registered. Rule 23
`[R-FROZEN-DERIVE]`: no derive re-run; §5.5 restates the freeze. Rule 24 `[R-REGISTRY]`: no field
created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and lane only. Rule 27 `[R-PUSH]`: every
pushed blob verified against local. Rule 28(a): the queue item taken is the handoff's item 2 with
its item 3, which one instrument answers; the standing adjudications this touches
(`miso_south_firm_export_block` **G**, `miso_south_export_ladder_rt_tail` **R**,
`vre_reference_rate_curtailment_grossup` **K**, `internal_congestion_split` **G**) are
**corroborated, never re-tested**, and `miso_manitoba_seam` stays closed as already-armed.
Rule 28(b): no verdict moves; evidence appended in-session. Rule 29 `[R-SCREEN]`: clause 0 in
full — zero-LP phase 0 first, and it **closed one queue leg, opened one admissible object and
refuted one named hypothesis before a single LP minute was spent**, which is the outcome the
clause exists to produce.
