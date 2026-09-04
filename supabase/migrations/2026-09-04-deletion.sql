-- Explicit ownership deletion; cross-owner records retain their frozen results.
begin;
create or replace function grinder_before_profile_delete() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 if exists(select 1 from grinder_crews c join grinder_memberships m on m.crew_id=c.id where c.owner_id=old.id and m.profile_id<>old.id) then raise exception 'Transfer ownership of your shared Crews before deleting your profile'; end if;
 if exists(select 1 from grinder_challenges c join grinder_challenge_entries e on e.challenge_id=c.id where c.owner_id=old.id and e.owner_id is distinct from old.id) then raise exception 'Transfer your hosted Challenges before deleting your profile'; end if;
 return old;
end $$;
drop trigger if exists grinder_before_profile_delete on profiles;
create trigger grinder_before_profile_delete before delete on profiles for each row execute function grinder_before_profile_delete();
-- Only these named relationships change. New tables cannot silently inherit a cascade.
do $$
declare rule record; fk record; definition text;
begin
 for rule in select * from (values
 ('runs','profile_id','CASCADE'),
 ('acks','from_profile','CASCADE'),('acks','to_profile','CASCADE'),('acks','run_id','CASCADE'),
 ('grinder_crews','owner_id','CASCADE'),
 ('grinder_invites','accepted_by','SET NULL'),
 ('runs','crew_id','SET NULL'),('runs','rig_revision','SET NULL'),('runs','source_actor_id','SET NULL'),
 ('grinder_replies','source_actor_id','SET NULL'),('grinder_replies','question_id','SET NULL'),
 ('grinder_rig_revisions','owner_id','CASCADE'),('grinder_agents','rig_revision','SET NULL'),
 ('grinder_agent_drafts','agent_id','CASCADE'),
 ('grinder_agent_questions','agent_id','CASCADE'),('grinder_agent_questions','asked_by','CASCADE'),('grinder_agent_questions','reply_id','SET NULL'),
 ('grinder_reports','reporter_id','CASCADE'),
 ('grinder_challenges','host_crew','CASCADE'),('grinder_challenges','owner_id','CASCADE'),
 ('grinder_challenge_entries','challenge_id','CASCADE'),('grinder_challenge_entries','owner_id','SET NULL'),('grinder_challenge_entries','crew_id','SET NULL'),('grinder_challenge_entries','rig_revision','SET NULL'),
 ('grinder_challenge_submissions','entry_id','CASCADE'),('grinder_challenge_submissions','run_id','SET NULL'),
 ('grinder_challenge_reviews','submission_id','CASCADE'),('grinder_challenge_reviews','reviewer_id','SET NULL'),('grinder_challenge_reviews','supersedes','SET NULL'),
 ('grinder_challenge_appeals','review_id','CASCADE'),('grinder_challenge_appeals','author_id','SET NULL'),
 ('grinder_practice_versions','owner_id','CASCADE'),('grinder_practice_versions','crew_id','CASCADE'),('grinder_practice_versions','source_run','SET NULL'),('grinder_practice_versions','rig_revision','SET NULL'),
 ('grinder_practice_attempts','owner_id','CASCADE'),('grinder_practice_attempts','practice_id','SET NULL'),
 ('grinder_experiments','owner_id','SET NULL'),('grinder_experiments','crew_id','CASCADE'),('grinder_experiments','practice_id','SET NULL'),
 ('grinder_experiment_cycles','owner_id','CASCADE'),('grinder_experiment_cycles','experiment_id','CASCADE')
 ) as rules(table_name,column_name,action)
 loop
  for fk in select c.conname,pg_get_constraintdef(c.oid) as definition
   from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=any(c.conkey)
   where c.contype='f' and c.conrelid=to_regclass('public.'||rule.table_name) and a.attname=rule.column_name
  loop
   if rule.action='SET NULL' then execute format('alter table public.%I alter column %I drop not null',rule.table_name,rule.column_name); end if;
   definition=regexp_replace(fk.definition,' ON DELETE (CASCADE|SET NULL|SET DEFAULT|RESTRICT|NO ACTION)','');
   execute format('alter table public.%I drop constraint %I',rule.table_name,fk.conname);
   execute format('alter table public.%I add constraint %I %s ON DELETE %s',rule.table_name,fk.conname,definition,rule.action);
  end loop;
 end loop;
end $$;
-- Deleting an answer must not reopen an already answered question.
create or replace function grinder_retire_deleted_answer() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 update grinder_agent_questions set expires_at=least(expires_at,now()) where reply_id=old.id;
 return old;
end $$;
drop trigger if exists retire_deleted_answer on grinder_replies;
create trigger retire_deleted_answer before delete on grinder_replies for each row execute function grinder_retire_deleted_answer();
commit;
