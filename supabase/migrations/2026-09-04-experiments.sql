-- Crew experiments preserve each cycle and the team's explicit adoption decision.
begin;
create table if not exists grinder_experiments (
 id uuid primary key default gen_random_uuid(),crew_id uuid not null references grinder_crews(id),
 owner_id uuid not null references profiles(id),practice_id uuid not null references grinder_practice_versions(id),
 name text not null check(length(trim(name)) between 1 and 160),
 intention text not null check(length(trim(intention)) between 1 and 2000),created_at timestamptz not null default now()
);
create table if not exists grinder_experiment_cycles (
 id uuid primary key default gen_random_uuid(),experiment_id uuid not null references grinder_experiments(id),
 owner_id uuid not null references profiles(id),baseline jsonb not null,outcome jsonb,
 decision text check(decision in ('adopt','revert','incomparable')),
 reflection text check(length(reflection)<=4000),created_at timestamptz not null default now(),reviewed_at timestamptz
);
alter table grinder_experiments enable row level security;
alter table grinder_experiment_cycles enable row level security;
drop policy if exists experiments_members on grinder_experiments;
create policy experiments_members on grinder_experiments for select to authenticated using(grinder_is_member(crew_id));
drop policy if exists cycles_members on grinder_experiment_cycles;
create policy cycles_members on grinder_experiment_cycles for select to authenticated using(exists(select 1 from grinder_experiments where id=experiment_id and grinder_is_member(crew_id)));
grant select on grinder_experiments,grinder_experiment_cycles to authenticated;
create or replace function grinder_create_experiment(crew uuid,practice uuid,title text,intent text) returns uuid
language plpgsql security definer set search_path=public as $$
declare result uuid;
begin
 if not grinder_is_member(crew) then raise exception 'Join the Crew to start an experiment'; end if;
 if not exists(select 1 from grinder_practice_versions where id=practice and (visibility='public' or (visibility='crew' and crew_id=crew))) then raise exception 'Choose a practice shared with this Crew'; end if;
 insert into grinder_experiments(crew_id,owner_id,practice_id,name,intention) values(crew,grinder_profile_id(),practice,title,intent) returning id into result;
 return result;
end $$;
create or replace function grinder_start_cycle(experiment uuid,baseline_run uuid) returns uuid
language plpgsql security definer set search_path=public as $$
declare result uuid; frozen jsonb;
begin
 if not exists(select 1 from grinder_experiments where id=experiment and grinder_is_member(crew_id)) then raise exception 'Experiment unavailable'; end if;
 frozen=grinder_run_snapshot(baseline_run);
 insert into grinder_experiment_cycles(experiment_id,owner_id,baseline) values(experiment,grinder_profile_id(),frozen) returning id into result;
 return result;
end $$;
create or replace function grinder_review_cycle(cycle uuid,outcome_run uuid,choice text,reflection_text text) returns void
language plpgsql security definer set search_path=public as $$
declare attempt grinder_experiment_cycles; observed jsonb;
begin
 select * into attempt from grinder_experiment_cycles where id=cycle for update;
 if not found or attempt.owner_id is distinct from grinder_profile_id() or not exists(select 1 from grinder_experiments where id=attempt.experiment_id and grinder_is_member(crew_id)) then raise exception 'Only this participant can record their outcome'; end if;
 if attempt.reviewed_at is not null then raise exception 'This cycle is fixed; start the next cycle'; end if;
 if choice is null or choice not in ('adopt','revert','incomparable') then raise exception 'Choose an adoption decision'; end if;
 if outcome_run is not null then
  observed=grinder_run_snapshot(outcome_run);
  if observed->>'started_at' is null or (observed->>'started_at')::timestamptz>now() or observed->>'measurement_revision'=attempt.baseline->>'measurement_revision' or (observed->>'started_at')::timestamptz<attempt.created_at then raise exception 'Choose a new session after the cycle began'; end if;
 end if;
 if (observed is null or observed->>'harness' is distinct from attempt.baseline->>'harness') and choice<>'incomparable' then raise exception 'Different or missing evidence needs an incomparable outcome'; end if;
 update grinder_experiment_cycles set outcome=observed,decision=choice,reflection=reflection_text,reviewed_at=now() where id=cycle;
end $$;
revoke all on function grinder_create_experiment(uuid,uuid,text,text),grinder_start_cycle(uuid,uuid),grinder_review_cycle(uuid,uuid,text,text) from public;
grant execute on function grinder_create_experiment(uuid,uuid,text,text),grinder_start_cycle(uuid,uuid),grinder_review_cycle(uuid,uuid,text,text) to authenticated;
commit;
