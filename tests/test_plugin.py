import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "granola-engineer"


def test_marketplace_lists_granola_engineer():
    data = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text())
    assert data["name"] == "fastapi-starter-kit-plugins"
    plugins = {row["name"]: row for row in data["plugins"]}
    assert plugins["granola-engineer"]["source"] == "./plugins/granola-engineer"


def test_plugin_manifest_is_valid():
    data = json.loads((PLUGIN / ".cursor-plugin" / "plugin.json").read_text())
    assert data["name"] == "granola-engineer"
    assert data["license"] == "MIT"
    assert (PLUGIN / data["logo"]).is_file()


def test_mcp_points_at_granola():
    data = json.loads((PLUGIN / "mcp.json").read_text())
    assert data["mcpServers"]["granola"]["url"] == "https://mcp.granola.ai/mcp"


def test_required_plugin_files_exist():
    required = [
        PLUGIN / "agents" / "granola-engineer.md",
        PLUGIN / "commands" / "granola-engineer.md",
        PLUGIN / "skills" / "granola-engineer" / "SKILL.md",
        PLUGIN / "rules" / "check-meeting-context.mdc",
        PLUGIN / "README.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert missing == []


def test_agent_frontmatter_names_granola_engineer():
    text = (PLUGIN / "agents" / "granola-engineer.md").read_text()
    assert text.startswith("---\n")
    assert "name: granola-engineer" in text
    assert "query_granola_meetings" in text
    assert "SQLAlchemy" in text


def test_project_overlay_matches_plugin():
    pairs = [
        (PLUGIN / "mcp.json", ROOT / ".cursor" / "mcp.json"),
        (
            PLUGIN / "agents" / "granola-engineer.md",
            ROOT / ".cursor" / "agents" / "granola-engineer.md",
        ),
        (
            PLUGIN / "rules" / "check-meeting-context.mdc",
            ROOT / ".cursor" / "rules" / "check-meeting-context.mdc",
        ),
        (
            PLUGIN / "commands" / "granola-engineer.md",
            ROOT / ".cursor" / "commands" / "granola-engineer.md",
        ),
        (
            PLUGIN / "skills" / "granola-engineer" / "SKILL.md",
            ROOT / ".cursor" / "skills" / "granola-engineer" / "SKILL.md",
        ),
    ]
    for src, dest in pairs:
        assert dest.is_file(), f"missing overlay {dest}"
        assert src.read_text() == dest.read_text(), f"drift {src} vs {dest}"
