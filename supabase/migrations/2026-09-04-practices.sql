-- Shared practice versions and explicit attempts. Counts do not establish causality.
begin;
create table if not exists grinder_practice_versions (
 id uuid primary key default gen_random_uuid(),owner_id uuid not null references profiles(id),
 title text not null check(length(trim(title)) between 1 and 160),
 task_context text not null check(length(trim(task_context)) between 1 and 2000),
 instruction text not null check(length(trim(instruction)) between 1 and 4000),
 expected text not null check(length(trim(expected)) between 1 and 2000),
 harness text not null default '' check(length(harness)<=100),
 source_run uuid references runs(id),rig_revision uuid references grinder_rig_revisions(id),
 visibility text not null default 'private' check(visibility in ('private','public','crew')),
 crew_id uuid references grinder_crews(id),created_at timestamptz not null default now(),
 check(visibility<>'crew' or crew_id is not null)
);
create table if not exists grinder_practice_attempts (
 id uuid primary key default gen_random_uuid(),practice_id uuid not null references grinder_practice_versions(id),
 owner_id uuid not null references profiles(id),baseline jsonb not null,
 outcome jsonb,decision text check(decision in ('keep','change','drop','incomparable')),
 tried boolean, note text check(length(note)<=4000),
 visibility text not null default 'private' check(visibility in ('private','shared')),
 created_at timestamptz not null default now(),reviewed_at timestamptz,
 check(decision is null or tried=true or decision='incomparable')
);
create or replace function grinder_can_read_practice(target uuid) returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from grinder_practice_versions where id=target and (owner_id=grinder_profile_id() or visibility='public' or (visibility='crew' and grinder_is_member(crew_id))))
$$;
alter table grinder_practice_versions enable row level security;
alter table grinder_practice_attempts enable row level security;
drop policy if exists practices_read on grinder_practice_versions;
create policy practices_read on grinder_practice_versions for select using(owner_id=grinder_profile_id() or visibility='public' or (visibility='crew' and grinder_is_member(crew_id)));
drop policy if exists practices_create on grinder_practice_versions;
create policy practices_create on grinder_practice_versions for insert to authenticated with check(owner_id=grinder_profile_id() and (visibility<>'crew' or grinder_is_member(crew_id)));
drop policy if exists attempts_read on grinder_practice_attempts;
create policy attempts_read on grinder_practice_attempts for select using(owner_id=grinder_profile_id() or (visibility='shared' and grinder_can_read_practice(practice_id)));
grant select on grinder_practice_versions,grinder_practice_attempts to anon,authenticated;
grant insert on grinder_practice_versions to authenticated;

create or replace function grinder_practice_source_guard() returns trigger
language plpgsql security definer set search_path=public as $$
begin
 if new.source_run is not null and not exists(select 1 from runs where id=new.source_run and grinder_can_read_run(id) and (new.visibility='private' or visibility='public' or (new.visibility='crew' and crew_shared and crew_id=new.crew_id))) then raise exception 'The source grind must be available to the practice audience'; end if;
 if new.rig_revision is not null and not exists(select 1 from grinder_rig_revisions where id=new.rig_revision and (visibility='public' or (new.visibility='private' and owner_id=new.owner_id))) then raise exception 'Choose an accessible Rig revision'; end if;
 return new;
end $$;
drop trigger if exists practice_source_guard on grinder_practice_versions;
create trigger practice_source_guard before insert on grinder_practice_versions for each row execute function grinder_practice_source_guard();

create or replace function grinder_run_snapshot(grind uuid) returns jsonb
language plpgsql security definer set search_path=public as $$
declare activity runs;
begin
 select * into activity from runs where id=grind and profile_id=grinder_profile_id();
 if not found then raise exception 'Choose one of your grinds'; end if;
 if activity.measurement_revision is null then raise exception 'This grind needs a measurement revision'; end if;
 return jsonb_build_object('measurement_revision',activity.measurement_revision,'harness',activity.harness,
 'turns_typed',activity.prompts,'claims',activity.claims,'claims_verified',activity.claims_verified,
 'artifacts_produced',activity.artifacts_produced,'rhythm',activity.rhythm,'trace_basis',activity.trace_basis,'duration_s',activity.duration_s,'started_at',activity.started_at);
end $$;
create or replace function grinder_start_attempt(practice uuid,baseline_run uuid,share boolean default false) returns uuid
language plpgsql security definer set search_path=public as $$
declare result uuid; frozen jsonb;
begin
 if grinder_profile_id() is null or not grinder_can_read_practice(practice) then raise exception 'Practice unavailable'; end if;
 frozen=grinder_run_snapshot(baseline_run);
 insert into grinder_practice_attempts(practice_id,owner_id,baseline,visibility)
 values(practice,grinder_profile_id(),frozen,case when share then 'shared' else 'private' end) returning id into result;
 return result;
end $$;
create or replace function grinder_review_attempt(attempt uuid,outcome_run uuid,was_tried boolean,choice text,reflection text) returns void
language plpgsql security definer set search_path=public as $$
declare original grinder_practice_attempts; observed jsonb;
begin
 select * into original from grinder_practice_attempts where id=attempt for update;
 if not found or original.owner_id is distinct from grinder_profile_id() then raise exception 'Only the participant can review this attempt'; end if;
 if original.reviewed_at is not null then raise exception 'This review is fixed; start another attempt for a new cycle'; end if;
 if was_tried is null or choice is null or choice not in ('keep','change','drop','incomparable') then raise exception 'Choose whether you tried it and an outcome'; end if;
 if outcome_run is not null then
  observed=grinder_run_snapshot(outcome_run);
  if observed->>'measurement_revision'=original.baseline->>'measurement_revision' then raise exception 'Choose a new run for the outcome'; end if;
  if (observed->>'started_at')::timestamptz<original.created_at then raise exception 'The outcome session must start after the attempt'; end if;
 end if;
 if (not was_tried or observed is null or observed->>'harness' is distinct from original.baseline->>'harness') and choice<>'incomparable' then raise exception 'Missing or different evidence needs an incomparable outcome'; end if;
 update grinder_practice_attempts set outcome=observed,tried=was_tried,decision=choice,note=reflection,reviewed_at=now() where id=attempt;
end $$;
revoke all on function grinder_run_snapshot(uuid),grinder_start_attempt(uuid,uuid,boolean),grinder_review_attempt(uuid,uuid,boolean,text,text) from public;
grant execute on function grinder_start_attempt(uuid,uuid,boolean),grinder_review_attempt(uuid,uuid,boolean,text,text) to authenticated;
commit;
