# Rebound Investing

A Claude Code skill for researching beaten-down stocks and crypto tokens with Rebound Capital's framework.

It speeds up the research. It doesn't make the decision. Claude pulls the data, runs the numbers and argues the other side. At six points you give your own answer before seeing Claude's.

## The framework

Based on [Rebound Capital](https://reboundcapital.substack.com)'s published process.

Buy high-quality, growing businesses after a sharp drop, when the drop comes from sentiment rather than a broken business. Risk is the chance of a permanent loss, not volatility, so a good business gets less risky as its price falls.

- **Quality**: ROIC above 20%, margins at the top of the industry, cash from operations above 70% of EBIT.
- **Growth**: more than 7% a year over 3–5 years, with gross and operating profit growing faster than revenue.
- **Value**: PEG of 2 or less, and a price more than 20% below intrinsic value.
- **Valuation**: bear, base and bull cases, with a 20–30x exit multiple on final-year free cash flow. Buy only when the expected return is about 15% a year and reward to risk is at least 2:1.
- **Catalysts**: the 2–3 numbers the thesis depends on, and the event that will close the gap to fair value.
- **Sizing**: at most 15% in one position, added in tranches over 2–3 months.

## Install

```
git clone https://github.com/paultimfv/rebound-investing ~/.claude/skills/rebound-investing
```

Needs Python 3. No packages and no API keys.

## Use

In Claude Code:

```
rebound NFLX            quick screen: why it's down + QGV
deep dive NFLX          the full process
rebound HYPE            same for a token
review my position in NFLX
```

The scripts also run on their own:

```
python3 scripts/qgv.py stock NFLX
python3 scripts/qgv.py token --cg hyperliquid --llama hyperliquid
python3 scripts/value.py --fcf 9.46e9 --shares 4.1e9 --net-cash -4.4e9 --price 66 \
  --bear 0.08:20 --base 0.15:25 --bull 0.20:30
```

## How it's built

```
SKILL.md                  the 7 steps and 6 decision points Claude follows
references/framework.md   the full rules
references/crypto.md      how each stock metric maps to a token
references/deep-dive.md   the deep-dive sections
templates/deep-dive.md    the write-up, with the verdict in YAML frontmatter
scripts/qgv.py            QGV screen: SEC filings + Yahoo for stocks, CoinGecko + DefiLlama for tokens
scripts/value.py          three-scenario valuation, 15% return price, reward to risk, implied growth
```

The YAML frontmatter is the machine-readable verdict, so other tools can read it. The skill never places trades.

Not financial advice.
