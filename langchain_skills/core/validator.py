import re
from typing import Any

from langchain_skills.exceptions import SkillValidationError


class SkillValidator:
    """Validates skill structure and metadata."""

    RESERVED_WORDS = []

    # Field constraints from Anthropic docs
    MAX_NAME_LENGTH = float("inf")
    MAX_DESCRIPTION_LENGTH = float("inf")

    @staticmethod
    def validate_name(name: str) -> None:
        """
        Validate skill name.

        Rules:
        - Maximum MAX_NAME_LENGTH characters
        - Only lowercase letters, numbers, and hyphens
        - Cannot contain reserved words

        Args:
            name: Skill name to validate

        Raises:
            SkillValidationError: If validation fails
        """
        if not name or not name.strip():
            raise SkillValidationError("Skill name cannot be empty")

        if len(name) > SkillValidator.MAX_NAME_LENGTH:
            raise SkillValidationError(
                f"Skill name must be {SkillValidator.MAX_NAME_LENGTH} characters or less"
            )

        if not re.match(r"^[a-z0-9-]+$", name):
            raise SkillValidationError(
                "Skill name must contain only lowercase letters, numbers, and hyphens"
            )

        if any(word in name.lower() for word in SkillValidator.RESERVED_WORDS):
            raise SkillValidationError(
                f"Skill name cannot contain reserved words: {SkillValidator.RESERVED_WORDS}"
            )

    @staticmethod
    def validate_description(description: str) -> None:
        """
        Validate skill description.

        Rules:
        - Cannot be empty
        - Maximum MAX_DESCRIPTION_LENGTH characters

        Args:
            description: Skill description to validate

        Raises:
            SkillValidationError: If validation fails
        """
        if not description or not description.strip():
            raise SkillValidationError("Skill description cannot be empty")

        if len(description) > SkillValidator.MAX_DESCRIPTION_LENGTH:
            raise SkillValidationError(
                f"Skill description must be {SkillValidator.MAX_DESCRIPTION_LENGTH} characters or less"
            )

    @staticmethod
    def validate_frontmatter(frontmatter: dict[str, Any]) -> None:
        """
        Validate complete frontmatter.

        Checks for required fields and validates their values.

        Args:
            frontmatter: Frontmatter dictionary from YAML

        Raises:
            SkillValidationError: If validation fails
        """
        errors = []

        # Check required fields
        if "name" not in frontmatter:
            errors.append("Missing required field: name")
        elif not isinstance(frontmatter["name"], str):
            errors.append("Field 'name' must be a string")
        else:
            try:
                SkillValidator.validate_name(str(frontmatter["name"]))
            except SkillValidationError as e:
                errors.append(str(e))

        if "description" not in frontmatter:
            errors.append("Missing required field: description")
        elif not isinstance(frontmatter["description"], str):
            errors.append("Field 'description' must be a string")
        else:
            try:
                SkillValidator.validate_description(str(frontmatter["description"]))
            except SkillValidationError as e:
                errors.append(str(e))

        if errors:
            raise SkillValidationError("\\n".join(errors))
