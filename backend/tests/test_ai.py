import pytest
from unittest.mock import patch
from app.services.ai_service import AIService


def test_filename_to_title_fallback():
    ai = AIService()
    title = ai._clean_filename_to_title("my_epic_gameplay_episode_01.mp4")
    assert title == "My Epic Gameplay Episode 01"

    title2 = ai._clean_filename_to_title("vlog-2026-summer-trip.MOV")
    assert title2 == "Vlog 2026 Summer Trip"


def test_generate_title_with_mocked_ollama():
    ai = AIService()
    with patch.object(ai, "_call_ollama", return_value="Amazing Speedrun Highlights"):
        title = ai.generate_title("speedrun_clip.mp4")
        assert title == "Amazing Speedrun Highlights"


def test_generate_title_fallback_on_ollama_failure():
    ai = AIService()
    with patch.object(ai, "_call_ollama", return_value=None):
        title = ai.generate_title("speedrun_clip.mp4")
        assert title == "Speedrun Clip"


def test_generate_tags_json_parsing():
    ai = AIService()
    valid_json = '{"tags": ["gaming", "fps", "highlights", "competitive"]}'
    with patch.object(ai, "_call_ollama", return_value=valid_json):
        tags = ai.generate_tags("Title", "Description", "game.mp4")
        assert tags == ["gaming", "fps", "highlights", "competitive"]


def test_generate_tags_fallback_on_invalid_json():
    ai = AIService()
    invalid_json = "Here are some tags: gaming, highlights"
    with patch.object(ai, "_call_ollama", return_value=invalid_json):
        tags = ai.generate_tags("Title", "Description", "game.mp4")
        assert tags == []
