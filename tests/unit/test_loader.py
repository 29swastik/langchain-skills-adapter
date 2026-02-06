"""Unit tests for SkillLoader."""

from pathlib import Path

import pytest

from langchain_skills.core.loader import SkillLoader
from langchain_skills.core.skill import Skill
from langchain_skills.exceptions import SkillLoadError, SkillNotFoundError, SkillValidationError


@pytest.mark.unit
class TestSkillLoader:
    """Test SkillLoader functionality."""

    # load_skill() Tests

    def test_load_skill_valid(
        self, temp_skill_dir: Path, create_skill_file, valid_skill_content: str
    ) -> None:
        """Test loading a valid skill file."""
        skill_path = create_skill_file(valid_skill_content, "test-skill")

        skill = SkillLoader.load_skill(skill_path)

        assert isinstance(skill, Skill)
        assert skill.name == "test-skill"
        assert skill.description == "A test skill for unit testing"
        assert "instructions for the agent" in skill.content

    def test_load_skill_minimal(
        self, temp_skill_dir: Path, create_skill_file, valid_skill_minimal: str
    ) -> None:
        """Test loading minimal valid skill."""
        skill_path = create_skill_file(valid_skill_minimal)

        skill = SkillLoader.load_skill(skill_path)

        assert skill.name == "minimal"
        assert skill.description == "Minimal skill"

    def test_load_skill_with_extra_fields(
        self, temp_skill_dir: Path, create_skill_file, skill_with_extra_fields: str
    ) -> None:
        """Test loading skill with extra frontmatter fields."""
        skill_path = create_skill_file(skill_with_extra_fields)

        skill = SkillLoader.load_skill(skill_path)

        assert skill.name == "extra-fields"
        assert skill.frontmatter["author"] == "Test Author"
        assert skill.frontmatter["version"] == "1.0.0"

    def test_load_skill_nonexistent_file(self, temp_skill_dir: Path) -> None:
        """Test loading non-existent file raises SkillNotFoundError."""
        nonexistent = temp_skill_dir / "nonexistent" / "SKILL.md"

        with pytest.raises(SkillNotFoundError, match="Skill file not found"):
            SkillLoader.load_skill(nonexistent)

    def test_load_skill_invalid_yaml(
        self, temp_skill_dir: Path, create_skill_file, invalid_yaml_content: str
    ) -> None:
        """Test loading skill with invalid YAML raises SkillLoadError."""
        skill_path = create_skill_file(invalid_yaml_content)

        with pytest.raises(SkillLoadError, match="Failed to parse YAML frontmatter"):
            SkillLoader.load_skill(skill_path)

    def test_load_skill_no_frontmatter(
        self, temp_skill_dir: Path, create_skill_file, no_frontmatter_content: str
    ) -> None:
        """Test loading skill without frontmatter raises SkillLoadError."""
        skill_path = create_skill_file(no_frontmatter_content)

        with pytest.raises(SkillLoadError, match="No YAML frontmatter found"):
            SkillLoader.load_skill(skill_path)

    def test_load_skill_missing_name(
        self, temp_skill_dir: Path, create_skill_file, missing_name_content: str
    ) -> None:
        """Test loading skill without name raises SkillValidationError."""
        skill_path = create_skill_file(missing_name_content)

        with pytest.raises(SkillValidationError, match="Missing required field: name"):
            SkillLoader.load_skill(skill_path)

    def test_load_skill_missing_description(
        self, temp_skill_dir: Path, create_skill_file, missing_description_content: str
    ) -> None:
        """Test loading skill without description raises SkillValidationError."""
        skill_path = create_skill_file(missing_description_content)

        with pytest.raises(SkillValidationError, match="Missing required field: description"):
            SkillLoader.load_skill(skill_path)

    def test_load_skill_invalid_name_format(
        self, temp_skill_dir: Path, create_skill_file, invalid_name_uppercase: str
    ) -> None:
        """Test loading skill with invalid name format raises SkillValidationError."""
        skill_path = create_skill_file(invalid_name_uppercase)

        with pytest.raises(SkillValidationError, match="only lowercase letters"):
            SkillLoader.load_skill(skill_path)

    # discover_skills() Tests

    def test_discover_skills_single(
        self, temp_skill_dir: Path, create_skill_file, valid_skill_content: str
    ) -> None:
        """Test discovering single skill in directory."""
        create_skill_file(valid_skill_content, "skill-one")

        skills = SkillLoader.discover_skills(temp_skill_dir)

        assert len(skills) == 1
        assert skills[0].name == "test-skill"

    def test_discover_skills_multiple_flat(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test discovering multiple skills in flat structure."""
        create_skill_file(
            "---\nname: skill-one\ndescription: First skill\n---\nContent 1", "skill-one"
        )
        create_skill_file(
            "---\nname: skill-two\ndescription: Second skill\n---\nContent 2", "skill-two"
        )

        skills = SkillLoader.discover_skills(temp_skill_dir)

        assert len(skills) == 2
        skill_names = {skill.name for skill in skills}
        assert "skill-one" in skill_names
        assert "skill-two" in skill_names

    def test_discover_skills_nested(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test discovering skills in nested directory structure."""
        create_skill_file("---\nname: top-level\ndescription: Top level skill\n---\n", "top-level")
        create_skill_file(
            "---\nname: nested-skill\ndescription: Nested skill\n---\n", "nested/deep/nested-skill"
        )

        skills = SkillLoader.discover_skills(temp_skill_dir)

        assert len(skills) == 2
        skill_names = {skill.name for skill in skills}
        assert "top-level" in skill_names
        assert "nested-skill" in skill_names

    def test_discover_skills_empty_directory(self, temp_skill_dir: Path) -> None:
        """Test discovering skills in empty directory returns empty list."""
        skills = SkillLoader.discover_skills(temp_skill_dir)

        assert skills == []

    def test_discover_skills_no_skill_files(self, temp_skill_dir: Path) -> None:
        """Test discovering skills in directory without SKILL.md files."""
        # Create some non-SKILL.md files
        (temp_skill_dir / "README.md").write_text("Not a skill")
        (temp_skill_dir / "other.txt").write_text("Also not a skill")

        skills = SkillLoader.discover_skills(temp_skill_dir)

        assert skills == []

    def test_discover_skills_nonexistent_directory(self) -> None:
        """Test discovering skills in non-existent directory raises error."""
        nonexistent = Path("/nonexistent/directory")

        with pytest.raises((FileNotFoundError, SkillNotFoundError)):
            SkillLoader.discover_skills(nonexistent)

    def test_discover_skills_from_fixture_directory(self) -> None:
        """Test discovering skills from test fixture directory."""
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "multiple_skills"

        if fixture_dir.exists():
            skills = SkillLoader.discover_skills(fixture_dir)

            assert len(skills) >= 3
            skill_names = {skill.name for skill in skills}
            assert "skill-one" in skill_names
            assert "skill-two" in skill_names
            assert "skill-three" in skill_names

    def test_discover_skills_mixed_valid_invalid(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test discovering skills with mix of valid and invalid files.

        Note: Current implementation raises on first invalid skill.
        """
        # Create one valid skill
        create_skill_file("---\nname: valid-skill\ndescription: Valid\n---\n", "valid-skill")

        # Create one invalid skill (missing name)
        create_skill_file("---\ndescription: Missing name\n---\n", "invalid-skill")

        # Current implementation raises SkillLoadError (wraps SkillValidationError)
        with pytest.raises((SkillValidationError, SkillLoadError)):
            SkillLoader.discover_skills(temp_skill_dir)

    def test_load_skill_path_preserved(
        self, temp_skill_dir: Path, create_skill_file, valid_skill_content: str
    ) -> None:
        """Test that loaded skill preserves original file path."""
        skill_path = create_skill_file(valid_skill_content, "my-skill")

        skill = SkillLoader.load_skill(skill_path)

        assert skill.path == skill_path
        assert skill.path.name == "SKILL.md"
        assert skill.base_directory == skill_path.parent
