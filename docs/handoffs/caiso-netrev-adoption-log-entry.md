# CAISO gas-offer net-revenue margin — ADOPTED as the go-forward offer form (owner, rule #1) — calibration-log entry (append to docs/calibration-log/caiso.md)

> Delivered as a handoff doc: `docs/calibration-log/caiso.md` is 44 KB and parallel
> CAISO sessions append to it, so a full-file API push would risk clobbering their
> entries (the caiso-114/115/116 precedent). Merge this into caiso.md on integration.

## 2026-07-23 — CAISO ADOPTS the gas-offer net-revenue margin form (owner directive, rule #1) — the structurally-correct offer form supersedes the fuel-scaled HR multiplier; keeper NOT re-promoted standalone (would regress C3b), re-keepered JOINTLY with the import/scarcity (C3c) lane so the board does not regress in isolation

**Owner decision, no solve, keeper unchanged.** Keeper `2026-07-19-caiso-102-hourfix`
stays the registered CAISO keeper (net-rev flag OFF) until the joint re-keeper below.
This entry records an owner directive that OVERRIDES the caiso-112 stance
("margin stays default-off"): the `gas_offer_net_revenue_margin` form is **adopted
as CAISO's go-forward gas-offer structure** because it is more structurally correct
than the fuel-scaled heat-rate-multiplier markup — the textbook rule #1 / rule #11
call (a real market behaviour stays in even though it makes the backcast fit worse;
the worse fit is the discovered symptom of a *different* defect).

### Why the net-revenue form is the correct structure (rule #1)

The HR-multiplier markup form prices a gas tranche's above-physical markup as
`mult × HR_base × fuel(t)` — so the bid **$ markup scales linearly with the fuel
bill**. That is not how bidders behave: start/no-load hurdles, competitive reach
and the scarcity wall are expressed as **fuel-invariant $/MWh net-revenue targets**,
not heat-rate multiples. The multiplicative form is unidentified inside the
homogeneous 2023–25 training gas window and blows the markup up out-of-window (the
2022 NEISO +57.7 $/MWh bulk overshoot at ~2.9× anchor gas). The net-revenue form
(`phys × HR_base × fuel(t) + (mult − phys) × HR_base × anchor`) keeps the physical
burn fuel-tracking but freezes the markup in $ at the delivered-gas anchor —
forward-stable, and already the ADOPTED NEISO keeper form (neiso-61). CAISO's
anchor is **4.7964 $/MMBtu** (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, mean of the keeper
delivered-gas 2023–25 = 6.95 / 3.37 / 4.06; SoCal/PG&E citygate hub-basis overlay).

### Verified A/B (reproduced this session, no solve — `scripts/probes/netrev_margin_ab.py` on the committed caiso-112 bundles `caiso_netrev_base` / `caiso_netrev_margin`)

| year | gas vs anchor | C3a base→margin | C3b dur-NRMSE base→margin |
|---|---|---|---|
| 2023 | 6.95 (≫, compress) | −6.8 → −7.2 % | 0.390 → **0.411** (worse) |
| 2024 | 3.37 (<, firm)     | −9.4 → −6.9 % | 0.429 → **0.445** (worse) |
| 2025 | 4.06 (≈, neutral)  | −3.9 → −2.7 % | 0.292 → 0.288 (better)    |

The mechanism behaves EXACTLY as designed (firms the low bands below anchor,
compresses above), reproducing the caiso-112 numbers digit-for-digit. **The C3b
regression is second-order and is a SYMPTOM of a first-order defect, not the offer
form.** The duration band table (2023, actual vs hour-matched model mean / gap):

| band | hours | actual | BASE gap | MARGIN gap |
|---|---|---|---|---|
| <40 | 3601 | 20.3 | +8.8 | +9.2 |
| 40–80 | 3717 | 56.1 | −4.2 | −3.9 |
| 80–150 | 1194 | 105.1 | **−23.0** | **−25.5** |
| 150–300 | 236 | 175.8 | **−59.7** | **−64.7** |
| >300 | 12 | 561.0 | **−477.3** | **−478.4** |

CAISO's mid/upper bands are under-priced by −23 to −480 $/MWh in **both** forms —
the massive import/scarcity-tail defect (C3c FAILs). The HR multiplier's fuel-scaled
markup accidentally inflates those bands a few $ at high gas, *partially masking* the
gap; the net-revenue form declines to (it's a fuel-invariant $ margin), so at
above-anchor gas it pulls the already-broken tail ~$2–5 lower — the entire C3b
delta. The offer-form choice is a second-order effect sitting on a first-order
under-priced tail; keeping the fitted HR multiplier to buy back that few-$ prop is
the rule-#1-forbidden move (mask the defect with the wrong mechanism).

### The decision — adopt the form, defer the keeper regression to the joint fix

- **Adopt** `gas_offer_net_revenue_margin` as CAISO's go-forward gas-offer form.
  The **next CAISO keeper solve carries `--gas-offer-margin`** (resolves the 4.7964
  anchor); the fuel-scaled HR-multiplier markup is retired from the CAISO recipe.
- **Do NOT promote a standalone net-rev keeper now.** In isolation it would move the
  keeper scorecard fail`{C3c, C4, C5a}` → fail`{C3b, C3c, C4, C5a}` — one more gate,
  purely because it exposes (does not cause) the under-priced mid-tail. Per the
  owner's packaging choice, the board should not regress in isolation.
- **Re-keeper JOINTLY with the import/scarcity (C3c) lane.** The under-priced mid/
  upper bands are the same import/scarcity-tail residual caiso-107/109/111 and this
  session's caiso-116 finding are about (the reduced-network import over-supply that
  caps CA's evening/scarcity price below the tail). When that lane moves the tail up,
  the net-rev keeper solve carries `--gas-offer-margin` and the C3b regression is
  absorbed (the form no longer compresses an already-broken tail — it compresses a
  correctly-priced one, as designed). Until then the registered keeper stays
  caiso-102-hourfix (net-rev off) and this adoption is the standing recipe decision.

No code default is flipped this session: making `--gas-offer-margin` default-on for
CAISO would break the current keeper's byte-identity replay and force the C3b
regression on the next solve prematurely — exactly what the deferred-keeper choice
avoids. The adoption lives as this recipe decision-of-record; the next keeper session
adds the flag when it also moves the tail.

### Ledger / provenance

- Identification landed on main (`379a9b3`, PR #2819/#2822): CAISO `phys_*` keys on
  all five gas classes (`_CAISO_OFFER_CURVE`, cited to
  `caiso_campd_marginal_hr_summary.csv` p50s) + anchor 4.7964
  (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`). 0 free parameters fitted (rule 25 / the design
  DOF ledger). Design: `docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md`.
- caiso-112 A/B bundles (`caiso_netrev_base` / `caiso_netrev_margin`, slim — hourlies
  only) reproduce the numbers above; a full keeper bundle (dispatch frames for
  C1/C4/C5a) is produced at the joint re-keeper.
- Supersedes the caiso-112 log stance ("margin stays default-off") for CAISO's
  go-forward recipe; caiso-112's board default (flag off in the current keeper) is
  unchanged until the joint re-keeper.
