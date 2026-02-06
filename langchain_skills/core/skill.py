"""Skill data model."""

import html
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """
    Represents a skill loaded from SKILL.md.

    A skill contains metadata (from YAML frontmatter), instructions (markdown content),
    and a reference to its filesystem location.
    """

    path: Path
    """Path to the SKILL.md file"""

    frontmatter: dict[str, Any]
    """Complete YAML frontmatter as dictionary (typically contains 'name' and 'description')"""

    content: str
    """Markdown body content (without frontmatter)"""

    @property
    def name(self) -> str:
        """Get skill name from frontmatter."""
        return self.frontmatter["name"]

    @property
    def description(self) -> str:
        """Get skill description from frontmatter."""
        return self.frontmatter["description"]

    @property
    def base_directory(self) -> Path:
        """Get parent directory of SKILL.md (skill's base directory)."""
        return self.path.parent

    def to_xml(self) -> str:
        """
        Convert frontmatter to XML format for tool description.

        Generates XML representation of ALL frontmatter fields,
        not just name and description.

        Returns:
            XML string with skill metadata

        Example:
            ```xml
            <skill>
              <name>pdf-processor</name>
              <description>Process PDF files</description>
            </skill>
            ```
        """
        # Generate XML for all frontmatter entries with HTML escaping
        frontmatter_xml = "\n".join(
            f"  <{key}>{html.escape(str(value))}</{key}>" for key, value in self.frontmatter.items()
        )
        return f"<skill>\n{frontmatter_xml}\n</skill>"

    def get_full_content(self) -> str:
        """
        Get complete skill response with base directory and content.

        This is what gets returned when the Skill tool is invoked.

        Returns:
            String with base directory line followed by skill content
        """
        return f"Base directory for this skill: {self.base_directory}\n\n{self.content}"
