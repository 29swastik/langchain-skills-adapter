"""Integration tests for end-to-end workflows."""

from pathlib import Path

import pytest

from langchain_skills import SkillTool


@pytest.mark.integration
class TestEndToEnd:
    """Test complete workflows from skill creation to execution."""

    def test_complete_workflow_single_skill(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test complete workflow: create skill, load it, invoke it."""
        # Step 1: Create skill
        skill_content = """---
name: example-skill
description: An example skill for testing
---

# Example Skill

This skill demonstrates the complete workflow.

## Instructions
1. Do something useful
2. Return results
"""
        skill_path = create_skill_file(skill_content, "example-skill")

        # Step 2: Load skill with SkillTool
        tool = SkillTool(directories=temp_skill_dir)

        # Step 3: Verify tool setup
        assert isinstance(tool, SkillTool)
        assert tool.name == "Skill"
        assert "example-skill" in tool.skills_map

        # Step 4: Verify tool description contains skill info
        assert "<skill>" in tool.description
        assert "<name>example-skill</name>" in tool.description
        assert "example skill for testing" in tool.description

        # Step 5: Invoke skill
        result = tool._run("example-skill")

        # Step 6: Verify result
        assert "Base directory for this skill:" in result
        assert str(skill_path.parent) in result
        assert "Example Skill" in result
        assert "Do something useful" in result

    def test_complete_workflow_multiple_skills(
        self, temp_skill_dir: Path, create_skill_file
    ) -> None:
        """Test workflow with multiple skills."""
        # Create multiple skills
        skills = [
            ("skill-one", "First skill", "Content for skill one"),
            ("skill-two", "Second skill", "Content for skill two"),
            ("skill-three", "Third skill", "Content for skill three"),
        ]

        for name, desc, content in skills:
            create_skill_file(f"---\nname: {name}\ndescription: {desc}\n---\n{content}", name)

        # Load all skills
        tool = SkillTool(directories=temp_skill_dir)

        # Verify all skills loaded
        assert len(tool.skills_map) == 3
        for name, _, _ in skills:
            assert name in tool.skills_map

        # Test invoking each skill
        for name, _, content in skills:
            result = tool._run(name)
            assert content in result

    def test_workflow_nested_directories(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test workflow with skills in nested directories."""
        # Create nested structure
        create_skill_file(
            "---\nname: top-level\ndescription: Top level\n---\nTop content", "top-level"
        )
        create_skill_file(
            "---\nname: nested\ndescription: Nested skill\n---\nNested content",
            "level1/level2/nested",
        )

        # Discover and load all skills
        tool = SkillTool(directories=temp_skill_dir)

        # Verify both found
        assert len(tool.skills_map) == 2
        assert "top-level" in tool.skills_map
        assert "nested" in tool.skills_map

        # Test both can be invoked
        result1 = tool._run("top-level")
        result2 = tool._run("nested")

        assert "Top content" in result1
        assert "Nested content" in result2

    def test_workflow_multiple_directories(self, temp_skill_dir: Path) -> None:
        """Test workflow loading from multiple separate directories."""
        # Create two separate skill directories
        dir1 = temp_skill_dir / "skills_dir1"
        dir1.mkdir(parents=True)
        (dir1 / "skill-a" / "SKILL.md").parent.mkdir(parents=True)
        (dir1 / "skill-a" / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: From dir1\n---\nContent A"
        )

        dir2 = temp_skill_dir / "skills_dir2"
        dir2.mkdir(parents=True)
        (dir2 / "skill-b" / "SKILL.md").parent.mkdir(parents=True)
        (dir2 / "skill-b" / "SKILL.md").write_text(
            "---\nname: skill-b\ndescription: From dir2\n---\nContent B"
        )

        # Load from both directories
        tool = SkillTool(directories=[dir1, dir2])

        # Verify both loaded
        assert len(tool.skills_map) == 2
        assert "skill-a" in tool.skills_map
        assert "skill-b" in tool.skills_map

        # Test both work
        assert "Content A" in tool._run("skill-a")
        assert "Content B" in tool._run("skill-b")

    def test_workflow_custom_template(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test workflow with custom description template."""
        create_skill_file("---\nname: test\ndescription: Test skill\n---\nContent", "test")

        custom_template = """My Custom Skill System

Available Skills:
{skills_xml}

Use these skills wisely!
"""

        tool = SkillTool(directories=temp_skill_dir, description_template=custom_template)

        # Verify custom template used
        assert "My Custom Skill System" in tool.description
        assert "Use these skills wisely!" in tool.description
        assert "<name>test</name>" in tool.description

    def test_workflow_error_handling(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test error handling in complete workflow."""
        create_skill_file("---\nname: only-skill\ndescription: Test\n---\nContent", "only-skill")

        tool = SkillTool(directories=temp_skill_dir)

        # Test invalid skill name
        result = tool._run("nonexistent")
        assert "Skill not found" in result
        assert "only-skill" in result

    def test_workflow_xml_generation(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test XML generation in workflow."""
        create_skill_file(
            "---\nname: xml-test\ndescription: Test XML with <special> & chars\n---\n", "xml-test"
        )

        tool = SkillTool(directories=temp_skill_dir)

        # Verify XML properly escaped
        assert "<name>xml-test</name>" in tool.description
        # Special chars should be escaped
        assert "&lt;special&gt;" in tool.description or "<special>" not in tool.description

    def test_workflow_skill_base_directory(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test that skill execution returns correct base directory."""
        skill_path = create_skill_file(
            "---\nname: basedir-test\ndescription: Test base dir\n---\nContent", "my-skill-dir"
        )

        tool = SkillTool(directories=temp_skill_dir)
        result = tool._run("basedir-test")

        # Verify base directory in result
        base_dir = skill_path.parent
        assert str(base_dir) in result
        assert "my-skill-dir" in result

    def test_workflow_with_fixture_skills(self) -> None:
        """Test workflow using real fixture files."""
        fixture_dir = Path(__file__).parent.parent / "fixtures" / "multiple_skills"

        if not fixture_dir.exists():
            pytest.skip("Fixture directory not found")

        tool = SkillTool(directories=fixture_dir)

        # Verify skills loaded
        assert len(tool.skills_map) > 0

        # Test invoking a known fixture skill
        if "skill-one" in tool.skills_map:
            result = tool._run("skill-one")
            assert "Base directory for this skill:" in result

    @pytest.mark.asyncio
    async def test_workflow_async_execution(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test async workflow."""
        create_skill_file(
            "---\nname: async-test\ndescription: Test async\n---\nAsync content", "async-test"
        )

        tool = SkillTool(directories=temp_skill_dir)

        # Test async invocation
        result = await tool._arun("async-test")

        assert "Async content" in result
        assert "Base directory for this skill:" in result

    def test_progressive_disclosure_concept(self, temp_skill_dir: Path, create_skill_file) -> None:
        """Test progressive disclosure: metadata first, then full content."""
        skill_content = """---
name: code-review
description: Reviews code for quality and best practices
---

# Code Review Skill

## Full Instructions
When activated, this skill provides detailed code review capabilities:

1. Analyze code structure
2. Check for best practices
3. Identify potential bugs
4. Suggest improvements

## Resources
You can access additional files in the base directory.
"""
        create_skill_file(skill_content, "code-review")

        tool = SkillTool(directories=temp_skill_dir)

        # Phase 1: Agent sees metadata in tool description
        assert "code-review" in tool.description
        assert "Reviews code for quality" in tool.description

        # Phase 2: Agent invokes skill and gets full content
        full_content = tool._run("code-review")
        assert "Full Instructions" in full_content
        assert "Analyze code structure" in full_content
        assert "Resources" in full_content

        # Verify base directory provided for resource access
        assert "Base directory for this skill:" in full_content
