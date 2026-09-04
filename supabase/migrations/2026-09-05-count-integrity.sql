begin;
create or replace function grinder_run_contract_guard() returns trigger
language plpgsql security definer set search_path=public as $$
begin
 if new.claims_verified is not null and new.claims is null then raise exception 'Verified claims require a counted-claims total'; end if;
 if new.prompts<0 or new.tool_calls<0 or new.files_touched<0 or new.commits<0 or new.claims<0 or new.claims_verified<0 or new.artifacts_produced<0 or new.claims_verified>new.claims then raise exception 'Grind counts must be non-negative and supported counts cannot exceed claims'; end if;
 if new.duration_s<0 or new.duration_s in ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8) then raise exception 'Invalid grind duration'; end if;
 if new.schema_version is not null and new.schema_version<>1 then raise exception 'Unsupported grind format'; end if;
 if new.measurement_revision is not null and new.measurement_revision!~'^[a-f0-9]{64}$' or new.baseline_revision is not null and new.baseline_revision!~'^[a-f0-9]{64}$' then raise exception 'Invalid measurement reference'; end if;
 if new.source_actor_id is not null and not exists(select 1 from grinder_agents where id=new.source_actor_id and owner_id=new.profile_id and (visibility='public' or new.visibility='private')) then raise exception 'Choose an owned agent with matching visibility'; end if;
 if new.rig_revision is not null and not exists(select 1 from grinder_rig_revisions where id=new.rig_revision and (visibility='public' or (owner_id=new.profile_id and new.visibility='private'))) then raise exception 'Rig is unavailable to this audience'; end if;
 return new;
end $$;
create or replace function public.grinder_check_agent_payload(payload jsonb) returns void
language plpgsql set search_path=public as $$
declare field text; value jsonb;
begin
 if jsonb_typeof(payload) is distinct from 'object' or octet_length(payload::text)>65536 then raise exception 'Send a grind object under 64 KiB'; end if;
 for field,value in select * from jsonb_each(payload) loop
  if not field=any(array['title','project','harness','turns_typed','duration_s','tool_calls','files_touched','commits','claims','claims_verified','artifacts_produced','started','visibility','rhythm','route','schema_version','measurement_revision','baseline_revision','trace_basis','note','run_id','body','reason','question_id']) then raise exception 'Unsupported public field: %',field; end if;
  if field=any(array['turns_typed','tool_calls','files_touched','commits','claims','claims_verified','artifacts_produced']) and value<>'null'::jsonb then
   if jsonb_typeof(value)<>'number' or (value::text)::numeric<0 or (value::text)::numeric<>floor((value::text)::numeric) or (value::text)::numeric>2147483647 then raise exception 'Counts must be non-negative whole numbers'; end if;
  end if;
 end loop;
 if payload->>'claims_verified' is not null and payload->>'claims' is null then raise exception 'Verified claims require a counted-claims total'; end if;
 if (payload->>'claims_verified')::integer>(payload->>'claims')::integer then raise exception 'Verified claims exceed counted claims'; end if;
 if payload ? 'duration_s' and payload->'duration_s'<>'null'::jsonb and (jsonb_typeof(payload->'duration_s')<>'number' or (payload->>'duration_s')::numeric<0) then raise exception 'Invalid duration'; end if;
 for field in select unnest(array['measurement_revision','baseline_revision']) loop
  if payload->field<>'null'::jsonb and (jsonb_typeof(payload->field)<>'string' or payload->>field!~'^[a-f0-9]{64}$') then raise exception 'Invalid measurement reference'; end if;
 end loop;
 if payload ? 'schema_version' and payload->>'schema_version'<>'1' then raise exception 'Unsupported grind format'; end if;
end $$;

commit;
