begin;
-- Link IDs are bearer secrets: only the run named by the current link may be read.
create or replace function grinder_link_access(target uuid) returns boolean
language sql stable set search_path=public as $$
 select coalesce(nullif(current_setting('request.headers',true),'')::jsonb->>'x-grinder-run-id'=target::text,false)
$$;
revoke all on function grinder_link_access(uuid) from public;
grant execute on function grinder_link_access(uuid) to anon,authenticated;
drop policy if exists grinder_link_not_enumerable on runs;
create policy grinder_link_not_enumerable on runs as restrictive for select to anon,authenticated
using(visibility<>'link' or profile_id=grinder_profile_id() or grinder_link_access(id) or (crew_shared and grinder_is_member(crew_id)));
create or replace function public.grinder_can_read_run(target uuid) returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from runs where id=target and not grinder_blocked_pair(profile_id,grinder_profile_id()) and
 (profile_id=grinder_profile_id() or visibility='public' or (visibility='link' and grinder_link_access(id))
 or (crew_shared and grinder_is_member(crew_id))))
$$;
drop policy if exists grinder_ack_read_audience on acks;
create policy grinder_ack_read_audience on acks as restrictive for select to anon,authenticated using(grinder_can_read_run(run_id));
commit;
