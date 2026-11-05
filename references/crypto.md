# Applying QGV to tokens

Precondition: the token must have **holder value accrual** (buybacks, fee switch, burn, staking paid in real revenue rather than emissions), or a dated, credible path to it. Without that there's no FCF, so the framework doesn't apply. Say so and stop.

## Translation table
| Equity concept | Token equivalent | Notes |
|---|---|---|
| Revenue | Fees paid by users (DefiLlama `dailyFees`) | |
| Gross profit | Protocol revenue (`dailyRevenue`), net of what goes to LPs and suppliers | take rate = revenue / fees ≈ gross margin |
| FCF / earnings | **Holder revenue** (`dailyHoldersRevenue`: buybacks + distributions) **minus token incentives/emissions paid out** | "real yield." Emissions are SBC: always subtract them |
| Shares outstanding | Circulating supply. Use **FDV** for the valuation and mcap for float | |
| Dilution / SBC | Unlock schedule + emissions per year as a % of supply | dilution of >5%/yr is a red flag |
| Buybacks | Programmatic buyback (e.g. an assistance fund). Check onchain that it happens | |
| ROIC | Revenue ÷ incentives spent (and ÷ treasury capital deployed) | >1 means usage isn't just being paid for |
| CFO/EBIT (earnings quality) | Share of fees that are organic: not wash trading, not incentive-farmed, not self-dealing | check unique users and fee concentration |
| Moat | Liquidity network effects, integrations, brand, switching costs, regulatory position | is market share stable through an incentive war? |
| Pricing power | Can it hold its take rate while competitors cut fees? | |
| Management | Team track record, insider and VC unlock behavior, governance, treasury discipline | |
| Forensic checks | Wash volume, points-farming spikes, treasury sales, related-party revenue, revenue tied to one market maker or whale | |
| Earnings miss | Unlock overhang, exploit, a KPI miss (volume or share drops), loss of a key integration | |
| 13F | Fund wallets, onchain smart money, fund portfolio disclosures, token treasury companies | |
| Special situations | Fee switch vote, ETF/listing, legal ruling, buyback start, exploit recovery, airdrop overhang ending | |

## Valuation adjustments
- Discount rate: 15–20% (vs ~10% for equities).
- Exit multiple on final-year holder FCF: **10–20x** (tokens derate harder, there are no legal claims on cash flows, and there's governance risk). 20x is the ceiling unless accrual is contractual and buybacks are proven.
- Use FDV, or supply in year 5 after unlocks, as the denominator. Never use circulating supply alone.
- Bear case: include a fee-war compression of the take rate and the full unlock overhang.

## Sizing
Halve the stock-equivalent position size. Cap any single token at 7.5% of the portfolio, and all crypto under one ~30% theme limit.

## Sources (free public APIs)
DefiLlama API (fees, revenue, holders revenue, TVL) · CoinGecko (price, supply, ATH) · project dashboards and docs (buyback wallets, unlock schedules) · direct RPC for onchain checks (buyback wallet balances, treasury moves) · Shoal Intel MCP for events (unlocks, exploits, governance).
