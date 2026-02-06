"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_skill_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test skills."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_skill_content() -> str:
    """Return valid SKILL.md content."""
    return """---
name: test-skill
description: A test skill for unit testing
---

This is the skill content.
It provides instructions for the agent.
"""


@pytest.fixture
def valid_skill_minimal() -> str:
    """Return minimal valid SKILL.md content."""
    return """---
name: minimal
description: Minimal skill
---
"""


@pytest.fixture
def invalid_yaml_content() -> str:
    """Return SKILL.md with invalid YAML."""
    return """---
name: test-skill
description: Missing closing quotes
  bad: [yaml
---
Content here
"""


@pytest.fixture
def no_frontmatter_content() -> str:
    """Return SKILL.md without frontmatter."""
    return """Just some content without any frontmatter."""


@pytest.fixture
def incomplete_frontmatter_content() -> str:
    """Return SKILL.md with only opening delimiter."""
    return """---
name: incomplete
description: Missing closing delimiter
This should fail
"""


@pytest.fixture
def missing_name_content() -> str:
    """Return SKILL.md missing name field."""
    return """---
description: Has description but no name
---
Content here
"""


@pytest.fixture
def missing_description_content() -> str:
    """Return SKILL.md missing description field."""
    return """---
name: no-description
---
Content here
"""


@pytest.fixture
def invalid_name_uppercase() -> str:
    """Return SKILL.md with uppercase name."""
    return """---
name: InvalidName
description: Name has uppercase letters
---
Content
"""


@pytest.fixture
def invalid_name_underscore() -> str:
    """Return SKILL.md with underscore in name."""
    return """---
name: invalid_name
description: Name has underscore
---
Content
"""


@pytest.fixture
def invalid_name_too_long() -> str:
    """Return SKILL.md with name exceeding 64 chars."""
    long_name = "a" * 65
    return f"""---
name: {long_name}
description: Name is too long
---
Content
"""


@pytest.fixture
def invalid_description_too_long() -> str:
    """Return SKILL.md with description exceeding 1024 chars."""
    long_desc = "a" * 1025
    return f"""---
name: valid-name
description: {long_desc}
---
Content
"""


@pytest.fixture
def skill_with_extra_fields() -> str:
    """Return SKILL.md with extra frontmatter fields."""
    return """---
name: extra-fields
description: Has additional fields
author: Test Author
version: 1.0.0
tags: [test, example]
---
Content with extra metadata
"""


@pytest.fixture
def multiline_description() -> str:
    """Return SKILL.md with multiline description."""
    return """---
name: multiline
description: |
  This is a multiline description.
  It spans multiple lines.
  Should be properly parsed.
---
Content here
"""


@pytest.fixture
def create_skill_file(temp_skill_dir: Path):
    """Factory fixture to create SKILL.md files."""

    def _create_file(content: str, subdir: str = "") -> Path:
        """Create SKILL.md file with given content."""
        if subdir:
            skill_dir = temp_skill_dir / subdir
            skill_dir.mkdir(parents=True, exist_ok=True)
        else:
            skill_dir = temp_skill_dir

        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(content)
        return skill_path

    return _create_file
