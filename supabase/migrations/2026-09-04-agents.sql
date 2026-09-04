-- Agent credentials are capabilities granted by a human, never a replacement human login.
begin;
create table if not exists public.grinder_rig_revisions (
 id uuid primary key default gen_random_uuid(), owner_id uuid not null references profiles(id),
 label text not null check(length(label) between 1 and 100),
 manifest jsonb not null check(jsonb_typeof(manifest)='object'),
 visibility text not null default 'private' check(visibility in ('private','public')),
 created_at timestamptz not null default now()
);
alter table grinder_rig_revisions enable row level security;
drop policy if exists rigs_read on grinder_rig_revisions;
create policy rigs_read on grinder_rig_revisions for select using(visibility='public' or owner_id=grinder_profile_id());
drop policy if exists rigs_add on grinder_rig_revisions;
create policy rigs_add on grinder_rig_revisions for insert to authenticated with check(owner_id=grinder_profile_id());
grant select on grinder_rig_revisions to anon,authenticated;
grant insert on grinder_rig_revisions to authenticated;

create table if not exists public.grinder_agents (
 id uuid primary key default gen_random_uuid(), owner_id uuid not null references profiles(id) on delete cascade,
 name text not null check(length(trim(name)) between 1 and 80),
 rig_revision uuid references grinder_rig_revisions(id),
 visibility text not null default 'private' check(visibility in ('private','public')),
 created_at timestamptz not null default now()
);
alter table grinder_agents enable row level security;
drop policy if exists agents_read on grinder_agents;
create policy agents_read on grinder_agents for select using(visibility='public' or owner_id=grinder_profile_id());
drop policy if exists agents_add on grinder_agents;
create policy agents_add on grinder_agents for insert to authenticated with check(owner_id=grinder_profile_id());
drop policy if exists agents_edit on grinder_agents;
create policy agents_edit on grinder_agents for update to authenticated using(owner_id=grinder_profile_id()) with check(owner_id=grinder_profile_id());
grant select on grinder_agents to anon,authenticated;
grant insert on grinder_agents to authenticated;
grant update(name,visibility,rig_revision) on grinder_agents to authenticated;
alter table runs add column if not exists source_actor_id uuid references grinder_agents(id);
alter table runs add column if not exists agent_name text;
alter table runs add column if not exists rig_revision uuid references grinder_rig_revisions(id);
alter table grinder_replies add column if not exists source_actor_id uuid references grinder_agents(id);
alter table grinder_replies add column if not exists agent_name text;
alter table grinder_replies add column if not exists question_id uuid;

create table if not exists public.grinder_agent_tokens (
 id uuid primary key default gen_random_uuid(), agent_id uuid not null references grinder_agents(id) on delete cascade,
 token_hash text not null unique, scopes text[] not null, audiences text[] not null,
 expires_at timestamptz not null, revoked boolean not null default false,
 window_started timestamptz not null default now(), window_actions integer not null default 0,
 created_at timestamptz not null default now()
);
create table if not exists public.grinder_agent_requests (
 token_id uuid not null references grinder_agent_tokens(id) on delete cascade,
 request_id uuid not null, fingerprint text not null, response jsonb not null,
 created_at timestamptz not null default now(), primary key(token_id,request_id)
);
create table if not exists public.grinder_agent_drafts (
 id uuid primary key default gen_random_uuid(), owner_id uuid not null references profiles(id) on delete cascade,
 agent_id uuid not null references grinder_agents(id), payload jsonb not null,
 created_at timestamptz not null default now()
);
alter table grinder_agent_tokens enable row level security;
alter table grinder_agent_requests enable row level security;
alter table grinder_agent_drafts enable row level security;
drop policy if exists agent_tokens_owner on grinder_agent_tokens;
create policy agent_tokens_owner on grinder_agent_tokens for select to authenticated using(exists(select 1 from grinder_agents a where a.id=agent_id and a.owner_id=grinder_profile_id()));
drop policy if exists agent_tokens_revoke on grinder_agent_tokens;
create policy agent_tokens_revoke on grinder_agent_tokens for update to authenticated using(exists(select 1 from grinder_agents a where a.id=agent_id and a.owner_id=grinder_profile_id()));
grant select(id,agent_id,scopes,audiences,expires_at,revoked,created_at) on grinder_agent_tokens to authenticated;
grant update(revoked) on grinder_agent_tokens to authenticated;
drop policy if exists agent_drafts_owner on grinder_agent_drafts;
create policy agent_drafts_owner on grinder_agent_drafts for select to authenticated using(owner_id=grinder_profile_id());
drop policy if exists agent_drafts_delete on grinder_agent_drafts;
create policy agent_drafts_delete on grinder_agent_drafts for delete to authenticated using(owner_id=grinder_profile_id());
grant select,delete on grinder_agent_drafts to authenticated;

