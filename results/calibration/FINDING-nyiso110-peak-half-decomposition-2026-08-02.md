# FINDING — nyiso-110: the PEAK half decomposes into MISSING EVERYDAY RESERVE-PRICE FORMATION (dollar-for-dollar, slope ≈ 1) on top of an energy side that is ALREADY OVER-PRICED at both ends — the keeper's C3a PASS is a cancellation, the spin-online formation route is measured LIVE at the peak on the current keeper, and the flag-only arm is pre-registered

**Date:** 2026-08-02 · **Scope:** NYISO, 2023–2025, the nyiso-109 named successor
(the peak half of the compressed price distribution) · **NO LP was solved, no
keeper changed, no bundle produced, no dashboard registration** (the
nyiso-93/94/95/97/99/101/105/107 disposition — rule 15 governs completed runs;
there is none). **Probe:** `scripts/probes/_nyiso110_peak_half_decomposition.py`
(committed; sidecar measurements A–D re-run in seconds with `--no-fleet`, the
stack/dormancy measurements E rebuild one fleet per year with no LP).
**Machine output:** `results/calibration/_nyiso110_peak_half_decomposition.json`.

The handoff asked (a) for a no-LP decomposition of the peak-half miss on the
keeper's own sidecars — how much is reserve/scarcity formation vs offer-surface
level vs the systemic amplitude signature — and (b) for either ONE
pre-registered lever from the §5.5 queue or a declaration that the lane is
systemic-blocked pending the owner amplitude-criterion call. The decomposition
came back sharper than the question: at NYISO the "systemic amplitude
signature" is not a residual left after reserve formation and offer level are
accounted — **it is, to first order, the missing reserve formation itself**,
and the flat-stack energy side owns only the smaller DA-basis remainder.

---

## §0 — the verdict in one table

| # | question | result | verdict |
|---|---|---|---|
| **B** | how much of the missing trough→peak swing is reserve formation? | measured spin-reserve differential (peak − trough) covers **89 / 64 / 64 %** of the missing swing on the DA basis and **131 / 97 / 107 %** on the RT basis (upper bound); hour-level passthrough slope of the peak miss on the measured spin price ≈ **1** (DA +1.15 / +1.31 / +0.75; RT censored +0.77 / +1.02 / +1.09) | **the dominant component** |
| **B2** | what does the energy side look like once the measured reserve content is stripped? | the model **over-prices BOTH ends** (RT energy basis: trough +5.7 / +3.5 / +4.2, peak +7.3 / +3.2 / +5.3) and its energy-only swing is **117 / 97 / 107 %** of the reserve-stripped actual swing (RT; DA 92 / 79 / 68 %) | **C3a passes by CANCELLATION** |
| **B3** | is the model's own reserve pricing alive? | co-opt reserve dual > 0 in **17 / 6 / 34 hours** of 8,760 (peak-window mean $0.11 / $0.06 / $0.44) vs a measured DA spin price **> $1 in 100 %** of peak-window hours (LW mean $9.72 / $8.62 / $17.46) | **dead — the NYISO face of the cross-ISO co-opt dormancy** |
| **C** | is the peak miss events or every day? | DA miss > 0 in 51 / 63 / 81 % of peak hours; $200-censoring moves the mean by ≤ $2.2; top decile carries 48–67 % of the positive mass | **broad, everyday** (with a DJF surplus beyond reserve, §3) |
| **E1** | can the model's stack even reach the actual peak price? | actual DA peak exceeds the model's most expensive available thermal offer in **0.0 %** of peak hours (RT ≤ 1.1 %; top-of-stack $410–475); where reachable, **1.33 / 1.38 / 1.68 GW** sits priced between the model's clearing price and the actual, with 3.7–5.2 GW priced above the actual | **reachable — a traversal gap, not a missing tier** |
| **E2** | who is marginal at the model's peak? | `econ` **83.2 / 83.7 / 85.2 %** of the peak marginal set at 96–100 % detection (the same family as the trough — nyiso-109 §8's flat-stack signature reproduced on the keeper's own offers) | **traversal, not a missing tier** |
| **E3** | is the model standing lower on its stack (volume error)? | model thermal at peak = **0.936 / 0.936 / 0.933** × measured (EIA-930 gas+oil, zero-dropout-screened) — a ~0.6 GW peak thermal shortfall, the LP's perfect-foresight hydro over-peak-shaving on the absorber side (xiso-1: hydro is NYISO's largest swing absorber at 37.5 %) | **real, secondary; §5.5 item 8's territory** |
| **E4** | is the spin-online formation route live on the CURRENT keeper? | hydro alone — armed reserve-eligible, zero opportunity cost by construction (held reserve spends no water) — covers the 655 MW NYCA spin requirement in only **51.1 / 35.6 / 39.3 %** of PEAK-window hours (89.3 / 81.9 / 87.5 % of all hours; conservative min(headroom, ρ·P) basis identical) | **NOT dormant at the peak — live, peak-concentrated formation channel, slack at the trough** |
| **(b)** | lever or blocked? | see §6–§7 | **PRE-REGISTER the flag-only `nyiso_spin_reserve_online` single-delta arm (off-queue, justified; PREREG committed before any solve)** |

