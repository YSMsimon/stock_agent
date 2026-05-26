---
name: search-skill
description: Teaches the agent how to construct targeted web search queries for stock research — covers tool parameters vs query operators, good/bad examples, and platform-specific patterns for social media (Reddit, X, StockTwits) and financial media (Bloomberg, Reuters, SEC EDGAR, and more).
---

You are equipped with a `web_search` tool and a `web_fetch` tool.

## Scope — what these tools are for

These tools are for **news, sentiment, and analysis only**:
- Breaking news and earnings reactions
- Analyst reports, upgrades, and downgrades
- Social media sentiment (Reddit, X, StockTwits)
- SEC filings (10-K, 10-Q, 8-K, Form 4)
- CEO statements and company announcements
- Macro commentary and market analysis
- Expert opinions and community DD

**Do NOT use `web_search` or `web_fetch` for:**
- Stock prices, OHLCV data, or quotes → handled by the market data agent
- Financial statements (income, balance sheet, cash flow) → handled by the market data agent
- Technical indicators, options chains, holder data → handled by the market data agent

This division keeps data accurate and fast — yfinance MCP tools return structured data directly; web tools return human-readable text that requires interpretation.

---

This skill teaches you how to use both the **tool parameters** and the **query string** correctly together.

Always build the most targeted call possible before invoking `web_search`.
Never fire a vague query — garbage in, garbage out.

---

## Two-Layer Approach

The `web_search` tool has two separate ways to filter results. Use each for its intended job:

| What you want to filter | Use | Why |
|---|---|---|
| Restrict to a domain | `include_domains` parameter | API-level filter — guaranteed, not a hint |
| Exclude a domain | `exclude_domains` parameter | API-level filter — guaranteed, not a hint |
| Limit by date | `days` parameter | Exact cutoff — more reliable than `after:` in query |
| Match exact phrase | `"..."` in query string | No tool param equivalent |
| Word must be in title | `intitle:` in query string | No tool param equivalent |
| Either of two terms | `OR` in query string | No tool param equivalent |
| Exclude a keyword | `-keyword` in query string | No tool param equivalent |
| Cashtag on social media | `$TICKER` in query string | No tool param equivalent |
| PDF only (SEC filings) | `filetype:pdf` in query string | No tool param equivalent |

**Rule:** Use tool params for domain and date. Use query string for content precision.

---

## Query String Operators (content precision — always relevant)

These have no tool param equivalent — use them in the query string every time:

| Operator | What it does | Example |
|---|---|---|
| `"..."` | Exact phrase match | `"NVDA earnings beat"` |
| `OR` | Either term | `"beat" OR "miss"` |
| `intitle:` | Word must be in page title | `intitle:"DD"` |
| `-keyword` | Exclude a keyword from results | `-rumor -speculation` |
| `$TICKER` | Cashtag for social media posts | `$NVDA` |
| `filetype:pdf` | PDF files only | `filetype:pdf "10-K"` |

---

## Tool Parameters (domain and date — prefer over query operators)

These are more reliable than putting `site:` or `after:` in the query string:

| Parameter | Type | What it does | Example |
|---|---|---|---|
| `include_domains` | `list[str]` | Restrict results to these domains | `["reddit.com", "x.com"]` |
| `exclude_domains` | `list[str]` | Remove these domains from results | `["pinterest.com"]` |
| `days` | `int` | Results from the last N days | `30` |
| `max_results` | `int` | How many results to return (max 10) | `5` |
| `search_depth` | `"basic"/"advanced"` | `advanced` returns full article text | `"advanced"` |

> **Note on `site:` in query string:** Still works and is not wrong. But when you have `include_domains` available, prefer that — it is a guaranteed API-level filter while `site:` in the query string is just a hint to the search engine.

> **Note on `after:` in query string:** Still works. But `days=30` is simpler and more reliable. Use `after:` in the query only when you need a specific date range (e.g. a tight window around earnings day) that `days` cannot express.

---

## Rules That Always Apply