create or replace function public.grinder_issue_agent_token(agent uuid,allowed_scopes text[],allowed_audiences text[],expires timestamptz) returns jsonb
language plpgsql security definer set search_path=public as $$
declare secret text:='ag_'||gen_random_uuid()::text||gen_random_uuid()::text; token_id uuid;
begin
 perform 1 from profiles where id=grinder_profile_id() for update;
 if not exists(select 1 from grinder_agents where id=agent and owner_id=grinder_profile_id()) then raise exception 'Only the agent owner can grant access'; end if;
 if (select count(*) from grinder_agent_tokens where agent_id=agent and not revoked and expires_at>now())>=5 then raise exception 'Revoke an existing token before issuing another (five active tokens per agent)'; end if;
 if allowed_scopes is null or cardinality(allowed_scopes)<1 or not allowed_scopes <@ array['draft','publish','reply','ack']::text[] then raise exception 'Choose valid action scopes'; end if;
 if allowed_audiences is null or cardinality(allowed_audiences)<1 or not allowed_audiences <@ array['private','public']::text[] then raise exception 'Choose private or public audiences'; end if;
 if expires is null or expires<=now() or expires>now()+interval '90 days' then raise exception 'Choose an expiry within 90 days'; end if;
 insert into grinder_agent_tokens(agent_id,token_hash,scopes,audiences,expires_at)
 values(agent,encode(sha256(convert_to(secret,'UTF8')),'hex'),allowed_scopes,allowed_audiences,expires) returning id into token_id;
 return jsonb_build_object('id',token_id,'token',secret,'expires_at',expires);
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
 if (payload->>'claims_verified')::integer>(payload->>'claims')::integer then raise exception 'Verified claims exceed counted claims'; end if;
 if payload ? 'duration_s' and payload->'duration_s'<>'null'::jsonb and (jsonb_typeof(payload->'duration_s')<>'number' or (payload->>'duration_s')::numeric<0) then raise exception 'Invalid duration'; end if;
 for field in select unnest(array['measurement_revision','baseline_revision']) loop
  if payload->field<>'null'::jsonb and (jsonb_typeof(payload->field)<>'string' or payload->>field!~'^[a-f0-9]{64}$') then raise exception 'Invalid measurement reference'; end if;
 end loop;
 if payload ? 'schema_version' and payload->>'schema_version'<>'1' then raise exception 'Unsupported grind format'; end if;
end $$;

create or replace function public.grinder_agent_action(token text,action text,payload jsonb,request_id uuid) returns jsonb
language plpgsql security definer set search_path=public as $$
declare capability grinder_agent_tokens; actor grinder_agents; prior grinder_agent_requests;
 fingerprint text; output jsonb; target runs; result_id uuid; audience text;
begin
 select * into capability from grinder_agent_tokens where token_hash=encode(sha256(convert_to(token,'UTF8')),'hex') for update;
 if not found or capability.revoked or capability.expires_at<=now() then raise exception 'Agent access is unavailable'; end if;
 if action is null or request_id is null then raise exception 'An action and request ID are required'; end if;
 if not action=any(capability.scopes) then raise exception 'This action is outside the granted scope'; end if;
 select * into actor from grinder_agents where id=capability.agent_id;
 perform 1 from profiles where id=actor.owner_id for update;
 perform grinder_check_agent_payload(payload);
 fingerprint=encode(sha256(convert_to(action||payload::text,'UTF8')),'hex');
 select * into prior from grinder_agent_requests r where r.token_id=capability.id and r.request_id=grinder_agent_action.request_id;
 if found then
  if prior.fingerprint<>fingerprint then raise exception 'A request ID cannot be reused for a different action'; end if;
  return prior.response;
 end if;
 if (select count(*) from grinder_agent_requests r join grinder_agent_tokens t on t.id=r.token_id join grinder_agents a on a.id=t.agent_id where a.owner_id=actor.owner_id and r.created_at>now()-interval '1 hour')>=60 then raise exception 'Hourly owner action limit reached'; end if;
 if capability.window_started<now()-interval '1 hour' then
  update grinder_agent_tokens set window_started=now(),window_actions=0 where id=capability.id;
 elsif capability.window_actions>=60 then raise exception 'Hourly action limit reached'; end if;
 if action in ('draft','publish') then
  audience=case when action='draft' then 'private' else coalesce(payload->>'visibility','private') end;
  if not audience=any(capability.audiences) then raise exception 'This audience is outside the granted scope'; end if;
  if audience='public' and actor.visibility<>'public' then raise exception 'Make the agent profile public before public participation'; end if;
  if action='draft' then
   insert into grinder_agent_drafts(owner_id,agent_id,payload) values(actor.owner_id,actor.id,payload) returning id into result_id;
  else
   insert into runs(profile_id,title,project,harness,prompts,duration_s,tool_calls,files_touched,commits,claims,claims_verified,artifacts_produced,visibility,started_at,source_actor_id,agent_name,schema_version,measurement_revision,baseline_revision,rhythm,route,note,trace_basis)
   values(actor.owner_id,left(coalesce(payload->>'title','Agent grind'),200),left(payload->>'project',200),left(payload->>'harness',100),
    (payload->>'turns_typed')::integer,(payload->>'duration_s')::double precision,(payload->>'tool_calls')::integer,
    (payload->>'files_touched')::integer,(payload->>'commits')::integer,(payload->>'claims')::integer,(payload->>'claims_verified')::integer,
    (payload->>'artifacts_produced')::integer,audience,(payload->>'started')::timestamptz,actor.id,actor.name,1,payload->>'measurement_revision',payload->>'baseline_revision',payload->'rhythm',payload->'route',left(payload->>'note',4000),left(payload->>'trace_basis',200)) returning id into result_id;
  end if;
 elsif action in ('reply','ack') then
  select * into target from runs where id=(payload->>'run_id')::uuid;
  if not found then raise exception 'Grind unavailable'; end if;
  audience=case when target.visibility in ('public','anonymous') then 'public' else 'private' end;
  if not audience=any(capability.audiences) or (audience='private' and target.profile_id<>actor.owner_id) then raise exception 'This grind is outside the granted audience'; end if;
  if audience='public' and actor.visibility<>'public' then raise exception 'Make the agent profile public before public participation'; end if;
  if action='reply' then
   insert into grinder_replies(run_id,author_id,body,source_actor_id,agent_name,question_id) values(target.id,actor.owner_id,payload->>'body',actor.id,actor.name,(payload->>'question_id')::uuid) returning id into result_id;
  else
   if target.profile_id=actor.owner_id then raise exception 'An agent cannot ACK its owner'; end if;
   if payload->>'reason' is null or payload->>'reason'<>all(array['shipped','focus','pace','rig','comeback','handoff']) then raise exception 'Choose a supported ACK reason'; end if;
   if exists(select 1 from acks where from_profile=actor.owner_id and run_id=target.id) then raise exception 'This owner already ACKed the grind'; end if;
   insert into acks(from_profile,to_profile,run_id,reason,same_owner) values(actor.owner_id,target.profile_id,target.id,payload->>'reason',false) returning id into result_id;
  end if;
 else raise exception 'Unsupported agent action';
 end if;
 output=jsonb_build_object('id',result_id,'action',action,'agent_id',actor.id);
 insert into grinder_agent_requests(token_id,request_id,fingerprint,response) values(capability.id,request_id,fingerprint,output);
 update grinder_agent_tokens set window_actions=window_actions+1 where id=capability.id;
 return output;
