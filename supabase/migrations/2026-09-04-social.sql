-- Social product records. Existing profiles and runs remain the identity and activity roots.
-- Run in one transaction: a failed installation must not expose a half-protected table.
begin;

create or replace function public.grinder_profile_id() returns uuid
language sql stable security definer set search_path = public
as $$ select id from public.profiles where auth_uid = auth.uid() limit 1 $$;

create table if not exists public.grinder_follows (
  follower_id uuid not null references public.profiles(id) on delete cascade,
  followed_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (follower_id, followed_id),
  check (follower_id <> followed_id)
);

create table if not exists public.grinder_crews (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id),
  name text not null check (length(trim(name)) between 1 and 80),
  description text not null default '' check (length(description) <= 1000),
  visibility text not null default 'private' check (visibility in ('private','public')),
  created_at timestamptz not null default now()
);
create table if not exists public.grinder_memberships (
  crew_id uuid not null references public.grinder_crews(id) on delete cascade,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  role text not null default 'member' check (role in ('owner','member')),
  joined_at timestamptz not null default now(),
  primary key (crew_id, profile_id)
);
create table if not exists public.grinder_invites (
  id uuid primary key default gen_random_uuid(),
  crew_id uuid not null references public.grinder_crews(id) on delete cascade,
  token_hash text not null unique,
  expires_at timestamptz not null default now() + interval '7 days',
  revoked boolean not null default false,
  accepted_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);
alter table public.runs add column if not exists crew_id uuid references public.grinder_crews(id);
alter table public.runs add column if not exists crew_shared boolean not null default false;

create or replace function public.grinder_is_member(target uuid) returns boolean
language sql stable security definer set search_path = public
as $$ select exists(select 1 from grinder_memberships where crew_id=target and profile_id=grinder_profile_id()) $$;

create or replace function public.grinder_owns_crew(target uuid) returns boolean
language sql stable security definer set search_path = public
as $$ select exists(select 1 from grinder_crews where id=target and owner_id=grinder_profile_id()) $$;

create or replace function public.grinder_can_read_run(target uuid) returns boolean
language sql stable security definer set search_path = public
as $$ select exists(select 1 from runs where id=target and
    (profile_id=grinder_profile_id() or visibility in ('public','link')
     or (crew_shared and grinder_is_member(crew_id)))) $$;

drop policy if exists grinder_crew_runs_read on public.runs;
create policy grinder_crew_runs_read on public.runs for select to authenticated
  using (crew_shared and grinder_is_member(crew_id));

create table if not exists public.grinder_replies (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.runs(id) on delete cascade,
  author_id uuid not null references public.profiles(id) on delete cascade,
  parent_id uuid references public.grinder_replies(id) on delete set null,
  body text not null check (length(trim(body)) between 1 and 3000),
  evidence_ref text check (length(evidence_ref) <= 200),
  created_at timestamptz not null default now(),
  edited_at timestamptz
);
create index if not exists grinder_replies_run_time on public.grinder_replies(run_id,created_at,id);

create table if not exists public.grinder_notifications (
  id uuid primary key default gen_random_uuid(),
  recipient_id uuid not null references public.profiles(id) on delete cascade,
  actor_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null check (kind in ('follow','reply','ack')),
  run_id uuid references public.runs(id) on delete cascade,
  source_id uuid,
  created_at timestamptz not null default now(),
  read_at timestamptz,
  unique(recipient_id,kind,source_id)
);
create index if not exists grinder_notifications_recipient on public.grinder_notifications(recipient_id,created_at desc);

alter table public.grinder_follows enable row level security;
alter table public.grinder_crews enable row level security;
alter table public.grinder_memberships enable row level security;
alter table public.grinder_invites enable row level security;
alter table public.grinder_replies enable row level security;
alter table public.grinder_notifications enable row level security;

drop policy if exists grinder_follows_read on public.grinder_follows;
create policy grinder_follows_read on public.grinder_follows for select using (true);
drop policy if exists grinder_follows_add on public.grinder_follows;
create policy grinder_follows_add on public.grinder_follows for insert to authenticated with check (follower_id=grinder_profile_id());
drop policy if exists grinder_follows_remove on public.grinder_follows;
create policy grinder_follows_remove on public.grinder_follows for delete to authenticated using (follower_id=grinder_profile_id());

