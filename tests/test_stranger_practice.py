"""A stranger's path: read someone else's moment, keep its practice on YOUR OWN baseline.

These hold the seams that make the path honest. Each one goes red on its own change:
the reader's baseline must be the reader's grind, the author's counts must never be
rendered beside the reader's, and readability, not ownership, must be the gate.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MOMENTS = (ROOT / "site/moments.js").read_text()
PRACTICES = (ROOT / "site/practices.js").read_text()
MIGRATION = (ROOT / "supabase/migrations/2026-09-07-adopt.sql").read_text()
ORDER = (ROOT / "scripts/migration-order.txt").read_text().split()


def test_migration_is_registered_in_deploy_order_after_moments():
    assert ORDER.index("2026-09-07-adopt.sql") > ORDER.index("2026-09-06-moments.sql")


def test_a_reader_who_is_not_the_author_is_offered_the_practice_not_a_generic_link():
    assert "Want to try a change yourself?" not in MOMENTS
    assert "${!owner ? keepForm(m, stale)" in MOMENTS
    assert "Keep this practice</button>" in MOMENTS


def test_the_readers_baseline_is_their_own_measured_grind():
    assert '.eq("profile_id", me().id)' in MOMENTS
    assert '.not("measurement_revision", "is", null)' in MOMENTS
    assert "baseline_run: keep.elements.baseline.value" in MOMENTS
    # the source grind is never offered as the reader's baseline
    assert "value=\"${esc(run.id)}\"" not in MOMENTS


def test_keeping_a_practice_is_an_explicit_consented_act():
    assert 'name="consent" required> Keep this practice on my account.' in MOMENTS
    assert "Nothing is sent to the author" in MOMENTS


def test_an_older_source_measurement_is_labelled_not_a_dead_end_for_a_reader():
    """The author's stale gate protects the author's own baseline binding, not the reader's."""
    assert "keepForm(m, stale)" in MOMENTS
    assert "measured again since the moment was written" in MOMENTS


def test_the_kept_practice_shows_where_it_came_from():
    assert "KEPT FROM ANOTHER BUILDER" in PRACTICES
    assert "/?run=${encodeURIComponent(kept.source_run)}&moment=" in PRACTICES
    assert "no longer readable to you" in PRACTICES


def test_the_source_builders_counts_are_never_placed_beside_the_readers():
    assert "Their counts are not shown here." in PRACTICES
    assert "does not establish that this practice caused the difference" in PRACTICES
    query = PRACTICES[PRACTICES.index("grinder_adopted_moments"):]
    query = query[: query.index(".eq(")]
    for count in ("prompts", "turns_typed", "claims", "artifacts_produced", "rhythm"):
        assert count not in query


def test_readability_not_ownership_is_the_gate():
    body = MIGRATION[MIGRATION.index("function grinder_adopt_moment"):]
    assert "not grinder_can_read_run(m.run_id)" in body
    assert "m.owner_id" not in body


def test_the_kept_practice_points_at_the_readers_own_grind():
    assert "values(who,action_title" in MIGRATION
    assert "baseline_run,'private')" in MIGRATION
    assert "grinder_start_attempt(p,baseline_run,false)" in MIGRATION


def test_provenance_stores_references_only_and_stays_private_to_the_adopter():
    table = MIGRATION[MIGRATION.index("create table if not exists grinder_adopted_moments"):]
    table = table[: table.index(");")]
    table = "\n".join(l for l in table.splitlines() if not l.strip().startswith("--"))
    for copied in ("title", "excerpt", "claim", "limitation"):
        assert copied not in table
    assert "create policy adopted_read on grinder_adopted_moments for select using(adopter_id=grinder_profile_id())" in MIGRATION
    assert "revoke insert,update,delete on grinder_adopted_moments from anon,authenticated" in MIGRATION


@pytest.mark.parametrize("granted", ["grant select on grinder_adopted_moments to authenticated",
                                     "grant execute on function grinder_adopt_moment(uuid,uuid,text,text) to authenticated"])
def test_anonymous_readers_are_never_granted_the_keep_path(granted):
    assert granted in MIGRATION
    assert granted.replace("to authenticated", "to anon") not in MIGRATION
