from pathlib import Path

from langchain_skills.core.skill import Skill
from langchain_skills.core.validator import SkillValidator
from langchain_skills.exceptions import SkillLoadError, SkillNotFoundError, SkillValidationError
from langchain_skills.utils.markdown_parser import MarkdownParser


class SkillLoader:
    @staticmethod
    def load_skill(skill_md_path: Path) -> Skill:
        """
        Load and parse a single SKILL.md file.

        Process:
        1. Read file content (UTF-8)
        2. Parse with MarkdownParser
        3. Validate required fields
        4. Return Skill object

        Args:
            skill_md_path: Path to SKILL.md file

        Returns:
            Parsed and validated Skill object

        Raises:
            SkillNotFoundError: If SKILL.md doesn't exist
            SkillValidationError: If validation fails
            SkillLoadError: If loading fails for other reasons
        """
        if not skill_md_path.exists():
            raise SkillNotFoundError(f"Skill file not found: {skill_md_path}")

        try:
            # Read and parse
            markdown = skill_md_path.read_text(encoding="utf-8")
            frontmatter, content = MarkdownParser.parse(markdown)

            # Validate frontmatter
            try:
                SkillValidator.validate_frontmatter(frontmatter)
            except SkillValidationError as e:
                # Add file path context to validation errors
                raise SkillValidationError(f"Validation failed for {skill_md_path}:\n  - {e}")

            # Create Skill object
            return Skill(path=skill_md_path, frontmatter=frontmatter, content=content)

        except (SkillNotFoundError, SkillValidationError, SkillLoadError):
            raise
        except Exception as e:
            raise SkillLoadError(f"Failed to load skill from {skill_md_path}: {e}") from e

    @staticmethod
    def discover_skills(root_directory: Path) -> list[Skill]:
        """
        Recursively find and load all SKILL.md files in a directory.

        Searches recursively for SKILL.md files and attempts to load each one.
        Stops on first error to fail fast.

        Args:
            root_directory: Root directory to search

        Returns:
            List of loaded Skill objects

        Raises:
            FileNotFoundError: If root directory doesn't exist
            NotADirectoryError: If path is not a directory
            SkillLoadError: If any skill fails to load
        """
        if not root_directory.exists():
            raise FileNotFoundError(f"Root directory does not exist: {root_directory}")

        if not root_directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {root_directory}")

        skills = []

        # Recursively find all SKILL.md files
        for skill_path in root_directory.rglob("SKILL.md"):
            if skill_path.is_file():
                try:
                    skill = SkillLoader.load_skill(skill_path)
                    skills.append(skill)
                except Exception as e:
                    raise SkillLoadError(f"Failed to load SKILL.md at {skill_path}: {e}") from e

        return skills
