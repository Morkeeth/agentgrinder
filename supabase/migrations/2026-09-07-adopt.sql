-- A stranger keeps a readable moment's next practice on their OWN baseline.
-- Nothing is written to the author's grind and no counts cross between accounts.
begin;
create table if not exists grinder_adopted_moments (
 practice_id uuid primary key references grinder_practice_versions(id) on delete cascade,
 adopter_id uuid not null references profiles(id) on delete cascade,
 attempt_id uuid not null references grinder_practice_attempts(id) on delete cascade,
 -- provenance references only. Titles and excerpts are NOT copied here: if the author later
 -- narrows the audience, the adopter's own practice survives and the source stops resolving.
 moment_id uuid references grinder_run_moments(id) on delete set null,
 source_run uuid references runs(id) on delete set null,
 source_measurement_revision text not null check(source_measurement_revision ~ '^[a-f0-9]{64}$'),
 source_measurement_stale boolean not null,
 created_at timestamptz not null default now(),
 unique(adopter_id,moment_id)
);
alter table grinder_adopted_moments enable row level security;
drop policy if exists adopted_read on grinder_adopted_moments;
create policy adopted_read on grinder_adopted_moments for select using(adopter_id=grinder_profile_id());
grant select on grinder_adopted_moments to authenticated;
revoke insert,update,delete on grinder_adopted_moments from anon,authenticated;

-- Readability, not ownership, is the gate: this is the path for someone who was not there.
-- A stale source measurement is recorded, not refused: the technique is still readable, the
-- author's counts have merely moved on. The adopter's baseline is their own measured grind,
-- enforced by grinder_run_snapshot inside grinder_start_attempt.
create or replace function grinder_adopt_moment(moment uuid,baseline_run uuid,action_title text,expected_change text) returns jsonb
language plpgsql security definer set search_path=public as $$
declare m grinder_run_moments; source runs; p uuid; a uuid; saved grinder_adopted_moments; who uuid;
begin
 who=grinder_profile_id();
 if who is null then raise exception 'Sign in to keep a practice of your own'; end if;
 select * into m from grinder_run_moments where id=moment for update;
 if not found or not grinder_can_read_run(m.run_id) then raise exception 'This moment is private or unavailable'; end if;
 select * into saved from grinder_adopted_moments where adopter_id=who and moment_id=m.id;
 if found then
  if not exists(select 1 from grinder_practice_versions where id=saved.practice_id and title=action_title and expected=expected_change and source_run=baseline_run) then raise exception 'You already kept a different practice from this moment'; end if;
  return jsonb_build_object('practice_id',saved.practice_id,'attempt_id',saved.attempt_id);
 end if;
 select * into source from runs where id=m.run_id;
 -- the practice's own source grind is the ADOPTER's baseline. The author's run is provenance only.
 insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,harness,source_run,visibility)
 values(who,action_title,'Kept from another builder''s grind moment. The source grind stays with its author.',
        action_title,expected_change,coalesce(source.harness,''),baseline_run,'private') returning id into p;
 a=grinder_start_attempt(p,baseline_run,false);
 insert into grinder_adopted_moments(practice_id,adopter_id,attempt_id,moment_id,source_run,source_measurement_revision,source_measurement_stale)
 values(p,who,a,m.id,m.run_id,m.measurement_revision,source.measurement_revision is distinct from m.measurement_revision);
 return jsonb_build_object('practice_id',p,'attempt_id',a);
end $$;
revoke all on function grinder_adopt_moment(uuid,uuid,text,text) from public,anon;
grant execute on function grinder_adopt_moment(uuid,uuid,text,text) to authenticated;
commit;