drop policy if exists grinder_crews_read on public.grinder_crews;
create policy grinder_crews_read on public.grinder_crews for select using (visibility='public' or grinder_is_member(id));
drop policy if exists grinder_crews_edit on public.grinder_crews;
create policy grinder_crews_edit on public.grinder_crews for update to authenticated using (owner_id=grinder_profile_id()) with check (owner_id=grinder_profile_id());
drop policy if exists grinder_members_read on public.grinder_memberships;
create policy grinder_members_read on public.grinder_memberships for select using
  (grinder_is_member(crew_id) or exists(select 1 from grinder_crews c where c.id=crew_id and c.visibility='public'));
drop policy if exists grinder_invites_read on public.grinder_invites;
create policy grinder_invites_read on public.grinder_invites for select to authenticated using (grinder_owns_crew(crew_id));
drop policy if exists grinder_invites_revoke on public.grinder_invites;
create policy grinder_invites_revoke on public.grinder_invites for update to authenticated using (grinder_owns_crew(crew_id)) with check (grinder_owns_crew(crew_id));

drop policy if exists grinder_replies_read on public.grinder_replies;
create policy grinder_replies_read on public.grinder_replies for select using (grinder_can_read_run(run_id));
drop policy if exists grinder_replies_add on public.grinder_replies;
create policy grinder_replies_add on public.grinder_replies for insert to authenticated with check
  (author_id=grinder_profile_id() and grinder_can_read_run(run_id));
drop policy if exists grinder_replies_edit on public.grinder_replies;
create policy grinder_replies_edit on public.grinder_replies for update to authenticated using
  (author_id=grinder_profile_id() and grinder_can_read_run(run_id)) with check (author_id=grinder_profile_id() and grinder_can_read_run(run_id));
drop policy if exists grinder_replies_delete on public.grinder_replies;
create policy grinder_replies_delete on public.grinder_replies for delete to authenticated using (author_id=grinder_profile_id());
drop policy if exists grinder_notifications_read on public.grinder_notifications;
create policy grinder_notifications_read on public.grinder_notifications for select to authenticated using
  (recipient_id=grinder_profile_id() and (run_id is null or grinder_can_read_run(run_id)));
drop policy if exists grinder_notifications_seen on public.grinder_notifications;
create policy grinder_notifications_seen on public.grinder_notifications for update to authenticated using
  (recipient_id=grinder_profile_id()) with check (recipient_id=grinder_profile_id());

-- Mutation grants are column-specific. A reply edit cannot move it to a different run,
-- change its author, or attach it to another person's private thread.
grant select on grinder_follows,grinder_crews,grinder_memberships,grinder_replies to anon,authenticated;
grant select on grinder_invites,grinder_notifications to authenticated;
grant insert,delete on grinder_follows,grinder_replies to authenticated;
grant update(body) on grinder_replies to authenticated;
grant update(name,description,visibility) on grinder_crews to authenticated;
grant update(revoked) on grinder_invites to authenticated;
grant update(read_at) on grinder_notifications to authenticated;

create or replace function public.grinder_create_crew(crew_name text, crew_visibility text default 'private') returns uuid
language plpgsql security definer set search_path = public as $$
declare me uuid := grinder_profile_id(); result uuid;
begin
  if me is null then raise exception 'Sign in to create a Crew'; end if;
  insert into grinder_crews(owner_id,name,visibility) values(me,trim(crew_name),crew_visibility) returning id into result;
  insert into grinder_memberships(crew_id,profile_id,role) values(result,me,'owner');
  return result;
end $$;

create or replace function public.grinder_invite(crew uuid) returns text
language plpgsql security definer set search_path = public as $$
declare token text := gen_random_uuid()::text || gen_random_uuid()::text;
begin
  if not grinder_owns_crew(crew) then raise exception 'Only the Crew owner can invite members'; end if;
  insert into grinder_invites(crew_id,token_hash) values(crew,encode(sha256(convert_to(token,'UTF8')),'hex'));
  return token;
end $$;

