"""Markdown parser with YAML frontmatter support."""

import re
from typing import Any

import yaml

from langchain_skills.exceptions import SkillLoadError


class MarkdownParser:
    """
    Parses markdown files with YAML frontmatter.

    Provides static method to parse SKILL.md files and extract
    YAML frontmatter and markdown content.

    Example:
        ```python
        frontmatter, content = MarkdownParser.parse(markdown_text)
        ```

        Input format:
        ```
        ---
        name: my-skill
        description: Does something useful
        ---

        # Skill Content
        ```
    """

    @staticmethod
    def parse(markdown_content: str) -> tuple[dict[str, Any], str]:
        """
        Parse markdown content and extract YAML frontmatter and body.

        Args:
            markdown_content: Raw markdown string with YAML frontmatter

        Returns:
            Tuple of (frontmatter dict, content string)

        Raises:
            SkillLoadError: If frontmatter is missing or invalid

        Example:
            >>> frontmatter, content = MarkdownParser.parse(skill_text)
            >>> print(frontmatter['name'])
            'my-skill'
        """
        if not markdown_content or not markdown_content.strip():
            raise SkillLoadError("No YAML frontmatter found in SKILL.md")

        # Check if document starts with frontmatter delimiter (---)
        if not markdown_content.startswith("---"):
            raise SkillLoadError("No YAML frontmatter found in SKILL.md")

        # Find the closing delimiter
        # Pattern: ---\n(yaml content)\n---\n(rest)
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, markdown_content, re.DOTALL)

        if not match:
            raise SkillLoadError("No YAML frontmatter found in SKILL.md")

        yaml_content = match.group(1)
        content = match.group(2).strip()

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(yaml_content)
            if frontmatter is None:
                frontmatter = {}
        except yaml.YAMLError as e:
            raise SkillLoadError(f"Failed to parse YAML frontmatter: {e}")

        return frontmatter, content
