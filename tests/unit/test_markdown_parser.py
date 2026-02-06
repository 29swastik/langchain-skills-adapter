"""Unit tests for MarkdownParser."""

from pathlib import Path

import pytest

from langchain_skills.exceptions import SkillLoadError
from langchain_skills.utils.markdown_parser import MarkdownParser


@pytest.mark.unit
class TestMarkdownParser:
    """Test MarkdownParser functionality."""

    def test_parse_valid_skill(self, valid_skill_content: str) -> None:
        """Test parsing valid SKILL.md content."""
        frontmatter, content = MarkdownParser.parse(valid_skill_content)

        assert isinstance(frontmatter, dict)
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill for unit testing"
        assert "This is the skill content" in content
        assert "instructions for the agent" in content

    def test_parse_minimal_skill(self, valid_skill_minimal: str) -> None:
        """Test parsing minimal valid SKILL.md."""
        frontmatter, content = MarkdownParser.parse(valid_skill_minimal)

        assert frontmatter["name"] == "minimal"
        assert frontmatter["description"] == "Minimal skill"
        assert content.strip() == ""

    def test_parse_multiline_description(self, multiline_description: str) -> None:
        """Test parsing SKILL.md with multiline description."""
        frontmatter, content = MarkdownParser.parse(multiline_description)

        assert frontmatter["name"] == "multiline"
        assert "multiline description" in frontmatter["description"]
        assert "multiple lines" in frontmatter["description"]

    def test_parse_extra_fields(self, skill_with_extra_fields: str) -> None:
        """Test parsing SKILL.md with extra frontmatter fields."""
        frontmatter, content = MarkdownParser.parse(skill_with_extra_fields)

        assert frontmatter["name"] == "extra-fields"
        assert frontmatter["author"] == "Test Author"
        assert frontmatter["version"] == "1.0.0"
        assert "test" in frontmatter["tags"]

    def test_parse_no_frontmatter(self, no_frontmatter_content: str) -> None:
        """Test parsing content without frontmatter raises error."""
        with pytest.raises(SkillLoadError, match="No YAML frontmatter found"):
            MarkdownParser.parse(no_frontmatter_content)

    def test_parse_incomplete_frontmatter(self, incomplete_frontmatter_content: str) -> None:
        """Test parsing incomplete frontmatter raises error."""
        with pytest.raises(SkillLoadError, match="No YAML frontmatter found"):
            MarkdownParser.parse(incomplete_frontmatter_content)

    def test_parse_invalid_yaml(self, invalid_yaml_content: str) -> None:
        """Test parsing invalid YAML raises error."""
        with pytest.raises(SkillLoadError, match="Failed to parse YAML frontmatter"):
            MarkdownParser.parse(invalid_yaml_content)

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content raises error."""
        with pytest.raises(SkillLoadError, match="No YAML frontmatter found"):
            MarkdownParser.parse("")

    def test_parse_only_delimiters(self) -> None:
        """Test parsing only delimiters without content."""
        content = "---\n---\n"
        with pytest.raises(SkillLoadError):
            MarkdownParser.parse(content)

    def test_parse_whitespace_handling(self) -> None:
        """Test parsing handles extra whitespace correctly."""
        content = """---
name: whitespace-test
description: Test whitespace handling
---

Content with leading/trailing whitespace.

"""
        frontmatter, parsed_content = MarkdownParser.parse(content)

        assert frontmatter["name"] == "whitespace-test"
        assert "Content with leading/trailing whitespace" in parsed_content

    def test_parse_complex_yaml(self) -> None:
        """Test parsing complex YAML structures."""
        content = """---
name: complex
description: Complex YAML test
nested:
  field: value
  list: [1, 2, 3]
tags:
  - test
  - example
---
Content
"""
        frontmatter, parsed_content = MarkdownParser.parse(content)

        assert frontmatter["name"] == "complex"
        assert frontmatter["nested"]["field"] == "value"
        assert frontmatter["nested"]["list"] == [1, 2, 3]
        assert "test" in frontmatter["tags"]

    def test_parse_special_characters_in_content(self) -> None:
        """Test parsing content with special characters."""
        content = """---
name: special-chars
description: Test special characters
---

Content with <xml>, "quotes", and 'apostrophes'.
Also & ampersands and #hashtags.
"""
        frontmatter, parsed_content = MarkdownParser.parse(content)

        assert "<xml>" in parsed_content
        assert '"quotes"' in parsed_content
        assert "&" in parsed_content

    def test_parse_from_file(self, temp_skill_dir: Path, valid_skill_content: str) -> None:
        """Test parsing from actual file."""
        skill_file = temp_skill_dir / "SKILL.md"
        skill_file.write_text(valid_skill_content)

        file_content = skill_file.read_text()
        frontmatter, content = MarkdownParser.parse(file_content)

        assert frontmatter["name"] == "test-skill"
        assert "instructions for the agent" in content
