-- 2026-09-13 · keep/change/drop requires the same harness AND time basis.
-- Additive: replaces review functions only. Coordinator applies; not run against production here.

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
  if observed->>'started_at' is null or (observed->>'started_at')::timestamptz>now() or (observed->>'started_at')::timestamptz<original.created_at then raise exception 'The outcome session must start after the attempt'; end if;
 end if;
 if (
      not was_tried
      or observed is null
      or observed->>'harness' is null
      or original.baseline->>'harness' is null
      or observed->>'harness' is distinct from original.baseline->>'harness'
      or observed->>'trace_basis' is null
      or original.baseline->>'trace_basis' is null
      or observed->>'trace_basis' is distinct from original.baseline->>'trace_basis'
    ) and choice<>'incomparable' then
  raise exception 'Missing or different evidence needs an incomparable outcome';
 end if;
 update grinder_practice_attempts set outcome=observed,tried=was_tried,decision=choice,note=reflection,reviewed_at=now() where id=attempt;
end $$;

create or replace function grinder_review_cycle(cycle uuid,outcome_run uuid,choice text,reflection_text text) returns void
language plpgsql security definer set search_path=public as $$
declare attempt grinder_experiment_cycles; observed jsonb;
begin
 select * into attempt from grinder_experiment_cycles where id=cycle for update;
 if not found or attempt.owner_id is distinct from grinder_profile_id() or not exists(select 1 from grinder_experiments where id=attempt.experiment_id and grinder_is_member(crew_id)) then raise exception 'Only this participant can record their outcome'; end if;
 if attempt.reviewed_at is not null then raise exception 'This cycle is fixed; start the next cycle'; end if;
 if choice is null or choice not in ('adopt','revert','incomparable') then raise exception 'Choose adopt, revert or incomparable'; end if;
 if outcome_run is not null then
  observed=grinder_run_snapshot(outcome_run);
  if observed->>'started_at' is null or (observed->>'started_at')::timestamptz>now() or observed->>'measurement_revision'=attempt.baseline->>'measurement_revision' or (observed->>'started_at')::timestamptz<attempt.created_at then raise exception 'Choose a new session after the cycle began'; end if;
 end if;
 if (
      observed is null
      or observed->>'harness' is null
      or attempt.baseline->>'harness' is null
      or observed->>'harness' is distinct from attempt.baseline->>'harness'
      or observed->>'trace_basis' is null
      or attempt.baseline->>'trace_basis' is null
      or observed->>'trace_basis' is distinct from attempt.baseline->>'trace_basis'
    ) and choice<>'incomparable' then
  raise exception 'Different or missing evidence needs an incomparable outcome';
 end if;
 update grinder_experiment_cycles set outcome=observed,decision=choice,reflection=reflection_text,reviewed_at=now() where id=cycle;
end $$;

revoke all on function grinder_review_attempt(uuid,uuid,boolean,text,text),grinder_review_cycle(uuid,uuid,text,text) from public;
grant execute on function grinder_review_attempt(uuid,uuid,boolean,text,text),grinder_review_cycle(uuid,uuid,text,text) to authenticated;
