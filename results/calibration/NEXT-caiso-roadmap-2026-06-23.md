# CAISO — next-steps roadmap (2026-06-23 session pickup)

State at pickup: all prior session work is merged to `main`. Current keeper is
`caiso-import-cap-floor` (PR #788): two-mechanism priced import node (hub prices
+ gas-coupling + solar-shape) + aggregate WECC 8.3 GW simultaneous-import cap +
per-tranche delivered-cost basis + RA gas-commitment floor 0.80 + negative
renewable offers. 2024: neg-price hrs 815 (~800 actual), net interchange −30.4
TWh vs −32.4 actual. Residual: mean LMP ~$8 high, body +$6.

Parallel thread left un-merged: `caiso-20-bidir-intertie` replaced the
two-mechanism node with a single signed WECC intertie (both legs at the measured
hub) and **flipped the 2024 diurnal interchange correlation from −0.65 to
positive** — fixing the *shape* the keeper still gets wrong — but it never
adopted the keeper's level fixes (delivered-cost basis, gas floor 0.80). The two
import representations are mutually exclusive in code
(`run_calibration.py` ~1835: bidir supersedes the hub injectors).

## Chosen path: UNIFY (in progress)

Bring the bidir-intertie mechanism to keeper parity so ONE keeper has both the
diurnal-shape fix and the price-level fix:

1. **Code:** add the per-tranche `CAISO_IMPORT_DELIVERY_BASIS` (line-loss +
   OATT wheeling markup over the hub MCE) to the import legs in
   `inject_caiso_bidir_intertie_prices` — mirroring
   `inject_caiso_import_hub_prices` (transmission.py ~575). The bidir export leg
   owes none (CAISO delivers to the neighbor at the bare hub). Arbitrage-free
   property preserved (import = hub·(1+loss)+wheel+carbon+ε ≥ export = hub−ε).
   The 8.3 GW import cap is already baked into the bidir leg
   (`CAISO_BIDIR_IMPORT_CAP_MW`).
2. **Config:** run bidir + `--caiso-gas-commitment-floor` (0.80) +
   `--negative-renewable-offers` + `--gas-hub-basis-overlay` (bidir run had the
   gas floor OFF; the keeper validated it at 0.80). gas-coupling / solar-shape
   are intentionally NOT used — bidir supersedes them (single unified hub).
3. **Solve** 3 years (2023 2024 2025), register as a keeper, compare to
   `caiso-import-cap-floor` on: mean LMP, body, neg-price precision/recall, net
   interchange, AND the diurnal interchange correlation.

Risk to watch: 2023 has no measured WECC hub series (OASIS Jan–Feb aged out), so
the bidir tie falls back to its static-ladder placeholder for 2023 — same
limitation the keeper has.

## Logged alternates (not chosen this session)

### B. Diurnal import price shape (the body-overprice diagnosis's recommended build)
`DIAGNOSIS-caiso-body-overprice-2026-06-21.md`: the residual +$6 body is a
flat-import diurnal artifact — over-import midday → $28 PNW_hydro_base floor
(reality is long → ~$14), under-import overnight → gas-CC $48 (reality $42). The
fix is a measured diurnal import *price* vector (cheap-but-positive midday,
cheap overnight). **Blocked** on OASIS measured WECC hub hourly prices (Mid-C /
Palo Verde) — not fetchable in this environment. Before committing here, check
whether the bidir hub series already supplies enough diurnal signal (it may
subsume this item) or whether any in-repo proxy exists. An availability cap is
NOT the instrument (caiso-16 regressed; band-only is a no-op; the
PNW_hydro_base −$20 collapse hit an ~85% precision wall — all ruled out).

### C. Evening-ramp residual
The evening ramp (h18–21) is *under*-priced (−21%, model flat $50 vs $66 peak)
and is currently offsetting the mean. Lifting it needs a non-AS mechanism:
the CAISO summary explicitly rejects an ORDC / AS-stream overlay (RA-backed,
$2,000 cap, no scarcity tail; the model already over-prices the body). Higher
risk of a dead end; revisit only after UNIFY settles the body/shape.
