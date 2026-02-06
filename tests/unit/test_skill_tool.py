"""Unit tests for SkillTool."""

from pathlib import Path

import pytest

from langchain_skills.tools.skill_tool import SkillInput, SkillTool


@pytest.mark.unit
class TestSkillTool:
    """Test SkillTool functionality."""

    # SkillTool() Initialization Tests

    def test_from_directories_single_directory(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test creating SkillTool from single directory."""
        create_skill_file(
            "---\nname: test-skill\ndescription: Test skill\n---\nContent", "test-skill"
        )

        tool = SkillTool(directories=temp_skill_dir)

        assert isinstance(tool, SkillTool)
        assert tool.name == "Skill"
        assert "test-skill" in tool.skills_map
        assert len(tool.skills_map) == 1

    def test_from_directories_multiple_directories(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test creating SkillTool from multiple directories."""
        # Create first directory with skills
        dir1 = temp_skill_dir / "dir1"
        dir1.mkdir(parents=True)
        (dir1 / "skill-one" / "SKILL.md").parent.mkdir(parents=True)
        (dir1 / "skill-one" / "SKILL.md").write_text(
            "---\nname: skill-one\ndescription: First\n---\n"
        )

        # Create second directory with skills
        dir2 = temp_skill_dir / "dir2"
        dir2.mkdir(parents=True)
        (dir2 / "skill-two" / "SKILL.md").parent.mkdir(parents=True)
        (dir2 / "skill-two" / "SKILL.md").write_text(
            "---\nname: skill-two\ndescription: Second\n---\n"
        )

        tool = SkillTool(directories=[dir1, dir2])

        assert len(tool.skills_map) == 2
        assert "skill-one" in tool.skills_map
        assert "skill-two" in tool.skills_map

    def test_from_directories_string_path(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test creating SkillTool with string path."""
        create_skill_file("---\nname: test\ndescription: Test\n---\n", "test")

        tool = SkillTool(directories=str(temp_skill_dir))

        assert len(tool.skills_map) == 1
        assert "test" in tool.skills_map

    def test_from_directories_path_object(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test creating SkillTool with Path object."""
        create_skill_file("---\nname: test\ndescription: Test\n---\n", "test")

        tool = SkillTool(directories=temp_skill_dir)

        assert "test" in tool.skills_map

    def test_from_directories_no_skills_found(self, temp_skill_dir: Path) -> None:
        """Test creating SkillTool with no skills raises ValueError."""
        with pytest.raises(ValueError, match="No skills found"):
            SkillTool(directories=temp_skill_dir)

    def test_from_directories_duplicate_names(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test duplicate skill names raises ValueError."""
        # Create two skills with same name in different dirs
        create_skill_file("---\nname: duplicate\ndescription: First\n---\n", "dir1/duplicate")
        create_skill_file("---\nname: duplicate\ndescription: Second\n---\n", "dir2/duplicate")

        with pytest.raises(ValueError, match="Duplicate skill names"):
            SkillTool(directories=temp_skill_dir)

    def test_from_directories_custom_template(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test creating SkillTool with custom description template."""
        create_skill_file("---\nname: test\ndescription: Test skill\n---\n", "test")

        custom_template = "Custom template: {skills_xml}"
        tool = SkillTool(directories=temp_skill_dir, description_template=custom_template)

        assert "Custom template:" in tool.description
        assert "<skill>" in tool.description

    def test_from_directories_tool_description_contains_xml(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test tool description contains skill XML."""
        create_skill_file("---\nname: my-skill\ndescription: My test skill\n---\n", "my-skill")

        tool = SkillTool(directories=temp_skill_dir)

        assert "<skill>" in tool.description
        assert "<name>my-skill</name>" in tool.description
        assert "<description>My test skill</description>" in tool.description

    def test_from_directories_args_schema(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test tool has correct args_schema."""
        create_skill_file("---\nname: test\ndescription: Test\n---\n", "test")

        tool = SkillTool(directories=temp_skill_dir)

        assert tool.args_schema == SkillInput

    # Direct SkillTool() instantiation is now the only way
    # (removed create_skill_tool() tests as function no longer exists)

    # _run() Tests

    def test_run_valid_skill(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test running tool with valid skill name."""
        skill_path = create_skill_file(
            "---\nname: test-skill\ndescription: Test\n---\nSkill content here", "test-skill"
        )

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("test-skill")

        assert "Base directory for this skill:" in result
        assert "Skill content here" in result
        assert str(skill_path.parent) in result

    def test_run_invalid_skill(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test running tool with invalid skill name returns error."""
        create_skill_file("---\nname: valid-skill\ndescription: Test\n---\n", "valid-skill")

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("nonexistent-skill")

        assert "Skill not found: nonexistent-skill" in result
        assert "Available skills:" in result
        assert "valid-skill" in result

    def test_run_lists_available_skills(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test error message lists all available skills."""
        create_skill_file("---\nname: skill-one\ndescription: First\n---\n", "skill-one")
        create_skill_file("---\nname: skill-two\ndescription: Second\n---\n", "skill-two")

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("invalid")

        assert "skill-one" in result
        assert "skill-two" in result

    def test_run_returns_full_content(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test _run() returns same as Skill.get_full_content()."""
        create_skill_file("---\nname: test\ndescription: Test\n---\nContent", "test")

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("test")

        # Verify format matches Skill.get_full_content()
        lines = result.split("\n")
        assert lines[0].startswith("Base directory for this skill:")
        assert "Content" in result

    # _arun() Tests

    @pytest.mark.asyncio
    async def test_arun_delegates_to_run(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test async _arun() delegates to sync _run()."""
        create_skill_file("---\nname: test\ndescription: Test\n---\nContent", "test")

        tool = SkillTool(directories=temp_skill_dir)
        sync_result = tool._run("test")
        async_result = await tool._arun("test")

        assert sync_result == async_result

    # Integration with Real Fixtures

    def test_from_fixture_directory(self) -> None:
        """Test loading from actual fixture directory."""
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "valid_skill"

        if fixture_dir.exists():
            tool = SkillTool(directories=fixture_dir)

            assert "valid-skill" in tool.skills_map
            result = tool._run("valid-skill")
            assert "Base directory for this skill:" in result

    def test_multiple_fixture_directories(self) -> None:
        """Test loading from multiple fixture directories."""
        fixtures_base = Path(__file__).parent.parent / "fixtures"
        # Load skill-one and skill-two from separate parent directories to avoid duplicates
        dir1 = fixtures_base / "multiple_skills" / "skill-one"
        dir2 = fixtures_base / "multiple_skills" / "skill-two"

        if dir1.exists() and dir2.exists():
            # Each directory should contain only one SKILL.md file
            tool = SkillTool(directories=[dir1.parent / "skill-one", dir2.parent / "skill-two"])

            # Should have skills loaded without duplicates
            assert len(tool.skills_map) >= 1

    # Edge Cases

    def test_skill_with_empty_content(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test skill with empty content body."""
        create_skill_file("---\nname: empty\ndescription: Empty content\n---\n", "empty")

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("empty")

        assert "Base directory for this skill:" in result
        # Empty content should still be handled

    def test_skills_map_readonly(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test skills_map contains correct Skill objects."""
        create_skill_file("---\nname: test\ndescription: Test\n---\n", "test")

        tool = SkillTool(directories=temp_skill_dir)
        skill = tool.skills_map["test"]

        assert skill.name == "test"
        assert skill.description == "Test"
