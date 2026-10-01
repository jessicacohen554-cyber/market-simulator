# PRE-DECLARATION — capx D31: the MISO T1-H consequence of the capacity-revenue repair (position + published RBDC shape)

**Written and pushed BEFORE the solve starts** (the D27 discipline). The repair
itself — the funded PRA intake, the published-shape RBDC replacement, and the
internal-supply accounting ratio — is committed at the parent of this commit
and was identified entirely from the published record before any solve; nothing
below can feed back into it. Graded at full magnitude in the finding, misses
included.

**The run:**

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d31
```

Bare HEAD invocation — the exact D27 recipe with only the out-dir changed, so
every movement vs `miso-2021-2025-realized-t1h-d27` is the two-leg repair (the
ONLY solve-affecting deltas on this branch vs D27's base are the D31 commit and
whatever rode into main between 2026-09-01 and this branch's rebase base
b70bf0f5 — the latter set contains no MISO-relevant solve-affecting default to
my reading of the log; any surprise there is reported, not absorbed).
`ScenarioConfig` is untouched, so the config cache key equals D27's
(`501b5f64b8adf8d4` expected); the fresh `--out-dir` (verified absent) is what
guarantees no stale bundle can serve — the constants-level repair is invisible
to the config hash by design, which is why guard (a) is the out-dir, not the
key.

**Mechanism arithmetic the predictions rest on** (computed from the committed
inputs before launch): corrected entering positions 1.0393 (2023) / 1.0321
(2024) on the D27 entering fleets (were 1.2111 / 1.2028); the 2022-bridge
screen's floor headroom shrinks from ~25.7 GW (S-123-released) to ~4.8–5.5 GW
of accredited room = **~6–7 GW of admittable nameplate at the ratio'd
accreditation**; the 2021–2024 screens still price the design-faithful
VERTICAL vintages ($0 at any position > 1.0, so the corrected ~1.03–1.04
positions still earn $0 capacity revenue); the 2025 screen prices the
published RBDC at an entering position ≈ 1.017 if ~6 GW executed in 2024 →
~$104/kW-yr at the one annual position (the one-position sum; the market's own
four-position sum was $79.07).

## P1 — the coal wave collapses to the floor's new headroom

`retire.decided` at the 2022-bridge screen: **4.5–9.5 GW, all coal** (central
~6.5), against D27's 25,646.6 MW. Executed coal 2024 equal to the decided
cohort (pipeline lag unchanged). **Falsifier:** decided coal > 12 GW or
< 2 GW, or any non-coal MW in the decided set.

## P2 — the non-coal channel does NOT open (the D32 object, untouched)

gas_st / gas_cc / gas_ct / oil executed: **exactly 0.000 GW**, all years. The
floor still binds every screen year, `_floor_retention_merit` still releases
coal-first-from-the-expensive-end, and this lane deliberately did not touch
the retention key (D32's charter). The repair moves the VOLUME the floor
admits, not the COMPOSITION. **Falsifier:** any non-coal fossil execution.

## P3 — G3 flips back to under-retirement

`retire.total_gw` **5.5–11 GW** (central ~7.5: coal ~6.5 + nuclear 0.768 +
biomass ~0.016) vs the 17.369 actual → err_frac **−37% to −68%**, band FAIL,
sign flipped from D27's +52.2% over to UNDER. `false_retire` returns to PASS
(< 10%; D27's 13.2 GW / 50.0% was the excess-coal arithmetic). Recall drops
back toward the D17-era 13/17-ish (fewer real coal units covered).
**Falsifier:** total lands in the ±10% band (PASS) or overshoots again
(> 20 GW).

## P4 — the 2025 screen's capacity leg is strictly positive; 2021–2024 stay $0

The per-fuel screen-revenue decomposition (evolution event rows): capacity leg
**$0.00 in every 2021–2024 screen** (vertical era at > 1.0 positions — the
design, not a defect) and **strictly positive for every fuel in the 2025
screen** — $85–115/kW-yr × the unit's (1 − EFORd) if the entering position
lands 1.01–1.03; lower (but > $25/kW-yr) if the executed wave is small and
the position sits 1.03–1.05. Consequence: essentially **zero 2025-screen
retirement decisions** (every fuel's bar clears on energy + capacity).
**Falsifier:** a $0.00 capacity leg in the 2025 screen, or a positive leg in
any vertical-era screen.

## P5 — adequacy invariants recover

I3 unserved/dump: **PASS all years** (the D27 FAILs were the 25.6 GW physical
exit; ~6.5 GW leaves ≥ 14% physical reserve margin every year). The armed
backstop still never fires (the floor stops exits at the requirement, so no
gap opens). I12 may still WARN early-window (unchanged mechanism).
**Falsifier:** any I3 FAIL year.

## P6 — additions move; direction uncertain, declared not predicted

The 2025 entry screen sees the RBDC's capacity revenue for the first time
(gas_ct: ~$97k/MW-yr capacity alone at a 1.017 position, near its hurdle), so
**economic gas and/or storage entry in 2025 is live** — possibly enough to
flip `add.*` bands in either direction; `entry_rate_limits` (armed default)
caps the size. I decline to predict the band outcomes; whatever happens is
reported at full magnitude. The D27 additions-clause MISS taught that these
bands are not insulated from capacity-side repairs.

## P7 — verdict rows

FC-3 stays **FAIL** (P3's G3 miss plus whatever the additions do); FC-7 reads
as D27 (run_config PASS, DOF-ledger caveat — the two new inputs are MEASURED
registry entries); determination stays **HOLD**. The ff-verdicts edit is a
pure insertion/update touching exactly `miso-t1h` + the preserved
`miso-t1h-pre-d31` key; **no verdict outside miso-t1h's rows moves** — if any
would, I STOP and route the cross-lane re-grade before registering.

## Registration plan (declared now so the artifact trail is fixed)

Register `miso-2021-2025-realized-t1h-d31` preserve-then-overwrite onto the
bare `miso-t1h` key; D27's record is preserved under `miso-t1h-pre-d31`
(itself keeping `miso-t1h-pre-d27` untouched); refresh the MISO block on the
forecast board (t1h provenance + retire G3 row); finding
`FINDING-capx-d31-miso-caprev-repair-2026-09-02.md` carries the graded
scorecard, the reconciliation table, and the honest exit-residual direction
under rule 14 — nothing above was sized, tuned, or sequenced by what it does
to the exit residual, and P2 states in advance that the residual this program
actually hunts (the non-coal channel) is expected NOT to move.
