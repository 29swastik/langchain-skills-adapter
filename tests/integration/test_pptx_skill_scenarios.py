"""
Integration tests for real-world PPTX skill usage scenarios.

These tests validate:
1. Basic skill functionality with real skill content
2. Filesystem tool integration patterns
3. Bash tool integration patterns
4. Complete end-to-end workflows
"""

import re
from pathlib import Path

import pytest

from langchain_skills.core.loader import SkillLoader
from langchain_skills.tools import SkillTool


class TestPPTXSkillBasicFunctionality:
    """Test basic skill loading and invocation with real PPTX skill."""

    @pytest.fixture
    def pptx_skill_path(self) -> Path:
        """Get path to the PPTX skill."""
        # Navigate from tests/integration to examples/pptx
        return Path(__file__).parent.parent.parent / "examples" / "pptx" / "SKILL.md"

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get examples directory path."""
        return Path(__file__).parent.parent.parent / "examples"

    def test_pptx_skill_exists(self, pptx_skill_path: Path):
        """Verify PPTX skill file exists."""
        assert pptx_skill_path.exists(), f"PPTX skill not found at {pptx_skill_path}"
        assert pptx_skill_path.is_file()
        assert pptx_skill_path.suffix == ".md"

    def test_load_pptx_skill(self, pptx_skill_path: Path):
        """Test loading the PPTX skill."""
        skill = SkillLoader.load_skill(pptx_skill_path)

        assert skill.name == "pptx"
        assert "presentation" in skill.description.lower()
        assert str(skill.base_directory) == str(pptx_skill_path.parent)
        assert len(skill.content) > 1000  # PPTX skill is comprehensive

    def test_pptx_skill_content_structure(self, pptx_skill_path: Path):
        """Verify PPTX skill has expected content structure."""
        skill = SkillLoader.load_skill(pptx_skill_path)

        # Check for key sections
        assert "## Overview" in skill.content
        assert (
            "## Reading and analyzing content" in skill.content
            or "Reading and analyzing" in skill.content
        )
        assert "## Creating a new PowerPoint" in skill.content or "Creating" in skill.content

        # Check for code examples
        assert "```bash" in skill.content or "```python" in skill.content

        # Check for script references
        assert "html2pptx" in skill.content
        assert "scripts/" in skill.content

    def test_create_skill_tool_with_pptx(self, examples_dir: Path):
        """Test creating SkillTool with PPTX skill."""
        tool = SkillTool(directories=[examples_dir])

        assert "pptx" in tool.skills_map
        # Tool name is capitalized by default
        assert tool.name.lower() == "skill"
        assert len(tool.skills_map) >= 1

    def test_invoke_pptx_skill(self, examples_dir: Path):
        """Test invoking PPTX skill through tool."""
        tool = SkillTool(directories=[examples_dir])
        result = tool._run("pptx")

        # Verify base directory is included
        assert "Base directory for this skill:" in result
        assert "pptx" in result

        # Verify content is included
        assert "presentation" in result.lower()
        assert len(result) > 1000

    def test_pptx_skill_xml_generation(self, pptx_skill_path: Path):
        """Test XML generation for PPTX skill."""
        skill = SkillLoader.load_skill(pptx_skill_path)
        xml = skill.to_xml()

        assert xml.startswith("<skill>")
        assert xml.endswith("</skill>")
        assert "<name>pptx</name>" in xml
        assert "<description>" in xml and "</description>" in xml

        # Verify special characters are escaped
        # If original description has &, <, >, they should be escaped
        if any(char in skill.description for char in ["&", "<", ">"]):
            assert "&amp;" in xml or "&lt;" in xml or "&gt;" in xml

    @pytest.mark.asyncio
    async def test_async_invoke_pptx_skill(self, examples_dir: Path):
        """Test async invocation of PPTX skill."""
        tool = SkillTool(directories=[examples_dir])
        result = await tool._arun("pptx")

        assert "Base directory for this skill:" in result
        assert "presentation" in result.lower()


class TestFilesystemToolIntegration:
    """Test patterns for filesystem tool integration with PPTX skill."""

    @pytest.fixture
    def pptx_skill_dir(self) -> Path:
        """Get PPTX skill directory."""
        return Path(__file__).parent.parent.parent / "examples" / "pptx"

    @pytest.fixture
    def skill_tool(self, pptx_skill_dir: Path) -> SkillTool:
        """Create SkillTool with PPTX skill."""
        return SkillTool(directories=[pptx_skill_dir])

    def test_extract_base_directory(self, skill_tool: SkillTool):
        """Test extracting base directory from skill output."""
        result = skill_tool._run("pptx")

        # Parse base directory
        lines = result.split("\n")
        assert len(lines) > 0

        first_line = lines[0]
        assert "Base directory for this skill:" in first_line

        # Extract directory path
        base_dir = first_line.split(":", 1)[1].strip()
        assert Path(base_dir).exists()
        assert Path(base_dir).is_dir()

    def test_locate_helper_scripts(self, skill_tool: SkillTool, pptx_skill_dir: Path):
        """Test locating helper scripts in skill directory."""
        result = skill_tool._run("pptx")
        base_dir = result.split("\n")[0].split(":", 1)[1].strip()

        # Check for scripts directory
        scripts_dir = Path(base_dir) / "scripts"
        assert scripts_dir.exists(), f"Scripts directory not found at {scripts_dir}"

        # Check for expected scripts
        expected_scripts = [
            "html2pptx.js",
            "thumbnail.py",
            "inventory.py",
            "replace.py",
            "rearrange.py",
        ]

        for script_name in expected_scripts:
            script_path = scripts_dir / script_name
            assert script_path.exists(), f"Expected script not found: {script_name}"

    def test_locate_ooxml_tools(self, skill_tool: SkillTool):
        """Test locating OOXML tools in skill directory."""
        result = skill_tool._run("pptx")
        base_dir = result.split("\n")[0].split(":", 1)[1].strip()

        # Check for ooxml directory
        ooxml_dir = Path(base_dir) / "ooxml"
        assert ooxml_dir.exists(), f"OOXML directory not found at {ooxml_dir}"

        # Check for ooxml scripts
        ooxml_scripts_dir = ooxml_dir / "scripts"
        assert ooxml_scripts_dir.exists()

        expected_ooxml_scripts = ["unpack.py", "pack.py", "validate.py"]
        for script_name in expected_ooxml_scripts:
            script_path = ooxml_scripts_dir / script_name
            assert script_path.exists(), f"Expected OOXML script not found: {script_name}"

    def test_locate_documentation_files(self, skill_tool: SkillTool):
        """Test locating documentation files referenced in skill."""
        result = skill_tool._run("pptx")
        base_dir = result.split("\n")[0].split(":", 1)[1].strip()

        # Check for referenced markdown files
        html2pptx_doc = Path(base_dir) / "html2pptx.md"
        ooxml_doc = Path(base_dir) / "ooxml.md"

        assert html2pptx_doc.exists(), "html2pptx.md not found"
        assert ooxml_doc.exists(), "ooxml.md not found"

        # Verify they have content
        assert html2pptx_doc.stat().st_size > 100
        assert ooxml_doc.stat().st_size > 100

    def test_construct_script_paths(self, skill_tool: SkillTool):
        """Test constructing full paths to scripts for execution."""
        result = skill_tool._run("pptx")
        base_dir = Path(result.split("\n")[0].split(":", 1)[1].strip())

        # Construct paths as an LLM would
        html2pptx_path = base_dir / "scripts" / "html2pptx.js"
        thumbnail_path = base_dir / "scripts" / "thumbnail.py"
        unpack_path = base_dir / "ooxml" / "scripts" / "unpack.py"

        assert html2pptx_path.exists()
        assert thumbnail_path.exists()
        assert unpack_path.exists()

        # Verify they're executable/readable
        assert html2pptx_path.is_file()
        assert thumbnail_path.is_file()
        assert unpack_path.is_file()


class TestBashToolIntegration:
    """Test patterns for bash/terminal tool integration with PPTX skill."""

    @pytest.fixture
    def skill_tool(self) -> SkillTool:
        """Create SkillTool with PPTX skill."""
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        return SkillTool(directories=[examples_dir])

    def test_extract_bash_commands(self, skill_tool: SkillTool):
        """Test extracting bash commands from skill content."""
        result = skill_tool._run("pptx")

        # Look for bash code blocks
        bash_blocks = []
        lines = result.split("\n")
        in_bash = False
        current_block = []

        for line in lines:
            if "```bash" in line:
                in_bash = True
                current_block = []
            elif "```" in line and in_bash:
                in_bash = False
                if current_block:
                    bash_blocks.append("\n".join(current_block))
            elif in_bash:
                current_block.append(line)

        assert len(bash_blocks) > 0, "No bash code blocks found in skill"

    def test_extract_python_commands(self, skill_tool: SkillTool):
        """Test extracting Python command examples from skill."""
        result = skill_tool._run("pptx")

        # Find python commands
        python_commands = []
        for line in result.split("\n"):
            if "python" in line.lower() and (".py" in line or "-m" in line):
                # Look for actual command patterns
                if (
                    line.strip().startswith("python ")
                    or "python ooxml/" in line
                    or "python -m" in line
                ):
                    cmd = line.strip()
                    if cmd and not cmd.startswith("#"):
                        python_commands.append(cmd)

        assert len(python_commands) > 0, "No Python commands found in skill"

        # Verify common commands are present
        command_texts = " ".join(python_commands)
        assert (
            "markitdown" in command_texts
            or "unpack.py" in command_texts
            or "thumbnail.py" in command_texts
        )

    def test_construct_executable_commands(self, skill_tool: SkillTool):
        """Test constructing executable commands with actual paths."""
        result = skill_tool._run("pptx")
        base_dir = result.split("\n")[0].split(":", 1)[1].strip()

        # Construct actual commands
        actual_commands = {
            "unpack": f"python {base_dir}/ooxml/scripts/unpack.py presentation.pptx ./unpacked/",
            "thumbnail": f"python {base_dir}/scripts/thumbnail.py presentation.pptx",
            "markitdown": "python -m markitdown presentation.pptx > content.md",
        }

        # Verify paths in commands exist (where applicable)
        assert Path(base_dir, "ooxml/scripts/unpack.py").exists()
        assert Path(base_dir, "scripts/thumbnail.py").exists()

        # Verify command structure
        for cmd_name, cmd in actual_commands.items():
            assert "python" in cmd
            if cmd_name != "markitdown":
                assert base_dir in cmd

    def test_identify_command_placeholders(self, skill_tool: SkillTool):
        """Test identifying placeholders in commands that need to be replaced."""
        result = skill_tool._run("pptx")

        # Find commands with placeholders
        placeholders_found = []
        for line in result.split("\n"):
            # Look for common placeholder patterns
            if "<" in line and ">" in line and "python" in line:
                # Extract placeholders
                matches = re.findall(r"<([^>]+)>", line)
                placeholders_found.extend(matches)

        # Common placeholders in PPTX skill
        assert len(placeholders_found) > 0, "No command placeholders found"

        # Verify common placeholders exist
        placeholder_text = " ".join(placeholders_found)
        # Examples: <office_file>, <output_dir>, <file.pptx>, etc.
        assert any(keyword in placeholder_text for keyword in ["file", "dir", "path", "office"])


class TestCompleteWorkflowScenarios:
    """Test complete end-to-end workflow scenarios."""

    @pytest.fixture
    def skill_tool(self) -> SkillTool:
        """Create SkillTool with PPTX skill."""
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        return SkillTool(directories=[examples_dir])

    def test_workflow_create_presentation_without_template(self, skill_tool: SkillTool):
        """Test workflow for creating presentation without template."""
        result = skill_tool._run("pptx")

        # Verify workflow section exists
        assert (
            "Creating a new PowerPoint presentation **without a template**" in result
            or "Creating a new PowerPoint" in result
        )

        # Verify key steps are mentioned
        assert "html2pptx" in result
        assert "workflow" in result.lower() or "steps" in result.lower()

        # Verify required files are mentioned
        assert "html2pptx.md" in result
        assert "html2pptx.js" in result

    def test_workflow_edit_existing_presentation(self, skill_tool: SkillTool):
        """Test workflow for editing existing presentations."""
        result = skill_tool._run("pptx")

        # Verify editing workflow exists
        assert "Editing an existing PowerPoint" in result or "edit" in result.lower()

        # Verify OOXML workflow is mentioned
        assert "ooxml" in result.lower()
        assert "unpack" in result.lower()
        assert "pack" in result.lower() or "repack" in result.lower()

    def test_workflow_using_template(self, skill_tool: SkillTool):
        """Test workflow for creating presentation using template."""
        result = skill_tool._run("pptx")

        # Verify template workflow exists
        assert "template" in result.lower()

        # Verify template-related operations mentioned
        assert "thumbnail" in result.lower() or "inventory" in result.lower()

    def test_skill_references_helper_documentation(self, skill_tool: SkillTool):
        """Test that skill properly references helper documentation."""
        result = skill_tool._run("pptx")
        base_dir = result.split("\n")[0].split(":", 1)[1].strip()

        # Verify references to documentation files
        assert "html2pptx.md" in result
        assert "ooxml.md" in result

        # Verify those files actually exist
        assert Path(base_dir, "html2pptx.md").exists()
        assert Path(base_dir, "ooxml.md").exists()

    def test_skill_provides_file_structure_info(self, skill_tool: SkillTool):
        """Test that skill provides information about file structures."""
        result = skill_tool._run("pptx")

        # Look for file structure descriptions
        # PPTX files have specific XML structure
        assert "ppt/slides" in result or "ppt/" in result
        assert ".xml" in result

        # Verify it mentions key PPTX components
        assert "slide" in result.lower()

    def test_llm_can_extract_all_necessary_information(self, skill_tool: SkillTool):
        """Test that an LLM can extract all necessary information from skill."""
        result = skill_tool._run("pptx")

        # Essential information an LLM needs:
        # 1. Base directory for scripts
        assert "Base directory for this skill:" in result

        # 2. Available workflows
        assert "##" in result  # Section headers

        # 3. Command examples
        assert "python" in result

        # 4. File references
        assert ".py" in result or ".js" in result

        # 5. Documentation references
        assert ".md" in result

        # All information should be in one invocation
        assert len(result) > 2000  # Comprehensive content


class TestSkillQualityValidation:
    """Validate the quality and completeness of the PPTX skill."""

    @pytest.fixture
    def pptx_skill_path(self) -> Path:
        """Get path to the PPTX skill."""
        return Path(__file__).parent.parent.parent / "examples" / "pptx" / "SKILL.md"

    def test_skill_has_valid_frontmatter(self, pptx_skill_path: Path):
        """Verify skill has valid YAML frontmatter."""
        with open(pptx_skill_path) as f:
            content = f.read()

        assert content.startswith("---\n")
        assert "name:" in content[:500]
        assert "description:" in content[:500]

    def test_skill_description_is_informative(self, pptx_skill_path: Path):
        """Verify skill description is clear and informative."""
        skill = SkillLoader.load_skill(pptx_skill_path)

        # Description should be substantial
        assert len(skill.description) > 50
        assert len(skill.description) < 1000  # But not too long

        # Should mention key functionality
        desc_lower = skill.description.lower()
        assert "presentation" in desc_lower or "pptx" in desc_lower

    def test_skill_content_has_code_examples(self, pptx_skill_path: Path):
        """Verify skill includes code examples."""
        skill = SkillLoader.load_skill(pptx_skill_path)

        # Should have code blocks
        assert "```" in skill.content
        code_block_count = skill.content.count("```")
        assert code_block_count >= 4  # At least 2 code blocks (opening and closing)

    def test_skill_content_organization(self, pptx_skill_path: Path):
        """Verify skill content is well organized with sections."""
        skill = SkillLoader.load_skill(pptx_skill_path)

        # Should have multiple sections
        h2_headers = skill.content.count("## ")
        assert h2_headers >= 3, "Skill should have multiple main sections"

        # Should have subsections
        h3_headers = skill.content.count("### ")
        assert h3_headers >= 2, "Skill should have subsections"

    def test_skill_meets_library_standards(self, pptx_skill_path: Path):
        """Verify skill meets library quality standards."""
        # Load successfully (validates YAML and structure)
        skill = SkillLoader.load_skill(pptx_skill_path)

        # Name follows conventions
        assert skill.name.islower()
        assert "-" not in skill.name or skill.name.replace("-", "").replace("_", "").isalnum()

        # Has substantial content
        assert len(skill.content) > 1000

        # Base directory is correct
        assert Path(skill.base_directory).exists()
        assert Path(skill.base_directory).is_dir()