## §1 — A: the target statistic, restated full-year on the committed hub actual

nyiso-109's 69/49/45 % was measured on the partially-covered RTM zonal clean;
the committed `actual_lmp_hourly_NYISO.parquet` hub DA/RT covers all 8,760
hours, and the xiso-1 hour-of-day amplitude construction reproduces exactly
(hod share 0.520 / 0.509 / 0.445 vs xiso-1's 52.0 / 50.9 / 44.5 %). Windows are
nyiso-109's verbatim: trough h01–h05, peak h17–h19.

| year · basis | model swing | actual swing | share | trough err | peak err |
|---|--:|--:|--:|--:|--:|
| 2023 DA | 10.82 | 17.99 | **60.1 %** | +4.79 | −2.39 |
| 2023 RT | 10.82 | 16.20 | 66.8 % | +5.49 | +0.11 |
| 2024 DA | 11.60 | 20.18 | **57.5 %** | +2.71 | −5.88 |
| 2024 RT | 11.60 | 20.37 | 56.9 % | +3.22 | −5.55 |
| 2025 DA | 16.44 | 36.12 | **45.5 %** | +2.45 | −17.23 |
| 2025 RT | 16.44 | 38.81 | 42.3 % | +2.48 | −19.90 |

The sign-symmetric compression nyiso-109 reported, on the full-year basis: the
trough is over-priced everywhere, the peak under-priced in 2024/2025, and 2023's
peak error is ~0 — which §2 shows is itself a cancellation, not a correct peak.

## §2 — B: the reserve-formation component, measured on NYISO's own published AS prices

**Rule 25 basis.** pjm-138 measured this construction on PJM's market; nothing
transfers. The measured side here is NYISO's own posted zonal AS clearing
prices — the committed `NYISO_as_{da,rt}_<year>.csv` (OASIS damasp/rtasp
intake), `spin_10` per settlement zone mapped onto model zones by the
repo's established cascade-tier representative-zone map
(`derive_nyiso_rcpf_overlay._MODEL_ZONE_TO_NYISO_AS`), load-weighted with the
keeper's own zonal demand. `spin_10` is the top of NYISO's posted cascade — a
spin provider's price internalizes the lower products — so it is the correct
single-product opportunity-cost proxy for a reserve-capable marginal unit, and
the conservative one (the repo's 3-product "stack" convention roughly doubles
it). The model side is the keeper's own `reserve_price` sidecar column — the
co-opt family duals, folded into the energy price by construction.

**The model's reserve pricing is dead; the market's is everywhere:**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model reserve dual > 0 (hours of 8,760) | **17** | **6** | **34** |
| model dual, peak-window mean | $0.11 | $0.06 | $0.44 |
| measured DA spin, peak-window LW mean | **$9.72** | **$8.62** | **$17.46** |
| — share of peak-window hours > $1 | **100 %** | **100 %** | **100 %** |
| — $200-censored | $9.72 | $8.62 | $16.28 |
| measured DA spin, trough-window LW mean | $3.36 | $3.09 | $4.88 |
| measured RT spin, peak-window LW mean | $7.29 | $8.77 | $25.67 |
| measured DA spin, all-hours mean | $5.70 | $5.28 | $9.09 |
| measured RT spin, all-hours mean | $2.46 | $2.38 | $7.59 |

The measured content is **not** event tail: censoring at $200 moves the DA
peak-window mean by ≤ $1.2 (spin > $200 in 0.0 / 0.0 / 0.5 % of peak hours).
It is the everyday co-optimization opportunity cost the LP never forms.

**The swing arithmetic.** The reserve differential (peak-window minus
trough-window measured spin) against the missing swing (actual minus model):

| basis | | 2023 | 2024 | 2025 |
|---|---|--:|--:|--:|
| DA | reserve differential | 6.37 | 5.53 | 12.58 |
| | missing swing | 7.18 | 8.59 | 19.68 |
| | **share owned by reserve** | **88.7 %** | **64.4 %** | **63.9 %** |
| RT | reserve differential | 7.04 | 8.47 | 23.94 |
| | missing swing | 5.38 | 8.77 | 22.38 |
| | **share owned by reserve** | **130.8 %** | **96.5 %** | **107.0 %** |

**Passthrough is dollar-for-dollar.** Regressing the hourly peak-window miss on
the hourly measured spin: DA slope **+1.15 / +1.31 / +0.75**, RT $200-censored
slope **+0.77 / +1.02 / +1.09**, hour-level correlation +0.53 / +0.62 / +0.66.
A slope of ~1 is the signature of a missing *additive* component, not a
mis-scaled one; the negative DA intercepts (−8.74 / −5.41 / +3.65) are the
energy side over-pricing that §2.1 isolates.

### §2.1 — B2: the energy-basis restatement — the C3a PASS is a cancellation

Subtract the measured spin content from the actual price and the model's own
(near-zero) folded dual from its price, and compare energy-only to energy-only.
This is a **bounding** construction — the spin price passes into the LMP only
where a reserve-capable unit is marginal, so it strips *at most* the true
content — and the RT event hours over-strip (RT spin spikes co-move with RT
LMP spikes), which is why the >100 % RT cells are quoted as upper bounds and
the censored slope ≈ 1 above is the load-bearing statement.

| year | RT energy trough err | RT energy peak err | RT energy swing share | DA energy swing share |
|---|--:|--:|--:|--:|
| 2023 | **+5.74** | **+7.29** | 116.9 % | 92.1 % |
| 2024 | **+3.52** | **+3.16** | 97.0 % | 78.7 % |
| 2025 | **+4.21** | **+5.33** | 107.5 % | 68.0 % |

Read it directly: **once the measured reserve content is accounted for, the
model's energy side over-prices BOTH ends of the day by $3–7/MWh, and its
energy-only diurnal swing is ~100 % of the reserve-stripped actual swing on the
RT basis** (68–92 % on DA — the flat-stack residual survives there, §5). The
keeper's C3a PASS is therefore a cancellation: an energy side ~$3–7 too dear,
netting against ~$2.4–7.6 of reserve content it never forms. nyiso-109's §8
marginal-rung census measured the same excess from the other side — the
residual markup on the price-setting rung ($6.84 / $10.13 / $9.24).

## §3 — C: the miss is broad and everyday, with a DJF surplus beyond reserve

DA-basis peak-window miss: mean +2.39 / +5.88 / +17.23, positive in 51 / 63 /
81 % of peak hours, p50 +0.19 / +2.07 / +9.13; $200-censoring moves the mean to
+2.08 / +5.78 / +15.07. Seasonally (DA): DJF **+8.08 / +11.27 / +32.00**, JJA
+0.60 / +4.61 / +21.84, shoulder +0.49 / +3.87 / +7.66 — against measured DJF
peak-window spin of only 9.43 / 9.79 / 18.72. The winter miss **exceeds** the
winter reserve content in 2023 and 2025: a second, smaller, winter-specific
non-reserve component sits on top (the `nyiso_iroquois_winter_spread` family's
territory — see §6's queue notes; its re-arm stays blocked on its own
adjudicated joint-lever condition).

## §4 — D: the day-level view — compression is the typical day, not an average artifact

Per-calendar-day model share of the actual trough→peak swing (days with actual
swing > $1): DA median **0.577 / 0.564 / 0.459**, model below half the actual
swing on 36 / 39 / 57 % of days, inverted days ≈ 0. The compression is the
shape of the ordinary day, consistent with xiso-1's finding that no single
scarcity event drives the amplitude statistic.

## §5 — E: the stack anatomy at peak, on the keeper's own offers

One fleet reconstruction per year (`replay_keeper` → `run_year(fleet_only=True)`,
no LP), 3,401–3,410 LP rows, on the keeper's exact solved offers.

**E1 — the actual peak is INSIDE the model's stack everywhere.** The model's
most expensive available thermal offer averages $410–475 in the peak window and
the actual DA peak exceeds it in **0.0 %** of peak hours (RT: 0.0 / 0.4 / 1.1 %,
mean unreachable excess ≤ $4.13 — the C3c tail hours, already ledgered). The
peak miss is therefore **not** scarcity-beyond-the-stack. What separates the
model's clearing price from the actual is a band of **1.33 / 1.38 / 1.68 GW**
(mean; p50 0.84 / 1.00 / 1.43 GW) of available capacity priced between the two
— the model stops 1–1.7 GW short of where the real market clears, with a
further 3.7–5.2 GW priced above the actual. The stack has a top and a middle;
the LP just never needs to climb them.

**E2 — the peak marginal rung is the same `econ` family as the trough.** On
the keeper's own offers at 96.2–99.8 % detection: `econ` **83.2 / 83.7 /
85.2 %** of the peak marginal set (`committed` 9.5–10.8 %, `peak` 4.4–6.7 %),
top pairs `ST_GAS:econ` / `CC_REGULAR:econ` / `CT_PEAKER:econ` — nyiso-109 §8's
trough census read from the peak side, on the current keeper. Marginal-offer
decomposition at peak: burn $27.9 / $26.7 / $54.5, VOM ~$3.3, residual markup
**$8.24 / $12.17 / $7.78** — the markup on the price-setting rung is the same
object as §2.1's energy-basis over-pricing (+$3–7), measured from the offer
side.

**E3 — the model burns ~6.5 % less thermal at peak than NYISO did.** Model
thermal (gas+CHP+ST+oil classes) vs EIA-930 `NG: NG` + `NG: OIL`
(zero-dropout-screened per nyiso-98; 0 / 1 / 0 suspect hours): **8.07 vs 8.62 /
8.70 vs 9.29 / 8.87 vs 9.51 GW** — ratio **0.936 / 0.936 / 0.933**. A ~0.6 GW
peak thermal shortfall, about half the E1 band: the LP's perfect-foresight
monthly-budget hydro peak-shaves harder than the real river system can (xiso-1
measured hydro as NYISO's largest diurnal absorber, +1,886 MW = 37.5 % of the
model's own swing), displacing thermal the real market ran and holding the
marginal rung lower. This is the energy-side traversal leg's identified
physical driver, and it is **§5.5 item 8's territory** (`hydro_ror_split`,
blocked on the Robert Moses Niagara hybrid label) — not a new lane.

**E4 — the spin-online formation route is LIVE on the current keeper, and
peak-concentrated.** The caiso-144-pattern ex-ante dormancy census, run so a
dead route would be closed without a solve: hydro is armed reserve-eligible on
the keeper (`nyiso_hydro_reserve_eligible`), holding reserve spends no water,
so every MW of hydro headroom is a zero-opportunity-cost spinning provider —
if hydro alone covered the 655 MW NYCA spin requirement in ~every hour, any
online-gated spin family would carry zero dual at every optimum and the route
would be dormant ex-ante. **It does not:** hydro headroom covers 655 MW in
only **51.1 / 35.6 / 39.3 %** of peak-window hours (p05 peak headroom 268 /
136 / 74 MW) against **89.3 / 81.9 / 87.5 %** of all hours; the conservative
min(headroom, ρ·P) basis is identical. The gate therefore has a live
formation channel concentrated exactly in the peak window where §2's content
is missing, and is slack in the trough where the content is small — the
measured differential's own shape. Two nyiso-84-era facts are superseded by
the current keeper state, both cited against their vintage: that session
measured the gate at the **nyiso-81 HEAD, before the nyiso-108 hydro input
repair**, when the 2025 LP hydro fleet was 3 plants / 21.05 TWh — the
overnight GT-commitment forcing it recorded fired in hours the repaired
hydro fleet now covers (all-hours coverage 82–89 %), which is what confines
the gate's bite to the peak window on today's keeper.

## §6 — the lever space, adjudicated route by route

The §5.5 queue holds **no admissible peak-half lever** (item 4,
`nyiso_iroquois_winter_spread`, stays blocked on its own adjudicated joint
summer-lever condition; items 8/9b/10/11b are dispatch/scoring items, not
price-formation levers), so any lever goes off-queue with its justification
stated (rule 28a). The decomposition enumerates the routes:

1. **In-LP reserve formation via the spin-online gate — LIVE, and the chosen
   lever.** `nyiso_spin_reserve_online` exists, is default-off, carries the
   product-definition driver (spinning = synchronized supply; ASM §2), a
   published all-hours requirement (655 MW NYCA spin, static in the measured
   as-enforced series all three years), and a forward story (regenerates from
   the published requirement + the fleet's online state; the ρ multiplier is a
   fleet property). nyiso-84 adjudicated it **as a C3c-depth lever only** —
   "binds massively, moves C3c zero hours" — and named a class-widening
   prerequisite for any promotion case. **Both halves are superseded by new
   evidence** (the DO-NOT-REDO discipline's own re-open condition): (a) the
   target is new — §2's everyday $2.4–7.6/MWh formation gap, which nyiso-84
   never scored, not the >$300 tail; (b) the supply state is new — the census
   was run at the pre-hydro-repair HEAD (2025 hydro: 3 plants), and E4 on the
   repaired keeper shows the overnight forcing objection no longer reaches
   (hydro covers 82–89 % of all hours) while the peak window is genuinely
   short. The flag-only arm is a **zero-new-DOF single delta** — no code
   change, no new ScenarioConfig field, no new derive.
   `PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md` (committed and
   pushed before any solve) carries the gates; §7 states the level-collision
   risk it must survive.

2. **The nyiso-84 class-widening build (online CC/steam governor headroom)** —
   stays the named successor **behind** the flag-only arm, not beside it: it
   needs a new eligibility scope, a measured ramp-limited headroom fraction
   per class (a new derive), and a new ScenarioConfig field — a real build
   with its own identification burden. If the flag-only arm forms with the
   right shape but insufficient level, that is the evidence that charters the
   build; if the arm is inert or wrong-shaped, the build inherits the
   refutation burden.

3. **Measured reserve-offer surface — REFUSED on identification.** NYISO
   publishes reserve clearing prices, not reserve offers (no 60-Day-equivalent
   disclosure of any kind — the same absence already established for energy
   offers by the WP-3 bridge derivation). An availability adder sized to the
   measured reserve price would feed the scored outcome back in as an input
   (rule 13's forbidden move) and any hand level is a fitted scalar (rule 21).

4. **ERCOT-style measured AS-MW withholding (`as_reserve_withholding`) —
   REFUSED on rule 19.** The co-opt already withholds the requirement volume
   in-LP; removing measured cleared MW from headroom on top would
   double-withhold the same phenomenon. The missing object is the PRICE
   content, not the volume.

5. **MIP commitment — forbidden** (P2 archived; no-MIP mandate). The co-opt
   dormancy's LP-vs-MIP root is cross-ISO (pjm-138 owner-closed it for PJM;
   rule 25 keeps that closure PJM's own), and the spin gate is precisely the
   LP-representable proxy NYISO's own machinery already carries.

6. **Congestion / interface limits — G** (nyiso-109, on NYISO's own P-32
   measurement); **DA virtuals — G** (nyiso-94); **TSA derate — G** (nyiso-95).
   Unchanged, not re-opened.

7. **The energy-side traversal leg** (the DA-basis residual after reserve:
   ~11 / 36 / 36 % of the missing swing; E3's ~0.6 GW hydro over-peak-shave)
   — attributed to §5.5 item 8 (`hydro_ror_split`, blocked on the Robert
   Moses classification) and to the flat within-day offer surface nyiso-109 §8
   measured (σ = $0.000000). No NYISO instrument exists for hour-varying
   offer conduct (no offer disclosure), so that half remains carried by the
   systemic xiso-1 row; **the winter surplus beyond reserve** (§3: DJF miss
   exceeds DJF spin content in 2023/2025) is item 4's blocked territory.

**The C3a un-cancellation arithmetic, stated ex-ante (the level story both
ways, per xiso-1's rule (b)).** C3a is scored rt_lw: actual 32.30 / 38.20 /
66.53, keeper +7.51 / −0.55 / −9.64 %. The measured RT spin content
(all-hours mean, the upper bound a perfectly-formed model would add):
$2.46 / $2.38 / $7.59 ⇒ full-content C3a would land ≈ **+15.1 / +5.7 /
+1.8 %** — 2025 is FIXED toward band-center, 2024 stays in-band, and **2023
breaches** (+10 crossed once ≥ ~33 % of its measured content forms). A
formation lever therefore predictably improves the failing-direction year and
pressures the passing one — the un-cancellation signature. The arm's actual
formation is an empirical question (the LP forms duals from its own scarcity,
not from the measured series), which is exactly what the pre-registered
C3a-2023 kill gate exists to adjudicate honestly: if it fires, the record
shows the structurally-correct mechanism colliding with a level gate that
passes today by cancellation — the sharpest possible input to the owner's
open amplitude-criterion call.

## §7 — what this does and does not license, and the owner call (surfaced, not decided)

**Licensed:** the flag-only single-delta arm behind its own pre-registration
(§6.1), scored on the EXISTING criteria with the amplitude REPORTED, never
gated — the rubric is not this session's to change.

**Not licensed:** any adder, multiplier, or reserve-offer level sized to the
measured reserve price or to the residual (rules 5/13/21); any second
mechanism stacked on the same phenomenon (rule 19 — the co-opt owns reserve
pricing and the gate is its supply-side scoping, not a new channel);
re-opening the congestion, DA-virtual, or TSA routes (G, unchanged); reading
this decomposition as transferring to any other ISO (rule 25 — the pjm-138
analogue was measured on PJM's data, this on NYISO's; the shared signature is
a question each lane answers itself).

**The OWNER CALL, surfaced and sharpened, not decided.** xiso-1 filed whether
the rubric should carry a diurnal-amplitude criterion; neiso-74 filed it
first. This decomposition adds the sharpest fact yet: **at NYISO the current
level criterion C3a passes by cancellation** — an energy side ~$3–7 too dear
netting against ~$2.4–7.6 of reserve content the model never forms — so the
level gate does not merely fail to SEE the amplitude defect (xiso-1's §6
point), it actively PENALIZES the structurally-correct repair: forming the
missing reserve content un-cancels 2023 and predictably breaches +10 % once
formation reaches ~a third of the measured content, while fixing the
failing-direction 2025. Whatever the arm returns, that structure is now
measured and on the record for the call. The rubric was NOT changed and no
amplitude number is gated anywhere in the pre-registration.

## §8 — governance record and DO-NOT-REDO

Rule-28 duties discharged in this session: `nyiso_rcpf_family` NYISO note
extended (the spin-gate disposition updated on the new evidence, cell stays
K), `energy_reserve_coopt` NYISO note gains the dormancy sizing (17 / 6 / 34
dual-hours vs the measured 100 %-of-peak-hours content — the pjm-138
construction on NYISO's own data), `diurnal_price_amplitude` NYISO cell stays
**O** with the decomposition recorded (the lane is active behind a
pre-registration, not blocked), and the matrix header is re-stamped. §5.5's
header and lever queue updated; `docs/calibration-log/nyiso.md` gains the
nyiso-110 entry. **No dashboard registration from the diagnosis itself** (no
run was solved when this finding was written); the pre-registered A/B that
follows registers BOTH arms whatever the verdict (rule 15), all three years
in one bundle each (rule 16), with any keeper promotion needing the LOYO
scoring rule 22 demands and the full post-step chain
(rebuild-benchmark → legitimacy_diagnostics → dashboard_add_run →
calibration_verdict → build_status).

**DO-NOT-REDO (binding on successors):**

- **Do not re-measure the peak-half decomposition** — re-run
  `scripts/probes/_nyiso110_peak_half_decomposition.py` (A–D in seconds with
  `--no-fleet`; E rebuilds fleets, no LP). It reads the keeper store's
  CURRENT bundle path via `--bundle`, so it re-reports against a new keeper.
- **Do not read the 2023 near-zero peak error as a correct peak.** §2.1: it is
  +7.3 of energy-side over-price cancelling −9.7 of missing reserve content.
  Judge peak-half work on the DECOMPOSED halves, never the net.
- **Do not size a reserve lever from the measured spin price** — it is the
  validation target (rule 13), and §6.3 closes the offer-surface reading of
  it on identification.
- **Do not treat E4's liveness as a promotion promise.** It rules out the
  ex-ante dormancy closure; the formation level and shape are the arm's to
  measure, and the C3a-2023 collision is pre-registered as a kill, not a
  surprise.
- **Do not stack the E3 hydro over-peak-shave onto this lane** — it is §5.5
  item 8 (`hydro_ror_split`), blocked on the Robert Moses classification, and
  arming anything there from this lane would cross rule 19.
- Carried forward unchanged and still binding: nyiso-109's §8 census facts
  (within-day offer σ = $0.000000; the trough marginal-rung identity),
  xiso-1's DO-NOT-REDO on re-measuring cross-ISO amplitude, and every
  nyiso-93/94/95/97/99/101/105/106/107 closure.

## §9 — reproduction

```
PYTHONPATH=.:src python scripts/probes/_nyiso110_peak_half_decomposition.py \
    --bundle results/calibration/nyiso109_zonalanchor_B \
    --out results/calibration/_nyiso110_peak_half_decomposition.json
```

Measurements A–D read only committed artifacts and run in seconds
(`--no-fleet`). Measurement E rebuilds the keeper's fleet per year via
`replay_keeper` → `run_year(fleet_only=True)` — one reconstruction per year,
no LP, run sequentially; a fresh container needs `pip install -e .`, the
pinned wheels, and a full `scripts/regenerate_clean.py` first (the nyiso-108
environment note).

---

## §10 — ADDENDUM (same session, post-solve): the pre-registered arm is INERT, and the E4 liveness reading is corrected

The A/B ran at the rebased HEAD (both arms after the ercot-150 landing;
registered `2026-08-01-nyiso110-control-zerodelta` /
`2026-08-02-nyiso110-spin-online-inert`; gate scorer
`scripts/probes/_nyiso110_spin_online_ab.py`, output
`results/calibration/_nyiso110_spin_online_ab.json`).

**Verdict: INERT, by the prereg's own K3 rule.** K1/K4 pass (the flag is armed
and recorded, exactly one config delta); K2 passes at **0.0 MW** max
class-hour delta (the control byte-reproduces the committed keeper — main's
ercot-150 commits are NYISO-inert, as the prereg's falsifiable expectation
stated); and the arm's reserve-dual hours are **IDENTICAL to control**
(17/6/34 of 8,760 against the 500/yr liveness floor). C3a moves **+0.006 pp**
(2023), swing shares are unchanged to 3 dp, and the class-energy deltas
(≤ 4 GWh) plus K6's sub-$2 single-hour dual wobbles are degenerate-vertex
noise from an added-but-never-binding constraint, not signal. No kill fired
and none was needed — there is nothing to kill.

**The E4 census tested the wrong binder — corrected on the record (the
nyiso-109 §7 discipline).** E4 measured hydro *headroom* (the per-gen
constraint) short of 655 MW in 49–64 % of peak hours and read that as a live
formation channel. The as-built class-2 gate is an **aggregate** row —
`R[2] ≤ ρ·Σ P` over the eligible fleet — and reserve-eligible hydro's
**output** alone (2–5 GW × ρ ≥ 0.5) keeps it slack in every hour of all
three years, while idle quick-start capacity remains admissible on the
per-gen side once the aggregate row is satisfied. The "conservative
min(headroom, ρ·P)" leg applied the composition to hydro alone instead of to
the pool, which is why it did not catch this. nyiso-84's observed binding
(652–1,589 h gate-only) was real at ITS HEAD because that fleet state
differed; on today's keeper the construction cannot bind.

**The refutation generalizes past the flag — the in-LP reserve-formation
family at NYISO is exhausted:**

* the **nyiso-84 class-widening successor is refuted ex-ante** by the same
  arithmetic: adding online CC/ST to the eligible set only ADDS aggregate
  output and per-gen headroom (more slack, not less);
* a **per-gen re-scoping** (`R_g ≤ ρ·P_g`) stays slack on hydro's own
  certified output, and **excluding hydro** would falsify its real NYISO
  reserve eligibility (rule 14) to manufacture a binding constraint (rule 1);
* **reserve offers** remain unidentifiable (§6.3) and **MIP** remains
  forbidden (§6.5).

Reality prices everyday spin positively DESPITE abundant zero-opportunity
hydro because providers submit availability offers and the RT co-opt prices
sub-hourly opportunity costs — neither exists in an hourly LP with $0
reserve offers, and NYISO publishes no offer data to measure. **The peak
half's dominant component is therefore not formable in-model at NYISO under
current rules.** `diurnal_price_amplitude` NYISO moves **O → G** (the
PJM/MISO no-build class): the decomposition stands, every route is
adjudicated on NYISO's own solved or measured evidence, and the lane
re-opens only behind (i) the owner amplitude-criterion call (§7 — now
carrying the cancellation fact AND this exhaustion), (ii) an owner-funded
reserve-offer / sub-hourly data intake, or (iii) the item-8 Robert Moses
resolution for the separate energy-side hydro leg. Keeper unchanged:
`2026-08-01-nyiso109-zonal-margin-anchor`. The owner's structural-integrity
promotion license (offered for this arm) has nothing to attach to — the arm
changes no structure and is not recommended as a keeper.
