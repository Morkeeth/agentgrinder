"""Meme layer — receipt-backed labels only."""
from agentgrinder.meme import roast_shape, vibe, vibe_or_default


def test_main_character_vibe():
    run = {"turns_typed": 2, "tool_calls": 80}
    assert vibe(run) == ("MAIN CHARACTER", vibe(run)[1])


def test_zero_ship_roast():
    run = {"turns_typed": 50, "tool_calls": 100, "commits": 0}
    lines = roast_shape(run)
    assert any("0 commits" in ln for ln in lines)


def test_ordinary_fallback():
    run = {"turns_typed": 12, "tool_calls": 20, "commits": 1}
    label, _ = vibe_or_default(run)
    assert label in ("ORDINARY GRIND", "ACTUALLY SHIPPED", "SURGICAL")
