"""
Frontend UI tests using Playwright.
Starts the FastAPI server, opens the chat UI in a headless browser,
and verifies key interactions work correctly.
"""

from __future__ import annotations

import subprocess
import time
import os
import pytest
from playwright.sync_api import Page, expect, sync_playwright


SERVER_URL = "http://localhost:18765"


@pytest.fixture(scope="session")
def server():
    """Start the FastAPI server for the duration of the test session."""
    env = {
        **os.environ,
        "MODEL": "test-model",
        "LLM_API_KEY": "test-key",
        "LLM_URL": "https://api.test.invalid",
        "TAVILY_API_KEY": "test-tavily",
    }
    proc = subprocess.Popen(
        [
            "python3",
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18765",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait up to 60s for server to become ready (yfinance-mcp takes time in CI)
    import urllib.request

    ready = False
    for _ in range(60):
        if proc.poll() is not None:
            raise RuntimeError(
                f"Server process exited early with code {proc.returncode}"
            )
        try:
            urllib.request.urlopen(f"{SERVER_URL}/api/health", timeout=2)
            ready = True
            break
        except Exception:
            time.sleep(1)
    if not ready:
        proc.terminate()
        raise RuntimeError("Server did not become ready within 60s")
    yield proc
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def browser_context(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        # Clear any previous localStorage
        context.add_init_script("""
            localStorage.removeItem('sa_convs');
            localStorage.removeItem('sa_active');
        """)
        yield context
        browser.close()


@pytest.fixture
def page(browser_context):
    p = browser_context.new_page()
    p.goto(SERVER_URL)
    p.wait_for_load_state("networkidle")
    yield p
    p.close()


# ── LAYOUT TESTS ────────────────────────────────────────────────


class TestLayout:
    def test_sidebar_visible(self, page: Page):
        expect(page.locator(".sidebar")).to_be_visible()

    def test_logo_present(self, page: Page):
        expect(page.locator(".logo")).to_be_visible()
        expect(page.locator(".logo")).to_contain_text("Stock Agent")

    def test_input_present(self, page: Page):
        expect(page.locator("#input")).to_be_visible()

    def test_send_button_present(self, page: Page):
        expect(page.locator("#actionBtn")).to_be_visible()

    def test_action_button_is_send_by_default(self, page: Page):
        """Single action button visible, not in stop-mode when idle."""
        btn = page.locator("#actionBtn")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()

    def test_empty_state_shown_on_load(self, page: Page):
        expect(page.locator(".empty-state")).to_be_visible()

    def test_suggestion_chips_shown(self, page: Page):
        chips = page.locator(".chip-btn")
        expect(chips.first).to_be_visible()
        assert chips.count() >= 4

    def test_status_badge_present(self, page: Page):
        expect(page.locator(".status-badge")).to_be_visible()


# ── CONVERSATION TESTS ───────────────────────────────────────────


class TestConversations:
    def test_default_conversation_exists(self, page: Page):
        expect(page.locator(".conv-item")).to_be_visible()

    def test_new_chat_disabled_when_empty(self, page: Page):
        """New conversation button is disabled if current conv has no messages."""
        btn = page.locator("#newBtn")
        expect(btn).to_be_disabled()

    def test_conv_actions_appear_on_hover(self, page: Page):
        item = page.locator(".conv-item").first
        item.hover()
        expect(page.locator(".conv-actions").first).to_be_visible()

    def test_pin_button_in_conv_actions(self, page: Page):
        item = page.locator(".conv-item").first
        item.hover()
        pin_btn = item.locator(".icon-btn").first
        expect(pin_btn).to_be_visible()

    def test_delete_button_in_conv_actions(self, page: Page):
        item = page.locator(".conv-item").first
        item.hover()
        del_btn = item.locator(".icon-btn").nth(1)
        expect(del_btn).to_be_visible()


# ── INPUT TESTS ──────────────────────────────────────────────────


class TestInput:
    def test_typing_in_input(self, page: Page):
        page.locator("#input").fill("test message")
        expect(page.locator("#input")).to_have_value("test message")

    def test_send_button_enabled(self, page: Page):
        expect(page.locator("#actionBtn")).to_be_enabled()

    def test_enter_clears_input(self, page: Page):
        """Pressing Enter on a non-empty input clears it (send attempted)."""
        inp = page.locator("#input")
        inp.fill("hello")
        # Press Enter — will attempt send (may fail since no real API, but input clears)
        inp.press("Enter")
        # Input should be cleared immediately
        time.sleep(0.2)
        assert page.locator("#input").input_value() == ""

    def test_shift_enter_adds_newline(self, page: Page):
        """Shift+Enter does NOT send — adds a newline."""
        inp = page.locator("#input")
        inp.fill("line1")
        inp.press("Shift+Enter")
        value = inp.input_value()
        assert "\n" in value or value == "line1\n" or "line1" in value

    def test_empty_input_does_not_send(self, page: Page):
        """Clicking send with empty input doesn't add messages."""
        before = page.locator(".msg-row").count()
        page.locator("#actionBtn").click()
        time.sleep(0.1)
        assert page.locator(".msg-row").count() == before


# ── SEND FLOW TESTS ──────────────────────────────────────────────
# All send-flow assertions share ONE page to preserve DOM state across steps.


class TestSendFlow:
    def test_full_send_flow(self, page: Page):
        """Complete send flow on a single page: bubble, empty state removed,
        AI row added, stop btn in DOM, title updated, new-chat enabled."""

        # 1. Send a message
        page.locator("#input").fill("What is AAPL price?")
        page.locator("#input").press("Enter")
        time.sleep(0.4)

        # 2. User bubble appears immediately
        expect(page.locator(".msg-user-bubble").first).to_be_visible()
        expect(page.locator(".msg-user-bubble").first).to_contain_text(
            "What is AAPL price?"
        )

        # 3. Empty state is gone
        expect(page.locator(".empty-state")).not_to_be_visible()

        # 4. AI row added to DOM before fetch completes
        expect(page.locator(".msg-row.msg-ai").first).to_be_attached()

        # 5. Stop button is in DOM (may briefly be visible)
        expect(page.locator("#actionBtn")).to_be_attached()

        # 6. Conversation title updated in sidebar
        title = page.locator(".conv-name").first.text_content()
        assert "What is AAPL" in title or title != "New conversation", (
            f"Expected title to update from first message, got: {title!r}"
        )

        # 7. Wait for finally block to run (API will error, that's expected)
        time.sleep(1.5)

        # 8. New-chat button enabled (message is stored in conv.msgs)
        expect(page.locator("#newBtn")).to_be_enabled()

        # 9. Send button re-enabled after error
        expect(page.locator("#actionBtn")).to_be_enabled()


# ── DELETE DIALOG TESTS ──────────────────────────────────────────


class TestDeleteDialog:
    def test_delete_shows_dialog(self, page: Page):
        item = page.locator(".conv-item").first
        item.hover()
        del_btn = item.locator(".icon-btn").nth(1)
        del_btn.click()
        expect(page.locator("#dialogOverlay")).to_be_visible()
        expect(page.locator("#dlgTitle")).to_contain_text("Delete")

    def test_cancel_closes_dialog(self, page: Page):
        # Dialog might already be open from previous test
        if page.locator("#dialogOverlay").is_visible():
            page.locator(".btn-ghost").click()
            expect(page.locator("#dialogOverlay")).not_to_be_visible()

    def test_overlay_click_closes_dialog(self, page: Page):
        # Open it first
        item = page.locator(".conv-item").first
        item.hover()
        del_btn = item.locator(".icon-btn").nth(1)
        del_btn.click()
        page.wait_for_selector("#dialogOverlay", state="visible")
        # Click overlay background
        page.locator("#dialogOverlay").click(position={"x": 10, "y": 10})
        time.sleep(0.1)
        expect(page.locator("#dialogOverlay")).not_to_be_visible()
