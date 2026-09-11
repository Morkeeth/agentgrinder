"""Primary navigation simplification: three destinations, not a ten-item bar."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text()


def test_primary_nav_has_three_destinations_not_ten():
    assert 'data-section="feed"' in INDEX
    assert 'data-section="mine"' in INDEX
    assert 'data-section="community"' in INDEX
    assert 'data-section="inbox"' in INDEX
    primary = INDEX.split('id="nav"', 1)[1].split("</nav>", 1)[0]
    before_account = primary.split("<details", 1)[0]
    # Inbox embeds a badge <span>; strip tags for label compare
    top = [
        re.sub(r"<[^>]+>", "", m).strip()
        for m in re.findall(r"<a\s[^>]*>(.*?)</a>", before_account, flags=re.S)
    ]
    assert top == ["Feed", "My runs", "Community", "Inbox"]
    for label in ("Following", "Forum", "Crews", "Challenges"):
        assert f">{label}</a>" not in before_account
    assert "Account" in primary
    assert "/?community" in INDEX


def test_mobile_nav_is_four_or_fewer_destinations():
    mobile = INDEX.split('id="mobile-product-nav"', 1)[1].split("</nav>", 1)[0]
    assert mobile.count("<a ") <= 4
    assert "Progress" not in mobile and "Practices" not in mobile
    assert "Challenges" not in mobile


def test_deep_links_still_present():
    for path in ("/?following", "/?forum", "/?crews", "/?challenges", "/?agents", "/?rigs", "/?practices", "/?progress"):
        assert path in INDEX


def test_account_menu_keyboard_dismiss_wired():
    assert "Escape" in INDEX
    assert "account-menu" in INDEX