create or replace function public.grinder_join_crew(token text) returns uuid
language plpgsql security definer set search_path = public as $$
declare me uuid := grinder_profile_id(); invitation grinder_invites;
begin
  if me is null then raise exception 'Sign in to join a Crew'; end if;
  select * into invitation from grinder_invites where token_hash=encode(sha256(convert_to(token,'UTF8')),'hex') for update;
  if not found or invitation.revoked or invitation.expires_at <= now() then raise exception 'This invitation is unavailable'; end if;
  if invitation.accepted_by is not null and invitation.accepted_by<>me then raise exception 'This invitation has already been used'; end if;
  insert into grinder_memberships(crew_id,profile_id) values(invitation.crew_id,me) on conflict do nothing;
  update grinder_invites set accepted_by=me where id=invitation.id;
  return invitation.crew_id;
end $$;

create or replace function public.grinder_remove_member(crew uuid, member uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if grinder_profile_id() is null or (member<>grinder_profile_id() and not grinder_owns_crew(crew)) then raise exception 'You cannot remove this member'; end if;
  if exists(select 1 from grinder_crews where id=crew and owner_id=member) then raise exception 'Transfer ownership before leaving the Crew'; end if;
  delete from grinder_memberships where crew_id=crew and profile_id=member;
end $$;

create or replace function public.grinder_reply_guard() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.parent_id is not null and not exists(select 1 from grinder_replies where id=new.parent_id and run_id=new.run_id) then
    raise exception 'The parent reply belongs to another grind';
  end if;
  if tg_op='UPDATE' then new.edited_at=now(); end if;
  return new;
end $$;
drop trigger if exists grinder_reply_guard on grinder_replies;
create trigger grinder_reply_guard before insert or update on grinder_replies for each row execute function grinder_reply_guard();

create or replace function public.grinder_notify_reply() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into grinder_notifications(recipient_id,actor_id,kind,run_id,source_id)
    select profile_id,new.author_id,'reply',new.run_id,new.id from runs where id=new.run_id and profile_id<>new.author_id
    on conflict do nothing;
  if new.parent_id is not null then
    insert into grinder_notifications(recipient_id,actor_id,kind,run_id,source_id)
      select author_id,new.author_id,'reply',new.run_id,new.id from grinder_replies where id=new.parent_id and author_id<>new.author_id
      on conflict do nothing;
  end if;
  return new;
end $$;
drop trigger if exists grinder_notify_reply on grinder_replies;
create trigger grinder_notify_reply after insert on grinder_replies for each row execute function grinder_notify_reply();

create or replace function public.grinder_share_with_crew(grind uuid,crew uuid,keep_public boolean default false) returns void
language plpgsql security definer set search_path = public as $$
begin
  if grinder_profile_id() is null or not exists(select 1 from runs where id=grind and profile_id=grinder_profile_id()) then raise exception 'Only the grind owner can share it'; end if;
  if not grinder_is_member(crew) then raise exception 'Join the Crew before sharing a grind'; end if;
  update runs set crew_id=crew,crew_shared=true,visibility=case when keep_public then 'public' else 'private' end where id=grind;
end $$;

create or replace function public.grinder_transfer_crew(crew uuid,new_owner uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not grinder_owns_crew(crew) then raise exception 'Only the owner can transfer the Crew'; end if;
  if not exists(select 1 from grinder_memberships where crew_id=crew and profile_id=new_owner) then raise exception 'Choose a current member'; end if;
  update grinder_memberships set role='member' where crew_id=crew;
  update grinder_memberships set role='owner' where crew_id=crew and profile_id=new_owner;
  update grinder_crews set owner_id=new_owner where id=crew;
  update grinder_challenges set owner_id=new_owner where host_crew=crew;
end $$;

create or replace function public.grinder_notify_follow() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into grinder_notifications(recipient_id,actor_id,kind,source_id)
    values(new.followed_id,new.follower_id,'follow',new.follower_id) on conflict do nothing;
  return new;
end $$;
drop trigger if exists grinder_notify_follow on grinder_follows;
create trigger grinder_notify_follow after insert on grinder_follows for each row execute function grinder_notify_follow();

revoke all on function grinder_share_with_crew(uuid,uuid,boolean),grinder_transfer_crew(uuid,uuid) from public;
grant execute on function grinder_share_with_crew(uuid,uuid,boolean),grinder_transfer_crew(uuid,uuid) to authenticated;

revoke all on function grinder_create_crew(text,text),grinder_invite(uuid),grinder_join_crew(text),grinder_remove_member(uuid,uuid) from public;
grant execute on function grinder_create_crew(text,text),grinder_invite(uuid),grinder_join_crew(text),grinder_remove_member(uuid,uuid) to authenticated;
commit;
