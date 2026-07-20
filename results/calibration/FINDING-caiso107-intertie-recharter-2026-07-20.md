# FINDING (caiso-107): both re-chartered intertie lanes are NOT READY on any CAISO-observable state — the EVENING RT-over-hub premium is wrong-signed AND year-unstable in the tight state, the BELLY depth is NOT stabilized by the hub LEVEL (CV worse than net-load). Neither mechanism is filed; the lane re-charters onto the import SUPPLY-CURVE pricing (model-internal state), keeper UNCHANGED.

**Session 2026-07-20 (CAISO-107 — executing the caiso-106 re-charter §7,
derive-first, measurement-only): keeper `2026-07-19-caiso-102-hourfix`
(NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}) UNCHANGED; no mechanism armed, no
solve, nothing registered.** Ladder unchanged — belly +6.0/+6.6/+4.3, evening
−5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4. Instrument (committed):
`scripts/probes/_caiso107_intertie_recharter.py` — pure raw-data (EIA-930 CISO
interchange + WECC hub DA LMP + CA actual RT/DA LMP + EIA-930 net-load), NO
solve, NO clean-data dependency; reuses the caiso-106 measurement primitives
(`_load`, the windows, the fixed net-load bands, the CV/LOYO honesty gate).

## 0. What caiso-106 handed to this session

FINDING-caiso106's single-year binding check split the caiso-105 unified
"too-elastic-both-directions" intertie diagnosis into two mechanistically
DISTINCT defects and re-chartered each with a fresh measurement (ask doc §7):

1. **EVENING = a PRICE defect.** The model's evening import VOLUME ≈ measured
   (so the withdrawn volume ceiling is inert); it prices the marginal MW at the
   hub-equalized (static firm-block contract) level, below reality's marginal
   supply. Candidate LP form: an inelastic exhaustion PREMIUM lifting the
   marginal tight-hour import offer above the hub by the MEASURED RT-over-hub
   separation in the tight state. NEXT STEP: measure that premium, gate it.
2. **BELLY = a VOLUME defect.** The net-import ceiling BINDS (model over-imports
   +2.6 GW in deep surplus) but the depth is not year-stable on CAISO net-load
   (west-wide dependence). Candidate observable: the Palo Verde / Malin hub
   LEVEL, which prices the neighbor surplus net-load misses. NEXT STEP:
   re-measure the depth on the hub LEVEL, test whether it stabilizes.

Derive-first (rule 1): no mechanism armed without an owner ask supporting a
specific LP form, and no ask on a measurement that fails its stability gate.

## 1. LANE 1 — the EVENING RT-over-hub premium is WRONG-SIGNED in the tight state and NOT year-stable → NOT READY

Measured mean (actual CA RT − measured DA hub) in the evening (hod 17-21),
conditioned on the observable tightness (fixed net-load bands and the tightest
net-load quintile):

| net-load band (GW) | mean RT − max(hub) 23/24/25 | mean RT − min(hub) 23/24/25 |
|---|---|---|
| [10,15) | +12.9 / +5.9 / +4.1 | +14.9 / +13.1 / +10.9 |
| [15,20) | +5.5 / −2.9 / −1.7 (SIGN-FLIP) | +8.7 / −1.1 / +1.9 (SIGN-FLIP) |
| [20,25) | −8.4 / −5.5 / −3.6 | −5.5 / −3.0 / +0.0 (SIGN-FLIP) |
| [25,30) | −11.4 / −7.8 / −5.2 | −6.8 / −4.7 / −3.1 |
| **[30,45) (tightest)** | **−66.6 / −34.8 / −10.4** | **−30.8 / −22.7 / −7.4** |

**The premium has the WRONG SIGN in exactly the state the mechanism targets.**
In the tight ([20,45) GW) evening, mean RT − max(hub) = **−17.1 $/MWh** (positive
in 0 % of tight band-years) and RT − min(hub) = **−9.3 $/MWh** (positive in 11 %):
actual CA RT prints *below* the DA hub when CAISO is tight, because the DA hub
itself spikes with the correlated-tight West (PALO DA reaches $145/$96/$64 mean
in [30,45), above CA RT $78/$62/$54). An exhaustion PREMIUM lifting the marginal
import *above* the hub would push the model's tight-hour λ the WRONG way
(over-price), not close the under-price.

