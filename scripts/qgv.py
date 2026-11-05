#!/usr/bin/env python3
"""QGV screen for a stock (SEC EDGAR + Yahoo) or token (CoinGecko + DefiLlama).

  qgv.py stock NVDA
  qgv.py token --cg hyperliquid --llama hyperliquid
Outputs a table with thresholds. Screen, not verdict.
"""
import json, os, sys, urllib.request, datetime as dt, argparse

# SEC requires "Name contact" in the UA; set SEC_UA to your own if this gets 403s
UA = {"User-Agent": os.environ.get("SEC_UA", "Rebound Research research@rebound-qgv.local")}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def pct(x):
    return "n/a" if x is None else f"{x*100:.1f}%"


def num(x):
    if x is None:
        return "n/a"
    a = abs(x)
    for d, s in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= d:
            return f"{x/d:.2f}{s}"
    return f"{x:.2f}"


def cagr(a, b, years):
    if a is None or b is None or a <= 0 or b <= 0 or years <= 0:
        return None
    return (b / a) ** (1 / years) - 1


def row(name, val, thr, ok):
    mark = "—" if ok is None else ("✅" if ok else "❌")
    print(f"| {name} | {val} | {thr} | {mark} |")


# ---------------- STOCK ----------------
def annual(facts, tags, unit="USD", instant=False):
    """{year: value} from calendar frames (CY2023 / CY2023Q4I). Merges candidate tags,
    preferring whichever tag has the most recent data (companies switch tags over time)."""
    found = []
    for tag in tags:
        for ns in ("us-gaap", "ifrs-full"):
            f = facts.get(ns, {}).get(tag)
            if not f:
                continue
            units = f["units"].get(unit) or next(iter(f["units"].values()))
            out = {}
            for e in units:
                fr = e.get("frame", "")
                if instant and fr.endswith("Q4I") and len(fr) == 9:
                    out[int(fr[2:6])] = e["val"]
                elif not instant and len(fr) == 6 and fr.startswith("CY"):
                    out[int(fr[2:])] = e["val"]
            if out:
                found.append(out)
    if not found:
        return {}
    found.sort(key=lambda d: max(d), reverse=True)
    merged = {}
    for d in reversed(found):
        merged.update(d)
    merged.update(found[0])
    return merged


