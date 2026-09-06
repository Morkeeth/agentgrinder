-- Builder-authored highlights, never automatically verified evidence or raw transcripts.
begin;
create table if not exists grinder_run_moments (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references runs(id) on delete cascade,
 owner_id uuid not null references profiles(id) on delete cascade,
 measurement_revision text not null check(measurement_revision ~ '^[a-f0-9]{64}$'),
 title text not null check(length(trim(title)) between 1 and 100),
 claim text not null check(length(trim(claim)) between 1 and 1000),
 evidence_ref text not null check(length(trim(evidence_ref)) between 1 and 1000),
 excerpt text not null check(length(trim(excerpt)) between 1 and 3000),
 limitation text not null check(length(trim(limitation)) between 1 and 1000),
 next_action text not null check(length(trim(next_action)) between 1 and 160),
 bucket integer check(bucket between 0 and 9999),
 created_at timestamptz not null default now()
);
alter table grinder_run_moments enable row level security;
drop policy if exists moments_read on grinder_run_moments;
create policy moments_read on grinder_run_moments for select using(grinder_can_read_run(run_id));
drop policy if exists moments_create on grinder_run_moments;
create policy moments_create on grinder_run_moments for insert to authenticated with check(owner_id=grinder_profile_id() and exists(select 1 from runs r where r.id=run_id and r.profile_id=grinder_profile_id() and r.measurement_revision=grinder_run_moments.measurement_revision));
drop policy if exists moments_remove on grinder_run_moments;
create policy moments_remove on grinder_run_moments for delete to authenticated using(owner_id=grinder_profile_id());
grant select on grinder_run_moments to anon,authenticated;
grant insert,delete on grinder_run_moments to authenticated;
revoke update on grinder_run_moments from anon,authenticated;
create table if not exists grinder_moment_practices (
 moment_id uuid primary key references grinder_run_moments(id) on delete cascade,
 practice_id uuid not null references grinder_practice_versions(id) on delete cascade,
 attempt_id uuid not null references grinder_practice_attempts(id) on delete cascade
);
alter table grinder_moment_practices enable row level security;
revoke all on grinder_moment_practices from anon,authenticated;
-- Freeze the baseline in the same transaction as the private practice/attempt.
create or replace function grinder_practice_from_moment(moment uuid,action_title text,expected_change text) returns jsonb
language plpgsql security definer set search_path=public as $$
declare m grinder_run_moments; r runs; p uuid; a uuid; saved grinder_moment_practices;
begin
 select * into m from grinder_run_moments where id=moment for update;
 if not found or m.owner_id is distinct from grinder_profile_id() then raise exception 'Choose a moment from your own grind'; end if;
 select * into saved from grinder_moment_practices where moment_id=m.id;
 if found then
  if not exists(select 1 from grinder_practice_versions where id=saved.practice_id and title=action_title and expected=expected_change) then raise exception 'This moment already started a different practice'; end if;
  return jsonb_build_object('practice_id',saved.practice_id,'attempt_id',saved.attempt_id);
 end if;
 select * into r from runs where id=m.run_id for update;
 if not found or r.profile_id is distinct from grinder_profile_id() or r.measurement_revision is distinct from m.measurement_revision then raise exception 'The grind measurement changed. Create a new moment before choosing its baseline'; end if;
 insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,harness,source_run,visibility)
 values(grinder_profile_id(),action_title,'From '||m.title,action_title,expected_change,coalesce(r.harness,''),r.id,'private') returning id into p;
 a=grinder_start_attempt(p,r.id,false);
 insert into grinder_moment_practices values(m.id,p,a);
 return jsonb_build_object('practice_id',p,'attempt_id',a);
end $$;
revoke all on function grinder_practice_from_moment(uuid,text,text) from public;
grant execute on function grinder_practice_from_moment(uuid,text,text) to authenticated;
commit;
