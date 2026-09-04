-- Profile deletion removes owned product records. A shared Crew needs a new owner first.
-- Public practice/event history can disappear when its owner deletes it; do not promise permanence.
begin;
create or replace function grinder_before_profile_delete() returns trigger
language plpgsql security definer set search_path=public as $$ begin
 if exists(select 1 from grinder_crews c join grinder_memberships m on m.crew_id=c.id where c.owner_id=old.id and m.profile_id<>old.id) then raise exception 'Transfer ownership of your shared Crews before deleting your profile'; end if;
 return old;
end $$;
drop trigger if exists grinder_before_profile_delete on profiles;
create trigger grinder_before_profile_delete before delete on profiles for each row execute function grinder_before_profile_delete();
-- Own records and dependent conversations follow their source's deletion. Existing unrelated
-- tables are untouched. The two optional references from runs are detached instead.
do $$
declare fk record; definition text;
begin
 for fk in
  select c.conname,t.relname as tablename,pg_get_constraintdef(c.oid) as definition
  from pg_constraint c join pg_class t on t.oid=c.conrelid join pg_namespace n on n.oid=t.relnamespace
  where c.contype='f' and c.confdeltype in ('a','r') and n.nspname='public' and (t.relname like 'grinder_%' or (t.relname='runs' and pg_get_constraintdef(c.oid) like 'FOREIGN KEY (profile_id)%'))
 loop
  definition=regexp_replace(fk.definition,' ON DELETE (CASCADE|SET NULL|SET DEFAULT|RESTRICT|NO ACTION)','');
  execute format('alter table public.%I drop constraint %I',fk.tablename,fk.conname);
  execute format('alter table public.%I add constraint %I %s ON DELETE CASCADE',fk.tablename,fk.conname,definition);
 end loop;
 for fk in
  select c.conname,pg_get_constraintdef(c.oid) as definition from pg_constraint c join pg_class t on t.oid=c.conrelid join pg_namespace n on n.oid=t.relnamespace
  where c.contype='f' and n.nspname='public' and t.relname='runs' and (pg_get_constraintdef(c.oid) like 'FOREIGN KEY (crew_id)%' or pg_get_constraintdef(c.oid) like 'FOREIGN KEY (rig_revision)%' or pg_get_constraintdef(c.oid) like 'FOREIGN KEY (source_actor_id)%')
 loop
  definition=regexp_replace(fk.definition,' ON DELETE (CASCADE|SET NULL|SET DEFAULT|RESTRICT|NO ACTION)','');
  execute format('alter table public.runs drop constraint %I',fk.conname);
  execute format('alter table public.runs add constraint %I %s ON DELETE SET NULL',fk.conname,definition);
 end loop;
end $$;
commit;