def stock(ticker):
    ticker = ticker.upper()
    tickers = get("https://www.sec.gov/files/company_tickers.json")
    cik = next((v["cik_str"] for v in tickers.values() if v["ticker"] == ticker), None)
    if cik is None:
        sys.exit(f"{ticker}: not in SEC list (foreign filer? use web data for 20-F/ASX/EU names)")
    cf = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    facts = cf["facts"]

    rev = annual(facts, ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "Revenue"])
    cogs = annual(facts, ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfSales"])
    gp = {**{yr: rev[yr] - cogs[yr] for yr in rev if yr in cogs}, **annual(facts, ["GrossProfit"])}
    gp.update({yr: rev[yr] - cogs[yr] for yr in rev if yr in cogs and yr not in gp})
    op = annual(facts, ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"])
    pretax = annual(facts, ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"])
    tax = annual(facts, ["IncomeTaxExpenseBenefit"])
    ni = annual(facts, ["NetIncomeLoss", "ProfitLoss"])
    cfo = annual(facts, ["NetCashProvidedByUsedInOperatingActivities"])
    capex = annual(facts, ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"])
    sbc = annual(facts, ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"])
    eq = annual(facts, ["StockholdersEquity"], instant=True)
    debt = annual(facts, ["LongTermDebt", "LongTermDebtNoncurrent"], instant=True)
    debt_c = annual(facts, ["LongTermDebtCurrent", "DebtCurrent"], instant=True)
    cash = annual(facts, ["CashAndCashEquivalentsAtCarryingValue"], instant=True)
    sti = annual(facts, ["ShortTermInvestments", "MarketableSecuritiesCurrent"], instant=True)
    shares_d = annual(facts, ["WeightedAverageNumberOfDilutedSharesOutstanding"], unit="shares")

    years = sorted(rev)
    if not years:
        sys.exit("no revenue facts found")
    y = years[-1]
    y3 = y - 3

    def g(d, yr=y):
        return d.get(yr)

    taxrate = (g(tax) / g(pretax)) if g(tax) and g(pretax) and g(pretax) > 0 else 0.21
    taxrate = min(max(taxrate, 0), 0.35)
    def ic(yr):
        e = g(eq, yr)
        if e is None:
            return None
        return e + (g(debt, yr) or 0) + (g(debt_c, yr) or 0) - (g(cash, yr) or 0) - (g(sti, yr) or 0)
    roic = (g(op) * (1 - taxrate) / ic(y)) if g(op) and ic(y) and ic(y) > 0 else None
    gm = g(gp) / g(rev) if g(gp) else None
    om = g(op) / g(rev) if g(op) else None
    conv = g(cfo) / g(op) if g(cfo) and g(op) and g(op) > 0 else None
    fcf = {yr: cfo[yr] - capex.get(yr, 0) for yr in cfo}
    rev_g = cagr(g(rev, y3), g(rev), 3)
    gp_g = cagr(g(gp, y3), g(gp), 3)
    op_g = cagr(g(op, y3), g(op), 3)
    fcf_g = cagr(fcf.get(y3), fcf.get(y), 3)

    # price
    price = hi = None
    try:
        ch = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1d")["chart"]["result"][0]
        price = ch["meta"]["regularMarketPrice"]
        closes = [c for c in ch["indicators"]["quote"][0]["close"] if c]
        hi = max(closes)
    except Exception as ex:
        print(f"(price fetch failed: {ex})")
    cover = facts.get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
    sh = max(cover, key=lambda e: e["end"])["val"] if cover else (shares_d[max(shares_d)] if shares_d else None)
    mcap = price * sh if price and sh else None
    netdebt = ((g(debt) or 0) + (g(debt_c) or 0) - (g(cash) or 0) - (g(sti) or 0))
    ev = mcap + netdebt if mcap else None
    ni_g = cagr(g(ni, y3), g(ni), 3)  # split-proof proxy for EPS growth
    pe = mcap / g(ni) if mcap and g(ni) and g(ni) > 0 else None
    peg = pe / (ni_g * 100) if pe and ni_g and ni_g > 0 else None
    pfcf = mcap / fcf[y] if mcap and fcf.get(y, 0) > 0 else None
    evebit = ev / g(op) if ev and g(op) and g(op) > 0 else None
    dd = price / hi - 1 if price and hi else None

    print(f"\n## {ticker} — {cf.get('entityName')}  (FY data: calendar {y}, SEC XBRL; price: Yahoo {dt.date.today()})\n")
    print(f"Price {price}  ·  1y high {hi and round(hi,2)}  ·  drawdown {pct(dd)}  ·  mcap {num(mcap)}  ·  EV {num(ev)}  ·  net debt {num(netdebt)}\n")
    print("| Metric | Value | Threshold | Pass |\n|---|---|---|---|")
    print("| **QUALITY** | | | |")
    row("ROIC (NOPAT / IC)", pct(roic), ">20%", roic and roic > 0.2)
    row("Gross margin", pct(gm), "top of industry", None)
    row("Operating margin", pct(om), "top of industry", None)
    row("GP growth vs revenue (3y)", f"{pct(gp_g)} vs {pct(rev_g)}", "GP > rev", (gp_g > rev_g) if gp_g and rev_g else None)
    row("OP growth vs revenue (3y)", f"{pct(op_g)} vs {pct(rev_g)}", "OP > rev", (op_g > rev_g) if op_g and rev_g else None)
    row("CFO / EBIT", pct(conv), ">70%", conv and conv > 0.7)
    print("| **GROWTH** | | | |")
    row("Revenue CAGR 3y (hist.)", pct(rev_g), ">7% fwd — check consensus", rev_g and rev_g > 0.07)
    row("FCF CAGR 3y", pct(fcf_g), "~10%+", fcf_g and fcf_g > 0.10)
    row("SBC % of FCF", pct(g(sbc) / fcf[y]) if g(sbc) and fcf.get(y, 0) > 0 else "n/a", "lower = cleaner", None)
    print("| **VALUE** | | | |")
    row("P/E (trailing)", f"{pe:.1f}x" if pe else "n/a", "", None)
    row(f"PEG (hist. 3y NI growth {pct(ni_g)})", f"{peg:.2f}" if peg else "n/a", "≤2 (use fwd growth)", peg and peg <= 2)
    row("P/FCF", f"{pfcf:.1f}x" if pfcf else "n/a", "vs history/peers", None)
    row("EV/EBIT", f"{evebit:.1f}x" if evebit else "n/a", "vs peers", None)
    row("Drawdown from 1y high", pct(dd), "ideas start at -20%+", dd is not None and dd <= -0.2)

    print("\n5y history:")
    print("| Year | Revenue | GP | OP | Net inc | CFO | FCF |\n|---|---|---|---|---|---|---|")
    for yr in years[-5:]:
        print(f"| {yr} | {num(g(rev,yr))} | {num(g(gp,yr))} | {num(g(op,yr))} | {num(g(ni,yr))} | {num(g(cfo,yr))} | {num(fcf.get(yr))} |")
    print(f"\nFor value.py: --fcf {fcf.get(y,0):.0f} --shares {sh or 0:.0f} --net-cash {-netdebt:.0f} --price {price}")


# ---------------- TOKEN ----------------
def llama(slug, dtype):
    try:
        d = get(f"https://api.llama.fi/summary/fees/{slug}?dataType={dtype}")
    except Exception:
        return None
    chart = [v for _, v in d.get("totalDataChart", [])]
    last = sum(chart[-365:]) if len(chart) >= 30 else None
    prev = sum(chart[-730:-365]) if len(chart) >= 730 else None
    ann30 = sum(chart[-30:]) * 365 / 30 if len(chart) >= 30 else None
    yoy = (last / prev - 1) if last and prev else None
    if yoy is None and len(chart) >= 395:  # <2y history: last 30d vs same 30d a year ago
        a, b = sum(chart[-30:]), sum(chart[-395:-365])
        yoy = (a / b - 1) if b else None
    return {"ttm": last, "prev": prev, "ann30": ann30, "yoy": yoy}


def token(cg, slug):
    c = get(f"https://api.coingecko.com/api/v3/coins/{cg}?localization=false&tickers=false&community_data=false&developer_data=false")
    m = c["market_data"]
    price, mcap, fdv = m["current_price"]["usd"], m["market_cap"]["usd"], m.get("fully_diluted_valuation", {}).get("usd")
    ath, dd = m["ath"]["usd"], m["ath_change_percentage"]["usd"] / 100
    circ, tot = m.get("circulating_supply"), m.get("max_supply") or m.get("total_supply")
    fees, revn, hold = llama(slug, "dailyFees"), llama(slug, "dailyRevenue"), llama(slug, "dailyHoldersRevenue")

    print(f"\n## {c['symbol'].upper()} — {c['name']}  (CoinGecko + DefiLlama, {dt.date.today()})\n")
    print(f"Price {price}  ·  ATH {ath}  ·  drawdown {pct(dd)}  ·  1y {m.get('price_change_percentage_1y') and round(m['price_change_percentage_1y'],1)}%")
    print(f"Mcap {num(mcap)}  ·  FDV {num(fdv)}  ·  float {pct(circ/tot) if circ and tot else 'n/a'}\n")
    print("| Metric | Value | Threshold | Pass |\n|---|---|---|---|")
    print("| **QUALITY** | | | |")
    tr = revn["ttm"] / fees["ttm"] if fees and revn and fees["ttm"] and revn["ttm"] else None
    row("Take rate (rev/fees, TTM)", pct(tr), "stable/rising", None)
    hr = hold["ttm"] / revn["ttm"] if hold and revn and hold["ttm"] and revn["ttm"] else None
    row("Holder share of revenue", pct(hr), "high; accrual must exist", hr and hr > 0.3)
    row("Organic fees / incentive ROI", "check manually", ">1x incentives", None)
    print("| **GROWTH** | | | |")
    row("Fees YoY (TTM)", pct(fees and fees["yoy"]), ">7%", fees and fees["yoy"] and fees["yoy"] > 0.07)
    row("Holder revenue YoY", pct(hold and hold["yoy"]), "~10%+", hold and hold["yoy"] and hold["yoy"] > 0.10)
    row("30d annualized vs TTM (holder)", f"{num(hold and hold['ann30'])} vs {num(hold and hold['ttm'])}", "momentum", None)
    print("| **VALUE** | | | |")
    for lbl, d in (("FDV / fees", fees), ("FDV / revenue", revn), ("FDV / holder rev (P/E)", hold)):
        v = fdv / d["ttm"] if fdv and d and d["ttm"] else None
        row(lbl, f"{v:.1f}x" if v else "n/a", "≤20x for P/E" if "holder" in lbl else "vs peers", (v <= 20) if v and "holder" in lbl else None)
    row("FDV / mcap (unlock overhang)", f"{fdv/mcap:.2f}x" if fdv and mcap else "n/a", "<1.3x clean", (fdv / mcap < 1.3) if fdv and mcap else None)
    row("Drawdown from ATH", pct(dd), "ideas start at -20%+", dd <= -0.2)
    if not hold or not hold["ttm"]:
        print("\n⚠️  No holders revenue on DefiLlama — confirm value accrual exists before continuing (Step 0).")
    supply = tot or circ
    print(f"\nFor value.py: --fcf {(hold and hold['ttm']) or 0:.0f} --shares {supply or 0:.0f} --net-cash 0 --price {price} --rate 0.15")
    print("(subtract annual token incentives/emissions from --fcf; add treasury net cash ex-own-token)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["stock", "token"])
    p.add_argument("ticker", nargs="?")
    p.add_argument("--cg")
    p.add_argument("--llama")
    a = p.parse_args()
    if a.kind == "stock":
        stock(a.ticker)
    else:
        token(a.cg or a.ticker, a.llama or a.cg or a.ticker)