1. **Set `days`** — stock data goes stale fast. Default to `days=30` unless the user specifies otherwise.
2. **Set `include_domains`** when targeting a specific site — more reliable than `site:` in the query.
3. **Quote multi-word phrases in the query** — `"interest rate cut"` not `interest rate cut`.
4. **Use `$TICKER` for social media, ticker name for news** — Reddit/X users write `$NVDA`; Reuters indexes `"NVIDIA"` or `"NVDA"`.
5. **Use `intitle:` for high-signal results** — if the term is in the page title, the page is almost certainly about that topic.
6. **Use `search_depth="advanced"` when you need to read the full article** — costs 2 credits but skips the need to call `web_fetch` separately.
7. **Use `OR` in the query for broader coverage** — `"beat" OR "miss"`, `"NVDA" OR "Nvidia"`.

---

## Good vs Bad Examples

All examples show the preferred format: clean query string for content, tool params for domain/date.

---

### Bad — vague query, no domain, no date
```
query: "NVDA stock"
```
### Good — content precision in query, domain and date via params
```
query          : '"$NVDA" "earnings beat"'
include_domains: ["reddit.com/r/wallstreetbets"]
days           : 30
```

---

### Bad — everything crammed into query string (old style)
```
query: "site:reddit.com/r/wallstreetbets $NVDA after:2026-05-25"
```
### Good — split correctly between query and params
```
query          : '"$NVDA" "short squeeze"'
include_domains: ["reddit.com/r/wallstreetbets"]
days           : 30
```

---

### Bad — no quotes on multi-word phrase
```
query          : "Federal Reserve interest rate"
include_domains: ["bloomberg.com"]
days           : 30
```
### Good — phrase quoted
```
query          : '"Federal Reserve" "interest rate"'
include_domains: ["bloomberg.com"]
days           : 30
```

---

### Bad — cashtag on a news site
```
query          : "$AAPL earnings"
include_domains: ["reuters.com"]
days           : 30
```
### Good — ticker name for news sites, cashtag for social
```
query          : '"Apple" OR "AAPL" "earnings"'
include_domains: ["reuters.com"]
days           : 30
```

---

### Bad — no `intitle:` on a research query (gets unrelated pages mentioning the word)
```
query          : '"NVDA" "DD"'
include_domains: ["reddit.com/r/stocks"]
days           : 90
```
### Good — `intitle:` ensures the page is actually a DD post
```
query          : '"NVDA" intitle:"DD"'
include_domains: ["reddit.com/r/stocks"]
days           : 90
```

---

### Bad — missing `OR` when you need multi-platform coverage
```
query          : '"$NVDA" earnings reaction'
include_domains: ["reddit.com"]
days           : 3
```
### Good — multi-domain via `include_domains`, precision in query
```
query          : '"$NVDA" "earnings" "beat" OR "miss"'
include_domains: ["reddit.com", "x.com", "stocktwits.com"]
days           : 3
```

---

### When `after:` in query IS still valid

Use `after:` + `before:` in the query string when you need a **specific date window** that `days` cannot express:

```
# Tight earnings reaction window — days=N counts from today, not from a specific date
query          : '"$AAPL" "earnings" after:2026-05-23 before:2026-05-25'
include_domains: ["x.com"]
days           : 30
```

---

## Social Media Platform Skills

Use social media when you need **sentiment, retail opinion, momentum, unusual activity, or early signals** before mainstream news picks them up.

---

### Reddit

**Best for:** retail sentiment, DD posts, options flow discussion, short squeeze candidates, sector mood.

**Key subreddits:**

| Subreddit | Focus |
|---|---|
| `r/wallstreetbets` | High-risk trades, meme stocks, options, sentiment extremes |
| `r/stocks` | General stock discussion, fundamentals, long-term |
| `r/investing` | Conservative, value investing, portfolio strategy |
| `r/options` | Options strategies, Greeks, unusual activity |
| `r/SecurityAnalysis` | Deep fundamental analysis, institutional-level DD |
| `r/StockMarket` | General market news and discussion |
| `r/pennystocks` | Small/micro-cap, high volatility |
| `r/dividends` | Dividend stocks, DRIP, income investing |
| `r/ETFs` | ETF discussion, sector ETFs |
| `r/ValueInvesting` | Graham/Buffett style, long-term thesis |

**Query patterns:**

```
# Sentiment on a ticker in WSB
query          : '"$NVDA"'
include_domains: ["reddit.com/r/wallstreetbets"]
days           : 30

# DD posts specifically
query          : '"NVDA" intitle:"DD"'
include_domains: ["reddit.com/r/stocks"]
days           : 90

# Short squeeze mentions
query          : '"$GME" "short squeeze"'
include_domains: ["reddit.com/r/wallstreetbets"]
days           : 30

# Options activity discussion
query          : '"NVDA" "unusual" OR "flow"'
include_domains: ["reddit.com/r/options"]
days           : 14

# Compare two tickers
query          : '"NVDA" OR "AMD" "comparison" OR "vs"'
include_domains: ["reddit.com/r/stocks"]
days           : 60
```

