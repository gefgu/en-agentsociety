"""Shared fixtures for PromptManager unit tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def prompt_manager():
    """Real PromptManager loaded from Python prompt classes."""
    from en_agentsociety.prompts.prompt_manager import PromptManager

    return PromptManager(prompts_dir="", active_config={})


@pytest.fixture
def mock_llm():
    """AsyncMock LLM. Set mock_llm.atext_request.return_value to control the response."""
    llm = MagicMock()
    llm.atext_request = AsyncMock(return_value='{"result": "ok"}')
    return llm


@pytest.fixture
def mock_memory():
    """AsyncMock memory with status/profile/stream sub-mocks."""
    memory = MagicMock()
    memory.status = MagicMock()
    memory.status.get = AsyncMock(return_value=None)
    memory.status.get_many = AsyncMock(side_effect=lambda keys: dict(keys))
    memory.status.update_many = AsyncMock(return_value=None)
    memory.profile = MagicMock()
    memory.profile.get = AsyncMock(return_value=None)
    memory.stream = MagicMock()
    memory.stream.search = AsyncMock(return_value=[])
    return memory
