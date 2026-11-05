---
name: rebound-investing
description: "Run Rebound Capital's QGV + drawdown process on any stock OR crypto token: screen, filter, deep dive, 3-scenario valuation, KPIs/catalysts, sizing, post-buy review. Use when the user says 'rebound', 'run the framework on X', 'QGV X', 'is X a rebound', 'deep dive X', 'should I buy X', 'X dumped, is it a buy', 'review my position in X', or pastes a ticker/token after a sharp drop. Accelerates the work; the user makes every judgment call."
---

# Rebound Investing — QGV drawdown framework (stocks + tokens)

Source: [Rebound Capital](https://reboundcapital.substack.com) ("Our investment process" + "QGV framework / watchlist"). Full condensed rules: `references/framework.md`. Token translation: `references/crypto.md`. Deep-dive sections: `references/deep-dive.md`.

## The contract: accelerate, don't replace

Claude does the legwork: pulls data, computes metrics, drafts the bear and short cases, runs the valuation math, and checks each rule. **The user makes the calls.** At each ✋ gate, stop and ask the user for their answer in one line *before* showing Claude's view. Then compare the two, and note where they differ and which rule applies. Don't fill a gate in for them, and don't skip one, even if they say "just tell me". Instead, give them the drafted options and let them pick.

Each step ends with a one-line **Rule** (the framework principle in play) and **Why** (the reasoning behind it). Over time the user should be able to say the rule before Claude does. If they get one wrong, correct them in one sentence.

Mode: `quick` = Steps 1–2 only (15 min, kill or continue). `full` = all steps. Default: quick. Offer full only if the idea passes Step 2.

## Step 0 — Classify the asset
Stock or token? Business type (compounder / cyclical / turnaround / financial / pre-revenue)? For a token, does it have **holder value accrual** (buyback, fee share, burn)? If it has no accrual and no credible path to it, stop: there's no FCF to value, so the framework doesn't apply. Say so and end.

## Step 1 — Why is it down? (the story)
Run `scripts/qgv.py` (it gets the drawdown from the high, metrics and flags). Categorize the source of the drop: earnings/guidance miss · sector selling off on a narrative · special situation (spin-off, court case, founder exit, unlock, exploit) · macro. Draft the market's story in two sentences.
✋ **Gate 1:** "Is the market punishing this for a *good* reason?" If yes → AVOID, done.
Rule: most ideas die here. Why: a drawdown is only an opportunity if the business didn't break.

## Step 2 — Filter (QGV)
Show the qgv.py table against the thresholds: ROIC >20%, margins at the top of the industry, GP and OP growing faster than revenue, CFO/EBIT >70%, expected 3–5y growth >7% (FCF growth ~10%+), PEG ≤2, price >20% below a rough IV. Thresholds are guides, not hard rules. Then answer the 4 filter questions (quality / narrative vs KPIs / fair or cheap / temporary?).
✋ **Gate 2:** "Q, G, V: which of the three fails, if any?" All three must be in their favor to continue.
Rule: QGV, all three. Why: quality without value is a lazy long; value without quality is a value trap.

## Step 3 — Deep dive (full mode)
Work through `references/deep-dive.md`. Rate each section 1–5. The five that matter most: **Moat · Pricing power (Porter's 5) · Management · Forensic accounting · Short thesis.** Claude writes the strongest short thesis it can.
✋ **Gate 3:** "Refute the short thesis in your own words, or concede it." If it can't be refuted (or is only valid in the very near term) → AVOID or HOLD.
Also check upstream: what are the suppliers and customers saying? Management guidance lags (the ASML lesson).

## Step 4 — Valuation (3 scenarios)
✋ **Gate 4:** The user sets the base-case growth and exit multiple first. Claude proposes the bear and bull cases and challenges their base.
- Base = the thesis in numbers. Bear = misses its own medium-term guide or underperforms the last 3–5y trend (no crash scenarios; position sizing handles tail risk). Bull = new products, markets or adoption succeed.
- Exit multiple on final-year FCF: **20–30x** (tokens: see crypto.md). This assumption matters more than any other.
- Run `scripts/value.py`. It gives IV per scenario, the 15%-CAGR buy price, reward:risk, margin of safety, and the reverse DCF (what the current price already discounts).
- Pass: price ≥20% below base IV · reward:risk ≥2:1 · price ≤ the 15%-CAGR price. Then ask: is the price discounting something between bear and base, or worse than bear? How does that compare with consensus?

## Step 5 — KPIs + catalysts
✋ **Gate 5 (the most important one):** "Which 2–3 numbers does this thesis rest on?" The user names them, and Claude challenges the list. Each KPI needs: current value, trend over the last 4–8 periods, the level that confirms the thesis, the level that breaks it, and its source and how often it updates.
Catalysts: name the event that closes the gap between price and IV (KPI inflection, ruling, new CEO, guide, unlock passing, buyback start). **Turnarounds: wait until the KPI turns before buying** (the LVMH and Novo lesson).
Rule: Amex. Why: Buffett tracked one number (usage), and that number was the whole bet.

## Step 6 — Rating + sizing
BUY only if: price < IV, the 15% CAGR return is achievable, the user is confident in the model, AND there's a credible catalyst. Otherwise HOLD or AVOID. Most names end in HOLD or AVOID, by design.
✋ **Gate 6:** The user gives the rating. If it feels comfortable, ask why it would be mispriced.
Sizing: based on quality × how bad the bear case is × how clear the catalyst is. Start small and add in tranches over 2–3 months (cheap gets cheaper first; the CSU lesson). Limits: ≤15% per name, ≤35% for the top 3, ≤30% per theme, always some cash. Tokens: halve the stock-equivalent size (see crypto.md).

## Step 7 — After buying (review mode: "review X")
Earnings or news: start with the KPIs vs prior periods. Ask "did anything change what the business is worth?" Ignore narratives and price-explaining headlines. Macro only counts if it hits this company more than others. Monthly or quarterly: rebuild from scratch. Which scenario is playing out? Has the moat changed? Decide add / hold / trim / sell. **Sell when the gap to IV closes and no catalysts remain** (Cochlear). Trim as the price approaches or exceeds IV (AMD).

## Output
Fill in `templates/deep-dive.md`. Its YAML frontmatter is the machine-readable verdict that the future execution agent (e.g. a broker or exchange agent) will read. Keep the field names stable. Never place an order from this skill. It produces a plan, and execution is a separate, explicitly confirmed step.
Save to the user's configured research folder (e.g. set in their CLAUDE.md); otherwise `./rebound/<TICKER>.md`. Confirm the location the first time. Re-runs append a dated `## Review YYYY-MM-DD` and update the frontmatter. Never overwrite past reviews.

## Data
- Stocks: `python3 scripts/qgv.py stock NVDA` (SEC EDGAR XBRL + Yahoo price). Forward estimates aren't in the script; get consensus from the web, and label it.
- Tokens: `python3 scripts/qgv.py token --cg hyperliquid --llama hyperliquid` (CoinGecko + DefiLlama). For anything onchain the APIs miss, read the chain directly over RPC.
- Valuation: `python3 scripts/value.py --help`.
Print the numbers with their source and as-of date. If a number is missing, say it's missing; never estimate one silently.
