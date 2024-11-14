from rich.console import Console
from ..novatool.ui.ai_components import (
    AIThinkingSpinner,
    AIEmotiveResponse,
    AIStatusIndicator,
    AIModelInfo,
    AICommandPalette,
    create_ai_tooltip,
    create_ai_timer_box
)
import pytest

@pytest.fixture
def console():
    return Console(force_terminal=True)

def test_ai_status_indicator():
    # Test different states
    for state in ["ready", "thinking", "busy", "error", "sleeping", "updating"]:
        panel = AIStatusIndicator.show(state)
        assert panel is not None
        assert state in str(panel).lower()

def test_ai_model_info():
    panel = AIModelInfo.display(
        model="gpt-4",
        provider="OpenAI",
        stats={"Temperature": 0.7, "Max Tokens": 1000}
    )
    assert panel is not None
    assert "gpt-4" in str(panel)
    assert "OpenAI" in str(panel)

def test_ai_command_palette():
    commands = {
        "help": "Show help menu",
        "status": "Check AI status",
        "clear": "Clear conversation"
    }
    panel = AICommandPalette.show_commands(commands)
    assert panel is not None
    assert "help" in str(panel)
    assert "status" in str(panel)

def test_ai_tooltip():
    panel = create_ai_tooltip(
        "Try asking more specific questions",
        "Add examples to get better responses"
    )
    assert panel is not None
    assert "💡" in str(panel)

def test_ai_timer_box():
    panel = create_ai_timer_box(
        "Model Loading",
        1.23,
        {"Cache": "Hit", "Size": "Large"}
    )
    assert panel is not None
    assert "1.23s" in str(panel)