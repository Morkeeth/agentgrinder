-- Private comparisons freeze both runs and can start one next-run practice.
begin;
create table if not exists grinder_comparisons (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references profiles(id) on delete cascade,
 earlier_run uuid references runs(id) on delete set null,
 later_run uuid references runs(id) on delete set null,
 before_run jsonb not null, after_run jsonb not null,
 task_context text not null check(length(trim(task_context)) between 1 and 2000),
 context_confirmed boolean not null default false,
 limitations text[] not null,
 request_id uuid not null,
 next_practice uuid references grinder_practice_versions(id) on delete set null,
 next_attempt uuid references grinder_practice_attempts(id) on delete set null,
 created_at timestamptz not null default now(), unique(owner_id,request_id)
);
alter table grinder_comparisons enable row level security;
revoke all on grinder_comparisons from anon,authenticated;
grant select,delete on grinder_comparisons to authenticated;
drop policy if exists comparisons_owner_read on grinder_comparisons;
create policy comparisons_owner_read on grinder_comparisons for select to authenticated using(owner_id=grinder_profile_id());
drop policy if exists comparisons_owner_delete on grinder_comparisons;
create policy comparisons_owner_delete on grinder_comparisons for delete to authenticated using(owner_id=grinder_profile_id());

create or replace function grinder_progress_snapshot(grind uuid) returns jsonb
language plpgsql security definer set search_path=public as $$
declare activity runs;
begin
 select * into activity from runs where id=grind and profile_id=grinder_profile_id();
 if not found then raise exception 'Choose one of your own runs'; end if;
 if activity.measurement_revision is null then raise exception 'Import a run with a measurement revision before saving a comparison'; end if;
 return grinder_run_snapshot(grind)||jsonb_build_object('run_id',activity.id,'title',activity.title,
 'schema_version',activity.schema_version,'tool_calls',activity.tool_calls,'files_touched',activity.files_touched,
 'commits',activity.commits,'rig_revision',activity.rig_revision,'source_actor_id',activity.source_actor_id);
end $$;

create or replace function grinder_save_comparison(earlier uuid,later uuid,context_text text,similar_context boolean,request uuid) returns uuid
language plpgsql security definer set search_path=public as $$
declare owner uuid:=grinder_profile_id(); old grinder_comparisons; before_value jsonb; after_value jsonb;
 reasons text[]:=array[]::text[]; saved uuid;
begin
 if owner is null then raise exception 'Sign in to save a private comparison'; end if;
 if request is null or similar_context is null then raise exception 'A request and context choice are required'; end if;
 if context_text is null or length(trim(context_text)) not between 1 and 2000 then raise exception 'Describe the tasks you are comparing'; end if;
 perform 1 from profiles where id=owner for update;
 select * into old from grinder_comparisons where owner_id=owner and request_id=request;
 if found then
  if old.before_run->>'run_id' is distinct from earlier::text or old.after_run->>'run_id' is distinct from later::text or old.task_context<>trim(context_text) or old.context_confirmed<>similar_context then raise exception 'A retry cannot change the comparison'; end if;
  return old.id;
 end if;
 before_value=grinder_progress_snapshot(earlier); after_value=grinder_progress_snapshot(later);
 if earlier=later or before_value->>'measurement_revision'=after_value->>'measurement_revision' then raise exception 'Choose two different measured runs'; end if;
 if not similar_context then reasons=array_append(reasons,'Task context is not confirmed comparable'); end if;
 if before_value->>'harness' is null or before_value->>'harness' is distinct from after_value->>'harness' then reasons=array_append(reasons,'The harness is different or unknown'); end if;
 if before_value->>'trace_basis' is null or before_value->>'trace_basis' is distinct from after_value->>'trace_basis' then reasons=array_append(reasons,'The measurement time basis is different or unknown'); end if;
 if before_value->>'schema_version' is null or before_value->>'schema_version' is distinct from after_value->>'schema_version' then reasons=array_append(reasons,'The measurement format is different or unknown'); end if;
 if before_value->>'started_at' is null or after_value->>'started_at' is null then
  reasons=array_append(reasons,'One of the session times is unknown');
 elsif (after_value->>'started_at')::timestamptz <= (before_value->>'started_at')::timestamptz or (after_value->>'started_at')::timestamptz>now() then
  reasons=array_append(reasons,'The later session is not dated after the earlier session and before now');
 end if;
 insert into grinder_comparisons(owner_id,earlier_run,later_run,before_run,after_run,task_context,context_confirmed,limitations,request_id)
 values(owner,earlier,later,before_value,after_value,trim(context_text),similar_context,reasons,request) returning id into saved;
 return saved;
end $$;

create or replace function grinder_practice_from_comparison(comparison uuid,action_title text,expected_change text) returns jsonb
language plpgsql security definer set search_path=public as $$
declare item grinder_comparisons; practice uuid; attempt uuid; existing grinder_practice_versions;
begin
 select * into item from grinder_comparisons where id=comparison and owner_id=grinder_profile_id() for update;
 if not found then raise exception 'Choose your own saved comparison'; end if;
 if action_title is null or expected_change is null or length(trim(action_title)) not between 1 and 160 or length(trim(expected_change)) not between 1 and 2000 then raise exception 'Name one action and the change you expect'; end if;
 if item.next_practice is not null then
  select * into existing from grinder_practice_versions where id=item.next_practice;
  if existing.title<>trim(action_title) or existing.expected<>trim(expected_change) then raise exception 'This comparison already has a next practice'; end if;
  return jsonb_build_object('practice_id',item.next_practice,'attempt_id',item.next_attempt);
 end if;
 insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,harness,source_run,visibility)
 values(item.owner_id,trim(action_title),item.task_context,trim(action_title),trim(expected_change),coalesce(item.after_run->>'harness',''),item.later_run,'private') returning id into practice;
 -- Use the saved snapshot, never a current row that could have changed since comparison.
 insert into grinder_practice_attempts(practice_id,owner_id,baseline,visibility)
 values(practice,item.owner_id,item.after_run,'private') returning id into attempt;
 update grinder_comparisons set next_practice=practice,next_attempt=attempt where id=item.id;
 return jsonb_build_object('practice_id',practice,'attempt_id',attempt);
end $$;
revoke all on function grinder_progress_snapshot(uuid),grinder_save_comparison(uuid,uuid,text,boolean,uuid),grinder_practice_from_comparison(uuid,text,text) from public,anon,authenticated;
grant execute on function grinder_save_comparison(uuid,uuid,text,boolean,uuid),grinder_practice_from_comparison(uuid,text,text) to authenticated;
commit;