**And it is not year-stable.** The tightest-net-load-quintile premium is
−73.4/−31.3/−7.9 (max-hub, CV 0.72, LOYO up to 559 %) and −33.6/−20.6/−5.7
(min-hub, CV 0.57, LOYO up to 378 %) — every scalar gate FAILS. The per-band
$/MWh gate FAILS in every tight band (CV 0.31–0.62) and sign-flips across the
transition bands.

**Measurement-integrity caveat (DA-vs-RT market mismatch).** The hub prints are
DAY-AHEAD LMP; CA RT is real-time. The evening CA DA−RT basis is large and
positive (+7.7/+8.5/+43.3 in the tight bands, +3 to +12 elsewhere), so a large
share of any apparent "RT below hub" is the day-ahead-hub-vs-real-time-CA market
mismatch, not a real-time transfer premium. A clean premium cannot even be
*defined* against a DA hub. (The model prices its import tranches off the same DA
hub, so the whole evening λ-vs-RT comparison carries this DA/RT wedge — see §3.)

**Why the raw-data premium contradicts caiso-103 §6's "RT ≈ at/above hub":**
caiso-103 §6 measured RT − hub = −2.3/+4.0/+6.7 in the MODEL's Q1 under-price
hours — a *model-residual-selected* state (the hours where the static firm-block
import rung sets λ low while reality's marginal supply is higher). That state is
NOT the tightest-net-load state and is NOT observable in raw data. Conditioning
on the observable (net-load) does not isolate it, and on that observable the
premium is wrong-signed and unstable. **The corrective quantity for the evening
defect is only cleanly defined against the model's own state, not any CAISO
observable** — the same identification obstacle that held the belly (§2).

**Verdict (rule 1 / derive-first):** the EVENING exhaustion-premium ask is NOT
filed. The premium is wrong-signed in the tight state, year-unstable on every
observable conditioning, and confounded by the DA/RT market mismatch. No LP form
proposed on refuted evidence.

## 2. LANE 2 — the BELLY depth is NOT stabilized by the hub LEVEL (CV worse than net-load) → NOT READY

Measured belly (hod 10-14) TOTAL net import p50 conditioned on the PaloVerde
(DSW) / min-of-hubs LEVEL — the west-wide observable the caiso-106 re-charter
proposed:

| PALO hub level ($/MWh) | p50 net import 23/24/25 (MW) | CV |
|---|---|---|
| [−120,−2) | −1206 / −1256 / +10 | 0.72 |
| [−2,8) | −644 / +904 / +1280 | 1.62 |
| [8,18) | −515 / +1664 / +935 | 1.30 |
| [18,28) | +240 / +2344 / +1500 | 0.63 |
| [28,40) | +848 / +2002 / +3314 | 0.49 |
| [40,120) | +100 / +1370 / +3256 | 0.82 |

**Hub-level conditioning makes the depth stability WORSE, not better.** Every
p50 band FAILS (CV 0.49–1.62) — worse than the net-load conditioning that
already failed (FINDING-caiso106 §3: fixed-band p50 CV 0.33–0.37). The same hub
level pairs with net EXPORT in 2023 and +900–1300 MW net IMPORT in 2024/25
(the [−2,8) band), so the hub LEVEL does not collapse the year drift. Even the
p95 exhaustion ceiling fails (CV 0.16–0.29). The min-of-hubs conditioning is
identical to two significant figures.

**The hub−CA basis does not rescue it either** (a thoroughness cross-check, the
natural "neighbor surplus relative to CA" observable): belly p50 net import by
(PALO − CA_DA) basis band is CV 0.71–0.89 with the import-side bands sparse
(< 25 samples/yr in basis ≥ +5) — also FAIL.

**Root cause (structural, confirms caiso-106 §3):** the DA hub LEVEL is itself
non-stationary (2025 has more solar/EDAM, so a given belly hub level maps to a
different west-wide surplus depth than in 2023), and the CA belly net transfer
depends on the *full* west-wide balance (WECC solar+hydro+load), which neither
the CA net-load NOR a single hub price summarizes. The hub level prices the
neighbor *marginal* energy, not the neighbor *surplus quantity* that sets how
much CA can export.

**Verdict (rule 1 / derive-first):** the BELLY net-import-ceiling ask is NOT
filed. The volume mechanism BINDS (caiso-106 §5) but the depth is not year-stable
on the hub LEVEL, the hub−CA basis, or CAISO net-load. No LP form on an unstable
measurement.

## 3. Unifying read — both intertie defects are model-λ-formation problems whose fix lives in the import SUPPLY-CURVE pricing, not a conditioned raw-data envelope

Both lanes fail the same way: the corrective quantity (evening premium, belly
depth) is only cleanly defined against the MODEL's own state (its residual, its
marginal-rung identity), and does NOT reduce to a year-stable function of any
raw CAISO observable tested (net-load, hub level, hub−CA basis). The measured,
forward-reproducible input the derive-first rule requires does not exist for a
conditioned intertie ENVELOPE on these observables.

