import re
import pytest
from unittest.mock import AsyncMock, patch
from common.config import Config
from tools.write_report import WriteReportTool


def make_tool(tmp_path):
    config = Config.__new__(Config)
    config.model = "test-model"
    config.llm_api_key = "test-key"
    config.llm_api_url = "https://api.test.com"
    config.tavily_api_key = "test-tavily"
    tool = WriteReportTool(config, yfinance_client=None)
    return tool


@pytest.mark.asyncio
async def test_report_written_to_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tool = make_tool(tmp_path)
    result = await tool.run("NVDA", "# NVDA Report\n\nSome content.")
    assert "Report written to" in result
    reports = list(tmp_path.glob("reports/NVDA_*.md"))
    assert len(reports) == 1
    assert "Some content." in reports[0].read_text()


@pytest.mark.asyncio
async def test_ticker_slug_strips_special_chars(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tool = make_tool(tmp_path)
    await tool.run("BRK.B", "# Report")
    reports = list(tmp_path.glob("reports/BRKB_*.md"))
    assert len(reports) == 1


@pytest.mark.asyncio
async def test_chart_injected_after_section_heading(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config.__new__(Config)
    config.model = "test-model"
    config.llm_api_key = "test-key"
    config.llm_api_url = "https://api.test.com"
    config.tavily_api_key = "test-tavily"

    mock_client = AsyncMock()
    tool = WriteReportTool(config, yfinance_client=mock_client)

    chart_embed = "![AAPL 3-Month Price Chart](charts/AAPL_3mo_test.png)"
    tool._generate_chart = AsyncMock(return_value=chart_embed)

    content = "# AAPL Report\n\n## 3. Price Chart & Performance\n\nSome text."
    await tool.run("AAPL", content)

    reports = list(tmp_path.glob("reports/AAPL_*.md"))
    written = reports[0].read_text()
    assert chart_embed in written
    assert written.index(chart_embed) > written.index("## 3. Price Chart")


@pytest.mark.asyncio
async def test_chart_fallback_injected_after_title(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config.__new__(Config)
    config.model = "test-model"
    config.llm_api_key = "test-key"
    config.llm_api_url = "https://api.test.com"
    config.tavily_api_key = "test-tavily"

    mock_client = AsyncMock()
    tool = WriteReportTool(config, yfinance_client=mock_client)

    chart_embed = "![TSLA 3-Month Price Chart](charts/TSLA_3mo_test.png)"
    tool._generate_chart = AsyncMock(return_value=chart_embed)

    # no "## 3. Price Chart" heading — should fall back to after title
    content = "# TSLA Report\n\n## 1. Executive Summary\n\nContent."
    await tool.run("TSLA", content)

    reports = list(tmp_path.glob("reports/TSLA_*.md"))
    written = reports[0].read_text()
    assert chart_embed in written
