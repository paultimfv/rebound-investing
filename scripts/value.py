#!/usr/bin/env python3
"""3-scenario exit-multiple DCF, Rebound style.

  value.py --fcf 60e9 --shares 24.4e9 --net-cash 50e9 --price 180 \
           --bear 0.05:20 --base 0.12:25 --bull 0.18:30 [--years 5] [--rate 0.10] [--dilution 0.0]

Scenario = FCF growth/yr : exit multiple on final-year FCF.
Outputs IV/share per scenario, the 15%-CAGR buy price, reward:risk, margin of safety,
and a reverse DCF (growth the current price implies at the base exit multiple).
"""
import argparse


def value(fcf, g, mult, years, rate, shares, net_cash, dilution):
    pv, f = 0.0, fcf
    for t in range(1, years + 1):
        f *= 1 + g
        pv += f / (1 + rate) ** t
    tv = f * mult
    pv += tv / (1 + rate) ** years
    sh = shares * (1 + dilution) ** years
    return (pv + net_cash) / sh, (tv + net_cash) / sh  # IV today, value/share in year N


def implied_growth(price, fcf, mult, years, rate, shares, net_cash, dilution):
    lo, hi = -0.5, 1.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if value(fcf, mid, mult, years, rate, shares, net_cash, dilution)[0] < price:
            lo = mid
        else:
            hi = mid
    return mid


def sc(s):
    g, m = s.split(":")
    return float(g), float(m)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for k in ("fcf", "shares", "price"):
        p.add_argument(f"--{k}", type=float, required=True)
    p.add_argument("--net-cash", type=float, default=0)
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--rate", type=float, default=0.10, help="discount rate for IV (stocks 0.10, tokens 0.15-0.20)")
    p.add_argument("--hurdle", type=float, default=0.15, help="target CAGR for buy price")
    p.add_argument("--dilution", type=float, default=0.0, help="annual share/token supply growth")
    for k in ("bear", "base", "bull"):
        p.add_argument(f"--{k}", type=sc, required=True)
    a = p.parse_args()

    print(f"FCF {a.fcf:,.0f} · shares {a.shares:,.0f} · net cash {a.net_cash:,.0f} · price {a.price} · "
          f"{a.years}y · rate {a.rate:.0%} · hurdle {a.hurdle:.0%} · dilution {a.dilution:.1%}/yr\n")
    print("| | growth | exit x | IV today | value yr%d | CAGR from price | buy-below (%.0f%% CAGR) |" % (a.years, a.hurdle * 100))
    print("|---|---|---|---|---|---|---|")
    res = {}
    for k in ("bear", "base", "bull"):
        g, m = getattr(a, k)
        iv, fut = value(a.fcf, g, m, a.years, a.rate, a.shares, a.net_cash, a.dilution)
        cg = (fut / a.price) ** (1 / a.years) - 1 if fut > 0 else float("nan")
        buy = fut / (1 + a.hurdle) ** a.years
        res[k] = (iv, fut, buy)
        print(f"| {k} | {g:.0%} | {m:.0f}x | {iv:,.2f} | {fut:,.2f} | {cg:.1%} | {buy:,.2f} |")

    bear, base, bull = res["bear"][0], res["base"][0], res["bull"][0]
    risk = a.price - bear
    rr = (base - a.price) / risk if risk > 0 else float("inf")
    rr_bull = (bull - a.price) / risk if risk > 0 else float("inf")
    mos = (base - a.price) / base
    buy = res["base"][2]
    ig = implied_growth(a.price, a.fcf, a.base[1], a.years, a.rate, a.shares, a.net_cash, a.dilution)

    def ck(b):
        return "✅" if b else "❌"
    print()
    print(f"{ck(mos >= 0.2)} Margin of safety vs base IV: {mos:.1%}   (need ≥20%)")
    print(f"{ck(rr >= 2)} Reward:risk (base): {rr:.2f}:1   bull: {rr_bull:.2f}:1   (need ≥2:1; risk = price − bear)")
    print(f"{ck(a.price <= buy)} Price {a.price} vs base 15%-CAGR buy-below {buy:,.2f}")
    print(f"Reverse DCF: price implies {ig:.1%}/yr FCF growth at {a.base[1]:.0f}x exit "
          f"(bear {a.bear[0]:.0%} · base {a.base[0]:.0%}) → "
          + ("worse than bear" if ig < a.bear[0] else "between bear and base" if ig < a.base[0] else "above base — priced for the thesis"))
    if risk <= 0:
        print("⚠️ Price is below the bear IV — check the bear case isn't too generous.")
