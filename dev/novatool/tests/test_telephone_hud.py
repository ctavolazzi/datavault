import pytest
from rich.console import Console
from rich.text import Text
import json
import os
import time
from telephone_hud import TelephoneGameMonitor

class TestTelephoneHUD:
    @pytest.fixture
    def hud(self):
        """Create a test HUD instance"""
        # Use test config path
        log_path = "test_telephone_game.log"
        return TelephoneGameMonitor(log_path)

    @pytest.fixture
    def test_log(self):
        """Create a temporary test log file"""
        log_path = "test_telephone_game.log"
        with open(log_path, "w") as f:
            f.write("")
        yield log_path
        # Cleanup
        if os.path.exists(log_path):
            os.remove(log_path)

    def test_config_loading(self, hud):
        """Test that config loads properly"""
        assert hud.config is not None
        assert "states" in hud.config
        assert "test_mode" in hud.config

    def test_styled_text(self, hud):
        """Test styled text generation"""
        text = hud.get_styled_text("test_mode")
        assert isinstance(text, Text)
        assert "TEST MODE" in text.plain

    def test_state_changes(self, hud, test_log):
        """Test HUD updates with different game states"""
        # Test startup
        startup_entry = {
            "event": "startup",
            "type": "game_start",
            "timestamp": time.time(),
            "message": "Game Starting!"
        }
        with open(test_log, "w") as f:
            f.write(json.dumps(startup_entry) + "\n")

        # Simulate file change
        hud.on_modified(type('Event', (), {'src_path': test_log})())

        assert "Game Starting!" in [msg.plain for msg in hud.messages]

    def test_processing_state(self, hud, test_log):
        """Test processing state with spinner"""
        query_entry = {
            "query": "What is AI?",
            "timestamp": time.time()
        }
        with open(test_log, "w") as f:
            f.write(json.dumps(query_entry) + "\n")

        hud.on_modified(type('Event', (), {'src_path': test_log})())
        assert hud.stats["is_thinking"] == True

    def test_response_handling(self, hud, test_log):
        """Test response handling"""
        response_entry = {
            "round": 1,
            "message": "AI is machine intelligence",
            "processing_time": 0.5,
            "word_count": 4,
            "timestamp": time.time()
        }
        with open(test_log, "w") as f:
            f.write(json.dumps(response_entry) + "\n")

        hud.on_modified(type('Event', (), {'src_path': test_log})())
        assert "AI is machine intelligence" in [msg.plain for msg in hud.messages]