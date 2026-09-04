begin;
create or replace function grinder_run_contract_guard() returns trigger
language plpgsql security definer set search_path=public as $$
begin
 if new.prompts<0 or new.tool_calls<0 or new.files_touched<0 or new.commits<0 or new.claims<0 or new.claims_verified<0 or new.artifacts_produced<0 or new.claims_verified>new.claims then raise exception 'Grind counts must be non-negative and supported counts cannot exceed claims'; end if;
 if new.duration_s<0 or new.duration_s in ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8) then raise exception 'Invalid grind duration'; end if;
 if new.schema_version is not null and new.schema_version<>1 then raise exception 'Unsupported grind format'; end if;
 if new.measurement_revision is not null and new.measurement_revision!~'^[a-f0-9]{64}$' or new.baseline_revision is not null and new.baseline_revision!~'^[a-f0-9]{64}$' then raise exception 'Invalid measurement reference'; end if;
 if new.source_actor_id is not null and not exists(select 1 from grinder_agents where id=new.source_actor_id and owner_id=new.profile_id and (visibility='public' or new.visibility='private')) then raise exception 'Choose an owned agent with matching visibility'; end if;
 if new.rig_revision is not null and not exists(select 1 from grinder_rig_revisions where id=new.rig_revision and (visibility='public' or (owner_id=new.profile_id and new.visibility='private'))) then raise exception 'Rig is unavailable to this audience'; end if;
 return new;
end $$;
drop trigger if exists run_contract_guard on runs;
create trigger run_contract_guard before insert or update on runs for each row execute function grinder_run_contract_guard();
create or replace function grinder_reply_actor_guard() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 if new.source_actor_id is not null and not exists(select 1 from grinder_agents a join runs r on r.id=new.run_id where a.id=new.source_actor_id and a.owner_id=new.author_id and (a.visibility='public' or r.visibility='private')) then raise exception 'Choose an owned agent with matching visibility'; end if;
 return new;
end $$;
drop trigger if exists reply_actor_guard on grinder_replies;
create trigger reply_actor_guard before insert or update on grinder_replies for each row execute function grinder_reply_actor_guard();
commit;
