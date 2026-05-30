import pytest
from unittest.mock import patch
from common.config import Config


def make_config(**overrides):
    defaults = {
        "MODEL": "test-model",
        "LLM_API_KEY": "test-key",
        "LLM_URL": "https://api.test.com",
        "TAVILY_API_KEY": "test-tavily",
    }
    env = {**defaults, **overrides}
    with patch.dict("os.environ", env, clear=True):
        return Config()


def test_validate_passes_with_all_vars():
    config = make_config()
    config.validate()  # should not raise


def test_validate_fails_missing_model():
    config = make_config()
    config.model = None
    with pytest.raises(ValueError, match="MODEL"):
        config.validate()


def test_validate_fails_missing_api_key():
    config = make_config()
    config.llm_api_key = None
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        config.validate()


def test_validate_fails_missing_url():
    config = make_config()
    config.llm_api_url = None
    with pytest.raises(ValueError, match="LLM_API_URL"):
        config.validate()


def test_validate_fails_missing_tavily():
    config = make_config()
    config.tavily_api_key = None
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        config.validate()


def test_config_reads_env_vars():
    config = make_config(MODEL="gpt-4o", LLM_URL="https://api.openai.com/v1")
    assert config.model == "gpt-4o"
    assert config.llm_api_url == "https://api.openai.com/v1"
