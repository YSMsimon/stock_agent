import json
import pytest
from agents.memory import MemorySystem


def test_add_message(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")
    assert mem.messages == [{"role": "user", "content": "hello"}]


def test_multiple_messages(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")
    mem.add_message("assistant", "hi there")
    assert len(mem.messages) == 2
    assert mem.messages[1]["role"] == "assistant"


def test_clear(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")
    mem.clear()
    assert mem.messages == []


def test_persists_to_disk(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")

    # load a second instance from the same path — should see saved messages
    mem2 = MemorySystem("test", base_dir=tmp_path)
    assert mem2.messages == [{"role": "user", "content": "hello"}]


def test_clear_persists_to_disk(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")
    mem.clear()

    mem2 = MemorySystem("test", base_dir=tmp_path)
    assert mem2.messages == []


def test_get_messages_for_llm_returns_copy(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.add_message("user", "hello")
    msgs = mem.get_messages_for_llm()
    msgs.append({"role": "user", "content": "injected"})
    # original should be unchanged
    assert len(mem.messages) == 1


def test_corrupted_json_recovers(tmp_path):
    mem = MemorySystem("test", base_dir=tmp_path)
    mem.memory_path.write_text("not valid json", encoding="utf-8")

    mem2 = MemorySystem("test", base_dir=tmp_path)
    assert mem2.messages == []