**When to search Reddit:**
- User asks "what does Reddit/WSB think about X"
- Checking retail sentiment before an earnings event
- Identifying meme stock momentum or short squeeze narrative
- Looking for crowd-sourced DD before making a fundamental call

---

### X (Twitter)

**Best for:** real-time breaking news, analyst tweets, CEO statements, fast-moving sentiment, earnings reaction in the first minutes.

**Query patterns:**

```
# Real-time ticker sentiment
query          : '"$NVDA"'
include_domains: ["x.com"]
days           : 7

# Earnings reaction — tight window, use after:/before: here since days counts from today
query          : '"$AAPL" "earnings" after:2026-05-23 before:2026-05-25'
include_domains: ["x.com"]
days           : 30

# Analyst or institution commentary
query          : '"$TSLA" "price target"'
include_domains: ["x.com"]
days           : 30

# CEO / exec statements
query          : '"Elon Musk" "Tesla"'
include_domains: ["x.com"]
days           : 14

# Breaking news reaction
query          : '"$NVDA" "beat" OR "miss"'
include_domains: ["x.com"]
days           : 3

# Fed / macro sentiment
query          : '"Federal Reserve" "rate cut"'
include_domains: ["x.com"]
days           : 14
```

**When to search X:**
- Earnings just dropped — check immediate market reaction
- Looking for analyst upgrades/downgrades announced on X before articles publish
- CEO or insider made a public statement
- Tracking a fast-moving news event (FDA approval, merger leak, etc.)

---

### StockTwits

**Best for:** pure trader sentiment, bullish/bearish ratio, retail trader positioning.

```
# Ticker sentiment feed
query          : '"$NVDA"'
include_domains: ["stocktwits.com"]
days           : 7

# Gaining social traction on a small-cap
query          : '"$TICKER"'
include_domains: ["stocktwits.com"]
days           : 3
```

**When to search StockTwits:**
- You want a pure retail trader temperature check
- Comparing bullish vs bearish sentiment ratio
- Checking if a small-cap is gaining social traction

---

### YouTube

**Best for:** earnings call recordings, CEO interviews, in-depth analysis videos, financial educator takes.

```
# Earnings call
query          : '"NVDA" "earnings call" "Q1 2026"'
include_domains: ["youtube.com"]

# CEO interview
query          : '"Jensen Huang" "interview"'
include_domains: ["youtube.com"]
days           : 90

# Analysis video
query          : '"NVDA" "stock analysis"'
include_domains: ["youtube.com"]
days           : 60
```

**When to search YouTube:**
- User wants to understand the earnings call narrative
- Looking for long-form fundamental analysis
- Finding CEO/CFO interviews for qualitative signals

---

### LinkedIn

**Best for:** executive moves, company announcements, hiring trends (signals growth/contraction).

```
# Executive move
query          : '"NVIDIA" "Chief" OR "VP" OR "Director" OR "appointed"'
include_domains: ["linkedin.com"]
days           : 90

# Company announcement
query          : '"NVIDIA" "announcement" OR "launch"'
include_domains: ["linkedin.com"]
days           : 30
```

**When to search LinkedIn:**
- Tracking C-suite changes (bearish signal if key execs leave)
- Checking hiring velocity as a growth proxy
- Finding official company announcements

---

## Financial Media Platform Skills

Use financial media when you need **verified facts, analyst reports, price targets, earnings data, SEC filings, and institutional-grade news.**

---

### Bloomberg

**Best for:** institutional news, macro analysis, Fed commentary, M&A, bond markets.

```
query          : '"NVDA" "earnings"'
include_domains: ["bloomberg.com"]
days           : 30

query          : '"Federal Reserve" "interest rate"'
include_domains: ["bloomberg.com"]
days           : 14

query          : '"NVDA" "price target"'
include_domains: ["bloomberg.com"]
days           : 60
```

---

### Reuters

**Best for:** breaking news, regulatory filings, global macro, corporate actions.

