begin;
create table if not exists grinder_forum_questions (
 id uuid primary key default gen_random_uuid(), run_id uuid not null references runs(id) on delete cascade,
 author_id uuid not null references profiles(id) on delete cascade,
 title text not null check(length(trim(title)) between 1 and 160),
 body text not null check(length(trim(body)) between 1 and 3000),
 accepted_reply uuid references grinder_replies(id) on delete set null,
 request_id uuid not null, created_at timestamptz not null default now(), unique(author_id,request_id)
);
alter table grinder_replies add column if not exists forum_question_id uuid references grinder_forum_questions(id) on delete cascade;
create index if not exists grinder_forum_answers on grinder_replies(forum_question_id,created_at);
create table if not exists grinder_forum_subscriptions (
 question_id uuid references grinder_forum_questions(id) on delete cascade,
 profile_id uuid references profiles(id) on delete cascade,
 last_seen_at timestamptz not null default now(), created_at timestamptz not null default now(),
 primary key(question_id,profile_id)
);
alter table grinder_forum_questions enable row level security;
alter table grinder_forum_subscriptions enable row level security;
revoke all on grinder_forum_questions,grinder_forum_subscriptions from public,anon,authenticated;
grant select on grinder_forum_questions to anon,authenticated;
grant select on grinder_forum_subscriptions to authenticated;
drop policy if exists forum_question_read on grinder_forum_questions;
create policy forum_question_read on grinder_forum_questions for select using(grinder_can_read_run(run_id));
drop policy if exists forum_question_blocked on grinder_forum_questions;
create policy forum_question_blocked on grinder_forum_questions as restrictive for select to authenticated using(not grinder_blocked(author_id,grinder_profile_id()));
drop policy if exists forum_subscription_read on grinder_forum_subscriptions;
create policy forum_subscription_read on grinder_forum_subscriptions for select to authenticated using(profile_id=grinder_profile_id() and exists(select 1 from grinder_forum_questions q where q.id=question_id and grinder_can_read_run(q.run_id)));

create or replace function grinder_forum_create(grind uuid,question_title text,question_body text,request uuid) returns uuid
language plpgsql security definer set search_path=public as $$
declare owner uuid:=grinder_profile_id(); prior grinder_forum_questions; saved uuid;
begin
 if owner is null or not grinder_can_read_run(grind) then raise exception 'Choose a run you can read'; end if;
 if exists(select 1 from runs where id=grind and grinder_blocked(owner,profile_id)) then raise exception 'Interaction unavailable'; end if;
 if request is null then raise exception 'A request ID is required'; end if;
 perform 1 from profiles where id=owner for update;
 select * into prior from grinder_forum_questions where author_id=owner and request_id=request;
 if found then
  if prior.run_id<>grind or prior.title is distinct from trim(question_title) or prior.body is distinct from trim(question_body) then raise exception 'A retry cannot change a question'; end if;
  return prior.id;
 end if;
 insert into grinder_forum_questions(run_id,author_id,title,body,request_id) values(grind,owner,trim(question_title),trim(question_body),request) returning id into saved;
 insert into grinder_forum_subscriptions(question_id,profile_id) values(saved,owner);
 return saved;
end $$;

create or replace function grinder_forum_subscribe(question uuid,enabled boolean) returns boolean
language plpgsql security definer set search_path=public as $$
declare owner uuid:=grinder_profile_id(); target grinder_forum_questions;
begin
 if owner is null or enabled is null then raise exception 'Sign in and choose a subscription'; end if;
 if not enabled then delete from grinder_forum_subscriptions where question_id=question and profile_id=owner;return false;end if;
 select * into target from grinder_forum_questions where id=question;
 if not found or not grinder_can_read_run(target.run_id) or grinder_blocked(owner,target.author_id) then raise exception 'Question unavailable'; end if;
 insert into grinder_forum_subscriptions(question_id,profile_id) values(question,owner) on conflict do nothing;
 return true;
end $$;

create or replace function grinder_forum_seen(question uuid,through_reply uuid) returns void
language plpgsql security definer set search_path=public as $$
begin
 if not exists(select 1 from grinder_forum_questions where id=question and grinder_can_read_run(run_id)) then raise exception 'Question unavailable'; end if;
 if through_reply is not null and not exists(select 1 from grinder_replies where id=through_reply and forum_question_id=question) then raise exception 'Choose a reply from this question'; end if;
 update grinder_forum_subscriptions set last_seen_at=greatest(last_seen_at,coalesce((select created_at from grinder_replies where id=through_reply and forum_question_id=question),(select created_at from grinder_forum_questions where id=question))) where question_id=question and profile_id=grinder_profile_id();
end $$;

create or replace function grinder_forum_accept(question uuid,answer uuid) returns void
language plpgsql security definer set search_path=public as $$
declare target grinder_forum_questions;
begin
 select * into target from grinder_forum_questions where id=question and author_id=grinder_profile_id() for update;
 if not found or not grinder_can_read_run(target.run_id) then raise exception 'Only the question author can choose an answer'; end if;
 if answer is not null and not exists(select 1 from grinder_replies where id=answer and forum_question_id=question and run_id=target.run_id and not grinder_blocked(author_id,target.author_id)) then raise exception 'Choose an answer from this question'; end if;
 update grinder_forum_questions set accepted_reply=answer where id=question;
end $$;

create or replace function grinder_forum_answer_guard() returns trigger
language plpgsql security definer set search_path=public as $$
declare target grinder_forum_questions;
begin
 if new.forum_question_id is not null then
  select * into target from grinder_forum_questions where id=new.forum_question_id;
  if not found or target.run_id<>new.run_id then raise exception 'Answer must belong to the question run'; end if;
  if grinder_blocked_pair(new.author_id,target.author_id) then raise exception 'Interaction unavailable'; end if;
 end if;
 if tg_op='UPDATE' and new.body is distinct from old.body then
  update grinder_forum_questions set accepted_reply=null where accepted_reply=old.id;
 end if;
 return new;
end $$;
drop trigger if exists grinder_forum_answer_guard on grinder_replies;
create trigger grinder_forum_answer_guard before insert or update on grinder_replies for each row execute function grinder_forum_answer_guard();
revoke all on function grinder_forum_create(uuid,text,text,uuid),grinder_forum_subscribe(uuid,boolean),grinder_forum_seen(uuid,uuid),grinder_forum_accept(uuid,uuid),grinder_forum_answer_guard() from public,anon,authenticated;
grant execute on function grinder_forum_create(uuid,text,text,uuid),grinder_forum_subscribe(uuid,boolean),grinder_forum_seen(uuid,uuid),grinder_forum_accept(uuid,uuid) to authenticated;
commit;
