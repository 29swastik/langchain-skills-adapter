"""LangChain tool for invoking skills."""

from pathlib import Path
from typing import Any

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from langchain_skills.core.loader import SkillLoader
from langchain_skills.core.skill import Skill

# Default tool description template
DEFAULT_TOOL_DESCRIPTION_TEMPLATE = """Execute a skill within the main conversation

<skills_instructions>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke skills using this tool with the skill name only (no arguments)
- When you invoke a skill, you will see <command-message>The "{{name}}" skill is loading</command-message>
- The skill's prompt will expand and provide detailed instructions on how to complete the task

NOTE: Response always starts with the base directory of the skill execution environment. You can use this to retrieve additional files or call shell commands.
Skill description follows after the base directory line.

Important:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already running
</skills_instructions>

<available_skills>
{skills_xml}
</available_skills>
"""


class SkillInput(BaseModel):
    """Input schema for Skill tool."""

    command: str = Field(description='The skill name (no arguments). E.g., "pdf" or "xlsx"')


class SkillTool(BaseTool):
    """
    LangChain tool that provides access to skills.

    This tool loads skills from specified directories and makes them available
    to agents. The agent invokes it with a skill name and receives the full skill content.

    **Skill Discovery:**
    SkillTool recursively searches for SKILL.md files within the provided directories.
    You can provide a parent directory, and it will discover all skills in subdirectories.

    **Supported Directory Structures:**

    Scenario 1 - Direct skill directory:
    ```
    skills/
    └── pdf/
        └── SKILL.md          # Skill name: "pdf"
    ```
    Usage: `SkillTool(directories="skills/pdf")`

    Scenario 2 - Parent directory with multiple skills:
    ```
    .copilot/skills/
    ├── pdf/
    │   └── SKILL.md          # Skill name: "pdf"
    ├── pptx/
    │   └── SKILL.md          # Skill name: "pptx"
    └── excel/
        └── SKILL.md          # Skill name: "excel"
    ```
    Usage: `SkillTool(directories=".copilot/skills")`  # Discovers all three skills

    Scenario 3 - Nested skill directories:
    ```
    skills/
    ├── documents/
    │   ├── pdf/
    │   │   └── SKILL.md      # Skill name: "pdf"
    │   └── word/
    │       └── SKILL.md      # Skill name: "word"
    └── data/
        └── csv/
            └── SKILL.md      # Skill name: "csv"
    ```
    Usage: `SkillTool(directories="skills")`  # Recursively discovers all nested skills

    Scenario 4 - Multiple parent directories:
    ```
    ~/.agents/skills/
    └── pdf/
        └── SKILL.md          # Skill name: "pdf"

    ./custom-skills/
    └── excel/
        └── SKILL.md          # Skill name: "excel"
    ```
    Usage: `SkillTool(directories=["~/.agents/skills", "./custom-skills"])`

    Examples:
        >>> # Simple case - single skill directory
        >>> skill_tool = SkillTool(directories=".copilot/skills/pdf")

        >>> # Parent directory - discovers all skills recursively
        >>> skill_tool = SkillTool(directories=".copilot/skills")

        >>> # Multiple parent directories
        >>> skill_tool = SkillTool(directories=["~/.agents/skills", "./custom-skills"])

        >>> # With custom description template
        >>> skill_tool = SkillTool(
        ...     directories=".agents/skills",
        ...     description_template="Custom: {skills_xml}"
        ... )
    """

    name: str = "Skill"
    description: str = ""
    args_schema: type[BaseModel] = SkillInput

    # Configuration fields
    directories: str | Path | list[str | Path] = Field(
        description="Directory or list of directories containing SKILL.md files"
    )
    description_template: str | None = Field(
        default=None,
        description="Optional custom template for tool description. Use {skills_xml} placeholder.",
    )

    # Internal state
    skills_map: dict[str, Skill] = Field(default_factory=dict, exclude=True)
    """Map of skill name -> Skill object"""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize SkillTool and load skills from directories."""
        super().__init__(**kwargs)

        self._load_skills()

        self._generate_description()

    def _load_skills(self) -> None:
        """Load all skills from configured directories."""
        # Normalize to list
        dirs = self.directories
        if isinstance(dirs, (str, Path)):
            dirs = [dirs]

        # Load all skills
        skills: list[Skill] = []
        for directory in dirs:
            path = Path(directory)
            discovered = SkillLoader.discover_skills(path)
            skills.extend(discovered)

        if not skills:
            raise ValueError(f"No skills found in directories: {dirs}")

        # Build skills map
        self.skills_map = {skill.name: skill for skill in skills}

        # Check for duplicates
        if len(self.skills_map) != len(skills):
            names = [s.name for s in skills]
            duplicates = set([n for n in names if names.count(n) > 1])
            raise ValueError(f"Duplicate skill names found: {duplicates}")

    def _generate_description(self) -> None:
        """Generate tool description from skills."""
        skills_xml = "\n".join(skill.to_xml() for skill in self.skills_map.values())
        template = self.description_template or DEFAULT_TOOL_DESCRIPTION_TEMPLATE
        self.description = template.format(skills_xml=skills_xml)

    def _run(self, command: str, run_manager: CallbackManagerForToolRun | None = None) -> str:
        """
        Execute skill tool - load and return skill content.

        Args:
            command: Skill name to load
            run_manager: Callback manager (optional)

        Returns:
            Skill content with base directory, or error message
        """
        skill: Skill = self.skills_map.get(command)

        if skill is not None:
            return skill.get_full_content()

        # Skill not found - provide helpful error
        available_skills = ", ".join(self.skills_map.keys())
        return f"Skill not found: {command}\nAvailable skills: {available_skills}"