```
query          : '"Apple" OR "AAPL" "earnings"'
include_domains: ["reuters.com"]
days           : 30

query          : '"NVDA" "acquisition" OR "merger"'
include_domains: ["reuters.com"]
days           : 90

query          : '"SEC" "investigation" "Tesla"'
include_domains: ["reuters.com"]
days           : 90
```

---

### CNBC

**Best for:** TV segment transcripts, analyst interviews, market open/close recaps.

```
query          : '"NVDA" "analyst" "price target"'
include_domains: ["cnbc.com"]
days           : 30

query          : '"AAPL" "earnings" "beat" OR "miss"'
include_domains: ["cnbc.com"]
days           : 14
```

---

### MarketWatch

**Best for:** earnings summaries, stock news, options expiry, retail-friendly analysis.

```
query          : '"NVDA" "earnings"'
include_domains: ["marketwatch.com"]
days           : 30

query          : '"NVDA" "short interest"'
include_domains: ["marketwatch.com"]
days           : 30
```

---

### Seeking Alpha

**Best for:** long-form analyst articles, bull/bear thesis, dividend analysis, sector deep dives.

```
query          : '"NVDA" "analysis"'
include_domains: ["seekingalpha.com"]
days           : 60
search_depth   : "advanced"

query          : '"NVDA" "bear case" OR "bull case"'
include_domains: ["seekingalpha.com"]
days           : 90

query          : '"NVDA" "dividend"'
include_domains: ["seekingalpha.com"]
days           : 90
```

---

### Wall Street Journal (WSJ)

**Best for:** investigative journalism, macro policy, corporate governance, in-depth features.

```
query          : '"NVDA"'
include_domains: ["wsj.com"]
days           : 30

query          : '"Federal Reserve" "Powell"'
include_domains: ["wsj.com"]
days           : 14
```

---

### Financial Times (FT)

**Best for:** global markets, European/Asian stock coverage, macro economics, trade policy.

```
query          : '"NVDA"'
include_domains: ["ft.com"]
days           : 30

query          : '"China" "semiconductor" "export" OR "tariff"'
include_domains: ["ft.com"]
days           : 90
```

---

### Barron's

**Best for:** weekend deep-dives, stock picks, options strategies, value/growth calls.

```
query          : '"NVDA"'
include_domains: ["barrons.com"]
days           : 60

query          : '"buy" OR "sell" "recommendation"'
include_domains: ["barrons.com"]
days           : 30
```

---

### Benzinga

**Best for:** options flow alerts, pre-market movers, unusual activity, fast news.

```
query          : '"NVDA" "unusual options" OR "unusual activity"'
include_domains: ["benzinga.com"]
days           : 7

query          : '"NVDA" "price target" "raised" OR "lowered"'
include_domains: ["benzinga.com"]
days           : 30
```

---

### Investopedia

**Best for:** understanding financial concepts and metric definitions — use for context, not news.

```
query          : '"price to earnings ratio" explained'
include_domains: ["investopedia.com"]

query          : '"VWAP" "how to"'
include_domains: ["investopedia.com"]
```

---

### The Motley Fool

**Best for:** long-term stock picks, beginner-friendly analysis, growth stock coverage.

```
query          : '"NVDA" "analysis" OR "outlook"'
include_domains: ["fool.com"]
days           : 90

query          : '"NVDA" "buy" OR "sell"'
include_domains: ["fool.com"]
days           : 60
```

---

### Zacks Investment Research

**Best for:** earnings estimates, EPS revisions, analyst rank changes.

```
query          : '"NVDA" "earnings estimate" OR "EPS revision"'
include_domains: ["zacks.com"]
days           : 30

query          : '"NVDA" "rank" OR "upgrade" OR "downgrade"'
include_domains: ["zacks.com"]
days           : 30
```

---

### Yahoo Finance

**Best for:** quick price data, earnings calendar, press releases, community sentiment.

```
query          : '"NVDA" "earnings"'
include_domains: ["finance.yahoo.com"]
days           : 30

query          : '"NVDA" "press release"'
include_domains: ["finance.yahoo.com"]
days           : 14
```

---

## Stock-Specific Platform Skills

---

### SEC EDGAR

**Best for:** 10-K (annual), 10-Q (quarterly), 8-K (material events), S-1 (IPO), insider filings (Form 4).

> Prefer `web_fetch` with a direct EDGAR URL when you know the filing type — it is faster and more precise than searching.

