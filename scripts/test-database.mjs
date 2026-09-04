// Runs the actual migration and RLS in PostgreSQL/WASM. Authentication is a test GUC;
// profile/run seed rows are explicit fixtures, not claimed live users.
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
process.on("uncaughtException", (error) => {
  console.error(error.message);
  process.exit(1);
});
if (Number(process.versions.node.split(".")[0]) < 20) {
  console.error("Database checks require Node 20 or newer.");
  process.exit(1);
}
const { PGlite } = await import("@electric-sql/pglite");
const db = new PGlite();
const userA = "10000000-0000-0000-0000-000000000001",
  userB = "10000000-0000-0000-0000-000000000002",
  userC = "10000000-0000-0000-0000-000000000003";
const runA = "20000000-0000-0000-0000-000000000001";
await db.exec(`create role anon; create role authenticated;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to anon,authenticated;
create table profiles(id uuid primary key,auth_uid uuid unique);
create table runs(id uuid primary key default gen_random_uuid(),profile_id uuid references profiles(id),visibility text,
title text,project text,harness text,prompts integer,duration_s double precision,tool_calls integer,files_touched integer,
commits integer,claims integer,claims_verified integer,artifacts_produced integer,started_at timestamptz);
create table acks(id uuid primary key default gen_random_uuid(),from_profile uuid references profiles(id),to_profile uuid references profiles(id),run_id uuid references runs(id),reason text,same_owner boolean,unique(from_profile,run_id));
alter table runs enable row level security;
create policy seed_runs_read on runs for select using (visibility='public' or profile_id=auth.uid());
grant select on profiles,runs to anon,authenticated;
insert into profiles values('${userA}','${userA}'),('${userB}','${userB}'),('${userC}','${userC}');
insert into runs(id,profile_id,visibility) values('${runA}','${userA}','public');`);
for (const file of (
  await readFile(new URL("./migration-order.txt", import.meta.url), "utf8")
)
  .trim()
  .split("\n")) {
  const sql = await readFile(
    new URL("../supabase/migrations/" + file, import.meta.url),
    "utf8",
  );
  await db.exec(sql);
  await db.exec(sql); // migrations must tolerate retries
}
await db.exec(execFileSync("python3", [new URL("./prepare-migration.py", import.meta.url).pathname], {encoding:"utf8"}));
async function as(id) {
  await db.exec("reset role");
  await db.query("select set_config('request.jwt.claim.sub',$1,false)", [id]);
  await db.exec("set role authenticated");
}
async function denied(sql, params = []) {
  let caught = false;
  try {
    await db.query(sql, params);
  } catch {
    caught = true;
  }
  assert(caught, "Expected server denial: " + sql);
}
await as(userA);
const crew = (await db.query("select grinder_create_crew('Test crew') id"))
  .rows[0].id;
assert.equal(
  (await db.query("select * from grinder_memberships")).rows.length,
  1,
);
const token = (await db.query("select grinder_invite($1) token", [crew]))
  .rows[0].token;
