begin;
alter table profiles add column if not exists featured_run_id uuid references runs(id) on delete set null;
create or replace function grinder_feature_run(grind uuid) returns void
language plpgsql security definer set search_path=public as $$ begin
 if grinder_profile_id() is null then raise exception 'Sign in to edit your Scrapbook'; end if;
 if grind is not null and not exists(select 1 from runs where id=grind and profile_id=grinder_profile_id() and visibility='public') then raise exception 'Choose one of your public grinds'; end if;
 update profiles set featured_run_id=grind where id=grinder_profile_id();
end $$;
revoke all on function grinder_feature_run(uuid) from public;
grant execute on function grinder_feature_run(uuid) to authenticated;
commit;
