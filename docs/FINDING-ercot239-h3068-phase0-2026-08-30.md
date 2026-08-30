# FINDING — ercot-239 round 3 (2026-08-30): h3068-2024 is the EXIT HOUR OF A ONE-HOUR-LATE MODEL EVENT on perfectly time-aligned inputs — net-load release lag ZERO, price release lag ONE; at h3068 the model still holds reserve-family steps ($416.67, NonSpin short 298 MW) and prices $798 on the thermal wall while its storage sits at 0 MW — the ercot-223 record's own "938 MWh h3068→h3069 re-timing" made visible price-side — where reality had already collapsed to $110 (λ $99, RTORPA $8.95, RTOLCAP recovered to 7,890)

**Session ercot-239, branch `claude/ercot-239-residual-queue-lbkvbf`.
ZERO-SOLVE — every number read from the FORWARD keeper's committed 2024
sidecars (`ercot234_eastex_identity`), the committed actuals, the EIA-930
wide extract and the measured ORDC/reserves series.** Precommit
`docs/PRECOMMIT-ercot239-h3068-phase0-2026-08-30.md` pushed +
blob-verified before any measurement; V-0 exact (model 798.20 / actual
110.41). Probe `scripts/probes/ercot239_h3068_phase0.py` →
`results/calibration/ercot239_h3068_phase0.json` (committed). No lever,
no gate change, no matrix verdict; keepers untouched.

## 0. Verdict in five lines

1. **The inputs are exonerated completely:** model and actual net load
   track within ~800 MW through the whole May-8 window and BOTH peak at
   h3067 and release at h3068 (M-3 net-load release lag = 0; demand
   alignment lag-0 asserted). P3 CONFIRMED.
2. **The model's EVENT is one hour late on both edges:** reality priced
   the ramp-in at h3064 ($966 at 50.2 GW net load; model $245 at the
   same load) and released at h3068 ($110.41, λ $99.36, RTORPA $8.95,
   RTOLCAP recovered 5,094 → 7,890); the model entered at h3065, topped
   at $5,000 (vs actual $3,049) at h3067, and released at h3069. h3068
   is the exit edge of that lag. P2 CONFIRMED.
3. **At h3068 the model is still INSIDE its event:** all three
   withheld families at the $416.67 (= VOLL/12) step, NonSpin short
   298 MW, ORDC-total short 2,567 MW (P4 REFUTED — the hold IS
   co-opt scarcity), thermal at 46.4 GW (600 MW below its event peak),
   and **storage at 0 MW discharge** — after 2,189 + 2,227 MW at
   h3066–67 — then 1,066 MW at h3069 at $53: discharging into the $53
   hour instead of the $798 hour is not price-optimal dispatch; it is
   the ercot-223 event-release guard's recorded re-timing ("h3068 keeps
   its floor (pass-1 settle $675 < $1,000) so the 938 MWh h3068→h3069
   re-timing", PRECOMMIT-ercot223 / FINDING-ercot223 §"the η-scaled
   freeze releases").
4. **P1 REFUTED as declared, sharpened by the data:** the $798 is NOT
   the adaptive floor's price (λ − floor_usd = $275, discharge 0) — the
   adaptive/release-guard structure acts on the WITHHOLDING side: it
   holds the storage energy OUT of h3068, and the price is then set by
   the thermal wall + the lingering reserve steps that the missing
   ~1 GW of storage would have relieved.
5. **The object, named for the queue:** the model's event-EXIT
   stickiness — one hour of storage re-timing + reserve-step decay on
   time-aligned inputs — is what the lidless G-SPUR permanently counts
   at h3068. It lives on the `ercot_storage_adaptive_expectation` /
   event-release-guard complex (the ercot-223 K mechanism), not on
   offers, inputs, or the ORDC.

## 1. The window (committed JSON carries all 19 hours)

| h | hod | model | actual | nl model | nl actual | storage dis | families | measured RTOLCAP (pctl) | measured RTORPA |
|---|-----|-------|--------|----------|-----------|-------------|----------|--------------------------|-----------------|
| 3064 | 16 | 245 | 966 | 49,417 | 50,245 | 9 | steps $1,250, NonSpin short 887 | 7,974 (p1.2) | 0.8 |
| 3065 | 17 | 2,127 | 997 | 50,819 | 50,805 | 261 | steps $1,667 | 7,724 (p0.8) | 3.2 |
| 3066 | 18 | 4,925 | 2,451 | 53,364 | 53,545 | 2,189 | steps $3,750 | 5,468 (p0.0) | 178.0 |
| 3067 | 19 | 5,000 | 3,049 | 54,230 | 54,293 | 2,227 | steps $3,834 | 5,094 (p0.0) | 178.6 |
| **3068** | **20** | **798** | **110** | 50,762 | 50,428 | **0** | **steps $416.67, NonSpin short 298** | 7,890 (p1.0) | 9.0 |
| 3069 | 21 | 53 | 30 | 46,097 | 45,642 | 1,066 | all zero | 10,859 (p13) | 0.0 |

Reading: the model's scarcity architecture fires on the right event with
the right inputs and decays ONE HOUR late; reality's own reserve room was
back above 7.8 GW at h3068 and its λ collapsed with it.

## 2. Prior grading

* **P1 REFUTED** (as declared): λ−floor $275 > $150; discharge 0. The
  refined mechanism-side reading is §0.4.
* **P2 CONFIRMED:** actual h3068 $110.41 < $200; h3066–67 $2,451/$3,049;
  measured RTORPA $8.95 / RTORDPA < $50.
* **P3 CONFIRMED:** net-load release lag 0 (both sides peak h3067,
  release h3068).
* **P4 REFUTED:** the model still carries family steps and shortfall at
  h3068 — the hold is genuinely co-opt scarcity decaying late, not a
  price-floor artifact.

## 3. What this round does NOT do

No lever (the event-release guard is the ercot-223 owner-promoted
keeper mechanism; any exit-timing refinement is a new owner-visible
round on that complex); no matrix verdict moved (an evidence NOTE lands
on the `ercot_storage_adaptive_expectation` cell per the precommit's
§4 permission); no keeper touched; years ⊂ {2024}; no
`--holdout-authorized`; ERCOT surfaces only; no run produced (rule 15
not triggered).

## 4. Queue statement for the owner

h3068-2024 is now fully attributed: **a one-hour event-exit lag of the
storage/reserve complex on time-aligned inputs** — the re-timed ~1 GWh
of storage plus the reserve-step decay prices the exit hour on the
thermal wall. It is the exit-edge twin of the entry-edge conduct gap
(reality priced h3064's ramp-in; the model did not — the round-1 conduct
theme at this event's front edge). If the owner wants the spur hour
repaired, the admissible direction is the event-release guard's exit
condition (its pass-1 settle test held the floor at $675 < $1,000 —
one fixed threshold away from releasing), worked as its own precommitted
round on the ercot-223 complex; the entry edge belongs to the same
RT/SCED conduct lane as rounds 1–2's queue items.