The actual root cause is upstream of an envelope: caiso-103 §6 identified that
the model's marginal evening import is the FIRM/CONTRACTED blocks
(`DSW_solar_PV`, `PNW_hydro_base`) which under `caiso_perhub_firm_base` KEEP
their **static contract-cost ladder prices ($28 / $48 Tier-3 proxies)** while
the spot tranches ride the measured hub — so the model's λ is *pinned below the
hub* by a static-priced firm rung being marginal, not by an import-volume
ceiling or an unpriced premium. The right-signed lever is a **supply-curve
pricing** change (the marginal firm/import rung should price at the live hub
rather than a static contract cost, or a static-priced firm block should not be
allowed to set λ), which is a re-pricing of the existing import ladder — NOT a
conditioned quantity envelope. This is the natural re-charter direction and it
sidesteps the identification obstacle: the hub price the marginal import should
carry is the model's OWN endogenous WECC-node dual (forward-reproducible by
construction), not a measured cross-year envelope.

## 4. Re-charter (post-measurement, 2026-07-20)

* **EVENING** → the exhaustion-PREMIUM lane is CLOSED (wrong-signed + unstable +
  DA/RT-confounded). Successor lane: **import supply-curve re-pricing** — make
  the marginal firm-block import rung price at the live (endogenous) hub instead
  of the static $28/$48 contract cost, so the tight-evening marginal import
  cannot pin λ below the hub. Needs its own charter (a pricing change to the
  `caiso_perhub_firm_base` ladder, scored on the evening residual with the belly/
  overnight guards) — NOT a raw-data-conditioned envelope.
* **BELLY** → the net-import ceiling remains the right-signed mechanism (it
  BINDS, caiso-106 §5) but has NO admissible identification: the depth is
  year-unstable on net-load, hub level, and hub−CA basis. Held as an open lane
  pending a genuine west-wide surplus-quantity observable (WECC-wide net-load /
  solar+hydro surplus, not a hub price) — or, like the evening, a supply-curve
  re-pricing of the belly import tranches so the model stops importing at hub
  prices in deep surplus (the export-reversal is a PRICE response, not a fixed
  volume). NOT filed this session.

Neither lane is filed. The withdrawn caiso-106 volume ceiling and this session's
premium/hub-level candidates are all on record as tested-and-refused.

## 5. Session artifacts

- Probe committed: `scripts/probes/_caiso107_intertie_recharter.py` (both lanes
  + the dollar-scale premium gate, the tight-state sign check, and the
  hub-level / hub-basis depth gates). Pure raw-data, no solve, no clean-data
  dependency; reruns to the tables in §1–§2.
- No solve, no bundle, nothing registered (measurement-only; keeper UNCHANGED).
- `_caiso106_binding_analysis.py` / `_caiso106_binding_2024.py` NOT re-run — the
  binding directions they established (evening slack, belly binds) are unchanged
  and load-bearing for the re-charter above; a fresh same-machine bundle adds
  nothing to a measurement that already fails at the raw-data stage.
