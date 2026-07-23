"""NYISO 2023 off-peak: TRUE available-capacity supply stack + marginal decomp.

Uses the real fleet availability array (pmax x availability = LP upper bound).
Answers definitively: is the off-peak marginal a genuinely-exhausted cheap fleet
(availability-limited) or an available unit priced too high?
"""
import numpy as np

NPZ = "/tmp/nyiso_2023_markup_decomp.npz"
HPM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def main():
    d = np.load(NPZ, allow_pickle=True)
    p0 = d["p0_prices"]
    if p0.shape[0] > p0.shape[1]:
        p0 = p0.T
    T = p0.shape[1]
    pg, ft = d["pg"], d["ft"]
    mc = d["mc_base_gen"]
    disp = d["p0_disp"]
    pmax = d["pmax"]
    avail = d["availability"]           # (n_gen, T)
    moh = np.repeat(np.arange(1, 13), [h * 24 for h in HPM])[:T]
    hod = np.tile(np.arange(24), T // 24 + 1)[:T]
    ref = p0[0]
    eff_cap = pmax[:, None] * avail     # (n_gen, T) true LP upper bound

    mask = np.where(np.isin(moh, [5, 6, 8]) & (hod <= 6))[0]
    served = disp.sum(axis=0)

    # true available capacity by fuel off-peak
    print("=== Off-peak shoulder: TRUE available capacity vs dispatch by fuel ===")
    for f in sorted(set(ft.tolist())):
        rows = np.where(ft == f)[0]
        acap = eff_cap[rows][:, mask].sum(axis=0).mean()
        run = disp[rows][:, mask].sum(axis=0).mean()
        if acap > 1:
            print(f"  {f:>16}: avail {acap:>8.0f} MW  run {run:>8.0f} MW  headroom {acap - run:>7.0f}")
    print(f"  {'served load':>16}: {served[mask].mean():>8.0f} MW")

    # true stack clearing: sort by mc, cumulate TRUE available cap, meet demand
    implied, headcheap = [], []
    for t in mask:
        price = ref[t]
        order = np.argsort(mc[:, t])
        cummc = mc[order, t]
        cumcap = np.cumsum(eff_cap[order, t])
        k = min(np.searchsorted(cumcap, served[t]), len(order) - 1)
        implied.append(cummc[k])
        cheap = mc[:, t] < price - 2.0
        headcheap.append(float((eff_cap[cheap, t] - disp[cheap, t]).clip(min=0).sum()))
    implied = np.array(implied)
    print("\n=== TRUE available-capacity stack clearing ===")
    print(f"  model P0 price:            ${ref[mask].mean():.2f}")
    print(f"  implied stack-clearing mc: ${implied.mean():.2f} (p50 ${np.median(implied):.2f})")
    print(f"  TRUE-avail cheap headroom at marginal hour: {np.mean(headcheap):.0f} MW")
    print("  (near-0 headroom + implied~=price => cheap fleet genuinely exhausted)")

    # exact marginal unit decomposition (partially-loaded, mc closest to price)
    running = (disp > 0.05 * eff_cap) & (disp < 0.98 * eff_cap)
    print("\n=== Exact marginal unit off-peak (mc-matched, partially loaded) ===")
    hr = d["heat_rate"]
    rows_by = {}
    for t in mask:
        cand = np.where(running[:, t])[0]
        if len(cand) == 0:
            continue
        g = cand[np.argmin(np.abs(mc[cand, t] - ref[t]))]
        c = str(pg[g])
        rows_by.setdefault(c, []).append((mc[g, t], hr[g]))
    for c, lst in sorted(rows_by.items(), key=lambda r: -len(r[1])):
        arr = np.array(lst)
        print(f"  {c:>12}: {len(lst):>4} h  mean mc ${arr[:, 0].mean():.2f}  "
              f"mean tranche-HR {arr[:, 1].mean():.2f}")


if __name__ == "__main__":
    main()
