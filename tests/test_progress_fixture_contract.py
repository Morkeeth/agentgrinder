"""Keep the controlled return-flow fixture executable when a browser is unavailable."""

import ast
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "scripts/check-progress-fixtures.py"


def test_return_fixture_compiles_and_uses_python_ids():
    source = FIXTURE.read_text()
    ast.parse(source)
    assert "==OUTCOME_ID" in source
    assert "f'#review-{ATTEMPT_ID}'" in source
    assert "==outcome" not in source
    assert "'+attemptId" not in source


def test_return_fixture_saves_reopens_and_leaves_no_pending_action():
    source = FIXTURE.read_text()
    save = source.index("name='Save review'")
    reopened = source.index("page.evaluate('practices.detail(practiceId)')", save)
    history = source.index("page.evaluate('progress.history()')", reopened)
    no_pending = source.index("name='Run the named check',exact=True).count()==0", history)
    assert save < reopened < history < no_pending
    assert "get_by_text('This return is recorded',exact=True)" in source[save:history]


def test_return_fixture_captures_each_viewport_at_its_claimed_size():
    source = FIXTURE.read_text()
    phone_size = source.index("{'width':390,'height':844}", source.index("screenshots=Path"))
    phone_shot = source.index("return-review-phone.png", phone_size)
    desktop_size = source.index("{'width':1280,'height':900}", phone_shot)
    desktop_shot = source.index("return-review-desktop.png", desktop_size)
    assert phone_size < phone_shot < desktop_size < desktop_shot
