begin;
create table if not exists grinder_blocks (
 blocker_id uuid not null references profiles(id) on delete cascade,
 blocked_id uuid not null references profiles(id) on delete cascade,
 created_at timestamptz not null default now(),primary key(blocker_id,blocked_id),check(blocker_id<>blocked_id)
);
create table if not exists grinder_reports (
 id uuid primary key default gen_random_uuid(),reporter_id uuid not null references profiles(id),
 run_id uuid references runs(id) on delete set null,reply_id uuid references grinder_replies(id) on delete set null,
 reason text not null check(length(trim(reason)) between 1 and 2000),created_at timestamptz not null default now()
);
alter table grinder_blocks enable row level security;
alter table grinder_reports enable row level security;
drop policy if exists blocks_owner on grinder_blocks;
create policy blocks_owner on grinder_blocks for all to authenticated using(blocker_id=grinder_profile_id()) with check(blocker_id=grinder_profile_id());
drop policy if exists reports_read on grinder_reports;
create policy reports_read on grinder_reports for select to authenticated using(reporter_id=grinder_profile_id());
drop policy if exists reports_create on grinder_reports;
create policy reports_create on grinder_reports for insert to authenticated with check(reporter_id=grinder_profile_id() and (run_id is not null or reply_id is not null) and (run_id is null or grinder_can_read_run(run_id)) and (reply_id is null or exists(select 1 from grinder_replies where id=reply_id)));
grant select,insert,delete on grinder_blocks to authenticated;
grant select,insert on grinder_reports to authenticated;
create or replace function grinder_blocked(a uuid,b uuid) returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from grinder_blocks where (blocker_id=a and blocked_id=b) or (blocker_id=b and blocked_id=a))
$$;
drop policy if exists blocked_runs on runs;
create policy blocked_runs on runs as restrictive for select to authenticated using(not grinder_blocked(profile_id,grinder_profile_id()));
drop policy if exists blocked_replies on grinder_replies;
create policy blocked_replies on grinder_replies as restrictive for select to authenticated using(not grinder_blocked(author_id,grinder_profile_id()));
drop policy if exists blocked_notifications on grinder_notifications;
create policy blocked_notifications on grinder_notifications as restrictive for select to authenticated using(not grinder_blocked(actor_id,grinder_profile_id()));
drop policy if exists blocked_practices on grinder_practice_versions;
create policy blocked_practices on grinder_practice_versions as restrictive for select to authenticated using(not grinder_blocked(owner_id,grinder_profile_id()));

create or replace function grinder_interaction_guard() returns trigger
language plpgsql security definer set search_path=public as $$
declare actor uuid; target uuid;
begin
 if tg_table_name='grinder_replies' then
  actor=new.author_id;select profile_id into target from runs where id=new.run_id;
 elsif tg_table_name='acks' then
  actor=new.from_profile;select profile_id into target from runs where id=new.run_id;
  if target is null or target=new.from_profile or target is distinct from new.to_profile then raise exception 'ACK needs another owner and their grind'; end if;
  if new.reason is null or new.reason<>all(array['shipped','focus','pace','rig','comeback','handoff']) then raise exception 'Choose a supported ACK reason'; end if;
  if not exists(select 1 from runs where id=new.run_id and (visibility in ('public','anonymous') or (crew_shared and exists(select 1 from grinder_memberships where crew_id=runs.crew_id and profile_id=actor)))) then raise exception 'Grind unavailable'; end if;
 else actor=new.follower_id;target=new.followed_id;
 end if;
 if grinder_blocked(actor,target) then raise exception 'This interaction is unavailable'; end if;
 return new;
end $$;
drop trigger if exists reply_interactions on grinder_replies;
create trigger reply_interactions before insert on grinder_replies for each row execute function grinder_interaction_guard();
drop trigger if exists ack_interactions on acks;
create trigger ack_interactions before insert on acks for each row execute function grinder_interaction_guard();
drop trigger if exists follow_interactions on grinder_follows;
create trigger follow_interactions before insert on grinder_follows for each row execute function grinder_interaction_guard();
create or replace function grinder_notify_ack() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 insert into grinder_notifications(recipient_id,actor_id,kind,run_id,source_id) values(new.to_profile,new.from_profile,'ack',new.run_id,new.id) on conflict do nothing;
 return new;
end $$;
drop trigger if exists notify_ack on acks;
create trigger notify_ack after insert on acks for each row execute function grinder_notify_ack();

create or replace function grinder_run_crew_guard() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 if new.crew_shared and (tg_op='INSERT' or new.crew_id is distinct from old.crew_id or new.crew_shared is distinct from old.crew_shared) and not exists(select 1 from grinder_memberships where crew_id=new.crew_id and profile_id=new.profile_id) then raise exception 'The grind owner must belong to the receiving Crew'; end if;
 return new;
end $$;
drop trigger if exists run_crew_guard on runs;
create trigger run_crew_guard before insert or update on runs for each row execute function grinder_run_crew_guard();
commit;
