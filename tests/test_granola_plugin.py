"""Validate the vendored granola-engineer Cursor plugin layout."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / ".cursor" / "plugins" / "granola"
WORKSPACE_MCP = ROOT / ".cursor" / "mcp.json"

REQUIRED_MCP_TOOLS = (
    "query_granola_meetings",
    "list_meetings",
    "list_meeting_folders",
    "get_meetings",
    "get_meeting_transcript",
)

SKILLS = ("granola-context", "granola-prep", "granola-review")
COMMANDS = (
    "granola-brief",
    "granola-bug-report",
    "granola-gaps",
    "granola-plan",
    "granola-pr",
    "granola-spec",
)


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise AssertionError("unclosed YAML frontmatter")
    block = text[4:end]
    meta: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise AssertionError(f"invalid frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def _plugin_json() -> dict:
    return json.loads((PLUGIN_ROOT / ".cursor-plugin" / "plugin.json").read_text())


def test_plugin_manifest_is_valid():
    manifest = _plugin_json()
    assert manifest["name"] == "granola"
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", manifest["name"])
    assert manifest["version"] == "1.0.0"
    assert "granola-engineer" in manifest["description"]
    assert manifest["author"]["name"] == "Granola"
    assert manifest["mcpServers"] == "./mcp.json"
    assert manifest["license"] == "MIT"
    for field in ("homepage", "repository"):
        value = manifest[field]
        assert value.startswith("https://")
        assert ".." not in value
    for path_value in manifest.values():
        if isinstance(path_value, str):
            assert not path_value.startswith("/")
            assert ".." not in Path(path_value).parts


def test_mcp_points_at_granola_http():
    plugin_mcp = json.loads((PLUGIN_ROOT / "mcp.json").read_text())
    workspace_mcp = json.loads(WORKSPACE_MCP.read_text())
    server = plugin_mcp["mcpServers"]["granola"]
    assert server["type"] == "http"
    assert server["url"] == "https://mcp.granola.ai/mcp"
    assert workspace_mcp == plugin_mcp


@pytest.mark.parametrize("skill", SKILLS)
def test_skills_exist_with_frontmatter(skill: str):
    path = PLUGIN_ROOT / "skills" / skill / "SKILL.md"
    meta = _parse_frontmatter(path.read_text())
    assert meta["name"] == skill
    assert meta["description"]
    body = path.read_text()
    assert "query_granola_meetings" in body


def test_granola_engineer_agent():
    path = PLUGIN_ROOT / "agents" / "granola-engineer.md"
    meta = _parse_frontmatter(path.read_text())
    assert meta["name"] == "granola-engineer"
    assert "meeting" in meta["description"].lower()
    body = path.read_text()
    for tool in REQUIRED_MCP_TOOLS:
        assert tool in body
    assert "contradict" in body.lower()


@pytest.mark.parametrize("command", COMMANDS)
def test_commands_exist_with_frontmatter(command: str):
    path = PLUGIN_ROOT / "commands" / f"{command}.md"
    meta = _parse_frontmatter(path.read_text())
    assert meta["name"] == command
    assert meta["description"]
    assert "query_granola_meetings" in path.read_text()


def test_meeting_context_rule_is_always_on():
    path = PLUGIN_ROOT / "rules" / "check-meeting-context.mdc"
    meta = _parse_frontmatter(path.read_text())
    assert meta["alwaysApply"] == "true"
    assert meta["description"]
    body = path.read_text()
    assert "Granola" in body
    assert "list_meetings" in body


def test_plugin_docs_and_license_exist():
    for name in ("README.md", "CHANGELOG.md", "LICENSE", "SOURCE.md"):
        path = PLUGIN_ROOT / name
        assert path.is_file(), name
        assert path.stat().st_size > 0
    readme = (PLUGIN_ROOT / "README.md").read_text()
    assert "/granola-engineer" in readme
    assert "https://mcp.granola.ai/mcp" in readme


def test_plugin_files_do_not_embed_secrets():
    secret_pattern = re.compile(
        r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]+['\"]",
        re.IGNORECASE,
    )
    for path in PLUGIN_ROOT.rglob("*"):
        if not path.is_file() or path.suffix in {".png", ".jpg"}:
            continue
        text = path.read_text(errors="ignore")
        assert secret_pattern.search(text) is None, path
