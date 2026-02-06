"""Unit tests for SkillValidator."""

import pytest

from langchain_skills.core.validator import SkillValidator
from langchain_skills.exceptions import SkillValidationError


@pytest.mark.unit
class TestSkillValidator:
    """Test SkillValidator functionality."""

    # Name Validation Tests

    def test_validate_name_valid(self) -> None:
        """Test valid skill names pass validation."""
        valid_names = [
            "code-reviewer",
            "pdf",
            "xlsx-parser",
            "a",
            "skill-with-many-hyphens",
            "123-numeric-start",
        ]

        for name in valid_names:
            SkillValidator.validate_name(name)  # Should not raise

    def test_validate_name_at_limit(self) -> None:
        """Test name with various lengths (no length limit)."""
        name = "a" * 64
        SkillValidator.validate_name(name)  # Should not raise

        # Also test longer names
        long_name = "a" * 100
        SkillValidator.validate_name(long_name)  # Should not raise

    def test_validate_name_empty(self) -> None:
        """Test empty name fails validation."""
        with pytest.raises(SkillValidationError, match="name cannot be empty"):
            SkillValidator.validate_name("")

    def test_validate_name_uppercase(self) -> None:
        """Test uppercase letters fail validation."""
        with pytest.raises(
            SkillValidationError, match="only lowercase letters, numbers, and hyphens"
        ):
            SkillValidator.validate_name("CodeReviewer")

    def test_validate_name_with_underscore(self) -> None:
        """Test underscores fail validation."""
        with pytest.raises(
            SkillValidationError, match="only lowercase letters, numbers, and hyphens"
        ):
            SkillValidator.validate_name("code_reviewer")

    def test_validate_name_with_spaces(self) -> None:
        """Test spaces fail validation."""
        with pytest.raises(
            SkillValidationError, match="only lowercase letters, numbers, and hyphens"
        ):
            SkillValidator.validate_name("code reviewer")

    def test_validate_name_with_special_chars(self) -> None:
        """Test special characters fail validation."""
        invalid_names = [
            "code@reviewer",
            "code.reviewer",
            "code!reviewer",
            "code$reviewer",
            "code#reviewer",
        ]

        for name in invalid_names:
            with pytest.raises(SkillValidationError):
                SkillValidator.validate_name(name)

    def test_validate_name_leading_hyphen(self) -> None:
        """Test leading hyphen is valid (allowed by regex)."""
        # If you want to disallow this, update the validator
        SkillValidator.validate_name("-leading-hyphen")

    def test_validate_name_trailing_hyphen(self) -> None:
        """Test trailing hyphen is valid (allowed by regex)."""
        SkillValidator.validate_name("trailing-hyphen-")

    # Description Validation Tests

    def test_validate_description_valid(self) -> None:
        """Test valid descriptions pass validation."""
        descriptions = [
            "A simple description",
            'Description with special chars: <>, &, "quotes"',
            "Multi\nline\ndescription",
            "A" * 1024,  # Long description
            "A" * 10000,  # Very long description (no limit)
        ]

        for desc in descriptions:
            SkillValidator.validate_description(desc)  # Should not raise

    def test_validate_description_empty(self) -> None:
        """Test empty description fails validation."""
        with pytest.raises(SkillValidationError, match="description cannot be empty"):
            SkillValidator.validate_description("")

    def test_validate_description_whitespace_only(self) -> None:
        """Test whitespace-only description fails validation."""
        with pytest.raises(SkillValidationError, match="description cannot be empty"):
            SkillValidator.validate_description("   \n\t  ")

    # Frontmatter Validation Tests

    def test_validate_frontmatter_valid(self) -> None:
        """Test valid frontmatter passes validation."""
        frontmatter = {"name": "test-skill", "description": "A test skill"}

        SkillValidator.validate_frontmatter(frontmatter)  # Should not raise

    def test_validate_frontmatter_with_extra_fields(self) -> None:
        """Test frontmatter with extra fields is allowed."""
        frontmatter = {
            "name": "test-skill",
            "description": "A test skill",
            "author": "Test Author",
            "version": "1.0.0",
        }

        SkillValidator.validate_frontmatter(frontmatter)  # Should not raise

    def test_validate_frontmatter_missing_name(self) -> None:
        """Test frontmatter missing name fails."""
        frontmatter = {"description": "A test skill"}

        with pytest.raises(SkillValidationError, match="Missing required field: name"):
            SkillValidator.validate_frontmatter(frontmatter)

    def test_validate_frontmatter_missing_description(self) -> None:
        """Test frontmatter missing description fails."""
        frontmatter = {"name": "test-skill"}

        with pytest.raises(SkillValidationError, match="Missing required field: description"):
            SkillValidator.validate_frontmatter(frontmatter)

    def test_validate_frontmatter_missing_both(self) -> None:
        """Test frontmatter missing both fields fails."""
        frontmatter: dict = {}

        with pytest.raises(SkillValidationError, match="Missing required field"):
            SkillValidator.validate_frontmatter(frontmatter)

    def test_validate_frontmatter_invalid_name(self) -> None:
        """Test frontmatter with invalid name format fails."""
        frontmatter = {"name": "Invalid_Name", "description": "A test skill"}

        with pytest.raises(SkillValidationError):
            SkillValidator.validate_frontmatter(frontmatter)

    def test_validate_frontmatter_name_not_string(self) -> None:
        """Test frontmatter with non-string name."""
        frontmatter = {"name": 123, "description": "A test skill"}

        with pytest.raises(SkillValidationError):
            SkillValidator.validate_frontmatter(frontmatter)

    def test_validate_frontmatter_description_not_string(self) -> None:
        """Test frontmatter with non-string description."""
        frontmatter = {"name": "test-skill", "description": ["not", "a", "string"]}

        with pytest.raises(SkillValidationError):
            SkillValidator.validate_frontmatter(frontmatter)