await as(userB);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 0);
await denied("select grinder_invite($1)", [crew]);
await db.query("select grinder_join_crew($1)", [token]);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 1);
await db.query(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userB, userA],
);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userA, userC],
);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$1)",
  [userB],
);
const reply = (
  await db.query(
    "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3) returning id",
    [runA, userB, "What check did you run?"],
  )
).rows[0].id;
await as(userA);
assert.equal(
  (await db.query("select * from grinder_notifications")).rows.length,
  2,
);
assert.equal(
  (
    await db.query(
      "update grinder_replies set body='changed' where id=$1 returning id",
      [reply],
    )
  ).rows.length,
  0,
);
await as(userC);
await denied("select grinder_join_crew($1)", [token]);
assert.equal(
  (await db.query("select * from grinder_notifications")).rows.length,
  0,
);
await db.exec("reset role");
await db.query("update runs set visibility='private' where id=$1", [runA]);
await as(userB);
assert.equal((await db.query("select * from grinder_replies")).rows.length, 0);
await denied(
  "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3)",
  [runA, userB, "Private leak"],
);
await as(userA);
await db.query("select grinder_share_with_crew($1,$2)", [runA, crew]);
await as(userB);
assert.equal((await db.query("select * from runs")).rows.length, 1);
await as(userC);
assert.equal((await db.query("select * from runs")).rows.length, 0);
await as(userA);
await db.query("select grinder_remove_member($1,$2)", [crew, userB]);
await as(userB);
assert.equal((await db.query("select * from grinder_crews")).rows.length, 0);
assert.equal((await db.query("select * from runs")).rows.length, 0);
await as(userA);
const actor = (
  await db.query(
    "insert into grinder_agents(owner_id,name) values($1,'Test agent') returning id",
    [userA],
  )
).rows[0].id;
const issued = (
  await db.query(
    "select grinder_issue_agent_token($1,array['draft','publish'],array['private'],now()+interval '1 day') as value",
    [actor],
  )
).rows[0].value;
await as(userB);
await denied(
  "select grinder_issue_agent_token($1,array['draft'],array['private'],now()+interval '1 day')",
  [actor],
);
const req = "30000000-0000-0000-0000-000000000001";
await db.exec("reset role;set role anon");
const drafted = (
  await db.query("select grinder_agent_action($1,'draft',$2,$3) value", [
    issued.token,
    { turns_typed: 2, title: "Fixture draft" },
    req,
  ])
).rows[0].value;
const repeated = (
  await db.query("select grinder_agent_action($1,'draft',$2,$3) value", [
    issued.token,
    { turns_typed: 2, title: "Fixture draft" },
    req,
  ])
).rows[0].value;
assert.equal(drafted.id, repeated.id);
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: 3 },
  req,
]);
await denied("select grinder_agent_action($1,'publish',$2,$3)", [
  issued.token,
  { visibility: "public" },
  "30000000-0000-0000-0000-000000000002",
]);
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: -1 },
  "30000000-0000-0000-0000-000000000003",
]);
await denied("select grinder_agent_action($1,'reply',$2,$3)", [
  issued.token,
  { run_id: runA, body: "Not permitted" },
  "30000000-0000-0000-0000-000000000004",
]);
await as(userA);
assert.equal(
  (await db.query("select * from grinder_agent_drafts")).rows.length,
  1,
);
await denied("select token_hash from grinder_agent_tokens");
await db.query("update grinder_agent_tokens set revoked=true where id=$1", [
  issued.id,
]);
await denied("update grinder_agent_tokens set revoked=false where id=$1", [
  issued.id,
]);
await denied(
  "insert into grinder_rig_revisions(owner_id,label,manifest) values($1,'Unsafe',$2)",
  [userA, { api_key: "fixture" }],
);
await db.exec("reset role;set role anon");
await denied("select grinder_agent_action($1,'draft',$2,$3)", [
  issued.token,
  { turns_typed: 2, title: "Fixture draft" },
  req,
]);
await as(userA);
const rigA = (
  await db.query(
    "insert into grinder_rig_revisions(owner_id,label,manifest,visibility) values($1,'Fixture rig',$2,'public') returning id",
    [userA, { harnesses: ["fixture"] }],
  )
).rows[0].id;
const challenge = (
  await db.query(
    "select grinder_create_challenge($1,'Fixture OCTACON',$2,now()+interval '1 day','octacon',8) id",
    [
      crew,
      { task: "Complete the fixture task", checks: ["Run the declared check"] },
    ],
  )
).rows[0].id;
const entryA = (
  await db.query("select grinder_enter_challenge($1,$2,$3) id", [
    challenge,
    crew,
    rigA,
  ])
).rows[0].id;
await denied("update grinder_challenges set contract='{}' where id=$1", [
  challenge,
]);
await as(userB);
const crewB = (
  await db.query("select grinder_create_crew('Second fixture crew') id")
).rows[0].id;
const rigB = (
  await db.query(
    "insert into grinder_rig_revisions(owner_id,label,manifest,visibility) values($1,'Second fixture rig',$2,'public') returning id",
    [userB, { harnesses: ["fixture"] }],
  )
).rows[0].id;
await db.query("select grinder_enter_challenge($1,$2,$3)", [
  challenge,
  crewB,
  rigB,
]);
await denied("select grinder_submit_challenge($1,$2)", [entryA, runA]);
await db.exec("reset role");
await db.query(
  "update runs set visibility='public',measurement_revision=$2,claims_verified=1,started_at=now(),rig_revision=$3 where id=$1",
  [runA, "a".repeat(64), rigA],
);
await as(userA);
const submission = (
  await db.query("select grinder_submit_challenge($1,$2) id", [entryA, runA])
).rows[0].id;
const rejected = (
  await db.query(
    "select grinder_review_submission($1,'rejected','Declared check was missing') id",
    [submission],
  )
).rows[0].id;
await db.query(
  "select grinder_appeal_review($1,'The check result is attached to the submitted revision')",
  [rejected],
);
await db.query(
  "select grinder_review_submission($1,'accepted','Reviewed the submitted result',$2)",
  [submission, rejected],
);
assert.equal(
  (await db.query("select * from grinder_challenge_reviews")).rows.length,
  2,
);
await db.exec("reset role");
await db.query("update runs set claims_verified=9 where id=$1", [runA]);
assert.equal(
  (
    await db.query(
      "select snapshot from grinder_challenge_submissions where id=$1",
      [submission],
    )
  ).rows[0].snapshot.claims_verified,
  1,
);
await db.query(
  "update grinder_challenges set closes_at=now()-interval '1 minute' where id=$1",
  [challenge],
);
await as(userA);
await denied("select grinder_submit_challenge($1,$2)", [entryA, runA]);
await as(userA);
await denied(
  "select grinder_create_challenge($1,'Invalid',$2,now()+interval '1 day')",
  [crew, { task: "Missing checks" }],
);
await denied(
  "select grinder_review_submission($1,'accepted','Duplicate without supersedes')",
  [submission],
);
const practice = (
  await db.query(
    "insert into grinder_practice_versions(owner_id,title,task_context,instruction,expected,visibility) values($1,'Check before claiming','Small fixes','Run the named check','Evidence for the changed behavior','public') returning id",
    [userA],
  )
).rows[0].id;
await as(userB);
await denied("select grinder_start_attempt($1,$2,true)", [practice, runA]);
await db.exec("reset role");
const runB = "20000000-0000-0000-0000-000000000002";
await db.query(
  "insert into runs(id,profile_id,visibility,harness,measurement_revision,started_at) values($1,$2,'private','fixture',$3,now()-interval '1 day')",
  [runB, userB, "b".repeat(64)],
);
await as(userB);
const attempt = (
  await db.query("select grinder_start_attempt($1,$2,true) id", [
    practice,
    runB,
  ])
).rows[0].id;
await denied(
  "select grinder_review_attempt($1,null,false,'keep','Not tried')",
  [attempt],
);
await db.query(
  "select grinder_review_attempt($1,null,false,'incomparable','Not tried')",
  [attempt],
);
await denied(
  "select grinder_review_attempt($1,null,false,'incomparable','Rewrite')",
  [attempt],
);
await as(userA);
assert.equal(
  (await db.query("select * from grinder_practice_attempts")).rows[0].decision,
  "incomparable",
);
await db.query(
  "insert into grinder_blocks(blocker_id,blocked_id) values($1,$2)",
  [userA, userB],
);
await as(userB);
assert.equal(
  (await db.query("select id from runs where id=$1", [runA])).rows.length,
  0,
);
await denied(
  "insert into grinder_follows(follower_id,followed_id) values($1,$2)",
  [userB, userA],
);
await denied(
  "insert into grinder_replies(run_id,author_id,body) values($1,$2,$3)",
  [runA, userB, "Blocked reply"],
);
await as(userA);
await db.query(
  "delete from grinder_blocks where blocker_id=$1 and blocked_id=$2",
  [userA, userB],
);
await as(userB);
assert.equal(
  (await db.query("select id from runs where id=$1", [runA])).rows.length,
  1,
);
await as(userA);
await db.query("update grinder_agents set visibility='public' where id=$1", [
  actor,
]);
const answering = (
  await db.query(
    "select grinder_issue_agent_token($1,array['publish','reply'],array['public'],now()+interval '1 day') value",
    [actor],
  )
).rows[0].value;
await db.exec("reset role;set role anon");
const agentRun = (
  await db.query(
    "select grinder_agent_action($1,'publish',$2,gen_random_uuid()) value",
    [
      answering.token,
      {
        title: "Public fixture grind",
        visibility: "public",
        turns_typed: 2,
        measurement_revision: "c".repeat(64),
      },
    ],
  )
).rows[0].value.id;
await as(userB);
const question = (
  await db.query("select grinder_ask_agent($1,$2,'Which check passed?') id", [
    actor,
    agentRun,
  ])
).rows[0].id;
await db.exec("reset role;set role anon");
const queue = (
  await db.query("select grinder_agent_questions($1) value", [answering.token])
).rows[0].value;
assert.equal(queue[0].question_id, question);
assert.equal(queue[0].evidence.turns_typed, 2);
assert(!JSON.stringify(queue).includes("token"));
await db.query("select grinder_agent_action($1,'reply',$2,gen_random_uuid())", [
  answering.token,
  {
    run_id: agentRun,
    question_id: question,
    body: "Only the reported counts are available. No named test output is included.",
  },
]);
assert.deepEqual(
  (
    await db.query("select grinder_agent_questions($1) value", [
      answering.token,
    ])
  ).rows[0].value,
  [],
);
await denied("select grinder_agent_action($1,'reply',$2,gen_random_uuid())", [
  answering.token,
  { run_id: agentRun, question_id: question, body: "Duplicate response" },
]);
await as(userA);
const experiment = (
  await db.query(
    "select grinder_create_experiment($1,$2,'Fixture experiment','Observe the next two cycles') id",
    [crew, practice],
  )
).rows[0].id;
const cycle = (
  await db.query("select grinder_start_cycle($1,$2) id", [experiment, runA])
).rows[0].id;
await db.query(
  "select grinder_review_cycle($1,null,'incomparable','No outcome yet')",
  [cycle],
);
const nextCycle = (
  await db.query("select grinder_start_cycle($1,$2) id", [experiment, runA])
).rows[0].id;
assert.notEqual(cycle, nextCycle);
await denied("select grinder_review_cycle($1,null,'adopt','No outcome')", [
  nextCycle,
]);
await as(userC);
assert.equal(
  (await db.query("select * from grinder_experiments")).rows.length,
  0,
);
await denied("select grinder_start_cycle($1,$2)", [experiment, runA]);
await db.exec("reset role");
const deleting = "10000000-0000-0000-0000-000000000004";
await db.query("insert into profiles(id,auth_uid) values($1,$1)", [deleting]);
await as(deleting);
const deletingCrew = (
  await db.query("select grinder_create_crew('Delete fixture') id")
).rows[0].id;
await db.query(
  "insert into grinder_rig_revisions(owner_id,label,manifest) values($1,'Delete rig','{}')",
  [deleting],
);
await db.exec("reset role");
await db.query("insert into runs(profile_id,visibility) values($1,'private')", [
  deleting,
]);
await db.query("delete from profiles where id=$1", [deleting]);
assert.equal(
  (await db.query("select * from grinder_crews where id=$1", [deletingCrew]))
    .rows.length,
  0,
);
assert.equal(
  (await db.query("select * from runs where profile_id=$1", [deleting])).rows
    .length,
  0,
);
await as(userA);
await db.query("select grinder_feature_run($1)", [runA]);
assert.equal(
  (await db.query("select featured_run_id from profiles where id=$1", [userA]))
    .rows[0].featured_run_id,
  runA,
);
await as(userB);
await denied("select grinder_feature_run($1)", [runA]);
await db.close();
console.log(
  "Database checks passed: social permissions; agent capabilities; two-crew Challenge; locked Contract; frozen submission; rejection, appeal and revised review; late-submission denial.",
);
