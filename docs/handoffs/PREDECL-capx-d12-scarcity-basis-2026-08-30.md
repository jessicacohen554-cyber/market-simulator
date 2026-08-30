# D12 pre-declarations — recorded BEFORE extracting steps 2022/2023/2025 margins and Σadder values

Written after seeing: the two chartered findings, the code seams, the FFR-9B replay
step-2022 merchant block (old posture), and the dual-replay 2024-step arms
(shipped-signal gas margins negative under both bounds). NOT yet seen: dual-replay
2022/2023/2025 shipped-signal thermal blocks; any Σadder annual values; any direct
dump recomputation.

## Candidate bases (stated before the arithmetic)

- **A (shipped)**: energy leg on S_next (lookahead stack + FFR-8A expected-ORDC
  tail, entering year Y+1); reserve leg r(t) = prior SOLVED year's realized
  post-solve ORDC adder (runner.py:3958-3960). Cross-year, cross-object mix.
- **B (scarcity-consistent forward)**: reserve leg = the SAME instrument
  invocation's expected-ORDC adder for the entering year (`adder_usd_mwh`).
  One scarcity object. Identity: max(S−vc, adder) = adder + max(base−vc, 0)
  (since S = base + adder, adder ≥ 0) — the textbook expected-ORDC revenue:
  every MW earns the expected reserve price every hour plus energy rents.
- **C (r_none)**: no reserve leg; energy-only. Bracket, not market-faithful
  (ERCOT pays RTORPA/RTOFFPA to reserves).
- **D (fully realized/backward)**: disarm construction (prior-year realized
  duals + overlay as energy leg; realized r) — measured live, terminal 40.24.
- **D' (composed + tail-free delta)**: the fwd-exp §4 named successor for the
  composition — same principle as B (one scarcity object per construction),
  orthogonal lane (composition unarmed at registered posture).
- **A+Δ (D11-R within-walk closure)**: r_walk = max(0, r + Δadder). Within-year
  only. If B is adopted, this closure is superseded (rule 19): the walked leg IS
  the walked adder.

## Pre-declared expected outcomes (the honesty test)

- **P-D1**: entering-2023 gas margins hugely positive under BOTH r_none and
  r_dump_adder (pre-tight expectation carries the energy leg; basis choice
  changes nothing there). Entering-2022 also positive under both.
- **P-D2**: entering-2025 negative under both bounds (control built nothing).
- **P-D3**: under basis B, bang-bang builds change ONLY at entering-2024
  (gas 6 GW → 0) vs shipped control; open-loop terminal-RM anchor drops from
  25.19 toward ~21–22 % (similar magnitude to the live exhaustion arm's 22.02,
  by a different mechanism).
- **P-D4**: under basis B the exhaustion rule's gas half is LIVE: the leg
  reprices with the walk (top-of-stack grows → adder collapses); expected walk
  behaviour: 2024 gas never starts, 2022 gas_ct may damp below 1571, 2023
  unchanged (caps bind first).
- **P-D5 (gas-inertness per basis)**: A → inert (measured, D11-R §4).
  B → live at exactly the post-tight-year step. C → same sign pattern as B at
  2024/2025; B−C = Σadder could matter at 2022 (expected tail mean ~14 $/MWh
  → ~$120k/MW-yr) but likely doesn't flip any sign. D → measured (disarm);
  gas cap-bound in its 2024 step too.
- **P-D6**: Σadder(entering-2024) tiny (~$5k/MW-yr, tail mean ~0.59) —
  so B ≈ C exactly where A diverges most: the shipped 2024 gas build is
  attributable to the realized-r leg ALONE (lower bound on its contribution =
  the |negative| margins: ≥ $10.7k gas_cc, ≥ $42.7k gas_ct per MW-yr).

## Addendum (recorded after reading the dual-replay 2022/2023/2025 blocks and
## the L-1b RM mapping, BEFORE any dump computation)

- **P-D3 correction, owned**: thermal COD lag is 2 (L-1b probe line 508), so a
  2024-step decision lands 2026 — OUTSIDE the RM ledger window. Basis B's
  bang-bang ledger RM path is therefore UNCHANGED (19.00/8.54/14.65/25.19);
  what moves is the post-window 2026 RM (−6 GW gas ≈ −7 pp at ~87 GW peak) and
  the scored decision-basis gas bands (gas_cc 9→6, gas_ct 7.571→4.571 GW).
  P-D3's "terminal ledger anchor drops to ~21–22" was WRONG — recorded as a
  miss before any computation.
- **P-D7 (exhaustion-arm 2025 step, cc7bbe dumps — NOT yet inspected)**: the
  arm built 6 GW gas at entering-2025 on its thinner fleet. Pre-declare: under
  basis B I expect that build to SHRINK or VANISH — i.e. I expect it was at
  least partly carried by the realized-r leg from the arm's own tighter 2024
  solve; if instead its energy leg alone clears fixed cost, basis B leaves it
  and I report that.
