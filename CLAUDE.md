# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python3 main.py
```

This starts the CLI chat loop. Type `/compact` to compress conversation history, `/exit` or Ctrl-C to quit.

**Environment** — requires `.env` in the project root:
```
MODEL="deepseek-v4-flash"
LLM_API_KEY="..."
LLM_URL="https://api.deepseek.com"
TAVILY_API_KEY="..."
```

**Dependencies:**
```bash
pip install -r requirements.txt
pip install yfinance-mcp   # MCP server (separate package)
```

## Architecture

This is a **CLI-only** multi-agent stock analysis system. There is no web UI.

### Agent hierarchy

```
OrchestratorAgent          ← user-facing, drives the full conversation
├── RunMarketDataTool       ← wraps MarketDataAgent as an LLM-callable tool
├── RunNewsSentimentTool    ← wraps NewsSentimentAgent as an LLM-callable tool
└── WriteReportTool         ← writes .md report + auto-generates candlestick chart PNG
        │
        ├── MarketDataAgent         ← calls yfinance-mcp tools directly
        │       └── MCPTool × 13   ← one MCPTool per yfinance-mcp tool
        │
        └── NewsSentimentAgent      ← calls Tavily web search
                └── WebSearchTool / WebFetchTool
```

`RunMarketDataTool` and `RunNewsSentimentTool` execute in **parallel** via `asyncio.gather` when the orchestrator calls both in a single LLM response.

### Base agent (`agents/base.py`)

All agents inherit from `Agent`. Key methods:
- `stream_chat(user_message)` — full agentic loop: builds messages → runs tool loop → streams final response
- `_run_tool_loop(messages)` — iterates up to 10 times: LLM call → parallel tool execution → append results
- `_execute_tool_call(tool_call)` — dispatches a single tool call by name

All LLM calls use `extra_body={"thinking": {"type": "disabled"}}` to suppress DeepSeek thinking mode. Remove this if switching to a non-thinking model (OpenAI, etc.).

### Memory (`agents/memory.py`)

Each agent has a `MemorySystem` that persists conversation history to `.stock_agent/{agent_name}.json`. Sub-agents (`MarketDataAgent`, `NewsSentimentAgent`) call `memory.clear()` before each invocation — they are stateless between orchestrator calls.

### Tools

| File | Purpose |
|------|---------|
| `tools/base.py` | Abstract `Tool` base class |
| `tools/mcp_tool.py` | Wraps a yfinance-mcp tool definition into a `Tool` |
| `tools/run_market_data.py` | Runs `MarketDataAgent` as a sub-agent tool |
| `tools/run_news_sentiment.py` | Runs `NewsSentimentAgent` as a sub-agent tool |
| `tools/write_report.py` | Writes `.md` report + generates chart via mplfinance |

### MCP client (`mcp_client/yfinance_client.py`)

Spawns `yfinance-mcp` as a subprocess over stdio. `connect()` must be called before use (done in `OrchestratorAgent.setup()`). `self.tools` is populated with the server's tool list after `connect()`. `MarketDataAgent` filters this list with `_TOOL_NAMES` to expose only the 13 relevant tools.

### Skills and prompts

- `prompts/{name}.md` — system prompt for each agent, loaded by `Agent.__init__`
- `skills/{name}/SKILL.md` — additional skill instructions appended to agent system prompts; frontmatter (`---`) is stripped automatically
- The orchestrator appends `skills/report/SKILL.md` (report format rules) to its system prompt
- `NewsSentimentAgent` appends `skills/search/SKILL.md` (search query construction guide)

### Report output

Reports are saved to `reports/{TICKER}_{timestamp}.md`. Charts are saved to `reports/charts/{TICKER}_3mo_{timestamp}.png` and embedded as relative paths (`charts/...`) so markdown viewers resolve them correctly when opening the `.md` file from the `reports/` folder.

### Context compaction

`/compact` in the CLI uses `CompactorAgent` (driven by `prompts/compactor.md`) to summarise old messages. It keeps the last 10 messages verbatim and replaces everything older with a single summary message.
