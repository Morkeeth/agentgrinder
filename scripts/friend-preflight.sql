-- Run inside the migration transaction, followed by ROLLBACK. All rows below are test fixtures.
set local role authenticated;
select set_config('request.jwt.claim.sub','f1000000-0000-0000-0000-000000000001',true);
insert into profiles(id,auth_uid,github_handle,name) values('f2000000-0000-0000-0000-000000000001','f1000000-0000-0000-0000-000000000001','grinder_preflight_a','Temporary preflight fixture A');
insert into runs(id,profile_id,title,visibility,prompts,duration_s,schema_version,measurement_revision)
values('f3000000-0000-0000-0000-000000000001','f2000000-0000-0000-0000-000000000001','Temporary preflight public run','public',2,90.5,1,repeat('a',64)),
('f3000000-0000-0000-0000-000000000002','f2000000-0000-0000-0000-000000000001','Temporary preflight private run','private',1,30,1,repeat('b',64));
select set_config('request.jwt.claim.sub','f1000000-0000-0000-0000-000000000002',true);
insert into profiles(id,auth_uid,github_handle,name) values('f2000000-0000-0000-0000-000000000002','f1000000-0000-0000-0000-000000000002','grinder_preflight_b','Temporary preflight fixture B');
do $$ begin
 if not exists(select 1 from runs where id='f3000000-0000-0000-0000-000000000001') then raise exception 'Friend cannot read public run'; end if;
 if exists(select 1 from runs where id='f3000000-0000-0000-0000-000000000002') then raise exception 'Friend can read private run'; end if;
end $$;
insert into acks(from_profile,to_profile,run_id,reason) values('f2000000-0000-0000-0000-000000000002','f2000000-0000-0000-0000-000000000001','f3000000-0000-0000-0000-000000000001','focus');
select set_config('request.jwt.claim.sub','f1000000-0000-0000-0000-000000000001',true);
do $$ begin
 if not exists(select 1 from grinder_notifications where recipient_id='f2000000-0000-0000-0000-000000000001' and kind='ack') then raise exception 'Author cannot see friend ACK'; end if;
end $$;
delete from runs where id='f3000000-0000-0000-0000-000000000001';
do $$ begin
 if exists(select 1 from acks where run_id='f3000000-0000-0000-0000-000000000001') then raise exception 'Run deletion left ACKs'; end if;
end $$;
reset role;
select 'PASS: real PostgreSQL roles, private/public import, friend ACK, return notification, run deletion. Transaction will roll back.' as friend_preflight;