```
# Search for filing type
query          : '"NVIDIA" "10-K"'
include_domains: ["sec.gov"]
days           : 365

query          : '"NVIDIA" "Form 4"'
include_domains: ["sec.gov"]
days           : 90

query          : '"NVIDIA" "8-K"'
include_domains: ["sec.gov"]
days           : 30

# Direct fetch — use web_fetch for a known EDGAR URL
url: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=NVIDIA&type=10-K
```

**When to use EDGAR:** Always for official financial statements, insider trades, or regulatory filings. Never trust a secondary source — go directly to EDGAR.

---

### TradingView

**Best for:** chart ideas, technical analysis scripts, community trade setups.

```
query          : '"NVDA" "idea" OR "setup"'
include_domains: ["tradingview.com"]
days           : 30

query          : '"NVDA" "support" OR "resistance"'
include_domains: ["tradingview.com"]
days           : 30
```

---

### Finviz

**Best for:** stock screener data, insider transactions, news aggregation, heat maps.

```
query          : '"NVDA" "insider"'
include_domains: ["finviz.com"]
days           : 30
```

---

### Macrotrends

**Best for:** long historical financial data (10–20 year revenue, EPS, margins, P/E history). No `days` needed — this is historical data.

```
query          : '"NVDA" "revenue"'
include_domains: ["macrotrends.net"]

query          : '"NVDA" "net profit margin"'
include_domains: ["macrotrends.net"]

query          : '"NVDA" "price earnings ratio"'
include_domains: ["macrotrends.net"]
```

---

### Gurufocus

**Best for:** institutional guru portfolios, intrinsic value estimates, moat ratings.

```
query          : '"NVDA" "intrinsic value" OR "DCF"'
include_domains: ["gurufocus.com"]
days           : 90
```

---

### Morningstar

**Best for:** star ratings, fair value estimates, economic moat, analyst reports, ETF analysis.

```
query          : '"NVDA" "fair value"'
include_domains: ["morningstar.com"]
days           : 90

query          : '"NVDA" "moat"'
include_domains: ["morningstar.com"]
days           : 180
```

---

## Multi-Source Combined Queries

Use `include_domains` with multiple entries when you want broad coverage in one call.

```
# Earnings coverage across major outlets
query          : '"NVDA" "earnings" "beat" OR "miss"'
include_domains: ["bloomberg.com", "reuters.com", "cnbc.com"]
days           : 7

# Analyst price target changes
query          : '"NVDA" "price target" "raised" OR "lowered"'
include_domains: ["benzinga.com", "marketwatch.com", "cnbc.com"]
days           : 30

# Social sentiment sweep
query          : '"$NVDA" "earnings"'
include_domains: ["reddit.com", "x.com", "stocktwits.com"]
days           : 3

# Insider and institutional activity
query          : '"NVIDIA" "insider" "buy" OR "sell"'
include_domains: ["sec.gov", "finviz.com", "gurufocus.com"]
days           : 90

# Macro impact on sector
query          : '"semiconductor" "tariff" OR "export ban"'
include_domains: ["bloomberg.com", "ft.com", "wsj.com"]
days           : 90
```

---

## Decision Guide — Which Platform to Search First

| User asks about | `include_domains` first | Then |
|---|---|---|
| "What does Reddit think about X" | `reddit.com/r/wallstreetbets` | `reddit.com/r/stocks` |
| "Latest earnings news" | `reuters.com`, `bloomberg.com` | `cnbc.com` |
| "Analyst price target" | `benzinga.com` | `marketwatch.com` |
| "Insider buying/selling" | `sec.gov` (Form 4 via web_fetch) | `finviz.com` |
| "Long-term revenue trend" | `macrotrends.net` | `gurufocus.com` |
| "Fair value / DCF estimate" | `morningstar.com` | `gurufocus.com` |
| "Options unusual activity" | `benzinga.com` | `reddit.com/r/options` |
| "Breaking news right now" | `x.com` | `reuters.com` |
| "Technical analysis setup" | `tradingview.com` | `reddit.com/r/stocks` |
| "SEC filing / 10-K / 10-Q" | `web_fetch` direct EDGAR URL | — |
| "Short squeeze potential" | `reddit.com/r/wallstreetbets` | `finviz.com` |
| "Macro / Fed impact" | `bloomberg.com` | `ft.com` |
| "CEO interview or statement" | `x.com` | `youtube.com` |
| "Dividend analysis" | `seekingalpha.com` | `reddit.com/r/dividends` |
