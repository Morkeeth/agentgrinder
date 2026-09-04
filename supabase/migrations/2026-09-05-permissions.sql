-- Supabase default grants must not widen this API. Re-run after all feature migrations.
begin;
revoke all on grinder_agent_drafts,grinder_agent_questions,grinder_agent_requests,grinder_agent_tokens,grinder_agents,grinder_blocks,grinder_challenge_appeals,grinder_challenge_entries,grinder_challenge_reviews,grinder_challenge_submissions,grinder_challenges,grinder_crews,grinder_experiment_cycles,grinder_experiments,grinder_follows,grinder_invites,grinder_memberships,grinder_notifications,grinder_practice_attempts,grinder_practice_versions,grinder_replies,grinder_reports,grinder_rig_revisions from public,anon,authenticated;
revoke truncate,references,trigger on profiles,runs,acks from public,anon,authenticated;
do $$ begin
 if to_regclass('public.follows') is not null then
  revoke truncate,references,trigger on public.follows from public,anon,authenticated;
 end if;
end $$;
grant select on grinder_follows,grinder_crews,grinder_memberships,grinder_replies to anon,authenticated;
grant select on grinder_invites,grinder_notifications to authenticated;
grant insert,delete on grinder_follows,grinder_replies to authenticated;
grant update(body) on grinder_replies to authenticated;
grant update(name,description,visibility) on grinder_crews to authenticated;
grant update(revoked) on grinder_invites to authenticated;
grant update(read_at) on grinder_notifications to authenticated;
grant select on grinder_rig_revisions to anon,authenticated;
grant insert on grinder_rig_revisions to authenticated;
grant select on grinder_agents to anon,authenticated;
grant insert on grinder_agents to authenticated;
grant update(name,visibility,rig_revision) on grinder_agents to authenticated;
grant select(id,agent_id,scopes,audiences,expires_at,revoked,created_at) on grinder_agent_tokens to authenticated;
grant update(revoked) on grinder_agent_tokens to authenticated;
grant select,delete on grinder_agent_drafts to authenticated;
grant select on grinder_challenges,grinder_challenge_entries,grinder_challenge_submissions,grinder_challenge_reviews,grinder_challenge_appeals to anon,authenticated;
grant select on grinder_practice_versions,grinder_practice_attempts to anon,authenticated;
grant insert on grinder_practice_versions to authenticated;
grant select,insert,delete on grinder_blocks to authenticated;
grant select,insert on grinder_reports to authenticated;
grant select on grinder_agent_questions to authenticated;
grant select on grinder_experiments,grinder_experiment_cycles to authenticated;
do $$ declare item record; begin
 for item in select oid::regprocedure as signature from pg_proc where pronamespace='public'::regnamespace and proname like 'grinder_%' loop
 execute format('revoke all on function %s from public,anon,authenticated',item.signature);
 end loop;
end $$;
grant execute on function grinder_share_with_crew(uuid,uuid,boolean),grinder_transfer_crew(uuid,uuid) to authenticated;
grant execute on function grinder_create_crew(text,text),grinder_invite(uuid),grinder_join_crew(text),grinder_remove_member(uuid,uuid) to authenticated;
grant execute on function grinder_issue_agent_token(uuid,text[],text[],timestamptz) to authenticated;
grant execute on function grinder_agent_action(text,text,jsonb,uuid) to anon,authenticated;
grant execute on function grinder_create_challenge(uuid,text,jsonb,timestamptz,text,integer),grinder_enter_challenge(uuid,uuid,uuid),grinder_submit_challenge(uuid,uuid),grinder_review_submission(uuid,text,text,uuid),grinder_appeal_review(uuid,text) to authenticated;
grant execute on function grinder_declare_run_rig(uuid,uuid) to authenticated;
grant execute on function grinder_start_attempt(uuid,uuid,boolean),grinder_review_attempt(uuid,uuid,boolean,text,text) to authenticated;
grant execute on function grinder_blocked(uuid,uuid) to authenticated;
grant execute on function grinder_ask_agent(uuid,uuid,text) to authenticated;
grant execute on function grinder_agent_questions(text) to anon,authenticated;
grant execute on function grinder_create_experiment(uuid,uuid,text,text),grinder_start_cycle(uuid,uuid),grinder_review_cycle(uuid,uuid,text,text) to authenticated;
grant execute on function grinder_feature_run(uuid) to authenticated;
grant execute on function grinder_link_access(uuid),grinder_profile_id(),grinder_is_member(uuid),grinder_owns_crew(uuid),grinder_can_read_run(uuid),grinder_can_read_practice(uuid) to anon,authenticated;
commit;
