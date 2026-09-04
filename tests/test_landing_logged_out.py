"""The logged-out landing page. What a judge with no account sees on the first click.

The defect this file pins: on 3 Sep 2026 the landing was a hero line, a paragraph and three
buttons. The product's whole argument, that an agent referees every claim before the card shows
a number, was invisible until GitHub sign-in. These are contract tests over site/index.html:
they check the landing renders a real public run and the words that explain the coach, not the
styling.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(REPO, "site", "index.html"), encoding="utf-8").read()

FEATURED_RUN = "28d5d0b7-eda2-4d94-a83c-580d2e3b75b2"


def test_landing_names_one_canonical_public_run_and_reads_it_anonymously():
    assert f'const FEATURED_RUN="{FEATURED_RUN}"' in HTML
    # the read is the same publishable key the rest of the page uses, and it is a plain select
    assert "async function fetchFeatured()" in HTML
    assert ".eq('id',FEATURED_RUN)" in HTML


def test_landing_draws_the_run_before_the_sign_in_call():
    assert "async function viewLanding()" in HTML
    assert "function landingHTML(r)" in HTML
    body = HTML[HTML.index("function landingHTML(r)"):]
    body = body[:body.index("\nasync function viewLanding()")]
    # the card is above the buttons, and the buttons are above how-it-works
    assert body.index("featuredCard(r)") < body.index("Get started")
    assert body.index("Get started") < body.index("howItWorks()")


def test_the_card_carries_the_verdict_its_numbers_and_the_tool_call_count():
    card = HTML[HTML.index("function featuredCard(r)"):]
    card = card[:card.index("\n// The five tools")]
    assert "vptHtml(r)" in card and "fiveRow(r)" in card       # the numbers
    assert "r.coach_verdict" in card                            # the verdict paragraph
    assert "verdict produced by <b>${esc(String(n))}</b> tool call" in card
    assert "write_verdict" in card and "refuses" in card        # the refusal line, in words


def test_a_snapshot_paints_before_the_fetch_and_matches_the_row_that_was_published():
    snap = HTML[HTML.index("const FEATURED_SNAPSHOT="):]
    snap = snap[:snap.index("async function fetchFeatured()")]
    for field in ("claims:7", "claims_verified:3", "artifacts_produced:8", "coach_tool_calls:37",
                  "prompts:3", "commits:6", "tool_calls:150"):
        assert field in snap, field
    assert "3 of 7 claims had evidence in their own turn." in snap
    # no private repo name, no absolute path, no prompt text rode along with it
    assert "/Users/" not in snap and "repo G" not in snap and "fleet-ops" not in snap


def test_how_it_works_names_the_five_tools_and_the_three_modes_logged_out():
    block = HTML[HTML.index("function howItWorks()"):]
    block = block[:block.index("function landingHTML(r)")]
    for tool in ("read_run", "check_claim", "verify_artifact", "git_evidence", "write_verdict"):
        assert f"['{tool}'," in block, tool
    for mode in ("local", "bedrock", "none"):
        assert f"['{mode}'," in block, mode
    assert "DEGRADED" in block
    assert "Keyless, no network, no spend" in block
    assert "Needs AWS credentials, costs money" in block
    # text only: no icon font, no emoji, no svg inside the strip
    assert "<svg" not in block
    assert not re.search(r"[\U0001F300-\U0001FAFF←-➿]", block)


def test_the_landing_promises_nothing_that_needs_an_account():
    body = HTML[HTML.index("function landingHTML(r)"):]
    body = body[:body.index("\nasync function viewLanding()")]
    assert "No account needed" in body
    # every link out of the landing is a page that renders without a session
    for href in re.findall(r"location\.href='([^']+)'", body):
        assert href in ("/?onboard", "/?explore"), href


def test_the_clone_command_is_a_real_public_url_not_a_placeholder():
    assert "git clone https://github.com/Morkeeth/agentgrinder" in HTML
    assert "git clone &lt;repo&gt;" not in HTML
