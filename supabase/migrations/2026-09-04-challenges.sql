-- Challenges pin a task contract, a Rig revision and the submitted measurement.
-- Results are explicitly organiser reviews. There is no inferred quality score.
begin;
create table if not exists grinder_challenges (
 id uuid primary key default gen_random_uuid(), host_crew uuid not null references grinder_crews(id),
 owner_id uuid not null references profiles(id), name text not null check(length(trim(name)) between 1 and 120),
 kind text not null check(kind in ('challenge','octacon')),
 contract jsonb not null check(jsonb_typeof(contract)='object'),
 capacity integer not null check(capacity between 2 and 100),
 closes_at timestamptz not null, created_at timestamptz not null default now(),
 check(kind<>'octacon' or capacity=8)
);
create table if not exists grinder_challenge_entries (
 id uuid primary key default gen_random_uuid(), challenge_id uuid not null references grinder_challenges(id),
 crew_id uuid not null references grinder_crews(id), owner_id uuid not null references profiles(id),
 crew_name text not null, rig_revision uuid not null references grinder_rig_revisions(id),
 created_at timestamptz not null default now(), unique(challenge_id,crew_id)
);
create unique index if not exists grinder_challenge_one_owner on grinder_challenge_entries(challenge_id,owner_id);
create table if not exists grinder_challenge_submissions (
 id uuid primary key default gen_random_uuid(), entry_id uuid not null references grinder_challenge_entries(id),
 run_id uuid not null references runs(id), measurement_revision text not null,
 snapshot jsonb not null, created_at timestamptz not null default now(), unique(entry_id,measurement_revision)
);
create table if not exists grinder_challenge_reviews (
 id uuid primary key default gen_random_uuid(), submission_id uuid not null references grinder_challenge_submissions(id),
 reviewer_id uuid not null references profiles(id), verdict text not null check(verdict in ('accepted','rejected')),
 evidence text not null check(length(trim(evidence)) between 1 and 4000),
 supersedes uuid references grinder_challenge_reviews(id), created_at timestamptz not null default now()
);
create table if not exists grinder_challenge_appeals (
 id uuid primary key default gen_random_uuid(), review_id uuid not null references grinder_challenge_reviews(id),
 author_id uuid not null references profiles(id), body text not null check(length(trim(body)) between 1 and 4000),
 created_at timestamptz not null default now()
);

alter table grinder_challenges enable row level security;
alter table grinder_challenge_entries enable row level security;
alter table grinder_challenge_submissions enable row level security;
alter table grinder_challenge_reviews enable row level security;
alter table grinder_challenge_appeals enable row level security;
-- Entering and submitting are deliberate public actions. Private sources are not exposed.
drop policy if exists challenges_read on grinder_challenges;
create policy challenges_read on grinder_challenges for select using(true);
drop policy if exists entries_read on grinder_challenge_entries;
create policy entries_read on grinder_challenge_entries for select using(true);
drop policy if exists submissions_read on grinder_challenge_submissions;
create policy submissions_read on grinder_challenge_submissions for select using(true);
drop policy if exists reviews_read on grinder_challenge_reviews;
create policy reviews_read on grinder_challenge_reviews for select using(true);
drop policy if exists appeals_read on grinder_challenge_appeals;
create policy appeals_read on grinder_challenge_appeals for select using(true);
grant select on grinder_challenges,grinder_challenge_entries,grinder_challenge_submissions,grinder_challenge_reviews,grinder_challenge_appeals to anon,authenticated;

