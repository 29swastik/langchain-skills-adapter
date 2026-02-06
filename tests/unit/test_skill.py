"""Unit tests for Skill dataclass."""

from pathlib import Path

import pytest

from langchain_skills.core.skill import Skill


@pytest.mark.unit
class TestSkill:
    """Test Skill dataclass functionality."""

    def test_create_skill(self, temp_skill_dir: Path) -> None:
        """Test creating a Skill instance."""
        skill_path = temp_skill_dir / "test-skill" / "SKILL.md"
        frontmatter = {"name": "test-skill", "description": "Test description"}
        content = "Test content"

        skill = Skill(path=skill_path, frontmatter=frontmatter, content=content)

        assert skill.path == skill_path
        assert skill.frontmatter == frontmatter
        assert skill.content == content

    def test_name_property(self, temp_skill_dir: Path) -> None:
        """Test name property extracts from frontmatter."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"name": "my-skill", "description": "Desc"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        assert skill.name == "my-skill"

    def test_description_property(self, temp_skill_dir: Path) -> None:
        """Test description property extracts from frontmatter."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"name": "test", "description": "My description"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        assert skill.description == "My description"

    def test_base_directory_property(self, temp_skill_dir: Path) -> None:
        """Test base_directory returns parent directory of SKILL.md."""
        skill_path = temp_skill_dir / "my-skill" / "SKILL.md"
        frontmatter = {"name": "test", "description": "Desc"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        assert skill.base_directory == skill_path.parent
        assert skill.base_directory.name == "my-skill"

    def test_to_xml_basic(self, temp_skill_dir: Path) -> None:
        """Test to_xml() generates correct XML."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"name": "test-skill", "description": "Test description"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")
        xml = skill.to_xml()

        assert "<skill>" in xml
        assert "</skill>" in xml
        assert "<name>test-skill</name>" in xml
        assert "<description>Test description</description>" in xml

    def test_to_xml_escapes_special_characters(self, temp_skill_dir: Path) -> None:
        """Test to_xml() escapes special XML characters."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {
            "name": "test",
            "description": "Description with <tags> & \"quotes\" and 'apostrophes'",
        }

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")
        xml = skill.to_xml()

        # Check that special characters are escaped
        assert "&lt;tags&gt;" in xml
        assert "&amp;" in xml
        assert "&quot;" in xml
        # html.escape() produces &#x27; for apostrophes
        assert "&#x27;" in xml or "&apos;" in xml

    def test_to_xml_multiline_description(self, temp_skill_dir: Path) -> None:
        """Test to_xml() handles multiline descriptions."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"name": "test", "description": "Line 1\nLine 2\nLine 3"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")
        xml = skill.to_xml()

        assert "<description>Line 1\nLine 2\nLine 3</description>" in xml

    def test_get_full_content_basic(self, temp_skill_dir: Path) -> None:
        """Test get_full_content() returns base directory and content."""
        skill_dir = temp_skill_dir / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"
        frontmatter = {"name": "test", "description": "Desc"}
        content = "Skill instructions here"

        skill = Skill(path=skill_path, frontmatter=frontmatter, content=content)
        full_content = skill.get_full_content()

        assert "Base directory for this skill:" in full_content
        assert str(skill_dir) in full_content
        assert "Skill instructions here" in full_content

    def test_get_full_content_format(self, temp_skill_dir: Path) -> None:
        """Test get_full_content() has correct format."""
        skill_dir = temp_skill_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"
        frontmatter = {"name": "test", "description": "Desc"}
        content = "Content here"

        skill = Skill(path=skill_path, frontmatter=frontmatter, content=content)
        full_content = skill.get_full_content()

        lines = full_content.split("\n")
        assert lines[0].startswith("Base directory for this skill:")
        assert lines[1] == ""  # Empty line separator
        assert "Content here" in full_content

    def test_get_full_content_empty_content(self, temp_skill_dir: Path) -> None:
        """Test get_full_content() with empty content."""
        skill_dir = temp_skill_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"
        frontmatter = {"name": "test", "description": "Desc"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")
        full_content = skill.get_full_content()

        assert "Base directory for this skill:" in full_content
        # Empty content should still be included
        assert full_content.endswith("\n\n") or full_content.endswith("\n")

    def test_skill_with_extra_frontmatter_fields(self, temp_skill_dir: Path) -> None:
        """Test Skill allows extra frontmatter fields."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {
            "name": "test",
            "description": "Desc",
            "author": "Test Author",
            "version": "1.0.0",
            "tags": ["test", "example"],
        }

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        assert skill.frontmatter["author"] == "Test Author"
        assert skill.frontmatter["version"] == "1.0.0"
        assert "test" in skill.frontmatter["tags"]

    def test_missing_name_in_frontmatter(self, temp_skill_dir: Path) -> None:
        """Test accessing name when missing from frontmatter."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"description": "Desc"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        # Should return None or raise KeyError
        with pytest.raises(KeyError):
            _ = skill.name

    def test_missing_description_in_frontmatter(self, temp_skill_dir: Path) -> None:
        """Test accessing description when missing from frontmatter."""
        skill_path = temp_skill_dir / "SKILL.md"
        frontmatter = {"name": "test"}

        skill = Skill(path=skill_path, frontmatter=frontmatter, content="")

        # Should return None or raise KeyError
        with pytest.raises(KeyError):
            _ = skill.description