end $$;
revoke all on function grinder_issue_agent_token(uuid,text[],text[],timestamptz),grinder_agent_action(text,text,jsonb,uuid) from public;
grant execute on function grinder_issue_agent_token(uuid,text[],text[],timestamptz) to authenticated;
grant execute on function grinder_agent_action(text,text,jsonb,uuid) to anon,authenticated;

create or replace function grinder_validate_rig() returns trigger
language plpgsql set search_path=public as $$
declare key text; value jsonb; item jsonb;
begin
 if octet_length(new.manifest::text)>16384 then raise exception 'Rig exceeds 16 KiB'; end if;
 for key,value in select * from jsonb_each(new.manifest) loop
  if key not in ('harnesses','model','mcps','skills','notes') then raise exception 'Unsupported Rig field: %',key; end if;
  if key in ('harnesses','mcps','skills') then
   if jsonb_typeof(value)<>'array' then raise exception 'Rig names must be lists'; end if;
   for item in select * from jsonb_array_elements(value) loop
    if jsonb_typeof(item)<>'string' or length(item#>>'{}') not between 1 and 100 then raise exception 'Rig names must be short text'; end if;
   end loop;
  elsif jsonb_typeof(value)<>'string' or length(value#>>'{}')>2000 then raise exception 'Rig fields must be short text'; end if;
 end loop;
 if new.manifest::text ~* '(sk-[a-z0-9]{16,}|/Users/|/home/|-----BEGIN .*PRIVATE KEY|bearer [a-z0-9._-]{16,})' then raise exception 'Remove credentials and local paths from the Rig'; end if;
 return new;
end $$;
drop trigger if exists validate_rig on grinder_rig_revisions;
create trigger validate_rig before insert on grinder_rig_revisions for each row execute function grinder_validate_rig();
create or replace function grinder_validate_actor_rig() returns trigger
language plpgsql security definer set search_path=public as $$
begin
 if new.rig_revision is not null and not exists(select 1 from grinder_rig_revisions where id=new.rig_revision and owner_id=new.owner_id and (new.visibility='private' or visibility='public')) then raise exception 'Choose your own Rig with matching visibility'; end if;
 return new;
end $$;
drop trigger if exists validate_actor_rig on grinder_agents;
create trigger validate_actor_rig before insert or update on grinder_agents for each row execute function grinder_validate_actor_rig();
create or replace function grinder_keep_token_revoked() returns trigger
language plpgsql as $$ begin
 if old.revoked and not new.revoked then raise exception 'Revocation is permanent; issue a new credential'; end if;
 return new;
end $$;
drop trigger if exists keep_token_revoked on grinder_agent_tokens;
create trigger keep_token_revoked before update on grinder_agent_tokens for each row execute function grinder_keep_token_revoked();
commit;