create or replace function grinder_create_challenge(crew uuid,title text,task_contract jsonb,closes timestamptz,format text default 'challenge',places integer default 8) returns uuid
language plpgsql security definer set search_path=public as $$
declare result uuid;
begin
 if not grinder_owns_crew(crew) then raise exception 'Only the host Crew owner can create a Challenge'; end if;
 if closes is null or closes<=now() then raise exception 'Choose a closing time in the future'; end if;
 if jsonb_typeof(task_contract) is distinct from 'object' or length(trim(coalesce(task_contract->>'task','')))=0 or jsonb_typeof(task_contract->'checks') is distinct from 'array' or jsonb_array_length(task_contract->'checks')=0 or octet_length(task_contract::text)>16384 then raise exception 'The Contract needs a task and a non-empty list of checks'; end if;
 if exists(select 1 from jsonb_array_elements(task_contract->'checks') item where jsonb_typeof(item)<>'string' or length(trim(item#>>'{}'))=0) then raise exception 'Each check needs a description'; end if;
 insert into grinder_challenges(host_crew,owner_id,name,kind,contract,capacity,closes_at)
 values(crew,grinder_profile_id(),title,format,task_contract,places,closes) returning id into result;
 return result;
end $$;

create or replace function grinder_enter_challenge(challenge uuid,crew uuid,rig uuid) returns uuid
language plpgsql security definer set search_path=public as $$
declare event grinder_challenges; result uuid; label text;
begin
 select * into event from grinder_challenges where id=challenge for update;
 if not found or event.closes_at<=now() then raise exception 'This Challenge is closed'; end if;
 if not grinder_owns_crew(crew) then raise exception 'Only a Crew owner can enter it'; end if;
 if event.owner_id=grinder_profile_id() then raise exception 'The organiser cannot enter their own Challenge'; end if;
 select id into result from grinder_challenge_entries where challenge_id=challenge and crew_id=crew;
 if found then return result; end if;
 if exists(select 1 from grinder_challenge_entries where challenge_id=challenge and owner_id=grinder_profile_id()) then raise exception 'One entry per owner per Challenge'; end if;
 if (select count(*) from grinder_challenge_entries where challenge_id=challenge)>=event.capacity then raise exception 'This Challenge is full'; end if;
 if not exists(select 1 from grinder_rig_revisions where id=rig and owner_id=grinder_profile_id() and visibility='public') then raise exception 'Choose your public Rig revision; entries expose the locked configuration'; end if;
 select name into label from grinder_crews where id=crew;
 insert into grinder_challenge_entries(challenge_id,crew_id,owner_id,crew_name,rig_revision)
 values(challenge,crew,grinder_profile_id(),label,rig) returning id into result;
 return result;
end $$;

create or replace function grinder_submit_challenge(entry uuid,grind uuid) returns uuid
language plpgsql security definer set search_path=public as $$
declare participant grinder_challenge_entries; event grinder_challenges; activity runs; result uuid;
begin
 select * into participant from grinder_challenge_entries where id=entry;
 if not found or participant.owner_id<>grinder_profile_id() or grinder_profile_id() is null then raise exception 'Only the entrant can submit this grind'; end if;
 select * into event from grinder_challenges where id=participant.challenge_id;
 if event.closes_at<=now() then raise exception 'Submissions have closed'; end if;
 select * into activity from runs where id=grind;
 if not found or activity.profile_id<>grinder_profile_id() or activity.visibility<>'public' then raise exception 'Choose your public grind'; end if;
 if activity.started_at is null or activity.started_at<participant.created_at or activity.started_at>now() then raise exception 'Choose a session started after entry and before now'; end if;
 if activity.rig_revision is distinct from participant.rig_revision then raise exception 'The grind must declare the locked Rig revision'; end if;
 if activity.measurement_revision is null or activity.measurement_revision!~'^[a-f0-9]{64}$' then raise exception 'This grind needs a measurement revision'; end if;
 insert into grinder_challenge_submissions(entry_id,run_id,measurement_revision,snapshot)
 values(entry,grind,activity.measurement_revision,jsonb_build_object('title',activity.title,'harness',activity.harness,
 'turns_typed',activity.prompts,'claims',activity.claims,'claims_verified',activity.claims_verified,
 'artifacts_produced',activity.artifacts_produced,'commits',activity.commits,'measurement_revision',activity.measurement_revision,
 'rhythm',activity.rhythm,'trace_basis',activity.trace_basis,'rig_revision',participant.rig_revision,'evidence_level','client-reported; awaiting organiser review'))
 on conflict(entry_id,measurement_revision) do nothing returning id into result;
 if result is null then select id into result from grinder_challenge_submissions where entry_id=entry and measurement_revision=activity.measurement_revision; end if;
 return result;
end $$;

create or replace function grinder_review_submission(submission uuid,decision text,reason text,previous_review uuid default null) returns uuid
language plpgsql security definer set search_path=public as $$
declare result uuid; host uuid; latest uuid;
begin
 select c.owner_id into host from grinder_challenges c join grinder_challenge_entries e on e.challenge_id=c.id join grinder_challenge_submissions s on s.entry_id=e.id where s.id=submission;
 if host is null or grinder_profile_id() is null or host<>grinder_profile_id() then raise exception 'Only the Challenge organiser can review a submission'; end if;
 perform 1 from grinder_challenge_submissions where id=submission for update;
 select id into latest from grinder_challenge_reviews where submission_id=submission order by created_at desc,id desc limit 1;
 if latest is distinct from previous_review then raise exception 'Review changed; refresh and supersede the current review'; end if;
 if previous_review is not null and not exists(select 1 from grinder_challenge_reviews where id=previous_review and submission_id=submission) then raise exception 'The previous review belongs to another submission'; end if;
 insert into grinder_challenge_reviews(submission_id,reviewer_id,verdict,evidence,supersedes) values(submission,host,decision,reason,previous_review) returning id into result;
 return result;
end $$;

create or replace function grinder_appeal_review(review uuid,reason text) returns uuid
language plpgsql security definer set search_path=public as $$
declare entrant uuid; result uuid;
begin
 select e.owner_id into entrant from grinder_challenge_entries e join grinder_challenge_submissions s on s.entry_id=e.id join grinder_challenge_reviews r on r.submission_id=s.id where r.id=review;
 if entrant is null or grinder_profile_id() is null or entrant<>grinder_profile_id() then raise exception 'Only the entrant can appeal this review'; end if;
 insert into grinder_challenge_appeals(review_id,author_id,body) values(review,entrant,reason) returning id into result;
 return result;
end $$;
revoke all on function grinder_create_challenge(uuid,text,jsonb,timestamptz,text,integer),grinder_enter_challenge(uuid,uuid,uuid),grinder_submit_challenge(uuid,uuid),grinder_review_submission(uuid,text,text,uuid),grinder_appeal_review(uuid,text) from public;
grant execute on function grinder_create_challenge(uuid,text,jsonb,timestamptz,text,integer),grinder_enter_challenge(uuid,uuid,uuid),grinder_submit_challenge(uuid,uuid),grinder_review_submission(uuid,text,text,uuid),grinder_appeal_review(uuid,text) to authenticated;
create or replace function grinder_declare_run_rig(grind uuid,rig uuid) returns void
language plpgsql security definer set search_path=public as $$
declare activity runs;
begin
 select * into activity from runs where id=grind and profile_id=grinder_profile_id();
 if not found then raise exception 'Only the grind owner can declare its Rig'; end if;
 if not exists(select 1 from grinder_rig_revisions where id=rig and owner_id=grinder_profile_id() and (visibility='public' or activity.visibility='private')) then raise exception 'Choose your Rig with matching visibility'; end if;
 update runs set rig_revision=rig where id=grind;
end $$;
revoke all on function grinder_declare_run_rig(uuid,uuid) from public;
grant execute on function grinder_declare_run_rig(uuid,uuid) to authenticated;
commit;
