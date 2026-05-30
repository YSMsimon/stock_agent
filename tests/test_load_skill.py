import pytest
from agents.base import load_skill, load_prompt


def test_load_skill_strips_frontmatter(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills" / "test_skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "---\nname: test\ndescription: a test skill\n---\n\n## Instructions\nDo the thing.",
        encoding="utf-8",
    )
    # point load_skill at our tmp skills dir
    import agents.base as base_module

    monkeypatch.setattr(base_module, "SKILLS_DIR", tmp_path / "skills")

    content = load_skill("test_skill")
    assert content.startswith("## Instructions")
    assert "name: test" not in content


def test_load_skill_no_frontmatter(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills" / "plain"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "## Plain skill\nNo frontmatter.", encoding="utf-8"
    )

    import agents.base as base_module

    monkeypatch.setattr(base_module, "SKILLS_DIR", tmp_path / "skills")

    content = load_skill("plain")
    assert content == "## Plain skill\nNo frontmatter."


def test_load_skill_missing_raises(tmp_path, monkeypatch):
    import agents.base as base_module

    monkeypatch.setattr(base_module, "SKILLS_DIR", tmp_path / "skills")

    with pytest.raises(FileNotFoundError, match="SKILL.md"):
        load_skill("nonexistent")


def test_load_prompt_missing_raises(tmp_path, monkeypatch):
    import agents.base as base_module

    monkeypatch.setattr(base_module, "PROMPTS_DIR", tmp_path / "prompts")

    with pytest.raises(FileNotFoundError, match="prompts/missing.md"):
        load_prompt("missing")
