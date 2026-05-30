from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import mplfinance as mpf

from common.config import Config
from tools.base import Tool

REPORTS_DIR = Path("reports")
CHARTS_DIR = Path("reports/charts")


class WriteReportTool(Tool):
    name = "write_report"

    def __init__(self, config: Config, yfinance_client=None) -> None:
        super().__init__(config)
        self._yfinance_client = yfinance_client

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "write_report",
                "description": (
                    "Write the final analysis report to a markdown file in the reports/ folder. "
                    "Call this as the last step after all data has been gathered and synthesised."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Uppercase ticker symbol, e.g. NVDA",
                        },
                        "content": {
                            "type": "string",
                            "description": "Full markdown report content to write to the file",
                        },
                    },
                    "required": ["ticker", "content"],
                },
            },
        }

    async def _generate_chart(self, slug: str) -> str | None:
        """Fetch OHLCV data, render a candlestick PNG, return the markdown embed string."""
        try:
            raw = await self._yfinance_client.call_tool(
                "get_price_history",
                {"symbol": slug, "period": "3mo", "interval": "1d"},
            )
            rows = json.loads(raw).get("data", [])
            if not rows:
                return None

            df = pd.DataFrame(rows)
            df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_convert(None)
            df = df.set_index("Date").sort_index()
            df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)

            CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = CHARTS_DIR / f"{slug}_3mo_{timestamp}.png"

            style = mpf.make_mpf_style(
                base_mpf_style="charles",
                marketcolors=mpf.make_marketcolors(
                    up="#26a69a",
                    down="#ef5350",
                    edge="inherit",
                    wick="inherit",
                    volume={"up": "#26a69a", "down": "#ef5350"},
                ),
                gridstyle=":",
                facecolor="#0d1117",
                edgecolor="#30363d",
                figcolor="#0d1117",
                gridcolor="#21262d",
                rc={
                    "axes.labelcolor": "#e6edf3",
                    "xtick.color": "#e6edf3",
                    "ytick.color": "#e6edf3",
                    "text.color": "#e6edf3",
                },
            )
            mpf.plot(
                df,
                type="candle",
                style=style,
                title=f"\n{slug} — 3mo Price Chart",
                ylabel="Price (USD)",
                volume=True,
                ylabel_lower="Volume",
                savefig=dict(fname=str(path), dpi=150, bbox_inches="tight"),
            )
            print(f"[write_report] chart → {path}")
            return f"![{slug} 3-Month Price Chart](charts/{path.name})"
        except Exception as e:
            print(f"[write_report] chart skipped: {e}")
            return None

    async def run(self, ticker: str, content: str) -> str:
        REPORTS_DIR.mkdir(exist_ok=True)
        slug = re.sub(r"[^A-Z0-9]", "", ticker.upper())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self._yfinance_client:
            chart_md = await self._generate_chart(slug)
            if chart_md:
                if "## 3. Price Chart" in content:
                    content = content.replace(
                        "## 3. Price Chart",
                        f"## 3. Price Chart\n\n{chart_md}",
                        1,
                    )
                else:
                    lines = content.split("\n")
                    insert_at = next(
                        (
                            i + 1
                            for i, line in enumerate(lines)
                            if line.startswith("# ")
                        ),
                        1,
                    )
                    lines.insert(insert_at, f"\n{chart_md}\n")
                    content = "\n".join(lines)

        path = REPORTS_DIR / f"{slug}_{timestamp}.md"
        path.write_text(content, encoding="utf-8")
        print(f"\n[write_report] → {path}")
        return f"Report written to {path}"
